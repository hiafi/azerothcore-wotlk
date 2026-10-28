"""
Rogue - S3 Combat, data half: every new row 203950-204003 (talent ranks, the Between the Eyes learn rank and marker,
Pistol Shot, Between the Eyes, Grappling Hook, En Garde, Blade Rush, the Opportunity / Primed Powder / Hair Trigger /
Surprise Attacks / Blade Rush / Improved Kick buffs, Anticipation, Celerity's Adrenaline Rush, the Blade Twisting and
Prey on the Weak debuffs, the second strike, the extra shot, the Blade Flurry copy, the Deft Maneuvers / Improved
Riposte / Hack and Slash strikes, the Improved Sprint / Endurance / Improved Feint helpers), the explicit
SkillLineAbility rows 30810 / 30811, the SpellDescriptionVariables 1350-1352 (U58 talent bonuses on tooltips), the
scripted_by / linked_spell / spell_group / custom_attr rows of the new ids and the hidden script numbers (`const()`) the
C++ reads through the generated RogueData.h.

Source of truth: docs/reworks/rogue-combat-rework.md (tooltips and aura texts verbatim),
.agents/plans/rogue-rework/rogue-rework.S3-HANDOFF.md (sections 4-5), rogue-rework.S3a-WP-BRIEF.md (variable names,
bits, effect order, resolutions; the brief wins over the handoff).

Talent rows, their SkillLineAbility bundling (Grappling Hook 30812, En Garde 30813, Blade Rush 30814) and the tab live
in rogue_talents.py; stock rank spells edited in place live in rogue_trigger_spells.py; shared stock rows (Sinister
Strike 1752, Eviscerate 2098, Riposte 14251, Kick 1766, Blade Flurry 13877, Adrenaline Rush 13750, Killing Spree 51690,
Cold Blood 14177's masks) live in rogue_spells.py / rogue_shared.py; S1's SDV 1323 lives in rogue_assassination.py and
S2's SDV 1335 / 1336 in rogue_subtlety.py (extended by S3, U58).

Raw class-mask keys come from `_masks.read_mask_keys` / `clear_mask_keys` / `class_mask_keys` only (letter = effect,
number = dword); never hand-write an EffectSpellClassMask / SpellClassMask key.

Import rule (WP-BRIEF section 11): this file imports only `lib.*` and `_masks`; the other S3 files import from it.
"""

from lib import potency as _potency
from lib.dsl import AuraType, Effect, EffectType, PowerType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import const, custom_attr, linked_spell, scripted_by, skill_line_ability, spell
from lib.dsl.registry import spell_group, spell_group_rule, tooltip_vars
from lib.dsl.tooltip import product, talent_mult

from . import _masks as m

# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h) ----
_SPELLFAMILY_ROGUE = 8
_ATTR0_IS_ABILITY = 0x10
_ATTR0_DO_NOT_DISPLAY = 0x80
_ATTR0_TALENT_PASSIVE = 464                 # ABILITY 0x10 | PASSIVE 0x40 | DO_NOT_DISPLAY 0x80 | DO_NOT_LOG 0x100
_ATTR0_FINISHER = 327696                    # 0x50010: stock Eviscerate / Sinister Strike frame
_ATTR0_SLICE_AND_DICE = 537198608           # 0x20050010: stock Slice and Dice 5171 (finisher frame + NO_IMMUNITIES)
_ATTR1_ALLOW_WHILE_STEALTHED = 0x20         # AttributesEx: a self buff cast while stealthed never breaks Stealth
_ATTR1_NO_THREAT = 0x400
_ATTR1_DISCOUNT_POWER_ON_MISS = 0x8000000   # stock builder frame (Sinister Strike): the energy comes back on a miss
_ATTR1_FINISHER = 0x100200                  # FINISHING_MOVE_DAMAGE 0x100000 | INITIATE_COMBAT 0x200 (stock 2098)
_ATTR1_EN_GARDE = 0x400420                  # stock 5171: FINISHING_MOVE_DURATION 0x400000 | NO_THREAT 0x400 | 0x20
_ATTR2_IGNORE_LOS = 0x4
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_STACK_PER_CASTER = 0x80              # DOT_STACKING_RULE: stack separately for each caster
_ATTR3_REQUIRES_MAIN_HAND = 0x400
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000
_ATTR3_SUPPRESS_TARGET_PROCS = 0x20000      # "no initial aggro": the cast never engages an unengaged enemy
_ATTR3_ALWAYS_HIT = 0x40000
_ATTR3_REQUIRES_OFF_HAND = 0x1000000
_ATTR3_NOT_A_PROC = 0x200                   # SPELL_ATTR3_NOT_A_PROC: the strike may roll weapon poisons
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
_ATTR3_SLICE_AND_DICE = 1342439424          # stock 5171's AttributesEx3 (0x50040000)
_ATTR4_SUPPRESS_WEAPON_PROCS = 0x800000
_ATTR4_SLICE_AND_DICE = 16                  # stock 5171's AttributesEx4
_ATTR6_SLICE_AND_DICE = 8388612             # stock 5171's AttributesEx6 (0x800004)
_CU_IGNORE_ARMOR = 0x8000                   # SPELL_ATTR0_CU_IGNORE_ARMOR (spell_custom_attr)
_CU_POSITIVE_EFF0_EFF1 = 0x6000000          # CU_POSITIVE_EFF0 | CU_POSITIVE_EFF1 (stock 5171's live row, R14)

# ---- targets / auras / misc values ----
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_UNIT_DEST_AREA_ENEMY = 16
_TARGET_DEST_DYNOBJ_ENEMY = 28              # the ground cursor (P0c)
_TARGET_DEST_TARGET_ENEMY = 53
_AURA_PARRY = 47
_AURA_MOD_POWER_REGEN_PERCENT = 110
_AURA_MOD_BASE_RESISTANCE_PCT = 142
_AURA_MOD_MELEE_HASTE = 138
_AURA_MECHANIC_DURATION_MOD = 232
_AURA_MOD_DAMAGE_FROM_CASTER = 271
_AURA_MOD_MINIMUM_SPEED = 305
_AURA_MOD_CRIT_CHANCE_FOR_CASTER = 308
_MISC_ALL_SCHOOLS = 127
_MISC_MAGIC_SCHOOLS = 126
_MISC_PHYSICAL = 1
_MISC_ROOT_MECHANIC = 7
_MISC_POWER_ENERGY = 3
_CR_PROC_CHANCE = 1 << 11                   # 1 << CombatRating.PROC_CHANCE (Accuracy; Malice's shape)

# ---- weapon requirements, ranges, combat-table classes ----
_ITEM_CLASS_WEAPON = 2
_ANY_MELEE_WEAPON = 173555                  # stock Eviscerate / Sinister Strike EquippedItemSubclass
_RANGE_SELF = 1
_RANGE_20_YD = 3
_RANGE_40_YD = 5
_RANGE_100_YD = 6                           # every row C++ casts at an enemy (script casts need a real range)
_DURATION_15_SEC = 8                        # SpellDuration idx 8 (stock Evasion's 15 s; En Garde is a fixed 15 s)
_RADIUS_5_YD = 8                            # SpellRadius idx 8 (5 yd; 8 yd = 14)
_DEFENSE_MELEE = 2                          # DmgClass melee: melee AP, armor, melee crit (Eviscerate's)

# ---- stock icons / visuals (WP-BRIEF section 9) ----
_ICON_QUICK_REFLEXES = 2224
_ICON_ACCURACY = 126                        # = Precision, by ruling
_ICON_BETWEEN_THE_EYES = 538
_ICON_PISTOL_SHOT = 393
_ICON_REINFORCED_LEATHER = 896
_ICON_GRAPPLING_HOOK = 3149
_ICON_QUICK_DRAW = 536
_ICON_RESTLESS_BLADES = 2115
_ICON_IMPROVED_RIPOSTE = 563
_ICON_EN_GARDE = 2781
_ICON_COUP_DE_GRACE = 138
_ICON_DEFT_MANEUVERS = 83
_ICON_HAIR_TRIGGER = 351
_ICON_CELERITY = 2127
_ICON_IMPROVED_FEINT = 539
_ICON_BLADE_RUSH = 457
_ICON_SURPRISE_ATTACKS = 2119
_ICON_OPPORTUNITY = 1631
_ICON_PRIMED_POWDER = 1196
_ICON_SURPRISE_BUFF = 2334
_ICON_BLADE_RUSH_BUFF = 2769
_ICON_ADRENALINE_RUSH = 235
_ICON_ANTICIPATION = 494
_ICON_BLADE_TWISTING = 2108
_ICON_IMPROVED_KICK = 2022
_ICON_SINISTER_STRIKE = 130
_ICON_BLADE_FLURRY = 1477
_ICON_HACK_AND_SLASH = 1462
_ICON_IMPROVED_SPRINT = 516                 # Sprint's (the helper is hidden)
_ICON_ENDURANCE = 178
_ICON_FEINT = 539
_ICON_PREY_ON_THE_WEAK = 2983
_SV_PISTOL_SHOT = 90252                     # mined: Pistol Shot, Between the Eyes, the extra shot
_SV_GRAPPLING_HOOK = 90253
_SV_BLADE_RUSH = 90254
_SV_SINISTER_STRIKE = 253
_SV_RIPOSTE = 3799
_SV_WHIRLWIND = 223                         # stock Whirlwind 1680's visual (Deft Maneuvers strike)
_SV_STRIKE = 39                            # stock strikes' visual (Hack and Slash strikes)

# Talent rows of the S3 grid (WP-BRIEF section 10.1), for SpellLevel = 9 + 5 x row + rank.
_ROW_QUICK_REFLEXES, _ROW_ACCURACY, _ROW_BETWEEN_THE_EYES, _ROW_REINFORCED_LEATHER = 0, 0, 2, 2
_ROW_QUICK_DRAW, _ROW_RESTLESS_BLADES, _ROW_IMPROVED_RIPOSTE = 4, 5, 5
_ROW_COUP_DE_GRACE, _ROW_DEFT_MANEUVERS, _ROW_HAIR_TRIGGER = 6, 6, 6
_ROW_CELERITY, _ROW_IMPROVED_FEINT, _ROW_SURPRISE_ATTACKS = 7, 7, 8


# =====================================================================================================================
# Script numbers (WP-BRIEF section 6; hidden constants, generated RogueData::NAME, read by RogueMechanics.cpp and the
# S3 scripts). Every [tune] number changes here, never in C++.
# =====================================================================================================================
ANTICIPATION_MAX_STACKS = const(
    'ANTICIPATION_MAX_STACKS', 2, 'Anticipation: stored combo points, = the buff 203997\'s stack count [fixed].')
ANTICIPATION_POLL_MS = const(
    'ANTICIPATION_POLL_MS', 100, 'Anticipation: Deadly Throw\'s release poll step, ms [fixed].')
ANTICIPATION_MISSILE_WAIT_MS = const(
    'ANTICIPATION_MISSILE_WAIT_MS', 1500, 'Anticipation: Deadly Throw\'s release poll limit, ms [fixed].')
ADRENALINE_RUSH_EXTRA_POINTS = const(
    'ADRENALINE_RUSH_EXTRA_POINTS', 1, 'Adrenaline Rush: extra combo point per builder cast [fixed].')
CELERITY_DURATION_MS = const(
    'CELERITY_DURATION_MS', 4000, 'Celerity: the granted Adrenaline Rush lasts this long, = 203996\'s duration, ms '
    '[fixed].')
OPPORTUNITY_EMPOWER_PCT = const(
    'OPPORTUNITY_EMPOWER_PCT', 50, 'Opportunity: Pistol Shot bonus damage, % (203984 eff1, the extra shots\' stamp) '
    '[fixed].')
SURPRISE_ATTACKS_EXTRA_SHOTS = const(
    'SURPRISE_ATTACKS_EXTRA_SHOTS', 2, 'Surprise Attacks capstone: extra Pistol Shots [fixed].')
SURPRISE_SHOT_DELAY_MS = const(
    'SURPRISE_SHOT_DELAY_MS', 200, 'Surprise Attacks capstone: delay between the shots, ms [tune].')
IMPROVED_RIPOSTE_EXTRA_TARGETS = const(
    'IMPROVED_RIPOSTE_EXTRA_TARGETS', 2, 'Improved Riposte capstone: extra enemies struck [fixed].')
IMPROVED_RIPOSTE_RADIUS_YD = const(
    'IMPROVED_RIPOSTE_RADIUS_YD', 8.0, 'Improved Riposte capstone: cleave radius around the target, yards [tune].')
DEFT_MANEUVERS_MIN_ENEMIES = const(
    'DEFT_MANEUVERS_MIN_ENEMIES', 3, 'Deft Maneuvers: engaged enemies needed [fixed].')
DEFT_MANEUVERS_MAX_POINTS = const(
    'DEFT_MANEUVERS_MAX_POINTS', 5, 'Deft Maneuvers: point cap of the one grant [fixed].')
DEFT_MANEUVERS_RADIUS_YD = const(
    'DEFT_MANEUVERS_RADIUS_YD', 8.0, 'Deft Maneuvers: count and strike radius (= 203992\'s), yards [tune].')
BLADE_FLURRY_EXTRA_TARGETS = const(
    'BLADE_FLURRY_EXTRA_TARGETS', 4, 'Blade Flurry: copies per hit [fixed].')
BLADE_FLURRY_RADIUS_YD = const(
    'BLADE_FLURRY_RADIUS_YD', 8.0, 'Blade Flurry: copy radius around the hit target, yards [tune].')
BLADE_FLURRY_COPY_PCT = const(
    'BLADE_FLURRY_COPY_PCT', 40, 'Blade Flurry: copy share of the damage dealt, % [fixed].')
PREY_DAMAGE_HEALTH_PCT = const(
    'PREY_DAMAGE_HEALTH_PCT', 35, 'Prey on the Weak: damage clause threshold, target health % [fixed].')
PREY_CRIT_HEALTH_PCT = const(
    'PREY_CRIT_HEALTH_PCT', 90, 'Prey on the Weak: crit clause threshold, target health % [fixed].')
HACK_AND_SLASH_CHANCE_PCT = const(
    'HACK_AND_SLASH_CHANCE_PCT', 6, 'Hack and Slash: base chance, % (x weapon speed / 2600 on autos, x Proc Chance) '
    '[fixed].')
KILLING_SPREE_HOP_RANGE_YD = const(
    'KILLING_SPREE_HOP_RANGE_YD', 10.0, 'Killing Spree: hop range, yards [fixed].')
KILLING_SPREE_STRIKE_INTERVAL_MS = const(
    'KILLING_SPREE_STRIKE_INTERVAL_MS', 500, 'Killing Spree: strike cadence, = 51690\'s amplitude, ms [fixed].')
GRAPPLE_SPEED_XY = const(
    'GRAPPLE_SPEED_XY', 30.0, 'Grappling Hook: horizontal speed, yards per second [tune].')
GRAPPLE_APEX_YD = const(
    'GRAPPLE_APEX_YD', 1.0, 'Grappling Hook: apex height (speedZ = sqrt(2 g apex)), yards [tune].')
UNFAIR_ADVANTAGE_ICD_MS = const(
    'UNFAIR_ADVANTAGE_ICD_MS', 2000, 'Unfair Advantage: the proc row\'s cooldown and the tooltip\'s 2 sec, ms [fixed].')
EN_GARDE_PCT_PER_CP = const(
    'EN_GARDE_PCT_PER_CP', 4, 'En Garde: damage reduction per combo point, % (EffectPointsPerCombo and the tooltip '
    'table) [fixed].')


def _c(row):
    """A const() row's value as tooltip text (8.0 -> '8')."""
    value = row['value']
    return str(int(value)) if float(value).is_integer() else str(value)


def _sec(row):
    """A millisecond const() row's value as whole-second tooltip text (2000 -> '2', 500 -> '0.5')."""
    value = row['value'] / 1000
    return str(int(value)) if float(value).is_integer() else str(value)


def _grey(text):
    """The capstone line on a rank below the last (paladin / hunter / DK rank-text convention)."""
    return f'|cFF9D9D9D{text}|r'


def _with_cap(text, capstone, last):
    """`text` plus the capstone sentence: plain on the last rank, grey below it."""
    return f'{text} {capstone if last else _grey(capstone)}'


# ---- effect helpers ----
def _aura(aura, base_points=0, misc_value=0, target=_TARGET_UNIT_CASTER, **kwargs):
    return Effect(type=EffectType.APPLY_AURA, apply_aura=int(aura), base_points=base_points,
                  misc_value=int(misc_value), implicit_target_a=target, **kwargs)


def _flat(op, base_points):
    return _aura(AuraType.ADD_FLAT_MODIFIER, base_points, op)


def _pct(op, base_points):
    return _aura(AuraType.ADD_PCT_MODIFIER, base_points, op)


def _dummy(base_points):
    return _aura(AuraType.DUMMY, base_points)


def _zero_aura(aura, misc_value=0, target=_TARGET_UNIT_CASTER):
    """A script-set aura: DieSides 0 and base 0, so the stored amount is exactly 0 until the script fills it in."""
    return Effect(type=EffectType.APPLY_AURA, apply_aura=int(aura), base_points=0, die_sides=0,
                  misc_value=int(misc_value), implicit_target_a=target)


def _reads(**by_effect):
    """Reader masks from `eff0=` / `eff1=` / `eff2=` (0-based effect index -> (d0, d1, d2) triple), through the
    `_masks` raw-key helper only (never hand-written keys)."""
    keys = {}
    for name, triple in by_effect.items():
        keys.update(m.read_mask_keys(int(name[-1]), triple))
    return keys


# =====================================================================================================================
# Hidden talent ranks / helpers / visible buffs (WP-BRIEF section 10.15)
# =====================================================================================================================
def _rank(spell_id, name, rank, row, effects, icon, description, raw=None, notes=''):
    """One hidden talent rank passive: Attributes 464, duration -1, SpellLevel 9 + 5 x row + rank, raw ProcTypeMask 0 /
    ProcChance 101. Stored base points = live - 1. `rank` is the NameSubtext number (None for a one-rank talent)."""
    overrides = {
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'RangeIndex': _RANGE_SELF,
        'SpellLevel': 9 + 5 * row + (rank or 1), 'ProcTypeMask': 0, 'ProcChance': 101,
        'NameSubtext_Lang_enUS': '' if rank is None else f'Rank {rank}',
        'Description_Lang_enUS': description,
    }
    overrides.update(raw or {})
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_TALENT_PASSIVE,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0,
        mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1, effects=effects, spell_icon_id=icon,
        notes='rogue-rework S3a A3, combat doc section 5: hidden talent rank passive (Attributes 464, SpellLevel '
              f'= 9 + 5 x {row} + rank, stored = live - 1). ' + notes,
        raw_overrides=overrides,
    )


def _buff(spell_id, name, effects, icon, duration_ms, text, raw=None, notes='', range_index=_RANGE_SELF):
    """A visible, non-passive self buff (custom-spells.md): number-free aura text = the doc's, Ex1 0x20 (a self buff
    cast while stealthed never breaks Stealth)."""
    overrides = {
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'RangeIndex': range_index, 'AttributesEx': _ATTR1_ALLOW_WHILE_STEALTHED,
        'Description_Lang_enUS': text, 'AuraDescription_Lang_enUS': text,
    }
    overrides.update(raw or {})
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0, range_yards=None,
        duration_ms=duration_ms, effects=effects, spell_icon_id=icon, notes=notes, raw_overrides=overrides,
    )


def _hidden_aura(spell_id, name, effects, icon, duration_ms, description, raw=None, notes=''):
    """A hidden self aura that is NOT passive (an aura link / a script cast applies it): DO_NOT_DISPLAY only, Ex1 0x20
    (S2's Enveloping Shadows helper 204173 shape)."""
    overrides = {
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'RangeIndex': _RANGE_SELF, 'AttributesEx': _ATTR1_ALLOW_WHILE_STEALTHED,
        'Description_Lang_enUS': description,
    }
    overrides.update(raw or {})
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY, cast_time_ms=0,
        cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
        range_yards=None, duration_ms=duration_ms, effects=effects, spell_icon_id=icon, notes=notes,
        raw_overrides=overrides,
    )


def _enemy_aura_raw(**extra):
    """Raw columns of a script-cast aura on an enemy: 100 yd (a script cast needs a real range), no facing."""
    raw = {'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
           'RangeIndex': _RANGE_100_YD, 'FacingCasterFlags': 0}
    raw.update(extra)
    return raw


# =====================================================================================================================
# SpellDescriptionVariables 1350-1352 (U58): talent bonuses on the Sinister Strike / Pistol Shot / Between the Eyes
# tooltips. SpellMod DAMAGE percents are multiplicative in the core (Player::ApplySpellMod), so `product` is right.
# talent_mult(effect=N) is 1-based. Names are at most 12 characters (helper suffixes included). A4 attaches 1350 to
# Sinister Strike; 1351 / 1352 are attached on Pistol Shot / Between the Eyes below (declared first: a spell takes its
# SDV object at construction).
# =====================================================================================================================
# 1350 Sinister Strike: Improved Sinister Strike (eff 1 of 13732 / 13863) x Surprise Attacks (eff 1 of 32601 / 203981 /
# 203982). Use `{potN*ssmult}` and the weapon percent `${$s1*$<ssmult>}`.
tooltip_sinister_strike_1350 = tooltip_vars(
    1350, 'Improved Sinister Strike x Surprise Attacks on Sinister Strike',
    impss=talent_mult([13732, 13863], effect=1),
    surprise=talent_mult([32601, 203981, 203982], effect=1),
    ssmult=product('impss', 'surprise'),
)

# 1351 Pistol Shot: Surprise Attacks. Use `{potN*surprise}` (product() needs two factors, so the one variable is used
# directly).
tooltip_pistol_shot_1351 = tooltip_vars(
    1351, 'Surprise Attacks on Pistol Shot',
    surprise=talent_mult([32601, 203981, 203982], effect=1),
)

# 1352 Between the Eyes: Coup de Grace (eff 1 of 203970-203972) x Surprise Attacks.
tooltip_between_the_eyes_1352 = tooltip_vars(
    1352, 'Coup de Grace x Surprise Attacks on Between the Eyes',
    cdg=talent_mult([203970, 203971, 203972], effect=1),
    surprise=talent_mult([32601, 203981, 203982], effect=1),
    btemult=product('cdg', 'surprise'),
)


# =====================================================================================================================
# Between the Eyes: the learn rank, the marker, Pistol Shot, Between the Eyes, Opportunity, Primed Powder
# =====================================================================================================================

# ---- Primed Powder 203985 (U61) ----
# pct DAMAGE +20 per stack on Between the Eyes (d2 b5), CumulativeAura 5 (stacks multiply on purpose: 5 stacks = +100%),
# 30 s (idx 9), visible; Between the Eyes' script removes it on the hit.
primed_powder_203985 = _buff(
    203985, 'Primed Powder', [_pct(SpellModOp.DAMAGE, 19)], _ICON_PRIMED_POWDER, 30000,
    'Your next Between the Eyes deals more damage.', raw={'CumulativeAura': 5, **_reads(eff0=m.PRIMED_POWDER_READ)},
    notes='rogue-rework S3a A3, combat doc "Primed Powder" (U61): pct DAMAGE +20% per stack (stored 19) on '
          'm.PRIMED_POWDER_READ (Between the Eyes d2 b5), CumulativeAura 5 (the 5 stacks multiply on purpose), 30 s '
          '(idx 9), visible, number-free text, Ex1 0x20. No spell_proc row; spell_rog_between_the_eyes removes it.',
)

# ---- Opportunity 203983 + companion 203984 (U61, item 6) ----
# 203983: visible DUMMY, CumulativeAura 3, 20 s. 203984: the hidden companion (linked type 2) that carries the
# SpellMods:
# pct COST -100 (stored -101) and pct DAMAGE +50 (stored 49) on Pistol Shot d2 b4. CumulativeAura 0, so the companion
# stays one stack and the cost mod is never multiplied by the parent's stack count.
opportunity_buff_203983 = _buff(
    203983, 'Opportunity', [_dummy(0)], _ICON_OPPORTUNITY, 20000,
    'Your next Pistol Shot is free and deals more damage.', raw={'CumulativeAura': 3},
    notes='rogue-rework S3a A3, combat doc "Opportunity" (U61, R21): visible DUMMY, CumulativeAura 3 (the charges '
          'show as the stack count), 20 s (idx 18), number-free text, Ex1 0x20. Granted by Sinister Strike\'s second '
          'strike, Eviscerate (marker held) and every Riposte hit (Rogue::GrantOpportunity); one stack is spent in '
          'Pistol Shot\'s AfterCast (R12). spell_linked_spell(203983, 203984, 2) holds the companion.',
)
opportunity_companion_203984 = _hidden_aura(
    203984, 'Opportunity',
    [_pct(SpellModOp.COST, -101), _pct(SpellModOp.DAMAGE, OPPORTUNITY_EMPOWER_PCT['value'] - 1)],
    _ICON_OPPORTUNITY, 20000, 'Pistol Shot costs no energy and deals more damage.',
    raw={'CumulativeAura': 0, **_reads(eff0=m.OPPORTUNITY_READ, eff1=m.OPPORTUNITY_READ)},
    notes='rogue-rework S3a A3, combat doc "Opportunity" (U61, item 6): hidden companion, held by '
          'spell_linked_spell(203983, 203984, 2) (it lives and dies with the parent, refreshed on every stack '
          'change). eff0 pct COST -100 (stored -101) and eff1 pct DAMAGE +50 (stored OPPORTUNITY_EMPOWER_PCT - 1), '
          'both '
          'on m.OPPORTUNITY_READ (Pistol Shot d2 b4; the extra shots carry d2 b24 and never see it). CumulativeAura 0 '
          'so the companion stays one stack (the cost mod is not multiplied). 20 s like the parent, DO_NOT_DISPLAY '
          'but not PASSIVE (an aura link needs a real aura), Ex1 0x20.',
)
linked_spell(opportunity_buff_203983.id, opportunity_companion_203984.id, 2,
             'Opportunity: the hidden companion that carries the cost and damage SpellMods lives with the buff')

# ---- Pistol Shot 203958 (U55, R25) ----
# Physical SCHOOL_DAMAGE ap_potency 90 direct (M2c; 120 in M2a) (SpellLevel 20) + ADD_COMBO_POINTS 1. Builder frame (typed 327696,
# Sinister Strike's raw AttributesEx 0x8000000 minus INITIATE_COMBAT: no auto-attack toward a 20 yd target), 30 energy,
# 20 yd (idx 3), Speed 0 (the hit resolves in the cast), DefenseType 2 (melee AP / armor / melee crit), no weapon at all
# (R25: EquippedItemClass -1, no Ex3 0x400), no USES_RANGED_SLOT, FacingCasterFlags 1, GCD 133 / 1000, SV 90252.
# d2 b4 | d2 b19 (m.PISTOL_SHOT_CLASS: the direct-builder group, so Seal Fate / Lethality / Cold Blood reach it).
pistol_shot_203958 = spell(
    id=203958, name='Pistol Shot', school=School.NORMAL, attributes=_ATTR0_FINISHER,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=30, mana_cost_pct=0,
    range_yards=None,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=90.0, potency_kind='direct',
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_PISTOL_SHOT,
    notes='rogue-rework S3a A3, combat doc "Pistol Shot" (U55, R25, Known-hard 3): learned from the Between the Eyes '
          'rank 203956 (SkillLineAbility 30810). eff0 Physical SCHOOL_DAMAGE ap_potency 50 direct [tune] at SpellLevel '
          '20 (120 since M2a), eff1 ADD_COMBO_POINTS 1. Builder frame: typed 327696, AttributesEx 0x8000000 (energy back on a miss), '
          'PreventionType 2, 30 energy, 20 yd (idx 3), Speed 0 (the combo point, Opportunity, Primed Powder, Quick '
          'Draw and Anticipation all resolve in the cast), DefenseType 2 (the melee AP Eviscerate uses), '
          'EquippedItemClass -1 and no Ex3 0x400: needs no weapon at all (R25), FacingCasterFlags 1, GCD 133 / 1000, '
          'SV 90252. d2 b4 | d2 b19 (m.PISTOL_SHOT_CLASS). Tooltip quotes the damage times the Surprise Attacks factor '
          '(SDV 1351). spell_rog_pistol_shot: latches Opportunity, OnPistolShotHit, spends one stack in AfterCast. '
          'M2a (M1 C1, [tune]): ap_potency 50 -> 120; M2c (user 2026-10-28, -25%): 120 -> 90 (the extra shot 203988 '
          'matches).',
    tooltip_vars=tooltip_pistol_shot_1351,
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.PISTOL_SHOT_CLASS), 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'AttributesEx': _ATTR1_DISCOUNT_POWER_ON_MISS, 'PreventionType': 2,
        'DefenseType': _DEFENSE_MELEE, 'FacingCasterFlags': 1, 'RangeIndex': _RANGE_20_YD, 'Speed': 0.0,
        'SpellLevel': 20, 'SpellVisualID_1': _SV_PISTOL_SHOT, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000,
        'Description_Lang_enUS': 'Draw a concealed pistol and fire a quick shot at an enemy, dealing {pot1*surprise} '
                                 'Physical damage. Usable while moving. Awards $s2 combo point.',
    },
)
scripted_by(pistol_shot_203958, 'spell_rog_pistol_shot')

# ---- Between the Eyes 203959 (U55, R25) ----
# Eviscerate's finisher frame (typed 327696, raw AttributesEx 0x100200, PreventionType 2) with no weapon requirement
# (R25), Physical SCHOOL_DAMAGE ap_potency 36.855 + cp_ap_potency 58.212 [tune] (M2c user ruling 2026-10-28: x1.8 of M2a's
# 20.475 / 32.34, which were 75% of Eviscerate; now ~104% of Eviscerate's 35.49 / 56.056, the ratio is no longer fixed), SpellLevel 20, 35 energy, 20 yd, Speed 0, no stun, GCD 133 / 1000, SV 90252. d2 b5 | d2 b18, never
# d0 b17 (m.BETWEEN_THE_EYES_CLASS).
_BTE_FLAT = _potency.resolve(
    _potency.PotencyEffect(ap_potency=36.855, kind=_potency.KIND_DIRECT, t_ms=1500.0), spell_level=20)
_BTE_CP = _potency.resolve(
    _potency.PotencyEffect(ap_potency=58.212, kind=_potency.KIND_PERIODIC, t_ms=1500.0), spell_level=20)


def _expr_plus(resolved, extra, *, ticks=1.0, scale=1.0):
    """`lib.potency.tooltip_expression` with the constant/stat term `extra` added INSIDE every branch of the outer
    `$max()` (a top-level `+` outside it is dropped by the client; potency.md "Tooltips"). Same shape as
    rogue_spells.py's `_expr_plus` (an own copy: this file imports no sibling)."""
    bonus = _potency._stat_bonus_term(resolved, ticks)
    tail = '+'.join(t for t in (bonus, extra) if t)
    suffix = f'+{tail}' if tail else ''
    f = _potency._fmt
    return (
        f'$max($max({tail or "0"},{f(resolved.tooltip_low_intercept * ticks * scale)}'
        f'+{f(resolved.tooltip_low_slope * ticks * scale)}*$PL{suffix}),'
        f'{f(resolved.points_per_level * ticks * scale)}*$max(0,$PL-{f(resolved.tooltip_high_offset)}){suffix})'
    )


# The 5-combo-point average (flat line + 5 x the per-point line, melee AP terms) inside one `$max()`, times the
# Coup de Grace x Surprise Attacks factor `$<btemult>` (SDV 1352).
_BTE_5CP_DAMAGE = '${' + _expr_plus(
    _BTE_FLAT,
    f'{_potency._fmt(5 * _BTE_CP.level60_value)}+{_potency._fmt(5 * _BTE_CP.ap_coefficient)}*$AP',
    scale=1.0 + _BTE_FLAT.variance_pct / 200.0) + '*$<btemult>}'

between_the_eyes_203959 = spell(
    id=203959, name='Between the Eyes', school=School.NORMAL, attributes=_ATTR0_FINISHER,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=35, mana_cost_pct=0,
    range_yards=None,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=36.855, cp_ap_potency=58.212, potency_kind='direct',
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_BETWEEN_THE_EYES,
    notes='rogue-rework S3a A3, combat doc "Between the Eyes (spell)" (U55, R25, Known-hard 3): learned from the rank '
          '203956 (SkillLineAbility 30811). Eviscerate 2098\'s finisher frame (typed 327696, AttributesEx 0x100200, '
          'PreventionType 2) without the weapon requirement and Ex3 0x400 (R25: EquippedItemClass -1). eff0 Physical '
          'SCHOOL_DAMAGE ap_potency 36.855 + cp_ap_potency 58.212 direct [tune] (M2c: x1.8 of M2a\'s 20.475 / 32.34, ~104% '
          'of Eviscerate; M2a R2 was 75% of Eviscerate, before that 14.625 / 23.1) at SpellLevel 20, 35 energy, 20 yd (idx 3), Speed 0, DefenseType 2, no stun, GCD '
          '133 '
          '/ 1000, SV 90252. d2 b5 | d2 b18 (m.BETWEEN_THE_EYES_CLASS), never d0 b17. The tooltip hand-builds the '
          '5-point value like Deadly Throw\'s and multiplies it by Coup de Grace x Surprise Attacks (SDV 1352). '
          'spell_rog_between_the_eyes: removes Primed Powder, ConsumeBladeRush on the hit.',
    tooltip_vars=tooltip_between_the_eyes_1352,
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.BETWEEN_THE_EYES_CLASS), 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'AttributesEx': _ATTR1_FINISHER, 'PreventionType': 2, 'DefenseType': _DEFENSE_MELEE,
        'FacingCasterFlags': 1, 'RangeIndex': _RANGE_20_YD, 'Speed': 0.0, 'SpellLevel': 20,
        'SpellVisualID_1': _SV_PISTOL_SHOT, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000,
        'Description_Lang_enUS': (
            f'Finishing move that shoots the target between the eyes, dealing {_BTE_5CP_DAMAGE} Physical damage at 5 '
            'combo points. Each stack of Primed Powder increases the damage by $203985s1%. Usable while moving.'),
    },
)
scripted_by(between_the_eyes_203959, 'spell_rog_between_the_eyes')

# ---- the Between the Eyes talent: marker 203957 and the learn rank 203956 (C7, item 3) ----
# The marker: hidden passive DUMMY 25 (the second strike's % chance; its presence also gates Eviscerate's Opportunity),
# learned by the rank. The rank: eff0 LEARN_SPELL Pistol Shot, eff1 LEARN_SPELL Between the Eyes, eff2 LEARN_SPELL the
# marker (the DK 61154 shape: `_addTalentAurasAndSpells` learns the targets as temporary spells and never casts a learn
# rank as an aura; resetTalents unlearns them), SpellLevel 20, hidden.
between_the_eyes_marker_203957 = _rank(
    203957, 'Between the Eyes', None, _ROW_BETWEEN_THE_EYES, [_dummy(24)], _ICON_BETWEEN_THE_EYES,
    'Your Sinister Strike has a $s1% chance to strike a second time and grant Opportunity.',
    notes='The talent\'s marker (C7): DUMMY 25 (the % chance of Sinister Strike\'s second strike, read by '
          'GetRankAmount EFFECT_0 in Rogue::OnSinisterStrikeHit; presence also gates Eviscerate\'s Opportunity). '
          'Taught by the learn rank 203956 (LEARN_SPELL eff2) and checked with HasAura / known.')

between_the_eyes_learn_203956 = _rank(
    203956, 'Between the Eyes', 1, _ROW_BETWEEN_THE_EYES,
    [Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=_TARGET_UNIT_CASTER,
            trigger_spell=pistol_shot_203958.id),
     Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=_TARGET_UNIT_CASTER,
            trigger_spell=between_the_eyes_203959.id),
     Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=_TARGET_UNIT_CASTER,
            trigger_spell=between_the_eyes_marker_203957.id)],
    _ICON_BETWEEN_THE_EYES,
    'Teaches Pistol Shot and Between the Eyes. Your Sinister Strike has a $203957s1% chance to strike a second time '
    'and grant Opportunity, and your Eviscerate always grants Opportunity. Opportunity makes your next Pistol Shot '
    f'cost no energy, deal {_c(OPPORTUNITY_EMPOWER_PCT)}% more damage and grant a stack of Primed Powder. Each stack '
    f'of '
    'Primed Powder increases the damage of your next Between the Eyes by $203985s1%.',
    notes='The talent rank (C7): three LEARN_SPELL effects (Pistol Shot 203958, Between the Eyes 203959, the marker '
          '203957). SpellLevel 20 (row 2 rank 1), hidden. Tooltip = the doc\'s; 25 / 20 come from the marker\'s and '
          'Primed Powder\'s own rows, 50 from OPPORTUNITY_EMPOWER_PCT.')

skill_line_ability(id=30810, skill_line=38, spell_id=pistol_shot_203958.id, class_mask=8, min_skill_line_rank=1,
                   acquire_method=0)
skill_line_ability(id=30811, skill_line=38, spell_id=between_the_eyes_203959.id, class_mask=8, min_skill_line_rank=1,
                   acquire_method=0)

# ---- the second strike 203986 (U61, C9) ----
# Sinister Strike's weapon frame (eff0 WEAPON_PERCENT_DAMAGE weapon_potency 250, eff1 NORMALIZED_WEAPON_DMG
# sp_potency 10
# direct T 1500, SpellLevel 1), no ADD_COMBO_POINTS (the point goes through GainComboPoints). Own bit d2 b23 only,
# Ex3 SUPPRESS_CASTER_PROCS | main hand, Ex4 SUPPRESS_WEAPON_PROCS, 100 yd, no facing, SS's visual, hidden.
sinister_strike_second_strike_203986 = spell(
    id=203986, name='Sinister Strike', school=School.NORMAL, attributes=_ATTR0_IS_ABILITY | _ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=None,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=250, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=10, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_SINISTER_STRIKE,
    notes='rogue-rework S3a A3, combat doc "Between the Eyes (talent)" (U61, C9, R21): the second strike cast by '
          'Rogue::OnSinisterStrikeHit. Sinister Strike 1752\'s weapon lines (eff0 weapon_potency 250 since M2a, eff1 '
          'NORMALIZED_WEAPON_DMG sp_potency 10 direct T 1500, SpellLevel 1) without ADD_COMBO_POINTS (R: no combo '
          'attributes; the point is granted through GainComboPoints). Own bit d2 b23 only (m.SS_SECOND_STRIKE_CLASS: '
          'Improved Sinister Strike, Aggression and Surprise Attacks read it; Blindside\'s charged mods, Cold Blood '
          'and '
          'the companion never land on it), Ex3 SUPPRESS_CASTER_PROCS | REQUIRES_MAIN_HAND, Ex4 '
          'SUPPRESS_WEAPON_PROCS, weapon requirement as 1752, 100 yd (idx 6), FacingCasterFlags 0, DefenseType 2, '
          'SV 253, hidden.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.SS_SECOND_STRIKE_CLASS),
        'EquippedItemClass': _ITEM_CLASS_WEAPON, 'EquippedItemSubclass': _ANY_MELEE_WEAPON, 'CastingTimeIndex': 1,
        'AttributesEx3': _ATTR3_REQUIRES_MAIN_HAND | _ATTR3_SUPPRESS_CASTER_PROCS,
        'AttributesEx4': _ATTR4_SUPPRESS_WEAPON_PROCS, 'DefenseType': _DEFENSE_MELEE, 'RangeIndex': _RANGE_100_YD,
        'FacingCasterFlags': 0, 'SpellLevel': 1, 'SpellVisualID_1': _SV_SINISTER_STRIKE,
        'Description_Lang_enUS': 'Strikes the target a second time for Sinister Strike\'s damage.',
    },
)

# ---- Hair Trigger buff 203987 (item 3) ----
# pct DAMAGE +200 [tune] (stored 199) on Pistol Shot d2 b4 (m.HAIR_TRIGGER_READ), ProcCharges 1 (charged: the next
# Pistol
# Shot consumes it, empowered or not; no spell_proc row), 15 s (idx 8), visible.
hair_trigger_buff_203987 = _buff(
    203987, 'Hair Trigger', [_pct(SpellModOp.DAMAGE, 199)], _ICON_HAIR_TRIGGER, 15000,
    'Your next Pistol Shot deals more damage.', raw={'ProcCharges': 1, **_reads(eff0=m.HAIR_TRIGGER_READ)},
    notes='rogue-rework S3a A3, combat doc "Hair Trigger" (item 3, R12): pct DAMAGE +200 [tune] (stored 199) on '
          'm.HAIR_TRIGGER_READ (Pistol Shot d2 b4 only; the extra shots carry d2 b24 and never see it), ProcCharges 1 '
          '(charged, no spell_proc row: the core consumes it when the shot\'s damage read it, so a dodged shot keeps '
          'it), 15 s (idx 8), visible, number-free text, Ex1 0x20.',
)

# ---- the extra shot 203988 (capstone of Surprise Attacks, C9) ----
# Pistol Shot's damage line on its own bit d2 b24 (m.PISTOL_SHOT_EXTRA_CLASS), no combo point, 100 yd, no facing,
# Ex3 SUPPRESS_CASTER_PROCS, hidden. spell_rog_pistol_shot_extra applies Opportunity's 50% from the stamp.
pistol_shot_extra_203988 = spell(
    id=203988, name='Pistol Shot', school=School.NORMAL, attributes=_ATTR0_IS_ABILITY | _ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=None,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=90.0, potency_kind='direct',
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_PISTOL_SHOT,
    notes='rogue-rework S3a A3, combat doc "Surprise Attacks" (C9): the capstone\'s extra shots. Pistol Shot 203958\'s '
          'damage line (Physical ap_potency 90 direct since M2c, SpellLevel 20) on its own bit d2 b24 only '
          '(m.PISTOL_SHOT_EXTRA_CLASS: Improved SS / Aggression / Surprise Attacks / Blade Twisting read it; Hair '
          'Trigger, Opportunity and Primed Powder never do), no combo point, 100 yd (idx 6), FacingCasterFlags 0, '
          'DefenseType 2, Ex3 SUPPRESS_CASTER_PROCS, SV 90252, hidden. spell_rog_pistol_shot_extra multiplies the '
          'hit by (100 + OPPORTUNITY_EMPOWER_PCT)% when the stamp says the first shot was empowered.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.PISTOL_SHOT_EXTRA_CLASS), 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'AttributesEx3': _ATTR3_SUPPRESS_CASTER_PROCS, 'DefenseType': _DEFENSE_MELEE,
        'RangeIndex': _RANGE_100_YD, 'FacingCasterFlags': 0, 'SpellLevel': 20, 'SpellVisualID_1': _SV_PISTOL_SHOT,
        'Description_Lang_enUS': 'Fires an additional pistol shot at the target.',
    },
)
scripted_by(pistol_shot_extra_203988, 'spell_rog_pistol_shot_extra')

# ---- Surprise Attacks buff 203989 (capstone) ----
surprise_attacks_buff_203989 = _buff(
    203989, 'Surprise Attacks', [_dummy(0)], _ICON_SURPRISE_BUFF, 20000,
    'Your next Pistol Shot fires additional times.',
    notes='rogue-rework S3a A3, combat doc "Surprise Attacks": DUMMY, 20 s (idx 18), visible, number-free text, Ex1 '
          '0x20. Cast by Rogue::OnSinisterStrikeHit when the second strike fires and the roll passes; consumed by '
          'the next Pistol Shot (two extra shots at +SURPRISE_SHOT_DELAY_MS).',
)


# =====================================================================================================================
# Talent ranks
# =====================================================================================================================

# ---- (0,0) Quick Reflexes 60405: aura 193 HASTE_ALL +1 / +2 / +3% (S1 Quick Pace's shape) ----
def _quick_reflexes(spell_id, rank):
    return _rank(
        spell_id, 'Quick Reflexes', rank, _ROW_QUICK_REFLEXES, [_aura(AuraType.HASTE_ALL, rank - 1)],
        _ICON_QUICK_REFLEXES, 'Increases your haste by $s1%.',
        notes=f'aura 193 HASTE_ALL (cast + melee + ranged haste in one effect, Quick Pace\'s shape) +{rank}% '
              f'(stored {rank - 1}).')


quick_reflexes_203950 = _quick_reflexes(203950, 1)
quick_reflexes_203951 = _quick_reflexes(203951, 2)
quick_reflexes_203952 = _quick_reflexes(203952, 3)


# ---- (0,3) Accuracy 60406: aura 306 MOD_CUSTOM_STAT_PCT misc 1 << 11 (Proc Chance) +2 / +4 / +6% (Malice's shape) ----
def _accuracy(spell_id, rank):
    return _rank(
        spell_id, 'Accuracy', rank, _ROW_ACCURACY, [_aura(AuraType.MOD_CUSTOM_STAT_PCT, 2 * rank - 1, _CR_PROC_CHANCE)],
        _ICON_ACCURACY, 'Increases your Proc Chance by $s1%.',
        notes=f'aura 306 MOD_CUSTOM_STAT_PCT misc 1 << 11 (Proc Chance) +{2 * rank}% (stored {2 * rank - 1}; '
              'Malice\'s shape). Accuracy shares Precision\'s icon by ruling.')


accuracy_203953 = _accuracy(203953, 1)
accuracy_203954 = _accuracy(203954, 2)
accuracy_203955 = _accuracy(203955, 3)


# ---- (2,2) Reinforced Leather 60408: aura 142 MOD_BASE_RESISTANCE_PCT misc 1 +15 / +30 / +45% (U57) ----
def _reinforced_leather(spell_id, rank):
    return _rank(
        spell_id, 'Reinforced Leather', rank, _ROW_REINFORCED_LEATHER,
        [_aura(_AURA_MOD_BASE_RESISTANCE_PCT, 15 * rank - 1, _MISC_PHYSICAL)], _ICON_REINFORCED_LEATHER,
        'Increases your armor contribution from cloth and leather items by $s1%.',
        notes=f'aura 142 MOD_BASE_RESISTANCE_PCT misc 1 +{15 * rank}% (stored {15 * rank - 1}; Enforcer Stance\'s eff0 '
              'shape: the core multiplies BASE_PCT mods, so rank 3 in stance is x2.61 item armor, U57).')


reinforced_leather_203960 = _reinforced_leather(203960, 1)
reinforced_leather_203961 = _reinforced_leather(203961, 2)
reinforced_leather_203962 = _reinforced_leather(203962, 3)

# ---- (4,3) Quick Draw 60410: DUMMY 1 (extra combo points on an empowered Pistol Shot) ----
quick_draw_203964 = _rank(
    203964, 'Quick Draw', None, _ROW_QUICK_DRAW, [_dummy(0)], _ICON_QUICK_DRAW,
    'Your empowered Pistol Shots award $s1 additional combo point.',
    notes='DUMMY 1 (extra combo points; read by GetRankAmount EFFECT_0 in Rogue::OnPistolShotHit).')

# ---- (5,0) Restless Blades 60411: DUMMY 1000 (ms of cooldown per combo point spent) ----
restless_blades_203965 = _rank(
    203965, 'Restless Blades', None, _ROW_RESTLESS_BLADES, [_dummy(999)], _ICON_RESTLESS_BLADES,
    'Your finishing moves reduce the remaining cooldown of Adrenaline Rush, Blade Flurry, Blade Rush, Grappling Hook, '
    'Killing Spree and Sprint by $/1000;s1 sec per combo point spent, and while you are in Enforcer Stance also of '
    'Evasion and Cloak of Shadows. Combo points you gain beyond your maximum are stored as Anticipation, up to '
    f'{_c(ANTICIPATION_MAX_STACKS)}, and granted after your next finishing move.',
    notes='DUMMY 1000 (ms per combo point spent; read by GetRankAmount EFFECT_0 in Rogue::ApplyCombatSpentClauses; '
          'presence gates Rogue::BankAnticipation).')


# ---- (5,1) Improved Riposte 60412: aura 47 parry +1 / +2 / +3%, pct THREAT +20 / +40 / +60% (Riposte d1 b8 | Ghostly
# Strike d2 b21), the capstone is rank 3's presence (the cleave 203993) ----
_IMPROVED_RIPOSTE_TEXT = ('Increases your Parry chance by $s1% and the threat of your Riposte and Ghostly Strike by '
                          '$s2%.')
_IMPROVED_RIPOSTE_CAP = (f'Capstone: Your Riposte strikes {_c(IMPROVED_RIPOSTE_EXTRA_TARGETS)} additional nearby '
                         'enemies.')


def _improved_riposte(spell_id, rank):
    return _rank(
        spell_id, 'Improved Riposte', rank, _ROW_IMPROVED_RIPOSTE,
        [_aura(_AURA_PARRY, rank - 1), _pct(SpellModOp.THREAT, 20 * rank - 1)], _ICON_IMPROVED_RIPOSTE,
        _with_cap(_IMPROVED_RIPOSTE_TEXT, _IMPROVED_RIPOSTE_CAP, rank == 3),
        raw=_reads(eff1=m.IMPROVED_RIPOSTE_THREAT_READ),
        notes=f'eff0 aura 47 parry +{rank}% (stored {rank - 1}), eff1 pct THREAT +{20 * rank}% '
              f'(stored {20 * rank - 1}) on m.IMPROVED_RIPOSTE_THREAT_READ (Riposte and its cleave d1 b8, Ghostly '
              'Strike d2 b21)'
              + ('; the capstone is HasAura(203968) (Rogue::OnRiposteHit casts the cleave 203993).'
                 if rank == 3 else '.'))


improved_riposte_203966 = _improved_riposte(203966, 1)
improved_riposte_203967 = _improved_riposte(203967, 2)
improved_riposte_203968 = _improved_riposte(203968, 3)


# ---- (6,0) Coup de Grace 60414: pct DAMAGE +10 / +20 / +30% on Eviscerate | Between the Eyes | Killing Spree's
# strikes;
# rank 3's eff1 is the Mastery poll (PERIODIC_DUMMY 1 s: spell_rog_coup_de_grace_mastery rewrites eff0 = 30 +
# Mastery) ----
_COUP_DE_GRACE_TEXT = 'Increases the damage of your Eviscerate, Between the Eyes and Killing Spree by $s1%.'
_COUP_DE_GRACE_CAP = ('Capstone: The damage bonus is increased by your Mastery, and the damage reduction of your En '
                      'Garde is increased by your Mastery.')


def _coup_de_grace(spell_id, rank):
    effects = [_pct(SpellModOp.DAMAGE, 10 * rank - 1)]
    if rank == 3:
        effects.append(Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000,
                              implicit_target_a=_TARGET_UNIT_CASTER))
    return _rank(
        spell_id, 'Coup de Grace', rank, _ROW_COUP_DE_GRACE, effects, _ICON_COUP_DE_GRACE,
        _with_cap(_COUP_DE_GRACE_TEXT, _COUP_DE_GRACE_CAP, rank == 3), raw=_reads(eff0=m.COUP_DE_GRACE_READ),
        notes=f'eff0 pct DAMAGE +{10 * rank}% (stored {10 * rank - 1}) on m.COUP_DE_GRACE_READ (Eviscerate d0 b17, '
              'Between the Eyes d2 b5, Killing Spree\'s strikes d1 b23)'
              + ('; eff1 PERIODIC_DUMMY 1000 ms is the Mastery poll (the S1 spell_rog_vile_poisons_mastery shape: '
                 'eff0 = 30 + lround(Mastery)); the capstone also multiplies En Garde at cast (HasAura(203972)).'
                 if rank == 3 else '.'))


coup_de_grace_203970 = _coup_de_grace(203970, 1)
coup_de_grace_203971 = _coup_de_grace(203971, 2)
coup_de_grace_203972 = _coup_de_grace(203972, 3)
scripted_by(coup_de_grace_203972, 'spell_rog_coup_de_grace_mastery')


# ---- (6,2) Deft Maneuvers 60415: DUMMY 50 / 100 (weapon % of the strike = the bp the C++ passes to 203992) ----
def _deft_maneuvers(spell_id, rank):
    return _rank(
        spell_id, 'Deft Maneuvers', rank, _ROW_DEFT_MANEUVERS, [_dummy(50 * rank - 1)], _ICON_DEFT_MANEUVERS,
        f'When you activate Blade Flurry with {_c(DEFT_MANEUVERS_MIN_ENEMIES)} or more enemies nearby, you strike all '
        f'of them for $s1% weapon damage and gain 1 combo point for each enemy struck, up to '
        f'{_c(DEFT_MANEUVERS_MAX_POINTS)}.',
        notes=f'DUMMY {50 * rank} (weapon %; read by GetRankAmount EFFECT_0 in Rogue::OnBladeFlurryCast, passed as bp0 '
              'to the strike 203992).')


deft_maneuvers_203973 = _deft_maneuvers(203973, 1)
deft_maneuvers_203974 = _deft_maneuvers(203974, 2)


# ---- (6,3) Hair Trigger 60416: DUMMY 4 / 8 (% chance per combo point spent on Between the Eyes) ----
def _hair_trigger(spell_id, rank):
    return _rank(
        spell_id, 'Hair Trigger', rank, _ROW_HAIR_TRIGGER, [_dummy(4 * rank - 1)], _ICON_HAIR_TRIGGER,
        'Each combo point you spend on Between the Eyes has a $s1% chance to make your next Pistol Shot within '
        '$203987d deal $203987s1% more damage.',
        notes=f'DUMMY {4 * rank} (% per combo point, x combo points, x Proc Chance; read by GetRankAmount EFFECT_0 in '
              'Rogue::ApplyCombatSpentClauses, Between the Eyes only).')


hair_trigger_203975 = _hair_trigger(203975, 1)
hair_trigger_203976 = _hair_trigger(203976, 2)


# ---- (7,2) Celerity 60417: DUMMY 2 / 4 (% chance on Sinister Strike / Pistol Shot) ----
def _celerity(spell_id, rank):
    return _rank(
        spell_id, 'Celerity', rank, _ROW_CELERITY, [_dummy(2 * rank - 1)], _ICON_CELERITY,
        'Your Sinister Strike and Pistol Shot have a $s1% chance to grant you Adrenaline Rush for '
        f'{_sec(CELERITY_DURATION_MS)} sec.',
        notes=f'DUMMY {2 * rank} (% chance per cast, x Proc Chance; read by GetRankAmount EFFECT_0 in '
              'Rogue::OnBuilderCast).')


celerity_203977 = _celerity(203977, 1)
celerity_203978 = _celerity(203978, 2)

# ---- (7,3) Improved Feint 60418: DUMMY 10 (% = the helper's amount with Enforcer Stance up at apply) ----
improved_feint_203979 = _rank(
    203979, 'Improved Feint', None, _ROW_IMPROVED_FEINT, [_dummy(9)], _ICON_IMPROVED_FEINT,
    'While you are in Enforcer Stance, your Feint also reduces all damage taken by $s1%, area damage included.',
    notes='DUMMY 10 (%; read by GetRankAmount EFFECT_0 in spell_rog_improved_feint_helper).')


# ---- (8,3) Surprise Attacks ranks 2 / 3 (32601 is rank 1, A2): pct DAMAGE +4 / +6% on the doc's list; rank 3's eff1 is
# the capstone chance (DUMMY 40 %) ----
_SURPRISE_TEXT = ('Increases the damage dealt by your Sinister Strike, Pistol Shot, Eviscerate, Between the Eyes, '
                  'Backstab, Ambush and Shiv by $s1%.')
_SURPRISE_CAP = ('Capstone: When your Sinister Strike strikes an additional time, you have a $203982s2% chance that '
                 f'your next Pistol Shot fires {_c(SURPRISE_ATTACKS_EXTRA_SHOTS)} additional times.')


def _surprise_attacks(spell_id, rank):
    effects = [_pct(SpellModOp.DAMAGE, 2 * rank - 1)]
    if rank == 3:
        effects.append(_dummy(39))
    return _rank(
        spell_id, 'Surprise Attacks', rank, _ROW_SURPRISE_ATTACKS, effects, _ICON_SURPRISE_ATTACKS,
        _with_cap(_SURPRISE_TEXT, _SURPRISE_CAP, rank == 3), raw=_reads(eff0=m.SURPRISE_ATTACKS_READ),
        notes=f'eff0 pct DAMAGE +{2 * rank}% (stored {2 * rank - 1}) on m.SURPRISE_ATTACKS_READ (Sinister '
              'Strike, Pistol Shot, Eviscerate, Between the Eyes, Backstab, Ambush, Shiv, the second strike and the '
              'extra shots)'
              + ('; eff1 DUMMY 40 is the capstone chance (read by GetRankAmount EFFECT_1 in '
                 'Rogue::OnSinisterStrikeHit; $203982s2).' if rank == 3 else '.'))


surprise_attacks_203981 = _surprise_attacks(203981, 2)
surprise_attacks_203982 = _surprise_attacks(203982, 3)


# =====================================================================================================================
# Grappling Hook, En Garde, Blade Rush: the three castables
# =====================================================================================================================

# ---- Grappling Hook 203963 (U70, P0c) ----
# Raw Targets 0x40 (the ground cursor), eff0 DUMMY A 28 (TARGET_DEST_DYNOBJ_ENEMY), 40 yd (idx 5), line of sight kept
# (no Ex2 0x4), off the GCD, no cost, 45 s (Cooldown Haste), SpellLevel 25, SV 90253, no SpellMissileID. d2 b16.
grappling_hook_203963 = spell(
    id=203963, name='Grappling Hook', school=School.NORMAL, attributes=_ATTR0_IS_ABILITY,
    cast_time_ms=0, cooldown_ms=45000, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0,
    mana_cost_pct=0, range_yards=None,
    effects=[Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=_TARGET_DEST_DYNOBJ_ENEMY)],
    spell_icon_id=_ICON_GRAPPLING_HOOK,
    notes='rogue-rework S3a A3, combat doc "Grappling Hook" (U70, C6, P0c ruling, item 13): P0c\'s row 204396. '
          'Raw Targets 0x40 (TARGET_FLAG_DEST_LOCATION: the ground cursor), eff0 DUMMY on A 28 '
          '(TARGET_DEST_DYNOBJ_ENEMY), 40 yd (idx 5), line of sight kept (no AttributesEx2 0x4), off the GCD (no '
          'StartRecovery), no cost, 45 s (Cooldown Haste), SpellLevel / BaseLevel 25, SV 90253 (mined), no '
          'SpellMissileID and no ValueMultiplier. d2 b16 (m.GRAPPLING_HOOK_CLASS). spell_rog_grappling_hook: refuses '
          'while rooted, then MoveJump to the clicked point at GRAPPLE_SPEED_XY. SkillLineAbility 30812 via the talent '
          'bundling.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.GRAPPLING_HOOK_CLASS), 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'Targets': 0x40, 'RangeIndex': _RANGE_40_YD, 'SpellLevel': 25, 'BaseLevel': 25,
        'SpellMissileID': 0, 'SpellVisualID_1': _SV_GRAPPLING_HOOK,
        'Description_Lang_enUS': 'Launch a grappling hook and pull yourself to the target location.',
    },
)
scripted_by(grappling_hook_203963, 'spell_rog_grappling_hook')


# ---- En Garde 203969 (C8, R14, item 12) ----
# Slice and Dice's frame (typed 0x20050010, raw AttributesEx 0x400420, Ex2 0x4, Ex3 / Ex4 / Ex6 as 5171,
# PreventionType 2,
# 100 yd): eff0 DUMMY A 6 on the enemy (the finisher's combo-point target), eff1 APPLY_AURA 87 (damage taken, all
# schools) A 1, stored bp -1 / die 1 (= 0) plus raw EffectPointsPerCombo_2 = -EN_GARDE_PCT_PER_CP, so CalcValue gives
# -4% per held point at aura creation. 15 s fixed (idx 8), no cost, no cooldown, GCD 133 / 1000, SpellLevel 35.
def _en_garde_table():
    per_point = EN_GARDE_PCT_PER_CP['value']
    lines = ', '.join(f'{n} point{"" if n == 1 else "s"}: {per_point * n}%' for n in range(1, 6))
    return (f'Finishing move that reduces all damage taken by {_c(EN_GARDE_PCT_PER_CP)}% per combo point for $d. '
            f'{lines}.')


en_garde_203969 = spell(
    id=203969, name='En Garde', school=School.NORMAL, attributes=_ATTR0_SLICE_AND_DICE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=None, duration_ms=15000,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        _aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, -1, _MISC_ALL_SCHOOLS),
    ],
    spell_icon_id=_ICON_EN_GARDE,
    notes='rogue-rework S3a A3, combat doc "En Garde" (C8, R14, item 12): the Slice and Dice 5171 frame copied (typed '
          '0x20050010, AttributesEx 0x400420, Ex2 0x4, Ex3 0x50040000 | SUPPRESS_TARGET_PROCS 0x20000 (the core adds '
          'that bit to 5171 by id, SpellInfoCorrections.cpp:738, so a cast at a sleeping enemy never pulls), Ex4 0x10, '
          'Ex6 0x800004, PreventionType 2, RangeIndex 6). eff0 DUMMY A 6 on the enemy (the finisher\'s combo-point '
          'target), eff1 APPLY_AURA 87 misc 127 A 1 with stored bp -1 / die 1 (= 0) and raw EffectPointsPerCombo_2 = '
          '-EN_GARDE_PCT_PER_CP (CalcValue adds -4 x held points at aura creation; the script sets '
          'canBeRecalculated = false). 15 s fixed (idx 8, not 5171\'s 185), no cost, no cooldown, GCD 133 / 1000, '
          'SpellLevel / BaseLevel 35, visible "Damage taken reduced.". d2 b6 | d2 b18 (m.EN_GARDE_CLASS). '
          'spell_custom_attr 0x6000000 (R14: the enemy-targeted DUMMY frame plus a self aura must read as a buff). '
          'spell_rog_en_garde multiplies the amount by (1 + Mastery) with Coup de Grace rank 3. SkillLineAbility 30813 '
          'via the talent bundling.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.EN_GARDE_CLASS), 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'AttributesEx': _ATTR1_EN_GARDE, 'AttributesEx2': _ATTR2_IGNORE_LOS,
        'AttributesEx3': _ATTR3_SLICE_AND_DICE | _ATTR3_SUPPRESS_TARGET_PROCS,
        'AttributesEx4': _ATTR4_SLICE_AND_DICE, 'AttributesEx6': _ATTR6_SLICE_AND_DICE, 'PreventionType': 2,
        'RangeIndex': _RANGE_100_YD, 'EffectPointsPerCombo_2': -EN_GARDE_PCT_PER_CP['value'], 'SpellLevel': 35,
        'BaseLevel': 35, 'DurationIndex': _DURATION_15_SEC, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000,
        'Description_Lang_enUS': _en_garde_table(), 'AuraDescription_Lang_enUS': 'Damage taken reduced.',
    },
)
scripted_by(en_garde_203969, 'spell_rog_en_garde')
custom_attr(en_garde_203969, _CU_POSITIVE_EFF0_EFF1)


# ---- Blade Rush buff 203990 (U71) ----
# pct DAMAGE +30 (stored 29) on Eviscerate | Between the Eyes | Killing Spree's strikes (m.BLADE_RUSH_EMPOWER_READ), not
# charged, 15 s (idx 8), visible; the first damaging finisher's hit (or Killing Spree's end) removes it.
blade_rush_buff_203990 = _buff(
    203990, 'Blade Rush', [_pct(SpellModOp.DAMAGE, 29)], _ICON_BLADE_RUSH_BUFF, 15000,
    'Your next finishing move deals more damage.', raw=_reads(eff0=m.BLADE_RUSH_EMPOWER_READ),
    notes='rogue-rework S3a A3, combat doc "Blade Rush" (U71, item 9): pct DAMAGE +30% (stored 29) on '
          'm.BLADE_RUSH_EMPOWER_READ (Eviscerate d0 b17, Between the Eyes d2 b5, Killing Spree\'s strikes d1 b23), not '
          'charged (the C++ removes it), 15 s (idx 8), visible, number-free text, Ex1 0x20. Cast by '
          'spell_rog_blade_rush\'s AfterCast; consumed by Eviscerate / Between the Eyes AfterHit '
          '(ConsumeBladeRush) and by Killing Spree\'s end.',
)

# ---- Blade Rush 203980 (U71, R13, item 14) ----
# eff0 CHARGE A 6, eff1 WEAPON_PERCENT_DAMAGE weapon_potency 100 on A 53 / B 16 radius 5 yd (idx 8: the target plus the
# engaged units around it), 20 yd (idx 3), no cost, 45 s (Cooldown Haste), GCD 133 / 1000, SpellLevel 50, SV 90254,
# DefenseType 2. No SUPPRESS_CASTER_PROCS: the cast rolls its procs once and its poisons per enemy (R13).
blade_rush_203980 = spell(
    id=203980, name='Blade Rush', school=School.NORMAL, attributes=_ATTR0_IS_ABILITY,
    cast_time_ms=0, cooldown_ms=45000, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0,
    mana_cost_pct=0, range_yards=None,
    effects=[
        Effect(type=EffectType.CHARGE, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=100, implicit_target_a=_TARGET_DEST_TARGET_ENEMY,
               implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=5.0),
    ],
    spell_icon_id=_ICON_BLADE_RUSH,
    notes='rogue-rework S3a A3, combat doc "Blade Rush" (U71, R13, item 14): P0 204388\'s shape. eff0 CHARGE on A 6, '
          'eff1 '
          'WEAPON_PERCENT_DAMAGE weapon_potency 100 [tune] on A 53 TARGET_DEST_TARGET_ENEMY / B 16 '
          'TARGET_UNIT_DEST_AREA_ENEMY radius 5 yd (idx 8; spell_rog_blade_rush keeps the explicit target + units in '
          'combat with the rogue), 20 yd (idx 3), no cost, 45 s (Cooldown Haste), GCD 133 / 1000, SpellLevel 50, '
          'DefenseType 2, PreventionType 2, weapon requirement as Eviscerate\'s (a weapon strike), SV 90254, no '
          'SUPPRESS_CASTER_PROCS (R13: poisons roll per enemy through PoisonRollAllowed, other procs once). No combo '
          'points; Blade Flurry never copies it. d2 b15 (m.BLADE_RUSH_CLASS). SkillLineAbility 30814 via the talent '
          'bundling.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.BLADE_RUSH_CLASS),
        'EquippedItemClass': _ITEM_CLASS_WEAPON, 'EquippedItemSubclass': _ANY_MELEE_WEAPON, 'CastingTimeIndex': 1,
        'PreventionType': 2, 'DefenseType': _DEFENSE_MELEE, 'RangeIndex': _RANGE_20_YD, 'SpellLevel': 50,
        'EffectRadiusIndex_2': _RADIUS_5_YD, 'SpellVisualID_1': _SV_BLADE_RUSH, 'StartRecoveryCategory': 133,
        'StartRecoveryTime': 1000,
        'Description_Lang_enUS': (
            'Charge to your target, striking it and all enemies within $a2 yards for $s2% weapon damage. Your next '
            'damaging finishing move within $203990d deals $203990s1% more damage.'),
    },
)
scripted_by(blade_rush_203980, 'spell_rog_blade_rush')


# =====================================================================================================================
# Celerity's Adrenaline Rush, Anticipation, Improved Kick's buff
# =====================================================================================================================

# ---- Adrenaline Rush (Celerity) 203996 (U74) ----
# Aura 110 MOD_POWER_REGEN_PERCENT misc 3 (energy) +100% (stored 99), 4 s (idx 35), Adrenaline Rush's icon and aura
# text,
# no family bits, visible. Exclusive with 13750 through spell_group 1288 below; the builders' extra point reads
# either id.
adrenaline_rush_celerity_203996 = _buff(
    203996, 'Adrenaline Rush', [_aura(_AURA_MOD_POWER_REGEN_PERCENT, 99, _MISC_POWER_ENERGY)], _ICON_ADRENALINE_RUSH,
    CELERITY_DURATION_MS['value'], 'Energy regeneration increased. Your builders award more combo points.',
    notes='rogue-rework S3a A3, combat doc "Celerity" (U74, item 10): the proc copy of Adrenaline Rush. Aura 110 '
          'MOD_POWER_REGEN_PERCENT misc 3 (energy) +100% (stored 99), CELERITY_DURATION_MS (4 s, idx 35), Adrenaline '
          'Rush\'s icon 235 and aura text, no family bits, visible, Ex1 0x20. In exclusive spell_group 1288 with 13750 '
          '(a new one replaces the old); Adrenaline Rush\'s +1 combo point reads HasAura(13750) || HasAura(203996).',
)
spell_group(1288, 13750, adrenaline_rush_celerity_203996)
spell_group_rule(1288, 1, 'Adrenaline Rush and Celerity\'s Adrenaline Rush: exclusive, a new one replaces the old')

# ---- Anticipation 203997 (U54) ----
# DUMMY self, CumulativeAura 2 (= ANTICIPATION_MAX_STACKS: the stored points), 20 s (idx 18), visible, combo point icon,
# aura text verbatim, raw AttributesEx 0x20.
anticipation_203997 = _buff(
    203997, 'Anticipation', [_dummy(0)], _ICON_ANTICIPATION, 20000,
    'Extra combo points are stored for after your next finishing move.',
    raw={'CumulativeAura': ANTICIPATION_MAX_STACKS['value']},
    notes='rogue-rework S3a A3, combat doc "Restless Blades" (U54, item 2): DUMMY self, CumulativeAura = '
          'ANTICIPATION_MAX_STACKS (2: the stored combo points show as the stack count), 20 s (idx 18; every gain '
          'refreshes), visible, the combo point icon 494 (Ruthlessness\'s), aura text verbatim, Ex1 0x20. Banked by '
          'Rogue::BankAnticipation, released by ReleaseAnticipation after the next finisher.',
)

# ---- Improved Kick buff 203999 (U73) ----
# eff0 ENERGIZE 40 energy [tune] (stored 39), eff1 aura 138 melee haste +35% [tune] (stored 34), 6 s (idx 32), visible.
improved_kick_buff_203999 = _buff(
    203999, 'Improved Kick',
    [Effect(type=EffectType.ENERGIZE, base_points=39, misc_value=_MISC_POWER_ENERGY,
            implicit_target_a=_TARGET_UNIT_CASTER),
     _aura(_AURA_MOD_MELEE_HASTE, 34)],
    _ICON_IMPROVED_KICK, 6000, 'Energy restored and attack speed increased.',
    notes='rogue-rework S3a A3, combat doc "Improved Kick" (U73): eff0 ENERGIZE 40 energy [tune] (stored 39, misc 3), '
          'eff1 aura 138 MOD_MELEE_HASTE +35% [tune] (stored 34), 6 s (idx 32), visible, number-free text, Ex1 0x20. '
          'The rank tooltips quote $203999s1 / s2 / d. Cast by Rogue::OnKickInterrupt.',
)


# =====================================================================================================================
# Debuffs, copies and strikes
# =====================================================================================================================

# ---- Blade Twisting debuff 203998 (Q13, R15) ----
# Aura 271 MOD_DAMAGE_FROM_CASTER bp 0 (the C++ passes the rank 2 / 4 as bp0) on m.BLADE_TWISTING_READ (every builder's
# hit), CumulativeAura 5, 12 s (idx 29), A 6, 100 yd, no facing, Ex3 0x80 (per caster), visible debuff.
blade_twisting_debuff_203998 = spell(
    id=203998, name='Blade Twisting', school=School.NORMAL, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0, range_yards=None,
    duration_ms=12000,
    effects=[_aura(_AURA_MOD_DAMAGE_FROM_CASTER, 0, 0, target=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_BLADE_TWISTING,
    notes='rogue-rework S3a A3, combat doc "Blade Twisting" (Q13, R15, item 12): aura 271 MOD_DAMAGE_FROM_CASTER bp '
          '0 (the '
          'C++ passes the rank 2 / 4 through CastCustomSpell on each hit of the five named casts; a new application '
          'adds a stack and refreshes) on m.BLADE_TWISTING_READ (the direct-builder group, Mutilate / Kingsbane hands, '
          'Fan of Knives, the second strike and the extra shots; never finishers, autos or bleeds), CumulativeAura 5, '
          '12 s (idx 29), A 6, RangeIndex 6, FacingCasterFlags 0, Ex3 0x80 (a stack per caster), visible debuff, icon '
          '2108.',
    raw_overrides=_enemy_aura_raw(
        AttributesEx3=_ATTR3_STACK_PER_CASTER, CumulativeAura=5, **_reads(eff0=m.BLADE_TWISTING_READ),
        Description_Lang_enUS='Increases the damage of the rogue\'s combo point builders against the target.',
        AuraDescription_Lang_enUS='Taking more damage from the rogue\'s strikes.'),
)

# ---- Prey on the Weak crit debuff 204003 (U60, R11) ----
# Aura 308 MOD_CRIT_CHANCE_FOR_CASTER bp 0 (the C++ passes the crit rank), A 6, 100 yd, no facing, 5 s (refreshed by each
# cast),
# hidden,
# raw AttributesEx 0x400 (NO_THREAT) and Ex3 0x20000 (SUPPRESS_TARGET_PROCS, no initial aggro) | 0x80 (per caster).
prey_on_the_weak_crit_204003 = spell(
    id=204003, name='Prey on the Weak', school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=None, duration_ms=5000,
    effects=[_aura(_AURA_MOD_CRIT_CHANCE_FOR_CASTER, 0, 0, target=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_PREY_ON_THE_WEAK,
    notes='rogue-rework S3a A3, combat doc "Prey on the Weak" (U60, R11, item 8): aura 308 '
          'MOD_CRIT_CHANCE_FOR_CASTER bp 0 '
          '(the C++ passes the crit rank 5 / 10 / 15 through CastCustomSpell and refreshes it with ChangeAmount when '
          'the rank moved), A 6, RangeIndex 6, FacingCasterFlags 0, 5 s (Rogue::UpdatePreyCritDebuff adds, refreshes '
          'and removes it), hidden, raw AttributesEx 0x400 (NO_THREAT), Ex3 0x20000 (SUPPRESS_TARGET_PROCS, no initial '
          'aggro) | 0x80 (a stack per caster). No family bits.',
    raw_overrides=_enemy_aura_raw(
        AttributesEx=_ATTR1_NO_THREAT, AttributesEx3=_ATTR3_SUPPRESS_TARGET_PROCS | _ATTR3_STACK_PER_CASTER,
        Description_Lang_enUS='Increases the rogue\'s critical strike chance against the target.'),
)

# ---- Blade Flurry copy 203991 (U59, item 4) ----
# The S2 echo shape (204162): Physical SCHOOL_DAMAGE bp from the script (potency_excluded), SpellClassSet 8 with NO
# family
# bits, Ex3 IGNORE_CASTER_MODIFIERS | ALWAYS_HIT | SUPPRESS_CASTER_PROCS, Ex2 CANT_CRIT, DefenseType 0, A 6, 100 yd, no
# facing, custom attr 0x8000, hidden.
blade_flurry_copy_203991 = spell(
    id=203991, name='Blade Flurry', school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=None,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
               potency_excluded='the amount is BLADE_FLURRY_COPY_PCT of the damage the original hit dealt, passed as '
                                'bp0 by Rogue::OnBladeFlurryDamage (percent-of-other-damage); no potency of its own'),
    ],
    spell_icon_id=_ICON_BLADE_FLURRY,
    notes='rogue-rework S3a A3, combat doc "Blade Flurry" (U59, item 4): the hidden copy Rogue::OnBladeFlurryDamage '
          'casts at up to 4 enemies near the hit target with bp0 = 40% of the damage dealt. The S2 echo shape '
          '(204162): Physical SCHOOL_DAMAGE, SpellClassSet 8 with NO family bits (no reader reaches it), Ex3 '
          'IGNORE_CASTER_MODIFIERS | ALWAYS_HIT | SUPPRESS_CASTER_PROCS, Ex2 CANT_CRIT, DefenseType 0, A 6, '
          'RangeIndex 6 (100 yd), FacingCasterFlags 0, custom attr 0x8000 (a share of post-armor damage), hidden, '
          'potency_excluded.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys((0, 0, 0)), 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'DefenseType': 0, 'RangeIndex': _RANGE_100_YD, 'FacingCasterFlags': 0,
        'AttributesEx2': _ATTR2_CANT_CRIT,
        'AttributesEx3': _ATTR3_IGNORE_CASTER_MODIFIERS | _ATTR3_ALWAYS_HIT | _ATTR3_SUPPRESS_CASTER_PROCS,
        'Description_Lang_enUS': 'Strikes a nearby enemy for a share of the damage dealt.',
    },
)
# The copy deals a share of damage that already went through armor; Unit.cpp checks armor before the bleed exemption, so
# without SPELL_ATTR0_CU_IGNORE_ARMOR every copy would lose armor a second time (S1-CODE-REVIEW M1, WP-BRIEF section 0).
custom_attr(blade_flurry_copy_203991, _CU_IGNORE_ARMOR)

# ---- Deft Maneuvers strike 203992 (U72, R13, R20) ----
# WEAPON_PERCENT_DAMAGE weapon_potency 100 (the top rank; the C++ passes the rank's percent as bp0: a weapon-percent
# effect
# has no level scaling, so the override is exact), SpellLevel 40, caster-centred 8 yd area (A 22 / B 15), no target cap
# (R13: every engaged enemy), no bits, hidden, no SUPPRESS_CASTER_PROCS (poisons roll per enemy).
deft_maneuvers_strike_203992 = spell(
    id=203992, name='Deft Maneuvers', school=School.NORMAL, attributes=_ATTR0_IS_ABILITY | _ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=None, radius_yards=8.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=100, implicit_target_a=_TARGET_SRC_CASTER,
               implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=8.0),
    ],
    spell_icon_id=_ICON_DEFT_MANEUVERS,
    notes='rogue-rework S3a A3, combat doc "Deft Maneuvers" (U72, R13, R20): the strike Rogue::OnBladeFlurryCast casts '
          'on the rogue (caster-centred): WEAPON_PERCENT_DAMAGE weapon_potency 100 (the top rank; the C++ passes the '
          'rank\'s 50 / 100 as bp0, exact because a weapon-percent effect has no level scaling), SpellLevel 40, A 22 '
          'TARGET_SRC_CASTER / B 15 TARGET_UNIT_SRC_AREA_ENEMY radius 8 yd (spell_rog_deft_maneuvers_strike keeps the '
          'units in combat with the rogue, not totems; no target cap, R13), main-hand weapon requirement, no family '
          'bit '
          'at all, no SUPPRESS_CASTER_PROCS and Ex3 |= NOT_A_PROC 0x200 (R13: its poisons roll per enemy), SV 223 '
          '(Whirlwind\'s), DefenseType 2, hidden. Blade Flurry '
          'never '
          'copies it.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys((0, 0, 0)), 'EquippedItemClass': _ITEM_CLASS_WEAPON,
        'EquippedItemSubclass': _ANY_MELEE_WEAPON, 'CastingTimeIndex': 1,
        'AttributesEx3': _ATTR3_REQUIRES_MAIN_HAND | _ATTR3_NOT_A_PROC,
        'DefenseType': _DEFENSE_MELEE, 'RangeIndex': _RANGE_100_YD, 'FacingCasterFlags': 0,
        'SpellLevel': 40, 'SpellVisualID_1': _SV_WHIRLWIND,
        'Description_Lang_enUS': 'Strikes all nearby enemies for weapon damage.',
    },
)
scripted_by(deft_maneuvers_strike_203992, 'spell_rog_deft_maneuvers_strike')

# ---- Improved Riposte cleave 203993 (U72, R20) ----
# Riposte's 150% weapon frame (weapon_potency 150, SpellLevel 35), no slow, no combo point, d1 b8 only
# (m.RIPOSTE_CLEAVE_CLASS: Improved Riposte's threat mod reaches it), A 6, 100 yd, no facing, Ex3 SUPPRESS_CASTER_PROCS.
improved_riposte_cleave_203993 = spell(
    id=203993, name='Riposte', school=School.NORMAL, attributes=_ATTR0_IS_ABILITY | _ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=None,
    effects=[Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=150,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_IMPROVED_RIPOSTE,
    notes='rogue-rework S3a A3, combat doc "Improved Riposte" (U72, R20): the capstone\'s cleave Rogue::OnRiposteHit '
          'casts '
          'at up to IMPROVED_RIPOSTE_EXTRA_TARGETS enemies near the target. Riposte 14251\'s 150% weapon frame '
          '(WEAPON_PERCENT_DAMAGE weapon_potency 150, SpellLevel 35; the stock row is -1 for the equipped item), no '
          'slow, no combo point, d1 b8 only (m.RIPOSTE_CLEAVE_CLASS: Improved Riposte\'s threat mod reaches it, '
          'never d2 b19), A 6, RangeIndex 6, FacingCasterFlags 0, Ex3 SUPPRESS_CASTER_PROCS, DefenseType 2, SV 3799, '
          'hidden.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.RIPOSTE_CLEAVE_CLASS), 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'AttributesEx3': _ATTR3_SUPPRESS_CASTER_PROCS, 'DefenseType': _DEFENSE_MELEE,
        'RangeIndex': _RANGE_100_YD, 'FacingCasterFlags': 0, 'SpellLevel': 35, 'SpellVisualID_1': _SV_RIPOSTE,
        'Description_Lang_enUS': 'Strikes a nearby enemy with a Riposte.',
    },
)


# ---- Hack and Slash strikes 203994 (main hand) / 203995 (off hand) (U63, R20) ----
# WEAPON_PERCENT_DAMAGE weapon_potency 100 (the top rank; the C++ passes the rank's 33 / 66 / 100 as bp0), SpellLevel
# 30,
# A 6, 100 yd, no facing, Ex3 SUPPRESS_CASTER_PROCS | the hand requirement, DefenseType 2, no bits, hidden.
def _hack_and_slash_strike(spell_id, hand_attr, hand_name):
    hand_flag = 'REQUIRES_MAIN_HAND' if hand_attr == _ATTR3_REQUIRES_MAIN_HAND else 'REQUIRES_OFF_HAND'
    return spell(
        id=spell_id, name='Hack and Slash', school=School.NORMAL, attributes=_ATTR0_IS_ABILITY | _ATTR0_DO_NOT_DISPLAY,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0,
        mana_cost_pct=0, range_yards=None,
        effects=[Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=100,
                        implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
        spell_icon_id=_ICON_HACK_AND_SLASH,
        notes='rogue-rework S3a A3, combat doc "Hack and Slash" (U63, R10, R20, item 7): the extra attack '
              f'Rogue::CastHackAndSlash casts with the {hand_name} weapon. WEAPON_PERCENT_DAMAGE weapon_potency 100 '
              '(the top rank; the C++ passes the rank\'s 33 / 66 / 100 as bp0, exact because a weapon-percent effect '
              'has no level scaling), SpellLevel 30, A 6, RangeIndex 6, FacingCasterFlags 0, Ex3 '
              f'SUPPRESS_CASTER_PROCS | {hand_flag}, DefenseType 2, no family bit at all (Blade Flurry copies it by '
              f'the damage hook, not by a bit), hidden. '
              'Rolls no poisons (R10: triggered hits roll nothing). SV 39 (the stock strikes\').',
        raw_overrides={
            'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys((0, 0, 0)),
            'EquippedItemClass': _ITEM_CLASS_WEAPON, 'EquippedItemSubclass': _ANY_MELEE_WEAPON, 'CastingTimeIndex': 1,
            'AttributesEx3': hand_attr | _ATTR3_SUPPRESS_CASTER_PROCS, 'DefenseType': _DEFENSE_MELEE,
            'RangeIndex': _RANGE_100_YD, 'FacingCasterFlags': 0, 'SpellLevel': 30,
            'SpellVisualID_1': _SV_STRIKE,
            'Description_Lang_enUS': f'An extra attack with your {hand_name} weapon.',
        },
    )


hack_and_slash_main_203994 = _hack_and_slash_strike(203994, _ATTR3_REQUIRES_MAIN_HAND, 'main hand')
hack_and_slash_off_203995 = _hack_and_slash_strike(203995, _ATTR3_REQUIRES_OFF_HAND, 'off hand')


# =====================================================================================================================
# Helpers (U64): hidden auras linked to Sprint / Evasion / Feint; the scripts set the amounts (0 without the talent)
# =====================================================================================================================

# ---- Improved Sprint helper 204000: root duration -50% (aura 232 misc 7), minimum speed 100% (aura 305) ----
# The stored amounts are the real ones (the rank-2 tooltip quotes $204000s1 / $204000s2); the script sets 0 without
# 13875.
improved_sprint_helper_204000 = _hidden_aura(
    204000, 'Improved Sprint',
    [_aura(_AURA_MECHANIC_DURATION_MOD, -51, _MISC_ROOT_MECHANIC), _aura(_AURA_MOD_MINIMUM_SPEED, 99)],
    _ICON_IMPROVED_SPRINT, -1, 'Shortens root effects on you and keeps your movement speed from dropping below normal.',
    notes='rogue-rework S3a A3, combat doc "Improved Sprint" (U64, item 16): hidden helper linked to Sprint 2983 '
          '(type 2: '
          'it lives exactly as long as Sprint). eff0 aura 232 MECHANIC_DURATION_MOD misc 7 (root) -50% (stored -51), '
          'eff1 aura 305 MOD_MINIMUM_SPEED +100% (stored 99), self, infinite (idx 21), DO_NOT_DISPLAY but not PASSIVE '
          '(an aura link needs a real aura), Ex1 0x20. spell_rog_improved_sprint_helper sets both amounts to 0 without '
          'Improved Sprint rank 2 (13875).',
)
scripted_by(improved_sprint_helper_204000, 'spell_rog_improved_sprint_helper')
linked_spell(2983, improved_sprint_helper_204000.id, 2,
             'Improved Sprint: the root / speed-floor helper lives exactly as long as Sprint')

# ---- Endurance helper 204001: Magic damage taken (aura 87 misc 126) ----
endurance_helper_204001 = _hidden_aura(
    204001, 'Endurance', [_zero_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, _MISC_MAGIC_SCHOOLS)], _ICON_ENDURANCE, -1,
    'Reduces the Magic damage you take while Evasion is active.',
    notes='rogue-rework S3a A3, combat doc "Endurance" (U64): hidden helper linked to Evasion 5277 (type 2). eff0 '
          'aura 87 '
          'MOD_DAMAGE_PERCENT_TAKEN misc 126 (every school but Physical) stored 0 (DieSides 0: spell_rog_endurance_'
          'helper sets -10 / -20 from Endurance\'s eff2), self, infinite (idx 21), DO_NOT_DISPLAY but not PASSIVE, '
          'Ex1 0x20.',
)
scripted_by(endurance_helper_204001, 'spell_rog_endurance_helper')
linked_spell(5277, endurance_helper_204001.id, 2,
             'Endurance: the Magic-damage helper lives exactly as long as Evasion')

# ---- Improved Feint helper 204002: all damage taken (aura 87 misc 127), only with Enforcer Stance up at apply ----
improved_feint_helper_204002 = _hidden_aura(
    204002, 'Improved Feint', [_zero_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, _MISC_ALL_SCHOOLS)], _ICON_FEINT, -1,
    'Reduces all damage you take while Feint is active.',
    notes='rogue-rework S3a A3, combat doc "Improved Feint" (U64): hidden helper linked to Feint 1966 (type 2). eff0 '
          'aura '
          '87 MOD_DAMAGE_PERCENT_TAKEN misc 127 stored 0 (DieSides 0: spell_rog_improved_feint_helper sets -10 with '
          '203979 held and Enforcer Stance up at apply, else 0), self, infinite (idx 21), DO_NOT_DISPLAY but not '
          'PASSIVE, Ex1 0x20.',
)
scripted_by(improved_feint_helper_204002, 'spell_rog_improved_feint_helper')
linked_spell(1966, improved_feint_helper_204002.id, 2,
             'Improved Feint: the damage-taken helper lives exactly as long as Feint')
