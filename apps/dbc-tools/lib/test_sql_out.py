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

import re
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


# WP-T Gate: "rendered SQL matches what apps/codestyle/codestyle-sql.py enforces". That script
# can't be imported directly in a test - it runs `git fetch origin Playerbot` and a real
# directory walk as an unconditional module-level side effect (no `if __name__ == "__main__"`
# guard) - so this re-checks the specific invariants it enforces that matter for generated
# content: backticks, a semicolon on every statement, no double semicolons, a DELETE immediately
# before its INSERT, no trailing whitespace/tabs, no multiple blank lines.
def _assert_codestyle_shape(test: unittest.TestCase, text: str) -> None:
    lines = text.splitlines()
    test.assertNotIn(";;", text, "double semicolon")
    previous_nonblank = ""
    for line in lines:
        test.assertEqual(line, line.rstrip(), f"trailing whitespace: {line!r}")
        test.assertNotIn("\t", line, f"tab found: {line!r}")
        if "INSERT" in line and not line.strip().startswith("--"):
            test.assertIn("DELETE", previous_nonblank, f"no DELETE immediately before INSERT: {line!r}")
        if line.strip():
            previous_nonblank = line
    blank_run = 0
    for line in lines:
        blank_run = blank_run + 1 if not line.strip() else 0
        test.assertLess(blank_run, 2, "multiple consecutive blank lines")
    for statement in text.split(";"):
        statement = statement.strip()
        if not statement or statement.startswith("--"):
            continue
        m = re.match(r"(DELETE FROM|INSERT INTO|UPDATE)\s+(\S+)", statement, re.IGNORECASE)
        if m:
            test.assertTrue(m.group(2).startswith("`") and "`" in m.group(2)[1:], f"unbacktick-quoted table: {statement[:60]!r}")


class WpTCodestyleShapeTest(unittest.TestCase):
    """WP-T's own new tables (declared + removal) through the same render functions every other
    table already uses - see _assert_codestyle_shape's docstring for why this doesn't just call
    apps/codestyle/codestyle-sql.py directly."""

    def test_declared_table_block(self):
        rows = [
            {"spell_trigger": 200326, "spell_effect": 57865, "type": 2, "comment": "x -> y"},
            {"spell_trigger": -200326, "spell_effect": -57865, "type": 0, "comment": "a -> b"},
        ]
        block = sql_out.render_generic_table_block(
            "spell_linked_spell", ("spell_trigger", "spell_effect", "type", "comment"),
            ("spell_trigger", "spell_effect", "type"), rows,
        )
        _assert_codestyle_shape(self, block + "\n")

    def test_removal_block_with_comment(self):
        block = sql_out.render_delete_only_block(
            "spell_script_names", ("spell_id", "ScriptName"), [(69366, "spell_dru_moonkin_form_passive")],
            "-- Declared removal: 1 spell_script_names row(s) no longer wanted.",
        )
        _assert_codestyle_shape(self, block + "\n")

    def test_full_pending_file_shape(self):
        declared = sql_out.render_generic_table_block(
            "spell_custom_attr", ("spell_id", "attributes"), ("spell_id",), [{"spell_id": 200425, "attributes": 1}],
        )
        removal = sql_out.render_delete_only_block(
            "trainer_spell", ("TrainerId", "SpellId"), [(212, 50464)], "-- Declared removal: retired.",
        )
        text = "-- Generated by apps/dbc-tools/generate.py\n\n" + "\n\n".join([declared, removal]) + "\n"
        _assert_codestyle_shape(self, text)


if __name__ == "__main__":
    unittest.main()
