"""
spell_threat() / remove_spell_threat() (Death Knight T1, step 3): the helpers, the spell_threat SPELL_TABLES entry and
its removal entry, and the unknown-spell lint.

Covered, per the handoff: a new row, a stock override (52212 pctMod 2.0) and a removal render and converge through
the real readers; a live `1.9` and a declared `1.9` read as unchanged; `flatMod NULL` vs a declared `None` is
unchanged; declaring and removing one key raises; an unknown spell warns.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_spell_threat.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import lint, spell_tables, sql_out, trainer_state  # noqa: E402
from lib.table_testkit import (  # noqa: E402
    codestyle_sql, generated_file, index_for, load_dsl, no_migrations, read_back, removal_for, render, spec_for,
)
from lib.dsl import registry  # noqa: E402

TABLE = "spell_threat"
COLUMNS = spell_tables.SPELL_THREAT_COLUMNS
KEY = spec_for(TABLE).key_columns

# Stock rows as the base dump has them (data/sql/base/db_world/spell_threat.sql).
STOCK = [
    {"entry": 45524, "flatMod": 240, "pctMod": 1, "apPctMod": 0},
    {"entry": 52212, "flatMod": 0, "pctMod": 1.9, "apPctMod": 0},
    {"entry": 56815, "flatMod": 0, "pctMod": 1.75, "apPctMod": 0},
]

CLASS_FILE = '''
from lib.dsl.registry import remove_spell_threat, spell, spell_threat

fixed_tick = spell(id=203130, name="Test Tick", cast_time_ms=0)
spell_threat(fixed_tick, pct_mod=1.9)                    # a declared Spell, like Death and Decay's 52212 row
spell_threat(203131, flat_mod=240)                       # a new id carrying Chains of Ice's flat threat
spell_threat(52212, pct_mod=2.0)                         # overrides the stock row
remove_spell_threat(8056)
'''


def _load(body: str = CLASS_FILE) -> dict:
    return load_dsl(body)


class HelperTest(unittest.TestCase):
    def setUp(self):
        self.dsl = _load()
        self.rows = {r["entry"]: r for r in self.dsl["spell_threats"]}

    def test_rows_carry_every_column(self):
        self.assertEqual(
            self.rows[203130], {"id": 203130, "entry": 203130, "flatMod": None, "pctMod": 1.9, "apPctMod": 0.0},
        )
        self.assertEqual(self.rows[203131]["flatMod"], 240)
        self.assertEqual(self.rows[203131]["pctMod"], 1.0)
        self.assertEqual(self.rows[52212]["pctMod"], 2.0)

    def test_a_removal_holds_only_the_key(self):
        self.assertEqual(self.dsl["spell_threat_removals"], [{"id": 8056, "entry": 8056}])

    def test_validation(self):
        bad_calls = [
            "spell_threat(0)", "spell_threat(-5)", "spell_threat('52212')", "spell_threat(True)",
            "spell_threat(52212, pct_mod=-0.1)", "spell_threat(52212, pct_mod=True)",
            "spell_threat(52212, pct_mod='2')", "spell_threat(52212, ap_pct_mod=None)",
            "spell_threat(52212, flat_mod=1.5)", "spell_threat(52212, flat_mod=True)",
            "remove_spell_threat(0)", "remove_spell_threat('x')",
        ]
        for call in bad_calls:
            with self.subTest(call=call):
                with self.assertRaises(ValueError):
                    _load(f"from lib.dsl.registry import spell_threat, remove_spell_threat\n{call}\n")

    def test_zero_pct_mod_and_negative_flat_mod_are_allowed(self):
        dsl = _load(
            "from lib.dsl.registry import spell_threat\nspell_threat(47568, flat_mod=0, pct_mod=0)\n"
            "spell_threat(47569, flat_mod=-100)\n"
        )
        self.assertEqual([(r["flatMod"], r["pctMod"]) for r in dsl["spell_threats"]], [(0, 0.0), (-100, 1.0)])

    def test_outside_a_load_the_helpers_raise(self):
        with self.assertRaises(RuntimeError):
            registry.spell_threat(52212)
        with self.assertRaises(RuntimeError):
            registry.remove_spell_threat(52212)

    def test_the_same_spell_twice_is_a_duplicate(self):
        import tempfile  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            for name in ("a.py", "b.py"):
                (Path(d) / name).write_text("from lib.dsl.registry import spell_threat\nspell_threat(52212)\n")
            with self.assertRaises(registry.DuplicateIdError):
                registry.load_classes_dir(Path(d))

    def test_the_docstring_names_the_stock_rows_it_exists_for(self):
        self.assertIn("52212", registry.spell_threat.__doc__)
        self.assertIn("MOD_THREAT", registry.spell_threat.__doc__)


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.dsl = _load()
        self.block = render(TABLE, index_for(TABLE, STOCK), self.dsl["spell_threats"])

    def test_new_rows_and_the_stock_override_render(self):
        self.assertTrue(self.block.startswith("DELETE FROM `spell_threat` WHERE (`entry`) IN ("))
        self.assertIn("INSERT INTO `spell_threat` (`entry`, `flatMod`, `pctMod`, `apPctMod`) VALUES", self.block)
        self.assertIn("(203130, NULL, 1.9, 0.0)", self.block)
        self.assertIn("(203131, 240, 1.0, 0.0)", self.block)
        self.assertIn("(52212, NULL, 2.0, 0.0)", self.block)

    def test_the_block_passes_the_real_sql_codestyle_check(self):
        removal = sql_out.render_delete_only_block(TABLE, KEY, [(8056.0,)])
        done = codestyle_sql(self.block + "\n\n" + removal)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("❌", done.stdout)

    def test_a_live_1_9_and_a_declared_1_9_read_as_unchanged(self):
        declared = [{"id": 52212, "entry": 52212, "flatMod": 0, "pctMod": 1.9, "apPctMod": 0.0}]
        self.assertEqual(index_for(TABLE, STOCK).rows_to_emit(spec_for(TABLE), declared), [])
        # the int literal the base dump has for pctMod 1 against a declared float 1.0
        declared = [{"id": 45524, "entry": 45524, "flatMod": 240, "pctMod": 1.0, "apPctMod": 0.0}]
        self.assertEqual(index_for(TABLE, STOCK).rows_to_emit(spec_for(TABLE), declared), [])

    def test_a_null_flat_mod_and_a_declared_none_are_unchanged(self):
        live = [{"entry": 203130, "flatMod": None, "pctMod": 1.9, "apPctMod": 0}]
        declared = [{"id": 203130, "entry": 203130, "flatMod": None, "pctMod": 1.9, "apPctMod": 0.0}]
        self.assertEqual(index_for(TABLE, live).rows_to_emit(spec_for(TABLE), declared), [])
        # a migration that left the column out takes the schema default, NULL for flatMod, 1 for pctMod, 0 for ap
        live = [{"entry": 203130}]
        declared = [{"id": 203130, "entry": 203130, "flatMod": None, "pctMod": 1.0, "apPctMod": 0.0}]
        self.assertEqual(index_for(TABLE, live).rows_to_emit(spec_for(TABLE), declared), [])

    def test_a_changed_value_is_re_emitted(self):
        declared = [{"id": 52212, "entry": 52212, "flatMod": 0, "pctMod": 2.0, "apPctMod": 0.0}]
        self.assertEqual(len(index_for(TABLE, STOCK).rows_to_emit(spec_for(TABLE), declared)), 1)


class ConvergenceTest(unittest.TestCase):
    """Hunter T1-1: render, feed the output back through the readers the diff uses, re-render: nothing."""

    def test_a_second_build_over_the_read_back_state_emits_nothing(self):
        dsl = _load()
        first = render(TABLE, index_for(TABLE, STOCK), dsl["spell_threats"])
        live = STOCK + read_back(first, TABLE, COLUMNS)  # later files win, as SpellTableIndex orders them
        self.assertEqual(render(TABLE, index_for(TABLE, live), dsl["spell_threats"]), "")
        keyed = {r["entry"]: r for r in live}
        self.assertEqual(keyed[52212]["pctMod"], 2.0)

    def test_the_override_of_52212_converges_through_the_real_stock_rows(self):
        # the real base dump + migrations, read the way load_spell_table_index reads them
        live = trainer_state.load_table_rows(TABLE)
        self.assertIn(52212, {int(r["entry"]) for r in live})
        dsl = _load()
        first = render(TABLE, index_for(TABLE, live), dsl["spell_threats"])
        self.assertIn("(52212, NULL, 2.0, 0.0)", first)
        again = live + read_back(first, TABLE, COLUMNS)
        self.assertEqual(render(TABLE, index_for(TABLE, again), dsl["spell_threats"]), "")

    def test_a_dropped_declaration_is_pruned_and_a_stock_override_is_reported(self):
        dsl = _load()
        first = render(TABLE, index_for(TABLE, STOCK), dsl["spell_threats"])
        with generated_file(first):
            emitted = spell_tables.load_generated_table_rows(TABLE, KEY)
        self.assertEqual({int(r["entry"]) for r in emitted}, {203130, 203131, 52212})
        index = index_for(TABLE, STOCK + emitted, emitted=emitted, base=STOCK)
        kept = [r for r in dsl["spell_threats"] if r["entry"] == 203131]
        result = index.rows_to_prune(spec_for(TABLE), kept)
        self.assertEqual(result.keys, [(203130.0,)])
        self.assertEqual(result.base_blocked, [(52212.0,)])

    def test_a_removal_emits_one_key_exact_delete_and_converges(self):
        dsl = _load("from lib.dsl.registry import remove_spell_threat\nremove_spell_threat(8056)\n")
        live_keys = {(8056.0,), (52212.0,)}
        with no_migrations():
            blocks, report = spell_tables.render_removal_blocks(dsl, {TABLE: live_keys})
        (block,) = [b for b in blocks if TABLE in b]
        self.assertEqual(block.splitlines()[-1], "DELETE FROM `spell_threat` WHERE (`entry`) IN ((8056));")
        self.assertIn("removal: spell_threat (entry=8056)", "\n".join(report))
        self.assertFalse([line for line in report if line.startswith("WARNING")])
        with generated_file(block):
            again, _ = spell_tables.render_removal_blocks(dsl, {TABLE: live_keys})
        self.assertEqual([b for b in again if TABLE in b], [])

    def test_a_key_that_exists_nowhere_warns(self):
        dsl = _load("from lib.dsl.registry import remove_spell_threat\nremove_spell_threat(999999)\n")
        with no_migrations():
            _, report = spell_tables.render_removal_blocks(dsl, {TABLE: set()})
        self.assertTrue(any(line.startswith("WARNING") and "spell_threat" in line for line in report))

    def test_declaring_and_removing_the_same_key_raises(self):
        dsl = _load(
            "from lib.dsl.registry import remove_spell_threat, spell_threat\n"
            "spell_threat(52212, pct_mod=2.0)\nremove_spell_threat(52212)\n"
        )
        with self.assertRaises(spell_tables.DeclareAndRemoveConflictError):
            spell_tables.render_removal_blocks(dsl, {TABLE: {(52212.0,)}})

    def test_the_removal_table_is_keyed_on_entry(self):
        spec = removal_for(TABLE)
        self.assertEqual(
            (spec.removal_key, spec.key_columns, spec.declared_key), ("spell_threat_removals", KEY, "spell_threats"),
        )


class UnknownSpellLintTest(unittest.TestCase):
    ROW = {"id": 203140, "entry": 203140, "flatMod": None, "pctMod": 1.9, "apPctMod": 0.0}

    def test_a_spell_in_neither_set_warns(self):
        warnings = lint.check_spell_threat_rows([self.ROW], {52212, 45524})
        self.assertEqual(len(warnings), 1)
        self.assertIn("spell_threat(203140)", warnings[0])
        self.assertIn("drops the row", warnings[0])

    def test_a_built_or_stock_spell_is_silent(self):
        self.assertEqual(lint.check_spell_threat_rows([self.ROW], {203140}), [])
        self.assertEqual(lint.check_spell_threat_rows([{**self.ROW, "entry": 52212}], {52212}), [])

    def test_no_rows_is_silent(self):
        self.assertEqual(lint.check_spell_threat_rows([], set()), [])


if __name__ == "__main__":
    unittest.main()
