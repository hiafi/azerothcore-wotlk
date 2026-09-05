"""Shared "current state" loading, in two flavors — see the "Two baselines,
two purposes" note below before reaching for either one.

`load_stock_rows`: base client DBC (if extracted) overlaid by the current
base SQL dump for a table — pure vanilla, nothing this pipeline or any past
rework has ever touched. This is the client's own starting point: every
build of the client patch has to start here, because the patch is assembled
fresh from `var/extractors/dbc` every run, never from a previous patch.

`load_existing_rows`: `load_stock_rows`'s result further overlaid by every
already-promoted migration under data/sql/updates/db_world/ that touches
that table - mirroring DBCDatabaseLoader's own override-by-ID semantics.
This is "what the server's world DB actually has right now."

## Two baselines, two purposes

`generate.py` needs both, for different questions, and conflating them is a
real bug this file shipped once already:

- **"Does this SQL migration need to touch ID N?"** — compare against
  `load_existing_rows`. If a past rework already promoted N's row to
  db_world/, re-emitting identical DELETE+INSERT SQL for it is pure noise —
  see the db_world/ overlay's own motivation below.
- **"Does the client patch need to carry ID N?"** — compare against
  `load_stock_rows`, never `load_existing_rows`. The client patch is a
  from-scratch merge of `var/extractors/dbc` (vanilla) with whatever rows
  generate.py decides differ from vanilla; an ID that's "unchanged" only
  relative to *already-promoted* data still differs from what the raw client
  file has, and the client needs that difference baked in on *every* build,
  not just the first one after the change was made. Using
  `load_existing_rows` here silently drops already-promoted content from
  every subsequent client patch — confirmed live: after the db_world/ overlay
  shipped, three Frost Mage talents (73, 1736, 1740) that had already been
  promoted stopped appearing in the generated Talent.dbc's client patch,
  landing back at their stock tier/column and colliding with the new talents
  placed there.

The db_world/ overlay (used only for the first question) exists so that a
past rework's promoted changes (e.g. the Frost Mage rework) read as "already
applied" rather than "different from vanilla" for *SQL-emission* purposes —
without it, every run of generate.py permanently re-classifies every ID any
past run ever touched as freshly edited, forever, regardless of whether this
run's source data changed it (see docs/dbc-build-pipeline.md's bug log). It's
a best-effort replay (`sql_dump.apply_statements`) over 776+ files of mixed
provenance - pure generator output, merged multi-rev migrations with
hand-written sections, and pure hand-written fixes - so it won't parse every
shape perfectly; see that function's docstring for why an imperfect replay
degrades safely instead of writing wrong data.

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


def load_stock_rows(table: DbcTable) -> dict[int, dict]:
    """Pure vanilla state: base client DBC overlaid by the base SQL dump only
    - no db_world/ promoted migrations. Use this (never `load_existing_rows`)
    for anything that decides what the *client patch* needs to contain - see
    this module's docstring for why."""
    rows: dict[int, dict] = {}
    dbc_path = BASE_DBC_DIR / table.dbc_filename
    if dbc_path.is_file():
        for row in dbcfile.read_dbc(dbc_path, table):
            rows[row[table.index_column]] = row
    sql_path = BASE_SQL_DIR / f"{table.sql_table}.sql"
    if sql_path.is_file():
        rows.update(sql_dump.read_table_dump(sql_path, table))
    return rows


def load_existing_rows(table: DbcTable) -> dict[int, dict]:
    """`load_stock_rows` further overlaid by every already-promoted db_world/
    migration - "what the server's world DB actually has right now". Use
    this for deciding what a *SQL migration* needs to touch, never for
    deciding what the *client patch* needs to contain - see this module's
    docstring for why those are different questions with different answers."""
    rows = load_stock_rows(table)
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
