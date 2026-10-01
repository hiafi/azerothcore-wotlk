"""
Unit tests for potency_report.py (PLAN P3 step 1) - imported via sys.path manipulation since the
script lives at the repo root of apps/dbc-tools/, not under lib/ (it's a standalone report tool,
like potency_report.py's own module docstring says, not part of the generate.py pipeline).
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import potency_report as pr  # noqa: E402
from lib.dsl import constants as C  # noqa: E402


class ClassifyEffectTest(unittest.TestCase):
    def test_school_damage(self):
        self.assertEqual(pr.classify_effect(C.EffectType.SCHOOL_DAMAGE, 0), "direct")

    def test_heal(self):
        self.assertEqual(pr.classify_effect(C.EffectType.HEAL, 0), "heal")

    def test_periodic_damage_aura(self):
        self.assertEqual(
            pr.classify_effect(C.EffectType.APPLY_AURA, C.AuraType.PERIODIC_DAMAGE), "periodic"
        )

    def test_periodic_heal_aura(self):
        self.assertEqual(
            pr.classify_effect(C.EffectType.APPLY_AURA, C.AuraType.PERIODIC_HEAL), "heal_periodic"
        )

    def test_school_absorb_aura(self):
        self.assertEqual(
            pr.classify_effect(C.EffectType.APPLY_AURA, C.AuraType.SCHOOL_ABSORB), "absorb"
        )

    def test_dummy_effect_not_classified(self):
        self.assertIsNone(pr.classify_effect(C.EffectType.DUMMY, 0))

    def test_unrelated_aura_not_classified(self):
        self.assertIsNone(pr.classify_effect(C.EffectType.APPLY_AURA, C.AuraType.MOD_STAT))


class NativeLevel60ValueTest(unittest.TestCase):
    def test_frostbolt_reference_row(self):
        # docs/potency-system.md's Frostbolt reference: base_points=-165, ppl=11.4286, die_sides=1,
        # spell_level=1 -> level 60 roll-averaged value should land at the doc's own 510 (minimum)
        # + 1 (die_sides==1's fixed +1, already inside base_points' own derivation - this checks
        # the *averaged* native value, matching simulate_value's roll=1.0 case exactly since
        # die_sides=1 has no spread).
        v = pr.native_level60_value(-165, 11.4286, 1, spell_level=1, base_level=1, max_level=0)
        self.assertAlmostEqual(v, 510, delta=1)

    def test_die_sides_zero_adds_nothing(self):
        v = pr.native_level60_value(100, 0, 0, spell_level=1, base_level=1, max_level=0)
        self.assertEqual(v, 100)

    def test_die_sides_averages_the_roll(self):
        # DieSides 5 -> irand(1,5), average 3.
        v = pr.native_level60_value(0, 0, 5, spell_level=60, base_level=60, max_level=0)
        self.assertEqual(v, 3.0)

    def test_max_level_clamps(self):
        v80 = pr.native_level60_value(0, 10, 0, spell_level=1, base_level=1, max_level=40)
        # level clamped to 40, then -1 (base_level=1) = 39 effective levels of scaling
        self.assertEqual(v80, 390)


class BuildClassReportTest(unittest.TestCase):
    def _entry(self, spell_id, name="Test Spell", cast_time_ms=1500):
        return {
            "id": spell_id, "name": name, "cast_time_ms": cast_time_ms,
            "effect1": {"type": int(C.EffectType.SCHOOL_DAMAGE)}, "effect2": None, "effect3": None,
        }

    def _live_row(self, **overrides):
        row = {
            "BaseLevel": 1, "SpellLevel": 1, "MaxLevel": 0,
            "Effect_1": int(C.EffectType.SCHOOL_DAMAGE), "EffectAura_1": 0,
            "EffectBasePoints_1": 0, "EffectRealPointsPerLevel_1": 0, "EffectDieSides_1": 0,
            "EffectBonusMultiplier_1": 0.0,
        }
        row.update(overrides)
        return row

    def test_no_mismatch_when_base_and_coefficient_agree(self):
        # Frostbolt-shaped: 100 potency at T=3.0s -> coef 0.857, matching base.
        entry = self._entry(116, "Frostbolt", cast_time_ms=3000)
        live = {116: self._live_row(
            EffectBasePoints_1=-165, EffectRealPointsPerLevel_1=11.4286, EffectDieSides_1=1,
            EffectBonusMultiplier_1=0.857,
        )}
        text, n_rows, n_mismatches, mismatched, n_excluded = pr.build_class_report("mage", [entry], live, {})
        self.assertEqual(n_rows, 1)
        self.assertEqual(n_mismatches, 0)

    def test_mismatch_when_coefficient_is_stale(self):
        # Same base/damage as above, but a coefficient tuned for a much longer cast time (stale,
        # unretuned after a cast-time change) - this is the real Frostbolt/Shadow Bolt bug found
        # live (P3, 2026-10-01): coefficient belongs to the *old* cast time, not the current one.
        entry = self._entry(116, "Frostbolt", cast_time_ms=3000)
        live = {116: self._live_row(
            EffectBasePoints_1=-165, EffectRealPointsPerLevel_1=11.4286, EffectDieSides_1=1,
            EffectBonusMultiplier_1=0.14,
        )}
        text, n_rows, n_mismatches, mismatched, n_excluded = pr.build_class_report("mage", [entry], live, {})
        self.assertEqual(n_mismatches, 1)
        self.assertIn("YES", text)

    def test_spell_bonus_data_row_wins_over_dbc_coefficient(self):
        # D1: a spell_bonus_data row replaces the DBC's own EffectBonusMultiplier entirely.
        entry = self._entry(686, "Shadow Bolt", cast_time_ms=2000)
        live = {686: self._live_row(
            EffectBasePoints_1=11, EffectRealPointsPerLevel_1=7.9661, EffectDieSides_1=5,
            EffectBonusMultiplier_1=0.14,  # would mismatch if used...
        )}
        bonus = {686: {"direct_bonus": 0.857, "dot_bonus": 0, "ap_bonus": 0, "ap_dot_bonus": 0}}
        text, n_rows, n_mismatches, mismatched, n_excluded = pr.build_class_report("warlock", [entry], live, bonus)
        self.assertIn("0.857", text)
        self.assertNotIn("0.14", text)  # the DBC field never shows up - the bonus row won

    def test_already_potency_effect_skipped(self):
        entry = self._entry(90000, "Already Migrated")
        entry["effect1"]["_potency"] = {"kind": "direct"}  # marks it as already converted
        live = {90000: self._live_row()}
        text, n_rows, n_mismatches, mismatched, n_excluded = pr.build_class_report("mage", [entry], live, {})
        self.assertEqual(n_rows, 0)

    def test_missing_live_row_skipped_not_fatal(self):
        entry = self._entry(99999)
        text, n_rows, n_mismatches, mismatched, n_excluded = pr.build_class_report("mage", [entry], {}, {})
        self.assertEqual(n_rows, 0)

    def test_zero_value_effect_skipped(self):
        entry = self._entry(1, "No-op")
        live = {1: self._live_row()}  # all zeros - v60 <= 0
        text, n_rows, n_mismatches, mismatched, n_excluded = pr.build_class_report("mage", [entry], live, {})
        self.assertEqual(n_rows, 0)

    def test_potency_excluded_effect_skipped_and_counted(self):
        # Conflagrate's real shape: a percent-of-other-damage effect (Effect.potency_excluded) -
        # even with a live coefficient that would otherwise mismatch, it's not an unreviewed row.
        entry = self._entry(17962, "Conflagrate")
        entry["effect1"]["_potency_excluded"] = "derived from Immolate/Shadowflame at runtime"
        live = {17962: self._live_row(
            EffectBasePoints_1=-165, EffectRealPointsPerLevel_1=11.4286, EffectDieSides_1=1,
            EffectBonusMultiplier_1=0.14,  # would mismatch if this effect weren't excluded
        )}
        text, n_rows, n_mismatches, mismatched, n_excluded = pr.build_class_report(
            "warlock", [entry], live, {}
        )
        self.assertEqual(n_rows, 0)
        self.assertEqual(n_mismatches, 0)
        self.assertEqual(n_excluded, 1)
        self.assertEqual(mismatched, [])


class ProposalFileTest(unittest.TestCase):
    def test_single_effect_spell_gets_no_eff_suffix(self):
        mismatched = [{"spell_id": 686, "name": "Shadow Bolt", "eff": 1, "proposed": 135.7}]
        text = pr.build_proposal_text(mismatched)
        self.assertEqual(text, "Shadow Bolt (686): 135.7\n")

    def test_multi_effect_spell_gets_eff_suffix_sorted(self):
        mismatched = [
            {"spell_id": 1094, "name": "Immolate", "eff": 2, "proposed": 14.6},
            {"spell_id": 1094, "name": "Immolate", "eff": 1, "proposed": 3.4},
        ]
        text = pr.build_proposal_text(mismatched)
        self.assertEqual(text, "Immolate (1094) eff1: 3.4\nImmolate (1094) eff2: 14.6\n")

    def test_round_trips_through_load_proposal_file(self):
        mismatched = [
            {"spell_id": 686, "name": "Shadow Bolt", "eff": 1, "proposed": 135.7},
            {"spell_id": 1094, "name": "Immolate", "eff": 1, "proposed": 3.4},
            {"spell_id": 1094, "name": "Immolate", "eff": 2, "proposed": 14.6},
        ]
        text = pr.build_proposal_text(mismatched)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "warlock-potency-proposals.txt"
            path.write_text(text, encoding="utf-8")
            result = pr.load_proposal_file(path)
        self.assertEqual(result, {(686, None): 135.7, (1094, 1): 3.4, (1094, 2): 14.6})

    def test_load_proposal_file_honors_hand_edits(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "proposals.txt"
            path.write_text(
                "# comment line, ignored\n"
                "\n"
                "Shadow Bolt (686): 150.0  # hand-overridden from the 135.7 default\n",
                encoding="utf-8",
            )
            result = pr.load_proposal_file(path)
        self.assertEqual(result, {(686, None): 150.0})

    def test_load_proposal_file_rejects_unparseable_line(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "proposals.txt"
            path.write_text("this is not a valid proposal line\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                pr.load_proposal_file(path)


class WriteProposalFileTest(unittest.TestCase):
    """Regression coverage for a real incident: rerunning potency_report.py overwrote a human's
    hand-edited warlock-potency-proposals.txt with fresh defaults, destroying their review. This
    must never happen again without --force-proposals."""

    def test_writes_when_file_does_not_exist(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "proposals.txt"
            wrote = pr.write_proposal_file(path, "Shadow Bolt (686): 135.7\n")
            self.assertTrue(wrote)
            self.assertEqual(path.read_text(encoding="utf-8"), "Shadow Bolt (686): 135.7\n")

    def test_does_not_overwrite_hand_edited_content(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "proposals.txt"
            path.write_text("Shadow Bolt (686): 140.0  # hand-tuned\n", encoding="utf-8")
            wrote = pr.write_proposal_file(path, "Shadow Bolt (686): 135.7\n")
            self.assertFalse(wrote)
            self.assertEqual(path.read_text(encoding="utf-8"), "Shadow Bolt (686): 140.0  # hand-tuned\n")

    def test_force_overwrites_hand_edited_content(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "proposals.txt"
            path.write_text("Shadow Bolt (686): 140.0  # hand-tuned\n", encoding="utf-8")
            wrote = pr.write_proposal_file(path, "Shadow Bolt (686): 135.7\n", force=True)
            self.assertTrue(wrote)
            self.assertEqual(path.read_text(encoding="utf-8"), "Shadow Bolt (686): 135.7\n")

    def test_rewrites_when_content_is_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "proposals.txt"
            path.write_text("Shadow Bolt (686): 135.7\n", encoding="utf-8")
            wrote = pr.write_proposal_file(path, "Shadow Bolt (686): 135.7\n")
            self.assertTrue(wrote)


if __name__ == "__main__":
    unittest.main()
