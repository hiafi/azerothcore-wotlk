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


if __name__ == "__main__":
    unittest.main()
