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


def order_talent_rows(rows: list[dict], base_rows: list[dict]) -> list[dict]:
    """Physical row order for Talent.dbc — NOT a flat ID sort.

    Confirmed via live-client testing (docs/dbc-build-pipeline.md's "Talent.dbc row order"
    finding): the 3.3.5a client's talent frame assigns each button slot by physical *encounter
    order* within a contiguous per-TabID block in the file, not by ID and not independently of
    file position. A flat global ID sort (pack_dbc_bytes's default) scatters every tab's rows
    across the whole file — IDs from different classes interleave — which breaks every tab that
    renders at all, not just ones this pipeline touched. Ordering instead has to:

      1. Keep each tab's rows physically contiguous, in the tab-block order the base/stock file
         already uses — so a tab this pipeline never touches stays byte-for-byte where the
         client already expects it (verified live: Arcane/Fire/other classes' tabs all broke
         under a flat ID sort and were fixed by this alone).
      2. Within each tab's block, order rows by (TierID, ColumnIndex) — physical order has to
         match the logical grid. Verified live: a block left in its *old* physical sub-order
         after a tier/column redesign rendered nothing for that tab, even though every
         individual row's own data (TierID/ColumnIndex included) was already correct.
      3. A brand-new talent ID (not in the base file at all) gets inserted into its own TabID's
         block via rule 2 — never appended past the file's old contiguous tab boundaries.

    `base_rows`: the base/extracted client DBC's rows, in original file order — the source of
    tab-block boundaries and their relative order in the file.
    """
    by_id = {r["ID"]: r for r in rows}

    tab_order: list[int] = []
    tab_ids: dict[int, list[int]] = {}
    for r in base_rows:
        tab = r["TabID"]
        if tab not in tab_ids:
            tab_order.append(tab)
            tab_ids[tab] = []
        tab_ids[tab].append(r["ID"])

    base_id_set = {r["ID"] for r in base_rows}
    for new_id, row in by_id.items():
        if new_id in base_id_set:
            continue
        tab = row["TabID"]
        if tab not in tab_ids:
            tab_order.append(tab)
            tab_ids[tab] = []
        tab_ids[tab].append(new_id)

    ordered: list[dict] = []
    for tab in tab_order:
        block = [by_id[i] for i in tab_ids[tab] if i in by_id]
        block.sort(key=lambda r: (r["TierID"], r["ColumnIndex"]))
        ordered.extend(block)

    if len(ordered) != len(rows):
        missing = {r["ID"] for r in rows} - {r["ID"] for r in ordered}
        raise ValueError(f"order_talent_rows: dropped row(s) {missing} — base_rows out of sync?")
    return ordered


def pack_dbc_bytes(table: DbcTable, rows: list[dict], *, sort: bool = True) -> bytes:
    """Pack rows into a binary WDBC file's bytes.

    By default, rows are sorted by the table's index column — reproducible and correct for
    every table this pipeline touches except Talent.dbc, whose physical row order is
    load-bearing to the client (see order_talent_rows). Pass `sort=False` with `rows` already in
    the exact desired physical order to skip the default sort.
    """
    if sort:
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
