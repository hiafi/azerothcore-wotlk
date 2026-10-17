---
name: class-rework
description: Run this repo's phased process for reworking a class's abilities/talent tree — design doc, dbc-tools data, C++ hooks, build/deploy, playtest guide. Use when the user asks to rework, retune, or overhaul a class's talents/abilities.
metadata:
  version: "1.2"
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

The design doc follows `docs/reworks/TEMPLATE.md`: one shared doc per class plus one doc per spec,
and for every spell and talent a block with slot and stock replacement, the exact tooltip, values
tagged `[fixed]`/`[tune]`, rules (what it triggers from, stacking, pets), what it isn't affected by,
and open questions. If the user's doc isn't in that shape, list the missing pieces (tooltips apart
from values, no "Replaces", unanswered edge cases) and get them before planning; converting a loose
doc later cost the hunter rework a reconcile pass and two question rounds. This is the spec
everything else derives from — pull actual
current values from the live DBC/DB via `apps/dbc-tools`, don't reconstruct from memory of stock
WotLK talents; several "this needs C++" calls only became clear by checking what data the pipeline
can already express (see `apps/dbc-tools/README.md`'s `SPELL_AURA_*`/`raw_overrides` coverage).

## Large reworks: staging, specs and agents

For a whole class (several specs, a pet system, shared baseline changes), the work runs as stages:
a harness session plans, reviews, builds, deploys and commits, and each stage is implemented by a
separate session from a handoff file in `.agents/plans/<class>-rework/`. The hunter rework (three
specs plus pets) took far longer than earlier classes; these rules come from what cost the most.

- **Write each spec's work package just in time.** Up front, plan only what every stage shares:
  the class-wide changes, ID blocks, family-bit map, rulings and stage order. Write a spec's detailed
  package right before its stage, from the design doc and the code as it is then. Hunter's three
  packages, written before any code landed, had 23 and 29 stale lines by the time MM and SV ran,
  and each needed a large verification pass first.
- **Prototype the client-visible mechanics first.** Before writing packages, deploy one throwaway
  spell per mechanic type the class uses (a cast-time spell, an instant, a proc buff the player
  must see, a pet ability, a "next cast is instant" proc) and check it in-game. Every item in
  `.agents/docs/systems/custom-spells.md` was a playtest surprise that cost a fix stage and a
  rebuild.
- **Spend Opus where it pays.** In a stage session: Sonnet at medium effort for mechanical work
  packages (data rows, tests, tooltips, playtest guides, small fixes); Sonnet high or Opus medium for
  C++ mechanisms; Opus high for reviews, diagnosis and spec or handoff drafting. Run one in-stage
  review, not three, plus the harness's independent Opus review of the diff; the independent review
  found the misses that mattered. Don't spawn a verification agent for something a grep answers.
- **Size each piece of work.** Small fixes (a few values, one file) the harness does directly; medium,
  single-implementer stages the harness launches itself as a background subagent from the handoff file
  (Sonnet by default); only big, orchestrated stages go to a separate user-run session.
- **Bundle playtest fixes.** Collect a playtest's findings into one fix handoff and one deploy rather
  than a build per finding.
- **Every handoff** names its preconditions (HEAD, clean tree, boot baseline), the absolute report
  path, and a predicted boot `Loaded`/`Validated`/"is not assigned" delta; the harness appends each
  deploy to the plan's deploy log so the next stage's preconditions can be checked.

## Phase 1 — New abilities/auras

Net-new spells/auras the tree will reference (a new proc effect, a new debuff, a new resource-like
mechanic) — built first because talents in Phases 2-3 grant or interact with these, not the other
way round.

- New spell IDs come from `apps/dbc-tools/source/ids.yaml`'s reserved block; add rows to
  `source/spells/<class>.csv` (learned-outright) or `<class>_talents.csv` (talent-point-granted).
  Never pick numbers ad hoc — see `apps/dbc-tools/README.md`'s "Source files".
  - **A new damage, heal, or absorb effect's number is a potency value
    (`sp_potency=`/`ap_potency=`/`potency_kind=`), not a hand-set `base_points=`/
    `points_per_level=`/`die_sides=`** — read `.agents/docs/systems/potency.md` before writing one;
    it covers the DSL fields, what's deliberately excluded (script-driven values, percent-of-other-
    damage effects, legacy rank-capped spells, pet/guardian casts), and the `{potN}`-style tooltip
    placeholders a potency effect's description needs (skipping them isn't cosmetic — the tooltip
    comes out missing the caster's live spell power/attack power entirely, not just simplified).
  - **Sign convention:** stored `base_points` is the live value minus 1 (die_sides=1 makes the
    engine add 1 back); a "-30%" reduction is stored as `-31`. This applies to effects that aren't
    potency (buffs, procs, stat mods, thresholds, flat percentages) and to **static rows** only.
    Values a script passes in depend on the API:
    - `CastCustomSpell`, `CastSpell` with `CustomSpellValues`, `SPELLVALUE_BASE_POINTn`: pass the
      **live** value (`-30` for -30%). `Spell::SetSpellValue` already runs it through
      `SpellEffectInfo::CalcBaseValue`, which subtracts 1 when `DieSides != 0`, and the die adds it
      back. Passing live − 1 comes out one point low.
    - A raw `baseAmount` into `Aura::TryCreate` / `TryRefreshStackOrCreate`: pass the **stored**
      value (live − 1). It goes straight into `CalcValue`, which adds the die roll.
    - `AuraEffect::SetAmount` / `ChangeAmount`, `SetHitDamage`, `SetEffectValue`: the **live** amount.
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
- **A talent that raises another spell's damage or healing by a percent** (`MOD_DAMAGE_PERCENT_DONE`,
  a `SPELLMOD_DAMAGE` effect, and the like) never shows on that spell's tooltip by itself. Combat
  includes it, the preview doesn't. Add the talent to the affected spells' `tooltip_vars` entry
  with `talent_mult(...)`, counting each of its effects that applies, and make sure those spells'
  descriptions use `{potN*var}`. Spells that still carry a stock `SpellDescriptionVariableID`
  (167 for Frost, and so on) need moving to the class's own entry, because stock chains check the
  old talent ranks and values. Ask the user which talents count: cross-tree ones are a design call.
  See `.agents/docs/systems/potency.md`, "Showing a talent's bonus on a tooltip".
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
  new/changed pending SQL migration takes effect on `docker compose up --no-deps ac-db-import` — **never
  rebuild the `ac-db-import` image** for SQL (it recompiles the whole tree, about 30 minutes); rebuild
  only `ac-worldserver`, and only for C++ changes. Keep the server up during the compile and stop it just
  before the import (characters SQL needs it stopped).
- After a rebuild+deploy, **grep the worldserver boot log for `did not pass Validate()` /
  `Validated N scripts`** — this is the cheapest way to catch a silently-dropped script (see
  Phase 3's talent-id/spell-id pitfall) before it wastes a playtest session.
- `apps/dbc-tools/generate.py`'s client patch (`patch-Z.mpq`) auto-deploys to
  `<DEPLOY_ROOT>/Data/patch-Z.mpq`, where `DEPLOY_ROOT` is this box's patch-root from
  `apps/dbc-tools/lib/local_config.py` (gitignored — see `local_config.py.example`; guarded by
  that directory existing, so it's a no-op on a checkout without a `local_config.py` or without
  this host's `apps/patch-service` setup) — testers' `patch-client.bat`
  picks it up once `manifest.txt` is refreshed. `patch-manifest-gen`'s files are root-owned inside
  its container, so force an immediate refresh with `docker restart patch-manifest-gen` rather than
  running `manifest_gen.py` directly as a normal user (it'll hit a `PermissionError`).

## Related docs

- `.agents/docs/systems/custom-spells.md` — engine and client gotchas for custom spells (cast bars,
  ranged-slot cast times, visible auras, triggered casts, Cooldown Haste); read before Phase 1.
- `docs/reworks/TEMPLATE.md` — the design doc format Phase 0 expects.
- `.agents/docs/systems/potency.md` — how a damage/heal/absorb effect's numbers should be authored
  (Phase 1), from the Warlock pilot (P4) onward.
- `docs/dbc-build-pipeline.md` — why DBCs are generated artifacts, not hand-edited.
- `apps/dbc-tools/README.md` — full pipeline usage (pulling existing data, the web UI, known
  limitations).
- `.agents/docs/cpp-scripts.md` — script registration conventions.
- `docs/bugs-and-fixes.md` — check before re-diagnosing a mysterious failure; add an entry once
  you've root-caused one from this process.
