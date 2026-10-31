"""
Stale overlay rows: rows an earlier `generate.py` run wrote into a DBC overlay table (`spell_dbc`, `talent_dbc`,
`talenttab_dbc`, `skilllineability_dbc`, `item_dbc`) that this run no longer wants, but would otherwise leave live.

`resolve.resolve_rows` decides what to emit by comparing each declared row with `state.load_existing_rows`, which is
the stock DBC plus the base dump plus the *promoted* (`db_world/`) migrations only. A row an earlier run wrote into a
still-pending migration is invisible to it. So when a declaration goes back to its stock values before that pending
file is promoted (the Shockwave case: talent 1872 moved to (10, 0) in one run, back to its stock (10, 1) in a later
one), the declared row equals "existing", reads as an unchanged reference copy, and nothing is emitted: no INSERT and
no DELETE. The overlay row from the earlier run stays live, and the server keeps reading it over the stock DBC (see
docs/bugs-and-fixes.md, "A talent moved back to its stock cell keeps the old position on the server").

This module replays the overlay table the way the server sees it (base dump, then every promoted, pending and module
migration in apply order) and records which ids a generated file wrote last. `find_stale` then compares those rows
with what this run declares:

- **Outside the reserved block, declared, live row differs from the declared row**: if the declared row equals the
  stock row and the base dump has no row for the id, the overlay row is removed (`deletes`; the server falls back to
  the stock DBC row). Otherwise the declared row is re-emitted as an edit (`reemit`). A row `resolve_rows` already
  marked as an edit is handled the same way when its declared row equals stock (`drop`, see `find_stale`).
- **Outside the reserved block, no longer declared**: the row is removed when the stock DBC still has the id and the
  base dump does not (`deletes`), which returns it to stock. A custom id with no stock row, or one the base dump also
  has, is only reported (`kept_undeclared`), because deleting it would drop the whole row rather than restore stock.
- **Inside the reserved block**: the block is a `DELETE ... BETWEEN` plus a full re-insert, so any difference (a row
  changed or no longer declared) only needs the block to be emitted (`reserved_changed`).

Provenance is the same as the prune pass's (`spell_tables.GENERATED_MARKER`): only a row a generated file wrote last
is ours to touch. A hand-written or module statement that writes the id afterwards (an INSERT, an UPDATE, or a DELETE
such as the Shockwave fix) takes it out of the set, so a hand fix is never reverted and a removal is emitted once.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import sql_dump, sqlcorpus, trainer_state
from .dbcfmt import DbcTable
from .resolve import _rows_equal
from .spell_tables import _is_generated


class _Recorder:
    """The three dict operations `sql_dump.apply_statements` uses (`rows[k] = row`, `rows.pop`, `rows.get`), passed
    through to `rows`, with every existing or written key noted in `touched`. `get` counts because an UPDATE edits the
    row it returns in place."""

    def __init__(self, rows: dict[int, dict]):
        self.rows = rows
        self.touched: set[int] = set()

    def __setitem__(self, key, value) -> None:
        self.touched.add(key)
        self.rows[key] = value

    def pop(self, key, default=None):
        if key in self.rows:
            self.touched.add(key)
        return self.rows.pop(key, default)

    def get(self, key, default=None):
        if key in self.rows:
            self.touched.add(key)
        return self.rows.get(key, default)


@dataclass
class OverlayState:
    rows: dict[int, dict] = field(default_factory=dict)  # the overlay table as the server loads it
    generated: set[int] = field(default_factory=set)  # ids whose current row a generated file wrote last
    base_ids: set[int] = field(default_factory=set)  # ids the base dump has


def apply_file(state: OverlayState, table: DbcTable, text: str, generated: bool) -> OverlayState:
    """Replays one migration's statements on `table` and updates the provenance of every id it touched."""
    recorder = _Recorder(state.rows)
    sql_dump.apply_statements(recorder, table, text)
    for key in recorder.touched:
        if generated and key in state.rows:
            state.generated.add(key)
        else:
            state.generated.discard(key)
    return state


def load_overlay_state(table: DbcTable) -> OverlayState:
    """`table`'s overlay rows after the base dump and every migration (promoted, pending, module), with provenance."""
    base_path = trainer_state.BASE_SQL_DIR / f"{table.sql_table}.sql"
    stable, volatile = trainer_state._split_stable(trainer_state._migration_files_mentioning(table.sql_table))

    def step(state: OverlayState, path: Path) -> OverlayState:
        if path == base_path:
            state.rows.update(sql_dump.read_table_dump(base_path, table))
            state.base_ids.update(state.rows)
            return state
        return apply_file(state, table, sqlcorpus.read_text(path), _is_generated(path))

    head = [base_path] if base_path.is_file() else []
    state = sqlcorpus.checkpointed(
        "overlay_provenance", (table.name, table.sql_table), head + stable, OverlayState, step,
    )
    for path in volatile:
        step(state, path)
    return state


@dataclass
class Stale:
    deletes: list[int] = field(default_factory=list)  # overlay rows to DELETE with nothing in their place
    undeclared: list[int] = field(default_factory=list)  # the part of `deletes` no longer declared at all
    reemit: list[int] = field(default_factory=list)  # declared ids to emit as edits (DELETE IN + INSERT)
    drop: list[int] = field(default_factory=list)  # emitted ids at stock values: no INSERT (a delete, or nothing)
    reserved_changed: bool = False  # the reserved block's live content differs from this run's rows
    kept_undeclared: list[int] = field(default_factory=list)  # undeclared generated rows left live (no stock row)


def find_stale(
    id_range: dict, declared: dict[int, dict], emitted_ids: set[int], overlay: OverlayState,
    stock_rows: dict[int, dict], prune: bool = True,
) -> Stale:
    """See the module docstring. `declared` is every declared row of the table, built (in and out of the reserved
    block); `emitted_ids` the out-of-block ids `resolve.resolve_rows` already marked as edits; `stock_rows` the stock
    DBC plus base dump (`state.load_stock_rows`).

    An emitted id whose declared row equals stock is not re-inserted (`drop`): the overlay row is deleted when a
    generated file wrote it (`deletes`), and nothing is written when there is no overlay row (the server already
    reads the stock DBC row; `state.load_existing_rows` replays a DELETE as removing the DBC row too, which is how
    such an id reads as edited). A stock-valued declaration over a hand-written or module row stays an edit.

    `prune=False` (generate.py --no-prune): an undeclared generated row is never deleted, it is reported in
    `kept_undeclared`. Declared rows back at stock are still deleted, since that follows the declarations."""
    result = Stale()

    def at_stock(row_id: int, want: dict) -> bool:
        stock = stock_rows.get(row_id)
        return row_id not in overlay.base_ids and stock is not None and _rows_equal(want, stock)

    for row_id in sorted(emitted_ids):
        want = declared.get(row_id)
        if want is None or not at_stock(row_id, want):
            continue
        if row_id not in overlay.rows:
            result.drop.append(row_id)
        elif row_id in overlay.generated:
            result.drop.append(row_id)
            result.deletes.append(row_id)
    for row_id in sorted(overlay.generated):
        live = overlay.rows.get(row_id)
        if live is None:
            continue
        want = declared.get(row_id)
        if id_range["start"] <= row_id <= id_range["end"]:
            if want is None or not _rows_equal(want, live):
                result.reserved_changed = True
            continue
        if row_id in emitted_ids:
            continue
        if want is None:
            if prune and row_id not in overlay.base_ids and stock_rows.get(row_id) is not None:
                result.deletes.append(row_id)
                result.undeclared.append(row_id)
            else:
                result.kept_undeclared.append(row_id)
        elif not _rows_equal(want, live):
            if at_stock(row_id, want):
                result.deletes.append(row_id)
            else:
                result.reemit.append(row_id)
    result.deletes.sort()
    return result
