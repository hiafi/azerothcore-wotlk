"""
Death Knight - S3a Unholy: the pulled stock helper/buff/hit rows the Unholy talents edit in place (Necrosis hit 51460,
Desolation buffs 63583 / 66800 / 66801). Pulled byte-identical at S3a WP-0.2 (npc.csv lines deleted); A7 edits them.
Source of truth: docs/reworks/death-knight-unholy-rework.md, .agents/plans/death-knight-rework/death-knight-rework.S3a-WP-BRIEF.md.
"""

from lib.dsl import AuraType, Effect, EffectType, School
from lib.dsl.registry import scripted_by, spell

necrosis_51460 = spell(
    id=51460,
    name='Necrosis',
    school=School.SHADOW,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, die_sides=0, implicit_target_a=6,
               potency_excluded='amount is a percent of the auto attack hit, set by the stock -51459 script'),
    ],
    spell_icon_id=9,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 536870912, 'AttributesEx3': (1074005504 & ~0x200) | 0x10000, 'AttributesEx4': 256, 'AttributesEx6': 536870912, 'CastingTimeIndex': 1, 'BaseLevel': 55, 'SpellLevel': 55, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Your auto attacks deal additional Shadow damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 15, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'RuneCostID': 884},
)


desolation_buff_63583 = spell(
    id=63583,
    name='Desolation',
    school=School.SHADOW,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=5,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
    ],
    spell_icon_id=235,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1024, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 12948, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Your Scourge Strikes cause you to deal $s1% additional damage with all attacks for the next $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage dealt increased.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 15, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'RuneCostID': 2327},
)


desolation_buff_66800 = spell(
    id=66800,
    name='Desolation',
    school=School.SHADOW,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=5,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
    ],
    spell_icon_id=235,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1024, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 12948, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Your Scourge Strikes cause you to deal $s1% additional damage with all attacks for the next $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage dealt increased.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 15, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'RuneCostID': 1208},
)


desolation_buff_66801 = spell(
    id=66801,
    name='Desolation',
    school=School.SHADOW,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=5,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
    ],
    spell_icon_id=235,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1024, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 12948, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Your Scourge Strikes cause you to deal $s1% additional damage with all attacks for the next $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage dealt increased.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 15, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'RuneCostID': 2320},
)


scripted_by(47632, 'spell_dk_death_coil_damage_unholy')
scripted_by(50526, 'spell_dk_wandering_plague_engaged')
