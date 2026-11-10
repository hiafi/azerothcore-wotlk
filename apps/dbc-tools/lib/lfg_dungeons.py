"""
generate.py's side of the dungeon finder declarations (lib/dsl/lfg.py; lfg-classic-heroic): the full rows built from
the stock client files after the source is loaded. `expand()` is the one entry point; generate.py calls it once per
run, right after `dungeon_heroic.expand()` (it edits the heroic `instance_encounters` rows that one derives) and before
the SPELL_TABLES render and before `--check` returns, so both paths see the same rows and ERRORs.

What it builds:

1. **LFGDungeons rows** (`lfg_dungeons`: the `lfgdungeons_dbc` overlay and patch-Z's LFGDungeons.dbc).
   - `lfg_random()`: TypeID 6, MapID 0, the declared level window, ExpansionLevel and group, the `like` row's
     Difficulty, Flags, Faction, TextureFilename, Order_Index and locale masks; the name in enUS only.
   - `lfg_heroic()`: a copy of the stock normal row (every name locale, map, faction, texture, expansion, description)
     with TypeID 5 (LFG_TYPE_HEROIC), Difficulty 1, the group's random level window (MinLevel, MaxLevel and
     Target_Level_Min / _Max; Target_Level the random's) and Group_Id. Flags stay the normal row's (3, as on every
     stock TBC heroic row).
2. **lfg_dungeon_template** (`lfg_dungeon_templates`): a heroic entry gets its normal entry's entrance position when
   the normal one has a row (LFGMgr falls back to the map's entrance areatrigger otherwise, which is the same for
   both difficulties).
3. **The final boss**: every heroic `instance_encounters` row lib/dungeon_heroic.py derived from a normal row whose
   `lastEncounterDungeon` is a declared heroic's `normal` gets the heroic entry's id there instead of 0
   (`ObjectMgr::LoadInstanceEncounters` keeps it per (map, difficulty), `Map::UpdateEncounterState` passes it to
   `LFGMgr::FinishDungeon`, which compares it with the group's dungeon).
4. **LFGDungeonGroup rows** (`lfg_groups`, client only): a new group from its declaration, a stock group with the
   declared OrderIndex (and name / type when given).

ERRORs (generate.py stops, also under `--check`): a missing stock file, an id clash with a stock or live row, a
random's `like` that is not a stock random, two randoms in one group, a heroic whose `normal` is not a stock normal
dungeon row, whose map has no declared heroic, whose group has no random or whose heroic encounters carry no final
boss, two heroics of one normal row, and a dungeon row in an undeclared group that is not stock either.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import dbcfmt, state
from .spell_tables import LFG_DUNGEON_TEMPLATE_COLUMNS

LFG_TYPE_DUNGEON = 1
LFG_TYPE_HEROIC = 5
LFG_TYPE_RANDOM = 6
DIFFICULTY_NORMAL = 0
DIFFICULTY_HEROIC = 1
LFG_FLAG_SEASONAL = 0x4  # LFGMgr.h: a holiday boss entry (Crown Chemical Co. on Shadowfang Keep), never pooled
# The normal finder entry a derived heroic instance_encounters row was copied from (lib/dungeon_heroic.py sets it):
# the normal row's lastEncounterDungeon. Bookkeeping only, never a column.
NORMAL_LFG_KEY = "_normal_lfg"
DERIVED = "_lfg_dungeons"


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
    """The stock LFGDungeons.dbc / LFGDungeonGroup.dbc and the live `lfg_dungeon_template` rows (`spell_table_index`:
    the run's SPELL_TABLES index)."""
    return LfgInputs(
        stock_dungeons=_stock(base_dir / dbcfmt.LFGDUNGEONS.dbc_filename, dbcfmt.LFGDUNGEONS),
        stock_groups=_stock(base_dir / dbcfmt.LFGDUNGEONGROUP.dbc_filename, dbcfmt.LFGDUNGEONGROUP),
        positions={_int(r.get("dungeonId")): r for r in spell_table_index.live_rows("lfg_dungeon_template")},
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


def _clear_derived(dsl_classes: dict) -> None:
    for key in ("lfg_dungeons", "lfg_dungeon_templates", "lfg_groups"):
        dsl_classes[key] = [r for r in dsl_classes.get(key, []) if not r.get(DERIVED)]
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
    stock = inputs.stock_dungeons
    groups = _group_rows(dsl_classes.get("lfg_group_declarations", []), inputs.stock_groups or {}, out)
    known_groups = set(groups) | {_int(r.get("Group_Id")) for r in stock.values()} | set(inputs.stock_groups or {})
    declared = dsl_classes.get("lfg_dungeon_declarations", [])
    for decl in declared:
        if decl["id"] in stock:
            out.errors.append(f"dungeon finder: LFGDungeons id {decl['id']} is a stock row - pick a free id")
    randoms: dict[int, dict] = {}
    rows: dict[int, dict] = {}
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
    positions = []
    for decl in (d for d in declared if d["kind"] == "heroic"):
        label = f"lfg_heroic({decl['id']}, normal={decl['normal']})"
        normal = stock.get(decl["normal"])
        if normal is None or _int(normal.get("TypeID")) != LFG_TYPE_DUNGEON \
                or _int(normal.get("Difficulty")) != DIFFICULTY_NORMAL or _int(normal.get("Flags")) & LFG_FLAG_SEASONAL:
            out.errors.append(f"{label}: {decl['normal']} is not a stock normal dungeon row (LFGDungeons TypeID 1, "
                              f"Difficulty 0, not seasonal)")
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
        position = inputs.positions.get(decl["normal"])
        if position is not None:
            template = {c: position.get(c) for c in LFG_DUNGEON_TEMPLATE_COLUMNS}
            template.update(dungeonId=decl["id"], name=f"{normal.get('Name_Lang_enUS')} (Heroic)")
            template.update(id=decl["id"])
            template[DERIVED] = True
            positions.append(template)
    for row_id, row in sorted(rows.items()):
        row["id"] = row_id
        row[DERIVED] = True
    _link_final_bosses(dsl_classes, by_normal, heroic_maps, stock, out)
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


def _link_final_bosses(dsl_classes: dict, by_normal: dict[int, int], heroic_maps: dict, stock: dict,
                       out: LfgExpansion) -> None:
    linked: dict[int, list[int]] = {}
    for row in dsl_classes.get("instance_encounters", []):
        normal_lfg = _int(row.get(NORMAL_LFG_KEY))
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
