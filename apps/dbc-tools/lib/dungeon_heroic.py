"""
generate.py's side of a declared heroic's E2 rows (dungeon difficulties E2, WP-T2): everything `dungeon(...,
heroic=heroic(...))` emits beyond T1's MapDifficulty and `dungeon_access_template` rows, built from live state after
the source is loaded. `expand()` is the one entry point; generate.py calls it once per run, before the SPELL_TABLES
render and before `--check` returns, so both paths see the same rows and ERRORs.

What it derives, per declared heroic (map M):

1. **Encounters** (`heroic(encounter_ids=...)`): the map's normal encounters (stock DungeonEncounter.dbc, then the
   live `dungeonencounter_dbc` overlay) in the stock file's order (OrderIndex), each copied to one declared id with
   Difficulty 1 and the normal row's Bit, OrderIndex, names and icon; plus the `instance_encounters` row with the
   normal row's credit type and entry and `lastEncounterDungeon` 0. The kill credit stays the **normal** entry: a
   heroic creature still reports `GetEntry()` = the normal entry (`Creature::InitEntry`), which `KillRewarder` and
   `Map::UpdateEncounterState` compare against `creditEntry`. `instance_encounters` has no difficulty column: the
   loader files each row under its DungeonEncounter row's (MapID, Difficulty) (`ObjectMgr::LoadInstanceEncounters`).
   Rows go to `dungeon_encounters` / `instance_encounters` (SPELL_TABLES) and the client half into patch-Z.
2. **spawnMask** (`heroic(spawn_mask=True)`, the default): every `creature` and `gameobject` spawn on M whose live
   spawnMask lacks the heroic bit gets one targeted `UPDATE ... SET spawnMask = spawnMask | 2 WHERE id IN (...) AND
   guid IN (...)` per table (the SQL linter's spawn shape). Diffed against the replayed live spawns
   (`lib/spawn_state.py`), so a map already at mask 3 (Deadmines after E1's WP-1D) emits nothing. Spawns a game event
   owns stay normal-only unless `event_spawns=True`. Never reverted: dropping the heroic leaves the masks.
3. **Heroic creature templates** (WP-G, `lib/heroic_templates.py`): for a heroic whose declaration carries a creature
   list (`dungeon(creatures=...)`), one level 60 `creature_template` row per creature of its entry set (ids from the
   append-only `source/world/heroic_ids.lock`), appended to `creature_templates` before step 4 reads them, and the
   normal -> heroic map written to `entry["heroic_entries"]`. Also the dungeon's creature lints and the SmartAI
   widening UPDATEs (normal-only rows also run on heroic).
4. **Per creature**: `entry["heroic_entries"]` on the `Registry.dungeons` bookkeeping entry, the normal -> heroic
   entry map (step 3, or a test's hand-written map). For each pair:
   - `difficulty_entry_1` on the normal row, as a one-column `creature_template_columns()`-style edit (joins
     `creature_template_edits`, so it renders as a column-limited UPDATE after the heroic templates' upserts and is
     diffed against the replayed live row). Never touches another column of a normal row.
   - an ERROR when a heroic entry ends with no `creature_template_model` row (the engine refuses to load it).
   - copies of the normal entry's rows in every side table the engine reads by the **heroic** entry
     (`SIDE_TABLES`): `creature_template_addon`, `_spell`, `_model`, `_resistance`, `_movement` and
     `creature_onkill_reputation`. A table in which the run already declares a row for the heroic entry is not copied
     for that entry (the declaration owns it).

ERRORs (generate.py stops, also under `--check`): every engine refusal `ObjectMgr::CheckCreatureTemplate` can decide
from the normal row and the entry map, plus the encounter and spawn problems below; WARNINGs for what still loads but
is probably not meant (a heroic encounter with no kill credit, linked respawn partners split across difficulties, a
pool half on heroic).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path

from . import dbcfmt, heroic_templates, spawn_state, spell_tables, sql_dump, state, trainer_state

DIFFICULTY_NORMAL = 0
DIFFICULTY_HEROIC = 1
HEROIC_SPAWN_BIT = 1 << DIFFICULTY_HEROIC  # a spawn is filed under each bit of its mask (ObjectMgr::AddCreatureToGrid)
DIFFICULTY_ENTRY_COLUMNS = ("difficulty_entry_1", "difficulty_entry_2", "difficulty_entry_3")
# linked_respawn.linkType (ObjectMgr::LoadLinkedRespawn): which spawn table the slave (guid) and master (linkedGuid)
# live in.
LINK_TABLES = {0: ("creature", "creature"), 1: ("creature", "gameobject"), 2: ("gameobject", "gameobject"),
               3: ("gameobject", "creature")}
WRAP_WIDTH = 120


@dataclass(frozen=True)
class SideTable:
    """A table keyed on a creature entry that the engine reads by the heroic entry (`GetCreatureTemplate()`'s entry):
    its rows for a normal entry are copied to the heroic entry."""

    name: str
    entry_column: str
    key_columns: tuple[str, ...]
    registry_key: str

    @property
    def columns(self) -> tuple[str, ...]:
        if self.name == "creature_template_model":
            return spell_tables.CREATURE_TEMPLATE_MODEL_COLUMNS
        return next(spec.columns for spec in spell_tables.SPELL_TABLES if spec.name == self.name)


SIDE_TABLES = (
    SideTable("creature_template_addon", "entry", ("entry",), "heroic_template_addons"),
    SideTable("creature_template_spell", "CreatureID", ("CreatureID", "Index"), "creature_template_spells"),
    SideTable("creature_template_model", "CreatureID", ("CreatureID", "Idx"), "creature_template_models"),
    SideTable("creature_template_resistance", "CreatureID", ("CreatureID", "School"), "heroic_template_resistances"),
    SideTable("creature_template_movement", "CreatureId", ("CreatureId",), "heroic_template_movements"),
    SideTable("creature_onkill_reputation", "creature_id", ("creature_id",), "heroic_onkill_reputations"),
)

# Marks a row this module appended to a shared list (creature_template_spells / _models / _edits), so a second
# expand() over the same dict replaces its own rows instead of doubling them.
DERIVED = "_dungeon_heroic"


@dataclass
class LiveWorld:
    """The live state `expand()` reads. `load_live_world()` builds it for a real run; tests build it by hand."""

    creature_templates: dict[int, dict]
    side_rows: dict[str, list[dict]] = field(default_factory=dict)
    stock_encounters: dict[int, dict] | None = None  # None: DungeonEncounter.dbc missing
    live_encounters: list[dict] = field(default_factory=list)
    instance_encounters: dict[int, dict] = field(default_factory=dict)
    heroic_maps: set[int] = field(default_factory=set)  # maps with a stock or live Difficulty 1 MapDifficulty row
    spawns: dict[str, dict[int, dict]] = field(default_factory=dict)  # "creature" / "gameobject" -> guid -> row
    linked_respawn: list[dict] = field(default_factory=list)
    pools: dict[str, dict[int, int]] = field(default_factory=dict)  # spawn table -> guid -> pool_entry
    event_guids: dict[str, set[int]] = field(default_factory=dict)  # spawn table -> guids a game event owns
    class_level_stats: dict[tuple[int, int], dict] = field(default_factory=dict)  # (level, class) -> row
    smart_scripts: list[dict] = field(default_factory=list)
    spell_difficulty: dict[int, dict] | None = None  # SpellDifficulty rows by ID (stock + overlay); None: file missing


@dataclass
class Expansion:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    spawn_blocks: list[str] = field(default_factory=list)
    smart_blocks: list[str] = field(default_factory=list)  # SmartAI widening UPDATEs (heroic_templates)
    retire_blocks: list[str] = field(default_factory=list)  # retired creatures' difficulty_entry_1 reverts
    lock_appended: list[str] = field(default_factory=list)  # new heroic_ids.lock lines (a full run writes them)
    lock_text: str = ""  # the lock file with them appended
    heroic_reports: list = field(default_factory=list)  # heroic_templates.HeroicReport per generated row
    # map -> spawn table -> guid -> template entry of every spawn on a declared heroic's map (generate.py --scope: a
    # dungeon scope owns the spawns and SmartAI of its map, lib/scope.py)
    map_spawns: dict[int, dict[str, dict[int, int]]] = field(default_factory=dict)


def _int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _signed(value) -> int:
    value = _int(value)
    return value - 0x100000000 if value >= 0x80000000 else value


def _heroics(dsl_classes: dict) -> list[dict]:
    return sorted((e for e in dsl_classes.get("dungeons", []) if e.get("heroic")), key=lambda e: e["map_id"])


def needs_live_world(dsl_classes: dict) -> bool:
    return bool(_heroics(dsl_classes))


def heroic_entry_maps(dsl_classes: dict) -> dict[int, dict[int, int]]:
    """map id -> {normal entry: heroic entry}, from each heroic dungeon's `heroic_entries` (WP-G's lock file)."""
    return {
        e["map_id"]: {int(n): int(h) for n, h in (e.get("heroic_entries") or {}).items()}
        for e in _heroics(dsl_classes) if e.get("heroic_entries")
    }


# ---------------------------------------------------------------------------------------------------------------------
# Live state

def _schema_defaults(table: str) -> dict:
    path = trainer_state.BASE_SQL_DIR / f"{table}.sql"
    return sql_dump.parse_create_table_defaults(path, table) if path.is_file() else {}


def load_live_world(
    creature_templates: dict[int, dict], spell_table_index, base_dir: Path = state.BASE_DBC_DIR,
) -> LiveWorld:
    """Every input `expand()` needs, replayed from the SQL on disk (base dump, migrations, frozen phase 0, pending,
    module SQL) and the stock client files; no database connection. `creature_templates` is generate.py's replayed
    `creature_template` (entry -> row); `spell_table_index` its SPELL_TABLES index (live MapDifficulty and
    DungeonEncounter overlay rows)."""
    side_rows = {}
    for side in SIDE_TABLES:
        side_rows[side.name] = trainer_state.load_replayed_table_rows(side.name, side.columns, side.key_columns)
    encounter_path = base_dir / dbcfmt.DUNGEONENCOUNTER.dbc_filename
    stock_encounters = (
        {int(r["ID"]): r for r in state.read_dbc_cached(encounter_path, dbcfmt.DUNGEONENCOUNTER)}
        if encounter_path.is_file() else None
    )
    instance = trainer_state.load_replayed_table_rows(
        "instance_encounters", spell_tables.INSTANCE_ENCOUNTERS_COLUMNS, ("entry",),
    )
    heroic_maps: set[int] = set()
    map_difficulty_path = base_dir / dbcfmt.MAPDIFFICULTY.dbc_filename
    stock_md = state.read_dbc_cached(map_difficulty_path, dbcfmt.MAPDIFFICULTY) if map_difficulty_path.is_file() else []
    for row in [*stock_md, *spell_table_index.live_rows("mapdifficulty_dbc")]:
        if _int(row.get("Difficulty")) == DIFFICULTY_HEROIC:
            heroic_maps.add(_int(row.get("MapID")))
    spawns = {table: spawn_state.load_spawn_state(table).by_guid() for table in spawn_state.SPAWN_TABLES}
    linked = trainer_state.load_replayed_table_rows(
        "linked_respawn", ("guid", "linkedGuid", "linkType"), ("guid", "linkType"),
    )
    pools, events = {}, {}
    for table in spawn_state.SPAWN_TABLES:
        pool_rows = trainer_state.load_replayed_table_rows(
            f"pool_{table}", ("guid", "pool_entry", "chance", "description"), ("guid",),
        )
        pools[table] = {_int(r.get("guid")): _int(r.get("pool_entry")) for r in pool_rows}
        event_rows = trainer_state.load_replayed_table_rows(
            f"game_event_{table}", ("eventEntry", "guid"), ("guid", "eventEntry"),
        )
        events[table] = {_int(r.get("guid")) for r in event_rows}
    stats_path = trainer_state.BASE_SQL_DIR / "creature_classlevelstats.sql"
    stats = trainer_state.load_replayed_table_rows(
        "creature_classlevelstats", tuple(sql_dump.parse_create_table_columns(stats_path, "creature_classlevelstats")),
        ("level", "class"),
    )
    smart_path = trainer_state.BASE_SQL_DIR / "smart_scripts.sql"
    smart = trainer_state.load_replayed_table_rows(
        "smart_scripts", tuple(sql_dump.parse_create_table_columns(smart_path, "smart_scripts")),
        ("entryorguid", "source_type", "id", "link"),
    )
    difficulty_path = base_dir / dbcfmt.SPELLDIFFICULTY.dbc_filename
    spell_difficulty = None
    if difficulty_path.is_file():
        spell_difficulty = {int(r["ID"]): r for r in state.read_dbc_cached(difficulty_path, dbcfmt.SPELLDIFFICULTY)}
        for row in trainer_state.load_replayed_table_rows(
            "spelldifficulty_dbc", dbcfmt.SPELLDIFFICULTY.columns, ("ID",),
        ):
            spell_difficulty[_int(row.get("ID"))] = row
    return LiveWorld(
        creature_templates=creature_templates, side_rows=side_rows, stock_encounters=stock_encounters,
        live_encounters=spell_table_index.live_rows("dungeonencounter_dbc"),
        instance_encounters={_int(r.get("entry")): r for r in instance}, heroic_maps=heroic_maps, spawns=spawns,
        linked_respawn=linked, pools=pools, event_guids=events,
        class_level_stats={(_int(r.get("level")), _int(r.get("class"))): r for r in stats}, smart_scripts=smart,
        spell_difficulty=spell_difficulty,
    )


# ---------------------------------------------------------------------------------------------------------------------
# 1. Encounters

def normal_encounters(map_id: int, live: LiveWorld, skip_ids: set[int] = frozenset()) -> list[dict]:
    """The map's Difficulty 0 encounter rows (stock file, then the live overlay by ID), in the stock file's order."""
    merged = dict(live.stock_encounters or {})
    for row in live.live_encounters:
        merged[_int(row.get("ID"))] = row
    rows = [
        r for i, r in merged.items()
        if i not in skip_ids and _int(r.get("MapID")) == map_id and _int(r.get("Difficulty")) == DIFFICULTY_NORMAL
    ]
    return sorted(rows, key=lambda r: (_signed(r.get("OrderIndex")), _int(r.get("Bit")), _int(r.get("ID"))))


def _encounter_rows(entry: dict, live: LiveWorld, all_declared_ids: set[int], out: Expansion):
    spec, map_id, name = entry["heroic"], entry["map_id"], entry["name"]
    ids = list(spec.get("encounter_ids") or ())
    if not ids:
        return [], []
    label = f"dungeon({map_id}, {name!r}) heroic encounter_ids"
    if live.stock_encounters is None:
        out.errors.append(
            f"{label}: no stock {dbcfmt.DUNGEONENCOUNTER.dbc_filename} at "
            f"{state.BASE_DBC_DIR / dbcfmt.DUNGEONENCOUNTER.dbc_filename} - copy it from the worldserver's DBC "
            f"directory (ac-worldserver:/azerothcore/env/dist/data/dbc/) into that directory; the normal boss rows and "
            f"the client patch both come from it"
        )
        return [], []
    errors_before = len(out.errors)
    for encounter_id in ids:
        if encounter_id in live.stock_encounters:
            out.errors.append(f"{label}: {encounter_id} is a stock DungeonEncounter id")
    for row in live.live_encounters:
        row_id = _int(row.get("ID"))
        if row_id in ids and _int(row.get("MapID")) != map_id:
            out.errors.append(
                f"{label}: live dungeonencounter_dbc row {row_id} belongs to map {_int(row.get('MapID'))} "
                f"(module or migration SQL) - pick other ids"
            )
    held = sorted(
        _int(r.get("ID")) for r in [*live.stock_encounters.values(), *live.live_encounters]
        if _int(r.get("MapID")) == map_id and _int(r.get("Difficulty")) == DIFFICULTY_HEROIC
        and _int(r.get("ID")) not in all_declared_ids
    )
    if held:
        out.errors.append(f"{label}: the map already has heroic encounter rows {held} (stock or live)")
    normals = normal_encounters(map_id, live, all_declared_ids)
    if len(normals) != len(ids):
        listed = ", ".join(f"{_int(r['ID'])} {r.get('Name_Lang_enUS')!r}" for r in normals)
        out.errors.append(
            f"{label}: {len(ids)} id(s) for {len(normals)} normal encounter(s) ({listed or 'none'}) - one id per "
            f"normal encounter, in this order"
        )
    if len(out.errors) > errors_before:
        return [], []
    dbc_rows, credit_rows = [], []
    for encounter_id, normal in zip(ids, normals):
        row = {column: normal.get(column) for column in dbcfmt.DUNGEONENCOUNTER.columns}
        row.update(ID=encounter_id, Difficulty=DIFFICULTY_HEROIC, OrderIndex=_signed(normal.get("OrderIndex")))
        dbc_rows.append(row)
        credit = live.instance_encounters.get(_int(normal["ID"]))
        if credit is None:
            out.warnings.append(
                f"{label}: normal encounter {_int(normal['ID'])} ({normal.get('Name_Lang_enUS')!r}) has no "
                f"instance_encounters row, so heroic encounter {encounter_id} gets no kill credit either"
            )
            continue
        comment = credit.get("comment") or normal.get("Name_Lang_enUS") or ""
        credit_rows.append({
            "entry": encounter_id, "creditType": _int(credit.get("creditType")),
            "creditEntry": _int(credit.get("creditEntry")), "lastEncounterDungeon": 0, "comment": f"{comment} - Heroic",
        })
    return dbc_rows, credit_rows


def client_encounter_rows(declared: list[dict]) -> dict[int, dict]:
    """Derived `dungeon_encounters` rows as DungeonEncounter.dbc rows, keyed by ID, for the patch-Z merge."""
    return {int(r["ID"]): {c: r[c] for c in dbcfmt.DUNGEONENCOUNTER.columns} for r in declared}


# ---------------------------------------------------------------------------------------------------------------------
# 2. spawnMask

def _wrap(values: list[int], indent: str = "    ") -> str:
    lines, line = [], ""
    for text in (str(v) for v in values):
        candidate = f"{line}, {text}" if line else text
        if len(indent) + len(candidate) + 1 > WRAP_WIDTH and line:
            lines.append(indent + line + ",")
            line = text
        else:
            line = candidate
    lines.append(indent + line)
    return "\n".join(lines)


def render_spawn_mask_update(table: str, label: str, spawns: list[dict]) -> str:
    """`UPDATE <table> SET spawnMask = spawnMask | 2 WHERE id IN (...) AND guid IN (...)` for `spawns` (rows with
    `guid` and `id`), behind a comment line; "" for none."""
    if not spawns:
        return ""
    entries = sorted({spawn_state.spawn_entry(r) for r in spawns})
    guids = sorted({_int(r["guid"]) for r in spawns})
    return (
        f"-- {label}: {len(guids)} {table} spawn(s) also spawn on heroic (spawnMask bit {HEROIC_SPAWN_BIT})\n"
        f"UPDATE `{table}` SET `spawnMask` = `spawnMask` | {HEROIC_SPAWN_BIT} WHERE `id` IN (\n{_wrap(entries)}\n"
        f") AND `guid` IN (\n{_wrap(guids)}\n);"
    )


def _spawn_masks(entry: dict, live: LiveWorld, out: Expansion) -> dict[str, dict[int, int]]:
    """Emits the map's spawnMask UPDATEs into `out` and returns the planned masks of the map's spawns."""
    spec, map_id, name = entry["heroic"], entry["map_id"], entry["name"]
    label = f"{name} (map {map_id}) heroic"
    planned: dict[str, dict[int, int]] = {}
    summary = []
    for table in spawn_state.SPAWN_TABLES:
        rows = [r for r in live.spawns.get(table, {}).values() if _int(r.get("map")) == map_id]
        out.map_spawns.setdefault(map_id, {})[table] = {_int(r["guid"]): spawn_state.spawn_entry(r) for r in rows}
        planned[table] = {_int(r["guid"]): spawn_state.spawn_mask(r) for r in rows}
        if not spec.get("spawn_mask"):
            continue
        events = live.event_guids.get(table, set())
        excluded = [r for r in rows if _int(r["guid"]) in events and not spec.get("event_spawns")]
        wanted = [r for r in rows if r not in excluded]
        todo = [r for r in wanted if not spawn_state.spawn_mask(r) & HEROIC_SPAWN_BIT]
        for r in todo:
            planned[table][_int(r["guid"])] |= HEROIC_SPAWN_BIT
        block = render_spawn_mask_update(table, label, todo)
        if block:
            out.spawn_blocks.append(block)
        summary.append(
            f"{len(todo)} of {len(rows)} {table} spawn(s) to set"
            + (f", {len(excluded)} game event spawn(s) left normal-only" if excluded else "")
        )
    if spec.get("spawn_mask") and not any(planned.values()):
        out.errors.append(f"dungeon({map_id}, {name!r}) heroic spawn_mask: no creature or gameobject spawn on the map")
    if summary:
        out.notes.append(f"dungeons: {label} spawnMask - " + "; ".join(summary))
    return planned


def _spawn_lints(entry: dict, planned: dict[str, dict[int, int]], live: LiveWorld, out: Expansion) -> None:
    map_id, name = entry["map_id"], entry["name"]
    label = f"dungeon({map_id}, {name!r}) heroic"

    def mask(table: str, guid: int) -> int | None:
        if guid in planned.get(table, {}):
            return planned[table][guid]
        row = live.spawns.get(table, {}).get(guid)
        return None if row is None else spawn_state.spawn_mask(row)

    for link in live.linked_respawn:
        tables = LINK_TABLES.get(_int(link.get("linkType")))
        if tables is None:
            continue
        slave, master = _int(link.get("guid")), _int(link.get("linkedGuid"))
        if slave not in planned.get(tables[0], {}) and master not in planned.get(tables[1], {}):
            continue
        slave_mask, master_mask = mask(tables[0], slave), mask(tables[1], master)
        if slave_mask is None or master_mask is None:
            continue  # a missing partner: the engine already drops the link today, not this declaration's doing
        what = f"linked_respawn {tables[0]} {slave} -> {tables[1]} {master} (linkType {_int(link.get('linkType'))})"
        if not slave_mask & master_mask:
            out.errors.append(f"{label}: {what}: masks {slave_mask} and {master_mask} no longer overlap - the engine "
                              f"drops the link (ObjectMgr::LoadLinkedRespawn)")
        elif bool(slave_mask & HEROIC_SPAWN_BIT) != bool(master_mask & HEROIC_SPAWN_BIT):
            out.warnings.append(f"{label}: {what}: only one of the two spawns is on heroic (masks {slave_mask} and "
                                f"{master_mask}), so on heroic the respawn link points at nothing")
    for table in spawn_state.SPAWN_TABLES:
        by_pool: dict[int, set[bool]] = {}
        for guid, pool in live.pools.get(table, {}).items():
            if guid in planned.get(table, {}):
                by_pool.setdefault(pool, set()).add(bool(planned[table][guid] & HEROIC_SPAWN_BIT))
        for pool in sorted(p for p, bits in by_pool.items() if len(bits) > 1):
            out.warnings.append(f"{label}: pool {pool} has {table} spawns both on and off heroic - the pool spawns "
                                f"from fewer members there (PoolMgr checks each member's mask)")
        if by_pool:
            out.notes.append(f"dungeons: {name} (map {map_id}) heroic: {len(by_pool)} {table} pool(s) on the map, "
                             f"members' masks checked")


# ---------------------------------------------------------------------------------------------------------------------
# 3. Per creature: difficulty_entry_1 and the side-table copies

def _difficulty_entry_errors(
    entry_maps: dict[int, dict[int, int]], live: LiveWorld, declared_full: dict[int, dict],
    declared_heroic_maps: set[int],
) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    owners: dict[int, tuple[int, int]] = {}  # normal -> (map, heroic)
    heroic_owner: dict[int, tuple[int, int]] = {}  # heroic -> (map, normal)
    for map_id, mapping in sorted(entry_maps.items()):
        for normal, heroic_entry in sorted(mapping.items()):
            if normal in owners and owners[normal][1] != heroic_entry:
                errors.append(f"creature {normal}: dungeons {owners[normal][0]} and {map_id} map it to heroic "
                              f"{owners[normal][1]} and {heroic_entry} - one difficulty_entry_1 per creature")
            owners.setdefault(normal, (map_id, heroic_entry))
            if heroic_entry in heroic_owner and heroic_owner[heroic_entry][1] != normal:
                errors.append(f"creature {heroic_entry}: heroic entry of both {heroic_owner[heroic_entry][1]} and "
                              f"{normal} - the engine refuses a shared difficulty entry")
            heroic_owner.setdefault(heroic_entry, (map_id, normal))
    pointed_at: dict[int, list[tuple[int, str]]] = {}
    for entry_id, row in live.creature_templates.items():
        for column in DIFFICULTY_ENTRY_COLUMNS:
            target = _int(row.get(column))
            if target:
                pointed_at.setdefault(target, []).append((entry_id, column))
    spawned_on: dict[int, set[int]] = {}
    for row in live.spawns.get("creature", {}).values():
        spawned_on.setdefault(spawn_state.spawn_entry(row), set()).add(_int(row.get("map")))
    for normal, (map_id, heroic_entry) in sorted(owners.items()):
        label = f"dungeon({map_id}) creature {normal} -> heroic {heroic_entry}"
        row = live.creature_templates.get(normal)
        if row is None:
            errors.append(f"{label}: no live creature_template row {normal}")
            continue
        if heroic_entry == normal:
            errors.append(f"{label}: a creature cannot be its own difficulty entry")
            continue
        heroic_row = declared_full.get(heroic_entry) or live.creature_templates.get(heroic_entry)
        if heroic_row is None:
            errors.append(f"{label}: heroic entry {heroic_entry} is neither declared this run nor live - "
                          f"difficulty_entry_1 would point at nothing")
        current = _int(row.get("difficulty_entry_1"))
        if current and current != heroic_entry:
            errors.append(f"{label}: the normal row already has difficulty_entry_1 = {current}")
        others = [(e, c) for e, c in pointed_at.get(normal, []) if e != normal]
        if others:
            errors.append(f"{label}: {normal} is itself the {others[0][1]} of creature {others[0][0]}, and a "
                          f"difficulty entry cannot have difficulty entries")
        shared = [(e, c) for e, c in pointed_at.get(heroic_entry, []) if e != normal]
        if shared:
            errors.append(f"{label}: {heroic_entry} is already the {shared[0][1]} of creature {shared[0][0]}")
        if heroic_row is not None and any(_int(heroic_row.get(c)) for c in DIFFICULTY_ENTRY_COLUMNS):
            errors.append(f"{label}: the heroic row {heroic_entry} has difficulty entries of its own")
        if normal in declared_full and _int(declared_full[normal].get("difficulty_entry_1")) != heroic_entry:
            errors.append(f"{label}: creature_template({normal}) declares the full row - set difficulty_entry_1 "
                          f"there instead of a one-column edit")
        for other_map in sorted(spawned_on.get(normal, set()) - {map_id}):
            if other_map in declared_heroic_maps:
                if normal not in entry_maps.get(other_map, {}):
                    warnings.append(f"{label}: {normal} also spawns on map {other_map}, whose declared heroic will "
                                    f"use {heroic_entry} for it as well")
            elif other_map in live.heroic_maps:
                errors.append(f"{label}: {normal} also spawns on map {other_map}, which has a stock or live "
                              f"difficulty 1 row: its difficulty 1 would switch to {heroic_entry} too")
    return errors, warnings


def _difficulty_entry_edits(dsl_classes: dict, entry_maps: dict[int, dict[int, int]]) -> list[str]:
    """Adds `difficulty_entry_1` to each normal entry's `creature_template_edits` row (a new derived row, or the
    column joins a `creature_template_columns()` edit of the same entry). Returns the ERRORs of a clash with such an
    edit that names the column itself."""
    errors = []
    edits = dsl_classes.setdefault("creature_template_edits", [])
    by_entry = {int(r["entry"]): r for r in edits}
    full = {int(r["entry"]) for r in dsl_classes.get("creature_templates", []) if not r.get(DERIVED)}
    for mapping in entry_maps.values():
        for normal, heroic_entry in sorted(mapping.items()):
            if normal in full:
                continue  # a creature_template() row owns the column (checked by _difficulty_entry_errors)
            row = by_entry.get(normal)
            if row is None:
                row = {"entry": normal, "id": normal, "_update_columns": (), DERIVED: True}
                edits.append(row)
                by_entry[normal] = row
            elif "difficulty_entry_1" in row["_update_columns"]:
                ours = row.get(DERIVED) or row.get("_difficulty_from_heroic")  # a second mapping: already an ERROR
                if not ours and _int(row.get("difficulty_entry_1")) != heroic_entry:
                    errors.append(f"creature {normal}: creature_template_columns() declares difficulty_entry_1 = "
                                  f"{row.get('difficulty_entry_1')!r} but its heroic entry is {heroic_entry}")
                continue
            elif not row.get(DERIVED):
                row["_difficulty_from_heroic"] = True
            row["difficulty_entry_1"] = heroic_entry
            if "difficulty_entry_1" not in row["_update_columns"]:
                row["_update_columns"] = (*row["_update_columns"], "difficulty_entry_1")
    return errors


def side_table_copies(
    entry_maps: dict[int, dict[int, int]], live: LiveWorld, declared: dict[str, list[dict]],
) -> dict[str, list[dict]]:
    """registry key -> the heroic copies of every normal entry's rows in `SIDE_TABLES`. Skips a (table, heroic entry)
    the run already declares a row for (`declared`, the run's own non-derived rows)."""
    out: dict[str, list[dict]] = {side.registry_key: [] for side in SIDE_TABLES}
    pairs = sorted({(n, h) for mapping in entry_maps.values() for n, h in mapping.items()})
    for side in SIDE_TABLES:
        defaults = _schema_defaults(side.name)
        own_rows = [r for r in declared.get(side.registry_key, []) if not r.get(DERIVED)]
        owned = {_int(r.get(side.entry_column)) for r in own_rows}
        by_entry: dict[int, list[dict]] = {}
        for row in live.side_rows.get(side.name, []):
            by_entry.setdefault(_int(row.get(side.entry_column)), []).append(row)
        # The run's own rows of a normal entry (a boss-kit add's creature_model() / creature_spell()) are what the run
        # writes: each replaces the replayed row with its key, or joins them (a creature new this run has none).
        for row in own_rows:
            rows = by_entry.setdefault(_int(row.get(side.entry_column)), [])
            key = tuple(_int(row.get(c)) for c in side.key_columns)
            rows[:] = [r for r in rows if tuple(_int(r.get(c)) for c in side.key_columns) != key] + [row]
        for normal, heroic_entry in pairs:
            if heroic_entry in owned:
                continue
            for row in sorted(by_entry.get(normal, []), key=lambda r: tuple(_int(r.get(c)) for c in side.key_columns)):
                copy = {c: row[c] if c in row else defaults.get(c) for c in side.columns}
                copy[side.entry_column] = heroic_entry
                copy["id"] = ":".join(str(copy[c]) for c in side.key_columns)
                copy[DERIVED] = True
                out[side.registry_key].append(copy)
    return out


def _model_errors(entry_maps: dict[int, dict[int, int]], dsl_classes: dict) -> list[str]:
    """ERRORs for a heroic entry left with no `creature_template_model` row (copied or declared):
    `Creature::InitEntry` refuses to load such a creature, so every heroic spawn of it is empty."""
    with_models = {_int(r.get("CreatureID")) for r in dsl_classes.get("creature_template_models", [])}
    errors = []
    for map_id, mapping in sorted(entry_maps.items()):
        for normal, heroic_entry in sorted(mapping.items()):
            if heroic_entry not in with_models:
                errors.append(f"dungeon({map_id}) creature {normal} -> heroic {heroic_entry}: no "
                              f"creature_template_model row for the heroic entry (the normal entry has none to copy) "
                              f"- Creature::InitEntry refuses to load it, so its heroic spawns are empty")
    return errors


# ---------------------------------------------------------------------------------------------------------------------
# The entry point

def with_declared_templates(live: LiveWorld, dsl_classes: dict) -> LiveWorld:
    """`live` with the run's own full `creature_template()` rows (source/npcs, source/classes) on top of the replayed
    creature_template: a creature declared this run (a boss-kit add listed in a dungeon's `extra=`) gets its heroic
    template, difficulty link and side-table copies in the same run, instead of only after its upsert reached the SQL
    on disk. A declared row replaces the replayed one: it is what this run writes. Derived (heroic) rows are left
    out."""
    declared = {int(r["entry"]): r for r in dsl_classes.get("creature_templates", []) if not r.get(DERIVED)}
    if not declared:
        return live
    return replace(live, creature_templates={**live.creature_templates, **declared})


def _clear_derived(dsl_classes: dict) -> None:
    for key in ("dungeon_encounters", "instance_encounters", "creature_templates",
                *(side.registry_key for side in SIDE_TABLES)):
        dsl_classes[key] = [r for r in dsl_classes.get(key, []) if not r.get(DERIVED)]
    edits = []
    for row in dsl_classes.get("creature_template_edits", []):
        if row.get(DERIVED):
            continue
        if "difficulty_entry_1" in row.get("_update_columns", ()) and row.get("_difficulty_from_heroic"):
            row = {k: v for k, v in row.items() if k not in ("difficulty_entry_1", "_difficulty_from_heroic")}
            row["_update_columns"] = tuple(c for c in row["_update_columns"] if c != "difficulty_entry_1")
        edits.append(row)
    dsl_classes["creature_template_edits"] = edits


def _heroic_templates(
    dsl_classes: dict, heroics: list[dict], live: LiveWorld, out: Expansion, ids_cfg: dict | None, lock: str | None,
) -> None:
    """Step 3: the heroic creature templates of every heroic whose declaration carries a creature list."""
    generated = [e for e in heroics if "creatures" in e]
    if not generated:
        return
    if ids_cfg is None:
        from . import source  # noqa: PLC0415 - needs ruamel (the venv); generate.py passes ids_cfg

        ids_cfg = source.load_ids(heroic_templates.TOOL_ROOT / "source" / "ids.yaml")
    if lock is None:
        lock = heroic_templates.LOCK_PATH.read_text() if heroic_templates.LOCK_PATH.is_file() else ""
    block = ids_cfg.get(heroic_templates.LOCK_BLOCK)
    try:
        parsed = heroic_templates.parse_lock(lock, block)
    except heroic_templates.LockError as error:
        out.errors.append(f"dungeons: {error}")
        return
    result = heroic_templates.build(
        generated, live, parsed, block, spell_tables.CREATURE_TEMPLATE_COLUMNS, spell_tables.CREATURE_TEMPLATE_DEFAULTS,
        DERIVED,
    )
    declared = {int(r["entry"]) for r in dsl_classes.get("creature_templates", [])}
    for row in result.rows:
        if int(row["entry"]) in declared:
            out.errors.append(f"creature_template {row['entry']}: declared by creature_template() and generated as "
                              f"a heroic template")
    dsl_classes.setdefault("creature_templates", []).extend(result.rows)
    out.errors += result.errors
    out.warnings += result.warnings
    out.notes += result.notes
    out.smart_blocks += result.smart_blocks
    out.retire_blocks += result.retire_blocks
    out.lock_appended = result.lock_appended
    out.lock_text = heroic_templates.lock_text(parsed, result.lock_appended)
    out.heroic_reports = result.reports
    if result.lock_appended:
        out.notes.append(f"dungeons: {len(result.lock_appended)} new heroic creature id(s) for "
                         f"{heroic_templates.LOCK_PATH.name} (a full run appends them; commit the file)")


def expand(
    dsl_classes: dict, load_live: Callable[[], LiveWorld], ids_cfg: dict | None = None, lock: str | None = None,
) -> Expansion:
    """Fills the derived rows of every declared heroic into `dsl_classes` (replacing any an earlier call added) and
    returns the run's ERRORs, WARNINGs, notes and SQL blocks. `load_live` is only called when a heroic is declared.
    `ids_cfg` is source/ids.yaml (read when None) and `lock` the text of source/world/heroic_ids.lock (read when
    None); both only matter for a heroic whose declaration carries a creature list."""
    out = Expansion()
    for entry in dsl_classes.get("dungeons", []):
        if entry.get("heroic_entries") and not entry.get("heroic"):
            out.errors.append(f"dungeon({entry['map_id']}, {entry['name']!r}): heroic_entries without a heroic")
    heroics = _heroics(dsl_classes)
    _clear_derived(dsl_classes)
    if not heroics:
        return out
    live = with_declared_templates(load_live(), dsl_classes)
    declared_ids: dict[int, int] = {}
    for entry in heroics:
        for encounter_id in entry["heroic"].get("encounter_ids") or ():
            if encounter_id in declared_ids:
                out.errors.append(f"DungeonEncounter id {encounter_id}: declared by dungeons "
                                  f"{declared_ids[encounter_id]} and {entry['map_id']}")
            declared_ids.setdefault(encounter_id, entry["map_id"])
    for entry in heroics:
        dbc_rows, credit_rows = _encounter_rows(entry, live, set(declared_ids), out)
        for row in dbc_rows:
            row[DERIVED] = True
        for row in credit_rows:
            row[DERIVED] = True
        dsl_classes["dungeon_encounters"].extend(dbc_rows)
        dsl_classes["instance_encounters"].extend(credit_rows)
        if dbc_rows:
            out.notes.append(
                f"dungeons: {entry['name']} (map {entry['map_id']}) heroic - {len(dbc_rows)} DungeonEncounter row(s) "
                f"{dbc_rows[0]['ID']}-{dbc_rows[-1]['ID']}, {len(credit_rows)} instance_encounters row(s)"
            )
        planned = _spawn_masks(entry, live, out)
        _spawn_lints(entry, planned, live, out)
    _heroic_templates(dsl_classes, heroics, live, out, ids_cfg, lock)
    entry_maps = heroic_entry_maps(dsl_classes)
    if entry_maps:
        declared_full = {int(r["entry"]): r for r in dsl_classes.get("creature_templates", [])}
        errors, warnings = _difficulty_entry_errors(
            entry_maps, live, declared_full, {e["map_id"] for e in heroics},
        )
        out.errors += errors
        out.warnings += warnings
        out.errors += _difficulty_entry_edits(dsl_classes, entry_maps)
        for key, rows in side_table_copies(entry_maps, live, dsl_classes).items():
            dsl_classes.setdefault(key, []).extend(rows)
        out.errors += _model_errors(entry_maps, dsl_classes)
        out.notes.append(
            f"dungeons: heroic creatures - difficulty_entry_1 on {sum(len(m) for m in entry_maps.values())} normal "
            f"row(s), side-table copies: " + ", ".join(
                f"{len([r for r in dsl_classes[s.registry_key] if r.get(DERIVED)])} {s.name}" for s in SIDE_TABLES
            )
        )
    return out
