"""Boot and remove a fresh isolated Portainer stack with no supplier credentials."""

import asyncio
import json
import os
import secrets
import subprocess
import tempfile
import time
from pathlib import Path

import httpx
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastmcp import Client
from portainer_env import write_portainer_env

ROOT = Path(__file__).resolve().parents[1]


def main():
    project = "suppliermcp-portainer-test-" + secrets.token_hex(4)
    network = project + "-edge"
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = (
        private.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    contracts = json.dumps({"test_note": "Unicode žluťoučký $literal"})
    env = {k: v for k, v in os.environ.items() if not k.startswith("SUPPLIERMCP_")}
    values = {
        "SUPPLIERMCP_IMAGE": os.environ.get(
            "SUPPLIERMCP_SMOKE_IMAGE", "suppliermcp:portainer-test"
        ),
        "POSTGRES_PASSWORD": secrets.token_urlsafe(24),
        "SUPPLIERMCP_TYPESENSE_KEY": secrets.token_urlsafe(24),
        "SUPPLIERMCP_AUTH_PUBLIC_KEY": public,
        "SUPPLIERMCP_SOURCE_CONTRACTS_JSON": contracts,
    }
    values["PORTAINER_ROUNDTRIP"] = ' $ABSENT ${ABSENT} apostrophe\' back\\slash "quote" '
    env.pop("POSTGRES_PASSWORD", None)
    env.pop("PORTAINER_ROUNDTRIP", None)

    def run(args):
        return subprocess.run(args, env=env, text=True, capture_output=True, check=True).stdout

    with tempfile.TemporaryDirectory(prefix=project) as directory:
        upload = Path(directory) / "upload.env"
        write_portainer_env(upload, values)
        stack_env = Path(directory) / "stack.env"
        parsed = [
            tuple(p.strip() for p in line.split("=", 1)) for line in upload.read_text().splitlines()
        ]
        stack_env.write_text("".join(f"{k}={v}\n" for k, v in parsed))
        stack_env.chmod(0o600)
        override = Path(directory) / "override.yaml"
        override.write_text(
            json.dumps(
                {
                    "services": {
                        "mcp": {
                            "ports": ["127.0.0.1::8000"],
                            "environment": {"PORTAINER_ROUNDTRIP": "${PORTAINER_ROUNDTRIP}"},
                        }
                    },
                    "networks": {"cloudflare": {"name": network}},
                }
            )
        )
        compose = [
            "docker",
            "compose",
            "--project-name",
            project,
            "--env-file",
            str(stack_env),
            "-f",
            str(ROOT / "compose.portainer.yaml"),
            "-f",
            str(override),
        ]
        run(["docker", "network", "create", network])
        try:
            run(compose + ["up", "-d", "--wait", "--wait-timeout", "180"])
            address = run(compose + ["port", "mcp", "8000"]).strip()
            url = "http://" + address
            assert httpx.get(url + "/health/ready").status_code == 200
            assert httpx.post(url + "/mcp").status_code == 401
            mounted = run(
                compose
                + [
                    "exec",
                    "-T",
                    "mcp",
                    "python",
                    "-c",
                    'from pathlib import Path; print(Path("/config/source-contracts.json").read_text(), end="")',
                ]
            )
            assert mounted == contracts
            transported = run(
                compose
                + [
                    "exec",
                    "-T",
                    "mcp",
                    "python",
                    "-c",
                    'import os; print(os.environ["PORTAINER_ROUNDTRIP"], end="")',
                ]
            )
            assert transported == values["PORTAINER_ROUNDTRIP"]
            token = jwt.encode(
                {
                    "sub": "smoke",
                    "iss": "suppliermcp",
                    "aud": "suppliermcp",
                    "exp": time.time() + 600,
                },
                private,
                algorithm="RS256",
            )

            async def verify():
                async with Client(url + "/mcp", auth=token) as client:
                    assert len(await client.list_tools()) == 7
                    assert len(await client.list_resources()) == 2
                    result = (await client.call_tool("get_catalog_status", {})).structured_content
                    status = result.get("result", result)
                    assert status["revision"] == 0
                    assert all(s["outcome"] == "disabled" for s in status["interfaces"].values())

            asyncio.run(verify())
            print(
                "PASS: fresh migrations, readiness, auth, seven tools, two resources, exact config, disabled sources"
            )
        finally:
            run(compose + ["down", "-v"])
            run(["docker", "network", "rm", network])


if __name__ == "__main__":
    main()
