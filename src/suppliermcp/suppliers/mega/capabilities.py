"""Account-specific method windows; unknown permissions fail closed."""

import hashlib
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


def account_binding(login):
    return hashlib.sha256(("i6ws.100mega.cz\0" + login).encode()).hexdigest()


def account_exports(options, login):
    return (
        options.get("exports", {})
        if options.get("account_login_sha256") == account_binding(login)
        else {}
    )


def verified_export_window(spec, account):
    """Intersect ISO supplier weekdays with zero-based local Python weekdays."""
    if spec.mode not in account.get("modes", []) or account.get("timezone") != "Europe/Prague":
        return {}
    local = account.get("windows", {}).get(spec.mode, account)
    return {
        "modes": [spec.mode],
        "timezone": "Europe/Prague",
        "days": sorted({day - 1 for day in spec.days} & set(local.get("days", []))),
        "hours": sorted(set(spec.hours) & set(local.get("hours", []))),
    }


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


def refresh_account_contracts(settings, previous):
    """Replace the authenticated account's capabilities while keeping its offer mappings."""
    from suppliermcp.suppliers.transport import SupplierTransport

    credentials = settings.credentials.get("mega")
    if not credentials:
        raise CatalogError("source_not_configured")
    binding = account_binding(credentials[0].get_secret_value())
    if previous.get("mega", {}).get("account_login_sha256", binding) != binding:
        raise CatalogError("account_contract_mismatch")
    transport = SupplierTransport(
        {"i6ws.100mega.cz"},
        {"capabilities"},
        auth=tuple(v.get_secret_value() for v in credentials),
        max_bytes=4 * 1024**2,
    )
    try:
        current = parse_capabilities(
            transport.read(
                "GET", "https://i6ws.100mega.cz/ResultTypeInfo.ashx", endpoint="capabilities"
            )
        )
    finally:
        transport.client.close()
    old = previous.get("mega", {}).get("exports", {})
    exports = {
        name: old.get(name, {})
        | {"modes": row["modes"], "windows": row["windows"], "timezone": "Europe/Prague"}
        for name, row in current.items()
    }
    return previous | {
        "mega": previous.get("mega", {}) | {"account_login_sha256": binding, "exports": exports}
    }


def main():
    import argparse
    import json
    import os
    import tempfile
    from pathlib import Path

    from suppliermcp.config import Settings

    parser = argparse.ArgumentParser(description="Refresh 100MEGA account-specific read windows")
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--source",
        type=Path,
        help="Existing source-contracts JSON; defaults to the output file if present",
    )
    args = parser.parse_args()
    source = args.source or args.output
    previous = json.loads(source.read_text()) if source.exists() else {}
    current = refresh_account_contracts(Settings.from_env(), previous)
    with tempfile.NamedTemporaryFile(dir=args.output.parent, mode="w", delete=False) as handle:
        temp = Path(handle.name)
        try:
            json.dump(current, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            os.replace(temp, args.output)
        finally:
            temp.unlink(missing_ok=True)
    print(f"Verified {len(current['mega']['exports'])} export names")


if __name__ == "__main__":
    main()
