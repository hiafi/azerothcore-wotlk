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
            backticked = m.group(2).startswith("`") and "`" in m.group(2)[1:]
            test.assertTrue(backticked, f"unbacktick-quoted table: {statement[:60]!r}")


UPSERT_COLUMNS = ("entry", "name", "faction")
UPSERT_KEY = ("entry",)


class RenderUpsertBlockTest(unittest.TestCase):
    """`render_upsert_block` - the `creature_template` shape from
    `data/sql/updates/db_world/2026_09_23_12.sql` (a table on
    apps/codestyle/codestyle-sql.py's `not_delete` list, so it can never be
    rendered as DELETE-then-INSERT)."""

    def test_empty_rows_renders_nothing(self):
        self.assertEqual(sql_out.render_upsert_block("creature_template", UPSERT_COLUMNS, UPSERT_KEY, []), "")

    def test_renders_insert_on_duplicate_key_update_no_delete(self):
        rows = [{"entry": 300102, "name": "Tentacle of Madness", "faction": 35}]
        block = sql_out.render_upsert_block("creature_template", UPSERT_COLUMNS, UPSERT_KEY, rows)
        self.assertEqual(
            block,
            "INSERT INTO `creature_template` (`entry`, `name`, `faction`) VALUES\n"
            "(300102, 'Tentacle of Madness', 35) ON DUPLICATE KEY UPDATE "
            "`name` = VALUES(`name`), `faction` = VALUES(`faction`);",
        )
        self.assertNotIn("DELETE", block)

    def test_multiple_rows_comma_joined_on_duplicate_only_after_last(self):
        rows = [
            {"entry": 300102, "name": "Tentacle of Madness", "faction": 35},
            {"entry": 300100, "name": "Divine Star", "faction": 35},
        ]
        block = sql_out.render_upsert_block("creature_template", UPSERT_COLUMNS, UPSERT_KEY, rows)
        # Sorted by key_columns (300100 before 300102), tuples comma-joined, and the
        # ON DUPLICATE clause appears exactly once, right after the *last* tuple.
        self.assertEqual(
            block,
            "INSERT INTO `creature_template` (`entry`, `name`, `faction`) VALUES\n"
            "(300100, 'Divine Star', 35),\n"
            "(300102, 'Tentacle of Madness', 35) ON DUPLICATE KEY UPDATE "
            "`name` = VALUES(`name`), `faction` = VALUES(`faction`);",
        )
        self.assertEqual(block.count("ON DUPLICATE"), 1)

    def test_update_clause_excludes_key_columns_only(self):
        rows = [{"entry": 300102, "name": "Tentacle of Madness", "faction": 35}]
        block = sql_out.render_upsert_block("creature_template", UPSERT_COLUMNS, UPSERT_KEY, rows)
        update_clause = block.split("ON DUPLICATE KEY UPDATE ", 1)[1]
        self.assertNotIn("`entry` = VALUES(`entry`)", update_clause)
        self.assertIn("`name` = VALUES(`name`)", update_clause)
        self.assertIn("`faction` = VALUES(`faction`)", update_clause)

    def test_matches_real_migration_shape(self):
        # data/sql/updates/db_world/2026_09_23_12.sql's `creature_template` INSERT, entry 300102 -
        # same literal-rendering convention (`_sql_literal` treats "" as NULL, same as every other
        # renderer in this module), so only structural shape is asserted here.
        rows = [{"entry": 300102, "name": "Tentacle of Madness", "faction": 35}]
        block = sql_out.render_upsert_block("creature_template", UPSERT_COLUMNS, UPSERT_KEY, rows)
        self.assertTrue(block.startswith("INSERT INTO `creature_template` (`entry`, `name`, `faction`) VALUES\n"))
        self.assertTrue(block.endswith(";"))
        self.assertNotIn("DELETE", block)


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


REPO_ROOT = Path(__file__).resolve().parents[3]
LINTER_PATH = REPO_ROOT / "apps" / "codestyle" / "codestyle-sql.py"
MULTILINE_TEXT = (
    "Increases your armor by $s2. $\n"
    "Increases your resistance to spells by $s1.\n"
    "  1 point: ${($m1+$b1*1)*$<dur>} damage over $d. \n"
    "(cloth), (leather) items; Bear Form; it's \\n literally\r\n"
    "(not a tuple row);"
)


def _real_linter():
    """The real apps/codestyle/codestyle-sql.py, imported by path (its hyphen rules out `import`)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("codestyle_sql_under_test", LINTER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MultilineStringLintTest(unittest.TestCase):
    """A string with embedded line breaks (a spell Description/ToolTip) must render on ONE physical
    line, as `\\n` escapes, so apps/codestyle/codestyle-sql.py passes the generated file."""

    def test_literal_escapes_line_breaks_and_round_trips(self):
        from lib import sql_dump
        literal = sql_out._sql_literal(MULTILINE_TEXT)
        self.assertNotIn("\n", literal)
        self.assertNotIn("\r", literal)
        self.assertEqual(sql_dump._read_value(literal, 0)[0], MULTILINE_TEXT)

    def test_reader_still_parses_old_literal_multiline_form(self):
        from lib import sql_dump
        self.assertEqual(sql_dump._read_value("'a\nb'", 0)[0], "a\nb")
        self.assertEqual(sql_dump._read_value("'it''s \\\\ \\' x'", 0)[0], "it's \\ ' x")

    @unittest.skipUnless(LINTER_PATH.exists(), "linter not present")
    def test_generated_file_passes_real_linter(self):
        import tempfile
        from lib import dbcfmt
        rows = [
            {"ID": 200001, "Description_Lang_enUS": MULTILINE_TEXT, "AuraDescription_Lang_enUS": MULTILINE_TEXT},
            {"ID": 200002, "Description_Lang_enUS": "plain", "AuraDescription_Lang_enUS": None},
        ]
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "rev_1.sql"
            self.assertTrue(sql_out.emit_pending_sql(
                out, [(dbcfmt.SPELL, {"start": 200000, "end": 200099}, rows, [])], "-- header"))
            text = out.read_text(encoding="utf-8")
            self.assertIn("(cloth), (leather) items", text)  # the multi-line text really got emitted
            linter = _real_linter()
            with out.open(encoding="utf-8") as f:
                linter.multiple_blank_lines_check(f, str(out))
                linter.trailing_whitespace_check(f, str(out))
                linter.sql_check(f, str(out))
                linter.insert_delete_safety_check(f, str(out))
                linter.semicolon_check(f, str(out))
                linter.backtick_check(f, str(out))
            self.assertFalse(linter.error_handler, linter.results)

    @unittest.skipUnless(LINTER_PATH.exists(), "linter not present")
    def test_control_old_literal_newline_form_fails_real_linter(self):
        """Guards the test above against going vacuous: the pre-fix rendering must still fail."""
        import tempfile
        from lib import dbcfmt
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "rev_1.sql"
            sql_out.emit_pending_sql(
                out, [(dbcfmt.SPELL, {"start": 200000, "end": 200099},
                       [{"ID": 200001, "Description_Lang_enUS": "x"}], [])], "-- header")
            out.write_text(out.read_text(encoding="utf-8").replace("'x'", "'a\n(cloth) b \nc'", 1),
                           encoding="utf-8")
            linter = _real_linter()
            with out.open(encoding="utf-8") as f:
                linter.trailing_whitespace_check(f, str(out))
                linter.backtick_check(f, str(out))
            self.assertTrue(linter.error_handler)


if __name__ == "__main__":
    unittest.main()
