"""
Dungeon finder entries (lfg-classic-heroic, .agents/plans/lfg-classic-heroic/): a random queue, the per-dungeon heroic
entries it draws from, and the "Specific Dungeons" section header they list under. Declared in `source/world/`
(shared: only a full generate.py run writes them). lib/lfg_dungeons.py builds the rows from the stock client files
once everything is loaded:

- `lfg_group(...)`: an LFGDungeonGroup.dbc row (the section header). Client-only, merged into patch-Z.
- `lfg_random(...)`: an LFGDungeons random row (TypeID 6, MapID 0). Server overlay `lfgdungeons_dbc` plus patch-Z.
  `LFGMgr::LoadLFGDungeons` files every non-random row under its Group_Id and a random row draws from its own group, so
  a random needs a group of its own.
- `lfg_override(...)`: an edit of a STOCK LFGDungeons row (type, group, flags, level window, entrance position): the
  whole row goes to the overlay and patch-Z over the stock one (the Blackrock Spire build turns Upper Blackrock Spire,
  a raid-type row the Finder cannot queue, into a dungeon entry so it can be queued and joins Random Classic).
  `last_encounter=` moves the row's final boss (below).
- `lfg_dungeon(...)`: a NEW normal dungeon row (TypeID 1, Difficulty 0): one more finder entry (a section) of an
  instance map, its texture and description copied from a stock row, filed in a normal group (Classic Dungeons, so it
  joins Random Classic). Server overlay plus patch-Z, its `lfg_dungeon_template` start, and its final boss.
- `lfg_heroic(...)`: an LFGDungeons heroic row (TypeID 5, Difficulty 1) copied from a stock normal dungeon row (name,
  map, texture), in the group of a random, with that random's level window. Also the heroic final boss's
  `instance_encounters.lastEncounterDungeon` (without it `Map::UpdateEncounterState` never calls
  `LFGMgr::FinishDungeon` and the run never completes) and, when the normal row has one, the `lfg_dungeon_template`
  entrance position. The map must have a declared heroic (`dungeon(..., heroic=heroic(...))`, lib/dsl/dungeon.py).
  `normal` may be a stock row or an lfg_dungeon() row.

The final boss (`last_encounter=` on lfg_dungeon() / lfg_override()): the normal `instance_encounters` row of that
DungeonEncounter id gets `lastEncounterDungeon` = the finder entry (`Map::UpdateEncounterState` ->
`LFGMgr::FinishDungeon`), and every other row that ends the same entry now (live) or in the stock dump is set to 0, so
the entry has exactly one final boss. The heroic copies (lib/dungeon_heroic.py) follow the edited link, so the heroic
entry of that normal row completes on the heroic copy of the new final boss.

    from lib.dsl.lfg import lfg_dungeon, lfg_group, lfg_heroic, lfg_random

    lfg_group(12, name="Classic Heroic", order_index=5, type_id=5)
    lfg_random(300, "Random Classic Heroic", group=12, like=260, expansion=0, min_level=60, max_level=62)
    lfg_heroic(301, normal=6, group=12)  # Deadmines
    lfg_override(44, type_id=1, group=1, flags=3, min_level=55, max_level=65, position=(98.25, -300.75, 63.1, 4.94))
    lfg_override(30, last_encounter=230)  # BRD - Prison now ends at the Ring of Law (Gerstahn's link is cleared)
    lfg_dungeon(308, "Blackrock Depths - Shadowforge City", map_id=230, like=30, min_level=48, max_level=58,
                target_level=53, last_encounter=235, position=(595.0, -92.0, -45.0, 0.0))
    lfg_heroic(310, normal=308, group=12)
"""

from __future__ import annotations

from . import registry as _registry
from .dungeon import _check_block, _plain_int

LFG_TYPE_DUNGEON = 1  # LFGMgr.h LfgType
LFG_TYPE_RAID = 2
LFG_TYPE_HEROIC = 5
LFG_TYPE_RANDOM = 6
GROUP_TYPE_HEROIC = 5  # LFGDungeonGroup.dbc TypeID of the stock heroic sections (3, 5)
MAX_LEVEL = 80  # DBCEnums.h DEFAULT_MAX_LEVEL
MAX_EXPANSION = 2
NAME_MAX_LENGTH = 100


def _name(label: str, value) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > NAME_MAX_LENGTH or "\n" in value:
        raise ValueError(f"{label}: name must be a non-empty one-line string of at most {NAME_MAX_LENGTH} characters, "
                         f"got {value!r}")
    return value


def lfg_group(group_id: int, *, order_index: int, name: str | None = None, type_id: int | None = None) -> dict:
    """A "Specific Dungeons" section header (LFGDungeonGroup.dbc row). `order_index`: where it lists (lower first;
    stock: Lich King Heroic 1 ... Classic Dungeons 5, raids 17-21).

    A new id comes from source/ids.yaml's `lfgdungeongroup` block and needs `name` and `type_id` (5 for a heroic
    section, 1 for a normal one). An id outside the block edits that stock row: it keeps its stock name and type
    unless given, and takes `order_index` (e.g. moving Classic Dungeons down one to fit a new section above it).
    generate.py stops on a stock id that does not exist, a new id that does, and a missing stock file."""
    label = f"lfg_group({group_id!r})"
    if not _plain_int(group_id) or group_id <= 0:
        raise ValueError(f"{label}: group_id must be a positive int")
    if not _plain_int(order_index) or order_index < 0:
        raise ValueError(f"{label}: order_index must be a non-negative int")
    block = (_registry._active_ids_cfg or {}).get("lfgdungeongroup")
    new = bool(block) and block["start"] <= group_id <= block["end"]
    if new:
        if name is None or type_id is None:
            raise ValueError(f"{label}: a new group (ids.yaml lfgdungeongroup block) needs name= and type_id=")
    if name is not None:
        _name(label, name)
    if type_id is not None and (not _plain_int(type_id) or type_id < 0):
        raise ValueError(f"{label}: type_id must be a non-negative int")
    entry = {"id": group_id, "new": new, "name": name, "order_index": order_index, "type_id": type_id}
    _registry._require_active().lfg_group_declarations.append(entry)
    return entry


def lfg_random(
    dungeon_id: int, name: str, *, group: int, like: int, expansion: int, min_level: int, max_level: int,
    target_level: int | None = None,
) -> dict:
    """A random dungeon queue (LFGDungeons.dbc TypeID 6) named `name` that draws from every dungeon row of `group`.
    `like` is a stock random row whose Difficulty, Flags, Faction and locale mask the row copies (260 Random Burning
    Crusade Heroic for a heroic random); `expansion` the ExpansionLevel (0 Classic: the player's account expansion
    must reach it, and mod-content-gate keeps a heroic random's window as is). `min_level` / `max_level` is the window
    the server and the client both use (the group's lfg_heroic() rows take it too); `target_level` the suggested level
    (default `min_level`). The id comes from source/ids.yaml's `lfgdungeons` block; one random per group."""
    label = f"lfg_random({dungeon_id!r}, {name!r})"
    if not _plain_int(dungeon_id):
        raise ValueError(f"{label}: dungeon_id must be an int")
    _check_block(label, "lfgdungeons", dungeon_id)
    _name(label, name)
    for key, value in (("group", group), ("like", like)):
        if not _plain_int(value) or value <= 0:
            raise ValueError(f"{label}: {key} must be a positive int, got {value!r}")
    if not _plain_int(expansion) or not 0 <= expansion <= MAX_EXPANSION:
        raise ValueError(f"{label}: expansion must be an int in 0..{MAX_EXPANSION}, got {expansion!r}")
    if not _plain_int(min_level) or not 1 <= min_level <= MAX_LEVEL:
        raise ValueError(f"{label}: min_level must be an int in 1..{MAX_LEVEL}, got {min_level!r}")
    if not _plain_int(max_level) or not min_level <= max_level <= 255:
        raise ValueError(f"{label}: max_level must be an int in min_level..255, got {max_level!r}")
    if target_level is None:
        target_level = min_level
    if not _plain_int(target_level) or not min_level <= target_level <= max_level:
        raise ValueError(f"{label}: target_level must be an int in min_level..max_level, got {target_level!r}")
    entry = {
        "id": dungeon_id, "kind": "random", "name": name, "group": group, "like": like, "expansion": expansion,
        "min_level": min_level, "max_level": max_level, "target_level": target_level,
    }
    _registry._require_active().lfg_dungeon_declarations.append(entry)
    return entry


def _position(label: str, position) -> tuple[float, float, float, float] | None:
    if position is None:
        return None
    if (not isinstance(position, (tuple, list)) or len(position) != 4
            or not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in position)):
        raise ValueError(f"{label}: position must be (x, y, z, orientation), got {position!r}")
    return tuple(float(v) for v in position)


def _encounter(label: str, value) -> int:
    if not _plain_int(value) or value <= 0:
        raise ValueError(f"{label}: last_encounter must be a DungeonEncounter id (the instance_encounters entry of the "
                         f"final boss), got {value!r}")
    return value


# The columns lfg_override() may change, by its argument name.
OVERRIDE_COLUMNS = {
    "type_id": "TypeID", "group": "Group_Id", "flags": "Flags", "min_level": "MinLevel", "max_level": "MaxLevel",
    "target_level": "Target_Level", "target_level_min": "Target_Level_Min", "target_level_max": "Target_Level_Max",
}


def lfg_override(
    dungeon_id: int, *, type_id: int | None = None, group: int | None = None, flags: int | None = None,
    min_level: int | None = None, max_level: int | None = None, target_level: int | None = None,
    target_level_min: int | None = None, target_level_max: int | None = None,
    position: tuple[float, float, float, float] | None = None, last_encounter: int | None = None,
) -> dict:
    """An edit of the STOCK LFGDungeons row `dungeon_id`: each argument given replaces that column of the stock row
    (`type_id` TypeID, `group` Group_Id, `flags` Flags, the level window, the target levels); the rest of the row
    (names, map, texture, expansion) stays stock. `position` is the entrance `(x, y, z, orientation)` of the row's
    `lfg_dungeon_template`, for a row that has none (the Finder then falls back to the map's entrance areatrigger,
    which a wing of a map shared with another entry cannot use, or to move a stock one).

    `last_encounter` moves the entry's final boss to that DungeonEncounter id (its normal `instance_encounters` row
    gets `lastEncounterDungeon` = `dungeon_id`; the row that ended it before is set to 0; see the module docstring).
    It may be the only edit: the LFGDungeons row then stays stock and is not written.

    The edited row goes to the server overlay (`lfgdungeons_dbc`) and patch-Z's LFGDungeons.dbc over the stock row, so
    the server and the client agree. Every later declaration sees the edited row: `lfg_heroic(normal=dungeon_id)`
    needs a stock normal dungeon row (TypeID 1), which this can make of a raid-type one. generate.py stops on an id
    that is not a stock row. Custom rows (ids.yaml's `lfgdungeons` block) are declared with lfg_random() /
    lfg_dungeon() / lfg_heroic(), never edited."""
    label = f"lfg_override({dungeon_id!r})"
    if last_encounter is not None:
        last_encounter = _encounter(label, last_encounter)
    if not _plain_int(dungeon_id) or dungeon_id <= 0:
        raise ValueError(f"{label}: dungeon_id must be a positive int")
    block = (_registry._active_ids_cfg or {}).get("lfgdungeons")
    if block and block["start"] <= dungeon_id <= block["end"]:
        raise ValueError(f"{label}: {dungeon_id} is in ids.yaml's lfgdungeons block (custom rows are declared with "
                         f"lfg_random() / lfg_dungeon() / lfg_heroic()); lfg_override edits a stock row")
    values = {"type_id": type_id, "group": group, "flags": flags, "min_level": min_level, "max_level": max_level,
              "target_level": target_level, "target_level_min": target_level_min,
              "target_level_max": target_level_max}
    edits = {name: value for name, value in values.items() if value is not None}
    for name, value in edits.items():
        limit = 255 if "level" in name else 0xFFFFFFFF
        if not _plain_int(value) or not 0 <= value <= limit:
            raise ValueError(f"{label}: {name} must be an int in 0..{limit}, got {value!r}")
    if "type_id" in edits and edits["type_id"] not in (LFG_TYPE_DUNGEON, LFG_TYPE_RAID, LFG_TYPE_HEROIC):
        raise ValueError(f"{label}: type_id must be 1 (dungeon), 2 (raid) or 5 (heroic), got {type_id!r}")
    low, high = edits.get("min_level"), edits.get("max_level")
    if low is not None and high is not None and low > high:
        raise ValueError(f"{label}: min_level {low} is above max_level {high}")
    position = _position(label, position)
    if not edits and position is None and last_encounter is None:
        raise ValueError(f"{label}: nothing to edit - give at least one column, a position or a last_encounter")
    entry = {"id": dungeon_id, "kind": "override", "edits": edits, "position": position,
             "last_encounter": last_encounter}
    _registry._require_active().lfg_dungeon_declarations.append(entry)
    return entry


def lfg_dungeon(
    dungeon_id: int, name: str, *, map_id: int, like: int, min_level: int, max_level: int, target_level: int,
    last_encounter: int, group: int = 1, flags: int = 3, target_level_min: int | None = None,
    target_level_max: int | None = None, position: tuple[float, float, float, float] | None = None,
) -> dict:
    """A NEW normal finder entry (LFGDungeons.dbc TypeID 1, Difficulty 0) named `name` on instance map `map_id`: one
    more section of a map that already has a stock entry (Blackrock Depths' Shadowforge City and Manufactory).

    `like` is a stock normal dungeon row (TypeID 1; an lfg_override()-edited row counts) whose TextureFilename,
    descriptions, Faction, ExpansionLevel, Order_Index and locale masks the row copies (30 Blackrock Depths - Prison
    for the BRD sections); the name is set in enUS only. `group` is the Specific Dungeons section it lists under and
    the random that draws it (1 Classic Dungeons -> 258 Random Classic Dungeon); `flags` 3 like every stock dungeon row.
    `min_level` / `max_level` is the window the server and the client use, `target_level` the suggested level;
    `target_level_min` / `_max` default to the stock rows' shape (target - 2 / target + 1, kept in the window).

    `last_encounter` is the DungeonEncounter id whose kill completes the entry (its normal `instance_encounters` row
    gets `lastEncounterDungeon` = `dungeon_id`; generate.py stops when that encounter is not a normal encounter of
    `map_id`, or has no instance_encounters row). `position` `(x, y, z, orientation)` is the Finder start
    (`lfg_dungeon_template`); without it LFGMgr falls back to the map's entrance areatrigger, the first section's
    door. An lfg_heroic(normal=dungeon_id) copies both. The id comes from source/ids.yaml's `lfgdungeons` block."""
    label = f"lfg_dungeon({dungeon_id!r}, {name!r})"
    if not _plain_int(dungeon_id):
        raise ValueError(f"{label}: dungeon_id must be an int")
    _check_block(label, "lfgdungeons", dungeon_id)
    _name(label, name)
    for key, value in (("map_id", map_id), ("like", like), ("group", group)):
        if not _plain_int(value) or value <= 0:
            raise ValueError(f"{label}: {key} must be a positive int, got {value!r}")
    if not _plain_int(flags) or not 0 <= flags <= 0xFFFFFFFF:
        raise ValueError(f"{label}: flags must be an int in 0..{0xFFFFFFFF}, got {flags!r}")
    if not _plain_int(min_level) or not 1 <= min_level <= MAX_LEVEL:
        raise ValueError(f"{label}: min_level must be an int in 1..{MAX_LEVEL}, got {min_level!r}")
    if not _plain_int(max_level) or not min_level <= max_level <= 255:
        raise ValueError(f"{label}: max_level must be an int in min_level..255, got {max_level!r}")
    if not _plain_int(target_level) or not min_level <= target_level <= max_level:
        raise ValueError(f"{label}: target_level must be an int in min_level..max_level, got {target_level!r}")
    if target_level_min is None:
        target_level_min = max(min_level, target_level - 2)
    if target_level_max is None:
        target_level_max = min(max_level, target_level + 1)
    if not _plain_int(target_level_min) or not min_level <= target_level_min <= target_level:
        raise ValueError(f"{label}: target_level_min must be an int in min_level..target_level, got "
                         f"{target_level_min!r}")
    if not _plain_int(target_level_max) or not target_level <= target_level_max <= max_level:
        raise ValueError(f"{label}: target_level_max must be an int in target_level..max_level, got "
                         f"{target_level_max!r}")
    entry = {
        "id": dungeon_id, "kind": "dungeon", "name": name, "map_id": map_id, "like": like, "group": group,
        "flags": flags, "min_level": min_level, "max_level": max_level, "target_level": target_level,
        "target_level_min": target_level_min, "target_level_max": target_level_max,
        "position": _position(label, position), "last_encounter": _encounter(label, last_encounter),
    }
    _registry._require_active().lfg_dungeon_declarations.append(entry)
    return entry


def lfg_heroic(dungeon_id: int, *, normal: int, group: int) -> dict:
    """The heroic finder entry (LFGDungeons.dbc TypeID 5, Difficulty 1) of the normal dungeon row `normal`, a stock
    row (6 Deadmines, 40 Stratholme - Main Gate, ...) or an lfg_dungeon() one: same names, map, texture and
    expansion, filed under `group`, with the level window of that group's lfg_random(). The id comes from
    source/ids.yaml's `lfgdungeons` block.

    generate.py stops when `normal` is neither a stock nor a declared normal dungeon row, its map has no declared
    heroic, the group has no random, or no heroic encounter of the map carries the normal row's final boss (the
    heroic run could never complete)."""
    label = f"lfg_heroic({dungeon_id!r}, normal={normal!r})"
    if not _plain_int(dungeon_id):
        raise ValueError(f"{label}: dungeon_id must be an int")
    _check_block(label, "lfgdungeons", dungeon_id)
    for key, value in (("normal", normal), ("group", group)):
        if not _plain_int(value) or value <= 0:
            raise ValueError(f"{label}: {key} must be a positive int, got {value!r}")
    entry = {"id": dungeon_id, "kind": "heroic", "normal": normal, "group": group}
    _registry._require_active().lfg_dungeon_declarations.append(entry)
    return entry
