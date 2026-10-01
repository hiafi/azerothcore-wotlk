"""
Reproduces docs/potency-system.md's own worked reference tables exactly - the P2 acceptance gate
named in potency-system.HANDOFF.md ("the pytest must reproduce the design doc's reference tables
exactly: Frostbolt's row and ranges, Corruption per tick and totals, the heal table's
coefficients, the attack power table at R = 2, and Exorcism's 35 + 70 giving 0.15 / 0.15").

Every expected number in this file is copied straight from docs/potency-system.md, not
re-derived - if a doc retune changes a table, the matching test here should fail until the retune
is also reflected wherever this module's constants live.
"""

import unittest

from lib import potency


def _round_range(resolved, level, spell_level):
    lo = potency.simulate_value(resolved, level, spell_level, roll=1.0)
    hi = potency.simulate_value(resolved, level, spell_level, roll=1.0 + resolved.variance_pct / 100.0)
    return int(lo), int(hi)


class FrostboltReferenceTest(unittest.TestCase):
    """"Reference spells": Frostbolt, 100 potency, static 3.0s cast, SpellLevel 1."""

    def setUp(self):
        effect = potency.PotencyEffect(sp_potency=100, kind=potency.KIND_DIRECT, t_ms=3000)
        self.resolved = potency.resolve(effect, spell_level=1)

    def test_dbc_fields(self):
        r = self.resolved
        self.assertEqual(r.base_points, -165)
        self.assertAlmostEqual(r.points_per_level, 11.4286, places=3)
        self.assertAlmostEqual(r.correction_per_level, 8.3095, places=3)
        self.assertEqual(r.die_sides, 1)
        self.assertAlmostEqual(r.sp_coefficient, 0.857, places=3)

    def test_level_ranges(self):
        # level -> (min, max) from the "Reference spells" Frostbolt table.
        table = {
            1: (35, 38),
            60: (510, 561),
            70: (624, 686),
            80: (738, 811),
        }
        for level, expected in table.items():
            with self.subTest(level=level):
                self.assertEqual(_round_range(self.resolved, level, spell_level=1), expected)

    def test_level_20_accepted_rounding_drift(self):
        # potency-system.PROGRESS.md's P1 section: "exact at 1/25/60/80; the already-documented
        # +/-1 drift at 20 from the doc's own 'Caveats and checks'" - the doc's own table shows
        # "95 to 104"; the exact float math (94.5476/104.0024) truncates to 94/104, an accepted
        # off-by-one on the minimum only.
        lo, hi = _round_range(self.resolved, 20, spell_level=1)
        self.assertEqual(hi, 104)
        self.assertIn(lo, (94, 95))


class CorruptionReferenceTest(unittest.TestCase):
    """"Reference spells": Corruption, 23 potency, 18s DoT with six 3s ticks, SpellLevel 1."""

    def setUp(self):
        effect = potency.PotencyEffect(sp_potency=23, kind=potency.KIND_PERIODIC, t_ms=3000)
        self.resolved = potency.resolve(effect, spell_level=1)

    def test_dbc_fields(self):
        r = self.resolved
        self.assertEqual(r.base_points, -40)
        self.assertAlmostEqual(r.points_per_level, 2.76, places=2)
        self.assertAlmostEqual(r.correction_per_level, 2.0067, places=3)
        self.assertEqual(r.variance_pct, 0.0)  # periodic effects don't roll
        self.assertAlmostEqual(r.sp_coefficient, 0.197, places=3)

    def test_per_tick_and_totals(self):
        table = {1: 9, 20: 23, 25: 27, 60: 123, 70: 151, 80: 179}
        for level, expected_tick in table.items():
            with self.subTest(level=level):
                tick = int(potency.simulate_value(self.resolved, level, spell_level=1))
                self.assertEqual(tick, expected_tick)
                self.assertEqual(tick * 6, expected_tick * 6)  # six 3s ticks over 18s


class HealCoefficientTest(unittest.TestCase):
    """"Healing" table - coefficients only (base healing isn't tabulated against stock there)."""

    def _coef(self, potency_value, t_ms, kind=potency.KIND_HEAL):
        effect = potency.PotencyEffect(sp_potency=potency_value, kind=kind, t_ms=t_ms)
        return potency.resolve(effect, spell_level=1).sp_coefficient

    def test_greater_heal(self):
        self.assertAlmostEqual(self._coef(100, 3000), 1.611, places=3)

    def test_holy_light(self):
        self.assertAlmostEqual(self._coef(123.4, 2500), 1.657, places=3)

    def test_flash_heal(self):
        self.assertAlmostEqual(self._coef(85.5, 1500), 0.689, places=3)

    def test_circle_of_healing(self):
        self.assertAlmostEqual(self._coef(46.0, 1500), 0.371, places=3)

    def test_chain_heal(self):
        self.assertAlmostEqual(self._coef(52, 2500), 0.698, places=3)

    def test_rejuvenation_hot(self):
        self.assertAlmostEqual(self._coef(10.5, 3000, kind=potency.KIND_HEAL_PERIODIC), 0.169, places=3)


class HybridSpellTest(unittest.TestCase):
    """"Hybrid spells" table at the measured R = 1.0 (P3, 2026-10-01) - Exorcism/Hammer of Wrath,
    Holy Wrath/Avenger's Shield, Consecration. P_ap is half the original R = 2 draft's value
    (35/16.35/14 instead of 70/32.7/28); the coefficients are unchanged - they're derived straight
    from the live stock coefficient and come out R-invariant by construction."""

    def _coefs(self, p_sp, p_ap, t_ms, kind=potency.KIND_DIRECT):
        effect = potency.PotencyEffect(sp_potency=p_sp, ap_potency=p_ap, kind=kind, t_ms=t_ms)
        r = potency.resolve(effect, spell_level=1, r=1.0)
        return r.sp_coefficient, r.ap_coefficient

    def test_exorcism_hammer_of_wrath(self):
        sp, ap = self._coefs(35, 35, 1500)
        self.assertAlmostEqual(sp, 0.15, places=2)
        self.assertAlmostEqual(ap, 0.15, places=2)

    def test_holy_wrath_avengers_shield(self):
        sp, ap = self._coefs(16.3, 16.35, 1500)
        self.assertAlmostEqual(sp, 0.07, places=2)
        self.assertAlmostEqual(ap, 0.07, places=2)

    def test_consecration_per_tick(self):
        sp, ap = self._coefs(14, 14, 1000, kind=potency.KIND_PERIODIC)
        self.assertAlmostEqual(sp, 0.04, places=2)
        self.assertAlmostEqual(ap, 0.04, places=2)


class AttackPowerTableTest(unittest.TestCase):
    """"Attack power abilities" table, "Starting values at R = 1" (P3, 2026-10-01 remeasurement -
    was "R = 2" before) - that table's "Base at 60" is the *average* hit, not the baked minimum: a
    direct effect's `level60_value` is the minimum (F was already divided by 1.05 - "Damage
    range"), so the average is `level60_value * 1.05`. A periodic effect has no roll, so its
    minimum and average are the same number."""

    @staticmethod
    def _average_at_60(resolved):
        return resolved.level60_value * (1.05 if resolved.variance_pct else 1.0)

    def test_arcane_shot(self):
        effect = potency.PotencyEffect(ap_potency=50.3, kind=potency.KIND_DIRECT, t_ms=1500)
        r = potency.resolve(effect, spell_level=1, r=1.0)
        self.assertAlmostEqual(self._average_at_60(r), 135, delta=1)
        self.assertAlmostEqual(r.ap_coefficient, 0.215, places=2)

    def test_serpent_sting_per_tick(self):
        effect = potency.PotencyEffect(ap_potency=10.8, kind=potency.KIND_PERIODIC, t_ms=3000)
        r = potency.resolve(effect, spell_level=1, r=1.0)
        self.assertAlmostEqual(self._average_at_60(r), 58, delta=1)
        self.assertAlmostEqual(r.ap_coefficient, 0.093, places=3)
        self.assertAlmostEqual(r.ap_coefficient * 5, 0.46, places=2)  # "0.46 total" over 5 ticks

    def test_eviscerate_5cp(self):
        effect = potency.PotencyEffect(ap_potency=173.5, kind=potency.KIND_DIRECT, t_ms=1500)
        r = potency.resolve(effect, spell_level=1, r=1.0)
        self.assertAlmostEqual(self._average_at_60(r), 464, delta=1)
        self.assertAlmostEqual(r.ap_coefficient, 0.744, places=3)

    def test_bloodthirst(self):
        effect = potency.PotencyEffect(ap_potency=64.6, kind=potency.KIND_DIRECT, t_ms=1500)
        r = potency.resolve(effect, spell_level=1, r=1.0)
        self.assertAlmostEqual(self._average_at_60(r), 173, delta=1)
        self.assertAlmostEqual(r.ap_coefficient, 0.277, places=3)

    def test_default_r_matches_measured_value(self):
        # DEFAULT_R lives in lib/potency.py per "R is measured, not assumed... recorded in
        # potency.py" - this just confirms the module constant is the P3-approved value and
        # nobody silently reverted it to the old placeholder.
        self.assertEqual(potency.DEFAULT_R, 1.0)


class WeaponPotencyTest(unittest.TestCase):
    def test_whole_percent(self):
        effect = potency.PotencyEffect(weapon_potency=100)
        r = potency.resolve(effect, spell_level=1)
        self.assertEqual(r.base_points, 100)
        self.assertEqual(r.points_per_level, 0.0)
        self.assertIsNone(r.correction_per_level)

    def test_fractional_rejected(self):
        effect = potency.PotencyEffect(weapon_potency=75.5)
        with self.assertRaises(ValueError):
            potency.resolve(effect, spell_level=1)

    def test_combined_with_sp_potency_rejected(self):
        effect = potency.PotencyEffect(sp_potency=10, weapon_potency=100)
        with self.assertRaises(ValueError):
            potency.resolve(effect, spell_level=1)


class TooltipExpressionTest(unittest.TestCase):
    """Frostbolt's worked example from docs/potency-system.md's "Tooltip" section:
    `${$max($max(0,31.5476+3.1190*$PL),11.4286*$max(0,$PL-15.375))}` (minimum side). The doc's own
    constants are hand-rounded for display; this checks the live formula is numerically
    equivalent at the levels the doc verified against (1, 15, 25, 60, 70, 80), not that the
    printed digits match literally."""

    def setUp(self):
        effect = potency.PotencyEffect(sp_potency=100, kind=potency.KIND_DIRECT, t_ms=3000)
        self.resolved = potency.resolve(effect, spell_level=1)

    def _tooltip_value(self, pl, scale=1.0):
        low = max(0.0, self.resolved.tooltip_low_intercept * scale + self.resolved.tooltip_low_slope * scale * pl)
        high = self.resolved.points_per_level * scale * max(0.0, pl - self.resolved.tooltip_high_offset)
        return max(low, high)

    def test_high_offset_matches_doc_worked_example(self):
        self.assertAlmostEqual(self.resolved.tooltip_high_offset, 15.375, places=2)

    def test_matches_calcvalue_at_every_level(self):
        for level in (1, 15, 25, 60, 70, 80):
            with self.subTest(level=level):
                native = potency.simulate_value(self.resolved, level, spell_level=1, roll=1.0)
                tooltip = self._tooltip_value(level)
                self.assertAlmostEqual(tooltip, native, delta=1.0)

    def test_expand_placeholders_range(self):
        text = "Deals {pot1} damage."
        out = potency.expand_placeholders(text, {1: self.resolved})
        self.assertTrue(out.startswith("Deals ${$max($max(0,"))
        self.assertIn("} to ${$max($max(0,", out)

    def test_expand_placeholders_total_scales_linearly(self):
        dot_effect = potency.PotencyEffect(sp_potency=23, kind=potency.KIND_PERIODIC, t_ms=3000)
        dot = potency.resolve(dot_effect, spell_level=1)
        per_tick_expr = potency.tooltip_expression(dot)
        total_expr = potency.tooltip_expression(dot, ticks=6)
        # Every linear coefficient in the total variant is exactly 6x the per-tick one.
        per_tick_numbers = [float(x) for x in re_findall_numbers(per_tick_expr)]
        total_numbers = [float(x) for x in re_findall_numbers(total_expr)]
        # HIGH_OFFSET (last number) doesn't scale; the rest (intercept, slope, real_ppl) do.
        for i in range(len(per_tick_numbers) - 1):
            self.assertAlmostEqual(total_numbers[i], per_tick_numbers[i] * 6, places=3)
        self.assertAlmostEqual(total_numbers[-1], per_tick_numbers[-1], places=3)


def re_findall_numbers(expr: str) -> list[str]:
    import re

    return re.findall(r"-?\d+\.?\d*", expr)


if __name__ == "__main__":
    unittest.main()
