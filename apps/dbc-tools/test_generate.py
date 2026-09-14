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


class _FakeTrainerIndex:
    def __init__(self, existing: dict):
        self.existing_trainer_spells = existing


TRAINER_SPELL_ROW = {
    "id": "13:200005", "TrainerId": 13, "SpellId": 200005, "MoneyCost": 500,
    "ReqSkillLine": 0, "ReqSkillRank": 0, "ReqAbility1": 0, "ReqAbility2": 0,
    "ReqAbility3": 0, "ReqLevel": 20, "VerifiedBuild": 0,
}


class TrainerSpellsToEmitTest(unittest.TestCase):
    def test_new_grant_is_emitted(self):
        idx = _FakeTrainerIndex(existing={})
        self.assertEqual(generate._trainer_spells_to_emit([TRAINER_SPELL_ROW], idx), [TRAINER_SPELL_ROW])

    def test_identical_existing_grant_is_not_re_emitted(self):
        idx = _FakeTrainerIndex(existing={(13, 200005): dict(TRAINER_SPELL_ROW)})
        self.assertEqual(generate._trainer_spells_to_emit([TRAINER_SPELL_ROW], idx), [])

    def test_changed_existing_grant_is_re_emitted(self):
        existing = dict(TRAINER_SPELL_ROW)
        existing["ReqLevel"] = 55  # source now wants a different level
        idx = _FakeTrainerIndex(existing={(13, 200005): existing})
        self.assertEqual(generate._trainer_spells_to_emit([TRAINER_SPELL_ROW], idx), [TRAINER_SPELL_ROW])


if __name__ == "__main__":
    unittest.main()
