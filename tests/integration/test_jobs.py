import pytest

from suppliermcp.catalog.contracts import BatchManifest, CatalogError, SourceItem
from suppliermcp.catalog.repository import get_product
from suppliermcp.config import Settings
from suppliermcp.sync.jobs import build_adapters, run_refresh


def test_no_configured_sources_make_no_adapters():
    assert build_adapters(Settings()) == {}


def test_refresh_publishes_and_failure_keeps_data(conn):
    class Adapter:
        interface = "mega"

        def fetch(self, domain, codes=None):
            return BatchManifest(
                interface="mega", domain=domain, complete=True, artifact_sha256="abc"
            )

        def parse(self, m):
            yield SourceItem(supplier="mega", source_id="1", sku="001", name="Item")

    adapter = Adapter()
    run_refresh(conn, adapter, "catalog")
    before = get_product(conn, "mega:1")

    def failure(*a, **kw):
        raise CatalogError("supplier_unavailable")

    adapter.fetch = failure
    with pytest.raises(CatalogError):
        run_refresh(conn, adapter, "catalog")
    assert get_product(conn, "mega:1") == before
    assert (
        conn.execute("SELECT data->>'outcome' FROM source_state WHERE interface='mega'").fetchone()[
            0
        ]
        == "supplier_unavailable"
    )


def test_endpoint_failure_preserves_other_refresh_states(conn):
    from suppliermcp.catalog.contracts import Offer
    from suppliermcp.sync import jobs

    class Adapter:
        interface = "mega"
        contracts = {}
        endpoints = {"catalog": "base", "price": "price"}

        def fetch_export(self, endpoint, codes=None):
            if endpoint == "parameters":
                raise CatalogError("supplier_unavailable")
            return BatchManifest(
                interface="mega", domain="catalog", endpoint=endpoint, complete=True
            )

        def parse(self, m):
            yield SourceItem(supplier="mega", source_id="1", sku="001", name="Item")
            yield Offer(item_id="mega:1", unit_net="10")

    jobs.run_export_refresh(conn, Adapter(), "base")
    with pytest.raises(CatalogError):
        jobs.run_export_refresh(conn, Adapter(), "parameters")
    assert get_product(conn, "mega:1").offers[0].refresh_failed is False
    state = conn.execute("SELECT data FROM source_state WHERE interface='mega'").fetchone()[0]
    assert state["endpoints"]["base"]["outcome"] == "ok"
    assert state["endpoints"]["parameters"]["outcome"] == "supplier_unavailable"
    assert state["domains"]["catalog"]["complete"] is True


def test_restricted_endpoint_records_next_allowed_time(conn, monkeypatch):
    from datetime import UTC, datetime

    from suppliermcp.suppliers.mega import capabilities
    from suppliermcp.suppliers.mega.adapter import MegaAdapter
    from suppliermcp.sync import jobs

    monkeypatch.setattr(capabilities, "utcnow", lambda: datetime(2026, 11, 6, 11, tzinfo=UTC))
    adapter = MegaAdapter(
        contracts={
            "AttSti": {
                "timezone": "Europe/Prague",
                "modes": ["full"],
                "windows": {"full": {"days": list(range(7)), "hours": list(range(24))}},
            }
        }
    )
    with pytest.raises(CatalogError, match="outside_supplier_window"):
        jobs.run_export_refresh(conn, adapter, "AttSti")
    state = conn.execute("SELECT data FROM source_state WHERE interface='mega'").fetchone()[0]
    assert state["endpoints"]["AttSti"]["next_allowed_at"] == "2026-11-06T20:00:00+00:00"
