"""
A small, narrowly-scoped reader for the `INSERT INTO` table `VALUES (...);`
statements mysqldump produces (the shape of `data/sql/base/db_world/
item_template.sql` and friends). Not a general SQL parser - just enough to
reconstruct `{entry: {column: value}}` for one table.

The tuple parser (`_read_tuples`) is adapted verbatim from
`apps/dbc-tools/lib/sql_dump.py`, which reads the exact same mysqldump
format for `spell_dbc`. It's copied rather than imported because dbc-tools
and item-tools are two independent local tools (each runnable on its own,
per `apps/dbc-tools/webui/app.py`'s own `python3 apps/dbc-tools/webui/
app.py` invocation style) with no shared installed package between their
`apps/*/lib/` directories to import across. If a third tool ever needs this
same parser, that's the point to factor it out into a real shared package
instead of a third copy.
"""

from __future__ import annotations

import re
from pathlib import Path

_INSERT_HEAD_RE = re.compile(
    r"INSERT\s+INTO\s+`(?P<table>\w+)`\s*(?:\((?P<cols>[^)]*)\))?\s*VALUES\s*",
    re.IGNORECASE,
)

_CREATE_TABLE_RE = re.compile(r"CREATE TABLE\s+`(?P<table>\w+)`\s*\(", re.IGNORECASE)

_COLUMN_LINE_RE = re.compile(r"^\s*`(?P<col>\w+)`\s")


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
                values.append("".join(buf))
                i = j + 1
            elif text[i : i + 4] == "NULL":
                values.append(None)
                i += 4
            else:
                j = i
                while text[j] not in ",)":
                    j += 1
                token = text[i:j].strip()
                values.append(float(token) if "." in token or "e" in token.lower() else int(token))
                i = j
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


def parse_create_table_columns(path: Path, table: str) -> list[str]:
    """Extract column names, in declared order, from a `CREATE TABLE
    \\`table\\` ( ... )` block in a mysqldump-style .sql file. This is how we
    know the positional order of an `INSERT INTO \\`item_template\\` VALUES
    (...)` row without hand-maintaining a column list that would silently
    drift from `data/sql/base/db_world/item_template.sql` (or a future
    schema-changing migration) if that ever adds/reorders/removes a column.
    """
    text = Path(path).read_text(encoding="utf-8")
    m = _CREATE_TABLE_RE.search(text)
    while m and m.group("table") != table:
        m = _CREATE_TABLE_RE.search(text, m.end())
    if not m:
        raise ValueError(f"{path}: no CREATE TABLE `{table}` found")
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
    if not columns:
        raise ValueError(f"{path}: CREATE TABLE `{table}` had no column definitions")
    return columns


def read_table_dump(path: Path, table: str, columns: list[str], index_column: str) -> dict[int, dict]:
    """Read every `INSERT INTO \\`table\\` VALUES (...);` statement in a
    mysqldump-style .sql file, keyed by `index_column`. `columns` must be
    the table's full column list in declared order (see
    `parse_create_table_columns`) - the base dump omits an explicit column
    list on its INSERTs, so positional order is the only thing tying a
    value to a column name."""
    text = Path(path).read_text(encoding="utf-8")
    rows: dict[int, dict] = {}
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
                raise ValueError(
                    f"{path}: row has {len(values)} values but {len(cols)} columns ({cols[:3]}...)"
                )
            row = dict(zip(cols, values))
            rows[row[index_column]] = row
    return rows


def read_table_rows(path: Path, table: str, columns: tuple[str, ...]) -> list[dict]:
    """Like `read_table_dump`, but for a table with no single-column
    primary key (a composite key, like `creature_loot_template`, or a
    surrogate one that isn't the right lookup key, like `creature`'s
    `guid`) - every row comes back as-is in a plain list rather than being
    collapsed into a dict keyed by one column, which would silently drop
    rows that share whatever column got picked."""
    text = Path(path).read_text(encoding="utf-8")
    out: list[dict] = []
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
        cols = explicit_cols or list(columns)
        tuples, pos = _read_tuples(text, m.end())
        for values in tuples:
            if len(values) != len(cols):
                raise ValueError(
                    f"{path}: row has {len(values)} values but {len(cols)} columns ({cols[:3]}...)"
                )
            out.append(dict(zip(cols, values)))
    return out
