"""Run authenticated supplier reads and retain only operation-level acceptance evidence."""

import argparse
import asyncio
import fnmatch
import json
import os
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

from suppliermcp.access import Identity
from suppliermcp.catalog.contracts import CatalogError
from suppliermcp.config import Settings
from suppliermcp.suppliers.mega.capabilities import (
    account_exports,
    next_window,
    verified_export_window,
)
from suppliermcp.suppliers.reads import OperationReader
from suppliermcp.suppliers.registry import operation_inventory


def next_allowed(spec, reader, now):
    credentials = reader.settings.credentials.get("mega")
    if not credentials:
        return None
    local = account_exports(
        reader.contracts.get("mega", {}), credentials[0].get_secret_value()
    ).get(spec.name, {})
    start = next_window(verified_export_window(spec, local), spec.mode, now)
    return start.isoformat() if start else None


def probe_arguments(spec, now):
    # Explicit dummy selectors make an absent-record response distinguishable from a real detail.
    scalar = {
        "int": 0,
        "string": "0",
        "dateTime": now.isoformat(),
        "boolean": True,
        "ProductNavigatorFilter": {},
    }
    args = {
        f.name: scalar[f.xsd_type] for f in spec.inputs if f.required or f.name.endswith("Symbol")
    }
    selected = {
        "dateFrom": now.date().isoformat(),
        "dateTo": now.date().isoformat(),
        "from": (now - timedelta(minutes=1)).isoformat(),
        "to": now.isoformat(),
        "encoding": "utf-8",
        "transformation": "INVOICEOLD" if "Invoice" in spec.name else "EDLINKOLDXML",
        "fileFormat": "XML",
    }
    args.update({k: v for k, v in selected.items() if k in {f.name for f in spec.inputs}})
    return args


def classify(spec, result):
    if result.truncated:
        return (
            "verified_nonempty"
            if any(is_data(spec, f.path) for f in result.fields)
            else "verified_response_page"
        )
    return (
        "verified_nonempty"
        if any(is_data(spec, f.path) for f in result.fields)
        else "verified_empty"
    )


def is_data(spec, path):
    parts = path.split("/")
    if spec.interface == "mega":
        return len(parts) > 2
    if spec.interface.startswith("ed_"):
        return not any(
            p.split("[")[0] in {"Status", "AddressId", "Count", "GeneratedDate", "ErrorText"}
            for p in parts
        )
    return True


async def probe(reader, spec, args, shape, dual_scope):
    now = datetime.now(UTC)
    scopes = {"catalog:read", "documents:read"} if dual_scope else {spec.scope}
    identity = Identity("local-acceptance", "account-operator", "local-reader", frozenset(scopes))
    row = {
        "observed_at": now.isoformat(timespec="seconds"),
        "interface": spec.interface,
        "mode": spec.mode,
        "scope": spec.scope,
        "both_scopes": dual_scope,
        "input": shape,
        "max_download_bytes": reader.settings.max_download_bytes,
        "max_expanded_bytes": reader.settings.max_expanded_bytes,
    }
    try:
        result = await reader.read_operation(identity, spec.operation_id, args)
        row["outcome"] = classify(spec, result)
        row["catalog_projection"] = result.catalog_projection
        row["more_pages"] = result.truncated
    except CatalogError as exc:
        row["outcome"] = exc.code
        if exc.code == "outside_supplier_window":
            row["next_allowed_utc"] = next_allowed(spec, reader, now)
    # Never copy upstream exceptions, URLs, arguments, fields or cursors into evidence.
    except Exception as exc:
        row["outcome"] = "client_error"
        row["error_type"] = type(exc).__name__
    return row


def save(path, rows):
    import tempfile

    with tempfile.NamedTemporaryFile(dir=path.parent, mode="w", delete=False) as handle:
        temp = Path(handle.name)
        try:
            json.dump({"operations": rows}, handle, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)


async def run(settings, options, fixtures):
    reader = OperationReader(settings)
    rows = json.loads(options.output.read_text())["operations"] if options.output.exists() else {}
    selected = [
        s
        for s in operation_inventory()
        if s.effect == "read"
        and any(fnmatch.fnmatchcase(s.operation_id, p) for p in options.operation)
        and (not options.status or rows.get(s.operation_id, {}).get("outcome") in options.status)
    ]
    if not selected:
        raise SystemExit("No matching reviewed operations")

    async def one(s):
        supplied = s.operation_id in fixtures
        args = fixtures[s.operation_id] if supplied else probe_arguments(s, datetime.now(UTC))
        row = await probe(
            reader,
            s,
            args,
            "operator_fixture" if supplied else "generated_read_only",
            options.both_scopes,
        )
        rows[s.operation_id] = row
        save(options.output, rows)

    for i in range(0, len(selected), options.concurrency):
        await asyncio.gather(*(one(s) for s in selected[i : i + options.concurrency]))
    print(dict(Counter(row["outcome"] for row in rows.values())))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument(
        "--operation", action="append", help="Operation ID or shell pattern; repeat to combine"
    )
    p.add_argument("--status", action="append", help="Retry only IDs with this saved outcome")
    p.add_argument(
        "--arguments-file", type=Path, help="Local JSON mapping operation IDs to supplier arguments"
    )
    p.add_argument(
        "--both-scopes",
        action="store_true",
        help="Exercise a separately authorized both-scope identity",
    )
    p.add_argument("--concurrency", type=int, choices=(1, 2, 3, 4), default=2)
    p.add_argument("--wire-mib", type=int, choices=range(1, 257), metavar="1..256", default=2)
    p.add_argument("--expanded-mib", type=int, choices=range(1, 1025), metavar="1..1024", default=8)
    opt = p.parse_args()
    opt.operation = opt.operation or ["*"]
    s = Settings.from_env()
    s.max_download_bytes = min(s.max_download_bytes, opt.wire_mib * 1024**2)
    s.max_expanded_bytes = min(s.max_expanded_bytes, opt.expanded_mib * 1024**2)
    s.max_response_bytes = min(s.max_response_bytes, 8192)
    fixtures = json.loads(opt.arguments_file.read_text()) if opt.arguments_file else {}
    asyncio.run(run(s, opt, fixtures))


if __name__ == "__main__":
    main()
