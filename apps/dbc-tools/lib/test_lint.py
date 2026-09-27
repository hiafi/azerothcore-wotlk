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
from lib.dsl.constants import RANGE_SELF, RANGE_SELF_INDEX  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

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
    "spellradius": {
        8: {"ID": 8, "Radius": 10.0},
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

    def test_name_lang_mismatch_warns(self):
        entry = _entry(name="Real Name", raw_overrides={"Name_Lang_enUS": "Stale Name"})
        warnings = lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Name_Lang_enUS", warnings[0])

    def test_effect_base_points_mismatch_warns(self):
        # Same shape as the reviewer's own concrete example (Sword and Board, 50227, effect 2 -
        # allow-listed for real, so a distinct id is used here to test the check itself).
        entry = _entry(
            id=999002, effect2={"type": 6, "base_points": 9},
            raw_overrides={"EffectBasePoints_2": -1},
        )
        warnings = lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES)
        self.assertEqual(len(warnings), 1)
        self.assertIn("EffectBasePoints_2", warnings[0])
        self.assertIn("effect2.base_points", warnings[0])

    def test_sword_and_board_is_allowlisted_for_real(self):
        # The actual, still-live mismatch this check's effect-level extension found in the real
        # repo (source/spells/npc.csv, not yet DSL-migrated) - confirms the allow-list entry
        # matches reality, not just a synthetic fixture.
        entry = _entry(
            id=50227, effect2={"type": 6, "base_points": 9},
            raw_overrides={"EffectBasePoints_2": -1},
        )
        self.assertIn((50227, "EffectBasePoints_2"), lint.RAW_OVERRIDE_MISMATCH_ALLOWLIST)
        self.assertEqual(lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES), [])

    def test_effect_field_matching_value_does_not_warn(self):
        entry = _entry(effect1={"type": 6, "base_points": 9}, raw_overrides={"EffectBasePoints_1": 9})
        self.assertEqual(lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES), [])

    def test_effect_die_sides_unset_default_is_one_not_zero(self):
        # build_spell_row does effect.get("die_sides", 1) - an *unset* die_sides is 1, not falsy,
        # so a raw override of e.g. 0 must be flagged as a real disagreement, not skipped.
        entry = _entry(effect1={"type": 6, "base_points": 1}, raw_overrides={"EffectDieSides_1": 0})
        warnings = lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES)
        self.assertEqual(len(warnings), 1)
        self.assertIn("EffectDieSides_1", warnings[0])

    def test_effect_die_sides_matching_unset_default_does_not_warn(self):
        entry = _entry(effect1={"type": 6, "base_points": 1}, raw_overrides={"EffectDieSides_1": 1})
        self.assertEqual(lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES), [])

    def test_effect_radius_index_mismatch_warns(self):
        entry = _entry(effect1={"type": 6, "radius_yards": 5.0}, raw_overrides={"EffectRadiusIndex_1": 8})
        warnings = lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES)
        self.assertEqual(len(warnings), 1)
        self.assertIn("EffectRadiusIndex_1", warnings[0])

    def test_effect_radius_index_uses_entry_level_default_radius_fallback(self):
        # build_spell_row: an effect with no radius_yards of its own falls back to the entry's
        # own radius_yards default - the lint has to replicate that exact fallback.
        entry = _entry(
            radius_yards=10.0, effect1={"type": 6}, raw_overrides={"EffectRadiusIndex_1": 8},
        )
        self.assertEqual(lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES), [])

    def test_effect_allowlist_entry_is_respected(self):
        entry = _entry(
            id=999, effect3={"type": 6, "base_points": 1}, raw_overrides={"EffectBasePoints_3": 2},
        )
        lint.RAW_OVERRIDE_MISMATCH_ALLOWLIST[(999, "EffectBasePoints_3")] = "test-only"
        try:
            self.assertEqual(lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES), [])
        finally:
            del lint.RAW_OVERRIDE_MISMATCH_ALLOWLIST[(999, "EffectBasePoints_3")]

    def test_no_effect_dict_is_not_judged(self):
        entry = _entry(raw_overrides={"EffectBasePoints_1": 5})
        self.assertEqual(lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES), [])


class CheckLinkedSpellKeyCollisionsTest(unittest.TestCase):
    def test_type_zero_trigger_collides_with_type_one_on_a_lower_spell(self):
        # The exact scenario from the review: a custom type=0 trigger at 200585 collides with the
        # stock type=1 (hit) row for Smite (585), since LoadSpellLinked shifts type=1 by 200000.
        rows = [
            {"spell_trigger": 200585, "spell_effect": 1, "type": 0},
            {"spell_trigger": 585, "spell_effect": 2, "type": 1},
        ]
        warnings = lint.check_linked_spell_key_collisions(rows)
        self.assertEqual(len(warnings), 1)
        self.assertIn("200585", warnings[0])
        self.assertIn("585", warnings[0])

    def test_no_collision_for_unrelated_triggers(self):
        rows = [
            {"spell_trigger": 200585, "spell_effect": 1, "type": 0},
            {"spell_trigger": 585, "spell_effect": 2, "type": 0},
        ]
        self.assertEqual(lint.check_linked_spell_key_collisions(rows), [])

    def test_same_row_twice_is_not_a_collision(self):
        rows = [
            {"spell_trigger": 200326, "spell_effect": 1, "type": 2},
            {"spell_trigger": 200326, "spell_effect": 1, "type": 2},
        ]
        self.assertEqual(lint.check_linked_spell_key_collisions(rows), [])

    def test_engine_key_matches_source(self):
        # SpellMgr::LoadSpellLinked: `if (type) { trigger += MAX*type if positive else -= }`.
        self.assertEqual(lint._spell_linked_engine_key(585, 0), 585)
        self.assertEqual(lint._spell_linked_engine_key(585, 1), 200585)
        self.assertEqual(lint._spell_linked_engine_key(585, 2), 400585)
        self.assertEqual(lint._spell_linked_engine_key(-585, 1), -200585)


class CheckZeroRangeUnitTargetTest(unittest.TestCase):
    def test_zero_range_enemy_target_warns(self):
        # Fury of Elune's beam (200338) as it shipped: range_yards=0.0 on a TARGET_UNIT_TARGET_ENEMY.
        entry = _entry(id=200338, range_yards=0.0, effect1={"type": 2, "implicit_target_a": 6})
        warnings = lint.check_zero_range_unit_target([entry])
        self.assertEqual(len(warnings), 1)
        self.assertIn("200338", warnings[0])

    def test_unset_range_dest_target_warns(self):
        entry = _entry(effect1={"type": 2, "implicit_target_a": 53, "implicit_target_b": 16})
        self.assertEqual(len(lint.check_zero_range_unit_target([entry])), 1)

    def test_self_only_spell_does_not_warn(self):
        entry = _entry(range_yards=0.0, effect1={"type": 6, "implicit_target_a": 1})
        self.assertEqual(lint.check_zero_range_unit_target([entry]), [])

    def test_real_range_does_not_warn(self):
        entry = _entry(range_yards=50000.0, effect1={"type": 2, "implicit_target_a": 6})
        self.assertEqual(lint.check_zero_range_unit_target([entry]), [])

    def test_self_constant_does_not_warn(self):
        entry = _entry(range_yards=RANGE_SELF, effect1={"type": 2, "implicit_target_a": 6})
        self.assertEqual(lint.check_zero_range_unit_target([entry]), [])

    def test_raw_range_index_override_does_not_warn(self):
        entry = _entry(effect1={"type": 2, "implicit_target_a": 6}, raw_overrides={"RangeIndex": 1})
        self.assertEqual(lint.check_zero_range_unit_target([entry]), [])

    def test_pulled_from_existing_data_is_exempt(self):
        entry = _entry(effect1={"type": 2, "implicit_target_a": 6}, notes="pulled from existing data")
        self.assertEqual(lint.check_zero_range_unit_target([entry]), [])

    def test_self_constant_builds_self_only_range_index(self):
        ids_cfg = {
            name: {"start": 1, "end": 1}
            for name in ("spellcasttimes", "spellduration", "spellrange", "spellradius")
        }
        self.assertEqual(ReuseContext({}, ids_cfg).range_index(RANGE_SELF), RANGE_SELF_INDEX)

    def test_self_constant_with_matching_raw_range_index_is_not_a_mismatch(self):
        entry = _entry(range_yards=RANGE_SELF, raw_overrides={"RangeIndex": RANGE_SELF_INDEX})
        self.assertEqual(lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES), [])

    def test_self_constant_with_other_raw_range_index_is_a_mismatch(self):
        entry = _entry(range_yards=RANGE_SELF, raw_overrides={"RangeIndex": 6})
        self.assertEqual(len(lint.check_raw_override_typed_mismatch([entry], INDEX_TABLES)), 1)


if __name__ == "__main__":
    unittest.main()
