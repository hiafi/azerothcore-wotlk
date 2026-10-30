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

import functools
import struct
from operator import itemgetter
from pathlib import Path
from typing import NamedTuple

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

    if record_count == 0:
        return []

    layout = _read_layout(table)
    columns = table.columns
    st = layout.packer
    if st.size == record_size:
        # records are contiguous: one C-level pass over the whole record block
        tuples = st.iter_unpack(data[records_start:strings_start])
    else:
        unpack_from = st.unpack_from
        tuples = (unpack_from(data, records_start + r * record_size) for r in range(record_count))

    rows = [dict(zip(columns, values)) for values in tuples]
    if layout.string_columns:
        strings = _StringPool(string_pool)
        for col in layout.string_columns:
            for row in rows:
                row[col] = strings[row[col]]
    return rows


class _StringPool(dict):
    """NUL-terminated strings of a DBC string block by offset, decoded on first use."""

    def __init__(self, pool: bytes):
        super().__init__()
        self._pool = pool

    def __missing__(self, offset: int) -> str:
        end = self._pool.index(b"\x00", offset)
        text = self[offset] = self._pool[offset:end].decode("utf-8", "replace")
        return text


class _ReadLayout(NamedTuple):
    packer: struct.Struct
    string_columns: tuple


@functools.lru_cache(maxsize=None)
def _read_layout(table: DbcTable) -> _ReadLayout:
    """One precompiled struct per table, plus the names of its string-offset columns."""
    codes = []
    string_columns = []
    for ch, col in zip(table.fmt, table.columns):
        if ch == "f":
            codes.append("f")
        elif ch == "s" or col in table.read_as_string:
            codes.append("I")
            string_columns.append(col)
        elif ch in ("n", "i", "x"):
            codes.append("i" if col in table.signed else "I")
        elif ch in ("b", "X"):
            codes.append("B")
        else:
            raise ValueError(f"unsupported format char {ch!r} in {table.name}")
    return _ReadLayout(struct.Struct("<" + "".join(codes)), tuple(string_columns))


@functools.lru_cache(maxsize=None)
def _string_columns(table: DbcTable) -> tuple:
    return tuple(col for ch, col in zip(table.fmt, table.columns) if ch == "s" or col in table.read_as_string)


def _pack_string_pool(rows: list[dict], table: DbcTable):
    """Build a deduplicated string pool; offset 0 is always "".

    Returns (pool_bytes, {value: offset})."""
    pool = bytearray(b"\x00")
    offsets: dict[str, int] = {"": 0}
    string_cols = _string_columns(table)
    for row in rows:
        for col in string_cols:
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
      3. A row goes into the block of its **final** (built) TabID, not the tab it has in the base file,
         so a stock talent moved to another tab (Sniper Training 2143, SV 362 -> MM 363) leaves its old
         block and sorts inside the new one; the old block keeps its place, just without the row. A
         brand-new talent ID is placed the same way - never appended past the file's old contiguous
         tab boundaries. Blocks follow the base file's tab order; a tab absent from the base file
         (the 60800 holding tab of `retire_talent`) gets its own block after every base block.

    Within a block, rows the base file already had come first (in base order), then the rest in the
    order given - the sort below is stable, so equal (TierID, ColumnIndex) pairs keep that order.

    `base_rows`: the base/extracted client DBC's rows, in original file order - the source of
    tab-block order.
    """
    by_id = {r["ID"]: r for r in rows}

    tab_order: list[int] = []
    tab_ids: dict[int, list[int]] = {}

    def place(tab: int, row_id: int) -> None:
        if tab not in tab_ids:
            tab_order.append(tab)
            tab_ids[tab] = []
        tab_ids[tab].append(row_id)

    # Base tabs first, in file order, even when every row of one has moved away.
    for r in base_rows:
        tab_ids.setdefault(r["TabID"], [])
        if r["TabID"] not in tab_order:
            tab_order.append(r["TabID"])
    base_id_set = {r["ID"] for r in base_rows}
    for r in base_rows:
        if r["ID"] in by_id:
            place(by_id[r["ID"]]["TabID"], r["ID"])
    for new_id, row in by_id.items():
        if new_id not in base_id_set:
            place(row["TabID"], new_id)

    ordered: list[dict] = []
    for tab in tab_order:
        block = [by_id[i] for i in tab_ids[tab]]
        block.sort(key=lambda r: (r["TierID"], r["ColumnIndex"]))
        ordered.extend(block)

    if len(ordered) != len(rows):
        missing = {r["ID"] for r in rows} - {r["ID"] for r in ordered}
        raise ValueError(f"order_talent_rows: dropped row(s) {missing} — base_rows out of sync?")
    return ordered


def _pack_body(table: DbcTable, rows: list[dict], string_offsets: dict[str, int]) -> bytes:
    """All records as one byte string.

    Columns are extracted in bulk (C-level itemgetter, falling back to row.get(col, 0) when a row
    lacks the column); float and string columns are coerced exactly as the per-field code did
    (float(val or 0.0), offsets[val or ""]). Integer columns go straight into struct.pack; a row
    whose value it rejects (negative, > 32 bit, None, float, str ...) gets the int(val or 0) &
    0xFFFFFFFF coercion instead."""
    mask = 0xFFFFFFFF
    cols = []
    int_positions = []
    for i, (ch, col) in enumerate(zip(table.fmt, table.columns)):
        if ch == "f":
            kind = 0
        elif ch == "s" or col in table.read_as_string:
            kind = 1
        elif ch in ("n", "i", "x"):
            kind = 2
        else:
            raise ValueError(f"unsupported format char {ch!r} in {table.name}")
        try:
            raw = list(map(itemgetter(col), rows))
        except KeyError:
            raw = [r.get(col, 0) for r in rows]
        if kind == 0:
            raw = [float(v or 0.0) for v in raw]
        elif kind == 1:
            raw = [string_offsets[v or ""] for v in raw]
        elif col in table.signed:  # negative by design: wrap them all up front
            raw = [int(v or 0) & mask for v in raw]
        else:
            int_positions.append(i)
        cols.append(raw)

    pack = _pack_struct(table).pack
    chunks = []
    for values in zip(*cols):
        try:
            chunks.append(pack(*values))
        except (struct.error, TypeError, OverflowError):
            fixed = list(values)
            for i in int_positions:
                fixed[i] = int(fixed[i] or 0) & mask
            chunks.append(pack(*fixed))
    return b"".join(chunks)


@functools.lru_cache(maxsize=None)
def _pack_struct(table: DbcTable) -> struct.Struct:
    return struct.Struct("<" + "".join("f" if ch == "f" else "I" for ch in table.fmt))


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

    if not rows:
        body = b""
    else:
        body = _pack_body(table, rows, string_offsets)

    header = struct.pack(
        "<4sIIII", MAGIC, len(rows), len(table.fmt), record_size, len(string_pool)
    )
    return header + body + string_pool


def pack_client_dbc(table: DbcTable, rows: list[dict], base_rows: list[dict]) -> bytes:
    """Packs a full client DBC (stock merged with custom rows) in the physical row order the client
    needs. Most tables are read by ID, but two are read in file order:

    - Talent.dbc: per-tab blocks in stock order, rows by (TierID, ColumnIndex) - order_talent_rows.
    - TalentTab.dbc: stock is ordered by (OrderIndex, ID) and the client lists a class's tabs in
      file order, so an ID sort shows a mage Fire -> Frost -> Arcane (docs/bugs-and-fixes.md,
      2026-10-02).

    lib/test_client_dbc_roundtrip.py checks that every client table repacks its stock file
    byte-identically through here, which also catches a string column read as an int."""
    if table.name == "Talent":
        return pack_dbc_bytes(table, order_talent_rows(rows, base_rows), sort=False)
    if table.name == "TalentTab":
        return pack_dbc_bytes(table, sorted(rows, key=lambda r: (r["OrderIndex"], r["ID"])), sort=False)
    return pack_dbc_bytes(table, rows)


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
