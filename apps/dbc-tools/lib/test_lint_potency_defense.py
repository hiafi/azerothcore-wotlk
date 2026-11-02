"""
Unit tests for `lib/lint.py`'s `check_potency_defense_type` (potency audit S1, 2026-11-01).

A potency coefficient on a DmgClass NONE (DefenseType 0) spell with no spell_bonus_data row never applies: the engine's
early return in SpellDamageBonusDone / SpellHealingBonusDone hands back the bare base.

Run directly:

    apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_lint_potency_defense.py -q
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import lint  # noqa: E402

SCHOOL_DAMAGE, HEAL, APPLY_AURA, DUMMY = 2, 10, 6, 3
AURA_PERIODIC_DAMAGE, AURA_PERIODIC_HEAL, AURA_SCHOOL_ABSORB = 3, 8, 69


def _effect(etype=SCHOOL_DAMAGE, aura=0, sp=0.4, ap=0.0):
    return {"type": etype, "apply_aura": aura, "_potency": {"sp_coefficient": sp, "ap_coefficient": ap}}


def _entry(spell_id=999001, defense_type=None, **effects):
    entry = {"id": spell_id, "name": "Fixture", "raw_overrides": {}}
    if defense_type is not None:
        entry["raw_overrides"]["DefenseType"] = defense_type
    entry.update(effects)
    return entry


class PotencyDefenseTypeLint(unittest.TestCase):
    def test_flags_direct_damage_with_defense_type_zero(self):
        errors = lint.check_potency_defense_type([_entry(effect1=_effect())], set())
        self.assertEqual(len(errors), 1)
        self.assertIn("999001", errors[0])

    def test_flags_direct_heal_and_both_effects(self):
        errors = lint.check_potency_defense_type([_entry(effect1=_effect(HEAL), effect2=_effect())], set())
        self.assertEqual(len(errors), 1)
        self.assertIn("effect 0", errors[0])
        self.assertIn("effect 1", errors[0])

    def test_flags_periodic_damage_and_heal_auras(self):
        for aura in (AURA_PERIODIC_DAMAGE, AURA_PERIODIC_HEAL):
            errors = lint.check_potency_defense_type([_entry(effect1=_effect(APPLY_AURA, aura))], set())
            self.assertEqual(len(errors), 1, aura)

    def test_magic_defense_type_passes(self):
        self.assertEqual(lint.check_potency_defense_type([_entry(defense_type=1, effect1=_effect())], set()), [])

    def test_any_nonzero_defense_type_passes(self):
        for dmg_class in (1, 2, 3):
            self.assertEqual(
                lint.check_potency_defense_type([_entry(defense_type=dmg_class, effect1=_effect())], set()), [],
            )

    def test_bonus_row_passes(self):
        self.assertEqual(lint.check_potency_defense_type([_entry(effect1=_effect(ap=0.7))], {999001}), [])

    def test_forced_magic_ids_pass(self):
        for spell_id in (33778, 64844, 379, 52042, 31707, 53652):
            self.assertEqual(lint.check_potency_defense_type([_entry(spell_id, effect1=_effect(HEAL))], set()), [])

    def test_dummy_carrier_and_absorb_are_not_checked(self):
        self.assertEqual(lint.check_potency_defense_type([_entry(effect1=_effect(DUMMY))], set()), [])
        self.assertEqual(
            lint.check_potency_defense_type([_entry(effect1=_effect(APPLY_AURA, AURA_SCHOOL_ABSORB))], set()), [],
        )

    def test_zero_coefficient_and_non_potency_effects_pass(self):
        self.assertEqual(lint.check_potency_defense_type([_entry(effect1=_effect(sp=0.0))], set()), [])
        self.assertEqual(
            lint.check_potency_defense_type([_entry(effect1={"type": SCHOOL_DAMAGE, "apply_aura": 0})], set()), [],
        )

    def test_forced_magic_allow_list_is_ids_only(self):
        self.assertTrue(all(isinstance(spell_id, int) for spell_id in lint.DMG_CLASS_FORCED_MAGIC_IDS))


if __name__ == "__main__":
    unittest.main()
