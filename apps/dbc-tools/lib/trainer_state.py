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

**Known limitation**: this is a union of every `INSERT` ever seen for these
tables across every file scanned - it does NOT replay `DELETE`/`UPDATE`
statements against them the way `lib/state.py`/`lib/sql_dump.py`'s
`apply_statements` does for `lib/dbcfmt.py`'s single-int-PK DBC tables
(`creature_default_trainer`/`trainer_spell`/`creature`/`creature_template`
don't fit that single-PK shape). A row inserted once and later deleted would
still read as "exists" here. Acceptable for what this is used for - a
build-time sanity check that a `TrainerId` isn't obviously dead, not a
source of truth for trainer content itself - but worth knowing about before
trusting this module for anything else.
"""

from __future__ import annotations

from pathlib import Path

from . import sql_dump

REPO_ROOT = Path(__file__).resolve().parents[3]
BASE_SQL_DIR = REPO_ROOT / "data" / "sql" / "base" / "db_world"
PROMOTED_SQL_DIR = REPO_ROOT / "data" / "sql" / "updates" / "db_world"
PENDING_SQL_DIR = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world"

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
    needle = f"`{table_name}`"
    for directory in (PROMOTED_SQL_DIR, PENDING_SQL_DIR):
        for path in sorted(directory.glob("*.sql")):
            text = path.read_text(encoding="utf-8")
            if needle not in text:
                continue
            try:
                rows.extend(sql_dump.read_table_rows(path, table_name, fallback_columns))
            except Exception as exc:  # pragma: no cover - defensive, see docstring above
                print(f"warning: trainer_state.py: skipping {path} for {table_name}: {exc}")
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
    return TrainerIndex(*(load_table_rows(name) for name in _TRAINER_TABLES))
