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

**Stock-trainer discount.** Every other stock trainer (`DISCOUNTED_TRAINER_IDS`) sells at
`STOCK_TRAINER_PRICE_FACTOR` (1/5) of its *hand-written* price: the replay of every file except the
ones this tool generated (`replay_hand_written_trainer_spells`), or a `trained_by()` declaration's
`money_cost`. Generated files are left out of the base so the discount never compounds on its own
output. Rounding is MySQL's for `MoneyCost * 0.2` on an integer column (half away from zero), the
2026-08-22 one-off UPDATE (`init-server` 535ff98c0) the policy replaces. Spells in
`DISCOUNT_EXCLUDED_SPELL_IDS` keep their price. A live row with no hand-written source (only a
generated file wrote it and nothing declares it) is left alone.

**What is emitted** is every in-scope row that differs from live, so an unchanged rerun emits
nothing.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
from fractions import Fraction
from pathlib import Path
from typing import Iterable

from . import sql_dump, sqlcorpus, trainer_state
from .spell_tables import _is_generated

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
    def __init__(
        self, curve: Iterable[tuple[int, int]], overrides: dict[int, int], priced_ids: Iterable[int],
        discount_factor: str | Fraction = "1", discounted_ids: Iterable[int] = (),
        discount_excluded_spells: Iterable[int] = (),
    ):
        self.curve: Curve = validate_curve(curve)
        self.overrides = {int(k): int(v) for k, v in overrides.items()}
        for spell_id, copper in self.overrides.items():
            if copper <= 0:
                raise PricingPolicyError(f"PRICE_OVERRIDES[{spell_id}] = {copper}: price must be > 0")
        self.priced_ids = frozenset(int(t) for t in priced_ids)
        self.discount_factor = Fraction(discount_factor)
        if not 0 < self.discount_factor <= 1:
            raise PricingPolicyError(f"STOCK_TRAINER_PRICE_FACTOR = {discount_factor}: must be in (0, 1]")
        self.discounted_ids = frozenset(int(t) for t in discounted_ids)
        both = sorted(self.discounted_ids & self.priced_ids)
        if both:
            raise PricingPolicyError(f"TrainerId(s) {both} are in both PRICED_TRAINER_IDS and DISCOUNTED_TRAINER_IDS")
        self.discount_excluded_spells = frozenset(int(s) for s in discount_excluded_spells)

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
    return Policy(
        module.PRICE_CURVE, getattr(module, "PRICE_OVERRIDES", {}), module.PRICED_TRAINER_IDS,
        getattr(module, "STOCK_TRAINER_PRICE_FACTOR", "1"), getattr(module, "DISCOUNTED_TRAINER_IDS", ()),
        getattr(module, "DISCOUNT_EXCLUDED_SPELL_IDS", ()),
    )


def discounted_price(base: int, factor: Fraction) -> int:
    """`base * factor` rounded half away from zero, in integer math: what MySQL stores for
    `SET MoneyCost = MoneyCost * 0.2` on an integer column (prices are never negative)."""
    return (2 * int(base) * factor.numerator + factor.denominator) // (2 * factor.denominator)


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


_replay_memo: tuple[dict[Key, dict], str] | None = None
_hand_written_memo: dict[Key, dict] | None = None


def _reset_replay_memo() -> None:
    global _replay_memo, _hand_written_memo
    _replay_memo = None
    _hand_written_memo = None


sqlcorpus.register_reset(_reset_replay_memo)


def replay_trainer_spells() -> dict[Key, dict]:
    """`trainer_spell` as the DB holds it after the base dump and every migration, replayed in apply
    order. A statement the replay cannot apply prints a WARNING (never silently skipped).

    `generate.py` calls this twice. While a `sqlcorpus` is active the replay runs once and the second call prints the
    same WARNING lines again (stdout stays what two replays would have written) and returns its own copy."""
    global _replay_memo
    if sqlcorpus.active() is None:
        return _replay_trainer_spells()
    if _replay_memo is None:
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rows = _replay_trainer_spells()
        except BaseException:
            sys.stdout.write(buf.getvalue())  # what the replay printed before it failed
            raise
        _replay_memo = (rows, buf.getvalue())
    rows, printed = _replay_memo
    sys.stdout.write(printed)
    return {key: dict(row) for key, row in rows.items()}


def _replay_trainer_spells() -> dict[Key, dict]:
    rows = trainer_state.load_replayed_table_rows(
        "trainer_spell", TRAINER_SPELL_COLUMNS, ("TrainerId", "SpellId"), warn_skipped=True,
        fill_missing=True,  # every trainer_spell column defaults to 0
    )
    return {(int(r["TrainerId"]), int(r["SpellId"])): r for r in rows}


def replay_hand_written_trainer_spells() -> dict[Key, dict]:
    """`trainer_spell` replayed like `replay_trainer_spells` but without the files this tool generated
    (`spell_tables.GENERATED_MARKER`): the price a hand-written file, the base dump or module SQL set,
    which the stock-trainer discount is taken from. No WARNING lines: the full replay already printed
    them. Memoised per run while a `sqlcorpus` is active; callers get their own copy."""
    global _hand_written_memo
    if _hand_written_memo is None or sqlcorpus.active() is None:
        columns, key = TRAINER_SPELL_COLUMNS, ("TrainerId", "SpellId")
        base_path = trainer_state.BASE_SQL_DIR / "trainer_spell.sql"
        defaults = sql_dump.parse_create_table_defaults(base_path, "trainer_spell") if base_path.is_file() else {}
        rows: dict[tuple, dict] = {}
        files = ([base_path] if base_path.is_file() else []) + [
            p for p in trainer_state._migration_files_mentioning("trainer_spell") if not _is_generated(p)
        ]
        for path in files:
            sql_dump.apply_composite_key_statements(
                rows, columns, key, "trainer_spell", sqlcorpus.read_text(path), None, True, defaults=defaults,
                source=path.name,
            )
        _hand_written_memo = {(int(r["TrainerId"]), int(r["SpellId"])): r for r in rows.values()}
    return {k: dict(r) for k, r in _hand_written_memo.items()}


def discount_stock_trainer_spells(
    rows: list[dict], live: dict[Key, dict], hand_written: dict[Key, dict], removed: set[Key], policy: Policy,
) -> list[dict]:
    """`rows` (`priced_trainer_spells`' result: the priced trainers' rows and every declared row) plus
    the live rows of `policy.discounted_ids`, with every discounted trainer's `MoneyCost` set to
    `policy.discount_factor` of its hand-written price: a declared row's `money_cost`, else the
    `hand_written` replay's. Other columns are the declaration's or live's. Excluded spells, keys
    removed by `untrain()` and live rows nothing hand-written or declared supplies keep their price
    (they are not added)."""
    out: dict[Key, dict] = {(int(r["TrainerId"]), int(r["SpellId"])): dict(r) for r in rows}
    declared = set(out)
    for key, live_row in live.items():
        if key[0] in policy.discounted_ids and key not in removed and key not in out and key in hand_written:
            out[key] = dict(live_row)
    for key, row in out.items():
        if key[0] not in policy.discounted_ids or key[1] in policy.discount_excluded_spells:
            continue
        base = row["MoneyCost"] if key in declared else hand_written[key]["MoneyCost"]
        row["MoneyCost"] = discounted_price(base, policy.discount_factor)
    return list(out.values())


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
