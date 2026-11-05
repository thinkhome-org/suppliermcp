"""Exercise installed Codex against a synthetic local MCP without editing user configuration."""

import importlib.util
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import psycopg

from suppliermcp.catalog.contracts import BatchManifest, Offer, SourceItem
from suppliermcp.catalog.db import migrate
from suppliermcp.sync.publish import publish, stage

ROOT = Path(__file__).resolve().parents[1]


def main():
    spec = importlib.util.spec_from_file_location(
        "http_fixture", ROOT / "tests/integration/test_mcp.py"
    )
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    with psycopg.connect("postgresql://test:test@localhost:55439/test", autocommit=True) as conn:
        migrate(conn)
        publish(
            conn,
            stage(
                conn,
                BatchManifest(
                    interface="mega",
                    domain="catalog",
                    mode="targeted",
                    artifact_sha256="codex-acceptance",
                ),
                [
                    SourceItem(
                        supplier="mega", source_id="acceptance", sku="0007", name="Paměť DDR5 32GB"
                    ),
                    Offer(
                        item_id="mega:acceptance",
                        unit_net="100",
                        fees_net="0",
                        currency="CZK",
                        order_multiple="1",
                        refresh_failed=True,
                    ),
                ],
            ),
        )
        import httpx

        from suppliermcp.search.index import IndexClient, rebuild_index

        with httpx.Client(
            base_url="http://localhost:58109", headers={"X-TYPESENSE-API-KEY": "test-only"}
        ) as http:
            rebuild_index(conn, IndexClient(http))
    output = ROOT / ".superpowers/sdd/2026-11-05-suppliermcp-v1"
    output.mkdir(parents=True, exist_ok=True)
    with (
        fixture.running_server() as (url, token),
        tempfile.TemporaryDirectory(prefix="suppliermcp-codex-") as directory,
    ):
        env = os.environ | {"SUPPLIERMCP_TEST_TOKEN": token()}
        for skills in [False, True]:
            if skills:
                shutil.copytree(ROOT / "skills", Path(directory) / ".agents/skills")
            prompt = (
                "Test the suppliermcp MCP using real calls only. "
                + (
                    "Read and use .agents/skills/product-discovery/SKILL.md and offer-comparison/SKILL.md. "
                    if skills
                    else ""
                )
                + "Look up exact mega SKU 0007 preserving zeros; search Czech text paměť DDR5; discover whether unsupported capacity_tib can be filtered; compare mega:acceptance for 7 units with refresh=true; inspect disabled source status. Explain uncertainty and do not buy anything. Use only suppliermcp tools and reading these optional skill files; do not use other connectors or modify files."
            )
            args = [
                "codex",
                "exec",
                "--ignore-user-config",
                "--ephemeral",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "--json",
                "-C",
                directory,
                "-c",
                'approval_policy="never"',
                "-c",
                f'mcp_servers.suppliermcp={{url="{url}",bearer_token_env_var="SUPPLIERMCP_TEST_TOKEN"}}',
                prompt,
            ]
            result = subprocess.run(
                args, env=env, capture_output=True, text=True, timeout=180, check=False
            )
            name = "codex-skills" if skills else "codex-tools"
            (output / (name + ".jsonl")).write_text(result.stdout)
            (output / (name + ".stderr")).write_text(result.stderr)
            print(name, "exit", result.returncode, "trace bytes", len(result.stdout))
            if result.returncode:
                print(result.stderr[-500:])
                break


if __name__ == "__main__":
    main()
