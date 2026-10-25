"""
Death Knight - S2a Frost: new rows 203270-203307 (Runic Attenuation, Glacial Advance + eruption, Gravefrost, Koltira's
Favor, Pillar of Frost, Unleashed Frenzy + buffs, Toravon's Whiteout + buff, Final Roar + burst, Obliteration + rune
helper, Rage of the Frozen Champion + energize, Enduring Strength, Seal of Necrofantasia, Frostwyrm's Wrath + energize
+ ramp, Breath of Sindragosa + tick) and the S2 script numbers (`_C` block at the end). Owner: A3.
Source of truth: docs/reworks/death-knight-frost-rework.md, S2-HANDOFF sections 2-5 (U8-U12, U19, U20, U23, U25),
S2a-WP-BRIEF (D1-D17, section 4 field contracts) and S2a-0VERIFY (items 4, 8, 12, 16).

SkillLineAbility rows 30750-30752 (Glacial Advance, Pillar of Frost, Breath of Sindragosa) and the talent rows come from
granted_by_talent in deathknight_talents.py (A1); this file only provides the castable spells. Talent rank spells are
hidden passives (attributes 0x1D0, Blood's talent-passive shape); a rank's SpellLevel is 9 + 5 x talent row + rank.
Visible buffs are non-passive, carry no Consolidated Buffs flag and have number-free aura texts. Variable names fix the
generated DeathKnightData header names: never rename a variable.
"""

from lib.dsl import AuraType, Effect, EffectType, PowerType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import bonus_coefficients, const, custom_attr, pot_text, procs_on, scripted_by, spell

from . import _masks as m

# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h) ----
_ATTR0_TALENT_PASSIVE = 464                         # ABILITY 0x10 | PASSIVE 0x40 | DO_NOT_DISPLAY 0x80 | NO_LOG 0x100
_ATTR0_PILLAR = 262160                              # stock Unbreakable Armor 51271: ABILITY 0x10 | NO_SHEATH 0x40000
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
_CU_AURA_CANNOT_BE_SAVED = 0x01000000               # SpellCustomAttributes (SpellInfo.h:201)
_SPELLFAMILY_DEATHKNIGHT = 15

# ---- Effects / misc values / targets (SharedDefines.h) ----
_EFFECT_ACTIVATE_RUNE = 146                         # SPELL_EFFECT_ACTIVATE_RUNE (not in the DSL enum)
_STAT_STRENGTH = 0
_SCHOOL_FROST = 16                                  # EffectMiscValue school mask of MOD_DAMAGE_PERCENT_DONE
_POWER_RUNIC_POWER = 6
_RUNE_FROST = 2                                     # RuneType of ACTIVATE_RUNE's MiscValue
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_DEST_AREA_ENEMY = 16
_TARGET_DEST_DEST = 87
_TARGET_UNIT_CONE_ENEMY_104 = 104                   # D2: a 104 degree total arc (Wake of Ashes), not the 24 degree _24

# ---- spell_proc masks (src/server/game/Spells/SpellMgr.h) ----
_PROC_FLAG_DONE_MELEE_AUTO_ATTACK = 0x4
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x10
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x4000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x10000
_PROC_SPELL_TYPE_ALL = 0x7
_PROC_SPELL_PHASE_CAST = 0x1
# A CAST-phase proc on a magic-class cast: hostile spells (Howling Blast) carry NEG, a self-target DUMMY cast (Glacial
# Advance) may be classed positive, so the row lists both (the family mask is what scopes it); melee-class strikes 0x10.
_PROC_CAST_STRIKE_AND_MAGIC = (
    _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS | _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS
    | _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG
)

# ---- Stock icons / visuals (S2-HANDOFF section 4, S2a-0VERIFY item 4) ----
_ICON_RUNIC_ATTENUATION = 3830
_ICON_GLACIAL_ADVANCE = 35
_ICON_GRAVEFROST = 55
_ICON_KOLTIRAS_FAVOR = 3925
_ICON_PILLAR_OF_FROST = 2703
_ICON_UNLEASHED_FRENZY = 2021
_ICON_TORAVONS_WHITEOUT = 2133
_ICON_FINAL_ROAR = 1700
_ICON_OBLITERATION = 4157                           # not 2639: Obliterate and Might of Mograine use it
_ICON_RAGE_OF_THE_FROZEN_CHAMPION = 2162
_ICON_ENDURING_STRENGTH = 200
_ICON_SEAL_OF_NECROFANTASIA = 2719
_ICON_FROSTWYRMS_WRATH = 3752
_ICON_BREATH_OF_SINDRAGOSA = 193
_SV_PILLAR = 44                                     # stock Unbreakable Armor's visual
_SV_GLACIAL_ERUPTION = 14011                        # Anub'arak's Impale spikes (14013 is earth)
_SV_SINDRAGOSA_BREATH = 14711                       # Sindragosa's Frost Breath (69649)

# ---- Talent rows (S2-HANDOFF section 3): a rank spell's SpellLevel = 9 + 5 x row + rank ----
_ROW_RUNIC_ATTENUATION = 1
_ROW_GLACIAL_ADVANCE = 4
_ROW_GRAVEFROST = 4
_ROW_KOLTIRAS_FAVOR = 5
_ROW_PILLAR_OF_FROST = 6
_ROW_UNLEASHED_FRENZY = 6
_ROW_TORAVONS_WHITEOUT = 7
_ROW_FINAL_ROAR = 7
_ROW_OBLITERATION = 8
_ROW_RAGE_OF_THE_FROZEN_CHAMPION = 8
_ROW_ENDURING_STRENGTH = 9
_ROW_SEAL_OF_NECROFANTASIA = 9
_ROW_FROSTWYRMS_WRATH = 9
_ROW_BREATH_OF_SINDRAGOSA = 10


def _rank_level(row, rank):
    return 9 + 5 * row + rank


def _capstone_text(text, capstone, last):
    """Capstone line under the rank text: grey below the last rank, plain on the last (S1 style)."""
    if last:
        return f'{text}\n\nCapstone: {capstone}'
    return f'{text}\n\n|cFF9D9D9DCapstone: {capstone}|r'


def _raw(description, aura_description=None, level=0, gcd=False, magic=False, **extra):
    """The per-spell defaults of every row below, plus `extra` raw columns (applied last)."""
    raw = {
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'RuneCostID': 0,
        'ProcChance': 101, 'SpellLevel': level,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
        'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': description,
        'AuraDescription_Lang_Mask': 16712188 if aura_description is None else 16712190,
    }
    if aura_description is not None:
        raw['AuraDescription_Lang_enUS'] = aura_description
    if gcd:
        raw['StartRecoveryCategory'] = 133
        raw['StartRecoveryTime'] = 1500
    if magic:
        raw['DefenseType'] = 1
        raw['PreventionType'] = 1
    raw.update(extra)
    return raw


def _chain_amplitudes(effects):
    return {f'EffectChainAmplitude_{i}': 1.0 for i in range(1, len(effects) + 1)}


def _masks_raw(masks):
    """`masks` maps a 1-based effect index to its (d0, d1, d2) EffectSpellClassMask triple (letter = effect, number =
    dword)."""
    raw = {}
    for effect_index, triple in (masks or {}).items():
        for dword, value in enumerate(triple, start=1):
            if value:
                raw[f'EffectSpellClassMask{"ABC"[effect_index - 1]}_{dword}'] = value
    return raw


def _passive_rank(spell_id, name, effects, icon, row, rank, description, note, masks=None, proc_chance=None):
    """A talent rank spell: hidden passive (attributes 0x1D0), duration -1, self range, family 15."""
    raw = _raw(
        description, level=_rank_level(row, rank), ProcChance=101 if proc_chance is None else proc_chance,
        **_chain_amplitudes(effects), **_masks_raw(masks),
    )
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_TALENT_PASSIVE,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=-1, effects=effects, spell_icon_id=icon, notes=note, raw_overrides=raw,
    )


def _helper(spell_id, name, effects, icon, description, note, school=School.NORMAL, **extra):
    """A hidden script / proc helper cast triggered on the caster: instant, self range, no cost, no GCD."""
    return spell(
        id=spell_id, name=name, school=school, attributes=0, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0, effects=effects, spell_icon_id=icon,
        notes=note, raw_overrides=_raw(description, **_chain_amplitudes(effects), **extra),
    )


def _buff(spell_id, name, effects, icon, duration_ms, description, aura_description, note, stacks=0, **extra):
    """A visible self buff: non-passive, no Consolidated Buffs flag, number-free aura text (custom-spells.md)."""
    raw = _raw(description, aura_description, **_chain_amplitudes(effects), **extra)
    if stacks:
        raw['CumulativeAura'] = stacks
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=effects, spell_icon_id=icon, notes=note, raw_overrides=raw,
    )


def _aura(apply_aura, base_points=0, misc_value=0, trigger_spell=0):
    """An APPLY_AURA effect on the caster."""
    return Effect(type=EffectType.APPLY_AURA, base_points=base_points, implicit_target_a=_TARGET_UNIT_CASTER,
                  apply_aura=apply_aura, misc_value=misc_value, trigger_spell=trigger_spell)


def _dummy_aura(base_points=0):
    return _aura(AuraType.DUMMY, base_points)


# =====================================================================================================================
# Runic Attenuation (203270-203271, talent 60345, row 1): auto attacks generate 3 Runic Power, doubled with a two-hander
# =====================================================================================================================

_RUNIC_ATTENUATION_NOTE = (
    'death-knight-rework S2a, Frost doc "Runic Attenuation" (1,3): hidden passive, eff0 PROC_TRIGGER_SPELL_WITH_VALUE '
    '(231) -> 203272 with the value 3 RP passed as the aura amount (stored 29 = 3.0 RP, RP x10). Chain spell_proc row '
    '(procs_on -203270): DONE melee auto attack only (either hand), Chance 0 = the rank\'s ProcChance 25 / 50, which '
    'is '
    'the two-hander value; spell_dk_runic_attenuation halves it for anything but a two-handed weapon (12.5 / 25%, '
    'tooltip 12 / 25%). SpellPhaseMask is 0 on purpose: an auto-attack-only ProcFlags row with a phase mask logs '
    '"SpellPhaseMask ... won\'t be used" at boot (SpellMgr.cpp:2116). SpellLevel 9 + 5 x row 1 + rank.'
)
runic_attenuation_203270 = _passive_rank(
    203270, 'Runic Attenuation',
    [_aura(AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, base_points=29, trigger_spell=203272)],
    _ICON_RUNIC_ATTENUATION, _ROW_RUNIC_ATTENUATION, 1,
    'Your auto attacks have a 12% chance to generate 3 Runic Power. The chance is doubled while you wield a '
    'two-handed weapon.',
    _RUNIC_ATTENUATION_NOTE, proc_chance=25,
)
runic_attenuation_203271 = _passive_rank(
    203271, 'Runic Attenuation',
    [_aura(AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, base_points=29, trigger_spell=203272)],
    _ICON_RUNIC_ATTENUATION, _ROW_RUNIC_ATTENUATION, 2,
    'Your auto attacks have a 25% chance to generate 3 Runic Power. The chance is doubled while you wield a '
    'two-handed weapon.',
    _RUNIC_ATTENUATION_NOTE, proc_chance=50,
)
procs_on(-203270, proc_flags=_PROC_FLAG_DONE_MELEE_AUTO_ATTACK, chance=0.0)
scripted_by(-203270, 'spell_dk_runic_attenuation')

# The energize: the aura passes the amount (value 3 RP = stored 29); the data value is the same so a plain cast also
# pays 3.
runic_attenuation_energize_203272 = _helper(
    203272, 'Runic Attenuation',
    [Effect(type=EffectType.ENERGIZE, base_points=29, implicit_target_a=_TARGET_UNIT_CASTER,
            misc_value=_POWER_RUNIC_POWER)],
    _ICON_RUNIC_ATTENUATION, 'Generates 3 Runic Power.',
    'death-knight-rework S2a (U19): the Runic Attenuation energize, ENERGIZE Runic Power (misc 6) stored 29 = 3 RP '
    '(RP x10) '
    'on the caster (implicit target 1: the proc may carry no victim). Cast triggered by the 231 aura of 203270 / '
    '203271. '
    'No cost, no family bits, SpellLevel 0.',
)

# =====================================================================================================================
# Glacial Advance (203273, talent 60346, row 4) and Glacial Eruption (203274): travelling spikes along the facing
# =====================================================================================================================

# The eruption: one spike, cast triggered by spell_dk_glacial_advance's scheduled events at a snapped ground point.
# 52 AP potency (S2 TUNE 2026-10-25, U33; was 75) direct (time basis 1500, L2), Frost, magic class, 3 yd around the point, one hit per enemy per cast
# (spell_dk_glacial_eruption), visual 14011. d2 b9 (GLACIAL_ADVANCE) so Runic Focus, Razorice and the Frost readers
# see it.
# SUPPRESS_CASTER_PROCS: the eruptions roll no procs (the cast does, once). SpellLevel 30 = 9 + 5 x 4 + 1 (L6).
glacial_eruption_203274 = spell(
    id=203274, name='Glacial Eruption', school=School.FROST, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0, radius_yards=3.0, duration_ms=0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=52.0, potency_kind='direct',
               implicit_target_a=_TARGET_DEST_DEST, implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=3.0),
    ],
    spell_icon_id=_ICON_GLACIAL_ADVANCE,
    notes=(
        'death-knight-rework S2a (U25): one Glacial Advance spike, cast triggered at a point by the scripted events. '
        'SCHOOL_DAMAGE ap_potency 52 (S2 TUNE, U33; was 75) direct (T 1500), TARGET_DEST_DEST + TARGET_UNIT_DEST_AREA_ENEMY radius 3 yd, '
        'range '
        '50000 (script cast at a point, bug 554), Frost, magic class, visual 14011 (Impale; 14013 is earth, 14060 the '
        'fallback). d2 b9 (m.GLACIAL_ADVANCE). AttributesEx3 SUPPRESS_CASTER_PROCS. SpellLevel 30 = 9 + 5 x 4 + 1.'
    ),
    raw_overrides=_raw(
        'Deals {pot1} Frost damage to enemies near the eruption.', level=30, magic=True,
        AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS, SpellClassMask_3=m.GLACIAL_ADVANCE,
        SpellVisualID_1=_SV_GLACIAL_ERUPTION, **_chain_amplitudes([None]),
    ),
)
scripted_by(glacial_eruption_203274, 'spell_dk_glacial_eruption')

# The cast: instant, 30 Runic Power (stored x10), 6 s, GCD 133 / 1500, magic class (core-hasted GCD), self DUMMY the
# script reads (it schedules the eruptions), NO IS_ABILITY (it would drop the core haste). d2 b9 carries the CAST-phase
# procs (Unleashed Frenzy, Obliteration). SkillLineAbility 30750 (Frost line 771) comes from granted_by_talent.
glacial_advance_203273 = spell(
    id=203273, name='Glacial Advance', school=School.FROST, attributes=0, cast_time_ms=0, cooldown_ms=6000,
    category_cooldown_ms=0, power_type=PowerType.RUNIC_POWER, mana_cost=300, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_GLACIAL_ADVANCE,
    notes=(
        'death-knight-rework S2a (U25, Frost doc "Glacial Advance", 4,1): talent castable, Frost, instant, 30 Runic '
        'Power '
        '(PowerType 6, ManaCost 300), 6 s DBC cooldown (below the 30 s Cooldown Haste floor), GCD 133 / 1500, magic '
        'class '
        '(DefenseType 1: the core hastes the GCD), NO IS_ABILITY, self range. eff0 DUMMY on the caster: '
        'spell_dk_glacial_advance (AfterCast) snaps five points along the facing and schedules the 203274 eruptions. '
        'd2 b9 (m.GLACIAL_ADVANCE) the only family bit. Tooltip = the doc text minus its cost and cooldown sentences. '
        'SpellLevel 30 = 9 + 5 x 4 + 1. SLA 30750 / talent 60346 are deathknight_talents.py\'s.'
    ),
    raw_overrides=_raw(
        'Summon glacial spikes from the ground that advance forward, each dealing '
        + pot_text(glacial_eruption_203274) + ' Frost damage to enemies near its eruption point.',
        level=30, gcd=True, magic=True, SpellClassMask_3=m.GLACIAL_ADVANCE, **_chain_amplitudes([None]),
    ),
)
scripted_by(glacial_advance_203273, 'spell_dk_glacial_advance')

# =====================================================================================================================
# Gravefrost (203275-203277, talent 60347, row 4): Heart Strike and Plague Strike +5/10/15%; rank 3 = Shadowfrost
# =====================================================================================================================

_GRAVEFROST_CAPSTONE = 'Heart Strike and Plague Strike deal Shadowfrost damage.'
_GRAVEFROST_NOTE = (
    'death-knight-rework S2a, Frost doc "Gravefrost" (4,2), U15: hidden passive, eff0 ADD_PCT_MODIFIER SPELLMOD_DAMAGE '
    'stored 4 / 9 / 14 (= +5 / 10 / 15%) on m.GRAVEFROST_READ = Heart Strike d0 b24 + Plague Strike d0 b0 (the Heart '
    'Strike off-hand copy 203322 carries b24 too). Rank 3 (203277) is the capstone marker: the Heart Strike / Plague '
    'Strike scripts test HasAura(203277) and switch the cast school to Shadowfrost (U5). SpellLevel 9 + 5 x 4 + rank.'
)


def _gravefrost_rank(spell_id, rank, stored, percent):
    return _passive_rank(
        spell_id, 'Gravefrost',
        [_aura(AuraType.ADD_PCT_MODIFIER, base_points=stored, misc_value=int(SpellModOp.DAMAGE))],
        _ICON_GRAVEFROST, _ROW_GRAVEFROST, rank,
        _capstone_text(f'Increases the damage of Heart Strike and Plague Strike by {percent}%.', _GRAVEFROST_CAPSTONE,
                       rank == 3),
        _GRAVEFROST_NOTE, masks={1: m.GRAVEFROST_READ},
    )


gravefrost_203275 = _gravefrost_rank(203275, 1, 4, 5)
gravefrost_203276 = _gravefrost_rank(203276, 2, 9, 10)
gravefrost_203277 = _gravefrost_rank(203277, 3, 14, 15)

# =====================================================================================================================
# Koltira's Favor (203278-203279, talent 60348, row 5): Obliterate +5/10% and a 5/10% Frost Rune refund
# =====================================================================================================================

_KOLTIRAS_NOTE = (
    'death-knight-rework S2a, Frost doc "Koltira\'s Favor" (5,1), U15 / U18: hidden passive. eff0 ADD_PCT_MODIFIER '
    'SPELLMOD_DAMAGE stored 4 / 9 (= +5 / 10%) on Obliterate (EffectSpellClassMaskA_2 = m.OBLITERATE, d1 b17). eff1 '
    'DUMMY: the proc effect. Chain spell_proc row (procs_on -203278): CAST phase (1) on Obliterate, melee-class '
    'ProcFlags 0x10, Chance 0 = the rank\'s ProcChance 5 / 10 (native, Proc Chance scales it). '
    'spell_dk_koltiras_favor (OnProc) finds the Frost Rune the cast just spent (snapshot taken in the Obliterate '
    'script) and refunds it with DeathKnight::ActivateRune. SpellLevel 9 + 5 x 5 + rank.'
)


def _koltiras_rank(spell_id, rank, stored, percent):
    return _passive_rank(
        spell_id, "Koltira's Favor",
        [_aura(AuraType.ADD_PCT_MODIFIER, base_points=stored, misc_value=int(SpellModOp.DAMAGE)), _dummy_aura()],
        _ICON_KOLTIRAS_FAVOR, _ROW_KOLTIRAS_FAVOR, rank,
        f'Your Obliterate deals {percent}% more damage and has a {percent}% chance to refund its Frost Rune.',
        _KOLTIRAS_NOTE, masks={1: (0, m.OBLITERATE, 0)}, proc_chance=percent,
    )


koltiras_favor_203278 = _koltiras_rank(203278, 1, 4, 5)
koltiras_favor_203279 = _koltiras_rank(203279, 2, 9, 10)
procs_on(
    -203278, proc_flags=_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS, family_name=_SPELLFAMILY_DEATHKNIGHT,
    family_mask=(0, m.OBLITERATE, 0), spell_type_mask=_PROC_SPELL_TYPE_ALL, spell_phase_mask=_PROC_SPELL_PHASE_CAST,
    chance=0.0,
)
scripted_by(-203278, 'spell_dk_koltiras_favor')

# =====================================================================================================================
# Pillar of Frost (203280, talent 60349, row 6): +20% Strength for 20 s, off the GCD, free
# =====================================================================================================================

# The stock Unbreakable Armor frame (attributes 262160 = IS_ABILITY | DO_NOT_SHEATH, no StartRecovery = off the GCD,
# 60 s, 20 s, self) minus its armor effect and its d0 b21 family bit (51714 / 50406 / Unbreakable Armor read it: Pillar
# NEVER takes it). Free (Q15). Strength is aura 137 MOD_TOTAL_STAT_PERCENTAGE misc 0, stored 19 = +20%; percent buffs
# multiply (Endless Winter, Unleashed Frenzy). spell_dk_pillar_of_frost applies / removes Toravon's Whiteout 203288 and
# Enduring Strength extends the duration. SkillLineAbility 30751 (Frost line 771) comes from granted_by_talent.
pillar_of_frost_203280 = spell(
    id=203280, name='Pillar of Frost', school=School.NORMAL, attributes=_ATTR0_PILLAR, cast_time_ms=0,
    cooldown_ms=60000, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=20000,
    effects=[_aura(AuraType.MOD_TOTAL_STAT_PERCENTAGE, base_points=19, misc_value=_STAT_STRENGTH)],
    spell_icon_id=_ICON_PILLAR_OF_FROST,
    notes=(
        'death-knight-rework S2a (U20, Frost doc "Pillar of Frost", 6,1): talent castable on the stock 51271 frame, '
        'attributes 262160, off the GCD (no StartRecovery), free (no RuneCostID), 60 s DBC cooldown (Cooldown Haste '
        'qualifies, >= 30 s), 20 s, self. eff0 MOD_TOTAL_STAT_PERCENTAGE misc 0 (Strength) stored 19 = +20%. NO family '
        'bits (never d0 b21). Visual 44, icon 2703. Visible aura (not passive, no consolidation flag), number-free '
        'aura text. spell_dk_pillar_of_frost handles Toravon\'s Whiteout. SpellLevel 40 = 9 + 5 x 6 + 1. SLA 30751 / '
        'talent 60349 are deathknight_talents.py\'s.'
    ),
    raw_overrides=_raw(
        'Calls upon the power of Frost to increase your Strength by $s1% for $d.', 'Strength increased.', level=40,
        SpellVisualID_1=_SV_PILLAR, **_chain_amplitudes([None]),
    ),
)
scripted_by(pillar_of_frost_203280, 'spell_dk_pillar_of_frost')

# =====================================================================================================================
# Unleashed Frenzy (203281-203282, talent 60350, row 6) and its stacking Strength buffs (203283-203284)
# =====================================================================================================================

# The visible buffs: aura 137 Strength 1 / 2% per stack (CalculateAmount multiplies by the stack), 3 stacks, 10 s,
# refreshed by each proc. Self target (the CAST-phase proc carries no victim).
unleashed_frenzy_buff_203283 = _buff(
    203283, 'Unleashed Frenzy', [_aura(AuraType.MOD_TOTAL_STAT_PERCENTAGE, base_points=0, misc_value=_STAT_STRENGTH)],
    _ICON_UNLEASHED_FRENZY, 10000, 'Increases your Strength by 1%.', 'Strength increased.',
    'death-knight-rework S2a (U23), Frost doc "Unleashed Frenzy" (6,3): rank 1 buff. MOD_TOTAL_STAT_PERCENTAGE misc 0 '
    'stored 0 = +1% Strength per stack, CumulativeAura 3, 10 s (refreshed by each proc). Visible, non-passive, '
    'number-free aura text, no family bits. Applied by the PROC_TRIGGER_SPELL of 203281.',
    stacks=3,
)
unleashed_frenzy_buff_203284 = _buff(
    203284, 'Unleashed Frenzy', [_aura(AuraType.MOD_TOTAL_STAT_PERCENTAGE, base_points=1, misc_value=_STAT_STRENGTH)],
    _ICON_UNLEASHED_FRENZY, 10000, 'Increases your Strength by 2%.', 'Strength increased.',
    'death-knight-rework S2a (U23), Frost doc "Unleashed Frenzy" (6,3): rank 2 buff. MOD_TOTAL_STAT_PERCENTAGE misc 0 '
    'stored 1 = +2% Strength per stack, CumulativeAura 3, 10 s (refreshed by each proc). Visible, non-passive, '
    'number-free aura text, no family bits. Applied by the PROC_TRIGGER_SPELL of 203282.',
    stacks=3,
)

_UNLEASHED_FRENZY_NOTE = (
    'death-knight-rework S2a, Frost doc "Unleashed Frenzy" (6,3), U23 / L3: hidden passive, eff0 PROC_TRIGGER_SPELL -> '
    'the rank\'s buff (self). Per-rank spell_proc row (declared below): CAST phase (1) on Frost Strike d1 b2 + Glacial '
    'Advance d2 b9 (m.UNLEASHED_FRENZY_PROC), once per non-triggered cast with no guard, Chance 100; ProcFlags carry '
    'the '
    'melee-class and both magic-class (positive / negative) done-spell flags because a self-DUMMY Glacial Advance may '
    'be '
    'classed positive. Breath of Sindragosa\'s drain does not count (not in the mask). SpellLevel 9 + 5 x 6 + rank.'
)
unleashed_frenzy_203281 = _passive_rank(
    203281, 'Unleashed Frenzy',
    [_aura(AuraType.PROC_TRIGGER_SPELL, trigger_spell=203283)],
    _ICON_UNLEASHED_FRENZY, _ROW_UNLEASHED_FRENZY, 1,
    'Your Frost Strike and Glacial Advance increase your Strength by 1% for 10 sec, stacking up to 3 times.',
    _UNLEASHED_FRENZY_NOTE,
)
unleashed_frenzy_203282 = _passive_rank(
    203282, 'Unleashed Frenzy',
    [_aura(AuraType.PROC_TRIGGER_SPELL, trigger_spell=203284)],
    _ICON_UNLEASHED_FRENZY, _ROW_UNLEASHED_FRENZY, 2,
    'Your Frost Strike and Glacial Advance increase your Strength by 2% for 10 sec, stacking up to 3 times.',
    _UNLEASHED_FRENZY_NOTE,
)
for _frenzy in (unleashed_frenzy_203281, unleashed_frenzy_203282):
    procs_on(
        _frenzy, proc_flags=_PROC_CAST_STRIKE_AND_MAGIC, family_name=_SPELLFAMILY_DEATHKNIGHT,
        family_mask=m.UNLEASHED_FRENZY_PROC, spell_type_mask=_PROC_SPELL_TYPE_ALL,
        spell_phase_mask=_PROC_SPELL_PHASE_CAST, chance=100.0,
    )

# =====================================================================================================================
# Toravon's Whiteout (203285-203287, talent 60351, row 7) and its Pillar-bound buff (203288)
# =====================================================================================================================

_TORAVONS_NOTE = (
    'death-knight-rework S2a, Frost doc "Toravon\'s Whiteout" (7,2): hidden passive, eff0 DUMMY stored 4 / 9 / 14 '
    '(value '
    '5 / 10 / 15, read with GetAmount() by spell_dk_pillar_of_frost, which applies buff 203288 with that amount on '
    'Pillar apply and removes it on Pillar remove). Not a SpellMod: nothing else reads the rank. SpellLevel 9 + 5 x 7 '
    '+ '
    'rank.'
)


def _toravons_rank(spell_id, rank, stored, percent):
    return _passive_rank(
        spell_id, "Toravon's Whiteout", [_dummy_aura(stored)], _ICON_TORAVONS_WHITEOUT, _ROW_TORAVONS_WHITEOUT, rank,
        f'Your Pillar of Frost also increases your Frost damage by {percent}%.', _TORAVONS_NOTE,
    )


toravons_whiteout_203285 = _toravons_rank(203285, 1, 4, 5)
toravons_whiteout_203286 = _toravons_rank(203286, 2, 9, 10)
toravons_whiteout_203287 = _toravons_rank(203287, 3, 14, 15)

# Visible, duration -1: it lives exactly as long as Pillar, extensions included (Enduring Strength), because the Pillar
# script applies it on Pillar's apply and removes it on Pillar's remove. The amount (stored 0 here) is set by the script
# to the known rank (5 / 10 / 15). Frost school (misc 16) reaches Shadowfrost too.
toravons_whiteout_buff_203288 = _buff(
    203288, "Toravon's Whiteout",
    [_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=0, misc_value=_SCHOOL_FROST)],
    _ICON_TORAVONS_WHITEOUT, -1, 'Increases your Frost damage.', 'Frost damage increased.',
    'death-knight-rework S2a (U20), Frost doc "Toravon\'s Whiteout" (7,2): the Pillar-bound buff. '
    'MOD_DAMAGE_PERCENT_DONE (79) misc 16 (Frost), stored 0, the amount is set by spell_dk_pillar_of_frost to the '
    'known '
    'rank 5 / 10 / 15. Duration -1 (removed with Pillar, so Enduring Strength\'s extension carries over). Visible, '
    'non-passive, number-free aura text, no family bits.',
)

# =====================================================================================================================
# Final Roar (203289-203290, talent 60352, row 7): Rune Tap +10/20 Runic Power; capstone = the roar when Breath ends
# =====================================================================================================================

_FINAL_ROAR_CAPSTONE = (
    'When Breath of Sindragosa ends, Sindragosa unleashes a final roar, dealing Frost damage equal to 10% of the '
    'damage '
    'your Breath dealt, split among enemies in a cone in front of you.'
)
_FINAL_ROAR_NOTE = (
    'death-knight-rework S2a, Frost doc "Final Roar" (7,3), U12 / U19: hidden passive. eff0 ADD_FLAT_MODIFIER '
    'SPELLMOD_EFFECT1 stored 99 / 199 (= +100 / +200 internal = +10 / +20 RP) on Rune Tap (EffectSpellClassMaskA_1 = '
    'm.RUNE_TAP, d0 b27); Rune Tap\'s ENERGIZE is its effect index 0 (DK0a seam). Rank 2 (203290) adds eff1 DUMMY '
    'stored 9 (value 10 = FINAL_ROAR_SHARE_PCT, informational): the capstone flag, an APPLY_AURA on a passive so '
    'spell_dk_breath_of_sindragosa tests HasAura(203290) (L4). SpellLevel 9 + 5 x 7 + rank.'
)
final_roar_203289 = _passive_rank(
    203289, 'Final Roar',
    [_aura(AuraType.ADD_FLAT_MODIFIER, base_points=99, misc_value=int(SpellModOp.EFFECT1))],
    _ICON_FINAL_ROAR, _ROW_FINAL_ROAR, 1,
    _capstone_text('Your Rune Tap generates 10 additional Runic Power.', _FINAL_ROAR_CAPSTONE, False),
    _FINAL_ROAR_NOTE, masks={1: (m.RUNE_TAP, 0, 0)},
)
final_roar_203290 = _passive_rank(
    203290, 'Final Roar',
    [_aura(AuraType.ADD_FLAT_MODIFIER, base_points=199, misc_value=int(SpellModOp.EFFECT1)), _dummy_aura(9)],
    _ICON_FINAL_ROAR, _ROW_FINAL_ROAR, 2,
    _capstone_text('Your Rune Tap generates 20 additional Runic Power.', _FINAL_ROAR_CAPSTONE, True),
    _FINAL_ROAR_NOTE, masks={1: (m.RUNE_TAP, 0, 0)},
)

# The roar: cast triggered by the Breath script when the aura ends by expiry / cancel. Family 15, NO bits (inert under
# Razorice and every reader), IGNORE_CASTER_MODIFIERS (no Mastery, Versatility, Toravon's, ramp), CANT_CRIT,
# SUPPRESS_CASTER_PROCS. The damage is the stored Breath total x FINAL_ROAR_SHARE_PCT / targets, set in OnHit with
# SetHitDamage (potency_excluded). 12 yd cone (D2: target 104), visual 14711.
final_roar_burst_203291 = spell(
    id=203291, name='Final Roar', school=School.FROST, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, radius_yards=12.0, duration_ms=0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_UNIT_CONE_ENEMY_104, radius_yards=12.0,
               potency_excluded='the damage is the stored Breath total x FINAL_ROAR_SHARE_PCT / targets, set with '
                                'SetHitDamage by spell_dk_final_roar, not CalcValue (percent of other damage)'),
    ],
    spell_icon_id=_ICON_FINAL_ROAR,
    notes=(
        'death-knight-rework S2a (U12 / D2), Frost doc "Final Roar": the capstone burst. SCHOOL_DAMAGE value 0 '
        '(potency_excluded: spell_dk_final_roar OnHit SetHitDamage(store x 10% / n)), cone TARGET_UNIT_CONE_ENEMY_104 '
        '(104 degree total arc) radius 12 yd, self range, Frost, magic class, visual 14711. Family 15 with NO bits. '
        'AttributesEx3 IGNORE_CASTER_MODIFIERS (0x20000000) | SUPPRESS_CASTER_PROCS (0x10000), AttributesEx2 '
        'CANT_CRIT. '
        'All-zero spell_bonus_data row. SpellLevel 0 (no potency).'
    ),
    raw_overrides=_raw(
        'Sindragosa unleashes a final roar, dealing Frost damage to enemies in a cone in front of you.', magic=True,
        AttributesEx2=_ATTR2_CANT_CRIT, AttributesEx3=_ATTR3_IGNORE_CASTER_MODIFIERS | _ATTR3_SUPPRESS_CASTER_PROCS,
        SpellVisualID_1=_SV_SINDRAGOSA_BREATH, **_chain_amplitudes([None]),
    ),
)
bonus_coefficients(final_roar_burst_203291, direct=0.0, dot=0.0, ap=0.0, ap_dot=0.0,
                   comment='Death Knight - Final Roar burst: the script sets the whole hit damage, no SP / AP')
scripted_by(final_roar_burst_203291, 'spell_dk_final_roar')

# =====================================================================================================================
# Obliteration (203292, talent 60353, row 8) and its Frost Rune helper (203293)
# =====================================================================================================================

obliteration_203292 = _passive_rank(
    203292, 'Obliteration', [_dummy_aura()], _ICON_OBLITERATION, _ROW_OBLITERATION, 1,
    _capstone_text(
        'While Pillar of Frost is active, your Frost Strike, Howling Blast and Glacial Advance always grant Killing '
        'Machine and have a 30% chance to activate a depleted Frost Rune.',
        'Obliterates empowered by Killing Machine deal additional damage equal to your Mastery.', True,
    ),
    'death-knight-rework S2a, Frost doc "Obliteration" (8,1), U20: hidden passive, eff0 DUMMY (the proc effect). '
    'spell_proc row (declared below): CAST phase (1) on Frost Strike d1 b2 + Howling Blast d1 b1 '
    '(m.OBLITERATION_PROC) + '
    'Glacial Advance d2 b9, once per non-triggered cast, Chance 100; melee-class and both magic-class done-spell flags '
    '(see Unleashed Frenzy). spell_dk_obliteration: CheckProc HasAura(Pillar of Frost), OnProc grants a Killing '
    'Machine '
    'stack, then rolls OBLITERATION_RUNE_PCT x Proc Chance for the Frost Rune helper 203293. The capstone (Mastery '
    'added to a Killing Machine Obliterate) tests HasAura(203292). Icon 4157 (not 2639). SpellLevel 9 + 5 x 8 + 1.',
)
procs_on(
    obliteration_203292, proc_flags=_PROC_CAST_STRIKE_AND_MAGIC, family_name=_SPELLFAMILY_DEATHKNIGHT,
    family_mask=m.OBLITERATION_PROC, spell_type_mask=_PROC_SPELL_TYPE_ALL, spell_phase_mask=_PROC_SPELL_PHASE_CAST,
    chance=100.0,
)
scripted_by(obliteration_203292, 'spell_dk_obliteration')

# ACTIVATE_RUNE misc 2 (Frost), count 1 (stored 0): readies the first recharging Frost slot, nothing if both are ready
# (SpellEffects.cpp:6176-6250). Cast triggered on the caster.
obliteration_frost_rune_203293 = _helper(
    203293, 'Obliteration',
    [Effect(type=_EFFECT_ACTIVATE_RUNE, base_points=0, implicit_target_a=_TARGET_UNIT_CASTER,
            misc_value=_RUNE_FROST)],
    _ICON_OBLITERATION, 'Activates a depleted Frost Rune.',
    'death-knight-rework S2a (U18 / U20): Obliteration\'s rune helper. ACTIVATE_RUNE (146) misc 2 = Frost, count 1 '
    '(stored 0), caster target. Cast triggered by spell_dk_obliteration. No cost, no family bits, SpellLevel 0.',
)

# =====================================================================================================================
# Rage of the Frozen Champion (203294-203295, talent 60354, row 8) and its energize (203296)
# =====================================================================================================================

_ROTFC_CAPSTONE = "Breath of Sindragosa's ticks have an 8% chance to grant Rime."
_ROTFC_NOTE = (
    'death-knight-rework S2a, Frost doc "Rage of the Frozen Champion" (8,3), U19: hidden passive, eff0 DUMMY stored 3 '
    '/ '
    '7 (value 4 / 8 RP, read with GetAmount() by the Howling Blast script, which casts 203296 with the amount x10 when '
    'a Rime Howling Blast resolves). Rank 2 (203295) adds eff1 DUMMY stored 7 (value 8 = '
    'RAGE_FROZEN_CHAMPION_RIME_PCT): '
    'the capstone flag (APPLY_AURA on a passive, L4); the Breath aura script tests HasAura(203295). SpellLevel 9 + 5 '
    'x 8 '
    '+ rank.'
)
rage_of_the_frozen_champion_203294 = _passive_rank(
    203294, 'Rage of the Frozen Champion', [_dummy_aura(3)], _ICON_RAGE_OF_THE_FROZEN_CHAMPION,
    _ROW_RAGE_OF_THE_FROZEN_CHAMPION, 1,
    _capstone_text('Your Rime-empowered Howling Blasts generate 4 additional Runic Power.', _ROTFC_CAPSTONE, False),
    _ROTFC_NOTE,
)
rage_of_the_frozen_champion_203295 = _passive_rank(
    203295, 'Rage of the Frozen Champion', [_dummy_aura(7), _dummy_aura(7)], _ICON_RAGE_OF_THE_FROZEN_CHAMPION,
    _ROW_RAGE_OF_THE_FROZEN_CHAMPION, 2,
    _capstone_text('Your Rime-empowered Howling Blasts generate 8 additional Runic Power.', _ROTFC_CAPSTONE, True),
    _ROTFC_NOTE,
)
rage_of_the_frozen_champion_energize_203296 = _helper(
    203296, 'Rage of the Frozen Champion',
    [Effect(type=EffectType.ENERGIZE, base_points=39, implicit_target_a=_TARGET_UNIT_CASTER,
            misc_value=_POWER_RUNIC_POWER)],
    _ICON_RAGE_OF_THE_FROZEN_CHAMPION, 'Generates additional Runic Power.',
    'death-knight-rework S2a (U19): the RotFC energize, ENERGIZE Runic Power (misc 6), caster target. The data value '
    '(stored 39 = 4 RP, rank 1) is overridden by the Howling Blast script (CastCustomSpell BASE_POINT0 = rank RP x 10; '
    'CalcBaseValue subtracts the 1 itself). No cost, no family bits, SpellLevel 0.',
)

# =====================================================================================================================
# Enduring Strength (203297-203298, talent 60355, row 9): Killing Machine extends Pillar
# =====================================================================================================================

_ENDURING_STRENGTH_NOTE = (
    'death-knight-rework S2a, Frost doc "Enduring Strength" (9,0), U20: hidden passive with two DUMMY effects read '
    'with '
    'GetAmount() by the Obliterate script: eff0 = extension per consumed Killing Machine stack in ms (stored 499 / 999 '
    '= 500 / 1000), eff1 = the per-Pillar cap in ms (stored 2999 / 5999 = 3000 / 6000). SpellLevel 9 + 5 x 9 + rank.'
)
enduring_strength_203297 = _passive_rank(
    203297, 'Enduring Strength', [_dummy_aura(499), _dummy_aura(2999)], _ICON_ENDURING_STRENGTH,
    _ROW_ENDURING_STRENGTH, 1,
    'Consuming Killing Machine while Pillar of Frost is active extends Pillar of Frost by 0.5 sec, up to 3 sec.',
    _ENDURING_STRENGTH_NOTE,
)
enduring_strength_203298 = _passive_rank(
    203298, 'Enduring Strength', [_dummy_aura(999), _dummy_aura(5999)], _ICON_ENDURING_STRENGTH,
    _ROW_ENDURING_STRENGTH, 2,
    'Consuming Killing Machine while Pillar of Frost is active extends Pillar of Frost by 1 sec, up to 6 sec.',
    _ENDURING_STRENGTH_NOTE,
)

# =====================================================================================================================
# Seal of Necrofantasia (203299-203301, talent 60356, row 9): Empower Rune Weapon cooldown -20/-40/-60 s
# =====================================================================================================================

_SEAL_NOTE = (
    'death-knight-rework S2a, Frost doc "Seal of Necrofantasia" (9,1), U23: hidden passive, eff0 ADD_FLAT_MODIFIER '
    'SPELLMOD_COOLDOWN stored -20001 / -40001 / -60001 (= -20 / -40 / -60 s) on Empower Rune Weapon '
    '(EffectSpellClassMaskA_1 '
    '= m.ERW, d0 b14). It applies before Cooldown Haste (Player.cpp:11213 vs 11290-11296). SpellLevel 9 + 5 x 9 + rank.'
)


def _seal_rank(spell_id, rank, stored, seconds):
    return _passive_rank(
        spell_id, 'Seal of Necrofantasia',
        [_aura(AuraType.ADD_FLAT_MODIFIER, base_points=stored, misc_value=int(SpellModOp.COOLDOWN))],
        _ICON_SEAL_OF_NECROFANTASIA, _ROW_SEAL_OF_NECROFANTASIA, rank,
        f'Reduces the cooldown of your Empower Rune Weapon by {seconds} sec.', _SEAL_NOTE, masks={1: (m.ERW, 0, 0)},
    )


seal_of_necrofantasia_203299 = _seal_rank(203299, 1, -20001, 20)
seal_of_necrofantasia_203300 = _seal_rank(203300, 2, -40001, 40)
seal_of_necrofantasia_203301 = _seal_rank(203301, 3, -60001, 60)

# =====================================================================================================================
# Frostwyrm's Wrath (203302-203303, talent 60357, row 9), its energize (203304) and the Breath ramp buff (203305)
# =====================================================================================================================

_FROSTWYRMS_CAPSTONE = 'Breath of Sindragosa deals 10% more damage for every 5 sec it remains active.'
_FROSTWYRMS_NOTE = (
    'death-knight-rework S2a, Frost doc "Frostwyrm\'s Wrath" (9,3), U19 / L3: hidden passive, eff0 '
    'PROC_TRIGGER_SPELL_WITH_VALUE (231) -> 203304 with the Runic Power as the aura amount (stored 49 / 99 = 5 / 10 '
    'RP, '
    'RP x10). Per-rank spell_proc row (declared below): CAST phase (1) on Horn of Winter (d1 b30, m.HORN_OF_WINTER), '
    'positive magic-class done-spell flag, Chance 100, once per cast; the energize helper targets the caster because '
    'the CAST-phase proc has no victim. Rank 2 (203303) adds eff1 DUMMY stored 9 (value 10 = FROSTWYRM_RAMP_PCT): the '
    'capstone flag (APPLY_AURA on a passive, L4), the Breath script tests HasAura(203303) and stacks the ramp 203305. '
    'SpellLevel 9 + 5 x 9 + rank.'
)
frostwyrms_wrath_203302 = _passive_rank(
    203302, "Frostwyrm's Wrath",
    [_aura(AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, base_points=49, trigger_spell=203304)],
    _ICON_FROSTWYRMS_WRATH, _ROW_FROSTWYRMS_WRATH, 1,
    _capstone_text('Your Horn of Winter generates 5 additional Runic Power.', _FROSTWYRMS_CAPSTONE, False),
    _FROSTWYRMS_NOTE,
)
frostwyrms_wrath_203303 = _passive_rank(
    203303, "Frostwyrm's Wrath",
    [_aura(AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, base_points=99, trigger_spell=203304), _dummy_aura(9)],
    _ICON_FROSTWYRMS_WRATH, _ROW_FROSTWYRMS_WRATH, 2,
    _capstone_text('Your Horn of Winter generates 10 additional Runic Power.', _FROSTWYRMS_CAPSTONE, True),
    _FROSTWYRMS_NOTE,
)
for _wrath in (frostwyrms_wrath_203302, frostwyrms_wrath_203303):
    procs_on(
        _wrath, proc_flags=_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, family_name=_SPELLFAMILY_DEATHKNIGHT,
        family_mask=(0, m.HORN_OF_WINTER, 0), spell_type_mask=_PROC_SPELL_TYPE_ALL,
        spell_phase_mask=_PROC_SPELL_PHASE_CAST, chance=100.0,
    )

frostwyrms_wrath_energize_203304 = _helper(
    203304, "Frostwyrm's Wrath",
    [Effect(type=EffectType.ENERGIZE, base_points=49, implicit_target_a=_TARGET_UNIT_CASTER,
            misc_value=_POWER_RUNIC_POWER)],
    _ICON_FROSTWYRMS_WRATH, 'Generates additional Runic Power.',
    'death-knight-rework S2a (U19): the Frostwyrm\'s Wrath energize, ENERGIZE Runic Power (misc 6) stored 49 = 5 RP, '
    'caster target (the CAST-phase proc carries no victim); the 231 aura passes the rank value 5 / 10 RP. No cost, no '
    'family bits, SpellLevel 0.',
)

# The visible ramp (capstone): one stack per FROSTWYRM_RAMP_TICKS Breath ticks, +FROSTWYRM_RAMP_PCT% Breath damage per
# stack, read by the tick script. Duration -1 and never saved (CU_AURA_CANNOT_BE_SAVED, like the Breath aura itself):
# the script removes it with Breath, so a stale stack must never survive a logout. 99 stacks = "no cap" (Breath cannot
# run 495 s). Self target.
frostwyrms_wrath_ramp_203305 = _buff(
    203305, "Frostwyrm's Wrath", [_dummy_aura()], _ICON_FROSTWYRMS_WRATH, -1,
    'Your Breath of Sindragosa deals more damage.', 'Breath of Sindragosa deals more damage.',
    'death-knight-rework S2a (U19), Frost doc "Frostwyrm\'s Wrath" (9,3): the visible capstone ramp. Self DUMMY (the '
    'tick script reads the stack count), CumulativeAura 99 (no practical cap), duration -1, removed with Breath by '
    'spell_dk_breath_of_sindragosa; CU_AURA_CANNOT_BE_SAVED so a logout cannot leave a stale stack. Visible, '
    'non-passive, number-free aura text, no family bits.',
    stacks=99,
)
custom_attr(frostwyrms_wrath_ramp_203305, attributes=_CU_AURA_CANNOT_BE_SAVED)

# =====================================================================================================================
# Breath of Sindragosa (203306, talent 60358, row 10) and its tick (203307)
# =====================================================================================================================

# The tick: cast triggered each second by spell_dk_breath_of_sindragosa. 42 AP potency direct (S2 TUNE
# 2026-10-25, U33; was 60), time_basis_ms 1000
# (L2: the
# real cadence), Frost, magic class, 12 yd cone (D2: target 104, a 104 degree total arc; the bot reads
# enemies_in_cone(12, 104)), visual 14711 (Sindragosa's Frost Breath). The primary takes the full tick, every other
# target 50% (script). d2 b10 (m.BREATH). SUPPRESS_CASTER_PROCS: ticks roll no procs. SpellLevel 60 = 9 + 5 x 10 + 1.
breath_of_sindragosa_tick_203307 = spell(
    id=203307, name='Breath of Sindragosa', school=School.FROST, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, radius_yards=12.0, duration_ms=0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=42.0, potency_kind='direct', time_basis_ms=1000,
               implicit_target_a=_TARGET_UNIT_CONE_ENEMY_104, radius_yards=12.0),
    ],
    spell_icon_id=_ICON_BREATH_OF_SINDRAGOSA,
    notes=(
        'death-knight-rework S2a (U11 / D2), Frost doc "Breath of Sindragosa" (10,1): the per-second tick. '
        'SCHOOL_DAMAGE ap_potency 42 (S2 TUNE, U33; was 60) direct, time_basis_ms 1000 (L2), TARGET_UNIT_CONE_ENEMY_104 (104 degree total '
        'arc) '
        'radius 12 yd, self range, Frost, magic class, visual 14711. d2 b10 (m.BREATH) the only family bit. '
        'AttributesEx3 SUPPRESS_CASTER_PROCS. spell_dk_breath_of_sindragosa_tick: primary full, secondary '
        'BREATH_SECONDARY_PCT, multiplier, AfterHit stores the damage for Final Roar. SpellLevel 60 = 9 + 5 x 10 + 1.'
    ),
    raw_overrides=_raw(
        'Deals {pot1.avg} Frost damage to enemies in a cone in front of you.', level=60, magic=True,
        AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS, SpellClassMask_3=m.BREATH,
        SpellVisualID_1=_SV_SINDRAGOSA_BREATH, **_chain_amplitudes([None]),
    ),
)
scripted_by(breath_of_sindragosa_tick_203307, 'spell_dk_breath_of_sindragosa_tick')

# The cast and its aura are one spell (the P0 item 6 shape, D15): instant, GCD 133 / 1500, magic class (core-hasted
# GCD),
# Runic Power power type with cost 0 (CheckCast requires BREATH_MIN_RP; the drain is the aura's), a normal 2 min DBC
# cooldown (Cooldown Haste applies generically, no script cooldown), self PERIODIC_DUMMY 1000 ms (never hasted: no
# ATTR5 bit), duration -1, family 15 with NO bits (Bonestorm precedent), right-click cancels (no re-press cancel).
# CU_AURA_CANNOT_BE_SAVED: a duration -1 aura would otherwise be saved at logout and resume at login without its drain
# script state. SkillLineAbility 30752 (Frost line 771) comes from granted_by_talent.
breath_of_sindragosa_203306 = spell(
    id=203306, name='Breath of Sindragosa', school=School.FROST, attributes=0, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, power_type=PowerType.RUNIC_POWER, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_BREATH_OF_SINDRAGOSA,
    notes=(
        'death-knight-rework S2a (U11 / D15, Frost doc "Breath of Sindragosa", 10,1): talent castable, Frost, instant, '
        'GCD 133 / 1500, magic class (DefenseType 1), NO IS_ABILITY, Runic Power power type with cost 0, 2 min DBC '
        'cooldown (Cooldown Haste applies), self range. eff0 PERIODIC_DUMMY 1000 ms, duration -1, never hasted. NO '
        'family bits. CU_AURA_CANNOT_BE_SAVED (0x01000000) via spell_custom_attr. Visible aura (not passive, no '
        'consolidation flag), number-free aura text. spell_dk_breath_of_sindragosa (Spell + Aura): CheckCast >= '
        'BREATH_MIN_RP, tick drain / cast of 203307 / ramp / Final Roar on EXPIRE or CANCEL only. Tooltip = the doc '
        'text '
        'minus its cooldown sentence. SpellLevel 60 = 9 + 5 x 10 + 1. SLA 30752 / talent 60358 are '
        'deathknight_talents.py\'s.'
    ),
    raw_overrides=_raw(
        'Continuously deal ' + pot_text(breath_of_sindragosa_tick_203307, variant='avg')
        + ' Frost damage every 1 sec to enemies in a cone in front of you, with reduced damage to secondary targets. '
          'Drains 10 Runic Power per sec, increasing by 1 every 5 sec. Lasts until you cancel it or cannot pay.\n\n'
          "Capstone: Breath of Sindragosa's damage is increased by your Mastery.",
        'Breathing frost at enemies in front of you, draining Runic Power.', level=60, gcd=True, magic=True,
        **_chain_amplitudes([None]),
    ),
)
scripted_by(breath_of_sindragosa_203306, 'spell_dk_breath_of_sindragosa')
custom_attr(breath_of_sindragosa_203306, attributes=_CU_AURA_CANNOT_BE_SAVED)

# ---- S2a script numbers (S2-HANDOFF section 3 "New DeathKnightData consts"; header names are the first argument) ----
_C = [
    ("KILLING_MACHINE_MAX_STACKS", 2, "Killing Machine stack cap (buff 203320)."),
    ("DEATHCHILL_DAMAGE_PCT", 20, "Deathchill direct-damage bonus percent."),
    ("HUNGERING_COLD_SLOW_STACKS_TO_FREEZE", 2, "Slow stacks that trigger the Hungering Cold freeze."),
    ("HUNGERING_COLD_STORM_MS", 10000, "Hungering Cold storm duration (a new Howling Blast resets it to this)."),
    ("BREATH_MIN_RP", 10, "Minimum Runic Power to cast Breath of Sindragosa."),
    ("BREATH_BASE_DRAIN", 10, "Breath drain per second (Runic Power)."),
    ("BREATH_DRAIN_STEP_TICKS", 5, "Breath drain rises by 1 every this many ticks."),
    ("BREATH_SECONDARY_PCT", 50, "Breath damage percent on secondary targets."),
    ("FROSTWYRM_RAMP_PCT", 10, "Frostwyrm's Wrath ramp: Breath damage percent per stack."),
    ("FROSTWYRM_RAMP_TICKS", 5, "Frostwyrm's Wrath ramp: ticks per stack."),
    ("FINAL_ROAR_SHARE_PCT", 10, "Final Roar: share of Breath damage dealt (stored, split among the cone)."),
    ("RIME_AVALANCHE_TARGETS", 5, "Avalanche icicle target cap."),
    ("RAGE_FROZEN_CHAMPION_RIME_PCT", 8, "Rage of the Frozen Champion capstone: Rime chance percent per Breath tick."),
    ("MERCILESS_COMBAT_HP_PCT", 35, "Merciless Combat threshold: target health percent."),
    ("OBLITERATION_RUNE_PCT", 30, "Obliteration: chance percent for a Frost Rune."),
    ("GLACIAL_ADVANCE_ERUPTIONS", 5, "Glacial Advance eruption count."),
    ("GLACIAL_ADVANCE_STEP_YARDS", 4, "Glacial Advance spacing between eruptions."),
    ("GLACIAL_ADVANCE_STEP_MS", 150, "Glacial Advance delay between eruptions."),
    ("RAZORICE_PCT_PER_STACK", 2, "Razorice: Frost vulnerability percent per stack."),
    ("OFFHAND_PENALTY_PCT", 50, "Off-hand damage penalty percent for non-physical off-hand strikes."),
]
for _name, _value, _doc in _C:
    globals()[_name] = const(_name, _value, _doc)
