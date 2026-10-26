"""
creation_action() / creation_cast() / creation_skill() and their removals (Death Knight T1, step 4): the helpers, the
three playercreateinfo_* SPELL_TABLES entries and their REMOVAL_TABLES entries.

Covered, per the handoff: each validation; render plus the real codestyle-sql.py (`type` and `rank` are column names,
the renderer quotes them); convergence through the real readers; removal; declare + remove conflict; and the three
reader-trap cases, run over the real tables (base dump + migrations + the P0 spike's hand-written file):
  (i)   a DK override of a stock key (race 1, class 6, button 4) renders and converges on rerun;
  (ii)  remove_creation_cast(48266, 32) emits one DELETE even though a hand file already deleted the row, and
        converges after;
  (iii) an undeclared priest key (which a hand-written UPDATE changed) is never touched.
Plus the First Aid removal: one key-exact DELETE for the live (0, 32, 129) row, the shared-mask rows never touched.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_creation_data.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import lint, spell_tables, sql_out, trainer_state  # noqa: E402
from lib.table_testkit import (  # noqa: E402
    codestyle_sql, generated_file, index_for, load_dsl, no_migrations, read_back, removal_for, render, spec_for,
)
from lib.dsl import registry  # noqa: E402

ACTION = "playercreateinfo_action"
CAST = "playercreateinfo_cast_spell"
SKILLS = "playercreateinfo_skills"

ACTION_FILE = '''
from lib.dsl.registry import creation_action, remove_creation_action

creation_action(1, 6, 0, 6603)
creation_action(1, 6, 4, 49000)            # overrides the stock button 4 (45902)
creation_action(2, 6, 30, 20549, 0)        # a new button
remove_creation_action(10, 6, 6)
'''
CAST_FILE = '''
from lib.dsl.registry import creation_cast, remove_creation_cast, spell

presence = spell(id=203110, name="Test Presence", cast_time_ms=0)
creation_cast(presence, 32, note="Death Knight - test presence")
creation_cast(203111, 32, race_mask=1)
remove_creation_cast(48266, 32)
'''
SKILL_FILE = '''
from lib.dsl.registry import creation_skill, remove_creation_skill

creation_skill(129, 1, rank=4, comment="test first aid")
remove_creation_skill(129, 32)
'''


class _Real:
    """The live rows as `load_spell_table_index` reads them (union of INSERTs over base + migrations + pending),
    loaded once: the reader-trap tests are about exactly this reader."""

    rows: dict[str, list[dict]] = {}

    @classmethod
    def get(cls, table: str) -> list[dict]:
        if table not in cls.rows:
            cls.rows[table] = trainer_state.load_table_rows(table)
        return cls.rows[table]


def _raises(call: str, pattern: str = "", prelude: str = "creation_action, creation_cast, creation_skill") -> None:
    names = prelude + ", remove_creation_action, remove_creation_cast, remove_creation_skill"
    with unittest.TestCase().assertRaisesRegex(ValueError, pattern):
        load_dsl(f"from lib.dsl.registry import {names}\n{call}\n")


class ActionHelperTest(unittest.TestCase):
    def setUp(self):
        self.dsl = load_dsl(ACTION_FILE)

    def test_rows_carry_every_column(self):
        rows = {r["id"]: r for r in self.dsl["creation_actions"]}
        self.assertEqual(
            rows["1:6:4"], {"id": "1:6:4", "race": 1, "class": 6, "button": 4, "action": 49000, "type": 0},
        )
        self.assertEqual(rows["2:6:30"]["action"], 20549)

    def test_a_removal_holds_only_the_key(self):
        self.assertEqual(
            self.dsl["creation_action_removals"], [{"id": "10:6:6", "race": 10, "class": 6, "button": 6}],
        )

    def test_validation(self):
        bad = [
            "creation_action(9, 6, 0, 1)", "creation_action(0, 6, 0, 1)", "creation_action(12, 6, 0, 1)",
            "creation_action(True, 6, 0, 1)", "creation_action(1, 10, 0, 1)", "creation_action(1, 12, 0, 1)",
            "creation_action(1, 0, 0, 1)", "creation_action(1, 6, -1, 1)", "creation_action(1, 6, 144, 1)",
            "creation_action(1, 6, '0', 1)", "creation_action(1, 6, 0, -1)", "creation_action(1, 6, 0, 1.5)",
            "creation_action(1, 6, 0, 1, 1)", "creation_action(1, 6, 0, 1, 0x20)", "creation_action(1, 6, 0, 1, True)",
            "remove_creation_action(9, 6, 0)", "remove_creation_action(1, 6, 144)",
        ]
        for call in bad:
            with self.subTest(call=call):
                _raises(call)

    def test_the_limits_and_every_action_type_are_accepted(self):
        dsl = load_dsl(
            "from lib.dsl.registry import creation_action\n"
            "creation_action(11, 11, 143, 5, 0x80)\ncreation_action(10, 1, 0, 5, 0x40)\ncreation_action(8, 9, 1, 5)\n"
        )
        self.assertEqual([r["type"] for r in dsl["creation_actions"]], [0x80, 0x40, 0])

    def test_outside_a_load_the_helpers_raise(self):
        with self.assertRaises(RuntimeError):
            registry.creation_action(1, 6, 0, 6603)
        with self.assertRaises(RuntimeError):
            registry.remove_creation_action(1, 6, 0)

    def test_the_same_key_twice_is_a_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.py", "b.py"):
                (Path(d) / name).write_text(
                    "from lib.dsl.registry import creation_action\ncreation_action(1, 6, 0, 6603)\n"
                )
            with self.assertRaises(registry.DuplicateIdError):
                registry.load_classes_dir(Path(d))


class CastAndSkillHelperTest(unittest.TestCase):
    def test_cast_rows(self):
        dsl = load_dsl(CAST_FILE)
        rows = {r["spell"]: r for r in dsl["creation_casts"]}
        self.assertEqual(
            rows[203110],
            {"id": "0:32:203110", "raceMask": 0, "classMask": 32, "spell": 203110,
             "note": "Death Knight - test presence"},
        )
        self.assertEqual((rows[203111]["raceMask"], rows[203111]["note"]), (1, None))
        self.assertEqual(
            dsl["creation_cast_removals"], [{"id": "0:32:48266", "raceMask": 0, "classMask": 32, "spell": 48266}],
        )

    def test_skill_rows(self):
        dsl = load_dsl(SKILL_FILE)
        self.assertEqual(
            dsl["creation_skills"],
            [{"id": "0:1:129", "raceMask": 0, "classMask": 1, "skill": 129, "rank": 4, "comment": "test first aid"}],
        )
        self.assertEqual(
            dsl["creation_skill_removals"], [{"id": "0:32:129", "raceMask": 0, "classMask": 32, "skill": 129}],
        )

    def test_mask_validation_follows_the_loader(self):
        bad = [
            "creation_cast(5, 0)",                    # a class mask of 0 would mean every class: say so explicitly
            "creation_cast(5, 512)",                  # class 10 does not exist
            "creation_cast(5, 2048)",                 # past the last class
            "creation_cast(5, 32, race_mask=256)",    # race 9 is not playable
            "creation_cast(5, 32, race_mask=2048)",
            "creation_cast(5, 32, race_mask=-1)",
            "creation_cast(5, True)", "creation_cast(5, '32')", "creation_cast(5, 32, race_mask=1.0)",
            "creation_cast(0, 32)", "creation_cast(-1, 32)", "creation_cast('5', 32)", "creation_cast(True, 32)",
            "remove_creation_cast(5, 0)", "remove_creation_cast(5, 32, race_mask=256)",
            "creation_skill(129, 0)", "creation_skill(129, 32, race_mask=256)", "creation_skill(0, 32)",
            "creation_skill(65536, 32)", "creation_skill(129, 32, rank=-1)", "creation_skill(129, 32, rank=65536)",
            "creation_skill(129, 32, rank=16)",  # MAX_SKILL_STEP: the server skips rank >= 16 at boot
            "creation_skill(True, 32)", "remove_creation_skill(0, 32)", "remove_creation_skill(129, 512)",
        ]
        for call in bad:
            with self.subTest(call=call):
                _raises(call)

    def test_the_playable_masks_are_the_loaders(self):
        self.assertEqual(registry.PLAYABLE_RACE_MASK, 1791)
        self.assertEqual(registry.CLASSMASK_ALL_PLAYABLE, 1535)
        load_dsl(
            "from lib.dsl.registry import creation_cast\ncreation_cast(5, 1535, race_mask=1791)\n"
            "creation_cast(6, 1024)\ncreation_cast(7, 32, race_mask=1024)\n"
        )

    def test_the_docstrings_state_the_scope(self):
        for helper in (registry.creation_action, registry.creation_cast):
            self.assertIn("boot", helper.__doc__)
            self.assertIn("new", helper.__doc__)
        self.assertIn("no primary key", registry.creation_cast.__doc__)


class RenderTest(unittest.TestCase):
    def test_each_table_renders_delete_then_insert_and_passes_the_real_codestyle_check(self):
        action = load_dsl(ACTION_FILE)["creation_actions"]
        cast = load_dsl(CAST_FILE)["creation_casts"]
        skill = load_dsl(SKILL_FILE)["creation_skills"]
        blocks = [
            render(ACTION, index_for(ACTION, []), action),
            render(CAST, index_for(CAST, []), cast),
            render(SKILLS, index_for(SKILLS, []), skill),
        ]
        self.assertIn(
            "DELETE FROM `playercreateinfo_action` WHERE (`race`, `class`, `button`) IN "
            "((1, 6, 0), (1, 6, 4), (2, 6, 30));",
            blocks[0],
        )
        self.assertIn(
            "INSERT INTO `playercreateinfo_action` (`race`, `class`, `button`, `action`, `type`) VALUES", blocks[0],
        )
        self.assertIn("(1, 6, 4, 49000, 0)", blocks[0])
        self.assertIn(
            "DELETE FROM `playercreateinfo_cast_spell` WHERE (`raceMask`, `classMask`, `spell`) IN (", blocks[1],
        )
        self.assertIn("(0, 32, 203110, 'Death Knight - test presence')", blocks[1])
        self.assertIn("(1, 32, 203111, NULL)", blocks[1])
        self.assertIn(
            "INSERT INTO `playercreateinfo_skills` (`raceMask`, `classMask`, `skill`, `rank`, `comment`)", blocks[2],
        )
        self.assertIn("(0, 1, 129, 4, 'test first aid')", blocks[2])
        removals = "\n\n".join(
            sql_out.render_delete_only_block(table, columns, [key])
            for table, columns, key in (
                (ACTION, ("race", "class", "button"), (10.0, 6.0, 6.0)),
                (CAST, ("raceMask", "classMask", "spell"), (0.0, 32.0, 48266.0)),
                (SKILLS, ("raceMask", "classMask", "skill"), (0.0, 32.0, 129.0)),
            )
        )
        done = codestyle_sql("\n\n".join(blocks) + "\n\n" + removals)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("❌", done.stdout)

    def test_a_declaration_equal_to_live_is_not_re_emitted(self):
        live = [{"race": 1, "class": 6, "button": 0, "action": 6603, "type": 0}]
        rows = index_for(ACTION, live).rows_to_emit(spec_for(ACTION), load_dsl(ACTION_FILE)["creation_actions"])
        self.assertEqual([r["button"] for r in rows], [4, 30])

    def test_a_note_left_out_of_a_hand_row_reads_as_null(self):
        live = [{"raceMask": 1, "classMask": 32, "spell": 203111}]
        rows = index_for(CAST, live).rows_to_emit(spec_for(CAST), load_dsl(CAST_FILE)["creation_casts"])
        self.assertEqual([r["spell"] for r in rows], [203110])


class ConvergenceTest(unittest.TestCase):
    """Hunter T1-1: render, read the output back through the readers the diff uses, re-render: nothing."""

    def _converges(self, table, declared):
        live = _Real.get(table)
        first = render(table, index_for(table, live), declared)
        self.assertTrue(first)
        again = live + read_back(first, table, spec_for(table).columns)
        self.assertEqual(render(table, index_for(table, again), declared), "")
        return first

    def test_actions_converge_over_the_real_table(self):
        self._converges(ACTION, load_dsl(ACTION_FILE)["creation_actions"])

    def test_casts_converge_over_the_real_table(self):
        self._converges(CAST, load_dsl(CAST_FILE)["creation_casts"])

    def test_skills_converge_over_the_real_table(self):
        self._converges(SKILLS, load_dsl(SKILL_FILE)["creation_skills"])

    def test_a_dropped_declaration_is_pruned(self):
        declared = load_dsl(ACTION_FILE)["creation_actions"]
        first = render(ACTION, index_for(ACTION, _Real.get(ACTION)), declared)
        with generated_file(first):
            emitted = spell_tables.load_generated_table_rows(ACTION, spec_for(ACTION).key_columns)
        # (1, 6, 0) = 6603 equals the stock row and is not emitted; (1, 6, 4) overrides one and (2, 6, 30) is new
        self.assertEqual({(r["race"], r["button"]) for r in emitted}, {(1, 4), (2, 30)})
        index = index_for(ACTION, _Real.get(ACTION) + emitted, emitted=emitted, base=_Real.get(ACTION))
        result = index.rows_to_prune(spec_for(ACTION), [r for r in declared if r["button"] == 0])
        self.assertEqual(result.keys, [(2.0, 6.0, 30.0)])      # a key this tool added: deleted
        self.assertEqual(result.base_blocked, [(1.0, 6.0, 4.0)])  # a stock key it overrode: reported, never deleted


class SkillRankTest(unittest.TestCase):
    def test_rank_15_is_the_highest_accepted(self):
        (row,) = load_dsl("from lib.dsl.registry import creation_skill\ncreation_skill(129, 32, rank=15)\n")[
            "creation_skills"
        ]
        self.assertEqual(row["rank"], 15)


class ReaderTrapTest(unittest.TestCase):
    """The live-state reader is a union of INSERTs. These run over the real tables."""

    def test_iv_a_redeclared_hand_deleted_row_is_not_re_emitted(self):
        """Documented gotcha (README): the union reader does not replay a hand-written DELETE, so a declaration
        equal to the deleted row's original INSERT reads as unchanged and renders nothing."""
        live = _Real.get(CAST)
        self.assertIn((0, 32, 48266), {(int(r["raceMask"]), int(r["classMask"]), int(r["spell"])) for r in live})
        declared = load_dsl(
            "from lib.dsl.registry import creation_cast\n"
            "creation_cast(48266, 32, note='Death Knight - Blood Presence')\n"
        )["creation_casts"]
        self.assertEqual(render(CAST, index_for(CAST, live), declared), "")

    def test_i_a_dk_override_of_a_stock_key_renders_then_converges(self):
        live = _Real.get(ACTION)
        stock = {(r["race"], r["class"], r["button"]): r for r in live}
        self.assertEqual(stock[(1, 6, 4)]["action"], 45902)  # the stock button the declaration overrides
        declared = load_dsl(
            "from lib.dsl.registry import creation_action\ncreation_action(1, 6, 4, 49000)\n"
        )["creation_actions"]
        first = render(ACTION, index_for(ACTION, live), declared)
        self.assertEqual(first.count("(1, 6, 4"), 2)  # the DELETE key and the INSERT row
        self.assertIn("(1, 6, 4, 49000, 0)", first)
        again = live + read_back(first, ACTION, spec_for(ACTION).columns)
        self.assertEqual(render(ACTION, index_for(ACTION, again), declared), "")
        self.assertEqual({(r["race"], r["class"], r["button"]): r for r in again}[(1, 6, 4)]["action"], 49000)

    def test_ii_the_48266_removal_emits_once_although_a_hand_file_already_deleted_it(self):
        dsl = load_dsl("from lib.dsl.registry import remove_creation_cast\nremove_creation_cast(48266, 32)\n")
        key = (0.0, 32.0, 48266.0)
        live_keys = {key}  # the union reader still sees the base INSERT: the hand file's DELETE is not replayed
        with tempfile.TemporaryDirectory() as d:
            hand = Path(d) / "rev_hand.sql"  # no generated marker: this is the spike's hand-written file
            hand.write_text(
                "DELETE FROM `playercreateinfo_cast_spell` WHERE `classMask` = 32 AND `spell` = 48266;\n",
                encoding="utf-8",
            )
            with mock.patch.object(trainer_state, "_migration_files_mentioning", return_value=[hand]):
                blocks, report = spell_tables.render_removal_blocks(dsl, {CAST: live_keys})
            (block,) = [b for b in blocks if CAST in b]
            self.assertEqual(
                block.splitlines()[-1],
                "DELETE FROM `playercreateinfo_cast_spell` WHERE (`raceMask`, `classMask`, `spell`) IN "
                "((0, 32, 48266));",
            )
            self.assertFalse([line for line in report if line.startswith("WARNING")])
            generated = Path(d) / "rev_gen.sql"
            generated.write_text(spell_tables.GENERATED_MARKER + "\n\n" + block + "\n", encoding="utf-8")
            with mock.patch.object(trainer_state, "_migration_files_mentioning", return_value=[hand, generated]):
                again, _ = spell_tables.render_removal_blocks(dsl, {CAST: live_keys})
        self.assertEqual([b for b in again if CAST in b], [])

    def test_ii_the_real_live_keys_hold_the_row_the_hand_file_deleted(self):
        keys = {
            (int(r["raceMask"]), int(r["classMask"]), int(r["spell"])) for r in _Real.get(CAST)
        }
        self.assertIn((0, 32, 48266), keys)

    def test_iii_an_undeclared_priest_key_is_never_touched(self):
        live = _Real.get(ACTION)
        priest = {k: r for k, r in {(r["race"], r["class"], r["button"]): r for r in live}.items() if k[1] == 5}
        self.assertIn((1, 5, 1), priest)  # 2026_09_06_01.sql UPDATEs this button; the union reader sees the INSERT
        declared = load_dsl(ACTION_FILE)["creation_actions"]
        index = index_for(ACTION, live, emitted=[], base=live)
        emitted_keys = {(r["race"], r["class"], r["button"]) for r in index.rows_to_emit(spec_for(ACTION), declared)}
        self.assertTrue(emitted_keys)
        self.assertFalse([k for k in emitted_keys if k[1] != 6])
        self.assertEqual(index.rows_to_prune(spec_for(ACTION), declared).keys, [])
        with no_migrations():
            live_keys = {(float(r["race"]), float(r["class"]), float(r["button"])) for r in live}
            blocks, _ = spell_tables.render_removal_blocks(load_dsl(ACTION_FILE), {ACTION: live_keys})
        (block,) = [b for b in blocks if ACTION in b]
        self.assertEqual(
            block.splitlines()[-1],
            "DELETE FROM `playercreateinfo_action` WHERE (`race`, `class`, `button`) IN ((10, 6, 6));",
        )


class FirstAidRemovalTest(unittest.TestCase):
    def test_the_live_row_renders_one_key_exact_delete_and_shared_rows_are_never_touched(self):
        live = _Real.get(SKILLS)
        keys = {(float(r["raceMask"]), float(r["classMask"]), float(r["skill"])) for r in live}
        self.assertIn((0.0, 32.0, 129.0), keys)
        self.assertIn((0.0, 35.0, 55.0), keys)  # Two-Handed Swords, shared by warrior / paladin / death knight
        dsl = load_dsl("from lib.dsl.registry import remove_creation_skill\nremove_creation_skill(129, 32)\n")
        with no_migrations():
            blocks, report = spell_tables.render_removal_blocks(dsl, {SKILLS: keys})
        (block,) = [b for b in blocks if SKILLS in b]
        self.assertEqual(
            block.splitlines()[-1],
            "DELETE FROM `playercreateinfo_skills` WHERE (`raceMask`, `classMask`, `skill`) IN ((0, 32, 129));",
        )
        self.assertNotIn("INSERT", block)
        self.assertNotIn("(0, 35, 55)", block)
        self.assertFalse([line for line in report if line.startswith("WARNING")])
        with generated_file(block):
            again, _ = spell_tables.render_removal_blocks(dsl, {SKILLS: keys})
        self.assertEqual([b for b in again if SKILLS in b], [])


class RemovalTest(unittest.TestCase):
    def setUp(self):
        patcher = no_migrations()
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_three_removal_specs_are_keyed_like_their_tables(self):
        for table, removal_key, declared_key in (
            (ACTION, "creation_action_removals", "creation_actions"),
            (CAST, "creation_cast_removals", "creation_casts"),
            (SKILLS, "creation_skill_removals", "creation_skills"),
        ):
            spec = removal_for(table)
            self.assertEqual((spec.removal_key, spec.declared_key), (removal_key, declared_key))
            self.assertEqual(spec.key_columns, spec_for(table).key_columns)

    def test_a_key_that_exists_nowhere_warns(self):
        dsl = load_dsl("from lib.dsl.registry import remove_creation_skill\nremove_creation_skill(999, 32)\n")
        _, report = spell_tables.render_removal_blocks(dsl, {SKILLS: set()})
        self.assertTrue(any(line.startswith("WARNING") and SKILLS in line for line in report))

    def test_declaring_and_removing_the_same_key_raises(self):
        for table, body in (
            (ACTION, "creation_action(1, 6, 0, 1)\nremove_creation_action(1, 6, 0)"),
            (CAST, "creation_cast(5, 32)\nremove_creation_cast(5, 32)"),
            (SKILLS, "creation_skill(129, 32)\nremove_creation_skill(129, 32)"),
        ):
            with self.subTest(table=table):
                dsl = load_dsl(
                    "from lib.dsl.registry import (creation_action, creation_cast, creation_skill, "
                    f"remove_creation_action, remove_creation_cast, remove_creation_skill)\n{body}\n"
                )
                with self.assertRaises(spell_tables.DeclareAndRemoveConflictError):
                    spell_tables.render_removal_blocks(dsl, {table: set()})


class UnknownSpellLintTest(unittest.TestCase):
    ACTION = {"race": 1, "class": 6, "button": 0, "action": 203150, "type": 0}
    CAST = {"raceMask": 0, "classMask": 32, "spell": 203151, "note": None}

    def test_an_unknown_spell_warns(self):
        warnings = lint.check_creation_rows([self.ACTION], [self.CAST], {6603})
        self.assertEqual(len(warnings), 2)
        self.assertIn("creation_action(1, 6, 0, 203150)", warnings[0])
        self.assertIn("creation_cast(203151, 32, 0)", warnings[1])

    def test_known_spells_and_non_spell_buttons_are_silent(self):
        self.assertEqual(lint.check_creation_rows([self.ACTION], [self.CAST], {203150, 203151}), [])
        macro = {**self.ACTION, "type": 0x40, "action": 7}
        self.assertEqual(lint.check_creation_rows([macro], [], set()), [])


if __name__ == "__main__":
    unittest.main()
