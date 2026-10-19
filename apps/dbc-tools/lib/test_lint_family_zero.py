"""
Unit tests for `lib/lint.py`'s `check_family_zero_spellmods` (hunter-rework S1c).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_lint_family_zero.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import lint  # noqa: E402


def _row(spell_id=200196, family=0, aura=107, misc=11, mask=(0, 0, 0)):
    row = {"ID": spell_id, "SpellClassSet": family, "EffectAura_1": aura, "EffectMiscValue_1": misc}
    for n, word in enumerate(mask, start=1):
        row[f"EffectSpellClassMaskA_{n}"] = word
    return row


def _entry(spell_id=200196):
    return {"id": spell_id, "name": "Improved Test"}


def _check(row, stock=None, allow=None):
    return lint.check_family_zero_spellmods([_entry(row["ID"])], [row], stock, allow)


class CheckFamilyZeroSpellmodsTest(unittest.TestCase):
    def test_custom_family_zero_spellmod_is_caught(self):
        warnings = _check(_row(mask=(0x4000, 0, 0)))
        self.assertEqual(len(warnings), 1)
        self.assertIn("200196", warnings[0])
        self.assertIn("effect 1", warnings[0])

    def test_pct_modifier_is_caught(self):
        self.assertEqual(len(_check(_row(aura=108, misc=0))), 1)

    def test_scoped_family_passes(self):
        self.assertEqual(_check(_row(family=6, mask=(0x4000, 0, 0))), [])

    def test_non_spellmod_aura_passes(self):
        self.assertEqual(_check(_row(aura=4)), [])

    def test_stock_identical_passes(self):
        row = _row(spell_id=21942, mask=(1, 2, 3))
        self.assertEqual(_check(row, stock={21942: dict(row)}), [])

    def test_stock_row_with_changed_mask_is_caught(self):
        row = _row(spell_id=21942, mask=(1, 2, 3))
        stock = dict(row, EffectSpellClassMaskA_1=9)
        self.assertEqual(len(_check(row, stock={21942: stock})), 1)

    def test_stock_row_with_added_spellmod_effect_is_caught(self):
        row = _row(spell_id=21942, misc=5)
        self.assertEqual(len(_check(row, stock={21942: dict(row, EffectMiscValue_1=11)})), 1)

    def test_stock_family_nonzero_rebuilt_as_family_zero_is_caught(self):
        row = _row(spell_id=21942, mask=(1, 2, 3))
        self.assertEqual(len(_check(row, stock={21942: dict(row, SpellClassSet=9)})), 1)

    def test_missing_spell_class_set_counts_as_zero(self):
        row = _row(mask=(1, 0, 0))
        del row["SpellClassSet"]
        self.assertEqual(len(_check(row)), 1)

    def test_effects_two_and_three_are_checked(self):
        row = {"ID": 200300, "SpellClassSet": 0, "EffectAura_1": 4, "EffectAura_2": 107, "EffectMiscValue_2": 11,
               "EffectAura_3": 108, "EffectMiscValue_3": 0}
        warnings = _check(row)
        self.assertEqual(len(warnings), 2)
        self.assertIn("effect 2", warnings[0])
        self.assertIn("effect 3", warnings[1])

    def test_allow_listed_passes(self):
        self.assertEqual(_check(_row(), allow={200196: "deliberate cross-class effect"}), [])

    def test_default_allow_list_is_empty_or_reasoned(self):
        for spell_id, reason in lint.FAMILY_ZERO_SPELLMOD_ALLOW.items():
            self.assertTrue(reason, f"allow-listed {spell_id} needs a reason")


if __name__ == "__main__":
    unittest.main()
