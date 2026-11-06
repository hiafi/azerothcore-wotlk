"""
Unit tests for `lib/replay_diff.py` (the replay-vs-live harness behind `replay_diff.py`). No database: the live side
is a dict, as `replay_diff.parse_mysql_batch` would return it.

    apps/dbc-tools/.venv/bin/python3 -m unittest lib.test_replay_diff   (from apps/dbc-tools)
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml  # noqa: E402

from lib import frozen_replay, replay_diff, state, trainer_state  # noqa: E402

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


TALENTTAB_DDL = (
    "CREATE TABLE `talenttab_dbc` (\n"
    "  `ID` int NOT NULL DEFAULT '0',\n"
    "  `Name_Lang_enUS` varchar(100) DEFAULT NULL,\n"
    "  `OrderIndex` int NOT NULL DEFAULT '0',\n"
    "  PRIMARY KEY (`ID`)\n"
    ") ENGINE=InnoDB;\n"
)


class DuplicateKeysFailTheCheckTest(unittest.TestCase):
    """Review N6: two replayed rows on one key are a replay bug the live table cannot show; the CLI exits 1."""

    def _cli(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("replay_diff_cli", Path(__file__).resolve().parents[1]
                                                      / "replay_diff.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_whole_exits_1_on_a_duplicate_key(self):
        import argparse
        import contextlib
        import io
        from unittest import mock

        cli = self._cli()
        schema = replay_diff.Schema(("entry", "v"), ("entry",), {}, frozenset())
        live = [{"entry": "1", "v": "2"}]
        args = argparse.Namespace(limit=5, json=None, database="db")
        for replayed, want in (([{"entry": 1, "v": 2}], 0), ([{"entry": 1, "v": 2}, {"entry": 1, "v": 2}], 1)):
            with self.subTest(replayed=replayed), \
                    mock.patch.object(replay_diff, "REPLAYED_TABLES", ("widget",)), \
                    mock.patch.object(replay_diff, "table_schema", return_value=schema), \
                    mock.patch.object(replay_diff, "replay_whole_table", return_value=(replayed, [], [])), \
                    mock.patch.object(replay_diff, "load_allowed", return_value={}), \
                    mock.patch.object(cli, "_live_schema", return_value=schema), \
                    mock.patch.object(cli, "_run_sql", return_value=live), \
                    mock.patch.object(cli.sqlcorpus, "activate"), \
                    contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(cli._whole(args, [], set(), {"widget"}), want)
            if want:
                self.assertIn("DUPLICATE KEYS: widget", out.getvalue())


class LiveOrphanRowsTest(unittest.TestCase):
    """`source/live_orphan_rows.sql` as the whole-table replay's last step: it fills rows no file wrote and remaps a
    cell only while it holds the value the remap replaced, under both loaders."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        for d in ("base", "promoted", "pending", "modules", "frozen"):
            (root / d).mkdir(parents=True)
        (root / "base" / "talenttab_dbc.sql").write_text(TALENTTAB_DDL)
        (root / "promoted" / "2026_09_01_00.sql").write_text(
            "INSERT INTO `talenttab_dbc` (`ID`, `Name_Lang_enUS`, `OrderIndex`) VALUES (1, 'file', 5), (2, 'two', 7);\n"
        )
        (root / "seed.sql").write_text(
            "-- a comment\n"
            "INSERT IGNORE INTO `talenttab_dbc` (`ID`, `Name_Lang_enUS`, `OrderIndex`) VALUES\n"
            "(1, 'seed', 9),\n"
            "(3, 'only live', 2);\n"
            "UPDATE `talenttab_dbc` SET `OrderIndex` = 70 WHERE `OrderIndex` = 7 AND `ID` IN (\n    2, 3);\n"
            "UPDATE `talenttab_dbc` SET `OrderIndex` = 50 WHERE `OrderIndex` = 4 AND `ID` IN (\n    1);\n"
        )
        (root / "secondary.sql").write_text("")
        self._orig = (
            trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR,
            trainer_state.MODULES_DIR, frozen_replay.FROZEN_ROOT, replay_diff.LIVE_ORPHAN_ROWS_SQL,
            state.LIVE_SECONDARY_ROWS_SQL,
        )
        trainer_state.BASE_SQL_DIR = root / "base"
        trainer_state.PROMOTED_SQL_DIR = root / "promoted"
        trainer_state.PENDING_SQL_DIR = root / "pending"
        trainer_state.MODULES_DIR = root / "modules"
        frozen_replay.FROZEN_ROOT = root / "frozen"
        replay_diff.LIVE_ORPHAN_ROWS_SQL = root / "seed.sql"
        state.LIVE_SECONDARY_ROWS_SQL = root / "secondary.sql"
        self.root = root

    def tearDown(self):
        (
            trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR,
            trainer_state.MODULES_DIR, frozen_replay.FROZEN_ROOT, replay_diff.LIVE_ORPHAN_ROWS_SQL,
            state.LIVE_SECONDARY_ROWS_SQL,
        ) = self._orig
        self._tmp.cleanup()

    def _replay(self, loader: str) -> dict:
        schema = replay_diff.table_schema("talenttab_dbc")
        rows, skipped, _ = replay_diff.replay_whole_table("talenttab_dbc", schema, loader=loader)
        self.assertEqual(skipped, [])
        return {int(r["ID"]): (r["Name_Lang_enUS"], int(r["OrderIndex"])) for r in rows}

    def test_fills_rows_no_file_wrote_and_remaps_guarded_cells(self):
        for loader in ("composite", "keyed"):
            with self.subTest(loader=loader):
                # 1: a file wrote it, INSERT IGNORE keeps the file's row and the guard (4) does not match.
                # 2: the file's 7 is remapped to 70. 3: only the seed has it; its 2 is not the guard's 7.
                self.assertEqual(self._replay(loader), {1: ("file", 5), 2: ("two", 70), 3: ("only live", 2)})

    def test_a_later_change_wins_over_the_remap(self):
        (self.root / "pending" / "rev_1.sql").write_text(
            "UPDATE `talenttab_dbc` SET `OrderIndex` = 8 WHERE `ID` = 2;\n"
            "INSERT INTO `talenttab_dbc` (`ID`, `Name_Lang_enUS`, `OrderIndex`) VALUES (3, 'from a file', 1);\n"
        )
        for loader in ("composite", "keyed"):
            with self.subTest(loader=loader):
                self.assertEqual(self._replay(loader), {1: ("file", 5), 2: ("two", 8), 3: ("from a file", 1)})

    def test_known_limit_a_later_delete_of_a_seeded_id_comes_back(self):
        # Review N7, pinned so a change to it is deliberate: the seed runs after every file, so a file that deletes a
        # seeded id sees it re-added (a false `*extra` in the check; the fix is to drop the id from the seed).
        (self.root / "pending" / "rev_1.sql").write_text("DELETE FROM `talenttab_dbc` WHERE `ID` = 3;\n")
        self.assertEqual(self._replay("composite")[3], ("only live", 2))
        self.assertIn("never add an allow-list entry",
                      (Path(__file__).resolve().parents[1] / "source" / "live_orphan_rows.sql").read_text()[:4000])

    def test_without_the_seed_file_nothing_is_added(self):
        replay_diff.LIVE_ORPHAN_ROWS_SQL = self.root / "missing.sql"
        self.assertEqual(self._replay("composite"), {1: ("file", 5), 2: ("two", 7)})


class LiveOrphanRowsFileTest(unittest.TestCase):
    """The shipped seed file: only the three tables, only the replay-safe statement shapes, and no id inside a block
    dbc-tools owns (a reserved block is regenerated from source, so a seeded row there would be pruned)."""

    def test_shapes_and_no_reserved_ids(self):
        text = replay_diff.LIVE_ORPHAN_ROWS_SQL.read_text(encoding="utf-8")
        blocks = yaml.safe_load((Path(__file__).resolve().parents[1] / "source" / "ids.yaml").read_text())
        reserved = {"spell_dbc": blocks["spell"], "talent_dbc": blocks["talent"], "talenttab_dbc": blocks["talenttab"]}
        heads = re.findall(r"^(INSERT IGNORE INTO|UPDATE|INSERT INTO|DELETE FROM|REPLACE INTO) `(\w+)`", text, re.M)
        self.assertTrue(heads)
        self.assertEqual({verb for verb, _ in heads}, {"INSERT IGNORE INTO", "UPDATE"})
        self.assertEqual({table for _, table in heads}, set(reserved))
        for update in re.findall(r"^UPDATE .*?;$", text, re.M | re.S):
            self.assertRegex(update, r"^UPDATE `\w+` SET `(\w+)` = -?\d+ WHERE `\1` = -?\d+ AND `ID` IN \([\d,\s]+\);$")
        for section in re.split(r"^(?=INSERT IGNORE INTO|UPDATE)", text, flags=re.M):
            m = re.match(r"(?:INSERT IGNORE INTO|UPDATE) `(\w+)`", section)
            if not m:
                continue
            block = reserved[m.group(1)]
            ids = [int(i) for i in re.findall(r"^\((-?\d+),", section, re.M)]
            if section.startswith("UPDATE"):
                ids = [int(i) for i in re.findall(r"\d+", section.split("IN (", 1)[1])]
            self.assertTrue(ids)
            inside = [i for i in ids if block["start"] <= i <= block["end"]]
            self.assertEqual(inside, [], m.group(1))


if __name__ == "__main__":
    unittest.main()
