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

import dataclasses
from dataclasses import dataclass, field

from .. import potency as _potency


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
    # Potency system (docs/potency-system.md, PLAN P2) - when either is nonzero (or
    # weapon_potency is set), base_points/points_per_level/die_sides below are *generated* by
    # Spell.to_entry() from these, not hand-authored - see that method's potency pass. At most one
    # of (sp_potency and/or ap_potency) or weapon_potency may be used on one effect ("Hybrid
    # spells": weapon potency is a separate third kind that can't combine with attack power
    # potency on one effect).
    sp_potency: float = 0.0
    ap_potency: float = 0.0
    potency_kind: str | None = None  # one of lib.potency.VALID_KINDS; default KIND_DIRECT
    weapon_potency: float | None = None
    time_basis_ms: int | None = None  # "Time basis" override, e.g. an off-GCD proc payout
    # Drives the base-damage line in place of sp_potency + ap_potency, for the rare effect whose
    # base shouldn't equal what its SP/AP coefficients alone would imply - see lib.potency.resolve.
    # Never changes sp_coefficient/ap_coefficient, only EffectBasePoints/RealPointsPerLevel/the
    # correction row.
    base_potency: float | None = None
    # Set instead of sp_potency/ap_potency/weapon_potency on a damage/heal/absorb effect whose real
    # value is computed entirely by its own SpellScript at runtime, bypassing CalcValue - a
    # percent-of-other-damage effect (docs/potency-system.md's "Out of scope by design": "Ignite,
    # Deep Wounds"), e.g. Conflagrate reading Immolate/Shadowflame's live DoT total via
    # ComputeFullDurationTotal and pushing it through SetSpellValue. The DBC EffectBasePoints/
    # EffectBonusMultiplier fields on an effect like this are dead (tooltip text only), so
    # potency_report.py would otherwise print a meaningless implied-potency number for it forever -
    # this is the human's one-line declaration that it's deliberately out of scope, not an
    # unreviewed row, and why (freeform reason string, required - shows up nowhere else).
    potency_excluded: str | None = None

    @property
    def has_potency(self) -> bool:
        return bool(
            self.sp_potency or self.ap_potency or self.weapon_potency is not None
            or self.base_potency is not None
        )

    def to_dict(self) -> dict:
        if self.potency_excluded and self.has_potency:
            raise ValueError(
                "potency_excluded can't be combined with sp_potency/ap_potency/weapon_potency on "
                "the same effect - an effect either has a potency or is declared out of scope, not "
                "both"
            )
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
        if self.potency_excluded:
            d["_potency_excluded"] = self.potency_excluded
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
    range_yards: float | str | None = None  # or constants.RANGE_SELF
    radius_yards: float | None = None
    duration_ms: int | None = None
    effects: list[Effect | None] = field(default_factory=list)
    spell_icon_id: int | None = None
    spell_weight: float | None = None
    coeff_weight: float | None = None
    raw_overrides: dict | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        # Populated by _resolve_potency() during to_entry() - lib.dsl.registry.spell() reads
        # these to auto-emit the spell_bonus_data/spell_potency_correction rows a potency effect
        # needs, the same way to_entry() itself only ever returns the plain Spell.dbc dict shape
        # (see this class's own docstring on why that shape can't grow new keys for them).
        self.potency_bonus_row: dict | None = None
        self.potency_correction_rows: list[dict] = []

    def to_entry(self) -> dict:
        if len(self.effects) > 3:
            raise ValueError(
                f"spell {self.id} ({self.name}): a spell has at most 3 effects, got "
                f"{len(self.effects)}"
            )
        raw_overrides = dict(self.raw_overrides) if self.raw_overrides else {}
        effect_dicts = [(e.to_dict() if e is not None else None) for e in self.effects]
        effect_dicts += [None, None, None]
        if any(e is not None and e.has_potency for e in self.effects):
            self._resolve_potency(effect_dicts, raw_overrides)
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
            "raw_overrides": raw_overrides or None,
            "notes": self.notes,
        }

    def _resolve_potency(self, effect_dicts: list[dict | None], raw_overrides: dict) -> None:
        """Potency system (docs/potency-system.md, PLAN P2 step 2). Runs once per `to_entry()`
        call, only when at least one effect declared `sp_potency`/`ap_potency`/`weapon_potency`.
        Turns those declared inputs into the DBC fields `lib/build.py` already knows how to read
        (no changes to build.py/resolve.py/dbcfmt.py - "Where potency lives"): each potency
        effect's own `base_points`/`points_per_level`/`die_sides` in `effect_dicts`, the spell's
        `BaseLevel`/`MaxLevel`/`EffectBonusMultiplier_N` in `raw_overrides`, the `{pot1}`-style
        placeholders in `raw_overrides`'s description text, and (stashed on `self`, for
        `lib.dsl.registry.spell()` to pick up) the `spell_bonus_data` row (D1/D6 - only emitted
        when some effect has `ap_potency`) and one `spell_potency_correction` row per non-weapon
        potency effect."""
        spell_level = raw_overrides.get("SpellLevel")
        if spell_level is None:
            raise ValueError(
                f"spell {self.id} ({self.name}): a potency effect needs raw_overrides={{'SpellLevel': "
                f"<n>, ...}} - BaseLevel/MaxLevel are then generated to match it (\"BaseLevel must "
                f"equal SpellLevel\", \"MaxLevel stays 0\")."
            )
        raw_overrides["BaseLevel"] = spell_level
        raw_overrides["MaxLevel"] = 0

        resolved_by_index: dict[int, _potency.ResolvedPotency] = {}
        ticks_by_index: dict[int, float] = {}
        # D6's engine limit: spell_bonus_data has one direct and one DoT spell-power coefficient
        # for the *whole* spell - once any effect has ap_potency, that row replaces every direct
        # effect's own EffectBonusMultiplier_N, even a sibling effect that's SP-only itself. So
        # every direct potency effect's sp_coefficient must agree (same for periodic), not just
        # the ones that themselves carry ap_potency.
        direct_sp_coeffs: list[float] = []
        dot_sp_coeffs: list[float] = []
        bonus_ap = bonus_ap_dot = None

        for i, (effect, d) in enumerate(zip(self.effects, effect_dicts)):
            if effect is None or not effect.has_potency:
                continue
            index = i + 1  # 1-based, matching Effect_1/2/3 and {pot1}/{pot2}/{pot3}
            if effect.base_points or effect.points_per_level or effect.die_sides != 1:
                raise ValueError(
                    f"spell {self.id} effect {index}: base_points/points_per_level/die_sides are "
                    f"generated for a potency effect - don't set them by hand (PLAN P2 step 2)."
                )
            if effect.weapon_potency is not None:
                pe = _potency.PotencyEffect(weapon_potency=effect.weapon_potency)
            else:
                kind = effect.potency_kind or _potency.KIND_DIRECT
                is_periodic_like = kind in _potency.PERIODIC_LIKE_KINDS
                t_ms = effect.time_basis_ms or (
                    effect.amplitude if is_periodic_like else (self.cast_time_ms or 1500)
                )
                if is_periodic_like and not t_ms:
                    raise ValueError(
                        f"spell {self.id} effect {index}: potency_kind={kind!r} needs a nonzero "
                        f"amplitude (or an explicit time_basis_ms override)."
                    )
                pe = _potency.PotencyEffect(
                    sp_potency=effect.sp_potency, ap_potency=effect.ap_potency, kind=kind, t_ms=t_ms,
                    base_potency=effect.base_potency,
                )
            resolved = _potency.resolve(pe, spell_level=int(spell_level))
            resolved_by_index[index] = resolved
            d["base_points"] = resolved.base_points
            d["points_per_level"] = resolved.points_per_level
            d["die_sides"] = resolved.die_sides
            # Bookkeeping only (never a real DBC column - see build_spell_row, which only ever
            # reads named keys off an effect dict): lib.potency_sheet's docs/potency/<class>.md
            # writer reads this back to show potency/coefficients/levels without redoing the math
            # a second time or needing the (long gone, by the time generate.py gets here) Effect
            # object this was resolved from.
            d["_potency"] = dataclasses.asdict(resolved)
            d["_potency"]["spell_level"] = int(spell_level)

            if effect.weapon_potency is not None:
                continue  # "no correction row", no DBC/spell_bonus_data coefficient either

            raw_overrides[f"EffectBonusMultiplier_{index}"] = resolved.sp_coefficient
            if is_periodic_like and self.duration_ms and pe.t_ms:
                ticks_by_index[index] = max(1.0, round(self.duration_ms / pe.t_ms))
                d["_potency"]["ticks"] = ticks_by_index[index]
            self.potency_correction_rows.append({
                "id": f"{self.id}:{i}",
                "spell_id": self.id,
                "effect_index": i,
                "correction_per_level": resolved.correction_per_level,
                "breakpoint_level": resolved.breakpoint_level,
                "variance_pct": resolved.variance_pct,
                "cp_line": 0.0,
                "cp_correction_per_level": 0.0,
                "cp_ap": 0.0,
                "comment": f"potency {resolved.total_potency:g}, {resolved.t_seconds:g}s",
            })
            (dot_sp_coeffs if is_periodic_like else direct_sp_coeffs).append(resolved.sp_coefficient)
            if effect.ap_potency:
                if is_periodic_like:
                    if bonus_ap_dot is not None and abs(bonus_ap_dot - resolved.ap_coefficient) > 1e-6:
                        raise ValueError(
                            f"spell {self.id}: every periodic effect with ap_potency must share one "
                            f"attack-power coefficient (D6 engine limit on spell_bonus_data.ap_dot_bonus) "
                            f"- got {bonus_ap_dot} and {resolved.ap_coefficient}."
                        )
                    bonus_ap_dot = resolved.ap_coefficient
                else:
                    if bonus_ap is not None and abs(bonus_ap - resolved.ap_coefficient) > 1e-6:
                        raise ValueError(
                            f"spell {self.id}: every direct effect with ap_potency must share one "
                            f"attack-power coefficient (D6 engine limit on spell_bonus_data.ap_bonus) "
                            f"- got {bonus_ap} and {resolved.ap_coefficient}."
                        )
                    bonus_ap = resolved.ap_coefficient

        if bonus_ap is not None or bonus_ap_dot is not None:
            if len(set(round(c, 6) for c in direct_sp_coeffs)) > 1:
                raise ValueError(
                    f"spell {self.id}: this spell has ap_potency, so every direct effect's "
                    f"spell-power coefficient must match (D6 engine limit - spell_bonus_data.direct_bonus "
                    f"is one value for the whole spell, even a sibling effect with no ap_potency of its "
                    f"own) - got {direct_sp_coeffs}."
                )
            if len(set(round(c, 6) for c in dot_sp_coeffs)) > 1:
                raise ValueError(
                    f"spell {self.id}: this spell has ap_potency, so every periodic effect's "
                    f"spell-power coefficient must match (D6 engine limit - spell_bonus_data.dot_bonus "
                    f"is one value for the whole spell) - got {dot_sp_coeffs}."
                )
            # D1: a potency spell with any ap_potency gets a spell_bonus_data row carrying BOTH
            # halves - it never has an AP value with the spell-power columns left at 0, and it
            # replaces the DBC's own EffectBonusMultiplier_N for this spell entirely (the DBC
            # value is still written above for spells with no AP potency at all - harmless, since
            # a spell_bonus_data row simply wins when one exists).
            self.potency_bonus_row = {
                "id": self.id,
                "entry": self.id,
                "direct_bonus": direct_sp_coeffs[0] if direct_sp_coeffs else 0.0,
                "dot_bonus": dot_sp_coeffs[0] if dot_sp_coeffs else 0.0,
                "ap_bonus": bonus_ap or 0.0,
                "ap_dot_bonus": bonus_ap_dot or 0.0,
                "comments": self.name,
            }

        for key in ("Description_Lang_enUS", "AuraDescription_Lang_enUS"):
            text = raw_overrides.get(key)
            if text and "{pot" in text:
                raw_overrides[key] = _potency.expand_placeholders(text, resolved_by_index, ticks_by_index)


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
