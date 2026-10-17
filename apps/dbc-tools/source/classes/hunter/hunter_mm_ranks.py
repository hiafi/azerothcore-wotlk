"""
Hunter - Marksmanship S2 talent rank spells 201960-201982 (hunter-rework MARKSMANSHIP.md 2.1 / 6 / 6.2).

Every rank is a hidden passive (attributes 464, duration -1, RangeIndex 1, target 1, SpellClassSet 9, no family bits
on the carrier, EquippedItemClass -1). Stored base_points are live - 1. SpellMod effects carry reader masks from
_masks.py only (never d1 b28). Every rank has ProcTypeMask 0 except the two with an explicit spell_proc row in
hunter_mm_spells.py (Precision r3 201965: 0x100; Rapid Killing r3 201981: 0x2), so no engine default proc entry ever
reads a stale mask (S2-HANDOFF M15). Tooltips are the 6.2 text: every number a `$sN` / cross-spell token or a `const()`
value interpolated from hunter_mm_spells.py; the capstone suffix is grey on every rank below the last and plain on the
last.

Skeleton written by S2a WP-0 0-dsl (variable stems and Names frozen for HunterData.h), completed by S2a WP-A2. Ranks
that S2b scripts (Trick Shots 201975, Rain of Arrows 201979/201980, Triangulation 201978's capstone, Rapid Killing
201981's execute DUMMY, Combat Experience 201982) carry their final data here and no S2b scripted_by / procs_on row;
201982's linked_spell to 201952 is S2b's. The sibling imports below are standard Python imports of the same class
package (registry.load_class_package), so hunter_mm_spells.py and hunter_trigger_spells.py load first.
"""

from lib.dsl import AuraType, Effect, EffectType, School, SpellModOp
from lib.dsl.registry import pot_text, spell

from . import _masks as m
from .hunter_mm_spells import (
    CONVERGENCE_MAX_TARGETS, CONVERGENCE_SPLASH_PCT, DEADEYE_CDR_MS, KEEN_EYE_GAIN, MULTI_SHOT_TARGET_CAP,
    PACK_MAX_TARGETS, PACK_RADIUS_YD, RAIN_OF_ARROWS_FIRE_PCT, RAPID_KILLING_HEALTH_PCT, convergence_201932,
    mm_convergence_1171,
)
from .hunter_trigger_spells import rapid_killing_35098

_MASK_KEYS = {1: 'A', 2: 'B', 3: 'C'}
_NOTE = 'hunter-rework S2a MARKSMANSHIP section 6 (A2): hidden talent rank passive, stored = live - 1.'


def _c(row):
    """A const() row's value as tooltip text (8.0 -> '8')."""
    value = row['value']
    return str(int(value)) if float(value).is_integer() else str(value)


def _sec(row):
    """A millisecond const() row's value as whole-second tooltip text (2000 -> '2')."""
    value = row['value'] / 1000
    return str(int(value)) if float(value).is_integer() else str(value)


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
    """A DUMMY aura (bp -1 = live 0 for a pure marker; trigger_spell 0)."""
    return _aura(AuraType.DUMMY, base_points)


def _desc(text, capstone=None, last=False):
    """G = grey suffix on a rank below the last, P = plain suffix on the last (MARKSMANSHIP 6 / PLAN section 2)."""
    if capstone is None:
        return text
    if last:
        return f"{text}\n\nCapstone Bonus: {capstone}"
    return f"{text}\n\n|cFF9D9D9DCapstone Bonus: {capstone}|r"


def _rank(spell_id, name, rank, effects, icon, description, masks=None, raw=None, tooltip_vars=None):
    """A talent rank passive. `masks` maps a 1-based effect index to its (d0, d1, d2) EffectSpellClassMask triple;
    `rank` is the NameSubtext number (None for a one-rank talent)."""
    overrides = {
        'EquippedItemClass': -1, 'SpellClassSet': 9, 'RangeIndex': 1, 'CastingTimeIndex': 1,
        'ProcTypeMask': 0, 'ProcChance': 101,
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
    overrides.update(raw or {})
    kwargs = {}
    if tooltip_vars is not None:
        kwargs['tooltip_vars'] = tooltip_vars
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=464,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=0.0, duration_ms=-1,
        effects=effects, spell_icon_id=icon, notes=_NOTE, raw_overrides=overrides, **kwargs,
    )


# ---- (0,2) Quick Draw 60225: haste +1/2/3% (Q27).
def _quick_draw(spell_id, rank, bp):
    return _rank(
        spell_id, 'Quick Draw', rank, [_aura(AuraType.HASTE_ALL, bp)], 537, "Increases your haste by $s1%.",
    )


quick_draw_201960 = _quick_draw(201960, 1, 0)
quick_draw_201961 = _quick_draw(201961, 2, 1)
quick_draw_201962 = _quick_draw(201962, 3, 2)

# ---- (1,2) Precision 60226: crit +1/2/3%; r3 eff1 DUMMY carries the HIT/CRIT spell_proc row (A1) read by
# spell_hun_precision_capstone (raw ProcTypeMask 0x100, ProcChance 100).
_PRECISION = "Increases your critical strike chance by $s1%."
_PRECISION_CAP = "Your critical strikes against a target with your Sniper's Mark add an extra stack to it."


def _precision(spell_id, rank, bp, last):
    effects = [_aura(AuraType.MOD_CRIT_PCT, bp)]
    raw = None
    if last:
        effects.append(_dummy())
        raw = {'ProcTypeMask': 0x100, 'ProcChance': 100}
    return _rank(
        spell_id, 'Precision', rank, effects, 3408, _desc(_PRECISION, _PRECISION_CAP, last=last), raw=raw,
    )


precision_201963 = _precision(201963, 1, 0, False)
precision_201964 = _precision(201964, 2, 1, False)
precision_201965 = _precision(201965, 3, 2, True)

# ---- (2,0) Improved Aimed Shot 1818: Aimed Shot damage +5/10/15% (reaches the S2b ricochet / bounce through d0 b17);
# r3 eff1 DUMMY marker (handler step 6 casts the free Arcane Shot 201933).
_IAS = "Increases the damage of your Aimed Shot by $s1%."
_IAS_CAP = (
    "Your Aimed Shot also fires an Arcane Shot at the target. This Arcane Shot costs no mana and does not trigger its "
    "cooldown."
)


def _improved_aimed_shot(spell_id, rank, bp, last):
    effects = [_pct(SpellModOp.DAMAGE, bp)] + ([_dummy()] if last else [])
    return _rank(
        spell_id, 'Improved Aimed Shot', rank, effects, 253, _desc(_IAS, _IAS_CAP, last=last),
        masks={1: m.AIMED_SHOT_MASK},
    )


improved_aimed_shot_201966 = _improved_aimed_shot(201966, 1, 4, False)
improved_aimed_shot_201967 = _improved_aimed_shot(201967, 2, 9, False)
improved_aimed_shot_201968 = _improved_aimed_shot(201968, 3, 14, True)

# ---- (3,0) Deadeye 2133: Aimed Shot crit +4/8/12; r3 eff1 DUMMY marker (handler step 6, DEADEYE_CDR_MS).
_DEADEYE = "Increases the critical strike chance of your Aimed Shot by $s1%."
_DEADEYE_CAP = (
    "Your Aimed Shot critical strikes reduce the remaining cooldown of your Sniper's Mark, Viper's Mark and Falcon's "
    f"Mark by {_sec(DEADEYE_CDR_MS)} sec."
)


def _deadeye(spell_id, rank, bp, last):
    effects = [_flat(SpellModOp.CRITICAL_CHANCE, bp)] + ([_dummy()] if last else [])
    return _rank(
        spell_id, 'Deadeye', rank, effects, 256, _desc(_DEADEYE, _DEADEYE_CAP, last=last),
        masks={1: m.AIMED_SHOT_MASK},
    )


deadeye_201969 = _deadeye(201969, 1, 3, False)
deadeye_201970 = _deadeye(201970, 2, 7, False)
deadeye_201971 = _deadeye(201971, 3, 11, True)

# ---- (4,2) Keen Eye 1351: eff0 DUMMY = the roll chance 10/20/30 (Hunter::RollKeenEye reads it through SpellInfo).
# Arcane Shot half in S2a; the Multi-Shot half is S2b's.
def _keen_eye(spell_id, rank, bp):
    return _rank(
        spell_id, 'Keen Eye', rank, [_dummy(bp)], 2318,
        f"Your Arcane Shot and Multi-Shot have a $s1% chance to add {_c(KEEN_EYE_GAIN)} extra stacks to each of your "
        "marks on the target.",
    )


keen_eye_201972 = _keen_eye(201972, 1, 9)
keen_eye_201973 = _keen_eye(201973, 2, 19)
keen_eye_201974 = _keen_eye(201974, 3, 29)

# ---- (5,3) Trick Shots 2131 (one rank): Multi-Shot +2 chain targets (3 + 2 = 5, works natively); eff1 DUMMY marker
# for S2b's spell_hun_multi_shot_mm and the handler's ricochet (step 7). Inert until S2b except the +2 targets.
# "50%" = the ricochet's 110 weapon potency of Aimed Shot's 220 (201934 is declared in S2b, no single DBC home).
trick_shots_201975 = _rank(
    201975, 'Trick Shots', None, [_flat(SpellModOp.JUMP_TARGETS, 1), _dummy()], 2541,
    f"Your Multi-Shot hits up to {_c(MULTI_SHOT_TARGET_CAP)} targets and copies your marks on its target, with their "
    f"stacks, to each enemy it hits. Your next Aimed Shot within $201943d ricochets to up to {_c(PACK_MAX_TARGETS)} "
    f"other enemies with your marks within {_c(PACK_RADIUS_YD)} yards, dealing 50% of its damage to each and "
    "consuming their marks.",
    masks={1: (m.MULTI_SHOT, 0, 0)},
)

# ---- (6,2) Triangulation 1821: eff0 DUMMY 3/6/9 per mark consumed (GetTriangulationMultiplier); r3 = Convergence
# (S2b casts 201932). Every rank quotes Convergence's potency through tooltip_vars 1171 (mfd = Marked for Death e1,
# the payoff DUMMY).
# The splash is "N% as much", not pot_text(effect=2): 201932 carries one direct AP coefficient on both effects (D6) and
# S2b's spell_hun_convergence scales EFFECT_1 by CONVERGENCE_SPLASH_PCT (A1's row), so eff2's potency is the centre's.
_TRIANGULATION = "Your Aimed Shot deals $s1% more damage for each of your marks it consumes."
_TRIANGULATION_CAP = (
    "When your Aimed Shot consumes all three of your marks, they fuse into a Convergence, dealing "
    + pot_text(convergence_201932, var='mfd')
    + f" Physical damage to the target and {_c(CONVERGENCE_SPLASH_PCT)}% as much to up to "
    + f"{_c(CONVERGENCE_MAX_TARGETS)} enemies within $201932a2 yards."
)


def _triangulation(spell_id, rank, bp, last):
    return _rank(
        spell_id, 'Triangulation', rank, [_dummy(bp)], 2235, _desc(_TRIANGULATION, _TRIANGULATION_CAP, last=last),
        tooltip_vars=mm_convergence_1171,
    )


triangulation_201976 = _triangulation(201976, 1, 2, False)
triangulation_201977 = _triangulation(201977, 2, 5, False)
triangulation_201978 = _triangulation(201978, 3, 8, True)

# ---- (6,3) Rain of Arrows 60229: Volley damage +10/20% (Volley tick 42243 + the S2b half Volley); capstone = r2
# known (S2b's spell_hun_volley_mm). "completes" = AURA_REMOVE_BY_EXPIRE (MM-C1). "50%" as Trick Shots (201935, S2b).
_RAIN_OF_ARROWS = "Increases the damage of your Volley by $s1%."
_RAIN_OF_ARROWS_CAP = (
    f"Each tick of your Volley has a {_c(RAIN_OF_ARROWS_FIRE_PCT)}% chance to grant Fire!. When your Volley completes, "
    f"your next Aimed Shot within $201944d bounces to up to {_c(PACK_MAX_TARGETS)} enemies within "
    f"{_c(PACK_RADIUS_YD)} yards, dealing 50% of its damage to each."
)


def _rain_of_arrows(spell_id, rank, bp, last):
    return _rank(
        spell_id, 'Rain of Arrows', rank, [_pct(SpellModOp.DAMAGE, bp)], 2511,
        _desc(_RAIN_OF_ARROWS, _RAIN_OF_ARROWS_CAP, last=last), masks={1: m.VOLLEY_DAMAGE},
    )


rain_of_arrows_201979 = _rain_of_arrows(201979, 1, 9, False)
rain_of_arrows_201980 = _rain_of_arrows(201980, 2, 19, True)

# ---- (2,3) Rapid Killing 1819 r3 (r1 34948 / r2 34949 in hunter_trigger_spells.py), a clone of 34949: eff0 DUMMY
# +12 [11] execute clause (S2b's UnitScript; inert in S2a), eff1 Rapid Fire cooldown -45 s [-45001] on (0x20,0,0),
# eff2 PROC_TRIGGER_SPELL -> 35098 on a kill (raw ProcTypeMask 0x2, ProcChance 100). Its spell_proc row
# (disable_effects_mask 0x3) and spell_hun_rapid_killing_capstone binding are A1's.
rapid_killing_201981 = _rank(
    201981, 'Rapid Killing', 3,
    [_dummy(11), _flat(SpellModOp.COOLDOWN, -45001),
     _aura(AuraType.PROC_TRIGGER_SPELL, -1, trigger_spell=rapid_killing_35098.id)],
    2285,
    _desc(
        f"Increases the damage of your shots against targets below {_c(RAPID_KILLING_HEALTH_PCT)}% health by $s1% "
        "and reduces the cooldown of your Rapid Fire by ${$m2/-1000} sec.",
        "Killing an enemy that yields experience causes your next $35098n Aimed Shots, Arcane Shots, Kill Shots or "
        "Chimera Shots to deal $35098s1% more damage.",
        last=True,
    ),
    masks={2: (m.RAPID_FIRE, 0, 0)},
    raw={'ProcTypeMask': 0x2, 'ProcChance': 100},
)

# ---- (5,0) Combat Experience 1804 r3 (r1 34475 / r2 34476 in hunter_trigger_spells.py), a clone of 34476 with the
# normalized effect order: eff0 aura 137 Agility (misc 1) +3% [2], eff1 MOD_CRIT_PCT +3% [2]. The capstone passive
# 201952 and linked_spell(201982, 201952, 2) are S2b's ("30%" is S2b's script value; no const home in S2a).
combat_experience_201982 = _rank(
    201982, 'Combat Experience', 3,
    [_aura(AuraType.MOD_TOTAL_STAT_PERCENTAGE, 2, 1), _aura(AuraType.MOD_CRIT_PCT, 2)],
    2223,
    _desc(
        "Increases your total Agility by $s1% and your critical strike chance by $s2%.",
        "Increases your Intellect by 30% of your Agility.",
        last=True,
    ),
)
