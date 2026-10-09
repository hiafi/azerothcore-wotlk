"""
Paladin - shared, non-castable spells of the seal core and the aura system (paladin-rework S1, WP-A2a).

Source of truth: .agents/plans/paladin-rework/paladin-rework.SHARED.md Part A (ids, bits), Part B
(B0 id map, B1.4-B1.6 seal passives and chance auras, B2 Primed, B4 unleashes and utility, B9 tooltip
variables) and Part C (C0, C1.4, C1.5 aura bursts), plus the user-ruling logs at the end of that file.

Declared here, in id order:
    201063-201068  Primed auras (B2)                      201081-201092  seal passives (B1.4)
    201069-201080  unleashes, ST and AoE (B4.1)           201093-201106  chance auras + utility (B1.5, B4.2)
    201160-201164  aura bursts (C1.4)                     spell_group 1211-1213, linked spells, tooltip_vars 1100-1104

Not declared here (other files own them): Judgement 201060 / Deliverance 201061, the six seals, the five
aura buttons, and every Ret / Holy / Prot spell. Spells owned elsewhere are referenced by bare id only.

Conventions (SHARED Part B common rules): every non-self helper has range_yards=50000.0 (CR1); a spell that
nothing scopes carries no family bits and no SpellClassSet; potency for every damage / heal number; the
spell-level (not effect-level) `raw_overrides` keys are the real Spell.dbc column names.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, RANGE_SELF, School
from lib.dsl.registry import (
    linked_spell, procs_on, product, scripted_by, spell, spell_group, spell_group_rule, talent_mult, tooltip_vars,
)

from . import _masks as m
from .paladin_holy_spells import concentration_tooltip


# --- Spell.dbc flag values used below (SharedDefines.h) -------------------------------------------------------
_ATTR0_DO_NOT_DISPLAY = 0x80
_ATTR0_DO_NOT_SHEATH = 0x40000  # triggered weapon strikes: no weapon-sheath animation
_ATTR0_NO_ACTIVE_DEFENSE = 0x200000
_ATTR0_AURA_IS_DEBUFF = 0x04000000
_ATTR0_NO_IMMUNITIES = 0x20000000
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x4  # paladin casts at secondary / ally targets; the area pick already did the LoS test
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000
_ATTR3_SUPPRESS_TARGET_PROCS = 0x20000
_ATTR3_ALWAYS_HIT = 0x40000

# DmgClass (the column the DSL calls DefenseType)
_DMG_NONE = 0
_DMG_MAGIC = 1
_DMG_MELEE = 2

# Effect types / aura types that the DSL enums do not name yet
_EFFECT_APPLY_AREA_AURA_PARTY = 35
_AURA_MOD_POWER_REGEN = 85  # SPELL_AURA_MOD_POWER_REGEN, misc 0 = mana
_AURA_MOD_SPEED_NOT_STACK = 171

_MISC_ALL_SCHOOLS = 127
_MISC_ALL_MAGIC = 126

# Seal icons (SHARED B0): SoC 561, SoV 2292, SoJ 307, SoL 299, SoW 206. Righteousness uses 90180, an alias of
# the stock SpellIcon 25 texture, for everything that must not carry icon 25 (Primed, passives, utility);
# the two Righteousness unleashes keep the literal seal icon 25 (the icon-25 correction only touches passives).
_ICON_SOR_ALIAS = 90180
_ICON_SOR = 25
_ICON_SOC = 561
_ICON_SOV = 2292
_ICON_SOV_DOT_ALIAS = 90182  # alias of the icon-2292 texture, so no Vengeance DoT carries icon 2292
_ICON_SOJ = 307
_ICON_SOL = 299
_ICON_SOW = 206

_HOLY = School.HOLY
_HOLY_FIRE = School.HOLY | School.FIRE  # Command
_HOLY_SHADOW = School.HOLY | School.SHADOW  # Vengeance ("Twilight")
_HOLY_FROST = School.HOLY | School.FROST  # Justice
_HOLY_ARCANE = School.HOLY | School.ARCANE  # Wisdom


def _text(description: str = "", aura: str = "") -> dict:
    """The four text-mask / enUS keys every row carries (16712190 = text present, 16712188 = blank)."""
    return {
        'Description_Lang_Mask': 16712190 if description else 16712188,
        'Description_Lang_enUS': description,
        'AuraDescription_Lang_Mask': 16712190 if aura else 16712188,
        'AuraDescription_Lang_enUS': aura,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_Mask': 16712188,
    }


def _chain(*effect_slots: int) -> dict:
    """EffectChainAmplitude_N = 1.0 for each used effect slot (1-based)."""
    return {f'EffectChainAmplitude_{n}': 1.0 for n in effect_slots}


# ===========================================================================================================
# B2 - Primed auras 201063-201068. 20 s, display stacks only (the authority is Paladin::SealState), survives
# the end of combat (no AuraInterruptFlags), not dispellable, cancellable, no family bits, no icon 25.
# One at a time: spell_group 1211 rule 1. Script: spell_pal_primed_aura.
# ===========================================================================================================

_PRIMED_TEXT = "Seal of {seal} is primed. Your next Judgement or Deliverance unleashes it, +10% per stack."


def _primed_raw(seal: str) -> dict:
    text = _PRIMED_TEXT.format(seal=seal)
    return {
        **_text(text, text), **_chain(1),
        'CastingTimeIndex': 1, 'CumulativeAura': 10, 'EquippedItemClass': -1, 'ProcChance': 101,
    }


def _primed_effect() -> Effect:
    return Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=1)


primed_righteousness_201063 = spell(
    id=201063, name='Primed: Righteousness', school=_HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=20000,
    effects=[_primed_effect()],
    spell_icon_id=_ICON_SOR_ALIAS,
    notes='paladin-rework SHARED B2/B0: Primed aura. Icon 90180 = alias of the SoR texture (Part A forbids icon 25 here).',
    raw_overrides=_primed_raw('Righteousness'),
)

primed_command_201064 = spell(
    id=201064, name='Primed: Command', school=_HOLY_FIRE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=20000,
    effects=[_primed_effect()],
    spell_icon_id=_ICON_SOC,
    notes='paladin-rework SHARED B2/B0: Primed aura.',
    raw_overrides=_primed_raw('Command'),
)

primed_vengeance_201065 = spell(
    id=201065, name='Primed: Vengeance', school=_HOLY_SHADOW,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=20000,
    effects=[_primed_effect()],
    spell_icon_id=_ICON_SOV,
    notes='paladin-rework SHARED B2/B0: Primed aura. Icon 2292 is safe here: the Judgement-of-Vengeance hardcode needs icon 2292 AND d1 0x400000, which no Primed aura carries.',
    raw_overrides=_primed_raw('Vengeance'),
)

primed_justice_201066 = spell(
    id=201066, name='Primed: Justice', school=_HOLY_FROST,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=20000,
    effects=[_primed_effect()],
    spell_icon_id=_ICON_SOJ,
    notes='paladin-rework SHARED B2/B0: Primed aura.',
    raw_overrides=_primed_raw('Justice'),
)

primed_light_201067 = spell(
    id=201067, name='Primed: Light', school=_HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=20000,
    effects=[_primed_effect()],
    spell_icon_id=_ICON_SOL,
    notes='paladin-rework SHARED B2/B0: Primed aura.',
    raw_overrides=_primed_raw('Light'),
)

primed_wisdom_201068 = spell(
    id=201068, name='Primed: Wisdom', school=_HOLY_ARCANE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=20000,
    effects=[_primed_effect()],
    spell_icon_id=_ICON_SOW,
    notes='paladin-rework SHARED B2/B0: Primed aura.',
    raw_overrides=_primed_raw('Wisdom'),
)

for _primed in (
    primed_righteousness_201063, primed_command_201064, primed_vengeance_201065,
    primed_justice_201066, primed_light_201067, primed_wisdom_201068,
):
    scripted_by(_primed, 'spell_pal_primed_aura')

spell_group(
    1211, primed_righteousness_201063, primed_command_201064, primed_vengeance_201065,
    primed_justice_201066, primed_light_201067, primed_wisdom_201068,
)
spell_group_rule(1211, stack_rule=1, description="Paladin Primed auras - one at a time")


# ===========================================================================================================
# B4.1 - unleashes 201069-201080. Instant, Speed 0 (the unleash context needs a synchronous cast), triggered,
# DmgClass MAGIC, ALWAYS_HIT, SpellLevel 1, family U (d0 0x800000) on every damaging one (the two Command
# unleashes also CU, d2 0x80000), none on Light's heals. Hybrid potency at T = 1.5. Script: spell_pal_seal_unleash
# (SpellScript + AuraScript pair).
# ===========================================================================================================

def _unleash_raw(description: str, aura: str = "", command: bool = False) -> dict:
    raw = {
        **_text(description, aura), **_chain(1),
        'AttributesEx2': _ATTR2_IGNORE_LINE_OF_SIGHT, 'AttributesEx3': _ATTR3_ALWAYS_HIT, 'CastingTimeIndex': 1,
        'DefenseType': _DMG_MAGIC, 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellClassSet': 10,
        'SpellClassMask_1': m.UNLEASH,
        'SpellLevel': 1,
    }
    if command:
        raw['SpellClassMask_3'] = m.UNLEASH_COMMAND
    return raw


def _unleash_heal_raw(description: str) -> dict:
    """Light's Renewal: no family bits, no SpellClassSet (nothing scopes it)."""
    return {
        **_text(description), **_chain(1),
        'CastingTimeIndex': 1, 'DefenseType': _DMG_MAGIC, 'EquippedItemClass': -1, 'ProcChance': 101,
        'SpellLevel': 1,
    }


def _unleash_direct(potency: float) -> Effect:
    return Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=potency, ap_potency=potency, potency_kind='direct', implicit_target_a=6)


def _unleash_dot(potency_per_tick: float) -> Effect:
    return Effect(
        type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000,
        sp_potency=potency_per_tick, ap_potency=potency_per_tick, potency_kind='periodic', implicit_target_a=6,
    )


def _unleash_heal() -> Effect:
    return Effect(type=EffectType.HEAL, sp_potency=100.0, potency_kind='heal', implicit_target_a=1)


# --- single target: "Judgement of <Seal>" --------------------------------------------------------------------

unleash_righteousness_201069 = spell(
    id=201069, name='Judgement of Righteousness', school=_HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_unleash_direct(97.5)],
    spell_icon_id=_ICON_SOR,
    notes='paladin-rework SHARED B4.1: Righteousness unleash (single target), 75/75 potency. Speed 0 and instant on purpose: the unleash context needs a synchronous cast - never give this a missile visual.'
          ' Effect 1 potency 75.0 -> 97.5 (2026-10-08, DPS balance pass, user ruling: Retribution x1.30).',
    raw_overrides=_unleash_raw('Deals {pot1} Holy damage.'),
)

unleash_command_201070 = spell(
    id=201070, name='Judgement of Command', school=_HOLY_FIRE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_unleash_direct(37.5)],
    spell_icon_id=_ICON_SOC,
    notes='paladin-rework SHARED B4.1: Command unleash (single target), 37.5/37.5 potency. Bits U + CU, no C (Purify the Unclean reads C = the passives only; Prot Improved Seal of Command scopes C | CU).',
    raw_overrides=_unleash_raw('Deals {pot1} Holy and Fire damage.', command=True),
)

unleash_vengeance_201071 = spell(
    id=201071, name='Judgement of Vengeance', school=_HOLY_SHADOW,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=15000,
    effects=[_unleash_dot(10.8)],
    spell_icon_id=_ICON_SOV_DOT_ALIAS,
    notes='paladin-rework SHARED B4.1: Vengeance unleash DoT, 9/9 per 3 s tick over 15 s (snapshots natively). Icon 90182 (alias of the 2292 texture) and no d1 0x400000, so the JoV +10%/stack hardcode never fires. The script sets canBeRecalculated = false.'
          ' Effect 1 (periodic) potency per tick 9.0 -> 10.8 (2026-10-08, DPS balance pass, user ruling: Retribution x1.20).',
    raw_overrides=_unleash_raw('Afflicts the target with Twilight damage over time.', '{pot1} Twilight damage every $t1 sec.'),
)

unleash_justice_201072 = spell(
    id=201072, name='Judgement of Justice', school=_HOLY_FROST,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_unleash_direct(60.0)],
    spell_icon_id=_ICON_SOJ,
    notes='paladin-rework SHARED B4.1: Justice unleash (single target), 60/60 potency; doubled by the script on a controlled target.',
    raw_overrides=_unleash_raw('Deals {pot1} Holy and Frost damage.'),
)

unleash_light_201073 = spell(
    id=201073, name="Light's Renewal", school=_HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[_unleash_heal()],
    spell_icon_id=_ICON_SOL,
    notes='paladin-rework SHARED B4.1: Light unleash (single target) = self heal, 100 healing potency, no damage and no family bits (so it never feeds the damaging-unleash procs).',
    raw_overrides=_unleash_heal_raw('Heals you for {pot1}.'),
)

unleash_wisdom_201074 = spell(
    id=201074, name='Judgement of Wisdom', school=_HOLY_ARCANE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_unleash_direct(58.5)],
    spell_icon_id=_ICON_SOW,
    notes='paladin-rework SHARED B4.1: Wisdom unleash (single target), 45/45 potency.'
          ' Effect 1 potency 45.0 -> 58.5 (2026-10-08, DPS balance pass, user ruling: Retribution x1.30).',
    raw_overrides=_unleash_raw('Deals {pot1} Holy and Arcane damage.'),
)

# --- AoE, one cast per target: "Deliverance of <Seal>" (the 40% is written into the numbers, no script scaler) --

unleash_righteousness_aoe_201075 = spell(
    id=201075, name='Deliverance of Righteousness', school=_HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_unleash_direct(30.0)],
    spell_icon_id=_ICON_SOR,
    notes='paladin-rework SHARED B4.1: Righteousness unleash (AoE, per target), 30/30 potency.',
    raw_overrides=_unleash_raw('Deals {pot1} Holy damage.'),
)

unleash_command_aoe_201076 = spell(
    id=201076, name='Deliverance of Command', school=_HOLY_FIRE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_unleash_direct(15.0)],
    spell_icon_id=_ICON_SOC,
    notes='paladin-rework SHARED B4.1: Command unleash (AoE, per target), 15/15 potency. Bits U + CU, no C.',
    raw_overrides=_unleash_raw('Deals {pot1} Holy and Fire damage.', command=True),
)

unleash_vengeance_aoe_201077 = spell(
    id=201077, name='Deliverance of Vengeance', school=_HOLY_SHADOW,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=15000,
    effects=[_unleash_dot(3.6)],
    spell_icon_id=_ICON_SOV_DOT_ALIAS,
    notes='paladin-rework SHARED B4.1: Vengeance unleash DoT (AoE, per target), 3.6/3.6 per 3 s tick over 15 s. Same icon / bit rules as 201071.',
    raw_overrides=_unleash_raw('Afflicts the target with Twilight damage over time.', '{pot1} Twilight damage every $t1 sec.'),
)

unleash_justice_aoe_201078 = spell(
    id=201078, name='Deliverance of Justice', school=_HOLY_FROST,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_unleash_direct(24.0)],
    spell_icon_id=_ICON_SOJ,
    notes='paladin-rework SHARED B4.1: Justice unleash (AoE, per target), 24/24 potency.',
    raw_overrides=_unleash_raw('Deals {pot1} Holy and Frost damage.'),
)

unleash_light_aoe_201079 = spell(
    id=201079, name="Light's Renewal", school=_HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[_unleash_heal()],
    spell_icon_id=_ICON_SOL,
    notes='paladin-rework SHARED B4.1: Light unleash (AoE) = self heal at full value once (effects on the caster happen once); a separate id only so the ST/AoE lookup stays uniform.',
    raw_overrides=_unleash_heal_raw('Heals you for {pot1}.'),
)

unleash_wisdom_aoe_201080 = spell(
    id=201080, name='Deliverance of Wisdom', school=_HOLY_ARCANE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_unleash_direct(18.0)],
    spell_icon_id=_ICON_SOW,
    notes='paladin-rework SHARED B4.1: Wisdom unleash (AoE, per target), 18/18 potency.',
    raw_overrides=_unleash_raw('Deals {pot1} Holy and Arcane damage.'),
)

for _unleash in (
    unleash_righteousness_201069, unleash_command_201070, unleash_vengeance_201071,
    unleash_justice_201072, unleash_light_201073, unleash_wisdom_201074,
    unleash_righteousness_aoe_201075, unleash_command_aoe_201076, unleash_vengeance_aoe_201077,
    unleash_justice_aoe_201078, unleash_light_aoe_201079, unleash_wisdom_aoe_201080,
):
    scripted_by(_unleash, 'spell_pal_seal_unleash')


# ===========================================================================================================
# B1.4 - seal passives 201081-201092. Two ids per seal: auto-attack form (plain WEAPON_PERCENT_DAMAGE) and
# ability form (adds NORMALIZED_WEAPON_DMG). DmgClass MELEE, target 6, DO_NOT_SHEATH | NO_ACTIVE_DEFENSE,
# ALWAYS_HIT, can crit, SpellLevel 1, family P (d2 0x200) + C (d2 0x400) on Command, no icon 25, Speed 0.
# Weapon potency is the raw percent. Script: spell_pal_seal_passive (all twelve).
# ===========================================================================================================

def _passive_raw(description: str, command: bool = False) -> dict:
    return {
        **_text(description),
        'AttributesEx3': _ATTR3_ALWAYS_HIT, 'CastingTimeIndex': 1, 'DefenseType': _DMG_MELEE,
        'EquippedItemClass': -1, 'ProcChance': 101, 'SpellClassSet': 10,
        'SpellClassMask_3': (m.SEAL_PASSIVE | m.SEAL_PASSIVE_COMMAND) if command else m.SEAL_PASSIVE,
        'SpellLevel': 1,
    }


def _weapon(percent: float, chain_targets: int = 0) -> Effect:
    return Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=percent, implicit_target_a=6, chain_targets=chain_targets)


def _normalized(chain_targets: int = 0) -> Effect:
    # No flat part: EffectBasePoints -1 with DieSides 1 is 0 live (the stock "empty" amount).
    return Effect(type=EffectType.NORMALIZED_WEAPON_DMG, base_points=-1, implicit_target_a=6, chain_targets=chain_targets)


_PASSIVE_ATTRIBUTES = _ATTR0_DO_NOT_SHEATH | _ATTR0_NO_ACTIVE_DEFENSE  # 0x240000

# --- auto-attack form ------------------------------------------------------------------------------------------

seal_of_righteousness_hit_201081 = spell(
    id=201081, name='Seal of Righteousness', school=_HOLY, attributes=_PASSIVE_ATTRIBUTES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_weapon(20.0)],
    spell_icon_id=_ICON_SOR_ALIAS,
    notes='paladin-rework SHARED B1.4: Seal of Righteousness passive, auto-attack form, 20% weapon (bits P). Icon 90180 not 25.',
    raw_overrides={**_passive_raw('Seal of Righteousness weapon damage.'), **_chain(1)},
)

seal_of_command_hit_201082 = spell(
    id=201082, name='Seal of Command', school=_HOLY_FIRE, attributes=_PASSIVE_ATTRIBUTES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_weapon(10.0, chain_targets=3)],
    spell_icon_id=_ICON_SOC,
    notes='paladin-rework SHARED B1.4: Seal of Command passive, auto-attack form, 10% weapon, chain 3 (the script trims it to 1 target for a multi-target source), bits P + C.',
    raw_overrides={**_passive_raw('Seal of Command weapon damage.', command=True), **_chain(1)},
)

seal_of_vengeance_hit_201083 = spell(
    id=201083, name='Seal of Vengeance', school=_HOLY_SHADOW, attributes=_PASSIVE_ATTRIBUTES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_weapon(10.0)],
    spell_icon_id=_ICON_SOV,
    notes='paladin-rework SHARED B1.4: Seal of Vengeance passive, auto-attack form, 10% weapon (bits P). Icon 2292 is safe: the JoV hardcode needs d1 0x400000 as well and a passive carries none.',
    raw_overrides={**_passive_raw('Seal of Vengeance weapon damage.'), **_chain(1)},
)

seal_of_justice_hit_201084 = spell(
    id=201084, name='Seal of Justice', school=_HOLY_FROST, attributes=_PASSIVE_ATTRIBUTES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_weapon(10.0)],
    spell_icon_id=_ICON_SOJ,
    notes='paladin-rework SHARED B1.4: Seal of Justice passive, auto-attack form, 10% weapon (bits P).',
    raw_overrides={**_passive_raw('Seal of Justice weapon damage.'), **_chain(1)},
)

seal_of_light_hit_201085 = spell(
    id=201085, name='Seal of Light', school=_HOLY, attributes=_PASSIVE_ATTRIBUTES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_weapon(5.0)],
    spell_icon_id=_ICON_SOL,
    notes='paladin-rework SHARED B1.4: Seal of Light passive, auto-attack form, 5% weapon (bits P).',
    raw_overrides={**_passive_raw('Seal of Light weapon damage.'), **_chain(1)},
)

seal_of_wisdom_hit_201086 = spell(
    id=201086, name='Seal of Wisdom', school=_HOLY_ARCANE, attributes=_PASSIVE_ATTRIBUTES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_weapon(5.0)],
    spell_icon_id=_ICON_SOW,
    notes='paladin-rework SHARED B1.4: Seal of Wisdom passive, auto-attack form, 5% weapon (bits P).',
    raw_overrides={**_passive_raw('Seal of Wisdom weapon damage.'), **_chain(1)},
)

# --- ability form (normalized weapon effect first, the weapon-percent effect deals the damage) ---------------

seal_of_righteousness_hit_normalized_201087 = spell(
    id=201087, name='Seal of Righteousness', school=_HOLY, attributes=_PASSIVE_ATTRIBUTES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_normalized(), _weapon(20.0)],
    spell_icon_id=_ICON_SOR_ALIAS,
    notes='paladin-rework SHARED B1.4: Seal of Righteousness passive, ability form (Crusader Strike shape: type 121 + type 31), 20% weapon, bits P.',
    raw_overrides={**_passive_raw('Seal of Righteousness weapon damage.'), **_chain(1, 2)},
)

seal_of_command_hit_normalized_201088 = spell(
    id=201088, name='Seal of Command', school=_HOLY_FIRE, attributes=_PASSIVE_ATTRIBUTES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_normalized(chain_targets=3), _weapon(10.0, chain_targets=3)],
    spell_icon_id=_ICON_SOC,
    notes='paladin-rework SHARED B1.4: Seal of Command passive, ability form, 10% weapon, chain 3 on BOTH effects (explicit-target selection is per effect; eff1 deals the damage, eff0 matches it so the two target lists and the script clear stay identical), bits P + C.',
    raw_overrides={**_passive_raw('Seal of Command weapon damage.', command=True), **_chain(1, 2)},
)

seal_of_vengeance_hit_normalized_201089 = spell(
    id=201089, name='Seal of Vengeance', school=_HOLY_SHADOW, attributes=_PASSIVE_ATTRIBUTES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_normalized(), _weapon(10.0)],
    spell_icon_id=_ICON_SOV,
    notes='paladin-rework SHARED B1.4: Seal of Vengeance passive, ability form, 10% weapon, bits P.',
    raw_overrides={**_passive_raw('Seal of Vengeance weapon damage.'), **_chain(1, 2)},
)

seal_of_justice_hit_normalized_201090 = spell(
    id=201090, name='Seal of Justice', school=_HOLY_FROST, attributes=_PASSIVE_ATTRIBUTES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_normalized(), _weapon(10.0)],
    spell_icon_id=_ICON_SOJ,
    notes='paladin-rework SHARED B1.4: Seal of Justice passive, ability form, 10% weapon, bits P.',
    raw_overrides={**_passive_raw('Seal of Justice weapon damage.'), **_chain(1, 2)},
)

seal_of_light_hit_normalized_201091 = spell(
    id=201091, name='Seal of Light', school=_HOLY, attributes=_PASSIVE_ATTRIBUTES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_normalized(), _weapon(5.0)],
    spell_icon_id=_ICON_SOL,
    notes='paladin-rework SHARED B1.4: Seal of Light passive, ability form, 5% weapon, bits P.',
    raw_overrides={**_passive_raw('Seal of Light weapon damage.'), **_chain(1, 2)},
)

seal_of_wisdom_hit_normalized_201092 = spell(
    id=201092, name='Seal of Wisdom', school=_HOLY_ARCANE, attributes=_PASSIVE_ATTRIBUTES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[_normalized(), _weapon(5.0)],
    spell_icon_id=_ICON_SOW,
    notes='paladin-rework SHARED B1.4: Seal of Wisdom passive, ability form, 5% weapon, bits P.',
    raw_overrides={**_passive_raw('Seal of Wisdom weapon damage.'), **_chain(1, 2)},
)

for _passive in (
    seal_of_righteousness_hit_201081, seal_of_command_hit_201082, seal_of_vengeance_hit_201083,
    seal_of_justice_hit_201084, seal_of_light_hit_201085, seal_of_wisdom_hit_201086,
    seal_of_righteousness_hit_normalized_201087, seal_of_command_hit_normalized_201088,
    seal_of_vengeance_hit_normalized_201089, seal_of_justice_hit_normalized_201090,
    seal_of_light_hit_normalized_201091, seal_of_wisdom_hit_normalized_201092,
):
    scripted_by(_passive, 'spell_pal_seal_passive')


# ===========================================================================================================
# B1.5 - chance effects. A spell has one spell_proc row, so the 20% effects ride on hidden auras linked to the
# seal (linked_spell type 2: applied and removed in lockstep). Hidden aura: PROC_TRIGGER_SPELL -> effect spell,
# target 1, infinite, DO_NOT_DISPLAY, no bits. The rows (procs_on) are 20% HIT-phase on the seal proc flags;
# Proc Chance applies automatically. Script: spell_pal_seal_chance_aura (CheckProc requires the matching active
# seal; 201094 / 201095 prevent the default action and cast their effect spell with a script-supplied amount).
# ===========================================================================================================

def _chance_aura_raw(description: str) -> dict:
    return {
        **_text(description), **_chain(1),
        'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101,
    }


seal_of_justice_stun_chance_201093 = spell(
    id=201093, name='Seal of Justice', school=_HOLY_FROST, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, implicit_target_a=1, trigger_spell=201096)],
    spell_icon_id=_ICON_SOJ,
    notes='paladin-rework SHARED B1.5: hidden chance aura linked to Seal of Justice 20164; 20% to cast the 0.5 s stun 201096 (creatures only, no boss, not stun-immune, no Justice Recovery - all in the script CheckProc). The default action (cast 201096 at the proc target) is wanted here. Optional CU_AURA_CANNOT_BE_SAVED not declared (SHARED: WP-B must verify the relink in game first); the CheckProc active-seal test covers a stale saved aura.',
    raw_overrides=_chance_aura_raw('Your melee attacks have a chance to stun the target.'),
)

seal_of_light_heal_chance_201094 = spell(
    id=201094, name='Seal of Light', school=_HOLY, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, implicit_target_a=1, trigger_spell=201097)],
    spell_icon_id=_ICON_SOL,
    notes='paladin-rework SHARED B1.5: hidden chance aura linked to Seal of Light 20165; 20% -> 201097 with a script-computed amount. The script prevents the default action.',
    raw_overrides=_chance_aura_raw('Your melee attacks have a chance to heal you.'),
)

seal_of_wisdom_mana_chance_201095 = spell(
    id=201095, name='Seal of Wisdom', school=_HOLY_ARCANE, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, implicit_target_a=1, trigger_spell=201098)],
    spell_icon_id=_ICON_SOW,
    notes='paladin-rework SHARED B1.5: hidden chance aura linked to Seal of Wisdom 20166; 20% -> 201098 with a script-computed amount. The script prevents the default action.',
    raw_overrides=_chance_aura_raw('Your melee attacks have a chance to restore your mana.'),
)

for _chance in (seal_of_justice_stun_chance_201093, seal_of_light_heal_chance_201094, seal_of_wisdom_mana_chance_201095):
    scripted_by(_chance, 'spell_pal_seal_chance_aura')
    procs_on(
        _chance, proc_flags=m.SEAL_PROC_FLAGS, spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE,
        spell_phase_mask=m.PROC_SPELL_PHASE_HIT, hit_mask=0, attributes_mask=0, chance=20, cooldown_ms=0,
    )

linked_spell(20164, 201093, type=2, comment='Seal of Justice -> hidden stun chance aura (paladin-rework SHARED B1.5)')
linked_spell(20165, 201094, type=2, comment='Seal of Light -> hidden heal chance aura (paladin-rework SHARED B1.5)')
linked_spell(20166, 201095, type=2, comment='Seal of Wisdom -> hidden mana chance aura (paladin-rework SHARED B1.5)')

seal_of_justice_stun_201096 = spell(
    id=201096, name='Seal of Justice', school=_HOLY_FROST,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=500,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, implicit_target_a=6)],
    spell_icon_id=_ICON_SOJ,
    notes='paladin-rework SHARED B1.5 (user ruling 2026-10-03, PLAN 1F F1): 0.5 s stun with NO mechanic (Mechanic 0, effect mechanic 0), so it is DIMINISHING_NONE and never accumulates DR on mobs; Justice Recovery 201106 (linked hit spell) is the 3 s lockout instead. No family bits. Also cast directly by Blade of Justice\'s Justice echo.',
    raw_overrides={**_text("Stuns the target for $d.", "Stunned."), **_chain(1), 'AttributesEx2': _ATTR2_IGNORE_LINE_OF_SIGHT, 'CastingTimeIndex': 1, 'DefenseType': _DMG_MAGIC, 'EquippedItemClass': -1, 'ProcChance': 101},
)

linked_spell(201096, 201106, type=1, comment='Seal of Justice stun -> Justice Recovery lockout on hit (paladin-rework SHARED B1.5, user ruling F1)')

seal_of_light_heal_201097 = spell(
    id=201097, name='Seal of Light', school=_HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[Effect(type=EffectType.HEAL, implicit_target_a=1, potency_excluded='percent of base health; base points supplied by the script (20% of GetCreateHealth)')],
    spell_icon_id=_ICON_SOL,
    notes='paladin-rework SHARED B1.5: Seal of Light self heal, 20% of base health, amount passed by spell_pal_seal_chance_aura via SPELLVALUE_BASE_POINT0.',
    raw_overrides={**_text("Heals you."), **_chain(1), 'CastingTimeIndex': 1, 'DefenseType': _DMG_MAGIC, 'EquippedItemClass': -1, 'ProcChance': 101},
)

seal_of_wisdom_mana_201098 = spell(
    id=201098, name='Seal of Wisdom', school=_HOLY_ARCANE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[Effect(type=EffectType.ENERGIZE, implicit_target_a=1, misc_value=0)],
    spell_icon_id=_ICON_SOW,
    notes='paladin-rework SHARED B1.5: Seal of Wisdom mana restore, 20% of base mana, amount passed by spell_pal_seal_chance_aura via SPELLVALUE_BASE_POINT0.',
    raw_overrides={**_text("Restores your mana."), **_chain(1), 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101},
)


# ===========================================================================================================
# B4.2 - unleash utility (cast by the Judgement / Deliverance dispatcher; amounts are live values passed as
# SPELLVALUE_BASE_POINT0, so every base_points here is a placeholder). No family bits on any of them (a C | CU
# SpellMod must never reach the Command debuff, and none carries U or the Judgement procs would fire on them).
# ===========================================================================================================

def _utility_raw(description: str, aura: str = "", dmg_class: int = _DMG_NONE, **extra) -> dict:
    return {
        **_text(description, aura), **_chain(1),
        'CastingTimeIndex': 1, 'DefenseType': dmg_class, 'EquippedItemClass': -1, 'ProcChance': 101, **extra,
    }


unleashed_righteousness_201099 = spell(
    id=201099, name='Unleashed Righteousness', school=_HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=10000,
    effects=[Effect(
        type=_EFFECT_APPLY_AREA_AURA_PARTY, apply_aura=AuraType.HASTE_ALL, implicit_target_a=1, radius_yards=40.0,
        potency_excluded='percent haste per seal stack; base points supplied by the dispatcher (0.63% x stacks, rounded once)',
    )],
    spell_icon_id=_ICON_SOR_ALIAS,
    notes='paladin-rework SHARED B4.2: Righteousness unleash party haste, 40 yd (starting guess), 10 s. Amount = RoundPctAmount(0.63 x stacks x (1 + effectPct/100)) passed by the dispatcher; skipped at 0 stacks.',
    raw_overrides=_utility_raw("Increases the haste of party members within $a1 yards by 0.63% per seal stack unleashed for $d.", "Haste increased by 0.63% per seal stack unleashed."),
)

unleashed_command_201100 = spell(
    id=201100, name='Unleashed Command', school=_HOLY_FIRE, dispel=DispelType.MAGIC,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=8000,
    effects=[Effect(
        type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=_MISC_ALL_SCHOOLS,
        implicit_target_a=6, potency_excluded='percent damage done per seal stack; base points (negative) supplied by the dispatcher',
    )],
    spell_icon_id=_ICON_SOC,
    notes='paladin-rework SHARED B4.2: Command unleash debuff, dispel Magic (starting guess), 8 s. Amount = -RoundPctAmount(0.63 x stacks x (1 + effectPct/100)). No family bits at all - neither C nor CU nor U.',
    raw_overrides=_utility_raw("Reduces the damage done by the target by 0.63% per seal stack unleashed for $d.", "Damage done reduced by 0.63% per seal stack unleashed.", _DMG_MAGIC, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT),
)

unleashed_vengeance_201101 = spell(
    id=201101, name='Unleashed Vengeance', school=_HOLY_SHADOW,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=15000,
    effects=[Effect(
        type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=_MISC_ALL_SCHOOLS, implicit_target_a=1,
        potency_excluded='percent of other damage: 20% of the Vengeance unleash DoT total, base points supplied by the dispatcher',
    )],
    spell_icon_id=_ICON_SOV,
    notes='paladin-rework SHARED B4.2: Vengeance unleash self shield = 20% of the main-target DoT total (divided by 0.4 for Deliverance), 15 s (starting guess; R silent). Icon 2292 is safe: no d1 0x400000.',
    raw_overrides=_utility_raw("Absorbs damage.", "Absorbs damage."),
)

unleashed_justice_201102 = spell(
    id=201102, name='Unleashed Justice', school=_HOLY_FROST, mechanic=Mechanic.STUN,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=5000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, mechanic=Mechanic.STUN, implicit_target_a=6)],
    spell_icon_id=_ICON_SOJ,
    notes='paladin-rework SHARED B4.2: Justice unleash stun (Judgement only), 5 s, mechanic STUN, normal DR (shares one DR with Hammer of Justice and 201105). Not gated by Justice Recovery.',
    raw_overrides=_utility_raw("Stuns the target for $d.", "Stunned.", _DMG_MAGIC, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT),
)

unleashed_light_201103 = spell(
    id=201103, name='Unleashed Light', school=_HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=15000,
    effects=[Effect(
        type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=2, implicit_target_a=1,
        potency_excluded='percent Holy damage per seal stack; base points supplied by the dispatcher',
    )],
    spell_icon_id=_ICON_SOL,
    notes='paladin-rework SHARED B4.2: Light unleash Holy damage buff, 15 s. Amount = RoundPctAmount(stacks x (1.25 + lightPerStackPct)); Sanctified Seals\' flat bonus excluded. Misc 2 = Holy; every combined seal school contains the Holy bit.',
    raw_overrides=_utility_raw("Increases your Holy damage by 1.25% per seal stack unleashed for $d.", "Holy damage increased by 1.25% per seal stack unleashed."),
)

unleashed_wisdom_201104 = spell(
    id=201104, name='Unleashed Wisdom', school=_HOLY_ARCANE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=5000,
    effects=[Effect(
        type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_ENERGIZE, misc_value=0, amplitude=1000, implicit_target_a=1,
        potency_excluded='percent of base mana per tick; base points supplied by the dispatcher',
    )],
    spell_icon_id=_ICON_SOW,
    notes='paladin-rework SHARED B4.2 (user ruling 2026-10-03): Wisdom unleash mana restore over time, 5 ticks of 1 s. Per-tick amount = CalculatePct(GetCreateMana(), 10 x (1 + effectPct/100)) passed by the dispatcher; it does NOT scale with seal stacks (only the unleash damage does).',
    raw_overrides=_utility_raw("Restores 10% of your base mana every sec for $d.", "Restoring 10% of base mana every sec."),
)

unleashed_justice_aoe_stun_201105 = spell(
    id=201105, name='Unleashed Justice', school=_HOLY_FROST, mechanic=Mechanic.STUN,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=2000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, mechanic=Mechanic.STUN, implicit_target_a=6)],
    spell_icon_id=_ICON_SOJ,
    notes='paladin-rework SHARED B4.2 (added in review-2, S-M1): clone of 201102 with a 2 s duration for the Deliverance stun, so diminishing returns scale it normally (SPELLVALUE_AURA_DURATION is applied after DR). Same name, icon, no bits; not gated by Justice Recovery.',
    raw_overrides=_utility_raw("Stuns the target for $d.", "Stunned.", _DMG_MAGIC, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT),
)

justice_recovery_201106 = spell(
    id=201106, name='Justice Recovery', school=_HOLY_FROST,
    attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_AURA_IS_DEBUFF | _ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=3000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=1)],
    spell_icon_id=_ICON_SOJ,
    notes='paladin-rework SHARED B1.5 (user ruling 2026-10-03, PLAN 1F F1): hidden 3 s lockout applied by linked_spell(201096, 201106, 1) to the unit the 0.5 s Seal of Justice stun hit (cast by that unit on itself, the paladin as originalCaster). Read by spell_pal_seal_chance_aura and Blade of Justice\'s Justice echo through HasAura(SPELL_JUSTICE_RECOVERY) with any caster. Negative, not dispellable, no mechanic, no bits, no proc row (DBC ProcTypeMask 0). Range 50000 declared although the link never range-checks it (CR1 carrier).',
    raw_overrides={**_text(), **_chain(1), 'AttributesEx3': _ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_SUPPRESS_TARGET_PROCS, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101},
)


# ===========================================================================================================
# C1.4 / C1.5 - aura bursts 201160-201164. 10 s, raid within 40 yd (TARGET_UNIT_CASTER_AREA_RAID = 56), positive,
# not purgeable, bit AB (d2 0x40000) on all five (Devotion also d2 b25, Concentration also d2 b26 - both
# forced at load for Improved Devotion Aura / Holy (3,0) - Retribution neither d2 b27 nor d0 b3), no SEAL / HAND
# bits and never the AURA bit d2 0x20. points_per_level 0 on every effect (the scripts scale 201162 / 201164).
# Cast TRIGGERED_FULL_MASK by spell_pal_aura_press on the aura button. SpellLevel = the aura's learn level.
# ===========================================================================================================

def _burst_raw(description: str, aura: str, mask3: int, spell_level: int, effect_slot: int = 1) -> dict:
    return {
        **_text(description, aura), **_chain(effect_slot),
        'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101,
        'SpellClassSet': 10, 'SpellClassMask_3': mask3, 'SpellLevel': spell_level,
    }


def _burst_effect(aura: int, base_points: int, misc_value: int = 0, **extra) -> Effect:
    return Effect(
        type=EffectType.APPLY_AURA, apply_aura=aura, base_points=base_points, points_per_level=0.0,
        misc_value=misc_value, implicit_target_a=56, radius_yards=40.0, **extra,
    )


retribution_burst_201160 = spell(
    id=201160, name='Retribution Burst', school=_HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=10000,
    effects=[_burst_effect(AuraType.MOD_CUSTOM_STAT_PCT, 9, misc_value=1 << 20)],
    spell_icon_id=555,
    notes='paladin-rework SHARED C1.4: Retribution Aura press burst, +10 Mastery (percentage points, misc 1 << CR_MASTERY) for 10 s. Carries AB only - neither d2 b27 nor d0 b3 (Sanctified / Swift Retribution would otherwise hit it).',
    raw_overrides=_burst_raw("Increases Mastery by $s1% for $d.", "Mastery increased by $s1%.", m.AURA_BURST, 16),
)

devotion_burst_201161 = spell(
    id=201161, name='Devotion Burst', school=_HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=10000,
    effects=[None, _burst_effect(AuraType.MOD_DAMAGE_PERCENT_TAKEN, -11, misc_value=_MISC_ALL_SCHOOLS)],
    spell_icon_id=291,
    notes='paladin-rework SHARED C1.4: Devotion Aura press burst, -10% damage taken for 10 s (starting guess). The reduction sits on effect INDEX 1 (eff0 empty) because Improved Devotion Aura\'s eff1 is SPELLMOD_EFFECT2 and its mask is forced to d2 b25 at load. Bits AB + d2 b25.',
    raw_overrides=_burst_raw("Reduces damage taken by $s2% for $d.", "Damage taken reduced by $s2%.", m.AURA_BURST | m.LOADTIME_IMP_DEVOTION, 1, effect_slot=2),
)

resistance_burst_201162 = spell(
    id=201162, name='Resistance Burst', school=_HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=10000,
    effects=[_burst_effect(
        AuraType.SCHOOL_ABSORB, 9, misc_value=_MISC_ALL_MAGIC,
        potency_excluded="percent of each target's maximum health; amount computed by spell_pal_resistance_burst",
    )],
    spell_icon_id=140,
    notes='paladin-rework SHARED C1.4: Resistance Aura press burst, absorbs magic damage equal to 10% of each target\'s maximum health (starting guess) for 10 s. spell_pal_resistance_burst turns the percent into health in DoEffectCalcAmount.',
    raw_overrides=_burst_raw("Absorbs magic damage equal to $s1% of maximum health for $d.", "Absorbs magic damage.", m.AURA_BURST, 28),
)

crusader_burst_201163 = spell(
    id=201163, name='Crusader Burst', school=_HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=10000,
    effects=[_burst_effect(_AURA_MOD_SPEED_NOT_STACK, 29)],
    spell_icon_id=2291,
    notes='paladin-rework SHARED C1.4: Crusader Aura press burst, +30% run speed (non-stacking, starting guess) for 10 s. Data only.',
    raw_overrides=_burst_raw("Increases movement speed by $s1% for $d.", "Movement speed increased by $s1%.", m.AURA_BURST, 20),
)

concentration_burst_201164 = spell(
    id=201164, name='Concentration Burst', school=_HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=10000,
    effects=[_burst_effect(_AURA_MOD_POWER_REGEN, 249, misc_value=0)],
    spell_icon_id=1487,
    tooltip_vars=concentration_tooltip,
    notes='paladin-rework SHARED C1.4: Concentration Aura press burst, 2.5% of each target\'s maximum mana per 5 s for 10 s (starting guess). Stored amount 250 = hundredths of a percent; spell_pal_concentration_burst scales it by the target\'s max mana. Effect indexes 1-2 empty (Holy (3,0)\'s EFFECT2 / EFFECT3 mods must find nothing). Bits AB + d2 b26, never d0 b17.',
    raw_overrides=_burst_raw("Restores ${$s1*$<ic>/100}% of maximum mana every 5 sec for $d.", "Mana regeneration increased.", m.AURA_BURST | m.LOADTIME_IMP_CONCENTRATION, 22),
)

scripted_by(resistance_burst_201162, 'spell_pal_resistance_burst')
scripted_by(concentration_burst_201164, 'spell_pal_concentration_burst')

# Only the two bursts whose amount differs between paladins need a group (SHARED C1.5): rule 4 keeps the
# strongest of two paladins' bursts. One group over all five would make different bursts exclusive.
spell_group(1212, devotion_burst_201161)
spell_group_rule(1212, stack_rule=4, description="Devotion Burst: strongest wins across paladins")
spell_group(1213, concentration_burst_201164)
spell_group_rule(1213, stack_rule=4, description="Concentration Burst: strongest wins across paladins")


# ===========================================================================================================
# B9 - tooltip variables for the shared spells' tooltips (SpellDescriptionVariables 1100-1104). Default feeders
# are Retribution's in-tree percent damage talents only (B8 Q13); conditional and runtime bonuses (Smite Evil,
# Two-Handed Specialization, +10%/stack, Sanctified Seals, the controlled x2) never enter an entry. Rank ids are
# the RETRIBUTION section 5 rank spells, referenced by bare id: `$?s<id>` checks the character knows the rank
# and `$<id>m<n>` reads its effect n (1-based). Spells (declared in paladin_spells.py) pick their own product:
# `{pot1*mult_j}`, `${$201081m1*$<mult_seal>}` and so on. 1101 is reserved and has no entry (B9: unleash
# tooltips are combat-log only).
# ===========================================================================================================

_IMPROVED_JUDGEMENTS = [25956, 25957, 201468]  # e1 +3/6/9% (JUDGEMENT_ALL)
_ART_OF_WAR = [53486, 53488, 201472]  # e1 +3/6/9% (AOW_DAMAGE)
_STRENGTH_OF_FAITH = [201446, 201447, 201448]  # e1 +1/2/3% all damage (aura 79)
_PURIFY_THE_UNCLEAN = [201451, 201452, 201453]  # e1 +3/6/9% (PURIFY_DAMAGE), e2 DOT
_IMPROVED_CRUSADER_STRIKE = [201449, 201450]  # e1 +5/10%
_SANCTITY_OF_BATTLE = [32043, 35396, 35397]  # e1 +5/10/15% (SANCTITY_DAMAGE), e2 DOT (SANCTITY_DOT)
_SANCTIFIED_WRATH = [53375, 53376]  # e3 +5/10% Exorcism
_SMITE_EVIL = [31866, 31867, 31868]  # e2 +1/2/3% all damage (aura 79); user ruling: shown on every shared tooltip

# Short names (ij = Improved Judgements, aw = The Art of War, sof = Strength of Faith, sm = Smite Evil,
# pu = Purify the Unclean): the long form is over the 1024-char entry cap once Smite Evil is added.
paladin_judgement_tooltip_1100 = tooltip_vars(
    1100, "Judgement / Deliverance own-hit damage talents (Retribution in-tree, SHARED B9 + Smite Evil)",
    ij=talent_mult(_IMPROVED_JUDGEMENTS),
    aw=talent_mult(_ART_OF_WAR),
    sof=talent_mult(_STRENGTH_OF_FAITH),
    sm=talent_mult(_SMITE_EVIL, effect=2),
    pu=talent_mult(_PURIFY_THE_UNCLEAN),
    mult_j=product("ij", "aw", "sof", "sm"),
    mult_dv=product("mult_j", "pu"),
)

# Short names (sof = Strength of Faith, sm = Smite Evil, pu = Purify the Unclean): the long forms
# (`strength_of_faith1`) read 0 in game, so every seal tooltip showed "0% weapon damage".
paladin_seal_tooltip_1102 = tooltip_vars(
    1102, "Seal tooltips quote the passive's weapon percent (Strength of Faith, Smite Evil; Purify the Unclean on Command only)",
    sof=talent_mult(_STRENGTH_OF_FAITH),
    sm=talent_mult(_SMITE_EVIL, effect=2),
    pu=talent_mult(_PURIFY_THE_UNCLEAN),
    mult_seal=product("sof", "sm"),
    mult_cmd=product("mult_seal", "pu"),
)

# Short names (ics = Improved Crusader Strike, aw = The Art of War, sob = Sanctity of Battle, sof = Strength of
# Faith, sm = Smite Evil): the long form is over the 1024-char entry cap once Smite Evil is added.
paladin_crusader_strike_tooltip_1103 = tooltip_vars(
    1103, "Crusader Strike weapon percent (Improved Crusader Strike, The Art of War, Sanctity of Battle, Strength of Faith, Smite Evil)",
    ics=talent_mult(_IMPROVED_CRUSADER_STRIKE),
    aw=talent_mult(_ART_OF_WAR),
    sob=talent_mult(_SANCTITY_OF_BATTLE),
    sof=talent_mult(_STRENGTH_OF_FAITH),
    sm=talent_mult(_SMITE_EVIL, effect=2),
    mult_cs=product("ics", "aw", "sob", "sof", "sm"),
)

# Very short variable names on purpose (the long form is over the 1024-char entry cap):
# f = Strength of Faith, m = Smite Evil, x = f * m, sb = Sanctity of Battle (sd = its DOT), sw = Sanctified
# Wrath, p = Purify the Unclean (pd = its DOT). mult_how is just x.
paladin_baseline_damage_tooltip_1104 = tooltip_vars(
    1104, "Exorcism / Hammer of Wrath / Holy Wrath / Consecration damage talents (Retribution in-tree, SHARED B9 + Smite Evil)",
    f=talent_mult(_STRENGTH_OF_FAITH),
    m=talent_mult(_SMITE_EVIL, effect=2),
    x=product("f", "m"),
    sb=talent_mult(_SANCTITY_OF_BATTLE),
    sd=talent_mult(_SANCTITY_OF_BATTLE, effect=2),
    sw=talent_mult(_SANCTIFIED_WRATH, effect=3),
    p=talent_mult(_PURIFY_THE_UNCLEAN),
    pd=talent_mult(_PURIFY_THE_UNCLEAN, effect=2),
    mult_exo=product("sb", "sw", "x"),
    mult_how="${$<x>*1}",
    mult_hw=product("p", "x"),
    mult_cons=product("sd", "pd", "x"),
)
