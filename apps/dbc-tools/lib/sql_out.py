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


def emit_pending_sql(output_path, blocks: list[tuple[DbcTable, dict, list[dict], list[int]]], header: str) -> bool:
    """`blocks` is a list of (table, id_range, rows, edited_ids). Writes
    nothing and returns False if every block is empty (nothing new/changed
    to emit)."""
    if not any(rows for _, _, rows, _ in blocks):
        return False
    # Note: no extra "\n" here — the "\n\n".join below already inserts one
    # blank line between the header and the first block; adding another
    # would leave two (codestyle-sql.py's "no multiple blank lines" rule).
    parts = [header.rstrip()]
    for table, id_range, rows, edited_ids in blocks:
        parts.append(_table_block(table, id_range, rows, edited_ids))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    return True
