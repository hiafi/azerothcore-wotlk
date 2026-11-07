"""
The general drop guard (dbc-tools-scoped-generate plan, section 2): before a write run (full, `--scope`, `--only
items`) writes its SQL or patch, it checks that the run would not delete, or rewrite with other content, a custom row
that is live or deployed but that this checkout has never seen. The 2026-11-07 near-miss: a branch whose generated
revs predated #96 rewrote the whole spell block (`DELETE ... BETWEEN 200101 AND 209999` + re-insert) without #96's
spells 205282 / 205304 / 205348, and its patch-Z lacked them too.

What it can and cannot see: it judges the run being made, against what is live / deployed *now*. A rev written earlier
(before the other branch's rows went live) cannot be caught at write time; `check_pending.py` judges the pending revs
the live `updates` table has not applied yet, right before db-import.

**Inputs, read-only.** Live ids come from the world DB through a mysql client command: `$DBC_TOOLS_MYSQL`, else
`LIVE_DB_MYSQL` in this checkout's lib/local_config.py, else (a worktree, which has no local_config.py) the main
checkout's (`git rev-parse --git-common-dir`). The deployed archive is the caller's (`--deployed-patch`,
`$DBC_TOOLS_DEPLOYED_PATCH`, this checkout's `DEPLOY_ROOT`), else the main checkout's `DEPLOY_ROOT/Data/patch-Z.mpq`.
The main checkout's settings are only ever read here, for the guard: they never make a run deploy.

**SQL half.** The rendered SQL is read back (lib/scope.py's statement reader). For each guarded table:

- a live custom id that a DELETE covers (a range, a list, a key tuple) and no INSERT re-adds is a *drop*;
- a live custom id the SQL re-inserts with content that differs from the live row is a *rewrite*.

**Client half.** In the deployed archive, every DBC the guard knows (CLIENT_TABLES): a custom id the deployed file
holds and the archive this run ships lacks is a drop. A full run replaces the archive, so a DBC it does not ship
loses every row (and a deployed member the guard has no definition for is reported by name); a repack (`--scope`,
`--only items`) leaves the members it does not replace alone. Item.dbc is left to the older, stricter Item.dbc guard
(`--allow-item-drop`) in a full run.

**Ownership.** A drop is refused only when no SQL file of this checkout (base dump, merged and pending updates, custom
and module SQL) ever INSERTed a row with that id (`known_ids`); otherwise it is this checkout's own removal (a note).
A rewrite is refused when no such file ever INSERTed the live content of that row (and none UPDATEs it): the live
content came from another branch, and this run would revert it. `--allow-drop` writes anyway; `--check` renders no
SQL, so the guard does not run there.
"""

from __future__ import annotations

import os
import re
import runpy
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import dbcfmt, patch_repack, replay_diff, scope, sql_dump, sqlcorpus, trainer_state

REPO_ROOT = Path(__file__).resolve().parents[3]
BASE_SQL_DIR = REPO_ROOT / "data" / "sql" / "base" / "db_world"
LOCAL_CONFIG_REL = Path("apps") / "dbc-tools" / "lib" / "local_config.py"

# SQL table -> (id column, ids.yaml blocks holding its custom ids).
GUARDED_TABLES: dict[str, tuple[str, tuple[str, ...]]] = {
    "spell_dbc": ("ID", ("spell",)),
    "talent_dbc": ("ID", ("talent",)),
    "talenttab_dbc": ("ID", ("talenttab",)),
    "skilllineability_dbc": ("ID", ("skilllineability",)),
    "item_dbc": ("ID", ("item",)),
    "item_template": ("entry", ("item",)),
    "itemset_dbc": ("ID", ("item_set",)),
    "itemextendedcost_dbc": ("ID", ("item_extended_cost",)),
    "creature_template": ("entry", ("creature", "npc_tools", "creature_heroic")),
    "creature_template_model": ("CreatureID", ("creature", "npc_tools", "creature_heroic")),
}
ITEM_DBC = "Item.dbc"
# Client DBC -> (the SQL table it mirrors, for the "known" check; None: client-only; ids.yaml blocks of its ids).
CLIENT_TABLES: dict[str, tuple[str | None, tuple[str, ...]]] = {
    "Spell.dbc": ("spell_dbc", ("spell",)),
    "Talent.dbc": ("talent_dbc", ("talent",)),
    "TalentTab.dbc": ("talenttab_dbc", ("talenttab",)),
    "SkillLineAbility.dbc": ("skilllineability_dbc", ("skilllineability",)),
    ITEM_DBC: ("item_dbc", ("item",)),
    "ItemSet.dbc": ("itemset_dbc", ("item_set",)),
    "ItemExtendedCost.dbc": ("itemextendedcost_dbc", ("item_extended_cost",)),
    "MapDifficulty.dbc": ("mapdifficulty_dbc", ("mapdifficulty",)),
    "DungeonEncounter.dbc": ("dungeonencounter_dbc", ("dungeonencounter",)),
    "ItemLimitCategory.dbc": ("itemlimitcategory_dbc", ("item_limit_category",)),
    "SpellRuneCost.dbc": ("spellrunecost_dbc", ("spellrunecost",)),
    "SpellCategory.dbc": ("spellcategory_dbc", ("spellcategory",)),
    "SpellDescriptionVariables.dbc": (None, ("spelldescriptionvariables",)),
    "SpellCastTimes.dbc": ("spellcasttimes_dbc", ("spellcasttimes",)),
    "SpellDuration.dbc": ("spellduration_dbc", ("spellduration",)),
    "SpellRange.dbc": ("spellrange_dbc", ("spellrange",)),
    "SpellRadius.dbc": ("spellradius_dbc", ("spellradius",)),
}


class GuardError(RuntimeError):
    """The live DB could not be read with the configured command."""


def _ranges(block_names, ids_cfg: dict) -> list[tuple[int, int]]:
    out = []
    for name in block_names:
        block = ids_cfg.get(name)
        if isinstance(block, dict) and "start" in block:
            out.append((int(block["start"]), int(block["end"])))
    return out


def custom_ranges(table: str, ids_cfg: dict) -> list[tuple[int, int]]:
    return _ranges(GUARDED_TABLES[table][1], ids_cfg)


def _in(entry_id: int, ranges) -> bool:
    return any(a <= entry_id <= b for a, b in ranges)


def client_table_defs() -> dict:
    """`{DBC file: DbcTable}` for every client table the guard can read."""
    from . import item_sets  # noqa: PLC0415 (item_sets imports half of lib)

    defs = {t.dbc_filename: t for t in vars(dbcfmt).values() if isinstance(t, dbcfmt.DbcTable)}
    defs[item_sets.ITEMSET.dbc_filename] = item_sets.ITEMSET
    defs[item_sets.ITEMEXTENDEDCOST.dbc_filename] = item_sets.ITEMEXTENDEDCOST
    return defs


# ---------------------------------------------------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------------------------------------------------

def _main_checkout_config() -> dict:
    """`LIVE_DB_MYSQL` / `DEPLOY_ROOT` of the main checkout's lib/local_config.py when this tree is a git worktree
    without its own (read for the guard only). Empty when there is none or this is the main checkout."""
    try:
        common = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    if common.returncode != 0 or not common.stdout.strip():
        return {}
    main_root = Path(common.stdout.strip()).parent
    path = main_root / LOCAL_CONFIG_REL
    if main_root.resolve() == REPO_ROOT.resolve() or not path.is_file():
        return {}
    try:
        values = runpy.run_path(str(path))
    except Exception:  # noqa: BLE001 - an unreadable config is the same as none
        return {}
    return {"path": path, "LIVE_DB_MYSQL": values.get("LIVE_DB_MYSQL"), "DEPLOY_ROOT": values.get("DEPLOY_ROOT")}


def _own_config() -> dict:
    try:
        from . import local_config  # noqa: PLC0415
    except ImportError:
        return {}
    return {"LIVE_DB_MYSQL": getattr(local_config, "LIVE_DB_MYSQL", None),
            "DEPLOY_ROOT": getattr(local_config, "DEPLOY_ROOT", None)}


def mysql_command() -> list[str] | None:
    """The live-DB client command: `$DBC_TOOLS_MYSQL`, else this checkout's `LIVE_DB_MYSQL`, else the main
    checkout's (a worktree), else None."""
    text = os.environ.get("DBC_TOOLS_MYSQL") or _own_config().get("LIVE_DB_MYSQL") or \
        _main_checkout_config().get("LIVE_DB_MYSQL")
    return shlex.split(text) if text else None


def env_deployed_patch() -> Path | None:
    """`$DBC_TOOLS_DEPLOYED_PATCH`: a read-only deployed archive (a worktree's guard input and scope base)."""
    text = os.environ.get("DBC_TOOLS_DEPLOYED_PATCH")
    return Path(text).expanduser().resolve() if text else None


def fallback_deployed_patch() -> Path | None:
    """The main checkout's `DEPLOY_ROOT/Data/patch-Z.mpq` (a worktree), read by the guard only."""
    root = _main_checkout_config().get("DEPLOY_ROOT")
    path = Path(root) / "Data" / "patch-Z.mpq" if root else None
    return path if path is not None and path.is_file() else None


def world_database() -> str:
    return os.environ.get("DBC_TOOLS_WORLD_DB", "acore_world")


def run_sql(command: list[str], sql: str, database: str | None = None, header: bool = False) -> str:
    """One read-only query through the mysql client command; its stdout (`-B`, with `-N` unless `header`)."""
    args = [*command, "-B", *([] if header else ["-N"]), database or world_database()]
    try:
        done = subprocess.run(args, input=sql.encode(), capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GuardError(f"could not run {' '.join(command[:3])} ...: {error}") from error
    if done.returncode != 0:
        raise GuardError(f"mysql failed ({done.returncode}): {done.stderr.decode(errors='replace').strip()}")
    return done.stdout.decode("utf-8", errors="replace")


def live_ids(command: list[str], tables, ids_cfg: dict, database: str | None = None) -> dict[str, set[int]]:
    """`{table: ids}` of the custom ids each guarded table holds in the live world DB (read-only SELECTs)."""
    out: dict[str, set[int]] = {}
    for table in tables:
        column = GUARDED_TABLES[table][0]
        where = " OR ".join(f"`{column}` BETWEEN {a} AND {b}" for a, b in custom_ranges(table, ids_cfg))
        text = run_sql(command, f"SELECT DISTINCT `{column}` FROM `{table}` WHERE {where};", database)
        out[table] = {int(line) for line in text.split() if line.strip().lstrip("-").isdigit()}
    return out


def live_rows(command: list[str], table: str, ids, database: str | None = None) -> dict[int, dict]:
    """`{id: row}` of the live rows of `table` with those ids (read-only SELECTs, 500 ids at a time)."""
    column = GUARDED_TABLES[table][0]
    ids = sorted(ids)
    out: dict[int, dict] = {}
    for start in range(0, len(ids), 500):
        chunk = ", ".join(str(i) for i in ids[start:start + 500])
        text = run_sql(command, f"SELECT * FROM `{table}` WHERE `{column}` IN ({chunk});", database, header=True)
        for row in replay_diff.parse_mysql_batch(text):
            out[int(row[column])] = row
    return out


# ---------------------------------------------------------------------------------------------------------------------
# What the SQL does
# ---------------------------------------------------------------------------------------------------------------------

def sql_drops(sql_text: str | None, live: dict[str, set[int]]) -> dict[str, list[int]]:
    """`{table: ids}`: live ids the SQL deletes and does not re-insert."""
    if not sql_text:
        return {}
    tables = {t: GUARDED_TABLES[t][0] for t in live}
    effects = scope.deleted_and_inserted(sql_text, tables)
    out = {}
    for table, (ranges, deleted, inserted) in effects.items():
        drops = sorted(i for i in live.get(table, ()) if (i in deleted or _in(i, ranges)) and i not in inserted)
        if drops:
            out[table] = drops
    return out


def inserted_rows(sql_text: str | None, tables) -> dict[str, dict[int, dict]]:
    """`{table: {id: row}}` the SQL INSERTs into the guarded `tables` (the last INSERT of an id wins)."""
    out: dict[str, dict[int, dict]] = {}
    if not sql_text:
        return out
    for raw in scope.split_statements(sql_text):
        if raw.startswith("--") or not raw.upper().startswith("INSERT"):
            continue
        m = re.match(r"^INSERT\s+INTO\s+`?(\w+)`?", raw, re.IGNORECASE)
        if not m or m.group(1) not in tables:
            continue
        stmt = scope.parse_statement(raw)
        column = GUARDED_TABLES[stmt.table][0]
        for _group, row in stmt.rows:
            value = scope._norm(row.get(column))
            if isinstance(value, int):
                out.setdefault(stmt.table, {})[value] = row
    return out


def _value(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def same_content(inserted: dict, live: dict) -> bool:
    """Whether every column of an INSERTed row equals the live row (numbers with MySQL FLOAT's tolerance)."""
    for column, want in inserted.items():
        if column not in live:
            continue
        a, b = _value(want), _value(live[column])
        if isinstance(a, float) and isinstance(b, float):
            if abs(a - b) > max(1e-5 * max(abs(a), abs(b)), 1e-6):
                return False
        elif a != b and not ({a, b} <= {None, 0.0}):
            return False
    return True


# ---------------------------------------------------------------------------------------------------------------------
# What this checkout's SQL history wrote
# ---------------------------------------------------------------------------------------------------------------------

def history_files(pending_dir: Path, table: str) -> list[Path]:
    """The base dump of `table`, then every update file in DBUpdater's apply order."""
    return [BASE_SQL_DIR / f"{table}.sql", *trainer_state.update_files(pending_dir=pending_dir)]


def _insert_re(table: str) -> re.Pattern:
    return re.compile(
        r"\b(?:INSERT|REPLACE)\s+(?:IGNORE\s+)?INTO\s+`?" + re.escape(table) + r"`?\s*(\(([^)]*)\))?\s*VALUES",
        re.IGNORECASE,
    )


def _row_starts(ids) -> re.Pattern:
    # a tuple's first value: right after VALUES or after the previous tuple's "),", never inside a string value
    return re.compile(r"(?:VALUES|\),)\s*(\(\s*(" + "|".join(str(i) for i in sorted(ids)) + r")\s*,)", re.IGNORECASE)


def insert_hits(table: str, ids, files: list[Path], with_rows: bool = False) -> dict[int, list]:
    """`{id: [(file, row or None), ...]}` in file order: every INSERT into `table` of a row whose first value is one of
    `ids`. `with_rows` also parses each such row (column list from the statement, or the base dump's CREATE TABLE)."""
    ids = {int(i) for i in ids}
    out: dict[int, list] = {}
    if not ids:
        return out
    starts = _row_starts(ids)
    insert = _insert_re(table)
    for path in files:
        if not path.is_file():
            continue
        if path.name != f"{table}.sql" and not sqlcorpus.mentions(path, table, loose=True):
            continue
        text = sqlcorpus.read_text(path)
        for m in insert.finditer(text):
            end = sql_dump._statement_end(text, m.end())
            columns = None
            if with_rows:
                if m.group(2):
                    columns = [c.strip().strip("`") for c in m.group(2).split(",")]
                else:
                    try:
                        columns = list(sql_dump.parse_create_table_columns(path, table))
                    except Exception:  # noqa: BLE001 - no CREATE TABLE: rows are not compared
                        columns = None
            # from the VALUES keyword on, so the statement's first tuple is found too
            for hit in starts.finditer(text, m.end() - len("VALUES"), end):
                row = None
                if columns is not None:
                    group = scope.first_group(text[hit.start(1):end])
                    if group:
                        values = scope._values(group)
                        if len(values) == len(columns):
                            row = dict(zip(columns, values))
                out.setdefault(int(hit.group(2)), []).append((path, row))
    return out


def known_ids(table: str, ids, pending_dir: Path) -> set[int]:
    """The ids of `ids` that some SQL file of this checkout INSERTed as a row of `table` (the base dump, the merged and
    pending updates, custom and module SQL): dropping such an id is this checkout's own removal."""
    return set(insert_hits(table, ids, history_files(pending_dir, table)))


def updated_ids(table: str, ids, files: list[Path]) -> set[int]:
    """The ids of `ids` an UPDATE of `table` in `files` names: their live content may come from it (lenient)."""
    ids = {int(i) for i in ids}
    found: set[int] = set()
    if not ids:
        return found
    update = re.compile(r"\bUPDATE\s+`?" + re.escape(table) + r"`?\s+SET\b", re.IGNORECASE)
    number = re.compile(r"\b(" + "|".join(str(i) for i in sorted(ids)) + r")\b")
    for path in files:
        if not path.is_file() or not sqlcorpus.mentions(path, table, loose=True):
            continue
        text = sqlcorpus.read_text(path)
        for m in update.finditer(text):
            end = sql_dump._statement_end(text, m.end())
            where = text.upper().find("WHERE", m.end(), end)
            if where >= 0:
                found.update(int(h.group(1)) for h in number.finditer(text, where, end))
    return found


def content_writers(table: str, live: dict[int, dict], files: list[Path]) -> dict[int, list[Path]]:
    """`{id: [file, ...]}`: the files whose INSERT of that id equals its live row, in file order."""
    out: dict[int, list[Path]] = {}
    for entry_id, hits in insert_hits(table, live, files, with_rows=True).items():
        for path, row in hits:
            if row is not None and same_content(row, live[entry_id]):
                out.setdefault(entry_id, []).append(path)
    return out


def rewrite_findings(sql_text: str | None, live: dict[str, set[int]], command, pending_dir: Path,
                     rows_reader=live_rows) -> dict[str, list[int]]:
    """`{table: ids}`: live rows the SQL re-inserts with other content, whose live content no INSERT of this checkout
    wrote and no UPDATE names (another branch's change this run would revert)."""
    out: dict[str, list[int]] = {}
    for table, rows in inserted_rows(sql_text, set(live)).items():
        candidates = sorted(i for i in rows if i in live.get(table, ()))
        if not candidates:
            continue
        current = rows_reader(command, table, candidates)
        differing = {i: current[i] for i in candidates if i in current and not same_content(rows[i], current[i])}
        if not differing:
            continue
        files = history_files(pending_dir, table)
        writers = content_writers(table, differing, files)
        lenient = updated_ids(table, set(differing) - set(writers), files)
        foreign = sorted(i for i in differing if i not in writers and i not in lenient)
        if foreign:
            out[table] = foreign
    return out


# ---------------------------------------------------------------------------------------------------------------------
# The client half
# ---------------------------------------------------------------------------------------------------------------------

def _dbc_ids(blob: bytes, table) -> set[int]:
    return {int(r[table.index_column]) for r in scope.read_dbc_bytes(blob, table)}


def client_drops(deployed: dict[str, bytes], shipped: dict[str, bytes], tables: dict | None, ids_cfg: dict,
                 replaces_archive: bool, include_item: bool = False) -> tuple[dict[str, list[int]], list[str]]:
    """`({DBC file: ids}, [member names])`: custom ids a deployed DBC holds that the shipped one lacks, and (a full run)
    deployed DBC members the guard has no definition for that the new archive would lose. `shipped`: `{DBC file:
    bytes}` this run puts in the archive; `replaces_archive`: a full run (a DBC missing from `shipped` disappears)
    rather than a repack (a DBC missing from `shipped` is unchanged). `tables`: `{DBC file: DbcTable}` (default: every
    table the guard knows)."""
    tables = tables if tables is not None else client_table_defs()
    out: dict[str, list[int]] = {}
    lost_members: list[str] = []
    for name, old in deployed.items():
        filename = name.replace("\\", "/").split("/")[-1]
        if filename not in shipped and not replaces_archive:
            continue
        if filename == ITEM_DBC and not include_item:
            continue
        mapping = CLIENT_TABLES.get(filename)
        table = tables.get(filename)
        if mapping is None or table is None:
            if replaces_archive and filename not in shipped and \
                    name.replace("\\", "/").lower().startswith("dbfilesclient/"):
                lost_members.append(name)
            continue
        new_ids = _dbc_ids(shipped[filename], table) if filename in shipped else set()
        drops = sorted(i for i in _dbc_ids(old, table) if _in(i, _ranges(mapping[1], ids_cfg)) and i not in new_ids)
        if drops:
            out[filename] = drops
    return out, lost_members


# ---------------------------------------------------------------------------------------------------------------------
# The write-run check
# ---------------------------------------------------------------------------------------------------------------------

@dataclass
class GuardResult:
    lines: list[str] = field(default_factory=list)  # printed as they are
    refused: bool = False


def _shown(ids: list[int]) -> str:
    return ", ".join(map(str, ids[:20])) + (" ..." if len(ids) > 20 else "")


NOT_WRITTEN = "No SQL or patch was written"


def check(*, sql_text: str | None, shipped: dict[str, bytes], replaces_archive: bool, deployed_archive: Path | None,
          tables: dict | None, ids_cfg: dict, pending_dir: Path, allow: bool, live_command: list[str] | None = None,
          live_reader=live_ids, rows_reader=live_rows, include_item: bool = False) -> GuardResult:
    """Runs both halves and says whether to stop. `shipped` / `replaces_archive` / `tables`: see `client_drops`."""
    out = GuardResult()
    if allow:
        out.lines.append("WARNING: drop guard: skipped (--allow-drop)")
        return out
    problems: list[str] = []
    checked: list[str] = []
    # SQL half
    if live_command is None:
        out.lines.append(
            "note: drop guard: live DB half skipped (set $DBC_TOOLS_MYSQL, or LIVE_DB_MYSQL in this or the main "
            "checkout's lib/local_config.py)"
        )
    elif sql_text:
        try:
            live = live_reader(live_command, list(GUARDED_TABLES), ids_cfg)
            rewrites = rewrite_findings(sql_text, live, live_command, pending_dir, rows_reader)
        except GuardError as error:
            out.lines.append(f"ERROR: drop guard: {error}. {NOT_WRITTEN}; fix the command or pass --allow-drop")
            out.refused = True
            return out
        checked.append(f"live DB ({len(GUARDED_TABLES)} tables)")
        for table, drops in sorted(sql_drops(sql_text, live).items()):
            known = known_ids(table, drops, pending_dir)
            foreign = [i for i in drops if i not in known]
            mine = [i for i in drops if i in known]
            if mine:
                out.lines.append(
                    f"note: drop guard: {table}: deleting {len(mine)} live row(s) this checkout wrote and no longer "
                    f"declares: {_shown(mine)}"
                )
            if foreign:
                problems.append(f"{table}: {len(foreign)} live row(s) this checkout never wrote: {_shown(foreign)}")
        for table, ids in sorted(rewrites.items()):
            problems.append(
                f"{table}: would rewrite {len(ids)} live row(s) whose live content no SQL file of this checkout wrote "
                f"(reverting another branch's change): {_shown(ids)}"
            )
    # Client half
    if deployed_archive is None or not Path(deployed_archive).is_file():
        out.lines.append(
            "note: drop guard: deployed patch-Z half skipped (no --deployed-patch, $DBC_TOOLS_DEPLOYED_PATCH, or "
            "DEPLOY_ROOT with a Data/patch-Z.mpq in this or the main checkout's lib/local_config.py)"
        )
    else:
        try:
            deployed = patch_repack.read_members(Path(deployed_archive))
        except (patch_repack.RepackError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
            out.lines.append(f"ERROR: drop guard: could not read {deployed_archive}: {error}. {NOT_WRITTEN}; "
                             f"pass --allow-drop to write anyway")
            out.refused = True
            return out
        checked.append(f"deployed {deployed_archive}")
        drops_by_file, lost = client_drops(deployed, shipped, tables, ids_cfg, replaces_archive, include_item)
        for filename, drops in sorted(drops_by_file.items()):
            sql_table = CLIENT_TABLES[filename][0]
            known = known_ids(sql_table, drops, pending_dir) if sql_table else set()
            foreign = [i for i in drops if i not in known]
            mine = [i for i in drops if i in known]
            if mine:
                out.lines.append(
                    f"note: drop guard: {filename}: removing {len(mine)} deployed row(s) this checkout wrote and no "
                    f"longer declares: {_shown(mine)}"
                )
            if foreign:
                problems.append(
                    f"{filename}: {len(foreign)} row(s) of the deployed {Path(deployed_archive).name} this checkout "
                    f"never wrote: {_shown(foreign)}"
                )
        if lost:
            problems.append(f"the new archive would lose deployed member(s) {', '.join(lost)}")
    if not checked and (sql_text or shipped):
        out.lines.append(
            "WARNING: drop guard: neither half could run, so nothing protects live or deployed rows from this run "
            "(see the two notes above)"
        )
    elif not problems:
        out.lines.append(f"note: drop guard: nothing live or deployed is dropped (checked {', '.join(checked)})")
    if problems:
        for problem in problems:
            out.lines.append(f"ERROR: drop guard: {problem}")
        out.lines.append(
            "ERROR: drop guard: this run would delete or revert live or deployed rows that another checkout or branch "
            f"wrote (typically this branch is behind: merge or rebase onto the branch that shipped them, then "
            f"regenerate). {NOT_WRITTEN}; pass --allow-drop to write anyway"
        )
        out.refused = True
    return out
