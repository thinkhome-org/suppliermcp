"""Verify the installed wheel carries every canonical migration and resource."""

from pathlib import Path

from suppliermcp.data import data_dir
from suppliermcp.mcp.resources import skill_text

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    installed = data_dir("migrations")
    assert "site-packages" in installed.parts, "Expected a wheel installation"
    expected = sorted((ROOT / "migrations").glob("*.sql"))
    assert expected and sorted(p.name for p in installed.glob("*.sql")) == [
        p.name for p in expected
    ]
    for path in expected:
        assert (installed / path.name).read_bytes() == path.read_bytes()
    for path in (ROOT / "skills").glob("*/SKILL.md"):
        assert skill_text(path.parent.name) == path.read_text()
