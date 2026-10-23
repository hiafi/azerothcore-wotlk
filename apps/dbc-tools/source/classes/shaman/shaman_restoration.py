"""
Shaman - S2a A3: the Restoration spec's new spells and creatures (docs/reworks/shaman-restoration-rework.md section 5;
brief .agents/plans/shaman-rework/shaman-rework.S2a-WP-BRIEF.md id map, S2-NOTES sections 1-3, S2a-0VERIFY).

Ids 202640-202681 (Resto block 202640-202759):
    202640-202654  talent rank spells and castables (Flowing Tides 3, Rainfall 2, Spirit Link Totem, Totemic Resonance,
                   Undulating Currents Totem, Tidecaller 2, Kindling 2, Cloudburst Totem, Improved Earth Shield rank 3,
                   the new Tidal Force castable)
    202660-202681  buffs, heals and helpers (read by the C++ by id)
SkillLineAbility 30700-30703 (Spirit Link, Undulating Currents, Cloudburst, Tidal Force), creatures 300279-300282.

Conventions (copied from shaman_elemental.py)
- SpellClassSet 11 only where a SpellMod / aura 283 / class bit needs it (a family-0 mod would match every spell); the
  Cloudburst release, the Tidal Force echo and the Bulwark shield stay in family 0 so no shaman mod or the Tidal Force
  stack (aura 283 with an all-zero mask = every family-11 heal of the caster) can reach them. `EquippedItemClass -1`
  on every row (L1).
- Static rows store live - 1 (a +10% mod is base_points 9; a -10% cast-time mod is -11). Percent SpellMods multiply by
  the stack count in `AuraEffect::CalculateAmount`, so a per-stack value is stored per stack.
- Visible buffs are non-passive with no consolidation flag (AttributesEx7 0x10000000 clear) and a number-free aura text.
  Hidden helpers carry SPELL_ATTR0_DO_NOT_DISPLAY. Counters that must outlive death (Healing Tide counter, Undulation
  counter) carry the L5 pair AttributesEx3 0x100000 + AttributesEx2 0x1.
- Capstone tooltip format (talent-tooltip-audit step 5): grey "Capstone Bonus: ..." on every rank below the last,
  plain on the last.
- Heals are potency rows with SpellLevel set (the learn level of the granting row); script-sized rows (echo, Bulwark
  shield, release) are potency_excluded.

Bindings declared here: spell_sha_resto_tidal_force (202654), spell_sha_resto_cloudburst (202652),
spell_sha_resto_cloudburst_store (202665), spell_sha_resto_undulating_heal (202663),
spell_sha_resto_totemic_resonance (202662); unbind of the stock spell_sha_tidal_force_dummy from 55198. Every other
class-table binding is on a stock id (A2 / A4).
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import (
    const, creature_model, creature_spell, creature_template, pot_text, procs_on, scripted_by, skill_line_ability,
    spell, unbind_script,
)

from . import _masks as m
from .shaman_resto_tooltips import shaman_healtotems_1224

SPELLFAMILY_SHAMAN = 11
NOTE = 'shaman-rework S2a A3: '

# ---- Spell.dbc flag values ------------------------------------------------------------------------------------------
ATTR0_PASSIVE_HIDDEN = 0x1D0          # PASSIVE | DO_NOT_DISPLAY | ...: the talent-rank shape (stock attributes 464)
ATTR0_DO_NOT_DISPLAY = 0x80
ATTR0_NO_AURA_CANCEL = 0x80000000      # SPELL_ATTR0_CANT_CANCEL: no right-click cancel (SpellHandler.cpp)
ATTR0_NOT_SHAPESHIFTED = 0x10000
ATTR2_ALLOW_DEAD_TARGET = 0x1
ATTR2_IGNORE_LOS = 0x4
ATTR2_CANT_CRIT = 0x20000000
ATTR3_DOT_STACKING_RULE = 0x80        # stack separately for each caster
ATTR3_SUPPRESS_CASTER_PROCS = 0x10000
ATTR3_ALLOW_AURA_WHILE_DEAD = 0x100000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
ATTR7_SUMMON_PLAYER_TOTEM = 0x20

TARGET_UNIT_CASTER = 1
TARGET_UNIT_TARGET_ALLY = 21
TARGET_DEST_CASTER_BACK_RIGHT = 43    # stock Air slot (3738 / 8512)
TARGET_DEST_CASTER_FRONT_RIGHT = 44   # stock Fire slot (Searing 3599)
TARGET_UNIT_TARGET_CHAINHEAL_ALLY = 45

SUMMON_PROPS_FIRE = 63
SUMMON_PROPS_AIR = 83

SCHOOL_ALL = 127

CR_COOLDOWN_HASTE_BIT = 1 << 22

PROC_FLAG_DONE_MAGIC_POS = 0x4000
PROC_FLAG_DONE_MAGIC_NEG = 0x10000
PROC_FLAG_DONE_PERIODIC = 0x40000
PROC_ATTR_REQ_SPELLMOD = 0x8
PROC_ATTR_TRIGGERED_CAN_PROC = 0x2
PHASE_CAST = 0x1
PHASE_HIT = 0x2
TYPE_HEAL = 0x2
TYPE_ALL = 0x7

SKILL_LINE_RESTORATION = 374
CLASS_MASK_SHAMAN = 64

# ---- Family masks (SpellClassSet 11) ------------------------------------------------------------------------------------
LB = 0x1                              # d0 b0
CL = 0x2                              # d0 b1
HEALING_WAVE = 0x40                   # d0 b6
LESSER_HEALING_WAVE = 0x80            # d0 b7
CHAIN_HEAL = 0x100                    # d0 b8
EARTH_SHOCK = 0x100000                # d0 b20
RIPTIDE = 0x10                        # d2 b4
EARTH_SHIELD_D1 = 0x400               # d1 b10 (Earth Shield 974, the stock shield anchor: allowed as a mod target)

# "Nature spell" scope of the Nature's Guardian crit buff: the shaman's own Nature casts that have a direct hit. Not
# Healing Rain (its pulses are separate triggered heals), not Earthquake (a ground zone), not the Fire / Frost shocks,
# not totem heals (the buff is consumed by the shaman's own casts only).
NG_CRIT_MASK = (LB | CL | EARTH_SHOCK | HEALING_WAVE | LESSER_HEALING_WAVE | CHAIN_HEAL, 0, RIPTIDE)

# ---- Spell icons (stock SpellIconID; unique inside the Restoration tree, art is the V stage) -----------------------------
ICON_FLOWING_TIDES = 545              # Water Breathing
ICON_RAINFALL = 2011                  # Spell_Nature_GiftoftheWaterSpirit (the Healing Rain icon)
ICON_SPIRIT_LINK = 3994               # Totemic Recall
ICON_TOTEMIC_RESONANCE = 2216         # Totemic Recall (alt)
ICON_UCT = 72                         # Flametongue Totem
ICON_TIDECALLER = 2134                # Summon Water Elemental
ICON_KINDLING = 51                    # Fire Nova
ICON_CLOUDBURST = 1397                # Windfury Totem
ICON_IES = 2015                       # Earth Shield
ICON_TIDAL_FORCE = 176                # Tidal Force
ICON_HEALING_STREAM = 1647            # Healing Stream Totem
ICON_TIDAL_WAVES = 3057               # Tidal Waves
ICON_LESSER_HEALING_WAVE = 964        # Lesser Healing Wave
ICON_CHAIN_HEAL = 963                 # Chain Heal
ICON_HEALING_WAVE = 13                # Healing Wave
ICON_NATURES_GUARDIAN = 2013          # Nature's Guardian
ICON_TOTEMIC_FOCUS = 46               # Totemic Focus
ICON_BULWARK = 690                    # Stoneskin Totem buff (the Earthen Wall shield icon)
ICON_TIDAL_FOCUS = 36                 # Tidal Focus
ICON_WATER_SHIELD = 2287              # Water Shield
ICON_MANA_TIDE = 94                   # Mana Tide Totem
ICON_RIPTIDE = 3786                   # Riptide

SV_AIR_SUMMON = 319
SV_FIRE_SUMMON = 221
SV_TIDAL_FORCE = 12092                # the stock Tidal Force 55198's visual
SV_CHAIN_HEAL = 3659                  # the stock Chain Heal 1064's visual: its cast kit 3169 carries the beam (SpellChainEffects 736)

# Stock totem displays (CreatureDisplayInfo): earth 4588, fire 4589, water 4587, air 4590.
DISPLAY_WATER_TOTEM = 4587
DISPLAY_FIRE_TOTEM = 4589
DISPLAY_AIR_TOTEM = 4590


# =====================================================================================================================
# Script numbers (generated into ShamanData::). The brief's list; per-rank percentages the C++ reads come from a
# rank's DUMMY effect or these (S1-L8).
# =====================================================================================================================
TIDAL_WAVES_MAX = const('TIDAL_WAVES_MAX', 3, 'Tidal Waves: maximum charges [tune]; also the CumulativeAura stack cap of 202669.')
TIDAL_WAVES_DURATION_MS = const('TIDAL_WAVES_DURATION_MS', 15000, 'Tidal Waves: duration, refreshed by each grant, ms [tune] (stock).')
TW_GRANT_CHAIN_HEAL = const('TW_GRANT_CHAIN_HEAL', 3, 'Tidal Waves: charges a Chain Heal grants [fixed].')
TW_GRANT_RIPTIDE = const('TW_GRANT_RIPTIDE', 2, 'Tidal Waves: charges a Riptide grants [fixed].')
TW_CHANCE_R1 = const('TW_CHANCE_R1', 33, 'Tidal Waves rank 1: chance a Chain Heal / Riptide cast grants charges, percent (Proc Chance applies) [fixed].')
TW_CHANCE_R2 = const('TW_CHANCE_R2', 66, 'Tidal Waves rank 2 grant chance, percent [fixed].')
TW_CHANCE_R3 = const('TW_CHANCE_R3', 100, 'Tidal Waves rank 3 grant chance, percent [fixed].')
UNDULATION_CASTS = const('UNDULATION_CASTS', 3, 'Undulation: every Nth Healing Wave / Lesser Healing Wave cast is stronger [fixed].')
UNDULATION_BONUS_PCT = const('UNDULATION_BONUS_PCT', 50, 'Undulation: bonus healing on the Nth cast, percent [fixed].')
RIP_CURRENT_CHANCE = const('RIP_CURRENT_CHANCE', 20, 'Rip Current: chance a Riptide cast also casts Riptide on a second ally, percent (Proc Chance applies) [fixed].')
RIP_CURRENT_RADIUS_YD = const('RIP_CURRENT_RADIUS_YD', 20.0, 'Rip Current: second-ally search radius around the primary target, yd [fixed].')
RAINFALL_CHANCE = const('RAINFALL_CHANCE', 15, 'Rainfall capstone: chance a Riptide cast makes the next Healing Rain instant, percent (Proc Chance applies) [fixed].')
KINDLING_CHANCE = const('KINDLING_CHANCE', 15, 'Kindling capstone: chance a Chain Heal cast cuts the Undulating Currents Totem cooldown, percent (Proc Chance applies) [fixed].')
KINDLING_CDR_MS = const('KINDLING_CDR_MS', 3000, 'Kindling capstone: real-time cooldown reduction of the Undulating Currents Totem, ms [fixed].')
IWS_CAPSTONE_MANA_PCT = const('IWS_CAPSTONE_MANA_PCT', 1, 'Improved Water Shield capstone: percent of maximum mana per direct-heal critical strike [fixed].')
BULWARK_PCT = const('BULWARK_PCT', 40, 'Earthen Bulwark: percent of the main Earthen Wall shield given to every other ally [fixed].')
BULWARK_RADIUS_YD = const('BULWARK_RADIUS_YD', 10.0, 'Earthen Bulwark: radius around the totem, yd [fixed].')
TOTEMIC_FOCUS_TARGETS = const('TOTEMIC_FOCUS_TARGETS', 5, 'Totemic Focus capstone: injured allies healed per totem placement [fixed].')
TOTEMIC_FOCUS_RADIUS_YD = const('TOTEMIC_FOCUS_RADIUS_YD', 20.0, 'Totemic Focus capstone: radius around the placed totem, yd [fixed].')
TOTEMIC_FOCUS_DELAY_MS = const('TOTEMIC_FOCUS_DELAY_MS', 1, 'Totemic Focus capstone: delay between the placement and the heal, ms [fixed].')
TR_PCT_PER_COUNT = const('TR_PCT_PER_COUNT', 5, 'Totemic Resonance: healing and absorb bonus per counted totem, percent [fixed].')
TR_MASTERY_COEFF_PCT = const('TR_MASTERY_COEFF_PCT', 30, 'Totemic Resonance capstone: percent of Mastery added to each count [fixed].')
TR_MAX_COUNT = const('TR_MAX_COUNT', 4, 'Totemic Resonance: maximum counts, one per element [fixed]; also the CumulativeAura cap of 202662.')
TR_REFRESH_MS = const('TR_REFRESH_MS', 1000, 'Totemic Resonance: live Mastery refresh period of the aura, ms [tune].')
CLOUDBURST_STORE_PCT = const('CLOUDBURST_STORE_PCT', 30, 'Cloudburst Totem: percent of effective Nature healing stored [fixed].')
CLOUDBURST_RADIUS_YD = const('CLOUDBURST_RADIUS_YD', 40.0, 'Cloudburst Totem: release radius around the totem, yd [fixed].')
CLOUDBURST_COOLDOWN_MS = const('CLOUDBURST_COOLDOWN_MS', 60000, 'Cloudburst Totem: base cooldown, ms (scripted from placement; Cooldown Haste applies) [fixed].')
CLOUDBURST_DURATION_MS = const('CLOUDBURST_DURATION_MS', 15000, 'Cloudburst Totem: duration, ms [fixed] (the summon row 202652 carries the same).')
SPIRIT_LINK_RADIUS_YD = const('SPIRIT_LINK_RADIUS_YD', 10.0, 'Spirit Link Totem: link radius, yd [tune].')
SPIRIT_LINK_INTERVAL_MS = const('SPIRIT_LINK_INTERVAL_MS', 1000, 'Spirit Link Totem: redistribution period, the first at placement, ms [tune].')
UCT_INTERVAL_MS = const('UCT_INTERVAL_MS', 2000, 'Undulating Currents Totem: ms between casts, the first at placement [fixed].')
UCT_CASTS = const('UCT_CASTS', 6, 'Undulating Currents Totem: casts per placement [fixed].')
UCT_RANGE_YD = const('UCT_RANGE_YD', 40.0, 'Undulating Currents Totem: target search radius, yd [tune].')
TIDE_TARGETS = const('TIDE_TARGETS', 10, 'Healing Tide Totem: allies healed per pulse, lowest health percent first [fixed].')
HST_TARGETS = const('HST_TARGETS', 5, 'Healing Stream Totem: allies healed per pulse (the Tide branch reads it beside TIDE_TARGETS) [fixed].')
IHS_PLACEMENTS = const('IHS_PLACEMENTS', 3, 'Improved Healing Stream capstone: every Nth Healing Stream placement is a Healing Tide [fixed].')
TF_DURATION_MS = const('TF_DURATION_MS', 10000, 'Tidal Force: duration of the caster aura 202672, ms [fixed].')
TF_ECHO_PCT = const('TF_ECHO_PCT', 30, 'Tidal Force: Healing Wave echo, percent of the amount healed [fixed].')
TF_ECHO_DELAY_MS = const('TF_ECHO_DELAY_MS', 1000, 'Tidal Force: delay of the Healing Wave echo, ms [fixed].')
TF_STACK_MAX = const('TF_STACK_MAX', 3, 'Tidal Force: Lesser Healing Wave stacks on the ally [fixed]; also the CumulativeAura cap of 202673.')
TM_EXT_HW_MS = const('TM_EXT_HW_MS', 2000, 'Tidal Mastery capstone: Tidal Force extension on a Healing Wave critical strike, ms [fixed].')
TM_EXT_RIPTIDE_MS = const('TM_EXT_RIPTIDE_MS', 2000, 'Tidal Mastery capstone: extension on a Riptide direct-heal critical strike, ms [fixed].')
TM_EXT_LHW_MS = const('TM_EXT_LHW_MS', 1000, 'Tidal Mastery capstone: extension on a Lesser Healing Wave critical strike, ms [fixed].')
TM_EXT_CH_MS = const('TM_EXT_CH_MS', 500, 'Tidal Mastery capstone: extension on a Chain Heal critical strike (once per cast), ms [fixed].')
TIDAL_FOCUS_CLEANSE_RADIUS_YD = const('TIDAL_FOCUS_CLEANSE_RADIUS_YD', 40.0, 'Tidal Focus capstone: party search radius around the placed Cleansing Totem, yd [fixed].')
TIDAL_FOCUS_CLEANSE_COUNT = const('TIDAL_FOCUS_CLEANSE_COUNT', 2, 'Tidal Focus capstone: disease and poison effects removed per party member, each [fixed].')
MANA_TIDE_PARTY_PCT_X10 = const('MANA_TIDE_PARTY_PCT_X10', 25, 'Mana Tide Totem: party mana per pulse, tenths of a percent of maximum mana (2.5%) [fixed].')
MANA_TIDE_SELF_PCT = const('MANA_TIDE_SELF_PCT', 5, 'Mana Tide Totem: shaman mana per pulse, percent of maximum mana [fixed].')
NG_THRESHOLD_PCT = const('NG_THRESHOLD_PCT', 30, 'Nature\'s Guardian capstone: health percent a damaging attack must bring the shaman below [fixed].')
NG_ICD_MS = const('NG_ICD_MS', 30000, 'Nature\'s Guardian capstone: internal cooldown, ms [tune] (the stock cooldown).')
IES_TW_ICD_MS = const('IES_TW_ICD_MS', 5000, 'Improved Earth Shield capstone: internal cooldown of the Tidal Waves charge, ms [fixed].')
BOTE_THRESHOLD_PCT = const('BOTE_THRESHOLD_PCT', 35, 'Blessing of the Eternals: target health percent at or below which the Earthliving bonus applies [fixed].')
BOTE_BONUS_R1 = const('BOTE_BONUS_R1', 40, 'Blessing of the Eternals rank 1: relative Earthliving chance bonus, percent [fixed].')
BOTE_BONUS_R2 = const('BOTE_BONUS_R2', 80, 'Blessing of the Eternals rank 2: relative Earthliving chance bonus, percent [fixed].')
AA_RADIUS_YD = const('AA_RADIUS_YD', 40.0, 'Ancestral Awakening: search radius for the most injured ally, yd [fixed].')
ICH_CHARGES_NEEDED = const('ICH_CHARGES_NEEDED', 2, 'Improved Chain Heal capstone: Tidal Waves charges consumed to arm the buff [fixed].')


# =====================================================================================================================
# Helpers
# =====================================================================================================================
def _text(description: str = '', aura: str = '') -> dict:
    return {
        'Description_Lang_Mask': 16712190 if description else 16712188,
        'Description_Lang_enUS': description,
        'AuraDescription_Lang_Mask': 16712190 if aura else 16712188,
        'AuraDescription_Lang_enUS': aura,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_Mask': 16712188,
    }


def _emask(effect: int, mask) -> dict:
    """EffectSpellClassMask{A,B,C}_{1,2,3}: the LETTER is the effect (1 -> A), the number the dword. `mask` is an int
    (dword 0) or a (d0, d1, d2) tuple."""
    letter = 'ABC'[effect - 1]
    dwords = mask if isinstance(mask, tuple) else (mask, 0, 0)
    return {f'EffectSpellClassMask{letter}_{i + 1}': value for i, value in enumerate(dwords) if value}


def _raw(description: str = '', aura: str = '', level: int = 1, family: bool = True, **extra) -> dict:
    raw = {
        **_text(description, aura),
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
        'CastingTimeIndex': 1,
        'EquippedItemClass': -1,
        'ProcChance': 101,
        'SpellLevel': level,
    }
    if family:
        raw['SpellClassSet'] = SPELLFAMILY_SHAMAN
    raw.update(extra)
    return raw


def _aura(aura, base_points: int = 0, misc_value: int = 0, target: int = TARGET_UNIT_CASTER, **kw) -> Effect:
    return Effect(type=EffectType.APPLY_AURA, apply_aura=aura, base_points=base_points, misc_value=int(misc_value),
                  implicit_target_a=target, **kw)


def _mod(op: SpellModOp, pct: bool, base_points: int) -> Effect:
    """A self-targeted SpellMod; the scope mask goes through `_emask` on the same effect slot."""
    return _aura(AuraType.ADD_PCT_MODIFIER if pct else AuraType.ADD_FLAT_MODIFIER, base_points, int(op))


def _dummy(base_points: int = 0) -> Effect:
    return _aura(AuraType.DUMMY, base_points)


def _desc(text: str, capstone: str | None = None, last: bool = False) -> str:
    """talent-tooltip-audit step 5: grey capstone clause on every non-final rank, plain on the final one."""
    if capstone is None:
        return text
    if last:
        return f'{text}\n\nCapstone Bonus: {capstone}'
    return f'{text}\n\n|cFF9D9D9DCapstone Bonus: {capstone}|r'


def _rank(spell_id: int, name: str, effects: list, icon: int, level: int, description: str, notes: str,
          subtext: str = '', **raw_extra):
    """A talent rank spell: hidden passive, infinite, self."""
    raw = _raw(description, '', level, **raw_extra)
    if subtext:
        raw['NameSubtext_Lang_Mask'] = 16712190
        raw['NameSubtext_Lang_enUS'] = subtext
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=ATTR0_PASSIVE_HIDDEN,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=-1, effects=effects, spell_icon_id=icon,
        notes=NOTE + notes, raw_overrides=raw,
    )


def _buff(spell_id: int, name: str, effects: list, icon: int, duration_ms: int, aura: str = '', description: str = '',
          notes: str = '', school=School.NATURE, hidden: bool = False, stacks: int = 0, charges: int = 0,
          level: int = 1, persist: bool = False, family: bool = True, range_yards=RANGE_SELF,
          no_cancel: bool = False, **raw_extra):
    """A buff. Visible by default (non-passive, no consolidation flag); `hidden` adds DO_NOT_DISPLAY; `persist` adds the
    death-persistence pair (L5); `no_cancel` adds ATTR0_NO_AURA_CANCEL (a state indicator the player must not click
    off). `stacks` = CumulativeAura, `charges` = ProcCharges."""
    raw = _raw(description, aura, level, family, **raw_extra)
    if stacks:
        raw['CumulativeAura'] = stacks
    if charges:
        raw['ProcCharges'] = charges
        raw['ProcChance'] = 100
    if persist:
        raw['AttributesEx2'] = raw.get('AttributesEx2', 0) | ATTR2_ALLOW_DEAD_TARGET
        raw['AttributesEx3'] = raw.get('AttributesEx3', 0) | ATTR3_ALLOW_AURA_WHILE_DEAD
    return spell(
        id=spell_id, name=name, school=school,
        attributes=(ATTR0_DO_NOT_DISPLAY if hidden else 0) | (ATTR0_NO_AURA_CANCEL if no_cancel else 0),
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=range_yards, duration_ms=duration_ms, effects=effects, spell_icon_id=icon,
        notes=NOTE + notes, raw_overrides=raw,
    )


def _heal(spell_id: int, name: str, potency: float, t_ms: int, icon: int, level: int, notes: str, description: str,
          target: int = TARGET_UNIT_TARGET_ALLY, family: bool = True, **raw_extra):
    """A totem- or script-cast potency heal at an ally: Nature, instant, free, range 50000 (RangeIndex 13) and
    AttributesEx2 0x4 (the targets sit anywhere near the caster; stock 52042 gets the same from SpellInfoCorrections)."""
    raw = _raw(description, '', level, family, DefenseType=1, PreventionType=1, **raw_extra)
    raw['AttributesEx2'] = raw.get('AttributesEx2', 0) | ATTR2_IGNORE_LOS
    return spell(
        id=spell_id, name=name, school=School.NATURE, attributes=0,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
        effects=[Effect(type=EffectType.HEAL, sp_potency=potency, potency_kind='heal', time_basis_ms=t_ms,
                        implicit_target_a=target)],
        spell_icon_id=icon, notes=NOTE + notes, raw_overrides=raw,
    )


def _totem_summon(spell_id: int, name: str, creature: int, props: int, target_a: int, duration_ms: int,
                  cooldown_ms: int, icon: int, level: int, description: str, notes: str, visual: int, tooltip_vars=None):
    """A player totem summon in the stock shape (SH0b `_summon`): SUMMON creature (base_points 4 as stock 5394 / 3738),
    SummonProperties in EffectMiscValueB_1, AttributesEx7 SUMMON_PLAYER_TOTEM, Category 0, instant, GCD 1000 / 133, no
    tool column, family d0 b29 only. The mana cost is 0 ([tune], set at the balance pass)."""
    raw = _raw(
        description, '', level,
        BaseLevel=level, DefenseType=1, EffectMiscValueB_1=props, AttributesEx7=ATTR7_SUMMON_PLAYER_TOTEM,
        StartRecoveryCategory=133, StartRecoveryTime=1000,
        SpellClassMask_1=m.SUMMON_D0_B29, SpellVisualID_1=visual,
    )
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=ATTR0_NOT_SHAPESHIFTED, category=0,
        cast_time_ms=0, cooldown_ms=cooldown_ms, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=target_a, misc_value=creature)],
        spell_icon_id=icon, notes=NOTE + notes, raw_overrides=raw, tooltip_vars=tooltip_vars,
    )


# =====================================================================================================================
# Talent rank spells 202640-202654 (the learn level of row N is 10 + 5N)
# =====================================================================================================================

# ---- Flowing Tides (60310, row 0): Cooldown Haste +1/2/3% -------------------------------------------------------------
def _flowing_tides(spell_id: int, pct: int):
    return _rank(
        spell_id, 'Flowing Tides',
        [_aura(AuraType.MOD_CUSTOM_STAT_PCT, pct - 1, CR_COOLDOWN_HASTE_BIT)], ICON_FLOWING_TIDES, 10,
        f'Increases your Cooldown Haste by {pct}%.',
        f'Flowing Tides rank {pct}: aura 306 (MOD_CUSTOM_STAT_PCT) misc 1 << 22 (CR_COOLDOWN_HASTE) +{pct}% (stored '
        f'{pct - 1}). No capstone.',
    )


flowing_tides_rank1_202640 = _flowing_tides(202640, 1)
flowing_tides_rank2_202641 = _flowing_tides(202641, 2)
flowing_tides_rank3_202642 = _flowing_tides(202642, 3)

# ---- Rainfall (60311, row 5): Healing Rain +5/10%; rank 2 = the capstone marker -------------------------------------------
_RAINFALL_CAPSTONE = 'Your Riptide has a 15% chance to make your next Healing Rain within 20 sec instant.'


def _rainfall(spell_id: int, pct: int, last: bool):
    effects = [_mod(SpellModOp.DAMAGE, True, pct - 1)]
    if last:
        effects.append(_dummy())
    return _rank(
        spell_id, 'Rainfall', effects, ICON_RAINFALL, 35,
        _desc(f'Increases the healing done by your Healing Rain by {pct}%.', _RAINFALL_CAPSTONE, last),
        f'Rainfall rank {pct // 5}: eff1 SPELLMOD_DAMAGE pct +{pct}% (stored {pct - 1}) on Healing Rain (d2 b21: the cast '
        f'and the pulse heal 202284; the torrent d2 b22 is not covered).'
        + (' Rank 2 is the capstone: eff2 is the marker (DUMMY); the Riptide script grants 202668 with RAINFALL_CHANCE '
           'while this rank is known.' if last else ''),
        **_emask(1, (0, 0, m.HEALING_RAIN)),
    )


rainfall_rank1_202643 = _rainfall(202643, 5, False)
rainfall_rank2_202644 = _rainfall(202644, 10, True)

# ---- Spirit Link Totem (60312, row 6): the castable IS the talent's single rank ------------------------------------------
spirit_link_totem_202645 = _totem_summon(
    202645, 'Spirit Link Totem', 300281, SUMMON_PROPS_AIR, TARGET_DEST_CASTER_BACK_RIGHT, 6000, 180000,
    ICON_SPIRIT_LINK, 40,
    'Summons a Spirit Link Totem for $d that links the health of party and raid members within 10 yards, '
    'redistributing it evenly every 1 sec and reducing their damage taken by 10%. 3 min cooldown.',
    'Spirit Link Totem (talent 60312 rank, SLA 30700, learned at 40): Air totem, 6 s [tune], RecoveryTime 180000 (Category '
    '0; Cooldown Haste divides it), instant, GCD 1000 / 133, cost 0 ([tune], set at the balance pass), back-right of the '
    'caster like 3738. Family d0 b29 only. The totem (300281, ScriptName npc_sha_spirit_link_totem) has no passive: its '
    'AI sets the linked allies to the average health percent on placement and every SPIRIT_LINK_INTERVAL_MS and '
    'refreshes the 202664 aura on them.',
    SV_AIR_SUMMON,
)

# ---- Totemic Resonance (60313, row 7): single-rank marker ----------------------------------------------------------------
totemic_resonance_202646 = _rank(
    202646, 'Totemic Resonance', [_dummy()], ICON_TOTEMIC_RESONANCE, 45,
    _desc('Each of your active healing totems and your Water Elemental increases your healing and absorbs by 5%. '
          'Healing totems are Healing Stream, Healing Tide, Earthen Wall, the Undulating Currents Totem, Cloudburst and '
          'Spirit Link.',
          'Each healing totem and your Water Elemental also adds 30% of your Mastery to this bonus.', True),
    'Totemic Resonance (talent 60313): marker (DUMMY). Shaman::RecountTotemicResonance applies the stacking aura 202662 '
    'while this rank is known (the doc\'s capstone is always on: one rank). Counted: Healing Stream 3527, Healing Tide '
    '300282, Earthen Wall 300274, UCT 300279, Cloudburst 300280, Spirit Link 300281, the Water Elemental totem 300272.',
)

# ---- Undulating Currents Totem (60314, row 8): the castable IS the talent's single rank ------------------------------------
undulating_currents_heal_202663 = spell(
    id=202663, name='Undulating Currents', school=School.NATURE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    effects=[Effect(
        type=EffectType.HEAL, sp_potency=30.0, potency_kind='heal', time_basis_ms=2000,
        implicit_target_a=TARGET_UNIT_TARGET_CHAINHEAL_ALLY, chain_targets=3,
    )],
    spell_icon_id=ICON_CHAIN_HEAL,
    notes=NOTE + 'the Undulating Currents Totem\'s Chain Heal: Nature, 30 potency on the healing scale (T 2000, about 424 '
          'at 60 [fixed]), target type 45 (CHAINHEAL_ALLY, Chain Heal\'s own), 3 targets (primary + 2 jumps), chain '
          'amplitude 0.6 (the stock 40% falloff), SpellLevel 50 = the totem\'s learn level. Cast by the totem '
          '(npc_sha_undulating_currents_totem, no owner GUID: no shaman proc rolls) at the most injured player within '
          '40 yd; spell_sha_resto_undulating_heal (OnObjectAreaTargetSelect on target type 45) clears and rebuilds the '
          'jump list from Heal::SelectMostInjured (players only, by percent). range 50000 + AttributesEx2 0x4 as the '
          'other totem heals. Family d2 b23 (Kindling, Purification; never Healing Way, which covers CH d0 b8 only). '
          '2026-10-22 playtest fix pass (P4): SpellVisualID_1 3659 = Chain Heal 1064\'s, so the cast kit 3169 (SpellChainEffects 736) '
          'draws the beam from the casting totem to the primary and on to each jump (the client chains the beam through the SMSG_SPELL_GO '
          'target list, which follows the rebuilt jump order); the impact kit 3170 plays on every target.',
    raw_overrides=_raw(
        'Heals the target for {pot1} and jumps to 2 additional allies.', '', 50,
        DefenseType=1, PreventionType=1, AttributesEx2=ATTR2_IGNORE_LOS,
        SpellClassMask_3=m.UNDULATING_HEAL, EffectChainAmplitude_1=0.6, SpellVisualID_1=SV_CHAIN_HEAL,
    ),
)
scripted_by(undulating_currents_heal_202663, 'spell_sha_resto_undulating_heal')

undulating_currents_totem_202647 = _totem_summon(
    202647, 'Undulating Currents Totem', 300279, SUMMON_PROPS_FIRE, TARGET_DEST_CASTER_FRONT_RIGHT, 12000, 45000,
    ICON_UCT, 50,
    'Summons an Undulating Currents Totem for $d that casts Chain Heal on the most injured ally within 40 yards every '
    '2 sec, healing for ' + pot_text(undulating_currents_heal_202663, var='uct') + ' and jumping to 2 additional '
    'allies. 45 sec cooldown.',
    'Undulating Currents Totem (talent 60314 rank, SLA 30701, learned at 50): Fire totem (props 63, the Searing slot '
    'target 44), 12 s, RecoveryTime 45000 (Category 0; Cooldown Haste divides it), instant, GCD 1000 / 133, cost 0 '
    '([tune]). Family d0 b29 only. The totem (300279, ScriptName npc_sha_undulating_currents_totem) has no passive: its '
    'AI casts 202663 on placement and every UCT_INTERVAL_MS, UCT_CASTS times. Tooltip variable entry 1224 (`uct`: '
    'Kindling x Purification).',
    SV_FIRE_SUMMON, tooltip_vars=shaman_healtotems_1224,
)

# ---- Tidecaller (60315, row 8): Water Bolt heal +50/100% ------------------------------------------------------------------
def _tidecaller(spell_id: int, pct: int):
    return _rank(
        spell_id, 'Tidecaller', [_mod(SpellModOp.DAMAGE, True, pct - 1)], ICON_TIDECALLER, 50,
        f'Increases the healing done by your Water Elemental\'s Water Bolt by {pct}%.',
        f'Tidecaller rank {pct // 50}: SPELLMOD_DAMAGE pct +{pct}% (stored {pct - 1}) on the Water Bolt heal 202277 only '
        f'(d2 b24; the damage bolt is d2 b25). The guardian\'s casts take the owner\'s SpellMods (FB N14).',
        **_emask(1, (0, 0, m.WATER_BOLT_HEAL)),
    )


tidecaller_rank1_202648 = _tidecaller(202648, 50)
tidecaller_rank2_202649 = _tidecaller(202649, 100)

# ---- Kindling (60316, row 9): UCT heal +10/20%; rank 2 = the capstone marker ----------------------------------------------
_KINDLING_CAPSTONE = ('Your Chain Heal has a 15% chance to reduce the remaining cooldown of your Undulating Currents '
                      'Totem by 3 sec.')


def _kindling(spell_id: int, pct: int, last: bool):
    effects = [_mod(SpellModOp.DAMAGE, True, pct - 1)]
    if last:
        effects.append(_dummy())
    return _rank(
        spell_id, 'Kindling', effects, ICON_KINDLING, 55,
        _desc(f'Increases the healing done by your Undulating Currents Totem by {pct}%.', _KINDLING_CAPSTONE, last),
        f'Kindling rank {pct // 10}: eff1 SPELLMOD_DAMAGE pct +{pct}% (stored {pct - 1}) on the UCT heal 202663 (d2 b23).'
        + (' Rank 2 is the capstone: eff2 is the marker (DUMMY); the Chain Heal script rolls KINDLING_CHANCE and cuts the '
           'UCT cooldown by KINDLING_CDR_MS real ms.' if last else ''),
        **_emask(1, (0, 0, m.UNDULATING_HEAL)),
    )


kindling_rank1_202650 = _kindling(202650, 10, False)
kindling_rank2_202651 = _kindling(202651, 20, True)

# ---- Cloudburst Totem (60317, row 10): the castable IS the talent's single rank --------------------------------------------
cloudburst_totem_202652 = _totem_summon(
    202652, 'Cloudburst Totem', 300280, SUMMON_PROPS_AIR, TARGET_DEST_CASTER_BACK_RIGHT, 15000, 0,
    ICON_CLOUDBURST, 60,
    'Summons a Cloudburst Totem for $d that collects power from your healing. When it expires, is recalled, is replaced '
    'by another Air totem or is dismissed with Totemic Recall, it heals all injured allies within 40 yards for 30% of '
    'the effective Nature healing you did while it was active, divided evenly among them. 1 min cooldown.',
    'Cloudburst Totem (talent 60317 rank, SLA 30702, learned at 60): Air totem, 15 s, NO DBC cooldown (the script starts '
    'it at release as max(0, 60 s / (1 + CDH) - time since placement), S2a known-hard 1), instant, GCD 1000 / 133, cost 0 '
    '([tune]), back-right like 3738. Family d0 b29 only. spell_sha_resto_cloudburst: CheckCast releases the totem and '
    'returns SPELL_FAILED_DONT_REPORT when one stands (the off-GCD recall), AfterCast records the placement. The totem '
    '(300280) has no ScriptName and no passive.',
    SV_AIR_SUMMON,
)
scripted_by(cloudburst_totem_202652, 'spell_sha_resto_cloudburst')

# ---- Improved Earth Shield rank 3 (talent 2059, row 8): charges +3, healing +15%, capstone = rank-based --------------------
# Mirrors A2's 51560 / 51561: eff1 aura 107 misc 4 (SPELLMOD_CHARGES) flat on Earth Shield (d1 b10), eff2 aura 108 pct on
# the same bit. SpellInfoCorrections.cpp:911-916 forces eff2's misc to SPELLMOD_DAMAGE on 51560 / 51561 (0-verify X2);
# this row declares misc 0 itself.
improved_earth_shield_rank3_202653 = _rank(
    202653, 'Improved Earth Shield',
    [_aura(AuraType.ADD_FLAT_MODIFIER, 2, int(SpellModOp.CHARGES)), _mod(SpellModOp.DAMAGE, True, 14)],
    ICON_IES, 50,
    _desc('Increases the number of charges of your Earth Shield by 3 and the healing it does by 15%.',
          'Healing with Earth Shield grants you 1 charge of Tidal Waves. This effect can only occur once every 5 sec. '
          'Requires the final rank of Tidal Waves.', True),
    'Improved Earth Shield rank 3 (the capstone; the new rank of talent 2059): eff1 SPELLMOD_CHARGES (aura 107 misc 4) '
    'flat +3 (stored 2), eff2 SPELLMOD_DAMAGE (aura 108 misc 0, declared here, X2) pct +15% (stored 14), both on '
    'Earth Shield 974 (d1 b10). The healing flows through 974\'s own effect (379 ignores caster mods). The capstone '
    '(Tidal Waves charge, IES_TW_ICD_MS) is rank-based in spell_sha_resto_earth_shield.',
    subtext='Rank 3',
    **_emask(1, (0, EARTH_SHIELD_D1, 0)), **_emask(2, (0, EARTH_SHIELD_D1, 0)),
)

# ---- Tidal Force (talent 582, row 2): the new castable (55198 stays untouched and leaves the talent) ----------------------
tidal_force_aura_202672 = _buff(
    202672, 'Tidal Force',
    [_mod(SpellModOp.DURATION, True, 49), _mod(SpellModOp.DAMAGE_MULTIPLIER, True, 66)],
    ICON_TIDAL_FORCE, 10000, 'Your heals are empowered.',
    'Your heals are empowered for 10 sec.',
    'Tidal Force caster aura (TF_DURATION_MS 10 s; Tidal Mastery\'s capstone extends it): eff1 SPELLMOD_DURATION pct '
    '+50% (stored 49) on Healing Rain (d2 b21: the rain lasts 50% longer, one Aura carries the dynobj and the periodic dummy, X8); eff2 SPELLMOD_DAMAGE_MULTIPLIER pct stored 66 '
    '(live +67: 0.6 x 1.67 = 1.002 per jump, S2a-0VERIFY (4) 3) on Chain Heal (d0 b8) = no falloff. Visible, '
    'non-passive, no consolidation flag. Applied by spell_sha_resto_tidal_force; the Healing Wave echo / Lesser Healing '
    'Wave stack are the script\'s.',
    **_emask(1, (0, 0, m.HEALING_RAIN)), **_emask(2, CHAIN_HEAL),
)

tidal_force_castable_202654 = spell(
    id=202654, name='Tidal Force', school=School.NATURE, attributes=0, category=0,
    cast_time_ms=0, cooldown_ms=120000, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=ICON_TIDAL_FORCE,
    notes=NOTE + 'the new Tidal Force (talent 582 rank list [202654], SLA 30703; 55198 leaves the talent and every '
          'spellbook): instant, OFF the global cooldown (StartRecoveryTime / Category 0), no cost, RecoveryTime 120000 '
          '(Category 0; Cooldown Haste divides it, Tidal Mastery cuts it by SPELLMOD_COOLDOWN flat on d2 b28 '
          'TIDAL_FORCE_CAST). Effect 1 is a DUMMY on the caster: spell_sha_resto_tidal_force (OnEffectHitTarget, EFFECT_0, '
          'SPELL_EFFECT_DUMMY) applies the caster aura 202672. Family d2 b28 only.',
    raw_overrides=_raw(
        'Call upon the power of the tides to empower your heals for 10 sec. Healing Wave: heals the target again for 30% '
        'of the amount healed after 1 sec. Lesser Healing Wave: increases your healing on the target by 5% for 8 sec, '
        'stacking up to 3 times. Chain Heal: no longer loses healing with each jump. Healing Rain: lasts 50% longer. '
        '2 min cooldown.', '', 20,
        BaseLevel=20, DefenseType=1, PreventionType=1, StartRecoveryCategory=0, StartRecoveryTime=0,
        SpellClassMask_3=m.TIDAL_FORCE_CAST, SpellVisualID_1=SV_TIDAL_FORCE,
    ),
)
scripted_by(tidal_force_castable_202654, 'spell_sha_resto_tidal_force')
unbind_script(55198, 'spell_sha_tidal_force_dummy')

# =====================================================================================================================
# Buffs, heals and helpers 202660-202681
# =====================================================================================================================

# ---- Improved Healing Stream capstone: the counter and the Healing Tide party heal ----------------------------------------------
healing_tide_counter_202660 = _buff(
    202660, 'Improved Healing Stream', [_dummy()], ICON_HEALING_STREAM, -1,
    'Your Healing Stream Totems are counting toward a Healing Tide Totem.',
    'Every third Healing Stream Totem you place becomes a Healing Tide Totem.',
    'Healing Tide counter (visible, non-passive, no consolidation flag, death-persistent L5 pair): DUMMY stack holder, '
    'CumulativeAura 3 (IHS_PLACEMENTS), infinite (the count persists out of combat). spell_sha_resto_healing_stream_totem '
    '(5394) counts placements; the third resets it and swaps the summon for the Healing Tide creature.',
    level=15, stacks=3, persist=True,
)

healing_tide_party_heal_202661 = _heal(
    202661, 'Healing Tide Totem', 30.0, 2000, ICON_HEALING_STREAM, 20,
    'the Healing Tide Totem\'s heal in a 5-player party: Nature, 30 potency on the healing scale (T 2000, about 424 at '
    '60; the doc\'s +50% over Healing Stream\'s 20), d0 b13 (the Healing Stream heal bit: Improved Healing Stream '
    'reaches it). Cast by the 5672 passive branch of the Tide creature (caster = the totem, no owner GUID: no shaman '
    'proc rolls; it can crit) on the 10 most injured players when the owner is in a 5-player party (not a raid); a raid '
    'uses 202271 (20). SpellLevel 20 = Healing Stream\'s.',
    'Heals the target for {pot1}.',
    SpellClassMask_1=m.HEALING_STREAM_HEAL,
)

# ---- Totemic Resonance: the stacking aura (visible; the count is the stack) -------------------------------------------------------
totemic_resonance_aura_202662 = _buff(
    202662, 'Totemic Resonance',
    [_aura(AuraType.MOD_HEALING_DONE_PERCENT, 4, 0), _aura(AuraType.PERIODIC_DUMMY, 0, amplitude=1000)],
    ICON_TOTEMIC_RESONANCE, -1,
    'Your healing totems are increasing your healing and absorbs.',
    'Each active healing totem increases your healing and absorbs.',
    'Totemic Resonance stacking aura (visible, non-passive, no consolidation flag, no family bits, ATTR0 0x80000000: '
    'cannot be right-click cancelled, S2a review m3): eff1 '
    'MOD_HEALING_DONE_PERCENT (aura 136) placeholder +5% per stack (stored 4); the script sets the live per-stack '
    'amount to 5 + 0.3 x Mastery. eff2 PERIODIC_DUMMY every TR_REFRESH_MS (the live Mastery refresh, Empowerment '
    'precedent). CumulativeAura 4 (TR_MAX_COUNT); the stack count is the number of counted totems, maintained by '
    'Shaman::RecountTotemicResonance. Heals over time read the aura live per tick (S2a-0VERIFY X1); the Earthen Wall / '
    'Bulwark absorbs and the Water Bolt heal multiply it in themselves.',
    level=45, stacks=4, no_cancel=True,
)
scripted_by(totemic_resonance_aura_202662, 'spell_sha_resto_totemic_resonance')

# ---- Spirit Link: the ally aura ----------------------------------------------------------------------------------------------------
spirit_link_aura_202664 = _buff(
    202664, 'Spirit Link',
    [_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, -11, SCHOOL_ALL, target=TARGET_UNIT_TARGET_ALLY)],
    ICON_SPIRIT_LINK, 2000,
    'Linked to nearby allies. Damage taken reduced.',
    'Linked to nearby allies, reducing damage taken by 10%.',
    'Spirit Link ally aura: aura 87 all schools -10% (stored -11) [tune], 2 s, re-applied every SPIRIT_LINK_INTERVAL_MS by '
    'npc_sha_spirit_link_totem on every player within SPIRIT_LINK_RADIUS_YD (a refresh, so it lasts as long as the totem '
    'plus the last interval). Visible, non-passive, no consolidation flag. range 50000 + AttributesEx2 0x4: the totem '
    'casts it at allies. No family bits.',
    level=40, family=False, range_yards=50000.0, AttributesEx2=ATTR2_IGNORE_LOS,
)

# ---- Cloudburst: the store buff (a proc aura) and the release heal ----------------------------------------------------------
cloudburst_store_202665 = _buff(
    202665, 'Cloudburst Totem', [_dummy()], ICON_CLOUDBURST, -1,
    'Your Cloudburst Totem is storing healing.',
    'Your Cloudburst Totem is storing 30% of your effective Nature healing.',
    'Cloudburst store buff (visible, non-passive, no consolidation flag, no family bits, ATTR0 0x80000000: cannot be '
    'right-click cancelled, S2a review m3): DUMMY proc aura, infinite (the '
    'totem\'s removal removes it; the script releases or discards on the remove mode). spell_proc below: own positive '
    'magic casts and periodic ticks, HIT phase, heal type, Nature school, 100%; spell_sha_resto_cloudburst_store stores '
    'CLOUDBURST_STORE_PCT of the effective heal (skips the release id). Totem and guardian heals are stored by the '
    'UnitScript::OnHeal hook (A13).',
    level=60, family=False, no_cancel=True,
)
procs_on(
    cloudburst_store_202665, proc_flags=PROC_FLAG_DONE_MAGIC_POS | PROC_FLAG_DONE_PERIODIC, school_mask=8,
    spell_type_mask=TYPE_HEAL, spell_phase_mask=PHASE_HIT, chance=100,
    attributes_mask=PROC_ATTR_TRIGGERED_CAN_PROC,   # Healing Rain pulses, Rip Current copy, Earth Shield heals are triggered
)
scripted_by(cloudburst_store_202665, 'spell_sha_resto_cloudburst_store')

cloudburst_release_202666 = spell(
    id=202666, name='Cloudburst', school=School.NATURE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    effects=[Effect(
        type=EffectType.HEAL, implicit_target_a=TARGET_UNIT_TARGET_ALLY,
        potency_excluded='script-sized: the stored amount divided by the number of injured allies is passed as the '
                         'base points by Shaman::ReleaseCloudburst (S2a brief, Cloudburst release).',
    )],
    spell_icon_id=ICON_CLOUDBURST,
    notes=NOTE + 'the Cloudburst release heal: script-sized (potency_excluded), no family (SpellClassSet 0, no bits: no '
          'Purification, no Totemic Resonance, not reached by the Tidal Force stack\'s all-zero family-11 mask), '
          'AttributesEx3 IGNORE_CASTER_MODIFIERS + AttributesEx2 CANT_CRIT (the doc: "takes no modifiers: no '
          'Purification, no Totemic Resonance, no crit"), SUPPRESS_CASTER_PROCS (rolls nothing, is never stored again). '
          'Cast from the owner with its own id, once per injured player within CLOUDBURST_RADIUS_YD of the totem. range '
          '50000 + AttributesEx2 0x4 (the totem may be gone).',
    raw_overrides=_raw(
        'Heals the target.', '', 60, family=False, DefenseType=1, PreventionType=1,
        AttributesEx2=ATTR2_IGNORE_LOS | ATTR2_CANT_CRIT,
        AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS | ATTR3_SUPPRESS_CASTER_PROCS,
    ),
)

# ---- Torrent heal (Healing Rain's Riptide torrent; Restoration owns it) ---------------------------------------------------------
torrent_heal_202667 = _heal(
    202667, 'Torrent', 10.0, 1500, ICON_RIPTIDE, 30,
    'the Healing Rain torrent (shared doc "Healing Rain"; replaces the 10-potency placeholder DUMMY, effect 3 of '
    '202283): Nature, 10 potency per target on the healing scale (T 1500, about 106 at 60), d2 b22 (Torrent, Healing '
    'Way, Purification, Tidal Mastery crit reach it). Cast triggered by the Riptide script at up to 5 most injured '
    'players in the shaman\'s own rain; AttributesEx3 SUPPRESS_CASTER_PROCS (it rolls none of the shaman\'s procs). '
    'SpellLevel 30 = Healing Rain\'s learn level.',
    'Heals the target for {pot1}.',
    SpellClassMask_3=m.TORRENT, AttributesEx3=ATTR3_SUPPRESS_CASTER_PROCS,
)

# ---- Rainfall capstone buff: the next Healing Rain is instant -------------------------------------------------------------------
rainfall_buff_202668 = _buff(
    202668, 'Rainfall', [_mod(SpellModOp.CASTING_TIME, True, -101)], ICON_RAINFALL, 20000,
    'Your next Healing Rain is instant.',
    'Your next Healing Rain within 20 sec is instant.',
    'Rainfall buff: SPELLMOD_CASTING_TIME pct -100% (stored -101) on Healing Rain (d2 b21), ProcCharges 1, 20 s '
    '(refreshes, never stacks). Consumed by the Healing Rain cast through the REQ_SPELLMOD row below (CAST phase, '
    'positive and negative magic casts so the rain\'s class is not a trap).',
    charges=1, level=35, **_emask(1, (0, 0, m.HEALING_RAIN)),
)
procs_on(
    rainfall_buff_202668, proc_flags=PROC_FLAG_DONE_MAGIC_POS | PROC_FLAG_DONE_MAGIC_NEG, family_name=SPELLFAMILY_SHAMAN,
    family_mask=(0, 0, m.HEALING_RAIN), spell_type_mask=TYPE_ALL, spell_phase_mask=PHASE_CAST,
    attributes_mask=PROC_ATTR_REQ_SPELLMOD, chance=100, charges=1,
)

# ---- Tidal Waves buff (new id: 53390 has forced charges and a d1 b26 collision) --------------------------------------------------
tidal_waves_buff_202669 = _buff(
    202669, 'Tidal Waves',
    [_mod(SpellModOp.CASTING_TIME, True, -11), _mod(SpellModOp.CRITICAL_CHANCE, False, 9)],
    ICON_TIDAL_WAVES, 15000,
    'Your Healing Wave casts faster and your Lesser Healing Wave is more likely to critically hit.',
    'Your Healing Wave casts faster and your Lesser Healing Wave is more likely to critically hit.',
    'Tidal Waves buff: CumulativeAura 3 (TIDAL_WAVES_MAX), 15 s (TIDAL_WAVES_DURATION_MS), no ProcCharges and no '
    'spell_proc (the scripts grant, read all stacks at cast and drop one in AfterCast). Per stack: eff1 '
    'SPELLMOD_CASTING_TIME pct -10% (stored -11) on Healing Wave (d0 b6), eff2 SPELLMOD_CRITICAL_CHANCE flat +10 (stored '
    '9) on Lesser Healing Wave (d0 b7); the engine multiplies both by the stack count. Does not survive death. No '
    'family bits on the buff itself.',
    stacks=3, level=55, **_emask(1, HEALING_WAVE), **_emask(2, LESSER_HEALING_WAVE),
)

undulation_counter_202670 = _buff(
    202670, 'Undulation', [_dummy()], ICON_TIDAL_WAVES, -1,
    'Counting toward a stronger Healing Wave or Lesser Healing Wave.',
    'Every third Healing Wave or Lesser Healing Wave you cast heals for 50% more.',
    'Undulation counter (visible, non-passive, no consolidation flag, death-persistent L5 pair): DUMMY stack holder, '
    'CumulativeAura 3 (UNDULATION_CASTS), infinite (the count persists through combat changes). The Healing Wave / '
    'Lesser Healing Wave script adds a stack per cast; on the third it clears the buff and raises that cast by '
    'UNDULATION_BONUS_PCT.',
    stacks=3, level=55, persist=True,
)

improved_chain_heal_buff_202671 = _buff(
    202671, 'Improved Chain Heal', [_dummy()], ICON_CHAIN_HEAL, -1,
    'Your next Chain Heal does not consume Riptide.',
    'Your next Chain Heal does not consume Riptide.',
    'Improved Chain Heal capstone buff (visible, non-passive, no consolidation flag): DUMMY holder, infinite (consumed '
    'by the Chain Heal that uses it, which still gets Riptide\'s +25%). Granted when ICH_CHARGES_NEEDED Tidal Waves '
    'charges have been consumed; the count is script state.',
    level=45,
)

# ---- Tidal Force: the LHW stack on the ally and the HW echo -----------------------------------------------------------------------
tidal_force_stack_202673 = _buff(
    202673, 'Tidal Force', [_aura(AuraType.MOD_HEALING_RECEIVED, 4, 0, target=TARGET_UNIT_TARGET_ALLY)],
    ICON_LESSER_HEALING_WAVE, 8000,
    'Healing received from the shaman increased.',
    'Healing received from the shaman increased by 5%.',
    'Tidal Force Lesser Healing Wave stack on the ally: aura 283 (MOD_HEALING_RECEIVED), stored 4 = +5% per stack, '
    'CumulativeAura 3 (TF_STACK_MAX), 8 s. SpellClassSet 11 with an all-zero effect mask = every shaman-family heal of '
    'THIS caster (direct and ticks); the engine scopes it to the aura caster, so totem / guardian heals never gain it '
    '(S2a-0VERIFY (4) 7). Visible, non-passive, no consolidation flag. Cast by spell_sha_resto_healing_wave on the '
    'Lesser Healing Wave target; range 50000 + AttributesEx2 0x4.',
    stacks=3, level=20, range_yards=50000.0, AttributesEx2=ATTR2_IGNORE_LOS,
    AttributesEx3=ATTR3_DOT_STACKING_RULE,   # S2a WP-R L3: two shamans' stacks must not replace each other
)

tidal_force_echo_202674 = spell(
    id=202674, name='Tidal Force', school=School.NATURE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    effects=[Effect(
        type=EffectType.HEAL, implicit_target_a=TARGET_UNIT_TARGET_ALLY,
        potency_excluded='script-sized: TF_ECHO_PCT of the Healing Wave heal it echoes is passed as the base points by '
                         'spell_sha_resto_healing_wave (the amount already carries every modifier).',
    )],
    spell_icon_id=ICON_HEALING_WAVE,
    notes=NOTE + 'the Healing Wave echo (Tidal Force): a triggered heal of TF_ECHO_PCT of the amount healed after '
          'TF_ECHO_DELAY_MS, script-sized (potency_excluded). SpellClassSet 0 (the Tidal Force stack\'s all-zero mask and '
          'every class mod stay off it), AttributesEx3 IGNORE_CASTER_MODIFIERS + SUPPRESS_CASTER_PROCS (rolls nothing, '
          'does not count as a Healing Wave cast for Undulation), AttributesEx2 CANT_CRIT (30% of an amount that '
          'already crit or not) + IGNORE_LOS (the ally may have moved).',
    raw_overrides=_raw(
        'Heals the target.', '', 20, family=False, DefenseType=1, PreventionType=1,
        AttributesEx2=ATTR2_IGNORE_LOS | ATTR2_CANT_CRIT,
        AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS | ATTR3_SUPPRESS_CASTER_PROCS,
    ),
)

# ---- Nature's Guardian capstone: the heal and the guaranteed-crit buff ------------------------------------------------------------
natures_guardian_heal_202675 = _heal(
    202675, 'Nature\'s Guardian', 100.0, 1500, ICON_NATURES_GUARDIAN, 40,
    'the Nature\'s Guardian capstone heal (3C Q4): Nature, 100 potency on the healing scale (T 1500, about 1,059 at 60 '
    '[tune]), self-cast by spell_sha_resto_nature_guardian (plain CastSpell, so potency applies and it can crit). Family '
    'd2 b27 (MINOR_HEAL: Purification reaches it). SpellLevel 40 = the talent row\'s.',
    'Heals you for {pot1}.',
    target=TARGET_UNIT_CASTER, SpellClassMask_3=m.MINOR_HEAL,
)

natures_guardian_crit_202676 = _buff(
    202676, 'Nature\'s Guardian', [_mod(SpellModOp.CRITICAL_CHANCE, False, 99)], ICON_NATURES_GUARDIAN, 30000,
    'Your next Nature spell is a critical strike.',
    'Your next Nature spell within 30 sec is a guaranteed critical strike.',
    'Nature\'s Guardian crit buff: flat SPELLMOD_CRITICAL_CHANCE +100 (stored 99) on the shaman\'s own Nature casts with '
    'a direct hit (NG_CRIT_MASK: LB, CL, Earth Shock, Healing Wave, Lesser Healing Wave, Chain Heal, Riptide; not Healing '
    'Rain, Earthquake, the other schools or totem heals), ProcCharges 1, 30 s [tune] (the doc gives no duration; = the '
    'capstone\'s ICD so it cannot outlive its refire). Consumed on the HIT phase by the row below (positive and negative '
    'magic casts).',
    charges=1, level=40, **_emask(1, NG_CRIT_MASK),
)
procs_on(
    natures_guardian_crit_202676, proc_flags=PROC_FLAG_DONE_MAGIC_POS | PROC_FLAG_DONE_MAGIC_NEG,
    family_name=SPELLFAMILY_SHAMAN, family_mask=NG_CRIT_MASK, spell_type_mask=TYPE_ALL, spell_phase_mask=PHASE_HIT,
    attributes_mask=PROC_ATTR_REQ_SPELLMOD, chance=100, charges=1,
)

# ---- Totemic Focus capstone: the placement heal -----------------------------------------------------------------------------------
totemic_focus_heal_202677 = _heal(
    202677, 'Totemic Focus', 5.0, 1500, ICON_TOTEMIC_FOCUS, 10,
    'the Totemic Focus capstone heal: Nature, 5 potency per target on the healing scale (T 1500, about 53 at 60 '
    '[fixed]), cast by the placed totem 1 ms after the placement (TOTEMIC_FOCUS_DELAY_MS) at up to TOTEMIC_FOCUS_TARGETS '
    'injured players within TOTEMIC_FOCUS_RADIUS_YD (Heal::SelectMostInjured, players only). Caster = the totem (no '
    'owner GUID, no shaman proc). Family d2 b27 (MINOR_HEAL: Purification reaches it). SpellLevel 10 = the talent row\'s.',
    'Heals the target for {pot1}.',
    SpellClassMask_3=m.MINOR_HEAL,
)

# ---- Earthen Bulwark: the splash shield ---------------------------------------------------------------------------------------------
earthen_bulwark_shield_202678 = spell(
    id=202678, name='Earthen Bulwark', school=School.NATURE, dispel=DispelType.MAGIC, attributes=0, category=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    duration_ms=6000,
    effects=[Effect(
        type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=SCHOOL_ALL,
        implicit_target_a=TARGET_UNIT_TARGET_ALLY,
        potency_excluded='script-sized: BULWARK_PCT of the main Earthen Wall shield (Shaman::GetEarthenWallAbsorb, which '
                         'already carries Totemic Resonance) is set as the amount by npc_sha_earthen_wall_totem.',
    )],
    spell_icon_id=ICON_BULWARK,
    notes=NOTE + 'Earthen Bulwark\'s shield on every other ally within BULWARK_RADIUS_YD of the totem: every-school absorb, '
          '6 s (refreshed to full on each pulse), amount set by the totem AI (potency_excluded). Visible, non-passive, no '
          'consolidation flag. NO family (SpellClassSet 0, no d1 b5 / b10, d0 b10 / d2 b15: the main shield owns d2 b15 '
          'and Earthen Wall talents must not double-apply). AttributesEx3 0x80 = stacks per caster as the main shield. '
          'range 50000 + AttributesEx2 0x4 as 202262.',
    raw_overrides=_raw(
        'Absorbs damage for $d.', 'A stone barrier absorbs damage.', 20, family=False,
        AttributesEx2=ATTR2_IGNORE_LOS, AttributesEx3=ATTR3_DOT_STACKING_RULE,
    ),
)

# ---- Tidal Focus capstone: the cleanse helper --------------------------------------------------------------------------------------
tidal_focus_cleanse_202679 = spell(
    id=202679, name='Tidal Focus', school=School.NATURE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    effects=[
        Effect(type=EffectType.DISPEL, base_points=1,
               misc_value=int(DispelType.DISEASE), implicit_target_a=TARGET_UNIT_TARGET_ALLY),
        Effect(type=EffectType.DISPEL, base_points=1, misc_value=int(DispelType.POISON),
               implicit_target_a=TARGET_UNIT_TARGET_ALLY),
    ],
    spell_icon_id=ICON_TIDAL_FOCUS,
    notes=NOTE + 'the Tidal Focus capstone cleanse (Q14): eff1 DISPEL disease x2 (stored 1), eff2 DISPEL poison x2 (stored '
          '1) = TIDAL_FOCUS_CLEANSE_COUNT each; cast triggered by spell_sha_resto_cleansing_totem (AfterCast of 8170) '
          'from the shaman at every party member within TIDAL_FOCUS_CLEANSE_RADIUS_YD of the placed totem, on top of the '
          'totem\'s own first pulse. No family bits. range 50000 + AttributesEx2 0x4.',
    raw_overrides=_raw(
        'Removes up to 2 disease effects and up to 2 poison effects from the target.', '', 20, family=False,
        DefenseType=1, PreventionType=1, AttributesEx2=ATTR2_IGNORE_LOS,
    ),
)

# ---- Improved Water Shield capstone: the energize ----------------------------------------------------------------------------------
water_shield_energize_202680 = spell(
    id=202680, name='Improved Water Shield', school=School.NATURE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    effects=[Effect(type=EffectType.ENERGIZE_PCT, base_points=0, misc_value=0, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=ICON_WATER_SHIELD,
    notes=NOTE + 'the Improved Water Shield capstone energize: ENERGIZE_PCT (137) mana, 1% of maximum mana '
          '(IWS_CAPSTONE_MANA_PCT; stored 0). Cast triggered at the caster by spell_sha_resto_imp_water_shield, once per '
          'cast, on a direct-heal critical strike. AttributesEx3 SUPPRESS_CASTER_PROCS (cannot proc itself or others). '
          'No family bits.',
    raw_overrides=_raw(
        'Restores 1% of your maximum mana.', '', 10, family=False,
        AttributesEx3=ATTR3_SUPPRESS_CASTER_PROCS,
    ),
)

# ---- Mana Tide Totem: the visible party aura ---------------------------------------------------------------------------------------
mana_tide_party_aura_202681 = _buff(
    202681, 'Mana Tide Totem', [_dummy()], ICON_MANA_TIDE, 10000,
    'Mana restored over time.',
    'Mana restored over time while the Mana Tide Totem stands.',
    'Mana Tide party aura (visible, non-passive, no consolidation flag): DUMMY holder on each party member in range, '
    '10 s = the totem\'s duration, applied by spell_sha_resto_mana_tide_totem (39610) with the pulse (the mana itself '
    'is the script\'s: MANA_TIDE_PARTY_PCT_X10 / MANA_TIDE_SELF_PCT). range 50000 + AttributesEx2 0x4. No family bits.',
    level=40, family=False, range_yards=50000.0, AttributesEx2=ATTR2_IGNORE_LOS,
)


# =====================================================================================================================
# Creatures 300279-300282: four Totem entries (every one a real Totem, summoned with SummonProperties 63 / 82 / 83)
# =====================================================================================================================
_TOTEM_COLUMNS = dict(
    minlevel=1, maxlevel=80, faction=58, speed_walk=1.0, speed_run=1.0, speed_swim=1.0, speed_flight=1.0,
    DamageModifier=1.0, ManaModifier=1.0, ArmorModifier=1.0, ExperienceModifier=1.0, RegenHealth=1,
    BaseAttackTime=2000, RangeAttackTime=2000, BaseVariance=1.0, RangeVariance=1.0, HoverHeight=1.0,
    unit_flags=0, unit_flags2=2048, type=11, flags_extra=0, detection_range=18.0, unit_class=1, HealthModifier=0.05,
)

# Undulating Currents: Wrath of Air / Healing Stream's columns; m_spells[0] empty, driven by its own UpdateAI.
undulating_currents_totem_300279 = creature_template(
    300279, 'Undulating Currents Totem', ScriptName='npc_sha_undulating_currents_totem', **_TOTEM_COLUMNS,
)
creature_model(300279, display_id=DISPLAY_FIRE_TOTEM)

# Cloudburst: no AI and no passive; the hooks and the store aura drive it.
cloudburst_totem_300280 = creature_template(
    300280, 'Cloudburst Totem', ScriptName='', **_TOTEM_COLUMNS,
)
creature_model(300280, display_id=DISPLAY_AIR_TOTEM)

# Spirit Link: m_spells[0] empty, driven by its own UpdateAI.
spirit_link_totem_300281 = creature_template(
    300281, 'Spirit Link Totem', ScriptName='npc_sha_spirit_link_totem', **_TOTEM_COLUMNS,
)
creature_model(300281, display_id=DISPLAY_AIR_TOTEM)

# Healing Tide: Healing Stream 3527's columns; Index 0 = the Healing Stream passive 5672 (spell_sha_healing_stream_passive
# branches on the totem entry), without which its heal loop never starts (S2a-0VERIFY X12).
healing_tide_totem_300282 = creature_template(
    300282, 'Healing Tide Totem', ScriptName='', **_TOTEM_COLUMNS,
)
creature_model(300282, display_id=DISPLAY_WATER_TOTEM)
creature_spell(300282, 0, 5672)

# =====================================================================================================================
# Spellbook entries (talent-granted castables: the shaman tabs carry no skill_line, so the rows are standalone, as
# Call of the Elements 30690)
# =====================================================================================================================
skill_line_ability(id=30700, skill_line=SKILL_LINE_RESTORATION, spell_id=spirit_link_totem_202645.id,
                   class_mask=CLASS_MASK_SHAMAN, acquire_method=0)
skill_line_ability(id=30701, skill_line=SKILL_LINE_RESTORATION, spell_id=undulating_currents_totem_202647.id,
                   class_mask=CLASS_MASK_SHAMAN, acquire_method=0)
skill_line_ability(id=30702, skill_line=SKILL_LINE_RESTORATION, spell_id=cloudburst_totem_202652.id,
                   class_mask=CLASS_MASK_SHAMAN, acquire_method=0)
skill_line_ability(id=30703, skill_line=SKILL_LINE_RESTORATION, spell_id=tidal_force_castable_202654.id,
                   class_mask=CLASS_MASK_SHAMAN, acquire_method=0)
