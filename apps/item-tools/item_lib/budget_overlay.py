"""
Base-⊕-overlay reader for the shape-based itemization system's reference and
content tables (`item_budget_curve`, `item_itemization`, `item_shape`, etc. -
see `docs/itemization-phase-2.md` §3) - the same "what does this look like
right now" question as `lib/overlay.py`, answered the same way: the rows come
from `lib/replay.py` (dbc-tools' SQL parser over every migration, in apply
order, with MySQL's statement-by-statement semantics).

None of these tables has a stock dump - they're this fork's own tables,
created and populated purely through `data/sql/updates/{db_world,
pending_db_world}/**.sql` (DELETE + INSERT, `.agents/docs/sql-guidelines.md`),
so the replay starts from an empty table. Their column lists and defaults come
from `_evolve_schemas()` below, which replays `CREATE TABLE`, `RENAME TABLE`
and `ALTER TABLE ... ADD/DROP COLUMN` across the migrations (`item_itemization`
began as `item_budget_assign`); the replay itself carries `item_budget_assign`'s
rows over at the `RENAME TABLE`.

A statement the replay cannot read is skipped and recorded in dbc-tools' skip
log, never guessed at; `get_all()` prints them to stderr (`replay.warn_skips`).
"""

from __future__ import annotations

import re
from pathlib import Path

from . import replay

REPO_ROOT = Path(__file__).resolve().parents[3]
MERGED_DIR = REPO_ROOT / "data/sql/updates/db_world"
PENDING_DIR = REPO_ROOT / "data/sql/updates/pending_db_world"

# Same idea as sql_dump.py's own _CREATE_TABLE_RE/parse_create_table_columns,
# but also matching "CREATE TABLE IF NOT EXISTS" - every budget-system table
# is created that way (idempotent against a migration re-run), unlike
# item_template's plain "CREATE TABLE" in its stock base dump.
_CREATE_TABLE_RE = re.compile(r"CREATE TABLE(?:\s+IF NOT EXISTS)?\s+`(?P<table>\w+)`\s*\(", re.IGNORECASE)
_COLUMN_LINE_RE = re.compile(r"^\s*`(?P<col>\w+)`\s")

# `item_itemization` has no CREATE TABLE of its own anywhere - it started life as
# `item_budget_assign` (CREATE TABLE) and got there via `RENAME TABLE ... TO ...` plus an
# `ALTER TABLE ... ADD/DROP COLUMN` in the same migration (docs/itemization-phase-2.md steps
# 5-6). table_columns() below replays all three statement kinds across every contributing file,
# in order, rather than assuming one CREATE TABLE settles a table's schema for good.
_RENAME_TABLE_RE = re.compile(r"RENAME\s+TABLE\s+`(?P<old>\w+)`\s+TO\s+`(?P<new>\w+)`", re.IGNORECASE)
_ALTER_TABLE_RE = re.compile(r"ALTER\s+TABLE\s+`(?P<table>\w+)`\s*(?P<clauses>.*?);", re.IGNORECASE | re.DOTALL)
_ADD_COLUMN_RE = re.compile(
    r"^ADD\s+(?:COLUMN\s+)?`(?P<col>\w+)`.*?(?:\bAFTER\s+`(?P<after>\w+)`|\bFIRST\b)?\s*$",
    re.IGNORECASE | re.DOTALL,
)
_DROP_COLUMN_RE = re.compile(r"^DROP\s+(?:COLUMN\s+)?`(?P<col>\w+)`\s*$", re.IGNORECASE)
_DEFAULT_RE = re.compile(r"DEFAULT\s+(?:'(?P<quoted>(?:[^'\\]|\\.|'')*)'|(?P<bare>-?\w+))", re.IGNORECASE)


def _parse_default(text: str):
    """The typed value of a column definition's `DEFAULT ...` clause (quoted
    or bare), or `0` if there's no DEFAULT at all - real MySQL requires one
    of DEFAULT/AUTO_INCREMENT/nullability for every column these migrations
    actually use, and every one of them is `NOT NULL ... DEFAULT`, so `0` as
    a fallback only matters for a column this parser fails to recognize at
    all, not a real gap in the schemas this tool reads."""
    m = _DEFAULT_RE.search(text)
    if not m:
        return 0
    raw = m.group("quoted") if m.group("quoted") is not None else m.group("bare")
    if raw.upper() == "NULL":
        return None
    try:
        return float(raw) if ("." in raw or "e" in raw.lower()) else int(raw)
    except ValueError:
        return raw  # a real string default (none of this system's tables have one today)



def _contributing_files() -> list[Path]:
    """Every migration and module SQL file, in apply order (`replay.sql_files()`: subdirectories such as
    `itemization_templates_v2/` included, sorted by bare file name the way DBUpdater keys them)."""
    return replay.sql_files()


# A file without any of these has nothing for the schema evolution below (the cheap test before stripping comments).
# Spelled out in upper, lower and title case rather than IGNORECASE: a case-insensitive search of the ~280 MB of SQL
# took 13 s, this one well under a second.
_SCHEMA_STATEMENT_RE = re.compile(
    r"(?:CREATE|RENAME|ALTER|create|rename|alter|Create|Rename|Alter)\s+(?:TABLE|table|Table)\b"
)


def _strip_line_comments(text: str) -> str:
    """Remove `-- ...` to end-of-line, everywhere outside a single-quoted
    string. This tool's own budget-table migrations put a short `-- comment`
    after individual VALUES tuples (see e.g. rev_1788325484487286047.sql's
    `(1, 5, 6000), -- Intellect 60%`) - real, valid SQL, but
    `lib.sql_dump._read_tuples` only expects a tuple or a terminating `;`
    between commas, not a comment, so it must be stripped before parsing.
    Quote-aware:
    a template name could in principle contain `--` inside its string."""
    out = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "'":
            out.append(ch)
            i += 1
            while i < n:
                if text[i] == "\\" and i + 1 < n:
                    out.append(text[i:i + 2])
                    i += 2
                    continue
                if text[i] == "'":
                    if i + 1 < n and text[i + 1] == "'":
                        out.append("''")
                        i += 2
                        continue
                    out.append("'")
                    i += 1
                    break
                out.append(text[i])
                i += 1
            continue
        if text[i:i + 2] == "--":
            while i < n and text[i] != "\n":
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _create_table_columns(text: str, start: int) -> tuple[list[str], dict[str, object]]:
    """(column names, {column: default value}) inside one `CREATE TABLE ...
    (` block, starting just after its opening paren (`start` = the match's
    `.end()`)."""
    depth = 1
    i = start
    n = len(text)
    columns = []
    defaults: dict[str, object] = {}
    line_start = i
    while i < n and depth > 0:
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                break
        elif ch == "\n":
            line = text[line_start:i]
            col_m = _COLUMN_LINE_RE.match(line)
            if col_m:
                col = col_m.group("col")
                columns.append(col)
                defaults[col] = _parse_default(line)
            line_start = i + 1
        i += 1
    return columns, defaults


_schema_cache: tuple[dict[str, list[str]], dict[str, dict[str, object]]] | None = None
_schema_cache_key: tuple | None = None


def _evolve_schemas() -> tuple[dict[str, list[str]], dict[str, dict[str, object]]]:
    """(every table name's column list, every table's {column: default
    value}), replaying `CREATE TABLE`, `RENAME TABLE ... TO ...`, and `ALTER
    TABLE ... ADD/DROP COLUMN` across every contributing file in order - not
    just the first `CREATE TABLE` found, since `item_itemization` has none
    of its own (it started as `item_budget_assign` and got there via a
    RENAME + ALTER in the same migration, docs/itemization-phase-2.md steps
    5-6). Defaults matter because an older INSERT written before a column
    existed lists an explicit, shorter column set - real MySQL backfills the
    missing column(s) with their DEFAULT, so `resolve_table_rows` needs to
    do the same to build a complete row (confirmed necessary: rev_178838010
    0133766912.sql's `item_weapon_dps_curve` INSERTs list only `(ilvl,
    quality, dps)`, predating `is_single_slot`). `ADD`/`DROP PRIMARY KEY`
    and anything else this repo's migrations don't actually use are
    silently ignored - they don't change the column list."""
    global _schema_cache, _schema_cache_key
    key = _current_cache_key()
    if _schema_cache is not None and key == _schema_cache_key:
        return _schema_cache

    schemas: dict[str, list[str]] = {}
    defaults: dict[str, dict[str, object]] = {}
    for path in _contributing_files():
        raw_text = replay.sqlcorpus.read_text(path)
        if not _SCHEMA_STATEMENT_RE.search(raw_text):
            continue
        text = _strip_line_comments(raw_text)

        for m in _CREATE_TABLE_RE.finditer(text):
            table = m.group("table")
            if table not in schemas:  # first CREATE TABLE wins; a later "IF NOT EXISTS" is a no-op
                schemas[table], defaults[table] = _create_table_columns(text, m.end())

        for m in _RENAME_TABLE_RE.finditer(text):
            old, new = m.group("old"), m.group("new")
            if old in schemas:
                schemas[new] = schemas.pop(old)
                defaults[new] = defaults.pop(old)

        for m in _ALTER_TABLE_RE.finditer(text):
            table = m.group("table")
            if table not in schemas:
                continue
            columns = schemas[table]
            table_defaults = defaults[table]
            for clause in replay.sql_dump._split_top_level_commas(m.group("clauses")):
                clause = clause.strip()
                add_m = _ADD_COLUMN_RE.match(clause)
                if add_m:
                    col, after = add_m.group("col"), add_m.group("after")
                    if col not in columns:
                        if after and after in columns:
                            columns.insert(columns.index(after) + 1, col)
                        else:
                            columns.append(col)
                    table_defaults[col] = _parse_default(clause)
                    continue
                drop_m = _DROP_COLUMN_RE.match(clause)
                if drop_m:
                    col = drop_m.group("col")
                    if col in columns:
                        columns.remove(col)
                    table_defaults.pop(col, None)
                    continue
                # ADD/DROP PRIMARY KEY, etc. - doesn't change the column list, nothing to do.

    _schema_cache = (schemas, defaults)
    _schema_cache_key = key
    return _schema_cache


def table_columns(table: str) -> list[str]:
    """Declared column order for `table` right now, replayed across every
    contributing migration (CREATE/RENAME/ALTER) - avoids hand-duplicating a
    column list that would silently drift from the real schema (same
    reasoning as `lib/schema.py` asserting against `lib.overlay.item_columns()`,
    just without a stable base file to pin the search to here)."""
    schemas, _defaults = _evolve_schemas()
    columns = schemas.get(table)
    if not columns:
        raise ValueError(f"no CREATE TABLE `{table}` (nor a RENAME TABLE that produced it) found "
                          f"in {MERGED_DIR} or {PENDING_DIR}")
    return columns


def table_defaults(table: str) -> dict[str, object]:
    """{column: default value} for `table` right now - see `_evolve_schemas()`."""
    _schemas, defaults = _evolve_schemas()
    return defaults.get(table, {})


def resolve_table_rows(table: str, key_columns: tuple[str, ...]) -> dict[tuple, dict]:
    """Every migration touching `table` (or an earlier name of it), replayed in apply order (`lib/replay.py`).
    Returns rows keyed by a tuple of `key_columns`' values (in the order given), e.g. `(66, 1)` for
    `item_armor_curve`'s `(ilvl, armor_class)`; every row holds every current column (an INSERT written before a
    later `ALTER TABLE ... ADD` gets the column's DEFAULT, as MySQL backfills it)."""
    return replay.load_table(table, key_columns)


_cache: dict[str, dict] = {}
_cache_key: tuple | None = None


def _current_cache_key() -> tuple:
    paths = _contributing_files()
    return tuple((str(p), p.stat().st_mtime_ns) for p in paths)


# (table, key_columns) for every table the shape-based itemization system
# reads or writes - see docs/itemization-phase-2.md §3. Single source of
# truth for the set of tables lib/budget.py, lib/shapes.py, and the webui
# routes need.
TABLES: dict[str, tuple[str, ...]] = {
    "item_itemization": ("entry",),
    "item_shape": ("shape_id",),
    "item_shape_stat": ("shape_id", "rank"),
    "item_shape_rule": ("shape_id", "rule_type", "stat_type"),
    "item_alloc_dist": ("dist_id", "rank"),
    "item_alloc_dist_name": ("dist_id",),
    "item_budget_curve": ("ilvl",),
    "item_stamina_curve": ("ilvl",),
    "item_armor_curve": ("ilvl", "armor_class"),
    "item_armor_slot_mult": ("inv_type",),
    "item_armor_quality_mult": ("quality",),
    "item_slot_mult": ("inv_type",),
    "item_quality_mult": ("quality",),
    "item_stat_cost": ("stat_type",),
    "item_gem_value_curve": ("ilvl",),
    "item_block_value_curve": ("ilvl", "quality"),
    "item_budget_set_discount": ("id",),
    # is_single_slot -- 0=paired (One-Hand/Main Hand/Off Hand), 1=single-slot
    # (Two-Hand/Ranged/Thrown/Relic), §7.7 of the design doc.
    "item_weapon_dps_curve": ("ilvl", "quality", "is_single_slot"),
    "item_weapon_dps_cost": ("id",),
    "item_weapon_dps_spread": ("id",),
    "item_budget_variant": ("entry",),
}


def get_all(force: bool = False) -> dict[str, dict[tuple, dict]]:
    """Cached `{table: {key: row}}` for every table in `TABLES`, same
    mtime-keyed invalidation as `lib.overlay.get_rows()`. `force=True` after
    this process itself just wrote a new pending file. Statements the replay
    skipped are printed to stderr after each fresh load."""
    global _cache_key
    key = _current_cache_key()
    if force or key != _cache_key or not _cache:
        _cache.clear()
        with replay.session(cache=True) as since:
            for table, key_columns in TABLES.items():
                _cache[table] = resolve_table_rows(table, key_columns)
            replay.warn_skips(set(TABLES), since=since)
        _cache_key = _current_cache_key()
    return _cache
