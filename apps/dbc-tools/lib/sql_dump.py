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

Since dbc-replay-fix the replays also read session variables and expressions
over them (`_apply_set`, `_Expr`), double-quoted strings, comments inside a
statement, `INSERT IGNORE`, `TRUNCATE`, `ALTER TABLE` column changes and any
WHERE in `parse_where_predicate`'s grammar; every statement they still skip is
recorded in `sqlcorpus.SKIPS` with its reason. Summary of the grammar:
`.agents/docs/systems/dbc-tools.md`, "What the SQL replay reads".
"""

from __future__ import annotations

import bisect
import functools
import itertools
import math
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
    r"(?P<ins_verb>INSERT(?:\s+IGNORE)?|REPLACE)\s+INTO\s+`(?P<table>\w+)`\s*(?:\((?P<cols>[^)]*)\))?\s*VALUES?\s*",
    re.IGNORECASE,
)


class ReplaySkip(ValueError):
    """A statement (or a value in one) the replay cannot apply; the message is the reason the skip log records."""


class _Unresolved:
    """The value of a session variable the replay could not compute (`SET @x := (SELECT ...)`): using it skips the
    statement, with this reason."""

    __slots__ = ("reason",)

    def __init__(self, reason: str):
        self.reason = reason

    def __reduce__(self):
        return (_Unresolved, (self.reason,))


# MySQL's backslash escapes inside a string literal; any other `\x` is just `x`.
_MYSQL_ESCAPES = {"n": "\n", "r": "\r", "t": "\t", "0": "\0", "b": "\b", "Z": "\x1a"}

# A numeric literal as `_read_value` reads a bare token: decimal int, float, or `0x` hex.
_NUMBER_TOKEN_RE = re.compile(r"[-+]?(?:0[xX][0-9a-fA-F]+|\d+(?:\.\d*)?(?:[eE][-+]?\d+)?|\.\d+(?:[eE][-+]?\d+)?)")
_OPERATOR_START = frozenset("+-*|&")


def _number(token: str):
    """A bare numeric token as `int` / `float` (hex as int); ValueError for anything else."""
    if token[:2].lower() == "0x":
        # MySQL hex literal (`0x10`) - common in hand-written spell_proc rows for
        # ProcFlags/HitMask. Checked before the float branch since a hex digit
        # can be 'e'.
        return int(token, 16)
    return float(token) if "." in token or "e" in token.lower() else int(token)


def _read_string(text: str, i: int) -> tuple[str, int]:
    """The quoted string literal at `text[i]` (`'...'` or `"..."`): MySQL's backslash escapes and a doubled quote
    character. Returns (value, index just past the closing quote)."""
    quote = text[i]
    n = len(text)
    j = i + 1
    buf = []
    while True:
        ch = text[j]
        if ch == "\\":
            escaped = text[j + 1]
            if escaped in "%_":  # MySQL keeps the backslash for these two (LIKE wildcards)
                buf.append("\\")
            buf.append(_MYSQL_ESCAPES.get(escaped, escaped))
            j += 2
            continue
        if ch == quote:
            if j + 1 < n and text[j + 1] == quote:
                buf.append(quote)
                j += 2
                continue
            break
        buf.append(ch)
        j += 1
    return "".join(buf), j + 1


def _variable(variables: dict | None, name: str):
    """The value of session variable `name` (MySQL variable names are case-insensitive)."""
    if variables is None or name.lower() not in variables:
        raise ReplaySkip(f"unknown session variable {name}")
    value = variables[name.lower()]
    if isinstance(value, _Unresolved):
        raise ReplaySkip(f"session variable {name} has no value the replay can compute ({value.reason})")
    return value


class _Expr:
    """A recursive-descent reader for the value expressions upstream and hand-written SQL write: integer (and float)
    arithmetic over literals and session variables. MySQL's precedence, highest first: unary `-`/`+`/`~`, `*`, `+`/`-`,
    `&`, `|`; parentheses; decimal, float and `0x` hex numbers, quoted strings, `NULL`, `@var`. Anything else (a
    function call, a subquery, a column name) raises `ReplaySkip`. `~` is MySQL's 64-bit unsigned NOT."""

    __slots__ = ("text", "pos", "variables", "row")

    def __init__(self, text: str, pos: int, variables: dict | None, row: dict | None = None):
        # `row`: the values a `` `column` `` reads (an UPDATE's `_RowExpr`); `_PROBE_ROW` reads 1 for any column;
        # None: a column is not a value.
        self.text, self.pos, self.variables, self.row = text, pos, variables, row

    def _peek(self) -> str:
        text, n = self.text, len(self.text)
        while self.pos < n and text[self.pos] in " \t\r\n":
            self.pos += 1
        return text[self.pos] if self.pos < n else ""

    def _fail(self, what: str):
        raise ReplaySkip(f"unsupported value expression ({what} at {self.text[self.pos:self.pos + 24]!r})")

    def _binary(self, op: str, a, b):
        try:
            if op == "*":
                return a * b
            if op == "+":
                return a + b
            if op == "-":
                return a - b
            if op == "&":
                return a & b
            return a | b
        except TypeError:
            self._fail(f"{op} on {type(a).__name__} and {type(b).__name__}")

    def parse(self):
        return self._bitor()

    def _bitor(self):
        value = self._bitand()
        while self._peek() == "|" and self.text[self.pos + 1:self.pos + 2] != "|":
            self.pos += 1
            value = self._binary("|", value, self._bitand())
        return value

    def _bitand(self):
        value = self._additive()
        while self._peek() == "&" and self.text[self.pos + 1:self.pos + 2] != "&":
            self.pos += 1
            value = self._binary("&", value, self._additive())
        return value

    def _additive(self):
        value = self._term()
        while True:
            ch = self._peek()
            if ch == "+" or (ch == "-" and not _is_comment(self.text, self.pos)):
                self.pos += 1
                value = self._binary(ch, value, self._term())
            else:
                return value

    def _term(self):
        value = self._unary()
        while self._peek() == "*":
            self.pos += 1
            value = self._binary("*", value, self._unary())
        return value

    def _unary(self):
        ch = self._peek()
        if ch in "-+~" and ch and not (ch == "-" and _is_comment(self.text, self.pos)):
            self.pos += 1
            value = self._unary()
            if not isinstance(value, (int, float)) or (ch == "~" and not isinstance(value, int)):
                self._fail(f"unary {ch} on {type(value).__name__}")
            if ch == "-":
                return -value
            if ch == "~":
                return ~value & 0xFFFFFFFFFFFFFFFF
            return value
        return self._primary()

    def _primary(self):
        text = self.text
        ch = self._peek()
        if ch == "(":
            self.pos += 1
            value = self._bitor()
            if self._peek() != ")":
                self._fail("unbalanced parenthesis")
            self.pos += 1
            return value
        if ch == "@":
            m = _VAR_NAME_RE.match(text, self.pos)
            if m is None:
                self._fail("a system variable")  # `@@SQL_MODE` (a dump's preamble)
            self.pos = m.end()
            return _variable(self.variables, m.group(0))
        if ch in "'\"":
            value, self.pos = _read_string(text, self.pos)
            return value
        if ch == "`" and self.row is not None:
            end = text.find("`", self.pos + 1)
            if end == -1:
                self._fail("unterminated column name")
            column = text[self.pos + 1:end]
            self.pos = end + 1
            if self.row is _PROBE_ROW:
                return 1
            if column not in self.row:
                raise ReplaySkip(f"the row has no {column} to compute with")
            return self.row[column]
        keyword = _KEYWORD_RE.match(text, self.pos)
        if keyword is not None:
            self.pos = keyword.end()
            return _KEYWORDS[keyword.group(0).upper()]
        m = _NUMBER_TOKEN_RE.match(text, self.pos)
        if m is None or text[m.start()] in "+-" or text[m.end():m.end() + 1].isalnum():
            self._fail("not a number, variable or parenthesis")
        self.pos = m.end()
        return _number(m.group(0))


_VAR_NAME_RE = re.compile(r"@\w+")
# The value keywords MySQL accepts in any letter case: `NULL`, and `TRUE` / `FALSE` (1 / 0).
_KEYWORD_RE = re.compile(r"(?:NULL|TRUE|FALSE)(?![\w])", re.IGNORECASE)
_KEYWORDS = {"NULL": None, "TRUE": 1, "FALSE": 0}
_PROBE_ROW: dict = {}  # `_Expr(row=_PROBE_ROW)`: parse a column expression without a row (every column reads 1)


def _is_comment(text: str, i: int) -> bool:
    """Whether `text[i]` starts a `-- ` line comment (MySQL needs whitespace or the end after the two dashes)."""
    return text.startswith("--", i) and (i + 2 >= len(text) or text[i + 2] in " \t\r\n")


def _eval_expr(text: str, i: int, variables: dict | None) -> tuple[object, int]:
    """The value expression at `text[i]` (see `_Expr`) and the index just past it."""
    parser = _Expr(text, i, variables)
    value = parser.parse()
    return value, parser.pos


def _read_value(
    text: str, i: int, terminators: str = ",)", variables: dict | None = None
) -> tuple[object, int]:
    """Parse a single SQL value starting at `text[i]` (leading whitespace already skipped by the caller). Returns
    (value, index_just_past_it). `terminators` bounds a bare numeric token - widen it for a value not immediately
    followed by ',' or ')' (e.g. the last assignment in an `UPDATE ... SET` clause, followed by whitespace then
    `WHERE`).

    A literal is a quoted string (`'...'` or `"..."`), `NULL` or a number (int, float, `0x` hex). Anything else is read
    as a value expression (`_Expr`) over `variables` (the session variables an earlier `SET @name := ...;` of the same
    file assigned, see `_apply_set`): `@GUID`, `@GUID+15`, `(@GUID+15)`, `-@GUID`, `@ENTRY*100+1`, `-(@CGUID+27)`.
    The frozen phase 0's trainer rewiring (`replay/frozen/`) and upstream's spawn and SmartAI files are written this
    way. An unknown variable, or `variables=None`, raises `ReplaySkip` like any other value the replay cannot read."""
    ch = text[i]
    if ch == "'" or ch == '"':
        return _read_string(text, i)
    if text[i : i + 4] == "NULL":
        return None, i + 4
    if ch in "nNtTfF":  # `null`, `true`, `false` in any letter case (`NULL` is the common case above)
        keyword = _KEYWORD_RE.match(text, i)
        if keyword is not None:
            return _KEYWORDS[keyword.group(0).upper()], keyword.end()
    if ch == "@" or ch == "(" or ch == "~" or (ch in "-+" and _operand_follows(text, i + 1)):
        return _eval_expr(text, i, variables)
    j = i
    while text[j] not in terminators:
        j += 1
    token = text[i:j].strip()
    try:
        value = _number(token)
    except ValueError:
        # `100*@X`, `5 + 3`, or something the expression reader will name in its error (a function call, ...).
        return _eval_expr(text, i, variables)
    k = j
    n = len(text)
    while k < n and text[k] in " \t\r\n":
        k += 1
    if k < n and text[k] in _OPERATOR_START and not _is_comment(text, k):
        return _eval_expr(text, i, variables)  # the number is the first operand of `5 * @X` (a SET's terminators)
    return value, j


def _operand_follows(text: str, i: int) -> bool:
    """Whether a `-`/`+` at `i - 1` is the unary sign of a parenthesis or a variable (`-@GUID`, `-(@CGUID+27)`)."""
    n = len(text)
    while i < n and text[i] in " \t\r\n":
        i += 1
    return i < n and text[i] in "@("


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
# treats it as an alternate tuple-list terminator, same as a bare ';', and hands the clause's span back; a row
# whose key is new is inserted as written, and an existing row gets only the clause's assignments
# (`_upsert_assignments` / `_apply_upsert`), the way MySQL runs it.
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
    text: str, start: int, variables: dict[str, int] | None = None, *, fast: bool = True,
    upsert: list | None = None,
) -> tuple[list[list], int]:
    """Parse a comma-separated list of parenthesized value-tuples starting at
    `text[start]` (which must be '('), stopping at the terminating ';' - or,
    for an `INSERT ... ON DUPLICATE KEY UPDATE` upsert, at the `ON DUPLICATE
    KEY UPDATE` clause that follows the last tuple (see `_ON_DUPLICATE_RE`),
    in which case the whole clause is skipped to the statement's real
    terminating ';' via `_skip_statement` - safe because this repo's upsert
    shape never has an embedded ';' inside that clause. Returns (tuples,
    index_just_past_the_semicolon). `fast=False` forces the character-level parser for every tuple (the reference the
    fast path is tested against). `upsert` (a list): gets the `(start, end)` of the `ON DUPLICATE KEY UPDATE`
    clause's assignments when there is one (`_upsert_assignments` reads them)."""
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
        duplicate = _ON_DUPLICATE_RE.match(text, i)
        if duplicate:
            end = _skip_statement(text, i)
            if upsert is not None:
                upsert.append((duplicate.end(), end - 1 if text[end - 1:end] == ";" else end))
            return tuples, end
    raise ValueError("unterminated INSERT statement (no trailing ';' found)")


_COL_EQ_RE = re.compile(r"`(?P<col>\w+)`\s*=\s*")


class _RowExpr:
    """An UPDATE assignment whose value reads columns of the row (`flags = flags | 64`, `mask = mask & ~(1 | 2 | 4)`,
    `(`event_flags` & ~1)`): `_Expr` over the expression text, the row's current values supplying the columns.
    Called with the row; raises `ReplaySkip` when the row does not hold a column it reads (an INSERT omitted it) or
    the value is not a number."""

    __slots__ = ("text", "variables")

    def __init__(self, text: str, variables: dict | None):
        self.text, self.variables = text, variables

    def __call__(self, row: dict):
        parser = _Expr(self.text, 0, self.variables, row)
        return parser.parse()


class _Chain:
    """Two assignments to one column in one `SET` (`unit_flags = unit_flags & ~2, unit_flags = unit_flags | 256`,
    2026_01_22_04.sql): MySQL applies them left to right."""

    __slots__ = ("col", "first", "second")

    def __init__(self, col: str, first, second):
        self.col, self.first, self.second = col, first, second

    def __call__(self, row: dict):
        staged = dict(row)
        staged[self.col] = self.first(row) if callable(self.first) else self.first
        return self.second(staged) if callable(self.second) else self.second


def _int_value(value):
    """`value` as MySQL stores it in an integer column: a non-integer number rounded half away from zero (`SET
    MoneyCost = MoneyCost * 0.2` stores 2469 for 2469.4, 13 for 12.6); anything else unchanged."""
    if isinstance(value, float) and math.isfinite(value):
        magnitude = math.floor(abs(value) + 0.5 + abs(value) * 1e-12)
        return magnitude if value >= 0 else -magnitude
    return value


def _evaluate(value, row: dict, defaults: dict | None):
    """An assignment's value for `row`: a literal as it is, a `_RowExpr` / `_Chain` evaluated over the row. A column
    the row does not hold (an INSERT omitted it) reads its schema default from `defaults`, as MySQL's stored row
    would; without one `ReplaySkip` propagates."""
    if not callable(value):
        return value
    try:
        return value(row)
    except ReplaySkip:
        if not defaults:
            raise
        return value({**defaults, **row})


def _assign(
    row: dict, assignments: dict, defaults: dict | None = None, int_columns: frozenset = frozenset(),
    modeled: frozenset | None = None,
) -> int:
    """Applies `_read_set_assignments(..., allow_expr=True)` output to `row`, left to right (an expression sees the
    columns earlier assignments set, as in MySQL). A number written to an integer column (`int_columns`) is rounded
    the way MySQL stores it (`_int_value`). Returns how many assignments to a column the replay models (`modeled`;
    None: every column) could not be evaluated (a column neither the row nor `defaults` holds, a value that is not a
    number); the caller records them, so none is left out silently. A column the table no longer has (an UPDATE of
    `mechanic_immune_mask` before upstream dropped it) is not replayed at all."""
    failures = 0
    for col, value in assignments.items():
        try:
            value = _evaluate(value, row, defaults)
        except ReplaySkip:
            failures += modeled is None or col in modeled
            continue
        row[col] = _int_value(value) if col in int_columns else value
    return failures


def _not_assigned(failures: int) -> ReplaySkip:
    return ReplaySkip(
        f"{failures} assignment(s) not applied: an expression reads a column the row does not hold and the schema "
        f"gives no default for"
    )


_UPSERT_PART_RE = re.compile(r"\s*`(?P<col>\w+)`\s*=\s*(?P<expr>[\s\S]*?)\s*$")
_VALUES_FUNCTION_RE = re.compile(r"VALUES\s*\(\s*`(?P<col>\w+)`\s*\)$", re.IGNORECASE)


def _upsert_assignments(
    clause: str, variables: dict | None, case: "_ColumnCase | None" = None,
) -> list[tuple[str, str, object]]:
    """An `ON DUPLICATE KEY UPDATE` clause as `[(column, "values", source column) | (column, "expr", value)]`, in
    order: `` `c` = VALUES(`c`) `` takes the value the INSERT would have written, any other value is a literal or an
    expression over variables and the existing row's columns (`_RowExpr`). Raises `ReplaySkip` for anything else."""
    parts = []
    for part in _split_top_level_commas(_prepare_statement(clause, variables) if _NEEDS_PREPARING_RE.search(clause)
                                        else clause):
        m = _UPSERT_PART_RE.match(part)
        if m is None or not m.group("expr"):
            raise ReplaySkip(f"unsupported ON DUPLICATE KEY UPDATE assignment ({' '.join(part.split())[:40]})")
        col = case.names_list([m.group("col")])[0] if case else m.group("col")
        expr = m.group("expr")
        source = _VALUES_FUNCTION_RE.match(expr)
        if source is not None:
            parts.append((col, "values", case.names_list([source.group("col")])[0] if case else source.group("col")))
            continue
        probe = _Expr(expr, 0, variables, _PROBE_ROW)
        probe.parse()  # raises when it is not a value expression
        if expr[probe.pos:].strip():
            raise ReplaySkip(f"unsupported ON DUPLICATE KEY UPDATE value ({expr[:40]})")
        parts.append((col, "expr", _RowExpr(expr, variables)))
    return parts


def _apply_upsert(
    existing: dict, inserted: dict, parts: list[tuple[str, str, object]], defaults: dict | None,
    int_columns: frozenset = frozenset(), modeled: frozenset | None = None,
) -> int:
    """What `INSERT ... ON DUPLICATE KEY UPDATE` does to the row that already holds the key: only the clause's
    columns change, left to right; `VALUES(c)` is the INSERT's value of `c` (its schema default when the INSERT left
    it out). Returns the number of assignments that could not be evaluated."""
    failures = 0
    for col, kind, payload in parts:
        if kind == "values":
            value = inserted[payload] if payload in inserted else (defaults or {}).get(payload)
        else:
            try:
                value = _evaluate(payload, existing, defaults)
            except ReplaySkip:
                failures += modeled is None or col in modeled
                continue
        existing[col] = _int_value(value) if col in int_columns else value
    return failures


def _read_set_assignments(
    text: str, start: int, variables: dict | None = None, allow_expr: bool = False,
) -> tuple[dict, int]:
    """Parse a `` `col` = value (, `col` = value)* `` list starting at
    `start` (right after `UPDATE ... SET `), stopping as soon as the next
    `` `col` = `` pattern doesn't match - i.e. at the WHERE clause. Returns
    (assignments, index_at_the_stop_point). With `allow_expr`, a value that reads columns of the row is a `_RowExpr`
    (applied by `_assign`)."""
    assignments: dict = {}
    i = start
    n = len(text)
    while i < n:
        i = _skip_ws_and_comments(text, i)  # `-- InitialMin: 10s` after an assignment (2026_06_13_04.sql)
        m = _COL_EQ_RE.match(text, i)
        if not m:
            break
        try:
            value, i = _read_value(text, m.end(), terminators=" \t\r\n,);", variables=variables)
        except ReplaySkip:
            if not allow_expr:
                raise
            probe = _Expr(text, m.end(), variables, _PROBE_ROW)
            probe.parse()  # raises when it is not an expression over columns either
            value, i = _RowExpr(text[m.end():probe.pos], variables), probe.pos
        col = m.group("col")
        if col in assignments:
            value = _Chain(col, assignments.pop(col), value)
        assignments[col] = value
        i = _skip_ws_and_comments(text, i)
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


def parse_create_table_int_columns(path: Path, table_name: str) -> frozenset[str]:
    """Column names whose SQL type is an integer family (`int`, `tinyint`, ...): where MySQL stores a quoted number
    as an integer and rounds a non-integer one (`apply_composite_key_statements`' `int_columns`)."""
    names = set()
    for line in _create_table_body(path, table_name).splitlines():
        m = _COLUMN_TYPE_RE.match(line)
        if m and m.group("type").lower() in _INT_COLUMN_TYPES:
            names.add(m.group("name"))
    return frozenset(names)


def read_table_rows(
    path: Path, table_name: str, columns: tuple[str, ...], tolerant: bool = False,
) -> list[dict]:
    """Like `read_table_dump`, but for a table with no single-column primary
    key (a composite key, or none at all) — every row is returned as-is in a
    plain list rather than being collapsed into a dict keyed by one column,
    which would silently drop rows that share whatever column got picked.

    A statement it cannot read raises, unless `tolerant`: then that statement is recorded in the skip log
    (`sqlcorpus.SKIPS`) and the rest of the file is still read (a migration's other statements are not lost to one
    odd shape). Session variables are the ones in effect where each statement starts (`_VariableTimeline`)."""
    text = sqlcorpus.read_text(path)
    timeline = _VariableTimeline(text)
    out: list[dict] = []
    pos = 0
    if tolerant:
        query = _next_statement(text, 0, table_name, "X")
        while query is not None:
            _record(table_name, text, query.start(), _INSERT_QUERY_REASON, path.name)
            query = _next_statement(text, _statement_end(text, query.end()), table_name, "X")
    while True:
        m = _next_match(_INSERT_HEAD_RE, text, pos, table_name)
        if not m:
            break
        cols = _column_list(m.group("cols")) or list(columns)
        try:
            tuples, pos = _read_tuples(text, m.end(), timeline.at(m.start()))
            for values in tuples:
                if len(values) != len(cols):
                    raise ReplaySkip(
                        f"{path}: row has {len(values)} values but {len(cols)} columns ({cols[:3]}...)"
                    )
        except (ValueError, IndexError) as exc:
            if not tolerant:
                raise
            _record(table_name, text, m.start(), _reason(exc), path.name)
            pos = _skip_statement(text, m.end())
            continue
        out.extend(dict(zip(cols, values)) for values in tuples)
    return out


_DELETE_HEAD_RE = re.compile(r"DELETE\s+FROM\s+`(?P<table>\w+)`\s*", re.IGNORECASE)
_UPDATE_HEAD_RE = re.compile(r"UPDATE\s+`(?P<table>\w+)`\s+SET\s+", re.IGNORECASE)
_DELETE_WHERE_RANGE_RE = re.compile(
    r"WHERE\s+`\w+`\s+BETWEEN\s+(?P<start>-?\d+)\s+AND\s+(?P<end>-?\d+)\s*;",
    re.IGNORECASE,
)
# Shared by DELETE and UPDATE - "WHERE `col` IN (id1, id2, ...);" means the same thing for both
# (delete/touch every listed row), just with a different statement in front of it.
_WHERE_IN_RE = re.compile(
    r"WHERE\s+`\w+`\s+IN\s*\((?P<ids>[^)'\"]*)\)\s*;",  # no quoted strings: those go to the general predicate
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
# to split further. A ';' inside a quoted string does not end it.
_WHERE_ANY_RE = re.compile(
    r"WHERE\s+(?P<conds>(?:'(?:[^'\\]|\\[\s\S]|'')*'|[^';])+?)\s*;", re.IGNORECASE
)

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
        m = _AND_EQ_COND_RE.fullmatch(_strip_outer_parens(part))
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
    text: str, start: int, variables: dict | None = None
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
    callers only handle one case. A DELETE written with session variables,
    double-quoted strings or comments is read through `_prepared_body` first.

    Complements `read_table_rows` (union of INSERTs, no DELETE replay), which
    stays as-is: it is the right answer for "what is live" across the base
    dump plus every hand-written migration, where DELETE shapes are far more
    varied than the ones `sql_out.py` emits."""
    text = sqlcorpus.read_text(path)
    timeline = _VariableTimeline(text)
    pos = 0
    while pos < len(text):
        ins = _next_match(_INSERT_HEAD_RE, text, pos, table_name)
        dele = _next_match(_DELETE_HEAD_RE, text, pos, table_name)
        if ins is None and dele is None:
            return
        # Whichever comes first in the file - that is the whole point of this function.
        if dele is None or (ins is not None and ins.start() < dele.start()):
            cols = _column_list(ins.group("cols")) or list(columns)
            tuples, pos = _read_tuples(text, ins.end(), timeline.at(ins.start()))
            rows = [dict(zip(cols, v)) for v in tuples if len(v) == len(cols)]
            yield "insert", rows
            continue
        try:
            body, bpos, end = _prepared_body(text, dele.end(), timeline.at(dele.start()))
        except (ValueError, IndexError):
            pos = _skip_statement(text, dele.end())
            yield "delete_unparsed", None
            continue
        pos = end
        m = _DELETE_WHERE_TUPLE_IN_RE.match(body, bpos)
        if m:
            key_cols = tuple(_column_list(m.group("cols")))
            tuples, _ = _read_key_tuples(body, m.end())
            yield "delete", (key_cols, [tuple(v) for v in tuples])
            continue
        m = _WHERE_IN_RE.match(body, bpos)
        if m:
            col = re.search(r"`(\w+)`", m.group(0)).group(1)
            yield "delete", ((col,), [(i,) for i in _parse_id_list(m.group("ids"))])
            continue
        m = _WHERE_EQ_RE.match(body, bpos)
        if m:
            col = re.search(r"`(\w+)`", m.group(0)).group(1)
            yield "delete", ((col,), [(int(m.group("id")),)])
            continue
        yield "delete_unparsed", None


def _parse_id_list(ids_text: str) -> list[int]:
    """The `(...)` body of a `WHERE col IN (...)`, one int per entry, with
    `-- trailing comments` stripped line by line - the frozen phase 0's trainer
    rewiring annotates every CreatureId that way (`913, -- Lyria Du Lac
    <Warrior Trainer>`)."""
    cleaned = "\n".join(line.split("--", 1)[0] for line in ids_text.splitlines())
    try:
        return [int(token.strip()) for token in cleaned.split(",") if token.strip()]
    except ValueError:
        raise ReplaySkip(f"unsupported IN list ({' '.join(ids_text.split())[:40]})") from None


# A string, a comment (MySQL's `-- ` needs whitespace after the dashes), or a statement-ending ';'.
_END_SCAN_RE = re.compile(
    r"'(?:[^'\\]|\\[\s\S])*'|\"(?:[^\"\\]|\\[\s\S])*\"|--(?=[ \t\r\n]|$)[^\n]*|#[^\n]*|/\*[\s\S]*?\*/|;",
    re.MULTILINE,
)
_END_HAZARD_RE = re.compile(r"['\"#]|--|/\*")


def _statement_end(text: str, pos: int) -> int:
    """The index just past the ';' ending the statement that continues at `pos` (a ';' inside a string or a comment
    does not end it), or the end of the text. The plain `find` answers for the usual statement with no quote or
    comment before its ';'."""
    j = text.find(";", pos)
    if j == -1:
        return len(text)
    if _END_HAZARD_RE.search(text, pos, j) is None:
        return j + 1
    for m in _END_SCAN_RE.finditer(text, pos):
        if m.group() == ";":
            return m.end()
    return len(text)


def _skip_statement(text: str, pos: int) -> int:
    """Fallback for a statement shape we don't recognize: advance past the
    statement's ';' so scanning can keep going instead of looping forever."""
    return _statement_end(text, pos)


_BACKTICKED_RE = re.compile(r"`(\w+)`")


class _ColumnCase:
    """MySQL column names are case-insensitive; the replay's rows and parsers are not. Spells a statement's column
    names the way the table's column list does (`WHERE Id = 47680` on `spell_dbc`, whose column is `ID`,
    2026_06_16_07.sql), so a WHERE judges, and a SET writes, the column the row holds."""

    def __init__(self, columns):
        self.canon = {c.lower(): c for c in columns}
        self.names = frozenset(columns)

    def names_list(self, names: list[str]) -> list[str]:
        return [n if n in self.names else self.canon.get(n.lower(), n) for n in names]

    def body(self, text: str, pos: int, end: int) -> tuple[str, int] | None:
        """`(rewritten body, 0)` when the statement `text[pos:end]` spells a column differently, else None."""
        for m in _BACKTICKED_RE.finditer(text, pos, end):
            name = m.group(1)
            if name not in self.names and name.lower() in self.canon:
                return _BACKTICKED_RE.sub(
                    lambda n: f"`{self.canon.get(n.group(1).lower(), n.group(1))}`", text[pos:end],
                ), 0
        return None


def _at_statement_end(text: str, pos: int) -> bool:
    """Whether only blanks and comments stand between `pos` and the statement's `;`."""
    i = _skip_ws_and_comments(text, pos)
    return i < len(text) and text[i] == ";"


def _column_list(cols_text: str | None) -> list[str] | None:
    """An INSERT's explicit column list as names (None when it has none). Backticked names are taken as they are, so
    a `-- comment` inside the list does not become a column."""
    if not cols_text:
        return None
    if "`" in cols_text:
        return re.findall(r"`(\w+)`", cols_text)
    return [c.strip() for c in cols_text.split(",")]


# ---------------------------------------------------------------------------------------------------------------------
# Session variables
#
# Upstream's SQL names its ids through session variables, assigned at the top of a file and used in VALUES tuples,
# SET clauses and WHERE predicates: `SET @CGUID := 12345;`, derived ones (`SET @PATH := @CGUID * 10;`, 2026_09_02_00),
# `SET @x := '2026-01-01 00:00:00';`. MySQL starts each file in a fresh session (DBUpdater runs the client once per
# file), so a replay keeps the variables per file. A `SET` whose value the replay cannot compute (a subquery, `IF()`)
# leaves the variable `_Unresolved`; a statement using it is skipped with that reason.

_NEXT_SET_VAR_RE = re.compile(r"\s*(?P<name>@\w+)\s*:?=\s*")


def _apply_set(text: str, pos: int, name: str, variables: dict) -> int:
    """Evaluates the `SET @name := <value>[, @other := <value>...];` whose first value starts at `pos` into
    `variables` (keys lower case: MySQL variable names are case-insensitive). Returns the index past its ';'."""
    i = pos
    while True:
        try:
            value, i = _read_value(text, i, terminators=" \t\r\n,;", variables=variables)
            i = _skip_ws_and_comments(text, i)
            if i >= len(text) or text[i] not in ",;":
                raise ReplaySkip(f"unsupported SET value at {text[i:i + 24]!r}")
        except (ValueError, IndexError) as exc:
            variables[name.lower()] = _Unresolved(f"SET {name}: {_reason(exc)}")
            return _skip_statement(text, pos)
        variables[name.lower()] = value
        if text[i] == ";":
            return i + 1
        m = _NEXT_SET_VAR_RE.match(text, i + 1)
        if m is None:
            return _skip_statement(text, i)
        name, i = m.group("name"), m.end()


class _VariableTimeline:
    """The session variables in effect at each position of one file, for the readers that jump from one statement of
    their table to the next instead of walking every statement (`read_table_rows`, `read_table_statements`). Built
    by evaluating every `SET @var` head in file order; `at(pos)` is what was assigned before `pos`."""

    def __init__(self, text: str):
        self._starts: list[int] = []
        self._states: list[dict] = []
        if "@" not in text:
            return
        variables: dict = {}
        pos = 0
        while True:
            m = _next_statement(text, pos, "", kinds="S")
            if m is None:
                break
            pos = _apply_set(text, m.end(), m.group("set_name"), variables)
            self._starts.append(m.start())
            self._states.append(dict(variables))

    def at(self, pos: int) -> dict:
        i = bisect.bisect_left(self._starts, pos)
        return self._states[i - 1] if i else {}


# ---------------------------------------------------------------------------------------------------------------------
# Statement bodies the WHERE / SET regexes cannot read as written
#
# `_prepared_body` hands a DELETE / UPDATE body to the shape parsers below with its session-variable expressions
# evaluated (`entryorguid = -(@CGUID+27)` -> `entryorguid = -12372`), its double-quoted strings single-quoted and its
# comments dropped. Only a body that has one of those is rewritten; the rest are read in place.

_NEEDS_PREPARING_RE = re.compile(r"[@\"#]|--|/\*")
_BODY_TOKEN_RE = re.compile(
    r"(?P<str>'(?:[^'\\]|\\[\s\S]|'')*')"
    r"|(?P<dq>\"(?:[^\"\\]|\\[\s\S]|\"\")*\")"
    r"|(?P<comment>--(?=[ \t\r\n]|$)[^\n]*|#[^\n]*|/\*[\s\S]*?\*/)"
    r"|(?P<ident>`[^`]*`)"
    r"|(?P<var>@\w+)"
    r"|(?P<num>0[xX][0-9a-fA-F]+|\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)"
    r"|(?P<word>[A-Za-z_]\w*)"
    r"|(?P<ws>[ \t\r\n]+)"
    r"|(?P<punct>[\s\S])",
    re.MULTILINE,
)
_RUN_PUNCT = frozenset("+-*()")
# A word before a `+`/`-` that makes it a sign, not a binary operator (`BETWEEN -(@GUID+14)`).
_SQL_KEYWORDS = frozenset(
    "AND OR NOT XOR IN BETWEEN WHERE SET IS LIKE VALUES SELECT CASE WHEN THEN ELSE ON BY LIMIT".split()
)


def _prepared_body(
    text: str, pos: int, variables: dict | None, case: "_ColumnCase | None" = None,
) -> tuple[str, int, int]:
    """`(body text, where the statement starts in it, index past the statement's ';' in text)` for the DELETE /
    UPDATE body continuing at `pos`. The body text is `text` itself (start `pos`) unless the statement needs
    `_prepare_statement` or its column names respelled (`case`); raises `ReplaySkip` when a variable in it cannot be
    evaluated."""
    end = _statement_end(text, pos)
    if _NEEDS_PREPARING_RE.search(text, pos, end) is not None:
        body, start, body_end = _prepare_statement(text[pos:end], variables), 0, None
    else:
        body, start, body_end = text, pos, end
    if case is not None:
        respelled = case.body(body, start, len(body) if body_end is None else body_end)
        if respelled is not None:
            body, start = respelled
    return body, start, end


def _prepare_statement(body: str, variables: dict | None) -> str:
    """`body` with every arithmetic run that holds a session variable replaced by its value, double-quoted strings
    single-quoted and comments blanked (see the section comment)."""
    tokens = [(m.lastgroup, m.group()) for m in _BODY_TOKEN_RE.finditer(body)]
    out: list[str] = []
    previous = ("", "")  # the last significant token written to `out`
    i, n = 0, len(tokens)
    while i < n:
        kind, token = tokens[i]
        if _in_run(kind, token) and kind != "ws":
            j = i
            while j < n and _in_run(*tokens[j]):
                j += 1
            run = tokens[i:j]
            if any(k == "var" for k, _ in run):
                out.append(_fold_run(run, previous, variables))
            else:
                out.extend(t for _, t in run)
            significant = [t for t in run if t[0] != "ws"]
            previous = significant[-1] if significant else previous
            i = j
            continue
        if kind == "dq":
            value, _ = _read_string(token, 0)
            token = "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"
            kind = "str"
        elif kind == "comment":
            token, kind = " ", "ws"
        out.append(token)
        if kind != "ws":
            previous = (kind, token)
        i += 1
    return "".join(out)


def _in_run(kind: str, token: str) -> bool:
    return kind in ("var", "num", "ws") or (kind == "punct" and token in _RUN_PUNCT)


def _fold_run(run: list[tuple[str, str]], previous: tuple[str, str], variables: dict | None) -> str:
    """One maximal run of numbers, variables, `+ - * ( )` and blanks that holds a variable, written back with the
    expression in it evaluated. The run's edges are trimmed to the expression first: a `(` or `)` that belongs to the
    surrounding SQL (`IN (@A, @B)`, `(`col` = @A)`) and a leading binary operator (`col + @A`) stay as they are."""
    lead: list[str] = []
    trail: list[str] = []
    core = list(run)
    while core and core[0][0] == "ws":
        lead.append(core.pop(0)[1])
    while core and core[-1][0] == "ws":
        trail.insert(0, core.pop()[1])

    def balance() -> int:
        return sum(1 for k, t in core if t == "(") - sum(1 for k, t in core if t == ")")

    while core and core[0][1] == "(" and balance() > 0:
        lead.append(core.pop(0)[1])
        while core and core[0][0] == "ws":
            lead.append(core.pop(0)[1])
    while core and core[-1][1] == ")" and balance() < 0:
        trail.insert(0, core.pop()[1])
        while core and core[-1][0] == "ws":
            trail.insert(0, core.pop()[1])
    if core and core[0][1] == "(" and previous[0] == "word" and previous[1].upper() == "IN":
        depth = 0
        for idx, (_, t) in enumerate(core):
            depth += (t == "(") - (t == ")")
            if depth == 0:
                break
        if idx == len(core) - 1:  # `IN (@A)`: the list's own parentheses
            lead.append(core.pop(0)[1])
            trail.insert(0, core.pop()[1])
    binary_before = previous[0] in ("ident", "str", "num", "var") or (
        previous[0] == "word" and previous[1].upper() not in _SQL_KEYWORDS
    ) or previous[1] == ")"
    if core and (core[0][1] == "*" or (core[0][1] in "+-" and binary_before)):
        lead.append(core.pop(0)[1])
        while core and core[0][0] == "ws":
            lead.append(core.pop(0)[1])
    expr = "".join(t for _, t in core)
    value, end = _eval_expr(expr, 0, variables)
    if expr[end:].strip():
        raise ReplaySkip(f"unsupported value expression {expr!r}")
    return "".join(lead) + _literal(value) + "".join(trail)


def _literal(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"
    return repr(value)


# ---------------------------------------------------------------------------------------------------------------------
# The skip log

def _reason(exc: BaseException) -> str:
    """A skip reason from an exception: `ReplaySkip`'s own message, else the exception's type and message."""
    if isinstance(exc, ReplaySkip):
        return str(exc)
    text = str(exc)
    return f"{type(exc).__name__}: {text}" if text else type(exc).__name__


def _source_name(text: str, source: str | None) -> str:
    if source:
        return source
    path = getattr(text, "path", None)
    return path.name if path is not None else "?"


def _record(
    table: str, text: str, start: int, reason: str, source: str | None,
    on_skip: Callable[[str], None] | None = None,
) -> None:
    """Records one statement the replay did not apply in `sqlcorpus.SKIPS`, and tells `on_skip` (the callers'
    older, per-statement callback: it gets the statement's start)."""
    sqlcorpus.SKIPS.record(table, _source_name(text, source), start, reason, text[start:start + 160])
    if on_skip:
        on_skip(text[start:start + 120])


def _head_index(text: str, pos: int):
    """The text's `sqlcorpus.HeadIndex` when it came from an active corpus and can answer a search from `pos`
    exactly like the regex would, else None (plain `str`, or a head-like string inside a skipped statement)."""
    if not isinstance(text, sqlcorpus.SqlText):
        return None
    index = text.head_index
    return None if index.overlaps(pos) else index


def _next_match(pattern: re.Pattern, text: str, pos: int, table_name: str) -> re.Match | None:
    """Like `pattern.search(text, pos)`, but skips over matches for a
    different table's statements, and heads inside a `--` / `#` line comment, instead of returning them. On a corpus
    text the precomputed head index answers instead of a regex scan (`pattern` is always one of the two single-kind
    head patterns)."""
    while True:
        m = _next_match_any(pattern, text, pos, table_name)
        if m is None or not _head_in_comment(text, m.start()):
            return m
        pos = m.end()


def _head_in_comment(text: str, start: int) -> bool:
    """Whether a statement head at `start` sits in a comment MySQL never runs: a line comment (`-- INSERT INTO ...`
    kept for reference) or a `/* ... */` block (`_in_block_comment`). A `--` or `#` inside a quoted string earlier on
    the line does not count."""
    return _in_line_comment_strict(text, start) or _in_block_comment(text, start)


def _in_line_comment_strict(text: str, start: int) -> bool:
    line_start = text.rfind("\n", 0, start) + 1
    if line_start == start:
        return False
    prefix = text[line_start:start]
    if "-" not in prefix and "#" not in prefix:
        return False
    for m in _END_SCAN_RE.finditer(prefix):
        token = m.group()
        if token[0] == "#" or token.startswith("--"):
            return True
    return False


@functools.lru_cache(maxsize=4)
def _block_comment_openers(text: str) -> list[int]:
    """Where each `/*` of `text` starts, except MySQL's executable `/*! ... */` (a dump's `/*!40101 SET ... */`, which
    MySQL runs). Cached per text: a str caches its hash, so a lookup is cheap for the corpus' shared texts."""
    return [m.start() for m in _BLOCK_OPEN_RE.finditer(text)]


_BLOCK_OPEN_RE = re.compile(r"/\*(?!!)")


def _in_block_comment(text: str, pos: int) -> bool:
    """Whether `pos` lies inside a `/* ... */` comment: the last `/*` before it is not closed before it, and is not
    itself inside a quoted string or a line comment on its own line."""
    openers = _block_comment_openers(text)
    if not openers:
        return False
    i = bisect.bisect_left(openers, pos) - 1
    while i >= 0:
        opener = openers[i]
        if text.find("*/", opener + 2, pos) != -1:
            return False  # the last comment before `pos` is closed before it (an earlier one is too)
        if not _opener_is_quoted_or_commented(text, opener):
            return True
        i -= 1  # a `/*` inside a string or a line comment opens nothing: look further back
    return False


def _opener_is_quoted_or_commented(text: str, opener: int) -> bool:
    """Whether the `/*` at `opener` sits in a quoted string or a line comment of its line (judged on that line; a
    string spanning lines is not seen)."""
    line_start = text.rfind("\n", 0, opener) + 1
    line_end = text.find("\n", opener)
    for m in _END_SCAN_RE.finditer(text, line_start, len(text) if line_end == -1 else line_end):
        if m.start() >= opener:
            return False  # the scan reached the opener itself: it starts a comment
        if m.end() > opener:
            return True  # a string or a line comment that runs over it
    return False


def _next_match_any(pattern: re.Pattern, text: str, pos: int, table_name: str) -> re.Match | None:
    index = _head_index(text, pos)
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


# `apply_statements`'s own combined head pattern - INSERT/DELETE/UPDATE/SET-var (and ALTER/TRUNCATE) in one
# alternation, with a distinctly-named table group per branch (Python's `re` forbids reusing a group name across
# alternatives). Used by the replays, which used to run `_next_match` for each of
# `_INSERT_HEAD_RE`/`_DELETE_HEAD_RE`/`_UPDATE_HEAD_RE` plus a separate `_SET_VAR_RE.search`,
# independently, every loop iteration - four full scans of the remaining text (each with its own
# "skip past a different table's statement" retry loop) to find one earliest match. Profiling
# `state.load_existing_rows(SPELL)` during the druid-rework Resto pass found this was the actual
# dominant cost of a `generate.py` run (regex `.search()` alone: 148s of a 210s call, most of it
# these three independent per-iteration scans re-walking past hundreds of other tables' statements
# in the same large migration file) - see docs/bugs-and-fixes.md's "generate.py looks hung" entry.
_STATEMENT_HEAD_RE = sqlcorpus.STATEMENT_HEAD_RE


def _next_statement(text: str, pos: int, table_name: str, kinds: str = "IDUSTX") -> re.Match | None:
    """`_next_match`'s counterpart for `_STATEMENT_HEAD_RE`: one combined scan per position
    instead of one per statement kind. `kinds` picks the head kinds (`sqlcorpus.HeadMatch`); a `SET` session-variable
    head is never table-filtered, and a head inside a line comment is passed over (`_head_in_comment`). On a corpus
    text the head index answers (one scan per file, shared by every table's replay)."""
    while True:
        m = _next_statement_any(text, pos, table_name, kinds)
        if m is None or not _head_in_comment(text, m.start()):
            return m
        pos = m.end()


def _next_statement_any(text: str, pos: int, table_name: str, kinds: str):
    index = _head_index(text, pos)
    if index is not None:
        return index.first(pos, table_name, kinds)
    while True:
        m = _STATEMENT_HEAD_RE.search(text, pos)
        if m is None:
            return None
        kind, matched = sqlcorpus.head_kind(m)
        if kind in kinds and (kind == "S" or matched == table_name):
            return m
        pos = m.end()


_INSERT_QUERY_REASON = "INSERT ... SELECT / INSERT ... SET: rows from a query the replay does not evaluate"


def _is_ignore(m) -> bool:
    """Whether an INSERT head is `INSERT IGNORE` (an existing key keeps its row)."""
    verb = m.group("ins_verb")
    return verb is not None and "IGNORE" in verb.upper()


@functools.lru_cache(maxsize=64)
def _int_columns(table: DbcTable) -> frozenset:
    """A DBC-backed table's integer columns (`n` / `i` in its fmt, not read as a string): where MySQL rounds a
    non-integer number it stores."""
    return frozenset(
        col for ch, col in zip(table.fmt, table.columns) if ch in "ni" and col not in table.read_as_string
    )


def _int_key(value):
    """A key value an INSERT wrote as a quoted number (`'5'`) as the integer MySQL stores in an integer column."""
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return value
    return value


def _apply_insert(
    rows: dict[int, dict], table: DbcTable, text: str, m: re.Match,
    variables: dict | None = None, report: Callable[[str], None] | None = None, case: "_ColumnCase | None" = None,
) -> int:
    explicit = _column_list(m.group("cols"))
    columns = (case.names_list(explicit) if case else explicit) if explicit else list(table.columns)
    upsert: list = []
    tuples, pos = _read_tuples(text, m.end(), variables, upsert=upsert)
    parts = _upsert_assignments(text[upsert[0][0]:upsert[0][1]], variables, case) if upsert else None
    string_columns = _string_columns(table)
    ignore = _is_ignore(m)
    index_column = table.index_column
    mismatched: list[int] = []
    failures = 0
    for values in tuples:
        if len(values) != len(columns):
            mismatched.append(len(values))  # not a shape we recognize for this table - skip, don't crash the replay
            continue
        row = dict(zip(columns, values))
        _fill_defaults(row, table, string_columns)
        key = row[index_column]
        if isinstance(key, str):
            key = row[index_column] = _int_key(key)
        existing = rows.get(key)
        if existing is not None:
            if ignore:
                continue
            if parts is not None:
                failures += _apply_upsert(
                    existing, row, parts, None, _int_columns(table), frozenset(table.columns),
                )
                continue
        rows[key] = row
    if mismatched and report:
        report(f"{len(mismatched)} INSERT row(s) not applied: {mismatched[0]} values for {len(columns)} columns")
    if failures and report:
        report(str(_not_assigned(failures)))
    return pos


def _fast_column(m: re.Match) -> str:
    """The one column a `_DELETE_WHERE_RANGE_RE` / `_WHERE_IN_RE` / `_WHERE_EQ_RE` match names."""
    return _BACKTICKED_RE.search(m.group(0)).group(1)


def _apply_delete(
    rows: dict[int, dict], text: str, pos: int, defaults: dict | None = None, index_column: str | None = None,
) -> int:
    """One keyed DELETE. The `BETWEEN` / `IN` / `=` shapes on the index column (`index_column`) are read as row ids;
    any WHERE on another column, and any other shape, is judged on each row (`parse_where_predicate`)."""
    m = _DELETE_WHERE_RANGE_RE.match(text, pos)
    if m and index_column is not None and _fast_column(m) != index_column:
        m = None
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
    if m and (index_column is None or _fast_column(m) == index_column):
        for id_ in _parse_id_list(m.group("ids")):
            rows.pop(id_, None)
        return m.end()
    m = _WHERE_EQ_RE.match(text, pos)
    if m and (index_column is None or _fast_column(m) == index_column):
        rows.pop(int(m.group("id")), None)
        return m.end()
    # The tuple form lib/spell_tables.py emits for every declared table, here with a single key
    # column: `WHERE (`entry`) IN ((200134), (200136));`. Skipping it left deleted spell_bonus_data
    # rows looking live (docs/bugs-and-fixes.md, 2026-10-02).
    m = _DELETE_WHERE_TUPLE_IN_RE.match(text, pos)
    if m and "," not in m.group("cols") and (index_column is None or _column_list(m.group("cols"))[0] == index_column):
        tuples, end = _read_key_tuples(text, m.end())
        for values in tuples:
            rows.pop(int(values[0]), None)
        return _skip_statement(text, end)
    # Any other WHERE in `parse_where_predicate`'s grammar, on any column (a row must hold the value to match).
    m = _WHERE_ANY_RE.match(text, pos)
    predicate = parse_where_predicate(m.group("conds"), defaults=defaults) if m else None
    if predicate is None:
        raise ReplaySkip("unsupported DELETE WHERE")
    for key in [k for k, row in rows.items() if predicate(row)]:
        rows.pop(key, None)
    return m.end()


def _apply_update(
    rows: dict[int, dict], table: DbcTable, text: str, pos: int,
    variables: dict | None = None,
) -> int:
    """One keyed UPDATE, the way MySQL runs it.

    `WHERE id = n` / `WHERE id IN (n, m, ...)` on the index column touch those rows (the second shape is real:
    the Glacial Spike/Fireball cast-time fix, `2026_09_14_01.sql`, repoints both spells' `CastingTimeIndex` in one
    statement). The same shapes on any other column are a filter like any other WHERE.

    An AND of equalities naming the index column (`WHERE ID = n AND other = v`, a defensive "only if it
    still has the value I expect" guard - Frozen Orb 300001's point fixes in `2026_09_01_01.sql`) uses the index
    condition to find the row, and every condition must hold, as in MySQL: a guard that fails leaves the row alone
    (db-import would too). `= NULL` is never true. A condition on a column this table does not model counts as
    satisfied (the replay cannot judge it, and the index column names the row).

    Any other WHERE in `parse_where_predicate`'s grammar is applied to every row it matches (on a column the row
    does not hold, a condition counts as satisfied when the WHERE also names the index column, else not). No WHERE:
    every row. `SET col = col | n` style self-expressions are evaluated; a number written to an integer column is
    rounded as MySQL stores it. Assigning the index column moves the row to its new id (a second row on that id
    makes MySQL refuse the statement: skipped)."""
    assignments, pos = _read_set_assignments(text, pos, variables, allow_expr=True)
    if not assignments:
        raise ReplaySkip("UPDATE SET clause not understood")
    index_column = table.index_column
    if _at_statement_end(text, pos):  # no WHERE: every row
        _update_keyed(rows, table, [k for k, _ in rows.items()], assignments)
        return _skip_statement(text, pos)
    m = _WHERE_EQ_RE.match(text, pos)
    if m and _fast_column(m) == index_column:
        ids, end = [int(m.group("id"))], m.end()
    else:
        m = _WHERE_IN_RE.match(text, pos)
        if m and _fast_column(m) == index_column:
            ids, end = _parse_id_list(m.group("ids")), m.end()
        else:
            m = _WHERE_ANY_RE.match(text, pos)
            if m is None:
                raise ReplaySkip("UPDATE without a WHERE the replay reads")
            end = m.end()
            conditions = parse_and_equality_conditions(m.group("conds"))
            by_col = dict(conditions) if conditions else {}
            if conditions and index_column in by_col and len(by_col) == len(conditions):
                key = _int_key(by_col[index_column])
                row = rows.get(key)
                ids = [key] if row is not None and all(
                    _equality_holds(row, c, v, None, lenient=True) for c, v in conditions
                ) else []
            else:
                names_key = f"`{index_column}`" in m.group("conds")
                predicate = parse_where_predicate(m.group("conds"), lenient=names_key)
                if predicate is None:
                    raise ReplaySkip("unsupported UPDATE WHERE")
                ids = [k for k, row in rows.items() if predicate(row)]
    _update_keyed(rows, table, ids, assignments)
    return end


def _equality_holds(row: dict, col: str, value, defaults: dict | None, lenient: bool) -> bool:
    """`col = value` (one condition of `parse_and_equality_conditions`) for a stored row, as MySQL judges it: `=
    NULL` is never true; strings compare case-insensitively and a number with a numeric string by value (`_same`). A
    column the row does not hold is judged on its schema default (`defaults`) and otherwise counts as `lenient`."""
    if value is None:
        return False
    if col in row:
        return _same(row[col], value)
    if defaults and col in defaults:
        return _same(defaults[col], value)
    return lenient


def _update_keyed(rows: dict[int, dict], table: DbcTable, ids: list, assignments: dict) -> None:
    """`assignments` applied to the keyed rows `ids` (see `_apply_update`)."""
    index_column = table.index_column
    int_columns = _int_columns(table)
    moves = index_column in assignments
    failures = 0
    staged: list[tuple[object, dict, dict]] = []
    for id_ in ids:
        row = rows.get(id_)
        if row is None:
            continue
        target = dict(row) if moves else row
        for col, value in assignments.items():
            try:
                value = _evaluate(value, target, None)
            except ReplaySkip:
                # A column this table does not model is not replayed at all; one it does model must not be left
                # out silently.
                failures += col in table.columns
                continue
            if value is None and col in table.columns and _is_string_column(table, col):
                value = ""
            target[col] = _int_value(value) if col in int_columns else value
        if moves:
            staged.append((id_, row, target))
    if moves and staged:
        old_ids = {id_ for id_, _, _ in staged}
        new_ids = [_int_key(target[index_column]) for _, _, target in staged]
        if len(set(new_ids)) != len(new_ids) or any(
            rows.get(i) is not None and i not in old_ids for i in new_ids
        ):
            raise ReplaySkip("UPDATE would give two rows one key (MySQL refuses the statement); not applied")
        for id_, _, _ in staged:
            rows.pop(id_, None)
        for (_, row, target), new_id in zip(staged, new_ids):
            row.clear()
            row.update(target)
            row[index_column] = new_id
            rows[new_id] = row
    if failures:
        raise _not_assigned(failures)


def apply_statements(
    rows: dict[int, dict], table: DbcTable, sql_text: str, on_skip: Callable[[str], None] | None = None,
    source: str | None = None,
) -> None:
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
    history, any other WHERE in `parse_where_predicate`'s grammar, session
    variables (`_apply_set`), `INSERT IGNORE` and `TRUNCATE`. A statement it
    doesn't recognize (a subquery, a malformed row) is skipped rather than
    raising - safe because the emitted SQL always comes from source CSV/YAML
    data (`resolve.resolve_rows`'s `build_one(entry)`), never from `rows`
    itself; an imperfect replay can only leave an ID looking "changed" when it
    isn't, never write wrong data. Skipped is not silent: each one is recorded
    in `sqlcorpus.SKIPS` with its reason (and passed to `on_skip`). `source`
    names the file in that record (default: the corpus text's own path).

    `rows` needs only `get`, `pop`, item assignment, `items` and `clear` (`stale_overlay._Recorder`)."""
    pos = 0
    variables: dict = {}
    table_name = table.sql_table
    case = _ColumnCase(table.columns)
    while True:
        m = _next_statement(sql_text, pos, table_name)
        if m is None:
            return
        start = m.start()

        def report(reason: str, start=start) -> None:
            _record(table_name, sql_text, start, reason, source, on_skip)

        try:
            if m.group("set_name") is not None:
                pos = _apply_set(sql_text, m.end(), m.group("set_name"), variables)
            elif m.group("sel_table") is not None:
                raise ReplaySkip(_INSERT_QUERY_REASON)
            elif m.group("ins_table") is not None:
                pos = _apply_insert(rows, table, sql_text, m, variables, report, case)
            elif m.group("trunc_table") is not None:
                rows.clear()
                pos = _skip_statement(sql_text, m.end())
            else:
                body, bpos, end = _prepared_body(sql_text, m.end(), variables, case)
                if m.group("del_table") is not None:
                    _apply_delete(rows, body, bpos, index_column=table.index_column)
                else:
                    _apply_update(rows, table, body, bpos, variables)
                pos = end
        except Exception as exc:
            report(_reason(exc))
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


# One condition of a WHERE (`parse_where_predicate`): `col <op> literal`, `col IN (literals)`, `col BETWEEN a AND b`
# (the AND already folded to `|` by `_BETWEEN_RE`), `col IS [NOT] NULL`.
_LITERAL = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?|0[xX][0-9a-fA-F]+|'(?:[^'\\]|\\.|'')*'"
_COND_RE = re.compile(
    r"^`(?P<col>\w+)`\s*(?:"
    rf"(?P<op>=|!=|<>|<=|>=|<|>)\s*(?P<val>{_LITERAL})"
    r"|(?P<notin>NOT\s+)?IN\s*\((?P<in>[^)]*)\)"
    r"|BETWEEN\s+(?P<lo>-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*\|\s*(?P<hi>-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)"
    r"|IS\s+(?P<notnull>NOT\s+)?NULL"
    r")$",
    re.IGNORECASE,
)
# `(`flags_extra` & 512) != 0` (2026_03_25_03.sql, after its `@MASK` is evaluated).
_MASK_COND_RE = re.compile(
    r"^\(\s*`(?P<col>\w+)`\s*&\s*(?P<mask>0[xX][0-9a-fA-F]+|\d+)\s*\)\s*(?P<op>!=|<>|=)\s*(?P<val>\d+)$"
)
# `ABS(`dmg_min1` - 141.647) < 0.01`: item-tools' guard on a FLOAT column (`item_lib/emit._guard_term`; MySQL keeps
# FLOAT in 32 bits, so an exact `=` on a computed value can miss). 1,953 item_template UPDATEs use it.
_ABS_COND_RE = re.compile(
    rf"^ABS\(\s*`(?P<col>\w+)`\s*(?P<sign>[-+])\s*(?P<lit>{_LITERAL})\s*\)"
    rf"\s*(?P<op><=|>=|<|>)\s*(?P<tol>{_LITERAL})$",
    re.IGNORECASE,
)
# The bounds may carry an exponent (`5e-05`: item-tools' float guard around a value near 0.01, `emit._guard_term`).
_BOUND = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
_BETWEEN_RE = re.compile(rf"BETWEEN\s+({_BOUND})\s+AND\s+({_BOUND})", re.IGNORECASE)
_IN_ITEM_RE = re.compile(rf"\s*({_LITERAL})\s*(?:,|$)")


def _split_top_level(text: str, word: str) -> list[str]:
    """Splits `text` on the keyword `word` (AND/OR) outside parentheses and quoted strings; a parenthesised IN list
    never contains one, but an OR-of-ANDs does."""
    parts, depth, start = [], 0, 0
    pattern = re.compile(rf"\s+{word}\s+", re.IGNORECASE)
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "'":
            _, i = _read_string(text, i)
            continue
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


def _where_literal(raw: str):
    """A WHERE literal (`_LITERAL`) as a value; strings compare case-insensitively (`_same`)."""
    if raw.startswith("'"):
        return _read_string(raw, 0)[0]
    return _number(raw)


def _same(a, b) -> bool:
    """`a = b` the way MySQL compares a column with a literal: strings case-insensitively (the default collations
    here are `_ci`), a number with a numeric string by value."""
    if isinstance(a, str) and isinstance(b, str):
        return a.casefold() == b.casefold()
    if isinstance(a, str) or isinstance(b, str):
        try:
            return float(a) == float(b)
        except (TypeError, ValueError):
            return False
    return a == b


def _in_test(values: list, negate: bool):
    """`v [NOT] IN (values)` with `_same`'s semantics, a set lookup per row (an UPDATE's IN list can hold hundreds
    of ids, judged against every candidate row)."""
    numbers = frozenset(x for x in values if not isinstance(x, str))
    strings = frozenset(x.casefold() for x in values if isinstance(x, str))

    def test(v) -> bool:
        if v is None:
            return False
        if isinstance(v, str):
            hit = v.casefold() in strings or (bool(numbers) and any(_same(v, x) for x in numbers))
        else:
            hit = v in numbers or (bool(strings) and any(_same(v, x) for x in strings))
        return hit != negate

    return test


def _compare(op: str, a, b) -> bool:
    if a is None or b is None:
        return False
    if op == "=":
        return _same(a, b)
    if op in ("!=", "<>"):
        return not _same(a, b)
    try:
        if isinstance(a, str) != isinstance(b, str):
            a, b = float(a), float(b)
        elif isinstance(a, str):
            a, b = a.casefold(), b.casefold()
        return {"<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b}[op]
    except (TypeError, ValueError):
        return False


def parse_where_predicate(where_text: str, lenient: bool = False, defaults: dict | None = None):
    """A WHERE clause as a `row -> bool` callable, or None when any part is outside the supported
    grammar: OR of (parenthesised) AND chains of `` `col` <op> literal`` (`=`, `!=`, `<>`, `<`, `>`, `<=`, `>=`;
    a number or a quoted string), `` `col` [NOT] IN (literal, ...)``, `` `col` BETWEEN a AND b``,
    `` `col` IS [NOT] NULL`` and `` ABS(`col` - n) < tolerance`` (item-tools' FLOAT guard); a parenthesised OR group
    inside an AND chain is a nested predicate. A column the row does not hold takes its value from `defaults` (the
    table's schema defaults) when it is there; otherwise `lenient` makes the condition count as satisfied (an
    UPDATE's guard, where "unknown" must not block the fix) and the default treats it as not matching (a DELETE must
    not remove what it cannot judge). Built so a composite-key replay can
    apply the hand-written DELETE/UPDATE shapes this repo actually contains (`TrainerId = 1 AND SpellId = 71` point
    deletes, `BETWEEN` ranges, the OR-of-AND form) instead of silently ignoring them."""
    text = _BETWEEN_RE.sub(lambda m: f"BETWEEN {m.group(1)}|{m.group(2)}", where_text.strip())
    defaults = defaults or {}
    disjuncts = []
    pins = []  # per disjunct: {column: the finite set of values it admits} for the numeric `=` / `IN` conditions
    for or_part in _split_top_level(_strip_outer_parens(text), "OR"):
        conds = []
        pinned: dict[str, frozenset] = {}
        for and_part in _split_top_level(_strip_outer_parens(or_part), "AND"):
            inner = _strip_outer_parens(and_part)
            if len(_split_top_level(inner, "OR")) > 1:
                # A parenthesised OR inside an AND chain (`Entry` IN (...) AND (`Reference` BETWEEN .. OR ..),
                # 2026_02_20_03.sql; 2026_09_09_04.sql): a nested predicate, judged on the whole row.
                nested = parse_where_predicate(inner, lenient=lenient, defaults=defaults)
                if nested is None:
                    return None
                conds.append((None, nested))
                continue
            m = _COND_RE.match(inner)
            if not m:
                near = _ABS_COND_RE.match(_strip_outer_parens(and_part))
                if near:
                    lit, tol = _where_literal(near.group("lit")), _where_literal(near.group("tol"))
                    if isinstance(lit, str) or isinstance(tol, str):
                        return None
                    sign = -1 if near.group("sign") == "-" else 1
                    conds.append((near.group("col"), lambda v, lit=lit, tol=tol, sign=sign, op=near.group("op"): (
                        isinstance(v, (int, float)) and _compare(op, abs(v + sign * lit), tol)
                    )))
                    continue
                mask = _MASK_COND_RE.match(and_part.strip())
                if not mask:
                    return None
                bits, op, value = _number(mask.group("mask")), mask.group("op"), int(mask.group("val"))
                conds.append((mask.group("col"), lambda v, bits=bits, op=op, value=value: (
                    isinstance(v, int) and _compare(op, v & bits, value)
                )))
                continue
            col = m.group("col")
            admitted = None
            if m.group("op") is not None:
                op, value = m.group("op"), _where_literal(m.group("val"))
                conds.append((col, lambda v, op=op, value=value: _compare(op, v, value)))
                if op == "=" and not isinstance(value, str):
                    admitted = frozenset((value,))
            elif m.group("in") is not None:
                body = m.group("in")
                values = []
                pos = 0
                while pos < len(body) and body[pos:].strip():
                    item = _IN_ITEM_RE.match(body, pos)
                    if item is None:
                        return None
                    values.append(_where_literal(item.group(1)))
                    pos = item.end()
                negate = m.group("notin") is not None
                conds.append((col, _in_test(values, negate)))
                if not negate and not any(isinstance(x, str) for x in values):
                    admitted = frozenset(values)
            elif m.group("lo") is not None:
                lo, hi = _number(m.group("lo")), _number(m.group("hi"))
                conds.append((col, lambda v, lo=lo, hi=hi: v is not None and _compare(">=", v, lo)
                              and _compare("<=", v, hi)))
            else:
                want_null = m.group("notnull") is None
                conds.append((col, lambda v, want_null=want_null: (v is None) == want_null))
                continue
            if admitted is not None:
                # Two conditions on one column both have to hold: the intersection.
                pinned[col] = pinned[col] & admitted if col in pinned else admitted
        disjuncts.append(conds)
        pins.append(pinned)

    def holds(row: dict, col: str | None, test) -> bool:
        if col is None:  # a nested OR group
            return test(row)
        if col in row:
            return test(row[col])
        if col in defaults:
            return test(defaults[col])
        return lenient

    def predicate(row: dict) -> bool:
        return any(all(holds(row, col, test) for col, test in conds) for conds in disjuncts)

    predicate.pins = pins  # lets a replay look candidate rows up by key instead of testing every row
    return predicate


def _names_key_column(where_text: str, key_columns: tuple[str, ...]) -> bool:
    """Whether a WHERE clause filters on at least one key column (an UPDATE's guard is lenient then)."""
    return any(f"`{c}`" in where_text for c in key_columns)


def _apply_composite_delete(
    rows: dict[tuple, dict], key_columns: tuple[str, ...], text: str, pos: int, defaults: dict | None = None,
    index: "_KeyIndex | None" = None,
) -> int:
    m = _DELETE_WHERE_TUPLE_IN_RE.match(text, pos)
    if m:
        delete_cols = tuple(_column_list(m.group("cols")))
        tuples, end = _read_key_tuples(text, m.end())
        end = _skip_statement(text, end)
        if delete_cols == key_columns:
            for values in tuples:
                _pop(rows, tuple(values), index)
            return end
        # Any other column list: the rows whose values in those columns are one of the listed tuples.
        wanted_all = {tuple(values) for values in tuples}
        for key in [k for k, row in rows.items() if tuple(row.get(c) for c in delete_cols) in wanted_all]:
            _pop(rows, key, index)
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
                # A key an INSERT wrote quoted (`'5'`) still matches `= 5`, as MySQL compares it.
                for key in [k for k in rows if _int_key(k[idx]) in wanted]:
                    _pop(rows, key, index)
                return m.end()
            break  # a non-key column: the general predicate below can still apply it
    # Any other WHERE in `parse_where_predicate`'s grammar, on any column. A condition on a column the row does not
    # hold uses the schema default, else does not match: a DELETE never removes what it cannot judge.
    m = _WHERE_ANY_RE.match(text, pos)
    predicate = parse_where_predicate(m.group("conds"), defaults=defaults) if m else None
    if predicate is None:
        raise ReplaySkip("unsupported DELETE WHERE")
    candidates = index.candidates(predicate.pins) if index is not None else None
    if candidates is None:
        doomed = [k for k, row in rows.items() if predicate(row)]
    else:
        doomed = []
        for row in candidates:
            if predicate(row):
                key = tuple(row.get(c) for c in key_columns)
                if rows.get(key) is row:
                    doomed.append(key)
                else:  # a row an UPDATE re-keyed sits under its INSERT-time key: find it
                    doomed.extend(k for k, r in rows.items() if r is row)
    for key in doomed:
        _pop(rows, key, index)
    return m.end()


def _pop(rows: dict, key: tuple, index: "_KeyIndex | None") -> None:
    row = rows.pop(key, None)
    if row is not None and index is not None:
        index.removed(row)


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
        self._partial: dict[tuple, dict] = {}  # column subset -> {values: [rows]}, see `candidates`

    def invalidate(self) -> None:
        self._map = None
        self._partial: dict[tuple, dict] = {}

    def replaced(self, old: dict | None, new: dict) -> None:
        """An INSERT stored `new` under a dict key, dropping `old` if that key held a row: keep the maps current instead
        of rebuilding them (a migration that INSERTs a creature and then UPDATEs it would otherwise rebuild per
        pair)."""
        if old is not None:
            self.removed(old)
        for cols, mapping in self._partial.items():
            content = tuple(new.get(c, _MISSING) for c in cols)
            if _MISSING in content:
                self._partial = {}
                break
            mapping.setdefault(content, []).append(new)
        if self._map is None or _MISSING in self._map:
            return
        content = tuple(new.get(c, _MISSING) for c in self.key_columns)
        if _MISSING in content:
            self._map = {_MISSING: []}
        else:
            self._map.setdefault(content, []).append(new)

    def removed(self, row: dict) -> None:
        """A DELETE dropped `row`: take it out of the maps instead of rebuilding them (a SmartAI file deletes and
        re-inserts hundreds of scripts, each judged through a partial-key map)."""
        maps = list(self._partial.items())
        if self._map is not None and _MISSING not in self._map:
            maps.append((self.key_columns, self._map))
        for cols, mapping in maps:
            bucket = mapping.get(tuple(row.get(c, _MISSING) for c in cols))
            if bucket:
                for i, held in enumerate(bucket):
                    if held is row:
                        del bucket[i]
                        break

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

    def candidates(self, pins: list[dict[str, frozenset]]) -> list[dict] | None:
        """`pinned_rows`, or when the WHERE pins only some key columns in every branch (`entryorguid = n AND
        source_type = 0` on `smart_scripts`' four-column key), the rows holding one of the pinned value combinations
        of just those columns, from a map built once per column subset (dropped with the main map). None: scan."""
        found = self.pinned_rows(pins)
        if found is not None or not pins:
            return found
        cols = tuple(c for c in self.key_columns if all(c in pinned for pinned in pins))
        if not cols:
            return None
        combos: set[tuple] = set()
        for pinned in pins:
            size = 1
            for c in cols:
                size *= len(pinned[c])
            if len(combos) + size > self.MAX_PINNED_KEYS:
                return None
            combos.update(itertools.product(*(pinned[c] for c in cols)))
        mapping = self._partial.get(cols)
        if mapping is None:
            mapping = {}
            for row in self.rows.values():
                content = tuple(row.get(c, _MISSING) for c in cols)
                if _MISSING in content:
                    return None
                mapping.setdefault(content, []).append(row)
            self._partial[cols] = mapping
        out: list[dict] = []
        seen: set[int] = set()
        for combo in combos:
            for row in mapping.get(combo, ()):
                if id(row) not in seen:
                    seen.add(id(row))
                    out.append(row)
        return out

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
    variables: dict | None = None, index: _KeyIndex | None = None, defaults: dict | None = None,
    int_columns: frozenset = frozenset(), modeled: frozenset | None = None,
) -> int:
    """One composite-key UPDATE. Every condition is honoured, key or not, the way MySQL would: a
    row is touched only if all of them hold (`= NULL` never does). A condition on a column the stored row does not
    hold (an INSERT omitted it) is judged on the schema default when `defaults` has it; otherwise it counts as
    satisfied when the WHERE names a key column, and as not matching when it does not (no key to narrow it). A WHERE
    outside the supported grammar raises `ReplaySkip`. The assignments are applied by `_update_composite` (a key
    column assigned moves the row to its new key)."""
    assignments, pos = _read_set_assignments(text, pos, variables, allow_expr=True)
    if assignments and _at_statement_end(text, pos):  # no WHERE: every row (`SET CreatureImmunitiesId = 0;`)
        _update_composite(rows, key_columns, list(rows.values()), assignments, defaults, index, int_columns, modeled)
        return _skip_statement(text, pos)
    m = _WHERE_ANY_RE.match(text, pos) if assignments else None
    if m is None:
        raise ReplaySkip("UPDATE SET clause or WHERE not understood")
    end = m.end()
    defaults = defaults or {}
    conditions = parse_and_equality_conditions(m.group("conds"))
    if conditions is not None and any(c in key_columns for c, _ in conditions):
        pinned = dict(conditions)
        candidates = None
        if index is not None and len(pinned) == len(conditions) and all(
            c in pinned and pinned[c] is not None and not isinstance(pinned[c], str) for c in key_columns
        ):
            # Every key column is pinned by a numeric equality (and none twice): only rows holding exactly that key
            # can match, so test those instead of every row. The full condition list is still checked on each. A
            # quoted value (`a = '1'`) takes the scan, where it matches a number by value.
            candidates = index.lookup(tuple(pinned[c] for c in key_columns))
        if candidates is None:
            candidates = rows.values()
        matched = [
            row for row in candidates if all(_equality_holds(row, c, v, defaults, True) for c, v in conditions)
        ]
    else:
        # Not an AND of equalities naming a key column: IN / BETWEEN / OR / comparisons, or a filter on non-key
        # columns.
        predicate = parse_where_predicate(
            m.group("conds"), lenient=_names_key_column(m.group("conds"), key_columns), defaults=defaults,
        )
        if predicate is None:
            raise ReplaySkip("unsupported UPDATE WHERE")
        candidates = index.candidates(predicate.pins) if index is not None else None
        matched = [row for row in (rows.values() if candidates is None else candidates) if predicate(row)]
    _update_composite(rows, key_columns, matched, assignments, defaults, index, int_columns, modeled)
    return end


def _content_key(row: dict, key_columns: tuple[str, ...], int_columns: frozenset) -> tuple:
    """The key a row's values give it; a quoted number in an integer key column is the integer MySQL stores."""
    return tuple(_int_key(row.get(c)) if c in int_columns else row.get(c) for c in key_columns)


def _update_composite(
    rows: dict[tuple, dict], key_columns: tuple[str, ...], matched: list[dict], assignments: dict,
    defaults: dict | None, index: _KeyIndex | None, int_columns: frozenset, modeled: frozenset | None = None,
) -> None:
    """`assignments` applied to the `matched` rows. An assignment to a key column moves the row to the key its values
    now give it, as MySQL does, so a later INSERT of the old key is a new row and a later WHERE finds it under the new
    one. When two rows would end up on one key, MySQL refuses the whole statement: nothing is applied and it is
    recorded as skipped. An expression the replay cannot evaluate is recorded too (`_not_assigned`)."""
    failures = 0
    moves = any(c in key_columns for c in assignments)
    if not moves:
        for row in matched:
            failures += _assign(row, assignments, defaults, int_columns, modeled)
    elif matched:
        staged = []
        for row in matched:
            new = dict(row)
            failures += _assign(new, assignments, defaults, int_columns, modeled)
            staged.append((row, _content_key(row, key_columns, int_columns), new,
                           _content_key(new, key_columns, int_columns)))
        old_keys = {old for _, old, _, _ in staged}
        new_keys = [new_key for _, _, _, new_key in staged]
        if len(set(new_keys)) != len(new_keys) or any(k in rows and k not in old_keys for k in new_keys):
            raise ReplaySkip("UPDATE would give two rows one key (MySQL refuses the statement); not applied")
        for row, old, _, _ in staged:
            if rows.get(old) is row:
                del rows[old]
            else:  # a caller's dict filed it under another key
                for key in [k for k, r in rows.items() if r is row]:
                    del rows[key]
        for row, _, new, new_key in staged:
            row.clear()
            row.update(new)
            rows[new_key] = row
        if index is not None:
            index.invalidate()
    if failures:
        raise _not_assigned(failures)


# `ALTER TABLE` clauses that change what a later positional INSERT or a later WHERE means: a renamed, dropped, added
# or moved column (`2026_06_16_00.sql`: `creature.id1` -> `id`, `id2`/`id3` dropped).
_ALTER_RENAME_RE = re.compile(
    r"(?:CHANGE\s+(?:COLUMN\s+)?`(?P<old>\w+)`\s+`(?P<new>\w+)`"
    r"|RENAME\s+COLUMN\s+`(?P<rold>\w+)`\s+TO\s+`(?P<rnew>\w+)`)",
    re.IGNORECASE,
)
_ALTER_DROP_RE = re.compile(r"DROP\s+(?:COLUMN\s+)?`(?P<col>\w+)`", re.IGNORECASE)
_ALTER_ADD_RE = re.compile(r"(?:ADD|MODIFY)\s+(?:COLUMN\s+)?`(?P<col>\w+)`", re.IGNORECASE)
_ALTER_PLACE_RE = re.compile(r"\b(?:FIRST|AFTER\s+`(?P<after>\w+)`)\s*$", re.IGNORECASE)


def _apply_alter(rows: dict, columns: list[str], body: str) -> None:
    """Applies an `ALTER TABLE` body's column changes to `columns` (the positional INSERT layout, in place) and to
    every row (a renamed column is renamed in each row, a dropped one removed). Index, key, engine and type-only
    clauses change nothing the replay keeps."""
    for clause in _split_top_level_commas(body.rstrip().rstrip(";")):
        clause = clause.strip()
        m = _ALTER_RENAME_RE.match(clause)
        if m:
            old, new = (m.group("old"), m.group("new")) if m.group("old") else (m.group("rold"), m.group("rnew"))
            if old != new:
                for row in rows.values():
                    if old in row:
                        row[new] = row.pop(old)
                columns[:] = [new if c == old else c for c in columns]
            _place(columns, new, clause)
            continue
        m = _ALTER_DROP_RE.match(clause)
        if m:
            col = m.group("col")
            for row in rows.values():
                row.pop(col, None)
            columns[:] = [c for c in columns if c != col]
            continue
        m = _ALTER_ADD_RE.match(clause)
        if m:
            col = m.group("col")
            if col not in columns:
                columns.append(col)
            _place(columns, col, clause)


def _place(columns: list[str], col: str, clause: str) -> None:
    """Moves `col` where the clause's trailing `FIRST` / `AFTER \\`x\\`` puts it (nowhere new without one)."""
    m = _ALTER_PLACE_RE.search(clause)
    if m is None or col not in columns:
        return
    columns.remove(col)
    after = m.group("after")
    if after is None:
        columns.insert(0, col)
    elif after in columns:
        columns.insert(columns.index(after) + 1, col)
    else:
        columns.append(col)


def _split_top_level_commas(text: str) -> list[str]:
    parts, depth, start, i, n = [], 0, 0, 0, len(text)
    while i < n:
        ch = text[i]
        if ch in "'\"":
            _, i = _read_string(text, i)
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(text[start:i])
            start = i + 1
        i += 1
    parts.append(text[start:])
    return parts


def _in_line_comment(text: str, pos: int) -> bool:
    """Whether `pos` sits after a `--` or `#` on its own line, or inside a `/* ... */` block comment."""
    line_start = text.rfind("\n", 0, pos) + 1
    prefix = text[line_start:pos]
    return "--" in prefix or "#" in prefix or _in_block_comment(text, pos)


def apply_composite_key_statements(
    rows: dict[tuple, dict], columns: tuple[str, ...], key_columns: tuple[str, ...],
    table_name: str, sql_text: str, on_skip: Callable[[str], None] | None = None,
    fill_missing: bool = False, defaults: dict | None = None, source: str | None = None,
    int_columns: frozenset | None = None, after_statement: Callable[[], None] | None = None,
) -> None:
    """`apply_statements`'s composite-key cousin - see this section's module-level comment for why
    it exists. Handles exactly the statement shapes this repo's real migrations and `sql_out.py`'s
    own renderers use for such a table:
      - `INSERT [IGNORE] INTO \\`table\\` (cols...) VALUES (...), ...;` - explicit or full column list.
      - `DELETE FROM \\`table\\` WHERE (\\`a\\`, \\`b\\`) IN ((v1, v2), ...);` -
        `sql_out.render_generic_table_block`'s own key-exact shape.
      - `DELETE FROM \\`table\\` WHERE \\`col\\` = n` / `WHERE \\`col\\` IN (...)` - a single
        column naming one member of `key_columns` (e.g. "delete every model of this creature",
        every `Idx`) - the prefix case, same idea as `spell_tables._matching_keys`.
      - `UPDATE \\`table\\` SET ... WHERE <AND-ed \\`col\\` = value conditions>;` - a point fix.
        Every condition is honoured, key or not, the way MySQL would (see
        `_apply_composite_update`); `SET col = col | n` style self-expressions are evaluated.
      - any other DELETE/UPDATE WHERE in `parse_where_predicate`'s grammar, on key or other columns
        (e.g. `TrainerId = 212 AND SpellId = 1`, `id = 33838 AND map = 603`).
      - session variables (`_apply_set`) and expressions over them anywhere a value goes, double-quoted strings,
        comments inside a statement (`_prepared_body`).
      - `ALTER TABLE` column renames / drops / adds (`_apply_alter`; the positional column layout follows them for
        the rest of the text) and `TRUNCATE` (empties `rows`).
    An unrecognized shape is skipped, never guessed at - same "degrade safely" contract as
    `apply_statements` - and never silently: it is recorded in `sqlcorpus.SKIPS` with the reason, and `on_skip` is
    called with the start of each statement the replay could not apply, so a caller whose output depends on the
    replay (the trainer pricing pass) can warn. `source` names the file in the record (default: the corpus text's
    path).

    `fill_missing` gives an INSERT's omitted columns the value 0 at INSERT time, so a later WHERE on
    them matches (right only for a table whose omitted columns all default to 0, e.g.
    `trainer_spell`); the default leaves them out, which `TableSpec.defaults` relies on.
    `defaults` (the table's schema defaults, `parse_create_table_defaults`) fills a *key* column an INSERT omitted
    (upstream's Brewfest Reveler rows leave out `smart_scripts.link`, 2026_10_05_00_upstream.sql) and is what a WHERE
    condition on any other omitted column is judged on; no other column is filled in.

    `int_columns` (the table's integer columns, `parse_create_table_int_columns`; none when not given: a default's
    type does not tell a FLOAT `DEFAULT '1'` from an INT) are where MySQL stores numbers: a key written as a quoted
    number (`'5'`) is the integer 5, and a non-integer number an UPDATE writes is rounded (`_int_value`).

    `INSERT ... ON DUPLICATE KEY UPDATE` inserts a new key's row as written and applies only the clause's
    assignments to an existing one. An UPDATE that assigns a key column moves the row to its new key.

    `after_statement` is called after each statement on the table (applied or skipped), for a caller that follows
    how a value changes statement by statement (`trainer_pricing`'s hand-written price)."""
    pos = 0
    variables: dict = {}
    defaults = defaults or {}
    int_columns = int_columns or frozenset()
    layout = list(columns)
    case = _ColumnCase(columns)
    index = _KeyIndex(rows, key_columns)
    while True:
        m = _next_statement(sql_text, pos, table_name, "IDUSATX")
        if m is None:
            return
        start = m.start()

        def report(reason: str, start=start) -> None:
            _record(table_name, sql_text, start, reason, source, on_skip)

        try:
            if m.group("set_name") is not None:
                pos = _apply_set(sql_text, m.end(), m.group("set_name"), variables)
            elif m.group("sel_table") is not None:
                raise ReplaySkip(_INSERT_QUERY_REASON)
            elif m.group("ins_table") is not None:
                explicit = _column_list(m.group("cols"))
                cols = case.names_list(explicit) if explicit else layout
                upsert: list = []
                tuples, pos = _read_tuples(sql_text, m.end(), variables, upsert=upsert)
                parts = (
                    _upsert_assignments(sql_text[upsert[0][0]:upsert[0][1]], variables, case) if upsert else None
                )
                ignore = _is_ignore(m)
                bad: list[str] = []
                failures = 0
                for values in tuples:
                    if len(values) != len(cols):
                        bad.append(f"{len(values)} values for {len(cols)} columns")
                        continue
                    row = dict(zip(cols, values))
                    if fill_missing:
                        for c in columns:
                            row.setdefault(c, 0)
                    try:
                        key = tuple(row[c] if c in row else defaults[c] for c in key_columns)
                    except KeyError as exc:
                        bad.append(f"no value for key column {exc.args[0]}")
                        continue
                    if int_columns and any(isinstance(v, str) for v in key):
                        key = tuple(_int_key(v) if c in int_columns else v for c, v in zip(key_columns, key))
                    for c, v in zip(key_columns, key):
                        row[c] = v
                    previous = rows.get(key)
                    if previous is not None:
                        if ignore:
                            continue
                        if parts is not None:
                            failures += _apply_upsert(
                                previous, row, parts, defaults, int_columns, frozenset(layout) | frozenset(defaults),
                            )
                            if any(c in key_columns for c, _, _ in parts):
                                index.invalidate()
                            continue
                    rows[key] = row
                    index.replaced(previous, row)
                if bad:
                    report(f"{len(bad)} INSERT row(s) not applied: {bad[0]}")
                if failures:
                    report(str(_not_assigned(failures)))
            elif m.group("trunc_table") is not None:
                rows.clear()
                index.invalidate()
                pos = _skip_statement(sql_text, m.end())
            elif m.group("alt_table") is not None:
                end = _statement_end(sql_text, m.end())
                _apply_alter(rows, layout, sql_text[m.end():end])
                index.invalidate()
                pos = end
            else:
                body, bpos, end = _prepared_body(sql_text, m.end(), variables, case)
                if m.group("del_table") is not None:
                    _apply_composite_delete(rows, key_columns, body, bpos, defaults, index)
                else:
                    _apply_composite_update(
                        rows, key_columns, body, bpos, variables, index, defaults, int_columns,
                        frozenset(layout) | frozenset(defaults),
                    )
                pos = end
        except Exception as exc:
            report(_reason(exc))
            pos = _skip_statement(sql_text, m.end())
        if after_statement is not None and m.group("set_name") is None:
            after_statement()
