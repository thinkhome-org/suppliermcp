import runpy
from pathlib import Path

build = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/build_wiki.py"))["build"]


def test_wiki_contains_only_public_documentation_with_resolvable_links(tmp_path):
    root = Path(__file__).resolve().parents[1]
    build(root, tmp_path)
    pages = {p.stem for p in tmp_path.glob("*.md")}
    assert {"Home", "Operations", "Portainer", "Supplier-API", "Codex"} <= pages
    assert all("inventory.json" not in p.name for p in tmp_path.iterdir())
    content = (tmp_path / "Home.md").read_text()
    assert "https://github.com/thinkhome-org/suppliermcp/blob/main/" in content
    assert "[Operations](Operations)" in content


def test_operation_reference_matches_the_runtime_inventory():
    root = Path(__file__).resolve().parents[1]
    render = runpy.run_path(str(root / "scripts/build_operation_reference.py"))["render"]
    for path, content in render():
        assert path.read_text() == content
