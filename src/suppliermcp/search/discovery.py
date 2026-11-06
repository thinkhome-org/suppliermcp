import hashlib
import json

from suppliermcp.catalog.contracts import CatalogError, CatalogQuery, SearchResult
from suppliermcp.catalog.repository import get_products, read_status

from .index import ALIAS, FACET_FIELDS, SEARCH_FIELDS, facet_key, normalize
from .listing import matching_ids, materialize
from .schema import catalog_schema, validate_filter


def search(conn, client, text, filters, principal, settings=None):
    if not text.strip() or len(text) > 1000:
        raise CatalogError("invalid_search_text")
    params = {
        "q": normalize(text),
        "query_by": ",".join(SEARCH_FIELDS),
        "query_by_weights": ",".join(map(str, SEARCH_FIELDS.values())),
        "include_fields": "id",
        "per_page": 250,
        "drop_tokens_threshold": 0,
        "num_typos": 0,
        "prefix": "false",
    }
    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        query = CatalogQuery(filters=filters)
        schema = catalog_schema(conn) if filters else {}
        # Only known, validated filter values enter the index expression.
        clauses = []
        for f in filters:
            validate_filter(f, schema)
            if f.operator not in {"eq", "in"}:
                continue
            values = [f.value] if f.operator == "eq" else f.value
            if f.field == "supplier" and all(v in {"ed", "mega"} for v in values):
                clauses.append("supplier:=[" + ",".join(values) + "]")
            elif f.field in FACET_FIELDS:
                clauses.append(
                    "verified:=[" + ",".join(facet_key(f.field, v) for v in values) + "]"
                )
        if clauses:
            params["filter_by"] = " && ".join(clauses)
        ids = {}
        unknown_hits = set()
        page = 1
        while True:
            data = client.request(
                "GET",
                f"/collections/{ALIAS}/documents/search",
                params={**params, "page": page},
            ).json()
            candidates = [hit["document"]["id"] for hit in data["hits"]]
            confirmed, unknown = matching_ids(conn, query, candidate_ids=candidates, schema=schema)
            allowed = set(confirmed)
            ids.update(dict.fromkeys(i for i in candidates if i in allowed))
            unknown_hits.update(unknown)
            exhausted = not candidates or page * params["per_page"] >= data["found"]
            if exhausted or len(ids) >= 1000:
                break
            page += 1
        limited = not exhausted or len(ids) > 1000
        ids = list(ids)[:1000]
        products = get_products(conn, ids, include_evidence=False)
        coverage = read_status(conn, settings.enabled_interfaces if settings else None)
        coverage.complete = False
        coverage.warnings.append("text_discovery_is_not_exhaustive")
        if coverage.index_revision < coverage.revision:
            coverage.warnings.append("index_lag")
        if limited:
            coverage.warnings.append("candidate_scan_limited_to_1000")
        digest = hashlib.sha256(
            json.dumps(
                {"text": text, "filters": [f.model_dump() for f in filters]}, sort_keys=True
            ).encode()
        ).hexdigest()
        result = materialize(
            conn,
            products,
            coverage,
            principal,
            digest,
            unknown_total=len(unknown_hits),
            settings=settings,
        )
        return SearchResult(**result.model_dump())
