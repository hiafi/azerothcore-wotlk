"""
Rogue - RG0a shared baseline, data half: the energy-haste passive, the six poison self auras, the Non-lethal poison
spell_group, their SkillLineAbility rows, and the hidden script numbers (`const()`) the C++ reads through the generated
RogueData.h. RG0b appends (bottom of the file) the tank kit and utility rows: Enforcer Stance + its crit-immunity child,
Insult, Ghostly Veil, Shroud of Concealment, the new Shiv and the Ambush teleport helper (203720-203726).

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
    const, custom_attr, linked_spell, procs_on, scripted_by, skill_line_ability, spell, spell_group, spell_group_rule,
    pot_text,
)

from . import _masks as m
from .rogue_assassination import tooltip_vile_poisons_1320
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
def _poison_aura(spell_id, name, payload, icon, chance, level, mask_d2, description, aura_description, notes,
                 tooltip=None):
    """One poison self aura: infinite, instant, 133 / 1000 GCD, non-passive buff, procs its payload on melee auto
    attacks and melee / ranged ability hits (spell_proc below); spell_rog_poison rolls the chance and casts the payload."""
    aura = spell(
        id=spell_id, name=name, school=School.NATURE, attributes=0, category=0,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0,
        mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=payload.id,
                        implicit_target_a=_TARGET_UNIT_CASTER)],
        spell_icon_id=icon, tooltip_vars=tooltip,
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
    _COATS + 'deal ' + pot_text(instant_poison_8680, effect=1, var='vile') + ' Nature damage to the target. Lasts until cancelled.',
    'Your weapons are coated with poison.',
    'Instant Poison, Lethal slot, procs payload 8680.', tooltip=tooltip_vile_poisons_1320)

# Deadly: "[damage] Nature damage over 12 sec" = the periodic effect's total at the 12 sec duration; eff0 of 2818.
deadly_poison_203702 = _poison_aura(
    203702, 'Deadly Poison', deadly_poison_2818, _ICON_DEADLY_POISON, 20, 30, m.LETHAL_AURA,
    _COATS + 'poison the target for ' + pot_text(deadly_poison_2818, effect=1, variant='total', var='vile')
    + ' Nature damage over $2818d. Stacks up to 5 times.',
    'Your weapons are coated with poison.',
    'Deadly Poison, Lethal slot, procs payload 2818.', tooltip=tooltip_vile_poisons_1320)

# Wound: "[10 potency] Nature damage and wound the target for 15 sec, causing your bleeds to deal 20% more damage"; the
# damage is eff1 of 13218 (DSL effect 2), the 20% is eff0 (aura 271 after A2's rewrite, stored 19).
wound_poison_203703 = _poison_aura(
    203703, 'Wound Poison', wound_poison_13218, _ICON_WOUND_POISON, 20, 32, m.LETHAL_AURA,
    _COATS + 'deal ' + pot_text(wound_poison_13218, effect=2, var='vile') + ' Nature damage and wound the target for $13218d, '
    'causing your bleeds to deal $13218s1% more damage to it.',
    'Your weapons are coated with poison.',
    'Wound Poison, Lethal slot, procs payload 13218.', tooltip=tooltip_vile_poisons_1320)

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


# =====================================================================================================================
# RG0b: the tank kit (Enforcer Stance, Insult, Ghostly Veil), Shroud of Concealment, the new Shiv, the Ambush teleport
# =====================================================================================================================
# Source of truth: docs/reworks/rogue-shared-rework.md (Enforcer Stance, Insult, Ghostly Strike, Shroud of Concealment,
# Shiv, Ambush entries), rogue-rework.RG0b-HANDOFF.md (Known-hard 1-6 and 9, U2-U4, U9), RG0b-WP-BRIEF.md (resolutions
# C5,
# C6, C9 and the DSL variable names), RG0b-0VERIFY.md (items 4 and 5), DK deathknight_shared.py (Blood Presence + the
# 203000
# child + the 57340 links) and the passed P0 spike shapes 204372 (Ambush teleport) and 204374 (Shroud).
# Ids: 203720 Enforcer Stance, 203721 its hidden crit-immunity child, 203722 Insult, 203723 Ghostly Veil, 203724 Shroud
# of
# Concealment, 203725 Shiv, 203726 Ambush Teleport; SkillLineAbility 30790-30793 (Enforcer, Insult, Shroud, Shiv).
# Ghostly Strike 14278, Ambush 8676 and the other stock rows are rogue_spells.py's (A2); trainer rows are
# rogue_trainers.py's.
_ATTR0_ONLY_STEALTHED = 0x20000
_ATTR1_SHIV = 134218240                  # stock 1752 AttributesEx 0x8000200 (brief C9: the decimal, not 0x8000400)
_ATTR3_SHIV = 0x400                      # stock 1752 AttributesEx3
_ATTR1_SHADOWSTEP = 0x420                # stock 36563 AttributesEx
_AURA_MOD_ATTACKER_MELEE_CRIT_CHANCE = 187
_AURA_MOD_ATTACKER_RANGED_CRIT_CHANCE = 188
_EFFECT_ATTACK_ME = 114                  # Taunt 355 eff0
_EFFECT_TELEPORT_UNITS = 5
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_CASTER_AREA_RAID = 56
_TARGET_DEST_TARGET_BACK = 65
_MISC_ALL_SCHOOLS = 127
_MISC_ARMOR = 1                          # MOD_BASE_RESISTANCE_PCT misc 1 = armor (item armor only)
_SCRIPT_CAST_RANGE = 50000.0             # bug 570: a script cast at a unit needs a real range
_TELEPORT_RADIUS_INDEX = 7               # stock 36563 eff0
_STEALTH_AURA_INTERRUPT_FLAGS = 0x23C04  # stock 1784
_FORM_STEALTH_MASK = 0x20000000
_ITEM_CLASS_WEAPON = 2
_ANY_MELEE_WEAPON = 173555               # 0x2A5F3, stock 1752 EquippedItemSubclass
_SKILL_COMBAT = 38
_SKILL_SUBTLETY = 39
_ICON_DEFENSIVE_STANCE = 276
_ICON_TAUNT = 24
_ICON_GHOSTLY_STRIKE = 596
_ICON_STEALTH = 250
_ICON_SHIV = 1834
_ICON_SHADOWSTEP = 2363
_SV_TAUNT = 34
_SV_STEALTH = 184
_SV_SHIV = 8056
_SV_SHADOWSTEP_TELEPORT = 8262
_ENFORCER_LEVEL = 10
_SHROUD_LEVEL = 28
_SHIV_LEVEL = 50
# SPELL_ATTR0_CU_POSITIVE_EFF2: aura 79 with a negative amount reads as a debuff
_CUSTOM_ATTR_POSITIVE_EFF2 = 0x08000000


# ---- Enforcer Stance crit-immunity child (DK 203000 shape) ----
# Hidden passive child of 203720 (spell_linked_spell type 2 below: added and removed with the parent). eff0 / eff1
# attacker
# melee / ranged crit chance stored -1001 (live -1000) = crit immunity that belongs to the stance, not to the rogue.
# M2a (M1 tank ruling T-C): eff2 MOD_DAMAGE_PERCENT_TAKEN misc 127 stored -21 (-20% damage taken, all schools) [tune].
# Enforcer Stance's own three slots are full, so the clause rides this linked child (no new id, no C++).
enforcer_stance_crit_immunity_203721 = spell(
    id=203721, name='Enforcer Stance Crit Immunity', school=School.NORMAL,
    attributes=_ATTR0_PASSIVE | _ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_ATTACKER_MELEE_CRIT_CHANCE, base_points=-1001,
               implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_ATTACKER_RANGED_CRIT_CHANCE, base_points=-1001,
               implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=-21,
               misc_value=_MISC_ALL_SCHOOLS, implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_DEFENSIVE_STANCE,
    notes='RG0b A1, shared doc "Enforcer Stance": hidden passive child of 203720 (spell_linked_spell type 2). eff0 / '
          'eff1 '
          'attacker melee / ranged crit chance -1001 (live -1000) = immune to melee and ranged crits, only while in '
          'the '
          'stance. DK Blood Presence child 203000 clone: AttributesEx2 0x1 + AttributesEx3 0x100000 so it follows the '
          'parent through death, SpellLevel 1, family 8 with no bits, no SkillLineAbility. M2a (M1 T-C ruling): eff2 '
          'MOD_DAMAGE_PERCENT_TAKEN misc 127 stored -21 (-20% damage taken) [tune]; Enforcer Stance quotes it as '
          '$203721s3.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE,
        'EquippedItemClass': -1,
        'SpellLevel': 1,
        'CastingTimeIndex': 1,
        'AttributesEx2': 0x1,
        'AttributesEx3': _ATTR3_ALLOW_AURA_WHILE_DEAD,
        'Description_Lang_enUS': 'You are immune to critical strikes from melee and ranged attacks. Damage taken '
                                 'reduced by $s3%.',
    },
)

# ---- Enforcer Stance 203720 ----
# Not passive, not a form (A18): a plain aura that right-clicks off. Off the GCD (no StartRecovery), RecoveryTime 1000
# with
# no category (cooldown shared with nothing, like Defensive Stance's 1 s). AttributesEx 0x20 keeps Stealth,
# AttributesEx3
# 0x100000 survives death (Blood Presence precedent). Attributes 0x29050010 = Defensive Stance 71's. eff0 aura 142 misc
# 1
# stored 399 (+400% armor from items; M2a, was 79 / +80%), eff1 aura 10 misc 127 stored 104 (+105% threat; M2a
# tried 149 / +150%, reverted 2026-10-28), eff2 aura 79 misc 127 stored -11
# (-10% damage done). custom_attr 0x08000000 (POSITIVE_EFF2, brief C6): the negative aura 79 on eff2 would make the buff
# a debuff. U2: with the hidden 29% reduction (Rogue Passive 21184) +105% nets about x1.46, so Enforcer links "Tank
# Class
# Passive Threat" 57340 (+43%) like every tank aura, total x2.08 = Defensive Stance / Bear / Blood Presence parity.
# M2a (M1 tank rulings): threat stays +105% (+150% tried and reverted: the tank sim counted no damage threat, and the
# rogue's real threat per damage was the highest of the tanks); -20% damage taken rides the linked child 203721
# (eff2), every slot here being in use.
enforcer_stance_203720 = spell(
    id=203720, name='Enforcer Stance', school=School.NORMAL,
    attributes=0x29050010,
    cast_time_ms=0, cooldown_ms=1000, category_cooldown_ms=0, category=0,
    power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_BASE_RESISTANCE_PCT, base_points=399,
               misc_value=_MISC_ARMOR, implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_THREAT, base_points=104,
               misc_value=_MISC_ALL_SCHOOLS, implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=-11,
               misc_value=_MISC_ALL_SCHOOLS, implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_DEFENSIVE_STANCE,
    notes='RG0b A1, shared doc "Enforcer Stance" (Known-hard 1, U2, C6): the rogue tank stance, trains at 10 '
          '(SpellLevel '
          '10). eff0 MOD_BASE_RESISTANCE_PCT misc 1 stored 79 (+80% armor from items), eff1 MOD_THREAT stored 104 '
          '(+105%), eff2 MOD_DAMAGE_PERCENT_DONE stored -11 (-10%) [tune]. Off the GCD, RecoveryTime 1000, Category 0, '
          'instant, self, infinite, no cost. Attributes 0x29050010 (Defensive Stance 71), AttributesEx 0x20 (does not '
          'break '
          'Stealth), AttributesEx3 0x100000 (survives death), EquippedItemClass -1. Crit immunity = the 203721 child '
          '(linked type 2); 57340 Tank Class Passive Threat linked for x2.08 total (U2). custom_attr 0x08000000. Stock '
          'Defensive Stance icon 276, no visual (V stage). No family bits. M2a (M1 tank rulings T-C + threat): armor '
          'stored 79 -> 399 (+400%), threat kept at stored 104 (+105%; +150% tried and reverted), and the new -20% '
          'damage taken clause on the linked child 203721 eff2 (quoted as $203721s3).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE,
        'EquippedItemClass': -1,
        'SpellLevel': _ENFORCER_LEVEL,
        'BaseLevel': _ENFORCER_LEVEL,
        'CastingTimeIndex': 1,
        'AttributesEx': _ATTR1_ALLOW_WHILE_STEALTHED,
        'AttributesEx3': _ATTR3_ALLOW_AURA_WHILE_DEAD,
        'Description_Lang_enUS': 'A tanking stance. You are immune to critical strikes from melee and ranged attacks, '
                                 'armor from your items is increased by $s1%, damage taken is reduced by '
                                 '$203721s3% and you generate more threat. Your damage dealt is reduced by $s3%. '
                                 'Lasts until cancelled.',
        'AuraDescription_Lang_enUS': 'Immune to critical strikes from melee and ranged attacks. Armor and threat '
                                     'increased. Damage taken and damage dealt reduced.',
    },
)
linked_spell(enforcer_stance_203720.id, enforcer_stance_crit_immunity_203721.id, 2,
             comment='Enforcer Stance - crit immunity child (RG0b)')
# U2: every tank aura links "Tank Class Passive Threat" 57340; the remover mirrors the DK one.
linked_spell(enforcer_stance_203720.id, 57340, 2, comment='Enforcer Stance - Tank Class Passive Threat (RG0b, U2)')
linked_spell(-enforcer_stance_203720.id, -57340, 0,
             comment='Enforcer Stance - remove Tank Class Passive Threat (RG0b, U2)')
custom_attr(enforcer_stance_203720, _CUSTOM_ATTR_POSITIVE_EFF2)

# ---- Insult 203722 ----
# Taunt 355's frame (eff0 ATTACK_ME, eff1 MOD_TAUNT 3 s, Category 82 / 8000 ms off the GCD, shared with the other
# taunts, user
# ruling) with the Defensive Stance requirement replaced by CasterAuraSpell 203720 (the server enforces it in
# CheckCast).
# Range 20 yd, no cost, Taunt's icon and visual, debuff text "Taunted.". No family bits.
insult_203722 = spell(
    id=203722, name='Insult', school=School.NORMAL,
    attributes=327696, category=82,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=8000,
    power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=20.0, duration_ms=3000,
    effects=[
        Effect(type=_EFFECT_ATTACK_ME, die_sides=0, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_TAUNT, die_sides=0,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_TAUNT,
    notes='RG0b A1, shared doc "Insult" (Known-hard 2): Taunt 355\'s frame, 20 yd, 3 s, off the GCD, no cost, Category '
          '82 '
          '/ 8000 ms (shared with Taunt, Growl, Dark Command, Death Grip), CasterAuraSpell 203720 (usable only in '
          'Enforcer '
          'Stance; client greying unconfirmed, playtest row). SpellLevel 10. Taunt\'s icon 24 and visual 34. No family '
          'bits.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE,
        'EquippedItemClass': -1,
        'SpellLevel': _ENFORCER_LEVEL,
        'BaseLevel': _ENFORCER_LEVEL,
        'CastingTimeIndex': 1,
        'CasterAuraSpell': enforcer_stance_203720.id,
        'AttributesEx2': 67108864,
        'AttributesEx4': 2048,
        'AttributesEx6': 8388608,
        'DefenseType': 1,
        'PreventionType': 1,
        'SpellVisualID_1': _SV_TAUNT,
        'Description_Lang_enUS': 'Taunt the target, forcing it to attack you. Usable only in Enforcer Stance.',
        'AuraDescription_Lang_enUS': 'Taunted.',
    },
)

# ---- Ghostly Veil 203723 ----
# The buff Ghostly Strike (14278, rogue_spells.py) puts on the rogue through its TRIGGER_SPELL effect (brief C5: the
# trigger
# fires in the launch phase, so the Veil lands on every cast, hit or miss). Aura 49 MOD_DODGE_PERCENT stored 9 (+10%), 5
# charges, no timer (U4), a recast resets to 5 (native). spell_proc: taken melee auto attack | taken melee-class spell,
# hit
# mask "hit or avoided" 0x2477, spell_type_mask 0 and spell_phase_mask 0 (a taken-only row ignores the phase), chance
# 100;
# every attack taken, hit or avoided, uses one charge, shown as the stack count.
ghostly_veil_203723 = spell(
    id=203723, name='Ghostly Veil', school=School.NORMAL,
    attributes=0, category=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DODGE_PERCENT, base_points=9,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_GHOSTLY_STRIKE,
    notes='RG0b A1, shared doc "Ghostly Strike" (Known-hard 3, U4, brief C5): positive aura 49 MOD_DODGE_PERCENT '
          'stored 9 '
          '(+10%), ProcCharges 5, infinite duration (charges only), self, a visible buff, Ghostly Strike\'s icon 596. '
          'spell_proc: flags 0x28, type mask 0, phase mask 0, hit mask 0x2477 (hit or avoided), chance 100, charges 5, '
          'no '
          'cooldown. No family bits. SpellLevel 10.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE,
        'EquippedItemClass': -1,
        'SpellLevel': _ENFORCER_LEVEL,
        'CastingTimeIndex': 1,
        'ProcCharges': 5,
        'Description_Lang_enUS': 'Increases your dodge chance by $s1% for your next $n melee attacks taken.',
        'AuraDescription_Lang_enUS': 'Dodge chance increased.',
    },
)
procs_on(
    ghostly_veil_203723, proc_flags=0x28, spell_type_mask=0, spell_phase_mask=0, hit_mask=0x2477, chance=100.0,
    charges=5, cooldown_ms=0,
)
scripted_by(ghostly_veil_203723, 'spell_rog_ghostly_veil')   # WP-R F1: the owner's own events never burn a charge

# ---- Shroud of Concealment 203724 ----
# P0 204374's row (a plain MOD_STEALTH aura on the raid area, so a member who breaks it does not get it back) at
# SpellLevel
# 28: base 139 + 5 per level at BaseLevel 28 equals Stealth 1784's value (4 + 5 per level at level 1) at every level. 15
# s,
# RecoveryTime 360000 (6 min, Cooldown Haste applies), GCD 133 / 1000, usable only while stealthed (ONLY_STEALTHED +
# Stances
# FORM_STEALTH) and does not break the caster's Stealth (AttributesEx 0x20). Stealth's AuraInterruptFlags 0x23C04,
# visual 184.
shroud_of_concealment_203724 = spell(
    id=203724, name='Shroud of Concealment', school=School.NORMAL,
    attributes=_ATTR0_ONLY_STEALTHED, category=0,
    cast_time_ms=0, cooldown_ms=360000, category_cooldown_ms=0,
    power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, radius_yards=30.0, duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=16, base_points=139, points_per_level=5.0,
               implicit_target_a=_TARGET_UNIT_CASTER_AREA_RAID, radius_yards=30.0),
    ],
    spell_icon_id=_ICON_STEALTH,
    notes='RG0b A1, shared doc "Shroud of Concealment" (Known-hard 4, P0 204374): trains at 28 (SpellLevel / BaseLevel '
          '28). '
          'eff0 APPLY_AURA MOD_STEALTH (16) on TARGET_UNIT_CASTER_AREA_RAID 30 yd, base 139 + 5 per level (= '
          'Stealth\'s '
          'value at every level), 15 s. RecoveryTime 360000, GCD 133 / 1000. Attributes ONLY_STEALTHED 0x20000, '
          'Stances '
          '0x20000000, AttributesEx 0x20, AuraInterruptFlags 0x23C04, Stealth icon 250 and visual 184. No d0 stealth '
          'bit '
          'and no family bits.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE,
        'EquippedItemClass': -1,
        'SpellLevel': _SHROUD_LEVEL,
        'BaseLevel': _SHROUD_LEVEL,
        'CastingTimeIndex': 1,
        'StartRecoveryCategory': 133,
        'StartRecoveryTime': 1000,
        'AttributesEx': _ATTR1_ALLOW_WHILE_STEALTHED,
        'ShapeshiftMask': _FORM_STEALTH_MASK,
        'AuraInterruptFlags': _STEALTH_AURA_INTERRUPT_FLAGS,
        'SpellVisualID_1': _SV_STEALTH,
        'Description_Lang_enUS': 'Extend a cloak that shrouds party and raid members within $a1 yards in shadows, '
                                 'providing '
                                 'stealth for $d. Usable only while stealthed.',
        'AuraDescription_Lang_enUS': 'Hidden in shadows.',
    },
)

# ---- Shiv 203725 ----
# Sinister Strike 1752's frame (not stock Shiv 5938's: brief C3/C9 - 5938's Ex3 0x1070000 suppresses caster procs and
# its
# Ex2 has CANT_CRIT, so the new Shiv's strike can roll the non-Lethal poison and crit): any melee weapon main hand,
# melee
# range, 20 energy, 30 s cooldown, GCD 133 / 1000, d0 b29 (stock Shiv's identity). eff0 WEAPON_PERCENT_DAMAGE
# weapon_potency
# 100, eff1 ADD_COMBO_POINTS. spell_rog_shiv_rework applies every held Lethal poison at 100%
# (Rogue::ApplyLethalPoisons);
# the strike itself rolls no Lethal poison (U3, guard rule 3a'' in PoisonRollAllowed). No flat part, so unnormalized.
shiv_203725 = spell(
    id=203725, name='Shiv', school=School.NORMAL,
    attributes=327696, category=0,
    cast_time_ms=0, cooldown_ms=30000, category_cooldown_ms=0,
    power_type=PowerType.ENERGY, mana_cost=20, mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=100.0,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_SHIV,
    notes='RG0b A1, shared doc "Shiv" (Known-hard 5, U3, U6, brief C9): the reworked Shiv on a new id (stock 5938 '
          'stays '
          'unbound). Trains at 50 (SpellLevel 50). Sinister Strike 1752\'s frame: Attributes 327696, AttributesEx '
          '134218240 (0x8000200), AttributesEx3 0x400, DefenseType 2, PreventionType 2, FacingCasterFlags 1, melee '
          'range, '
          'EquippedItemClass 2 / subclass 0x2A5F3, ProcChance 101. 20 energy, 30 s cooldown (Cooldown Haste applies), '
          'GCD '
          '133 / 1000, family d0 b29 (m.SHIV), icon 1834, visual 8056. eff0 weapon_potency 100, eff1 ADD_COMBO_POINTS. '
          'Script spell_rog_shiv_rework (AfterHit: ApplyLethalPoisons).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE,
        'SpellClassMask_1': m.SHIV,
        'SpellClassMask_3': m.DIRECT_BUILDER_GROUP,   # S1 d2 b19
        'EquippedItemClass': _ITEM_CLASS_WEAPON,
        'EquippedItemSubclass': _ANY_MELEE_WEAPON,
        'SpellLevel': _SHIV_LEVEL,
        'BaseLevel': _SHIV_LEVEL,
        'CastingTimeIndex': 1,
        'DefenseType': 2,
        'PreventionType': 2,
        'FacingCasterFlags': 1,
        'RangeIndex': 2,                     # stock Melee Range row, as Sinister Strike 1752
        'ProcChance': 101,
        'StartRecoveryCategory': 133,
        'StartRecoveryTime': 1000,
        'AttributesEx': _ATTR1_SHIV,
        'AttributesEx3': _ATTR3_SHIV,
        'SpellVisualID_1': _SV_SHIV,
        'Description_Lang_enUS': 'Attack with your main hand weapon for $s1% weapon damage and apply each of your '
                                 'Lethal '
                                 'poisons to the target. Awards $s2 combo $lpoint:points;.',
    },
)
scripted_by(shiv_203725, 'spell_rog_shiv_rework')

# ---- Ambush Teleport 203726 ----
# Hidden helper cast (triggered) by spell_rog_ambush from Ambush 8676's BeforeCast when the rogue is stealthed and out
# of melee
# range: the stock 36563 teleport effect (TELEPORT_UNITS, A 1 / B 65 DEST_TARGET_BACK, radius index 7), Shadowstep's
# visual
# 8262 and AttributesEx 0x420. 50000 yd range so the script cast is not range-checked (bug 570). P0 204372's row.
ambush_teleport_203726 = spell(
    id=203726, name='Ambush Teleport', school=School.NORMAL,
    attributes=_ATTR0_DO_NOT_DISPLAY, category=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    power_type=PowerType.ENERGY, mana_cost=0, mana_cost_pct=0,
    range_yards=_SCRIPT_CAST_RANGE,
    effects=[
        Effect(type=_EFFECT_TELEPORT_UNITS, die_sides=0, implicit_target_a=_TARGET_UNIT_CASTER,
               implicit_target_b=_TARGET_DEST_TARGET_BACK),
    ],
    spell_icon_id=_ICON_SHADOWSTEP,
    notes='RG0b A1, shared doc "Ambush" (Known-hard 6, P0 204372): hidden helper (Attributes 0x80) cast triggered by '
          'spell_rog_ambush. eff0 TELEPORT_UNITS A 1 / B 65 (behind the target), EffectRadiusIndex_1 7, AttributesEx '
          '0x420, '
          'Shadowstep visual 8262, range 50000 yd, no GCD, no cost, no family bits.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_ROGUE,
        'EquippedItemClass': -1,
        'CastingTimeIndex': 1,
        'AttributesEx': _ATTR1_SHADOWSTEP,
        'EffectRadiusIndex_1': _TELEPORT_RADIUS_INDEX,
        'SpellVisualID_1': _SV_SHADOWSTEP_TELEPORT,
        'Description_Lang_enUS': 'Teleports you behind the target.',
    },
)

# SkillLineAbility 30790-30793 (U9): Enforcer Stance and Insult on Combat (38, the tank spec), Shroud next to Stealth on
# Subtlety (39), the new Shiv on 38 (stock Shiv's line). Rogue class mask 8, AcquireMethod 0 (trained). The trainer rows
# are
# rogue_trainers.py's; Ghostly Strike, Fan of Knives and Deadly Throw keep their stock SLA rows.
for _sla_id, _skill, _spell in (
    (30790, _SKILL_COMBAT, enforcer_stance_203720), (30791, _SKILL_COMBAT, insult_203722),
    (30792, _SKILL_SUBTLETY, shroud_of_concealment_203724), (30793, _SKILL_COMBAT, shiv_203725),
):
    skill_line_ability(id=_sla_id, skill_line=_skill, spell_id=_spell.id, class_mask=_CLASS_MASK_ROGUE,
                       min_skill_line_rank=1, acquire_method=0)
