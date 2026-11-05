"""Rendered deployment boundaries, without production secrets or a Docker daemon."""

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def render(missing=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("SUPPLIERMCP_")}
    supplied = {
        "SUPPLIERMCP_IMAGE": "ghcr.io/thinkhome-org/suppliermcp@sha256:" + "0" * 64,
        "POSTGRES_PASSWORD": "test-only-url-safe-password",
        "SUPPLIERMCP_TYPESENSE_KEY": "test-only-index-key",
        "SUPPLIERMCP_AUTH_PUBLIC_KEY": "-----BEGIN PUBLIC KEY-----\nTEST\n-----END PUBLIC KEY-----",
        "SUPPLIERMCP_SOURCE_CONTRACTS_JSON": json.dumps(
            {"mega": {"label": "Unicode žluťoučký", "exports": {}}}
        ),
    }
    env.update(supplied)
    if missing:
        env.pop(missing, None)
    result = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            "/dev/null",
            "-f",
            str(ROOT / "compose.portainer.yaml"),
            "config",
            "--format",
            "json",
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    return result, supplied


def test_portainer_render_isolates_services_and_orders_fresh_migrations():
    result, supplied = render()
    assert result.returncode == 0, result.stderr
    config = json.loads(result.stdout)
    services = config["services"]
    assert not any(s.get("ports") for s in services.values())
    assert {n for n, s in services.items() if "cloudflare" in s.get("networks", {})} == {"mcp"}
    assert config["networks"]["cloudflare"]["external"] is True
    assert services["mcp"]["networks"]["cloudflare"]["aliases"] == ["suppliermcp-origin"]
    assert services["migrate"]["restart"] == "no"
    assert services["migrate"]["command"] == ["python", "-m", "suppliermcp.worker", "migrate"]
    for name in ("mcp", "worker"):
        assert (
            services[name]["depends_on"]["migrate"]["condition"] == "service_completed_successfully"
        )
        assert services[name]["image"] == supplied["SUPPLIERMCP_IMAGE"]
        assert (
            services[name]["environment"]["SUPPLIERMCP_AUTH_PUBLIC_KEY"]
            == supplied["SUPPLIERMCP_AUTH_PUBLIC_KEY"]
        )
        assert services[name]["configs"][0]["target"] == "/config/source-contracts.json"
        assert not any(v["type"] == "bind" for v in services[name].get("volumes", []))
    assert (
        config["configs"]["source_contracts"]["content"]
        == supplied["SUPPLIERMCP_SOURCE_CONTRACTS_JSON"]
    )
    assert all(not v.get("external") for v in config["volumes"].values())


@pytest.mark.parametrize(
    "missing",
    [
        "SUPPLIERMCP_IMAGE",
        "POSTGRES_PASSWORD",
        "SUPPLIERMCP_TYPESENSE_KEY",
        "SUPPLIERMCP_AUTH_PUBLIC_KEY",
        "SUPPLIERMCP_SOURCE_CONTRACTS_JSON",
    ],
)
def test_portainer_rejects_missing_required_configuration(missing):
    result, _ = render(missing)
    assert result.returncode != 0
    assert missing in result.stderr
