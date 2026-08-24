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
"""

from __future__ import annotations

import re
from pathlib import Path

from .dbcfmt import DbcTable

_INSERT_HEAD_RE = re.compile(
    r"INSERT\s+INTO\s+`(?P<table>\w+)`\s*(?:\((?P<cols>[^)]*)\))?\s*VALUES\s*",
    re.IGNORECASE,
)


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
            for col in table.columns:
                row.setdefault(col, "" if table.fmt[table.columns.index(col)] == "s" else 0)
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
