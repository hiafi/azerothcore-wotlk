# item-tools (`apps/item-tools/`)

A local web UI for browsing/editing `item_template` directly - see
`apps/item-tools/README.md` for the full design rationale. Sibling of
`apps/dbc-tools` but deliberately simpler: items have no client-side DBC to
rebuild, so there's no `generate.py`/MPQ pipeline, just a read of
base-dump-⊕-migrations (`lib/overlay.py`) and a write of one guarded SQL
statement per save (`lib/emit.py`).

## Load-bearing gotcha: `item_template` can't be DELETE+INSERTed

`item_template` (along with `creature_template`, `gameobject_template`,
`quest_template`) is on `apps/codestyle/codestyle-sql.py`'s `not_delete`
list - a `DELETE FROM item_template` fails the linter outright. If you're
hand-writing an `item_template` change instead of going through the
webui, match the two conventions already established in this repo's
history:

- **Editing an existing row**: a plain `UPDATE ... SET <changed cols> WHERE
  \`entry\` = N AND <changed cols> = <old values>` - guarded on the old
  value of every column you're changing, so re-running an already-applied
  file is a no-op instead of an error. See the Conjure Refreshment item-level
  edit (originally `rev_1787824212353499531.sql`) inside
  `data/sql/updates/pending_db_world/frost_mage_rework.sql` (the merged
  Frost Mage rework migration) for a real example.
- **A brand-new row**: `INSERT INTO item_template (...) VALUES (...) ON
  DUPLICATE KEY UPDATE col = VALUES(col), ...` - an upsert, both idempotent
  and never needs a `DELETE`. See the `creature_template` precedent this
  was modeled on (originally `rev_1787563173168071680.sql`), also inside
  `data/sql/updates/pending_db_world/frost_mage_rework.sql`.

`apps/item-tools/lib/emit.py` generates exactly these two shapes; you
shouldn't need to hand-write either if you're going through the webui.

**Pending migrations live under `item_weight_system/`.** Every pending
migration this system has produced (reference-table population,
`item_budget_*` templates/assignments, and the materialized
`item_template` regenerates that follow from them) lives under
`data/sql/updates/pending_db_world/item_weight_system/`, kept apart from
this fork's other, unrelated pending SQL so the whole system's history is
browsable in one place. Purely organizational: both the real
`DBUpdater` (`UpdateFetcher::Update` in
`src/server/database/Updater/UpdateFetcher.cpp`) and this app's own
base-⊕-overlay readers (`lib/overlay.py`'s and `lib/budget_overlay.py`'s
`_contributing_files()`) key applied/replayed migrations off bare
filename, not directory path — confirmed live, moving Buckets 1-2's ~20
files into that subdirectory changed nothing about which rows either one
computes. Don't add a non-`.sql` file (a `README`, etc.) inside it, though
— `apps/codestyle/codestyle-sql.py`'s file walk isn't extension-filtered
and would try to lint it as SQL.

**Guarding a `FLOAT` column** (`dmg_min1`/`dmg_max1`/`spellppmRate_N`) needs a
small-tolerance comparison, not exact `=`, whenever the old value is itself a
*previously computed* float rather than clean original data - MySQL's 32-bit
storage doesn't reliably round-trip a Python `repr()`'d value back to exact
equality even when both print identically. `lib/emit._guard_term()` handles
this automatically (used by both `write_update` and `budget_emit`'s
`_update_statement`) - see `docs/bugs-and-fixes.md`'s entry on this for the
live incident that found it. Don't hand-roll a guard clause on a float
column without it.

## Budget templates (`/templates`)

Hand-authors the percentage-allocation itemization system's
`item_budget_template`/`item_budget_assign` (`docs/itemization-changes.md`
§9.1/§9.8), and regenerates an item's real `item_template` stats from them.
Two new modules carry this, both still no-live-DB:

- `lib/budget_overlay.py` - a generic DELETE+INSERT replay reader (this
  table family's actual convention, unlike `item_template`'s guarded UPDATE
  - see `lib/overlay.py`'s module docstring and this file's "Load-bearing
  gotcha" above) for every budget-system table, reference tables included.
- `lib/budget.py` - a Python port of `ItemBudget.cpp`'s `ResolveBudget()`.
  A **separate implementation of the same formula**, not a call into the
  C++ - if that formula ever changes (the deferred custom-stat-ID fix
  mentioned in `docs/itemization-changes.md` §5, for instance), this needs
  a matching hand-edit or item-tools' previews/writes will silently drift
  from what the live worldserver actually materializes. Both files carry a
  comment pointing at the other for exactly this reason.

## Dungeon/raid loot browser

`/dungeons` and `/dungeons/<map_id>` (`lib/loot.py`) join `creature` +
`creature_template` + `creature_loot_template`/`reference_loot_template`
against `item_template` to show what drops where, with a link into each
item's edit form. Those tables (plus `instance_encounters`, used for boss
detection - see the next paragraph) are read from their **base dumps
only** (no pending-SQL replay) - see the README's "Known limitations"
before assuming a change to creature loot shows up there immediately.

**Boss vs "Trash Drops" isn't `rank`.** A dungeon's own boss is `rank ==
CREATURE_ELITE_ELITE`, identical to its trash - only a raid's bosses are
reliably `rank == CREATURE_ELITE_WORLDBOSS`. So boss detection is instead
built from `instance_encounters` (real achievement/kill-credit data,
`creditType == ENCOUNTER_CREDIT_KILL_CREATURE` rows give a creature_template
entry), unioned with the WORLDBOSS-rank signal as a fallback. See
`lib.loot._boss_creature_entries`'s docstring for the coverage gaps (a
boss with no instance_encounters row, or one summoned dynamically rather
than statically spawned, won't be flagged and simply won't appear).
