"""
A small, narrowly-scoped reader for the `INSERT INTO` table `VALUES (...);`
statements mysqldump produces (the shape of every `data/sql/base/db_world/
*_dbc.sql` file). Not a general SQL parser — just enough to reconstruct
`{ID: {column: value}}` for one table, which is what `pull.py` needs to
reverse-import existing rows into source form.

`read_table_rows` is the same parser for plain (non-DBC-backed) world-DB
tables that have no single-column primary key — e.g. `trainer_spell`
(keyed on `TrainerId, SpellId`) — so it returns every row as a plain list
instead of collapsing them into a dict keyed by one column.

`apply_statements` is a different shape of the same not-a-general-parser
idea: a best-effort replay of DELETE/INSERT/UPDATE statements touching one
table, applied in file order, used by `state.py` to overlay already-promoted
migrations (`data/sql/updates/db_world/*.sql`) on top of a base dump. It
covers exactly the DELETE/INSERT shapes `sql_out.py` emits plus the
hand-written DELETE/UPDATE shapes seen in this repo's migration history —
see its own docstring for what happens (safely) when it meets a shape it
doesn't recognize.
"""

from __future__ import annotations

import re
from pathlib import Path

from .dbcfmt import DbcTable

_INSERT_HEAD_RE = re.compile(
    r"INSERT\s+INTO\s+`(?P<table>\w+)`\s*(?:\((?P<cols>[^)]*)\))?\s*VALUES\s*",
    re.IGNORECASE,
)


def _read_value(text: str, i: int, terminators: str = ",)") -> tuple[object, int]:
    """Parse a single SQL literal (quoted string, NULL, or number) starting at
    `text[i]` (leading whitespace already skipped by the caller). Returns
    (value, index_just_past_the_literal). `terminators` bounds a bare numeric
    token - widen it for a value not immediately followed by ',' or ')' (e.g.
    the last assignment in an `UPDATE ... SET` clause, followed by whitespace
    then `WHERE`)."""
    n = len(text)
    if text[i] == "'":
        j = i + 1
        buf = []
        while True:
            if text[j] == "\\":
                buf.append(text[j + 1])
                j += 2
                continue
            if text[j] == "'":
                if j + 1 < n and text[j + 1] == "'":
                    buf.append("'")
                    j += 2
                    continue
                break
            buf.append(text[j])
            j += 1
        return "".join(buf), j + 1
    if text[i : i + 4] == "NULL":
        return None, i + 4
    j = i
    while text[j] not in terminators:
        j += 1
    token = text[i:j].strip()
    return (float(token) if "." in token or "e" in token.lower() else int(token)), j


def _read_tuples(text: str, start: int) -> tuple[list[list], int]:
    """Parse a comma-separated list of parenthesized value-tuples starting at
    `text[start]` (which must be '('), stopping at the terminating ';'.
    Returns (tuples, index_just_past_the_semicolon)."""
    tuples = []
    i = start
    n = len(text)
    while i < n:
        while text[i] in " \t\r\n":
            i += 1
        if text[i] == ";":
            return tuples, i + 1
        if text[i] != "(":
            raise ValueError(f"expected '(' or ';' at offset {i}, found {text[i]!r}")
        i += 1
        values = []
        while True:
            while text[i] in " \t\r\n":
                i += 1
            value, i = _read_value(text, i)
            values.append(value)
            while text[i] in " \t\r\n":
                i += 1
            if text[i] == ",":
                i += 1
                continue
            if text[i] == ")":
                i += 1
                break
        tuples.append(values)
        while text[i] in " \t\r\n":
            i += 1
        if text[i] == ",":
            i += 1
            continue
        if text[i] == ";":
            return tuples, i + 1
    raise ValueError("unterminated INSERT statement (no trailing ';' found)")


_COL_EQ_RE = re.compile(r"`(?P<col>\w+)`\s*=\s*")


def _read_set_assignments(text: str, start: int) -> tuple[dict, int]:
    """Parse a `` `col` = value (, `col` = value)* `` list starting at
    `start` (right after `UPDATE ... SET `), stopping as soon as the next
    `` `col` = `` pattern doesn't match - i.e. at the WHERE clause. Returns
    (assignments, index_at_the_stop_point)."""
    assignments: dict = {}
    i = start
    n = len(text)
    while i < n:
        while i < n and text[i] in " \t\r\n":
            i += 1
        m = _COL_EQ_RE.match(text, i)
        if not m:
            break
        value, i = _read_value(text, m.end(), terminators=" \t\r\n,);")
        assignments[m.group("col")] = value
        while i < n and text[i] in " \t\r\n":
            i += 1
        if i < n and text[i] == ",":
            i += 1
            continue
        break
    return assignments, i


def _is_string_column(table: DbcTable, col: str) -> bool:
    """True for an `fmt == 's'` column, and for the handful of `'x'`
    (nominally-uint32) columns dbcfmt.py's `read_as_string` marks as
    genuinely string data in the real client file (e.g. TalentTab's tab
    name) - see dbcfmt.py's module docstring."""
    return table.fmt[table.columns.index(col)] == "s" or col in table.read_as_string


def _fill_defaults(row: dict, table: DbcTable) -> None:
    """Fill in a per-type default for any column that's missing entirely (an
    explicit column list narrower than `table.columns`) or explicitly NULL.

    NULL needs the same treatment as missing: `sql_out.py`'s `_sql_literal`
    serializes both a blank string and Python `None` as literal SQL `NULL`
    (to keep generated files smaller), but `build.py`'s row construction
    (`dbcfile.empty_row` + `_set_all_locales`) never produces `None` for a
    string column, only `""`. Without normalizing NULL back to `""` here, an
    ID that `generate.py` itself wrote out verbatim (no real change) reads
    back different from what `build_one()` would produce for it - exactly
    the phantom-diff bug `state.py`'s db_world overlay exists to avoid."""
    for col in table.columns:
        if row.get(col) is None:
            row[col] = "" if _is_string_column(table, col) else 0


def read_table_dump(path: Path, table: DbcTable) -> dict[int, dict]:
    """Read every INSERT INTO statement for table.sql_table in a
    mysqldump-style .sql file, keyed by the table's index column."""
    text = Path(path).read_text(encoding="utf-8")
    rows: dict[int, dict] = {}
    pos = 0
    while True:
        m = _INSERT_HEAD_RE.search(text, pos)
        if not m:
            break
        if m.group("table") != table.sql_table:
            pos = m.end()
            continue
        explicit_cols = (
            [c.strip(" `") for c in m.group("cols").split(",")] if m.group("cols") else None
        )
        columns = explicit_cols or list(table.columns)
        tuples, pos = _read_tuples(text, m.end())
        for values in tuples:
            if len(values) != len(columns):
                raise ValueError(
                    f"{path}: row has {len(values)} values but {len(columns)} columns "
                    f"({columns[:3]}...)"
                )
            row = dict(zip(columns, values))
            _fill_defaults(row, table)
            rows[row[table.index_column]] = row
    return rows


def read_table_rows(path: Path, table_name: str, columns: tuple[str, ...]) -> list[dict]:
    """Like `read_table_dump`, but for a table with no single-column primary
    key (a composite key, or none at all) — every row is returned as-is in a
    plain list rather than being collapsed into a dict keyed by one column,
    which would silently drop rows that share whatever column got picked."""
    text = Path(path).read_text(encoding="utf-8")
    out: list[dict] = []
    pos = 0
    while True:
        m = _INSERT_HEAD_RE.search(text, pos)
        if not m:
            break
        if m.group("table") != table_name:
            pos = m.end()
            continue
        explicit_cols = (
            [c.strip(" `") for c in m.group("cols").split(",")] if m.group("cols") else None
        )
        cols = explicit_cols or list(columns)
        tuples, pos = _read_tuples(text, m.end())
        for values in tuples:
            if len(values) != len(cols):
                raise ValueError(
                    f"{path}: row has {len(values)} values but {len(cols)} columns "
                    f"({cols[:3]}...)"
                )
            out.append(dict(zip(cols, values)))
    return out


_DELETE_HEAD_RE = re.compile(r"DELETE\s+FROM\s+`(?P<table>\w+)`\s*", re.IGNORECASE)
_UPDATE_HEAD_RE = re.compile(r"UPDATE\s+`(?P<table>\w+)`\s+SET\s+", re.IGNORECASE)
_DELETE_WHERE_RANGE_RE = re.compile(
    r"WHERE\s+`\w+`\s+BETWEEN\s+(?P<start>-?\d+)\s+AND\s+(?P<end>-?\d+)\s*;",
    re.IGNORECASE,
)
_DELETE_WHERE_IN_RE = re.compile(
    r"WHERE\s+`\w+`\s+IN\s*\((?P<ids>[^)]*)\)\s*;",
    re.IGNORECASE,
)
_WHERE_EQ_RE = re.compile(
    r"WHERE\s*\(?\s*`\w+`\s*=\s*(?P<id>-?\d+)\s*\)?\s*;",
    re.IGNORECASE,
)


def _skip_statement(text: str, pos: int) -> int:
    """Fallback for a statement shape we don't recognize: advance past the
    next ';' so scanning can keep going instead of looping forever."""
    idx = text.find(";", pos)
    return idx + 1 if idx != -1 else len(text)


def _next_match(pattern: re.Pattern, text: str, pos: int, table_name: str) -> re.Match | None:
    """Like `pattern.search(text, pos)`, but skips over matches for a
    different table's statements instead of returning them."""
    while True:
        m = pattern.search(text, pos)
        if m is None or m.group("table") == table_name:
            return m
        pos = m.end()


def _apply_insert(rows: dict[int, dict], table: DbcTable, text: str, m: re.Match) -> int:
    explicit_cols = (
        [c.strip(" `") for c in m.group("cols").split(",")] if m.group("cols") else None
    )
    columns = explicit_cols or list(table.columns)
    tuples, pos = _read_tuples(text, m.end())
    for values in tuples:
        if len(values) != len(columns):
            continue  # not a shape we recognize for this table - skip, don't crash the replay
        row = dict(zip(columns, values))
        _fill_defaults(row, table)
        rows[row[table.index_column]] = row
    return pos


def _apply_delete(rows: dict[int, dict], text: str, pos: int) -> int:
    m = _DELETE_WHERE_RANGE_RE.match(text, pos)
    if m:
        start, end = int(m.group("start")), int(m.group("end"))
        for key in [k for k in rows if start <= k <= end]:
            del rows[key]
        return m.end()
    m = _DELETE_WHERE_IN_RE.match(text, pos)
    if m:
        for token in m.group("ids").split(","):
            rows.pop(int(token.strip()), None)
        return m.end()
    m = _WHERE_EQ_RE.match(text, pos)
    if m:
        rows.pop(int(m.group("id")), None)
        return m.end()
    return _skip_statement(text, pos)


def _apply_update(rows: dict[int, dict], table: DbcTable, text: str, pos: int) -> int:
    assignments, pos = _read_set_assignments(text, pos)
    m = _WHERE_EQ_RE.match(text, pos)
    if m and assignments:
        row = rows.get(int(m.group("id")))
        if row is not None:
            for col, value in assignments.items():
                if value is None and col in table.columns and _is_string_column(table, col):
                    value = ""
                row[col] = value
        return m.end()
    return _skip_statement(text, pos)


def apply_statements(rows: dict[int, dict], table: DbcTable, sql_text: str) -> None:
    """Best-effort replay of every DELETE/INSERT/UPDATE statement touching
    `table.sql_table` in `sql_text`, applied in file order, mutating `rows`
    in place.

    Used by `state.load_existing_rows` to overlay already-promoted
    migrations (`data/sql/updates/db_world/*.sql`) on top of a base dump, so
    the pipeline can tell "already applied" from "actually changed" instead
    of permanently re-diffing every ID any past run ever touched against
    pure vanilla data.

    Not a general SQL parser: it covers the two DELETE shapes and the one
    INSERT shape `sql_out.py` emits, plus the hand-written `DELETE ... WHERE
    \\`col\\` = n` and `UPDATE ... SET col = val, ... WHERE \\`col\\` = n`
    shapes seen in this repo's migration history. A statement it doesn't
    recognize (a compound WHERE, a table this replay wasn't told to expect,
    a malformed row) is silently skipped rather than raising - safe because
    the emitted SQL always comes from source CSV/YAML data
    (`resolve.resolve_rows`'s `build_one(entry)`), never from `rows` itself;
    an imperfect replay can only leave an ID looking "changed" when it
    isn't (today's bug, just smaller in scope), never write wrong data."""
    pos = 0
    while True:
        ins_m = _next_match(_INSERT_HEAD_RE, sql_text, pos, table.sql_table)
        del_m = _next_match(_DELETE_HEAD_RE, sql_text, pos, table.sql_table)
        upd_m = _next_match(_UPDATE_HEAD_RE, sql_text, pos, table.sql_table)
        candidates = [m for m in (ins_m, del_m, upd_m) if m is not None]
        if not candidates:
            return
        m = min(candidates, key=lambda match: match.start())
        try:
            if m is ins_m:
                pos = _apply_insert(rows, table, sql_text, m)
            elif m is del_m:
                pos = _apply_delete(rows, sql_text, m.end())
            else:
                pos = _apply_update(rows, table, sql_text, m.end())
        except Exception:
            pos = _skip_statement(sql_text, m.end())
