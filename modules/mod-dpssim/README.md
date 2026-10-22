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

## Tank sim (tank mode)

A profile with `Mode = Tank` (`conf/profiles/ProtWarriorTankSim.conf`, a draft until TS3) runs the DPS sim with one
change: the dummies swing at the actor. Plan: `.agents/plans/tank-sim/tank-sim.PLAN.md`.

- Profile keys: `TankScenario` (`dps` refills the actor's health after every step so it never dies; `survive` does not,
  the run ends at its death and `ActorDiedAtMs` is the time to death), `TankHitDamage` (the boss, 1 target, default
  `2250-2750` before armor) and `TankPackHitDamage` (each dummy of a 2+ target run, `500-600`), `TankSwingMs` (2000),
  `TankDummyCrit` (true). `DpsSim.Tank*` in the conf override them; `DpsSim.TankPullAuras` (conf only) casts spells on
  the dummies at the pull for known-value runs. There is no dummy parry-haste switch: the PvE always-hit rule means a
  dummy never parries the actor. The tank's own parry haste (a parry by the actor speeding up its next swing) is the
  core's, untouched.
- The AI is swapped in on the summoned dummies at run time (`SimTankDummyAI`, `Creature::AIM_Initialize`), only in tank
  mode; a DPS or heal run keeps the passive AI. The dummies do nothing until the pull, so the pre-pull buff phase is
  untouched. The solver sets their base weapon damage so the undebuffed hit lands in the configured range, with the
  attack power at 15% of the minimum hit (`SimTankDummy::AP_SHARE_OF_MIN`): an attack-power debuff such as
  Demoralizing Shout takes at most that much off.
- The boss dummy (1 target) is a raid boss to the actor: its real level is the actor's + 3 (the level it already rolled
  hit and crit at, so armor reduction now matches it too) and it is stun immune. Pack dummies keep the actor's level
  and stay stunnable. Both are logged at install ("boss dummy ... stun immune").
- Layout: one dummy 3 yd dead ahead of the actor; a pack on a 3 yd arc within +-30 degrees of its facing, all facing it.
- `DamageTakenRecorder` records every swing (outcome, pre-armor, armor, block, shields by spell, final damage, rage
  across the swing); the actor's own healing comes from the `HealRecorder` with the actor as its whole group. The batch
  logs a `tank iteration` summary per iteration and writes one report per iteration (see "Tank reports" below).
- The character sheet is `RunResult::TankActor`, read one second into the fight (stance and first buffs up: a Prot
  Warrior is only crit immune in Defensive Stance); `TankActorAtPull` is the same read at the pull, before the bot
  acted. A `survive` run the actor lived through has `TankSurvived` set and counts its TTD as the full duration.
- Between iterations (every mode) the reset removes non-passive auras and passive-flagged auras with a duration (a
  spell's delay holder, e.g. Thunderstruck's echo), so nothing from one iteration fires in the next one's buff phase.
- Needs the core hook `UnitScript::OnMeleeOutcomeFinal` (CalcDamageInfo).

### Running it

```
tools/run-sim.sh ProtWarriorTankSim 120 60 1 10                        # dps scenario, one boss dummy, avg of 10
TANKSIM_SCENARIO=survive tools/run-sim.sh ProtWarriorTankSim 120 60 1 10   # time to death
tools/run-sim.sh ProtWarriorTankSim 120 60 1 10 100 5                  # 5-dummy pack (the 7th argument, [targets])
TANKSIM_HIT=3000 TANKSIM_SWING_MS=2500 tools/run-sim.sh ProtWarriorTankSim 120 60 1 10
```

Environment overrides (each maps onto the `DpsSim.Tank*` key of the profile key it names; without one the profile's own
value applies; a bad value or a non-tank profile is refused before anything starts):

| Variable | Conf key | Values |
|---|---|---|
| `TANKSIM_SCENARIO` | `DpsSim.TankScenario` | `dps` or `survive` |
| `TANKSIM_HIT` | `DpsSim.TankHitDamage` | the boss's hit before armor, `2250-2750` or one value |
| `TANKSIM_PACK_HIT` | `DpsSim.TankPackHitDamage` | each pack dummy's hit before armor, `500-600` |
| `TANKSIM_SWING_MS` | `DpsSim.TankSwingMs` | 500-10000 |

Presets (the profile defaults, plan T3/T4): a boss hit of 2,250-2,750 before armor every 2.0 s with crits on, or each
pack dummy for 500-600; the boss is a level actor+3, the pack elites the actor's level. Files:
`reports/<Profile>.tank-<scenario>.<targets>t[.x<hash>].<ts>.report.json` (and `.iterN.` files), so aggregation never
mixes scenarios or pack sizes (`x<hash>` is added when `TANKSIM_HIT`, `TANKSIM_PACK_HIT` or `TANKSIM_SWING_MS`
override the profile, like the heal sim's scenario tag; `DPSSIM_EXTRA_CONF` may not set the `DpsSim.Tank*` keys,
run-sim.sh refuses it); the baked page is `reports/TankProfileReport.html`.

### Tank reports (`"kind": "tank"`)

A tank report is the DPS report exactly as before (`config`, `summary`, `spells`, `hits`, `auraEvents`, `manaSamples`,
`casts`, `targets`) with `"kind": "tank"` as its first key and a `"tank"` section as its last; DPS and heal reports are
unchanged. The `tank` object (schema in `src/SimReport.h`): `config` (scenario, hit ranges, swing ms, crit switch,
dummy count and kind, solver values per dummy), `actor` (the character sheet after the first second and at the pull),
`summary`, `perDummy` (full outcome split, damage taken, threat), `absorbsBySpell`, `selfHeals`, `swings`, `samples`
(health, power, Bulwark stacks every 500 ms), `threat` (per dummy, every second). Time bases: swing times are the start
of the step, samples and the time of death are read after it, so the swing that killed the actor is stamped one step
before `actorDiedAtMs`.

`tank.summary` highlights: the outcome counts and percent (miss, dodge, parry, block, full block, crit, crush, hit),
`avoidancePct`, `mitigation` by source (avoided, armor, block, absorb), `damageTaken` (already after the shields),
`dtps`, `selfHealEffective` / `selfHps`, `netDtps` = (damage taken - effective self-healing) / seconds (absorbs are
never subtracted again), `ttdMs` and `survived`, `minHealthPct`, `msUnder35Pct`, `rageGained` / `rageGainedPerSec`
(rage from the swings, rage tanks only; 0 and hidden on the page for any other resource), `tps` (= `tpsAlive`),
`lowestThreat`, expected against observed crit % and `critBugCount` (crits on a swing whose rolled chance was 0, with
`critBugAtMs`; the run log's warning also fires on any crit when the crit chance was 0 at the pull). Rates divide
by `rateBaseMs`: the time of death in `survive` when the tank died, the
full duration otherwise. `dpsAlive` / `tpsAlive` are the damage and threat over that same time; the top-level
`summary.dps` stays total damage over the full duration (a dead tank is charged the whole fight, as every DPS report
does), so read `dpsAlive` in a `survive` run.

### Reading dps against survive

- **dps** (health refilled every step, the tank never dies): the headline is **DPS** with **TPS** beside it; the hits
  are real, so damage-taken rage, shields used up and the Revenge / Bulwark / avoid procs all happen. DTPS and the
  mitigation split describe the incoming hits and are not a survival figure. Trimmed on DPS like any DPS batch.
- **survive** (no outside healing, the run ends at death): the headline is **time to death (TTD)** with **net DTPS**
  beside it. A run that lives the whole duration counts the duration as its TTD and is marked *survived* (the batch
  shows the survived count). The aggregate trims on TTD, dead runs included (the DPS rule that keeps dead runs does
  not apply: every run here is expected to die), and the representative run is the median-TTD kept one.
- `tools/aggregate_reports.py` merges tank reports (kind `tank`) with their own path: every numeric field of
  `tank.summary` is averaged over the kept runs, per-dummy / absorb / self-heal rows are averaged, the timelines come
  from the representative run, and `aggregate.tank` has the survived / died counts and every run's value
  (`perIteration`). It refuses to mix kinds, scenarios, target setups, hit ranges, swing speeds, crit switches, pull
  auras (and, in `survive`, durations).
- `tools/build_report_html.py` bakes a tank report into the DPS template plus the "Damage taken" section
  (`tools/tank-section.html`, injected at the template's `__TANK_*__` markers): headline tiles, a crit-bug banner, the
  outcome breakdown (observed against expected), the mitigation bar with the shields by spell, health over time with
  the swings and the defensive aura windows (Shield Block, Last Stand, Shield Wall, Ironfur, ... matched by spell name),
  self-healing by spell, the class resource over time (and Bulwark stacks), threat per dummy and a per-dummy table.
  A DPS page is byte-for-byte what the template alone gives.

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
- Profiles: `DiscPriestHealSim`, `HolyPriestHealSim` (Human, race 1), `RestoDruidHealSim` (Tauren, race 6) and
  `HolyPaladinHealSim` (Human); each one's header has its talent decode, gear arithmetic and the sweep commands.
  `NoHealerHealSim` is the harness test profile.
- A heal run is at most 300 s and takes no `[targets]` argument.
- Reports are `reports/<Profile>.<group>.<tag>.<ts>.report.json` (the tag is the preset, `x<hash>` for a custom list,
  `-inf` for infinite mana) and the baked page is `reports/HealProfileReport.html`. `tools/aggregate_reports.py`
  trims by HPS (a run with any death is never trimmed) and refuses to merge different scenarios;
  `tools/heal-report-template.html` is the page. Pin scenarios read as HPS; drain scenarios read as deaths, overheal and
  mana.
- Known-value tests: `DpsSim.RunTests=1` (optionally `DpsSim.TestFilter=heal`) also runs six heal-mode tests (a Flash
  Heal's amount, an undefended drain target's death, a Power Word: Shield's absorb, Renew's ticks, no pushback on a
  pinned healer, Guardian Spirit's credit). They replace the healer's bot AI with a scripted cast
  (`RunConfig::HealStepHook`) on an untalented, ungeared Priest. Run one with
  `DPSSIM_EXTRA_CONF='DpsSim.RunTests = 1\nDpsSim.TestFilter = heal' tools/run-sim.sh NoHealerHealSim 10 60 1 1`
  (the script then exits 1, as no report is written; keep the log with `DPSSIM_KEEP_LOG=1` and grep `[PASS]`/`[FAIL]`).

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
