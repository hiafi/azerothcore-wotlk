"""
Read-only "what drops where": `instance_template` (map -> dungeon/raid),
`creature` (spawns) + `creature_template` (name/rank/lootid), and
`creature_loot_template` + `reference_loot_template` (lootid -> items),
joined against `item_template`'s already-overlay-aware rows from
`lib.overlay.get_rows()` so an edit made through this tool shows up here
immediately.

Base-dump only for the four tables above (no pending-SQL overlay replay
the way `lib/overlay.py` does for `item_template`) - this repo's history
hasn't added custom loot yet, and these tables are large enough
(`creature.sql` alone is ~150k rows) that extending the replay machinery
to them is deferred until it's actually needed; see the README's "Known
limitations". `item_template` itself is always current, since it's read
through `lib.overlay.get_rows()`, not read again here.
"""

from __future__ import annotations

import re
from pathlib import Path

from .overlay import REPO_ROOT, get_rows
from .sql_dump import parse_create_table_columns, read_table_dump, read_table_rows

BASE_DIR = REPO_ROOT / "data/sql/base/db_world"
INSTANCE_TEMPLATE = BASE_DIR / "instance_template.sql"
CREATURE = BASE_DIR / "creature.sql"
CREATURE_TEMPLATE = BASE_DIR / "creature_template.sql"
CREATURE_LOOT_TEMPLATE = BASE_DIR / "creature_loot_template.sql"
REFERENCE_LOOT_TEMPLATE = BASE_DIR / "reference_loot_template.sql"

# ItemModType (apps/item-tools' own reading of the enum this fork actually
# ships, not the stock one) - src/server/game/Entities/Item/ItemTemplate.h,
# "enum ItemModType". Re-check that file if this list looks stale; slots
# 22/23/24 are this fork's custom repurposing (see the enum's own comments
# there), not stock ITEM_MOD_HIT_TAKEN_*.
ITEM_MOD_NAMES = {
    0: "Mana", 1: "Health", 3: "Agility", 4: "Strength", 5: "Intellect",
    6: "Spirit", 7: "Stamina", 12: "Defense Rating", 13: "Dodge Rating",
    14: "Parry Rating", 15: "Block Rating", 16: "Melee Hit Rating",
    17: "Ranged Hit Rating", 18: "Spell Hit Rating", 19: "Melee Crit Rating",
    20: "Ranged Crit Rating", 21: "Spell Crit Rating", 22: "Mastery Rating",
    23: "Versatility Rating", 24: "Cooldown Rating",
    25: "Crit Taken Melee Rating", 26: "Crit Taken Ranged Rating",
    27: "Crit Taken Spell Rating", 28: "Melee Haste Rating",
    29: "Ranged Haste Rating", 30: "Spell Haste Rating", 31: "Hit Rating",
    32: "Crit Rating", 33: "Proc Rating", 34: "Crit Taken Rating",
    35: "Resilience Rating", 36: "Haste Rating", 37: "Expertise Rating",
    38: "Attack Power", 39: "Ranged Attack Power",
    41: "Spell Healing Done", 42: "Spell Damage Done", 43: "Mana Regen",
    44: "Armor Penetration Rating", 45: "Spell Power", 46: "Health Regen",
    47: "Spell Penetration", 48: "Block Value",
}

# SharedDefines.h ITEM_QUALITY_* (0-7, standard client values, unmodified by
# this fork). Also the .item-quality-N CSS classes in style.css.
QUALITY_NAMES = {
    0: "Poor", 1: "Common", 2: "Uncommon", 3: "Rare",
    4: "Epic", 5: "Legendary", 6: "Artifact", 7: "Heirloom",
}

# CreatureEliteType (SharedDefines.h).
RANK_NAMES = {0: "", 1: "Elite", 2: "Rare Elite", 3: "Boss", 4: "Rare"}

_NAME_OVERRIDES = {
    "instance_the_stockade": "The Stockade",
    "instance_zulfarrak": "Zul'Farrak",
    "instance_zulgurub": "Zul'Gurub",
    "instance_zulaman": "Zul'Aman",
    "instance_onyxias_lair": "Onyxia's Lair",
    "instance_gruuls_lair": "Gruul's Lair",
    "instance_magtheridons_lair": "Magtheridon's Lair",
    "instance_ahnkahet": "Ahn'kahet: The Old Kingdom",
    "instance_the_eye": "The Eye",
    "instance_old_hillsbrad": "Old Hillsbrad Foothills",
}


def _pretty_instance_name(script: str, map_id: int) -> str:
    if not script:
        return f"Map {map_id}"
    if script in _NAME_OVERRIDES:
        return _NAME_OVERRIDES[script]
    words = script.removeprefix("instance_").split("_")
    return " ".join(w.capitalize() for w in words)


_cache: dict[str, tuple] = {}


def _cached(key: str, path: Path, builder):
    mtime = path.stat().st_mtime_ns
    hit = _cache.get(key)
    if hit is not None and hit[0] == mtime:
        return hit[1]
    value = builder()
    _cache[key] = (mtime, value)
    return value


def dungeon_maps() -> dict[int, str]:
    """{map id: display name} for every row in instance_template - i.e.
    every actual dungeon/raid/instanced map, in this build's DB."""
    def build():
        cols = parse_create_table_columns(INSTANCE_TEMPLATE, "instance_template")
        rows = read_table_dump(INSTANCE_TEMPLATE, "instance_template", cols, "map")
        return {
            row["map"]: _pretty_instance_name(row["script"], row["map"])
            for row in rows.values()
        }
    return _cached("dungeon_maps", INSTANCE_TEMPLATE, build)


def _creature_templates() -> dict[int, dict]:
    def build():
        cols = parse_create_table_columns(CREATURE_TEMPLATE, "creature_template")
        return read_table_dump(CREATURE_TEMPLATE, "creature_template", cols, "entry")
    return _cached("creature_templates", CREATURE_TEMPLATE, build)


def _map_to_entries() -> dict[int, set[int]]:
    """{map id: {creature_template entries spawned there}} - id1/id2/id3
    are all folded in (a spawn row can randomly pick among up to 3
    templates; see creature.sql's own column comments)."""
    def build():
        cols = parse_create_table_columns(CREATURE, "creature")
        rows = read_table_rows(CREATURE, "creature", tuple(cols))
        index: dict[int, set[int]] = {}
        for row in rows:
            bucket = index.setdefault(row["map"], set())
            for id_col in ("id1", "id2", "id3"):
                entry = row.get(id_col)
                if entry:
                    bucket.add(entry)
        return index
    return _cached("map_to_entries", CREATURE, build)


def _loot_table(path: Path, cache_key: str) -> dict[int, list[dict]]:
    def build():
        cols = parse_create_table_columns(path, cache_key)
        rows = read_table_rows(path, cache_key, tuple(cols))
        index: dict[int, list[dict]] = {}
        for row in rows:
            index.setdefault(row["Entry"], []).append(row)
        return index
    return _cached(cache_key, path, build)


def _creature_loot() -> dict[int, list[dict]]:
    return _loot_table(CREATURE_LOOT_TEMPLATE, "creature_loot_template")


def _reference_loot() -> dict[int, list[dict]]:
    return _loot_table(REFERENCE_LOOT_TEMPLATE, "reference_loot_template")


def creatures_on_map(map_id: int) -> list[dict]:
    """creature_template rows for every distinct creature spawned on
    `map_id`, sorted by name."""
    templates = _creature_templates()
    entries = _map_to_entries().get(map_id, set())
    rows = [templates[e] for e in entries if e in templates]
    rows.sort(key=lambda r: r["name"])
    return rows


def loot_for_creature(creature_row: dict) -> list[dict]:
    """Flattened `{item, chance, quest_required, min_count, max_count}`
    list for one creature_template row - direct creature_loot_template
    entries plus one level of Reference expansion through
    reference_loot_template."""
    lootid = creature_row["lootid"] or creature_row["entry"]
    direct = _creature_loot().get(lootid, [])
    out = []
    for row in direct:
        if row["Reference"]:
            for ref_row in _reference_loot().get(row["Reference"], []):
                out.append({
                    "item": ref_row["Item"],
                    "chance": row["Chance"] * ref_row["Chance"] / 100,
                    "quest_required": bool(row["QuestRequired"] or ref_row["QuestRequired"]),
                    "min_count": ref_row["MinCount"],
                    "max_count": ref_row["MaxCount"],
                })
        elif row["Item"]:
            out.append({
                "item": row["Item"],
                "chance": row["Chance"],
                "quest_required": bool(row["QuestRequired"]),
                "min_count": row["MinCount"],
                "max_count": row["MaxCount"],
            })
    return out


def quality_name(quality: int) -> str:
    return QUALITY_NAMES.get(quality, f"Quality {quality}")


def rank_name(rank: int) -> str:
    return RANK_NAMES.get(rank, "")


def summarize_stats(item_row: dict) -> list[str]:
    """['+15 Intellect', '+22 Stamina', ...] for the item's 10 stat
    slots, skipping zero/unknown-type slots."""
    out = []
    for n in range(1, 11):
        stat_type = item_row.get(f"stat_type{n}", 0)
        value = item_row.get(f"stat_value{n}", 0)
        if not value or not stat_type:
            continue
        name = ITEM_MOD_NAMES.get(stat_type, f"stat_type {stat_type}")
        out.append(f"{value:+d} {name}")
    return out


def dungeon_summary(map_id: int, min_quality: int = 2) -> list[dict]:
    """One entry per creature on `map_id` that drops at least one item at
    or above `min_quality`, each with its qualifying loot resolved against
    the live (overlay-aware) item_template rows."""
    items = get_rows()
    summary = []
    for creature in creatures_on_map(map_id):
        drops = []
        for loot in loot_for_creature(creature):
            item = items.get(loot["item"])
            if item is None or item["Quality"] < min_quality:
                continue
            drops.append({**loot, "item_row": item})
        if drops:
            drops.sort(key=lambda d: -d["item_row"]["Quality"])
            summary.append({"creature": creature, "drops": drops})
    return summary
