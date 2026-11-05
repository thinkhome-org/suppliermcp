import importlib.util
import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "build_plugin", ROOT / "integrations/codex/build_plugin.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_deterministic_verified_package(tmp_path):
    result = module.build_plugin(ROOT, tmp_path / "plugin", "https://catalog.example/mcp")
    for name in ["plugin", "mcp"]:
        jsonschema.validate(
            json.loads((result / f"{name}.json").read_text()),
            json.loads((ROOT / f"tests/fixtures/plugin-schemas/{name}.json").read_text()),
        )
    for name in ["product-discovery", "offer-comparison"]:
        assert (result / f"skills/{name}/SKILL.md").read_bytes() == (
            ROOT / f"skills/{name}/SKILL.md"
        ).read_bytes()
    assert len(list(result.rglob("SKILL.md"))) == 2
    assert not (result / ".env").exists()
    with pytest.raises(ValueError):
        module.build_plugin(ROOT, tmp_path / "bad", "https://user:secret@example.com/mcp")


def test_reject_skill_symlink(tmp_path):
    (tmp_path / "skills/product-discovery").mkdir(parents=True)
    (tmp_path / "skills/product-discovery/SKILL.md").symlink_to(ROOT / "pyproject.toml")
    with pytest.raises(ValueError):
        module.build_plugin(tmp_path, tmp_path / "output", "https://example.com/mcp")


def test_compose_isolation():
    import yaml

    compose = yaml.safe_load((ROOT / "compose.yaml").read_text())
    assert {name for name, service in compose["services"].items() if service.get("ports")} == {
        "mcp"
    }
    assert all(
        "@sha256:" in service["image"]
        for name, service in compose["services"].items()
        if name in {"postgres", "typesense"}
    )
    assert compose["services"]["mcp"]["ports"] == ["127.0.0.1:8000:8000"]


def test_remote_skill_content_matches_source():
    from suppliermcp.mcp.resources import skill_text

    for name in ["product-discovery", "offer-comparison"]:
        assert skill_text(name) == (ROOT / f"skills/{name}/SKILL.md").read_text()
