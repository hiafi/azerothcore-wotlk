"""
Rogue - S1 Assassination, data half: every new row 203800-203847 (talent ranks, Mutilate's new hands, Doomblade,
Blindside, Poison Bomb, Shattering Vial, Kingsbane, the talent buffs and debuffs, the Vile Poisons helpers), the
SpellDescriptionVariables 1320-1323 (U15 talent bonuses on tooltips), the scripted_by rows of the new ids and the
hidden script numbers (`const()`) the C++ reads through the generated RogueData.h.

Source of truth: docs/reworks/rogue-assassination-rework.md (tooltips and aura texts verbatim),
.agents/plans/rogue-rework/rogue-rework.S1-HANDOFF.md (sections 4-5), rogue-rework.S1a-WP-BRIEF.md (variable names,
bits, effect order, resolutions; the brief wins over the handoff).

Talent rows, their SkillLineAbility bundling (Poison Bomb 30800, Kingsbane 30801) and the tab live in rogue_talents.py;
stock rank spells edited in place live in rogue_trigger_spells.py; shared stock rows (Mutilate 1329, Cold Blood, Hunger
for Blood, Envenom, the group bits) live in rogue_spells.py / rogue_shared.py.

Conventions of this file (WP-BRIEF section 10.15 / 13): talent ranks are hidden passives (Attributes 464, SpellLevel =
9 + 5 x talent row + rank, EquippedItemClass -1, stored base points = live - 1); every buff the player should see is a
NON-passive aura with a number-free aura text (custom-spells.md); helper casts and the hands are hidden
(DO_NOT_DISPLAY). Family bits are exactly the carriers of the WP-BRIEF section 4 table (the bit table is the authority).
Rows cast at an enemy by a script carry a real 100 yd range (a triggered cast is range-checked, RG0a handoff C4).
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, PowerType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import const, custom_attr, linked_spell, pot_text, scripted_by, spell, tooltip_vars
from lib.dsl.tooltip import product, talent_mult

from . import _masks as m

# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h) ----
_SPELLFAMILY_ROGUE = 8
_ATTR0_DO_NOT_DISPLAY = 0x80
_ATTR0_TALENT_PASSIVE = 464                 # ABILITY 0x10 | PASSIVE 0x40 | DO_NOT_DISPLAY 0x80 | DO_NOT_LOG 0x100
_ATTR0_MELEE_STRIKE = 327696                # 0x50010: stock Mutilate / Sinister Strike frame
_ATTR1_ALLOW_WHILE_STEALTHED = 0x20         # AttributesEx: a self buff cast while stealthed never breaks Stealth
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_STACK_PER_CASTER = 0x80              # DOT_STACKING_RULE: stack separately for each caster
_ATTR3_NOT_A_PROC = 0x200
_ATTR3_REQUIRES_MAIN_HAND = 0x400
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000
_ATTR3_SUPPRESS_TARGET_PROCS = 0x20000      # "no initial aggro" (R4)
_ATTR3_ALWAYS_HIT = 0x40000
_ATTR3_REQUIRES_OFF_HAND = 0x1000000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000

# ---- Auras / effects / targets / misc values ----
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_DEST_AREA_ENEMY = 16
_TARGET_DEST_TARGET_ENEMY = 53              # enemy-targeted ground cloud (Spore Cloud 50274: A 53 / B 16)
_AURA_MOD_INCREASE_ENERGY = 35              # Vigor: misc 3 = energy
_AURA_MOD_MOUNTED_SPEED_NOT_STACK = 172
_AURA_MOD_DAMAGE_FROM_CASTER = 271
_POWER_ENERGY = 3
_MECHANIC_BLEED = 15
_MISC_CRITICAL_CHANCE = int(SpellModOp.CRITICAL_CHANCE)

# ---- Weapon requirements (WP-BRIEF R3) ----
_ITEM_CLASS_WEAPON = 2
_ONE_HAND_WEAPONS = 41105                   # 0xA091: axe 0, mace 4, sword 7, fist 13, dagger 15
_SCRIPT_CAST_RANGE = 100.0                  # a script-cast payload at an enemy: a real range (Wound Poison 13218's)

# ---- Stock icons / visuals (S1a-0VERIFY item 16a) ----
_SV_KINGSBANE = 90250                       # Ascension 277580 / SV 42720
_SV_POISON_BOMB = 90251                     # Ascension 284169 / SV 42787: vial missile + cloud in one row
_ICON_QUICK_PACE = 115
_ICON_DOOMBLADE = 1501
_ICON_BLINDSIDE = 2126
_ICON_POISON_BOMB = 90372                 # Ascension inv_ability_poison_nova (build_patch_i.py)
_ICON_SHATTERING_VIAL = 90370             # Ascension ability_rogue_crimsonvial (build_patch_i.py)
_ICON_VENOMOUS_FAN = 1528
_ICON_ZOLDYCK = 1644
_ICON_CUT_THROAT = 2318
_ICON_TOXIC_BLADE = 2269
_ICON_CARNAGE = 2006
_ICON_DASHING_SCOUNDREL = 2428
_ICON_KINGSBANE = 90371                   # Ascension inv_ability_rogue_sepsis (build_patch_i.py)
_ICON_REMORSELESS = 695
_ICON_OVERKILL = 2285
_ICON_COLD_BLOOD = 32
_ICON_SEAL_FATE = 55
_ICON_VIGOR = 691
_ICON_FLEET_FOOTED = 2113
_ICON_VILE_POISONS = 2905

# Talent rows (tier) of the S1 grid, for SpellLevel = 9 + 5 x row + rank (DK brief D3).
_ROW_QUICK_PACE, _ROW_DOOMBLADE, _ROW_BLINDSIDE, _ROW_VIAL, _ROW_VENOMOUS_FAN = 0, 2, 3, 4, 5
_ROW_VIGOR, _ROW_FLEET_FOOTED, _ROW_OVERKILL, _ROW_ZOLDYCK, _ROW_CUT_THROAT = 2, 4, 6, 7, 7
_ROW_TOXIC_BLADE, _ROW_CARNAGE, _ROW_DASHING = 8, 8, 9


# =====================================================================================================================
# Script numbers (WP-BRIEF section 6; hidden constants, generated RogueData::NAME, read by RogueMechanics.cpp and the
# S1 scripts). Every [tune] number changes here, never in C++.
# =====================================================================================================================
MUTILATE_PER_POISON_PCT = const(
    'MUTILATE_PER_POISON_PCT', 15, 'Mutilate: +% damage per own poison on the target [tune].')
MUTILATE_NORMALIZED_SPEED_MS = const(
    'MUTILATE_NORMALIZED_SPEED_MS', 1700, 'Mutilate: reference weapon speed each hand is rescaled to, ms [fixed].')
RUTHLESSNESS_ICD_MS = const(
    'RUTHLESSNESS_ICD_MS', 9000, 'Ruthlessness: per-rogue internal cooldown, ms [fixed].')
DEADLY_BREW_ICD_MS = const(
    'DEADLY_BREW_ICD_MS', 4000, 'Deadly Brew: per-rogue internal cooldown, ms [fixed].')
DASHING_SCOUNDREL_ICD_MS = const(
    'DASHING_SCOUNDREL_ICD_MS', 1000, 'Dashing Scoundrel: per-rogue energy cap interval, ms [fixed].')
DOOMBLADE_TICKS = const(
    'DOOMBLADE_TICKS', 4, 'Doomblade: stored-bleed tick count (the 2 sec period comes from 203829\'s data) [fixed].')
DOOMBLADE_CAPSTONE_PCT_PER_BLEED = const(
    'DOOMBLADE_CAPSTONE_PCT_PER_BLEED', 5, 'Doomblade capstone: Envenom +% per own bleed on the target [fixed].')
KINGSBANE_STACK_PCT = const(
    'KINGSBANE_STACK_PCT', 5, 'Kingsbane: +% damage per stack [fixed].')
KINGSBANE_MAX_STACKS = const(
    'KINGSBANE_MAX_STACKS', 50, 'Kingsbane: stack cap [fixed].')
KINGSBANE_ENVENOM_STACKS = const(
    'KINGSBANE_ENVENOM_STACKS', 2, 'Kingsbane: stacks per Lethal poison application while Envenom is up (1 otherwise) '
    '[fixed].')
POISON_BOMB_IMPACT_STACKS = const(
    'POISON_BOMB_IMPACT_STACKS', 2, 'Poison Bomb: Deadly Poison applications per enemy on impact [fixed].')
POISON_BOMB_PULSES = const(
    'POISON_BOMB_PULSES', 3, 'Poison Bomb: pulses after the impact [fixed].')
POISON_BOMB_PULSE_MS = const(
    'POISON_BOMB_PULSE_MS', 2000, 'Poison Bomb: spacing of the pulses, ms (events are not hasted) [fixed].')
POISON_BOMB_RADIUS_YD = const(
    'POISON_BOMB_RADIUS_YD', 8, 'Poison Bomb: impact and pulse search radius, yards [fixed].')
INDISCRIMINATE_CARNAGE_RADIUS_YD = const(
    'INDISCRIMINATE_CARNAGE_RADIUS_YD', 8, 'Indiscriminate Carnage: spread radius around the primary, yards [tune].')
ZOLDYCK_HEALTH_PCT = const(
    'ZOLDYCK_HEALTH_PCT', 30, 'Zoldyck Recipe: live target health threshold, % [fixed].')
SEAL_FATE_CAPSTONE_PCT_PER_CP = const(
    'SEAL_FATE_CAPSTONE_PCT_PER_CP', 20, 'Seal Fate capstone: chance per combo point when a finisher consumes Cold '
    'Blood, % [fixed].')
OVERKILL_TAIL_MS = const(
    'OVERKILL_TAIL_MS', 20000, 'Overkill: how long the buff lasts after stealth ends, ms [fixed].')
QUICK_RECOVERY_ENERGY = const(
    'QUICK_RECOVERY_ENERGY', 10, 'Quick Recovery: energy refunded (bp0 of the stock energize 31663) [fixed].')
VENOMOUS_FAN_POISON_MULT = const(
    'VENOMOUS_FAN_POISON_MULT', 2, 'Venomous Fan capstone: Fan of Knives poison chance multiplier, after Proc Chance, '
    'capped at 100% [fixed].')
WOUND_MASTERY_DIVISOR = const(
    'WOUND_MASTERY_DIVISOR', 2, 'Improved Poisons capstone: Mastery / this goes into Wound Poison\'s bleed bonus '
    '[fixed].')


def _c(row):
    """A const() row's value as tooltip text (8.0 -> '8')."""
    value = row['value']
    return str(int(value)) if float(value).is_integer() else str(value)


def _sec(row):
    """A millisecond const() row's value as whole-second tooltip text (2000 -> '2')."""
    value = row['value'] / 1000
    return str(int(value)) if float(value).is_integer() else str(value)


def _grey(text):
    """The capstone line on a rank below the last (paladin / hunter / DK rank-text convention)."""
    return f'|cFF9D9D9D{text}|r'


def _with_cap(text, capstone, last):
    """`text` plus a blank line and the capstone sentence (house format, `Capstone Bonus: ...`): plain on the last
    rank, grey below it."""
    return f'{text}\n\n{capstone if last else _grey(capstone)}'


# ---- effect and mask helpers ----
_MASK_LETTER = {1: 'A', 2: 'B', 3: 'C'}


def _masks(effect_index, triple):
    """EffectSpellClassMask{A,B,C}_{1,2,3} columns for the 1-based `effect_index` from a (d0, d1, d2) triple."""
    return {f'EffectSpellClassMask{_MASK_LETTER[effect_index]}_{dword}': value
            for dword, value in enumerate(triple, start=1) if value}


def _aura(aura, base_points=0, misc_value=0, target=_TARGET_UNIT_CASTER, **kwargs):
    return Effect(type=EffectType.APPLY_AURA, apply_aura=aura, base_points=base_points, misc_value=int(misc_value),
                  implicit_target_a=target, **kwargs)


def _flat(op, base_points):
    return _aura(AuraType.ADD_FLAT_MODIFIER, base_points, op)


def _pct(op, base_points):
    return _aura(AuraType.ADD_PCT_MODIFIER, base_points, op)


def _dummy(base_points):
    return _aura(AuraType.DUMMY, base_points)


def _class_mask(triple):
    """SpellClassMask_{1,2,3} columns (the spell's own family bits) from a (d0, d1, d2) triple."""
    return {f'SpellClassMask_{dword}': value for dword, value in enumerate(triple, start=1) if value}


# =====================================================================================================================
# Hidden talent ranks (WP-BRIEF section 13): Attributes 464, duration -1, SpellLevel 9 + 5 x row + rank
# =====================================================================================================================
def _rank(spell_id, name, rank, row, effects, icon, description, masks=None, notes='', raw=None):
    """One hidden talent rank passive. `masks` maps a 1-based effect index to its (d0, d1, d2) reader triple; `rank` is
    the NameSubtext number (None for a one-rank talent). Stored base points are live - 1."""
    overrides = {
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'RangeIndex': 1,
        'SpellLevel': 9 + 5 * row + (rank or 1), 'ProcTypeMask': 0, 'ProcChance': 101,
        'NameSubtext_Lang_enUS': '' if rank is None else f'Rank {rank}',
        'Description_Lang_enUS': description,
    }
    for effect_index, triple in (masks or {}).items():
        overrides.update(_masks(effect_index, triple))
    overrides.update(raw or {})
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_TALENT_PASSIVE,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=0.0, duration_ms=-1, effects=effects, spell_icon_id=icon,
        notes='rogue-rework S1a A3, assassination doc section 5: hidden talent rank passive (Attributes 464, '
              'SpellLevel '
              f'= 9 + 5 x {row} + rank, stored = live - 1). ' + notes,
        raw_overrides=overrides,
    )


# =====================================================================================================================
# Helper rows first (the rank tooltips quote them)
# =====================================================================================================================

# ---- Mutilate hands 203827 / 203828 (WP-BRIEF R3, Known-hard 2) ----
# The stock 5374 / 27576 frames (Attributes 0x50010, Ex3 MH 0x600 / OH 0x1000200, Ex4 / Ex7 as stock) with the
# one-hand mask, hidden. eff0 WEAPON_PERCENT_DAMAGE weapon_potency 145 FIRST, eff1 NORMALIZED_WEAPON_DMG sp_potency 10
# direct T 1500 SECOND (the Sinister Strike 1752 shape). d2 b20 only: d1 b21 stays on the parent, never d1 b1 / b2
# (the core +20% and the stock Cold Blood / Remorseless scripts key on them). B13 rescale and the per-poison bonus:
# spell_rog_dual_strike_hand.
def _mutilate_hand(spell_id, offhand):
    which = 'off hand' if offhand else 'main hand'
    ex3_text = ('0x1000200 (REQUIRES_OFF_HAND_WEAPON + NOT_A_PROC)' if offhand
                else '0x600 (REQUIRES_MAIN_HAND_WEAPON + NOT_A_PROC)')
    return spell(
        id=spell_id, name='Mutilate', school=School.NORMAL, attributes=_ATTR0_MELEE_STRIKE | _ATTR0_DO_NOT_DISPLAY,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0,
        mana_cost_pct=0, range_yards=None,
        effects=[
            Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=145.0,
                   implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
            Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=10.0, potency_kind='direct', time_basis_ms=1500,
                   implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        ],
        spell_icon_id=533,
        notes=f'rogue-rework S1a A3, assassination doc "Mutilate" (Known-hard 2, R3, R15): the {which} hand, '
              'triggered by 1329 eff1 / eff2. Stock 5374 / 27576 frame (Attributes 0x50010 + hidden 0x80, Ex3 '
              f'{ex3_text}{"" if offhand else ", Ex4 0x1"}, Ex7 stock, DefenseType 2, raw RangeIndex 2) with the '
              'one-hand weapon mask '
              '41105 (Spell::CheckItems runs on triggered casts). eff0 weapon_potency 145 first, eff1 sp_potency 10 '
              'direct T 1500 second (SS shape). SpellLevel 20. d2 b20 only (m.MUTILATE_HANDS). script '
              'spell_rog_dual_strike_hand: B13 rescale to a 1.7 weapon + 15% per own poison.',
        raw_overrides={
            'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': _ITEM_CLASS_WEAPON,
            'EquippedItemSubclass': _ONE_HAND_WEAPONS, 'SpellLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 2,
            'RangeIndex': 2, 'ProcChance': 101,
            'AttributesEx3': _ATTR3_NOT_A_PROC | (_ATTR3_REQUIRES_OFF_HAND if offhand else _ATTR3_REQUIRES_MAIN_HAND),
            **({} if offhand else {'AttributesEx4': 1}),
            'AttributesEx7': 58720256,
            'SpellClassMask_3': m.MUTILATE_HANDS,
            'Description_Lang_enUS': f'Attacks with your {which} weapon for $s1% weapon damage plus {{pot2.avg}}.',
        },
    )


mutilate_mh_203827 = _mutilate_hand(203827, offhand=False)
mutilate_oh_203828 = _mutilate_hand(203828, offhand=True)
scripted_by(mutilate_mh_203827, 'spell_rog_dual_strike_hand')
scripted_by(mutilate_oh_203828, 'spell_rog_dual_strike_hand')

# ---- Doomblade bleed 203829 and tick 203830 (Known-hard 6, R17) ----
# The bleed is the stored-bleed carrier: PERIODIC_DUMMY (226) 2000 ms, 8 s (idx 31), mechanic 15, no haste attribute,
# Ex3 0x80, visible debuff "Bleeding.". The tick 203830 is the damage a script casts per period (bp0 = the stored
# tick): Physical SCHOOL_DAMAGE, Ex3 IGNORE_CASTER_MODIFIERS + ALWAYS_HIT + SUPPRESS_CASTER_PROCS, Ex2 CANT_CRIT,
# DefenseType 0, hidden, potency_excluded. Both carry d2 b11 only (never d0 b20: Doomblade is not Rupture).
doomblade_bleed_203829 = spell(
    id=203829, name='Doomblade', school=School.NORMAL, mechanic=_MECHANIC_BLEED, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=_SCRIPT_CAST_RANGE, duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=2000, mechanic=_MECHANIC_BLEED,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_DOOMBLADE,
    notes='rogue-rework S1a A3, assassination doc "Doomblade" (Known-hard 6): the visible bleed debuff. PERIODIC_DUMMY '
          '2000 ms (a fixed cadence: no SPELL_HASTE_AFFECTS_PERIODIC), 8 s (idx 31), mechanic 15, Ex3 0x80 (stack per '
          'caster), DefenseType 0 (a landed crit never misses its own bleed), icon 1501, 100 yd (script cast). d2 b11 '
          'only. ApplyStoredBleed stores the per-tick amount, spell_rog_doomblade casts the tick.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'SpellClassMask_3': m.DOOMBLADE, 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'AttributesEx3': _ATTR3_STACK_PER_CASTER,
        'Description_Lang_enUS': 'Causes the target to bleed.',
        'AuraDescription_Lang_enUS': 'Bleeding.',
    },
)
scripted_by(doomblade_bleed_203829, 'spell_rog_doomblade')

doomblade_tick_203830 = spell(
    id=203830, name='Doomblade', school=School.NORMAL, mechanic=_MECHANIC_BLEED, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=_SCRIPT_CAST_RANGE,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, mechanic=_MECHANIC_BLEED, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
               potency_excluded='the amount is the stored tick a script passes as bp0 (a share of a Mutilate crit '
                                'that already carried every modifier); percent-of-other-damage, no potency of its own'),
    ],
    spell_icon_id=_ICON_DOOMBLADE,
    notes='rogue-rework S1a A3, assassination doc "Doomblade" (Known-hard 6, R17): the hidden tick cast by '
          'spell_rog_doomblade with bp0 = the stored per-tick amount. Physical SCHOOL_DAMAGE, mechanic 15, Ex3 '
          'IGNORE_CASTER_MODIFIERS 0x20000000 + ALWAYS_HIT 0x40000 + SUPPRESS_CASTER_PROCS 0x10000, Ex2 CANT_CRIT, '
          'DefenseType 0 (never missed, dodged or parried). d2 b11 only. potency_excluded.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'SpellClassMask_3': m.DOOMBLADE, 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'DefenseType': 0, 'AttributesEx2': _ATTR2_CANT_CRIT,
        'AttributesEx3': _ATTR3_IGNORE_CASTER_MODIFIERS | _ATTR3_ALWAYS_HIT | _ATTR3_SUPPRESS_CASTER_PROCS,
        'Description_Lang_enUS': 'Deals Physical damage to the target.',
    },
)

# ---- Blindside buff 203831 and Nature strike 203832 (Known-hard 9, R9, R17) ----
# The buff: 12 s (idx 29), refreshes (never stacks), pct COST -100 on Sinister Strike (d0 b1, so the client sees its
# own family's mod), visible, no charges (spell_rog_sinister_strike_blindside removes it). The strike: Nature
# SCHOOL_DAMAGE whose bp0 is the Sinister Strike hit's final damage (Cold Blood's +20% included), d1 b19 only (R9: no
# d2 b10, or Cold Blood's mask would add itself twice), CANT_CRIT (U13), Ex3 SUPPRESS_CASTER_PROCS + ALWAYS_HIT,
# DefenseType 1, hidden.
blindside_buff_203831 = spell(
    id=203831, name='Blindside', school=School.NORMAL, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=12000,
    effects=[_pct(SpellModOp.COST, -101)],
    spell_icon_id=_ICON_BLINDSIDE,
    notes='rogue-rework S1a A3, assassination doc "Blindside" (Known-hard 9): the visible buff, 12 s (idx 29), '
          'pct COST '
          '-100 (stored -101) on Sinister Strike (m.BLINDSIDE_COST_READ), non-passive, number-free aura text, no '
          'charges (the SS script removes it), Ex 0x20 (never breaks Stealth). No family bits of its own.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'AttributesEx': _ATTR1_ALLOW_WHILE_STEALTHED, **_masks(1, m.BLINDSIDE_COST_READ),
        'Description_Lang_enUS': 'Your next Sinister Strike costs no energy, awards an extra combo point, applies your '
                                 'Lethal poisons and deals additional Nature damage.',
        'AuraDescription_Lang_enUS': 'Your next Sinister Strike is free and deals Nature damage.',
    },
)

blindside_strike_203832 = spell(
    id=203832, name='Blindside', school=School.NATURE, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=_SCRIPT_CAST_RANGE,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
               potency_excluded='the amount is the empowered Sinister Strike hit\'s final Physical damage, passed by '
                                'spell_rog_sinister_strike_blindside as bp0 (percent-of-other-damage)'),
    ],
    spell_icon_id=_ICON_BLINDSIDE,
    notes='rogue-rework S1a A3, assassination doc "Blindside" (Known-hard 9, R9, R17): the hidden Nature half cast by '
          'spell_rog_sinister_strike_blindside, bp0 = the SS hit\'s damage. d1 b19 only (poison damage: Vile Poisons, '
          'Zoldyck, Remorseless capstone and Toxic Blade reach it; NOT d2 b10, R9), Ex2 CANT_CRIT (U13), Ex3 '
          'SUPPRESS_CASTER_PROCS + ALWAYS_HIT, DefenseType 1. potency_excluded.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'SpellClassMask_2': m.POISON_GROUP, 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'DefenseType': 1, 'AttributesEx2': _ATTR2_CANT_CRIT,
        'AttributesEx3': _ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_ALWAYS_HIT,
        'Description_Lang_enUS': 'Deals Nature damage to the target.',
    },
)

# ---- Cold Blood after-buff 203833 and Seal Fate capstone speed 203834 (Known-hard 8, R10) ----
cold_blood_after_203833 = spell(
    id=203833, name='Cold Blood', school=School.NORMAL, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=15000,
    effects=[_aura(AuraType.MOD_WEAPON_CRIT_PERCENT, 3)],
    spell_icon_id=_ICON_COLD_BLOOD,
    notes='rogue-rework S1a A3, assassination doc "Cold Blood" (Known-hard 8, R10): the 15 s (idx 8) after-buff, one '
          'effect: aura 52 MOD_WEAPON_CRIT_PERCENT +4 (stored 3) with EquippedItemClass -1 so it reaches melee '
          'AND ranged '
          'crit (UpdateAllWeaponDependentCritAuras; 57 is spell crit, the handoff\'s "52 + 57" was a slip). Visible, '
          'non-passive, number-free text.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'AttributesEx': _ATTR1_ALLOW_WHILE_STEALTHED,
        'Description_Lang_enUS': 'Your melee and ranged critical strike chance is increased.',
        'AuraDescription_Lang_enUS': 'Critical strike chance increased.',
    },
)

seal_fate_haste_203834 = spell(
    id=203834, name='Seal Fate', school=School.NORMAL, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=4000,
    effects=[_aura(AuraType.MOD_INCREASE_SPEED, 69)],
    spell_icon_id=_ICON_SEAL_FATE,
    notes='rogue-rework S1a A3, assassination doc "Seal Fate" capstone (Known-hard 8): aura 31 MOD_INCREASE_SPEED +70 '
          '(stored 69), 4 s, cast by spell_rog_cold_blood_rework when a finisher consumes Cold Blood. Visible, '
          'non-passive, number-free text.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'AttributesEx': _ATTR1_ALLOW_WHILE_STEALTHED,
        'Description_Lang_enUS': 'Your movement speed is increased.',
        'AuraDescription_Lang_enUS': 'Movement speed increased.',
    },
)

# ---- Shattering Vial splash 203836 (Known-hard 13) ----
# Nature PERIODIC_DAMAGE 1000 ms x 2 s on every enemy within 8 yd of the target's position (A 53 dest at the target /
# B 16, the Spore Cloud shape), ap_potency 15 per tick (30 over the 2 s) [tune], SpellLevel 30, Dispel none (it never
# counts for Mutilate's per-poison bonus), Ex3 SUPPRESS_CASTER_PROCS, hidden. d1 b19 + d2 b13 (not in HfB's mask).
# spell_rog_shattering_vial keeps units IsInCombatWith(caster) (U29).
shattering_vial_splash_203836 = spell(
    id=203836, name='Shattering Vial', school=School.NATURE, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=_SCRIPT_CAST_RANGE, radius_yards=8.0, duration_ms=2000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=1000, ap_potency=15.0,
               potency_kind='periodic', implicit_target_a=_TARGET_DEST_TARGET_ENEMY,
               implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=8.0),
    ],
    spell_icon_id=_ICON_SHATTERING_VIAL,
    notes='rogue-rework S1a A3, assassination doc "Shattering Vial" (Known-hard 13): the splash cast by the dispatcher '
          '(5% per combo point on Envenom / Rupture). Nature PERIODIC_DAMAGE 1 s x 2 s, ap_potency 15 per tick (30 '
          'over 2 s) [tune], SpellLevel 30, 8 yd (A 53 dest at the target / B 16), Dispel none, Ex3 '
          'SUPPRESS_CASTER_PROCS, hidden. d1 b19 + d2 b13 (m.SHATTERING_VIAL; not in Hunger for Blood\'s mask). '
          'spell_rog_shattering_vial filters targets to those in combat with the caster (U29).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'SpellClassMask_2': m.POISON_GROUP, 'SpellClassMask_3': m.SHATTERING_VIAL,
        'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'SpellLevel': 30, 'DefenseType': 1,
        'AttributesEx3': _ATTR3_SUPPRESS_CASTER_PROCS,
        'Description_Lang_enUS': 'Shatters a poison vial, dealing Nature damage over time to enemies near the target.',
    },
)
scripted_by(shattering_vial_splash_203836, 'spell_rog_shattering_vial')

# ---- Toxic Blade debuff 203837 (Known-hard 13, section 13) ----
toxic_blade_debuff_203837 = spell(
    id=203837, name='Toxic Blade', school=School.NATURE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=_SCRIPT_CAST_RANGE, duration_ms=8000,
    effects=[_aura(_AURA_MOD_DAMAGE_FROM_CASTER, 9, target=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_TOXIC_BLADE,
    notes='rogue-rework S1a A3, assassination doc "Toxic Blade" capstone: aura 271 MOD_DAMAGE_FROM_CASTER +10 '
          '(stored 9) '
          'on the target, read by caster guid + class mask (m.POISON_DAMAGE_READ: d1 b19), 8 s (idx 31), Ex3 0x80 (a '
          'second rogue\'s does not replace this one\'s), DefenseType 0 (a Shiv that hit never misses its debuff). '
          'Visible debuff, number-free text; cast on the Shiv\'s hit target by spell_rogue_shared.cpp\'s Shiv script.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'AttributesEx3': _ATTR3_STACK_PER_CASTER, **_masks(1, m.POISON_DAMAGE_READ),
        'Description_Lang_enUS': 'The target takes more damage from the rogue\'s poisons.',
        'AuraDescription_Lang_enUS': 'Taking more damage from the rogue\'s poisons.',
    },
)

# ---- Remorseless buffs 203838 (crit) and 203839 (capstone poison damage) (R12, Known-hard section 13) ----
# 203838 is one row (base 25): the C++ casts it with bp0 = the rank amount (25 / 50). Raw ProcTypeMask 87376 /
# ProcCharges 1 / ProcChance 100 = stock 14143's proc shape (no spell_proc row): the charge is consumed by the proc
# system on the first listed strike that hits; spell_rog_remorseless_attacks_rework rejects the hands (the parent
# removes once).
remorseless_crit_203838 = spell(
    id=203838, name='Remorseless Attacks', school=School.NORMAL, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=20000,
    effects=[_flat(SpellModOp.CRITICAL_CHANCE, 24)],
    spell_icon_id=_ICON_REMORSELESS,
    notes='rogue-rework S1a A3, assassination doc "Remorseless Attacks" (R12, section 13): flat CRITICAL_CHANCE +25 '
          '(stored 24; the C++ passes bp0 25 / 50 by rank) on m.REMORSELESS_READ (SS, Backstab, Ambush, '
          'Mutilate hands, '
          'Ghostly Strike), 20 s (idx 18), raw ProcTypeMask 87376 / ProcCharges 1 / ProcChance 100 (stock '
          '14143\'s proc '
          'shape, no spell_proc row), visible, non-passive, number-free text.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'AttributesEx': _ATTR1_ALLOW_WHILE_STEALTHED, 'ProcTypeMask': 87376, 'ProcCharges': 1, 'ProcChance': 100,
        **_masks(1, m.REMORSELESS_READ),
        'Description_Lang_enUS': 'Your next Sinister Strike, Backstab, Mutilate, Ambush or Ghostly Strike has a higher '
                                 'chance to be a critical strike.',
        'AuraDescription_Lang_enUS': 'Your next strike has a higher chance to be a critical strike.',
    },
)
scripted_by(remorseless_crit_203838, 'spell_rog_remorseless_attacks_rework')

remorseless_poison_203839 = spell(
    id=203839, name='Remorseless Attacks', school=School.NORMAL, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=10000,
    effects=[_pct(SpellModOp.DAMAGE, 9), _pct(SpellModOp.DOT, 9)],
    spell_icon_id=_ICON_REMORSELESS,
    notes='rogue-rework S1a A3, assassination doc "Remorseless Attacks" capstone: eff0 pct DAMAGE +10, eff1 pct '
          'DOT +10 '
          '(stored 9), both on m.REMORSELESS_POISON_READ (d1 b19: rogue poisons and Envenom), 10 s (idx 1), cast '
          'with the crit buff by a rank-2 rogue. Visible, non-passive, number-free text. A DoT applied inside '
          'the window '
          'keeps the bonus for its whole duration (a SpellMod is read at application).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'AttributesEx': _ATTR1_ALLOW_WHILE_STEALTHED,
        **_masks(1, m.REMORSELESS_POISON_READ), **_masks(2, m.REMORSELESS_POISON_READ),
        'Description_Lang_enUS': 'Your poison damage is increased.',
        'AuraDescription_Lang_enUS': 'Poison damage increased.',
    },
)

# ---- Overkill buff 203843 (section 13) ----
# aura 110 MOD_POWER_REGEN_PERCENT misc 3 (energy), base 20 (stored 19; the C++ passes bp0 = the rank amount 20 / 40),
# infinite while stealthed; UpdateOverkill shortens it to OVERKILL_TAIL_MS once stealth ends. Visible, non-passive.
overkill_buff_203843 = spell(
    id=203843, name='Overkill', school=School.NORMAL, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[_aura(AuraType.MOD_POWER_REGEN_PERCENT, 19, _POWER_ENERGY)],
    spell_icon_id=_ICON_OVERKILL,
    notes='rogue-rework S1a A3, assassination doc "Overkill": aura 110 MOD_POWER_REGEN_PERCENT misc 3 (energy) +20 '
          '(stored 19; bp0 = the rank amount 20 / 40 from Rogue::UpdateOverkill), infinite while stealthed, shortened '
          'to OVERKILL_TAIL_MS after it. Visible, non-passive, number-free text, Ex 0x20 (never breaks Stealth).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'AttributesEx': _ATTR1_ALLOW_WHILE_STEALTHED,
        'Description_Lang_enUS': 'Your energy regenerates faster.',
        'AuraDescription_Lang_enUS': 'Energy regeneration increased.',
    },
)

# ---- Vile Poisons helpers 203844-203846 (section 13) ----
# Hidden passives linked to the rank spells (type 2: applied and removed with the rank). eff0 flat DURATION +1000 /
# +2000 / +3000 ms on Wound Poison's d0 b28; 203846 (the capstone rank's) also has a 1 s PERIODIC_DUMMY:
# spell_rog_vile_poisons_mastery keeps rank 3's damage amounts at 30 + Mastery from it.
def _vile_helper(spell_id, rank, poll):
    effects = [_flat(SpellModOp.DURATION, 1000 * rank - 1)]
    if poll:
        effects.append(_aura(AuraType.PERIODIC_DUMMY, 0, amplitude=1000))
    return spell(
        id=spell_id, name='Vile Poisons', school=School.NORMAL, attributes=_ATTR0_TALENT_PASSIVE,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=0.0, duration_ms=-1, effects=effects, spell_icon_id=_ICON_VILE_POISONS,
        notes=f'rogue-rework S1a A3, assassination doc "Vile Poisons": hidden helper of rank {rank} (linked type 2 '
              f'from the rank spell). eff0 flat DURATION +{rank} s (stored {1000 * rank - 1}) on Wound Poison '
              '(m.VILE_POISONS_WOUND_DURATION_READ)' + (', eff1 PERIODIC_DUMMY 1 s: the Mastery poll '
                                                         '(spell_rog_vile_poisons_mastery).' if poll else '.'),
        raw_overrides={
            'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'RangeIndex': 1,
            'SpellLevel': 9 + 5 * 5 + rank, 'ProcTypeMask': 0, 'ProcChance': 101,
            **_masks(1, m.VILE_POISONS_WOUND_DURATION_READ),
            'Description_Lang_enUS': 'Increases the duration of your Wound Poison.',
        },
    )


vile_poisons_helper_r1_203844 = _vile_helper(203844, 1, poll=False)
vile_poisons_helper_r2_203845 = _vile_helper(203845, 2, poll=False)
vile_poisons_helper_r3_203846 = _vile_helper(203846, 3, poll=True)
scripted_by(vile_poisons_helper_r3_203846, 'spell_rog_vile_poisons_mastery')
# The per-rank links (stock Vile Poisons ranks 16513-16515, kept in place by rogue_trigger_spells.py).
linked_spell(16513, vile_poisons_helper_r1_203844.id, 2, comment='Vile Poisons r1 - Wound Poison duration helper (S1)')
linked_spell(16514, vile_poisons_helper_r2_203845.id, 2, comment='Vile Poisons r2 - Wound Poison duration helper (S1)')
linked_spell(16515, vile_poisons_helper_r3_203846.id, 2, comment='Vile Poisons r3 - duration + Mastery helper (S1)')

# ---- Dashing Scoundrel energize 203847 (section 13) ----
dashing_scoundrel_energize_203847 = spell(
    id=203847, name='Dashing Scoundrel', school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[Effect(type=EffectType.ENERGIZE, base_points=0, misc_value=_POWER_ENERGY,
                    implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_DASHING_SCOUNDREL,
    notes='rogue-rework S1a A3, assassination doc "Dashing Scoundrel": the hidden 1 energy refund (ENERGIZE misc 3, '
          'stored 0 = live 1) cast by Rogue::OnRogueDamageCrit, 1 s per-rogue cap in C++. No family bits.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'AttributesEx': _ATTR1_ALLOW_WHILE_STEALTHED,
        'Description_Lang_enUS': 'Restores energy.',
    },
)

# ---- Kingsbane: DoT 203842, hands 203840 / 203841, castable parent 203822 (Known-hard 4) ----
# DoT: Nature PERIODIC_DAMAGE 2000 ms, 14 s (idx 305), ap_potency 23 periodic [tune], SpellLevel 60, Dispel Poison,
# Ex3 0x80, CumulativeAura 0 (StackAmount 0: the aura packet shows the charges, set by AddKingsbaneStacks, R5),
# ProcCharges 0 / ProcTypeMask 0 and no proc row, so nothing drops a charge. d1 b19 + d2 b9. Visible debuff with the
# doc's text. DefenseType 0 (a strike that landed never misses its own debuff).
kingsbane_dot_203842 = spell(
    id=203842, name='Kingsbane', school=School.NATURE, dispel=DispelType.POISON, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=_SCRIPT_CAST_RANGE, duration_ms=14000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000, ap_potency=23.0,
               potency_kind='periodic', implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_KINGSBANE,
    notes='rogue-rework S1a A3, assassination doc "Kingsbane" (Known-hard 4, U28, R5): the DoT. Nature PERIODIC_DAMAGE '
          '2000 ms (fixed cadence), 14 s (idx 305), ap_potency 23 periodic [tune], SpellLevel 60, Dispel Poison, Ex3 '
          '0x80 (stack per caster), CumulativeAura 0, ProcCharges 0, ProcTypeMask 0, no proc row. d1 b19 + d2 b9 '
          '(m.KINGSBANE_DOT: Hunger for Blood and Find Weakness read it). Visible debuff, the doc\'s text. '
          'spell_rog_kingsbane_dot fixes the base once and ChangeAmounts per stack; the stack count shows as charges.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'SpellClassMask_2': m.POISON_GROUP, 'SpellClassMask_3': m.KINGSBANE_DOT,
        'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'SpellLevel': 60, 'DefenseType': 0,
        'AttributesEx3': _ATTR3_STACK_PER_CASTER, 'CumulativeAura': 0, 'ProcCharges': 0, 'ProcTypeMask': 0,
        'Description_Lang_enUS': 'Poisons the target, dealing {pot1} Nature damage every 2 sec. Damage increases as '
                                 'more poisons are applied.',
        'AuraDescription_Lang_enUS': 'Taking Nature damage over time. Damage increases as more poisons are applied.',
    },
)
scripted_by(kingsbane_dot_203842, 'spell_rog_kingsbane_dot')


# The hands: Nature WEAPON_PERCENT_DAMAGE weapon_potency 100 [tune], the stock hand frames (Ex3 MH 0x600 / OH
# 0x1000200, the one-hand weapon mask), DefenseType 2, hidden. d1 b19 + d2 b10 (m.POISON_STRIKE): the only d2 b10
# carriers (R9). The hook records them; the Kingsbane parent resolves Seal Fate / Focused Attacks once, so the hands
# need no script (R15).
def _kingsbane_hand(spell_id, offhand):
    which = 'off hand' if offhand else 'main hand'
    return spell(
        id=spell_id, name='Kingsbane', school=School.NATURE, attributes=_ATTR0_MELEE_STRIKE | _ATTR0_DO_NOT_DISPLAY,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0,
        mana_cost_pct=0, range_yards=None,
        effects=[
            Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=100.0,
                   implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        ],
        spell_icon_id=_ICON_KINGSBANE,
        notes=f'rogue-rework S1a A3, assassination doc "Kingsbane" (Known-hard 4, R3, R9, R15): the {which} hand, '
              'triggered by 203822 eff1 / eff2. Nature WEAPON_PERCENT_DAMAGE weapon_potency 100 [tune], the stock hand '
              f'frame (Ex3 {"0x1000200" if offhand else "0x600"}), one-hand weapon mask 41105, DefenseType 2, '
              'raw RangeIndex 2, SpellLevel 60, hidden. d1 b19 + d2 b10 (m.POISON_STRIKE). No script (the hook '
              'records it, the parent resolves once).',
        raw_overrides={
            'SpellClassSet': _SPELLFAMILY_ROGUE, 'SpellClassMask_2': m.POISON_GROUP,
            'SpellClassMask_3': m.POISON_STRIKE, 'EquippedItemClass': _ITEM_CLASS_WEAPON,
            'EquippedItemSubclass': _ONE_HAND_WEAPONS, 'SpellLevel': 60,
            'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 2, 'RangeIndex': 2, 'ProcChance': 101,
            'AttributesEx3': _ATTR3_NOT_A_PROC | (_ATTR3_REQUIRES_OFF_HAND if offhand else _ATTR3_REQUIRES_MAIN_HAND),
            **({} if offhand else {'AttributesEx4': 1}),
            'AttributesEx7': 58720256,
            'Description_Lang_enUS': f'Attacks with your {which} weapon for $s1% weapon damage as Nature damage.',
        },
    )


kingsbane_mh_203840 = _kingsbane_hand(203840, offhand=False)
kingsbane_oh_203841 = _kingsbane_hand(203841, offhand=True)

# The doc's tooltip verbatim: the tick damage through the DoT's potency text, the periods and counts from the DoT /
# consts.
_KINGSBANE_TEXT = (
    'Strike the target with both weapons and poison them for $203842d, dealing '
    + pot_text(kingsbane_dot_203842, effect=1)
    + ' Nature damage every $203842t1 sec. Each time you apply a Lethal poison to the target, Kingsbane\'s damage '
    f'increases by {_c(KINGSBANE_STACK_PCT)}%, twice as much while Envenom is active. Stacks up to '
    f'{_c(KINGSBANE_MAX_STACKS)} times. Awards $s1 combo $lpoint:points;.'
)

# The castable parent: Mutilate 1329's frame (Attributes 0x50010, Ex 0x8000200, Ex2 0x100000, Ex3 0x1010400:
# REQUIRES_OFF_HAND + SUPPRESS_CASTER_PROCS + REQUIRES_MAIN_HAND, so the parent rolls no procs and the hands' damage
# records feed one resolution), 35 energy [tune], 60 s (Cooldown Haste applies), melee (raw RangeIndex 2), GCD 133 /
# 1000, one-hand weapon mask, SpellLevel and BaseLevel 60, SV 90250. eff0 ADD_COMBO_POINTS 1, eff1 TRIGGER_SPELL
# 203840, eff2 TRIGGER_SPELL 203841. Family bit d2 b22 KINGSBANE_PARENT only (Cold Blood RANGE reader, review M1).
kingsbane_203822 = spell(
    id=203822, name='Kingsbane', school=School.NORMAL, attributes=_ATTR0_MELEE_STRIKE,
    cast_time_ms=0, cooldown_ms=60000, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=35,
    mana_cost_pct=0, range_yards=None,
    effects=[
        Effect(type=EffectType.ADD_COMBO_POINTS, base_points=0, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
               trigger_spell=kingsbane_mh_203840.id),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
               trigger_spell=kingsbane_oh_203841.id),
    ],
    spell_icon_id=_ICON_KINGSBANE,
    notes='rogue-rework S1a A3, assassination doc "Kingsbane" (Known-hard 4, R3): the capstone castable '
          '(SkillLineAbility '
          '30801 via the talent bundling). Mutilate 1329\'s frame (Attributes 0x50010, Ex 0x8000200, Ex2 0x100000, Ex3 '
          '0x1010400, DefenseType 2, PreventionType 2, FacingCasterFlags 1, raw RangeIndex 2), 35 energy [tune], 60 s '
          '(Cooldown Haste applies), GCD 133 / 1000, one-hand weapon mask 41105, SpellLevel / BaseLevel 60, SV 90250. '
          'eff0 ADD_COMBO_POINTS 1, eff1 / eff2 trigger the hands. Family bit d2 b22 KINGSBANE_PARENT only (Cold Blood RANGE reader, S1a review M1). spell_rog_kingsbane: '
          'replaces the old '
          'DoT with a fresh one, resolves the dual strike once, Cold Blood consumption.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'SpellClassMask_3': m.KINGSBANE_PARENT,
        'EquippedItemClass': _ITEM_CLASS_WEAPON,
        'EquippedItemSubclass': _ONE_HAND_WEAPONS, 'SpellLevel': 60, 'BaseLevel': 60, 'CastingTimeIndex': 1,
        'DefenseType': 2, 'PreventionType': 2, 'FacingCasterFlags': 1, 'RangeIndex': 2, 'ProcChance': 101,
        'AttributesEx': 134218240, 'AttributesEx2': 1048576,
        'AttributesEx3': _ATTR3_REQUIRES_OFF_HAND | _ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_REQUIRES_MAIN_HAND,
        'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellVisualID_1': _SV_KINGSBANE,
        'Description_Lang_enUS': _KINGSBANE_TEXT,
    },
)
scripted_by(kingsbane_203822, 'spell_rog_kingsbane')

# ---- Poison Bomb 203807 (Known-hard 10, R4): the castable and the area itself, one row ----
# The P0 204386 shape that passed check 9: Speed 18, 30 yd, eff0 PERSISTENT_AREA_AURA aura DUMMY, A 53 / B 16, radius
# 8, 6 s, SV 90251 (the vial missile and the cloud in one row), plus Ex3 SUPPRESS_TARGET_PROCS 0x20000 ("no initial
# aggro") and SUPPRESS_CASTER_PROCS 0x10000: HasInitialAggro() is false, so the cast never pulls an unengaged enemy
# and rolls no procs (R4, 0-verify item 11). 30 energy, 30 s (Cooldown Haste applies), GCD 133 / 1000, d2 b14. The
# impact and the three pulses are spell_rog_poison_bomb's (ApplyPoison on engaged enemies only). Enemies in the cloud
# may show a "Poison Bomb" DUMMY debuff (accepted, a playtest note).
poison_bomb_203807 = spell(
    id=203807, name='Poison Bomb', school=School.NATURE, attributes=0,
    cast_time_ms=0, cooldown_ms=30000, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=30,
    mana_cost_pct=0, range_yards=30.0, radius_yards=8.0, duration_ms=6000,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY,
               implicit_target_a=_TARGET_DEST_TARGET_ENEMY, implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY,
               radius_yards=8.0),
    ],
    spell_icon_id=_ICON_POISON_BOMB,
    notes='rogue-rework S1a A3, assassination doc "Poison Bomb" (Known-hard 10, R4): castable AND area, one row '
          '(203835 is '
          'not built). The P0 204386 shape: Speed 18, 30 yd, eff0 PERSISTENT_AREA_AURA DUMMY, A 53 / B 16, '
          'radius 8, 6 s, '
          'SV 90251, DefenseType 1, plus Ex3 0x30000 (SUPPRESS_TARGET_PROCS "no initial aggro" + '
          'SUPPRESS_CASTER_PROCS) so '
          'the cast never engages an unengaged enemy. 30 energy, 30 s (Cooldown Haste), GCD 133 / 1000, SpellLevel / '
          'BaseLevel 30, d2 b14 (m.POISON_BOMB). spell_rog_poison_bomb applies the Deadly Poison stacks (engaged '
          'enemies only). The cloud may show a DUMMY debuff icon on enemies (accepted).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'SpellClassMask_3': m.POISON_BOMB, 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'SpellLevel': 30, 'BaseLevel': 30, 'DefenseType': 1, 'Speed': 18.0,
        'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellVisualID_1': _SV_POISON_BOMB,
        'AttributesEx3': _ATTR3_SUPPRESS_TARGET_PROCS | _ATTR3_SUPPRESS_CASTER_PROCS,
        'Description_Lang_enUS': (
            f'Throw a Poison Bomb at an enemy, unleashing deadly fumes that immediately apply '
            f'{_c(POISON_BOMB_IMPACT_STACKS)} stacks of Deadly Poison to enemies near the target and an additional '
            f'stack every {_sec(POISON_BOMB_PULSE_MS)} sec for $d.'),
        'AuraDescription_Lang_enUS': 'Standing in a cloud of poison.',
    },
)
scripted_by(poison_bomb_203807, 'spell_rog_poison_bomb')


# =====================================================================================================================
# Talent ranks (WP-BRIEF section 13). Hidden passives; the rank tooltips are the doc's text with `$sN` / `$<id>sN`
# tokens (the numbers live in one place: the rank row or a const()); a capstone sentence is grey below the last rank.
# =====================================================================================================================

# ---- (0,0) Quick Pace 60390: aura 193 HASTE_ALL +1 / +2 / +3% (the hunter Quick Draw shape) ----
def _quick_pace(spell_id, rank):
    return _rank(
        spell_id, 'Quick Pace', rank, _ROW_QUICK_PACE, [_aura(AuraType.HASTE_ALL, rank - 1)], _ICON_QUICK_PACE,
        'Increases your haste by $s1%.',
        notes='aura 193 HASTE_ALL (cast + melee + ranged haste in one effect, the hunter Quick Draw shape) '
              f'+{rank}% (stored {rank - 1}).')


quick_pace_203800 = _quick_pace(203800, 1)
quick_pace_203801 = _quick_pace(203801, 2)
quick_pace_203802 = _quick_pace(203802, 3)

# ---- (2,2) Doomblade 60391: DUMMY 15 / 30 (% share); the capstone is r2's presence (Envenom reads 203804) ----
_DOOMBLADE_TEXT = ('Your Mutilate critical strikes make the target bleed for $s1% of the damage dealt over $203829d. '
                   'A new Doomblade adds its damage to what remains of the old one.')
_DOOMBLADE_CAP = (f'Capstone Bonus: Your Envenom deals {_c(DOOMBLADE_CAPSTONE_PCT_PER_BLEED)}% more damage for each of your '
                  'bleeds on the target.')


def _doomblade(spell_id, rank):
    return _rank(
        spell_id, 'Doomblade', rank, _ROW_DOOMBLADE, [_dummy(15 * rank - 1)], _ICON_DOOMBLADE,
        _with_cap(_DOOMBLADE_TEXT, _DOOMBLADE_CAP, rank == 2),
        notes=f'DUMMY {15 * rank} (the % share of a Mutilate cast\'s damage; read by GetRankAmount EFFECT_0)'
              + ('; the capstone is HasAura(203804).' if rank == 2 else '.'))


doomblade_203803 = _doomblade(203803, 1)
doomblade_203804 = _doomblade(203804, 2)

# ---- (3,0) Blindside 60392: DUMMY 10 / 20 (% chance on a Mutilate cast) ----
def _blindside(spell_id, rank):
    return _rank(
        spell_id, 'Blindside', rank, _ROW_BLINDSIDE, [_dummy(10 * rank - 1)], _ICON_BLINDSIDE,
        'Your Mutilate has a $s1% chance to make your next Sinister Strike cost no energy, award 2 combo points, apply '
        'both of your Lethal poisons, and deal additional Nature damage equal to its Physical damage.',
        notes=f'DUMMY {10 * rank} (% chance, rolled once per Mutilate cast, x Proc Chance).')


blindside_203805 = _blindside(203805, 1)
blindside_203806 = _blindside(203806, 2)

# ---- (4,2) Shattering Vial 60394: DUMMY 5 (% per combo point) ----
shattering_vial_203808 = _rank(
    203808, 'Shattering Vial', None, _ROW_VIAL, [_dummy(4)], _ICON_SHATTERING_VIAL,
    'Your Envenom and Rupture have a $s1% chance per combo point spent to shatter a poison vial at the target\'s '
    'location, dealing ' + pot_text(shattering_vial_splash_203836, effect=1, variant='total')
    + ' Nature damage over $203836d to all enemies within $203836a1 yards.',
    notes='DUMMY 5 (% per combo point, x Proc Chance); the splash is 203836.')

# ---- (5,2) Venomous Fan 60395: pct DAMAGE +15 / +30 on Fan of Knives; capstone: x2 poison chance (203810) ----
_VENOMOUS_FAN_CAP = 'Capstone Bonus: Your Fan of Knives has double the chance to apply your poisons.'


def _venomous_fan(spell_id, rank):
    return _rank(
        spell_id, 'Venomous Fan', rank, _ROW_VENOMOUS_FAN, [_pct(SpellModOp.DAMAGE, 15 * rank - 1)],
        _ICON_VENOMOUS_FAN, _with_cap('Your Fan of Knives deals $s1% more damage.', _VENOMOUS_FAN_CAP, rank == 2),
        masks={1: m.VENOMOUS_FAN_READ},
        notes=f'pct DAMAGE +{15 * rank} on Fan of Knives (m.VENOMOUS_FAN_READ: d1 b18, 51723 + 52874)'
              + ('; the capstone is HasAura(203810).' if rank == 2 else '.'))


venomous_fan_203809 = _venomous_fan(203809, 1)
venomous_fan_203810 = _venomous_fan(203810, 2)

# ---- (7,1) Zoldyck Recipe 60396: DUMMY 10 / 20 / 30 (% more damage below the health threshold) ----
def _zoldyck(spell_id, rank):
    return _rank(
        spell_id, 'Zoldyck Recipe', rank, _ROW_ZOLDYCK, [_dummy(10 * rank - 1)], _ICON_ZOLDYCK,
        f'Your poisons and bleeds deal $s1% more damage to targets below {_c(ZOLDYCK_HEALTH_PCT)}% health.',
        notes=f'DUMMY {10 * rank} (% more damage, read live per hit and tick by GetHealthClauseMultiplier).')


zoldyck_recipe_203811 = _zoldyck(203811, 1)
zoldyck_recipe_203812 = _zoldyck(203812, 2)
zoldyck_recipe_203813 = _zoldyck(203813, 3)

# ---- (7,2) Cut Throat 60397: DUMMY 4 / 8 (% per combo point on Envenom) ----
def _cut_throat(spell_id, rank):
    return _rank(
        spell_id, 'Cut Throat', rank, _ROW_CUT_THROAT, [_dummy(4 * rank - 1)], _ICON_CUT_THROAT,
        'Your Envenom has a $s1% chance per combo point to apply Garrote to the target.',
        notes=f'DUMMY {4 * rank} (% per combo point, x Proc Chance).')


cut_throat_203814 = _cut_throat(203814, 1)
cut_throat_203815 = _cut_throat(203815, 2)

# ---- (8,0) Toxic Blade 60398: flat EFFECT2 +1 / +2 on Shiv (its index-1 ADD_COMBO_POINTS); capstone casts 203837 ----
_TOXIC_BLADE_CAP = ('Capstone Bonus: For $203837d after your Shiv hits, the target takes $203837s1% more damage from '
                    'your poisons.')


def _toxic_blade(spell_id, rank):
    return _rank(
        spell_id, 'Toxic Blade', rank, _ROW_TOXIC_BLADE, [_flat(SpellModOp.EFFECT2, rank - 1)], _ICON_TOXIC_BLADE,
        _with_cap('Your Shiv awards $s1 additional combo $lpoint:points;.', _TOXIC_BLADE_CAP, rank == 2),
        masks={1: m.TOXIC_BLADE_SHIV_READ},
        notes=f'flat EFFECT2 +{rank} on Shiv 203725 (m.TOXIC_BLADE_SHIV_READ: d0 b29; Shiv\'s ADD_COMBO_POINTS is its '
              'index-1 effect, 0-verify item 7)' + ('; the capstone is HasAura(203817).' if rank == 2 else '.'))


toxic_blade_203816 = _toxic_blade(203816, 1)
toxic_blade_203817 = _toxic_blade(203817, 2)

# ---- (8,2) Indiscriminate Carnage 60399: DUMMY 1 / 2 (extra Rupture targets) ----
def _carnage(spell_id, rank):
    return _rank(
        spell_id, 'Indiscriminate Carnage', rank, _ROW_CARNAGE, [_dummy(rank - 1)], _ICON_CARNAGE,
        'Your Rupture also applies to $s1 additional nearby $lenemy:enemies; already in combat with you or your group.',
        notes=f'DUMMY {rank} (extra enemies; the radius is INDISCRIMINATE_CARNAGE_RADIUS_YD).')


indiscriminate_carnage_203818 = _carnage(203818, 1)
indiscriminate_carnage_203819 = _carnage(203819, 2)

# ---- (9,1) Dashing Scoundrel 60400: DUMMY 5 / 10 (% crit; the energy needs either rank) ----
def _dashing_scoundrel(spell_id, rank):
    return _rank(
        spell_id, 'Dashing Scoundrel', rank, _ROW_DASHING, [_dummy(5 * rank - 1)], _ICON_DASHING_SCOUNDREL,
        'While Envenom is active, your poisons have a $s1% increased chance to critically strike, and their critical '
        f'strikes generate $203847s1 Energy. This energy cannot occur more than once per '
        f'{_sec(DASHING_SCOUNDREL_ICD_MS)} sec.',
        notes=f'DUMMY {5 * rank} (% poison crit, read by Envenom\'s aura script into its eff1; the energy needs either '
              'rank).')


dashing_scoundrel_203820 = _dashing_scoundrel(203820, 1)
dashing_scoundrel_203821 = _dashing_scoundrel(203821, 2)

# ---- (4,3) Fleet Footed r3 203824: aura 172 +10, eff1 DUMMY 10 (% per combo point). r1 / r2 are 31208 / 31209 ----
fleet_footed_203824 = _rank(
    203824, 'Fleet Footed', 3, _ROW_FLEET_FOOTED,
    [_aura(_AURA_MOD_MOUNTED_SPEED_NOT_STACK, 9), _dummy(9)], _ICON_FLEET_FOOTED,
    'Increases your mounted movement speed by $s1%. This does not stack with other movement speed increasing effects. '
    'Your finishing moves have a $s2% chance per combo point to clear any movement speed reduction and immobilization '
    'effects.',
    notes='aura 172 MOD_MOUNTED_SPEED_NOT_STACK +10 (stored 9), eff1 DUMMY 10 (% per combo point, the same at every '
          'rank; read by GetRankAmount EFFECT_1).')

# ---- (2,3) Vigor r2 203823: 14983's frame, aura 35 MOD_INCREASE_ENERGY misc 3 +30 ----
vigor_203823 = _rank(
    203823, 'Vigor', 2, _ROW_VIGOR, [_aura(_AURA_MOD_INCREASE_ENERGY, 29, _POWER_ENERGY)], _ICON_VIGOR,
    'Increases your maximum Energy by $s1.',
    notes='14983\'s frame (rank 1, +15 energy by A2): aura 35 MOD_INCREASE_ENERGY misc 3 +30 (stored 29).')

# ---- (6,0) Overkill 60... 203825-203826: DUMMY 20 / 40 (% energy regeneration, bp0 of the buff 203843) ----
def _overkill(spell_id, rank):
    return _rank(
        spell_id, 'Overkill', rank, _ROW_OVERKILL, [_dummy(20 * rank - 1)], _ICON_OVERKILL,
        f'While stealthed, and for {_sec(OVERKILL_TAIL_MS)} sec after breaking stealth, you regenerate $s1% additional '
        'energy.',
        notes=f'DUMMY {20 * rank} (% energy regeneration; Rogue::UpdateOverkill passes it as bp0 to 203843).')


overkill_203825 = _overkill(203825, 1)
overkill_203826 = _overkill(203826, 2)


# =====================================================================================================================
# SpellDescriptionVariables 1320-1323 (U15, R18): talent bonuses on tooltips. A3 declares, A4 attaches with
# `tooltip_vars=` on the stock rows it owns (and on the three Lethal auras 203701-203703). `{potN*var}` multiplies a
# potency range by the variable. Names are at most 12 characters (a talent_mult chain adds a rank suffix).
# SpellMod DAMAGE / DOT percents are multiplicative in the core (Player::ApplySpellMod), so `product` is right.
# =====================================================================================================================
# 1320 Vile Poisons rank % (Mastery is not shown): the three Lethal auras and Envenom. Use `{potN*vile}`.
tooltip_vile_poisons_1320 = tooltip_vars(
    1320, 'Vile Poisons rank bonus (no Mastery) on the Lethal poison auras and Envenom',
    vile=talent_mult([16513, 16514, 16515], effect=1),
)

# 1321 Venomous Fan % on Fan of Knives. Use `{potN*fan}`.
tooltip_venomous_fan_1321 = tooltip_vars(
    1321, 'Venomous Fan rank bonus on Fan of Knives',
    fan=talent_mult([203809, 203810], effect=1),
    # S2 (U34, R18): Throwing Specialization (5952 / 51679 eff 1: pct DAMAGE on Deadly Throw + Fan of Knives); Fan of
    # Knives' tooltip uses `{potN*fanmult}` (was `fan`).
    throwspec=talent_mult([5952, 51679], effect=1),
    fanmult=product('fan', 'throwspec'),
)

# 1322 Blood Spatter % (Garrote + Rupture) and Seal Fate's +10% DOT (Rupture only). Garrote uses `{potN*blood}`, Rupture
# `{potN*mult}` (= blood x seal). Seal Fate's pct DOT is the 1-based effect 3 of every rank (A2: eff2).
tooltip_blood_spatter_1322 = tooltip_vars(
    1322, 'Blood Spatter on Garrote and Rupture; Seal Fate\'s DOT bonus on Rupture',
    blood=talent_mult([51632, 51633], effect=1),
    seal=talent_mult([14186, 14190, 14193], effect=3),
    mult=product('blood', 'seal'),
    # S2 (U34, R18): From the Shadows' DOT effect (eff 2 of 14057 / 14072: Garrote), Deadliness' DOT effect (eff 2 of
    # 30902-30904: Garrote + Rupture) and Serrated Blades (eff 1 of 14171-14173: Rupture). Garrote's tooltip uses
    # `{potN*garmult}` (was `blood`), Rupture's `{potN*rupmult}` (was `mult`, kept declared: nothing else may read it).
    ftsdot=talent_mult([14057, 14072], effect=2),
    deadly=talent_mult([30902, 30903, 30904], effect=2),
    serrated=talent_mult([14171, 14172, 14173], effect=1),
    garmult=product('blood', 'ftsdot', 'deadly'),
    rupmult=product('blood', 'seal', 'serrated', 'deadly'),
)

# 1323 Seal Fate's +10% direct damage on Eviscerate and Deadly Throw (1-based effect 2 of every rank). Use
# `{potN*seal}`.
tooltip_seal_fate_1323 = tooltip_vars(
    1323, 'Seal Fate direct damage bonus on Eviscerate and Deadly Throw',
    seal=talent_mult([14186, 14190, 14193], effect=2),
    # S2 (U34, R18): Throwing Specialization on Deadly Throw; Deadly Throw's tooltip uses `{potN*dtmult}` / the
    # hand-built `$<dtmult>` (was `seal`); Eviscerate keeps `seal`.
    throwspec=talent_mult([5952, 51679], effect=1),
    dtmult=product('seal', 'throwspec'),
    # S3 (U58, WP-BRIEF section 8): Eviscerate also shows Coup de Grace (eff 1 of 203970-203972) x Surprise Attacks
    # (eff 1 of 32601 / 203981 / 203982); Eviscerate's tooltip uses `$<evmult>` (was `seal`); `seal` stays declared.
    cdg=talent_mult([203970, 203971, 203972], effect=1),
    surprise=talent_mult([32601, 203981, 203982], effect=1),
    evmult=product('seal', 'cdg', 'surprise'),
)

# Doomblade's tick deals a share of hand damage that already went through armor; Unit.cpp checks armor before the bleed
# exemption, so without SPELL_ATTR0_CU_IGNORE_ARMOR every tick would lose armor a second time (S1-CODE-REVIEW M1). Not
# 0x200000 (ignore damage taken mods): Wound Poison's bleed bonus stays live on the tick.
custom_attr(doomblade_tick_203830, 0x8000)
