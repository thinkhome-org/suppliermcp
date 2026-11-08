import hashlib
import runpy
from pathlib import Path

import pytest

from suppliermcp.suppliers.registry import operation_inventory

gate = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/verify_promotion.py"))


@pytest.fixture
def candidate(tmp_path):
    image = "ghcr.io/thinkhome-org/suppliermcp@sha256:" + "b" * 64
    source = "a" * 40
    observed = "2025-01-01T00:00:00+00:00"
    lines = []
    for name in gate["ASSETS"]:
        data = image.encode() if name == "image-reference.txt" else name.encode()
        (tmp_path / name).write_bytes(data)
        lines.append(f"{hashlib.sha256(data).hexdigest()}  {name}\n")
    sums = "".join(lines).encode()
    (tmp_path / "SHA256SUMS").write_bytes(sums)
    record = dict(
        version="2.0.0",
        image=image,
        source_commit=source,
        stage_tag="v2.0.0-stage.1",
        checksums_sha256=hashlib.sha256(sums).hexdigest(),
        checks={
            key: dict(outcome="passed", image=image, observed_at=observed, receipt_sha256="e" * 64)
            for key in gate["CHECKS"]
        },
    )
    rows = {
        s.operation_id: dict(
            image=image,
            package_version="2.0.0",
            outcome="verified_nonempty",
            interface=s.interface,
            mode=s.mode,
            scope=s.scope,
            observed_at=observed,
        )
        for s in operation_inventory()
        if s.effect == "read"
    }
    return record, rows, tmp_path, source


def test_complete_staged_candidate(candidate):
    gate["verify"](*candidate)


@pytest.mark.parametrize(
    "failure",
    [
        "missing_row",
        "wrong_image",
        "blocked",
        "rc_version",
        "missing_chatgpt",
        "no_receipt",
        "asset_changed",
    ],
)
def test_incomplete_evidence_cannot_promote(candidate, failure):
    record, rows, assets, _ = candidate
    key = next(iter(rows))
    chatgpt = "personal_chatgpt_web_oauth_catalog_and_documents"
    if failure == "missing_row":
        del rows[key]
    elif failure == "wrong_image":
        rows[key]["image"] = "old"
    elif failure == "blocked":
        rows[key]["outcome"] = "missing_input"
    elif failure == "rc_version":
        rows[key]["package_version"] = "2.0.0rc2"
    elif failure == "missing_chatgpt":
        del record["checks"][chatgpt]
    elif failure == "no_receipt":
        record["checks"][chatgpt]["receipt_sha256"] = ""
    else:
        (assets / "suppliermcp-codex-2.0.0.zip").write_bytes(b"changed")
    with pytest.raises(ValueError):
        gate["verify"](*candidate)


def test_catalog_scope_accepts_only_documented_known_limitations(candidate):
    record, rows, _, _ = candidate
    record["release_scope"] = ["catalog", "search", "offer_comparison"]
    record["known_limitations"] = {}
    for key, outcome in gate["KNOWN_LIMITATIONS"].items():
        rows[key]["outcome"] = outcome
        record["known_limitations"][key] = dict(
            outcome=outcome, reason="Known upstream limitation", issue=4
        )
    gate["verify"](*candidate)
    rows["ed_public.getProductList"]["outcome"] = "supplier_http_5xx"
    with pytest.raises(ValueError):
        gate["verify"](*candidate)


@pytest.mark.parametrize("failure", ["unknown", "different_outcome", "wrong_image", "no_reason"])
def test_limitation_cannot_hide_other_failures(candidate, failure):
    record, rows, _, _ = candidate
    key = "mega_order.GetStatus"
    record["release_scope"] = ["catalog", "search", "offer_comparison"]
    rows[key]["outcome"] = "missing_genuine_order_fixture"
    record["known_limitations"] = {
        key: dict(outcome=rows[key]["outcome"], reason="No orders", issue=4)
    }
    if failure == "unknown":
        record["known_limitations"]["ed_public.getProductList"] = record["known_limitations"][key]
    elif failure == "different_outcome":
        rows[key]["outcome"] = "permission_denied"
    elif failure == "wrong_image":
        rows[key]["image"] = "old"
    else:
        record["known_limitations"][key]["reason"] = ""
    with pytest.raises(ValueError):
        gate["verify"](*candidate)
