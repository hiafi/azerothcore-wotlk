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

import functools
import itertools
import re
from pathlib import Path
from typing import Callable

from . import sqlcorpus
from .dbcfmt import DbcTable

# `REPLACE INTO` is read exactly like `INSERT INTO`: MySQL deletes any row with the same key and then
# inserts, so the new row stands alone and columns the statement omits are NOT kept from the old
# row. Every replay site below stores a parsed row with `rows[key] = row` (a whole-dict
# assignment, never `.update()`), which is already those semantics; the plain-union readers
# (`read_table_dump`, `read_table_rows`) have no old row to drop. Needed for the dpssim/training
# dummies (creature_template 900001-900006, 900012), which were created with `REPLACE INTO`.
_INSERT_HEAD_RE = re.compile(
    r"(?:INSERT|REPLACE)\s+INTO\s+`(?P<table>\w+)`\s*(?:\((?P<cols>[^)]*)\))?\s*VALUES\s*",
    re.IGNORECASE,
)


_VAR_EXPR_RE = re.compile(r"(?P<name>@\w+)(?:\s*(?P<op>[+-])\s*(?P<num>\d+))?")


# MySQL's backslash escapes inside a string literal; any other `\x` is just `x`.
_MYSQL_ESCAPES = {"n": "\n", "r": "\r", "t": "\t", "0": "\0", "b": "\b", "Z": "\x1a"}


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
                escaped = text[j + 1]
                if escaped in "%_":  # MySQL keeps the backslash for these two (LIKE wildcards)
                    buf.append("\\")
                buf.append(_MYSQL_ESCAPES.get(escaped, escaped))
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


# `INSERT ... VALUES (...) ON DUPLICATE KEY UPDATE ...;` - the do-not-delete-table upsert shape
# `sql_out.render_upsert_block` emits (see data/sql/updates/db_world/2026_09_23_12.sql's
# `creature_template` block: a real, hand-written INSERT of this exact shape). `_read_tuples`
# treats it as an alternate tuple-list terminator, same as a bare ';' - the UPDATE clause's own
# `` `col` = VALUES(`col`) `` pairs are never read; only the VALUES(...) tuples matter, which
# matches how the statement actually behaves against a brand-new row.
_ON_DUPLICATE_RE = re.compile(r"ON\s+DUPLICATE\s+KEY\s+UPDATE", re.IGNORECASE)


# Fast path for `_read_tuples`: a tuple made only of plain literals (no `@var`, no comment inside, no hex) is delimited
# by one regex and its values pulled out by a second, instead of one Python call per value (the spell snapshots are
# 37 million values). Anything else - and any tuple the regex cannot fully account for - goes to the character-level
# parser below, which stays the definition of what a tuple means; the two are held to the same answer by
# lib/test_sql_dump_fast.py and by the harness.
_STRING = r"'(?:[^'\\]++|\\[\s\S]|'')*+'"
_NUMBER_INT = r"-?\d+"
_NUMBER_FLOAT = r"-?\d+(?:\.\d+(?:[eE][-+]?\d+)?|[eE][-+]?\d+)"
_VALUE = rf"(?:{_STRING}|NULL|{_NUMBER_FLOAT}|{_NUMBER_INT})"
_BLANK = r"[ \t\r\n]*"  # exactly what _skip_ws_and_comments skips (no comments: those take the slow path)
_TUPLE_RE = re.compile(rf"\({_BLANK}{_VALUE}(?:{_BLANK},{_BLANK}{_VALUE})*{_BLANK}\)")
# Splits a tuple `_TUPLE_RE` already validated into its tokens: a quoted string, or anything up to the next separator.
_TOKEN_RE = re.compile(r"'(?:[^'\\]++|\\[\s\S]|'')*+'|[^,()\s]++")
_ESCAPE_RE = re.compile(r"\\([\s\S])|''")


def _unescape_match(m: re.Match) -> str:
    escaped = m.group(1)
    if escaped is None:
        return "'"
    if escaped in "%_":  # MySQL keeps the backslash for these two (LIKE wildcards)
        return "\\" + escaped
    return _MYSQL_ESCAPES.get(escaped, escaped)


class _TokenValues(dict):
    """token text -> the value `_read_value` gives it. A snapshot is mostly the same few tokens (`0`, `NULL`, `1`),
    so after the first sighting a value costs one dict lookup, done by `map` without a Python-level loop."""

    def __missing__(self, token: str):
        first = token[0]
        if first == "'":
            body = token[1:-1]
            value = _ESCAPE_RE.sub(_unescape_match, body) if "\\" in body or "''" in body else body
        elif token == "NULL":
            value = None
        elif "." in token or "e" in token or "E" in token:
            value = float(token)
        else:
            value = int(token)
        self[token] = value
        return value


def _read_tuples(
    text: str, start: int, variables: dict[str, int] | None = None, *, fast: bool = True
) -> tuple[list[list], int]:
    """Parse a comma-separated list of parenthesized value-tuples starting at
    `text[start]` (which must be '('), stopping at the terminating ';' - or,
    for an `INSERT ... ON DUPLICATE KEY UPDATE` upsert, at the `ON DUPLICATE
    KEY UPDATE` clause that follows the last tuple (see `_ON_DUPLICATE_RE`),
    in which case the whole clause is skipped to the statement's real
    terminating ';' via `_skip_statement` - safe because this repo's upsert
    shape never has an embedded ';' inside that clause. Returns (tuples,
    index_just_past_the_semicolon). `fast=False` forces the character-level parser for every tuple (the reference the
    fast path is tested against)."""
    tuples = []
    token_values = _TokenValues()
    i = start
    n = len(text)
    while i < n:
        i = _skip_ws_and_comments(text, i)
        if text[i] == ";":
            return tuples, i + 1
        if text[i] != "(":
            raise ValueError(f"expected '(' or ';' at offset {i}, found {text[i]!r}")
        plain = _TUPLE_RE.match(text, i) if fast else None
        if plain is not None:
            values = list(map(token_values.__getitem__, _TOKEN_RE.findall(text, i + 1, plain.end() - 1)))
            i = plain.end()
        else:
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
        if _ON_DUPLICATE_RE.match(text, i):
            return tuples, _skip_statement(text, i)
    raise ValueError("unterminated INSERT statement (no trailing ';' found)")


_COL_EQ_RE = re.compile(r"`(?P<col>\w+)`\s*=\s*")


_SELF_EXPR_RE = re.compile(r"`(?P<src>\w+)`\s*(?P<op>[|&+-])\s*(?P<neg>~?)\s*(?P<num>\d+)")


def _self_expression(col: str, m: re.Match):
    """`col = col | 64` style assignment as a function of the old value, or None if `m` is not a
    self-referencing integer expression (`|`, `&`, `&~`, `+`, `-`)."""
    if m.group("src") != col:
        return None
    n, op = int(m.group("num")), m.group("op")
    if m.group("neg"):
        if op != "&":
            return None
        return lambda old: old & ~n
    return {"|": lambda old: old | n, "&": lambda old: old & n,
            "+": lambda old: old + n, "-": lambda old: old - n}[op]


def _assign(row: dict, assignments: dict) -> None:
    """Applies `_read_set_assignments(..., allow_expr=True)` output to `row`; an expression on a
    column the row does not hold (an INSERT omitted it) cannot be evaluated and is left out."""
    for col, value in assignments.items():
        if callable(value):
            if isinstance(row.get(col), int):
                row[col] = value(row[col])
        else:
            row[col] = value


def _read_set_assignments(
    text: str, start: int, variables: dict[str, int] | None = None, allow_expr: bool = False,
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
        expr = _SELF_EXPR_RE.match(text, m.end()) if allow_expr else None
        func = _self_expression(m.group("col"), expr) if expr else None
        if func is not None:
            value, i = func, expr.end()
        else:
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


@functools.lru_cache(maxsize=64)
def _string_columns(table: DbcTable) -> frozenset:
    """Every column `_is_string_column` is true for - computed once per table (the per-column `columns.index` lookup it
    replaces was O(columns) for each NULL in each of a snapshot's tens of thousands of rows)."""
    return frozenset(
        col for ch, col in zip(table.fmt, table.columns) if ch == "s" or col in table.read_as_string
    )


@functools.lru_cache(maxsize=64)
def _column_set(table: DbcTable) -> frozenset:
    return frozenset(table.columns)


def _fill_defaults(row: dict, table: DbcTable, string_columns: frozenset | None = None) -> None:
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
    if string_columns is None:
        string_columns = _string_columns(table)
    if row.keys() == _column_set(table):
        # Every column present (the usual full-width row): only the NULLs need a default, and there is no need to
        # probe 234 columns for them one by one.
        for col in [c for c, v in row.items() if v is None]:
            row[col] = "" if col in string_columns else 0
        return
    for col in table.columns:
        if row.get(col) is None:
            row[col] = "" if col in string_columns else 0


def read_table_dump(path: Path, table: DbcTable) -> dict[int, dict]:
    """Read every INSERT INTO statement for table.sql_table in a
    mysqldump-style .sql file, keyed by the table's index column."""
    text = sqlcorpus.read_text(path)
    rows: dict[int, dict] = {}
    pos = 0
    string_columns = _string_columns(table)
    while True:
        m = _next_match(_INSERT_HEAD_RE, text, pos, table.sql_table)
        if not m:
            break
        explicit_cols = (
            [c.strip().strip("`") for c in m.group("cols").split(",")] if m.group("cols") else None
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
            _fill_defaults(row, table, string_columns)
            rows[row[table.index_column]] = row
    return rows


_CREATE_TABLE_RE_TEMPLATE = r"CREATE TABLE\s+`{table}`\s*\("
_COLUMN_LINE_RE = re.compile(r"^\s*`(?P<name>\w+)`\s+\w")


def _create_table_body(path: Path, table_name: str) -> str:
    """The text strictly between a `CREATE TABLE \\`table_name\\` (` and its matching closing `)`
    - shared by `parse_create_table_columns` and `parse_create_table_defaults`, which both need to
    walk the same column-definition lines but extract a different piece of each one."""
    text = sqlcorpus.read_text(path)
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
    return text[m.end():i - 1]


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
    columns = []
    for line in _create_table_body(path, table_name).splitlines():
        cm = _COLUMN_LINE_RE.match(line)
        if cm:
            columns.append(cm.group("name"))
    return tuple(columns)


# Captures a column's type keyword (right after its backtick-quoted name) and its DEFAULT literal
# (a quoted string or bare NULL) - `[^,]*?` skips over `unsigned`/`NOT NULL`/`CHARACTER SET ...`
# etc without crossing into a following column's line (this schema never puts a comma inside a
# type or its modifiers before DEFAULT). A trailing `COMMENT '...'` after the DEFAULT value is
# simply never reached by this capture group, so it doesn't need to be skipped separately.
_COLUMN_DEFAULT_RE = re.compile(
    r"^\s*`(?P<name>\w+)`\s+(?P<type>[a-zA-Z]+)\b[^,]*?DEFAULT\s+(?P<default>'(?:[^'\\]|\\.)*'|NULL)",
    re.IGNORECASE,
)
_INT_COLUMN_TYPES = {"int", "tinyint", "smallint", "mediumint", "bigint"}
_FLOAT_COLUMN_TYPES = {"float", "double", "decimal"}


def _typed_default(type_name: str, raw_literal: str) -> object:
    if raw_literal.upper() == "NULL":
        return None
    value = raw_literal[1:-1].replace("''", "'")  # strip the quotes; unescape a doubled quote
    type_name = type_name.lower()
    if type_name in _INT_COLUMN_TYPES:
        return int(value)
    if type_name in _FLOAT_COLUMN_TYPES:
        return float(value)
    return value  # char/varchar/text/enum/... (or an unrecognized type) - keep as text


def parse_create_table_defaults(path: Path, table_name: str) -> dict[str, object]:
    """Extracts each column's own schema `DEFAULT` (typed as int/float/str/`None`), from the same
    `CREATE TABLE` `parse_create_table_columns` reads - for a helper like
    `lib.dsl.registry.creature_template()` that builds a *full* row and needs "what would this
    column be if nothing set it" for every column it wasn't explicitly given, without hand-
    transcribing ~54 defaults (the same transcription-bug argument `parse_create_table_columns`'s
    own docstring makes for the column list itself). A column with no `DEFAULT` clause at all is
    simply absent from the returned dict - `creature_template`'s own `CREATE TABLE` gives every
    column one, so this hasn't come up in practice; a caller with a real "no known default" case
    decides what that means rather than this function guessing.

    `DEFAULT 'x'` is always quoted in a `SHOW CREATE TABLE`-style dump even for a numeric column
    (`` `entry` int unsigned NOT NULL DEFAULT '0' ``) - the column's own type keyword, captured
    right after its name, is what decides whether that quoted text becomes a Python `int`/`float`
    or stays a plain string; `DEFAULT NULL` is always `None` regardless of type."""
    defaults: dict[str, object] = {}
    for line in _create_table_body(path, table_name).splitlines():
        m = _COLUMN_DEFAULT_RE.match(line)
        if m:
            defaults[m.group("name")] = _typed_default(m.group("type"), m.group("default"))
    return defaults


_COLUMN_TYPE_RE = re.compile(r"^\s*`(?P<name>\w+)`\s+(?P<type>[a-zA-Z]+)\b")


def parse_create_table_string_columns(path: Path, table_name: str) -> frozenset[str]:
    """Column names whose SQL type is a string family (`char`/`varchar`/`text`/`enum`/...),
    independent of whether they have a `DEFAULT` clause at all (unlike `parse_create_table_defaults`,
    which can't tell "no default" apart from "this column's default is `NULL`, but it's still a
    string column" - `creature_template`'s `subname`/`IconName` are exactly that: `char(100)
    DEFAULT NULL`). Built for a caller that needs to construct a synthetic `dbcfmt.DbcTable` for
    `sql_dump.apply_statements`/`apply_composite_key_statements` (e.g.
    `trainer_state.load_replayed_table_rows`) - those need to know which columns default to `''`
    rather than `0` when a statement leaves them unset, and guessing from a `DEFAULT` value alone
    would misclassify exactly this case."""
    names = set()
    for line in _create_table_body(path, table_name).splitlines():
        m = _COLUMN_TYPE_RE.match(line)
        if not m:
            continue
        type_name = m.group("type").lower()
        if type_name not in _INT_COLUMN_TYPES and type_name not in _FLOAT_COLUMN_TYPES:
            names.add(m.group("name"))
    return frozenset(names)


def read_table_rows(path: Path, table_name: str, columns: tuple[str, ...]) -> list[dict]:
    """Like `read_table_dump`, but for a table with no single-column primary
    key (a composite key, or none at all) — every row is returned as-is in a
    plain list rather than being collapsed into a dict keyed by one column,
    which would silently drop rows that share whatever column got picked."""
    text = sqlcorpus.read_text(path)
    # Every integer `SET @name := n;` in the file, resolved up front (not in statement order -
    # good enough for the "assigned once at the top" shape these files use).
    variables = _file_variables(text)
    out: list[dict] = []
    pos = 0
    while True:
        m = _next_match(_INSERT_HEAD_RE, text, pos, table_name)
        if not m:
            break
        explicit_cols = (
            [c.strip().strip("`") for c in m.group("cols").split(",")] if m.group("cols") else None
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

# A broad catch-all WHERE, used only as the last fallback in `_apply_update`/`_apply_composite_update`
# after the specific single-condition shapes above have already failed to match - captures
# everything between WHERE and the statement's terminating ';' for `parse_and_equality_conditions`
# to split further. Safe to be this permissive only because it's tried last: this repo's real
# WHERE clauses never embed a literal ';' inside a string value here, so the first ';' really is
# the statement end.
_WHERE_ANY_RE = re.compile(r"WHERE\s+(?P<conds>.+?);", re.IGNORECASE | re.DOTALL)

# `` `col` = value `` - one conjunct of the AND-chain `parse_and_equality_conditions` splits on.
_AND_EQ_COND_RE = re.compile(
    r"`(?P<col>\w+)`\s*=\s*(?P<val>-?\d+(?:\.\d+)?|'(?:[^'\\]|\\.)*'|NULL)", re.IGNORECASE
)


def parse_and_equality_conditions(where_text: str) -> list[tuple[str, object]] | None:
    """Splits a WHERE clause's `` `col1` = v1 AND `col2` = v2 ... `` into `[(col, value), ...]` -
    the one conjunctive-equality shape this repo's hand-written creature migrations actually use
    for a point fix after the original INSERT: a defensive "only if it still has the value I
    expect" guard (e.g. `UPDATE creature_template SET flags_extra = 66 WHERE entry = 300001 AND
    flags_extra = 194;`, `data/sql/updates/db_world/2026_09_01_01.sql` - Frozen Orb 300001's real
    history). Returns `None` if any conjunct isn't a plain `` `col` = value `` (an `OR`, a range,
    a subquery, ...) so the caller can degrade safely instead of guessing. Order is preserved, but
    callers should look conditions up by column name - the row's actual key isn't always first."""
    conditions = []
    for part in re.split(r"(?i)\bAND\b", where_text):
        m = _AND_EQ_COND_RE.fullmatch(part.strip())
        if not m:
            return None
        raw = m.group("val")
        if raw.upper() == "NULL":
            value: object = None
        elif raw.startswith("'"):
            value = raw[1:-1].replace("''", "'")
        elif "." in raw:
            value = float(raw)
        else:
            value = int(raw)
        conditions.append((m.group("col"), value))
    return conditions


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
    text = sqlcorpus.read_text(path)
    variables = _file_variables(text)
    pos = 0
    while pos < len(text):
        ins = _next_match(_INSERT_HEAD_RE, text, pos, table_name)
        dele = _next_match(_DELETE_HEAD_RE, text, pos, table_name)
        if ins is None and dele is None:
            return
        # Whichever comes first in the file - that is the whole point of this function.
        if dele is None or (ins is not None and ins.start() < dele.start()):
            explicit = (
                [c.strip().strip("`") for c in ins.group("cols").split(",")] if ins.group("cols") else None
            )
            cols = explicit or list(columns)
            tuples, pos = _read_tuples(text, ins.end(), variables)
            rows = [dict(zip(cols, v)) for v in tuples if len(v) == len(cols)]
            yield "insert", rows
            continue
        pos = dele.end()
        m = _DELETE_WHERE_TUPLE_IN_RE.match(text, pos)
        if m:
            key_cols = tuple(c.strip().strip("`") for c in m.group("cols").split(","))
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


def _file_variables(text: str) -> dict[str, int]:
    """Every integer `SET @name := n;` in the file (an `@`-free file has none, which is most of them)."""
    if "@" not in text:
        return {}
    return {m.group("name"): int(m.group("value")) for m in _SET_VAR_RE.finditer(text)}


def _head_index(text: str):
    """The text's `sqlcorpus.HeadIndex` when it came from an active corpus, else None (plain `str`)."""
    return text.head_index if isinstance(text, sqlcorpus.SqlText) else None


def _next_match(pattern: re.Pattern, text: str, pos: int, table_name: str) -> re.Match | None:
    """Like `pattern.search(text, pos)`, but skips over matches for a
    different table's statements instead of returning them. On a corpus text the precomputed head index answers
    instead of a regex scan (`pattern` is always one of the two single-kind head patterns)."""
    index = _head_index(text)
    if index is not None:
        if pattern is _INSERT_HEAD_RE:
            return index.first(pos, table_name, "I")
        if pattern is _DELETE_HEAD_RE:
            return index.first(pos, table_name, "D")
    while True:
        m = pattern.search(text, pos)
        if m is None or m.group("table") == table_name:
            return m
        pos = m.end()


# `apply_statements`'s own combined head pattern - INSERT/DELETE/UPDATE/SET-var in one alternation,
# with a distinctly-named table group per branch (Python's `re` forbids reusing a group name across
# alternatives). Used only by `apply_statements`, which used to run `_next_match` for each of
# `_INSERT_HEAD_RE`/`_DELETE_HEAD_RE`/`_UPDATE_HEAD_RE` plus a separate `_SET_VAR_RE.search`,
# independently, every loop iteration - four full scans of the remaining text (each with its own
# "skip past a different table's statement" retry loop) to find one earliest match. Profiling
# `state.load_existing_rows(SPELL)` during the druid-rework Resto pass found this was the actual
# dominant cost of a `generate.py` run (regex `.search()` alone: 148s of a 210s call, most of it
# these three independent per-iteration scans re-walking past hundreds of other tables' statements
# in the same large migration file) - see docs/bugs-and-fixes.md's "generate.py looks hung" entry.
_STATEMENT_HEAD_RE = sqlcorpus.STATEMENT_HEAD_RE


def _next_statement(text: str, pos: int, table_name: str) -> re.Match | None:
    """`_next_match`'s counterpart for `_STATEMENT_HEAD_RE`: one combined scan per position
    instead of one per statement kind. A `SET` session-variable match (no `*_table` group) is
    never table-filtered, matching `apply_statements`'s original `_SET_VAR_RE.search` behavior. On a corpus text the
    head index answers (one scan per file, shared by every table's replay)."""
    index = _head_index(text)
    if index is not None:
        return index.first(pos, table_name, "IDUS")
    while True:
        m = _STATEMENT_HEAD_RE.search(text, pos)
        if m is None:
            return None
        matched_table = m.group("ins_table") or m.group("del_table") or m.group("upd_table")
        if matched_table is None or matched_table == table_name:
            return m
        pos = m.end()


def _apply_insert(
    rows: dict[int, dict], table: DbcTable, text: str, m: re.Match,
    variables: dict[str, int] | None = None,
) -> int:
    explicit_cols = (
        [c.strip().strip("`") for c in m.group("cols").split(",")] if m.group("cols") else None
    )
    columns = explicit_cols or list(table.columns)
    tuples, pos = _read_tuples(text, m.end(), variables)
    string_columns = _string_columns(table)
    for values in tuples:
        if len(values) != len(columns):
            continue  # not a shape we recognize for this table - skip, don't crash the replay
        row = dict(zip(columns, values))
        _fill_defaults(row, table, string_columns)
        rows[row[table.index_column]] = row
    return pos


def _apply_delete(rows: dict[int, dict], text: str, pos: int) -> int:
    m = _DELETE_WHERE_RANGE_RE.match(text, pos)
    if m:
        # Iterate the (small, fixed-width) target range, not every key currently in `rows` - a
        # `WHERE id BETWEEN 200000 AND 209999` range-clear is the standard first statement of
        # nearly every generate.py-emitted migration (one per class/pass), and `rows` grows to
        # tens of thousands of entries as `state.load_existing_rows` replays ~80 of these files in
        # sequence - the old `[k for k in rows if start <= k <= end]` scanned the *entire current
        # dict* on every single one of those files, making this the dominant cost of a
        # `generate.py` run (~190s of it, profiled during the druid-rework Resto pass) and one that
        # gets worse every time another class's migrations are promoted. See
        # docs/bugs-and-fixes.md's "generate.py looks hung but is CPU-bound" entry.
        start, end = int(m.group("start")), int(m.group("end"))
        for key in range(start, end + 1):
            rows.pop(key, None)
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
    # The tuple form lib/spell_tables.py emits for every declared table, here with a single key
    # column: `WHERE (`entry`) IN ((200134), (200136));`. Skipping it left deleted spell_bonus_data
    # rows looking live (docs/bugs-and-fixes.md, 2026-10-02).
    m = _DELETE_WHERE_TUPLE_IN_RE.match(text, pos)
    if m and "," not in m.group("cols"):
        tuples, end = _read_key_tuples(text, m.end())
        for values in tuples:
            rows.pop(int(values[0]), None)
        return _skip_statement(text, end)
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
    surfacing as a spurious drift report from `generate.py`.

    A third shape, `WHERE \\`col\\` = n AND \\`other\\` = v` (one row, a defensive "only if it
    still has the value I expect" guard) falls back to `parse_and_equality_conditions` - real
    precedent: Frozen Orb 300001's `flags_extra`/`CreatureDisplayID` point fixes in
    `data/sql/updates/db_world/2026_09_01_01.sql`. Only the condition naming `table.index_column`
    is used to find the row; a condition on any other column is the guard and isn't re-checked - a
    replay processes migrations exactly once, in file order, so by the time it reaches this
    statement the guard is expected to already hold."""
    assignments, pos = _read_set_assignments(text, pos, variables)
    if not assignments:
        return _skip_statement(text, pos)
    m = _WHERE_EQ_RE.match(text, pos)
    if m:
        ids, end = [int(m.group("id"))], m.end()
    else:
        m = _WHERE_IN_RE.match(text, pos)
        if m:
            ids, end = _parse_id_list(m.group("ids")), m.end()
        else:
            m = _WHERE_ANY_RE.match(text, pos)
            conditions = parse_and_equality_conditions(m.group("conds")) if m else None
            by_col = dict(conditions) if conditions else {}
            if m is None or table.index_column not in by_col:
                return _skip_statement(text, pos)
            ids, end = [by_col[table.index_column]], m.end()
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
    \\`col\\` = n`, `UPDATE ... SET col = val, ... WHERE \\`col\\` = n` and
    `UPDATE ... WHERE \\`col\\` = n AND \\`other\\` = v` (a defensive guard -
    see `_apply_update`'s docstring) shapes seen in this repo's migration
    history. A statement it doesn't recognize (an OR'd or ranged WHERE, a
    table this replay wasn't told to expect, a malformed row) is silently
    skipped rather than raising - safe because
    the emitted SQL always comes from source CSV/YAML data
    (`resolve.resolve_rows`'s `build_one(entry)`), never from `rows` itself;
    an imperfect replay can only leave an ID looking "changed" when it
    isn't (today's bug, just smaller in scope), never write wrong data."""
    pos = 0
    variables: dict[str, int] = {}
    while True:
        m = _next_statement(sql_text, pos, table.sql_table)
        if m is None:
            return
        try:
            if m.group("set_name") is not None:
                variables[m.group("set_name")] = int(m.group("set_value"))
                pos = m.end()
            elif m.group("ins_table") is not None:
                pos = _apply_insert(rows, table, sql_text, m, variables)
            elif m.group("del_table") is not None:
                pos = _apply_delete(rows, sql_text, m.end())
            else:
                pos = _apply_update(rows, table, sql_text, m.end(), variables)
        except Exception:
            pos = _skip_statement(sql_text, m.end())


# ---------------------------------------------------------------------------
# `apply_statements`'s composite-key cousin: a table keyed on more than one column (e.g.
# creature_template_model's (CreatureID, Idx)) has no single `table.index_column` for
# `_apply_insert`/`_apply_delete`/`_apply_update` to key `rows` by. Built for the same reason as
# the AND-guard fallback above: creature_template_model's real migration history has genuine
# hand-written UPDATEs and single-column DELETEs after the original INSERT (Frozen Orb 300001's
# CreatureDisplayID went through several revisions this way, data/sql/updates/db_world/
# 2026_09_01_01.sql) - a plain union of INSERTs (trainer_state.load_table_rows) keeps reporting
# the *original* INSERT's values as live forever.
# ---------------------------------------------------------------------------


_COND_RE = re.compile(
    r"^`(?P<col>\w+)`\s*(?:"
    r"=\s*(?P<eq>-?\d+)"
    r"|IN\s*\((?P<in>[^)]*)\)"
    r"|BETWEEN\s+(?P<lo>-?\d+)\s*\|\s*(?P<hi>-?\d+)"
    r")$",
    re.IGNORECASE,
)
_BETWEEN_RE = re.compile(r"BETWEEN\s+(-?\d+)\s+AND\s+(-?\d+)", re.IGNORECASE)


def _split_top_level(text: str, word: str) -> list[str]:
    """Splits `text` on the keyword `word` (AND/OR) outside parentheses; a parenthesised IN list
    never contains one, but an OR-of-ANDs does."""
    parts, depth, start = [], 0, 0
    pattern = re.compile(rf"\s+{word}\s+", re.IGNORECASE)
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0:
            m = pattern.match(text, i)
            if m:
                parts.append(text[start:i])
                start = i = m.end()
                continue
        i += 1
    parts.append(text[start:])
    return [p.strip() for p in parts]


def _strip_outer_parens(text: str) -> str:
    text = text.strip()
    while text.startswith("(") and text.endswith(")"):
        depth = 0
        for i, ch in enumerate(text):
            depth += ch == "("
            depth -= ch == ")"
            if depth == 0 and i < len(text) - 1:
                return text  # the first '(' closes before the end: not one wrapping pair
        text = text[1:-1].strip()
    return text


def parse_where_predicate(where_text: str, lenient: bool = False):
    """A WHERE clause as a `row -> bool` callable, or None when any part is outside the supported
    grammar: OR of (parenthesised) AND chains of `` `col` = n``, `` `col` IN (n, ...)`` and
    `` `col` BETWEEN a AND b``. `lenient` makes a condition on a column the row does not hold count
    as satisfied (an UPDATE's guard, where "unknown" must not block the fix); the default treats it
    as not matching (a DELETE must not remove what it cannot judge). Built so a composite-key replay
    can apply the hand-written
    DELETE/UPDATE shapes this repo actually contains (`TrainerId = 1 AND SpellId = 71` point
    deletes, `BETWEEN` ranges, the OR-of-AND form) instead of silently ignoring them."""
    text = _BETWEEN_RE.sub(lambda m: f"BETWEEN {m.group(1)}|{m.group(2)}", where_text.strip())
    disjuncts = []
    pins = []  # per disjunct: {column: the finite set of values it admits} for the `=` / `IN` conditions
    for or_part in _split_top_level(_strip_outer_parens(text), "OR"):
        conds = []
        pinned: dict[str, frozenset] = {}
        for and_part in _split_top_level(_strip_outer_parens(or_part), "AND"):
            m = _COND_RE.match(_strip_outer_parens(and_part))
            if not m:
                return None
            col = m.group("col")
            if m.group("eq") is not None:
                value = int(m.group("eq"))
                conds.append((col, lambda v, value=value: v == value))
                admitted = frozenset((value,))
            elif m.group("in") is not None:
                try:
                    values = {int(x) for x in m.group("in").split(",") if x.strip()}
                except ValueError:
                    return None
                conds.append((col, lambda v, values=values: v in values))
                admitted = frozenset(values)
            else:
                lo, hi = int(m.group("lo")), int(m.group("hi"))
                conds.append((col, lambda v, lo=lo, hi=hi: v is not None and lo <= v <= hi))
                continue
            # Two conditions on one column both have to hold: the intersection.
            pinned[col] = pinned[col] & admitted if col in pinned else admitted
        disjuncts.append(conds)
        pins.append(pinned)

    def predicate(row: dict) -> bool:
        return any(
            all(lenient if col not in row else test(row[col]) for col, test in conds)
            for conds in disjuncts
        )

    predicate.pins = pins  # lets a replay look candidate rows up by key instead of testing every row
    return predicate


def _names_key_column(where_text: str, key_columns: tuple[str, ...]) -> bool:
    """Whether a WHERE clause filters on at least one key column. The general predicate is only
    trusted then; a filter purely on other columns stays "skipped, never guessed at"."""
    return any(f"`{c}`" in where_text for c in key_columns)


def _apply_composite_delete(
    rows: dict[tuple, dict], key_columns: tuple[str, ...], text: str, pos: int,
    report: Callable[[str], None] | None = None,
) -> int:
    start = pos
    m = _DELETE_WHERE_TUPLE_IN_RE.match(text, pos)
    if m:
        delete_cols = tuple(c.strip().strip("`") for c in m.group("cols").split(","))
        tuples, end = _read_key_tuples(text, m.end())
        end = _skip_statement(text, end)
        if delete_cols == key_columns:
            for values in tuples:
                rows.pop(tuple(values), None)
            return end
        try:
            idx = [key_columns.index(c) for c in delete_cols]
        except ValueError:
            if report:
                report(text[start:start + 120])
            return end  # a column we don't key on - can't tell what it removes
        # One pass for every listed value (was one pass per value): the same keys go either way.
        wanted_all = {tuple(values) for values in tuples}
        for key in [k for k in rows if tuple(k[i] for i in idx) in wanted_all]:
            rows.pop(key, None)
        return end
    for pattern in (_WHERE_IN_RE, _WHERE_EQ_RE):
        m = pattern.match(text, pos)
        if m:
            col = re.search(r"`(\w+)`", m.group(0)).group(1)
            if col in key_columns:
                idx = key_columns.index(col)
                if pattern is _WHERE_IN_RE:
                    wanted = set(_parse_id_list(m.group("ids")))
                else:
                    wanted = {int(m.group("id"))}
                for key in [k for k in rows if k[idx] in wanted]:
                    rows.pop(key, None)
                return m.end()
            break  # a non-key column: the general predicate below can still apply it
    m = _WHERE_ANY_RE.match(text, pos)
    predicate = (
        parse_where_predicate(m.group("conds")) if m and _names_key_column(m.group("conds"), key_columns) else None
    )
    if predicate is not None:
        for key in [k for k, row in rows.items() if predicate(row)]:
            rows.pop(key, None)
        return m.end()
    if report:
        report(text[start:start + 120])
    return _skip_statement(text, pos)


_MISSING = object()


class _KeyIndex:
    """Rows of a composite-key replay looked up by what they *contain* in the key columns.

    The dict a replay builds is keyed by the key tuple taken at INSERT time, but `UPDATE .. SET <key column> = ..`
    rewrites a row's content without re-keying it, and a later `WHERE` is judged against the content. So the lookup
    here is by content, not by dict key, and is rebuilt (lazily, O(rows)) after anything that could have changed
    which row holds which key: an INSERT, a DELETE, or an assignment to a key column. Between those (the long runs
    of point `UPDATE`s in the promoted history, 1,203 of them in one upstream merge) it is one dict lookup each
    instead of a scan of every row."""

    def __init__(self, rows: dict[tuple, dict], key_columns: tuple[str, ...]):
        self.rows = rows
        self.key_columns = key_columns
        self._map: dict[tuple, list[dict]] | None = None

    def invalidate(self) -> None:
        self._map = None

    def replaced(self, old: dict | None, new: dict) -> None:
        """An INSERT stored `new` under a dict key, dropping `old` if that key held a row: keep the map current instead
        of rebuilding it (a migration that INSERTs a creature and then UPDATEs it would otherwise rebuild per pair)."""
        if self._map is None or _MISSING in self._map:
            return
        if old is not None:
            bucket = self._map.get(tuple(old.get(c, _MISSING) for c in self.key_columns))
            if bucket is not None:
                for i, row in enumerate(bucket):
                    if row is old:
                        del bucket[i]
                        break
        content = tuple(new.get(c, _MISSING) for c in self.key_columns)
        if _MISSING in content:
            self._map = {_MISSING: []}
        else:
            self._map.setdefault(content, []).append(new)

    def lookup(self, content_key: tuple) -> list[dict] | None:
        """The rows holding exactly `content_key` in the key columns; None when some row lacks a key column (the
        replay's own rows never do, but a caller may hand in any dict), where the caller must scan instead - a
        missing column counts as satisfied there."""
        if self._map is None:
            mapping: dict[tuple, list[dict]] = {}
            for row in self.rows.values():
                content = tuple(row.get(c, _MISSING) for c in self.key_columns)
                if _MISSING in content:
                    mapping = {_MISSING: []}
                    break
                mapping.setdefault(content, []).append(row)
            self._map = mapping
        if _MISSING in self._map:
            return None
        return self._map.get(content_key, [])

    # Most the candidate lookup will enumerate before giving up and letting the caller scan.
    MAX_PINNED_KEYS = 20000

    def pinned_rows(self, pins: list[dict[str, frozenset]]) -> list[dict] | None:
        """Every row that could satisfy a WHERE whose OR-ed branches each pin the key columns (`pins`, from
        `parse_where_predicate`): the rows holding one of the pinned key combinations, each once. None when some
        branch leaves a key column free, or the combinations are too many, or `lookup` cannot answer: scan instead.
        A superset of the matches - the caller still applies the predicate to each."""
        keys: set[tuple] = set()
        total = 0
        for pinned in pins:
            if not all(c in pinned for c in self.key_columns):
                return None
            size = 1
            for c in self.key_columns:
                size *= len(pinned[c])
            total += size
            if total > self.MAX_PINNED_KEYS:
                return None
            keys.update(itertools.product(*(pinned[c] for c in self.key_columns)))
        found: list[dict] = []
        seen: set[int] = set()
        for key in keys:
            rows = self.lookup(key)
            if rows is None:
                return None
            for row in rows:
                if id(row) not in seen:
                    seen.add(id(row))
                    found.append(row)
        return found


def _apply_composite_update(
    rows: dict[tuple, dict], key_columns: tuple[str, ...], text: str, pos: int,
    variables: dict[str, int] | None = None, report: Callable[[str], None] | None = None,
    index: _KeyIndex | None = None,
) -> int:
    """One composite-key UPDATE. Every condition is honoured, key or not, the way MySQL would: a
    row is touched only if all of them hold. A condition on a column the stored row does not hold
    (an INSERT omitted it) cannot be judged and counts as satisfied. A WHERE that names no key
    column, or is outside the supported grammar, is reported and skipped."""
    start = pos
    assignments, pos = _read_set_assignments(text, pos, variables, allow_expr=True)
    m = _WHERE_ANY_RE.match(text, pos) if assignments else None
    if m is None:
        if report:
            report("UPDATE ... SET " + text[start:start + 100])
        return _skip_statement(text, pos)
    end = m.end()
    conditions = parse_and_equality_conditions(m.group("conds"))
    if conditions is not None and any(c in key_columns for c, _ in conditions):
        pinned = dict(conditions)
        if index is not None and len(pinned) == len(conditions) and all(c in pinned for c in key_columns):
            # Every key column is pinned by an equality (and none twice): only rows holding exactly that key can
            # match, so test those instead of every row. The full condition list is still checked on each.
            candidates = index.lookup(tuple(pinned[c] for c in key_columns))
            if candidates is None:
                candidates = rows.values()
        else:
            candidates = rows.values()
        for row in candidates:
            if all(c not in row or row[c] == v for c, v in conditions):
                _assign(row, assignments)
        if index is not None and any(c in key_columns for c in assignments):
            index.invalidate()
        return end
    # Not an AND of equalities naming a key column: IN / BETWEEN / OR, or a filter on non-key columns.
    predicate = (
        parse_where_predicate(m.group("conds"), lenient=True)
        if _names_key_column(m.group("conds"), key_columns) else None
    )
    if predicate is None:
        if report:
            report("UPDATE ... SET " + text[start:start + 100])
        return end
    candidates = index.pinned_rows(predicate.pins) if index is not None else None
    for row in rows.values() if candidates is None else candidates:
        if predicate(row):
            _assign(row, assignments)
    if index is not None and any(c in key_columns for c in assignments):
        index.invalidate()
    return end


def _in_line_comment(text: str, pos: int) -> bool:
    """Whether `pos` sits after a `--` or `#` on its own line."""
    line_start = text.rfind("\n", 0, pos) + 1
    prefix = text[line_start:pos]
    return "--" in prefix or "#" in prefix


def apply_composite_key_statements(
    rows: dict[tuple, dict], columns: tuple[str, ...], key_columns: tuple[str, ...],
    table_name: str, sql_text: str, on_skip: Callable[[str], None] | None = None,
    fill_missing: bool = False,
) -> None:
    """`apply_statements`'s composite-key cousin - see this section's module-level comment for why
    it exists. Handles exactly the statement shapes this repo's real migrations and `sql_out.py`'s
    own renderers use for such a table:
      - `INSERT INTO \\`table\\` (cols...) VALUES (...), ...;` - explicit or full column list.
      - `DELETE FROM \\`table\\` WHERE (\\`a\\`, \\`b\\`) IN ((v1, v2), ...);` -
        `sql_out.render_generic_table_block`'s own key-exact shape.
      - `DELETE FROM \\`table\\` WHERE \\`col\\` = n` / `WHERE \\`col\\` IN (...)` - a single
        column naming one member of `key_columns` (e.g. "delete every model of this creature",
        every `Idx`) - the prefix case, same idea as `spell_tables._matching_keys`.
      - `UPDATE \\`table\\` SET ... WHERE <AND-ed \\`col\\` = value conditions>;` - a point fix.
        Every condition is honoured, key or not, the way MySQL would (see
        `_apply_composite_update`); `SET col = col | n` style self-expressions are evaluated.
      - any other DELETE/UPDATE WHERE made of OR / AND / `=` / `IN (...)` / `BETWEEN`
        (`parse_where_predicate`), e.g. `TrainerId = 212 AND SpellId = 1`.
    An unrecognized shape is skipped, never guessed at - same "degrade safely" contract as
    `apply_statements` - but not silently when `on_skip` is given: it is called with the start of
    each statement the replay could not apply, so a caller whose output depends on the replay
    (the trainer pricing pass) can warn.

    `fill_missing` gives an INSERT's omitted columns the value 0 at INSERT time, so a later WHERE on
    them matches (right only for a table whose omitted columns all default to 0, e.g.
    `trainer_spell`); the default leaves them out, which `TableSpec.defaults` relies on.
    `TRUNCATE` of the table is reported (it empties the table; the replay does not model it)."""
    pos = 0
    variables: dict[str, int] = {}
    if on_skip:
        for t in re.finditer(rf"\bTRUNCATE\s+(?:TABLE\s+)?`?{re.escape(table_name)}`?\b", sql_text, re.IGNORECASE):
            if not _in_line_comment(sql_text, t.start()):
                on_skip(sql_text[t.start():t.start() + 60])
    index = _KeyIndex(rows, key_columns)
    while True:
        m = _next_statement(sql_text, pos, table_name)
        if m is None:
            return
        try:
            if m.group("set_name") is not None:
                variables[m.group("set_name")] = int(m.group("set_value"))
                pos = m.end()
            elif m.group("ins_table") is not None:
                explicit = (
                    [c.strip().strip("`") for c in m.group("cols").split(",")] if m.group("cols") else None
                )
                cols = explicit or list(columns)
                tuples, pos = _read_tuples(sql_text, m.end(), variables)
                for values in tuples:
                    try:
                        if len(values) != len(cols):
                            raise ValueError("column count mismatch")
                        row = dict(zip(cols, values))
                        if fill_missing:
                            for c in columns:
                                row.setdefault(c, 0)
                        key = tuple(row[c] for c in key_columns)
                    except (KeyError, ValueError):
                        if on_skip:
                            on_skip("INSERT row " + repr(values)[:100])
                        continue
                    previous = rows.get(key)
                    rows[key] = row
                    index.replaced(previous, row)
            elif m.group("del_table") is not None:
                index.invalidate()
                pos = _apply_composite_delete(rows, key_columns, sql_text, m.end(), on_skip)
            else:
                pos = _apply_composite_update(rows, key_columns, sql_text, m.end(), variables, on_skip, index)
        except Exception:
            if on_skip:
                on_skip(sql_text[m.start():m.start() + 120])
            pos = _skip_statement(sql_text, m.end())
