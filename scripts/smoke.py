"""Authenticated disposable Compose smoke; removes only its randomly named project."""

import asyncio
import json
import secrets
import subprocess
import tempfile
import time
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastmcp import Client

ROOT = Path(__file__).resolve().parents[1]


async def verify(token, seeded=False):
    async with Client("http://127.0.0.1:8000/mcp", auth=token) as client:
        assert len(await client.list_tools()) == 7
        status = (await client.call_tool("get_catalog_status", {})).structured_content["result"]
        assert len(status["interfaces"]) == 3
        if seeded:
            result = (
                await client.call_tool(
                    "lookup_products",
                    {"identifiers": [{"kind": "sku", "supplier": "mega", "value": "0007"}]},
                )
            ).structured_content["result"]
            assert result["entries"][0]["status"] == "found"
        assert await client.read_resource("catalog://skills/product-discovery")


def main():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = (
        private.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    token = jwt.encode(
        {"sub": "smoke", "iss": "suppliermcp", "aud": "suppliermcp", "exp": time.time() + 1800},
        private,
        algorithm="RS256",
    )
    project = "suppliermcp-smoke-" + secrets.token_hex(4)
    with tempfile.TemporaryDirectory(prefix=project) as temporary:
        path = Path(temporary)
        env = path / "smoke.env"
        env.write_text(
            "POSTGRES_PASSWORD="
            + secrets.token_hex(20)
            + "\nSUPPLIERMCP_TYPESENSE_KEY="
            + secrets.token_hex(20)
            + "\nSUPPLIERMCP_AUTH_PUBLIC_KEY='"
            + public
            + "'\n"
        )
        env.chmod(0o600)
        override = path / "compose.yaml"
        override.write_text(
            json.dumps({"services": {name: {"env_file": [str(env)]} for name in ["mcp", "worker"]}})
        )
        command = [
            "docker",
            "compose",
            "--project-name",
            project,
            "--env-file",
            str(env),
            "-f",
            str(ROOT / "compose.yaml"),
            "-f",
            str(override),
        ]

        def run(*args, input=None):
            result = subprocess.run(
                command + list(args), input=input, text=True, cwd=ROOT, capture_output=True
            )
            if result.returncode:
                raise RuntimeError(
                    "Compose command failed: " + " ".join(args) + "\n" + result.stderr[-2000:]
                )
            return result.stdout

        try:
            run("config", "--quiet")
            run("up", "-d", "--wait", "postgres", "typesense")
            run("run", "--rm", "mcp", "python", "-m", "suppliermcp.worker", "migrate")
            run("up", "-d", "--wait", "mcp", "worker")
            asyncio.run(verify(token))
            code = """from suppliermcp.config import Settings
from suppliermcp.catalog.db import connect
from suppliermcp.catalog.contracts import SourceItem,BatchManifest
from suppliermcp.sync.publish import stage,publish
with connect(Settings.from_env()) as c:
 publish(c,stage(c,BatchManifest(interface='mega',domain='catalog',complete=True,artifact_sha256='smoke'),[SourceItem(supplier='mega',source_id='7',sku='0007',name='Synthetic memory')]))
"""
            run("exec", "-T", "mcp", "python", "-", input=code)
            run("restart", "mcp", "postgres")
            run("up", "-d", "--wait", "mcp")
            asyncio.run(verify(token, seeded=True))
            combinations = """import itertools
from pydantic import SecretStr
from suppliermcp.config import Settings
from suppliermcp.mcp.server import create_server
for bits in itertools.product([False,True],repeat=3):
 s=Settings.from_env()
 s.credentials={name:(SecretStr('synthetic'),SecretStr('synthetic')) for name,on in zip(['ed_public','ed_private','mega'],bits) if on}
 create_server(s)
 assert len(s.enabled_interfaces)==sum(bits)
print('8 optional-interface startup combinations verified')
"""
            print(run("exec", "-T", "mcp", "python", "-", input=combinations).strip())
            print(
                "Authenticated image, seven tools, remote skill bytes, migration and restart persistence verified"
            )
        finally:
            run("down", "-v", "--remove-orphans")


if __name__ == "__main__":
    main()
