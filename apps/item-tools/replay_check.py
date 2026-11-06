#!/usr/bin/env python3
"""
Whole-table check for item-tools: every table item-tools reads, replayed the way item-tools replays it
(`item_lib/replay.py`, dbc-tools' parser), against the live world DB, row by row and cell by cell. Read-only: the
replay reads SQL files, the live side is `SELECT`s through a mysql client command you give it (the query goes in on
stdin, so a `docker exec` needs `-i`):

    apps/dbc-tools/.venv/bin/python3 apps/item-tools/replay_check.py \\
        --mysql "docker exec -i <ac-database container> sh -c 'mysql -uroot -p\\"\\$MYSQL_ROOT_PASSWORD\\"'"

`--mysql` defaults to `$DBC_TOOLS_MYSQL`. Only files the live `updates` table lists are replayed (a pending file not
applied yet is left out and listed). Rows are matched on the key item-tools reads them by; the comparison and the
allow list are dbc-tools' whole-table check (`apps/dbc-tools/lib/replay_diff.py`): `NULL`/missing = the column's
default, numbers as floats with a FLOAT tolerance, strings exactly. Explained differences live in
`apps/item-tools/replay/ALLOWED_TABLE_DIFFS` (TSV `table`, `key`, `column`, `reason`; key `*` = any key; column `*`,
`*missing` (live only) or `*extra` (replay only) for a row on one side). `--tables a,b` limits the run, `--json FILE`
writes every difference and skipped statement, `--limit N` caps the unexplained differences printed per table,
`--modules DIR` reads module SQL from another checkout's `modules/` (a worktree without the live server's modules),
`--also a.sql,b.sql` replays those not-yet-imported files too (a pending file that captures live state).
Exit status 1 on an unexplained difference, a duplicate replayed key or a stale allow-list entry (stale is judged on
a full run only).
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

TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from item_lib import budget_overlay, replay  # noqa: E402
from lib import replay_diff  # noqa: E402 - dbc-tools' lib, put on sys.path by item_lib.replay

ALLOWED_TABLE_DIFFS = TOOL_ROOT / "replay" / "ALLOWED_TABLE_DIFFS"

# Every table item-tools reads, with the key it reads it by (None: the table's primary key). `item_template`
# (`overlay.py`), the itemization tables (`budget_overlay.TABLES`) and the dungeon browser's tables (`loot.py`).
CHECKED_TABLES: dict[str, tuple[str, ...] | None] = {
    "item_template": ("entry",),
    **budget_overlay.TABLES,
    "instance_template": None,
    "instance_encounters": None,
    "creature_template": None,
    "creature": None,
    "creature_loot_template": None,
    "reference_loot_template": None,
}


def run_sql(mysql: list[str], database: str, sql: str) -> list[dict]:
    done = subprocess.run(
        [*mysql, "-B", "--default-character-set=utf8mb4", database], input=sql.encode(), capture_output=True,
    )
    if done.returncode != 0:
        raise SystemExit(f"replay_check.py: mysql failed ({done.returncode}): {done.stderr.decode(errors='replace')}")
    # Some live text columns hold bytes that are not UTF-8: decode leniently (such a cell reads as a difference).
    return replay_diff.parse_mysql_batch(done.stdout.decode("utf-8", errors="replace"))


def compare_table(
    table: str, schema, rows: list[dict], live_rows: list[dict], allowed: dict,
) -> tuple[list, int]:
    """`(differences, duplicate keys)`, each difference's `reason` set from `allowed` (None = unexplained)."""
    differences, duplicates = replay_diff.whole_table_compare(table, schema, rows, live_rows)
    replay_diff.explain_whole(differences, allowed)
    return differences, duplicates


def count(differences: list, kind: str, explained: bool | None = None) -> int:
    result = replay_diff.WholeTableResult(table="", loader="", key_columns=(), differences=differences)
    return result.count(kind, explained)


def _show(value: object) -> str:
    text = repr(value)
    return text if len(text) <= 60 else text[:57] + "..."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--mysql", default=os.environ.get("DBC_TOOLS_MYSQL"), help="mysql client command")
    parser.add_argument("--database", default="acore_world")
    parser.add_argument("--tables", help="comma-separated subset")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json", help="write every difference and skip to this file")
    parser.add_argument("--also", help="comma-separated file names to replay as if applied live (a pending file "
                                       "written to capture live state, before it is imported)")
    parser.add_argument("--modules", help="read module SQL from this modules/ directory (a worktree that lacks the "
                                          "live server's modules: point it at the main checkout's)")
    args = parser.parse_args(argv)
    if not args.mysql:
        parser.error("--mysql (or $DBC_TOOLS_MYSQL) is required")
    mysql = shlex.split(args.mysql)
    only = set(args.tables.split(",")) if args.tables else None
    unknown = (only or set()) - set(CHECKED_TABLES)
    if unknown:
        parser.error(f"not a table item-tools reads: {', '.join(sorted(unknown))}")

    if args.modules:
        replay.trainer_state.MODULES_DIR = Path(args.modules)
    allowed = replay_diff.load_allowed(ALLOWED_TABLE_DIFFS)
    applied = {r["name"] for r in run_sql(mysql, args.database, "SELECT `name` FROM `updates`;")}
    applied |= set(args.also.split(",")) if args.also else set()
    replay.sqlcorpus.activate(None, "item-tools-replay-check")  # each file read once for every table, no disk cache
    report = []
    all_differences = []
    for table, key_columns in CHECKED_TABLES.items():
        if only is not None and table not in only:
            continue
        started = time.monotonic()
        schema = replay.table_schema(table, key_columns)
        skipped: list[str] = []
        rows = replay.load_table(
            table, key_columns, applied, on_skip=lambda name, s: skipped.append(f"{name}: {' '.join(s.split())}"),
        )
        left_out = [
            p.name for p in replay.contributing_files(table) if p.name not in applied and p.parent != replay.BASE_DIR
        ]
        live_rows = run_sql(mysql, args.database, f"SELECT * FROM `{table}`;")
        differences, duplicates = compare_table(table, schema, list(rows.values()), live_rows, allowed)
        all_differences += differences
        unexplained = [d for d in differences if d.reason is None]
        live_columns = set(live_rows[0]) if live_rows else set()
        schema_drift = sorted(set(replay.final_columns(table)) ^ live_columns) if live_rows else []
        print(
            f"{table}: live {len(live_rows)}, replay {len(rows)}; "
            f"missing {count(differences, 'missing')} ({count(differences, 'missing', False)} unexplained), "
            f"extra {count(differences, 'extra')} ({count(differences, 'extra', False)} unexplained), "
            f"cells {count(differences, 'cells')} ({count(differences, 'cells', False)} unexplained); "
            f"{len(skipped)} skipped statement(s); {duplicates} duplicate key(s) [{time.monotonic() - started:.1f}s]",
            flush=True,
        )
        if schema_drift:
            print(f"  columns on one side only (replay schema vs live): {', '.join(schema_drift)}")
        for s in skipped[:args.limit]:
            print(f"  skipped: {s[:150]}")
        for d in unexplained[:args.limit]:
            print(f"  {replay_diff.key_text(d.key)} {d.column}: replay {_show(d.replayed)}, live {_show(d.live)}")
        if len(unexplained) > args.limit:
            print(f"  ... {len(unexplained) - args.limit} more unexplained")
        report.append({
            "table": table, "live": len(live_rows), "replay": len(rows), "duplicates": duplicates,
            "skipped": skipped, "left_out": left_out, "schema_drift": schema_drift,
            "differences": [
                {"key": list(d.key), "column": d.column, "replayed": repr(d.replayed), "live": repr(d.live),
                 "reason": d.reason}
                for d in differences
            ],
        })
    stale = replay_diff.explain_whole(all_differences, allowed) if only is None else set()
    for table, key, column in sorted(stale):
        print(f"STALE allow-list entry (matches nothing): {table} {key} {column}")
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=1), encoding="utf-8")
    bad = sum(1 for d in all_differences if d.reason is None)
    duplicates = sum(r["duplicates"] for r in report)
    for r in report:
        if r["duplicates"]:
            print(f"DUPLICATE KEYS: {r['table']}: {r['duplicates']} replayed row(s) share a key with another (the "
                  f"live table cannot hold that: the replay is wrong somewhere)")
    print(f"total: {bad} unexplained difference(s), {duplicates} duplicate replayed key(s) over {len(report)} table(s)")
    return 1 if bad or stale or duplicates else 0


if __name__ == "__main__":
    sys.exit(main())
