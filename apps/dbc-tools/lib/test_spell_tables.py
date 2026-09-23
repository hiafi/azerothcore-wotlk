"""
Unit tests for `lib/spell_tables.py` and the three registry helpers it
emits for (`scripted_by`/`bonus_coefficients`/`procs_on` in
`lib/dsl/registry.py`). Same shape as `test_trainer_state.py`: temp
directories stand in for the base dump + migrations so the "already live,
don't re-emit" diff is exercised against real parsed SQL, not mocks.

Run directly:

    python3 apps/dbc-tools/lib/test_spell_tables.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import spell_tables, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402

CLASS_FILE = '''
from lib.dsl.registry import bonus_coefficients, procs_on, scripted_by, spell

meteor = spell(id=200095, name="Meteor", school=4, cooldown_ms=45000)
scripted_by(meteor, "spell_mage_meteor")
scripted_by(12654, "spell_mage_ignite_dot", "spell_mage_ignite_display")
bonus_coefficients(meteor, direct=0.3, dot=0.15)
procs_on(200098, proc_flags=0x10000, family_name=3, family_mask=(0x2, 0, 0), chance=100, cooldown_ms=2500)
'''

BASE_SQL = {
    "spell_script_names": (
        "CREATE TABLE `spell_script_names` (\n"
        "  `spell_id` int NOT NULL,\n"
        "  `ScriptName` char(64) NOT NULL\n"
        ") ENGINE=InnoDB;\n"
    ),
    "spell_bonus_data": (
        "CREATE TABLE `spell_bonus_data` (\n"
        "  `entry` int unsigned NOT NULL DEFAULT '0',\n"
        "  `direct_bonus` float NOT NULL DEFAULT '0',\n"
        "  `dot_bonus` float NOT NULL DEFAULT '0',\n"
        "  `ap_bonus` float NOT NULL DEFAULT '0',\n"
        "  `ap_dot_bonus` float NOT NULL DEFAULT '0',\n"
        "  `comments` varchar(255) DEFAULT NULL,\n"
        "  PRIMARY KEY (`entry`)\n"
        ") ENGINE=InnoDB;\n"
    ),
    "spell_proc": (
        "CREATE TABLE `spell_proc` (\n"
        + "".join(f"  `{c}` int NOT NULL DEFAULT '0',\n" for c in spell_tables.SPELL_PROC_COLUMNS)
        + "  PRIMARY KEY (`SpellId`)\n"
        ") ENGINE=InnoDB;\n"
    ),
}


def _load_class(source: str) -> dict:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "mage.py"
        path.write_text(source)
        reg = registry.load_class_file(path)
    return {k: getattr(reg, k) for k in registry.MERGE_KEYS}


class RegistryHelpersTest(unittest.TestCase):
    def setUp(self):
        self.dsl = _load_class(CLASS_FILE)

    def test_scripted_by_one_row_per_name_with_composite_id(self):
        rows = self.dsl["spell_script_names"]
        self.assertEqual(
            [(r["spell_id"], r["ScriptName"]) for r in rows],
            [(200095, "spell_mage_meteor"), (12654, "spell_mage_ignite_dot"), (12654, "spell_mage_ignite_display")],
        )
        self.assertEqual(rows[0]["id"], "200095:spell_mage_meteor")

    def test_bonus_coefficients_defaults_comment_to_spell_name(self):
        (row,) = self.dsl["spell_bonus_data"]
        self.assertEqual(row["entry"], 200095)
        self.assertEqual((row["direct_bonus"], row["dot_bonus"], row["ap_bonus"]), (0.3, 0.15, 0.0))
        self.assertEqual(row["comments"], "Meteor")

    def test_procs_on_splits_family_mask_into_three_columns(self):
        (row,) = self.dsl["spell_procs"]
        self.assertEqual(row["SpellId"], 200098)
        self.assertEqual((row["SpellFamilyMask0"], row["SpellFamilyMask1"], row["SpellFamilyMask2"]), (2, 0, 0))
        self.assertEqual((row["Chance"], row["Cooldown"], row["ProcFlags"]), (100.0, 2500, 0x10000))

    def test_helpers_outside_load_raise(self):
        with self.assertRaises(RuntimeError):
            registry.scripted_by(1, "x")
        with self.assertRaises(RuntimeError):
            registry.bonus_coefficients(1, direct=1.0)
        with self.assertRaises(RuntimeError):
            registry.procs_on(1, proc_flags=1)

    def test_scripted_by_rejects_empty_or_overlong_names(self):
        with self.assertRaises(ValueError):
            _load_class('from lib.dsl.registry import scripted_by\nscripted_by(1)\n')
        with self.assertRaises(ValueError):
            _load_class(f'from lib.dsl.registry import scripted_by\nscripted_by(1, "{"x" * 65}")\n')

    def test_duplicate_binding_across_files_raises(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.py", "b.py"):
                (Path(d) / name).write_text('from lib.dsl.registry import scripted_by\nscripted_by(5, "s")\n')
            with self.assertRaises(registry.DuplicateIdError):
                registry.load_classes_dir(Path(d))


class SpellTableIndexTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        base = Path(self._tmp.name) / "base"
        promoted = Path(self._tmp.name) / "promoted"
        pending = Path(self._tmp.name) / "pending"
        for d in (base, promoted, pending):
            d.mkdir()
        self._promoted = promoted
        for table, sql in BASE_SQL.items():
            (base / f"{table}.sql").write_text(sql)
        self._orig = (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR)
        trainer_state.BASE_SQL_DIR = base
        trainer_state.PROMOTED_SQL_DIR = promoted
        trainer_state.PENDING_SQL_DIR = pending
        self.dsl = _load_class(CLASS_FILE)

    def tearDown(self):
        (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR) = self._orig
        self._tmp.cleanup()

    def _blocks(self) -> list[str]:
        return spell_tables.render_blocks(spell_tables.load_spell_table_index(), self.dsl)

    def test_nothing_live_emits_all_three_tables(self):
        blocks = self._blocks()
        self.assertEqual(len(blocks), 3)
        self.assertIn("DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN "
                      "((12654, 'spell_mage_ignite_display'), (12654, 'spell_mage_ignite_dot'), "
                      "(200095, 'spell_mage_meteor'));", blocks[0])
        self.assertIn("INSERT INTO `spell_bonus_data`", blocks[1])
        self.assertIn("(200095, 0.3, 0.15, 0.0, 0.0, 'Meteor')", blocks[1])
        self.assertIn("DELETE FROM `spell_proc` WHERE (`SpellId`) IN ((200098));", blocks[2])

    def test_identical_live_rows_are_not_re_emitted(self):
        (self._promoted / "live.sql").write_text(
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES "
            "(200095, 'spell_mage_meteor'), (12654, 'spell_mage_ignite_dot'), (12654, 'spell_mage_ignite_display');\n"
            "INSERT INTO `spell_bonus_data` (`entry`, `direct_bonus`, `dot_bonus`, `ap_bonus`, `ap_dot_bonus`, `comments`) "
            "VALUES (200095, 0.3, 0.15, 0, 0, 'Meteor');\n"
        )
        blocks = self._blocks()
        self.assertEqual(len(blocks), 1)  # only spell_proc still has anything to say
        self.assertIn("spell_proc", blocks[0])

    def test_changed_coefficient_is_re_emitted(self):
        (self._promoted / "live.sql").write_text(
            "INSERT INTO `spell_bonus_data` (`entry`, `direct_bonus`, `dot_bonus`, `ap_bonus`, `ap_dot_bonus`, `comments`) "
            "VALUES (200095, 0.25, 0.15, 0, 0, 'Meteor');\n"
        )
        blocks = self._blocks()
        self.assertTrue(any("spell_bonus_data" in b and "0.3, 0.15" in b for b in blocks))

    def test_partial_column_live_row_compares_on_declared_columns(self):
        # A hand-written migration that omitted the ap_* columns (defaults 0)
        # still counts as identical to a declaration with ap=0.
        (self._promoted / "live.sql").write_text(
            "INSERT INTO `spell_bonus_data` (`entry`, `direct_bonus`, `dot_bonus`, `comments`) "
            "VALUES (200095, 0.3, 0.15, 'Meteor');\n"
        )
        blocks = self._blocks()
        self.assertFalse(any("spell_bonus_data" in b for b in blocks))


GENERATED_HEADER = spell_tables.GENERATED_MARKER + " — DO NOT hand-edit.\n"


class PruneTest(unittest.TestCase):
    """The prune pass: rows an earlier generated run emitted that the source
    no longer declares. See .agents/plans/dbc-tools-prune-pass/."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self._base, self._promoted, self._pending = root / "base", root / "promoted", root / "pending"
        for d in (self._base, self._promoted, self._pending):
            d.mkdir()
        for table, sql in BASE_SQL.items():
            (self._base / f"{table}.sql").write_text(sql)
        self._orig = (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR)
        trainer_state.BASE_SQL_DIR = self._base
        trainer_state.PROMOTED_SQL_DIR = self._promoted
        trainer_state.PENDING_SQL_DIR = self._pending
        self.dsl = _load_class(CLASS_FILE)

    def tearDown(self):
        (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR) = self._orig
        self._tmp.cleanup()

    def _write(self, name: str, body: str, generated: bool = True):
        (self._promoted / name).write_text((GENERATED_HEADER if generated else "") + body)

    def _prune(self):
        return spell_tables.render_prune_blocks(spell_tables.load_spell_table_index(), self.dsl)

    # The real case this was built for: a renamed script leaves the old
    # (spell_id, ScriptName) pair behind, plus a retired procs_on row.
    def test_orphaned_rows_are_pruned(self):
        self._write("gen.sql",
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES "
            "(200095, 'spell_mage_meteor'), (200095, 'spell_mage_meteor_old');\n")
        blocks, report = self._prune()
        self.assertEqual(len(blocks), 1)
        self.assertIn("DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN "
                      "((200095, 'spell_mage_meteor_old'));", blocks[0])
        # still-declared row untouched
        self.assertNotIn("'spell_mage_meteor')", blocks[0].split("IN (")[1])
        self.assertTrue(any("removing spell_script_names" in line for line in report))

    def test_declared_rows_are_never_pruned(self):
        self._write("gen.sql",
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES "
            "(200095, 'spell_mage_meteor'), (12654, 'spell_mage_ignite_dot'), "
            "(12654, 'spell_mage_ignite_display');\n")
        blocks, report = self._prune()
        self.assertEqual(blocks, [])
        self.assertEqual([l for l in report if "removing" in l], [])

    # Provenance: an identical orphan in a hand-written migration is not ours.
    def test_hand_written_migration_rows_are_not_pruned(self):
        self._write("hand.sql",
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES "
            "(200095, 'spell_mage_meteor_old');\n", generated=False)
        blocks, report = self._prune()
        self.assertEqual(blocks, [])
        self.assertEqual([l for l in report if "removing" in l], [])

    # Safety rule 1: a past run overrode a stock row; deleting leaves a hole.
    def test_base_dump_overlap_is_reported_not_deleted(self):
        (self._base / "spell_proc.sql").write_text(
            BASE_SQL["spell_proc"]
            + "INSERT INTO `spell_proc` (`SpellId`) VALUES (12345);\n")
        self._write("gen.sql", "INSERT INTO `spell_proc` (`SpellId`) VALUES (12345);\n")
        blocks, report = self._prune()
        self.assertEqual(blocks, [])
        self.assertTrue(any("NOT removing spell_proc" in line and "12345" in line for line in report))

    # Safety rule 2: zero declarations + a history means the source didn't load.
    def test_circuit_breaker_refuses_to_empty_a_table(self):
        self._write("gen.sql",
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES (200095, 'a'), (7, 'b');\n")
        blocks, report = spell_tables.render_prune_blocks(
            spell_tables.load_spell_table_index(), {})
        self.assertEqual(blocks, [])
        self.assertTrue(any("SKIPPED spell_script_names" in line for line in report))

    def test_delete_block_renders_ints_not_floats(self):
        self._write("gen.sql", "INSERT INTO `spell_proc` (`SpellId`) VALUES (200098), (99999);\n")
        blocks, _ = self._prune()
        self.assertIn("DELETE FROM `spell_proc` WHERE (`SpellId`) IN ((99999));", blocks[0])
        self.assertNotIn(".0", blocks[0])

    # spell_proc's "this spell and every rank in its chain" negative-id rows
    # are the real-world instance of safety rule 1 (three such rows are
    # currently overridden in this repo: -14531, -45234, -47516).
    def test_negative_spell_id_overriding_stock_is_not_pruned(self):
        (self._base / "spell_proc.sql").write_text(
            BASE_SQL["spell_proc"]
            + "INSERT INTO `spell_proc` (`SpellId`) VALUES (-47516);\n")
        self._write("gen.sql", "INSERT INTO `spell_proc` (`SpellId`) VALUES (-47516);\n")
        blocks, report = self._prune()
        self.assertEqual(blocks, [])
        self.assertTrue(any("NOT removing spell_proc" in l and "-47516" in l for l in report))

    def test_key_sort_tolerates_none_and_mixed_types(self):
        from lib import sql_out
        self.assertEqual(
            sql_out.stable_key_sort([(2.0, "b"), (None, "a"), (1.0, "z"), (2.0, "a")]),
            [(None, "a"), (1.0, "z"), (2.0, "a"), (2.0, "b")])

    # The regression this replay exists for: once a prune has emitted its
    # DELETE into a generated file, a later run must see the row as gone
    # rather than re-reporting it forever.
    def test_already_pruned_row_is_not_reported_again(self):
        self._write("01_gen.sql",
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES "
            "(200095, 'spell_mage_meteor'), (200095, 'spell_mage_meteor_old');\n")
        blocks, report = self._prune()
        self.assertEqual(len(blocks), 1)  # first run: prunes the orphan

        # Simulate that prune having been written out as the next generated file.
        self._write("02_gen.sql",
            "DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN "
            "((200095, 'spell_mage_meteor_old'));\n")
        blocks, report = self._prune()
        self.assertEqual(blocks, [])
        self.assertEqual([l for l in report if "removing" in l], [])

    # A DELETE+INSERT block (render_generic_table_block) must not read as a
    # net removal - the INSERT immediately puts the row back.
    def test_delete_then_insert_in_same_file_keeps_the_row(self):
        self._write("gen.sql",
            "DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN "
            "((200095, 'spell_mage_meteor_old'));\n"
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES "
            "(200095, 'spell_mage_meteor_old');\n")
        blocks, _ = self._prune()
        self.assertEqual(len(blocks), 1)
        self.assertIn("spell_mage_meteor_old", blocks[0])

    # Single-column DELETE against a two-column-keyed table removes every
    # matching row (the prefix case in _matching_keys).
    def test_single_column_delete_removes_all_matching_keys(self):
        self._write("gen.sql",
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES "
            "(4242, 'a'), (4242, 'b');\n"
            "DELETE FROM `spell_script_names` WHERE `spell_id` IN (4242);\n")
        blocks, report = self._prune()
        self.assertEqual(blocks, [])
        self.assertEqual([l for l in report if "removing" in l], [])

    def test_spell_proc_delete_replay(self):
        self._write("gen.sql",
            "INSERT INTO `spell_proc` (`SpellId`) VALUES (777);\n"
            "DELETE FROM `spell_proc` WHERE (`SpellId`) IN ((777));\n")
        blocks, report = self._prune()
        self.assertEqual(blocks, [])

    # Safety: a shape the replay can't read must shrink the prune, not guess.
    def test_unparsed_delete_shape_disables_prune_for_that_table(self):
        self._write("gen.sql",
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES (200095, 'orphan');\n"
            "DELETE FROM `spell_script_names` WHERE `ScriptName` LIKE 'spell_%';\n")
        blocks, report = self._prune()
        self.assertEqual(blocks, [])


if __name__ == "__main__":
    unittest.main()
