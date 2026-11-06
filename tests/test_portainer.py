"""Rendered deployment boundaries, without production secrets or a Docker daemon."""

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def render(missing=None, extra=None):
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
    supplied["SUPPLIERMCP_AUTH_CLIENTS"] = '{"client-a":{}}'
    supplied["SUPPLIERMCP_ED_PRIVATE_LOGIN"] = "test-private"
    supplied["SUPPLIERMCP_ED_PRIVATE_PASSWORD"] = "test-private-password"
    supplied.update(extra or {})
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
        for key in ("SUPPLIERMCP_ED_PRIVATE_LOGIN", "SUPPLIERMCP_ED_PRIVATE_PASSWORD"):
            assert services[name]["environment"][key] == supplied[key]
        assert (
            services[name]["environment"]["SUPPLIERMCP_AUTH_PUBLIC_KEY"]
            == supplied["SUPPLIERMCP_AUTH_PUBLIC_KEY"]
        )
        assert (
            services[name]["environment"]["SUPPLIERMCP_AUTH_CLIENTS"]
            == supplied["SUPPLIERMCP_AUTH_CLIENTS"]
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


def test_portainer_ui_env_file_roundtrip_preserves_special_values(tmp_path):
    _, values = render()
    values["SUPPLIERMCP_MEGA_LOGIN"] = "test'login"
    values["SUPPLIERMCP_MEGA_PASSWORD"] = (
        " dollars $ABSENT ${ABSENT} $$ apostrophe' slash\\ quote\" "
    )
    values["SUPPLIERMCP_SOURCE_CONTRACTS_JSON"] = json.dumps(
        {"note": "žluťoučký $ABSENT ${ABSENT} apostrophe'"}
    )
    source, output = tmp_path / "input.json", tmp_path / "portainer.env"
    source.write_text(json.dumps(values))
    prepared = subprocess.run(
        ["python", str(ROOT / "scripts/portainer_env.py"), str(source), str(output)],
        capture_output=True,
        text=True,
    )
    assert prepared.returncode == 0, prepared.stderr
    lines = output.read_text().splitlines()
    assert len(lines) == len(values)
    assert output.stat().st_mode & 0o777 == 0o600
    # Portainer's UI trims each physical line/value, then its backend writes raw NAME=value.
    parsed = [tuple(part.strip() for part in line.split("=", 1)) for line in lines]
    stack_env = tmp_path / "stack.env"
    stack_env.write_text("".join(f"{key}={value}\n" for key, value in parsed))
    env = {k: v for k, v in os.environ.items() if k not in values}
    env["ABSENT"] = "MUST_NOT_EXPAND"
    result = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            str(stack_env),
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
    assert result.returncode == 0, result.stderr
    config = json.loads(result.stdout)
    actual = config["services"]["mcp"]["environment"]
    for key in (
        "SUPPLIERMCP_AUTH_PUBLIC_KEY",
        "SUPPLIERMCP_MEGA_LOGIN",
        "SUPPLIERMCP_MEGA_PASSWORD",
    ):
        # Compose escapes literal dollars for re-reading its rendered output.
        assert actual[key].replace("$$", "$") == values[key]
    assert (
        config["configs"]["source_contracts"]["content"].replace("$$", "$")
        == values["SUPPLIERMCP_SOURCE_CONTRACTS_JSON"]
    )


def test_contract_updates_change_both_service_hashes():
    _, values = render()
    env = {k: v for k, v in os.environ.items() if not k.startswith("SUPPLIERMCP_")}
    env.update(values)
    command = [
        "docker",
        "compose",
        "--env-file",
        "/dev/null",
        "-f",
        str(ROOT / "compose.portainer.yaml"),
        "config",
        "--hash",
        "mcp,worker",
    ]
    first = subprocess.check_output(command, env=env, text=True)
    env["SUPPLIERMCP_SOURCE_CONTRACTS_JSON"] = '{"mega":{"intervals_seconds":{"catalog":86400}}}'
    second = subprocess.check_output(command, env=env, text=True)
    first, second = (
        dict(line.split() for line in first.splitlines()),
        dict(line.split() for line in second.splitlines()),
    )
    assert first["mcp"] != second["mcp"]
    assert first["worker"] != second["worker"]


def test_portainer_env_rejects_variable_name_injection(tmp_path):
    source, output = tmp_path / "input.json", tmp_path / "portainer.env"
    source.write_text(json.dumps({"SAFE\nINJECTED": "sensitive-test-value"}))
    result = subprocess.run(
        ["python", str(ROOT / "scripts/portainer_env.py"), str(source), str(output)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert not output.exists()
    assert "sensitive-test-value" not in result.stderr


def test_green_stack_does_not_advertise_the_blue_tunnel_alias():
    result, _ = render(
        extra={
            "SUPDB_ORIGIN_ALIAS": "supdb-green-origin",
            "SUPDB_PUBLIC_HOST": "supdb-green.example.org",
        }
    )
    assert result.returncode == 0
    mcp = json.loads(result.stdout)["services"]["mcp"]
    assert mcp["networks"]["cloudflare"]["aliases"] == ["supdb-green-origin"]
    hosts = json.loads(mcp["environment"]["SUPPLIERMCP_ALLOWED_HOSTS"])
    assert hosts == [
        "supdb-green.example.org",
        "supdb-green-origin:8000",
        "127.0.0.1:*",
        "localhost:*",
    ]


def test_identity_stack_accepts_forwarded_headers_only_from_configured_proxy():
    values = {
        "SUPDB_IDP_DB_PASSWORD": "test-only",
        "SUPDB_IDP_PUBLIC_URL": "https://login.example.org",
        "SUPDB_IDP_ADMIN": "test-admin",
        "SUPDB_IDP_ADMIN_PASSWORD": "test-only",
        "SUPDB_IDP_TRUSTED_PROXY_ADDRESSES": "172.20.0.7/32",
    }
    raw = subprocess.check_output(
        [
            "docker",
            "compose",
            "--env-file",
            "/dev/null",
            "-f",
            str(ROOT / "compose.identity.yaml"),
            "config",
            "--format",
            "json",
        ],
        text=True,
        env=os.environ | values,
    )
    services = json.loads(raw)["services"]
    keycloak = services["keycloak"]["environment"]
    assert keycloak["KC_PROXY_HEADERS"] == "xforwarded"
    assert keycloak["KC_PROXY_TRUSTED_ADDRESSES"] == "172.20.0.7/32"
    assert not any(s.get("ports") for s in services.values())
    assert "cloudflare" not in services["identity-db"]["networks"]
