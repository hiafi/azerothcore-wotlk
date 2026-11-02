"""
Potency audit S4 / F10 (2026-11-01): an effect a script reads as a PERCENT must not carry potency (the percent would grow
with level: Anti-Magic Shell read about 76% at level 60 and 109% at 80). `lint.check_percent_field_potency` holds a
curated (spell id, effect index) list plus a shape rule (potency only on damage/heal/absorb-shaped effects). Fixtures for
the lint, and the real Death Knight package for the three F10 effects. The whole-tree run is `generate.py --check`.

Run: cd apps/dbc-tools && .venv/bin/python3 -m pytest lib/test_potency_percent_fields.py -q -p no:cacheprovider
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import lint  # noqa: E402


def _entry(spell_id: int, **effects: dict) -> dict:
    entry = {"id": spell_id, "name": "Test"}
    entry.update(effects)
    return entry


_POTENCY = {"total_potency": 7.1}


class PercentFieldLintTest(unittest.TestCase):
    def test_curated_percent_field_with_potency_is_an_error(self):
        entry = _entry(48707, effect1={"type": 6, "apply_aura": 69, "points_per_level": 0.0, "_potency": _POTENCY})
        errors = lint.check_percent_field_potency([entry])
        self.assertEqual(len(errors), 1)
        self.assertIn("spell 48707 (Test) effect 0", errors[0])

    def test_curated_percent_field_with_a_level_slope_is_an_error(self):
        entry = _entry(52284, effect1={"type": 6, "apply_aura": 69, "base_points": 4, "points_per_level": 0.17})
        self.assertEqual(len(lint.check_percent_field_potency([entry])), 1)

    def test_curated_percent_field_flat_and_excluded_is_clean(self):
        entry = _entry(
            48743, effect1={"type": 3}, effect2={"type": 1},
            effect3={"type": 10, "base_points": 39, "points_per_level": 0.0, "_potency_excluded": "percent"},
        )
        self.assertEqual(lint.check_percent_field_potency([entry]), [])

    def test_same_spell_other_effect_index_is_not_flagged(self):
        entry = _entry(48743, effect1={"type": 3, "_potency": _POTENCY})
        self.assertEqual(lint.check_percent_field_potency([entry]), [])

    def test_potency_on_a_stat_aura_is_an_error(self):
        entry = _entry(300001, effect1={"type": 6, "apply_aura": 101, "_potency": _POTENCY})  # MOD_RESISTANCE_PCT
        errors = lint.check_percent_field_potency([entry])
        self.assertEqual(len(errors), 1)
        self.assertIn("not a damage/heal/absorb effect", errors[0])

    def test_potency_on_damage_heal_absorb_shapes_is_clean(self):
        shapes = [(2, 0), (10, 0), (31, 0), (121, 0), (6, 3), (6, 8), (6, 53), (6, 69), (27, 4), (35, 69), (3, 0)]
        entries = [_entry(300100 + i, effect1={"type": t, "apply_aura": a, "_potency": _POTENCY})
                   for i, (t, a) in enumerate(shapes)]
        self.assertEqual(lint.check_percent_field_potency(entries), [])


class DeathKnightPercentFieldsTest(unittest.TestCase):
    """The real DK package: the three F10 effects are flat percents again."""

    @classmethod
    def setUpClass(cls):
        from lib.test_deathknight_dk0a import _data
        cls.spells = {int(e["id"]): e for e in _data()["package"].spells}

    def test_lint_is_clean_on_the_dk_package(self):
        self.assertEqual(lint.check_percent_field_potency(list(self.spells.values())), [])

    def test_f10_values(self):
        for spell_id, index, value in ((48707, 0, 74), (52284, 0, 4), (48743, 2, 39)):
            effect = self.spells[spell_id][f"effect{index + 1}"]
            self.assertEqual(int(effect["base_points"]), value, spell_id)
            self.assertEqual(float(effect["points_per_level"]), 0.0, spell_id)
            self.assertNotIn("_potency", effect, spell_id)
            self.assertTrue(effect.get("_potency_excluded"), spell_id)
        # The rank-2/3 twins (stock 52285 / 52286: 10% / 15%) are not declared; rank 1 is the 5% under them.
        self.assertLess(int(self.spells[52284]["effect1"]["base_points"]) + 1, 10)


if __name__ == "__main__":
    unittest.main()
