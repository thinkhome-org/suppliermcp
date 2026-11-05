import json
from pathlib import Path

import httpx

from suppliermcp.catalog.contracts import BatchManifest, Identifier, SourceItem
from suppliermcp.search.discovery import search
from suppliermcp.search.exact import lookup
from suppliermcp.search.index import IndexClient, rebuild_index
from suppliermcp.sync.publish import publish, stage


def test_curated_queries(conn):
    cases = json.loads(Path(__file__).with_name("queries.json").read_text())
    products = {
        c["id"]: SourceItem(supplier="mega", source_id=c["id"], sku="00" + c["id"], name=c["name"])
        for c in cases
    }
    publish(
        conn,
        stage(
            conn,
            BatchManifest(
                interface="mega", domain="catalog", artifact_sha256="evaluation", complete=True
            ),
            products.values(),
        ),
    )
    with httpx.Client(
        base_url="http://localhost:58109", headers={"X-TYPESENSE-API-KEY": "test-only"}
    ) as http:
        index = IndexClient(http)
        rebuild_index(conn, index)
        for case in cases:
            ids = {
                r.product_id for r in search(conn, index, case["query"], [], "evaluation").results
            }
            assert "mega:" + case["id"] in ids, case
            assert not ids.intersection("mega:" + v for v in case["exclude"]), case
            assert (
                lookup(
                    conn, [Identifier(kind="sku", supplier="mega", value="00" + case["id"])]
                ).entries[0]["status"]
                == "found"
            )
