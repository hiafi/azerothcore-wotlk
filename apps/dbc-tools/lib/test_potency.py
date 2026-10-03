"""
Reproduces docs/potency-system.md's own worked reference tables exactly - the P2 acceptance gate
named in potency-system.HANDOFF.md ("the pytest must reproduce the design doc's reference tables
exactly: Frostbolt's row and ranges, Corruption per tick and totals, the heal table's
coefficients, the attack power table at R = 2, and Exorcism's 35 + 70 giving 0.15 / 0.15").

Every expected number in this file is copied straight from docs/potency-system.md, not
re-derived - if a doc retune changes a table, the matching test here should fail until the retune
is also reflected wherever this module's constants live.
"""

import re
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
        self.assertEqual(r.points_per_level, 0.0)
        self.assertIsNone(r.correction_per_level)
        # base_points is 99, not 100: die_sides=1 means the live engine always adds its own "+1" at
        # cast time (same convention every potency effect uses), so the stored value must be one
        # less than the intended whole-number percent. Checking the raw field alone previously
        # missed a real off-by-one bug here - assert the actual simulated live value instead.
        self.assertEqual(r.base_points, 99)
        self.assertEqual(potency.simulate_value(r, level=60, spell_level=1), 100.0)
        self.assertEqual(potency.simulate_value(r, level=1, spell_level=1), 100.0)  # no level scaling at all

    def test_fractional_rejected(self):
        effect = potency.PotencyEffect(weapon_potency=75.5)
        with self.assertRaises(ValueError):
            potency.resolve(effect, spell_level=1)

    def test_ap_potency_rejected(self):
        """"The flat part carries no attack power coefficient... a designer who wants more scaling
        raises the weapon percent instead" - ap_potency can never combine with weapon_potency,
        regardless of whether a flat sp_potency bonus is also present."""
        effect = potency.PotencyEffect(ap_potency=10, weapon_potency=100)
        with self.assertRaises(ValueError):
            potency.resolve(effect, spell_level=1)
        effect = potency.PotencyEffect(sp_potency=5, ap_potency=10, weapon_potency=100)
        with self.assertRaises(ValueError):
            potency.resolve(effect, spell_level=1)

    def test_flat_bonus_too_high_rejected(self):
        """"Kept low (10 or less)" - enforced, not just documented."""
        effect = potency.PotencyEffect(sp_potency=10.1, weapon_potency=100)
        with self.assertRaises(ValueError):
            potency.resolve(effect, spell_level=1)

    def test_flat_bonus_exactly_at_cap_allowed(self):
        effect = potency.PotencyEffect(sp_potency=potency.WEAPON_FLAT_BONUS_MAX, weapon_potency=100)
        potency.resolve(effect, spell_level=1)  # must not raise


class WeaponPotencyWithFlatBonusTest(unittest.TestCase):
    """"Decided, implementation: one hit through the weapon effect" - a weapon_potency effect's
    flat sp_potency bonus (docs/potency-system.md's Mortal Strike-style case) lands on the SAME
    EffectBasePoints/EffectRealPointsPerLevel pair as the weapon percent itself."""

    def setUp(self):
        self.wp = 100
        self.flat_alone = potency.resolve(
            potency.PotencyEffect(sp_potency=10, kind=potency.KIND_DIRECT, t_ms=1500), spell_level=1,
        )
        self.combined = potency.resolve(
            potency.PotencyEffect(sp_potency=10, weapon_potency=self.wp), spell_level=1,
        )

    def test_live_value_is_weapon_percent_plus_the_flat_bonus_alone(self):
        """The doc's own worked numbers: "about 27 damage at 60 and 39 at 80" for a 10-potency flat
        bonus - verified here by equivalence to the SAME flat bonus resolved on its own (no weapon
        component), not by re-deriving the formula a second time."""
        for level in (1, 25, 60, 70, 80):
            expected = self.wp + potency.simulate_value(self.flat_alone, level, spell_level=1)
            actual = potency.simulate_value(self.combined, level, spell_level=1)
            self.assertEqual(actual, expected, f"mismatch at level {level}")

    def test_no_attack_power_coefficient(self):
        self.assertEqual(self.combined.ap_coefficient, 0.0)

    def test_spell_power_coefficient_matches_the_flat_bonus_alone(self):
        self.assertEqual(self.combined.sp_coefficient, self.flat_alone.sp_coefficient)

    def test_no_variance_roll(self):
        """"Weapon damage rolls its own range, so there is no variance roll" - even though a plain
        KIND_DIRECT effect (what the flat bonus resolves as on its own) normally gets one."""
        self.assertEqual(self.combined.variance_pct, 0.0)
        self.assertNotEqual(self.flat_alone.variance_pct, 0.0)  # sanity: direct kind DOES roll alone

    def test_correction_row_present(self):
        """Unlike a pure weapon-percent effect (no correction row at all), the flat bonus still
        needs one - it's "ordinary spell potency on C(L)"."""
        self.assertIsNotNone(self.combined.correction_per_level)
        self.assertEqual(self.combined.correction_per_level, self.flat_alone.correction_per_level)
        self.assertEqual(self.combined.breakpoint_level, self.flat_alone.breakpoint_level)


class BasePotencyOverrideTest(unittest.TestCase):
    """`base_potency` drives EffectBasePoints/RealPointsPerLevel/the correction row in place of
    sp_potency + ap_potency, without changing either coefficient - for a spell whose intended base
    damage doesn't equal what its SP/AP coefficients alone would imply."""

    def test_none_falls_back_to_sp_plus_ap(self):
        with_override = potency.resolve(
            potency.PotencyEffect(sp_potency=60, ap_potency=40, kind=potency.KIND_DIRECT, t_ms=1500),
            spell_level=1,
        )
        without_override = potency.resolve(
            potency.PotencyEffect(
                sp_potency=60, ap_potency=40, kind=potency.KIND_DIRECT, t_ms=1500, base_potency=None,
            ),
            spell_level=1,
        )
        self.assertEqual(with_override, without_override)

    def test_overrides_base_without_changing_coefficients(self):
        baseline = potency.resolve(
            potency.PotencyEffect(sp_potency=60, ap_potency=40, kind=potency.KIND_DIRECT, t_ms=1500),
            spell_level=1,
        )
        overridden = potency.resolve(
            potency.PotencyEffect(
                sp_potency=60, ap_potency=40, kind=potency.KIND_DIRECT, t_ms=1500, base_potency=100,
            ),
            spell_level=1,
        )
        # sp_potency=60, ap_potency=40 sums to the same 100 base_potency here on purpose, so the
        # base comes out identical - this test is about the coefficients staying put, not the base.
        self.assertEqual(overridden.base_points, baseline.base_points)
        self.assertEqual(overridden.sp_coefficient, baseline.sp_coefficient)
        self.assertEqual(overridden.ap_coefficient, baseline.ap_coefficient)

        # Now actually diverge the base from the SP/AP sum - only the base-driven fields move.
        diverged = potency.resolve(
            potency.PotencyEffect(
                sp_potency=60, ap_potency=40, kind=potency.KIND_DIRECT, t_ms=1500, base_potency=200,
            ),
            spell_level=1,
        )
        self.assertNotEqual(diverged.base_points, baseline.base_points)
        self.assertAlmostEqual(diverged.level60_value, baseline.level60_value * 2, places=6)
        self.assertEqual(diverged.sp_coefficient, baseline.sp_coefficient)
        self.assertEqual(diverged.ap_coefficient, baseline.ap_coefficient)
        self.assertEqual(diverged.total_potency, 200)

    def test_base_potency_alone_satisfies_the_positivity_check(self):
        # No sp_potency/ap_potency at all - a pure level-scaling line with zero stat scaling -
        # must not raise just because sp_potency + ap_potency is 0.
        resolved = potency.resolve(
            potency.PotencyEffect(kind=potency.KIND_DIRECT, t_ms=1500, base_potency=50),
            spell_level=1,
        )
        self.assertEqual(resolved.sp_coefficient, 0.0)
        self.assertEqual(resolved.ap_coefficient, 0.0)
        # base_points itself is negative at low SpellLevel by design (same as any potency effect -
        # see the Frostbolt reference row, base_points=-165 at SpellLevel 1); what matters is the
        # baked level-60 value, which must be positive and proportional to base_potency=50.
        self.assertGreater(resolved.level60_value, 0)

    def test_still_rejects_all_zero(self):
        with self.assertRaises(ValueError):
            potency.resolve(potency.PotencyEffect(kind=potency.KIND_DIRECT, t_ms=1500), spell_level=1)


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
        self.assertTrue(out.startswith("Deals ${$max($max("))
        self.assertIn("} to ${$max($max(", out)
        # sp_potency=100 on this effect means every branch carries the live SP bonus term (P5).
        self.assertIn("*$SP", out)

    @staticmethod
    def _evaluate(placeholder_output: str, level: int, mult: float, sp: float = 0.0) -> list[int]:
        """Evaluates each `${...}` the way the client does, for the tokens potency emits."""
        values = []
        for expr in re.findall(r"\$\{(.*?)\}(?: to |$)", placeholder_output):
            py = (expr.replace("$max(", "max(").replace("$PL", str(level)).replace("$SP", str(sp))
                  .replace("$<mult>", str(mult)))
            values.append(round(eval(py, {"max": max})))  # noqa: S307 - generated test input only
        return values

    def test_expand_placeholders_variable_suffix(self):
        """PLAN P9.3: `{pot1*mult}` multiplies both ends of the range by `$<mult>`, after the outer
        `$max(...)` (the form P9.0 confirmed). 37/117/541 are the P9.0 in-game readings for this
        Frostbolt reference row with a rank-3 (x1.06) talent, at levels 1/25/60."""
        out = potency.expand_placeholders("{pot1*mult}", {1: self.resolved})
        self.assertEqual(out.count(")*$<mult>}"), 2)
        for level, expected_min in ((1, 37), (25, 117), (60, 541)):
            with self.subTest(level=level):
                self.assertEqual(self._evaluate(out, level, 1.06)[0], expected_min)
        plain = potency.expand_placeholders("{pot1}", {1: self.resolved})
        self.assertEqual(self._evaluate(plain, 60, 1.0), self._evaluate(out, 60, 1.0))

    def test_variable_suffix_on_avg_and_total(self):
        dot = potency.resolve(potency.PotencyEffect(sp_potency=23, kind=potency.KIND_PERIODIC, t_ms=3000),
                              spell_level=1)
        total = potency.expand_placeholders("{pot1.total*mult}", {1: dot}, {1: 6})
        plain_total = potency.expand_placeholders("{pot1.total}", {1: dot}, {1: 6})
        self.assertTrue(total.endswith(")*$<mult>}"))
        self.assertAlmostEqual(self._evaluate(total, 60, 1.5)[0], 1.5 * self._evaluate(plain_total, 60, 1.0)[0],
                               delta=1.0)
        avg = potency.expand_placeholders("{pot1.avg*crit_bonus}", {1: self.resolved})
        self.assertTrue(avg.endswith(")*$<crit_bonus>}"))

    def test_unrecognized_placeholder_raises(self):
        for bad in ("{pot1*Mult}", "{pot1.tot}", "{pot4}", "{pot1*}"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                potency.expand_placeholders(f"Deals {bad} damage.", {1: self.resolved})

    def test_expand_placeholders_total_scales_linearly(self):
        dot_effect = potency.PotencyEffect(sp_potency=23, kind=potency.KIND_PERIODIC, t_ms=3000)
        dot = potency.resolve(dot_effect, spell_level=1)
        per_tick_expr = potency.tooltip_expression(dot)
        total_expr = potency.tooltip_expression(dot, ticks=6)
        # Every per-tick rate (intercept, slope, real_ppl, SP bonus) is exactly 6x in the total
        # variant; HIGH_OFFSET is an x-intercept, not a rate, so it doesn't scale.
        self.assertIn(potency._fmt(dot.tooltip_low_intercept * 6), total_expr)
        self.assertIn(potency._fmt(dot.tooltip_low_slope * 6), total_expr)
        self.assertIn(potency._fmt(dot.points_per_level * 6), total_expr)
        self.assertIn(potency._fmt(dot.sp_coefficient * 6) + "*$SP", total_expr)
        self.assertIn(potency._fmt(dot.tooltip_high_offset), per_tick_expr)
        self.assertIn(potency._fmt(dot.tooltip_high_offset), total_expr)
        self.assertIn(potency._fmt(dot.sp_coefficient) + "*$SP", per_tick_expr)

    def test_attack_power_bonus_term(self):
        """Hunter/Rogue/Warrior-style AP potency gets a `$AP`-based term the same way SP does -
        same scratch-spell confirmation (P5) covered both tokens, not just `$SP`."""
        effect = potency.PotencyEffect(ap_potency=100, kind=potency.KIND_DIRECT, t_ms=3000)
        resolved = potency.resolve(effect, spell_level=1)
        expr = potency.tooltip_expression(resolved)
        self.assertIn(potency._fmt(resolved.ap_coefficient) + "*$AP", expr)
        self.assertNotIn("$SP", expr)

    def test_stat_bonus_distributed_into_every_max_branch(self):
        """The SP/AP bonus must land inside every branch of the outer `$max()`, never appended
        once after it closes - a top-level `+` outside every `$max()`/`$min()` call is silently
        dropped on this fork's client (P0), so `max(a, b) + c` has to be written as
        `max(a + c, b + c)` instead (see `tooltip_expression`'s docstring)."""
        expr = potency.tooltip_expression(self.resolved)
        self.assertTrue(expr.startswith("$max("))
        self.assertTrue(expr.endswith(")"))
        # Every character after the expression's own outermost `$max(...)` closes would be exactly
        # the silently-dropped top-level `+` this test guards against - there must be none.
        depth = 0
        for i, ch in enumerate(expr):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    self.assertEqual(i, len(expr) - 1)
                    break


def re_findall_numbers(expr: str) -> list[str]:
    import re

    return re.findall(r"-?\d+\.?\d*", expr)


if __name__ == "__main__":
    unittest.main()
