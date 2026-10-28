"""
Rogue - S2 Subtlety, data half: every new row 204130-204173 (talent ranks, Master of Subtlety's fresh ranks, the
Hemorrhage / Premeditation passive ranks, Death from Above and its area hit / landing / flight aura, the Hemorrhage
bleed and tick, Akaari's echo and clone tint, the Finality / Lingering Shadow / Master of Subtlety / Mark of the Master
Assassin / Relentless Strikes / Honor Among Thieves buffs, the Sinister Calling volley, the Second Volley and Throwing
Specialization copies, the Enveloping Shadows helper), creature 300350 (Akaari's clone), the SpellDescriptionVariables
1335 / 1336 (U34 talent bonuses on tooltips), the scripted_by / linked_spell / custom_attr rows of the new ids and the
hidden script numbers (`const()`) the C++ reads through the generated RogueData.h.

Source of truth: docs/reworks/rogue-subtlety-rework.md (tooltips and aura texts verbatim),
.agents/plans/rogue-rework/rogue-rework.S2-HANDOFF.md (sections 4-5), rogue-rework.S2a-WP-BRIEF.md (variable names,
bits, effect order, resolutions; the brief wins over the handoff).

Talent rows, their SkillLineAbility bundling (Death from Above 30825) and the tab live in rogue_talents.py; stock rank
spells edited in place live in rogue_trigger_spells.py; shared stock rows (Shadow Dance 51713, Shadowstep 36554,
Preparation 14185, Hunger for Blood's mask, the script bindings on 53 / 2098 / 26679 / 1943 / 8676) live in
rogue_spells.py / rogue_shared.py; S1's SDV objects 1321-1323 (extended by S2, U34) live in rogue_assassination.py.

Raw class-mask keys come from `_masks.read_mask_keys` / `clear_mask_keys` / `class_mask_keys` only (letter = effect,
number = dword); never hand-write an EffectSpellClassMask / SpellClassMask key.
"""

from lib import potency as _potency
from lib.dsl import AuraType, Effect, EffectType, Mechanic, PowerType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import const, creature_model, creature_template, custom_attr, linked_spell, scripted_by, spell
from lib.dsl.registry import tooltip_vars
from lib.dsl.tooltip import product, talent_mult

from . import _masks as m

# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h) ----
_SPELLFAMILY_ROGUE = 8
_ATTR0_DO_NOT_DISPLAY = 0x80
_ATTR0_TALENT_PASSIVE = 464                 # ABILITY 0x10 | PASSIVE 0x40 | DO_NOT_DISPLAY 0x80 | DO_NOT_LOG 0x100
_ATTR0_FINISHER = 327696                    # 0x50010: stock Eviscerate / Mutilate frame
_ATTR0_FAN_OF_KNIVES = 65552                # 0x10010: stock Fan of Knives 51723 / 52874
_ATTR0_DEADLY_THROW = 4259858               # 0x410012: stock Deadly Throw 26679 (ranged slot)
_ATTR1_ALLOW_WHILE_STEALTHED = 0x20         # AttributesEx: a self buff cast while stealthed never breaks Stealth (R19)
_ATTR1_FAN_OF_KNIVES = 0x10                 # stock 51723 / 52874 AttributesEx
_ATTR1_FINISHER = 0x100200                  # FINISHING_MOVE_DAMAGE 0x100000 | INITIATE_COMBAT 0x200 (stock 2098)
_ATTR1_IMMUNITY_PURGES_EFFECT = 0x8000      # AttributesEx: an immunity aura purges the auras it makes immune to
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_STACK_PER_CASTER = 0x80              # DOT_STACKING_RULE: stack separately for each caster
_ATTR3_REQUIRES_MAIN_HAND = 0x400
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000
_ATTR3_ALWAYS_HIT = 0x40000
_ATTR3_REQUIRES_OFF_HAND = 0x1000000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
_CU_IGNORE_ARMOR = 0x8000                   # SPELL_ATTR0_CU_IGNORE_ARMOR (spell_custom_attr), S1-CODE-REVIEW M1

# ---- targets / auras / misc values ----
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_UNIT_DEST_AREA_ENEMY = 16
_TARGET_DEST_CASTER = 18
_TARGET_DEST_TARGET_ENEMY = 53
_AURA_SAFE_FALL = 144
_AURA_MOD_ARMOR_PENETRATION_PCT = 280
_MECHANIC_BLEED = 15
_MISC_ROOT_MECHANIC = 7                     # MECHANIC_ROOT: aura 77's misc value
_MISC_ALL_SCHOOLS = 127
_MISC_PHYSICAL = 1                          # school mask for aura 79 / 87 / 280
_CR_VERSATILITY = 1 << 21                   # 1 << CombatRating.VERSATILITY
_CR_COOLDOWN_HASTE = 1 << 22                # 1 << CombatRating.COOLDOWN_HASTE

# ---- weapon requirements and ranges (S2a-0VERIFY item 17) ----
_ITEM_CLASS_WEAPON = 2
_ANY_MELEE_WEAPON = 173555                  # stock Eviscerate / Fan of Knives EquippedItemSubclass
_THROWN_WEAPON = 65536                      # stock Deadly Throw EquippedItemSubclass
_RANGE_SELF = 1
_RANGE_MELEE = 2
_RANGE_100_YD = 6                           # R11: every row C++ casts at an enemy
_RANGE_15_YD = 11

# ---- stock icons / visuals (S2a-WP-BRIEF section 9) ----
_ICON_DEEPENING_SHADOWS = 2680
_ICON_SHADOW_RESOLVE = 131
_ICON_SECOND_VOLLEY = 1505
_ICON_LINGERING_SHADOW = 2206
_ICON_FINALITY = 169
_ICON_EXECUTIONER = 2283
_ICON_AKAARIS_ECHO = 87
_ICON_MOMA = 2984
_ICON_DEATH_FROM_ABOVE = 3139
_ICON_MASTER_OF_SUBTLETY = 2114
_ICON_HEMORRHAGE = 153                      # stock Hemorrhage 16511 (the talent's and the bleed's look)
_ICON_HEMORRHAGE_BLEED = 153
_ICON_PREMEDITATION = 98                    # stock Premeditation 14183
_ICON_RELENTLESS_STRIKES = 559
_ICON_HONOR_AMONG_THIEVES = 2903
_ICON_ENVELOPING_SHADOWS = 2111
_ICON_SINISTER_CALLING = 1528               # Fan of Knives' neighbour look (Venomous Fan 1528)
_ICON_FAN_OF_KNIVES = 2904
_ICON_DEADLY_THROW = 2097
_SV_SHADOWFORM_TINT = 3619                  # Shadowform 15473's SpellVisual: the clone tint (P0 204390)
_SV_EVISCERATE = 671
_SV_FAN_OF_KNIVES = 12317
_SV_FAN_OF_KNIVES_OFF_HAND = 12318
_SV_DEADLY_THROW = 7929

# Talent rows of the S2 grid (S2a-WP-BRIEF section 10.1), for SpellLevel = 9 + 5 x row + rank.
_ROW_DEEPENING_SHADOWS, _ROW_SHADOW_RESOLVE, _ROW_SECOND_VOLLEY, _ROW_LINGERING_SHADOW = 0, 1, 3, 3
_ROW_FINALITY, _ROW_EXECUTIONER, _ROW_AKAARIS_ECHO, _ROW_MOMA = 4, 5, 8, 9
_ROW_MASTER_OF_SUBTLETY, _ROW_HEMORRHAGE, _ROW_PREMEDITATION = 6, 4, 6


# =====================================================================================================================
# Script numbers (WP-BRIEF section 6; hidden constants, generated RogueData::NAME, read by RogueMechanics.cpp and the
# S2 scripts). Every [tune] number changes here, never in C++.
# =====================================================================================================================
SHADOW_DANCE_CDR_PER_CP_MS = const(
    'SHADOW_DANCE_CDR_PER_CP_MS', 1000, 'Shadow Dance: cooldown taken off per combo point a finisher spends, ms '
    '[fixed].')
EXECUTIONER_CDR_PER_CP_MS = const(
    'EXECUTIONER_CDR_PER_CP_MS', 500, 'Executioner capstone: extra Shadow Dance cooldown taken off per combo point '
    'below the health threshold, ms [fixed].')
SLAUGHTER_CDR_MS = const(
    'SLAUGHTER_CDR_MS', 500, 'Slaughter from the Shadows: Shadow Dance cooldown taken off per proc (Backstab), ms '
    '[fixed].')
EXECUTIONER_HEALTH_PCT = const(
    'EXECUTIONER_HEALTH_PCT', 35, 'Executioner: live target health threshold, % [fixed].')
SINISTER_CALLING_PCT_PER_CP = const(
    'SINISTER_CALLING_PCT_PER_CP', 4, 'Sinister Calling capstone: volley chance per combo point spent, % [fixed].')
SINISTER_CALLING_MAX_TARGETS = const(
    'SINISTER_CALLING_MAX_TARGETS', 3, 'Sinister Calling volley: the target plus 2 others [fixed].')
SECOND_VOLLEY_DELAY_MS = const(
    'SECOND_VOLLEY_DELAY_MS', 300, 'Second Volley: delay of the second Fan of Knives, ms [tune].')
THROWING_SPEC_EXTRA_TARGETS = const(
    'THROWING_SPEC_EXTRA_TARGETS', 2, 'Throwing Specialization capstone: Deadly Throw copies [fixed].')
THROWING_SPEC_RADIUS_YD = const(
    'THROWING_SPEC_RADIUS_YD', 8.0, 'Throwing Specialization capstone: copies\' search radius around the primary, '
    'yards [tune].')
AKAARI_ECHO_DELAY_MS = const(
    'AKAARI_ECHO_DELAY_MS', 2000, 'Akaari\'s Echo: delay before the echo strikes, ms [fixed].')
AKAARI_ECHO_SHARE_PCT = const(
    'AKAARI_ECHO_SHARE_PCT', 50, 'Akaari\'s Echo: share of the Ambush\'s damage the echo deals, % [tune].')
AKAARI_CLONE_DESPAWN_MS = const(
    'AKAARI_CLONE_DESPAWN_MS', 1500, 'Akaari\'s Echo: clone lifetime, ms [fixed].')
AKAARI_CLONE_BEHIND_YD = const(
    'AKAARI_CLONE_BEHIND_YD', 1.5, 'Akaari\'s Echo: clone distance behind the target, yards [fixed].')
AKAARI_CLONE_SWING_DELAY_MS = const(
    'AKAARI_CLONE_SWING_DELAY_MS', 200, 'Akaari\'s Echo: clone swing emote delay, ms [fixed].')
MASTER_OF_SUBTLETY_TAIL_MS = const(
    'MASTER_OF_SUBTLETY_TAIL_MS', 8000, 'Master of Subtlety: buff duration after leaving true Stealth, ms [fixed].')
MOMA_TAIL_MS = const(
    'MOMA_TAIL_MS', 3000, 'Mark of the Master Assassin: buff duration after leaving Stealth, ms [fixed].')
HONOR_AMONG_THIEVES_ALLY_RANGE_YD = const(
    'HONOR_AMONG_THIEVES_ALLY_RANGE_YD', 40.0, 'Honor Among Thieves: ally search range, yards [tune].')
CHEAT_DEATH_CAP_MAX_HEALTH_PCT = const(
    'CHEAT_DEATH_CAP_MAX_HEALTH_PCT', 15, 'Cheat Death: a lethal blow is absorbed up to current health plus this % '
    'of maximum health [fixed].')
DFA_LANDING_RANGE_YD = const(
    'DFA_LANDING_RANGE_YD', 8.0, 'Death from Above: the landing hits only a target within this of the landing, '
    'yards [fixed].')
DFA_LANDING_PAST_YD = const(
    'DFA_LANDING_PAST_YD', 1.5, 'Death from Above: landing point past the target along rogue -> target, yards '
    '[fixed].')
DFA_MIN_JUMP_YD = const(
    'DFA_MIN_JUMP_YD', 1.5, 'Death from Above: minimum horizontal leg length, yards [fixed].')
DFA_APEX_HEIGHT_YD = const(
    'DFA_APEX_HEIGHT_YD', 8.0, 'Death from Above: apex above the higher end, yards [tune].')
DFA_RISE_FRACTION = const(
    'DFA_RISE_FRACTION', 0.4, 'Death from Above: apex position along the line to the landing point [tune].')
DFA_RISE_MS = const(
    'DFA_RISE_MS', 650, 'Death from Above: rise leg air time, ms [tune].')
DFA_DRIFT_MS = const(
    'DFA_DRIFT_MS', 500, 'Death from Above: slow-fall leg air time between the rise and the dive, ms [tune].')
DFA_DRIFT_DROP_YD = const(
    'DFA_DRIFT_DROP_YD', 2.0, 'Death from Above: slow-fall leg drop below the apex, yards [tune].')
DFA_DRIFT_FORWARD_YD = const(
    'DFA_DRIFT_FORWARD_YD', 1.0, 'Death from Above: slow-fall leg drift toward the landing point, yards [tune].')
DFA_DIVE_MS = const(
    'DFA_DIVE_MS', 600, 'Death from Above: dive leg air time, ms (rise + slow fall + dive about 1.75 s) [tune].')
# The flight aura 204171 covers the whole leap with margin: 2 s plus the slow fall.
DFA_FLIGHT_MS = 2000 + DFA_DRIFT_MS['value']
DFA_UNREACHABLE_Z_YD = const(
    'DFA_UNREACHABLE_Z_YD', 5.0, 'Death from Above: landing z vs target z beyond this = unreachable, yards [tune].')


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


def _reads(**by_effect):
    """Reader masks from `eff0=` / `eff1=` / `eff2=` (0-based effect index -> (d0, d1, d2) triple), through the
    `_masks` raw-key helper only (never hand-written keys)."""
    keys = {}
    for name, triple in by_effect.items():
        keys.update(m.read_mask_keys(int(name[-1]), triple))
    return keys


# =====================================================================================================================
# Hidden talent ranks (WP-BRIEF section 10.15): Attributes 464, duration -1, SpellLevel 9 + 5 x row + rank,
# raw ProcTypeMask 0 / ProcChance 101. Stored base points = live - 1.
# =====================================================================================================================
def _rank(spell_id, name, rank, row, effects, icon, description, raw=None, notes=''):
    """One hidden talent rank passive. `rank` is the NameSubtext number (None for a one-rank talent)."""
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
        notes='rogue-rework S2a A3, subtlety doc section 5: hidden talent rank passive (Attributes 464, SpellLevel '
              f'= 9 + 5 x {row} + rank, stored = live - 1). ' + notes,
        raw_overrides=overrides,
    )


def _buff(spell_id, name, effects, icon, duration_ms, text, raw=None, notes='', range_index=_RANGE_SELF):
    """A visible, non-passive self buff (custom-spells.md): number-free aura text = the doc's, Ex1 0x20 (R19: it may be
    cast while stealthed without breaking Stealth)."""
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


# ---------------------------------------------------------------------------------------------------------------------
# Death from Above frame and potency: the area hit 204169 first (the castable's tooltip quotes it)
# ---------------------------------------------------------------------------------------------------------------------
# 204169: Physical SCHOOL_DAMAGE, cp_ap_potency 8 per combo point (40 potency at 5) [tune], SpellLevel 60, 8 yd around
# Death from Above's target (A 53 TARGET_DEST_TARGET_ENEMY / B 16 TARGET_UNIT_DEST_AREA_ENEMY, cast at the target;
# S2a-REVIEW L8), RangeIndex 6 / facing 0 (a script cast, R11), d2 b7 | d2 b18, hidden. A cp-only potency effect needs
# base_potency 0 (potency.resolve rejects an all-zero effect without one). R12: no combo-point attributes, so the finish
# phase never clears the rogue's points and Cold Blood / Relentless never read it as a finisher; the per-combo-point
# line still reads the live points (SpellPotency::Apply uses GetComboPoints() with no attribute test).
death_from_above_area_204169 = spell(
    id=204169, name='Death from Above', school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=None, radius_yards=8.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_potency=0.0, cp_ap_potency=8.0, potency_kind='direct',
               implicit_target_a=_TARGET_DEST_TARGET_ENEMY, implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY,
               radius_yards=8.0),
    ],
    spell_icon_id=_ICON_DEATH_FROM_ABOVE,
    notes='rogue-rework S2a A3, subtlety doc "Death from Above" (Known-hard 3, R12, R15): the area hit cast by '
          'spell_rog_death_from_above at the DUMMY hit. Physical SCHOOL_DAMAGE, cp_ap_potency 8 per combo point '
          '(40 at 5) [tune], base_potency 0 (cp-only effect), SpellLevel 60, cast at the DfA target: A 53 '
          'TARGET_DEST_TARGET_ENEMY / B 16 TARGET_UNIT_DEST_AREA_ENEMY radius 8 around it (S2a-REVIEW L8; '
          'spell_rog_death_from_above_area keeps the explicit target + units in combat with the rogue), DefenseType 2 '
          '(melee crit, dodgeable like Eviscerate), RangeIndex 6 (100 yd), FacingCasterFlags 0, no combo attributes '
          '(R12), EquippedItemClass -1, hidden. d2 b7 | d2 b18 (m.DEATH_FROM_ABOVE_CLASS), never d0 b17.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.DEATH_FROM_ABOVE_CLASS), 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'SpellLevel': 60, 'DefenseType': 2, 'PreventionType': 0, 'RangeIndex': _RANGE_100_YD,
        'FacingCasterFlags': 0,
        'Description_Lang_enUS': 'Strikes the target and the enemies within 8 yards of it for Physical damage.',
    },
)
scripted_by(death_from_above_area_204169, 'spell_rog_death_from_above_area')

# 204170: the landing. Physical SCHOOL_DAMAGE ap_potency 29.25 + cp_ap_potency 46.2 (1.5 x Eviscerate's 19.5 / 30.8)
# [tune], SpellLevel 60, A 6 on the target, 100 yd (R11, a script cast), Eviscerate's visual 671 (U47), d2 b8 | d2 b18
# (counts as an Eviscerate for Finality / Seal-style readers), never d0 b17. R4: the C++ passes the snapshot as bp0
# (CastCustomSpell skips the potency rescale) and SpellDamageBonusDone adds 29.25 potency of AP read at the landing.
death_from_above_landing_204170 = spell(
    id=204170, name='Death from Above', school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=None,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=29.25, cp_ap_potency=46.2, potency_kind='direct',
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_DEATH_FROM_ABOVE,
    notes='rogue-rework S2a A3, subtlety doc "Death from Above" (Known-hard 3, R4, R11, R12, R15): the landing hit, cast '
          'by Rogue::LaunchDeathFromAbove with bp0 = the snapshot. Physical SCHOOL_DAMAGE ap_potency 29.25 + '
          'cp_ap_potency 46.2 direct [tune] (1.5 x Eviscerate\'s 19.5 / 30.8), SpellLevel 60, A 6, RangeIndex 6 '
          '(100 yd), FacingCasterFlags 0, DefenseType 2, Eviscerate\'s visual 671, no combo attributes, hidden. d2 b8 | '
          'd2 b18 (m.DFA_LANDING_CLASS), never d0 b17. R4: the flat 29.25 potency of AP is live at the landing '
          '(~10% of a 5-point landing); no potency_excluded.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.DFA_LANDING_CLASS), 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'SpellLevel': 60, 'DefenseType': 2, 'PreventionType': 0, 'RangeIndex': _RANGE_100_YD,
        'FacingCasterFlags': 0, 'SpellVisualID_1': _SV_EVISCERATE,
        'Description_Lang_enUS': 'Comes down on the target with an Eviscerate that is 50% stronger.',
    },
)
scripted_by(death_from_above_landing_204170, 'spell_rog_death_from_above_landing')

# 204171: the flight aura. Root immunity + safe fall + pacify (aura 25: no swings, no PreventionType 2 spells; Shadow
# Dance and Preparation are PreventionType 0 and stay usable in the air), 2 s + DFA_DRIFT_MS (2.5 s: rise 0.65 s +
# slow fall 0.5 s + dive 0.6 s, with margin), visible "Leaping.". Ex1 0x8000:
# the root immunity purges a root already on the rogue (a rooted rogue may cast Death from Above; S2-CODE-REVIEW L2).
death_from_above_flight_204171 = _buff(
    204171, 'Death from Above',
    [_aura(AuraType.MECHANIC_IMMUNITY, 0, _MISC_ROOT_MECHANIC), _aura(_AURA_SAFE_FALL, 99), _aura(AuraType.MOD_PACIFY, 0)],
    _ICON_DEATH_FROM_ABOVE, DFA_FLIGHT_MS, 'Leaping.',
    raw={'AttributesEx': _ATTR1_ALLOW_WHILE_STEALTHED | _ATTR1_IMMUNITY_PURGES_EFFECT},
    notes='rogue-rework S2a A3, subtlety doc "Death from Above" (Known-hard 3, R8): the flight aura Rogue::'
          'LaunchDeathFromAbove adds and removes. eff0 aura 77 MECHANIC_IMMUNITY misc 7 (root), eff1 aura 144 SAFE_FALL, '
          'eff2 aura 25 MOD_PACIFY (not 60 PACIFY_SILENCE: casting Shadow Dance is a PreventionType 0 spell), 2.5 s '
          '(2 s + the slow fall DFA_DRIFT_MS), visible, number-free text, Ex1 0x20 (R19) | 0x8000 IMMUNITY_PURGES_EFFECT (a root already on '
          'the rogue is purged when the leap starts; S2-CODE-REVIEW L2).',
)

# ---------------------------------------------------------------------------------------------------------------------
# Death from Above 204148: the castable
# ---------------------------------------------------------------------------------------------------------------------
_DFA_CP = _potency.resolve(
    _potency.PotencyEffect(ap_potency=8.0, kind=_potency.KIND_PERIODIC, t_ms=1500.0), spell_level=60)
# The 5-combo-point area damage (40 potency): 5 x the level-60 line + 5 x the AP coefficient x AP, inside one `$max()`
# (a top-level `+` outside it is dropped by the client; potency.md "Tooltips").
_DFA_AREA_5CP = ('${$max(0,' + _potency._fmt(5 * _DFA_CP.level60_value) + '+'
                 + _potency._fmt(5 * _DFA_CP.ap_coefficient) + '*$AP)}')
_DEATH_FROM_ABOVE_TEXT = (
    f'Finishing move that strikes the target and all enemies within $204169a1 yards for {_DFA_AREA_5CP} Physical damage, '
    'then leaps into the air and comes down on the target with an Eviscerate that is 50% stronger. Damage per combo '
    'point.')

# Eviscerate's frame (R15): typed Attributes 327696, raw AttributesEx 0x100200, Ex3 0x400, weapon requirement 2 / 173555,
# PreventionType 2, FacingCasterFlags 1, but DefenseType 0 (the DUMMY never misses; the two hits roll their own), 25 energy
# [tune], 15 yd (RangeIndex 11), 20 s (the Player.cpp allow list makes Cooldown Haste apply), GCD 133 / 1000, SpellLevel /
# BaseLevel 60, eff0 DUMMY on the target (A 6). The only row that carries the finisher attributes (R12).
death_from_above_204148 = spell(
    id=204148, name='Death from Above', school=School.NORMAL, attributes=_ATTR0_FINISHER,
    cast_time_ms=0, cooldown_ms=20000, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=25,
    mana_cost_pct=0, range_yards=None,
    effects=[Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_DEATH_FROM_ABOVE,
    notes='rogue-rework S2a A3, subtlety doc "Death from Above" (Known-hard 3, R8, R15): the capstone castable (SkillLine'
          'Ability 30825 via the talent bundling). Eviscerate 2098\'s frame (typed Attributes 327696, Ex 0x100200, Ex3 '
          '0x400, EquippedItemClass 2 / 173555, PreventionType 2, FacingCasterFlags 1) with DefenseType 0, 25 energy '
          '[tune], RangeIndex 11 (15 yd), 20 s (Cooldown Haste through the Player.cpp allow list), GCD 133 / 1000, '
          'SpellLevel / BaseLevel 60. eff0 DUMMY on the target. d2 b7 | d2 b18 (m.DEATH_FROM_ABOVE_CLASS). '
          'spell_rog_death_from_above: snapshot + area hit + Rogue::LaunchDeathFromAbove. The tooltip quotes the area '
          'hit at 5 combo points (40 potency).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.DEATH_FROM_ABOVE_CLASS),
        'EquippedItemClass': _ITEM_CLASS_WEAPON, 'EquippedItemSubclass': _ANY_MELEE_WEAPON, 'CastingTimeIndex': 1,
        'AttributesEx': _ATTR1_FINISHER, 'AttributesEx3': _ATTR3_REQUIRES_MAIN_HAND, 'DefenseType': 0,
        'PreventionType': 2, 'FacingCasterFlags': 1, 'RangeIndex': _RANGE_15_YD, 'SpellLevel': 60, 'BaseLevel': 60,
        'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'Description_Lang_enUS': _DEATH_FROM_ABOVE_TEXT,
    },
)
scripted_by(death_from_above_204148, 'spell_rog_death_from_above')

# =====================================================================================================================
# Helper rows (the rank tooltips quote their durations)
# =====================================================================================================================

# ---- Master of Subtlety buff 204154 (Known-hard 5) ----
# eff0 aura 79 MOD_DAMAGE_PERCENT_DONE misc 1 (Physical; mixed-school hits match) bp 0 (the script sets the amount),
# eff1 aura 226 PERIODIC_DUMMY 1000 ms (the Mastery poll, S1 spell_rog_vile_poisons_mastery precedent), infinite (idx 21;
# the C++ sets tails), visible.
master_of_subtlety_buff_204154 = _buff(
    204154, 'Master of Subtlety',
    [_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, 0, _MISC_PHYSICAL),
     Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000,
            implicit_target_a=_TARGET_UNIT_CASTER)],
    _ICON_MASTER_OF_SUBTLETY, -1, 'Your physical attacks deal more damage.',
    notes='rogue-rework S2a A3, subtlety doc "Master of Subtlety" (Known-hard 5): eff0 aura 79 misc 1 (Physical) bp 0 '
          '(spell_rog_master_of_subtlety_buff sets the amount through Rogue::GetMasterOfSubtletyPct), eff1 aura 226 '
          '1 s (the Mastery poll). Infinite (idx 21): Rogue::UpdateHiddenBuffs shortens it to the tail. Visible, '
          'non-passive, number-free text, Ex1 0x20. No family bits.',
)
scripted_by(master_of_subtlety_buff_204154, 'spell_rog_master_of_subtlety_buff')

# ---- Relentless Strikes armor buff 204155 ----
# aura 280 MOD_ARMOR_PENETRATION_PCT misc 1 bp 9 (+10%, Serrated Blades' eff1 shape), 5 s (idx 28), visible.
relentless_strikes_buff_204155 = _buff(
    204155, 'Relentless Strikes', [_aura(_AURA_MOD_ARMOR_PENETRATION_PCT, 9, _MISC_PHYSICAL)], _ICON_RELENTLESS_STRIKES,
    5000, 'Your attacks ignore some of your target\'s armor.',
    notes='rogue-rework S2a A3, subtlety doc "Relentless Strikes" (Known-hard 12): aura 280 misc 1 +10% (stored 9; '
          'Serrated Blades\' eff1 shape), 5 s (idx 28), cast by the dispatcher with the 25 energy. Visible, number-free '
          'text, Ex1 0x20.',
)

# ---- Lingering Shadow buff 204156 ----
# DUMMY, StackAmount (CumulativeAura) 2, 15 s (idx 8), visible; Rogue::OnShadowedRemoved casts it and sets the stacks.
lingering_shadow_buff_204156 = _buff(
    204156, 'Lingering Shadow', [_dummy(0)], _ICON_LINGERING_SHADOW, 15000,
    'Your next Backstab awards an additional combo point.', raw={'CumulativeAura': 2},
    notes='rogue-rework S2a A3, subtlety doc "Lingering Shadow" (U50): DUMMY, CumulativeAura 2, 15 s (idx 8), cast when '
          'Shadowed ends (stacks = the rank), one stack per Backstab. Visible, number-free text, Ex1 0x20.',
)

# ---- Finality buffs 204157 / 204158 / 204159 (U43) ----
# bp 0 (the C++ passes 10 / 20 = the rank), 30 s (idx 9), no charges, visible; pct DAMAGE on Eviscerate + the landing,
# pct DOT on Rupture, pct DAMAGE on Deadly Throw (+ its copies, d1 b0).
finality_eviscerate_204157 = _buff(
    204157, 'Finality', [_pct(SpellModOp.DAMAGE, 0)], _ICON_FINALITY, 30000,
    'Your next Eviscerate deals more damage.', raw=_reads(eff0=m.FINALITY_EVISCERATE_READ),
    notes='rogue-rework S2a A3, subtlety doc "Finality" (U43): pct DAMAGE bp 0 (the C++ passes the rank 10 / 20) on '
          'm.FINALITY_EVISCERATE_READ (Eviscerate d0 b17 + the landing d2 b8), 30 s (idx 9), no charges, visible, '
          'number-free text, Ex1 0x20.',
)
finality_rupture_204158 = _buff(
    204158, 'Finality', [_pct(SpellModOp.DOT, 0)], _ICON_FINALITY, 30000, 'Your next Rupture deals more damage.',
    raw=_reads(eff0=m.FINALITY_RUPTURE_READ),
    notes='rogue-rework S2a A3, subtlety doc "Finality" (U43): pct DOT bp 0 (the C++ passes the rank) on '
          'm.FINALITY_RUPTURE_READ (Rupture d0 b20), 30 s (idx 9), no charges, visible, number-free text, Ex1 0x20. The '
          'bonus is snapshotted into the DoT at application.',
)
finality_deadly_throw_204159 = _buff(
    204159, 'Finality', [_pct(SpellModOp.DAMAGE, 0)], _ICON_FINALITY, 30000,
    'Your next Deadly Throw deals more damage.', raw=_reads(eff0=m.FINALITY_DEADLY_THROW_READ),
    notes='rogue-rework S2a A3, subtlety doc "Finality" (U43): pct DAMAGE bp 0 (the C++ passes the rank) on '
          'm.FINALITY_DEADLY_THROW_READ (d1 b0: Deadly Throw and its 204168 copies), 30 s (idx 9), no charges, visible, '
          'number-free text, Ex1 0x20.',
)

# ---- Hemorrhage bleed 204160 and tick 204161 (Known-hard 4) ----
# The Doomblade shapes (rogue_assassination.py 203829 / 203830) on d2 b12 only (never d0 b20: Hemorrhage is not Rupture).
# The bleed is the stored-bleed carrier: PERIODIC_DUMMY 2000 ms, 8 s (idx 31), mechanic 15, Ex3 0x80, visible debuff
# "Bleeding.", 100 yd (R11). The tick is the damage spell_rog_hemorrhage casts per period (bp0 = the stored tick).
hemorrhage_bleed_204160 = spell(
    id=204160, name='Hemorrhage', school=School.NORMAL, mechanic=_MECHANIC_BLEED, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=None, duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=2000, mechanic=_MECHANIC_BLEED,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_HEMORRHAGE_BLEED,
    notes='rogue-rework S2a A3, subtlety doc "Hemorrhage" (Known-hard 4, R11): the visible bleed debuff. PERIODIC_DUMMY '
          '2000 ms (fixed cadence: no haste attribute), 8 s (idx 31), mechanic 15, Ex3 0x80 (stack per caster), '
          'DefenseType 0, RangeIndex 6 (100 yd, a script cast), FacingCasterFlags 0. d2 b12 only '
          '(m.HEMORRHAGE_CLASS), never d0 b20. ApplyStoredBleed stores the per-tick amount, spell_rog_hemorrhage '
          'casts the tick.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.HEMORRHAGE_CLASS), 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'DefenseType': 0, 'RangeIndex': _RANGE_100_YD, 'FacingCasterFlags': 0,
        'AttributesEx3': _ATTR3_STACK_PER_CASTER,
        'Description_Lang_enUS': 'Causes the target to bleed.',
        'AuraDescription_Lang_enUS': 'Bleeding.',
    },
)
scripted_by(hemorrhage_bleed_204160, 'spell_rog_hemorrhage')

hemorrhage_tick_204161 = spell(
    id=204161, name='Hemorrhage', school=School.NORMAL, mechanic=_MECHANIC_BLEED, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=None,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, mechanic=_MECHANIC_BLEED, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
               potency_excluded='the amount is the stored tick a script passes as bp0 (30% of an Eviscerate or landing '
                                'hit that already carried every modifier); percent-of-other-damage, no potency of its '
                                'own'),
    ],
    spell_icon_id=_ICON_HEMORRHAGE_BLEED,
    notes='rogue-rework S2a A3, subtlety doc "Hemorrhage" (Known-hard 4, R11): the hidden tick cast by '
          'spell_rog_hemorrhage with bp0 = the stored per-tick amount. Physical SCHOOL_DAMAGE, mechanic 15, Ex3 '
          'IGNORE_CASTER_MODIFIERS 0x20000000 + ALWAYS_HIT 0x40000 + SUPPRESS_CASTER_PROCS 0x10000, Ex2 CANT_CRIT, '
          'DefenseType 0, RangeIndex 6, FacingCasterFlags 0, custom attr 0x8000 (a share of post-armor damage, '
          'S1-CODE-REVIEW M1). d2 b12 only. potency_excluded.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.HEMORRHAGE_CLASS), 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'DefenseType': 0, 'RangeIndex': _RANGE_100_YD, 'FacingCasterFlags': 0,
        'AttributesEx2': _ATTR2_CANT_CRIT,
        'AttributesEx3': _ATTR3_IGNORE_CASTER_MODIFIERS | _ATTR3_ALWAYS_HIT | _ATTR3_SUPPRESS_CASTER_PROCS,
        'Description_Lang_enUS': 'Deals Physical damage to the target.',
    },
)
# The tick deals a share of damage that already went through armor; Unit.cpp checks armor before the bleed exemption, so
# without SPELL_ATTR0_CU_IGNORE_ARMOR every tick would lose armor a second time (S1 lesson, Doomblade 203830).
custom_attr(hemorrhage_tick_204161, _CU_IGNORE_ARMOR)

# ---- Akaari's echo strike 204162 and the clone tint 204163 (U46) ----
# The echo: Physical SCHOOL_DAMAGE bp from script, SpellClassSet 8 with NO family bits at all (the echo reaches no reader),
# Ex3 IGNORE_CASTER_MODIFIERS + ALWAYS_HIT + SUPPRESS_CASTER_PROCS, Ex2 CANT_CRIT, DefenseType 0, melee range (RangeIndex 2:
# "lost out of range" on purpose), FacingCasterFlags 0, custom attr 0x8000, hidden, potency_excluded.
akaaris_echo_strike_204162 = spell(
    id=204162, name='Akaari\'s Echo', school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=None,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
               potency_excluded='the amount is a share of the Ambush\'s damage that Rogue::ScheduleAkaariEcho passes '
                                'as bp0 (percent-of-other-damage); no potency of its own'),
    ],
    spell_icon_id=_ICON_AKAARIS_ECHO,
    notes='rogue-rework S2a A3, subtlety doc "Akaari\'s Echo" (Known-hard 9, R11): the hidden echo strike cast by '
          'Rogue::ScheduleAkaariEcho with bp0 = 50% of the Ambush. Physical SCHOOL_DAMAGE, SpellClassSet 8 with NO '
          'family bits (no reader reaches it; no d0 b9), Ex3 IGNORE_CASTER_MODIFIERS + ALWAYS_HIT + '
          'SUPPRESS_CASTER_PROCS, Ex2 CANT_CRIT, DefenseType 0, RangeIndex 2 (melee: lost when the rogue moved out of '
          'range), FacingCasterFlags 0, custom attr 0x8000. potency_excluded. Executioner excludes it by id (R3).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys((0, 0, 0)), 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'DefenseType': 0, 'RangeIndex': _RANGE_MELEE, 'FacingCasterFlags': 0,
        'AttributesEx2': _ATTR2_CANT_CRIT,
        'AttributesEx3': _ATTR3_IGNORE_CASTER_MODIFIERS | _ATTR3_ALWAYS_HIT | _ATTR3_SUPPRESS_CASTER_PROCS,
        'Description_Lang_enUS': 'Strikes the target from the shadows.',
    },
)
custom_attr(akaaris_echo_strike_204162, _CU_IGNORE_ARMOR)

# The tint: P0 204390's row (an `_instant` DUMMY self aura, SV 3619 = Shadowform's state kit, 2 s idx 39), visible on the
# clone only (Rogue::ScheduleAkaariEcho adds it with AddAura, bug-doc 1067).
akaaris_echo_tint_204163 = spell(
    id=204163, name='Akaari\'s Echo', school=School.NORMAL, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=2000,
    effects=[_dummy(0)],
    spell_icon_id=_ICON_AKAARIS_ECHO,
    notes='rogue-rework S2a A3, subtlety doc "Akaari\'s Echo" (Known-hard 9, S2a-0VERIFY item 12): P0 204390\'s row. One '
          'DUMMY self effect, SpellVisualID_1 3619 (Shadowform 15473\'s state kit 3129), 2 s (idx 39), attributes 0 '
          '(visible), added to the clone with AddAura. No family bits.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'SpellVisualID_1': _SV_SHADOWFORM_TINT,
        'Description_Lang_enUS': 'A shadow copy of the rogue.', 'AuraDescription_Lang_enUS': 'Shadowy.',
    },
)

# ---- Mark of the Master Assassin buff 204164 (U36) ----
# eff0 flat CRITICAL_CHANCE bp 0 (the C++ passes the rank 50 / 100) on m.MOMA_READ_S3 (S3, U65: MOMA_READ plus Between
# the Eyes d2 b5 and Blade Rush d2 b15), infinite (idx 21), visible.
mark_of_the_master_assassin_buff_204164 = _buff(
    204164, 'Mark of the Master Assassin', [_flat(SpellModOp.CRITICAL_CHANCE, 0)], _ICON_MOMA, -1,
    'Critical strike chance increased.', raw=_reads(eff0=m.MOMA_READ_S3),
    notes='rogue-rework S2a A3, subtlety doc "Mark of the Master Assassin" (U36, Known-hard 5, R20): flat '
          'CRITICAL_CHANCE bp 0 (the C++ passes 50 / 100 = the rank) on m.MOMA_READ (every rogue button\'s direct hit '
          'incl. Riposte; never poisons, autos or periodic damage), infinite (idx 21), tails by '
          'Rogue::UpdateHiddenBuffs. Visible, number-free text, Ex1 0x20. S3a A3 (U65): the mask is '
          'm.MOMA_READ_S3 (adds Between the Eyes d2 b5 and Blade Rush d2 b15; Pistol Shot and Riposte are in via d2 '
          'b19).',
)

# ---- Sinister Calling volley 204165 (Known-hard 12, R11) ----
# SchoolMask 0x21 (Shadowstrike: Physical + Shadow), ap_potency 30 per target [tune] direct at SpellLevel 47, dest at the
# target (A 53) + enemies within 8 yd (B 16), d2 b17, Ex3 SUPPRESS_CASTER_PROCS, Fan of Knives' visual, 100 yd, no facing.
sinister_calling_volley_204165 = spell(
    id=204165, name='Sinister Calling', school=School.NORMAL | School.SHADOW, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=None, radius_yards=8.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=30.0, potency_kind='direct',
               implicit_target_a=_TARGET_DEST_TARGET_ENEMY, implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY,
               radius_yards=8.0),
    ],
    spell_icon_id=_ICON_SINISTER_CALLING,
    notes='rogue-rework S2a A3, subtlety doc "Sinister Calling" (Known-hard 12, R11, R12): the capstone volley cast at '
          'the finisher\'s target by the dispatcher. SchoolMask 0x21 (Shadowstrike), ap_potency 30 direct per target '
          '[tune] at SpellLevel 47, A 53 TARGET_DEST_TARGET_ENEMY / B 16 TARGET_UNIT_DEST_AREA_ENEMY radius 8 '
          '(spell_rog_sinister_calling_volley keeps the explicit target + units in combat with the rogue, at most 3), '
          'RangeIndex 6, FacingCasterFlags 0, DefenseType 2 (melee table, judgement call: the brief leaves it open), '
          'no combo attributes, Fan of Knives\' visual 12317, Ex3 SUPPRESS_CASTER_PROCS, hidden. d2 b17 '
          '(m.SINISTER_CALLING_VOLLEY_CLASS).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.SINISTER_CALLING_VOLLEY_CLASS),
        'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'SpellLevel': 47, 'DefenseType': 2, 'RangeIndex': _RANGE_100_YD,
        'FacingCasterFlags': 0, 'SpellVisualID_1': _SV_FAN_OF_KNIVES, 'AttributesEx3': _ATTR3_SUPPRESS_CASTER_PROCS,
        'Description_Lang_enUS': 'Flings a volley of knives at the target and nearby enemies.',
    },
)
scripted_by(sinister_calling_volley_204165, 'spell_rog_sinister_calling_volley')

# ---- Second Volley copies 204166 / 204167 (U41) ----
# 204166 = Fan of Knives 51723's eff0 (weapon_potency 70, A 18 / B 16 radius 8) + eff1 ADD_COMBO_POINTS (as 51723), d1 b18
# (keeps the dagger +50% hardcode on purpose), SpellLevel 24, 51723's visual, Ex3 SUPPRESS_CASTER_PROCS (+ the stock main
# hand requirement), no combo attributes (R12). 204167 = 52874's frame (off hand), linked from 204166 (type 0, the 51723 ->
# 52874 shape). 204166 is bound to the shared Fan of Knives script (one combo point on the selection per cast).
second_volley_main_204166 = spell(
    id=204166, name='Fan of Knives', school=School.NORMAL, attributes=_ATTR0_FAN_OF_KNIVES | _ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, radius_yards=8.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=70, implicit_target_a=_TARGET_DEST_CASTER,
               implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=8.0),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=_TARGET_DEST_CASTER,
               implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=8.0),
    ],
    spell_icon_id=_ICON_FAN_OF_KNIVES,
    notes='rogue-rework S2a A3, subtlety doc "Second Volley" (U41, Known-hard 8, R12): the main-hand copy a Fan of Knives '
          'proc casts 300 ms later (triggered: no poison roll, no Seal Fate, no third fan). 51723\'s eff0 '
          'WEAPON_PERCENT_DAMAGE weapon_potency 70 + eff1 ADD_COMBO_POINTS on the same A 18 / B 16 radius 8, Speed 18, '
          'SpellLevel 24, visual 12317, d1 b18 (m.SECOND_VOLLEY_CLASS: the dagger +50% hardcode stays), Ex3 0x10400 '
          '(main hand + SUPPRESS_CASTER_PROCS), no combo attributes, PreventionType 0. Bound to spell_rog_fan_of_knives '
          '(one point on the selection per cast); linked to the off-hand 204167.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.SECOND_VOLLEY_CLASS),
        'EquippedItemClass': _ITEM_CLASS_WEAPON, 'EquippedItemSubclass': _ANY_MELEE_WEAPON, 'CastingTimeIndex': 1,
        'AttributesEx': _ATTR1_FAN_OF_KNIVES, 'AttributesEx3': _ATTR3_REQUIRES_MAIN_HAND | _ATTR3_SUPPRESS_CASTER_PROCS,
        'DefenseType': 2, 'PreventionType': 0, 'RangeIndex': _RANGE_SELF, 'SpellLevel': 24, 'Speed': 18.0,
        'SpellVisualID_1': _SV_FAN_OF_KNIVES,
        'Description_Lang_enUS': 'Throws a second volley of knives at all enemies within $a1 yards, causing $s1% weapon '
                                 'damage. Awards 1 combo point.',
    },
)
scripted_by(second_volley_main_204166, 'spell_rog_fan_of_knives')

second_volley_off_204167 = spell(
    id=204167, name='Fan of Knives', school=School.NORMAL, attributes=_ATTR0_FAN_OF_KNIVES | _ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, radius_yards=8.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=70, implicit_target_a=_TARGET_DEST_CASTER,
               implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=8.0),
    ],
    spell_icon_id=_ICON_FAN_OF_KNIVES,
    notes='rogue-rework S2a A3, subtlety doc "Second Volley" (U41, Known-hard 8): the off-hand copy, linked from 204166 '
          '(type 0, the 51723 -> 52874 shape). 52874\'s frame (off hand: Ex3 REQUIRES_OFF_HAND 0x1000000 + '
          'SUPPRESS_CASTER_PROCS 0x10000, Speed 18, visual 12318), eff0 weapon_potency 70, SpellLevel 24, d1 b18 '
          '(m.SECOND_VOLLEY_CLASS), no combo effect, no combo attributes.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.SECOND_VOLLEY_CLASS),
        'EquippedItemClass': _ITEM_CLASS_WEAPON, 'EquippedItemSubclass': _ANY_MELEE_WEAPON, 'CastingTimeIndex': 1,
        'AttributesEx': _ATTR1_FAN_OF_KNIVES, 'AttributesEx3': _ATTR3_REQUIRES_OFF_HAND | _ATTR3_SUPPRESS_CASTER_PROCS,
        'DefenseType': 2, 'PreventionType': 0, 'RangeIndex': _RANGE_SELF, 'SpellLevel': 24, 'Speed': 18.0,
        'SpellVisualID_1': _SV_FAN_OF_KNIVES_OFF_HAND,
        'Description_Lang_enUS': 'Throws a second volley of knives at all enemies within $a1 yards, causing $s1% weapon '
                                 'damage.',
    },
)
linked_spell(second_volley_main_204166.id, second_volley_off_204167.id, 0,
             'Second Volley: the main-hand copy also throws the off hand (the 51723 -> 52874 shape)')

# ---- Throwing Specialization copy 204168 (U40, Known-hard 7) ----
# Deadly Throw 26679's eff0 (ap_potency 14.625 + cp_ap_potency 23.1, SpellLevel 36) and eff1 slow, thrown requirement and
# ranged frame, but no combo-point attributes (R12), 100 yd / no facing (R11), d1 b0 only (R21: no d2 b18, so an
# Assassination hybrid's Ruthlessness / Find Weakness on finishers do not reach the copies; harmless for Subtlety),
# Ex3 SUPPRESS_CASTER_PROCS, hidden. The per-combo-point line reads the live points (SpellPotency::Apply).
throwing_specialization_copy_204168 = spell(
    id=204168, name='Deadly Throw', school=School.NORMAL, attributes=_ATTR0_DEADLY_THROW | _ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=None, duration_ms=6000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=14.625, cp_ap_potency=23.1, potency_kind='direct',
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=_ICON_DEADLY_THROW,
    notes='rogue-rework S2a A3, subtlety doc "Throwing Specialization" (U40, Known-hard 7, R11, R12, R21): the copy '
          'spell_rog_deadly_throw_subtlety casts at up to 2 other enemies. Deadly Throw 26679\'s eff0 SCHOOL_DAMAGE '
          'ap_potency 14.625 + cp_ap_potency 23.1 direct at SpellLevel 36 and eff1 slow (aura 33, -50%, 6 s), typed '
          'Attributes 4259858, thrown weapon requirement 2 / 65536 (the flat AP term reads ranged AP through '
          'IsRangedWeaponSpell), DefenseType 3, Speed 50, visual 7929, CastingTimeIndex 18, no combo attributes, '
          'RangeIndex 6, FacingCasterFlags 0, Ex3 SUPPRESS_CASTER_PROCS, hidden. d1 b0 only (m.DEADLY_THROW_COPY_CLASS): '
          'no d2 b18, so Ruthlessness / Find Weakness on finishers do not reach the copies (R21, accepted).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, **m.class_mask_keys(m.DEADLY_THROW_COPY_CLASS),
        'EquippedItemClass': _ITEM_CLASS_WEAPON, 'EquippedItemSubclass': _THROWN_WEAPON, 'CastingTimeIndex': 18,
        'DefenseType': 3, 'PreventionType': 0, 'RangeIndex': _RANGE_100_YD, 'FacingCasterFlags': 0, 'SpellLevel': 36,
        'Speed': 50.0, 'SpellVisualID_1': _SV_DEADLY_THROW, 'AttributesEx3': _ATTR3_SUPPRESS_CASTER_PROCS,
        'Description_Lang_enUS': 'Throws a weapon at the target, causing Physical damage and reducing its movement '
                                 'speed.',
        'AuraDescription_Lang_enUS': 'Movement slowed.',
    },
)

# ---- Honor Among Thieves buff 204172 (U39, U48, R9) ----
# eff0 aura 79 MOD_DAMAGE_PERCENT_DONE misc 127 bp 2 (+3%), 10 s (idx 1), target A 21 (an ally), 100 yd, visible; applied
# with AddAura on the rogue and the picked ally, so the range / target rows never run. A second rogue's replaces this one.
honor_among_thieves_buff_204172 = _buff(
    204172, 'Honor Among Thieves',
    [_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, 2, _MISC_ALL_SCHOOLS, target=_TARGET_UNIT_TARGET_ALLY)],
    _ICON_HONOR_AMONG_THIEVES, 10000, 'Damage increased.', range_index=_RANGE_100_YD,
    notes='rogue-rework S2a A3, subtlety doc "Honor Among Thieves" (U39, U48, R9): aura 79 misc 127 (all schools) +3% '
          '(stored 2), 10 s (idx 1), A 21 TARGET_UNIT_TARGET_ALLY, RangeIndex 6, visible, number-free text, Ex1 0x20. '
          'Added with AddAura on the rogue and the ally; no spell_group (a second rogue\'s buff replaces this one).',
)

# ---- Enveloping Shadows helper 204173 (U44) ----
# eff0 aura 87 MOD_DAMAGE_PERCENT_TAKEN misc 1 bp 0 (the script sets -rank), self, infinite, hidden but NOT passive: an aura
# link (spell_linked_spell 203723 -> 204173 type 2) applies and removes it with Ghostly Veil.
enveloping_shadows_helper_204173 = spell(
    id=204173, name='Enveloping Shadows', school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, 0, _MISC_PHYSICAL)],
    spell_icon_id=_ICON_ENVELOPING_SHADOWS,
    notes='rogue-rework S2a A3, subtlety doc "Enveloping Shadows" (U44): hidden helper linked to Ghostly Veil 203723 '
          '(type 2: it lives exactly as long as the Veil). eff0 aura 87 MOD_DAMAGE_PERCENT_TAKEN misc 1 (Physical) bp 0 '
          '(spell_rog_enveloping_shadows sets -rank 2 / 4 / 6 in DoEffectCalcAmount), self, infinite (idx 21), '
          'DO_NOT_DISPLAY but not PASSIVE (an aura link needs a real aura), Ex1 0x20 (R19).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'AttributesEx': _ATTR1_ALLOW_WHILE_STEALTHED,
        'Description_Lang_enUS': 'Reduces the physical damage you take while Ghostly Veil is active.',
    },
)
scripted_by(enveloping_shadows_helper_204173, 'spell_rog_enveloping_shadows')
linked_spell(203723, enveloping_shadows_helper_204173.id, 2,
             'Enveloping Shadows: the damage-taken helper lives exactly as long as Ghostly Veil')


# =====================================================================================================================
# Talent ranks
# =====================================================================================================================

# ---- (0,1) Deepening Shadows 60425: aura 306 Cooldown Haste +1 / +2 / +3% (paladin_holy_ranks.py:147 shape) ----
def _deepening_shadows(spell_id, rank):
    return _rank(
        spell_id, 'Deepening Shadows', rank, _ROW_DEEPENING_SHADOWS,
        [_aura(AuraType.MOD_CUSTOM_STAT_PCT, rank - 1, _CR_COOLDOWN_HASTE)], _ICON_DEEPENING_SHADOWS,
        'Increases your Cooldown Haste by $s1%.',
        notes=f'aura 306 MOD_CUSTOM_STAT_PCT misc 1 << 22 (Cooldown Haste) +{rank}% (stored {rank - 1}).')


deepening_shadows_204130 = _deepening_shadows(204130, 1)
deepening_shadows_204131 = _deepening_shadows(204131, 2)
deepening_shadows_204132 = _deepening_shadows(204132, 3)


# ---- (1,1) Shadow Resolve 60426: aura 306 Versatility +1 / +2 / +3% (deathknight_blood.py shape) ----
def _shadow_resolve(spell_id, rank):
    return _rank(
        spell_id, 'Shadow Resolve', rank, _ROW_SHADOW_RESOLVE,
        [_aura(AuraType.MOD_CUSTOM_STAT_PCT, rank - 1, _CR_VERSATILITY)], _ICON_SHADOW_RESOLVE,
        'Increases your Versatility by $s1%.',
        notes=f'aura 306 MOD_CUSTOM_STAT_PCT misc 1 << 21 (Versatility) +{rank}% (stored {rank - 1}).')


shadow_resolve_204133 = _shadow_resolve(204133, 1)
shadow_resolve_204134 = _shadow_resolve(204134, 2)
shadow_resolve_204135 = _shadow_resolve(204135, 3)


# ---- (3,2) Second Volley 60427: DUMMY 20 / 40 (% chance on a Fan of Knives cast) ----
def _second_volley(spell_id, rank):
    return _rank(
        spell_id, 'Second Volley', rank, _ROW_SECOND_VOLLEY, [_dummy(20 * rank - 1)], _ICON_SECOND_VOLLEY,
        'Your Fan of Knives has a $s1% chance to throw a second Fan of Knives, which awards 1 additional combo point.',
        notes=f'DUMMY {20 * rank} (% chance, rolled once per Fan of Knives cast, x Proc Chance; read by GetRankAmount '
              'EFFECT_0).')


second_volley_204136 = _second_volley(204136, 1)
second_volley_204137 = _second_volley(204137, 2)


# ---- (3,3) Lingering Shadow 60428: DUMMY 1 / 2 (Backstabs; also the buff's stacks) ----
def _lingering_shadow(spell_id, rank):
    return _rank(
        spell_id, 'Lingering Shadow', rank, _ROW_LINGERING_SHADOW, [_dummy(rank - 1)], _ICON_LINGERING_SHADOW,
        'When Shadowed ends, your next $s1 $lBackstab:Backstabs; $lawards:award; 1 additional combo point. Lasts '
        '$204156d.',
        notes=f'DUMMY {rank} (Backstabs = the buff\'s stack count; read by GetRankAmount EFFECT_0).')


lingering_shadow_204138 = _lingering_shadow(204138, 1)
lingering_shadow_204139 = _lingering_shadow(204139, 2)


# ---- (4,2) Finality 60429: DUMMY 10 / 20 (% = the three buffs' bp) ----
def _finality(spell_id, rank):
    return _rank(
        spell_id, 'Finality', rank, _ROW_FINALITY, [_dummy(10 * rank - 1)], _ICON_FINALITY,
        'When you use Eviscerate, Rupture or Deadly Throw, your next use of that same finisher deals $s1% more damage. '
        'Each finisher has its own empowerment, lasting $204157d, and you can hold several at once. Using an '
        'empowered finisher does not empower the next one.',
        notes=f'DUMMY {10 * rank} (% more damage = the bp the C++ gives 204157 / 204158 / 204159).')


finality_204140 = _finality(204140, 1)
finality_204141 = _finality(204141, 2)

# ---- (5,1) Executioner 60430: DUMMY 10 / 20 (% below the health threshold); the capstone is r2's presence ----
_EXECUTIONER_TEXT = f'Your abilities deal $s1% more damage to targets below {_c(EXECUTIONER_HEALTH_PCT)}% health.'
_EXECUTIONER_CAP = (f'Capstone: Your finishing moves against targets below {_c(EXECUTIONER_HEALTH_PCT)}% health also '
                    f'reduce the remaining cooldown of Shadow Dance by {_sec(EXECUTIONER_CDR_PER_CP_MS)} sec per combo '
                    'point spent.')


def _executioner(spell_id, rank):
    return _rank(
        spell_id, 'Executioner', rank, _ROW_EXECUTIONER, [_dummy(10 * rank - 1)], _ICON_EXECUTIONER,
        _with_cap(_EXECUTIONER_TEXT, _EXECUTIONER_CAP, rank == 2),
        notes=f'DUMMY {10 * rank} (% more damage, read live per hit and tick by GetHealthClauseMultiplier)'
              + ('; the capstone is HasAura(204143).' if rank == 2 else '.'))


executioner_204142 = _executioner(204142, 1)
executioner_204143 = _executioner(204143, 2)


# ---- (8,0) Akaari's Echo 60431: DUMMY 15 / 30 (% chance on an Ambush) ----
def _akaaris_echo(spell_id, rank):
    return _rank(
        spell_id, 'Akaari\'s Echo', rank, _ROW_AKAARIS_ECHO, [_dummy(15 * rank - 1)], _ICON_AKAARIS_ECHO,
        'Your Ambush has a $s1% chance to strike the target again from the shadows '
        f'{_sec(AKAARI_ECHO_DELAY_MS)} sec later, for {_c(AKAARI_ECHO_SHARE_PCT)}% of the damage it dealt.',
        notes=f'DUMMY {15 * rank} (% chance per Ambush, x Proc Chance; read by GetRankAmount EFFECT_0).')


akaaris_echo_204144 = _akaaris_echo(204144, 1)
akaaris_echo_204145 = _akaaris_echo(204145, 2)


# ---- (9,1) Mark of the Master Assassin 60432: DUMMY 50 / 100 (% crit = the buff's bp) ----
def _moma(spell_id, rank):
    return _rank(
        spell_id, 'Mark of the Master Assassin', rank, _ROW_MOMA, [_dummy(50 * rank - 1)], _ICON_MOMA,
        f'While stealthed and for {_sec(MOMA_TAIL_MS)} sec after leaving Stealth, the critical strike chance of your '
        'direct damage is increased by $s1%.',
        notes=f'DUMMY {50 * rank} (% crit; Rogue::UpdateHiddenBuffs passes it as bp0 to 204164).')


mark_of_the_master_assassin_204146 = _moma(204146, 1)
mark_of_the_master_assassin_204147 = _moma(204147, 2)

# ---- (6,1) Master of Subtlety (fresh ids, 1C.27): DUMMY 4 / 8 / 12 (%); the capstone adds Mastery ----
_MOS_TEXT = (f'Physical attacks made while Hidden, and for {_sec(MASTER_OF_SUBTLETY_TAIL_MS)} sec after leaving '
             'Stealth, deal $s1% more damage.')
_MOS_CAP = 'Capstone: This damage bonus is increased by your Mastery.'


def _master_of_subtlety(spell_id, rank):
    return _rank(
        spell_id, 'Master of Subtlety', rank, _ROW_MASTER_OF_SUBTLETY, [_dummy(4 * rank - 1)],
        _ICON_MASTER_OF_SUBTLETY, _with_cap(_MOS_TEXT, _MOS_CAP, rank == 3),
        notes=f'DUMMY {4 * rank} (%; Rogue::GetMasterOfSubtletyPct)'
              + ('; the capstone (Mastery added 1:1) is HasAura(204151).' if rank == 3 else '.'))


master_of_subtlety_204149 = _master_of_subtlety(204149, 1)
master_of_subtlety_204150 = _master_of_subtlety(204150, 2)
master_of_subtlety_204151 = _master_of_subtlety(204151, 3)

# ---- (4,3) Hemorrhage rank 204152 (U38): DUMMY 30 (% share of the Eviscerate / landing damage) ----
hemorrhage_204152 = _rank(
    204152, 'Hemorrhage', None, _ROW_HEMORRHAGE, [_dummy(29)], _ICON_HEMORRHAGE,
    'Your Eviscerate also causes the target to hemorrhage, dealing $s1% of the Eviscerate\'s damage as a bleed over '
    '$204160d.',
    notes='DUMMY 30 (% share; read by GetRankAmount EFFECT_0 in Rogue::OnEviscerateHit). The talent has flags 0 (a '
          'passive rank).')

# ---- (6,0) Premeditation rank 204153 (U38): DUMMY 2 (combo points) ----
premeditation_204153 = _rank(
    204153, 'Premeditation', None, _ROW_PREMEDITATION, [_dummy(1)], _ICON_PREMEDITATION,
    'When you activate Shadow Dance or Vanish, you gain $s1 combo points.',
    notes='DUMMY 2 (combo points; read by GetRankAmount EFFECT_0 in the dispatcher). The talent has flags 0 (a passive '
          'rank).')


# =====================================================================================================================
# Creature 300350: Akaari's clone (U46). A copy of the P0 spike's 300369 template (faction 31, level 60, exp 2, mage class,
# NON_ATTACKABLE | NOT_SELECTABLE 0x2000002, flags2 2048, type 7 / type_flags 0x1000000, HealthModifier 0.4, speed 1 /
# 1.14286, detection 20, HoverHeight 1, no AI, no script), display 11686 (Mirror Image's). The live 300369 row is an
# orphan of the spike and stays untouched.
# =====================================================================================================================
akaari_clone_300350 = creature_template(
    300350, 'Akaari Clone', minlevel=60, maxlevel=60, exp=2, faction=31, speed_walk=1.0, speed_run=1.14286,
    detection_range=20.0, DamageModifier=1.0, BaseAttackTime=2000, RangeAttackTime=2000, unit_class=8,
    unit_flags=33554434, unit_flags2=2048, type=7, type_flags=16777216, HoverHeight=1.0, HealthModifier=0.4,
    RegenHealth=1, flags_extra=0, npcflag=0, AIName='', ScriptName='',
)
creature_model(300350, display_id=11686, scale=1.0, idx=0, probability=1.0)


# =====================================================================================================================
# SpellDescriptionVariables 1335 / 1336 (U34, R18): talent bonuses on the Backstab / Ambush tooltips. A3 declares, A4
# attaches with `tooltip_vars=` on Backstab 53 / Ambush 8676 and rewrites the multiplier tokens (`{potN*bsmult}` /
# `{potN*ammult}`). talent_mult(effect=N) is 1-based. SpellMod DAMAGE percents are multiplicative in the core
# (Player::ApplySpellMod), so `product` is right. Names are at most 12 characters (helper suffixes included).
# =====================================================================================================================
# 1335 Backstab: From the Shadows (eff 1 of 14057 / 14072) x Slaughter from the Shadows (eff 1 of 51708-51710).
tooltip_backstab_1335 = tooltip_vars(
    1335, 'From the Shadows x Slaughter from the Shadows on Backstab',
    fts=talent_mult([14057, 14072], effect=1),
    slaughter=talent_mult([51708, 51709, 51710], effect=1),
    bsmult=product('fts', 'slaughter'),
    # S3 (U58): Surprise Attacks (eff 1 of 32601 / 203981 / 203982); Backstab's tooltip uses `bsall` (was `bsmult`).
    surprise=talent_mult([32601, 203981, 203982], effect=1),
    bsall=product('bsmult', 'surprise'),
)

# 1336 Ambush: From the Shadows x Waylay (eff 1 of 51692 / 51696).
tooltip_ambush_1336 = tooltip_vars(
    1336, 'From the Shadows x Waylay on Ambush',
    fts=talent_mult([14057, 14072], effect=1),
    waylay=talent_mult([51692, 51696], effect=1),
    ammult=product('fts', 'waylay'),
    # S3 (U58): Surprise Attacks; Ambush's tooltip uses `amall` (was `ammult`).
    surprise=talent_mult([32601, 203981, 203982], effect=1),
    amall=product('ammult', 'surprise'),
)
