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


def command_potency(authored: float, slot: str) -> float:
    """The round 1 potency of a command authored at `authored` (PLAN §3) in `slot` ('I' or 'II')."""
    if slot not in ('I', 'II'):
        raise ValueError(f"command_potency: slot {slot!r}, expected 'I' or 'II'")
    return round(authored * (COMMAND_I_SCALE if slot == 'I' else COMMAND_II_SCALE), 4)


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
