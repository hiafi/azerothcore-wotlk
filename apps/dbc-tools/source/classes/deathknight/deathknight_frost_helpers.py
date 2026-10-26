"""
Death Knight - S2a Frost: the pulled stock helper/buff/off-hand rows the Frost talents edit in place (Icy Clutch, Icy Talons buffs, Freezing Fog, Plague Strike off-hand copy).
Source of truth: docs/reworks/death-knight-frost-rework.md, .agents/plans/death-knight-rework/death-knight-rework.S2a-WP-BRIEF.md.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, School
from lib.dsl.registry import (
    bonus_coefficients, const, custom_attr, linked_spell, procs_on, scripted_by, spell, unbind_bonus_coefficients,
    unbind_script,
)

from . import _masks as m

icy_clutch_50434 = spell(
    id=50434,
    name='Icy Clutch',
    school=School.FROST,
    attributes=67108864,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=143,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 4, 'AttributesEx3': 262144, 'AttributesEx4': 1, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 2640, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Victims of your Frost Fever disease are Chilled, reducing their movement speed for $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement slowed.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 15, 'SpellClassMask_2': 262144, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


icy_clutch_50435 = spell(
    id=50435,
    name='Icy Clutch',
    school=School.FROST,
    attributes=67108864,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-36, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=143,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 4, 'AttributesEx3': 262144, 'AttributesEx4': 1, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 2640, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Victims of your Frost Fever disease are Chilled, reducing their movement speed for $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement slowed.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 15, 'SpellClassMask_2': 262144, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


icy_clutch_50436 = spell(
    id=50436,
    name='Icy Clutch',
    school=School.FROST,
    attributes=67108864,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=143,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 4, 'AttributesEx3': 262144, 'AttributesEx4': 1, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 2640, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Victims of your Frost Fever disease are Chilled, reducing their movement speed for $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement slowed.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 15, 'SpellClassMask_2': 262144, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


icy_talons_50882 = spell(
    id=50882,
    name='Icy Talons',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, mechanic=8, implicit_target_a=1, apply_aura=AuraType.MOD_MELEE_HASTE),
    ],
    spell_icon_id=3785,
    notes='pulled from existing data; S2 user ruling 2026-10-25: stored 2 = +3% (was +7%)',
    raw_overrides={'CastingTimeIndex': 1, 'SpellLevel': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 2759, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You leech heat from victims of your Frost Fever, so that when their melee attack speed is reduced, yours increases for the next $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attack speed increased.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 15, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


icy_talons_58575 = spell(
    id=58575,
    name='Icy Talons',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, mechanic=8, implicit_target_a=1, apply_aura=AuraType.MOD_MELEE_HASTE),
    ],
    spell_icon_id=3785,
    notes='pulled from existing data; S2 user ruling 2026-10-25: stored 5 = +6% (was +14%)',
    raw_overrides={'CastingTimeIndex': 1, 'SpellLevel': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 2759, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'You leech heat from victims of your Frost Fever, so that when their melee attack speed is reduced, yours increases for the next $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attack speed increased.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 15, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


icy_talons_58576 = spell(
    id=58576,
    name='Icy Talons',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, mechanic=8, implicit_target_a=1, apply_aura=AuraType.MOD_MELEE_HASTE),
    ],
    spell_icon_id=3785,
    notes='pulled from existing data; S2 user ruling 2026-10-25: stored 9 = +10% (was +20%)',
    raw_overrides={'CastingTimeIndex': 1, 'SpellLevel': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 2759, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'You leech heat from victims of your Frost Fever, so that when their melee attack speed is reduced, yours increases for the next $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attack speed increased.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 15, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


freezing_fog_59052 = spell(
    id=59052,
    name='Freezing Fog',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    attributes=151060480,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1001, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=14),
    ],
    spell_icon_id=2131,
    notes='pulled from existing data',
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 65536, 'ProcChance': 100, 'ProcCharges': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectDieSides_3': 1, 'EffectBasePoints_3': -1, 'ImplicitTargetA_2': 1, 'EffectSpellClassMaskA_2': 2, 'EffectSpellClassMaskB_2': 2, 'EffectSpellClassMaskC_1': 8192, 'SpellVisualID_1': 10148, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Your next Howling Blast costs no runes.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Howling Blast costs no runes.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 15, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


plague_strike_66216 = spell(
    id=66216,
    name='Plague Strike',
    school=School.NORMAL,
    attributes=2359312,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=49, implicit_target_a=6),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, base_points=1, points_per_level=0.5933, implicit_target_a=6),
    ],
    spell_icon_id=2719,
    notes=(
        'RETUNE 2026-10-25 (re-anchor): the flat follows 45462\'s re-anchored eff0 at 0.245 x: 2 at level 1, 37 at 60 '
        '(bp 1, 0.5933 per level; was bp 30 / 2.48 = 177 at 60). '
        'pulled from existing data; S2a D1: off-hand copy of 45462 (Threat of Thassarian), percent effect first (weapon_potency 49 = '
        '45462 E1), then 0.245 x the main-hand flat (45462 is flat-first so its flat is scaled by 49%; half of that for the off-hand doubling: bp 124 / 10.12 per level), '
        'EFFECT_2 empty (stale E2 twins deleted), cast-triggered.'
    ),
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 17039360, 'CastingTimeIndex': 1, 'SpellLevel': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'SpellVisualID_1': 11624, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A vicious strike that deals offhand weapon damage plus a bonus and infects the target with Blood Plague, a disease dealing Shadow damage over time.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassSet': 15, 'SpellClassMask_1': 1, 'DefenseType': 2, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'RuneCostID': 1845},
)


scripted_by(plague_strike_66216, 'spell_dk_frost_offhand')
