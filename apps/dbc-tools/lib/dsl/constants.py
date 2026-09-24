"""
Named constants for the `Spell.dbc` column values already in use across
`source/spells/*.csv`/`source/talents/*.yaml` — the readability half of the
DSL (see this package's `__init__.py` docstring).

Deliberately **not** a full transcription of every `SpellSchools`/
`Mechanics`/`SpellEffects`/`AuraType` value AzerothCore defines (~50-150
members each) — per the plan's "Open questions", that's grown incrementally
as migration actually hits a value that isn't covered yet, not hand-typed
upfront for values nothing here has ever used. Every member below was
cross-checked against its C++ source rather than guessed; see the comment
above each enum for exactly where.

A source file can always fall back to a plain `int` for anything not named
here yet — every DSL field that takes one of these enums also accepts a
bare int, since the enums are just named ints (`IntEnum`/`IntFlag`), not a
separate type `build_spell_row` would need to unwrap.
"""

from __future__ import annotations

from enum import IntEnum, IntFlag


class School(IntFlag):
    """`SchoolMask` - a real bitmask, not a single choice: e.g. Frostfire
    damage is `School.FROST | School.FIRE`. Values transcribed from
    `SPELL_SCHOOL_MASK_*` in src/server/shared/SharedDefines.h (each is
    `1 << SPELL_SCHOOL_*`, not the raw 0-6 `SpellSchools` index - don't
    confuse the two; `spell_dbc.SchoolMask` is always the mask form)."""

    NORMAL = 1  # physical
    HOLY = 2
    FIRE = 4
    NATURE = 8
    FROST = 16
    SHADOW = 32
    ARCANE = 64


class PowerType(IntEnum):
    """`PowerType` column. Transcribed from `Powers` in
    src/server/shared/SharedDefines.h. HEALTH is the real (rarely-used)
    sentinel for "costs health instead of a power bar" - stored here as
    plain -2 for readability; the source enum spells it `0xFFFFFFFE`
    (identical bit pattern, just the unsigned spelling of -2)."""

    MANA = 0
    RAGE = 1
    FOCUS = 2
    ENERGY = 3
    HAPPINESS = 4
    RUNE = 5
    RUNIC_POWER = 6
    HEALTH = -2


class DispelType(IntEnum):
    """`DispelType` column. Transcribed from `DispelType` in
    src/server/shared/SharedDefines.h."""

    NONE = 0
    MAGIC = 1
    CURSE = 2
    DISEASE = 3
    POISON = 4
    STEALTH = 5
    INVISIBILITY = 6
    ALL = 7


class Mechanic(IntEnum):
    """`Mechanic` column and each effect's `EffectMechanic_N`. Transcribed
    from `Mechanics` in src/server/shared/SharedDefines.h - subset actually
    seen in source so far; add more as needed (see module docstring)."""

    NONE = 0
    CHARM = 1
    DISORIENTED = 2
    FEAR = 5
    ROOT = 7
    SILENCE = 9
    SLEEP = 10
    SNARE = 11
    STUN = 12
    FREEZE = 13
    KNOCKOUT = 14
    POLYMORPH = 17
    BANISH = 18
    SAPPED = 30


class EffectType(IntEnum):
    """Each effect's `type` (-> `Effect_N`). Transcribed from `SpellEffects`
    in src/server/shared/SharedDefines.h - subset actually seen in source so
    far; add more as needed (see module docstring)."""

    SCHOOL_DAMAGE = 2
    DUMMY = 3
    APPLY_AURA = 6
    POWER_DRAIN = 8
    HEAL = 10
    PERSISTENT_AREA_AURA = 27
    SUMMON = 28
    ENERGIZE = 30
    WEAPON_PERCENT_DAMAGE = 31  # druid-rework PLAN §6.4
    OPEN_LOCK = 33
    LEARN_SPELL = 36
    DISPEL = 38
    CHARGE = 96  # druid-rework PLAN §6.4 (SPELL_EFFECT_CHARGE)
    WEAPON_DAMAGE = 58
    THREAT = 63
    TRIGGER_SPELL = 64
    APPLY_AREA_AURA_RAID = 65
    INTERRUPT_CAST = 68
    SCRIPT_EFFECT = 77  # druid-rework PLAN §6.4
    ADD_COMBO_POINTS = 80
    KNOCK_BACK = 98
    NORMALIZED_WEAPON_DMG = 121  # druid-rework PLAN §6.4
    HEAL_PCT = 136  # druid-rework PLAN §6.4
    ENERGIZE_PCT = 137  # SPELL_EFFECT_ENERGIZE_PCT - a direct effect, not an APPLY_AURA aura type


class AuraType(IntEnum):
    """Each effect's `apply_aura` (-> `EffectAura_N`) when `type` is
    `EffectType.APPLY_AURA`. Transcribed from `AuraType` in
    src/server/game/Spells/Auras/SpellAuraDefines.h - subset actually seen
    in source so far; add more as needed (see module docstring)."""

    PERIODIC_DAMAGE = 3
    DUMMY = 4
    MOD_CONFUSE = 5
    MOD_FEAR = 7
    PERIODIC_HEAL = 8
    MOD_ATTACKSPEED = 9  # druid-rework PLAN §6.4
    MOD_THREAT = 10
    MOD_TAUNT = 11
    MOD_STUN = 12
    MOD_DAMAGE_DONE = 13
    PERIODIC_TRIGGER_SPELL = 23
    PERIODIC_ENERGIZE = 24
    MOD_PACIFY = 25
    MOD_ROOT = 26
    MOD_SILENCE = 27
    MOD_STAT = 29
    MOD_INCREASE_SPEED = 31
    MOD_DECREASE_SPEED = 33
    MOD_INCREASE_HEALTH = 34  # druid-rework PLAN §6.4
    PROC_TRIGGER_SPELL = 42
    MOD_DODGE_PERCENT = 49  # druid-rework PLAN §6.4
    MOD_WEAPON_CRIT_PERCENT = 52  # druid-rework PLAN §6.4
    PERIODIC_LEECH = 53
    TRANSFORM = 56
    MOD_SCALE = 61  # druid-rework PLAN §6.4
    MOD_DISARM = 67
    MECHANIC_IMMUNITY = 77
    MOD_DAMAGE_PERCENT_TAKEN = 87
    PERIODIC_DAMAGE_PERCENT = 89
    MOD_ATTACK_POWER = 99
    MOD_RESISTANCE_PCT = 101  # druid-rework PLAN §6.4
    MOD_HEALING_PCT = 118
    MOD_SPELL_HIT_CHANCE = 55
    MOD_SPELL_CRIT_CHANCE = 57
    SCHOOL_ABSORB = 69
    MOD_CASTING_SPEED_NOT_STACK = 65  # the standard passive "+X% spell haste"
    MOD_SPELL_CRIT_CHANCE_SCHOOL = 71
    MOD_POWER_COST_SCHOOL_PCT = 72
    MOD_DAMAGE_PERCENT_DONE = 79
    ADD_FLAT_MODIFIER = 107  # SpellMod - EffectMiscValue is the SPELLMOD_* op, classmask scopes it
    ADD_PCT_MODIFIER = 108
    ADD_TARGET_TRIGGER = 109  # druid-rework PLAN §6.4
    MOD_POWER_REGEN_PERCENT = 110  # druid-rework PLAN §6.4
    MOD_MANA_REGEN_INTERRUPT = 134
    MOD_HEALING_DONE = 135  # druid-rework BALANCE.md CORE-AUDIT row 6 - flat healing-done bonus (not a percent), consumed by spell_dru_astral_surge_sp's DoEffectCalcAmount
    MOD_HEALING_DONE_PERCENT = 136
    MOD_TOTAL_STAT_PERCENTAGE = 137
    MOD_MELEE_HASTE = 138  # druid-rework PLAN §6.4
    MOD_SPEED_ALWAYS = 129
    MOD_CRIT_DAMAGE_BONUS = 163
    MOD_SPELL_DAMAGE_OF_STAT_PERCENT = 174
    MOD_SPELL_HEALING_OF_STAT_PERCENT = 175
    MOD_BASE_RESISTANCE_PCT = 142  # druid-rework PLAN §6.4 / BALANCE §3.3
    REDUCE_PUSHBACK = 149  # druid-rework PLAN §6.4 / BALANCE §3.3
    MOD_ATTACK_POWER_PCT = 166  # druid-rework PLAN §6.4
    MOD_RATING = 189
    HASTE_ALL = 193  # SPELL_AURA_MELEE_SLOW in C++ (misnamed) - applies cast+melee+ranged haste in one effect (Bloodlust's own aura, SpellAuraEffects.cpp:4762) - PLAN §1's "generalized spell haste" mechanism
    MOD_RAGE_FROM_DAMAGE_DEALT = 213  # druid-rework PLAN §6.4
    MOD_MANA_REGEN_FROM_STAT = 219  # druid-rework PLAN §6.4 / BALANCE §3.3
    MOD_RATING_FROM_STAT = 220
    PERIODIC_DUMMY = 226
    MOD_AOE_DAMAGE_AVOIDANCE = 229  # druid-rework PLAN §6.4
    PROC_TRIGGER_SPELL_WITH_VALUE = 231  # druid-rework PLAN §6.4 / BALANCE §3.3 (not 227, that's the PERIODIC variant)
    MOD_HOT_PCT = 259  # druid-rework PLAN §6.4
    MOD_HEALING_RECEIVED = 283  # SpellAuraDefines.h: "Possibly only for some spell family class spells"
    ABILITY_PERIODIC_CRIT = 286  # druid-rework PLAN §6.4
    MOD_CRIT_PCT = 290
    # Custom aura types this fork added (see each one's comment in SpellAuraDefines.h):
    MOD_LEECH_PCT = 295  # % of damage dealt returned as health - Unit::GetLeechPercentage
    MOD_CUSTOM_STAT_PCT = 306  # flat % to one custom stat; misc_value = 1 << CR_* (see CombatRating below)


class SpellModOp(IntEnum):
    """`misc_value` of an `AuraType.ADD_FLAT_MODIFIER`/`ADD_PCT_MODIFIER`
    effect - which property of the classmask-matched spells it modifies.
    Transcribed from `SpellModOp` in src/server/game/Spells/SpellDefines.h.
    Every one of these needs a real `EffectSpellClassMask*` on the same
    effect slot or it applies to the whole spell family - see
    apps/dbc-tools/README.md's classmask gotcha and `lib/lint.py`."""

    DAMAGE = 0
    DURATION = 1
    THREAT = 2
    EFFECT1 = 3
    CHARGES = 4
    RANGE = 5
    RADIUS = 6
    CRITICAL_CHANCE = 7
    ALL_EFFECTS = 8
    NOT_LOSE_CASTING_TIME = 9
    CASTING_TIME = 10
    COOLDOWN = 11
    EFFECT2 = 12
    IGNORE_ARMOR = 13
    COST = 14
    CRIT_DAMAGE_BONUS = 15
    RESIST_MISS_CHANCE = 16
    JUMP_TARGETS = 17
    CHANCE_OF_SUCCESS = 18
    ACTIVATION_TIME = 19
    DAMAGE_MULTIPLIER = 20
    GLOBAL_COOLDOWN = 21
    DOT = 22
    EFFECT3 = 23
    BONUS_MULTIPLIER = 24
    PROC_PER_MINUTE = 26
    VALUE_MULTIPLIER = 27
    RESIST_DISPEL_CHANCE = 28


class CombatRating(IntEnum):
    """`CombatRating` in src/server/game/Entities/Unit/Unit.h - the index a
    `AuraType.MOD_RATING`/`MOD_CUSTOM_STAT_PCT` effect selects through its
    `misc_value` as a **bit** (`1 << CR_*`), so pass e.g.
    `misc_value=1 << CombatRating.VERSATILITY`. Only the four custom stats
    this fork added are named here (they're the only ones a talent has ever
    needed to grant by aura); the rest are plain stock ratings."""

    DODGE = 2  # stock CR_DODGE - druid-rework PLAN §6.4
    PROC_CHANCE = 11  # Custom: was CR_HIT_TAKEN_MELEE
    MASTERY = 20  # Custom: was CR_WEAPON_SKILL_MAINHAND
    VERSATILITY = 21  # Custom: was CR_WEAPON_SKILL_OFFHAND
    COOLDOWN_HASTE = 22  # Custom: was CR_WEAPON_SKILL_RANGED


class ShapeshiftForm(IntEnum):
    """`ShapeshiftMask`/`ShapeshiftExclude` bit source and `spellshapeshiftform_dbc`'s
    `form_id` - transcribed from `ShapeShiftForm` in
    src/server/game/Entities/Unit/UnitDefines.h. Only the forms druid-rework
    passes actually reference are named here (see module docstring)."""

    CAT = 1
    TREE = 2
    TRAVEL = 3
    AQUA = 4
    BEAR = 5
    DIREBEAR = 8
    FLIGHT_EPIC = 27
    FLIGHT = 29
    MOONKIN = 31
