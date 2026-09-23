"""Unit tests for `sql_dump.apply_statements` — see its docstring and
`state.py`'s for why this exists (overlaying already-promoted migrations so
`generate.py` stops permanently re-diffing every ID a past rework ever
touched against pure vanilla data).

No test harness exists elsewhere in apps/dbc-tools/, so this is a plain
stdlib `unittest` module. Run directly:

    python3 apps/dbc-tools/lib/test_sql_dump.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import sql_dump  # noqa: E402
from lib.dbcfmt import DbcTable  # noqa: E402

TABLE = DbcTable(
    name="Widget",
    dbc_filename="Widget.dbc",
    sql_table="widget_dbc",
    fmt="nsi",
    columns=("ID", "Name", "Value"),
)


class ApplyStatementsTest(unittest.TestCase):
    def test_delete_range_removes_rows(self):
        rows = {1: {"ID": 1}, 5: {"ID": 5}, 10: {"ID": 10}}
        sql_dump.apply_statements(
            rows, TABLE, "DELETE FROM `widget_dbc` WHERE `ID` BETWEEN 1 AND 5;"
        )
        self.assertEqual(set(rows), {10})

    def test_delete_id_list_removes_rows(self):
        rows = {1: {"ID": 1}, 2: {"ID": 2}, 3: {"ID": 3}}
        sql_dump.apply_statements(rows, TABLE, "DELETE FROM `widget_dbc` WHERE `ID` IN (1, 3);")
        self.assertEqual(set(rows), {2})

    def test_delete_single_id_removes_row(self):
        rows = {42: {"ID": 42}}
        sql_dump.apply_statements(rows, TABLE, "DELETE FROM `widget_dbc` WHERE (`ID` = 42);")
        self.assertEqual(rows, {})

    def test_insert_adds_and_overwrites_by_id(self):
        rows: dict = {}
        sql = (
            "INSERT INTO `widget_dbc` (`ID`, `Name`, `Value`) VALUES "
            "(1, 'Foo', 10), (2, 'Bar', 20);"
        )
        sql_dump.apply_statements(rows, TABLE, sql)
        self.assertEqual(rows[1], {"ID": 1, "Name": "Foo", "Value": 10})
        self.assertEqual(rows[2], {"ID": 2, "Name": "Bar", "Value": 20})

    def test_update_patches_only_named_fields(self):
        rows = {1: {"ID": 1, "Name": "Foo", "Value": 10}}
        sql_dump.apply_statements(rows, TABLE, "UPDATE `widget_dbc` SET `Value` = 99 WHERE (`ID` = 1);")
        self.assertEqual(rows[1], {"ID": 1, "Name": "Foo", "Value": 99})

    def test_insert_null_string_column_reads_back_as_empty_string(self):
        # sql_out.py's _sql_literal serializes a blank string as literal SQL
        # NULL (to keep generated files smaller); reading that back must not
        # produce None, or every such column would spuriously mismatch
        # build_one()'s always-"" convention (dbcfile.empty_row / build.py's
        # _set_all_locales) - this is the exact regression this test guards.
        rows: dict = {}
        sql = "INSERT INTO `widget_dbc` (`ID`, `Name`, `Value`) VALUES (1, NULL, 10);"
        sql_dump.apply_statements(rows, TABLE, sql)
        self.assertEqual(rows[1], {"ID": 1, "Name": "", "Value": 10})

    def test_update_null_string_column_reads_back_as_empty_string(self):
        rows = {1: {"ID": 1, "Name": "Foo", "Value": 10}}
        sql_dump.apply_statements(rows, TABLE, "UPDATE `widget_dbc` SET `Name` = NULL WHERE (`ID` = 1);")
        self.assertEqual(rows[1], {"ID": 1, "Name": "", "Value": 10})

    def test_update_with_session_variable_and_commented_in_list(self):
        # mod-progression's phase_00-creature_default_trainer.sql, verbatim shape.
        rows = {328: {"ID": 328, "Value": 16}, 331: {"ID": 331, "Value": 16}, 1: {"ID": 1, "Value": 5}}
        sql_dump.apply_statements(rows, TABLE, (
            "SET @TrainerId := 200;\n"
            "UPDATE `widget_dbc` SET `Value` = @TrainerId+12 WHERE `ID` IN (\n"
            "    328, -- Zaldimar Wefhellt <Mage Trainer>\n"
            "    331 -- Maginor Dumas <Mage Trainer>\n"
            ");\n"
        ))
        self.assertEqual([rows[328]["Value"], rows[331]["Value"], rows[1]["Value"]], [212, 212, 5])

    def test_update_where_id_in_list_patches_every_row(self):
        # Real shape from data/sql/updates/db_world/2026_09_14_01.sql (the Glacial Spike/
        # Fireball cast-time fix): one UPDATE repointing several IDs to the same new value.
        # Before _apply_update understood `WHERE \`ID\` IN (...)`, this fell through to
        # _skip_statement entirely - every row here would have stayed at Value=10.
        rows = {133: {"ID": 133, "Value": 10}, 200002: {"ID": 200002, "Value": 10}, 999: {"ID": 999, "Value": 10}}
        sql_dump.apply_statements(
            rows, TABLE, "UPDATE `widget_dbc` SET `Value` = 30002 WHERE `ID` IN (133, 200002);"
        )
        self.assertEqual(rows[133]["Value"], 30002)
        self.assertEqual(rows[200002]["Value"], 30002)
        self.assertEqual(rows[999]["Value"], 10)  # not in the list - untouched

    def test_update_where_id_in_list_skips_unknown_ids(self):
        rows = {133: {"ID": 133, "Value": 10}}
        sql_dump.apply_statements(
            rows, TABLE, "UPDATE `widget_dbc` SET `Value` = 99 WHERE `ID` IN (133, 404);"
        )
        self.assertEqual(rows[133]["Value"], 99)
        self.assertNotIn(404, rows)

    def test_update_on_unknown_id_is_skipped_not_raised(self):
        rows: dict = {}
        sql_dump.apply_statements(rows, TABLE, "UPDATE `widget_dbc` SET `Value` = 99 WHERE (`ID` = 404);")
        self.assertEqual(rows, {})

    def test_statements_apply_in_file_order(self):
        # A delete-then-reinsert-then-patch must leave the *last* value in
        # place — proving in-order application, not "all deletes then all
        # inserts then all updates".
        rows = {1: {"ID": 1, "Name": "Old", "Value": 1}}
        sql = (
            "DELETE FROM `widget_dbc` WHERE `ID` IN (1);\n"
            "INSERT INTO `widget_dbc` (`ID`, `Name`, `Value`) VALUES (1, 'New', 2);\n"
            "UPDATE `widget_dbc` SET `Value` = 3 WHERE (`ID` = 1);\n"
        )
        sql_dump.apply_statements(rows, TABLE, sql)
        self.assertEqual(rows[1], {"ID": 1, "Name": "New", "Value": 3})

    def test_ignores_statements_for_other_tables(self):
        rows = {1: {"ID": 1}}
        sql_dump.apply_statements(rows, TABLE, "DELETE FROM `other_dbc` WHERE `ID` IN (1);")
        self.assertEqual(rows, {1: {"ID": 1}})

    def test_unrecognized_where_clause_is_skipped_not_raised(self):
        rows = {1: {"ID": 1, "Value": 10}}
        sql = "UPDATE `widget_dbc` SET `Value` = 99 WHERE `ID` = 1 AND `Name` = 'x';"
        sql_dump.apply_statements(rows, TABLE, sql)  # must not raise
        self.assertEqual(rows[1], {"ID": 1, "Value": 10})


class ReadTableRowsTest(unittest.TestCase):
    """`lib.trainer_state`'s Phase 3 use case: `trainer_spell`/`creature`
    are hand-written enough that this needs to survive shapes
    `apply_statements`'s own tests above don't exercise."""

    def test_skips_trailing_line_comment_between_tuples(self):
        # The exact shape that broke this - data/sql/updates/db_world/
        # 2026_09_06_04.sql's trainer_spell inserts, one comment per row.
        sql = (
            "INSERT INTO `trainer_spell` (`TrainerId`, `SpellId`) VALUES\n"
            "(13, 48266),    -- Blood Presence\n"
            "(13, 45462);    -- Plague Strike\n"
        )
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "x.sql"
            path.write_text(sql)
            rows = sql_dump.read_table_rows(path, "trainer_spell", ())
        self.assertEqual(
            rows,
            [{"TrainerId": 13, "SpellId": 48266}, {"TrainerId": 13, "SpellId": 45462}],
        )

    def test_skips_leading_and_mid_tuple_comments_too(self):
        sql = (
            "INSERT INTO `t` (`A`, `B`) VALUES\n"
            "-- a leading comment\n"
            "(1, -- inline comment before a value\n2);\n"
        )
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "x.sql"
            path.write_text(sql)
            rows = sql_dump.read_table_rows(path, "t", ())
        self.assertEqual(rows, [{"A": 1, "B": 2}])

    def test_session_variable_with_offset_in_insert(self):
        # `SET @CGUID := 500;` then `(@CGUID+0, ...)` - the creature-spawn migration shape that
        # used to be skipped outright with an "invalid literal" warning.
        sql = (
            "SET @CGUID := 500;\n"
            "INSERT INTO `t` (`A`, `B`) VALUES (@CGUID+0, @CGUID + 2), (@CGUID, 1);\n"
        )
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "x.sql"
            path.write_text(sql)
            rows = sql_dump.read_table_rows(path, "t", ())
        self.assertEqual(rows, [{"A": 500, "B": 502}, {"A": 500, "B": 1}])

    def test_hex_literals_parse_as_ints(self):
        # Hand-written spell_proc rows routinely use MySQL hex for
        # ProcFlags/HitMask (data/sql/updates/db_world/2026_03_09_01.sql:
        # 0x61401035) - these used to make the whole file unparseable.
        # `0x1e5` also has to survive the "'e' means float" heuristic.
        sql = "INSERT INTO `t` (`A`, `B`, `C`) VALUES (0x10, 0x1e5, 0X0);\n"
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "x.sql"
            path.write_text(sql)
            rows = sql_dump.read_table_rows(path, "t", ())
        self.assertEqual(rows, [{"A": 16, "B": 0x1E5, "C": 0}])


class ParseCreateTableColumnsTest(unittest.TestCase):
    def test_extracts_columns_in_order(self):
        sql = (
            "CREATE TABLE `creature` (\n"
            "  `guid` int unsigned NOT NULL AUTO_INCREMENT,\n"
            "  `id1` int unsigned NOT NULL DEFAULT '0',\n"
            "  `map` smallint unsigned NOT NULL DEFAULT '0',\n"
            "  PRIMARY KEY (`guid`)\n"
            ") ENGINE=InnoDB;\n"
        )
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "creature.sql"
            path.write_text(sql)
            columns = sql_dump.parse_create_table_columns(path, "creature")
        self.assertEqual(columns, ("guid", "id1", "map"))

    def test_ignores_other_tables_and_constraint_lines(self):
        sql = (
            "CREATE TABLE `other` (`x` int);\n"
            "CREATE TABLE `trainer_spell` (\n"
            "  `TrainerId` int unsigned NOT NULL,\n"
            "  `SpellId` int unsigned NOT NULL,\n"
            "  PRIMARY KEY (`TrainerId`,`SpellId`),\n"
            "  KEY `idx_spell` (`SpellId`)\n"
            ") ENGINE=InnoDB;\n"
        )
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "x.sql"
            path.write_text(sql)
            columns = sql_dump.parse_create_table_columns(path, "trainer_spell")
        self.assertEqual(columns, ("TrainerId", "SpellId"))

    def test_missing_table_raises(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "x.sql"
            path.write_text("CREATE TABLE `other` (`x` int);\n")
            with self.assertRaises(ValueError):
                sql_dump.parse_create_table_columns(path, "nonexistent")


class ReadTableStatementsTest(unittest.TestCase):
    """`read_table_statements` - the ordered INSERT/DELETE reader the prune
    pass replays (`lib/spell_tables.py`)."""

    def _events(self, sql: str, table="spell_script_names", columns=("spell_id", "ScriptName")):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "x.sql"
            path.write_text(sql, encoding="utf-8")
            return list(sql_dump.read_table_statements(path, table, columns))

    def test_reads_insert_and_composite_delete_in_file_order(self):
        events = self._events(
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES (1, 'a'), (2, 'b');\n"
            "DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN ((1, 'a'), (2, 'b'));\n"
        )
        self.assertEqual([k for k, _ in events], ["insert", "delete"])
        self.assertEqual(events[0][1], [{"spell_id": 1, "ScriptName": "a"},
                                        {"spell_id": 2, "ScriptName": "b"}])
        self.assertEqual(events[1][1], (("spell_id", "ScriptName"), [(1, "a"), (2, "b")]))

    def test_order_is_file_order_not_statement_type(self):
        events = self._events(
            "DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN ((9, 'z'));\n"
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES (9, 'z');\n"
        )
        self.assertEqual([k for k, _ in events], ["delete", "insert"])

    def test_single_column_delete_shapes_normalise_to_one_tuple_form(self):
        for sql, expected in (
            ("DELETE FROM `spell_proc` WHERE `SpellId` IN (7, 8);", [(7,), (8,)]),
            ("DELETE FROM `spell_proc` WHERE `SpellId` = 7;", [(7,)]),
            ("DELETE FROM `spell_proc` WHERE (`SpellId`) IN ((7));", [(7,)]),
        ):
            events = self._events(sql, table="spell_proc", columns=("SpellId",))
            self.assertEqual(len(events), 1, sql)
            self.assertEqual(events[0][0], "delete", sql)
            self.assertEqual(events[0][1][1], expected, sql)

    def test_other_tables_are_ignored(self):
        events = self._events(
            "INSERT INTO `other_table` (`a`) VALUES (1);\n"
            "DELETE FROM `other_table` WHERE `a` = 1;\n"
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES (3, 'c');\n"
        )
        self.assertEqual([k for k, _ in events], ["insert"])
        self.assertEqual(events[0][1], [{"spell_id": 3, "ScriptName": "c"}])

    def test_unrecognized_delete_shape_is_flagged_not_silently_skipped(self):
        events = self._events("DELETE FROM `spell_script_names` WHERE `ScriptName` LIKE 'x%';\n")
        self.assertEqual([k for k, _ in events], ["delete_unparsed"])

    def test_negative_and_quoted_values_round_trip(self):
        events = self._events(
            "DELETE FROM `spell_proc` WHERE (`SpellId`) IN ((-47516), (-14531));",
            table="spell_proc", columns=("SpellId",))
        self.assertEqual(events[0][1][1], [(-47516,), (-14531,)])


if __name__ == "__main__":
    unittest.main()
