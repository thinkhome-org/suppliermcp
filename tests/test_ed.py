from datetime import timedelta
from decimal import Decimal

import pytest

from suppliermcp.catalog.contracts import (
    BatchManifest,
    CatalogError,
    Observation,
    Offer,
    SourceItem,
    utcnow,
)
from suppliermcp.suppliers.ed.authority import merge_ed
from suppliermcp.suppliers.ed.private import EdPrivateAdapter
from suppliermcp.suppliers.ed.public import EdPublicAdapter


def test_public_prices_and_out_of_stock(tmp_path):
    p = tmp_path / "public.xml"
    p.write_text(
        """<ProductList xmlns="http://www.elinkx.cz"><Product><ProId>123</ProId><Code>001</Code><Name>SSD</Name><YourPrice>125.50</YourPrice><YourPriceWithFees>126.50</YourPriceWithFees><OnStock>true</OnStock><PriceCurrency>CZK</PriceCurrency></Product><Product><ProId>124</ProId><Code>002</Code><Name>RAM</Name><OnStock>false</OnStock></Product></ProductList>"""
    )
    m = BatchManifest(
        interface="ed_public", domain="catalog", endpoint="getProductList", path=str(p)
    )
    rows = list(EdPublicAdapter().parse(m))
    assert {r.source_id for r in rows if isinstance(r, SourceItem)} == {"123", "124"}
    offer = next(r for r in rows if isinstance(r, Offer))
    assert offer.unit_net == Decimal("125.50") and offer.fees_net == Decimal("1.00")
    assert len(offer.observations) >= 3


def test_private_placeholders_and_unknown_date(tmp_path):
    p = tmp_path / "private.xml"
    p.write_text(
        "<ArrayOfProduct><Product><ProId>123</ProId><Code>001</Code><Name>SSD</Name><YourPrice>0</YourPrice><Vat>0</Vat><OnStock>false</OnStock><DateAvailible>1900-01-01</DateAvailible></Product></ArrayOfProduct>"
    )
    m = BatchManifest(
        interface="ed_private",
        domain="catalog",
        endpoint="getProductCatalogueDownloadXML",
        path=str(p),
    )
    rows = list(EdPrivateAdapter().parse(m))
    offer = next(r for r in rows if isinstance(r, Offer))
    assert offer.unit_net is None and offer.vat_percent is None
    obs = next(
        o for r in rows if isinstance(r, SourceItem) for o in r.observations if o.field == "OnStock"
    )
    assert obs.state == "placeholder"
    public = Observation(
        interface="ed_public", endpoint="getProductList", field="YourPrice", value="125.50"
    )
    assert merge_ed([public, *offer.observations])[0].value == "125.50"
    # The stock export, unlike the baseline, declares DateAvailible.
    p.write_text(
        "<ArrayOfProductShort><ProductShort><ProId>123</ProId><Code>001</Code><DateAvailible>1900-01-01</DateAvailible></ProductShort></ArrayOfProductShort>"
    )
    m.endpoint = "getProductCatalogueStockDownloadXML"
    item = next(r for r in EdPrivateAdapter().parse(m) if isinstance(r, SourceItem))
    assert next(o for o in item.observations if o.field == "DateAvailible").state == "missing"


def test_conflicting_prices_not_silently_resolved():
    a = Observation(interface="ed_public", endpoint="getProductList", field="YourPrice", value="10")
    b = a.model_copy(
        update={"interface": "ed_private", "endpoint": "getProductDetail", "value": "11"}
    )
    assert all(o.state == "conflict" for o in merge_ed([a, b]))
    stamp = utcnow()
    a.source_updated_at = stamp - timedelta(hours=1)
    b.source_updated_at = stamp
    assert merge_ed([a, b])[0].value == "11"


def test_private_failure_and_readiness():
    class Gateway:
        def call(self, method, **params):
            return b"<Response><StatusCode>DONE</StatusCode><IsReady>false</IsReady></Response>"

    adapter = EdPrivateAdapter(gateway=Gateway(), sleep=lambda n: None)
    with pytest.raises(CatalogError, match="export_not_ready"):
        adapter.fetch("catalog")


def test_supplier_error_does_not_echo_message(tmp_path):
    p = tmp_path / "error.xml"
    p.write_text(
        "<ArrayOfProduct><Product><ProId>1</ProId><Code>A</Code></Product><StatusCode>ERROR</StatusCode><ErrorText>secret</ErrorText></ArrayOfProduct>"
    )
    with pytest.raises(CatalogError, match="supplier_response_error") as e:
        list(
            EdPublicAdapter().parse(
                BatchManifest(
                    interface="ed_public", domain="catalog", endpoint="getProductList", path=str(p)
                )
            )
        )
    assert "secret" not in str(e.value)


def test_schema_is_preserved(tmp_path):
    from suppliermcp.catalog.contracts import SchemaRecord

    p = tmp_path / "schema.xml"
    p.write_text(
        "<Navigator><ProductCategory><CategoryCode>12</CategoryCode><CategoryName>Memory</CategoryName></ProductCategory></Navigator>"
    )
    rows = list(
        EdPrivateAdapter().parse(
            BatchManifest(
                interface="ed_private", domain="schema", endpoint="getNavigator", path=str(p)
            )
        )
    )
    assert isinstance(rows[0], SchemaRecord)
    assert rows[0].values["CategoryCode"] == "12"


def test_enrichment_partition_failure_keeps_other_partitions(tmp_path):
    from suppliermcp.sync.artifacts import ArtifactStore

    class Gateway:
        def call(self, method, **params):
            if method == "getProductCommodityList":
                return b"<List><CommodityCode>   </CommodityCode><CommodityCode> A </CommodityCode><CommodityCode>B</CommodityCode></List>"
            if params.get("Comodities") == "B":
                raise CatalogError("supplier_unavailable")
            assert params == {"onStock": False, "Comodities": "A"}
            self.attempts = getattr(self, "attempts", 0) + 1
            ready = "false" if self.attempts == 1 else "true"
            return f"<ProductListStatus><isReady>{ready}</isReady><url>https://ed.example/file</url></ProductListStatus>".encode()

    class Transport:
        def download(self, url, store, manifest):
            assert url == "https://ed.example/file"
            store.save([b"<ArrayOfProductComplete/>"], manifest)

    adapter = EdPrivateAdapter(
        gateway=Gateway(),
        store=ArtifactStore(tmp_path),
        transport=Transport(),
        sleep=lambda _: None,
    )
    manifests, failures = adapter.enrichment()
    manifests = list(manifests)
    assert len(manifests) == 1 and failures == ["B"]
    assert list(adapter.parse(manifests[0])) == []
    assert not manifests[0].complete


def test_relationship_and_navigator_evidence(tmp_path):
    from suppliermcp.catalog.contracts import SchemaRecord

    path = tmp_path / "relations.xml"
    path.write_text(
        "<ProductRelationList><ProductRealationParent><ProId>1</ProId><Code>A</Code><Childs><ProductRealationChild><ProId>2</ProId><Code>B</Code><Qty>1</Qty><RelTypeId>7</RelTypeId><RelTypeName>Accessory</RelTypeName></ProductRealationChild></Childs></ProductRealationParent></ProductRelationList>"
    )
    batch = BatchManifest(
        interface="ed_private", domain="schema", path=str(path), endpoint="getProductRelationList"
    )
    records = list(EdPrivateAdapter().parse(batch))
    assert any(
        isinstance(r, SchemaRecord) and r.kind == "relationship" and r.values["target_id"] == "ed:2"
        for r in records
    )


def test_description_budget(tmp_path):
    path = tmp_path / "oversized.xml"
    path.write_text(
        "<ArrayOfProduct><Product><ProId>1</ProId><Code>A</Code><Description>"
        + ("x" * 100)
        + "</Description></Product></ArrayOfProduct>"
    )
    adapter = EdPublicAdapter()
    adapter.max_description_bytes = 50
    with pytest.raises(CatalogError, match="description_too_large"):
        list(
            adapter.parse(
                BatchManifest(
                    interface="ed_public",
                    domain="catalog",
                    endpoint="getProductList",
                    path=str(path),
                )
            )
        )


@pytest.mark.parametrize(
    ("xml", "expected"),
    [
        ("<ArrayOfProductComplete><Unknown/></ArrayOfProductComplete>", "invalid_export"),
        ("<ArrayOfProductComplete>invalid</ArrayOfProductComplete>", "invalid_export"),
        (
            "<ProductListStatus><isReady>true</isReady></ProductListStatus>",
            "catalog_projection_unavailable",
        ),
    ],
)
def test_non_catalog_content_is_not_an_empty_commodity(tmp_path, xml, expected):
    path = tmp_path / "chunk.xml"
    path.write_text(xml)
    manifest = BatchManifest(
        interface="ed_private",
        endpoint="getProductCatalogueFullDownloadXML",
        domain="catalog",
        path=str(path),
    )
    with pytest.raises(CatalogError, match=expected):
        list(EdPrivateAdapter().parse(manifest))
