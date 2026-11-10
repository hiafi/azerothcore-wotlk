"""
Boss loot declarations (item-variants plan v2 section 7.3, stage IV7): a boss's list as one loot group of `item()`
keys at one ladder tier, emitted by lib/loot_tables.py as `creature_loot_template` rows keyed (Entry, GroupId).

    from lib.dsl.loot import boss_loot, copy_normal_loot, remove_loot_group, remove_reference_pool

    boss_loot(644, ("dm_rhahkzors_hammer", "dm_rockslicer"), tier="normal")              # Rhahk'Zor, normal
    boss_loot(310008, ("dm_rhahkzors_hammer", "dm_rockslicer"), tier="heroic")           # his heroic body
    boss_loot(643, SNEED_POOL, tier="normal", picks=2, reference=1700000)               # two distinct items
    boss_loot(310004, VANCLEEF_HARD_MODE, tier="heroic_hm", group=2, loot_mode=2)       # lit kills only
    remove_loot_group(642, group=1, why="the Shredder's items moved into Sneed's pool")
    remove_reference_pool(35030, why="Ras's list replaced his two rolls on it")         # a stock pool, unused now
    copy_normal_loot(310070, why="the encounter's list is on Vectus")                   # heroic Marduk: copies only
    loot_chance(310160, 13335, 2, group=4)                                              # a drop at an explicit chance
    loot_chance(310160, 13335, 8, group=4, loot_mode=2, reference=1700008)             # ... and a hard mode extra

**The loot rule** (docs/dungeons/boss-rework-systems.md section 2, Loot lists): every boss list is one loot group of
equal-chance entries (Chance 0), so the group always yields an item; a stock generic pool kept on the boss rolls in a
group of its own, never in the list's. So a list has no chances to give: every row is Chance 0, MinCount and MaxCount
1. Rows outside the declared groups (group 0's cloth, food and quest items, a generic reference in its own group) are
never touched.

**`picks=N`** (a list that drops N distinct items, Sneed's pool) puts one reference row in the group (`Reference` R,
`MaxCount` N, Chance 0) and the list in `reference_loot_template` R, group 1, Chance 0. The engine processes the
reference N times, and a group roll skips an equippable item the loot already holds from the same group, so the N
items are distinct (`LootGroupInvalidSelector`, LootMgr.cpp). `reference=` is the id, from source/ids.yaml's
`loot_reference` block; a shipped id never moves.

**`loot_mode`** is the rows' `LootMode` bit: the default 1 (`LOOT_MODE_DEFAULT`) always rolls; 2
(`LOOT_MODE_HARD_MODE_1`) rolls only when the creature's loot mode has it at death, which the boss script sets with
`AddLootMode` while its hard mode is lit (Ulduar's mechanism; the loot is filled in `Unit::Kill` with
`creature->GetLootMode()`, before `JustDied`).

**`tier`** is the ladder tier name every item drops at (lib/dsl/items.py, the lock file's tier column). A normal
lootid drops the items' own-level tier (the ladder's first tier without an `ilvl=`); a heroic creature's own lootid
drops the ladder's first tier with an explicit item level (Heroic, or Heroic Hard Mode): lib/loot_tables.py checks it.

`remove_loot_group()` deletes one stock group outright (the Shredder's, whose items moved into Sneed's pool). Its live
rows must all be items some `item()` declares (or the removal's `replaces_*`), so a generic pool is never dropped by it.

**`replaces_items=` / `replaces_references=`** (Scholomance, WP-L) name the stock rows of a declared group that the
declaration intentionally drops: a per-boss list replaces the instructors' shared pool (reference 35031), the Tier 0
helms and the cut pieces. A live row of the group that is neither an `item()` entry nor listed here is still an ERROR
(a generic pool rolls in a group of its own, never instead). Items are `item_template` entries, references are
`reference_loot_template` Entries (the Reference column).

`remove_loot_rows()` deletes single rows (by Item) of one group, group 0 included: the Tier 0 trash drops and the cut
stock pieces that sit in a boss's ungrouped rows. Plain item rows (Reference 0) are matched by `items`; `references=`
names reference rows (the stock pool a boss rolls in his ungrouped rows, the Baron's 35028). It never touches a group a
`boss_loot()` owns, and the heroic copies (lib/loot_tables.py derive_heroic_copies) are made from the live rows without
the removed ones.

**`loot_chance()`** (Stratholme, WP-L-1) is the one thing a list cannot be: a row at an explicit chance, the only way
to roll a rare drop (Deathcharger's Reins) at a chance of its own. A group of `loot_chance()` rows is one loot group
whose explicit chances are rolled in turn (`LootGroup::Roll`), so it yields at most one of its rows per kill, and a row
whose `LootMode` bit is not on the kill's loot mode sits out (`LootGroupInvalidSelector`): a normal heroic kill (mode
1) rolls the 2% row only, a hard mode kill (mode 1 | 2) rolls the 2% and the 8% row, 10% in all, never two drops.
`creature_loot_template`'s key is (Entry, Item, Reference, GroupId), so a group cannot hold one item twice: the second
row of an item names `reference=` (a `reference_loot_template` Entry of the `loot_reference` block), which makes it a
grouped reference row (`Item` = `Reference` = the pool, MaxCount 1) into a pool that holds the item alone. A group is
declared by `loot_chance()` or by `boss_loot()`, never both; `replaces_items=` / `replaces_references=` name the live
rows of the group the declaration drops on purpose, as for `boss_loot()`.

**Set tokens.** A key of `boss_loot()` may also be a `set_token()` key (source/items/haunted_set.py): it resolves to the
token's entry at the declared tier, which is the token the kill gives (Normal on a normal lootid, Heroic on a heroic
one). A token drops from a group of its own (one equal-chance entry always drops).

`remove_reference_pool()` deletes a whole stock `reference_loot_template` Entry that nothing uses once the lists
replace it (an unused Entry is a boot ERROR). lib/loot_tables.py refuses it while a loot row of any loot table still
references it after the run.

`copy_normal_loot()` gives a heroic lootid with no list of its own (Marduk, whose encounter list Vectus carries) the
copies of its normal boss's groups. Every heroic copy carries the normal rows' loot `conditions` (a quest step, a
reputation aura, a profession), and a loot row a declaration drops takes its conditions with it.

Registered into `Registry.loot_declarations` keyed on (lootid, group): one declaration per group (row removals are keyed
on ("loot-rows", lootid, group), pool removals on ("loot-pool", reference, 0), copies on ("loot-copy", lootid, 0), a
chance row on ("loot-chance", lootid, group, item, reference or 0): the group is theirs together).
"""

from __future__ import annotations

from dataclasses import dataclass

from . import registry as _registry

LOOT_MODE_DEFAULT = 0x1  # SharedDefines.h LootModes
LOOT_MODE_HARD_MODE_1 = 0x2
MAX_GROUP_ID = (1 << 7) - 1  # LootStoreItem::IsValid: GroupId is a 7 bit field
MAX_COUNT = 255  # MaxCount is a tinyint unsigned


class LootDeclarationError(ValueError):
    pass


@dataclass(frozen=True)
class LootDecl:
    lootid: int
    group: int
    items: tuple[str, ...] = ()
    tier: str = ""
    picks: int = 1
    reference: int | None = None
    loot_mode: int = LOOT_MODE_DEFAULT
    removal: bool = False  # remove_loot_group(): DELETE the group, insert nothing
    why: str = ""
    replaces_items: tuple[int, ...] = ()  # live item rows of the group this declaration drops on purpose
    replaces_references: tuple[int, ...] = ()  # live reference rows of the group it drops on purpose
    row_removal: bool = False  # remove_loot_rows(): DELETE the item rows `rows` of the group
    rows: tuple[int, ...] = ()
    pool_removal: bool = False  # remove_reference_pool(): DELETE reference_loot_template Entry `reference`
    copy_only: bool = False  # copy_normal_loot(): a heroic lootid with no list, only the copies of its normal loot
    ref_rows: tuple[int, ...] = ()  # remove_loot_rows(references=): the reference rows (Reference ids) it deletes too
    chance: float | None = None  # loot_chance(): the row's explicit Chance (percent); None for every other kind
    item_entry: int = 0  # loot_chance(): the item_template entry of the row
    label: str = ""  # loot_chance(): the item's name for the row comment

    @property
    def listing(self) -> bool:
        """A boss_loot() or remove_loot_group() declaration (one (lootid, group) of creature_loot_template)."""
        return not (self.row_removal or self.pool_removal or self.copy_only)

    @property
    def where(self) -> str:
        if self.chance is not None:
            return f"loot_chance({self.lootid}, {self.item_entry}, group={self.group})"
        if self.pool_removal:
            return f"remove_reference_pool({self.reference})"
        if self.copy_only:
            return f"copy_normal_loot({self.lootid})"
        if self.removal:
            return f"remove_loot_group({self.lootid}, group={self.group})"
        if self.row_removal:
            return f"remove_loot_rows({self.lootid}, group={self.group})"
        return f"boss_loot({self.lootid}, group={self.group})"


def _plain_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _check_target(where: str, lootid, group) -> None:
    if not _plain_int(lootid) or lootid <= 0:
        raise LootDeclarationError(f"{where}: lootid must be a positive int (a creature_loot_template Entry)")
    if not _plain_int(group) or not 1 <= group <= MAX_GROUP_ID:
        raise LootDeclarationError(
            f"{where}: group must be an int in 1-{MAX_GROUP_ID} (group 0 is the ungrouped rows, which cannot be "
            f"equal chance)"
        )


def _register(decl: LootDecl) -> LootDecl:
    active = _registry._active
    if active is not None:
        if decl.pool_removal:
            key = ("loot-pool", decl.reference, 0)
        elif decl.copy_only:
            key = ("loot-copy", decl.lootid, 0)
        elif decl.chance is not None:
            key = ("loot-chance", decl.lootid, decl.group, decl.item_entry, decl.reference or 0)
        else:
            key = ("loot-rows" if decl.row_removal else "loot", decl.lootid, decl.group)
        if any(entry["id"] == key for entry in active.loot_declarations):
            hint = (" (a second row of one item in a group needs its own reference=)"
                    if decl.chance is not None else "")
            raise _registry.DuplicateIdError(f"{decl.where}: declared twice{hint}")
        active.loot_declarations.append({"id": key, "_decl": decl})
    return decl


def _check_replaces(where: str, replaces_items, replaces_references) -> tuple[tuple[int, ...], tuple[int, ...]]:
    out = []
    for label, values in (("replaces_items", replaces_items), ("replaces_references", replaces_references)):
        if not isinstance(values, (tuple, list)) or not all(_plain_int(v) and v > 0 for v in values):
            raise LootDeclarationError(f"{where}: {label} must be a tuple of positive ints")
        if len(set(values)) != len(values):
            raise LootDeclarationError(f"{where}: {label} lists an entry twice")
        out.append(tuple(values))
    return out[0], out[1]


def boss_loot(
    lootid: int, items, *, tier: str, group: int = 1, picks: int = 1, reference: int | None = None,
    loot_mode: int = LOOT_MODE_DEFAULT, replaces_items=(), replaces_references=(),
) -> LootDecl:
    """Group `group` of `lootid` becomes the list `items` (`item()` or `set_token()` keys) at ladder tier `tier`, all
    at equal chance; `picks=N` (with `reference=`) drops N distinct items of the list; `loot_mode=2` rolls only on a
    hard mode kill; `replaces_items=` / `replaces_references=` name the stock rows of the group dropped on purpose.
    See the module docstring."""
    where = f"boss_loot({lootid!r}, group={group!r})"
    _check_target(where, lootid, group)
    if isinstance(items, str) or not isinstance(items, (tuple, list)) or not items:
        raise LootDeclarationError(f"{where}: items must be a non-empty tuple of item() keys")
    if not all(isinstance(key, str) and key for key in items):
        raise LootDeclarationError(f"{where}: every item must be an item() key (a non-empty string)")
    duplicates = sorted({key for key in items if list(items).count(key) > 1})
    if duplicates:
        raise LootDeclarationError(f"{where}: {duplicates} listed twice (each item is one equal-chance entry)")
    if not isinstance(tier, str) or not tier:
        raise LootDeclarationError(f"{where}: tier must be a ladder tier name (e.g. 'normal', 'heroic')")
    if not _plain_int(picks) or not 1 <= picks <= min(len(items), MAX_COUNT):
        raise LootDeclarationError(
            f"{where}: picks={picks!r} must be an int from 1 to the list's size ({len(items)}): the picks are "
            f"distinct items"
        )
    if picks > 1 and reference is None:
        raise LootDeclarationError(
            f"{where}: picks={picks} needs reference= (a reference_loot_template id from source/ids.yaml's "
            f"loot_reference block): N distinct items come from one reference row processed N times"
        )
    if picks == 1 and reference is not None:
        raise LootDeclarationError(f"{where}: reference= is only for picks > 1 (a one-item list is the group itself)")
    if reference is not None and (not _plain_int(reference) or reference <= 0):
        raise LootDeclarationError(f"{where}: reference={reference!r} must be a positive int")
    if not _plain_int(loot_mode) or not 1 <= loot_mode <= 0xFFFF:
        raise LootDeclarationError(f"{where}: loot_mode={loot_mode!r} must be a LootMode bit mask (1-65535)")
    replaces_items, replaces_references = _check_replaces(where, replaces_items, replaces_references)
    return _register(LootDecl(
        lootid=lootid, group=group, items=tuple(items), tier=tier, picks=picks, reference=reference,
        loot_mode=loot_mode, replaces_items=replaces_items, replaces_references=replaces_references,
    ))


def loot_chance(
    lootid: int, item: int, chance: float, group: int, loot_mode: int = LOOT_MODE_DEFAULT, *,
    reference: int | None = None, replaces_items=(), replaces_references=(), name: str = "",
) -> LootDecl:
    """One row of group `group` of `lootid`: item_template entry `item` at an explicit `chance` (percent, 0 to 100) on
    kills whose loot mode has a bit of `loot_mode`. The rows of one group (several calls, one per row) are rolled in
    turn and yield at most one drop. `reference=` makes the row a grouped reference row into a one-item pool of that
    id (a second row of the same item in the group needs it: the table's key is Entry, Item, Reference, GroupId).
    `replaces_items=` / `replaces_references=` name the stock rows of the group dropped on purpose; `name` is the
    item's name for the row comment. See the module docstring."""
    where = f"loot_chance({lootid!r}, {item!r}, group={group!r})"
    _check_target(where, lootid, group)
    if not _plain_int(item) or item <= 0:
        raise LootDeclarationError(f"{where}: item must be a positive int (an item_template entry)")
    if isinstance(chance, bool) or not isinstance(chance, (int, float)) or not 0.000001 <= chance <= 100:
        raise LootDeclarationError(f"{where}: chance={chance!r} must be a percent from 0.000001 to 100")
    if not _plain_int(loot_mode) or not 1 <= loot_mode <= 0xFFFF:
        raise LootDeclarationError(f"{where}: loot_mode={loot_mode!r} must be a LootMode bit mask (1-65535)")
    if reference is not None and (not _plain_int(reference) or reference <= 0):
        raise LootDeclarationError(f"{where}: reference={reference!r} must be a positive int")
    if not isinstance(name, str):
        raise LootDeclarationError(f"{where}: name must be a string")
    replaces_items, replaces_references = _check_replaces(where, replaces_items, replaces_references)
    return _register(LootDecl(
        lootid=lootid, group=group, loot_mode=loot_mode, reference=reference, chance=float(chance), item_entry=item,
        label=name.strip(), replaces_items=replaces_items, replaces_references=replaces_references,
    ))


def remove_loot_group(
    lootid: int, *, group: int, why: str, replaces_items=(), replaces_references=(),
) -> LootDecl:
    """Deletes group `group` of `lootid` and inserts nothing (a stock list whose items moved to another boss's
    list). Every live row of the group must be an item some `item()` declares or one of `replaces_*`; `why` is
    printed with the removal."""
    where = f"remove_loot_group({lootid!r}, group={group!r})"
    _check_target(where, lootid, group)
    if not isinstance(why, str) or not why.strip():
        raise LootDeclarationError(f"{where}: why= (where the group's items went) is required")
    replaces_items, replaces_references = _check_replaces(where, replaces_items, replaces_references)
    return _register(LootDecl(
        lootid=lootid, group=group, removal=True, why=why.strip(), replaces_items=replaces_items,
        replaces_references=replaces_references,
    ))


def remove_loot_rows(lootid: int, items=(), *, group: int = 0, why: str, references=()) -> LootDecl:
    """Deletes the plain item rows `items` (`item_template` entries) and the reference rows `references`
    (`reference_loot_template` Entries) of group `group` of `lootid` (a stock Tier 0 drop, a cut piece or a stock pool
    in a boss's ungrouped rows). Other rows of the group stay; `why` is printed with the removal."""
    where = f"remove_loot_rows({lootid!r}, group={group!r})"
    if not _plain_int(lootid) or lootid <= 0:
        raise LootDeclarationError(f"{where}: lootid must be a positive int (a creature_loot_template Entry)")
    if not _plain_int(group) or not 0 <= group <= MAX_GROUP_ID:
        raise LootDeclarationError(f"{where}: group must be an int in 0-{MAX_GROUP_ID}")
    for label, values in (("items", items), ("references", references)):
        if not isinstance(values, (tuple, list)) or not all(_plain_int(v) and v > 0 for v in values):
            raise LootDeclarationError(f"{where}: {label} must be a tuple of positive ints")
        if len(set(values)) != len(values):
            raise LootDeclarationError(f"{where}: {label} lists an entry twice")
    if not items and not references:
        raise LootDeclarationError(f"{where}: items must be a non-empty tuple of item_template entries "
                                   f"(or references= the reference rows to drop)")
    if not isinstance(why, str) or not why.strip():
        raise LootDeclarationError(f"{where}: why= (why the rows go) is required")
    return _register(LootDecl(
        lootid=lootid, group=group, row_removal=True, rows=tuple(items), ref_rows=tuple(references),
        why=why.strip(),
    ))


def remove_reference_pool(reference: int, *, why: str) -> LootDecl:
    """Deletes the whole `reference_loot_template` Entry `reference` (a stock pool every user of which a list now
    replaces; the engine logs an unused reference Entry at boot, `LootStore::ReportUnusedIds`). lib/loot_tables.py
    refuses it while any loot row this run leaves in place still references the pool; its loot conditions go with it.
    `why` is printed with the removal."""
    where = f"remove_reference_pool({reference!r})"
    if not _plain_int(reference) or reference <= 0:
        raise LootDeclarationError(f"{where}: reference must be a positive int (a reference_loot_template Entry)")
    if not isinstance(why, str) or not why.strip():
        raise LootDeclarationError(f"{where}: why= (why nothing uses the pool any more) is required")
    return _register(LootDecl(lootid=0, group=0, reference=reference, pool_removal=True, why=why.strip()))


def copy_normal_loot(lootid: int, *, why: str) -> LootDecl:
    """Heroic lootid `lootid` (a heroic creature's own entry) drops no list of its own, only the copies of its normal
    boss's groups (lib/loot_tables.py derive_heroic_copies, conditions included): a boss whose encounter list another
    boss carries, who keeps his own reagents and quest items. `why` says where the list is."""
    where = f"copy_normal_loot({lootid!r})"
    if not _plain_int(lootid) or lootid <= 0:
        raise LootDeclarationError(f"{where}: lootid must be a positive int (a heroic creature's own entry)")
    if not isinstance(why, str) or not why.strip():
        raise LootDeclarationError(f"{where}: why= (where the boss's list is) is required")
    return _register(LootDecl(lootid=lootid, group=0, copy_only=True, why=why.strip()))
