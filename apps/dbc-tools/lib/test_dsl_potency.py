"""
Unit tests for the potency system's DSL wiring (docs/potency-system.md, PLAN P2 step 2) -
lib.dsl.model.Spell._resolve_potency() and lib.dsl.registry.spell()'s auto-emission of
spell_bonus_data/spell_potency_correction rows. lib/test_potency.py already proves the underlying
math reproduces the design doc's own reference tables; this file proves the DSL glue (Effect ->
Spell.to_entry() -> registry.spell()) wires that math to the right dict keys.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import potency
from lib.dsl import model, registry


class SpellPotencyResolutionTest(unittest.TestCase):
    """Direct Spell().to_entry() calls - no registry needed for the per-effect DBC-field math."""

    def test_direct_damage_effect_generates_dbc_fields(self):
        s = model.Spell(
            id=90000, name="Test Bolt", cast_time_ms=3000,
            effects=[model.Effect(type=2, sp_potency=100, potency_kind=potency.KIND_DIRECT)],
            raw_overrides={"SpellLevel": 1},
        )
        entry = s.to_entry()
        self.assertEqual(entry["effect1"]["base_points"], -165)
        self.assertAlmostEqual(entry["effect1"]["points_per_level"], 11.4286, places=3)
        self.assertEqual(entry["effect1"]["die_sides"], 1)
        self.assertEqual(entry["raw_overrides"]["BaseLevel"], 1)
        self.assertEqual(entry["raw_overrides"]["MaxLevel"], 0)
        self.assertAlmostEqual(entry["raw_overrides"]["EffectBonusMultiplier_1"], 0.857, places=3)
        self.assertEqual(len(s.potency_correction_rows), 1)
        row = s.potency_correction_rows[0]
        self.assertEqual((row["spell_id"], row["effect_index"]), (90000, 0))
        self.assertAlmostEqual(row["correction_per_level"], 8.3095, places=3)
        self.assertEqual(row["breakpoint_level"], 25)
        self.assertEqual(row["variance_pct"], 10.0)
        self.assertIsNone(s.potency_bonus_row)  # no ap_potency on this spell

    def test_base_potency_overrides_base_without_touching_coefficient(self):
        default = model.Spell(
            id=90008, name="Test Base Bolt (default)", cast_time_ms=1500,
            effects=[model.Effect(type=2, sp_potency=50, potency_kind=potency.KIND_DIRECT)],
            raw_overrides={"SpellLevel": 1},
        ).to_entry()
        overridden = model.Spell(
            id=90009, name="Test Base Bolt (overridden)", cast_time_ms=1500,
            effects=[model.Effect(
                type=2, sp_potency=50, potency_kind=potency.KIND_DIRECT, base_potency=120,
            )],
            raw_overrides={"SpellLevel": 1},
        ).to_entry()
        self.assertNotEqual(overridden["effect1"]["base_points"], default["effect1"]["base_points"])
        self.assertAlmostEqual(
            overridden["raw_overrides"]["EffectBonusMultiplier_1"],
            default["raw_overrides"]["EffectBonusMultiplier_1"], places=6,
        )

    def test_missing_spell_level_raises(self):
        s = model.Spell(
            id=90001, name="Bad Bolt", cast_time_ms=1500,
            effects=[model.Effect(type=2, sp_potency=50)],
        )
        with self.assertRaises(ValueError):
            s.to_entry()

    def test_hand_written_base_points_alongside_potency_raises(self):
        s = model.Spell(
            id=90002, name="Conflicting Bolt", cast_time_ms=1500,
            effects=[model.Effect(type=2, sp_potency=50, base_points=10)],
            raw_overrides={"SpellLevel": 1},
        )
        with self.assertRaises(ValueError):
            s.to_entry()

    def test_hybrid_effect_emits_bonus_row(self):
        # sp_potency=ap_potency=35 at the measured R=1.0 (DEFAULT_R) reproduces Exorcism/Hammer of
        # Wrath's symmetric 0.15/0.15 split - potency-system.md's "Hybrid spells" (P3, 2026-10-01).
        s = model.Spell(
            id=90003, name="Test Exorcism", cast_time_ms=1500,
            effects=[model.Effect(type=2, sp_potency=35, ap_potency=35)],
            raw_overrides={"SpellLevel": 1},
        )
        s.to_entry()
        self.assertIsNotNone(s.potency_bonus_row)
        self.assertAlmostEqual(s.potency_bonus_row["direct_bonus"], 0.15, places=2)
        self.assertAlmostEqual(s.potency_bonus_row["ap_bonus"], 0.15, places=2)
        self.assertEqual(s.potency_bonus_row["dot_bonus"], 0.0)
        self.assertEqual(s.potency_bonus_row["ap_dot_bonus"], 0.0)

    def test_periodic_effect_uses_amplitude_not_cast_time(self):
        s = model.Spell(
            id=90004, name="Test Corruption", cast_time_ms=0, duration_ms=18000,
            effects=[
                model.Effect(
                    type=6, apply_aura=3, amplitude=3000,
                    sp_potency=23, potency_kind=potency.KIND_PERIODIC,
                )
            ],
            raw_overrides={"SpellLevel": 1},
        )
        entry = s.to_entry()
        self.assertEqual(entry["effect1"]["base_points"], -40)
        self.assertAlmostEqual(entry["effect1"]["points_per_level"], 2.76, places=2)
        row = s.potency_correction_rows[0]
        self.assertEqual(row["variance_pct"], 0.0)  # periodic - no roll

    def test_weapon_potency_skips_correction_and_bonus_data(self):
        s = model.Spell(
            id=90005, name="Test Strike", cast_time_ms=0,
            effects=[model.Effect(type=38, weapon_potency=100)],
            raw_overrides={"SpellLevel": 1},
        )
        entry = s.to_entry()
        # 99, not 100: die_sides=1 means the live engine adds its own "+1" at cast time (every
        # potency effect's convention) - simulate_value (lib/test_potency.py's WeaponPotencyTest)
        # confirms this reproduces a live value of exactly 100.
        self.assertEqual(entry["effect1"]["base_points"], 99)
        self.assertEqual(entry["effect1"]["points_per_level"], 0.0)
        self.assertEqual(s.potency_correction_rows, [])
        self.assertIsNone(s.potency_bonus_row)
        self.assertNotIn("EffectBonusMultiplier_1", entry["raw_overrides"])

    def test_weapon_potency_with_flat_bonus_emits_correction_and_dbc_coefficient(self):
        """Unlike a pure weapon_potency effect, a weapon_potency + flat sp_potency bonus DOES need
        a correction row and a real EffectBonusMultiplier_1 - the flat part is "ordinary spell
        potency on C(L)" riding on the same effect ("Weapon attacks")."""
        s = model.Spell(
            id=90010, name="Test Weapon Strike (flat bonus)", cast_time_ms=0,
            effects=[model.Effect(type=38, weapon_potency=100, sp_potency=10)],
            raw_overrides={"SpellLevel": 1},
        )
        entry = s.to_entry()
        self.assertEqual(len(s.potency_correction_rows), 1)
        row = s.potency_correction_rows[0]
        self.assertEqual(row["variance_pct"], 0.0)  # "no variance roll" even though direct kind
        self.assertIsNone(s.potency_bonus_row)  # no ap_potency involved - DBC field wins, not spell_bonus_data
        self.assertIn("EffectBonusMultiplier_1", entry["raw_overrides"])
        self.assertGreater(entry["raw_overrides"]["EffectBonusMultiplier_1"], 0.0)
        # The exact numeric equivalence (100 + a 10-potency flat direct effect's own live value, at
        # every level) is proven once in lib/test_potency.py's WeaponPotencyWithFlatBonusTest - this
        # test only needs to confirm the DSL wiring (correction row + DBC coefficient) is reachable.

    def test_finisher_emits_cp_correction_columns_and_zeroes_points_per_combo(self):
        """cp_sp_potency/cp_ap_potency (PLAN P6 step 4, "Combo points don't scale with level") land
        in the correction row's cp_line/cp_correction_per_level/cp_ap - not the DBC, which has no
        per-level field for EffectPointsPerCombo_N at all - and that DBC field is always forced to 0
        so SpellPotency::Apply()'s combo-point term is the only one applied, never both."""
        s = model.Spell(
            id=90011, name="Test Finisher", cast_time_ms=0,
            effects=[model.Effect(type=2, ap_potency=19.5, cp_ap_potency=30.8, implicit_target_a=6)],
            raw_overrides={"SpellLevel": 1},
        )
        entry = s.to_entry()
        self.assertEqual(entry["raw_overrides"]["EffectPointsPerCombo_1"], 0)
        self.assertEqual(len(s.potency_correction_rows), 1)
        row = s.potency_correction_rows[0]
        self.assertGreater(row["cp_line"], 0.0)
        self.assertGreater(row["cp_correction_per_level"], 0.0)
        self.assertGreater(row["cp_ap"], 0.0)

    def test_finisher_flat_ap_potency_still_emits_bonus_row(self):
        s = model.Spell(
            id=90012, name="Test Finisher (flat ap_bonus)", cast_time_ms=0,
            effects=[model.Effect(type=2, ap_potency=19.5, cp_ap_potency=30.8, implicit_target_a=6)],
            raw_overrides={"SpellLevel": 1},
        )
        s.to_entry()
        self.assertIsNotNone(s.potency_bonus_row)
        self.assertAlmostEqual(s.potency_bonus_row["ap_bonus"], 19.5 / 100.0 * (1.5 / 3.5), places=4)

    def test_finisher_cp_base_potency_decouples_line_from_ap_coefficient(self):
        """cp_base_potency (PLAN P6 step 5, Ferocious Bite) overrides cp_line independently of
        cp_ap - a bare cp_ap_potency ties the two at a fixed ratio (C60 / ((1/100)*(t/3.5)/r)),
        which doesn't match every stock finisher's own flat/AP split (docs/potency-system.md's
        worked Ferocious Bite derivation: 36 flat vs 0.07 AP per combo point don't share that
        ratio). cp_ap_potency=16.333 alone should give cp_ap=0.07; cp_base_potency=13.458 should
        then independently pin cp_line to 36, matching lib.potency.resolve's own base_potency
        override for the flat line."""
        s = model.Spell(
            id=90014, name="Test Finisher (cp_base_potency)", cast_time_ms=0,
            effects=[model.Effect(type=2, base_potency=31.0, cp_ap_potency=16.333, cp_base_potency=13.458, implicit_target_a=6)],
            raw_overrides={"SpellLevel": 1},
        )
        entry = s.to_entry()
        self.assertEqual(entry["raw_overrides"]["EffectPointsPerCombo_1"], 0)
        row = s.potency_correction_rows[0]
        self.assertAlmostEqual(row["cp_ap"], 0.07, places=3)
        self.assertAlmostEqual(row["cp_line"], 36.0, delta=0.1)

    def test_cp_potency_rejects_combination_with_weapon_potency(self):
        s = model.Spell(
            id=90013, name="Bad Weapon Finisher", cast_time_ms=0,
            effects=[model.Effect(type=38, weapon_potency=100, cp_ap_potency=10)],
            raw_overrides={"SpellLevel": 1},
        )
        with self.assertRaises(ValueError):
            s.to_entry()

    def test_description_placeholder_expansion(self):
        s = model.Spell(
            id=90006, name="Test Bolt", cast_time_ms=3000,
            effects=[model.Effect(type=2, sp_potency=100)],
            raw_overrides={"SpellLevel": 1, "Description_Lang_enUS": "Deals {pot1} damage."},
        )
        entry = s.to_entry()
        text = entry["raw_overrides"]["Description_Lang_enUS"]
        self.assertNotIn("{pot1}", text)
        self.assertIn("${$max($max(", text)
        self.assertIn(" to ${$max($max(", text)
        self.assertIn("*$SP", text)

    def test_mismatched_direct_sp_coefficient_across_effects_raises(self):
        # Both effects carry ap_potency but at different cast-time-derived coefficients - D6 says
        # spell_bonus_data has one direct_bonus for the whole spell, so this must be rejected
        # rather than silently picking one.
        s = model.Spell(
            id=90007, name="Bad Hybrid", cast_time_ms=1500,
            effects=[
                model.Effect(type=2, sp_potency=35, ap_potency=70, time_basis_ms=1500),
                model.Effect(type=2, sp_potency=35, ap_potency=70, time_basis_ms=2500),
            ],
            raw_overrides={"SpellLevel": 1},
        )
        with self.assertRaises(ValueError):
            s.to_entry()


class PotencyExcludedTest(unittest.TestCase):
    """Effect.potency_excluded - the escape hatch for a percent-of-other-damage effect like
    Conflagrate, whose real damage is computed by its own SpellScript at runtime and whose DBC
    EffectBasePoints/EffectBonusMultiplier fields are dead (potency_report.py reads this to skip
    the row entirely instead of printing a meaningless implied potency for it)."""

    def test_sets_dict_marker(self):
        effect = model.Effect(type=2, potency_excluded="derived from Immolate at runtime")
        self.assertEqual(
            effect.to_dict()["_potency_excluded"], "derived from Immolate at runtime"
        )

    def test_unset_by_default(self):
        effect = model.Effect(type=2)
        self.assertNotIn("_potency_excluded", effect.to_dict())

    def test_combined_with_sp_potency_raises(self):
        effect = model.Effect(type=2, sp_potency=50, potency_excluded="derived at runtime")
        with self.assertRaises(ValueError):
            effect.to_dict()

    def test_combined_with_weapon_potency_raises(self):
        effect = model.Effect(type=2, weapon_potency=10, potency_excluded="derived at runtime")
        with self.assertRaises(ValueError):
            effect.to_dict()


class RegistrySpellAutoEmissionTest(unittest.TestCase):
    """registry.spell() end to end, via a real temp class file - proves a potency effect can't
    forget its spell_bonus_data/spell_potency_correction row the way a hand-written
    bonus_coefficients() call could."""

    def test_hybrid_spell_auto_emits_bonus_row_and_correction_row(self):
        import tempfile

        source = '''
from lib.dsl.registry import spell
from lib.dsl.model import Effect

exorcism = spell(
    id=90100, name="Test Exorcism", cast_time_ms=1500,
    effects=[Effect(type=2, sp_potency=35, ap_potency=70)],
    raw_overrides={"SpellLevel": 1},
)
'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "potency_test_class.py"
            path.write_text(source)
            reg = registry.load_class_file(path)
        self.assertEqual(len(reg.spells), 1)
        self.assertEqual(len(reg.spell_bonus_data), 1)
        self.assertEqual(reg.spell_bonus_data[0]["entry"], 90100)
        self.assertEqual(len(reg.potency_corrections), 1)
        self.assertEqual(reg.potency_corrections[0]["spell_id"], 90100)


if __name__ == "__main__":
    unittest.main()
