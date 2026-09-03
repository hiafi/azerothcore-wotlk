"""
Generic base-⊕-overlay reader for the itemization budget system's reference
and content tables (`item_budget_curve`, `item_budget_template`,
`item_budget_assign`, etc. - see `docs/itemization-changes.md` §3) - the same
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

_EQ_RE = re.compile(r"`(?P<col>\w+)`\s*=\s*(?P<val>-?\d+)")
_IN_RE = re.compile(r"`(?P<col>\w+)`\s*IN\s*\(\s*(?P<vals>[^)]+)\)")
_BETWEEN_RE = re.compile(r"`(?P<col>\w+)`\s*BETWEEN\s*(?P<lo>-?\d+)\s*AND\s*(?P<hi>-?\d+)")


def _contributing_files() -> list[Path]:
    # Recursive glob + sort-by-bare-filename (not full path): pending
    # migrations may live in a topic subdirectory (e.g. `item_weight_system/`,
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


def table_columns(table: str) -> list[str]:
    """Declared column order for `table`, read from whichever migration file
    happens to hold its `CREATE TABLE` - avoids hand-duplicating a column
    list that would silently drift from the real schema (same reasoning as
    `lib/schema.py` asserting against `lib.overlay.item_columns()`, just
    without a stable base file to pin the search to here)."""
    for path in _contributing_files():
        text = path.read_text(encoding="utf-8")
        if f"`{table}`" not in text:
            continue
        m = _CREATE_TABLE_RE.search(text)
        while m and m.group("table") != table:
            m = _CREATE_TABLE_RE.search(text, m.end())
        if not m:
            continue
        depth = 1
        i = m.end()
        n = len(text)
        columns = []
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
                    columns.append(col_m.group("col"))
                line_start = i + 1
            i += 1
        if columns:
            return columns
    raise ValueError(f"no CREATE TABLE `{table}` found in {MERGED_DIR} or {PENDING_DIR}")


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
            explicit_cols = (
                [c.strip(" `") for c in m.group("cols").split(",")] if m.group("cols") else None
            )
            cols = explicit_cols or columns
            tuples, pos = _read_tuples(text, m.end())
            for values in tuples:
                if len(values) != len(cols):
                    print(f"WARNING: {path}: INSERT into `{table}` has {len(values)} values for "
                          f"{len(cols)} columns, skipping", file=sys.stderr)
                    continue
                row = dict(zip(cols, values))
                key = tuple(row[k] for k in key_columns)
                rows[key] = row

    return rows


_cache: dict[str, dict] = {}
_cache_key: tuple | None = None


def _current_cache_key() -> tuple:
    paths = _contributing_files()
    return tuple((str(p), p.stat().st_mtime_ns) for p in paths)


# (table, key_columns) for every table the budget system reads or writes -
# see docs/itemization-changes.md §3. Single source of truth for the set of
# tables lib/budget.py and the webui routes need.
TABLES: dict[str, tuple[str, ...]] = {
    "item_budget_template": ("template_id", "stat_type"),
    "item_budget_template_name": ("template_id",),
    "item_budget_assign": ("entry",),
    "item_budget_curve": ("ilvl",),
    "item_stamina_curve": ("ilvl",),
    "item_armor_curve": ("ilvl", "armor_class"),
    "item_armor_slot_mult": ("inv_type",),
    "item_armor_quality_mult": ("quality",),
    "item_slot_mult": ("inv_type",),
    "item_quality_mult": ("quality",),
    "item_stat_cost": ("stat_type",),
    "item_budget_socket_cost": ("socket_color",),
    "item_budget_set_discount": ("id",),
    "item_weapon_dps_curve": ("ilvl", "quality"),
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
