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
