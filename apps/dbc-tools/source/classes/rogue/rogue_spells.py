"""
Rogue - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/rogue.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .rogue_...` below) resolve.
"""

from dataclasses import replace as _replace

from lib import potency as _potency
from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import custom_attr, pot_text, scripted_by, spell, spell_group, trained_by, unbind_script, unlink_spell
from . import _masks as m
from .rogue_combat import (
    ADRENALINE_RUSH_EXTRA_POINTS, BLADE_FLURRY_COPY_PCT, BLADE_FLURRY_EXTRA_TARGETS, KILLING_SPREE_HOP_RANGE_YD,
    _c, tooltip_sinister_strike_1350,
)
from .rogue_assassination import (
    mutilate_mh_203827, mutilate_oh_203828, tooltip_blood_spatter_1322, tooltip_seal_fate_1323,
    tooltip_venomous_fan_1321, tooltip_vile_poisons_1320,
)
from .rogue_shared import ghostly_veil_203723
from .rogue_subtlety import tooltip_ambush_1336, tooltip_backstab_1335
from .rogue_trigger_spells import vanish_11327


# S1 (WP-BRIEF R3): the one-hand weapon mask, raw EquippedItemSubclass 0xA091 = axe 0, mace 4, sword 7, fist 13, dagger 15.
_ONE_HAND_MASK = 41105


# ---- RG0b hand-built finisher tooltips (rogue-rework RG0b-WP-BRIEF: Rupture / Deadly Throw) ----
def _expr_plus(resolved, extra, *, ticks=1.0, scale=1.0):
    """`lib.potency.tooltip_expression` with the constant/stat term `extra` added INSIDE every branch of the outer
    `$max()` (a top-level `+` outside it is dropped by the client). With `extra=''` it equals tooltip_expression."""
    bonus = _potency._stat_bonus_term(resolved, ticks)
    tail = '+'.join(t for t in (bonus, extra) if t)
    suffix = f'+{tail}' if tail else ''
    f = _potency._fmt
    return (
        f'$max($max({tail or "0"},{f(resolved.tooltip_low_intercept * ticks * scale)}'
        f'+{f(resolved.tooltip_low_slope * ticks * scale)}*$PL{suffix}),'
        f'{f(resolved.points_per_level * ticks * scale)}*$max(0,$PL-{f(resolved.tooltip_high_offset)}){suffix})'
    )


# Deadly Throw 26679 effect 1 (direct, instant -> T 1.5 s, SpellLevel 36): flat ap_potency 26.6175, plus per combo point
# cp_ap_potency 42.042 (= 0.75 x Eviscerate's 35.49 / 56.056 since M2c; M2a 20.475 / 32.34, was 14.625 / 23.1). The flat AP term reads RANGED
# attack power ($RAP: thrown requirement, SpellInfo::IsRangedWeaponSpell); the per-combo-point AP term always reads MELEE
# attack power ($AP, SpellPotency::Apply). 5-point average value at level 60: see the M2c values above (M2a read 54.8 + 432.5 + ~0.0878 x RAP + 0.693 x AP)
# (+5% mid-roll on the flat).
_DT_LEVEL = 36
_dt_flat = _potency.resolve(
    _potency.PotencyEffect(ap_potency=26.6175, kind=_potency.KIND_DIRECT, t_ms=1500.0), spell_level=_DT_LEVEL)
_dt_flat = _replace(_dt_flat, ap_token=_potency.RANGED_AP_TOKEN)
_dt_cp = _potency.resolve(
    _potency.PotencyEffect(ap_potency=42.042, kind=_potency.KIND_PERIODIC, t_ms=1500.0), spell_level=_DT_LEVEL)
# Eviscerate 2098 effect 1 (direct, T 1.5 s, SpellLevel 1): flat ap_potency 35.49 + per combo point cp_ap_potency
# 56.056 (M2c user ruling 2026-10-28 +30% of M2a's 27.3 / 43.12, themselves x1.4 of 19.5 / 30.8), both AP terms melee $AP. The tooltip ladder quotes the average per combo point
# (flat line +5% mid-roll, plus N x the per-point line) times Seal Fate x Coup de Grace x Surprise Attacks ($<evmult>,
# SDV 1323), each line one `$max()` (potency.md "Tooltips").
_EVISCERATE_LEVEL = 1
_ev_flat = _potency.resolve(
    _potency.PotencyEffect(ap_potency=35.49, kind=_potency.KIND_DIRECT, t_ms=1500.0), spell_level=_EVISCERATE_LEVEL)
_ev_cp = _potency.resolve(
    _potency.PotencyEffect(ap_potency=56.056, kind=_potency.KIND_PERIODIC, t_ms=1500.0),
    spell_level=_EVISCERATE_LEVEL)


def _eviscerate_points(points):
    return '${' + _expr_plus(
        _ev_flat,
        f'{_potency._fmt(points * _ev_cp.level60_value)}+{_potency._fmt(points * _ev_cp.ap_coefficient)}*$AP',
        scale=1.0 + _ev_flat.variance_pct / 200.0) + '*$<evmult>}'


_EVISCERATE_LADDER = 'Finishing move that causes damage per combo point:' + ''.join(
    f'\r\n   {n} {"point  " if n == 1 else "points"}: {_eviscerate_points(n)} damage' for n in range(1, 6))

_DT_5CP_DAMAGE = '${' + _expr_plus(
    _dt_flat,
    f'{_potency._fmt(5 * _dt_cp.level60_value)}+{_potency._fmt(5 * _dt_cp.ap_coefficient)}*$AP',
    scale=1.0 + _dt_flat.variance_pct / 200.0) + '*$<dtmult>}'   # Seal Fate x Throwing Specialization (SDV 1323)


backstab_53 = spell(
    id=53,
    name='Backstab',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=45,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=250, implicit_target_a=6),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=10, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=6),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    tooltip_vars=tooltip_backstab_1335,
    spell_icon_id=243,
    notes=(
        'rogue-rework RG0b A2 (shared doc "Backstab", HANDOFF Known-hard 7): cost 60 -> 45. Potency layout '
        '(EffectWeaponDmg, potency.md "Weapon attacks"): eff0 WEAPON_PERCENT_DAMAGE weapon_potency 150 FIRST, eff1 '
        'NORMALIZED_WEAPON_DMG sp_potency 10 direct T 1500 SECOND (= 150% x weapon + flat; the stock flat-first layout '
        'was (weapon + flat) x 150%), eff2 ADD_COMBO 1. SpellLevel 4; BaseLevel / MaxLevel / per-level keys come from '
        'the generator. Stock family bits (0x800004), dagger requirement 0x8000, behind-the-target custom attr 0x20000 '
        'and every other column kept. Cost not talent-reducible (shared doc). '
        'rogue-rework M2a (M1 U4, [tune]): weapon_potency 150 -> 250.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 1048576, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Backstab the target, causing ${$s1*$<bsall>}% weapon damage plus {pot2.avg*bsall}. Awards 1 combo point. Requires a dagger in the main hand. Must be behind the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 32768, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 8388612, 'SpellClassMask_3': m.DIRECT_BUILDER_GROUP, 'SpellClassSet': 8, 'SpellLevel': 4, 'SpellPriority': 50, 'SpellVisualID_1': 155, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


kidney_shot_408 = spell(
    id=408,
    name='Kidney Shot',
    school=School.NORMAL,
    mechanic=Mechanic.STUN,
    attributes=327696,
    category=270,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=20000,
    power_type=PowerType.ENERGY,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=499,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1→level-60 slope (anchor 8643, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (8643, rank 2); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 4456960, 'AttributesEx3': 1024, 'AttributesEx4': 2056, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that stuns the target.  Lasts longer per combo point:\r\n   1 point  : 1 second\r\n   2 points: 2 seconds\r\n   3 points: 3 seconds\r\n   4 points: 4 seconds\r\n   5 points: 5 seconds', 'DurationIndex': 187, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 2097152, 'SpellClassMask_3': m.FINISHER_GROUP, 'SpellClassSet': 8, 'SpellLevel': 30, 'SpellVisualID_1': 679, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


garrote_703 = spell(
    id=703,
    name='Garrote',
    school=School.NORMAL,
    mechanic=15,
    attributes=2555920,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=18000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, mechanic=15, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000, ap_potency=13.3, potency_kind='periodic'),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=1330),
    ],
    tooltip_vars=tooltip_blood_spatter_1322,
    spell_icon_id=498,
    notes=(
        'single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 14); RealPointsPerLevel from rank1→level-60 slope (anchor 11290, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48676, rank 10); flat energy cost kept as-is (Rogue is Energy-based, not Mana); effect3 (Garrote - Silence trigger, spell 1330) added: absent from rank 1, introduced at rank 7 (26839) and present at every rank through max; preserved on the survivor per explicit decision, flat (single-rank data point, no growth to derive a slope from). '
        'potency-system (PLAN P7-Rogue): converted to ap_potency=13.3 (periodic, matching the live, '
        'already-mismatched ap_dot_bonus=0.070 coefficient\'s base-implied potency from '
        'rogue-potency-report.md/rogue-potency-proposals.txt) - reproduces the pre-conversion V60 of '
        '71 exactly (simulate_value).'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 1048576, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Bleeding.', 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Garrote the enemy, silencing it for 3 sec and causing {pot1.total*garmult} Physical damage over $d. Awards 1 combo point. Must be Hidden and behind the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 536870912, 'SpellClassMask_1': 256, 'SpellClassSet': 8, 'SpellLevel': 14, 'SpellVisualID_1': 757, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)

# S1 (WP-BRIEF R1): clears the stock REQ_CASTER_BEHIND_TARGET (0x20000); spell_rog_garrote_cut_throat re-adds the arc check
# for player-cast Garrote only, so Cut Throat's triggered Garrote is legal from any side.
custom_attr(garrote_703, 0)
scripted_by(garrote_703, 'spell_rog_garrote_cut_throat')


distract_1725 = spell(
    id=1725,
    name='Distract',
    school=School.NORMAL,
    mechanic=4,
    attributes=1074003984,
    category=22,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    power_type=PowerType.ENERGY,
    mana_cost=30,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=69, base_points=9, implicit_target_a=16, radius_yards=10.0),
    ],
    spell_icon_id=1478,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 132384, 'AttributesEx3': 131072, 'AuraDescription_Lang_Mask': 16712188, 'AuraInterruptFlags': 3, 'BaseLevel': 22, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Throws a distraction, attracting the attention of all nearby monsters for $s1 seconds.  Does not break stealth.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 4096, 'SpellClassSet': 8, 'SpellLevel': 22, 'SpellVisualID_1': 261, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'Targets': 64},
)


sinister_strike_1752 = spell(
    id=1752,
    name='Sinister Strike',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=40,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=250, implicit_target_a=6),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=10, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=6),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=130,
    notes=(
        'rogue-rework RG0b A2 (shared doc "Sinister Strike", HANDOFF Known-hard 7): cost 45 -> 40 (stock less Improved '
        'Sinister Strike\'s 5, built in). Potency layout (EffectWeaponDmg, potency.md "Weapon attacks"): eff0 '
        'WEAPON_PERCENT_DAMAGE weapon_potency 100 FIRST, eff1 NORMALIZED_WEAPON_DMG sp_potency 10 direct T 1500 SECOND '
        '(= 100% x weapon + flat), eff2 ADD_COMBO 1. SpellLevel 1; stock SpellDescriptionVariableID 171 (the percent '
        'variable), BaseLevel, MaxLevel and per-level keys dropped. Stock family bits (0x800002) and every other '
        'column '
        'kept. The flat part is the doc\'s [tune] starting value (balanced in M). '
        'S3a A4 (U58): tooltip_vars = SDV 1350 and the multiplier token ssmult (Improved Sinister Strike x Surprise '
        'Attacks) on the weapon percent and the flat part; second binding spell_rog_sinister_strike_combat. '
        'rogue-rework M2a (M1 S2, [tune]): weapon_potency 100 -> 250 (the second strike 203986 mirrors it).'
    ),
    tooltip_vars=tooltip_sinister_strike_1350,
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'An instant strike that causes ${$s1*$<ssmult>}% weapon damage plus {pot2.avg*ssmult}. Awards 1 combo point.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 8388610, 'SpellClassMask_3': m.DIRECT_BUILDER_GROUP, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellVisualID_1': 253, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)

scripted_by(sinister_strike_1752, 'spell_rog_sinister_strike_blindside')
scripted_by(sinister_strike_1752, 'spell_rog_sinister_strike_combat')   # S3: second strike / Opportunity / Celerity


kick_1766 = spell(
    id=1766,
    name='Kick',
    school=School.NORMAL,
    attributes=327696,
    category=88,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.ENERGY,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.INTERRUPT_CAST, die_sides=0, mechanic=26, implicit_target_a=6),
    ],
    spell_icon_id=246,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 8, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A quick kick that interrupts spellcasting and prevents any spell in that school from being cast for $d.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 16, 'SpellClassSet': 8, 'SpellLevel': 12, 'SpellVisualID_1': 90},
)

scripted_by(kick_1766, 'spell_rog_kick_combat')   # S3 (R5): Improved Kick's capstone (interrupt detection)


gouge_1776 = spell(
    id=1776,
    name='Gouge',
    school=School.NORMAL,
    attributes=1376272,
    category=33,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.ENERGY,
    mana_cost=45,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=0.4, potency_kind='direct', implicit_target_a=6),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, mechanic=Mechanic.KNOCKOUT, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=245,
    notes=(
        'pulled from existing data. '
        'potency-system (PLAN P7-Rogue): converted to ap_potency=0.4 (direct, matching the live, '
        'already-mismatched ap_bonus=0.210 coefficient\'s base-implied potency from '
        'rogue-potency-report.md/rogue-potency-proposals.txt - Gouge\'s damage is a token amount, '
        'the stun is the real effect) - reproduces the pre-conversion V60 of 1 exactly '
        '(simulate_value).'
    ),
    raw_overrides={'AttributesEx': 134479872, 'AttributesEx3': 1032, 'AttributesEx4': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Incapacitated.', 'AuraInterruptFlags': 2, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes {pot1} damage, incapacitating the opponent for $d, and turns off your attack.  Target must be facing you.  Any damage caused will revive the target.  Awards $s2 combo $lpoint:points;.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 8, 'SpellClassMask_3': m.DIRECT_BUILDER_GROUP, 'SpellClassSet': 8, 'SpellLevel': 6, 'SpellVisualID_1': 256, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


stealth_1784 = spell(
    id=1784,
    name='Stealth',
    school=School.NORMAL,
    dispel=DispelType.STEALTH,
    attributes=437583888,
    category=38,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=30),
        Effect(type=EffectType.APPLY_AURA, base_points=4, points_per_level=5.0, implicit_target_a=1, apply_aura=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=250,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 30, 'AttributesEx': 16, 'AttributesEx2': 2097152, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stealthed.  Movement slowed by $s3%.', 'AuraInterruptFlags': 146436, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows the rogue to sneak around, but reduces your speed by $s3%.  Lasts until cancelled.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeCasterAuraState': 12, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'SpellClassMask_1': 4194304, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellVisualID_1': 184, 'StartRecoveryCategory': 1178},
)


pick_lock_1804 = spell(
    id=1804,
    name='Pick Lock',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=5000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.OPEN_LOCK, base_points=4, points_per_level=5.0, implicit_target_a=26, misc_value=1),
    ],
    spell_icon_id=106,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 6, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows opening of locked chests and doors.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'EquippedItemSubclass': -1, 'InterruptFlags': 31, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 16384, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellVisualID_1': 104},
)


cheap_shot_1833 = spell(
    id=1833,
    name='Cheap Shot',
    school=School.NORMAL,
    mechanic=Mechanic.STUN,
    attributes=2555920,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=60,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
        Effect(type=EffectType.ADD_COMBO_POINTS, base_points=1, implicit_target_a=6),
    ],
    spell_icon_id=244,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134479872, 'AttributesEx2': 1048576, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Stuns the target for $d. Awards 2 combo points. Must be Hidden.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 536870912, 'SpellClassMask_1': 1024, 'SpellClassSet': 8, 'SpellLevel': 26, 'SpellVisualID_1': 266, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


disarm_trap_1842 = spell(
    id=1842,
    name='Disarm Trap',
    school=School.NORMAL,
    attributes=196624,
    cast_time_ms=1000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.OPEN_LOCK, base_points=199, points_per_level=5.0, implicit_target_a=23, misc_value=4),
    ],
    spell_icon_id=228,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131104, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 4, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Disarm a hostile trap.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ShapeshiftMask': 536870912, 'SpellClassMask_2': 8192, 'SpellClassSet': 8, 'SpellLevel': 30, 'SpellVisualID_1': 252, 'Targets': 16384},
)


vanish_1856 = spell(
    id=1856,
    name='Vanish',
    school=School.NORMAL,
    attributes=135594000,
    category=39,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=180000,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=vanish_11327.id),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=18461),
        Effect(type=79, base_points=-1, implicit_target_a=1),
    ],
    spell_icon_id=252,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 22); RealPointsPerLevel from rank1→level-60 slope (anchor 1857, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (26889, rank 3); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'ActiveIconID': 30, 'AttributesEx': 1056, 'AttributesEx2': 2, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Improved stealth.', 'AuraInterruptFlags': 15367, 'BaseLevel': 22, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows the rogue to vanish from sight, entering an improved stealth mode for $11327d.  Also breaks movement impairing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeCasterAuraState': 12, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 139944, 'RangeIndex': 1, 'SpellClassMask_1': 2048, 'SpellClassSet': 8, 'SpellLevel': 22, 'SpellVisualID_1': 255},
)


_RUPTURE_DESCRIPTION = (
    'Finishing move that causes {pot1*rupmult} Physical damage every 2 sec. Lasts longer per combo point: '
    '1 point: 8 sec, 2 points: 12 sec, 3 points: 16 sec, 4 points: 20 sec, 5 points: 24 sec.'
)


rupture_1943 = spell(
    id=1943,
    name='Rupture',
    school=School.NORMAL,
    mechanic=15,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=4000,
    max_duration_ms=24000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, mechanic=15, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000, base_potency=29.4075, ap_potency=9.84375, potency_kind='periodic'),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    tooltip_vars=tooltip_blood_spatter_1322,
    spell_icon_id=500,
    notes=(
        'single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor 11275, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48672, rank 9); flat energy cost kept as-is (Rogue is Energy-based, not Mana). '
        'potency-system (PLAN P7-Rogue, finisher - same shape as P6\'s Rip): the flat per-tick line '
        '(no AP) is base_potency=16.8 (periodic, matching the base-implied potency from '
        'rogue-potency-report.md) - reproduces the pre-conversion per-tick flat value exactly (60, '
        'via simulate_value; there is no spell_bonus_data row for 1943, confirmed by the report). '
        'Rupture DOES have real AP scaling, but as a SCRIPT (spell_rog_rupture::CalculateAmount, '
        'src/server/scripts/Spells/spell_rogue.cpp - a per-combo-tier attackpowerPerCombo[] lookup '
        'added once per application, not a repeating per-combo-point multiply, found only by '
        'grepping spell_rogue.cpp directly - it does not show up in spell_bonus_data or '
        'SpellEffects.cpp\'s F11 audit list), matching the real 0.0375*AP rate at 5 combo points. '
        'cp_base_potency=0.561 reproduces the DBC\'s own flat EffectPointsPerCombo_1=2.0 '
        'per-combo-point-per-tick line to within 0.05%. cp_ap_potency=1.3125 gives an ap_coefficient '
        'of exactly 0.0075, so that 5 combo points\' worth (SpellPotency::Apply multiplies by '
        'comboPoints) reproduces the script\'s AP*0.0375 term at the 5-combo-point reference '
        'exactly, same "fit the linear cp_ap shape to the 5-combo reference, accept drift at other '
        'combo counts" approach Rip\'s own non-linear-lookup replacement used (PLAN P6 step 4). '
        'Total at level 60/5 combo/1000 AP: 60 (flat) + 5*(2.0+0.0075*1000) = 107.5, matching the '
        'pre-conversion total (60 flat + 5*2.0 DBC combo line + 1000*0.0375 script AP term = 107.5) '
        'exactly. EffectPointsPerCombo_1 is generated as 0; spell_rog_rupture\'s own AP addition is '
        'gated behind SpellPotency::HasRow() (src/server/scripts/Spells/spell_rogue.cpp) so it does '
        'not double count on top of the new cp_ap coefficient. '
        'rogue-rework RG0b A2 (shared doc "Rupture"): duration 4 s + 4 s per combo point = duration_ms=4000, '
        'max_duration_ms=24000 (a SpellDuration row is minted; the raw DurationIndex 553 is gone), 8 / 12 / 16 / 20 / '
        '24 s '
        'at 1-5 points; damage per tick unchanged. '
        'RG0b playtest (user 2026-10-27): the tick no longer grows with combo points, only the duration does. Every '
        'tick pays the old 5-point tick (base 16.8 + 5 x 0.561 = 19.605, AP 5 x 1.3125 = 6.5625 potency; level 60 = '
        '70.0 + 0.0375 x AP), so the 5-point total is unchanged (840.1 + 0.45 x AP over 12 ticks) and fewer points '
        'only shorten it. The tooltip shows the tick ({pot1}). Stock SpellDescriptionVariableID 63 (the ladder '
        'variables) dropped. '
        'rogue-rework M2a (M1 S1, [tune]): tick x1.5, base_potency 19.605 -> 29.4075, ap_potency 6.5625 -> 9.84375.'
    ),
    raw_overrides={'AttributesEx': 1049088, 'AttributesEx3': 1024, 'AttributesEx4': 8, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Bleeding.', 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': _RUPTURE_DESCRIPTION, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 1048576, 'SpellClassMask_3': m.FINISHER_GROUP, 'SpellClassSet': 8, 'SpellLevel': 20, 'SpellVisualID_1': 250, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)

scripted_by(rupture_1943, 'spell_rog_rupture_carnage')   # beside the stock -1943 spell_rog_rupture
scripted_by(rupture_1943, 'spell_rog_rupture_finality')   # S2: Finality (third binding)


feint_1966 = spell(
    id=1966,
    name='Feint',
    school=School.NORMAL,
    attributes=327696,
    category=0,
    cast_time_ms=0,
    cooldown_ms=15000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-41, implicit_target_a=1, apply_aura=229, misc_value=127),
    ],
    spell_icon_id=539,
    notes=(
        'rogue-rework RG0b A2 (shared doc "Feint", HANDOFF Known-hard 7, C7): retail Feint. The stock THREAT effect '
        '(eff0) is gone, leaving one effect: aura 229 MOD_AOE_DAMAGE_AVOIDANCE misc 127 stored -41 (-40% area damage '
        'taken) on the caster, 6 s (the live infinite 30101 duration was a bug). Cost 20 -> 35, own cooldown 15 s '
        '(RecoveryTime 15000, Category 82 / 10 s dropped to 0 / 0 so it no longer shares the taunt category and never '
        'starts Insult\'s cooldown). Self range and FacingCasterFlags 0 (no enemy target), so Feint rolls no poisons. '
        'Aura 229 on the caster is positive by default: no custom_attr (0-verify item 4). Stock family bit d0 b27 '
        '(Bloodfang 5P reader) kept. Cooldown under 30 s: not Cooldown Haste.'
    ),
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken from area of effect attacks reduced.', 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Performs an evasive maneuver, reducing damage taken from area of effect attacks by 40% for 6 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 0, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'SpellClassMask_1': 134217728, 'SpellClassSet': 8, 'SpellLevel': 16, 'SpellVisualID_1': 738, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


blind_2094 = spell(
    id=2094,
    name='Blind',
    school=School.NORMAL,
    mechanic=Mechanic.DISORIENTED,
    attributes=1074855952,
    category=1187,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=20000,
    power_type=PowerType.ENERGY,
    mana_cost=30,
    mana_cost_pct=0,
    range_yards=10.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-61, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_CONFUSE),
    ],
    spell_icon_id=48,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 65536, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Disoriented.', 'AuraInterruptFlags': 4718594, 'BaseLevel': 34, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blinds the target, causing it to wander disoriented for up to $d.  Any damage caused will remove the effect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'SpellClassMask_1': 16777216, 'SpellClassSet': 8, 'SpellLevel': 34, 'SpellVisualID_1': 3440, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


eviscerate_2098 = spell(
    id=2098,
    name='Eviscerate',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=35.49, cp_ap_potency=56.056, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    tooltip_vars=tooltip_seal_fate_1323,
    spell_icon_id=514,
    notes=(
        'potency-system (PLAN P6 step 4, finishers - proof case): converted from the single-rank '
        'bootstrap (BasePoints/BaseLevel/SpellLevel kept from rank 1, learn level 1). ap_potency=19.5 '
        'is the flat one-shot part (about 11% of the whole, matching stock\'s own flat/per-combo '
        'split - docs/potency-system.md\'s "Combo points don\'t scale with level"), cp_ap_potency='
        '30.8 is per combo point; together they reproduce the pre-conversion total at level 60, 5 '
        'combo points, 1000 attack power (1208) to within 0.2%. EffectPointsPerCombo_1 is generated '
        'as 0 - SpellPotency::Apply() adds the per-combo-point term instead. '
        'rogue-rework M2a (M1 R2, user ruling: Eviscerate becomes [tune]): x1.4, ap_potency 19.5 -> 27.3, '
        'cp_ap_potency 30.8 -> 43.12; M2c (user 2026-10-28): +30% to 35.49 / 56.056. Deadly Throw keeps its 75% ratio; '
        'Between the Eyes (x1.8 of M2a) and the Death from Above landing (x1.15 of M2a) were set on their own in M2c. '
        'The stock-shaped ladder ($m1 / $b1 / $AP x 0.03-0.35) is replaced by the potency '
        'ladder _EVISCERATE_LADDER (average per combo point, both AP terms melee $AP, times $<evmult>).'
    ),
    raw_overrides={'AttributesEx': 1049088, 'AttributesEx3': 1024, 'AttributesEx4': 8, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': _EVISCERATE_LADDER, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 8519680, 'SpellClassMask_3': m.FINISHER_GROUP, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellVisualID_1': 671, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


deadly_poison_2823 = spell(
    id=2823,
    name='Deadly Poison',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=7),
    ],
    spell_icon_id=513,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1→level-60 slope (anchor 25351, rank 5); coefficient/cast_time_ms/mana_cost_pct from max rank (57973, rank 9); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana); effect1 (type 54, ENCHANT_ITEM_TEMPORARY-family) left untouched -- base_points unused by that effect handler, not a real scaling quantity',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $2823h% chance of poisoning the enemy for ${$2818m1*4+0.12*$AP} Nature damage over $2818d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 30, 'SpellVisualID_1': 12720, 'Targets': 16},
)


deadly_poison_ii_2824 = spell(
    id=2824,
    name='Deadly Poison II',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=599, misc_value=8),
    ],
    spell_icon_id=513,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 38, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $2824h% chance of poisoning the enemy for ${$2819m1*4+0.12*$AP} Nature damage over $2819d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 38, 'SpellVisualID_1': 12720, 'Targets': 16},
)


sprint_2983 = spell(
    id=2983,
    name='Sprint',
    school=School.NORMAL,
    attributes=65552,
    category=44,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=180000,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, points_per_level=0.4, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=516,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1→level-60 slope (anchor 11305, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (11305, rank 3); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed increased by $s1%.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the rogue's movement speed by $s1% for $d.  Does not break stealth.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 64, 'SpellClassSet': 8, 'SpellLevel': 10, 'SpellVisualID_1': 6},
)


slice_and_dice_5171 = spell(
    id=5171,
    name='Slice and Dice',
    school=School.NORMAL,
    attributes=537198608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=19, points_per_level=0.4, implicit_target_a=1, apply_aura=138),
    ],
    spell_icon_id=515,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1→level-60 slope (anchor 6774, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (6774, rank 2); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 4195360, 'AttributesEx2': 4, 'AttributesEx3': 1342439424, 'AttributesEx4': 16, 'AttributesEx6': 8388612, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attack speed increased by $s2%.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that increases melee attack speed by $s2%.  Lasts longer per combo point:\r\n   1 point  : ${(9+$<glyph>)*(100+$<mult>)/100} seconds\r\n   2 points: ${(12+$<glyph>)*(100+$<mult>)/100} seconds\r\n   3 points: ${(15+$<glyph>)*(100+$<mult>)/100} seconds\r\n   4 points: ${(18+$<glyph>)*(100+$<mult>)/100} seconds\r\n   5 points: ${(21+$<glyph>)*(100+$<mult>)/100} seconds', 'DurationIndex': 185, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'SpellClassMask_1': 262144, 'SpellClassMask_3': m.FINISHER_GROUP, 'SpellClassSet': 8, 'SpellDescriptionVariableID': 164, 'SpellLevel': 10, 'SpellPriority': 50, 'SpellVisualID_1': 254, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


evasion_5277 = spell(
    id=5277,
    name='Evasion',
    school=School.NORMAL,
    attributes=65552,
    category=66,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=180000,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=49),
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=1, apply_aura=185),
    ],
    spell_icon_id=178,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1→level-60 slope (anchor 26669, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (26669, rank 2); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana); effect2 (ranged attacker hit chance, -26%) added: absent from rank 1, introduced only at rank 2/max (26669); preserved on the survivor per explicit decision, flat (single-rank data point)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases dodge chance by $s1%.', 'BaseLevel': 8, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "The rogue's dodge chance will increase by $s1% for $d.", 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 32, 'SpellClassSet': 8, 'SpellLevel': 8, 'SpellVisualID_1': 72},
)


shiv_5938 = spell(
    id=5938,
    name='Shiv',
    school=School.NORMAL,
    attributes=2424848,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=6),
    ],
    spell_icon_id=1834,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx2': 537919488, 'AttributesEx3': 17235968, 'AttributesEx4': 1025, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 70, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Performs an instant off-hand weapon attack that automatically applies the poison from your off-hand weapon to the target.  Slower weapons require more Energy.  Neither Shiv nor the poison it applies can be a critical strike.  Awards 1 combo point.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 536870912, 'SpellClassSet': 8, 'SpellLevel': 70, 'SpellVisualID_1': 8056, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)
# RG0b U6: the stock Shiv keeps its rows (and SLA 13461 / the C++ class), but its only script binding goes: the new
# Shiv 203725 (rogue_shared.py) replaces it, and spell_rog_shiv cast the off-hand strike 5940.
unbind_script(shiv_5938, 'spell_rog_shiv')


sap_6770 = spell(
    id=6770,
    name='Sap',
    school=School.NORMAL,
    mechanic=Mechanic.SAPPED,
    attributes=3604496,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=65,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=25000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=249,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1→level-60 slope (anchor 11297, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (51724, rank 4); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 134481184, 'AttributesEx3': 131073, 'AttributesEx4': 8388608, 'AttributesEx5': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Sapped.', 'AuraInterruptFlags': 4718594, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Incapacitates the target for up to $d.  Must be stealthed.  Only works on Humanoids that are not in combat.  Any damage caused will revive the target.  Only 1 target may be sapped at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcTypeMask': 69648, 'RangeIndex': 2, 'ShapeshiftMask': 536870912, 'SpellClassMask_1': 128, 'SpellClassSet': 8, 'SpellLevel': 10, 'SpellVisualID_1': 257, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'TargetCreatureType': 64},
)


expose_armor_8647 = spell(
    id=8647,
    name='Expose Armor',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=6, apply_aura=101, misc_value=1),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=563,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1049088, 'AttributesEx3': 1024, 'AttributesEx4': 8, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Armor decreased by $s1%.', 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that exposes the target, reducing armor by $s1% and lasting longer per combo point:\r\n   1 point  : $?s56803[18][6] sec.\r\n   2 points: $?s56803[24][12] sec.\r\n   3 points: $?s56803[30][18] sec.\r\n   4 points: $?s56803[36][24] sec.\r\n   5 points: $?s56803[42][30] sec.', 'DurationIndex': 588, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 524288, 'SpellClassMask_3': m.FINISHER_GROUP, 'SpellClassSet': 8, 'SpellLevel': 14, 'SpellVisualID_1': 3441, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


ambush_8676 = spell(
    id=8676,
    name='Ambush',
    school=School.NORMAL,
    attributes=2555920,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=45,
    mana_cost_pct=0,
    range_yards=25.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=350, implicit_target_a=6),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=10, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=6),
        Effect(type=EffectType.ADD_COMBO_POINTS, base_points=1, implicit_target_a=6),
    ],
    tooltip_vars=tooltip_ambush_1336,
    spell_icon_id=856,
    notes=(
        'rogue-rework RG0b A2 (shared doc "Ambush", HANDOFF Known-hard 7, P0 variant A): cost 60 -> 45, any melee '
        'weapon '
        '(EquippedItemSubclass 0x2A5F3 = 173555, the dagger requirement and dagger bonus gone), weapon 275% -> 175%. '
        'Range 5 -> 25 yd (the teleport reach; found, not minted). Potency layout: eff0 weapon_potency 175 FIRST, eff1 '
        'NORMALIZED_WEAPON_DMG sp_potency 10 direct T 1500 SECOND, eff2 ADD_COMBO bp 1 (= 2 points). SpellLevel 18. '
        'custom_attr(8676, 0) clears the stock REQ_CASTER_BEHIND_TARGET (0x20000): it strikes from any side. '
        'spell_rog_ambush (spell_rogue_shared.cpp) casts the Ambush Teleport helper 203726 BeforeCast when the caster '
        'was stealthed and is out of melee range. Attributes 0x270010 (ONLY_STEALTHED), Stances 0x20000000 and family '
        'bits 0x800200 kept, so a Shadowed (aura 275) rogue passes CheckCast. NPC users 7052 / 7056 (SAI spellhit -> '
        'Kill Self on 8676) keep landing a spell hit. '
        'rogue-rework M2a (M1 U1, [tune]): weapon_potency 175 -> 350.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 1048576, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Ambush the target, causing ${$s1*$<amall>}% weapon damage plus {pot2.avg*amall}. If you are stealthed and more than melee range away, you first teleport behind the target. Awards 2 combo points. Must be Hidden.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'ShapeshiftMask': 536870912, 'SpellClassMask_1': 8389120, 'SpellClassMask_3': m.DIRECT_BUILDER_GROUP, 'SpellClassSet': 8, 'SpellLevel': 18, 'SpellPriority': 50, 'SpellVisualID_1': 155, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)
custom_attr(ambush_8676, 0)
scripted_by(ambush_8676, 'spell_rog_ambush')
scripted_by(ambush_8676, 'spell_rog_ambush_subtlety')   # S2: Akaari's Echo (second binding beside RG0b's)
scripted_by(backstab_53, 'spell_rog_backstab_subtlety')   # S2: Slaughter from the Shadows / Lingering Shadow
scripted_by(eviscerate_2098, 'spell_rog_eviscerate_subtlety')   # S2: Hemorrhage / Finality
scripted_by(eviscerate_2098, 'spell_rog_eviscerate_combat')   # S3: Opportunity / Blade Rush consume


instant_poison_8679 = spell(
    id=8679,
    name='Instant Poison',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=323),
    ],
    spell_icon_id=247,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor 11340, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (57968, rank 9); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana); effect1 (type 54, ENCHANT_ITEM_TEMPORARY-family) left untouched -- base_points unused by that effect handler, not a real scaling quantity',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$8680m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 20, 'SpellVisualID_1': 12720, 'Targets': 16},
)


instant_poison_ii_8686 = spell(
    id=8686,
    name='Instant Poison II',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=324),
    ],
    spell_icon_id=247,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 28, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$8685m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 28, 'SpellVisualID_1': 12720, 'Targets': 16},
)


instant_poison_iii_8688 = spell(
    id=8688,
    name='Instant Poison III',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=325),
    ],
    spell_icon_id=247,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 36, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$8689m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 36, 'SpellVisualID_1': 12720, 'Targets': 16},
)


instant_poison_iv_11338 = spell(
    id=11338,
    name='Instant Poison IV',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=623),
    ],
    spell_icon_id=247,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 44, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$11335m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 44, 'SpellVisualID_1': 12720, 'Targets': 16},
)


instant_poison_v_11339 = spell(
    id=11339,
    name='Instant Poison V',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=624),
    ],
    spell_icon_id=247,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 52, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$11336m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 52, 'SpellVisualID_1': 12720, 'Targets': 16},
)


instant_poison_vi_11340 = spell(
    id=11340,
    name='Instant Poison VI',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=625),
    ],
    spell_icon_id=247,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$11337m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 60, 'SpellVisualID_1': 12720, 'Targets': 16},
)


deadly_poison_iii_11355 = spell(
    id=11355,
    name='Deadly Poison III',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=599, misc_value=626),
    ],
    spell_icon_id=513,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 46, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $11355h% chance of poisoning the enemy for ${$11353m1*4+0.12*$AP} Nature damage over $11353d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 46, 'SpellVisualID_1': 12720, 'Targets': 16},
)


deadly_poison_iv_11356 = spell(
    id=11356,
    name='Deadly Poison IV',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=599, misc_value=627),
    ],
    spell_icon_id=513,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 54, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $11356h% chance of poisoning the enemy for ${$11354m1*4+0.12*$AP} Nature damage over $11354d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 54, 'SpellVisualID_1': 12720, 'Targets': 16},
)


wound_poison_13219 = spell(
    id=13219,
    name='Wound Poison',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=703),
    ],
    spell_icon_id=1496,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 32); RealPointsPerLevel from rank1→level-60 slope (anchor 13227, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (57978, rank 7); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana); effect1 (type 54, ENCHANT_ITEM_TEMPORARY-family) left untouched -- base_points unused by that effect handler, not a real scaling quantity',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 32, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy, causing ${$13218m2+0.04*$AP} Nature damage and reducing all healing effects used on them by $13218s1% for $13218d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 8, 'SpellLevel': 32, 'SpellVisualID_1': 12720, 'Targets': 16},
)


wound_poison_ii_13225 = spell(
    id=13225,
    name='Wound Poison II',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=704),
    ],
    spell_icon_id=1496,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy, causing ${$13222m2+0.04*$AP} Nature damage and reducing all healing effects used on them by $13222s1% for $13222d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 8, 'SpellLevel': 40, 'SpellVisualID_1': 12720, 'Targets': 16},
)


wound_poison_iii_13226 = spell(
    id=13226,
    name='Wound Poison III',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=705),
    ],
    spell_icon_id=1496,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 48, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy, causing ${$13223m2+0.04*$AP} Nature damage and reducing all healing effects used on them by $13223s1% for $13223d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 8, 'SpellLevel': 48, 'SpellVisualID_1': 12720, 'Targets': 16},
)


wound_poison_iv_13227 = spell(
    id=13227,
    name='Wound Poison IV',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=706),
    ],
    spell_icon_id=1496,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 56, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy, causing ${$13224m2+0.04*$AP} Nature damage and reducing all healing effects used on them by $13224s1% for $13224d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 8, 'SpellLevel': 56, 'SpellVisualID_1': 12720, 'Targets': 16},
)


backstab_25300 = spell(
    id=25300,
    name='Backstab',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=60,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=149, implicit_target_a=6),
        Effect(type=31, base_points=149, implicit_target_a=6),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=243,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 1048576, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Backstab the target, causing $m2% weapon damage plus ${$m1*1.5} to the target.  Must be behind the target.  Requires a dagger in the main hand.  Awards $s3 combo $lpoint:points;.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 32768, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 8388612, 'SpellClassSet': 8, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 155, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


feint_25302 = spell(
    id=25302,
    name='Feint',
    school=School.NORMAL,
    attributes=327696,
    category=82,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.ENERGY,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.THREAT, base_points=-801, points_per_level=-1.0, implicit_target_a=6),
    ],
    spell_icon_id=539,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Performs a feint, causing no damage but lowering your threat by a large amount, making the enemy less likely to attack you.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 70, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 134217728, 'SpellClassSet': 8, 'SpellLevel': 60, 'SpellVisualID_1': 738, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


deadly_poison_v_25351 = spell(
    id=25351,
    name='Deadly Poison V',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=599, misc_value=2630),
    ],
    spell_icon_id=513,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $25351h% chance of poisoning the enemy for ${$25349m1*4+0.12*$AP} Nature damage over $25349d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 60, 'SpellVisualID_1': 12720, 'Targets': 16},
)


deadly_throw_26679 = spell(
    id=26679,
    name='Deadly Throw',
    school=School.NORMAL,
    attributes=4259858,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=26.6175, cp_ap_potency=42.042, potency_kind='direct',
               implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    tooltip_vars=tooltip_seal_fate_1323,
    spell_icon_id=2097,
    notes=(
        'rogue-rework RG0b A2 (shared doc "Deadly Throw", HANDOFF Known-hard 7, C1 / U5): learn level 64 -> 36. eff0 '
        'WEAPON_DAMAGE (58 bp + EffectPointsPerCombo_1 105) -> SCHOOL_DAMAGE Physical on Eviscerate 2098\'s potency '
        'shape: '
        'ap_potency 14.625 + cp_ap_potency 23.1 direct (= 0.75 x Eviscerate\'s 19.5 / 30.8; 130.1 potency at 5 '
        'points), '
        'no thrown-weapon roll. SpellLevel 36 (BaseLevel / MaxLevel / EffectPointsPerCombo_1 generated). The flat AP '
        'term '
        'reads RANGED attack power (thrown requirement, $RAP) and the per-combo-point term MELEE attack power ($AP): '
        '_DT_5CP_DAMAGE hand-builds the 5-point average with 308.9625 + 0.495 x $AP inside every $max() branch. eff1 '
        'slow 50% for 6 s and eff2 DUMMY kept (stock); no interrupt of its own (stock Throwing Specialization\'s '
        'interrupt is gone, S2 owns the replacement). Stock family bits d0 0x800000 + d1 0x1 kept. '
        'rogue-rework M2a (M1 R2): Eviscerate x1.4 and Deadly Throw keeps its 75% ratio: ap_potency 14.625 -> 20.475, '
        'cp_ap_potency 23.1 -> 32.34; M2c: Eviscerate +30% and Deadly Throw follows, 26.6175 / 42.042 (the Subtlety '
        'copy 204168 matches).'
    ),
    raw_overrides={'AttributesEx': 1049088, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement slowed.', 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that throws your thrown weapon at the target, causing ' + _DT_5CP_DAMAGE + ' Physical damage at 5 combo points and reducing its movement speed by 50% for 6 sec. Requires a thrown weapon.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 65536, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 74, 'Speed': 50.0, 'SpellClassMask_1': 8388608, 'SpellClassMask_2': 1, 'SpellClassMask_3': m.FINISHER_GROUP, 'SpellClassSet': 8, 'SpellLevel': 36, 'SpellVisualID_1': 7929, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)
scripted_by(deadly_throw_26679, 'spell_rog_deadly_throw_subtlety')   # S2: Throwing Specialization copies / Finality


anesthetic_poison_26785 = spell(
    id=26785,
    name='Anesthetic Poison',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=2640),
    ],
    spell_icon_id=110,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 68); RealPointsPerLevel from rank1→top rank's own top level (80, rank1 learn level ≥ 60) slope (anchor 57982, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (57982, rank 2); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana); effect1 (type 54, ENCHANT_ITEM_TEMPORARY-family) left untouched -- base_points unused by that effect handler, not a real scaling quantity",
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 68, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.  Each strike has a $26785h% chance of poisoning the enemy which instantly inflicts $26688s1 Nature damage and dispels $26688s2 Enrage effect, but causes no additional threat.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_2': 16, 'SpellClassSet': 8, 'SpellLevel': 68, 'SpellVisualID_1': 12720, 'Targets': 16},
)


instant_poison_vii_26891 = spell(
    id=26891,
    name='Instant Poison VII',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=2641),
    ],
    spell_icon_id=247,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 68, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$26890m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 68, 'SpellVisualID_1': 12720, 'Targets': 16},
)


deadly_poison_vi_26967 = spell(
    id=26967,
    name='Deadly Poison VI',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=599, misc_value=2642),
    ],
    spell_icon_id=513,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 62, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $26967h% chance of poisoning the enemy for ${$26968m1*4+0.12*$AP} Nature damage over $26968d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 62, 'SpellVisualID_1': 12720, 'Targets': 16},
)


deadly_poison_vii_27186 = spell(
    id=27186,
    name='Deadly Poison VII',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=599, misc_value=2643),
    ],
    spell_icon_id=513,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 70, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $27186h% chance of poisoning the enemy for ${$27187m1*4+0.12*$AP} Nature damage over $27187d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 70, 'SpellVisualID_1': 12720, 'Targets': 16},
)


wound_poison_v_27188 = spell(
    id=27188,
    name='Wound Poison V',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=2644),
    ],
    spell_icon_id=1496,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 64, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy, causing ${$27189m2+0.04*$AP} Nature damage and reducing all healing effects used on them by $27189s1% for $27189d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 8, 'SpellLevel': 64, 'SpellVisualID_1': 12720, 'Targets': 16},
)


eviscerate_31016 = spell(
    id=31016,
    name='Eviscerate',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(
            type=EffectType.SCHOOL_DAMAGE, base_points=53, die_sides=109, implicit_target_a=6,
            potency_excluded='legacy rank-capped: superseded max-rank (MaxLevel implicitly uncapped would make '
            'this stronger than the single-rank bootstrap 2098 at some levels) kept only for an item_template '
            'RequiredSpell reference, same bucket as the Warlock P4 precedent for a superseded rank kept only '
            'for an item reference (PLAN P4). Not touched, not uncapped.',
        ),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    tooltip_vars=tooltip_seal_fate_1323,
    spell_icon_id=514,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 1049088, 'AttributesEx3': 1024, 'AttributesEx4': 8, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that causes damage per combo point:\r\n   1 point  : ${($m1+(($b1*1)+$AP*0.03))*$<seal>}-${($M1+(($b1*1)+$AP*0.07))*$<seal>} damage\r\n   2 points: ${($m1+(($b1*2)+$AP*0.06))*$<seal>}-${($M1+(($b1*2)+$AP*0.14))*$<seal>} damage\r\n   3 points: ${($m1+(($b1*3)+$AP*0.09))*$<seal>}-${($M1+(($b1*3)+$AP*0.21))*$<seal>} damage\r\n   4 points: ${($m1+(($b1*4)+$AP*0.12))*$<seal>}-${($M1+(($b1*4)+$AP*0.28))*$<seal>} damage\r\n   5 points: ${($m1+(($b1*5)+$AP*0.15))*$<seal>}-${($M1+(($b1*5)+$AP*0.35))*$<seal>} damage', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_1': 170.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 8519680, 'SpellClassSet': 8, 'SpellLevel': 60, 'SpellVisualID_1': 671, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


cloak_of_shadows_31224 = spell(
    id=31224,
    name='Cloak of Shadows',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=90000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-91, implicit_target_a=1, apply_aura=186, misc_value=126),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=35729),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=1),
    ],
    spell_icon_id=1933,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131104, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases chance to resist spells by $s1%.', 'BaseLevel': 46, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly removes all existing harmful spell effects and increases your chance to resist all spells by $s1% for $d.  Does not remove effects that prevent you from using Cloak of Shadows.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 65536, 'SpellClassSet': 8, 'SpellLevel': 46, 'SpellVisualID_1': 3619, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


envenom_32645 = spell(
    id=32645,
    name='Envenom',
    school=School.NATURE,
    dispel=DispelType.POISON,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=1000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_potency=0.0, cp_base_potency=44.112, cp_ap_potency=21.0, potency_kind='direct', implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER,
               misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=107, misc_value=18),
    ],
    tooltip_vars=tooltip_vile_poisons_1320,
    spell_icon_id=2237,
    notes=(
        "single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 62); RealPointsPerLevel from rank1→top rank's own top level (80, rank1 learn level ≥ 60) slope (anchor 57993, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (57993, rank 4); flat energy cost kept as-is (Rogue is Energy-based, not Mana). "
        "potency-system (PLAN P7-Rogue, F11 hard-coded-AP audit): Envenom is entirely per-dose/"
        "per-combo-point damage (SpellEffects.cpp's Rogue case: `damage *= doses; damage += "
        "AP*0.09*combo;`, no flat one-shot component), so base_potency=0.0 (explicit, not None - "
        "see lib.potency.resolve's total>0-or-base_potency-not-None check) with ALL scaling in "
        "cp_base_potency/cp_ap_potency. cp_base_potency=44.112 reproduces the old per-dose "
        "CalcValue native (118, at level 62 - SpellLevel/BaseLevel=62 (potency basis; SpellLevel is now 42 per RG0a), so the preservation target "
        "is computed at level 62 like Druid Maim's own precedent, not the generic level-60 "
        "anchor). cp_ap_potency=21.0 gives an ap_coefficient of exactly 0.09, reproducing the old "
        "hard-coded AP*0.09*combo term exactly. Together: 5*(118+0.09*1000) = 1040, matching the "
        "pre-conversion total at level 62/5 combo(doses)/1000 AP exactly. Both the doses "
        "multiplication and the AP addition are gated behind SpellPotency::HasRow() in "
        "SpellEffects.cpp (not just the AP line - see the SpellEffects.cpp comment and "
        "p7-rogue-SUMMARY.md for why both had to move together: SpellPotency::Apply() already "
        "multiplies the per-combo-point line by comboPoints internally, so leaving the old "
        "`damage *= doses` active on top would double-count the combo scaling)."
        " rogue-rework S1a A4 (section 10.7): DBC eff1 = self flat CRITICAL_CHANCE (Dashing Scoundrel, value from the Aura script's DoEffectCalcAmount; 0 without a rank) on POISON_DAMAGE_READ, finisher bit d2 b18, aura text U14 conditional, Slice and Dice line for rogues with Mutilate. Raw DurationIndex 285 untouched."
    ),
    raw_overrides={'AttributesEx': 1049088, 'AttributesEx3': 1024, 'AttributesEx4': 9, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$?s203821[Your poisons are applied more often and are more likely to critically strike.]'
                                      '?s203820[Your poisons are applied more often and are more likely to critically strike.]'
                                      '[Your poisons are applied more often.]', 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that consumes your Deadly Poison doses on the target to deal instant poison damage per dose, and increases the chance to apply your Lethal poisons by $s3% for 1 sec plus 1 sec per combo point.$?s1329[ Also applies Slice and Dice for its 5 combo point duration.][]', 'DurationIndex': 285, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': m.POISON_DAMAGE_READ[0], 'EffectSpellClassMaskB_2': m.POISON_DAMAGE_READ[1], 'EffectSpellClassMaskB_3': m.POISON_DAMAGE_READ[2], 'EffectSpellClassMaskC_3': m.LETHAL_AURA, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 8388608, 'SpellClassMask_2': m.ENVENOM_D1 | m.POISON_GROUP, 'SpellClassMask_3': m.FINISHER_GROUP, 'SpellClassSet': 8, 'SpellLevel': 42, 'SpellVisualID_1': 8144, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'TargetAuraState': 16},
)

scripted_by(envenom_32645, 'spell_rog_envenom_assassination')


dismantle_51722 = spell(
    id=51722,
    name='Dismantle',
    school=School.NORMAL,
    mechanic=3,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=278),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=254),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_DISARM),
    ],
    spell_icon_id=2908,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Disarmed.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Disarm the enemy, removing all weapons, shield or other equipment carried for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 1048576, 'SpellClassSet': 8, 'SpellLevel': 20, 'SpellVisualID_1': 11540, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)
# Only on a stock TrainerId no NPC uses; 206 is the live Rogue trainer (docs/spell_learn_level.md).
trained_by(dismantle_51722, trainer_id=206, req_level=20, money_cost=3000)


fan_of_knives_51723 = spell(
    id=51723,
    name='Fan of Knives',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=100, implicit_target_a=18, implicit_target_b=16,
               radius_yards=8.0),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=18, implicit_target_b=16, radius_yards=8.0),
    ],
    tooltip_vars=tooltip_venomous_fan_1321,
    spell_icon_id=2904,
    notes=(
        'rogue-rework RG0b A2 (shared doc "Fan of Knives", HANDOFF Known-hard 7): learn level 80 -> 24 (SpellLevel 24; '
        'BaseLevel generated), awards 1 combo point. eff0 WEAPON_PERCENT_DAMAGE weapon_potency 70 (stock bp 69), eff1 '
        'ADD_COMBO 1 on the same A 18 / B 16 radius 8 (AddComboPointGain resets per target: N targets award 1, A29). '
        'The '
        'dagger +50% hardcode (family d1 b18, 0x40000) stays on purpose: 105% with daggers, 70% otherwise. Off-hand '
        'copy 52874 (spell_linked_spell 51723 -> 52874) untouched. '
        'rogue-rework M2a (M1 AoE option B, [tune]): weapon_potency 70 -> 100 (150% with daggers through the same '
        'hardcode); the off hand 52874 (npc.csv bp 69 -> 99) and the Second Volley copies 204166 / 204167 match.'
    ),
    raw_overrides={'AttributesEx': 16, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly throw both weapons at all enemies within 8 yards, causing ${$s1*1.5*$<fanmult>}% weapon damage with daggers and ${$s1*$<fanmult>}% with other weapons. Awards 1 combo point.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'Speed': 18.0, 'SpellClassMask_2': 262144, 'SpellClassSet': 8, 'SpellLevel': 24, 'SpellVisualID_1': 12317, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)

scripted_by(fan_of_knives_51723, 'spell_rog_fan_of_knives')

tricks_of_the_trade_57934 = spell(
    id=57934,
    name='Tricks of the Trade',
    school=School.NORMAL,
    attributes=33882128,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=15,
    mana_cost_pct=0,
    range_yards=20.0,
    duration_ms=30000,
    effects=[
        Effect(type=130, base_points=99, implicit_target_a=57),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3413,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 67634208, 'AttributesEx3': 256, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'The threat caused by your next damaging attack and all actions taken for $57933d afterwards will be transferred to the target.  In addition, all damage caused by the target is increased by $57933s1% during this time.', 'BaseLevel': 56, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The current party or raid member becomes the target of your Tricks of the Trade.  The threat caused by your next damaging attack and all actions taken for $57933d afterwards will be transferred to the target.  In addition, all damage caused by the target is increased by $57933s1% during this time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 340, 'SpellClassMask_2': 131072, 'SpellClassSet': 8, 'SpellLevel': 56, 'SpellVisualID_1': 12786, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


instant_poison_viii_57967 = spell(
    id=57967,
    name='Instant Poison VIII',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=3768),
    ],
    spell_icon_id=247,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 73, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$57964m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 8', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 73, 'SpellVisualID_1': 12720, 'Targets': 16},
)


instant_poison_ix_57968 = spell(
    id=57968,
    name='Instant Poison IX',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=3769),
    ],
    spell_icon_id=247,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 79, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$57965m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 79, 'SpellVisualID_1': 12720, 'Targets': 16},
)


deadly_poison_viii_57972 = spell(
    id=57972,
    name='Deadly Poison VIII',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=599, misc_value=3770),
    ],
    spell_icon_id=513,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 76, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $57972h% chance of poisoning the enemy for ${$57969m1*4+0.12*$AP} Nature damage over $57969d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 8', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 76, 'SpellVisualID_1': 12720, 'Targets': 16},
)


deadly_poison_ix_57973 = spell(
    id=57973,
    name='Deadly Poison IX',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=599, misc_value=3771),
    ],
    spell_icon_id=513,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 80, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $57973h% chance of poisoning the enemy for ${$57970m1*4+0.12*$AP} Nature damage over $57970d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 80, 'SpellVisualID_1': 12720, 'Targets': 16},
)


wound_poison_vi_57977 = spell(
    id=57977,
    name='Wound Poison VI',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=3772),
    ],
    spell_icon_id=1496,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 72, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy, causing ${$57974m2+0.04*$AP} Nature damage and reducing all healing effects used on them by $57974s1% for $57974d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 8, 'SpellLevel': 72, 'SpellVisualID_1': 12720, 'Targets': 16},
)


wound_poison_vii_57978 = spell(
    id=57978,
    name='Wound Poison VII',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=3773),
    ],
    spell_icon_id=1496,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 78, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy, causing ${$57975m2+0.04*$AP} Nature damage and reducing all healing effects used on them by $57975s1% for $57975d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 8, 'SpellLevel': 78, 'SpellVisualID_1': 12720, 'Targets': 16},
)


anesthetic_poison_ii_57982 = spell(
    id=57982,
    name='Anesthetic Poison II',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=3774),
    ],
    spell_icon_id=110,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 77, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.  Each strike has a $57982h% chance of poisoning the enemy which instantly inflicts $57981s1 Nature damage and dispels $57981s2 Enrage effect, but causes no additional threat.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_2': 16, 'SpellClassSet': 8, 'SpellLevel': 77, 'SpellVisualID_1': 12720, 'Targets': 16},
)


mutilate_1329 = spell(
    id=1329,
    name='Mutilate',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=45,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.ADD_COMBO_POINTS, base_points=1, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=mutilate_mh_203827.id),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=mutilate_oh_203828.id),
    ],
    spell_icon_id=2117,
    notes=(
        'single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1→level-60 slope (anchor 34412, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48666, rank 6); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)'
        'rogue-rework S1a A4 (WP-BRIEF R3, section 10.2): cost 60 -> 45, triggers the new hands 203827 / 203828 (the stock 5374 / 27576 stay in rogue_trigger_spells.py, unreferenced), EquippedItemSubclass 41105 (any one-hander; REQ_OFFHAND kept in Ex3), BaseLevel / SpellLevel 40 -> 20, stock SpellDescriptionVariableID 172 dropped, tooltip verbatim from the doc. spell_rog_mutilate -> spell_rog_mutilate_rework.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 1048576, 'AttributesEx3': 16843776, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly attacks with both weapons for $203827s1% normalized weapon damage plus an '
                                 'additional ' + pot_text(mutilate_mh_203827, effect=2, variant='avg') + ' with each weapon. '
                                 'Damage is increased by 15% for each of your Poisons on the target. Awards $s1 combo points.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': _ONE_HAND_MASK, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 2097152, 'SpellClassSet': 8, 'SpellLevel': 20, 'SpellVisualID_1': 7913, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)

# U20: Mutilate's stock script is replaced by the dual-strike resolver (WP-BRIEF section 8).
unbind_script(-1329, 'spell_rog_mutilate')
scripted_by(mutilate_1329, 'spell_rog_mutilate_rework')


hemorrhage_16511 = spell(
    id=16511,
    name='Hemorrhage',
    school=School.NORMAL,
    attributes=67436560,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=15000,
    effects=[
        Effect(type=121, die_sides=0, implicit_target_a=6),
        Effect(type=31, base_points=109, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=12, points_per_level=0.5333333333333333, implicit_target_a=6, apply_aura=14, misc_value=1),
    ],
    spell_icon_id=153,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1→level-60 slope (anchor 17348, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48660, rank 5); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1026, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases damage taken by $s3.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'An instant strike that deals $s2% weapon damage (${$m2*1.45}% if a dagger is equipped) and causes the target to hemorrhage, increasing any Physical damage dealt to the target by up to $<bonus>.  Lasts $n charges or $d.  Awards 1 combo point.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcCharges': 10, 'ProcTypeMask': 139944, 'RangeIndex': 2, 'SpellClassMask_1': 41943040, 'SpellClassSet': 8, 'SpellDescriptionVariableID': 64, 'SpellLevel': 30, 'SpellVisualID_1': 5119, 'StanceBarOrder': 4294967295, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


adrenaline_rush_13750 = spell(
    id=13750,
    name='Adrenaline Rush',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=110, misc_value=3),
    ],
    spell_icon_id=235,
    notes=(
        'pulled from existing data. rogue-rework S3a A4 (section 10.10, U74): cooldown 180 s -> 120 s; OFF the global '
        'cooldown (StartRecoveryCategory / StartRecoveryTime 0); aura 110 misc 3 +100% (stock) unchanged; the extra '
        'combo point per builder cast is C++ (HasAura 13750 or 203996, ADRENALINE_RUSH_EXTRA_POINTS); stock AttributesEx kept '
        '(breaks Stealth like stock, user ruling 2026-10-27); stock family bit d1 b7 kept (ADRENALINE_RUSH_D1); '
        'tooltip and aura text = the doc, verbatim. Exclusive with Celerity\'s copy 203996 through '
        'spell_group 1288 (A3).'
    ),
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Energy regeneration increased. Your builders award more combo points.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': f'Increases your energy regeneration rate by $s1% and causes your combo point builders to award {_c(ADRENALINE_RUSH_EXTRA_POINTS)} additional combo point for $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 128, 'SpellClassSet': 8, 'SpellVisualID_1': 8996, 'StartRecoveryCategory': 0, 'StartRecoveryTime': 0},
)


blade_flurry_13877 = spell(
    id=13877,
    name='Blade Flurry',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1477,
    notes=(
        'pulled from existing data. rogue-rework S3a A4 (section 10.4, U59): the stock +20% attack speed (aura 138) is '
        'gone: eff0 is a self DUMMY marker (the C++ copier reads HasAura(13877)); 12 s, 30 s cooldown, no energy cost, '
        'GCD 133 / 1000 kept; raw ProcTypeMask 0 / ProcChance 101 (the stock proc fields 20 / 100 would make the core '
        'proc-check a marker); raw AttributesEx 0x20 (self buff, does not break Stealth); the stock family bits '
        '(d0 b30 | d1 b11) kept as they are (WP-BRIEF R24); tooltip and aura text = the doc, verbatim, the numbers from '
        'the BLADE_FLURRY_* consts. spell_rog_blade_flurry is unbound from 13877 only (the NPC ids keep it) and '
        'spell_rog_blade_flurry_rework bound.'
    ),
    raw_overrides={'AttributesEx': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your attacks strike nearby enemies.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': f"Your attacks also strike up to {_c(BLADE_FLURRY_EXTRA_TARGETS)} additional nearby enemies for {_c(BLADE_FLURRY_COPY_PCT)}% of the damage dealt. Lasts $d. Can't be active at the same time as Sweeping Strikes, and shares a cooldown with it. Usable while shapeshifted.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassMask_1': 1073741824, 'SpellClassMask_2': 2048, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 211, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)

unbind_script(13877, 'spell_rog_blade_flurry')   # 13877 only: the NPC ids 33735 / 51211 / 65956 keep the stock script
scripted_by(blade_flurry_13877, 'spell_rog_blade_flurry_rework')


cold_blood_14177 = spell(
    id=14177,
    name='Cold Blood',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER,
               misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER,
               misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER,
               misc_value=SpellModOp.RANGE),
    ],
    spell_icon_id=32,
    notes=(
        'pulled from existing data'
        'rogue-rework S1a A4 (section 10.8, U17): attributes 33882128 -> 327696 (COOLDOWN_ON_EVENT stripped), 180 s cooldown unchanged; eff0 flat CRITICAL_CHANCE +100, eff1 pct DAMAGE +20, eff2 flat RANGE +5 (eff0 / eff1 on COLD_BLOOD_READ, eff2 on COLD_BLOOD_RANGE_READ = + Mutilate parent d1 b21 + Kingsbane parent d2 b22, S1a review M1); ProcTypeMask 87376 / ProcCharges 1 / ProcChance 100 kept; tooltip and aura text verbatim; after-buff 203833 text reads $203833s1 / $203833d. '
        'S3a A4 (U65): readers widened with Between the Eyes d2 b5 and Blade Rush d2 b15 (COLD_BLOOD_READ_S3 on eff0 / eff1, COLD_BLOOD_RANGE_READ_S3 on eff2).'
    ),
    raw_overrides={'AttributesEx': 32, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next ability is a critical strike.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, your next direct damage Rogue ability has $s1% increased critical strike chance, '
                                 '$s2% increased damage and is usable from ${$s3+5} yards. When consumed you will gain '
                                 '$203833s1% melee and ranged critical strike chance for $203833d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, **m.read_mask_keys(0, m.COLD_BLOOD_READ_S3), **m.read_mask_keys(1, m.COLD_BLOOD_READ_S3), **m.read_mask_keys(2, m.COLD_BLOOD_RANGE_READ_S3), 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassMask_2': 64, 'SpellClassSet': 8, 'SpellVisualID_1': 4371},
)

unbind_script(14177, 'spell_rog_cold_blood')
scripted_by(cold_blood_14177, 'spell_rog_cold_blood_rework')


premeditation_14183 = spell(
    id=14183,
    name='Premeditation',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=20000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.ADD_COMBO_POINTS, base_points=1, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=148),
    ],
    spell_icon_id=98,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268567584, 'AttributesEx3': 196608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When used, adds $s1 combo points to your target.  You must add to or use those combo points within $d or the combo points are lost.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ShapeshiftMask': 536870912, 'SpellClassMask_2': 32, 'SpellClassSet': 8, 'SpellLevel': 20},
)


preparation_14185 = spell(
    id=14185,
    name='Preparation',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=480000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=207,
    notes=(
        'pulled from existing data. rogue-rework S2a A4 (R5): tooltip = the doc\'s, verbatim; effects, cooldown (8 min), '
        'GCD and the reset list (script spell_rog_preparation) unchanged.'
    ),
    raw_overrides={'AttributesEx': 32, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, immediately finishes the cooldown on your Evasion, Sprint, Vanish, Cold Blood and Shadowstep.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 4096, 'SpellClassSet': 8, 'SpellVisualID_1': 3259, 'StanceBarOrder': 4294967295, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


riposte_14251 = spell(
    id=14251,
    name='Riposte',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=10,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=30000,
    effects=[
        Effect(type=31, base_points=149, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, mechanic=8, implicit_target_a=6, apply_aura=138),
        Effect(type=EffectType.ADD_COMBO_POINTS, base_points=1, implicit_target_a=6),
    ],
    spell_icon_id=278,
    notes=(
        'pulled from existing data. rogue-rework S3a A4 (section 10.6, U65 / U69): eff2 ADD_COMBO_POINTS bp 1 = 2 '
        'combo points (was 1); family mask = RIPOSTE_CLASS_S3 (d1 b8 stock | d2 b19 direct-builder group, so Seal Fate '
        '/ Lethality / the Blade Twisting and Surprise Attacks readers reach it), written whole through '
        'class_mask_keys; the 150% weapon hit, the 20% slow (30 s), 10 energy and 6 s cooldown are stock; the slow '
        'joins stock spell_group 1059 (attack-speed slows: the strongest applies, no stacking with Thunder Clap); '
        'tooltip and debuff text = the doc, verbatim (Opportunity and the dodge lighting are C++: '
        'spell_rog_riposte, RoguePlayerScript::OnPlayerIsClass).'
    ),
    raw_overrides={'AttributesEx': 131584, 'AttributesEx4': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attack speed reduced.', 'CasterAuraState': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "A strike that becomes active after you dodge or parry an attack. Deals $s1% weapon damage, slows the target's melee attack speed by $s2% for $d, awards $s3 combo points and grants Opportunity.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, **m.class_mask_keys(m.RIPOSTE_CLASS_S3), 'SpellClassSet': 8, 'SpellVisualID_1': 3799, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)

scripted_by(riposte_14251, 'spell_rog_riposte')   # S3: Opportunity, Improved Riposte's cleave
spell_group(1059, riposte_14251)                  # stock attack-speed-slow group (EXCLUSIVE_SAME_EFFECT)


ghostly_strike_14278 = spell(
    id=14278,
    name='Ghostly Strike',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=40,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=100, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, trigger_spell=ghostly_veil_203723.id, implicit_target_a=1),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=596,
    notes=(
        'rogue-rework RG0b A2 (shared doc "Ghostly Strike", HANDOFF Known-hard 7, C5): the Subtlety talent becomes a '
        'baseline trainer spell at 10 (SpellLevel 10; talent 303 retired by rogue_talents.py). Cooldown 20 s -> 0, '
        'duration 7 s -> 0 (the self aura is gone: eff1 is now TRIGGER_SPELL A 1 -> Ghostly Veil 203723, +10% dodge '
        'for '
        '5 melee attacks taken, fired in the LAUNCH phase so it lands on every cast, hit or miss). eff0 '
        'WEAPON_PERCENT_DAMAGE weapon_potency 100 (no flat part, no dagger bonus), eff2 ADD_COMBO 1. Family d0 '
        '0x44000000 -> 0x40000000: b26 (0x4000000, the dagger +50% hardcode) dropped, b30 kept. Cost 40 (stock).'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A strike that deals $s1% weapon damage and increases your dodge chance by $203723s1% for your next $203723n melee attacks taken. Awards 1 combo point.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': m.GHOSTLY_STRIKE, 'SpellClassMask_3': m.DIRECT_BUILDER_GROUP | m.GHOSTLY_STRIKE_ID, 'SpellClassSet': 8, 'SpellLevel': 10, 'SpellVisualID_1': 4159, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


shadowstep_36554 = spell(
    id=36554,
    name='Shadowstep',
    school=School.NORMAL,
    attributes=536870928,
    category=1206,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=10,
    mana_cost_pct=0,
    range_yards=25.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=203726),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=69, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=2363,
    notes=(
        'pulled from existing data. rogue-rework S2a A4 (S2-HANDOFF 10.12, C4): eff0 TRIGGER_SPELL 36563 (the 20% '
        'damage buff + teleport) -> 203726 (Ambush Teleport: the same TELEPORT_UNITS behind the target, own hidden '
        'row), eff1 TRIGGER_SPELL 44373 (the 50% threat reduction) removed, eff2 (speed aura 31 bp 69 = +70%, 3 s) '
        'kept. Cost 10 energy, 30 s, 25 yd, off the GCD, family d1 b9 and ExcludeTargetAuraSpell kept; tooltip and '
        'aura text verbatim from the doc. The stale eff2 class-mask twins (C_1 772 / C_2 2) are inert on an aura 31.'
    ),
    raw_overrides={'AttributesEx': 1056, 'AttributesEx2': 268435456, 'AttributesEx3': 196608, 'AttributesEx6': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed increased.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Step through the shadows to appear behind your target and gain $s3% increased movement speed for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_1': 772, 'EffectSpellClassMaskC_2': 2, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 65219, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'SpellClassMask_2': 512, 'SpellClassSet': 8, 'SpellLevel': 1},
)


hunger_for_blood_51662 = spell(
    id=51662,
    name='Hunger For Blood',
    school=School.NORMAL,
    dispel=9,
    mechanic=31,
    attributes=2424848,
    cast_time_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    cooldown_ms=120000,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER,
               misc_value=SpellModOp.ACTIVATION_TIME),
    ],
    spell_icon_id=2961,
    notes=(
        'pulled from existing data'
        "rogue-rework S1a A4 (section 10.5): self buff 10 s, pct ACTIVATION_TIME -50 on HUNGER_FOR_BLOOD_READ, Dispel Enrage kept, off the GCD (0 / 0), no cost, 120 s cooldown, no DUMMY, no TargetAuraState, visible with the doc's aura text. "
        "S2a A4 (R7): reader mask = HUNGER_FOR_BLOOD_READ_S2 (d2 += b12, the Hemorrhage bleed) through m.read_mask_keys(0, ...)."
    ),
    raw_overrides={'AttributesEx': 1056, 'AttributesEx3': 64, 'AttributesEx6': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Enraged. Your poisons and bleeds deal damage faster.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Enrages you, causing the periodic damage of your poisons and bleeds to tick twice as fast for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, **m.read_mask_keys(0, m.HUNGER_FOR_BLOOD_READ_S2), 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 16777216, 'SpellClassSet': 8, 'SpellVisualID_1': 11821, 'StartRecoveryCategory': 0, 'StartRecoveryTime': 0},
)

scripted_by(hunger_for_blood_51662, 'spell_rog_hunger_for_blood')


killing_spree_51690 = spell(
    id=51690,
    name='Killing Spree',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=10.0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=226, amplitude=500, misc_value=3),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=18, implicit_target_b=16, radius_yards=10.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=263),
    ],
    spell_icon_id=2907,
    notes=(
        'pulled from existing data. rogue-rework S3a A4 (section 10.5, U62, WP-BRIEF R6): now a FINISHER at 25 energy '
        '(was free), 2 min cooldown and GCD 133 / 1000 stock; raw AttributesEx = stock 0x400 | 0x400000 '
        '(FINISHING_MOVE_DURATION) = 0x400400 and NO 0x20 (the core ORs ALLOW_WHILE_STEALTHED, SpellInfoCorrections); '
        'DurationIndex 39 (2 s, min = max) and AttributesEx5 0x200 (START_PERIODIC_AT_APPLY) kept: the script '
        'sets the real duration = points x 500 ms in AfterEffectApply (strikes = 1 + points); the effects keep the stock '
        'no-explicit-target frame (eff0 PERIODIC_DUMMY 500 ms, eff1 DUMMY A 18 / B 16, eff2 aura 263); the +20% damage '
        'link 61851 is removed (unlink_spell); family mask = KILLING_SPREE_CLASS_S3 (d1 b23 stock | d2 b18 finisher '
        'group) written whole; tooltip = the doc, verbatim, hop range from KILLING_SPREE_HOP_RANGE_YD; the aura text '
        'keeps the stock first line without the removed +damage sentence. Script rebound to '
        'spell_rog_killing_spree_rework.'
    ),
    raw_overrides={'AttributesEx': 4195328, 'AttributesEx2': 268435456, 'AttributesEx3': 197633, 'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attacking an enemy every $t1 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': f'Finishing move that steps through the shadows from enemy to enemy within {_c(KILLING_SPREE_HOP_RANGE_YD)} yards, attacking with both weapons for $57841s1% weapon damage. Strikes once, plus once per combo point. Can hit the same target multiple times. Cannot hit invisible or stealthed targets. If you have Titan\'s Grip learned, this ability deals 25% less damage.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, **m.class_mask_keys(m.KILLING_SPREE_CLASS_S3), 'SpellClassSet': 8, 'SpellVisualID_1': 12981, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)

unbind_script(51690, 'spell_rog_killing_spree')
scripted_by(killing_spree_51690, 'spell_rog_killing_spree_rework')
unlink_spell(51690, 61851, 2)   # the stock +20% damage done aura


shadow_dance_51713 = spell(
    id=51713,
    name='Shadow Dance',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=275),
        Effect(type=EffectType.APPLY_AURA, base_points=74, implicit_target_a=1, apply_aura=AuraType.MOD_POWER_REGEN_PERCENT,
               misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=30),
    ],
    spell_icon_id=2959,
    notes=(
        'rogue-rework S2a A4 (S2-HANDOFF 10.2, WP-BRIEF R6): the stock level-60+ capstone becomes the level 20 Subtlety '
        'baseline. Duration 6 s -> 8 s, cooldown 60 s -> 30 s, no cost, off the GCD (StartRecoveryCategory absent = 0), '
        'BaseLevel / SpellLevel 60 -> 20. eff0 aura 275 (the stock "ignore stealth requirement" mask) now reads only '
        'SHADOWED_HIDDEN_READ (Ambush + Garrote + Cheap Shot): Sap / Pick Pocket / Disarm Trap and the stale 0x2020 / '
        'B / C twins are gone (Sap needs true stealth). eff1 (free in the stock row) = aura 110 MOD_POWER_REGEN_PERCENT '
        'misc 3 (energy) bp 74 / die 1 = +75% (multiplies with Energy Haste 203700, StatSystem.cpp:974-980). eff2 '
        'MOD_SHAPESHIFT misc 13 -> 30 (form 30 = Stealth\'s: Ambush / Garrote carry ShapeshiftMask 0x20000000; the rogue '
        'family is exempt from "remove other shapeshift", SpellAuraEffects.cpp:2076 / :2151). No MOD_STEALTH: Shadowed is '
        'Hidden without being stealthed. Raw AttributesEx stays 0x20400 on purpose (R6): casting Shadow Dance from true '
        'Stealth breaks the Stealth, as designed. Own family mask d1 b25 kept; StanceBarOrder 1 and the stock visual '
        '11827 kept. Cooldown reductions (finishers, Slaughter, Executioner) are C++ (Rogue::ReduceCooldown); '
        'Cooldown Haste applies (30 s >= the 30 s floor). Tooltip and aura text verbatim from the doc.'
    ),
    raw_overrides={'AttributesEx': 132096, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Shadowed. You are Hidden and regenerate energy faster.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Enter the Shadow Dance for $d, becoming Shadowed. While Shadowed you are Hidden, so you can use Ambush, Garrote and Cheap Shot, and your energy regenerates $s2% faster. Your finishing moves reduce the remaining cooldown of Shadow Dance by 1 sec per combo point spent.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, **m.read_mask_keys(0, m.SHADOWED_HIDDEN_READ), **m.clear_mask_keys(1, 2), 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 33554432, 'SpellClassSet': 8, 'SpellLevel': 20, 'SpellVisualID_1': 11827, 'StanceBarOrder': 1},
)
