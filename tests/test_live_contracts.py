from pathlib import Path

import httpx
import pytest

from suppliermcp.catalog.contracts import BatchManifest, CatalogError, SourceItem
from suppliermcp.suppliers.ed.gateway import EdGateway
from suppliermcp.suppliers.ed.public import EdPublicAdapter
from suppliermcp.suppliers.transport import SupplierTransport
from suppliermcp.sync.artifacts import ArtifactStore

PRODUCT = b"<ArrayOfProduct><Product><ProId>7</ProId><Code>0007</Code><Name>Memory</Name></Product></ArrayOfProduct>"


def test_ed_lowercase_export_status(tmp_path):
    def respond(request):
        if request.method == "POST":
            return httpx.Response(
                200,
                content=b"<Response><Status><StatusCode>DONE</StatusCode></Status><ProductListStatus><url>https://api.example/catalog</url><fileName>catalog.xml</fileName><isReady>true</isReady></ProductListStatus></Response>",
            )
        return httpx.Response(200, content=PRODUCT)

    transport = SupplierTransport(
        {"api.example"},
        {"getProductListDownloadXML", "getProductListDownloadZIP", "download"},
        client=httpx.Client(transport=httpx.MockTransport(respond)),
        resolver=lambda _: ["93.184.216.34"],
    )
    adapter = EdPublicAdapter(
        EdGateway(transport, "https://api.example/service", "test", "test"),
        ArtifactStore(tmp_path),
        transport,
    )
    manifest = adapter.fetch("catalog")
    assert Path(manifest.path).read_bytes() == PRODUCT
    assert [r.sku for r in adapter.parse(manifest) if isinstance(r, SourceItem)] == ["0007"]


def test_ed_not_ready_is_polled(tmp_path):
    class Gateway:
        calls = 0

        def call(self, method, **params):
            self.calls += 1
            return b"<Response><isReady>false</isReady></Response>" if self.calls == 1 else PRODUCT

    gateway = Gateway()
    adapter = EdPublicAdapter(gateway, ArtifactStore(tmp_path), sleep=lambda _: None)
    manifest = adapter.fetch("catalog")
    assert [r.sku for r in adapter.parse(manifest) if isinstance(r, SourceItem)] == ["0007"]


def test_ed_status_without_catalog_is_rejected(tmp_path):
    path = tmp_path / "status.xml"
    path.write_text("<Response><StatusCode>DONE</StatusCode></Response>")
    with pytest.raises(CatalogError, match="invalid_export"):
        list(
            EdPublicAdapter().parse(
                BatchManifest(interface="ed_public", domain="catalog", path=str(path))
            )
        )


class Chunks(httpx.SyncByteStream):
    def __init__(self, fail=False):
        self.fail = fail

    def __iter__(self):
        yield b"abc"
        if self.fail:
            raise httpx.ReadError("sensitive upstream message")
        yield b"def"


def test_partial_download_is_not_retained_as_complete(tmp_path):
    attempts = []

    def respond(request):
        attempts.append(1)
        return httpx.Response(200, stream=Chunks(fail=len(attempts) == 1))

    transport = SupplierTransport(
        {"api.example"},
        {"download"},
        client=httpx.Client(transport=httpx.MockTransport(respond)),
        resolver=lambda _: ["93.184.216.34"],
        sleep=lambda _: None,
    )
    manifest = BatchManifest(interface="ed_public", domain="catalog")
    path = transport.download("https://api.example/catalog", ArtifactStore(tmp_path), manifest)
    assert path.read_bytes() == b"abcdef"
    assert len(list(tmp_path.glob("*.data"))) == 1
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_streaming_limit_rejects_last_chunk(tmp_path):
    transport = SupplierTransport(
        {"api.example"},
        {"download"},
        client=httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, stream=Chunks()))
        ),
        resolver=lambda _: ["93.184.216.34"],
        max_bytes=5,
    )
    with pytest.raises(CatalogError, match="payload_too_large"):
        transport.download(
            "https://api.example/catalog",
            ArtifactStore(tmp_path),
            BatchManifest(interface="ed_public", domain="catalog"),
        )
    assert not list(tmp_path.glob("*.data"))
    assert not list(tmp_path.glob("*.json"))


def test_mega_price_currency_and_nested_evidence(tmp_path):
    from suppliermcp.catalog.contracts import Offer
    from suppliermcp.suppliers.mega.adapter import MegaAdapter

    p = tmp_path / "price.xml"
    p.write_text(
        '<Result CurCode="CZK"><StoItem Id="7" Code="0007" PriceOrd="123.45" PriceRef="2" PriceRef2="0" EAN="0012345678901"><Extra Id="a" Value="one"/><Extra Id="b" Value="two"/></StoItem></Result>'
    )
    m = BatchManifest(interface="mega", domain="price", endpoint="StoItemPriceOrdCur", path=str(p))
    rows = list(MegaAdapter().parse(m))
    offer = next(r for r in rows if isinstance(r, Offer))
    assert str(offer.unit_net) == "123.45" and offer.currency == "CZK"
    assert offer.fees_net == 2
    item = next(r for r in rows if isinstance(r, SourceItem))
    assert item.ean == "0012345678901"
    assert {o.value for o in item.observations if o.field == "Extra.Value"} == {"one", "two"}


def test_mega_row_parameters_and_relationships(tmp_path):
    from suppliermcp.catalog.contracts import SchemaRecord
    from suppliermcp.suppliers.mega.adapter import MegaAdapter

    p = tmp_path / "params.xml"
    p.write_text(
        '<Result><Row Id="a" StiId="7" StiCode="0007" CpaId="42" Name="Color" Value="red"/><Row Id="b" StiId="7" StiCode="0007" CpaId="42" Name="Color" Value="blue"/></Result>'
    )
    m = BatchManifest(interface="mega", domain="schema", endpoint="CpsStiVal", path=str(p))
    rows = list(MegaAdapter().parse(m))
    facts = [r for r in rows if isinstance(r, SchemaRecord) and r.kind == "product_facts"]
    assert len(facts) == 2
    assert {
        o["value"] for r in facts for o in r.values["observations"] if o["field"] == "parameter:42"
    } == {"red", "blue"}
    p.write_text(
        '<Result><StiRelation Id="1" StiId="7" StiIdR="8" SreId="2" SreName="Accessory"/></Result>'
    )
    m.endpoint = "StiRelation"
    rel = next(
        r
        for r in MegaAdapter().parse(m)
        if isinstance(r, SchemaRecord) and r.kind == "relationship"
    )
    assert rel.values["item_id"] == "mega:7" and rel.values["target_id"] == "mega:8"


def test_mega_mode_specific_window():
    from datetime import UTC, datetime

    from suppliermcp.suppliers.mega.capabilities import require_window

    contract = {
        "modes": ["full", "targeted"],
        "timezone": "Europe/Prague",
        "windows": {"full": {"days": [3], "hours": [21]}, "targeted": {"days": [3], "hours": [17]}},
    }
    at = datetime(2026, 11, 5, 16, 0, tzinfo=UTC)
    require_window(contract, "targeted", at)
    with pytest.raises(CatalogError, match="outside_supplier_window"):
        require_window(contract, "full", at)


def test_mega_capability_table_and_malformed_input():
    from suppliermcp.suppliers.mega import capabilities

    days = "".join(f'<span class="enabled">{i:02}</span>' for i in range(1, 8))
    hours = "".join(
        f'<span class="{"enabled" if i == 21 else "disabled"}">{i:02}</span>'
        for i in [*range(1, 24), 0]
    )
    cell = "<td>" + days + hours + "</td>"
    html = (
        '<html><table id="infotable"><tr><td><nobr>StoItemBase</nobr></td><td/>'
        + cell * 3
        + "<td>Products</td></tr></table></html>"
    ).encode()
    result = capabilities.parse_capabilities(html)
    assert result["StoItemBase"]["windows"]["full"]["hours"] == [21]
    assert result["StoItemBase"]["windows"]["full"]["days"] == list(range(7))
    with pytest.raises(CatalogError, match="invalid_capabilities"):
        capabilities.parse_capabilities(b"<html>Login required</html>")


def test_product_export_fetch_and_business_export_denial(tmp_path):
    from suppliermcp.suppliers.mega.adapter import MegaAdapter

    def respond(request):
        assert request.url.params["resultType"] == "CpsStiVal"
        assert request.url.params["code"] == "0007"
        return httpx.Response(
            200, content=b'<Result><Row StiId="7" CpaId="42" Value="red"/></Result>'
        )

    transport = SupplierTransport(
        {"api.example"},
        {"GetResultByCode"},
        client=httpx.Client(transport=httpx.MockTransport(respond)),
        resolver=lambda _: ["93.184.216.34"],
    )
    contract = {
        "modes": ["targeted"],
        "timezone": "Europe/Prague",
        "days": list(range(7)),
        "hours": list(range(24)),
    }
    adapter = MegaAdapter(
        transport, ArtifactStore(tmp_path), {"CpsStiVal": contract}, base_url="https://api.example"
    )
    manifest = adapter.fetch_export("CpsStiVal", codes=["0007"])
    assert manifest.endpoint == "CpsStiVal" and manifest.authoritative_identity is False
    assert list(adapter.parse(manifest))[0].values["item_id"] == "mega:7"
    with pytest.raises(CatalogError, match="operation_not_allowed"):
        adapter.fetch_export("Order")


def test_mega_disabled_method_has_empty_permission_cell():
    from suppliermcp.suppliers.mega.capabilities import parse_capabilities

    html = b'<html><table id="infotable"><tr><td><nobr>CpsSti</nobr></td><td/><td class="disabled">|01|02|03|04|05|06|07|<br/>|01|02|03|04|05|06|07|08|09|10|11|12|<br/>|13|14|15|16|17|18|19|20|21|22|23|00|<br/></td><td class="disabled">|01|02|03|04|05|06|07|<br/>|01|02|03|04|05|06|07|08|09|10|11|12|<br/>|13|14|15|16|17|18|19|20|21|22|23|00|<br/></td><td class="disabled">|01|02|03|04|05|06|07|<br/>|01|02|03|04|05|06|07|08|09|10|11|12|<br/>|13|14|15|16|17|18|19|20|21|22|23|00|<br/></td><td>Parameters</td></tr></table></html>'
    result = parse_capabilities(html)
    assert result["CpsSti"]["modes"] == []


def test_tree_product_placeholder_is_not_an_invalid_identity(tmp_path):
    from suppliermcp.catalog.contracts import SchemaRecord
    from suppliermcp.suppliers.mega.adapter import MegaAdapter

    p = tmp_path / "tree.xml"
    p.write_text('<Result><SPresentTree Id="42" Name="Memory"><StoItem/></SPresentTree></Result>')
    m = BatchManifest(interface="mega", domain="schema", endpoint="SPresentTree", path=str(p))
    rows = list(MegaAdapter().parse(m))
    assert isinstance(rows[0], SchemaRecord) and rows[0].values["Name"] == "Memory"


def test_sparse_and_special_product_exports_preserve_all_facts(tmp_path):
    from suppliermcp.suppliers.mega.adapter import MegaAdapter

    p = tmp_path / "extra.xml"
    m = BatchManifest(interface="mega", domain="schema", endpoint="X-LMStiPacking", path=str(p))
    p.write_text(
        '<Result><StoItem Id="7" Kod="0007" IdBaleni="1" Vaha="2"/><StoItem Id="7" Kod="0007" IdBaleni="2" Vaha="3"/></Result>'
    )
    rows = list(MegaAdapter().parse(m))
    assert len(rows) == 2 and all(r.kind == "product_facts" for r in rows)
    assert {o["value"] for r in rows for o in r.values["observations"] if o["field"] == "Vaha"} == {
        "2",
        "3",
    }
    p.write_text("<Result><StoItem/></Result>")
    assert list(MegaAdapter().parse(m)) == []


def test_shop_export_preserves_sku_join_and_nested_fields(tmp_path):
    from suppliermcp.suppliers.mega.adapter import MegaAdapter

    p = tmp_path / "shop.xml"
    p.write_text(
        "<SHOP><SHOPITEM><CODE>0007</CODE><NAME>Memory</NAME><PARAMETERS><PARAMETER><NAME>Color</NAME><VALUE>red</VALUE></PARAMETER></PARAMETERS></SHOPITEM></SHOP>"
    )
    m = BatchManifest(interface="mega", domain="schema", endpoint="StoItemShoptet_El", path=str(p))
    rows = list(MegaAdapter().parse(m))
    assert rows[0].values["sku"] == "0007"
    assert any(o["value"] == "red" for o in rows[0].values["observations"])
