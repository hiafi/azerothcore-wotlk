"""
Replay vs live, for every table a frozen replay input writes (progression-slim PS1, `lib/frozen_replay.py`).

The question it answers: does the replay (base dump, promoted files with the frozen inputs at their slot, pending,
module SQL) reproduce what the live world DB holds for everything the frozen SQL wrote? The CLI is `replay_diff.py`;
this module is the DB-free part (footprint, comparison, allow list) so it can be unit tested.

**Footprint.** For each table, the replay runs once over the full file list and snapshots the table right before the
first and right after the last frozen file. The footprint is what changed between the two: a row the frozen SQL
inserted (every column), deleted (every column, the row must stay absent unless a later file re-inserts it), or
updated (the columns whose value changed). A frozen statement that sets a cell to the value it already had is not in
the footprint (nothing to check: the replay is right with or without it).

**Comparison.** For each footprint cell, the final replayed value against the live value: both rows absent is a
match, one absent is a `presence` difference, otherwise values are compared after normalising (`NULL`/missing = the
column's schema default, numbers as floats with a float-column tolerance, strings exactly). Statements the replay
cannot apply are counted per table (`skipped`) since they are the usual cause of a difference.

**Allow list.** `ALLOWED_DIFFS` (in the frozen directory, a TSV of `table`, `key`, `column`, `reason`; key values
joined with `,`; column `*` for a whole-row presence difference) names the differences that are explained. Anything
else is reported as unexplained, and the CLI exits 1.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import frozen_replay, sql_dump, sqlcorpus, trainer_state

ALLOWED_DIFFS_NAME = "ALLOWED_DIFFS"

_PRIMARY_KEY_RE = re.compile(r"PRIMARY KEY\s*\((?P<cols>[^)]*)\)", re.IGNORECASE)
_UNIQUE_KEY_RE = re.compile(r"UNIQUE KEY\s*`?\w*`?\s*\((?P<cols>[^)]*)\)", re.IGNORECASE)
_TRUNCATE_RE_TEMPLATE = r"\bTRUNCATE\s+(?:TABLE\s+)?`?{table}`?\s*;"
# MySQL FLOAT is single precision and the client prints 6 significant digits (0.41142857 reads back as 0.411429).
_FLOAT_REL_TOL = 1e-5


@dataclass(frozen=True)
class Schema:
    columns: tuple[str, ...]
    key_columns: tuple[str, ...]
    defaults: dict
    string_columns: frozenset


@dataclass
class Difference:
    table: str
    key: tuple
    column: str  # "*" for a row present on one side only
    replayed: object
    live: object
    reason: str | None = None  # the allow-list reason, when explained


@dataclass
class TableResult:
    table: str
    footprint_rows: int = 0
    footprint_cells: int = 0
    skipped: list[str] = field(default_factory=list)
    differences: list[Difference] = field(default_factory=list)

    @property
    def unexplained(self) -> list[Difference]:
        return [d for d in self.differences if d.reason is None]


def frozen_tables(slot: frozen_replay.FrozenSlot) -> dict[str, list[Path]]:
    """Every table a frozen slot's files write (INSERT/REPLACE/DELETE/UPDATE/TRUNCATE), with the files that do."""
    tables: dict[str, list[Path]] = {}
    for path in slot.files:
        text = path.read_text(encoding="utf-8")
        names = set()
        for m in sqlcorpus.STATEMENT_HEAD_RE.finditer(text):
            name = m.group("ins_table") or m.group("del_table") or m.group("upd_table")
            if name and not sql_dump._in_line_comment(text, m.start()):
                names.add(name)
        for m in re.finditer(r"\bTRUNCATE\s+(?:TABLE\s+)?`(\w+)`", text, re.IGNORECASE):
            names.add(m.group(1))
        for name in names:
            tables.setdefault(name, []).append(path)
    return dict(sorted(tables.items()))


def table_schema(table: str) -> Schema:
    """Columns, key, defaults and string columns from the base dump's `CREATE TABLE`. The key is the primary key, else
    the first unique key, else every column."""
    path = trainer_state.BASE_SQL_DIR / f"{table}.sql"
    columns = sql_dump.parse_create_table_columns(path, table)
    body = sql_dump._create_table_body(path, table)
    m = _PRIMARY_KEY_RE.search(body) or _UNIQUE_KEY_RE.search(body)
    key = tuple(c.strip().strip("`") for c in m.group("cols").split(",")) if m else columns
    return Schema(
        columns, key, sql_dump.parse_create_table_defaults(path, table),
        sql_dump.parse_create_table_string_columns(path, table),
    )


def _apply(rows: dict, schema: Schema, table: str, text: str, on_skip: Callable[[str], None]) -> None:
    """`sql_dump.apply_composite_key_statements`, plus `TRUNCATE` (the replay reports it but does not model it; the
    frozen phase 0 truncates `mail_level_reward`)."""
    pattern = re.compile(_TRUNCATE_RE_TEMPLATE.format(table=re.escape(table)), re.IGNORECASE)
    pos = 0
    for m in pattern.finditer(text):
        if sql_dump._in_line_comment(text, m.start()):
            continue
        sql_dump.apply_composite_key_statements(rows, schema.columns, schema.key_columns, table, text[pos:m.start()],
                                                on_skip)
        rows.clear()
        pos = m.end()
    sql_dump.apply_composite_key_statements(rows, schema.columns, schema.key_columns, table, text[pos:], on_skip)
    if any(re.search(rf"\bSET\b[^;]*`{re.escape(c)}`\s*=", text, re.IGNORECASE) for c in schema.key_columns):
        rekey(rows, schema.key_columns)


def rekey(rows: dict, key_columns: tuple[str, ...]) -> None:
    """Files each row under the key its values now hold. The replay updates a key column in place (the frozen phase 0
    swaps loot items and quest ids that way: `UPDATE ... SET Item = 40752 WHERE Item = 47241`) but leaves the row
    under its old key; MySQL moves it."""
    moved = [(k, r) for k, r in rows.items() if all(c in r for c in key_columns)
             and k != tuple(r[c] for c in key_columns)]
    for old, _ in moved:
        del rows[old]
    for _, row in moved:
        rows[tuple(row[c] for c in key_columns)] = row


def replay_with_snapshots(
    table: str, schema: Schema, include_frozen: bool = True, applied: set[str] | None = None,
) -> tuple[dict, dict, dict, list, list]:
    """`(final, before, after, skipped, left_out)`: the replayed table at the end, right before the first frozen file
    and right after the last one (`before`/`after` are empty when no frozen file writes the table or `include_frozen`
    is off), the statements the replay could not apply (`file: statement start`), and the files left out because
    their name is not in `applied` (the live `updates` names; `None` keeps every file)."""
    base = trainer_state.BASE_SQL_DIR / f"{table}.sql"
    files = trainer_state._migration_files_mentioning(table)
    if not include_frozen:
        files = [p for p in files if not frozen_replay.is_frozen(p)]
    left_out = [p for p in files if applied is not None and p.name not in applied]
    files = ([base] if base.is_file() else []) + [p for p in files if p not in left_out]
    frozen_at = [i for i, p in enumerate(files) if frozen_replay.is_frozen(p)]
    rows: dict = {}
    before: dict = {}
    after: dict = {}
    skipped: list[str] = []
    for i, path in enumerate(files):
        if frozen_at and i == frozen_at[0]:
            before = {k: dict(v) for k, v in rows.items()}
        text = sqlcorpus.read_text(path)
        if path != base:
            # Frozen files already come back normalised from read_text; the other files get the same treatment here.
            text = frozen_replay.canonical_columns(
                frozen_replay.split_multi_set(frozen_replay.strip_line_comments(text)), schema.columns,
            )
        _apply(rows, schema, table, text, lambda s, name=path.name: skipped.append(f"{name}: {' '.join(s.split())}"))
        if frozen_at and i == frozen_at[-1]:
            after = {k: dict(v) for k, v in rows.items()}
    return rows, before, after, skipped, left_out


def _value(row: dict, column: str, schema: Schema) -> object:
    return row[column] if column in row else schema.defaults.get(column)


def footprint(before: dict, after: dict, schema: Schema) -> dict[tuple, tuple[str, ...]]:
    """`{key: columns}` the frozen SQL wrote: every column of a row it inserted or deleted, the changed columns of a
    row it updated."""
    result: dict[tuple, tuple[str, ...]] = {}
    for key in before.keys() | after.keys():
        if key not in before or key not in after:
            result[key] = schema.columns
            continue
        old, new = before[key], after[key]
        changed = tuple(
            c for c in schema.columns
            if not values_equal(_value(old, c, schema), _value(new, c, schema), c in schema.string_columns)
        )
        if changed:
            result[key] = changed
    return result


def _normalise(value: object, is_string: bool) -> object:
    if value is None:
        return "" if is_string else 0.0
    if is_string:
        return str(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def values_equal(a: object, b: object, is_string: bool = False) -> bool:
    """`NULL`/missing equal the column's empty value; numbers compare as floats with a FLOAT-column tolerance."""
    a, b = _normalise(a, is_string), _normalise(b, is_string)
    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, rel_tol=_FLOAT_REL_TOL, abs_tol=1e-9)
    return a == b


def key_text(key: tuple) -> str:
    return ",".join(_key_part(v) for v in key)


def _key_part(value: object) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def compare(
    table: str, schema: Schema, cells: dict[tuple, tuple[str, ...]], final: dict, live: dict[str, dict],
) -> list[Difference]:
    """The footprint `cells` of the replayed `final` rows against `live` (`{key_text: row}`, as read from the DB)."""
    differences: list[Difference] = []
    final_by_text = {key_text(k): v for k, v in final.items()}
    for key in sorted(cells, key=key_text):
        text = key_text(key)
        replayed, actual = final_by_text.get(text), live.get(text)
        if replayed is None and actual is None:
            continue
        if replayed is None or actual is None:
            differences.append(Difference(table, key, "*", replayed is not None, actual is not None))
            continue
        for column in cells[key]:
            if column not in actual:
                continue  # not a live column (schema drift); reported by the CLI
            r, a = _value(replayed, column, schema), actual[column]
            if not values_equal(r, a, column in schema.string_columns):
                differences.append(Difference(table, key, column, r, a))
    return differences


def load_allowed(path: Path) -> dict[tuple[str, str, str], str]:
    """`{(table, key text, column): reason}` from an `ALLOWED_DIFFS` TSV (`#` comments and blank lines skipped)."""
    allowed: dict[tuple[str, str, str], str] = {}
    if not path.is_file():
        return allowed
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 4 or not parts[3].strip():
            raise ValueError(f"{path}:{number}: want 4 tab-separated fields (table, key, column, reason)")
        table, key, column, reason = (p.strip() for p in parts)
        allowed[(table, key, column)] = reason
    return allowed


def explain(differences: list[Difference], allowed: dict[tuple[str, str, str], str]) -> set[tuple[str, str, str]]:
    """Sets each difference's `reason` from `allowed`; returns the allow-list entries that matched nothing (stale)."""
    used = set()
    for d in differences:
        entry = (d.table, key_text(d.key), d.column)
        if entry in allowed:
            d.reason = allowed[entry]
            used.add(entry)
    return set(allowed) - used


def parse_mysql_batch(output: str) -> list[dict]:
    """`mysql -B` output (header line, tab-separated, `\\t`/`\\n`/`\\\\`/`\\0` escaped, `NULL` for NULL) as dicts."""
    lines = output.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if not lines:
        return []
    header = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        fields = line.split("\t")
        rows.append({c: _unescape_mysql(v) for c, v in zip(header, fields)})
    return rows


_MYSQL_ESCAPES = {"n": "\n", "t": "\t", "\\": "\\", "0": "\0", "r": "\r"}


def _unescape_mysql(value: str) -> object:
    if value == "NULL":
        return None
    if "\\" not in value:
        return value
    return re.sub(r"\\(.)", lambda m: _MYSQL_ESCAPES.get(m.group(1), m.group(1)), value)
