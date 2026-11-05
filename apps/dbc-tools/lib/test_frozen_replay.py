"""
Unit tests for `lib/frozen_replay.py`: the frozen mod-progression phase 0 replay input (progression-slim PS1).

Run directly:

    apps/dbc-tools/.venv/bin/python3 -m unittest lib.test_frozen_replay   (from apps/dbc-tools)
"""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import frozen_replay, sqlcorpus, state, trainer_state  # noqa: E402
from lib.dbcfmt import DbcTable  # noqa: E402

PHASE_00 = frozen_replay.FROZEN_ROOT / "2026_09_02_mod_progression_phase_00"
REAL_PROMOTED = trainer_state.PROMOTED_SQL_DIR


def _manifest(directory: Path) -> list[tuple[str, str]]:
    lines = (directory / "MANIFEST").read_text(encoding="utf-8").splitlines()
    return [tuple(line.split()) for line in lines if line and not line.startswith("#")]


class RealPhase00Test(unittest.TestCase):
    """The checked-in copy: what ran on the live DB, and a slot that fits the real promoted history."""

    def test_files_are_the_42_that_ran_byte_for_byte(self):
        manifest = _manifest(PHASE_00)
        self.assertEqual(len(manifest), 42)
        self.assertEqual(sorted(p.name for p in PHASE_00.glob("*.sql")), sorted(name for _, name in manifest))
        for sha1, name in manifest:
            self.assertEqual(hashlib.sha1((PHASE_00 / name).read_bytes()).hexdigest().upper(), sha1, name)

    def test_manifest_lists_the_apply_order(self):
        (slot,) = frozen_replay.slots()
        self.assertEqual([p.name for p in slot.files], [name for _, name in _manifest(PHASE_00)])
        # Byte order, as DBUpdater applied them: creature.sql before creature_addon.sql.
        names = [p.name for p in slot.files]
        self.assertLess(names.index("phase_00-creature.sql"), names.index("phase_00-creature_addon.sql"))

    def test_slot_anchors_are_adjacent_promoted_files(self):
        (slot,) = frozen_replay.slots()
        self.assertEqual((slot.after, slot.before), ("2026_08_21_01.sql", "2026_08_22_00.sql"))
        promoted = sorted(REAL_PROMOTED.glob("*.sql"))
        names = [p.name for p in promoted]
        self.assertEqual(names.index(slot.before), names.index(slot.after) + 1)
        spliced = frozen_replay.splice(promoted)
        at = [p.name for p in spliced].index(slot.after) + 1
        self.assertEqual(spliced[at:at + len(slot.files)], list(slot.files))
        self.assertEqual(spliced[at + len(slot.files)].name, slot.before)

    def test_the_replay_needs_no_mod_progression_checkout(self):
        files = trainer_state._migration_files_mentioning("creature_default_trainer")
        self.assertIn(PHASE_00 / "phase_00-creature_default_trainer.sql", files)
        self.assertFalse(any("mod-progression" in p.parts for p in files))


class SpliceTest(unittest.TestCase):
    """`splice` against a temporary frozen root and promoted list."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.frozen = root / "frozen"
        self.slot = self.frozen / "2026_09_02_x"
        self.slot.mkdir(parents=True)
        (self.slot / "SLOT").write_text("# comment\nafter = 2026_08_21_01.sql\nbefore = 2026_08_22_00.sql\n")
        for name in ("p-creature_addon.sql", "p-creature.sql"):
            (self.slot / name).write_text("-- frozen\n")
        self.promoted = root / "promoted"
        self.promoted.mkdir()
        self._orig = frozen_replay.FROZEN_ROOT
        frozen_replay.FROZEN_ROOT = self.frozen

    def tearDown(self):
        frozen_replay.FROZEN_ROOT = self._orig
        self._tmp.cleanup()

    def _promoted(self, *names: str) -> list[Path]:
        return [self.promoted / n for n in names]

    def _names(self, paths: list[Path]) -> list[str]:
        return [p.name for p in paths]

    def test_files_go_right_after_the_after_anchor_in_byte_order(self):
        spliced = frozen_replay.splice(self._promoted("2026_08_20_00.sql", "2026_08_21_01.sql", "2026_08_22_00.sql"))
        self.assertEqual(
            self._names(spliced),
            ["2026_08_20_00.sql", "2026_08_21_01.sql", "p-creature.sql", "p-creature_addon.sql", "2026_08_22_00.sql"],
        )
        self.assertTrue(all(frozen_replay.is_frozen(p) for p in spliced[2:4]))
        self.assertFalse(frozen_replay.is_frozen(spliced[0]))

    def test_before_anchor_alone_places_the_files_before_it(self):
        spliced = frozen_replay.splice(self._promoted("2026_08_22_00.sql", "2026_09_01_00.sql"))
        self.assertEqual(
            self._names(spliced), ["p-creature.sql", "p-creature_addon.sql", "2026_08_22_00.sql", "2026_09_01_00.sql"],
        )

    def test_a_list_without_either_anchor_is_unchanged(self):
        promoted = self._promoted("a.sql", "b.sql")
        self.assertEqual(frozen_replay.splice(promoted), promoted)
        self.assertEqual(frozen_replay.splice([]), [])

    def test_a_promoted_file_inside_the_slot_is_an_error(self):
        with self.assertRaises(frozen_replay.FrozenSlotError):
            frozen_replay.splice(self._promoted("2026_08_21_01.sql", "2026_08_21_02.sql", "2026_08_22_00.sql"))

    def test_a_malformed_slot_is_an_error(self):
        (self.slot / "SLOT").write_text("after = 2026_08_21_01.sql\n")
        with self.assertRaises(frozen_replay.FrozenSlotError):
            frozen_replay.slots()
        (self.slot / "SLOT").write_text("after = 2026_08_22_00.sql\nbefore = 2026_08_21_01.sql\n")
        with self.assertRaises(frozen_replay.FrozenSlotError):
            frozen_replay.slots()

    def test_a_directory_without_slot_is_ignored(self):
        (self.frozen / "notes").mkdir()
        self.assertEqual([s.directory.name for s in frozen_replay.slots()], ["2026_09_02_x"])


class StateSpliceTest(unittest.TestCase):
    """`state.load_existing_rows` (the DBC tables, e.g. phase 0's map_dbc / mapdifficulty_dbc / spell_dbc) replays
    the frozen files at their slot too."""

    TABLE = DbcTable(name="Widget", dbc_filename="Widget.dbc", sql_table="widget_dbc", fmt="nsi",
                     columns=("ID", "Name", "Value"))

    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        for d in ("base", "promoted", "dbc", "frozen/slot"):
            (root / d).mkdir(parents=True)
        (root / "base" / "widget_dbc.sql").write_text(
            "CREATE TABLE `widget_dbc` (\n  `ID` int NOT NULL,\n  `Name` varchar(10) DEFAULT NULL,\n"
            "  `Value` int NOT NULL DEFAULT '0',\n  PRIMARY KEY (`ID`)\n) ENGINE=InnoDB;\n"
            "INSERT INTO `widget_dbc` VALUES (1, 'one', 10), (2, 'two', 20);\n"
        )
        (root / "seed.sql").write_text("-- nothing\n")
        (root / "promoted" / "2026_08_21_01.sql").write_text("UPDATE `widget_dbc` SET `Value` = 11 WHERE `ID` = 1;\n")
        (root / "promoted" / "2026_08_22_00.sql").write_text("UPDATE `widget_dbc` SET `Value` = 22 WHERE `ID` = 2;\n")
        (root / "frozen" / "slot" / "SLOT").write_text("after = 2026_08_21_01.sql\nbefore = 2026_08_22_00.sql\n")
        (root / "frozen" / "slot" / "phase_00-widget_dbc.sql").write_text(
            "UPDATE `widget_dbc` SET `Value` = 99 WHERE `ID` IN (1, 2);\n"
        )
        self._orig = [(state, n, getattr(state, n)) for n in (
            "BASE_SQL_DIR", "PROMOTED_SQL_DIR", "BASE_DBC_DIR", "LIVE_SECONDARY_ROWS_SQL")]
        self._orig.append((frozen_replay, "FROZEN_ROOT", frozen_replay.FROZEN_ROOT))
        self._orig.append((trainer_state, "BASE_SQL_DIR", trainer_state.BASE_SQL_DIR))
        trainer_state.BASE_SQL_DIR = root / "base"  # frozen_replay.normalise reads the CREATE TABLE there
        state.BASE_SQL_DIR, state.PROMOTED_SQL_DIR = root / "base", root / "promoted"
        state.BASE_DBC_DIR, state.LIVE_SECONDARY_ROWS_SQL = root / "dbc", root / "seed.sql"
        frozen_replay.FROZEN_ROOT = root / "frozen"
        state._promoted_sql_cache = None

    def tearDown(self):
        for module, name, value in self._orig:
            setattr(module, name, value)
        state._promoted_sql_cache = None
        self._tmp.cleanup()

    def test_a_frozen_file_is_read_normalised(self):
        frozen = frozen_replay.FROZEN_ROOT / "slot" / "phase_00-widget_dbc.sql"
        frozen.write_text(
            "SET @a := 1, @b := 2;\nUPDATE `widget_dbc` SET `value` = 99 WHERE `id` IN (\n    1 -- one\n);\n"
        )
        self.assertEqual(
            sqlcorpus.read_text(frozen),
            "SET @a := 1; SET @b := 2;\nUPDATE `widget_dbc` SET `Value` = 99 WHERE `ID` IN (\n    1 \n);\n",
        )
        promoted = state.PROMOTED_SQL_DIR / "2026_08_21_01.sql"
        self.assertEqual(sqlcorpus.read_text(promoted), promoted.read_text())  # only frozen files are touched

    def test_frozen_update_lands_between_its_neighbours(self):
        rows = state.load_existing_rows(self.TABLE)
        self.assertEqual((rows[1]["Value"], rows[2]["Value"]), (99, 22))


if __name__ == "__main__":
    unittest.main()
