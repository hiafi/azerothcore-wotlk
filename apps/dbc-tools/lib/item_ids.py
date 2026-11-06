"""
The item id lock (item-variants plan v2 s4, stage IV1): `source/items/item_ids.lock`, the committed record of which
`item_template` entry each (item key, ladder tier) owns. Follows `source/world/heroic_ids.lock`
(`lib/heroic_templates.py`): plain text, append-only, ids assigned deterministically so `--check` reports the ids a
full run writes, and the only source file a full `generate.py` run writes (after the SQL, only when a line is new).

Lines (`#` comments and blank lines are skipped):

    <entry> <key> <tier>                    a minted entry, from source/ids.yaml's item_minted block
    <entry> <key> <tier> base               a stock item taken over by item(base=<entry>) as its first tier
    <entry> <key> <tier> retired <date> <class> <subclass> <sound> <material> <display> <invtype> <sheath>
    <entry> <key> <tier> base retired <date>

**Mint.** A (key, tier) without a line takes the next id after the highest minted id in the file (gaps are never
reused), skipping every id another owner holds (live `item_template` / `item_dbc` rows, `items.csv`). A (key, tier)
keeps its id forever, whatever its name, level or shapes later become.

**Retire.** An id is never reused: players can hold the item, and `item_template` is never deleted. A minted line
whose (key, tier) is no longer declared (the item, the tier, or a tier now `deferred=True`) stops the run unless the
line is marked `retired <date>` with the 7 Item.dbc fields of its row, so IV2 keeps emitting its `item_dbc` row (the
block DELETE would otherwise blank-icon an item players own). A `base` line whose declaration is gone is only reported
(the stock rows stay as last written); `base retired <date>` silences that. A retired (key, tier) cannot be declared
again: give the item a new key or the tier a new name.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = TOOL_ROOT / "source" / "items" / "item_ids.lock"
LOCK_BLOCK = "item_minted"
# Written only when the file does not exist yet (IV0 commits the real header).
LOCK_HEADER = (
    "# Item variant ids (item-variants plan s4; lib/item_ids.py): one line per (item key, ladder tier),\n"
    "# `<entry> <key> <tier> [base | retired <date> <class> <subclass> <sound> <material> <display> <invtype>\n"
    "# <sheath>]`, minted from source/ids.yaml's item_minted block. Append-only: a full generate.py run appends new\n"
    "# lines; never reorder, renumber or delete one (an id must never move or be reused).\n"
)
# The Item.dbc fields a retired line carries, in line order, as item_template columns.
RETIRED_DBC_COLUMNS = ("class", "subclass", "SoundOverrideSubclass", "Material", "displayid", "InventoryType", "sheath")

_KEY = r"[a-z][a-z0-9_]*"
_LINE_RE = re.compile(rf"^(\d+) ({_KEY}) ({_KEY})(?: (.*))?$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_INT_RE = re.compile(r"^-?\d+$")


class LockError(ValueError):
    pass


@dataclass(frozen=True)
class LockLine:
    entry: int
    key: str
    tier: str
    base: bool = False
    retired: str | None = None  # the date
    dbc_fields: tuple[int, ...] | None = None  # RETIRED_DBC_COLUMNS values of a retired minted line
    number: int = 0

    @property
    def pair(self) -> tuple[str, str]:
        return self.key, self.tier

    def dbc_row(self) -> dict | None:
        """The retired line's Item.dbc fields as item_template column values."""
        return None if self.dbc_fields is None else dict(zip(RETIRED_DBC_COLUMNS, self.dbc_fields))


@dataclass
class Lock:
    lines: list[LockLine] = field(default_factory=list)
    text: str = ""

    @property
    def by_pair(self) -> dict[tuple[str, str], LockLine]:
        return {line.pair: line for line in self.lines}

    @property
    def by_entry(self) -> dict[int, LockLine]:
        return {line.entry: line for line in self.lines}

    def minted_entries(self) -> set[int]:
        return {line.entry for line in self.lines if not line.base}


def parse_lock(text: str, block: dict | None = None) -> Lock:
    """Reads the lock; raises LockError on a malformed line, a repeated entry or (key, tier), a minted id outside
    `block` (`{start, end}`) or a `base` entry inside it."""
    lock = Lock(text=text)
    entries: dict[int, int] = {}
    pairs: dict[tuple[str, str], int] = {}
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        where = f"{LOCK_PATH.name} line {number}"
        m = _LINE_RE.match(line)
        if not m:
            raise LockError(f"{where}: expected `<entry> <key> <tier> [base | retired ...]`, got {raw!r}")
        entry, key, tier, rest = int(m.group(1)), m.group(2), m.group(3), (m.group(4) or "").split()
        base = False
        retired = None
        dbc_fields = None
        if rest[:1] == ["base"]:
            base = True
            rest = rest[1:]
        if rest:
            if rest[0] != "retired" or len(rest) < 2 or not _DATE_RE.match(rest[1]):
                raise LockError(f"{where}: after the tier only `base` and/or `retired <YYYY-MM-DD> ...` may follow")
            retired = rest[1]
            fields = rest[2:]
            if base:
                if fields:
                    raise LockError(f"{where}: a retired base line carries no Item.dbc fields (the stock row has them)")
            else:
                if len(fields) != len(RETIRED_DBC_COLUMNS) or not all(_INT_RE.match(f) for f in fields):
                    raise LockError(
                        f"{where}: a retired minted line carries its row's {len(RETIRED_DBC_COLUMNS)} Item.dbc fields "
                        f"as integers ({' '.join(RETIRED_DBC_COLUMNS)})"
                    )
                dbc_fields = tuple(int(f) for f in fields)
        if entry in entries:
            raise LockError(f"{where}: entry {entry} is already on line {entries[entry]}")
        if (key, tier) in pairs:
            raise LockError(f"{where}: {key} {tier} is already on line {pairs[(key, tier)]}")
        if block:
            inside = block["start"] <= entry <= block["end"]
            if base and inside:
                raise LockError(f"{where}: base entry {entry} is inside the {LOCK_BLOCK} block (a base is stock)")
            if not base and not inside:
                raise LockError(
                    f"{where}: {entry} is outside source/ids.yaml's {LOCK_BLOCK} block "
                    f"({block['start']}-{block['end']})"
                )
        entries[entry] = number
        pairs[(key, tier)] = number
        lock.lines.append(LockLine(entry, key, tier, base, retired, dbc_fields, number))
    return lock


def load_lock(path: Path = LOCK_PATH, block: dict | None = None) -> Lock:
    return parse_lock(path.read_text(encoding="utf-8") if path.is_file() else "", block)


@dataclass(frozen=True)
class Wanted:
    """One declared, non-deferred tier: `base` is the stock entry when the tier is a `base=` item's first tier."""

    key: str
    tier: str
    base: int | None = None


@dataclass
class Assignment:
    entries: dict[tuple[str, str], int] = field(default_factory=dict)  # (key, tier) -> entry, every wanted pair
    appended: list[str] = field(default_factory=list)  # new lock lines, in order
    minted: list[tuple[int, str, str]] = field(default_factory=list)  # new minted (entry, key, tier)
    bases: list[tuple[int, str, str]] = field(default_factory=list)  # new base (entry, key, tier)
    retired: list[LockLine] = field(default_factory=list)  # retired minted lines (IV2 keeps their item_dbc rows)
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def retire_suggestion(line: LockLine, live_row: dict | None, today: str | None = None) -> str:
    """The line to write instead of `line` to retire it."""
    today = today or datetime.date.today().isoformat()
    if line.base:
        return f"{line.entry} {line.key} {line.tier} base retired {today}"
    if live_row is None:
        fields = " ".join(f"<{c}>" for c in RETIRED_DBC_COLUMNS)
    else:
        fields = " ".join(str(int(float(live_row.get(c) or 0))) for c in RETIRED_DBC_COLUMNS)
    return f"{line.entry} {line.key} {line.tier} retired {today} {fields}"


def assign(
    lock: Lock, wanted: list[Wanted], block: dict, taken: set[int] = frozenset(),
    live_rows: dict[int, dict] | None = None, today: str | None = None,
) -> Assignment:
    """Entries for `wanted` (in order): the lock's, else a `base` line for a stock first tier, else the next free id
    of `block` after the highest minted id in the lock, skipping `taken` (ids other owners hold). Then the retire guard
    over every lock line no wanted pair claims. Never raises for a content problem: they come back as `errors`."""
    out = Assignment()
    live_rows = live_rows or {}
    by_pair = lock.by_pair
    by_entry = lock.by_entry
    in_block = [line.entry for line in lock.lines if not line.base and block["start"] <= line.entry <= block["end"]]
    next_id = max([block["start"] - 1, *in_block]) + 1
    claimed: dict[int, tuple[str, str]] = {}
    full = False
    for want in wanted:
        pair = (want.key, want.tier)
        label = f"item {want.key!r} tier {want.tier!r}"
        line = by_pair.get(pair)
        if line is not None:
            if line.retired:
                out.errors.append(
                    f"{label}: its id {line.entry} was retired on {line.retired} ({LOCK_PATH.name} line "
                    f"{line.number}); a retired id is never reused - give the item a new key or the tier a new name"
                )
                continue
            if want.base is not None and not line.base:
                out.errors.append(
                    f"{label}: {LOCK_PATH.name} line {line.number} gives it minted entry {line.entry}, but it is now "
                    f"base={want.base}; a minted id cannot become a stock item (retire the line and use a new key)"
                )
                continue
            if want.base is None and line.base:
                out.errors.append(
                    f"{label}: {LOCK_PATH.name} line {line.number} records it as stock entry {line.entry} (base=); "
                    f"put base={line.entry} back, or retire the line and use a new key"
                )
                continue
            if want.base is not None and want.base != line.entry:
                out.errors.append(
                    f"{label}: {LOCK_PATH.name} line {line.number} records base={line.entry}, not base={want.base}; "
                    f"retire the line and use a new key to take over another stock item"
                )
                continue
            out.entries[pair] = line.entry
            claimed[line.entry] = pair
            continue
        if want.base is not None:
            owner = by_entry.get(want.base)
            if owner is not None or want.base in claimed:
                other = owner.pair if owner is not None else claimed[want.base]
                out.errors.append(
                    f"{label}: stock entry {want.base} already belongs to item {other[0]!r} tier {other[1]!r} "
                    f"(one owner per entry)"
                )
                continue
            out.entries[pair] = want.base
            claimed[want.base] = pair
            out.bases.append((want.base, want.key, want.tier))
            out.appended.append(f"{want.base} {want.key} {want.tier} base")
            continue
        while next_id in taken or next_id in by_entry or next_id in claimed:
            next_id += 1
        if next_id > block["end"]:
            if not full:
                out.errors.append(
                    f"source/ids.yaml's {LOCK_BLOCK} block ({block['start']}-{block['end']}) is full; widen it"
                )
                full = True
            continue
        out.entries[pair] = next_id
        claimed[next_id] = pair
        out.minted.append((next_id, want.key, want.tier))
        out.appended.append(f"{next_id} {want.key} {want.tier}")
        next_id += 1
    wanted_pairs = {(w.key, w.tier) for w in wanted}
    for line in lock.lines:
        if line.pair in wanted_pairs:
            continue
        if line.retired:
            if not line.base:
                out.retired.append(line)
            continue
        suggestion = retire_suggestion(line, live_rows.get(line.entry), today)
        if line.base:
            out.notes.append(
                f"items: stock entry {line.entry} ({line.key} {line.tier}) is no longer declared; its item_template "
                f"and item_itemization rows stay as last written (restore them by hand if needed). To silence this, "
                f"mark the line `{suggestion}`"
            )
        else:
            out.errors.append(
                f"items: {line.key} {line.tier} (entry {line.entry}, {LOCK_PATH.name} line {line.number}) is no "
                f"longer declared; an item id is never reused and players may hold it. Declare it again, or retire "
                f"it by replacing the line with `{suggestion}`"
            )
    return out


def lock_text(lock: Lock, appended: list[str]) -> str:
    """The lock file with `appended` added at the end (the header on a new file); existing lines byte for byte."""
    text = lock.text or LOCK_HEADER
    if appended:
        if not text.endswith("\n"):
            text += "\n"
        text += "".join(f"{line}\n" for line in appended)
    return text


def unowned_block_entries(lock: Lock, live_entries, block: dict) -> list[int]:
    """Live `item_template` entries inside `block` that no lock line owns: someone else wrote into the minted block."""
    owned = {line.entry for line in lock.lines}
    return sorted(e for e in live_entries if block["start"] <= int(e) <= block["end"] and int(e) not in owned)
