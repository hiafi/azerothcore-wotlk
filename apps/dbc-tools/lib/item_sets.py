"""
Dungeon sets (item variants, Haunted set track, 2026-11-06): item sets and their bonuses, set tokens, and the vendors
that trade a token for a set piece, declared with `lib/dsl/sets.py` in source/items/.

**Item sets.** One `ItemSet.dbc` row per `item_set()`: the server overlay `itemset_dbc` (DBCStores.cpp:
`LOAD_DBC(sItemSetStore, "ItemSet.dbc", "itemset_dbc")`; ObjectMgr zeroes an `item_template.itemset` it cannot find,
so the row must be live before the item rows name it) and the same row in patch-Z, which the client's set tooltip
reads (name, item list, bonus spells and thresholds). A stock set (181-189 for Haunted) starts from its stock DBC row
(name and item list kept unless declared) with the stock bonuses replaced; a new one comes from source/ids.yaml's
`item_set` block. The server counts worn pieces by `item_template.itemset` alone (`AddItemsSetItem`, Item.cpp), so
every tier of a piece counts toward its set: each piece's `itemset` must name the set on every tier (checked here on
the rows lib/item_emit.py built). The row's item list holds each piece's first tier, the Normal entry: the server
reads only 10 ids and never uses them for the count; whether the client marks a worn Heroic or Empowered piece in the
tooltip's list is a playtest check (the bonus lines follow the server's count either way).

**Tokens.** Every non-deferred tier of a `set_token()`'s ladder is one `item_template` row, copied whole from the
`like=` stock token (class 15, its display and bonding), with the declaration's name and description, the tier's
level, quality and required level (the first tier: the token's own), the Heroic flag on a `heroic_flag` tier and the
tier's label in the tooltip label table on the others. The rows join lib/item_emit.py's minted rows (so the
`item_template` upsert, the `item_dbc` block and the client Item.dbc carry them, a full run and `--only items` alike),
with explicit ids from source/ids.yaml's `item_set_token` block, inside the `item` block the `item_dbc` DELETE covers.
Each token tier has one `ItemExtendedCost` row (`itemextendedcost_dbc` + patch-Z: the client prints the cost in the
vendor window from its own file): one token of that tier.

**Vendors.** `npc_vendor` rows keyed (entry, item, ExtendedCost): the vendor's tiers (all when `tiers=` is None) of
every piece of its sets, at the token of the piece's slot and tier, `slot` ordered tier by tier, then by the vendor's
token order, then by set. A vendor list sends at most 150 items (`MAX_VENDOR_ITEMS`) and keeps at most 255 rows
(`VendorItemData::GetItemCount` is a uint8): above 150 is a warning, above 255 an error. No gold price: a row with an
ExtendedCost charges no gold (`VendorItem::IsGoldRequired`).

The three tables are declared tables like `SPELL_TABLES` (`lib/spell_tables.TableSpec`): DELETE + INSERT of the rows
that differ from the replayed live rows, and a prune of rows an earlier run emitted that no declaration claims (the
circuit breaker stays on: a run that declares no row of a table with history prunes nothing of it), with
their own index (`load_index`) so lib/spell_tables.py stays untouched. A full run renders them (`render_blocks`);
`--only items` carries the token rows only (they are items) and warns while a set row is not live.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import dbcfile, dbcfmt, item_emit, spell_tables, sql_out, trainer_state
from .dsl import items as items_dsl
from .dsl import sets as sets_dsl
from .dsl.sets import ItemSetDecl, SetTokenDecl, SetVendorDecl

NAME_LANG_MASK = 16712190  # every stock ItemSet.dbc row's
VENDOR_FLAG = 0x80  # UNIT_NPC_FLAG_VENDOR
MAX_VENDOR_ITEMS = 150  # Creature.h: the client's SMSG_LIST_INVENTORY limit
MAX_VENDOR_ROWS = 255  # VendorItemData::GetItemCount() is a uint8
TOKEN_BLOCK = "item_set_token"
SET_BLOCK = "item_set"
COST_BLOCK = "item_extended_cost"

# ItemSet.dbc: DBCfmt.h's ItemSetEntryfmt ("dssssssssssssssssxiiiiiiiiiixxxxxxxiiiiiiiiiiiiiiiiii") with the index
# written 'n', the 16 name locales 's' and the 7 item ids the server skips 'x'; columns from the base dump's
# itemset_dbc CREATE TABLE. The stock file (509 rows, max ID 901) is the server's DBC directory's
# (ac-worldserver:/azerothcore/env/dist/data/dbc/ItemSet.dbc), copied to var/extractors/dbc/.
ITEMSET = dbcfmt.DbcTable(
    name="ItemSet",
    dbc_filename="ItemSet.dbc",
    sql_table="itemset_dbc",
    fmt="n" + "s" * 16 + "x" + "i" * 10 + "x" * 7 + "i" * 8 + "i" * 8 + "ii",
    columns=dbcfmt._cols(
        "ID", dbcfmt._locale_cols("Name"), ("ItemID", 17), ("SetSpellID", 8), ("SetThreshold", 8), "RequiredSkill",
        "RequiredSkillRank",
    ),
)
# ItemExtendedCost.dbc: DBCfmt.h's ItemExtendedCostEntryfmt ("niiiiiiiiiiiiiix"); columns from the base dump. Stock
# file: 972 rows, max ID 2997 (DBCStores.cpp asserts 2997 is the last 3.3.5a row).
ITEMEXTENDEDCOST = dbcfmt.DbcTable(
    name="ItemExtendedCost",
    dbc_filename="ItemExtendedCost.dbc",
    sql_table="itemextendedcost_dbc",
    fmt="n" + "i" * 14 + "x",
    columns=dbcfmt._cols(
        "ID", "HonorPoints", "ArenaPoints", "ArenaBracket", ("ItemID", 5), ("ItemCount", 5), "RequiredArenaRating",
        "ItemPurchaseGroup",
    ),
)
NPC_VENDOR_COLUMNS = ("entry", "slot", "item", "maxcount", "incrtime", "ExtendedCost", "VerifiedBuild")

SET_TABLES = (
    spell_tables.TableSpec("itemset_dbc", ITEMSET.columns, ("ID",), "item_set_rows"),
    spell_tables.TableSpec("itemextendedcost_dbc", ITEMEXTENDEDCOST.columns, ("ID",), "item_extended_cost_rows"),
    spell_tables.TableSpec("npc_vendor", NPC_VENDOR_COLUMNS, ("entry", "item", "ExtendedCost"), "npc_vendor_rows",
                           defaults={"VerifiedBuild": None}),
)
_PRUNE_WHY = {
    "itemset_dbc": "Left in place, the set keeps these bonuses (a stock set id would never return to stock).",
    "itemextendedcost_dbc": "Left in place, vendor rows naming the cost keep charging the token.",
    "npc_vendor": "Left in place, the vendor keeps selling the item.",
}
TOKEN_LABEL_NOTE = "set token"


def _int(value) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _in_block(ids_cfg: dict, block: str, value: int) -> bool | None:
    """True / False, or None when source/ids.yaml has no such block."""
    spec = ids_cfg.get(block)
    if spec is None:
        return None
    return spec["start"] <= value <= spec["end"]


@dataclass
class SetExpansion:
    set_rows: list[dict] = field(default_factory=list)
    cost_rows: list[dict] = field(default_factory=list)
    vendor_rows: list[dict] = field(default_factory=list)
    token_rows: list[dict] = field(default_factory=list)
    # {set id: {"bonuses": [(pieces, spell id)], "pieces": [[item_template entry of every tier of one piece]]}}: the
    # client tooltip's view of the set (lib/item_set_members.py), whole piece list, every tier.
    members: dict[int, dict] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def declared(self) -> bool:
        return bool(self.set_rows or self.cost_rows or self.vendor_rows or self.token_rows)

    def client_rows(self) -> dict:
        """{DbcTable: {ID: row}} for the patch-Z merge."""
        return {
            ITEMSET: {int(r["ID"]): {c: r[c] for c in ITEMSET.columns} for r in self.set_rows},
            ITEMEXTENDEDCOST: {int(r["ID"]): {c: r[c] for c in ITEMEXTENDEDCOST.columns} for r in self.cost_rows},
        }


def _declarations(dsl_classes: dict) -> tuple[dict, dict, list]:
    sets: dict[int, ItemSetDecl] = {}
    tokens: dict[str, SetTokenDecl] = {}
    vendors: list[SetVendorDecl] = []
    for entry in dsl_classes.get("item_set_declarations", []):
        decl = entry["_decl"]
        if isinstance(decl, ItemSetDecl):
            sets[decl.set_id] = decl
        elif isinstance(decl, SetTokenDecl):
            tokens[decl.key] = decl
        elif isinstance(decl, SetVendorDecl):
            vendors.append(decl)
    return sets, tokens, vendors


def stock_set_rows(base_dir: Path) -> dict[int, dict]:
    path = base_dir / ITEMSET.dbc_filename
    return {int(r["ID"]): r for r in dbcfile.read_dbc(path, ITEMSET)} if path.is_file() else {}


def _empty_row(table: dbcfmt.DbcTable) -> dict:
    return {c: ("" if c.startswith("Name_Lang_") and c != "Name_Lang_Mask" else 0) for c in table.columns}


def base_file_errors(expansion: SetExpansion, base_dir: Path) -> list[str]:
    """The stock DBCs a full run merges the set and cost rows into (else the client never sees them)."""
    out = []
    for table, rows in ((ITEMSET, expansion.set_rows), (ITEMEXTENDEDCOST, expansion.cost_rows)):
        path = base_dir / table.dbc_filename
        if rows and not path.is_file():
            out.append(
                f"item sets: {len(rows)} {table.name} row(s) declared but no stock {table.dbc_filename} at {path} - "
                f"copy it from the worldserver's DBC directory (docker cp "
                f"ac-worldserver:/azerothcore/env/dist/data/dbc/{table.dbc_filename} {path})"
            )
    return out


def expand(
    dsl_classes: dict, item_expansion, item_emission, *, ids_cfg: dict, live_item_rows: dict[int, dict],
    base_dir: Path, items_csv_ids=(), stock_sets: dict[int, dict] | None = None,
) -> SetExpansion:
    """Resolves the set, token and vendor declarations against the resolved items (`item_expansion`, `item_emission`
    from lib/item_variants.py / lib/item_emit.py). Adds the token rows, Item.dbc entries and labels to
    `item_emission` and the set, cost and vendor rows to `dsl_classes`. Never raises for a content problem."""
    out = SetExpansion()
    sets, tokens, vendors = _declarations(dsl_classes)
    if not (sets or tokens or vendors):
        return out
    if stock_sets is None:
        stock_sets = stock_set_rows(base_dir)
    items = {item.decl.key: item for item in item_expansion.items}
    tier_rows = {t.tier.entry: t.row for t in item_emission.tiers}
    declared_spells = {int(s["id"]) for s in dsl_classes.get("spells", [])}

    _expand_sets(out, sets, items, tier_rows, ids_cfg, stock_sets, declared_spells)
    token_entries = _expand_tokens(out, tokens, ids_cfg, live_item_rows, item_expansion, items_csv_ids)
    _expand_vendors(out, vendors, sets, tokens, items, tier_rows, dsl_classes)
    if out.errors:
        return out

    for row in out.token_rows:
        item_emission.template_rows.append(row)
        item_emission.dbc_entries.append(_dbc_entry(row, f"{TOKEN_LABEL_NOTE} {token_entries[row['entry']]}"))
    for tier_entry, label in _token_labels(tokens).items():
        item_emission.labels[tier_entry] = label
    item_emission.labels = dict(sorted(item_emission.labels.items()))
    dsl_classes.setdefault("item_set_rows", []).extend(out.set_rows)
    dsl_classes.setdefault("item_extended_cost_rows", []).extend(out.cost_rows)
    dsl_classes.setdefault("npc_vendor_rows", []).extend(out.vendor_rows)
    out.notes.append(
        f"item sets: {len(out.set_rows)} set(s), {len(tokens)} token(s) on {len(out.token_rows)} tier row(s), "
        f"{len(out.cost_rows)} extended cost(s), {len(vendors)} vendor(s) with {len(out.vendor_rows)} row(s)"
    )
    return out


def _dbc_entry(row: dict, note: str) -> dict:
    out = {"id": int(row["entry"]), "notes": note}
    for field_name, column in item_emit.DBC_FIELDS:
        out[field_name] = _int(row.get(column))
    return out


def _token_labels(tokens: dict[str, SetTokenDecl]) -> dict[int, str]:
    out = {}
    for token in tokens.values():
        for spec in token.ladder.tiers:
            entry = token.entry(spec.name)
            if entry is not None and not spec.heroic_flag:
                out[entry] = spec.label
    return out


def _expand_sets(out, sets, items, tier_rows, ids_cfg, stock_sets, declared_spells) -> None:
    owner: dict[str, int] = {}
    for set_id, decl in sorted(sets.items()):
        where = decl.where
        stock = stock_sets.get(set_id)
        if stock is None:
            in_block = _in_block(ids_cfg, SET_BLOCK, set_id)
            if in_block is None:
                out.errors.append(f"{where}: source/ids.yaml has no {SET_BLOCK} block (new item set ids come from it)")
                continue
            if not in_block:
                out.errors.append(f"{where}: {set_id} is neither a stock ItemSet.dbc id nor in source/ids.yaml's "
                                  f"{SET_BLOCK} block")
                continue
            if decl.name is None:
                out.errors.append(f"{where}: a new set needs name=")
                continue
        first_entries = []
        pieces: list[list[int]] = []
        for key in decl.items:
            if key in owner:
                out.errors.append(f"{where}: item {key!r} is already in item_set({owner[key]})")
                continue
            owner[key] = set_id
            item = items.get(key)
            if item is None:
                out.errors.append(f"{where}: {key!r} is not a resolved item() key")
                continue
            if not item.tiers:
                out.errors.append(f"{where}: item {key!r} has no minted tier")
                continue
            if item.inventory_type not in sets_dsl.ARMOR_SLOTS:
                out.errors.append(f"{where}: item {key!r} is not armor (InventoryType {item.inventory_type})")
            for tier in item.tiers:
                row = tier_rows.get(tier.entry)
                itemset = _int(row.get("itemset")) if row is not None else None
                if itemset != set_id:
                    out.errors.append(
                        f"{where}: item {key!r} tier {tier.tier!r} (entry {tier.entry}) has itemset {itemset}; every "
                        f"tier must name the set (a base= piece keeps its stock itemset, a new one passes itemset=)"
                    )
            first_entries.append(item.tiers[0].entry)
            pieces.append([tier.entry for tier in item.tiers])
        for threshold, spell_id in decl.bonuses:
            if spell_id not in declared_spells:
                out.warnings.append(f"{where}: bonus spell {spell_id} ({threshold} pieces) is not declared in source/")
        row = dict(stock) if stock is not None else _empty_row(ITEMSET)
        row["ID"] = set_id
        if decl.name is not None:
            row["Name_Lang_enUS"] = decl.name
        row["Name_Lang_Mask"] = NAME_LANG_MASK
        for n in range(1, sets_dsl.MAX_SET_ITEMS_CLIENT + 1):
            row[f"ItemID_{n}"] = first_entries[n - 1] if n <= len(first_entries) else 0
        bonuses = sorted(decl.bonuses)
        for n in range(1, sets_dsl.MAX_SET_SPELLS + 1):
            spell_id = bonuses[n - 1][1] if n <= len(bonuses) else 0
            threshold = bonuses[n - 1][0] if n <= len(bonuses) else 0
            row[f"SetSpellID_{n}"], row[f"SetThreshold_{n}"] = spell_id, threshold
        row["RequiredSkill"], row["RequiredSkillRank"] = 0, 0
        out.set_rows.append(row)
        out.members[set_id] = {"bonuses": bonuses, "pieces": pieces}


def _expand_tokens(out, tokens, ids_cfg, live_item_rows, item_expansion, items_csv_ids) -> dict[int, str]:
    """The token tier rows and their extended cost rows; returns {entry: "key tier"}."""
    names: dict[int, str] = {}
    minted = {tier.entry for item in item_expansion.items for tier in item.tiers}
    csv_ids = {int(i) for i in items_csv_ids}
    costs: dict[int, str] = {}
    for key, token in sorted(tokens.items()):
        where = token.where
        like = live_item_rows.get(token.like)
        if like is None:
            out.errors.append(f"{where}: like={token.like} has no live item_template row")
            continue
        if _int(like.get("class")) != sets_dsl.TOKEN_ITEM_CLASS:
            out.errors.append(f"{where}: like={token.like} is not a class {sets_dsl.TOKEN_ITEM_CLASS} token")
        for spec in token.ladder.tiers:
            if spec.deferred:
                continue
            entry, cost = token.entry(spec.name), token.cost(spec.name)
            for block, value, what in ((TOKEN_BLOCK, entry, "entry"), (COST_BLOCK, cost, "cost")):
                in_block = _in_block(ids_cfg, block, value)
                if in_block is None:
                    out.errors.append(f"{where}: source/ids.yaml has no {block} block")
                elif not in_block:
                    out.errors.append(f"{where} tier {spec.name!r}: {what} {value} is outside source/ids.yaml's "
                                      f"{block} block")
            if entry in names or entry in minted or entry in csv_ids:
                out.errors.append(f"{where} tier {spec.name!r}: entry {entry} is already taken")
                continue
            if cost in costs:
                out.errors.append(f"{where} tier {spec.name!r}: cost {cost} is also {costs[cost]}'s")
                continue
            names[entry] = f"{key} {spec.name}"
            costs[cost] = f"{key} {spec.name}"
            defaults = spell_tables.ITEM_TEMPLATE_DEFAULTS
            row = {c: like.get(c, defaults.get(c)) for c in spell_tables.ITEM_TEMPLATE_COLUMNS}
            row.update(dict(token.columns))
            row.update(sets_dsl.TOKEN_FORCED)
            if spec.explicit:
                ilvl, quality, required = spec.ilvl, spec.quality, spec.required_level
            else:
                ilvl, quality, required = token.ilvl, token.quality, token.required_level
            flags = _int(row.get("Flags"))
            heroic = items_dsl.HEROIC_TOOLTIP_FLAG
            flags = flags | heroic if spec.heroic_flag else flags & ~heroic
            row.update(entry=entry, name=token.name, description=token.description, ItemLevel=ilvl, Quality=quality,
                       RequiredLevel=required, Flags=flags)
            out.token_rows.append(row)
            out.cost_rows.append(_cost_row(cost, entry))
    out.cost_rows.sort(key=lambda r: r["ID"])
    return names


def _cost_row(cost: int, token_entry: int) -> dict:
    row = {c: 0 for c in ITEMEXTENDEDCOST.columns}
    row.update(ID=cost, ItemID_1=token_entry, ItemCount_1=1)
    return row


def _expand_vendors(out, vendors, sets, tokens, items, tier_rows, dsl_classes) -> None:
    creatures = {int(r["entry"]): r for r in dsl_classes.get("creature_templates", [])}
    sold: dict[int, set[int]] = {}
    for vendor in vendors:
        where = vendor.where
        creature = creatures.get(vendor.entry)
        if creature is None:
            out.warnings.append(f"{where}: no creature_template() declares {vendor.entry} in source/ (a stock vendor?)")
        elif not _int(creature.get("npcflag")) & VENDOR_FLAG:
            out.errors.append(f"{where}: creature {vendor.entry} has no vendor flag (npcflag 0x80)")
        by_slot: dict[int, tuple[int, SetTokenDecl]] = {}
        for order, key in enumerate(vendor.tokens):
            token = tokens.get(key)
            if token is None:
                out.errors.append(f"{where}: {key!r} is not a set_token() key")
                continue
            for slot in token.slots:
                if slot in by_slot:
                    out.errors.append(
                        f"{where}: InventoryType {slot} is bought by {by_slot[slot][1].key!r} and {key!r}"
                    )
                by_slot[slot] = (order, token)
        if vendor.tiers is not None:
            known = {t.name for token in tokens.values() for t in token.ladder.tiers}
            unknown = [t for t in vendor.tiers if t not in known]
            if unknown:
                out.errors.append(f"{where}: tiers {unknown} are on no token's ladder")
        planned = []
        for set_order, set_id in enumerate(vendor.sets):
            decl = sets.get(set_id)
            if decl is None:
                out.errors.append(f"{where}: {set_id} is not an item_set() id")
                continue
            for key in decl.items:
                item = items.get(key)
                if item is None:
                    continue  # reported by the set
                slot = by_slot.get(item.inventory_type)
                if slot is None:
                    out.errors.append(f"{where}: no token buys {key!r} (InventoryType {item.inventory_type})")
                    continue
                token_order, token = slot
                for tier in item.tiers:
                    if vendor.tiers is not None and tier.tier not in vendor.tiers:
                        continue
                    cost = token.cost(tier.tier)
                    if cost is None:
                        out.errors.append(f"{where}: token {token.key!r} has no tier {tier.tier!r} for {key!r}")
                        continue
                    position = [s.name for s in token.ladder.tiers].index(tier.tier)
                    planned.append(((position, token_order, set_order), tier.entry, cost))
        planned.sort(key=lambda p: p[0])
        if not planned:
            out.errors.append(f"{where}: sells nothing (no piece of its sets on its tiers)")
        if len(planned) > MAX_VENDOR_ROWS:
            out.errors.append(f"{where}: {len(planned)} rows; the server keeps {MAX_VENDOR_ROWS} per vendor")
        elif len(planned) > MAX_VENDOR_ITEMS:
            out.warnings.append(f"{where}: {len(planned)} rows; the client is sent the first {MAX_VENDOR_ITEMS}")
        seen = sold.setdefault(vendor.entry, set())
        for slot_index, (_, entry, cost) in enumerate(planned):
            if entry in seen:
                out.errors.append(f"{where}: item {entry} is listed twice")
                continue
            seen.add(entry)
            out.vendor_rows.append({"entry": vendor.entry, "slot": slot_index, "item": entry, "maxcount": 0,
                                    "incrtime": 0, "ExtendedCost": cost, "VerifiedBuild": None})


# ---------------------------------------------------------------------------------------------------------------------
# Rendering


def load_index() -> spell_tables.SpellTableIndex:
    return spell_tables.SpellTableIndex(
        {spec.name: trainer_state.load_table_rows(spec.name) for spec in SET_TABLES},
        emitted={spec.name: spell_tables.load_generated_table_rows(spec.name, spec.key_columns) for spec in SET_TABLES},
        base={spec.name: spell_tables.load_base_table_rows(spec.name, spec.key_columns) for spec in SET_TABLES},
        tables=SET_TABLES,
    )


def render_blocks(index: spell_tables.SpellTableIndex, dsl_classes: dict, prune: bool = True,
                  ) -> tuple[list[str], list[str]]:
    """`(sql_blocks, report_lines)`: the prune DELETEs first (rows an earlier run emitted that nothing declares
    now), then one DELETE + INSERT per table of the declared rows that differ from live."""
    blocks: list[str] = []
    report: list[str] = []
    for spec in SET_TABLES:
        declared = dsl_classes.get(spec.registry_key, [])
        if not prune:
            continue
        result = index.rows_to_prune(spec, declared)
        if result.breaker_tripped:
            report.append(f"prune: SKIPPED {spec.name} - rows from previous runs but none declared this run")
            continue
        for key in result.base_blocked:
            report.append(f"prune: NOT removing {spec.name} {key} - the stock dump owns the key; resolve by hand")
        if result.keys:
            report += [f"prune: removing {spec.name} {key} - no longer declared" for key in result.keys]
            comment = (f"-- Prune: {len(result.keys)} {spec.name} row(s) an earlier generate.py run emitted for a "
                       f"dungeon set\n-- that source/items/ no longer declares. {_PRUNE_WHY[spec.name]}")
            blocks.append(sql_out.render_delete_only_block(spec.name, spec.key_columns, result.keys, comment))
    for spec in SET_TABLES:
        rows = index.rows_to_emit(spec, dsl_classes.get(spec.registry_key, []))
        block = sql_out.render_generic_table_block(spec.name, spec.columns, spec.key_columns, rows)
        if block:
            blocks.append(block)
    return blocks, report


def differ_notes(index: spell_tables.SpellTableIndex, dsl_classes: dict) -> list[str]:
    parts = []
    for spec in SET_TABLES:
        declared = dsl_classes.get(spec.registry_key, [])
        if declared:
            parts.append(f"{len(index.rows_to_emit(spec, declared))} of {len(declared)} {spec.name}")
    return [f"item sets: differ from live: {', '.join(parts)}"] if parts else []


def not_live_warning(index: spell_tables.SpellTableIndex, dsl_classes: dict) -> str | None:
    """`--only items` ships the token rows but no set, cost or vendor row: say so while any of them is not live."""
    pending = sum(len(index.rows_to_emit(spec, dsl_classes.get(spec.registry_key, []))) for spec in SET_TABLES)
    if not pending:
        return None
    return (f"item sets: {pending} itemset_dbc / itemextendedcost_dbc / npc_vendor row(s) are not live and "
            f"--only items does not ship them; run a full generate.py")
