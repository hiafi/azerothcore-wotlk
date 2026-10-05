"""
Unit tests for `lib/lint.py`'s `check_range_on_nonself_helpers` (X1, paladin-rework SHARED B6 item 7).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_lint_range.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import lint  # noqa: E402
from lib.dsl.constants import RANGE_SELF  # noqa: E402


def _spell(spell_id=201100, **overrides):
    entry = {"id": spell_id, "name": "Helper", "range_yards": 0.0, "raw_overrides": {}, "notes": ""}
    entry.update(overrides)
    return entry


def _eff(a=1, b=0, type_=6):
    return {"type": type_, "implicit_target_a": a, "implicit_target_b": b}


class CheckRangeOnNonSelfHelpersTest(unittest.TestCase):
    def test_enemy_unit_target_warns(self):
        warnings = lint.check_range_on_nonself_helpers([_spell(effect1=_eff(6))])
        self.assertEqual(len(warnings), 1)
        self.assertIn("201100", warnings[0])

    def test_dest_target_warns(self):
        self.assertEqual(len(lint.check_range_on_nonself_helpers([_spell(effect1=_eff(53, 16))])), 1)

    def test_area_aura_on_caster_shape_warns(self):
        # target A = caster with an area (raid-around-caster) target B: other units are hit.
        self.assertEqual(len(lint.check_range_on_nonself_helpers([_spell(effect2=_eff(1, 56))])), 1)

    def test_effect_in_any_slot_counts(self):
        entry = _spell(effect1=_eff(1), effect3=_eff(6))
        self.assertEqual(len(lint.check_range_on_nonself_helpers([entry])), 1)

    def test_caster_only_does_not_warn(self):
        entry = _spell(effect1=_eff(1), effect2=_eff(1, 0))
        self.assertEqual(lint.check_range_on_nonself_helpers([entry]), [])

    def test_empty_effect_target_ignored(self):
        entry = _spell(effect1=_eff(1), effect2=_eff(6, 0, type_=0))
        self.assertEqual(lint.check_range_on_nonself_helpers([entry]), [])

    def test_range_yards_does_not_warn(self):
        self.assertEqual(lint.check_range_on_nonself_helpers([_spell(range_yards=50000.0, effect1=_eff(6))]), [])

    def test_range_self_marker_does_not_warn(self):
        self.assertEqual(lint.check_range_on_nonself_helpers([_spell(range_yards=RANGE_SELF, effect1=_eff(6))]), [])

    def test_raw_range_index_does_not_warn(self):
        entry = _spell(effect1=_eff(6), raw_overrides={"RangeIndex": 6})
        self.assertEqual(lint.check_range_on_nonself_helpers([entry]), [])

    def test_raw_range_index_zero_still_warns(self):
        entry = _spell(effect1=_eff(6), raw_overrides={"RangeIndex": 0})
        self.assertEqual(len(lint.check_range_on_nonself_helpers([entry])), 1)

    def test_stock_id_is_out_of_scope(self):
        self.assertEqual(lint.check_range_on_nonself_helpers([_spell(spell_id=31884, effect1=_eff(6))]), [])

    def test_pulled_from_existing_data_is_exempt(self):
        entry = _spell(effect1=_eff(6), notes="pulled from existing data")
        self.assertEqual(lint.check_range_on_nonself_helpers([entry]), [])

    def test_allow_list_exempts(self):
        entry = _spell(201106, effect1=_eff(6))
        self.assertEqual(lint.check_range_on_nonself_helpers([entry], allow={201106}), [])
        self.assertEqual(len(lint.check_range_on_nonself_helpers([entry], allow=set())), 1)

    def test_skip_ids_suppresses_duplicate_report(self):
        entry = _spell(effect1=_eff(6))
        self.assertEqual(lint.check_range_on_nonself_helpers([entry], skip_ids={201100}), [])


if __name__ == "__main__":
    unittest.main()
