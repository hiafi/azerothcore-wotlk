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


if __name__ == "__main__":
    unittest.main()
