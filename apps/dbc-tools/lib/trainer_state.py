"""
Read-only reconstruction of just enough world-DB state to validate that a
`TrainerId` a spell declaration wants to grant from actually resolves to a
real, placed, correctly-flagged NPC - Phase 3 of `.agents/plans/
spell-source-dsl/spell-source-dsl.PLAN.md`. This is the direct fix for the
bug that's shipped twice: a fully-authored `trainer_spell` curve pointing at
a `TrainerId` no live NPC ever serves (`docs/bugs-and-fixes.md:482`), and a
bugfix pass editing the wrong of several plausible-looking `TrainerId`s
because nothing checked which one a real NPC actually resolves to
(`docs/bugs-and-fixes.md:925`).

Pure static-file scan (`data/sql/base/db_world` + `updates/db_world` +
`updates/pending_db_world`), no live MySQL connection - consistent with the
rest of this pipeline (see `lib/state.py`'s own docstring for why). Includes
`updates/pending_db_world` (unlike `lib/state.py`'s DBC-table reconstruction,
which deliberately excludes it for a different, DBC-table-specific reason -
see that module's docstring): a trainer wiring fix might already exist in a
not-yet-promoted migration, and treating it as "still missing" here would be
a false failure for exactly the case this is meant to help with.

**Module SQL and the frozen phase 0 count too.** `DBUpdater` applies every
module's own `data/sql/db-world/*.sql` at worldserver start (`module_sql_files`).
mod-progression's phase 0, applied once on 2026-09-02, is where this server's
class trainers got rewired (`UPDATE creature_default_trainer SET TrainerId =
@TrainerId+N WHERE CreatureId IN (...)`: every mage trainer moves from the
stock 16 to 212). Scanning only `data/sql/` made `trained_by()` reject the
one TrainerId that actually works here (first hit: Meteor, Fire Mage
rework, 2026-09-15). The module is retired; the files that ran are kept as a
frozen replay input at the position they ran (`lib/frozen_replay.py`).

**Replay vs union.** `creature_default_trainer` (single-int PK, and the one
table the rewiring above rewrites in place) is reconstructed by *replaying*
INSERT/UPDATE/DELETE in order via `sql_dump.apply_statements`, the same as
`lib/state.py` does for DBC tables. The other three (`trainer_spell`,
`creature`, `creature_template` - composite keys, or far too big to care)
stay a plain union of every `INSERT` ever seen, so a row inserted once and
later deleted still reads as "exists" there. Acceptable for a build-time
"is this TrainerId obviously dead" check, not a source of truth for trainer
content itself.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import re

from . import frozen_replay, sql_dump, sqlcorpus
from .dbcfmt import DbcTable

REPO_ROOT = Path(__file__).resolve().parents[3]
BASE_SQL_DIR = REPO_ROOT / "data" / "sql" / "base" / "db_world"
PROMOTED_SQL_DIR = REPO_ROOT / "data" / "sql" / "updates" / "db_world"
PENDING_SQL_DIR = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world"
MODULES_DIR = REPO_ROOT / "modules"


CUSTOM_SQL_DIR = REPO_ROOT / "data" / "sql" / "custom" / "db_world"


def _sql_tree(directory: Path) -> list[Path]:
    """Every `*.sql` under `directory`, subdirectories included (DBUpdater's `FillFileListRecursively`)."""
    return list(directory.rglob("*.sql")) if directory.is_dir() else []


def module_sql_files() -> list[Path]:
    """Every module SQL file `DBUpdater` would apply to the world DB: each module's `data/sql/<dir>/` whose name
    contains `db-world` (`UpdateFetcher::ReceiveIncludedDirectories`), recursively, by bare file name."""
    if not MODULES_DIR.is_dir():
        return []
    files: list[Path] = []
    for module_dir in sorted(MODULES_DIR.iterdir()):
        sql_dir = module_dir / "data" / "sql"
        if not sql_dir.is_dir():
            continue
        for world in sorted(d for d in sql_dir.iterdir() if d.is_dir() and "db-world" in d.name):
            files.extend(_sql_tree(world))
    return sorted(files, key=lambda p: p.name)


class DuplicateUpdateName(ValueError):
    """Two update files with one bare name: DBUpdater refuses to start ("Duplicate filename"), since it orders and
    tracks updates by file name alone."""


def update_files(promoted_dir: Path | None = None, pending_dir: Path | None = None) -> list[Path]:
    """Every world-DB update file, in the order DBUpdater applies them to a fresh database
    (`src/server/database/Updater/UpdateFetcher.cpp`, `UpdateFetcher::Update`). All include directories go into one
    `std::set` ordered by bare file name (`PathCompare`), subdirectories included, and the set is applied in two
    passes:

    1. the RELEASED (and ARCHIVED) files: `data/sql/updates/db_world/**`, with the frozen replay inputs
       (`frozen_replay.splice`, mod-progression's phase 0, which the module itself applied outside DBUpdater) at
       their slot;
    2. the PENDING, CUSTOM and MODULE files together, by bare name: `data/sql/updates/pending_db_world/**`,
       `data/sql/custom/db_world/**` and every module's `data/sql/db-world/**`. A module file named `2016_...` runs
       before a pending `rev_...`, one named `zz_...` after it.

    `data/sql/archive/db_world` is not read: its files are older than the base dumps, which already hold them (the
    base dump's `updates` rows mark them applied). Raises `DuplicateUpdateName` where DBUpdater would.
    `promoted_dir` / `pending_dir` replace the two update directories (`state.py` keeps its own, which tests point
    elsewhere)."""
    released = sorted(_sql_tree(promoted_dir or PROMOTED_SQL_DIR), key=lambda p: p.name)
    second = sorted(
        [*_sql_tree(pending_dir or PENDING_SQL_DIR), *_sql_tree(CUSTOM_SQL_DIR), *module_sql_files()],
        key=lambda p: p.name,
    )
    seen: dict[str, Path] = {}
    for path in (*released, *second):
        if path.name in seen:
            raise DuplicateUpdateName(f"update file name {path.name} is used twice ({seen[path.name]}, {path})")
        seen[path.name] = path
    return [*frozen_replay.splice(released), *second]


def is_promoted(path: Path) -> bool:
    """Whether `path` is a promoted `db_world` file (or under one of its subdirectories)."""
    return PROMOTED_SQL_DIR in Path(path).parents


def second_pass_files(pending_dir: Path | None = None) -> list[Path]:
    """`update_files()`' second pass: pending, custom and module SQL, by bare name (what db-import applies on top of
    the promoted state)."""
    return [
        p for p in update_files(pending_dir=pending_dir)
        if not is_promoted(p) and not frozen_replay.is_frozen(p)
    ]


# src/server/game/Entities/Unit/UnitDefines.h
UNIT_NPC_FLAG_TRAINER = 0x00000010

_TRAINER_TABLES = ("creature_default_trainer", "trainer_spell", "creature_template", "creature")


def load_table_rows(table_name: str, project: tuple[str, ...] | None = None) -> list[dict]:
    """Every INSERT `table_name` has ever appeared in, across the base dump
    and every db_world/pending_db_world migration that mentions it (a cheap
    substring check before bothering to parse each file). Public because
    `lib/spell_tables.py` reuses it for `spell_script_names`/
    `spell_bonus_data`/`spell_proc` - same union-of-INSERTs semantics and
    the same "no DELETE replay" limitation from the module docstring.

    The base dump is expected to always parse cleanly (confirmed for all
    four tables this module uses - creature/creature_template's base files
    alone are 149879/29947 rows) and is *not* wrapped in the same
    try/except as the migrations loop below - a failure there is loud on
    purpose, since silently returning near-nothing for the bulk of real
    creature data would make every trainer_problems() check meaninglessly
    "clean". Individual migration files, by contrast, are hand-written and
    varied enough (mysqldump-style `INSERT` is only the majority shape) that
    one being unparseable (`ON DUPLICATE KEY UPDATE`, a `@GUID`-variable
    expression instead of a literal, ...) shouldn't take the whole check
    down - skip it with a warning, same defensive posture as
    `state.load_existing_rows`'s own `apply_statements` loop, and for the
    same reason: an imperfect read degrading safely beats a hard crash on
    a run trying to do something unrelated to whichever migration choked.

    `project` keeps only those columns of each row (a caller that reads two columns of the 150k-row `creature` dump
    need not hold, or cache, the other thirty)."""
    base_path = BASE_SQL_DIR / f"{table_name}.sql"
    fallback_columns: tuple[str, ...] = ()
    if base_path.is_file():
        fallback_columns = sql_dump.parse_create_table_columns(base_path, table_name)

    def step(rows: list[dict], path: Path) -> list[dict]:
        if path == base_path:
            more = sql_dump.read_table_rows(base_path, table_name, fallback_columns)
        else:
            # A statement it cannot read is recorded in the skip log (sqlcorpus.SKIPS) and the rest of the file is
            # still read; anything else going wrong skips the file, loudly.
            try:
                more = sql_dump.read_table_rows(path, table_name, fallback_columns, tolerant=True)
            except Exception as exc:  # pragma: no cover - defensive, see docstring above
                print(f"warning: trainer_state.py: skipping {path} for {table_name}: {exc}")
                sqlcorpus.SKIPS.record(table_name, path.name, 0, f"whole file skipped: {exc}", "")
                return rows
        if project is not None:
            more = [{c: row[c] for c in project if c in row} for row in more]
        rows.extend(more)
        return rows

    stable, volatile = _split_stable(_migration_files_mentioning(table_name))
    rows = sqlcorpus.checkpointed(
        "table_rows", (table_name, project), ([base_path] if base_path.is_file() else []) + stable, list, step,
    )
    for path in volatile:
        step(rows, path)
    return rows


# The statement words that can stand right before a table name, when the name is written without backticks.
_BARE_HEAD_BEFORE_RE = re.compile(
    r"(?:\bINSERT\s+(?:IGNORE\s+)?INTO|\bREPLACE\s+INTO|\bDELETE\s+FROM|\bUPDATE|\bTRUNCATE(?:\s+TABLE)?)\s+$",
    re.IGNORECASE,
)
_ALIAS_AFTER_RE = re.compile(r"`\s+(?:AS\s+)?(?!SET\b)\w+", re.IGNORECASE)
_UPDATE_BEFORE_RE = re.compile(r"\bUPDATE\s+$", re.IGNORECASE)


def invisible_statements(table_name: str, text: str) -> list[tuple[int, str]]:
    """`(offset, statement start)` of every statement on `table_name` the head scanner (`sql_dump._STATEMENT_HEAD_RE`)
    cannot match: the table name written without backticks, or an `UPDATE` with a table alias. Statements in a
    `--` / `#` line comment are left out. Found from the occurrences of the name (a plain search, case as written:
    this repo's SQL spells table names in lower case), so a file pays for its mentions of the table, not for a scan
    per kind."""
    found = []
    n = len(table_name)
    pos = text.find(table_name)
    while pos != -1:
        before = text[pos - 1] if pos else " "
        after = text[pos + n] if pos + n < len(text) else " "
        if not (after.isalnum() or after == "_") and not (before.isalnum() or before == "_"):
            offset = max(0, pos - 40)
            if before == "`":
                m = _UPDATE_BEFORE_RE.search(text, offset, pos - 1)
                if m and _ALIAS_AFTER_RE.match(text, pos + n):
                    found.append((m.start(), text[m.start():pos + n + 20]))
            else:
                m = _BARE_HEAD_BEFORE_RE.search(text, offset, pos)
                if m:
                    found.append((m.start(), text[m.start():pos + n]))
        pos = text.find(table_name, pos + n)
    return [(start, statement) for start, statement in found if not sql_dump._in_line_comment(text, start)]


def _record_invisible(table_name: str, path: Path, text: str, warn: Callable[[str], None] | None) -> None:
    """Records (and passes to `warn`) every statement on `table_name` in `text` the replay's head scanner cannot see
    (`invisible_statements`): those are skipped too, and no skip is silent."""
    for start, statement in invisible_statements(table_name, text):
        sqlcorpus.SKIPS.record(
            table_name, path.name, start, "statement the replay cannot see (unquoted table name or an alias)",
            text[start:start + 160],
        )
        if warn:
            warn(statement)


def _migration_files_mentioning(table_name: str, loose: bool = False) -> list[Path]:
    """Every non-base SQL file that mentions `table_name`, in DBUpdater's apply order (`update_files`: promoted core
    updates with the frozen inputs spliced in at their slot, then pending, custom and module SQL by bare file name;
    subdirectories included). A cheap substring check before bothering to parse each file; `loose` also opens a file
    that only names the table unquoted, so its statements can be warned about."""
    return [p for p in update_files() if sqlcorpus.mentions(p, table_name, loose)]


def _split_stable(files: list[Path]) -> tuple[list[Path], list[Path]]:
    """`files` (from `_migration_files_mentioning`) as `(promoted prefix, the rest)`. The promoted `db_world` files and
    the frozen inputs spliced among them are immutable history, so a replay of them can be cached
    (`sqlcorpus.checkpointed`); pending and module files change from run to run and are replayed on top every time."""
    n = 0
    while n < len(files) and (is_promoted(files[n]) or frozen_replay.is_frozen(files[n])):
        n += 1
    return files[:n], files[n:]


def load_keyed_table_rows(table_name: str, columns: tuple[str, ...]) -> dict[int, dict]:
    """`load_table_rows` for a single-int-PK table, but *replaying*
    INSERT/UPDATE/DELETE in apply order (base dump, promoted, pending, module
    SQL) via `sql_dump.apply_statements` instead of unioning INSERTs - so an
    `UPDATE ... SET TrainerId = @TrainerId+12 WHERE CreatureId IN (...)`
    actually moves the rows it names. `columns[0]` is the key.

    The synthetic `DbcTable`'s `fmt` is derived from the table's own `CREATE TABLE` (`sql_dump.
    parse_create_table_string_columns`) rather than assumed all-numeric - `creature_default_trainer`
    (this function's original caller) happens to have none, but a caller with a real string column
    (e.g. `creature_template`'s `name`/`ScriptName`/...) would otherwise have every missing/NULL
    string value default to `0` instead of `''` (`sql_dump._fill_defaults`/`_apply_update`'s own
    NULL handling both key off `fmt`), a wrong value that then compares as different from a
    genuinely-unset declared string field."""
    base_path = BASE_SQL_DIR / f"{table_name}.sql"
    string_columns = (
        sql_dump.parse_create_table_string_columns(base_path, table_name) if base_path.is_file() else frozenset()
    )
    fmt = "n" + "".join("s" if c in string_columns else "i" for c in columns[1:])
    table = DbcTable(name=table_name, dbc_filename="", sql_table=table_name, fmt=fmt, columns=tuple(columns))

    def step(rows: dict[int, dict], path: Path) -> dict[int, dict]:
        text = sqlcorpus.read_text(path)
        sql_dump.apply_statements(rows, table, text, source=path.name)
        if path != base_path:
            _record_invisible(table_name, path, text, None)
        return rows

    stable, volatile = _split_stable(_migration_files_mentioning(table_name, loose=True))
    rows = sqlcorpus.checkpointed(
        "keyed_rows", (table_name, tuple(columns)), ([base_path] if base_path.is_file() else []) + stable, dict, step,
    )
    for path in volatile:
        step(rows, path)
    return rows


def load_replayed_table_rows(
    table_name: str, columns: tuple[str, ...], key_columns: tuple[str, ...],
    warn_skipped: bool = False, fill_missing: bool = False,
) -> list[dict]:
    """True live state for `table_name`, replaying INSERT/UPDATE/DELETE in apply order across the
    base dump and every migration/module file that mentions it - unlike `load_table_rows`'s plain
    union of every INSERT ever seen, this actually reflects a later hand-written UPDATE or DELETE.

    Built for `creature_template`/`creature_template_model` (`lib/spell_tables.py`'s
    `CREATURE_TABLES`): their real migration history has genuine hand-written point fixes after
    the original INSERT - Frozen Orb 300001's `flags_extra` (194 -> 66) and `CreatureDisplayID`
    (through several revisions) both changed this way in `data/sql/updates/db_world/
    2026_09_01_01.sql` - so `load_table_rows`'s union kept reporting the *original* INSERT's
    values as live forever, which made a re-declaration matching that stale value look unchanged
    and silently skip re-emitting the real fix (found via code review, 2026-09-28).

    Always uses `sql_dump.apply_composite_key_statements` (even for a single-column key, e.g.
    `creature_template`'s bare `("entry",)`) rather than `load_keyed_table_rows`/`apply_statements`
    - deliberately, not just for one code path instead of two: `apply_statements`'s INSERT handling
    calls `_fill_defaults`, which backfills a column a partial-column-list INSERT omitted with a
    blanket `0`/`''` *immediately*, so the key is never actually missing from the row dict by the
    time a caller sees it - defeating `lib.spell_tables.TableSpec.defaults`'s whole point (a
    missing key falling back to the column's *real* schema default, not a blanket `0`). This
    matters for exactly the same reason the AND-guard/composite-key work above does: three real
    module SQL files (`mod-transmog`, `mod-mythic-plus` x2) INSERT `creature_template` with a
    partial column list, so this isn't a hypothetical (found via code review, 2026-09-28).
    `apply_composite_key_statements`'s own INSERT handling never calls `_fill_defaults` - a column
    a statement didn't mention simply isn't in the row dict, exactly what `TableSpec.defaults`
    needs to see.

    Every statement on `table_name` the replay could not apply is recorded in the run's skip log
    (`sqlcorpus.SKIPS`, summarised by `generate.py`). `warn_skipped` also prints a WARNING (file name plus the start
    of the statement) for each one right away. Opt-in because most callers' tables tolerate an imperfect replay;
    `lib/trainer_pricing.py` writes rows derived from this one, so an unapplied DELETE there could resurrect a row.
    With it on, a file is also scanned for statements the replay's scanner cannot even see (unquoted table name,
    `UPDATE ... AS alias`); each prints the same WARNING.

    The table's schema defaults (base dump `CREATE TABLE`) fill a key column an INSERT left out and judge a WHERE on
    any other column an INSERT left out (`sql_dump.apply_composite_key_statements`'s `defaults`).

    `fill_missing` gives columns an INSERT omitted the value 0 at INSERT time (see
    `sql_dump.apply_composite_key_statements`); only for tables whose columns all default to 0.

    The WHERE of a DELETE/UPDATE may use OR / AND / `=` / `IN (...)` / `BETWEEN`, and `SET col = col | n`
    style expressions are evaluated (`sql_dump.parse_where_predicate`); this applies to every caller."""
    base_path = BASE_SQL_DIR / f"{table_name}.sql"

    def reporter(path: Path) -> Callable[[str], None] | None:
        if not warn_skipped:
            return None
        return lambda snippet: print(
            f"WARNING: trainer_state.py: {path.name}: cannot replay this {table_name} statement, "
            f"live state may be wrong: {' '.join(snippet.split())[:100]}"
        )

    defaults = sql_dump.parse_create_table_defaults(base_path, table_name) if base_path.is_file() else {}
    int_columns = sql_dump.parse_create_table_int_columns(base_path, table_name) if base_path.is_file() else None

    def step(rows: dict[tuple, dict], path: Path) -> dict[tuple, dict]:
        text = sqlcorpus.read_text(path)
        sql_dump.apply_composite_key_statements(
            rows, columns, key_columns, table_name, text, reporter(path), fill_missing, defaults=defaults,
            source=path.name, int_columns=int_columns,
        )
        if path != base_path:
            _record_invisible(table_name, path, text, reporter(path))
        return rows

    stable, volatile = _split_stable(_migration_files_mentioning(table_name, loose=True))
    rows = sqlcorpus.checkpointed(
        "replayed_rows", (table_name, tuple(columns), tuple(key_columns), warn_skipped, fill_missing),
        ([base_path] if base_path.is_file() else []) + stable, dict, step,
    )
    for path in volatile:
        step(rows, path)
    return list(rows.values())


class TrainerIndex:
    """Precomputed once per `generate.py` run - scanning every migration
    file for each of ~4 tables is not something a per-spell/per-talent DSL
    call (`trained_by`) should redo itself. Also exposes the current
    `trainer_spell` rows so a caller can skip re-emitting SQL for a grant
    that's already live, identically."""

    def __init__(
        self,
        creature_default_trainer: list[dict],
        trainer_spell: list[dict],
        creature_template: list[dict],
        creature: list[dict],
    ):
        self._creature_ids_by_trainer: dict[int, set[int]] = {}
        for row in creature_default_trainer:
            self._creature_ids_by_trainer.setdefault(int(row["TrainerId"]), set()).add(
                int(row["CreatureId"])
            )

        self._npcflag_by_entry: dict[int, int] = {}
        for row in creature_template:
            self._npcflag_by_entry[int(row["entry"])] = int(row["npcflag"])

        self._spawned_entries: set[int] = set()
        for row in creature:
            for key in ("id1", "id2", "id3"):
                value = row.get(key)
                if value:
                    self._spawned_entries.add(int(value))

        self.existing_trainer_spells: dict[tuple[int, int], dict] = {
            (int(row["TrainerId"]), int(row["SpellId"])): row for row in trainer_spell
        }

    def trainer_problems(self, trainer_id: int) -> list[str]:
        """Human-readable problems with `trainer_id` - empty means "at
        least one creature_default_trainer row for this TrainerId resolves
        to a creature_template flagged UNIT_NPC_FLAG_TRAINER that's actually
        spawned somewhere". Doesn't raise itself, so a caller can fold every
        rank's problems into one clear error (see registry.trained_by)."""
        creature_ids = self._creature_ids_by_trainer.get(trainer_id, set())
        if not creature_ids:
            return [f"TrainerId {trainer_id} has no creature_default_trainer row at all"]
        problems = []
        for creature_id in sorted(creature_ids):
            npcflag = self._npcflag_by_entry.get(creature_id)
            if npcflag is None:
                problems.append(
                    f"creature_default_trainer -> CreatureId {creature_id} has no "
                    f"creature_template row"
                )
            elif not (npcflag & UNIT_NPC_FLAG_TRAINER):
                problems.append(
                    f"creature_template {creature_id}'s npcflag ({npcflag}) doesn't include "
                    f"UNIT_NPC_FLAG_TRAINER (0x10)"
                )
            elif creature_id not in self._spawned_entries:
                problems.append(
                    f"creature_template {creature_id} is flagged as a trainer but has no spawn "
                    f"in `creature`"
                )
            else:
                return []  # at least one CreatureId for this TrainerId fully checks out
        return problems


def load_trainer_index() -> TrainerIndex:
    return TrainerIndex(
        list(load_keyed_table_rows("creature_default_trainer", ("CreatureId", "TrainerId")).values()),
        load_table_rows("trainer_spell"),
        # TrainerIndex reads two columns of creature_template and three of creature (150k rows): keep just those.
        load_table_rows("creature_template", project=("entry", "npcflag")),
        load_table_rows("creature", project=("id1", "id2", "id3")),
    )
