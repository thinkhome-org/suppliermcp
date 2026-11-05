"""Principal-bound, immutable product evidence pages; JSON chunks are lossless."""

import json
import secrets
from datetime import timedelta

from psycopg.types.json import Jsonb

from suppliermcp.catalog.contracts import CatalogError, utcnow
from suppliermcp.catalog.repository import get_products

ATTACHMENT = r"(att|image|picture|photo|url|document|manual)"


def product_page(conn, product_id, section, cursor, principal, settings):
    if cursor:
        if product_id is not None or section is not None:
            raise CatalogError("result_query_mismatch")
        return _next(conn, cursor, principal)
    if not product_id:
        raise CatalogError("product_id_required")
    section = section or "overview"
    if section not in {"overview", "observations", "attachments", "relationships"}:
        raise CatalogError("invalid_detail_section")
    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        products = get_products(conn, [product_id], include_evidence=False)
        if not products:
            raise CatalogError("product_not_found")
        view = products[0]
        if section == "overview":
            counts = dict(
                conn.execute(
                    "SELECT 'observations',count(*) FROM observations WHERE item_id=%s UNION ALL SELECT 'relationships',count(*) FROM relationships WHERE item_id=%s UNION ALL SELECT 'attachments',count(*) FROM observations WHERE item_id=%s AND field ~* %s",
                    (product_id, product_id, product_id, ATTACHMENT),
                )
            )
            view.detail_continuation["sections"] = counts
            if (
                len(json.dumps(view.model_dump(mode="json")).encode())
                <= settings.max_response_bytes
            ):
                return view
        result_id = secrets.token_urlsafe(24)
        expires = utcnow() + timedelta(seconds=settings.result_ttl_seconds)
        data = {
            "kind": "detail",
            "product_id": product_id,
            "section": section,
            "count": 0,
            "page_size": settings.page_size,
            "max_response_bytes": settings.max_response_bytes,
        }
        conn.execute("DELETE FROM query_results WHERE expires_at<now()")
        conn.execute(
            "INSERT INTO query_results VALUES (%s,%s,%s,%s,%s)",
            (result_id, principal, "detail", expires, Jsonb(data)),
        )
        count = 0
        with conn.cursor(name="detail_records") as source:
            if section == "overview":
                source.execute("SELECT %s::jsonb", (Jsonb(view.model_dump(mode="json")),))
            elif section == "relationships":
                source.execute(
                    "SELECT data FROM relationships WHERE item_id=%s ORDER BY interface,endpoint,target_id,kind",
                    (product_id,),
                )
            else:
                sql = "SELECT data FROM observations WHERE item_id=%s"
                params = [product_id]
                if section == "attachments":
                    sql += " AND field ~* %s"
                    params.append(ATTACHMENT)
                source.execute(sql + " ORDER BY interface,endpoint,field,value_key", params)
            for record_index, (record,) in enumerate(source):
                raw = json.dumps(record, ensure_ascii=False)
                # ASCII escaping may expand one code point to 12 bytes in an envelope.
                width = max(1, (settings.max_response_bytes - 1500) // 12)
                chunks = (
                    [raw[i : i + width] for i in range(0, len(raw), width)]
                    if len(json.dumps(record).encode()) > settings.max_response_bytes - 1500
                    else None
                )
                records = (
                    (
                        {
                            "encoding": "json",
                            "record_index": record_index,
                            "chunk_index": i,
                            "chunk_count": len(chunks),
                            "text": chunk,
                        }
                        for i, chunk in enumerate(chunks)
                    )
                    if chunks
                    else iter([{"record_index": record_index, "data": record}])
                )
                for value in records:
                    conn.execute(
                        "INSERT INTO query_result_rows VALUES (%s,%s,%s)",
                        (result_id, count, Jsonb(value)),
                    )
                    count += 1
        data["count"] = count
        conn.execute("UPDATE query_results SET data=%s WHERE id=%s", (Jsonb(data), result_id))
        cursor = secrets.token_urlsafe(24)
        conn.execute("INSERT INTO query_cursors VALUES (%s,%s,0)", (cursor, result_id))
        return _next(conn, cursor, principal)


def _next(conn, cursor, principal):
    row = conn.execute(
        "SELECT r.id,r.principal,r.expires_at,r.data,c.offset_value FROM query_cursors c JOIN query_results r ON r.id=c.result_id WHERE c.id=%s",
        (cursor,),
    ).fetchone()
    if not row or row[1] != principal:
        raise CatalogError("result_not_found")
    result_id, _, expires, data, offset = row
    if expires <= utcnow():
        raise CatalogError("result_expired")
    if data.get("kind") != "detail":
        raise CatalogError("result_query_mismatch")
    continuation = secrets.token_urlsafe(24)
    result = {
        "product_id": data["product_id"],
        "section": data["section"],
        "records": [],
        "total_chunks": data["count"],
        "next_cursor": None,
        "snapshot_id": result_id,
        "expires_at": expires.isoformat(),
    }
    rows = conn.execute(
        "SELECT data FROM query_result_rows WHERE result_id=%s AND ordinal>=%s ORDER BY ordinal LIMIT %s",
        (result_id, offset, data["page_size"]),
    ).fetchall()
    for (record,) in rows:
        result["records"].append(record)
        result["next_cursor"] = (
            continuation if offset + len(result["records"]) < data["count"] else None
        )
        if len(json.dumps(result).encode()) > data["max_response_bytes"]:
            result["records"].pop()
            if not result["records"]:
                raise CatalogError("response_budget_too_small")
            result["next_cursor"] = continuation
            break
    if result["next_cursor"]:
        conn.execute(
            "INSERT INTO query_cursors VALUES (%s,%s,%s)",
            (continuation, result_id, offset + len(result["records"])),
        )
    return result
