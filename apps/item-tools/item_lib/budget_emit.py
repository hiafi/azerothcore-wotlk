"""
Writes shape-based itemization edits as new `data/sql/updates/pending_db_world/
rev_<ns>.sql` files - the DELETE+INSERT idiom (`.agents/docs/sql-guidelines.md`:
"every INSERT preceded by a matching DELETE"), not `lib.emit`'s guarded-UPDATE
idiom, since `item_itemization` isn't on `codestyle-sql.py`'s `not_delete`
list the way `item_template` is. See `lib/budget_overlay.py`'s module
docstring for the reading half of this convention.

Unlike the old percentage-allocation system, there's no template/shape
authoring here at all - primary and secondary shapes are a fixed catalog
(`item_shape`/`item_shape_stat`/`item_shape_rule`/`item_alloc_dist`), edited
by hand-written migrations, not through this tool (see `lib/shapes.py`'s
module docstring). This module only ever writes one item's own
`item_itemization` row.

`item_template` itself (the regenerated stat/armor/block columns, and
spell-slot clearing for an absorbed spell) still goes through `lib.emit`'s
guarded UPDATE - reused here, not reimplemented - since that table's rules
are unchanged by any of this.
"""

from __future__ import annotations

from .emit import _guard_term, _new_pending_path, _quote_value, _wrap_comment

ITEMIZATION_COLUMNS = (
    "entry", "budget_mult", "stamina_delta", "dps_delta", "absorbed_spell_slots",
    "armor_delta", "primary_shape_id", "secondary_shape_id", "primary_share",
    "block_value_delta",
)


def _delete_insert_row(table: str, pk_column: str, row: dict) -> list[str]:
    """`DELETE FROM \\`table\\` WHERE \\`pk_column\\` = N; INSERT INTO
    \\`table\\` (...) VALUES (...);` for one row - the single-row case of the
    `lib.budget_overlay`-readable DELETE+INSERT convention."""
    col_list = ", ".join(f"`{c}`" for c in row)
    values = ", ".join(_quote_value(v) for v in row.values())
    return [
        f"DELETE FROM `{table}` WHERE `{pk_column}` = {row[pk_column]};",
        f"INSERT INTO `{table}` ({col_list}) VALUES ({values});",
    ]


def _update_statement(table: str, pk_column: str, pk_value, changes: dict, original: dict) -> str:
    """One guarded `UPDATE` statement, same shape as `lib.emit.write_update`
    builds - factored out here so a combined save (itemization row +
    regenerated item_template stats) can put it in the same file."""
    set_clause = ", ".join(f"`{col}` = {_quote_value(val)}" for col, val in changes.items())
    guard_clause = " AND ".join(_guard_term(col, original[col]) for col in changes)
    return f"UPDATE `{table}` SET {set_clause} WHERE `{pk_column}` = {pk_value} AND {guard_clause};"


def write_itemization_and_regenerate(entry: int, itemization_fields: dict, item_changes: dict,
                                      item_original: dict, comment: str):
    """One pending file: the `item_itemization` DELETE+INSERT, plus a guarded
    `item_template` UPDATE for whichever stat/armor/block columns the
    regenerated breakdown actually changed (`item_changes` empty means the
    item's materialized stats didn't change - e.g. only `budget_mult` was
    edited and it happened not to move any rounded value - in which case
    that block is omitted). `itemization_fields` must have every
    `item_itemization` column (see `ITEMIZATION_COLUMNS`)."""
    lines = _wrap_comment(comment)
    lines.append("")
    lines.extend(_delete_insert_row("item_itemization", "entry", itemization_fields))
    if item_changes:
        lines.append("")
        lines.append(_update_statement("item_template", "entry", entry, item_changes, item_original))
    path = _new_pending_path()
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
