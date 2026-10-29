"""
Warrior - W0a shared foundations, data half: the rage-model script numbers (`const()`s the C++ reads through the
generated WarriorData.h), the three stances pulled out of npc.csv, Stance Mastery's value, quest spell 8616.

Source of truth: docs/reworks/warrior-shared-rework.md ("Stances", "Rage generation"),
.agents/plans/warrior-rework/warrior-rework.W0a-HANDOFF.md (D9, D10, D12-D14, Known-hard 1 and 2) and
warrior-rework.W0a-WP-BRIEF.md (variable names).

Rage model (D12/D13): one table keyed on level, the level-60 bracket applies at every level until 70/80 open. Dealt rage
per white hit is (k * 7.5 * damage / c + speed) / 2, capped at the stock 15 * damage / c, where the speed part is the
hasted swing time * 3.5 * m (main hand) or * 0.875 (off hand). k and m are first cuts: the W0a rage sweep (D15) solves
them and the solved values land in the next rebuild.
"""

from lib.dsl import Effect
from lib.dsl.registry import const, override_skill_line_ability, spell


# =====================================================================================================================
# Script numbers (hidden constants; generated WarriorData::NAME, read by WarriorMechanics.cpp)
# =====================================================================================================================
RAGE_K_60 = const(
    'RAGE_K_60', 0.43,
    'Rage: level-60 bracket, multiplier on the damage term of rage dealt (stock 1.0) [tune].')
RAGE_M_60 = const(
    'RAGE_M_60', 1.35,
    'Rage: level-60 bracket, multiplier on the weapon-speed term of rage dealt (stock 1.0); user pick 2026-10-29 from '
    'the W0a rage sweep (two-hander = stock at bracket start, dual-wield advantage halved) [tune].')
RAGE_MH_SPEED_FACTOR = const(
    'RAGE_MH_SPEED_FACTOR', 3.5,
    'Rage: main-hand weapon-speed factor, rage per second of hasted swing time before m (stock 3.5) [fixed].')
RAGE_OH_SPEED_FACTOR = const(
    'RAGE_OH_SPEED_FACTOR', 0.875,
    'Rage: off-hand weapon-speed factor, rage per second of hasted swing time (stock 1.75, halved) [fixed].')
RAGE_SPEED_FIXED_POINT = const(
    'RAGE_SPEED_FIXED_POINT', 100,
    'Rage: the speed factor handed to Unit::RewardRage is in hundredths so m\'s decimals survive [fixed].',
    cpp_type='uint32')
RAGE_STANCE_MASTERY_POINTS = const(
    'RAGE_STANCE_MASTERY_POINTS', 149,
    'Stance Mastery 12678: effect base points (x10 = 1,500 retained rage, above any max rage) [fixed].',
    cpp_type='int32')


# =====================================================================================================================
# Stances (D9; shared doc "Stances", "Battle Stance", "Berserker Stance", "Defensive Stance")
# =====================================================================================================================
# Pulled out of npc.csv with pull_dsl.py (71, 2457, 2458, 7381). Only the named fields differ from the pulled rows:
# Battle Stance's second effect, the three tooltips and aura texts, Berserker Stance's learn level. The shapeshift
# effects (aura 36), stance bar order, Category 47 / 1 s swap cooldown, off-the-GCD attributes and the stock threat auras
# (21156 / 7381 -20%, 7376 +45% + linked 57339) are untouched. The tooltips are the shared doc verbatim; their numbers
# are the stock-fixed effect values (Battle's 10% is aura 213's 9 + 1), pinned by the W0a tests.
# No ability needs a stance any more: the abilities' ShapeshiftMask is zeroed in warrior_spells.py (D9).
defensive_stance_71 = spell(
    id=71,
    name='Defensive Stance',
    school=1,
    attributes=688193552,
    category=47,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1000,
    power_type=1,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=6, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=18),
    ],
    spell_icon_id=276,
    notes='pulled from existing data; W0a A2: tooltip and aura text from the shared doc (D9), nothing else changed',
    raw_overrides={'AttributesEx': 268436480, 'AttributesEx3': 1048576, 'AttributesEx4': 2097152, 'AttributesEx6': 4096, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 10, 'SpellLevel': 10, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 44, 'ActiveIconID': 276, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'A defensive combat stance. Decreases damage taken by 10% and damage dealt by 5%. You are immune to critical strikes from melee and ranged attacks, and you generate more threat.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced. Damage dealt reduced. Immune to critical strikes from melee and ranged attacks. Threat generated increased.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 4, 'SpellClassMask_1': 8388608, 'StanceBarOrder': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# Battle Stance: effect 2 was aura 280 MOD_ARMOR_PENETRATION_PCT (bp 9 = +10% armor penetration, dropped, shared doc
# section 8); it is now aura 213 MOD_RAGE_FROM_DAMAGE_DEALT, bp 9 + die 1 = +10 (AddPct), read only on the white-swing
# attacker path of Warrior::RewardRage / Unit::RewardRage, so "auto attacks only" holds (D9).
battle_stance_2457 = spell(
    id=2457,
    name='Battle Stance',
    school=1,
    attributes=696582160,
    category=47,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1000,
    power_type=1,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=6, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=17),
        Effect(type=6, base_points=9, implicit_target_a=1, apply_aura=213),
    ],
    spell_icon_id=279,
    notes='pulled from existing data; W0a A2 (D9): eff1 aura 280 armor penetration -> aura 213 MOD_RAGE_FROM_DAMAGE_DEALT '
          '+10% (stored 9, die 1), tooltip and aura text from the shared doc',
    raw_overrides={'AttributesEx': 2415920128, 'AttributesEx2': 1, 'AttributesEx3': 1048576, 'AttributesEx4': 2097152, 'AttributesEx6': 4096, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 4052, 'ActiveIconID': 279, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'A balanced combat stance. Your auto attacks generate 10% more rage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Auto attacks generate more rage.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 4, 'SpellClassMask_1': 8388608, 'SpellClassMask_2': 8388608, 'DefenseType': 2, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# Berserker Stance: trained at level 16 (was 30); BaseLevel = SpellLevel = 16 so the trainer-level lint passes (A3 moves
# the trainer rows).
berserker_stance_2458 = spell(
    id=2458,
    name='Berserker Stance',
    school=1,
    attributes=688193552,
    category=47,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1000,
    power_type=1,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=6, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=19),
    ],
    spell_icon_id=84,
    notes='pulled from existing data; W0a A2 (D3/D9): BaseLevel = SpellLevel 30 -> 16, tooltip and aura text from the '
          'shared doc (the crit / damage-taken numbers live on 7381)',
    raw_overrides={'AttributesEx': 268436480, 'AttributesEx2': 1, 'AttributesEx3': 1048576, 'AttributesEx4': 2097152, 'AttributesEx6': 4096, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 16, 'SpellLevel': 16, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 4053, 'ActiveIconID': 84, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'An aggressive stance. Increases your melee critical strike chance by 3%, but you take 5% more damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee critical strike chance increased. Damage taken increased.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 4, 'SpellClassMask_1': 8388608, 'DefenseType': 2, 'PreventionType': 2, 'StanceBarOrder': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# Berserker Stance Passive: unchanged (+3% crit, +5% damage taken, -20% threat). Only here so the pull is complete;
# the doc's aura text lives on the stance itself, which is the visible buff.
berserker_stance_passive_7381 = spell(
    id=7381,
    name='Berserker Stance Passive',
    school=1,
    attributes=327888,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=1,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=6, base_points=2, implicit_target_a=1, apply_aura=52),
        Effect(type=6, base_points=4, implicit_target_a=1, apply_aura=87, misc_value=127),
        Effect(type=6, base_points=-21, implicit_target_a=1, apply_aura=10, misc_value=127),
    ],
    spell_icon_id=84,
    notes='pulled from existing data; W0a A2: unchanged',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 30, 'SpellLevel': 30, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Increases crit chance by $s1%.\r\nIncreases all damage taken by $s2%.\r\nDecreases threat generated by $s3%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 4, 'SpellClassMask_2': 2048, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# =====================================================================================================================
# Quest spell 8616 (D22; shared doc section 8 "Intercept")
# =====================================================================================================================
# The Affray (quest 1719) reward. It taught Berserker Stance and Intercept; Intercept is removed, so only the stance
# remains. The quest row is untouched (SQL elsewhere).
path_of_the_berserker_8616 = spell(
    id=8616,
    name='Path of the Berserker',
    school=1,
    attributes=65792,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=36, die_sides=0, trigger_spell=2458),
    ],
    spell_icon_id=1,
    notes='pulled from existing data; W0a A2 (D22): effect 2 (learn Intercept 20252) and the Intercept sentence dropped',
    raw_overrides={'Targets': 256, 'CastingTimeIndex': 14, 'InterruptFlags': 15, 'ProcChance': 101, 'DurationIndex': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 3639, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teaches Berserker Stance (Rank 1).', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# =====================================================================================================================
# Stance Mastery auto-learn (D10). The spell itself (12678) is in warrior_trigger_spells.py.
# =====================================================================================================================
# Stock SkillLineAbility 15513: Stance Mastery on skill 257 (Protection), acquire method 0 (talent-taught, trainer 1
# only). Skill 26 (Arms) acquire 2 (LEARNED_ON_SKILL_LEARN) makes Player::_LoadSkills -> learnSkillRewardedSpells teach
# it at creation and at every login, bots included. No characters SQL.
override_skill_line_ability(15513, skill_line=26, acquire_method=2)  # Stance Mastery: every warrior knows it
