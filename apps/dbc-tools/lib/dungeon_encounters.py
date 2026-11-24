"""
generate.py's side of lib/dsl/dungeon.py's encounter declarations (Scarlet Monastery build FD-SM): the rows of every
`dungeon_encounter()` (a new DungeonEncounter row) and `repoint_encounter()` (an edit of a stock one), built from the
stock DungeonEncounter.dbc and the live rows after the source is loaded. `expand()` is the one entry point; generate.py
calls it once per run, right BEFORE `dungeon_heroic.expand()` (a declared heroic copies the declared normal rows, see
`dungeon_heroic.with_declared_encounters()`), and its ERRORs and notes ride on the dungeon expansion, which both the
full run and `--check` report.

What it builds:

1. **DungeonEncounter rows** (`dungeon_encounters`: the `dungeonencounter_dbc` overlay, and through
   `dungeon_heroic.client_encounter_rows()` the patch-Z DungeonEncounter.dbc, merged over the stock file by ID).
   - `dungeon_encounter()`: every column from the declaration; the name in enUS (other locales empty) and the
     `Name_Lang_Mask` of the stock rows (0xFF01FE, enUS present).
   - `repoint_encounter()`: the stock row with the declared columns replaced (a new name clears the other locales);
     the same ID, map and difficulty, so a save's completed mask and a heroic copy stay valid.
2. **instance_encounters rows** (the kill credit): `credit_creature(entry)` -> creditType 0, `credit_spell(id)` ->
   creditType 1, with the declared `lastEncounterDungeon`. A repoint without `credit=` / `last_encounter=` keeps the
   live row's values (and writes nothing when the row is unchanged); one with no live credit and no declared credit
   writes none. `ObjectMgr::LoadInstanceEncounters` files each row under its DungeonEncounter row's (MapID,
   Difficulty), so the credit needs no difficulty column.

Every row this module adds carries `MARK`, so a second `expand()` replaces its rows instead of doubling them, and
`dungeon_heroic` tells declared rows from its own derived ones.

ERRORs (generate.py stops, also under `--check`):
- a missing stock DungeonEncounter.dbc (the base of both halves);
- `dungeon_encounter()` with a stock id (that is `repoint_encounter()`), or an id a live overlay row of another map or
  difficulty holds (module or migration SQL); a (map, difficulty) with no stock or declared MapDifficulty row;
- `repoint_encounter()` of an id that is not a stock row;
- two rows of one (map, difficulty) list on one Bit (stock, module rows and declared, after repoints) - the second
  kill would set the first one's completed bit;
- a credit creature that exists neither live nor in this run's creature_template() rows (the server skips the row);
- a `last_encounter` that is no stock or declared LFGDungeons row of the encounter's map and difficulty, or a finder
  entry another live credit row already ends (`ObjectMgr` keeps only the first), or an `lfg_override()` /
  `lfg_dungeon()` `last_encounter=` naming a declared encounter (set it on the encounter declaration instead).
WARNINGs: two rows of one list on one OrderIndex (the client orders them by ID), a credit spell this run does not
declare (it must exist live, or the server skips the credit row).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from . import dbcfmt, state

MARK = "_dungeon_encounter"  # a row this module appended to dungeon_encounters / instance_encounters
NAME_MASK = 0xFF01FE  # Name_Lang_Mask of every stock row (enUS present)
LOCALE_NAMES = tuple(c for c in dbcfmt.DUNGEONENCOUNTER.columns if c.startswith("Name_Lang_") and c != "Name_Lang_Mask")


def _int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _signed(value) -> int:
    value = _int(value)
    return value - 0x100000000 if value >= 0x80000000 else value


@dataclass
class EncounterInputs:
    """What `expand()` reads. `load_inputs()` builds it for a real run; tests build it by hand."""

    stock_encounters: dict[int, dict] | None  # stock DungeonEncounter.dbc by ID; None: the file is missing
    live_encounters: list[dict] = field(default_factory=list)  # the replayed dungeonencounter_dbc overlay
    credits: dict[int, dict] = field(default_factory=dict)  # the replayed instance_encounters, by entry
    map_difficulties: set[tuple[int, int]] | None = None  # stock + live MapDifficulty (MapID, Difficulty); None: skip
    creature_entries: set[int] = field(default_factory=set)  # live creature_template entries
    spell_ids: set[int] | None = None  # spells this run declares; None: no spell check
    lfg_dungeons: dict[int, dict] | None = None  # stock + live LFGDungeons rows by ID; None: file missing, no check
    # ids.yaml's dungeonencounter block: live overlay rows inside it are this tool's own output (the declarations are
    # the truth for those), rows outside it are module or migration SQL and count as held
    block: tuple[int, int] | None = None


@dataclass
class EncounterExpansion:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def needs_inputs(dsl_classes: dict) -> bool:
    return bool(dsl_classes.get("encounter_declarations"))


def load_inputs(
    spell_table_index, creature_entries, spell_ids=None, ids_cfg: dict | None = None,
    base_dir: Path = state.BASE_DBC_DIR,
) -> EncounterInputs:
    """The stock DungeonEncounter.dbc / MapDifficulty.dbc / LFGDungeons.dbc, the live `dungeonencounter_dbc`,
    `instance_encounters`, `mapdifficulty_dbc` and `lfgdungeons_dbc` rows (`spell_table_index`: the run's SPELL_TABLES
    index), the live creature entries and the run's declared spell ids."""
    encounter_path = base_dir / dbcfmt.DUNGEONENCOUNTER.dbc_filename
    stock = (
        {int(r["ID"]): r for r in state.read_dbc_cached(encounter_path, dbcfmt.DUNGEONENCOUNTER)}
        if encounter_path.is_file() else None
    )
    md_path = base_dir / dbcfmt.MAPDIFFICULTY.dbc_filename
    pairs = None
    if md_path.is_file():
        pairs = {
            (_int(r.get("MapID")), _int(r.get("Difficulty")))
            for r in [*state.read_dbc_cached(md_path, dbcfmt.MAPDIFFICULTY),
                      *spell_table_index.live_rows("mapdifficulty_dbc")]
        }
    lfg_path = base_dir / dbcfmt.LFGDUNGEONS.dbc_filename
    lfg = None
    if lfg_path.is_file():
        lfg = {int(r["ID"]): r for r in state.read_dbc_cached(lfg_path, dbcfmt.LFGDUNGEONS)}
        for row in spell_table_index.live_rows("lfgdungeons_dbc"):
            lfg[_int(row.get("ID"))] = row
    block = (ids_cfg or {}).get("dungeonencounter")
    return EncounterInputs(
        stock_encounters=stock,
        live_encounters=spell_table_index.live_rows("dungeonencounter_dbc"),
        credits={_int(r.get("entry")): r for r in spell_table_index.live_rows("instance_encounters")},
        map_difficulties=pairs, creature_entries={int(e) for e in creature_entries},
        spell_ids=None if spell_ids is None else {int(s) for s in spell_ids}, lfg_dungeons=lfg,
        block=(int(block["start"]), int(block["end"])) if block else None,
    )


def _clear(dsl_classes: dict) -> None:
    for key in ("dungeon_encounters", "instance_encounters"):
        dsl_classes[key] = [r for r in dsl_classes.get(key, []) if not r.get(MARK)]


def _label(decl: dict) -> str:
    if decl["kind"] == "new":
        return f"dungeon_encounter({decl['id']}, {decl['name']!r})"
    return f"repoint_encounter({decl['id']})"


def _new_row(decl: dict) -> dict:
    row = {c: "" for c in LOCALE_NAMES}
    row.update(
        ID=decl["id"], MapID=decl["map_id"], Difficulty=decl["difficulty"], OrderIndex=decl["order_index"],
        Bit=decl["bit"], Name_Lang_enUS=decl["name"], Name_Lang_Mask=NAME_MASK, SpellIconID=decl["icon"],
    )
    return row


def _repoint_row(decl: dict, stock: dict) -> dict:
    row = {c: stock.get(c) for c in dbcfmt.DUNGEONENCOUNTER.columns}
    row["OrderIndex"] = _signed(row.get("OrderIndex"))
    if decl["name"] is not None:
        row.update({c: "" for c in LOCALE_NAMES})
        row["Name_Lang_enUS"] = decl["name"]
    for key, column in (("order_index", "OrderIndex"), ("bit", "Bit"), ("icon", "SpellIconID")):
        if decl[key] is not None:
            row[column] = decl[key]
    return row


def _credit_row(decl: dict, row: dict, live: dict | None) -> dict | None:
    """The `instance_encounters` row of one declaration, or None for none."""
    credit, last = decl["credit"], decl["last_encounter"]
    if decl["kind"] == "new":
        if credit is None:
            return None
        credit_type, entry = credit
        return {"entry": decl["id"], "creditType": credit_type, "creditEntry": entry,
                "lastEncounterDungeon": last or 0, "comment": row["Name_Lang_enUS"]}
    if live is None and credit is None:
        return None  # nothing to keep and nothing declared (last_encounter alone needs a credit: checked)
    out = {
        "entry": decl["id"],
        "creditType": _int(live.get("creditType")) if live else 0,
        "creditEntry": _int(live.get("creditEntry")) if live else 0,
        "lastEncounterDungeon": _int(live.get("lastEncounterDungeon")) if live else 0,
        "comment": (live.get("comment") if live else None) or row["Name_Lang_enUS"],
    }
    if credit is not None:
        out["creditType"], out["creditEntry"] = credit
    if last is not None:
        out["lastEncounterDungeon"] = last
    if decl["name"] is not None:
        out["comment"] = decl["name"]
    return out


def expand(dsl_classes: dict, load: Callable[[], EncounterInputs]) -> EncounterExpansion:
    """Fills `dungeon_encounters` / `instance_encounters` with the declared rows (replacing any an earlier call added)
    and returns the run's ERRORs, WARNINGs and notes. `load` is only called when something is declared."""
    out = EncounterExpansion()
    _clear(dsl_classes)
    declared = list(dsl_classes.get("encounter_declarations", []))
    if not declared:
        return out
    inputs = load()
    if inputs.stock_encounters is None:
        out.errors.append(
            f"dungeon encounters: no stock {dbcfmt.DUNGEONENCOUNTER.dbc_filename} at "
            f"{state.BASE_DBC_DIR / dbcfmt.DUNGEONENCOUNTER.dbc_filename} - copy it from the worldserver's DBC "
            f"directory (ac-worldserver:/azerothcore/env/dist/data/dbc/) into that directory; the overlay rows and the "
            f"client patch both come from it"
        )
        return out
    stock = inputs.stock_encounters
    errors_before = len(out.errors)
    declared_md = {(_int(r.get("MapID")), _int(r.get("Difficulty"))) for r in dsl_classes.get("map_difficulties", [])}
    heroic_ids = {
        _int(e): entry["map_id"] for entry in dsl_classes.get("dungeons", []) if entry.get("heroic")
        for e in entry["heroic"].get("encounter_ids") or ()
    }
    live_by_id = {_int(r.get("ID")): r for r in inputs.live_encounters}
    rows: dict[int, dict] = {}
    credits: list[dict] = []
    for decl in sorted(declared, key=lambda d: d["id"]):
        label, encounter_id = _label(decl), decl["id"]
        if encounter_id in heroic_ids:
            out.errors.append(f"{label}: {encounter_id} is also a heroic encounter id of dungeon "
                              f"{heroic_ids[encounter_id]} (heroic(encounter_ids=...)) - pick another id")
            continue
        if decl["kind"] == "new":
            if encounter_id in stock:
                out.errors.append(f"{label}: {encounter_id} is a stock DungeonEncounter id - edit a stock row with "
                                  f"repoint_encounter(), a new row takes an id from ids.yaml's dungeonencounter block")
                continue
            live = live_by_id.get(encounter_id)
            if live is not None and (_int(live.get("MapID")), _int(live.get("Difficulty"))) != (
                    decl["map_id"], decl["difficulty"]):
                out.errors.append(
                    f"{label}: live dungeonencounter_dbc row {encounter_id} belongs to map {_int(live.get('MapID'))} "
                    f"difficulty {_int(live.get('Difficulty'))} (module or migration SQL, or another declaration's "
                    f"earlier output) - pick another id"
                )
                continue
            pair = (decl["map_id"], decl["difficulty"])
            if inputs.map_difficulties is not None and pair not in inputs.map_difficulties | declared_md:
                out.errors.append(f"{label}: map {pair[0]} has no MapDifficulty row for difficulty {pair[1]} (stock, "
                                  f"live or declared) - not an instance map, or that difficulty does not exist")
                continue
            row = _new_row(decl)
        else:
            base = stock.get(encounter_id)
            if base is None:
                out.errors.append(f"{label}: {encounter_id} is not a stock DungeonEncounter row - a new encounter is "
                                  f"dungeon_encounter(...) with an id from ids.yaml's dungeonencounter block")
                continue
            row = _repoint_row(decl, base)
        credit = _credit_row(decl, row, inputs.credits.get(encounter_id))
        if decl["kind"] == "repoint" and decl["last_encounter"] and credit is None:
            out.errors.append(f"{label}: last_encounter={decl['last_encounter']} needs a credit, and stock row "
                              f"{encounter_id} has no instance_encounters row - pass credit= too")
            continue
        rows[encounter_id] = row
        if credit is not None:
            credits.append(credit)
    _bit_checks(rows, stock, inputs, out)
    _credit_checks(rows, credits, inputs, dsl_classes, out)
    if len(out.errors) > errors_before:
        return out
    for row_id in sorted(rows):
        row = dict(rows[row_id], id=row_id)
        row[MARK] = True
        dsl_classes["dungeon_encounters"].append(row)
    for credit in credits:
        credit = dict(credit, id=credit["entry"])
        credit[MARK] = True
        dsl_classes["instance_encounters"].append(credit)
    for row_id in sorted(rows):
        row = rows[row_id]
        decl = next(d for d in declared if d["id"] == row_id)
        credit = next((c for c in credits if c["entry"] == row_id), None)
        how = "no credit" if credit is None else (
            f"credit {'creature' if credit['creditType'] == 0 else 'spell'} {credit['creditEntry']}"
            + (f", ends finder entry {credit['lastEncounterDungeon']}" if credit["lastEncounterDungeon"] else "")
        )
        out.notes.append(
            f"dungeon encounters: {'new' if decl['kind'] == 'new' else 'repointed stock'} {row_id} "
            f"{row['Name_Lang_enUS']!r} (map {row['MapID']} difficulty {row['Difficulty']}, bit {row['Bit']}, order "
            f"{row['OrderIndex']}), {how}"
        )
    return out


def _bit_checks(rows: dict[int, dict], stock: dict[int, dict], inputs: EncounterInputs,
                out: EncounterExpansion) -> None:
    """One Bit per (map, difficulty) list: stock rows, module rows (live, outside the block), then the declared rows."""
    merged = dict(stock)
    for row in inputs.live_encounters:
        row_id = _int(row.get("ID"))
        if inputs.block is not None and inputs.block[0] <= row_id <= inputs.block[1]:
            continue  # this tool's own earlier output: the declarations (and dungeon_heroic) decide those
        merged[row_id] = row
    merged.update(rows)
    lists = {(_int(rows[i]["MapID"]), _int(rows[i]["Difficulty"])) for i in rows}
    for pair in sorted(lists):
        members = [r for r in merged.values() if (_int(r.get("MapID")), _int(r.get("Difficulty"))) == pair]
        by_bit: dict[int, list[int]] = {}
        by_order: dict[int, list[int]] = {}
        for r in members:
            by_bit.setdefault(_int(r.get("Bit")), []).append(_int(r.get("ID")))
            by_order.setdefault(_signed(r.get("OrderIndex")), []).append(_int(r.get("ID")))
        for bit, ids in sorted(by_bit.items()):
            if len(ids) > 1 and any(i in rows for i in ids):
                out.errors.append(
                    f"dungeon encounters: map {pair[0]} difficulty {pair[1]}: rows {sorted(ids)} share Bit {bit} - one "
                    f"kill would complete both (the completed mask has one bit per encounter)"
                )
        for order, ids in sorted(by_order.items()):
            if len(ids) > 1 and any(i in rows for i in ids):
                out.warnings.append(
                    f"dungeon encounters: map {pair[0]} difficulty {pair[1]}: rows {sorted(ids)} share OrderIndex "
                    f"{order}; the client lists them by ID, and a heroic copies them in (OrderIndex, Bit, ID) order"
                )


def _credit_checks(rows: dict[int, dict], credits: list[dict], inputs: EncounterInputs, dsl_classes: dict,
                   out: EncounterExpansion) -> None:
    declared_creatures = {_int(r.get("entry")) for r in dsl_classes.get("creature_templates", [])}
    declared_lfg = {}
    for decl in dsl_classes.get("lfg_dungeon_declarations", []):
        if decl.get("kind") == "dungeon":
            declared_lfg[decl["id"]] = {"MapID": decl["map_id"], "Difficulty": 0}
        elif decl.get("kind") == "heroic" and inputs.lfg_dungeons is not None:
            normal = inputs.lfg_dungeons.get(decl["normal"]) or declared_lfg.get(decl["normal"])
            if normal is not None:
                declared_lfg[decl["id"]] = {"MapID": _int(normal.get("MapID")), "Difficulty": 1}
    redeclared = set(rows)
    for credit in credits:
        entry, row = credit["entry"], rows[credit["entry"]]
        label = f"DungeonEncounter {entry} ({row['Name_Lang_enUS']!r})"
        if credit["creditType"] == 0:
            creature = credit["creditEntry"]
            if creature not in inputs.creature_entries and creature not in declared_creatures:
                out.errors.append(f"{label}: credit creature {creature} has no creature_template row (live or "
                                  f"declared) - ObjectMgr::LoadInstanceEncounters skips the credit")
        elif inputs.spell_ids is not None and credit["creditEntry"] not in inputs.spell_ids:
            out.warnings.append(f"{label}: credit spell {credit['creditEntry']} is not declared in this run's "
                                f"source/ - unless it exists live, ObjectMgr::LoadInstanceEncounters skips the credit")
        last = credit["lastEncounterDungeon"]
        if not last:
            continue
        lfg_row = declared_lfg.get(last) or (inputs.lfg_dungeons or {}).get(last)
        if inputs.lfg_dungeons is not None and lfg_row is None:
            out.errors.append(f"{label}: last_encounter {last} is no LFGDungeons row (stock, live or declared)")
            continue
        if lfg_row is not None and (_int(lfg_row.get("MapID")), _int(lfg_row.get("Difficulty"))) != (
                _int(row["MapID"]), _int(row["Difficulty"])):
            out.errors.append(
                f"{label}: last_encounter {last} is a finder entry of map {_int(lfg_row.get('MapID'))} difficulty "
                f"{_int(lfg_row.get('Difficulty'))}, the encounter is on map {row['MapID']} difficulty "
                f"{row['Difficulty']} - LFGMgr::FinishDungeon would never match it"
            )
            continue
        others = sorted(
            e for e, r in inputs.credits.items()
            if e not in redeclared and _int(r.get("lastEncounterDungeon")) == last
        )
        others += sorted(c["entry"] for c in credits if c is not credit and c["lastEncounterDungeon"] == last)
        if others:
            out.errors.append(f"{label}: finder entry {last} already ends at encounter(s) {others} - "
                              f"ObjectMgr::LoadInstanceEncounters keeps only the first final boss")
    for decl in dsl_classes.get("lfg_dungeon_declarations", []):
        encounter = decl.get("last_encounter")
        if encounter is not None and encounter in rows:
            out.errors.append(
                f"lfg_{decl['kind']}({decl['id']}, last_encounter={encounter}): {encounter} is declared with "
                f"dungeon_encounter() / repoint_encounter() - set last_encounter={decl['id']} on that declaration "
                f"instead (two writers of one instance_encounters row)"
            )
