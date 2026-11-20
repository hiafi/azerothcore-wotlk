"""
generate.py's side of the dungeon finder declarations (lib/dsl/lfg.py; lfg-classic-heroic): the full rows built from
the stock client files after the source is loaded. `expand()` is the one entry point; generate.py calls it once per
run, right after `dungeon_heroic.expand()` (it edits the heroic `instance_encounters` rows that one derives) and before
the SPELL_TABLES render and before `--check` returns, so both paths see the same rows and ERRORs.

What it builds:

0. **Stock row edits** (`lfg_override()`): the stock row with the declared columns replaced, written to the overlay and
   patch-Z over the stock row (only when a column changes), and the declared entrance position as that dungeon's
   `lfg_dungeon_template` row. Every declaration below reads the edited row (a raid-type stock row made a dungeon
   entry can be a heroic's `normal`).
1. **LFGDungeons rows** (`lfg_dungeons`: the `lfgdungeons_dbc` overlay and patch-Z's LFGDungeons.dbc).
   - `lfg_dungeon()`: a new normal dungeon row (TypeID 1, Difficulty 0): a copy of the `like` stock row (texture,
     descriptions, faction, expansion, locale masks) with the declared id, enUS name (other name locales empty), map,
     group, flags and level window; its `position` as an `lfg_dungeon_template` row. Every declaration below reads it
     as a stock row (an lfg_heroic() may take it as `normal`).
   - `lfg_random()`: TypeID 6, MapID 0, the declared level window, ExpansionLevel and group, the `like` row's
     Difficulty, Flags, Faction, TextureFilename, Order_Index and locale masks; the name in enUS only.
   - `lfg_heroic()`: a copy of the stock normal row (every name locale, map, faction, texture, expansion, description)
     with TypeID 5 (LFG_TYPE_HEROIC), Difficulty 1, the group's random level window (MinLevel, MaxLevel and
     Target_Level_Min / _Max; Target_Level the random's) and Group_Id. Flags stay the normal row's (3, as on every
     stock TBC heroic row).
2. **lfg_dungeon_template** (`lfg_dungeon_templates`): a heroic entry gets its normal entry's entrance position when
   the normal one has a row (LFGMgr falls back to the map's entrance areatrigger otherwise, which is the same for
   both difficulties).
3. **The final boss**:
   - `last_encounter=` (lfg_dungeon(), lfg_override()): the normal `instance_encounters` row of that encounter, with
     `lastEncounterDungeon` = the finder entry, and every other row whose live or stock-dump value is that entry, set
     to 0 (the stock dump keeps the cleared row emitted after it went live, so the run stays stable). Rows go to
     `instance_encounters` (the prune pass never deletes a stock key; dropping the declaration leaves the edit live).
   - every heroic `instance_encounters` row lib/dungeon_heroic.py derived from a normal row whose `lastEncounterDungeon`
     (as edited above, else live) is a declared heroic's `normal` gets the heroic entry's id there instead of 0
   (`ObjectMgr::LoadInstanceEncounters` keeps it per (map, difficulty), `Map::UpdateEncounterState` passes it to
   `LFGMgr::FinishDungeon`, which compares it with the group's dungeon).
4. **LFGDungeonGroup rows** (`lfg_groups`, client only): a new group from its declaration, a stock group with the
   declared OrderIndex (and name / type when given).

ERRORs (generate.py stops, also under `--check`): a missing stock file, an id clash with a stock or live row, an
lfg_dungeon() whose `like` is not a stock normal dungeon row or whose group is unknown, a `last_encounter` that is not
a normal encounter of the entry's map or has no instance_encounters row, one encounter ending two entries, an edit
that leaves another finder entry of the map without a final boss, an
`lfg_override()` of an id that is not a stock row (or two of one id, or an edit that leaves a dungeon row of a raid-only
group), a
random's `like` that is not a stock random, two randoms in one group, a heroic whose `normal` is not a stock normal
dungeon row, whose map has no declared heroic, whose group has no random or whose heroic encounters carry no final
boss, two heroics of one normal row, and a dungeon row in an undeclared group that is not stock either.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import dbcfmt, state
from .dsl.lfg import OVERRIDE_COLUMNS
from .spell_tables import LFG_DUNGEON_TEMPLATE_COLUMNS, load_base_table_rows

LFG_TYPE_DUNGEON = 1
LFG_TYPE_HEROIC = 5
LFG_TYPE_RANDOM = 6
DIFFICULTY_NORMAL = 0
DIFFICULTY_HEROIC = 1
LFG_FLAG_SEASONAL = 0x4  # LFGMgr.h: a holiday boss entry (Crown Chemical Co. on Shadowfang Keep), never pooled
# The normal finder entry a derived heroic instance_encounters row was copied from (lib/dungeon_heroic.py sets it):
# the normal row's lastEncounterDungeon. Bookkeeping only, never a column.
NORMAL_LFG_KEY = "_normal_lfg"
NORMAL_ENTRY_KEY = "_normal_entry"  # the normal encounter that derived heroic row copies (lib/dungeon_heroic.py)
DERIVED = "_lfg_dungeons"
LINK = "_lfg_last_encounter"  # a normal instance_encounters row this module wrote (a last_encounter edit)


def _int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


@dataclass
class LfgInputs:
    """What `expand()` reads. `load_inputs()` builds it for a real run; tests build it by hand. None for a stock
    file means the file is missing from var/extractors/dbc/."""

    stock_dungeons: dict[int, dict] | None
    stock_groups: dict[int, dict] | None
    positions: dict[int, dict] = field(default_factory=dict)  # lfg_dungeon_template rows by dungeonId
    # For `last_encounter=` only: DungeonEncounter rows by ID (stock file, then the live overlay; None: file missing),
    # the live `instance_encounters` rows and the base dump's (both by entry).
    encounters: dict[int, dict] | None = None
    credits: dict[int, dict] = field(default_factory=dict)
    base_credits: dict[int, dict] = field(default_factory=dict)


@dataclass
class LfgExpansion:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _stock(path: Path, table: dbcfmt.DbcTable) -> dict[int, dict] | None:
    if not path.is_file():
        return None
    return {int(r["ID"]): r for r in state.read_dbc_cached(path, table)}


def load_inputs(spell_table_index, base_dir: Path = state.BASE_DBC_DIR) -> LfgInputs:
    """The stock LFGDungeons.dbc / LFGDungeonGroup.dbc / DungeonEncounter.dbc, the live `lfg_dungeon_template`,
    `dungeonencounter_dbc` and `instance_encounters` rows (`spell_table_index`: the run's SPELL_TABLES index) and the
    base dump's `instance_encounters`."""
    encounters = _stock(base_dir / dbcfmt.DUNGEONENCOUNTER.dbc_filename, dbcfmt.DUNGEONENCOUNTER)
    if encounters is not None:
        for row in spell_table_index.live_rows("dungeonencounter_dbc"):
            encounters[_int(row.get("ID"))] = row
    return LfgInputs(
        stock_dungeons=_stock(base_dir / dbcfmt.LFGDUNGEONS.dbc_filename, dbcfmt.LFGDUNGEONS),
        stock_groups=_stock(base_dir / dbcfmt.LFGDUNGEONGROUP.dbc_filename, dbcfmt.LFGDUNGEONGROUP),
        positions={_int(r.get("dungeonId")): r for r in spell_table_index.live_rows("lfg_dungeon_template")},
        encounters=encounters,
        credits={_int(r.get("entry")): r for r in spell_table_index.live_rows("instance_encounters")},
        base_credits={_int(r.get("entry")): r for r in load_base_table_rows("instance_encounters")},
    )


def needs_inputs(dsl_classes: dict) -> bool:
    return bool(dsl_classes.get("lfg_dungeon_declarations") or dsl_classes.get("lfg_group_declarations"))


def _missing_file(table: dbcfmt.DbcTable, how: str) -> str:
    return (
        f"dungeon finder: no stock {table.dbc_filename} at {state.BASE_DBC_DIR / table.dbc_filename} - {how}; the "
        f"rows and the client patch both come from it"
    )


def _group_rows(declared: list[dict], stock: dict[int, dict], out: LfgExpansion) -> dict[int, dict]:
    rows = {}
    for decl in declared:
        group_id = decl["id"]
        label = f"lfg_group({group_id})"
        if decl["new"]:
            if group_id in stock:
                out.errors.append(f"{label}: {group_id} is a stock LFGDungeonGroup id")
                continue
            row = {c: "" if c.startswith("Name_Lang_") and c != "Name_Lang_Mask" else 0
                   for c in dbcfmt.LFGDUNGEONGROUP.columns}
            # Every stock row carries 0xFF01FE (enUS present); copy it from one so a new row looks the same.
            row["Name_Lang_Mask"] = next(iter(stock.values()))["Name_Lang_Mask"] if stock else 0xFF01FE
        else:
            if group_id not in stock:
                out.errors.append(f"{label}: no stock LFGDungeonGroup row {group_id} to edit (a new group takes an id "
                                  f"from ids.yaml's lfgdungeongroup block)")
                continue
            row = dict(stock[group_id])
        row["ID"] = group_id
        if decl["name"] is not None:
            row["Name_Lang_enUS"] = decl["name"]
        if decl["type_id"] is not None:
            row["TypeID"] = decl["type_id"]
        row["OrderIndex"] = decl["order_index"]
        row["id"] = group_id
        row[DERIVED] = True
        rows[group_id] = row
    orders: dict[int, list[int]] = {}
    for row in {**stock, **rows}.values():
        orders.setdefault(_int(row["OrderIndex"]), []).append(_int(row["ID"]))
    for order, ids in sorted(orders.items()):
        if len(ids) > 1 and any(i in rows for i in ids):
            out.warnings.append(
                f"dungeon finder: LFGDungeonGroup rows {sorted(ids)} share OrderIndex {order}; the client lists them "
                f"in file order (by ID), so give each its own"
            )
    return rows


def _random_row(decl: dict, stock: dict[int, dict], out: LfgExpansion) -> dict | None:
    label = f"lfg_random({decl['id']}, {decl['name']!r})"
    like = stock.get(decl["like"])
    if like is None or _int(like.get("TypeID")) != LFG_TYPE_RANDOM:
        out.errors.append(f"{label}: like={decl['like']} is not a stock random row (LFGDungeons TypeID 6)")
        return None
    row = dict(like)
    for column in dbcfmt.LFGDUNGEONS.columns:
        if column.startswith("Name_Lang_") and column != "Name_Lang_Mask":
            row[column] = ""
    row.update(
        ID=decl["id"], Name_Lang_enUS=decl["name"], MinLevel=decl["min_level"], MaxLevel=decl["max_level"],
        Target_Level=decl["target_level"], Target_Level_Min=decl["min_level"], Target_Level_Max=decl["max_level"],
        MapID=0, TypeID=LFG_TYPE_RANDOM, ExpansionLevel=decl["expansion"], Group_Id=decl["group"],
    )
    return row


def _heroic_row(decl: dict, normal: dict, random: dict) -> dict:
    row = dict(normal)
    row.update(
        ID=decl["id"], MinLevel=random["MinLevel"], MaxLevel=random["MaxLevel"], Target_Level=random["Target_Level"],
        Target_Level_Min=random["Target_Level_Min"], Target_Level_Max=random["Target_Level_Max"],
        Difficulty=DIFFICULTY_HEROIC, TypeID=LFG_TYPE_HEROIC, Group_Id=decl["group"],
    )
    return row


def _template(dungeon_id: int, name, position: tuple) -> dict:
    x, y, z, o = position
    return {
        "dungeonId": dungeon_id, "name": name, "position_x": x, "position_y": y, "position_z": z, "orientation": o,
        "VerifiedBuild": 0, "id": dungeon_id, DERIVED: True,
    }


def _dungeon_row(decl: dict, stock: dict[int, dict], out: LfgExpansion) -> dict | None:
    """The new normal row of one `lfg_dungeon()`, or None after an ERROR."""
    label = f"lfg_dungeon({decl['id']}, {decl['name']!r})"
    like = stock.get(decl["like"])
    if like is None or _int(like.get("TypeID")) != LFG_TYPE_DUNGEON or _int(like.get("Difficulty")) != 0:
        out.errors.append(f"{label}: like={decl['like']} is not a stock normal dungeon row (LFGDungeons TypeID 1, "
                          f"Difficulty 0) to copy the texture and description from")
        return None
    if _int(like.get("MapID")) != decl["map_id"]:
        out.warnings.append(f"{label}: like={decl['like']} is on map {_int(like.get('MapID'))}, the entry on map "
                            f"{decl['map_id']} - its texture and description name another dungeon")
    row = dict(like)
    for column in dbcfmt.LFGDUNGEONS.columns:
        if column.startswith("Name_Lang_") and column != "Name_Lang_Mask":
            row[column] = ""
    row.update(
        ID=decl["id"], Name_Lang_enUS=decl["name"], MinLevel=decl["min_level"], MaxLevel=decl["max_level"],
        Target_Level=decl["target_level"], Target_Level_Min=decl["target_level_min"],
        Target_Level_Max=decl["target_level_max"], MapID=decl["map_id"], Difficulty=DIFFICULTY_NORMAL,
        Flags=decl["flags"], TypeID=LFG_TYPE_DUNGEON, Group_Id=decl["group"],
    )
    return row


def _override_row(decl: dict, stock: dict[int, dict], edited: dict[int, dict], out: LfgExpansion):
    """The edited row and the declared entrance position (an `lfg_dungeon_template` row) of one `lfg_override()`, or
    (None, None) after an ERROR."""
    label = f"lfg_override({decl['id']})"
    if decl["id"] not in stock:
        out.errors.append(f"{label}: no stock LFGDungeons row {decl['id']} to edit (a new entry takes an id from "
                          f"ids.yaml's lfgdungeons block, declared with lfg_random() / lfg_dungeon() / lfg_heroic())")
        return None, None
    if decl["id"] in edited:
        out.errors.append(f"{label}: row {decl['id']} is edited twice")
        return None, None
    row = dict(stock[decl["id"]])
    for name, value in decl["edits"].items():
        row[OVERRIDE_COLUMNS[name]] = value
    if _int(row["MinLevel"]) > _int(row["MaxLevel"]):
        out.errors.append(f"{label}: MinLevel {row['MinLevel']} is above MaxLevel {row['MaxLevel']} after the edit")
        return None, None
    row["id"] = decl["id"]
    row[DERIVED] = True
    template = None
    if decl["position"] is not None:
        template = _template(decl["id"], row.get("Name_Lang_enUS"), decl["position"])
    return row, template


def _clear_derived(dsl_classes: dict) -> None:
    for key in ("lfg_dungeons", "lfg_dungeon_templates", "lfg_groups"):
        dsl_classes[key] = [r for r in dsl_classes.get(key, []) if not r.get(DERIVED)]
    dsl_classes["instance_encounters"] = [r for r in dsl_classes.get("instance_encounters", []) if not r.get(LINK)]
    for row in dsl_classes.get("instance_encounters", []):
        if row.get(DERIVED):
            row["lastEncounterDungeon"] = 0
            del row[DERIVED]


def expand(dsl_classes: dict, load: callable) -> LfgExpansion:
    """Fills `lfg_dungeons`, `lfg_dungeon_templates` and `lfg_groups` from the declarations (replacing what an earlier
    call added) and links the heroic final bosses. `load` returns the `LfgInputs` and is only called when something is
    declared."""
    out = LfgExpansion()
    _clear_derived(dsl_classes)
    if not needs_inputs(dsl_classes):
        return out
    inputs: LfgInputs = load()
    if inputs.stock_dungeons is None:
        out.errors.append(_missing_file(
            dbcfmt.LFGDUNGEONS, "extract DBFilesClient/LFGDungeons.dbc from the client's patch-enUS-3.MPQ (or copy it "
            "from the azerothcore-wotlk_ac-client-data volume's /dbc/) into that directory",
        ))
        return out
    if dsl_classes.get("lfg_group_declarations") and inputs.stock_groups is None:
        out.errors.append(_missing_file(
            dbcfmt.LFGDUNGEONGROUP, "copy it from the azerothcore-wotlk_ac-client-data docker volume (/dbc/"
            "LFGDungeonGroup.dbc) into that directory",
        ))
        return out
    stock = dict(inputs.stock_dungeons)
    positions_in = dict(inputs.positions)
    edited: dict[int, dict] = {}
    written: dict[int, dict] = {}  # edited stock rows with a changed column: these go to the overlay and patch-Z
    override_positions: list[dict] = []
    for decl in (d for d in dsl_classes.get("lfg_dungeon_declarations", []) if d["kind"] == "override"):
        row, template = _override_row(decl, inputs.stock_dungeons, edited, out)
        if row is None:
            continue
        edited[decl["id"]] = row
        stock[decl["id"]] = row
        if decl["edits"]:
            written[decl["id"]] = row
        if template is not None:
            positions_in[decl["id"]] = template
            override_positions.append(template)
    groups = _group_rows(dsl_classes.get("lfg_group_declarations", []), inputs.stock_groups or {}, out)
    known_groups = set(groups) | {_int(r.get("Group_Id")) for r in stock.values()} | set(inputs.stock_groups or {})
    declared = dsl_classes.get("lfg_dungeon_declarations", [])
    for decl in declared:
        if decl["kind"] != "override" and decl["id"] in stock:
            out.errors.append(f"dungeon finder: LFGDungeons id {decl['id']} is a stock row - pick a free id")
    rows: dict[int, dict] = dict(written)
    for decl in (d for d in declared if d["kind"] == "dungeon"):
        if decl["id"] in stock:
            continue  # the stock-row ERROR above
        if decl["group"] not in known_groups:
            out.errors.append(f"lfg_dungeon({decl['id']}): group {decl['group']} is neither stock nor declared with "
                              f"lfg_group()")
        row = _dungeon_row(decl, stock, out)
        if row is None:
            continue
        stock[decl["id"]] = row
        rows[decl["id"]] = row
        if decl["position"] is not None:
            template = _template(decl["id"], decl["name"], decl["position"])
            positions_in[decl["id"]] = template
            override_positions.append(template)
        else:
            out.notes.append(f"dungeon finder: lfg_dungeon({decl['id']}) has no position - the Finder starts it at "
                             f"map {decl['map_id']}'s entrance areatrigger")
    links = _last_encounters(declared, stock, inputs, out)
    randoms: dict[int, dict] = {}
    for decl in (d for d in declared if d["kind"] == "random"):
        if decl["group"] in randoms:
            out.errors.append(
                f"lfg_random({decl['id']}): group {decl['group']} already has random {randoms[decl['group']]['ID']} - "
                f"a random draws from its whole group, so give each random its own group"
            )
            continue
        if decl["group"] not in known_groups:
            out.errors.append(f"lfg_random({decl['id']}): group {decl['group']} is neither stock nor declared with "
                              f"lfg_group()")
        row = _random_row(decl, stock, out)
        if row is not None:
            randoms[decl["group"]] = row
            rows[decl["id"]] = row
    heroic_maps = {
        int(e["map_id"]): e for e in dsl_classes.get("dungeons", []) if e.get("heroic")
    }
    by_normal: dict[int, int] = {}
    positions = list(override_positions)
    for decl in (d for d in declared if d["kind"] == "heroic"):
        label = f"lfg_heroic({decl['id']}, normal={decl['normal']})"
        normal = stock.get(decl["normal"])
        if normal is None or _int(normal.get("TypeID")) != LFG_TYPE_DUNGEON \
                or _int(normal.get("Difficulty")) != DIFFICULTY_NORMAL or _int(normal.get("Flags")) & LFG_FLAG_SEASONAL:
            out.errors.append(f"{label}: {decl['normal']} is not a stock normal dungeon row (LFGDungeons TypeID 1, "
                              f"Difficulty 0, not seasonal) or an lfg_dungeon() one")
            continue
        if decl["normal"] in by_normal:
            out.errors.append(f"{label}: normal {decl['normal']} already has heroic entry {by_normal[decl['normal']]}")
            continue
        map_id = _int(normal.get("MapID"))
        if map_id not in heroic_maps:
            out.errors.append(
                f"{label}: map {map_id} ({normal.get('Name_Lang_enUS')}) has no declared heroic - add "
                f"heroic=heroic(...) to its dungeon(...) in source/world/dungeons/ first"
            )
            continue
        random = randoms.get(decl["group"])
        if random is None:
            out.errors.append(f"{label}: group {decl['group']} has no lfg_random() - the heroic entry takes its level "
                              f"window from the group's random")
            continue
        by_normal[decl["normal"]] = decl["id"]
        rows[decl["id"]] = _heroic_row(decl, normal, random)
        position = positions_in.get(decl["normal"])
        if position is not None:
            template = {c: position.get(c) for c in LFG_DUNGEON_TEMPLATE_COLUMNS}
            template.update(dungeonId=decl["id"], name=f"{normal.get('Name_Lang_enUS')} (Heroic)")
            template.update(id=decl["id"])
            template[DERIVED] = True
            positions.append(template)
    for row_id, row in sorted(rows.items()):
        row["id"] = row_id
        row[DERIVED] = True
    _link_final_bosses(dsl_classes, by_normal, links, out)
    dsl_classes["instance_encounters"] = [*dsl_classes.get("instance_encounters", []),
                                          *_link_rows(links, inputs)]
    dsl_classes["lfg_dungeons"] = [*dsl_classes.get("lfg_dungeons", []), *(rows[i] for i in sorted(rows))]
    dsl_classes["lfg_dungeon_templates"] = [*dsl_classes.get("lfg_dungeon_templates", []), *positions]
    dsl_classes["lfg_groups"] = [*dsl_classes.get("lfg_groups", []), *(groups[i] for i in sorted(groups))]
    for group_id, random in sorted(randoms.items()):
        pool = sorted(i for i, r in rows.items() if _int(r.get("Group_Id")) == group_id and i != random["ID"])
        out.notes.append(
            f"dungeon finder: {random['ID']} {random['Name_Lang_enUS']!r} (levels {random['MinLevel']}-"
            f"{random['MaxLevel']}, group {group_id}) draws from " + (", ".join(
                f"{i} {rows[i]['Name_Lang_enUS']}" for i in pool) or "nothing")
        )
    _unlisted_heroics(heroic_maps, by_normal, stock, out)
    return out


def _last_encounters(declared: list[dict], stock: dict[int, dict], inputs: LfgInputs,
                     out: LfgExpansion) -> dict[int, int]:
    """The `last_encounter=` edits: appends nothing itself, returns {normal encounter id: lastEncounterDungeon} of
    every normal `instance_encounters` row to write (the declared final bosses and the rows they take the link from),
    after the ERROR checks; `expand()` writes the rows."""
    wanted = [d for d in declared if d.get("last_encounter") is not None and d["kind"] in ("dungeon", "override")
              and d["id"] in stock]
    if not wanted:
        return {}
    if inputs.encounters is None:
        out.errors.append(_missing_file(
            dbcfmt.DUNGEONENCOUNTER, "copy it from the worldserver's DBC directory (ac-worldserver:/azerothcore/env/"
            "dist/data/dbc/) into that directory; last_encounter= checks the encounter against it",
        ))
        return {}
    live = {e: _int(r.get("lastEncounterDungeon")) for e, r in inputs.credits.items()}
    base = {e: _int(r.get("lastEncounterDungeon")) for e, r in inputs.base_credits.items()}
    links: dict[int, int] = {}
    maps: set[int] = set()
    for decl in wanted:
        lfg_id, encounter_id = decl["id"], decl["last_encounter"]
        label = f"lfg_{'dungeon' if decl['kind'] == 'dungeon' else 'override'}({lfg_id}, last_encounter={encounter_id})"
        map_id = _int(stock[lfg_id].get("MapID"))
        encounter = inputs.encounters.get(encounter_id)
        if encounter is None or _int(encounter.get("MapID")) != map_id \
                or _int(encounter.get("Difficulty")) != DIFFICULTY_NORMAL:
            out.errors.append(f"{label}: {encounter_id} is not a normal encounter of map {map_id} (DungeonEncounter "
                              f"MapID {map_id}, Difficulty 0)")
            continue
        if encounter_id not in inputs.credits:
            out.errors.append(f"{label}: encounter {encounter_id} ({encounter.get('Name_Lang_enUS')}) has no "
                              f"instance_encounters row, so no kill could complete the entry")
            continue
        if encounter_id in links:
            out.errors.append(f"{label}: encounter {encounter_id} already ends finder entry {links[encounter_id]}")
            continue
        links[encounter_id] = lfg_id
        maps.add(map_id)
        out.notes.append(f"dungeon finder: {lfg_id} {stock[lfg_id].get('Name_Lang_enUS')} completes on encounter "
                         f"{encounter_id} {encounter.get('Name_Lang_enUS')}")
    edits = dict(links)
    for lfg_id in set(links.values()):
        for entry in sorted(live):  # a row deleted live stays deleted
            if entry not in links and lfg_id in (live[entry], base.get(entry)):
                edits[entry] = 0
                if live.get(entry) == lfg_id:
                    out.notes.append(f"dungeon finder: encounter {entry} no longer ends finder entry {lfg_id}")
    # Every finder entry of a touched map that has a final boss live keeps exactly one.
    on_maps = {e for e, r in inputs.encounters.items() if _int(r.get("MapID")) in maps}
    after = {e: edits.get(e, live.get(e, 0)) for e in on_maps if e in inputs.credits}
    for lfg_id in sorted({live[e] for e in on_maps if live.get(e)} | set(links.values())):
        ends = sorted(e for e, value in after.items() if value == lfg_id)
        if not ends:
            out.errors.append(f"dungeon finder: finder entry {lfg_id} loses its final boss (encounter "
                              f"{[e for e in on_maps if live.get(e) == lfg_id]} now ends another entry) - give it a "
                              f"last_encounter= too")
        elif len(ends) > 1:
            out.errors.append(f"dungeon finder: finder entry {lfg_id} ends at encounters {ends}; ObjectMgr keeps "
                              f"only the first")
    return edits


def _link_rows(edits: dict[int, int], inputs: LfgInputs) -> list[dict]:
    rows = []
    for entry, lfg_id in sorted(edits.items()):
        live = inputs.credits[entry]
        row = {c: live.get(c) for c in ("entry", "creditType", "creditEntry", "comment")}
        row.update(entry=entry, lastEncounterDungeon=lfg_id)
        row[LINK] = True
        rows.append(row)
    return rows


def _link_final_bosses(dsl_classes: dict, by_normal: dict[int, int], links: dict[int, int],
                       out: LfgExpansion) -> None:
    linked: dict[int, list[int]] = {}
    moved = {lfg_id for lfg_id in links.values() if lfg_id}  # entries whose final boss this run declares
    for row in dsl_classes.get("instance_encounters", []):
        if row.get(LINK):
            continue
        normal_entry = row.get(NORMAL_ENTRY_KEY)
        if normal_entry is not None and _int(normal_entry) in links:
            normal_lfg = links[_int(normal_entry)]
        else:
            normal_lfg = _int(row.get(NORMAL_LFG_KEY))
            if normal_lfg in moved:
                normal_lfg = 0  # the live link of a row the declaration did not keep
        heroic_id = by_normal.get(normal_lfg)
        if heroic_id is None:
            continue
        row["lastEncounterDungeon"] = heroic_id
        row[DERIVED] = True
        linked.setdefault(heroic_id, []).append(_int(row.get("entry")))
    for normal_id, heroic_id in sorted(by_normal.items()):
        entries = linked.get(heroic_id, [])
        label = f"lfg_heroic({heroic_id}, normal={normal_id})"
        if not entries:
            out.errors.append(
                f"{label}: no heroic instance_encounters row carries the normal entry's final boss (no normal "
                f"encounter has lastEncounterDungeon {normal_id}, or the map's heroic has no encounter_ids) - the "
                f"heroic run could never complete"
            )
        elif len(entries) > 1:
            out.errors.append(f"{label}: heroic encounters {entries} all end the run; ObjectMgr keeps only the first")
        else:
            out.notes.append(f"dungeon finder: {label} completes on heroic encounter {entries[0]}")


def _unlisted_heroics(heroic_maps: dict, by_normal: dict[int, int], stock: dict, out: LfgExpansion) -> None:
    """A note for each stock normal finder row on a declared-heroic map that has no lfg_heroic()."""
    for map_id, entry in sorted(heroic_maps.items()):
        missing = sorted(
            i for i, r in stock.items()
            if _int(r.get("MapID")) == map_id and _int(r.get("TypeID")) == LFG_TYPE_DUNGEON
            and _int(r.get("Difficulty")) == DIFFICULTY_NORMAL and not _int(r.get("Flags")) & LFG_FLAG_SEASONAL
            and i not in by_normal
        )
        if missing:
            out.notes.append(
                f"dungeon finder: {entry['name']} (map {map_id}) has a heroic but no lfg_heroic() for finder "
                f"entr{'y' if len(missing) == 1 else 'ies'} {missing}: it is not in any heroic random"
            )


def client_dungeon_rows(declared: list[dict]) -> dict[int, dict]:
    """`lfg_dungeons` rows as LFGDungeons.dbc rows (only the file's columns), keyed by ID, for the patch-Z merge."""
    return {int(r["ID"]): {c: r[c] for c in dbcfmt.LFGDUNGEONS.columns} for r in declared}


def client_group_rows(declared: list[dict]) -> dict[int, dict]:
    """`lfg_groups` rows as LFGDungeonGroup.dbc rows, keyed by ID, for the patch-Z merge."""
    return {int(r["ID"]): {c: r[c] for c in dbcfmt.LFGDUNGEONGROUP.columns} for r in declared}
