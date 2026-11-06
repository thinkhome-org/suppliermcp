"""Build a credential-free portable Agent Plugins 1.0 package."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


def build_plugin(source: Path, destination: Path, mcp_url: str, *, codex: bool = False) -> Path:
    url = urlsplit(mcp_url)
    if (
        url.scheme not in {"http", "https"}
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
    ):
        raise ValueError("Expected a credential-free MCP URL")
    if url.scheme == "http" and url.hostname not in {"localhost", "127.0.0.1"}:
        raise ValueError("Remote MCP requires HTTPS")
    files = {}
    for name in ["product-discovery", "offer-comparison"]:
        path = source / "skills" / name / "SKILL.md"
        if any(parent.is_symlink() for parent in [path, *path.parents]):
            raise ValueError("Skill symlinks are forbidden")
        content = path.read_text()
        if (
            not content.startswith(f"---\nname: {name}\ndescription: Use when ")
            or "\n---\n" not in content[4:]
        ):
            raise ValueError("Invalid skill frontmatter")
        if re.search(r"\]\((?!https?://)[^)]*\)", content):
            raise ValueError("This package supports self-contained skills only")
        files[f"skills/{name}/SKILL.md"] = content
    manifest = {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": "suppliermcp",
        "version": "2.0.0-rc.1",
        "description": "Read-only supplier product discovery and per-product offer comparison.",
    }
    mcp = {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
        "mcpServers": {"suppliermcp": {"type": "streamable-http", "url": mcp_url}},
    }
    manifest_path, mcp_path = "plugin.json", "mcp.json"
    if codex:
        manifest.pop("$schema")
        manifest.update(skills="./skills", mcpServers="./.mcp.json")
        mcp.pop("$schema")
        mcp["mcpServers"]["suppliermcp"].update(
            type="http", bearer_token_env_var="SUPPLIERMCP_THINKHOME_TOKEN"
        )
        manifest_path, mcp_path = ".codex-plugin/plugin.json", ".mcp.json"
    files.update(
        {
            manifest_path: json.dumps(manifest, indent=2) + "\n",
            mcp_path: json.dumps(mcp, indent=2) + "\n",
        }
    )
    destination.mkdir(parents=True, exist_ok=False)
    for name, content in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    parser.add_argument("--url", required=True)
    parser.add_argument("--codex", action="store_true", help="Build the native Codex package")
    args = parser.parse_args()
    print(
        build_plugin(
            Path(__file__).resolve().parents[2], args.destination, args.url, codex=args.codex
        )
    )
