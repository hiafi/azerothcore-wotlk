"""
Pure math for the potency system (docs/potency-system.md, PLAN P2 -
`.agents/plans/potency-system/potency-system.PLAN.md`). No side effects, no registry/DB/file
access - `lib/dsl/model.py`'s `Spell.to_entry()` calls into this to turn an effect's declared
`sp_potency`/`ap_potency`/`weapon_potency` into the DBC fields (`EffectBasePoints`,
`EffectRealPointsPerLevel`, `EffectDieSides`, `EffectBonusMultiplier_N`), the
`spell_bonus_data`/`spell_potency_correction` rows, and the tooltip's nested-`$max()` expression.

Every constant and formula here traces straight back to a named section of that doc - don't
retune anything in this file without updating the doc first ("Potency lives only in the Python
source" / "Where potency lives"). Every formula below is cross-checked against the doc's own
worked reference tables in `test_potency.py` (Frostbolt, Corruption, the heal table, the hybrid
Exorcism/Holy Wrath/Consecration table, and the attack-power table at R=2) - if a retune in the
doc changes a constant, update it here and that test file will say exactly which table broke.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Kinds (DSL's `potency_kind=`) - "Periodic effects", "Healing", "Damage range"
# ---------------------------------------------------------------------------

KIND_DIRECT = "direct"
KIND_PERIODIC = "periodic"
KIND_HEAL = "heal"
KIND_HEAL_PERIODIC = "heal_periodic"
KIND_ABSORB = "absorb"
VALID_KINDS = (KIND_DIRECT, KIND_PERIODIC, KIND_HEAL, KIND_HEAL_PERIODIC, KIND_ABSORB)
# "Absorbs behave exactly like heals: same formula, multiplier and coefficient."
HEAL_LIKE_KINDS = (KIND_HEAL, KIND_HEAL_PERIODIC, KIND_ABSORB)
# Time basis is the tick interval, not cast time ("Time basis" table) - and no DieSides-style
# min-to-max roll, "because an aura rolls its amount once at application" ("Damage range").
PERIODIC_LIKE_KINDS = (KIND_PERIODIC, KIND_HEAL_PERIODIC)

# ---------------------------------------------------------------------------
# Level scaling ("Level scaling") - C(L) is two straight segments meeting at level 25.
# ---------------------------------------------------------------------------

C_LOW_INTERCEPT = 0.165625
C_LOW_SLOPE = 0.016375
C_HIGH_SLOPE = 0.06
BREAKPOINT_LEVEL = 25  # where the two C(L) segments meet; also spell_potency_correction's breakpoint_level
REFERENCE_LEVEL = 60  # "Level 60 is the launch cap and the most important number to hit"

# "Healing"
HEAL_BASE_MULT = 3.96
HEAL_COEF_MULT = 1.88
# "Damage range" - potency sets the average; the generator bakes the minimum as potency / 1.05,
# and the hook rolls the minimum up to 1.1x it (direct damage effects only).
DIRECT_MIN_DIVISOR = 1.05
DIRECT_VARIANCE_PCT = 10.0
# "Attack power abilities" - measured in P3 (2026-10-01, user-approved) from best-in-slot level 60
# gear under this server's stat system: effective spell power (gear Spell Power + 0.5x(Intellect +
# Spirit), this fork's custom formula) on the best obtainable caster gear vs. effective attack
# power (gear Attack Power + 2xStrength, the stock Warrior/Paladin/DK formula) on the best
# obtainable physical gear, both at RequiredLevel 60/Quality Epic/ItemLevel 60-100 (non-obtainable
# fixture/test item_template rows excluded - see potency-system.PROGRESS.md's P3 section). Measured
# ~1.07, rounded to 1.0 by the user. Supersedes the original "R = 2, 1,000 AP vs 500 SP" placeholder
# - see docs/potency-system.md's "Attack power abilities" section for the full writeup.
DEFAULT_R = 1.0


def c_of_level(level: float) -> float:
    """C(L), the level constant per potency point ("Level scaling")."""
    return (
        C_LOW_INTERCEPT
        + C_LOW_SLOPE * min(level, BREAKPOINT_LEVEL)
        + C_HIGH_SLOPE * max(0.0, level - BREAKPOINT_LEVEL)
    )


C60 = c_of_level(REFERENCE_LEVEL)  # 2.675 - "the upper segment passes exactly through stock at 60 and 70"


@dataclass(frozen=True)
class PotencyEffect:
    """One effect's declared potency inputs, already resolved against the owning spell's
    `cast_time_ms`/effect `amplitude`/`time_basis_ms` override into a single `t_ms` - see
    "Time basis". `lib.dsl.model.Spell.to_entry()` does that resolution (it has the spell-level
    context this module deliberately doesn't); this stays a pure function of plain numbers."""

    sp_potency: float = 0.0
    ap_potency: float = 0.0
    kind: str = KIND_DIRECT
    t_ms: float = 1500.0
    weapon_potency: float | None = None
    # Drives the base-damage line (F, hence EffectBasePoints/EffectRealPointsPerLevel/the
    # correction row) in place of sp_potency + ap_potency, when the base the spell should deal
    # needs to differ from what its SP/AP coefficients alone would imply. sp_coefficient/
    # ap_coefficient are always computed from sp_potency/ap_potency directly - this only
    # overrides what feeds the shared base-damage formula, never the per-stat scaling.
    base_potency: float | None = None


@dataclass(frozen=True)
class ResolvedPotency:
    """Everything the DBC/correction row/tooltip need for one effect - "dbc-tools generator"."""

    base_points: int
    points_per_level: float
    die_sides: int
    sp_coefficient: float
    ap_coefficient: float
    correction_per_level: float | None  # None for a weapon_potency effect - no correction row at all
    breakpoint_level: int
    variance_pct: float
    level60_value: float  # the baked value at 60 (minimum, for direct effects)
    tooltip_low_intercept: float
    tooltip_low_slope: float
    tooltip_high_offset: float
    t_seconds: float
    total_potency: float
    kind: str


def resolve(effect: PotencyEffect, spell_level: int, r: float = DEFAULT_R) -> ResolvedPotency:
    """The "dbc-tools generator" table, in order. `spell_level` is the effect's own spell's
    `SpellLevel` (== `BaseLevel` - "BaseLevel must equal SpellLevel", "Caveats and checks")."""
    if effect.weapon_potency is not None:
        return _resolve_weapon(effect)
    if effect.kind not in VALID_KINDS:
        raise ValueError(f"potency_kind={effect.kind!r} must be one of {VALID_KINDS}")
    total = effect.sp_potency + effect.ap_potency
    if total <= 0 and effect.base_potency is None:
        raise ValueError(
            "a potency effect needs sp_potency + ap_potency > 0 (set weapon_potency instead for "
            "a weapon strike, or base_potency to drive the base from a number other than the SP/AP "
            "coefficients)"
        )
    t = effect.t_ms / 1000.0
    is_direct = effect.kind == KIND_DIRECT
    is_heal_like = effect.kind in HEAL_LIKE_KINDS

    # "Base damage comes from both" (Hybrid spells): F is built from total potency (P_sp + P_ap) -
    # unless base_potency says otherwise, for the rare spell whose base shouldn't equal what its
    # SP/AP coefficients alone imply.
    base_total = effect.base_potency if effect.base_potency is not None else total
    f = base_total * t / 1.5
    if is_heal_like:
        f *= HEAL_BASE_MULT
    if is_direct:
        # "F is divided by 1.05 so the baked value is the minimum and potency stays the average."
        f /= DIRECT_MIN_DIVISOR

    real_points_per_level = C_HIGH_SLOPE * f
    correction_per_level = (C_HIGH_SLOPE - C_LOW_SLOPE) * f  # K = (hi - lo) x F
    level60_value = C60 * f
    base_points = round(level60_value) - 1 - int((REFERENCE_LEVEL - spell_level) * real_points_per_level)

    coef_mult = HEAL_COEF_MULT if is_heal_like else 1.0
    sp_coefficient = (effect.sp_potency / 100.0) * (t / 3.5) * coef_mult
    ap_coefficient = (effect.ap_potency / 100.0) * (t / 3.5) / r

    # "Generator implication (P2)": LOW_INTERCEPT/LOW_SLOPE/HIGH_OFFSET, same derivation as
    # EffectRealPointsPerLevel/K above but off the *low* segment's C(L) coefficients, purely for
    # the tooltip string - never stored in the DBC or any table.
    tooltip_low_slope = C_LOW_SLOPE * f
    tooltip_low_intercept = C_LOW_INTERCEPT * f
    tooltip_high_offset = (
        REFERENCE_LEVEL - round(level60_value) / real_points_per_level if real_points_per_level else 0.0
    )

    return ResolvedPotency(
        base_points=base_points,
        points_per_level=real_points_per_level,
        die_sides=1,
        sp_coefficient=sp_coefficient,
        ap_coefficient=ap_coefficient,
        correction_per_level=correction_per_level,
        breakpoint_level=BREAKPOINT_LEVEL,
        variance_pct=DIRECT_VARIANCE_PCT if is_direct else 0.0,
        level60_value=level60_value,
        tooltip_low_intercept=tooltip_low_intercept,
        tooltip_low_slope=tooltip_low_slope,
        tooltip_high_offset=tooltip_high_offset,
        t_seconds=t,
        total_potency=base_total,
        kind=effect.kind,
    )


def _resolve_weapon(effect: PotencyEffect) -> ResolvedPotency:
    """"Weapon attacks": the weapon percent effect's base points are the potency itself, with
    EffectRealPointsPerLevel 0 and no correction row - gear already scales weapon damage through
    item level and attack power, so weapon potency never touches C(L)."""
    if effect.sp_potency or effect.ap_potency:
        raise ValueError(
            "weapon_potency can't be combined with sp_potency/ap_potency on the same effect "
            "(\"Hybrid spells\": weapon potency is a separate third kind)"
        )
    wp = effect.weapon_potency
    if wp != round(wp):
        raise ValueError(f"weapon_potency must be a whole number, got {wp!r} (\"Keep weapon potency whole\")")
    return ResolvedPotency(
        base_points=int(round(wp)),
        points_per_level=0.0,
        die_sides=1,
        sp_coefficient=0.0,
        ap_coefficient=0.0,
        correction_per_level=None,
        breakpoint_level=0,
        variance_pct=0.0,
        level60_value=float(wp),
        tooltip_low_intercept=0.0,
        tooltip_low_slope=0.0,
        tooltip_high_offset=0.0,
        t_seconds=0.0,
        total_potency=wp,
        kind="weapon",
    )


def simulate_value(resolved: ResolvedPotency, level: int, spell_level: int, roll: float = 1.0) -> float:
    """Reproduces `SpellEffectInfo::CalcValue` plus the potency correction hook
    (`src/server/game/Spells/SpellInfo.cpp`, `SpellPotency.cpp`) for one caster level - so the
    pytest reference-table checks and the per-class potency sheet both read numbers the way the
    live engine actually computes them, not a second hand-derived approximation. `roll` is the
    hook's own `frand(1, 1 + variance_pct/100)` - pass 1.0 for the minimum, `1 + variance_pct/100`
    for the maximum."""
    level = max(level, spell_level)  # BaseLevel == SpellLevel, so CalcValue clamps up to it
    native = resolved.base_points + int((level - spell_level) * resolved.points_per_level) + 1  # DieSides 1
    value = float(native)
    if resolved.correction_per_level is not None and level < resolved.breakpoint_level:
        value += resolved.correction_per_level * (resolved.breakpoint_level - level)
    return value * roll


def _stat_bonus_term(resolved: ResolvedPotency, ticks: float) -> str:
    """The caster's live spell-power/attack-power contribution, as a `${...}`-safe term - found
    missing 2026-10-01 (P5): `{pot1}`'s nested-`$max()` formula only ever encoded the level-scaled
    base, so a converted spell's tooltip undershot real combat damage by exactly its SP/AP bonus.
    `$SP`/`$AP` (current effective spell/attack power) confirmed live, by a scratch-spell round
    trip, to work inside a raw `${...}` math block - see potency-system.PROGRESS.md's P5 section.
    Scales by `ticks` (same as the base terms) so a `.total` placeholder sums the per-tick bonus
    over every tick; never by `scale` (the direct-effect ±variance roll), since the live hook only
    randomizes the base value - the SP/AP bonus is added afterwards, unrolled, by a separate,
    later step (`Unit::SpellDamageBonusDone`), so both sides of a `{X} to {1.1X}` range must carry
    the identical bonus."""
    terms = []
    if resolved.sp_coefficient:
        terms.append(f"{_fmt(resolved.sp_coefficient * ticks)}*$SP")
    if resolved.ap_coefficient:
        terms.append(f"{_fmt(resolved.ap_coefficient * ticks)}*$AP")
    return "+".join(terms)


def tooltip_expression(resolved: ResolvedPotency, *, ticks: float = 1.0, scale: float = 1.0) -> str:
    """The inside of one `${...}` block - the validated nested-`$max()` expression
    ("Tooltip"). `scale` is 1.0 for the minimum side of a direct effect's range, `1 +
    variance_pct/100` for the maximum side. `ticks` multiplies every linear coefficient by the
    tick count for a periodic effect's `.total` placeholder (see `expand_placeholders`) - the
    HIGH_OFFSET x-intercept doesn't change under a uniform scale, only the two slopes/intercepts
    that get scaled by it do.

    The SP/AP bonus (`_stat_bonus_term`) is added into *every* branch of the outer `$max()` rather
    than appended once to the result - `max(a, b) + c == max(a + c, b + c)` for any constant `c`,
    and a top-level `+` outside every `$max()`/`$min()` call silently drops everything after it on
    this fork's client (confirmed live, P0). Distributing the addition into each branch keeps the
    whole expression inside one top-level `$max()` call, sidestepping the bug the same way the
    base formula already does."""
    low_intercept = resolved.tooltip_low_intercept * ticks * scale
    low_slope = resolved.tooltip_low_slope * ticks * scale
    real_ppl = resolved.points_per_level * ticks * scale
    high_offset = resolved.tooltip_high_offset
    bonus = _stat_bonus_term(resolved, ticks)
    bonus_suffix = f"+{bonus}" if bonus else ""
    zero_branch = bonus if bonus else "0"
    return (
        f"$max($max({zero_branch},{_fmt(low_intercept)}+{_fmt(low_slope)}*$PL{bonus_suffix}),"
        f"{_fmt(real_ppl)}*$max(0,$PL-{_fmt(high_offset)}){bonus_suffix})"
    )


def _fmt(x: float) -> str:
    """Trims a computed constant to a sane number of decimals for the generated tooltip text,
    without trailing-zero/bare-'.0' noise."""
    return f"{x:.4f}".rstrip("0").rstrip(".") or "0"


_PLACEHOLDER_RE = re.compile(r"\{pot(?P<index>[123])(?:\.(?P<variant>avg|total))?\}")


def expand_placeholders(
    text: str,
    resolved_by_index: dict[int, ResolvedPotency],
    ticks_by_index: dict[int, float] | None = None,
) -> str:
    """Replaces `{pot1}` / `{pot1.avg}` / `{pot1.total}` (1-based effect index, matching
    `Effect_1`/`Effect_2`/`Effect_3`) in a spell's description text with the validated tooltip
    expression - PLAN P2 step 3. `{pot1}` is the range (`${min} to ${max}` for a direct effect
    with a variance roll, a single `${value}` for anything else), `{pot1.avg}` the average as one
    `${...}`, `{pot1.total}` the periodic sum over its effect's tick count (duration / amplitude -
    `ticks_by_index`, supplied by the caller since this module doesn't see `duration_ms`)."""
    ticks_by_index = ticks_by_index or {}

    def _sub(m: re.Match) -> str:
        idx = int(m.group("index"))
        variant = m.group("variant")
        resolved = resolved_by_index.get(idx)
        if resolved is None:
            raise ValueError(f"{{pot{idx}}} used in a description, but effect {idx} has no potency set")
        if variant == "total":
            n = ticks_by_index.get(idx, 1.0)
            return f"${{{tooltip_expression(resolved, ticks=n)}}}"
        if variant == "avg":
            avg_scale = 1.0 + (resolved.variance_pct / 200.0 if resolved.variance_pct else 0.0)
            return f"${{{tooltip_expression(resolved, scale=avg_scale)}}}"
        if resolved.variance_pct:
            lo = tooltip_expression(resolved, scale=1.0)
            hi = tooltip_expression(resolved, scale=1.0 + resolved.variance_pct / 100.0)
            return f"${{{lo}}} to ${{{hi}}}"
        return f"${{{tooltip_expression(resolved)}}}"

    return _PLACEHOLDER_RE.sub(_sub, text)
