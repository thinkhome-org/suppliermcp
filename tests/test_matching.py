from suppliermcp.catalog.contracts import Observation, SourceItem
from suppliermcp.catalog.matching import match_items


def item(supplier, pack=None, mpn="ABC"):
    obs = (
        []
        if pack is None
        else [
            Observation(
                interface="mega" if supplier == "mega" else "ed_public",
                endpoint="list",
                field="pack_count",
                value=pack,
            )
        ]
    )
    return SourceItem(
        supplier=supplier,
        source_id="1",
        sku="001",
        name="RAM",
        manufacturer="Acme",
        mpn=mpn,
        observations=obs,
    )


def test_matching_requires_packaging_evidence():
    assert match_items(item("ed"), item("mega")).verdict == "unresolved"
    assert match_items(item("ed", "1"), item("mega", "2")).verdict == "different"
    assert match_items(item("ed", "1"), item("mega", "1")).verdict == "same"
    assert match_items(item("ed", "1"), item("mega", "1", "ABCD")).verdict == "unresolved"
