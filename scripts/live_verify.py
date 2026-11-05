"""Opt-in read-only live checks. Reports contain counts/statuses, never payloads or secrets."""

import argparse
import asyncio
import json
import os
import time
from pathlib import Path

import httpx
from fastmcp import Client

from suppliermcp.catalog.contracts import CatalogError, utcnow
from suppliermcp.suppliers.mega.exports import PRODUCT_EXPORTS


def failure(error):
    # Exception messages and upstream bodies may contain credentials or account URLs.
    return {"outcome": "failed", "error_type": type(error).__name__}


def product_export(endpoint):
    return endpoint in PRODUCT_EXPORTS


def unpack(result):
    data = result.structured_content
    return data.get("result", data)


async def verify(url, token):
    report = {"checked_at": utcnow().isoformat(), "checks": {}}
    checks = report["checks"]
    async with httpx.AsyncClient() as http:
        checks["unauthenticated_rejected"] = (await http.post(url)).status_code == 401
    async with Client(url, auth=token, timeout=120) as client:
        checks["tool_count"] = len(await client.list_tools())
        resources = await client.list_resources()
        checks["resource_count"] = len(resources)
        status = unpack(await client.call_tool("get_catalog_status", {}))
        report["coverage"] = status
        schema = unpack(await client.call_tool("get_catalog_schema", {}))
        checks["schema_available"] = "error" not in schema
        for supplier in ["ed", "mega"]:
            started = time.monotonic()
            page = unpack(
                await client.call_tool("list_products", {"query": {"supplier": supplier}})
            )
            catalog_total = page.get("total", 0)
            if page.get("error", {}).get("code") == "result_too_large":
                partition = json.loads(page["error"]["message"])
                catalog_total = partition["count"]
                page = unpack(
                    await client.call_tool(
                        "list_products",
                        {"query": {"supplier": supplier, **partition["partitions"][0]}},
                    )
                )
            sample = {
                "catalog_total": catalog_total,
                "list_seconds": round(time.monotonic() - started, 3),
                "total": page.get("total", 0),
                "list_available": "error" not in page,
            }
            report[supplier] = sample
            rows = page.get("results", [])
            if not rows:
                continue
            item = rows[0]["item"]
            product_id = rows[0]["product_id"]
            exact = unpack(
                await client.call_tool(
                    "lookup_products",
                    {"identifiers": [{"kind": "sku", "supplier": supplier, "value": item["sku"]}]},
                )
            )
            sample["exact_sku_found"] = any(
                p["product_id"] == product_id
                for e in exact.get("entries", [])
                for p in e.get("products", [])
            )
            detail = unpack(
                await client.call_tool(
                    "get_product", {"product_id": product_id, "section": "observations"}
                )
            )
            sample["details_available"] = "error" not in detail
            sample["detail_chunks"] = detail.get("total_chunks", 0)
            if detail.get("next_cursor"):
                more = unpack(
                    await client.call_tool("get_product", {"cursor": detail["next_cursor"]})
                )
                sample["detail_continuation_available"] = "error" not in more
            if page.get("next_cursor"):
                more = unpack(
                    await client.call_tool("list_products", {"cursor": page["next_cursor"]})
                )
                sample["list_continuation_disjoint"] = not (
                    {r["product_id"] for r in rows}
                    & {r["product_id"] for r in more.get("results", [])}
                )
            search = unpack(
                await client.call_tool("search_products", {"text": (item["name"] or item["sku"])[:1000]})
            )
            sample["search_available"] = "error" not in search
            sample["search_matches"] = len(search.get("results", []))
            comparison = unpack(
                await client.call_tool(
                    "compare_offers", {"product_ids": [product_id], "quantities": {product_id: 2}}
                )
            )
            sample["comparison_available"] = (
                isinstance(comparison, list)
                and len(comparison) == 1
                and not comparison[0].get("error")
            )
    return report


def probes():
    from suppliermcp.config import Settings
    from suppliermcp.sync.jobs import build_adapters

    report = {}
    for interface, adapter in build_adapters(Settings.from_env()).items():
        try:
            endpoint = getattr(adapter, "endpoints", getattr(adapter, "methods", {})).get("catalog")
            if interface == "mega" and not product_export(endpoint):
                raise CatalogError("operation_not_allowed")
            started = time.monotonic()
            manifest = adapter.fetch("catalog")
            counts = {}
            for row in adapter.parse(manifest):
                name = type(row).__name__
                counts[name] = counts.get(name, 0) + 1
            report[interface] = {
                "outcome": "parsed",
                "counts": counts,
                "complete": manifest.complete,
                "seconds": round(time.monotonic() - started, 3),
            }
        except Exception as error:
            report[interface] = failure(error)
        finally:
            adapter.transport.client.close()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--url", default="http://127.0.0.1:8000/mcp")
    parser.add_argument("--probe-suppliers", action="store_true")
    args = parser.parse_args()
    try:
        report = asyncio.run(verify(args.url, os.environ["SUPPLIERMCP_TOKEN"]))
        if args.probe_suppliers:
            report["supplier_probes"] = probes()
    except Exception as error:
        report = failure(error)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print("Sanitized live report written.")


if __name__ == "__main__":
    main()
