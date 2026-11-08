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


def test_valid_identical_gtin_proves_trade_item_without_invented_pack_count():
    left, right = item("ed"), item("mega")
    left.ean = right.ean = "5099206099906"
    decision = match_items(left, right)
    assert decision.verdict == "same"
    assert decision.evidence == ["gtin"]
    # Order multiples and logistics cartons do not change the identified trade item.
    for obj, field, value in [(left, "MultipleQuantity", "10"), (right, "QtyPack", "50")]:
        obj.observations.append(
            Observation(
                interface="ed_public" if obj is left else "mega",
                endpoint="list",
                field=field,
                value=value,
            )
        )
    assert match_items(left, right).verdict == "same"


def test_gtin_does_not_override_explicit_pack_variant_or_identity_conflicts():
    left, right = item("ed", "1"), item("mega", "2")
    left.ean = right.ean = "5099206099906"
    assert match_items(left, right).verdict == "different"
    right.observations = []
    right.mpn = "DIFFERENT"
    assert match_items(left, right).verdict == "unresolved"
    right.mpn = left.mpn
    right.manufacturer = "Other"
    assert match_items(left, right).verdict == "different"


def test_missing_invalid_or_different_gtin_keeps_packaging_gate():
    for a, b in [
        ("5099206099907", "5099206099907"),
        ("0000000000000", "0000000000000"),
        ("EAN", "EAN"),
        ("5099206099906", "8715946711270"),
    ]:
        left, right = item("ed"), item("mega")
        left.ean, right.ean = a, b
        assert match_items(left, right).verdict == "unresolved"


def test_different_valid_gtins_are_not_merged_by_mpn_and_pack_count():
    left, right = item("ed", "1"), item("mega", "1")
    left.ean, right.ean = "5099206099906", "8715946711270"
    assert match_items(left, right).verdict == "unresolved"
