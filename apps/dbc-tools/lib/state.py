"""Shared "current state" loading: base client DBC (if extracted) overlaid
by the current base SQL dump for a table, mirroring DBCDatabaseLoader's own
override-by-ID semantics. Used by both generate.py and pull.py.

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


def load_existing_rows(table: DbcTable) -> dict[int, dict]:
    rows: dict[int, dict] = {}
    dbc_path = BASE_DBC_DIR / table.dbc_filename
    if dbc_path.is_file():
        for row in dbcfile.read_dbc(dbc_path, table):
            rows[row[table.index_column]] = row
    sql_path = BASE_SQL_DIR / f"{table.sql_table}.sql"
    if sql_path.is_file():
        rows.update(sql_dump.read_table_dump(sql_path, table))
    return rows
