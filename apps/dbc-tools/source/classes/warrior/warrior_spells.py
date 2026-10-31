"""
Warrior - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/warrior.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .warrior_...` below) resolve.
"""

from lib.dsl import AuraType, Effect, EffectType, Mechanic, PowerType, School
from lib.dsl.registry import leave_spell_group, product, remove_spell_proc, spell, talent_mult, tooltip_vars, unbind_script

from . import _masks


# ----------------------------------------------------------------------------------------------------------
# warrior-rework S1 D26 - talent bonuses on Protection spell tooltips (SpellDescriptionVariables, Warrior
# Protection block 1420-1424 of ids.yaml). A SpellMod never moves a tooltip, so each unconditional percent
# talent is folded in here with talent_mult (reads the rank spell's own value, so a retune follows). Shield
# Slam (1423) is skipped on purpose: Gag Order is an EFFECT2 mod that scales only the base value, so a
# {pot2*mult} would overstate it. Conditional bonuses (Empowered Revenge, Sword and Board, Tempered) stay on
# the talent tooltips.
# ----------------------------------------------------------------------------------------------------------
revenge_tooltip = tooltip_vars(
    1420, "Prot talent multiplier for Revenge: Improved Revenge (eff1 DAMAGE +15/30%)",
    ir=talent_mult([12797, 12799]),
)
devastate_tooltip = tooltip_vars(
    1421, "Prot talent multiplier for Devastate: Puncture (eff1 DAMAGE +5/10/15%, whole hit: weapon % and flat)",
    pun=talent_mult([12308, 12810, 12811]),
)
thunder_clap_tooltip = tooltip_vars(
    1422, "Prot talent multiplier for Thunder Clap: Improved Thunder Clap (eff2 DAMAGE) x Thunderstruck (eff1 DAMAGE)",
    itc=talent_mult([12287, 12665, 12666], effect=2),
    ts=talent_mult([200051, 200052, 200053]),
    mult=product("itc", "ts"),
)
shockwave_tooltip = tooltip_vars(
    1424, "Prot talent multiplier for Shockwave: Thunderstruck (eff1 DAMAGE +10/20/30%)",
    ts=talent_mult([200051, 200052, 200053]),
)


# ----------------------------------------------------------------------------------------------------------
# warrior-rework S2 D27 - talent bonuses on Arms spell tooltips (SpellDescriptionVariables 1385-1388). Same rule
# as above: each unconditional percent talent is folded in with talent_mult. Conditional bonuses (Momentum,
# Strength of Arms, Wrecking Crew, Exploiter, Colossus Smash) stay on the talent tooltips.
# ----------------------------------------------------------------------------------------------------------
heavy_blows_tooltip = tooltip_vars(
    1385, "Arms talent multiplier for Heavy Blows (eff1 DAMAGE +5/10/15%, whole hit); S3 moved Heroic Strike and Slam to 1405/1406, kept defined",
    hb=talent_mult([12282, 12663, 12664]),
)
battlelord_tooltip = tooltip_vars(
    1386, "Arms talent multiplier for Overpower: Battlelord (eff1 DAMAGE +10/20%, whole hit)",
    bl=talent_mult([204533, 204534]),
)
improved_mortal_strike_tooltip = tooltip_vars(
    1387, "Arms talent multiplier for Mortal Strike: Improved Mortal Strike (eff1 DAMAGE +5/10%, damage only)",
    ims=talent_mult([35446, 35448]),
)
improved_rend_tooltip = tooltip_vars(
    1388, "Arms talent multiplier for Rend: Improved Rend (eff1 DOT +10/20/30%)",
    ir=talent_mult([12286, 12658, 204540]),
)


# ----------------------------------------------------------------------------------------------------------
# warrior-rework S3 D37 - talent bonuses on Fury spell tooltips (SpellDescriptionVariables 1405-1409, Fury block of
# ids.yaml). One spell has one SDV id, so Heroic Strike and Slam leave S2's 1385 (Heavy Blows only) for rows that repeat
# Heavy Blows and add the Fury talents; 1385 stays defined. Only the unconditional percent talents are folded in
# (DAMAGE pct mods multiply, Player.cpp:10127-10131); the conditional ones (Enrage, Merciless, Improved Execute,
# Bloodsurge, Blood Rush) stay on the talent tooltips. Unending Fury carries the same value on both of its effects:
# e1 for Heroic Strike | Slam | Cleave (d0), e2 for Bloodthirst | Whirlwind (d1).
# ----------------------------------------------------------------------------------------------------------
heroic_strike_tooltip = tooltip_vars(
    1405, "Fury talent multiplier for Heroic Strike: Heavy Blows (+5/10/15%) x Frenzied Blows (+5/10%) x Unending Fury "
          "(+5/10/15%), all eff1 DAMAGE on the whole hit",
    hb=talent_mult([12282, 12663, 12664]),
    fb=talent_mult([204659, 204660]),
    uf=talent_mult([56927, 56929, 56930]),
    mult=product("hb", "fb", "uf"),
)
slam_tooltip = tooltip_vars(
    1406, "Fury talent multiplier for Slam: Heavy Blows (+5/10/15%) x Unending Fury (+5/10/15%), eff1 DAMAGE",
    hb=talent_mult([12282, 12663, 12664]),
    uf=talent_mult([56927, 56929, 56930]),
    mult=product("hb", "uf"),
)
cleave_tooltip = tooltip_vars(
    1407, "Fury talent multiplier for Cleave: Improved Cleave (+5/10/15%) x Frenzied Blows (+5/10%) x Unending Fury "
          "(+5/10/15%), all eff1 DAMAGE",
    ic=talent_mult([12329, 12950, 20496]),
    fb=talent_mult([204659, 204660]),
    uf=talent_mult([56927, 56929, 56930]),
    mult=product("ic", "fb", "uf"),
)
bloodthirst_tooltip = tooltip_vars(
    1408, "Fury talent multiplier for Bloodthirst: Unending Fury (+5/10/15%, the eff2 DAMAGE on d1 0x404)",
    uf=talent_mult([56927, 56929, 56930], effect=2),
)
whirlwind_tooltip = tooltip_vars(
    1409, "Fury talent multiplier for Whirlwind: Improved Whirlwind (+3/6%, eff1 DAMAGE) x Unending Fury "
          "(+5/10/15%, eff2 DAMAGE)",
    iw=talent_mult([29721, 29776]),
    uf=talent_mult([56927, 56929, 56930], effect=2),
    mult=product("iw", "uf"),
)


shield_bash_72 = spell(
    id=72,
    name='Shield Bash',
    school=School.NORMAL,
    attributes=327696,
    category=88,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=12000,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.INTERRUPT_CAST, base_points=-1, mechanic=26, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=6, trigger_spell=29703),
    ],
    spell_icon_id=280,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 8, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Bash the target with your shield dazing them and interrupting spellcasting, which prevents any spell in that school from being cast for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 0, 'SpellClassMask_1': 2048, 'SpellClassSet': 4, 'SpellLevel': 12, 'SpellPriority': 50, 'SpellVisualID_1': 42},
)


heroic_strike_78 = spell(
    id=78,
    name='Heroic Strike',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=183, implicit_target_a=6),
        Effect(type=EffectType.WEAPON_DAMAGE, sp_potency=12, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=6),
    ],
    tooltip_vars=heroic_strike_tooltip,
    spell_icon_id=856,
    notes=(
        'warrior-rework W0a A1 (shared doc "Heroic Strike", HANDOFF D4/D5/D3): an instant strike on the GCD. Stock '
        'Attributes 0x50014 -> 0x50010 (ON_NEXT_SWING 0x4 cleared: the whole server change, Spell::IsNextMeleeSwingSpell '
        'reads only that bit), StartRecovery 0/0 -> 133/1500. Potency layout (EffectWeaponDmg applies the effects in '
        'index order, so the percent comes first): eff0 WEAPON_PERCENT_DAMAGE weapon_potency 150 (D4: stock-anchored, '
        'the mean of the 2.6 s one-hander and 3.6 s two-hander reference weapons), eff1 WEAPON_DAMAGE sp_potency 10 '
        'direct T 1500 (the flat part; the rogue Sinister Strike 1752 shape on the stock type-58 carrier). SpellLevel 1. '
        'Stale single-rank bootstrap keys (BaseLevel, MaxLevel, EffectBonusMultiplier_1, the per-level flat) dropped. '
        'Family bit d0 b6 and every other stock column kept. warrior-rework S2 D27: the damage read Heavy Blows '
        '(tooltip_vars 1385); S3 D37 moves it to 1405 (Heavy Blows x Frenzied Blows x Unending Fury, token $<mult>).'
    ),
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'An instant strike that deals ${$m1*$<mult>}% weapon damage plus {pot2.avg*mult}.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 64, 'SpellClassMask_3': _masks.DAMAGING_ABILITY_GROUP, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 39, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


charge_100 = spell(
    id=100,
    name='Charge',
    school=School.NORMAL,
    attributes=537198608,
    category=1219,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=15000,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=25.0,
    effects=[
        Effect(type=96, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, base_points=89, points_per_level=1.0714285714285714, implicit_target_a=1, radius_yards=0.0),
        Effect(type=EffectType.TRIGGER_SPELL, points_per_level=-0.017857142857142856, die_sides=0, implicit_target_a=6, trigger_spell=7922),
    ],
    spell_icon_id=457,
    notes='warrior-rework W0b D5: Attributes 0x30050010 -> 0x20050010 (NOT_IN_COMBAT_ONLY_PEACEFUL cleared, usable in combat), tooltip from the shared doc; pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx6': 8388608, 'AttributesEx7': 262144, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 4, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Charge an enemy, stunning it briefly. Out of combat you generate $/10;s2 rage; in combat you generate 5 to 10 rage, more the farther you charge. Usable in combat.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectRadiusIndex_2': 36, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 65219, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 95, 'ShapeshiftMask': 0, 'SpellClassMask_1': 1, 'SpellClassSet': 4, 'SpellLevel': 4, 'SpellPriority': 50, 'SpellVisualID_1': 867, 'StartRecoveryCategory': 1178},
)


commanding_shout_469 = spell(
    id=469,
    name='Commanding Shout',
    school=School.NORMAL,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=112, points_per_level=4.8422, implicit_target_a=56, apply_aura=230, radius_yards=30.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=2, radius_yards=30.0),
    ],
    spell_icon_id=1934,
    notes=(
        'warrior-rework W0a A1 (shared doc "Commanding Shout", HANDOFF D18): learned at 22 with a level curve that follows '
        'Battle Shout 6673\'s slope instead of the stock flat 1,080 at every level below 68. BaseLevel = SpellLevel = 22, '
        'MaxLevel 60 (frozen until the 70/80 brackets open), base 112 + 4.8422 per level: 113 at 22, ~200 at 40, 297 at 60 '
        '(the 297 is the stock row\'s own slope extrapolated to 60, an M placeholder; Battle Shout builds 157 at 22 and '
        '414 at 60, so V(L) = 297 x BS(L) / BS(60)). warrior-rework S3 D30: new e1 aura 29 MOD_STAT misc 2 (Stamina), same '
        'target and radius as e0; spell_warr_commanding_presence (DoEffectCalcAmount on e1) sets its amount from the '
        'caster\'s Commanding Presence rank.'
    ),
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Maximum health increased. Stamina increased.', 'BaseLevel': 22, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the maximum health of all party and raid members within $a1 yards by an amount that scales with level, $s1 at your level, for $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 60, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 128, 'SpellClassSet': 4, 'SpellLevel': 22, 'SpellVisualID_1': 246, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


disarm_676 = spell(
    id=676,
    name='Disarm',
    school=School.NORMAL,
    mechanic=3,
    attributes=327696,
    category=109,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_DISARM),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=278),
    ],
    spell_icon_id=560,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx4': 536872960, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Disarmed!', 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Disarm the enemy's main hand and ranged weapons for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 0, 'SpellClassMask_1': 512, 'SpellClassSet': 4, 'SpellLevel': 18, 'SpellPriority': 50, 'SpellVisualID_1': 398, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mocking_blow_694 = spell(
    id=694,
    name='Mocking Blow',
    school=School.NORMAL,
    attributes=327696,
    category=40,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=6000,
    effects=[
        Effect(type=121, base_points=-1, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_TAUNT),
        Effect(type=114, base_points=-1, implicit_target_a=6),
    ],
    spell_icon_id=1477,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AttributesEx4': 2048, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunted.', 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A mocking attack that causes a moderate amount of threat and forces the target to focus attacks on you for $d.  If the target is tauntable, also deals weapon damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 196608, 'SpellClassMask_1': 134217728, 'SpellClassSet': 4, 'SpellLevel': 16, 'SpellVisualID_1': 39, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rend_772 = spell(
    id=772,
    name='Rend',
    school=School.NORMAL,
    mechanic=15,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, ap_potency=11.23, potency_kind='periodic', mechanic=15, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    tooltip_vars=improved_rend_tooltip,
    spell_icon_id=245,
    notes=(
        'warrior-rework W0a A1 (shared doc "Rend", HANDOFF D19): ap_potency 10.7 -> 9 per 3 s tick (45 over 15 s; stock '
        'at 60 is 185 + 100% weapon damage over 5 ticks, about 620). The weapon part is gone: spell_warr_rend is '
        'unbound (below), so the amount is the potency value alone. ShapeshiftMask -> 0. Tooltip and aura text from '
        'the doc. Earlier history: pulled from existing data; potency system P7 converted it to ap_potency. '
        'warrior-rework S2 D23 (Q9, user ruling 2026-10-30): Rend needs a weapon again - EquippedItemClass 2 / '
        'EquippedItemSubclass 173555, the stock gate (every melee weapon a warrior can wield: axes, maces, swords, '
        'one- and two-handed, polearms, staves, fist weapons, daggers, spears). With the gate the core folds the '
        'weapon-gated physical aura-79 mods (Two-Handed Weapon Specialization, Two-Handed Weapon Mastery) into the '
        'bleed at application (Unit.cpp SpellPctDamageModsDone), so spell_warr_rend_arms divides them back out: '
        'two-hander talents do not raise bleeds. D27: the bleed damage reads Improved Rend (tooltip_vars 1388). The tooltip is per tick ("every $t1 sec for $d"), not a total: Lingering Wounds (a duration SpellMod) lengthens the bleed without moving the base 15 s, so a total would be wrong at 3/3.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Bleeding.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Wounds the target, causing it to bleed for {pot1*ir} every $t1 sec for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 0, 'SpellClassMask_1': 32, 'SpellClassSet': 4, 'SpellLevel': 4, 'SpellVisualID_1': 372, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)

unbind_script(-100, 'spell_warr_charge')   # W0b D5: the fork spell_warr_charge_rework is bound in warrior_shared.py
unbind_script(3411, 'spell_warr_intervene')   # W0b D6/D8: the fork spell_warr_intervene_rework is bound in warrior_shared.py
unbind_script(-772, 'spell_warr_rend')   # W0a D19: drops the script's weapon part and the dead rank >= 9 bonus


cleave_845 = spell(
    id=845,
    name='Cleave',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=144, implicit_target_a=6, chain_targets=2),
        Effect(type=EffectType.WEAPON_DAMAGE, sp_potency=12, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=6, chain_targets=2),
    ],
    tooltip_vars=cleave_tooltip,
    spell_icon_id=277,
    notes=(
        'warrior-rework W0a A1 (shared doc "Cleave", HANDOFF D4/D5/D3): an instant strike on the GCD, learned at 14. '
        'Attributes 0x50014 -> 0x50010 (next-swing bit cleared), StartRecovery 133/1500. eff0 WEAPON_PERCENT_DAMAGE '
        'weapon_potency 120 chain 2, eff1 WEAPON_DAMAGE sp_potency 10 direct T 1500 chain 2 (same targets as eff0; '
        'percent first, flat second). SpellLevel 20 -> 14. Stale bootstrap keys dropped. Family bit d0 b22 kept. warrior-rework S3 D37: the damage reads '
        'Improved Cleave x Frenzied Blows x Unending Fury (tooltip_vars 1407, token $<mult>).'
    ),
    raw_overrides={'AttributesEx': 512, 'AttributesEx2': 4096, 'AttributesEx3': 1024, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'An instant strike that hits the target and 1 nearby enemy for ${$m1*$<mult>}% weapon damage plus {pot2.avg*mult}.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 4194304, 'SpellClassMask_3': _masks.DAMAGING_ABILITY_GROUP, 'SpellClassSet': 4, 'SpellLevel': 14, 'SpellPriority': 50, 'SpellVisualID_1': 219, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shield_wall_871 = spell(
    id=871,
    name='Shield Wall',
    school=School.NORMAL,
    attributes=327696,
    category=132,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=12000,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-61, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=281,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced.', 'BaseLevel': 28, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1% for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 0, 'SpellClassMask_1': 8192, 'SpellClassSet': 4, 'SpellLevel': 28, 'SpellPriority': 50, 'SpellVisualID_1': 345},
)


demoralizing_shout_1160 = spell(
    id=1160,
    name='Demoralizing Shout',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-36, points_per_level=-5.696969696969697, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_ATTACK_POWER, radius_yards=10.0),
    ],
    spell_icon_id=282,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 14); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces melee attack power by $s1.', 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the melee attack power of all enemies within $a1 yards by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 131072, 'SpellClassSet': 4, 'SpellLevel': 14, 'SpellVisualID_1': 210, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


challenging_shout_1161 = spell(
    id=1161,
    name='Challenging Shout',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_TAUNT, radius_yards=10.0),
    ],
    spell_icon_id=50,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 67108864, 'AttributesEx4': 2048, 'AttributesEx5': 2147483648, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunted.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Forces all enemies within $a1 yards to focus attacks on you for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 524288, 'SpellClassSet': 4, 'SpellLevel': 26, 'SpellVisualID_1': 209, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


slam_1464 = spell(
    id=1464,
    name='Slam',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=200, implicit_target_a=6),
        Effect(type=EffectType.WEAPON_DAMAGE, sp_potency=18, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=6),
    ],
    tooltip_vars=slam_tooltip,
    spell_icon_id=559,
    notes=(
        'warrior-rework W0a A1 (shared doc "Slam", HANDOFF D6/D4): an instant strike on the GCD with a 6 s cooldown that '
        'deals its damage itself (P0 204875 shape; the stock eff0 DUMMY that cast 50783 is gone, 50783 stays an inert '
        'row). CastingTimeIndex 16 -> 1, InterruptFlags 13 -> 0, RecoveryTime 6000, Attributes 0x250110 -> 0x50010 (as '
        'the spike clone: 0x100 DO_NOT_LOG and 0x200000 NO_ACTIVE_DEFENSE belonged to the dummy), AttributesEx3 0x30400 '
        '-> 0x400 (SUPPRESS_CASTER_PROCS / SUPPRESS_TARGET_PROCS belonged to the dummy). eff0 WEAPON_PERCENT_DAMAGE '
        'weapon_potency 115, eff1 WEAPON_DAMAGE sp_potency 10 direct T 1500. SpellLevel 30. spell_warr_slam unbound '
        '(below): a script base point would override the potency value (potency.md "What doesn\'t get a potency '
        'value" 1). warrior-rework S2 D27: the damage read Heavy Blows (tooltip_vars 1385); S3 D37 moves it to 1406 '
        '(Heavy Blows x Unending Fury, token $<mult>).'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 131072, 'AttributesEx3': 1024, 'AttributesEx6': 32, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'An instant strike that deals ${$m1*$<mult>}% weapon damage plus {pot2.avg*mult}.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'InterruptFlags': 0, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 2097152, 'SpellClassMask_3': _masks.DAMAGING_ABILITY_GROUP, 'SpellClassSet': 4, 'SpellLevel': 30, 'SpellVisualID_1': 1165, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)

unbind_script(-1464, 'spell_warr_slam')   # W0a D6: 1464 deals the damage itself; 50783 stays an inert row


whirlwind_1680 = spell(
    id=1680,
    name='Whirlwind',
    school=School.NORMAL,
    attributes=327696,
    category=891,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.RAGE,
    mana_cost=250,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=121, base_points=-1, implicit_target_a=22, implicit_target_b=15, radius_yards=8.0),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=22, trigger_spell=44949),
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=156, implicit_target_a=22, implicit_target_b=15,
               radius_yards=8.0),
    ],
    tooltip_vars=whirlwind_tooltip,
    spell_icon_id=83,
    notes=(
        'pulled from existing data. warrior-rework S3 D37: the description shows the weapon percent (100%, the '
        'normalized weapon effect) through Improved Whirlwind x Unending Fury (tooltip_vars 1409, token $<mult>).'
    ),
    raw_overrides={'AttributesEx': 16, 'AttributesEx3': 1024, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 36, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'In a whirlwind of steel you attack up to $i enemies within $a1 yards, causing ${$m3*$<mult>}% weapon damage from both melee weapons to each enemy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'MaxTargets': 4, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 1, 'ShapeshiftMask': 0, 'SpellClassMask_2': 4, 'SpellClassMask_3': _masks.DAMAGING_ABILITY_GROUP, 'SpellClassSet': 4, 'SpellLevel': 36, 'SpellVisualID_1': 223, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hamstring_1715 = spell(
    id=1715,
    name='Hamstring',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=23,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1032, 'AttributesEx6': 10485760, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement slowed by $s1%.', 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Maims the enemy, reducing movement speed by $s1% for $d$?s58372[, and has a $58372h% chance to immobilize the target for $58373d.][.]', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 0, 'SpellClassMask_1': 2, 'SpellClassSet': 4, 'SpellLevel': 8, 'SpellPriority': 50, 'SpellVisualID_1': 556, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


recklessness_1719 = spell(
    id=1719,
    name='Recklessness',
    school=School.NORMAL,
    dispel=9,
    mechanic=31,
    attributes=327696,
    category=132,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=12000,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=5),
    ],
    spell_icon_id=138,
    notes=(
        'warrior-rework W0b D19/D20: off the GCD (StartRecovery 0/0; Category 132 and its 12 s lockout kept); eff0 class '
        'mask -> (0, 0, d2 b3) the damaging-ability group. warrior-rework S3 B-R1 (D6 changed): NO spell_proc row. The '
        'W0b CAST/HIT row is removed (remove_spell_proc(1719) drops the live phase-2 row) and ProcTypeMask / ProcChance '
        'are 0 so the generator and SpellMgr build none: a CAST-phase row would remove the aura at the CAST event when '
        'the last charge goes, before the AfterHit children (Frenzied Blows strikes) take the +100 crit. '
        'Player::RemoveSpellMods spends exactly one charge per Spell that applied the mod, at Spell::finish, after every '
        'target and synchronous child (the Momentum / Bloodsurge shape). Rampage (d2 b2) takes no mod; its script drops '
        'the charge itself.'
    ),
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Special ability attacks have an additional $s1% chance to critically hit but all damage taken is increased by $s2%.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next $n special ability attacks have an additional $s1% to critically hit but all damage taken is increased by $s2%.  Lasts $d.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 0, 'EffectSpellClassMaskA_2': 0, 'EffectSpellClassMaskA_3': _masks.DAMAGING_ABILITY_GROUP, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 0, 'ProcCharges': 3, 'ProcTypeMask': 0, 'RangeIndex': 1, 'ShapeshiftMask': 0, 'SpellClassMask_1': 16, 'SpellClassSet': 4, 'SpellLevel': 50, 'SpellVisualID_1': 236, 'StartRecoveryCategory': 0, 'StartRecoveryTime': 0},
)
remove_spell_proc(1719)   # S3 B-R1: charges are spent by Player::RemoveSpellMods at Spell::finish, not by a proc row


shield_block_2565 = spell(
    id=2565,
    name='Shield Block',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=51),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=150),
    ],
    spell_icon_id=28,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 2, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Block chance and block value increased by $s1%.', 'BaseLevel': 16, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to block and block value by $s1% for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_2': 512, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 0, 'SpellClassMask_1': 4096, 'SpellClassSet': 4, 'SpellLevel': 16, 'SpellVisualID_1': 3442},
)


bloodrage_2687 = spell(
    id=2687,
    name='Bloodrage',
    school=School.NORMAL,
    dispel=9,
    mechanic=31,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.HEALTH,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=199, implicit_target_a=1, misc_value=1),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=2, implicit_target_a=1, trigger_spell=29131),
    ],
    spell_icon_id=86,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Generates $/10;2687s1 rage at the cost of health, and then generates an additional $?s12296[${$29131m1*$29131d/10+$m2}][$/10;29131o1] rage over $29131d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 256, 'SpellClassSet': 4, 'SpellLevel': 10},
)


intervene_3411 = spell(
    id=3411,
    name='Intervene',
    school=School.NORMAL,
    attributes=536870928,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=25.0,
    duration_ms=6000,
    effects=[
        Effect(type=96, base_points=-1, implicit_target_a=57),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=57, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127, radius_yards=10.0),
    ],
    spell_icon_id=2205,
    notes='warrior-rework W0b D8: eff1 aura 111 (intercept) -> aura 87 MOD_DAMAGE_PERCENT_TAKEN -10% (bp -11, die 1), all schools, 6 s; old proc fields zeroed; SpellLevel = BaseLevel 30. Script binding swapped (spell_warr_intervene unbound, fork declared in warrior_shared.py).',
    raw_overrides={'AttributesEx5': 2048, 'AttributesEx6': 67108864, 'AttributesEx7': 262144, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Run at a party or raid member, reducing their damage taken by $s2% for $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 65219, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 0, 'ProcCharges': 0, 'ProcTypeMask': 0, 'RangeIndex': 95, 'ShapeshiftMask': 0, 'SpellClassMask_2': 65536, 'SpellClassSet': 4, 'SpellLevel': 30, 'SpellVisualID_1': 9107},
)


intimidating_shout_5246 = spell(
    id=5246,
    name='Intimidating Shout',
    school=School.NORMAL,
    mechanic=Mechanic.FEAR,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=250,
    mana_cost_pct=0,
    range_yards=8.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=20511),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_FEAR, radius_yards=8.0),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_INCREASE_SPEED, radius_yards=8.0),
    ],
    spell_icon_id=148,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 136, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Intimidated.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 22, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The warrior shouts, causing up to $5246i enemies within $5246a2 yards to cower in fear.  The targeted enemy will be unable to move while cowering.  Lasts $5246d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxTargets': 5, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'SpellClassMask_1': 262144, 'SpellClassSet': 4, 'SpellLevel': 22, 'SpellPriority': 50, 'SpellVisualID_1': 247, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


execute_5308 = spell(
    id=5308,
    name='Execute',
    school=School.NORMAL,
    attributes=327952,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=92, points_per_level=24.339285714285715, implicit_target_a=6),
    ],
    spell_icon_id=1648,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 24); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AttributesEx4': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 24, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Attempt to finish off a wounded foe, causing ${$m1+$AP*0.2} damage and converting each extra point of rage into $*10;F1 additional damage (up to a maximum cost of 30 rage).  Only usable on enemies that have less than 20% health.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 0.30000001192092896, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 2, 'ShapeshiftMask': 0, 'SpellClassMask_1': 536870912, 'SpellClassSet': 4, 'SpellLevel': 24, 'SpellPriority': 50, 'SpellVisualID_1': 250, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetAuraState': 2},
)


thunder_clap_6343 = spell(
    id=6343,
    name='Thunder Clap',
    school=School.NORMAL,
    attributes=327696,
    category=49,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    power_type=PowerType.RAGE,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=83.0, potency_kind='direct', implicit_target_a=22, implicit_target_b=15, radius_yards=8.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, mechanic=8, implicit_target_a=22, implicit_target_b=15, apply_aura=138, radius_yards=8.0),
    ],
    tooltip_vars=thunder_clap_tooltip,
    spell_icon_id=199,
    notes=(
        'pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept '
        'from rank 1 (learn level 6); RealPointsPerLevel from rank1->covers-60-overridden'
        '(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/'
        'mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (warrior pass): '
        'converted to ap_potency=83.0 (warrior-potency-proposals.txt - matches the mismatched '
        'base-implied default; old ap_bonus 0.120, new 0.356). Effect 2 (the attack-speed slow '
        'debuff) is untouched. warrior-rework W0a D20 (shared doc "Thunder Clap"): the slow lasts 30 s (was the level 6 '
        'value of 10 s); ShapeshiftMask -> 0; tooltips from the doc. warrior-rework S1 D26: the damage reads '
        '{pot1*mult} (Improved Thunder Clap x Thunderstruck, tooltip_vars 1422).'
    ),
    raw_overrides={'AttributesEx': 136, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Time between attacks increased.', 'BaseLevel': 6, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blasts nearby enemies, dealing {pot1*mult} Physical damage and increasing the time between their attacks by $s2% for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'RangeIndex': 1, 'ShapeshiftMask': 0, 'SpellClassMask_1': 128, 'SpellClassSet': 4, 'SpellLevel': 6, 'SpellVisualID_1': 145, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


pummel_6552 = spell(
    id=6552,
    name='Pummel',
    school=School.NORMAL,
    attributes=327696,
    category=88,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.INTERRUPT_CAST, die_sides=0, mechanic=26, implicit_target_a=6),
    ],
    spell_icon_id=756,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 8, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Pummel the target, interrupting spellcasting and preventing any spell in that school from being cast for $d.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 0, 'SpellClassMask_1': 8, 'SpellClassSet': 4, 'SpellLevel': 16, 'SpellVisualID_1': 1023},
)


revenge_6572 = spell(
    id=6572,
    name='Revenge',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=3000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=441.5, potency_kind='direct', implicit_target_a=6),
    ],
    tooltip_vars=revenge_tooltip,
    spell_icon_id=562,
    notes=(
        'pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept '
        'from rank 1 (learn level 14); RealPointsPerLevel from rank1->covers-60-overridden'
        '(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/'
        'mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (warrior pass): '
        'converted to ap_potency=441.5 (warrior-potency-proposals.txt - matches the mismatched '
        'base-implied default; old ap_bonus 0.310, new 1.892). warrior-rework W0a D8: Category 65 -> 0 with a plain '
        'RecoveryTime 3000 (Revenge no longer shares a cooldown with Overpower); ShapeshiftMask -> 0. '
        'warrior-rework S1 D26: the damage reads {pot1*ir} (Improved Revenge, tooltip_vars 1420).'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AttributesEx4': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 14, 'CasterAuraState': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly counterattack an enemy for {pot1*ir}. Usable for 5 sec after you block, dodge or parry.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 0, 'SpellClassMask_1': 1024, 'SpellClassMask_3': _masks.DAMAGING_ABILITY_GROUP, 'SpellClassSet': 4, 'SpellLevel': 14, 'SpellPriority': 50, 'SpellVisualID_1': 342, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


battle_shout_6673 = spell(
    id=6673,
    name='Battle Shout',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, points_per_level=6.772151898734177, implicit_target_a=56, apply_aura=AuraType.MOD_ATTACK_POWER, radius_yards=30.0),
        Effect(type=EffectType.APPLY_AURA, base_points=14, points_per_level=6.772151898734177, implicit_target_a=56, apply_aura=124, radius_yards=30.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=0, radius_yards=30.0),
    ],
    spell_icon_id=456,
    notes=(
        'pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. '
        'warrior-rework S3 D30: new e2 aura 29 MOD_STAT misc 0 (Strength), same target and radius as e0/e1; spell_warr_commanding_presence '
        '(DoEffectCalcAmount on e2) sets its amount from the caster\'s Commanding Presence rank (0 / half / full of COMMANDING_PRESENCE_AT_60 scaled by level).'
    ),
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases your attack power by $s1. Strength increased.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The warrior shouts, increasing attack power of all raid and party members within $a1 yards by $s1.  Lasts $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 246, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


overpower_7384 = spell(
    id=7384,
    name='Overpower',
    school=School.NORMAL,
    attributes=2424848,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=168, implicit_target_a=6),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=17, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=6),
    ],
    tooltip_vars=battlelord_tooltip,
    spell_icon_id=26,
    notes=(
        'warrior-rework W0a A1 (shared doc "Overpower", HANDOFF D4/D5/D7/D8): weapon potency. eff0 '
        'WEAPON_PERCENT_DAMAGE weapon_potency 100 first, eff1 NORMALIZED_WEAPON_DMG sp_potency 10 direct T 1500 second; '
        'the stock eff0 type 121 bp -1 and the eff1 1 ms DUMMY aura (and duration_ms 1) are gone (as P0 204870). '
        'Category 65 / 5 s -> Category 0, no cooldown (Revenge no longer shares it). AttributesEx 0x100000 '
        'FINISHING_MOVE_DAMAGE cleared in W0b (D3, 0x58100200 -> 0x58000200): usable on CasterAuraSpell 204403 (the Overpower '
        'charge aura, overpower_204403 in warrior_shared.py) instead of a combo point. SpellLevel 12. spell_warr_overpower '
        'stays bound (EFFECT_0 SPELL_EFFECT_ANY). warrior-rework S2 D27: the damage reads Battlelord (tooltip_vars 1386).'
    ),
    raw_overrides={'AttributesEx': 1476395520, 'AttributesEx3': 1024, 'AttributesEx4': 512, 'AttributesEx6': 1024, 'AuraDescription_Lang_Mask': 16712188, 'CasterAuraSpell': 204403, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly overpower the enemy, dealing ${$m1*$<bl>}% weapon damage plus {pot2.avg*bl}. Usable only with an Overpower charge. Parrying an attack grants a charge.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 0, 'SpellClassMask_1': 4, 'SpellClassMask_3': _masks.DAMAGING_ABILITY_GROUP, 'SpellClassSet': 4, 'SpellLevel': 12, 'SpellVisualID_1': 39, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


pummel_13491 = spell(
    id=13491,
    name='Pummel',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.INTERRUPT_CAST, points_per_level=0.5540540540540541, die_sides=0, mechanic=26, implicit_target_a=6),
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=0.7, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=756,
    notes=(
        'pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept '
        'from rank 1 (learn level 6); RealPointsPerLevel from rank1->covers-60-overridden'
        '(undershoot-vs-top-rank) (anchor rank 3 @ level 80); coefficient/cast_time_ms/'
        'mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (warrior pass): '
        'effect 2 converted to ap_potency=0.7 (warrior-potency-report.md base-implied default, '
        'non-mismatched; negligible damage either way - AP framing chosen over the tool\'s naive '
        'SP default, see the P7 summary). Effect 1 (the interrupt) is untouched.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 6, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Pummel the target for {pot2} damage and interrupt the spell being cast for $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 65536, 'SpellClassSet': 4, 'SpellLevel': 6, 'SpellVisualID_1': 1023, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


berserker_rage_18499 = spell(
    id=18499,
    name='Berserker Rage',
    school=School.NORMAL,
    dispel=9,
    mechanic=31,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=30),
    ],
    spell_icon_id=1465,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 32768, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Fear, Sap and Incapacitate effects.  Generating extra rage when taking damage.', 'BaseLevel': 32, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The warrior enters a berserker rage, removing and granting immunity to Fear, Sap and Incapacitate effects and generating extra rage when taking damage.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 139944, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 4, 'SpellLevel': 32, 'SpellVisualID_1': 47, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


retaliation_20230 = spell(
    id=20230,
    name='Retaliation',
    school=School.NORMAL,
    attributes=327696,
    category=132,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=12000,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=278,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 512, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Counterattacking all melee attacks.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly counterattack any enemy that strikes you in melee for $20230d.  Melee attacks made from behind cannot be counterattacked.  A maximum of $20230n attacks will cause retaliation.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcCharges': 20, 'ProcTypeMask': 40, 'RangeIndex': 1, 'ShapeshiftMask': 65536, 'SpellClassMask_2': 8, 'SpellClassSet': 4, 'SpellLevel': 20, 'SpellVisualID_1': 7395, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


intercept_20252 = spell(
    id=20252,
    name='Intercept',
    school=School.NORMAL,
    attributes=537198608,
    category=1158,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=25.0,
    effects=[
        Effect(type=96, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=20253),
    ],
    spell_icon_id=516,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx6': 8388608, 'AttributesEx7': 262144, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Charge an enemy, causing ${$AP*0.12} damage (based on attack power) and stunning it for $20253d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 65219, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 95, 'ShapeshiftMask': 262144, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 4, 'SpellLevel': 30, 'SpellVisualID_1': 29},
)


spell_reflection_23920 = spell(
    id=23920,
    name='Spell Reflection',
    school=School.NORMAL,
    attributes=134545424,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=28),
    ],
    spell_icon_id=1935,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108866, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reflects the next spell cast on you.', 'BaseLevel': 44, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Raise your shield, reflecting the next spell cast on you.  Lasts $d.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 139936, 'RangeIndex': 1, 'ShapeshiftMask': 0, 'SpellClassMask_2': 2, 'SpellClassSet': 4, 'SpellLevel': 44, 'SpellVisualID_1': 7962},
)


shield_slam_23922 = spell(
    id=23922,
    name='Shield Slam',
    school=School.NORMAL,
    attributes=327696,
    category=1209,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    power_type=PowerType.RAGE,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=6, misc_value=1),
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=242.6, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=413,
    notes=(
        'pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept '
        'from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60-overridden'
        '(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/'
        'mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (warrior pass): '
        'converted to ap_potency=242.6 (warrior-potency-report.md base-implied default, '
        'non-mismatched). Verified real effect type per the P7 task\'s own instruction: effect 2 '
        'is a plain SCHOOL_DAMAGE effect, not weapon-type (SpellEffects.cpp\'s "Shield Slam" '
        'SPELLFAMILY_WARRIOR case only adds the shield-block-value bonus, unrelated to attack '
        'power - no F11 gate needed). The old EffectBonusMultiplier_2=1.0 was a dead/vestigial '
        'spell power coefficient (Warriors never itemize spell power under this fork\'s stat '
        'system) - reframed to AP, which is what the ability actually scales with for every real '
        'Warrior build.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Slam the target with your shield, causing {pot2} damage, modified by your shield block value, and dispels $s1 magic effect on the target.  Also causes a high amount of threat.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 512, 'SpellClassMask_3': _masks.DAMAGING_ABILITY_GROUP, 'SpellClassSet': 4, 'SpellLevel': 40, 'SpellVisualID_1': 42, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


heroic_strike_25286 = spell(
    id=25286,
    name='Heroic Strike',
    school=School.NORMAL,
    attributes=327700,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=200, implicit_target_a=6),
    ],
    spell_icon_id=856,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A strong attack that increases melee damage by $s1 and causes a high amount of threat.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 64, 'SpellClassSet': 4, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 39},
)


revenge_25288 = spell(
    id=25288,
    name='Revenge',
    school=School.NORMAL,
    attributes=327696,
    category=65,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=5000,
    power_type=PowerType.RAGE,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(
            type=EffectType.SCHOOL_DAMAGE, base_points=722, die_sides=161, implicit_target_a=6,
            potency_excluded="superseded rank, kept only because an item_template row (21299, "
            "'Manual of Revenge VI') casts this exact spell id (see this spell's notes=) - this "
            "rank has no RealPointsPerLevel (frozen at its own BasePoints for every level >= 60, "
            "same BaseLevel=SpellLevel=60, MaxLevel=0), so unlike a MaxLevel-capped legacy rank "
            "it's already uncapped but simply doesn't scale; converting to potency would still "
            "silently add real level scaling above 60, buffing whatever casts this rank - the "
            "same class of historical-power-ceiling change the Warlock pilot's MaxLevel-capped "
            "ranks were excluded for (potency-system.PROGRESS.md P4). User precedent followed: "
            "exclude, keep as-is.",
        ),
    ],
    spell_icon_id=562,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AttributesEx4': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CasterAuraState': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly counterattack an enemy for ${$m1+$AP*0.310} to ${$M1+$AP*0.310} damage.   Revenge is only usable after the warrior blocks, dodges or parries an attack.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 131072, 'SpellClassMask_1': 1024, 'SpellClassSet': 4, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 342, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


battle_shout_25289 = spell(
    id=25289,
    name='Battle Shout',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=231, points_per_level=1.0, implicit_target_a=56, apply_aura=AuraType.MOD_ATTACK_POWER, radius_yards=30.0),
        Effect(type=EffectType.APPLY_AURA, base_points=231, points_per_level=1.0, implicit_target_a=56, apply_aura=124, radius_yards=30.0),
    ],
    spell_icon_id=456,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases your attack power by $s1.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The warrior shouts, increasing attack power of all raid and party members within $a1 yards by $s1.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 68, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 4, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 246, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


cleave_30213 = spell(
    id=30213,
    name='Cleave',
    school=School.NORMAL,
    attributes=327696,
    category=40,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=31, points_per_level=3.066666666666667, implicit_target_a=6, chain_targets=2),
    ],
    spell_icon_id=277,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AttributesEx2': 4096, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "A sweeping attack that does the Felguard's weapon damage plus $s1 to the target and his nearest ally.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 4194304, 'SpellClassSet': 4, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 219, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


enraged_regeneration_55694 = spell(
    id=55694,
    name='Enraged Regeneration',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=20, amplitude=1000),
    ],
    spell_icon_id=2008,
    notes='warrior-rework W0b D26: plain heal - CasterAuraState 17 (needs an Enrage) -> 0, eff1 (immunity to Enrage, aura 77) dropped, SpellLevel = BaseLevel 56, texts from the shared doc.',
    raw_overrides={'AttributesEx': 98304, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Regenerating health.', 'BaseLevel': 56, 'CasterAuraState': 0, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You regenerate $o1% of your maximum health over $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 131072, 'SpellClassSet': 4, 'SpellLevel': 56, 'SpellPriority': 50, 'SpellVisualID_1': 12582, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


heroic_throw_57755 = spell(
    id=57755,
    name='Heroic Throw',
    school=School.NORMAL,
    attributes=2424848,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=4.5, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=3182,
    notes=(
        'pulled from existing data. Potency system P7 (warrior pass): converted to ap_potency=4.5 '
        '(warrior-potency-proposals.txt - matches the mismatched base-implied default; old '
        'ap_bonus 0.500, new 0.019). Standard flat+AP-coefficient model (no hard-coded '
        'SpellEffects.cpp case for this spell), so no F11 gate needed.'
    ),
    raw_overrides={'AttributesEx': 512, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Throws your weapon at the enemy causing {pot1} damage (based on attack power).  This ability causes high threat.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'Speed': 50.0, 'SpellClassMask_2': 1, 'SpellClassMask_3': _masks.DAMAGING_ABILITY_GROUP, 'SpellClassSet': 4, 'SpellLevel': 60, 'SpellVisualID_1': 13222, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shattering_throw_64382 = spell(
    id=64382,
    name='Shattering Throw',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=1500,
    cooldown_ms=300000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=250,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=4.5, potency_kind='direct', implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=6, apply_aura=101, misc_value=1),
    ],
    spell_icon_id=3998,
    notes=(
        'pulled from existing data. Potency system P7 (warrior pass): effect 1 converted to '
        'ap_potency=4.5 (warrior-potency-proposals.txt - matches the mismatched base-implied '
        'default; old ap_bonus 0.500, new 0.019). Standard flat+AP-coefficient model, no F11 gate '
        'needed. Effect 2 (armor-reduction debuff) is untouched.'
    ),
    raw_overrides={'AttributesEx': 512, 'AttributesEx3': 1024, 'AttributesEx7': 25165824, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Armor reduced by $s2%.', 'BaseLevel': 52, 'CastingTimeIndex': 16, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Throws your weapon at the enemy causing {pot1} damage (based on attack power), reducing the armor on the target by $64382s2% for $64382d or removing any invulnerabilities.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'InterruptFlags': 9, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ShapeshiftMask': 0, 'Speed': 50.0, 'SpellClassMask_2': 4194304, 'SpellClassMask_3': _masks.DAMAGING_ABILITY_GROUP, 'SpellClassSet': 4, 'SpellLevel': 52, 'SpellVisualID_1': 13222, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mortal_strike_12294 = spell(
    id=12294,
    name='Mortal Strike',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=250,  # 25 rage: Arms Q3 fallback, user 2026-10-29 after the W0a rage sweep
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=6, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=228, implicit_target_a=6),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=18, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=6),
    ],
    tooltip_vars=improved_mortal_strike_tooltip,
    spell_icon_id=564,
    notes=(
        'warrior-rework W0a A1 (Arms doc "Mortal Strike", HANDOFF D4/D5/D8): weapon potency. eff0 aura 118 -50% healing '
        'kept, eff1 WEAPON_PERCENT_DAMAGE weapon_potency 130, eff2 NORMALIZED_WEAPON_DMG sp_potency 10 direct T 1500 '
        '(percent before flat; the stock eff1 type 121 per-level flat is gone). SpellLevel 40 -> 20 (potency spell: '
        'BaseLevel = SpellLevel, MaxLevel 0). Category 971 -> 0 with a plain RecoveryTime 6000 (no longer shares a '
        'cooldown with Bloodthirst). warrior-rework S2 D27: the damage (not the healing reduction) reads Improved '
        'Mortal Strike (tooltip_vars 1387).'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Healing received is reduced.', 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A vicious strike that deals ${$m2*$<ims>}% weapon damage plus {pot3.avg*ims} and wounds the target, reducing the healing it receives by $s1% for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 2, 'SpellClassMask_1': 33554432, 'SpellClassMask_3': _masks.DAMAGING_ABILITY_GROUP, 'SpellClassSet': 4, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 39, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


devastate_20243 = spell(
    id=20243,
    name='Devastate',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        None,
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=120, implicit_target_a=6),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=10, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=6),
    ],
    tooltip_vars=devastate_tooltip,
    spell_icon_id=1508,
    notes=(
        'pulled from existing data. warrior-rework S1 D8 (user ruling 2026-10-29, brief ruling 1): 10 potency per Sunder '
        'stack. eff1 WEAPON_PERCENT_DAMAGE weapon_potency 120 (kept), eff2 NORMALIZED_WEAPON_DMG sp_potency 10 direct '
        'T 1500 (Mortal Strike shape; was the stock type 121 per-level flat, 119 per stack at 60). The core '
        'SpellEffects.cpp Devastate branch reads CalculateSpellDamage(2) as (stacks - 1) x value on top of the '
        'always-added fixed_bonus, so the flat part is n x V for n = the stack count after this cast applies its own '
        'Sunder: a 5-stack Devastate adds 5V = 50 potency (about 134 damage at 60; V is 25-27.5). The tooltip says it '
        'as the engine counts. SpellLevel 50 -> 10 (open level; potency spell: BaseLevel = SpellLevel, MaxLevel 0, the '
        'old BaseLevel 50 / MaxLevel 80 overrides are gone). Shield requirement kept. D26: weapon % and flat part both '
        'read Puncture through {pot3.avg*pun} / ${$m2*$<pun>} (tooltip_vars 1421).'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': '', 'CastingTimeIndex': 1, 'CumulativeAura': 5, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Sunder the target's armor causing the Sunder Armor effect.  In addition, causes ${$m2*$<pun>}% weapon damage plus {pot3.avg*pun} for each application of Sunder Armor on the target, counting the application from this attack.  The Sunder Armor effect can stack up to $u times.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'FacingCasterFlags': 1, 'ImplicitTargetA_1': 6, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 64, 'SpellClassMask_3': _masks.DAMAGING_ABILITY_GROUP, 'SpellClassSet': 4, 'SpellLevel': 10, 'SpellVisualID_1': 12295, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


death_wish_12292 = spell(
    id=12292,
    name='Death Wish',
    school=School.NORMAL,
    dispel=9,
    mechanic=31,
    attributes=134479888,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY,
               amplitude=1000),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=169,
    notes=(
        'pulled from existing data. warrior-rework S3 D5: the stock +20% physical damage (e0 aura 79) is gone (Enrage '
        'owns the damage); e1 is a PERIODIC_DUMMY 1000 ms tick that spell_warr_death_wish_fury holds Enrage with (its '
        'hold never depends on the meter); e2 +5% damage taken kept. Duration 30 s -> 15 s (idx 8), RecoveryTime 180000 '
        '-> 120000 (Cooldown Haste applies; Intensify Rage cuts it first), off the GCD (StartRecovery 0/0), 10 rage '
        '(stock, counts toward the Enrage meter through the dispatcher), stock Dispel 9 / Mechanic 31 kept (Q9). Aura '
        'group 1107 membership removed below (its aura 79 is gone). Tooltip from the Fury doc.'
    ),
    raw_overrides={'AttributesEx': 98304, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Enrage is stronger and will not fade. You take more damage.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Enrages you and increases the physical damage bonus of your Enrage by 50% for $d. Your Enrage cannot expire while Death Wish is active. You take $s3% more damage for the duration.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 1048576, 'SpellClassSet': 4, 'SpellLevel': 30, 'SpellPriority': 50, 'SpellVisualID_1': 4599, 'StartRecoveryCategory': 0, 'StartRecoveryTime': 0},
)
leave_spell_group(1107, death_wish_12292)   # S3 D5: the temporary-damage group's aura 79 is gone with e0


piercing_howl_12323 = spell(
    id=12323,
    name='Piercing Howl',
    school=School.NORMAL,
    mechanic=Mechanic.SNARE,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_DECREASE_SPEED, radius_yards=10.0),
    ],
    spell_icon_id=134,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Dazed.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes all enemies within $a1 yards to be Dazed, reducing movement speed by $s1% for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 32, 'SpellClassSet': 4, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 2677, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


sweeping_strikes_12328 = spell(
    id=12328,
    name='Sweeping Strikes',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=300,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=515,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next $n melee attacks strike an additional nearby opponent.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next $n melee attacks strike an additional nearby opponent.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcCharges': 5, 'ProcTypeMask': 20, 'RangeIndex': 1, 'ShapeshiftMask': 0, 'SpellClassMask_2': 1048576, 'SpellClassSet': 4, 'SpellLevel': 30, 'SpellPriority': 50, 'SpellVisualID_1': 211},
)


concussion_blow_12809 = spell(
    id=12809,
    name='Concussion Blow',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.STUN, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=54.6, potency_kind='direct', implicit_target_a=6),
        None,
    ],
    spell_icon_id=25,
    notes=(
        'Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Concussion Blow (12809) - was left as an '
        'untouched "pulled from existing data" reference copy. warrior-rework S1 D9 (brief ruling 4): the damage '
        'moves from the stock script-overwritten DUMMY (eff2, 38% of attack power via spell_warr_concussion_blow, now '
        'unbound) onto eff1 SCHOOL_DAMAGE ap_potency 54.6 (= stock 38% AP at about 1,000 AP; about 139 + 0.234 x AP); '
        'eff2 cleared. SpellLevel 30 (open level; BaseLevel follows). Cooldown stays 30 s. Tooltip reads {pot2}.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'AuraInterruptFlags': 4718592, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Stuns the opponent for $d and deals {pot2} damage (based on attack power). Targets that cannot be stunned are instead Concussed, dealing 15% reduced damage for 10 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 67108864, 'SpellClassMask_3': _masks.DAMAGING_ABILITY_GROUP, 'SpellClassSet': 4, 'SpellLevel': 30, 'SpellVisualID_1': 2719, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


last_stand_12975 = spell(
    id=12975,
    name='Last Stand',
    school=School.NORMAL,
    attributes=262160,
    category=1251,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=180000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=29, implicit_target_a=1),
    ],
    spell_icon_id=177,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, this ability temporarily grants you $s1% of your maximum health for $12976d.  After the effect expires, the health is lost.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 524288, 'SpellClassSet': 4, 'SpellLevel': 20, 'SpellPriority': 50},
)


bloodthirst_23881 = spell(
    id=23881,
    name='Bloodthirst',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=91.0, potency_kind='direct', implicit_target_a=6),
        Effect(type=EffectType.DUMMY),
    ],
    tooltip_vars=bloodthirst_tooltip,
    spell_icon_id=38,
    notes=(
        'pulled from existing data. Potency system P7 (warrior pass, F11 audit): Bloodthirst is '
        'NOT in warrior-potency-report.md (no spell_bonus_data row) - its real damage model is '
        'hard-coded in spell_warr_bloodthirst::HandleDamage (spell_warrior.cpp): '
        'damage=GetEffectValue(), then ApplyPct(damage, AP), i.e. live damage = GetEffectValue()% '
        'of attack power. Live EffectBasePoints=49 with DieSides=1 means GetEffectValue()=50, so '
        'the live percentage is actually 50% AP - 5 points over the documented stock target of 45% '
        '(docs/potency-system.md\'s "Attack power abilities" table already gives Bloodthirst\'s '
        'ap_potency as 64.6, derived from that 45%/450-at-1000AP target; this is an already-'
        'decided value, not re-derived here, per the same "don\'t re-derive" rule as R itself - see '
        'the P7 summary for the live-vs-doc discrepancy this surfaced, a ~10% disclosed reduction '
        'at reference gear, consistent with other pre-existing tuning drift P3 already found '
        'elsewhere). The hard-coded ApplyPct(damage, AP) line is now gated behind '
        'SpellPotency::HasRow() (spell_warrior.cpp). Effect 2 (the DUMMY, feeding the Bloodthirst '
        'heal-charge mechanism via a separate, undeclared spell 23880/23885) is untouched - it '
        'only ever reads its own CalcValue, unaffected by effect 1\'s conversion. '
        'User decision 2026-10-02: ap_potency 65.0 (was 64.6; the other candidates were 70.4 to keep '
        'the drifted live values, and the base-implied 18.7). warrior-rework W0a D8: Category 971 -> 0 with a plain '
        'RecoveryTime 4000 (its stock value; no longer shares a cooldown with Mortal Strike). warrior-rework S3 D9: '
        'cost 200 -> 0 (the 10 rage is gained in C++ on the landed hit), RecoveryTime 4000 -> 6000 (Category stays 0), '
        'SpellLevel 40 -> 20 (the potency resolver re-derives BaseLevel and keeps the level-60 value), e1 DUMMY kept '
        'at index 1 (spell_warr_bloodthirst_heal 23880 reads Effects[EFFECT_1], the 1%), NO ENERGIZE effect (a '
        'caster-target effect makes the caster a second target, the Victory Rush bug class). Rebound from stock '
        'spell_warr_bloodthirst to spell_warr_bloodthirst_fury (warrior_fury.py). Tooltip from the Fury doc; the damage '
        'reads Unending Fury (tooltip_vars 1408, token {pot1*uf}).'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly attack the target, causing {pot1*uf} Physical damage and generating 10 rage. Each bleed applied by you increases the damage of Bloodthirst by 8%, up to 40%. In addition, your next successful melee attack restores $m2% of your maximum health. Lasts $23885d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 1024, 'SpellClassMask_3': _masks.DAMAGING_ABILITY_GROUP, 'SpellClassSet': 4, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 372, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


bladestorm_46924 = spell(
    id=46924,
    name='Bladestorm',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=90000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=250,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=204495),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=147, misc_value=1733),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=263),
    ],
    spell_icon_id=2782,
    notes=(
        'pulled from existing data. warrior-rework S2 D10 (Arms doc "Bladestorm"): learned at 50 (SpellLevel/BaseLevel '
        '60 -> 50, values stay anchored to the level 60 stock value); eff0 trigger 50622 -> 204495 (the Arms whirl, 5 '
        'targets, own mask d1 0x4000 only; 50622 / 44949 stay untouched for Fury\'s Whirlwind and have no NPC user); '
        'tooltip and aura text from the doc.'
    ),
    raw_overrides={'AttributesEx': 32784, 'AttributesEx3': 1024, 'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spinning. Cannot use other abilities.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You become a whirlwind of steel, striking up to 5 nearby enemies immediately and every $t1 sec for $d. You can move but cannot use other abilities, and you cannot be stopped unless disarmed or killed.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_2': 4, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 16384, 'SpellClassSet': 4, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 10704, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shockwave_46968 = spell(
    id=46968,
    name='Shockwave',
    school=School.NORMAL,
    attributes=327696,
    category=1201,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=20000,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.STUN, implicit_target_a=104, apply_aura=AuraType.MOD_STUN, radius_yards=10.0),
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=107.7, potency_kind='direct', implicit_target_a=104, radius_yards=10.0),
        Effect(type=EffectType.DUMMY, base_points=74),
    ],
    tooltip_vars=shockwave_tooltip,
    spell_icon_id=2777,
    notes=(
        'pulled from existing data. Potency system P7 (warrior pass, F11 audit): Shockwave is NOT '
        'in warrior-potency-report.md - effect 2\'s own native base_points=-1 is a placeholder '
        '(classify_effect skipped it, v60<=0), and the real damage is hard-coded in '
        'SpellEffects.cpp\'s SPELLFAMILY_WARRIOR "// Shockwave" case (m_spellInfo->Id==46968): '
        'pct=CalculateSpellDamage(..., effIndex 2 i.e. the DUMMY, 0-based) then '
        'damage+=CalculatePct(AP, pct), i.e. live damage = DUMMY effect value % of attack power. '
        'Live DUMMY base_points=74 with DieSides=1 means its CalcValue=75, so the live percentage '
        'is 75% AP. ap_potency=107.7 on effect 2 reproduces that same total (750 at level 60/1000 '
        'AP: base 274.5 + 0.4618*AP) via the normal ap_potency formula; the hard-coded '
        'CalculateSpellDamage/CalculatePct(AP, pct) line is now gated behind '
        'SpellPotency::HasRow() (SpellEffects.cpp). Effect 3 (the DUMMY, base_points=74) is left '
        'exactly as-is - it is now unused by the gated C++ path but the tooltip\'s old $m3 '
        'reference is replaced with {pot2} below, so nothing reads it live anymore. '
        'warrior-rework S1 D9 (brief ruling 4): the live 107.7 row on eff1 is kept (spell_warr_shockwave no longer '
        'overwrites it; damage is about 274-301 + 0.4616 x AP), SpellLevel 60. D26: the damage reads {pot2*ts} '
        '(Thunderstruck, tooltip_vars 1424). Tooltip from the Protection doc.'
    ),
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Sends a wave of force in front of the caster, causing {pot2*ts} damage (based on attack power) and stunning all enemy targets in a frontal cone for $d.  Targets that cannot be stunned take double damage instead.  Shockwave adds an amount equal to 20% of your maximum health to your Storm\'s Bulwark shield, plus an additional 1% for each target struck, up to 5 targets.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 32768, 'SpellClassSet': 4, 'SpellLevel': 60, 'SpellVisualID_1': 10703, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
