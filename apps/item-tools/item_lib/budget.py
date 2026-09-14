"""
Python port of `ResolveBudget()`/`ApplyItemizationAllocation()`
(`src/server/game/Globals/ItemBudget.cpp`) - the shape-based itemization
system's actual runtime formula (see `docs/itemization-phase-2.md` §4-§7).
This is a SEPARATE implementation of the same math, not a call into the C++ -
keep the two in sync by hand if the formula ever changes; `ItemBudget.cpp`'s
`ResolveBudget()` is the source of truth this was ported from.

Pure functions - no file I/O of its own. Callers pass in the item's
`item_template` row (from `lib.overlay.get_rows()`), the itemization
reference/content tables (from `lib.budget_overlay.get_all()`), and the
assembled shape catalog (from `lib.shapes.catalog()`).
"""

from __future__ import annotations

import math

from . import shapes as shape_lib

ITEM_CLASS_WEAPON = 2
ITEM_CLASS_ARMOR = 4
ITEM_SUBCLASS_ARMOR_SHIELD = 6
ITEM_MOD_STAMINA = 7
MAX_ITEM_PROTO_STATS = 10
MAX_ITEM_PROTO_SPELLS = 5
MAX_ITEM_PROTO_SOCKETS = 3

# Hand category for the weapon DPS curve's is_single_slot key - paired-slot weapons
# (One-Hand/Main Hand/Off Hand) share their budget with a second item; single-slot
# weapons (Two-Hand/Ranged/Thrown/Relic) don't, and run ~1.30x the DPS at the same
# ilvl/quality for exactly that reason - see docs/itemization-phase-2.md §7.7.
SINGLE_SLOT_INV_TYPES = {15, 17, 25, 26, 28}


def _is_single_slot(inv_type: int) -> bool:
    return inv_type in SINGLE_SLOT_INV_TYPES


def _round(x: float) -> int:
    """C++'s std::lround: round-half-away-from-zero, not Python's
    round-half-to-even."""
    return math.floor(x + 0.5) if x >= 0 else math.ceil(x - 0.5)


class BudgetError(Exception):
    """Reference data required for this item is missing, or the chosen
    primary/secondary shape doesn't exist - mirrors ResolveBudget() returning
    false. The webui should show this as a plain message, not a stack trace;
    it's an expected state (e.g. previewing an item level that has no curve
    entry yet), same as the C++'s validation pass logging and skipping
    rather than crashing."""


def compute_breakdown(item_row: dict, itemization_row: dict, tables: dict[str, dict],
                       shape_catalog: dict[int, dict]) -> dict:
    """Mirrors `ResolveBudget()`. `item_row` is one `item_template` row
    (`lib.overlay.get_rows()`'s value shape). `itemization_row` is one
    `item_itemization` row - pass a dict with the real column names even for
    a not-yet-saved preview (`entry`/`budget_mult`/`stamina_delta`/
    `dps_delta`/`absorbed_spell_slots`/`armor_delta`/`primary_shape_id`/
    `secondary_shape_id`/`primary_share`/`block_value_delta`). `tables` is
    `lib.budget_overlay.get_all()`'s return value; `shape_catalog` is
    `lib.shapes.catalog()`'s.

    Returns a dict with the same shape as ItemBudget::Breakdown (see
    ItemBudget.h) using snake_case keys, plus `allocations`: a list of
    `{stat_type, is_primary, alloc, raw, rounded}` in primary-then-secondary
    rank order after the merged largest-remainder rounding.
    """
    entry = item_row["entry"]
    ilvl = item_row["ItemLevel"]
    quality = item_row["Quality"]
    inv_type = item_row["InventoryType"]
    item_class = item_row["class"]
    sub_class = item_row["subclass"]
    primary_shape_id = itemization_row["primary_shape_id"]
    secondary_shape_id = itemization_row["secondary_shape_id"]

    slot_mult_row = tables["item_slot_mult"].get((inv_type,))
    quality_mult_row = tables["item_quality_mult"].get((quality,))
    curve_row = tables["item_budget_curve"].get((ilvl,))
    stamina_curve_row = tables["item_stamina_curve"].get((ilvl,))
    primary_shape = shape_catalog.get(primary_shape_id)
    secondary_shape = shape_catalog.get(secondary_shape_id)

    missing = []
    if slot_mult_row is None:
        missing.append(f"item_slot_mult has no row for InventoryType {inv_type}")
    if quality_mult_row is None:
        missing.append(f"item_quality_mult has no row for Quality {quality}")
    if curve_row is None:
        missing.append(f"item_budget_curve has no row for ilvl {ilvl}")
    if stamina_curve_row is None:
        missing.append(f"item_stamina_curve has no row for ilvl {ilvl}")
    if primary_shape is None:
        missing.append(f"item_shape has no row for primary_shape_id {primary_shape_id}")
    if secondary_shape is None:
        missing.append(f"item_shape has no row for secondary_shape_id {secondary_shape_id}")
    if missing:
        raise BudgetError("; ".join(missing))

    b: dict = {
        "entry": entry,
        "primary_shape_id": primary_shape_id,
        "secondary_shape_id": secondary_shape_id,
        "primary_share": itemization_row["primary_share"],
        "item_level": ilvl,
        "quality": quality,
        "inventory_type": inv_type,
        "is_weapon": item_class == ITEM_CLASS_WEAPON,
    }

    slot_mult = slot_mult_row["mult"]
    quality_mult = quality_mult_row["mult"]
    budget_mult = itemization_row["budget_mult"]
    b["slot_mult"] = slot_mult
    b["quality_mult"] = quality_mult
    b["budget_mult"] = budget_mult

    is_set_piece = bool(item_row.get("itemset"))
    set_discount_row = tables["item_budget_set_discount"].get((1,))
    set_discount = (set_discount_row["discount"] if set_discount_row else 0.9) if is_set_piece else 1.0
    b["is_set_piece"] = is_set_piece
    b["set_discount"] = set_discount

    # Step 1 (docs/itemization-phase-2.md §4): base.
    base = curve_row["budget"] * slot_mult * quality_mult * budget_mult * set_discount

    # Step 2: budget = base - socket_count * GemValueCurve(ilvl) - socket_bonus_value.
    socket_count = sum(1 for n in (1, 2, 3) if item_row.get(f"socketColor_{n}", 0))
    gem_value = 0.0
    if socket_count > 0:
        gem_row = tables["item_gem_value_curve"].get((ilvl,))
        gem_value = gem_row["gem_budget"] if gem_row else 0.0
    socket_budget_cost = socket_count * gem_value
    # socketBonus pricing isn't implemented server-side either (SpellItemEnchantment DBC data
    # isn't resident in this database) - always 0, same as ItemBudget.cpp.
    socket_bonus_value = 0
    b["socket_count"] = socket_count
    b["socket_budget_cost"] = socket_budget_cost
    b["socket_bonus_value"] = socket_bonus_value

    budget = _round(base - socket_budget_cost - socket_bonus_value)
    b["budget"] = budget

    # Off-budget baselines: Stamina, Armor, Block Value - itemization-changes.md §9.3/§9.3a,
    # docs/itemization-phase-2.md §7.4. None of these are funded from the budget above.
    stamina_cost_row = tables["item_stat_cost"].get((ITEM_MOD_STAMINA,))
    stamina_cost = stamina_cost_row["cost"] if stamina_cost_row else 1.0

    baseline_stamina = _round(stamina_curve_row["stamina"] * slot_mult * quality_mult)
    stamina_delta = itemization_row["stamina_delta"]
    b["baseline_stamina"] = baseline_stamina
    b["stamina_delta"] = stamina_delta
    b["final_stamina"] = max(0, baseline_stamina + stamina_delta)

    armor_delta = itemization_row["armor_delta"]
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

    block_value_delta = itemization_row["block_value_delta"]
    block_value_row = tables["item_block_value_curve"].get((ilvl, quality))
    is_shield = item_class == ITEM_CLASS_ARMOR and sub_class == ITEM_SUBCLASS_ARMOR_SHIELD
    has_block_value_curve = is_shield and block_value_row is not None
    b["block_value_delta"] = block_value_delta
    b["has_block_value_curve"] = bool(has_block_value_curve)
    if has_block_value_curve:
        baseline_block_value = _round(block_value_row["block_value"])
        b["baseline_block_value"] = baseline_block_value
        b["final_block_value"] = max(0, baseline_block_value + block_value_delta)

    # Deltas that fund themselves out of the item's own budget (unlike Armor/Block Value's
    # deltas above, which are free additive knobs).
    effective_budget = float(budget) - (stamina_delta * stamina_cost)

    b["dps_delta"] = 0.0
    b["baseline_dps"] = 0.0
    b["final_dps"] = 0.0
    b["dmg_min"] = 0.0
    b["dmg_max"] = 0.0
    if b["is_weapon"]:
        dps_row = tables["item_weapon_dps_curve"].get((ilvl, quality, int(_is_single_slot(inv_type))))
        if dps_row:
            dps_cost_row = tables["item_weapon_dps_cost"].get((1,))
            dps_spread_row = tables["item_weapon_dps_spread"].get((1,))
            weapon_dps_cost = dps_cost_row["cost"] if dps_cost_row else 1.0
            weapon_dps_spread = dps_spread_row["spread"] if dps_spread_row else 0.3

            baseline_dps = dps_row["dps"]
            dps_delta = itemization_row["dps_delta"]
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

    # Step 3: two-sided split. secondary_budget is the exact complement of primary_budget (not
    # independently recomputed from a "secondary share"), so the two sides always sum back to
    # effective_budget with no rounding leak.
    # NOT effective_budget * (primary_share / 10000.0) -- matches ItemBudget.cpp's real operand
    # grouping (`effectiveBudget * static_cast<double>(row.PrimaryShare) / 10000.0`, left-to-right
    # at equal `*`/`/` precedence) exactly, since the two groupings round to different doubles for
    # some real inputs and this needs to match the live materializer bit-for-bit, not just
    # approximately -- confirmed necessary: entry 27713 rounds a secondary allocation differently
    # under the two groupings, right at a largest-remainder tiebreak boundary.
    primary_budget = effective_budget * b["primary_share"] / 10000.0
    secondary_budget = effective_budget - primary_budget
    b["primary_budget"] = primary_budget
    b["secondary_budget"] = secondary_budget

    # Step 4: allocate each side against its shape's ordered stat list and distribution. Every
    # rank goes through this exact same formula in the same order, so ranks that are supposed to
    # tie (Even trio/Lead-plus-two's equal-alloc ranks) produce bit-identical floats - §4.1.
    stat_cost_table = tables["item_stat_cost"]
    working = []

    def _allocate_side(shape: dict, side_budget: float, is_primary_side: bool):
        stats = shape["stats"]
        alloc = shape["alloc"]
        n = min(len(stats), len(alloc))  # a mismatch is already logged, §8 check 1
        for i in range(n):
            stat_type = stats[i]
            a = alloc[i]
            cost_row = stat_cost_table.get((stat_type,))
            cost = cost_row["cost"] if cost_row else 1.0

            raw = side_budget * (a / 10000.0)
            exact = raw / cost if cost > 0.0 else 0.0
            floor = math.floor(exact)
            working.append({
                "stat_type": stat_type, "is_primary": is_primary_side, "alloc": a,
                "exact": exact, "floor": int(floor), "remainder": exact - floor,
            })

    _allocate_side(primary_shape, primary_budget, True)
    _allocate_side(secondary_shape, secondary_budget, False)

    floor_sum = sum(w["floor"] for w in working)
    exact_sum = sum(w["exact"] for w in working)
    target = _round(exact_sum)
    remainder = max(0, target - floor_sum)
    b["rounding_remainder_points"] = remainder

    # Step 5: largest-remainder rounding, ONCE over the merged list of both sides. Explicit
    # tiebreak - ascending stat_type - as a secondary sort key: ties are common (any Even
    # pair/Lead-plus-two/Even trio shape produces exactly equal remainders on its
    # equal-allocation ranks), and a plain sort by remainder alone would leave the result
    # dependent on the sort implementation rather than on this rule - §4.1.
    order = sorted(range(len(working)), key=lambda i: (-working[i]["remainder"], working[i]["stat_type"]))
    for i in order[:remainder]:
        working[i]["floor"] += 1

    b["allocations"] = [
        {"stat_type": w["stat_type"], "is_primary": w["is_primary"], "alloc": w["alloc"],
         "raw": w["exact"], "rounded": w["floor"]}
        for w in working
    ]

    return b


def materialized_item_fields(breakdown: dict) -> dict:
    """The `item_template` columns `ApplyItemizationAllocation()` actually
    overwrites, given a `compute_breakdown()` result - `stat_typeN`/
    `stat_valueN` for N in 1..10 (primary-then-secondary allocations then
    Stamina, zero-padded), `armor` if `has_armor_curve`, `block` if
    `has_block_value_curve`, and `dmg_min1`/`dmg_max1` if it's a weapon with
    a resolved DPS curve entry. Doesn't touch anything else (spell slots are
    a separate concern - see `absorb_spell_fields()`)."""
    fields: dict = {}
    slot = 1
    for alloc in breakdown["allocations"]:
        fields[f"stat_type{slot}"] = alloc["stat_type"]
        fields[f"stat_value{slot}"] = alloc["rounded"]
        slot += 1

    fields[f"stat_type{slot}"] = ITEM_MOD_STAMINA
    fields[f"stat_value{slot}"] = breakdown["final_stamina"]
    slot += 1

    for clear in range(slot, MAX_ITEM_PROTO_STATS + 1):
        fields[f"stat_type{clear}"] = 0
        fields[f"stat_value{clear}"] = 0

    if breakdown["has_armor_curve"]:
        fields["armor"] = breakdown["final_armor"]

    if breakdown["has_block_value_curve"]:
        fields["block"] = breakdown["final_block_value"]

    if breakdown["is_weapon"] and (breakdown["dmg_min"] > 0.0 or breakdown["dmg_max"] > 0.0):
        fields["dmg_min1"] = breakdown["dmg_min"]
        fields["dmg_max1"] = breakdown["dmg_max"]

    return fields


def absorb_spell_fields(absorbed_spell_slots: int) -> dict:
    """The `item_template` columns cleared for each bit set in
    `absorbed_spell_slots` - mirrors `ApplyItemizationAllocation()`'s spell-
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


def display_row(entry: int, item_row: dict, tables: dict[str, dict], shape_catalog: dict[int, dict]) -> dict:
    """`item_row` with its stat_typeN/stat_valueN/armor/block/dmg_min1/
    dmg_max1 columns replaced by what the shape-based system actually
    materializes for this item at server boot, for an item with a real
    `item_itemization` row. Needed anywhere this tool shows "what does this
    item actually grant" rather than "what's literally stored": materialization
    happens in memory only (`ApplyItemizationAllocation()` overwrites the
    runtime `ItemTemplateContainer`, never the database) - see
    `docs/itemization-phase-2.md`'s `ItemBudget.h` header comment - so the
    database row for an assigned item is stale by design, not a bug in this
    tool's own overlay reader. Confirmed necessary: `lib/loot.py`'s dungeon/
    raid drop browser was showing the literal (pre-shape) stat line for every
    assigned item until this was wired in. Returns `item_row` unchanged for
    an item with no `item_itemization` row - its literal columns really are
    what it grants - or if `compute_breakdown()` can't resolve it (same
    reference-data gaps `BudgetError` already covers elsewhere)."""
    itemization_row = tables["item_itemization"].get((entry,))
    if itemization_row is None:
        return item_row
    try:
        breakdown = compute_breakdown(item_row, itemization_row, tables, shape_catalog)
    except BudgetError:
        return item_row
    return {**item_row, **materialized_item_fields(breakdown)}


def eligible_secondary_shapes(primary_shape: dict, shape_catalog: dict[int, dict]) -> list[dict]:
    """Every secondary shape whose rules pass against `primary_shape`'s own
    stat set - for the item form's secondary-shape dropdown. Mirrors
    ItemBudget.cpp's SecondaryShapeRulesSatisfied(), via lib.shapes."""
    primary_stat_set = set(primary_shape["stats"])
    return [
        shape for shape in shape_catalog.values()
        if shape["kind"] == shape_lib.KIND_SECONDARY and shape_lib.rules_satisfied(shape, primary_stat_set)
    ]
