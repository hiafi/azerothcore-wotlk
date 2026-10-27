"""
Rogue - RG0a shared baseline, data half: the energy-haste passive, the six poison self auras, the Non-lethal poison
spell_group, their SkillLineAbility rows, and the hidden script numbers (`const()`) the C++ reads through the generated
RogueData.h.

Source of truth: docs/reworks/rogue-shared-rework.md ("Energy and haste", "Poisons" + the six poison entries),
.agents/plans/rogue-rework/rogue-rework.RG0a-HANDOFF.md (Known-hard items 1 and 2, IDs, Family bits, Shared facts,
corrections C1 and C6), rogue-rework.RG0a-WP-BRIEF.md (variable names), p0-spike-ref/rogue_p0_spike.py (the passed shapes
of the energy passive and the poison aura frame).

Ids: 203700 Energy Haste, 203701-203706 the poison auras (Instant, Deadly, Wound, Crippling, Mind-numbing, Anesthetic),
SkillLineAbility 30780-30785 (same order), spell_group 1287 (Non-lethal). There is no Lethal group (C6): Lethal exclusivity
is the spell_rog_poison slot script (Lethal slots = RogueData::POISON_LETHAL_SLOTS), so a second Lethal slot is one number.

Conventions: SpellClassSet 8, EquippedItemClass -1 (the auras survive weapon swaps and disarms), AttributesEx3
ALLOW_AURA_WHILE_DEAD (survive death), the poison auras are NOT passive (they show as buffs and right-click off) and carry
AttributesEx ALLOW_WHILE_STEALTHED (a swap never breaks Stealth); GCD 133 / 1000 (the core hastes only the 1500 GCD), cast
time instant, self range, infinite duration. Family bits per handoff C1 (the aura carries the bit the chance mods read,
never the payload's identity bits): Lethal d2 b1, Crippling d2 b2, Mind-numbing + Anesthetic d2 b3. Aura texts are number-free
and tooltips are the shared doc verbatim, damage through pot_text(), other numbers `$<payload>s1` / `$<payload>d`.
"""

from lib.dsl import AuraType, Effect, EffectType, PowerType, RANGE_SELF, School
from lib.dsl.registry import (
    const, procs_on, scripted_by, skill_line_ability, spell, spell_group, spell_group_rule, pot_text,
)

from . import _masks as m
from .rogue_trigger_spells import (
    anesthetic_poison_26688, crippling_poison_3409, deadly_poison_2818, instant_poison_8680, mind_numbing_poison_5760,
    wound_poison_13218,
)

# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h) ----
_SPELLFAMILY_ROGUE = 8
_ATTR0_PASSIVE = 0x40
_ATTR0_DO_NOT_DISPLAY = 0x80
_ATTR1_ALLOW_WHILE_STEALTHED = 0x20      # AttributesEx: a poison swap never breaks Stealth
_ATTR3_ALLOW_AURA_WHILE_DEAD = 0x100000  # AttributesEx3: the aura survives death

# ---- Auras / effects / targets ----
_POWER_ENERGY = 3                        # MOD_POWER_REGEN_PERCENT misc value
_TARGET_UNIT_CASTER = 1

# ---- spell_proc masks (src/server/game/Spells/SpellMgr.h) ----
_PROC_DONE_MELEE_AUTO_ATTACK = 0x4
_PROC_DONE_SPELL_MELEE_DMG_CLASS = 0x10
_PROC_DONE_SPELL_RANGED_DMG_CLASS = 0x100  # Throw 2764 / Deadly Throw 26679 are DmgClass 3 without AUTO_REPEAT (C5)
_PROC_SPELL_PHASE_HIT = 0x2
# Melee auto attack | melee-class spell | ranged-class spell. Shoot (auto-repeat, 0x40) stays out.
_POISON_PROC_FLAGS = _PROC_DONE_MELEE_AUTO_ATTACK | _PROC_DONE_SPELL_MELEE_DMG_CLASS | _PROC_DONE_SPELL_RANGED_DMG_CLASS

# ---- Stock icons / visuals ----
_ICON_ENERGY_HASTE = 235     # Adrenaline Rush
_ICON_INSTANT_POISON = 247
_ICON_DEADLY_POISON = 513
_ICON_WOUND_POISON = 1496
_ICON_CRIPPLING_POISON = 163
_ICON_MIND_NUMBING_POISON = 264
_ICON_ANESTHETIC_POISON = 110
_SV_POISON_AURA = 12720      # SpellVisualID_1 of the six poison auras

_SKILL_ASSASSINATION = 253   # SkillLine 40 (Poisons) has no tab (A36); the Assassination tab is the spellbook home
_CLASS_MASK_ROGUE = 8


# =====================================================================================================================
# Script numbers (hidden constants; generated RogueData::NAME, read by RogueMechanics.cpp / spell_rogue_shared.cpp)
# =====================================================================================================================
POISON_LETHAL_CHANCE_PCT = const(
    'POISON_LETHAL_CHANCE_PCT', 20,
    'Poisons: Lethal (Instant, Deadly, Wound) base application chance per hit or cast, % [tune].')
POISON_CRIPPLING_CHANCE_PCT = const(
    'POISON_CRIPPLING_CHANCE_PCT', 30, 'Poisons: Crippling base application chance, % (stock) [fixed].')
POISON_MIND_NUMBING_CHANCE_PCT = const(
    'POISON_MIND_NUMBING_CHANCE_PCT', 50, 'Poisons: Mind-numbing base application chance, % (stock) [fixed].')
POISON_ANESTHETIC_CHANCE_PCT = const(
    'POISON_ANESTHETIC_CHANCE_PCT', 50, 'Poisons: Anesthetic base application chance, % (stock) [fixed].')
POISON_REFERENCE_WEAPON_SPEED_MS = const(
    'POISON_REFERENCE_WEAPON_SPEED_MS', 2600,
    'Poisons: an auto attack\'s chance is multiplied by the hitting hand\'s weapon speed over this, ms [fixed].')
POISON_LETHAL_SLOTS = const(
    'POISON_LETHAL_SLOTS', 1, 'Poisons: Lethal slots (Assassination\'s Master Poisoner capstone makes it 2) [fixed].')
POISON_GLOW_ENCHANT = const(
    'POISON_GLOW_ENCHANT', 323,
    'Poisons: SpellItemEnchantment id (ItemVisual 26) written into the visible temp-enchant half of the weapon slots [fixed].')
ENERGY_HASTE_MAX_PCT = const(
    'ENERGY_HASTE_MAX_PCT', 100, 'Energy and haste: the cap on the energy regeneration bonus from haste, % [fixed].')


# =====================================================================================================================
# Energy Haste 203700 (shared doc "Energy and haste"): energy regeneration x (1 + spell haste) for every energy user
# =====================================================================================================================
# Hidden passive granted by RoguePlayerScript (EnsureEnergyHaste), never .learned, no SkillLineAbility. eff0 is the stock
# 63622 shape: MOD_POWER_REGEN_PERCENT (110) misc 3 POWER_ENERGY, stored base_points -1 (live 0); spell_rog_energy_haste
# keeps it at clamp(round(100 / castSpeed - 100), 0, ENERGY_HASTE_MAX_PCT) from the periodic eff1 (PERIODIC_DUMMY 500 ms,
# no haste attribute). Attributes 0xC0 (PASSIVE | DO_NOT_DISPLAY), AttributesEx3 ALLOW_AURA_WHILE_DEAD, no GCD, no bits.
energy_haste_203700 = spell(
    id=203700, name='Energy Haste', school=School.NORMAL,
    attributes=_ATTR0_PASSIVE | _ATTR0_DO_NOT_DISPLAY, category=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_POWER_REGEN_PERCENT, misc_value=_POWER_ENERGY,
               base_points=-1, implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=500,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_ENERGY_HASTE,
    notes='RG0a A1, shared doc "Energy and haste": hidden passive, granted by RoguePlayerScript::EnsureEnergyHaste to '
          'every energy user (rogue, druid; the one Classless change point is Rogue::IsEnergyUser). eff0 aura 110 misc 3 '
          '(POWER_ENERGY) stored -1 = live 0 (stock 63622 shape), eff1 PERIODIC_DUMMY 500 ms; spell_rog_energy_haste '
          'writes eff0 = clamp(round(100 / castSpeed - 100), 0, ENERGY_HASTE_MAX_PCT) and SyncEnergyHaste pushes the '
          'change to the client-predicted regen field. Attributes 0xC0, AttributesEx3 0x100000, SpellLevel 1, no GCD, '
          'no family bits, no SkillLineAbility.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE,
        'EquippedItemClass': -1,
        'SpellLevel': 1,
        'CastingTimeIndex': 1,
        'AttributesEx3': _ATTR3_ALLOW_AURA_WHILE_DEAD,
        'Description_Lang_enUS': 'Your energy regenerates faster with haste.',
    },
)
scripted_by(energy_haste_203700, 'spell_rog_energy_haste')


# =====================================================================================================================
# The six poison self auras 203701-203706 (shared doc "Poisons" + the six poison entries)
# =====================================================================================================================
def _poison_aura(spell_id, name, payload, icon, chance, level, mask_d2, description, aura_description, notes):
    """One poison self aura: infinite, instant, 133 / 1000 GCD, non-passive buff, procs its payload on melee auto
    attacks and melee / ranged ability hits (spell_proc below); spell_rog_poison rolls the chance and casts the payload."""
    aura = spell(
        id=spell_id, name=name, school=School.NATURE, attributes=0, category=0,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0,
        mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=payload.id,
                        implicit_target_a=_TARGET_UNIT_CASTER)],
        spell_icon_id=icon,
        notes='RG0a A1, shared doc "Poisons": ' + notes + f' Trains at {level} (SpellLevel = learn level). Base chance '
              f'{chance}% (RogueData, read by the roll script). Family bit d2 {mask_d2:#x} (handoff C1: the aura '
              'carries the bit the chance mods read, never the payload\'s identity bits). Attributes 0 (not passive: a '
              'buff that right-clicks off), AttributesEx 0x20 (ALLOW_WHILE_STEALTHED), AttributesEx3 0x100000 '
              '(survives death), EquippedItemClass -1 (survives swaps and disarms), GCD 133 / 1000, instant, self, '
              'infinite. spell_proc: flags 0x114, HIT phase, chance 100, attributes_mask 0 (triggered casts never roll).',
        raw_overrides={
            'SpellClassSet': _SPELLFAMILY_ROGUE,
            'SpellClassMask_3': mask_d2,
            'EquippedItemClass': -1,
            'SpellLevel': level,
            'CastingTimeIndex': 1,
            'StartRecoveryCategory': 133,
            'StartRecoveryTime': 1000,
            'AttributesEx': _ATTR1_ALLOW_WHILE_STEALTHED,
            'AttributesEx3': _ATTR3_ALLOW_AURA_WHILE_DEAD,
            'SpellVisualID_1': _SV_POISON_AURA,
            'Description_Lang_enUS': description,
            'AuraDescription_Lang_enUS': aura_description,
        },
    )
    procs_on(
        aura, proc_flags=_POISON_PROC_FLAGS, spell_type_mask=0, spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=0,
        attributes_mask=0, chance=100.0, cooldown_ms=0,
    )
    scripted_by(aura, 'spell_rog_poison')
    return aura


_COATS = 'Coats your weapons with poison. Each of your hits and attacks has a chance to '

# Instant: "[30 potency] Nature damage"; eff0 of 8680 is the damage.
instant_poison_203701 = _poison_aura(
    203701, 'Instant Poison', instant_poison_8680, _ICON_INSTANT_POISON, 20, 20, m.LETHAL_AURA,
    _COATS + 'deal ' + pot_text(instant_poison_8680, effect=1) + ' Nature damage to the target. Lasts until cancelled.',
    'Your weapons are coated with poison.',
    'Instant Poison, Lethal slot, procs payload 8680.')

# Deadly: "[damage] Nature damage over 12 sec" = the periodic effect's total at the 12 sec duration; eff0 of 2818.
deadly_poison_203702 = _poison_aura(
    203702, 'Deadly Poison', deadly_poison_2818, _ICON_DEADLY_POISON, 20, 30, m.LETHAL_AURA,
    _COATS + 'poison the target for ' + pot_text(deadly_poison_2818, effect=1, variant='total')
    + ' Nature damage over $2818d. Stacks up to 5 times.',
    'Your weapons are coated with poison.',
    'Deadly Poison, Lethal slot, procs payload 2818.')

# Wound: "[10 potency] Nature damage and wound the target for 15 sec, causing your bleeds to deal 20% more damage"; the
# damage is eff1 of 13218 (DSL effect 2), the 20% is eff0 (aura 271 after A2's rewrite, stored 19).
wound_poison_203703 = _poison_aura(
    203703, 'Wound Poison', wound_poison_13218, _ICON_WOUND_POISON, 20, 32, m.LETHAL_AURA,
    _COATS + 'deal ' + pot_text(wound_poison_13218, effect=2) + ' Nature damage and wound the target for $13218d, '
    'causing your bleeds to deal $13218s1% more damage to it.',
    'Your weapons are coated with poison.',
    'Wound Poison, Lethal slot, procs payload 13218.')

crippling_poison_203704 = _poison_aura(
    203704, 'Crippling Poison', crippling_poison_3409, _ICON_CRIPPLING_POISON, 30, 20, m.CRIPPLING_AURA,
    _COATS + 'reduce the target\'s movement speed by $3409s1% for $3409d.',
    'Your weapons are coated with a slowing poison.',
    'Crippling Poison, Non-lethal slot, procs payload 3409.')

mind_numbing_poison_203705 = _poison_aura(
    203705, 'Mind-numbing Poison', mind_numbing_poison_5760, _ICON_MIND_NUMBING_POISON, 50, 24, m.NONLETHAL_AURA,
    _COATS + 'increase the target\'s casting time by $5760s1% for $5760d.',
    'Your weapons are coated with a numbing poison.',
    'Mind-numbing Poison, Non-lethal slot, procs payload 5760.')

# Anesthetic: "remove 1 Enrage effect from the target and deal [10 potency] Nature damage"; the damage is eff0 of 26688.
anesthetic_poison_203706 = _poison_aura(
    203706, 'Anesthetic Poison', anesthetic_poison_26688, _ICON_ANESTHETIC_POISON, 50, 40, m.NONLETHAL_AURA,
    _COATS + 'remove 1 Enrage effect from the target and deal ' + pot_text(anesthetic_poison_26688, effect=1)
    + ' Nature damage.',
    'Your weapons are coated with a calming poison.',
    'Anesthetic Poison, Non-lethal slot, procs payload 26688.')

# Non-lethal exclusivity: casting one evicts the other two (_RemoveNoStackAurasDueToAura). Lethal has no group (C6): the
# slot script owns it (POISON_LETHAL_SLOTS); 1286 stays reserved and unused.
spell_group(1287, crippling_poison_203704, mind_numbing_poison_203705, anesthetic_poison_203706)
spell_group_rule(1287, stack_rule=1, description='Rogue Non-lethal poisons: one at a time')

# SkillLineAbility 30780-30785 in spell order. Skill 253 (Assassination tab; skill 40 has no tab, A36), rogue class mask 8,
# AcquireMethod 0 (trained). The trainer rows are rogue_trainers.py's.
for _sla_id, _aura in (
    (30780, instant_poison_203701), (30781, deadly_poison_203702), (30782, wound_poison_203703),
    (30783, crippling_poison_203704), (30784, mind_numbing_poison_203705), (30785, anesthetic_poison_203706),
):
    skill_line_ability(id=_sla_id, skill_line=_SKILL_ASSASSINATION, spell_id=_aura.id, class_mask=_CLASS_MASK_ROGUE,
                       min_skill_line_rank=1, acquire_method=0)
