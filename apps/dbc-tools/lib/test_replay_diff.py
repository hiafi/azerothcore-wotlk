"""
Unit tests for `lib/replay_diff.py` (the replay-vs-live harness behind `replay_diff.py`). No database: the live side
is a dict, as `replay_diff.parse_mysql_batch` would return it.

    apps/dbc-tools/.venv/bin/python3 -m unittest lib.test_replay_diff   (from apps/dbc-tools)
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import frozen_replay, replay_diff, trainer_state  # noqa: E402

WIDGET_DDL = (
    "CREATE TABLE `widget` (\n"
    "  `entry` int unsigned NOT NULL DEFAULT '0',\n"
    "  `name` varchar(50) DEFAULT NULL,\n"
    "  `level` tinyint unsigned NOT NULL DEFAULT '1',\n"
    "  `scale` float NOT NULL DEFAULT '1',\n"
    "  PRIMARY KEY (`entry`)\n"
    ") ENGINE=InnoDB;\n"
)
PAIR_DDL = (
    "CREATE TABLE `pair` (\n"
    "  `a` int NOT NULL,\n"
    "  `b` varchar(20) NOT NULL,\n"
    "  UNIQUE KEY `idx` (`a`,`b`)\n"
    ") ENGINE=InnoDB;\n"
)


class HarnessTest(unittest.TestCase):

    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        for d in ("base", "promoted", "pending", "modules", "frozen/slot"):
            (root / d).mkdir(parents=True)
        self.root = root
        (root / "base" / "widget.sql").write_text(
            WIDGET_DDL + "INSERT INTO `widget` VALUES (1, 'one', 10, 1), (2, 'two', 20, 1), (3, 'three', 30, 1);\n"
        )
        (root / "base" / "pair.sql").write_text(PAIR_DDL)
        (root / "promoted" / "2026_08_21_01.sql").write_text("UPDATE `widget` SET `level` = 11 WHERE `entry` = 1;\n")
        (root / "promoted" / "2026_08_22_00.sql").write_text("UPDATE `widget` SET `level` = 22 WHERE `entry` = 2;\n")
        (root / "frozen" / "slot" / "SLOT").write_text("after = 2026_08_21_01.sql\nbefore = 2026_08_22_00.sql\n")
        (root / "frozen" / "slot" / "phase_00-widget.sql").write_text(
            "UPDATE `widget` SET `level` = 60 WHERE `entry` IN (\n"
            "    1, -- One <Trainer>\n"
            "    2 -- Two\n"
            ");\n"
            "UPDATE `widget` SET `scale` = 1 WHERE `entry` = 3; -- a no-op: not in the footprint\n"
            "DELETE FROM `widget` WHERE `entry` = 3;\n"
            "INSERT INTO `widget` (`entry`, `name`) VALUES (4, 'four');\n"
        )
        self._orig = (
            trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR,
            trainer_state.MODULES_DIR, frozen_replay.FROZEN_ROOT,
        )
        trainer_state.BASE_SQL_DIR = root / "base"
        trainer_state.PROMOTED_SQL_DIR = root / "promoted"
        trainer_state.PENDING_SQL_DIR = root / "pending"
        trainer_state.MODULES_DIR = root / "modules"
        frozen_replay.FROZEN_ROOT = root / "frozen"

    def tearDown(self):
        (
            trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR,
            trainer_state.MODULES_DIR, frozen_replay.FROZEN_ROOT,
        ) = self._orig
        self._tmp.cleanup()

    def _run(self, **kwargs):
        schema = replay_diff.table_schema("widget")
        final, before, after, skipped, left_out = replay_diff.replay_with_snapshots("widget", schema, **kwargs)
        return schema, final, replay_diff.footprint(before, after, schema), skipped, left_out

    def test_frozen_tables_lists_what_each_file_writes(self):
        (slot,) = frozen_replay.slots()
        self.assertEqual(list(replay_diff.frozen_tables(slot)), ["widget"])

    def test_schema_key_falls_back_to_a_unique_key(self):
        self.assertEqual(replay_diff.table_schema("widget").key_columns, ("entry",))
        self.assertEqual(replay_diff.table_schema("pair").key_columns, ("a", "b"))

    def test_footprint_is_what_the_frozen_sql_changed(self):
        schema, final, cells, skipped, _ = self._run()
        self.assertEqual(skipped, [])  # the commented IN list is applied, not skipped
        self.assertEqual(cells[(1,)], ("level",))
        self.assertEqual(cells[(2,)], ("level",))
        self.assertEqual(cells[(3,)], schema.columns)  # deleted
        self.assertEqual(cells[(4,)], schema.columns)  # inserted
        self.assertEqual((final[(1,)]["level"], final[(2,)]["level"]), (60, 22))  # 22: after the slot

    def test_live_equal_to_the_replay_has_no_difference(self):
        schema, final, cells, _, _ = self._run()
        live = {
            "1": {"entry": "1", "level": "60"},
            "2": {"entry": "2", "level": "22"},
            "4": {"entry": "4", "name": "four", "level": "1", "scale": "1", "comment": None},
        }
        self.assertEqual(replay_diff.compare("widget", schema, cells, final, live), [])

    def test_differences_presence_and_value_and_the_allow_list(self):
        schema, final, cells, _, _ = self._run()
        live = {
            "1": {"entry": "1", "level": "61"},
            "2": {"entry": "2", "level": "22"},
            "3": {"entry": "3", "name": "three", "level": "30", "scale": "1"},
        }
        diffs = replay_diff.compare("widget", schema, cells, final, live)
        self.assertEqual(
            [(replay_diff.key_text(d.key), d.column, d.replayed, d.live) for d in diffs],
            [("1", "level", 60, "61"), ("3", "*", False, True), ("4", "*", True, False)],
        )
        allow = self.root / "allow.tsv"
        allow.write_text("# comment\nwidget\t1\tlevel\thand fix after the slot\nwidget\t9\t*\tstale entry\n")
        stale = replay_diff.explain(diffs, replay_diff.load_allowed(allow))
        self.assertEqual(diffs[0].reason, "hand fix after the slot")
        self.assertEqual([d.column for d in diffs if d.reason is None], ["*", "*"])
        self.assertEqual(stale, {("widget", "9", "*")})

    def test_a_malformed_allow_list_line_is_an_error(self):
        allow = self.root / "allow.tsv"
        allow.write_text("widget\t1\tlevel\n")
        with self.assertRaises(ValueError):
            replay_diff.load_allowed(allow)

    def test_files_not_applied_live_are_left_out(self):
        (self.root / "pending" / "rev_1.sql").write_text("UPDATE `widget` SET `level` = 5 WHERE `entry` = 1;\n")
        _, final, _, _, left_out = self._run(applied={"2026_08_21_01.sql", "2026_08_22_00.sql", "phase_00-widget.sql"})
        self.assertEqual([p.name for p in left_out], ["rev_1.sql"])
        self.assertEqual(final[(1,)]["level"], 60)
        _, final, _, _, _ = self._run()
        self.assertEqual(final[(1,)]["level"], 5)

    def test_without_the_frozen_files_the_footprint_is_empty(self):
        _, final, cells, _, _ = self._run(include_frozen=False)
        self.assertEqual(cells, {})
        self.assertEqual(final[(1,)]["level"], 11)

    def test_key_swap_with_lowercase_column_and_multi_set(self):
        (self.root / "base" / "loot.sql").write_text(
            "CREATE TABLE `loot` (\n  `Entry` int NOT NULL,\n  `Item` int NOT NULL,\n"
            "  PRIMARY KEY (`Entry`,`Item`)\n) ENGINE=InnoDB;\n"
            "INSERT INTO `loot` VALUES (1, 47241), (2, 47241);\n"
        )
        (self.root / "frozen" / "slot" / "phase_00-loot.sql").write_text(
            "SET @a := 10, @b := 20;\n"
            "UPDATE `loot` SET `Item` = 40752 WHERE `entry` IN ( -- swap\n    1 -- boss one\n) AND `Item` = 47241;\n"
            "INSERT INTO `loot` (`Entry`, `Item`) VALUES (@a+0, @b+1);\n"
        )
        schema = replay_diff.table_schema("loot")
        final, before, after, skipped, _ = replay_diff.replay_with_snapshots("loot", schema)
        self.assertEqual(skipped, [])
        self.assertEqual(sorted(final), [(1, 40752), (2, 47241), (10, 21)])
        self.assertEqual(sorted(replay_diff.footprint(before, after, schema)), [(1, 40752), (1, 47241), (10, 21)])

    def test_truncate_empties_the_table(self):
        (self.root / "frozen" / "slot" / "phase_00-widget.sql").write_text(
            "TRUNCATE TABLE `widget`;\nINSERT INTO `widget` (`entry`, `level`) VALUES (7, 7);\n"
        )
        _, final, cells, skipped, _ = self._run()
        self.assertEqual(sorted(final), [(7,)])
        self.assertEqual(sorted(cells), [(1,), (2,), (3,), (7,)])
        self.assertEqual(skipped, [])


class HelpersTest(unittest.TestCase):

    def test_values_equal(self):
        self.assertTrue(replay_diff.values_equal(5.75, "5.75"))
        self.assertTrue(replay_diff.values_equal(0.1, "0.100000001"))  # FLOAT read-back
        self.assertFalse(replay_diff.values_equal(5.7, "5.75"))
        self.assertTrue(replay_diff.values_equal(None, "0"))
        self.assertTrue(replay_diff.values_equal(None, "", is_string=True))
        self.assertFalse(replay_diff.values_equal("a", "A", is_string=True))

    def test_strip_line_comments_keeps_strings(self):
        self.assertEqual(
            frozen_replay.strip_line_comments("SET a = '--x' WHERE b IN (1, -- one\n2); -- end\n"),
            "SET a = '--x' WHERE b IN (1, \n2); \n",
        )

    def test_parse_mysql_batch(self):
        rows = replay_diff.parse_mysql_batch("a\tb\n1\tline\\none\\ttab\\\\\nNULL\t\n")
        self.assertEqual(rows, [{"a": "1", "b": "line\none\ttab\\"}, {"a": None, "b": ""}])
        self.assertEqual(replay_diff.parse_mysql_batch(""), [])

    def test_rekey_moves_a_row_whose_key_column_changed(self):
        row = {"Entry": 1, "Item": 40752}
        rows = {(1, 47241): row, (2, 5): {"Entry": 2, "Item": 5}}
        replay_diff.rekey(rows, ("Entry", "Item"))
        self.assertEqual(sorted(rows), [(1, 40752), (2, 5)])
        self.assertIs(rows[(1, 40752)], row)

    def test_canonical_columns_fixes_letter_case(self):
        self.assertEqual(
            frozen_replay.canonical_columns("UPDATE `loot` SET `Item` = 1 WHERE `entry` IN (2);", ("Entry", "Item")),
            "UPDATE `loot` SET `Item` = 1 WHERE `Entry` IN (2);",
        )

    def test_split_multi_set(self):
        self.assertEqual(
            frozen_replay.split_multi_set("SET @lootId := 46000, @refId := 46001;\nSET @x := 1;"),
            "SET @lootId := 46000; SET @refId := 46001;\nSET @x := 1;",
        )

    def test_key_text(self):
        self.assertEqual(replay_diff.key_text((10440, 2.0, "x")), "10440,2,x")


if __name__ == "__main__":
    unittest.main()
