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

**mod-dungeon-difficulties is required too** (Blackrock Spire WP-KT-B1). The kit's flex wrapper
(`src/Kit/DungeonKitFlex.cpp`) and `SummonWave` call its flex scaler (`FlexScale.h`, `DungeonDifficulties::Flex`); the
same `.cmake` stops the configure when `modules/mod-dungeon-difficulties/src/FlexScale.h` is missing or the module is
disabled. The scaler lands with hiafi/mod-dungeon-difficulties branch `feat/flex-blackrock-spire` (off main 8418cda):
merge that PR before (or with) the core PR that brings Blackrock Spire, and check the checkout before an image build.

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
| `src/Kit/DungeonKit*.h` (Math, State, Arena, Logic, Ids, Floor, Flow) | The shared kit's pure part (`DungeonKit`) |
| `src/Kit/DungeonKit.{h,cpp}` | Kit engine glue: AI factory, `RefFlat`, `ImpactThenLinger`, `JumpTo`, ... |
| `src/Kit/DungeonKitFloor.h` | Pure: `FloorPath`, floor spot picks, `PuddleSet` (union, merge rule, area) |
| `src/Kit/DungeonKitFlow.h` | Pure: `WeightedSplit`, `CappedWaveSize`, `CastQueue`, `HoldBook`, percent encoding |
| `src/Kit/DungeonKitFields.{h,cpp}` | Engine: `PuddleField`, `RegistryHit`, `FollowThenLand`, `SummonWave`, ... |
| `src/Kit/DungeonKitSpells.cpp` | `spell_dungeon_refflat_damage` / `_periodic`: generic percent spells |
| `src/Kit/DungeonKitWallLogic.h` | Pure: walls, 5 yd placement, crossings, strike book, outright kill, dispensing |
| `src/Kit/DungeonKitWalls.{h,cpp}` | Engine: `LethalWall(s)`, `FinishLethalStrike`, `RelicDispenserAI`, `Dispense` |
| `src/Kit/DungeonKitFlexRules.h` | Pure: flex 5-10 rules: `Flex::TargetCount`, `HealthAt`, `LootRolls`, `TankSwapOn`, `LootBits` |
| `src/Kit/DungeonKitFlex.{h,cpp}` | Engine: DD's scaler for scripts: `Flex::Count`, `OnPull`, `SetFlexLoot`, `SetHealth` |
| `src/Kit/DungeonKitChaseLogic.h` | Pure: `ChaseClock`, `CrawlClock`, `FallCatchBook` |
| `src/Kit/DungeonKitChase.{h,cpp}` | Engine: `Chaser`, `CrawlPickups` (pickups that crawl to a goal), `FallWatch` |
| `src/Kit/DungeonKitFrontLogic.h` | Pure: rolling front plans: timing, ring slices, gaps off pools, carrier spots |
| `src/Kit/DungeonKitFronts.{h,cpp}` | Engine: `FrontDirector` (ring and wall sequences on BM's fronts), `PoolsOf` |
| `src/Kit/DungeonKitRingLogic.h` | Pure: the ring wall (band, crossings, `RingWatch`, push-out plan, grace) |
| `src/Kit/DungeonKitRing.{h,cpp}` | Engine: `LethalRing(s)` (a lethal ring wall with a push-out), `RingInside` |
| `src/Kit/ArenaGuard.{h,cpp}` | The arena guard (grips, hold, leash), `LeashPreset`, cell `Confinement` |
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
| `src/Scholomance/ScholomanceRework.h` | Pure: Scholomance entries, states, data ids, rooms, points, arenas, save |
| `src/Scholomance/instance_scholomance_rework.cpp` | Instance (stock name, replaced at load; Kirtonos kept) |
| `src/Scholomance/ScholomanceKit.{h,cpp}` | Scholomance glue: the grip-less leash, Gandling's reveal, Passing Grades |
| `src/Scholomance/SoloLesson{.h,.cpp,Logic.h}` | Detention's solo lesson interface and per-room factories |
| `src/Scholomance/ScholomanceTestCommand.{h,cpp}` | The `.dbtest scholo` shell and its `instance` table |
| `src/Scholomance/boss_<name>_rework.cpp`, `<Boss>Logic.h` | One pair per Scholomance boss WP; S12/S13 hard modes |
| `src/Scholomance/RasFight.h` | Ras's hard mode hooks into his fight (S4 -> S12) |
| `src/Scholomance/MaliciaFight.h` | Malicia's examiner hooks for the Graduate Exam (S5 -> S13) |
| `src/Scholomance/GandlingFight.h` | Gandling's fight engine for the Graduate Exam: modes, region (S11 -> S13) |
| `src/Scholomance/ras_hard_mode.cpp`, `RasHardModeLogic.h` | Ras's hard mode, the Torn Keepsake (S12) |
| `src/Scholomance/graduate_exam.cpp`, `GraduateExamLogic.h` | Gandling's hard mode, the Graduate Exam (S13) |
| `src/Scholomance/GraduateExam.h` | The Graduate Exam's driver as the instance owns it: grade auras, the gauntlet |
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
| `src/Stratholme/StratholmeRework.h` | Pure: entries, 17 states, data ids, texts, slices, points, arenas, save |
| `src/Stratholme/instance_stratholme_rework.cpp` | Instance (stock name, replaced at load; Jarien, Sothos on 2, 3) |
| `src/Stratholme/StratholmeKit.{h,cpp}` | Stratholme glue: the leash options (the kit's `LeashPreset`) |
| `src/Stratholme/StratholmeTestCommand.{h,cpp}` | The `.dbtest strat` shell and its `instance` table |
| `src/Stratholme/boss_<name>_rework.cpp`, `<Boss>Logic.h` | One pair per Stratholme boss WP; S8/S15 hard modes |
| `src/Stratholme/DathrohanFight.h` | Balnazzar's hard mode hooks (S7 to S8, the `BaronFight.h` pattern) |
| `src/Stratholme/hard_mode_items.cpp` | Balnazzar and Baron hard mode item scripts, the Condemned damage hook |
| `src/Stratholme/StratholmeHardModeItemsLogic.h` | Pure: Stratholme item effect ids (205660-205672), shares, picks |
| `src/BlackrockSpire/BlackrockSpireRework.h` | Pure: entries, 28 states, data ids, slices, points, arenas, save |
| `src/BlackrockSpire/instance_blackrock_spire_rework.cpp` | Instance (stock name, replaced at load; stock slots kept) |
| `src/BlackrockSpire/BlackrockSpireKit.{h,cpp}` | Glue: leash options, `OnBossPull` (flex count, pull line) |
| `src/BlackrockSpire/BlackrockSpireTestCommand.{h,cpp}` | The `.dbtest brs` shell and its `instance` table |
| `src/BlackrockSpire/boss_<name>_rework.cpp`, `<Boss>Logic.h` | One pair per boss WP; B9/B15 hard modes |
| `src/BlackrockSpire/WyrmthalakFight.h` | B8's hooks for the war horn: the per-pull `WyrmthalakHardMode` object, its factory |
| `src/BlackrockSpire/wyrmthalak_hard_mode.cpp`, `WyrmthalakHardModeLogic.h` | B9 war horn on B8's hooks; `.dbtest brs warhorn` |
| `src/BlackrockSpire/drakkisath_hard_mode.cpp`, `DrakkisathHardModeLogic.h` | B15 General's Army; `.dbtest brs army` |
| `src/BlackrockSpire/UrokShards.h` | B5's Stolen Magic shard and Stolen Power, shared by Urok and the war horn (WT10) |
| `src/BlackrockSpire/hard_mode_items.cpp` | Wyrmthalak and Drakkisath hard mode item scripts: the Ward's stacks, the Champion's Mark |
| `src/BlackrockSpire/BlackrockSpireHardModeItemsLogic.h` | Pure: Blackrock Spire item effect ids (206800-206811), stack and award rules |
| `src/BlackrockDepths/hard_mode_items.cpp` | Encore, Incendius, Argelmach, Emperor hard mode item scripts, Theldren's damage hook |
| `src/BlackrockDepths/BlackrockDepthsHardModeItemsLogic.h` | Pure: Blackrock Depths item effect ids (206830-206853), shares, picks, beam |
| `src/DungeonSets/haunted_set_bonuses.cpp` | Haunted set bonus scripts (10 sets x 3 and 5 pieces) and their hooks |
| `src/DungeonSets/HauntedSetLogic.h` | Pure: Haunted set bonus ids (205700-205793), script numbers, rolls, picks |
| `src/DungeonSets/molten_set_bonuses.cpp` | Molten set bonus scripts (10 sets x 3 and 5 pieces): Heat, eruptions, cooldown hooks |
| `src/DungeonSets/MoltenSetLogic.h` | Pure: Molten set bonus ids (206900-206993), Heat counts and gains, the Cooldown Haste list mirror |
| `src/Generated/ItemSpellCopies.h` | Generated by dbc-tools (IV10): item effect spell copies per tier, `Resolve` |
| `tests/run.sh` | Host tests (g++ and clang++), no server build needed |
| `tests/dungeon_kit_test.cpp` | The shared kit's pure part, and the Deadmines aliases' parity with it |
| `tests/kit_flex_parity_test.cpp` | The kit's flex rules against DD's `FlexMath.h` (run when DD's source is found; `DD_SRC`) |
| `tests/kit_test.cpp`, `tests/<boss>_test.cpp` | Suites for the Deadmines kit and each boss's `<Boss>Logic.h` |
| `tests/stratholme_test.cpp`, `tests/strat_<boss>_test.cpp` | The Stratholme skeleton and each boss |
| `tests/blackrock_spire_test.cpp`, `tests/brs_<boss>_test.cpp` | The Blackrock Spire skeleton and each boss |

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

## Kit: the flex scaler and the wave 1 movers (Blackrock Spire WP-KT-B1)

Flex dungeons (DD `DungeonDifficulties.Flex.Maps`, Blackrock Spire first): the player count is read at each pull and
held for the fight, health x (1 + 0.25 x (N - 5)), target counts double at 6 or more, two loot rolls at 10, a taunt
swap only at 10, damage never scales. DD owns the count, the hold and the health; a boss calls the kit:

```cpp
void JustEngagedWith(Unit* who) override
{
    BossAI::JustEngagedWith(who);
    _n = DungeonKit::Flex::OnPull(me, _hardMode);   // holds the count, scales health, sets LootMode 4 (and 8) at 10
}
uint8 const targets = DungeonKit::Flex::TargetCount(_n, 1, 2);    // pure; Logic headers too
if (DungeonKit::Flex::TankSwapOn(_n)) { /* the taunt swap entry */ }
DungeonKit::Flex::SetHealth(me, kHardModeHealth, true);           // script-set health: the 5-player base
```

The flex loot bits are set at the pull, never in `JustDied` (the corpse loot is filled before it). Kit adds from
`SummonWave` take the encounter's count at their own pull; a `WaveSpec::health` on a flex map is their 5-player base.
Off a flex map the same calls give 5 players, unscaled health and no flex loot bits.

The movers (`DungeonKitChase.h`; each is owned by one AI: Update from `UpdateAI`, Stop / Clear / Disarm from
`Reset`, `JustDied` and `EnterEvadeMode`):

- `Chaser`: a unit runs at one target at a set speed (slows still apply), taunt immune and fixated; a toss or a stun
  stops it at least 1 s; a new pick when its target dies, or every N s in no-threat mode; `onArrive` ends the chase
  (or fires per contact with `endOnArrive = false`). Zigris's sheep, the Hatcher, the Hunt, whelps, Broodlings.
- `CrawlPickups`: walk-over pickups on a unit of their own: a telegraph-only Soak anchored on it (MissedSoak Never),
  taken on touch by an eligible player (`onPick`), crawling along the floor to a goal unit or point after a wait
  (`onReach`); `SetGoal` moves every live one to a new goal. `order` (optional) sets the Soak's claim order for the
  bots only: its `capStacks` stops bots claiming while `who` still lets anyone touch it. Urok's shards, Wyrmthalak's
  Stolen Boulders.
- `FallWatch`: catches players and their pets and guardians (no totems, no charmed mobs) inside a region a set height
  under a deck before they land (`onCatch`; a caught player's fall start is reset, so the jump back deals no fall
  damage), once per grace. Omokk's Pit Drop.

## Kit: rolling fronts and the ring wall (Blackrock Spire WP-KT-B2)

The script side of mod-boss-mechanics' rolling fronts (BM README "Rolling fronts"; `Mechanic::ConeFront`,
`LineFront`, `FrontSafe`). BM registers and judges one front; `DungeonKit::FrontDirector` (`DungeonKitFronts.h`) runs
a sequence of them on a clock the AI drives (`Update` from `UpdateAI`, `Clear` from `Reset`, `JustDied`,
`EnterEvadeMode`: it cancels every registered front and safe slot and despawns the carriers):

- `StartRings(owner, apex, RingSequence)`: Emberseer's Furnace Pulse rings. The plan (`Fronts::PlanRings`) gives each
  ring its launch (first warn, then the spacing), its slice (turned clockwise per ring) and its registration (SP: a
  ring's slice shows as the ring before it launches; `revealAtPreviousLaunch = false` shows them all at once). Each
  ring gets a `FrontSafe` (the bot tank leads the boss into the slice) unless `safeSlot = false`.
  `Fronts::LastPassMs` / `FirstReachMs` time the posts (EM6: flare once the last ring passed 21 yd; the next pulse
  waits so its first ring cannot reach 15 yd first).
- `StartWalls(owner, start, WallSequence)`: Rend's Freezing Sweep. One gap per wall inside the usable span
  (`gaps.spanYd`: the arena's narrow strip), off every live pool (`pools`, read at each wall's registration;
  `PoolsOf(puddleField)`); a later wall's gap on the other side and within 20 yd of the previous one. When no lane is
  pool-free (several 6 yd pools across a 40 yd strip often cover it), the lane with the least floor under pools is
  taken and logged (`poolSqYd=`): the side and the distance rules outrank a pool-free lane.
- Damage, school, Weakened, rider and tag are the boss's (`decorate(ref, index)`); `within` gives each front the room's
  bounds (outside them every spot reads safe to the solver). Optional carriers (`FrontCarrierSpec`: an invisible
  entry with an aura) spawn at each launch along the band and move with it; `onLaunch` is for the cast visual.

The ring wall (`DungeonKitRing.h`), the circle form of `LethalWall` for Drakkisath's Champion's Challenge:
`LethalRing(owner, spec)` / `LethalRings::Add` closes a lethal band (registry `Donut`, `.Lethal()`) round
`spec.center`, pushes out everyone but `keepIn` at once (a knockback to 3 yd past the band, no damage; pets too,
never totems), arms after 1.5 s, and for its life (12 s) strikes whoever stands in the band or crosses it (an outright
kill, as the arena walls). A unit the kit pushed flies over the band under a grace; with `pushDuringLife` anyone not
kept in found inside the disc later is pushed out again. `RingInside(spec)` is the challenger bot's `Within` bounds.
`carrierEntry` / `carrierAura` spawn the ring's look (despawned by `LethalRings::Clear`). With `pets = false` (the
duel ring, by ruling) pets and guardians are never struck, and the ring declares `.SparesPets()`, so a bot that owns a
pet keeps no pet margin from it (Blackrock Spire F-3: with one, a pet owner found no spot inside the ring clear of the
Thunderclap). `LethalWall` with `pets = false` declares it the same way (none does today).

Tests: `tests/kit_fronts_test.cpp` (pure plans and the ring rules) and `tests/kit_fronts_parity_test.cpp` (the
mirrored BM rules, run when `BM_SRC` or `../mod-boss-mechanics/src` has `MechanicFront.h`).
