import pytest

from suppliermcp.catalog.contracts import CatalogError
from suppliermcp.suppliers.ed.transforms import project_old_csv


class Fields(list):
    def field(self, path, value):
        self.append((path, value))


def test_only_reviewed_columns_emitted_with_reordered_chunked_input():
    raw = "\ufeffKod\tAddress\tKomodita\tNazev\r\n001\tprivate\t\tČip".encode()
    fields = Fields()
    project_old_csv((bytes([byte]) for byte in raw), fields, "member[1]/")
    assert fields == [("member[1]/Product[1]/Kod", "001"), ("member[1]/Product[1]/Nazev", "Čip")]


@pytest.mark.parametrize(
    "payload",
    [
        b"Kod\tKod\tNazev\tKomodita\n",
        b"Invoice\tAddress\n123\tsecret",
        b"Kod\tNazev\tKomodita\n001\tshifted\tforeign\textra",
        b"Kod\tNazev\tKomodita\n001\t\xff\tx",
        b"x" * 65537,
    ],
)
def test_invalid_tables_fail_closed(payload):
    with pytest.raises(CatalogError, match="catalog_projection_unavailable"):
        project_old_csv([payload], Fields(), "")


def test_biff8_binary_fixture_rejects_foreign_content_and_preserves_value_boundaries():
    import io
    import json
    from pathlib import Path

    from suppliermcp.suppliers.ed.xls_worker import decode

    raw = (Path(__file__).parent / "fixtures" / "ed-catalog-synthetic.xls").read_bytes()
    output = io.BytesIO()
    decode(io.BytesIO(raw), output)
    assert json.loads(output.getvalue())[1:3] == ["sku-1", "name\twith\nline"]
    for body in (
        raw.replace(b"Part 1", b"Orders"),
        raw.replace(b"Dealer", b"BillTo"),
        b"PK\x03\x04",
    ):
        with pytest.raises(ValueError):
            decode(io.BytesIO(body), io.BytesIO())


def test_subprocess_rejects_truncated_biff_and_limits_input_before_start():
    import sys

    from suppliermcp.suppliers.ed.transforms import project_xls
    from suppliermcp.suppliers.ed.xls_worker import MAX_BYTES

    if sys.platform != "linux":
        pytest.skip("XLS resource limits require Linux")
    fields = Fields()
    with pytest.raises(CatalogError, match="catalog_projection_unavailable"):
        project_xls([bytes.fromhex("d0cf11e0a1b11ae1")], fields, "")
    with pytest.raises(CatalogError, match="payload_too_large"):
        project_xls([b"x" * (MAX_BYTES + 1)], fields, "")
    assert not fields
