from decimal import Decimal

import pytest

from suppliermcp.catalog.contracts import BatchManifest, CatalogError, Offer, SourceItem
from suppliermcp.suppliers.mega.adapter import MegaAdapter


def parse(tmp_path, xml, endpoint="StoItemBase", mode="full", contract=None):
    p = tmp_path / "data.xml"
    p.write_text(xml)
    m = BatchManifest(
        interface="mega",
        domain="stock" if endpoint == "StoItemQtyFree" else "catalog",
        endpoint=endpoint,
        mode=mode,
        path=str(p),
    )
    rows = list(MegaAdapter(contracts=contract or {}).parse(m))
    return rows, m


def test_base_defaults_preserve_unknowns(tmp_path):
    rows, m = parse(
        tmp_path, '<Result><StoItem Id="1" Code="000123" Name="SSD" PriceDea="10.10"/></Result>'
    )
    item = next(r for r in rows if isinstance(r, SourceItem))
    offer = next(r for r in rows if isinstance(r, Offer))
    assert item.sku == "000123"
    assert next(o.value for o in item.observations if o.field == "QtyPack") == "1"
    assert offer.order_multiple is None and offer.currency is None
    assert offer.unit_net == Decimal("10.10") and offer.fees_net is None
    assert not m.complete  # a successfully parsed file is not proof of account coverage


def test_flag_mode_and_full_stock_contract(tmp_path):
    rows, m = parse(
        tmp_path,
        '<Result><StoItem Id="1" Code="001" QtyFreeIs="1"/></Result>',
        endpoint="StoItemQtyFree",
        contract={
            "StoItemQtyFree": {"stock_mode": "flag", "coverage": "complete", "stock_only": True}
        },
    )
    offer = next(r for r in rows if isinstance(r, Offer))
    assert offer.stock_qty is None and offer.stock_state == "in_stock"
    assert m.complete and m.stock_only


def test_missing_stock_in_delta_not_full(tmp_path):
    _, m = parse(
        tmp_path,
        "<Result/>",
        endpoint="StoItemQtyFree",
        mode="delta",
        contract={"StoItemQtyFree": {"coverage": "complete", "stock_only": True}},
    )
    assert not m.complete


def test_unknown_window_prevents_network_call():
    class Transport:
        def read(self, *args, **kw):
            pytest.fail("No read permitted before schedule capability is established")

    with pytest.raises(CatalogError, match="capability_not_verified"):
        MegaAdapter(transport=Transport()).fetch("catalog")


def test_missing_identity_and_invalid_schema(tmp_path):
    with pytest.raises(CatalogError, match="missing_product_identity"):
        parse(tmp_path, '<Result><StoItem Name="Broken"/></Result>')
    with pytest.raises(CatalogError, match="catalog_projection_unavailable"):
        parse(tmp_path, "<html><body>Error</body></html>")


def test_currency_export_and_mode_windows_are_selected_when_verified():
    contract = {
        "modes": ["full"],
        "timezone": "Europe/Prague",
        "windows": {"full": {"days": [0], "hours": [21]}},
    }
    adapter = MegaAdapter(contracts={"StoItemPriceOrdCur": contract})
    assert adapter.endpoints["price"] == "StoItemPriceOrdCur"
    assert adapter.discover().windows["StoItemPriceOrdCur"]["windows"] == contract["windows"]


def test_retry_revalidates_window_before_second_http_request(tmp_path, monkeypatch):
    from datetime import UTC, datetime

    import httpx

    from suppliermcp.suppliers.mega import capabilities
    from suppliermcp.suppliers.transport import SupplierTransport
    from suppliermcp.sync.artifacts import ArtifactStore

    clock = [datetime(2026, 11, 5, 20, 59, 59, tzinfo=UTC)]
    monkeypatch.setattr(capabilities, "utcnow", lambda: clock[0])
    calls = []

    def reply(request):
        calls.append(request)
        return httpx.Response(503 if len(calls) == 1 else 200, content=b"<Result/>")

    def sleep(_):
        clock[0] = datetime(2026, 11, 5, 21, 0, tzinfo=UTC)

    transport = SupplierTransport(
        {"i6ws.100mega.cz"},
        {"GetResult"},
        client=httpx.Client(transport=httpx.MockTransport(reply)),
        resolver=lambda host: ["8.8.8.8"],
        sleep=sleep,
    )
    adapter = MegaAdapter(
        transport,
        ArtifactStore(tmp_path),
        {
            "StoItemBase": {
                "modes": ["full"],
                "timezone": "Europe/Prague",
                "days": [3],
                "hours": [21],
            }
        },
    )
    with pytest.raises(CatalogError, match="outside_supplier_window"):
        adapter.fetch("catalog")
    assert len(calls) == 1


def test_worker_rejects_attsti_at_noon_even_with_permissive_local_window(monkeypatch):
    from datetime import UTC, datetime

    from suppliermcp.suppliers.mega import capabilities

    monkeypatch.setattr(capabilities, "utcnow", lambda: datetime(2026, 11, 6, 11, tzinfo=UTC))
    adapter = MegaAdapter(
        contracts={
            "AttSti": {
                "timezone": "Europe/Prague",
                "modes": ["full"],
                "days": list(range(7)),
                "hours": list(range(24)),
            }
        }
    )
    with pytest.raises(CatalogError, match="outside_supplier_window"):
        adapter.fetch_export("AttSti")


def test_window_file_must_belong_to_the_configured_login():
    from suppliermcp.suppliers.mega.capabilities import account_binding, account_exports

    opts = {
        "account_login_sha256": account_binding("first"),
        "exports": {"Test": {"modes": ["full"]}},
    }
    assert account_exports(opts, "second") == {}
    assert account_exports({"exports": opts["exports"]}, "first") == {}
    assert account_exports(opts, "first") == opts["exports"]
