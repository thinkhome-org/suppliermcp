import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "live_verify", Path(__file__).parents[1] / "scripts/live_verify.py"
)


def test_live_report_errors_cannot_leak_supplier_secrets():
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.failure(
        RuntimeError("password=SUPERSECRET https://user:secret@example.test/account")
    )
    assert result == {"outcome": "failed", "error_type": "RuntimeError"}


def test_only_product_export_probes_allowed():
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.product_export("CpsStiVal")
    assert not module.product_export("Order")
    assert not module.product_export("https://example.test")
