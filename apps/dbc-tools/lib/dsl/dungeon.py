"""
Per-dungeon declarations (dungeon difficulties, .agents/plans/dungeon-difficulties/): one `dungeon(...)` call per
instance map, in `source/world/dungeons/<name>.py`, holding everything this tool emits for that dungeon.

E1 (WP-T1) emits, for a dungeon with `heroic=heroic(...)`:

- a `mapdifficulty_dbc` row (Difficulty 1) and the same row merged into the client `MapDifficulty.dbc` in patch-Z.
  Without the server row `GetDownscaledMapDifficultyData` steps a heroic request down to normal; without the client
  row the client has no refusal text and no difficulty name for Raid Info.
- a `dungeon_access_template` row (map, difficulty 1): the level / item level gate `MapMgr::PlayerCannotEnter`
  checks (GMs skip it).

E2 (WP-T2, generate.py's side in lib/dungeon_heroic.py) adds, for the same heroic:

- `encounter_ids=`: one heroic DungeonEncounter row per normal encounter of the map (stock file plus live overlay),
  copying its Bit, OrderIndex and names, server overlay and patch-Z, and the `instance_encounters` row that credits it
  (the normal row's credit type and entry, no dungeon finder link). Without them `Map::UpdateEncounterState` finds no
  heroic list: no completed-encounter bit, no boss list for mod-dungeon-clear.
- `spawn_mask=True` (the default): every creature and gameobject spawn on the map gets the heroic bit, as a targeted
  `UPDATE ... SET spawnMask = spawnMask | 2` of the spawns live does not already have it on. Game event spawns are left
  out unless `event_spawns=True`.
- the per-creature emitters, inert until WP-G hands over its normal -> heroic entry map (the lock file) as
  `entry["heroic_entries"]` on the `Registry.dungeons` bookkeeping entry: `difficulty_entry_1` on each normal row (one
  column) and copies of the side tables the engine reads by the heroic entry.

A `dungeon(...)` without `heroic` emits nothing: the normal rows belong to stock data and the frozen phase 0 SQL.
Later stages extend the same two calls rather than adding a second declaration per dungeon: WP-G adds the creature
list and the heroic template generator (tier, bosses, overrides) - see the E1-T1 report for the proposed shape. They
read `Registry.dungeons` (one entry per call: `map_id`, `name`, `heroic` as a plain dict or None, `heroic_entries`).

    from lib.dsl.dungeon import dungeon, heroic

    dungeon(36, "Deadmines", heroic=heroic(
        map_difficulty_id=1000, access_id=122, min_level=60, encounter_ids=range(1000, 1007),
    ))
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .. import dbcfmt
from . import registry as _registry

DUNGEON_DIFFICULTY_HEROIC = 1  # DBCEnums.h Difficulty; also dungeon_access_template.difficulty for a 5-man heroic
DEFAULT_MAX_LEVEL = 80  # DBCEnums.h
# Utgarde Keep's stock heroic row (MapDifficulty.dbc ID 143) - every 5-man heroic in the stock file has these.
HEROIC_RESET_SECONDS = 86400
HEROIC_MAX_PLAYERS = 5
HEROIC_MESSAGE_MASK = 0xFF01FE  # Message_Lang_Mask of a row with an enUS message (0xFF01FC without one)
HEROIC_DIFFICULTY_STRING = "DUNGEON_DIFFICULTY_5PLAYER_HEROIC"  # the client's Raid Info / tooltip name for it
MESSAGE_MAX_LENGTH = 200  # mapdifficulty_dbc.Message_Lang_enUS is varchar(200)
ITEM_LEVEL_MAX = 0xFFFF  # dungeon_access_template.min_avg_item_level is smallint unsigned
MAX_PLAYERS_MAX = 40


def _plain_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


@dataclass(frozen=True)
class HeroicSpec:
    """What `heroic()` returns; `dungeon()` turns it into rows. E2 adds fields here (tier, bosses, overrides)."""

    map_difficulty_id: int
    access_id: int
    min_level: int
    max_level: int = 0
    min_item_level: int = 0
    reset_seconds: int = HEROIC_RESET_SECONDS
    max_players: int = HEROIC_MAX_PLAYERS
    message: str = ""
    encounter_ids: tuple[int, ...] = ()
    spawn_mask: bool = True
    event_spawns: bool = False


def heroic(
    *, map_difficulty_id: int, access_id: int, min_level: int, max_level: int = 0, min_item_level: int = 0,
    reset_seconds: int = HEROIC_RESET_SECONDS, max_players: int = HEROIC_MAX_PLAYERS, message: str | None = None,
    encounter_ids=(), spawn_mask: bool = True, event_spawns: bool = False,
) -> HeroicSpec:
    """The heroic difficulty (Difficulty 1) of a 5-man dungeon, for `dungeon(..., heroic=...)`.

    `map_difficulty_id` is the MapDifficulty row id, from `source/ids.yaml`'s `mapdifficulty` block (stock tops out at
    753); `access_id` the `dungeon_access_template.id`, from the `dungeon_access` block (a tinyint: stock tops out at
    121). Both stay fixed once shipped: the client caches the patch, and a save names the map and difficulty, not the
    row, but a moved id would leave the old row behind until the prune pass removes it.

    `min_level` / `max_level` (0 = no cap) / `min_item_level` (0 = none; the average equipped item level) are the
    entry gate. `reset_seconds` is the lockout (`RaidDuration`, a day like every stock heroic; non-zero, or a kill
    binds nothing); `max_players` the group size the client shows (5). `message` is what the client prints when the
    gate refuses a player; the default names `min_level` like the stock rows do ("Heroic Difficulty requires you to
    be level 80.").

    `encounter_ids` (E2) are the DungeonEncounter ids of the heroic boss list, from the `dungeonencounter` block (stock
    tops out at 894), one per normal encounter of the map in the stock file's order (`range(1000, 1007)` for the
    seven Deadmines bosses); each heroic row copies its normal row. Empty: no heroic encounter rows. Like every id
    here, never move them once shipped.

    `spawn_mask` (E2, default on: a heroic with no spawns is an empty instance with no doors) puts every creature and
    gameobject spawn of the map on heroic too; `event_spawns=True` includes the spawns a game event owns (holiday
    bosses, Scourge Invasion), which stay normal-only by default."""
    if message is None:
        message = f"Heroic Difficulty requires you to be level {min_level}."
    label = f"heroic(map_difficulty_id={map_difficulty_id!r}, ...)"
    for name, value in (("map_difficulty_id", map_difficulty_id), ("access_id", access_id)):
        if not _plain_int(value):
            raise ValueError(f"{label}: {name} must be an int, got {value!r}")
    if not _plain_int(min_level) or not 1 <= min_level <= DEFAULT_MAX_LEVEL:
        raise ValueError(f"{label}: min_level must be an int in 1..{DEFAULT_MAX_LEVEL}, got {min_level!r}")
    if not _plain_int(max_level) or not (max_level == 0 or min_level <= max_level <= DEFAULT_MAX_LEVEL):
        raise ValueError(
            f"{label}: max_level must be 0 (no cap) or an int in min_level..{DEFAULT_MAX_LEVEL}, got {max_level!r}"
        )
    if not _plain_int(min_item_level) or not 0 <= min_item_level <= ITEM_LEVEL_MAX:
        raise ValueError(f"{label}: min_item_level must be an int in 0..{ITEM_LEVEL_MAX}, got {min_item_level!r}")
    if not _plain_int(reset_seconds) or reset_seconds <= 0:
        raise ValueError(
            f"{label}: reset_seconds must be a positive int (a heroic with no reset time binds nothing), "
            f"got {reset_seconds!r}"
        )
    if not _plain_int(max_players) or not 1 <= max_players <= MAX_PLAYERS_MAX:
        raise ValueError(f"{label}: max_players must be an int in 1..{MAX_PLAYERS_MAX}, got {max_players!r}")
    if not isinstance(message, str) or not message.strip() or len(message) > MESSAGE_MAX_LENGTH:
        raise ValueError(
            f"{label}: message must be a non-empty string of at most {MESSAGE_MAX_LENGTH} characters (an empty one "
            f"makes the server send no refusal text), got {message!r}"
        )
    try:
        encounters = tuple(encounter_ids)
    except TypeError:
        raise ValueError(f"{label}: encounter_ids must be a sequence of ints, got {encounter_ids!r}") from None
    if not all(_plain_int(e) and e > 0 for e in encounters) or len(set(encounters)) != len(encounters):
        raise ValueError(f"{label}: encounter_ids must be distinct positive ints, got {encounter_ids!r}")
    for name, value in (("spawn_mask", spawn_mask), ("event_spawns", event_spawns)):
        if not isinstance(value, bool):
            raise ValueError(f"{label}: {name} must be True or False, got {value!r}")
    if event_spawns and not spawn_mask:
        raise ValueError(f"{label}: event_spawns=True needs spawn_mask=True")
    return HeroicSpec(
        map_difficulty_id=map_difficulty_id, access_id=access_id, min_level=min_level, max_level=max_level,
        min_item_level=min_item_level, reset_seconds=reset_seconds, max_players=max_players, message=message,
        encounter_ids=encounters, spawn_mask=spawn_mask, event_spawns=event_spawns,
    )


def _check_block(caller: str, block_name: str, value: int) -> None:
    block = (_registry._active_ids_cfg or {}).get(block_name)
    if not block:
        raise ValueError(
            f"{caller}: needs source/ids.yaml's `{block_name}` block - pass ids_cfg through "
            f"registry.load_class_file(path, ids_cfg=...) (generate.py already does)"
        )
    if not block["start"] <= value <= block["end"]:
        raise ValueError(
            f"{caller}: {value} is outside source/ids.yaml's {block_name} reserved block "
            f"({block['start']}-{block['end']}) - a stock row must not be overridden by accident"
        )


def map_difficulty_row(map_id: int, spec: HeroicSpec, comment: str = "") -> dict:
    """The full `mapdifficulty_dbc` / MapDifficulty.dbc row for `spec` (every column, other locales empty)."""
    row = {"id": spec.map_difficulty_id, "ID": spec.map_difficulty_id, "MapID": map_id,
           "Difficulty": DUNGEON_DIFFICULTY_HEROIC}
    for locale in dbcfmt.LOCALE_SUFFIXES:
        row[f"Message_Lang_{locale}"] = ""
    row["Message_Lang_enUS"] = spec.message
    row["Message_Lang_Mask"] = HEROIC_MESSAGE_MASK
    row["RaidDuration"] = spec.reset_seconds
    row["MaxPlayers"] = spec.max_players
    row["Difficultystring"] = HEROIC_DIFFICULTY_STRING
    row["comment"] = comment
    return row


def access_row(map_id: int, name: str, spec: HeroicSpec) -> dict:
    """The `dungeon_access_template` row for `spec`."""
    return {
        "id": spec.access_id, "map_id": map_id, "difficulty": DUNGEON_DIFFICULTY_HEROIC,
        "min_level": spec.min_level, "max_level": spec.max_level, "min_avg_item_level": spec.min_item_level,
        "comment": f"{name} - Heroic",
    }


def dungeon(map_id: int, name: str, *, heroic: HeroicSpec | None = None) -> dict:
    """Declares the dungeon on `map_id` (a Map.dbc id, e.g. 36 Deadmines) named `name`. With `heroic=heroic(...)` it
    emits that difficulty's MapDifficulty row (server overlay and client patch-Z) and its `dungeon_access_template`
    row; without it, nothing (a reference declaration later stages fill in). A map may be declared once.

    generate.py stops (also under `--check`) when the map has no stock MapDifficulty row (not an instance map: wrong
    id?), when a declared (map, difficulty) is already a stock or live MapDifficulty row under another id, when a live
    `dungeon_access_template` row already covers it under another id, and when the stock MapDifficulty.dbc is missing
    from var/extractors/dbc/. The heroic's encounter rows, spawn masks and per-creature rows are built by generate.py
    from live state (lib/dungeon_heroic.py), which has its own ERRORs. Returns the bookkeeping entry."""
    caller = f"dungeon({map_id!r}, {name!r})"
    if not _plain_int(map_id) or map_id <= 0:
        raise ValueError(f"{caller}: map_id must be a Map.dbc id (positive int)")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{caller}: name (the dungeon's name) is required")
    if heroic is not None and not isinstance(heroic, HeroicSpec):
        raise ValueError(f"{caller}: heroic must come from heroic(...), got {heroic!r}")
    registry = _registry._require_active()
    # `heroic_entries` (normal creature entry -> heroic entry) is WP-G's: its lock file fills it; lib/dungeon_heroic.py
    # reads it for difficulty_entry_1 and the side-table copies, and does nothing while it is empty.
    entry = {
        "id": map_id, "map_id": map_id, "name": name, "heroic": asdict(heroic) if heroic else None,
        "heroic_entries": {},
    }
    if heroic is not None:
        _check_block(f"{caller}: heroic map_difficulty_id", "mapdifficulty", heroic.map_difficulty_id)
        _check_block(f"{caller}: heroic access_id", "dungeon_access", heroic.access_id)
        for encounter_id in heroic.encounter_ids:
            _check_block(f"{caller}: heroic encounter_ids", "dungeonencounter", encounter_id)
        registry.map_difficulties.append(map_difficulty_row(map_id, heroic, f"{name} - Heroic"))
        registry.dungeon_access.append(access_row(map_id, name, heroic))
    registry.dungeons.append(entry)
    return entry
