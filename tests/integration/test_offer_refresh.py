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


async def test_identical_gtin_compares_suppliers_without_conflating_order_multiple(conn):
    import os

    from suppliermcp.access import Identity
    from suppliermcp.config import Settings
    from suppliermcp.service import CatalogService

    for supplier, interface, price, multiple in [
        ("ed", "ed_public", "10", "10"),
        ("mega", "mega", "12", "1"),
    ]:
        source = SourceItem(
            supplier=supplier,
            source_id="1",
            sku=supplier,
            name="Same trade item",
            manufacturer="Logitech",
            mpn="910-006477",
            ean="5099206099906",
        )
        publish(
            conn,
            stage(
                conn,
                BatchManifest(interface=interface, domain="catalog"),
                [
                    source,
                    Offer(
                        item_id=source.item_id,
                        currency="CZK",
                        unit_net=price,
                        fees_net="0",
                        order_multiple=multiple,
                    ),
                ],
            ),
        )
    service = CatalogService(
        Settings(
            database_url=os.getenv(
                "SUPPLIERMCP_TEST_DSN", "postgresql://test:test@localhost:55439/test"
            )
        ),
        Identity("issuer", "user", "client", frozenset({"catalog:read"})),
    )
    [one] = await service.compare_offers(["ed:1"], quantities={"ed:1": Decimal(1)})
    assert {v.item_id for v in one.offers} == {"ed:1", "mega:1"}
    assert {v.orderable_qty for v in one.offers} == {Decimal(1), Decimal(10)}
    assert one.last_known_winner is None
    assert "different_orderable_quantities_not_ranked" in one.warnings
    [ten] = await service.compare_offers(["ed:1"], quantities={"ed:1": Decimal(10)})
    assert {v.total_net for v in ten.offers} == {Decimal(100), Decimal(120)}
    assert ten.last_known_winner == "ed:1"
    assert ten.fresh_winner is None
