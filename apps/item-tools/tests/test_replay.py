"""
item-tools' SQL replay (`item_lib/replay.py`, dbc-tools' parser) and the readers built on it (`overlay`,
`budget_overlay`, `loot`), over a scratch repo layout.

    apps/dbc-tools/.venv/bin/python3 -m unittest discover -s apps/item-tools/tests
"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from item_lib import budget_overlay, loot, overlay, replay  # noqa: E402

ITEM_DUMP = """\
CREATE TABLE `item_template` (
  `entry` int unsigned NOT NULL DEFAULT '0',
  `name` varchar(255) NOT NULL DEFAULT '',
  `Quality` tinyint unsigned NOT NULL DEFAULT '0',
  `stat_value1` int NOT NULL DEFAULT '0',
  `dmg_min1` float NOT NULL DEFAULT '0',
  `Flags` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`entry`)
) ENGINE=InnoDB;
INSERT INTO `item_template` VALUES (1,'One',2,10,100,0),(2,'Two',3,20,180.457,1),(3,'Three',4,30,50,0);
"""

CREATURE_DUMP = """\
CREATE TABLE `creature` (
  `guid` int unsigned NOT NULL AUTO_INCREMENT,
  `id1` int unsigned NOT NULL DEFAULT '0',
  `id2` int unsigned NOT NULL DEFAULT '0',
  `map` smallint unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`guid`)
) ENGINE=InnoDB;
INSERT INTO `creature` VALUES (1,10,0,36),(2,11,12,36);
"""


class ScratchRepo(unittest.TestCase):
    """A repo layout in a temporary directory, with replay's directories (and dbc-tools' module dir) pointed at it."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.base = root / "data/sql/base/db_world"
        self.merged = root / "data/sql/updates/db_world"
        self.pending = root / "data/sql/updates/pending_db_world"
        self.modules = root / "modules"
        for d in (self.base, self.merged, self.pending, self.modules):
            d.mkdir(parents=True)
        patches = [
            mock.patch.object(replay, "BASE_DIR", self.base),
            mock.patch.object(replay, "MERGED_DIR", self.merged),
            mock.patch.object(replay, "PENDING_DIR", self.pending),
            mock.patch.object(replay.trainer_state, "MODULES_DIR", self.modules),
            mock.patch.object(overlay, "BASE_FILE", self.base / "item_template.sql"),
            mock.patch.object(replay, "CACHE_DIR", root / "var/item-tools-cache"),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self._tmp.cleanup)
        replay.sqlcorpus.SKIPS.clear()

    def write(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


class FileOrderTest(ScratchRepo):
    def test_subdirectories_by_bare_name_then_pending_then_modules(self):
        a = self.write(self.merged / "2026_01_01_00.sql", "UPDATE `item_template` SET `Quality` = 1;\n")
        b = self.write(self.merged / "topic" / "2026_01_01_00b.sql", "UPDATE `item_template` SET `Quality` = 1;\n")
        c = self.write(self.merged / "2026_01_02_00.sql", "UPDATE `item_template` SET `Quality` = 1;\n")
        d = self.write(self.pending / "topic" / "rev_1.sql", "UPDATE `item_template` SET `Quality` = 1;\n")
        e = self.write(self.pending / "rev_2.sql", "-- nothing about items\n")
        f = self.write(self.modules / "mod-x/data/sql/db-world/x.sql", "UPDATE `item_template` SET `Quality` = 1;\n")
        self.write(self.base / "item_template.sql", ITEM_DUMP)
        self.assertEqual(replay.sql_files(), [a, b, c, d, e, f])
        self.assertEqual(replay.contributing_files("item_template"), [self.base / "item_template.sql", a, b, c, d, f])
        self.assertEqual(
            replay.contributing_files("item_template", applied={"2026_01_02_00.sql", "x.sql"}),
            [self.base / "item_template.sql", c, f],
        )


class DbUpdaterOrderTest(ScratchRepo):
    def test_module_sql_and_pending_interleave_by_bare_name(self):
        # dbc-replay-fix review, design question 4: DBUpdater's second pass is one name order over pending, custom and
        # module SQL. The module file named 2016_... runs before the pending rev that later sets the same row.
        self.write(self.base / "item_template.sql", ITEM_DUMP)
        self.write(self.pending / "rev_1.sql", "UPDATE `item_template` SET `Quality` = 5 WHERE `entry` = 1;\n")
        self.write(self.modules / "mod-x/data/sql/db-world/2016_11_17_x.sql",
                   "UPDATE `item_template` SET `Quality` = 9, `Flags` = 1 WHERE `entry` = 1;\n")
        self.assertEqual([p.name for p in replay.sql_files()], ["2016_11_17_x.sql", "rev_1.sql"])
        row = overlay.resolve_current_rows()[1]
        self.assertEqual((row["Quality"], row["Flags"]), (5, 1))


class UpsertTest(ScratchRepo):
    def test_partial_upsert_keeps_the_other_columns(self):
        # Review S5: item-tools' old overlay merged an upsert into the existing row; the shared parser now does what
        # MySQL does (only the clause's columns change).
        self.write(self.base / "item_template.sql", ITEM_DUMP)
        self.write(self.merged / "2026_01_01_00.sql", (
            "INSERT INTO `item_template` (`entry`, `Quality`) VALUES (2, 6), (4, 1) "
            "ON DUPLICATE KEY UPDATE `Quality` = VALUES(`Quality`);\n"
        ))
        rows = overlay.resolve_current_rows()
        self.assertEqual((rows[2]["name"], rows[2]["Quality"], rows[2]["stat_value1"]), ("Two", 6, 20))
        self.assertEqual((rows[4]["name"], rows[4]["Quality"]), ("", 1))


class ItemTemplateTest(ScratchRepo):
    def setUp(self):
        super().setUp()
        self.write(self.base / "item_template.sql", ITEM_DUMP)

    def test_guards_are_honoured_like_mysql(self):
        self.write(self.merged / "2026_01_01_00.sql", (
            "UPDATE `item_template` SET `stat_value1` = 11 WHERE `entry` = 1 AND `stat_value1` = 10;\n"
            "UPDATE `item_template` SET `stat_value1` = 99 WHERE `entry` = 1 AND `stat_value1` = 10;\n"  # stale guard
            "UPDATE `item_template` SET `dmg_min1` = 181.2888 WHERE `entry` = 2 AND ABS(`dmg_min1` - 180.457) < 0.01;\n"
            "UPDATE `item_template` SET `dmg_min1` = 1 WHERE `entry` = 3 AND ABS(`dmg_min1` - 49) < 0.01;\n"
            "UPDATE `item_template` SET `Flags` = `Flags`|4096|32768 WHERE `entry` IN (2, 3);\n"
        ))
        rows = overlay.resolve_current_rows()
        self.assertEqual(rows[1]["stat_value1"], 11)
        self.assertEqual(rows[2]["dmg_min1"], 181.2888)
        self.assertEqual(rows[3]["dmg_min1"], 50)
        self.assertEqual((rows[2]["Flags"], rows[3]["Flags"]), (1 | 4096 | 32768, 4096 | 32768))
        self.assertEqual(replay.skips(), [])

    def test_upsert_partial_insert_variables_and_statement_order(self):
        self.write(self.pending / "rev_1.sql", (
            "INSERT INTO `item_template` (`entry`, `name`, `Quality`) VALUES\n"
            "(900000, 'New', 4) ON DUPLICATE KEY UPDATE `name` = VALUES(`name`), `Quality` = VALUES(`Quality`);\n"
            "SET @E := 3;\n"
            "DELETE FROM `item_template` WHERE `entry` = @E;\n"
            "INSERT INTO `item_template` (`entry`, `name`) VALUES (@E, \"Three again\");\n"
        ))
        rows = overlay.resolve_current_rows()
        self.assertEqual(rows[900000], {"entry": 900000, "name": "New", "Quality": 4, "stat_value1": 0,
                                        "dmg_min1": 0.0, "Flags": 0})
        self.assertEqual((rows[3]["name"], rows[3]["stat_value1"]), ("Three again", 0))

    def test_frozen_order_module_sql_and_apply_text(self):
        self.write(self.modules / "mod-x/data/sql/db-world/x.sql",
                   "UPDATE `item_template` SET `Quality` = 5 WHERE `entry` = 1;\n")
        rows = overlay.resolve_current_rows()
        self.assertEqual(rows[1]["Quality"], 5)
        overlay.apply_text("UPDATE `item_template` SET `Quality` = 6 WHERE `entry` IN (1, 2);\n", rows)
        self.assertEqual((rows[1]["Quality"], rows[2]["Quality"], rows[3]["Quality"]), (6, 6, 4))

    def test_a_skip_is_recorded_and_warned(self):
        self.write(self.merged / "2026_01_01_00.sql",
                   "UPDATE `item_template` SET `Quality` = 1 WHERE `entry` = (SELECT 1);\n"
                   "UPDATE item_template SET `Quality` = 1 WHERE `entry` = 2;\n")
        overlay.resolve_current_rows()
        found = replay.skips({"item_template"})
        self.assertEqual(len(found), 2)
        self.assertEqual({s.source for s in found}, {"2026_01_01_00.sql"})
        out = io.StringIO()
        replay.warn_skips({"item_template"}, file=out)
        self.assertIn("WARNING: replay: 2 SQL statement(s) could not be replayed", out.getvalue())
        self.assertIn("item_template: 2 statement(s) in 1 file(s)", out.getvalue())

    def test_get_rows_warns_once_per_fresh_resolve(self):
        self.write(self.merged / "2026_01_01_00.sql",
                   "UPDATE `item_template` SET `Quality` = 1 WHERE `entry` = (SELECT 1);\n")
        with mock.patch.dict(overlay._cache, {"key": None, "rows": None}):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                overlay.get_rows()
                overlay.get_rows()
        self.assertEqual(err.getvalue().count("WARNING: replay: 1 SQL statement(s)"), 1)

    def test_session_keeps_skips_and_leaves_no_corpus_active(self):
        self.write(self.merged / "2026_01_01_00.sql",
                   "UPDATE `item_template` SET `Quality` = 1 WHERE `entry` = (SELECT 1);\n")
        replay.sqlcorpus.SKIPS.record("other", "f.sql", 0, "earlier", "x")
        with replay.session() as since:
            self.assertIsNotNone(replay.sqlcorpus.active())
            self.assertEqual(since, 1)
            replay.load_table("item_template", ("entry",))
        self.assertIsNone(replay.sqlcorpus.active())
        self.assertEqual([s.table for s in replay.sqlcorpus.SKIPS.entries], ["other", "item_template"])


class DiskCacheTest(ScratchRepo):
    def test_a_cached_session_gives_the_same_rows_and_replays_pending_on_top(self):
        self.write(self.base / "item_template.sql", ITEM_DUMP)
        self.write(self.merged / "2026_01_01_00.sql", "UPDATE `item_template` SET `Quality` = 7 WHERE `entry` = 1;\n")
        cold = overlay.resolve_current_rows(cache=True)
        self.assertTrue(any(replay.CACHE_DIR.rglob("snap-*.bin")))
        self.write(self.pending / "rev_1.sql", "UPDATE `item_template` SET `Quality` = 8 WHERE `entry` = 2;\n")
        warm = overlay.resolve_current_rows(cache=True)
        self.assertEqual(warm, {**cold, 2: {**cold[2], "Quality": 8}})
        self.assertEqual(warm, overlay.resolve_current_rows())


class SchemaChangeTest(ScratchRepo):
    def test_rename_table_carries_rows_and_alter_backfills_defaults(self):
        self.write(self.merged / "2026_01_01_00.sql", (
            "CREATE TABLE IF NOT EXISTS `item_budget_assign` (\n"
            "  `entry` int unsigned NOT NULL DEFAULT '0',\n"
            "  `template_id` int unsigned NOT NULL DEFAULT '0',\n"
            "  `budget_mult` float NOT NULL DEFAULT '1',\n"
            "  PRIMARY KEY (`entry`)\n) ENGINE=InnoDB;\n"
            "DELETE FROM `item_budget_assign` WHERE `entry` IN (1, 2);\n"
            "INSERT INTO `item_budget_assign` (`entry`, `template_id`, `budget_mult`) VALUES (1, 5, 0.5), (2, 5, 1);\n"
        ))
        self.write(self.merged / "2026_01_02_00.sql", (
            "UPDATE `item_budget_assign` SET `budget_mult` = 0.75 WHERE `entry` = 1;\n"
            "RENAME TABLE `item_budget_assign` TO `item_itemization`;\n"
            "ALTER TABLE `item_itemization`\n  DROP COLUMN `template_id`,\n"
            "  ADD `primary_share` smallint unsigned NOT NULL DEFAULT '6000';\n"
            "INSERT INTO `item_itemization` (`entry`, `budget_mult`, `primary_share`) VALUES (3, 1, 5000);\n"
            "DELETE FROM `item_itemization` WHERE `entry` = 2;\n"  # a DELETE after the INSERT: statement order
        ))
        # A later, unrelated table of the old name must not leak into the renamed one.
        self.write(self.merged / "2026_01_03_00.sql", (
            "CREATE TABLE `item_budget_assign` (`entry` int NOT NULL DEFAULT '0') ENGINE=InnoDB;\n"
            "INSERT INTO `item_budget_assign` (`entry`) VALUES (77);\n"
        ))
        self.assertEqual(budget_overlay.table_columns("item_itemization"), ["entry", "budget_mult", "primary_share"])
        rows = budget_overlay.resolve_table_rows("item_itemization", ("entry",))
        self.assertEqual(rows, {
            (1,): {"entry": 1, "budget_mult": 0.75, "primary_share": 6000},
            (3,): {"entry": 3, "budget_mult": 1, "primary_share": 5000},
        })

    def test_alter_rename_column_and_loot_reads_id(self):
        self.write(self.base / "creature.sql", CREATURE_DUMP)
        self.write(self.merged / "2026_06_16_00.sql", (
            "ALTER TABLE `creature` CHANGE COLUMN `id1` `id` int unsigned NOT NULL DEFAULT '0', DROP COLUMN `id2`;\n"
            "INSERT INTO `creature` (`guid`, `id`, `map`) VALUES (3, 13, 36);\n"
            "DELETE FROM `creature` WHERE `id` = 10 AND `map` = 36;\n"
        ))
        self.assertEqual(replay.final_columns("creature"), ["guid", "id", "map"])
        rows = replay.load_table("creature")
        self.assertEqual(sorted(rows.values(), key=lambda r: r["guid"]),
                         [{"guid": 2, "id": 11, "map": 36}, {"guid": 3, "id": 13, "map": 36}])
        tables = {"creature": list(rows.values())}
        with mock.patch.object(loot, "_tables", return_value={**tables, "derived": {}}):
            self.assertEqual(loot._map_to_entries(), {36: {11, 13}})


if __name__ == "__main__":
    unittest.main()
