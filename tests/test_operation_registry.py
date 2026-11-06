import json
from pathlib import Path

import pytest

from suppliermcp.catalog.contracts import CatalogError
from suppliermcp.suppliers.registry import operation_inventory, resolve_operation

DOCS = Path(__file__).resolve().parents[1] / "docs" / "supplier-api"


def test_every_supplier_operation_and_export_mode_has_one_decision():
    ids = [spec.operation_id for spec in operation_inventory()]
    expected = set()
    for interface in ("ed_public", "ed_private"):
        inv = json.loads((DOCS / (interface.replace("_", "-") + "-inventory.json")).read_text())
        expected.update(f"{interface}.{row['name']}" for row in inv["operations"])
    mega = json.loads((DOCS / "100mega-inventory.json").read_text())
    for row in mega["exports"]:
        for name in row["names"]:
            for mode, window in row["modes"].items():
                key = f"mega.{name}.{mode}"
                expected.add(key)
                spec = next(s for s in operation_inventory() if s.operation_id == key)
                assert (list(spec.days), list(spec.hours)) == (window["days"], window["hours"])
                if not window["days"] or not window["hours"]:
                    assert spec.effect == "blocked"
    for service, methods in mega["wsdl_operations"].items():
        expected.update(f"{service}.{name}" for name in methods)
    assert len(ids) == len(expected)
    assert set(ids) == expected


def test_only_reviewed_reads_resolve():
    for spec in operation_inventory():
        if spec.effect == "read":
            assert resolve_operation(spec.operation_id) == spec
            assert spec.scope in ("catalog:read", "documents:read")
            assert spec.target.startswith("https://")
            assert spec.output_schema and spec.evidence
            assert not {"login", "password", "resultType"} & {p.name for p in spec.inputs}
        else:
            with pytest.raises(CatalogError, match="operation_not_allowed"):
                resolve_operation(spec.operation_id)
    for name in (
        "mega_order.GetFuture",
        "ed_private.createNewOrder",
        "mega_order.ExecuteTrgX",
        "ed_public.getAuthTokenEshop",
        "ed_public.getOrderListDownloadXMLWithTransform_INT",
        "ed_private.getProductCatalogueFullDownloadXMLWithTransform",
    ):
        with pytest.raises(CatalogError, match="operation_not_allowed"):
            resolve_operation(name)


def test_document_scope_and_fixed_contracts():
    for name in (
        "ed_public.getInvoiceDetail",
        "ed_public.getSellerInfo",
        "mega_order.GetComShipTo",
        "mega_order.GetStatusListAppendReady",
        "mega.ComShipTo.full",
    ):
        assert resolve_operation(name).scope == "documents:read"
    spec = resolve_operation("mega.StoItemBase.targeted")
    assert spec.scope == "catalog:read"
    assert spec.target == "https://i6ws.100mega.cz/Default.asmx/GetResultByCode"
    assert [p.name for p in spec.inputs] == ["code"]
    assert spec.days and spec.hours and spec.strategy == "stream"
