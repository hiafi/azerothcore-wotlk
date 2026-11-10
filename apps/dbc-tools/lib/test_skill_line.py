"""
override_skill_line() (crafting rework C2): the full-row override of a stock SkillLine row, the `skillline_dbc`
SPELL_TABLES entry it feeds and the patch-Z SkillLine.dbc merge, plus the C2 declarations in source/world/crafting.py
(Herbalism, Mining and Skinning to the secondary category; the 18 gathering perk rows to AcquireMethod 0).

The tests that need the stock files (var/extractors/dbc/SkillLine.dbc, copied from the worldserver's DBC directory, and
SkillLineAbility.dbc) are skipped when they are missing; the rest run on a fixture row.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_skill_line.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import generate  # noqa: E402
from lib import build, dbcfile, dbcfmt, drop_guard, spell_tables, state  # noqa: E402
from lib.table_testkit import (  # noqa: E402
    codestyle_sql, generated_file, index_for, load_dsl, read_back, render, spec_for,
)
from lib.dsl import registry  # noqa: E402

TABLE = "skillline_dbc"
COLUMNS = spell_tables.SKILLLINE_COLUMNS
STOCK_FILE = state.BASE_DBC_DIR / dbcfmt.SKILLLINE.dbc_filename
SLA_FILE = state.BASE_DBC_DIR / dbcfmt.SKILLLINEABILITY.dbc_filename
CRAFTING_FILE = TOOL_ROOT / "source" / "world" / "crafting.py"

_STRINGS = {c for c in COLUMNS if "_Lang_" in c and not c.endswith("_Mask")}
FIXTURE = {
    186: {c: ("" if c in _STRINGS else 0) for c in COLUMNS} | {
        "ID": 186, "CategoryID": 11, "DisplayName_Lang_enUS": "Mining", "DisplayName_Lang_Mask": 16712190,
        "Description_Lang_enUS": "Higher mining skill ...", "Description_Lang_Mask": 16712190, "SpellIconID": 2418,
        "AlternateVerb_Lang_Mask": 16712172,
    },
}

MINING = "from lib.dsl.registry import SkillCategory, override_skill_line\n" \
         "override_skill_line(186, CategoryID=SkillCategory.SECONDARY)\n"


def _bundle(rows=None) -> dict:
    return spell_tables.dsl_live_data({}, {}, skillline_rows=FIXTURE if rows is None else rows)


class FixtureHelperTest(unittest.TestCase):
    def test_the_override_changes_only_the_named_column(self):
        (row,) = load_dsl(MINING, live_data=_bundle())["skill_lines"]
        self.assertEqual(row, dict(FIXTURE[186], CategoryID=9, id=186))
        self.assertIs(type(row["CategoryID"]), int)  # the IntEnum is stored as a plain int

    def test_the_struct_names_are_accepted(self):
        for call, column, value in (("categoryId=9", "CategoryID", 9), ("spellIcon=1", "SpellIconID", 1),
                                    ("canLink=1", "CanLink", 1)):
            with self.subTest(call=call):
                source = f"from lib.dsl.registry import override_skill_line\noverride_skill_line(186, {call})\n"
                self.assertEqual(load_dsl(source, live_data=_bundle())["skill_lines"][0][column], value)

    def test_errors(self):
        head = "from lib.dsl.registry import override_skill_line\n"
        with self.assertRaisesRegex(KeyError, "no such column"):
            load_dsl(head + "override_skill_line(186, Category=9)\n", live_data=_bundle())
        with self.assertRaisesRegex(ValueError, "no stock SkillLine row for id 999"):
            load_dsl(head + "override_skill_line(999, CategoryID=9)\n", live_data=_bundle())
        with self.assertRaisesRegex(ValueError, "ID column is the key"):
            load_dsl(head + "override_skill_line(186, ID=187)\n", live_data=_bundle())
        for bad in ("CategoryID='9'", "CategoryID=None", "CategoryID=True", "DisplayName_Lang_enUS=5"):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "must be"):
                load_dsl(head + f"override_skill_line(186, {bad})\n", live_data=_bundle())

    def test_the_same_id_in_two_files_is_a_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.py", "b.py"):
                (Path(d) / name).write_text(MINING)
            with self.assertRaises(registry.DuplicateIdError):
                registry.load_classes_dir(Path(d), live_data=_bundle())

    def test_a_missing_stock_file_raises_the_error_generate_prints(self):
        with self.assertRaisesRegex(registry.MissingStockFileError, "SkillLine.dbc is missing"):
            load_dsl(MINING, live_data=_bundle({}))

    def test_a_missing_bundle_raises(self):
        with self.assertRaisesRegex(RuntimeError, "override_skill_line\\(\\) needs the live skillline rows"):
            load_dsl(MINING)
        with self.assertRaisesRegex(RuntimeError, "needs the live skillline rows"):
            load_dsl(MINING, live_data=spell_tables.dsl_live_data({}, {}))

    def test_outside_a_load_the_helper_raises(self):
        with self.assertRaises(RuntimeError):
            registry.override_skill_line(186, CategoryID=9)

    def test_the_lazy_bundle_entry_is_not_loaded_unless_the_helper_runs(self):
        def boom():
            raise AssertionError("the SkillLine stock rows must not load when no file overrides a row")

        live = spell_tables.dsl_live_data({}, {}, skillline_rows=boom)
        load_dsl("from lib.dsl.registry import spell\nspell(id=200001, name='x', cast_time_ms=0)\n", live_data=live)


class FixtureRenderTest(unittest.TestCase):
    def setUp(self):
        self.dsl = load_dsl(MINING, live_data=_bundle())
        self.block = render(TABLE, index_for(TABLE, []), self.dsl["skill_lines"])

    def test_the_full_row_renders_in_column_order(self):
        self.assertTrue(self.block.startswith("DELETE FROM `skillline_dbc` WHERE (`ID`) IN ((186));"))
        cols = ", ".join(f"`{c}`" for c in COLUMNS)
        self.assertIn(f"INSERT INTO `skillline_dbc` ({cols}) VALUES", self.block)
        self.assertEqual(len(COLUMNS), 56)

    def test_the_block_passes_the_real_sql_codestyle_check(self):
        done = codestyle_sql(self.block)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_a_rerun_over_the_read_back_row_emits_nothing(self):
        live = read_back(self.block, TABLE, COLUMNS)
        self.assertEqual(len(live), 1)
        self.assertEqual(render(TABLE, index_for(TABLE, live), self.dsl["skill_lines"]), "")

    def test_a_dropped_declaration_is_pruned(self):
        with generated_file(self.block):
            emitted = spell_tables.load_generated_table_rows(TABLE, spec_for(TABLE).key_columns)
        self.assertEqual([int(r["ID"]) for r in emitted], [186])
        result = index_for(TABLE, emitted, emitted=emitted).rows_to_prune(spec_for(TABLE), [])
        self.assertEqual(result.keys, [(186.0,)])
        self.assertFalse(result.breaker_tripped)

    def test_the_client_rows_are_the_dbc_shape(self):
        rows = generate._skill_line_rows(self.dsl["skill_lines"])
        self.assertEqual(set(rows), {186})
        self.assertEqual(tuple(rows[186]), COLUMNS)  # no bookkeeping key ("id") leaks into the client row
        self.assertEqual(rows[186]["CategoryID"], 9)

    def test_the_drop_guard_knows_the_client_file(self):
        self.assertEqual(drop_guard.CLIENT_TABLES["SkillLine.dbc"], ("skillline_dbc", ()))


@unittest.skipUnless(STOCK_FILE.is_file(), "var/extractors/dbc/SkillLine.dbc is not extracted")
class StockFileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = state.load_stock_rows(dbcfmt.SKILLLINE)

    def test_the_gathering_rows_are_stock_primary_professions(self):
        for skill_id, name, icon in ((182, "Herbalism", 345), (186, "Mining", 2418), (393, "Skinning", 1)):
            with self.subTest(skill=skill_id):
                row = self.stock[skill_id]
                self.assertEqual((row["CategoryID"], row["DisplayName_Lang_enUS"], row["SpellIconID"]), (11, name, icon))
        self.assertEqual(self.stock[185]["CategoryID"], 9)  # Cooking: already secondary

    def test_the_merged_file_round_trips_and_keeps_every_stock_row(self):
        dsl = load_dsl(MINING, live_data=_bundle(self.stock))
        base_rows = dbcfile.read_dbc(STOCK_FILE, dbcfmt.SKILLLINE)
        merged = {row["ID"]: row for row in base_rows}
        merged.update(generate._skill_line_rows(dsl["skill_lines"]))
        packed = dbcfile.pack_client_dbc(dbcfmt.SKILLLINE, list(merged.values()), base_rows)
        with tempfile.TemporaryDirectory() as d:
            copy = Path(d) / "SkillLine.dbc"
            copy.write_bytes(packed)
            back = {r["ID"]: r for r in dbcfile.read_dbc(copy, dbcfmt.SKILLLINE)}
        self.assertEqual(len(back), len(base_rows))
        self.assertEqual(back[186], dict(self.stock[186], CategoryID=9))
        for row in base_rows:
            if row["ID"] != 186:
                self.assertEqual(back[row["ID"]], row)

    def test_the_stock_file_round_trips_with_strings_kept_as_strings(self):
        rows = dbcfile.read_dbc(STOCK_FILE, dbcfmt.SKILLLINE)
        with tempfile.TemporaryDirectory() as d:
            copy = Path(d) / "SkillLine.dbc"
            copy.write_bytes(dbcfile.pack_dbc_bytes(dbcfmt.SKILLLINE, rows))
            self.assertEqual(dbcfile.read_dbc(copy, dbcfmt.SKILLLINE), rows)
        for row in rows:
            for column in ("Description_Lang_enUS", "AlternateVerb_Lang_enUS"):
                self.assertIsInstance(row[column], str, f"{column} of skill {row['ID']}")

    def test_the_fmt_is_dbcfmt_h(self):
        self.assertEqual(dbcfmt.SKILLLINE.fmt, "nixssssssssssssssssxxxxxxxxxxxxxxxxxxixxxxxxxxxxxxxxxxxi")


@unittest.skipUnless(STOCK_FILE.is_file() and SLA_FILE.is_file(), "SkillLine.dbc / SkillLineAbility.dbc not extracted")
class CraftingDeclarationsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sla_stock = state.load_stock_rows(dbcfmt.SKILLLINEABILITY)
        live = spell_tables.dsl_live_data(
            {}, {}, skilllineability_rows=cls.sla_stock, skilllineability_stock_rows=cls.sla_stock,
            skillline_rows=state.load_stock_rows(dbcfmt.SKILLLINE),
        )
        cls.dsl = load_dsl(CRAFTING_FILE.read_text(), live_data=live)

    def test_the_three_gathering_skills_become_secondary(self):
        rows = {r["ID"]: r for r in self.dsl["skill_lines"]}
        self.assertEqual(set(rows), {182, 186, 393})
        for row in rows.values():
            self.assertEqual(row["CategoryID"], 9)

    def test_the_18_perk_rows_stop_teaching_and_change_nothing_else(self):
        perk_spells = {
            53120, 53121, 53122, 53123, 53124, 53040,  # Toughness
            53125, 53662, 53663, 53664, 53665, 53666,  # Master of Anatomy
            55428, 55480, 55500, 55501, 55502, 55503,  # Lifeblood
        }
        entries = self.dsl["skill_line_abilities"]
        self.assertEqual(len(entries), 18)
        seen = set()
        for entry in entries:
            built = build.build_skilllineability_row(entry)
            stock = self.sla_stock[entry["id"]]
            with self.subTest(sla=entry["id"]):
                self.assertEqual(stock["AcquireMethod"], 1)
                self.assertEqual(built["AcquireMethod"], 0)
                self.assertEqual({c for c in stock if built[c] != stock[c]}, {"AcquireMethod"})
                self.assertIn(stock["SkillLine"], (182, 186, 393))
            seen.add(stock["Spell"])
        self.assertEqual(seen, perk_spells)
        # no other stock row teaches a perk spell (so none keeps teaching it)
        teaching = {i for i, r in self.sla_stock.items() if r["Spell"] in perk_spells}
        self.assertEqual(teaching, {e["id"] for e in entries})


if __name__ == "__main__":
    unittest.main()
