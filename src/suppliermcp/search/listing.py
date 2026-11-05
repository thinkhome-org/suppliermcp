import hashlib
import json
import secrets
from datetime import timedelta
from decimal import Decimal

from psycopg.types.json import Jsonb

from suppliermcp.catalog.contracts import CatalogError, Page, ProductView, utcnow
from suppliermcp.catalog.repository import get_product, read_status
from suppliermcp.config import Settings

from .schema import catalog_schema, validate_filter


def matching_ids(conn, query):
    schema = catalog_schema(conn)
    conditions, params = [], []
    for f in query.filters:
        validate_filter(f, schema)
        expr = "(SELECT CASE WHEN v.state='known' THEN "
        numeric = schema[f.field]["type"] == "number"
        expr += "v.value::numeric" if numeric else "v.value"
        if f.operator == "in":
            expr += " = ANY(%s)"
            values = [Decimal(str(v)) for v in f.value] if numeric else f.value
            params.append(values)
        else:
            expr += " " + {"eq": "=", "gte": ">=", "lte": "<="}[f.operator] + " %s"
            params.append(Decimal(str(f.value)) if numeric else f.value)
        expr += " ELSE NULL END FROM catalog_values v WHERE v.item_id=s.id AND v.field=%s)"
        params.append(f.field)
        conditions.append(expr)
    expr = " AND ".join(conditions) or "true"
    base = "s.active"
    if query.supplier:
        base += " AND s.data->>'supplier'=%s"
        params.append(query.supplier)
    for bound, op in [(query.source_id_from, ">="), (query.source_id_to, "<")]:
        if bound is not None:
            base += " AND s.id " + op + " %s"
            params.append(bound)
    sql = f"SELECT s.id,({expr}) AS matched FROM source_items s WHERE {base} ORDER BY s.id"
    rows = conn.execute(sql, params).fetchall()
    return [i for i, m in rows if m is True], [i for i, m in rows if m is None]


def materialize(
    conn, products, coverage, principal, query_hash, total=None, unknown_total=0, settings=None
):
    settings = settings or Settings()
    result_id = secrets.token_urlsafe(24)
    expires = utcnow() + timedelta(seconds=settings.result_ttl_seconds)
    data = {
        "page_size": settings.page_size,
        "max_response_bytes": settings.max_response_bytes,
        "results": [p.model_dump(mode="json") for p in products],
        "total": len(products) if total is None else total,
        "unknown_total": unknown_total,
        "coverage": coverage.model_dump(mode="json"),
    }
    conn.execute("DELETE FROM query_results WHERE expires_at < now()")
    conn.execute(
        "INSERT INTO query_results VALUES (%s,%s,%s,%s,%s)",
        (result_id, principal, query_hash, expires, Jsonb(data)),
    )
    cursor = secrets.token_urlsafe(24)
    conn.execute("INSERT INTO query_cursors VALUES (%s,%s,0)", (cursor, result_id))
    return next_page(conn, cursor, principal)


def start_listing(conn, query, principal, settings=None):
    settings = settings or Settings()
    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        if not conn.execute("SELECT 1 FROM source_items LIMIT 1").fetchone():
            raise CatalogError("catalog_not_populated")
        if (
            query.currency
            and not conn.execute(
                "SELECT 1 FROM catalog_values WHERE field='currency' AND value=%s LIMIT 1",
                (query.currency,),
            ).fetchone()
        ):
            raise CatalogError("unsupported_currency")
        confirmed, unknown = matching_ids(conn, query)
        ids = confirmed if query.classification == "confirmed" else unknown
        if len(ids) > settings.max_result_rows:
            raise CatalogError(
                "result_too_large",
                json.dumps(
                    {
                        "count": len(ids),
                        "partitions": [
                            {
                                "source_id_from": ids[i],
                                "source_id_to": ids[i + settings.max_result_rows]
                                if i + settings.max_result_rows < len(ids)
                                else None,
                            }
                            for i in range(0, len(ids), settings.max_result_rows)
                        ],
                    }
                ),
            )
        products = [get_product(conn, i) for i in ids]
        if query.sort != "id":

            def price(p):
                eligible = [
                    o.unit_net
                    for o in p.offers
                    if o.currency == query.currency and o.unit_net is not None
                ]
                return min(eligible) if eligible else None

            present = [p for p in products if price(p) is not None]
            missing = [p for p in products if price(p) is None]
            products = sorted(present, key=price, reverse=query.sort == "price_desc") + missing
        coverage = read_status(conn)
        # Completeness is scoped to persisted account data and explicitly supported fields.
        coverage.complete = all(
            v.get("outcome") == "ok" for v in coverage.interfaces.values()
        ) and bool(coverage.interfaces)
        digest = hashlib.sha256(query.model_dump_json().encode()).hexdigest()
        return materialize(
            conn,
            products,
            coverage,
            principal,
            digest,
            unknown_total=len(unknown),
            settings=settings,
        )


def next_page(conn, cursor, principal, query_hash=None):
    row = conn.execute(
        "SELECT r.id,r.principal,r.expires_at,r.data,c.offset_value,r.query_hash FROM query_cursors c JOIN query_results r ON r.id=c.result_id WHERE c.id=%s",
        (cursor,),
    ).fetchone()
    if not row or row[1] != principal:
        raise CatalogError("result_not_found")
    result_id, _, expires, data, offset, stored_hash = row
    if query_hash is not None and query_hash != stored_hash:
        raise CatalogError("result_query_mismatch")
    if expires <= utcnow():
        raise CatalogError("result_expired")
    selected = []
    for item in data["results"][offset : offset + data.get("page_size", 20)]:
        if (
            len(json.dumps(selected + [item]).encode())
            > data.get("max_response_bytes", 256 * 1024) * 0.9
        ):
            if not selected:
                raise CatalogError("item_too_large", "Use get_product for the item details")
            break
        selected.append(item)
    continuation = None
    if offset + len(selected) < len(data["results"]):
        continuation = secrets.token_urlsafe(24)
        conn.execute(
            "INSERT INTO query_cursors VALUES (%s,%s,%s)",
            (continuation, result_id, offset + len(selected)),
        )
    return Page(
        results=[ProductView.model_validate(p) for p in selected],
        total=data["total"],
        unknown_total=data["unknown_total"],
        coverage=data["coverage"],
        next_cursor=continuation,
        snapshot_id=result_id,
        expires_at=expires,
    )
