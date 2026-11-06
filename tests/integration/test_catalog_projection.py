import json
import zipfile

import pytest

from suppliermcp.catalog.contracts import BatchManifest
from suppliermcp.catalog.repository import get_product
from suppliermcp.config import Settings
from suppliermcp.mcp.details import dictionary_page, product_page
from suppliermcp.search.index import documents
from suppliermcp.search.schema import catalog_schema
from suppliermcp.suppliers.ed.private import EdPrivateAdapter
from suppliermcp.suppliers.mega.adapter import MegaAdapter
from suppliermcp.sync.publish import publish, stage


@pytest.mark.parametrize("compressed", [False, True])
def test_only_projected_fields_reach_detail_filters_and_index(conn, tmp_path, compressed):
    private = "customer-address-canary"
    xml = f"""<Result Extra="{private}"><ShipTo><StoItem Id="bad" Code="bad" Name="{private}"/></ShipTo>
        <StoItem Id="7" Code="007" Name="router" Unknown="{private}">
        <ImgGal Id="5" Name="hero" Extra="{private}"><Street>{private}</Street></ImgGal>
        <ShipTo Street="{private}"><ImgGal Name="{private}"/></ShipTo></StoItem></Result>"""
    path = tmp_path / "catalog"
    if compressed:
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("catalog.xml", xml)
    else:
        path.write_text(xml)
    manifest = BatchManifest(
        interface="mega", endpoint="StoItemBase", domain="catalog", path=str(path)
    )
    publish(conn, stage(conn, manifest, MegaAdapter().parse(manifest)))
    assert conn.execute("SELECT id FROM source_items").fetchall() == [("mega:7",)]
    facts = get_product(conn, "mega:7").item.observations
    assert [o.value for o in facts if o.field == "ImgGal.Name"] == ["hero"]
    details = product_page(conn, "mega:7", "observations", None, "test", Settings())
    assert private not in json.dumps(details)
    assert "native:mega:Unknown" not in catalog_schema(conn)
    doc = documents(conn, [("mega:7", {}, 1)])[0]
    assert "hero" in doc["text"] and private not in doc["text"]


def test_ed_dictionary_and_serialized_nested_xml_are_projected(conn, tmp_path):
    path = tmp_path / "ed.xml"
    private = "customer-address-canary"
    path.write_text(f"""<ArrayOfProductComplete><ProductComplete><ProId>1</ProId><Code>A</Code>
    <ProductNavigatorDataList Extra="{private}"><ProductNavigatorData><AttributeCode>7</AttributeCode>
    <ValueCode>42</ValueCode><ShipTo><Street>{private}</Street></ShipTo></ProductNavigatorData>
    </ProductNavigatorDataList><ShipTo><ProductComplete><ProId>3</ProId><Code>bad</Code>
    </ProductComplete></ShipTo></ProductComplete></ArrayOfProductComplete>""")
    manifest = BatchManifest(
        interface="ed_private",
        endpoint="getProductCatalogueFullDownloadXML",
        domain="catalog",
        path=str(path),
    )
    adapter = EdPrivateAdapter()
    publish(conn, stage(conn, manifest, adapter.parse(manifest)))
    assert conn.execute("SELECT id FROM source_items").fetchall() == [("ed:1",)]
    view = get_product(conn, "ed:1")
    assert private not in view.model_dump_json()
    assert [o.value for o in view.item.observations if o.field == "attribute:7"] == ["42"]
    path.write_text(f"""<Navigator><ProductCategory Extra="{private}"><CategoryCode>2</CategoryCode>
    <CategoryName>Memory</CategoryName><ShipTo><Street>{private}</Street></ShipTo>
    </ProductCategory></Navigator>""")
    manifest = BatchManifest(
        interface="ed_private", endpoint="getNavigator", domain="schema", path=str(path)
    )
    publish(conn, stage(conn, manifest, adapter.parse(manifest)))
    page = dictionary_page(conn, None, None, "test", Settings())
    assert "Memory" in json.dumps(page) and private not in json.dumps(page)
