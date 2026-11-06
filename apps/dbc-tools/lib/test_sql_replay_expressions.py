"""
The statement shapes the SQL replay learned in dbc-replay-fix (`sql_dump`): session variables assigned from
expressions, expressions over them in VALUES / SET / WHERE, double-quoted strings, comments inside a statement,
`INSERT IGNORE`, `TRUNCATE`, `ALTER TABLE` column renames, an omitted key column, WHEREs on non-key columns, and the
skip log that makes every statement the replay cannot apply visible.

    apps/dbc-tools/.venv/bin/python3 -m unittest lib.test_sql_replay_expressions   (from apps/dbc-tools)
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import sql_dump, sqlcorpus  # noqa: E402
from lib.dbcfmt import DbcTable  # noqa: E402

SS_COLUMNS = ("entryorguid", "source_type", "id", "link", "event_type", "comment")
SS_KEY = ("entryorguid", "source_type", "id", "link")
SS_DEFAULTS = {"entryorguid": 0, "source_type": 0, "id": 0, "link": 0, "event_type": 0, "comment": ""}
WIDGET = DbcTable(
    name="Widget", dbc_filename="Widget.dbc", sql_table="widget_dbc", fmt="nsi", columns=("ID", "Name", "Value"),
)


def replay(sql: str, columns=SS_COLUMNS, key=SS_KEY, table="smart_scripts", defaults=SS_DEFAULTS, rows=None):
    rows = {} if rows is None else rows
    sql_dump.apply_composite_key_statements(rows, columns, key, table, sql, defaults=defaults, source="t.sql")
    return rows


class ValueExpressionTest(unittest.TestCase):
    def value(self, text: str, variables=None):
        return sql_dump._read_value(text + ")", 0, variables=variables)[0]

    def test_shapes(self):
        v = {"@guid": 1000, "@entry": 24, "@cguid": 50}
        for text, want in (
            ("@GUID", 1000), ("@GUID+15", 1015), ("(@GUID+15)", 1015), ("-@GUID", -1000),
            ("@ENTRY*100+1", 2401), ("@ENTRY * 100", 2400), ("-(@CGUID+27)", -77), ("100*@ENTRY", 2400),
            ("(@GUID)*2+(@ENTRY-4)", 2020), ("~1 & 7", 6), ("0x10 | 0x01", 17), ("-5", -5), ("2.5", 2.5),
        ):
            with self.subTest(text=text):
                self.assertEqual(self.value(text, v), want)

    def test_variable_names_are_case_insensitive(self):
        self.assertEqual(self.value("@Guid", {"@guid": 3}), 3)

    def test_unknown_and_unresolved_variables_raise_replay_skip(self):
        with self.assertRaisesRegex(sql_dump.ReplaySkip, "unknown session variable @x"):
            self.value("@x", {})
        with self.assertRaisesRegex(sql_dump.ReplaySkip, "no value the replay can compute"):
            self.value("@x + 1", {"@x": sql_dump._Unresolved("subquery")})

    def test_double_quoted_strings(self):
        self.assertEqual(self.value('"a""b\\"c"'), 'a"b"c')
        self.assertEqual(self.value('""'), "")
        self.assertEqual(self.value('"it\'s"'), "it's")

    def test_function_call_is_not_a_value(self):
        with self.assertRaises(sql_dump.ReplaySkip):
            self.value("UNIX_TIMESTAMP()")


class SetStatementTest(unittest.TestCase):
    def run_sets(self, sql: str) -> dict:
        variables: dict = {}
        pos = 0
        while True:
            m = sql_dump._next_statement(sql, pos, "", kinds="S")
            if m is None:
                return variables
            pos = sql_dump._apply_set(sql, m.end(), m.group("set_name"), variables)

    def test_derived_chain_multi_and_non_integer(self):
        v = self.run_sets(
            "SET @CGUID := 12345;\nSET @PATH := @CGUID * 10;\nSET @NEXT = @PATH + (@CGUID - 5) * 2;\n"
            "SET @A := 1, @B := @A + 1;\nSET @WHEN := '2026-01-01 00:00:00';\nSET @F := 1.5;\nSET @N := -(@A + 3);\n"
            "SET @HEX = 0x10 | 0x20;\n"
        )
        self.assertEqual(
            (v["@cguid"], v["@path"], v["@next"], v["@a"], v["@b"], v["@when"], v["@f"], v["@n"], v["@hex"]),
            (12345, 123450, 123450 + 24680, 1, 2, "2026-01-01 00:00:00", 1.5, -4, 48),
        )

    def test_subquery_and_if_leave_the_variable_unresolved(self):
        v = self.run_sets("SET @G := (SELECT MAX(`guid`) + 1 FROM `creature`);\nSET @S = IF(@G IS NULL, 'a', 'b');\n")
        self.assertIsInstance(v["@g"], sql_dump._Unresolved)
        self.assertIsInstance(v["@s"], sql_dump._Unresolved)

    def test_variables_are_per_text_and_in_order(self):
        rows = replay(
            "SET @E := 10;\nINSERT INTO `smart_scripts` (`entryorguid`, `id`) VALUES (@E, 0);\n"
            "SET @E := 20;\nINSERT INTO `smart_scripts` (`entryorguid`, `id`) VALUES (@E, 0);\n"
        )
        self.assertEqual({k[0] for k in rows}, {10, 20})
        rows = replay("INSERT INTO `smart_scripts` (`entryorguid`, `id`) VALUES (@E, 0);\n", rows=rows)
        self.assertEqual({k[0] for k in rows}, {10, 20})  # a new text is a new session: @E is unknown


class WhereExpressionTest(unittest.TestCase):
    BASE = (
        "INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`) VALUES "
        "(-1000, 0, 0, 0), (-1006, 0, 0, 0), (2400, 9, 0, 0), (2401, 9, 0, 0), (24, 0, 0, 0), (25, 0, 0, 0);\n"
    )

    def keys(self, sql: str) -> set:
        return {k[0] for k in replay("SET @GUID := 1000; SET @ENTRY := 24; SET @CGUID := 1000;\n" + self.BASE + sql)}

    def test_deletes(self):
        everything = {-1000, -1006, 2400, 2401, 24, 25}
        for where, gone in (
            ("`entryorguid` = -@GUID AND `source_type` = 0", {-1000}),
            ("`entryorguid` = @ENTRY*100+1 AND `source_type` = 9", {2401}),
            ("(`source_type` = 0 AND `entryorguid` BETWEEN -(@CGUID+6) AND -(@CGUID+0))", {-1000, -1006}),
            ("`entryorguid` IN (@ENTRY*100, @ENTRY*100+1) AND `source_type` = 9", {2400, 2401}),
            ("`entryorguid` IN (@ENTRY)", {24}),
            ("`entryorguid` IN ((@ENTRY+1)*100, 24)", {24}),
            ("`entryorguid` = (@GUID+15)*0+25", {25}),
        ):
            with self.subTest(where=where):
                self.assertEqual(self.keys(f"DELETE FROM `smart_scripts` WHERE {where};\n"), everything - gone)

    def test_update_with_comments_and_expressions(self):
        rows = replay(
            "SET @E := 24;\n" + self.BASE +
            "UPDATE `smart_scripts` SET `event_type` = 10000, -- InitialMin: 10s\n"
            "  `comment` = \"say \"\"hi\"\"\" WHERE `entryorguid` = @E AND `source_type` = 0; -- trailing\n"
        )
        self.assertEqual((rows[(24, 0, 0, 0)]["event_type"], rows[(24, 0, 0, 0)]["comment"]), (10000, 'say "hi"'))

    def test_prepare_statement_leaves_binary_operators_and_strings(self):
        body = sql_dump._prepare_statement(
            "SET `v` = `v` + @A, `c` = '@A -- not a comment' WHERE `x` = -@A AND `y` IN (@A, 2) -- c\n;",
            {"@a": 5},
        )
        self.assertEqual(body, "SET `v` = `v` + 5, `c` = '@A -- not a comment' WHERE `x` = -5 AND `y` IN (5, 2)  \n;")


class StatementShapeTest(unittest.TestCase):
    def test_row_expressions_and_repeated_columns(self):
        rows = replay(
            "INSERT INTO `smart_scripts` (`entryorguid`, `event_type`) VALUES (1, 7);\n"
            "UPDATE `smart_scripts` SET `event_type` = (`event_type` & ~1) WHERE `entryorguid` = 1;\n"
            "UPDATE `smart_scripts` SET `event_type` = `event_type` & ~(2 | 4), `event_type` = `event_type` | 256 "
            "WHERE `entryorguid` = 1;\n"
        )
        self.assertEqual(rows[(1, 0, 0, 0)]["event_type"], 256)

    def test_omitted_key_column_takes_the_schema_default(self):
        rows = replay(
            "INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `comment`) VALUES (5, 0, 1, 'x');"
        )
        self.assertEqual(list(rows), [(5, 0, 1, 0)])
        self.assertEqual(rows[(5, 0, 1, 0)]["link"], 0)

    def test_insert_ignore_truncate(self):
        rows = replay(
            "INSERT INTO `smart_scripts` (`entryorguid`, `comment`) VALUES (1, 'a');\n"
            "INSERT IGNORE INTO `smart_scripts` (`entryorguid`, `comment`) VALUES (1, 'b'), (2, 'c');\n"
        )
        self.assertEqual({k[0]: r["comment"] for k, r in rows.items()}, {1: "a", 2: "c"})
        self.assertEqual(replay("TRUNCATE TABLE `smart_scripts`;", rows=rows), {})

    def test_alter_rename_and_positional_layout(self):
        rows = replay(
            "INSERT INTO `creature` VALUES (1, 10, 0);\n"
            "ALTER TABLE `creature` CHANGE COLUMN `id1` `id` int unsigned NOT NULL DEFAULT 0, DROP COLUMN `id2`;\n"
            "ALTER TABLE `creature` ADD `map` int NOT NULL DEFAULT '0' AFTER `id`;\n"
            "INSERT INTO `creature` VALUES (2, 20, 530);\n"
            "UPDATE `creature` SET `map` = 1 WHERE `id` = 10;\n"
            "DELETE FROM `creature` WHERE `id` = 99 AND `map` = 0;\n",
            columns=("guid", "id1", "id2"), key=("guid",), table="creature", defaults={},
        )
        self.assertEqual(rows, {(1,): {"guid": 1, "id": 10, "map": 1}, (2,): {"guid": 2, "id": 20, "map": 530}})

    def test_non_key_where_is_strict_and_uses_defaults(self):
        rows = replay(
            "INSERT INTO `smart_scripts` (`entryorguid`, `event_type`) VALUES (1, 5), (2, 6);\n"
            "INSERT INTO `smart_scripts` (`entryorguid`) VALUES (3);\n"
            "DELETE FROM `smart_scripts` WHERE `event_type` = 5;\n"
            "DELETE FROM `smart_scripts` WHERE `event_type` = 0;\n"  # 3 holds no event_type: its default, 0, matches
        )
        self.assertEqual({k[0] for k in rows}, {2})

    def test_no_where_mask_condition_string_in_and_commented_heads(self):
        rows = replay(
            "INSERT INTO `smart_scripts` (`entryorguid`, `event_type`, `comment`) VALUES (1, 5, 'a'), (2, 6, 'b'), "
            "(3, 7, 'c');\n"
            "-- INSERT INTO `smart_scripts` (`entryorguid`) VALUES (9);\n"
            "SET @MASK := 2;\n"
            "UPDATE `smart_scripts` SET `event_type` = `event_type` & ~@MASK WHERE (`event_type` & @MASK) != 0;\n"
            "DELETE FROM `smart_scripts` WHERE `comment` IN ('A', 'x');\n"
            "UPDATE `smart_scripts` SET `event_type` = `event_type` + 1;\n"
        )
        self.assertEqual({k[0]: r["event_type"] for k, r in rows.items()}, {2: 5, 3: 6})

    def test_abs_float_guard(self):
        # item-tools' guard on a FLOAT column (item_lib/emit._guard_term): the UPDATE applies only when it holds.
        columns, key = ("entry", "dmg_min1", "dmg_max1"), ("entry",)
        rows = replay(
            "INSERT INTO `item_template` (`entry`, `dmg_min1`, `dmg_max1`) VALUES (1, 180.457, 335.135), "
            "(2, 100, 200);\n"
            "UPDATE `item_template` SET `dmg_min1` = 181.2888, `dmg_max1` = 336.6792 WHERE `entry` = 1 "
            "AND ABS(`dmg_min1` - 180.457) < 0.01 AND ABS(`dmg_max1` - 335.135) < 0.01;\n"
            "UPDATE `item_template` SET `dmg_min1` = 1 WHERE `entry` = 2 AND ABS(`dmg_min1` - 99) < 0.01;\n"
            "UPDATE `item_template` SET `dmg_max1` = 7 WHERE (ABS(`dmg_max1` + -200) <= 0.5);\n",
            columns, key, "item_template", {"entry": 0, "dmg_min1": 0.0, "dmg_max1": 0.0},
        )
        self.assertEqual({k[0]: (r["dmg_min1"], r["dmg_max1"]) for k, r in rows.items()},
                         {1: (181.2888, 336.6792), 2: (100, 7)})
        self.assertIsNone(sql_dump.parse_where_predicate("ABS(`a` - 'x') < 1"))

    def test_nested_or_group_in_an_and_chain(self):
        # 2026_02_20_03.sql / 2026_09_09_04.sql (creature_loot_template): `A AND (B OR (C AND D))`.
        columns, key = ("Entry", "Item", "Reference"), ("Entry", "Item")
        rows = replay(
            "INSERT INTO `creature_loot_template` (`Entry`, `Item`, `Reference`) VALUES (1, 1, 0), (1, 2, 15), "
            "(1, 3, 35), (1, 4, 50), (2, 5, 15);\n"
            "DELETE FROM `creature_loot_template` WHERE\n`Entry` IN (1)\nAND (\n`Reference` BETWEEN 10 AND 20 OR\n"
            "`Reference` BETWEEN 30 AND 40\n);\n"
            "DELETE FROM `creature_loot_template` WHERE `Entry` = 1 AND (`Item` IN (9) OR (`Item` IN (4) AND "
            "`Reference` IN (50)));\n",
            columns, key, "creature_loot_template", {"Entry": 0, "Item": 0, "Reference": 0},
        )
        self.assertEqual(sorted(rows), [(1, 1), (2, 5)])
        self.assertIsNone(sql_dump.parse_where_predicate("`a` = 1 AND (`b` = 2 OR SIN(`c`) = 0)"))

    def test_column_names_are_case_insensitive(self):
        rows = replay(
            "INSERT INTO `smart_scripts` (`EntryOrGuid`, `Event_Type`) VALUES (1, 5), (2, 6);\n"
            "UPDATE `smart_scripts` SET `EVENT_TYPE` = 9 WHERE `entryOrGUID` = 1;\n"
            "DELETE FROM `smart_scripts` WHERE `ENTRYORGUID` = 2;\n"
        )
        self.assertEqual(
            rows, {(1, 0, 0, 0): {"entryorguid": 1, "event_type": 9, "source_type": 0, "id": 0, "link": 0}},
        )
        dbc_rows = {7: {"ID": 7, "Name": "", "Value": 1}}
        sql_dump.apply_statements(dbc_rows, WIDGET, "UPDATE `widget_dbc` SET `value` = 2 WHERE `Id` = 7;")
        self.assertEqual(dbc_rows[7]["Value"], 2)

    def test_single_key_replay_reads_the_same_shapes(self):
        rows = {}
        sql_dump.apply_statements(
            rows, WIDGET,
            "SET @ID := 7;\nINSERT INTO `widget_dbc` VALUES (@ID, \"seven\", @ID*2), (@ID+1, 'eight', 0);\n"
            "UPDATE `widget_dbc` SET `Value` = `Value` | 1 WHERE `Name` = 'SEVEN';\n"
            "DELETE FROM `widget_dbc` WHERE `ID` = @ID+1 OR `Value` > 100;\n",
        )
        self.assertEqual(rows, {7: {"ID": 7, "Name": "seven", "Value": 15}})

    def test_read_table_rows_uses_the_variables_in_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.sql"
            path.write_text(
                "SET @G := 1;\nINSERT INTO `t` (`a`) VALUES (@G);\n"
                "SET @G := @G + 10;\nINSERT INTO `t` (`a`) VALUES (@G);\n"
                "INSERT INTO `t` (`a`) VALUES (@NOPE);\nINSERT INTO `t` (`a`) VALUES (\"x\");\n"
            )
            sqlcorpus.SKIPS.clear()
            self.assertEqual(
                sql_dump.read_table_rows(path, "t", ("a",), tolerant=True), [{"a": 1}, {"a": 11}, {"a": "x"}],
            )
            self.assertEqual([s.reason for s in sqlcorpus.SKIPS.entries], ["unknown session variable @NOPE"])
            with self.assertRaises(sql_dump.ReplaySkip):
                sql_dump.read_table_rows(path, "t", ("a",))


class SkipLogTest(unittest.TestCase):
    def setUp(self):
        sqlcorpus.SKIPS.clear()
        self.addCleanup(sqlcorpus.SKIPS.clear)

    def test_every_skip_is_recorded_with_its_reason(self):
        seen = []
        rows: dict = {}
        sql_dump.apply_composite_key_statements(
            rows, SS_COLUMNS, SS_KEY, "smart_scripts",
            "SET @G := (SELECT 1);\n"
            "INSERT INTO `smart_scripts` (`entryorguid`) VALUES (@G);\n"
            "DELETE FROM `smart_scripts` WHERE `entryorguid` IN (SELECT 1);\n"
            "INSERT INTO `smart_scripts` (`entryorguid`, `id`) VALUES (1, 0), (2);\n",
            on_skip=seen.append, defaults=SS_DEFAULTS, source="odd.sql",
        )
        self.assertEqual(list(rows), [(1, 0, 0, 0)])
        reasons = [s.reason for s in sqlcorpus.SKIPS.entries]
        self.assertEqual(len(reasons), 3)
        self.assertIn("SET @G", reasons[0])
        self.assertEqual(reasons[1], "unsupported IN list (SELECT 1)")
        self.assertEqual(reasons[2], "1 INSERT row(s) not applied: 1 values for 2 columns")
        self.assertEqual({s.source for s in sqlcorpus.SKIPS.entries}, {"odd.sql"})
        self.assertEqual(len(seen), 3)
        [line] = sqlcorpus.SKIPS.summary()
        self.assertTrue(line.startswith("smart_scripts: 3 statement(s) in 1 file(s): "), line)
        self.assertIn("1x unsupported IN list", line)

    def test_unique_merges_two_loaders_of_one_table(self):
        for _ in range(2):
            sql_dump.apply_statements({}, WIDGET, "DELETE FROM `widget_dbc` WHERE `ID` = (SELECT 1);", source="a.sql")
        self.assertEqual(len(sqlcorpus.SKIPS.entries), 2)
        self.assertEqual(len(sqlcorpus.SKIPS.unique()), 1)

    def test_a_cache_hit_records_the_same_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.sql"
            path.write_text("DELETE FROM `widget_dbc` WHERE `ID` = (SELECT 1);\n")

            def step(rows, p):
                sql_dump.apply_statements(rows, WIDGET, sqlcorpus.read_text(p))
                return rows

            for expect_hit in (False, True):
                sqlcorpus.activate(Path(tmp) / "cache", "v1")
                try:
                    sqlcorpus.checkpointed("k", (), [path], dict, step)
                    self.assertEqual(sqlcorpus.active().stats["hit"], int(expect_hit))
                    self.assertEqual([(s.source, s.reason) for s in sqlcorpus.SKIPS.entries],
                                     [("a.sql", "unsupported DELETE WHERE")])
                finally:
                    sqlcorpus.deactivate()


if __name__ == "__main__":
    unittest.main()
