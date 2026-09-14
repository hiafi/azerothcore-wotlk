"""
Assembles the shape catalog (`item_shape`/`item_shape_stat`/`item_shape_rule`/
`item_alloc_dist`) from `lib.budget_overlay.get_all()`'s raw table rows into
the shape of `src/server/game/Globals/ItemBudget.cpp`'s in-memory `_shapes`/
`_shapeStats`/`_shapeRules`/`_dist` maps - see docs/itemization-phase-2.md §3.

Unlike every reference/curve table this tool already reads (item_budget_curve,
item_stat_cost, ...), the shape catalog is NOT edited through this tool at
all - it's a fixed, curated catalog (24 primary + 46 secondary shapes as of
this writing), authored by hand-written regression-backed migrations the same
way item_budget_curve is (see apps/item-tools/README.md's "read-only here"
note on curve tables) - lib/shapes.py exists purely to *read* it for display
(the item form's primary/secondary shape dropdowns, the /shapes browse page)
and for `lib.budget`'s rule validation, not to write it.
"""

from __future__ import annotations

KIND_PRIMARY = 0
KIND_SECONDARY = 1

RULE_REQUIRES_ANY = 1
RULE_FORBIDS = 2

RULE_TYPE_NAMES = {RULE_REQUIRES_ANY: "requires any of", RULE_FORBIDS: "forbids"}


def _dist_alloc(tables: dict) -> dict[int, list[int]]:
    """dist_id -> [alloc, ...] in rank order (1-indexed ranks, list is 0-indexed)."""
    by_dist: dict[int, dict[int, int]] = {}
    for (dist_id, rank), row in tables["item_alloc_dist"].items():
        by_dist.setdefault(dist_id, {})[rank] = row["alloc"]
    return {dist_id: [ranks[r] for r in sorted(ranks)] for dist_id, ranks in by_dist.items()}


def _shape_stats(tables: dict) -> dict[int, list[int]]:
    """shape_id -> [stat_type, ...] in rank order."""
    by_shape: dict[int, dict[int, int]] = {}
    for (shape_id, rank), row in tables["item_shape_stat"].items():
        by_shape.setdefault(shape_id, {})[rank] = row["stat_type"]
    return {shape_id: [ranks[r] for r in sorted(ranks)] for shape_id, ranks in by_shape.items()}


def _shape_rules(tables: dict) -> dict[int, list[tuple[int, int]]]:
    """shape_id -> [(rule_type, stat_type), ...]."""
    by_shape: dict[int, list[tuple[int, int]]] = {}
    for (shape_id, rule_type, stat_type), _row in tables["item_shape_rule"].items():
        by_shape.setdefault(shape_id, []).append((rule_type, stat_type))
    return by_shape


def catalog(tables: dict) -> dict[int, dict]:
    """Every shape_id (primary and secondary together) -> {name, kind,
    dist_id, dist_name, stats: [stat_type,...], alloc: [ten-thousandths,...]
    (parallel to stats, rank order), rules: [(rule_type, stat_type),...]}."""
    dist_alloc = _dist_alloc(tables)
    dist_names = {dist_id: row["name"] for (dist_id,), row in tables["item_alloc_dist_name"].items()}
    stats_by_shape = _shape_stats(tables)
    rules_by_shape = _shape_rules(tables)

    out: dict[int, dict] = {}
    for (shape_id,), row in tables["item_shape"].items():
        dist_id = row["dist_id"]
        stats = stats_by_shape.get(shape_id, [])
        alloc = dist_alloc.get(dist_id, [])
        out[shape_id] = {
            "shape_id": shape_id,
            "name": row["name"],
            "kind": row["kind"],
            "dist_id": dist_id,
            "dist_name": dist_names.get(dist_id, f"dist {dist_id}"),
            "stats": stats,
            "alloc": alloc[:len(stats)],
            "rules": rules_by_shape.get(shape_id, []),
        }
    return out


def primary_shapes(tables: dict) -> dict[int, dict]:
    return {sid: s for sid, s in catalog(tables).items() if s["kind"] == KIND_PRIMARY}


def secondary_shapes(tables: dict) -> dict[int, dict]:
    return {sid: s for sid, s in catalog(tables).items() if s["kind"] == KIND_SECONDARY}


def rules_satisfied(shape: dict, primary_stat_set: set[int]) -> bool:
    """Mirrors ItemBudget.cpp's SecondaryShapeRulesSatisfied(): a shape with
    no rules is universally eligible; otherwise every `forbids` must hold and
    at least one `requires_any` (if any exist) must match `primary_stat_set`
    (the CHOSEN primary shape's own stat set, not this secondary shape's)."""
    rules = shape["rules"]
    if not rules:
        return True
    has_requires_any = False
    any_matched = False
    for rule_type, stat_type in rules:
        if rule_type == RULE_REQUIRES_ANY:
            has_requires_any = True
            if stat_type in primary_stat_set:
                any_matched = True
        elif rule_type == RULE_FORBIDS:
            if stat_type in primary_stat_set:
                return False
    return (not has_requires_any) or any_matched


def rule_stat_lists(shape: dict) -> tuple[list[int], list[int]]:
    """(requires_any stat types, forbids stat types) - flat lists, for
    embedding into an HTML data-attribute so client-side JS can re-evaluate
    rules_satisfied() without re-implementing the (rule_type, stat_type)
    tuple shape itself."""
    requires_any = [st for rt, st in shape["rules"] if rt == RULE_REQUIRES_ANY]
    forbids = [st for rt, st in shape["rules"] if rt == RULE_FORBIDS]
    return requires_any, forbids


def stat_percentages(shape: dict) -> list[tuple[int, float]]:
    """[(stat_type, percent), ...] for display - alloc is ten-thousandths."""
    return [(st, a / 100.0) for st, a in zip(shape["stats"], shape["alloc"])]


def rule_summary(shape: dict, item_mod_names: dict[int, str]) -> str:
    """One-line human description of a shape's rules, e.g. 'requires any of
    Strength, Agility' or 'forbids Spirit' - empty string if none. Multiple
    rules of the same type are grouped into one phrase."""
    by_type: dict[int, list[str]] = {}
    for rule_type, stat_type in shape["rules"]:
        by_type.setdefault(rule_type, []).append(item_mod_names.get(stat_type, str(stat_type)))
    return "; ".join(
        f"{RULE_TYPE_NAMES.get(rule_type, rule_type)} {', '.join(names)}"
        for rule_type, names in by_type.items()
    )
