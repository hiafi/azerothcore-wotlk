"""
Phase 0 validation for `lib/dsl/` (`.agents/plans/spell-source-dsl/
spell-source-dsl.PLAN.md`).

Proves the DSL can reproduce, byte-for-byte, the exact `spell_dbc` row the
CSV-driven pipeline built for real, real spells - Frostbolt (116), Polymorph
(118), Blizzard (10), Invisibility (66), Frozen Orb Pulse (200008),
hand-ported here from a frozen historical copy of `source/spells/mage.csv`
(see `_FROZEN_MAGE_CSV_SUBSET` - that file no longer exists post-Phase-4,
Mage having fully migrated to `source/classes/mage.py`). Both the CSV-parsed
entry and the hand-written DSL `Spell` are run through the *same*,
completely unmodified `build.build_spell_row` (with one shared
`ReuseContext` per spell, so an identical `cast_time_ms`/`range_yards`/
`duration_ms`/`radius_yards` resolves to the identical reused-or-minted
secondary-DBC index either way) - the whole point being that `lib/build.py`
itself needed zero changes to accept DSL-built entries. See this package's
`lib/dsl/__init__.py` docstring for what's in and out of scope for Phase 0.
The last two spells are Phase 4 regressions (a leading empty effect slot,
and an effect inheriting the spell-level radius) - see their own
`_dsl_*`/test docstrings.

No test harness exists elsewhere in apps/dbc-tools/ beyond `test_sql_dump.py`
(also plain stdlib `unittest`) - matching that. Run directly:

    python3 apps/dbc-tools/lib/test_dsl.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, source  # noqa: E402
from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, School, Spell  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

IDS_YAML = TOOL_ROOT / "source" / "ids.yaml"

# Frozen historical copy of the exact 5 rows this suite checks, from
# source/spells/mage.csv as it stood right before Phase 4 migrated Mage to
# source/classes/mage.py (spell-source-dsl.PLAN.md) - that file no longer
# exists (Mage's source of truth is now source/classes/mage.py alone), so
# this suite can't read it live anymore. Frozen on purpose: this test's job
# was always "does the DSL reproduce what real CSV-driven parsing produces
# for real rows", which is a statement about the CSV *format*, not about
# whatever happens to be live in source/ right now - freezing the input
# keeps that meaning intact instead of quietly becoming "does the DSL match
# itself" once nothing generates these rows from CSV anymore.
_FROZEN_MAGE_CSV_SUBSET = \
'id,name,school,dispel,mechanic,attributes,category,cast_time_ms,cooldown_ms,category_cooldown_ms,power_type,mana_cost,mana_cost_pct,range_yards,radius_yards,duration_ms,effect1,effect2,effect3,spell_icon_id,spell_weight,coeff_weight,raw_overrides,notes\n10,Blizzard,16,0,0,65536,0,0,0,0,0,0,74,30.0,,8000,"{""amplitude"": 0, ""apply_aura"": 4, ""base_points"": 24, ""chain_targets"": 0, ""die_sides"": 1, ""implicit_target_a"": 28, ""implicit_target_b"": 0, ""mechanic"": 0, ""misc_value"": 0, ""points_per_level"": 3.1, ""radius_yards"": 8.0, ""trigger_spell"": 0, ""type"": 27}","{""amplitude"": 1000, ""apply_aura"": 23, ""base_points"": 0, ""chain_targets"": 0, ""die_sides"": 0, ""implicit_target_a"": 1, ""implicit_target_b"": 0, ""mechanic"": 0, ""misc_value"": 0, ""points_per_level"": 0.0, ""radius_yards"": null, ""trigger_spell"": 42208, ""type"": 6}",,285,,,"{""AttributesEx"": 268435596, ""AttributesEx2"": 4194304, ""AttributesEx5"": 8192, ""AuraDescription_Lang_Mask"": 16712190, ""AuraDescription_Lang_enUS"": ""$42208s1 Frost damage every $42208t1 $lsecond:seconds;."", ""BaseLevel"": 20, ""CastingTimeIndex"": 1, ""ChannelInterruptFlags"": 31788, ""DefenseType"": 1, ""Description_Lang_Mask"": 16712190, ""Description_Lang_enUS"": ""Ice shards pelt the target area doing ${$42208m1*8*$<mult>} Frost damage over $10d."", ""EffectBonusMultiplier_1"": 0.11900000274181366, ""EffectChainAmplitude_1"": 1.0, ""EffectChainAmplitude_2"": 1.0, ""EffectChainAmplitude_3"": 1.0, ""EquippedItemClass"": -1, ""InterruptFlags"": 15, ""MaxLevel"": 80, ""NameSubtext_Lang_Mask"": 16712190, ""NameSubtext_Lang_enUS"": """", ""Name_Lang_Mask"": 16712190, ""PreventionType"": 1, ""ProcChance"": 100, ""SpellClassMask_1"": 524416, ""SpellClassSet"": 3, ""SpellDescriptionVariableID"": 167, ""SpellLevel"": 20, ""SpellPriority"": 50, ""SpellVisualID_1"": 9490, ""StartRecoveryCategory"": 133, ""StartRecoveryTime"": 1500, ""Targets"": 64}",single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80\n66,Invisibility,64,6,0,1114112,1162,0,180000,0,0,0,16,0.0,,3000,,"{""amplitude"": 1000, ""apply_aura"": 23, ""base_points"": -1, ""chain_targets"": 0, ""die_sides"": 1, ""implicit_target_a"": 1, ""implicit_target_b"": 0, ""mechanic"": 0, ""misc_value"": 0, ""points_per_level"": 0.0, ""radius_yards"": null, ""trigger_spell"": 35009, ""type"": 6}",,2308,,,"{""AttributesEx"": 131072, ""AttributesEx3"": 1073741824, ""AttributesEx4"": 64, ""AuraDescription_Lang_Mask"": 16712190, ""AuraDescription_Lang_enUS"": ""Fading."", ""AuraInterruptFlags"": 660484, ""BaseLevel"": 58, ""CastingTimeIndex"": 1, ""DefenseType"": 1, ""Description_Lang_Mask"": 16712190, ""Description_Lang_enUS"": ""$?s54354[Instantly makes the caster invisible, reducing all threat.][Fades the caster to invisibility over $66d, reducing threat each second.]  The effect is cancelled if you perform any actions.  While invisible, you can only see other invisible targets and those who can see invisible.  Lasts $32612d."", ""EffectBasePoints_3"": 99, ""EffectChainAmplitude_1"": 1.0, ""EffectChainAmplitude_2"": 1.0, ""EffectChainAmplitude_3"": 1.0, ""EffectDieSides_3"": 1, ""EquippedItemClass"": -1, ""ExcludeCasterAuraState"": 12, ""InterruptFlags"": 8, ""NameSubtext_Lang_Mask"": 16712188, ""Name_Lang_Mask"": 16712190, ""PreventionType"": 1, ""ProcChance"": 101, ""RangeIndex"": 1, ""SpellClassMask_1"": 2147483648, ""SpellClassMask_2"": 262144, ""SpellClassSet"": 3, ""SpellLevel"": 58, ""SpellPriority"": 50, ""SpellVisualID_1"": 7964, ""StartRecoveryCategory"": 133, ""StartRecoveryTime"": 1500}",pulled from existing data\n116,Frostbolt,16,1,0,65536,0,2000,0,0,0,0,11,30.0,,5000,"{""amplitude"": 0, ""apply_aura"": 33, ""base_points"": -41, ""chain_targets"": 0, ""die_sides"": 1, ""implicit_target_a"": 6, ""implicit_target_b"": 0, ""mechanic"": 11, ""misc_value"": 0, ""points_per_level"": 0.0, ""radius_yards"": null, ""trigger_spell"": 0, ""type"": 6}","{""amplitude"": 0, ""apply_aura"": 0, ""base_points"": 17, ""chain_targets"": 0, ""die_sides"": 3, ""implicit_target_a"": 6, ""implicit_target_b"": 0, ""mechanic"": 0, ""misc_value"": 0, ""points_per_level"": 7.5464, ""radius_yards"": null, ""trigger_spell"": 0, ""type"": 2}","{""amplitude"": 0, ""apply_aura"": 118, ""base_points"": -1, ""chain_targets"": 0, ""die_sides"": 1, ""implicit_target_a"": 6, ""implicit_target_b"": 0, ""mechanic"": 0, ""misc_value"": 127, ""points_per_level"": 0.0, ""radius_yards"": null, ""trigger_spell"": 0, ""type"": 6}",188,,,"{""AttributesEx6"": 2097152, ""AuraDescription_Lang_Mask"": 16712190, ""AuraDescription_Lang_enUS"": ""Movement slowed by $s1%."", ""BaseLevel"": 4, ""DefenseType"": 1, ""Description_Lang_Mask"": 16712190, ""Description_Lang_enUS"": ""Launches a bolt of frost at the enemy, causing ${$m2*$<mult>} to ${$M2*$<mult>} Frost damage and slowing movement speed by $s1% for $d."", ""EffectBonusMultiplier_2"": 0.8569999933242798, ""EffectChainAmplitude_1"": 1.0, ""EffectChainAmplitude_2"": 1.0, ""EffectChainAmplitude_3"": 1.0, ""EquippedItemClass"": -1, ""FacingCasterFlags"": 1, ""InterruptFlags"": 15, ""MaxLevel"": 80, ""NameSubtext_Lang_Mask"": 16712190, ""NameSubtext_Lang_enUS"": """", ""Name_Lang_Mask"": 16712190, ""PreventionType"": 1, ""ProcChance"": 101, ""Speed"": 28.0, ""SpellClassMask_1"": 32, ""SpellClassSet"": 3, ""SpellDescriptionVariableID"": 167, ""SpellLevel"": 4, ""SpellPriority"": 50, ""SpellVisualID_1"": 13, ""StartRecoveryCategory"": 133, ""StartRecoveryTime"": 1500}",single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80\n118,Polymorph,64,1,17,1074855936,0,1500,0,0,0,0,7,30.0,,20000,"{""amplitude"": 0, ""apply_aura"": 5, ""base_points"": -1, ""chain_targets"": 0, ""die_sides"": 1, ""implicit_target_a"": 6, ""implicit_target_b"": 0, ""mechanic"": 0, ""misc_value"": 0, ""points_per_level"": 0.0, ""radius_yards"": null, ""trigger_spell"": 0, ""type"": 6}","{""amplitude"": 0, ""apply_aura"": 56, ""base_points"": 0, ""chain_targets"": 0, ""die_sides"": 0, ""implicit_target_a"": 6, ""implicit_target_b"": 0, ""mechanic"": 0, ""misc_value"": 16372, ""points_per_level"": 0.0, ""radius_yards"": null, ""trigger_spell"": 0, ""type"": 6}",,82,,,"{""AttributesEx"": 262144, ""AttributesEx2"": 64, ""AttributesEx4"": 1610612736, ""AttributesEx5"": 32, ""AttributesEx6"": 8388608, ""AuraDescription_Lang_Mask"": 16712190, ""AuraDescription_Lang_enUS"": ""Cannot attack or cast spells.  Increased regeneration."", ""AuraInterruptFlags"": 524290, ""BaseLevel"": 8, ""CastingTimeIndex"": 16, ""DefenseType"": 1, ""Description_Lang_Mask"": 16712190, ""Description_Lang_enUS"": ""Transforms the enemy into a sheep, forcing it to wander around for up to $d.  While wandering, the sheep cannot attack or cast spells but will regenerate very quickly.  Any damage will transform the target back into its normal form.  Only one target can be polymorphed at a time.  Only works on Beasts, Humanoids and Critters."", ""EffectBasePoints_3"": -1, ""EffectChainAmplitude_1"": 1.0, ""EffectChainAmplitude_2"": 1.0, ""EffectChainAmplitude_3"": 1.0, ""EffectDieSides_3"": 1, ""EquippedItemClass"": -1, ""InterruptFlags"": 15, ""MaxLevel"": 80, ""NameSubtext_Lang_Mask"": 16712190, ""NameSubtext_Lang_enUS"": """", ""Name_Lang_Mask"": 16712190, ""PreventionType"": 1, ""ProcChance"": 101, ""SpellClassMask_1"": 16777216, ""SpellClassSet"": 3, ""SpellLevel"": 8, ""SpellPriority"": 50, ""SpellVisualID_1"": 12978, ""StartRecoveryCategory"": 133, ""StartRecoveryTime"": 1500, ""TargetCreatureType"": 193}",single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80\n200008,Frozen Orb Pulse,16,1,0,0,0,0,0,0,0,0,,,10,4000,"{""amplitude"": 0, ""apply_aura"": 0, ""base_points"": 199, ""chain_targets"": 0, ""die_sides"": 1, ""implicit_target_a"": 16, ""implicit_target_b"": 0, ""mechanic"": 0, ""misc_value"": 0, ""points_per_level"": 0.0, ""trigger_spell"": 0, ""type"": 2}","{""amplitude"": 0, ""apply_aura"": 33, ""base_points"": -31, ""chain_targets"": 0, ""die_sides"": 1, ""implicit_target_a"": 16, ""implicit_target_b"": 0, ""mechanic"": 11, ""misc_value"": 0, ""points_per_level"": 0.0, ""trigger_spell"": 0, ""type"": 6}",,2132,,0.15,"{""SpellClassSet"": 0, ""Name_Lang_Mask"": 16712190, ""Description_Lang_Mask"": 0, ""AuraDescription_Lang_Mask"": 16712188, ""AuraDescription_Lang_enUS"": ""Movement speed reduced."", ""EquippedItemClass"": -1, ""ProcChance"": 101, ""RangeIndex"": 1, ""SpellPriority"": 50}","Frost Mage rework (docs/frost-mage-redesign.md sec 1, Frozen Orb\'s pulse): ""Every 1 sec, deals 200 Frost damage plus 0.15 spell power coefficient to all enemies within 10 yards, and applies a chill reducing movement speed by 30% for 4 sec."" Two effects on one row, same shape as the real Cone of Cold (120): SCHOOL_DAMAGE (base_points 199, -1 convention) + APPLY_AURA MOD_DECREASE_SPEED (base_points -31, -1 convention for -30%, EffectMechanic MECHANIC_SNARE=11), both TARGET_UNIT_DEST_AREA_ENEMY (16, not the SRC variant this row originally shipped with - see ""Cast by"" below for why). Neither effect JSON sets its own ""radius_yards"" key (build.py only falls back to the row\'s top-level radius_yards when the per-effect key is absent, not when it\'s present-but-null - learned the hard way diffing a hand-built row against generate.py\'s actual output), so both inherit the row\'s radius_yards (10, -> EffectRadiusIndex 13, the same row Cone of Cold\'s own radius already reuses) and duration_ms (4000, -> DurationIndex 35, the same row Shattering Cold/200003 already reuses). Coefficient (0.15) goes through spell_bonus_data like every other new spell this session - see the accompanying pending SQL. Cast by the OWNING PLAYER (not the orb) at an explicit dest = the orb\'s live position, once per second, from npc_mage_frozen_orb::UpdateAI (spell_mage.cpp) - a deliberate change from the original SRC-based ""orb self-casts via a periodic aura (200009)"" design, which silently attributed all damage/threat/combat-log entries to the orb instead of the player (root-caused via live playtest: FoF procced and the pulse showed in the combat log, but never in the player\'s own damage meter). TARGET_UNIT_DEST_AREA_ENEMY lets the player be the actual spell caster (correct attribution *and* correct spell-power scaling off the player\'s own stats) while still centering the AoE on the orb\'s moving position rather than the stationary player. 200009 (Frozen Orb Periodic) is no longer cast by anything - left as an orphaned row rather than deleted, see spell_mage.cpp\'s own notes. spell_mage_frozen_orb_pulse (spell_mage.cpp) still exists for BoostChillEffect (Chilled to the Bone) and to tell the orb\'s AI a pulse landed (halts movement, starts the FoF grant chain) - it does not touch the damage/slow itself, both of which are native DBC effects needing no script. Attributes=0 and no player-facing name/description text (Description_Lang_Mask=0) - never cast directly by a player action, never shown in a spellbook/tooltip."\n'


def _csv_entries_by_id() -> dict[int, dict]:
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as f:
        f.write(_FROZEN_MAGE_CSV_SUBSET)
        path = Path(f.name)
    try:
        return {e["id"]: e for e in source.load_one_spell_file(path)}
    finally:
        path.unlink()


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


def _dsl_invisibility() -> Spell:
    # Regression test for a real bug found during Phase 4's real-data
    # verification (spell-source-dsl.PLAN.md): Effect_1 is genuinely empty
    # here (Invisibility's real data lives in Effect_2) - csv_to_dsl.py used
    # to compact that gap away, silently shifting this effect into slot 1.
    # `effects[0] = None` is the explicit "this slot is empty" placeholder;
    # see Spell.effects's docstring for why that must never be compacted.
    return Spell(
        id=66,
        name="Invisibility",
        school=School.ARCANE,
        dispel=DispelType.INVISIBILITY,
        attributes=1114112,
        category=1162,
        cooldown_ms=180000,
        mana_cost_pct=16,
        range_yards=0.0,
        duration_ms=3000,
        effects=[
            None,
            Effect(
                type=EffectType.APPLY_AURA,
                apply_aura=AuraType.PERIODIC_TRIGGER_SPELL,
                base_points=-1,
                implicit_target_a=1,
                amplitude=1000,
                trigger_spell=35009,
            ),
        ],
        spell_icon_id=2308,
        notes="pulled from existing data",
        raw_overrides={
            "AttributesEx": 131072,
            "AttributesEx3": 1073741824,
            "AttributesEx4": 64,
            "AuraDescription_Lang_Mask": 16712190,
            "AuraDescription_Lang_enUS": "Fading.",
            "AuraInterruptFlags": 660484,
            "BaseLevel": 58,
            "CastingTimeIndex": 1,
            "DefenseType": 1,
            "Description_Lang_Mask": 16712190,
            "Description_Lang_enUS": (
                "$?s54354[Instantly makes the caster invisible, reducing all threat.][Fades the "
                "caster to invisibility over $66d, reducing threat each second.]  The effect is "
                "cancelled if you perform any actions.  While invisible, you can only see other "
                "invisible targets and those who can see invisible.  Lasts $32612d."
            ),
            "EffectBasePoints_3": 99,
            "EffectChainAmplitude_1": 1.0,
            "EffectChainAmplitude_2": 1.0,
            "EffectChainAmplitude_3": 1.0,
            "EffectDieSides_3": 1,
            "EquippedItemClass": -1,
            "ExcludeCasterAuraState": 12,
            "InterruptFlags": 8,
            "NameSubtext_Lang_Mask": 16712188,
            "Name_Lang_Mask": 16712190,
            "PreventionType": 1,
            "ProcChance": 101,
            "RangeIndex": 1,
            "SpellClassMask_1": 2147483648,
            "SpellClassMask_2": 262144,
            "SpellClassSet": 3,
            "SpellLevel": 58,
            "SpellPriority": 50,
            "SpellVisualID_1": 7964,
            "StartRecoveryCategory": 133,
            "StartRecoveryTime": 1500,
        },
    )


def _dsl_frozen_orb_pulse() -> Spell:
    # Regression test for a second real bug found during Phase 4's
    # real-data verification: neither effect sets its own radius_yards, so
    # both must inherit the spell-level radius_yards=10.0 - Effect.to_dict()
    # used to always emit an explicit "radius_yards": None, which
    # lib/build.py's `effect.get("radius_yards", default_radius)` treats as
    # "explicitly no radius" (key present) rather than "inherit the
    # spell's" (key absent), silently zeroing EffectRadiusIndex.
    return Spell(
        id=200008,
        name="Frozen Orb Pulse",
        school=School.FROST,
        dispel=DispelType.MAGIC,
        radius_yards=10.0,
        duration_ms=4000,
        effects=[
            Effect(
                type=EffectType.SCHOOL_DAMAGE,
                base_points=199,
                implicit_target_a=16,
            ),
            Effect(
                type=EffectType.APPLY_AURA,
                apply_aura=AuraType.MOD_DECREASE_SPEED,
                base_points=-31,
                mechanic=Mechanic.SNARE,
                implicit_target_a=16,
            ),
        ],
        spell_icon_id=2132,
        coeff_weight=0.15,
        raw_overrides={
            "SpellClassSet": 0,
            "Name_Lang_Mask": 16712190,
            "Description_Lang_Mask": 0,
            "AuraDescription_Lang_Mask": 16712188,
            "AuraDescription_Lang_enUS": "Movement speed reduced.",
            "EquippedItemClass": -1,
            "ProcChance": 101,
            "RangeIndex": 1,
            "SpellPriority": 50,
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

    def test_invisibility_leading_empty_effect_slot(self):
        self._assert_matches_csv(_dsl_invisibility())

    def test_frozen_orb_pulse_effect_inherits_spell_level_radius(self):
        self._assert_matches_csv(_dsl_frozen_orb_pulse())


if __name__ == "__main__":
    unittest.main()
