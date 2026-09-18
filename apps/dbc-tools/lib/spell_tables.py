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

from dataclasses import dataclass

from . import sql_out, trainer_state

# Column tuples mirror each table's CREATE TABLE in data/sql/base/db_world/,
# minus the synthetic "id" the registry adds for duplicate-declaration
# bookkeeping (see Registry's docstring).
SPELL_SCRIPT_NAMES_COLUMNS = ("spell_id", "ScriptName")
SPELL_BONUS_DATA_COLUMNS = ("entry", "direct_bonus", "dot_bonus", "ap_bonus", "ap_dot_bonus", "comments")
SPELL_PROC_COLUMNS = (
    "SpellId", "SchoolMask", "SpellFamilyName", "SpellFamilyMask0", "SpellFamilyMask1",
    "SpellFamilyMask2", "ProcFlags", "SpellTypeMask", "SpellPhaseMask", "HitMask",
    "AttributesMask", "DisableEffectsMask", "ProcsPerMinute", "Chance", "Cooldown", "Charges",
)


@dataclass(frozen=True)
class TableSpec:
    name: str
    columns: tuple[str, ...]
    key_columns: tuple[str, ...]
    registry_key: str  # the lib.dsl.registry.Registry attribute holding declared rows


SPELL_TABLES = (
    TableSpec("spell_script_names", SPELL_SCRIPT_NAMES_COLUMNS, ("spell_id", "ScriptName"), "spell_script_names"),
    TableSpec("spell_bonus_data", SPELL_BONUS_DATA_COLUMNS, ("entry",), "spell_bonus_data"),
    TableSpec("spell_proc", SPELL_PROC_COLUMNS, ("SpellId",), "spell_procs"),
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


def _same_row(existing: dict, declared: dict, columns: tuple[str, ...]) -> bool:
    """A column a hand-written migration left out entirely took the table's
    DEFAULT - `0` for every numeric column in these three tables, `NULL` for
    the one text column (`spell_bonus_data.comments`) - so a missing key on
    the live side compares as that default, not as "unknown"."""
    for c in columns:
        default = 0 if isinstance(declared.get(c), (int, float)) else None
        if _normalise(existing.get(c, default)) != _normalise(declared.get(c)):
            return False
    return True


class SpellTableIndex:
    """Live rows for each of `SPELL_TABLES`, keyed by that table's key
    tuple - built once per `generate.py` run (each table means re-parsing
    every migration that mentions it)."""

    def __init__(self, existing: dict[str, list[dict]]):
        self._by_key: dict[str, dict[tuple, dict]] = {}
        for spec in SPELL_TABLES:
            keyed: dict[tuple, dict] = {}
            for row in existing.get(spec.name, []):
                try:
                    key = tuple(_normalise(row[c]) for c in spec.key_columns)
                except KeyError:
                    continue  # a migration that inserted a partial column set can't be keyed
                keyed[key] = row  # later migrations win - files are scanned in sorted order
            self._by_key[spec.name] = keyed

    def rows_to_emit(self, spec: TableSpec, declared: list[dict]) -> list[dict]:
        """`declared` minus anything already live with identical values."""
        keyed = self._by_key.get(spec.name, {})
        out = []
        for row in declared:
            key = tuple(_normalise(row[c]) for c in spec.key_columns)
            existing = keyed.get(key)
            if existing is not None and _same_row(existing, row, spec.columns):
                continue
            out.append(row)
        return out


def load_spell_table_index() -> SpellTableIndex:
    return SpellTableIndex({spec.name: trainer_state.load_table_rows(spec.name) for spec in SPELL_TABLES})


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


def count_declared(dsl_classes: dict[str, list[dict]]) -> dict[str, int]:
    return {spec.name: len(dsl_classes.get(spec.registry_key, [])) for spec in SPELL_TABLES}
