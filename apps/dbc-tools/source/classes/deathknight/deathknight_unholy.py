"""
Death Knight - S3a Unholy: new talent ranks 203440-203455, the Dark Transformation and Raise Abomination castables,
SLA 30760-30761 (via granted_by_talent), the Unholy consts.
Source of truth: docs/reworks/death-knight-unholy-rework.md,
.agents/plans/death-knight-rework/death-knight-rework.S3a-WP-BRIEF.md.

Talent rank spells are hidden passives (attributes 0x1D0, Blood's / Frost's talent-passive shape); a rank's SpellLevel
is 9 + 5 x talent row + rank. The talent rows and the SkillLineAbility rows 30760 / 30761 come from granted_by_talent
in deathknight_talents.py (A1); this file only provides the rank spells and the two castables. Tooltips are the doc
text minus the cost and cooldown sentences. Variable names fix the generated DeathKnightData header names: never
rename one.
"""

from lib.dsl import AuraType, Effect, EffectType, PowerType, RANGE_SELF, School
from lib.dsl.registry import const, linked_spell, pot_text, procs_on, scripted_by, spell

from . import _masks as m
from .deathknight_unholy_b import (
    dark_transformation_ready_203465, harbinger_of_doom_buff_203463, putrid_cloud_tick_203473,
    rotten_touch_buff_203462,
)

# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h) ----
_ATTR0_TALENT_PASSIVE = 464                         # ABILITY 0x10 | PASSIVE 0x40 | DO_NOT_DISPLAY 0x80 | NO_LOG 0x100
_SPELLFAMILY_DEATHKNIGHT = 15

# ---- Effects / misc values / targets (SharedDefines.h) ----
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_PET = 5
_TARGET_DEST_CASTER_SUMMON = 32                     # front left of the caster, doesn't use the radius
_MISC_ALL_SCHOOLS = 127
_NPC_TRANSFORM_ABOMINATION = 17898                  # display 12818 (P0 item 7, passed)
_SUMMON_PROPS_GUARDIAN = 61                         # ALLY / GUARDIAN, numSummons 1 (0-verify B)

# ---- spell_proc masks (src/server/game/Spells/SpellMgr.h) ----
_PROC_FLAG_DONE_MELEE_AUTO_ATTACK = 0x4
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x10
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x4000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x10000
_PROC_FLAG_DONE_MAINHAND_ATTACK = 0x400000
_PROC_SPELL_TYPE_ALL = 0x7
_PROC_SPELL_PHASE_CAST = 0x1
_PROC_SPELL_PHASE_HIT = 0x2
# Death Coil is a magic-class spell: hostile at an enemy (NEG), beneficial at the ghoul (POS).
_PROC_COIL_ANY = _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG

# ---- Stock icons (S3a-WP-BRIEF section 7) ----
_ICON_FESTERING_PLAGUE = 1468
_ICON_ALL_WILL_SERVE = 1590
_ICON_INFECTED_CLAWS = 1116
_ICON_DOOMED_BIDDING = 170
_ICON_DARK_TRANSFORMATION = 90
_ICON_ROTTEN_TOUCH = 77
_ICON_RAISE_ABOMINATION = 90312  # build_patch_i.py ICON_ID_RAISE_ABOMINATION (was stock 313)
_ICON_HARBINGER_OF_DOOM = 76

# ---- Talent rows (S3-HANDOFF section 3): a rank spell's SpellLevel = 9 + 5 x row + rank ----
_ROW_FESTERING_PLAGUE = 2
_ROW_ALL_WILL_SERVE = 2
_ROW_INFECTED_CLAWS = 6
_ROW_DOOMED_BIDDING = 6
_ROW_DARK_TRANSFORMATION = 6
_ROW_ROTTEN_TOUCH = 7
_ROW_RAISE_ABOMINATION = 8
_ROW_HARBINGER_OF_DOOM = 8


def _rank_level(row, rank):
    return 9 + 5 * row + rank


def _capstone_text(text, capstone, last):
    """Capstone line under the rank text: grey below the last rank, plain on the last (S1 / S2 style)."""
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


def _aura(apply_aura, base_points=0, misc_value=0, trigger_spell=0, target=_TARGET_UNIT_CASTER):
    """An APPLY_AURA effect (on the caster unless `target` says otherwise)."""
    return Effect(type=EffectType.APPLY_AURA, base_points=base_points, implicit_target_a=target,
                  apply_aura=apply_aura, misc_value=misc_value, trigger_spell=trigger_spell)


def _passive_rank(spell_id, name, effects, icon, row, rank, description, note, proc_chance=None):
    """A talent rank spell: hidden passive (attributes 0x1D0), duration -1, self range, family 15, no family bits."""
    raw = _raw(
        description, level=_rank_level(row, rank), ProcChance=101 if proc_chance is None else proc_chance,
        **_chain_amplitudes(effects),
    )
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_TALENT_PASSIVE,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=-1, effects=effects, spell_icon_id=icon, notes=note, raw_overrides=raw,
    )


# =====================================================================================================================
# Festering Plague (203440, talent 60365, row 2): Plague Strike applies Festering Wounds
# =====================================================================================================================

# A flag carrier: nothing reads its effect, the Plague Strike script (spell_dk_plague_strike_unholy) tests
# HasAura(203440) and rolls the +1 / +2 wounds itself (FESTERING_PLAGUE_PLUS1_PCT / _PLUS2_PCT, x Proc Chance).
festering_plague_203440 = _passive_rank(
    203440, 'Festering Plague', [_aura(AuraType.DUMMY)], _ICON_FESTERING_PLAGUE, _ROW_FESTERING_PLAGUE, 1,
    'Your Plague Strike also infects the target with a Festering Wound, with a 25% chance to infect it with 1 more or '
    'a 5% chance to infect it with 2 more. Critical strikes infect it with 1 more. Up to 10 wounds.',
    'death-knight-rework S3a, Unholy doc "Festering Plague" (2,1), U8: hidden passive DUMMY carrier, the only rank. '
    'Pure flag: HasAura(203440) in spell_dk_plague_strike_unholy (one exclusive roll 25% +1 / 5% +2, x Proc Chance, '
    '+1 on a crit, cap 10). The tooltip numbers are the FESTERING_PLAGUE_* consts. SpellLevel 9 + 5 x 2 + 1.',
)

# =====================================================================================================================
# All Will Serve (203441-203442, talent 60366, row 2): minion damage 5 / 10%; rank 2 = Necromancy
# =====================================================================================================================

_NECROMANCY_CAPSTONE = (
    'Necromancy. Your Plague Strike no longer applies Festering Wounds and instead grants you 3 Necromantic Energy, up '
    'to 6, and its Unholy Rune returns as a Death Rune. Your Scourge Strike consumes 1 Necromantic Energy to raise a '
    'Lesser Ghoul, and no longer creates Death Runes.'
)
_ALL_WILL_SERVE_NOTE = (
    'death-knight-rework S3a, Unholy doc "All Will Serve" (2,3), U14 / U16: hidden passive, eff0 DUMMY stored 4 / 9 '
    '(value 5 / 10 = the minion damage percent, read with GetAmount() by GetAllWillServePct and the minion damage '
    'seam). Rank 2 (203442) is the Necromancy capstone: an APPLY_AURA passive so HasAura(203442) gates it (L4). '
    'SpellLevel 9 + 5 x 2 + rank.'
)
all_will_serve_203441 = _passive_rank(
    203441, 'All Will Serve', [_aura(AuraType.DUMMY, base_points=4)], _ICON_ALL_WILL_SERVE, _ROW_ALL_WILL_SERVE, 1,
    _capstone_text('Your undead minions deal 5% more damage.', _NECROMANCY_CAPSTONE, False), _ALL_WILL_SERVE_NOTE,
)
all_will_serve_203442 = _passive_rank(
    203442, 'All Will Serve', [_aura(AuraType.DUMMY, base_points=9)], _ICON_ALL_WILL_SERVE, _ROW_ALL_WILL_SERVE, 2,
    _capstone_text('Your undead minions deal 10% more damage.', _NECROMANCY_CAPSTONE, True), _ALL_WILL_SERVE_NOTE,
)

# =====================================================================================================================
# Infected Claws (203443-203444, talent 60367, row 6): the permanent ghoul's Claw infects with a Festering Wound
# =====================================================================================================================

_INFECTED_CLAWS_NOTE = (
    'death-knight-rework S3a, Unholy doc "Infected Claws" (6,0), U23: hidden passive, eff0 DUMMY stored 14 / 29 '
    '(value 15 / 30 = the chance percent, read with GetAmount() by DeathKnight::ApplyInfectedClaws / the pet aura '
    '203467 CheckProc, x the owner\'s Proc Chance). The owner-cast proc aura 203467 and the pet-spellbook display '
    '203468 are deathknight_unholy_b.py\'s. SpellLevel 9 + 5 x 6 + rank.'
)
infected_claws_203443 = _passive_rank(
    203443, 'Infected Claws', [_aura(AuraType.DUMMY, base_points=14)], _ICON_INFECTED_CLAWS, _ROW_INFECTED_CLAWS, 1,
    "Your ghoul's Claw has a 15% chance to infect the target with a Festering Wound. If you know Necromancy, it "
    'instead grants your ghoul 1 Shadow Infusion.', _INFECTED_CLAWS_NOTE,
)
infected_claws_203444 = _passive_rank(
    203444, 'Infected Claws', [_aura(AuraType.DUMMY, base_points=29)], _ICON_INFECTED_CLAWS, _ROW_INFECTED_CLAWS, 2,
    "Your ghoul's Claw has a 30% chance to infect the target with a Festering Wound. If you know Necromancy, it "
    'instead grants your ghoul 1 Shadow Infusion.', _INFECTED_CLAWS_NOTE,
)

# =====================================================================================================================
# Doomed Bidding (203445-203447, talent 60368, row 6): Death Coil has a chance to raise a Lesser Ghoul
# =====================================================================================================================

_DOOMED_BIDDING_NOTE = (
    'death-knight-rework S3a, Unholy doc "Doomed Bidding" (6,2), U24 / L3: hidden passive, eff0 DUMMY (the proc '
    'effect). Chain spell_proc row (procs_on -203445): CAST phase (1) on Death Coil d0 b13 (m.DEATH_COIL), once per '
    'non-triggered 47541 cast with no guard (a HIT row on d0 b13 would also match the 47632 / 47633 missiles and roll '
    'twice), magic-class ProcFlags POS | NEG (hostile Coil at an enemy, beneficial at the ghoul), Chance 0 = the '
    "rank's ProcChance 8 / 16 / 25 (native, Proc Chance scales it). spell_dk_doomed_bidding raises a Lesser Ghoul "
    "next to the Coil's target. SpellLevel 9 + 5 x 6 + rank."
)


def _doomed_bidding_rank(spell_id, rank, percent):
    return _passive_rank(
        spell_id, 'Doomed Bidding', [_aura(AuraType.DUMMY)], _ICON_DOOMED_BIDDING, _ROW_DOOMED_BIDDING, rank,
        f'Your Death Coil has an {percent}% chance to raise a Lesser Ghoul.' if percent == 8
        else f'Your Death Coil has a {percent}% chance to raise a Lesser Ghoul.',
        _DOOMED_BIDDING_NOTE, proc_chance=percent,
    )


doomed_bidding_203445 = _doomed_bidding_rank(203445, 1, 8)
doomed_bidding_203446 = _doomed_bidding_rank(203446, 2, 16)
doomed_bidding_203447 = _doomed_bidding_rank(203447, 3, 25)
procs_on(
    -203445, proc_flags=_PROC_COIL_ANY, family_name=_SPELLFAMILY_DEATHKNIGHT, family_mask=(m.DEATH_COIL, 0, 0),
    spell_type_mask=_PROC_SPELL_TYPE_ALL, spell_phase_mask=_PROC_SPELL_PHASE_CAST, chance=0.0,
)
scripted_by(-203445, 'spell_dk_doomed_bidding')

# =====================================================================================================================
# Dark Transformation (203448, talent 60369, row 6): the P0 item 7 shape, off the GCD, greyed by the 203465 marker
# =====================================================================================================================

# Three effects, all on the pet (TARGET_UNIT_PET): eff0 TRANSFORM (56) into creature 17898 (display 12818), eff1 aura
# 79 +80% all schools, eff2 the DUMMY proc effect the cleave rides on. spell_proc row below (actor = the pet): melee
# auto attacks and melee-class spells (the Claw 47468, family 0); spell_dk_dark_transformation's aura half
# filters to the melee swing / Claw and casts the cleave 203466 once per hit. CasterAuraSpell is the visible marker
# 203465 (the client greys the button without it, bug 448); the linked spell removes it on cast. No IS_ABILITY (the
# attribute would drop the core haste), off the GCD (no StartRecovery), no cooldown, no cost: the five Shadow
# Infusion stacks are the price (spell_dk_dark_transformation CheckCast / OnCast). SLA 30760 / talent 60369 are
# deathknight_talents.py's. SpellLevel 9 + 5 x 6 + 1.
dark_transformation_203448 = spell(
    id=203448, name='Dark Transformation', school=School.NORMAL, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=45.0, duration_ms=25000,
    effects=[
        _aura(AuraType.TRANSFORM, misc_value=_NPC_TRANSFORM_ABOMINATION, target=_TARGET_UNIT_PET),
        _aura(AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=79, misc_value=_MISC_ALL_SCHOOLS,
              target=_TARGET_UNIT_PET),
        _aura(AuraType.DUMMY, target=_TARGET_UNIT_PET),
    ],
    spell_icon_id=_ICON_DARK_TRANSFORMATION,
    notes=(
        'death-knight-rework S3a (U22, Unholy doc "Dark Transformation", 6,3): talent castable on the P0 item 7 shape '
        '(p0-spike-ref/deathknight_p0_spike.py:383-408, passed). Off the GCD, instant, no cost, no cooldown, 25 s '
        '[tune], RangeIndex 36 (stock Ghoul Frenzy 63560, a pet target). eff0 TRANSFORM misc 17898 (display 12818), '
        'eff1 MOD_DAMAGE_PERCENT_DONE (79) misc 127 stored 79 = +80%, eff2 DUMMY: all TARGET_UNIT_PET. '
        'CasterAuraSpell = 203465 (the marker); linked_spell(203448, -203465, 0) removes it on cast. spell_proc row '
        '(procs_on on this id, actor = the pet): ProcFlags 0x14 (melee auto attack + melee-class spell), no family, '
        'HIT phase, Chance 100, DisableEffectsMask 0x3 (RETUNE: eff0 TRANSFORM is a breakable CC on a proc row); '
        'the aura script filters to the swing / Claw. NO IS_ABILITY, no family bits. '
        'Non-passive visible aura, number-free aura text. SpellLevel 40 = 9 + 5 x 6 + 1.'
    ),
    raw_overrides=_raw(
        'Your Death Coils grant your ghoul Shadow Infusion, stacking up to 5. At 5 stacks, transform your ghoul into '
        'a monstrosity for $d, increasing its damage by $s2% and causing its attacks to hit all enemies within 8 '
        'yards for 50% damage.',
        'Transformed into a monstrosity. Deals more damage, and its attacks hit nearby enemies.', level=40,
        CasterAuraSpell=dark_transformation_ready_203465.id,
        **_chain_amplitudes([None] * 3),
    ),
)
linked_spell(dark_transformation_203448.id, -dark_transformation_ready_203465.id, type=0,
             comment='Dark Transformation consumes its ready marker (S3a U22)')
# RETUNE 2026-10-25 (S3b-2-DIAG Q1): DisableEffectsMask 0x3. With a spell_proc row the engine checks every effect of
# the aura, and eff0 TRANSFORM is a breakable CC there (SpellAuraEffects.cpp CheckEffectProc /
# HandleBreakableCCAuraProc, amount 0): the ghoul's first swing or Claw removed the whole aura. Only eff2 (the DUMMY
# the cleave script reads) procs.
procs_on(
    dark_transformation_203448, proc_flags=_PROC_FLAG_DONE_MELEE_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS,
    spell_type_mask=_PROC_SPELL_TYPE_ALL, spell_phase_mask=_PROC_SPELL_PHASE_HIT, chance=100.0,
    disable_effects_mask=0x3,
)
scripted_by(dark_transformation_203448, 'spell_dk_dark_transformation')

# =====================================================================================================================
# Rotten Touch (203449-203451, talent 60370, row 7): Plague Strike arms the next Death Coil to burst 2 wounds
# =====================================================================================================================

_ROTTEN_TOUCH_NOTE = (
    'death-knight-rework S3a, Unholy doc "Rotten Touch" (7,0), U24 / L3: hidden passive, eff0 PROC_TRIGGER_SPELL -> '
    'the buff 203462 (deathknight_unholy_b.py: a self buff, one charge, 20 s, a second proc refreshes it). Chain '
    'spell_proc row (procs_on -203449): CAST phase (1) on Plague Strike d0 b0 (m.PLAGUE_STRIKE), melee-class '
    "ProcFlags 0x10, once per non-triggered cast (the Threat of Thassarian off-hand copy is triggered), Chance 0 = "
    "the rank's ProcChance 5 / 10 / 15 (native, Proc Chance scales it). The Death Coil scripts consume the buff "
    '(spell_dk_death_coil_unholy arms, spell_dk_death_coil_damage_unholy bursts 2). SpellLevel 9 + 5 x 7 + rank.'
)


def _rotten_touch_rank(spell_id, rank, percent):
    return _passive_rank(
        spell_id, 'Rotten Touch',
        [_aura(AuraType.PROC_TRIGGER_SPELL, trigger_spell=rotten_touch_buff_203462.id)],
        _ICON_ROTTEN_TOUCH, _ROW_ROTTEN_TOUCH, rank,
        f'Your Plague Strike has a {percent}% chance to make your next Death Coil within 20 sec burst 2 Festering '
        'Wounds on its target.',
        _ROTTEN_TOUCH_NOTE, proc_chance=percent,
    )


rotten_touch_203449 = _rotten_touch_rank(203449, 1, 5)
rotten_touch_203450 = _rotten_touch_rank(203450, 2, 10)
rotten_touch_203451 = _rotten_touch_rank(203451, 3, 15)
procs_on(
    -203449, proc_flags=_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS, family_name=_SPELLFAMILY_DEATHKNIGHT,
    family_mask=(m.PLAGUE_STRIKE, 0, 0), spell_type_mask=_PROC_SPELL_TYPE_ALL,
    spell_phase_mask=_PROC_SPELL_PHASE_CAST, chance=0.0,
)

# =====================================================================================================================
# Raise Abomination (203452, talent 60371, row 8): 40 Runic Power, 1 min, a 20 s guardian wreathed in a putrid cloud
# =====================================================================================================================

# SUMMON of creature 300321 (props 61: ALLY / GUARDIAN, one summon) at TARGET_DEST_CASTER_SUMMON (beside the Death
# Knight, front left, no radius), 20 s. 40 Runic Power (PowerType 6, ManaCost 400), 60 s DBC cooldown (Cooldown Haste
# qualifies, >= 30 s), GCD 133 / 1500, magic class (the core hastes the GCD), NO IS_ABILITY, self range, no family
# bits. A summon-only cast: the AI (npc_dk_abomination) applies the cloud 203472 and the ward 203474 on spawn. The
# tooltip is the doc text minus its cost and cooldown sentences; the cloud number is the tick's potency (9, A6's
# 203473). SLA 30761 / talent 60371 are deathknight_talents.py's. SpellLevel 9 + 5 x 8 + 1.
raise_abomination_203452 = spell(
    id=203452, name='Raise Abomination', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=60000,
    category_cooldown_ms=0, power_type=PowerType.RUNIC_POWER, mana_cost=400, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=20000,
    effects=[
        Effect(type=EffectType.SUMMON, implicit_target_a=_TARGET_DEST_CASTER_SUMMON, misc_value=300321),
    ],
    spell_icon_id=_ICON_RAISE_ABOMINATION,
    notes=(
        'death-knight-rework S3a (U21, Unholy doc "Raise Abomination", 8,1): talent castable. SUMMON creature '
        '300321 (EffectMiscValueB 61 = ALLY / GUARDIAN, numSummons 1) at TARGET_DEST_CASTER_SUMMON (32), 20 s, self '
        'range. 40 Runic Power (ManaCost 400), 60 s cooldown, GCD 133 / 1500, magic class, NO IS_ABILITY, no family '
        'bits. A summon-only cast (no TargetInfo): scripts use AfterCast, never AfterHit (D3). Tooltip = the doc text '
        'minus the cost and cooldown sentences, the cloud number from the tick 203473 potency. SpellLevel 50 = 9 + '
        '5 x 8 + 1. SLA 30761 / talent 60371 are deathknight_talents.py\'s.'
    ),
    raw_overrides=_raw(
        'Raise an Abomination to fight at your side for $d. It is wreathed in a putrid cloud that deals '
        + pot_text(putrid_cloud_tick_203473) + ' Shadow damage every 1 sec to all enemies within 8 yards, and infects '
        'each enemy inside with a Festering Wound every 3 sec. If you know Necromancy, the cloud applies no wounds.',
        level=50, gcd=True, magic=True, EffectMiscValueB_1=_SUMMON_PROPS_GUARDIAN, **_chain_amplitudes([None]),
    ),
)

# =====================================================================================================================
# Harbinger of Doom (203453-203455, talent 60372, row 8): a main-hand swing makes the next Death Coil free
# =====================================================================================================================

_HARBINGER_NOTE = (
    'death-knight-rework S3a, Unholy doc "Harbinger of Doom" (8,3), U24 / L24: hidden passive, eff0 '
    'PROC_TRIGGER_SPELL -> the buff 203463 (a charged SPELLMOD_COST -100% on Death Coil, no spell_proc row of its '
    'own). Chain spell_proc row (procs_on -203453): ProcFlags 0x400000 (DONE_MAINHAND_ATTACK) ALONE, phase 0, no '
    'family: the main-hand flag rides on both the main-hand swing (0x4 | 0x400000) and main-hand melee-class spells '
    '(0x10 | 0x400000), but a row without a spell-phase mask is rejected for any event whose type mask carries a '
    'spell flag (SpellMgr.cpp CanSpellTriggerProcOnEvent, REQ_SPELL_PHASE_PROC_FLAG_MASK), so only the main-hand '
    'auto attack procs: not the off hand, not Blood-Caked Strike, not Plague Strike or any strike. Chance 0 = the '
    "rank's ProcChance 5 / 10 / 15 (native, Proc Chance scales it). SpellLevel 9 + 5 x 8 + rank."
)


def _harbinger_rank(spell_id, rank, percent):
    return _passive_rank(
        spell_id, 'Harbinger of Doom',
        [_aura(AuraType.PROC_TRIGGER_SPELL, trigger_spell=harbinger_of_doom_buff_203463.id)],
        _ICON_HARBINGER_OF_DOOM, _ROW_HARBINGER_OF_DOOM, rank,
        f'Your main hand auto attacks have a {percent}% chance to make your next Death Coil within 20 sec cost no '
        'Runic Power.',
        _HARBINGER_NOTE, proc_chance=percent,
    )


harbinger_of_doom_203453 = _harbinger_rank(203453, 1, 5)
harbinger_of_doom_203454 = _harbinger_rank(203454, 2, 10)
harbinger_of_doom_203455 = _harbinger_rank(203455, 3, 15)
procs_on(-203453, proc_flags=_PROC_FLAG_DONE_MAINHAND_ATTACK, spell_phase_mask=0, chance=0.0)


_C = [
    ('FESTERING_WOUND_MAX_STACKS', 10, 'Festering Wound stack cap; a wound past it bursts at once (overflow).'),
    ('FESTERING_WOUND_RP_PER_WOUND', 3, 'Runic Power per burst wound (own-cast sources only).'),
    ('FESTERING_PLAGUE_PLUS1_PCT', 25, 'Festering Plague: chance percent of +1 wound on Plague Strike (x Proc Chance).'),
    ('FESTERING_PLAGUE_PLUS2_PCT', 5, 'Festering Plague: chance percent of +2 wounds on Plague Strike (x Proc Chance).'),
    ('WOUND_BURST_MIN', 2, 'Scourge Strike bursts max(this, stacks / 2) wounds, capped at the stack.'),
    ('WOUND_EXPLOSION_PCT', 30, 'Death explosion: percent of a wound burst per wound.'),
    ('WOUND_EXPLOSION_TARGETS', 5, 'Death explosion target cap.'),
    ('SCOURGE_STRIKE_DEATH_RUNE_PCT', 33, 'Scourge Strike: base chance percent per plain rune spent to return a ready Death Rune.'),
    ('SCOURGE_STRIKE_DISEASE_PCT', 12, 'Scourge Strike Shadow part: percent of the hit per own disease.'),
    ('NECROMANTIC_ENERGY_PER_STRIKE', 3, 'Necromancy: Necromantic Energy per Plague Strike.'),
    ('NECROMANTIC_ENERGY_MAX', 6, 'Necromancy: Necromantic Energy stack cap.'),
    ('NECROMANCY_RP', 0, 'Necromancy: Runic Power per energy-spending Scourge Strike (RETUNE 2026-10-25: was 10).'),
    ('LESSER_GHOUL_CAP', 8, 'Lesser Ghoul cap; the oldest is replaced.'),
    ('LESSER_GHOUL_RANGE_YARDS', 40, 'Corpse Explosion: Lesser Ghoul search range.'),
    ('CORPSE_EXPLOSION_CORPSE_RANGE_YARDS', 30, 'Corpse Explosion: corpse fallback search range.'),
    ('SHADOW_INFUSION_STACKS', 5, 'Shadow Infusion stacks needed for Dark Transformation.'),
    ('DARK_TRANSFORMATION_CLEAVE_PCT', 50, 'Dark Transformation cleave: percent of the unmitigated hit.'),
    ('ABOMINATION_WOUND_EVERY_TICKS', 3, 'Putrid Cloud: a wound every this many ticks per target.'),
    ('GARGOYLE_NECROMANCY_PCT', 3, 'Gargoyle Necromancy: minion damage percent per stack.'),
    ('GARGOYLE_NECROMANCY_MAX_STACKS', 10, 'Gargoyle Necromancy stack cap.'),
    ('GARGOYLE_RP_PER_RAMP_STACK', 10, 'Gargoyle ramp: Runic Power spent per +1% stack.'),
    ('GARGOYLE_WINDOW_MS', 20000, 'Gargoyle strike window before it flies away.'),
    ('UNHOLY_BLIGHT_SHARE_PCT', 10, 'Unholy Blight: percent of the Death Coil damage dealt over the DoT.'),
]
for _name, _value, _doc in _C:
    globals()[_name] = const(_name, _value, _doc)
