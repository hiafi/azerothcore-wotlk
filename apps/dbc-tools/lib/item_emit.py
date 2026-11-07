"""
Item variants emission (item-variants plan v2 s5, stage IV2): turns `item_variants.expand()`'s resolved tiers into
the rows a run writes, and renders the ones that differ from the replayed live state.

Per tier (`ResolvedTier`):

- **`item_template`.** A minted entry gets a full row: the stock row of a `base=` item (copied), or the schema
  defaults plus `like=` columns plus the item's own columns for a new item; then the tier's item level, quality,
  required level, name, flags (`0x8` on a `heroic_flag` tier, cleared elsewhere), sockets and spells; then the stats
  the budget materializes (`item_lib.budget.compute_breakdown` + `materialized_item_fields`). Rendered as a full-row
  upsert (`sql_out.render_upsert_block`; `item_template` is on the SQL linter's do-not-delete list). A `base=` stock
  entry (the first tier) gets a column-limited edit of the columns it owns (s5.1): the stat lines, `armor` on a curved
  slot, `block` on a shield, `dmg_min1` / `dmg_max1` on a weapon, and only when declared its item level, quality,
  required level, name, sockets, spells and explicit columns. That row joins `dsl_classes["item_templates"]`, so it
  goes out through the existing `item_template()` path (`spell_tables.render_item_blocks`, diffed against the
  replayed row, reported if a later run drops it).
- **`item_itemization`** and **`item_budget_variant`** (with its `tier` column): keyed blocks, `DELETE ... WHERE
  entry IN (<changed>)` + INSERT, only for rows that differ from the replayed live row (s5.2). No block DELETE, no
  prune: a stock entry's row is never deleted, only rewritten.
- **`item_dbc` / client `Item.dbc`**: `source/items.csv`-shaped entries (`build.build_item_row`'s input) for every
  minted entry, every retired lock line (from the 7 fields on the line) and a stock entry whose declared columns
  change one of the 7 Item.dbc fields. `generate.py` merges them into the items.csv entries, so the existing item
  block (`DELETE ... BETWEEN 70000 AND 79999` + INSERT, and the patch-Z merge) carries them. A duplicate id is an
  ERROR.
- **Tier labels** (`ItemEmission.labels`, entry -> label) for IV4's `ItemTierLabels.lua`: every tier except a
  `heroic_flag` one (the client prints "Heroic" from flag 0x8 itself), plus every retired lock line that carries a
  label (players keep the item, so they keep the line).

**Stat lines.** The materialized stat lines leave out every line whose value is 0 (a `secondary=None` item's
zero-budget secondary, a Stamina line that rounds to 0): `budget.materialized_item_fields` and the server's own
boot-time materializer (`ItemBudget.cpp` `ApplyItemizationAllocation`) both skip such a line (R1 S6), so the database
row and the item the client sees agree.

**Sockets** are the item's on every tier except a `tier(sockets=False)` one (user ruling 2026-11-06: the leveling
Normal tier has none, they ate its whole budget), which writes no socket, no socket bonus and so gets no socket
discount. On a stock entry the socket columns are owned only when declared or cleared that way.

**Durability.** A minted tier gets `ResolvedTier.max_durability` (the median of live items of its class, subclass,
slot and quality near its item level, else the donor's; `lib/item_variants.py`), unless it declares `MaxDurability`.
Prices and disenchanting stay the copied / schema values for now (IV9).

**Spells.** A minted tier of a `base=` item has the stock spell slots that `absorbed_spell_slots` folds into the
budget cleared in its row (`budget.absorb_spell_fields`, what the server does in memory). The stock entry itself
keeps them in the database (the server clears them at boot), so `keep_spells=True` can still bring them back.

A second run over the replayed overlay (the first run's pending file applied) renders nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import item_variants, spell_tables, sql_out
from .dsl import items as items_dsl

TEMPLATE_SPEC = spell_tables.ITEM_TABLES[0]
ITEMIZATION_TABLE = "item_itemization"
ITEMIZATION_COLUMNS = ("entry", *item_variants.ITEMIZATION_COLUMNS)
VARIANT_TABLE = "item_budget_variant"
VARIANT_COLUMNS = ("entry", "base_entry", "tier")
STAT_COLUMNS = tuple(c for n in range(1, 11) for c in (f"stat_type{n}", f"stat_value{n}"))
SOCKET_COLUMNS = (
    *(c for n in range(1, 4) for c in (f"socketColor_{n}", f"socketContent_{n}")), "socketBonus",
)
SPELL_PARTS = ("id", "trigger", "charges", "ppmRate", "cooldown", "category", "categorycooldown")
SPELL_COLUMNS = tuple(f"spell{part}_{n}" for n in range(1, 6) for part in SPELL_PARTS)
# source/items.csv field -> item_template column: the 7 Item.dbc fields (lib/item_ids.RETIRED_DBC_COLUMNS' set).
DBC_FIELDS = (
    ("class_id", "class"), ("subclass_id", "subclass"), ("sound_override_subclass_id", "SoundOverrideSubclass"),
    ("material", "Material"), ("display_info_id", "displayid"), ("inventory_type", "InventoryType"),
    ("sheathe_type", "sheath"),
)
# Columns compute_breakdown keys reference tables on: coerced to int (the replay can hand back a float).
_BREAKDOWN_INT_COLUMNS = (
    "entry", "ItemLevel", "Quality", "InventoryType", "class", "subclass", "itemset", "delay",
    "socketColor_1", "socketColor_2", "socketColor_3",
)


def _budget():
    item_variants._item_lib()
    from item_lib import budget  # noqa: PLC0415

    return budget


def _int(value) -> int:
    return item_variants._int(value)


# ---------------------------------------------------------------------------------------------------------------------
# Result


@dataclass
class TierRows:
    tier: item_variants.ResolvedTier
    row: dict  # the full item_template row this tier should have
    owned: tuple[str, ...] | None  # a stock entry's owned columns; None for a minted entry (the whole row)
    stats: dict  # the materialized columns (stat lines without zero values, armor, block, damage)
    breakdown: dict  # compute_breakdown's result for `row`


@dataclass
class ItemEmission:
    tiers: list[TierRows] = field(default_factory=list)
    template_rows: list[dict] = field(default_factory=list)  # minted entries, full rows
    template_edits: list[dict] = field(default_factory=list)  # stock entries, `_update_columns` rows
    itemization_rows: list[dict] = field(default_factory=list)
    variant_rows: list[dict] = field(default_factory=list)
    dbc_entries: list[dict] = field(default_factory=list)  # source/items.csv-shaped
    labels: dict[int, str] = field(default_factory=dict)  # entry -> tooltip label (IV4)
    errors: list[str] = field(default_factory=list)

    def by_entry(self) -> dict[int, TierRows]:
        return {t.tier.entry: t for t in self.tiers}


# ---------------------------------------------------------------------------------------------------------------------
# Rows


def materialized_stat_fields(breakdown: dict) -> dict:
    """`budget.materialized_item_fields`: the stat lines (0-value lines left out, as the C++ does), armor, block and
    weapon damage the budget writes."""
    return _budget().materialized_item_fields(breakdown)


def _spell_columns(spells: tuple[items_dsl.ItemSpell, ...]) -> dict:
    empty = items_dsl.ItemSpell(0, 0)
    out = {}
    for slot in range(1, items_dsl.MAX_SPELLS + 1):
        out.update((spells[slot - 1] if slot <= len(spells) else empty).columns(slot))
    return out


def _socket_columns(sockets: tuple[int, ...], bonus: int | None) -> dict:
    out = {}
    for n in range(1, 4):
        out[f"socketColor_{n}"] = sockets[n - 1] if n <= len(sockets) else 0
        out[f"socketContent_{n}"] = 0
    out["socketBonus"] = bonus or 0
    return out


def _breakdown(row: dict, itemization: dict, tables: dict, catalog: dict) -> dict:
    budget = _budget()
    item_row = dict(row)
    for column in _BREAKDOWN_INT_COLUMNS:
        item_row[column] = _int(item_row.get(column))
    return budget.compute_breakdown(item_row, itemization, tables, catalog)


def _tier_row(item: item_variants.ResolvedItem, tier: item_variants.ResolvedTier, defaults: dict,
              columns: tuple[str, ...]) -> tuple[dict, list[str]]:
    """The tier's item_template row before the stats, and the columns the declaration sets on it."""
    decl = item.decl
    if decl.base is not None:
        row = {c: item.source_row.get(c, defaults.get(c)) for c in columns}
    else:
        row = {c: defaults.get(c) for c in columns}
        row.update(item.like_columns)
    declared = dict(tier.columns)
    row.update(declared)
    set_columns = list(declared)
    row["entry"] = tier.entry
    if decl.name is not None:
        row["name"] = decl.name
        set_columns.append("name")
    level_given = decl.ilvl is not None or decl.quality is not None or decl.required_level is not None
    row["ItemLevel"], row["Quality"], row["RequiredLevel"] = tier.ilvl, tier.quality, tier.required_level
    if not (tier.stock and not level_given):
        set_columns += ["ItemLevel", "Quality", "RequiredLevel"]
    flags = _int(row.get("Flags"))
    flags = flags | items_dsl.HEROIC_TOOLTIP_FLAG if tier.heroic_flag else flags & ~items_dsl.HEROIC_TOOLTIP_FLAG
    if flags != _int(row.get("Flags")) or not tier.stock:
        row["Flags"] = flags
        set_columns.append("Flags")
    if not tier.sockets:
        # tier(sockets=False): no sockets, no bonus, so no socket discount in the budget either.
        if decl.sockets is not None or any(_int(row.get(c)) for c in SOCKET_COLUMNS):
            row.update(_socket_columns((), None))
            set_columns += SOCKET_COLUMNS
    elif decl.sockets is not None:
        row.update(_socket_columns(decl.sockets, decl.socket_bonus))
        set_columns += SOCKET_COLUMNS
    if not tier.stock and tier.max_durability is not None:
        row["MaxDurability"] = tier.max_durability  # R1 S2: a minted tier's durability from live data
    if decl.spells is not None:
        row.update(_spell_columns(decl.spells))
        set_columns += SPELL_COLUMNS
    elif not tier.stock:
        # A minted copy of a stock item: the spells the budget absorbs are cleared, as the server does in memory.
        row.update(_budget().absorb_spell_fields(_int(tier.itemization["absorbed_spell_slots"])))
    return row, set_columns


def _dbc_entry(entry: int, row: dict, note: str) -> dict:
    out = {"id": int(entry), "notes": note}
    for field_name, column in DBC_FIELDS:
        out[field_name] = _int(row.get(column))
    return out


def build(
    expansion: item_variants.ItemExpansion, *, columns: tuple[str, ...] = spell_tables.ITEM_TEMPLATE_COLUMNS,
    defaults: dict | None = None,
) -> ItemEmission:
    """Every row the resolved tiers own (unrendered, undiffed). Budget problems come back as `errors`."""
    budget = _budget()
    defaults = spell_tables.ITEM_TEMPLATE_DEFAULTS if defaults is None else defaults
    out = ItemEmission()
    for item in expansion.items:
        decl = item.decl
        for tier in item.tiers:
            where = f"{decl.where} tier {tier.tier!r} (entry {tier.entry})"
            row, set_columns = _tier_row(item, tier, defaults, columns)
            itemization = {"entry": tier.entry, **tier.itemization}
            try:
                breakdown = _breakdown(row, itemization, expansion.tables, expansion.catalog)
            except budget.BudgetError as error:
                out.errors.append(f"{where}: the budget does not resolve: {error}")
                continue
            if len(breakdown["allocations"]) + 1 > budget.MAX_ITEM_PROTO_STATS:
                out.errors.append(f"{where}: {len(breakdown['allocations'])} stats plus Stamina exceed the "
                                  f"{budget.MAX_ITEM_PROTO_STATS} stat slots")
                continue
            stats = materialized_stat_fields(breakdown)
            row.update(stats)
            if tier.stock:
                owned = tuple(dict.fromkeys(c for c in (*STAT_COLUMNS, *stats, *set_columns) if c != "entry"))
                edit = dict(row)
                edit.update(id=tier.entry, _update_columns=owned, _source_class="items")
                out.template_edits.append(edit)
                if any(column in set_columns for _, column in DBC_FIELDS):
                    out.dbc_entries.append(_dbc_entry(tier.entry, row, f"{decl.key} {tier.tier} (stock, edited)"))
            else:
                owned = None
                out.template_rows.append(dict(row))
                out.dbc_entries.append(_dbc_entry(tier.entry, row, f"{decl.key} {tier.tier}"))
            out.itemization_rows.append(itemization)
            if tier.variant_base is not None:
                out.variant_rows.append({"entry": tier.entry, "base_entry": tier.variant_base, "tier": tier.number})
            if tier.writes_label:
                out.labels[tier.entry] = tier.label
            out.tiers.append(TierRows(tier=tier, row=row, owned=owned, stats=stats, breakdown=breakdown))
    if expansion.assignment is not None:
        for line in expansion.assignment.retired:
            out.dbc_entries.append(_dbc_entry(line.entry, line.dbc_row(), f"{line.key} {line.tier} (retired)"))
            if line.label:  # owned copies keep their tooltip label (R1 N2)
                out.labels[line.entry] = line.label
    out.labels = dict(sorted(out.labels.items()))
    return out


def merge_dbc_entries(csv_entries: list[dict], emission: ItemEmission) -> tuple[list[dict], list[str]]:
    """`csv_entries` (source/items.csv) plus the emission's Item.dbc entries; an id both declare is an ERROR (the
    entry keeps the items.csv row)."""
    taken = {int(e["id"]): "source/items.csv" for e in csv_entries}
    merged, errors = list(csv_entries), []
    for entry in emission.dbc_entries:
        owner = taken.get(entry["id"])
        if owner is not None:
            errors.append(f"items: Item.dbc row {entry['id']} ({entry['notes']}) is also declared by {owner}; "
                          f"one owner per entry")
            continue
        taken[entry["id"]] = entry["notes"]
        merged.append(entry)
    return merged, errors


# ---------------------------------------------------------------------------------------------------------------------
# Rendering


def _same(live: dict | None, row: dict, columns: tuple[str, ...], defaults: dict) -> bool:
    if live is None:
        return False
    for column in columns:
        default = defaults.get(column, 0 if isinstance(row.get(column), (int, float)) else None)
        if spell_tables._normalise(live.get(column, default)) != spell_tables._normalise(row.get(column)):
            return False
    return True


def changed_template_rows(emission: ItemEmission, live_rows: dict[int, dict]) -> list[dict]:
    """The minted full rows that differ from the live (replayed) `item_template` row, or have none."""
    out = []
    for row in emission.template_rows:
        live = live_rows.get(int(row["entry"]))
        if live is None or not spell_tables._same_row(live, row, TEMPLATE_SPEC):
            out.append(row)
    return out


def changed_keyed_rows(rows: list[dict], live: dict, columns: tuple[str, ...], defaults: dict | None = None) -> list:
    """`rows` that differ from `live` (`{(entry,): row}`, the replayed table) in any of `columns`."""
    defaults = defaults or {}
    return [row for row in rows if not _same(live.get((int(row["entry"]),)), row, columns, defaults)]


def render_keyed_block(table: str, columns: tuple[str, ...], rows: list[dict]) -> str:
    """`DELETE FROM table WHERE entry IN (...)` + one INSERT of `rows`; "" for no rows."""
    if not rows:
        return ""
    rows = sorted(rows, key=lambda r: int(r["entry"]))
    keys = ", ".join(str(int(r["entry"])) for r in rows)
    cols = ", ".join(f"`{c}`" for c in columns)
    tuples = ",\n".join("(" + ", ".join(sql_out._sql_literal(r.get(c)) for c in columns) + ")" for r in rows)
    return f"DELETE FROM `{table}` WHERE `entry` IN ({keys});\nINSERT INTO `{table}` ({cols}) VALUES\n{tuples};"


@dataclass
class Rendered:
    blocks: list[str]
    template_rows: list[dict]
    itemization_rows: list[dict]
    variant_rows: list[dict]
    retuned: list[int] = field(default_factory=list)  # minted entries already live whose stats change (R1 N13)


# The columns a client caches for an item it has seen: a change to one on a live minted row needs an
# item_budget_version bump (plan s10), or players keep the old tooltip.
RETUNE_COLUMNS = (*STAT_COLUMNS, "dmg_min1", "dmg_max1", "armor", "block", "ItemLevel", "Quality")


def render(emission: ItemEmission, live_rows: dict[int, dict], tables: dict,
           variant_columns: tuple[str, ...] = VARIANT_COLUMNS) -> Rendered:
    """The minted `item_template` upsert, the `item_itemization` block and the `item_budget_variant` block, each with
    only the rows that differ from live. (The stock entries' column edits go out through
    `spell_tables.render_item_blocks`; see the module docstring.)"""
    template_rows = changed_template_rows(emission, live_rows)
    retuned = sorted(
        int(row["entry"]) for row in template_rows
        if (live := live_rows.get(int(row["entry"]))) is not None
        and any(spell_tables._normalise(live.get(c)) != spell_tables._normalise(row.get(c)) for c in RETUNE_COLUMNS)
    )
    itemization_rows = changed_keyed_rows(
        emission.itemization_rows, tables.get(ITEMIZATION_TABLE, {}), ITEMIZATION_COLUMNS,
    )
    variant_rows = changed_keyed_rows(
        emission.variant_rows, tables.get(VARIANT_TABLE, {}), variant_columns, {"tier": 0},
    )
    blocks = [
        sql_out.render_upsert_block(TEMPLATE_SPEC.name, TEMPLATE_SPEC.columns, TEMPLATE_SPEC.key_columns,
                                    template_rows),
        render_keyed_block(ITEMIZATION_TABLE, ITEMIZATION_COLUMNS, itemization_rows),
        render_keyed_block(VARIANT_TABLE, variant_columns, variant_rows),
    ]
    return Rendered([b for b in blocks if b], template_rows, itemization_rows, variant_rows, retuned)


def summary_notes(emission: ItemEmission, rendered: Rendered | None, edits: list[dict] | None = None) -> list[str]:
    """One line on what the items emit (and, with `rendered`, how much of it differs from live)."""
    notes = [
        f"items: {len(emission.template_rows)} minted item_template row(s), {len(emission.template_edits)} stock "
        f"entry edit(s), {len(emission.itemization_rows)} item_itemization row(s), {len(emission.variant_rows)} "
        f"item_budget_variant row(s), {len(emission.dbc_entries)} Item.dbc row(s), {len(emission.labels)} tier "
        f"label(s)"
    ]
    if rendered is not None:
        notes.append(
            f"items: differ from live: {len(rendered.template_rows)} minted row(s)"
            + (f", {len(edits)} stock edit(s)" if edits is not None else "")
            + f", {len(rendered.itemization_rows)} itemization row(s), {len(rendered.variant_rows)} variant row(s)"
        )
        if rendered.retuned:
            shown = ", ".join(map(str, rendered.retuned[:20])) + (" ..." if len(rendered.retuned) > 20 else "")
            notes.append(
                f"items: {len(rendered.retuned)} minted item(s) already live change stats or level ({shown}): "
                f"clients keep the old tooltip until item_budget_version is bumped (plan s10)"
            )
    return notes
