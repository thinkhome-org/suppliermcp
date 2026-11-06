from decimal import Decimal

from suppliermcp.catalog.contracts import BatchManifest, Offer, SourceItem, utcnow
from suppliermcp.catalog.repository import get_product
from suppliermcp.sync.publish import publish, stage


def test_missing_price_in_new_export_keeps_old_evidence(conn):
    t = utcnow()
    item = SourceItem(supplier="mega", source_id="1", sku="1", name="One")
    m = BatchManifest(interface="mega", domain="catalog", complete=True, artifact_sha256="a")
    publish(
        conn,
        stage(
            conn,
            m,
            [
                item,
                Offer(item_id="mega:1", unit_net="10", fees_net="0", currency="CZK", evidence_at=t),
            ],
        ),
    )
    m2 = m.model_copy(update={"artifact_sha256": "b", "started_at": utcnow()})
    publish(conn, stage(conn, m2, [item, Offer(item_id="mega:1")]))
    offer = get_product(conn, "mega:1").offers[0]
    assert offer.unit_net == Decimal(10) and offer.evidence_at == t


async def test_direct_read_account_is_excluded_from_catalog_refresh(conn, tmp_path, monkeypatch):
    import pytest
    from psycopg.conninfo import make_conninfo

    from suppliermcp.access import Identity
    from suppliermcp.catalog.contracts import CatalogError
    from suppliermcp.config import Settings
    from suppliermcp.service import CatalogService
    from suppliermcp.sync import jobs

    item = SourceItem(supplier="ed", source_id="1", sku="SKU", name="Item")
    manifest = BatchManifest(
        interface="ed_private", domain="catalog", complete=True, artifact_sha256="ed"
    )
    publish(conn, stage(conn, manifest, [item]))
    settings = Settings(
        credentials={"fixture_account": ("login", "password")},
        database_url=make_conninfo(conn.info.dsn, password=conn.info.password),
        artifact_dir=tmp_path,
    )
    service = CatalogService(
        settings, Identity("issuer", "user", "client", frozenset({"catalog:read"}))
    )
    assert not jobs.build_adapters(settings)
    with pytest.raises(CatalogError, match="source_not_configured"):
        jobs.schedule_refresh("fixture_account", "price", ["SKU"], settings)
    calls = []
    monkeypatch.setattr(
        jobs, "schedule_refresh", lambda interface, *a, **kw: calls.append(interface)
    )
    [result] = await service.compare_offers(["ed:1"], refresh=True)
    assert "refresh_unavailable" in result.warnings and "refresh_pending" not in result.warnings
    assert not calls
    coverage = await service.get_catalog_status()
    assert set(coverage.interfaces) == {"ed_public", "ed_private", "mega"}
    assert all(not state["configured"] for state in coverage.interfaces.values())

    settings.credentials.update(
        {name: settings.credentials["fixture_account"] for name in ("ed_private", "mega")}
    )
    adapters = jobs.build_adapters(settings)
    try:
        assert set(adapters) == {"ed_private", "mega"}
    finally:
        for adapter in adapters.values():
            adapter.transport.client.close()
    [result] = await service.compare_offers(["ed:1"], refresh=True)
    assert calls == ["ed_private"] and "refresh_pending" in result.warnings
