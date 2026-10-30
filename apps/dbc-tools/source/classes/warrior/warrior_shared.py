"""
Warrior - W0a/W0b shared foundations, data half: the rage-model script numbers and the W0b leap/Charge numbers
(`const()`s the C++ reads through the generated WarriorData.h), the three stances pulled out of npc.csv, Stance
Mastery's value, quest spell 8616, and the W0b shared spells 204400-204409 (further down).

Source of truth: docs/reworks/warrior-shared-rework.md ("Stances", "Rage generation"),
.agents/plans/warrior-rework/warrior-rework.W0a-HANDOFF.md (D9, D10, D12-D14, Known-hard 1 and 2) and
warrior-rework.W0a-WP-BRIEF.md (variable names).

Rage model (D12/D13): one table keyed on level, the level-60 bracket applies at every level until 70/80 open. Dealt rage
per white hit is (k * 7.5 * damage / c + speed) / 2, capped at the stock 15 * damage / c, where the speed part is the
hasted swing time * the spell-haste factor max(1, 1 / cast speed) (W0b D21) * 3.5 * m (main hand) or * 0.875 (off hand).
k 0.43 and m 1.35 are the W0a rage sweep's picks.
"""

from lib.dsl import AuraType, Effect, EffectType, PowerType, RANGE_SELF, School
from lib.dsl.registry import (
    const,
    custom_attr,
    override_skill_line_ability,
    pot_text,
    procs_on,
    scripted_by,
    skill_line_ability,
    spell,
    spell_group,
    spell_group_rule,
)

from . import _masks


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

# --- W0b (D31) ---
HEROIC_LEAP_AIR_MS = const(
    'HEROIC_LEAP_AIR_MS', 1000,
    'Heroic Leap: air time of the leap in milliseconds, whatever the distance (P0 proven shape) [tune].',
    cpp_type='uint32')
HEROIC_LEAP_APEX_YD = const(
    'HEROIC_LEAP_APEX_YD', 5.0,
    'Heroic Leap: apex height of the jump arc in yards (MoveJump speedZ = sqrt(2 g apex)) [tune].')
CHARGE_COMBAT_MIN_YD = const(
    'CHARGE_COMBAT_MIN_YD', 8.0,
    'Charge in combat: the distance at which the in-combat rage is lowest (5 rage), the spell minimum range [fixed].')
CHARGE_COMBAT_MAX_YD = const(
    'CHARGE_COMBAT_MAX_YD', 25.0,
    'Charge in combat: the distance at which the in-combat rage is highest (10 rage), the spell maximum range [fixed].')


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


# =====================================================================================================================
# W0b: the shared kit's new spells (D3, D9, D12-D14, D30). Overpower charges, Heroic Leap, Skull Banner, Victory Rush's
# heal. Spells 204400-204409, SLA 30840-30842, spell_group 1296; the two banner creatures are in
# source/npcs/warrior_npcs.py (a class package is also loaded without creature columns, where creature_template()
# raises). Tooltips and aura texts are the shared doc (docs/reworks/warrior-shared-rework.md) verbatim.
# Shapes proven by the P0 spike (.agents/plans/warrior-rework/P0-RESULTS.md items 1, 3, 4).
# =====================================================================================================================
SPELLFAMILY_WARRIOR = 4

SPELL_ATTR0_PASSIVE = 0x40
SPELL_ATTR0_DO_NOT_DISPLAY = 0x80
SPELL_ATTR0_NO_IMMUNITIES = 0x20000000           # immunities neither block nor purge the aura
SPELL_ATTR0_NO_AURA_CANCEL = 0x80000000          # the player cannot right-click the aura off
ABILITY_ATTRIBUTES = 0x50010                     # stock warrior buttons (52174, 12294, ...)
HIDDEN_PASSIVE = SPELL_ATTR0_PASSIVE | SPELL_ATTR0_DO_NOT_DISPLAY
SPELL_ATTR3_ALLOW_AURA_WHILE_DEAD = 0x100000     # the aura persists through death
SPELL_ATTR0_CU_NEGATIVE_EFF0 = 0x1000            # SpellInfo.h (hunter 201810 precedent)
SPELL_ATTR0_CU_AURA_CANNOT_BE_SAVED = 0x1000000  # SpellInfo.h

AURA_SAFE_FALL = 144
MECHANIC_ROOT = 7

TARGET_UNIT_CASTER = 1
TARGET_UNIT_DEST_AREA_ENEMY = 16
TARGET_DEST_DYNOBJ_ENEMY = 28      # the ground cursor (rogue P0b/P0c ruling)
TARGET_DEST_CASTER_FRONT = 47      # stock 23034 Battle Standard's summon point
TARGET_UNIT_CASTER_AREA_RAID = 56
TARGET_DEST_DEST = 87

DMG_CLASS_MELEE = 2
PREVENTION_TYPE_PACIFY = 2
TARGET_FLAG_DEST_LOCATION = 0x40

# Existing index rows only (0-verify item 4); no secondary row minted.
RANGE_INDEX_8_40 = 94              # "Sting", 8-40 yd
SCRIPT_CAST_RANGE = 50000.0        # bug log: a script-cast spell beyond melee range needs the 50000 yd row
RADIUS_INDEX_1 = 16                # 1 yd (stock 23034 eff0)
RADIUS_INDEX_8 = 14                # 8 yd
RADIUS_INDEX_40 = 23               # 40 yd
DURATION_3S, DURATION_20S, DURATION_2MIN, DURATION_INFINITE = 27, 18, 4, 21

SUMMON_PROPERTIES_BATTLE_STANDARD = 121   # stock 23034's miscB
NPC_SKULL_BANNER_ALLIANCE_ENTRY = 300370  # source/npcs/warrior_npcs.py
NPC_SKULL_BANNER_HORDE_ENTRY = 300371

ICON_OVERPOWER = 26
ICON_HEROIC_LEAP, SV_HEROIC_LEAP, SV_HEROIC_LEAP_SLAM = 3149, 29, 11441
ICON_BATTLE_STANDARD, SV_BATTLE_STANDARD = 1691, 6801
ICON_VICTORY_RUSH = 2053

HEROIC_LEAP_LEVEL = 38
SKULL_BANNER_LEVEL = 60


def _raw(description, aura_description=None, level=None, **extra):
    """Per-spell defaults of the shared kit plus `extra` raw columns (applied last): family 4, no equipment
    requirement, instant cast, chain amplitudes 1.0 (a 0 makes a second target take no damage), `level` sets
    BaseLevel and SpellLevel together (the trainer-level lint and the potency anchor)."""
    raw = {
        'SpellClassSet': SPELLFAMILY_WARRIOR,
        'EquippedItemClass': -1,
        'CastingTimeIndex': 1,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'Description_Lang_enUS': description,
    }
    if level is not None:
        raw['BaseLevel'] = level
        raw['SpellLevel'] = level
    if aura_description is not None:
        raw['AuraDescription_Lang_enUS'] = aura_description
    raw.update(extra)
    return raw


def _w0b(spell_id, name, effects, icon, notes, raw, *, attributes=0, rage=0, range_yards=None, cooldown_ms=0):
    """Every W0b spell: physical, instant, rage, no category; durations, ranges and radii as raw indices."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=attributes, category=0, cast_time_ms=0,
        cooldown_ms=cooldown_ms, category_cooldown_ms=0, power_type=PowerType.RAGE, mana_cost=rage * 10,
        mana_cost_pct=0, range_yards=range_yards, effects=effects, spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _self_aura(aura, **kwargs):
    return Effect(type=EffectType.APPLY_AURA, apply_aura=aura, implicit_target_a=TARGET_UNIT_CASTER, **kwargs)


# --- Overpower charges (D2, D3): a parry grants a visible stack, Overpower needs one (CasterAuraSpell on 7384), each
# cast spends exactly one (USE_STACKS_FOR_CHARGES) ---
overpower_204403 = _w0b(
    204403, 'Overpower',
    [_self_aura(AuraType.DUMMY)],
    ICON_OVERPOWER,
    'W0b D3: the Overpower charge. Visible self aura, not passive, CumulativeAura 5, 20 s, eff0 DUMMY. Added (one '
    'stack per parry) by 204404\'s proc; its spell_proc row spends one stack per Overpower cast (Overpower\'s own '
    'family bit d0 0x4, CAST phase, USE_STACKS_FOR_CHARGES, Charges 0: with 1 the aura would use charges and stop '
    'proccing at 0). 7384 needs it through CasterAuraSpell.',
    _raw('Overpower is usable.', 'Overpower is usable.', CumulativeAura=5, DurationIndex=DURATION_20S),
    range_yards=RANGE_SELF,
)
procs_on(overpower_204403, proc_flags=0x10, family_name=SPELLFAMILY_WARRIOR, family_mask=(0x4, 0, 0),
         spell_phase_mask=0x1, attributes_mask=0x10, chance=100, charges=0)

overpower_training_204404 = _w0b(
    204404, 'Overpower Training',
    [_self_aura(AuraType.PROC_TRIGGER_SPELL, trigger_spell=204403)],
    ICON_OVERPOWER,
    'W0b D2/D3: hidden passive every warrior knows (SkillLineAbility 30842, skill 26, acquire method 2). eff0 '
    'PROC_TRIGGER_SPELL -> 204403 on TAKEN melee / ranged hits that the warrior parries (DBC ProcTypeMask 0x2A8, '
    'spell_proc HitMask PROC_HIT_PARRY 0x20, SpellPhaseMask 0 on a TAKEN-only row: the warrior\'s own hits never '
    'feed it).',
    _raw('Parrying an attack grants an Overpower charge.', ProcTypeMask=0x2A8, ProcChance=100,
         DurationIndex=DURATION_INFINITE),
    attributes=HIDDEN_PASSIVE, range_yards=RANGE_SELF,
)
procs_on(overpower_training_204404, proc_flags=0x2A8, hit_mask=0x20, spell_phase_mask=0, chance=100)

# --- Heroic Leap (D9): the ground-targeted button, the flight aura and the landing slam. The landing is declared first:
# the button's tooltip quotes its damage with pot_text(). ---
heroic_leap_204401 = _w0b(
    204401, 'Heroic Leap',
    [Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=117.0, potency_kind='direct',
            implicit_target_a=TARGET_DEST_DEST, implicit_target_b=TARGET_UNIT_DEST_AREA_ENEMY)],
    ICON_HEROIC_LEAP,
    'W0b D9: the landing slam, cast triggered by spell_warr_heroic_leap at the landing point: physical SCHOOL_DAMAGE '
    '117 AP potency at A 87 / B 16, EffectRadiusIndex 14 (8 yd), 50000 yd (script-cast, bug log), DmgClass melee, '
    'Heroic Leap family bit d2 b0, the landing visual 11441. SpellLevel 38. No stun. Not 0x80 (read in the combat '
    'log).',
    _raw('Slams down on landing, dealing {pot1} Physical damage to all enemies within 8 yards.',
         level=HEROIC_LEAP_LEVEL,
         DefenseType=DMG_CLASS_MELEE, PreventionType=PREVENTION_TYPE_PACIFY, EffectRadiusIndex_1=RADIUS_INDEX_8,
         SpellClassMask_3=_masks.HEROIC_LEAP, SpellVisualID_1=SV_HEROIC_LEAP_SLAM, DurationIndex=DURATION_INFINITE),
    attributes=ABILITY_ATTRIBUTES, range_yards=SCRIPT_CAST_RANGE,
)

heroic_leap_204400 = _w0b(
    204400, 'Heroic Leap',
    [Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_DEST_DYNOBJ_ENEMY)],
    ICON_HEROIC_LEAP,
    'W0b D9: the button. Ground cursor (Targets 0x40, eff0 DUMMY at A 28), RangeIndex 94 (8-40 yd), off the GCD, no '
    'cost, 60 s cooldown, no category, DmgClass melee (the button\'s own cast raises one cast-phase proc event), line '
    'of sight kept (6544\'s ignore-LoS bit not copied), Heroic Leap family bit d2 b0, SpellLevel 38. '
    'spell_warr_heroic_leap: rooted / charging / already leaping / unwalkable-point refusals, the 204402 flight aura, '
    'the MoveJump and the 204401 landing.',
    _raw('Leap through the air toward a target location, slamming down and dealing ' + pot_text(heroic_leap_204401, 1)
         + ' Physical damage to all enemies within 8 yards.', level=HEROIC_LEAP_LEVEL, DefenseType=DMG_CLASS_MELEE,
         Targets=TARGET_FLAG_DEST_LOCATION, RangeIndex=RANGE_INDEX_8_40, SpellClassMask_3=_masks.HEROIC_LEAP,
         SpellVisualID_1=SV_HEROIC_LEAP, DurationIndex=DURATION_INFINITE),
    attributes=ABILITY_ATTRIBUTES, cooldown_ms=60000,
)
scripted_by(heroic_leap_204400, 'spell_warr_heroic_leap')

leaping_204402 = _w0b(
    204402, 'Leaping',
    [_self_aura(AuraType.MECHANIC_IMMUNITY, misc_value=MECHANIC_ROOT),
     _self_aura(AURA_SAFE_FALL, base_points=99)],
    ICON_HEROIC_LEAP,
    'W0b D9: the flight aura, added at launch and removed at landing by spell_warr_heroic_leap (3 s cap): '
    'MECHANIC_IMMUNITY (77) to roots, SAFE_FALL (144). Charge and Intervene refuse while it is up. '
    'CU_AURA_CANNOT_BE_SAVED: it never survives a relog. Hidden (shared doc "Shows a buff: no", user 2026-10-29) and '
    'not cancellable (harness review R2: a cancel mid-air would reopen Charge/Intervene during the jump).',
    _raw('You are in the air.', 'Leaping. Immune to roots and falling damage.', DurationIndex=DURATION_3S),
    attributes=SPELL_ATTR0_DO_NOT_DISPLAY | SPELL_ATTR0_NO_AURA_CANCEL, range_yards=RANGE_SELF,
)
custom_attr(leaping_204402, SPELL_ATTR0_CU_AURA_CANNOT_BE_SAVED)

# --- Skull Banner (D12, D13): the button summons the per-faction banner and buffs the party; Rallied is the lockout ---
skull_banner_204405 = _w0b(
    204405, 'Skull Banner',
    [Effect(type=EffectType.SUMMON, base_points=1499, implicit_target_a=TARGET_DEST_CASTER_FRONT,
            misc_value=NPC_SKULL_BANNER_ALLIANCE_ENTRY),
     Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER_AREA_RAID)],
    ICON_BATTLE_STANDARD,
    'W0b D13: instant, off the GCD, cost 0, 3 min cooldown, 20 s. eff0 = stock 23034 Battle Standard\'s eff0 (SUMMON '
    'base 1499, A 47, EffectRadiusIndex 16, miscB SummonProperties 121) with misc 300370 (the Alliance banner; a '
    'Horde caster gets 204408 instead, the script drops this summon). eff1 DUMMY at A 56 with EffectRadiusIndex 23 '
    '(40 yd, the Bloodlust shape): spell_warr_skull_banner drops non-players and anyone with Rallied or the buff, '
    'then AddAuras 204406 and 204407 on each hit target.',
    _raw('Plant a Skull Banner, increasing the critical strike chance of all party and raid members within 40 yards by '
         '10% for 20 sec. Allies who benefit cannot benefit from another Skull Banner for 2 min.',
         level=SKULL_BANNER_LEVEL, EffectRadiusIndex_1=RADIUS_INDEX_1,
         EffectMiscValueB_1=SUMMON_PROPERTIES_BATTLE_STANDARD, EffectRadiusIndex_2=RADIUS_INDEX_40,
         SpellVisualID_1=SV_BATTLE_STANDARD, DurationIndex=DURATION_20S),
    range_yards=RANGE_SELF, cooldown_ms=180000,
)
scripted_by(skull_banner_204405, 'spell_warr_skull_banner')

skull_banner_204406 = _w0b(
    204406, 'Skull Banner',
    [_self_aura(AuraType.MOD_CRIT_PCT, base_points=9)],
    ICON_BATTLE_STANDARD,
    'W0b D13: the buff, AddAura\'d by 204405\'s script (bug 1067: never a CastSpell whose implicit target is the '
    'caster): MOD_CRIT_PCT (290) base 9 = +10% melee / ranged / spell crit, 20 s. spell_group 1296 rule 1: one copy '
    'whoever casts it.',
    _raw('Critical strike chance increased by 10%.', 'Critical strike chance increased.',
         DurationIndex=DURATION_20S),
    range_yards=RANGE_SELF,
)
spell_group(1296, skull_banner_204406)
spell_group_rule(1296, stack_rule=1, description='Skull Banner')

rallied_204407 = _w0b(
    204407, 'Rallied',
    [_self_aura(AuraType.DUMMY)],
    ICON_BATTLE_STANDARD,
    'W0b D13: the 2 min lockout debuff AddAura\'d by 204405\'s script on everyone it buffed: DUMMY, persists through '
    'death (AttributesEx3 0x100000), shown as a debuff through spell_custom_attr SPELL_ATTR0_CU_NEGATIVE_EFF0 (hunter '
    '201810 precedent), saved across logout. Every Skull Banner skips a Rallied player. NO_IMMUNITIES (harness review '
    'R1): Divine Shield / Hand of Protection / Ice Block neither purge it nor stop it landing.',
    _raw('You cannot benefit from Skull Banner.', 'Cannot benefit from Skull Banner.',
         AttributesEx3=SPELL_ATTR3_ALLOW_AURA_WHILE_DEAD, DurationIndex=DURATION_2MIN),
    attributes=SPELL_ATTR0_NO_IMMUNITIES, range_yards=RANGE_SELF,
)
custom_attr(rallied_204407, SPELL_ATTR0_CU_NEGATIVE_EFF0)

skull_banner_204408 = _w0b(
    204408, 'Skull Banner',
    [Effect(type=EffectType.SUMMON, base_points=1499, implicit_target_a=TARGET_DEST_CASTER_FRONT,
            misc_value=NPC_SKULL_BANNER_HORDE_ENTRY)],
    ICON_BATTLE_STANDARD,
    'W0b D12: the Horde banner helper, cast triggered by spell_warr_skull_banner for a Horde caster in place of '
    '204405\'s own summon: the same SUMMON (base 1499, A 47, EffectRadiusIndex 16, miscB 121, 20 s) with misc '
    '300371. Hidden (0x80), no spellbook row.',
    _raw('Plants a Horde Skull Banner.', EffectRadiusIndex_1=RADIUS_INDEX_1,
         EffectMiscValueB_1=SUMMON_PROPERTIES_BATTLE_STANDARD, SpellVisualID_1=SV_BATTLE_STANDARD,
         DurationIndex=DURATION_20S),
    attributes=SPELL_ATTR0_DO_NOT_DISPLAY, range_yards=RANGE_SELF,
)

# --- Victory Rush's heal (D14): a helper, because an eff1 HEAL_PCT at A 1 on 34428 would make the caster a second
# target of its own cast and run the full hit / proc pipeline on the caster (bug log "self-targeted effect") ---
victory_rush_204409 = _w0b(
    204409, 'Victory Rush',
    [Effect(type=EffectType.HEAL_PCT, base_points=19, implicit_target_a=TARGET_UNIT_CASTER)],
    ICON_VICTORY_RUSH,
    'W0b D14: the 20% heal, cast triggered on the caster by spell_warr_victory_rush_heal (AfterCast on 34428), once '
    'per cast. HEAL_PCT base 19 (+1) at A 1, self range, no spellbook row (no SkillLineAbility), no 0x80 so the heal '
    'shows in the combat log. 34428\'s tooltip reads it as $204409s1%.',
    _raw('Heals you for $s1% of your maximum health.'),
    attributes=ABILITY_ATTRIBUTES, range_yards=RANGE_SELF,
)

# =====================================================================================================================
# Spellbook tabs (D16, D18; brief ruling 5) and script bindings for stock ids (brief ruling 8; A1 owns the matching
# unbinds in warrior_spells.py)
# =====================================================================================================================
# 6544 (the client's own Heroic Leap) has no stock SkillLineAbility row; Battle Shout's tab is Fury (256), not Arms.
skill_line_ability(id=30840, skill_line=26, spell_id=204400, class_mask=1)    # Heroic Leap: Arms tab
skill_line_ability(id=30841, skill_line=256, spell_id=204405, class_mask=1)   # Skull Banner: Fury tab (Battle Shout)
skill_line_ability(id=30842, skill_line=26, spell_id=204404, class_mask=1, acquire_method=2)  # Overpower Training
# Victorious State 32215 (stock SLA 15058, skill 95 Defense, acquire 2): every warrior knows it from creation.
override_skill_line_ability(15058, skill_line=26, acquire_method=2)

scripted_by(-100, 'spell_warr_charge_rework')            # Charge and its rank chain (stock script unbound in A1's file)
scripted_by(3411, 'spell_warr_intervene_rework')         # Intervene (stock script unbound in A1's file)
scripted_by(34428, 'spell_warr_victory_rush_heal')       # in addition to the stock spell_warr_victory_rush
