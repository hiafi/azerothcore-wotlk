"""dbcfile's precompiled-struct read_dbc / pack_dbc_bytes must match the original per-field
implementation exactly (kept verbatim below as _old_*): same rows (key order, types), same bytes.

Real-file comparisons need the stock files in var/extractors/dbc/ (skipped per table when absent).
"""

import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import dbcfile, dbcfmt, state  # noqa: E402
from lib.dbcfile import MAGIC  # noqa: E402
from lib.dbcfmt import DbcTable  # noqa: E402

ALL = [t for t in vars(dbcfmt).values() if isinstance(t, DbcTable)]


# --- verbatim copies of the original implementations -------------------------------------------

def _old_read_dbc(path: Path, table: DbcTable) -> list[dict]:
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




def _old_pack_string_pool(rows: list[dict], table: DbcTable):
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




def _old_pack_dbc_bytes(table: DbcTable, rows: list[dict], *, sort: bool = True) -> bytes:
    """Pack rows into a binary WDBC file's bytes.

    By default, rows are sorted by the table's index column — reproducible and correct for
    every table this pipeline touches except Talent.dbc, whose physical row order is
    load-bearing to the client (see order_talent_rows). Pass `sort=False` with `rows` already in
    the exact desired physical order to skip the default sort.
    """
    if sort:
        rows = sorted(rows, key=lambda r: r[table.index_column])
    record_size = 4 * len(table.fmt)  # every field here is exactly 4 bytes
    string_pool, string_offsets = _old_pack_string_pool(rows, table)

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


# --- tests --------------------------------------------------------------------------------------

def _same_rows(test, new, old):
    test.assertEqual(len(new), len(old))
    for n, o in zip(new, old):
        test.assertEqual(list(n), list(o))  # key order
        test.assertEqual(n, o)
        for k in n:
            test.assertIs(type(n[k]), type(o[k]), k)


def _write(tmp, table, raw):
    path = Path(tmp) / table.dbc_filename
    path.write_bytes(raw)
    return path


def _mini_table(fmt, columns, **kw):
    return DbcTable("Mini", "Mini.dbc", "mini", fmt, tuple(columns), **kw)


class RealFilesMatchOldImplementation(unittest.TestCase):
    def test_every_extracted_table(self):
        seen = 0
        for table in ALL:
            path = state.BASE_DBC_DIR / table.dbc_filename
            if not path.is_file():
                continue
            with self.subTest(table=table.dbc_filename):
                try:
                    old_rows = _old_read_dbc(path, table)
                except ValueError:
                    continue  # fmt doesn't describe this file (field count mismatch)
                seen += 1
                new_rows = dbcfile.read_dbc(path, table)
                _same_rows(self, new_rows, old_rows)
                self.assertEqual(dbcfile.pack_dbc_bytes(table, new_rows), _old_pack_dbc_bytes(table, old_rows))
                self.assertEqual(
                    dbcfile.pack_dbc_bytes(table, new_rows, sort=False),
                    _old_pack_dbc_bytes(table, old_rows, sort=False),
                )
        if not seen:
            self.skipTest("no extracted DBCs")


class SyntheticEdgeCases(unittest.TestCase):
    def roundtrip(self, table, rows):
        new = dbcfile.pack_dbc_bytes(table, rows)
        self.assertEqual(new, _old_pack_dbc_bytes(table, rows))
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, table, new)
            back = dbcfile.read_dbc(path, table)
            _same_rows(self, back, _old_read_dbc(path, table))
        return back

    def test_signed_float_string_columns(self):
        table = _mini_table("nifsss", ("ID", "Signed", "Ratio", "Name", "Note", "Alias"),
                            signed=frozenset({"Signed"}), read_as_string=frozenset({"Alias"}))
        rows = [
            {"ID": 3, "Signed": -5, "Ratio": -1.5, "Name": "caf\u00e9 \u4e2d\u6587", "Note": "", "Alias": "x"},
            {"ID": 1, "Signed": 2147483647, "Ratio": 0.1, "Name": None, "Note": "dup", "Alias": "dup"},
            {"ID": 2, "Signed": -2147483648, "Ratio": 3, "Name": "dup", "Note": "dup"},
            {"ID": 4},  # every other column missing
            {"ID": 5, "Signed": None, "Ratio": None, "Name": 0, "Note": None, "Alias": ""},
            {"ID": 6, "Signed": 4294967295, "Ratio": True},  # unsigned value in a signed column wraps back
        ]
        back = self.roundtrip(table, rows)
        self.assertEqual([r["ID"] for r in back], [1, 2, 3, 4, 5, 6])
        self.assertEqual(back[2]["Signed"], -5)
        self.assertEqual(back[2]["Name"], "caf\u00e9 \u4e2d\u6587")
        self.assertIsInstance(back[2]["Ratio"], float)

    def test_invalid_utf8_is_replaced(self):
        table = _mini_table("ns", ("ID", "S"))
        raw = struct.pack("<4sIIII", MAGIC, 1, 2, 8, 4) + struct.pack("<II", 1, 1) + b"\x00\xff\xfe\x00"
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, table, raw)
            new = dbcfile.read_dbc(path, table)
            _same_rows(self, new, _old_read_dbc(path, table))
        self.assertEqual(new[0]["S"], "\ufffd\ufffd")

    def test_shared_string_offset_and_empty_table(self):
        table = _mini_table("nss", ("ID", "A", "B"))
        raw = struct.pack("<4sIIII", MAGIC, 2, 3, 12, 3) + struct.pack("<IIIIII", 1, 1, 1, 2, 0, 1) + b"\x00h\x00"
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, table, raw)
            _same_rows(self, dbcfile.read_dbc(path, table), _old_read_dbc(path, table))
        self.assertEqual(self.roundtrip(table, []), [])

    def test_byte_columns_read(self):
        table = _mini_table("nbXs", ("ID", "B1", "B2", "S"))
        # record: u32, u8, u8, u32 string offset -> 10 bytes
        raw = (struct.pack("<4sIIII", MAGIC, 2, 4, 10, 3)
               + struct.pack("<IBBI", 7, 200, 9, 1) + struct.pack("<IBBI", 8, 1, 2, 0) + b"\x00a\x00")
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, table, raw)
            new = dbcfile.read_dbc(path, table)
            _same_rows(self, new, _old_read_dbc(path, table))
        self.assertEqual(new, [{"ID": 7, "B1": 200, "B2": 9, "S": "a"}, {"ID": 8, "B1": 1, "B2": 2, "S": ""}])

    def test_record_size_larger_than_fields(self):
        table = _mini_table("nn", ("ID", "V"))
        raw = (struct.pack("<4sIIII", MAGIC, 2, 2, 12, 1) + struct.pack("<III", 1, 2, 99)
               + struct.pack("<III", 3, 4, 99) + b"\x00")
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, table, raw)
            _same_rows(self, dbcfile.read_dbc(path, table), _old_read_dbc(path, table))

    def test_unsupported_chars(self):
        table = _mini_table("nb", ("ID", "B"))
        with self.assertRaises(ValueError) as old_err:
            _old_pack_dbc_bytes(table, [{"ID": 1, "B": 1}])
        with self.assertRaises(ValueError) as new_err:
            dbcfile.pack_dbc_bytes(table, [{"ID": 1, "B": 1}])
        self.assertEqual(str(new_err.exception), str(old_err.exception))
        self.assertEqual(dbcfile.pack_dbc_bytes(table, []), _old_pack_dbc_bytes(table, []))
        bad = _mini_table("nZ", ("ID", "Z"))
        raw = struct.pack("<4sIIII", MAGIC, 1, 2, 8, 1) + struct.pack("<II", 1, 2) + b"\x00"
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, bad, raw)
            with self.assertRaises(ValueError) as old_err:
                _old_read_dbc(path, bad)
            with self.assertRaises(ValueError) as new_err:
                dbcfile.read_dbc(path, bad)
            self.assertEqual(str(new_err.exception), str(old_err.exception))

    def test_header_errors(self):
        table = _mini_table("nn", ("ID", "V"))
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, table, struct.pack("<4sIIII", b"XXXX", 0, 2, 8, 1) + b"\x00")
            with self.assertRaises(ValueError):
                dbcfile.read_dbc(path, table)
            path = _write(tmp, table, struct.pack("<4sIIII", MAGIC, 0, 3, 8, 1) + b"\x00")
            with self.assertRaises(ValueError):
                dbcfile.read_dbc(path, table)


if __name__ == "__main__":
    unittest.main()
