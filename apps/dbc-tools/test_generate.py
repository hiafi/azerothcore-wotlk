"""
Unit tests for `generate.py`'s `_merge_dsl_sources` — Phase 1 of
`.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md`. Exercises just
the merge/duplicate-detection logic in memory; doesn't call `generate.main()`
itself, which does real filesystem I/O (SQL/DBC/MPQ output) and is slow
enough to be a poor fit for a unit test — see the plan's session handoff for
why a full `generate.py` run was set aside as a Phase 1 smoke test.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/test_generate.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate  # noqa: E402
from lib import source  # noqa: E402


def _talents(**overrides) -> dict:
    base = {"tabs": [], "talents": [], "skill_line_abilities": []}
    base.update(overrides)
    return base


class MergeDslSourcesTest(unittest.TestCase):
    def test_merges_non_conflicting_entries(self):
        spell_entries = [{"id": 116, "name": "Frostbolt", "_source_file": "mage.csv"}]
        talents = _talents(tabs=[{"id": 41, "name": "Fire"}])
        dsl_classes = {
            "spells": [{"id": 200001, "name": "New Spell"}],
            "talents": [{"id": 60000}],
            "tabs": [],
            "skill_line_abilities": [{"id": 30400}],
        }
        generate._merge_dsl_sources(spell_entries, talents, dsl_classes)
        self.assertEqual([e["id"] for e in spell_entries], [116, 200001])
        self.assertEqual([e["id"] for e in talents["tabs"]], [41])
        self.assertEqual([e["id"] for e in talents["talents"]], [60000])
        self.assertEqual([e["id"] for e in talents["skill_line_abilities"]], [30400])

    def test_empty_dsl_classes_is_a_no_op(self):
        spell_entries = [{"id": 116, "name": "Frostbolt", "_source_file": "mage.csv"}]
        talents = _talents(tabs=[{"id": 41, "name": "Fire"}])
        empty = {"spells": [], "talents": [], "tabs": [], "skill_line_abilities": []}
        generate._merge_dsl_sources(spell_entries, talents, empty)
        self.assertEqual(len(spell_entries), 1)
        self.assertEqual(len(talents["tabs"]), 1)

    def test_spell_id_collision_with_csv_raises(self):
        spell_entries = [{"id": 116, "name": "Frostbolt", "_source_file": "mage.csv"}]
        talents = _talents()
        dsl_classes = {
            "spells": [{"id": 116, "name": "Impostor Frostbolt"}],
            "talents": [], "tabs": [], "skill_line_abilities": [],
        }
        with self.assertRaises(source.DuplicateIdError):
            generate._merge_dsl_sources(spell_entries, talents, dsl_classes)

    def test_tab_id_collision_with_yaml_raises(self):
        spell_entries = []
        talents = _talents(tabs=[{"id": 41, "name": "Fire"}])
        dsl_classes = {
            "spells": [], "talents": [], "skill_line_abilities": [],
            "tabs": [{"id": 41, "name": "Impostor Fire"}],
        }
        with self.assertRaises(source.DuplicateIdError):
            generate._merge_dsl_sources(spell_entries, talents, dsl_classes)


class _FakeTable:
    """Duck-typed stand-in for a `lib.dbcfmt.DbcTable` - `_drop_unchanged_blocks`
    only ever reads `.index_column`."""

    def __init__(self, index_column: str = "ID"):
        self.index_column = index_column


ID_RANGE = {"start": 200000, "end": 200099}


class DropUnchangedBlocksTest(unittest.TestCase):
    def test_unchanged_table_is_dropped(self):
        table = _FakeTable()
        rows = [{"ID": 200000, "v": 1}]
        existing = {200000: {"ID": 200000, "v": 1}}
        filtered, n_dropped = generate._drop_unchanged_blocks(
            [(table, ID_RANGE, rows, [], existing)]
        )
        self.assertEqual(filtered, [])
        self.assertEqual(n_dropped, 1)

    def test_changed_table_is_kept(self):
        table = _FakeTable()
        rows = [{"ID": 200000, "v": 99}]
        existing = {200000: {"ID": 200000, "v": 1}}
        filtered, n_dropped = generate._drop_unchanged_blocks(
            [(table, ID_RANGE, rows, [], existing)]
        )
        self.assertEqual(filtered, [(table, ID_RANGE, rows, [])])
        self.assertEqual(n_dropped, 0)

    def test_edited_ids_keeps_the_table_even_if_reserved_content_matches(self):
        table = _FakeTable()
        rows = [{"ID": 200000, "v": 1}]
        existing = {200000: {"ID": 200000, "v": 1}}
        filtered, n_dropped = generate._drop_unchanged_blocks(
            [(table, ID_RANGE, rows, [116], existing)]
        )
        self.assertEqual(filtered, [(table, ID_RANGE, rows, [116])])
        self.assertEqual(n_dropped, 0)

    def test_forced_table_is_kept(self):
        """lib/stale_overlay.py found live reserved rows that promoted state cannot show: keep the block."""
        table = _FakeTable()
        table.name = "Talent"
        rows = [{"ID": 200000, "v": 1}]
        existing = {200000: {"ID": 200000, "v": 1}}
        filtered, n_dropped = generate._drop_unchanged_blocks(
            [(table, ID_RANGE, rows, [], existing)], force={"Talent"},
        )
        self.assertEqual(filtered, [(table, ID_RANGE, rows, [])])
        self.assertEqual(n_dropped, 0)

    def test_mixed_list_keeps_only_the_changed_tables(self):
        # Two different tables (own ID space each, even though this synthetic test happens to
        # reuse the same numeric ID_RANGE for both) - each must be judged against its own
        # existing-rows dict, not a shared one.
        unchanged_table, changed_table = _FakeTable(), _FakeTable()
        unchanged_rows = [{"ID": 200000, "v": 1}]
        changed_rows = [{"ID": 200001, "v": 2}]
        filtered, n_dropped = generate._drop_unchanged_blocks([
            (unchanged_table, ID_RANGE, unchanged_rows, [], {200000: {"ID": 200000, "v": 1}}),
            (changed_table, ID_RANGE, changed_rows, [], {200001: {"ID": 200001, "v": 1}}),
        ])
        self.assertEqual(filtered, [(changed_table, ID_RANGE, changed_rows, [])])
        self.assertEqual(n_dropped, 1)


class DropUnchangedAgainstPendingTest(unittest.TestCase):
    """dbc-replay-fix follow-up: `applied` (promoted + pending revs, as db-import leaves the table) makes a block whose
    content already sits in a pending rev a no-op, so a no-change run writes no rev."""

    def setUp(self):
        self.table = _FakeTable()
        self.table.name = "Spell"
        self.promoted = {200000: {"ID": 200000, "v": 1}, 116: {"ID": 116, "v": 1}}

    def run_drop(self, rows, edited, applied, force=frozenset()):
        return generate._drop_unchanged_blocks(
            [(self.table, ID_RANGE, rows, edited, self.promoted)], force=force, applied={"Spell": applied},
        )

    def test_no_change_run_with_the_content_in_a_pending_rev_emits_nothing(self):
        rows = [{"ID": 200000, "v": 2}, {"ID": 116, "v": 5}]
        applied = {200000: {"ID": 200000, "v": 2}, 116: {"ID": 116, "v": 5}}
        self.assertEqual(self.run_drop(rows, [116], applied), ([], 1))

    def test_a_real_change_still_emits(self):
        applied = {200000: {"ID": 200000, "v": 2}, 116: {"ID": 116, "v": 5}}
        for rows, edited in (
            ([{"ID": 200000, "v": 3}, {"ID": 116, "v": 5}], [116]),  # reserved content changed
            ([{"ID": 200000, "v": 2}, {"ID": 116, "v": 6}], [116]),  # an edited stock row changed
            ([{"ID": 200000, "v": 2}, {"ID": 200001, "v": 1}, {"ID": 116, "v": 5}], [116]),  # a new row
            ([{"ID": 200000, "v": 2}, {"ID": 116, "v": 5}, {"ID": 133, "v": 1}], [116, 133]),  # edit not applied yet
        ):
            with self.subTest(rows=rows):
                self.assertEqual(self.run_drop(rows, edited, applied), ([(self.table, ID_RANGE, rows, edited)], 0))

    def test_prune_still_emits(self):
        # A reserved row dropped from source but still applied (the block's DELETE BETWEEN removes it), and a stale
        # overlay delete (an edited id with no row) of a row still applied.
        applied = {200000: {"ID": 200000, "v": 2}, 200005: {"ID": 200005, "v": 1}, 117: {"ID": 117, "v": 9}}
        rows = [{"ID": 200000, "v": 2}]
        self.assertEqual(self.run_drop(rows, [], applied), ([(self.table, ID_RANGE, rows, [])], 0))
        applied.pop(200005)
        self.assertEqual(self.run_drop(rows, [117], applied), ([(self.table, ID_RANGE, rows, [117])], 0))
        applied.pop(117)
        self.assertEqual(self.run_drop(rows, [117], applied), ([], 1))  # already deleted by a pending rev

    def test_forced_and_unlisted_tables_keep_the_old_rule(self):
        rows = [{"ID": 200000, "v": 2}]
        applied = {200000: {"ID": 200000, "v": 2}}
        self.assertEqual(self.run_drop(rows, [], applied, force={"Spell"}), ([(self.table, ID_RANGE, rows, [])], 0))
        filtered, n_dropped = generate._drop_unchanged_blocks(
            [(self.table, ID_RANGE, rows, [], self.promoted)], applied={"Talent": applied},
        )
        self.assertEqual((filtered, n_dropped), ([(self.table, ID_RANGE, rows, [])], 0))

    def test_applied_function_is_asked_only_for_blocks_promoted_state_calls_changed(self):
        asked = []

        def applied(table):
            asked.append(table.name)
            return {200000: {"ID": 200000, "v": 2}}

        same = [{"ID": 200000, "v": 1}]  # equal to promoted: dropped without asking
        self.assertEqual(generate._drop_unchanged_blocks(
            [(self.table, ID_RANGE, same, [], self.promoted)], applied=applied), ([], 1))
        self.assertEqual(asked, [])
        pending_only = [{"ID": 200000, "v": 2}]
        self.assertEqual(generate._drop_unchanged_blocks(
            [(self.table, ID_RANGE, pending_only, [], self.promoted)], applied=applied), ([], 1))
        self.assertEqual(asked, ["Spell"])


class PendingDependencyNoteTest(unittest.TestCase):
    """Review S7 / ruling 1: a block dropped because its content sits in pending files names them, and says they must
    ship (not that the content is already live)."""

    def setUp(self):
        self.table = _FakeTable()
        self.table.name = "Spell"
        self.promoted = {200000: {"ID": 200000, "v": 1}}

    def test_dropped_block_names_its_pending_files(self):
        from lib import state

        pending = generate.PENDING_SQL_DIR
        applied = state.AppliedRows({200000: {"ID": 200000, "v": 2}})
        applied.sources = {200000: [pending / "rev_2.sql", pending / "rev_1.sql"], 116: [pending / "rev_1.sql"]}
        deps: dict = {}
        result = generate._drop_unchanged_blocks(
            [(self.table, ID_RANGE, [{"ID": 200000, "v": 2}], [], self.promoted)], applied={"Spell": applied},
            dependencies=deps,
        )
        self.assertEqual(result, ([], 1))
        self.assertEqual([p.name for p in deps["Spell"]], ["rev_1.sql", "rev_2.sql"])
        notes = generate._pending_dependency_notes(deps)
        self.assertEqual(len(notes), 1)
        self.assertIn("Spell: not re-emitted because its content is in pending file(s) rev_1.sql, rev_2.sql", notes[0])
        self.assertIn("must ship", notes[0])

    def test_a_kept_block_or_one_equal_to_promoted_state_names_nothing(self):
        from lib import state

        applied = state.AppliedRows({200000: {"ID": 200000, "v": 2}})
        applied.sources = {200000: [generate.PENDING_SQL_DIR / "rev_1.sql"]}
        deps: dict = {}
        generate._drop_unchanged_blocks(
            [(self.table, ID_RANGE, [{"ID": 200000, "v": 3}], [], self.promoted)], applied={"Spell": applied},
            dependencies=deps,
        )
        generate._drop_unchanged_blocks(
            [(self.table, ID_RANGE, [{"ID": 200000, "v": 1}], [], self.promoted)], applied={"Spell": applied},
            dependencies=deps,
        )
        self.assertEqual(deps, {})

    def test_module_files_are_not_named(self):
        deps = {"Spell": [Path("/x/modules/mod-transmog/data/sql/db-world/2016_11_17_transmog_npc.sql")]}
        self.assertEqual(generate._pending_dependency_notes(deps), [])

    def test_block_ids(self):
        self.assertEqual(generate._block_ids({"start": 5, "end": 7}, [116]), {5, 6, 7, 116})


class LoadAppliedRowsTest(unittest.TestCase):
    def test_module_sql_runs_in_dbupdater_name_order_and_sources_are_tracked(self):
        # Review design question 4: DBUpdater's second pass orders pending and module files together by bare name. A
        # module file that sorts first (mod-transmog's 2016_11_17_transmog_npc.sql) is overwritten by the pending rev
        # after it, so the spell block it touches reads as unchanged; one that sorts last wins.
        import tempfile
        from unittest import mock

        from lib import dbcfmt, state, trainer_state

        table = dbcfmt.DbcTable(name="W", dbc_filename="W.dbc", sql_table="w_dbc", fmt="ni", columns=("ID", "v"))
        existing = {1: {"ID": 1, "v": 1}}
        with tempfile.TemporaryDirectory() as tmp:
            pending, modules = Path(tmp) / "pending", Path(tmp) / "modules"
            world = modules / "mod-transmog" / "data" / "sql" / "db-world"
            world.mkdir(parents=True)
            pending.mkdir()
            (world / "2016_11_17_transmog_npc.sql").write_text("DELETE FROM `w_dbc` WHERE `ID` = 1;\n"
                                                              "INSERT INTO `w_dbc` VALUES (1, 77);\n")
            (world / "zz_late.sql").write_text("INSERT INTO `w_dbc` VALUES (9, 9);\n")
            (pending / "rev_1.sql").write_text(
                "DELETE FROM `w_dbc` WHERE `ID` = 1;\nINSERT INTO `w_dbc` VALUES (1, 5);\n"
            )
            with mock.patch.object(state, "PENDING_SQL_DIR", pending), \
                    mock.patch.object(trainer_state, "MODULES_DIR", modules):
                applied = state.load_applied_rows(table, existing, watch={1, 9})
        self.assertEqual(dict(applied), {1: {"ID": 1, "v": 5}, 9: {"ID": 9, "v": 9}})
        self.assertEqual({k: [p.name for p in v] for k, v in applied.sources.items()},
                         {1: ["2016_11_17_transmog_npc.sql", "rev_1.sql"], 9: ["zz_late.sql"]})


    def test_pending_revs_replayed_in_name_order_on_a_copy(self):
        import tempfile
        from unittest import mock

        from lib import dbcfmt, state

        table = dbcfmt.DbcTable(name="W", dbc_filename="W.dbc", sql_table="w_dbc", fmt="ni", columns=("ID", "v"))
        existing = {1: {"ID": 1, "v": 1}, 2: {"ID": 2, "v": 2}}
        with tempfile.TemporaryDirectory() as tmp:
            pending = Path(tmp)
            (pending / "rev_2.sql").write_text("UPDATE `w_dbc` SET `v` = 30 WHERE `ID` = 1;\n")
            (pending / "rev_1.sql").write_text(
                "DELETE FROM `w_dbc` WHERE `ID` = 2;\nINSERT INTO `w_dbc` VALUES (1, 10), (3, 3);\n"
            )
            (pending / "other.sql").write_text("UPDATE `x_dbc` SET `v` = 0;\n")
            with mock.patch.object(state, "PENDING_SQL_DIR", pending):
                applied = state.load_applied_rows(table, existing)
        self.assertEqual(applied, {1: {"ID": 1, "v": 30}, 3: {"ID": 3, "v": 3}})
        self.assertEqual(existing, {1: {"ID": 1, "v": 1}, 2: {"ID": 2, "v": 2}})


TRAINER_SPELL_ROW = {
    "id": "13:200005", "TrainerId": 13, "SpellId": 200005, "MoneyCost": 500,
    "ReqSkillLine": 0, "ReqSkillRank": 0, "ReqAbility1": 0, "ReqAbility2": 0,
    "ReqAbility3": 0, "ReqLevel": 20, "VerifiedBuild": 0,
}


class TrainerSpellsToEmitTest(unittest.TestCase):
    def test_new_grant_is_emitted(self):
        live = {}
        self.assertEqual(generate._trainer_spells_to_emit([TRAINER_SPELL_ROW], live), [TRAINER_SPELL_ROW])

    def test_identical_existing_grant_is_not_re_emitted(self):
        live = {(13, 200005): dict(TRAINER_SPELL_ROW)}
        self.assertEqual(generate._trainer_spells_to_emit([TRAINER_SPELL_ROW], live), [])

    def test_changed_existing_grant_is_re_emitted(self):
        existing = dict(TRAINER_SPELL_ROW)
        existing["ReqLevel"] = 55  # source now wants a different level
        live = {(13, 200005): existing}
        self.assertEqual(generate._trainer_spells_to_emit([TRAINER_SPELL_ROW], live), [TRAINER_SPELL_ROW])


if __name__ == "__main__":
    unittest.main()
