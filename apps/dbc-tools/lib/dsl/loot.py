"""
Boss loot declarations (item-variants plan v2 section 7.3, stage IV7): a boss's list as one loot group of `item()`
keys at one ladder tier, emitted by lib/loot_tables.py as `creature_loot_template` rows keyed (Entry, GroupId).

    from lib.dsl.loot import boss_loot, remove_loot_group

    boss_loot(644, ("dm_rhahkzors_hammer", "dm_rockslicer"), tier="normal")              # Rhahk'Zor, normal
    boss_loot(310008, ("dm_rhahkzors_hammer", "dm_rockslicer"), tier="heroic")           # his heroic body
    boss_loot(643, SNEED_POOL, tier="normal", picks=2, reference=1700000)               # two distinct items
    boss_loot(310004, VANCLEEF_HARD_MODE, tier="heroic_hm", group=2, loot_mode=2)       # lit kills only
    remove_loot_group(642, group=1, why="the Shredder's items moved into Sneed's pool")

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
rows must all be items some `item()` declares, so a generic pool is never dropped by it.

Registered into `Registry.loot_declarations` keyed on (lootid, group): one declaration per group.
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

    @property
    def where(self) -> str:
        if self.removal:
            return f"remove_loot_group({self.lootid}, group={self.group})"
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
        key = ("loot", decl.lootid, decl.group)
        if any(entry["id"] == key for entry in active.loot_declarations):
            raise _registry.DuplicateIdError(f"{decl.where}: the group is declared twice")
        active.loot_declarations.append({"id": key, "_decl": decl})
    return decl


def boss_loot(
    lootid: int, items, *, tier: str, group: int = 1, picks: int = 1, reference: int | None = None,
    loot_mode: int = LOOT_MODE_DEFAULT,
) -> LootDecl:
    """Group `group` of `lootid` becomes the list `items` (`item()` keys) at ladder tier `tier`, all at equal
    chance; `picks=N` (with `reference=`) drops N distinct items of the list; `loot_mode=2` rolls only on a hard mode
    kill. See the module docstring."""
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
    return _register(LootDecl(
        lootid=lootid, group=group, items=tuple(items), tier=tier, picks=picks, reference=reference,
        loot_mode=loot_mode,
    ))


def remove_loot_group(lootid: int, *, group: int, why: str) -> LootDecl:
    """Deletes group `group` of `lootid` and inserts nothing (a stock list whose items moved to another boss's
    list). Every live row of the group must be an item some `item()` declares; `why` is printed with the removal."""
    where = f"remove_loot_group({lootid!r}, group={group!r})"
    _check_target(where, lootid, group)
    if not isinstance(why, str) or not why.strip():
        raise LootDeclarationError(f"{where}: why= (where the group's items went) is required")
    return _register(LootDecl(lootid=lootid, group=group, removal=True, why=why.strip()))
