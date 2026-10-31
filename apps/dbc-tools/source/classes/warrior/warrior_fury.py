"""
Warrior - S3 Fury delta, data half owned by agent A2a: the mechanics spells 204630-204652, 204679 and 204680, the
first declaration of Bloodthirst's heal buff 23885 (its legacy npc.csv line is deleted in the same change), every S3
`scripted_by` / `unbind_script` / `remove_spell_proc` / `procs_on` on a stock or legacy id that is not a Fury talent
rank, and the `const()` rows the Fury C++ reads through the generated WarriorData.h. The talent rank rows
204653-204678 and the first-declared stock rank rows (Cruelty, Unbridled Wrath, Blood Craze, Enrage, Flurry) are
warrior_fury_ranks.py (A2b); the talent grid, Rampage / Bloodthirst / Death Wish / Recklessness spell rows and the
shouts are warrior_talents.py / warrior_spells.py (A3).

Source of truth: docs/reworks/warrior-fury-rework.md (aura texts verbatim),
.agents/plans/warrior-rework/warrior-rework.S3-WP-BRIEF.md (frozen variable names, class names, rulings; the brief
wins), warrior-rework.S3-HANDOFF.md (D3-D39 bold defaults, C1-C20) and the two 0-verify files
(warrior-rework.S3-0VERIFY-A.md / -B.md). Row shapes copy warrior_arms.py (S2: the charged buffs, the script-cast
strikes, the stock-row first declaration) and the P0 spike (p0-spike-ref/warrior_p0_spike.py: Rampage, the meter,
Death Wish).

Visibility (D38): the buffs the doc says "Shows a buff: yes" carry no PASSIVE 0x40 / DO_NOT_DISPLAY 0x80 (Attributes 0);
the helper spells carry 0x80 only. Every SpellMod effect names its dword in the spell's own
EffectSpellClassMask{A,B,C}_{1,2,3} columns (letter = effect index, number = dword) and every row is
SpellClassSet 4: the aura-262 / aura-280 carriers rely on it (0-verify A item 7, an unfamiliar set would apply them to
every class). The charged buffs (204637, 204638, 204647, 204649, 204652) have ProcTypeMask 0 and NO spell_proc row:
they are dropped once per Spell by Player::RemoveSpellMods, or by script (C3, C4). Shredding Blows' buffs are the one
exception (aura 280 is not a trigger aura, so an explicit consuming row is the only consumer, B-R3).

Bindings use raw ids, never imports of variables from the sibling files, so this file has no import cycle with the
rank files A1, A2b and A3 are editing.
"""

from lib.dsl import AuraType, Effect, EffectType, PowerType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import (
    bonus_coefficients, const, custom_attr, procs_on, remove_spell_proc, scripted_by, spell, spell_group_rule,
    unbind_script,
)

from . import _masks
from .warrior_shared import SPELL_ATTR0_CU_AURA_CANNOT_BE_SAVED, SPELL_ATTR3_ALLOW_AURA_WHILE_DEAD


# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h, decoded) ----
_ATTR0_IS_ABILITY = 0x10                    # SPELL_ATTR0_ABILITY
_ATTR0_PASSIVE = 0x40                       # never on a visible buff (D38)
_ATTR0_DO_NOT_DISPLAY = 0x80                # hidden helper (D38); never on a visible buff
_ABILITY_ATTRIBUTES = 0x50010               # stock warrior strike buttons: IS_ABILITY + two stock bits
_ATTR_EX_STRIKE = 0x8000200                 # stock Mortal Strike's AttributesEx (P0 Rampage frame)
_ATTR3_STRIKE_FRAME = 0x400                 # stock Mortal Strike's AttributesEx3 (P0 Rampage frame)
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000      # SPELL_ATTR3_SUPPRESS_CASTER_PROCS: the hit raises no caster procs
_ATTR3_REQUIRES_OFF_HAND_WEAPON = 0x1000000  # SPELL_ATTR3_REQUIRES_OFF_HAND_WEAPON: m_attackType = OFF_ATTACK
_ATTR4_SUPPRESS_WEAPON_PROCS = 0x800000     # SPELL_ATTR4_SUPPRESS_WEAPON_PROCS: no weapon enchant / item procs

# ---- Auras / targets / misc values ----
_SPELLFAMILY_WARRIOR = 4
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_MECHANIC_SILENCE = 9
_SCHOOLS_ALL = 127                          # aura 79 / 87 misc 127: every school
_SCHOOL_PHYSICAL = 1                        # aura 79 misc 1
_AURA_MOD_ARMOR_PENETRATION_PCT = 280       # SPELL_AURA_MOD_ARMOR_PENETRATION_PCT (Shredding Blows)
_POWER_RAGE_MISC = 1
_SCRIPT_CAST_RANGE = 50000.0                # a spell a script casts at another unit: a real range (bug log 570)
_WEAPON_CLASS = 2
_WEAPON_SUBCLASSES = 173555                 # stock strike buttons' EquippedItemSubclass
_DMG_CLASS_MELEE = 2
_PREVENTION_PACIFY = 2
_GCD_CATEGORY = 133
_GCD_MS = 1500
_RANGE_INDEX_MELEE = 2

# ---- SpellClassSet 4 family bits the Fury rows carry or read (0-verify A item 3) ----
_HEROIC_STRIKE_D0 = 0x40
_CLEAVE_D0 = 0x400000
_SLAM_D0 = 0x200000
_EXECUTE_D0 = 0x20000000
_BLOODTHIRST_D1 = 0x400
_WHIRLWIND_D1 = 0x4

# ---- Stock icons / visuals (borrowed, V replaces: D45) ----
_ICON_RAMPAGE = 2006                        # stock 29801
_ICON_ENRAGE_TALENT = 95                    # stock Enrage talent's icon (the meter)
_ICON_BERSERKER_RAGE = 1465                 # the Enrage buff (its glow is Berserker Rage's visual 47)
_ICON_BLOODTHIRST = 38
_ICON_DEATH_WISH = 169
_ICON_RECKLESSNESS = 138
_ICON_FLURRY = 108
_ICON_BLOOD_CRAZE = 215
_ICON_SLAM_PROC = 2767                      # stock Slam! (the Bloodsurge buff)
_ICON_SUDDEN_DEATH = 1989
_ICON_TITANS_GRIP = 2750
_ICON_BLOODRAGE = 86
_ICON_SUNDER = 565
_ICON_HEROIC_STRIKE = 856
_ICON_CLEAVE = 277
_ICON_WHIRLWIND = 83
_SV_BLOODTHIRST = 372
_SV_HEROIC_STRIKE = 39
_SV_CLEAVE = 219
_SV_BERSERKER_RAGE = 47
_SV_BLOODSURGE = 10701                      # stock Slam!'s proc look

# ---- Index rows (existing only, no row minted: D39) ----
_DURATION_2S = 2000                         # SpellDuration 39
_DURATION_3S = 3000                         # 27
_DURATION_5S = 5000                         # 28
_DURATION_8S = 8000                         # 31
_DURATION_10S = 10000                       # 1
_DURATION_12S = 12000                       # 29
_DURATION_15S = 15000                       # 8
_DURATION_INFINITE = 21


def _raw(description, aura_description=None, level=None, **extra):
    """Per-spell defaults of the Fury kit plus `extra` raw columns (applied last): family 4, no equipment requirement,
    instant cast, chain amplitudes 1.0 (a 0 makes a second target take nothing), `level` sets BaseLevel and
    SpellLevel together (the potency anchor and the trainer-level lint)."""
    raw = {
        'SpellClassSet': _SPELLFAMILY_WARRIOR,
        'EquippedItemClass': -1,
        'CastingTimeIndex': 1,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'SpellPriority': 50,
        'Description_Lang_enUS': description,
    }
    if level is not None:
        raw['BaseLevel'] = level
        raw['SpellLevel'] = level
    if aura_description is not None:
        raw['AuraDescription_Lang_enUS'] = aura_description
    raw.update(extra)
    return raw


def _fury(spell_id, name, effects, icon, notes, raw, *, attributes=0, rage=0, range_yards=None, cooldown_ms=0,
          duration_ms=None, mechanic=0):
    """Every non-rank Fury spell: physical, instant, rage cost if any, no category, raw index columns in `raw`.
    `duration_ms=None` is the permanent SpellDuration row (index 21)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, mechanic=mechanic, attributes=attributes, category=0,
        cast_time_ms=0, cooldown_ms=cooldown_ms, category_cooldown_ms=0, power_type=PowerType.RAGE,
        mana_cost=rage * 10, mana_cost_pct=0, range_yards=range_yards, duration_ms=duration_ms, effects=effects,
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _self_aura(aura, **kwargs):
    return Effect(type=EffectType.APPLY_AURA, apply_aura=aura, implicit_target_a=_TARGET_UNIT_CASTER, **kwargs)


def _spellmod(aura, op, base_points, **kwargs):
    """ADD_FLAT_MODIFIER / ADD_PCT_MODIFIER on the caster; the family-bit mask goes in the spell's
    EffectSpellClassMask{A,B,C}_{1,2,3} raw column (letter = effect index, number = dword)."""
    return _self_aura(aura, base_points=base_points, misc_value=int(op), **kwargs)


def _weapon_strike(percent, target=_TARGET_UNIT_TARGET_ENEMY, **kwargs):
    return Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=float(percent), implicit_target_a=target,
                  **kwargs)


def _weapon_flat(potency, target=_TARGET_UNIT_TARGET_ENEMY):
    """Heroic Strike / Cleave's flat part on the stock type-58 carrier (warrior_spells.py 78 / 845: 12 / 12 potency)."""
    return Effect(type=EffectType.WEAPON_DAMAGE, sp_potency=potency, potency_kind='direct', time_basis_ms=_GCD_MS,
                  implicit_target_a=target)


# =====================================================================================================================
# 204630 Rampage (the castable)  -- D7, doc "Rampage"
# =====================================================================================================================
# The talent 1659 rank (A3: player_castable=True, SLA 30855, Flags 1). The P0 spike shape (p0_rampage_204891, PASSED):
# the strike-button frame (Attributes 0x50010, AttributesEx 0x8000200, AttributesEx3 0x400, melee range index 2, weapon
# class 2 / 173555, FacingCasterFlags 1, pacify prevention), DmgClass melee so the cast raises exactly one CAST-phase
# melee event (0-verify B item 6; the HIT event is NO_DMG_HEAL), GCD 133 / 1500, 60 rage, RecoveryTime 10000 with
# Category 0, SpellLevel = BaseLevel 50. eff0 DUMMY on the enemy (no damage: the four strikes are the script's). The
# carrier is d2 b2 ONLY (never b3: Recklessness' crit mod and its CAST row must not reach the parent; the script's
# DropCharge is the only consumer, B-R1). Icon 2006 (stock 29801).
rampage_fury_204630 = _fury(
    204630, 'Rampage',
    [Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    _ICON_RAMPAGE,
    'warrior-rework S3 A2a (D7, doc "Rampage"): the castable, talent 1659\'s rank. Strike-button frame (P0 '
    'p0_rampage_204891): Attributes 0x50010, AttributesEx 0x8000200, AttributesEx3 0x400, melee range (index 2), '
    'weapon '
    'class 2 / 173555, FacingCasterFlags 1, DmgClass melee (one CAST-phase melee event per press), GCD 133 / 1500, 60 '
    'rage [fixed], RecoveryTime 10000 [fixed] with Category 0, SpellLevel = BaseLevel 50. eff0 DUMMY on the enemy. '
    'SpellClassMask_3 = 0x4 (d2 b2 only, never b3). Icon 2006. spell_warr_rampage_fury runs the four strikes.',
    _raw('Strike the target 4 times in quick succession, alternating main hand and off hand, each strike dealing 185% '
         'weapon damage. While you are Enraged, Rampage\'s damage is increased by your Enrage bonus a second time.',
         level=50, RangeIndex=_RANGE_INDEX_MELEE, FacingCasterFlags=1, DefenseType=_DMG_CLASS_MELEE,
         PreventionType=_PREVENTION_PACIFY, EquippedItemClass=_WEAPON_CLASS, EquippedItemSubclass=_WEAPON_SUBCLASSES,
         AttributesEx=_ATTR_EX_STRIKE, AttributesEx3=_ATTR3_STRIKE_FRAME, SpellClassMask_3=_masks.RAMPAGE,
         StartRecoveryCategory=_GCD_CATEGORY, StartRecoveryTime=_GCD_MS, DurationIndex=_DURATION_INFINITE),
    attributes=_ABILITY_ATTRIBUTES, rage=50, range_yards=5.0, cooldown_ms=10000,
)

# =====================================================================================================================
# 204631 / 204632 Rampage strikes (main hand, off hand)  -- D7 / D8
# =====================================================================================================================
# WEAPON_PERCENT_DAMAGE 180% per strike [tune] (D8, handoff Q2: per-rage parity with Heroic Strike at 60 rage; the doc
# table still says 120%). Hidden, triggered-only, DmgClass melee (each strike rolls its own crit), 50000 yd and no
# facing flag (a script cast, S2-REVIEW finding 2, 0-verify A difference 6), EquippedItemClass -1 (the cast-time
# off-hand weapon check is skipped for class -1, so the script's HasOffhandWeaponForAttack guard is the only gate,
# B-R2), carrier d2 b2 ONLY (never b3: Recklessness' crit rides the snapshot 204679, Impale reads 0xF), AttributesEx3
# SUPPRESS_CASTER_PROCS + AttributesEx4 SUPPRESS_WEAPON_PROCS (Sweeping never copies a strike and nothing procs per
# strike). The off-hand strike adds AttributesEx3 REQUIRES_OFF_HAND_WEAPON (m_attackType = OFF_ATTACK: off-hand weapon,
# Dual Wield Specialization). Bloodthirst's impact (visual 372). SpellLevel 1 (the S2 script-strike precedent).
def _rampage_strike(spell_id, hand, extra_ex3, notes_hand):
    return _fury(
        spell_id, 'Rampage',
        [_weapon_strike(185)],
        _ICON_RAMPAGE,
        'warrior-rework S3 A2a (D7 / D8): the Rampage ' + hand + ' strike, cast triggered by spell_warr_rampage_fury '
        '(0 / 330 / 660 / 1000 ms). WEAPON_PERCENT_DAMAGE 180% [tune], ' + notes_hand + ' DmgClass melee, hidden '
        '(0x80), 50000 yd, no facing flag, EquippedItemClass -1 (the script guard HasOffhandWeaponForAttack is the '
        'only off-hand gate), SpellClassMask_3 = 0x4 (d2 b2 only), AttributesEx3 SUPPRESS_CASTER_PROCS' + extra_ex3[1]
        + ', AttributesEx4 SUPPRESS_WEAPON_PROCS, SpellLevel 1, visual 372.',
        _raw('Strike the target with your ' + hand + ' weapon.', level=1, DefenseType=_DMG_CLASS_MELEE,
             PreventionType=_PREVENTION_PACIFY, AttributesEx3=extra_ex3[0], AttributesEx4=_ATTR4_SUPPRESS_WEAPON_PROCS,
             SpellClassMask_3=_masks.RAMPAGE, SpellVisualID_1=_SV_BLOODTHIRST, DurationIndex=_DURATION_INFINITE),
        attributes=_ATTR0_DO_NOT_DISPLAY, range_yards=_SCRIPT_CAST_RANGE,
    )


rampage_strike_mh_204631 = _rampage_strike(
    204631, 'main-hand', (_ATTR3_SUPPRESS_CASTER_PROCS, ''), 'main-hand damage,')
rampage_strike_oh_204632 = _rampage_strike(
    204632, 'off-hand',
    (_ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_REQUIRES_OFF_HAND_WEAPON, ' + REQUIRES_OFF_HAND_WEAPON 0x1000000'),
    'off-hand damage and modifiers (0.5 factor, Dual Wield Specialization),')


# =====================================================================================================================
# 204633 / 204634 Frenzied Blows strikes (Heroic Strike / Cleave off-hand)  -- D19
# =====================================================================================================================
# Copies of Heroic Strike 78 / Cleave 845's damage rows (the same weapon percent + the flat 10 potency) as SINGLE-TARGET
# off-hand spells cast synchronously from AfterHit per landed target. NOT a paste of the parents' frames (0-verify A
# difference 5): chain 0 on both effects (Improved Cleave rank 3's JUMP_TARGETS makes 0 -> 1, not a chain), no
# AttributesEx 0x8000000 / AttributesEx2 0x1000 / AttributesEx3 0x400 / AttributesEx5 0x8000, no FacingCasterFlags,
# 50000 yd. AttributesEx3 REQUIRES_OFF_HAND_WEAPON (OFF_ATTACK) + SUPPRESS_CASTER_PROCS, AttributesEx4
# SUPPRESS_WEAPON_PROCS, EquippedItemClass -1 (B-R2: class -1 + the C++ guard), cost 0. Carriers d0 b6 / d0 b22 + d2 b3
# so every HS / Cleave damage modifier (Heavy Blows, Frenzied Blows, Unending Fury, Improved Cleave, Bloodsurge's +20%,
# Recklessness' crit, Impale) reaches the strike as part of the parent cast. Hidden (0x80).
frenzied_blows_heroic_strike_204633 = _fury(
    204633, 'Frenzied Blows',
    [_weapon_strike(183), _weapon_flat(12)],
    _ICON_HEROIC_STRIKE,
    'warrior-rework S3 A2a (D19): the off-hand Heroic Strike, cast by spell_warr_hs_cleave_fury (AfterHit, per landed '
    'target, triggered, synchronous). Copy of 78\'s damage rows: eff0 WEAPON_PERCENT_DAMAGE 150%, eff1 WEAPON_DAMAGE '
    'sp_potency 10 direct T 1500, single target (no chain). DmgClass melee, AttributesEx3 REQUIRES_OFF_HAND_WEAPON + '
    'SUPPRESS_CASTER_PROCS, AttributesEx4 SUPPRESS_WEAPON_PROCS, EquippedItemClass -1 (script guard), 50000 yd, no '
    'facing flag, cost 0, carriers d0 0x40 + d2 0x8, hidden (0x80), SpellLevel 1, visual 39.',
    _raw('Strike the target with your off-hand weapon.', level=1, DefenseType=_DMG_CLASS_MELEE,
         PreventionType=_PREVENTION_PACIFY,
         AttributesEx3=_ATTR3_REQUIRES_OFF_HAND_WEAPON | _ATTR3_SUPPRESS_CASTER_PROCS,
         AttributesEx4=_ATTR4_SUPPRESS_WEAPON_PROCS, SpellClassMask_1=_HEROIC_STRIKE_D0,
         SpellClassMask_3=_masks.DAMAGING_ABILITY_GROUP, SpellVisualID_1=_SV_HEROIC_STRIKE,
         DurationIndex=_DURATION_INFINITE),
    attributes=_ATTR0_DO_NOT_DISPLAY, range_yards=_SCRIPT_CAST_RANGE,
)

frenzied_blows_cleave_204634 = _fury(
    204634, 'Frenzied Blows',
    [_weapon_strike(144), _weapon_flat(12)],
    _ICON_CLEAVE,
    'warrior-rework S3 A2a (D19): the off-hand Cleave strike, cast per Cleave target by spell_warr_hs_cleave_fury. '
    'Copy of 845\'s damage rows: eff0 WEAPON_PERCENT_DAMAGE 120%, eff1 WEAPON_DAMAGE sp_potency 10 direct T 1500, '
    'chain 0 on both effects (single target: Improved Cleave rank 3\'s JUMP_TARGETS gives 0 + 1 = no chain). DmgClass '
    'melee, AttributesEx3 REQUIRES_OFF_HAND_WEAPON + SUPPRESS_CASTER_PROCS, AttributesEx4 SUPPRESS_WEAPON_PROCS, '
    'EquippedItemClass -1 (script guard), 50000 yd, no facing flag, cost 0, carriers d0 0x400000 + d2 0x8, hidden '
    '(0x80), SpellLevel = BaseLevel 14, visual 219.',
    _raw('Strike the target with your off-hand weapon.', level=14, DefenseType=_DMG_CLASS_MELEE,
         PreventionType=_PREVENTION_PACIFY,
         AttributesEx3=_ATTR3_REQUIRES_OFF_HAND_WEAPON | _ATTR3_SUPPRESS_CASTER_PROCS,
         AttributesEx4=_ATTR4_SUPPRESS_WEAPON_PROCS, SpellClassMask_1=_CLEAVE_D0,
         SpellClassMask_3=_masks.DAMAGING_ABILITY_GROUP, SpellVisualID_1=_SV_CLEAVE,
         DurationIndex=_DURATION_INFINITE),
    attributes=_ATTR0_DO_NOT_DISPLAY, range_yards=_SCRIPT_CAST_RANGE,
)


# =====================================================================================================================
# 204635 Enrage meter, 204636 Enrage  -- D3, D4, doc "Enrage"
# =====================================================================================================================
# Meter: visible DUMMY on the caster, CumulativeAura 20 (one stack per 10 rage; the fill at 200 fires first, so 19 is
# the most ever shown: P0 item 8 PASS), permanent
# (index 21), custom attr CU_AURA_CANNOT_BE_SAVED (the meter lives in Player::CustomData and resets on login, the
# Leaping 204402 precedent), AttributesEx3 ALLOW_AURA_WHILE_DEAD (death does not hide the progress).
enrage_meter_204635 = _fury(
    204635, 'Rage Meter',
    [_self_aura(AuraType.DUMMY)],
    _ICON_ENRAGE_TALENT,
    'warrior-rework S3 A2a (D3, doc "Enrage"): the rage meter. Visible (Attributes 0), eff0 DUMMY on the caster, '
    'CumulativeAura 20 (one stack per 10 rage paid, the P0 p0_enrage_meter_204897 shape), permanent (DurationIndex '
    '21), AttributesEx3 ALLOW_AURA_WHILE_DEAD 0x100000, custom attr CU_AURA_CANNOT_BE_SAVED (resets on login). Fill '
    'and step are the ENRAGE_METER_FILL / ENRAGE_METER_STACK consts.',
    _raw('Spending rage builds toward Enrage.', 'Spending rage builds toward Enrage.', CumulativeAura=20,
         AttributesEx3=SPELL_ATTR3_ALLOW_AURA_WHILE_DEAD, DurationIndex=_DURATION_INFINITE),
    range_yards=RANGE_SELF,
)
custom_attr(enrage_meter_204635, SPELL_ATTR0_CU_AURA_CANNOT_BE_SAVED)

# Enrage: visible 12 s self buff, Dispel 0 / Mechanic 0 (no enrage dispel type: nothing strips or counts it), not in
# spell_group 1104. eff0 aura 79 misc 1 (physical damage; EquippedItemClass -1 or SpellPctDamageModsDone drops it for a
# class -1 spell, 0-verify B item 8), eff1 aura 138 MOD_MELEE_HASTE (attack speed only, never 193), eff2 PERIODIC_DUMMY
# 1000 ms (the Mastery poll). The amounts are the AuraScript's (DoEffectCalcAmount): bp 9 (+10%) is only the DBC
# placeholder. Berserker Rage's glow (visual 47).
enrage_buff_204636 = _fury(
    204636, 'Enrage',
    [_self_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=_SCHOOL_PHYSICAL, base_points=9),
     _self_aura(AuraType.MOD_MELEE_HASTE, base_points=9),
     _self_aura(AuraType.PERIODIC_DUMMY, amplitude=1000)],
    _ICON_BERSERKER_RAGE,
    'warrior-rework S3 A2a (D4, doc "Enrage"): visible 12 s buff (DurationIndex 29), Dispel 0 / Mechanic 0, outside '
    'spell_group 1104. eff0 aura 79 misc 1 (physical damage), eff1 aura 138 (attack speed only, never 193: no GCD, no '
    'rage), eff2 PERIODIC_DUMMY 1000 ms (the Mastery poll). bp 9 is a placeholder: spell_warr_enrage_fury recalculates '
    'e0 / e1. EquippedItemClass -1. Berserker Rage\'s glow (visual 47).',
    _raw('Your physical damage and melee attack speed are increased.',
         'Your physical damage and attack speed are increased.', SpellVisualID_1=_SV_BERSERKER_RAGE),
    range_yards=RANGE_SELF, duration_ms=_DURATION_12S,
)


# =====================================================================================================================
# 204637 Blood Rush, 204647 Merciless free Rampage, 204649 Fresh Meat crit  -- D14, D18, D10
# =====================================================================================================================
# Blood Rush (visible, 5 s, ProcCharges 1, ProcTypeMask 0, NO spell_proc: the Momentum shape): eff0 ADD_PCT_MODIFIER
# COST -100% (bp -101) on Rampage (EffectSpellClassMaskA_3 = d2 0x4). The Rampage script removes it on every Rampage.
blood_rush_buff_204637 = _fury(
    204637, 'Blood Rush',
    [_spellmod(AuraType.ADD_PCT_MODIFIER, SpellModOp.COST, -101)],
    _ICON_RAMPAGE,
    'warrior-rework S3 A2a (D14, doc "Blood Rush"): visible 5 s buff (DurationIndex 28), ProcCharges 1, ProcTypeMask 0 '
    'and NO spell_proc row (the Momentum shape; the Rampage script removes it on every Rampage). eff0 '
    'ADD_PCT_MODIFIER COST -100% (bp -101) on Rampage (EffectSpellClassMaskA_3 = d2 0x4). A cost SpellMod, so the '
    'bot\'s CalcPowerCost read sees the free cast.',
    _raw('Your next Rampage costs no rage.', 'Your next Rampage costs no rage.', ProcChance=101, ProcCharges=1,
         EffectSpellClassMaskA_3=_masks.RAMPAGE),
    range_yards=RANGE_SELF, duration_ms=_DURATION_5S,
)

# Merciless capstone: hidden, permanent, no charges, the same COST -100% on Rampage; added / removed by the
# Recklessness AuraScript (D6 / D18). Attributes 0x80 (not PASSIVE: an AddAura'd aura).
merciless_free_rampage_204647 = _fury(
    204647, 'Merciless',
    [_spellmod(AuraType.ADD_PCT_MODIFIER, SpellModOp.COST, -101)],
    _ICON_RAMPAGE,
    'warrior-rework S3 A2a (D18, doc "Merciless"): the capstone half. Hidden (0x80), permanent (no duration), no '
    'charges, ProcTypeMask 0, no spell_proc. eff0 ADD_PCT_MODIFIER COST -100% (bp -101) on Rampage '
    '(EffectSpellClassMaskA_3 = d2 0x4). The Recklessness AuraScript adds it on apply and removes it on remove.',
    _raw('Rampage costs no rage.', EffectSpellClassMaskA_3=_masks.RAMPAGE),
    attributes=_ATTR0_DO_NOT_DISPLAY, range_yards=RANGE_SELF,
)

# Fresh Meat crit: hidden, ProcCharges 1, ProcTypeMask 0, no spell_proc, eff0 ADD_FLAT_MODIFIER CRITICAL_CHANCE +100
# (bp 99) on Bloodthirst (EffectSpellClassMaskA_2 = d1 0x400). Added by the dispatcher on a non-triggered Bloodthirst on
# a healthy target, removed by the fork Bloodthirst's AfterCast (only one +100 crit applies per cast, C4). A 3 s
# duration is the backstop for a cast that never reaches AfterCast.
fresh_meat_crit_204649 = _fury(
    204649, 'Fresh Meat',
    [_spellmod(AuraType.ADD_FLAT_MODIFIER, SpellModOp.CRITICAL_CHANCE, 99)],
    _ICON_BLOODTHIRST,
    'warrior-rework S3 A2a (D10, doc "Fresh Meat"): hidden (0x80), 3 s backstop (DurationIndex 27), ProcCharges 1, '
    'ProcTypeMask 0, no spell_proc. eff0 ADD_FLAT_MODIFIER CRITICAL_CHANCE +100% (bp 99) on Bloodthirst '
    '(EffectSpellClassMaskA_2 = d1 0x400). The dispatcher adds it, the fork Bloodthirst AfterCast removes it.',
    _raw('Your Bloodthirst critically strikes.', ProcChance=101, ProcCharges=1,
         EffectSpellClassMaskA_2=_BLOODTHIRST_D1),
    attributes=_ATTR0_DO_NOT_DISPLAY, range_yards=RANGE_SELF, duration_ms=_DURATION_3S,
)


# =====================================================================================================================
# 204638 Deathmaker  -- D16, doc "Deathmaker"
# =====================================================================================================================
# Visible 10 s buff (DurationIndex 1), eff0 aura 262 ABILITY_IGNORE_AURASTATE on Execute (EffectSpellClassMaskA_1 = d0
# 0x20000000), ProcTypeMask 0 and NO spell_proc (aura 262 is a trigger aura: any ProcTypeMask would auto-generate a
# consumer). SpellClassSet 4 is load-bearing (0-verify A item 7: a set-0 aura ignores the aura state for every
# family). Consumed in the fork Execute's OnCast.
deathmaker_buff_204638 = _fury(
    204638, 'Deathmaker',
    [_self_aura(AuraType.ABILITY_IGNORE_AURASTATE)],
    _ICON_SUDDEN_DEATH,
    'warrior-rework S3 A2a (D16, doc "Deathmaker"): visible 10 s buff (DurationIndex 1), eff0 aura 262 '
    'ABILITY_IGNORE_AURASTATE on Execute (EffectSpellClassMaskA_1 = d0 0x20000000), SpellClassSet 4 (load-bearing), '
    'ProcTypeMask 0, NO spell_proc, no charges. Consumed by spell_warr_execute_fury\'s OnCast; a new proc '
    'refreshes it.',
    _raw('Execute is usable on any target.', 'Execute is usable on any target.', ProcChance=101,
         EffectSpellClassMaskA_1=_EXECUTE_D0),
    range_yards=RANGE_SELF, duration_ms=_DURATION_10S,
)


# =====================================================================================================================
# 204639 / 204640 Dance of Death crit and heal  -- D26, doc "Dance of Death"
# =====================================================================================================================
# Crit: visible 8 s (DurationIndex 31), aura 290 MOD_CRIT_PCT (all crit). bp 1 (+2%) is the rank-1 placeholder: the
# script casts it with bp0 = the rank's value as a FINAL value. A new kill refreshes, never stacks.
dance_of_death_buff_204639 = _fury(
    204639, 'Dance of Death',
    [_self_aura(AuraType.MOD_CRIT_PCT, base_points=1)],
    _ICON_DEATH_WISH,
    'warrior-rework S3 A2a (D26, doc "Dance of Death"): visible 8 s (DurationIndex 31), eff0 aura 290 MOD_CRIT_PCT '
    '(melee, ranged, spell crit). bp 1 (+2%) is the rank-1 placeholder: spell_warr_dance_of_death casts it with bp0 = '
    'the rank value (final). Refresh, never stack.',
    _raw('Critical strike chance increased.', 'Critical strike chance increased.'),
    range_yards=RANGE_SELF, duration_ms=_DURATION_8S,
)

# Heal: hidden HEAL on the caster, the capstone's "base + 40% of attack power" set as a potency of 50 [tune]. No
# IGNORE_CASTER_MODIFIERS (the warrior's healing modifiers, Titan's Grip's -10% included, apply).
dance_of_death_heal_204640 = _fury(
    204640, 'Dance of Death',
    [Effect(type=EffectType.HEAL, ap_potency=50.0, potency_kind='heal', implicit_target_a=_TARGET_UNIT_CASTER)],
    _ICON_BLOODTHIRST,
    'warrior-rework S3 A2a (D26, doc "Dance of Death"): the capstone heal, cast by spell_warr_dance_of_death at most '
    'once per 5 s. Hidden (0x80) HEAL on the caster, ap_potency 50 [tune] ("base + 40% of attack power"), no '
    'IGNORE_CASTER_MODIFIERS (Titan\'s Grip\'s penalty applies), SpellLevel = BaseLevel 1.',
    _raw('Heals you.', level=1),
    attributes=_ATTR0_DO_NOT_DISPLAY, range_yards=RANGE_SELF,
)


# =====================================================================================================================
# 204641 Improved Execute stack, 204642 Cadence, 204643 Will of the Berserker crit  -- D17, D13, D24
# =====================================================================================================================
# Improved Execute capstone: visible 5 s (DurationIndex 28), aura 52 +10% melee crit per stack (bp 9), CumulativeAura 3.
improved_execute_buff_204641 = _fury(
    204641, 'Improved Execute',
    [_self_aura(AuraType.MOD_WEAPON_CRIT_PERCENT, base_points=9)],
    _ICON_SUDDEN_DEATH,
    'warrior-rework S3 A2a (D17, doc "Improved Execute"): visible 5 s (DurationIndex 28), eff0 aura 52 +10% melee crit '
    '(bp 9) per stack [tune], CumulativeAura 3. Cast by Warrior::OnExecuteHit on an Execute below 20%: one stack, '
    'refresh.',
    _raw('Critical strike chance increased.', 'Critical strike chance increased.', CumulativeAura=3),
    range_yards=RANGE_SELF, duration_ms=_DURATION_5S,
)

# Cadence (Quick Execution's capstone): visible 12 s (DurationIndex 29), aura 193 haste (attack speed + GCD + rage,
# Q8) +1% per stack (bp 0), CumulativeAura 3, no spell_group.
cadence_204642 = _fury(
    204642, 'Cadence',
    [_self_aura(AuraType.HASTE_ALL, base_points=0)],
    _ICON_FLURRY,
    'warrior-rework S3 A2a (D13, doc "Quick Execution"): visible 12 s (DurationIndex 29), eff0 aura 193 HASTE_ALL +1% '
    '(bp 0) per stack [tune], CumulativeAura 3, no spell_group. Granted by Quick Execution rank 3\'s proc on each '
    'Bloodthirst hit.',
    _raw('Haste increased.', 'Haste increased.', CumulativeAura=3),
    range_yards=RANGE_SELF, duration_ms=_DURATION_12S,
)

# Will of the Berserker's buff: visible 12 s (DurationIndex 29), aura 290 +10% all crit (bp 9). Cast by the
# Recklessness AuraScript on an EXPIRE / DEFAULT removal; never refreshed by anything else.
will_of_the_berserker_buff_204643 = _fury(
    204643, 'Will of the Berserker',
    [_self_aura(AuraType.MOD_CRIT_PCT, base_points=9)],
    _ICON_RECKLESSNESS,
    'warrior-rework S3 A2a (D24, doc "Will of the Berserker"): visible 12 s (DurationIndex 29), eff0 aura 290 '
    'MOD_CRIT_PCT +10% (bp 9) [tune]. Cast by spell_warr_recklessness_fury when Recklessness ends (EXPIRE or DEFAULT, '
    'never CANCEL / DEATH / ENEMY_SPELL).',
    _raw('Critical strike chance increased.', 'Critical strike chance increased.'),
    range_yards=RANGE_SELF, duration_ms=_DURATION_12S,
)


# =====================================================================================================================
# 204644-204646 Shredding Blows buffs  -- D27, doc "Shredding Blows"
# =====================================================================================================================
# Visible 15 s (DurationIndex 8), eff0 aura 280 misc 0 +4/8/12% armor penetration (bp 3 / 7 / 11) read on the sentinel
# bit d2 0x100 that no spell carries (EffectSpellClassMaskA_3 = _masks.SHREDDING_SENTINEL), so only white swings
# (null spell, EquippedItemClass -1: Unit.cpp:2316-2333) read it. ProcCharges 3, ProcTypeMask 0x4 (DBC), ProcChance 100
# (the explicit row's chance 0 falls back to it), EXPLICIT consuming spell_proc row below (aura 280 is not a trigger
# aura: without a row the charges never drop, C3). SpellClassSet 4 is load-bearing (0-verify A item 7: a set-0 buff
# would give its armor penetration to every ability of every class). The core ignores bonus% of min((armor + X) / 3,
# armor): about 0.89 of the stated % at 4,350 armor (B-R3 blind spot).
def _shredding_buff(spell_id, rank, base_points):
    return _fury(
        spell_id, 'Shredding Blows',
        [_self_aura(_AURA_MOD_ARMOR_PENETRATION_PCT, base_points=base_points, misc_value=0)],
        _ICON_SUNDER,
        f'warrior-rework S3 A2a (D27, doc "Shredding Blows"): rank {rank} buff. Visible 15 s (DurationIndex 8), eff0 '
        f'aura 280 +{base_points + 1}% armor penetration (bp {base_points}, misc 0) read on the sentinel d2 0x100 '
        '(EffectSpellClassMaskA_3, never carried: white swings only), ProcCharges 3, ProcTypeMask 0x4 and an explicit '
        'consuming spell_proc row (flags 0x4 only), ProcChance 100, SpellClassSet 4 (load-bearing), '
        'EquippedItemClass -1.',
        _raw("Your attacks ignore some of the target's armor.", "Your attacks ignore some of the target's armor.",
             ProcTypeMask=0x4, ProcChance=100, ProcCharges=3,
             EffectSpellClassMaskA_3=_masks.SHREDDING_SENTINEL),
        range_yards=RANGE_SELF, duration_ms=_DURATION_15S,
    )


shredding_blows_buff_r1_204644 = _shredding_buff(204644, 1, 3)
shredding_blows_buff_r2_204645 = _shredding_buff(204645, 2, 7)
shredding_blows_buff_r3_204646 = _shredding_buff(204646, 3, 11)


# =====================================================================================================================
# 204648 Intensify Rage silence, 204680 Bloodrage copy  -- D25, doc "Intensify Rage"
# =====================================================================================================================
# The capstone's two casts, both from Warrior::OnPummelInterrupt (never 2687 triggered: a triggered spellbook spell
# greys its button for the full cooldown). Silence: visible debuff on the target, 3 s (DurationIndex 27), aura 27 with
# Mechanic 9, 50000 yd (script cast).
intensify_rage_silence_204648 = _fury(
    204648, 'Intensify Rage',
    [Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=_MECHANIC_SILENCE,
            implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, apply_aura=AuraType.MOD_SILENCE)],
    _ICON_BLOODRAGE,
    'warrior-rework S3 A2a (D25, doc "Intensify Rage"): the capstone silence, cast on the Pummeled target. Visible '
    'debuff, 3 s [fixed] (DurationIndex 27), eff0 APPLY_AURA MOD_SILENCE (27) with Mechanic 9 on the enemy, 50000 yd. '
    'No family bits.',
    _raw('Silenced.', 'Silenced.'),
    range_yards=_SCRIPT_CAST_RANGE, duration_ms=_DURATION_3S, mechanic=_MECHANIC_SILENCE,
)

# Bloodrage copy: hidden, no cost, no cooldown. ENERGIZE 20 rage (bp 199, misc 1 = rage) on the caster +
# TRIGGER_SPELL -> 29131 (the stock periodic energize, 1 rage per second for 10 s) with 2687's bp 2. No
# SpellClassMask: it deliberately does NOT take Bloodrage's own bit d0 0x100 (Improved Bloodrage's EFFECT1 mod (Prot)
# and the T10 4P COST mod do not reach the copy; Intensify Rage's own COST mod must not either: the copy is already
# free).
intensify_rage_bloodrage_204680 = _fury(
    204680, 'Bloodrage',
    [Effect(type=EffectType.ENERGIZE, base_points=199, implicit_target_a=_TARGET_UNIT_CASTER,
            misc_value=_POWER_RAGE_MISC),
     Effect(type=EffectType.TRIGGER_SPELL, base_points=2, implicit_target_a=_TARGET_UNIT_CASTER,
            trigger_spell=29131)],
    _ICON_BLOODRAGE,
    'warrior-rework S3 A2a (D25, doc "Intensify Rage"): the capstone\'s Bloodrage at no health cost. Hidden (0x80), no '
    'cost, no cooldown. eff0 ENERGIZE bp 199 misc 1 (20 rage), eff1 TRIGGER_SPELL -> 29131 with bp 2 (as 2687). No '
    'family bits: it does not take Improved Bloodrage / T10 4P (d0 0x100) or Intensify Rage\'s own COST mod.',
    _raw('Generates 20 rage, and then generates an additional 10 rage over 10 sec.'),
    attributes=_ATTR0_DO_NOT_DISPLAY, range_yards=RANGE_SELF,
)


# =====================================================================================================================
# 204650 Blood Craze heal  -- D11, doc "Blood Craze"
# =====================================================================================================================
# Hidden instant HEAL on the caster; bp0 = max health x per-mille / 1000 (x2 Enraged) is a FINAL value the C++ passes.
# No IGNORE_CASTER_MODIFIERS and an all-zero spell_bonus_data row (Titan's Grip's -10% healing applies).
# Potency-excluded (percent of max health).
blood_craze_heal_204650 = _fury(
    204650, 'Blood Craze',
    [Effect(type=EffectType.HEAL, implicit_target_a=_TARGET_UNIT_CASTER,
            potency_excluded='the amount is 0.5/1/1.5% of the warrior\'s maximum health (doubled while Enraged) that '
                             'Warrior::OnBloodthirstHit passes as bp0 (percent-of-other-value rule, Fury doc "Blood '
                             'Craze"); no potency of its own')],
    _ICON_BLOOD_CRAZE,
    'warrior-rework S3 A2a (D11, doc "Blood Craze"): hidden (0x80) instant HEAL on the caster, bp0 = max health x '
    'per-mille / 1000 (x2 Enraged) from Warrior::OnBloodthirstHit (final value). No IGNORE_CASTER_MODIFIERS (Titan\'s '
    'Grip\'s -10% healing applies), potency_excluded.',
    _raw('Heals you for a share of your maximum health.'),
    attributes=_ATTR0_DO_NOT_DISPLAY, range_yards=RANGE_SELF,
)
# S3 fix m1: without a spell_bonus_data row Unit::SpellHealingBonusDone returns a DmgClass NONE heal untouched, before
# DoneTotalMod, where Titan's Grip's aura 136 (-10% healing) applies. The all-zero row adds no spell / attack power and
# lets the heal reach DoneTotalMod (D11).
bonus_coefficients(blood_craze_heal_204650, direct=0.0, dot=0.0, ap=0.0, ap_dot=0.0,
                   comment='Warrior - Blood Craze heal: no power scaling; the row lets healing-done mods apply')


# =====================================================================================================================
# 204651 Titan's Grip penalty  -- D31, doc "Titan's Grip"
# =====================================================================================================================
# Visible while a two-hander is in the off hand (Warrior::UpdateTitansGripPenalty adds / removes it): eff0 aura 79 misc
# 127 -10% all damage (bp -11), eff1 aura 136 MOD_HEALING_DONE_PERCENT -10% (bp -11). EquippedItemClass -1 (a class
# -1 spell drops an aura 79 with an equipment gate, 0-verify B item 8), not passive, permanent, custom attr
# CU_AURA_CANNOT_BE_SAVED (re-derived at login). Stock 49152 stays an untouched row, forced to 0 by its script.
titans_grip_penalty_204651 = _fury(
    204651, "Titan's Grip",
    [_self_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=_SCHOOLS_ALL, base_points=-11),
     _self_aura(AuraType.MOD_HEALING_DONE_PERCENT, base_points=-11)],
    _ICON_TITANS_GRIP,
    'warrior-rework S3 A2a (D31, doc "Titan\'s Grip"): the visible penalty, present iff the off-hand item is a '
    'two-hander. Visible (Attributes 0, never PASSIVE), permanent, eff0 aura 79 misc 127 -10% (bp -11), eff1 aura 136 '
    'MOD_HEALING_DONE_PERCENT -10% (bp -11), EquippedItemClass -1, custom attr CU_AURA_CANNOT_BE_SAVED, '
    'AttributesEx3 ALLOW_AURA_WHILE_DEAD (orchestrator, B1 finding: death would strip the penalty and nothing re-adds '
    'it). Exempt from Mastery (Q7).',
    _raw('Your damage and healing are reduced.', 'Your damage and healing are reduced.',
         AttributesEx3=SPELL_ATTR3_ALLOW_AURA_WHILE_DEAD),
    range_yards=RANGE_SELF,
)
custom_attr(titans_grip_penalty_204651, SPELL_ATTR0_CU_AURA_CANNOT_BE_SAVED)


# =====================================================================================================================
# 204652 Bloodsurge buff  -- D15, doc "Bloodsurge"
# =====================================================================================================================
# Visible 15 s (DurationIndex 8, handoff Q6), ProcCharges 1, ProcTypeMask 0, NO spell_proc (the Momentum shape: dropped
# once per Spell at Spell::finish, after every target and every synchronous child, so every Cleave target and the
# Frenzied Blows strike are computed with it). eff0 ADD_PCT_MODIFIER COST -100% (bp -101) on Slam | Cleave
# (EffectSpellClassMaskA_1 = d0 0x600000), eff1 ADD_PCT_MODIFIER DAMAGE +20% (bp 19) on the same bits
# (EffectSpellClassMaskB_1). Stock 46916 stays as is.
bloodsurge_buff_204652 = _fury(
    204652, 'Bloodsurge',
    [_spellmod(AuraType.ADD_PCT_MODIFIER, SpellModOp.COST, -101),
     _spellmod(AuraType.ADD_PCT_MODIFIER, SpellModOp.DAMAGE, 19)],
    _ICON_SLAM_PROC,
    'warrior-rework S3 A2a (D15, doc "Bloodsurge"): visible 15 s buff (DurationIndex 8), ProcCharges 1, ProcTypeMask '
    '0, NO spell_proc (the Momentum shape). eff0 ADD_PCT_MODIFIER COST -100% (bp -101) and eff1 ADD_PCT_MODIFIER '
    'DAMAGE +20% (bp 19) [tune] on Slam | Cleave (EffectSpellClassMaskA_1 = B_1 = d0 0x600000). Stock Slam! 46916 '
    'is untouched. Stock Bloodsurge proc look (visual 10701).',
    _raw('Your next Slam or Cleave costs no rage and deals 20% more damage.',
         'Your next Slam or Cleave costs no rage and deals more damage.', ProcChance=101, ProcCharges=1,
         EffectSpellClassMaskA_1=_SLAM_D0 | _CLEAVE_D0, EffectSpellClassMaskB_1=_SLAM_D0 | _CLEAVE_D0,
         SpellVisualID_1=_SV_BLOODSURGE),
    range_yards=RANGE_SELF, duration_ms=_DURATION_15S,
)


# =====================================================================================================================
# 204679 Rampage Recklessness snapshot  -- D7
# =====================================================================================================================
# Hidden 2 s aura (DurationIndex 39) added by spell_warr_rampage_fury when the press had Recklessness, removed when
# the sequence ends or stops: eff0 ADD_FLAT_MODIFIER CRITICAL_CHANCE +100% (bp 99) on Rampage's strikes
# (EffectSpellClassMaskA_3 = d2 0x4), no charges, no spell_proc (a mod without charges: Recklessness' own charge is
# spent by DropCharge).
rampage_snapshot_204679 = _fury(
    204679, 'Rampage',
    [_spellmod(AuraType.ADD_FLAT_MODIFIER, SpellModOp.CRITICAL_CHANCE, 99)],
    _ICON_RECKLESSNESS,
    'warrior-rework S3 A2a (D7, doc "Rampage"): the press-state Recklessness crit. Hidden (0x80, not passive), 2 s '
    '(DurationIndex 39), eff0 ADD_FLAT_MODIFIER CRITICAL_CHANCE +100% (bp 99) on Rampage\'s strikes '
    '(EffectSpellClassMaskA_3 = d2 0x4), no charges, no spell_proc. Added by the Rampage script, removed when the '
    'sequence ends or stops.',
    _raw('Your Rampage strikes critically strike.', EffectSpellClassMaskA_3=_masks.RAMPAGE),
    attributes=_ATTR0_DO_NOT_DISPLAY, range_yards=RANGE_SELF, duration_ms=_DURATION_2S,
)


# =====================================================================================================================
# 23885 Bloodthirst's heal buff (first declaration of the stock legacy row)  -- D9, doc "Bloodthirst"
# =====================================================================================================================
# Pulled from npc.csv:3793 (deleted in the same change). ProcCharges 3 -> 1 (the next melee hit only), 8 s kept
# (DurationIndex 31), the aura text from the doc. The proc row below is explicit and damage-only (SpellTypeMask 1) so
# Rampage's no-damage press cannot consume it (C2). Effect, ProcTypeMask 0x14, ProcChance 100 as stock: eff0
# PROC_TRIGGER_SPELL -> 23880 (the 1% heal, still the legacy npc.csv row bound to spell_warr_bloodthirst_heal).
bloodthirst_heal_buff_23885 = spell(
    id=23885,
    name='Bloodthirst',
    school=1,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=1,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=_DURATION_8S,
    effects=[
        Effect(type=6, die_sides=0, implicit_target_a=1, apply_aura=42, trigger_spell=23880),
    ],
    spell_icon_id=38,
    notes='warrior-rework S3 A2a (D9): first declaration of the stock heal buff (npc.csv:3793 deleted). ProcCharges 3 '
          '-> 1 (the next melee hit only), 8 s kept, aura text "Your next melee attack restores health.". The '
          'explicit damage-only spell_proc row below keeps Rampage\'s no-damage press from consuming it (C2). The '
          'heal 23880 stays a legacy npc.csv row.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 20, 'ProcChance': 100, 'ProcCharges': 1, 'BaseLevel': 40,
                   'SpellLevel': 40, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellPriority': 50,
                   'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172,
                   'Description_Lang_enUS': 'Your next melee attack restores health. Lasts 8 sec.',
                   'Description_Lang_Mask': 16712190,
                   'AuraDescription_Lang_enUS': 'Your next melee attack restores health.',
                   'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 4, 'EffectChainAmplitude_1': 1.0,
                   'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0,
                   'EffectBonusMultiplier_2': 1.0},
)


# =====================================================================================================================
# S3 script bindings (brief section 2; the classes live in spell_warrior_fury.cpp, AddSC_warrior_fury_spell_scripts)
# =====================================================================================================================
scripted_by(23881, 'spell_warr_bloodthirst_fury')           # Bloodthirst: bleed bonus, hit rage, 23885 in AfterHit
scripted_by(-5308, 'spell_warr_execute_fury')               # Execute: stock body + Deathmaker, meter, Improved Exec
scripted_by(204630, 'spell_warr_rampage_fury')              # Rampage: snapshot, Recklessness charge, the four strikes
scripted_by(204636, 'spell_warr_enrage_fury')               # Enrage: amount recalculation, the Mastery poll
scripted_by(12292, 'spell_warr_death_wish_fury')            # Death Wish: Enrage grant, hold, PERIODIC_DUMMY e1
scripted_by(1719, 'spell_warr_recklessness_fury')           # Recklessness: Enrage, 204647, Will of the Berserker
scripted_by(78, 'spell_warr_hs_cleave_fury')                # Heroic Strike / Cleave: Frenzied Blows' off-hand strike
scripted_by(845, 'spell_warr_hs_cleave_fury')
scripted_by(49152, 'spell_warr_titans_grip_hardcode')       # stock Titan's Grip penalty -> 0 (204651 is the new one)
scripted_by(-204524, 'spell_warr_two_handed_weapon_mastery_gate')  # S2's THWM ranks: 0 while an off-hand weapon is held
scripted_by(6552, 'spell_warr_pummel_fury')                 # Pummel: Intensify Rage's capstone interrupt hook
scripted_by(-204653, 'spell_warr_dance_of_death')           # Dance of Death ranks: OnEffectProc -> crit, heal, Charge
scripted_by(6673, 'spell_warr_commanding_presence')         # Battle Shout: the Strength effect's amount
scripted_by(469, 'spell_warr_commanding_presence')          # Commanding Shout: the Stamina effect's amount
scripted_by(-204671, 'spell_warr_deathmaker')               # Deathmaker ranks: CheckProc = Warrior::IsStrikeCast

# "The stronger shout wins, as stock" (D30, Fury doc "Commanding Presence"). Battle Shout's stock group 1003 is already
# EXCLUSIVE_HIGHEST (4), so a talented Battle Shout's Strength effect out-ranks a plain one in
# Unit::IsHighestExclusiveAura. Commanding Shout's stock group 1091 is rule 0 (DEFAULT): two copies of the one-rank
# 469 from different warriors fall through to Aura::CanStackWith's same-rank-chain rule and the LAST cast replaces the
# other, so a plain Commanding Shout overwrote a Commanding Presence one (10-31 bug I). Rule 4 compares each effect
# (health, then the Stamina effect) and keeps the stronger; ties still refresh. Nested groups are unchanged: 1093 (vs
# Blood Pact, rule 4) and 1011 (one shout per warrior, rule 2).
spell_group_rule(1091, stack_rule=4, description='Commanding Shout')

# Stock classes S3 retires from these ids (the stock classes stay registered where other ids still use them).
unbind_script(23881, 'spell_warr_bloodthirst')              # D9: replaced by spell_warr_bloodthirst_fury (23880 stays)
unbind_script(-5308, 'spell_warr_execute')                  # D17: replaced by spell_warr_execute_fury
unbind_script(-46913, 'spell_warr_extra_proc')              # D15: Bloodsurge now triggers 204652 (the T10 hook is lost)
unbind_script(-12317, 'spell_gen_proc_from_direct_damage')  # D3: Enrage is a DUMMY carrier now (-49004 stays)

# spell_proc rows the rewritten ranks no longer use (their ProcTypeMask / ProcChance are zeroed in the rank rows or the
# talents are retired, so no default entry is built either). The Enrage / Blood Craze / Unbridled Wrath rank-key
# removals (-12317, -16487, 12322 / 12999 / 13000-13002) are with the rank rows (warrior_fury_ranks.py).
remove_spell_proc(-20500)                                   # Improved Berserker Rage (retired talent, D12)
remove_spell_proc(46910)                                    # Furious Attacks rank 1 (retired talent, D16)
remove_spell_proc(46911)                                    # Furious Attacks rank 2 (retired talent, D16)

# spell_proc rows on stock / legacy ids.
# Bloodsurge (D15): a Bloodthirst or Whirlwind cast (d1 0x404), CAST phase so it rolls once per cast and not per
# target, the rank's DBC chance 10/20/30 (A1). Heroic Strike is dropped from the list.
procs_on(-46913, proc_flags=0x10, family_name=_SPELLFAMILY_WARRIOR, family_mask=(0, _BLOODTHIRST_D1 | _WHIRLWIND_D1, 0),
         spell_phase_mask=0x1)
# Bloodthirst's heal buff (D9, C2): only a DAMAGING melee hit consumes the charge (SpellTypeMask 1 = damage), HIT phase;
# the auto-generated entry would be MASK_ALL and let Rampage's no-damage press eat it.
procs_on(23885, proc_flags=0x14, spell_type_mask=0x1, spell_phase_mask=0x2)
# Wrecking Crew (D33, S2 finding 11): main-hand white crits and ability crits only (DONE_MAINHAND_ATTACK 0x400000 |
# melee ability 0x10), HIT phase, crit; the live row's damage type kept. Off-hand white crits no longer proc.
procs_on(-46867, proc_flags=0x400010, spell_type_mask=0x1, spell_phase_mask=0x2, hit_mask=0x2)
# Shredding Blows' consumers (B-R3, D27): flags 0x4 (auto attacks, main and off hand) only; any phase / type field with
# no spell flag is a boot ERROR. The default hit mask NORMAL | CRIT | ABSORB applies (a dodge or miss does not consume).
procs_on(204644, proc_flags=0x4, spell_type_mask=0, spell_phase_mask=0, hit_mask=0)
procs_on(204645, proc_flags=0x4, spell_type_mask=0, spell_phase_mask=0, hit_mask=0)
procs_on(204646, proc_flags=0x4, spell_type_mask=0, spell_phase_mask=0, hit_mask=0)


# =====================================================================================================================
# Script numbers (hidden constants; generated WarriorData::NAME, read by WarriorMechanics.cpp / spell_warrior_fury.cpp)
# =====================================================================================================================
ENRAGE_METER_FILL = const(
    'ENRAGE_METER_FILL', 200,
    'Enrage meter: rage points paid per fill (doc "Enrage" 190; user 2026-10-30: 200; the C++ multiplies by 10 for '
    'power units) [tune].')
ENRAGE_METER_STACK = const(
    'ENRAGE_METER_STACK', 10,
    'Enrage meter: rage points per displayed stack (at most 19 shown: the 200th rage fires Enrage) [fixed].')
COMMANDING_PRESENCE_AT_60 = const(
    'COMMANDING_PRESENCE_AT_60', 30,
    'Commanding Presence: Strength (Battle Shout) / Stamina (Commanding Shout) at rank 2 and level 60, scaled linearly '
    'with the warrior\'s level, half at rank 1 (handoff Q6) [tune].')
RAMPAGE_STRIKE_2_MS = const(
    'RAMPAGE_STRIKE_2_MS', 330,
    'Rampage: delay of the second strike after the cast in milliseconds (the first is at 0) [tune].',
    cpp_type='uint32')
RAMPAGE_STRIKE_3_MS = const(
    'RAMPAGE_STRIKE_3_MS', 660,
    'Rampage: delay of the third strike after the cast in milliseconds [tune].', cpp_type='uint32')
RAMPAGE_STRIKE_4_MS = const(
    'RAMPAGE_STRIKE_4_MS', 1000,
    'Rampage: delay of the fourth strike after the cast in milliseconds [tune].', cpp_type='uint32')
WILL_OF_THE_BERSERKER_CDR_MS = const(
    'WILL_OF_THE_BERSERKER_CDR_MS', 2000,
    'Will of the Berserker: Recklessness cooldown cut per Rampage cast in milliseconds, real time [tune].',
    cpp_type='uint32')
DANCE_OF_DEATH_HEAL_ICD_MS = const(
    'DANCE_OF_DEATH_HEAL_ICD_MS', 5000,
    'Dance of Death capstone: internal cooldown of the heal in milliseconds (the crit buff has none) [fixed].',
    cpp_type='uint32')
BLOODTHIRST_RAGE = const(
    'BLOODTHIRST_RAGE', 10,
    'Bloodthirst: rage generated on the hit, before Improved Bloodthirst [fixed].')
BLOODTHIRST_BLEED_BONUS_PCT = const(
    'BLOODTHIRST_BLEED_BONUS_PCT', 8,
    'Bloodthirst: damage bonus per bleed this warrior has applied on the target [tune].')
BLOODTHIRST_BLEED_BONUS_MAX_PCT = const(
    'BLOODTHIRST_BLEED_BONUS_MAX_PCT', 40,
    'Bloodthirst: cap of the bleed bonus [tune].')
MERCILESS_HEALTH_PCT = const(
    'MERCILESS_HEALTH_PCT', 35,
    'Merciless: the target health below which the bonus applies [fixed].')
IMPROVED_EXECUTE_HEALTH_PCT = const(
    'IMPROVED_EXECUTE_HEALTH_PCT', 20,
    'Improved Execute: the target health below which the bonus is doubled and the capstone stacks [tune].')
UNENDING_FURY_WHIRLWIND_CUT_MS = const(
    'UNENDING_FURY_WHIRLWIND_CUT_MS', 1500,
    'Unending Fury capstone: Whirlwind cooldown cut per Cleave cast in milliseconds, real time [tune].',
    cpp_type='uint32')
