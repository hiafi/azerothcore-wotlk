"""
Read-only "what drops where": `instance_template` (map -> dungeon/raid),
`creature` (spawns) + `creature_template` (name/rank/lootid),
`creature_loot_template` + `reference_loot_template` (lootid -> items), and
`instance_encounters` (which creature entries are a real encounter boss),
joined against `item_template`'s already-overlay-aware rows from
`lib.overlay.get_rows()` so an edit made through this tool shows up here
immediately.

Base-dump only for the five tables above (no pending-SQL overlay replay
the way `lib/overlay.py` does for `item_template`) - this repo's history
hasn't added custom loot yet, and these tables are large enough
(`creature.sql` alone is ~150k rows) that extending the replay machinery
to them is deferred until it's actually needed; see the README's "Known
limitations". `item_template` itself is always current, since it's read
through `lib.overlay.get_rows()`, not read again here.
"""

from __future__ import annotations

from pathlib import Path

from .item_enums import ITEM_MOD_NAMES
from .overlay import REPO_ROOT, get_rows
from .sql_dump import parse_create_table_columns, read_table_dump, read_table_rows

BASE_DIR = REPO_ROOT / "data/sql/base/db_world"
INSTANCE_TEMPLATE = BASE_DIR / "instance_template.sql"
CREATURE = BASE_DIR / "creature.sql"
CREATURE_TEMPLATE = BASE_DIR / "creature_template.sql"
CREATURE_LOOT_TEMPLATE = BASE_DIR / "creature_loot_template.sql"
REFERENCE_LOOT_TEMPLATE = BASE_DIR / "reference_loot_template.sql"
INSTANCE_ENCOUNTERS = BASE_DIR / "instance_encounters.sql"

# SharedDefines.h ITEM_QUALITY_* (0-7, standard client values, unmodified by
# this fork). Also the .item-quality-N CSS classes in style.css.
QUALITY_NAMES = {
    0: "Poor", 1: "Common", 2: "Uncommon", 3: "Rare",
    4: "Epic", 5: "Legendary", 6: "Artifact", 7: "Heirloom",
}

# CreatureEliteType (SharedDefines.h). Not what dungeon_summary uses to
# decide "Boss" vs "Trash Drops" (see _boss_creature_entries below) - every
# dungeon boss is also just rank Elite, same as a dungeon's trash, so rank
# alone can't tell them apart. It's still shown next to a creature's name.
RANK_NAMES = {0: "", 1: "Elite", 2: "Rare Elite", 3: "Boss", 4: "Rare"}
CREATURE_ELITE_WORLDBOSS = 3  # SharedDefines.h - a second, rank-based boss signal; see below

# Map.h EncounterCreditType - instance_encounters.creditType. Only KILL_
# CREATURE rows point at a creature_template entry (CAST_SPELL rows'
# creditEntry is a spell ID instead, and are skipped).
ENCOUNTER_CREDIT_KILL_CREATURE = 0

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


def _boss_creature_entries() -> set[int]:
    """creature_template entries that are a real encounter boss - built
    from `instance_encounters` (`data/sql/base/db_world/
    instance_encounters.sql`, achievement/kill-credit tracking data), not
    `rank`: a dungeon's own boss is rank Elite, identical to its trash, so
    rank can't tell them apart the way it can for a raid's rank-WORLDBOSS
    bosses (still folded in too, via CREATURE_ELITE_WORLDBOSS in
    dungeon_summary - belt and suspenders, since some world-boss-style
    encounters have no instance_encounters row at all).

    Coverage gap worth knowing: this only lists what's actually in that
    table - a boss encounter with no instance_encounters row, or one whose
    row is creditType CAST_SPELL rather than KILL_CREATURE (no creature
    entry to point at), won't be flagged. It also can't catch a boss
    that's summoned dynamically by a script rather than placed as a static
    `creature` table spawn (e.g. ICC's Sindragosa) - creatures_on_map()
    itself never sees those rows either way, so they're missing from the
    dungeon browser entirely, not just misclassified."""
    def build():
        cols = parse_create_table_columns(INSTANCE_ENCOUNTERS, "instance_encounters")
        rows = read_table_rows(INSTANCE_ENCOUNTERS, "instance_encounters", tuple(cols))
        return {
            row["creditEntry"] for row in rows
            if row["creditType"] == ENCOUNTER_CREDIT_KILL_CREATURE
        }
    return _cached("boss_creature_entries", INSTANCE_ENCOUNTERS, build)


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


def dungeon_summary(map_id: int, min_quality: int = 2) -> dict:
    """`{"bosses": [...], "trash": [...]}` for every creature on `map_id`
    that drops at least one item at or above `min_quality`, resolved
    against the live (overlay-aware) item_template rows.

    A creature counts as a boss - keeping its own per-creature entry under
    "bosses" - if it's in `_boss_creature_entries()` (real encounter data,
    not rank: see that function's docstring for why rank alone can't tell
    a dungeon's boss from its trash) or is rank CREATURE_ELITE_WORLDBOSS.
    Everything else (normal/elite/rare elite/rare trash) is pooled by item
    into "trash", one row per unique item regardless of how many different
    trash creatures drop it (a dungeon's trash list is usually large and
    overlapping; per-creature trash blocks the way bosses get them just
    isn't "at a glance")."""
    items = get_rows()
    boss_entries = _boss_creature_entries()
    bosses = []
    trash_by_item: dict[int, dict] = {}
    for creature in creatures_on_map(map_id):
        drops = []
        for one_drop in loot_for_creature(creature):
            item = items.get(one_drop["item"])
            if item is None or item["Quality"] < min_quality:
                continue
            drops.append({**one_drop, "item_row": item})
        if not drops:
            continue
        if creature["entry"] in boss_entries or creature["rank"] == CREATURE_ELITE_WORLDBOSS:
            drops.sort(key=lambda d: -d["item_row"]["Quality"])
            bosses.append({"creature": creature, "drops": drops})
        else:
            for drop in drops:
                bucket = trash_by_item.setdefault(drop["item"], {
                    "item_row": drop["item_row"], "chance": drop["chance"],
                    "quest_required": False, "creatures": set(),
                })
                bucket["chance"] = max(bucket["chance"], drop["chance"])
                bucket["quest_required"] = bucket["quest_required"] or drop["quest_required"]
                bucket["creatures"].add(creature["name"])

    trash = sorted(
        (
            {**bucket, "creatures": sorted(bucket["creatures"])}
            for bucket in trash_by_item.values()
        ),
        key=lambda b: (-b["item_row"]["Quality"], b["item_row"]["name"]),
    )
    return {"bosses": bosses, "trash": trash}
