"""
Typed `acquire_method` / `superseded_by` on `skill_line_ability()` (hunter-rework SHARED §C7.2, T1 step 1).
Fixtures only.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_acquire_method.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, dbcfile, dbcfmt, superseded_ranks  # noqa: E402
from lib.dsl import AcquireMethod, registry  # noqa: E402

PET_ABILITY_FILE = '''
from lib.dsl.registry import AcquireMethod, skill_line_ability

pet_bite = skill_line_ability(
    id=30990, skill_line=270, spell_id=17253, acquire_method=AcquireMethod.LEARNED_ON_SKILL_LEARN,
    superseded_by=17255,
)
plain = skill_line_ability(id=30991, skill_line=270, spell_id=17254)
'''


def _load(source: str) -> registry.Registry:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "hunter.py"
        path.write_text(source)
        return registry.load_class_file(path)


class AcquireMethodTest(unittest.TestCase):
    def test_enum_values_match_the_core_enum(self):
        self.assertEqual(
            [AcquireMethod.NONE, AcquireMethod.LEARNED_ON_SKILL_VALUE, AcquireMethod.LEARNED_ON_SKILL_LEARN],
            [0, 1, 2],
        )
        self.assertEqual(superseded_ranks.SKILL_LINE_ABILITY_LEARNED_ON_SKILL_LEARN, AcquireMethod.LEARNED_ON_SKILL_LEARN)

    def test_pet_ability_row_carries_the_typed_columns(self):
        reg = _load(PET_ABILITY_FILE)
        row = build.build_skilllineability_row(reg.skill_line_abilities[0])
        self.assertEqual(row["AcquireMethod"], 2)
        self.assertEqual(row["SupercededBySpell"], 17255)
        self.assertEqual((row["SkillLine"], row["Spell"]), (270, 17253))

    def test_acquire_method_none_value_is_emitted_not_skipped(self):
        # NONE (0) is a real choice (retire_pet_spell emits it); only `None` means "not declared".
        entry = registry.model.SkillLineAbility(id=1, skill_line=270, spell_id=5, acquire_method=0).to_entry()
        self.assertEqual(entry["acquire_method"], 0)

    def test_row_with_neither_field_is_byte_identical_to_before(self):
        reg = _load(PET_ABILITY_FILE)
        entry = reg.skill_line_abilities[1]
        self.assertNotIn("acquire_method", entry)
        self.assertNotIn("superseded_by", entry)
        legacy = {"id": 30991, "skill_line": 270, "spell_id": 17254, "class_mask": 0, "race_mask": 0,
                  "min_skill_line_rank": 1, "raw_overrides": None}
        self.assertEqual(entry, legacy)
        expected = dbcfile.empty_row(dbcfmt.SKILLLINEABILITY)
        expected.update(ID=30991, SkillLine=270, Spell=17254, MinSkillLineRank=1)
        self.assertEqual(build.build_skilllineability_row(entry), expected)

    def test_raw_overrides_still_win(self):
        entry = {"id": 1, "skill_line": 270, "spell_id": 5, "acquire_method": 2, "raw_overrides": {"AcquireMethod": 1}}
        self.assertEqual(build.build_skilllineability_row(entry)["AcquireMethod"], 1)

    def test_declared_row_beats_a_superseded_rank_override(self):
        # Stock row 4371 teaches superseded rank 7799; the declaration (typed, AcquireMethod 2 kept) wins.
        chains = {3110: [(3110, 1), (7799, 2)]}
        spells = [{"id": 3110, "notes": "single-rank bootstrap"}]
        stock = dbcfile.empty_row(dbcfmt.SKILLLINEABILITY)
        stock.update(ID=4371, SkillLine=188, Spell=7799, MinSkillLineRank=1, AcquireMethod=2)
        declared = [registry.model.SkillLineAbility(
            id=4371, skill_line=188, spell_id=7799, acquire_method=AcquireMethod.LEARNED_ON_SKILL_LEARN,
        ).to_entry()]
        result = superseded_ranks.skilllineability_overrides(chains, spells, {4371: stock}, declared)
        self.assertEqual(result.entries, [])
        self.assertEqual(len(result.collisions), 1)
        self.assertIn("4371", result.collisions[0])
        self.assertIn("declared row wins", result.collisions[0])


if __name__ == "__main__":
    unittest.main()
