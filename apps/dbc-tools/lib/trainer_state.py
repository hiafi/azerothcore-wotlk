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

**Module SQL counts too.** `DBUpdater` applies every module's own
`data/sql/db-world/*.sql` at worldserver start, and mod-progression applies
`src/phase_NN/sql/*.sql` for every phase up to the configured
`Progression.Phase` - and phase_00 is exactly where this server's class
trainers get rewired (`UPDATE creature_default_trainer SET TrainerId =
@TrainerId+N WHERE CreatureId IN (...)`: every mage trainer moves from the
stock 16 to 212). Scanning only `data/sql/` made `trained_by()` reject the
one TrainerId that actually works here (first hit: Meteor, Fire Mage
rework, 2026-09-15), so both module locations are scanned as well - see
`MODULE_SQL_FILES`.

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

import re

from . import sql_dump
from .dbcfmt import DbcTable

REPO_ROOT = Path(__file__).resolve().parents[3]
BASE_SQL_DIR = REPO_ROOT / "data" / "sql" / "base" / "db_world"
PROMOTED_SQL_DIR = REPO_ROOT / "data" / "sql" / "updates" / "db_world"
PENDING_SQL_DIR = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world"
MODULES_DIR = REPO_ROOT / "modules"
# The worldserver.conf-side modules config this deployment actually runs with (docker bind-mounts
# env/dist/etc); the .dist default is the fallback for a checkout with no env/ yet.
PROGRESSION_CONF = REPO_ROOT / "env" / "dist" / "etc" / "modules" / "mod_progression.conf"
PROGRESSION_CONF_DIST = MODULES_DIR / "mod-progression" / "conf" / "mod_progression.conf.dist"
PROGRESSION_PHASE_DEFAULT = 18  # mod_progression_database.cpp's GetOption default

_PROGRESSION_PHASE_RE = re.compile(r"^\s*Progression\.Phase\s*=\s*(\d+)", re.MULTILINE)


def progression_phase() -> int:
    """`Progression.Phase` as the live server sees it - mod-progression applies
    `src/phase_NN/sql/` for every NN <= this (mod_progression_database.cpp's
    GetActivePhases)."""
    for conf in (PROGRESSION_CONF, PROGRESSION_CONF_DIST):
        if conf.is_file():
            m = _PROGRESSION_PHASE_RE.search(conf.read_text(encoding="utf-8"))
            if m:
                return int(m.group(1))
    return PROGRESSION_PHASE_DEFAULT


def module_sql_files() -> list[Path]:
    """Every module SQL file `DBUpdater` would apply to the world DB, in the
    order it applies them: each module's `data/sql/db-world/` (recursively -
    some modules nest a `base/`/`updates/` split), then mod-progression's
    active phases in phase order."""
    if not MODULES_DIR.is_dir():
        return []
    files: list[Path] = []
    for module_dir in sorted(MODULES_DIR.iterdir()):
        world = module_dir / "data" / "sql" / "db-world"
        if world.is_dir():
            files.extend(sorted(world.rglob("*.sql")))
    phases_root = MODULES_DIR / "mod-progression" / "src"
    if phases_root.is_dir():
        for phase in range(progression_phase() + 1):
            files.extend(sorted((phases_root / f"phase_{phase:02}" / "sql").glob("*.sql")))
    return files

# src/server/game/Entities/Unit/UnitDefines.h
UNIT_NPC_FLAG_TRAINER = 0x00000010

_TRAINER_TABLES = ("creature_default_trainer", "trainer_spell", "creature_template", "creature")


def load_table_rows(table_name: str) -> list[dict]:
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
    a run trying to do something unrelated to whichever migration choked."""
    base_path = BASE_SQL_DIR / f"{table_name}.sql"
    fallback_columns: tuple[str, ...] = ()
    rows: list[dict] = []
    if base_path.is_file():
        fallback_columns = sql_dump.parse_create_table_columns(base_path, table_name)
        rows.extend(sql_dump.read_table_rows(base_path, table_name, fallback_columns))
    for path in _migration_files_mentioning(table_name):
        try:
            rows.extend(sql_dump.read_table_rows(path, table_name, fallback_columns))
        except Exception as exc:  # pragma: no cover - defensive, see docstring above
            print(f"warning: trainer_state.py: skipping {path} for {table_name}: {exc}")
    return rows


def _migration_files_mentioning(table_name: str) -> list[Path]:
    """Every non-base SQL file that mentions `table_name`, in apply order:
    promoted core updates, pending core updates, then module SQL (a cheap
    substring check before bothering to parse each file)."""
    needle = f"`{table_name}`"
    candidates = [
        *(sorted(PROMOTED_SQL_DIR.glob("*.sql")) if PROMOTED_SQL_DIR.is_dir() else []),
        *(sorted(PENDING_SQL_DIR.glob("*.sql")) if PENDING_SQL_DIR.is_dir() else []),
        *module_sql_files(),
    ]
    return [p for p in candidates if needle in p.read_text(encoding="utf-8")]


def load_keyed_table_rows(table_name: str, columns: tuple[str, ...]) -> dict[int, dict]:
    """`load_table_rows` for a single-int-PK table, but *replaying*
    INSERT/UPDATE/DELETE in apply order (base dump, promoted, pending, module
    SQL) via `sql_dump.apply_statements` instead of unioning INSERTs - so an
    `UPDATE ... SET TrainerId = @TrainerId+12 WHERE CreatureId IN (...)`
    actually moves the rows it names. `columns[0]` is the key."""
    table = DbcTable(
        name=table_name, dbc_filename="", sql_table=table_name,
        fmt="n" + "i" * (len(columns) - 1), columns=tuple(columns),
    )
    rows: dict[int, dict] = {}
    base_path = BASE_SQL_DIR / f"{table_name}.sql"
    if base_path.is_file():
        sql_dump.apply_statements(rows, table, base_path.read_text(encoding="utf-8"))
    for path in _migration_files_mentioning(table_name):
        sql_dump.apply_statements(rows, table, path.read_text(encoding="utf-8"))
    return rows


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
        *(load_table_rows(name) for name in _TRAINER_TABLES[1:]),
    )
