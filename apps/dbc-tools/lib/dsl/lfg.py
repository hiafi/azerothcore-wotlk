"""
Dungeon finder entries (lfg-classic-heroic, .agents/plans/lfg-classic-heroic/): a random queue, the per-dungeon heroic
entries it draws from, and the "Specific Dungeons" section header they list under. Declared in `source/world/`
(shared: only a full generate.py run writes them). lib/lfg_dungeons.py builds the rows from the stock client files
once everything is loaded:

- `lfg_group(...)`: an LFGDungeonGroup.dbc row (the section header). Client-only, merged into patch-Z.
- `lfg_random(...)`: an LFGDungeons random row (TypeID 6, MapID 0). Server overlay `lfgdungeons_dbc` plus patch-Z.
  `LFGMgr::LoadLFGDungeons` files every non-random row under its Group_Id and a random row draws from its own group, so
  a random needs a group of its own.
- `lfg_heroic(...)`: an LFGDungeons heroic row (TypeID 5, Difficulty 1) copied from a stock normal dungeon row (name,
  map, texture), in the group of a random, with that random's level window. Also the heroic final boss's
  `instance_encounters.lastEncounterDungeon` (without it `Map::UpdateEncounterState` never calls
  `LFGMgr::FinishDungeon` and the run never completes) and, when the normal row has one, the `lfg_dungeon_template`
  entrance position. The map must have a declared heroic (`dungeon(..., heroic=heroic(...))`, lib/dsl/dungeon.py).

    from lib.dsl.lfg import lfg_group, lfg_heroic, lfg_random

    lfg_group(12, name="Classic Heroic", order_index=5, type_id=5)
    lfg_random(300, "Random Classic Heroic", group=12, like=260, expansion=0, min_level=60, max_level=62)
    lfg_heroic(301, normal=6, group=12)  # Deadmines
"""

from __future__ import annotations

from . import registry as _registry
from .dungeon import _check_block, _plain_int

LFG_TYPE_DUNGEON = 1  # LFGMgr.h LfgType
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


def lfg_heroic(dungeon_id: int, *, normal: int, group: int) -> dict:
    """The heroic finder entry (LFGDungeons.dbc TypeID 5, Difficulty 1) of the stock normal dungeon row `normal`
    (6 Deadmines, 40 Stratholme - Main Gate, ...): same names, map, texture and expansion, filed under `group`, with
    the level window of that group's lfg_random(). The id comes from source/ids.yaml's `lfgdungeons` block.

    generate.py stops when `normal` is not a stock normal dungeon row, its map has no declared heroic, the group has
    no random, or no heroic encounter of the map carries the normal row's final boss (the heroic run could never
    complete)."""
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
