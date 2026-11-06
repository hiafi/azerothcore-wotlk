#!/usr/bin/env python3
"""
Extracts every creature of the 19 vanilla dungeons (spawned, encounter credit, summoned) into the generated
`CREATURES` block of `source/world/dungeons/<name>.py` (dungeon difficulties E2, WP-G; the rules are in
lib/dungeon_extract.py's docstring). Read-only on the database: SELECTs through a mysql client command.

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/extract_dungeon_creatures.py \\
        --mysql "mysql -h127.0.0.1 -P3307 -uroot -p<password>" [--map 36 ...] [--check]

- `--mysql` defaults to `$DBC_TOOLS_MYSQL` (the replay_diff.py convention); `--database` to `acore_world`.
- `--map` limits the run to those map ids (repeatable); default all 19.
- `--check` writes nothing: it prints, per dungeon, whether the file would change, and exits 1 when any would.

A missing file is created with a heroic-off `dungeon(...)` call. An existing file keeps everything outside the
`# BEGIN GENERATED CREATURES` / `# END GENERATED CREATURES` markers byte for byte, so hand edits (`extra=`, `roles=`,
`skip=`, `heroic=heroic(...)`) survive a rerun; a file without exactly one pair of markers is left alone (error).
Spells come from var/extractors/dbc/Spell.dbc overlaid with the live `spell_dbc` rows, encounters from
DungeonEncounter.dbc overlaid with `dungeonencounter_dbc`.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from lib import dbcfile, dbcfmt, dungeon_extract, replay_diff, state  # noqa: E402

DUNGEON_DIR = TOOL_ROOT / "source" / "world" / "dungeons"
SPELL_COLUMNS = tuple(
    f"{base}_{i}" for base in ("Effect", "EffectAura", "EffectMiscValue", "EffectTriggerSpell") for i in (1, 2, 3)
)


def run_sql(mysql: list[str], database: str, sql: str) -> list[dict]:
    done = subprocess.run(
        [*mysql, "-B", "--default-character-set=utf8mb4", database], input=sql, capture_output=True, text=True,
    )
    if done.returncode:
        raise SystemExit(f"extract_dungeon_creatures.py: mysql failed ({done.returncode}): {done.stderr.strip()}")
    return replay_diff.parse_mysql_batch(done.stdout)


def load_world(mysql: list[str], database: str, maps: list[int]) -> dungeon_extract.World:
    """Every table the extraction reads, for `maps` (SELECTs only)."""
    in_maps = ", ".join(str(m) for m in maps)

    def q(sql: str) -> list[dict]:
        return run_sql(mysql, database, sql)

    spawns = q(f"SELECT `guid`, `id`, `map` FROM `creature` WHERE `map` IN ({in_maps});")
    go_spawns = q(f"SELECT `guid`, `id`, `map` FROM `gameobject` WHERE `map` IN ({in_maps});")
    multispawn: dict[int, set[int]] = {}
    for row in q(f"SELECT m.`spawnId`, m.`entry` FROM `creature_multispawn` m JOIN `creature` c "
                 f"ON c.`guid` = m.`spawnId` WHERE c.`map` IN ({in_maps});"):
        multispawn.setdefault(int(row["spawnId"]), set()).add(int(row["entry"]))
    event_guids = {int(r["guid"]) for r in q("SELECT DISTINCT `guid` FROM `game_event_creature`;")}
    templates = {int(r["entry"]): r for r in q(
        "SELECT `entry`, `name`, `minlevel`, `maxlevel`, `exp`, `rank`, `unit_class`, `type`, `npcflag`, "
        "`flags_extra` FROM `creature_template`;"
    )}
    smart = q(
        "SELECT `entryorguid`, `source_type`, `id`, `link`, `action_type`, `action_param1`, `action_param2`, "
        "`action_param3`, `action_param4`, `action_param5`, `action_param6` FROM `smart_scripts` "
        "WHERE `source_type` IN (0, 1, 9);"
    )
    template_spells: dict[int, set[int]] = {}
    for row in q("SELECT `CreatureID`, `Spell` FROM `creature_template_spell`;"):
        template_spells.setdefault(int(row["CreatureID"]), set()).add(int(row["Spell"]))
    groups = q("SELECT `summonerId`, `summonerType`, `groupId`, `entry` FROM `creature_summon_groups`;")
    spells = {int(r["ID"]): r for r in dbcfile.read_dbc(state.BASE_DBC_DIR / "Spell.dbc", dbcfmt.SPELL)}
    for row in q(f"SELECT `ID`, {', '.join(f'`{c}`' for c in SPELL_COLUMNS)} FROM `spell_dbc`;"):
        spells[int(row["ID"])] = row
    encounter_path = state.BASE_DBC_DIR / dbcfmt.DUNGEONENCOUNTER.dbc_filename
    if not encounter_path.is_file():
        raise SystemExit(f"extract_dungeon_creatures.py: {encounter_path} is missing (copy it from the worldserver's "
                         f"DBC directory)")
    encounters = {int(r["ID"]): r for r in dbcfile.read_dbc(encounter_path, dbcfmt.DUNGEONENCOUNTER)}
    for row in q("SELECT `ID`, `MapID`, `Difficulty` FROM `dungeonencounter_dbc`;"):
        encounters[int(row["ID"])] = row
    instance = {int(r["entry"]): r for r in q(
        "SELECT `entry`, `creditType`, `creditEntry` FROM `instance_encounters`;"
    )}
    return dungeon_extract.World(
        creature_spawns=spawns, gameobject_spawns=go_spawns, templates=templates, multispawn=multispawn,
        event_guids=event_guids, encounters=list(encounters.values()), instance_encounters=instance,
        smart_scripts=smart, template_spells=template_spells, summon_groups=groups, spells=spells,
    )


def file_text(path: Path, extract: dungeon_extract.DungeonExtract, stem: str) -> str:
    if not path.is_file():
        return dungeon_extract.render_new_file(extract, stem)
    return dungeon_extract.replace_block(path.read_text(), dungeon_extract.render_block(extract))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--mysql", default=os.environ.get("DBC_TOOLS_MYSQL"), help="mysql client command")
    parser.add_argument("--database", default="acore_world")
    parser.add_argument("--map", type=int, action="append", dest="maps", help="map id (repeatable); default all 19")
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 when a file would change")
    parser.add_argument("--out-dir", type=Path, default=DUNGEON_DIR)
    args = parser.parse_args(argv)
    if not args.mysql:
        parser.error("--mysql (or $DBC_TOOLS_MYSQL) is required")
    maps = args.maps or sorted(dungeon_extract.VANILLA_DUNGEONS)
    unknown = [m for m in maps if m not in dungeon_extract.VANILLA_DUNGEONS]
    if unknown:
        parser.error(f"not a vanilla dungeon map: {unknown}")
    world = load_world(shlex.split(args.mysql), args.database, maps)
    changed, failed = [], []
    for map_id in maps:
        name, stem = dungeon_extract.VANILLA_DUNGEONS[map_id]
        extract = dungeon_extract.extract(world, map_id, name)
        path = args.out_dir / f"{stem}.py"
        counts = extract.counts()
        summary = ", ".join(f"{n} {k}" for k, n in counts.items() if n)
        try:
            text = file_text(path, extract, stem)
        except dungeon_extract.BlockError as error:
            print(f"ERROR: {path.name}: {error}")
            failed.append(path)
            continue
        old = path.read_text() if path.is_file() else None
        state_text = "unchanged" if text == old else ("new" if old is None else "changed")
        print(f"{name} (map {map_id}) -> {path.name}: {state_text}; {summary}")
        if extract.missing_templates:
            print(f"note: {name}: entries with no creature_template row skipped: {extract.missing_templates}")
        if text != old:
            changed.append(path)
            if not args.check:
                path.write_text(text)
    if failed:
        return 2
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    sys.exit(main())
