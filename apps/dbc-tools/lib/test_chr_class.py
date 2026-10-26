"""
chr_class() (Death Knight T1, step 4b): the full-row override of a stock ChrClasses row, and the `chrclasses_dbc`
SPELL_TABLES entry it feeds. The use is `chr_class(6, CinematicSequenceID=0)`: the server then plays the race's intro
cinematic for a new Death Knight (CharacterHandler.cpp HandlePlayerLogin: the class cinematic if non-zero, else the
race's).

The tests that need the stock file (var/extractors/dbc/ChrClasses.dbc, copied from the worldserver's DBC directory)
are skipped when it is missing; the rest run on a fixture row.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_chr_class.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import dbcfile, dbcfmt, spell_tables, state  # noqa: E402
from lib.table_testkit import (  # noqa: E402
    codestyle_sql, generated_file, index_for, load_dsl, read_back, render, spec_for,
)
from lib.dsl import registry  # noqa: E402

TABLE = "chrclasses_dbc"
COLUMNS = spell_tables.CHRCLASSES_COLUMNS
STOCK_FILE = state.BASE_DBC_DIR / dbcfmt.CHRCLASSES.dbc_filename
HAVE_STOCK = STOCK_FILE.is_file()

FIXTURE = {
    6: {column: 0 for column in COLUMNS} | {
        "ID": 6, "Field01": 9, "DisplayPower": 6, "PetNameToken": 1, "Name_Lang_enUS": "Death Knight",
        "Name_Lang_Mask": 16712190, "Name_Female_Lang_Mask": 16712172, "Name_Male_Lang_Mask": 16712172,
        "Filename": "DEATHKNIGHT", "SpellClassSet": 15, "Flags": 122, "CinematicSequenceID": 165,
        "Required_Expansion": 2,
    },
}
for _row in FIXTURE.values():  # string columns are "" in a read DBC row, not 0
    for _column in COLUMNS:
        if _column.startswith("Name") and not _column.endswith("Mask") and _column != "Name_Lang_enUS":
            _row[_column] = ""

DEATH_KNIGHT = "from lib.dsl.registry import chr_class\nchr_class(6, CinematicSequenceID=0)\n"


def _bundle(rows=None) -> dict:
    return spell_tables.dsl_live_data({}, {}, chrclasses_rows=FIXTURE if rows is None else rows)


def _stock_rows() -> dict[int, dict]:
    return state.load_stock_rows(dbcfmt.CHRCLASSES)


class FixtureHelperTest(unittest.TestCase):
    def test_the_override_changes_only_the_named_column(self):
        dsl = load_dsl(DEATH_KNIGHT, live_data=_bundle())
        (row,) = dsl["chr_classes"]
        expected = dict(FIXTURE[6], CinematicSequenceID=0, id=6)
        self.assertEqual(row, expected)

    def test_the_struct_names_are_accepted(self):
        for call, column, value in (
            ("CinematicSequence=0", "CinematicSequenceID", 0), ("powerType=3", "DisplayPower", 3),
            ("spellfamily=7", "SpellClassSet", 7), ("expansion=1", "Required_Expansion", 1),
        ):
            with self.subTest(call=call):
                dsl = load_dsl(f"from lib.dsl.registry import chr_class\nchr_class(6, {call})\n", live_data=_bundle())
                self.assertEqual(dsl["chr_classes"][0][column], value)

    def test_errors(self):
        with self.assertRaisesRegex(KeyError, "no such column"):
            load_dsl("from lib.dsl.registry import chr_class\nchr_class(6, Cinematic=0)\n", live_data=_bundle())
        with self.assertRaisesRegex(ValueError, "no stock ChrClasses row for id 12"):
            load_dsl("from lib.dsl.registry import chr_class\nchr_class(12, Flags=0)\n", live_data=_bundle())
        with self.assertRaisesRegex(ValueError, "ID column is the key"):
            load_dsl("from lib.dsl.registry import chr_class\nchr_class(6, ID=7)\n", live_data=_bundle())

    def test_a_missing_stock_file_raises_the_error_generate_prints(self):
        with self.assertRaisesRegex(registry.MissingStockFileError, "ChrClasses.dbc is missing"):
            load_dsl(DEATH_KNIGHT, live_data=_bundle({}))

    def test_a_missing_bundle_raises(self):
        with self.assertRaisesRegex(RuntimeError, "chr_class\\(\\) needs the live chrclasses rows"):
            load_dsl(DEATH_KNIGHT)
        with self.assertRaisesRegex(RuntimeError, "chr_class\\(\\) needs the live chrclasses rows"):
            load_dsl(DEATH_KNIGHT, live_data=spell_tables.dsl_live_data({}, {}))

    def test_a_lazy_bundle_entry_is_loaded_once_on_first_use(self):
        calls = []

        def lazy():
            calls.append(1)
            return FIXTURE

        live = spell_tables.dsl_live_data({}, {}, chrclasses_rows=lazy)
        load_dsl("from lib.dsl.registry import chr_class\nchr_class(6, Flags=1)\n", live_data=live)
        load_dsl("from lib.dsl.registry import chr_class\nchr_class(6, Flags=2)\n", live_data=live)
        self.assertEqual(len(calls), 1)
        load_dsl("from lib.dsl.registry import spell\nspell(id=200001, name='x', cast_time_ms=0)\n", live_data=live)

    def test_outside_a_load_the_helper_raises(self):
        with self.assertRaises(RuntimeError):
            registry.chr_class(6, CinematicSequenceID=0)

    def test_the_docstring_states_the_cinematic_rule(self):
        doc = registry.chr_class.__doc__
        self.assertIn("CharacterHandler.cpp:887-898", doc)
        self.assertIn("ChrRaces.CinematicSequence", doc)


class FixtureRenderTest(unittest.TestCase):
    def setUp(self):
        self.dsl = load_dsl(DEATH_KNIGHT, live_data=_bundle())
        self.block = render(TABLE, index_for(TABLE, []), self.dsl["chr_classes"])

    def test_the_full_row_renders_in_column_order(self):
        self.assertTrue(self.block.startswith("DELETE FROM `chrclasses_dbc` WHERE (`ID`) IN ((6));"))
        cols = ", ".join(f"`{c}`" for c in COLUMNS)
        self.assertIn(f"INSERT INTO `chrclasses_dbc` ({cols}) VALUES", self.block)
        self.assertEqual(len(COLUMNS), 60)

    def test_the_block_passes_the_real_sql_codestyle_check(self):
        done = codestyle_sql(self.block)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("❌", done.stdout)

    def test_a_rerun_over_the_read_back_row_emits_nothing(self):
        live = read_back(self.block, TABLE, COLUMNS)
        self.assertEqual(len(live), 1)
        self.assertEqual(render(TABLE, index_for(TABLE, live), self.dsl["chr_classes"]), "")

    def test_a_dropped_declaration_is_pruned(self):
        with generated_file(self.block):
            emitted = spell_tables.load_generated_table_rows(TABLE, spec_for(TABLE).key_columns)
        self.assertEqual([int(r["ID"]) for r in emitted], [6])
        index = index_for(TABLE, emitted, emitted=emitted)
        # dropping the only declaration (zero left) must still delete the overlay row: no circuit breaker here
        result = index.rows_to_prune(spec_for(TABLE), [])
        self.assertEqual(result.keys, [(6.0,)])
        self.assertFalse(result.breaker_tripped)


@unittest.skipUnless(HAVE_STOCK, "var/extractors/dbc/ChrClasses.dbc is not extracted")
class StockFileTest(unittest.TestCase):
    def test_row_6_is_the_death_knight(self):
        row = _stock_rows()[6]
        self.assertEqual(
            (row["DisplayPower"], row["SpellClassSet"], row["Required_Expansion"], row["Name_Lang_enUS"]),
            (6, 15, 2, "Death Knight"),
        )
        self.assertEqual(row["Filename"], "DEATHKNIGHT")
        self.assertGreater(row["CinematicSequenceID"], 0)  # the class cinematic the override removes

    def test_the_override_equals_the_stock_row_in_every_other_column(self):
        stock = _stock_rows()[6]
        dsl = load_dsl(DEATH_KNIGHT, live_data=spell_tables.dsl_live_data({}, {}, chrclasses_rows=_stock_rows()))
        (row,) = dsl["chr_classes"]
        differing = {c for c in COLUMNS if row[c] != stock[c]}
        self.assertEqual(differing, {"CinematicSequenceID"})
        self.assertEqual(row["CinematicSequenceID"], 0)
        self.assertEqual(
            (row["DisplayPower"], row["SpellClassSet"], row["Required_Expansion"], row["Name_Lang_enUS"]),
            (6, 15, 2, "Death Knight"),
        )

    def test_it_renders_passes_the_codestyle_check_converges_and_is_pruned_when_dropped(self):
        dsl = load_dsl(DEATH_KNIGHT, live_data=spell_tables.dsl_live_data({}, {}, chrclasses_rows=_stock_rows()))
        block = render(TABLE, index_for(TABLE, []), dsl["chr_classes"])
        done = codestyle_sql(block)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        live = read_back(block, TABLE, COLUMNS)
        self.assertEqual(render(TABLE, index_for(TABLE, live), dsl["chr_classes"]), "")
        with generated_file(block):
            emitted = spell_tables.load_generated_table_rows(TABLE, spec_for(TABLE).key_columns)
        result = index_for(TABLE, emitted, emitted=emitted).rows_to_prune(spec_for(TABLE), [])
        self.assertEqual(result.keys, [(6.0,)])

    def test_a_value_of_the_wrong_type_raises(self):
        live = spell_tables.dsl_live_data({}, {}, chrclasses_rows=_stock_rows())
        for bad in ("CinematicSequenceID=None", "CinematicSequenceID='0'", "Filename=5", "DisplayPower=1.5"):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "must be"):
                load_dsl(f"from lib.dsl.registry import chr_class\nchr_class(6, {bad})\n", live_data=live)

    def test_the_stock_file_round_trips_with_strings_kept_as_strings(self):
        rows = dbcfile.read_dbc(STOCK_FILE, dbcfmt.CHRCLASSES)
        packed = dbcfile.pack_dbc_bytes(dbcfmt.CHRCLASSES, rows)
        with tempfile.TemporaryDirectory() as d:
            copy = Path(d) / "ChrClasses.dbc"
            copy.write_bytes(packed)
            back = dbcfile.read_dbc(copy, dbcfmt.CHRCLASSES)
        self.assertEqual(back, rows)
        string_columns = {c for c in COLUMNS if c.startswith("Name") and not c.endswith("Mask")} | {"Filename"}
        for row in rows:
            for column in string_columns:
                self.assertIsInstance(row[column], str, f"{column} of class {row['ID']}")

    def test_the_fmt_marks_the_columns_the_core_reads(self):
        fmt = dbcfmt.CHRCLASSES.fmt
        for column, letter in (
            ("ID", "n"), ("DisplayPower", "i"), ("Name_Lang_enUS", "s"), ("SpellClassSet", "i"),
            ("Flags", "x"), ("CinematicSequenceID", "i"), ("Required_Expansion", "i"),
        ):
            self.assertEqual(fmt[COLUMNS.index(column)], letter, column)
        # the columns the fmt skips but the file stores as strings are read as strings
        for column in ("Filename", "Name_Female_Lang_enUS", "Name_Male_Lang_enUS"):
            self.assertEqual(fmt[COLUMNS.index(column)], "x")
            self.assertIn(column, dbcfmt.CHRCLASSES.read_as_string)


if __name__ == "__main__":
    unittest.main()
