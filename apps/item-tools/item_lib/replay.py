"""
The SQL replay item-tools reads every world-DB table through: dbc-tools' parser (`apps/dbc-tools/lib/sql_dump.py`,
`apply_composite_key_statements`), not a copy of it.

Why shared: item-tools used to carry its own narrow reader (`item_template` UPDATE/INSERT shapes only, base dumps
only for the loot tables, all of a file's DELETEs before its INSERTs for the budget tables). dbc-replay-fix made
dbc-tools' parser reproduce the live DB for every table it replays (`replay_diff.py --whole`); this module gives
item-tools the same answer instead of a second parser with its own gaps. What the parser reads and what it still
skips: `.agents/docs/systems/dbc-tools.md`, "What the SQL replay reads, the skip log, and the whole-table check".

**Files, in apply order** (`contributing_files`): the base dump (when the table has one), then every SQL file that
names the table, in DBUpdater's order (dbc-tools' `trainer_state.update_files`, the one list both tools share):
  1. `data/sql/updates/db_world/**` (subdirectories too, e.g. `itemization_templates_v2/`, sorted by bare file
     name), with dbc-tools' frozen replay inputs spliced in at the slot they ran (`lib/frozen_replay.py`:
     mod-progression's phase 0 wrote `item_template` and the loot tables);
  2. `data/sql/updates/pending_db_world/**`, `data/sql/custom/db_world/**` and module SQL
     (`modules/*/data/sql/db-world/**`) together, by bare file name: DBUpdater's second pass.

**Semantics are MySQL's**: an UPDATE's guard (`AND col = <old value>`) is honoured, a DELETE + INSERT runs in
statement order, `INSERT IGNORE`, `TRUNCATE`, `ALTER TABLE`, session variables and expressions are read.
`RENAME TABLE a TO b` carries `a`'s rows over to `b` (`item_budget_assign` -> `item_itemization`). A column an
INSERT left out takes the schema default, as MySQL fills it.

**No skip is silent**: a statement the parser cannot apply is recorded in dbc-tools' skip log (`sqlcorpus.SKIPS`)
with its reason, and so is a statement the head scanner cannot see (`trainer_state._record_invisible`).
`skip_summary()` / `warn_skips()` report them; the webui prints them to stderr after each load.

Inside a dbc-tools run (`sqlcorpus.active()`), the replay of the immutable prefix (base dump, promoted files,
frozen inputs) is cached on disk like every dbc-tools loader; outside one it is a plain replay.
"""

from __future__ import annotations

import contextlib
import re
import sys
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[3]
DBC_TOOLS = REPO_ROOT / "apps" / "dbc-tools"


def _import_dbc_tools():
    """dbc-tools' `lib` package (its directory goes on `sys.path`, as dbc-tools' own scripts do). Refuses a different
    package already imported as `lib`, which would otherwise be used silently."""
    loaded = sys.modules.get("lib")
    if loaded is not None:
        origin = Path(getattr(loaded, "__file__", "") or "").resolve()
        if DBC_TOOLS.resolve() / "lib" not in origin.parents:
            raise ImportError(f"item-tools needs apps/dbc-tools/lib as `lib`, but `lib` is already {origin}")
    elif str(DBC_TOOLS) not in sys.path:
        sys.path.append(str(DBC_TOOLS))
    from lib import frozen_replay, sql_dump, sqlcorpus, trainer_state  # noqa: PLC0415

    return frozen_replay, sql_dump, sqlcorpus, trainer_state


frozen_replay, sql_dump, sqlcorpus, trainer_state = _import_dbc_tools()

BASE_DIR = REPO_ROOT / "data/sql/base/db_world"
MERGED_DIR = REPO_ROOT / "data/sql/updates/db_world"
PENDING_DIR = REPO_ROOT / "data/sql/updates/pending_db_world"

_RENAME_TABLE_RE = re.compile(r"RENAME\s+TABLE\s+`(?P<old>\w+)`\s+TO\s+`(?P<new>\w+)`\s*;", re.IGNORECASE)
_PRIMARY_KEY_RE = re.compile(r"PRIMARY KEY\s*\((?P<cols>[^)]*)\)", re.IGNORECASE)


def base_file(table: str) -> Path | None:
    path = BASE_DIR / f"{table}.sql"
    return path if path.is_file() else None


def sql_files() -> list[Path]:
    """Every non-base SQL file a replay may read, in apply order (see the module docstring)."""
    return trainer_state.update_files(MERGED_DIR, PENDING_DIR)


def _is_stable(path: Path) -> bool:
    """Promoted and frozen files never change, so their replay can be cached; pending and module files can."""
    return MERGED_DIR in path.parents or frozen_replay.is_frozen(path)


def _mentions(path: Path, names: tuple[str, ...]) -> bool:
    # `loose`: a file that names the table only unquoted is opened too, so its statements are recorded as skips.
    return any(sqlcorpus.mentions(path, name, loose=True) for name in names)


def table_names(table: str, files: list[Path] | None = None) -> tuple[str, ...]:
    """`table` and every earlier name it had (`RENAME TABLE old TO table`), oldest first."""
    names = [table]
    for path in reversed(files if files is not None else sql_files()):
        if not _mentions(path, (names[0],)):
            continue
        for m in _RENAME_TABLE_RE.finditer(sqlcorpus.read_text(path)):
            if m.group("new") == names[0] and m.group("old") not in names:
                names.insert(0, m.group("old"))
    return tuple(names)


def contributing_files(table: str, applied: set[str] | None = None) -> list[Path]:
    """The base dump (if any) and every file that names `table` (or an earlier name of it), in apply order. `applied`
    (the live `updates` table's file names) leaves out what the live DB has not run; the base dump is always kept."""
    files = sql_files()
    names = table_names(table, files)
    base = base_file(table)
    found = [p for p in files if _mentions(p, names) and (applied is None or p.name in applied)]
    return ([base] if base else []) + found


class Schema:
    """A table's column order, key, defaults and string columns: from its base dump's `CREATE TABLE`, else (a table
    a migration created) from item-tools' schema evolution over the migrations (`budget_overlay`)."""

    def __init__(self, columns: tuple[str, ...], key_columns: tuple[str, ...], defaults: dict,
                 string_columns: frozenset, int_columns: frozenset | None = None):
        self.columns = columns
        self.key_columns = key_columns
        self.defaults = defaults
        self.string_columns = string_columns
        self.int_columns = int_columns  # None (a table with no base dump): not known, nothing is rounded


def table_schema(table: str, key_columns: tuple[str, ...] | None = None) -> Schema:
    base = base_file(table)
    if base is not None:
        columns = tuple(sql_dump.parse_create_table_columns(base, table))
        if key_columns is None:
            m = _PRIMARY_KEY_RE.search(sql_dump._create_table_body(base, table))
            key_columns = tuple(c.strip().strip("`") for c in m.group("cols").split(",")) if m else columns
        defaults = sql_dump.parse_create_table_defaults(base, table)
        strings = sql_dump.parse_create_table_string_columns(base, table)
        # A string column with no DEFAULT clause (TEXT) is '' when an INSERT leaves it out (MySQL's implicit default
        # for NOT NULL text in non-strict mode); a numeric one with none is 0.
        for column in columns:
            defaults.setdefault(column, "" if column in strings else 0)
        return Schema(columns, key_columns, defaults, strings, sql_dump.parse_create_table_int_columns(base, table))
    from . import budget_overlay  # noqa: PLC0415 - budget_overlay imports this module

    columns = tuple(budget_overlay.table_columns(table))
    defaults = dict(budget_overlay.table_defaults(table))
    if key_columns is None:
        key_columns = budget_overlay.TABLES.get(table) or columns
    strings = frozenset(c for c, v in defaults.items() if isinstance(v, str))
    return Schema(columns, key_columns, defaults, strings)


def _rekey(rows: dict, key_columns: tuple[str, ...]) -> None:
    """Files each row under the key its values now hold (an UPDATE that set a key column leaves the row under its old
    key; MySQL moves it)."""
    moved = [(k, r) for k, r in rows.items() if k != tuple(r.get(c) for c in key_columns)]
    for old, _ in moved:
        del rows[old]
    for _, row in moved:
        rows[tuple(row.get(c) for c in key_columns)] = row


def _sets_key(text: str, key_columns: tuple[str, ...]) -> bool:
    return any(re.search(rf"\bSET\b[^;]*`{re.escape(c)}`\s*=", text, re.IGNORECASE) for c in key_columns)


def _names_in_effect(files: list[Path], names: tuple[str, ...]) -> dict[Path, str]:
    """The name `files[i]` starts under: the oldest name until the file that renames it, then the next one."""
    current = names[0]
    result: dict[Path, str] = {}
    for path in files:
        result[path] = current
        if path.parent == BASE_DIR or len(names) == 1 or not _mentions(path, (current,)):
            continue
        for m in _RENAME_TABLE_RE.finditer(sqlcorpus.read_text(path)):
            if m.group("old") == current and m.group("new") in names:
                current = m.group("new")
    return result


def _step(rows: dict, path: Path, name: str, names: tuple[str, ...], schema: Schema,
          on_skip: Callable[[str, str], None] | None) -> dict:
    """Replays one file onto `rows` under `name` (the table's name when the file starts), switching to the new name
    at a `RENAME TABLE name TO ...`."""
    text = sqlcorpus.read_text(path)
    segments: list[tuple[str, str]] = []  # (name in effect, text)
    pos = 0
    if len(names) > 1:
        for m in _RENAME_TABLE_RE.finditer(text):
            if m.group("old") == name and m.group("new") in names:
                segments.append((name, text[pos:m.start()]))
                pos = m.end()
                name = m.group("new")
    segments.append((name, text[pos:]))
    for current, chunk in segments:
        if current not in chunk:
            continue
        report = (lambda s: on_skip(path.name, s)) if on_skip else None
        sql_dump.apply_composite_key_statements(
            rows, schema.columns, schema.key_columns, current, chunk, report, defaults=schema.defaults,
            source=path.name, int_columns=schema.int_columns,
        )
        if path.parent != BASE_DIR:
            trainer_state._record_invisible(current, path, chunk, report)
    if path.parent != BASE_DIR and _sets_key(text, schema.key_columns):
        _rekey(rows, schema.key_columns)
    return rows


def load_table(
    table: str, key_columns: tuple[str, ...] | None = None, applied: set[str] | None = None,
    on_skip: Callable[[str, str], None] | None = None, files: list[Path] | None = None,
) -> dict[tuple, dict]:
    """`{key tuple: row}` for `table` as the live DB holds it: base dump plus every file in apply order
    (`contributing_files`), replayed with dbc-tools' parser. Every row carries every column of the table's schema (an
    omitted one takes its default). `applied` and `on_skip(file name, statement start)` are for the whole-table
    check (`apps/item-tools/replay_check.py`); `files` replaces the non-base files (a test's selection)."""
    schema = table_schema(table, key_columns)
    if files is None:
        files = contributing_files(table, applied)
    else:
        base = base_file(table)
        files = ([base] if base else []) + [p for p in files if p != base]
    names = table_names(table)
    name_at = _names_in_effect(files, names)

    def step(rows: dict, path: Path) -> dict:
        return _step(rows, path, name_at[path], names, schema, on_skip)

    n = 0
    while n < len(files) and (files[n].parent == BASE_DIR or _is_stable(files[n])):
        n += 1
    if applied is None and on_skip is None:
        rows = sqlcorpus.checkpointed(
            "item_tools_rows", (table, schema.key_columns, schema.columns, names), files[:n], dict, step,
        )
    else:  # the check: never from (or into) the cache, since `applied` / `on_skip` are not part of its key
        rows = {}
        for path in files[:n]:
            step(rows, path)
    for path in files[n:]:
        step(rows, path)
    columns = final_columns(table, files, names)
    for row in rows.values():
        for column in columns:
            if column not in row:
                row[column] = schema.defaults.get(column, "" if column in schema.string_columns else 0)
    return rows


_ALTER_HEAD_RE = re.compile(r"ALTER\s+TABLE\s+`(?P<table>\w+)`", re.IGNORECASE)


def final_columns(table: str, files: list[Path] | None = None, names: tuple[str, ...] | None = None) -> list[str]:
    """The table's columns after every `ALTER TABLE` in `files` (base dump's `CREATE TABLE` onwards; `creature.id1`
    became `id`, 2026_06_16_00). A table with no base dump already has its evolved columns (`table_schema`)."""
    schema = table_schema(table)
    columns = list(schema.columns)
    if base_file(table) is None:
        return columns
    files = files if files is not None else contributing_files(table)
    names = names or table_names(table)
    for path in files:
        if path.parent == BASE_DIR:
            continue
        text = sqlcorpus.read_text(path)
        for m in _ALTER_HEAD_RE.finditer(text):
            if m.group("table") in names and not sql_dump._in_line_comment(text, m.start()):
                sql_dump._apply_alter({}, columns, text[m.end():sql_dump._statement_end(text, m.end())])
    return columns


def load_keyed(table: str, key_column: str, applied: set[str] | None = None) -> dict:
    """`load_table` for a single-column key, as `{key value: row}`."""
    return {key[0]: row for key, row in load_table(table, (key_column,), applied).items()}


CACHE_DIR = REPO_ROOT / "var" / "item-tools-cache"


def cache_version() -> str:
    """The code a cached replay depends on: item-tools' readers and dbc-tools' parser package."""
    return sqlcorpus.code_version([Path(__file__).resolve().parent, DBC_TOOLS / "lib"])


@contextlib.contextmanager
def session(cache: bool = False):
    """Reads each SQL file once for every table loaded inside the block: when no dbc-tools corpus is active (the
    webui, a test), one is activated for the block and dropped after it, so its file texts and statement indexes do
    not stay in memory. `cache` also keeps each table's replay of the immutable files (base dump, promoted, frozen)
    on disk under `var/item-tools-cache/` (dbc-tools' snapshot cache: keyed by the files' content hashes and
    `cache_version()`), so only pending and module SQL is replayed after the first load. Inside a dbc-tools run the
    active corpus is used as it is. Yields the skip log position at the start, for `warn_skips(since=...)`; skips
    recorded in the block are kept after it (the corpus' reset would otherwise clear them)."""
    if sqlcorpus.active() is not None:
        yield len(sqlcorpus.SKIPS.entries)
        return
    kept = list(sqlcorpus.SKIPS.entries)
    sqlcorpus.activate(CACHE_DIR if cache else None, cache_version() if cache else "item-tools")  # clears SKIPS
    sqlcorpus.SKIPS.entries.extend(kept)
    try:
        yield len(kept)
    finally:
        recorded = list(sqlcorpus.SKIPS.entries)
        sqlcorpus.deactivate()  # clears SKIPS again
        sqlcorpus.SKIPS.entries.extend(recorded)


def skips(tables: set[str] | None = None, since: int = 0) -> list:
    """The skip log entries (dbc-tools' `sqlcorpus.Skip`) for `tables` (all when None), one per statement, from
    position `since` of the log on."""
    log = sqlcorpus.SkipLog()
    log.entries = sqlcorpus.SKIPS.entries[since:]
    return [s for s in log.unique() if tables is None or s.table in tables]


def skip_summary(tables: set[str] | None = None, since: int = 0) -> list[str]:
    log = sqlcorpus.SkipLog()
    log.entries = sqlcorpus.SKIPS.entries[since:]
    return log.summary(tables)


def warn_skips(tables: set[str] | None = None, since: int = 0, file=None) -> None:
    """Prints the skip summary the way dbc-tools' generate.py does (`WARNING: replay: ...`), when there is
    anything."""
    found = skips(tables, since)
    if not found:
        return
    out = file if file is not None else sys.stderr
    print(f"WARNING: replay: {len(found)} SQL statement(s) could not be replayed; the rows they touch may not "
          f"match live:", file=out)
    for line in skip_summary(tables, since):
        print(f"  {line}", file=out)
