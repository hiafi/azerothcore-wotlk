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

**Set tokens.** A list key may be a `set_token()` key (source/items/haunted_set.py; the Haunted tokens): it resolves to
the token's entry for the declared tier through the same difficulty rule as an item (`build(tokens=...)`).

**Stock rows a list replaces.** `boss_loot(replaces_items=, replaces_references=)` and `remove_loot_group(...)` name the
live rows of the group they drop on purpose (a shared pool reference, the Tier 0 helms, cut pieces); any other live
row that no `item()` declares is still an ERROR. `remove_loot_rows()` deletes single item rows (also of group 0), and
the heroic copies are made without them.

**Pools and conditions** (Scholomance F-C4). `remove_reference_pool()` deletes a stock `reference_loot_template` Entry
the lists replaced, refused while any loot row the run leaves in place still references it (`check_live`). Heroic
copies carry the normal rows' loot `conditions` (SourceType 1, SourceGroup = the lootid, SourceEntry = the item), and a
row the run drops takes its conditions with it, as does a removed pool (SourceType 10): `derive_heroic_copies` works
out `plan.conditions`, `render` writes each set that differs from the replayed `conditions` table.
`copy_normal_loot()` gives a heroic lootid with no list the copies alone. The hand-named ids (`remove_loot_rows()`,
`replaces_*`) must exist: an item_template row, a live or removed pool.

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
  of the boss's loot, rolled only when the script added the bit to the creature's loot mode before the kill;
- a `loot_chance()` group is the exception to the equal-chance rule: its rows carry explicit Chances (0 to 100, summing
  to at most 100, MinCount = MaxCount = 1), a row of an item the group already holds is a grouped reference row into
  a one-item pool of its own (`reference_loot_template` Chance 100), and no `boss_loot()` owns the group.
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
# Every other loot table whose rows may name a reference pool (remove_reference_pool() refuses a pool still used).
OTHER_LOOT_TABLES = tuple(f"{name}_loot_template" for name in (
    "gameobject", "item", "pickpocketing", "skinning", "fishing", "disenchant", "prospecting", "milling", "mail",
    "spell", "player",
))
CONDITIONS = "conditions"
CONDITION_COLUMNS = (
    "SourceTypeOrReferenceId", "SourceGroup", "SourceEntry", "SourceId", "ElseGroup", "ConditionTypeOrReference",
    "ConditionTarget", "ConditionValue1", "ConditionValue2", "ConditionValue3", "NegativeCondition", "ErrorType",
    "ErrorTextId", "ScriptName", "Comment",
)
CONDITION_KEY_COLUMNS = CONDITION_COLUMNS[:10]  # the table's primary key
# ConditionMgr.h ConditionSourceType: a loot row's conditions are keyed (SourceGroup = loot Entry, SourceEntry = Item)
SOURCE_CREATURE_LOOT = 1
SOURCE_REFERENCE_LOOT = 10


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
    # (Entry, GroupId) -> (items, references) of the live rows the declaration drops on purpose (replaces_*)
    replaces: dict[tuple[int, int], tuple[frozenset[int], frozenset[int]]] = field(default_factory=dict)
    row_removals: dict[tuple[int, int], tuple[tuple[int, ...], str]] = field(default_factory=dict)  # remove_loot_rows
    copies: dict[tuple[int, int], list[dict]] = field(default_factory=dict)  # (heroic Entry, GroupId) -> rows
    pool_removals: dict[int, str] = field(default_factory=dict)  # remove_reference_pool(): reference Entry -> why
    # remove_loot_rows(references=): (Entry, GroupId) -> the reference rows (Reference ids) it deletes
    row_ref_removals: dict[tuple[int, int], tuple[int, ...]] = field(default_factory=dict)
    # loot_chance(): the (Entry, GroupId) groups of explicit-chance rows (also in `groups`), the one-item pools of their
    # grouped reference rows (also in `references`) and the item_template entries they name
    chance_groups: set[tuple[int, int]] = field(default_factory=set)
    chance_refs: set[int] = field(default_factory=set)
    chance_items: set[int] = field(default_factory=set)
    # The loot conditions this run manages (derive_heroic_copies): (SourceTypeOrReferenceId, SourceGroup) -> (the
    # SourceEntry items it owns there, None for the whole SourceGroup; the rows they must have). A heroic copy's items
    # carry the normal rows' conditions; a row the run drops (and a removed pool) takes its conditions with it.
    conditions: dict[tuple[int, int], tuple[frozenset[int] | None, list[dict]]] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class _Drop:
    """One resolved list entry: an item tier or a set token at the declared tier."""
    entry: int
    name: str
    label: str


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
         reference: int = 0, max_count: int = 1, chance: float = 0) -> dict:
    return {
        "Entry": entry, "Item": item, "Reference": reference, "Chance": chance, "QuestRequired": 0,
        "LootMode": loot_mode,
        # A reference row needs MinCount == MaxCount (LootMgr.cpp CheckLootRefs reports anything else); MaxCount is how
        # many times the pool is rolled.
        "GroupId": group, "MinCount": max_count if reference else 1, "MaxCount": max_count, "Comment": comment,
    }


def build(
    declarations: list[dict], expansion: item_variants.ItemExpansion, *, ids_cfg: dict,
    heroic_pairs: dict[int, int], creature_rows: dict[int, dict], strict_lootid: bool = True,
    tokens: dict | None = None,
) -> LootPlan:
    """Resolves `declarations` (`dsl_classes["loot_declarations"]`) against the item expansion. `heroic_pairs` is
    normal -> heroic creature entry (heroic_ids.lock); `creature_rows` the creature_template rows by entry as this run
    will leave them (live, with the declared and generated heroic rows over them). `strict_lootid=False` (an
    `--only items` run, which renders no creature_template row) makes a heroic row whose lootid is not its own entry
    a WARNING instead of an ERROR. `tokens` is the `set_token()` declarations by key (lib/dsl/sets.py)."""
    plan = LootPlan()
    all_decls: list[loot_dsl.LootDecl] = [entry["_decl"] for entry in declarations]
    if not all_decls:
        return plan
    decls = [d for d in all_decls if d.listing]
    copy_only = [d for d in all_decls if d.copy_only]
    tokens = tokens or {}
    items = {item.decl.key: item for item in expansion.items}
    for item in expansion.items:
        for tier in item.tiers:
            plan.owned_items.add(tier.entry)
            plan.equippable[tier.entry] = item.inventory_type != 0
    for token in tokens.values():
        plan.owned_items.update(entry for _, entry in token.entries)
    for decl in all_decls:
        if decl.row_removal:
            key = (decl.lootid, decl.group)
            if any(d.lootid == decl.lootid and d.group == decl.group for d in decls):
                plan.errors.append(f"{decl.where}: the group is also declared by boss_loot()/remove_loot_group(); "
                                   f"remove its rows there (replaces_items=) instead")
                continue
            plan.row_removals[key] = (decl.rows, decl.why)
            if decl.ref_rows:
                plan.row_ref_removals[key] = decl.ref_rows
    heroic_entries = set(heroic_pairs.values())
    block = ids_cfg.get(REFERENCE_BLOCK)
    for decl in all_decls:
        if not decl.pool_removal:
            continue
        if any(d.reference == decl.reference for d in decls):
            plan.errors.append(f"{decl.where}: the pool is a declared list's (boss_loot(reference=))")
        elif block and block["start"] <= decl.reference <= block["end"]:
            plan.errors.append(f"{decl.where}: the pool is in the {REFERENCE_BLOCK} block ({block['start']}-"
                               f"{block['end']}), whose pools belong to boss_loot(); drop the declaration instead")
        else:
            plan.pool_removals[decl.reference] = decl.why
    for decl in copy_only:
        if decl.lootid not in heroic_entries:
            plan.errors.append(f"{decl.where}: {decl.lootid} is not a heroic creature (heroic_ids.lock); only a "
                               f"heroic lootid copies a normal boss's loot")
        elif any(d.lootid == decl.lootid for d in decls):
            plan.errors.append(f"{decl.where}: the lootid also declares a list (boss_loot() copies the normal loot "
                               f"already)")
    by_entry: dict[int, list[loot_dsl.LootDecl]] = {}
    for decl in decls:
        by_entry.setdefault(decl.lootid, []).append(decl)

    _build_chance_groups(plan, [d for d in decls if d.chance is not None], decls, by_entry, block, creature_rows)

    for decl in decls:
        if decl.chance is not None:
            continue
        where = decl.where
        key = (decl.lootid, decl.group)
        if decl.removal:
            plan.groups[key] = []
            plan.removals[key] = decl.why
            if decl.replaces_items or decl.replaces_references:
                plan.replaces[key] = (frozenset(decl.replaces_items), frozenset(decl.replaces_references))
            continue
        heroic = decl.lootid in heroic_entries
        boss = _boss_name(decl.lootid, creature_rows)
        resolved: list[_Drop] = []
        for item_key in decl.items:
            item = items.get(item_key)
            token = tokens.get(item_key) if item is None else None
            if item is None and token is None:
                plan.errors.append(f"{where}: {item_key!r} is not a resolved item() key (nor a set_token() key; "
                                   f"unknown, or its declaration has errors)")
                continue
            ladder = item.decl.ladder if item is not None else token.ladder
            spec = ladder.tier(decl.tier)
            if spec is None or spec.deferred:
                plan.errors.append(
                    f"{where}: item {item_key!r} has no {'minted ' if spec else ''}tier {decl.tier!r} on ladder "
                    f"{ladder.name!r} ({', '.join(ladder.names)})"
                )
                continue
            want = first_explicit_tier(ladder) if heroic else own_level_tier(ladder)
            if want is None or want.name != spec.name:
                kind = "a heroic creature's lootid" if heroic else "a normal lootid"
                plan.errors.append(
                    f"{where}: item {item_key!r} drops tier {decl.tier!r}, but {kind} drops "
                    f"{repr(want.name) if want else 'no tier'} of ladder {ladder.name!r} "
                    f"(normal: the items' own level; heroic: the first explicit item level)"
                )
                continue
            if item is not None:
                tier = next((t for t in item.tiers if t.tier == decl.tier), None)
                if tier is None:
                    plan.errors.append(f"{where}: item {item_key!r} tier {decl.tier!r} has no item_template entry")
                    continue
                resolved.append(_Drop(tier.entry, _item_name(item, tier), tier.label))
            else:
                resolved.append(_Drop(token.entry(decl.tier), token.name, spec.label))
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
                _row(ref, drop.entry, f"{boss} pool - {drop.name} ({drop.label})",
                     group=REFERENCE_POOL_GROUP, loot_mode=decl.loot_mode)
                for drop in resolved
            ]
            plan.picks[ref] = decl.picks
            rows.append(_row(decl.lootid, ref, f"{boss} - {decl.picks} of the {boss} pool ({resolved[0].label})",
                             group=decl.group, loot_mode=decl.loot_mode, reference=ref, max_count=decl.picks))
        else:
            rows += [
                _row(decl.lootid, drop.entry, f"{boss} - {drop.name} ({drop.label})",
                     group=decl.group, loot_mode=decl.loot_mode)
                for drop in resolved
            ]
        plan.groups[key] = rows
        if decl.replaces_items or decl.replaces_references:
            plan.replaces[key] = (frozenset(decl.replaces_items), frozenset(decl.replaces_references))

    _check_creatures(plan, decls + copy_only, heroic_pairs, creature_rows, strict_lootid)
    normal_of = {h: n for n, h in heroic_pairs.items()}
    for lootid in sorted({d.lootid for d in decls + copy_only if not d.removal} & set(normal_of)):
        normal_row = creature_rows.get(normal_of[lootid])
        source = _int(normal_row.get("lootid")) if normal_row else 0
        if source and source != lootid:
            plan.heroic_sources[lootid] = source
    plan.errors += lint_rows(plan)
    return plan


def _build_chance_groups(
    plan: LootPlan, chance_decls: list[loot_dsl.LootDecl], decls: list[loot_dsl.LootDecl],
    by_entry: dict[int, list[loot_dsl.LootDecl]], block: dict | None, creature_rows: dict[int, dict],
) -> None:
    """The `loot_chance()` groups: each (Entry, GroupId) is the rows of all its declarations (explicit Chance), a
    repeated item a grouped reference row into a one-item pool of the `loot_reference` block."""
    groups: dict[tuple[int, int], list[loot_dsl.LootDecl]] = {}
    for decl in chance_decls:
        groups.setdefault((decl.lootid, decl.group), []).append(decl)
    for key, members in sorted(groups.items()):
        entry, group = key
        members = sorted(members, key=lambda d: (d.item_entry, d.reference or 0))
        owner = next((d for d in decls if (d.lootid, d.group) == key and d.chance is None), None)
        if owner is not None:
            plan.errors.append(f"{members[0].where}: group {group} of lootid {entry} is also declared by "
                               f"{owner.where}; a group is loot_chance() rows or one list, never both")
            continue
        boss = _boss_name(entry, creature_rows)
        rows: list[dict] = []
        valid = True
        for decl in members:
            where = decl.where
            if decl.loot_mode & loot_dsl.LOOT_MODE_DEFAULT and decl.loot_mode != loot_dsl.LOOT_MODE_DEFAULT:
                plan.errors.append(f"{where}: loot_mode={decl.loot_mode} includes LOOT_MODE_DEFAULT (1) beside other "
                                   f"bits; a row rolls on default kills (1) or on its own bit only")
                valid = False
            elif decl.loot_mode != loot_dsl.LOOT_MODE_DEFAULT and not any(
                    d.loot_mode == loot_dsl.LOOT_MODE_DEFAULT and not d.removal for d in by_entry[entry]):
                plan.errors.append(f"{where}: a loot_mode={decl.loot_mode} row drops on top of the boss's loot, but "
                                   f"lootid {entry} declares no default group")
                valid = False
            name = decl.label or f"item {decl.item_entry}"
            comment = f"{boss} - {name} ({decl.chance:g}%)"
            plan.chance_items.add(decl.item_entry)
            if decl.reference is None:
                rows.append(_row(entry, decl.item_entry, comment, group=group, loot_mode=decl.loot_mode,
                                 chance=decl.chance))
                continue
            ref = decl.reference
            if block is None:
                plan.errors.append(f"{where}: source/ids.yaml has no {REFERENCE_BLOCK} block")
                valid = False
            elif not block["start"] <= ref <= block["end"]:
                plan.errors.append(f"{where}: reference={ref} is outside source/ids.yaml's {REFERENCE_BLOCK} block "
                                   f"({block['start']}-{block['end']})")
                valid = False
            elif ref in plan.references:
                plan.errors.append(f"{where}: reference={ref} is already another declaration's pool")
                valid = False
            else:
                plan.references[ref] = [
                    _row(ref, decl.item_entry, f"{boss} - {name} (pool of the {decl.chance:g}% row)",
                         group=0, loot_mode=decl.loot_mode, chance=100)
                ]
                plan.chance_refs.add(ref)
            rows.append(_row(entry, ref, f"{comment} via pool {ref}", group=group, loot_mode=decl.loot_mode,
                             reference=ref, chance=decl.chance))
        if not valid:
            continue
        plan.groups[key] = rows
        plan.chance_groups.add(key)
        items = frozenset(i for d in members for i in d.replaces_items)
        refs = frozenset(r for d in members for r in d.replaces_references)
        if items or refs:
            plan.replaces[key] = (items, refs)


def derive_heroic_copies(plan: LootPlan, live_creature: list[dict], live_conditions: list[dict] | None = None) -> None:
    """Every live group of a heroic list's normal lootid that no declaration owns (group 0's cloth, food and quest
    items, a generic world loot reference in its own group) is copied unchanged onto the heroic lootid: the boss's
    generic pools roll on top of the list on heroic too, never instead. Derived from the replayed normal rows each
    run, so a rerun is silent and a later change to a normal group follows. A copy that lands on a declared heroic
    group is an ERROR; a live heroic group that is neither declared nor a copy any more is a WARNING (never pruned).

    `live_conditions` (the replayed `conditions` rows; None skips this) gives every copied item row the normal row's
    loot conditions (Ras's head needs his human form, a Scourgestone the Argent Dawn Commission, a recipe the
    profession), and drops the conditions of every loot row and pool the run deletes (`derive_conditions`)."""
    _derive_copies(plan, live_creature)
    if live_conditions is not None:
        derive_conditions(plan, live_creature, live_conditions)


def _derive_copies(plan: LootPlan, live_creature: list[dict]) -> None:
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
            rows = _without_removed(plan, (normal, group), rows)
            if rows:
                plan.copies[(heroic, group)] = [{**{c: r.get(c) for c in COLUMNS}, "Entry": heroic} for r in rows]
        for (entry, group) in sorted(live):
            if entry == heroic and (heroic, group) not in plan.groups and (heroic, group) not in plan.copies:
                plan.warnings.append(f"{CREATURE_LOOT} {heroic} group {group}: live, but neither declared nor a "
                                     f"copy of normal lootid {normal} any more; left in place")


def _loot_items(rows) -> set[int]:
    """The Item of every plain item row (a condition's SourceEntry)."""
    return {_int(r.get("Item")) for r in rows if not _int(r.get("Reference"))}


def derive_conditions(plan: LootPlan, live_creature: list[dict], live_conditions: list[dict]) -> None:
    """`plan.conditions`: what the loot conditions on the lootids and pools this run writes must be.

    - A heroic copy's item rows get the normal lootid's conditions on the same items (SourceGroup = the heroic
      lootid). The copy owns those items' conditions on the heroic lootid.
    - A plain item row the run drops from a lootid (a replaced list row, a removed group, a `remove_loot_rows()` row)
      takes its conditions with it, unless the item still drops from the lootid: an orphaned condition is a boot
      ERROR (ConditionMgr: "SourceGroup ... does not exist in creature_loot_template").
    - A removed pool (`remove_reference_pool()`) takes every condition of its Entry."""
    by_group = _condition_index(live_conditions)
    owned: dict[tuple[int, int], set[int]] = {}
    wanted: dict[tuple[int, int], list[dict]] = {}
    for (heroic, group), rows in sorted(plan.copies.items()):
        normal = plan.heroic_sources[heroic]
        items = _loot_items(rows)
        key = (SOURCE_CREATURE_LOOT, heroic)
        owned.setdefault(key, set()).update(items)
        wanted.setdefault(key, []).extend(
            {**{c: r.get(c) for c in CONDITION_COLUMNS}, "SourceGroup": heroic}
            for r in by_group.get((SOURCE_CREATURE_LOOT, normal), []) if _int(r.get("SourceEntry")) in items
        )
    touched = {e for e, _ in plan.groups} | {e for e, _ in plan.row_removals} | {e for e, _ in plan.copies}
    live = _group_index(live_creature, touched)
    for entry in sorted(touched):
        before, after = set(), set()
        for (live_entry, group), rows in live.items():
            if live_entry != entry:
                continue
            before |= _loot_items(rows)
            if (entry, group) not in plan.groups and (entry, group) not in plan.copies:
                after |= _loot_items(_without_removed(plan, (entry, group), rows))
        for (plan_entry, _group), rows in list(plan.groups.items()) + list(plan.copies.items()):
            if plan_entry == entry:
                after |= _loot_items(rows)
        conditioned = {_int(r.get("SourceEntry")) for r in by_group.get((SOURCE_CREATURE_LOOT, entry), [])}
        dropped = (before - after) & conditioned
        if dropped:
            owned.setdefault((SOURCE_CREATURE_LOOT, entry), set()).update(dropped)
    for key, items in owned.items():
        plan.conditions[key] = (frozenset(items), wanted.get(key, []))
    for ref in plan.pool_removals:
        plan.conditions[(SOURCE_REFERENCE_LOOT, ref)] = (None, [])


def _condition_index(rows: list[dict]) -> dict[tuple[int, int], list[dict]]:
    """The loot conditions (creature and reference loot) by (SourceTypeOrReferenceId, SourceGroup)."""
    out: dict[tuple[int, int], list[dict]] = {}
    for row in rows:
        key = (_int(row.get("SourceTypeOrReferenceId")), _int(row.get("SourceGroup")))
        if key[0] in (SOURCE_CREATURE_LOOT, SOURCE_REFERENCE_LOOT):
            out.setdefault(key, []).append(row)
    return out


def _without_removed(plan: LootPlan, key: tuple[int, int], rows: list[dict]) -> list[dict]:
    """`rows` of group `key` without the item rows a `remove_loot_rows()` deletes."""
    removed = set(plan.row_removals.get(key, ((), ""))[0])
    removed_refs = set(plan.row_ref_removals.get(key, ()))
    return [r for r in rows
            if (_int(r.get("Reference")) not in removed_refs if _int(r.get("Reference"))
                else _int(r.get("Item")) not in removed)]


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
        if (entry, group) in plan.chance_groups:
            errors += _chance_errors(where, rows, plan)
            continue
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
        if ref in plan.chance_refs:
            if len(rows) != 1 or any(
                float(r["Chance"]) != 100 or r["GroupId"] != 0 or r["Reference"] or r["MinCount"] != 1
                or r["MaxCount"] != 1 or r["QuestRequired"] for r in rows
            ):
                errors.append(f"{where}: a loot_chance() pool holds its one item ungrouped at Chance 100, drops once")
            continue
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


def _chance_errors(where: str, rows: list[dict], plan: LootPlan) -> list[str]:
    """The rules of a `loot_chance()` group: explicit Chances in (0, 100] summing to at most 100 (the engine refuses
    more, `LootGroup::Verify`), every row drops once, a reference row is a declared one-item pool's."""
    errors = []
    for row in rows:
        chance = float(row["Chance"])
        if not 0 < chance <= 100:
            errors.append(f"{where}: item {row['Item']} has Chance {row['Chance']} (an explicit chance is 0-100)")
        if row["MinCount"] != 1 or row["MaxCount"] != 1:
            errors.append(f"{where}: item {row['Item']} has MinCount {row['MinCount']} / MaxCount {row['MaxCount']} "
                          f"(a chance row drops once)")
        if row["QuestRequired"]:
            errors.append(f"{where}: item {row['Item']} is a quest drop")
        if row["Reference"] and (row["Item"] != row["Reference"] or row["Reference"] not in plan.chance_refs):
            errors.append(f"{where}: reference {row['Reference']} is not a declared loot_chance() pool")
    if sum(float(r["Chance"]) for r in rows) > 100 + 1e-9:
        errors.append(f"{where}: the chances add up to {sum(float(r['Chance']) for r in rows):g}% (more than 100)")
    seen = [(r["Item"], r["Reference"]) for r in rows]
    if len(set(seen)) != len(seen):
        errors.append(f"{where}: an item is listed twice")
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


def load_live_conditions() -> list[dict]:
    """The replayed `conditions` rows (every column filled), for the loot conditions derive_heroic_copies manages."""
    path = trainer_state.BASE_SQL_DIR / f"{CONDITIONS}.sql"
    defaults = sql_dump.parse_create_table_defaults(path, CONDITIONS) if path.is_file() else {}
    rows = trainer_state.load_replayed_table_rows(CONDITIONS, CONDITION_COLUMNS, CONDITION_KEY_COLUMNS)
    return [{c: row.get(c, defaults.get(c)) for c in CONDITION_COLUMNS} for row in rows]


def load_other_loot() -> dict[str, list[dict]]:
    """The replayed rows of every other loot table that may name a pool (OTHER_LOOT_TABLES), by table: only a run
    with a remove_reference_pool() needs them."""
    out = {}
    for table in OTHER_LOOT_TABLES:
        if (trainer_state.BASE_SQL_DIR / f"{table}.sql").is_file():
            out[table] = trainer_state.load_replayed_table_rows(table, COLUMNS, KEY_COLUMNS)
    return out


def _group_index(rows: list[dict], entries: set[int]) -> dict[tuple[int, int], list[dict]]:
    out: dict[tuple[int, int], list[dict]] = {}
    for row in rows:
        entry = _int(row.get("Entry"))
        if entry in entries:
            out.setdefault((entry, _int(row.get("GroupId"))), []).append(row)
    return out


def check_live(
    plan: LootPlan, live_creature: list[dict], live_reference: list[dict], ids_cfg: dict, *,
    item_entries=None, other_loot: dict[str, list[dict]] | None = None,
) -> None:
    """The rules that need the live tables: a declared group never drops a row that is not a declared item, and a
    heroic copy group never drops a row that is not in the copy (a generic pool rolls in its own group, never
    instead); a list item also in another group of the same Entry; a live
    reference_loot_template Entry inside the reserved block that no declaration owns; a removed pool that a loot row
    the run leaves in place still references (`other_loot`: the other loot tables by name, see OTHER_LOOT_TABLES); a
    `remove_loot_rows()` or `replaces_items=` item with no `item_template` row (`item_entries`, when given), and a
    `replaces_references=` pool that is neither live nor removed by `remove_reference_pool()` (a typo is silent
    otherwise)."""
    _check_named_ids(plan, live_reference, item_entries)
    _check_pool_users(plan, live_creature, live_reference, other_loot or {})
    entries = {entry for entry, _ in plan.groups}
    live = _group_index(live_creature, entries)
    declared_refs = set(plan.references)
    for key, rows in sorted(plan.groups.items()):
        entry, group = key
        foreign = []
        replaced_items, replaced_refs = plan.replaces.get(key, (frozenset(), frozenset()))
        held = {(_int(r.get("Item")), _int(r.get("Reference"))) for r in rows}
        for row in live.get(key, []):
            item, ref = _int(row.get("Item")), _int(row.get("Reference"))
            if (item, ref) in held and key in plan.chance_groups:
                continue  # a chance row the declaration rewrites (the Reins' own row)
            if ref:
                if ref not in declared_refs and ref not in replaced_refs:
                    foreign.append(f"reference {ref}")
            elif item not in plan.owned_items and item not in replaced_items:
                foreign.append(f"item {item}")
        if foreign:
            plan.errors.append(
                f"{CREATURE_LOOT} {entry} group {group}: the declaration would drop {', '.join(foreign)}, which no "
                f"item() declares; a generic pool rolls in a group of its own, never instead - move it to its own "
                f"group first (or name the stock row in replaces_items= / replaces_references= when the list "
                f"replaces it)"
            )
        listed = {r["Item"] for r in rows if not r["Reference"]}
        listed |= {p["Item"] for r in rows if r["Reference"] for p in plan.references.get(r["Reference"], [])}
        for (other_entry, other_group), other_rows in sorted(live.items()):
            if other_entry != entry or (other_entry, other_group) in plan.groups \
                    or (other_entry, other_group) in plan.copies:
                continue
            other_rows = _without_removed(plan, (other_entry, other_group), other_rows)
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


def _check_named_ids(plan: LootPlan, live_reference: list[dict], item_entries) -> None:
    """The ids a declaration names by hand (removed rows, replaced stock rows) exist: a mistyped one matches no row,
    so it would never be deleted and nothing would say so."""
    pools = {_int(r.get("Entry")) for r in live_reference} | set(plan.pool_removals)
    known = None if item_entries is None else {_int(e) for e in item_entries}
    for (entry, group), refs in sorted(plan.row_ref_removals.items()):
        missing = sorted(r for r in refs if r not in pools)
        if missing:
            plan.errors.append(f"remove_loot_rows({entry}, group={group}): references= names {missing}, which is "
                               f"no {REFERENCE_LOOT} Entry (live or removed by remove_reference_pool())")
    if known is not None:
        unknown = sorted(i for i in plan.chance_items if i not in known)
        if unknown:
            plan.errors.append(f"loot_chance(): {unknown} has no item_template row")
    for (entry, group), (items, refs) in sorted(plan.replaces.items()):
        missing = sorted(r for r in refs if r not in pools)
        if missing:
            plan.errors.append(f"{CREATURE_LOOT} {entry} group {group}: replaces_references= names {missing}, which is "
                               f"no {REFERENCE_LOOT} Entry (live or removed by remove_reference_pool())")
        unknown = [] if known is None else sorted(i for i in items if i not in known)
        if unknown:
            plan.errors.append(f"{CREATURE_LOOT} {entry} group {group}: replaces_items= names {unknown}, which has "
                               f"no item_template row")
    if known is None:
        return
    for (entry, group), (items, _why) in sorted(plan.row_removals.items()):
        unknown = sorted(i for i in items if i not in known)
        if unknown:
            plan.errors.append(f"remove_loot_rows({entry}, group={group}): {unknown} has no item_template row (a "
                               f"mistyped entry would remove nothing)")


def _check_pool_users(plan: LootPlan, live_creature: list[dict], live_reference: list[dict],
                      other_loot: dict[str, list[dict]]) -> None:
    """A removed pool must be unused once the run's rows are in: no creature loot row outside the declared groups
    (whose rows the run replaces), no row the run writes, no other pool and no row of another loot table refers to
    it."""
    if not plan.pool_removals:
        return
    users: dict[int, list[str]] = {}

    def note(ref: int, where: str) -> None:
        if ref in plan.pool_removals:
            users.setdefault(ref, []).append(where)

    for row in live_creature:
        key = (_int(row.get("Entry")), _int(row.get("GroupId")))
        if key not in plan.groups and key not in plan.copies:
            if _int(row.get("Reference")) in plan.row_ref_removals.get(key, ()):
                continue  # remove_loot_rows(references=) deletes this row
            note(_int(row.get("Reference")), f"{CREATURE_LOOT} {key[0]} group {key[1]}")
    for (entry, group), rows in list(plan.groups.items()) + list(plan.copies.items()):
        for row in rows:
            note(_int(row.get("Reference")), f"{CREATURE_LOOT} {entry} group {group} (declared)")
    for row in live_reference:
        entry = _int(row.get("Entry"))
        if entry not in plan.references and entry not in plan.pool_removals:
            note(_int(row.get("Reference")), f"{REFERENCE_LOOT} {entry}")
    for rows in plan.references.values():
        for row in rows:
            note(_int(row.get("Reference")), f"{REFERENCE_LOOT} {row['Entry']} (declared)")
    for table, rows in sorted(other_loot.items()):
        for row in rows:
            note(_int(row.get("Reference")), f"{table} {_int(row.get('Entry'))}")
    for ref, where in sorted(users.items()):
        plan.errors.append(f"remove_reference_pool({ref}): still referenced by {', '.join(sorted(set(where))[:6])}; "
                           f"a removed pool must be unused")


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
    row_removals: list[tuple[int, int]] = field(default_factory=list)  # the remove_loot_rows() groups written
    pool_removals: list[int] = field(default_factory=list)  # the remove_reference_pool() pools written
    conditions: list[tuple[int, int]] = field(default_factory=list)  # the (SourceType, SourceGroup) condition sets


def render(plan: LootPlan, live_creature: list[dict], live_reference: list[dict],
           live_conditions: list[dict] | None = None) -> Rendered:
    """One DELETE (+ INSERT) per declared group or reference pool whose rows differ from live; nothing when equal.
    The managed loot conditions (`plan.conditions`, from derive_heroic_copies) render the same way against
    `live_conditions`."""
    live = _group_index(live_creature, {entry for entry, _ in plan.groups} | {entry for entry, _ in plan.copies}
                        | {entry for entry, _ in plan.row_removals})
    live_refs: dict[int, list[dict]] = {}
    for row in live_reference:
        entry = _int(row.get("Entry"))
        if entry in plan.references or entry in plan.pool_removals:
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
    for key, (items, why) in sorted(plan.row_removals.items()):
        entry, group = key
        present = sorted({_int(r.get("Item")) for r in live.get(key, [])
                          if not _int(r.get("Reference")) and _int(r.get("Item")) in set(items)})
        present_refs = sorted({_int(r.get("Reference")) for r in live.get(key, [])
                               if _int(r.get("Reference")) in set(plan.row_ref_removals.get(key, ()))})
        if not present and not present_refs:
            continue
        where = f"`Entry` = {entry} AND `GroupId` = {group}"
        statements = []
        if present:
            statements.append(f"DELETE FROM `{CREATURE_LOOT}` WHERE {where} AND `Reference` = 0 AND "
                              f"`Item` IN ({', '.join(map(str, present))});")
        if present_refs:
            statements.append(f"DELETE FROM `{CREATURE_LOOT}` WHERE {where} AND "
                              f"`Reference` IN ({', '.join(map(str, present_refs))});")
        out.blocks.append(f"-- {CREATURE_LOOT} {entry} group {group}: rows removed ({why})\n" + "\n".join(statements))
        out.row_removals.append(key)
    for ref, why in sorted(plan.pool_removals.items()):
        if not live_refs.get(ref):
            continue
        out.blocks.append(f"-- {REFERENCE_LOOT} {ref} removed: {why}\n"
                          f"DELETE FROM `{REFERENCE_LOOT}` WHERE `Entry` = {ref};")
        out.pool_removals.append(ref)
    live_conds = _condition_index(live_conditions or [])
    for (source, group), (items, rows) in sorted(plan.conditions.items()):
        have = [r for r in live_conds.get((source, group), [])
                if items is None or _int(r.get("SourceEntry")) in items]
        if _condition_canonical(rows) == _condition_canonical(have):
            continue
        where = f"`SourceTypeOrReferenceId` = {source} AND `SourceGroup` = {group}"
        if items is not None:
            entries = sorted({_int(r.get("SourceEntry")) for r in have + rows})
            where += f" AND `SourceEntry` IN ({', '.join(map(str, entries))})"
        table = CREATURE_LOOT if source == SOURCE_CREATURE_LOOT else REFERENCE_LOOT
        block = f"-- {CONDITIONS} of {table} {group}\nDELETE FROM `{CONDITIONS}` WHERE {where};"
        if rows:
            cols = ", ".join(f"`{c}`" for c in CONDITION_COLUMNS)
            ordered = sorted(rows, key=lambda r: tuple(_int(r.get(c)) for c in CONDITION_KEY_COLUMNS))
            values = ",\n".join("(" + ", ".join(sql_out._sql_literal(r.get(c)) for c in CONDITION_COLUMNS) + ")"
                                for r in ordered)
            block += f"\nINSERT INTO `{CONDITIONS}` ({cols}) VALUES\n{values};"
        out.blocks.append(block)
        out.conditions.append((source, group))
    return out


def _condition_canonical(rows) -> set[tuple]:
    return {tuple(spell_tables._normalise(r.get(c)) for c in CONDITION_COLUMNS) for r in rows}


def summary_notes(plan: LootPlan, rendered: Rendered | None) -> list[str]:
    lists = sum(1 for rows in plan.groups.values() if rows)
    notes = [
        f"loot: {lists} list group(s) ({len(plan.chance_groups)} of them loot_chance()), "
        f"{len(plan.removals)} removed group(s), {len(plan.references)} reference "
        f"pool(s) on {len({e for e, _ in plan.groups})} lootid(s), {len(plan.copies)} heroic copy group(s) of "
        f"normal loot, {len(plan.row_removals)} row removal group(s) "
        f"({sum(len(items) for items, _ in plan.row_removals.values())} row(s)), {len(plan.pool_removals)} pool "
        f"removal(s), {len(plan.conditions)} managed loot condition set(s)"
    ]
    if rendered is not None:
        notes.append(f"loot: differ from live: {len(rendered.groups)} group(s), {len(rendered.references)} pool(s), "
                     f"{len(rendered.copies)} heroic copy group(s), {len(rendered.row_removals)} row removal(s), "
                     f"{len(rendered.pool_removals)} pool removal(s), {len(rendered.conditions)} condition set(s)")
    return notes
