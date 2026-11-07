"""
The general drop guard (dbc-tools-scoped-generate plan, section 2): before a write run (full or `--scope`) writes
anything, it checks that the run would not delete a custom row that is live or deployed but that this checkout has
never seen. The 2026-11-07 near-miss: a branch whose generated revs predated #96 rewrote the whole spell block
(`DELETE ... BETWEEN 200101 AND 209999` + re-insert) without #96's spells 205282 / 205304 / 205348, and its patch-Z
lacked them too.

**SQL half (live DB).** The rendered pending SQL is read back (lib/scope.py's statement reader): for each guarded table
the ids it DELETEs (a range, a list, a key tuple list) and the ids it INSERTs. A live id the SQL deletes and does not
re-insert is a drop. Live ids come from the world DB through a mysql client command: `$DBC_TOOLS_MYSQL` (the same
variable `replay_diff.py` reads), else `LIVE_DB_MYSQL` in lib/local_config.py, e.g.
`docker exec -i <ac-database container> mysql -uroot -p<password>`. Without either, the SQL half is skipped (a note
says so). A configured command that fails stops the run.

**Client half (deployed patch-Z).** `DEPLOY_ROOT/Data/patch-Z.mpq` (lib/local_config.py), or `--deployed-patch`: an id
in a guarded DBC's custom block that the deployed file holds and the archive this run ships lacks is a drop. A full
run ships a new archive (a DBC it does not build is gone from the client); a scoped run repacks the deployed one (a
member it does not replace is unchanged). Item.dbc is left to the older Item.dbc guard (`--allow-item-drop`), which is
stricter. Without a deployed archive the client half is skipped (a note says so).

**Ownership.** A drop is refused only when this checkout does not know the id: no SQL file it holds (the base dump,
the merged and pending updates, custom and module SQL) ever wrote a row with that id as its first value. A row this
checkout's SQL wrote and its source no longer declares is a deliberate removal (a note lists it). `--allow-drop`
writes anyway; `--check` renders no SQL, so the guard does not run there.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import patch_repack, scope, sql_dump, sqlcorpus, trainer_state

REPO_ROOT = Path(__file__).resolve().parents[3]
BASE_SQL_DIR = REPO_ROOT / "data" / "sql" / "base" / "db_world"

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
# Client DBC -> the SQL table it mirrors (its custom block and its "known" check). Item.dbc joins it for a scoped run,
# which the older full-build Item.dbc guard does not cover.
ITEM_DBC = "Item.dbc"
CLIENT_TABLES = {
    "Spell.dbc": "spell_dbc",
    "Talent.dbc": "talent_dbc",
    "TalentTab.dbc": "talenttab_dbc",
    "SkillLineAbility.dbc": "skilllineability_dbc",
    "ItemSet.dbc": "itemset_dbc",
    "ItemExtendedCost.dbc": "itemextendedcost_dbc",
}


class GuardError(RuntimeError):
    """The live DB could not be read with the configured command."""


def custom_ranges(table: str, ids_cfg: dict) -> list[tuple[int, int]]:
    out = []
    for name in GUARDED_TABLES[table][1]:
        block = ids_cfg.get(name)
        if isinstance(block, dict) and "start" in block:
            out.append((int(block["start"]), int(block["end"])))
    return out


def _in(entry_id: int, ranges) -> bool:
    return any(a <= entry_id <= b for a, b in ranges)


def mysql_command() -> list[str] | None:
    """The live-DB client command: `$DBC_TOOLS_MYSQL`, else lib/local_config.py's `LIVE_DB_MYSQL`, else None."""
    text = os.environ.get("DBC_TOOLS_MYSQL")
    if not text:
        try:
            from . import local_config  # noqa: PLC0415
        except ImportError:
            local_config = None
        text = getattr(local_config, "LIVE_DB_MYSQL", None)
    return shlex.split(text) if text else None


def world_database() -> str:
    return os.environ.get("DBC_TOOLS_WORLD_DB", "acore_world")


def live_ids(command: list[str], tables, ids_cfg: dict, database: str | None = None) -> dict[str, set[int]]:
    """`{table: ids}` of the custom ids each guarded table holds in the live world DB (read-only SELECTs)."""
    out: dict[str, set[int]] = {}
    for table in tables:
        column = GUARDED_TABLES[table][0]
        ranges = custom_ranges(table, ids_cfg)
        where = " OR ".join(f"`{column}` BETWEEN {a} AND {b}" for a, b in ranges)
        sql = f"SELECT DISTINCT `{column}` FROM `{table}` WHERE {where};"
        try:
            done = subprocess.run(
                [*command, "-B", "-N", database or world_database()], input=sql.encode(), capture_output=True,
                timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise GuardError(f"could not run {' '.join(command[:3])} ...: {error}") from error
        if done.returncode != 0:
            raise GuardError(
                f"mysql failed ({done.returncode}) reading {table}: {done.stderr.decode(errors='replace').strip()}"
            )
        out[table] = {int(line) for line in done.stdout.decode().split() if line.strip().lstrip("-").isdigit()}
    return out


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


def _dbc_ids(blob: bytes, table) -> set[int]:
    return {int(r[table.index_column]) for r in scope.read_dbc_bytes(blob, table)}


def client_drops(deployed: dict[str, bytes], shipped: dict[str, bytes], tables: dict, ids_cfg: dict,
                 replaces_archive: bool, include_item: bool = False) -> dict[str, list[int]]:
    """`{DBC file: ids}`: custom ids a deployed DBC holds that the shipped one lacks. `shipped`: `{DBC file: bytes}`
    this run puts in the archive; `replaces_archive`: a full run (a DBC missing from `shipped` disappears) rather
    than a repack (a DBC missing from `shipped` is unchanged). `tables`: `{DBC file: DbcTable}`."""
    by_file = {name.replace("\\", "/").split("/")[-1]: blob for name, blob in deployed.items()}
    out = {}
    checked = {**CLIENT_TABLES, **({ITEM_DBC: "item_dbc"} if include_item else {})}
    for filename, sql_table in checked.items():
        old = by_file.get(filename)
        if old is None or filename not in tables:
            continue
        if filename in shipped:
            new_ids = _dbc_ids(shipped[filename], tables[filename])
        elif replaces_archive:
            new_ids = set()
        else:
            continue
        ranges = custom_ranges(sql_table, ids_cfg)
        drops = sorted(i for i in _dbc_ids(old, tables[filename]) if _in(i, ranges) and i not in new_ids)
        if drops:
            out[filename] = drops
    return out


def known_ids(table: str, ids, pending_dir: Path) -> set[int]:
    """The ids of `ids` that some SQL file of this checkout wrote as a row's first value of `table` (`(<id>,`): the
    base dump, the merged and pending updates, custom and module SQL. A drop of such an id is this checkout's own
    removal, not another branch's row."""
    ids = set(ids)
    if not ids:
        return set()
    files = [BASE_SQL_DIR / f"{table}.sql", *trainer_state.update_files(pending_dir=pending_dir)]
    pattern = re.compile(r"\(\s*(" + "|".join(str(i) for i in sorted(ids)) + r")\s*,")
    insert = re.compile(
        r"\b(?:INSERT|REPLACE)\s+(?:IGNORE\s+)?INTO\s+`?" + re.escape(table) + r"`?[\s(]", re.IGNORECASE,
    )
    found: set[int] = set()
    for path in files:
        if not path.is_file():
            continue
        if path.name != f"{table}.sql" and not sqlcorpus.mentions(path, table, loose=True):
            continue
        text = sqlcorpus.read_text(path)
        for m in insert.finditer(text):
            end = sql_dump._statement_end(text, m.end())
            found.update(int(hit.group(1)) for hit in pattern.finditer(text, m.end(), end))
        if found >= ids:
            break
    return found


@dataclass
class GuardResult:
    lines: list[str] = field(default_factory=list)  # printed as they are
    refused: bool = False


def _shown(ids: list[int]) -> str:
    return ", ".join(map(str, ids[:20])) + (" ..." if len(ids) > 20 else "")


def check(*, sql_text: str | None, shipped: dict[str, bytes], replaces_archive: bool, deployed_archive: Path | None,
          tables: dict, ids_cfg: dict, pending_dir: Path, allow: bool, live_command: list[str] | None = None,
          live_reader=live_ids, include_item: bool = False) -> GuardResult:
    """Runs both halves and says whether to stop. `shipped` / `replaces_archive` / `tables`: see `client_drops`."""
    out = GuardResult()
    if allow:
        out.lines.append("WARNING: drop guard: skipped (--allow-drop)")
        return out
    problems: list[str] = []
    # SQL half
    if live_command is None:
        out.lines.append(
            "note: drop guard: live DB half skipped (set $DBC_TOOLS_MYSQL or LIVE_DB_MYSQL in lib/local_config.py)"
        )
    elif sql_text:
        try:
            live = live_reader(live_command, list(GUARDED_TABLES), ids_cfg)
        except GuardError as error:
            out.lines.append(
                f"ERROR: drop guard: {error}. Nothing was written; fix the command or pass --allow-drop to write anyway"
            )
            out.refused = True
            return out
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
    # Client half
    if deployed_archive is None or not Path(deployed_archive).is_file():
        out.lines.append(
            "note: drop guard: deployed patch-Z half skipped (no lib/local_config.py DEPLOY_ROOT with a "
            "Data/patch-Z.mpq, and no --deployed-patch)"
        )
    else:
        try:
            deployed = patch_repack.read_members(Path(deployed_archive))
        except (patch_repack.RepackError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
            out.lines.append(f"ERROR: drop guard: could not read {deployed_archive}: {error}. Nothing was written; "
                             f"pass --allow-drop to write anyway")
            out.refused = True
            return out
        drops_by_file = client_drops(deployed, shipped, tables, ids_cfg, replaces_archive, include_item)
        for filename, drops in sorted(drops_by_file.items()):
            known = known_ids(CLIENT_TABLES.get(filename, "item_dbc"), drops, pending_dir)
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
    checked = []
    if live_command is not None and sql_text:
        checked.append(f"live DB ({len(GUARDED_TABLES)} tables)")
    if deployed_archive is not None and Path(deployed_archive).is_file():
        checked.append(f"deployed {Path(deployed_archive).name}")
    if checked and not problems:
        out.lines.append(f"note: drop guard: nothing live or deployed is dropped (checked {', '.join(checked)})")
    if problems:
        for problem in problems:
            out.lines.append(f"ERROR: drop guard: {problem}")
        out.lines.append(
            "ERROR: drop guard: this run would delete live or deployed rows that another checkout or branch wrote "
            "(typically this branch is behind: merge or rebase onto the branch that shipped them, then regenerate). "
            "Nothing was written; pass --allow-drop to write anyway"
        )
        out.refused = True
    return out
