"""
Regression tests for the dbc-replay-fix review (`.agents/plans/dbc-replay-fix/dbc-replay-fix.REVIEW.md`): each test
names its finding (S1-S6, N1-N5, N9) and replays the reviewer's repro where there is one. The replay must do what
MySQL does, or record the statement as skipped; it must never differ silently.

    apps/dbc-tools/.venv/bin/python3 lib/test_sql_replay_review.py   (from apps/dbc-tools)
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import sql_dump, sqlcorpus, trainer_state  # noqa: E402
from lib.dbcfmt import DbcTable  # noqa: E402

COLS = ("a", "b", "c")
KEY = ("a", "b")
INTS = frozenset(COLS)
KEYED = DbcTable(name="T", dbc_filename="", sql_table="t", fmt="nis", columns=("ID", "a", "s"))
KEYED_BASE = "INSERT INTO `t` (`ID`,`a`,`s`) VALUES (1,5,'x'),(5,1,'y'),(7,7,NULL);\n"


def composite(sql: str, defaults=None, int_columns=INTS) -> tuple[list[tuple], list[str]]:
    """`(rows as sorted (a, b, c) tuples, skip reasons)` after replaying `sql` onto an empty `t`."""
    sqlcorpus.SKIPS.clear()
    rows: dict = {}
    sql_dump.apply_composite_key_statements(
        rows, COLS, KEY, "t", sql, defaults=defaults, source="t.sql", int_columns=int_columns,
    )
    for key, row in rows.items():  # the replay files every row under the key its values give it
        assert key == tuple(row.get(c) for c in KEY), (key, row)
    return sorted((tuple(r.get(c) for c in COLS) for r in rows.values()), key=repr), _reasons()


def keyed(sql: str) -> tuple[dict, list[str]]:
    sqlcorpus.SKIPS.clear()
    rows: dict = {}
    sql_dump.apply_statements(rows, KEYED, KEYED_BASE + sql, source="t.sql")
    return {k: (r["a"], r["s"]) for k, r in sorted(rows.items())}, _reasons()


def _reasons() -> list[str]:
    return [s.reason for s in sqlcorpus.SKIPS.entries]


class S1RekeyTest(unittest.TestCase):
    """An UPDATE that assigns a key column moves the row to its new key (probe1 cases 1, 1b, 16)."""

    def test_rekey_then_insert_the_old_key(self):
        self.assertEqual(composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,10),(1,2,20);\n"
            "UPDATE `t` SET `b` = 3 WHERE `a` = 1 AND `b` = 2;\n"
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,2,99);\n"
        ), ([(1, 1, 10), (1, 2, 99), (1, 3, 20)], []))

    def test_rekey_then_insert_ignore_the_old_key(self):
        self.assertEqual(composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,2,20);\n"
            "UPDATE `t` SET `b` = 3 WHERE `a` = 1 AND `b` = 2;\n"
            "INSERT IGNORE INTO `t` (`a`,`b`,`c`) VALUES (1,2,99);\n"
        ), ([(1, 2, 99), (1, 3, 20)], []))

    def test_rekey_by_predicate_and_without_where_then_delete_by_the_new_key(self):
        self.assertEqual(composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,2,20),(2,2,30);\n"
            "UPDATE `t` SET `b` = `b` + 10 WHERE `a` IN (1);\n"
            "UPDATE `t` SET `a` = `a` + 100;\n"
            "DELETE FROM `t` WHERE `a` = 101 AND `b` = 12;\n"
        ), ([(102, 2, 30)], []))

    def test_a_key_collision_refuses_the_statement_like_mysql(self):
        rows, reasons = composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,10),(1,2,20);\n"
            "UPDATE `t` SET `b` = 1 WHERE `a` = 1 AND `b` = 2;\n"
        )
        self.assertEqual(rows, [(1, 1, 10), (1, 2, 20)])
        self.assertEqual(len(reasons), 1)
        self.assertIn("two rows one key", reasons[0])

    def test_keyed_replay_moves_the_row_too(self):
        # probe2: `UPDATE t SET ID = 2 WHERE ID = 1` then an INSERT of 1 is a new row.
        rows, reasons = keyed(
            "UPDATE `t` SET `ID` = 2 WHERE `ID` = 1;\nINSERT INTO `t` (`ID`,`a`,`s`) VALUES (1,0,'n');"
        )
        self.assertEqual((rows, reasons), ({1: (0, "n"), 2: (5, "x"), 5: (1, "y"), 7: (7, "")}, []))


class _MinimalRows:
    """Only what `apply_statements` promises to use (`stale_overlay._Recorder`'s surface)."""

    def __init__(self):
        self.data: dict = {}

    def __setitem__(self, key, value):
        self.data[key] = value

    def pop(self, key, default=None):
        return self.data.pop(key, default)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def items(self):
        return self.data.items()

    def clear(self):
        self.data.clear()


class KeyedRowsInterfaceTest(unittest.TestCase):
    def test_moves_and_no_where_updates_use_only_the_documented_interface(self):
        rows = _MinimalRows()
        sql_dump.apply_statements(
            rows, KEYED, KEYED_BASE + "UPDATE `t` SET `a` = 0;\nUPDATE `t` SET `ID` = 2 WHERE `ID` = 1;\n",
        )
        self.assertEqual({k: r["a"] for k, r in rows.data.items()}, {2: 0, 5: 0, 7: 0})


class S2KeyedNonKeyWhereTest(unittest.TestCase):
    """A single-condition WHERE on a non-key column is a filter, not the row id (probe2)."""

    def test_delete_and_update_on_a_non_key_column(self):
        for sql, want in (
            ("DELETE FROM `t` WHERE `a` = 5;", {5: (1, "y"), 7: (7, "")}),
            ("DELETE FROM `t` WHERE `a` IN (5);", {5: (1, "y"), 7: (7, "")}),
            ("DELETE FROM `t` WHERE `a` BETWEEN 5 AND 5;", {5: (1, "y"), 7: (7, "")}),
            ("UPDATE `t` SET `s` = 'z' WHERE `a` = 5;", {1: (5, "z"), 5: (1, "y"), 7: (7, "")}),
            ("UPDATE `t` SET `s` = 'z' WHERE `a` IN (5, 7);", {1: (5, "z"), 5: (1, "y"), 7: (7, "z")}),
        ):
            with self.subTest(sql=sql):
                self.assertEqual(keyed(sql), (want, []))

    def test_the_same_shapes_on_the_key_still_name_the_row(self):
        self.assertEqual(keyed("DELETE FROM `t` WHERE `ID` = 5;")[0], {1: (5, "x"), 7: (7, "")})
        self.assertEqual(keyed("DELETE FROM `t` WHERE `ID` BETWEEN 5 AND 7;")[0], {1: (5, "x")})


class S3KeyedGuardTest(unittest.TestCase):
    """Every equality of an AND chain holds or the keyed UPDATE does nothing, like an `IS NULL` guard (probe2)."""

    def test_a_failing_equality_guard_leaves_the_row(self):
        self.assertEqual(keyed("UPDATE `t` SET `a` = 99 WHERE `ID` = 1 AND `a` = 6;")[0][1], (5, "x"))
        self.assertEqual(keyed("UPDATE `t` SET `a` = 99 WHERE `ID` = 1 AND `s` IS NULL;")[0][1], (5, "x"))

    def test_a_holding_guard_applies(self):
        self.assertEqual(keyed("UPDATE `t` SET `a` = 99 WHERE `ID` = 1 AND `a` = 5;")[0][1], (99, "x"))
        self.assertEqual(keyed("UPDATE `t` SET `a` = 99 WHERE `ID` = 1 AND `s` = 'X';")[0][1], (99, "x"))


class S4OmittedColumnExpressionTest(unittest.TestCase):
    """An expression on a column the INSERT left out reads the schema default, or is recorded (probe4)."""

    def test_the_schema_default_is_read(self):
        self.assertEqual(composite(
            "INSERT INTO `t` (`a`,`b`) VALUES (1,1);\n"
            "UPDATE `t` SET `c` = `c` | 4 WHERE `a` = 1 AND `b` = 1;\n"
            "UPDATE `t` SET `c` = `c` + 1;\n",
            defaults={"a": 0, "b": 0, "c": 0},
        ), ([(1, 1, 5)], []))

    def test_without_a_default_it_is_recorded(self):
        rows, reasons = composite(
            "INSERT INTO `t` (`a`,`b`) VALUES (1,1);\nUPDATE `t` SET `c` = `c` | 4 WHERE `a` = 1 AND `b` = 1;\n",
        )
        self.assertEqual(rows, [(1, 1, None)])
        self.assertEqual(len(reasons), 1)
        self.assertIn("assignment(s) not applied", reasons[0])

    def test_a_column_the_table_does_not_have_is_not_replayed(self):
        # `mechanic_immune_mask` style: a column upstream dropped later; nothing the replay holds can be wrong.
        rows, reasons = composite(
            "INSERT INTO `t` (`a`,`b`) VALUES (1,1);\nUPDATE `t` SET `gone` = `gone` | 4 WHERE `a` = 1 AND `b` = 1;\n",
            defaults={"a": 0, "b": 0, "c": 0},
        )
        self.assertEqual((rows, reasons), ([(1, 1, None)], []))


class S5UpsertTest(unittest.TestCase):
    """`ON DUPLICATE KEY UPDATE` changes only the clause's columns of an existing row (probe1 cases 4, 4b; probe2)."""

    def test_partial_upsert_keeps_the_other_columns(self):
        self.assertEqual(composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,10);\n"
            "INSERT INTO `t` (`a`,`b`) VALUES (1,1) ON DUPLICATE KEY UPDATE `b` = VALUES(`b`);\n"
        ), ([(1, 1, 10)], []))

    def test_expression_reads_the_existing_row(self):
        self.assertEqual(composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,10);\n"
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,50), (2,2,7) ON DUPLICATE KEY UPDATE `c` = `c` + 1;\n"
        ), ([(1, 1, 11), (2, 2, 7)], []))

    def test_values_of_an_omitted_column_is_its_default_and_a_full_upsert_replaces(self):
        self.assertEqual(composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,10), (2,2,20);\n"
            "INSERT INTO `t` (`a`,`b`) VALUES (1,1) ON DUPLICATE KEY UPDATE `c` = VALUES(`c`);\n"
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (2,2,21) ON DUPLICATE KEY UPDATE `c` = VALUES(`c`);\n",
            defaults={"c": 3},
        ), ([(1, 1, 3), (2, 2, 21)], []))

    def test_an_unreadable_clause_is_recorded(self):
        rows, reasons = composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,10);\n"
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,50) ON DUPLICATE KEY UPDATE `c` = GREATEST(`c`, 3);\n"
        )
        self.assertEqual(rows, [(1, 1, 10)])
        self.assertEqual(len(reasons), 1)

    def test_keyed_partial_upsert(self):
        self.assertEqual(
            keyed("INSERT INTO `t` (`ID`,`a`) VALUES (1,8) ON DUPLICATE KEY UPDATE `a` = VALUES(`a`);"),
            ({1: (8, "x"), 5: (1, "y"), 7: (7, "")}, []),
        )


class S6InsertSelectTest(unittest.TestCase):
    """`INSERT ... SELECT` / `INSERT ... SET` is recorded as skipped (probe5)."""

    def test_composite_keyed_and_union_readers_record_it(self):
        for sql in (
            "INSERT INTO `t` (`a`,`b`,`c`) SELECT `a`, 2, `c` FROM `t` WHERE `b` = 1;\n",
            "INSERT IGNORE INTO `t` SELECT * FROM `t2`;\n",
            "INSERT INTO `t` (`a`, `b`, `c`) (SELECT 1, 2, 3);\n",
            "REPLACE INTO `t` SET `a` = 1, `b` = 2;\n",
        ):
            with self.subTest(sql=sql):
                self.assertEqual(composite(sql)[1], [sql_dump._INSERT_QUERY_REASON])
                self.assertEqual(keyed(sql.replace("`b`", "`ID`"))[1], [sql_dump._INSERT_QUERY_REASON])

    def test_union_reader(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.sql"
            path.write_text("INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,1);\nINSERT INTO `t` SELECT 2, 2, 2;\n")
            sqlcorpus.SKIPS.clear()
            rows = sql_dump.read_table_rows(path, "t", COLS, tolerant=True)
        self.assertEqual(len(rows), 1)
        self.assertEqual(_reasons(), [sql_dump._INSERT_QUERY_REASON])

    def test_a_values_insert_is_still_an_insert(self):
        self.assertEqual(composite("INSERT INTO `t` (`a`,`b`,`c`) VALUE (1,1,1);\n"), ([(1, 1, 1)], []))


class N1BlockCommentTest(unittest.TestCase):
    def test_a_head_inside_a_block_comment_is_not_run(self):
        self.assertEqual(composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,10);\n/*\nDELETE FROM `t` WHERE `a` = 1;\n*/\n"
        ), ([(1, 1, 10)], []))

    def test_after_the_comment_closes_and_inside_a_string(self):
        self.assertEqual(composite(
            "/* old: DELETE FROM `t` WHERE `a` = 9; */\n"
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,10), (2,2,20);\n"
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (3,3,'a /* not a comment');\n"
            "DELETE FROM `t` WHERE `a` = 1;\n"
        ), ([(2, 2, 20), (3, 3, "a /* not a comment")], []))

    def test_an_executable_comment_is_not_a_comment(self):
        # MySQL runs `/*! ... */`: its statement is not passed over (here the replay cannot read it, and says so).
        rows, reasons = composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (2,2,20);\n/*!40000 DELETE FROM `t` WHERE `a` = 2 */;\n"
        )
        self.assertEqual(len(reasons), 1)

    def test_keyed_and_invisible_scan(self):
        self.assertEqual(keyed("/* DELETE FROM `t` WHERE `ID` = 1; */")[0][1], (5, "x"))
        self.assertEqual(trainer_state.invisible_statements("t", "/*\nDELETE FROM t WHERE a = 1;\n*/\n"), [])


class N2QuotedKeyTest(unittest.TestCase):
    def test_a_quoted_numeric_key_is_the_integer(self):
        self.assertEqual(
            composite("INSERT INTO `t` (`a`,`b`,`c`) VALUES ('5','1',10);\nDELETE FROM `t` WHERE `a` = 5;"), ([], []),
        )
        self.assertEqual(composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES ('5','1',10);\n"
            "DELETE FROM `t` WHERE `a` = 5 AND `b` = 1;\n"
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (5,1,11);\n"
        ), ([(5, 1, 11)], []))

    def test_a_quoted_pin_matches_by_value(self):
        self.assertEqual(composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,10);\nUPDATE `t` SET `c` = 11 WHERE `a` = '1' AND `b` = 1;\n"
        ), ([(1, 1, 11)], []))

    def test_a_quoted_key_without_known_types_still_matches_a_numeric_delete(self):
        rows, _ = composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES ('5','1',10);\nDELETE FROM `t` WHERE `a` = 5;", int_columns=None,
        )
        self.assertEqual(rows, [])


class N3EqualsNullTest(unittest.TestCase):
    def test_equals_null_is_never_true(self):
        self.assertEqual(composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,NULL);\n"
            "UPDATE `t` SET `c` = 7 WHERE `a` = 1 AND `b` = 1 AND `c` = NULL;\n"
        ), ([(1, 1, None)], []))
        self.assertEqual(keyed("UPDATE `t` SET `a` = 9 WHERE `ID` = 7 AND `s` = NULL;")[0][7], (7, ""))


class N4IntegerRoundingTest(unittest.TestCase):
    def test_arithmetic_on_an_integer_column_is_rounded_like_mysql(self):
        self.assertEqual(composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,12345), (1,2,63), (1,3,62);\n"
            "UPDATE `t` SET `c` = `c` * 0.2;\n"
        ), ([(1, 1, 2469), (1, 2, 13), (1, 3, 12)], []))

    def test_a_literal_and_a_float_column(self):
        self.assertEqual(composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,0);\nUPDATE `t` SET `c` = 2.5 WHERE `a` = 1 AND `b` = 1;\n",
        )[0], [(1, 1, 3)])
        self.assertEqual(composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,0);\nUPDATE `t` SET `c` = 2.5 WHERE `a` = 1 AND `b` = 1;\n",
            int_columns=frozenset(KEY),
        )[0], [(1, 1, 2.5)])

    def test_int_value(self):
        self.assertEqual([sql_dump._int_value(v) for v in (2469.4, 2.5, -2.5, 12.6, 3, "x", 0.49999999999)],
                         [2469, 3, -3, 13, 3, "x", 0])

    def test_parse_create_table_int_columns(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.sql"
            path.write_text("CREATE TABLE `t` (\n  `a` int unsigned NOT NULL,\n  `b` tinyint NOT NULL DEFAULT '0',\n"
                            "  `c` float NOT NULL DEFAULT '1',\n  `d` varchar(5) DEFAULT NULL\n) ENGINE=InnoDB;\n")
            self.assertEqual(sql_dump.parse_create_table_int_columns(path, "t"), {"a", "b"})


class N5ExponentBoundTest(unittest.TestCase):
    def test_between_bounds_with_an_exponent(self):
        predicate = sql_dump.parse_where_predicate("`entry` = 1 AND `dmg_min1` BETWEEN 5e-05 AND 0.02005")
        self.assertIsNotNone(predicate)
        self.assertTrue(predicate({"entry": 1, "dmg_min1": 0.01005}))
        self.assertFalse(predicate({"entry": 1, "dmg_min1": 0.03}))


class N9LowercaseKeywordTest(unittest.TestCase):
    def test_null_true_false_in_any_case(self):
        self.assertEqual(composite("INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,null), (1,2,true), (1,3,False);\n"),
                         ([(1, 1, None), (1, 2, 1), (1, 3, 0)], []))
        self.assertEqual(composite(
            "INSERT INTO `t` (`a`,`b`,`c`) VALUES (1,1,5);\nUPDATE `t` SET `c` = null WHERE `a` = 1 AND `b` = 1;\n"
        )[0], [(1, 1, None)])


class AfterStatementTest(unittest.TestCase):
    def test_called_once_per_statement_on_the_table(self):
        seen = []
        rows: dict = {}
        sql_dump.apply_composite_key_statements(
            rows, COLS, KEY, "t",
            "SET @X := 1;\nINSERT INTO `t` (`a`,`b`,`c`) VALUES (@X,1,1);\nUPDATE `u` SET `c` = 2;\n"
            "UPDATE `t` SET `c` = 2;\nDELETE FROM `t` WHERE `a` = 9 LIMIT 1;\n",
            after_statement=lambda: seen.append(sorted(r["c"] for r in rows.values())),
        )
        self.assertEqual(seen, [[1], [2], [2]])  # the INSERT, the UPDATE, the skipped DELETE; not SET, not `u`


if __name__ == "__main__":
    unittest.main()
