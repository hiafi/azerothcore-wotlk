"""
Unit tests for `lib/trainer_state.py` - Phase 3 of `.agents/plans/
spell-source-dsl/spell-source-dsl.PLAN.md`. Uses temp directories (not the
real repo's ~800 migration files) so this is fast and deterministic; the
real-data path was separately sanity-checked by hand against this repo's
actual data during development (TrainerId 13 - the Death Knight bug from
docs/bugs-and-fixes.md - correctly comes back clean, a made-up TrainerId
correctly comes back dead).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_trainer_state.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import trainer_state  # noqa: E402

CREATE_TABLE_SQL = {
    "creature_default_trainer": (
        "CREATE TABLE `creature_default_trainer` (\n"
        "  `CreatureId` int unsigned NOT NULL,\n"
        "  `TrainerId` int unsigned NOT NULL DEFAULT '0',\n"
        "  PRIMARY KEY (`CreatureId`)\n"
        ") ENGINE=InnoDB;\n"
    ),
    "trainer_spell": (
        "CREATE TABLE `trainer_spell` (\n"
        "  `TrainerId` int unsigned NOT NULL,\n"
        "  `SpellId` int unsigned NOT NULL,\n"
        "  `MoneyCost` int unsigned NOT NULL DEFAULT '0',\n"
        "  `ReqSkillLine` int unsigned NOT NULL DEFAULT '0',\n"
        "  `ReqSkillRank` int unsigned NOT NULL DEFAULT '0',\n"
        "  `ReqAbility1` int unsigned NOT NULL DEFAULT '0',\n"
        "  `ReqAbility2` int unsigned NOT NULL DEFAULT '0',\n"
        "  `ReqAbility3` int unsigned NOT NULL DEFAULT '0',\n"
        "  `ReqLevel` tinyint unsigned NOT NULL DEFAULT '0',\n"
        "  `VerifiedBuild` int DEFAULT '0',\n"
        "  PRIMARY KEY (`TrainerId`,`SpellId`)\n"
        ") ENGINE=InnoDB;\n"
    ),
    "creature_template": (
        "CREATE TABLE `creature_template` (\n"
        "  `entry` int unsigned NOT NULL DEFAULT '0',\n"
        "  `npcflag` int unsigned NOT NULL DEFAULT '0',\n"
        "  PRIMARY KEY (`entry`)\n"
        ") ENGINE=InnoDB;\n"
    ),
    "creature": (
        "CREATE TABLE `creature` (\n"
        "  `guid` int unsigned NOT NULL AUTO_INCREMENT,\n"
        "  `id1` int unsigned NOT NULL DEFAULT '0',\n"
        "  `id2` int unsigned NOT NULL DEFAULT '0',\n"
        "  `id3` int unsigned NOT NULL DEFAULT '0',\n"
        "  PRIMARY KEY (`guid`)\n"
        ") ENGINE=InnoDB;\n"
    ),
}


class TrainerStateTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        base = Path(self._tmp.name) / "base"
        promoted = Path(self._tmp.name) / "promoted"
        pending = Path(self._tmp.name) / "pending"
        for d in (base, promoted, pending):
            d.mkdir()
        self._base, self._promoted, self._pending = base, promoted, pending
        for table, sql in CREATE_TABLE_SQL.items():
            (base / f"{table}.sql").write_text(sql)
        modules = Path(self._tmp.name) / "modules"
        modules.mkdir()
        self._modules = modules
        self._orig = (
            trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR,
            trainer_state.MODULES_DIR, trainer_state.PROGRESSION_CONF, trainer_state.PROGRESSION_CONF_DIST,
        )
        trainer_state.BASE_SQL_DIR = base
        trainer_state.PROMOTED_SQL_DIR = promoted
        trainer_state.PENDING_SQL_DIR = pending
        trainer_state.MODULES_DIR = modules
        trainer_state.PROGRESSION_CONF = modules / "mod_progression.conf"  # absent unless a test writes it
        trainer_state.PROGRESSION_CONF_DIST = modules / "mod_progression.conf.dist"

    def tearDown(self):
        (
            trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR,
            trainer_state.MODULES_DIR, trainer_state.PROGRESSION_CONF, trainer_state.PROGRESSION_CONF_DIST,
        ) = self._orig
        self._tmp.cleanup()

    def _write(self, dir_path: Path, name: str, table: str, columns: tuple, rows: list[tuple]) -> None:
        cols_sql = ", ".join(f"`{c}`" for c in columns)
        values = ", ".join(
            "(" + ", ".join(str(v) for v in row) + ")" for row in rows
        )
        (dir_path / name).write_text(f"INSERT INTO `{table}` ({cols_sql}) VALUES {values};\n")

    def _wire_up_trainer(self, trainer_id: int, creature_id: int, npcflag: int, spawned: bool) -> None:
        self._write(self._promoted, f"cdt_{creature_id}.sql", "creature_default_trainer",
                    ("CreatureId", "TrainerId"), [(creature_id, trainer_id)])
        self._write(self._promoted, f"ct_{creature_id}.sql", "creature_template",
                    ("entry", "npcflag"), [(creature_id, npcflag)])
        if spawned:
            self._write(self._promoted, f"c_{creature_id}.sql", "creature",
                        ("id1", "id2", "id3"), [(creature_id, 0, 0)])

    def test_fully_wired_trainer_has_no_problems(self):
        self._wire_up_trainer(13, 33251, trainer_state.UNIT_NPC_FLAG_TRAINER, spawned=True)
        idx = trainer_state.load_trainer_index()
        self.assertEqual(idx.trainer_problems(13), [])

    def test_unknown_trainer_id_is_a_problem(self):
        idx = trainer_state.load_trainer_index()
        problems = idx.trainer_problems(999)
        self.assertEqual(len(problems), 1)
        self.assertIn("no creature_default_trainer row", problems[0])

    def test_trainer_id_wired_to_non_trainer_flagged_creature_is_a_problem(self):
        self._wire_up_trainer(13, 33251, npcflag=0, spawned=True)  # no TRAINER bit
        idx = trainer_state.load_trainer_index()
        problems = idx.trainer_problems(13)
        self.assertEqual(len(problems), 1)
        self.assertIn("npcflag", problems[0])

    def test_trainer_id_wired_to_unspawned_creature_is_a_problem(self):
        self._wire_up_trainer(13, 33251, trainer_state.UNIT_NPC_FLAG_TRAINER, spawned=False)
        idx = trainer_state.load_trainer_index()
        problems = idx.trainer_problems(13)
        self.assertEqual(len(problems), 1)
        self.assertIn("no spawn", problems[0])

    def test_one_good_creature_id_among_several_is_enough(self):
        # TrainerId 13 has two creature_default_trainer rows: one dead
        # (unspawned), one fully wired - the whole TrainerId should read as
        # fine, since some real NPC in the world does serve it.
        self._wire_up_trainer(13, 100, trainer_state.UNIT_NPC_FLAG_TRAINER, spawned=False)
        self._wire_up_trainer(13, 200, trainer_state.UNIT_NPC_FLAG_TRAINER, spawned=True)
        idx = trainer_state.load_trainer_index()
        self.assertEqual(idx.trainer_problems(13), [])

    def test_pending_migration_is_included(self):
        # A fix that only exists in pending_db_world/ (not yet promoted)
        # must still count - see this module's docstring for why, unlike
        # lib/state.py's DBC-table reconstruction.
        self._write(self._pending, "fix.sql", "creature_default_trainer",
                    ("CreatureId", "TrainerId"), [(500, 77)])
        self._write(self._promoted, "ct_500.sql", "creature_template",
                    ("entry", "npcflag"), [(500, trainer_state.UNIT_NPC_FLAG_TRAINER)])
        self._write(self._promoted, "c_500.sql", "creature", ("id1", "id2", "id3"), [(500, 0, 0)])
        idx = trainer_state.load_trainer_index()
        self.assertEqual(idx.trainer_problems(77), [])

    def _progression_rewire(self, phase: int, creature_id: int, offset: int) -> None:
        # The exact shape of mod-progression's phase_00-creature_default_trainer.sql.
        sql_dir = self._modules / "mod-progression" / "src" / f"phase_{phase:02}" / "sql"
        sql_dir.mkdir(parents=True)
        (sql_dir / f"phase_{phase:02}-creature_default_trainer.sql").write_text(
            "SET @TrainerId := 200;\n"
            f"UPDATE `creature_default_trainer` SET `TrainerId` = @TrainerId+{offset} WHERE `CreatureId` IN (\n"
            f"    {creature_id}, -- Some Trainer <Mage Trainer>\n"
            "    999999 -- not a real row, must be ignored\n"
            ");\n"
        )

    def test_progression_phase_update_rewires_trainer_id(self):
        # Stock data says CreatureId 328 -> TrainerId 16; phase_00 moves it to 212 (200+12). The
        # old id must read as dead and the new one as live - this is the exact false-negative
        # that blocked trained_by(..., 212) for Meteor.
        self._wire_up_trainer(16, 328, trainer_state.UNIT_NPC_FLAG_TRAINER, spawned=True)
        self._progression_rewire(0, 328, 12)
        idx = trainer_state.load_trainer_index()
        self.assertEqual(idx.trainer_problems(212), [])
        self.assertIn("no creature_default_trainer row", idx.trainer_problems(16)[0])

    def test_progression_phase_above_configured_phase_is_not_applied(self):
        self._wire_up_trainer(16, 328, trainer_state.UNIT_NPC_FLAG_TRAINER, spawned=True)
        self._progression_rewire(0, 328, 12)   # applied (phase 0 <= 2)
        self._progression_rewire(13, 328, -199)  # phase_13 reverts to stock - NOT applied at phase 2
        trainer_state.PROGRESSION_CONF.write_text("# comment\nProgression.Phase = 2\n")
        idx = trainer_state.load_trainer_index()
        self.assertEqual(trainer_state.progression_phase(), 2)
        self.assertEqual(idx.trainer_problems(212), [])

    def test_module_db_world_sql_is_scanned(self):
        # A plain module's data/sql/db-world/ INSERT counts like a core migration would.
        sql_dir = self._modules / "mod-example" / "data" / "sql" / "db-world"
        sql_dir.mkdir(parents=True)
        (sql_dir / "trainer.sql").write_text(
            "INSERT INTO `creature_default_trainer` (`CreatureId`, `TrainerId`) VALUES (700, 88);\n"
        )
        self._write(self._promoted, "ct_700.sql", "creature_template",
                    ("entry", "npcflag"), [(700, trainer_state.UNIT_NPC_FLAG_TRAINER)])
        self._write(self._promoted, "c_700.sql", "creature", ("id1", "id2", "id3"), [(700, 0, 0)])
        idx = trainer_state.load_trainer_index()
        self.assertEqual(idx.trainer_problems(88), [])

    def test_existing_trainer_spells_indexed_by_composite_key(self):
        self._write(self._promoted, "ts.sql", "trainer_spell",
                    ("TrainerId", "SpellId", "ReqLevel"), [(13, 48266, 55)])
        idx = trainer_state.load_trainer_index()
        self.assertEqual(idx.existing_trainer_spells[(13, 48266)]["ReqLevel"], 55)

    def test_unparseable_migration_file_is_skipped_not_fatal(self):
        # @GUID-style expressions (a real, common pattern in this repo's
        # creature spawn migrations) can't be parsed as a plain int literal -
        # must warn and skip that one file, not blow up the whole load.
        self._wire_up_trainer(13, 33251, trainer_state.UNIT_NPC_FLAG_TRAINER, spawned=True)
        (self._promoted / "weird.sql").write_text(
            "INSERT INTO `creature` (`id1`, `id2`, `id3`) VALUES (@GUID+0, 0, 0);\n"
        )
        idx = trainer_state.load_trainer_index()  # must not raise
        self.assertEqual(idx.trainer_problems(13), [])


if __name__ == "__main__":
    unittest.main()
