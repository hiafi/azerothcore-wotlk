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
