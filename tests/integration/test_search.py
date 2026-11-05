import os

import httpx
import pytest

from suppliermcp.catalog.contracts import BatchManifest, CatalogError, Filter, SourceItem
from suppliermcp.search.discovery import search
from suppliermcp.search.index import IndexClient, drain_outbox, rebuild_index
from suppliermcp.sync.publish import publish, stage


@pytest.fixture
def index():
    with httpx.Client(
        base_url="http://localhost:58109", headers={"X-TYPESENSE-API-KEY": "test-only"}
    ) as http:
        for c in http.get("/collections").json():
            http.delete("/collections/" + c["name"])
        yield IndexClient(http)


def add(conn, name="Paměť DDR5 32GB", hash="one"):
    return publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="mega", domain="catalog", artifact_sha256=hash, complete=True),
            [SourceItem(supplier="mega", source_id="1", sku="001", name=name, manufacturer="Acme")],
        ),
    )


def test_rebuild_lag_filter_and_replay(conn, index):
    add(conn)
    first = rebuild_index(conn, index)
    assert search(conn, index, "pamet DDR5", [], "alice").results[0].product_id == "mega:1"
    add(conn, name="Memory DDR4 32GB", hash="two")
    result = search(
        conn, index, "DDR5", [Filter(field="manufacturer", operator="eq", value="Other")], "alice"
    )
    assert result.results == [] and result.coverage.complete is False
    assert "index_lag" in result.coverage.warnings
    assert drain_outbox(conn, index) == 1
    assert drain_outbox(conn, index) == 0
    assert not search(conn, index, "DDR5", [], "alice").results
    second = rebuild_index(conn, index)
    assert second != first
    conn.execute("UPDATE source_items SET active=false")
    conn.execute("INSERT INTO index_outbox(item_id,revision) VALUES ('mega:1',999)")
    drain_outbox(conn, index)
    assert not search(conn, index, "DDR4", [], "alice").results


def test_partial_import_keeps_pending(conn, index):
    add(conn)
    rebuild_index(conn, index)
    add(conn, hash="two")
    real = index.import_documents
    index.import_documents = lambda collection, documents: [False for _ in documents]
    assert drain_outbox(conn, index) == 0
    assert conn.execute("SELECT count(*) FROM index_outbox WHERE NOT done").fetchone()[0] == 1
    index.import_documents = real
    assert drain_outbox(conn, index) == 1


def test_search_outage_typed(conn):
    add(conn)
    with httpx.Client(base_url="http://localhost:1", timeout=0.1) as http:
        with pytest.raises(CatalogError) as error:
            search(conn, IndexClient(http), "memory", [], "alice")
    assert error.value.code == "text_search_unavailable"


@pytest.mark.parametrize("operator,value", [("eq", "ed"), ("in", ["ed"])])
def test_supplier_filter_precedes_candidate_limit(conn, index, operator, value):
    for supplier, count in [("ed", 1), ("mega", 1001)]:
        publish(
            conn,
            stage(
                conn,
                BatchManifest(
                    interface="ed_public" if supplier == "ed" else "mega",
                    domain="catalog",
                    artifact_sha256=supplier,
                    complete=True,
                ),
                [
                    SourceItem(supplier=supplier, source_id=str(n), sku=str(n), name="SSD")
                    for n in range(count)
                ],
            ),
        )
    rebuild_index(conn, index)
    result = search(
        conn, index, "ssd", [Filter(field="supplier", operator=operator, value=value)], "alice"
    )
    assert [p.product_id for p in result.results] == ["ed:0"]
    assert "candidate_scan_limited_to_1000" not in result.coverage.warnings


def test_worker_upgrades_index_without_supplier_field(conn, index):
    from suppliermcp.config import Settings
    from suppliermcp.sync.jobs import create_app

    add(conn)
    index.request(
        "POST",
        "/collections",
        json={
            "name": "legacy",
            "fields": [{"name": "text", "type": "string"}, {"name": "revision", "type": "int64"}],
        },
    )
    index.request("PUT", "/aliases/supplier_catalog", json={"collection_name": "legacy"})
    settings = Settings(
        database_url=os.getenv(
            "SUPPLIERMCP_TEST_DSN", "postgresql://test:test@localhost:55439/test"
        ),
        typesense_url="http://localhost:58109",
        typesense_key="test-only",
    )
    create_app(settings).tasks["suppliermcp.index"].func()
    fields = index.request("GET", "/collections/supplier_catalog").json()["fields"]
    assert any(f["name"] == "supplier" for f in fields)
