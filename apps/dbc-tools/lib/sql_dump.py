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


_VAR_EXPR_RE = re.compile(r"(?P<name>@\w+)(?:\s*(?P<op>[+-])\s*(?P<num>\d+))?")


def _read_value(
    text: str, i: int, terminators: str = ",)", variables: dict[str, int] | None = None
) -> tuple[object, int]:
    """Parse a single SQL literal (quoted string, NULL, or number) starting at
    `text[i]` (leading whitespace already skipped by the caller). Returns
    (value, index_just_past_the_literal). `terminators` bounds a bare numeric
    token - widen it for a value not immediately followed by ',' or ')' (e.g.
    the last assignment in an `UPDATE ... SET` clause, followed by whitespace
    then `WHERE`).

    `variables` enables the one non-literal shape this repo's hand-written
    SQL actually uses: a MySQL session variable, bare (`@TrainerId`) or with
    one integer offset (`@TrainerId+3`, `@CGUID + 0`), where the variable was
    assigned a plain integer by an earlier `SET @name := n;` (see
    `apply_statements`). mod-progression's trainer rewiring is written
    entirely this way. An unknown variable, or `variables=None`, raises like
    any other unparseable token."""
    n = len(text)
    if text[i] == "@":
        m = _VAR_EXPR_RE.match(text, i)
        if variables is None or m.group("name") not in variables:
            raise ValueError(f"unresolved session variable {text[i:i + 24]!r}")
        value = variables[m.group("name")]
        if m.group("op"):
            value += int(m.group("num")) * (1 if m.group("op") == "+" else -1)
        return value, m.end()
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
    if token[:2].lower() == "0x":
        # MySQL hex literal (`0x10`) - common in hand-written spell_proc rows for
        # ProcFlags/HitMask. Checked before the float branch since a hex digit
        # can be 'e'.
        return int(token, 16), j
    return (float(token) if "." in token or "e" in token.lower() else int(token)), j


def _skip_ws_and_comments(text: str, i: int) -> int:
    """Advances past whitespace and `-- ...`-style line comments (to end of
    line). Real hand-written migrations in this repo sometimes annotate
    each VALUES tuple with a trailing comment - e.g. trainer_spell inserts
    like `(13, 48266, ...),    -- Blood Presence` - which plain whitespace
    skipping doesn't account for."""
    n = len(text)
    while i < n:
        if text[i] in " \t\r\n":
            i += 1
            continue
        if text[i : i + 2] == "--":
            j = text.find("\n", i)
            i = n if j == -1 else j + 1
            continue
        break
    return i


def _read_tuples(
    text: str, start: int, variables: dict[str, int] | None = None
) -> tuple[list[list], int]:
    """Parse a comma-separated list of parenthesized value-tuples starting at
    `text[start]` (which must be '('), stopping at the terminating ';'.
    Returns (tuples, index_just_past_the_semicolon)."""
    tuples = []
    i = start
    n = len(text)
    while i < n:
        i = _skip_ws_and_comments(text, i)
        if text[i] == ";":
            return tuples, i + 1
        if text[i] != "(":
            raise ValueError(f"expected '(' or ';' at offset {i}, found {text[i]!r}")
        i += 1
        values = []
        while True:
            i = _skip_ws_and_comments(text, i)
            value, i = _read_value(text, i, variables=variables)
            values.append(value)
            i = _skip_ws_and_comments(text, i)
            if text[i] == ",":
                i += 1
                continue
            if text[i] == ")":
                i += 1
                break
        tuples.append(values)
        i = _skip_ws_and_comments(text, i)
        if text[i] == ",":
            i += 1
            continue
        if text[i] == ";":
            return tuples, i + 1
    raise ValueError("unterminated INSERT statement (no trailing ';' found)")


_COL_EQ_RE = re.compile(r"`(?P<col>\w+)`\s*=\s*")


def _read_set_assignments(
    text: str, start: int, variables: dict[str, int] | None = None
) -> tuple[dict, int]:
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
        value, i = _read_value(text, m.end(), terminators=" \t\r\n,);", variables=variables)
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


_CREATE_TABLE_RE_TEMPLATE = r"CREATE TABLE\s+`{table}`\s*\("
_COLUMN_LINE_RE = re.compile(r"^\s*`(?P<name>\w+)`\s+\w")


def parse_create_table_columns(path: Path, table_name: str) -> tuple[str, ...]:
    """Extracts a table's column names, in file-column order, straight from
    its own `CREATE TABLE` statement - for a wide table (creature_template
    is ~70 columns) whose base dump uses a bare `INSERT INTO x VALUES (...)`
    with no explicit column list (see read_table_rows), so parsing it
    correctly at all needs the complete, exactly-ordered column list as the
    fallback - and hand-transcribing that (the way lib/dbcfmt.py does for
    DBC tables, which are a curated *subset* of a much narrower table) would
    be its own source of transcription bugs for a table this wide. Skips
    non-column lines (`PRIMARY KEY (...)`, `KEY ...`, `CONSTRAINT ...`) since
    none of them start with a backtick-quoted-name-then-type pattern."""
    text = Path(path).read_text(encoding="utf-8")
    m = re.search(_CREATE_TABLE_RE_TEMPLATE.format(table=re.escape(table_name)), text, re.IGNORECASE)
    if not m:
        raise ValueError(f"{path}: no CREATE TABLE `{table_name}` found")
    depth = 1
    i = m.end()
    while depth > 0:
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
        i += 1
    body = text[m.end():i - 1]
    columns = []
    for line in body.splitlines():
        cm = _COLUMN_LINE_RE.match(line)
        if cm:
            columns.append(cm.group("name"))
    return tuple(columns)


def read_table_rows(path: Path, table_name: str, columns: tuple[str, ...]) -> list[dict]:
    """Like `read_table_dump`, but for a table with no single-column primary
    key (a composite key, or none at all) — every row is returned as-is in a
    plain list rather than being collapsed into a dict keyed by one column,
    which would silently drop rows that share whatever column got picked."""
    text = Path(path).read_text(encoding="utf-8")
    # Every integer `SET @name := n;` in the file, resolved up front (not in statement order -
    # good enough for the "assigned once at the top" shape these files use).
    variables = {m.group("name"): int(m.group("value")) for m in _SET_VAR_RE.finditer(text)}
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
        tuples, pos = _read_tuples(text, m.end(), variables)
        for values in tuples:
            if len(values) != len(cols):
                raise ValueError(
                    f"{path}: row has {len(values)} values but {len(cols)} columns "
                    f"({cols[:3]}...)"
                )
            out.append(dict(zip(cols, values)))
    return out


_DELETE_HEAD_RE = re.compile(r"DELETE\s+FROM\s+`(?P<table>\w+)`\s*", re.IGNORECASE)
# `SET @TrainerId := 200;` - integer session variables only (see _read_value). A `SET @GUID :=
# (SELECT MAX(guid)+1 ...)` doesn't match and stays what it always was: an unresolvable token that
# skips the statement using it.
_SET_VAR_RE = re.compile(r"SET\s+(?P<name>@\w+)\s*:?=\s*(?P<value>-?\d+)\s*;", re.IGNORECASE)
_UPDATE_HEAD_RE = re.compile(r"UPDATE\s+`(?P<table>\w+)`\s+SET\s+", re.IGNORECASE)
_DELETE_WHERE_RANGE_RE = re.compile(
    r"WHERE\s+`\w+`\s+BETWEEN\s+(?P<start>-?\d+)\s+AND\s+(?P<end>-?\d+)\s*;",
    re.IGNORECASE,
)
# Shared by DELETE and UPDATE - "WHERE `col` IN (id1, id2, ...);" means the same thing for both
# (delete/touch every listed row), just with a different statement in front of it.
_WHERE_IN_RE = re.compile(
    r"WHERE\s+`\w+`\s+IN\s*\((?P<ids>[^)]*)\)\s*;",
    re.IGNORECASE,
)
_WHERE_EQ_RE = re.compile(
    r"WHERE\s*\(?\s*`\w+`\s*=\s*(?P<id>-?\d+)\s*\)?\s*;",
    re.IGNORECASE,
)


# The composite-key DELETE `sql_out.py` emits: "WHERE (`a`, `b`) IN ((1, 'x'), (2, 'y'));".
# Deliberately separate from `_WHERE_IN_RE` above, whose `[^)]*` body stops dead at the first
# ')' and so can never read a list of tuples.
_DELETE_WHERE_TUPLE_IN_RE = re.compile(
    r"WHERE\s*\(\s*(?P<cols>`\w+`(?:\s*,\s*`\w+`)*)\s*\)\s+IN\s*\(",
    re.IGNORECASE,
)


def _read_key_tuples(
    text: str, start: int, variables: dict[str, int] | None = None
) -> tuple[list[list], int]:
    """Parse `(v, v), (v, v)` and stop on the ')' closing the enclosing IN
    list - the one difference from `_read_tuples`, which is written for an
    INSERT's VALUES and terminates on ';' instead."""
    tuples: list[list] = []
    i = start
    n = len(text)
    while i < n:
        i = _skip_ws_and_comments(text, i)
        if text[i] == ")":
            return tuples, i + 1
        if text[i] != "(":
            raise ValueError(f"expected '(' or ')' at offset {i}, found {text[i]!r}")
        i += 1
        values = []
        while True:
            i = _skip_ws_and_comments(text, i)
            value, i = _read_value(text, i, variables=variables)
            values.append(value)
            i = _skip_ws_and_comments(text, i)
            if text[i] == ",":
                i += 1
                continue
            if text[i] == ")":
                i += 1
                break
        tuples.append(values)
        i = _skip_ws_and_comments(text, i)
        if text[i] == ",":
            i += 1
    raise ValueError("unterminated IN (...) list (no closing ')' found)")


def read_table_statements(path: Path, table_name: str, columns: tuple[str, ...]):
    """Yield one table's INSERT/DELETE statements **in file order**, so a
    caller can replay them instead of taking the union of INSERTs and
    pretending no row was ever deleted.

    Events are `("insert", rows)` and `("delete", (key_columns, key_tuples))`;
    a DELETE whose shape isn't recognized yields `("delete_unparsed", None)`
    so the caller can decide how paranoid to be rather than silently
    believing rows survived it. A single-column WHERE col IN (...) / col = n
    is normalised to the same one-column shape as the composite form, so
    callers only handle one case.

    Complements `read_table_rows` (union of INSERTs, no DELETE replay), which
    stays as-is: it is the right answer for "what is live" across the base
    dump plus every hand-written migration, where DELETE shapes are far more
    varied than the ones `sql_out.py` emits."""
    text = Path(path).read_text(encoding="utf-8")
    variables = {m.group("name"): int(m.group("value")) for m in _SET_VAR_RE.finditer(text)}
    pos = 0
    while pos < len(text):
        ins = _next_match(_INSERT_HEAD_RE, text, pos, table_name)
        dele = _next_match(_DELETE_HEAD_RE, text, pos, table_name)
        if ins is None and dele is None:
            return
        # Whichever comes first in the file - that is the whole point of this function.
        if dele is None or (ins is not None and ins.start() < dele.start()):
            explicit = (
                [c.strip(" `") for c in ins.group("cols").split(",")] if ins.group("cols") else None
            )
            cols = explicit or list(columns)
            tuples, pos = _read_tuples(text, ins.end(), variables)
            rows = [dict(zip(cols, v)) for v in tuples if len(v) == len(cols)]
            yield "insert", rows
            continue
        pos = dele.end()
        m = _DELETE_WHERE_TUPLE_IN_RE.match(text, pos)
        if m:
            key_cols = tuple(c.strip(" `") for c in m.group("cols").split(","))
            tuples, pos = _read_key_tuples(text, m.end(), variables)
            pos = _skip_statement(text, pos)
            yield "delete", (key_cols, [tuple(v) for v in tuples])
            continue
        m = _WHERE_IN_RE.match(text, pos)
        if m:
            col = re.search(r"`(\w+)`", m.group(0)).group(1)
            pos = m.end()
            yield "delete", ((col,), [(i,) for i in _parse_id_list(m.group("ids"))])
            continue
        m = _WHERE_EQ_RE.match(text, pos)
        if m:
            col = re.search(r"`(\w+)`", m.group(0)).group(1)
            pos = m.end()
            yield "delete", ((col,), [(int(m.group("id")),)])
            continue
        pos = _skip_statement(text, pos)
        yield "delete_unparsed", None


def _parse_id_list(ids_text: str) -> list[int]:
    """The `(...)` body of a `WHERE col IN (...)`, one int per entry, with
    `-- trailing comments` stripped line by line - mod-progression's trainer
    rewiring annotates every CreatureId that way (`913, -- Lyria Du Lac
    <Warrior Trainer>`)."""
    cleaned = "\n".join(line.split("--", 1)[0] for line in ids_text.splitlines())
    return [int(token.strip()) for token in cleaned.split(",") if token.strip()]


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


def _apply_insert(
    rows: dict[int, dict], table: DbcTable, text: str, m: re.Match,
    variables: dict[str, int] | None = None,
) -> int:
    explicit_cols = (
        [c.strip(" `") for c in m.group("cols").split(",")] if m.group("cols") else None
    )
    columns = explicit_cols or list(table.columns)
    tuples, pos = _read_tuples(text, m.end(), variables)
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
    m = _WHERE_IN_RE.match(text, pos)
    if m:
        for id_ in _parse_id_list(m.group("ids")):
            rows.pop(id_, None)
        return m.end()
    m = _WHERE_EQ_RE.match(text, pos)
    if m:
        rows.pop(int(m.group("id")), None)
        return m.end()
    return _skip_statement(text, pos)


def _apply_update(
    rows: dict[int, dict], table: DbcTable, text: str, pos: int,
    variables: dict[str, int] | None = None,
) -> int:
    """`UPDATE ... SET col = val, ... WHERE \\`col\\` = n` (one row) or
    `WHERE \\`col\\` IN (n, m, ...)` (several rows, same assignments applied
    to each) - the second shape is a real one, not hypothetical: the
    Glacial Spike/Fireball cast-time fix (`rev_1789232500000000000.sql`,
    promoted as `2026_09_14_01.sql`) uses exactly this to repoint both
    spells' `CastingTimeIndex` in one statement. Before this handled it,
    that statement fell through to `_skip_statement` silently (per this
    module's "degrade safely" contract) - safe (never wrote wrong data,
    per `apply_statements`'s own docstring) but left `state.py`'s
    reconstruction of "what's live" stale for every ID past the first,
    surfacing as a spurious drift report from `generate.py`."""
    assignments, pos = _read_set_assignments(text, pos, variables)
    if not assignments:
        return _skip_statement(text, pos)
    m = _WHERE_EQ_RE.match(text, pos)
    if m:
        ids, end = [int(m.group("id"))], m.end()
    else:
        m = _WHERE_IN_RE.match(text, pos)
        if not m:
            return _skip_statement(text, pos)
        ids = _parse_id_list(m.group("ids"))
        end = m.end()
    for id_ in ids:
        row = rows.get(id_)
        if row is None:
            continue
        for col, value in assignments.items():
            if value is None and col in table.columns and _is_string_column(table, col):
                value = ""
            row[col] = value
    return end


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
    variables: dict[str, int] = {}
    while True:
        ins_m = _next_match(_INSERT_HEAD_RE, sql_text, pos, table.sql_table)
        del_m = _next_match(_DELETE_HEAD_RE, sql_text, pos, table.sql_table)
        upd_m = _next_match(_UPDATE_HEAD_RE, sql_text, pos, table.sql_table)
        set_m = _SET_VAR_RE.search(sql_text, pos)
        candidates = [m for m in (ins_m, del_m, upd_m, set_m) if m is not None]
        if not candidates:
            return
        m = min(candidates, key=lambda match: match.start())
        try:
            if m is set_m:
                variables[m.group("name")] = int(m.group("value"))
                pos = m.end()
            elif m is ins_m:
                pos = _apply_insert(rows, table, sql_text, m, variables)
            elif m is del_m:
                pos = _apply_delete(rows, sql_text, m.end())
            else:
                pos = _apply_update(rows, table, sql_text, m.end(), variables)
        except Exception:
            pos = _skip_statement(sql_text, m.end())
