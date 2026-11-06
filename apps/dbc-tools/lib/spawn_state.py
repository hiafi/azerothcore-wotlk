"""
Live spawn state for the dungeon difficulties spawnMask emitter (E2, WP-T2): which `creature` / `gameobject` spawn
(guid) holds which entry on which map with which `spawnMask`, replayed from the base dump and every migration the way
the server's database ends up (base dump, promoted with the frozen phase 0 spliced in, pending, module SQL).

Built on `sql_dump.apply_composite_key_statements` keyed on `guid`, with three fixes this table's history needs
(each checked against the live DB on 2026-11-05: after them the 19 vanilla dungeon maps replay with no spawn, entry,
map or spawnMask difference; see the E2-T2 report):

- **`id1` is `id`.** `2026_06_16_00.sql` renamed `creature.id1` to `id` and dropped `id2`/`id3`. Every migration's text
  is read with `` `id1` `` written `` `id` `` (the base dump's positional rows get the renamed column list), so a row
  and the WHERE that names it agree on one column name either side of the rename.
- **Double-quoted strings.** Upstream's sniffed spawn files write `""` and `"text"` (`2026_03_10_00.sql`, the
  Deadmines doors and levers); `sql_dump` reads only single-quoted literals and skipped those INSERTs whole. A file
  holding one is read with each double-quoted literal rewritten single-quoted (comments and single-quoted strings are
  left alone).
- **DELETE / UPDATE with no `guid` in the WHERE** (`DELETE FROM creature WHERE id = 33838 AND map = 603`): the
  guid-keyed replay skips those, so they are applied here in file order with `sql_dump.parse_where_predicate`
  (strict: a condition on a column the row does not hold does not match). An UPDATE that writes none of the kept
  columns is a no-op for this view and is ignored.

Rows keep only `KEPT_COLUMNS`. Statements the replay still cannot apply (a positional INSERT written after the
rename, a WHERE outside the predicate grammar) are counted in `SpawnState.skipped` and never guessed at.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import sql_dump, sqlcorpus, trainer_state

SPAWN_TABLES = ("creature", "gameobject")
KEPT_COLUMNS = ("guid", "id", "map", "zoneId", "areaId", "spawnMask", "phaseMask")


@dataclass
class SpawnState:
    """`rows`: the replay's own dict, keyed `(guid,)`, each row {KEPT_COLUMNS} (`by_guid()` re-keys it by the guid the
    row holds). `skipped`: (file name, statement start) the replay could not apply."""

    rows: dict[tuple, dict] = field(default_factory=dict)
    skipped: list[tuple[str, str]] = field(default_factory=list)

    def by_guid(self) -> dict[int, dict]:
        return {_int(row.get("guid")): row for row in self.rows.values()}

    def on_map(self, map_id: int) -> list[dict]:
        return [row for row in self.rows.values() if _int(row.get("map")) == map_id]


def _int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def spawn_entry(row: dict) -> int:
    return _int(row.get("id"))


def spawn_mask(row: dict) -> int:
    """A spawn's mask; a row an INSERT left the column out of has the schema DEFAULT 1."""
    value = row.get("spawnMask")
    return 1 if value is None else _int(value)


# ---------------------------------------------------------------------------------------------------------------------
# Text normalisation


def _rewrite_double_quoted(text: str) -> str:
    """Every double-quoted string literal outside comments and single-quoted strings, written single-quoted (with
    `'` doubled and `""` undoubled). Returns `text` itself when it holds no double quote."""
    if '"' not in text:
        return text
    out: list[str] = []
    i, n, start = 0, len(text), 0
    while i < n:
        ch = text[i]
        if ch == "-" and text.startswith("--", i) or ch == "#":
            j = text.find("\n", i)
            i = n if j == -1 else j + 1
            continue
        if ch == "/" and text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        if ch == "'":
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == "'":
                    if i + 1 < n and text[i + 1] == "'":
                        i += 2
                        continue
                    break
                i += 1
            i += 1
            continue
        if ch == '"':
            j = i + 1
            buf: list[str] = []
            while j < n:
                if text[j] == "\\" and j + 1 < n:
                    buf.append(text[j:j + 2])
                    j += 2
                    continue
                if text[j] == '"':
                    if j + 1 < n and text[j + 1] == '"':
                        buf.append('"')
                        j += 2
                        continue
                    break
                buf.append("''" if text[j] == "'" else text[j])
                j += 1
            out.append(text[start:i])
            out.append("'" + "".join(buf) + "'")
            i = start = j + 1
            continue
        i += 1
    out.append(text[start:])
    return "".join(out)


def normalise_text(text: str, table: str) -> str:
    """A migration's text as this replay reads it (see the module docstring). Returns `text` itself when nothing
    changes, so a corpus text keeps its precomputed statement-head index."""
    out = text
    if table == "creature" and "`id1`" in out:
        out = out.replace("`id1`", "`id`")
    return _rewrite_double_quoted(out)


# ---------------------------------------------------------------------------------------------------------------------
# guid-less DELETE / UPDATE

def _head_re(table: str) -> re.Pattern:
    return re.compile(rf"\b(?P<kind>DELETE\s+FROM|UPDATE)\s+`{re.escape(table)}`\s+", re.IGNORECASE)


_WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def _guidless_spans(text: str, table: str) -> list[tuple[int, int, str]]:
    """(start, end, kind) of each DELETE / UPDATE on `table` whose WHERE does not name `guid`."""
    spans = []
    for m in _head_re(table).finditer(text):
        if sql_dump._in_line_comment(text, m.start()):
            continue
        end = text.find(";", m.end())
        end = len(text) if end == -1 else end + 1
        where = _WHERE_RE.search(text, m.end(), end)
        if where is None or "`guid`" in text[where.end():end]:
            continue
        spans.append((m.start(), end, "delete" if m.group("kind").upper().startswith("DELETE") else "update"))
    return spans


def _apply_guidless(
    state: SpawnState, table: str, path: Path, text: str, span: tuple[int, int, str], variables: dict,
) -> None:
    start, end, kind = span
    statement = text[start:end]
    where = _WHERE_RE.search(statement)
    where_text = statement[where.end():].rstrip().rstrip(";")
    if kind == "delete":
        predicate = sql_dump.parse_where_predicate(where_text, lenient=False)
        if predicate is None:
            state.skipped.append((path.name, " ".join(statement.split())[:100]))
            return
        for key in [k for k, row in state.rows.items() if predicate(row)]:
            del state.rows[key]
        return
    set_at = re.match(rf"UPDATE\s+`{re.escape(table)}`\s+SET\s+", statement, re.IGNORECASE)
    if set_at is None:
        state.skipped.append((path.name, " ".join(statement.split())[:100]))
        return
    try:
        assignments, _ = sql_dump._read_set_assignments(statement, set_at.end(), variables, allow_expr=True)
    except (ValueError, IndexError):
        state.skipped.append((path.name, " ".join(statement.split())[:100]))
        return
    if not any(column in KEPT_COLUMNS for column in assignments):
        return  # writes nothing this view keeps
    predicate = sql_dump.parse_where_predicate(where_text, lenient=False)
    if predicate is None:
        state.skipped.append((path.name, " ".join(statement.split())[:100]))
        return
    for row in state.rows.values():
        if predicate(row):
            sql_dump._assign(row, {c: v for c, v in assignments.items() if c in KEPT_COLUMNS})


_SET_VAR_RE = re.compile(r"SET\s+(?P<name>@\w+)\s*:?=\s*(?P<value>-?\d+)\s*;", re.IGNORECASE)


def _variables_before(text: str, pos: int) -> dict[str, int]:
    return {m.group("name"): int(m.group("value")) for m in _SET_VAR_RE.finditer(text, 0, pos)}


def _prefix(variables: dict[str, int]) -> str:
    return "".join(f"SET {name} := {value};\n" for name, value in variables.items())


# ---------------------------------------------------------------------------------------------------------------------
# The replay

def _columns(table: str) -> list[str]:
    base = trainer_state.BASE_SQL_DIR / f"{table}.sql"
    columns = list(sql_dump.parse_create_table_columns(base, table))
    return ["id" if c == "id1" else c for c in columns]


def _project(state: SpawnState) -> None:
    for key, row in list(state.rows.items()):
        if len(row) > len(KEPT_COLUMNS) or any(c not in KEPT_COLUMNS for c in row):
            state.rows[key] = {c: row[c] for c in KEPT_COLUMNS if c in row}


def make_step(table: str, base_path: Path):
    columns = tuple(_columns(table))
    key = ("guid",)

    def step(state: SpawnState, path: Path) -> SpawnState:
        raw = sqlcorpus.read_text(path)
        text = raw if path == base_path else normalise_text(raw, table)

        def report(snippet: str) -> None:
            state.skipped.append((path.name, " ".join(snippet.split())[:100]))

        spans = _guidless_spans(text, table) if path != base_path else []
        if not spans:
            sql_dump.apply_composite_key_statements(state.rows, columns, key, table, text, report)
        else:
            last = 0
            for span in spans:
                variables = _variables_before(text, span[0])
                chunk = _prefix(_variables_before(text, last)) + text[last:span[0]]
                sql_dump.apply_composite_key_statements(state.rows, columns, key, table, chunk, report)
                _apply_guidless(state, table, path, text, span, variables)
                last = span[1]
            chunk = _prefix(_variables_before(text, last)) + text[last:]
            sql_dump.apply_composite_key_statements(state.rows, columns, key, table, chunk, report)
        _project(state)
        return state

    return step


def load_spawn_state(table: str) -> SpawnState:
    """The replayed spawns of `table` ("creature" or "gameobject"); the promoted prefix is cached on disk like every
    other loader (`sqlcorpus.checkpointed`), pending and module files are replayed on top each run."""
    if table not in SPAWN_TABLES:
        raise ValueError(f"load_spawn_state: {table!r} is not one of {SPAWN_TABLES}")
    base_path = trainer_state.BASE_SQL_DIR / f"{table}.sql"
    step = make_step(table, base_path)
    stable, volatile = trainer_state._split_stable(trainer_state._migration_files_mentioning(table))
    state = sqlcorpus.checkpointed(
        "spawn_state", (table, KEPT_COLUMNS), [base_path, *stable], SpawnState, step,
    )
    for path in volatile:
        step(state, path)
    return state
