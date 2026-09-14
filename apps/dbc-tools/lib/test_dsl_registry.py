"""
Unit tests for `lib/dsl/registry.py` - Phase 1 of `.agents/plans/
spell-source-dsl/spell-source-dsl.PLAN.md`. Uses real temp `.py` files
(not mocks) since the thing under test *is* "import this file from disk and
see what it registered".

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_dsl_registry.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib.dsl import registry  # noqa: E402

MAGE_FILE = '''
from lib.dsl.registry import spell, tab, talent

frostbolt = spell(id=116, name="Frostbolt", school=16, cast_time_ms=2000)

frost_tab = tab(id=60800, name="Frost", class_mask=128)

t = talent(id=60000, tab_id=frost_tab.id, tier=0, column=0, rank_spell_ids=[frostbolt.id])
'''

WARRIOR_FILE = '''
from lib.dsl.registry import spell

charge = spell(id=100, name="Charge", school=1)
'''

DUPLICATE_FILE = '''
from lib.dsl.registry import spell

impostor = spell(id=116, name="Not Actually Frostbolt", school=1)
'''

SKIPPED_FILE = '''
from lib.dsl.registry import spell

# If this ever gets loaded, it'll collide with mage.py's real Frostbolt (116)
# and the test would fail loudly instead of silently passing - that's the
# point: proves leading-underscore files are actually skipped, not merely
# assumed to be.
spell(id=116, name="Should never be imported", school=1)
'''


IDS_CFG = {"spell": {"start": 200000, "end": 209999}}

# A custom (in-reserved-block) spell ID, real cast_time_ms, correctly marked
# player_castable=True with a matching skill_line_ability id - the "did it
# correctly" case.
GRANTED_CUSTOM_CASTABLE = '''
from lib.dsl.registry import spell, tab, granted_by_talent

frost_tab = tab(id=60800, name="Frost", class_mask=128, skill_line=6)
frostbolt = spell(id=200001, name="Custom Frostbolt", school=16, cast_time_ms=2000)
granted_by_talent(
    id=60000, tab=frost_tab, tier=0, column=0,
    ranks=[frostbolt], player_castable=True, skill_line_ability_ids=[30400],
)
'''

# A reused stock spell ID (outside the reserved block) that "looks castable"
# (real cast_time_ms) but player_castable is left unset - must NOT raise,
# since a stock ID already has its own real SkillLineAbility row for free.
GRANTED_STOCK_ID_NO_DECISION_NEEDED = '''
from lib.dsl.registry import spell, tab, granted_by_talent

frost_tab = tab(id=60800, name="Frost", class_mask=128, skill_line=6)
frostbolt = spell(id=116, name="Frostbolt", school=16, cast_time_ms=2000)
granted_by_talent(id=60000, tab=frost_tab, tier=0, column=0, ranks=[frostbolt])
'''

# A bare-int rank (no Spell() declaration at all) mixed with a real one -
# the Phase 4 real-data case (some old stock talent ranks were never pulled
# into source). Must not crash, and must not need a decision for the bare
# int (only the real Spell still might, depending on its own shape).
GRANTED_BARE_INT_RANK_MIXED_WITH_SPELL = '''
from lib.dsl.registry import spell, tab, granted_by_talent

frost_tab = tab(id=60800, name="Frost", class_mask=128, skill_line=6)
frostbolt = spell(id=116, name="Frostbolt", school=16, cast_time_ms=2000)
granted_by_talent(id=60000, tab=frost_tab, tier=0, column=0, ranks=[29447, frostbolt])
'''

# A custom, castable-looking spell ID with player_castable left unset - the
# exact ambiguity that must hard-fail rather than silently default.
GRANTED_CUSTOM_AMBIGUOUS = '''
from lib.dsl.registry import spell, tab, granted_by_talent

frost_tab = tab(id=60800, name="Frost", class_mask=128, skill_line=6)
frostbolt = spell(id=200002, name="Custom Frostbolt", school=16, cast_time_ms=2000)
granted_by_talent(id=60000, tab=frost_tab, tier=0, column=0, ranks=[frostbolt])
'''

# A custom, castable-looking spell ID explicitly marked player_castable=False
# (a hidden triggered effect that happens to have a cast_time/cooldown for
# some other reason) - must NOT raise and must NOT register a row.
GRANTED_CUSTOM_NOT_CASTABLE = '''
from lib.dsl.registry import spell, tab, granted_by_talent

frost_tab = tab(id=60800, name="Frost", class_mask=128, skill_line=6)
icicles = spell(id=200003, name="Icicles", school=16, cast_time_ms=1500)
granted_by_talent(id=60000, tab=frost_tab, tier=0, column=0,
                   ranks=[icicles], player_castable=False)
'''

# player_castable=True but no skill_line_ability_ids entry for the rank.
GRANTED_CUSTOM_MISSING_SLA_ID = '''
from lib.dsl.registry import spell, tab, granted_by_talent

frost_tab = tab(id=60800, name="Frost", class_mask=128, skill_line=6)
frostbolt = spell(id=200004, name="Custom Frostbolt", school=16, cast_time_ms=2000)
granted_by_talent(id=60000, tab=frost_tab, tier=0, column=0,
                   ranks=[frostbolt], player_castable=True)
'''


class GrantedByTalentTest(unittest.TestCase):
    def _load(self, source: str, ids_cfg=IDS_CFG):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "mage.py"
            path.write_text(source)
            return registry.load_class_file(path, ids_cfg=ids_cfg)

    def test_derives_skill_line_ability_for_custom_castable_spell(self):
        reg = self._load(GRANTED_CUSTOM_CASTABLE)
        self.assertEqual(len(reg.skill_line_abilities), 1)
        sla = reg.skill_line_abilities[0]
        self.assertEqual(sla["id"], 30400)
        self.assertEqual(sla["skill_line"], 6)
        self.assertEqual(sla["spell_id"], 200001)
        self.assertEqual(sla["class_mask"], 128)

    def test_stock_id_needs_no_decision(self):
        reg = self._load(GRANTED_STOCK_ID_NO_DECISION_NEEDED)
        self.assertEqual(reg.skill_line_abilities, [])

    def test_bare_int_rank_mixed_with_spell_does_not_crash(self):
        reg = self._load(GRANTED_BARE_INT_RANK_MIXED_WITH_SPELL)
        self.assertEqual(reg.talents[0]["rank_spell_ids"], [29447, 116])
        self.assertEqual(reg.skill_line_abilities, [])

    def test_custom_castable_ambiguous_raises(self):
        with self.assertRaises(registry.MissingSkillLineAbilityError):
            self._load(GRANTED_CUSTOM_AMBIGUOUS)

    def test_custom_marked_not_castable_is_skipped(self):
        reg = self._load(GRANTED_CUSTOM_NOT_CASTABLE)
        self.assertEqual(reg.skill_line_abilities, [])

    def test_missing_skill_line_ability_id_raises(self):
        with self.assertRaises(ValueError):
            self._load(GRANTED_CUSTOM_MISSING_SLA_ID)

    def test_missing_ids_cfg_raises(self):
        with self.assertRaises(RuntimeError):
            self._load(GRANTED_CUSTOM_CASTABLE, ids_cfg=None)


class FakeTrainerIndex:
    """Duck-typed stand-in for lib.trainer_state.TrainerIndex - registry.py
    never imports the real class (see load_class_file's docstring), so a
    fake with the same two-member surface is all trained_by() needs to
    exercise without dragging in a real SQL-file scan."""

    def __init__(self, dead_trainer_ids: set[int] = frozenset(), existing: dict | None = None):
        self._dead = dead_trainer_ids
        self.existing_trainer_spells = existing or {}

    def trainer_problems(self, trainer_id: int) -> list[str]:
        return [f"TrainerId {trainer_id} is dead"] if trainer_id in self._dead else []


TRAINED_BY_FILE = '''
from lib.dsl.registry import spell, trained_by

frostbolt = spell(id=200005, name="Frostbolt", school=16, cast_time_ms=2000)
trained_by(frostbolt, trainer_id=13, req_level=20, money_cost=500)
'''

TRAINED_BY_DEAD_TRAINER_FILE = '''
from lib.dsl.registry import spell, trained_by

frostbolt = spell(id=200006, name="Frostbolt", school=16, cast_time_ms=2000)
trained_by(frostbolt, trainer_id=666, req_level=20)
'''


class TrainedByTest(unittest.TestCase):
    def _load(self, source: str, trainer_index):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "mage.py"
            path.write_text(source)
            return registry.load_class_file(path, trainer_index=trainer_index)

    def test_registers_trainer_spell_row_for_a_live_trainer(self):
        reg = self._load(TRAINED_BY_FILE, FakeTrainerIndex())
        self.assertEqual(len(reg.trainer_spells), 1)
        row = reg.trainer_spells[0]
        self.assertEqual(row["TrainerId"], 13)
        self.assertEqual(row["SpellId"], 200005)
        self.assertEqual(row["MoneyCost"], 500)
        self.assertEqual(row["ReqLevel"], 20)
        self.assertEqual(row["id"], "13:200005")

    def test_dead_trainer_raises(self):
        with self.assertRaises(registry.DeadTrainerError):
            self._load(TRAINED_BY_DEAD_TRAINER_FILE, FakeTrainerIndex(dead_trainer_ids={666}))

    def test_missing_trainer_index_raises(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "mage.py"
            path.write_text(TRAINED_BY_FILE)
            with self.assertRaises(RuntimeError):
                registry.load_class_file(path)  # no trainer_index passed


class RegistryTest(unittest.TestCase):
    def test_spell_call_outside_load_raises(self):
        with self.assertRaises(RuntimeError):
            registry.spell(id=1, name="Nothing")

    def test_load_class_file_collects_declarations(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "mage.py"
            path.write_text(MAGE_FILE)
            reg = registry.load_class_file(path)
        self.assertEqual([e["id"] for e in reg.spells], [116])
        self.assertEqual([e["id"] for e in reg.tabs], [60800])
        self.assertEqual([e["id"] for e in reg.talents], [60000])
        self.assertEqual(reg.talents[0]["tab_id"], 60800)

    def test_active_registry_cleared_after_load(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "mage.py"
            path.write_text(MAGE_FILE)
            registry.load_class_file(path)
        self.assertIsNone(registry._active)

    def test_load_classes_dir_merges_multiple_files(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "mage.py").write_text(MAGE_FILE)
            (Path(d) / "warrior.py").write_text(WARRIOR_FILE)
            merged = registry.load_classes_dir(Path(d))
        self.assertEqual(sorted(e["id"] for e in merged["spells"]), [100, 116])
        self.assertEqual([e["id"] for e in merged["tabs"]], [60800])

    def test_load_classes_dir_skips_underscore_files(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "mage.py").write_text(MAGE_FILE)
            (Path(d) / "_example.py").write_text(SKIPPED_FILE)
            merged = registry.load_classes_dir(Path(d))
        self.assertEqual(len(merged["spells"]), 1)

    def test_load_classes_dir_missing_directory_returns_empty(self):
        merged = registry.load_classes_dir(Path("/nonexistent/does/not/exist"))
        self.assertEqual(merged, {key: [] for key in registry.MERGE_KEYS})

    def test_load_classes_dir_duplicate_id_across_files_raises(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "mage.py").write_text(MAGE_FILE)
            (Path(d) / "zzz_conflict.py").write_text(DUPLICATE_FILE)
            with self.assertRaises(registry.DuplicateIdError):
                registry.load_classes_dir(Path(d))


if __name__ == "__main__":
    unittest.main()
