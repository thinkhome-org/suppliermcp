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


def document(row):
    item_id, data, revision = row
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
            "SELECT id,item_id FROM index_outbox WHERE NOT done ORDER BY id LIMIT 200"
        ).fetchall()
        if not rows:
            return 0
        for event_id, item_id in rows:
            row = conn.execute(
                "SELECT id,data,revision FROM source_items WHERE id=%s AND active", (item_id,)
            ).fetchone()
            if row:
                success = client.import_documents(ALIAS, [document(row)])[0]
            else:
                client.request(
                    "DELETE",
                    f"/collections/{ALIAS}/documents/" + quote(item_id, safe=""),
                    params={"ignore_not_found": "true"},
                )
                success = True
            if success:
                conn.execute("UPDATE index_outbox SET done=true WHERE id=%s", (event_id,))
                count += 1
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
                if not all(client.import_documents(name, [document(r) for r in rows])):
                    raise CatalogError("index_import_failed")
        client.request("PUT", f"/aliases/{ALIAS}", json={"collection_name": name})
        conn.execute("UPDATE index_outbox SET done=true WHERE NOT done")
    return name
