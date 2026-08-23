"""
Binary WDBC reader/writer.

Implements exactly the layout in `src/common/DataStores/DBCFileLoader.cpp`:

    header:  'WDBC' magic, record_count, field_count, record_size, string_size
    records: record_count * record_size bytes, each field packed in `fmt` order
    strings: a string pool, offset 0 is always the empty string

Only the field types actually used by the tables in `dbcfmt.py` are
implemented: 'n'/'i'/'x' (uint32), 'f' (float32), 's' (string offset) — plus
any column listed in a table's `read_as_string`, decoded as a string
regardless of its fmt char (see dbcfmt.py's module docstring for why).
"""

from __future__ import annotations

import struct
from pathlib import Path

from .dbcfmt import DbcTable

MAGIC = b"WDBC"


def read_dbc(path: Path, table: DbcTable) -> list[dict]:
    """Read a binary DBC file into a list of {column_name: value} dicts."""
    data = Path(path).read_bytes()
    magic, record_count, field_count, record_size, string_size = struct.unpack_from(
        "<4sIIII", data, 0
    )
    if magic != MAGIC:
        raise ValueError(f"{path}: not a WDBC file (bad magic {magic!r})")
    if field_count != len(table.fmt):
        raise ValueError(
            f"{path}: file has {field_count} fields, expected {len(table.fmt)} "
            f"for {table.name}"
        )

    header_size = 20
    records_start = header_size
    strings_start = records_start + record_count * record_size
    string_pool = data[strings_start:strings_start + string_size]

    def read_string(offset: int) -> str:
        end = string_pool.index(b"\x00", offset)
        return string_pool[offset:end].decode("utf-8", "replace")

    rows = []
    for r in range(record_count):
        base = records_start + r * record_size
        offset = 0
        row = {}
        for ch, col in zip(table.fmt, table.columns):
            if ch == "f":
                (val,) = struct.unpack_from("<f", data, base + offset)
                offset += 4
            elif ch == "s" or col in table.read_as_string:
                (strref,) = struct.unpack_from("<I", data, base + offset)
                val = read_string(strref)
                offset += 4
            elif ch in ("n", "i", "x"):
                fmt_char = "<i" if col in table.signed else "<I"
                (val,) = struct.unpack_from(fmt_char, data, base + offset)
                offset += 4
            elif ch in ("b", "X"):
                val = data[base + offset]
                offset += 1
            else:
                raise ValueError(f"unsupported format char {ch!r} in {table.name}")
            row[col] = val
        rows.append(row)
    return rows


def _pack_string_pool(rows: list[dict], table: DbcTable):
    """Build a deduplicated string pool; offset 0 is always "".

    Returns (pool_bytes, {value: offset})."""
    pool = bytearray(b"\x00")
    offsets: dict[str, int] = {"": 0}
    for row in rows:
        for ch, col in zip(table.fmt, table.columns):
            if ch != "s" and col not in table.read_as_string:
                continue
            val = row.get(col) or ""
            if val not in offsets:
                offsets[val] = len(pool)
                pool += val.encode("utf-8") + b"\x00"
    return bytes(pool), offsets


def pack_dbc_bytes(table: DbcTable, rows: list[dict]) -> bytes:
    """Pack rows (sorted by index column) into a binary WDBC file's bytes."""
    rows = sorted(rows, key=lambda r: r[table.index_column])
    record_size = 4 * len(table.fmt)  # every field here is exactly 4 bytes
    string_pool, string_offsets = _pack_string_pool(rows, table)

    body = bytearray()
    for row in rows:
        for ch, col in zip(table.fmt, table.columns):
            val = row.get(col, 0)
            if ch == "f":
                body += struct.pack("<f", float(val or 0.0))
            elif ch == "s" or col in table.read_as_string:
                body += struct.pack("<I", string_offsets[val or ""])
            elif ch in ("n", "i", "x"):
                body += struct.pack("<I", int(val or 0) & 0xFFFFFFFF)
            else:
                raise ValueError(f"unsupported format char {ch!r} in {table.name}")

    header = struct.pack(
        "<4sIIII", MAGIC, len(rows), len(table.fmt), record_size, len(string_pool)
    )
    return header + bytes(body) + string_pool


def write_dbc(path: Path, table: DbcTable, rows: list[dict]) -> None:
    """Write rows (sorted by index column) as a binary WDBC file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pack_dbc_bytes(table, rows))


def empty_row(table: DbcTable) -> dict:
    """A full-width row with every column defaulted (0 / 0.0 / "")."""
    row = {}
    for ch, col in zip(table.fmt, table.columns):
        row[col] = "" if (ch == "s" or col in table.read_as_string) else 0
    return row
