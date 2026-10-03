"""Guard for the client patch (docs/bugs-and-fixes.md, 2026-10-02, the TalentTab entry).

Every table generate.py can put into patch-Z.mpq must repack its own stock file byte-identically
through dbcfile.pack_client_dbc, the function generate.py uses. A failure means one of two things,
and both have shipped broken client data before:

- a string column read as an int (its value is a string-block offset, and a repack points it at
  the wrong string): TalentTab.BackgroundFile blanked every talent background, SpellRange's
  DisplayName would have garbled range text
- a table whose physical row order the client depends on: TalentTab reordered every class's
  talent tabs

Needs the stock files in var/extractors/dbc/ (skipped per table when one is missing).
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import dbcfile, dbcfmt, lint, state  # noqa: E402

CLIENT_TABLES = (*dbcfmt.ALL_TABLES, dbcfmt.SPELLDESCRIPTIONVARIABLES)

# Stock SkillLineAbility.dbc isn't ID-sorted and pack_client_dbc sorts it by ID. It has shipped
# that way in every patch-Z without spellbook problems, so its order isn't load-bearing. Rows must
# still read and write back losslessly.
ID_SORTED_ON_PURPOSE = {"SkillLineAbility"}


class ClientDbcRoundTripTest(unittest.TestCase):
    def test_every_client_table_repacks_stock_byte_identical(self):
        for table in CLIENT_TABLES:
            path = state.BASE_DBC_DIR / table.dbc_filename
            with self.subTest(table=table.dbc_filename):
                if not path.is_file():
                    self.skipTest(f"{path} not extracted")
                raw = path.read_bytes()
                rows = dbcfile.read_dbc(path, table)
                if table.name in ID_SORTED_ON_PURPOSE:
                    self.assertEqual(dbcfile.pack_dbc_bytes(table, rows, sort=False), raw)
                    continue
                self.assertEqual(
                    dbcfile.pack_client_dbc(table, rows, rows), raw,
                    f"{table.dbc_filename} doesn't survive a repack - a string column read as an int "
                    f"(add it to read_as_string) or a load-bearing row order (see pack_client_dbc)",
                )


class TalentTabOrderTest(unittest.TestCase):
    def test_tabs_pack_by_order_index_then_id(self):
        table = dbcfmt.TALENTTAB
        rows = []
        for tab_id, order in ((41, 1), (61, 2), (81, 0), (161, 0)):
            row = dbcfile.empty_row(table)
            row.update(ID=tab_id, OrderIndex=order, BackgroundFile=f"Tab{tab_id}")
            rows.append(row)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / table.dbc_filename
            path.write_bytes(dbcfile.pack_client_dbc(table, rows, rows))
            back = dbcfile.read_dbc(path, table)
        self.assertEqual([r["ID"] for r in back], [81, 161, 41, 61])
        self.assertEqual(back[0]["BackgroundFile"], "Tab81")



class ClientPatchLintTest(unittest.TestCase):
    STOCK = {"TalentTab": {398: {"ID": 398, "RaceMask": -260097, "OrderIndex": 0}}}

    def test_talenttab_shipping_names_rows_and_columns(self):
        shipping = {"TalentTab": {398: {"ID": 398, "RaceMask": 4294707199, "OrderIndex": 0}}}
        warnings = lint.check_client_patch(shipping, self.STOCK, {"TalentTab.dbc"})
        self.assertEqual(len(warnings), 1)
        self.assertIn("talent frame", warnings[0])
        self.assertIn("398 (RaceMask: -260097 -> 4294707199)", warnings[0])

    def test_new_and_dropped_tables_vs_last_build(self):
        shipping = {"Spell": {1: {}}, "SpellRange": {30200: {}}}
        warnings = lint.check_client_patch(shipping, {}, {"Spell.dbc", "Item.dbc"})
        self.assertEqual(len(warnings), 2)
        self.assertIn("SpellRange.dbc is new in the client patch", warnings[0])
        self.assertIn("Item.dbc was in the last client patch build", warnings[1])

    def test_unchanged_file_set_and_first_build_are_quiet(self):
        shipping = {"Spell": {1: {}}, "Item": {70001: {}}}
        self.assertEqual(lint.check_client_patch(shipping, {}, {"Spell.dbc", "Item.dbc"}), [])
        self.assertEqual(lint.check_client_patch(shipping, {}, None), [])


if __name__ == "__main__":
    unittest.main()
