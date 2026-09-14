"""
Emits a pending world-DB SQL migration for the rows this run produced.

Two DELETE shapes, per touched table, both idempotent on rerun:
  - `WHERE ID BETWEEN <reserved block>` for our reserved range — mirrors the
    idiom already used by the custom stat system's own migration, originally
    `rev_1787377390451498201.sql`, now folded into the merged custom-stat
    migration `custom_stats.sql`.
  - `WHERE ID IN (...)` for specific existing IDs this run is *editing*
    (see lib/resolve.py) — scattered, not contiguous, so a range delete
    would either miss them or (worse) sweep up unrelated rows.
Then one sorted INSERT per table covering everything (new content and
edits alike).
"""

from __future__ import annotations

from .dbcfmt import DbcTable


def _sql_literal(value) -> str:
    if value is None or value == "":
        return "NULL"
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, int):
        return str(value)
    escaped = str(value).replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def _table_block(table: DbcTable, id_range: dict, rows: list[dict], edited_ids: list[int]) -> str:
    lines = [
        f"DELETE FROM `{table.sql_table}` WHERE `{table.index_column}` "
        f"BETWEEN {id_range['start']} AND {id_range['end']};"
    ]
    if edited_ids:
        id_list = ", ".join(str(i) for i in sorted(edited_ids))
        lines.append(
            f"DELETE FROM `{table.sql_table}` WHERE `{table.index_column}` IN ({id_list});"
        )
    if rows:
        rows = sorted(rows, key=lambda r: r[table.index_column])
        cols = ", ".join(f"`{c}`" for c in table.columns)
        tuples = ",\n".join(
            "(" + ", ".join(_sql_literal(row.get(c)) for c in table.columns) + ")"
            for row in rows
        )
        lines.append(f"INSERT INTO `{table.sql_table}` ({cols}) VALUES\n{tuples};")
    return "\n".join(lines)


def render_generic_table_block(
    table_name: str, columns: tuple[str, ...], key_columns: tuple[str, ...], rows: list[dict]
) -> str:
    """Same idempotent-on-rerun DELETE-then-INSERT shape as `_table_block`,
    but for a plain world-DB table with no single-int reserved-ID range to
    range-delete — e.g. `trainer_spell`, keyed on `(TrainerId, SpellId)`
    (Phase 3 of `.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md`,
    `lib/dsl/registry.py`'s `trained_by()`). Deletes exactly `rows`' own key
    tuples — never a range, since a `TrainerId` isn't a reserved block the
    way a minted spell/talent ID is; it names one already-existing class
    trainer. Returns `""` for an empty `rows` (nothing to emit)."""
    if not rows:
        return ""
    rows = sorted(rows, key=lambda r: tuple(r[c] for c in key_columns))
    key_cols_sql = ", ".join(f"`{c}`" for c in key_columns)
    key_tuples = ", ".join(
        "(" + ", ".join(_sql_literal(row[c]) for c in key_columns) + ")" for row in rows
    )
    cols_sql = ", ".join(f"`{c}`" for c in columns)
    tuples = ",\n".join(
        "(" + ", ".join(_sql_literal(row.get(c)) for c in columns) + ")" for row in rows
    )
    return (
        f"DELETE FROM `{table_name}` WHERE ({key_cols_sql}) IN ({key_tuples});\n"
        f"INSERT INTO `{table_name}` ({cols_sql}) VALUES\n{tuples};"
    )


def emit_pending_sql(
    output_path,
    blocks: list[tuple[DbcTable, dict, list[dict], list[int]]],
    header: str,
    extra_blocks: list[str] | None = None,
) -> bool:
    """`blocks` is a list of (table, id_range, rows, edited_ids). `extra_blocks`
    is pre-rendered SQL text (e.g. from `render_generic_table_block`) for
    tables that don't fit that shape — appended after the per-table blocks,
    in the order given. Writes nothing and returns False if everything is
    empty (nothing new/changed to emit)."""
    extra_blocks = [b for b in (extra_blocks or []) if b]
    if not any(rows for _, _, rows, _ in blocks) and not extra_blocks:
        return False
    # Note: no extra "\n" here — the "\n\n".join below already inserts one
    # blank line between the header and the first block; adding another
    # would leave two (codestyle-sql.py's "no multiple blank lines" rule).
    parts = [header.rstrip()]
    for table, id_range, rows, edited_ids in blocks:
        parts.append(_table_block(table, id_range, rows, edited_ids))
    parts.extend(extra_blocks)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    return True
