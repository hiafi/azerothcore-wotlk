"""
Unit tests for `lib/lint.py`'s `check_raw_override_typed_mismatch` - WP-T
(.agents/plans/druid-rework/druid-rework.WP-T-HANDOFF.md, PLAN A9/§5.0 item 4).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_lint.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import lint  # noqa: E402

# A minimal index_tables fixture: two SpellCastTimes ids (16 and 30004) that both resolve to the
# same 1500ms Base - the real-world pair the docstring/handoff calls out ("CastingTimeIndex 16 and
# 30004 are both 1500 ms") - plus one that doesn't (30001 -> 2000ms), and a RangeIndex.
INDEX_TABLES = {
    "spellcasttimes": {
        16: {"ID": 16, "Base": 1500, "PerLevel": 0, "Minimum": 0},
        30004: {"ID": 30004, "Base": 1500, "PerLevel": 0, "Minimum": 0},
        30001: {"ID": 30001, "Base": 2000, "PerLevel": 0, "Minimum": 0},
    },
    "spellduration": {},
    "spellrange": {
        6: {"ID": 6, "RangeMax_1": 100.0, "RangeMax_2": 100.0},
    },
}


def _entry(**overrides) -> dict:
    base = {"id": 200001, "name": "Test Spell"}
    base.update(overrides)
    return base


class CheckRawOverrideTypedMismatchTest(unittest.TestCase):
    def test_indexed_field_value_mismatch_warns(self):
        entry = _entry(cast_time_ms=2000, raw_overrides={"CastingTimeIndex": 16})  # 16 -> 1500ms
        warnings = lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES)
        self.assertEqual(len(warnings), 1)
        self.assertIn("200001", warnings[0])
        self.assertIn("CastingTimeIndex", warnings[0])

    def test_indexed_field_same_value_different_index_id_does_not_warn(self):
        # The exact case the docstring calls out: two different index ids (16, 30004) that
        # resolve to the *same* underlying value must not be flagged - comparing index ids
        # directly (instead of what they resolve to) is the bug this check must not have.
        entry = _entry(cast_time_ms=1500, raw_overrides={"CastingTimeIndex": 30004})
        self.assertEqual(lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES), [])

    def test_indexed_field_matching_index_id_does_not_warn(self):
        entry = _entry(cast_time_ms=1500, raw_overrides={"CastingTimeIndex": 16})
        self.assertEqual(lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES), [])

    def test_range_index_mismatch_warns(self):
        entry = _entry(range_yards=30.0, raw_overrides={"RangeIndex": 6})  # 6 -> 100 yards
        warnings = lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES)
        self.assertEqual(len(warnings), 1)
        self.assertIn("RangeIndex", warnings[0])

    def test_direct_field_mismatch_warns(self):
        entry = _entry(cooldown_ms=45000, raw_overrides={"RecoveryTime": 30000})
        warnings = lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES)
        self.assertEqual(len(warnings), 1)
        self.assertIn("RecoveryTime", warnings[0])

    def test_direct_field_matching_value_does_not_warn(self):
        entry = _entry(cooldown_ms=45000, raw_overrides={"RecoveryTime": 45000})
        self.assertEqual(lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES), [])

    def test_typed_field_left_at_default_is_not_a_disagreement(self):
        # cast_time_ms was never set (falsy) - the raw override isn't "disagreeing" with
        # anything, it's just an unmodeled column.
        entry = _entry(raw_overrides={"CastingTimeIndex": 16})
        self.assertEqual(lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES), [])

    def test_no_raw_overrides_is_a_no_op(self):
        entry = _entry(cast_time_ms=2000)
        self.assertEqual(lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES), [])

    def test_pulled_from_existing_data_is_exempt(self):
        entry = _entry(
            cast_time_ms=2000, raw_overrides={"CastingTimeIndex": 16}, notes="pulled from existing data",
        )
        self.assertEqual(lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES), [])

    def test_allowlisted_spell_and_column_is_suppressed(self):
        entry = _entry(id=200079, range_yards=30.0, raw_overrides={"RangeIndex": 6})
        self.assertIn((200079, "RangeIndex"), lint.RAW_OVERRIDE_MISMATCH_ALLOWLIST)
        self.assertEqual(lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES), [])

    def test_unresolvable_raw_index_is_not_judged(self):
        # A raw index id that doesn't resolve to anything live isn't this check's job to flag.
        entry = _entry(cast_time_ms=2000, raw_overrides={"CastingTimeIndex": 999999})
        self.assertEqual(lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES), [])


if __name__ == "__main__":
    unittest.main()
