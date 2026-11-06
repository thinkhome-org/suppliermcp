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

from suppliermcp.service import CATALOG_OPERATIONS

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
        "SUPPLIERMCP_AUTH_LEGACY_SUBJECTS": '["smoke"]',
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
        blue = compose
        run(["docker", "network", "create", network])
        try:
            rollback_image = os.environ.get("SUPPLIERMCP_ROLLBACK_IMAGE")
            database = compose + ["exec", "-T", "postgres"]
            marker_query = (
                "SELECT count(*) FROM source_items WHERE id='mega:rollback-check' AND active"
            )
            psql = database + ["psql", "-XAt", "-v", "ON_ERROR_STOP=1", "-U", "suppliermcp", "-c"]
            if rollback_image:
                env["SUPPLIERMCP_IMAGE"] = rollback_image
                run(compose + ["up", "-d", "--wait", "--wait-timeout", "180"])
                run(
                    psql
                    + [
                        """INSERT INTO source_items(id,data,revision) VALUES ('mega:rollback-check',
                    '{"supplier":"mega","source_id":"rollback-check","sku":"0007","name":"Synthetic"}',0)"""
                    ]
                )
                # Quiesce writers before backing up the disposable v1 installation.
                run(compose + ["stop", "mcp", "worker"])
                backup = Path(directory) / "v1.sql"
                with backup.open("wb") as out:
                    subprocess.run(
                        database
                        + [
                            "pg_dump",
                            "-U",
                            "suppliermcp",
                            "--no-owner",
                            "--no-privileges",
                            "suppliermcp",
                        ],
                        stdout=out,
                        env=env,
                        check=True,
                    )
                backup.chmod(0o600)
                env["SUPPLIERMCP_IMAGE"] = values["SUPPLIERMCP_IMAGE"]
                # A v1 catalogue cannot prove XML ancestry. Upgrade on isolated volumes.
                refused = subprocess.run(
                    compose + ["run", "--rm", "--no-deps", "migrate"], capture_output=True, env=env
                )
                assert refused.returncode != 0 and b"catalog_reprojection_required" in (
                    refused.stdout + refused.stderr
                )
                assert run(psql + [marker_query]).strip() == "1"
                compose = list(blue)
                compose[compose.index(project)] = project + "-green"
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
                    assert {tool.name for tool in await client.list_tools()} == {
                        *CATALOG_OPERATIONS,
                        "list_operations",
                        "read_operation",
                    }
                    assert len(await client.list_resources()) == 2
                    result = (await client.call_tool("get_catalog_status", {})).structured_content
                    status = result.get("result", result)
                    assert status["revision"] == 0
                    assert all(s["outcome"] == "disabled" for s in status["interfaces"].values())

            asyncio.run(verify())
            if rollback_image:
                assert run(psql + [marker_query]).strip() == "1"
                run(compose + ["restart", "mcp", "postgres", "typesense", "worker"])
                run(compose + ["up", "-d", "--wait", "--wait-timeout", "180"])
                assert run(psql + [marker_query]).strip() == "1"
                # Destroy only the disposable blue volume; restore the independent backup.
                env["SUPPLIERMCP_IMAGE"] = rollback_image
                run(blue + ["down", "-v"])
                run(blue + ["up", "-d", "--wait", "postgres"])
                with backup.open("rb") as source:
                    subprocess.run(
                        database + ["psql", "-qX", "-v", "ON_ERROR_STOP=1", "-U", "suppliermcp"],
                        stdin=source,
                        stdout=subprocess.DEVNULL,
                        env=env,
                        check=True,
                    )
                run(blue + ["up", "-d", "--wait", "--wait-timeout", "180"])
                assert run(psql + [marker_query]).strip() == "1"
                restored_url = "http://" + run(blue + ["port", "mcp", "8000"]).strip()

                async def check_restored_image():
                    async with Client(restored_url + "/mcp", auth=token) as client:
                        result = await client.call_tool(
                            "lookup_products",
                            {"identifiers": [{"kind": "sku", "supplier": "mega", "value": "0007"}]},
                        )
                        data = result.structured_content
                        assert data.get("result", data)["entries"][0]["status"] == "found"

                asyncio.run(check_restored_image())
                print(
                    "PASS: populated v1 upgrade rejection, isolated v2 restart and v1 backup restoration with authenticated SKU lookup"
                )
            print(
                "PASS: fresh migrations, readiness, auth, nine tools, two resources, exact config, disabled sources"
            )
        finally:
            run(compose + ["down", "-v"])
            if compose != blue:
                run(blue + ["down", "-v"])
            run(["docker", "network", "rm", network])


if __name__ == "__main__":
    main()
