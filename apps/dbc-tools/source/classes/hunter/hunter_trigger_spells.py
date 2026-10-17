"""
Hunter - spells that are never directly cast - proc/periodic-tick effects, trigger_spell targets, hidden talent-rank buffs, etc..

Split from a single source/classes/hunter.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .hunter_...` below) resolve.
"""

from lib.dsl import AuraType, CombatRating, DispelType, Effect, EffectType, Mechanic, School, SpellModOp
from lib.dsl.registry import spell

from . import _masks as m
from .hunter_bm_spells import PHOENIX_PLUME_REVIVE_PCT
from .hunter_mm_spells import (
    BARRAGE_ICD_MS, COMBAT_EXPERIENCE_CAPSTONE_PCT, FOCUSED_AIM_CDR_MS, RAPID_KILLING_HEALTH_PCT, fire_mm_buff_201940,
    mm_volley_1172,
)

_PLUME_REVIVE = str(int(PHOENIX_PLUME_REVIVE_PCT['value']))

# ---- hunter-rework S2a A3 (MARKSMANSHIP 5 / 6): helpers for the stock MM ranks and buffs edited in place below ----
_MM_MASK_KEYS = {1: 'A', 2: 'B', 3: 'C'}


def _mm_masks(masks):
    """`masks` maps a 1-based effect index to its (d0, d1, d2) EffectSpellClassMask triple. In the raw key the letter
    is the effect and the digit the dword (README gotcha); zero dwords are left out."""
    overrides = {}
    for effect_index, triple in masks.items():
        for dword, value in enumerate(triple, start=1):
            if value:
                overrides[f'EffectSpellClassMask{_MM_MASK_KEYS[effect_index]}_{dword}'] = value
    return overrides


def _mm_desc(text, capstone, last):
    """MARKSMANSHIP 6 header: grey capstone suffix on the ranks below the last, plain on the last."""
    if last:
        return f"{text}\n\nCapstone Bonus: {capstone}"
    return f"{text}\n\n|cFF9D9D9DCapstone Bonus: {capstone}|r"


def _mm_c(row):
    """A const() row's value as tooltip text (35.0 -> '35')."""
    value = row['value']
    return str(int(value)) if float(value).is_integer() else str(value)


def _mm_sec(row):
    """A millisecond const() row's value as whole-second tooltip text (1000 -> '1')."""
    return _mm_c({'value': row['value'] / 1000})


freezing_trap_effect_3355 = spell(
    id=3355,
    name='Freezing Trap Effect',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.FREEZE,
    attributes=1073741824,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=10.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=308, misc_value=7),
    ],
    spell_icon_id=180,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 262144, 'AttributesEx4': 536872960, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Frozen.', 'AuraInterruptFlags': 4718594, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Place a frost trap that freezes the first enemy that approaches, preventing all action for up to $3355d.  Any damage caused will break the ice.  Trap will exist for $1499d.  Only one trap can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 522959, 'EffectSpellClassMaskB_2': 3632402689, 'EffectSpellClassMaskB_3': 184137, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 8, 'SpellClassSet': 9, 'SpellLevel': 20, 'SpellVisualID_1': 4499},
)


immolation_trap_13797 = spell(
    id=13797,
    name='Immolation Trap',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=10.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, ap_potency=49.5, potency_kind='periodic', implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    spell_icon_id=678,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 16); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (hunter pass): converted to ap_potency=49.5 (potency-report default, base/coef already agreed); tooltip simplified from the old $<mult>/$<duration> SpellDescriptionVariable formula to {pot1}/{pot1.total} (same convention as every other conversion - SpellDescriptionVariableID left in raw_overrides, now unused).',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '{pot1} Fire damage every $t1 seconds.', 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Place a fire trap that will burn the first enemy to approach for {pot1.total} Fire damage over $13797d.  Trap will exist for $13797d.  Only one trap can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': 131072, 'SpellClassSet': 9, 'SpellDescriptionVariableID': 121, 'SpellLevel': 16, 'SpellVisualID_1': 4500},
)


explosive_trap_effect_13812 = spell(
    id=13812,
    name='Explosive Trap Effect',
    school=School.FIRE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=134.2, potency_kind='direct', implicit_target_a=22, implicit_target_b=15, radius_yards=10.0),
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=14, points_per_level=1.6304347826086956, implicit_target_a=28, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000, radius_yards=10.0),
    ],
    spell_icon_id=37,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 34); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (hunter pass): converted effect 1 (the explosion burst) to ap_potency=134.2 (potency-report default, base/coef already agreed); effect 2 (the burn-over-time persistent-area aura) is left unconverted - potency_report.py\'s classify_effect() does not scan PERSISTENT_AREA_AURA/PERIODIC_DAMAGE on this effect shape, so it never appeared in the P3 report.',
    raw_overrides={'AttributesEx': 136, 'AttributesEx3': 262720, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s2 Fire damage every $t2 seconds.', 'BaseLevel': 34, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Place a fire trap that explodes when an enemy approaches, causing {pot1} Fire damage and burning all enemies for $13812o2 additional Fire damage over $13812d to all within $13812a1 yards.  Trap will exist for $13813d.  Only one trap can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 4, 'SpellClassMask_3': 16384, 'SpellClassSet': 9, 'SpellLevel': 34, 'SpellVisualID_1': 10389, 'Targets': 64},
)


improved_scorpid_sting_19491 = spell(
    id=19491,
    name='Improved Scorpid Sting',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=112, misc_value=2388),
    ],
    spell_icon_id=256,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the Stamina of targets affected by your Scorpid Sting by 10% of the amount of Strength reduced.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 32768, 'EffectSpellClassMaskA_1': 32768, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_eyes_of_the_beast_19557 = spell(
    id=19557,
    name='Improved Eyes of the Beast',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29999, points_per_level=500.0, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=49,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Eyes of the Beast by $/1000;s1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 4194304, 'EffectSpellClassMaskA_1': 4194304, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


bestial_fury_19603 = spell(
    id=19603,
    name='Bestial Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, points_per_level=1.3333333333333333, implicit_target_a=1, apply_aura=108, misc_value=18),
    ],
    spell_icon_id=50,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your pet a $s1% chance to gain $19604s1 Focus after getting a critical strike.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 1073741824, 'EffectSpellClassMaskA_1': 1073741824, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


wyvern_sting_24131 = spell(
    id=24131,
    name='Wyvern Sting',
    school=School.NATURE,
    dispel=DispelType.POISON,
    attributes=159383552,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, sp_potency=129.0, potency_kind='periodic', implicit_target_a=25, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
    ],
    spell_icon_id=1721,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (hunter pass): converted to sp_potency=129.0 (potency-report default, base/coef already agreed - this effect already had genuine spell-power scaling live, not attack power, despite being a Hunter ability).',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '{pot1} Nature damage every $t1 seconds.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A stinging shot that puts the target to sleep for $19386d.  Any damage will cancel the effect.  When the target wakes up, the Sting causes {pot1.total} Nature damage over $24131d.  Only one Sting per Hunter can be active on the target at a time.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 0.16699999570846558, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 256, 'SpellClassSet': 9, 'SpellLevel': 40, 'SpellVisualID_1': 7206},
)


silent_hunter_34472 = spell(
    id=34472,
    name='Silent Hunter',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, points_per_level=-0.16666666666666666, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=127),
    ],
    spell_icon_id=2221,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces threat from all attacks by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


displacement_34478 = spell(
    id=34478,
    name='Displacement',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2, points_per_level=-0.03333333333333333, implicit_target_a=1, apply_aura=184),
        Effect(type=EffectType.APPLY_AURA, base_points=-2, points_per_level=-0.03333333333333333, implicit_target_a=1, apply_aura=185),
        Effect(type=EffectType.APPLY_AURA, base_points=-2, points_per_level=-0.03333333333333333, implicit_target_a=1, apply_aura=186, misc_value=126),
    ],
    spell_icon_id=2235,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces your chance to be hit by all attacks by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


master_tactician_34833 = spell(
    id=34833,
    name='Master Tactician',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, points_per_level=0.13333333333333333, implicit_target_a=1, apply_aura=52),
    ],
    spell_icon_id=2233,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Critical strike chance with all attacks increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your successful ranged attacks have a chance to increase your critical strike chance with all attacks by $34833s1% for $34833d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 522819, 'EffectSpellClassMaskA_2': 128, 'EffectSpellClassMaskB_1': 522819, 'EffectSpellClassMaskB_2': 1, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9, 'EffectSpellClassMaskA_3': 536870912},
)


rapid_killing_35098 = spell(
    id=35098,
    name='Rapid Killing',
    school=School.NORMAL,
    attributes=134217728,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=2285,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 5.10): stock row edited in place; Rapid Killing capstone buff (201981 kill proc): +30% [29], ppl 0, 2 charges, mask RAPID_KILLING_BUFF (adds Kill Shot d1 0x800000), ProcTypeMask 0 (spent by its 8 CAST row, A1).',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712190,
        'AuraDescription_Lang_enUS': 'Your next $n Aimed Shots, Arcane Shots, Kill Shots or Chimera Shots deal $s1% more damage.',
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Killing an enemy that yields experience causes your next $35098n Aimed Shots, Arcane Shots, Kill Shots or Chimera Shots to deal $35098s1% more damage.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'MaxLevel': 80,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': '',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 100,
        'ProcCharges': 2,
        'ProcTypeMask': 0,
        'RangeIndex': 1,
        'SpellClassMask_2': 16777216,
        'SpellClassSet': 9,
        **_mm_masks({1: m.RAPID_KILLING_BUFF}),
    },
)


volley_42243 = spell(
    id=42243,
    name='Volley',
    school=School.ARCANE,
    attributes=2,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=75.5, potency_kind='direct', implicit_target_a=76, implicit_target_b=16, radius_yards=8.0),
    ],
    spell_icon_id=126,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (hunter pass): converted to ap_potency=75.5 (potency-report default, base/coef already agreed). hunter-rework S2a A3 (MARKSMANSHIP 5.11/5.12): {pot1*mult} with tooltip_vars 1172 (Barrage, Rain of Arrows).',
    tooltip_vars=mm_volley_1172,
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 1073741824, 'AttributesEx3': 32, 'AttributesEx5': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Continuously fires a volley of ammo at the target area, causing {pot1*mult} Arcane damage to enemy targets within $a1 yards every ${$1510d/6}.2 $Lsecond:seconds; for $1510d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 135, 'SpellClassMask_1': 8192, 'SpellClassSet': 9, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 9493, 'StartRecoveryCategory': 133},
)


feeding_frenzy_60096 = spell(
    id=60096,
    name='Feeding Frenzy',
    school=School.NORMAL,
    attributes=272,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, points_per_level=0.13333333333333333, implicit_target_a=1, apply_aura=79, misc_value=7295),
    ],
    spell_icon_id=2960,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your pet does $s1% additional damage to targets with less than 35% health.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1026, 'EffectSpellClassMaskA_2': 131078, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 9, 'SpellPriority': 50},
)


sniper_training_64418 = spell(
    id=64418,
    name='Sniper Training',
    school=School.NATURE,
    attributes=134217728,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=3437,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 5.11): stock row edited in place; +1% per stack [0], ppl 0, 3 stacks, 12 s; eff0 DAMAGE on HUNTER_SHOTS, eff1 DOT on the mark DoTs (d2 b28); visible (M1).',
    raw_overrides={
        'AttributesEx': 32,
        'AttributesEx2': 16384,
        'AuraDescription_Lang_Mask': 16712190,
        'AuraDescription_Lang_enUS': 'Damage of your shots increased by $s1%.',
        'CastingTimeIndex': 1,
        'CumulativeAura': 3,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'While you stand still for $53302s1 sec, you gain Sniper Training, increasing the damage of your shots by $64418s1% for $64418d. Stacks up to 3 times.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'MaxLevel': 80,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': '',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.HUNTER_SHOTS, 2: (0, 0, m.MARK_DOT)}),
    },
)


ferocious_inspiration_75593 = spell(
    id=75593,
    name='Ferocious Inspiration',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=65, implicit_target_a=1, apply_aura=79, misc_value=127, radius_yards=100.0),
    ],
    spell_icon_id=2232,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80; hunter-rework S1a A3 (B8): points_per_level 0, MaxLevel 0 so rank 1 is a flat 1%',
    raw_overrides={'AttributesEx6': 1140850688, 'AttributesEx7': 0, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All damage increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'All party and raid members have all damage increased by $s1%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67108864, 'EquippedItemClass': -1, 'MaxLevel': 0, 'NameSubtext_Lang_Mask': 16712172, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 32, 'SpellClassSet': 9},
)


ferocious_inspiration_75446 = spell(
    id=75446,
    name='Ferocious Inspiration',
    school=1,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=65, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=127, radius_yards=100.0),
    ],
    spell_icon_id=2232,
    notes='pulled from existing data; hunter-rework S1b PT-1: AttributesEx7 0 (the stock 0x10000000 consolidates the buff into one aura-bar slot)',
    raw_overrides={'AttributesEx6': 1140850688, 'AttributesEx7': 0, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 67108864, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'All party and raid members have all damage increased by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All damage increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 9, 'SpellClassMask_2': 32, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


ferocious_inspiration_75447 = spell(
    id=75447,
    name='Ferocious Inspiration',
    school=1,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=65, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=127, radius_yards=100.0),
    ],
    spell_icon_id=2232,
    notes='pulled from existing data; hunter-rework S1b PT-1: AttributesEx7 0 (the stock 0x10000000 consolidates the buff into one aura-bar slot)',
    raw_overrides={'AttributesEx6': 1140850688, 'AttributesEx7': 0, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 67108864, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'All party and raid members have all damage increased by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All damage increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 9, 'SpellClassMask_2': 32, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


savage_strikes_19159 = spell(
    id=19159,
    name='Savage Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=86,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of Raptor Strike, Mongoose Bite and Counterattack by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskA_2': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


savage_strikes_19160 = spell(
    id=19160,
    name='Savage Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=86,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of Raptor Strike, Mongoose Bite and Counterattack by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskA_2': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


entrapment_19184 = spell(
    id=19184,
    name='Entrapment',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=19185),
    ],
    spell_icon_id=20,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Frost Trap or Snake Trap are triggered you entrap all afflicted targets, preventing them from moving for $19185d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2097152, 'RangeIndex': 1, 'SpellClassSet': 9},
)


survivalist_19255 = spell(
    id=19255,
    name='Survivalist',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137, misc_value=2),
    ],
    spell_icon_id=164,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Stamina by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


survivalist_19256 = spell(
    id=19256,
    name='Survivalist',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=137, misc_value=2),
    ],
    spell_icon_id=164,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Stamina by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


survivalist_19257 = spell(
    id=19257,
    name='Survivalist',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=137, misc_value=2),
    ],
    spell_icon_id=164,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Stamina by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


survivalist_19258 = spell(
    id=19258,
    name='Survivalist',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=137, misc_value=2),
    ],
    spell_icon_id=164,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Stamina by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


survivalist_19259 = spell(
    id=19259,
    name='Survivalist',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=137, misc_value=2),
    ],
    spell_icon_id=164,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Stamina by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


survival_tactics_19286 = spell(
    id=19286,
    name='Survival Tactics',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=857,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the chance your Feign Death ability and all trap spells will be resisted by $s1%, and reduces the cooldown of your Disengage ability by $/1000;S2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 284, 'EffectSpellClassMaskA_2': 8192, 'EffectSpellClassMaskB_2': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


survival_tactics_19287 = spell(
    id=19287,
    name='Survival Tactics',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-4001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=857,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the chance your Feign Death ability and all trap spells will be resisted by $s1%, and reduces the cooldown of your Disengage ability by $/1000;S2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 284, 'EffectSpellClassMaskA_2': 8192, 'EffectSpellClassMaskB_2': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 17408, 'RangeIndex': 1, 'SpellClassSet': 9},
)


surefooted_19290 = spell(
    id=19290,
    name='Surefooted',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=232, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=232, misc_value=7),
    ],
    spell_icon_id=246,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the duration of movement impairing effects by $s1%.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


surefooted_19294 = spell(
    id=19294,
    name='Surefooted',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=232, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=232, misc_value=7),
    ],
    spell_icon_id=246,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the duration of movement impairing effects by $s1%.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


trap_mastery_19376 = spell(
    id=19376,
    name='Trap Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=69,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Frost Trap and Freezing Trap - Increases the duration by $s1%.\r\n\r\nImmolation Trap, Explosive Trap and Black Arrow - Increases the periodic damage done by $s2%.\r\n\r\nSnake Trap - Increases the number of snakes summoned by $*2;s3.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 24, 'EffectSpellClassMaskB_1': 4, 'EffectSpellClassMaskB_2': 134217728, 'EffectSpellClassMaskB_3': 131072, 'EffectSpellClassMaskC_2': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


entrapment_19387 = spell(
    id=19387,
    name='Entrapment',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64803),
    ],
    spell_icon_id=20,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Frost Trap or Snake Trap are triggered you entrap all afflicted targets, preventing them from moving for $64803d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2097152, 'RangeIndex': 1, 'SpellClassSet': 9},
)


entrapment_19388 = spell(
    id=19388,
    name='Entrapment',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64804),
    ],
    spell_icon_id=20,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Frost Trap or Snake Trap are triggered you entrap all afflicted targets, preventing them from moving for $64804d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2097152, 'RangeIndex': 1, 'SpellClassSet': 9},
)


lone_survivor_19407 = spell(
    id=19407,
    name='Lone Survivor',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=500),
    ],
    spell_icon_id=535,
    notes="hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; repurposed Improved Concussive Shot (row 1341): eff0 Classic % / eff1 Classless % (DUMMY, read by S2b's spell_hun_lone_survivor), eff2 PERIODIC_DUMMY 500 ms; stock masks cleared; attributes 448 kept (live).",
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'While you have no pet, your damage is increased by $s1% ($s2% on the Classless realm).',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
    },
)


lone_survivor_19412 = spell(
    id=19412,
    name='Lone Survivor',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=500),
    ],
    spell_icon_id=535,
    notes="hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; repurposed Improved Concussive Shot (row 1341): eff0 Classic % / eff1 Classless % (DUMMY, read by S2b's spell_hun_lone_survivor), eff2 PERIODIC_DUMMY 500 ms; stock masks cleared; attributes 448 kept (live).",
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'While you have no pet, your damage is increased by $s1% ($s2% on the Classless realm).',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
    },
)


efficiency_19416 = spell(
    id=19416,
    name='Efficiency',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=133,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 SPELLMOD_COST -> DUMMY (the 201945 buff strength the Aimed Shot handler passes), stock masks cleared, ProcTypeMask 0.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your Aimed Shot reduces the cast time and global cooldown of your next $201945n Steady Shots or Aimed Shots by $s1%. Lasts $201945d.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
    },
)


efficiency_19417 = spell(
    id=19417,
    name='Efficiency',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=133,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 SPELLMOD_COST -> DUMMY (the 201945 buff strength the Aimed Shot handler passes), stock masks cleared, ProcTypeMask 0.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your Aimed Shot reduces the cast time and global cooldown of your next $201945n Steady Shots or Aimed Shots by $s1%. Lasts $201945d.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
    },
)


efficiency_19418 = spell(
    id=19418,
    name='Efficiency',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=133,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 SPELLMOD_COST -> DUMMY (the 201945 buff strength the Aimed Shot handler passes), stock masks cleared, ProcTypeMask 0.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your Aimed Shot reduces the cast time and global cooldown of your next $201945n Steady Shots or Aimed Shots by $s1%. Lasts $201945d.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
    },
)


efficiency_19419 = spell(
    id=19419,
    name='Efficiency',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-13, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=133,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the Mana cost of your Shots and Stings by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 522752, 'EffectSpellClassMaskA_2': 2290094208, 'EffectSpellClassMaskA_3': 536870913, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


efficiency_19420 = spell(
    id=19420,
    name='Efficiency',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=133,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the Mana cost of your Shots and Stings by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 522752, 'EffectSpellClassMaskA_2': 2290094208, 'EffectSpellClassMaskA_3': 536870913, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_hunter_s_mark_19421 = spell(
    id=19421,
    name="Improved Hunter's Mark",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.EFFECT2),
        Effect(type=EffectType.APPLY_AURA, base_points=-34, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=538,
    notes="hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 SPELLMOD_EFFECT2 +33/66/100%; eff1 cost unchanged; mask Hunter's Mark (0x400) on both effects.",
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Increases the attack power bonus of your Hunter's Mark by $s1% and reduces its mana cost by $s2%.",
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: (m.HUNTERS_MARK, 0, 0), 2: (m.HUNTERS_MARK, 0, 0)}),
    },
)


improved_hunter_s_mark_19422 = spell(
    id=19422,
    name="Improved Hunter's Mark",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.EFFECT2),
        Effect(type=EffectType.APPLY_AURA, base_points=-67, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=538,
    notes="hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 SPELLMOD_EFFECT2 +33/66/100%; eff1 cost unchanged; mask Hunter's Mark (0x400) on both effects.",
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Increases the attack power bonus of your Hunter's Mark by $s1% and reduces its mana cost by $s2%.",
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: (m.HUNTERS_MARK, 0, 0), 2: (m.HUNTERS_MARK, 0, 0)}),
    },
)


improved_hunter_s_mark_19423 = spell(
    id=19423,
    name="Improved Hunter's Mark",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.EFFECT2),
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=538,
    notes="hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 SPELLMOD_EFFECT2 +33/66/100%; eff1 cost unchanged; mask Hunter's Mark (0x400) on both effects.",
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Increases the attack power bonus of your Hunter's Mark by $s1% and reduces its mana cost by $s2%.",
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: (m.HUNTERS_MARK, 0, 0), 2: (m.HUNTERS_MARK, 0, 0)}),
    },
)


precise_shots_19454 = spell(
    id=19454,
    name='Precise Shots',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=2228,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; repurposed Improved Arcane Shot (row 1346): eff0 +5/10/15% on Steady Shot; r3 eff1 DUMMY (Aimed Shot handler grants 201946); stock Arcane Shot mask dropped.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc('Increases the damage of your Steady Shot by $s1%.', 'Your Aimed Shot causes your next $201946n Steady Shots to deal $201946s1% more damage.', last=False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.STEADY_SHOT_MASK}),
    },
)


precise_shots_19455 = spell(
    id=19455,
    name='Precise Shots',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=2228,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; repurposed Improved Arcane Shot (row 1346): eff0 +5/10/15% on Steady Shot; r3 eff1 DUMMY (Aimed Shot handler grants 201946); stock Arcane Shot mask dropped.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc('Increases the damage of your Steady Shot by $s1%.', 'Your Aimed Shot causes your next $201946n Steady Shots to deal $201946s1% more damage.', last=False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.STEADY_SHOT_MASK}),
    },
)


precise_shots_19456 = spell(
    id=19456,
    name='Precise Shots',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2228,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; repurposed Improved Arcane Shot (row 1346): eff0 +5/10/15% on Steady Shot; r3 eff1 DUMMY (Aimed Shot handler grants 201946); stock Arcane Shot mask dropped.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc('Increases the damage of your Steady Shot by $s1%.', 'Your Aimed Shot causes your next $201946n Steady Shots to deal $201946s1% more damage.', last=True),
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.STEADY_SHOT_MASK}),
    },
)


barrage_19461 = spell(
    id=19461,
    name='Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=85,
    notes="hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 +5/10/15% on BARRAGE_DAMAGE (Aimed Shot leaves it), stock Volley DOT eff1 dropped; r3 eff1 DUMMY + ProcTypeMask 0x100 / ProcChance 25 (half Volley capstone, S2b's spell_proc row and script).",
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc('Increases the damage of your Multi-Shot and Volley by $s1%.', f"Your Multi-Shot has a $24691h% chance to call down a Volley at the target's location that lasts half as long and deals half the damage. This effect cannot occur more than once every {int(BARRAGE_ICD_MS['value']) // 1000} sec.", last=False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.BARRAGE_DAMAGE}),
    },
)


barrage_19462 = spell(
    id=19462,
    name='Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=85,
    notes="hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 +5/10/15% on BARRAGE_DAMAGE (Aimed Shot leaves it), stock Volley DOT eff1 dropped; r3 eff1 DUMMY + ProcTypeMask 0x100 / ProcChance 25 (half Volley capstone, S2b's spell_proc row and script).",
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc('Increases the damage of your Multi-Shot and Volley by $s1%.', f"Your Multi-Shot has a $24691h% chance to call down a Volley at the target's location that lasts half as long and deals half the damage. This effect cannot occur more than once every {int(BARRAGE_ICD_MS['value']) // 1000} sec.", last=False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.BARRAGE_DAMAGE}),
    },
)


improved_stings_19464 = spell(
    id=19464,
    name='Improved Stings',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=536,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 DOT +6/13/20% on IMPROVED_STINGS_MASK (Serpent Sting + mark DoTs); stock Viper Sting / dispel effects dropped.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Increases the damage of your Serpent Sting, Viper's Bite and Viper's Venom by $s1%.",
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.IMPROVED_STINGS_MASK}),
    },
)


improved_stings_19465 = spell(
    id=19465,
    name='Improved Stings',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=12, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=536,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 DOT +6/13/20% on IMPROVED_STINGS_MASK (Serpent Sting + mark DoTs); stock Viper Sting / dispel effects dropped.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Increases the damage of your Serpent Sting, Viper's Bite and Viper's Venom by $s1%.",
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.IMPROVED_STINGS_MASK}),
    },
)


improved_stings_19466 = spell(
    id=19466,
    name='Improved Stings',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=536,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 DOT +6/13/20% on IMPROVED_STINGS_MASK (Serpent Sting + mark DoTs); stock Viper Sting / dispel effects dropped.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Increases the damage of your Serpent Sting, Viper's Bite and Viper's Venom by $s1%.",
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.IMPROVED_STINGS_MASK}),
    },
)


mortal_shots_19485 = spell(
    id=19485,
    name='Mortal Shots',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CRIT_DAMAGE_BONUS),
    ],
    spell_icon_id=219,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 crit damage +6/13/20% on MORTAL_SHOTS_MASK; stock Serpent Sting eff1 dropped.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike damage bonus of your ranged abilities by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.MORTAL_SHOTS_MASK}),
    },
)


mortal_shots_19487 = spell(
    id=19487,
    name='Mortal Shots',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=12, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CRIT_DAMAGE_BONUS),
    ],
    spell_icon_id=219,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 crit damage +6/13/20% on MORTAL_SHOTS_MASK; stock Serpent Sting eff1 dropped.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike damage bonus of your ranged abilities by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.MORTAL_SHOTS_MASK}),
    },
)


mortal_shots_19488 = spell(
    id=19488,
    name='Mortal Shots',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CRIT_DAMAGE_BONUS),
    ],
    spell_icon_id=219,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 crit damage +6/13/20% on MORTAL_SHOTS_MASK; stock Serpent Sting eff1 dropped.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike damage bonus of your ranged abilities by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.MORTAL_SHOTS_MASK}),
    },
)


mortal_shots_19489 = spell(
    id=19489,
    name='Mortal Shots',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=23, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=47, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=219,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your ranged abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 408064, 'EffectSpellClassMaskA_2': 2155872256, 'EffectSpellClassMaskA_3': 536873537, 'EffectSpellClassMaskB_1': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


mortal_shots_19490 = spell(
    id=19490,
    name='Mortal Shots',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=219,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your ranged abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 408064, 'EffectSpellClassMaskA_2': 2155872256, 'EffectSpellClassMaskA_3': 536873537, 'EffectSpellClassMaskB_1': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


hawk_eye_19498 = spell(
    id=19498,
    name='Hawk Eye',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=5),
    ],
    spell_icon_id=161,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your ranged weapons by $s1 yards.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 522753, 'EffectSpellClassMaskA_2': 2290094208, 'EffectSpellClassMaskA_3': 536871937, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


hawk_eye_19499 = spell(
    id=19499,
    name='Hawk Eye',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=5),
    ],
    spell_icon_id=161,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your ranged weapons by $s1 yards.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 522753, 'EffectSpellClassMaskA_2': 2290094208, 'EffectSpellClassMaskA_3': 536871937, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


hawk_eye_19500 = spell(
    id=19500,
    name='Hawk Eye',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=5),
    ],
    spell_icon_id=161,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your ranged weapons by $s1 yards.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 522753, 'EffectSpellClassMaskA_2': 2290094208, 'EffectSpellClassMaskA_3': 536871937, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


trueshot_aura_19506 = spell(
    id=19506,
    name='Trueshot Aura',
    school=School.ARCANE,
    attributes=151060480,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=65, base_points=9, implicit_target_a=1, apply_aura=167, radius_yards=100.0),
        Effect(type=65, base_points=9, implicit_target_a=1, apply_aura=166, radius_yards=45.0),
    ],
    spell_icon_id=128,
    notes='pulled from existing data; hunter-rework S2a A3 (MARKSMANSHIP 5.11, MM-B3): description only, data stock +10%.',
    raw_overrides={'AttributesEx4': 2097152, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases attack power by $s1%.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the attack power of party and raid members within $a1 yards by $s1%. Does not stack with other similar effects.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 2097152, 'SpellClassSet': 9, 'SpellLevel': 40, 'SpellVisualID_1': 5839, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


improved_aspect_of_the_monkey_19549 = spell(
    id=19549,
    name='Improved Aspect of the Monkey',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=3),
    ],
    spell_icon_id=1549,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the Dodge bonus of your Aspect of the Monkey and Aspect of the Dragonhawk by $s1%.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 524288, 'EffectSpellClassMaskA_3': 8192, 'EffectSpellClassMaskB_3': 4096, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_aspect_of_the_monkey_19550 = spell(
    id=19550,
    name='Improved Aspect of the Monkey',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=3),
    ],
    spell_icon_id=1549,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the Dodge bonus of your Aspect of the Monkey and Aspect of the Dragonhawk by $s1%.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 524288, 'EffectSpellClassMaskA_3': 8192, 'EffectSpellClassMaskB_3': 4096, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_aspect_of_the_monkey_19551 = spell(
    id=19551,
    name='Improved Aspect of the Monkey',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=3),
    ],
    spell_icon_id=1549,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the Dodge bonus of your Aspect of the Monkey and Aspect of the Dragonhawk by $s1%.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 524288, 'EffectSpellClassMaskA_3': 8192, 'EffectSpellClassMaskB_3': 4096, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_aspect_of_the_hawk_19552 = spell(
    id=19552,
    name='Improved Aspect of the Hawk',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CHANCE_OF_SUCCESS),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=112,
    notes='pulled from existing data; hunter-rework S1a A3: chance 5/10/15, AP bonus 2/4/6, new eff2 MOD_CRIT_PCT; mask now Hawk only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the chance for your Aspect of the Hawk to increase your attack power by $s1% and its attack power bonus by $s2%, and increases your critical strike chance by $s3%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048576, 'EffectSpellClassMaskB_2': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_aspect_of_the_hawk_19553 = spell(
    id=19553,
    name='Improved Aspect of the Hawk',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CHANCE_OF_SUCCESS),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=112,
    notes='pulled from existing data; hunter-rework S1a A3: chance 5/10/15, AP bonus 2/4/6, new eff2 MOD_CRIT_PCT; mask now Hawk only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the chance for your Aspect of the Hawk to increase your attack power by $s1% and its attack power bonus by $s2%, and increases your critical strike chance by $s3%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048576, 'EffectSpellClassMaskB_2': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_aspect_of_the_hawk_19554 = spell(
    id=19554,
    name='Improved Aspect of the Hawk',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CHANCE_OF_SUCCESS),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=112,
    notes='pulled from existing data; hunter-rework S1a A3: chance 5/10/15, AP bonus 2/4/6, new eff2 MOD_CRIT_PCT; mask now Hawk only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the chance for your Aspect of the Hawk to increase your attack power by $s1% and its attack power bonus by $s2%, and increases your critical strike chance by $s3%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048576, 'EffectSpellClassMaskB_2': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_aspect_of_the_hawk_19555 = spell(
    id=19555,
    name='Improved Aspect of the Hawk',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=112,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While Aspect of the Hawk or Dragonhawk is active, all normal ranged attacks have a $s1% chance of increasing ranged attack speed by $s2% for $6150d.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048576, 'EffectSpellClassMaskA_3': 4096, 'EffectSpellClassMaskB_2': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_aspect_of_the_hawk_19556 = spell(
    id=19556,
    name='Improved Aspect of the Hawk',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=112,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While Aspect of the Hawk or Dragonhawk is active, all normal ranged attacks have a $s1% chance of increasing ranged attack speed by $s2% for $6150d.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048576, 'EffectSpellClassMaskA_3': 4096, 'EffectSpellClassMaskB_2': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


pathfinding_19559 = spell(
    id=19559,
    name='Pathfinding',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CHANCE_OF_SUCCESS),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << CombatRating.VERSATILITY),
    ],
    spell_icon_id=1181,
    notes='pulled from existing data; hunter-rework S1a A3: Monkey chance + Versatility (BM 5); eff2 (aura 211) removed',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the chance for your Aspect of the Monkey to grant Versatility by $s1%, and increases your Versatility by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Increases the speed bonus of your Aspect of the Cheetah, Aspect of the Pack and mounts by $201813s1%. Does not stack with other effects that increase mounted speed.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


pathfinding_19560 = spell(
    id=19560,
    name='Pathfinding',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CHANCE_OF_SUCCESS),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << CombatRating.VERSATILITY),
    ],
    spell_icon_id=1181,
    notes='pulled from existing data; hunter-rework S1a A3: Monkey chance + Versatility (BM 5); eff2 (aura 211) removed',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the chance for your Aspect of the Monkey to grant Versatility by $s1%, and increases your Versatility by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Increases the speed bonus of your Aspect of the Cheetah, Aspect of the Pack and mounts by $201813s1%. Does not stack with other effects that increase mounted speed.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_mend_pet_19572 = spell(
    id=19572,
    name='Improved Mend Pet',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=4086),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=267,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Mend Pet spell by $s2% and gives the Mend Pet spell a $s1% chance of cleansing $24406s1 Curse, Disease, Magic or Poison effect from the pet each tick.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8388608, 'EffectSpellClassMaskB_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_mend_pet_19573 = spell(
    id=19573,
    name='Improved Mend Pet',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=4087),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=267,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Mend Pet spell by $s2% and gives the Mend Pet spell a $s1% chance of cleansing $24406s1 Curse, Disease, Magic or Poison effect from the pet each tick.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8388608, 'EffectSpellClassMaskB_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_revive_pet_19575 = spell(
    id=19575,
    name="Phoenix's Plume",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
    ],
    spell_icon_id=2787,
    notes="pulled from existing data; hunter-rework S1a A3: Improved Revive Pet -> Phoenix's Plume (eff0 ADD_PCT_MODIFIER DAMAGE + eff1 ADD_PCT_MODIFIER DOT (misc 22, S1b S1a-2) on (0,0,0x400000))",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your Command I and Command II by $s1%.\n\n|cFF9D9D9DCapstone Bonus: If your pet dies in combat, it returns to life with " + _PLUME_REVIVE + "% of its health. This effect cannot occur more than once every $201810d.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_3': 4194304, 'EffectSpellClassMaskB_3': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


endurance_training_19583 = spell(
    id=19583,
    name='Endurance Training',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=133),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
    ],
    spell_icon_id=24,
    notes='pulled from existing data; hunter-rework S1a A3: pet health +5/10/15, own health +2/4/6, new eff2 pet damage on TPP01',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your total health by $s2%, and increases your pet's total health by $s1% and the damage it deals by $s3%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EffectSpellClassMaskC_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


endurance_training_19584 = spell(
    id=19584,
    name='Endurance Training',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=133),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
    ],
    spell_icon_id=24,
    notes='pulled from existing data; hunter-rework S1a A3: pet health +5/10/15, own health +2/4/6, new eff2 pet damage on TPP01',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your total health by $s2%, and increases your pet's total health by $s1% and the damage it deals by $s3%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EffectSpellClassMaskC_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


endurance_training_19585 = spell(
    id=19585,
    name='Endurance Training',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=133),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
    ],
    spell_icon_id=24,
    notes='pulled from existing data; hunter-rework S1a A3: pet health +5/10/15, own health +2/4/6, new eff2 pet damage on TPP01',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your total health by $s2%, and increases your pet's total health by $s1% and the damage it deals by $s3%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EffectSpellClassMaskC_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


endurance_training_19586 = spell(
    id=19586,
    name='Endurance Training',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=107, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=133),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the health of your pet by $s1% and your total health by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


endurance_training_19587 = spell(
    id=19587,
    name='Endurance Training',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=133),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the health of your pet by $s1% and your total health by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


bestial_discipline_19590 = spell(
    id=19590,
    name='Bestial Discipline',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=263,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the Focus regeneration of your pets by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 536870912, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


bestial_discipline_19592 = spell(
    id=19592,
    name='Bestial Discipline',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=263,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the Focus regeneration of your pets by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 536870912, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


boar_s_speed_19596 = spell(
    id=19596,
    name="Boar's Speed",
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED, misc_value=8),
    ],
    spell_icon_id=1578,
    notes="pulled from existing data. H0-P1 (PET.md 7.1): bp 29 -> 9 (stored = live - 1: rank 1 is now 10%); ranks 2-3 are 201750/201751 (bp 19/29) in hunter_pet.py, cloned from this row.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's movement speed by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 268435456, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


ferocity_19598 = spell(
    id=19598,
    name='Ferocity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=1561,
    notes='pulled from existing data; hunter-rework S1a A3: text only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your pet by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 1073741824, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


ferocity_19599 = spell(
    id=19599,
    name='Ferocity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=1561,
    notes='pulled from existing data; hunter-rework S1a A3: text only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your pet by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 1073741824, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


ferocity_19600 = spell(
    id=19600,
    name='Ferocity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=1561,
    notes='pulled from existing data; hunter-rework S1a A3: text only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your pet by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 1073741824, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


ferocity_19601 = spell(
    id=19601,
    name='Ferocity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=1561,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your pet by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 1073741824, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


ferocity_19602 = spell(
    id=19602,
    name='Ferocity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=1561,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your pet by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 1073741824, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


thick_hide_19609 = spell(
    id=19609,
    name='Thick Hide',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=107, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=142, misc_value=1),
    ],
    spell_icon_id=1558,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the armor rating of your pets by $s1% and your armor contribution from items by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


thick_hide_19610 = spell(
    id=19610,
    name='Thick Hide',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=107, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=142, misc_value=1),
    ],
    spell_icon_id=1558,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the armor rating of your pets by $s1% and your armor contribution from items by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


thick_hide_19612 = spell(
    id=19612,
    name='Thick Hide',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=142, misc_value=1),
    ],
    spell_icon_id=1558,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the armor rating of your pets by $s1% and your armor contribution from items by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


unleashed_fury_19616 = spell(
    id=19616,
    name='Unleashed Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
    ],
    spell_icon_id=50,
    notes='pulled from existing data; hunter-rework S1a A3: 8/16/25%',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage done by your pet by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


unleashed_fury_19617 = spell(
    id=19617,
    name='Unleashed Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
    ],
    spell_icon_id=50,
    notes='pulled from existing data; hunter-rework S1a A3: 8/16/25%',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage done by your pet by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


unleashed_fury_19618 = spell(
    id=19618,
    name='Unleashed Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
    ],
    spell_icon_id=50,
    notes='pulled from existing data; hunter-rework S1a A3: 8/16/25%',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage done by your pet by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


unleashed_fury_19619 = spell(
    id=19619,
    name='Unleashed Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=50,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your pets by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


unleashed_fury_19620 = spell(
    id=19620,
    name='Unleashed Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=50,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your pets by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


frenzy_19621 = spell(
    id=19621,
    name='Frenzy',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=18),
    ],
    spell_icon_id=1562,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your pet a $s1% chance to gain a $19615s1% attack speed increase for $19615d after dealing a critical strike.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 2147483648, 'EffectSpellClassMaskA_1': 2147483648, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


frenzy_19622 = spell(
    id=19622,
    name='Frenzy',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=107, misc_value=18),
    ],
    spell_icon_id=1562,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your pet a $s1% chance to gain a $19615s1% attack speed increase for $19615d after dealing a critical strike.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 2147483648, 'EffectSpellClassMaskA_1': 2147483648, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


frenzy_19623 = spell(
    id=19623,
    name='Frenzy',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=107, misc_value=18),
    ],
    spell_icon_id=1562,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your pet a $s1% chance to gain a $19615s1% attack speed increase for $19615d after dealing a critical strike.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 2147483648, 'EffectSpellClassMaskA_1': 2147483648, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


frenzy_19624 = spell(
    id=19624,
    name='Frenzy',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=79, implicit_target_a=1, apply_aura=107, misc_value=18),
    ],
    spell_icon_id=1562,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your pet a $s1% chance to gain a $19615s1% attack speed increase for $19615d after dealing a critical strike.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 2147483648, 'EffectSpellClassMaskA_1': 2147483648, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


frenzy_19625 = spell(
    id=19625,
    name='Frenzy',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=18),
    ],
    spell_icon_id=1562,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your pet a $s1% chance to gain a $19615s1% attack speed increase for $19615d after dealing a critical strike.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 2147483648, 'EffectSpellClassMaskA_1': 2147483648, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


surefooted_24283 = spell(
    id=24283,
    name='Surefooted',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=232, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=232, misc_value=7),
    ],
    spell_icon_id=246,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the duration of movement impairing effects by $s1%.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_revive_pet_24443 = spell(
    id=24443,
    name="Phoenix's Plume",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
    ],
    spell_icon_id=2787,
    notes="pulled from existing data; hunter-rework S1a A3: Improved Revive Pet -> Phoenix's Plume (eff0 ADD_PCT_MODIFIER DAMAGE + eff1 ADD_PCT_MODIFIER DOT (misc 22, S1b S1a-2) on (0,0,0x400000))",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your Command I and Command II by $s1%.\n\n|cFF9D9D9DCapstone Bonus: If your pet dies in combat, it returns to life with " + _PLUME_REVIVE + "% of its health. This effect cannot occur more than once every $201810d.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_3': 4194304, 'EffectSpellClassMaskB_3': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


barrage_24691 = spell(
    id=24691,
    name='Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=0),
    ],
    spell_icon_id=85,
    notes="hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 +5/10/15% on BARRAGE_DAMAGE (Aimed Shot leaves it), stock Volley DOT eff1 dropped; r3 eff1 DUMMY + ProcTypeMask 0x100 / ProcChance 25 (half Volley capstone, S2b's spell_proc row and script).",
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc('Increases the damage of your Multi-Shot and Volley by $s1%.', f"Your Multi-Shot has a $24691h% chance to call down a Volley at the target's location that lasts half as long and deals half the damage. This effect cannot occur more than once every {int(BARRAGE_ICD_MS['value']) // 1000} sec.", last=True),
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 25,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        'ProcTypeMask': 256,
        **_mm_masks({1: m.BARRAGE_DAMAGE}),
    },
)


animal_handler_34453 = spell(
    id=34453,
    name='Animal Handler',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2999, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DURATION),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=SpellModOp.ALL_EFFECTS),
    ],
    spell_icon_id=2234,
    notes='pulled from existing data; hunter-rework S1a A3: eff1 pet AP 6/12%',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's attack power by $s2% and the duration of your Master's Call by ${$m1/1000} sec.", 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_3': 524288, 'EffectSpellClassMaskB_2': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


animal_handler_34454 = spell(
    id=34454,
    name='Animal Handler',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5999, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DURATION),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=SpellModOp.ALL_EFFECTS),
    ],
    spell_icon_id=2234,
    notes='pulled from existing data; hunter-rework S1a A3: eff1 pet AP 6/12%',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's attack power by $s2% and the duration of your Master's Call by ${$m1/1000} sec.", 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_3': 524288, 'EffectSpellClassMaskB_2': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


ferocious_inspiration_34455 = spell(
    id=34455,
    name='Ferocious Inspiration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=18),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2232,
    notes='pulled from existing data; hunter-rework S1a A3: text only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by all party and raid members by $75593s1%, and increases the damage of your Arcane Shot and Steady Shot by $s3%. Does not stack with other effects that increase party damage by a percentage.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 32, 'EffectSpellClassMaskB_2': 64, 'EffectSpellClassMaskC_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9, 'EffectSpellClassMaskC_3': 536870912},
)


ferocious_inspiration_34459 = spell(
    id=34459,
    name='Ferocious Inspiration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=18),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2232,
    notes='pulled from existing data; hunter-rework S1a A3: text only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by all party and raid members by $75446s1%, and increases the damage of your Arcane Shot and Steady Shot by $s3%. Does not stack with other effects that increase party damage by a percentage.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 32, 'EffectSpellClassMaskB_2': 64, 'EffectSpellClassMaskC_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9, 'EffectSpellClassMaskC_3': 536870912},
)


ferocious_inspiration_34460 = spell(
    id=34460,
    name='Ferocious Inspiration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=18),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2232,
    notes='pulled from existing data; hunter-rework S1a A3: text only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by all party and raid members by $75447s1%, and increases the damage of your Arcane Shot and Steady Shot by $s3%. Does not stack with other effects that increase party damage by a percentage.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 32, 'EffectSpellClassMaskB_2': 64, 'EffectSpellClassMaskC_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9, 'EffectSpellClassMaskC_3': 536870912},
)


catlike_reflexes_34462 = spell(
    id=34462,
    name='Catlike Reflexes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
    ],
    spell_icon_id=2224,
    notes='pulled from existing data; hunter-rework S1a A3: eff0 ADD_PCT_MODIFIER DAMAGE on Kill Command, pet dodge 4/8/12, eff2 (KC cooldown) removed',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's chance to dodge by $s2%, and increases the damage of your Kill Command by $s1%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EffectSpellClassMaskB_2': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


catlike_reflexes_34464 = spell(
    id=34464,
    name='Catlike Reflexes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
    ],
    spell_icon_id=2224,
    notes='pulled from existing data; hunter-rework S1a A3: eff0 ADD_PCT_MODIFIER DAMAGE on Kill Command, pet dodge 4/8/12, eff2 (KC cooldown) removed',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's chance to dodge by $s2%, and increases the damage of your Kill Command by $s1%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EffectSpellClassMaskB_2': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


catlike_reflexes_34465 = spell(
    id=34465,
    name='Catlike Reflexes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
    ],
    spell_icon_id=2224,
    notes='pulled from existing data; hunter-rework S1a A3: eff0 ADD_PCT_MODIFIER DAMAGE on Kill Command, pet dodge 4/8/12, eff2 (KC cooldown) removed',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's chance to dodge by $s2%, and increases the damage of your Kill Command by $s1%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EffectSpellClassMaskB_2': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


serpent_s_swiftness_34466 = spell(
    id=34466,
    name="Serpent's Swiftness",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=2225,
    notes='pulled from existing data; hunter-rework S1a A3: eff0 DUMMY Nature share, eff1 ADD_PCT_MODIFIER DOT on Serpent Sting; ProcTypeMask 0x100, ProcChance 100 (data only; scripted in S1b)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Steady Shot deals an additional $s1% of its damage as Nature damage, and the damage of your Serpent Sting is increased by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Each Steady Shot you cast reduces the remaining cooldown of your Kill Command by ${$34468m3/1000} sec.|r', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 256, 'RangeIndex': 1, 'SpellClassSet': 9},
)


serpent_s_swiftness_34467 = spell(
    id=34467,
    name="Serpent's Swiftness",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=2225,
    notes='pulled from existing data; hunter-rework S1a A3: eff0 DUMMY Nature share, eff1 ADD_PCT_MODIFIER DOT on Serpent Sting; ProcTypeMask 0x100, ProcChance 100 (data only; scripted in S1b)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Steady Shot deals an additional $s1% of its damage as Nature damage, and the damage of your Serpent Sting is increased by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Each Steady Shot you cast reduces the remaining cooldown of your Kill Command by ${$34468m3/1000} sec.|r', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 256, 'RangeIndex': 1, 'SpellClassSet': 9},
)


serpent_s_swiftness_34468 = spell(
    id=34468,
    name="Serpent's Swiftness",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=999, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2225,
    notes='pulled from existing data; hunter-rework S1a A3: eff0 DUMMY Nature share, eff1 ADD_PCT_MODIFIER DOT on Serpent Sting; ProcTypeMask 0x100, ProcChance 100 (data only; scripted in S1b)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Steady Shot deals an additional $s1% of its damage as Nature damage, and the damage of your Serpent Sting is increased by $s2%.\n\nCapstone Bonus: Each Steady Shot you cast reduces the remaining cooldown of your Kill Command by ${$34468m3/1000} sec.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 256, 'RangeIndex': 1, 'SpellClassSet': 9},
)


serpent_s_swiftness_34469 = spell(
    id=34469,
    name="Serpent's Swiftness",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=140),
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=2225,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases ranged combat attack speed by $s1% and your pet's melee attack speed by $s2%.", 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


serpent_s_swiftness_34470 = spell(
    id=34470,
    name="Serpent's Swiftness",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=140),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=2225,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases ranged combat attack speed by $s1% and your pet's melee attack speed by $s2%.", 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


combat_experience_34475 = spell(
    id=34475,
    name='Combat Experience',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=2223,
    notes="hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 Agility +1/2% (aura 137 misc 1), eff1 crit +1/2% (stock Intellect half dropped; 34476's swapped effect order normalized); stale masks cleared.",
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc('Increases your total Agility by $s1% and your critical strike chance by $s2%.', f'Increases your Intellect by {_mm_c(COMBAT_EXPERIENCE_CAPSTONE_PCT)}% of your Agility.', last=False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
    },
)


combat_experience_34476 = spell(
    id=34476,
    name='Combat Experience',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=2223,
    notes="hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 Agility +1/2% (aura 137 misc 1), eff1 crit +1/2% (stock Intellect half dropped; 34476's swapped effect order normalized); stale masks cleared.",
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc('Increases your total Agility by $s1% and your critical strike chance by $s2%.', f'Increases your Intellect by {_mm_c(COMBAT_EXPERIENCE_CAPSTONE_PCT)}% of your Agility.', last=False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
    },
)


careful_aim_34482 = spell(
    id=34482,
    name='Careful Aim',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=212, misc_value=3),
    ],
    spell_icon_id=2222,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; aura 212 (MOD_RANGED_ATTACK_POWER_OF_STAT_PERCENT) misc 3 Intellect 20/40/60%; stale A/B masks and the phantom eff1 (BasePoints/DieSides/ImplicitTargetA _2) deleted (M15).',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your ranged attack power by an amount equal to $s1% of your total Intellect.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
    },
)


careful_aim_34483 = spell(
    id=34483,
    name='Careful Aim',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=212, misc_value=3),
    ],
    spell_icon_id=2222,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; aura 212 (MOD_RANGED_ATTACK_POWER_OF_STAT_PERCENT) misc 3 Intellect 20/40/60%; stale A/B masks and the phantom eff1 (BasePoints/DieSides/ImplicitTargetA _2) deleted (M15).',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your ranged attack power by an amount equal to $s1% of your total Intellect.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
    },
)


careful_aim_34484 = spell(
    id=34484,
    name='Careful Aim',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=212, misc_value=3),
    ],
    spell_icon_id=2222,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; aura 212 (MOD_RANGED_ATTACK_POWER_OF_STAT_PERCENT) misc 3 Intellect 20/40/60%; stale A/B masks and the phantom eff1 (BasePoints/DieSides/ImplicitTargetA _2) deleted (M15).',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your ranged attack power by an amount equal to $s1% of your total Intellect.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
    },
)


master_marksman_34485 = spell(
    id=34485,
    name='Master Marksman',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=fire_mm_buff_201940.id),
    ],
    spell_icon_id=2230,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 PROC_TRIGGER_SPELL -> Fire! 201940 (spell_proc row -34485, A1), ProcChance 4/8/12, ProcTypeMask 0x100; stock crit and cost effects dropped, stale masks cleared.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your Steady Shots have a $h% chance to grant Fire!, making your next Aimed Shot within $201940d instant and free. An early Aimed Shot consumes your marks at whatever stacks they have.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 4,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        'ProcTypeMask': 256,
    },
)


master_marksman_34486 = spell(
    id=34486,
    name='Master Marksman',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=fire_mm_buff_201940.id),
    ],
    spell_icon_id=2230,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 PROC_TRIGGER_SPELL -> Fire! 201940 (spell_proc row -34485, A1), ProcChance 4/8/12, ProcTypeMask 0x100; stock crit and cost effects dropped, stale masks cleared.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your Steady Shots have a $h% chance to grant Fire!, making your next Aimed Shot within $201940d instant and free. An early Aimed Shot consumes your marks at whatever stacks they have.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 8,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        'ProcTypeMask': 256,
    },
)


master_marksman_34487 = spell(
    id=34487,
    name='Master Marksman',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=fire_mm_buff_201940.id),
    ],
    spell_icon_id=2230,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 PROC_TRIGGER_SPELL -> Fire! 201940 (spell_proc row -34485, A1), ProcChance 4/8/12, ProcTypeMask 0x100; stock crit and cost effects dropped, stale masks cleared.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your Steady Shots have a $h% chance to grant Fire!, making your next Aimed Shot within $201940d instant and free. An early Aimed Shot consumes your marks at whatever stacks they have.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 12,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        'ProcTypeMask': 256,
    },
)


master_marksman_34488 = spell(
    id=34488,
    name='Master Marksman',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=52),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=2230,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance by $s1%, and reduces the Mana cost of your Steady Shot, Aimed Shot, and Chimera Shot by $s2%.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 131072, 'EffectSpellClassMaskB_3': 536870913, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


master_marksman_34489 = spell(
    id=34489,
    name='Master Marksman',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=52),
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=2230,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance by $s1%, and reduces the Mana cost of your Steady Shot, Aimed Shot, and Chimera Shot by $s2%.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 131072, 'EffectSpellClassMaskB_3': 536870913, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


resourcefulness_34491 = spell(
    id=34491,
    name='Resourcefulness',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2240,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of all traps, melee abilities and Black Arrow by $s1% and reduces the cooldown of all traps and Black Arrow by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 222, 'EffectSpellClassMaskA_2': 540672, 'EffectSpellClassMaskB_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


resourcefulness_34492 = spell(
    id=34492,
    name='Resourcefulness',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-41, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-4001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2240,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of all traps, melee abilities and Black Arrow by $s1% and reduces the cooldown of all traps and Black Arrow by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 222, 'EffectSpellClassMaskA_2': 540672, 'EffectSpellClassMaskB_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


resourcefulness_34493 = spell(
    id=34493,
    name='Resourcefulness',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-61, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-6001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2240,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of all traps, melee abilities and Black Arrow by $s1% and reduces the cooldown of all traps and Black Arrow by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 222, 'EffectSpellClassMaskA_2': 540672, 'EffectSpellClassMaskB_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


survival_instincts_34494 = spell(
    id=34494,
    name='Survival Instincts',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2239,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1% and increases the critical strike chance of your Arcane Shot, Steady Shot, and Explosive Shot by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 222, 'EffectSpellClassMaskB_1': 2048, 'EffectSpellClassMaskB_2': 2147483648, 'EffectSpellClassMaskB_3': 536871488, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


survival_instincts_34496 = spell(
    id=34496,
    name='Survival Instincts',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2239,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1% and increases the critical strike chance of your Arcane Shot, Steady Shot, and Explosive Shot by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 222, 'EffectSpellClassMaskB_1': 2048, 'EffectSpellClassMaskB_2': 2147483648, 'EffectSpellClassMaskB_3': 536871488, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


thrill_of_the_hunt_34497 = spell(
    id=34497,
    name='Thrill of the Hunt',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2236,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a $s1% chance to regain 40% of the mana cost of any shot when it critically hits.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 222, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 256, 'RangeIndex': 1, 'SpellClassSet': 9},
)


thrill_of_the_hunt_34498 = spell(
    id=34498,
    name='Thrill of the Hunt',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2236,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a $s1% chance to regain 40% of the mana cost of any shot when it critically hits.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 222, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 256, 'RangeIndex': 1, 'SpellClassMask_2': 2155872256, 'SpellClassSet': 9},
)


thrill_of_the_hunt_34499 = spell(
    id=34499,
    name='Thrill of the Hunt',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2236,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a $s1% chance to regain 40% of the mana cost of any shot when it critically hits.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 222, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 262400, 'RangeIndex': 1, 'SpellClassSet': 9},
)


expose_weakness_34500 = spell(
    id=34500,
    name='Expose Weakness',
    school=School.ARCANE,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=34501),
    ],
    spell_icon_id=2112,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your ranged criticals have a $h% chance to grant you Expose Weakness. Expose Weakness increases your attack power by $34501s1% of your Agility for $34501d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 33, 'ProcTypeMask': 262464, 'RangeIndex': 1, 'SpellClassSet': 9},
)


expose_weakness_34502 = spell(
    id=34502,
    name='Expose Weakness',
    school=School.ARCANE,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=34501),
    ],
    spell_icon_id=2112,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your ranged criticals have a $h% chance to grant you Expose Weakness. Expose Weakness increases your attack power by $34501s1% of your Agility for $34501d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 66, 'ProcTypeMask': 262464, 'RangeIndex': 1, 'SpellClassSet': 9},
)


expose_weakness_34503 = spell(
    id=34503,
    name='Expose Weakness',
    school=School.ARCANE,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=34501),
    ],
    spell_icon_id=2112,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your ranged criticals have a $h% chance to grant you Expose Weakness. Expose Weakness increases your attack power by $34501s1% of your Agility for $34501d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcTypeMask': 262464, 'RangeIndex': 1, 'SpellClassSet': 9},
)


master_tactician_34506 = spell(
    id=34506,
    name='Master Tactician',
    school=School.ARCANE,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=master_tactician_34833.id),
    ],
    spell_icon_id=2233,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your successful ranged attacks have a $h% chance to increase your critical strike chance with all attacks by $34833s1% for $34833d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 522819, 'EffectSpellClassMaskA_2': 128, 'EffectSpellClassMaskB_1': 522819, 'EffectSpellClassMaskB_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 10, 'ProcTypeMask': 320, 'RangeIndex': 1, 'SpellClassSet': 9, 'EffectSpellClassMaskA_3': 536870912},
)


master_tactician_34507 = spell(
    id=34507,
    name='Master Tactician',
    school=School.ARCANE,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=34834),
    ],
    spell_icon_id=2233,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your successful ranged attacks have a $h% chance to increase your critical strike chance with all attacks by $34834s1% for $34834d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 522819, 'EffectSpellClassMaskA_2': 128, 'EffectSpellClassMaskB_1': 522819, 'EffectSpellClassMaskB_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 10, 'ProcTypeMask': 320, 'RangeIndex': 1, 'SpellClassSet': 9, 'EffectSpellClassMaskA_3': 536870912},
)


master_tactician_34508 = spell(
    id=34508,
    name='Master Tactician',
    school=School.ARCANE,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=34835),
    ],
    spell_icon_id=2233,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your successful ranged attacks have a $h% chance to increase your critical strike chance with all attacks by $34835s1% for $34835d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 522819, 'EffectSpellClassMaskA_2': 128, 'EffectSpellClassMaskB_1': 522819, 'EffectSpellClassMaskB_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 10, 'ProcTypeMask': 320, 'RangeIndex': 1, 'SpellClassSet': 9, 'EffectSpellClassMaskA_3': 536870912},
)


the_beast_within_34692 = spell(
    id=34692,
    name='The Beast Within',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=2229,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% and while your pet is under the effects of Bestial Wrath, you also go into a rage causing $34471s2% additional damage and reducing mana costs of all spells by $34471s1% for $34471d.  While enraged, you do not feel pity or remorse or fear and you cannot be stopped unless killed.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9, 'SpellLevel': 50, 'TargetCreatureType': 1},
)


master_tactician_34838 = spell(
    id=34838,
    name='Master Tactician',
    school=School.ARCANE,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=34836),
    ],
    spell_icon_id=2233,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your successful ranged attacks have a $h% chance to increase your critical strike chance with all attacks by $34836s1% for $34836d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 522819, 'EffectSpellClassMaskA_2': 128, 'EffectSpellClassMaskB_1': 522819, 'EffectSpellClassMaskB_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 10, 'ProcTypeMask': 320, 'RangeIndex': 1, 'SpellClassSet': 9, 'EffectSpellClassMaskA_3': 536870912},
)


master_tactician_34839 = spell(
    id=34839,
    name='Master Tactician',
    school=School.ARCANE,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=34837),
    ],
    spell_icon_id=2233,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your successful ranged attacks have a $h% chance to increase your critical strike chance with all attacks by $34837s1% for $34837d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 522819, 'EffectSpellClassMaskA_2': 128, 'EffectSpellClassMaskB_1': 522819, 'EffectSpellClassMaskB_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 10, 'ProcTypeMask': 320, 'RangeIndex': 1, 'SpellClassSet': 9, 'EffectSpellClassMaskA_3': 536870912},
)


rapid_killing_34948 = spell(
    id=34948,
    name='Rapid Killing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=0),
        Effect(type=EffectType.APPLY_AURA, base_points=-15001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=2285,
    notes="hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 PROC_TRIGGER_SPELL 35098/35099 -> DUMMY +4/8% (execute clause, S2b's UnitScript), trigger 0, ProcTypeMask 0; eff1 Rapid Fire cooldown -15/-30 s.",
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc('Increases the damage of your shots against targets below ' + _mm_c(RAPID_KILLING_HEALTH_PCT) + '% health by $s1% and reduces the cooldown of your Rapid Fire by ${$m2/-1000} sec.', 'Killing an enemy that yields experience causes your next $35098n Aimed Shots, Arcane Shots, Kill Shots or Chimera Shots to deal $35098s1% more damage.', last=False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 100,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        'ProcTypeMask': 0,
        **_mm_masks({2: (m.RAPID_FIRE, 0, 0)}),
    },
)


rapid_killing_34949 = spell(
    id=34949,
    name='Rapid Killing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=0),
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=2285,
    notes="hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 PROC_TRIGGER_SPELL 35098/35099 -> DUMMY +4/8% (execute clause, S2b's UnitScript), trigger 0, ProcTypeMask 0; eff1 Rapid Fire cooldown -15/-30 s.",
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc('Increases the damage of your shots against targets below ' + _mm_c(RAPID_KILLING_HEALTH_PCT) + '% health by $s1% and reduces the cooldown of your Rapid Fire by ${$m2/-1000} sec.', 'Killing an enemy that yields experience causes your next $35098n Aimed Shots, Arcane Shots, Kill Shots or Chimera Shots to deal $35098s1% more damage.', last=False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 100,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        'ProcTypeMask': 0,
        **_mm_masks({2: (m.RAPID_FIRE, 0, 0)}),
    },
)


go_for_the_throat_34950 = spell(
    id=34950,
    name='Go for the Throat',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=34952),
    ],
    spell_icon_id=2318,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your ranged critical hits cause your pet to generate $34952s1 Focus.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2048, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 262464, 'RangeIndex': 1, 'SpellClassSet': 9},
)


go_for_the_throat_34954 = spell(
    id=34954,
    name='Go for the Throat',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=34953),
    ],
    spell_icon_id=2318,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your ranged critical hits cause your pet to generate $34953s1 Focus.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2048, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 262464, 'RangeIndex': 1, 'SpellClassSet': 9},
)


focused_fire_35029 = spell(
    id=35029,
    name='Focused Fire',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=1),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=2221,
    notes='pulled from existing data; hunter-rework S1a A3: eff1 ADD_PCT_MODIFIER DAMAGE on Kill Command (0,0x800,0), new eff2 MOD_CRIT_PCT; eff0 DUMMY stays (B7)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of you and your pet by $s3%, and increases the damage of your Kill Command by $s2%.", 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


focused_fire_35030 = spell(
    id=35030,
    name='Focused Fire',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=1, implicit_target_a=1),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=2221,
    notes='pulled from existing data; hunter-rework S1a A3: eff1 ADD_PCT_MODIFIER DAMAGE on Kill Command (0,0x800,0), new eff2 MOD_CRIT_PCT; eff0 DUMMY stays (B7)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of you and your pet by $s3%, and increases the damage of your Kill Command by $s2%.", 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


concussive_barrage_35100 = spell(
    id=35100,
    name='Concussive Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=35101),
    ],
    spell_icon_id=1485,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your successful Chimera Shot and Multi-Shot attacks have a $h% chance to Daze the target for $35101d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 131392, 'RangeIndex': 1, 'SpellClassSet': 9},
)


concussive_barrage_35102 = spell(
    id=35102,
    name='Concussive Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=35101),
    ],
    spell_icon_id=1485,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your successful Chimera Shot and Multi-Shot attacks have a $h% chance to Daze the target for $35101d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65856, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_barrage_35104 = spell(
    id=35104,
    name='Improved Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=108, misc_value=9),
    ],
    spell_icon_id=85,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Multi-Shot and Aimed Shot abilities by $s1% and reduces the pushback suffered from damaging attacks while channeling Volley by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 135168, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_barrage_35110 = spell(
    id=35110,
    name='Improved Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=108, misc_value=9),
    ],
    spell_icon_id=85,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Multi-Shot and Aimed Shot abilities by $s1% and reduces the pushback suffered from damaging attacks while channeling Volley by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 135168, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_barrage_35111 = spell(
    id=35111,
    name='Improved Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=9),
    ],
    spell_icon_id=85,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Multi-Shot and Aimed Shot abilities by $s1% and reduces the pushback suffered from damaging attacks while channeling Volley by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 135168, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


cornered_52234 = spell(
    id=52234,
    name='Cornered',
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=79, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=197),
    ],
    spell_icon_id=2239,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CasterAuraState': 13, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When at less than 35% health, your pet does $s1% more damage and has a $s2% reduced chance to be critically hit.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_tracking_52783 = spell(
    id=52783,
    name='Improved Tracking',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=3522,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While tracking Beasts, Demons, Dragonkin, Elementals, Giants, Humanoids and Undead, all damage done to those types by the Hunter is increased by $s1%.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_3': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_tracking_52785 = spell(
    id=52785,
    name='Improved Tracking',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=3522,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While tracking Beasts, Demons, Dragonkin, Elementals, Giants, Humanoids and Undead, all damage done to those types by the Hunter is increased by $s1%.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_3': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_tracking_52786 = spell(
    id=52786,
    name='Improved Tracking',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=3522,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While tracking Beasts, Demons, Dragonkin, Elementals, Giants, Humanoids and Undead, all damage done to those types by the Hunter is increased by $s1%.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_3': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_tracking_52787 = spell(
    id=52787,
    name='Improved Tracking',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=3522,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While tracking Beasts, Demons, Dragonkin, Elementals, Giants, Humanoids and Undead, all damage done to those types by the Hunter is increased by $s1%.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_3': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_tracking_52788 = spell(
    id=52788,
    name='Improved Tracking',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=3522,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While tracking Beasts, Demons, Dragonkin, Elementals, Giants, Humanoids and Undead, all damage done to those types by the Hunter is increased by $s1%.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_3': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


wild_quiver_53215 = spell(
    id=53215,
    name='Wild Quiver',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=1, trigger_spell=53254),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=274),
    ],
    spell_icon_id=2935,
    notes="hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; ProcChance 10/20/30, ProcTypeMask 0x140 on every rank (r3's stock 0x11140 normalized, M15), stale eff0 Multi-Shot mask deleted (spell_proc row -53215, A1); eff1 (no-ammo aura 274, d2 b7 = 53254) kept; rank attributes kept per live.",
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your Auto Shot and Steady Shot have a $h% chance to fire an additional shot, dealing $53254s1% weapon damage as Nature damage.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 10,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        'ProcTypeMask': 320,
        **_mm_masks({2: (0, 0, m.WILD_QUIVER)}),
    },
)


wild_quiver_53216 = spell(
    id=53216,
    name='Wild Quiver',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=1, trigger_spell=53254),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=274),
    ],
    spell_icon_id=2935,
    notes="hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; ProcChance 10/20/30, ProcTypeMask 0x140 on every rank (r3's stock 0x11140 normalized, M15), stale eff0 Multi-Shot mask deleted (spell_proc row -53215, A1); eff1 (no-ammo aura 274, d2 b7 = 53254) kept; rank attributes kept per live.",
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your Auto Shot and Steady Shot have a $h% chance to fire an additional shot, dealing $53254s1% weapon damage as Nature damage.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 20,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        'ProcTypeMask': 320,
        **_mm_masks({2: (0, 0, m.WILD_QUIVER)}),
    },
)


wild_quiver_53217 = spell(
    id=53217,
    name='Wild Quiver',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=1, trigger_spell=53254),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=274),
    ],
    spell_icon_id=2935,
    notes="hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; ProcChance 10/20/30, ProcTypeMask 0x140 on every rank (r3's stock 0x11140 normalized, M15), stale eff0 Multi-Shot mask deleted (spell_proc row -53215, A1); eff1 (no-ammo aura 274, d2 b7 = 53254) kept; rank attributes kept per live.",
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your Auto Shot and Steady Shot have a $h% chance to fire an additional shot, dealing $53254s1% weapon damage as Nature damage.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 30,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        'ProcTypeMask': 320,
        **_mm_masks({2: (0, 0, m.WILD_QUIVER)}),
    },
)


improved_steady_shot_53221 = spell(
    id=53221,
    name='Improved Steady Shot',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=1, trigger_spell=53220),
    ],
    spell_icon_id=3409,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Steady Shot hits have a $h% chance to increase the damage done by your next Aimed Shot, Arcane Shot or Chimera Shot by $53220s1%, and reduce the mana cost of your next Aimed Shot, Arcane Shot or Chimera Shot by $53220s2%.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 5, 'ProcTypeMask': 320, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_steady_shot_53222 = spell(
    id=53222,
    name='Improved Steady Shot',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=1, trigger_spell=53220),
    ],
    spell_icon_id=3409,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Steady Shot hits have a $h% chance to increase the damage done by your next Aimed Shot, Arcane Shot or Chimera Shot by $53220s1%, and reduce the mana cost of your next Aimed Shot, Arcane Shot or Chimera Shot by $53220s2%.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 320, 'RangeIndex': 1, 'SpellClassSet': 9},
)


improved_steady_shot_53224 = spell(
    id=53224,
    name='Improved Steady Shot',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=1, trigger_spell=53220),
    ],
    spell_icon_id=3409,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Steady Shot hits have a $h% chance to increase the damage done by your next Aimed Shot, Arcane Shot or Chimera Shot by $53220s1%, and reduce the mana cost of your next Aimed Shot, Arcane Shot or Chimera Shot by $53220s2%.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 15, 'ProcTypeMask': 320, 'RangeIndex': 1, 'SpellClassSet': 9},
)


rapid_recuperation_53228 = spell(
    id=53228,
    name='Rapid Recuperation',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=1, trigger_spell=53230),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3560,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You gain $64180s1% of your mana every $53230t1 sec while under the effect of Rapid Fire, and you gain $56654s1% of your mana every $56654t1 sec for $56654d when you gain Rapid Killing.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 17408, 'RangeIndex': 1, 'SpellClassSet': 9},
)


rapid_recuperation_53232 = spell(
    id=53232,
    name='Rapid Recuperation',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=1, trigger_spell=54227),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3560,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You gain $64181s1% of your mana every $54227t1 sec while under the effect of Rapid Fire, and you gain $58882s1% of your mana every $58882t1 sec for $58882d when you gain Rapid Killing.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 17408, 'RangeIndex': 1, 'SpellClassSet': 9},
)


piercing_shots_53234 = spell(
    id=53234,
    name='Piercing Shots',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=13),
    ],
    spell_icon_id=3247,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 unchanged (STEADY_AIMED mask, spell_proc row -53234 narrowed by A4); stale B_1 on the missing eff1 deleted (M15); tooltip drops Chimera Shot.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your critical Steady Shots and Aimed Shots cause the target to bleed for $s1% of the damage dealt over $63468d.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 100,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        'ProcTypeMask': 256,
        **_mm_masks({1: m.STEADY_AIMED}),
    },
)


piercing_shots_53237 = spell(
    id=53237,
    name='Piercing Shots',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=13),
    ],
    spell_icon_id=3247,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 unchanged (STEADY_AIMED mask, spell_proc row -53234 narrowed by A4); stale B_1 on the missing eff1 deleted (M15); tooltip drops Chimera Shot.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your critical Steady Shots and Aimed Shots cause the target to bleed for $s1% of the damage dealt over $63468d.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 100,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        'ProcTypeMask': 256,
        **_mm_masks({1: m.STEADY_AIMED}),
    },
)


piercing_shots_53238 = spell(
    id=53238,
    name='Piercing Shots',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=13),
    ],
    spell_icon_id=3247,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 unchanged (STEADY_AIMED mask, spell_proc row -53234 narrowed by A4); stale B_1 on the missing eff1 deleted (M15); tooltip drops Chimera Shot.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your critical Steady Shots and Aimed Shots cause the target to bleed for $s1% of the damage dealt over $63468d.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 100,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        'ProcTypeMask': 256,
        **_mm_masks({1: m.STEADY_AIMED}),
    },
)


marked_for_death_53241 = spell(
    id=53241,
    name='Marked for Death',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=3410,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 DUMMY 2/4/6 (Sniper payoff, read by HunterMechanics; eff0 because SpellInfoCorrections.cpp:409 overwrites the eff0 mask at load), eff1 DOT +2/4/6% on the mark DoTs (d2 b28), eff2 +2/4/6% on the mark presses (d2 b27); stock aura 112 and every stale mask (A_2 held d1 b28) deleted; icon 3410; attributes 208 kept (live).',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc("Increases the damage of your marks, Viper's Bite, Viper's Venom and Convergence, and of your Aimed Shot and Chimera Shot against targets with your Sniper's Mark, by $s1%.", "Your Mastery increases the damage of your marks, Viper's Bite, Viper's Venom and Convergence, and of your Aimed Shot and Chimera Shot against targets with your Sniper's Mark.", last=False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({2: (0, 0, m.MARK_DOT), 3: (0, 0, m.MARK_PRESS)}),
    },
)


marked_for_death_53243 = spell(
    id=53243,
    name='Marked for Death',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=3410,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 DUMMY 2/4/6 (Sniper payoff, read by HunterMechanics; eff0 because SpellInfoCorrections.cpp:409 overwrites the eff0 mask at load), eff1 DOT +2/4/6% on the mark DoTs (d2 b28), eff2 +2/4/6% on the mark presses (d2 b27); stock aura 112 and every stale mask (A_2 held d1 b28) deleted; icon 3410; attributes 208 kept (live).',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc("Increases the damage of your marks, Viper's Bite, Viper's Venom and Convergence, and of your Aimed Shot and Chimera Shot against targets with your Sniper's Mark, by $s1%.", "Your Mastery increases the damage of your marks, Viper's Bite, Viper's Venom and Convergence, and of your Aimed Shot and Chimera Shot against targets with your Sniper's Mark.", last=False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({2: (0, 0, m.MARK_DOT), 3: (0, 0, m.MARK_PRESS)}),
    },
)


marked_for_death_53244 = spell(
    id=53244,
    name='Marked for Death',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=3410,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 DUMMY 2/4/6 (Sniper payoff, read by HunterMechanics; eff0 because SpellInfoCorrections.cpp:409 overwrites the eff0 mask at load), eff1 DOT +2/4/6% on the mark DoTs (d2 b28), eff2 +2/4/6% on the mark presses (d2 b27); stock aura 112 and every stale mask (A_2 held d1 b28) deleted; icon 3410; attributes 208 kept (live).',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc("Increases the damage of your marks, Viper's Bite, Viper's Venom and Convergence, and of your Aimed Shot and Chimera Shot against targets with your Sniper's Mark, by $s1%.", "Your Mastery increases the damage of your marks, Viper's Bite, Viper's Venom and Convergence, and of your Aimed Shot and Chimera Shot against targets with your Sniper's Mark.", last=True),
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({2: (0, 0, m.MARK_DOT), 3: (0, 0, m.MARK_PRESS)}),
    },
)


marked_for_death_53245 = spell(
    id=53245,
    name='Marked for Death',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=112, misc_value=7599),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=3524,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your damage done by your shots and the damage done by your pet's special abilities by $s1% on marked targets, and increases the critical strike damage bonus of your Aimed Shot, Arcane Shot, Steady Shot, Kill Shot and Chimera Shot by $s2%.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 399361, 'EffectSpellClassMaskA_2': 276955136, 'EffectSpellClassMaskA_3': 1, 'EffectSpellClassMaskB_1': 133120, 'EffectSpellClassMaskB_2': 8388608, 'EffectSpellClassMaskB_3': 536870913, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


marked_for_death_53246 = spell(
    id=53246,
    name='Marked for Death',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=112, misc_value=7598),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=3524,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your damage done by your shots and the damage done by your pet's special abilities by $s1% on marked targets, and increases the critical strike damage bonus of your Aimed Shot, Arcane Shot, Steady Shot, Kill Shot and Chimera Shot by $s2%.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 399361, 'EffectSpellClassMaskA_2': 276955136, 'EffectSpellClassMaskA_3': 1, 'EffectSpellClassMaskB_1': 133120, 'EffectSpellClassMaskB_2': 8388608, 'EffectSpellClassMaskB_3': 536870913, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


invigoration_53252 = spell(
    id=53252,
    name='Invigoration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=8),
    ],
    spell_icon_id=3487,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your pet scores a critical hit with a special ability, you have a $s1% chance to instantly regenerate $53398s1% mana.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 134217728, 'EffectSpellClassMaskB_2': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


invigoration_53253 = spell(
    id=53253,
    name='Invigoration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=8),
    ],
    spell_icon_id=3487,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your pet scores a critical hit with a special ability, you have a $s1% chance to instantly regenerate $53398s1% mana.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


cobra_strikes_53256 = spell(
    id=53256,
    name='Cobra Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2936,
    notes='pulled from existing data; hunter-rework S1a A11: eff0 DUMMY (no trigger), ProcChance 5/10/15, ProcTypeMask 0x100; inert until S1b',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Steady Shots have a $h% chance to reset the cooldown of your Arcane Shot.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 5, 'ProcTypeMask': 256, 'RangeIndex': 1, 'SpellClassSet': 9},
)


cobra_strikes_53259 = spell(
    id=53259,
    name='Cobra Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2936,
    notes='pulled from existing data; hunter-rework S1a A11: eff0 DUMMY (no trigger), ProcChance 5/10/15, ProcTypeMask 0x100; inert until S1b',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Steady Shots have a $h% chance to reset the cooldown of your Arcane Shot.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 256, 'RangeIndex': 1, 'SpellClassSet': 9},
)


cobra_strikes_53260 = spell(
    id=53260,
    name='Cobra Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2936,
    notes='pulled from existing data; hunter-rework S1a A11: eff0 DUMMY (no trigger), ProcChance 5/10/15, ProcTypeMask 0x100; inert until S1b',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Steady Shots have a $h% chance to reset the cooldown of your Arcane Shot.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 15, 'ProcTypeMask': 256, 'RangeIndex': 1, 'SpellClassSet': 9},
)


longevity_53262 = spell(
    id=53262,
    name='Longevity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=3561,
    notes='pulled from existing data; hunter-rework S1a A3: -10/15/20%, mask (0,0x2000000,0x200000)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Bestial Wrath, Command I and Command II by ${$m1*-1}%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 33554432, 'EffectSpellClassMaskA_3': 2097152, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


longevity_53263 = spell(
    id=53263,
    name='Longevity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=3561,
    notes='pulled from existing data; hunter-rework S1a A3: -10/15/20%, mask (0,0x2000000,0x200000)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Bestial Wrath, Command I and Command II by ${$m1*-1}%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 33554432, 'EffectSpellClassMaskA_3': 2097152, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


longevity_53264 = spell(
    id=53264,
    name='Longevity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=3561,
    notes='pulled from existing data; hunter-rework S1a A3: -10/15/20%, mask (0,0x2000000,0x200000)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Bestial Wrath, Command I and Command II by ${$m1*-1}%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 33554432, 'EffectSpellClassMaskA_3': 2097152, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


aspect_mastery_53265 = spell(
    id=53265,
    name='Aspect Mastery',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=3),
    ],
    spell_icon_id=3523,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Aspect of the Viper - Reduces the damage penalty by $s1%.\r\n\r\nAspect of the Monkey - Reduces the damage done to you while active by $s2%.\r\n\r\nAspect of the Hawk - Increases the attack power bonus by $s3%.\r\n\r\nAspect of the Dragonhawk - Combines the bonuses from Aspect of the Monkey and Hawk.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 262144, 'EffectSpellClassMaskB_1': 524288, 'EffectSpellClassMaskB_3': 8192, 'EffectSpellClassMaskC_1': 1048576, 'EffectSpellClassMaskC_3': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


beast_mastery_53270 = spell(
    id=53270,
    name='Beast Mastery',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=146, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=145),
    ],
    spell_icon_id=3519,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You master the art of Beast training, teaching you the ability to tame Exotic pets and increasing your total amount of Pet Skill Points by $s2.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 131072, 'EffectSpellClassMaskB_2': 8388609, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


hunting_party_53290 = spell(
    id=53290,
    name='Hunting Party',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=137, misc_value=1),
    ],
    spell_icon_id=3406,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Agility by an additional $s2%, and your Arcane Shot, Explosive Shot and Steady Shot critical strikes have a $h% chance to grant up to 10 party or raid members mana regeneration equal to 1% of the maximum mana per 5 sec. Lasts for $57669d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 33, 'ProcTypeMask': 332096, 'RangeIndex': 1, 'SpellClassSet': 9},
)


hunting_party_53291 = spell(
    id=53291,
    name='Hunting Party',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137, misc_value=1),
    ],
    spell_icon_id=3406,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Agility by an additional $s2%, and your Arcane Shot, Explosive Shot and Steady Shot critical strikes have a $h% chance to grant up to 10 party or raid members mana regeneration equal to 1% of the maximum mana per 5 sec. Lasts for $57669d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 66, 'ProcTypeMask': 332096, 'RangeIndex': 1, 'SpellClassSet': 9},
)


hunting_party_53292 = spell(
    id=53292,
    name='Hunting Party',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=137, misc_value=1),
    ],
    spell_icon_id=3406,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Agility by an additional $s2%, and your Arcane Shot, Explosive Shot and Steady Shot critical strikes have a $h% chance to grant up to 10 party or raid members mana regeneration equal to 1% of the maximum mana per 5 sec. Lasts for $57669d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcTypeMask': 279872, 'RangeIndex': 1, 'SpellClassSet': 9},
)


noxious_stings_53295 = spell(
    id=53295,
    name='Noxious Stings',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=112, misc_value=7991),
    ],
    spell_icon_id=3521,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'If Wyvern Sting is dispelled, the dispeller is also afflicted by Wyvern Sting lasting $s2% of the duration remaining, and increases all damage done by you on targets afflicted by your Serpent Sting by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16384, 'EffectSpellClassMaskB_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


noxious_stings_53296 = spell(
    id=53296,
    name='Noxious Stings',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=112, misc_value=7990),
    ],
    spell_icon_id=3521,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'If Wyvern Sting is dispelled, the dispeller is also afflicted by Wyvern Sting lasting $s2% of the duration remaining, and increases all damage done by you on targets afflicted by your Serpent Sting by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16384, 'EffectSpellClassMaskB_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


noxious_stings_53297 = spell(
    id=53297,
    name='Noxious Stings',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=112, misc_value=7989),
    ],
    spell_icon_id=3521,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'If Wyvern Sting is dispelled, the dispeller is also afflicted by Wyvern Sting lasting $s2% of the duration remaining, and increases all damage done by you on targets afflicted by your Serpent Sting by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16384, 'EffectSpellClassMaskB_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


point_of_no_escape_53298 = spell(
    id=53298,
    name='Point of No Escape',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=3520,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of all of your attacks on targets affected by your Frost Trap, Freezing Trap and Freezing Arrow by $s1%.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 8, 'EffectSpellClassMaskB_1': 16, 'EffectSpellClassMaskC_2': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


point_of_no_escape_53299 = spell(
    id=53299,
    name='Point of No Escape',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=3520,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of all of your attacks on targets affected by your Frost Trap, Freezing Trap and Freezing Arrow by $s1%.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 8, 'EffectSpellClassMaskB_1': 16, 'EffectSpellClassMaskC_2': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


sniper_training_53302 = spell(
    id=53302,
    name='Sniper Training',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, misc_value=14),
    ],
    spell_icon_id=3437,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; moved from SV (talent 2143 -> MM (7,2)); eff0 stationary countdown 6 s -> 3 s [2] (stock spell_hun_sniper_training reads it); stock Kill Shot crit eff1 dropped; stale masks deleted (M15).',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'While you stand still for $53302s1 sec, you gain Sniper Training, increasing the damage of your shots by $64418s1% for $64418d. Stacks up to 3 times.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
    },
)


sniper_training_53303 = spell(
    id=53303,
    name='Sniper Training',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, misc_value=14),
    ],
    spell_icon_id=3437,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; moved from SV (talent 2143 -> MM (7,2)); eff0 stationary countdown 6 s -> 3 s [2] (stock spell_hun_sniper_training reads it); stock Kill Shot crit eff1 dropped; stale masks deleted (M15).',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'While you stand still for $53303s1 sec, you gain Sniper Training, increasing the damage of your shots by $64419s1% for $64419d. Stacks up to 3 times.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
    },
)


sniper_training_53304 = spell(
    id=53304,
    name='Sniper Training',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, misc_value=14),
    ],
    spell_icon_id=3437,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; moved from SV (talent 2143 -> MM (7,2)); eff0 stationary countdown 6 s -> 3 s [2] (stock spell_hun_sniper_training reads it); stock Kill Shot crit eff1 dropped; stale masks deleted (M15).',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'While you stand still for $53304s1 sec, you gain Sniper Training, increasing the damage of your shots by $64420s1% for $64420d. Stacks up to 3 times.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
    },
)


mobility_53483 = spell(
    id=53483,
    name='Mobility',
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=119, base_points=-8001, implicit_target_a=1, apply_aura=107, misc_value=11, radius_yards=100.0),
    ],
    spell_icon_id=2234,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268435456, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the cooldown of your pet's Dash by ${$m1/-1000} sec.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 536870912, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


mobility_53485 = spell(
    id=53485,
    name='Mobility',
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=119, base_points=-16001, implicit_target_a=1, apply_aura=107, misc_value=11, radius_yards=100.0),
    ],
    spell_icon_id=2234,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268435456, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the cooldown of your pet's Dash by ${$m1/-1000} sec.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 536870912, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


cornered_53497 = spell(
    id=53497,
    name='Cornered',
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=79, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-61, implicit_target_a=1, apply_aura=197),
    ],
    spell_icon_id=2239,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CasterAuraState': 13, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When at less than 35% health, your pet does $s1% more damage and has a $s2% reduced chance to be critically hit.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


feeding_frenzy_53511 = spell(
    id=53511,
    name='Feeding Frenzy',
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=226, amplitude=2000, misc_value=7295),
    ],
    spell_icon_id=2960,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your pet does $s1% additional damage to targets with less than 35% health.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1026, 'EffectSpellClassMaskA_2': 131078, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 9, 'SpellPriority': 50},
)


feeding_frenzy_53512 = spell(
    id=53512,
    name='Feeding Frenzy',
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=226, amplitude=2000, misc_value=7295),
    ],
    spell_icon_id=2960,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your pet does $s1% additional damage to targets with less than 35% health.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1026, 'EffectSpellClassMaskA_2': 131078, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9, 'SpellPriority': 50},
)


mobility_53554 = spell(
    id=53554,
    name='Mobility',
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=119, base_points=-8001, implicit_target_a=1, apply_aura=107, misc_value=11, radius_yards=100.0),
    ],
    spell_icon_id=2234,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268435456, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the cooldown on your pet's Dive ability by ${$m1/-1000} sec.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 536870912, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


mobility_53555 = spell(
    id=53555,
    name='Mobility',
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=119, base_points=-16001, implicit_target_a=1, apply_aura=107, misc_value=11, radius_yards=100.0),
    ],
    spell_icon_id=2234,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268435456, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the cooldown on your pet's Dive ability by ${$m1/-1000} sec.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 536870912, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


focused_aim_53620 = spell(
    id=53620,
    name='Focused Aim',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.NOT_LOSE_CASTING_TIME),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=3411,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 pushback 33/66/100% on STEADY_AIMED; eff1 hit (aura 54) -> crit +1/2/3%.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc('Increases your critical strike chance by $s2% and reduces the pushback suffered from damaging attacks while casting Steady Shot or Aimed Shot by $s1%.', 'Your Steady Shot critical strikes reduce the remaining cooldown of Aimed Shot by ' + _mm_sec(FOCUSED_AIM_CDR_MS) + ' sec.', last=False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.STEADY_AIMED}),
    },
)


focused_aim_53621 = spell(
    id=53621,
    name='Focused Aim',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.NOT_LOSE_CASTING_TIME),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=3411,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 pushback 33/66/100% on STEADY_AIMED; eff1 hit (aura 54) -> crit +1/2/3%.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc('Increases your critical strike chance by $s2% and reduces the pushback suffered from damaging attacks while casting Steady Shot or Aimed Shot by $s1%.', 'Your Steady Shot critical strikes reduce the remaining cooldown of Aimed Shot by ' + _mm_sec(FOCUSED_AIM_CDR_MS) + ' sec.', last=False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.STEADY_AIMED}),
    },
)


focused_aim_53622 = spell(
    id=53622,
    name='Focused Aim',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.NOT_LOSE_CASTING_TIME),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=3411,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; eff0 pushback 33/66/100% on STEADY_AIMED; eff1 hit (aura 54) -> crit +1/2/3%.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc('Increases your critical strike chance by $s2% and reduces the pushback suffered from damaging attacks while casting Steady Shot or Aimed Shot by $s1%.', 'Your Steady Shot critical strikes reduce the remaining cooldown of Aimed Shot by ' + _mm_sec(FOCUSED_AIM_CDR_MS) + ' sec.', last=True),
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.STEADY_AIMED}),
    },
)


kindred_spirits_56314 = spell(
    id=56314,
    name='Kindred Spirits',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
    ],
    spell_icon_id=3559,
    notes='pulled from existing data; hunter-rework S1a A3: text only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's damage and the healing it receives by $57447s1% and its movement speed by $57485s1%. The movement speed increase does not stack with other movement speed effects.\n\n|cFF9D9D9DCapstone Bonus: Allows you to tame exotic beasts, and grants your pet $53270s2 additional talent points.|r", 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 524288, 'EffectSpellClassMaskC_1': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


kindred_spirits_56315 = spell(
    id=56315,
    name='Kindred Spirits',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
    ],
    spell_icon_id=3559,
    notes='pulled from existing data; hunter-rework S1a A3: text only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's damage and the healing it receives by $57452s1% and its movement speed by $57484s1%. The movement speed increase does not stack with other movement speed effects.\n\n|cFF9D9D9DCapstone Bonus: Allows you to tame exotic beasts, and grants your pet $53270s2 additional talent points.|r", 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 524288, 'EffectSpellClassMaskC_1': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


kindred_spirits_56316 = spell(
    id=56316,
    name='Kindred Spirits',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
    ],
    spell_icon_id=3559,
    notes='pulled from existing data; hunter-rework S1a A3: text only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's damage and the healing it receives by $57453s1% and its movement speed by $57483s1%. The movement speed increase does not stack with other movement speed effects.\n\nCapstone Bonus: Allows you to tame exotic beasts, and grants your pet $53270s2 additional talent points.", 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 524288, 'EffectSpellClassMaskC_1': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


kindred_spirits_56317 = spell(
    id=56317,
    name='Kindred Spirits',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
    ],
    spell_icon_id=3559,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's damage by $s1% and you and your pet's movement speed by $s2% while your pet is active. This does not stack with other movement speed increasing effects.", 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 524288, 'EffectSpellClassMaskC_1': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


kindred_spirits_56318 = spell(
    id=56318,
    name='Kindred Spirits',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
    ],
    spell_icon_id=3559,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's damage by $s1% and you and your pet's movement speed by $s2% while your pet is active. This does not stack with other movement speed increasing effects.", 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 524288, 'EffectSpellClassMaskC_1': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


t_n_t_56333 = spell(
    id=56333,
    name='T.N.T.',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=355,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Explosive Shot,  Explosive Trap, Black Arrow and Immolation Trap by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 4, 'EffectSpellClassMaskB_2': 2147483648, 'EffectSpellClassMaskB_3': 512, 'EffectSpellClassMaskC_1': 4, 'EffectSpellClassMaskC_2': 134217728, 'EffectSpellClassMaskC_3': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


t_n_t_56336 = spell(
    id=56336,
    name='T.N.T.',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=355,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Explosive Shot,  Explosive Trap, Black Arrow and Immolation Trap by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 4, 'EffectSpellClassMaskB_2': 2147483648, 'EffectSpellClassMaskB_3': 512, 'EffectSpellClassMaskC_1': 4, 'EffectSpellClassMaskC_2': 134217728, 'EffectSpellClassMaskC_3': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


t_n_t_56337 = spell(
    id=56337,
    name='T.N.T.',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=355,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Explosive Shot,  Explosive Trap, Black Arrow and Immolation Trap by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 4, 'EffectSpellClassMaskB_2': 2281701376, 'EffectSpellClassMaskB_3': 512, 'EffectSpellClassMaskC_1': 4, 'EffectSpellClassMaskC_2': 134217728, 'EffectSpellClassMaskC_3': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


hunter_vs_wild_56339 = spell(
    id=56339,
    name='Hunter vs. Wild',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=268, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=212, misc_value=2),
    ],
    spell_icon_id=3647,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 268435456, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases you and your pet's attack power and ranged attack power equal to $s1% of your total Stamina.", 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 9},
)


hunter_vs_wild_56340 = spell(
    id=56340,
    name='Hunter vs. Wild',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=268, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=212, misc_value=2),
    ],
    spell_icon_id=3647,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases you and your pet's attack power and ranged attack power equal to $s1% of your total Stamina.", 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 9},
)


hunter_vs_wild_56341 = spell(
    id=56341,
    name='Hunter vs. Wild',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=268, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=212, misc_value=2),
    ],
    spell_icon_id=3647,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases you and your pet's attack power and ranged attack power equal to $s1% of your total Stamina.", 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 9},
)


lock_and_load_56342 = spell(
    id=56342,
    name='Lock and Load',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=2, trigger_spell=56453),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=21, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3579,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a $s1% chance when you trap a target with Freezing Trap, Freezing Arrow or Frost Trap and a $s2% chance when you deal periodic damage with your Immolation Trap, Explosive Trap or Black Arrow to cause your next 2 Arcane Shot or Explosive Shot spells to trigger no cooldown, cost no mana and consume no ammo. This effect has a $56342s3 sec cooldown.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2359296, 'RangeIndex': 1, 'SpellClassSet': 9},
)


lock_and_load_56343 = spell(
    id=56343,
    name='Lock and Load',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=2, trigger_spell=56453),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3579,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a $s1% chance when you trap a target with Freezing Trap, Freezing Arrow or Frost Trap and a $s2% chance when you deal periodic damage with your Immolation Trap, Explosive Trap or Black Arrow to cause your next 2 Arcane Shot or Explosive Shot spells to trigger no cooldown, cost no mana and consume no ammo. This effect has a $56342s3 sec cooldown.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2359296, 'RangeIndex': 1, 'SpellClassSet': 9},
)


lock_and_load_56344 = spell(
    id=56344,
    name='Lock and Load',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=2, trigger_spell=56453),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3579,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a $s1% chance when you trap a target with Freezing Trap, Freezing Arrow or Frost Trap and a $s2% chance when you deal periodic damage with your Immolation Trap, Explosive Trap or Black Arrow to cause your next 2 Arcane Shot or Explosive Shot spells to trigger no cooldown, cost no mana and consume no ammo. This effect has a $56342s3 sec cooldown.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2359296, 'RangeIndex': 1, 'SpellClassSet': 9},
)


trap_mastery_63457 = spell(
    id=63457,
    name='Trap Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=69,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Frost Trap and Freezing Trap - Increases the duration by $s1%.\r\n\r\nImmolation Trap, Explosive Trap and Black Arrow - Increases the periodic damage done by $s2%.\r\n\r\nSnake Trap - Increases the number of snakes summoned by $*2;s3.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 24, 'EffectSpellClassMaskB_1': 4, 'EffectSpellClassMaskB_2': 134217728, 'EffectSpellClassMaskB_3': 131072, 'EffectSpellClassMaskC_2': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


trap_mastery_63458 = spell(
    id=63458,
    name='Trap Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=69,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Frost Trap and Freezing Trap - Increases the duration by $s1%.\r\n\r\nImmolation Trap, Explosive Trap and Black Arrow - Increases the periodic damage done by $s2%.\r\n\r\nSnake Trap - Increases the number of snakes summoned by $*2;s3.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 24, 'EffectSpellClassMaskB_1': 4, 'EffectSpellClassMaskB_2': 134217728, 'EffectSpellClassMaskB_3': 131072, 'EffectSpellClassMaskC_2': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


quick_shots_6150 = spell(
    id=6150,
    name='Quick Shots',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER_PCT),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=167),
    ],
    spell_icon_id=561,
    notes='pulled for H0 (hunter rework WP-0); rewritten as the Aspect of the Hawk proc (SHARED B6.3): +10% melee and ranged attack power for 10 s',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 3301, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Granted by Aspect of the Hawk.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attack power increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 9, 'SpellClassMask_2': 512, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


freezing_arrow_60202 = spell(
    id=60202,
    name='Freezing Arrow',
    school=School.FROST,
    attributes=65536,
    category=411,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=100.0,
    duration_ms=30000,
    effects=[
        Effect(type=104, die_sides=0, implicit_target_a=87, misc_value=193771),
    ],
    spell_icon_id=180,
    notes='pulled for H0 (hunter rework WP-0)',
    raw_overrides={'AttributesEx2': 134217732, 'Targets': 64, 'CastingTimeIndex': 1, 'InterruptFlags': 1, 'ProcChance': 101, 'BaseLevel': 46, 'SpellLevel': 46, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fire a freezing arrow that places a Freezing Trap at the target location, freezing the first enemy that approaches, preventing all action for up to $14309d.  Any damage caused will break the ice.  Trap will exist for $60202d.  Only one trap can be active at a time.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassSet': 9, 'SpellClassMask_1': 128, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


freezing_arrow_effect_60210 = spell(
    id=60210,
    name='Freezing Arrow Effect',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.FREEZE,
    attributes=1073741824,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=10.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_CRIT_CHANCE_FOR_CASTER),
    ],
    spell_icon_id=180,
    notes='pulled for H0 (hunter rework WP-0)',
    raw_overrides={'AttributesEx': 262144, 'AttributesEx2': 134217728, 'AttributesEx4': 536872960, 'AttributesEx6': 8388608, 'CastingTimeIndex': 1, 'AuraInterruptFlags': 4718594, 'ProcChance': 101, 'BaseLevel': 46, 'SpellLevel': 46, 'EquippedItemClass': -1, 'EffectSpellClassMaskB_1': 522951, 'EffectSpellClassMaskB_2': 3632404737, 'EffectSpellClassMaskB_3': 85641, 'SpellVisualID_1': 4499, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fire a freezing arrow that places a Freezing Trap at the target location, freezing the first enemy that approaches, preventing all action for up to $14309d.  Any damage caused will break the ice.  Trap will exist for $60202d.  Only one trap can be active at a time.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Frozen.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 9, 'SpellClassMask_1': 8, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


glyph_of_the_hawk_56856 = spell(
    id=56856,
    name='Glyph of the Hawk',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=8),
    ],
    spell_icon_id=1,
    notes='pulled for H0 (hunter rework WP-0)',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_2': 512, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Increases the attack power bonus of your Aspect of the Hawk proc by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 9, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0},
)


glyph_of_explosive_shot_63066 = spell(
    id=63066,
    name='Glyph of Explosive Shot',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=7),
    ],
    spell_icon_id=1,
    notes='pulled for H0 (hunter rework WP-0)',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_3': 512, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Increases the critical strike chance of Explosive Shot by $63066s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 9, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0},
)


intimidation_24394 = spell(
    id=24394,
    name='Intimidation',
    school=School.NORMAL,
    mechanic=Mechanic.STUN,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.THREAT, base_points=579, points_per_level=21.0, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=166,
    notes='pulled for H0 (hunter rework WP-0)',
    raw_overrides={'AttributesEx6': 8388608, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 40, 'SpellLevel': 40, 'RangeIndex': 2, 'EquippedItemClass': -1, 'SpellVisualID_1': 2816, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Command your pet to intimidate the target, causing a high amount of threat and stunning the target for $24394d. Lasts $19577d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'AuraDescription_Lang_Mask': 16712190, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


sniper_training_64419 = spell(
    id=64419,
    name='Sniper Training',
    school=School.NATURE,
    attributes=134217728,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=3437,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 5.11): stock row edited in place; +2% per stack [1], ppl 0, 3 stacks, 12 s; eff0 DAMAGE on HUNTER_SHOTS, eff1 DOT on the mark DoTs (d2 b28); visible (M1).',
    raw_overrides={
        'AttributesEx': 32,
        'AttributesEx2': 16384,
        'AuraDescription_Lang_Mask': 16712190,
        'AuraDescription_Lang_enUS': 'Damage of your shots increased by $s1%.',
        'CastingTimeIndex': 1,
        'CumulativeAura': 3,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'While you stand still for $53303s1 sec, you gain Sniper Training, increasing the damage of your shots by $64419s1% for $64419d. Stacks up to 3 times.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.HUNTER_SHOTS, 2: (0, 0, m.MARK_DOT)}),
    },
)


sniper_training_64420 = spell(
    id=64420,
    name='Sniper Training',
    school=School.NATURE,
    attributes=134217728,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=3437,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 5.11): stock row edited in place; +3% per stack [2], ppl 0, 3 stacks, 12 s; eff0 DAMAGE on HUNTER_SHOTS, eff1 DOT on the mark DoTs (d2 b28); visible (M1).',
    raw_overrides={
        'AttributesEx': 32,
        'AttributesEx2': 16384,
        'AuraDescription_Lang_Mask': 16712190,
        'AuraDescription_Lang_enUS': 'Damage of your shots increased by $s1%.',
        'CastingTimeIndex': 1,
        'CumulativeAura': 3,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'While you stand still for $53304s1 sec, you gain Sniper Training, increasing the damage of your shots by $64420s1% for $64420d. Stacks up to 3 times.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.HUNTER_SHOTS, 2: (0, 0, m.MARK_DOT)}),
    },
)


master_tactician_34834 = spell(
    id=34834,
    name='Master Tactician',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_WEAPON_CRIT_PERCENT),
    ],
    spell_icon_id=2233,
    notes='pulled for H0 (hunter rework WP-0)',
    raw_overrides={'AttributesEx2': 4, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 522819, 'EffectSpellClassMaskA_2': 128, 'EffectSpellClassMaskB_1': 522819, 'EffectSpellClassMaskB_2': 1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your successful ranged attacks have a chance to increase your critical strike chance with all attacks by $34834s1% for $34834d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Critical strike chance with all attacks increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 9, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectSpellClassMaskA_3': 536870912},
)


master_tactician_34835 = spell(
    id=34835,
    name='Master Tactician',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_WEAPON_CRIT_PERCENT),
    ],
    spell_icon_id=2233,
    notes='pulled for H0 (hunter rework WP-0)',
    raw_overrides={'AttributesEx2': 4, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 522819, 'EffectSpellClassMaskA_2': 128, 'EffectSpellClassMaskB_1': 522819, 'EffectSpellClassMaskB_2': 1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your successful ranged attacks have a chance to increase your critical strike chance with all attacks by $34835s1% for $34835d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Critical strike chance with all attacks increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 9, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectSpellClassMaskA_3': 536870912},
)


master_tactician_34836 = spell(
    id=34836,
    name='Master Tactician',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.MOD_WEAPON_CRIT_PERCENT),
    ],
    spell_icon_id=2233,
    notes='pulled for H0 (hunter rework WP-0)',
    raw_overrides={'AttributesEx2': 4, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 522819, 'EffectSpellClassMaskA_2': 128, 'EffectSpellClassMaskB_1': 522819, 'EffectSpellClassMaskB_2': 1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your successful ranged attacks have a chance to increase your critical strike chance with all attacks by $34836s1% for $34836d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Critical strike chance with all attacks increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 9, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectSpellClassMaskA_3': 536870912},
)


master_tactician_34837 = spell(
    id=34837,
    name='Master Tactician',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_WEAPON_CRIT_PERCENT),
    ],
    spell_icon_id=2233,
    notes='pulled for H0 (hunter rework WP-0)',
    raw_overrides={'AttributesEx2': 4, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 522819, 'EffectSpellClassMaskA_2': 128, 'EffectSpellClassMaskB_1': 522819, 'EffectSpellClassMaskB_2': 1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your successful ranged attacks have a chance to increase your critical strike chance with all attacks by $34837s1% for $34837d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Critical strike chance with all attacks increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 9, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectSpellClassMaskA_3': 536870912},
)


cobra_strikes_53257 = spell(
    id=53257,
    name='Cobra Strikes',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=7),
    ],
    spell_icon_id=2936,
    notes='Re-masked in H0-P1 from d1 b28 (every pet ability) to d2 b22 (commanded pet spells, carried from S1): the stock mask made every Spit/Venom Spit crit for 10 s without spending a stack. BM S1 rewrites the talent (PROC_TRIGGER_SPELL -> DUMMY, Arcane Shot reset).',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'CumulativeAura': 2, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_3': 4194304, 'SpellVisualID_1': 11387, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': "You have a chance when you critically hit with Arcane Shot, Steady Shot or Kill Shot to cause your pet's next 2 special attacks to critically hit.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Pet critical strike chance with abilities increased 100%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 9, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


# ---------------------------------------------------------------------------
# S1a pulls (hunter-rework S1a 0-dsl): rows pulled unchanged; values are edited by later S1a work packages.
# ---------------------------------------------------------------------------

the_beast_within_34471 = spell(
    id=34471,
    name='The Beast Within',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=AuraType.MOD_POWER_COST_SCHOOL_PCT, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
    ],
    spell_icon_id=2229,
    notes='pulled from existing data; hunter-rework S1a A6: 15 s, eff1 bp 4 (script sets per rank), eff2 stun immunity deleted',
    raw_overrides={'AttributesEx': 164864, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 50, 'SpellLevel': 50, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 1, 'SpellVisualID_1': 7278, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'When your pet is under the effects of Bestial Wrath, you also go into a rage causing $34471s2% additional damage and reducing mana costs of all spells by $34471s1% for $34471d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Enraged.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryCategory': 133, 'SpellClassSet': 9, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0},
)


kindred_spirits_57447 = spell(
    id=57447,
    name='Kindred Spirits',
    school=School.NATURE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_PCT),
    ],
    spell_icon_id=3559,
    notes='pulled from existing data; hunter-rework S1a: bp 7/14/20; new eff1 MOD_HEALING_PCT (healing taken) same bp',
    raw_overrides={'CastingTimeIndex': 1, 'AuraInterruptFlags': 524288, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': "Increases your pet's damage and the healing it receives by $57447s1% and its movement speed by $57485s1%. The movement speed increase does not stack with other movement speed effects.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All damage done increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


kindred_spirits_57452 = spell(
    id=57452,
    name='Kindred Spirits',
    school=School.NATURE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_PCT),
    ],
    spell_icon_id=3559,
    notes='pulled from existing data; hunter-rework S1a: bp 7/14/20; new eff1 MOD_HEALING_PCT (healing taken) same bp',
    raw_overrides={'CastingTimeIndex': 1, 'AuraInterruptFlags': 524288, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': "Increases your pet's damage and the healing it receives by $57452s1% and its movement speed by $57484s1%. The movement speed increase does not stack with other movement speed effects.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All damage done increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


kindred_spirits_57453 = spell(
    id=57453,
    name='Kindred Spirits',
    school=School.NATURE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_PCT),
    ],
    spell_icon_id=3559,
    notes='pulled from existing data; hunter-rework S1a: bp 7/14/20; new eff1 MOD_HEALING_PCT (healing taken) same bp',
    raw_overrides={'CastingTimeIndex': 1, 'AuraInterruptFlags': 524288, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': "Increases your pet's damage and the healing it receives by $57453s1% and its movement speed by $57483s1%. The movement speed increase does not stack with other movement speed effects.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All damage done increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


kindred_spirits_57483 = spell(
    id=57483,
    name='Kindred Spirits',
    school=School.NATURE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=3559,
    notes='pulled from existing data; hunter-rework S1a: effect 119 -> 6 (plain APPLY_AURA on the pet), no radius; bp 3/6/10',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx2': 4194308, 'AttributesEx3': 268435456, 'AttributesEx5': 1024, 'AttributesEx7': 268435456, 'CastingTimeIndex': 1, 'AuraInterruptFlags': 524288, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': "Increases your pet's damage and the healing it receives by $57453s1% and its movement speed by $57483s1%. The movement speed increase does not stack with other movement speed effects.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increased movement speed by $s1%. This does not stack with other movement speed increasing effects.', 'AuraDescription_Lang_Mask': 16712190, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


kindred_spirits_57484 = spell(
    id=57484,
    name='Kindred Spirits',
    school=School.NATURE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=3559,
    notes='pulled from existing data; hunter-rework S1a: effect 119 -> 6 (plain APPLY_AURA on the pet), no radius; bp 3/6/10',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx2': 4194308, 'AttributesEx3': 268435456, 'AttributesEx5': 1024, 'AttributesEx7': 268435456, 'CastingTimeIndex': 1, 'AuraInterruptFlags': 524288, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': "Increases your pet's damage and the healing it receives by $57452s1% and its movement speed by $57484s1%. The movement speed increase does not stack with other movement speed effects.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increased movement speed by $s1%. This does not stack with other movement speed increasing effects.', 'AuraDescription_Lang_Mask': 16712190, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


kindred_spirits_57485 = spell(
    id=57485,
    name='Kindred Spirits',
    school=School.NATURE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=3559,
    notes='pulled from existing data; hunter-rework S1a: effect 119 -> 6 (plain APPLY_AURA on the pet), no radius; bp 3/6/10',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx2': 4194308, 'AttributesEx3': 268435456, 'AttributesEx5': 1024, 'AttributesEx7': 268435456, 'CastingTimeIndex': 1, 'AuraInterruptFlags': 524288, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': "Increases your pet's damage and the healing it receives by $57447s1% and its movement speed by $57485s1%. The movement speed increase does not stack with other movement speed effects.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increased movement speed by $s1%. This does not stack with other movement speed increasing effects.', 'AuraDescription_Lang_Mask': 16712190, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


focused_fire_35060 = spell(
    id=35060,
    name='Focused Fire',
    school=School.NATURE,
    attributes=328064,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=-1,
    effects=[
        Effect(type=119, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
    ],
    spell_icon_id=2221,
    notes='pulled from existing data; hunter-rework S1a B7: eff0 bp -1 (zeroed pet aura)',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx2': 4194304, 'AttributesEx3': 268435456, 'CastingTimeIndex': 1, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


focused_fire_35061 = spell(
    id=35061,
    name='Focused Fire',
    school=School.NATURE,
    attributes=328064,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=-1,
    effects=[
        Effect(type=119, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
    ],
    spell_icon_id=2221,
    notes='pulled from existing data; hunter-rework S1a B7: eff0 bp -1 (zeroed pet aura)',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx2': 4194304, 'AttributesEx3': 268435456, 'CastingTimeIndex': 1, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


glyph_of_aspect_of_the_viper_56851 = spell(
    id=56851,
    name='Glyph of Aspect of the Viper',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.EFFECT1),
    ],
    spell_icon_id=1,
    notes='pulled from existing data; hunter-rework S1a A10: re-keyed to ADD_PCT_MODIFIER EFFECT1 on Viper poison (0,0,0x4000000)',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Increases the mana restored by your Aspect of the Viper by 10%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 9, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectSpellClassMaskA_3': 67108864},
)


kill_command_58914 = spell(
    id=58914,
    name='Kill Command',
    school=School.NORMAL,
    attributes=256,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=5, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2226,
    notes='inert by data, hunter-rework S1a A9',
    raw_overrides={'AttributesEx2': 4, 'CastingTimeIndex': 1, 'ProcTypeMask': 0, 'ProcChance': 0, 'ProcCharges': 0, 'BaseLevel': 1, 'SpellLevel': 1, 'CumulativeAura': 3, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases damage done by pet special abilities by $34027s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases damage done by pet special abilities by $34027s1%.', 'AuraDescription_Lang_Mask': 16712190, 'DefenseType': 2, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


kill_command_34027 = spell(
    id=34027,
    name='Kill Command',
    school=School.NORMAL,
    attributes=327952,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2226,
    notes='inert by data, hunter-rework S1a A9',
    raw_overrides={'AttributesEx': 512, 'CastingTimeIndex': 1, 'ProcTypeMask': 0, 'ProcChance': 0, 'ProcCharges': 0, 'BaseLevel': 66, 'SpellLevel': 66, 'CumulativeAura': 3, 'EquippedItemClass': -1, 'SpellVisualID_1': 8138, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Give the command to kill, increasing your pet's damage done from special attacks by ${$34027M1*3}%.  Each special attack done by the pet reduces the damage bonus by $34027s1%.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage done by pet special abilities increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 9, 'SpellClassMask_2': 2048, 'DefenseType': 2, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


kill_command_60110 = spell(
    id=60110,
    name='Kill Command',
    school=School.NORMAL,
    attributes=328080,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2226,
    notes='inert by data, hunter-rework S1a A9',
    raw_overrides={'AttributesEx': 512, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 66, 'SpellLevel': 66, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Give the command to kill, increasing your pet's damage done from special attacks by ${$34027M1*3}%.  Each special attack done by the pet reduces the damage bonus by $34027s1%.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 9, 'DefenseType': 2, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


kill_command_60113 = spell(
    id=60113,
    name='Kill Command',
    school=School.NORMAL,
    attributes=328080,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2226,
    notes='inert by data, hunter-rework S1a A9',
    raw_overrides={'AttributesEx': 512, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 66, 'SpellLevel': 66, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Give the command to kill, increasing your pet's damage done from special attacks by ${$34027M1*3}%.  Each special attack done by the pet reduces the damage bonus by $34027s1%.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 9, 'DefenseType': 2, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# ---- S2a pulls (hunter-rework S2a WP-0 0-dsl; MARKSMANSHIP 3 item 1) ----
# Untouched reference copies from pull_dsl.py --constants: Lethal Shots 19426/19427/19429 and Ranged Weapon
# Specialization 19507-19509 (bare ints in hunter_talents.py until A4), Wild Quiver Auto Shot 53254 and Chimera Shot -
# Serpent 53353 (moved here from source/spells/npc.csv in the same change). A3 edits them in place (MARKSMANSHIP 5.6,
# 5.11, 6). 53353 keeps its stock CRLF description breaks, as its npc.csv row had them.

lethal_shots_19426 = spell(
    id=19426,
    name='Lethal Shots',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=105,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; pulled S2a; aura 52 ranged crit (family 0, ranged-weapon gated) -> Arcane Shot crit +2/4/6 (FLAT CRITICAL_CHANCE, mask d0 b11); SpellClassSet 9, EquippedItemClass -1 (subclass dropped).',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc('Increases the critical strike chance of your Arcane Shot by $s1%.', 'Your Arcane Shot critical strikes restore twice as much mana.', last=False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: (m.ARCANE_SHOT, 0, 0)}),
    },
)


lethal_shots_19427 = spell(
    id=19427,
    name='Lethal Shots',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=105,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; pulled S2a; aura 52 ranged crit (family 0, ranged-weapon gated) -> Arcane Shot crit +2/4/6 (FLAT CRITICAL_CHANCE, mask d0 b11); SpellClassSet 9, EquippedItemClass -1 (subclass dropped).',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc('Increases the critical strike chance of your Arcane Shot by $s1%.', 'Your Arcane Shot critical strikes restore twice as much mana.', last=False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: (m.ARCANE_SHOT, 0, 0)}),
    },
)


lethal_shots_19429 = spell(
    id=19429,
    name='Lethal Shots',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=105,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; pulled S2a; aura 52 ranged crit (family 0, ranged-weapon gated) -> Arcane Shot crit +2/4/6 (FLAT CRITICAL_CHANCE, mask d0 b11); SpellClassSet 9, EquippedItemClass -1 (subclass dropped).',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _mm_desc('Increases the critical strike chance of your Arcane Shot by $s1%.', 'Your Arcane Shot critical strikes restore twice as much mana.', last=True),
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: (m.ARCANE_SHOT, 0, 0)}),
    },
)


ranged_weapon_specialization_19507 = spell(
    id=19507,
    name='Ranged Weapon Specialization',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=1632,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; pulled S2a; aura 79 physical +1/3/5% (family 0, ranged-weapon gated) -> PCT DAMAGE +2/4/6% on RWS_SHOTS; SpellClassSet 9, EquippedItemClass -1 (subclass and DurationIndex 0 dropped, duration -1).',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the damage of your Auto Shot and shots by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.RWS_SHOTS}),
    },
)


ranged_weapon_specialization_19508 = spell(
    id=19508,
    name='Ranged Weapon Specialization',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=1632,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; pulled S2a; aura 79 physical +1/3/5% (family 0, ranged-weapon gated) -> PCT DAMAGE +2/4/6% on RWS_SHOTS; SpellClassSet 9, EquippedItemClass -1 (subclass and DurationIndex 0 dropped, duration -1).',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the damage of your Auto Shot and shots by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.RWS_SHOTS}),
    },
)


ranged_weapon_specialization_19509 = spell(
    id=19509,
    name='Ranged Weapon Specialization',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=1632,
    notes='hunter-rework S2a A3 (MARKSMANSHIP 6): stock rank edited in place, stored = live - 1; pulled S2a; aura 79 physical +1/3/5% (family 0, ranged-weapon gated) -> PCT DAMAGE +2/4/6% on RWS_SHOTS; SpellClassSet 9, EquippedItemClass -1 (subclass and DurationIndex 0 dropped, duration -1).',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the damage of your Auto Shot and shots by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 9,
        **_mm_masks({1: m.RWS_SHOTS}),
    },
)


wild_quiver_auto_shot_53254 = spell(
    id=53254,
    name='Wild Quiver Auto Shot',
    school=School.NATURE,
    attributes=327698,
    cast_time_ms=-1000000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=60, implicit_target_a=6),
    ],
    spell_icon_id=83,
    notes='pulled S2a; hunter-rework S2a A3 (MARKSMANSHIP 5.11): weapon_potency 60 (stock 80%), AttributesEx3 |= 0x10000 (the extra shot rolls no procs, so its d0 b0 cannot re-proc Wild Quiver).',
    raw_overrides={'AttributesEx2': 131072, 'AttributesEx3': 65536, 'CastingTimeIndex': 18, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'Speed': 40.0, 'EquippedItemClass': -1, 'ActiveIconID': 122, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'You have a chance to shoot an additional shot when doing damage with your auto shot, dealing $53254s1% weapon nature damage. Wild Quiver consumes no ammo.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Firing $s1% Weapon Damage to the target.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 9, 'SpellClassMask_1': 1, 'SpellClassMask_3': 128, 'DefenseType': 3, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


chimera_shot_serpent_53353 = spell(
    id=53353,
    name='Chimera Shot - Serpent',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=-1000000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, die_sides=0, implicit_target_a=6),
    ],
    spell_icon_id=3412,
    notes='pulled S2a; hunter-rework S2a A3 (MARKSMANSHIP 5.6): SpellClassMask_3 0xC00 -> 0x800 (d2 b10 stripped, CHIMERA_SERPENT kept).',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx6': 33, 'CastingTimeIndex': 18, 'ProcChance': 101, 'BaseLevel': 60, 'SpellLevel': 60, 'Speed': 40.0, 'EquippedItemClass': -1, 'SpellVisualID_1': 11725, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'You deal $53209s3% weapon damage, refreshing the current Sting on your target and triggering an effect:\r\n\r\nSerpent Sting - Instantly deals 40% of the damage done by your Serpent Sting.\r\n\r\nViper Sting - Instantly restores mana to you equal to 60% of the total amount drained by your Viper Sting.\r\n\r\nScorpid Sting - Attempts to Disarm the target for 10 sec. This effect cannot occur more than once per 1 minute.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'SpellClassSet': 9, 'SpellClassMask_3': 2048, 'DefenseType': 3, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
