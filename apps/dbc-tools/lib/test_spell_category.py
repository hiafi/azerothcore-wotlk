"""
Paladin T1 tests (.agents/plans/paladin-rework/paladin-rework.T1-HANDOFF.md): `spell_category()`
(spellcategory_dbc), its undeclared-category check, `remove_spell_proc()` (spell_proc removals) and
the non-zero-ProcFlags warning. Fixtures only - no real class content.

Run directly:

    python3 apps/dbc-tools/lib/test_spell_category.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import generate  # noqa: E402
from lib import dbcfile, dbcfmt, lint, spell_tables, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402

IDS_CFG = {"spellcategory": {"start": 1300, "end": 1309}}

SPELLCATEGORY_BASE = (
    "CREATE TABLE `spellcategory_dbc` (\n"
    "  `ID` int unsigned NOT NULL DEFAULT '0',\n"
    "  `Flags` int unsigned NOT NULL DEFAULT '0',\n"
    "  PRIMARY KEY (`ID`)\n"
    ") ENGINE=InnoDB;\n"
)
SPELL_PROC_BASE = (
    "CREATE TABLE `spell_proc` (\n"
    + "".join(f"  `{c}` int NOT NULL DEFAULT '0',\n" for c in spell_tables.SPELL_PROC_COLUMNS)
    + "  PRIMARY KEY (`SpellId`)\n"
    ") ENGINE=InnoDB;\n"
    "INSERT INTO `spell_proc` VALUES (-53695,0,0,0,0,0,69904,0,0,0,0,0,0,0,0,0);\n"
)


def _load(source: str, ids_cfg=IDS_CFG) -> dict:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "paladin.py"
        path.write_text(source)
        reg = registry.load_class_file(path, ids_cfg=ids_cfg)
    return {k: getattr(reg, k) for k in registry.MERGE_KEYS}


class SpellCategoryRegistryTest(unittest.TestCase):
    def test_declares_row(self):
        dsl = _load("from lib.dsl.registry import spell_category\nspell_category(1300, comment='auras')\n")
        (row,) = dsl["spell_categories"]
        self.assertEqual((row["ID"], row["Flags"], row["id"]), (1300, 0, 1300))

    def test_flags_passed_through(self):
        dsl = _load("from lib.dsl.registry import spell_category\nspell_category(1301, flags=4)\n")
        self.assertEqual(dsl["spell_categories"][0]["Flags"], 4)

    def test_id_outside_block_raises(self):
        for bad in (1253, 1310, 0):
            with self.assertRaises(ValueError, msg=bad):
                _load(f"from lib.dsl.registry import spell_category\nspell_category({bad})\n")

    def test_missing_block_raises(self):
        with self.assertRaises(ValueError):
            _load("from lib.dsl.registry import spell_category\nspell_category(1300)\n", ids_cfg={})

    def test_bad_flags_raises(self):
        with self.assertRaises(ValueError):
            _load("from lib.dsl.registry import spell_category\nspell_category(1300, flags=-1)\n")

    def test_duplicate_declaration_across_files_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.py", "b.py"):
                (Path(d) / name).write_text("from lib.dsl.registry import spell_category\nspell_category(1300)\n")
            with self.assertRaises(registry.DuplicateIdError):
                registry.load_classes_dir(Path(d), ids_cfg=IDS_CFG)


class _TableDirsTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.base, self.promoted, self.pending = root / "base", root / "promoted", root / "pending"
        for d in (self.base, self.promoted, self.pending):
            d.mkdir()
        (self.base / "spellcategory_dbc.sql").write_text(SPELLCATEGORY_BASE)
        (self.base / "spell_proc.sql").write_text(SPELL_PROC_BASE)
        self._orig = (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR)
        trainer_state.BASE_SQL_DIR = self.base
        trainer_state.PROMOTED_SQL_DIR = self.promoted
        trainer_state.PENDING_SQL_DIR = self.pending

    def tearDown(self):
        (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR) = self._orig
        self._tmp.cleanup()

    def _write_generated(self, blocks):
        header = spell_tables.GENERATED_MARKER + " -- DO NOT hand-edit.\n"
        (self.promoted / "gen.sql").write_text(header + "\n\n".join(blocks) + "\n")


class SpellCategoryEmissionTest(_TableDirsTestCase):
    SOURCE = "from lib.dsl.registry import spell_category\nspell_category(1300)\n"

    def _blocks(self, dsl):
        return spell_tables.render_blocks(spell_tables.load_spell_table_index(), dsl)

    def test_emits_delete_then_insert_by_id(self):
        (block,) = self._blocks(_load(self.SOURCE))
        self.assertIn("DELETE FROM `spellcategory_dbc` WHERE (`ID`) IN ((1300));", block)
        self.assertIn("INSERT INTO `spellcategory_dbc` (`ID`, `Flags`) VALUES", block)
        self.assertLess(block.index("DELETE"), block.index("INSERT"))
        self.assertNotIn("comment", block)

    def test_rerun_unchanged_is_silent_and_flag_change_re_emits(self):
        self._write_generated(self._blocks(_load(self.SOURCE)))
        self.assertEqual(self._blocks(_load(self.SOURCE)), [])
        changed = "from lib.dsl.registry import spell_category\nspell_category(1300, flags=2)\n"
        self.assertEqual(len(self._blocks(_load(changed))), 1)

    def test_dropped_declaration_is_pruned(self):
        self._write_generated(self._blocks(_load(self.SOURCE)))
        dsl = _load("from lib.dsl.registry import spell_category\nspell_category(1301)\n")
        blocks, report = spell_tables.render_prune_blocks(spell_tables.load_spell_table_index(), dsl)
        self.assertEqual(len(blocks), 1)
        self.assertIn("DELETE FROM `spellcategory_dbc` WHERE (`ID`) IN ((1300));", blocks[0])


class UndeclaredCategoryCheckTest(unittest.TestCase):
    BLOCK = IDS_CFG["spellcategory"]

    def test_declared_category_is_clean(self):
        entries = [{"id": 200001, "name": "Aura", "category": 1300}]
        self.assertEqual(lint.check_undeclared_spell_categories(entries, {1300}, self.BLOCK), [])

    def test_undeclared_custom_category_is_an_error(self):
        entries = [{"id": 200001, "name": "Aura", "category": 1300}]
        (error,) = lint.check_undeclared_spell_categories(entries, set(), self.BLOCK)
        self.assertIn("200001", error)
        self.assertIn("spell_category(1300)", error)

    def test_raw_override_category_counts_and_wins(self):
        entries = [{"id": 200002, "name": "Aura", "category": 0, "raw_overrides": {"Category": 1305}}]
        self.assertEqual(len(lint.check_undeclared_spell_categories(entries, {1300}, self.BLOCK)), 1)
        entries = [{"id": 200002, "name": "Aura", "category": 1305, "raw_overrides": {"Category": 5}}]
        self.assertEqual(lint.check_undeclared_spell_categories(entries, set(), self.BLOCK), [])

    def test_stock_categories_and_missing_block_are_ignored(self):
        entries = [{"id": 1, "name": "Stock", "category": 1253}, {"id": 2, "name": "None"}]
        self.assertEqual(lint.check_undeclared_spell_categories(entries, set(), self.BLOCK), [])
        entries = [{"id": 3, "name": "X", "category": 1300}]
        self.assertEqual(lint.check_undeclared_spell_categories(entries, set(), None), [])


class RemoveSpellProcTest(_TableDirsTestCase):
    SOURCE = "from lib.dsl.registry import remove_spell_proc\nremove_spell_proc(-53695)\nremove_spell_proc(20128)\n"

    def test_registry_rows_allow_negative_ids(self):
        dsl = _load(self.SOURCE)
        self.assertEqual([r["SpellId"] for r in dsl["proc_removals"]], [-53695, 20128])

    def test_emits_key_exact_delete(self):
        blocks, report = spell_tables.render_removal_blocks(_load(self.SOURCE))
        (block,) = blocks
        self.assertIn("DELETE FROM `spell_proc` WHERE (`SpellId`) IN ((-53695), (20128));", block)
        self.assertNotIn("INSERT", block)
        self.assertTrue(any("removal: spell_proc (SpellId=-53695)" in line for line in report))

    def test_warns_only_for_key_that_exists_nowhere(self):
        _, report = spell_tables.render_removal_blocks(_load(self.SOURCE))
        warnings = [line for line in report if line.startswith("WARNING:")]
        self.assertEqual(len(warnings), 1)
        self.assertIn("SpellId=20128", warnings[0])  # -53695 is in the base dump

    def test_rerun_after_emission_is_silent(self):
        blocks, _ = spell_tables.render_removal_blocks(_load(self.SOURCE))
        self._write_generated(blocks)
        self.assertEqual(spell_tables.render_removal_blocks(_load(self.SOURCE)), ([], []))

    def test_declare_and_remove_conflict_raises(self):
        dsl = _load(
            "from lib.dsl.registry import procs_on, remove_spell_proc\n"
            "procs_on(-53695, proc_flags=1, chance=5)\nremove_spell_proc(-53695)\n"
        )
        with self.assertRaises(spell_tables.DeclareAndRemoveConflictError):
            spell_tables.render_removal_blocks(dsl)

    def test_duplicate_declaration_is_rejected(self):
        with self.assertRaises(registry.DuplicateIdError):
            with tempfile.TemporaryDirectory() as d:
                for name in ("a.py", "b.py"):
                    (Path(d) / name).write_text(
                        "from lib.dsl.registry import remove_spell_proc\nremove_spell_proc(-53695)\n"
                    )
                registry.load_classes_dir(Path(d), ids_cfg=IDS_CFG)


class RemovedProcFlagsWarningTest(unittest.TestCase):
    def test_warns_while_proc_flags_non_zero(self):
        rows = {53695: {"ID": 53695, "ProcTypeMask": 69904}, 53696: {"ID": 53696, "ProcTypeMask": 69904}}
        (warning,) = lint.check_removed_proc_flags([-53695], rows)
        self.assertIn("53695", warning)
        self.assertIn("NOT disabled", warning)

    def test_silent_once_both_ranks_zeroed(self):
        rows = {53695: {"ID": 53695, "ProcTypeMask": 0}, 53696: {"ID": 53696, "ProcTypeMask": 0}}
        self.assertEqual(lint.check_removed_proc_flags([-53695, 53696], rows), [])

    def test_negative_id_checks_every_rank_and_names_offender(self):
        rows = {53695: {"ProcTypeMask": 0}, 53696: {"ProcTypeMask": 69904}}
        (warning,) = lint.check_removed_proc_flags([-53695], rows, {53695: [53695, 53696]})
        self.assertIn("spell 53696 ", warning)

    def test_negative_id_silent_when_all_ranks_zeroed(self):
        rows = {53695: {"ProcTypeMask": 0}, 53696: {"ProcTypeMask": 0}}
        self.assertEqual(lint.check_removed_proc_flags([-53695], rows, {53695: [53695, 53696]}), [])

    def test_positive_id_ignores_chain(self):
        rows = {53695: {"ProcTypeMask": 0}, 53696: {"ProcTypeMask": 69904}}
        self.assertEqual(lint.check_removed_proc_flags([53695], rows, {53695: [53695, 53696]}), [])

    def test_dsl_chain_beats_existing_talents(self):
        existing = {1: {"SpellRank_1": 53695, "SpellRank_2": 53696, "SpellRank_3": 0}}
        dsl = [{"rank_spell_ids": [53695, 53696, 99001]}]
        chains = lint.build_talent_rank_chains(existing, dsl)
        self.assertEqual(chains[53695], [53695, 53696, 99001])
        self.assertEqual(lint.build_talent_rank_chains(existing, [])[53695], [53695, 53696])
        rows = {53695: {"ProcTypeMask": 0}, 53696: {"ProcTypeMask": 0}, 99001: {"ProcTypeMask": 5}}
        (warning,) = lint.check_removed_proc_flags([-53695], rows, chains)
        self.assertIn("spell 99001 ", warning)

    def test_unknown_spell_is_skipped_silently(self):
        self.assertEqual(lint.check_removed_proc_flags([-99999], {}), [])


class SpellCategoryClientRowTest(unittest.TestCase):
    """The client half: declared rows merge over the stock SpellCategory.dbc into the patch."""

    TABLE = dbcfmt.SPELLCATEGORY

    def test_table_shape_and_no_double_sql(self):
        self.assertEqual((self.TABLE.fmt, self.TABLE.columns), ("ni", ("ID", "Flags")))
        self.assertEqual(self.TABLE.sql_table, "spellcategory_dbc")
        # SQL stays the SPELL_TABLES delta; a second SQL source would emit the block twice.
        self.assertNotIn(self.TABLE, dbcfmt.ALL_TABLES)
        self.assertNotIn("SpellCategory", generate.SECONDARY_TABLES)
        self.assertIn("spellcategory_dbc", [t.name for t in spell_tables.SPELL_TABLES])

    def test_declared_rows_to_dbc_rows(self):
        rows = generate._spell_category_rows([{"ID": 1300, "Flags": 0, "id": 1300}, {"ID": 1301, "Flags": 4}])
        self.assertEqual(rows, {1300: {"ID": 1300, "Flags": 0}, 1301: {"ID": 1301, "Flags": 4}})
        self.assertEqual(generate._spell_category_rows([]), {})

    def test_merges_over_stock_rows_and_round_trips(self):
        stock = [{"ID": 1, "Flags": 0}, {"ID": 1253, "Flags": 5}]
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / self.TABLE.dbc_filename
            path.write_bytes(dbcfile.pack_dbc_bytes(self.TABLE, stock))
            base_rows = dbcfile.read_dbc(path, self.TABLE)
            merged = {r["ID"]: r for r in base_rows}
            merged.update(generate._spell_category_rows([{"ID": 1300, "Flags": 0}]))
            path.write_bytes(dbcfile.pack_client_dbc(self.TABLE, list(merged.values()), base_rows))
            out = dbcfile.read_dbc(path, self.TABLE)
        self.assertEqual(sorted(r["ID"] for r in out), [1, 1253, 1300])
        self.assertEqual({r["ID"]: r["Flags"] for r in out}, {1: 0, 1253: 5, 1300: 0})

    def test_missing_base_dbc_fails_loudly_when_declared(self):
        with TemporaryDirectory() as tmp:
            rows = generate._spell_category_rows([{"ID": 1300, "Flags": 0}])
            error = generate._spell_category_base_error(rows, Path(tmp))
            self.assertIn("SpellCategory.dbc", error)
            self.assertIn("1300", error)
            self.assertIsNone(generate._spell_category_base_error({}, Path(tmp)))
            (Path(tmp) / "SpellCategory.dbc").write_bytes(b"")
            self.assertIsNone(generate._spell_category_base_error(rows, Path(tmp)))


if __name__ == "__main__":
    unittest.main()
