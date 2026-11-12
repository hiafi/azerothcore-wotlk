"""
Spells that create a minted item (crafting rework C7): a recipe spell in `source/world/` names the item it creates by
its `item()` key, because the item's entry is only known once `lib/item_variants.py` has minted it (source/items is
expanded after source/world is loaded). The spell carries a placeholder string in a raw `EffectItemType_<n>` column:

    spell(id=207600, ..., effects=[Effect(type=24, implicit_target_a=1)],
          raw_overrides={"EffectItemType_1": item_key_refs.ref("crafted_t1_cloth_int_head")})

`resolve()` runs in generate.py right after the item expansion and swaps each placeholder for the (key, tier)'s
entry: from the run's assignment, else from the lock file (`source/items/item_ids.lock`; a scoped run loads no
source/items). A placeholder nothing resolves is an ERROR naming the spell, so a spell never reaches a DBC row or SQL
with a string in an integer column.
"""

from __future__ import annotations

from collections.abc import Mapping

from lib import item_ids

PREFIX = "item:"
ITEM_TYPE_COLUMNS = tuple(f"EffectItemType_{n}" for n in (1, 2, 3))


def ref(key: str, tier: str = "normal") -> str:
    """The placeholder for (item key, ladder tier)'s entry."""
    return f"{PREFIX}{key}:{tier}"


def is_ref(value) -> bool:
    return isinstance(value, str) and value.startswith(PREFIX)


def parse(value: str) -> tuple[str, str]:
    key, _, tier = value[len(PREFIX):].partition(":")
    return key, tier or "normal"


def resolve(spells: list[dict], entries: Mapping[tuple[str, str], int] | None,
            lock_loader=lambda: item_ids.load_lock()) -> list[str]:
    """Replaces every placeholder in `spells` (entries of `dsl_classes["spells"]`, edited in place). Returns the
    errors. `entries` is the run's (key, tier) -> entry assignment; the lock is read only for a pair it lacks."""
    errors: list[str] = []
    lock_entries: dict[tuple[str, str], int] | None = None
    for spell in spells:
        raw = spell.get("raw_overrides") or {}
        for column in ITEM_TYPE_COLUMNS:
            value = raw.get(column)
            if not is_ref(value):
                continue
            pair = parse(value)
            entry = (entries or {}).get(pair)
            if entry is None:
                if lock_entries is None:
                    lock_entries = {line.pair: line.entry for line in lock_loader().lines if not line.retired}
                entry = lock_entries.get(pair)
            if entry is None:
                errors.append(f"spell {spell.get('id')} ({spell.get('name')}): {column} names item {pair[0]!r} tier "
                              f"{pair[1]!r}, which no item() declares and the lock does not hold")
                continue
            raw[column] = entry
    return errors
