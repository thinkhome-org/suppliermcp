from typing import Literal

from pydantic import Field

from suppliermcp.catalog.contracts import Model


class MatchDecision(Model):
    verdict: Literal["same", "different", "unresolved"]
    evidence: list[str] = Field(default_factory=list)


def _valid_gtin(value):
    return bool(
        value
        and len(value) in {8, 12, 13, 14}
        and value.isascii()
        and value.isdecimal()
        and value.strip("0")
        and sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(reversed(value))) % 10 == 0
    )


def match_items(left, right):
    def attrs(item):
        return {o.field: str(o.value) for o in item.observations if o.state == "known"}

    a, b = attrs(left), attrs(right)
    for field in ["pack_count", "condition", "capacity", "form_factor", "interface", "variant"]:
        if field in a and field in b and a[field] != b[field]:
            return MatchDecision(verdict="different", evidence=[field + "_conflict"])
    if (
        left.manufacturer
        and right.manufacturer
        and left.manufacturer.casefold() != right.manufacturer.casefold()
    ):
        return MatchDecision(verdict="different", evidence=["manufacturer_conflict"])
    if left.mpn and right.mpn and left.mpn != right.mpn:
        return MatchDecision(verdict="unresolved", evidence=["mpn_differs"])
    valid_left, valid_right = _valid_gtin(left.ean), _valid_gtin(right.ean)
    if valid_left and valid_right:
        if left.ean != right.ean:
            return MatchDecision(verdict="unresolved", evidence=["gtin_differs"])
        # GS1 identifies the trade item/packaging level; logistics cartons are not price units.
        return MatchDecision(verdict="same", evidence=["gtin"])
    same_mpn = bool(
        left.mpn
        and left.mpn == right.mpn
        and left.manufacturer
        and right.manufacturer
        and left.manufacturer.casefold() == right.manufacturer.casefold()
    )
    if not same_mpn or "pack_count" not in a or "pack_count" not in b:
        return MatchDecision(verdict="unresolved", evidence=["insufficient_identity_or_packaging"])
    return MatchDecision(verdict="same", evidence=["manufacturer_mpn", "pack_count"])
