"""
Resolves "what `item_template` looks like right now": the base client dump
(`data/sql/base/db_world/item_template.sql`) with every already-merged
migration (`data/sql/updates/db_world/*.sql`) and every still-pending one
(`data/sql/updates/pending_db_world/*.sql`) that touches `item_template`
replayed on top, in filename order - the same base-⊕-overlay idea
`apps/dbc-tools/lib/resolve.py` uses for `spell_dbc`, adapted for a table
that (per `apps/codestyle/codestyle-sql.py`'s `not_delete` list) is only
ever touched with `UPDATE ... WHERE` or `INSERT ... ON DUPLICATE KEY
UPDATE`, never `DELETE`+`INSERT` - see `lib/emit.py` for the writing half
of that convention.

This only needs to recover *what changed*, not evaluate real SQL WHERE
semantics: every migration in this repo's history runs exactly once
against the state it was written against, so a `WHERE` clause's job here
is just "which entry/entries does this touch", not "does the guard still
hold" - `AND` col=<old value> guards (written so a stray re-run of an
already-applied file is a no-op) are parsed and ignored, not evaluated.
Anything with a WHERE shape this doesn't recognize is skipped with a
warning printed to stderr rather than guessed at.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from .sql_dump import parse_create_table_columns, read_table_dump, _read_tuples

REPO_ROOT = Path(__file__).resolve().parents[3]
BASE_FILE = REPO_ROOT / "data/sql/base/db_world/item_template.sql"
MERGED_DIR = REPO_ROOT / "data/sql/updates/db_world"
PENDING_DIR = REPO_ROOT / "data/sql/updates/pending_db_world"


def _contributing_files() -> list[Path]:
    # Recursive glob + sort-by-bare-filename (not full path): pending
    # migrations may live in a topic subdirectory (e.g. `item_weight_system/`)
    # rather than flat in PENDING_DIR, and filename order is what actually
    # matters here - it's what the real AzerothCore DBUpdater keys off of too
    # (`UpdateFetcher::Update`'s `applied.find(filePath.filename()...)`), not
    # directory placement. Same helper/rationale as `budget_overlay.py`'s.
    files = []
    if MERGED_DIR.is_dir():
        files.extend(MERGED_DIR.glob("**/*.sql"))
    if PENDING_DIR.is_dir():
        files.extend(PENDING_DIR.glob("**/*.sql"))
    return sorted(files, key=lambda p: p.name)


_UPDATE_RE = re.compile(
    r"UPDATE\s+`item_template`\s+SET\s+(?P<sets>.+?)\s+WHERE\s+(?P<where>.+?);",
    re.IGNORECASE | re.DOTALL,
)
_INSERT_RE = re.compile(
    r"INSERT\s+INTO\s+`item_template`\s*\((?P<cols>[^)]*)\)\s*VALUES\s*",
    re.IGNORECASE,
)
_ENTRY_EQ_RE = re.compile(r"`entry`\s*=\s*(\d+)", re.IGNORECASE)
_ENTRY_IN_RE = re.compile(r"`entry`\s*IN\s*\(([^)]+)\)", re.IGNORECASE)


def _split_top_level_commas(s: str) -> list[str]:
    """Split on ',' outside of single-quoted strings (with backslash- and
    doubled-quote escaping, same rules as the base dump's own strings)."""
    parts = []
    buf = []
    i, n = 0, len(s)
    while i < n:
        ch = s[i]
        if ch == "'":
            buf.append(ch)
            i += 1
            while i < n:
                if s[i] == "\\" and i + 1 < n:
                    buf.append(s[i : i + 2])
                    i += 2
                    continue
                if s[i] == "'":
                    if i + 1 < n and s[i + 1] == "'":
                        buf.append("''")
                        i += 2
                        continue
                    buf.append("'")
                    i += 1
                    break
                buf.append(s[i])
                i += 1
            continue
        if ch == ",":
            parts.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    parts.append("".join(buf))
    return parts


def _parse_scalar(token: str):
    token = token.strip()
    if token.upper() == "NULL":
        return None
    if token.startswith("'") and token.endswith("'"):
        inner = token[1:-1].replace("''", "'")
        return re.sub(r"\\(.)", r"\1", inner)
    try:
        return int(token)
    except ValueError:
        return float(token)


def _split_assignments(sets_text: str) -> list[tuple[str, str]]:
    """`col = value` pairs as (column, raw RHS text) - RHS is left
    unevaluated since a handful of real migrations (e.g. `` `Flags` =
    `Flags`|4096|32768 ``) self-reference the column's *current* value
    rather than assigning a literal, which can only be resolved per-entry
    (see `_resolve_value`), not once for the whole SET clause."""
    pairs = []
    for piece in _split_top_level_commas(sets_text):
        m = re.match(r"\s*`(\w+)`\s*=\s*(.*)$", piece, re.DOTALL)
        if m:
            pairs.append((m.group(1), m.group(2)))
    return pairs


def _resolve_value(col: str, raw: str, current_row: dict):
    """A plain literal, or a same-column bitwise-OR-with-itself expression
    (the one self-referencing shape seen in this repo's history so far -
    `data/sql/updates/db_world/2026_06_01_00.sql`'s `` `Flags` =
    `Flags`|4096|32768 ``) resolved against `current_row`'s value for `col`
    before this statement applies."""
    or_m = re.match(rf"^\s*`{re.escape(col)}`\s*((?:\|\s*\d+\s*)+)$", raw)
    if or_m:
        value = current_row.get(col) or 0
        for num in re.findall(r"\|\s*(\d+)", or_m.group(1)):
            value |= int(num)
        return value
    return _parse_scalar(raw)


def _entries_from_where(where_text: str) -> list[int] | None:
    m = _ENTRY_IN_RE.search(where_text)
    if m:
        return [int(tok) for tok in m.group(1).split(",")]
    m = _ENTRY_EQ_RE.search(where_text)
    if m:
        return [int(m.group(1))]
    return None


def _apply_updates(text: str, rows: dict[int, dict], source: str) -> None:
    for m in _UPDATE_RE.finditer(text):
        entries = _entries_from_where(m.group("where"))
        if entries is None:
            print(f"WARNING: {source}: couldn't find `entry` in WHERE clause, skipping: "
                  f"WHERE {m.group('where')[:120]}", file=sys.stderr)
            continue
        assignments = _split_assignments(m.group("sets"))
        for entry in entries:
            row = rows.get(entry)
            if row is None:
                continue
            for col, raw in assignments:
                row[col] = _resolve_value(col, raw, row)


def _apply_inserts(text: str, rows: dict[int, dict], source: str) -> None:
    pos = 0
    while True:
        m = _INSERT_RE.search(text, pos)
        if not m:
            break
        cols = [c.strip(" `") for c in m.group("cols").split(",")]
        values, pos = _read_single_tuple_then_skip_to_semicolon(text, m.end())
        if len(values) != len(cols):
            print(f"WARNING: {source}: item_template INSERT has {len(values)} values for "
                  f"{len(cols)} columns, skipping", file=sys.stderr)
            continue
        row = dict(zip(cols, values))
        entry = row.get("entry")
        if entry is None:
            continue
        rows[entry] = {**rows.get(entry, {}), **row}


def _read_single_tuple_then_skip_to_semicolon(text: str, start: int) -> tuple[list, int]:
    """Read exactly one `(...)` value-tuple starting at `text[start]`
    (skipping leading whitespace), then jump straight to the next
    terminating ';' - regardless of what sits between the tuple and it (an
    `ON DUPLICATE KEY UPDATE ...` clause, in this tool's own emitted shape;
    see `lib/emit.py`). Only single-row inserts are expected for
    `item_template` (one new item per statement), so unlike
    `sql_dump._read_tuples` this deliberately doesn't handle a
    comma-separated multi-row VALUES list."""
    i = start
    n = len(text)
    while text[i] in " \t\r\n":
        i += 1
    if text[i] != "(":
        raise ValueError(f"expected '(' at offset {i}, found {text[i]!r}")
    depth = 0
    j = i
    end = None
    while j < n:
        ch = text[j]
        if ch == "'":
            j += 1
            while j < n:
                if text[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if text[j] == "'":
                    if j + 1 < n and text[j + 1] == "'":
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                end = j + 1
                break
        j += 1
    if end is None:
        raise ValueError(f"unterminated '(' starting at offset {i}")
    values, _ = _read_tuples(text[i:end] + ";", 0)
    semi = text.index(";", end)
    return values[0], semi + 1


def resolve_current_rows() -> dict[int, dict]:
    """Base + every merged + every pending `item_template` change, applied
    in order. Column order comes from the base file's own CREATE TABLE, not
    a hand-maintained list, so a schema change is picked up automatically."""
    columns = parse_create_table_columns(BASE_FILE, "item_template")
    rows = read_table_dump(BASE_FILE, "item_template", columns, "entry")

    files = _contributing_files()

    for path in files:
        text = path.read_text(encoding="utf-8")
        if "item_template" not in text:
            continue
        _apply_updates(text, rows, str(path))
        _apply_inserts(text, rows, str(path))

    return rows


def item_columns() -> list[str]:
    return parse_create_table_columns(BASE_FILE, "item_template")


_cache: dict = {"key": None, "rows": None}


def _cache_key() -> tuple:
    """Every contributing file's mtime, so a save (new pending file) or a
    manual edit to any of these invalidates the cache automatically -
    cheaper than re-parsing ~46k base rows on every request when nothing
    has changed."""
    paths = [BASE_FILE] + _contributing_files()
    return tuple((str(p), p.stat().st_mtime_ns) for p in paths)


def get_rows(force: bool = False) -> dict[int, dict]:
    """Cached `resolve_current_rows()` - the webui's routes should call
    this instead of `resolve_current_rows()` directly. `force=True` (after
    this process itself just wrote a new pending file) skips the mtime
    check, since a file written in the same second the cache was built can
    otherwise share an mtime with the cached read on some filesystems."""
    key = _cache_key()
    if force or key != _cache["key"]:
        _cache["rows"] = resolve_current_rows()
        _cache["key"] = _cache_key()  # re-read after resolving, in case a
        # file changed mid-resolve; cheap relative to the resolve itself.
    return _cache["rows"]
