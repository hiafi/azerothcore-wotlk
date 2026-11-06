# mod-dungeon-bosses

Reworked dungeon bosses for this realm: boss, add, gameobject and instance scripts built on mod-boss-mechanics'
registry (telegraphs, hitboxes, bot data). The first dungeon is the Deadmines (the Deadmines Pilot,
`.agents/plans/deadmines-pilot/`); Shadowfang Keep and Scholomance follow in their own `src/<Dungeon>/` folders.

The reworked scripts cannot live in `src/server/scripts/`: that target cannot see module headers, and the stock files
there are upstream-owned. This module is core-tracked (whitelisted in `.gitignore`, like mod-dpssim and
mod-content-gate) and ships in the same core PR as its data.

## Dependency

**mod-boss-mechanics is required.** Every boss script includes `BossMechanics.h` (through the `modules` target's
`PUBLIC_INCLUDES`). `mod-dungeon-bosses.cmake` stops the CMake configure with a clear message when mod-boss-mechanics is
missing or disabled; to build without it, disable this module too (`-DDISABLED_AC_MODULES="mod-dungeon-bosses"`).

## Binding: new script names, data does the rest

The stock scripts stay untouched and inert. Data rebinds the dungeon to this module's scripts under new names:

- `instance_template` map 36 -> `instance_deadmines_rework` (core pending SQL);
- each boss's `creature_template.ScriptName` -> `boss_<name>_rework`, `AIName` emptied (apps/dbc-tools
  `source/npcs/deadmines/`, one file per boss);
- the boss-kit creatures (300420-300449) and gameobjects (301000-301099) carry `npc_dm_*` / `go_dm_*`.

AI factories (`RegisterDeadminesReworkCreatureAI`) only build an AI inside an instance bound to
`instance_deadmines_rework`. The module ships no SQL of its own: every row goes through dbc-tools or core pending SQL,
so db-import and the dbc-tools replay see one history.

## Layout

| Path | What |
| --- | --- |
| `mod-dungeon-bosses.cmake` | Configure-time dependency check (included by `modules/CMakeLists.txt`) |
| `src/dungeon_bosses_loader.cpp` | `Addmod_dungeon_bossesScripts()`: calls every boss file's `AddSC_` |
| `src/Deadmines/DeadminesRework.h` | Pure: entries, boss states, data ids, text groups, spell slices, measured frames |
| `src/Deadmines/DeadminesKitMath.h` | Pure: `NH<T>` tuning, `RefFlatValue`, map-plane geometry, the save string |
| `src/Deadmines/DeadminesKit.{h,cpp}` | Engine glue: `RefFlat`, `ImpactThenLinger`, `CastBar`, `IsHeroicMap`, ... |
| `src/Deadmines/DeadminesTestCommand.{h,cpp}` | The `.dmtest` GM command shell and its per-boss hook |
| `src/Deadmines/instance_deadmines_rework.cpp` | Instance script: boss states, doors, VanCleef, Johnson's roll |
| `src/Deadmines/boss_<name>_rework.cpp` | One file per boss work package (boss, its adds, its `.dmtest` subcommands) |
| `src/Deadmines/<Boss>Logic.h` | Pure, host-testable part of one boss (spell ids, tuning, timers, picks, geometry) |
| `tests/run.sh` | Host tests (g++ and clang++), no server build needed |
| `tests/kit_test.cpp`, `tests/<boss>_test.cpp` | Suites for the kit and each boss's `<Boss>Logic.h` |

## Adding a dungeon

1. `src/<Dungeon>/<Dungeon>Rework.h` (pure ids and frames), an instance script under a new name
   (`instance_<dungeon>_rework`), and one `boss_<name>_rework.cpp` + `<Boss>Logic.h` per boss. Reuse the Deadmines kit
   pattern; move a helper to a shared `src/Common/` folder when a second dungeon needs it.
2. Declare and call each `AddSC_` in `src/dungeon_bosses_loader.cpp`.
3. Add the test files to `tests/run.sh` (and an `-I` for the new folder).
4. Data: an `ids.yaml` reservation; dbc-tools declarations (spells, new creatures, `creature_template_columns` with the
   new `ScriptName` and `AIName ''`, heroic `extra=` / `overrides` in `source/world/dungeons/<name>.py`); core pending
   SQL for `instance_template`, gameobjects, `smart_scripts` removals, spawns and `creature_text`.

## Tests

```bash
modules/mod-dungeon-bosses/tests/run.sh        # every suite, g++ and clang++
CXX=clang++ modules/mod-dungeon-bosses/tests/run.sh
```
