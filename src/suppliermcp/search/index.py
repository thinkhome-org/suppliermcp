"""Rebuildable index; PostgreSQL remains authoritative."""

import hashlib
import json
import re
import secrets
import unicodedata
from pathlib import Path
from urllib.parse import quote

import httpx

from suppliermcp.catalog.contracts import CatalogError
from suppliermcp.catalog.db import require_projected_catalog

ALIAS = "supplier_catalog_clean_v2"
SYNONYMS = json.loads(Path(__file__).with_name("synonyms.json").read_text())


def normalize(text):
    plain = "".join(
        c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c)
    )
    return " ".join(SYNONYMS.get(word, word) for word in plain.split())


SEARCH_FIELDS = {"code": 12, "model": 10, "model_component": 7, "name": 8, "brand": 5, "text": 1}
FACET_FIELDS = {"manufacturer", "stock_state", "category", "currency"}


def facet_key(field, value):
    return hashlib.sha256(f"{field}\0{value}".encode()).hexdigest()


class IndexClient:
    def __init__(self, http):
        self.http = http

    def request(self, method, path, *, allow_missing=False, **kwargs):
        try:
            response = self.http.request(method, path, **kwargs)
            if not (allow_missing and response.status_code == 404):
                response.raise_for_status()
            return response
        except httpx.HTTPError:
            raise CatalogError(
                "text_search_unavailable",
                "Use lookup_products or list_products while the index is unavailable",
                True,
            ) from None

    def import_documents(self, collection, documents):
        response = self.request(
            "POST",
            f"/collections/{collection}/documents/import",
            params={"action": "upsert"},
            content="\n".join(json.dumps(d) for d in documents),
        )
        try:
            rows = [json.loads(line) for line in response.text.splitlines()]
            if len(rows) != len(documents):
                raise ValueError()
            return [r.get("success") is True for r in rows]
        except (ValueError, AttributeError):
            raise CatalogError("index_invalid_response") from None

    def create(self, name):
        self.request(
            "POST",
            "/collections",
            json={
                "name": name,
                "fields": [
                    *({"name": field, "type": "string"} for field in SEARCH_FIELDS),
                    {"name": "verified", "type": "string[]", "facet": True},
                    {"name": "unknown_facets", "type": "string[]", "facet": True},
                    {"name": "revision", "type": "int64"},
                    {"name": "supplier", "type": "string", "facet": True},
                ],
            },
        )


def configured_client(settings):
    return IndexClient(
        httpx.Client(
            base_url=settings.typesense_url,
            headers={"X-TYPESENSE-API-KEY": settings.typesense_key.get_secret_value()},
            timeout=30,
        )
    )


def document(row, conn=None):
    item_id, data, revision = row
    if conn is not None:
        return documents(conn, [row])[0]
    text = " ".join(str(data.get(k) or "") for k in ["name", "sku", "manufacturer", "mpn", "ean"])
    text += " " + " ".join(
        str(o.get("value") or "") for o in data.get("observations", []) if o.get("state") == "known"
    )
    # Typesense joins hyphenated words. Keep exact compound tokens and expose complete model parts.
    identifiers = normalize(" ".join(data.get(k) or "" for k in ("name", "sku", "mpn")))
    parts = [
        part
        for part in re.findall(r"\b([a-z0-9]+)-(?=[a-z0-9])", identifiers)
        if not part.isalpha() and not part.isdigit()
    ]
    return {
        "id": item_id,
        "name": normalize(data.get("name") or ""),
        "code": normalize(" ".join(data.get(k) or "" for k in ("sku", "ean"))),
        "model": normalize(data.get("mpn") or ""),
        "model_component": " ".join(dict.fromkeys(parts)),
        "brand": normalize(data.get("manufacturer") or ""),
        "verified": [],
        "unknown_facets": sorted(FACET_FIELDS),
        "text": normalize(text),
        "revision": revision,
        "supplier": data.get("supplier", item_id.partition(":")[0]),
    }


def documents(conn, rows):
    from suppliermcp.catalog.repository import get_products

    views = {v.product_id: v for v in get_products(conn, [r[0] for r in rows])}
    facets = {}
    known_fields = {}
    for item_id, field, value in conn.execute(
        "SELECT item_id,field,value FROM catalog_values WHERE item_id=ANY(%s) "
        "AND field=ANY(%s) AND state='known'",
        (list(views), sorted(FACET_FIELDS)),
    ):
        facets.setdefault(item_id, []).append(facet_key(field, value))
        known_fields.setdefault(item_id, set()).add(field)
    labels = dict(
        conn.execute(
            "SELECT data->>'code',data->>'label' FROM source_schema WHERE kind='parameter'"
        )
    )
    categories = dict(
        conn.execute(
            "SELECT data->>'Id',data->>'Name' FROM source_schema WHERE kind IN ('SCategorySys','SCategorySys_El')"
        )
    )
    result = []
    for item_id, _, revision in rows:
        view = views[item_id]
        data = view.item.model_dump(mode="json")
        extra = [str(r.get("name") or "") for r in view.relationships]
        extra.extend(
            labels.get(o.field.removeprefix("parameter:"), "")
            for o in view.item.observations
            if o.field.startswith("parameter:")
        )
        extra.extend(
            categories.get(str(o.value), "") or ""
            for o in view.item.observations
            if o.interface == "mega" and o.field == "ScaId" and o.state == "known"
        )
        doc = document((item_id, data, revision))
        doc["verified"] = facets.get(item_id, [])
        doc["unknown_facets"] = sorted(FACET_FIELDS - known_fields.get(item_id, set()))
        doc["text"] += " " + normalize(" ".join(extra))
        result.append(doc)
    return result


def drain_outbox(conn, client):
    count = 0
    with conn.transaction():
        require_projected_catalog(conn)
        conn.execute("SELECT pg_advisory_xact_lock(91003)")
        # Share the publication lane so a snapshot cannot overtake a newer publication.
        conn.execute("SELECT pg_advisory_xact_lock(91002)")
        rows = conn.execute(
            "SELECT item_id,max(id) FROM index_outbox WHERE NOT done GROUP BY item_id ORDER BY min(id) LIMIT 200"
        ).fetchall()
        batch, events = [], []
        active = {
            r[0]: r
            for r in conn.execute(
                "SELECT id,data,revision FROM source_items WHERE id=ANY(%s) AND active",
                ([r[0] for r in rows],),
            )
        }
        for item_id, event_id in rows:
            row = active.get(item_id)
            if row:
                batch.append(row)
                events.append((item_id, event_id))
            else:
                client.request(
                    "DELETE",
                    f"/collections/{ALIAS}/documents/" + quote(item_id, safe=""),
                    params={"ignore_not_found": "true"},
                )
                count += conn.execute(
                    "UPDATE index_outbox SET done=true WHERE item_id=%s AND id<=%s AND NOT done",
                    (item_id, event_id),
                ).rowcount
        successes = client.import_documents(ALIAS, documents(conn, batch)) if batch else []
        for (item_id, event_id), success in zip(events, successes, strict=True):
            if success:
                count += conn.execute(
                    "UPDATE index_outbox SET done=true WHERE item_id=%s AND id<=%s AND NOT done",
                    (item_id, event_id),
                ).rowcount
    return count


def rebuild_index(conn, client):
    name = "catalog_" + secrets.token_hex(8)
    with conn.transaction():
        require_projected_catalog(conn)
        conn.execute("SELECT pg_advisory_xact_lock(91003)")
        conn.execute("SELECT pg_advisory_xact_lock(91002)")
        client.create(name)
        with conn.cursor(name="index_rebuild") as cursor:
            cursor.execute("SELECT id,data,revision FROM source_items WHERE active ORDER BY id")
            while rows := cursor.fetchmany(200):
                if not all(client.import_documents(name, documents(conn, rows))):
                    raise CatalogError("index_import_failed")
        client.request("PUT", f"/aliases/{ALIAS}", json={"collection_name": name})
        conn.execute("UPDATE index_outbox SET done=true WHERE NOT done")
    return name


def drain_pending(conn, client):
    total = 0
    while processed := drain_outbox(conn, client):
        total += processed
    return total
