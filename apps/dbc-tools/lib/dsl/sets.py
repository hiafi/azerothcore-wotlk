"""
Dungeon set declarations (item variants, Haunted set track, 2026-11-06): item sets with their set bonuses, the per-slot
tokens a set family drops, and the vendors that trade a token for a set piece. `lib/item_sets.py` resolves them
against the item declarations (`lib/dsl/items.py`) and emits the rows.

    from lib.dsl.sets import item_set, set_token, set_vendor

    item_set(181, items=("haunted_magisters_crown", ...), bonuses=((3, wraith_volley), (5, soul_rend)))
    item_set(1000, name="Protector's Armor", items=(...), bonuses=(...))          # a new set, from ids.yaml item_set
    set_token("haunted_helmet", name="Haunted Helmet", slots=(1,), ladder=VANILLA_DUNGEON, like=22353,
              ilvl=60, quality=Quality.RARE, required_level=0,
              entries={"normal": 70500, "heroic": 70501, ...}, costs={"normal": 3000, "heroic": 3001, ...})
    set_vendor(300480, sets=(181, 182), tokens=("haunted_helmet", ...))

**Item sets** (`ItemSet.dbc`, server overlay `itemset_dbc`). A set is its pieces (`item()` keys) and its bonuses,
`(pieces worn, spell)` pairs. The server counts worn pieces by `item_template.itemset` (`AddItemsSetItem`,
Item.cpp), so every tier of a piece counts toward the same set: the pieces' `itemset` column (the stock row's for a
`base=` piece, `itemset=` for a new one) must name the set on every tier, which lib/item_sets.py checks. A stock set
id (181) keeps its stock name and item list unless `name=` is given; its stock bonuses are replaced by `bonuses=`. A
new set id comes from source/ids.yaml's `item_set` block and needs `name=`. The row's item list (what the client's
set tooltip lists) is each piece's first tier (the Normal entry), in declaration order.

**Tokens.** One token per slot per family, a plain non-equippable item (class 15, the stock tier token's row copied
from `like=`), minted on every non-deferred tier of `ladder` with the tier's level and quality (the first tier takes
`ilvl=` / `quality=` / `required_level=`), the Heroic flag on a `heroic_flag` tier and the tier label on the others,
like an `item()` tier. `entries=` gives each tier's `item_template` entry (source/ids.yaml `item_set_token` block) and
`costs=` its `ItemExtendedCost` id (`item_extended_cost` block): one token of that tier is the price of any piece of
the token's slots at the same tier. Ids are explicit (a shipped id never moves; a removed token is retired by hand).
`slots=` are the `InventoryType`s the token buys (chest takes 5 and 20, robe).

**Vendors.** `set_vendor(entry, sets=, tokens=, tiers=)` puts the `tiers` (ladder tier names; None: every tier) of
every piece of `sets` on the vendor's list (`npc_vendor`), priced by the token of the piece's slot at the piece's tier
(`ExtendedCost`), ordered tier by tier, then by slot, then by set. The vendor creature itself is a
`creature_template()` declaration (npcflag 128). A list holds at most 150 items the client is sent
(`MAX_VENDOR_ITEMS`) and 255 rows the server keeps (`VendorItemData::GetItemCount` is a uint8): checked.

Registered into `Registry.item_set_declarations` (`id` = ("set", id) / ("token", key) / ("vendor", entry)), so a
duplicate is a `DuplicateIdError` like any other declared table.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from . import registry as _registry
from .items import LABEL_FORBIDDEN, Ladder, Quality

MAX_SET_ITEMS_SERVER = 10  # MAX_ITEM_SET_ITEMS, DBCStructure.h (the client file holds 17)
MAX_SET_ITEMS_CLIENT = 17
MAX_SET_SPELLS = 8  # MAX_ITEM_SET_SPELLS
MAX_SET_PIECES_WORN = 19  # EQUIPMENT_SLOT_END: a threshold above it can never be reached
TOKEN_ITEM_CLASS = 15  # ITEM_CLASS_MISCELLANEOUS
# InventoryType values a set piece can have (ItemTemplate.h InventoryType): the armor slots.
ARMOR_SLOTS = {1: "head", 3: "shoulders", 5: "chest", 20: "chest (robe)", 6: "waist", 7: "legs", 8: "feet",
               9: "wrist", 10: "hands"}
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
# Columns a token takes from the declaration or the tier, never from `columns=`.
_TOKEN_OWNED = frozenset({"entry", "name", "ItemLevel", "Quality", "RequiredLevel", "description"})


class SetDeclarationError(ValueError):
    pass


def _plain_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _spell_id(where: str, spell) -> int:
    spell_id = getattr(spell, "id", spell)
    if not _plain_int(spell_id) or spell_id <= 0:
        raise SetDeclarationError(f"{where}: {spell!r} is not a spell id or a declared spell")
    return spell_id


def _register(kind: str, ident, decl):
    active = _registry._active
    if active is not None:
        key = (kind, ident)
        if any(entry["id"] == key for entry in active.item_set_declarations):
            raise _registry.DuplicateIdError(f"{decl.where}: declared twice")
        active.item_set_declarations.append({"id": key, "_decl": decl})
    return decl


# ---------------------------------------------------------------------------------------------------------------------
# Item sets


@dataclass(frozen=True)
class ItemSetDecl:
    set_id: int
    items: tuple[str, ...]
    bonuses: tuple[tuple[int, int], ...]  # (pieces worn, spell id)
    name: str | None = None

    @property
    def where(self) -> str:
        return f"item_set({self.set_id})"


def item_set(set_id: int, *, items, bonuses, name: str | None = None) -> ItemSetDecl:
    """An item set: its pieces (`item()` keys), its bonuses (`(pieces worn, spell)` pairs) and, for a new set, its
    name. See the module docstring."""
    where = f"item_set({set_id!r})"
    if not _plain_int(set_id) or set_id <= 0:
        raise SetDeclarationError(f"{where}: the set id must be a positive int (an ItemSet.dbc id)")
    if isinstance(items, str) or not isinstance(items, (tuple, list)) or not items:
        raise SetDeclarationError(f"{where}: items must be a non-empty tuple of item() keys")
    if not all(isinstance(k, str) and _KEY_RE.match(k) for k in items):
        raise SetDeclarationError(f"{where}: every item must be an item() key")
    if len(set(items)) != len(items):
        raise SetDeclarationError(f"{where}: an item is listed twice")
    if len(items) > MAX_SET_ITEMS_CLIENT:
        raise SetDeclarationError(f"{where}: {len(items)} pieces, the ItemSet.dbc row holds {MAX_SET_ITEMS_CLIENT}")
    if isinstance(bonuses, (str, bytes)) or not isinstance(bonuses, (tuple, list)) or not bonuses:
        raise SetDeclarationError(f"{where}: bonuses must be a non-empty tuple of (pieces worn, spell) pairs")
    if len(bonuses) > MAX_SET_SPELLS:
        raise SetDeclarationError(f"{where}: at most {MAX_SET_SPELLS} bonuses (MAX_ITEM_SET_SPELLS)")
    pairs = []
    for bonus in bonuses:
        if not isinstance(bonus, (tuple, list)) or len(bonus) != 2:
            raise SetDeclarationError(f"{where}: bonus {bonus!r} must be a (pieces worn, spell) pair")
        threshold, spell = bonus
        if not _plain_int(threshold) or not 1 <= threshold <= min(len(items), MAX_SET_PIECES_WORN):
            raise SetDeclarationError(
                f"{where}: bonus threshold {threshold!r} must be an int from 1 to the set's size ({len(items)})"
            )
        pairs.append((threshold, _spell_id(where, spell)))
    if len({spell for _, spell in pairs}) != len(pairs):
        raise SetDeclarationError(f"{where}: a bonus spell is listed twice")
    if name is not None and (not isinstance(name, str) or not name.strip() or any(c in name for c in "\n\r|")):
        raise SetDeclarationError(f"{where}: name={name!r} must be a one-line, non-empty string")
    return _register("set", set_id, ItemSetDecl(set_id=set_id, items=tuple(items), bonuses=tuple(pairs), name=name))


# ---------------------------------------------------------------------------------------------------------------------
# Tokens


@dataclass(frozen=True)
class SetTokenDecl:
    key: str
    name: str
    slots: tuple[int, ...]
    ladder: Ladder
    like: int
    entries: tuple[tuple[str, int], ...]  # (tier name, item_template entry), ladder order
    costs: tuple[tuple[str, int], ...]  # (tier name, ItemExtendedCost id), ladder order
    ilvl: int | None = None
    quality: int | None = None
    required_level: int | None = None
    description: str = ""
    columns: tuple[tuple[str, object], ...] = ()

    @property
    def where(self) -> str:
        return f"set_token({self.key!r})"

    def entry(self, tier: str) -> int | None:
        return dict(self.entries).get(tier)

    def cost(self, tier: str) -> int | None:
        return dict(self.costs).get(tier)


def set_token(
    key: str, *, name: str, slots, ladder: Ladder, like: int, entries: dict, costs: dict, ilvl: int | None = None,
    quality: int | None = None, required_level: int | None = None, description: str = "", **columns,
) -> SetTokenDecl:
    """A set family's token for one slot, minted on every non-deferred tier of `ladder` (see the module docstring).
    `columns` are other `item_template` columns for every tier (e.g. `stackable=`)."""
    where = f"set_token({key!r})"
    if not isinstance(key, str) or not _KEY_RE.match(key):
        raise SetDeclarationError(f"{where}: the key must match {_KEY_RE.pattern}")
    if not isinstance(name, str) or not name.strip():
        raise SetDeclarationError(f"{where}: name= is required")
    if not isinstance(ladder, Ladder):
        raise SetDeclarationError(f"{where}: ladder= must be a ladder(...)")
    slots = tuple(slots) if isinstance(slots, (tuple, list)) else (slots,)
    if not slots or any(s not in ARMOR_SLOTS for s in slots) or len(set(slots)) != len(slots):
        raise SetDeclarationError(f"{where}: slots={slots!r} must be distinct armor InventoryTypes "
                                  f"({sorted(ARMOR_SLOTS)})")
    if not _plain_int(like) or like <= 0:
        raise SetDeclarationError(f"{where}: like= must be a stock item_template entry (a stock token)")
    first = ladder.tiers[0]
    if first.explicit:
        if any(v is not None for v in (ilvl, quality, required_level)):
            raise SetDeclarationError(f"{where}: ladder {ladder.name!r} sets every tier's level")
    elif not (_plain_int(ilvl) and 1 <= ilvl <= 300 and _plain_int(quality) and quality in tuple(Quality)
              and _plain_int(required_level) and 0 <= required_level <= 80):
        raise SetDeclarationError(f"{where}: the first tier takes ilvl=, quality= and required_level=")
    tiers = [t.name for t in ladder.tiers if not t.deferred]
    ordered = []
    for label, mapping in (("entries", entries), ("costs", costs)):
        if not isinstance(mapping, dict) or set(mapping) != set(tiers):
            raise SetDeclarationError(f"{where}: {label}= must name exactly the ladder's tiers {tiers}")
        if not all(_plain_int(v) and v > 0 for v in mapping.values()) or len(set(mapping.values())) != len(mapping):
            raise SetDeclarationError(f"{where}: {label}= values must be distinct positive ints")
        ordered.append(tuple((t, mapping[t]) for t in tiers))
    if not isinstance(description, str) or any(c in description for c in LABEL_FORBIDDEN[:2]):
        raise SetDeclarationError(f"{where}: description= must be a string without quotes or backslashes")
    owned = sorted(c for c in columns if c in _TOKEN_OWNED)
    if owned:
        raise SetDeclarationError(f"{where}: {', '.join(owned)} come from the declaration or the tier")
    decl = SetTokenDecl(
        key=key, name=name, slots=slots, ladder=ladder, like=like, entries=ordered[0], costs=ordered[1],
        ilvl=ilvl, quality=None if quality is None else int(quality), required_level=required_level,
        description=description, columns=tuple(sorted(columns.items())),
    )
    return _register("token", key, decl)


# ---------------------------------------------------------------------------------------------------------------------
# Vendors


@dataclass(frozen=True)
class SetVendorDecl:
    entry: int
    sets: tuple[int, ...]
    tokens: tuple[str, ...]
    tiers: tuple[str, ...] | None = None  # ladder tier names this vendor sells; None: every tier

    @property
    def where(self) -> str:
        return f"set_vendor({self.entry})"


def set_vendor(entry: int, *, sets, tokens, tiers=None) -> SetVendorDecl:
    """Vendor `entry` trades `tokens` for the `tiers` (every tier when None) of every piece of `sets` (see the module
    docstring)."""
    where = f"set_vendor({entry!r})"
    if not _plain_int(entry) or entry <= 0:
        raise SetDeclarationError(f"{where}: entry must be a creature_template entry")
    sets = tuple(sets) if isinstance(sets, (tuple, list)) else ()
    if not sets or not all(_plain_int(s) and s > 0 for s in sets) or len(set(sets)) != len(sets):
        raise SetDeclarationError(f"{where}: sets= must be a non-empty tuple of distinct item_set() ids")
    tokens = tuple(tokens) if isinstance(tokens, (tuple, list)) else ()
    if not tokens or not all(isinstance(t, str) and _KEY_RE.match(t) for t in tokens) or len(set(tokens)) != len(
            tokens):
        raise SetDeclarationError(f"{where}: tokens= must be a non-empty tuple of distinct set_token() keys")
    if tiers is not None:
        tiers = tuple(tiers) if isinstance(tiers, (tuple, list)) else ()
        if not tiers or not all(isinstance(t, str) and _KEY_RE.match(t) for t in tiers) or len(set(tiers)) != len(
                tiers):
            raise SetDeclarationError(f"{where}: tiers= must be None or a non-empty tuple of distinct tier names")
    return _register("vendor", entry, SetVendorDecl(entry=entry, sets=sets, tokens=tokens, tiers=tiers))
