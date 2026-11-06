"""
Item declarations resolved into ladder tiers (item-variants plan v2 s3 / s5.3, stage IV1): `expand()` takes every
`item(...)` of `source/items/` (`lib/dsl/items.py`), checks it against the live item rows and the itemization catalog,
gives each non-deferred tier its `item_template` entry (`lib/item_ids.py`) and works out, per tier, the item level,
quality, required level, flags, label and `item_itemization` row the emitters (IV2) write. Everything here is
read-only; the only file a full run writes from it is the lock (`ItemExpansion.lock_text`).

**Checks** (each message names the item key): the shapes exist, have the right kind and the secondary's rules hold
against the primary; `itemization="live"` has a live row; `base=` / `like=` exist; columns are real `item_template`
columns and none is a budget stat; one owner per entry (`item(base=X)` against `item_template(X)`, `items.csv` and
other items); the slot is budgetable (`item_slot_mult`) and an armor slot has an armor curve (a shield has none
until IV0b); per item, the tier item levels strictly increase (a WARNING when a tier lowers the quality); every
reference curve has each tier's item level and quality; and the budget resolves (`item_lib.budget.compute_breakdown`
on a stand-in row). A ladder name used by two different ladders is an ERROR.

**Itemization row per tier.** Shapes by name (`primary=None` is the Null shape; `secondary=None` takes the lowest-id
secondary shape whose rules pass, at `primary_share` 10000 it gets no budget). `primary_share` defaults to 6000 with
both shapes, 0 without a primary, 10000 without a secondary; `budget_mult` to 0.7 when the item has a Use / Equip /
Chance on hit effect (`spells=`, or a `keep_spells=True` stock item that has one), else 1.0. A `base=` item's stock
spell slots are cleared through `absorbed_spell_slots` unless `keep_spells=True` or `spells=` replaces them. The
`extra_*` fractions are resolved per tier against that tier's own baseline (Stamina, armor, weapon DPS, block value),
rounded as `item_itemization` stores them. `itemization="live"` keeps the live row exactly on the first tier; on the
higher tiers its absolute deltas become fractions of the first tier's baselines first, so they scale too.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

from . import item_ids
from .dsl import items as items_dsl

ITEM_CLASS_WEAPON = 2
ITEM_CLASS_ARMOR = 4
ARMOR_SUBCLASS_SHIELD = 6
ARMOR_CURVE_SUBCLASSES = (1, 2, 3, 4, 6)  # cloth, leather, mail, plate, shield: item_armor_curve.armor_class
SPELL_SLOTS = 5
ITEMIZATION_COLUMNS = (
    "budget_mult", "stamina_delta", "dps_delta", "absorbed_spell_slots", "armor_delta", "primary_shape_id",
    "secondary_shape_id", "primary_share", "block_value_delta",
)
REQUIRED_NEW_COLUMNS = ("class", "subclass", "InventoryType", "displayid")


def _item_lib():
    """apps/item-tools' `item_lib.budget` and `item_lib.shapes` (no file I/O of their own)."""
    from . import trainer_state  # noqa: PLC0415

    item_tools = str(trainer_state.REPO_ROOT / "apps" / "item-tools")
    if item_tools not in sys.path:
        sys.path.append(item_tools)
    from item_lib import budget, shapes  # noqa: PLC0415

    return budget, shapes


def load_itemization_tables() -> tuple[dict, dict]:
    """(tables, shape catalog): the replayed itemization tables (`item_lib.budget_overlay.get_all()`, base dump plus
    every migration, pending and module SQL) and `item_lib.shapes.catalog()` over them."""
    _, shapes = _item_lib()
    from item_lib import budget_overlay  # noqa: PLC0415

    tables = budget_overlay.get_all()
    return tables, shapes.catalog(tables)


def _int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


# ---------------------------------------------------------------------------------------------------------------------
# Result


@dataclass
class ResolvedTier:
    key: str
    tier: str
    label: str
    entry: int
    stock: bool  # the base= item's own stock entry (edited in place, never minted)
    ilvl: int
    quality: int
    required_level: int
    heroic_flag: bool
    variant_base: int | None  # the first tier's entry, None on the first tier itself
    itemization: dict  # ITEMIZATION_COLUMNS -> value
    columns: dict  # explicit item_template columns of this tier (the item's, then the tier's overrides)
    baselines: dict = field(default_factory=dict)  # stamina / armor / dps / block of this tier, for the deltas

    @property
    def writes_label(self) -> bool:
        """Heroic tiers get the client's own line from flag 0x8, so no label table entry (IV4)."""
        return not self.heroic_flag


@dataclass
class ResolvedItem:
    decl: items_dsl.ItemDecl
    source_row: dict  # the stock row of a base= item; {} for a new item (its row is defaults + like + columns)
    like_columns: dict  # LIKE_COLUMNS copied from like= (empty for base= items)
    inventory_type: int
    item_class: int
    subclass: int
    sockets: tuple[int, ...]  # the socket colors every tier carries
    tiers: list[ResolvedTier] = field(default_factory=list)


@dataclass
class ItemExpansion:
    items: list[ResolvedItem] = field(default_factory=list)
    ladders: dict[str, items_dsl.Ladder] = field(default_factory=dict)
    assignment: item_ids.Assignment | None = None
    lock_appended: list[str] = field(default_factory=list)
    lock_text: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def minted(self) -> list[tuple[int, str, str]]:
        return self.assignment.minted if self.assignment else []


# ---------------------------------------------------------------------------------------------------------------------
# Shapes and curves


def _shape_index(catalog: dict) -> dict[str, dict]:
    return {shape["name"]: shape for shape in catalog.values()}


def _find_shape(where: str, name: str, kind: int, index: dict, errors: list[str]) -> dict | None:
    _, shapes = _item_lib()
    shape = index.get(name)
    if shape is None:
        import difflib  # noqa: PLC0415

        close = difflib.get_close_matches(name, list(index), n=3)
        errors.append(f"{where}: no item_shape named {name!r}" + (f" (did you mean {close}?)" if close else ""))
        return None
    if shape["kind"] != kind:
        want = "primary" if kind == shapes.KIND_PRIMARY else "secondary"
        errors.append(f"{where}: item_shape {name!r} is not a {want} shape")
        return None
    return shape


def _baselines(tables: dict, ilvl: int, quality: int, inv_type: int, item_class: int, subclass: int) -> dict:
    """The tier's off-budget baselines, as `compute_breakdown` derives them (None where the item has none)."""
    budget, _ = _item_lib()
    out = {"stamina": None, "armor": None, "dps": None, "block": None}
    slot = tables["item_slot_mult"].get((inv_type,))
    qual = tables["item_quality_mult"].get((quality,))
    stamina = tables["item_stamina_curve"].get((ilvl,))
    if slot and qual and stamina:
        out["stamina"] = budget._round(stamina["stamina"] * slot["mult"] * qual["mult"])
    if item_class == ITEM_CLASS_ARMOR:
        curve = tables["item_armor_curve"].get((ilvl, subclass))
        armor_slot = tables["item_armor_slot_mult"].get((inv_type,))
        armor_qual = tables["item_armor_quality_mult"].get((quality,))
        if curve and armor_slot and armor_qual:
            out["armor"] = budget._round(curve["armor"] * armor_slot["mult"] * armor_qual["mult"])
        if subclass == ARMOR_SUBCLASS_SHIELD:
            block = tables["item_block_value_curve"].get((ilvl, quality))
            if block:
                out["block"] = budget._round(block["block_value"])
    if item_class == ITEM_CLASS_WEAPON:
        single = int(inv_type in budget.SINGLE_SLOT_INV_TYPES)
        dps = tables["item_weapon_dps_curve"].get((ilvl, quality, single))
        if dps:
            out["dps"] = float(dps["dps"])
    return out


def _curve_problems(tables: dict, ilvl: int, quality: int, inv_type: int, item_class: int, subclass: int,
                    sockets: int) -> list[str]:
    budget, _ = _item_lib()
    missing = []
    if (ilvl,) not in tables["item_budget_curve"]:
        missing.append(f"item_budget_curve has no ilvl {ilvl}")
    if (ilvl,) not in tables["item_stamina_curve"]:
        missing.append(f"item_stamina_curve has no ilvl {ilvl}")
    if (quality,) not in tables["item_quality_mult"]:
        missing.append(f"item_quality_mult has no Quality {quality}")
    if item_class == ITEM_CLASS_ARMOR and subclass in ARMOR_CURVE_SUBCLASSES:
        if (ilvl, subclass) not in tables["item_armor_curve"]:
            missing.append(f"item_armor_curve has no (ilvl {ilvl}, armor_class {subclass})")
        if (quality,) not in tables["item_armor_quality_mult"]:
            missing.append(f"item_armor_quality_mult has no Quality {quality}")
        if subclass == ARMOR_SUBCLASS_SHIELD and (ilvl, quality) not in tables["item_block_value_curve"]:
            missing.append(f"item_block_value_curve has no (ilvl {ilvl}, Quality {quality})")
    if item_class == ITEM_CLASS_WEAPON:
        single = int(inv_type in budget.SINGLE_SLOT_INV_TYPES)
        if (ilvl, quality, single) not in tables["item_weapon_dps_curve"]:
            missing.append(f"item_weapon_dps_curve has no (ilvl {ilvl}, Quality {quality}, single slot {single})")
    if sockets and (ilvl,) not in tables["item_gem_value_curve"]:
        missing.append(f"item_gem_value_curve has no ilvl {ilvl}")
    return missing


def _scaled(fraction: float, baseline) -> float:
    return fraction * baseline if baseline else 0.0


# ---------------------------------------------------------------------------------------------------------------------
# Resolution


def _stock_spell_slots(row: dict) -> int:
    return sum(1 << (n - 1) for n in range(1, SPELL_SLOTS + 1) if _int(row.get(f"spellid_{n}")))


def _socket_colors(row: dict) -> tuple[int, ...]:
    return tuple(_int(row.get(f"socketColor_{n}")) for n in range(1, 4) if _int(row.get(f"socketColor_{n}")))


def _resolve_item(
    decl: items_dsl.ItemDecl, live_rows: dict[int, dict], tables: dict, catalog: dict, shape_index: dict,
    columns: tuple[str, ...], errors: list[str], warnings: list[str],
) -> tuple[ResolvedItem, list[dict]] | None:
    """The item-level checks and the per-tier plan (entries are filled in later). Returns None when a check failed
    in a way that stops the tier plan (the errors say why)."""
    budget, shapes = _item_lib()
    where = decl.where
    start = len(errors)
    unknown = sorted(c for c in dict(decl.columns) if c not in columns)
    for tier_name, cols in decl.overrides:
        unknown += sorted(f"{c} (overrides[{tier_name!r}])" for c, _ in cols if c not in columns)
    if unknown:
        errors.append(f"{where}: no such item_template column(s): {', '.join(unknown)}")
    if decl.base is not None:
        source_row = live_rows.get(decl.base)
        if source_row is None:
            errors.append(f"{where}: base={decl.base} has no live item_template row (base dump plus migrations)")
            return None
        like_columns = {}
    else:
        like_row = {}
        if decl.like is not None:
            like_row = live_rows.get(decl.like)
            if like_row is None:
                errors.append(f"{where}: like={decl.like} has no live item_template row")
                return None
        like_columns = {c: like_row[c] for c in items_dsl.LIKE_COLUMNS if c in like_row}
        source_row = {}  # a new item copies only LIKE_COLUMNS (not the like= item's set, spells or sockets)
    explicit = dict(decl.columns)
    look = {**source_row, **like_columns, **explicit}
    if decl.base is None:
        missing = [c for c in REQUIRED_NEW_COLUMNS if c not in like_columns and c not in explicit]
        if missing:
            errors.append(f"{where}: a new item needs like=<stock entry> or the column(s) {', '.join(missing)}")
            return None
    inv_type, item_class = _int(look.get("InventoryType")), _int(look.get("class"))
    subclass = _int(look.get("subclass"))
    if decl.sockets is not None:
        sockets = decl.sockets
    else:
        sockets = _socket_colors(source_row) if decl.base is not None else ()

    if (inv_type,) not in tables["item_slot_mult"]:
        errors.append(f"{where}: InventoryType {inv_type} has no item_slot_mult row, so the slot is not budgetable")
    curved = item_class == ITEM_CLASS_ARMOR and subclass in ARMOR_CURVE_SUBCLASSES
    if curved:
        has_curve = any(k[1] == subclass for k in tables["item_armor_curve"])
        if not has_curve or (inv_type,) not in tables["item_armor_slot_mult"]:
            what = "a shield" if subclass == ARMOR_SUBCLASS_SHIELD else f"armor subclass {subclass}"
            errors.append(
                f"{where}: {what} in InventoryType {inv_type} has no armor curve (item_armor_curve armor_class "
                f"{subclass} / item_armor_slot_mult {inv_type})"
                + (" - shields wait for IV0b's shield armor curve" if subclass == ARMOR_SUBCLASS_SHIELD else "")
            )
        if "armor" in explicit or any("armor" in dict(cols) for _, cols in decl.overrides):
            errors.append(f"{where}: armor comes from the armor curve on this slot and cannot be passed")
    if decl.extra_armor and not curved:
        errors.append(f"{where}: extra_armor= needs a slot with an armor curve")
    if decl.extra_dps and item_class != ITEM_CLASS_WEAPON:
        errors.append(f"{where}: extra_dps= needs a weapon")
    if decl.extra_block and not (item_class == ITEM_CLASS_ARMOR and subclass == ARMOR_SUBCLASS_SHIELD):
        errors.append(f"{where}: extra_block= needs a shield")

    stock_slots = _stock_spell_slots(source_row) if decl.base is not None else 0
    if decl.keep_spells:
        has_effect = bool(stock_slots)
        absorbed = 0
    elif decl.spells is not None:
        has_effect = bool(decl.spells)
        absorbed = 0
    else:
        has_effect = False
        absorbed = stock_slots

    # The itemization row of the first tier (deltas are fractions until the tier is known).
    live_row = None
    if decl.itemization == "live":
        live_row = tables["item_itemization"].get((decl.base,))
        if live_row is None:
            errors.append(f"{where}: itemization=\"live\" but base={decl.base} has no live item_itemization row")
            return None
        primary_id, secondary_id = _int(live_row["primary_shape_id"]), _int(live_row["secondary_shape_id"])
        share, mult = _int(live_row["primary_share"]), float(live_row["budget_mult"])
        absorbed = _int(live_row["absorbed_spell_slots"])
    else:
        primary_name = decl.primary if decl.primary is not None else items_dsl.NULL_PRIMARY_SHAPE
        primary = _find_shape(f"{where} primary", primary_name, shapes.KIND_PRIMARY, shape_index, errors)
        if decl.secondary is not None:
            secondary = _find_shape(f"{where} secondary", decl.secondary, shapes.KIND_SECONDARY, shape_index, errors)
            if primary is not None and secondary is not None and not shapes.rules_satisfied(
                secondary, set(primary["stats"]),
            ):
                errors.append(
                    f"{where}: secondary shape {decl.secondary!r} does not go with primary {primary['name']!r} "
                    f"({shapes.rule_summary(secondary, {})})"
                )
        else:
            secondary = None
            if primary is not None:
                secondary = next((
                    s for _, s in sorted(catalog.items())
                    if s["kind"] == shapes.KIND_SECONDARY and shapes.rules_satisfied(s, set(primary["stats"]))
                ), None)
                if secondary is None:
                    errors.append(f"{where}: no secondary shape goes with primary {primary['name']!r}")
        if primary is None or secondary is None:
            return None
        primary_id, secondary_id = primary["shape_id"], secondary["shape_id"]
        if decl.primary_share is not None:
            share = decl.primary_share
        elif decl.primary is None:
            share = 0
        elif decl.secondary is None:
            share = 10000
        else:
            share = items_dsl.DEFAULT_SHARE_BOTH
        if decl.budget_mult is not None:
            mult = decl.budget_mult
        else:
            mult = items_dsl.EFFECT_BUDGET_MULT if has_effect else 1.0
    if len(errors) > start:
        return None

    # Tier levels, per item: the first tier takes the item's (or the stock row's) own.
    plans = []
    first = decl.ladder.tiers[0]
    for spec in decl.ladder.tiers:
        if spec.explicit:
            ilvl, quality, required = spec.ilvl, spec.quality, spec.required_level
        elif decl.base is not None:
            ilvl = decl.ilvl if decl.ilvl is not None else _int(source_row.get("ItemLevel"))
            quality = decl.quality if decl.quality is not None else _int(source_row.get("Quality"))
            required = (decl.required_level if decl.required_level is not None
                        else _int(source_row.get("RequiredLevel")))
        else:
            ilvl = decl.ilvl
            quality = decl.quality if decl.quality is not None else int(items_dsl.Quality.RARE)
            required = (decl.required_level if decl.required_level is not None
                        else max(1, ilvl - items_dsl.NEW_ITEM_LEVEL_GAP))
        plans.append({"spec": spec, "ilvl": ilvl, "quality": quality, "required": required,
                      "first": spec is first})
    for low, high in zip(plans, plans[1:]):
        if high["ilvl"] <= low["ilvl"]:
            errors.append(
                f"{where}: tier {high['spec'].name!r} (ilvl {high['ilvl']}) does not rise above tier "
                f"{low['spec'].name!r} (ilvl {low['ilvl']}); the ladder's levels must strictly increase"
            )
        if high["quality"] < low["quality"]:
            warnings.append(
                f"{where}: tier {high['spec'].name!r} lowers the quality ({low['quality']} -> {high['quality']})"
            )
    for plan in plans:
        if plan["spec"].deferred:
            continue
        for problem in _curve_problems(tables, plan["ilvl"], plan["quality"], inv_type, item_class, subclass,
                                       len(sockets)):
            errors.append(f"{where} tier {plan['spec'].name!r}: {problem}")
    if len(errors) > start:
        return None

    # Fractions of each delta: declared, or (live) the first tier's absolute delta over its baseline.
    fractions = {"stamina": decl.extra_stamina, "armor": decl.extra_armor, "dps": decl.extra_dps,
                 "block": decl.extra_block}
    if live_row is not None:
        first_base = _baselines(tables, plans[0]["ilvl"], plans[0]["quality"], inv_type, item_class, subclass)
        for name, column in (("stamina", "stamina_delta"), ("armor", "armor_delta"), ("dps", "dps_delta"),
                             ("block", "block_value_delta")):
            fractions[name] = float(live_row[column]) / first_base[name] if first_base[name] else 0.0
    resolved = ResolvedItem(
        decl=decl, source_row=source_row, like_columns=like_columns, inventory_type=inv_type,
        item_class=item_class, subclass=subclass, sockets=tuple(sockets),
    )
    tier_plans = []
    for plan in plans:
        spec = plan["spec"]
        if spec.deferred:
            continue
        base = _baselines(tables, plan["ilvl"], plan["quality"], inv_type, item_class, subclass)
        if live_row is not None and plan["first"]:
            itemization = {c: live_row[c] for c in ITEMIZATION_COLUMNS}
        else:
            itemization = {
                "budget_mult": mult,
                "stamina_delta": budget._round(_scaled(fractions["stamina"], base["stamina"])),
                "dps_delta": round(_scaled(fractions["dps"], base["dps"]), 4),
                "absorbed_spell_slots": absorbed,
                "armor_delta": budget._round(_scaled(fractions["armor"], base["armor"])),
                "primary_shape_id": primary_id,
                "secondary_shape_id": secondary_id,
                "primary_share": share,
                "block_value_delta": budget._round(_scaled(fractions["block"], base["block"])),
            }
        tier_columns = {**explicit, **decl.override_columns(spec.name)}
        # The budget must resolve on a stand-in row of this tier (the C++ would skip the item otherwise).
        stand_in = {**look, **tier_columns, "entry": decl.base or 0, "ItemLevel": plan["ilvl"],
                    "Quality": plan["quality"]}
        for n in range(1, 4):
            stand_in[f"socketColor_{n}"] = sockets[n - 1] if n <= len(sockets) else 0
        try:
            budget.compute_breakdown(stand_in, {"entry": stand_in["entry"], **itemization}, tables, catalog)
        except budget.BudgetError as error:
            errors.append(f"{where} tier {spec.name!r}: the budget does not resolve: {error}")
            continue
        tier_plans.append({
            "spec": spec, "ilvl": plan["ilvl"], "quality": plan["quality"], "required": plan["required"],
            "first": plan["first"], "itemization": itemization, "columns": tier_columns, "baselines": base,
        })
    if len(errors) > start:
        return None
    return resolved, tier_plans


def expand(
    declarations: list[dict], *, ids_cfg: dict, live_rows: dict[int, dict], columns: tuple[str, ...],
    items_csv_ids=(), item_template_decl_ids=(), tables_loader=load_itemization_tables,
    item_dbc_ids_loader=None, lock: item_ids.Lock | None = None, lock_path=item_ids.LOCK_PATH,
    today: str | None = None,
) -> ItemExpansion:
    """Resolves `declarations` (`dsl_classes["item_declarations"]`). `live_rows` are the live item_template rows by
    entry, `columns` its column names; `items_csv_ids` and `item_template_decl_ids` the entries other declarations
    own. `tables_loader` gives (tables, catalog) and runs only when an item is declared; `item_dbc_ids_loader` gives
    the live item_dbc ids a new id must skip (runs only when an id is minted). `lock` defaults to the file."""
    out = ItemExpansion()
    block = ids_cfg.get(item_ids.LOCK_BLOCK)
    decls = [entry["_decl"] for entry in declarations]
    try:
        if lock is None:
            lock = item_ids.load_lock(lock_path, block)
        elif block:
            lock = item_ids.parse_lock(lock.text, block)
    except item_ids.LockError as error:
        out.errors.append(f"items: {error}")
        return out
    if not decls and not lock.lines:
        out.lock_text = lock.text
        return out
    if block is None:
        out.errors.append(f"items: source/ids.yaml has no {item_ids.LOCK_BLOCK} block - minted item ids come from it")
        return out

    # One name per ladder object.
    for decl in decls:
        known = out.ladders.get(decl.ladder.name)
        if known is not None and known != decl.ladder:
            out.errors.append(
                f"item {decl.key!r}: ladder name {decl.ladder.name!r} is used by two different ladders"
            )
        out.ladders.setdefault(decl.ladder.name, decl.ladder)

    # One owner per entry: base= against item_template(), items.csv, other items and the item block.
    item_block = ids_cfg.get("item")
    csv_ids = {int(e) for e in items_csv_ids}
    edited = {int(e) for e in item_template_decl_ids}
    bases: dict[int, str] = {}
    for decl in decls:
        if decl.base is None:
            continue
        if decl.base in edited:
            out.errors.append(f"{decl.where}: base={decl.base} is also edited by item_template({decl.base}, ...); "
                              f"one owner per entry - move those columns into the item() declaration")
        if decl.base in csv_ids:
            out.errors.append(f"{decl.where}: base={decl.base} also has a source/items.csv row; one owner per entry")
        if item_block and item_block["start"] <= decl.base <= item_block["end"]:
            out.errors.append(f"{decl.where}: base={decl.base} is inside the custom item block, not a stock item")
        if decl.base in bases:
            out.errors.append(f"{decl.where}: base={decl.base} is already item {bases[decl.base]!r}'s")
        bases.setdefault(decl.base, decl.key)
    for line in lock.lines:
        if not line.base and (line.entry in csv_ids or line.entry in edited):
            out.errors.append(f"items: minted entry {line.entry} ({line.key} {line.tier}) is also declared by "
                              f"{'source/items.csv' if line.entry in csv_ids else 'item_template()'}")
    unowned = item_ids.unowned_block_entries(lock, live_rows, block)
    if unowned:
        out.errors.append(
            f"items: live item_template row(s) {', '.join(map(str, unowned[:20]))}"
            f"{' ...' if len(unowned) > 20 else ''} sit in the {item_ids.LOCK_BLOCK} block "
            f"({block['start']}-{block['end']}) but no {item_ids.LOCK_PATH.name} line owns them"
        )

    resolved_items: list[tuple[ResolvedItem, list[dict]]] = []
    if decls:
        tables, catalog = tables_loader()
        shape_index = _shape_index(catalog)
        for decl in decls:
            result = _resolve_item(decl, live_rows, tables, catalog, shape_index, columns, out.errors, out.warnings)
            if result is not None:
                resolved_items.append(result)

    # Ids: every declared, non-deferred tier (also of an item whose checks failed, so the retire guard does not
    # call a merely broken item "removed"; its lines are not appended while the run has errors anyway).
    wanted = []
    for decl in decls:
        first = next((t for t in decl.ladder.tiers if not t.deferred), None)
        for spec in decl.ladder.tiers:
            if spec.deferred:
                continue
            wanted.append(item_ids.Wanted(decl.key, spec.name, decl.base if spec is first else None))
    taken = set(live_rows) | csv_ids | edited
    needs_mint = any(w.base is None and (w.key, w.tier) not in lock.by_pair for w in wanted)
    if needs_mint and item_dbc_ids_loader is not None:
        taken |= set(item_dbc_ids_loader())
    assignment = item_ids.assign(lock, wanted, block, taken, live_rows, today)
    out.assignment = assignment
    out.errors += assignment.errors
    out.notes += assignment.notes

    for resolved, tier_plans in resolved_items:
        decl = resolved.decl
        if any((decl.key, p["spec"].name) not in assignment.entries for p in tier_plans):
            continue
        variant_base = None
        for plan in tier_plans:
            spec = plan["spec"]
            entry = assignment.entries[(decl.key, spec.name)]
            resolved.tiers.append(ResolvedTier(
                key=decl.key, tier=spec.name, label=spec.label, entry=entry,
                stock=decl.base is not None and entry == decl.base, ilvl=plan["ilvl"], quality=plan["quality"],
                required_level=plan["required"], heroic_flag=spec.heroic_flag, variant_base=variant_base,
                itemization=plan["itemization"], columns=plan["columns"], baselines=plan["baselines"],
            ))
            if variant_base is None:
                variant_base = entry
        out.items.append(resolved)

    if out.errors:
        out.lock_text = lock.text
        return out
    out.lock_appended = assignment.appended
    out.lock_text = item_ids.lock_text(lock, assignment.appended)
    if assignment.minted or assignment.bases:
        out.notes.append(
            f"items: {len(assignment.minted)} new item id(s) and {len(assignment.bases)} new stock base(s) for "
            f"{item_ids.LOCK_PATH.name} (a full run appends them; commit the file)"
        )
    return out


def summary_notes(expansion: ItemExpansion, check: bool) -> list[str]:
    """What `--check` (every new lock line) or a full run (a count) prints about the ids."""
    if expansion.assignment is None:
        return []
    notes = []
    tiers = sum(len(item.tiers) for item in expansion.items)
    if expansion.items:
        notes.append(f"items: {len(expansion.items)} item(s), {tiers} tier(s) on {len(expansion.ladders)} ladder(s)")
    if check:
        notes += [f"items: would append to {item_ids.LOCK_PATH.name}: {line}" for line in expansion.lock_appended]
    return notes
