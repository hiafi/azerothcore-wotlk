"""
Python port of `ResolveBudget()`/`ApplyItemBudgetAllocation()`
(`src/server/game/Globals/ItemBudget.cpp`) - the percentage-allocation
itemization system's actual runtime formula (see
`docs/itemization-changes.md` §2/§6). This is a SEPARATE implementation of
the same math, not a call into the C++ - keep the two in sync by hand if the
formula ever changes; `ItemBudget.cpp`'s `ResolveBudget()` is the source of
truth this was ported from, and it should say the same back (see that
function's own comment pointing here).

Pure functions - no file I/O of its own. Callers pass in the item's
`item_template` row (from `lib.overlay.get_rows()`) and the budget system's
reference/content tables (from `lib.budget_overlay.get_all()`).
"""

from __future__ import annotations

import math

ITEM_CLASS_WEAPON = 2
ITEM_CLASS_ARMOR = 4
ITEM_QUALITY_UNCOMMON = 2
ITEM_MOD_STAMINA = 7
MAX_ITEM_PROTO_STATS = 10
MAX_ITEM_PROTO_SPELLS = 5
MAX_ITEM_PROTO_SOCKETS = 3


def _round(x: float) -> int:
    """C++'s std::lround: round-half-away-from-zero, not Python's
    round-half-to-even."""
    return math.floor(x + 0.5) if x >= 0 else math.ceil(x - 0.5)


class BudgetError(Exception):
    """Reference data required for this item is missing - mirrors
    ResolveBudget() returning false. The webui should show this as a plain
    message, not a stack trace; it's an expected state (e.g. previewing an
    item level or armor class that has no curve entry yet), same as the
    C++'s validation pass logging and skipping rather than crashing."""


def compute_breakdown(item_row: dict, assign_row: dict, tables: dict[str, dict]) -> dict:
    """Mirrors `ResolveBudget()`. `item_row` is one `item_template` row
    (`lib.overlay.get_rows()`'s value shape). `assign_row` is one
    `item_budget_assign` row - pass a dict with the real column names even
    for a not-yet-saved preview (`entry`/`template_id`/`budget_mult`/
    `stamina_delta`/`dps_delta`/`absorbed_spell_slots`/`armor_delta`).
    `tables` is `lib.budget_overlay.get_all()`'s return value.

    Returns a dict with the same shape as ItemBudget::Breakdown (see
    ItemBudget.h) using snake_case keys, plus `stats`: a list of
    `{stat_type, alloc, raw, rounded}` in template order after
    largest-remainder rounding.
    """
    entry = item_row["entry"]
    ilvl = item_row["ItemLevel"]
    quality = item_row["Quality"]
    inv_type = item_row["InventoryType"]
    item_class = item_row["class"]
    sub_class = item_row["subclass"]
    template_id = assign_row["template_id"]

    slot_mult_row = tables["item_slot_mult"].get((inv_type,))
    quality_mult_row = tables["item_quality_mult"].get((quality,))
    curve_row = tables["item_budget_curve"].get((ilvl,))
    stamina_curve_row = tables["item_stamina_curve"].get((ilvl,))
    template_stats = [row for (tid, _stat), row in tables["item_budget_template"].items() if tid == template_id]

    missing = []
    if slot_mult_row is None:
        missing.append(f"item_slot_mult has no row for InventoryType {inv_type}")
    if quality_mult_row is None:
        missing.append(f"item_quality_mult has no row for Quality {quality}")
    if curve_row is None:
        missing.append(f"item_budget_curve has no row for ilvl {ilvl}")
    if stamina_curve_row is None:
        missing.append(f"item_stamina_curve has no row for ilvl {ilvl}")
    if not template_stats:
        missing.append(f"item_budget_template {template_id} has no stat rows")
    if missing:
        raise BudgetError("; ".join(missing))

    b: dict = {
        "entry": entry,
        "template_id": template_id,
        "item_level": ilvl,
        "quality": quality,
        "inventory_type": inv_type,
        "is_weapon": item_class == ITEM_CLASS_WEAPON,
    }

    slot_mult = slot_mult_row["mult"]
    quality_mult = quality_mult_row["mult"]
    budget_mult = assign_row["budget_mult"]
    b["slot_mult"] = slot_mult
    b["quality_mult"] = quality_mult
    b["budget_mult"] = budget_mult

    socket_cost = tables["item_budget_socket_cost"]
    socket_count = 0
    socket_discount = 1.0
    for n in (1, 2, 3):
        color = item_row.get(f"socketColor_{n}", 0)
        if not color:
            continue
        socket_count += 1
        cost_row = socket_cost.get((color,))
        socket_discount *= cost_row["discount"] if cost_row else 1.0
    b["socket_count"] = socket_count
    b["socket_discount"] = socket_discount

    is_set_piece = bool(item_row.get("itemset"))
    set_discount_row = tables["item_budget_set_discount"].get((1,))
    set_discount = (set_discount_row["discount"] if set_discount_row else 0.9) if is_set_piece else 1.0
    b["is_set_piece"] = is_set_piece
    b["set_discount"] = set_discount

    effective_mult = budget_mult * socket_discount * set_discount
    budget = _round(curve_row["budget"] * slot_mult * quality_mult * effective_mult)
    b["effective_mult"] = effective_mult
    b["budget"] = budget

    stamina_cost_row = tables["item_stat_cost"].get((ITEM_MOD_STAMINA,))
    stamina_cost = stamina_cost_row["cost"] if stamina_cost_row else 1.0

    baseline_stamina = _round(stamina_curve_row["stamina"] * slot_mult * quality_mult)
    stamina_delta = assign_row["stamina_delta"]
    b["baseline_stamina"] = baseline_stamina
    b["stamina_delta"] = stamina_delta
    b["final_stamina"] = max(0, baseline_stamina + stamina_delta)

    # Armor: off-budget like Stamina, own slot/quality multipliers, never
    # funded from the budget - see docs/itemization-changes.md §9.3a.
    armor_delta = assign_row["armor_delta"]
    armor_curve_row = tables["item_armor_curve"].get((ilvl, sub_class))
    armor_slot_row = tables["item_armor_slot_mult"].get((inv_type,))
    armor_qual_row = tables["item_armor_quality_mult"].get((quality,))
    has_armor_curve = item_class == ITEM_CLASS_ARMOR and armor_curve_row and armor_slot_row and armor_qual_row
    b["armor_delta"] = armor_delta
    b["has_armor_curve"] = bool(has_armor_curve)
    if has_armor_curve:
        b["armor_class"] = sub_class
        baseline_armor = _round(armor_curve_row["armor"] * armor_slot_row["mult"] * armor_qual_row["mult"])
        b["baseline_armor"] = baseline_armor
        b["final_armor"] = max(0, baseline_armor + armor_delta)

    effective_budget = float(budget) - (stamina_delta * stamina_cost)

    b["dps_delta"] = 0.0
    b["baseline_dps"] = 0.0
    b["final_dps"] = 0.0
    b["dmg_min"] = 0.0
    b["dmg_max"] = 0.0
    if b["is_weapon"]:
        dps_row = tables["item_weapon_dps_curve"].get((ilvl, quality))
        if dps_row:
            dps_cost_row = tables["item_weapon_dps_cost"].get((1,))
            dps_spread_row = tables["item_weapon_dps_spread"].get((1,))
            weapon_dps_cost = dps_cost_row["cost"] if dps_cost_row else 1.0
            weapon_dps_spread = dps_spread_row["spread"] if dps_spread_row else 0.3

            baseline_dps = dps_row["dps"]
            dps_delta = assign_row["dps_delta"]
            final_dps = max(0.0, baseline_dps + dps_delta)
            effective_budget -= dps_delta * weapon_dps_cost

            avg_damage = final_dps * (item_row.get("delay", 0) / 1000.0)
            b["baseline_dps"] = baseline_dps
            b["dps_delta"] = dps_delta
            b["final_dps"] = final_dps
            b["dmg_min"] = avg_damage * (1.0 - weapon_dps_spread / 2.0)
            b["dmg_max"] = avg_damage * (1.0 + weapon_dps_spread / 2.0)

    if effective_budget < 0.0:
        effective_budget = 0.0
    b["effective_budget"] = _round(effective_budget)

    stat_cost_table = tables["item_stat_cost"]
    working = []
    floor_sum = 0
    exact_sum = 0.0
    for stat_row in template_stats:
        stat_type = stat_row["stat_type"]
        alloc = stat_row["alloc"]
        cost_row = stat_cost_table.get((stat_type,))
        cost = cost_row["cost"] if cost_row else 1.0
        is_primary = bool(cost_row["is_primary"]) if cost_row else False

        raw_budget = effective_budget * (alloc / 10000.0)
        exact = raw_budget / cost if cost > 0.0 else 0.0
        floor = math.floor(exact)
        working.append({
            "stat_type": stat_type, "is_primary": is_primary, "alloc": alloc,
            "exact": exact, "floor": int(floor), "remainder": exact - floor,
        })
        floor_sum += int(floor)
        exact_sum += exact

    target = _round(exact_sum)
    remainder = max(0, target - floor_sum)
    b["rounding_remainder_points"] = remainder

    order = sorted(range(len(working)), key=lambda i: working[i]["remainder"], reverse=True)
    for i in order[:remainder]:
        working[i]["floor"] += 1

    b["stats"] = [
        {"stat_type": w["stat_type"], "is_primary": w["is_primary"], "alloc": w["alloc"],
         "raw": w["exact"], "rounded": w["floor"]}
        for w in working
    ]

    return b


def materialized_item_fields(breakdown: dict) -> dict:
    """The `item_template` columns `ApplyItemBudgetAllocation()` actually
    overwrites, given a `compute_breakdown()` result - `stat_typeN`/
    `stat_valueN` for N in 1..10 (stats then Stamina, zero-padded), `armor`
    if `has_armor_curve`, and `dmg_min1`/`dmg_max1` if it's a weapon with a
    resolved DPS curve entry. Doesn't touch anything else (spell slots are a
    separate concern - see `absorb_spell_fields()`)."""
    fields: dict = {}
    slot = 1
    for stat in breakdown["stats"]:
        fields[f"stat_type{slot}"] = stat["stat_type"]
        fields[f"stat_value{slot}"] = stat["rounded"]
        slot += 1

    fields[f"stat_type{slot}"] = ITEM_MOD_STAMINA
    fields[f"stat_value{slot}"] = breakdown["final_stamina"]
    slot += 1

    for clear in range(slot, MAX_ITEM_PROTO_STATS + 1):
        fields[f"stat_type{clear}"] = 0
        fields[f"stat_value{clear}"] = 0

    if breakdown["has_armor_curve"]:
        fields["armor"] = breakdown["final_armor"]

    if breakdown["is_weapon"] and (breakdown["dmg_min"] > 0.0 or breakdown["dmg_max"] > 0.0):
        fields["dmg_min1"] = breakdown["dmg_min"]
        fields["dmg_max1"] = breakdown["dmg_max"]

    return fields


def absorb_spell_fields(absorbed_spell_slots: int) -> dict:
    """The `item_template` columns cleared for each bit set in
    `absorbed_spell_slots` - mirrors `ApplyItemBudgetAllocation()`'s spell-
    slot-clearing loop exactly (`spellid_N`/`spelltrigger_N`/
    `spellcharges_N`/`spellppmRate_N`/`spellcooldown_N`/`spellcategory_N`/
    `spellcategorycooldown_N`, 1-indexed to match `Spells[N-1]`)."""
    fields: dict = {}
    for i in range(MAX_ITEM_PROTO_SPELLS):
        if not (absorbed_spell_slots & (1 << i)):
            continue
        n = i + 1
        fields[f"spellid_{n}"] = 0
        fields[f"spelltrigger_{n}"] = 0
        fields[f"spellcharges_{n}"] = 0
        fields[f"spellppmRate_{n}"] = 0.0
        fields[f"spellcooldown_{n}"] = -1
        fields[f"spellcategory_{n}"] = 0
        fields[f"spellcategorycooldown_{n}"] = -1
    return fields
