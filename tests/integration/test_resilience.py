from datetime import timedelta
from decimal import Decimal

import pytest

from suppliermcp.catalog.contracts import BatchManifest, CatalogError, Offer, SourceItem, utcnow
from suppliermcp.catalog.offers import compare
from suppliermcp.catalog.repository import get_product
from suppliermcp.sync.jobs import run_refresh
from suppliermcp.sync.publish import publish, stage


def item(code="1"):
    return SourceItem(supplier="mega", source_id=code, sku="00" + code, name="Memory DDR5")


def test_interruption_recovery_and_cached_outage(conn):
    publish(
        conn,
        stage(
            conn,
            BatchManifest(
                interface="mega", domain="catalog", artifact_sha256="before", complete=True
            ),
            [item(), Offer(item_id="mega:1", unit_net="10")],
        ),
    )

    def interrupted():
        yield item("2")
        raise CatalogError("invalid_export")

    with pytest.raises(CatalogError):
        stage(conn, BatchManifest(interface="mega", domain="catalog"), interrupted())
    assert conn.execute("SELECT id FROM source_items").fetchall() == [("mega:1",)]
    publish(
        conn,
        stage(
            conn,
            BatchManifest(
                interface="mega", domain="catalog", mode="targeted", artifact_sha256="recover"
            ),
            [item("2")],
        ),
    )
    assert set(r[0] for r in conn.execute("SELECT id FROM source_items")) == {"mega:1", "mega:2"}

    class Offline:
        interface = "mega"

        def fetch(self, *args):
            raise CatalogError("supplier_unavailable")

    with pytest.raises(CatalogError):
        run_refresh(conn, Offline(), "price")
    offer = get_product(conn, "mega:1").offers[0]
    assert offer.unit_net == Decimal(10) and offer.refresh_failed
    result = compare([offer], Decimal(1), utcnow())
    assert not result.fresh_winner and result.offers[0].total_net is None


def test_stock_reconciliation_does_not_copy_price_between_domains(conn):
    publish(
        conn,
        stage(
            conn,
            BatchManifest(
                interface="mega", domain="catalog", artifact_sha256="base", complete=True
            ),
            [item(), item("2"), Offer(item_id="mega:1", unit_net="10")],
        ),
    )
    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="mega", domain="price", artifact_sha256="price"),
            [Offer(item_id="mega:1", unit_net="12")],
        ),
    )
    publish(
        conn,
        stage(
            conn,
            BatchManifest(
                interface="mega",
                domain="stock",
                artifact_sha256="stock",
                complete=True,
                stock_only=True,
            ),
            [item("2"), Offer(item_id="mega:2", stock_qty="5", stock_state="in_stock")],
        ),
    )
    prices = dict(
        conn.execute("SELECT domain,data->>'unit_net' FROM current_offers WHERE item_id='mega:1'")
    )
    assert prices == {"catalog": "10", "price": "12", "stock": None}
    assert get_product(conn, "mega:1").offers[0].stock_state == "out_of_stock"


def test_comparable_timestamp_ties_remain_conflicts(conn):
    timestamp = utcnow() - timedelta(minutes=1)
    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="ed_public", domain="catalog", artifact_sha256="p"),
            [
                SourceItem(supplier="ed", source_id="1", sku="one", name="Memory"),
                Offer(
                    item_id="ed:1",
                    unit_net="10",
                    source_updated_at=timestamp,
                    freshness_seconds=3600,
                ),
            ],
        ),
    )
    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="ed_private", domain="price", artifact_sha256="q"),
            [
                Offer(
                    item_id="ed:1",
                    unit_net="11",
                    source_updated_at=timestamp,
                    freshness_seconds=3600,
                )
            ],
        ),
    )
    assert get_product(conn, "ed:1").offers[0].unit_net is None


def test_private_baseline_runs_enrichment(conn):
    class Private:
        interface = "ed_private"
        store = None
        called = False

        def fetch(self, domain, codes):
            return BatchManifest(
                interface=self.interface,
                domain=domain,
                endpoint="baseline",
                artifact_sha256="base",
                complete=True,
            )

        def parse(self, manifest):
            if manifest.endpoint == "baseline":
                yield SourceItem(supplier="ed", source_id="1", sku="one", name="Memory")
            else:
                yield Offer(item_id="ed:1", unit_net="25")

        def enrichment(self):
            self.called = True
            return [
                BatchManifest(
                    interface=self.interface,
                    domain="catalog",
                    mode="targeted",
                    endpoint="full",
                    artifact_sha256="detail",
                )
            ], ["missing-commodity"]

    adapter = Private()
    run_refresh(conn, adapter, "catalog")
    assert adapter.called
    assert get_product(conn, "ed:1").offers[0].unit_net == 25
    assert (
        conn.execute(
            "SELECT data->>'outcome' FROM source_state WHERE interface='ed_private'"
        ).fetchone()[0]
        == "partial"
    )


@pytest.mark.parametrize("code", ["supplier_unauthorized", "supplier_timeout"])
def test_auth_and_timeout_leave_other_source_and_retained_data_queryable(conn, code):
    from suppliermcp.catalog.contracts import CatalogQuery, Identifier
    from suppliermcp.catalog.repository import read_status
    from suppliermcp.search.exact import lookup
    from suppliermcp.search.listing import start_listing

    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="mega", domain="catalog"),
            [item(), Offer(item_id="mega:1", unit_net="10")],
        ),
    )
    publish(
        conn,
        stage(
            conn,
            BatchManifest(interface="ed_public", domain="catalog"),
            [SourceItem(supplier="ed", source_id="2", sku="002", name="Other")],
        ),
    )

    class Failing:
        interface = "mega"

        def fetch(self, *args):
            raise CatalogError(code)

    with pytest.raises(CatalogError, match=code):
        run_refresh(conn, Failing(), "price")
    assert (
        lookup(conn, [Identifier(kind="sku", supplier="mega", value="001")]).entries[0]["status"]
        == "found"
    )
    assert start_listing(conn, CatalogQuery(supplier="ed"), "alice").total == 1
    assert get_product(conn, "mega:1").offers[0].unit_net == Decimal(10)
    assert read_status(conn, ["ed_public"]).interfaces["mega"]["outcome"] == "disabled"


def test_unavailable_index_keeps_published_outbox_repairable(conn):
    import httpx

    from suppliermcp.search.index import IndexClient, drain_pending

    revision = publish(
        conn, stage(conn, BatchManifest(interface="mega", domain="catalog"), [item()])
    )

    def offline(request):
        raise httpx.ConnectError("offline", request=request)

    with httpx.Client(base_url="http://index", transport=httpx.MockTransport(offline)) as client:
        with pytest.raises(CatalogError) as failure:
            drain_pending(conn, IndexClient(client))
        assert failure.value.code == "text_search_unavailable"
    assert get_product(conn, "mega:1").product_id == "mega:1"
    assert conn.execute("SELECT revision, done FROM index_outbox").fetchone() == (revision, False)

    def recovered(request):
        import json

        assert json.loads(request.content)["id"] == "mega:1"
        return httpx.Response(200, json={"success": True})

    with httpx.Client(base_url="http://index", transport=httpx.MockTransport(recovered)) as client:
        assert drain_pending(conn, IndexClient(client)) == 1
    assert conn.execute("SELECT done FROM index_outbox").fetchone() == (True,)


def test_direct_and_queued_refreshes_exclude_overlapping_export(conn):
    import psycopg

    class Busy:
        interface = "mega"
        endpoints = {"catalog": "StoItemBase"}

        def fetch(self, domain, codes):
            with psycopg.connect(
                conn.info.dsn, password=conn.info.password, autocommit=True
            ) as other:
                with pytest.raises(CatalogError, match="refresh_in_progress"):
                    run_refresh(other, self, domain)
            return BatchManifest(
                interface=self.interface, domain=domain, endpoint=self.endpoints[domain]
            )

        def parse(self, manifest):
            yield item()

    run_refresh(conn, Busy(), "catalog")


def test_simultaneous_outcome_updates_preserve_both_endpoints(conn):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from types import SimpleNamespace

    import psycopg

    from suppliermcp.sync.jobs import record_refresh_outcome

    barrier = Barrier(8)

    def write(number):
        with psycopg.connect(conn.info.dsn, password=conn.info.password, autocommit=True) as other:
            barrier.wait(timeout=15)
            record_refresh_outcome(
                other,
                SimpleNamespace(interface="mega"),
                "schema",
                str(number),
                utcnow(),
                "ok",
                None,
                number,
            )

    with ThreadPoolExecutor(max_workers=8) as workers:
        list(workers.map(write, range(8)))
    state = conn.execute("SELECT data FROM source_state WHERE interface='mega'").fetchone()[0]
    assert set(state["endpoints"]) == set(map(str, range(8)))


def test_scheduler_repeated_tick_preserves_each_pending_job(conn, tmp_path):
    import os

    from suppliermcp.config import Settings
    from suppliermcp.sync.jobs import create_app

    contracts = tmp_path / "contracts.json"
    contracts.write_text('{"ed_private":{"intervals_seconds":{"catalog":86400,"stock":7200}}}')
    settings = Settings(
        database_url=os.getenv(
            "SUPPLIERMCP_TEST_DSN", "postgresql://test:test@localhost:55439/test"
        ),
        source_contracts_path=contracts,
        artifact_dir=tmp_path / "artifacts",
        credentials={"ed_private": ("test", "test")},
    )
    app = create_app(settings)
    with app.open():
        if not conn.execute("SELECT to_regclass('procrastinate_jobs')").fetchone()[0]:
            app.schema_manager.apply_schema()
        conn.execute("TRUNCATE procrastinate_jobs CASCADE")
        try:
            tick = app.tasks["suppliermcp.tick"].func
            tick(timestamp=0)
            tick(timestamp=60)
            queued = conn.execute(
                "SELECT queueing_lock FROM procrastinate_jobs WHERE status='todo' ORDER BY queueing_lock"
            ).fetchall()
            assert queued == [
                ("ed_private:getProductCatalogueDownloadXML",),
                ("ed_private:getProductCatalogueStockDownloadXML",),
                ("index",),
            ]
        finally:
            conn.execute("TRUNCATE procrastinate_jobs CASCADE")
