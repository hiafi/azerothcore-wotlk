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
    OPEN_LOCK = 33
    LEARN_SPELL = 36
    DISPEL = 38
    WEAPON_DAMAGE = 58
    THREAT = 63
    TRIGGER_SPELL = 64
    INTERRUPT_CAST = 68
    ADD_COMBO_POINTS = 80
    KNOCK_BACK = 98


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
    PROC_TRIGGER_SPELL = 42
    PERIODIC_LEECH = 53
    TRANSFORM = 56
    MOD_DISARM = 67
    MECHANIC_IMMUNITY = 77
    MOD_DAMAGE_PERCENT_TAKEN = 87
    PERIODIC_DAMAGE_PERCENT = 89
    MOD_ATTACK_POWER = 99
    MOD_HEALING_PCT = 118
