---
name: dbc-deploy
description: Full content-pipeline deploy — run dbc-tools generate.py, rebuild worldserver only if C++ also changed, apply pending DB migrations via db-import, bring the server back up, and monitor the boot. Use when the user asks to deploy dbc-tools changes, run generate and migrate, push a spell/talent data change live, or says "generate, rebuild, migrate and monitor".
metadata:
  version: "1.0"
---

# dbc-deploy

Wraps the full loop for getting a `apps/dbc-tools/source/**` (or hand-added
`pending_db_world/*.sql`) change live: **generate → (rebuild) → migrate → boot → monitor**. Read
`.agents/docs/systems/dbc-tools.md` and `apps/dbc-tools/README.md` first if you haven't already —
this skill is the deploy mechanics, not the data-authoring rules (classmask scoping etc. — see the
`classmask-scope-audit` skill for that).

Per `AGENTS.md`, only run this when explicitly asked.

## Step 1 — Generate

```bash
cd apps/dbc-tools && .venv/bin/python3 generate.py
```

(fall back to plain `python3 generate.py` if `.venv` doesn't exist). This reconciles every
`source/spells/*.csv` and `source/talents/*.yaml` entry against what's actually live and, only for
what changed, emits a new `data/sql/updates/pending_db_world/rev_*.sql` file plus (if the relevant
base DBCs were extracted into `var/extractors/dbc/`) an updated `var/dbc-patch/`. **If nothing
changed, it says so and produces no new file — that's success, not a bug**, don't go looking for a
migration that was never meant to exist.

**Read the output before moving on.** A `WARNING:` line means `lib/lint.py`'s
`check_classmask_scoping` (or another check) found a likely-broken `SpellMod` scoping — almost
always a real bug (see the `classmask-scope-audit` skill), not noise. Stop and flag it to the user
rather than deploying through it, unless they've explicitly said to proceed anyway.

## Step 2 — Decide whether a rebuild is needed

Content that's pure DBC/SQL data (new spell/talent rows, retuned values, a `SpellMod`) is **fully
live from the SQL migration alone** once imported — `ObjectMgr`/`SpellMgr` load `spell_dbc`/
`talent_dbc` etc. as a DB overlay at boot, no C++ involved. A rebuild is only needed when the change
also touches a `.cpp`/`.h` file (a new `AuraScript`/`SpellScript` hook, `Register()` binding, engine
code) — extremely common in this fork's reworks (a new spell id usually pairs with a new script),
but not universal.

Check what's actually changed:

```bash
git status --short -- src/
```

- **Nonempty** → C++ changed. Follow the `rebuild-worldserver` skill for the build (Steps 0-3 of
  that skill), but **stop before its Step 4** (bringing the container back up) — migrations need to
  land first, and the container should come back up already pointed at the post-migration DB.
- **Empty** → data-only. Skip straight to Step 3; no image rebuild needed, only the restart in
  Step 4.

## Step 3 — Apply the migration

`ac-db-import`'s image bind-mounts the host `./data` directory (see
`docker-compose.override.yml`'s comment on this), so a new `pending_db_world/*.sql` file takes
effect on a plain run — **no image rebuild needed for this step even when Step 2 also rebuilt
worldserver for unrelated C++ changes**:

```bash
docker compose up ac-db-import
```

This is a one-shot container — it exits when done. Confirm it actually applied the file (not just
that the container exited 0):

```bash
docker compose logs ac-db-import --since 5m | grep -iE "rev_|error|fail"
```

If it fails with something like `Duplicate column`/`Table already exists` on a file that should be
new, stop — that's very likely the DB already having the change applied outside the tracked
migration path. Read `docs/bugs-and-fixes.md`'s "`db-import` fails with..." entry before doing
anything else; the fix is almost never "delete the file and re-run."

## Step 4 — Bring worldserver up and monitor

If Step 2 found C++ changes and you already ran the `rebuild-worldserver` skill's build step, its
image is already built — just do that skill's Steps 4-6 now (start, wait for `ready...`, check for
DBC/script validation errors in the boot log).

If Step 2 was data-only (no rebuild), the existing image is fine — just restart the container so it
re-reads the DB overlay it loads at boot:

```bash
docker compose stop ac-worldserver
docker compose up -d ac-worldserver
timeout 120 bash -c 'until docker logs ac-worldserver 2>&1 | grep -q "ready\.\.\."; do sleep 2; done'
docker logs ac-worldserver --since 5m 2>&1 | grep -iE "did not match dbc effect data|error|warn"
```

## Step 5 — Client patch (only if this changed something the client renders)

A new spell/talent's **name, icon, tooltip, or talent-tree position** needs the client-side DBC
patch too, not just the SQL (see `apps/dbc-tools/README.md`'s "Why this works the way it does") —
pure server-side tuning (damage, proc chance, a C++ hook's behavior) does not. If this deploy
included client-visible changes and a `patch-service` instance is running for this environment
(`docker ps --filter name=patch-` — gitignored, per-operator, not always present), trigger an
immediate manifest refresh rather than waiting for its timer:

```bash
python3 apps/patch-service/manifest_gen.py
```

Skip this step entirely if no `patch-` containers are running, or the change was server-only.

## Step 6 — Report

State plainly, in order: what `generate.py` produced (or "nothing changed"), whether a rebuild ran
and its result, whether the migration applied cleanly, the restart/boot result, and whether the
client patch step ran. If any step was skipped, say which and why (e.g. "no rebuild — this was
data-only").
