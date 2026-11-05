from typing import Literal

from pydantic import Field

from suppliermcp.catalog.contracts import Model


class MatchDecision(Model):
    verdict: Literal["same", "different", "unresolved"]
    evidence: list[str] = Field(default_factory=list)


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
    same_ean = bool(left.ean and left.ean == right.ean)
    same_mpn = bool(
        left.mpn
        and left.mpn == right.mpn
        and left.manufacturer
        and right.manufacturer
        and left.manufacturer.casefold() == right.manufacturer.casefold()
    )
    if not (same_ean or same_mpn) or "pack_count" not in a or "pack_count" not in b:
        return MatchDecision(verdict="unresolved", evidence=["insufficient_identity_or_packaging"])
    return MatchDecision(
        verdict="same", evidence=["ean" if same_ean else "manufacturer_mpn", "pack_count"]
    )
