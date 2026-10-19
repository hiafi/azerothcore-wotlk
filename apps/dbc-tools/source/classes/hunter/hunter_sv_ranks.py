"""
Hunter - Survival S3 talent rank spells 202080-202108 (hunter-rework SURVIVAL.md 2.1 / 6 / 6.1 / 6.2 / 8.1).

Every rank is a hidden passive (attributes 464, duration -1, RangeIndex 1, target 1, SpellClassSet 9, no family bits on
the carrier, EquippedItemClass -1, SpellLevel = the talent row's learn level 10 + 5N). Stored base_points are live - 1
(die_sides 1). SpellMod effects carry reader masks from _masks.py only (never d1 b28). Every rank has ProcTypeMask 0
except the five proc carriers, whose raw ProcChance / ProcTypeMask are the SURVIVAL 6 values and whose spell_proc rows
are A1's (hunter_sv_spells.py, SURVIVAL 8.1): Favored Prey r3 202084 (0x140, 5), Relentless r3 202087 (0x100, 15),
Predator's Guard r3 202094 (0x100, 10), Demolitions r3 202097 (0x100, 100), Volatile Payload r3 202105 (0x100, 30).
So no engine default proc entry ever reads a stale mask (S2-HANDOFF M15, S3-HANDOFF N8). The no-row DUMMY carriers
(Shrapnel, Improved Mantis Strike r3, Point of No Escape r3, Deadly Focus r2's mana marker) keep ProcTypeMask 0.

Tooltips are the SURVIVAL 6.1 text: every number a `$sN` / cross-spell token, a `pot_text()` or a `const()` value
interpolated from hunter_sv_spells.py (TOOLTIP-RECONCILE X10); the capstone suffix is grey on every rank below the last
and plain on the last (X1 / PLAN section 2).

Skeleton written by S3a WP-0 0-dsl (variable stems and Names frozen for HunterData.h), completed by S3a WP-A2. Imports:
`_masks` and hunter_sv_spells.py (a standard sibling import of the same class package, registry.load_class_package;
hunter_sv_spells.py names these ranks by bare id, so there is no cycle). Never imports hunter_spells.py.
"""

from lib.dsl import AuraType, CombatRating, Effect, EffectType, School, SpellModOp
from lib.dsl.registry import pot_text, spell

from . import _masks as m
from .hunter_sv_spells import IGT_SLOW_MIN_DISTANCE_YD, shrapnel_hit_202053

_MASK_KEYS = {1: 'A', 2: 'B', 3: 'C'}
_PROC_CHANCE = 1 << CombatRating.PROC_CHANCE
_NOTE = 'hunter-rework S3a SURVIVAL section 6 (A2): hidden talent rank passive, stored = live - 1.'


def _c(row):
    """A const() row's value as tooltip text (10.0 -> '10')."""
    value = row['value']
    return str(int(value)) if float(value).is_integer() else str(value)


def _level(row):
    """The learn level of a talent on tree row `row` (SURVIVAL 6: row N -> 10 + 5N)."""
    return 10 + 5 * row


def _aura(aura, base_points=0, misc_value=0, trigger_spell=0):
    """One self-targeted APPLY_AURA effect (target 1)."""
    return Effect(
        type=EffectType.APPLY_AURA, base_points=base_points, implicit_target_a=1, apply_aura=aura,
        misc_value=int(misc_value), trigger_spell=trigger_spell,
    )


def _flat(op, base_points):
    return _aura(AuraType.ADD_FLAT_MODIFIER, base_points, op)


def _pct(op, base_points):
    return _aura(AuraType.ADD_PCT_MODIFIER, base_points, op)


def _dummy(base_points=-1):
    """A DUMMY aura: bp -1 (live 0) for a pure proc carrier (trigger 0, misc 0, SURVIVAL 8.1 DUMMY-carrier rule),
    otherwise the script-read amount, stored live - 1."""
    return _aura(AuraType.DUMMY, base_points)


def _proc_trigger(trigger_spell):
    """A PROC_TRIGGER_SPELL carrier (amount unused: bp -1 = live 0)."""
    return _aura(AuraType.PROC_TRIGGER_SPELL, -1, 0, trigger_spell=trigger_spell)


def _desc(text, capstone=None, last=False):
    """G = grey suffix on a rank below the last, P = plain suffix on the last (SURVIVAL 6.1 / PLAN section 2)."""
    if capstone is None:
        return text
    if last:
        return f"{text}\n\nCapstone Bonus: {capstone}"
    return f"{text}\n\n|cFF9D9D9DCapstone Bonus: {capstone}|r"


def _rank(spell_id, name, rank, level, effects, icon, description, masks=None, proc=None):
    """A talent rank passive. `masks` maps a 1-based effect index to its (d0, d1, d2) EffectSpellClassMask triple;
    `rank` is the NameSubtext number (None for a one-rank talent); `proc` is the (ProcTypeMask, ProcChance) pair of a
    carrier whose spell_proc row A1 declares (None = ProcTypeMask 0)."""
    proc_type_mask, proc_chance = proc or (0, 101)
    overrides = {
        'EquippedItemClass': -1, 'SpellClassSet': 9, 'RangeIndex': 1, 'CastingTimeIndex': 1, 'SpellLevel': level,
        'ProcTypeMask': proc_type_mask, 'ProcChance': proc_chance,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': '' if rank is None else f'Rank {rank}',
        'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': description,
        'AuraDescription_Lang_Mask': 16712188,
    }
    for i in range(1, len(effects) + 1):
        overrides[f'EffectChainAmplitude_{i}'] = 1.0
    for effect_index, triple in (masks or {}).items():
        for dword, value in enumerate(triple, start=1):
            if value:
                overrides[f'EffectSpellClassMask{_MASK_KEYS[effect_index]}_{dword}'] = value
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=464,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=0.0, duration_ms=-1,
        effects=effects, spell_icon_id=icon, notes=_NOTE, raw_overrides=overrides,
    )


# ---- (0,0) Deadly Focus 1820 (repurposed Hawk Eye), learn 10: Mongoose Bite / Mantis Strike damage +10/20%
# (STRIKE_HITS). r2 eff1 flat RANGE +10 yd on THREE_STRIKES; eff2 DUMMY bp 24 (live 25; user 2026-10-18, was 15, 5) =
# user ruling 6's marker, the percent of base mana Raptor Strike 2973 restores (B2's Hunter::GetShotManaPct reads
# 202081 EFFECT_2 through SpellInfo when the player knows 202081). No mask on eff2: not a SpellMod, no family-0 leak.
_DF = "Increases the damage of your Mongoose Bite and Mantis Strike by $s1%."
_DF_CAP = ("Your Raptor Strike, Mongoose Bite and Mantis Strike have $202081s2 yd more range. Raptor Strike restores "
           "$202081s3% of your base mana.")


def _deadly_focus(spell_id, rank, bp, last):
    effects = [_pct(SpellModOp.DAMAGE, bp)]
    masks = {1: m.STRIKE_HITS}
    if last:
        effects += [_flat(SpellModOp.RANGE, 9), _dummy(24)]
        masks[2] = m.THREE_STRIKES
    return _rank(
        spell_id, 'Deadly Focus', rank, _level(0), effects, 538, _desc(_DF, _DF_CAP, last=last), masks=masks,
    )


deadly_focus_202080 = _deadly_focus(202080, 1, 9, False)
deadly_focus_202081 = _deadly_focus(202081, 2, 19, True)

# ---- (0,3) Favored Prey 1623 (repurposed Improved Tracking), learn 10: Proc Chance +2/4/6%. r3 eff1 DUMMY carrier
# (raw ProcChance 5, ProcTypeMask 0x140 = DONE_RANGED_AUTO | DONE_SPELL_RANGED; row 8.1 CAST|HIT, A1;
# spell_hun_favored_prey OnEffectProc(EFFECT_1, SPELL_AURA_DUMMY)).
_FP = "Increases your Proc Chance by $s1%."
_FP_CAP = ("Your direct damage has a $202084h% chance to grant you Favored Prey, increasing your damage against all "
           "creatures of the target's type by $202063s1% for $202063d.")


def _favored_prey(spell_id, rank, bp, last):
    effects = [_aura(AuraType.MOD_CUSTOM_STAT_PCT, bp, _PROC_CHANCE)]
    if last:
        effects.append(_dummy())
    return _rank(
        spell_id, 'Favored Prey', rank, _level(0), effects, 2221, _desc(_FP, _FP_CAP, last=last),
        proc=(0x140, 5) if last else None,
    )


favored_prey_202082 = _favored_prey(202082, 1, 1, False)
favored_prey_202083 = _favored_prey(202083, 2, 3, False)
favored_prey_202084 = _favored_prey(202084, 3, 5, True)

# ---- (1,0) Relentless 1621 (repurposed Savage Strikes), learn 15: armor ignore 6/13/20% (pct IGNORE_ARMOR on
# THREE_STRIKES, C25). r3 eff1 PROC_TRIGGER_SPELL -> Mongoose Fury 202042 (raw ProcChance 15, ProcTypeMask 0x100;
# row 8.1 CAST on RELENTLESS_PROC, A1).
_REL = "Your Raptor Strike, Mongoose Bite and Mantis Strike ignore $s1% of the target's armor."
_REL_CAP = ("Your Raptor Strike and Mantis Strike have a $202087h% chance to grant Mongoose Fury, causing your next "
            "Mongoose Bite within $202042d to deal $202042s1% more damage.")


def _relentless(spell_id, rank, bp, last):
    effects = [_pct(SpellModOp.IGNORE_ARMOR, bp)]
    if last:
        effects.append(_proc_trigger(202042))
    return _rank(
        spell_id, 'Relentless', rank, _level(1), effects, 86, _desc(_REL, _REL_CAP, last=last),
        masks={1: m.THREE_STRIKES}, proc=(0x100, 15) if last else None,
    )


relentless_202085 = _relentless(202085, 1, -7, False)
relentless_202086 = _relentless(202086, 2, -14, False)
relentless_202087 = _relentless(202087, 3, -21, True)

# ---- (1,1) Improved Glaive Toss 60250, learn 15: Glaive Toss damage +5/10/15%. r3 eff1 flat JUMP_TARGETS bp 1 (live 2:
# 3 + 2 = 5 targets); the > IGT_SLOW_MIN_DISTANCE_YD slow 202056 is spell_hun_glaive_toss_sv's (B1).
_IGT = "Increases the damage of your Glaive Toss by $s1%."
_IGT_CAP = (f"Your Glaive Toss bounces to $202090s2 additional nearby enemies. Enemies hit while you are farther than "
            f"{_c(IGT_SLOW_MIN_DISTANCE_YD)} yards away are slowed by $202056s1% for $202056d.")


def _improved_glaive_toss(spell_id, rank, bp, last):
    effects = [_pct(SpellModOp.DAMAGE, bp)]
    masks = {1: (0, 0, m.GLAIVE_TOSS)}
    if last:
        effects.append(_flat(SpellModOp.JUMP_TARGETS, 1))
        masks[2] = (0, 0, m.GLAIVE_TOSS)
    return _rank(
        spell_id, 'Improved Glaive Toss', rank, _level(1), effects, 90231, _desc(_IGT, _IGT_CAP, last=last),
        masks=masks,
    )


improved_glaive_toss_202088 = _improved_glaive_toss(202088, 1, 4, False)
improved_glaive_toss_202089 = _improved_glaive_toss(202089, 2, 9, False)
improved_glaive_toss_202090 = _improved_glaive_toss(202090, 3, 14, True)

# ---- (1,3) Survival Instincts 1810, learn 15: new rank 3 (r1 34494, r2 34496 in hunter_trigger_spells.py, A3), a clone
# of 34496 at the new values: eff0 MOD_DAMAGE_PERCENT_TAKEN misc 127 bp -4 (-3%), eff1 flat CRITICAL_CHANCE bp 5 (+6%)
# on SURVIVAL_INSTINCTS_CRIT. 34496's stale A_1 222 is not copied. No capstone (one text on every rank).
survival_instincts_202091 = _rank(
    202091, 'Survival Instincts', 3, _level(1),
    [_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, -4, 127), _flat(SpellModOp.CRITICAL_CHANCE, 5)],
    2239,
    "Reduces all damage taken by $s1% and increases the critical strike chance of your Arcane Shot, Steady Shot, "
    "Explosive Shot, Wildfire Bomb and Glaive Toss by $s2%.",
    masks={2: m.SURVIVAL_INSTINCTS_CRIT},
)

# ---- (3,0) Predator's Guard 1311 (repurposed Deflection), learn 25: damage taken -1/2/3%. r3 eff1 PROC_TRIGGER_SPELL
# -> 202043 (raw ProcChance 10, ProcTypeMask 0x100; row 8.1 HIT on STRIKE_HITS, A1).
_PG = "Reduces all damage taken by $s1%."
_PG_CAP = ("Your Mongoose Bite and Mantis Strike hits have a $202094h% chance to grant Predator's Guard for $202043d, "
           "reducing damage taken by a further $202043s1% and increasing the damage of your Raptor Strike, Mongoose "
           "Bite and Mantis Strike by $202043s2%.")


def _predators_guard(spell_id, rank, bp, last):
    effects = [_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, bp, 127)]
    if last:
        effects.append(_proc_trigger(202043))
    return _rank(
        spell_id, "Predator's Guard", rank, _level(3), effects, 558, _desc(_PG, _PG_CAP, last=last),
        proc=(0x100, 10) if last else None,
    )


predators_guard_202092 = _predators_guard(202092, 1, -2, False)
predators_guard_202093 = _predators_guard(202093, 2, -3, False)
predators_guard_202094 = _predators_guard(202094, 3, -4, True)

# ---- (3,1) Demolitions 60252, learn 25: Wildfire Bomb / Explosive Shot damage +5/10/15% (pct DAMAGE on
# DEMOLITIONS_DAMAGE, pct DOT on DEMOLITIONS_DOT = Wildfire's burn). r3 eff2 DUMMY bp 1999 (2000 ms Wildfire Bomb cut,
# read by spell_hun_demolitions OnEffectProc(EFFECT_2, SPELL_AURA_DUMMY)); raw ProcChance 100, ProcTypeMask 0x100
# (row 8.1 HIT crit on (0, EXPLOSIVE_SHOT, 0), A1).
_DEMO = "Increases the damage of your Wildfire Bomb and Explosive Shot by $s1%."
_DEMO_CAP = ("When the initial hit of your Explosive Shot critically strikes its target, the remaining cooldown of "
             "your Wildfire Bomb is reduced by ${$202097m3/1000} sec.")


def _demolitions(spell_id, rank, bp, last):
    effects = [_pct(SpellModOp.DAMAGE, bp), _pct(SpellModOp.DOT, bp)]
    if last:
        effects.append(_dummy(1999))
    return _rank(
        spell_id, 'Demolitions', rank, _level(3), effects, 1696, _desc(_DEMO, _DEMO_CAP, last=last),
        masks={1: m.DEMOLITIONS_DAMAGE, 2: m.DEMOLITIONS_DOT}, proc=(0x100, 100) if last else None,
    )


demolitions_202095 = _demolitions(202095, 1, 4, False)
demolitions_202096 = _demolitions(202096, 2, 9, False)
demolitions_202097 = _demolitions(202097, 3, 14, True)

# ---- (5,1) Shrapnel 60253, learn 35: eff0 DUMMY chance 10 / 20% read by Hunter::TryShrapnel through SpellInfo (no row,
# ProcTypeMask 0). "Each blast" includes the initial hit (SV WP3).
_SHRAPNEL = ("Each blast of your Explosive Shot has a $s1% chance to fling shrapnel at a random enemy near the "
             "target, dealing " + pot_text(shrapnel_hit_202053) + " Fire damage.")
shrapnel_202098 = _rank(202098, 'Shrapnel', 1, _level(5), [_dummy(9)], 90234, _SHRAPNEL)
shrapnel_202099 = _rank(202099, 'Shrapnel', 2, _level(5), [_dummy(19)], 90234, _SHRAPNEL)

# ---- (6,0) Improved Mantis Strike 60254, learn 40: Mantis Strike damage +5/10/15%. r3 eff1 DUMMY bp 2999 (3000 ms
# Wildfire Bomb cut, read by spell_hun_mantis_strike AfterCast; no row, ProcTypeMask 0).
_IMS = "Increases the damage of your Mantis Strike by $s1%."
_IMS_CAP = "Your Mantis Strike reduces the remaining cooldown of your Wildfire Bomb by ${$202102m2/1000} sec."


def _improved_mantis_strike(spell_id, rank, bp, last):
    effects = [_pct(SpellModOp.DAMAGE, bp)]
    if last:
        effects.append(_dummy(2999))
    return _rank(
        spell_id, 'Improved Mantis Strike', rank, _level(6), effects, 2252, _desc(_IMS, _IMS_CAP, last=last),
        masks={1: (0, m.MANTIS_STRIKE, 0)},
    )


improved_mantis_strike_202100 = _improved_mantis_strike(202100, 1, 4, False)
improved_mantis_strike_202101 = _improved_mantis_strike(202101, 2, 9, False)
improved_mantis_strike_202102 = _improved_mantis_strike(202102, 3, 14, True)

# ---- (7,1) Volatile Payload 60255, learn 45: Explosive Trap blast +10/20/30% (pct SPELLMOD_DAMAGE misc 0 on 13812's
# d0 b2, V6 / S3-HANDOFF stale line 23: reaches the whole blast, never the DOT-typed ground fire). r3 eff1 DUMMY carrier
# (raw ProcChance 30, ProcTypeMask 0x100; row 8.1 CAST on (0, WILDFIRE_BOMB, 0), A1; spell_hun_volatile_payload
# OnEffectProc(EFFECT_1, SPELL_AURA_DUMMY) resets category 1250).
_VP = "Increases the damage of your Explosive Trap's initial blast by $s1%."
_VP_CAP = ("Your Wildfire Bomb has a $202105h% chance to reset the cooldown of your Explosive Trap and Immolation "
           "Trap.")


def _volatile_payload(spell_id, rank, bp, last):
    effects = [_pct(SpellModOp.DAMAGE, bp)]
    if last:
        effects.append(_dummy())
    return _rank(
        spell_id, 'Volatile Payload', rank, _level(7), effects, 1755, _desc(_VP, _VP_CAP, last=last),
        masks={1: (m.EXPLOSIVE_TRAP_EFFECT, 0, 0)}, proc=(0x100, 30) if last else None,
    )


volatile_payload_202103 = _volatile_payload(202103, 1, 9, False)
volatile_payload_202104 = _volatile_payload(202104, 2, 19, False)
volatile_payload_202105 = _volatile_payload(202105, 3, 29, True)

# ---- (7,2) Point of No Escape 2142, learn 45: new rank 3 (r1 53298, r2 53299 in hunter_trigger_spells.py, A3), the
# rewritten 53299 shape at r3's value: eff0 DUMMY bp 5 (6%) read by Hunter::GetPointOfNoEscapePct, no masks, no eff1
# (53299's eff1 becomes None), ProcTypeMask 0. Inert until S3b's marker 202058.
point_of_no_escape_202106 = _rank(
    202106, 'Point of No Escape', 3, _level(7), [_dummy(5)], 3520,
    "Increases your damage against targets affected by your Tar Bomb or Frost Trap by $s1%.",
)

# ---- (9,1) Dark Hunting 2141 (repurposed Noxious Stings), learn 55: Burning Tar damage +10/20% (pct DOT on d1 b27).
# r2 eff1 flat COOLDOWN -5001 (-5 s) on Tar Bomb (d1 b26).
_DH = "Increases the damage of your Burning Tar by $s1%."
_DH_CAP = "Reduces the cooldown of your Tar Bomb by ${$202108m2/-1000} sec."


def _dark_hunting(spell_id, rank, bp, last):
    effects = [_pct(SpellModOp.DOT, bp)]
    masks = {1: (0, m.BURNING_TAR, 0)}
    if last:
        effects.append(_flat(SpellModOp.COOLDOWN, -5001))
        masks[2] = (0, m.TAR_BOMB, 0)
    return _rank(
        spell_id, 'Dark Hunting', rank, _level(9), effects, 1506, _desc(_DH, _DH_CAP, last=last), masks=masks,
    )


dark_hunting_202107 = _dark_hunting(202107, 1, 9, False)
dark_hunting_202108 = _dark_hunting(202108, 2, 19, True)
