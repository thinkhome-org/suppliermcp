"""Reviewed supplier contracts. Runtime discovery never grants a new capability."""

import json
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from types import MappingProxyType
from typing import Literal

from suppliermcp.catalog.contracts import CatalogError

Scope = Literal["catalog:read", "documents:read"]


@dataclass(frozen=True)
class InputField:
    name: str
    xsd_type: str
    required: bool


@dataclass(frozen=True)
class OperationSpec:
    operation_id: str
    interface: str
    name: str
    mode: str
    effect: Literal["read", "write", "blocked"]
    scope: Scope | None
    target: str
    action: str
    inputs: tuple[InputField, ...]
    output_schema: str
    evidence: str
    strategy: Literal["bounded", "stream", "download"]
    days: tuple[int, ...] = ()
    hours: tuple[int, ...] = ()


_EXPORT_METHODS = {
    "full": ("GetResult", ()),
    "targeted": ("GetResultByCode", (InputField("code", "string", True),)),
    "delta": (
        "GetResultByFromTo",
        (
            InputField("from", "dateTime", True),
            InputField("to", "dateTime", True),
        ),
    ),
}


@cache
def _registry():
    contracts = json.loads(files(__package__).joinpath("operation_contracts.json").read_text())
    mega = contracts.pop("mega")
    specs = {}
    for interface, service in contracts.items():
        for name, (effect, scope, fields, output, evidence) in service["operations"].items():
            operation_id = f"{interface}.{name}"
            strategy = (
                "download" if interface.startswith("ed_") and "Download" in name else "bounded"
            )
            specs[operation_id] = OperationSpec(
                operation_id,
                interface,
                name,
                "soap",
                effect,
                scope,
                service["target"],
                service["namespace"].rstrip("/") + "/" + name,
                tuple(InputField(*field) for field in fields),
                output,
                evidence,
                strategy,
            )
    for name, (scope, evidence, windows) in mega["exports"].items():
        for (mode, (method, fields)), window in zip(_EXPORT_METHODS.items(), windows, strict=True):
            days, hours = mega["windows"][window]
            operation_id = f"mega.{name}.{mode}"
            effect = "read" if scope and days and hours else "blocked"
            specs[operation_id] = OperationSpec(
                operation_id,
                "mega",
                name,
                mode,
                effect,
                scope,
                f"https://i6ws.100mega.cz/Default.asmx/{method}",
                "",
                fields,
                f"{name}_Schema",
                evidence,
                "stream",
                tuple(days),
                tuple(hours),
            )
    return MappingProxyType(specs)


def operation_inventory() -> tuple[OperationSpec, ...]:
    return tuple(_registry().values())


def resolve_operation(operation_id: str) -> OperationSpec:
    spec = _registry().get(operation_id)
    if spec is None or spec.effect != "read":
        raise CatalogError("operation_not_allowed")
    return spec
