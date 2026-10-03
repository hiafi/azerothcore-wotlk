"""SpellDescriptionVariables.dbc support (potency-system.PLAN.md P9.1): the table definition, the
ids.yaml block, generate.py's patch wiring, and a round trip through the DBC writer."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import generate  # noqa: E402
from lib import dbcfile, dbcfmt, source, state  # noqa: E402

TABLE = dbcfmt.SPELLDESCRIPTIONVARIABLES
STOCK = state.BASE_DBC_DIR / TABLE.dbc_filename
IDS_YAML = Path(__file__).resolve().parents[1] / "source" / "ids.yaml"

# Shaped like stock entry 167 (CRLF-separated, variables referencing variables).
CUSTOM_TEXT = (
    "$p1=$?s11151[${$11151m1*0.01+1}][${1}]\r\n"
    "$p2=$?s12952[${$12952m1*0.01+1}][${$<p1>}]\r\n"
    "$mult=${$<p2>}"
)


def _round_trip(rows: list[dict]) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / TABLE.dbc_filename
        path.write_bytes(dbcfile.pack_dbc_bytes(TABLE, rows))
        return dbcfile.read_dbc(path, TABLE)


class TableDefinitionTest(unittest.TestCase):
    def test_client_only_two_column_table(self):
        self.assertEqual(TABLE.columns, ("ID", "Variables"))
        self.assertEqual(TABLE.fmt, "ns")
        self.assertEqual(TABLE.sql_table, "")
        self.assertNotIn(TABLE, dbcfmt.ALL_TABLES)

    def test_custom_row_round_trips(self):
        rows = [{"ID": 1000, "Variables": CUSTOM_TEXT}, {"ID": 1001, "Variables": "$x=${2}"}]
        self.assertEqual(_round_trip(rows), rows)


class IdsBlockTest(unittest.TestCase):
    def test_block_sits_above_stock(self):
        block = source.load_ids(IDS_YAML)["spelldescriptionvariables"]
        self.assertEqual((block["start"], block["end"]), (1000, 1999))
        self.assertGreater(block["start"], 181)  # stock file's highest id


class TooltipVarRowsTest(unittest.TestCase):
    def test_declared_entries_become_dbc_rows(self):
        rows = generate._tooltip_var_rows([{"id": 1000, "Variables": CUSTOM_TEXT}])
        self.assertEqual(rows, {1000: {"ID": 1000, "Variables": CUSTOM_TEXT}})

    def test_nothing_declared_means_no_patch_rows(self):
        self.assertEqual(generate._tooltip_var_rows([]), {})


@unittest.skipUnless(STOCK.is_file(), f"needs the stock {TABLE.dbc_filename} in {state.BASE_DBC_DIR}")
class StockFileTest(unittest.TestCase):
    def test_stock_file_repacks_byte_identical(self):
        rows = dbcfile.read_dbc(STOCK, TABLE)
        self.assertEqual(len(rows), 30)
        self.assertEqual(max(r["ID"] for r in rows), 181)
        self.assertEqual(dbcfile.pack_dbc_bytes(TABLE, rows), STOCK.read_bytes())

    def test_custom_row_merges_over_stock(self):
        merged = {r["ID"]: r for r in dbcfile.read_dbc(STOCK, TABLE)}
        merged.update(generate._tooltip_var_rows([{"id": 1000, "Variables": CUSTOM_TEXT}]))
        back = {r["ID"]: r["Variables"] for r in _round_trip(list(merged.values()))}
        self.assertEqual(len(back), 31)
        self.assertEqual(back[1000], CUSTOM_TEXT)
        self.assertTrue(back[167].startswith("$arctic1=$?s31674"))


if __name__ == "__main__":
    unittest.main()
