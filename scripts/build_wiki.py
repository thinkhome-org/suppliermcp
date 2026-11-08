"""Publish a curated copy of the repository documentation to a GitHub Wiki."""

import re
import sys
from pathlib import Path
from urllib.parse import quote, urlsplit

PAGES = {
    "Home": "README.md",
    "Stable-release": "docs/stable-release.md",
    "Operations": "docs/operations.md",
    "Portainer": "docs/portainer.md",
    "Login": "docs/login.md",
    "Compatibility": "docs/compatibility.md",
    "Validation": "docs/validation.md",
    "Supplier-contracts": "docs/supplier-contracts.md",
    "Packaging-and-comparison": "docs/supplier-api/packaging-and-comparison.md",
    "Supplier-API": "docs/supplier-api/README.md",
    "eD-PUBLIC": "docs/supplier-api/ed_public-reference.md",
    "eD-PRIVATE": "docs/supplier-api/ed_private-reference.md",
    "100MEGA-exports": "docs/supplier-api/mega-reference.md",
    "100MEGA-order": "docs/supplier-api/mega_order-reference.md",
    "100MEGA-service": "docs/supplier-api/mega_default-reference.md",
    "Operation-reads": "docs/supplier-api/operation-reads.md",
    "V2-acceptance": "docs/supplier-api/v2-acceptance.md",
    "Implementation-decisions": "docs/implementation-decisions.md",
    "Codex": "integrations/codex/README.md",
}
BASE = "https://github.com/thinkhome-org/suppliermcp/blob/main/"


def build(root, destination):
    for title, source in PAGES.items():
        path = root / source

        def rewrite(match, directory=path.parent):
            target = match[1]
            if target.startswith("#") or urlsplit(target).scheme:
                return match[0]
            relative, _, anchor = target.partition("#")
            resolved = (directory / relative).resolve().relative_to(root)
            return "](" + BASE + quote(str(resolved)) + ("#" + anchor if anchor else "") + ")"

        content = re.sub(r"\]\(([^\s)]+)\)", rewrite, path.read_text())
        if title == "Home":
            content += "\n## Wiki\n\n" + "".join(
                f"- [{name}]({name})\n" for name in PAGES if name != "Home"
            )
        (destination / (title + ".md")).write_text(content)


if __name__ == "__main__":
    build(Path(__file__).resolve().parents[1], Path(sys.argv[1]))
