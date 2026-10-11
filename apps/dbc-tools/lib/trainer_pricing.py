"""Class-trainer price policy - `source/trainer_pricing.py`'s learn-level price curve applied to
the `trainer_spell` rows of the priced trainers.

**Price is a function of `ReqLevel` (and an optional per-spell override) only.** No per-spell base
price is read, so there is nothing to compound: the pass is idempotent and retunable by editing
the curve and regenerating.

**Rows in scope:** the true live `trainer_spell` state (a replay over every file, generated ones
included) for trainers in `PRICED_TRAINER_IDS`, with `trained_by()` declarations merged in. A
declaration supplies every column except `MoneyCost`: its `money_cost` is ignored on a priced
trainer and honoured on any other. Keys removed by `untrain()` are excluded so the pass never
re-inserts a row the removal block deletes.

**What is emitted** is every in-scope row that differs from live, so an unchanged rerun emits
nothing.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Iterable

from . import trainer_state

POLICY_FILE = Path(__file__).resolve().parents[1] / "source" / "trainer_pricing.py"

TRAINER_SPELL_COLUMNS = (
    "TrainerId", "SpellId", "MoneyCost", "ReqSkillLine", "ReqSkillRank",
    "ReqAbility1", "ReqAbility2", "ReqAbility3", "ReqLevel", "VerifiedBuild",
)

Key = tuple[int, int]
Curve = tuple[tuple[int, int], ...]


class PricingPolicyError(ValueError):
    """`source/trainer_pricing.py` is malformed."""


class Policy:
    def __init__(self, curve: Iterable[tuple[int, int]], overrides: dict[int, int], priced_ids: Iterable[int]):
        self.curve: Curve = validate_curve(curve)
        self.overrides = {int(k): int(v) for k, v in overrides.items()}
        for spell_id, copper in self.overrides.items():
            if copper <= 0:
                raise PricingPolicyError(f"PRICE_OVERRIDES[{spell_id}] = {copper}: price must be > 0")
        self.priced_ids = frozenset(int(t) for t in priced_ids)

    def price_for(self, req_level: int, spell_id: int) -> int:
        """The override for `spell_id` if there is one, otherwise the curve's price at `req_level`."""
        override = self.overrides.get(int(spell_id))
        return override if override is not None else curve_price(self.curve, int(req_level))


def validate_curve(curve: Iterable[tuple[int, int]]) -> Curve:
    """Levels strictly increasing, prices non-decreasing and > 0, at least one anchor."""
    points = tuple((int(level), int(price)) for level, price in curve)
    if not points:
        raise PricingPolicyError("PRICE_CURVE is empty")
    for (l0, p0), (l1, p1) in zip(points, points[1:]):
        if l1 <= l0:
            raise PricingPolicyError(f"PRICE_CURVE levels must strictly increase: {l0} then {l1}")
        if p1 < p0:
            raise PricingPolicyError(f"PRICE_CURVE prices must not decrease: {p0}c at {l0}, {p1}c at {l1}")
    for level, price in points:
        if price <= 0:
            raise PricingPolicyError(f"PRICE_CURVE price at level {level} must be > 0, got {price}")
        if price % _step(price):
            raise PricingPolicyError(
                f"PRICE_CURVE price at level {level} ({price}c) must be a multiple of its rounding step "
                f"({_step(price)}c), or interpolated prices could exceed the next anchor"
            )
    return points


def _step(value: int) -> int:
    """Rounding step for a price of about `value` copper: 1c below 100c, 10c below 1g, else 1s."""
    return 1 if value < 100 else 10 if value < 10000 else 100


def curve_price(curve: Curve, level: int) -> int:
    """Price at `level`: an anchor's own price exactly, clamped outside the anchors, and between two
    anchors the linear interpolation in integer math, rounded half up to `_step`."""
    if level <= curve[0][0]:
        return curve[0][1]
    if level >= curve[-1][0]:
        return curve[-1][1]
    for (l0, p0), (l1, p1) in zip(curve, curve[1:]):
        if l0 <= level <= l1:
            if level == l1:
                return p1
            span = l1 - l0
            numerator = p0 * span + (p1 - p0) * (level - l0)  # price * span
            step = _step(numerator // span)
            return (2 * numerator + step * span) // (2 * step * span) * step
    raise AssertionError("unreachable: level lies inside the curve")  # pragma: no cover


def load_policy(path: Path = POLICY_FILE) -> Policy:
    """The policy from the data file, loaded by path since `source/` is data, not a package."""
    spec = importlib.util.spec_from_file_location("_trainer_pricing_policy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return Policy(module.PRICE_CURVE, getattr(module, "PRICE_OVERRIDES", {}), module.PRICED_TRAINER_IDS)


def live_priced_trainer_ids(
    policy: Policy, trainer_index: trainer_state.TrainerIndex,
) -> tuple[set[int], list[tuple[int, list[str]]]]:
    """`(ids, skipped)`: the allow-listed trainers that resolve to a live, spawned NPC, and the
    allow-listed ones that do not (with their `trainer_problems()`), which the caller warns about."""
    ids: set[int] = set()
    skipped: list[tuple[int, list[str]]] = []
    for trainer_id in sorted(policy.priced_ids):
        problems = trainer_index.trainer_problems(trainer_id)
        if problems:
            skipped.append((trainer_id, problems))
        else:
            ids.add(trainer_id)
    return ids, skipped


def replay_trainer_spells() -> dict[Key, dict]:
    """`trainer_spell` as the DB holds it after the base dump and every migration, replayed in apply
    order. A statement the replay cannot apply prints a WARNING (never silently skipped)."""
    rows = trainer_state.load_replayed_table_rows(
        "trainer_spell", TRAINER_SPELL_COLUMNS, ("TrainerId", "SpellId"), warn_skipped=True,
        fill_missing=True,  # every trainer_spell column defaults to 0
    )
    return {(int(r["TrainerId"]), int(r["SpellId"])): r for r in rows}


def priced_trainer_spells(
    declared: list[dict], live: dict[Key, dict], priced_ids: set[int], removed: set[Key], policy: Policy,
) -> list[dict]:
    """Every `trainer_spell` row that should exist after the policy: live rows of `priced_ids` and
    declared rows, `MoneyCost` from `policy.price_for(ReqLevel, SpellId)` on a priced trainer. A
    declared row for any other trainer passes through unchanged, `money_cost` honoured."""
    rows: dict[Key, dict] = {}
    for key, live_row in live.items():
        if key[0] in priced_ids and key not in removed:
            rows[key] = dict(live_row)
    for row in declared:
        key = (int(row["TrainerId"]), int(row["SpellId"]))
        if key in removed:
            continue
        rows[key] = dict(row)
    for key, row in rows.items():
        if key[0] in priced_ids:
            row["MoneyCost"] = policy.price_for(row["ReqLevel"], key[1])
    return list(rows.values())
