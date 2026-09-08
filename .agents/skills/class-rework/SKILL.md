---
name: class-rework
description: Run this repo's phased process for reworking a class's abilities/talent tree — design doc, dbc-tools data, C++ hooks, build/deploy, playtest guide. Use when the user asks to rework, retune, or overhaul a class's talents/abilities.
metadata:
  version: "1.0"
---

# Class rework

The process this fork uses to take a class from "here's the new design" to "live and
playtestable," used for the Frost Mage and Protection Warrior reworks. Five phases, done in
order — each one only makes sense once the previous is real. Read `AGENTS.md`'s "Mandatory
reading per task" for the docs each phase's edits require (`cpp-guidelines.md`, `cpp-scripts.md`,
`sql-guidelines.md`); this skill is the glue between them, not a replacement.

Don't start coding before Phase 0 is written down and, for anything beyond a small tweak, don't
start Phase 1 before the user has signed off on a plan (`ExitPlanMode`) covering the concrete
spell/talent IDs, new C++ classes, and any ambiguous design calls (see "Judgment calls" below) —
several of the mastery-formula and stacking questions in past reworks only got resolved because
they were flagged explicitly in the plan doc rather than assumed.

## Phase 0 — Design doc

Write `docs/<class>_rework.md`: every new spell/aura in prose (what it does, numbers, duration,
stacking rules), then the talent tree row by row (name, ranks, effect per rank, capstone bonus if
the last rank unlocks bonus behavior). This is the spec everything else derives from — pull actual
current values from the live DBC/DB via `apps/dbc-tools`, don't reconstruct from memory of stock
WotLK talents; several "this needs C++" calls only became clear by checking what data the pipeline
can already express (see `apps/dbc-tools/README.md`'s `SPELL_AURA_*`/`raw_overrides` coverage).

## Phase 1 — New abilities/auras

Net-new spells/auras the tree will reference (a new proc effect, a new debuff, a new resource-like
mechanic) — built first because talents in Phases 2-3 grant or interact with these, not the other
way round.

- New spell IDs come from `apps/dbc-tools/source/ids.yaml`'s reserved block; add rows to
  `source/spells/<class>.csv` (learned-outright) or `<class>_talents.csv` (talent-point-granted).
  Never pick numbers ad hoc — see `apps/dbc-tools/README.md`'s "Source files".
  - **Sign convention:** stored `base_points` is the live value minus 1 (die_sides=1 makes the
    engine add 1 back); a "-30%" reduction is stored as `-31`. Applies to `CastCustomSpell` basepoints
    too, not just static rows.
- If a mechanic needs a hook with no `SpellScript`/`AuraScript` equivalent (e.g. "reduce damage
  after a block-value subtraction already happened in core combat math"), don't grow
  `Unit.cpp`/`Player.cpp` inline. Add `src/server/game/Entities/Unit/<Class>Mechanics.h`/`.cpp`
  (mirror `MageMechanics.h`/`.cpp`) exposing one free function per mechanic in a `namespace
  <Class> { ... }`, then wire it into the core file with a single `#include` and a single call
  site. Keeps class-specific logic out of the shared hot files.
- If several talents will grant the same kind of effect (e.g. a stacking absorb shield), build one
  shared helper now (`Grant<Effect>(caster, amount, refreshDuration)` in the class's spell script
  file) that Phase 2/3 talents call into, rather than duplicating the grant logic per talent.
- **Judgment calls to get from the user, not assume:** how a percentage-based grant composes with
  a percentage stat like mastery — confirm whether it's applied to the base amount alone or to the
  combined (base + per-target/per-stack bonus) total, and whether multi-stack scaling is additive
  or multiplicative. Write the answer into the plan doc once confirmed so later phases don't
  re-ask.

## Phase 2 — Data-only talents

Everything the tree needs that's expressible as pure `apps/dbc-tools` data — plain aura mods,
existing `SPELL_AURA_*` types, `spell_bonus_data` coefficients, classmask-scoped `SpellMod`
effects. No C++ in this phase; if a talent clause needs one, defer it explicitly to a running list
for Phase 3 (name the talent + the exact clause, not just "needs code") rather than fudging it with
data that's close but not quite right.

- `python3 apps/dbc-tools/generate.py` after each batch of edits; read its stdout — it prints
  which IDs it's minting vs. editing, and `WARNING:` lines from `lib/lint.py` about classmask
  scoping are real bugs, not noise (see the README's `EffectSpellClassMaskA/B/C` gotcha — this
  exact mistake has shipped more than once).
- Talent tab placement (tier/column) needs a free slot — check the live tab's existing entries in
  `source/talents/<class>.yaml` before assigning one, not just the next unused-looking number.
- `apps/dbc-tools/lib/test_sql_dump.py` and `apps/codestyle/codestyle-sql.py` clean before moving
  on.

## Phase 3 — C++ talents

The deferred-from-Phase-2 list: procs, capstones on the last rank of a talent, cross-talent
interactions, anything reading another talent's tuned value at cast/hit time.

- **Read a talent's tuned value live** via the marker-aura-by-icon idiom: give the talent's rank
  spells a `SPELL_AURA_DUMMY` effect on an otherwise-unused effect slot, with a genuinely unique
  `SpellIconID`, then read it with `caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_<CLASS>,
  <icon>, <effIndex>)->GetAmount()`. Since only one rank of a talent is ever known at once, keying
  by icon (not spell id) means the read doesn't care which rank is active. Pick a new icon per
  talent — reusing one collides lookups across unrelated talents.
- **Talent id ≠ spell id.** `talent_dbc`'s own id (the YAML's `id:` field) is a different space
  from the actual learnable/castable spell id (`rank_spell_ids`). `HasAura()`, `ValidateSpellInfo`,
  and any `sSpellMgr->GetSpellInfo()` lookup need the **spell** id. Passing the talent id compiles
  fine and fails silently at runtime — `ValidateSpellInfo` just drops the whole script from that
  spell with a one-line warning in the boot log, no crash. After wiring any new `Validate()` list,
  **grep the boot log for `did not pass Validate()`** before declaring the phase done; a script
  that silently didn't register is the single most common failure mode here.
- `spell_script_names` needs an explicit DELETE-then-INSERT row for every new/changed class,
  shipped in the same pending SQL migration as the C++ (`cpp-scripts.md`). The linter
  (`codestyle-sql.py`) requires the DELETE to be one physical line immediately before the INSERT —
  a logically-equivalent multi-line DELETE fails the check even though it's correct; match the
  single-line format already used elsewhere in `data/sql/updates/db_world/`.
- Match the file's existing precedent for numeric handling (e.g. explicit `int32(...)` casts around
  `CalculatePct` results assigned to signed locals) rather than introducing a new style.
- Register every new class in the file's `AddSC_<class>_spell_scripts()`.

## Phase 4 — Playtest guide

Write `docs/<class>_playtest.md` once Phase 3 is deployed, for the user to manually verify
behavior in-game (this repo currently has no automated spell/aura test harness for this kind of
change — see `.agents/docs/e2e-policy.md` for why this isn't e2e-shaped work). Structure that's
worked before:

1. **Setup** — GM commands to reach the right level/talents/gear fast, and any caveat about
   testing against a dummy vs. a live mob (e.g. block/parry/dodge mechanics need a real attacker).
2. **Smoke test** — the fastest few actions that would reveal a totally broken build.
3. **Row-by-row checklist** — one entry per ability/talent, with the *actual tuned numbers* pulled
   from the CSV/YAML (not paraphrased from the design doc), so the tester can check a real number
   against what they see in-game.
4. **Deep-dive on high-risk items** — anything with a non-obvious interaction, a simplification
   made during implementation, or an open design question you're flagging back to the user (state
   the question explicitly; don't bury it in prose).
5. **Bug report template** — what to capture if something's off (spell id, expected vs. actual,
   repro steps) so a fix doesn't need a follow-up round of "what did you actually see."

Send it with `SendUserFile`, not just left in the repo.

## Build & deploy

The dev stack is Docker-based (`ac-worldserver`, `ac-authserver`, `ac-db-import`, the database
container), driven with `sg docker -c "docker compose ..."` (plain-shell `docker` won't see group
membership).

- `docker compose stop ac-worldserver` before rebuilding — faster than rebuilding a running
  container.
- `docker-compose.override.yml` bind-mounts `./data:/azerothcore/data:ro` into `ac-db-import`, so a
  new/changed pending SQL migration takes effect on `docker compose up -d` — **no image rebuild
  needed** for SQL-only changes, only for C++ changes to the worldserver binary.
- After a rebuild+deploy, **grep the worldserver boot log for `did not pass Validate()` /
  `Validated N scripts`** — this is the cheapest way to catch a silently-dropped script (see
  Phase 3's talent-id/spell-id pitfall) before it wastes a playtest session.
- `apps/dbc-tools/generate.py`'s client patch (`patch-Z.mpq`) auto-deploys to
  `/home/plex/wow_server/patch-root/Data/patch-Z.mpq` (guarded by that directory existing, so it's
  a no-op on a checkout without this host's `apps/patch-service` setup) — testers' `patch-client.bat`
  picks it up once `manifest.txt` is refreshed. `patch-manifest-gen`'s files are root-owned inside
  its container, so force an immediate refresh with `docker restart patch-manifest-gen` rather than
  running `manifest_gen.py` directly as a normal user (it'll hit a `PermissionError`).

## Related docs

- `docs/dbc-build-pipeline.md` — why DBCs are generated artifacts, not hand-edited.
- `apps/dbc-tools/README.md` — full pipeline usage (pulling existing data, the web UI, known
  limitations).
- `.agents/docs/cpp-scripts.md` — script registration conventions.
- `docs/bugs-and-fixes.md` — check before re-diagnosing a mysterious failure; add an entry once
  you've root-caused one from this process.
