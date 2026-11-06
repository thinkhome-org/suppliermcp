"""Exercise the production Keycloak/Postgres Compose definition with disposable credentials."""

import json
import os
import secrets
import subprocess
import tempfile
import time
from pathlib import Path

import httpx


def main():
    project = "supdb-idp-smoke-" + secrets.token_hex(4)
    edge = project + "-edge"
    env = os.environ | {
        "SUPDB_IDP_DB_PASSWORD": secrets.token_urlsafe(32),
        "SUPDB_IDP_PUBLIC_URL": "https://login.example.invalid",
        "SUPDB_IDP_ADMIN": "smoke-admin",
        "SUPDB_IDP_ADMIN_PASSWORD": secrets.token_urlsafe(32),
        "SUPDB_IDP_TRUSTED_PROXY_ADDRESSES": "127.0.0.1/32",
    }
    compose_file = Path(__file__).resolve().parents[1] / "compose.identity.yaml"
    with tempfile.TemporaryDirectory() as directory:
        override = Path(directory) / "smoke.json"
        override.write_text(
            json.dumps(
                {
                    "services": {"keycloak": {"ports": ["127.0.0.1::8080"]}},
                    "networks": {"cloudflare": {"name": edge}},
                }
            )
        )
        cmd = ["docker", "compose", "-p", project, "-f", str(compose_file), "-f", str(override)]

        def compose(*args):
            return subprocess.check_output([*cmd, *args], env=env, text=True).strip()

        def discovery(realm):
            origin = "http://" + compose("port", "keycloak", "8080")
            for _ in range(90):
                try:
                    response = httpx.get(
                        origin + "/realms/" + realm + "/.well-known/openid-configuration", timeout=3
                    )
                    if response.is_success:
                        data = response.json()
                        assert data["issuer"] == env["SUPDB_IDP_PUBLIC_URL"] + "/realms/" + realm
                        assert "S256" in data["code_challenge_methods_supported"]
                        return origin
                except httpx.TransportError:
                    pass
                time.sleep(2)
            raise RuntimeError("Identity provider did not publish its configured HTTPS issuer")

        subprocess.run(["docker", "network", "create", edge], check=True, stdout=subprocess.DEVNULL)
        try:
            compose("up", "-d")
            discovery("master")
            # Local admin CLI runs inside the test service. No credentials enter process argv on the host.
            compose(
                "exec",
                "-T",
                "keycloak",
                "sh",
                "-ec",
                "/opt/keycloak/bin/kcadm.sh config credentials --server http://127.0.0.1:8080 "
                '--realm master --user "$KC_BOOTSTRAP_ADMIN_USERNAME" --password "$KC_BOOTSTRAP_ADMIN_PASSWORD"; '
                "/opt/keycloak/bin/kcadm.sh create realms -s realm=supdb-smoke -s enabled=true",
            )
            discovery("supdb-smoke")
            compose("restart", "identity-db", "keycloak")
            discovery("supdb-smoke")
            print("PASS: dedicated HTTPS issuer, S256 and persisted realm after restart")
        finally:
            compose("down", "-v")
            subprocess.run(["docker", "network", "rm", edge], check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
