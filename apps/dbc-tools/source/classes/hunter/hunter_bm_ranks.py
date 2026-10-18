"""
Hunter - Beast Mastery S1a talent rank spells 201820-201857 (hunter-rework BEAST-MASTERY.md 2.1 / 5 / 5.1).

Every rank is a hidden passive (attributes 464, duration -1, RangeIndex 1, target 1, SpellClassSet 9, no family bits on the
carrier, EquippedItemClass -1). Stored base_points are live - 1 (die_sides 1). SpellMod effects carry reader masks only
(never d1 b28). Tooltips are the 5.1 text: every number is a `$sN` / cross-spell token or a `const()` value interpolated
from hunter_bm_spells.py; the capstone suffix is grey on every rank below the last and plain on the last.

Ranks that S1b scripts (201826, 201831, 201838, 201841-201843, 201849-201851) carry their final data here and no
scripted_by / procs_on row. 201848 carries the CAST-phase spell_proc row. The sibling imports below are standard Python
imports of the same class package (registry.load_class_package), so hunter_bm_spells.py loads first.
"""

from lib.dsl import AuraType, CombatRating, Effect, EffectType, School, SpellModOp
from lib.dsl.registry import pot_text, procs_on, spell

from . import _masks as m
from .hunter_bm_spells import (
    BEAST_CLEAVE_RADIUS_YD, IAOTV_CAPSTONE_MANA_PCT, PHOENIX_PLUME_REVIVE_PCT, SPIKED_COLLAR_MAX_TARGETS,
    SPIKED_COLLAR_RADIUS_YD, bm_stomp_1161, stomp_pet_201804,
)

_MASK_KEYS = {1: 'A', 2: 'B', 3: 'C'}
_VERSATILITY = 1 << CombatRating.VERSATILITY
_COOLDOWN_HASTE = 1 << CombatRating.COOLDOWN_HASTE
_PROC_CHANCE = 1 << CombatRating.PROC_CHANCE
_NOTE = 'hunter-rework S1a BEAST-MASTERY section 5 (A2): hidden talent rank passive, stored = live - 1.'


def _c(row):
    """A const() row's value as tooltip text (8.0 -> '8')."""
    value = row['value']
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


def _dummy(base_points=0):
    return _aura(AuraType.DUMMY, base_points)


def _desc(text, capstone=None, last=False):
    """G = grey suffix on a rank below the last, P = plain suffix on the last (PLAN section 2)."""
    if capstone is None:
        return text
    if last:
        return f"{text}\n\nCapstone Bonus: {capstone}"
    return f"{text}\n\n|cFF9D9D9DCapstone Bonus: {capstone}|r"


def _rank(spell_id, name, rank, effects, icon, description, masks=None, raw=None, tooltip_vars=None):
    """A talent rank passive. `masks` maps a 1-based effect index to its (d0, d1, d2) EffectSpellClassMask triple;
    `rank` is the NameSubtext number (None for a one-rank talent)."""
    overrides = {
        'EquippedItemClass': -1, 'SpellClassSet': 9, 'RangeIndex': 1, 'CastingTimeIndex': 1, 'ProcChance': 101,
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

# ---- (0,0) Pathfinding 1384: r3 clones 19560 (r1/r2 are in hunter_trigger_spells.py). Capstone via linked_spell 201813 (A1).
_PATHFINDING = (
    "Increases the chance for your Aspect of the Monkey to grant Versatility by $s1%, and increases your "
    "Versatility by $s2%."
)
_PATHFINDING_CAP = (
    "Increases the speed bonus of your Aspect of the Cheetah, Aspect of the Pack and mounts by $201813s1%. Does not "
    "stack with other effects that increase mounted speed."
)
pathfinding_201820 = _rank(
    201820, 'Pathfinding', 3,
    [_flat(SpellModOp.CHANCE_OF_SUCCESS, 14), _aura(AuraType.MOD_CUSTOM_STAT_PCT, 2, _VERSATILITY)], 1181,
    _desc(_PATHFINDING, _PATHFINDING_CAP, last=True), masks={1: (m.ASPECT_OF_THE_MONKEY, 0, 0)},
)

# ---- (0,1) Primal Focus 60200: Cooldown Haste +1/2/3%.
def _primal_focus(spell_id, rank, bp):
    return _rank(
        spell_id, 'Primal Focus', rank, [_aura(AuraType.MOD_CUSTOM_STAT_PCT, bp, _COOLDOWN_HASTE)], 2253,
        "Increases your Cooldown Haste by $s1%.",
    )


primal_focus_201821 = _primal_focus(201821, 1, 0)
primal_focus_201822 = _primal_focus(201822, 2, 1)
primal_focus_201823 = _primal_focus(201823, 3, 2)

# ---- (0,3) Improved Aspect of the Dragonhawk 1381: explode chance, explosion damage, haste.
def _dragonhawk(spell_id, rank, chance, damage, haste):
    return _rank(
        spell_id, 'Improved Aspect of the Dragonhawk', rank,
        [_flat(SpellModOp.CHANCE_OF_SUCCESS, chance), _pct(SpellModOp.DAMAGE, damage),
         _aura(AuraType.HASTE_ALL, haste)], 2328,
        "Increases the chance for your Aspect of the Dragonhawk to explode by $s1% and the explosion's damage by $s2%, "
        "and increases your haste by $s3%.",
        masks={1: (0, 0, m.ASPECT_OF_THE_DRAGONHAWK), 2: (0, 0, m.DRAGONHAWK_EXPLOSION)},
    )


improved_aspect_of_the_dragonhawk_201824 = _dragonhawk(201824, 1, 4, 9, 0)
improved_aspect_of_the_dragonhawk_201825 = _dragonhawk(201825, 2, 9, 19, 1)

# ---- (1,1) Phoenix's Plume 1625: r3 clones 19575 (capstone revive is S1b / 201810).
_PLUME = "Increases the damage of your Command I and Command II by $s1%."
_PLUME_CAP = (
    f"If your pet dies in combat, it returns to life with {_c(PHOENIX_PLUME_REVIVE_PCT)}% of its health. "
    "This effect cannot occur more than once every $201810d."
)
phoenix_s_plume_201826 = _rank(
    201826, "Phoenix's Plume", 3, [_pct(SpellModOp.DAMAGE, 29), _pct(SpellModOp.DOT, 29)], 2787,
    _desc(_PLUME, _PLUME_CAP, last=True), masks={1: m.COMMANDED_READER, 2: m.COMMANDED_READER},
)

# ---- (1,2) Spiked Collar 1395: pet damage; r3 eff1 DUMMY bp 49 = the 50% share read by S1b.
_COLLAR = "Increases the damage done by your pet by $s1%."
_COLLAR_CAP = (
    f"Your Kill Command also strikes up to {_c(SPIKED_COLLAR_MAX_TARGETS)} additional enemies within "
    f"{_c(SPIKED_COLLAR_RADIUS_YD)} yards of its target for $201829s2% of its damage."
)
spiked_collar_201827 = _rank(
    201827, 'Spiked Collar', 1, [_flat(SpellModOp.ALL_EFFECTS, 2)], 2934, _desc(_COLLAR, _COLLAR_CAP),
    masks={1: (m.TAMED_PET_PASSIVE_01, 0, 0)},
)
spiked_collar_201828 = _rank(
    201828, 'Spiked Collar', 2, [_flat(SpellModOp.ALL_EFFECTS, 5)], 2934, _desc(_COLLAR, _COLLAR_CAP),
    masks={1: (m.TAMED_PET_PASSIVE_01, 0, 0)},
)
spiked_collar_201829 = _rank(
    201829, 'Spiked Collar', 3, [_flat(SpellModOp.ALL_EFFECTS, 8), _dummy(49)], 2934,
    _desc(_COLLAR, _COLLAR_CAP, last=True), masks={1: (m.TAMED_PET_PASSIVE_01, 0, 0)},
)

# ---- (2,3) Improved Aspect of the Viper 2138: trigger chance, mana restored (201602 eff1), Proc Chance rating.
_VIPER = (
    "Increases the chance for your Aspect of the Viper to poison its target by $s1% and the mana its poison "
    "restores by $s2%, and increases your Proc Chance by $s3%."
)
_VIPER_CAP = (
    f"When your pet critically hits with its basic attack or a command, you regenerate "
    f"{_c(IAOTV_CAPSTONE_MANA_PCT)}% of your maximum mana and grant Replenishment to up to 10 party or raid members."
)


def _viper(spell_id, rank, chance, mana, proc, last):
    return _rank(
        spell_id, 'Improved Aspect of the Viper', rank,
        [_flat(SpellModOp.CHANCE_OF_SUCCESS, chance), _pct(SpellModOp.EFFECT1, mana),
         _aura(AuraType.MOD_CUSTOM_STAT_PCT, proc, _PROC_CHANCE)], 2227,
        _desc(_VIPER, _VIPER_CAP, last=last),
        masks={1: (0, m.ASPECT_OF_THE_VIPER, 0), 2: (0, 0, m.VIPER_POISON)},
    )


improved_aspect_of_the_viper_201830 = _viper(201830, 1, 4, 24, 0, False)
improved_aspect_of_the_viper_201831 = _viper(201831, 2, 9, 49, 1, True)

# ---- (3,0) Arcane Attunement 1385: Arcane Shot damage and mana (EFFECT2 = the mana DUMMY).
def _attunement(spell_id, rank, bp):
    return _rank(
        spell_id, 'Arcane Attunement', rank, [_pct(SpellModOp.DAMAGE, bp), _pct(SpellModOp.EFFECT2, bp)], 3487,
        "Increases the damage of your Arcane Shot by $s1%, and your Arcane Shot restores $s2% more mana.",
        masks={1: (m.ARCANE_SHOT, 0, 0), 2: (m.ARCANE_SHOT, 0, 0)},
    )


arcane_attunement_201832 = _attunement(201832, 1, 9)
arcane_attunement_201833 = _attunement(201833, 2, 19)
arcane_attunement_201834 = _attunement(201834, 3, 29)

# ---- (3,3) Improved Aspect of the Beast 1397: Beast trigger chance and pet damage.
def _aotb(spell_id, rank, chance, damage):
    return _rank(
        spell_id, 'Improved Aspect of the Beast', rank,
        [_flat(SpellModOp.CHANCE_OF_SUCCESS, chance), _flat(SpellModOp.ALL_EFFECTS, damage)], 1562,
        "Increases the chance for your Aspect of the Beast to send your pet into a rage by $s1%, and increases the "
        "damage done by your pet by $s2%.",
        masks={1: (0, 0, m.ASPECT_OF_THE_BEAST), 2: (m.TAMED_PET_PASSIVE_01, 0, 0)},
    )


improved_aspect_of_the_beast_201835 = _aotb(201835, 1, 1, 2)
improved_aspect_of_the_beast_201836 = _aotb(201836, 2, 3, 5)
improved_aspect_of_the_beast_201837 = _aotb(201837, 3, 5, 8)

# ---- (4,0) Stomp 1390: one-rank DUMMY marker; the text shows 201804's potency value times Earthshaker (tooltip var 1161).
stomp_talent_201838 = _rank(
    201838, 'Stomp', None, [_dummy()], 129,
    "Your Arcane Shot commands your pet to Stomp, dealing " + pot_text(stomp_pet_201804, var='es')
    + " Physical damage to all enemies within $201804a1 yards of its target.",
    tooltip_vars=bm_stomp_1161,
)

# ---- (4,2) Shark Attack 1388: pet damage +5/10%.
shark_attack_201839 = _rank(
    201839, 'Shark Attack', 1, [_flat(SpellModOp.ALL_EFFECTS, 4)], 2918,
    "Increases the damage done by your pet by $s1%.",
    masks={1: (m.TAMED_PET_PASSIVE_01, 0, 0)},
)
shark_attack_201840 = _rank(
    201840, 'Shark Attack', 2, [_flat(SpellModOp.ALL_EFFECTS, 9)], 2918,
    "Increases the damage done by your pet by $s1%.",
    masks={1: (m.TAMED_PET_PASSIVE_01, 0, 0)},
)

# ---- (4,3) Culling the Herd 60202: DUMMY 1/2/3% read by the S1b script.
def _culling(spell_id, rank, bp):
    return _rank(
        spell_id, 'Culling the Herd', rank, [_dummy(bp)], 4115,
        "When your pet's basic attack critically strikes, you and your pet deal $s1% increased damage for $201808d.",
    )


culling_the_herd_201841 = _culling(201841, 1, 0)
culling_the_herd_201842 = _culling(201842, 2, 1)
culling_the_herd_201843 = _culling(201843, 3, 2)

# ---- (5,0) Earthshaker 60203: Stomp damage and radius.
def _earthshaker(spell_id, rank, damage, radius):
    return _rank(
        spell_id, 'Earthshaker', rank, [_pct(SpellModOp.DAMAGE, damage), _flat(SpellModOp.RADIUS, radius)], 66,
        "Increases the damage of your pet's Stomp by $s1% and its radius by $s2 yards.",
        masks={1: m.STOMP_READER, 2: m.STOMP_READER},
    )


earthshaker_201844 = _earthshaker(201844, 1, 14, 1)
earthshaker_201845 = _earthshaker(201845, 2, 29, 3)

# ---- (5,1) Pack Hunter 60204: Multi-Shot damage and jump targets.
def _pack_hunter(spell_id, rank, damage, targets):
    return _rank(
        spell_id, 'Pack Hunter', rank, [_pct(SpellModOp.DAMAGE, damage), _flat(SpellModOp.JUMP_TARGETS, targets)], 1697,
        "Increases the damage of your Multi-Shot by $s1%, and your Multi-Shot strikes $s2 additional "
        "$ltarget:targets;.",
        masks={1: (m.MULTI_SHOT, 0, 0), 2: (m.MULTI_SHOT, 0, 0)},
    )


pack_hunter_201846 = _pack_hunter(201846, 1, 9, 0)
pack_hunter_201847 = _pack_hunter(201847, 2, 19, 1)

# ---- (6,2) Beast Cleave 60205: eff0 PROC_TRIGGER_SPELL -> 201806, once per Multi-Shot cast (CAST phase).
beast_cleave_talent_201848 = _rank(
    201848, 'Beast Cleave', None, [_aura(AuraType.PROC_TRIGGER_SPELL, 0, 0, 201806)], 277,
    "After you Multi-Shot, your pet's single-target attacks and your Kill Command also strike all enemies within "
    f"{_c(BEAST_CLEAVE_RADIUS_YD)} yards of the target for $201806s2% of the damage dealt. Lasts $201806d.",
    raw={'ProcTypeMask': 0x100, 'ProcChance': 100},
)
procs_on(
    beast_cleave_talent_201848, proc_flags=m.PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS, family_name=9,
    family_mask=(m.MULTI_SHOT, 0, 0), spell_phase_mask=m.PROC_SPELL_PHASE_CAST, chance=100.0,
)

# ---- (7,1) Cobra Shot 60206: DUMMY Nature share 5/10/15%; r3 capstone links 201811 (A1). Read by S1b scripts.
_COBRA = (
    "Your Steady Shot deals an additional $s1% of its damage as Nature damage."
)
_COBRA_CAP = "Your Steady Shot becomes instant. Cannot be combined with other talents that transform Steady Shot."


def _cobra(spell_id, rank, bp, last):
    return _rank(
        spell_id, 'Cobra Shot', rank, [_dummy(bp)], 3409, _desc(_COBRA, _COBRA_CAP, last=last),
        raw={'ProcTypeMask': 0x100, 'ProcChance': 100},
    )


cobra_shot_201849 = _cobra(201849, 1, 7, False)
cobra_shot_201850 = _cobra(201850, 2, 15, False)
cobra_shot_201851 = _cobra(201851, 3, 24, True)

# ---- (7,2) Master's Command 2136: commanded-spell damage.
def _masters_command(spell_id, rank, bp):
    return _rank(
        spell_id, "Master's Command", rank, [_pct(SpellModOp.DAMAGE, bp), _pct(SpellModOp.DOT, bp)], 3486,
        "Increases the damage of your Command I and Command II by $s1%.",
        masks={1: m.COMMANDED_READER, 2: m.COMMANDED_READER},
    )


master_s_command_201852 = _masters_command(201852, 1, 9)
master_s_command_201853 = _masters_command(201853, 2, 19)
master_s_command_201854 = _masters_command(201854, 3, 29)

# ---- (8,1) The Beast Within 1803: DUMMY 5/10/15% passed to 34471 by the script; r3 capstone links 201812 (A1).
_TBW = (
    "While your pet is under the effects of Bestial Wrath, you also go into a rage, dealing $s1% additional damage "
    "and paying ${$34471m1*-1}% less mana for $34471d."
)
_TBW_CAP = "Your pets and your Kill Command deal additional damage equal to your Mastery."


def _tbw(spell_id, rank, bp, last):
    return _rank(spell_id, 'The Beast Within', rank, [_dummy(bp)], 2229, _desc(_TBW, _TBW_CAP, last=last))


the_beast_within_201855 = _tbw(201855, 1, 4, False)
the_beast_within_201856 = _tbw(201856, 2, 9, False)
the_beast_within_201857 = _tbw(201857, 3, 14, True)
