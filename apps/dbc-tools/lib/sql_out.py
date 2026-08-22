"""
Emits a pending world-DB SQL migration for the rows this run produced —
`DELETE ... WHERE ID BETWEEN <reserved block>` followed by a sorted
`INSERT`, one pair per touched table. Mirrors the idiom already used by
`data/sql/updates/pending_db_world/rev_1787377390451498201.sql` (the custom
stat system's own migration): delete-then-insert over a fixed reserved
range makes reruns idempotent, since the DELETE always clears exactly the
block this tool owns before reinserting the current rows.
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


def _table_block(table: DbcTable, id_range: dict, rows: list[dict]) -> str:
    lines = [
        f"DELETE FROM `{table.sql_table}` WHERE `{table.index_column}` "
        f"BETWEEN {id_range['start']} AND {id_range['end']};"
    ]
    if rows:
        rows = sorted(rows, key=lambda r: r[table.index_column])
        cols = ", ".join(f"`{c}`" for c in table.columns)
        tuples = ",\n".join(
            "(" + ", ".join(_sql_literal(row.get(c)) for c in table.columns) + ")"
            for row in rows
        )
        lines.append(f"INSERT INTO `{table.sql_table}` ({cols}) VALUES\n{tuples};")
    return "\n".join(lines)


def emit_pending_sql(output_path, blocks: list[tuple[DbcTable, dict, list[dict]]], header: str) -> bool:
    """`blocks` is a list of (table, id_range, rows). Writes nothing and
    returns False if every block is empty (nothing new/changed to emit)."""
    if not any(rows for _, _, rows in blocks):
        return False
    parts = [header.rstrip() + "\n"]
    for table, id_range, rows in blocks:
        parts.append(_table_block(table, id_range, rows))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    return True
