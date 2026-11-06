#!/usr/bin/env python3
"""
Replay vs live for every table a frozen replay input writes (`lib/replay_diff.py` explains the method).

Read-only: it replays the SQL files (no DB) and runs SELECTs against the live world DB through a mysql client command
you give it (the query goes in on stdin, so a `docker exec` needs `-i`):

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/replay_diff.py \\
        --mysql "docker exec -i <ac-database container> mysql -uroot -p<password>"

`--mysql` defaults to `$DBC_TOOLS_MYSQL`. `--tables a,b` limits the run, `--baseline` also replays without the frozen
files and reports how many footprint cells that gets wrong (what the frozen slot fixes), `--limit N` caps the
differences printed per table (default 20). Exit status 1 when a difference is not in the slot's `ALLOWED_DIFFS`,
or an `ALLOWED_DIFFS` entry matches nothing (stale).

`--whole` runs the whole-table check instead: every row and cell of every table dbc-tools replays
(`lib/replay_diff.REPLAYED_TABLES`, or `--tables`), replay vs live, keyed on each table's primary key. The DBC-backed
tables are checked twice, once per replay function (`composite` and `keyed`). Explained differences are listed in
`replay/ALLOWED_TABLE_DIFFS` (same TSV as `ALLOWED_DIFFS`; `*` as the key means every key of that column). `--json
FILE` writes every difference and skipped statement. Exit status 1 on an unexplained difference, a stale entry or a
duplicate replayed key.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import frozen_replay, replay_diff, sqlcorpus  # noqa: E402

# Above this many distinct values of the first key column the query reads the whole table instead of an IN list.
_MAX_IN_LIST = 20000


def _run_sql(mysql: list[str], database: str, sql: str) -> list[dict]:
    done = subprocess.run(
        [*mysql, "-B", "--default-character-set=utf8mb4", database], input=sql.encode(), capture_output=True,
    )
    if done.returncode != 0:
        raise SystemExit(f"replay_diff.py: mysql failed ({done.returncode}): {done.stderr.decode(errors='replace')}")
    # Some live text columns hold bytes that are not UTF-8: decode leniently (such a cell reads as a difference).
    return replay_diff.parse_mysql_batch(done.stdout.decode("utf-8", errors="replace"))


def _quote(value: object) -> str:
    if isinstance(value, (int, float)):
        return replay_diff.key_text((value,))
    return "'" + str(value).replace("\\", "\\\\").replace("'", "''") + "'"


def _live_rows(
    mysql: list[str], database: str, table: str, schema: replay_diff.Schema, cells: dict,
) -> tuple[dict[str, dict], list[str]]:
    """`({key_text: row}, footprint columns missing live)` for the footprint's rows."""
    live_columns = {
        r["COLUMN_NAME"] for r in _run_sql(
            mysql, database,
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            f"WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = '{table}';",
        )
    }
    wanted = sorted({c for cols in cells.values() for c in cols} | set(schema.key_columns))
    missing = [c for c in wanted if c not in live_columns]
    select = ", ".join(f"`{c}`" for c in wanted if c in live_columns)
    sql = f"SELECT {select} FROM `{table}`"
    first = {k[0] for k in cells}
    if len(first) <= _MAX_IN_LIST:
        sql += f" WHERE `{schema.key_columns[0]}` IN ({', '.join(_quote(v) for v in sorted(first, key=str))})"
    rows = _run_sql(mysql, database, sql + ";")
    return {replay_diff.key_text(tuple(r[c] for c in schema.key_columns)): r for r in rows}, missing


def _show(value: object) -> str:
    text = repr(value)
    return text if len(text) <= 60 else text[:57] + "..."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--mysql", default=os.environ.get("DBC_TOOLS_MYSQL"), help="mysql client command")
    parser.add_argument("--database", default="acore_world")
    parser.add_argument("--tables", help="comma-separated subset")
    parser.add_argument("--baseline", action="store_true", help="also count what a replay without the slot gets wrong")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--whole", action="store_true", help="whole-table check of every replayed table")
    parser.add_argument("--json", help="--whole: write every difference and skip to this file")
    args = parser.parse_args(argv)
    if not args.mysql:
        parser.error("--mysql (or $DBC_TOOLS_MYSQL) is required")
    mysql = shlex.split(args.mysql)
    only = set(args.tables.split(",")) if args.tables else None

    # Replay only what the live DB ran: a pending (or module) file not in `updates` yet is left out and listed.
    applied = {r["name"] for r in _run_sql(mysql, args.database, "SELECT `name` FROM `updates`;")}
    if args.whole:
        return _whole(args, mysql, applied, only)
    status = 0
    for slot in frozen_replay.slots():
        allowed = replay_diff.load_allowed(slot.directory / replay_diff.ALLOWED_DIFFS_NAME)
        print(f"== {slot.directory.name}: {len(slot.files)} file(s) after {slot.after}, before {slot.before}")
        all_differences: list[replay_diff.Difference] = []
        totals = [0, 0, 0, 0]  # footprint rows, cells, differences, unexplained
        for table, files in replay_diff.frozen_tables(slot).items():
            if only is not None and table not in only:
                continue
            started = time.monotonic()
            schema = replay_diff.table_schema(table)
            final, before, after, skipped, left_out = replay_diff.replay_with_snapshots(table, schema, applied=applied)
            cells = replay_diff.footprint(before, after, schema)
            live, missing = _live_rows(mysql, args.database, table, schema, cells) if cells else ({}, [])
            differences = replay_diff.compare(table, schema, cells, final, live)
            all_differences += differences
            replay_diff.explain(differences, allowed)
            unexplained = [d for d in differences if d.reason is None]
            n_cells = sum(len(c) for c in cells.values())
            totals = [totals[0] + len(cells), totals[1] + n_cells, totals[2] + len(differences),
                      totals[3] + len(unexplained)]
            line = (f"{table}: footprint {len(cells)} row(s), {n_cells} cell(s); {len(differences)} difference(s), "
                    f"{len(unexplained)} unexplained")
            if args.baseline:
                base_final = replay_diff.replay_with_snapshots(table, schema, include_frozen=False, applied=applied)[0]
                line += f"; without the slot: {len(replay_diff.compare(table, schema, cells, base_final, live))}"
            print(f"{line} [{time.monotonic() - started:.1f}s]")
            frozen_skips = [s for s in skipped if s.split(":", 1)[0] in {p.name for p in files}]
            if frozen_skips:
                print(f"  {len(frozen_skips)} frozen statement(s) the replay cannot apply:")
                for s in frozen_skips[:args.limit]:
                    print(f"    {s[:150]}")
            if left_out:
                print(f"  left out (not applied live): {', '.join(p.name for p in left_out)}")
            if missing:
                print(f"  footprint column(s) not in the live table: {', '.join(missing)}")
            for d in differences[:args.limit]:
                tag = f"explained: {d.reason}" if d.reason else "UNEXPLAINED"
                print(f"  {replay_diff.key_text(d.key)} {d.column}: replay {_show(d.replayed)}, live {_show(d.live)}"
                      f" ({tag})")
            if len(differences) > args.limit:
                print(f"  ... {len(differences) - args.limit} more")
        stale = replay_diff.explain(all_differences, allowed) if only is None else set()
        for table, key, column in sorted(stale):
            print(f"STALE allow-list entry (matches nothing): {table} {key} {column}")
        print(f"total: footprint {totals[0]} row(s), {totals[1]} cell(s); {totals[2]} difference(s), "
              f"{totals[3]} unexplained")
        if totals[3] or stale:
            status = 1
    return status


def _live_schema(mysql: list[str], database: str, table: str) -> replay_diff.Schema:
    """`replay_diff.Schema` from the live table's definition, for a table with no base dump."""
    rows = _run_sql(
        mysql, database,
        "SELECT COLUMN_NAME, COLUMN_DEFAULT, DATA_TYPE, COLUMN_KEY FROM information_schema.COLUMNS "
        f"WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = '{table}' ORDER BY ORDINAL_POSITION;",
    )
    columns = tuple(r["COLUMN_NAME"] for r in rows)
    key = tuple(r["COLUMN_NAME"] for r in rows if r["COLUMN_KEY"] == "PRI") or columns
    numeric = {"int", "tinyint", "smallint", "mediumint", "bigint", "float", "double", "decimal"}
    strings = frozenset(r["COLUMN_NAME"] for r in rows if r["DATA_TYPE"].lower() not in numeric)
    integers = frozenset(
        r["COLUMN_NAME"] for r in rows
        if r["DATA_TYPE"].lower() in {"int", "tinyint", "smallint", "mediumint", "bigint"}
    )
    defaults = {}
    for r in rows:
        value = r["COLUMN_DEFAULT"]
        if value is not None and r["COLUMN_NAME"] not in strings:
            value = float(value) if "." in value else int(value)
        defaults[r["COLUMN_NAME"]] = value
    return replay_diff.Schema(columns, key, defaults, strings, integers)


def _whole(args: argparse.Namespace, mysql: list[str], applied: set[str], only: set[str] | None) -> int:
    """`--whole`: see the module docstring."""
    allowed = replay_diff.load_allowed(replay_diff.ALLOWED_TABLE_DIFFS)
    tables = [t for t in replay_diff.REPLAYED_TABLES if only is None or t in only]
    sqlcorpus.activate(None, "replay_diff")  # each file read and head-scanned once for every table (no disk cache)
    results: list[replay_diff.WholeTableResult] = []
    for table in tables:
        if (replay_diff.trainer_state.BASE_SQL_DIR / f"{table}.sql").is_file():
            schema = replay_diff.table_schema(table)
        else:  # a table a migration created (spell_potency_correction): its live definition
            schema = _live_schema(mysql, args.database, table)
        live_rows = _run_sql(mysql, args.database, f"SELECT * FROM `{table}`;")
        loaders = ("composite", "keyed") if table in replay_diff.DBC_REPLAYED_TABLES else ("composite",)
        for loader in loaders:
            started = time.monotonic()
            rows, skipped, left_out = replay_diff.replay_whole_table(table, schema, applied, loader)
            differences, duplicates = replay_diff.whole_table_compare(table, schema, rows, live_rows)
            result = replay_diff.WholeTableResult(
                table, loader, schema.key_columns, len(live_rows), len(rows), duplicates, skipped,
                [p.name for p in left_out], differences, time.monotonic() - started,
            )
            results.append(result)
            replay_diff.explain_whole(differences, allowed)
            unexplained = [d for d in differences if d.reason is None]
            print(
                f"{table} [{loader}]: live {result.live_rows}, replay {result.replay_rows}; "
                f"missing {result.count('missing')} ({result.count('missing', False)} unexplained), "
                f"extra {result.count('extra')} ({result.count('extra', False)} unexplained), "
                f"cells {result.count('cells')} ({result.count('cells', False)} unexplained); "
                f"{len(skipped)} skipped statement(s); {duplicates} duplicate key(s) [{result.seconds:.1f}s]",
                flush=True,
            )
            for d in unexplained[:args.limit]:
                print(f"  {replay_diff.key_text(d.key)} {d.column}: replay {_show(d.replayed)}, live {_show(d.live)}")
            if len(unexplained) > args.limit:
                print(f"  ... {len(unexplained) - args.limit} more unexplained")
    stale = replay_diff.explain_whole([d for r in results for d in r.differences], allowed) if only is None else set()
    for table, key, column in sorted(stale):
        print(f"STALE allow-list entry (matches nothing): {table} {key} {column}")
    if args.json:
        Path(args.json).write_text(json.dumps([
            {
                "table": r.table, "loader": r.loader, "live": r.live_rows, "replay": r.replay_rows,
                "duplicates": r.duplicate_keys, "skipped": r.skipped, "left_out": r.left_out,
                "differences": [
                    {"key": list(d.key), "column": d.column, "replayed": repr(d.replayed), "live": repr(d.live),
                     "reason": d.reason}
                    for d in r.differences
                ],
            }
            for r in results
        ], indent=1), encoding="utf-8")
    bad = sum(1 for r in results for d in r.differences if d.reason is None)
    duplicates = sum(r.duplicate_keys for r in results)
    for r in results:
        if r.duplicate_keys:
            print(f"DUPLICATE KEYS: {r.table} [{r.loader}]: {r.duplicate_keys} replayed row(s) share a key with "
                  f"another (the live table cannot hold that: the replay is wrong somewhere)")
    print(f"total: {bad} unexplained difference(s), {duplicates} duplicate replayed key(s) over {len(results)} "
          f"table check(s)")
    return 1 if bad or stale or duplicates else 0


if __name__ == "__main__":
    sys.exit(main())
