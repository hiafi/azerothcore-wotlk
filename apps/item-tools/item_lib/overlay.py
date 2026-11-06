"""
Resolves "what `item_template` looks like right now": the base client dump
(`data/sql/base/db_world/item_template.sql`) with every SQL file that touches
`item_template` replayed on top in apply order - promoted migrations (with
their subdirectories, e.g. `itemization_templates_v2/`), the frozen
mod-progression phase 0 at the slot it ran, pending migrations, then module
SQL. See `lib/replay.py` for the file order and the parser: it is dbc-tools'
(`apps/dbc-tools/lib/sql_dump.py`), shared rather than copied.

`item_template` is on `apps/codestyle/codestyle-sql.py`'s `not_delete` list,
so its migrations are guarded `UPDATE ... WHERE entry = N AND col = <old>`
statements or `INSERT ... ON DUPLICATE KEY UPDATE` upserts (`lib/emit.py`
writes both). The replay evaluates a guard the way MySQL does: an UPDATE
whose guard no longer holds changes nothing (a `BETWEEN` or older `ABS(col - x) < 0.01` float
guard included), so the replayed row is what the live DB holds, not what the
migration's author expected it to hold. A statement the replay cannot read is
skipped and recorded in dbc-tools' skip log (`get_rows()` prints a summary to
stderr), never guessed at.
"""

from __future__ import annotations

import sys
from pathlib import Path

from . import replay

REPO_ROOT = replay.REPO_ROOT
BASE_FILE = REPO_ROOT / "data/sql/base/db_world/item_template.sql"
MERGED_DIR = replay.MERGED_DIR
PENDING_DIR = REPO_ROOT / "data/sql/updates/pending_db_world"  # where lib/emit.py writes (tests redirect it)

TABLE = "item_template"


def _contributing_files() -> list[Path]:
    """Every non-base SQL file that touches `item_template`, in apply order (`replay.contributing_files`)."""
    return [p for p in replay.contributing_files(TABLE) if p != BASE_FILE]


def resolve_current_rows(cache: bool = False) -> dict[int, dict]:
    """Base + every file that touches `item_template`, replayed in apply order, as `{entry: row}`. Column order and
    defaults come from the base file's own CREATE TABLE (and any later ALTER), not a hand-maintained list. `cache`:
    see `replay.session`."""
    with replay.session(cache):  # listing the files reads them: inside the session, once for both
        rows = replay.load_table(TABLE, ("entry",), files=_contributing_files())
    return {key[0]: row for key, row in rows.items()}


def apply_text(text: str, rows: dict[int, dict], source: str = "?") -> None:
    """Replays the `item_template` statements of one SQL text onto `{entry: row}` in place: what a file this tool
    or dbc-tools just rendered does to the overlay (dbc-tools' round-trip test)."""
    keyed = {(entry,): row for entry, row in rows.items()}
    schema = replay.table_schema(TABLE, ("entry",))
    replay.sql_dump.apply_composite_key_statements(
        keyed, schema.columns, schema.key_columns, TABLE, text, defaults=schema.defaults, source=source,
    )
    rows.clear()
    rows.update({key[0]: row for key, row in keyed.items()})


def item_columns() -> list[str]:
    return replay.final_columns(TABLE)


_cache: dict = {"key": None, "rows": None}


def _cache_key() -> tuple:
    """Every SQL file's mtime (all of them: telling which touch the table
    would mean reading them), so a save (new pending file) or a manual edit
    invalidates the cache automatically - cheaper than re-parsing ~46k base
    rows on every request when nothing has changed."""
    paths = [BASE_FILE] + replay.sql_files()
    return tuple((str(p), p.stat().st_mtime_ns) for p in paths)


def get_rows(force: bool = False) -> dict[int, dict]:
    """Cached `resolve_current_rows()` - the webui's routes should call
    this instead of `resolve_current_rows()` directly. `force=True` (after
    this process itself just wrote a new pending file) skips the mtime
    check, since a file written in the same second the cache was built can
    otherwise share an mtime with the cached read on some filesystems.
    Statements the replay skipped are printed to stderr after each fresh
    resolve (`replay.warn_skips`)."""
    key = _cache_key()
    if force or key != _cache["key"]:
        since = len(replay.sqlcorpus.SKIPS.entries)
        _cache["rows"] = resolve_current_rows(cache=True)
        _cache["key"] = _cache_key()  # re-read after resolving, in case a
        # file changed mid-resolve; cheap relative to the resolve itself.
        replay.warn_skips({TABLE}, since=since, file=sys.stderr)
    return _cache["rows"]
