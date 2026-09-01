"""
Writes an edit to `item_template` as a new `data/sql/updates/pending_db_world/
rev_<ns>.sql` file, following the two conventions already established by hand
in this repo's history for tables on `apps/codestyle/codestyle-sql.py`'s
`not_delete` list (`item_template` among them - see the Conjure Refreshment
item-level edit and the `npc_mage_frozen_orb` upsert inside
data/sql/updates/pending_db_world/frost_mage_rework.sql, the merged
Frost Mage rework migration - originally rev_1787824212353499531.sql and
rev_1787563173168071680.sql respectively):

  - **Editing an existing row**: a plain `UPDATE` per save, guarded by the old
    value of every column being changed (WHERE entry = N AND col = <old value>
    AND ...) so replaying an already-applied file a second time is a no-op
    instead of an error.
  - **A brand-new row**: an INSERT with an ON DUPLICATE KEY UPDATE clause -
    an upsert, which is both idempotent and never needs a `DELETE` (the
    `creature_template`/`npc_mage_frozen_orb` precedent, originally
    rev_1787563173168071680.sql, now inside the merged Frost Mage rework
    migration frost_mage_rework.sql).
"""

from __future__ import annotations

import time
from pathlib import Path

from . import overlay

_MAX_COMMENT_WIDTH = 118  # 120-col limit minus "-- "


def _quote_value(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    escaped = str(value).replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def _wrap_comment(text: str) -> list[str]:
    """Wrap `text` into `-- `-prefixed lines at `_MAX_COMMENT_WIDTH`, the
    same 120-col limit `.editorconfig` sets for the rest of the repo."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > _MAX_COMMENT_WIDTH and current:
            lines.append(f"-- {current}")
            current = word
        else:
            current = candidate
    if current:
        lines.append(f"-- {current}")
    return lines


def _new_pending_path() -> Path:
    # Read overlay.PENDING_DIR at call time (not imported by value at module
    # load) so redirecting it - e.g. a test pointing it at a scratch dir -
    # actually takes effect here too, not just in overlay.py's own reads.
    overlay.PENDING_DIR.mkdir(parents=True, exist_ok=True)
    return overlay.PENDING_DIR / f"rev_{time.time_ns()}.sql"


def diff_row(original: dict, edited: dict) -> dict:
    """Columns present in both dicts whose value actually changed."""
    return {
        col: edited[col]
        for col in edited
        if col in original and edited[col] != original[col]
    }


def write_update(entry: int, changes: dict, original: dict, comment: str) -> Path:
    """`changes` is `{column: new value}` for an edit to an existing row;
    `original` supplies the guard (old) values for those same columns."""
    if not changes:
        raise ValueError("no changed columns to write")
    set_clause = ", ".join(f"`{col}` = {_quote_value(val)}" for col, val in changes.items())
    guard_clause = " AND ".join(
        f"`{col}` = {_quote_value(original[col])}" for col in changes
    )
    stmt = (
        f"UPDATE `item_template` SET {set_clause} "
        f"WHERE `entry` = {entry} AND {guard_clause};"
    )
    lines = _wrap_comment(comment) + [stmt]
    path = _new_pending_path()
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_insert(entry: int, values: dict, comment: str) -> Path:
    """`values` must be a full `item_template` row (every column present -
    see `lib/overlay.item_columns()` for the required set/order)."""
    cols = list(values.keys())
    col_list = ", ".join(f"`{c}`" for c in cols)
    val_list = ", ".join(_quote_value(values[c]) for c in cols)
    upsert_list = ", ".join(f"`{c}` = VALUES(`{c}`)" for c in cols if c != "entry")
    stmt = (
        f"INSERT INTO `item_template` ({col_list}) VALUES\n"
        f"({val_list}) ON DUPLICATE KEY UPDATE {upsert_list};"
    )
    lines = _wrap_comment(comment) + [
        "-- No DELETE here - item_template is on this repo's SQL linter's do-not-delete list, and "
        "this is a first-time",
        "-- insert, not an edit to an existing row, so there's no matching UPDATE...WHERE to fall "
        "back on either. An",
        "-- upsert is both idempotent and never deletes.",
        stmt,
    ]
    path = _new_pending_path()
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
