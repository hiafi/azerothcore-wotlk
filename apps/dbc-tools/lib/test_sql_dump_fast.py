"""The fast paths in `sql_dump` / `sqlcorpus` must give exactly the answer of the code they replace.

Each test pairs a fast path with its reference: the regex tuple parser with the character-level one
(`_read_tuples(fast=False)`), the composite-key index with a full scan (`_KeyIndex.lookup` patched to give up), the
statement-head index with the regex search loop (a plain `str` instead of a corpus `SqlText`), the lowercase head
scan with a plain `finditer`. Run: python3 -m pytest apps/dbc-tools/lib/test_sql_dump_fast.py
"""

from __future__ import annotations

import random
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import sql_dump, sqlcorpus  # noqa: E402
from lib.dbcfmt import DbcTable  # noqa: E402


def _parse(body: str, fast: bool):
    try:
        return sql_dump._read_tuples(body, 0, fast=fast)
    except Exception as exc:  # the error is part of the contract: both parsers must fail the same way
        return ("ERR", type(exc).__name__, str(exc))


def _typed(value):
    if isinstance(value, list):
        return [_typed(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_typed(v) for v in value)
    return (type(value).__name__, value)


class TupleParserTest(unittest.TestCase):
    CASES = [
        "(1, 'a', NULL, 2.5, -3, 1e5, 1E-3, 0.0);",
        "(1,2,3),(4,5,6),\n(7,8,9);",
        "('it''s', 'back\\\\slash', 'q\\'uote', 'tab\\there', 'pct\\%x', 'under\\_y', 'nl\\nx', 'z\\Zq', 'nul\\0');",
        "('multi\nline', 'comma, inside', 'paren ) inside', 'NULL', '');",
        "(1, -- comment\n 2),(3, 4);",
        "(1, 2), -- between tuples\n(3, 4);",
        "(0x1F, 5);",
        "(@var, @var + 2, 3);",
        "(NULL, null);",
        "(1 2);",
        "(1.,2);",
        "(.5, 1);",
        "('unterminated, 2);",
        "('a''', 'b''''c');",
        "(1,\t2 ,\r\n3 );",
        "(1, 2);",  # a non-breaking space is not whitespace to the parser
        "(+5, 2);",
        "(1_000, 2);",
        "(NULLx, 2);",
        "('é', 'ü', '日本');",
        "(1, 2) ON DUPLICATE KEY UPDATE `a` = VALUES(`a`);",
        "(99999999999999999999, -0, 007);",
        "('\\\\''', 1);",  # backslash-backslash then a doubled quote
        "(1, 'a'\n,2);",
    ]

    def test_fast_matches_reference(self):
        for body in self.CASES:
            with self.subTest(body=body):
                variables = {"@var": 7}
                fast = self._both(body, variables, True)
                slow = self._both(body, variables, False)
                self.assertEqual(_typed(fast), _typed(slow))

    @staticmethod
    def _both(body, variables, fast):
        try:
            return sql_dump._read_tuples(body, 0, variables, fast=fast)
        except Exception as exc:
            return ("ERR", type(exc).__name__, str(exc))

    def test_random_literals(self):
        rng = random.Random(7)
        alphabet = ["a", "b", " ", ",", "(", ")", "'", "''", "\\", "\\'", "\\n", "\\%", "-", "NULL", "é", "\n", ";"]

        def literal():
            kind = rng.random()
            if kind < 0.3:
                return str(rng.randint(-100000, 100000))
            if kind < 0.4:
                return repr(round(rng.uniform(-50, 50), rng.randint(1, 6)))
            if kind < 0.45:
                return "NULL"
            body = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 12)))
            return "'" + body.replace("\\", "\\\\").replace("'", "''") + "'" if rng.random() < 0.6 else "'" + body + "'"

        for _ in range(400):
            tuples = ",".join(
                "(" + ", ".join(literal() for _ in range(rng.randint(1, 8))) + ")" for _ in range(rng.randint(1, 4))
            )
            body = tuples + ";"
            self.assertEqual(_typed(_parse(body, True)), _typed(_parse(body, False)), body)


COMPOSITE_COLUMNS = ("a", "b", "v", "w")
COMPOSITE_KEYS = ("a", "b")


def _composite_script(rng: random.Random) -> str:
    out = []
    for _ in range(rng.randint(8, 25)):
        a, b = rng.randint(1, 4), rng.randint(1, 3)
        kind = rng.random()
        if kind < 0.3:
            out.append(
                f"INSERT INTO `t` (`a`, `b`, `v`, `w`) VALUES ({a}, {b}, {rng.randint(0, 9)}, {rng.randint(0, 9)});"
            )
        elif kind < 0.45:
            out.append(f"UPDATE `t` SET `v` = {rng.randint(10, 99)} WHERE `a` = {a} AND `b` = {b};")
        elif kind < 0.55:
            out.append(f"UPDATE `t` SET `v` = `v` | {rng.choice([1, 2, 4])} WHERE `a` = {a} AND `b` = {b};")
        elif kind < 0.65:
            out.append(f"UPDATE `t` SET `w` = {rng.randint(10, 99)} WHERE `a` IN ({a}, {a % 4 + 1}) AND `b` = {b};")
        elif kind < 0.72:
            out.append(
                f"UPDATE `t` SET `w` = 5 WHERE (`a` = {a} AND `b` = {b}) OR (`a` = {a % 4 + 1} AND `b` IN (1, 2));"
            )
        elif kind < 0.78:
            out.append(f"UPDATE `t` SET `a` = {rng.randint(1, 4)} WHERE `a` = {a} AND `b` = {b};")  # re-keys content
        elif kind < 0.84:
            out.append(f"UPDATE `t` SET `v` = 1 WHERE `a` = {a} AND `b` = {b} AND `w` = {rng.randint(0, 9)};")
        elif kind < 0.88:
            out.append(f"UPDATE `t` SET `v` = 2 WHERE `a` BETWEEN 1 AND {a};")
        elif kind < 0.92:
            out.append(f"UPDATE `t` SET `v` = 3 WHERE `a` = {a};")  # leaves a key column free: scans
        elif kind < 0.96:
            out.append(f"DELETE FROM `t` WHERE (`a`, `b`) IN (({a}, {b}));")
        else:
            out.append(f"DELETE FROM `t` WHERE `a` = {a};")
    return "\n".join(out)


class CompositeIndexTest(unittest.TestCase):
    def _replay(self, text: str, use_index: bool):
        rows: dict = {}
        if use_index:
            sql_dump.apply_composite_key_statements(rows, COMPOSITE_COLUMNS, COMPOSITE_KEYS, "t", text)
        else:
            with mock.patch.object(sql_dump._KeyIndex, "lookup", lambda self, key: None), \
                    mock.patch.object(sql_dump._KeyIndex, "pinned_rows", lambda self, pins: None):
                sql_dump.apply_composite_key_statements(rows, COMPOSITE_COLUMNS, COMPOSITE_KEYS, "t", text)
        return rows

    def test_index_matches_scan_on_random_histories(self):
        rng = random.Random(11)
        for n in range(300):
            script = _composite_script(rng)
            with self.subTest(n=n):
                self.assertEqual(self._replay(script, True), self._replay(script, False), script)

    def test_index_matches_scan_with_preloaded_rows_missing_a_key_column(self):
        rows_a = {(1, 1): {"a": 1, "v": 0}, (2, 1): {"a": 2, "b": 1, "v": 0}}
        rows_b = {k: dict(v) for k, v in rows_a.items()}
        text = "UPDATE `t` SET `v` = 9 WHERE `a` = 1 AND `b` = 1;\nUPDATE `t` SET `v` = 8 WHERE `a` = 2 AND `b` = 1;"
        sql_dump.apply_composite_key_statements(rows_a, COMPOSITE_COLUMNS, COMPOSITE_KEYS, "t", text)
        with mock.patch.object(sql_dump._KeyIndex, "lookup", lambda self, key: None):
            sql_dump.apply_composite_key_statements(rows_b, COMPOSITE_COLUMNS, COMPOSITE_KEYS, "t", text)
        self.assertEqual(rows_a, rows_b)
        self.assertEqual(rows_a[(1, 1)]["v"], 9)

    def test_prefix_delete_matches_one_pass_per_value(self):
        rows = {(a, b): {"a": a, "b": b} for a in range(1, 6) for b in range(1, 4)}
        sql_dump.apply_composite_key_statements(
            rows, COMPOSITE_COLUMNS, COMPOSITE_KEYS, "t", "DELETE FROM `t` WHERE `a` IN (2, 4);"
        )
        self.assertEqual({a for a, _b in rows}, {1, 3, 5})


WIDGET = DbcTable(
    name="Widget", dbc_filename="Widget.dbc", sql_table="widget_dbc", fmt="nsi", columns=("ID", "Name", "Value"),
)

SAMPLE_SQL = """-- header
INSERT INTO `other` VALUES (1, 'x');
SET @base := 100;
INSERT INTO `widget_dbc` (`ID`, `Name`, `Value`) VALUES (1, 'one', 10), (2, NULL, 20);
insert into `widget_dbc` values (3, 'three', 30);
UPDATE `widget_dbc` SET `Value` = 99 WHERE `ID` = 1;
update `other` set `a` = 1 where `id` = 2;
DELETE FROM `widget_dbc` WHERE `ID` IN (2);
-- INSERT INTO `widget_dbc` VALUES (7, 'commented', 70);
REPLACE INTO `widget_dbc` VALUES (4, 'four', 40);
DELETE FROM `other` WHERE `id` = 1;
INSERT INTO `widget_dbc` (`ID`, `Name`, `Value`) VALUES (@base + 5, 'var', 50);
UPDATE `widget_dbc` SET `Name` = NULL WHERE `ID` = 3;
"""


class HeadIndexTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "sample.sql"
        self.path.write_text(SAMPLE_SQL, encoding="utf-8")
        sqlcorpus.activate(None, "test")
        self.addCleanup(sqlcorpus.deactivate)

    def test_replay_on_corpus_text_matches_plain_text(self):
        corpus_text = sqlcorpus.read_text(self.path)
        self.assertIsInstance(corpus_text, sqlcorpus.SqlText)
        plain = str(corpus_text)
        rows_a: dict = {}
        rows_b: dict = {}
        sql_dump.apply_statements(rows_a, WIDGET, corpus_text)
        sql_dump.apply_statements(rows_b, WIDGET, plain)
        self.assertEqual(rows_a, rows_b)
        self.assertEqual(set(rows_a), {1, 3, 4, 7, 105})  # a commented-out INSERT still replays, as before

    def test_read_functions_match_on_corpus_text(self):
        for fn in (
            lambda p: sql_dump.read_table_rows(p, "widget_dbc", ("ID", "Name", "Value")),
            lambda p: list(sql_dump.read_table_statements(p, "widget_dbc", ("ID", "Name", "Value"))),
            lambda p: sql_dump.read_table_dump(p, WIDGET),
        ):
            from_corpus = self._capture(fn)
            sqlcorpus.deactivate()
            plain = self._capture(fn)
            sqlcorpus.activate(None, "test")
            self.assertEqual(from_corpus, plain)

    def _capture(self, fn):
        try:
            return fn(self.path)
        except Exception as exc:  # a file the plain reader rejects must be rejected the same way
            return ("ERR", type(exc).__name__, str(exc))

    def test_composite_replay_matches_on_corpus_text(self):
        corpus_text = sqlcorpus.read_text(self.path)
        rows_a: dict = {}
        rows_b: dict = {}
        sql_dump.apply_composite_key_statements(rows_a, WIDGET.columns, ("ID",), "widget_dbc", corpus_text)
        sql_dump.apply_composite_key_statements(rows_b, WIDGET.columns, ("ID",), "widget_dbc", str(corpus_text))
        self.assertEqual(rows_a, rows_b)

    def test_corpus_text_translates_newlines_like_read_text(self):
        crlf = Path(self._tmp.name) / "crlf.sql"
        crlf.write_bytes(b"-- a\r\nINSERT INTO `widget_dbc` VALUES (1, 'x\r\ny', 2);\r\rUPDATE `t` SET `a` = 1;\r\n")
        self.assertEqual(str(sqlcorpus.read_text(crlf)), crlf.read_text(encoding="utf-8"))

    def test_mentions_matches_the_plain_check(self):
        for table in ("widget_dbc", "other", "missing", "widget"):
            for loose in (False, True):
                with self.subTest(table=table, loose=loose):
                    corpus = sqlcorpus.active()
                    cached = corpus.mentions(self.path, table, loose)
                    sqlcorpus.deactivate()
                    plain = sqlcorpus.mentions(self.path, table, loose)
                    sqlcorpus.activate(None, "test")
                    self.assertEqual(cached, plain)

    def test_head_scan_matches_regex_scan(self):
        texts = [
            SAMPLE_SQL,
            SAMPLE_SQL.upper(),
            "İnsert into `x` values (1);\nINSERT INTO `y` VALUES (2);",  # U+0130 lowercases to two characters
            "SET @a := 1; SET @b = -2;\nUPDATE `t` SET `c` = 1;\nDELETE  FROM `t`  WHERE 1;",
            "offset reset setting charset update_x `update`",
            "",
        ]
        for text in texts:
            with self.subTest(text=text[:30]):
                expected = [sqlcorpus._head_entry(m) for m in sqlcorpus.STATEMENT_HEAD_RE.finditer(text)]
                self.assertEqual(sqlcorpus.scan_heads(text), expected)

    def test_head_index_answers_like_the_regex_loop(self):
        text = sqlcorpus.read_text(self.path)
        index = text.head_index
        for pos in range(0, len(text), 7):
            for table in ("widget_dbc", "other", "none"):
                expected = None
                p = pos
                while True:
                    m = sql_dump._STATEMENT_HEAD_RE.search(str(text), p)
                    if m is None:
                        break
                    matched = m.group("ins_table") or m.group("del_table") or m.group("upd_table")
                    if matched is None or matched == table:
                        expected = m
                        break
                    p = m.end()
                got = index.first(pos, table, "IDUS")
                self.assertEqual(None if got is None else (got.start(), got.end()),
                                 None if expected is None else (expected.start(), expected.end()))


class UnescapeTest(unittest.TestCase):
    def test_token_values_match_read_value(self):
        tokens = [
            "'a'", "'it''s'", "'x\\ny'", "'p\\%q'", "'q\\_r'", "'b\\\\s'", "NULL", "5", "-5", "1.5", "2e3", "1E-2",
        ]
        for token in tokens:
            with self.subTest(token=token):
                self.assertEqual(
                    _typed(sql_dump._TokenValues()[token]), _typed(sql_dump._read_value(token + ")", 0)[0])
                )


if __name__ == "__main__":
    unittest.main()
