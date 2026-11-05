"""
generate.py's side of lib/dsl/dungeon.py (dungeon difficulties E1): the client MapDifficulty.dbc rows a run merges
into patch-Z, and the ERRORs both `--check` and the full run stop on.
"""

from __future__ import annotations

from pathlib import Path

from . import dbcfmt, state


def map_difficulty_client_rows(declared: list[dict]) -> dict[int, dict]:
    """Declared `map_difficulties` rows as MapDifficulty.dbc rows (only the file's columns), keyed by ID. The server
    half is the SPELL_TABLES `mapdifficulty_dbc` delta; this half is merged over the stock file on every build, like
    spell_rune_cost()'s."""
    return {int(r["ID"]): {c: r[c] for c in dbcfmt.MAPDIFFICULTY.columns} for r in declared}


def stock_file_error(declared: list[dict], base_dir: Path) -> str | None:
    """A declared heroic needs the stock MapDifficulty.dbc as the patch's base layer (and the lints below need it to
    see the stock rows). None when fine."""
    path = base_dir / dbcfmt.MAPDIFFICULTY.dbc_filename
    if declared and not path.is_file():
        ids = ", ".join(str(int(r["ID"])) for r in sorted(declared, key=lambda r: int(r["ID"])))
        return (
            f"dungeon(heroic=...) declares MapDifficulty row(s) {ids} but there is no stock "
            f"{dbcfmt.MAPDIFFICULTY.dbc_filename} at {path} - copy it from the worldserver's DBC directory "
            f"(ac-worldserver:/azerothcore/env/dist/data/dbc/{dbcfmt.MAPDIFFICULTY.dbc_filename}) into that directory "
            f"(see .agents/docs/systems/dbc-tools.md)"
        )
    return None


def check_dungeons(
    map_difficulties: list[dict], dungeon_access: list[dict], stock_map_difficulties: dict[int, dict] | None,
    live_map_difficulties: list[dict], live_access: list[dict],
) -> list[str]:
    """ERRORs for declared dungeon difficulties.

    - the map has no stock MapDifficulty row at all: not an instance map, so a wrong id
    - the (map, difficulty) is already a stock MapDifficulty row, or a live mapdifficulty_dbc row, under another id:
      `sMapDifficultyMap` keeps whichever the store visits last (DBCStores.cpp), and the client would carry two rows
    - a live dungeon_access_template row covers the (map, difficulty) under another id: two requirement rows for one
      pair, of which `ObjectMgr::LoadAccessRequirements` keeps the last loaded

    `stock_map_difficulties` is None when the stock file is missing (`stock_file_error` reports that; the stock checks
    are skipped). The live rows are the replayed overlay and table (base dump, migrations, module SQL), this tool's
    own earlier output included - a row with the declared id is that output, not a clash."""
    errors: list[str] = []
    if stock_map_difficulties is not None:
        stock_maps = {int(r["MapID"]) for r in stock_map_difficulties.values()}
        stock_pairs = {(int(r["MapID"]), int(r["Difficulty"])): int(r["ID"]) for r in stock_map_difficulties.values()}
    live_pairs: dict[tuple[int, int], set[int]] = {}
    for r in live_map_difficulties:
        live_pairs.setdefault((int(r["MapID"]), int(r["Difficulty"])), set()).add(int(r["ID"]))
    for row in map_difficulties:
        row_id, pair = int(row["ID"]), (int(row["MapID"]), int(row["Difficulty"]))
        label = f"dungeon({pair[0]}) MapDifficulty {row_id} (difficulty {pair[1]})"
        if stock_map_difficulties is not None:
            if pair[0] not in stock_maps:
                errors.append(
                    f"{label}: map {pair[0]} has no stock MapDifficulty row, so it is not an instance map - wrong id? "
                    f"dungeon() takes a Map.dbc id"
                )
            stock_id = stock_pairs.get(pair)
            if stock_id is not None and stock_id != row_id:
                errors.append(
                    f"{label}: the stock MapDifficulty.dbc already has row {stock_id} for this map and difficulty - "
                    f"two rows for one pair leave the server and the client each picking one"
                )
        clashes = sorted(live_pairs.get(pair, set()) - {row_id})
        if clashes:
            errors.append(
                f"{label}: live mapdifficulty_dbc row(s) {clashes} already cover this map and difficulty "
                f"(module or migration SQL) - remove them or declare that id"
            )
    access_pairs: dict[tuple[int, int], set[int]] = {}
    for r in live_access:
        if r.get("map_id") in (None, "") or r.get("difficulty") in (None, ""):
            continue
        access_pairs.setdefault((int(r["map_id"]), int(r["difficulty"])), set()).add(int(r["id"]))
    for row in dungeon_access:
        row_id, pair = int(row["id"]), (int(row["map_id"]), int(row["difficulty"]))
        clashes = sorted(access_pairs.get(pair, set()) - {row_id})
        if clashes:
            errors.append(
                f"dungeon({pair[0]}) dungeon_access_template {row_id} (difficulty {pair[1]}): live row(s) {clashes} "
                f"already hold the entry requirements of this map and difficulty - remove them or declare that id"
            )
    return errors


def summary_notes(dungeons: list[dict]) -> list[str]:
    """One line per declared heroic, for the run's output."""
    notes = []
    for entry in sorted(dungeons, key=lambda e: e["map_id"]):
        spec = entry.get("heroic")
        if not spec:
            continue
        cap = f"-{spec['max_level']}" if spec["max_level"] else "+"
        notes.append(
            f"dungeons: {entry['name']} (map {entry['map_id']}) heroic - MapDifficulty {spec['map_difficulty_id']} "
            f"(reset {spec['reset_seconds']} s, {spec['max_players']} players), dungeon_access_template "
            f"{spec['access_id']} (level {spec['min_level']}{cap}, item level {spec['min_item_level']})"
        )
    return notes


def errors_for_run(dsl_classes: dict, live_index, base_dir: Path = state.BASE_DBC_DIR) -> list[str]:
    """Every dungeon ERROR, wired the same way for `--check` and the full run. `live_index` is the run's
    `spell_tables.SpellTableIndex` (its live rows of both tables); the stock rows come from `base_dir`."""
    errors = []
    path = base_dir / dbcfmt.MAPDIFFICULTY.dbc_filename
    stock_rows = (
        {r["ID"]: r for r in state.read_dbc_cached(path, dbcfmt.MAPDIFFICULTY)} if path.is_file() else None
    )
    base_error = stock_file_error(dsl_classes["map_difficulties"], base_dir)
    if base_error:
        errors.append(base_error)
    errors += check_dungeons(
        dsl_classes["map_difficulties"], dsl_classes["dungeon_access"], stock_rows,
        live_index.live_rows("mapdifficulty_dbc"), live_index.live_rows("dungeon_access_template"),
    )
    return errors
