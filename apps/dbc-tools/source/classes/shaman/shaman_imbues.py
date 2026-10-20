"""
Shaman - SH0a imbue system: the new child / attack / Stoneskin spells, the imbue spell_group, the spell_proc rows of the
five imbue auras, every script binding of the imbue + Stoneskin scripts, the retired stock bindings, and the Stoneskin
script numbers.

Source of truth: docs/reworks/shaman-shared-rework.md (Imbues, Rockbiter, Stoneskin, Flametongue, Frostbrand, Windfury,
Earthliving), .agents/plans/shaman-rework/shaman-rework.SH0a-WP-BRIEF.md (id map, script table, decisions 1 and 10),
SH0-HANDOFF.md (family bits, potency table, lessons L1-L18), P0-REPORT section 3 spike 3 (the imbue shape and the
spell_proc SpellPhaseMask lesson).

Ids (spell block 202200-202259, brief id map): 202200 Rockbiter tank aura child, 202201 Frostbrand proc child, 202202
Flametongue Attack, 202203 Frostbrand Attack, 202204 / 202205 Windfury Attack main hand / off hand, 202206 Stoneskin.
The five imbue auras themselves (8017, 8024, 8033, 8232, 51730) are rewritten in place by shaman_spells.py (A1); this file
only references them by bare id (spell_group, spell_proc, scripted_by). The Attunement bindings are shaman_attunements.py's.

Conventions: EquippedItemClass -1 on every row (L1); the hidden children are passive + DO_NOT_DISPLAY with
AttributesEx3 ALLOW_AURA_WHILE_DEAD and AttributesEx2 ALLOW_DEAD_TARGET so they follow their parent through death (L5)
and carry no family bits (FAMILY-BITS 4.3); the triggered attacks carry their own family bit (d0 b21 / b24 / b23) and no
NOT_A_PROC (a triggered spell without it triggers no other aura's procs, B4/B6); every non-self triggered helper has
range_yards=50000.0 (L6); every potency row sets SpellLevel (the generator owns BaseLevel / MaxLevel); aura texts are
number-free and tooltips are the shared doc verbatim.
"""

from lib.dsl import AuraType, Effect, EffectType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import (
    const, procs_on, remove_spell_proc, scripted_by, spell, spell_group, spell_group_rule, unbind_script,
)

from . import _masks as m

# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h) ----
_SPELLFAMILY_SHAMAN = 11
_ATTR0_PASSIVE = 0x40
_ATTR0_DO_NOT_DISPLAY = 0x80
_ATTR0_DO_NOT_SHEATH = 0x40000
_ATTR2_ALLOW_DEAD_TARGET = 0x1
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000  # FT / FB Attacks. NOT the no-proc guard: that is "triggered with no NOT_A_PROC"
# (SpellAuras.cpp GetProcEffectMask); this bit is only a belt-and-braces marker.
_ATTR3_ALLOW_AURA_WHILE_DEAD = 0x100000
_ATTR3_REQUIRES_OFF_HAND_WEAPON = 0x1000000  # makes Spell::m_attackType OFF_ATTACK for a melee-class spell

# ---- Spell.dbc values ----
_DMG_MAGIC = 1   # the column the DSL calls DefenseType: SPELL_DAMAGE_CLASS_MAGIC
_DMG_MELEE = 2   # SPELL_DAMAGE_CLASS_MELEE
_AURA_MOD_ATTACKER_MELEE_CRIT_CHANCE = 187
_AURA_MOD_ATTACKER_RANGED_CRIT_CHANCE = 188
_MISC_ALL_SCHOOLS = 127
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6

# spell_proc masks (src/server/game/Spells/SpellMgr.h)
_PROC_DONE_MELEE_AUTO_ATTACK = 0x4
_PROC_DONE_SPELL_MELEE_DMG_CLASS = 0x10
_PROC_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x4000
_PROC_SPELL_TYPE_DAMAGE = 0x1
_PROC_SPELL_TYPE_HEAL = 0x2
_PROC_SPELL_PHASE_HIT = 0x2
# Every melee hit, either hand, auto attack or ability. A melee-class spell flag needs a phase (P0 202766).
_MELEE_HIT_PROC_FLAGS = _PROC_DONE_MELEE_AUTO_ATTACK | _PROC_DONE_SPELL_MELEE_DMG_CLASS

# Earth Shock's identity bit (stock 8042 SpellClassMask_1 1048576, d0 b20): the Rockbiter threat modifier reads it.
_EARTH_SHOCK_D0 = 0x100000

# Stock icons (the analog's SpellIconID): Flametongue 679, Frostbrand 681, Windfury Wind Shear-style 220, Stoneskin
# Totem buff 8072 690. The Rockbiter child takes 690, not 688: a family-11 DUMMY with icon 688 at effect 0 is the
# "Lava Lash +25% per Flametongue" hardcode (SpellEffects.cpp, H6 hazard), so nothing of ours carries 688.
_ICON_FLAMETONGUE = 679
_ICON_FROSTBRAND = 681
_ICON_WINDFURY = 220
_ICON_STONESKIN = 690

# Stock visuals of the analog hit spells: Flametongue Attack 10444, Frostbrand Attack 8034, Windfury Attack 25504.
_SV_FLAMETONGUE_ATTACK = 8763
_SV_FROSTBRAND_ATTACK = 13
_SV_WINDFURY_ATTACK = 8251


def _hidden_child_raw(description, **extra):
    """A hidden passive child of an imbue (L1, L5): no family bits, the parent's family set, EquippedItemClass -1."""
    raw = {
        'SpellClassSet': _SPELLFAMILY_SHAMAN,
        'EquippedItemClass': -1,
        'SpellLevel': 1,
        'CastingTimeIndex': 1,
        'AttributesEx2': _ATTR2_ALLOW_DEAD_TARGET,
        'AttributesEx3': _ATTR3_ALLOW_AURA_WHILE_DEAD,
        'Description_Lang_enUS': description,
    }
    raw.update(extra)
    return raw


# =====================================================================================================================
# Hidden children (applied and removed with their parent imbue by spell_sha_imbue)
# =====================================================================================================================

# Rockbiter (shared doc "Rockbiter"): "You are immune to critical strikes from melee and ranged attacks" + "Under Rockbiter,
# Earth Shock generates double threat (+100%)". The immunity is the two attacker-crit auras at -1001 (stored; live -1000, far
# past any crit chance), the threat is a SPELLMOD_THREAT op 2 +100% scoped to Earth Shock's d0 b20 on effect index 2 (letter
# C = effect 3, number 1 = dword 0, README classmask gotcha). H3 (user ruling 2026-10-19): this compounds with Rockbiter's
# own +100% general threat (8017 eff1) to 4x base on Earth Shock, built as written. The child carries no family bits of its
# own (it is a modifier, never a modified spell).
rockbiter_tank_202200 = spell(
    id=202200, name='Rockbiter Tank Aura', school=School.NATURE,
    attributes=_ATTR0_PASSIVE | _ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_ATTACKER_MELEE_CRIT_CHANCE, base_points=-1001,
               implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_ATTACKER_RANGED_CRIT_CHANCE, base_points=-1001,
               implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=int(SpellModOp.THREAT),
               base_points=99, implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_STONESKIN,
    notes='SH0a A3, shared doc "Rockbiter": hidden passive child of 8017 (spell_sha_imbue applies / removes it). eff0 aura 187 '
          'and eff1 aura 188 (attacker melee / ranged crit chance) -1001 = crit immunity; eff2 ADD_PCT_MODIFIER '
          'SPELLMOD_THREAT op 2 +100% (stored 99) scoped to Earth Shock d0 b20 through EffectSpellClassMaskC_1 (H3: '
          'compounds with 8017 eff1 +100% to 4x base). No family bits; AttributesEx3 0x100000 + AttributesEx2 0x1 so it '
          'follows the parent through death.',
    raw_overrides=_hidden_child_raw(
        'Rockbiter: immune to critical strikes, and Earth Shock generates more threat.',
        EffectSpellClassMaskC_1=_EARTH_SHOCK_D0,
    ),
)

# Frostbrand (shared doc "Frostbrand"): "Your melee hits have a 15% chance to deal additional Frost damage and grant you 1
# charge of Maelstrom Weapon". A flat percent proc: the spell_proc row below carries 15 (Proc Chance multiplies it natively).
# The DUMMY effect is the proc carrier; spell_sha_frostbrand_proc casts the Frostbrand Attack from it.
frostbrand_proc_202201 = spell(
    id=202201, name='Frostbrand Proc', school=School.FROST,
    attributes=_ATTR0_PASSIVE | _ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=0,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FROSTBRAND,
    notes='SH0a A3, shared doc "Frostbrand": hidden passive DUMMY proc child of 8033 (spell_sha_imbue applies / removes it). '
          'spell_proc below: melee hits (flags 0x14), SpellPhaseMask HIT, 15% (Proc Chance applies natively). No family bits. '
          'AttributesEx3 0x100000 + AttributesEx2 0x1 so it follows the parent through death.',
    raw_overrides=_hidden_child_raw('Frostbrand: your melee hits can deal additional Frost damage.'),
)
procs_on(
    frostbrand_proc_202201, proc_flags=_MELEE_HIT_PROC_FLAGS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
    spell_phase_mask=_PROC_SPELL_PHASE_HIT, chance=15,
)


# =====================================================================================================================
# Triggered hits (never player-cast; no SkillLineAbility)
# =====================================================================================================================

# Flametongue (shared doc "Flametongue"): "8 potency per 1 sec of weapon speed". eff0 carries the 8 potency (T 1500, Fire,
# direct); eff1 is a DUMMY that carries the hitting hand's speed in ms: the proc script casts this spell with
# SPELLVALUE_BASE_POINT1 = weapon GetAttackTime(att), and spell_sha_flametongue_attack scales the hit by ms / 1000.
# Stored 999 = live 1000 ms, so a bare cast reads "one second of weapon speed" = exactly 8 potency.
# AttributesEx3 0x10000: rolls no procs ("The Fire damage is a triggered hit and rolls no procs"). No NOT_A_PROC.
flametongue_attack_202202 = spell(
    id=202202, name='Flametongue Attack', school=School.FIRE, attributes=_ATTR0_DO_NOT_SHEATH,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=8.0, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.DUMMY, base_points=999, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_FLAMETONGUE,
    notes='SH0a A3, shared doc "Flametongue": the imbue hit, triggered by spell_sha_flametongue_proc (8024) on every melee hit '
          'of either hand. eff0 potency 8 Fire direct, T 1500, d0 b21. eff1 DUMMY carries the hitting hand\'s weapon speed '
          'in ms (SPELLVALUE_BASE_POINT1; stored 999 = live 1000 ms = 1 s = 8 potency when cast bare). '
          'spell_sha_flametongue_attack multiplies the hit by ms / 1000 (B4). AttributesEx 0x88, DO_NOT_SHEATH and '
          'RangeIndex as stock 10444; AttributesEx3 0x10000 (marker only; the real no-proc guard is the cast being triggered with no NOT_A_PROC, '
          'SpellAuras.cpp GetProcEffectMask).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_SHAMAN, 'SpellClassMask_1': m.FLAMETONGUE_ATTACK, 'DefenseType': _DMG_MAGIC,
        'EquippedItemClass': -1, 'SpellLevel': 10, 'CastingTimeIndex': 1, 'AttributesEx': 0x88,
        'AttributesEx3': _ATTR3_SUPPRESS_CASTER_PROCS, 'SpellVisualID_1': _SV_FLAMETONGUE_ATTACK,
        'Description_Lang_enUS': 'Deals {pot1} Fire damage, scaled by the speed of the weapon that hit.',
    },
)

# Frostbrand (shared doc "Frostbrand"): "Frost damage per proc 20 potency". Triggered by spell_sha_frostbrand_proc. The stock
# 8034 slow is not part of the rework text and is not built.
frostbrand_attack_202203 = spell(
    id=202203, name='Frostbrand Attack', school=School.FROST, attributes=_ATTR0_DO_NOT_SHEATH,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=20.0, potency_kind='direct', time_basis_ms=1500,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_FROSTBRAND,
    notes='SH0a A3, shared doc "Frostbrand": the 15% proc hit, triggered by spell_sha_frostbrand_proc (child 202201). Potency '
          '20 Frost direct, T 1500, d0 b24. Stock 8034\'s slow dropped (not in the rework text). AttributesEx 0x88 as '
          'stock 8034/10444; AttributesEx3 0x10000 (marker only; the real no-proc guard is the cast being triggered with no NOT_A_PROC, '
          'SpellAuras.cpp GetProcEffectMask).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_SHAMAN, 'SpellClassMask_1': m.FROSTBRAND_ATTACK, 'DefenseType': _DMG_MAGIC,
        'EquippedItemClass': -1, 'SpellLevel': 20, 'CastingTimeIndex': 1, 'AttributesEx': 0x88,
        'AttributesEx3': _ATTR3_SUPPRESS_CASTER_PROCS, 'SpellVisualID_1': _SV_FROSTBRAND_ATTACK,
        'Description_Lang_enUS': 'Deals {pot1} Frost damage.',
    },
)

# Windfury (shared doc "Windfury"): "two extra attacks", each 100% weapon damage (weapon_potency 100, "no level scaling"),
# +20% of attack power on each by spell_sha_windfury_attack (U7). One WEAPON_PERCENT_DAMAGE effect: the weapon is the one
# Spell::m_attackType names, BASE_ATTACK for the main hand and OFF_ATTACK when AttributesEx3 REQUIRES_OFF_HAND_WEAPON
# (0x1000000) is set (Spell.cpp melee-class constructor). The equipped-item checks in Spell::CheckItems are skipped for
# EquippedItemClass -1, so "the off hand needs a weapon" is enforced by spell_sha_windfury_proc, which only casts the OH
# copy for an off-hand hit. DefenseType 2 (melee), Physical. Rolls Maelstrom Weapon later (named exception), so no
# SUPPRESS_CASTER_PROCS and no NOT_A_PROC.
windfury_attack_mh_202204 = spell(
    id=202204, name='Windfury Attack', school=School.NORMAL, attributes=_ATTR0_DO_NOT_SHEATH,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    effects=[Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=100, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_WINDFURY,
    notes='SH0a A3, shared doc "Windfury": main-hand extra attack, two per proc (spell_sha_windfury_proc). One '
          'WEAPON_PERCENT_DAMAGE effect, weapon_potency 100, d0 b23 (H7 Flurry, Spirit Weapons). BASE_ATTACK weapon. '
          'spell_sha_windfury_attack adds +20% AP. No NOT_A_PROC and no SUPPRESS_CASTER_PROCS (they roll Maelstrom Weapon).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_SHAMAN, 'SpellClassMask_1': m.WINDFURY_ATTACK, 'DefenseType': _DMG_MELEE,
        'EquippedItemClass': -1, 'SpellLevel': 30, 'CastingTimeIndex': 1, 'SpellVisualID_1': _SV_WINDFURY_ATTACK,
        'AttributesEx4': 0x00800000,  # SUPPRESS_WEAPON_PROCS: no item/enchant procs (SH0a review L4, doc rule)
        'Description_Lang_enUS': 'An extra attack with your main hand weapon for $s1% weapon damage.',
    },
)

windfury_attack_oh_202205 = spell(
    id=202205, name='Windfury Attack', school=School.NORMAL, attributes=_ATTR0_DO_NOT_SHEATH,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    effects=[Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=100, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_WINDFURY,
    notes='SH0a A3, shared doc "Windfury": off-hand extra attack, cast only for an off-hand hit. Same as 202204 with '
          'AttributesEx3 REQUIRES_OFF_HAND_WEAPON 0x1000000, which makes Spell::m_attackType OFF_ATTACK; the cast-time '
          'weapon check is skipped for EquippedItemClass -1, so spell_sha_windfury_proc is the gate (off-hand hit only).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_SHAMAN, 'SpellClassMask_1': m.WINDFURY_ATTACK, 'DefenseType': _DMG_MELEE,
        'EquippedItemClass': -1, 'SpellLevel': 30, 'CastingTimeIndex': 1, 'SpellVisualID_1': _SV_WINDFURY_ATTACK,
        'AttributesEx3': _ATTR3_REQUIRES_OFF_HAND_WEAPON,
        'AttributesEx4': 0x00800000,  # SUPPRESS_WEAPON_PROCS: no item/enchant procs (SH0a review L4, doc rule)
        'Description_Lang_enUS': 'An extra attack with your off-hand weapon for $s1% weapon damage.',
    },
)


# =====================================================================================================================
# Stoneskin (shared doc "Stoneskin")
# =====================================================================================================================

# "Each stack of Stoneskin reduces all damage you take by 1%, up to 50 stacks. Taking damage erodes your stacks." A visible
# (not passive, not consolidated) buff, applied and stacked only by scripts (Shaman::AddStoneskin) while Rockbiter is up and
# eroded by Shaman::ErodeStoneskin. CumulativeAura 50 is the StackAmount; aura 87 (damage taken %) misc 127 (all schools)
# -1 per stack, stored -2 (live -1); AuraEffect::CalculateAmount multiplies it by the stack count. Permanent duration: the
# 2 min out-of-combat timer is the shaman's (STONESKIN_OOC_MS). The buff icon is the Stoneskin Totem buff's (8072, 690).
# Not a death-surviving aura: it falls off with the shaman's death and is re-earned.
stoneskin_202206 = spell(
    id=202206, name='Stoneskin', school=School.NATURE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=0,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=_MISC_ALL_SCHOOLS,
                    base_points=-2, implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_STONESKIN,
    notes='SH0a A3, shared doc "Stoneskin": visible stacking buff, CumulativeAura (StackAmount) 50, aura 87 misc 127 stored -2 '
          '(live -1% per stack). Built by Shaman::AddStoneskin under Rockbiter, eroded by Shaman::ErodeStoneskin. No family '
          'bits, no SkillLineAbility. Icon 690 = the Stoneskin Totem buff (8072).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_SHAMAN, 'EquippedItemClass': -1, 'SpellLevel': 1, 'CastingTimeIndex': 1,
        'CumulativeAura': 50,
        'Description_Lang_enUS': 'Each stack of Stoneskin reduces all damage you take by 1%, up to 50 stacks. '
                                 'Taking damage erodes your stacks.',
        'AuraDescription_Lang_enUS': 'Damage taken reduced. Taking damage erodes this effect.',
    },
)

# Script numbers (docs/potency-system.md tier 3; generated into ShamanData::). The shared doc's [tune]/[fixed] values.
STONESKIN_EARTH_SHOCK = const('STONESKIN_EARTH_SHOCK', 15, 'Stoneskin stacks Earth Shock grants, once per cast [tune].')
STONESKIN_STORMSTRIKE = const('STONESKIN_STORMSTRIKE', 5, 'Stoneskin stacks Stormstrike grants [tune].')
STONESKIN_LAVA_LASH = const('STONESKIN_LAVA_LASH', 5, 'Stoneskin stacks Lava Lash grants [tune].')
STONESKIN_CHAIN_LIGHTNING = const('STONESKIN_CHAIN_LIGHTNING', 1, 'Stoneskin stacks Chain Lightning grants per target hit [tune].')
STONESKIN_MAX = const('STONESKIN_MAX', 50, 'Stoneskin stack cap [fixed]; also spell 202206\'s CumulativeAura.')
STONESKIN_OOC_MS = const('STONESKIN_OOC_MS', 120000, 'Out-of-combat time before the Stoneskin stacks fall off, ms [fixed].')


# =====================================================================================================================
# Imbue exclusivity, proc rows
# =====================================================================================================================

# Shared doc "Imbues": "imbues active at once 1". EXCLUSIVE (rule 1) on the five imbue auras: a new imbue evicts the old.
spell_group(1251, 8017, 8024, 8033, 8232, 51730)
spell_group_rule(1251, stack_rule=1, description='Shaman imbues: one at a time')

# spell_proc rows of the imbue auras (the aura's DUMMY effect is the carrier; the script casts the hit). Every melee-class
# spell flag needs SpellPhaseMask (P0 202766): HIT (2). Chance in the row once; the Proc Chance stat multiplies it natively.
# SpellTypeMask DAMAGE (1) like the stock rows: Stormstrike's own no-damage melee-class hit must not fire the imbue procs.
# Flametongue: every melee hit, either hand ("Not affected by: Proc Chance (it triggers on every hit)").
procs_on(8024, proc_flags=_MELEE_HIT_PROC_FLAGS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, chance=100)
# Windfury: 20% on a hit from either hand, no internal cooldown.
procs_on(8232, proc_flags=_MELEE_HIT_PROC_FLAGS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, chance=20, cooldown_ms=0)
# Earthliving: a direct heal landing (positive magic-class spell, heal type, HIT phase). Chance 100 here: the script rolls the
# real 20% through Shaman::RollProcChance (per target healed, owner-resolving, x (1 + Proc Chance)).
procs_on(
    51730, proc_flags=_PROC_DONE_SPELL_MAGIC_DMG_CLASS_POS, spell_type_mask=_PROC_SPELL_TYPE_HEAL,
    spell_phase_mask=_PROC_SPELL_PHASE_HIT, chance=100,
)


# =====================================================================================================================
# Script bindings (brief script table). spell_sha_attunement is shaman_attunements.py's.
# =====================================================================================================================

for _imbue in (8017, 8024, 8033, 8232, 51730):
    scripted_by(_imbue, 'spell_sha_imbue')
scripted_by(8024, 'spell_sha_flametongue_proc')
scripted_by(frostbrand_proc_202201, 'spell_sha_frostbrand_proc')
scripted_by(8232, 'spell_sha_windfury_proc')
scripted_by(windfury_attack_mh_202204, 'spell_sha_windfury_attack')
scripted_by(windfury_attack_oh_202205, 'spell_sha_windfury_attack')
scripted_by(51730, 'spell_sha_earthliving_proc')
scripted_by(flametongue_attack_202202, 'spell_sha_flametongue_attack')
for _stoneskin_source in (8042, 421, 17364, 60103):   # Earth Shock, Chain Lightning, Stormstrike, Lava Lash
    scripted_by(_stoneskin_source, 'spell_sha_stoneskin_grant')


# =====================================================================================================================
# Retired stock bindings and their orphaned spell_proc rows (exact live keys, L7)
# =====================================================================================================================

# The stock weapon-imbue passives (10400 Flametongue Weapon passive, 33757 Windfury Weapon, 51940 Earthliving Weapon
# passive) are no longer cast by anything; the new imbue auras replace them. 33757's key is positive in the live table,
# the other two are rank-chain keys (-<id>).
unbind_script(-10400, 'spell_sha_flametongue_weapon')
unbind_script(33757, 'spell_sha_windfury_weapon')
unbind_script(-51940, 'spell_sha_earthliving_weapon')
remove_spell_proc(-10400)
remove_spell_proc(33757)
remove_spell_proc(-51940)
