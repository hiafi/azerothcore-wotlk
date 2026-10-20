"""
Shaman - spells that are never directly cast - proc/periodic-tick effects, trigger_spell targets, hidden talent-rank buffs, etc..

Split from a single source/classes/shaman.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .shaman_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, School, SpellModOp
from lib.dsl.registry import (
    procs_on, remove_spell_proc, scripted_by, spell, trained_by, unbind_bonus_coefficients, unbind_script,
)

from . import _masks as m


# =====================================================================================================================
# S1a A2 (shaman-rework S1a WP brief, docs/reworks/shaman-elemental-rework.md section 5): the stock Elemental rank
# spells below are rewritten in place (variable names, hence ShamanData:: names, are unchanged). Every row is built from
# `_talent()`, so no stale raw twin from the stock row survives (the build starts from an empty row). Stored
# base_points = live - 1. Masks are EffectSpellClassMask{A,B,C}_{1,2,3}: the letter is the effect, the number the dword
# (README "Gotcha"); `masks={effect_index: (d0, d1, d2)}` below.
# =====================================================================================================================

_SHOCKS = 0x90100000          # d0: Earth b20, Flame b28, Frost b31
_LB = 0x1                     # d0 b0
_CL = 0x2                     # d0 b1
_FLAME_SHOCK = 0x10000000     # d0 b28
_LAVA_BURST = 0x1000          # d1 b12
_THUNDERSTORM = 0x2000        # d1 b13
_WIND_SHEAR = 0x8000000       # d1 b27 (57994 only; never b11, which Purge / Water Walking share)
_LAVA_LASH = 0x4              # d2 b2 (Lava Lash's own bit; effect masks may target it)
_SEARING_SUMMON = 0x10        # d0 b4 (Searing Totem 3599)
_FIRE_NOVA_COST = 0x8000000   # d0 b27 (Fire Nova 1535)
_FIRE_NOVA_DAMAGE = 0x40000   # d1 b18 (Fire Nova 8349)
_RANK_SUBTEXT = 'Rank {}'
_CR_VERSATILITY = 1 << 21     # 1 << CombatRating.VERSATILITY
_PROC_DONE_SPELL_MAGIC_NEG = 0x10000
_PROC_DONE_PERIODIC = 0x40000
_PROC_PHASE_HIT = 0x2
_PROC_TYPE_DAMAGE = 0x1
_PROC_HIT_NORMAL_CRIT = 0x3
_PROC_HIT_CRIT = 0x2
_FFN = 0x1C                   # school mask Fire | Frost | Nature


def _desc(text, capstone=None, last=False):
    """Rank text from the doc; the capstone clause is grey on every rank below the last (hunter / paladin idiom)."""
    if capstone is None:
        return text
    if last:
        return f"{text}\n\nCapstone: {capstone}"
    return f"{text}\n\n|cFF9D9D9DCapstone: {capstone}|r"


def _aura(aura, base_points=0, misc_value=0, **kw):
    """One self-targeted APPLY_AURA effect."""
    return Effect(
        type=EffectType.APPLY_AURA, base_points=base_points, implicit_target_a=1, apply_aura=aura,
        misc_value=int(misc_value), **kw,
    )


def _mod(op, base_points, pct=True):
    """A SpellMod effect (the class mask goes in `masks=` of `_talent`, keyed by this effect's 1-based index)."""
    return _aura(AuraType.ADD_PCT_MODIFIER if pct else AuraType.ADD_FLAT_MODIFIER, base_points, int(op))


def _dummy(base_points=0):
    """A DUMMY effect: trigger_spell 0 and misc 0, so a spell_proc row on its spell never casts a stale trigger (X5).
    On a proc talent it is also the effect CheckEffectProc passes (B2); its amount carries the rank value."""
    return _aura(AuraType.DUMMY, base_points)


def _talent(spell_id, name, rank, effects, icon, description, masks=None, level=0, school=School.NORMAL,
            attributes=464, notes='', **raw_extra):
    """A talent rank spell: passive, family 11, EquippedItemClass -1 (L1), no latent twin."""
    raw = {
        'EquippedItemClass': -1, 'SpellClassSet': 11, 'CastingTimeIndex': 1, 'RangeIndex': 1, 'ProcChance': 101,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': rank,
        'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': description,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
    }
    if level:
        raw['SpellLevel'] = level
    for effect_index, triple in (masks or {}).items():
        for dword, value in enumerate(triple, start=1):
            if value:
                raw[f'EffectSpellClassMask{"ABC"[effect_index - 1]}_{dword}'] = value
    raw.update(raw_extra)
    return spell(
        id=spell_id, name=name, school=school, attributes=attributes, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0, effects=effects, spell_icon_id=icon,
        notes=notes, raw_overrides=raw,
    )


lightning_shield_324 = spell(
    id=324,
    name='Lightning Shield',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=12, points_per_level=5.097222222222222, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=26545),
    ],
    spell_icon_id=19,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 11 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx3': 196608, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Lightning Shield damages attackers.', 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The caster is surrounded by $n balls of lightning.  When a spell, melee or ranged attack hits the caster, the attacker will be struck for $26364s1 Nature damage.  This expends one lightning ball.  Only one ball will fire every few seconds.  Lasts $d.  Only one Elemental Shield can be active on the Shaman at any one time.', 'EffectBonusMultiplier_1': 0.2669999897480011, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 3, 'ProcTypeMask': 139944, 'RangeIndex': 1, 'SpellClassMask_1': 1024, 'SpellClassSet': 11, 'SpellLevel': 8, 'SpellVisualID_1': 37, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


healing_stream_5672 = spell(
    id=5672,
    name='Healing Stream',
    school=School.NATURE,
    attributes=64,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, points_per_level=0.31666666666666665, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=2000, trigger_spell=52041),
    ],
    spell_icon_id=1647,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 128, 'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals $s1 every $t1 seconds.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 11, 'SpellLevel': 20, 'SpellVisualID_1': 366},
)


cleansing_totem_passive_8172 = spell(
    id=8172,
    name='Cleansing Totem Passive',
    school=School.NATURE,
    attributes=67904,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=3000, trigger_spell=8171),
    ],
    spell_icon_id=1673,
    notes='pulled from existing data; SH0b A2: AttributesEx5 0x200 (first pulse at t=0). Shared with NPC totems 22091/22487 (harmless).',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 38, 'SpellLevel': 38, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'AttributesEx5': 512},
)


healing_stream_totem_heal_52041 = spell(
    id=52041,
    name='Healing Stream Totem',
    school=School.SHADOW,
    attributes=134218112,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.DUMMY, sp_potency=0.35, potency_kind='heal_periodic', time_basis_ms=2000, implicit_target_a=20, radius_yards=30.0),
    ],
    spell_icon_id=2213,
    notes=(
        "pulled from existing data. Potency system P8 (2026-10-02): new declaration - this is the "
        "spell healing_stream_5672's own PERIODIC_TRIGGER_SPELL aura casts every 2s (trigger_spell=52041, "
        "already wired correctly). 5672's own base_points (5 + 0.3166/level) is the vestigial tooltip "
        "number shown to players ($5672s1 in the totem summon spell's description) and is left untouched "
        "- the REAL seed value is this spell's own EFFECT_0 (SPELL_EFFECT_DUMMY, base_points=5 flat, no "
        "level scaling at all before this conversion), read via GetEffectValue() in "
        "spell_sha_healing_stream_totem::HandleDummy (src/server/scripts/Spells/spell_shaman.cpp), run "
        "through owner->SpellHealingBonusDone()/Restorative Totems %/Glyph of Healing Stream Totem %, "
        "then re-applied as a custom bp on SPELL_SHAMAN_TOTEM_HEALING_STREAM_HEAL (52042, which also "
        "carries its own spell_bonus_data direct_bonus=0.0827 - untouched, out of scope, applied a second "
        "time by the normal heal-cast pipeline since 52042's cast always skips the potency hook per D2). "
        "potency_kind='heal_periodic' with time_basis_ms=2000 (not amplitude, this effect isn't itself "
        "periodic - the 2s period belongs to 5672's own aura) mirrors Rain of Fire's P4 precedent "
        "(potency-system.PROGRESS.md P4). sp_potency=0.35 is base-implied from the current flat value of "
        "5 (5 / (3.96 x C(60) x (2.0/1.5)) = 0.354, rounded) - this is a tiny number because almost all of "
        "this ability's real healing comes from 52042's own spell_bonus_data coefficient against spell "
        "power, not from this seed; converting it only fixes the seed's complete lack of level scaling."
    ),
    raw_overrides={'AttributesEx2': 268435456, 'CastingTimeIndex': 1, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 11, 'SpellClassMask_1': 67117056, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'SpellLevel': 1},
)


mana_spring_5677 = spell(
    id=5677,
    name='Mana Spring',
    school=School.NATURE,
    attributes=64,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=65, base_points=15, points_per_level=1.3888888888888888, implicit_target_a=1, apply_aura=85, radius_yards=30.0),
    ],
    spell_icon_id=338,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 26); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Gain $s1 mana every 5 seconds.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'RangeIndex': 1, 'SpellClassMask_1': 16384, 'SpellClassSet': 11, 'SpellLevel': 26, 'SpellVisualID_1': 367},
)


flametongue_weapon_proc_8026 = spell(
    id=8026,
    name='Flametongue Weapon Proc',
    school=School.FIRE,
    attributes=262400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=325, points_per_level=19.0, implicit_target_a=6),
    ],
    spell_icon_id=679,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_1': 2097152, 'SpellClassSet': 11, 'SpellLevel': 10},
)


frostbrand_attack_8034 = spell(
    id=8034,
    name='Frostbrand Attack',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, points_per_level=9.666666666666666, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=41, points_per_level=-1.5333333333333334, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=271),
    ],
    spell_icon_id=681,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 16777220, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement slowed by $s1%.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Imbue the Shaman's weapon with frost.  Each hit has a chance of causing $8034s2 additional Frost damage and slowing the target's movement speed by $8034s1% for $8034d.  Lasts 30 minutes.", 'EffectBonusMultiplier_1': 0.10000000149011612, 'EffectBonusMultiplier_2': 0.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_1': 2416967683, 'EffectSpellClassMaskC_2': 16, 'EffectSpellClassMaskC_3': 4, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_1': 16777216, 'SpellClassSet': 11, 'SpellLevel': 20, 'SpellVisualID_1': 13},
)


stoneskin_8072 = spell(
    id=8072,
    name='Stoneskin',
    school=School.NATURE,
    attributes=320,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=65, base_points=94, points_per_level=13.881578947368421, implicit_target_a=1, apply_aura=22, misc_value=1, radius_yards=30.0),
    ],
    spell_icon_id=690,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 32768, 'SpellClassSet': 11, 'SpellLevel': 4, 'SpellVisualID_1': 366},
)


strength_of_earth_8076 = spell(
    id=8076,
    name='Strength of Earth',
    school=School.NATURE,
    attributes=320,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=65, base_points=9, points_per_level=2.0714285714285716, implicit_target_a=1, apply_aura=AuraType.MOD_STAT, radius_yards=30.0),
        Effect(type=65, base_points=9, points_per_level=2.0714285714285716, implicit_target_a=1, apply_aura=AuraType.MOD_STAT, misc_value=1, radius_yards=20.0),
        Effect(type=65, base_points=-1, implicit_target_a=1, apply_aura=52),
    ],
    spell_icon_id=691,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Strength and Agility by $s1.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 11, 'SpellLevel': 10, 'SpellVisualID_1': 366},
)


frost_resistance_8182 = spell(
    id=8182,
    name='Frost Resistance',
    school=School.NATURE,
    attributes=320,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=65, base_points=29, points_per_level=1.7857142857142858, implicit_target_a=1, apply_aura=143, misc_value=16, radius_yards=30.0),
    ],
    spell_icon_id=1713,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 24); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Frost Resistance increased by $s1', 'BaseLevel': 24, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 67108864, 'SpellClassSet': 11, 'SpellLevel': 24, 'SpellVisualID_1': 366},
)


fire_resistance_8185 = spell(
    id=8185,
    name='Fire Resistance',
    school=School.FROST,
    attributes=320,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=65, base_points=29, points_per_level=1.9230769230769231, implicit_target_a=1, apply_aura=143, misc_value=4, radius_yards=30.0),
    ],
    spell_icon_id=1712,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 28); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Fire Resistance increased by $s1.', 'BaseLevel': 28, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 67108864, 'SpellClassSet': 11, 'SpellLevel': 28, 'SpellVisualID_1': 366},
)


magma_totem_8187 = spell(
    id=8187,
    name='Magma Totem',
    school=School.FIRE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=8.6, implicit_target_a=22, implicit_target_b=15, radius_yards=8.0),
    ],
    spell_icon_id=37,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 26); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P8 (2026-10-02): converted to sp_potency=92.3 (base-implied, docs/potency-system.PLAN.md P8, shaman-potency-report.md) - Magma Totem\'s own periodic nova, cast via the generic TotemAI::UpdateAI loop, plain cast, no custom bp, T=1.5s (no cast_time/amplitude of its own). SH0b A2 (2026-10-19): sp_potency 92.3 -> 20 (shaman rework Magma Totem pulse; NPC Magma totem drift accepted), description rewritten. 2026-10-20 smoke-test fix pass: 20 -> 8.6 (x0.43, rough damage cut).',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 1073741824, 'AttributesEx3': 64, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals {pot1} Fire damage to all enemies within $a1 yards every 1.5 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 1073741828, 'SpellClassSet': 11, 'SpellLevel': 26, 'SpellVisualID_1': 2107},
)


fire_nova_8349 = spell(
    id=8349,
    name='Fire Nova',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=104.1, potency_kind='direct', implicit_target_a=87, implicit_target_b=16, radius_yards=10.0),
    ],
    spell_icon_id=33,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 12); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. '
          'Potency system P7-Shaman: converted to sp_potency=242.2 (shaman-potency-proposals.txt, mismatched row). Cast by the player: spell_sha_fire_nova::HandleDummy (spell_shaman.cpp) runs `caster->CastSpell(totem, ..., true)` on the Fire Nova player spell (1535) with the totem only as the target, not the caster, and with no custom base points - so this is an ordinary player-attributed potency conversion, not a D2 script-bp case.',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 1073741824, 'AttributesEx3': 1073741824, 'AttributesEx5': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Causes the shaman's active Fire totem to emit a wave of flames, inflicting {pot1} Fire damage to enemies within $a1 yards of the totem.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 2147745792, 'SpellClassSet': 11, 'SpellLevel': 12, 'SpellVisualID_1': 14908, 'Targets': 64},
)


flametongue_weapon_passive_10400 = spell(
    id=10400,
    name='Flametongue Weapon (Passive)',
    school=School.NATURE,
    attributes=262592,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=325, points_per_level=19.0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=6, points_per_level=2.914285714285714, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=57),
    ],
    spell_icon_id=688,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 16777216, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassMask_1': 2097152, 'SpellClassSet': 11, 'SpellLevel': 10},
)


nature_resistance_10596 = spell(
    id=10596,
    name='Nature Resistance',
    school=School.NATURE,
    attributes=320,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=65, base_points=29, points_per_level=2.0, implicit_target_a=1, apply_aura=143, misc_value=8, radius_yards=30.0),
    ],
    spell_icon_id=1675,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Nature Resistance increased by $s1.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 67108864, 'SpellClassSet': 11, 'SpellLevel': 30, 'SpellVisualID_1': 366},
)


ancestral_fortitude_16177 = spell(
    id=16177,
    name='Ancestral Fortitude',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, points_per_level=-0.11666666666666667, implicit_target_a=21, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=1),
    ],
    spell_icon_id=200,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces physical damage taken by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces physical damage taken by $s1%. Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassMask_2': 67108864, 'SpellClassSet': 11},
)


flurry_16257 = spell(
    id=16257,
    name='Flurry',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, points_per_level=0.4067796610169492, implicit_target_a=1, apply_aura=138),
    ],
    spell_icon_id=108,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attack speed increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your attack speed by $16257s1% for your next 3 swings after dealing a critical strike.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcCharges': 3, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassMask_2': 512, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 2759},
)


reincarnation_20608 = spell(
    id=20608,
    name='Reincarnation',
    school=School.NATURE,
    attributes=8388672,
    category=1161,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1800000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 1048576, 'AttributesEx4': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows you to resurrect yourself upon death with $21169s1% health and mana.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Passive', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassMask_1': 512, 'SpellClassSet': 11, 'SpellLevel': 30},
)


lightning_shield_26364 = spell(
    id=26364,
    name='Lightning Shield',
    school=School.NATURE,
    attributes=16777216,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=103.9, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=62,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 11 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. '
          'Potency system P7-Shaman: converted to sp_potency=103.9 (shaman-potency-proposals.txt, mismatched row). Cast by the player via lightning_shield_324\'s own PROC_TRIGGER_SPELL aura (triggered off the player\'s own buff, not a totem/pet), so this is an ordinary player-attributed potency conversion, not a D2 script-bp case (lightning_shield_324 casts it with no CastCustomSpell override).',
    raw_overrides={'AttributesEx2': 805306372, 'AttributesEx3': 512, 'AttributesEx4': 16384, 'AttributesEx5': 393224, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Casts a bolt of lightning at the target for {pot1} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 1024, 'SpellClassSet': 11, 'SpellLevel': 8},
)


elemental_devastation_30165 = spell(
    id=30165,
    name='Elemental Devastation',
    school=School.NORMAL,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, points_per_level=0.1, implicit_target_a=1, apply_aura=52),
    ],
    spell_icon_id=1930,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases your chance to get a critical strike with melee attacks by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your offensive spell crits will increase your chance to get a critical strike with melee attacks by $30165s1% for $30165d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1073741824, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


elemental_shields_30669 = spell(
    id=30669,
    name='Elemental Shields',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=188),
    ],
    spell_icon_id=2025,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all physical damage taken by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


elemental_absorption_30701 = spell(
    id=30701,
    name='Elemental Absorption',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, points_per_level=0.26666666666666666, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2016,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you take damage from a Fire, Frost or Nature effect, you gain mana equal to $s1% of the damage caused.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 3, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'SpellClassSet': 11},
)


totemic_recall_36936 = spell(
    id=36936,
    name='Totemic Recall',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=110, base_points=24),
    ],
    spell_icon_id=3994,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Returns your totems to the earth, giving you $s1% of the mana required to cast each totem destroyed by Totemic Recall.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11, 'SpellLevel': 30, 'SpellVisualID_1': 8593, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
# Only on a stock TrainerId no NPC uses; 210 is the live Shaman trainer (docs/spell_learn_level.md).
trained_by(totemic_recall_36936, trainer_id=210, req_level=30, money_cost=7000)


stoneskin_totem_38115 = spell(
    id=38115,
    name='Stoneskin Totem',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=41, misc_value=21994),
    ],
    spell_icon_id=690,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneskin Totem with $s1 health at the feet of the caster.  The totem protects party members within $8156a1 yards, reducing melee damage taken by $8156s1.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 81, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 14, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


searing_totem_38116 = spell(
    id=38116,
    name='Searing Totem',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=35000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=44, misc_value=21995),
    ],
    spell_icon_id=680,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Searing Totem with $s1 health at your feet for $d that repeatedly attacks an enemy within $6350r1 yards for $6350s1 Fire damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 63, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 16, 'SpellClassSet': 11, 'SpellLevel': 20, 'SpellVisualID_1': 221, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


lightning_bolt_45284 = spell(
    id=45284,
    name='Lightning Bolt',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(
            type=EffectType.SCHOOL_DAMAGE, base_points=6, points_per_level=4.455696202531645, implicit_target_a=6,
            potency_excluded="percent-of-other-damage: spell_sha_lightning_overload::HandleProc (spell_shaman.cpp) "
            "always overrides this via CastCustomSpell(..., SPELLVALUE_BASE_POINT0, damage, ...) where damage is "
            "half (and, on a crit, quartered) of the triggering Lightning Bolt/Chain Lightning hit's own already-"
            "rolled damage - this spell's own DBC base points are dead/tooltip-only, never read by CalcValue "
            "at runtime, same category as Warlock's Conflagrate/Ignite-style exclusions.",
        ),
    ],
    spell_icon_id=62,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 14 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. '
          "Potency system P7-Shaman: NOT converted despite shaman-potency-report.md proposing 100.6 - this is the Lightning Overload talent's free-cast copy, whose damage is always script-computed as half the triggering hit's damage (see eff0's reason), not an independent potency value.",
    raw_overrides={'AttributesEx': 1024, 'AttributesEx4': 128, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Casts a bolt of lightning at the target for $s1 Nature damage.', 'EffectBonusMultiplier_1': 0.3569999933242798, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 20.0, 'SpellClassMask_1': 1, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellVisualID_1': 173},
)


chain_lightning_45297 = spell(
    id=45297,
    name='Chain Lightning',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(
            type=EffectType.SCHOOL_DAMAGE, base_points=95, points_per_level=8.145833333333334, die_sides=13, implicit_target_a=6, chain_targets=3,
            potency_excluded="percent-of-other-damage: spell_sha_lightning_overload::HandleProc (spell_shaman.cpp) "
            "always overrides this via CastCustomSpell(..., SPELLVALUE_BASE_POINT0, damage, ...) where damage is "
            "half (and, on a crit, quartered) of the triggering Lightning Bolt/Chain Lightning hit's own already-"
            "rolled damage - this spell's own DBC base points are dead/tooltip-only, never read by CalcValue "
            "at runtime, same category as Warlock's Conflagrate/Ignite-style exclusions.",
        ),
    ],
    spell_icon_id=165,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 32); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. '
          "Potency system P7-Shaman: NOT converted despite shaman-potency-report.md proposing 123.4 - this is the Lightning Overload talent's free-cast copy, whose damage is always script-computed as half the triggering hit's damage (see eff0's reason), not an independent potency value.",
    raw_overrides={'AttributesEx': 1024, 'AttributesEx4': 128, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 32, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Hurls a lightning bolt at the enemy, dealing $s1 Nature damage and then jumping to additional nearby enemies.  Each jump reduces the damage by 30%.  Affects $x1 total targets.', 'EffectBonusMultiplier_1': 0.2854999899864197, 'EffectChainAmplitude_1': 0.699999988079071, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2, 'SpellClassSet': 11, 'SpellLevel': 32, 'SpellVisualID_1': 36},
)


earthliving_weapon_passive_51940 = spell(
    id=51940,
    name='Earthliving Weapon (Passive)',
    school=School.NATURE,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=51945),
        Effect(type=EffectType.APPLY_AURA, base_points=25, points_per_level=2.48, implicit_target_a=1, apply_aura=135, misc_value=126),
    ],
    spell_icon_id=1929,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 16777216, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 17408, 'RangeIndex': 1, 'SpellClassMask_2': 1048576, 'SpellClassSet': 11, 'SpellLevel': 30},
)


earthliving_51945 = spell(
    id=51945,
    name='Earthliving',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, sp_potency=5.0, potency_kind='heal_periodic', implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000, time_basis_ms=3000),
    ],
    spell_icon_id=3060,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. '
          'Potency system P7-Shaman: converted to sp_potency=5.1 then SH0a A2 set 5.0 (12 s / 3 s) (shaman-potency-proposals.txt, mismatched row). Cast by the player via earthliving_weapon_passive_51940\'s own PROC_TRIGGER_SPELL aura (triggered off the player\'s own weapon-enchant buff, not a totem/pet).',
    raw_overrides={'AttributesEx3': 128, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Healing over time.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target for {pot1.total} over $d.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 524288, 'SpellClassSet': 11, 'SpellLevel': 30, 'SpellVisualID_1': 11443, 'StartRecoveryCategory': 133},
)


flametongue_totem_52109 = spell(
    id=52109,
    name='Flametongue Totem',
    school=School.NATURE,
    attributes=320,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=65, base_points=24, points_per_level=2.7045454545454546, implicit_target_a=22, implicit_target_b=33, apply_aura=AuraType.MOD_DAMAGE_DONE, misc_value=126, radius_yards=30.0),
        Effect(type=65, base_points=24, points_per_level=2.7045454545454546, implicit_target_a=22, implicit_target_b=33, apply_aura=135, misc_value=127, radius_yards=30.0),
    ],
    spell_icon_id=72,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 28); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 72); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Magical damage and healing from spells and effects increased by up to $s1.', 'BaseLevel': 28, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712188, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 33554432, 'SpellClassSet': 11, 'SpellLevel': 28},
)


water_shield_52127 = spell(
    id=52127,
    name='Water Shield',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, points_per_level=6.466666666666667, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=52128),
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=0.75, implicit_target_a=1, apply_aura=85),
    ],
    spell_icon_id=2287,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx3': 196608, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Water Shield restores mana.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The caster is surrounded by $52127n globes of water, granting $52127s2 mana per 5 sec.  When a spell, melee or ranged attack hits the caster, $52128s1 mana is restored to the caster. This expends one water globe.  Only one globe will activate every few seconds.  Lasts $52127d.  Only one Elemental Shield can be active on the Shaman at any one time.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 60, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 3, 'ProcTypeMask': 139944, 'RangeIndex': 1, 'SpellClassMask_2': 32, 'SpellClassSet': 11, 'SpellLevel': 20, 'SpellVisualID_1': 7358, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
# Only on a stock TrainerId no NPC uses; 210 is the live Shaman trainer (docs/spell_learn_level.md).
trained_by(water_shield_52127, trainer_id=210, req_level=20, money_cost=2200)


totem_of_wrath_57658 = spell(
    id=57658,
    name='Totem of Wrath',
    school=School.FIRE,
    attributes=320,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=65, base_points=99, points_per_level=6.0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE, misc_value=126, radius_yards=40.0),
        Effect(type=65, base_points=99, points_per_level=6.0, implicit_target_a=1, apply_aura=135, misc_value=127, radius_yards=40.0),
    ],
    spell_icon_id=2019,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increase spell power by $s1 and increases the critical strike chance on all nearby targets within $a1 yards by $30708s1%.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712172, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 67108864, 'SpellClassMask_2': 33554432, 'SpellClassSet': 11, 'SpellLevel': 50},
)


lava_flows_haste_64694 = spell(
    id=64694,
    name='Lava Flows',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        _aura(216, 1),
        _aura(AuraType.MOD_MELEE_HASTE, 1),
    ],
    spell_icon_id=3087,
    notes='S1a A2 (docs/reworks/shaman-elemental-rework.md Lava Flows): rank 1 haste buff, spell + melee haste 2% for 12 s, '
          'cast by spell_sha_ele_spell_hooks on Flame Shock / Lava Burst (Shaman::LavaFlowsHasteSpell). Not in the haste '
          'group (brief Decision 8). Variable renamed from lava_flows_64694 so the header name is SPELL_LAVA_FLOWS_HASTE. '
          'The stock aura 65 dispel clause and the latent raw effect 2/3 twins are gone.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Haste increased.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell and melee haste.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


concussion_16035 = _talent(
    16035, 'Concussion', 'Rank 1',
    [_mod(SpellModOp.DAMAGE, 4), _mod(SpellModOp.DAMAGE, 2), _mod(SpellModOp.DOT, 2)], 12,
    'Increases the damage of your Lightning Bolt and Chain Lightning by 5%. Increases the damage of your Thunderstorm, Lava Burst, Earthquake, Elemental Blast and Shock spells by 3%.',
    masks={1: (_LB | _CL, 0, 0), 2: (_SHOCKS, _LAVA_BURST | _THUNDERSTORM, m.EARTHQUAKE | m.ELEMENTAL_BLAST),
           3: (_FLAME_SHOCK, 0, 0)},
    notes='S1a A2: eff1 Lightning Bolt / Chain Lightning +5%, eff2 the rest +3% (talent_mult effect 2), eff3 the Flame Shock periodic at +3% (SPELLMOD_DOT, the engine never applies DAMAGE to a tick). Copies inherit by parent bit.',
)


call_of_flame_16038 = _talent(
    16038, 'Call of Flame', 'Rank 1',
    [_mod(SpellModOp.DAMAGE, 9), _mod(SpellModOp.DAMAGE, 4), _mod(SpellModOp.COST, -11)], 31,
    'Increases the damage and reduces the mana cost of your Fire totems and Fire Nova by 10%. Increases the damage of your Lava Burst by 5%.',
    masks={1: (m.SEARING_MAGMA_BOLT, _FIRE_NOVA_DAMAGE, 0), 2: (0, _LAVA_BURST, 0),
           3: (_SEARING_SUMMON | m.MAGMA_SUMMON_D0_B12 | _FIRE_NOVA_COST, 0, 0)},
    notes='S1a A2 (brief Decision 9): eff1 Searing bolt + Magma pulse (d0 b30) and Fire Nova 8349 (d1 b18) +10%, eff2 Lava Burst +5%, eff3 cost on Searing 3599 (d0 b4), Magma 202268 (d0 b12) and Fire Nova 1535 (d0 b27) -10%. Never d0 b29 or d1 b23 (the Fire Elemental is not a Fire totem).',
)


convection_16039 = _talent(
    16039, 'Convection', 'Rank 1',
    [_mod(SpellModOp.COST, -6), _mod(SpellModOp.DAMAGE, 1), _mod(SpellModOp.DOT, 1)], 122,
    'Reduces the mana cost of your Shock, Lightning Bolt, Chain Lightning, Lava Burst, Earthquake and Wind Shear spells by 5% and increases their damage by 2%.',
    masks={1: (_SHOCKS | _LB | _CL, _LAVA_BURST | _WIND_SHEAR, m.EARTHQUAKE),
           2: (_SHOCKS | _LB | _CL, _LAVA_BURST, m.EARTHQUAKE), 3: (_FLAME_SHOCK, 0, 0)},
    notes='S1a A2 (brief Decision 7): eff1 cost (Wind Shear by its own d1 b27, never b11), eff2 damage on the same minus Wind Shear (talent_mult effect 2), eff3 the Flame Shock tick. Rank 2 no longer carries Thunderstorm (d1 b13).',
)


reverberation_16040 = _talent(
    16040, 'Reverberation', 'Rank 1',
    [_mod(SpellModOp.COOLDOWN, -501, pct=False)], 501,
    'Reduces the cooldown of your Shock spells by 0.5 sec. When you deal damage with a Shock spell, the direct damage of your next different Shock spell or Elemental Blast within 8 sec is increased by 20%.',
    masks={1: (_SHOCKS, 0, 0)},
    notes='S1a A2 (brief Decision 7): cooldown on the three shocks only; Wind Shear (d1 b27) dropped from the mask. The grant is spell_sha_ele_spell_hooks, the buffs are the Reverberation variants.',
)


call_of_thunder_16041 = _talent(
    16041, 'Call of Thunder', 'Rank 1',
    [_mod(SpellModOp.CRITICAL_CHANCE, 1, pct=False)], 141,
    _desc('Increases the critical strike chance of your Lightning Bolt, Chain Lightning and Thunderstorm by 2%.',
          'Thunderstorm can be cast while stunned.'),
    masks={1: (_LB | _CL, _THUNDERSTORM, 0)},
    notes='S1a A2: flat crit +2% on Lightning Bolt / Chain Lightning / Thunderstorm. The capstone (rank 3) is the second Thunderstorm rank 202594, granted by Shaman::SyncThunderstormRank.',
)


earth_s_grasp_16043 = spell(
    id=16043,
    name="Earth's Grasp",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=689,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the health of your Stoneclaw Totem by $s1% and the radius of your Earthbind Totem by $s2%, and reduces the cooldown of both totems by $s3%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8, 'EffectSpellClassMaskB_2': 1, 'EffectSpellClassMaskB_3': 16384, 'EffectSpellClassMaskC_1': 8, 'EffectSpellClassMaskC_3': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_fire_nova_16086 = _talent(
    16086, 'Rising Flames', 'Rank 1',
    [_mod(SpellModOp.CRIT_DAMAGE_BONUS, 49), _mod(SpellModOp.COOLDOWN, -2001, pct=False)], 33,
    _desc('Increases the critical strike damage bonus of your Searing Totem and Magma Totem by 50% and reduces the cooldown of your Fire Nova by 2 sec.',
          'While your Magma Totem or Fire Elemental is active, you gain a stack of Rising Flames every 2 sec, up to 5. Each stack increases the damage of your next Fire Nova by 10%. Fire Nova consumes all stacks.'),
    masks={1: (m.SEARING_MAGMA_BOLT, 0, 0), 2: (_FIRE_NOVA_COST, 0, 0)}, ProcChance=100,
    notes='S1a A2: repurposed Improved Fire Nova. eff1 crit damage bonus on Searing bolt + Magma pulse (d0 b30), eff2 Fire Nova 1535 cooldown (d0 b27). The stock damage effect and the latent EffectBasePoints_3 twin are gone.',
)


elemental_fury_16089 = _talent(
    16089, 'Elemental Fury', '',
    [_mod(SpellModOp.CRIT_DAMAGE_BONUS, 29)], 1137,
    _desc('Your spell critical strikes deal 165% damage. Does not stack with other similar effects.',
          'While Clearcasting from Elemental Focus is active, your Nature damage is increased by 8% and your other magic damage by 5%.'),
    masks={1: (0xD1300003, 0x43000, m.EARTHQUAKE | m.ELEMENTAL_BLAST)},
    notes='S1a A2: crit damage bonus +30% of the 50% base bonus (165%). Stock mask plus d2 b19 / b20 (Earthquake, Elemental Blast). The capstone is the hidden aura 202584 (spell_sha_ele_fury_capstone on Clearcasting).',
)


concussion_16105 = _talent(
    16105, 'Concussion', 'Rank 2',
    [_mod(SpellModOp.DAMAGE, 9), _mod(SpellModOp.DAMAGE, 5), _mod(SpellModOp.DOT, 5)], 12,
    'Increases the damage of your Lightning Bolt and Chain Lightning by 10%. Increases the damage of your Thunderstorm, Lava Burst, Earthquake, Elemental Blast and Shock spells by 6%.',
    masks={1: (_LB | _CL, 0, 0), 2: (_SHOCKS, _LAVA_BURST | _THUNDERSTORM, m.EARTHQUAKE | m.ELEMENTAL_BLAST),
           3: (_FLAME_SHOCK, 0, 0)},
    notes='S1a A2: see concussion_16035.',
)


concussion_16106 = _talent(
    16106, 'Concussion', 'Rank 3',
    [_mod(SpellModOp.DAMAGE, 14), _mod(SpellModOp.DAMAGE, 9), _mod(SpellModOp.DOT, 9)], 12,
    'Increases the damage of your Lightning Bolt and Chain Lightning by 15%. Increases the damage of your Thunderstorm, Lava Burst, Earthquake, Elemental Blast and Shock spells by 10%.',
    masks={1: (_LB | _CL, 0, 0), 2: (_SHOCKS, _LAVA_BURST | _THUNDERSTORM, m.EARTHQUAKE | m.ELEMENTAL_BLAST),
           3: (_FLAME_SHOCK, 0, 0)},
    notes='S1a A2: see concussion_16035.',
)


concussion_16107 = spell(
    id=16107,
    name='Concussion',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=12,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Lightning Bolt, Chain Lightning, Thunderstorm, Lava Burst and Shock spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2416967683, 'EffectSpellClassMaskA_2': 12288, 'EffectSpellClassMaskB_1': 268435456, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


concussion_16108 = spell(
    id=16108,
    name='Concussion',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=12,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Lightning Bolt, Chain Lightning, Thunderstorm, Lava Burst and Shock spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2416967683, 'EffectSpellClassMaskA_2': 12288, 'EffectSpellClassMaskB_1': 268435456, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


convection_16109 = _talent(
    16109, 'Convection', 'Rank 2',
    [_mod(SpellModOp.COST, -11), _mod(SpellModOp.DAMAGE, 3), _mod(SpellModOp.DOT, 3)], 122,
    'Reduces the mana cost of your Shock, Lightning Bolt, Chain Lightning, Lava Burst, Earthquake and Wind Shear spells by 10% and increases their damage by 4%.',
    masks={1: (_SHOCKS | _LB | _CL, _LAVA_BURST | _WIND_SHEAR, m.EARTHQUAKE),
           2: (_SHOCKS | _LB | _CL, _LAVA_BURST, m.EARTHQUAKE), 3: (_FLAME_SHOCK, 0, 0)},
    notes='S1a A2: see convection_16039.',
)


convection_16110 = _talent(
    16110, 'Convection', 'Rank 3',
    [_mod(SpellModOp.COST, -16), _mod(SpellModOp.DAMAGE, 5), _mod(SpellModOp.DOT, 5)], 122,
    'Reduces the mana cost of your Shock, Lightning Bolt, Chain Lightning, Lava Burst, Earthquake and Wind Shear spells by 15% and increases their damage by 6%.',
    masks={1: (_SHOCKS | _LB | _CL, _LAVA_BURST | _WIND_SHEAR, m.EARTHQUAKE),
           2: (_SHOCKS | _LB | _CL, _LAVA_BURST, m.EARTHQUAKE), 3: (_FLAME_SHOCK, 0, 0)},
    notes='S1a A2: see convection_16039.',
)


convection_16111 = spell(
    id=16111,
    name='Convection',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-9, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=122,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Shock, Lightning Bolt, Chain Lightning, Lava Burst, and Wind Shear spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2416967683, 'EffectSpellClassMaskA_2': 134221824, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


convection_16112 = spell(
    id=16112,
    name='Convection',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=122,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Shock, Lightning Bolt, Chain Lightning, Lava Burst, and Wind Shear spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2416967683, 'EffectSpellClassMaskA_2': 134221824, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


reverberation_16113 = _talent(
    16113, 'Reverberation', 'Rank 2',
    [_mod(SpellModOp.COOLDOWN, -1001, pct=False)], 501,
    'Reduces the cooldown of your Shock spells by 1 sec. When you deal damage with a Shock spell, the direct damage of your next different Shock spell or Elemental Blast within 8 sec is increased by 20%.',
    masks={1: (_SHOCKS, 0, 0)},
    notes='S1a A2: see reverberation_16040.',
)


reverberation_16114 = _talent(
    16114, 'Reverberation', 'Rank 3',
    [_mod(SpellModOp.COOLDOWN, -1501, pct=False)], 501,
    'Reduces the cooldown of your Shock spells by 1.5 sec. When you deal damage with a Shock spell, the direct damage of your next different Shock spell or Elemental Blast within 8 sec is increased by 20%.',
    masks={1: (_SHOCKS, 0, 0)},
    notes='S1a A2: see reverberation_16040.',
)


reverberation_16115 = spell(
    id=16115,
    name='Reverberation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-801, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=501,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Shock and Wind Shear spells by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2416967680, 'EffectSpellClassMaskA_2': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


reverberation_16116 = spell(
    id=16116,
    name='Reverberation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=501,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Shock and Wind Shear spells by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2416967680, 'EffectSpellClassMaskA_2': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


earth_s_grasp_16130 = spell(
    id=16130,
    name="Earth's Grasp",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=689,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the health of your Stoneclaw Totem by $s1% and the radius of your Earthbind Totem by $s2%, and reduces the cooldown of both totems by $s3%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8, 'EffectSpellClassMaskB_2': 1, 'EffectSpellClassMaskB_3': 16384, 'EffectSpellClassMaskC_1': 8, 'EffectSpellClassMaskC_3': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


call_of_flame_16160 = _talent(
    16160, 'Call of Flame', 'Rank 2',
    [_mod(SpellModOp.DAMAGE, 19), _mod(SpellModOp.DAMAGE, 9), _mod(SpellModOp.COST, -21)], 31,
    'Increases the damage and reduces the mana cost of your Fire totems and Fire Nova by 20%. Increases the damage of your Lava Burst by 10%.',
    masks={1: (m.SEARING_MAGMA_BOLT, _FIRE_NOVA_DAMAGE, 0), 2: (0, _LAVA_BURST, 0),
           3: (_SEARING_SUMMON | m.MAGMA_SUMMON_D0_B12 | _FIRE_NOVA_COST, 0, 0)},
    notes='S1a A2: see call_of_flame_16038.',
)


call_of_flame_16161 = _talent(
    16161, 'Call of Flame', 'Rank 3',
    [_mod(SpellModOp.DAMAGE, 29), _mod(SpellModOp.DAMAGE, 14), _mod(SpellModOp.COST, -31)], 31,
    'Increases the damage and reduces the mana cost of your Fire totems and Fire Nova by 30%. Increases the damage of your Lava Burst by 15%.',
    masks={1: (m.SEARING_MAGMA_BOLT, _FIRE_NOVA_DAMAGE, 0), 2: (0, _LAVA_BURST, 0),
           3: (_SEARING_SUMMON | m.MAGMA_SUMMON_D0_B12 | _FIRE_NOVA_COST, 0, 0)},
    notes='S1a A2: see call_of_flame_16038.',
)


elemental_focus_16164 = _talent(
    16164, 'Elemental Focus', '',
    [_dummy(14)], 212,
    'After landing a critical strike with a Fire, Frost or Nature damage spell, you enter a Clearcasting state that reduces the mana cost of your next two Fire, Frost or Nature spells by 15%.',
    level=1, AttributesEx3=0x4000000, ProcTypeMask=_PROC_DONE_SPELL_MAGIC_NEG, ProcChance=100,
    notes='S1a A2 (brief Decision 5): rank 1. The proc effect is a DUMMY (the PROC_TRIGGER_SPELL to 16246 is gone: spell_sha_ele_elemental_focus casts Clearcasting and sets the amount, here 15 live). Row moved to the chain key -16164.',
)


totemic_focus_16173 = spell(
    id=16173,
    name='Totemic Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=46,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your totems by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 537399320, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


ancestral_healing_16176 = spell(
    id=16176,
    name='Ancestral Healing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=ancestral_fortitude_16177.id),
    ],
    spell_icon_id=200,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces your target's physical damage taken by $16177s1% for $16177d after getting a critical effect from one of your healing spells.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 11},
)


purification_16178 = spell(
    id=16178,
    name='Purification',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=136, misc_value=127),
    ],
    spell_icon_id=133,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effectiveness of your healing spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


tidal_focus_16179 = spell(
    id=16179,
    name='Tidal Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=36,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your healing spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EffectSpellClassMaskA_2': 1024, 'EffectSpellClassMaskA_3': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_water_shield_16180 = spell(
    id=16180,
    name='Improved Water Shield',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2287,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a $s1% chance to instantly gain mana as if you consumed a Water Shield Orb when you gain a critical effect from your Healing Wave or Riptide spells, a ${$m1*0.6}% chance when you gain a critical effect from your Lesser Healing Wave spell, and a ${$m1*0.3}% chance when you gain a critical effect from your Chain Heal spell.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 11},
)


healing_focus_16181 = spell(
    id=16181,
    name='Healing Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=22, implicit_target_a=1, apply_aura=108, misc_value=9),
    ],
    spell_icon_id=964,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the pushback suffered from damaging attacks while casting any Shaman healing spell by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_healing_wave_16182 = spell(
    id=16182,
    name='Improved Healing Wave',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=13,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Healing Wave spell by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 64, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_reincarnation_16184 = spell(
    id=16184,
    name='Improved Reincarnation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-420001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Reincarnation spell by $/60000;s1 min and increases the amount of health and mana recovered when reincarnating by an additional $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 512, 'EffectSpellClassMaskB_1': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


restorative_totems_16187 = spell(
    id=16187,
    name='Restorative Totems',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=8),
    ],
    spell_icon_id=338,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Mana Spring Totem by $s1%, and increases the amount healed by your Healing Stream Totem by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16384, 'EffectSpellClassMaskB_1': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


tidal_mastery_16194 = spell(
    id=16194,
    name='Tidal Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=100,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your healing and lightning spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1475, 'EffectSpellClassMaskA_2': 8192, 'EffectSpellClassMaskA_3': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 64, 'SpellClassSet': 11},
)


improved_water_shield_16196 = spell(
    id=16196,
    name='Improved Water Shield',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2287,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a $s1% chance to instantly gain mana as if you consumed a Water Shield Orb when you gain a critical effect from your Healing Wave or Riptide spells, a ${$m1*0.6}% chance when you gain a critical effect from your Lesser Healing Wave spell, and a ${$m1*0.3}% chance when you gain a critical effect from your Chain Heal spell.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_water_shield_16198 = spell(
    id=16198,
    name='Improved Water Shield',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2287,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a $s1% chance to instantly gain mana as if you consumed a Water Shield Orb when you gain a critical effect from your Healing Wave or Riptide spells, a ${$m1*0.6}% chance when you gain a critical effect from your Lesser Healing Wave spell, and a ${$m1*0.3}% chance when you gain a critical effect from your Chain Heal spell.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 11},
)


restorative_totems_16205 = spell(
    id=16205,
    name='Restorative Totems',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=8),
    ],
    spell_icon_id=338,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Mana Spring Totem by $s1%, and increases the amount healed by your Healing Stream Totem by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16384, 'EffectSpellClassMaskB_1': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


restorative_totems_16206 = spell(
    id=16206,
    name='Restorative Totems',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=44, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=8),
    ],
    spell_icon_id=338,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Mana Spring Totem by $s1%, and increases the amount healed by your Healing Stream Totem by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16384, 'EffectSpellClassMaskB_1': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_reincarnation_16209 = spell(
    id=16209,
    name='Improved Reincarnation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-900001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Reincarnation spell by $/60000;s1 min and increases the amount of health and mana recovered when reincarnating by an additional $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 512, 'EffectSpellClassMaskB_1': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


purification_16210 = spell(
    id=16210,
    name='Purification',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=136, misc_value=127),
    ],
    spell_icon_id=133,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effectiveness of your healing spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


purification_16211 = spell(
    id=16211,
    name='Purification',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=136, misc_value=127),
    ],
    spell_icon_id=133,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effectiveness of your healing spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


purification_16212 = spell(
    id=16212,
    name='Purification',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=136, misc_value=127),
    ],
    spell_icon_id=133,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effectiveness of your healing spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


purification_16213 = spell(
    id=16213,
    name='Purification',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=136, misc_value=127),
    ],
    spell_icon_id=133,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effectiveness of your healing spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


tidal_focus_16214 = spell(
    id=16214,
    name='Tidal Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=36,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your healing spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EffectSpellClassMaskA_2': 1024, 'EffectSpellClassMaskA_3': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


tidal_focus_16215 = spell(
    id=16215,
    name='Tidal Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=36,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your healing spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EffectSpellClassMaskA_2': 1024, 'EffectSpellClassMaskA_3': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


tidal_focus_16216 = spell(
    id=16216,
    name='Tidal Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=36,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your healing spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EffectSpellClassMaskA_2': 1024, 'EffectSpellClassMaskA_3': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


tidal_focus_16217 = spell(
    id=16217,
    name='Tidal Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=36,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your healing spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EffectSpellClassMaskA_2': 1024, 'EffectSpellClassMaskA_3': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


tidal_mastery_16218 = spell(
    id=16218,
    name='Tidal Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=100,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your healing and lightning spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1475, 'EffectSpellClassMaskA_2': 8192, 'EffectSpellClassMaskA_3': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 64, 'SpellClassSet': 11},
)


tidal_mastery_16219 = spell(
    id=16219,
    name='Tidal Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=100,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your healing and lightning spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1475, 'EffectSpellClassMaskA_2': 8192, 'EffectSpellClassMaskA_3': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 64, 'SpellClassSet': 11},
)


tidal_mastery_16220 = spell(
    id=16220,
    name='Tidal Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=100,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your healing and lightning spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1475, 'EffectSpellClassMaskA_2': 8192, 'EffectSpellClassMaskA_3': 80, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


tidal_mastery_16221 = spell(
    id=16221,
    name='Tidal Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=100,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your healing and lightning spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1475, 'EffectSpellClassMaskA_2': 8192, 'EffectSpellClassMaskA_3': 80, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


totemic_focus_16222 = spell(
    id=16222,
    name='Totemic Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=46,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your totems by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 537399320, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


totemic_focus_16223 = spell(
    id=16223,
    name='Totemic Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=46,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your totems by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 537399320, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


totemic_focus_16224 = spell(
    id=16224,
    name='Totemic Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=46,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your totems by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 537399320, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


totemic_focus_16225 = spell(
    id=16225,
    name='Totemic Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=46,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your totems by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 537399320, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_healing_wave_16226 = spell(
    id=16226,
    name='Improved Healing Wave',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-201, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=13,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Healing Wave spell by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 64, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_healing_wave_16227 = spell(
    id=16227,
    name='Improved Healing Wave',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-301, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=13,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Healing Wave spell by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 64, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_healing_wave_16228 = spell(
    id=16228,
    name='Improved Healing Wave',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-401, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=13,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Healing Wave spell by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 64, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_healing_wave_16229 = spell(
    id=16229,
    name='Improved Healing Wave',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-501, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=13,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Healing Wave spell by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 64, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


healing_focus_16230 = spell(
    id=16230,
    name='Healing Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=45, implicit_target_a=1, apply_aura=108, misc_value=9),
    ],
    spell_icon_id=964,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the pushback suffered from damaging attacks while casting any Shaman healing spell by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


healing_focus_16232 = spell(
    id=16232,
    name='Healing Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=69, implicit_target_a=1, apply_aura=108, misc_value=9),
    ],
    spell_icon_id=964,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the pushback suffered from damaging attacks while casting any Shaman healing spell by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


ancestral_healing_16235 = spell(
    id=16235,
    name='Ancestral Healing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=16236),
    ],
    spell_icon_id=200,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces your target's physical damage taken by $16236s1% for $16236d after getting a critical effect from one of your healing spells.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 11},
)


ancestral_healing_16240 = spell(
    id=16240,
    name='Ancestral Healing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=16237),
    ],
    spell_icon_id=200,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces your target's physical damage taken by $16237s1% for $16237d after getting a critical effect from one of your healing spells.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 11},
)


guardian_totems_16258 = spell(
    id=16258,
    name='Guardian Totems',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=-1001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=690,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount of armor increased by your Stoneskin Totem by $s1% and reduces the cooldown of your Grounding Totem by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 32768, 'EffectSpellClassMaskB_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


enhancing_totems_16259 = spell(
    id=16259,
    name='Enhancing Totems',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=691,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Strength of Earth and Flametongue Totems by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_shields_16261 = spell(
    id=16261,
    name='Improved Shields',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=3),
    ],
    spell_icon_id=19,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Lightning Shield orbs by $s1%, increases the amount of mana gained from your Water Shield orbs by $s2% and increases the amount of healing done by your Earth Shield orbs by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EffectSpellClassMaskB_2': 1056, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_ghost_wolf_16262 = spell(
    id=16262,
    name='Improved Ghost Wolf',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1001, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=67,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cast time of your Ghost Wolf spell by $/1000;s1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 2048, 'EffectSpellClassMaskA_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


elemental_weapons_16266 = spell(
    id=16266,
    name='Elemental Weapons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=12, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=679,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage caused by your Windfury Weapon effect by $s3%  increases the spell damage on your Flametongue Weapon by $s2% and increases the bonus healing on your Earthliving Weapon by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 1048576, 'EffectSpellClassMaskB_1': 2097152, 'EffectSpellClassMaskC_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_ghost_wolf_16287 = spell(
    id=16287,
    name='Improved Ghost Wolf',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=107, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=67,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cast time of your Ghost Wolf spell by $/1000;s1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2048, 'EffectSpellClassMaskB_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 8, 'SpellClassSet': 11},
)


improved_shields_16290 = spell(
    id=16290,
    name='Improved Shields',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=3),
    ],
    spell_icon_id=19,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Lightning Shield orbs by $s1%, increases the amount of mana gained from your Water Shield orbs by $s2% and increases the amount of healing done by your Earth Shield orbs by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EffectSpellClassMaskB_2': 1056, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


guardian_totems_16293 = spell(
    id=16293,
    name='Guardian Totems',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=690,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount of armor increased by your Stoneskin Totem by $s1% and reduces the cooldown of your Grounding Totem by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 32768, 'EffectSpellClassMaskB_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


enhancing_totems_16295 = spell(
    id=16295,
    name='Enhancing Totems',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=691,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Strength of Earth and Flametongue Totems by $s1%.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 33619968, 'EffectSpellClassMaskB_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_fire_nova_16544 = _talent(
    16544, 'Rising Flames', 'Rank 2',
    [_mod(SpellModOp.CRIT_DAMAGE_BONUS, 99), _mod(SpellModOp.COOLDOWN, -4001, pct=False),
     _aura(AuraType.PERIODIC_DUMMY, 0, amplitude=2000)], 33,
    _desc('Increases the critical strike damage bonus of your Searing Totem and Magma Totem by 100% and reduces the cooldown of your Fire Nova by 4 sec.',
          'While your Magma Totem or Fire Elemental is active, you gain a stack of Rising Flames every 2 sec, up to 5. Each stack increases the damage of your next Fire Nova by 10%. Fire Nova consumes all stacks.',
          last=True),
    masks={1: (m.SEARING_MAGMA_BOLT, 0, 0), 2: (_FIRE_NOVA_COST, 0, 0)}, ProcChance=100,
    notes='S1a A2: rank 2 capstone. eff3 is the PERIODIC_DUMMY (amplitude 2000 = RISING_FLAMES_TICK_MS) spell_sha_ele_rising_flames hooks (EFFECT_FIRST_FOUND).',
)


lightning_mastery_16578 = _talent(
    16578, 'Lightning Mastery', 'Rank 1',
    [_dummy(32)], 320,
    'Your spell casts that critically strike have a 33% chance to grant you a stack of Raw Power. While Raw Power is active, your Lightning Bolt and Chain Lightning casts that critically strike have a 7% chance per stack to trigger Lightning Mastery, consuming all Raw Power to increase your spell critical strike damage bonus by 50% for 8 sec.',
    ProcTypeMask=_PROC_DONE_SPELL_MAGIC_NEG, ProcChance=100,
    notes='S1a A2: the cast time cut is gone. DUMMY proc carrier (amount = Raw Power chance 33 live); the rolls are spell_sha_ele_lightning_mastery.',
)


lightning_mastery_16579 = _talent(
    16579, 'Lightning Mastery', 'Rank 2',
    [_dummy(65)], 320,
    'Your spell casts that critically strike have a 66% chance to grant you a stack of Raw Power. While Raw Power is active, your Lightning Bolt and Chain Lightning casts that critically strike have a 7% chance per stack to trigger Lightning Mastery, consuming all Raw Power to increase your spell critical strike damage bonus by 50% for 8 sec.',
    ProcTypeMask=_PROC_DONE_SPELL_MAGIC_NEG, ProcChance=100,
    notes='S1a A2: see lightning_mastery_16578.',
)


lightning_mastery_16580 = _talent(
    16580, 'Lightning Mastery', 'Rank 3',
    [_dummy(99)], 320,
    'Your spell casts that critically strike have a 100% chance to grant you a stack of Raw Power. While Raw Power is active, your Lightning Bolt and Chain Lightning casts that critically strike have a 7% chance per stack to trigger Lightning Mastery, consuming all Raw Power to increase your spell critical strike damage bonus by 50% for 8 sec.',
    ProcTypeMask=_PROC_DONE_SPELL_MAGIC_NEG, ProcChance=100,
    notes='S1a A2: see lightning_mastery_16578.',
)


lightning_mastery_16581 = spell(
    id=16581,
    name='Lightning Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-401, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=320,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cast time of your Lightning Bolt, Chain Lightning, and Lava Burst spells by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3, 'EffectSpellClassMaskA_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


lightning_mastery_16582 = spell(
    id=16582,
    name='Lightning Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-501, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=320,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cast time of your Lightning Bolt, Chain Lightning, and Lava Burst spells by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3, 'EffectSpellClassMaskA_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


elemental_warding_28996 = _talent(
    28996, 'Elemental Warding', 'Rank 1',
    [_aura(AuraType.MOD_CUSTOM_STAT_PCT, 0, _CR_VERSATILITY)], 198,
    _desc('Increases your Versatility by 1%.',
          'Your Earth Elemental deals 20% more damage, and while it is active your maximum health is increased by 10%.'),
    notes='S1a A2: Versatility +1% (aura 306, misc 1 << 21). The capstone is C++ (Earth Elemental +20% guardian aura, +10% health aura 202585).',
)


elemental_warding_28997 = _talent(
    28997, 'Elemental Warding', 'Rank 2',
    [_aura(AuraType.MOD_CUSTOM_STAT_PCT, 1, _CR_VERSATILITY)], 198,
    _desc('Increases your Versatility by 2%.',
          'Your Earth Elemental deals 20% more damage, and while it is active your maximum health is increased by 10%.'),
    notes='S1a A2: see elemental_warding_28996.',
)


elemental_warding_28998 = _talent(
    28998, 'Elemental Warding', 'Rank 3',
    [_aura(AuraType.MOD_CUSTOM_STAT_PCT, 2, _CR_VERSATILITY)], 198,
    _desc('Increases your Versatility by 3%.',
          'Your Earth Elemental deals 20% more damage, and while it is active your maximum health is increased by 10%.',
          last=True),
    notes='S1a A2: see elemental_warding_28996.',
)


elemental_reach_28999 = _talent(
    28999, 'Elemental Reach', 'Rank 1',
    [_mod(SpellModOp.RANGE, 2, pct=False)], 1921,
    _desc('Increases the range of your damaging spells by 3 yards. Does not stack with other similar effects.',
          'Your direct damage Fire, Frost and Nature spells against targets more than 20 yards away have a 33% chance to increase your magic damage by 6% for 10 sec. This effect can only occur once every 15 sec.'),
    masks={1: (_SHOCKS | _LB | _CL, _LAVA_BURST, m.EARTHQUAKE | m.ELEMENTAL_BLAST)},
    notes='S1a A2: range +3 yd on shaman damage spells only (Lightning Bolt, Chain Lightning, Lava Burst, the shocks, Earthquake cast, Elemental Blast). The stock Fire Nova, Thunderstorm radius and Flame Shock effects are gone.',
)


elemental_reach_29000 = _talent(
    29000, 'Elemental Reach', 'Rank 2',
    [_mod(SpellModOp.RANGE, 5, pct=False), _dummy(0)], 1921,
    _desc('Increases the range of your damaging spells by 6 yards. Does not stack with other similar effects.',
          'Your direct damage Fire, Frost and Nature spells against targets more than 20 yards away have a 33% chance to increase your magic damage by 6% for 10 sec. This effect can only occur once every 15 sec.',
          last=True),
    masks={1: (_SHOCKS | _LB | _CL, _LAVA_BURST, m.EARTHQUAKE | m.ELEMENTAL_BLAST)},
    ProcTypeMask=_PROC_DONE_SPELL_MAGIC_NEG, ProcChance=100,
    notes='S1a A2: rank 2 capstone; eff2 DUMMY is the proc carrier for spell_sha_ele_reach_capstone (spell_proc 29000, 100% - the script rolls 33% x Proc Chance).',
)


eye_of_the_storm_29062 = _talent(
    29062, 'Eye of the Storm', 'Rank 1',
    [_aura(AuraType.HASTE_ALL, 0), _mod(SpellModOp.NOT_LOSE_CASTING_TIME, 32)], 2028,
    _desc('Increases your spell, ranged and melee haste by 1%. Reduces the pushback suffered from damaging attacks while casting by 33%.',
          "Your Chain Lightning's damage is reduced by only 10% per jump, instead of 30%."),
    masks={2: (_LB | _CL, 0x9000, 0)},
    notes='S1a A2: eff1 haste +1% (aura 193), eff2 pushback (stock op and mask, values 33/66/100 stored 32/65/99 as the hunter precedent).',
)


eye_of_the_storm_29064 = _talent(
    29064, 'Eye of the Storm', 'Rank 2',
    [_aura(AuraType.HASTE_ALL, 1), _mod(SpellModOp.NOT_LOSE_CASTING_TIME, 65)], 2028,
    _desc('Increases your spell, ranged and melee haste by 2%. Reduces the pushback suffered from damaging attacks while casting by 66%.',
          "Your Chain Lightning's damage is reduced by only 10% per jump, instead of 30%."),
    masks={2: (_LB | _CL, 0x9000, 0)},
    notes='S1a A2: see eye_of_the_storm_29062.',
)


eye_of_the_storm_29065 = _talent(
    29065, 'Eye of the Storm', 'Rank 3',
    [_aura(AuraType.HASTE_ALL, 2), _mod(SpellModOp.NOT_LOSE_CASTING_TIME, 99),
     _mod(SpellModOp.DAMAGE_MULTIPLIER, 28)], 2028,
    _desc('Increases your spell, ranged and melee haste by 3%. Reduces the pushback suffered from damaging attacks while casting by 100%.',
          "Your Chain Lightning's damage is reduced by only 10% per jump, instead of 30%.", last=True),
    masks={2: (_LB | _CL, 0x9000, 0), 3: (_CL, 0, 0)},
    notes='S1a A2 (brief Decision 2): eff3 capstone, SPELLMOD_DAMAGE_MULTIPLIER pct stored 28 (live 29): the per-jump factor 0.7 * 1.29 = 0.903, the nearest an additive percent mod reaches to the doc 0.9 (S1a 0-verify section 6). DEVIATION: 0.903, not 0.9.',
)


elemental_weapons_29079 = spell(
    id=29079,
    name='Elemental Weapons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=26, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=679,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage caused by your Windfury Weapon effect by $s3%  increases the spell damage on your Flametongue Weapon by $s2% and increases the bonus healing on your Earthliving Weapon by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 1048576, 'EffectSpellClassMaskB_1': 2097152, 'EffectSpellClassMaskC_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


elemental_weapons_29080 = spell(
    id=29080,
    name='Elemental Weapons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=679,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage caused by your Windfury Weapon effect by $s3%  increases the spell damage on your Flametongue Weapon by $s2% and increases the bonus healing on your Earthliving Weapon by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 1048576, 'EffectSpellClassMaskB_1': 2097152, 'EffectSpellClassMaskC_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


elemental_devastation_29179 = _talent(
    29179, 'Elemental Devastation', 'Rank 2',
    [_dummy(5)], 1930,
    'Your non-periodic Fire, Frost and Nature spell critical strikes increase your Proc Chance by 6% for 10 sec.',
    AttributesEx3=0x4000000, ProcTypeMask=_PROC_DONE_SPELL_MAGIC_NEG, ProcChance=100,
    notes='S1a A2: rank 2. DUMMY proc carrier (amount = Proc Chance 6 live); spell_sha_ele_devastation casts the buff 202580 and sets its amount by rank. The stock melee-crit buffs 30165 / 29177 / 29178 are no longer triggered.',
)


elemental_devastation_29180 = _talent(
    29180, 'Elemental Devastation', 'Rank 3',
    [_dummy(9)], 1930,
    'Your non-periodic Fire, Frost and Nature spell critical strikes increase your Proc Chance by 10% for 10 sec.',
    AttributesEx3=0x4000000, ProcTypeMask=_PROC_DONE_SPELL_MAGIC_NEG, ProcChance=100,
    notes='S1a A2: see elemental_devastation_29179.',
)


healing_grace_29187 = spell(
    id=29187,
    name='Healing Grace',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=962,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the threat generated by your healing spells by $s1% and reduces the chance your helpful spells and damage over time effects will be dispelled by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EffectSpellClassMaskA_2': 524288, 'EffectSpellClassMaskA_3': 16, 'EffectSpellClassMaskB_1': 268438528, 'EffectSpellClassMaskB_2': 67636452, 'EffectSpellClassMaskB_3': 17, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


healing_grace_29189 = spell(
    id=29189,
    name='Healing Grace',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=962,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the threat generated by your healing spells by $s1% and reduces the chance your helpful spells and damage over time effects will be dispelled by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EffectSpellClassMaskA_2': 524288, 'EffectSpellClassMaskA_3': 16, 'EffectSpellClassMaskB_1': 268438528, 'EffectSpellClassMaskB_2': 67636452, 'EffectSpellClassMaskB_3': 17, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


healing_grace_29191 = spell(
    id=29191,
    name='Healing Grace',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=29, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=962,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the threat generated by your healing spells by $s1% and reduces the chance your helpful spells and damage over time effects will be dispelled by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EffectSpellClassMaskA_2': 524288, 'EffectSpellClassMaskA_3': 16, 'EffectSpellClassMaskB_1': 268438528, 'EffectSpellClassMaskB_2': 67636452, 'EffectSpellClassMaskB_3': 17, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_windfury_totem_29192 = spell(
    id=29192,
    name='Improved Windfury Totem',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=3),
    ],
    spell_icon_id=1397,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the melee haste granted by your Windfury totem by $s1%.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 2097152, 'EffectSpellClassMaskB_2': 4, 'EffectSpellClassMaskC_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_windfury_totem_29193 = spell(
    id=29193,
    name='Improved Windfury Totem',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=3),
    ],
    spell_icon_id=1397,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the melee haste granted by your Windfury totem by $s1%.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 2097152, 'EffectSpellClassMaskB_2': 4, 'EffectSpellClassMaskC_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


healing_way_29202 = spell(
    id=29202,
    name='Healing Way',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=1929,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by your Healing Wave spell by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


healing_way_29205 = spell(
    id=29205,
    name='Healing Way',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=1929,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by your Healing Wave spell by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


healing_way_29206 = spell(
    id=29206,
    name='Healing Way',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=1929,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by your Healing Wave spell by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


elemental_devastation_30160 = _talent(
    30160, 'Elemental Devastation', 'Rank 1',
    [_dummy(2)], 1930,
    'Your non-periodic Fire, Frost and Nature spell critical strikes increase your Proc Chance by 3% for 10 sec.',
    AttributesEx3=0x4000000, ProcTypeMask=_PROC_DONE_SPELL_MAGIC_NEG, ProcChance=100,
    notes='S1a A2: see elemental_devastation_29179 (rank 1, Proc Chance 3 live).',
)


unrelenting_storm_30664 = _talent(
    30664, 'Unrelenting Storm', 'Rank 1',
    [_dummy(0)], 2010,
    _desc('Casting Lightning Bolt, Lava Burst or Elemental Blast increases your spell and melee haste by 0.5% for 8 sec, stacking up to 3 times.',
          'At 3 stacks, your next Chain Lightning consumes them to deal 15% more damage and causes its primary target to take 10% more spell damage from you for 12 sec. Does not stack with other similar effects.'),
    notes='S1a A2: marker only. The stock Lightning Shield mana clause is gone; the stacks, the haste (0.5 / 1 / 1.5 per stack) and the capstone are spell_sha_ele_spell_hooks + the buff rows.',
)


unrelenting_storm_30665 = _talent(
    30665, 'Unrelenting Storm', 'Rank 2',
    [_dummy(0)], 2010,
    _desc('Casting Lightning Bolt, Lava Burst or Elemental Blast increases your spell and melee haste by 1% for 8 sec, stacking up to 3 times.',
          'At 3 stacks, your next Chain Lightning consumes them to deal 15% more damage and causes its primary target to take 10% more spell damage from you for 12 sec. Does not stack with other similar effects.'),
    notes='S1a A2: see unrelenting_storm_30664.',
)


unrelenting_storm_30666 = _talent(
    30666, 'Unrelenting Storm', 'Rank 3',
    [_dummy(0)], 2010,
    _desc('Casting Lightning Bolt, Lava Burst or Elemental Blast increases your spell and melee haste by 1.5% for 8 sec, stacking up to 3 times.',
          'At 3 stacks, your next Chain Lightning consumes them to deal 15% more damage and causes its primary target to take 10% more spell damage from you for 12 sec. Does not stack with other similar effects.',
          last=True),
    notes='S1a A2: see unrelenting_storm_30664.',
)


elemental_precision_30672 = _talent(
    30672, 'Elemental Precision', 'Rank 1',
    [_aura(AuraType.MOD_SPELL_CRIT_CHANCE, 0)], 2017,
    _desc('Increases your spell critical strike chance by 1%.',
          'Your non-periodic spell critical strikes have a 10% chance to reset the cooldown of your Elemental Blast and make your next Elemental Blast within 20 sec a guaranteed critical strike.'),
    notes='S1a A2: spell crit +1% (aura 57); the stock hit and threat clauses are gone.',
)


elemental_precision_30673 = _talent(
    30673, 'Elemental Precision', 'Rank 2',
    [_aura(AuraType.MOD_SPELL_CRIT_CHANCE, 1)], 2017,
    _desc('Increases your spell critical strike chance by 2%.',
          'Your non-periodic spell critical strikes have a 10% chance to reset the cooldown of your Elemental Blast and make your next Elemental Blast within 20 sec a guaranteed critical strike.'),
    notes='S1a A2: see elemental_precision_30672.',
)


elemental_precision_30674 = _talent(
    30674, 'Elemental Precision', 'Rank 3',
    [_aura(AuraType.MOD_SPELL_CRIT_CHANCE, 2), _dummy(0)], 2017,
    _desc('Increases your spell critical strike chance by 3%.',
          'Your non-periodic spell critical strikes have a 10% chance to reset the cooldown of your Elemental Blast and make your next Elemental Blast within 20 sec a guaranteed critical strike.',
          last=True),
    ProcTypeMask=_PROC_DONE_SPELL_MAGIC_NEG, ProcChance=100,
    notes='S1a A2: rank 3 capstone; eff2 DUMMY is the proc carrier for spell_sha_ele_precision_capstone (spell_proc 30674, 100%: the script rolls 10% x Proc Chance once per cast).',
)


lightning_overload_30675 = _talent(
    30675, 'Lightning Overload', 'Rank 1',
    [_dummy(5)], 2018,
    _desc('Gives your Lightning Bolt and Chain Lightning a 6% chance to cast a second, similar spell on the same target at no additional cost that deals half damage and no threat. This chance is tripled for critical strikes.',
          'While your Fire Elemental is active, your Lava Burst can also trigger Lightning Overload.'),
    ProcTypeMask=_PROC_DONE_SPELL_MAGIC_NEG, ProcChance=100,
    notes='S1a A2: DUMMY proc carrier (amount = the rank chance, 6 live). spell_proc -30675 now procs at 100% (the scripted roll is the only one) on Lightning Bolt, Chain Lightning and Lava Burst; spell_sha_ele_lightning_overload.',
)


lightning_overload_30678 = _talent(
    30678, 'Lightning Overload', 'Rank 2',
    [_dummy(12)], 2018,
    _desc('Gives your Lightning Bolt and Chain Lightning a 13% chance to cast a second, similar spell on the same target at no additional cost that deals half damage and no threat. This chance is tripled for critical strikes.',
          'While your Fire Elemental is active, your Lava Burst can also trigger Lightning Overload.'),
    ProcTypeMask=_PROC_DONE_SPELL_MAGIC_NEG, ProcChance=100,
    notes='S1a A2: see lightning_overload_30675.',
)


lightning_overload_30679 = _talent(
    30679, 'Lightning Overload', 'Rank 3',
    [_dummy(19)], 2018,
    _desc('Gives your Lightning Bolt and Chain Lightning a 20% chance to cast a second, similar spell on the same target at no additional cost that deals half damage and no threat. This chance is tripled for critical strikes.',
          'While your Fire Elemental is active, your Lava Burst can also trigger Lightning Overload.',
          last=True),
    ProcTypeMask=_PROC_DONE_SPELL_MAGIC_NEG, ProcChance=100,
    notes='S1a A2: see lightning_overload_30675.',
)


mental_quickness_30812 = spell(
    id=30812,
    name='Mental Quickness',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=237, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=238, misc_value=127),
    ],
    spell_icon_id=2022,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your instant cast Shaman spells by $s1% and increases your spell power by an amount equal to $s2% of your attack power.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_2': 1, 'EffectSpellClassMaskA_1': 3092780056, 'EffectSpellClassMaskA_2': 68728, 'EffectSpellClassMaskA_3': 28, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


mental_quickness_30813 = spell(
    id=30813,
    name='Mental Quickness',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=237, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=238, misc_value=127),
    ],
    spell_icon_id=2022,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your instant cast Shaman spells by $s1% and increases your spell power by an amount equal to $s2% of your attack power.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_2': 1, 'EffectSpellClassMaskA_1': 3092780056, 'EffectSpellClassMaskA_2': 68728, 'EffectSpellClassMaskA_3': 28, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


mental_quickness_30814 = spell(
    id=30814,
    name='Mental Quickness',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=237, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=238, misc_value=127),
    ],
    spell_icon_id=2022,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your instant cast Shaman spells by $s1% and increases your spell power by an amount equal to $s2% of your attack power.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_2': 1, 'EffectSpellClassMaskA_1': 3092780056, 'EffectSpellClassMaskA_2': 68728, 'EffectSpellClassMaskA_3': 28, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


focused_mind_30864 = spell(
    id=30864,
    name='Focused Mind',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=234, misc_value=26),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=234, misc_value=9),
    ],
    spell_icon_id=2014,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the duration of any Silence or Interrupt effects used against the Shaman by $s1%. This effect does not stack with other similar effects.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


focused_mind_30865 = spell(
    id=30865,
    name='Focused Mind',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=234, misc_value=26),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=234, misc_value=9),
    ],
    spell_icon_id=2014,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the duration of any Silence or Interrupt effects used against the Shaman by $s1%. This effect does not stack with other similar effects.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


focused_mind_30866 = spell(
    id=30866,
    name='Focused Mind',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=234, misc_value=26),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=234, misc_value=9),
    ],
    spell_icon_id=2014,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the duration of any Silence or Interrupt effects used against the Shaman by $s1%. This effect does not stack with other similar effects.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


nature_s_blessing_30867 = spell(
    id=30867,
    name="Nature's Blessing",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=175, misc_value=3),
    ],
    spell_icon_id=2012,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your healing by an amount equal to $s1% of your Intellect.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


nature_s_blessing_30868 = spell(
    id=30868,
    name="Nature's Blessing",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=175, misc_value=3),
    ],
    spell_icon_id=2012,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your healing by an amount equal to $s1% of your Intellect.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


nature_s_blessing_30869 = spell(
    id=30869,
    name="Nature's Blessing",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=175, misc_value=3),
    ],
    spell_icon_id=2012,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your healing by an amount equal to $s1% of your Intellect.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_chain_heal_30872 = spell(
    id=30872,
    name='Improved Chain Heal',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=963,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by your Chain Heal spell by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_chain_heal_30873 = spell(
    id=30873,
    name='Improved Chain Heal',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=963,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by your Chain Heal spell by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


nature_s_guardian_30881 = spell(
    id=30881,
    name="Nature's Guardian",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18350),
    ],
    spell_icon_id=2013,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever a damaging attack brings you below $s2% health, your maximum health is increased by $s1% for $31616d and your threat level towards the attacker is reduced.  30 second cooldown.', 'EffectBasePoints_2': 29, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'SpellClassSet': 11},
)


nature_s_guardian_30883 = spell(
    id=30883,
    name="Nature's Guardian",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18350),
    ],
    spell_icon_id=2013,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever a damaging attack brings you below $s2% health, your maximum health is increased by $s1% for $31616d and your threat level towards the attacker is reduced.  30 second cooldown.', 'EffectBasePoints_2': 29, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'SpellClassSet': 11},
)


nature_s_guardian_30884 = spell(
    id=30884,
    name="Nature's Guardian",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18350),
    ],
    spell_icon_id=2013,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever a damaging attack brings you below $s2% health, your maximum health is increased by $s1% for $31616d and your threat level towards the attacker is reduced.  30 second cooldown.', 'EffectBasePoints_2': 29, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'SpellClassSet': 11},
)


nature_s_guardian_30885 = spell(
    id=30885,
    name="Nature's Guardian",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18350),
    ],
    spell_icon_id=2013,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever a damaging attack brings you below $s2% health, your maximum health is increased by $s1% for $31616d and your threat level towards the attacker is reduced.  30 second cooldown.', 'EffectBasePoints_2': 29, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'SpellClassSet': 11},
)


nature_s_guardian_30886 = spell(
    id=30886,
    name="Nature's Guardian",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18350),
    ],
    spell_icon_id=2013,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever a damaging attack brings you below $s2% health, your maximum health is increased by $s1% for $31616d and your threat level towards the attacker is reduced.  30 second cooldown.', 'EffectBasePoints_2': 29, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'SpellClassSet': 11},
)


shamanistic_focus_43338 = spell(
    id=43338,
    name='Shamanistic Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-46, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=2016,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Shock spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2416967680, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50},
)


elemental_oath_51466 = _talent(
    51466, 'Elemental Oath', 'Rank 1',
    [Effect(type=65, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE, radius_yards=100.0),
     _aura(AuraType.ADD_FLAT_MODIFIER, 0, int(SpellModOp.EFFECT2), die_sides=0)], 3053,
    'Increases your spell critical strike chance by 1%. Increases the spell critical strike chance of all party and raid members by 1%. Does not stack with other similar effects.',
    masks={2: (0, 0x4000, 0)}, level=1, attributes=80, SpellPriority=50, AttributesEx6=1073741824,
    AuraDescription_Lang_Mask=16712190, AuraDescription_Lang_enUS='Spell critical strike chance increased.',
    ProcChance=0,
    notes='S1a A2 (brief Decision 1): party / raid spell crit +1% (self included). The stock Clearcasting damage clause is NOT in the doc: eff2 is the slot SpellInfoCorrections.cpp:333 forces to a flat SPELLMOD_EFFECT2 mask d1 0x4000, so it is declared with the same shape at value 0 (base_points 0, die_sides 0 -> 0): inert. The raw eff2 twins, the stock ProcTypeMask and the consolidated-buff flag are gone.',
)


elemental_oath_51470 = _talent(
    51470, 'Elemental Oath', 'Rank 2',
    [Effect(type=65, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE, radius_yards=100.0),
     _aura(AuraType.ADD_FLAT_MODIFIER, 0, int(SpellModOp.EFFECT2), die_sides=0)], 3053,
    'Increases your spell critical strike chance by 2%. Increases the spell critical strike chance of all party and raid members by 2%. Does not stack with other similar effects.',
    masks={2: (0, 0x4000, 0)}, level=1, attributes=80, SpellPriority=50, AttributesEx6=1073741824,
    AuraDescription_Lang_Mask=16712190, AuraDescription_Lang_enUS='Spell critical strike chance increased.',
    ProcChance=0,
    notes='S1a A2: see elemental_oath_51466.',
)


astral_shift_51474 = _talent(
    51474, 'Astral Shift', 'Rank 1',
    [_aura(AuraType.MOD_SPELL_CRIT_CHANCE, 0)], 3066,
    _desc('Increases your spell critical strike chance by 1%. When you are stunned, feared or silenced, you shift into the Astral Plane, reducing all damage taken by 10% for the duration.',
          'Being stunned, feared or silenced while casting an offensive Nature spell grants an empowered Astral Shift, reducing all damage taken by 25% for 6 sec.'),
    level=1, attributes=262352, AttributesEx3=67108864, AttributesEx4=524288, ProcTypeMask=0, ProcChance=0,
    SpellPriority=50,
    notes='S1a A2: eff1 spell crit +1%. The damage-taken buff 202590 is cast by ShamanAstralShiftUnitScript (UnitScript OnAuraApply, spell_shaman_elemental.cpp), so the talent carries no proc and no effect 2 (S1a review M1: a proc never fires for triggered or script-added controls). The stock SCHOOL_ABSORB percent and the 52179 visual trigger are gone.',
)


astral_shift_51478 = _talent(
    51478, 'Astral Shift', 'Rank 2',
    [_aura(AuraType.MOD_SPELL_CRIT_CHANCE, 1)], 3066,
    _desc('Increases your spell critical strike chance by 2%. When you are stunned, feared or silenced, you shift into the Astral Plane, reducing all damage taken by 10% for the duration.',
          'Being stunned, feared or silenced while casting an offensive Nature spell grants an empowered Astral Shift, reducing all damage taken by 25% for 6 sec.'),
    level=1, attributes=262352, AttributesEx3=67108864, AttributesEx4=524288, ProcTypeMask=0, ProcChance=0,
    SpellPriority=50,
    notes='S1a A2: see astral_shift_51474.',
)


lava_flows_51480 = _talent(
    51480, 'Lava Flows', 'Rank 1',
    [_mod(SpellModOp.CRIT_DAMAGE_BONUS, 7)], 3087,
    _desc('Increases the critical strike damage bonus of your Lava Burst, Flame Shock and Lava Lash by 8%. Casting Flame Shock or Lava Burst increases your spell and melee haste by 2% for 12 sec.',
          "Lava Surge. Your Flame Shock's periodic damage has a 15% chance to reset the cooldown of your Lava Burst and make your next Lava Burst within 15 sec instant. This effect can only occur once every 6 sec."),
    masks={1: (_FLAME_SHOCK, _LAVA_BURST, _LAVA_LASH)},
    notes='S1a A2: crit damage bonus +8% on Flame Shock, Lava Burst and Lava Lash (the Lava Lash clause is kept for the classless realm, d2 b2 is a target here, not an identity). The Sundering / dispel clause and the latent EffectBasePoints_3 twin are gone; the haste is Shaman::LavaFlowsHasteSpell.',
)


lava_flows_51481 = _talent(
    51481, 'Lava Flows', 'Rank 2',
    [_mod(SpellModOp.CRIT_DAMAGE_BONUS, 15)], 3087,
    _desc('Increases the critical strike damage bonus of your Lava Burst, Flame Shock and Lava Lash by 16%. Casting Flame Shock or Lava Burst increases your spell and melee haste by 4% for 12 sec.',
          "Lava Surge. Your Flame Shock's periodic damage has a 15% chance to reset the cooldown of your Lava Burst and make your next Lava Burst within 15 sec instant. This effect can only occur once every 6 sec."),
    masks={1: (_FLAME_SHOCK, _LAVA_BURST, _LAVA_LASH)},
    notes='S1a A2: see lava_flows_51480.',
)


lava_flows_51482 = _talent(
    51482, 'Lava Flows', 'Rank 3',
    [_mod(SpellModOp.CRIT_DAMAGE_BONUS, 24), _dummy(0)], 3087,
    _desc('Increases the critical strike damage bonus of your Lava Burst, Flame Shock and Lava Lash by 25%. Casting Flame Shock or Lava Burst increases your spell and melee haste by 6% for 12 sec.',
          "Lava Surge. Your Flame Shock's periodic damage has a 15% chance to reset the cooldown of your Lava Burst and make your next Lava Burst within 15 sec instant. This effect can only occur once every 6 sec.",
          last=True),
    masks={1: (_FLAME_SHOCK, _LAVA_BURST, _LAVA_LASH)}, ProcTypeMask=_PROC_DONE_PERIODIC, ProcChance=15,
    notes='S1a A2: rank 3 (Lava Surge). eff2 DUMMY is the proc carrier; spell_proc 51482 is DONE_PERIODIC on Flame Shock, 15% native (Proc Chance applies), ICD 6000; spell_sha_ele_lava_surge.',
)


storm_earth_and_fire_51483 = _talent(
    51483, 'Storm, Earth and Fire', 'Rank 1',
    [_mod(SpellModOp.COOLDOWN, -751, pct=False), _mod(SpellModOp.DOT, 9)], 3063,
    'Reduces the cooldown of your Chain Lightning by 0.75 sec. Increases the periodic damage of your Flame Shock by 10%.',
    masks={1: (_CL, 0, 0), 2: (_FLAME_SHOCK, 0, 0)}, level=1, SpellPriority=50,
    notes='S1a A2 (Q7): two clauses. The Earthbind root clause (stock eff2, d1 b27) is gone; the periodic effect moved from eff3 to eff2.',
)


storm_earth_and_fire_51485 = _talent(
    51485, 'Storm, Earth and Fire', 'Rank 2',
    [_mod(SpellModOp.COOLDOWN, -1501, pct=False), _mod(SpellModOp.DOT, 19)], 3063,
    'Reduces the cooldown of your Chain Lightning by 1.5 sec. Increases the periodic damage of your Flame Shock by 20%.',
    masks={1: (_CL, 0, 0), 2: (_FLAME_SHOCK, 0, 0)}, level=1, SpellPriority=50,
    notes='S1a A2: see storm_earth_and_fire_51483.',
)


storm_earth_and_fire_51486 = _talent(
    51486, 'Storm, Earth and Fire', 'Rank 3',
    [_mod(SpellModOp.COOLDOWN, -2501, pct=False), _mod(SpellModOp.DOT, 29)], 3063,
    'Reduces the cooldown of your Chain Lightning by 2.5 sec. Increases the periodic damage of your Flame Shock by 30%.',
    masks={1: (_CL, 0, 0), 2: (_FLAME_SHOCK, 0, 0)}, level=1, SpellPriority=50,
    notes='S1a A2: see storm_earth_and_fire_51483.',
)


improved_stormstrike_51521 = spell(
    id=51521,
    name='Improved Stormstrike',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=11, trigger_spell=63375),
    ],
    spell_icon_id=3159,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you Stormstrike, you have a $h% chance to immediately grant you $63375s1% of your base mana.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 16, 'EffectSpellClassMaskB_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_stormstrike_51522 = spell(
    id=51522,
    name='Improved Stormstrike',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=11, trigger_spell=63375),
    ],
    spell_icon_id=3159,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you Stormstrike, you have a $h% chance to immediately grant you $63375s1% of your base mana.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 16, 'EffectSpellClassMaskB_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50},
)


earthen_power_51523 = spell(
    id=51523,
    name='Earthen Power',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=3),
    ],
    spell_icon_id=2289,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Earthbind Totem's pulses have a $s1% chance to also remove all snare effects from you and nearby friendly targets, and your Earth Shock reduces enemy attack speed by an additional $/10;s2%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11, 'SpellLevel': 50, 'StartRecoveryCategory': 133},
)


earthen_power_51524 = spell(
    id=51524,
    name='Earthen Power',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=3),
    ],
    spell_icon_id=2289,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Earthbind Totem's pulses have a $s1% chance to also remove all snare effects from you and nearby friendly targets, and your Earth Shock reduces enemy attack speed by an additional $/10;s2%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11, 'SpellLevel': 1, 'StartRecoveryCategory': 133},
)


static_shock_51525 = spell(
    id=51525,
    name='Static Shock',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=4),
    ],
    spell_icon_id=3059,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a $s1% chance to hit your target with a Lightning Shield orb charge when you deal damage with melee attacks and abilities, and your Lightning Shield gains $s2 additional charges.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 2, 'ProcTypeMask': 12652564, 'RangeIndex': 1, 'SpellClassMask_3': 8192, 'SpellClassSet': 11},
)


static_shock_51526 = spell(
    id=51526,
    name='Static Shock',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=4),
    ],
    spell_icon_id=3059,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a $s1% chance to hit your target with a Lightning Shield orb charge when you deal damage with melee attacks and abilities, and your Lightning Shield gains $s2 additional charges.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 4, 'ProcTypeMask': 12652564, 'RangeIndex': 1, 'SpellClassMask_3': 8192, 'SpellClassSet': 11},
)


static_shock_51527 = spell(
    id=51527,
    name='Static Shock',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=4),
    ],
    spell_icon_id=3059,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a $s1% chance to hit your target with a Lightning Shield orb charge when you deal damage with melee attacks and abilities, and your Lightning Shield gains $s2 additional charges.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 6, 'ProcTypeMask': 12652884, 'RangeIndex': 1, 'SpellClassMask_3': 8192, 'SpellClassSet': 11},
)


maelstrom_weapon_51528 = spell(
    id=51528,
    name='Maelstrom Weapon',
    school=School.NORMAL,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=53817),
    ],
    spell_icon_id=3156,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you deal damage with a melee weapon, you have a chance to reduce the cast time of your next Lightning Bolt, Chain Lightning, Lesser Healing Wave, Healing Wave, Chain Heal, or Hex spell by $53817s1%. Stacks up to 5 times. Lasts $53817d.', 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 61243, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 12582932, 'RangeIndex': 1, 'SpellClassMask_2': 2, 'SpellClassMask_3': 512, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50},
)


maelstrom_weapon_51529 = spell(
    id=51529,
    name='Maelstrom Weapon',
    school=School.NORMAL,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=53817),
    ],
    spell_icon_id=3156,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you deal damage with a melee weapon, you have a chance (higher than rank 1) to reduce the cast time of your next Lightning Bolt, Chain Lightning, Lesser Healing Wave, Healing Wave, Chain Heal, or Hex spell by $53817s1%. Stacks up to 5 times. Lasts $53817d.', 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 64563, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 12582932, 'RangeIndex': 1, 'SpellClassMask_3': 512, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50},
)


maelstrom_weapon_51530 = spell(
    id=51530,
    name='Maelstrom Weapon',
    school=School.NORMAL,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=53817),
    ],
    spell_icon_id=3156,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you deal damage with a melee weapon, you have a chance (higher than rank 2) to reduce the cast time of your next Lightning Bolt, Chain Lightning, Lesser Healing Wave, Healing Wave, Chain Heal, or Hex spell by $53817s1%. Stacks up to 5 times. Lasts $53817d.', 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 59187, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 12582932, 'RangeIndex': 1, 'SpellClassMask_3': 512, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50},
)


maelstrom_weapon_51531 = spell(
    id=51531,
    name='Maelstrom Weapon',
    school=School.NORMAL,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=53817),
    ],
    spell_icon_id=3156,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you deal damage with a melee weapon, you have a chance (higher than rank 3) to reduce the cast time of your next Lightning Bolt, Chain Lightning, Lesser Healing Wave, Healing Wave, Chain Heal, or Hex spell by $53817s1%. Stacks up to 5 times. Lasts $53817d.', 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 64563, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 12582932, 'RangeIndex': 1, 'SpellClassMask_3': 512, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50},
)


maelstrom_weapon_51532 = spell(
    id=51532,
    name='Maelstrom Weapon',
    school=School.NORMAL,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=53817),
    ],
    spell_icon_id=3156,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you deal damage with a melee weapon, you have a chance (higher than rank 4) to reduce the cast time of your next Lightning Bolt, Chain Lightning, Lesser Healing Wave, Healing Wave, Chain Heal, or Hex spell by $53817s1%. Stacks up to 5 times. Lasts $53817d.', 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 64563, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 12582932, 'RangeIndex': 1, 'SpellClassMask_3': 512, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50},
)


blessing_of_the_eternals_51554 = spell(
    id=51554,
    name='Blessing of the Eternals',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=57, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
    ],
    spell_icon_id=3157,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your spells by $s1%, and increases the chance to apply the Earthliving heal over time effect on the target by $s2% when they are at or under 35% total health.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 32, 'EffectSpellClassMaskB_2': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


blessing_of_the_eternals_51555 = spell(
    id=51555,
    name='Blessing of the Eternals',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=57, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=79, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
    ],
    spell_icon_id=3157,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your spells by $s1%, and increases the chance to apply the Earthliving heal over time effect on the target by $s2% when they are at or under 35% total health.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 32, 'EffectSpellClassMaskB_2': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


ancestral_awakening_51556 = spell(
    id=51556,
    name='Ancestral Awakening',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3065,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you critically heal with your Healing Wave, Lesser Healing Wave or Riptide you summon an Ancestral spirit to aid you, instantly healing the lowest percentage health friendly party or raid target within 40 yards for $s1% of the amount healed.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 11},
)


ancestral_awakening_51557 = spell(
    id=51557,
    name='Ancestral Awakening',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3065,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you critically heal with your Healing Wave, Lesser Healing Wave or Riptide you summon an Ancestral spirit to aid you, instantly healing the lowest percentage health friendly party or raid target within 40 yards for $s1% of the amount healed.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 11},
)


ancestral_awakening_51558 = spell(
    id=51558,
    name='Ancestral Awakening',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3065,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you critically heal with your Healing Wave, Lesser Healing Wave or Riptide you summon an Ancestral spirit to aid you, instantly healing the lowest percentage health friendly party or raid target within 40 yards for $s1% of the amount healed.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_earth_shield_51560 = spell(
    id=51560,
    name='Improved Earth Shield',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=107, misc_value=4),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=3),
    ],
    spell_icon_id=2015,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount of charges for your Earth Shield by $s1, and increases the healing done by your Earth Shield by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_2': 1024, 'EffectSpellClassMaskB_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


improved_earth_shield_51561 = spell(
    id=51561,
    name='Improved Earth Shield',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=4),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=3),
    ],
    spell_icon_id=2015,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount of charges for your Earth Shield by $s1, and increases the healing done by your Earth Shield by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_2': 1024, 'EffectSpellClassMaskB_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


tidal_waves_51562 = spell(
    id=51562,
    name='Tidal Waves',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=7, trigger_spell=53390),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=3057,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you cast Chain Heal or Riptide, you have a $s1% chance to lower the cast time of your Healing Wave spell by $53390s1% and increase the critical effect chance of your Lesser Healing Wave spell by $53390s2%, until two such spells have been cast. In addition, your Healing Wave gains an additional $s2% of your bonus healing effects and your Lesser Healing Wave gains an additional $s3% of your bonus healing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 192, 'EffectSpellClassMaskA_2': 8192, 'EffectSpellClassMaskB_1': 64, 'EffectSpellClassMaskC_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 17408, 'RangeIndex': 1, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50},
)


tidal_waves_51563 = spell(
    id=51563,
    name='Tidal Waves',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=7, trigger_spell=53390),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=107, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=3057,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you cast Chain Heal or Riptide, you have a $s1% chance to lower the cast time of your Healing Wave spell by $53390s1% and increase the critical effect chance of your Lesser Healing Wave spell by $53390s2%, until two such spells have been cast. In addition, your Healing Wave gains an additional $s2% of your bonus healing effects and your Lesser Healing Wave gains an additional $s3% of your bonus healing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 192, 'EffectSpellClassMaskA_2': 8192, 'EffectSpellClassMaskB_1': 64, 'EffectSpellClassMaskC_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 40, 'ProcTypeMask': 17408, 'RangeIndex': 1, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50},
)


tidal_waves_51564 = spell(
    id=51564,
    name='Tidal Waves',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=7, trigger_spell=53390),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=107, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=3057,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you cast Chain Heal or Riptide, you have a $s1% chance to lower the cast time of your Healing Wave spell by $53390s1% and increase the critical effect chance of your Lesser Healing Wave spell by $53390s2%, until two such spells have been cast. In addition, your Healing Wave gains an additional $s2% of your bonus healing effects and your Lesser Healing Wave gains an additional $s3% of your bonus healing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 192, 'EffectSpellClassMaskA_2': 8192, 'EffectSpellClassMaskB_1': 64, 'EffectSpellClassMaskC_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 60, 'ProcTypeMask': 17408, 'RangeIndex': 1, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50},
)


tidal_waves_51565 = spell(
    id=51565,
    name='Tidal Waves',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=79, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=7, trigger_spell=53390),
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=107, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=3057,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you cast Chain Heal or Riptide, you have a $s1% chance to lower the cast time of your Healing Wave spell by $53390s1% and increase the critical effect chance of your Lesser Healing Wave spell by $53390s2%, until two such spells have been cast. In addition, your Healing Wave gains an additional $s2% of your bonus healing effects and your Lesser Healing Wave gains an additional $s3% of your bonus healing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 192, 'EffectSpellClassMaskA_2': 8192, 'EffectSpellClassMaskB_1': 64, 'EffectSpellClassMaskC_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 80, 'ProcTypeMask': 17408, 'RangeIndex': 1, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50},
)


tidal_waves_51566 = spell(
    id=51566,
    name='Tidal Waves',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=7, trigger_spell=53390),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=3057,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you cast Chain Heal or Riptide, you have a $s1% chance to lower the cast time of your Healing Wave spell by $53390s1% and increase the critical effect chance of your Lesser Healing Wave spell by $53390s2%, until two such spells have been cast. In addition, your Healing Wave gains an additional $s2% of your bonus healing effects and your Lesser Healing Wave gains an additional $s3% of your bonus healing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 192, 'EffectSpellClassMaskA_2': 8192, 'EffectSpellClassMaskB_1': 64, 'EffectSpellClassMaskC_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 17408, 'RangeIndex': 1, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_shields_51881 = spell(
    id=51881,
    name='Improved Shields',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=3),
    ],
    spell_icon_id=19,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Lightning Shield orbs by $s1%, increases the amount of mana gained from your Water Shield orbs by $s2% and increases the amount of healing done by your Earth Shield orbs by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EffectSpellClassMaskB_2': 1056, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


mental_dexterity_51883 = spell(
    id=51883,
    name='Mental Dexterity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=268, misc_value=3),
    ],
    spell_icon_id=38,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Attack Power by $s1% of your Intellect.', 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_1': 3093042200, 'EffectSpellClassMaskA_2': 3192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


mental_dexterity_51884 = spell(
    id=51884,
    name='Mental Dexterity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=268, misc_value=3),
    ],
    spell_icon_id=38,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Attack Power by $s1% of your Intellect.', 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_1': 3093042200, 'EffectSpellClassMaskA_2': 3192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


mental_dexterity_51885 = spell(
    id=51885,
    name='Mental Dexterity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=268, misc_value=3),
    ],
    spell_icon_id=38,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Attack Power by $s1% of your Intellect.', 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_1': 3093042200, 'EffectSpellClassMaskA_2': 3192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


enhancing_totems_52456 = spell(
    id=52456,
    name='Enhancing Totems',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=691,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Strength of Earth and Flametongue Totems by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33619968, 'EffectSpellClassMaskB_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


elemental_fury_60184 = _talent(
    60184, 'Elemental Fury', '',
    [_mod(SpellModOp.CRIT_DAMAGE_BONUS, 59)], 1137,
    _desc('Your spell critical strikes deal 180% damage. Does not stack with other similar effects.',
          'While Clearcasting from Elemental Focus is active, your Nature damage is increased by 8% and your other magic damage by 5%.'),
    masks={1: (0xD1300003, 0x43000, m.EARTHQUAKE | m.ELEMENTAL_BLAST)},
    notes='S1a A2: see elemental_fury_16089 (+60% of the base bonus).',
)


elemental_fury_60185 = _talent(
    60185, 'Elemental Fury', '',
    [_mod(SpellModOp.CRIT_DAMAGE_BONUS, 99)], 1137,
    _desc('Your spell critical strikes deal 200% damage. Does not stack with other similar effects.',
          'While Clearcasting from Elemental Focus is active, your Nature damage is increased by 8% and your other magic damage by 5%.',
          last=True),
    masks={1: (0xD1300003, 0x43000, m.EARTHQUAKE | m.ELEMENTAL_BLAST)},
    notes='S1a A2: see elemental_fury_16089 (+100% of the base bonus). Rank 3 is the capstone rank the Clearcasting script reads.',
)


elemental_fury_60187 = spell(
    id=60187,
    name='Elemental Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=79, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=1137,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Searing and Magma Totems and your Fire, Frost, and Nature spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3509583875, 'EffectSpellClassMaskA_2': 274432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


elemental_fury_60188 = spell(
    id=60188,
    name='Elemental Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=1137,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Searing and Magma Totems and your Fire, Frost, and Nature spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3509583875, 'EffectSpellClassMaskA_2': 274432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


cobra_reflexes_61683 = spell(
    id=61683,
    name='Cobra Reflexes',
    school=School.NATURE,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=9),
    ],
    spell_icon_id=72,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's attack speed by $61683s1%.  Your pet will hit faster but each hit will do less damage.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcCharges': 1, 'RangeIndex': 1, 'SpellClassSet': 11, 'SpellVisualID_1': 11387},
)


shamanism_62097 = _talent(
    62097, 'Shamanism', 'Rank 1',
    [_mod(SpellModOp.DAMAGE, 4)], 2427,
    _desc('Increases the damage of your Lightning Bolt and Chain Lightning by 5%. Each time your Lightning Bolt or Chain Lightning deals damage, including Lightning Overloads, you have a 33% chance to reduce the remaining cooldown of Elemental Mastery and Thunderstorm by 1 sec.',
          'Increases the haste granted by Elemental Mastery by an additional 5%.'),
    masks={1: (_LB | _CL, 0, 0)}, level=1, SpellPriority=50,
    notes='S1a A2: Lightning Bolt / Chain Lightning +5% damage (the stock bonus-multiplier clauses are gone). The cooldown roll is spell_sha_ele_spell_hooks / the overload copy script.',
)


shamanism_62098 = _talent(
    62098, 'Shamanism', 'Rank 2',
    [_mod(SpellModOp.DAMAGE, 9)], 2427,
    _desc('Increases the damage of your Lightning Bolt and Chain Lightning by 10%. Each time your Lightning Bolt or Chain Lightning deals damage, including Lightning Overloads, you have a 33% chance to reduce the remaining cooldown of Elemental Mastery and Thunderstorm by 1 sec.',
          'Increases the haste granted by Elemental Mastery by an additional 5%.'),
    masks={1: (_LB | _CL, 0, 0)}, level=1, SpellPriority=50,
    notes='S1a A2: see shamanism_62097.',
)


shamanism_62099 = _talent(
    62099, 'Shamanism', 'Rank 3',
    [_mod(SpellModOp.DAMAGE, 14), _mod(SpellModOp.EFFECT1, 4, pct=False)], 2427,
    _desc('Increases the damage of your Lightning Bolt and Chain Lightning by 15%. Each time your Lightning Bolt or Chain Lightning deals damage, including Lightning Overloads, you have a 33% chance to reduce the remaining cooldown of Elemental Mastery and Thunderstorm by 1 sec.',
          'Increases the haste granted by Elemental Mastery by an additional 5%.',
          last=True),
    masks={1: (_LB | _CL, 0, 0), 2: (0, 0, m.EM_HASTE)}, level=1, SpellPriority=50,
    notes='S1a A2 (brief Decision 11): rank 3 capstone, eff2 flat SPELLMOD_EFFECT1 +5 on d2 b26 (Elemental Mastery haste 64701, effect 1 = the 10% haste -> 15%).',
)


shamanism_62100 = spell(
    id=62100,
    name='Shamanism',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=107, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=2427,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Lightning Bolt and Chain Lightning spells gain an additional $s1% and your Lava Burst gains an additional $s2% of your bonus damage effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_2': 4096, 'EffectSpellClassMaskC_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50},
)


shamanism_62101 = spell(
    id=62101,
    name='Shamanism',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=107, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=2427,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Lightning Bolt and Chain Lightning spells gain an additional $s1% and your Lava Burst gains an additional $s2% of your bonus damage effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_2': 4096, 'EffectSpellClassMaskC_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50},
)


booming_echoes_63370 = _talent(
    63370, 'Booming Echoes', 'Rank 1',
    [_mod(SpellModOp.DAMAGE, 4), _mod(SpellModOp.DOT, 4)], 2460,
    _desc('Increases the damage of your Shock spells and Elemental Blast by 5%.',
          'Each of your Lightning Overloads grants 1 Echo, stacking up to 10 times. Lasts 30 sec. Each Echo increases the damage of your next Earth Shock by 30% and its critical strike damage bonus by 10%. Summoning your Earth Elemental grants 5 Echoes. Earth Shock consumes all Echoes, or half of them while your Earth Elemental is active.'),
    masks={1: (_SHOCKS, 0, m.ELEMENTAL_BLAST), 2: (_FLAME_SHOCK, 0, 0)},
    notes='S1a A2: shocks + Elemental Blast +5% (talent_mult effect 1), eff2 the Flame Shock tick. The stock shock cooldown clause is gone.',
)


booming_echoes_63372 = _talent(
    63372, 'Booming Echoes', 'Rank 2',
    [_mod(SpellModOp.DAMAGE, 9), _mod(SpellModOp.DOT, 9)], 2460,
    _desc('Increases the damage of your Shock spells and Elemental Blast by 10%.',
          'Each of your Lightning Overloads grants 1 Echo, stacking up to 10 times. Lasts 30 sec. Each Echo increases the damage of your next Earth Shock by 30% and its critical strike damage bonus by 10%. Summoning your Earth Elemental grants 5 Echoes. Earth Shock consumes all Echoes, or half of them while your Earth Elemental is active.'),
    masks={1: (_SHOCKS, 0, m.ELEMENTAL_BLAST), 2: (_FLAME_SHOCK, 0, 0)},
    notes='S1a A2: see booming_echoes_63370.',
)


frozen_power_63373 = spell(
    id=63373,
    name='Frozen Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3780,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Lightning Bolt, Chain Lightning, Lava Lash and Shock spells by $s1% on targets afflicted by your Frostbrand Attack effect, and your Frost Shock has a $s2% chance to root the target in ice for $63685d. when used on targets at or further than $63685s1 yards from you.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16777216, 'EffectSpellClassMaskB_2': 4, 'EffectSpellClassMaskC_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


frozen_power_63374 = spell(
    id=63374,
    name='Frozen Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3780,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Lightning Bolt, Chain Lightning, Lava Lash and Shock spells by $s1% on targets afflicted by your Frostbrand Attack effect, and your Frost Shock has a $s2% chance to root the target in ice for $63685d. when used on targets at or further than $63685s1 yards from you.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16777216, 'EffectSpellClassMaskB_2': 4, 'EffectSpellClassMaskC_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


# ---------------------------------------------------------------------------------------------
# Potency system P8 (2026-10-02) - pets, guardians, totems (never player-cast; see
# .agents/plans/potency-system/potency-system.PLAN.md's P8 section and
# potency-system.HANDOFF.md's "P8: pets, guardians, totems" extra).
# ---------------------------------------------------------------------------------------------

stoneclaw_totem_absorb_55328 = spell(
    id=55328,
    name='Stoneclaw Totem',
    school=School.NATURE,
    attributes=536871168,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.SCRIPT_EFFECT, base_potency=50.0, potency_kind='absorb', implicit_target_a=27),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=689,
    notes=(
        "pulled from existing data. Potency system P8 (2026-10-02): new declaration, D2 escape-hatch "
        "case - the player-castable Stoneclaw Totem (stoneclaw_totem_5730, shaman_spells.py) only "
        "SUMMON()s totem creature 3579; creature_template_spell(3579, slot 1) = 55328, so the TOTEM "
        "itself casts this id, once, at summon time (passive-type totem, Totem::InitSummon's "
        "`CastSpell(this, GetSpell(), true)` self-cast - confirmed by reading Totem.cpp, NOT the "
        "player, contra an earlier research pass's note; the totem's level always equals the owner's "
        "(Totem::InitStats), so the distinction doesn't change the derived potency). EFFECT_0 "
        "(SPELL_EFFECT_SCRIPT_EFFECT) is read by spell_sha_stoneclaw_totem::HandleScriptEffect "
        "(src/server/scripts/Spells/spell_shaman.cpp) via GetEffectValue() and re-applied as a custom "
        "bp on SPELL_SHAMAN_STONECLAW_TOTEM (55277, the real SCHOOL_ABSORB aura put on sibling totems), "
        "which always skips its OWN potency hook per D2. No separate SpellPotency::Apply() call is "
        "added, though: this spell's own cast of EFFECT_0 is a plain, non-customized cast (Totem::"
        "InitSummon's CastSpell has no CustomSpellValues), so SpellEffectInfo::CalcValue's "
        "`bp == BasePoints` check already holds and the potency hook fires normally - GetEffectValue() "
        "therefore already returns the corrected value before it's handed to 55277 (see the matching "
        "comment at the CastCustomSpell call site in spell_shaman.cpp, and spell_warrior.cpp's "
        "spell_warr_bloodthirst::HandleDamage for the same established principle on an already-"
        "converted spell: 'once it has a potency row, GetEffectValue() already IS the full ... "
        "derived total'). Adding a second Apply() call here would double the low-level correction and "
        "the +/-10% roll. potency_kind='absorb' (T=1.5s instant-shield convention, docs/potency-"
        "system.md 'Healing'). sp_potency=1.9 is base-implied from the current flat EffectBasePoints "
        "of 20 (no RealPointsPerLevel at all before this conversion): 20 / (3.96 x C(60)) = 1.888, "
        "rounded. 55277 itself is left undeclared/untouched (always script-bp-driven, no tooltip of "
        "its own worth migrating, and not named in the P8 task scope). "
        "Stoneclaw review 2026-10-03 (user): sp_potency=1.9 -> base_potency=50, no SP. 1.9 was "
        "base-implied from rank 1's flat 20 read as a level-60 value (3/20/29 at 8/60/80 vs stock "
        "ranks' 21/330/1085). No sp_potency: EFFECT_0 is a SCRIPT_EFFECT and SCHOOL_ABSORB gets no "
        "engine spell-power bonus, so a coefficient here would never apply (stock had none either). "
        "Stoneclaw Totem 5730's description shows this value through pot_text()."
    ),
    raw_overrides={'AttributesEx': 128, 'AttributesEx2': 335544324, 'CastingTimeIndex': 1, 'ProcChance': 101, 'EquippedItemClass': -1, 'SpellVisualID_1': 370, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Taunting creatures.', 'AuraDescription_Lang_Mask': 16712190, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'SpellLevel': 1},
)


angered_earth_36213 = spell(
    id=36213,
    name='Angered Earth',
    school=School.NORMAL,
    mechanic=16,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=114, implicit_target_a=22, implicit_target_b=15, radius_yards=15.0),
        Effect(type=63, base_points=1099, points_per_level=25.0, implicit_target_a=22, implicit_target_b=15, radius_yards=15.0),
    ],
    spell_icon_id=66,
    notes=(
        "pulled from existing data. Potency system P8 (2026-10-02): checked, NOT converted - Earth "
        "Elemental Totem's guardian ability (npc_pet_shaman_earth_elemental, src/server/scripts/Pet/"
        "pet_shaman.cpp, DoCastVictim(SPELL_SHAMAN_ANGEREDEARTH)). Both effects are pure threat: "
        "EFFECT_0 is type 114 (SPELL_EFFECT_ATTACK_ME, a taunt - no EffectType DSL name exists for it, "
        "src/server/shared/SharedDefines.h), EFFECT_1 is type 63 (SPELL_EFFECT_THREAT, 1099 + 25/level "
        "bonus threat only). Neither effect deals damage or healing - this is explicitly out of scope "
        "per docs/potency-system.md's 'Out of scope by design' list ('threat'). Declared plain, as "
        "pulled, with no sp_potency/ap_potency; this corrects the P8 task brief's premise that this "
        "ability has a damage/heal component worth converting."
    ),
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 67108864, 'AttributesEx4': 2048, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 34, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Taunts and causes additional high threat to all enemies within $a1 yards.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 5, 'DefenseType': 2, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'BaseLevel': 66, 'SpellLevel': 66},
)


fire_elemental_fire_nova_12470 = spell(
    id=12470,
    name='Fire Nova',
    school=School.FIRE,
    attributes=589824,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=30,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=19.2, implicit_target_a=22, implicit_target_b=15, radius_yards=10.0),
    ],
    spell_icon_id=33,
    notes=(
        "pulled from existing data. Potency system P8 (2026-10-02): new declaration - Fire Elemental "
        "Totem's guardian ability (npc_pet_shaman_fire_elemental, src/server/scripts/Pet/pet_shaman.cpp, "
        "me->CastSpell(me, SPELL_SHAMAN_FIRENOVA, false) on an 8-15s timer), plain cast, no custom bp. "
        "Fire/Earth elemental guardians spawn at exactly the owner's level (Spell::SummonGuardian, "
        "SpellEffects.cpp, SetLevel(caster->GetLevel()) - confirmed no special case for this summon id). "
        "sp_potency=44.6 is base-implied from the current live fields (base_points=147, die_sides=23 - "
        "averaged (1+23)/2=12 per docs/bugs-and-fixes.md's own DieSides-averaging convention - "
        "V60=159, T=2.0s cast time: 159 / (C(60) x (2.0/1.5)) = 44.58, rounded). The live "
        "EffectBonusMultiplier_1 of 1.0 is a large mismatch against this base-implied value (would "
        "imply potency ~175) but is irrelevant in practice (an NPC guardian has ~0 spell power); base-"
        "implied wins by default per docs/potency-system.md, flagged for review."
    ),
    raw_overrides={'AttributesEx': 136, 'CastingTimeIndex': 5, 'InterruptFlags': 9, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 963, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Inflicts {pot1} Fire damage to nearby enemies.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'BaseLevel': 20, 'SpellLevel': 20},
)
unbind_bonus_coefficients(fire_elemental_fire_nova_12470)  # stale spell_bonus_data row overrode the potency coefficient (D1)


fire_elemental_fire_blast_57984 = spell(
    id=57984,
    name='Fire Blast',
    school=School.FIRE,
    attributes=589824,
    category=19,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=40,
    mana_cost_pct=0,
    range_yards=20.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=19.3, implicit_target_a=6),
    ],
    spell_icon_id=12,
    notes=(
        "pulled from existing data. Potency system P8 (2026-10-02): new declaration - Fire Elemental "
        "Totem's guardian ability (npc_pet_shaman_fire_elemental, src/server/scripts/Pet/pet_shaman.cpp, "
        "me->CastSpell(me->GetVictim(), SPELL_SHAMAN_FIREBLAST, false) on a 4-8s timer), plain cast, no "
        "custom bp, same owner-level-at-summon guarantee as Fire Nova above. sp_potency=44.9 is base-"
        "implied (base_points=109, die_sides=21 averaged to 11, V60=120, T=1.5s since cast_time_ms=0: "
        "120 / C(60) = 44.86, rounded). The live EffectBonusMultiplier_1 of 0.429 implies ~100 potency "
        "by coefficient, a real mismatch (same NPC-spell-power caveat as Fire Nova); base-implied wins "
        "by default, flagged for review."
    ),
    raw_overrides={'FacingCasterFlags': 1, 'CastingTimeIndex': 1, 'InterruptFlags': 8, 'ProcChance': 101, 'EquippedItemClass': -1, 'SpellVisualID_1': 143, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Inflicts {pot1} Fire damage to an enemy.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 3, 'SpellClassMask_1': 131074, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'BaseLevel': 20, 'SpellLevel': 20},
)
unbind_bonus_coefficients(fire_elemental_fire_blast_57984)  # stale spell_bonus_data row overrode the potency coefficient (D1)


fire_elemental_fire_shield_13377 = spell(
    id=13377,
    name='Fire Shield',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=2512,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=3000, trigger_spell=13376),
    ],
    spell_icon_id=0,
    notes=(
        "pulled from existing data. Potency system P8 (2026-10-02): checked per the task brief - no "
        "damage/heal component of its own (base_points=-1 on an APPLY_AURA/PERIODIC_TRIGGER_SPELL aura "
        "is not a potency target; it's a plain trigger carrier). Cast once, self-targeted, by "
        "npc_pet_shaman_fire_elemental on JustEngagedWith (src/server/scripts/Pet/pet_shaman.cpp, "
        "me->CastSpell(me, SPELL_SHAMAN_FIRESHIELD, true)), never re-cast (EVENT_SHAMAN_FIRESHIELD is "
        "commented out in that file). The real, convertible damage is on its trigger_spell target, "
        "13376 (declared below) - same pattern as Healing Stream Totem's 5672->52041 split. Also shared "
        "with an unrelated NPC, boss_pyroguard_emberseer (EasternKingdoms/BlackrockMountain/"
        "BlackrockSpire) via the same two hard-coded ids; not declared/touched there, out of scope."
    ),
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EquippedItemSubclass': -1, 'EffectChainAmplitude_1': 1, 'EffectChainAmplitude_2': 1, 'EffectChainAmplitude_3': 1, 'BaseLevel': 40, 'SpellLevel': 40},
)


fire_elemental_fire_shield_pulse_13376 = spell(
    id=13376,
    name='Fire Shield',
    school=School.FIRE,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=5.6, potency_kind='periodic', time_basis_ms=3000, implicit_target_a=22, implicit_target_b=15, radius_yards=5.0),
    ],
    spell_icon_id=31,
    notes=(
        "pulled from existing data. Potency system P8 (2026-10-02): new declaration - the real damage "
        "component of Fire Elemental Totem's Fire Shield (13377's PERIODIC_TRIGGER_SPELL, every 3s, "
        "self-targeted; this effect's own implicit_target_a/b=22/15 then hits nearby enemies). Caster "
        "is always the Fire Elemental guardian (owner-level-at-summon guarantee, see Fire Nova above). "
        "potency_kind='periodic' (not heal-like) with time_basis_ms=3000 (this effect carries no "
        "amplitude of its own - the 3s period belongs to 13377's own aura), same pattern as the "
        "Healing Stream Totem split. sp_potency=13.1 is base-implied (base_points=0, "
        "points_per_level=1.2, V60=0+floor(59*1.2)=70, T=3.0s: 70 / (C(60) x (3.0/1.5)) = 13.08, "
        "rounded). The live EffectBonusMultiplier_1 of 0.032 implies only ~3.7 potency by coefficient - "
        "a large mismatch; base-implied wins by default, flagged for review. Shared with "
        "boss_pyroguard_emberseer (see 13377's note) - that NPC's own damage from this ability will "
        "also scale through the same converted row, at its own level; not a new risk (RealPointsPerLevel "
        "already scaled it by caster level before this conversion too)."
    ),
    raw_overrides={'AttributesEx': 136, 'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 1465, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Deals {pot1} Fire damage to all nearby enemies.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'BaseLevel': 1, 'SpellLevel': 1},
)
unbind_bonus_coefficients(fire_elemental_fire_shield_pulse_13376)  # stale spell_bonus_data row overrode the potency coefficient (D1)


reincarnation_21169 = spell(
    id=21169,
    name='Reincarnation',
    school=School.NATURE,
    attributes=8388608,
    category=1161,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1800000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=94, base_points=19),
    ],
    spell_icon_id=24,
    notes='pulled from existing data; SH0a A2: Reagent_1/ReagentCount_1 cleared (Ankh no longer required)',
    raw_overrides={'CastingTimeIndex': 1, 'BaseLevel': 30, 'SpellLevel': 30, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 344, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 11, 'SpellClassMask_1': 512, 'StanceBarOrder': 3, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


glyph_of_fire_elemental_totem_55455 = spell(
    id=55455,
    name='Glyph of Fire Elemental Totem',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=11),
    ],
    spell_icon_id=1,
    notes='pulled from existing data; SH0a A2 (T0a-REPORT s2): EffectBasePoints_1 -1 (value 0, die 1) so the glyph no longer floors the reworked 2 min Fire Elemental cooldown to 0; class mask kept (an all-zero mask matches the whole family); retired with the glyph project.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 8388608, 'EffectSpellClassMaskB_1': 16384, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'This glyph no longer has any effect.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 11, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


clearcasting_16246 = spell(
    id=16246,
    name='Clearcasting',
    school=64,
    dispel=1,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=15000,
    effects=[
        _mod(SpellModOp.COST, -16),
    ],
    spell_icon_id=212,
    notes='S1a A2 (brief Decisions 1 and 5): pulled from source/spells/npc.csv (row deleted in the same change). Elemental Focus Clearcasting: 2 charges, 15 s, eff1 mana cost -15 base (spell_sha_ele_elemental_focus sets 15 / 30 by rank). The stock eff2 (MOD_DAMAGE_PERCENT_DONE, the Elemental Oath damage carrier) is removed: the Oath clause is not in the doc. Cost and consume masks gain d2 b19 / b20 (Earthquake, Elemental Blast); spell_proc 16246 carries the same consume mask.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 87376, 'ProcChance': 100, 'ProcCharges': 2, 'BaseLevel': 10, 'SpellLevel': 10, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 2551185859, 'EffectSpellClassMaskA_2': 5120, 'EffectSpellClassMaskA_3': 16 | m.EARTHQUAKE | m.ELEMENTAL_BLAST, 'SpellVisualID_1': 2736, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Reduces the mana cost of your next two Fire, Frost or Nature spells.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next spells cost less mana.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 11, 'SpellClassMask_2': 16384, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


lava_flows_haste_65263 = spell(
    id=65263,
    name='Lava Flows',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        _aura(216, 3),
        _aura(AuraType.MOD_MELEE_HASTE, 3),
    ],
    spell_icon_id=3087,
    notes='S1a A2: pulled from existing data; rank 2 haste buff, spell + melee haste 4% for 12 s (see lava_flows_haste_64694). Not a chain rank: Shaman::LavaFlowsHasteSpell maps talent rank -> this id.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Haste increased.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell and melee haste.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


lava_flows_haste_65264 = spell(
    id=65264,
    name='Lava Flows',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        _aura(216, 5),
        _aura(AuraType.MOD_MELEE_HASTE, 5),
    ],
    spell_icon_id=3087,
    notes='S1a A2: pulled from existing data; rank 3 haste buff, spell + melee haste 6% for 12 s (see lava_flows_haste_64694).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Haste increased.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell and melee haste.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11},
)


astral_shift_51479 = _talent(
    51479, 'Astral Shift', 'Rank 3',
    [_aura(AuraType.MOD_SPELL_CRIT_CHANCE, 2)], 3066,
    _desc('Increases your spell critical strike chance by 3%. When you are stunned, feared or silenced, you shift into the Astral Plane, reducing all damage taken by 10% for the duration.',
          'Being stunned, feared or silenced while casting an offensive Nature spell grants an empowered Astral Shift, reducing all damage taken by 25% for 6 sec.',
          last=True),
    level=1, attributes=262352, AttributesEx3=67108864, AttributesEx4=524288, ProcTypeMask=0, ProcChance=0,
    SpellPriority=50,
    notes='S1a A2: pulled from existing data; rank 3 (capstone: the empowered shift is chosen by rank in ShamanAstralShiftUnitScript). See astral_shift_51474.',
)


# =====================================================================================================================
# S1a A2: spell_proc rows and script bindings for the Elemental rank spells (WP brief class table, B2's constraints:
# the scripted rolls proc at 100%, every proc talent has a DUMMY effect, Lava Surge keeps the native 15% + ICD 6 s).
# Every row with a done-spell / periodic ProcFlags carries SpellPhaseMask HIT (L9).
# =====================================================================================================================

# Lightning Overload: Lightning Bolt, Chain Lightning and (capstone, script-gated) Lava Burst, every damaging hit.
procs_on(
    -30675, proc_flags=_PROC_DONE_SPELL_MAGIC_NEG, family_name=11, family_mask=(_LB | _CL, _LAVA_BURST, 0),
    spell_type_mask=_PROC_TYPE_DAMAGE, spell_phase_mask=_PROC_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_CRIT, chance=100,
)
unbind_script(-30675, 'spell_sha_lightning_overload')
scripted_by(-30675, 'spell_sha_ele_lightning_overload')

# Elemental Focus (Decision 5): the chain key carries rank 2; the positive row and script key of rank 1 go. No proc
# cooldown (S1a review m4): the refresh to 2 charges is idempotent and must follow every crit, even one 0.5 s after the
# last (a hard-cast Lightning Bolt crit, then an instant Frost Shock crit).
remove_spell_proc(16164)
procs_on(
    -16164, proc_flags=_PROC_DONE_SPELL_MAGIC_NEG, school_mask=_FFN, spell_type_mask=_PROC_TYPE_DAMAGE,
    spell_phase_mask=_PROC_PHASE_HIT, hit_mask=_PROC_HIT_CRIT, chance=100,
)
unbind_script(16164, 'spell_sha_elemental_focus')
scripted_by(-16164, 'spell_sha_ele_elemental_focus')

# Clearcasting 16246: the consume mask gains d2 b19 / b20 (same as its cost effect); Oath's damage script is unbound.
procs_on(
    16246, proc_flags=0, family_name=11, family_mask=(2551185859, 5120, 16 | m.EARTHQUAKE | m.ELEMENTAL_BLAST),
    spell_phase_mask=1, attributes_mask=12,
)
unbind_script(16246, 'spell_sha_clearcasting')
scripted_by(16246, 'spell_sha_ele_fury_capstone')

# Elemental Devastation: non-periodic Fire / Frost / Nature crit of a shaman spell.
procs_on(
    -30160, proc_flags=_PROC_DONE_SPELL_MAGIC_NEG, school_mask=_FFN, family_name=11, spell_type_mask=_PROC_TYPE_DAMAGE,
    spell_phase_mask=_PROC_PHASE_HIT, hit_mask=_PROC_HIT_CRIT, chance=100,
)
scripted_by(-30160, 'spell_sha_ele_devastation')

# Lightning Mastery: Raw Power / Lightning Mastery rolls on any non-periodic spell crit (once per cast in the script).
procs_on(
    -16578, proc_flags=_PROC_DONE_SPELL_MAGIC_NEG, school_mask=_FFN, family_name=11, spell_type_mask=_PROC_TYPE_DAMAGE,
    spell_phase_mask=_PROC_PHASE_HIT, hit_mask=_PROC_HIT_CRIT, chance=100,
)
scripted_by(-16578, 'spell_sha_ele_lightning_mastery')

# Elemental Precision capstone (rank 3 only).
procs_on(
    30674, proc_flags=_PROC_DONE_SPELL_MAGIC_NEG, family_name=11, spell_type_mask=_PROC_TYPE_DAMAGE,
    spell_phase_mask=_PROC_PHASE_HIT, hit_mask=_PROC_HIT_CRIT, chance=100,
)
scripted_by(30674, 'spell_sha_ele_precision_capstone')

# Elemental Reach capstone (rank 2 only): distance and ICD in the script.
procs_on(
    29000, proc_flags=_PROC_DONE_SPELL_MAGIC_NEG, school_mask=_FFN, family_name=11, spell_type_mask=_PROC_TYPE_DAMAGE,
    spell_phase_mask=_PROC_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_CRIT, chance=100,
)
scripted_by(29000, 'spell_sha_ele_reach_capstone')

# Lava Surge (Lava Flows rank 3): Flame Shock periodic damage, 15% native, ICD 6 s.
procs_on(
    51482, proc_flags=_PROC_DONE_PERIODIC, family_name=11, family_mask=(_FLAME_SHOCK, 0, 0),
    spell_type_mask=_PROC_TYPE_DAMAGE, spell_phase_mask=_PROC_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_CRIT, chance=15,
    cooldown_ms=6000,
)
scripted_by(51482, 'spell_sha_ele_lava_surge')

# Rising Flames capstone (rank 2): the stack tick.
scripted_by(16544, 'spell_sha_ele_rising_flames')

# Astral Shift: the stock pair is unbound and nothing replaces it. The shift is started from ShamanAstralShiftUnitScript
# (UnitScript OnAuraApply, spell_shaman_elemental.cpp) so every stun, fear or silence counts, triggered ones included
# (S1a review M1). The talent has no proc, so there is no spell_proc row and no script on the chain.
unbind_script(-51474, 'spell_sha_astral_shift')
unbind_script(-51474, 'spell_sha_astral_shift_aura')
# The live all-zero row -51474 only worked by inheriting the DBC proc flags; with the flags now 0 it would log a boot
# error ("doesn't have ProcFlags value defined"), so it goes.
remove_spell_proc(-51474)

# Fire Nova damage 8349: the Rising Flames stack scaling (B3, spell_shaman_totems.cpp). The Rising Flames buff carries no
# SPELLMOD_DAMAGE on these masks: the script scales the hit, a mod would count twice.
scripted_by(fire_nova_8349, 'spell_sha_fire_nova_rework_damage')
