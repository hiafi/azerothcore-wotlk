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
| `src/Kit/DungeonKit*.h` (Math, State, Arena, Logic, Ids) | The shared dungeon kit's pure part (`DungeonKit`) |
| `src/Kit/DungeonKit.{h,cpp}` | Kit engine glue: AI factory, `RefFlat`, `ImpactThenLinger`, `JumpTo`, ... |
| `src/Kit/ArenaGuard.{h,cpp}` | The arena guard (pull grip, grip back, hold, leash) and cell `Confinement` |
| `src/Kit/DungeonTestCommand.{h,cpp}` | The generic `.<x>test` GM command shell, one per dungeon |
| `src/Deadmines/DeadminesRework.h` | Pure: entries, boss states, data ids, text groups, spell slices, measured frames |
| `src/Deadmines/DeadminesKitMath.h` | Pure: `DeadminesKit` = the kit's names, plus Johnson's roll and the save string |
| `src/Deadmines/DeadminesKit.{h,cpp}` | Engine glue: the kit's names, `DeckFrame()`, the factory macros |
| `src/Deadmines/DeadminesTestCommand.{h,cpp}` | The `.dmtest` shell (the kit's, for map 36) and its per-boss hook |
| `src/Deadmines/instance_deadmines_rework.cpp` | Instance script: boss states, doors, VanCleef, Johnson's roll |
| `src/Deadmines/boss_<name>_rework.cpp` | One file per boss work package (boss, its adds, its `.dmtest` subcommands) |
| `src/Deadmines/<Boss>Logic.h` | Pure, host-testable part of one boss (spell ids, tuning, timers, picks, geometry) |
| `src/Deadmines/hard_mode_items.cpp` | VanCleef hard mode item effects: Powder Keg Fuse, Blackguard's Signet, Lantern |
| `src/Deadmines/HardModeItemsLogic.h` | Pure: their spell and creature ids (205400-205409, 300430) |
| `src/Scholomance/scholomance_items.cpp` | Scholomance item scripts: Phylactery, Bonechill, Papers, Portal Rod |
| `src/Scholomance/ScholomanceItemsLogic.h` | Pure: Scholomance item effect ids (205620-205642), tally, swap rules |
| `src/ShadowfangKeep/sfk_hard_mode_items.cpp` | Arugal hard mode item scripts: the Shadow Tome's Voidwalker |
| `src/ShadowfangKeep/SfkHardModeItemsLogic.h` | Pure: Shadowfang Keep item effect ids (205600-205604, 300460) |
| `src/ShadowfangKeep/ShadowfangKeepRework.h` | Pure: SFK entries, states, data ids, texts, slices, points, arenas |
| `src/ShadowfangKeep/instance_shadowfang_keep_rework.cpp` | Instance (stock name, replaced at load; Hummel kept) |
| `src/ShadowfangKeep/ShadowfangKeepTestCommand.{h,cpp}` | The `.sfktest` shell, its `instance` and `cells` tables |
| `src/ShadowfangKeep/boss_<name>_rework.cpp`, `<Boss>Logic.h` | One pair per SFK boss WP; S10 `face_him_alone.cpp` |
| `src/ShadowfangKeep/MeatHook.{h,cpp}` | Meat Hook (Razorclaw RC1, Silverlaine's Echo of Razorclaw) |
| `src/ShadowfangKeep/Hunt.{h,cpp}`, `HuntLogic.h` | The Hunt chase (Odo OD1, Silverlaine's Echo of Odo) |
| `src/ShadowfangKeep/SoulDrain.h` | Soul Drain (Rethilgore, Silverlaine's Echo of Rethilgore) |
| `src/ShadowfangKeep/LairPrisoner.h` | The lair prisoner's gossip hooks (Arugal S9, Face Him Alone S10) |
| `src/Stratholme/hard_mode_items.cpp` | Balnazzar and Baron hard mode item scripts, the Condemned damage hook |
| `src/Stratholme/StratholmeHardModeItemsLogic.h` | Pure: Stratholme item effect ids (205660-205672), shares, picks |
| `src/DungeonSets/haunted_set_bonuses.cpp` | Haunted set bonus scripts (10 sets x 3 and 5 pieces) and their hooks |
| `src/DungeonSets/HauntedSetLogic.h` | Pure: Haunted set bonus ids (205700-205793), script numbers, rolls, picks |
| `src/Generated/ItemSpellCopies.h` | Generated by dbc-tools (IV10): item effect spell copies per tier, `Resolve` |
| `tests/run.sh` | Host tests (g++ and clang++), no server build needed |
| `tests/dungeon_kit_test.cpp` | The shared kit's pure part, and the Deadmines aliases' parity with it |
| `tests/kit_test.cpp`, `tests/<boss>_test.cpp` | Suites for the Deadmines kit and each boss's `<Boss>Logic.h` |

## Adding a dungeon

1. `src/<Dungeon>/<Dungeon>Rework.h` (pure ids and frames), an instance script under a new name
   (`instance_<dungeon>_rework`), and one `boss_<name>_rework.cpp` + `<Boss>Logic.h` per boss, on the shared kit
   (`src/Kit/`): `RegisterDungeonReworkCreatureAI(ai, kInstanceScriptName)`, `DungeonKit::NH`, an `ArenaGuard` per
   boss, a `.<x>test` shell (`DungeonTest::RegisterDungeon`), `FormatStates` / `ParseStates` for the save. A helper a
   second dungeon needs moves into `src/Kit/` (generic name, a test in `tests/dungeon_kit_test.cpp`). dbc-tools: the
   builders and constants of `apps/dbc-tools/lib/dsl/dungeon_kit.py`.
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
