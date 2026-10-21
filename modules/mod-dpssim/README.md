# mod-dpssim

DPS simulator daemon for this fork. First-party module, tracked directly in this repo (see the
`.gitignore` exception for `modules/mod-dpssim`) — not a general-purpose AzerothCore catalogue
module, bespoke to this server's custom stat system (Versatility/Mastery/Cooldown Haste/Proc
Chance) and the core patches it depends on.

- Design doc: [`docs/dps-sim-module.md`](../../docs/dps-sim-module.md)
- Implementation plan: [`.agents/plans/dps-sim-module/dps-sim-module.PLAN.md`](../../.agents/plans/dps-sim-module/dps-sim-module.PLAN.md)

## Status

M1 (Harness) in progress. Currently a skeleton: `DpsSimWorldScript::OnDpsSimRun()` smoke-tests
the sim-mode boot branch and the two Phase 1 core patches (RNG seed, sim-clock override) but does
not yet run an actual sim job. See the plan doc's Phase 1 task list for what's next
(`SimDaemon`/`SimActor`/`SimTarget`/`SimClock`/`EventRecorder`, the known-value/timestep/
determinism/accelerated-clock tests).

## Enabling

Set `DpsSim.Enabled = 1` in this process's `worldserver.conf` (see `conf/dpssim.conf.dist`).
**Never enable this on a config also meant to serve real players** — sim mode skips the auth/
world socket listeners entirely and is never a connectable realm.

## Hunters and their pet

A hunter profile (`conf/profiles/BmHunterSim.conf`, `MmHunterSim.conf`, `SvHunterSim.conf`) sets `PetCreatureEntry`, the
creature_template entry of a beast the actor tames before the first iteration (`SimBot::Create()`, then
`SimBot::EnsurePet()` at the start of every iteration). The pet is made the way a live bot's pet is
(`Player::CreatePet()`, the actor's level, autocast on, then `PlayerbotFactory::InitPetTalents()` for the pet-tree
points), but from a fixed entry instead of `InitPet()`'s random pick, so every iteration and every run has the same pet.
A dead pet is revived and a missing one tamed again. The pet's swings and spells are recorded under the owner (rows
read "(pet)" in the report). A hunter actor also gets the "Requires No Ammo" aura, so its ranged weapon needs no
arrows. The run log shows what ran: "tamed pet ...", and "strategies resolved: combat [...], non-combat [...]".

## Healing sim (heal mode)

A profile with `Mode = Heal` (`conf/profiles/HolyPriestHealSim.conf`) runs the healing sim: the profile's class is the
healer, it heals a party or raid of headless allies that a "Sim Raid Boss" damages with real hits. The healer is always
one of the targets. Plan: `.agents/plans/healing-sim/healing-sim.PLAN.md`.

```
HEALSIM_GROUP=party HEALSIM_TARGETS=pin50 tools/run-sim.sh HolyPriestHealSim 60 60 1 3
HEALSIM_TARGETS=drain:150 tools/run-sim.sh HolyPriestHealSim 120 60 1 3          # the group defaults to the profile's
HEALSIM_INFINITE_MANA=1 HEALSIM_TARGETS=pin50 tools/run-sim.sh HolyPriestHealSim 60 60 1 3
```

- `HEALSIM_GROUP`: `party`, `raid10` or `raid20`. `HEALSIM_TARGETS`: the preset `pin50` / `pin20` (every member held at
  that health by real hits: the pure-HPS measurement), `drain:<n>` (every member takes n damage a second, tanks 3x; the
  survival measurement), or a full list such as `tank:drain:450, 3*dps:drain:150, self:drain:100`.
  `HEALSIM_INFINITE_MANA=1` keeps the healer's mana full during the fight.
- A heal run is at most 300 s and takes no `[targets]` argument.
- Reports are `reports/<Profile>.<group>.<tag>.<ts>.report.json` (the tag is the preset, `x<hash>` for a custom list,
  `-inf` for infinite mana) and the baked page is `reports/HealProfileReport.html`. `tools/aggregate_reports.py`
  trims by HPS (a run with any death is never trimmed) and refuses to merge different scenarios;
  `tools/heal-report-template.html` is the page. Pin scenarios read as HPS; drain scenarios read as deaths, overheal and
  mana.

## The sim never touches the live characters DB

The sim actor is a real `Player` with no `characters` row, and it creates pets, level-up mail and items whose ids come
from sequences (`character_pet.id`, `mail.id`, item guids, ...) shared with the live server. Those can't all be reserved
module-side (`docs/bugs-and-fixes.md`, "Sim actor autosave"), so the isolation is at the database:

1. **Throwaway schema.** `tools/run-sim.sh` clones the live characters schema (structure of every table, plus the rows of
   the static/bookkeeping tables a worldserver reads at boot, `CHARS_COPY_DATA_TABLES`) into
   `acore_characters_sim_<pid>`, points the sim container's `AC_CHARACTER_DATABASE_INFO` at it, and drops it on exit,
   including after a failed or interrupted run. The live `acore_characters` is never connected to by the sim process.
   A schema left by a `kill -9` can be removed with `DROP DATABASE acore_characters_sim_<pid>`.
2. **Fails closed.** `OnDpsSimRun()` refuses to run unless the characters DB name starts with `acore_characters_sim`
   (the live name, or an unreadable `CharacterDatabaseInfo`, aborts the run).

Defence in depth, harmless on a scratch schema (`src/SimActor.cpp`): `SimActor::Create()` zeroes `PlayerSaveInterval` /
`PlayerSave.AdditionalSaves` in-process so the autosave timer never fires; actors take guids from
`SimActor::SIM_GUID_BASE` (0x7FFF0000) upward instead of the Player generator; and `DpsSimPlayerScript::OnPlayerSave`
counts and logs any `SaveToDB()` on a sim guid. `DpsSim.RunTests=1`'s no-persist test asserts the count is 0 after 20
simulated minutes and no rows sit in the reserved block. There is no per-guid purge any more: the schema is dropped
whole.
