"""
Warrior - S3 Fury delta, rank-row half (agent A2b): the eleven minted talent rank chains 204653-204678 and the
first declarations of the stock Fury rank rows S3 rewrites (Cruelty, Unbridled Wrath + its energize, Blood Craze,
Enrage, the Flurry ranks and the two Flurry buffs A1's file does not hold), plus the `procs_on` /
`remove_spell_proc` rows whose key is one of these ranks.

Source of truth: docs/reworks/warrior-fury-rework.md (talent tooltips verbatim; capstone clauses),
.agents/plans/warrior-rework/warrior-rework.S3-WP-BRIEF.md (section 6 frozen variable names, B-R3),
warrior-rework.S3-HANDOFF.md (D3, D10-D14, D16, D18-D20, D24, D26-D29, D36, D38, D39) and
warrior-rework.S3-0VERIFY-A.md (difference 4: the Unbridled Wrath ranks must not carry stock's weapon gate;
difference 14: bp = value - 1). Row shapes are S2's
(`warrior_arms.py`): `_talent_rank` / `_rank_raw` for minted ranks, the Trauma shape for first-declared stock rows.

What lives elsewhere (never edited from here): the mechanics spells 204630-204652 / 204679 / 204680, 23885, every
`scripted_by` / `unbind_script` / `const()` and the non-rank `procs_on` rows are `warrior_fury.py` (A2a); the stock
rows A1 edits in place (Armored to the Teeth, Commanding Presence, Improved Execute / Cleave / Whirlwind, Intensify
Rage, Bloodsurge, Unending Fury, Flurry buff 12966, Impale) are `warrior_trigger_spells.py`; the grid is
`warrior_talents.py` (A3), which imports the variables below by their frozen names. Trigger spells are referenced by
numeric id (`trigger_spell=204637`), never by importing another new file's variables.

Conventions: every carrier is a DUMMY effect whose base points are the value minus one (die sides 1); ranks that
only carry a value have ProcTypeMask / ProcChance 0 (no auto-generated proc entry); ranks that proc carry the DBC
ProcTypeMask and a ProcChance the explicit `spell_proc` row inherits (Chance 0 in a row means "the DBC chance").
"""

from lib.dsl import AuraType, Effect, EffectType, SpellModOp, School
from lib.dsl.registry import pot_text, procs_on, remove_spell_proc, spell

from ._tooltips import _desc

try:  # the Dance of Death heal is A2a's spell: only its tooltip value is read from it (pot_text needs the object)
    from .warrior_fury import dance_of_death_heal_204640 as _dance_of_death_heal
except ImportError:  # warrior_fury.py not written yet (parallel authoring); the check below then fails loudly
    _dance_of_death_heal = None

# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h, decoded) ----
_TALENT_RANK_ATTRIBUTES = 464               # 0x1D0: the passive talent-rank shape (Resolve, S2's _talent_rank)
_SPELLFAMILY_WARRIOR = 4
_TARGET_UNIT_CASTER = 1
_RANGE_INDEX_SELF = 1

# ---- Family bits the Fury ranks read or procs key on (FAMILY-BITS section 2; fury-data section 7.4) ----
_HEROIC_STRIKE_D0 = 0x40
_CLEAVE_D0 = 0x400000
_BLOODTHIRST_D1 = 0x400
_PROC_PHASE_CAST = 0x1
_PROC_PHASE_HIT = 0x2

# ---- proc flags / hit masks (src/server/game/Spells/SpellMgr.h) ----
_PROC_KILL = 0x2                            # PROC_FLAG_KILL
_PROC_MELEE_SWING_AND_ABILITY = 0x14        # DONE_MELEE_AUTO_ATTACK (0x4) | DONE_SPELL_MELEE_DMG_CLASS (0x10)
_PROC_MELEE_ABILITY = 0x10                  # DONE_SPELL_MELEE_DMG_CLASS
_PROC_ATTR_REQ_EXP_OR_HONOR = 0x1           # PROC_ATTR_REQ_EXP_OR_HONOR (a kill must yield experience or honor)
_PROC_SPELL_TYPE_DAMAGE = 0x1               # PROC_SPELL_TYPE_DAMAGE
_PROC_HIT_CRITICAL = 0x2                    # PROC_HIT_CRITICAL

# ---- Stock icons (spell_icon_names.csv; V replaces the minted ones, handoff D45) ----
_ICON_DANCE_OF_DEATH = 3139                 # Spell_Shadow_Skull
_ICON_CRUELTY = 514
_ICON_MERCILESS = 1651                      # INV_Misc_Bone_OrcSkull_01
_ICON_FRENZIED_BLOWS = 2023                 # Ability_DualWieldSpecialization (Dual Wield Specialization keeps 533)
_ICON_UNBRIDLED_WRATH = 689
_ICON_BLOOD_CRAZE = 215
_ICON_ENRAGE = 95
_ICON_QUICK_EXECUTION = 2285                # Ability_Hunter_RapidKilling
_ICON_FRESH_MEAT = 2774                     # Ability_Warrior_BloodBath
_ICON_IMPROVED_BLOODTHIRST = 2021           # Spell_Nature_UnleashedRage
_ICON_FLURRY = 108
_ICON_UNSHACKLED_FURY = 1662                # Racial_Orc_BerserkerStrength
_ICON_DEATHMAKER = 3201                     # INV_Bone_Skull_04
_ICON_SHREDDING_BLOWS = 565                 # Ability_Warrior_Sunder
_ICON_WILL_OF_THE_BERSERKER = 1661          # Racial_Troll_Berserk
_ICON_BLOOD_RUSH = 86                       # Ability_Racial_BloodRage


def _raw(description, **extra):
    """The passive minted-rank frame (S2's `_rank_raw`): SpellClassSet 4, no equipment gate, SpellLevel 1, self range,
    instant cast, chain amplitudes 1.0. ProcChance 0 unless `extra` says otherwise: a rank that procs passes its own."""
    raw = {
        'SpellClassSet': _SPELLFAMILY_WARRIOR,
        'EquippedItemClass': -1,
        'CastingTimeIndex': 1,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'SpellLevel': 1,
        'SpellPriority': 50,
        'ProcTypeMask': 0,
        'ProcChance': 0,
        'RangeIndex': _RANGE_INDEX_SELF,
        'NameSubtext_Lang_enUS': '',
        'Description_Lang_enUS': description,
    }
    raw.update(extra)
    return raw


def _talent_rank(spell_id, name, effects, icon, notes, raw):
    """A passive talent-rank spell: no cooldown, no cost, self range, 0.0 yd (Resolve shape)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_TALENT_RANK_ATTRIBUTES, cast_time_ms=0,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0, effects=effects,
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _self_aura(aura, **kwargs):
    return Effect(type=EffectType.APPLY_AURA, apply_aura=aura, implicit_target_a=_TARGET_UNIT_CASTER, **kwargs)


def _carrier(base_points):
    """A DUMMY value carrier the C++ reads (value = base_points + 1)."""
    return _self_aura(AuraType.DUMMY, base_points=base_points)


def _spellmod_pct(op, base_points):
    return _self_aura(AuraType.ADD_PCT_MODIFIER, base_points=base_points, misc_value=int(op))


def _stock_raw(rank, description, **extra):
    """The stock row's raw columns (Trauma shape): Lang masks as the pulled rows, 'Rank N' subtext, chain
    amplitudes, then `extra` (applied last)."""
    raw = {
        'CastingTimeIndex': 1,
        'RangeIndex': _RANGE_INDEX_SELF,
        'EquippedItemClass': -1,
        'SpellPriority': 50,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': f'Rank {rank}',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': description,
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
    }
    raw.update(extra)
    return raw


def _stock(spell_id, name, effects, icon, notes, raw, *, attributes=_TALENT_RANK_ATTRIBUTES, duration_ms=None):
    """A first-declared stock row: physical, no cost, no cooldown, 0.0 yd, `duration_ms` only where the stock row had
    a DurationIndex."""
    kwargs = {} if duration_ms is None else {'duration_ms': duration_ms}
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=attributes, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0, effects=effects,
        spell_icon_id=icon, notes=notes, raw_overrides=raw, **kwargs,
    )


# =====================================================================================================================
# Dance of Death 204653-204655  -- D26, doc "Dance of Death" (capstone on rank 3)
# =====================================================================================================================
# eff0 DUMMY carrier crit 2 / 4 / 6% (bp 1 / 3 / 5), read by spell_warr_dance_of_death (-204653), which casts the crit
# buff 204639 with the carrier as its final value and, on rank 3, the heal 204640 + the Charge reset. One spell_proc
# row for the whole chain: PROC_FLAG_KILL, REQ_EXP_OR_HONOR (an enemy that yields no experience / honor never
# procs); KillCredit::OnKill already pays assisters through ProcSkillsAndAuras(PROC_FLAG_KILL). Deterministic: the
# DBC ProcChance is 100 (the row inherits it), ProcTypeMask 0x2 = the row's flag.
def _dance_of_death_capstone():
    if _dance_of_death_heal is None:
        raise ImportError('warrior_fury.py does not define dance_of_death_heal_204640 yet (A2a)')
    return ('Killing an enemy heals you for ' + pot_text(_dance_of_death_heal) +
            ' and resets the cooldown of your Charge. The healing can occur once every 5 sec.')


def _dance_of_death(spell_id, rank, percent):
    return _talent_rank(
        spell_id, 'Dance of Death', [_carrier(percent - 1)], _ICON_DANCE_OF_DEATH,
        f'warrior-rework S3 A2b (D26, doc "Dance of Death"): rank {rank}. eff0 DUMMY carrier {percent}% crit (bp '
        f'{percent - 1}), read by spell_warr_dance_of_death (-204653). DBC ProcTypeMask 0x2 / ProcChance 100; the '
        f'spell_proc row is -204653 (PROC_FLAG_KILL, REQ_EXP_OR_HONOR). Capstone via _desc.',
        _raw(_desc(f'After you kill an enemy, your critical strike chance is increased by {percent}% for 8 sec.',
                   _dance_of_death_capstone(), last=(rank == 3)), ProcTypeMask=_PROC_KILL, ProcChance=100),
    )


dance_of_death_204653 = _dance_of_death(204653, 1, 2)
dance_of_death_204654 = _dance_of_death(204654, 2, 4)
dance_of_death_204655 = _dance_of_death(204655, 3, 6)

procs_on(-204653, proc_flags=_PROC_KILL, attributes_mask=_PROC_ATTR_REQ_EXP_OR_HONOR)


# =====================================================================================================================
# Merciless 204656-204658  -- D18, doc "Merciless" (capstone on rank 3)
# =====================================================================================================================
# eff0 DUMMY carrier 3 / 6 / 9% (bp 2 / 5 / 8), read by Warrior::GetMercilessMultiplier. No proc. The capstone
# (Rampage free while Recklessness is up) is the Recklessness AuraScript adding / removing 204647 when rank 3 is held.
_MERCILESS_CAPSTONE = 'While Recklessness is active, Rampage costs no rage.'


def _merciless(spell_id, rank, percent):
    return _talent_rank(
        spell_id, 'Merciless', [_carrier(percent - 1)], _ICON_MERCILESS,
        f'warrior-rework S3 A2b (D18, doc "Merciless"): rank {rank}. eff0 DUMMY carrier {percent}% (bp '
        f'{percent - 1}), read by Warrior::GetMercilessMultiplier (x2 while Enraged, Berserker Stance, target below '
        f'35%). ProcTypeMask / ProcChance 0. Capstone via _desc.',
        _raw(_desc(f'While in Berserker Stance, your damage against targets below 35% health is increased by '
                   f'{percent}%. This bonus is doubled while you are Enraged.', _MERCILESS_CAPSTONE,
                   last=(rank == 3))),
    )


merciless_204656 = _merciless(204656, 1, 3)
merciless_204657 = _merciless(204657, 2, 6)
merciless_204658 = _merciless(204658, 3, 9)


# =====================================================================================================================
# Frenzied Blows 204659-204660  -- D19, doc "Frenzied Blows" (capstone on rank 2)
# =====================================================================================================================
# eff0 ADD_PCT_MODIFIER DAMAGE +5 / 10% (bp 4 / 9) on Heroic Strike (d0 0x40) | Cleave (d0 0x400000), named dword
# EffectSpellClassMaskA_1. The capstone off-hand strike is spell_warr_hs_cleave_fury's (strikes 204633 / 204634).
_FRENZIED_BLOWS_CAPSTONE = 'While you are Enraged, your Heroic Strike and Cleave also strike with your off-hand weapon.'


def _frenzied_blows(spell_id, rank, percent):
    return _talent_rank(
        spell_id, 'Frenzied Blows', [_spellmod_pct(SpellModOp.DAMAGE, percent - 1)], _ICON_FRENZIED_BLOWS,
        f'warrior-rework S3 A2b (D19, doc "Frenzied Blows"): rank {rank}. eff0 ADD_PCT_MODIFIER DAMAGE +{percent}% '
        f'(bp {percent - 1}) on Heroic Strike | Cleave (EffectSpellClassMaskA_1 = d0 0x400040). ProcTypeMask / '
        f'ProcChance 0. Capstone via _desc.',
        _raw(_desc(f'Increases the damage of your Heroic Strike and Cleave by {percent}%.', _FRENZIED_BLOWS_CAPSTONE,
                   last=(rank == 2)),
             EffectSpellClassMaskA_1=_HEROIC_STRIKE_D0 | _CLEAVE_D0),
    )


frenzied_blows_204659 = _frenzied_blows(204659, 1, 5)
frenzied_blows_204660 = _frenzied_blows(204660, 2, 10)


# =====================================================================================================================
# Quick Execution 204661-204663  -- D13, doc "Quick Execution" (capstone on rank 3)
# =====================================================================================================================
# eff0 aura 193 HASTE_ALL +1 / 2 / 3% (bp 0 / 1 / 2): haste that also shortens the global cooldown and raises rage
# (Q8). Rank 3 eff1 PROC_TRIGGER_SPELL -> Cadence 204642 on every Bloodthirst hit: DBC ProcTypeMask 0x10 / ProcChance
# 100, spell_proc = family 4, Bloodthirst d1 0x400, HIT phase (below). Ranks 1-2 carry no proc.
_QUICK_EXECUTION_CAPSTONE = ('Your Bloodthirst grants Cadence, increasing your haste by 1% for 12 sec, stacking up to '
                             '3 times.')


def _quick_execution(spell_id, rank):
    effects = [_self_aura(AuraType.HASTE_ALL, base_points=rank - 1)]
    extra = {}
    if rank == 3:
        effects.append(_self_aura(AuraType.PROC_TRIGGER_SPELL, trigger_spell=204642))
        extra = {'ProcTypeMask': _PROC_MELEE_ABILITY, 'ProcChance': 100}
    return _talent_rank(
        spell_id, 'Quick Execution', effects, _ICON_QUICK_EXECUTION,
        f'warrior-rework S3 A2b (D13, doc "Quick Execution"): rank {rank}. eff0 aura 193 HASTE_ALL +{rank}% (bp '
        f'{rank - 1}; cast + attack speed, shortens the GCD, Q8)' +
        (', eff1 PROC_TRIGGER_SPELL -> Cadence 204642 (spell_proc: Bloodthirst d1 0x400, HIT phase). Capstone via '
         '_desc.' if rank == 3 else '. No proc on this rank. Capstone via _desc.'),
        _raw(_desc(f'Increases your haste by {rank}%.', _QUICK_EXECUTION_CAPSTONE, last=(rank == 3)), **extra),
    )


quick_execution_204661 = _quick_execution(204661, 1)
quick_execution_204662 = _quick_execution(204662, 2)
quick_execution_204663 = _quick_execution(204663, 3)

# D13: each Bloodthirst hit (family 4, d1 0x400, HIT phase) grants Cadence; the rank's DBC chance (100) is inherited.
procs_on(204663, proc_flags=_PROC_MELEE_ABILITY, family_name=_SPELLFAMILY_WARRIOR,
         family_mask=(0, _BLOODTHIRST_D1, 0), spell_phase_mask=_PROC_PHASE_HIT)


# =====================================================================================================================
# Fresh Meat 204664-204665  -- D10, doc "Fresh Meat"
# =====================================================================================================================
# eff0 DUMMY carrier 90 / 80 (bp 89 / 79 = the health threshold %), read by the Bloodthirst dispatcher branch.
def _fresh_meat(spell_id, rank, percent):
    return _talent_rank(
        spell_id, 'Fresh Meat', [_carrier(percent - 1)], _ICON_FRESH_MEAT,
        f'warrior-rework S3 A2b (D10, doc "Fresh Meat"): rank {rank}. eff0 DUMMY carrier {percent} (bp {percent - 1}) '
        f'= the health threshold, read by the Bloodthirst dispatcher branch (adds 204649). ProcTypeMask / '
        f'ProcChance 0.',
        _raw(f'Your Bloodthirst always critically strikes targets above {percent}% health.'),
    )


fresh_meat_204664 = _fresh_meat(204664, 1, 90)
fresh_meat_204665 = _fresh_meat(204665, 2, 80)


# =====================================================================================================================
# Improved Bloodthirst 204666-204667  -- D12, doc "Improved Bloodthirst"
# =====================================================================================================================
# eff0 DUMMY carrier 3 / 6 extra rage (bp 2 / 5), read by Warrior::OnBloodthirstHit (Bloodthirst has no energize
# effect: D9, so no EFFECT3 SpellMod). The stock Improved Berserker Rage proc row -20500 is retired in warrior_fury.py.
def _improved_bloodthirst(spell_id, rank, rage):
    return _talent_rank(
        spell_id, 'Improved Bloodthirst', [_carrier(rage - 1)], _ICON_IMPROVED_BLOODTHIRST,
        f'warrior-rework S3 A2b (D12, doc "Improved Bloodthirst"): rank {rank}. eff0 DUMMY carrier {rage} extra rage '
        f'(bp {rage - 1}), read by Warrior::OnBloodthirstHit. ProcTypeMask / ProcChance 0.',
        _raw(f'Your Bloodthirst generates {rage} additional rage.'),
    )


improved_bloodthirst_204666 = _improved_bloodthirst(204666, 1, 3)
improved_bloodthirst_204667 = _improved_bloodthirst(204667, 2, 6)


# =====================================================================================================================
# Unshackled Fury 204668-204670  -- doc "Unshackled Fury" (capstone on rank 3)
# =====================================================================================================================
# eff0 DUMMY carrier +2 / 4 / 6% Enrage bonus (bp 1 / 3 / 5), read by Warrior::GetEnrageBonusPct; rank 3 also adds
# Mastery 1:1 (the capstone, same function). No proc.
_UNSHACKLED_FURY_CAPSTONE = 'Mastery further increases the physical damage bonus of your Enrage.'


def _unshackled_fury(spell_id, rank):
    percent = rank * 2
    return _talent_rank(
        spell_id, 'Unshackled Fury', [_carrier(percent - 1)], _ICON_UNSHACKLED_FURY,
        f'warrior-rework S3 A2b (doc "Unshackled Fury"): rank {rank}. eff0 DUMMY carrier +{percent}% Enrage bonus (bp '
        f'{percent - 1}), read by Warrior::GetEnrageBonusPct (rank 3 adds Mastery). ProcTypeMask / ProcChance 0. '
        f'Capstone via _desc.',
        _raw(_desc(f'Increases the physical damage bonus of your Enrage by {percent}%.', _UNSHACKLED_FURY_CAPSTONE,
                   last=(rank == 3))),
    )


unshackled_fury_204668 = _unshackled_fury(204668, 1)
unshackled_fury_204669 = _unshackled_fury(204669, 2)
unshackled_fury_204670 = _unshackled_fury(204670, 3)


# =====================================================================================================================
# Deathmaker 204671-204672  -- D16, doc "Deathmaker"
# =====================================================================================================================
# eff0 aura 42 PROC_TRIGGER_SPELL -> the buff 204638 (A2a), DBC ProcTypeMask 0x14, ProcChance 3 / 6 (the row inherits
# it per rank). spell_proc -204671: melee swings and melee ability casts, CAST phase (abilities roll once per cast),
# family 4 with an empty mask (a family-0 row would roll on every melee cast of every class, S2 R10); the AuraScript
# spell_warr_deathmaker (bound in warrior_fury.py) gates it with Warrior::IsStrikeCast.
def _deathmaker(spell_id, rank, chance):
    return _talent_rank(
        spell_id, 'Deathmaker', [_self_aura(AuraType.PROC_TRIGGER_SPELL, trigger_spell=204638)], _ICON_DEATHMAKER,
        f'warrior-rework S3 A2b (D16, doc "Deathmaker"): rank {rank}. eff0 PROC_TRIGGER_SPELL -> 204638, DBC '
        f'ProcTypeMask 0x14, ProcChance {chance} [tune]; spell_proc -204671 (flags 0x14, family 4, empty mask, CAST '
        f'phase).',
        _raw(f'Your melee hits have a {chance}% chance to make your next Execute usable regardless of the target\'s '
             f'health. Lasts 10 sec.', ProcTypeMask=_PROC_MELEE_SWING_AND_ABILITY, ProcChance=chance),
    )


deathmaker_204671 = _deathmaker(204671, 1, 3)
deathmaker_204672 = _deathmaker(204672, 2, 6)

procs_on(-204671, proc_flags=_PROC_MELEE_SWING_AND_ABILITY, family_name=_SPELLFAMILY_WARRIOR,
         spell_phase_mask=_PROC_PHASE_CAST)


# =====================================================================================================================
# Shredding Blows 204673-204675  -- D27, doc "Shredding Blows"
# =====================================================================================================================
# The Flurry shape: eff0 aura 42 -> the rank's buff 204644 / 204645 / 204646 (A2a), DBC ProcTypeMask 0x14,
# ProcChance 100. spell_proc (the GRANT row, B-R3): flags 0x14, damage spells only, HIT phase, critical hits (any
# melee crit). The consuming rows on the buffs are A2a's.
def _shredding_blows(spell_id, rank, buff, percent):
    return _talent_rank(
        spell_id, 'Shredding Blows', [_self_aura(AuraType.PROC_TRIGGER_SPELL, trigger_spell=buff)],
        _ICON_SHREDDING_BLOWS,
        f'warrior-rework S3 A2b (D27, doc "Shredding Blows"): rank {rank}. eff0 PROC_TRIGGER_SPELL -> {buff} '
        f'({percent}% armor ignored), DBC ProcTypeMask 0x14 / ProcChance 100; spell_proc: flags 0x14, SpellTypeMask '
        f'1, HIT phase, HitMask 0x2 (the Flurry grant shape).',
        _raw(f'After you deal a melee critical strike, your next 3 swings ignore {percent}% of the target\'s armor.',
             ProcTypeMask=_PROC_MELEE_SWING_AND_ABILITY, ProcChance=100),
    )


shredding_blows_204673 = _shredding_blows(204673, 1, 204644, 4)
shredding_blows_204674 = _shredding_blows(204674, 2, 204645, 8)
shredding_blows_204675 = _shredding_blows(204675, 3, 204646, 12)

for _rank_id in (204673, 204674, 204675):
    procs_on(_rank_id, proc_flags=_PROC_MELEE_SWING_AND_ABILITY, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
             spell_phase_mask=_PROC_PHASE_HIT, hit_mask=_PROC_HIT_CRITICAL)


# =====================================================================================================================
# Will of the Berserker 204676  -- D24, doc "Will of the Berserker"
# =====================================================================================================================
# eff0 DUMMY marker (the Rampage script reads the rank: -2 s on Recklessness; the Recklessness AuraScript casts the
# crit buff 204643 when it ends). Flags 0 (the talent entry is A3's). No proc.
will_of_the_berserker_204676 = _talent_rank(
    204676, 'Will of the Berserker', [_carrier(0)], _ICON_WILL_OF_THE_BERSERKER,
    'warrior-rework S3 A2b (D24, doc "Will of the Berserker"): the single rank. eff0 DUMMY marker (read through '
    'GetRankCarrier / HasAura, never HasSpell). ProcTypeMask / ProcChance 0.',
    _raw('Each Rampage reduces the remaining cooldown of Recklessness by 2 sec. When Recklessness ends, your '
         'critical strike chance is increased by 10% for 12 sec.'),
)


# =====================================================================================================================
# Blood Rush 204677-204678  -- D14, doc "Blood Rush"
# =====================================================================================================================
# eff0 aura 42 -> the free-Rampage buff 204637 (A2a), DBC ProcTypeMask 0x10, ProcChance 20 / 40. spell_proc per rank:
# flags 0x10, family 4, Bloodthirst d1 0x400, CAST phase (one roll per Bloodthirst cast; the rank's DBC chance is
# inherited).
def _blood_rush(spell_id, rank, chance):
    return _talent_rank(
        spell_id, 'Blood Rush', [_self_aura(AuraType.PROC_TRIGGER_SPELL, trigger_spell=204637)], _ICON_BLOOD_RUSH,
        f'warrior-rework S3 A2b (D14, doc "Blood Rush"): rank {rank}. eff0 PROC_TRIGGER_SPELL -> 204637, DBC '
        f'ProcTypeMask 0x10, ProcChance {chance} [tune]; spell_proc: flags 0x10, family 4, Bloodthirst d1 0x400, CAST '
        f'phase.',
        _raw(f'After you use Bloodthirst, your next Rampage within 5 sec has a {chance}% chance to cost no rage.',
             ProcTypeMask=_PROC_MELEE_ABILITY, ProcChance=chance),
    )


blood_rush_204677 = _blood_rush(204677, 1, 20)
blood_rush_204678 = _blood_rush(204678, 2, 40)

for _rank_id in (204677, 204678):
    procs_on(_rank_id, proc_flags=_PROC_MELEE_ABILITY, family_name=_SPELLFAMILY_WARRIOR,
             family_mask=(0, _BLOODTHIRST_D1, 0), spell_phase_mask=_PROC_PHASE_CAST)


# =====================================================================================================================
# First declarations of the stock Fury rank rows  -- D3, D11, D20, D28, D29 (pull_dsl.py text, renamed)
# =====================================================================================================================
# Cruelty 12320 / 12852 / 12853 (D29): eff0 aura 52 MOD_WEAPON_CRIT_PERCENT kept (+1 / 2 / 3%), new eff1 aura 137
# MOD_TOTAL_STAT_PERCENTAGE misc 0 (Strength) +1 / 2 / 3% [tune]; the stock weapon gate (class 2 / 173555) is dropped
# (EquippedItemClass -1, Q12: the Strength must work without a weapon, and aura 52 with class -1 reaches every
# attack type). SpellClassSet 0 as stock (no SpellMod). Cut ranks 12855 / 12856 stay inert stock rows.
def _cruelty(spell_id, rank):
    return _stock(
        spell_id, 'Cruelty',
        [Effect(type=EffectType.APPLY_AURA, base_points=rank - 1, implicit_target_a=_TARGET_UNIT_CASTER,
                apply_aura=AuraType.MOD_WEAPON_CRIT_PERCENT),
         _self_aura(AuraType.MOD_TOTAL_STAT_PERCENTAGE, base_points=rank - 1, misc_value=0)],
        _ICON_CRUELTY,
        f'warrior-rework S3 A2b (D29, Q12, doc "Cruelty"): stock row first-declared, rank {rank}. eff0 aura 52 '
        f'crit +{rank}% kept, new eff1 aura 137 MOD_TOTAL_STAT_PERCENTAGE misc 0 Strength +{rank}% [tune]; '
        f'EquippedItemClass 2 / 173555 -> -1.',
        _stock_raw(rank, f'Increases your melee and ranged critical strike chance by {rank}%. Increases your total '
                         f'Strength by {rank}%.', ProcChance=101, SpellLevel=1,
                         **({'DurationIndex': 0} if rank == 1 else {})),
        duration_ms=None if rank == 1 else -1,
    )


cruelty_12320 = _cruelty(12320, 1)
cruelty_12852 = _cruelty(12852, 2)
cruelty_12853 = _cruelty(12853, 3)


# Unbridled Wrath 12322 / 12999 (D20): eff0 aura 42 -> the energize 12964 kept; DBC ProcTypeMask 0x4 -> 0x14 (swings
# and melee ability casts), ProcChance 100 -> 10 / 20. 0-verify A difference 4: the stock weapon gate (class 2 /
# 0x2a5f3) is dropped (class -1, subclass 0): a CAST-phase proc event has no DamageInfo, so Aura::GetProcEffectMask
# would reject every Heroic Strike / Cleave roll while a gate is set. The spell_proc rows replace the stock PPM rows.
def _unbridled_wrath(spell_id, rank, chance):
    return _stock(
        spell_id, 'Unbridled Wrath',
        [Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=_TARGET_UNIT_CASTER,
                apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12964)],
        _ICON_UNBRIDLED_WRATH,
        f'warrior-rework S3 A2b (D20, doc "Unbridled Wrath"): stock row first-declared, rank {rank}. eff0 aura 42 -> '
        f'12964, DBC ProcTypeMask 0x4 -> 0x14, ProcChance {chance} [tune]; EquippedItemClass 2 -> -1 (a CAST-phase '
        f'event has no DamageInfo, 0-verify A difference 4). spell_proc {spell_id} replaces the stock PPM row '
        f'(flags 0x14, family 4, mask d0 0x400040, CAST phase).',
        _stock_raw(rank, f'Your auto attacks, Heroic Strike and Cleave have a {chance}% chance to generate 4 '
                         f'additional rage.', ProcTypeMask=_PROC_MELEE_SWING_AND_ABILITY, ProcChance=chance,
                   SpellLevel=1),
        duration_ms=-1,
    )


unbridled_wrath_12322 = _unbridled_wrath(12322, 1, 15)   # balance 2026-10-30 (user): 10/20 -> 15/30
unbridled_wrath_12999 = _unbridled_wrath(12999, 2, 30)

# 12964: ENERGIZE rage bp 9 -> 39 (value 40 tenths = 4 rage); only Unbridled Wrath triggers it.
unbridled_wrath_energize_12964 = _stock(
    12964, 'Unbridled Wrath',
    [Effect(type=EffectType.ENERGIZE, base_points=39, implicit_target_a=_TARGET_UNIT_CASTER, misc_value=1)],
    _ICON_UNBRIDLED_WRATH,
    'warrior-rework S3 A2b (D20): stock 12964 first-declared; ENERGIZE rage bp 9 -> 39 (4 rage, tenths). Only the '
    'Unbridled Wrath ranks trigger it.',
    _stock_raw(1, 'Generates 4 rage.', ProcChance=101, SpellLevel=1, DurationIndex=0),
    attributes=262160,
)

for _stock_id in (12322, 12999):
    procs_on(_stock_id, proc_flags=_PROC_MELEE_SWING_AND_ABILITY, family_name=_SPELLFAMILY_WARRIOR,
             family_mask=(_HEROIC_STRIKE_D0 | _CLEAVE_D0, 0, 0), spell_phase_mask=_PROC_PHASE_CAST,
             chance=15 if _stock_id == 12322 else 30)

# The cut ranks' stock PPM rows (the talent keeps 2 ranks; 13000-13002 stay inert spells).
remove_spell_proc(13000)
remove_spell_proc(13001)
remove_spell_proc(13002)


# Blood Craze 16487 / 16489 / 16492 (D11): eff0 aura 42 -> DUMMY carrier 5 / 10 / 15 per-mille of max health (bp 4 /
# 9 / 14), ProcTypeMask / ProcChance 0, spell_proc -16487 removed. The stock HoT 16488 / 16490 / 16491 stay inert.
_BLOOD_CRAZE_STOCK_HOT = {16487: 16488, 16489: 16490, 16492: 16491}


def _blood_craze(spell_id, rank, per_mille):
    percent = f'{per_mille / 10:g}'
    return _stock(
        spell_id, 'Blood Craze', [_carrier(per_mille - 1)], _ICON_BLOOD_CRAZE,
        f'warrior-rework S3 A2b (D11, doc "Blood Craze"): stock row first-declared, rank {rank}. eff0 was '
        f'PROC_TRIGGER_SPELL -> {_BLOOD_CRAZE_STOCK_HOT[spell_id]}; now a DUMMY carrier {per_mille} '
        f'per-mille (bp {per_mille - 1}) read by Warrior::OnBloodthirstHit. ProcTypeMask / ProcChance 0, '
        f'spell_proc -16487 removed.',
        _stock_raw(rank, f'Your Bloodthirst heals you for {percent}% of your maximum health. This healing is doubled '
                         f'while you are Enraged.', ProcTypeMask=0, ProcChance=0, DurationIndex=0),
    )


blood_craze_16487 = _blood_craze(16487, 1, 5)
blood_craze_16489 = _blood_craze(16489, 2, 10)
blood_craze_16492 = _blood_craze(16492, 3, 15)

remove_spell_proc(-16487)


# Enrage 12317 / 13045-13048 (D3): both effects DUMMY carriers 2 / 4 / 6 / 8 / 10 (bp 1 / 3 / 5 / 7 / 9): eff0 the
# physical damage %, eff1 the melee haste %. ProcTypeMask / ProcChance 0, spell_proc -12317 removed. The stock
# GetProcEffectMask path is gone with it (the stock triggered buffs 12880 / 14201-14204 stay inert).
def _enrage(spell_id, rank):
    percent = rank * 2
    return _stock(
        spell_id, 'Enrage', [_carrier(percent - 1), _carrier(percent - 1)], _ICON_ENRAGE,
        f'warrior-rework S3 A2b (D3, doc "Enrage"): stock row first-declared, rank {rank}. eff0 / eff1 DUMMY carriers '
        f'{percent}% (bp {percent - 1}): eff0 physical damage, eff1 melee haste, read through GetRankCarrier by '
        f'Warrior::GetEnrageBonusPct and the Enrage buff 204636. ProcTypeMask / ProcChance 0, spell_proc -12317 '
        f'removed (its script binding is unbound in warrior_fury.py).',
        _stock_raw(rank, f'Every 200 rage you spend Enrages you, increasing your physical damage by {percent}% and '
                         f'your melee haste by {percent}% for 12 sec. Recklessness also Enrages you.',
                   ProcTypeMask=0, ProcChance=0, SpellLevel=1, DurationIndex=0),
        attributes=262352,
    )


enrage_12317 = _enrage(12317, 1)
enrage_13045 = _enrage(13045, 2)
enrage_13046 = _enrage(13046, 3)
enrage_13047 = _enrage(13047, 4)
enrage_13048 = _enrage(13048, 5)

remove_spell_proc(-12317)


# Flurry 12319 / 12971 / 12972 (D28): the rank rows are the stock rows unchanged (aura 42 -> 12966 / 12967 / 12968,
# ProcTypeMask 0x14, the stock -12319 spell_proc row stays), first-declared only so `SPELL_FLURRY` follows the talent
# rank. Their descriptions read the buffs' `$12966s1`-style values (8 / 16 / 25%).
def _flurry(spell_id, rank, buff):
    return _stock(
        spell_id, 'Flurry',
        [Effect(type=EffectType.APPLY_AURA, implicit_target_a=_TARGET_UNIT_CASTER,
                apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=buff)],
        _ICON_FLURRY,
        f'warrior-rework S3 A2b (D28): stock row first-declared unchanged, rank {rank} (aura 42 -> {buff}). Declared '
        f'so SPELL_FLURRY moves from 12966 to 12319 (no C++ user); the stock spell_proc -12319 row is kept.',
        _stock_raw(rank, f'Increases your attack speed by ${buff}s1% for your next 3 swings after dealing a melee '
                         f'critical strike.', AttributesEx3=67108864, ProcTypeMask=20, ProcChance=100, SpellLevel=1,
                   DurationIndex=0),
        attributes=262336,
    )


flurry_12319 = _flurry(12319, 1, 12966)
flurry_12971 = _flurry(12971, 2, 12967)
flurry_12972 = _flurry(12972, 3, 12968)


# Flurry buffs 12967 / 12968 (D28): bp 9 -> 15 (16%), 14 -> 24 (25%). Everything else as stock (aura 138, 3 charges,
# ProcTypeMask 0x4, 15 s, SpellClassSet 4; the stock consumption rows stay). 12966 is A1's `flurry_buff_r1_12966`.
def _flurry_buff(spell_id, rank, base_points):
    return _stock(
        spell_id, 'Flurry',
        [Effect(type=EffectType.APPLY_AURA, base_points=base_points, implicit_target_a=_TARGET_UNIT_CASTER,
                apply_aura=AuraType.MOD_MELEE_HASTE)],
        _ICON_FLURRY,
        f'warrior-rework S3 A2b (D28): stock buff first-declared, rank {rank}. aura 138 bp {base_points} '
        f'(+{base_points + 1}% attack speed; was bp {9 if rank == 2 else 14}), 3 charges, 15 s. Rank 1 (12966) is '
        f'A1\'s.',
        _stock_raw(rank, f'Increases your attack speed by ${spell_id}s1% for your next 3 swings after dealing a '
                         f'melee critical strike.', ProcTypeMask=4, ProcChance=100, ProcCharges=3, SpellLevel=1,
                   SpellVisualID_1=12379, AuraDescription_Lang_enUS='Attack speed increased.',
                   AuraDescription_Lang_Mask=16712190, SpellClassSet=_SPELLFAMILY_WARRIOR),
        attributes=262144, duration_ms=15000,
    )


flurry_buff_r2_12967 = _flurry_buff(12967, 2, 15)
flurry_buff_r3_12968 = _flurry_buff(12968, 3, 24)
