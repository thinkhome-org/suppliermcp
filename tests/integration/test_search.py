import os

import httpx
import pytest

from suppliermcp.catalog.contracts import BatchManifest, CatalogError, Filter, SourceItem
from suppliermcp.search.discovery import search
from suppliermcp.search.index import ALIAS, IndexClient, drain_outbox, rebuild_index
from suppliermcp.sync.publish import publish, stage


@pytest.fixture
def index():
    with httpx.Client(
        base_url=os.getenv("SUPPLIERMCP_TEST_INDEX_URL", "http://localhost:58109"),
        headers={"X-TYPESENSE-API-KEY": "test-only"},
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


def test_worker_upgrades_v1_index(conn, index):
    from suppliermcp.config import Settings
    from suppliermcp.sync.jobs import create_app

    add(conn)
    index.request(
        "POST",
        "/collections",
        json={
            "name": "legacy",
            "fields": [
                {"name": "text", "type": "string"},
                {"name": "revision", "type": "int64"},
                {"name": "supplier", "type": "string", "facet": True},
            ],
        },
    )
    index.request("PUT", "/aliases/supplier_catalog", json={"collection_name": "legacy"})
    # A failed or interrupted deployment can leave an alias whose collection is gone.
    index.request(
        "POST",
        "/collections",
        json={"name": "retired", "fields": [{"name": "text", "type": "string"}]},
    )
    index.request("PUT", f"/aliases/{ALIAS}", json={"collection_name": "retired"})
    index.request("DELETE", "/collections/retired")
    settings = Settings(
        database_url=os.getenv(
            "SUPPLIERMCP_TEST_DSN", "postgresql://test:test@localhost:55439/test"
        ),
        typesense_url=os.getenv("SUPPLIERMCP_TEST_INDEX_URL", "http://localhost:58109"),
        typesense_key="test-only",
    )
    create_app(settings).tasks["suppliermcp.index"].func()
    assert index.request("GET", "/aliases/supplier_catalog").json()["collection_name"] == "legacy"
    fields = index.request("GET", f"/collections/{ALIAS}").json()["fields"]
    assert {"supplier", "verified", "name", "brand", "model", "code"} <= {f["name"] for f in fields}


def test_numeric_filter_returns_only_match_at_original_position_1001(conn, index):
    from suppliermcp.catalog.contracts import Offer

    rows = []
    for n in range(1001):
        item = SourceItem(supplier="mega", source_id=str(n), sku=str(n), name="SSD")
        rows.extend([item, Offer(item_id=item.item_id, stock_qty=n)])
    publish(
        conn,
        stage(
            conn, BatchManifest(interface="mega", domain="catalog", artifact_sha256="numeric"), rows
        ),
    )
    rebuild_index(conn, index)
    page = index.request(
        "GET",
        f"/collections/{ALIAS}/documents/search",
        params={"q": "ssd", "query_by": "text", "per_page": 250, "page": 5},
    ).json()
    last = page["hits"][0]["document"]["id"]
    result = search(
        conn,
        index,
        "ssd",
        [Filter(field="stock_qty", operator="eq", value=int(last.split(":")[1]))],
        "alice",
    )
    assert [p.product_id for p in result.results] == [last]


def test_model_match_outranks_description_mention(conn, index):
    from suppliermcp.catalog.contracts import Observation

    rows = [
        SourceItem(supplier="mega", source_id="device", sku="001", name="Router", mpn="M200"),
        SourceItem(
            supplier="mega",
            source_id="accessory",
            sku="002",
            name="Stand",
            observations=[
                Observation(
                    interface="mega",
                    endpoint="base",
                    field="description",
                    value="Compatible with M200",
                )
            ],
        ),
    ]
    publish(
        conn,
        stage(
            conn, BatchManifest(interface="mega", domain="catalog", artifact_sha256="rank"), rows
        ),
    )
    rebuild_index(conn, index)
    results = search(conn, index, "M200", [], "alice").results
    assert [row.product_id for row in results] == ["mega:device", "mega:accessory"]


def test_facet_prefilter_retains_unknown_rows(conn, index):
    rows = [
        SourceItem(supplier="mega", source_id=str(i), sku=str(i), name="SSD", manufacturer=brand)
        for i, brand in enumerate(["Acme", "Other", None])
    ]
    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="mega", domain="catalog", artifact_sha256="unknown-facet"),
            rows,
        ),
    )
    rebuild_index(conn, index)
    result = search(
        conn, index, "ssd", [Filter(field="manufacturer", operator="eq", value="Acme")], "alice"
    )
    assert [row.product_id for row in result.results] == ["mega:0"]
    assert result.unknown_total == 1
