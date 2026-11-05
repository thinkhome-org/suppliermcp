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
        """<ProductList xmlns="urn:test"><Product><ProId>123</ProId><Code>001</Code><Name>SSD</Name><YourPrice>125.50</YourPrice><YourPriceWithFees>126.50</YourPriceWithFees><OnStock>true</OnStock><PriceCurrency>CZK</PriceCurrency></Product><Product><ProId>124</ProId><Code>002</Code><Name>RAM</Name><OnStock>false</OnStock></Product></ProductList>"""
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
        o
        for r in rows
        if isinstance(r, SourceItem)
        for o in r.observations
        if o.field == "DateAvailible"
    )
    assert obs.state == "missing"
    public = Observation(
        interface="ed_public", endpoint="getProductList", field="YourPrice", value="125.50"
    )
    assert merge_ed([public, *offer.observations])[0].value == "125.50"


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
    p.write_text("<Response><StatusCode>ERROR</StatusCode><ErrorText>secret</ErrorText></Response>")
    with pytest.raises(CatalogError) as e:
        list(
            EdPublicAdapter().parse(
                BatchManifest(interface="ed_public", domain="catalog", path=str(p))
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
                return b"<List><ProductCommodity><CommodityCode>A</CommodityCode></ProductCommodity><ProductCommodity><CommodityCode>B</CommodityCode></ProductCommodity></List>"
            if params.get("Comodities") == "B":
                raise CatalogError("supplier_unavailable")
            return b"<Products><Product><ProId>123</ProId><Code>001</Code><Name>SSD</Name></Product></Products>"

    adapter = EdPrivateAdapter(gateway=Gateway(), store=ArtifactStore(tmp_path))
    manifests, failures = adapter.enrichment()
    assert len(manifests) == 1 and failures == ["B"]
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
        "<Product><ProId>1</ProId><Code>A</Code><Description>"
        + ("x" * 100)
        + "</Description></Product>"
    )
    adapter = EdPublicAdapter()
    adapter.max_description_bytes = 50
    with pytest.raises(CatalogError, match="description_too_large"):
        list(adapter.parse(BatchManifest(interface="ed_public", domain="catalog", path=str(path))))
