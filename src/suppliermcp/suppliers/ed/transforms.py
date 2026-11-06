"""Bounded catalog projections for public eD price-list transforms."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from suppliermcp.catalog.contracts import CatalogError
from suppliermcp.suppliers.ed.xls_worker import HEADER, MAX_BYTES

# The public manual and the observed EDLINKOLDCSV header (additional XLS price columns).
_COLUMNS = frozenset(
    "Komodita Kod Nazev Dealer EndUser VaseCena SNC Skladem PartNo Zaruka Status DPH "
    "AO SumaPoplatky ValuePack ValuePackQty EAN SklademText".split()
)
_MAX_LINE = 64 * 1024


def _lines(chunks):
    pending = bytearray()
    for chunk in chunks:
        start = 0
        while start < len(chunk):
            end = chunk.find(b"\n", start)
            stop = len(chunk) if end == -1 else end
            if len(pending) + stop - start > _MAX_LINE:
                raise CatalogError("catalog_projection_unavailable")
            pending.extend(chunk[start:stop])
            if end == -1:
                break
            yield bytes(pending).removesuffix(b"\r")
            pending.clear()
            start = end + 1
    if pending:
        yield bytes(pending)


def project_old_csv(chunks, preview, prefix):
    lines = _lines(chunks)
    try:
        header = next(lines, b"").decode("utf-8-sig").split("\t")
        if (
            len(header) > 128
            or len(set(header)) != len(header)
            or not {"Kod", "Nazev", "Komodita"}.issubset(header)
        ):
            raise CatalogError("catalog_projection_unavailable")
        selected = [(index, name) for index, name in enumerate(header) if name in _COLUMNS]
        for row, line in enumerate(lines, 1):
            if b"\x00" in line or b"\r" in line:
                raise CatalogError("catalog_projection_unavailable")
            cells = line.decode("utf-8").split("\t")
            if len(cells) != len(header):
                raise CatalogError("catalog_projection_unavailable")
            for index, name in selected:
                if cells[index]:
                    preview.field(f"{prefix}Product[{row}]/{name}", cells[index])
    except UnicodeDecodeError:
        raise CatalogError("catalog_projection_unavailable") from None


def project_xls(chunks, preview, prefix):
    with tempfile.TemporaryFile() as source, tempfile.TemporaryFile() as table:
        for chunk in chunks:
            if source.tell() + len(chunk) > MAX_BYTES:
                raise CatalogError("payload_too_large")
            source.write(chunk)
        source.seek(0)
        try:
            result = subprocess.run(
                [sys.executable, "-I", Path(__file__).with_name("xls_worker.py")],
                stdin=source,
                stdout=table,
                stderr=subprocess.DEVNULL,
                env={},
                timeout=20,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise CatalogError("catalog_projection_unavailable") from None
        if result.returncode:
            raise CatalogError("catalog_projection_unavailable")
        table.seek(0)
        columns = [*HEADER[:-1], "SklademText"]
        for row, line in enumerate(iter(lambda: table.readline(65537), b""), 1):
            if len(line) > 65536:
                raise CatalogError("catalog_projection_unavailable")
            try:
                values = json.loads(line)
            except (ValueError, RecursionError):
                raise CatalogError("catalog_projection_unavailable") from None
            if (
                not isinstance(values, list)
                or len(values) != len(columns)
                or not all(isinstance(v, str) for v in values)
            ):
                raise CatalogError("catalog_projection_unavailable")
            for name, value in zip(columns, values, strict=True):
                if value:
                    preview.field(f"{prefix}Product[{row}]/{name}", value)


def table_projection(args):
    if args.get("transformation") == "EDLINKOLDCSV" and args.get("encoding", "").lower() in {
        "utf-8",
        "utf8",
    }:
        return project_old_csv
    if args.get("transformation") == "EDLINKXLS" and sys.platform == "linux":
        return project_xls
    raise CatalogError("catalog_projection_unavailable")
