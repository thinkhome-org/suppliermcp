"""Isolated Linux-only decoder for the documented public eD BIFF8 price list."""

import json
import os
import sys

# The two Skladem labels in this native layout are the flag and the textual stock state.
HEADER = (
    "Komodita Kod Nazev Dealer EndUser VaseCena SNC Skladem PartNo Zaruka Status DPH "
    "AO ValuePack ValuePackQty EAN Skladem"
).split()
MAX_BYTES = 16 * 1024**2


def decode(source, output):
    import xlrd

    if source.read(8) != bytes.fromhex("d0cf11e0a1b11ae1"):
        raise ValueError
    source.seek(0)
    raw = source.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError
    with (
        open(os.devnull, "w") as quiet,
        xlrd.open_workbook(
            file_contents=raw, on_demand=True, ragged_rows=True, logfile=quiet
        ) as book,
    ):
        # sheet_names omits macro and chart sheets, while the BIFF count includes them.
        if (
            book.biff_version != 80
            or book._all_sheets_count != 1
            or book.sheet_names() != ["Part 1"]
        ):
            raise ValueError
        sheet = book.sheet_by_index(0)
        if (
            sheet.visibility != 0
            or not 1 <= sheet.nrows <= 65536
            or sheet.ncols != len(HEADER)
            or sheet.row_values(0) != HEADER
        ):
            raise ValueError
        for row in range(1, sheet.nrows):
            values = []
            for cell in sheet.row(row):
                if cell.ctype not in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_NUMBER):
                    raise ValueError
                values.append(str(cell.value))
            if len(values) != len(HEADER):
                raise ValueError
            line = (json.dumps(values, ensure_ascii=False) + "\n").encode()
            if len(line) > 65536:
                raise ValueError
            output.write(line)


def main():
    if sys.platform != "linux":
        return 1
    import resource

    try:
        for kind, value in (
            (resource.RLIMIT_AS, 256 * 1024**2),
            (resource.RLIMIT_CPU, 15),
            (resource.RLIMIT_FSIZE, 32 * 1024**2),
            (resource.RLIMIT_CORE, 0),
        ):
            resource.setrlimit(kind, (value, value))
        decode(sys.stdin.buffer, sys.stdout.buffer)
        sys.stdout.buffer.flush()
    except Exception:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
