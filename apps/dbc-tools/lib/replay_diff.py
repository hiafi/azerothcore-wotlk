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

import inspect
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


# ---------------------------------------------------------------------------------------------------------------------
# Whole-table check (`replay_diff.py --tables-check`): every row of every table dbc-tools replays, replay vs live.
#
# The footprint check above only looks at the cells the frozen phase 0 wrote. This one asks the wider question: does
# the replay the loaders use (`sql_dump.apply_composite_key_statements` over the base dump and every applied file, in
# apply order; and `sql_dump.apply_statements` for the DBC-backed tables `state.load_existing_rows` reads) give the
# live table, row for row and cell for cell? Rows are matched on the table's primary key (else its first unique key),
# read from the row's own values, the way every loader's caller reads them.

# Every table a dbc-tools loader replays (`trainer_state.load_replayed_table_rows` / `load_keyed_table_rows`,
# `state.load_existing_rows`, `spell_tables`' declared and removal tables), plus the tables later stages replay with
# the same parser (`smart_scripts`, the `creature` / `gameobject` spawns).
DBC_REPLAYED_TABLES = (
    "spell_dbc", "talent_dbc", "talenttab_dbc", "skilllineability_dbc", "item_dbc", "spellcasttimes_dbc",
    "spellduration_dbc", "spellrange_dbc", "spellradius_dbc", "creaturespelldata_dbc",
)
REPLAYED_TABLES = (
    *DBC_REPLAYED_TABLES,
    "creature_template", "creature_template_model", "creature_default_trainer", "trainer_spell",
    "spell_script_names", "spell_bonus_data", "spell_proc", "spell_linked_spell", "spell_group",
    "spell_group_stack_rules", "spell_custom_attr", "spellshapeshiftform_dbc", "spellcategory_dbc",
    "spell_potency_correction", "disables", "creature_template_spell", "spellrunecost_dbc", "chrclasses_dbc",
    "spell_threat", "playercreateinfo_action", "playercreateinfo_cast_spell", "playercreateinfo_skills",
    "mapdifficulty_dbc", "dungeon_access_template", "spell_required", "spell_ranks",
    "smart_scripts", "creature", "gameobject",
)
ALLOWED_TABLE_DIFFS = Path(__file__).resolve().parents[1] / "replay" / "ALLOWED_TABLE_DIFFS"


@dataclass
class WholeTableResult:
    table: str
    loader: str  # "composite" (apply_composite_key_statements) or "keyed" (apply_statements, DBC tables)
    key_columns: tuple[str, ...]
    live_rows: int = 0
    replay_rows: int = 0
    duplicate_keys: int = 0  # replayed rows that hold the same key as another replayed row
    skipped: list[str] = field(default_factory=list)
    left_out: list[str] = field(default_factory=list)
    differences: list[Difference] = field(default_factory=list)
    seconds: float = 0.0

    def count(self, kind: str, explained: bool | None = None) -> int:
        """`kind`: "missing" (live only), "extra" (replay only) or "cells"; `explained` None counts both."""
        def matches(d: Difference) -> bool:
            if kind == "missing":
                ok = d.column == "*" and d.live and not d.replayed
            elif kind == "extra":
                ok = d.column == "*" and d.replayed and not d.live
            else:
                ok = d.column != "*"
            return ok and (explained is None or (d.reason is not None) == explained)
        return sum(1 for d in self.differences if matches(d))


def whole_table_files(table: str, applied: set[str] | None) -> tuple[list[Path], list[Path]]:
    """`(files, left_out)`: the base dump and every file that mentions `table`, in apply order, minus the files whose
    name the live `updates` table does not list (`applied`; None keeps them all; the base dump is always kept)."""
    base = trainer_state.BASE_SQL_DIR / f"{table}.sql"
    files = _call(trainer_state._migration_files_mentioning, table, loose=True)
    left_out = [p for p in files if applied is not None and p.name not in applied]
    return ([base] if base.is_file() else []) + [p for p in files if p not in left_out], left_out


def replay_whole_table(
    table: str, schema: Schema, applied: set[str] | None = None, loader: str = "composite",
) -> tuple[list[dict], list[str], list[Path]]:
    """`(rows, skipped, left_out)`: the table as the loaders replay it. `loader` "composite" is
    `sql_dump.apply_composite_key_statements` on the schema's own columns and key (what `load_replayed_table_rows`
    does); "keyed" is `sql_dump.apply_statements` on a synthetic one-key `DbcTable` (what `state.load_existing_rows`
    does for a DBC-backed table, minus the client DBC seed: the live table holds only what the SQL wrote)."""
    files, left_out = whole_table_files(table, applied)
    skipped: list[str] = []

    def on_skip(name: str):
        return lambda s: skipped.append(f"{name}: {' '.join(s.split())}")

    if loader == "keyed":
        from .dbcfmt import DbcTable  # noqa: PLC0415 - only this mode needs it

        fmt = "n" + "".join("s" if c in schema.string_columns else "i" for c in schema.columns[1:])
        dbc_table = DbcTable(name=table, dbc_filename="", sql_table=table, fmt=fmt, columns=schema.columns)
        keyed: dict = {}
        for path in files:
            if path.name == f"{table}.sql" and path.parent == trainer_state.BASE_SQL_DIR:
                keyed.update(sql_dump.read_table_dump(path, dbc_table))
            else:
                text = sqlcorpus.read_text(path)
                _call(sql_dump.apply_statements, keyed, dbc_table, text, on_skip=on_skip(path.name), source=path.name)
                if hasattr(trainer_state, "_record_invisible"):
                    trainer_state._record_invisible(table, path, text, on_skip(path.name))
        _seed_live_secondary_rows(keyed, table, lambda rows, text: sql_dump.apply_statements(rows, dbc_table, text))
        _apply_live_orphan_rows(table, lambda text: _call(
            sql_dump.apply_statements, keyed, dbc_table, text, on_skip=on_skip(LIVE_ORPHAN_ROWS_SQL.name),
            source=LIVE_ORPHAN_ROWS_SQL.name,
        ))
        return list(keyed.values()), skipped, left_out
    rows: dict = {}
    for path in files:
        text = sqlcorpus.read_text(path)
        _call(
            sql_dump.apply_composite_key_statements, rows, schema.columns, schema.key_columns, table,
            text, on_skip=on_skip(path.name), defaults=schema.defaults, source=path.name,
        )
        if hasattr(trainer_state, "_record_invisible") and path.parent != trainer_state.BASE_SQL_DIR:
            trainer_state._record_invisible(table, path, text, on_skip(path.name))
    if table in DBC_REPLAYED_TABLES:
        _seed_live_secondary_rows(rows, table, lambda target, text: sql_dump.apply_composite_key_statements(
            target, schema.columns, schema.key_columns, table, text))
        _apply_live_orphan_rows(table, lambda text: _call(
            sql_dump.apply_composite_key_statements, rows, schema.columns, schema.key_columns, table, text,
            on_skip=on_skip(LIVE_ORPHAN_ROWS_SQL.name), defaults=schema.defaults, source=LIVE_ORPHAN_ROWS_SQL.name,
        ))
    return list(rows.values()), skipped, left_out


def _seed_live_secondary_rows(rows: dict, table: str, apply) -> None:
    """`state.load_existing_rows`' last step for a DBC-backed table: the live-only reserved-block rows of
    `source/live_secondary_rows.sql` fill the ids no migration wrote (they never override a replayed row)."""
    from .state import LIVE_SECONDARY_ROWS_SQL  # noqa: PLC0415 - state imports the DBC reader

    text = LIVE_SECONDARY_ROWS_SQL.read_text(encoding="utf-8") if LIVE_SECONDARY_ROWS_SQL.is_file() else ""
    if f"`{table}`" not in text:
        return
    seeded: dict = {}
    apply(seeded, text)
    for key, row in seeded.items():
        rows.setdefault(key, row)


# Live-only spell_dbc / talent_dbc / talenttab_dbc rows and index remaps from deleted pending migrations (see the
# file's header). Applied as written, after everything else: its `INSERT IGNORE`s and guarded UPDATEs never override
# what a file wrote. Only this check reads it; `state.load_existing_rows` keeps the client DBC's stock rows.
LIVE_ORPHAN_ROWS_SQL = Path(__file__).resolve().parents[1] / "source" / "live_orphan_rows.sql"


def _apply_live_orphan_rows(table: str, apply: Callable[[str], None]) -> None:
    """`apply(text)` with `LIVE_ORPHAN_ROWS_SQL`'s text when it writes `table` (the replay's last step)."""
    text = LIVE_ORPHAN_ROWS_SQL.read_text(encoding="utf-8") if LIVE_ORPHAN_ROWS_SQL.is_file() else ""
    if f"`{table}`" in text:
        apply(text)


def _call(function, *args, **kwargs):
    """`function(*args, **kwargs)` without the keyword arguments it does not take: the check also runs against the
    replay code from before `on_skip`/`defaults`/`source` existed, to measure what a change fixed."""
    accepted = inspect.signature(function).parameters
    return function(*args, **{k: v for k, v in kwargs.items() if k in accepted})


def whole_table_compare(
    table: str, schema: Schema, rows: list[dict], live_rows: list[dict], columns: tuple[str, ...] | None = None,
) -> tuple[list[Difference], int]:
    """`(differences, duplicate keys)`: every key present on one side only (column `*`), and every cell of a row both
    sides hold that differs, over the live columns (`columns` narrows them: the DBC loader's curated subset). A
    replayed row's key is read from its values; two replayed rows on one key count as a duplicate and the later one
    is compared."""
    replayed: dict[str, dict] = {}
    duplicates = 0
    for row in rows:
        text = key_text(tuple(row.get(c) for c in schema.key_columns))
        duplicates += text in replayed
        replayed[text] = row
    live = {key_text(tuple(_live_key_part(r[c]) for c in schema.key_columns)): r for r in live_rows}
    differences: list[Difference] = []
    for text in sorted(replayed.keys() | live.keys()):
        r, a = replayed.get(text), live.get(text)
        key = tuple(text.split(","))
        if r is None or a is None:
            differences.append(Difference(table, key, "*", r is not None, a is not None))
            continue
        for column in a:
            if columns is not None and column not in columns:
                continue
            value = r[column] if column in r else schema.defaults.get(column)
            if not values_equal(value, a[column], column in schema.string_columns):
                differences.append(Difference(table, key, column, value, a[column]))
    return differences, duplicates


def _live_key_part(value: object) -> object:
    """A live key cell as the replay would hold it: `mysql -B` prints `1.0` floats as `1`, ints as digits."""
    if isinstance(value, str):
        try:
            number = float(value)
        except ValueError:
            return value
        return int(number) if number.is_integer() and "." not in value and "e" not in value.lower() else number
    return value


def explain_whole(
    differences: list[Difference], allowed: dict[tuple[str, str, str], str],
) -> set[tuple[str, str, str]]:
    """`explain`, plus `*` in the key field of an allow-list entry: every key of that table and column. The column
    `*` is a row present on one side only; `*missing` only a row live has and the replay lacks, `*extra` the other
    way round. Returns the entries that matched nothing."""
    used = set()
    for d in differences:
        kinds = [d.column]
        if d.column == "*":
            kinds.append("*missing" if d.live else "*extra")
        entries = [(d.table, k, c) for c in kinds for k in (key_text(d.key), "*")]
        for entry in entries:
            if entry in allowed:
                d.reason = allowed[entry]
                used.add(entry)
                break
    return set(allowed) - used
