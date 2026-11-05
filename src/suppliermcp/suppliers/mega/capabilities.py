"""Account-verified export contracts; undocumented capabilities stay unknown."""

from zoneinfo import ZoneInfo

from suppliermcp.catalog.contracts import CatalogError, utcnow


def require_window(contract, mode, now=None):
    if mode not in contract.get("modes", []) or not contract.get("timezone"):
        raise CatalogError("capability_not_verified")
    when = (now or utcnow()).astimezone(ZoneInfo(contract["timezone"]))
    if when.weekday() not in contract.get("days", []) or when.hour not in contract.get("hours", []):
        raise CatalogError("outside_supplier_window", retryable=True)
