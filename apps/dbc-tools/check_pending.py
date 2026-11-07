#!/usr/bin/env python3
"""
Pre-import check of the pending world revs (dbc-tools-scoped-generate R-S1 B1): run right before `ac-db-import`.

Usage: python3 apps/dbc-tools/check_pending.py [--pending-dir DIR] [--allow-drop]

The drop guard in generate.py judges a run against what is live when the run is made. A rev written earlier, before
another branch's rows went live (the 2026-11-07 wave 1 rev), passes it and does the damage at import. This command
takes the pending files the live `updates` table has not applied yet (`SELECT name FROM updates`: pending revs, custom
and module SQL, by bare file name like DBUpdater) and reads back what they would do to the guarded custom rows
(lib/drop_guard.py's tables: spell_dbc, talent_dbc, item_dbc, item_template, creature_template, ...), all of them
together in apply order:

- **drop**: a live custom row they DELETE and none of them re-inserts;
- **rewrite**: a live custom row they re-insert with content that differs from the live row.

Each is refused (exit 1) when the live row is not this checkout's to change from the rev's point of view:

- no SQL file of this checkout ever INSERTed that id (drop), or its live content (rewrite; an UPDATE naming the id
  counts as a possible writer); or
- the file that wrote the live row is itself a second-pass file applied *after* the rev in name order: the rev was
  written before that row existed (a stale branch) and would wipe or revert it.

Anything else is this checkout's own removal or edit and is listed as a note. Read-only: SELECTs on the world DB
through `$DBC_TOOLS_MYSQL` / `LIVE_DB_MYSQL` (this checkout's or the main checkout's lib/local_config.py), nothing
written. Exit 0 ok, 1 refused, 2 no DB command / DB error. `--allow-drop` reports and exits 0.

Known limit: a rev written by a stale checkout *after* the other branch's row went live, deleting it, is judged like a
deliberate removal here (a later name than the row's writer); generate.py's write-time guard catches that case when
the run can see the live DB.
"""

from __future__ import annotations

import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from lib import drop_guard, scope, source, trainer_state  # noqa: E402

PENDING_SQL_DIR = TOOL_ROOT.parents[1] / "data" / "sql" / "updates" / "pending_db_world"


def _shown(ids) -> str:
    ids = sorted(ids)
    return ", ".join(map(str, ids[:20])) + (" ..." if len(ids) > 20 else "")


def run(argv: list[str], *, command=None, applied_reader=None, live_reader=drop_guard.live_ids,
        rows_reader=drop_guard.live_rows, out=print) -> int:
    pending_dir = PENDING_SQL_DIR
    allow = "--allow-drop" in argv
    if "--pending-dir" in argv:
        pending_dir = Path(argv[argv.index("--pending-dir") + 1]).resolve()
    command = command if command is not None else drop_guard.mysql_command()
    if command is None:
        out("ERROR: check-pending: no live DB command (set $DBC_TOOLS_MYSQL or LIVE_DB_MYSQL in lib/local_config.py)")
        return 2
    ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
    try:
        if applied_reader is not None:
            applied = applied_reader()
        else:
            applied = {line.strip() for line in drop_guard.run_sql(command, "SELECT `name` FROM `updates`;").split()}
        all_files = trainer_state.update_files(pending_dir=pending_dir)
        second = trainer_state.second_pass_files(pending_dir=pending_dir)
        unapplied = [p for p in second if p.name not in applied]
        if not unapplied:
            out("check-pending: every pending file is applied live, nothing to check")
            return 0
        out(f"check-pending: {len(unapplied)} pending file(s) not applied live: "
            f"{', '.join(p.name for p in unapplied[:10])}{' ...' if len(unapplied) > 10 else ''}")
        live = live_reader(command, list(drop_guard.GUARDED_TABLES), ids_cfg)
        texts = {p: p.read_text(encoding="utf-8") for p in unapplied}
        combined = "\n".join(texts.values())
        drops = drop_guard.sql_drops(combined, live)
        inserted = drop_guard.inserted_rows(combined, set(live))
        current_rows = {}
        for table, rows in inserted.items():
            ids = sorted(i for i in rows if i in live.get(table, ()))
            current_rows[table] = rows_reader(command, table, ids) if ids else {}
    except drop_guard.GuardError as error:
        out(f"ERROR: check-pending: {error}")
        return 2

    applied_files = [p for p in all_files if p not in set(unapplied)]
    second_names = {p.name for p in second}
    problems: dict[tuple, list[int]] = {}  # (table, what, reason, rev, writer) -> ids

    def first_file(table: str, entry_id: int, kind: str) -> Path | None:
        """The first unapplied file that deletes (kind "delete") or inserts ("insert") the id."""
        for path, text in texts.items():
            ranges, deleted, ins = scope.deleted_and_inserted(text, {table: drop_guard.GUARDED_TABLES[table][0]})[table]
            if kind == "delete" and (entry_id in deleted or drop_guard._in(entry_id, ranges)):
                return path
            if kind == "insert" and entry_id in ins:
                return path
        return None

    def judge(table: str, entry_id: int, writers: list[Path], rev: Path | None, what: str) -> bool:
        """Records a problem and returns True, or False (this checkout's own change)."""
        rev_name = rev.name if rev is not None else "?"
        if not writers:
            problems.setdefault((table, what, "unknown", rev_name, ""), []).append(entry_id)
            return True
        last = writers[-1]
        if rev is not None and last.name in second_names and last.name > rev.name:
            problems.setdefault((table, what, "stale", rev_name, last.name), []).append(entry_id)
            return True
        return False

    for table, ids in sorted(drops.items()):
        hits = drop_guard.insert_hits(table, ids, [drop_guard.BASE_SQL_DIR / f"{table}.sql", *applied_files])
        own = []
        for entry_id in ids:
            writers = [path for path, _row in hits.get(entry_id, [])]
            if not judge(table, entry_id, writers, first_file(table, entry_id, "delete"), "deleted"):
                own.append(entry_id)
        if own:
            out(f"note: check-pending: {table}: deleting {len(own)} live row(s) this checkout wrote: {_shown(own)}")
    for table, rows in sorted(inserted.items()):
        current = current_rows.get(table, {})
        differing = {i: current[i] for i in rows if i in current and not drop_guard.same_content(rows[i], current[i])}
        if not differing:
            continue
        files = [drop_guard.BASE_SQL_DIR / f"{table}.sql", *applied_files]
        writers = drop_guard.content_writers(table, differing, files)
        lenient = drop_guard.updated_ids(table, set(differing) - set(writers), files)
        own = []
        for entry_id in sorted(differing):
            if entry_id in lenient and entry_id not in writers:
                own.append(entry_id)
                continue
            if not judge(table, entry_id, writers.get(entry_id, []), first_file(table, entry_id, "insert"),
                         "rewritten"):
                own.append(entry_id)
        if own:
            out(f"note: check-pending: {table}: updating {len(own)} live row(s): {_shown(own)}")
    if not problems:
        out("check-pending: ok, no unapplied pending file deletes or reverts another branch's live custom row")
        return 0
    for (table, what, reason, rev, writer), ids in sorted(problems.items()):
        if reason == "unknown":
            out(f"ERROR: check-pending: {rev}: {table}: {len(ids)} live row(s) {what} that no SQL file of this "
                f"checkout wrote: {_shown(ids)}")
        else:
            out(f"ERROR: check-pending: {rev}: {table}: {len(ids)} live row(s) {what}, written by {writer}, which is "
                f"applied after {rev}: the rev predates them (a stale branch's rev): {_shown(ids)}")
    if allow:
        out("WARNING: check-pending: --allow-drop, exiting 0 anyway")
        return 0
    out("ERROR: check-pending: do not import; regenerate the offending revs on a tree with the other branch merged "
        "(or pass --allow-drop)")
    return 1


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
