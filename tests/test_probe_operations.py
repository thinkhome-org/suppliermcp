import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

from suppliermcp.config import Settings
from suppliermcp.suppliers.reads import OperationReader
from suppliermcp.suppliers.registry import resolve_operation

path = Path(__file__).resolve().parents[1] / "scripts" / "probe_operations.py"
spec = importlib.util.spec_from_file_location("probe_operations", path)
probes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probes)


async def test_missing_capability_is_sanitized_and_does_not_claim_a_supplier_call(tmp_path):
    reader = OperationReader(Settings(credentials={"mega": ("login", "password")}))
    spec = resolve_operation("mega.StoItemBase.targeted")
    row = await probes.probe(reader, spec, {"code": "sensitive-input"}, "operator_fixture", False)
    assert row["outcome"] == "capability_not_verified"
    assert "sensitive-input" not in json.dumps(row)
    assert probes.next_allowed(spec, reader, datetime.now(UTC)) is None
    path = tmp_path / "evidence.json"
    probes.save(path, {spec.operation_id: row})
    assert json.loads(path.read_text())["operations"][spec.operation_id] == row


def test_document_and_catalog_probe_distinguish_metadata_from_data():
    assert not probes.is_data(
        resolve_operation("ed_public.getInvoiceList"), "Envelope[1]/Body[1]/Status[1]/StatusCode[1]"
    )
    assert not probes.is_data(resolve_operation("mega.StoItemBase.targeted"), "Result[1]/@UrlBase")
    assert probes.is_data(
        resolve_operation("mega.StoItemBase.targeted"), "Result[1]/StoItem[1]/@Code"
    )


def test_iso_registry_weekdays_intersect_monday_and_sunday():
    from dataclasses import replace

    import pytest

    from suppliermcp.catalog.contracts import CatalogError
    from suppliermcp.suppliers.mega.capabilities import require_window, verified_export_window

    spec = resolve_operation("mega.StoItemBase.targeted")
    local = {
        "modes": [spec.mode],
        "timezone": "Europe/Prague",
        "days": list(range(7)),
        "hours": list(range(24)),
    }
    monday = datetime(2026, 11, 2, 0, tzinfo=UTC)
    sunday = datetime(2026, 11, 8, 0, tzinfo=UTC)
    for day, valid, invalid in [(1, monday, sunday), (7, sunday, monday)]:
        contract = verified_export_window(replace(spec, days=(day,), hours=(1,)), local)
        require_window(contract, spec.mode, valid)
        with pytest.raises(CatalogError, match="outside_supplier_window"):
            require_window(contract, spec.mode, invalid)
