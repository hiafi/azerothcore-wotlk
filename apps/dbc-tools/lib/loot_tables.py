"""
Boss loot tables (item-variants plan v2 section 7.3, stage IV7): turns `lib/dsl/loot.py`'s declarations into
`creature_loot_template` and `reference_loot_template` rows, checks them against the loot rules, and renders the
groups that differ from the replayed live tables.

**Keys and ownership.** A `boss_loot()` owns one (Entry, GroupId) of `creature_loot_template`: its block is
`DELETE ... WHERE Entry = X AND GroupId = N` + INSERT, emitted only when the declared rows differ from the replayed
group (base dump, migrations, pending and module SQL), so a rerun after import is silent. A `picks=N` list also owns
its whole `reference_loot_template` Entry (source/ids.yaml's `loot_reference` block). Rows outside the declared groups
are never touched; a `remove_loot_group()` is the DELETE alone.

**Item ids.** Every key resolves through `item_variants.expand()`'s tiers (the lock file `source/items/item_ids.lock`,
or the deterministic ids `--check` reports before a full run writes them): a `base=` item's Normal tier is its stock
entry.

**The rules** (docs/dungeons/boss-rework-systems.md section 2, Loot lists; `lint_rows` and `check_live`):

- a list is one group of equal-chance entries: Chance 0, MinCount = MaxCount = 1, GroupId 1-127, no item twice, so
  the group always yields one item (`LootTemplate::LootGroup::Roll`);
- a generic pool rolls on top, never instead: a declared group's live rows must all be items an `item()` declares (or
  this tool's reference row), or the run stops rather than drop the pool; a list item also in another live group of
  the same Entry is a WARNING (it could drop twice);
- `picks=N`: the reference row is Chance 0 with MaxCount N, its pool is one Chance 0 group of at least N equippable
  items (the group roll's duplicate skip only covers equippable items, InventoryType != 0);
- difficulty: a heroic creature's lootid (an entry of source/world/heroic_ids.lock) drops the ladder's first tier with
  an explicit item level (Heroic, Heroic Hard Mode), any other lootid the items' own-level tier (Normal); the heroic
  creature_template row's `lootid` must be its own entry (set by the dungeon file's `overrides` columns);
- a heroic lootid with a declared list keeps every other group of its normal boss's lootid (cloth, food, quest items,
  generic references), copied unchanged in the same GroupId (`derive_heroic_copies`, from the replayed normal rows);
- a hard mode group (`loot_mode` without bit 1) sits next to a default list group on the same Entry: one item on top
  of the boss's loot, rolled only when the script added the bit to the creature's loot mode before the kill.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import item_variants, spell_tables, sql_dump, sql_out, trainer_state
from .dsl import loot as loot_dsl

CREATURE_LOOT = "creature_loot_template"
REFERENCE_LOOT = "reference_loot_template"
COLUMNS = (
    "Entry", "Item", "Reference", "Chance", "QuestRequired", "LootMode", "GroupId", "MinCount", "MaxCount", "Comment",
)
KEY_COLUMNS = ("Entry", "Item", "Reference", "GroupId")
REFERENCE_BLOCK = "loot_reference"
REFERENCE_POOL_GROUP = 1  # the pool's group inside its reference_loot_template Entry


@dataclass
class LootPlan:
    groups: dict[tuple[int, int], list[dict]] = field(default_factory=dict)  # (Entry, GroupId) -> rows ([]: removal)
    references: dict[int, list[dict]] = field(default_factory=dict)  # reference_loot_template Entry -> rows
    removals: dict[tuple[int, int], str] = field(default_factory=dict)  # (Entry, GroupId) -> why
    owned_items: set[int] = field(default_factory=set)  # every tier entry of every declared item
    picks: dict[int, int] = field(default_factory=dict)  # reference Entry -> picks
    equippable: dict[int, bool] = field(default_factory=dict)  # item entry -> InventoryType != 0
    # Follow-up 1: a heroic lootid with a declared list keeps every other group its normal boss drops (cloth, food,
    # quest items, generic world loot references), copied unchanged (derive_heroic_copies, from the live normal rows).
    heroic_sources: dict[int, int] = field(default_factory=dict)  # heroic lootid -> the normal boss's lootid
    copies: dict[tuple[int, int], list[dict]] = field(default_factory=dict)  # (heroic Entry, GroupId) -> rows
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _int(value, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def own_level_tier(ladder) -> object | None:
    """The tier a normal lootid drops: the ladder's first non-deferred tier that takes the item's own level."""
    return next((t for t in ladder.tiers if not t.deferred and not t.explicit), None)


def first_explicit_tier(ladder) -> object | None:
    """The tier a heroic lootid drops: the ladder's first non-deferred tier with an explicit item level."""
    return next((t for t in ladder.tiers if not t.deferred and t.explicit), None)


def _boss_name(lootid: int, creature_rows: dict[int, dict]) -> str:
    row = creature_rows.get(lootid)
    if row is None:
        row = next((r for _, r in sorted(creature_rows.items()) if _int(r.get("lootid")) == lootid), None)
    return str(row.get("name")) if row and row.get("name") else f"lootid {lootid}"


def _item_name(item: item_variants.ResolvedItem, tier: item_variants.ResolvedTier) -> str:
    return str(tier.columns.get("name") or item.decl.name or item.source_row.get("name") or item.decl.key)


def _row(entry: int, item: int, comment: str, *, group: int, loot_mode: int = loot_dsl.LOOT_MODE_DEFAULT,
         reference: int = 0, max_count: int = 1) -> dict:
    return {
        "Entry": entry, "Item": item, "Reference": reference, "Chance": 0, "QuestRequired": 0, "LootMode": loot_mode,
        # A reference row needs MinCount == MaxCount (LootMgr.cpp CheckLootRefs reports anything else); MaxCount is how
        # many times the pool is rolled.
        "GroupId": group, "MinCount": max_count if reference else 1, "MaxCount": max_count, "Comment": comment,
    }


def build(
    declarations: list[dict], expansion: item_variants.ItemExpansion, *, ids_cfg: dict,
    heroic_pairs: dict[int, int], creature_rows: dict[int, dict], strict_lootid: bool = True,
) -> LootPlan:
    """Resolves `declarations` (`dsl_classes["loot_declarations"]`) against the item expansion. `heroic_pairs` is
    normal -> heroic creature entry (heroic_ids.lock); `creature_rows` the creature_template rows by entry as this run
    will leave them (live, with the declared and generated heroic rows over them). `strict_lootid=False` (an
    `--only items` run, which renders no creature_template row) makes a heroic row whose lootid is not its own entry
    a WARNING instead of an ERROR."""
    plan = LootPlan()
    decls: list[loot_dsl.LootDecl] = [entry["_decl"] for entry in declarations]
    if not decls:
        return plan
    items = {item.decl.key: item for item in expansion.items}
    for item in expansion.items:
        for tier in item.tiers:
            plan.owned_items.add(tier.entry)
            plan.equippable[tier.entry] = item.inventory_type != 0
    heroic_entries = set(heroic_pairs.values())
    block = ids_cfg.get(REFERENCE_BLOCK)
    by_entry: dict[int, list[loot_dsl.LootDecl]] = {}
    for decl in decls:
        by_entry.setdefault(decl.lootid, []).append(decl)

    for decl in decls:
        where = decl.where
        key = (decl.lootid, decl.group)
        if decl.removal:
            plan.groups[key] = []
            plan.removals[key] = decl.why
            continue
        heroic = decl.lootid in heroic_entries
        boss = _boss_name(decl.lootid, creature_rows)
        resolved: list[tuple[item_variants.ResolvedItem, item_variants.ResolvedTier]] = []
        for item_key in decl.items:
            item = items.get(item_key)
            if item is None:
                plan.errors.append(f"{where}: {item_key!r} is not a resolved item() key (unknown, or its declaration "
                                   f"has errors)")
                continue
            spec = item.decl.ladder.tier(decl.tier)
            if spec is None or spec.deferred:
                plan.errors.append(
                    f"{where}: item {item_key!r} has no {'minted ' if spec else ''}tier {decl.tier!r} on ladder "
                    f"{item.decl.ladder.name!r} ({', '.join(item.decl.ladder.names)})"
                )
                continue
            want = first_explicit_tier(item.decl.ladder) if heroic else own_level_tier(item.decl.ladder)
            if want is None or want.name != spec.name:
                kind = "a heroic creature's lootid" if heroic else "a normal lootid"
                plan.errors.append(
                    f"{where}: item {item_key!r} drops tier {decl.tier!r}, but {kind} drops "
                    f"{repr(want.name) if want else 'no tier'} of ladder {item.decl.ladder.name!r} "
                    f"(normal: the items' own level; heroic: the first explicit item level)"
                )
                continue
            tier = next((t for t in item.tiers if t.tier == decl.tier), None)
            if tier is None:
                plan.errors.append(f"{where}: item {item_key!r} tier {decl.tier!r} has no item_template entry")
                continue
            resolved.append((item, tier))
        if len(resolved) != len(decl.items):
            continue

        if decl.loot_mode != loot_dsl.LOOT_MODE_DEFAULT:
            if decl.loot_mode & loot_dsl.LOOT_MODE_DEFAULT:
                plan.errors.append(f"{where}: loot_mode={decl.loot_mode} includes LOOT_MODE_DEFAULT (1), so it would "
                                   f"roll on every kill; a hard mode group carries only its own bit")
            if not any(d.loot_mode == loot_dsl.LOOT_MODE_DEFAULT and not d.removal for d in by_entry[decl.lootid]):
                plan.errors.append(f"{where}: a loot_mode={decl.loot_mode} group drops on top of the boss's list, but "
                                   f"lootid {decl.lootid} declares no default list group")

        rows = []
        if decl.picks > 1:
            ref = decl.reference
            if block is None:
                plan.errors.append(f"{where}: source/ids.yaml has no {REFERENCE_BLOCK} block")
                continue
            if not block["start"] <= ref <= block["end"]:
                plan.errors.append(f"{where}: reference={ref} is outside source/ids.yaml's {REFERENCE_BLOCK} block "
                                   f"({block['start']}-{block['end']})")
                continue
            if ref in plan.references:
                plan.errors.append(f"{where}: reference={ref} is already another list's pool")
                continue
            plan.references[ref] = [
                _row(ref, tier.entry, f"{boss} pool - {_item_name(item, tier)} ({tier.label})",
                     group=REFERENCE_POOL_GROUP, loot_mode=decl.loot_mode)
                for item, tier in resolved
            ]
            plan.picks[ref] = decl.picks
            rows.append(_row(decl.lootid, ref, f"{boss} - {decl.picks} of the {boss} pool ({resolved[0][1].label})",
                             group=decl.group, loot_mode=decl.loot_mode, reference=ref, max_count=decl.picks))
        else:
            rows += [
                _row(decl.lootid, tier.entry, f"{boss} - {_item_name(item, tier)} ({tier.label})",
                     group=decl.group, loot_mode=decl.loot_mode)
                for item, tier in resolved
            ]
        plan.groups[key] = rows

    _check_creatures(plan, decls, heroic_pairs, creature_rows, strict_lootid)
    normal_of = {h: n for n, h in heroic_pairs.items()}
    for lootid in sorted({d.lootid for d in decls if not d.removal} & set(normal_of)):
        normal_row = creature_rows.get(normal_of[lootid])
        source = _int(normal_row.get("lootid")) if normal_row else 0
        if source and source != lootid:
            plan.heroic_sources[lootid] = source
    plan.errors += lint_rows(plan)
    return plan


def derive_heroic_copies(plan: LootPlan, live_creature: list[dict]) -> None:
    """Every live group of a heroic list's normal lootid that no declaration owns (group 0's cloth, food and quest
    items, a generic world loot reference in its own group) is copied unchanged onto the heroic lootid: the boss's
    generic pools roll on top of the list on heroic too, never instead. Derived from the replayed normal rows each
    run, so a rerun is silent and a later change to a normal group follows. A copy that lands on a declared heroic
    group is an ERROR; a live heroic group that is neither declared nor a copy any more is a WARNING (never pruned)."""
    if not plan.heroic_sources:
        return
    sources = set(plan.heroic_sources.values())
    live = _group_index(live_creature, sources | set(plan.heroic_sources))
    for heroic, normal in sorted(plan.heroic_sources.items()):
        for (entry, group), rows in sorted(live.items()):
            if entry != normal or (normal, group) in plan.groups:
                continue
            if (heroic, group) in plan.groups:
                plan.errors.append(
                    f"{CREATURE_LOOT} {heroic} group {group}: normal lootid {normal}'s group {group} is copied onto "
                    f"the heroic lootid, but a declaration already owns that group; give one of them another GroupId"
                )
                continue
            plan.copies[(heroic, group)] = [{**{c: r.get(c) for c in COLUMNS}, "Entry": heroic} for r in rows]
        for (entry, group) in sorted(live):
            if entry == heroic and (heroic, group) not in plan.groups and (heroic, group) not in plan.copies:
                plan.warnings.append(f"{CREATURE_LOOT} {heroic} group {group}: live, but neither declared nor a "
                                     f"copy of normal lootid {normal} any more; left in place")


def _check_creatures(plan: LootPlan, decls: list[loot_dsl.LootDecl], heroic_pairs: dict[int, int],
                     creature_rows: dict[int, dict], strict_lootid: bool) -> None:
    """The heroic lootid rule, a lootid no creature drops, and a heroic body still sharing its normal list."""
    heroic_entries = set(heroic_pairs.values())
    used = {_int(r.get("lootid")) for r in creature_rows.values()}
    listed = {d.lootid for d in decls if not d.removal}
    for lootid in sorted(listed):
        if lootid in heroic_entries:
            row = creature_rows.get(lootid)
            have = _int(row.get("lootid")) if row else None
            if have != lootid:
                message = (
                    f"boss_loot({lootid}): heroic creature {lootid}'s lootid is {have}, not its own entry; set "
                    f"columns={{'lootid': {lootid}}} in its dungeon file's heroic overrides"
                )
                (plan.errors if strict_lootid else plan.warnings).append(
                    message if strict_lootid else message + " (a full run emits the heroic row)"
                )
        elif lootid not in used:
            plan.warnings.append(f"boss_loot({lootid}): no creature_template row has lootid {lootid}")
    for normal, heroic in sorted(heroic_pairs.items()):
        normal_row, heroic_row = creature_rows.get(normal), creature_rows.get(heroic)
        if not normal_row or not heroic_row:
            continue
        lootid = _int(normal_row.get("lootid"))
        if lootid in listed and heroic not in listed and _int(heroic_row.get("lootid")) == lootid:
            plan.warnings.append(
                f"boss_loot({lootid}): heroic creature {heroic} ({heroic_row.get('name')}) still uses the normal "
                f"lootid {lootid}, so heroic drops the Normal list; give it its own lootid and a heroic list"
            )


def lint_rows(plan: LootPlan) -> list[str]:
    """The equal-chance list rule on the rows themselves (a test hook as much as a run check)."""
    errors = []
    for (entry, group), rows in sorted(plan.groups.items()):
        where = f"{CREATURE_LOOT} {entry} group {group}"
        if rows and not 1 <= group <= loot_dsl.MAX_GROUP_ID:
            errors.append(f"{where}: a list needs a GroupId in 1-{loot_dsl.MAX_GROUP_ID}")
        errors += _list_errors(where, rows)
        for row in rows:
            if row["Reference"]:
                pool = plan.references.get(row["Reference"])
                if pool is None:
                    errors.append(f"{where}: reference {row['Reference']} has no declared pool")
                elif row["MaxCount"] > len(pool):
                    errors.append(f"{where}: {row['MaxCount']} picks from a pool of {len(pool)}")
            elif row["MaxCount"] != 1:
                errors.append(f"{where}: item {row['Item']} has MaxCount {row['MaxCount']} (a list item drops once)")
        if len({r["LootMode"] for r in rows}) > 1:
            errors.append(f"{where}: mixed LootMode values in one list")
    for ref, rows in sorted(plan.references.items()):
        where = f"{REFERENCE_LOOT} {ref}"
        errors += _list_errors(where, rows)
        if {r["GroupId"] for r in rows} != {REFERENCE_POOL_GROUP}:
            errors.append(f"{where}: the pool must be one group ({REFERENCE_POOL_GROUP})")
        if any(r["Reference"] or r["MaxCount"] != 1 for r in rows):
            errors.append(f"{where}: a pool holds plain items that drop once")
        picks = plan.picks.get(ref, 1)
        if picks > 1:
            unequippable = [r["Item"] for r in rows if not plan.equippable.get(r["Item"], False)]
            if unequippable:
                errors.append(f"{where}: {picks} distinct picks need equippable items (the duplicate skip covers "
                              f"InventoryType != 0 only); not equippable: {unequippable}")
    return errors


def _list_errors(where: str, rows: list[dict]) -> list[str]:
    errors = []
    for row in rows:
        if float(row["Chance"]) != 0:
            errors.append(f"{where}: item {row['Item']} has Chance {row['Chance']} (a list is equal chance, 0)")
        expected_min = row["MaxCount"] if row["Reference"] else 1
        if row["MinCount"] != expected_min:
            errors.append(f"{where}: item {row['Item']} has MinCount {row['MinCount']} (expected {expected_min})")
        if row["QuestRequired"]:
            errors.append(f"{where}: item {row['Item']} is a quest drop")
    seen = [(r["Item"], r["Reference"]) for r in rows]
    if len(set(seen)) != len(seen):
        errors.append(f"{where}: an item is listed twice")
    return errors


# ---------------------------------------------------------------------------------------------------------------------
# Live state


def _with_defaults(table: str, rows: list[dict]) -> list[dict]:
    """A column an INSERT left out takes its schema DEFAULT (the replay leaves it out of the row), so a declared row
    compares equal to the live one MySQL actually holds."""
    path = trainer_state.BASE_SQL_DIR / f"{table}.sql"
    defaults = sql_dump.parse_create_table_defaults(path, table) if path.is_file() else {}
    return [{c: row.get(c, defaults.get(c)) for c in COLUMNS} for row in rows]


def load_live() -> tuple[list[dict], list[dict]]:
    """The replayed `creature_loot_template` and `reference_loot_template` rows (base dump, migrations, pending and
    module SQL, in apply order; cached like every replayed table), every column filled."""
    return (
        _with_defaults(CREATURE_LOOT, trainer_state.load_replayed_table_rows(CREATURE_LOOT, COLUMNS, KEY_COLUMNS)),
        _with_defaults(REFERENCE_LOOT, trainer_state.load_replayed_table_rows(REFERENCE_LOOT, COLUMNS, KEY_COLUMNS)),
    )


def _group_index(rows: list[dict], entries: set[int]) -> dict[tuple[int, int], list[dict]]:
    out: dict[tuple[int, int], list[dict]] = {}
    for row in rows:
        entry = _int(row.get("Entry"))
        if entry in entries:
            out.setdefault((entry, _int(row.get("GroupId"))), []).append(row)
    return out


def check_live(plan: LootPlan, live_creature: list[dict], live_reference: list[dict], ids_cfg: dict) -> None:
    """The rules that need the live tables: a declared group never drops a row that is not a declared item, and a
    heroic copy group never drops a row that is not in the copy (a generic pool rolls in its own group, never
    instead); a list item also in another group of the same Entry; a live
    reference_loot_template Entry inside the reserved block that no declaration owns."""
    entries = {entry for entry, _ in plan.groups}
    live = _group_index(live_creature, entries)
    declared_refs = set(plan.references)
    for key, rows in sorted(plan.groups.items()):
        entry, group = key
        foreign = []
        for row in live.get(key, []):
            item, ref = _int(row.get("Item")), _int(row.get("Reference"))
            if ref:
                if ref not in declared_refs:
                    foreign.append(f"reference {ref}")
            elif item not in plan.owned_items:
                foreign.append(f"item {item}")
        if foreign:
            plan.errors.append(
                f"{CREATURE_LOOT} {entry} group {group}: the declaration would drop {', '.join(foreign)}, which no "
                f"item() declares; a generic pool rolls in a group of its own, never instead - move it to its own "
                f"group first"
            )
        listed = {r["Item"] for r in rows if not r["Reference"]}
        listed |= {p["Item"] for r in rows if r["Reference"] for p in plan.references.get(r["Reference"], [])}
        for (other_entry, other_group), other_rows in sorted(live.items()):
            if other_entry != entry or (other_entry, other_group) in plan.groups \
                    or (other_entry, other_group) in plan.copies:
                continue
            twice = sorted(listed & {_int(r.get("Item")) for r in other_rows if not _int(r.get("Reference"))})
            if twice:
                plan.warnings.append(f"{CREATURE_LOOT} {entry}: list item(s) {twice} also drop from live group "
                                     f"{other_group} (they could drop twice)")
    # A heroic copy group is rewritten (DELETE + INSERT) as a whole, so a live row in it that the copy does not hold
    # would be dropped without a word: it is a foreign row as much as one in a declared group.
    copy_live = _group_index(live_creature, {entry for entry, _ in plan.copies})
    for key, rows in sorted(plan.copies.items()):
        entry, group = key
        held = {(_int(r.get("Item")), _int(r.get("Reference"))) for r in rows}
        foreign = []
        for row in copy_live.get(key, []):
            item, ref = _int(row.get("Item")), _int(row.get("Reference"))
            if (item, ref) not in held:
                foreign.append(f"reference {ref}" if ref else f"item {item}")
        if foreign:
            plan.errors.append(
                f"{CREATURE_LOOT} {entry} group {group}: the copy of normal lootid {plan.heroic_sources.get(entry)}'s "
                f"group {group} would drop {', '.join(foreign)}, which that group does not hold; a generic pool "
                f"rolls in a group of its own, never inside a copied one - move it to its own group first"
            )
    block = ids_cfg.get(REFERENCE_BLOCK)
    if block:
        unowned = sorted({
            _int(r.get("Entry")) for r in live_reference
            if block["start"] <= _int(r.get("Entry")) <= block["end"] and _int(r.get("Entry")) not in declared_refs
        })
        if unowned:
            plan.errors.append(
                f"{REFERENCE_LOOT}: live Entry {', '.join(map(str, unowned))} sits in the {REFERENCE_BLOCK} block "
                f"({block['start']}-{block['end']}) but no boss_loot() owns it"
            )


# ---------------------------------------------------------------------------------------------------------------------
# Rendering


def _canonical(rows) -> set[tuple]:
    return {tuple(spell_tables._normalise(r.get(c)) for c in COLUMNS) for r in rows}


def _values(rows: list[dict]) -> str:
    rows = sorted(rows, key=lambda r: (r["Entry"], r["GroupId"], r["Reference"], r["Item"]))
    return ",\n".join("(" + ", ".join(sql_out._sql_literal(r[c]) for c in COLUMNS) + ")" for r in rows)


def _insert(table: str, rows: list[dict]) -> str:
    cols = ", ".join(f"`{c}`" for c in COLUMNS)
    return f"INSERT INTO `{table}` ({cols}) VALUES\n{_values(rows)};"


@dataclass
class Rendered:
    blocks: list[str]
    groups: list[tuple[int, int]]  # the (Entry, GroupId) groups written (removals included)
    references: list[int]
    copies: list[tuple[int, int]] = field(default_factory=list)  # the heroic copies written


def render(plan: LootPlan, live_creature: list[dict], live_reference: list[dict]) -> Rendered:
    """One DELETE (+ INSERT) per declared group or reference pool whose rows differ from live; nothing when equal."""
    live = _group_index(live_creature, {entry for entry, _ in plan.groups} | {entry for entry, _ in plan.copies})
    live_refs: dict[int, list[dict]] = {}
    for row in live_reference:
        entry = _int(row.get("Entry"))
        if entry in plan.references:
            live_refs.setdefault(entry, []).append(row)
    out = Rendered([], [], [])
    for ref, rows in sorted(plan.references.items()):
        if _canonical(rows) == _canonical(live_refs.get(ref, [])):
            continue
        out.references.append(ref)
        out.blocks.append(f"DELETE FROM `{REFERENCE_LOOT}` WHERE `Entry` = {ref};\n{_insert(REFERENCE_LOOT, rows)}")
    for key, rows in sorted(plan.groups.items()):
        entry, group = key
        have = live.get(key, [])
        if _canonical(rows) == _canonical(have):
            continue
        delete = f"DELETE FROM `{CREATURE_LOOT}` WHERE `Entry` = {entry} AND `GroupId` = {group};"
        if not rows:
            if not have:
                continue
            why = plan.removals.get(key, "")
            out.blocks.append(f"-- {CREATURE_LOOT} {entry} group {group} removed: {why}\n{delete}")
        else:
            out.blocks.append(f"{delete}\n{_insert(CREATURE_LOOT, rows)}")
        out.groups.append(key)
    for key, rows in sorted(plan.copies.items()):
        entry, group = key
        if _canonical(rows) == _canonical(live.get(key, [])):
            continue
        out.blocks.append(
            f"-- {CREATURE_LOOT} {entry} group {group}: copy of normal lootid {plan.heroic_sources[entry]}'s group "
            f"{group}\nDELETE FROM `{CREATURE_LOOT}` WHERE `Entry` = {entry} AND `GroupId` = {group};\n"
            f"{_insert(CREATURE_LOOT, rows)}"
        )
        out.copies.append(key)
    return out


def summary_notes(plan: LootPlan, rendered: Rendered | None) -> list[str]:
    lists = sum(1 for rows in plan.groups.values() if rows)
    notes = [
        f"loot: {lists} list group(s), {len(plan.removals)} removed group(s), {len(plan.references)} reference "
        f"pool(s) on {len({e for e, _ in plan.groups})} lootid(s), {len(plan.copies)} heroic copy group(s) of "
        f"normal loot"
    ]
    if rendered is not None:
        notes.append(f"loot: differ from live: {len(rendered.groups)} group(s), {len(rendered.references)} pool(s), "
                     f"{len(rendered.copies)} heroic copy group(s)")
    return notes
