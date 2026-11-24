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

FD-SM (generate.py's side in lib/dungeon_encounters.py) adds encounter rows of their own, outside any heroic:

- `dungeon_encounter(id, map_id=, order_index=, bit=, name=, credit=credit_creature(entry) | credit_spell(id))`: a
  NEW DungeonEncounter row (server overlay and patch-Z) and its `instance_encounters` credit, for a boss slot the stock
  file lacks. A heroic of the map counts it as a normal encounter.
- `repoint_encounter(id, name=, credit=, ...)`: an edit of a STOCK row (same id, map, difficulty and bit unless
  given), e.g. a cut boss's row turned into the encounter that replaced it.

    dungeon_encounter(1074, map_id=189, order_index=250, bit=7, name="Ironspine", credit=credit_creature(6489))
    repoint_encounter(449, name="The Last Stand", credit=credit_spell(212301))

E2 (WP-G, generate.py's side in lib/heroic_templates.py) adds the creature list and the heroic templates:

- `creatures=` (every declaration): the dungeon's creatures as `creature(entry, name, role, ...)` lines, the generated
  `CREATURES` block `extract_dungeon_creatures.py` writes (spawned, encounter credit and summoned creatures, see
  lib/dungeon_extract.py). Reference data: a dungeon without `heroic` still emits nothing, and no declaration ever
  writes a normal creature row. Hand edits live outside the generated block: `extra=` (creatures the extraction cannot
  see, e.g. C++ summons), `roles=` (role corrections), `skip=` (entries that never get a heroic template) and
  `retired=` (shipped heroic creatures taken out of the set: their difficulty link is reverted).
- with `heroic`: one level 60 heroic `creature_template` row per creature of the heroic entry set (lib/
  heroic_templates.py: the declared creatures plus whatever live spawns or credits on the map, minus skips, critters,
  triggers, friendly NPCs and event-only creatures), ids from the append-only lock file
  `source/world/heroic_ids.lock` (`creature_heroic` block), stats from the tier table (`heroic(tier=...)`) and the
  per-creature `heroic(overrides=...)`; `heroic_entries` then carries the normal -> heroic map to T2's emitters.

Everything reads `Registry.dungeons` (one entry per call: `map_id`, `name`, `heroic` as a plain dict or None,
`heroic_entries`, `creatures`, `skip`, `retired`).

    from lib.dsl.dungeon import creature, dungeon, heroic

    CREATURES = (creature(644, "Rhahk'Zor", "boss", spawns=1), ...)  # generated
    dungeon(36, "Deadmines", creatures=CREATURES, roles={3586: "boss"}, heroic=heroic(
        map_difficulty_id=1000, access_id=122, min_level=60, encounter_ids=range(1000, 1007),
        overrides={644: dict(health=320_000)},
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
# A creature's role in its dungeon (lib/dungeon_extract.py sets them; `dungeon(roles=...)` corrects them). boss: the
# boss tier and INSTANCE_BIND on heroic; trash: the rank's tier; npc / critter / trigger: no heroic template.
ROLES = ("boss", "trash", "npc", "critter", "trigger")
# `heroic(tier=...)` names a table in lib/heroic_templates.py's TIERS; these are its row names (by rank, plus boss).
TIER_ROWS = ("normal", "elite", "rare", "boss")
OVERRIDE_KEYS = ("health", "melee", "tier", "columns")
# creature_template columns an override's `columns` may not set: the row's identity and the inputs and outputs of the
# tier solve (lib/heroic_templates.py solves HealthModifier / DamageModifier for the tier's level, exp 0 and the normal
# row's BaseVariance). The level is the tier's and the spell rule (mod-dungeon-difficulties) and reference health
# assume it; health and melee have their own override keys.
SOLVED_COLUMNS = ("entry", "minlevel", "maxlevel", "exp", "HealthModifier", "DamageModifier", "BaseVariance")


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
    tier: str = "vanilla"
    tier_values: tuple[tuple[str, int, int], ...] = ()  # (row, health, melee) replacing a TIERS row for this dungeon
    overrides: tuple[tuple[int, tuple], ...] = ()  # (entry, sorted (key, value) pairs); see heroic()
    widen_smart_scripts: bool = True
    no_credit: tuple[int, ...] = ()  # normal DungeonEncounter ids whose heroic copy gets no instance_encounters row


def heroic(
    *, map_difficulty_id: int, access_id: int, min_level: int, max_level: int = 0, min_item_level: int = 0,
    reset_seconds: int = HEROIC_RESET_SECONDS, max_players: int = HEROIC_MAX_PLAYERS, message: str | None = None,
    encounter_ids=(), spawn_mask: bool = True, event_spawns: bool = False, tier: str = "vanilla",
    tier_values: dict | None = None, overrides: dict | None = None, widen_smart_scripts: bool = True,
    no_credit=(),
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
    seven Deadmines bosses); each heroic row copies its normal row. The map's `dungeon_encounter()` rows (Difficulty
    0) count as normal encounters and a `repoint_encounter()` edit is copied as edited, all in (OrderIndex, Bit, ID)
    order: Scarlet Monastery's 7 stock plus 7 declared rows take 14 ids. Empty: no heroic encounter rows. Like every
    id here, never move them once shipped (a new normal row between two stock ones shifts every later heroic id's
    pairing, so declare new rows before the heroic first ships).

    `no_credit` names NORMAL DungeonEncounter ids (the stock rows, e.g. 234 Fineous Darkvire) whose heroic copy keeps
    its DungeonEncounter row and its id in `encounter_ids` (the client's lockout list, the Bit, the id order) but gets
    no `instance_encounters` kill credit row: no kill completes that encounter on heroic. For an encounter whose
    credit is dropped on normal too (a hand SQL DELETE of the stock row, which generate.py never writes); with the
    normal row gone, a listed id is also exempt from the "no kill credit" WARNING. generate.py stops when a listed id
    is not a normal encounter of the map.

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
    try:
        no_credit_ids = tuple(sorted(set(no_credit)))
    except TypeError:
        raise ValueError(f"{label}: no_credit must be a sequence of DungeonEncounter ids, got {no_credit!r}") from None
    if not all(_plain_int(e) and e > 0 for e in no_credit_ids):
        raise ValueError(f"{label}: no_credit must be positive DungeonEncounter ids, got {no_credit!r}")
    if no_credit_ids and not encounters:
        raise ValueError(f"{label}: no_credit needs encounter_ids (it drops the credit of a heroic encounter copy)")
    if not isinstance(widen_smart_scripts, bool):
        raise ValueError(f"{label}: widen_smart_scripts must be True or False, got {widen_smart_scripts!r}")
    if not isinstance(tier, str) or not tier:
        raise ValueError(f"{label}: tier must be a tier table name, got {tier!r}")
    values = []
    for row, pair in sorted((tier_values or {}).items()):
        if row not in TIER_ROWS or not isinstance(pair, tuple) or len(pair) != 2 \
                or not all(_plain_int(v) and v > 0 for v in pair):
            raise ValueError(
                f"{label}: tier_values must map a row of {TIER_ROWS} to (health, melee) positive ints, got "
                f"{row!r}: {pair!r}"
            )
        values.append((row, *pair))
    return HeroicSpec(
        map_difficulty_id=map_difficulty_id, access_id=access_id, min_level=min_level, max_level=max_level,
        min_item_level=min_item_level, reset_seconds=reset_seconds, max_players=max_players, message=message,
        encounter_ids=encounters, spawn_mask=spawn_mask, event_spawns=event_spawns, tier=tier,
        tier_values=tuple(values), overrides=_overrides(label, overrides or {}),
        widen_smart_scripts=widen_smart_scripts, no_credit=no_credit_ids,
    )


def _overrides(label: str, overrides: dict) -> tuple[tuple[int, tuple], ...]:
    if not isinstance(overrides, dict):
        raise ValueError(f"{label}: overrides must be a dict of entry -> dict(...), got {overrides!r}")
    out = []
    for entry, values in sorted(overrides.items()):
        where = f"{label}: overrides[{entry!r}]"
        if not _plain_int(entry) or entry <= 0:
            raise ValueError(f"{where}: the key must be a creature entry")
        if not isinstance(values, dict) or not values:
            raise ValueError(f"{where}: must be a non-empty dict of {OVERRIDE_KEYS}")
        unknown = sorted(set(values) - set(OVERRIDE_KEYS))
        if unknown:
            raise ValueError(f"{where}: unknown key(s) {unknown} - one of {OVERRIDE_KEYS}")
        for key in ("health", "melee"):
            if key in values and (not isinstance(values[key], (int, float)) or isinstance(values[key], bool)
                                  or values[key] <= 0):
                raise ValueError(f"{where}: {key} must be a positive number, got {values[key]!r}")
        if "tier" in values and values["tier"] not in TIER_ROWS:
            raise ValueError(f"{where}: tier must be one of {TIER_ROWS}, got {values['tier']!r}")
        columns = values.get("columns", {})
        if not isinstance(columns, dict) or not all(isinstance(c, str) for c in columns):
            raise ValueError(f"{where}: columns must be a dict of creature_template column -> value")
        solved = sorted(set(columns) & set(SOLVED_COLUMNS))
        if solved:
            raise ValueError(
                f"{where}: columns {solved} are set by the tier solve (level, exp 0, health and melee modifiers) - "
                f"use health=, melee= or tier= instead"
            )
        pairs = tuple(sorted((k, tuple(sorted(v.items())) if k == "columns" else v) for k, v in values.items()))
        out.append((entry, pairs))
    return tuple(out)


def override_dict(spec: dict) -> dict[int, dict]:
    """`heroic(overrides=...)` back as {entry: {"health": .., "melee": .., "tier": .., "columns": {..}}} from the
    bookkeeping entry's plain-dict heroic."""
    out = {}
    for entry, pairs in spec.get("overrides") or ():
        values = dict(pairs)
        if "columns" in values:
            values["columns"] = dict(values["columns"])
        out[int(entry)] = values
    return out


@dataclass(frozen=True)
class DungeonCreature:
    """One creature of a dungeon (`creature(...)`): identity and how it gets there, never stats."""

    entry: int
    name: str
    role: str
    spawns: int = 0
    summoned_by: tuple[str, ...] = ()
    event: bool = False


def creature(
    entry: int, name: str, role: str, *, spawns: int = 0, summoned_by=(), event: bool = False,
) -> DungeonCreature:
    """A creature of a dungeon's `creatures=` / `extra=` list. `role` is one of `ROLES`; `spawns` how many spawns it
    has on the map (0: summoned or credit only); `summoned_by` free text naming who brings it in ("creature 622 smart
    cast 3605", "C++ boss_x"); `event=True` when every spawn there belongs to a game event (no heroic template unless
    the heroic includes event spawns)."""
    label = f"creature({entry!r}, {name!r})"
    if not _plain_int(entry) or entry <= 0:
        raise ValueError(f"{label}: entry must be a positive int")
    if not isinstance(name, str):
        raise ValueError(f"{label}: name must be a string")
    if role not in ROLES:
        raise ValueError(f"{label}: role must be one of {ROLES}, got {role!r}")
    if not _plain_int(spawns) or spawns < 0:
        raise ValueError(f"{label}: spawns must be an int >= 0")
    if isinstance(summoned_by, str) or not all(isinstance(s, str) for s in summoned_by):
        raise ValueError(f"{label}: summoned_by must be a tuple of strings")
    if not isinstance(event, bool):
        raise ValueError(f"{label}: event must be True or False")
    return DungeonCreature(entry, name, role, spawns, tuple(summoned_by), event)


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


def dungeon(
    map_id: int, name: str, *, heroic: HeroicSpec | None = None, creatures=(), extra=(), roles: dict | None = None,
    skip=(), retired=(),
) -> dict:
    """Declares the dungeon on `map_id` (a Map.dbc id, e.g. 36 Deadmines) named `name`. With `heroic=heroic(...)` it
    emits that difficulty's MapDifficulty row (server overlay and client patch-Z) and its `dungeon_access_template`
    row; without it, nothing (a reference declaration later stages fill in). A map may be declared once.

    generate.py stops (also under `--check`) when the map has no stock MapDifficulty row (not an instance map: wrong
    id?), when a declared (map, difficulty) is already a stock or live MapDifficulty row under another id, when a live
    `dungeon_access_template` row already covers it under another id, and when the stock MapDifficulty.dbc is missing
    from var/extractors/dbc/. The heroic's encounter rows, spawn masks and per-creature rows are built by generate.py
    from live state (lib/dungeon_heroic.py), which has its own ERRORs. Returns the bookkeeping entry.

    `creatures` is the generated creature list (`creature(...)` lines, the `CREATURES` block), `extra` hand-added
    creatures (C++ summons), `roles={entry: role}` hand role corrections of either list, `skip` entries that never get
    a heroic template. An entry may appear once across `creatures` and `extra`.

    `retired` names creatures that shipped with a heroic template (a `heroic_ids.lock` line for this map) and leave
    the heroic entry set on purpose: generate.py reverts their normal row's `difficulty_entry_1` (a guarded UPDATE)
    and stops copying their side rows; the lock line and the heroic row stay. A shipped creature that leaves the set
    without being listed here stops generate.py with an ERROR."""
    caller = f"dungeon({map_id!r}, {name!r})"
    if not _plain_int(map_id) or map_id <= 0:
        raise ValueError(f"{caller}: map_id must be a Map.dbc id (positive int)")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{caller}: name (the dungeon's name) is required")
    if heroic is not None and not isinstance(heroic, HeroicSpec):
        raise ValueError(f"{caller}: heroic must come from heroic(...), got {heroic!r}")
    listed: dict[int, dict] = {}
    for source, group in (("extracted", creatures), ("extra", extra)):
        for item in group:
            if not isinstance(item, DungeonCreature):
                raise ValueError(f"{caller}: {source} creatures must come from creature(...), got {item!r}")
            if item.entry in listed:
                raise ValueError(f"{caller}: creature {item.entry} is listed twice (creatures= and extra= together)")
            listed[item.entry] = {**asdict(item), "source": source}
    for entry, role in sorted((roles or {}).items()):
        if entry not in listed:
            raise ValueError(f"{caller}: roles names creature {entry!r}, which is in neither creatures= nor extra=")
        if role not in ROLES:
            raise ValueError(f"{caller}: roles[{entry}] must be one of {ROLES}, got {role!r}")
        listed[entry]["role"] = role
    skipped = tuple(sorted(set(skip)))
    if not all(_plain_int(e) and e > 0 for e in skipped):
        raise ValueError(f"{caller}: skip must be creature entries, got {skip!r}")
    retired_entries = tuple(sorted(set(retired)))
    if not all(_plain_int(e) and e > 0 for e in retired_entries):
        raise ValueError(f"{caller}: retired must be creature entries, got {retired!r}")
    registry = _registry._require_active()
    # `heroic_entries` (normal creature entry -> heroic entry) is WP-G's: its lock file fills it; lib/dungeon_heroic.py
    # reads it for difficulty_entry_1 and the side-table copies, and does nothing while it is empty.
    entry = {
        "id": map_id, "map_id": map_id, "name": name, "heroic": asdict(heroic) if heroic else None,
        "heroic_entries": {}, "creatures": [listed[e] for e in listed], "skip": skipped,
        "retired": retired_entries,
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


# ---------------------------------------------------------------------------------------------------------------------
# Encounter rows (Scarlet Monastery build FD-SM): new normal DungeonEncounter rows and edits of stock ones. Declared
# here, built by lib/dungeon_encounters.py once the run has the stock file and the live rows (it checks them there).

DIFFICULTY_MAX = 3  # DBCEnums.h Difficulty: 0-1 for a dungeon, 0-3 for a raid
ENCOUNTER_BIT_MAX = 31  # the completed-encounter mask is a uint32 (Map::UpdateEncounterState: 1 << Bit)
ENCOUNTER_NAME_MAX = 100  # dungeonencounter_dbc.Name_Lang_enUS is varchar(100)
CREDIT_KILL_CREATURE = 0  # EncounterCreditType: ENCOUNTER_CREDIT_KILL_CREATURE
CREDIT_CAST_SPELL = 1  # ENCOUNTER_CREDIT_CAST_SPELL (UpdateEncounterState with the spell id, e.g. a fake death)
LFG_DUNGEON_ID_MAX = 0xFFFF  # instance_encounters.lastEncounterDungeon is a smallint unsigned


@dataclass(frozen=True)
class EncounterCredit:
    """What `credit_creature()` / `credit_spell()` return: one `instance_encounters` credit (type and entry)."""

    credit_type: int
    entry: int


def credit_creature(entry: int) -> EncounterCredit:
    """The encounter completes when creature `entry` dies (creditType 0): the engine also marks that creature a
    dungeon boss (`CREATURE_FLAG_EXTRA_DUNGEON_BOSS`). On heroic the heroic copy still reports the normal entry."""
    if not _plain_int(entry) or entry <= 0:
        raise ValueError(f"credit_creature({entry!r}): entry must be a creature entry (positive int)")
    return EncounterCredit(CREDIT_KILL_CREATURE, entry)


def credit_spell(spell_id: int) -> EncounterCredit:
    """The encounter completes when the instance reports spell `spell_id` (creditType 1): a server-side dummy the
    instance script passes to `UpdateEncounterState(ENCOUNTER_CREDIT_CAST_SPELL, spell_id, source)` (or a real cast of
    it), for an encounter no single kill ends (a council, a fake death). Declare the spell in source/ too."""
    if not _plain_int(spell_id) or spell_id <= 0:
        raise ValueError(f"credit_spell({spell_id!r}): spell_id must be a spell id (positive int)")
    return EncounterCredit(CREDIT_CAST_SPELL, spell_id)


def _encounter_common(label: str, *, name, order_index, bit, credit, last_encounter, icon) -> None:
    if name is not None and (not isinstance(name, str) or not name.strip() or len(name) > ENCOUNTER_NAME_MAX):
        raise ValueError(f"{label}: name must be a non-empty string of at most {ENCOUNTER_NAME_MAX} characters "
                         f"(the client's lockout list shows it), got {name!r}")
    if order_index is not None and (not _plain_int(order_index) or not -0x80000000 <= order_index <= 0x7FFFFFFF):
        raise ValueError(f"{label}: order_index must be a signed 32-bit int, got {order_index!r}")
    if bit is not None and (not _plain_int(bit) or not 0 <= bit <= ENCOUNTER_BIT_MAX):
        raise ValueError(f"{label}: bit must be an int in 0..{ENCOUNTER_BIT_MAX} (the completed-encounter mask is "
                         f"32 bits), got {bit!r}")
    if credit is not None and not isinstance(credit, EncounterCredit):
        raise ValueError(f"{label}: credit must come from credit_creature(entry) or credit_spell(spell_id), "
                         f"got {credit!r}")
    if last_encounter is not None and (not _plain_int(last_encounter)
                                       or not 0 <= last_encounter <= LFG_DUNGEON_ID_MAX):
        raise ValueError(f"{label}: last_encounter must be 0 or an LFGDungeons id (the finder entry this kill "
                         f"completes), got {last_encounter!r}")
    if last_encounter and credit is None and label.startswith("dungeon_encounter("):
        raise ValueError(f"{label}: last_encounter needs a credit (it lives on the instance_encounters row)")
    if icon is not None and (not _plain_int(icon) or icon < 0):
        raise ValueError(f"{label}: icon must be a SpellIcon id (int >= 0), got {icon!r}")


def _register_encounter(label: str, entry: dict) -> dict:
    registry = _registry._require_active()
    if any(e["id"] == entry["id"] for e in registry.encounter_declarations):
        raise _registry.DuplicateIdError(f"{label}: DungeonEncounter {entry['id']} is declared twice")
    registry.encounter_declarations.append(entry)
    return entry


def dungeon_encounter(
    encounter_id: int, *, map_id: int, order_index: int, bit: int, name: str, credit: EncounterCredit | None,
    difficulty: int = 0, last_encounter: int = 0, icon: int = 0,
) -> dict:
    """A NEW DungeonEncounter row: one more boss of an instance difficulty's encounter list (server overlay
    `dungeonencounter_dbc`, the same row merged into patch-Z's DungeonEncounter.dbc for the client's lockout list and
    Finder proposal) and the `instance_encounters` row that credits it.

    `encounter_id` comes from source/ids.yaml's `dungeonencounter` block and never moves once shipped. `map_id` /
    `difficulty` (0 normal, 1 heroic; the map needs a MapDifficulty row for it) pick the list; `bit` is the encounter's
    index in the completed mask (unique in the list, 0..31; a rework instance script uses the same number as its boss
    slot); `order_index` its place in the client's list (signed; the stock rows of a 5-man step by 1000, so a boss
    between two stock ones takes a value between theirs). `name` is the enUS name the client shows (other locales
    empty, as on every stock row of a vanilla dungeon); `icon` the SpellIconID (0 on every vanilla row).

    `credit=credit_creature(entry)` (the kill of that creature) or `credit_spell(spell_id)` (the instance reports the
    spell); `credit=None` writes no `instance_encounters` row (the encounter is listed but no kill completes it).
    `last_encounter` is the LFGDungeons id this kill completes (`instance_encounters.lastEncounterDungeon`, 0 = none):
    one final boss per finder entry, checked against the stock and live rows.

    A heroic of the same map (`heroic(encounter_ids=...)`) counts a declared Difficulty 0 row like a stock one: it
    needs one more heroic id and copies the row (bit, order, name, credit) in OrderIndex order. generate.py stops on a
    stock id (use repoint_encounter()), a live row of another map under the id, a bit already held in the list, an
    unknown credit creature, a map without that difficulty and a finder entry that would end twice."""
    label = f"dungeon_encounter({encounter_id!r}, {name!r})"
    if not _plain_int(encounter_id) or encounter_id <= 0:
        raise ValueError(f"{label}: encounter_id must be a DungeonEncounter id (positive int)")
    if not _plain_int(map_id) or map_id <= 0:
        raise ValueError(f"{label}: map_id must be a Map.dbc id (positive int)")
    if not _plain_int(difficulty) or not 0 <= difficulty <= DIFFICULTY_MAX:
        raise ValueError(f"{label}: difficulty must be an int in 0..{DIFFICULTY_MAX}, got {difficulty!r}")
    for key, value in (("name", name), ("order_index", order_index), ("bit", bit)):
        if value is None:
            raise ValueError(f"{label}: {key} is required")
    _encounter_common(label, name=name, order_index=order_index, bit=bit, credit=credit,
                      last_encounter=last_encounter, icon=icon)
    _check_block(label, "dungeonencounter", encounter_id)
    return _register_encounter(label, {
        "id": encounter_id, "kind": "new", "map_id": map_id, "difficulty": difficulty, "order_index": order_index,
        "bit": bit, "name": name, "credit": (credit.credit_type, credit.entry) if credit else None,
        "last_encounter": last_encounter, "icon": icon,
    })


def repoint_encounter(
    encounter_id: int, *, name: str | None = None, order_index: int | None = None, bit: int | None = None,
    credit: EncounterCredit | None = None, last_encounter: int | None = None, icon: int | None = None,
) -> dict:
    """An edit of a STOCK DungeonEncounter row: the encounter keeps its id, map and difficulty (saves, the client's
    lockout bits and any heroic copy stay valid) but becomes another fight - Scarlet Monastery's 449 (High Inquisitor
    Fairbanks, bit 5, OrderIndex 5000) turns into the Last Stand. Each argument given replaces that column: `name`
    (enUS; the other locales are cleared, so a localized client shows no stale name), `order_index`, `bit`, `icon`.

    `credit` replaces the stock `instance_encounters` credit (type and entry); `last_encounter` its
    `lastEncounterDungeon`. Not given: the live credit row stays as it is (a stock credit cannot be dropped here,
    generate.py never deletes a stock key: a hand SQL DELETE plus `heroic(no_credit=...)` does that).

    The row goes to the overlay and patch-Z over the stock one, the credit to `instance_encounters`; a declared heroic
    of the map copies the edited row. Dropping the declaration prunes the overlay row (the server falls back to the
    stock row; the client keeps the shipped name until the next patch) but leaves the credit edit live."""
    label = f"repoint_encounter({encounter_id!r})"
    if not _plain_int(encounter_id) or encounter_id <= 0:
        raise ValueError(f"{label}: encounter_id must be a stock DungeonEncounter id (positive int)")
    _encounter_common(label, name=name, order_index=order_index, bit=bit, credit=credit,
                      last_encounter=last_encounter, icon=icon)
    if all(v is None for v in (name, order_index, bit, credit, last_encounter, icon)):
        raise ValueError(f"{label}: nothing to change - pass at least one of name, order_index, bit, credit, "
                         f"last_encounter, icon")
    return _register_encounter(label, {
        "id": encounter_id, "kind": "repoint", "name": name, "order_index": order_index, "bit": bit,
        "credit": (credit.credit_type, credit.entry) if credit else None, "last_encounter": last_encounter,
        "icon": icon,
    })
