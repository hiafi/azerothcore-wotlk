# mod-content-gate

The realm's content switch. One `.conf` says what is open; everything the gate covers is **closed unless listed**:
every dungeon and raid map (per difficulty), battleground and arena, outdoor PvP zone, Outland and Northrend. Stock
holidays run on their stock schedule unless closed by the conf. Content that belongs to an unlock (quests, spawns,
world bosses, meeting stones) is world-DB data grouped in **bundles** that open with their switch.

It replaces mod-progression (plan: `.agents/plans/progression-slim/`). It also carries the content scripts kept from
mod-progression: Onyxia at level 60 / 40 players, the Ahn'Qiraj gong and gate, Mark of Kazzak and the Nightbane summon.

## Files

| Path | What |
| --- | --- |
| `conf/content_gate.conf.dist` | The switch, with the day-one set (copy to `etc/modules/content_gate.conf`) |
| `data/sql/db-world/base/content_gate_tables.sql` | Bundle tables (module SQL, applied by db-import) |
| `src/ContentGateRules.h` | Pure rules: conf parsing, mode flags, closed set, bundles, diffs, zones (host-tested) |
| `src/ContentGate.{h,cpp}` | Engine glue: DisableMgr feed, bundle loader, event control, watchdog, status |
| `src/ContentGateScripts.cpp` | Hooks (one class per script type), continent guard, `.gate` commands |
| `src/scripts/` | Ported mod-progression scripts (author: Revision <tkn963@gmail.com>, GPL-2) |
| `tests/run.sh` | Host tests (g++ and clang++), no server build needed |

## How it gates

The module feeds `DisableMgr` **in memory** (`DisableMgr::AddDisable`); it never writes the `disables` table.

- **Boot:** `DatabaseScript::OnAfterDatabaseLoadCreatureTemplates` runs right after `LoadDisables` and before quests,
  game events and outdoor PvP load. It adds one map disable per closed dungeon/raid map (the closed difficulty flags),
  the closed outdoor PvP types, the closed events and the closed bundles' member disables. Battlegrounds are added in
  `OnBeforeWorldInitialized`, after the battleground templates are built, so a closed battleground keeps its template
  and can be opened live.
- **`.reload config`:** `DisableMgr` has no remove, so on the next world tick the module calls `LoadDisables()` and
  `CheckQuestDisables()` (the DB rows come back), adds its new closed set on top and starts every newly opened event
  that is due (bundle events are always due). Closing an event stops it (DisableMgr does that), which despawns its
  bundle spawns.
- **`.reload disables`** wipes the in-memory entries. A watchdog (`ContentGate.WatchdogMs`, default 5 s) looks up a
  sentinel loot disable on an impossible item id; when it is gone it re-adds the set and logs a warning.
- **DB rows win.** `AddDisable` never overwrites an existing key, so a `disables` row with the same key as a module
  entry decides that key. The cutover deletes the rows the module owns; `.gate status` lists any leftover as a
  conflict.
- **Engine limits:** outdoor PvP and Wintergrasp are read at boot only; quests opened live miss the boot quest
  post-processing until a restart. `.gate status` lists these as "Restart needed".

Everything that writes DisableMgr or GameEventMgr runs on the world thread (boot hooks or `WorldScript::OnUpdate`,
which runs after the map threads finished their tick).

### Continents

Map 530 also holds the Blood Elf and Draenei starting zones and cities, so Outland cannot be a map disable. The
continent guard is a `PlayerScript`:

- `OnPlayerBeforeTeleport` refuses a non-GM teleport into a closed continent: map 571 while Northrend is closed; map
  530 into an Outland-proper zone (Hellfire, Zangarmarsh, Terokkar, Nagrand, Blade's Edge, Netherstorm, Twisting
  Nether, Shadowmoon, Auchindoun, Shattrath, Isle of Quel'Danas) while Outland is closed. That covers the Dark Portal areatrigger, portals,
  hearthstones and summons. Players and bots alike (bots are `SEC_PLAYER`); GMs pass with
  `RBAC_PERM_SKIP_CHECK_DISABLE_MAP`, the same permission that skips map disables.
- **Northrend transports:** the ship's map hop calls `TeleportTo(..., TELE_TO_NOT_LEAVE_TRANSPORT)`; a refusal
  would leave the passenger at sea, so the guard puts them back on the old-world dock of that transport (Menethil,
  Tirisfal tower, Orgrimmar tower, Stormwind harbor), or at their homebind for an unknown transport. Northrend is
  gated by this hook, not by a map 571 disable, because a map disable refuses the hop before the hook runs.
- `OnPlayerUpdateZone` is the backstop (login inside a closed zone, a path the teleport check missed): one second
  later the player is sent to the Blasted Lands side of the Dark Portal (Outland) or to their homebind (Northrend; the
  faction capital if the homebind itself is behind a gate).
- `ContentGate.Wintergrasp.FollowNorthrend = 1` keeps `Wintergrasp.Enable = 2` (all processing off) while Northrend is
  closed.

## Bundles

A bundle is one row in `content_gate_bundle` plus member rows in `content_gate_bundle_disable`:

```sql
content_gate_bundle (name VARCHAR(32) PK, gameEvent TINYINT UNSIGNED, opensWith VARCHAR(64), comment)
content_gate_bundle_disable (bundle VARCHAR(32), sourceType TINYINT UNSIGNED, entry INT UNSIGNED, comment,
                             PRIMARY KEY (bundle, sourceType, entry))
```

- `opensWith`: `map:<id>:<mode>` (open when that map difficulty is open), `bg:<id>`, `outland`, `northrend`, or empty
  (opened only by name in `ContentGate.Open.Bundles`). A bundle named in `Open.Bundles` is open regardless.
- `gameEvent`: an always-on custom `game_event` (start in the past, end far in the future, `occurence = length`,
  `holiday = 0`, `world_event = 0`) whose `game_event_creature` / `game_event_gameobject` rows are the bundle's spawns
  (`phaseMask = 1`). While the bundle is closed the module disables the event, so the spawns are gone. `eventEntry`
  is `TINYINT UNSIGNED` in this schema: bundle events use ids 200-255. One event per bundle.
- Members (`sourceType` 1 quest, 4 achievement criteria, 10 loot) are disabled while the bundle is closed. A member
  must not also have a row in `disables`.
- **Fails closed.** An event in the block 200-255 that no loaded bundle owns is kept closed whatever the conf says. If
  the bundle tables are missing (the module SQL was not applied), every event 200-255 is kept closed, an ERROR is
  logged and `.gate status` shows it; the first cutover SQL file also probes the tables, so such an import stops
  before it changes anything.
- Doors in front of a gated instance need no bundle: the instance's map gate already blocks entry.

Examples of the day-one data (rows ship as pending world SQL, not with the module): `molten_core` opens with
`map:409:N` (Lothos Riftwaker, Core Fragment), `zul_gurub` with `map:309:N` (the Yojamba camp and the world bosses
Azuregos and Lord Kazzak), `karazhan` with `map:532:N`. `.gate reload` re-reads the tables.

Onyxia's Lair (249) keeps two raid difficulty rows (10N and 25N, both 40 players): open it with `249:*` in
`ContentGate.Open.Instances.*`, not `249:N`, or a leader on 25-player raid difficulty is refused. The `onyxia` bundle
(`map:249:N`) opens with either.

Arenas: the arena season events (75, 76, 55-60) follow bg 6. The core force-starts the current season's event at
boot and on `.arena season set` (that skips the disable), so while 6 is closed the module stops it again after boot
and on every watchdog check; opening 6 starts the current season's event. Any closed event a GM starts with
`.event start` is stopped the same way.

## Conf

See `conf/content_gate.conf.dist`; every key is documented there. Keys are read once per (re)load. The conf loader
ignores keys that are not in the `.dist`, so a new `ContentGate.Open.Instances.*` key must be added to the `.dist`.
Other modules can ask the gate whether a map difficulty is open: `sContentGate->IsInstanceOpen(mapId, difficulty)`.

## Commands (GM, console too)

- `.gate status`: open instances, closed counts, battlegrounds, outdoor PvP, continents, Wintergrasp, closed events,
  every bundle (open/closed, event active, members), conf and bundle errors, DB conflicts, restart notes, sentinel and
  watchdog state.
- `.gate reload`: re-read the bundle tables and re-apply the cached conf on the next world tick (conf edits need
  `.reload config`).

## Ported scripts

- `instance_onyxias_lair`, `boss_onyxia` (`instance_template` 249, `creature_template` 10184): level 60, 40 players.
  Same script names as core's, so they replace them (modules load after core).
- `go_scarab_gong`, `go_scarab_gate` (`gameobject_template` 180717, 176146-176148): the AQ gate opening. The gate
  stays shut until Ahn'Qiraj (509 or 531) is open in the gate.
- `spell_mark_of_kazzak` (`spell_script_names` 21056): vanilla Lord Kazzak (ZG bundle).
- `spell_summon_nightbane` (`spell_script_names` 31116): inert while Karazhan is closed.

These keep mod-progression's function and class names on purpose: building this module next to mod-progression
fails at link time (duplicate `AddSC_*`) instead of silently mixing two copies. Never put mod-progression back into
`modules/`.

## Tests

```bash
modules/mod-content-gate/tests/run.sh          # g++ and clang++, whichever exist; CXX=... picks one
```
