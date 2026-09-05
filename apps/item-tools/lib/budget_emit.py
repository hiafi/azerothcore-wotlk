"""
Writes budget-system edits as new `data/sql/updates/pending_db_world/
rev_<ns>.sql` files - the DELETE+INSERT idiom (`.agents/docs/sql-guidelines.md`:
"every INSERT preceded by a matching DELETE"), not `lib.emit`'s guarded-UPDATE
idiom, since none of `item_budget_template`/`item_budget_template_name`/
`item_budget_assign` are on `codestyle-sql.py`'s `not_delete` list the way
`item_template` is. See `lib/budget_overlay.py`'s module docstring for the
reading half of this convention.

`item_template` itself (the regenerated stat/armor columns, and spell-slot
clearing for an absorbed spell) still goes through `lib.emit`'s guarded
UPDATE - reused here, not reimplemented - since that table's rules are
unchanged by any of this.
"""

from __future__ import annotations

from .emit import _guard_term, _new_pending_path, _quote_value, _wrap_comment


def _delete_insert_block(table: str, key_columns: tuple[str, ...], rows: list[dict]) -> list[str]:
    """`DELETE FROM \\`table\\` WHERE ...; INSERT INTO \\`table\\` (...)
    VALUES (...), ...;` for a full replace of every row in `rows` (each a
    `{column: value}` dict with the same keys). `rows` must be non-empty.
    The DELETE's WHERE always uses `IN (...)` over the key columns' values -
    one of the three shapes `lib.budget_overlay` knows how to read back."""
    if not rows:
        raise ValueError("no rows to write")

    if len(key_columns) == 1:
        col = key_columns[0]
        values = sorted({row[col] for row in rows})
        # Wrapped across lines (15/line, same convention as this session's other
        # bulk generators) once the single-line form would blow the 120-col
        # limit -- lib.budget_overlay's DELETE regex is re.DOTALL and int()
        # strips whitespace/newlines, so a wrapped IN(...) reads back identically.
        joined = ', '.join(str(v) for v in values)
        if len(joined) <= 100:
            where = f"`{col}` IN ({joined})"
        else:
            chunks = [', '.join(str(v) for v in values[i:i + 15]) for i in range(0, len(values), 15)]
            where = f"`{col}` IN (\n  " + ",\n  ".join(chunks) + "\n)"
    else:
        # Composite key (item_budget_template's (template_id, stat_type)):
        # every row here shares the same template_id in practice (one
        # template edited at a time), so delete the whole template_id's
        # rows rather than trying to express a composite IN(...) - simpler,
        # and correct as long as callers only ever pass rows for one
        # template_id per call (true for write_template below).
        first_col = key_columns[0]
        values = sorted({row[first_col] for row in rows})
        if len(values) != 1:
            raise ValueError(f"_delete_insert_block: rows span multiple {first_col} values: {values}")
        where = f"`{first_col}` = {values[0]}"

    cols = list(rows[0].keys())
    col_list = ", ".join(f"`{c}`" for c in cols)
    value_lines = ",\n".join(
        "(" + ", ".join(_quote_value(row[c]) for c in cols) + ")"
        for row in rows
    )

    return [
        f"DELETE FROM `{table}` WHERE {where};",
        f"INSERT INTO `{table}` ({col_list}) VALUES",
        value_lines + ";",
    ]


def _update_statement(table: str, pk_column: str, pk_value, changes: dict, original: dict) -> str:
    """One guarded `UPDATE` statement, same shape as `lib.emit.write_update`
    builds - factored out here so a combined save (assign + regenerated
    item_template stats) can put it in the same file as the DELETE+INSERT
    blocks above, instead of `lib.emit.write_update`'s own file write."""
    set_clause = ", ".join(f"`{col}` = {_quote_value(val)}" for col, val in changes.items())
    guard_clause = " AND ".join(_guard_term(col, original[col]) for col in changes)
    return f"UPDATE `{table}` SET {set_clause} WHERE `{pk_column}` = {pk_value} AND {guard_clause};"


def write_template(template_id: int, name: str, stats: list[dict], comment: str):
    """`stats` is a list of `{stat_type, alloc}` (ten-thousandths, already
    summing to 10000 - the caller/route validates that, not this)."""
    template_rows = [{"template_id": template_id, "stat_type": s["stat_type"], "alloc": s["alloc"]} for s in stats]
    name_rows = [{"template_id": template_id, "name": name}]

    lines = _wrap_comment(comment)
    lines.append("")
    lines.extend(_delete_insert_block("item_budget_template", ("template_id", "stat_type"), template_rows))
    lines.append("")
    lines.extend(_delete_insert_block("item_budget_template_name", ("template_id",), name_rows))

    path = _new_pending_path()
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_assign(entry: int, assign_fields: dict, comment: str):
    """`assign_fields` must have every `item_budget_assign` column
    (`entry`/`template_id`/`budget_mult`/`stamina_delta`/`dps_delta`/
    `absorbed_spell_slots`/`armor_delta`)."""
    lines = _wrap_comment(comment)
    lines.append("")
    lines.extend(_delete_insert_block("item_budget_assign", ("entry",), [assign_fields]))
    path = _new_pending_path()
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_assign_and_regenerate(entry: int, assign_fields: dict, item_changes: dict, item_original: dict, comment: str,
                                 template: tuple[int, str, list[dict]] | None = None):
    """One pending file: optionally the template's own DELETE+INSERT
    (`template` = `(template_id, name, stats)`, when the item page's inline
    shape editor changed a template exclusively owned by this one item, or
    is defining a brand new one - see `webui/app.py`'s `item_budget_save`),
    the `item_budget_assign` DELETE+INSERT, and a guarded `item_template`
    UPDATE for whichever stat/armor columns the regenerated breakdown
    actually changed (`item_changes` empty means the item's materialized
    stats didn't change - e.g. only `budget_mult` was edited and it happened
    not to move any rounded value - in which case that block is omitted)."""
    lines = _wrap_comment(comment)

    if template is not None:
        template_id, name, stats = template
        template_rows = [{"template_id": template_id, "stat_type": s["stat_type"], "alloc": s["alloc"]} for s in stats]
        name_rows = [{"template_id": template_id, "name": name}]
        lines.append("")
        lines.extend(_delete_insert_block("item_budget_template", ("template_id", "stat_type"), template_rows))
        lines.append("")
        lines.extend(_delete_insert_block("item_budget_template_name", ("template_id",), name_rows))

    lines.append("")
    lines.extend(_delete_insert_block("item_budget_assign", ("entry",), [assign_fields]))
    if item_changes:
        lines.append("")
        lines.append(_update_statement("item_template", "entry", entry, item_changes, item_original))
    path = _new_pending_path()
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_regenerate_many(entries_changes: list[tuple[int, dict, dict]], comment: str):
    """One pending file with one guarded `item_template` UPDATE per
    `(entry, changes, original)` - used when a template edit regenerates
    every item currently assigned to it. Entries with no actual change are
    skipped. Returns None (writes nothing) if every entry was a no-op."""
    statements = [
        _update_statement("item_template", "entry", entry, changes, original)
        for entry, changes, original in entries_changes
        if changes
    ]
    if not statements:
        return None
    lines = _wrap_comment(comment)
    lines.append("")
    lines.extend(statements)
    path = _new_pending_path()
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
