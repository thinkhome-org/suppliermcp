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


def test_codex_package_declares_skills_and_secret_free_bearer_auth(tmp_path):
    result = module.build_plugin(
        ROOT, tmp_path / "codex", "https://suppliermcp.thinkhome.org/mcp", codex=True
    )
    manifest = json.loads((result / ".codex-plugin/plugin.json").read_text())
    assert (result / manifest["skills"]).is_dir()
    mcp = json.loads((result / manifest["mcpServers"]).read_text())
    assert mcp["mcpServers"]["suppliermcp"] == {
        "type": "http",
        "url": "https://suppliermcp.thinkhome.org/mcp",
        "bearer_token_env_var": "SUPPLIERMCP_THINKHOME_TOKEN",
    }
    assert len(list(result.rglob("SKILL.md"))) == 2
    assert not (result / "mcp.json").exists()


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


def test_runtime_mounts_contracts_for_both_processes():
    import yaml

    compose = yaml.safe_load((ROOT / "compose.yaml").read_text())
    for name in ["mcp", "worker"]:
        service = compose["services"][name]
        assert (
            service["environment"]["SUPPLIERMCP_SOURCE_CONTRACTS_PATH"]
            == "/config/source-contracts.json"
        )
        assert any("/config/source-contracts.json:ro" in v for v in service["volumes"])
        assert service["env_file"][0]["path"] == "${SUPPLIERMCP_ENV_FILE:-.env}"


def test_release_plugin_version_tracks_wheel_version(tmp_path):
    import shutil

    source = tmp_path / "source"
    shutil.copytree(ROOT / "skills", source / "skills")
    for package, plugin in [("2.0.0rc3", "2.0.0-rc.3"), ("2.0.0", "2.0.0")]:
        (source / "pyproject.toml").write_text(f'[project]\nversion = "{package}"\n')
        path = module.build_plugin(source, tmp_path / package, "https://catalog.example/mcp")
        assert json.loads((path / "plugin.json").read_text())["version"] == plugin
