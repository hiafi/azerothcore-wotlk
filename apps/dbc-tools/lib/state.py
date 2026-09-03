"""Shared "current state" loading: base client DBC (if extracted) overlaid by
the current base SQL dump for a table, then further overlaid by every
already-promoted migration under data/sql/updates/db_world/ that touches that
table - mirroring DBCDatabaseLoader's own override-by-ID semantics. Used by
both generate.py and pull.py.

The db_world/ overlay exists so that a past rework's promoted changes (e.g.
the Frost Mage rework) read as "already applied" rather than "different from
vanilla" - without it, every run of generate.py permanently re-classifies
every ID any past run ever touched as freshly edited, forever, regardless of
whether this run's source data changed it (see docs/dbc-build-pipeline.md's
bug log). It's a best-effort replay (`sql_dump.apply_statements`) over
776+ files of mixed provenance - pure generator output, merged multi-rev
migrations with hand-written sections, and pure hand-written fixes - so it
won't parse every shape perfectly; see that function's docstring for why an
imperfect replay degrades safely instead of writing wrong data.

Deliberately does not read data/sql/updates/pending_db_world/: this pipeline
regenerates its own reserved ranges from source on every run rather than
diffing against its own prior output — see docs/dbc-build-pipeline.md.
"""

from __future__ import annotations

from pathlib import Path

from . import dbcfile, sql_dump
from .dbcfmt import DbcTable

REPO_ROOT = Path(__file__).resolve().parents[3]
BASE_DBC_DIR = REPO_ROOT / "var" / "extractors" / "dbc"
BASE_SQL_DIR = REPO_ROOT / "data" / "sql" / "base" / "db_world"
PROMOTED_SQL_DIR = REPO_ROOT / "data" / "sql" / "updates" / "db_world"


def load_existing_rows(table: DbcTable) -> dict[int, dict]:
    rows: dict[int, dict] = {}
    dbc_path = BASE_DBC_DIR / table.dbc_filename
    if dbc_path.is_file():
        for row in dbcfile.read_dbc(dbc_path, table):
            rows[row[table.index_column]] = row
    sql_path = BASE_SQL_DIR / f"{table.sql_table}.sql"
    if sql_path.is_file():
        rows.update(sql_dump.read_table_dump(sql_path, table))
    needle = f"`{table.sql_table}`"
    for path in sorted(PROMOTED_SQL_DIR.glob("*.sql")):
        text = path.read_text(encoding="utf-8")
        if needle not in text:
            continue
        try:
            sql_dump.apply_statements(rows, table, text)
        except Exception as exc:  # pragma: no cover - defensive, see module docstring
            print(f"warning: state.py: skipping {path} for {table.sql_table}: {exc}")
    return rows
