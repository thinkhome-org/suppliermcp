"""Render the public, payload-free read and exclusion reference from runtime contracts."""

from itertools import groupby
from pathlib import Path

from suppliermcp.suppliers.registry import operation_inventory

OUT = Path(__file__).resolve().parents[1] / "docs/supplier-api"
TITLES = {
    "ed_public": "eD PUBLIC",
    "ed_private": "eD PRIVATE",
    "mega": "100MEGA exports",
    "mega_order": "100MEGA Order.asmx",
    "mega_default": "100MEGA Default.asmx",
}


def render():
    inventory = sorted(operation_inventory(), key=lambda spec: (spec.interface, spec.operation_id))
    for interface, entries in groupby(inventory, key=lambda spec: spec.interface):
        lines = [
            "# " + TITLES[interface],
            "",
            "Generated from the reviewed runtime registry. Use the exact operation ID with "
            "the Python, REST or MCP interface. An input ending in ? is optional in the supplier "
            "contract. The service may enforce stricter input rules for a safe read.",
            "",
            "[Calling and paging](operation-reads.md) · [Live acceptance](v2-acceptance.md)",
            "",
        ]
        if interface == "mega":
            lines += [
                "Hours use Europe/Prague. Weekdays use ISO numbering (Monday = 1). "
                "The installation's authenticated capability list must also permit the mode.",
                "",
            ]
        for spec in entries:
            lines += ["## " + spec.operation_id, ""]
            if spec.effect == "read":
                inputs = ", ".join(
                    f"`{field.name}{'' if field.required else '?'}: {field.xsd_type}`"
                    for field in spec.inputs
                )
                lines += [
                    f"- Scope: `{spec.scope}`",
                    f"- Supplier inputs: {inputs or 'none beyond server-side authentication'}",
                    f"- Output: `{spec.output_schema}`",
                ]
                if interface == "mega":
                    days = ", ".join(map(str, sorted(spec.days)))
                    hours = ", ".join(map(str, sorted(spec.hours)))
                    lines.append(f"- Allowed by reviewed contract: days {days}; hours {hours}.")
            else:
                lines += [f"- Excluded from client calls (`{spec.effect}`)."]
            lines += ["- Evidence: " + spec.evidence.replace("\n", " "), ""]
        yield OUT / (interface + "-reference.md"), "\n".join(lines)


if __name__ == "__main__":
    for path, content in render():
        path.write_text(content)
