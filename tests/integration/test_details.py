import json

import pytest

from suppliermcp.catalog.contracts import (
    BatchManifest,
    CatalogError,
    CatalogQuery,
    Observation,
    SourceItem,
)
from suppliermcp.config import Settings
from suppliermcp.sync.publish import publish, stage


def seed(conn):
    text = "Příliš žluťoučký 🐎" * 2000
    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="mega", domain="catalog"),
            [
                SourceItem(
                    supplier="mega",
                    source_id="1",
                    sku="001",
                    name="Product",
                    observations=[
                        Observation(
                            interface="mega", endpoint="base", field="Description", value=text
                        )
                    ],
                )
            ],
        ),
    )
    return text


def test_detail_chunks_are_complete_immutable_and_principal_bound(conn):
    from suppliermcp.mcp.details import product_page

    text = seed(conn)
    settings = Settings(max_response_bytes=4096, page_size=3)
    page = product_page(conn, "mega:1", "observations", None, "alice", settings)
    first_cursor = page["next_cursor"]
    assert first_cursor
    with pytest.raises(CatalogError, match="result_not_found"):
        product_page(conn, None, None, first_cursor, "bob", settings)
    with pytest.raises(CatalogError, match="result_query_mismatch"):
        product_page(conn, "mega:1", None, first_cursor, "alice", settings)
    conn.execute("UPDATE observations SET data=jsonb_set(data,'{value}','\"changed\"')")
    chunks = []
    while True:
        assert len(json.dumps(page).encode()) <= settings.max_response_bytes
        chunks.extend(page["records"])
        if not page["next_cursor"]:
            break
        page = product_page(conn, None, None, page["next_cursor"], "alice", settings)
    assert json.loads("".join(c["text"] for c in chunks))["value"] == text
    conn.execute("UPDATE query_results SET expires_at=now()-interval '1 second'")
    with pytest.raises(CatalogError, match="result_expired"):
        product_page(conn, None, None, first_cursor, "alice", settings)


def test_listing_stores_compact_rows_and_overview_compatible(conn):
    from suppliermcp.mcp.details import product_page
    from suppliermcp.search.listing import start_listing

    seed(conn)
    page = start_listing(conn, CatalogQuery(), "alice")
    assert not page.results[0].item.observations
    assert page.results[0].detail_continuation
    assert (
        "results"
        not in conn.execute(
            "SELECT data FROM query_results WHERE id=%s", (page.snapshot_id,)
        ).fetchone()[0]
    )
    assert (
        conn.execute(
            "SELECT count(*) FROM query_result_rows WHERE result_id=%s", (page.snapshot_id,)
        ).fetchone()[0]
        == 1
    )
    overview = product_page(conn, "mega:1", None, None, "alice", Settings())
    assert (
        overview.item.sku == "001" and overview.detail_continuation["sections"]["observations"] == 1
    )


def test_relationship_pages_are_duplicate_free(conn):
    from suppliermcp.mcp.details import product_page

    seed(conn)
    conn.execute(
        "INSERT INTO relationships(item_id,target_id,kind,data) SELECT 'mega:1','mega:'||i,'accessory',jsonb_build_object('target_id','mega:'||i) FROM generate_series(2,26) i"
    )
    settings = Settings(page_size=3)
    page = product_page(conn, "mega:1", "relationships", None, "alice", settings)
    seen = []
    while True:
        seen.extend(r["data"]["target_id"] for r in page["records"])
        if not page["next_cursor"]:
            break
        page = product_page(conn, None, None, page["next_cursor"], "alice", settings)
    assert len(seen) == len(set(seen)) == 25


def test_hundred_thousand_compact_rows(conn):
    from suppliermcp.search.listing import start_listing

    conn.execute(
        "INSERT INTO source_items(id,data,revision) SELECT 'mega:'||i,jsonb_build_object('supplier','mega','source_id',i::text,'sku',i::text,'name','Product'),1 FROM generate_series(1,100000) i"
    )
    page = start_listing(conn, CatalogQuery(), "alice")
    assert page.total == 100000 and len(page.results) == 20
    assert (
        conn.execute(
            "SELECT count(*) FROM query_result_rows WHERE result_id=%s", (page.snapshot_id,)
        ).fetchone()[0]
        == 100000
    )


def test_large_schema_has_complete_immutable_continuation(conn):
    from suppliermcp.search.schema import catalog_schema_page

    seed(conn)
    conn.execute(
        "INSERT INTO catalog_values(item_id,field,value,state,value_type) SELECT 'mega:1','native:mega:parameter:'||i,'x','known','text' FROM generate_series(1,300) i"
    )
    settings = Settings(max_response_bytes=4096)
    page = catalog_schema_page(conn, None, None, "alice", settings)
    fields = {}
    assert page.get("_continuation", {}).get("next_cursor")
    while True:
        assert len(json.dumps(page).encode()) <= 4096
        continuation = page.pop("_continuation", {})
        fields.update(page)
        if not continuation.get("next_cursor"):
            break
        page = catalog_schema_page(conn, None, continuation["next_cursor"], "alice", settings)
    assert all("native:mega:parameter:" + str(i) in fields for i in range(1, 301))
