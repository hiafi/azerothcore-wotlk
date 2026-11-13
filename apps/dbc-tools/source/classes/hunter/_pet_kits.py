"""
Hunter pet families (.agents/plans/hunter-pet-families/hunter-pet-families.PLAN.md): shared constants and row helpers
for the per-family pet kits. F0 creates it; the family stages (F1 Ferocity, F2 Tenacity, F3 Cunning) import it from
their own files (`from . import _pet_kits as kits`).

Leading underscore = not loaded as a class file by lib/dsl/registry.py's load_class_package, just an importable module.
It declares nothing.
"""

from lib.dsl import PowerType

from . import _masks as m

# ---- round 1 potency start (PLAN §11 ruling 1) ----
# A new family's commands start at these fractions of the PLAN §3 numbers (the brainstorm budgets: Ferocity 400 / 1000,
# Tenacity 600 / 1000, Cunning 900 / 1800). The 2026-11-01 balance pass left every type-default Command I at x0.84 and
# every Command II at x0.65 of those budgets (CORE-AUDIT §1.4); the sims (SIM1, TUNE) correct from there. F0 applies
# neither: the five finished kits keep their live values.
COMMAND_I_SCALE = 0.84
COMMAND_II_SCALE = 0.65


# ---- family-type damage scales (PLAN §11 ruling 23, user 2026-11-13) ----
# The 32-family sim sweep (120 s x 5, 1 target, full_raid buffs) put Cunning at ~3,000 DPS against Ferocity ~1,690 and
# Tenacity ~1,830, so the type scales below are the first correction (per-family tuning toward ~2,000 follows in TUNE).
# Both scales act on the authored/current number at the point it is written, so the PLAN §3 / balance-pass number stays
# visible in the source and the notes; they are data only (nothing in C++ reads them).
FEROCITY_TENACITY_BASIC_SCALE = 1.5     # Bite 17253, Claw 16827, Smack 49966: the Ferocity and Tenacity basic attacks
CUNNING_DAMAGE_SCALE = 0.39             # every Cunning command / helper / basic damage potency (never a utility value)
RULING_23_NOTE = ' Ruling 23 (user 2026-11-13): Cunning damage potency x0.39 on top of the authored number.'
# Ruling 23b (user 2026-11-13, PLAN §11): after ruling 23 the re-sweep put Tenacity at ~1,912 DPS against ~1,750 for
# Ferocity and Cunning; Tenacity command damage averages 779 DPS of that, so every Tenacity command and damage helper
# takes x0.80 (the basics keep ruling 23's x1.5; utilities, absorbs, heals and the flat Bad Attitude shield are never
# scaled).
TENACITY_COMMAND_SCALE = 0.80
RULING_23B_NOTE = ' Ruling 23b (user 2026-11-13): Tenacity command damage potency x0.80 on top of the authored number.'
# Ruling 24 (user 2026-11-13, PLAN §11): pet type identity. Single-target order Ferocity > Tenacity > Cunning, AoE
# order Cunning > Tenacity > Ferocity, 3% steps around Tenacity. A single-target command is one Beast Cleave copies (the
# Hunter::IsBeastCleaveExcluded rule: no area or chain > 1 effect, no TRIGGER_SPELL into an area) together with its
# non-area damage helpers (multi-hit strikes, Twin Bite's second bite); an AoE command, its splash and every utility,
# basic attack and Tenacity value keep their numbers. The Beast Cleave half of the ruling (the pet's copies by type) is
# C++ (PET_BEAST_CLEAVE_*_SCALE in hunter_bm_spells.py).
FEROCITY_ST_COMMAND_SCALE = 1.07
CUNNING_ST_COMMAND_SCALE = 0.94         # on top of ruling 23's CUNNING_DAMAGE_SCALE
_ST_SCALES = {'Ferocity': FEROCITY_ST_COMMAND_SCALE, 'Cunning': CUNNING_ST_COMMAND_SCALE}


def ruling_24_note(tree: str, *before: float) -> str:
    """The notes line of a ruling 24 spell: each pre-ruling-24 potency `before` -> its scaled value."""
    scale = _ST_SCALES[tree]
    pairs = ', '.join(f'{round(b, 4):g} -> {round(b * scale, 4):g}' for b in before)
    return (f' Ruling 24 (user 2026-11-13): {tree} single-target command damage potency x{scale:g}'
            f'{" (on top of ruling 23)" if tree == "Cunning" else ""}: {pairs}.')


def command_potency(authored: float, slot: str, *, cunning: bool = False, tenacity: bool = False,
                    ferocity: bool = False, single_target: bool = False) -> float:
    """The round 1 potency of a command authored at `authored` (PLAN §3) in `slot` ('I' or 'II'). `cunning=True` is a
    Cunning command's damage (ruling 23, x0.39) and `tenacity=True` a Tenacity command's (ruling 23b, x0.80): the type
    scale applies on top (heals, absorbs and debuff values never pass it). `single_target=True` marks a single-target
    command or damage helper (ruling 24): x1.07 with `ferocity=True`, a further x0.94 with `cunning=True`, nothing
    more for Tenacity."""
    if slot not in ('I', 'II'):
        raise ValueError(f"command_potency: slot {slot!r}, expected 'I' or 'II'")
    if cunning + tenacity + ferocity > 1:
        raise ValueError("command_potency: cunning, tenacity and ferocity are exclusive")
    if single_target and not (cunning or tenacity or ferocity):
        raise ValueError("command_potency: single_target needs the family type (ferocity / tenacity / cunning)")
    scale = COMMAND_I_SCALE if slot == 'I' else COMMAND_II_SCALE
    if cunning:
        scale *= CUNNING_DAMAGE_SCALE
        if single_target:
            scale *= CUNNING_ST_COMMAND_SCALE
    elif tenacity:
        scale *= TENACITY_COMMAND_SCALE
    elif ferocity and single_target:
        scale *= FEROCITY_ST_COMMAND_SCALE
    return round(authored * scale, 4)


def cunning_damage(current: float, *, single_target: bool = False) -> float:
    """A Cunning damage potency written as a literal (Spider, the type defaults: balance-pass numbers, no PLAN §3
    authored value): `current` x the ruling 23 scale, and x the ruling 24 single-target scale with
    `single_target=True`."""
    scale = CUNNING_DAMAGE_SCALE * (CUNNING_ST_COMMAND_SCALE if single_target else 1.0)
    return round(current * scale, 4)


def ferocity_st_damage(current: float) -> float:
    """A Ferocity single-target command potency written as a literal (Wolf, Cat, Raptor's Savage Rend, the Ferocity
    type defaults: balance-pass numbers): `current` x the ruling 24 scale."""
    return round(current * FEROCITY_ST_COMMAND_SCALE, 4)


def tenacity_damage(current: float) -> float:
    """A Tenacity command damage potency written as a literal (Bear's Swipe and Maul, the Tenacity type defaults:
    balance-pass numbers, no PLAN §3 authored value): `current` x the ruling 23b scale."""
    return round(current * TENACITY_COMMAND_SCALE, 4)


def basic_potency(current: float, tree: str) -> float:
    """A pet basic attack's potency under the ruling 23 type scales: Ferocity and Tenacity x1.5, Cunning x0.39.
    `current` is the pre-ruling number (Claw / Smack 25.5, Bite 40.8, Spit 33.0)."""
    if tree in ('Ferocity', 'Tenacity'):
        return round(current * FEROCITY_TENACITY_BASIC_SCALE, 4)
    if tree == 'Cunning':
        return round(current * CUNNING_DAMAGE_SCALE, 4)
    raise ValueError(f"basic_potency: tree {tree!r}, expected Ferocity, Tenacity or Cunning")


# AoE commands: the 50% share of every non-primary target is the const COMMAND_AOE_FALLOFF_PCT in hunter_bm_spells.py
# (the C++ script reads it from HunterData.h); bind an AoE command to it with
# `scripted_by(spell, 'spell_hun_command_aoe_falloff')`, plus 'spell_hun_command_splash' when an area effect would
# otherwise hit the primary a second time (the Swipe shape, CORE-AUDIT §2.2).

# ---- slot 2 / slot 3 utilities (PLAN §3, §5.3) ----
# Pet-cast, Focus 0, family 9. SpellClassMask_2 = d1 b28 (pet ability) + d1 b29 (pet utility, the Mobility group).
# Ancient Hysteria, Eternal Guardian and Earthen Bulwark pass `mobility=False` (ruling 10): d1 b28 alone.
UTILITY_ATTRIBUTES = 0x50010        # IS_ABILITY | NOT_SHAPESHIFTED | DO_NOT_SHEATH (Roar of Courage, Tear Armor)
UTILITY_POWER_TYPE = PowerType.FOCUS
ATTR1_INITIATE_COMBAT = 0x200       # enemy-target utilities only (Tear Armor, Web Pull): the pet starts attacking


def utility_raw(level: int, *, enemy_target: bool = False, mobility: bool = True, **extra) -> dict:
    """The raw_overrides every slot 2 / slot 3 utility shares: unlock level (`SpellLevel`, the SkillLineAbility row
    teaches it at that pet level), family 9 with the utility carrier, EquippedItemClass -1, no chain amplitude drift.
    `enemy_target` adds AttributesEx INITIATE_COMBAT (the pet attacks what it casts on). `extra` wins."""
    raw = {
        'SpellLevel': level, 'BaseLevel': level, 'EquippedItemClass': -1, 'SpellClassSet': 9,
        'SpellClassMask_2': m.PET_ABILITY | (m.PET_UTILITY if mobility else 0),
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
    }
    if enemy_target:
        raw['AttributesEx'] = ATTR1_INITIATE_COMBAT
    raw.update(extra)
    return raw
