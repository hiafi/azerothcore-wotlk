"""
`budget_overlay`'s schema evolution reads `ALTER TABLE` statements to the statement's own `;`. A `;` inside a quoted
column COMMENT used to end the statement early (a regex to the first `;`), which left an unterminated string and
crashed the replay with an IndexError in `sql_dump._read_string` (level 60 secondary curve, LS1b).

    apps/dbc-tools/.venv/bin/python3 -m pytest -q apps/item-tools/tests/test_budget_overlay_alter.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from item_lib import budget_overlay, replay  # noqa: E402

SQL = """
ALTER TABLE `t_one`
  ADD COLUMN `a` tinyint unsigned NOT NULL DEFAULT '3'
    COMMENT '0 = off (x); 1 = on; it''s fine'
    AFTER `id`,
  ADD COLUMN `b` int NOT NULL DEFAULT '7' COMMENT "double; quoted";

ALTER TABLE `t_two` ADD COLUMN `c` float NOT NULL DEFAULT '0.5' COMMENT 'back\\'slash; escaped';
UPDATE `t_one` SET `a` = 1 WHERE `id` = 2;
ALTER TABLE `t_two` DROP COLUMN `d`;
"""


class AlterTableParseTest(unittest.TestCase):
    def test_statements_end_at_their_own_semicolon(self):
        statements = list(budget_overlay._alter_table_statements(SQL))
        self.assertEqual([table for table, _ in statements], ["t_one", "t_two", "t_two"])
        self.assertIn("'0 = off (x); 1 = on; it''s fine'", statements[0][1])
        self.assertIn('"double; quoted"', statements[0][1])
        self.assertIn("'back\\'slash; escaped'", statements[1][1])
        self.assertNotIn("UPDATE", statements[1][1])
        self.assertEqual(statements[2][1].strip(), "DROP COLUMN `d`")

    def test_clauses_split_and_read_their_defaults(self):
        table, clauses = next(budget_overlay._alter_table_statements(SQL))
        parts = [c.strip() for c in replay.sql_dump._split_top_level_commas(clauses)]
        self.assertEqual(len(parts), 2)
        first = budget_overlay._ADD_COLUMN_RE.match(parts[0])
        self.assertEqual((first.group("col"), first.group("after")), ("a", "id"))
        self.assertEqual(budget_overlay._parse_default(parts[0]), 3)
        self.assertEqual(budget_overlay._ADD_COLUMN_RE.match(parts[1]).group("col"), "b")
        self.assertEqual(budget_overlay._parse_default(parts[1]), 7)

    def test_no_terminator_runs_to_the_end(self):
        statements = list(budget_overlay._alter_table_statements("ALTER TABLE `t` ADD COLUMN `x` int COMMENT 'a;b'"))
        self.assertEqual(statements, [("t", "ADD COLUMN `x` int COMMENT 'a;b'")])


if __name__ == "__main__":
    unittest.main()
