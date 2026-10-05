"""
Emission of the three plain world-DB spell tables a `source/classes/*` DSL
file can declare alongside a spell - `spell_script_names` (`scripted_by`),
`spell_bonus_data` (`bonus_coefficients`) and `spell_proc` (`procs_on`), all
in `lib/dsl/registry.py`. Before this, every one of them was a separate
hand-written migration next to the C++ it belongs to (see any
`data/sql/updates/db_world/2026_09_*.sql` from the Arcane Mage rework),
which is exactly the "declared in one place, wired in a second, forgot the
second" bug shape the DSL exists to close: a script name with no
`spell_script_names` row never runs and never logs; a custom spell with no
`spell_bonus_data` row silently gets the engine's cast-time-derived
coefficient instead of the one the design doc specifies.

Same mechanics as `trainer_spell`'s path in `generate.py`: each table's
declared rows are diffed against what's already live (a static scan of the
base dump + every migration, via `trainer_state.load_table_rows`) so a
rerun with unchanged source emits nothing, and what does change is rendered
with `sql_out.render_generic_table_block`'s DELETE-then-INSERT on the exact
key tuples. Inherits `load_table_rows`'s "union of INSERTs, no DELETE
replay" limitation - a row deleted by a later migration still reads as
live here, so it can only ever under-emit an unchanged row, never emit a
wrong one.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pathlib import Path

from . import dbcfmt, sql_dump, sql_out, trainer_state

# Column tuples mirror each table's CREATE TABLE in data/sql/base/db_world/,
# minus the synthetic "id" the registry adds for duplicate-declaration
# bookkeeping (see Registry's docstring).
SPELL_SCRIPT_NAMES_COLUMNS = ("spell_id", "ScriptName")
SPELL_BONUS_DATA_COLUMNS = ("entry", "direct_bonus", "dot_bonus", "ap_bonus", "ap_dot_bonus", "comments")
# Potency system (docs/potency-system.md, PLAN P1/P2): spell_potency_correction, the one
# hand-written CREATE TABLE this whole DSL is allowed (pending_db_world's P1 migration;
# `.agents/docs/systems/dbc-tools.md` - every other declared table here is otherwise generator-
# owned from day one). `cp_*` are reserved for P7's finishers, always 0 until then.
SPELL_POTENCY_CORRECTION_COLUMNS = (
    "spell_id", "effect_index", "correction_per_level", "breakpoint_level", "variance_pct",
    "cp_line", "cp_correction_per_level", "cp_ap", "comment",
)
SPELL_PROC_COLUMNS = (
    "SpellId", "SchoolMask", "SpellFamilyName", "SpellFamilyMask0", "SpellFamilyMask1",
    "SpellFamilyMask2", "ProcFlags", "SpellTypeMask", "SpellPhaseMask", "HitMask",
    "AttributesMask", "DisableEffectsMask", "ProcsPerMinute", "Chance", "Cooldown", "Charges",
)
# WP-T (.agents/plans/druid-rework/druid-rework.WP-T-HANDOFF.md, PLAN B11/§5.0): five more
# declared tables, same column-tuple-mirrors-CREATE-TABLE convention as the three above.
SPELL_LINKED_SPELL_COLUMNS = ("spell_trigger", "spell_effect", "type", "comment")
SPELL_GROUP_COLUMNS = ("id", "spell_id")
SPELL_GROUP_STACK_RULES_COLUMNS = ("group_id", "stack_rule", "description")
SPELL_CUSTOM_ATTR_COLUMNS = ("spell_id", "attributes")
# Paladin T1: spellcategory_dbc is a pure server-side overlay (empty base table) - see
# lib.dsl.registry.spell_category().
SPELLCATEGORY_COLUMNS = ("ID", "Flags")
# spellshapeshiftform_dbc is DBC-backed (unlike the other four, plain world-DB tables) - reuse
# lib.dbcfmt's own column list rather than re-transcribing it a second time.
SPELLSHAPESHIFTFORM_COLUMNS = dbcfmt.SPELLSHAPESHIFTFORM.columns

# T1 (.agents/plans/warlock-rework/warlock-rework.T1-HANDOFF.md): creature_template/
# creature_template_model - a rework's own NPCs, previously always a hand-written migration (e.g.
# Tentacle of Madness, data/sql/updates/db_world/2026_09_23_12.sql). creature_template is ~54
# columns wide and on the SQL linter's do-not-delete list (apps/codestyle/codestyle-sql.py's
# `not_delete`) - unlike every column tuple above, this one is parsed from the base dump's own
# CREATE TABLE rather than hand-transcribed (see sql_dump.parse_create_table_columns's own
# docstring on why that matters for a table this wide), and its per-column DEFAULTs are parsed the
# same way for lib.dsl.registry.creature_template()'s "full row" building. creature_template_model
# is narrow (6 columns, no other table reuses them) and stays a hand-typed tuple like every table
# above.
CREATURE_TEMPLATE_PATH = trainer_state.BASE_SQL_DIR / "creature_template.sql"
CREATURE_TEMPLATE_COLUMNS = sql_dump.parse_create_table_columns(CREATURE_TEMPLATE_PATH, "creature_template")
CREATURE_TEMPLATE_DEFAULTS = sql_dump.parse_create_table_defaults(CREATURE_TEMPLATE_PATH, "creature_template")
CREATURE_TEMPLATE_MODEL_COLUMNS = (
    "CreatureID", "Idx", "CreatureDisplayID", "DisplayScale", "Probability", "VerifiedBuild",
)


# First line of every file `generate.py` writes (its `header`). This is the
# prune pass's whole notion of provenance: a row is ours to remove only if a
# past run of this tool emitted it, and marker-bearing files are exactly the
# set of files past runs wrote. Everything else - the base dump, hand-written
# migrations, module SQL - is off limits by construction. Keep in sync with
# `generate.py`'s `header`.
GENERATED_MARKER = "-- Generated by apps/dbc-tools/generate.py"


def _is_generated(path: Path) -> bool:
    """Cheap first-*two*-lines check; a file that can't be read isn't ours.

    Not just line 1: `apps/ci/ci-pending-sql.sh`'s promotion step
    (`pending_db_world` -> `db_world`) always prepends exactly one
    `-- DB update X -> Y` header line above whatever the file started with
    (`echo ... >"$OUTPUT_FILE"` then `cat "$entry" >>"$OUTPUT_FILE"` - a
    real, verified promotion, not a guess), pushing `GENERATED_MARKER` from
    line 1 to line 2. Checking only line 1 meant every promoted generated
    file silently stopped being recognized as "ours" - both for the prune
    pass above and for `load_removed_keys` below (found via review,
    2026-09-23: confirmed against every real file in
    `data/sql/updates/db_world/`, which all start with `-- DB update`)."""
    try:
        with path.open(encoding="utf-8") as fh:
            first_two = (fh.readline(), fh.readline())
        return any(line.startswith(GENERATED_MARKER) for line in first_two)
    except OSError:  # pragma: no cover - defensive
        return False


def load_generated_table_rows(table_name: str, key_columns: tuple[str, ...]) -> list[dict]:
    """Rows this tool has emitted and not since removed, replayed in apply
    order across every generated migration still on disk.

    Deliberately *not* `trainer_state.load_table_rows`: that one unions the
    base dump and every migration regardless of author, which is the right
    answer for "what's live" and exactly the wrong one for "what may we
    delete".

    It is also a real **replay** rather than that function's union of
    INSERTs, because the prune pass writes its own DELETEs into these very
    files. Taking the union would re-report every already-pruned row on every
    subsequent run, forever - emitting a redundant DELETE each time and
    writing a migration file even for an otherwise no-op run.

    An unrecognized DELETE shape is treated as "this file may have removed
    anything": the table's emitted set is dropped, which can only make the
    prune *smaller* (nothing gets deleted that shouldn't). Generated files
    only ever contain the shapes `sql_out.py` emits, so this is a guard
    against a future emitter change, not an expected path."""
    fallback_columns: tuple[str, ...] = ()
    base_path = trainer_state.BASE_SQL_DIR / f"{table_name}.sql"
    if base_path.is_file():
        fallback_columns = sql_dump.parse_create_table_columns(base_path, table_name)

    live: dict[tuple, dict] = {}
    for path in trainer_state._migration_files_mentioning(table_name):
        if not _is_generated(path):
            continue
        try:
            for kind, payload in sql_dump.read_table_statements(path, table_name, fallback_columns):
                if kind == "insert":
                    for row in payload:
                        key = _row_key(row, key_columns)
                        if key is not None:
                            live[key] = row
                elif kind == "delete":
                    delete_cols, key_tuples = payload
                    for values in key_tuples:
                        for key in _matching_keys(live, key_columns, delete_cols, values):
                            live.pop(key, None)
                else:  # delete_unparsed
                    print(
                        f"warning: spell_tables.py: {path} has a DELETE on {table_name} in a shape "
                        f"this replay doesn't understand; skipping prune for {table_name}"
                    )
                    return []
        except Exception as exc:  # pragma: no cover - defensive, cf. load_table_rows
            print(f"warning: spell_tables.py: skipping {path} for {table_name}: {exc}")
    return list(live.values())


def _row_key(row: dict, key_columns: tuple[str, ...]) -> tuple | None:
    try:
        return tuple(_normalise(row[c]) for c in key_columns)
    except KeyError:
        return None


def _matching_keys(
    live: dict[tuple, dict], key_columns: tuple[str, ...],
    delete_cols: tuple[str, ...], values: tuple,
) -> list[tuple]:
    """Keys in `live` that a DELETE naming `delete_cols` = `values` removes.

    Usually `delete_cols` is the table's full key and this is a single exact
    hit. It can also be a *prefix* - a single-column `DELETE ... WHERE
    SpellId IN (...)` against a table keyed on more than one column - in
    which case every key sharing those leading values goes."""
    wanted = tuple(_normalise(v) for v in values)
    if delete_cols == key_columns:
        return [wanted] if wanted in live else []
    try:
        idx = [key_columns.index(c) for c in delete_cols]
    except ValueError:
        return []  # a column we don't key on - can't tell what it removes, so remove nothing
    return [k for k in live if tuple(k[i] for i in idx) == wanted]


def load_base_table_rows(table_name: str) -> list[dict]:
    """Stock rows only, straight from the base dump - used to refuse to prune
    a key a past run *overrode* rather than introduced (safety rule 1 of
    `.agents/plans/dbc-tools-prune-pass/dbc-tools-prune-pass.PLAN.md`)."""
    base_path = trainer_state.BASE_SQL_DIR / f"{table_name}.sql"
    if not base_path.is_file():
        return []
    columns = sql_dump.parse_create_table_columns(base_path, table_name)
    return sql_dump.read_table_rows(base_path, table_name, columns)


@dataclass(frozen=True)
class TableSpec:
    name: str
    columns: tuple[str, ...]
    key_columns: tuple[str, ...]
    registry_key: str  # the lib.dsl.registry.Registry attribute holding declared rows
    # Real per-column schema DEFAULT, for a table where that isn't 0/NULL for every column (e.g.
    # creature_template's minlevel=1, speed_run=1.14286, ...) - see _same_row's docstring for why
    # a table needing this must pass its own, or comparing a declaration against a migration that
    # omitted one of these columns silently mis-detects "unchanged". Empty for every table where
    # 0/NULL is already correct (unaffected - see _same_row's fallback).
    defaults: dict = field(default_factory=dict)


SPELL_TABLES = (
    TableSpec("spell_script_names", SPELL_SCRIPT_NAMES_COLUMNS, ("spell_id", "ScriptName"), "spell_script_names"),
    TableSpec("spell_bonus_data", SPELL_BONUS_DATA_COLUMNS, ("entry",), "spell_bonus_data"),
    TableSpec("spell_proc", SPELL_PROC_COLUMNS, ("SpellId",), "spell_procs"),
    TableSpec(
        "spell_linked_spell", SPELL_LINKED_SPELL_COLUMNS,
        ("spell_trigger", "spell_effect", "type"), "linked_spells",
    ),
    TableSpec("spell_group", SPELL_GROUP_COLUMNS, ("id", "spell_id"), "spell_groups"),
    TableSpec(
        "spell_group_stack_rules", SPELL_GROUP_STACK_RULES_COLUMNS, ("group_id",), "spell_group_rules",
    ),
    TableSpec("spell_custom_attr", SPELL_CUSTOM_ATTR_COLUMNS, ("spell_id",), "custom_attrs"),
    TableSpec("spellshapeshiftform_dbc", SPELLSHAPESHIFTFORM_COLUMNS, ("ID",), "shapeshift_forms"),
    TableSpec("spellcategory_dbc", SPELLCATEGORY_COLUMNS, ("ID",), "spell_categories"),
    TableSpec(
        "spell_potency_correction", SPELL_POTENCY_CORRECTION_COLUMNS,
        ("spell_id", "effect_index"), "potency_corrections",
    ),
)


def _normalise(value):
    """Live rows come back from `sql_dump` with whatever literal shape the
    migration used (`0` vs `0.0`, `NULL` vs `''`); the DSL always produces
    typed Python values. Compare on a common footing so a declaration that
    matches what's live in every way that matters isn't re-emitted over a
    formatting difference."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return str(value)


def _same_row(existing: dict, declared: dict, spec: TableSpec) -> bool:
    """A column a hand-written migration left out entirely took the table's
    own schema DEFAULT - `0`/`NULL` for every column in the original three tables (and the five
    WP-T ones after them), so the old fallback (0 for a numeric declared value, else `None`)
    happened to always be right for those. `creature_template` breaks that assumption - many of
    its columns default to something else (`minlevel`/`maxlevel` 1, `speed_run` 1.14286,
    `RegenHealth` 1, ...), confirmed as a live case via code review (2026-09-28): three module SQL
    files really do INSERT `creature_template` with a partial column list omitting one of these.
    `spec.defaults` (its real per-column schema DEFAULT, when the caller has one - see
    `TableSpec`'s own comment) is checked first; the old 0/None guess is still the fallback for
    every table that never needed anything else."""
    for c in spec.columns:
        if c in spec.defaults:
            default = spec.defaults[c]
        else:
            default = 0 if isinstance(declared.get(c), (int, float)) else None
        if _normalise(existing.get(c, default)) != _normalise(declared.get(c)):
            return False
    return True


class SpellTableIndex:
    """Live rows for each of `SPELL_TABLES`, keyed by that table's key
    tuple - built once per `generate.py` run (each table means re-parsing
    every migration that mentions it)."""

    def __init__(
        self,
        existing: dict[str, list[dict]],
        emitted: dict[str, list[dict]] | None = None,
        base: dict[str, list[dict]] | None = None,
        tables: tuple[TableSpec, ...] = SPELL_TABLES,
    ):
        self._tables = tables
        self._by_key: dict[str, dict[tuple, dict]] = {}
        # Key sets for the prune pass: `_emitted` is what past runs of this
        # tool wrote (the only rows it may remove), `_base` is stock content
        # it must never leave a hole in. Both default empty so an index built
        # the old two-argument way simply has nothing to prune.
        self._emitted: dict[str, set[tuple]] = {}
        self._base: dict[str, set[tuple]] = {}
        for spec in tables:
            keyed: dict[tuple, dict] = {}
            for row in existing.get(spec.name, []):
                key = self._key(spec, row)
                if key is None:
                    continue  # a migration that inserted a partial column set can't be keyed
                keyed[key] = row  # later migrations win - files are scanned in sorted order
            self._by_key[spec.name] = keyed
            self._emitted[spec.name] = self._key_set(spec, (emitted or {}).get(spec.name, []))
            self._base[spec.name] = self._key_set(spec, (base or {}).get(spec.name, []))

    @staticmethod
    def _key(spec: TableSpec, row: dict) -> tuple | None:
        try:
            return tuple(_normalise(row[c]) for c in spec.key_columns)
        except KeyError:
            return None

    @classmethod
    def _key_set(cls, spec: TableSpec, rows: list[dict]) -> set[tuple]:
        return {k for k in (cls._key(spec, r) for r in rows) if k is not None}

    def live_keys(self, table_name: str) -> set[tuple]:
        """Key tuples already known live for `table_name` (one of `SPELL_TABLES`) - this index
        already scanned the base dump + every migration to build `_by_key` at construction time,
        so a caller that also needs "what's live" for one of these tables (e.g.
        `render_removal_blocks`'s typo guard) can reuse it instead of re-scanning the same files a
        second time (finding from review, 2026-09-23 - see `generate.py`'s wiring)."""
        return set(self._by_key.get(table_name, {}).keys())

    def live_rows(self, table_name: str) -> list[dict]:
        """Full rows already known live for `table_name` - same reuse rationale as `live_keys()`,
        for a caller that needs more than just the key (e.g. `lint.check_linked_spell_key_collisions`
        needs every column `_spell_linked_engine_key` reads, not just the key tuple)."""
        return list(self._by_key.get(table_name, {}).values())

    def rows_to_emit(self, spec: TableSpec, declared: list[dict]) -> list[dict]:
        """`declared` minus anything already live with identical values."""
        keyed = self._by_key.get(spec.name, {})
        out = []
        for row in declared:
            key = tuple(_normalise(row[c]) for c in spec.key_columns)
            existing = keyed.get(key)
            if existing is not None and _same_row(existing, row, spec):
                continue
            out.append(row)
        return out


    def rows_to_prune(self, spec: TableSpec, declared: list[dict]) -> PruneResult:
        """Keys a past run emitted that `declared` no longer claims.

        Two refusals, both from the PLAN's safety rules:

        * **Circuit breaker** - a table with an emitted history but *zero*
          declarations this run almost certainly means the source failed to
          load, not that every row was deliberately retired. Pruning then
          would wipe the table's whole managed surface, so refuse the table
          outright.
        * **Base overlap** - the key also exists in the stock dump, so a past
          run overrode a stock row instead of adding a new one. A DELETE would
          leave nothing where stock had something (only reachable for the
          single-key tables; `spell_script_names` is keyed on the
          spell/name pair, so a differently named stock script is a different
          key). Report it for a human instead of guessing."""
        emitted = self._emitted.get(spec.name, set())
        if not emitted:
            return PruneResult(spec, [], [], False)
        declared_keys = self._key_set(spec, declared)
        if not declared_keys:
            return PruneResult(spec, [], [], True)
        orphans = emitted - declared_keys
        base = self._base.get(spec.name, set())
        prunable = sql_out.stable_key_sort(k for k in orphans if k not in base)
        blocked = sql_out.stable_key_sort(k for k in orphans if k in base)
        return PruneResult(spec, prunable, blocked, False)


@dataclass(frozen=True)
class PruneResult:
    spec: TableSpec
    keys: list[tuple]           # safe to DELETE
    base_blocked: list[tuple]   # orphaned, but stock also owns the key - needs a human
    breaker_tripped: bool       # zero declarations for a table with history - refused


# Why an orphan in each table is not merely untidy - quoted into the emitted
# migration so the DELETE explains itself to whoever reads it later.
_PRUNE_WHY = {
    "spell_script_names": 'Left in place, a row naming a ScriptName that no\n'
                          '-- longer exists in C++ logs "Scriptname ... not found" at every boot.',
    "spell_proc": "Left in place, a stale row keeps a proc chance\n"
                  "-- alive that no declared script handles.",
    "spell_bonus_data": "Left in place, a stale row keeps overriding the\n"
                        "-- engine's own spell coefficient.",
}
_PRUNE_WHY_DEFAULT = "Left in place it keeps applying."


def render_prune_blocks(
    index: SpellTableIndex, dsl_classes: dict[str, list[dict]]
) -> tuple[list[str], list[str]]:
    """`(sql_blocks, report_lines)`. A prune is never silent: every removed
    row, every base-blocked orphan and every tripped breaker gets a line, and
    `generate.py` prints them all."""
    blocks: list[str] = []
    report: list[str] = []
    for spec in SPELL_TABLES:
        result = index.rows_to_prune(spec, dsl_classes.get(spec.registry_key, []))
        if result.breaker_tripped:
            report.append(
                f"prune: SKIPPED {spec.name} - it has rows from previous runs but this run "
                f"declared none. Refusing to delete the lot; check source/classes/* loaded."
            )
            continue
        for key in result.base_blocked:
            report.append(
                f"prune: NOT removing {spec.name} {_key_text(spec.key_columns, key)} - no longer "
                f"declared, but the stock dump owns this key too, so deleting it would leave a "
                f"hole where AzerothCore has a row. Resolve by hand."
            )
        if not result.keys:
            continue
        for key in result.keys:
            report.append(
                f"prune: removing {spec.name} {_key_text(spec.key_columns, key)} - no longer declared"
            )
        comment = (
            f"-- Prune: {len(result.keys)} {spec.name} row(s) emitted by an earlier "
            f"generate.py run that source/classes/*\n"
            f"-- no longer declares. {_PRUNE_WHY.get(spec.name, _PRUNE_WHY_DEFAULT)}"
        )
        blocks.append(
            sql_out.render_delete_only_block(spec.name, spec.key_columns, result.keys, comment)
        )
    return blocks, report


def pruned_keys(index: SpellTableIndex, dsl_classes: dict[str, list[dict]], table_name: str) -> set[tuple]:
    """Keys of `table_name` that `render_prune_blocks` will DELETE this run (empty when the table's
    breaker tripped; stock-dump-owned keys are never in it). Lets a lint treat a row as gone when
    this same run's output deletes it - see `lint.check_potency_bonus_overrides`."""
    for spec in SPELL_TABLES:
        if spec.name == table_name:
            result = index.rows_to_prune(spec, dsl_classes.get(spec.registry_key, []))
            return set() if result.breaker_tripped else set(result.keys)
    return set()


def _key_text(key_columns: tuple[str, ...], key: tuple) -> str:
    """`(spell_id=17322, ScriptName='spell_pri_shadow_reach')` - for humans.
    Key parts arrive `_normalise`d, so ints are floats by the time we see
    them; render whole numbers without the `.0`."""
    parts = []
    for column, value in zip(key_columns, key):
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        parts.append(f"{column}={value!r}" if isinstance(value, str) else f"{column}={value}")
    return "(" + ", ".join(parts) + ")"


def load_spell_table_index() -> SpellTableIndex:
    return SpellTableIndex(
        {spec.name: trainer_state.load_table_rows(spec.name) for spec in SPELL_TABLES},
        emitted={spec.name: load_generated_table_rows(spec.name, spec.key_columns) for spec in SPELL_TABLES},
        base={spec.name: load_base_table_rows(spec.name) for spec in SPELL_TABLES},
    )


def render_blocks(index: SpellTableIndex, dsl_classes: dict[str, list[dict]]) -> list[str]:
    """One pre-rendered SQL block per table that has something new/changed
    to say, in `SPELL_TABLES` order, ready for `sql_out.emit_pending_sql`'s
    `extra_blocks`. Empty strings (nothing to emit) are dropped."""
    blocks = []
    for spec in SPELL_TABLES:
        rows = index.rows_to_emit(spec, dsl_classes.get(spec.registry_key, []))
        block = sql_out.render_generic_table_block(spec.name, spec.columns, spec.key_columns, rows)
        if block:
            blocks.append(block)
    return blocks


def count_declared(
    dsl_classes: dict[str, list[dict]], tables: tuple[TableSpec, ...] = SPELL_TABLES,
) -> dict[str, int]:
    return {spec.name: len(dsl_classes.get(spec.registry_key, [])) for spec in tables}


# ---------------------------------------------------------------------------
# T1 (.agents/plans/warlock-rework/warlock-rework.T1-HANDOFF.md): creature_template/
# creature_template_model. Kept out of SPELL_TABLES/render_prune_blocks entirely, deliberately -
# creature_template is on the SQL linter's do-not-delete list, so it's never DELETE-then-INSERT'd
# the way every SPELL_TABLES entry is (see lib.dsl.registry.creature_template()'s docstring and
# lib.sql_out.render_upsert_block), and pruning only creature_template_model would leave a creature
# without a model. render_creature_retirement_report below reuses SpellTableIndex.rows_to_prune's
# orphan detection (same "emitted earlier, not declared now" computation render_prune_blocks uses)
# but only ever reports an orphan - it never turns one into a DELETE.
# ---------------------------------------------------------------------------

# creature_template_model's own real schema defaults (data/sql/base/db_world/
# creature_template_model.sql's CREATE TABLE) - hand-typed like its column tuple above (6 columns,
# narrow and stable), NOT lib.dsl.registry.creature_model()'s friendlier probability=1.0 default
# (that one's deliberately different from the schema's 0 - see that helper's docstring). _same_row
# needs the real schema value here: what a migration that omitted this column would actually have.
CREATURE_TEMPLATE_MODEL_DEFAULTS = {"Idx": 0, "DisplayScale": 1.0, "Probability": 0.0, "VerifiedBuild": None}

CREATURE_TABLES = (
    TableSpec(
        "creature_template", CREATURE_TEMPLATE_COLUMNS, ("entry",), "creature_templates",
        defaults=CREATURE_TEMPLATE_DEFAULTS,
    ),
    TableSpec(
        "creature_template_model", CREATURE_TEMPLATE_MODEL_COLUMNS, ("CreatureID", "Idx"),
        "creature_template_models", defaults=CREATURE_TEMPLATE_MODEL_DEFAULTS,
    ),
)


def load_creature_table_index() -> SpellTableIndex:
    """Loading the base creature_template dump (~30k rows, 5MB) again here (trainer_state.py's
    TrainerIndex already parsed it once, for a different purpose - npcflag/spawn lookups) is
    acceptable per the T1 handoff, rather than plumbing that already-parsed list through just to
    avoid a second pass.

    Uses `trainer_state.load_replayed_table_rows`, not `load_table_rows` - a real bug, found via
    code review (2026-09-28): `load_table_rows` unions every INSERT ever seen and never replays an
    UPDATE/DELETE, which stays correct for the other declared tables (their real migration history
    is always DELETE-then-INSERT) but is wrong for creature_template/creature_template_model - both
    have genuine hand-written point-fix UPDATEs after the original INSERT (Frozen Orb 300001's
    `flags_extra` 194->66 and `CreatureDisplayID` through several revisions,
    `data/sql/updates/db_world/2026_09_01_01.sql`). A union view kept reporting those *original*
    values as live forever, so a later re-declaration matching the stale value would have compared
    as unchanged and silently never re-applied the real fix. See
    `lib.trainer_state.load_replayed_table_rows`'s own docstring."""
    return SpellTableIndex(
        {
            spec.name: trainer_state.load_replayed_table_rows(spec.name, spec.columns, spec.key_columns)
            for spec in CREATURE_TABLES
        },
        emitted={spec.name: load_generated_table_rows(spec.name, spec.key_columns) for spec in CREATURE_TABLES},
        base={spec.name: load_base_table_rows(spec.name) for spec in CREATURE_TABLES},
        tables=CREATURE_TABLES,
    )


def render_creature_blocks(index: SpellTableIndex, dsl_classes: dict[str, list[dict]]) -> list[str]:
    """One pre-rendered SQL block per `CREATURE_TABLES` entry with something new/changed to emit,
    in `CREATURE_TABLES` order (creature_template before creature_template_model, per the T1
    handoff) - `creature_template` renders as an upsert (`sql_out.render_upsert_block`, no DELETE
    ever), `creature_template_model` as the same DELETE-then-INSERT every other declared table
    here gets (`sql_out.render_generic_table_block`) - deleting a specific (CreatureID, Idx) model
    row it's about to re-insert is fine; it's *creature_template* the linter refuses to see
    DELETEd, and *dropping a declaration* that neither table ever prunes for (see this module's
    docstring above)."""
    blocks = []
    for spec in CREATURE_TABLES:
        rows = index.rows_to_emit(spec, dsl_classes.get(spec.registry_key, []))
        if not rows:
            continue
        if spec.name == "creature_template":
            block = sql_out.render_upsert_block(spec.name, spec.columns, spec.key_columns, rows)
        else:
            block = sql_out.render_generic_table_block(spec.name, spec.columns, spec.key_columns, rows)
        if block:
            blocks.append(block)
    return blocks


def render_creature_retirement_report(
    index: SpellTableIndex, dsl_classes: dict[str, list[dict]]
) -> list[str]:
    """Report-only counterpart to `render_prune_blocks` for `CREATURE_TABLES`: a creature row a
    past run emitted that source no longer declares is never turned into a DELETE (see this
    module's docstring above) - just reported, for a human to remove by hand if they actually want
    it gone. Reuses `SpellTableIndex.rows_to_prune`'s orphan computation (circuit breaker + base-
    overlap refusal included) purely for "what's no longer declared"; nothing here ever renders a
    SQL block."""
    report: list[str] = []
    for spec in CREATURE_TABLES:
        result = index.rows_to_prune(spec, dsl_classes.get(spec.registry_key, []))
        if result.breaker_tripped:
            report.append(
                f"creature: SKIPPED checking {spec.name} for retired entries - it has rows from "
                f"previous runs but this run declared none. Check source/classes/* loaded."
            )
            continue
        for key in (*result.keys, *result.base_blocked):
            report.append(
                f"creature: {spec.name} {_key_text(spec.key_columns, key)} is no longer declared - "
                f"left in place; {spec.name} is never auto-deleted, remove by hand if wanted."
            )
    return report


# ---------------------------------------------------------------------------
# Declared removals (WP-T, PLAN B11/§5.0): unbind_script()/unlink_spell()/
# leave_spell_group()/untrain() in lib/dsl/registry.py. A key-exact DELETE for
# a row this tool never emitted itself (stock Blizzard data, or an older
# hand-written migration) - the one sanctioned way to retract one, since the
# prune pass above only ever touches rows a *past generate.py run* emitted
# (its `_emitted` set). A declared removal must never be treated as a prune
# orphan (there's nothing in `_emitted` for it to match in the first place),
# and a prune must never be treated as a declared removal (it has no
# `RemovalSpec` - it's keyed off the *source* no longer declaring something
# this tool itself put there).
# ---------------------------------------------------------------------------


class DeclareAndRemoveConflictError(ValueError):
    """Raised when one run's source/classes/* both declares and removes the
    exact same row - e.g. `scripted_by(200095, "x")` and
    `unbind_script(200095, "x")` in the same run. Contradictory by
    construction; there is no sensible "which one wins" answer, so this
    refuses rather than picking one silently."""


@dataclass(frozen=True)
class RemovalSpec:
    removal_key: str       # Registry field holding the removal declarations (see registry.py)
    table_name: str
    key_columns: tuple[str, ...]
    declared_key: str      # dsl_classes key this removal must not also declare - see DeclareAndRemoveConflictError
    why: str                # human-readable reason, quoted into the emitted comment/report


REMOVAL_TABLES = (
    RemovalSpec(
        "script_removals", "spell_script_names", ("spell_id", "ScriptName"),
        "spell_script_names", "a rework rebinds or retires this C++ script",
    ),
    RemovalSpec(
        "linked_spell_removals", "spell_linked_spell", ("spell_trigger", "spell_effect", "type"),
        "linked_spells", "a rework removes this linked-spell relationship",
    ),
    RemovalSpec(
        "spell_group_removals", "spell_group", ("id", "spell_id"),
        "spell_groups", "a rework removes this spell from the group",
    ),
    RemovalSpec(
        "trainer_removals", "trainer_spell", ("TrainerId", "SpellId"),
        "trainer_spells", "a rework retires this trainer grant",
    ),
    RemovalSpec(
        "spell_required_removals", "spell_required", ("spell_id", "req_spell"),
        "spell_required", "a rework retires this additional trainer spell requirement",
    ),
    RemovalSpec(
        "spell_rank_removals", "spell_ranks", ("spell_id",),
        "spell_ranks", "a rework collapses this rank chain to a single spell",
    ),
    RemovalSpec(
        "bonus_removals", "spell_bonus_data", ("entry",),
        "spell_bonus_data", "the spell switched to a generated potency coefficient",
    ),
    RemovalSpec(
        "proc_removals", "spell_proc", ("SpellId",),
        "spell_procs", "a rework retires this proc (zero the DBC ProcTypeMask too - see remove_spell_proc())",
    ),
)


def load_removed_keys(table_name: str, key_columns: tuple[str, ...]) -> set[tuple]:
    """Every key that is currently **net-removed** across every generated file mentioning
    `table_name` - the removal helpers' own "emitted once" provenance.

    A genuine replay (insert clears, matching-shape delete adds), not a bare scan for a DELETE
    with the right shape - that was this function's original design, and it was wrong (review,
    2026-09-23): a removal helper's key can be one *this same tool already declared and inserted*
    in an earlier run, before the declaration was later replaced by a removal (e.g.
    `trained_by(X, ...)` in one run, `untrain(X, ...)` after the design changed). That earlier
    run's own `render_generic_table_block` DELETE-then-INSERT (its normal idempotent-rerun shape)
    emits a DELETE with the *exact same* key-column shape a removal does, so scanning for "any
    matching-shape DELETE" misread that still-live row as already removed, and
    `render_removal_blocks` silently skipped emitting the real removal - see this module's
    "Declared removals" section. Tracking net effect (mirroring `load_generated_table_rows`'s own
    INSERT/DELETE replay, just the opposite quantity - which keys are net-*removed* rather than
    which rows are net-*live*) is what makes "declared, then inserted, then later removed" and
    "declared and removed in the same run without ever being inserted" both resolve correctly.

    Only a DELETE whose own column list is exactly `key_columns` counts as *this* removal
    provenance - the removal helpers always emit that exact shape (`sql_out.
    render_delete_only_block`), so a differently-shaped DELETE (e.g. the prune pass's own
    single-column-prefix output for the same table) is someone/something else's and is skipped,
    same as before. An unparsed DELETE shape drops the whole accumulated set for the table (return
    empty) rather than guess - symmetric with `load_generated_table_rows`'s own "shrink, never
    guess" posture: fewer keys read as "already removed" only means a future run re-emits a
    harmless, idempotent DELETE, never that a real removal silently never happens."""
    removed: set[tuple] = set()
    for path in trainer_state._migration_files_mentioning(table_name):
        if not _is_generated(path):
            continue
        try:
            for kind, payload in sql_dump.read_table_statements(path, table_name, ()):
                if kind == "insert":
                    for row in payload:
                        key = _row_key(row, key_columns)
                        if key is not None:
                            removed.discard(key)
                elif kind == "delete":
                    delete_cols, key_tuples = payload
                    if tuple(delete_cols) != tuple(key_columns):
                        continue
                    for values in key_tuples:
                        removed.add(tuple(_normalise(v) for v in values))
                else:  # delete_unparsed
                    print(
                        f"warning: spell_tables.py: {path} has a DELETE on {table_name} in a shape "
                        f"load_removed_keys doesn't understand; treating nothing in it as removed"
                    )
                    return set()
        except Exception as exc:  # pragma: no cover - defensive, cf. load_generated_table_rows
            print(f"warning: spell_tables.py: skipping {path} for {table_name} removals: {exc}")
    return removed


def _keys_of(rows: list[dict], key_columns: tuple[str, ...]) -> set[tuple]:
    return {tuple(_normalise(r[c]) for c in key_columns) for r in rows}


def _phases_by_key(table_name: str, key_columns: tuple[str, ...]) -> dict[tuple, list[int]]:
    """Which mod-progression phases INSERT each key of `table_name`, in phase
    order - every phase on disk, not just the active ones
    (`trainer_state.load_phase_table_rows`)."""
    phases: dict[tuple, list[int]] = {}
    for phase, rows in trainer_state.load_phase_table_rows(table_name).items():
        keyed = [r for r in rows if all(c in r for c in key_columns)]
        for key in _keys_of(keyed, key_columns):
            phases.setdefault(key, []).append(phase)
    return phases


def _phase_list(phases: list[int]) -> str:
    return ", ".join(f"phase_{p:02}" for p in phases)


def render_removal_blocks(
    dsl_classes: dict[str, list[dict]], live_keys_by_table: dict[str, set[tuple]] | None = None,
) -> tuple[list[str], list[str]]:
    """`(sql_blocks, report_lines)` for every declared removal in
    `REMOVAL_TABLES` - the counterpart to `render_blocks()`/
    `render_prune_blocks()` above for a row this tool never emitted itself.
    Every emitted key also gets a report line (never silent about a
    removal), a key with no match anywhere in the base dump/migrations/
    module SQL gets a `WARNING:` line (almost always a
    typo) but is still emitted - the DELETE is idempotent either way (it
    matches nothing, so it's a harmless no-op), and refusing outright would
    be worse than a false positive: the same key could legitimately have
    been removed already by an *older hand-written* migration that
    `trainer_state.load_table_rows` (a union of INSERTs, no DELETE replay -
    see its docstring) still reads as live. A key this same run also
    *declares* raises `DeclareAndRemoveConflictError` rather than silently
    picking a side.

    mod-progression phase SQL is applied after core `db_world` SQL, so a
    key some phase INSERTs (`_phases_by_key`, every phase on disk) doesn't
    stay removed: a phase above `Progression.Phase` gets its own `WARNING:`
    in place of the typo one (the row isn't live *yet*, and comes back when
    the realm reaches that phase), and an already-applied phase gets a
    `note:` (only a fresh world DB gets the row back). Nothing here can fix
    that ordering - see README.md's "Removing a row mod-progression's phase
    SQL inserts".

    `live_keys_by_table` (optional): `{table_name: {key tuples}}` for tables the caller already
    scanned elsewhere - `generate.py` passes `SpellTableIndex.live_keys()` for the three
    `REMOVAL_TABLES` entries that are also `SPELL_TABLES` (`spell_script_names`,
    `spell_linked_spell`, `spell_group`) plus `TrainerIndex.existing_trainer_spells`'s own keys
    for `trainer_spell`, so this doesn't re-scan the base dump + every migration a second time per
    table on every run (review, 2026-09-23). Falls back to a fresh `trainer_state.load_table_rows`
    scan per table (the original behavior, still covers module SQL - including mod-progression's
    phase files - via `_migration_files_mentioning`) for any table not present in the map, so this
    still works standalone (e.g. in tests) with no caller-side plumbing required."""
    blocks: list[str] = []
    report: list[str] = []
    for spec in REMOVAL_TABLES:
        removals = dsl_classes.get(spec.removal_key, [])
        if not removals:
            continue
        removal_keys = _keys_of(removals, spec.key_columns)
        declared_keys = _keys_of(dsl_classes.get(spec.declared_key, []), spec.key_columns)
        conflict = removal_keys & declared_keys
        if conflict:
            texts = ", ".join(_key_text(spec.key_columns, k) for k in sorted(conflict, key=repr))
            raise DeclareAndRemoveConflictError(
                f"{spec.table_name}: this run both declares and removes the same row(s): {texts}"
            )
        if live_keys_by_table is not None and spec.table_name in live_keys_by_table:
            live_keys = live_keys_by_table[spec.table_name]
        else:
            live_keys = _keys_of(
                [r for r in trainer_state.load_table_rows(spec.table_name) if all(c in r for c in spec.key_columns)],
                spec.key_columns,
            )
        already_removed = load_removed_keys(spec.table_name, spec.key_columns)
        to_emit = sql_out.stable_key_sort(removal_keys - already_removed)
        if not to_emit:
            continue
        active_phase = trainer_state.progression_phase()
        phases_by_key = _phases_by_key(spec.table_name, spec.key_columns)
        for key in to_emit:
            key_text = _key_text(spec.key_columns, key)
            phases = phases_by_key.get(key, [])
            later = [p for p in phases if p > active_phase]
            applied = [p for p in phases if p <= active_phase]
            if later:
                report.append(
                    f"WARNING: {spec.table_name} removal {key_text} is inserted by mod-progression "
                    f"{_phase_list(later)}, which this realm hasn't applied yet (Progression.Phase = "
                    f"{active_phase}) - the DELETE matches nothing now and the row comes back when the "
                    f"realm reaches phase {later[0]}. Not a typo; see README's removal section."
                )
            elif key not in live_keys:
                report.append(
                    f"WARNING: {spec.table_name} removal {key_text} doesn't exist anywhere (base "
                    f"dump, migrations, module SQL, any mod-progression phase) - check for a typo."
                )
            if applied:
                report.append(
                    f"note: {spec.table_name} removal {key_text} is also inserted by mod-progression "
                    f"{_phase_list(applied)} - a fresh world DB applies this DELETE before phase SQL "
                    f"and gets the row back; a realm already past that phase keeps the removal."
                )
        for key in to_emit:
            report.append(f"removal: {spec.table_name} {_key_text(spec.key_columns, key)} - {spec.why}")
        comment = (
            f"-- Declared removal: {len(to_emit)} {spec.table_name} row(s) no longer wanted - "
            f"{spec.why} (unbind_script()/unlink_spell()/leave_spell_group()/untrain()/"
            f"unbind_bonus_coefficients()/remove_spell_proc(), source/classes/*)."
        )
        blocks.append(sql_out.render_delete_only_block(spec.table_name, spec.key_columns, to_emit, comment))
    return blocks, report
