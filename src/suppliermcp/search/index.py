"""Rebuildable index; PostgreSQL remains authoritative."""

import json
import secrets
import unicodedata
from pathlib import Path
from urllib.parse import quote

import httpx

from suppliermcp.catalog.contracts import CatalogError

ALIAS = "supplier_catalog"
SYNONYMS = json.loads(Path(__file__).with_name("synonyms.json").read_text())


def normalize(text):
    plain = "".join(
        c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c)
    )
    return " ".join(SYNONYMS.get(word, word) for word in plain.split())


class IndexClient:
    def __init__(self, http):
        self.http = http

    def request(self, method, path, **kwargs):
        try:
            response = self.http.request(method, path, **kwargs)
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
                    {"name": "text", "type": "string"},
                    {"name": "revision", "type": "int64"},
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
        from suppliermcp.catalog.repository import get_product

        data = get_product(conn, item_id).item.model_dump(mode="json")
    text = " ".join(str(data.get(k) or "") for k in ["name", "sku", "manufacturer", "mpn", "ean"])
    text += " " + " ".join(
        str(o.get("value") or "") for o in data.get("observations", []) if o.get("state") == "known"
    )
    return {"id": item_id, "text": normalize(text), "revision": revision}


def drain_outbox(conn, client):
    count = 0
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(91003)")
        # Share the publication lane so a snapshot cannot overtake a newer publication.
        conn.execute("SELECT pg_advisory_xact_lock(91002)")
        rows = conn.execute(
            "SELECT item_id,max(id) FROM index_outbox WHERE NOT done GROUP BY item_id ORDER BY min(id) LIMIT 200"
        ).fetchall()
        documents, events = [], []
        for item_id, event_id in rows:
            row = conn.execute(
                "SELECT id,data,revision FROM source_items WHERE id=%s AND active", (item_id,)
            ).fetchone()
            if row:
                documents.append(document(row, conn=conn))
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
        successes = client.import_documents(ALIAS, documents) if documents else []
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
        conn.execute("SELECT pg_advisory_xact_lock(91003)")
        conn.execute("SELECT pg_advisory_xact_lock(91002)")
        client.create(name)
        with conn.cursor(name="index_rebuild") as cursor:
            cursor.execute("SELECT id,data,revision FROM source_items WHERE active ORDER BY id")
            while rows := cursor.fetchmany(200):
                if not all(client.import_documents(name, [document(r, conn=conn) for r in rows])):
                    raise CatalogError("index_import_failed")
        client.request("PUT", f"/aliases/{ALIAS}", json={"collection_name": name})
        conn.execute("UPDATE index_outbox SET done=true WHERE NOT done")
    return name


def drain_pending(conn, client):
    total = 0
    while processed := drain_outbox(conn, client):
        total += processed
    return total
