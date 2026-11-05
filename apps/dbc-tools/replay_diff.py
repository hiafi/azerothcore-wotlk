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
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import frozen_replay, replay_diff  # noqa: E402

# Above this many distinct values of the first key column the query reads the whole table instead of an IN list.
_MAX_IN_LIST = 20000


def _run_sql(mysql: list[str], database: str, sql: str) -> list[dict]:
    done = subprocess.run(
        [*mysql, "-B", "--default-character-set=utf8mb4", database], input=sql, capture_output=True, text=True,
    )
    if done.returncode != 0:
        raise SystemExit(f"replay_diff.py: mysql failed ({done.returncode}): {done.stderr.strip()}")
    return replay_diff.parse_mysql_batch(done.stdout)


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
    args = parser.parse_args(argv)
    if not args.mysql:
        parser.error("--mysql (or $DBC_TOOLS_MYSQL) is required")
    mysql = shlex.split(args.mysql)
    only = set(args.tables.split(",")) if args.tables else None

    # Replay only what the live DB ran: a pending (or module) file not in `updates` yet is left out and listed.
    applied = {r["name"] for r in _run_sql(mysql, args.database, "SELECT `name` FROM `updates`;")}
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


if __name__ == "__main__":
    sys.exit(main())
