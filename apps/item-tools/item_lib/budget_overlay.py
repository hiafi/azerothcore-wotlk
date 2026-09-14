"""
Generic base-⊕-overlay reader for the shape-based itemization system's
reference and content tables (`item_budget_curve`, `item_itemization`,
`item_shape`, etc. - see `docs/itemization-phase-2.md` §3) - the same
"what does this look like right now" idea as `lib/overlay.py`, but for a
different SQL idiom.

Unlike `item_template` (on `codestyle-sql.py`'s `not_delete` list, so every
real edit there is a guarded `UPDATE` or an upsert `INSERT` - see
`lib/overlay.py`), none of these tables are protected, and every migration
that's touched them so far (this fork's own budget-system work) uses the
repo's other standard convention instead (`.agents/docs/sql-guidelines.md`:
"every INSERT preceded by a matching DELETE"): `DELETE FROM `table` WHERE
<key match>; INSERT INTO `table` (...) VALUES (...), (...), ...;`. None of
these tables has a stock dump either - they're entirely this fork's own
custom tables, created and populated purely through
`data/sql/updates/{db_world,pending_db_world}/*.sql`, so there's no base file
to start from, just an empty table replayed forward.

Recognizes exactly the three WHERE shapes this repo's own budget-system
migrations use: `` `col` = N ``, `` `col` IN (...) ``, `` `col` BETWEEN A AND
B `` - single column only, even for a composite-key table like
`item_armor_curve` (a `DELETE ... WHERE `ilvl` BETWEEN ...` there removes
every `armor_class` row for those item levels, immediately before the
following INSERT repopulates all of them - safe because within one file a
DELETE is always followed by the INSERT that fully replaces what it just
removed, so processing every DELETE in a file and then every INSERT in that
same file, rather than interleaving them in document order, produces the
same result). Anything else prints a WARNING to stderr and is skipped, same
posture as `lib/overlay.py`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from .overlay import _split_top_level_commas
from .sql_dump import _INSERT_HEAD_RE, _read_tuples

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

_EQ_RE = re.compile(r"`(?P<col>\w+)`\s*=\s*(?P<val>-?\d+)")
_IN_RE = re.compile(r"`(?P<col>\w+)`\s*IN\s*\(\s*(?P<vals>[^)]+)\)")
_BETWEEN_RE = re.compile(r"`(?P<col>\w+)`\s*BETWEEN\s*(?P<lo>-?\d+)\s*AND\s*(?P<hi>-?\d+)")


def _contributing_files() -> list[Path]:
    # Recursive glob + sort-by-bare-filename (not full path): pending
    # migrations may live in a topic subdirectory (e.g. `itemization_templates_v2/`,
    # keeping this fork's own budget-system work visually grouped) rather
    # than flat in PENDING_DIR, and filename order is what actually matters
    # here - it's what the real AzerothCore DBUpdater keys off of too
    # (`UpdateFetcher::Update`'s `applied.find(filePath.filename()...)`),
    # not directory placement.
    files = []
    if MERGED_DIR.is_dir():
        files.extend(MERGED_DIR.glob("**/*.sql"))
    if PENDING_DIR.is_dir():
        files.extend(PENDING_DIR.glob("**/*.sql"))
    return sorted(files, key=lambda p: p.name)


def _strip_line_comments(text: str) -> str:
    """Remove `-- ...` to end-of-line, everywhere outside a single-quoted
    string. This tool's own budget-table migrations put a short `-- comment`
    after individual VALUES tuples (see e.g. rev_1788325484487286047.sql's
    `(1, 5, 6000), -- Intellect 60%`) - real, valid SQL, but
    `lib.sql_dump._read_tuples` only expects a tuple or a terminating `;`
    between commas, not a comment, so it must be stripped before parsing.
    Quote-aware for the same reason `lib.overlay._split_top_level_commas` is:
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
        raw_text = path.read_text(encoding="utf-8")
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
            for clause in _split_top_level_commas(m.group("clauses")):
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


def _matched_keys(where_text: str, key_columns: tuple[str, ...]):
    """(column, set-of-matched-values) for a recognized single-column WHERE
    shape, or None if this WHERE clause doesn't match one of the three known
    shapes (or matches on a column that isn't one of `key_columns`)."""
    m = _IN_RE.search(where_text)
    if m and m.group("col") in key_columns:
        return m.group("col"), {int(v) for v in m.group("vals").split(",")}
    m = _BETWEEN_RE.search(where_text)
    if m and m.group("col") in key_columns:
        lo, hi = int(m.group("lo")), int(m.group("hi"))
        return m.group("col"), set(range(lo, hi + 1))
    m = _EQ_RE.search(where_text)
    if m and m.group("col") in key_columns:
        return m.group("col"), {int(m.group("val"))}
    return None


def resolve_table_rows(table: str, key_columns: tuple[str, ...]) -> dict[tuple, dict]:
    """Every merged then pending migration touching `table`, filename order,
    DELETE-then-INSERT replayed as a full key-range replace. Returns rows
    keyed by a tuple of `key_columns`' values (in the order given), e.g.
    `(66, 1)` for `item_armor_curve`'s `(ilvl, armor_class)`."""
    columns = table_columns(table)
    defaults = table_defaults(table)
    rows: dict[tuple, dict] = {}
    delete_re = re.compile(
        rf"DELETE\s+FROM\s+`{re.escape(table)}`\s+WHERE\s+(?P<where>.+?);",
        re.IGNORECASE | re.DOTALL,
    )

    for path in _contributing_files():
        raw_text = path.read_text(encoding="utf-8")
        if table not in raw_text:
            continue
        text = _strip_line_comments(raw_text)

        for m in delete_re.finditer(text):
            matched = _matched_keys(m.group("where"), key_columns)
            if matched is None:
                print(f"WARNING: {path}: couldn't recognize DELETE FROM `{table}` WHERE shape, "
                      f"skipping: WHERE {m.group('where')[:120]}", file=sys.stderr)
                continue
            col, values = matched
            idx = key_columns.index(col)
            for key in [k for k in rows if k[idx] in values]:
                del rows[key]

        pos = 0
        while True:
            m = _INSERT_HEAD_RE.search(text, pos)
            if not m:
                break
            if m.group("table") != table:
                pos = m.end()
                continue
            # .strip().strip("`"), not .strip(" `") -- an explicit column list wrapped across
            # multiple lines (this session's own SQL style, once the single-line form would blow
            # the 120-col limit -- e.g. item_itemization's real INSERT header) leaves a literal
            # newline at the front of every column after the first on its line, which .strip(" `")
            # can't remove (it only strips the two literal characters given, not whitespace
            # generally) -- confirmed necessary, not hypothetical: this produced a stray
            # "\n  `absorbed_spell_slots`"-shaped key before the fix.
            explicit_cols = (
                [c.strip().strip("`") for c in m.group("cols").split(",")] if m.group("cols") else None
            )
            cols = explicit_cols or columns
            tuples, pos = _read_tuples(text, m.end())
            for values in tuples:
                if len(values) != len(cols):
                    print(f"WARNING: {path}: INSERT into `{table}` has {len(values)} values for "
                          f"{len(cols)} columns, skipping", file=sys.stderr)
                    continue
                row = dict(zip(cols, values))
                if explicit_cols is not None:
                    # An older INSERT written before a later ALTER TABLE added a column lists a
                    # shorter explicit column set - real MySQL backfills the missing column(s)
                    # with their DEFAULT rather than leaving them unset, so this row must too
                    # (confirmed necessary: item_weapon_dps_curve's is_single_slot, added after
                    # some already-merged INSERTs that only ever named ilvl/quality/dps).
                    for col in columns:
                        if col not in row:
                            row[col] = defaults.get(col, 0)
                key = tuple(row[k] for k in key_columns)
                rows[key] = row

    return rows


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
    this process itself just wrote a new pending file."""
    global _cache_key
    key = _current_cache_key()
    if force or key != _cache_key or not _cache:
        _cache.clear()
        for table, key_columns in TABLES.items():
            _cache[table] = resolve_table_rows(table, key_columns)
        _cache_key = _current_cache_key()
    return _cache
