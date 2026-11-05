"""Account-specific method windows; unknown permissions fail closed."""

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from defusedxml.ElementTree import fromstring

from suppliermcp.catalog.contracts import CatalogError, utcnow


def parse_capabilities(data: bytes) -> dict:
    try:
        root = fromstring(data, forbid_dtd=True)
        result = {}
        for row in root.findall('.//table[@id="infotable"]/tr'):
            cells = row.findall("td")
            if len(cells) != 6:
                continue
            names = [e.text for e in cells[0].findall("nobr")]
            windows = {}
            for mode, cell in zip(["full", "targeted", "delta"], cells[2:5], strict=True):
                spans = cell.findall("span")
                if (
                    not spans
                    and all(c.tag == "br" for c in cell)
                    and (cell.get("class") == "disabled" or not "".join(cell.itertext()).strip())
                ):
                    windows[mode] = {"days": [], "hours": []}
                    continue
                if (
                    len(spans) != 31
                    or [int(s.text) for s in spans[:7]] != list(range(1, 8))
                    or sorted(int(s.text) for s in spans[7:]) != list(range(24))
                ):
                    raise ValueError()
                if any(s.get("class") not in {"enabled", "disabled"} for s in spans):
                    raise ValueError()
                windows[mode] = {
                    "days": [int(s.text) - 1 for s in spans[:7] if s.get("class") == "enabled"],
                    "hours": [int(s.text) for s in spans[7:] if s.get("class") == "enabled"],
                }
            for name in names:
                if not name or name in result:
                    raise ValueError()
                result[name] = {
                    "modes": [m for m, w in windows.items() if w["days"] and w["hours"]],
                    "windows": windows,
                    "description": "".join(cells[5].itertext()).strip(),
                }
        if not result:
            raise ValueError()
        return result
    except Exception:
        raise CatalogError("invalid_capabilities") from None


def require_window(contract, mode, now=None):
    if mode not in contract.get("modes", []) or not contract.get("timezone"):
        raise CatalogError("capability_not_verified")
    try:
        when = (now or utcnow()).astimezone(ZoneInfo(contract["timezone"]))
    except ZoneInfoNotFoundError:
        raise CatalogError("capability_not_verified") from None
    window = contract.get("windows", {}).get(mode, contract)
    if when.weekday() not in window.get("days", []) or when.hour not in window.get("hours", []):
        raise CatalogError("outside_supplier_window", retryable=True)


def next_window(contract, mode, now=None):
    from datetime import timedelta

    start = now or utcnow()
    for hour in range(8 * 24):
        candidate = (
            start
            if hour == 0
            else (start + timedelta(hours=hour)).replace(minute=0, second=0, microsecond=0)
        )
        try:
            require_window(contract, mode, candidate)
            return candidate
        except CatalogError as error:
            if error.code != "outside_supplier_window":
                return None
    return None
