---
name: rebuild-worldserver
description: Rebuild the ac-worldserver (or ac-authserver) docker image from current source, stop the running container first, bring it back up, and monitor the boot for readiness/errors. Use when the user asks to rebuild the server, restart worldserver with new code, redeploy a C++ change, or says "rebuild and test"/"rebuild and monitor".
metadata:
  version: "1.0"
---

# Rebuild worldserver

Rebuilds the `ac-worldserver` docker image from the current working tree (C++ changes take effect
only after this — `AGENTS.md`: don't run this unless the user asked, but once asked, follow this
skill rather than ad hoc commands). `args`: `authserver` to target `ac-authserver` instead; default
is `ac-worldserver`. Everywhere below, substitute the chosen service/container name.

If this rebuild is part of a content pipeline (dbc-tools `generate.py` output, a new/edited
`pending_db_world` migration), use the `dbc-deploy` skill instead — it wraps this skill with the
generate + migrate steps in the right order.

## Step 0 — Sanity check before spending a build

A full worldserver rebuild on a loaded host regularly takes **30+ minutes**, so it's worth a few
seconds up front to avoid burning that on something broken or pointless:

- `git status --short -- src/` (or the specific files you changed) — confirm your edits are still
  actually on disk. If you added temporary debug logging earlier in this session and it's now
  missing, something reverted it (another concurrent session, a cleanup pass, a stash) — re-add it
  and verify with `grep` before building, not after; discovering this only once the 30-minute build
  finishes is exactly the mistake this note exists to prevent.
- If the change is script/AuraScript code, skim it once for obvious scope errors — the most common
  one hit in practice: calling `GetEffIndex()` (or anything else that's only a member of
  `AuraEffect`) from inside an `AuraScript` hook like `CheckProc` that isn't handed an `AuraEffect*`
  — it compiles fine as a name lookup failure (`fatal error: use of undeclared identifier`), so
  nothing catches it before the build does.

## Step 1 — Stop the running container first

Always stop the target container before starting the build, even though the build itself doesn't
strictly require it — a stale running server is easy to mistake for the new one once the build
finishes, and this project's convention (confirmed by the user) is to stop it explicitly:

```bash
docker compose stop ac-worldserver
```

## Step 2 — Build, with output you can actually read

```bash
docker compose build ac-worldserver > /tmp/<scratch>/build.log 2>&1
```

Run this **in the background** (`run_in_background: true` on the Bash tool, or equivalent) — it's
long. **Redirect straight to a file with `>`, never pipe through `| tail -N`.** `tail` buffers its
entire input and only prints once the upstream command's output stream closes, so a `| tail -100`
pipeline shows **nothing** until the build finishes or fails — indistinguishable from a hang. A
plain `>` redirect lets you `tail -f`/re-`Read` the log file at any time to see live progress.

While it runs, you can confirm it's actually making progress (as opposed to stuck) without reading
the log: `docker stats --no-stream <buildkit-container-name>` a couple of times a few seconds apart
— CPU usage should be bursty-but-nonzero across samples, especially on a busy shared host where
`make`/`ninja` jobs briefly spike well above 100%.

## Step 3 — Wait for it, then check the result

Do **not** `sleep N` in a loop to poll a background build — either let the harness's background-task
notification tell you when it's done, or if you must poll, use a bounded `until` loop
(`until grep -q ... ; do sleep 5; done`), never a chain of bare `sleep`s (blocked in this harness for
exactly this reason).

When it finishes, check both the exit status and the log for the actual failure text — a failed
`docker compose build` still exits the *shell wrapper* with whatever status, but the useful signal
is in the log:

```bash
grep -n "error:" /tmp/<scratch>/build.log   # compiler errors (clang/g++), with file:line
grep -n "FAILED:" /tmp/<scratch>/build.log  # ninja's own failure marker
tail -20 /tmp/<scratch>/build.log           # final lines either way
```

If it failed: report the exact `file:line: error: ...` text, fix it, and re-run Step 2 — ccache
makes the retry much faster than the first build since everything up to the broken file is cached.
Do **not** proceed to Step 4 on a failed build; the old image is still what's tagged, and starting
the container back up just re-runs the pre-fix binary, which is a common source of "I rebuilt but
nothing changed" confusion.

If it succeeded, the log ends with `<service> Built` (or `naming to ... done` from a plain
`docker build`).

## Step 4 — Bring it back up and confirm it's actually ready

```bash
docker compose up -d ac-worldserver
```

Then wait for boot completion with a bounded loop, not a guess-and-check sleep:

```bash
timeout 120 bash -c 'until docker logs ac-worldserver 2>&1 | grep -q "ready\.\.\."; do sleep 2; done'
```

## Step 5 — Look past "ready" for silent problems

A clean "ready..." line does not mean every script bound correctly. Check the boot log for
validation errors that print but don't stop the boot — these mean a script you just changed (or one
elsewhere it collided with) silently isn't running in-game:

```bash
docker logs ac-worldserver --since 5m 2>&1 | grep -iE "did not match dbc effect data|error|warn" 
```

The most common one: `Spell <id> Effect Index: EFFECT_n ... of script <name> did not match dbc
effect data - handler bound to hook <hook> of SpellScript won't be executed` — the script's C++
`Register()` call references an effect index/type the spell's actual DBC data doesn't have at that
index. Fix by correcting either the DBC row (`apps/dbc-tools`) or the `Register()` call, not by
ignoring it.

## Step 6 — Report

State plainly: build duration, pass/fail, the container's current status, and whether the boot log
was clean or had validation errors (quote them). If the user is about to retest something in-game,
remind them the server just restarted — any character that was online is now logged out.
