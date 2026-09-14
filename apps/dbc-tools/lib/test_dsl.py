"""
Phase 0 validation for `lib/dsl/` (`.agents/plans/spell-source-dsl/
spell-source-dsl.PLAN.md`).

Proves the DSL can reproduce, byte-for-byte, the exact `spell_dbc` row the
existing CSV-driven pipeline already builds for real, already-shipped
spells - Frostbolt (116), Polymorph (118), Blizzard (10), hand-ported here
from `source/spells/mage.csv`. Both the CSV-parsed entry and the
hand-written DSL `Spell` are run through the *same*, completely unmodified
`build.build_spell_row` (with one shared `ReuseContext` per spell, so an
identical `cast_time_ms`/`range_yards`/`duration_ms`/`radius_yards` resolves
to the identical reused-or-minted secondary-DBC index either way) - the
whole point being that `lib/build.py` itself needed zero changes to accept
DSL-built entries. See this package's `lib/dsl/__init__.py` docstring for
what's in and out of scope for Phase 0.

No test harness exists elsewhere in apps/dbc-tools/ beyond `test_sql_dump.py`
(also plain stdlib `unittest`) - matching that. Run directly:

    python3 apps/dbc-tools/lib/test_dsl.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, source  # noqa: E402
from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, School, Spell  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

MAGE_CSV = TOOL_ROOT / "source" / "spells" / "mage.csv"
IDS_YAML = TOOL_ROOT / "source" / "ids.yaml"


def _csv_entries_by_id() -> dict[int, dict]:
    return {e["id"]: e for e in source.load_one_spell_file(MAGE_CSV)}


def _fresh_reuse() -> ReuseContext:
    ids_cfg = source.load_ids(IDS_YAML)
    return ReuseContext(existing_rows_by_table={}, ids_cfg=ids_cfg)


# Hand-ported from source/spells/mage.csv - see that file for the CSV form of
# the exact same three rows. Deliberately verbatim rather than "cleaned up"
# (e.g. Frostbolt's real DispelType is 1/MAGIC even though it's a damage
# spell, not obviously a dispel-relevant one) - Phase 0 is about proving
# fidelity to what's already shipped, not second-guessing pulled Blizzard
# data.
def _dsl_frostbolt() -> Spell:
    return Spell(
        id=116,
        name="Frostbolt",
        school=School.FROST,
        dispel=DispelType.MAGIC,
        attributes=65536,
        cast_time_ms=2000,
        mana_cost_pct=11,
        range_yards=30.0,
        duration_ms=5000,
        effects=[
            Effect(
                type=EffectType.APPLY_AURA,
                apply_aura=AuraType.MOD_DECREASE_SPEED,
                base_points=-41,
                mechanic=Mechanic.SNARE,
                implicit_target_a=6,
            ),
            Effect(
                type=EffectType.SCHOOL_DAMAGE,
                base_points=17,
                points_per_level=7.5464,
                die_sides=3,
                implicit_target_a=6,
            ),
            Effect(
                type=EffectType.APPLY_AURA,
                apply_aura=AuraType.MOD_HEALING_PCT,
                base_points=-1,
                implicit_target_a=6,
                misc_value=127,
            ),
        ],
        spell_icon_id=188,
        raw_overrides={
            "AttributesEx6": 2097152,
            "AuraDescription_Lang_Mask": 16712190,
            "AuraDescription_Lang_enUS": "Movement slowed by $s1%.",
            "BaseLevel": 4,
            "DefenseType": 1,
            "Description_Lang_Mask": 16712190,
            "Description_Lang_enUS": (
                "Launches a bolt of frost at the enemy, causing ${$m2*$<mult>} to "
                "${$M2*$<mult>} Frost damage and slowing movement speed by $s1% for $d."
            ),
            "EffectBonusMultiplier_2": 0.8569999933242798,
            "EffectChainAmplitude_1": 1.0,
            "EffectChainAmplitude_2": 1.0,
            "EffectChainAmplitude_3": 1.0,
            "EquippedItemClass": -1,
            "FacingCasterFlags": 1,
            "InterruptFlags": 15,
            "MaxLevel": 80,
            "NameSubtext_Lang_Mask": 16712190,
            "NameSubtext_Lang_enUS": "",
            "Name_Lang_Mask": 16712190,
            "PreventionType": 1,
            "ProcChance": 101,
            "Speed": 28.0,
            "SpellClassMask_1": 32,
            "SpellClassSet": 3,
            "SpellDescriptionVariableID": 167,
            "SpellLevel": 4,
            "SpellPriority": 50,
            "SpellVisualID_1": 13,
            "StartRecoveryCategory": 133,
            "StartRecoveryTime": 1500,
        },
    )


def _dsl_polymorph() -> Spell:
    return Spell(
        id=118,
        name="Polymorph",
        school=School.ARCANE,
        dispel=DispelType.MAGIC,
        mechanic=Mechanic.POLYMORPH,
        attributes=1074855936,
        cast_time_ms=1500,
        mana_cost_pct=7,
        range_yards=30.0,
        duration_ms=20000,
        effects=[
            Effect(
                type=EffectType.APPLY_AURA,
                apply_aura=AuraType.MOD_CONFUSE,
                base_points=-1,
                implicit_target_a=6,
            ),
            Effect(
                type=EffectType.APPLY_AURA,
                apply_aura=AuraType.TRANSFORM,
                die_sides=0,
                implicit_target_a=6,
                misc_value=16372,
            ),
        ],
        spell_icon_id=82,
        raw_overrides={
            "AttributesEx": 262144,
            "AttributesEx2": 64,
            "AttributesEx4": 1610612736,
            "AttributesEx5": 32,
            "AttributesEx6": 8388608,
            "AuraDescription_Lang_Mask": 16712190,
            "AuraDescription_Lang_enUS": "Cannot attack or cast spells.  Increased regeneration.",
            "AuraInterruptFlags": 524290,
            "BaseLevel": 8,
            "CastingTimeIndex": 16,
            "DefenseType": 1,
            "Description_Lang_Mask": 16712190,
            "Description_Lang_enUS": (
                "Transforms the enemy into a sheep, forcing it to wander around for up to "
                "$d.  While wandering, the sheep cannot attack or cast spells but will "
                "regenerate very quickly.  Any damage will transform the target back into "
                "its normal form.  Only one target can be polymorphed at a time.  Only "
                "works on Beasts, Humanoids and Critters."
            ),
            "EffectBasePoints_3": -1,
            "EffectChainAmplitude_1": 1.0,
            "EffectChainAmplitude_2": 1.0,
            "EffectChainAmplitude_3": 1.0,
            "EffectDieSides_3": 1,
            "EquippedItemClass": -1,
            "InterruptFlags": 15,
            "MaxLevel": 80,
            "NameSubtext_Lang_Mask": 16712190,
            "NameSubtext_Lang_enUS": "",
            "Name_Lang_Mask": 16712190,
            "PreventionType": 1,
            "ProcChance": 101,
            "SpellClassMask_1": 16777216,
            "SpellClassSet": 3,
            "SpellLevel": 8,
            "SpellPriority": 50,
            "SpellVisualID_1": 12978,
            "StartRecoveryCategory": 133,
            "StartRecoveryTime": 1500,
            "TargetCreatureType": 193,
        },
    )


def _dsl_blizzard() -> Spell:
    return Spell(
        id=10,
        name="Blizzard",
        school=School.FROST,
        attributes=65536,
        mana_cost_pct=74,
        range_yards=30.0,
        duration_ms=8000,
        effects=[
            Effect(
                type=EffectType.PERSISTENT_AREA_AURA,
                apply_aura=AuraType.DUMMY,
                base_points=24,
                points_per_level=3.1,
                implicit_target_a=28,
                radius_yards=8.0,
            ),
            Effect(
                type=EffectType.APPLY_AURA,
                apply_aura=AuraType.PERIODIC_TRIGGER_SPELL,
                die_sides=0,
                implicit_target_a=1,
                amplitude=1000,
                trigger_spell=42208,
            ),
        ],
        spell_icon_id=285,
        raw_overrides={
            "AttributesEx": 268435596,
            "AttributesEx2": 4194304,
            "AttributesEx5": 8192,
            "AuraDescription_Lang_Mask": 16712190,
            "AuraDescription_Lang_enUS": "$42208s1 Frost damage every $42208t1 $lsecond:seconds;.",
            "BaseLevel": 20,
            "CastingTimeIndex": 1,
            "ChannelInterruptFlags": 31788,
            "DefenseType": 1,
            "Description_Lang_Mask": 16712190,
            "Description_Lang_enUS": (
                "Ice shards pelt the target area doing ${$42208m1*8*$<mult>} Frost damage "
                "over $10d."
            ),
            "EffectBonusMultiplier_1": 0.11900000274181366,
            "EffectChainAmplitude_1": 1.0,
            "EffectChainAmplitude_2": 1.0,
            "EffectChainAmplitude_3": 1.0,
            "EquippedItemClass": -1,
            "InterruptFlags": 15,
            "MaxLevel": 80,
            "NameSubtext_Lang_Mask": 16712190,
            "NameSubtext_Lang_enUS": "",
            "Name_Lang_Mask": 16712190,
            "PreventionType": 1,
            "ProcChance": 100,
            "SpellClassMask_1": 524416,
            "SpellClassSet": 3,
            "SpellDescriptionVariableID": 167,
            "SpellLevel": 20,
            "SpellPriority": 50,
            "SpellVisualID_1": 9490,
            "StartRecoveryCategory": 133,
            "StartRecoveryTime": 1500,
            "Targets": 64,
        },
    )


class DslFidelityTest(unittest.TestCase):
    """One test per hand-ported spell - a failure here means the DSL
    dataclasses disagree with source/spells/mage.csv's actual data, not
    (necessarily) a bug in build.py."""

    def setUp(self):
        self.csv_entries = _csv_entries_by_id()

    def _assert_matches_csv(self, dsl_spell: Spell) -> None:
        csv_entry = self.csv_entries[dsl_spell.id]
        reuse = _fresh_reuse()
        csv_row = build.build_spell_row(csv_entry, reuse)
        dsl_row = build.build_spell_row(dsl_spell.to_entry(), reuse)
        self.assertEqual(
            csv_row,
            dsl_row,
            f"spell {dsl_spell.id} ({dsl_spell.name}): DSL-built row differs from "
            f"CSV-built row",
        )

    def test_frostbolt(self):
        self._assert_matches_csv(_dsl_frostbolt())

    def test_polymorph(self):
        self._assert_matches_csv(_dsl_polymorph())

    def test_blizzard(self):
        self._assert_matches_csv(_dsl_blizzard())


if __name__ == "__main__":
    unittest.main()
