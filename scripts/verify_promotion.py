"""Validate reviewed live evidence before promoting the staged 2.0.0 bytes."""

import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from suppliermcp.suppliers.registry import operation_inventory

IMAGE = r"ghcr\.io/thinkhome-org/suppliermcp@sha256:[0-9a-f]{64}"
HASH = r"[0-9a-f]{64}"
CHECKS = {
    "portainer_restart",
    "portainer_backup_restore_and_v1_rollback",
    "actual_codex_oauth_catalog_and_documents",
    "personal_chatgpt_web_oauth_catalog_and_documents",
    "rest_catalog_and_document_denial",
    "python_catalog_and_documents",
    "catalog_selection_relevance_and_performance",
}
ASSETS = {
    "suppliermcp-2.0.0-py3-none-any.whl",
    "suppliermcp-codex-2.0.0.zip",
    "suppliermcp-portable-2.0.0.zip",
    "image-reference.txt",
}


def require(test, message):
    if not test:
        raise ValueError(message)


def timestamp(value):
    observed = datetime.fromisoformat(value)
    return observed.tzinfo is not None and observed <= datetime.now(UTC)


def verify(record, rows, assets, source):
    image = record["image"]
    require(re.fullmatch(IMAGE, image), "Invalid immutable image")
    require(record["version"] == "2.0.0", "Wrong release version")
    require(re.fullmatch(r"v2\.0\.0-stage\.[1-9][0-9]*", record["stage_tag"]), "Invalid stage")
    require(
        record["source_commit"] == source and re.fullmatch(r"[0-9a-f]{40}", source),
        "Staged Git revision differs",
    )
    require((assets / "image-reference.txt").read_text().strip() == image, "Staged digest differs")
    sums = (assets / "SHA256SUMS").read_bytes()
    require(
        hashlib.sha256(sums).hexdigest() == record["checksums_sha256"], "Asset manifest differs"
    )
    expected = "".join(
        f"{hashlib.sha256((assets / name).read_bytes()).hexdigest()}  {name}\n" for name in ASSETS
    )
    require(sorted(sums.decode().splitlines()) == sorted(expected.splitlines()), "Asset mismatch")
    specs = {s.operation_id: s for s in operation_inventory() if s.effect == "read"}
    require(specs and set(rows) == set(specs), "Supplier matrix differs from the reviewed registry")
    for key, spec in specs.items():
        row = rows[key]
        require(
            row.get("image") == image
            and row.get("package_version") == "2.0.0"
            and row.get("outcome") in {"verified_nonempty", "verified_empty"}
            and row.get("interface") == spec.interface
            and row.get("mode") == spec.mode
            and row.get("scope") == spec.scope
            and timestamp(row["observed_at"]),
            f"Missing successful live evidence for {key}",
        )
    require(set(record["checks"]) == CHECKS, "Missing or unexpected acceptance checks")
    for name, check in record["checks"].items():
        require(
            check.get("outcome") == "passed"
            and check.get("image") == image
            and timestamp(check["observed_at"])
            and re.fullmatch(HASH, check["receipt_sha256"]),
            f"Incomplete operator evidence for {name}",
        )


if __name__ == "__main__":
    directory, assets, source = sys.argv[1:]
    directory = Path(directory)
    verify(
        json.loads((directory / "acceptance.json").read_text()),
        json.loads((directory / "operations.json").read_text())["operations"],
        Path(assets),
        source,
    )
