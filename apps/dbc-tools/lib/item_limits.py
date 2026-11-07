"""
Unique-equipped across tiers (item variants IV10 follow-up 1, user ruling 2026-11-06): every tier of an item that
carries an effect spell shares one `ItemLimitCategory` with an equip limit of 1, so a player cannot wear two tiers of
the same effect at once (two independent keg cooldowns, two Signet procs). Plain stat items stay unrestricted.

**Which items.** `item(..., unique_equip=None)` (the default) means: unique when the item has an effect, i.e.
`spells=` names at least one spell (Use, Equip or Chance on hit, scaled or not), or `keep_spells=True` keeps a stock
row that has one. `unique_equip=True` / `False` overrides it. `ItemLimitCategory` cannot be passed as a column.

**The stock mechanism.** `item_template.ItemLimitCategory` names an `ItemLimitCategory.dbc` row (`Quantity`,
`Flags` 1 = equip mode, `ITEM_LIMIT_CATEGORY_MODE_EQUIP`). The server reads the row from its DBC plus the
`itemlimitcategory_dbc` overlay (DBCStores.cpp) and refuses a second equip (`Player::CanEquipUniqueItem`); ObjectMgr
zeroes an item's category it cannot find, so the row must be live before the item rows. The client prints
"Unique-Equipped: <name> (1)" from its own ItemLimitCategory.dbc by the id the item query carries, so the row also
goes into patch-Z. One row per item: `Name_Lang_enUS` = the item's name (its first tier's: the `name=` of a new item,
the stock row's of a `base=` one), the other locales empty, `Name_Lang_Mask` the stock value, `Quantity` 1, `Flags` 1.

**Ids: a lock, not a derivation.** `source/items/item_limit_ids.lock`, one `<category id> <item key>` line per item,
append-only like `item_ids.lock`, minted from source/ids.yaml's `item_limit_category` block (1000-1999; stock ids end
at 85, the column is a signed smallint) after the highest id in the file, skipping every live `itemlimitcategory_dbc`
id. A derivation was rejected: from an entry it fails for `base=` stock items (their first entry is a stock id, far
outside any small block) and changes if a ladder's first tier changes; from a hash of the key it can collide. The lock
keeps a key's id forever and is the same on every machine; `--check` lists the lines a full run would append and
never writes.

**Retire.** A line whose item no longer wants a category (dropped, or `unique_equip=False`) stops the run unless it is
marked `<id> <key> retired <date> [<name>]`. A retired line keeps emitting its row (players can hold items that name
it; `item_template` rows are never deleted), with the name on the line (else the key). An item still declared but no
longer unique gets `ItemLimitCategory` 0 written on every tier (the stock entry of a `base=` item too).
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import dbcfmt

TOOL_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = TOOL_ROOT / "source" / "items" / "item_limit_ids.lock"
LOCK_BLOCK = "item_limit_category"
NAME_LANG_MASK = 16712190  # every stock ItemLimitCategory.dbc row's
QUANTITY = 1
FLAGS_EQUIP = 1  # ITEM_LIMIT_CATEGORY_MODE_EQUIP (DBCEnums.h)
COLUMN = "ItemLimitCategory"
SPELL_SLOTS = 5
LOCK_HEADER = (
    "# Item limit categories (item variants IV10 follow-up 1; lib/item_limits.py): one line per item whose tiers\n"
    "# share a unique-equip limit of 1, `<category id> <item key> [retired <date> [<name>]]`, minted from\n"
    "# source/ids.yaml's item_limit_category block. Append-only: a full generate.py run appends new lines; never\n"
    "# reorder, renumber or delete one. A merge conflict: keep the merged side's lines, drop the other side's new\n"
    "# lines and delete its not-yet-imported rev_*.sql, then re-run generate.py (same recovery as item_ids.lock).\n"
)
_KEY = r"[a-z][a-z0-9_]*"
_LINE_RE = re.compile(rf"^(\d+) ({_KEY})(?: retired (\d{{4}}-\d{{2}}-\d{{2}})(?: (.+))?)?$")


class LockError(ValueError):
    pass


@dataclass(frozen=True)
class LockLine:
    category: int
    key: str
    retired: str | None = None
    name: str | None = None
    number: int = 0


@dataclass
class Lock:
    lines: list[LockLine] = field(default_factory=list)
    text: str = ""

    @property
    def by_key(self) -> dict[str, LockLine]:
        return {line.key: line for line in self.lines}


def parse_lock(text: str, block: dict | None = None) -> Lock:
    lock = Lock(text=text)
    ids: dict[int, int] = {}
    keys: dict[str, int] = {}
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        where = f"{LOCK_PATH.name} line {number}"
        m = _LINE_RE.match(line)
        if not m:
            raise LockError(f"{where}: expected `<category id> <item key> [retired <date> [<name>]]`, got {raw!r}")
        entry = LockLine(int(m.group(1)), m.group(2), m.group(3), m.group(4), number)
        if entry.category in ids:
            raise LockError(f"{where}: category {entry.category} is already on line {ids[entry.category]}")
        if entry.key in keys:
            raise LockError(f"{where}: item {entry.key} is already on line {keys[entry.key]}")
        if block and not block["start"] <= entry.category <= block["end"]:
            raise LockError(f"{where}: {entry.category} is outside source/ids.yaml's {LOCK_BLOCK} block "
                            f"({block['start']}-{block['end']})")
        ids[entry.category] = number
        keys[entry.key] = number
        lock.lines.append(entry)
    return lock


def load_lock(path: Path = LOCK_PATH, block: dict | None = None) -> Lock:
    return parse_lock(path.read_text(encoding="utf-8") if path.is_file() else "", block)


def lock_text(lock: Lock, appended: list[str]) -> str:
    text = lock.text or LOCK_HEADER
    if appended:
        if not text.endswith("\n"):
            text += "\n"
        text += "".join(f"{line}\n" for line in appended)
    return text


def _int(value) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def has_effect(item) -> bool:
    """`item` (a `ResolvedItem`) carries a Use / Equip / Chance on hit spell on its tiers."""
    decl = item.decl
    if decl.spells is not None:
        return bool(decl.spells)
    if decl.keep_spells:
        return any(_int(item.source_row.get(f"spellid_{n}")) for n in range(1, SPELL_SLOTS + 1))
    return False


def wants_limit(item) -> bool:
    return item.decl.unique_equip if item.decl.unique_equip is not None else has_effect(item)


def category_row(category: int, name: str) -> dict:
    row = {c: "" for c in dbcfmt.ITEMLIMITCATEGORY.columns if c.startswith("Name_Lang_")}
    row.update(id=category, ID=category, Name_Lang_enUS=name, Name_Lang_Mask=NAME_LANG_MASK, Quantity=QUANTITY,
               Flags=FLAGS_EQUIP)
    return row


def client_rows(declared: list[dict]) -> dict[int, dict]:
    """Declared `item_limit_categories` rows as ItemLimitCategory.dbc rows, keyed by ID, for the patch-Z merge."""
    return {int(r["ID"]): {c: r[c] for c in dbcfmt.ITEMLIMITCATEGORY.columns} for r in declared}


def base_file_error(rows: list[dict], base_dir: Path) -> str | None:
    """Declared categories need the stock ItemLimitCategory.dbc as the patch's base layer (else the client has no
    tooltip line for them). None when fine."""
    path = base_dir / dbcfmt.ITEMLIMITCATEGORY.dbc_filename
    if rows and not path.is_file():
        return (
            f"items: {len(rows)} item limit categor(ies) declared but no stock {dbcfmt.ITEMLIMITCATEGORY.dbc_filename} "
            f"at {path} - copy it from the worldserver's DBC directory "
            f"(docker cp ac-worldserver:/azerothcore/env/dist/data/dbc/{dbcfmt.ITEMLIMITCATEGORY.dbc_filename} {path})"
        )
    return None


@dataclass
class LimitExpansion:
    categories: dict[str, int] = field(default_factory=dict)  # item key -> category id (wanted items)
    rows: list[dict] = field(default_factory=list)  # itemlimitcategory_dbc rows (wanted and retired)
    lock_appended: list[str] = field(default_factory=list)
    lock_text: str = ""
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _item_name(item) -> str:
    name = item.decl.name if item.decl.name is not None else item.source_row.get("name")
    return str(name or item.decl.key)


def expand(item_expansion, ids_cfg: dict, *, lock: Lock | None = None, lock_path: Path | None = None,
           taken_loader=None, today: str | None = None) -> LimitExpansion:
    """The category of every item that wants one, its row, and the tiers' `ItemLimitCategory` column (set on
    `ResolvedTier.columns`, so lib/item_emit.py writes it: a minted row whole, a stock entry as an owned column).
    Never raises for a content problem."""
    out = LimitExpansion()
    block = ids_cfg.get(LOCK_BLOCK)
    try:
        lock = load_lock(lock_path or LOCK_PATH, block) if lock is None else parse_lock(lock.text, block)
    except LockError as error:
        out.errors.append(f"items: {error}")
        return out
    out.lock_text = lock.text
    wanted = [item for item in item_expansion.items if wants_limit(item)]
    if not wanted and not lock.lines:
        return out
    if block is None:
        out.errors.append(f"items: source/ids.yaml has no {LOCK_BLOCK} block - item limit categories come from it")
        return out
    by_key = lock.by_key
    in_lock = {line.category for line in lock.lines}
    next_id = max([block["start"] - 1, *in_lock]) + 1
    taken: set[int] | None = None
    full = False
    for item in wanted:
        key = item.decl.key
        line = by_key.get(key)
        if line is not None:
            if line.retired:
                out.errors.append(f"item {key!r}: its limit category {line.category} was retired on {line.retired} "
                                  f"({LOCK_PATH.name} line {line.number}); a retired id is never reused - give the "
                                  f"item a new key, or keep unique_equip=False")
                continue
            out.categories[key] = line.category
            continue
        if taken is None:
            taken = in_lock | {int(i) for i in (taken_loader() if taken_loader else ())}
        while next_id in taken or next_id in out.categories.values():
            next_id += 1
        if next_id > block["end"]:
            if not full:
                out.errors.append(f"items: source/ids.yaml's {LOCK_BLOCK} block ({block['start']}-{block['end']}) "
                                  f"is full; widen it")
                full = True
            continue
        out.categories[key] = next_id
        out.lock_appended.append(f"{next_id} {key}")
        next_id += 1
    wanted_keys = {item.decl.key for item in wanted}
    declared_keys = {item.decl.key for item in item_expansion.items}
    stamp = today or datetime.date.today().isoformat()
    for line in lock.lines:
        if line.key in wanted_keys or line.retired:
            continue
        where = "is no longer unique-equipped" if line.key in declared_keys else "is no longer declared"
        out.errors.append(
            f"items: {line.key} ({LOCK_PATH.name} line {line.number}, limit category {line.category}) {where}; "
            f"a category id is never reused and owned items may name it. Make it unique again, or retire the line: "
            f"`{line.category} {line.key} retired {stamp} <item name>`"
        )
    if out.errors:
        return out

    for item in item_expansion.items:
        key = item.decl.key
        if key in out.categories:
            value = out.categories[key]
            out.rows.append(category_row(value, _item_name(item)))
        elif key in by_key:  # retired, still declared: the tiers no longer name it
            value = 0
        else:
            continue
        stock = _int(item.source_row.get(COLUMN)) if item.decl.base is not None else 0
        if stock and stock != value:
            out.notes.append(f"item {key!r}: the stock row's ItemLimitCategory {stock} is replaced by {value}")
        for tier in item.tiers:
            tier.columns[COLUMN] = value
    for line in lock.lines:
        if line.retired:
            out.rows.append(category_row(line.category, line.name or line.key))
    out.rows.sort(key=lambda r: r["ID"])
    out.lock_text = lock_text(lock, out.lock_appended)
    if out.categories:
        out.notes.append(f"items: {len(out.categories)} unique-equipped item(s) (one limit category each, all tiers)")
    return out


def summary_notes(expansion: LimitExpansion, check: bool) -> list[str]:
    notes = list(expansion.notes)
    if check:
        notes += [f"items: would append to {LOCK_PATH.name}: {line}" for line in expansion.lock_appended]
    elif expansion.lock_appended:
        notes.append(f"items: {len(expansion.lock_appended)} new item limit categor(ies) for {LOCK_PATH.name} (a full "
                     f"run appends them; commit the file)")
    return notes
