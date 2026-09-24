# Upstream merges and custom core edits

This fork tracks `upstream/Playerbot` (`mod-playerbots/azerothcore-wotlk`). A fork edit inside an
upstream-owned file can vanish in a merge **without a conflict** — e.g. when upstream moves the
function it lived in to another file. Conflicts are loud; silent drops are the danger.

## Writing custom code

- Prefer, in order: DBC/DB data (`apps/dbc-tools`) → `SpellScript`/`AuraScript` → an existing
  `ScriptMgr` hook (`src/server/game/Scripting/ScriptDefines/`) → an inline core edit.
- Neutralize a stock hardcode by changing the data it keys on (icon, talent spell id, family flag,
  aura state) rather than deleting upstream lines, when that makes it permanently inert. A pure
  deletion is the one edit the guard can't see (below).
- New behaviour for stock scripts goes in a new fork file (`spell_<class>_<spec>.cpp`) rebound by
  SQL, rather than rewriting the stock class in the upstream-owned `spell_<class>.cpp`.
- An unavoidable core edit is one line calling a `<Class>::` function in
  `src/server/game/Entities/Unit/<Class>Mechanics.h/.cpp` (or a small block), with a `// Custom:`
  comment saying why.

## The guard

`python3 apps/merge-guard/merge_guard.py` needs no manifest or markers — it reads git history.
For every upstream-owned file the fork had modified, it takes the lines the fork added (vs the
upstream it was based on) and checks each one is still in that file after the merge:

- `MISSING` — the line is gone (fails). A `moved? now in:` hint names other files touched by the
  merge that now hold the same line (upstream moved the code).
- `CHANGED` — gone, but a similar new fork line is in the same file (reformatting or conflict
  resolution). Doesn't fail; eyeball it.

Validated against the lossy 2026-09-20 update: `check --result aa32e0dde --upstream 7f12e89ee`
reports exactly the four dropped 100%-hit lines, with `HitChance = 10000;` traced to `Object.cpp`.

## Merge procedure

1. `git fetch upstream`, then merge `upstream/Playerbot` and resolve conflicts.
2. Before committing (or right after — it then compares with `HEAD^1`):
   `python3 apps/merge-guard/merge_guard.py check`.
3. For each `MISSING`: find where upstream moved the code (`git log -p upstream/Playerbot -- <file>`,
   the `moved?` hint) and re-apply the edit there. Re-run until clean.
4. Build, then commit.

`list` prints the fork's added-line count per upstream-owned file — a quick view of the custom
surface. Background: `docs/bugs-and-fixes.md`, "A `// Custom:` core edit silently disappears after
an upstream merge".
