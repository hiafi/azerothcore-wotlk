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

### Any pet family, the full_raid buff set, the family sweep

- **Family switch.** `DpsSim.PetCreatureEntry` replaces the profile's pet for one run. `run-sim.sh` sets it from
  `DPSSIM_PET_FAMILY` (a key, name or family number of `tools/pet_families.tsv`, one "Tamable <family>" creature per
  family, all 32) or `DPSSIM_PET_ENTRY`, and the names carry it: `BmHunterSim.pet-cat.<ts>...`.
- **Buff sets** (`DpsSim.BuffSet`, `SimBuffSet.h`, DPS runs only). `self_only`, the default, adds nothing (every run
  before this). `full_raid` puts `DpsSim.RaidBuffs` on the actor and its pet at the end of the pre-pull buff phase
  (after a pet re-tame or revive), `DpsSim.RaidDebuffs` on every dummy, both pinned (no expiry) and put back once a sim
  second if they go missing, and `DpsSim.RaidPullBuffs` (Bloodlust and Sated) on the actor and pet with their own
  duration. The sim adds the auras with `Unit::AddAura` (the actor as the caster); nobody casts them. Every member is in
  the same `spell_group` as the hunter pet family effect of its category, so a family's own cast is suppressed by the
  group rule and adds nothing (hunter-pet-families ruling 7). The lists and their defaults are in `dpssim.conf.dist`;
  `run-sim.sh` takes `DPSSIM_BUFF_SET=full_raid` (".full_raid" in the names) and `DPSSIM_RAID_BUFFS` /
  `DPSSIM_RAID_DEBUFFS` / `DPSSIM_RAID_PULL_BUFFS` to replace a list (".full_raid-x<hash>"). The run log names each
  member with its effects and groups ("raid buffs (actor and pet): ...") and, on the first iteration, the amounts it
  landed with ("buff set: 24932 Leader of the Pack on the actor: aura 52 = 5, ..."), or that it did not land.
  An entry may end in "@amount" ("21183:0@3", a negative amount is allowed) to set the amount of its applied effects:
  a spell group is looked up by the first rank of a chain, and Heart of the Crusader's chain is not in `spell_ranks`,
  so its first rank (1%) is applied with rank 3's 3%. `full_raid` is for hunter actors only (the aura's caster is the
  actor, so a class that owns one of the listed spells would see it as its own: its bot skips the cast, or the two
  replace each other every second); another class needs a neutral caster first, and the run refuses it. One sim second
  after the pull, before the first refresh pass, the log prints "buff set coverage": per actor, pet and dummy what is
  missing, and which of the pet's auras the actor's own aura carried (an area aura propagated) and which are copies
  added directly. Every iteration logs what the refresh put back and every put-back that failed, with the member of
  its spell group in the way (a family effect that outranks the baseline shows up there).
- **Disabled spells and immune dummies.** `DpsSim.DisableSpells` (`DPSSIM_DISABLE_SPELLS`, ".no<ids>" in the names)
  takes spells out of the actor's and its pet's spellbooks, to measure one ability (a family's own group buff, a
  utility): the job fails when neither knows a listed id, and a spell another spell triggers still lands.
  `DpsSim.DummyImmuneAuras` (`DPSSIM_DUMMY_IMMUNE_AURAS`, ".imm<ids>") makes every dummy immune to the listed spell
  ids instead, so the hit that applies an owner-only debuff lands and the debuff does not (Boar's Gore debuff
  201665 once F2 is live).
- **The sweep.** `tools/pet_family_sweep.py run` runs the BM profile for every family at 1, 3 and 5 targets under
  `full_raid` (120 s x 5, 100 ms step, at most 6 sims at once; `--families`, `--targets`, `--dry-run`), then writes
  `reports/petsweep-<sweep>/sweep.csv` and `summary.md`: DPS per target count, the pet's damage share, the distance
  from the median family and a flag for more than 50 DPS from it at 1 target. `index <dir>` rebuilds the summary.
  `--disable-family-spells raptor=201985` takes spells out for one family's runs only (the Raptor's Tail Sweep, a
  knockback, scatters the dummies so the pack rows of the hunter bot never fire at 3 and 5 targets); an unknown family
  is an error and the disables are in the manifest, the CSV and the summary. A run fails when its report lacks
  `petCreatureEntry` / `buffSet` / `disabledSpells` (an image that predates SIM1) or has other values than the job
  asked for. The pet share counts the pet and the minions it owns.
  Tests: `python3 -I modules/mod-dpssim/tools/test_pet_family_sweep.py`.

## Power and rune samples (`powerSamples[]`)

The playerbot DPS report (and a tank report, which is the DPS report plus a `tank` section) carries `powerSamples[]`,
one entry every 500 ms of the measured run: `{timestampMs, powerType, power, maxPower[, runes: {blood, frost, unholy,
death}]}`. `power` and `maxPower` are what the player reads (rage and runic power are stored x10 and divided here;
`powerType` is the core's `Powers` enum, 6 = runic power). `runes` exists for a Death Knight only: the runes that are
READY at the sample, counted by their current type (a Death Rune is `death` alone), so a rune sitting ready while the
bot casts something else shows as an idle rune, and runic power at the cap or a Breath of Sindragosa drain read straight
off the series. The hardcoded-rotation run writes the key empty, and the heal report has no `powerSamples` key at all.
`tools/aggregate_reports.py` (the multi-iteration report `run-sim.sh` prints) carries the representative run's series
into the aggregate, like `manaSamples`. Source: `RunResult::PowerSample`, `MaybeSamplePower()` in `SimDaemon.cpp`.

## Spend per cast and per-step aura samples (`casts[].powerCost`, `auraSamples[]`)

Two additions to the DPS report (and the tank report, which is the DPS report plus a `tank` section); both leave every
existing field, and the order of the existing keys, as they were.

- `casts[]` entries now end with `powerCost`: `{timestampMs, spellId, triggered, target, powerCost}`. It is
  `Spell::GetPowerCost()` at cast time (the spell's own `m_powerCost`), in the cast's power type and the engine's units,
  so rage and runic power are x10 (a 25-rage Mortal Strike reads 250) while mana is as stored. It is the cost the spell
  was built with, not the resource the cast actually consumed: a free cast (Momentum's free Slam) reads 0, but a
  script's extra spend (Execute's extra rage, the Sudden Death floor that `SetPower`s in `spell_warr_execute`) is
  invisible here, a dodged or parried strike still records the full cost, and a triggered spell that carries a cost
  reads that cost, non-zero (sum `powerCost` over `triggered == false` casts only). So the sum of `powerCost` is the
  nominal spend only; the analysis takes Execute's extra
  spend from the `powerSamples` delta. (The heal report had it already.)
- `auraSamples[]` follows `casts` and exists only when the profile sets **`AuraSampleIds`**, a comma-separated list of
  spell ids (`AuraSampleIds = 204403, 200123`; a duplicate id is read once; every entry must be a whole number that
  fits 32 bits, or the profile is refused). Every sim step (the 100 ms `stepMs`, not
  the 500 ms cadence of `powerSamples`), after the bot has acted, each listed id is looked up twice and an entry
  is written for each lookup that finds an aura:

  ```
  {"ts": 4300, "spellId": 204403, "onTarget": false, "stacks": 3, "remainingMs": 7400}
  ```

  `onTarget: false` is the aura on the actor (any caster); `onTarget: true` is the actor's own aura (the actor is the
  caster) on target 0, the primary dummy (the other dummies are not sampled). A refresh of an aura produces no aura
  event, so a refresh shows only as `remainingMs` rising before the aura ran out. `ts` is ms since the iteration start
  (the `powerSamples` time base),
  taken after the step's clock advance and the bot's action, so the state after a cast at T first appears at
  `ts = T + stepMs`: compare a cast at T with the sample at T + stepMs. `stacks` is the stack amount, `remainingMs`
  the time left (`-1` for a permanent aura). Nothing is written while an aura
  is absent, so a gap in `ts` is the aura being down and a stack falling to zero reads as the last entry. A profile
  without the key writes no `auraSamples` key at all (the report is byte-for-byte what it was). It samples a DPS run and
  a tank run; a heal run ignores it. Memory is one entry per id per side per step: a 60 s run with ten ids is about
  6,000 entries per side.
- `tools/aggregate_reports.py` carries both through: `casts` (with `powerCost`) and `auraSamples` come, like
  `powerSamples`, verbatim from the representative iteration; the per-iteration `iterN.report.json` files keep every
  iteration's own. Source: `RunResult::AuraSample`, `MaybeSampleAuras()` in `SimDaemon.cpp`, `Profile::AuraSampleIds`
  in `SimProfile.h`.

## Off-hand white swings and `DummyStartHealthPct` (S3 Fury additions)

The off-hand tag is NOT opt-in: every dual-wield actor (Rogues, Enhancement, dual-wield Death Knights, Fury, Titan's
Grip) now gets a second "Melee (off-hand)" row, and its "Melee" row shrinks by the off-hand share (about a third);
totals are unchanged. To compare a dual-wield report with a pre-S3 one (e.g. the `CombatRogueSim` regression baseline),
add the "Melee" and "Melee (off-hand)" rows. A two-hander's report is unchanged. `DummyStartHealthPct` is additive (0
or absent = as before). `tools/aggregate_reports.py` carries both through unchanged (a `spells[]` row is keyed by
`(spellId, isPet, sourceEntry)`, so the off-hand row never merges into the main-hand one).

- **Off-hand white swings.** The actor's main-hand white swings stay spell id `0` (`EventRecorder::MELEE_SPELL_ID`),
  so every consumer that reads "spellId 0 = white swing" (Prot/Arms/Bear/Rogue reports, `rage_sweep.py`) is unchanged.
  A dual-wielder's OFF-HAND white swings are recorded as the pseudo spell id **`0xFFFF0001` (4294901761,
  `EventRecorder::OFFHAND_MELEE_SPELL_ID`)**, in `hits[]` and `spells[]` like any other row (`isPet` false,
  `sourceEntry` 0). Source: `EventRecorder` also subscribes to `UNITHOOK_ON_MELEE_OUTCOME_FINAL`, which carries the
  swing's attack type and fires right after `OnMeleeDamageFinal`; it re-tags the row that hook just wrote, so a swing
  is never counted twice. A run with no off-hand weapon produces no row with that id, a pet's swings keep
  `0xFFFFFFFE`, and misses/dodges/parries (damage 0) are still not rows. Titan's Grip's second two-hander is an
  off-hand swing too, so it lands under this id. The id is above every real spell id (and not
  `0xFFFFFFFE`); `build_report_html.py` names it "Melee (off-hand)", and `tools/rage_sweep.py` splits the hands by
  this tag (spellId 0 = main hand, `0xFFFF0001` = off hand).
- **`DummyStartHealthPct = <0-100>`** (profile key, float percent of `DummyMaxHealth`; 0 or absent = every dummy
  starts full, as before). Each dummy starts every iteration at that percentage of its max health (at least 1), so a
  drain run can begin inside an execute phase: `DummyHealthDrain = true`, `DummyMaxHealth = 600000`,
  `DummyStartHealthPct = 21` is below 35% from the pull and crosses 20% after about 6 s at ~1,000 DPS (6,000 damage),
  and the 120,000 health left at 20% keeps a 60 s run off the 1-health floor (where drain clamps the damage taken).
  Size it from the run's DPS: start % = 20 + DPS x seconds-to-20% / DummyMaxHealth x 100. Without `DummyHealthDrain`
  the dummy takes no damage and stays at that percentage for the whole run (an "always below 20%" run). In tank mode
  the key only applies with `DummyHealthDrain = true`; without drain the tank dummies keep the huge default pool and
  are refilled to full every step. A value outside 0-100 or not a number fails the profile load. Source:
  `Profile::DummyStartHealthPct` (`SimProfile.h`), applied by `SimDummyAI::ResetHealth()` after the dummy is created
  (`SimTarget::Create()`) and by every `RefillResources()` (between iterations and after the pre-pull buff phase,
  whose combat stop lets the dummy regenerate), with or without drain.

## Minion attribution (`sourceEntry`, pet auras, `minionSamples[]`)

The DPS report and the tank report (the DPS report plus a `tank` section) attribute the actor's minions one by one:

- `hits[]` and `spells[]` rows carry `sourceEntry`, the creature entry of the attacker (0 for the actor). `spells[]` is
  keyed by `(spellId, isPet, sourceEntry)`, and so is the aggregate `tools/aggregate_reports.py` writes, so the white
  swings of the permanent ghoul (26125), the Lesser Ghouls (300320), the Army of the Dead ghouls (24207) and the
  Abomination (300321) are separate rows although they share the pseudo spell id `0xFFFFFFFE`, and a Gargoyle Strike
  (27829) never merges into another minion's row. A report from before the field counts every row as `sourceEntry` 0.
- `auraEvents[]` also records the auras gained and lost by a unit the actor owns (a pet, guardian or totem; passive
  auras skipped), as `"unit": "pet"` with `unitEntry`, the unit's creature entry (0 for the actor), so Shadow Infusion
  and Dark Transformation uptime on the ghoul read straight off the series. Consumers that treat "not actor" as "target"
  must test `unit == "target"`.
- `minionSamples[]`: `{timestampMs, counts: {"<entry>": n, ...}}` every 500 ms (the `powerSamples` cadence), the alive
  units the actor controls per creature entry (its pet, guardians, totems and slotted summons, each counted once). The
  hardcoded-rotation run writes the key empty and the heal report has no `minionSamples` key. The aggregate carries the
  representative run's series, like `powerSamples`. Source: `RunResult::MinionSample`, `MaybeSampleMinions()` in
  `SimDaemon.cpp`, `EventRecorder::GetHitSourceEntries()`.

## Tank sim (tank mode)

A profile with `Mode = Tank` runs the DPS sim with one change: the dummies swing at the actor. Plan:
`.agents/plans/tank-sim/tank-sim.PLAN.md`. Profiles (level 60, real dungeon tank gear, the bots' premade talents):
`ProtWarriorTankSim` (Human, race 1), `ProtPaladinTankSim` (Human, race 1; the same plate set) and `BearTankSim`
(Tauren, race 6; the bear tank build, not Bestial Fury). Each header lists the talent decode, the gear and the sheet
to expect.

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
- Threat: the dummies take the actor's real damage (clamped to 1 health), so `Unit::DealDamage` adds damage threat
  with every native modifier (stances, `spell_threat`, SPELLMOD_THREAT). Without `DummyHealthDrain` they keep a 100M
  pool (`DummyMaxHealth` is ignored) and are refilled to full every step, so no execute or health-threshold effect
  fires; with it they drain as a DPS run's dummy does. Tank reports before this change counted flat threat only.
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
- Known-value tests: `DpsSim.RunTests=1` with `DpsSim.TestFilter=tank.` runs the eight tank tests (`tank.outcomes`,
  `tank.crit_immune`, `tank.hit_formula`, `tank.revenge`, `tank.ttd`, `tank.survived`, `tank.thunderclap_slow`,
  `tank.stun_immune`; `src/SimTests.cpp` documents what each asserts). They load `ProtWarriorTankSim.conf` from the
  directory of `DpsSim.Profile` and script the actor through `RunConfig::TankStepHook` / `TankSilenceBot`:
  `DPSSIM_KEEP_LOG=1 DPSSIM_EXTRA_CONF='DpsSim.RunTests = 1\nDpsSim.TestFilter = tank.' tools/run-sim.sh
  ProtWarriorTankSim 10 60 1 1`. A test run writes no report, so run-sim.sh ends with "produced no report"; the
  `[PASS]` / `[FAIL]` lines are in the kept run log.

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
`powerSamples`, `minionSamples`, `casts`, `targets`) with `"kind": "tank"` as its first key and a `"tank"` section as
its last; the heal report is unchanged. The `tank` object (schema in `src/SimReport.h`): `config` (scenario, hit
ranges, swing ms, crit switch, dummy count and kind, solver values per dummy), `actor` (the character sheet after the
first second and at the pull), `summary`, `perDummy` (full outcome split, damage taken, threat), `absorbsBySpell`,
`selfHeals`, `swings`, `samples` (health, power, Bulwark stacks every 500 ms), `threat` (per dummy, every second).
Time bases: swing times are the start of the step, samples and the time of death are read after it, so the swing that
killed the actor is stamped one step before `actorDiedAtMs`.

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
HEALSIM_TARGETS=drain:150 HEALSIM_DRAIN_NOISE=0.5 HEALSIM_DRAIN_PULSE_MS=3000 tools/run-sim.sh HolyPriestHealSim 120 60 1 3
```

- `HEALSIM_GROUP`: `party`, `raid10` or `raid20`. `HEALSIM_TARGETS`: the preset `pin50` / `pin20` (every member held at
  that health by real hits: the pure-HPS measurement), `drain:<n>` (every member takes n damage a second, tanks 3x; the
  survival measurement), or a full list such as `tank:drain:450, 3*dps:drain:150, self:drain:100`.
  `HEALSIM_INFINITE_MANA=1` keeps the healer's mana full during the fight.
- Drain shape, for a noisier and more realistic check where overhealing and target choice matter. A drain value is
  always damage per second, whatever the pulse length. `HEALSIM_DRAIN_PULSE_MS` (profile key `DrainPulseMs`, conf
  `DpsSim.DrainPulseMs`, whole ms, at least 100, default 1000) sets how often the Sim Damage Pulse lands: a 3000 ms
  pulse deals 3x the amount of a 1000 ms one. `HEALSIM_DRAIN_NOISE` (profile key `DrainNoise`, conf `DpsSim.DrainNoise`,
  0 to 1, default 0 = equal pulses) makes each pulse unequal: every living draining member draws a weight
  `1 + noise * u` (u uniform in [-1, 1]) and takes its normal amount (a tank's 3x included) times that weight, rescaled
  so the pulse's total damage is exactly the noiseless pulse's total (the damage per second is unchanged, only who takes
  it moves). The shares are whole hit points; one that rounds to 0 skips that hit. The environment variables beat the
  profile keys. A run with a non-default noise or pulse adds `.n50`, `.p3000` or `.n50p3000` to its file names, the
  report's `config` has `drainNoise` and `drainPulseMs`, and `aggregate_reports.py` refuses to mix different values.
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
  pinned healer, Guardian Spirit's credit) and a seventh (`heal-drain-noise`: a noisy drain keeps each pulse's total and
  varies the shares). They replace the healer's bot AI with a scripted cast
  (`RunConfig::HealStepHook`) on an untalented, ungeared Priest. Run one with
  `DPSSIM_EXTRA_CONF='DpsSim.RunTests = 1\nDpsSim.TestFilter = heal' tools/run-sim.sh NoHealerHealSim 10 60 1 1`
  (the script then exits 1, as no report is written; keep the log with `DPSSIM_KEEP_LOG=1` and grep `[PASS]`/`[FAIL]`).

## Mechanics sim (mechanics mode)

The dungeon mechanics plan's sim (`.agents/plans/dungeon-mechanics/dungeon-mechanics.STAGE-M4-HANDOFF.md`, section 3.4):
the profile under test is one member of a group of **real bots** that fights a boss stand-in while mod-boss-mechanics
runs its drills on it. Every member reports its damage, the failures the module's global failure sink saw for it (by
type and mechanic) and the module's own counters (solves, outcomes, lock blocks, mode time, leaks, solve and route µs).
The paired baseline is the same run with the program `none`. The worldserver must be built with mod-boss-mechanics
(`SimBossMechanics.h` includes the module behind `__has_include`, so the sim still builds without it; a mechanics run
then refuses to start).

```
MECHSIM=1 tools/run-sim.sh RetPaladinSim 120 60 2 5 100                     # the program rotation, 5 x 120 s
MECHSIM=1 MECHSIM_BASELINE=1 tools/run-sim.sh RetPaladinSim 120 60 2 5 100  # its paired baseline
MECHSIM=1 MECHSIM_GROUP=9 MECHSIM_PROGRAMS="barrage:60" tools/run-sim.sh FireMageSim 120 60 2 5 100   # crowd barrage
tools/mechanics_sweep.py run                         # every reworked spec, mechanics + baseline, at most 6 at once
tools/mechanics_sweep.py index reports/mechsweep-<sweep>    # re-pair a sweep, write index.json / index.md
```

- **The group** (`SimMechanicsConfig.h`): 1 tank, 1 healer, 3 DPS by default (`MECHSIM_GROUP` / `DpsSim.MechanicsGroup`,
  2-40: 1 tank, 2 above 10; 1 healer, 2 for 6-10, 4 above 10). The profile under test takes its role's slot: a Tank
  profile the tank slot, a Heal profile the healer slot, any other a DPS slot (`MECHSIM_ROLE` overrides; a
  `Mode = Mechanics` profile names its slot with `MechanicsRole`). The other slots are fixed reference profiles, the
  same for every spec of a sweep: tank `ProtWarriorTankSim`, healer `RestoShamanHealSim`, DPS `ArmsWarriorSim`,
  `FireMageSim`, `CombatRogueSim` (lists, cycled for bigger groups, skipping the profile under test;
  `DpsSim.Mechanics{Tank,Healer,Dps}Profiles`). Every member is created **Horde** (Orc, Blood Elf for a Paladin, Troll
  for a Priest or Mage, Tauren for a Druid), so the group can heal and buff itself; `[race]` is ignored.
- **The place** (`SimMechanicsScenario.h`): the open world at the Orc start (`DpsSim.MechanicsAnchorRace`; the Human
  start's Wild Turkey keeps the AoE gates closed), every member moved onto that map. The boss stand-in (the DPS sim's
  boss dummy, 900004-900006) stands 10 yd ahead of the anchor; the tank 3 yd in front of it, the others on an arc
  (DPS 12 yd, healers 18 yd). Every member goes back to its spot between iterations.
- **The group is all bots**, so `PlayerbotAI::FindNewMaster()` finds no master and nobody follows anybody;
  `follow`, `stay`, `guard` and `passive` are removed from both engines anyway (the run log lists each member's
  strategies and what was removed). Each bot's AI is ticked **once** per step, as live: playerbots'
  `OnPlayerAfterUpdate` inside `Map::Update`; the loop only acknowledges near teleports (`SimBot::AckNearTeleport`).
  The DPS, heal and tank modes (and the mechanics mode's pre-pull buff phase) still tick twice per step
  (`SimBot::UpdateAI` plus that hook); their calibration assumes it (STAGE-M4-R-REPORT M-4). **The m4-s1 sweep numbers
  came from the double-tick build**: its bots reacted at twice the live rate, so its failures, DPS loss and late
  arrivals are optimistic; re-baseline before comparing.
- **The boss swings at the tank** (`DpsSim.MechanicsBossSwings`, on): the tank sim's dummy AI, with the first tank
  profile's `TankHitDamage` / `TankSwingMs` / `TankDummyCrit`. The tank is unkillable (a lethal swing is refilled and
  counted as `tankSaves`: the healer did not keep up). Without health drain the boss is refilled every step.
- **The program** (`DpsSim.MechanicsPrograms`, `MECHSIM_PROGRAMS`): `;`-separated mod-boss-mechanics programs
  (`Drill::ParseProgram`: drill names with cycles, `lanes`, `barrage` / `minefield` / `uminefield` with seconds),
  iteration i runs entry i mod n, once (no loop). **`;` alternates, `,` chains**: `a;b` runs a in even iterations and
  b in odd ones; `a,b` runs a, then b 4 s after a's last cycle, inside every iteration, so b never runs when a fills
  the fight (`deadmines-followups,sfk-hunt,scholomance-shapes` is 248 s: a 120 s fight never reaches the third). A
  program whose entries never start is logged at WARN with their names, and the report carries
  `config.programLengthsMs` and `config.programLateEntries`. The default rotation covers every kind in five 120 s
  fights: `smite,fenrus,ras` (Frontal, Spread, Bait, RunOut, Stack), `cookie,barrage:15` (cones, puddles, run-outs),
  `soaks,minefield:30`, `alexei` (156 s; a 120 s fight sees hold still, stack, spread, out of bounds, line up, desks and
  four heroic pairs), `barrage:60,lanes:3,uminefield:20`. The drill dice of iteration i are seeded `MechanicsSeed + i`,
  the same in the baseline; drill hits deal `MechanicsDamage` (1).
- **The start of every iteration**: the group's pre-pull buff phase (the longest `PrePullBuffMs` of the members), the
  pull, then `Sim::StartProgram(boss, member under test, program)` and `Sim::ReconcileBot` for every member (the
  module's gate installs `boss mechanics` once the scope exists; the run never ticks the world, so
  `Sim::RegisterBotGlue` registers the glue once before any bot exists). At the end: `Sim::ReadBotStats` and
  `Sim::TakeProgramErrors`, then `Sim::StopProgram` (markers, ledger, Weakened gone), then `Sim::ResetBotStats`.
- **Program entry errors**: an entry that fails at its start (a drill step that no longer parses, for example a spell
  row missing after a deploy, or nobody to land on) is skipped by the module, which logs it at `LOG_ERROR`. The sim
  takes the iteration's errors into `summary.programEntryErrors` (count) and `programEntryErrorMessages`; the
  aggregate lists them in `summary.programErrors` with the start errors, and the sweep index flags the spec.
- **Fallibility** is off (`MECHSIM_FALLIBILITY=1` turns it on and adds `.f1` to the names). run-sim.sh's scratch
  config also turns `BossMechanics.Enable`, `Bots.Enable` and `Bots.OpenWorldTestScope` on.

### Mechanics reports (`"kind": "mechanics"`)

One file per iteration (`src/SimReport.h` has the schema): `config` (the group, the programs, this iteration's program
and seed, the boss settings, fallibility, each program's length and the entries past the fight), `summary` (program
started or its error, `programStartLagMs` (the game clock against the pull when the program started: 0, else its later
entries ran that much off; the sweep index flags it), the program entry errors, actor
and group DPS, failures, group failures, stray failures, actor and group HPS, deaths, members without the strategy, the
tank's damage taken and saves), `members[]` (per member: role, profile, class, spec tab, strategies, damage and DPS on
the boss, healing done (`healEffective`, `healOverheal`, `healAbsorb`) and `hps` = (effective + absorbs) / duration,
casts, failures by type and `"<Kind>/<tag>"`, hits, moving time and distance, death, and `stats`: the module's mode
time, leaks with spell ids, counters and cost block), `groupFailures` (MissedSoak), `failureLog` (every failure in
order, capped at 2,000).
Files: `reports/<Profile>.mech-<tag>.g<size>[.f1][.<DPSSIM_BATCH_TAG>].<ts>...` with tag `rot` (default rotation),
`base` (baseline), `desc` (the descriptor slice) or `x<hash>` (other `MECHSIM_PROGRAMS`); the page is
`reports/MechanicsProfileReport.html` (`tools/mechanics-report-template.html`).

`tools/aggregate_reports.py` merges a run's iterations **without trimming** (5 iterations trim nothing anyway, and the
iterations run different programs): per member `{mean, min, max, perIteration}` for DPS, damage, casts, moving time and
distance, failure and hit counts with their sum, failures summed by type and mechanic, the module's counters summed (a
name ending in `Max` takes the maximum), leaks summed by spell id. It refuses to merge runs with another group, program
list, duration, damage, boss setting or fallibility.

### The sweep (`tools/mechanics_sweep.py`)

`run` launches every reworked spec (`mechanics_sweep.py list`: all ten classes, one profile per spec) twice, the
rotation and the baseline, next to each other, at most 6 sims at once (`--jobs`, capped at 6: about 2.4 GB each), each
with `DPSSIM_BATCH_TAG=<sweep>-<profile>-<mech|base>` and `DPSSIM_NO_HTML=1`, defaults 120 s x 5 iterations at a
100 ms step, level 60 (`--duration`, `--iterations`, `--step`, `--level`, `--group`, `--programs`, `--fallibility`,
`--specs` filters, `--profiles` replaces the matrix, `--dry-run` prints the run-sim.sh lines). Logs, `manifest.json`,
`index.json` and `index.md` go to `reports/mechsweep-<sweep>/`. The index pairs each spec's two runs: per member the
failures by type and mechanic, DPS with and without mechanics, `dpsLossPct = (1 - mech / base) x 100` (and its range
over the paired iterations); the same for HPS (`hpsLossPct`), which `index.md` shows instead of DPS when the member
under test is a healer, plus the group's HPS with and without mechanics (the boss swings at the tank in the baseline,
so a healer heals there too; reports from before the heal recorder read as 0 HPS), moving time against the
baseline's, escape / hold / freeze time, leaks, solve and route maxima; specs with a failure of the member under test,
a leak, a missing strategy, a program error (a start error or a failed entry) or a death come first. The reference
members' failures are listed too (they are the same group in every spec).

**Each build drill's own pass bar** (`DRILL_BARS` in the tool, mirrored from mod-boss-mechanics `MechanicDrill.h` and
the build reports; `tools/test_mechanics_sweep.py` checks the mirror against the module source): gated tags with a per
spec run limit (usually at most 1), reported tags that are listed in their own column and never fail, no gated tag on
more than 3 specs (a sweep problem at the top of `index.md`), and for `sfk-hunt` limits on the reference members
(`Zone/1` at most 1, `Zone/3` none) and on the missed bells (group `Soak/2` at most 2). When every drill of the
programs has a bar, "Problems" lists only what breaks it; a program with any other entry (the default rotation,
`barrage`, ...) keeps the old rule, every failure of the member under test. Several barred drills in one sweep share
the ledger's tags, so a tag is gated if any of them gates it. The index also flags a program longer than the fight
(older reports: estimated from the bar table's cycle lengths) and a nonzero `summary.programStartLagMs` (the program
started on a stale game clock, so its later entries ran early). `run` warns before launching a comma program longer
than `--duration` and `;` programs the iterations do not split evenly. To sweep several build drills, run each alone
(`--programs sfk-hunt:4`) or alternate them (`--programs 'deadmines-followups;sfk-hunt:4;scholomance-shapes:3'
--iterations 6`).

### The boss descriptor slice and counters (M5)

The dungeon mechanics M5 descriptor (interrupts, dispels, purges, target priority, the ignore list) runs in the sim as
the **descriptor slice**: mod-boss-mechanics' `descriptor` program (casts to kick, a do-not-kick cast, dispellable,
urgent and deadline debuffs, purgeable and Enrage buffs on adds, a priority add, ignored copies and a break-out
prison; 64 s) twice in a row, `descriptor:2`, so a 120 s iteration sees it start twice as the 300403 dummy's loop does.
It is not in the default rotation; the M4 slices are unchanged. Its casts, adds and auras come from program entries on
the owner, so they run on the sim's boss stand-in (`SimTarget` 900004-900006) as on the dummy; adds and prisons spawn
4-8 yd around it at its level. While a program with descriptor entries runs, the owner carries the reworked bosses'
immunities (CreatureImmunitiesId -273: stun, silence, fear ...; kicks land), as 300403 and a reworked boss do; the
template's set (-26, grips only) comes back when the program stops, and the M4 slices never change it.

```
MECHSIM=1 MECHSIM_PROGRAMS="descriptor:2" tools/run-sim.sh RetPaladinSim 120 60 2 5 100   # files tagged mech-desc
tools/mechanics_sweep.py run --descriptor            # every reworked spec, descriptor slice + baseline
tools/mechanics_sweep.py run --descriptor --specs shaman,warlock
```

Any single drill (`interrupts`, `dispels`, `purges`, `targets`, `ignore`) or `descriptor-drills` (all five in turn,
about 430 s) runs through `--programs` / `MECHSIM_PROGRAMS` as any other program.

Every member's module counters carry the M5 blocks of `MechanicBotCounters.h` (`stats.counters`, summed over the
iterations; a name ending in `Max` takes the maximum):

| Counter | Meaning |
| --- | --- |
| `kicksLanded` | kicks on a listed cast this bot held the claim of |
| `kicksWasted` | kicks on an unlisted cast while a listed cast was due before the kick was back |
| `doNotKickKicks` | kicks on a do-not-kick cast (a violation; the sweep flags a spec with any) |
| `duplicateKicks` | kicks on a listed cast another bot had claimed |
| `overloadHolds` | casts the bot could kick but held for a higher one due |
| `listedMissed` | listed casts that completed; counted by **one bot per group**: only the group sum is whole |
| `stockKicksDropped` | stock kick actions the descriptor's kick multiplier zeroed |
| `castStops` | stuns, silences, incapacitates, fears outside the kick table judged as kicks (also counted above) |
| `urgentDispels`, `urgentLatencyMsMax` | cures that removed a listed loss-of-control aura; longest time to removal |
| `deadlineDispels`, `deadlineMisses` | deadline auras cured in time, and the ones that ran out on this bot |
| `listedDispels`, `purges` | other listed cures; listed enemy buffs stripped (the pet's Devour Magic included) |
| `dispelWrongAura` | cures that removed another aura while an urgent or deadline one of its type stayed |
| `focusSwitches`, `msLowerTarget` | switches onto the pick; ms attacking something else while the pick lived |
| `breakOutMsMax` | the longest a prison held its player, as this bot saw it |
| `ignoredHits`, `ignoredDamage` | damage events and damage the bot dealt to ignored units |
| `petIgnoredHits`, `petIgnoredDamage` | the same for its pets, guardians and totems |
| `ignoreBlocks`, `ignoreDrops`, `petRecalls` | actions zeroed for an ignored target; targets dropped; pets recalled |
| `solveRefreshes`, `refreshUsMax`, `refreshUsTotal` | M5 C4: the allies' refresh before a solve, timed apart (\*) |

(\*) `solveUs` no longer holds the refresh: compare an older `solveUsMax` with `solveUsMax + refreshUsMax`.

The report page has a "Boss descriptor" table (every member plus a group row) and `refreshUsMax` in the brain table.
The sweep index puts the counters under each member line's `descriptor` and the group's sums under the spec's
`descriptorGroup` (`index.json`), and `index.md` gets a "Boss descriptor" table (group totals, the member under test in
brackets) when the sweep ran the slice or any run has a descriptor counter. Lower-priority target **time** stands in
for damage on lower targets: the sim records damage on the boss only.

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
