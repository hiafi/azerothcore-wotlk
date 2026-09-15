"""
Dataclasses for the DSL's hand-authored spell/talent/tab/skill-line-ability
declarations - see this package's `__init__.py` docstring.

Each `to_entry()` produces exactly the dict shape `lib/source.py`'s
`load_spells_csv`/`load_talents_yaml` already produce (same keys
`lib/build.py`'s `build_spell_row`/`build_talent_row`/`build_talenttab_row`/
`build_skilllineability_row` already read) - that's what lets Phase 0 prove
fidelity by feeding both an old CSV-parsed entry and a new DSL-built entry
through the *same*, completely unmodified `build.py` and asserting the two
full-width rows come out identical (`lib/test_dsl.py`), and what will let
Phase 1 wire `source/classes/*.py` into `generate.py` as a second input
without changing `build.py`/`resolve.py`/`dbcfmt.py`/`lint.py`/`sql_out.py`/
`patch_out.py` at all.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def _int(value) -> int | None:
    """`None` stays `None` (build.py's `entry.get(field, 0) or 0` already
    treats that the same as 0); anything else - a plain int or one of
    constants.py's IntEnum/IntFlag members - collapses to a plain int, since
    that's the type build_spell_row/etc. and json.dumps (raw_overrides,
    effectN) both expect."""
    return None if value is None else int(value)


@dataclass
class Effect:
    """One `effectN` slot. Field names/defaults mirror the JSON schema
    documented in apps/dbc-tools/README.md's "Source files" section exactly
    - `type` is required (an all-zero/absent effect is modeled by leaving
    the slot out of `Spell.effects` entirely, not by an all-default
    `Effect()`), everything else defaults the same way a blank CSV JSON
    field already does."""

    type: int
    base_points: int = 0
    points_per_level: float = 0.0
    die_sides: int = 1
    mechanic: int = 0
    implicit_target_a: int = 0
    implicit_target_b: int = 0
    apply_aura: int = 0
    amplitude: int = 0
    misc_value: int = 0
    trigger_spell: int = 0
    chain_targets: int = 0
    radius_yards: float | None = None

    def to_dict(self) -> dict:
        d = {
            "type": _int(self.type),
            "base_points": self.base_points,
            "points_per_level": self.points_per_level,
            "die_sides": self.die_sides,
            "mechanic": _int(self.mechanic),
            "implicit_target_a": self.implicit_target_a,
            "implicit_target_b": self.implicit_target_b,
            "apply_aura": _int(self.apply_aura),
            "amplitude": self.amplitude,
            "misc_value": self.misc_value,
            "trigger_spell": self.trigger_spell,
            "chain_targets": self.chain_targets,
        }
        # `radius_yards` is deliberately OMITTED (not set to None) when unset - lib/build.py's
        # build_spell_row does `effect.get("radius_yards", default_radius)`, which only falls
        # back to the spell-level radius when the key is *absent*, not when it's present-but-
        # None (that means "explicitly no radius", a real distinct case). Found via Phase 4's
        # real-data verification (spell 200008, Frozen Orb Pulse) - shipping this as
        # `"radius_yards": self.radius_yards` unconditionally silently broke radius inheritance
        # for every effect that relies on it, dropping EffectRadiusIndex to 0. See
        # `apps/dbc-tools/lib/test_dsl.py`'s regression test for this exact case.
        if self.radius_yards is not None:
            d["radius_yards"] = self.radius_yards
        return d


def ApplyAura(aura: int, base_points: int = 0, **kwargs) -> Effect:
    """Sugar for the overwhelmingly common `type=EffectType.APPLY_AURA`
    case - `ApplyAura(AuraType.MOD_DECREASE_SPEED, base_points=-17, ...)`
    instead of spelling out `type=EffectType.APPLY_AURA, apply_aura=...`
    every time. Any other `Effect` field (amplitude, implicit_target_a,
    duration-affecting radius_yards, ...) still passes through as a kwarg."""
    from .constants import EffectType

    return Effect(type=EffectType.APPLY_AURA, apply_aura=aura, base_points=base_points, **kwargs)


def Damage(base_points: int, points_per_level: float = 0.0, **kwargs) -> Effect:
    """Sugar for `type=EffectType.SCHOOL_DAMAGE`."""
    from .constants import EffectType

    return Effect(
        type=EffectType.SCHOOL_DAMAGE,
        base_points=base_points,
        points_per_level=points_per_level,
        **kwargs,
    )


@dataclass
class Spell:
    """One `Spell.dbc` row. Field names mirror `SPELL_CSV_FIELDNAMES` in
    `lib/source.py` (minus `_source_file`, which is CSV-file bookkeeping
    with no DSL equivalent) exactly, so `to_entry()`'s output needs zero
    translation in `build_spell_row`.

    `effects` replaces the CSV's positional `effect1`/`effect2`/`effect3`
    columns with an ordered list (at most 3) - index 0 is Effect_1, etc.
    An element can be `None` for a genuinely-empty slot that precedes a
    populated one (e.g. Effect_1 empty, Effect_2 real) - don't compact those
    away; `EffectSpellClassMask{A,B,C}_{1,2,3}`'s letter=effect-index
    convention (see `apps/dbc-tools/README.md`'s gotcha) means which literal
    slot an effect lands in can matter to a *different* spell's classmask
    override. `raw_overrides` is unchanged: the exact same any-column-name
    escape hatch, applied last, that already makes `pull.py` lossless."""

    id: int
    name: str
    school: int = 0
    dispel: int = 0
    mechanic: int = 0
    attributes: int = 0
    category: int = 0
    cast_time_ms: int | None = None
    cooldown_ms: int | None = None
    category_cooldown_ms: int | None = None
    power_type: int = 0
    mana_cost: int | None = None
    mana_cost_pct: int | None = None
    range_yards: float | None = None
    radius_yards: float | None = None
    duration_ms: int | None = None
    effects: list[Effect | None] = field(default_factory=list)
    spell_icon_id: int | None = None
    spell_weight: float | None = None
    coeff_weight: float | None = None
    raw_overrides: dict | None = None
    notes: str | None = None

    def to_entry(self) -> dict:
        if len(self.effects) > 3:
            raise ValueError(
                f"spell {self.id} ({self.name}): a spell has at most 3 effects, got "
                f"{len(self.effects)}"
            )
        effect_dicts = [(e.to_dict() if e is not None else None) for e in self.effects]
        effect_dicts += [None, None, None]
        return {
            "id": self.id,
            "name": self.name,
            "school": _int(self.school),
            "dispel": _int(self.dispel),
            "mechanic": _int(self.mechanic),
            "attributes": _int(self.attributes),
            "category": _int(self.category),
            "cast_time_ms": self.cast_time_ms,
            "cooldown_ms": self.cooldown_ms,
            "category_cooldown_ms": self.category_cooldown_ms,
            "power_type": _int(self.power_type),
            "mana_cost": self.mana_cost,
            "mana_cost_pct": self.mana_cost_pct,
            "range_yards": self.range_yards,
            "radius_yards": self.radius_yards,
            "duration_ms": self.duration_ms,
            "effect1": effect_dicts[0],
            "effect2": effect_dicts[1],
            "effect3": effect_dicts[2],
            "spell_icon_id": self.spell_icon_id,
            "spell_weight": self.spell_weight,
            "coeff_weight": self.coeff_weight,
            "raw_overrides": dict(self.raw_overrides) if self.raw_overrides else None,
            "notes": self.notes,
        }


@dataclass
class Talent:
    """One `Talent.dbc` row. Field names mirror `source/talents/*.yaml`'s
    `talents:` entries (see its schema comment) exactly."""

    id: int
    tab_id: int
    tier: int
    column: int
    rank_spell_ids: list[int] = field(default_factory=list)
    depends_on: dict | None = None  # {"talent_id": int, "rank": int}
    flags: int = 0
    raw_overrides: dict | None = None

    def to_entry(self) -> dict:
        return {
            "id": self.id,
            "tab_id": self.tab_id,
            "tier": self.tier,
            "column": self.column,
            "rank_spell_ids": list(self.rank_spell_ids),
            "depends_on": dict(self.depends_on) if self.depends_on else None,
            "flags": _int(self.flags),
            "raw_overrides": dict(self.raw_overrides) if self.raw_overrides else None,
        }


@dataclass
class TalentTab:
    """One `TalentTab.dbc` row. Field names mirror `source/talents/*.yaml`'s
    `tabs:` entries exactly, plus one DSL-only field:

    `skill_line` is **not** a real `TalentTab.dbc` column and is deliberately
    left out of `to_entry()`'s output — it's bookkeeping `registry.py`'s
    `granted_by_talent()` reads directly off this object (not off the entry
    dict) to derive a `SkillLineAbility` row for a player-castable talent
    rank in this tab, per `docs/skilllineability-handoff.md`'s "SkillLine
    per class" table (e.g. Mage Frost=6, Fire=8, Arcane=237). Leave it unset
    for a tab whose ranks are never granted-and-player-castable."""

    id: int
    name: str
    class_mask: int = 0
    pet_talent_mask: int = 0
    order_index: int = 0
    spell_icon_id: int = 0
    skill_line: int | None = None
    raw_overrides: dict | None = None

    def to_entry(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "class_mask": _int(self.class_mask),
            "pet_talent_mask": _int(self.pet_talent_mask),
            "order_index": _int(self.order_index),
            "spell_icon_id": _int(self.spell_icon_id),
            "raw_overrides": dict(self.raw_overrides) if self.raw_overrides else None,
        }


@dataclass
class SkillLineAbility:
    """One `SkillLineAbility.dbc` row. Field names mirror
    `source/talents/*.yaml`'s `skill_line_abilities:` entries exactly. See
    `docs/skilllineability-handoff.md` for why this table exists at all -
    Phase 2 of the plan is what stops a source file needing one of these
    hand-added and kept in sync with a `Talent` entry separately."""

    id: int
    skill_line: int
    spell_id: int
    class_mask: int = 0
    race_mask: int = 0
    min_skill_line_rank: int = 1
    raw_overrides: dict | None = None

    def to_entry(self) -> dict:
        return {
            "id": self.id,
            "skill_line": self.skill_line,
            "spell_id": self.spell_id,
            "class_mask": _int(self.class_mask),
            "race_mask": _int(self.race_mask),
            "min_skill_line_rank": _int(self.min_skill_line_rank),
            "raw_overrides": dict(self.raw_overrides) if self.raw_overrides else None,
        }
