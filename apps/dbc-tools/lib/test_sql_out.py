"""
Unit tests for `lib/sql_out.py`'s `render_generic_table_block` - Phase 3 of
`.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md`. The existing
`_table_block`/`emit_pending_sql` DBC-table path is exercised indirectly by
every other class-rework migration this repo has ever generated, so this
only covers the new generic (composite-key, no-reserved-range) path.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_sql_out.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import sql_out  # noqa: E402

COLUMNS = ("TrainerId", "SpellId", "ReqLevel")
KEY = ("TrainerId", "SpellId")


class RenderGenericTableBlockTest(unittest.TestCase):
    def test_empty_rows_renders_nothing(self):
        self.assertEqual(sql_out.render_generic_table_block("trainer_spell", COLUMNS, KEY, []), "")

    def test_renders_composite_key_delete_and_insert(self):
        rows = [{"TrainerId": 13, "SpellId": 200005, "ReqLevel": 20}]
        block = sql_out.render_generic_table_block("trainer_spell", COLUMNS, KEY, rows)
        self.assertIn("DELETE FROM `trainer_spell` WHERE (`TrainerId`, `SpellId`) IN ((13, 200005));", block)
        self.assertIn("INSERT INTO `trainer_spell` (`TrainerId`, `SpellId`, `ReqLevel`) VALUES", block)
        self.assertIn("(13, 200005, 20)", block)

    def test_sorted_by_key_for_reviewable_diffs(self):
        rows = [
            {"TrainerId": 13, "SpellId": 999, "ReqLevel": 1},
            {"TrainerId": 13, "SpellId": 100, "ReqLevel": 1},
        ]
        block = sql_out.render_generic_table_block("trainer_spell", COLUMNS, KEY, rows)
        self.assertLess(block.index("13, 100"), block.index("13, 999"))

    def test_never_range_deletes(self):
        # A TrainerId isn't a reserved ID block the way a minted spell/talent
        # ID is - this must never emit a BETWEEN-range delete.
        rows = [{"TrainerId": 13, "SpellId": 200005, "ReqLevel": 20}]
        block = sql_out.render_generic_table_block("trainer_spell", COLUMNS, KEY, rows)
        self.assertNotIn("BETWEEN", block)


if __name__ == "__main__":
    unittest.main()
