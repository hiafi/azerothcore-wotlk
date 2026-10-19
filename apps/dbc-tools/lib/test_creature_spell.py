"""
creature_spell() / remove_creature_spell() (shaman-rework T1, step 2): the helpers, the creature_template_spell
SPELL_TABLES entry they feed, and its removal entry.

Covered, per the handoff: a new totem row and an override of stock 15439 Index 0 render; the block passes the real
codestyle-sql.py (a no-op `git` shim keeps it off the network, as hunter T1 did); convergence (hunter T1-1: render,
feed the output back through the live-state reader the diff uses, re-render, get nothing); a removal emits one
key-exact DELETE; the P0 spike's hand-written rows are left alone; a bad index and an unknown entry raise, an unknown
spell warns.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_creature_spell.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import lint, spell_tables, sql_dump, sql_out, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402

COLUMNS = spell_tables.CREATURE_TEMPLATE_SPELL_COLUMNS
TABLE = "creature_template_spell"
SPEC = next(spec for spec in spell_tables.SPELL_TABLES if spec.name == TABLE)
REMOVAL = next(spec for spec in spell_tables.REMOVAL_TABLES if spec.table_name == TABLE)

IDS_CFG = {"creature": {"start": 300000, "end": 300999}}
# Stock rows as the base dump has them (VerifiedBuild 12340): the fire elemental totem keeps its summon on Index 0.
STOCK = [
    {"CreatureID": 15439, "Index": 0, "Spell": 32982, "VerifiedBuild": 12340},
    {"CreatureID": 3579, "Index": 0, "Spell": 5728, "VerifiedBuild": 12340},
    {"CreatureID": 3579, "Index": 1, "Spell": 55328, "VerifiedBuild": 12340},
]
# The P0 spike's hand-written rows (rev_1792393868936008368.sql): live, but this tool never emitted them.
SPIKE = [
    {"CreatureID": 300298, "Index": 0, "Spell": 32982, "VerifiedBuild": 0},
    {"CreatureID": 300299, "Index": 0, "Spell": 202761, "VerifiedBuild": 0},
]

CLASS_FILE = '''
from lib.dsl.registry import creature_spell, remove_creature_spell, spell

pulse = spell(id=202761, name="Test Pulse", cast_time_ms=0)
creature_spell(300270, 0, pulse)                    # a Spell object
creature_spell(300271, 0, 32982)                    # a stock guardian summon on Index 0
creature_spell(15439, 0, 202761)                    # overrides the stock row
remove_creature_spell(300298, 0)
'''


def _load(source: str = CLASS_FILE, creature_rows=None) -> dict:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "shaman.py"
        path.write_text(source)
        reg = registry.load_class_file(
            path, ids_cfg=IDS_CFG,
            existing_creature_rows={15439: {}, 300298: {}, 300299: {}} if creature_rows is None else creature_rows,
        )
    return {k: getattr(reg, k) for k in registry.MERGE_KEYS}


def _index(live: list[dict], emitted: list[dict] | None = None, base: list[dict] | None = None):
    return spell_tables.SpellTableIndex(
        {TABLE: live}, emitted={TABLE: emitted or []}, base={TABLE: base or []}, tables=(SPEC,),
    )


def _blocks(index, dsl):
    rows = index.rows_to_emit(SPEC, dsl["creature_template_spells"])
    return sql_out.render_generic_table_block(TABLE, COLUMNS, SPEC.key_columns, rows)


class HelperTest(unittest.TestCase):
    def setUp(self):
        self.dsl = _load()

    def test_rows_carry_every_column(self):
        rows = {(r["CreatureID"], r["Index"]): r for r in self.dsl["creature_template_spells"]}
        self.assertEqual(
            rows[(300270, 0)],
            {"id": "300270:0", "CreatureID": 300270, "Index": 0, "Spell": 202761, "VerifiedBuild": 0},
        )
        self.assertEqual(rows[(300271, 0)]["Spell"], 32982)
        self.assertEqual(rows[(15439, 0)]["Spell"], 202761)

    def test_a_removal_holds_only_the_key(self):
        (removal,) = self.dsl["creature_spell_removals"]
        self.assertEqual(removal, {"id": "300298:0", "CreatureID": 300298, "Index": 0})

    def test_verified_build_none_reproduces_a_null_column(self):
        dsl = _load('from lib.dsl.registry import creature_spell\ncreature_spell(300270, 1, 5, verified_build=None)\n')
        self.assertIsNone(dsl["creature_template_spells"][0]["VerifiedBuild"])

    def test_bad_index_raises(self):
        for index in (-1, 8, 99, "0", 1.0, True):
            with self.subTest(index=index):
                with self.assertRaisesRegex(ValueError, "index must be an int in 0..7"):
                    _load(f'from lib.dsl.registry import creature_spell\ncreature_spell(300270, {index!r}, 5)\n')
                with self.assertRaisesRegex(ValueError, "index must be an int in 0..7"):
                    _load(
                        "from lib.dsl.registry import remove_creature_spell\n"
                        f"remove_creature_spell(300270, {index!r})\n"
                    )

    def test_unknown_entry_raises(self):
        with self.assertRaisesRegex(ValueError, "entry 9999999 is neither"):
            _load('from lib.dsl.registry import creature_spell\ncreature_spell(9999999, 0, 5)\n')
        with self.assertRaisesRegex(ValueError, "entry 12345 is neither"):
            _load('from lib.dsl.registry import remove_creature_spell\nremove_creature_spell(12345, 0)\n')

    def test_an_existing_creature_outside_the_block_is_fine(self):
        _load('from lib.dsl.registry import creature_spell\ncreature_spell(777, 0, 5)\n', creature_rows={777: {}})

    def test_non_positive_spell_raises(self):
        with self.assertRaises(ValueError):
            _load('from lib.dsl.registry import creature_spell\ncreature_spell(300270, 0, 0)\n')

    def test_outside_a_load_the_helpers_raise(self):
        with self.assertRaises(RuntimeError):
            registry.creature_spell(300270, 0, 5)
        with self.assertRaises(RuntimeError):
            registry.remove_creature_spell(300270, 0)

    def test_the_same_slot_twice_is_a_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.py", "b.py"):
                (Path(d) / name).write_text(
                    'from lib.dsl.registry import creature_spell\ncreature_spell(300270, 0, 5)\n'
                )
            with self.assertRaises(registry.DuplicateIdError):
                registry.load_classes_dir(Path(d), ids_cfg=IDS_CFG, existing_creature_rows={})

    def test_the_docstring_states_the_index_zero_rule(self):
        self.assertIn("Index 0", registry.creature_spell.__doc__)
        self.assertIn("m_spells[0]", registry.creature_spell.__doc__)


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.dsl = _load()

    def test_a_new_totem_row_renders(self):
        block = _blocks(_index(STOCK), self.dsl)
        self.assertIn("(300270, 0, 202761, 0)", block)
        self.assertIn("(300271, 0, 32982, 0)", block)
        self.assertTrue(block.startswith("DELETE FROM `creature_template_spell` WHERE (`CreatureID`, `Index`) IN ("))
        self.assertIn(
            "INSERT INTO `creature_template_spell` (`CreatureID`, `Index`, `Spell`, `VerifiedBuild`) VALUES", block,
        )

    def test_an_override_of_stock_15439_index_0_renders(self):
        block = _blocks(_index(STOCK), self.dsl)
        self.assertIn("(15439, 0, 202761, 0)", block)
        self.assertIn("(15439, 0)", block.split(";")[0])  # the DELETE names the stock key

    def test_a_declaration_equal_to_live_is_not_re_emitted(self):
        live = STOCK + [{"CreatureID": 300270, "Index": 0, "Spell": 202761, "VerifiedBuild": 0}]
        rows = _index(live).rows_to_emit(SPEC, self.dsl["creature_template_spells"])
        self.assertNotIn(300270, {r["CreatureID"] for r in rows})

    def test_the_block_passes_the_real_sql_codestyle_check(self):
        text = (
            "-- Generated by apps/dbc-tools/generate.py - DO NOT hand-edit.\n\n"
            + _blocks(_index(STOCK), self.dsl) + "\n\n"
            + sql_out.render_delete_only_block(TABLE, SPEC.key_columns, [(300298.0, 0.0)]) + "\n"
        )
        with tempfile.TemporaryDirectory() as d:
            pending = Path(d) / "data" / "sql" / "updates" / "pending_db_world"
            pending.mkdir(parents=True)
            (pending / "rev_1.sql").write_text(text, encoding="utf-8")
            # codestyle-sql.py ends with `git fetch` + `git diff` against origin/Playerbot; a no-op `git` first on PATH
            # keeps this off the network. The per-file checks on the scratch pending file are what it is for.
            fake_bin = Path(d) / "bin"
            fake_bin.mkdir()
            (fake_bin / "git").write_text("#!/bin/sh\nexit 0\n")
            (fake_bin / "git").chmod(0o755)
            done = subprocess.run(
                [sys.executable, str(REPO_ROOT / "apps" / "codestyle" / "codestyle-sql.py")],
                cwd=d, capture_output=True, text=True, env={**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}"},
            )
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("❌", done.stdout)


class ConvergenceTest(unittest.TestCase):
    """Hunter T1-1: what is rendered must be read back by the reader the diff uses, so a rerun emits nothing."""

    def _read_back(self, sql: str) -> list[dict]:
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "rev_1.sql"
            path.write_text(spell_tables.GENERATED_MARKER + "\n\n" + sql + "\n", encoding="utf-8")
            return sql_dump.read_table_rows(path, TABLE, COLUMNS)

    def test_a_second_build_over_the_read_back_state_emits_nothing(self):
        dsl = _load()
        first = _blocks(_index(STOCK), dsl)
        self.assertTrue(first)
        # Later files win, exactly as load_table_rows + SpellTableIndex order them: stock first, then the new rows.
        live = STOCK + self._read_back(first)
        self.assertEqual(_blocks(_index(live), dsl), "")
        self.assertEqual(spell_tables.SpellTableIndex({TABLE: live}, tables=(SPEC,)).rows_to_emit(
            SPEC, dsl["creature_template_spells"]), [])

    def test_the_overridden_stock_row_is_what_the_index_reads_back(self):
        dsl = _load()
        live = STOCK + self._read_back(_blocks(_index(STOCK), dsl))
        keyed = {(r["CreatureID"], r["Index"]): r for r in live}
        self.assertEqual(keyed[(15439, 0)]["Spell"], 202761)

    def test_a_dropped_declaration_is_pruned_through_the_generated_file_replay(self):
        dsl = _load()
        first = _blocks(_index(STOCK + SPIKE), dsl)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "rev_1.sql"
            path.write_text(spell_tables.GENERATED_MARKER + "\n\n" + first + "\n", encoding="utf-8")
            with mock.patch.object(trainer_state, "_migration_files_mentioning", return_value=[path]):
                emitted = spell_tables.load_generated_table_rows(TABLE, SPEC.key_columns)
        self.assertEqual({(r["CreatureID"], r["Index"]) for r in emitted}, {(300270, 0), (300271, 0), (15439, 0)})
        index = _index(STOCK + SPIKE + emitted, emitted=emitted, base=STOCK)
        # only 300271 stays declared: 300270 is pruned, the stock-owned 15439 override is reported, the spike stays
        kept = [r for r in dsl["creature_template_spells"] if r["CreatureID"] == 300271]
        result = index.rows_to_prune(SPEC, kept)
        self.assertEqual(result.keys, [(300270.0, 0.0)])
        self.assertEqual(result.base_blocked, [(15439.0, 0.0)])

    def test_a_removal_converges_through_load_removed_keys(self):
        dsl = _load()
        # hermetic: ignore the working tree's pending migrations (a real generated rev may already hold this DELETE)
        with mock.patch.object(trainer_state, "_migration_files_mentioning", return_value=[]):
            blocks, report = spell_tables.render_removal_blocks(dsl, {TABLE: {(300298.0, 0.0)}})
        creature_blocks = [b for b in blocks if "creature_template_spell" in b]
        self.assertEqual(len(creature_blocks), 1)
        self.assertIn("removal: creature_template_spell (CreatureID=300298, Index=0)", "\n".join(report))
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "rev_1.sql"
            path.write_text(spell_tables.GENERATED_MARKER + "\n\n" + creature_blocks[0] + "\n", encoding="utf-8")
            with mock.patch.object(trainer_state, "_migration_files_mentioning", return_value=[path]):
                again, _ = spell_tables.render_removal_blocks(dsl, {TABLE: {(300298.0, 0.0)}})
        self.assertEqual([b for b in again if "creature_template_spell" in b], [])


class RemovalTest(unittest.TestCase):
    def setUp(self):
        # hermetic: ignore the working tree's pending migrations (a real generated rev may already hold these DELETEs)
        patcher = mock.patch.object(trainer_state, "_migration_files_mentioning", return_value=[])
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_removal_emits_one_key_exact_delete(self):
        dsl = _load('from lib.dsl.registry import remove_creature_spell\nremove_creature_spell(300298, 0)\n')
        blocks, report = spell_tables.render_removal_blocks(dsl, {TABLE: {(300298.0, 0.0)}})
        creature_blocks = [b for b in blocks if "creature_template_spell" in b]
        self.assertEqual(len(creature_blocks), 1)
        statement = creature_blocks[0].splitlines()[-1]
        self.assertEqual(
            statement, "DELETE FROM `creature_template_spell` WHERE (`CreatureID`, `Index`) IN ((300298, 0));",
        )
        self.assertNotIn("INSERT", creature_blocks[0])
        self.assertFalse([line for line in report if line.startswith("WARNING")])

    def test_the_spike_removals_are_two_keys_in_one_statement(self):
        dsl = _load(
            'from lib.dsl.registry import remove_creature_spell\n'
            'remove_creature_spell(300298, 0)\nremove_creature_spell(300299, 0)\n',
        )
        live = {(300298.0, 0.0), (300299.0, 0.0)}
        (block,) = [b for b in spell_tables.render_removal_blocks(dsl, {TABLE: live})[0] if TABLE in b]
        self.assertIn("IN ((300298, 0), (300299, 0));", block)

    def test_a_key_that_exists_nowhere_warns(self):
        dsl = _load('from lib.dsl.registry import remove_creature_spell\nremove_creature_spell(300298, 3)\n')
        _, report = spell_tables.render_removal_blocks(dsl, {TABLE: set()})
        self.assertTrue(any(line.startswith("WARNING") and "creature_template_spell" in line for line in report))

    def test_declaring_and_removing_the_same_slot_raises(self):
        dsl = _load(
            'from lib.dsl.registry import creature_spell, remove_creature_spell\n'
            'creature_spell(300270, 0, 5)\nremove_creature_spell(300270, 0)\n',
        )
        with self.assertRaises(spell_tables.DeclareAndRemoveConflictError):
            spell_tables.render_removal_blocks(dsl, {TABLE: set()})


class SpikeRowsTest(unittest.TestCase):
    """The P0 spike's rows are live but hand-written: never pruned, never re-emitted."""

    def test_they_are_neither_pruned_nor_emitted_when_undeclared(self):
        dsl = _load(
            'from lib.dsl.registry import creature_spell\ncreature_spell(300270, 0, 5)\n',
        )
        index = _index(STOCK + SPIKE)  # emitted=[]: this tool never wrote them
        self.assertEqual({r["CreatureID"] for r in index.rows_to_emit(SPEC, dsl["creature_template_spells"])}, {300270})
        self.assertEqual(index.rows_to_prune(SPEC, dsl["creature_template_spells"]).keys, [])

    def test_a_declared_row_this_tool_emitted_is_pruned_when_dropped(self):
        emitted = [{"CreatureID": 300270, "Index": 0, "Spell": 202761, "VerifiedBuild": 0}]
        index = _index(STOCK + SPIKE + emitted, emitted=emitted, base=STOCK)
        # still declared by something else, so the breaker does not trip; the dropped key is the orphan
        result = index.rows_to_prune(SPEC, [{"CreatureID": 300271, "Index": 0, "Spell": 5, "VerifiedBuild": 0}])
        self.assertEqual(result.keys, [(300270.0, 0.0)])
        self.assertEqual(result.base_blocked, [])

    def test_a_dropped_override_of_a_stock_row_is_reported_not_deleted(self):
        emitted = [{"CreatureID": 15439, "Index": 0, "Spell": 202761, "VerifiedBuild": 0}]
        index = _index(STOCK + emitted, emitted=emitted, base=STOCK)
        result = index.rows_to_prune(SPEC, [{"CreatureID": 300271, "Index": 0, "Spell": 5, "VerifiedBuild": 0}])
        self.assertEqual(result.keys, [])
        self.assertEqual(result.base_blocked, [(15439.0, 0.0)])

    def test_the_real_prune_render_reports_the_stock_blocked_row(self):
        emitted = [{"CreatureID": 15439, "Index": 0, "Spell": 202761, "VerifiedBuild": 0}]
        index = spell_tables.SpellTableIndex(
            {spec.name: (STOCK + emitted if spec.name == TABLE else []) for spec in spell_tables.SPELL_TABLES},
            emitted={TABLE: emitted}, base={TABLE: STOCK},
        )
        dsl = {spec.registry_key: [] for spec in spell_tables.SPELL_TABLES}
        dsl["creature_template_spells"] = [{"CreatureID": 300271, "Index": 0, "Spell": 5, "VerifiedBuild": 0}]
        blocks, report = spell_tables.render_prune_blocks(index, dsl)
        self.assertEqual(blocks, [])
        self.assertTrue(any("NOT removing creature_template_spell" in line for line in report))

    def test_the_real_prune_render_deletes_only_what_was_emitted(self):
        emitted = [{"CreatureID": 300270, "Index": 0, "Spell": 202761, "VerifiedBuild": 0}]
        index = spell_tables.SpellTableIndex(
            {spec.name: (STOCK + SPIKE + emitted if spec.name == TABLE else []) for spec in spell_tables.SPELL_TABLES},
            emitted={TABLE: emitted}, base={TABLE: STOCK},
        )
        dsl = {spec.registry_key: [] for spec in spell_tables.SPELL_TABLES}
        dsl["creature_template_spells"] = [{"CreatureID": 300271, "Index": 0, "Spell": 5, "VerifiedBuild": 0}]
        blocks, report = spell_tables.render_prune_blocks(index, dsl)
        (block,) = blocks
        self.assertIn("IN ((300270, 0));", block)
        self.assertNotIn("300298", block)
        self.assertNotIn("300299", block)


class UnknownSpellLintTest(unittest.TestCase):
    ROW = {"CreatureID": 300270, "Index": 0, "Spell": 202761, "VerifiedBuild": 0}

    def test_a_spell_in_neither_set_warns(self):
        warnings = lint.check_creature_spell_rows([self.ROW], {5, 32982})
        self.assertEqual(len(warnings), 1)
        self.assertIn("creature_spell(300270, 0, 202761)", warnings[0])

    def test_a_built_spell_is_silent(self):
        self.assertEqual(lint.check_creature_spell_rows([self.ROW], {202761}), [])

    def test_a_stock_spell_is_silent(self):
        self.assertEqual(lint.check_creature_spell_rows([{**self.ROW, "Spell": 32982}], {32982, 5}), [])


if __name__ == "__main__":
    unittest.main()
