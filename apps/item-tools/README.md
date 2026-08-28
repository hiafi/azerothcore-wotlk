# item-tools

A small local web UI for browsing and editing `item_template` - the sibling
of `apps/dbc-tools` for gear instead of spells/talents, but a deliberately
simpler design (see "Why this isn't dbc-tools again" below) since items
don't need a client-side DBC rebuild the way spells do.

## Why this isn't dbc-tools again

dbc-tools exists because `Spell.dbc`/`Talent.dbc` are client-rendered
binary files that also happen to be overlaid by a world-DB table - so it
needs a whole source-CSV → generate → SQL-and-MPQ-patch pipeline. Item
stats and tooltips are sent to the client live by the server straight from
`item_template`; there's no client binary in the loop for ordinary item
editing. That means item-tools skips entirely:

- a `generate.py`/build step (nothing to compile - a save writes SQL
  directly);
- a client patch / MPQ writer (nothing client-side to regenerate);
- a source-CSV intermediate format (there's already a queryable "source of
  truth": the base dump plus every migration on top of it - see below).

It also can't reuse dbc-tools' DELETE+INSERT-per-row edit pattern:
`item_template` is on `apps/codestyle/codestyle-sql.py`'s `not_delete`
list (along with `creature_template`, `gameobject_template`,
`quest_template`), so every edit here is a guarded `UPDATE` and every new
row an upsert `INSERT ... ON DUPLICATE KEY UPDATE` - see `lib/emit.py`'s
docstring for the exact shapes, both already established by hand elsewhere
in this repo's `pending_db_world` history before this tool existed.

## How "current state" is computed

No live database connection, no auth, no build step - same LAN-tool shape
as dbc-tools/webui. `lib/overlay.py` reads:

1. `data/sql/base/db_world/item_template.sql` - the full stock dump;
2. every `data/sql/updates/db_world/*.sql` that touches `item_template`
   (already-merged migrations);
3. every `data/sql/updates/pending_db_world/*.sql` that touches
   `item_template` (not yet merged);

and replays the `UPDATE`/`INSERT` statements it finds, in filename order,
on top of the base rows. This is enough to answer "what does the client
actually see for this item right now" without a running worldserver or
MySQL - the same base-⊕-overlay idea `apps/dbc-tools/lib/resolve.py` uses,
just without a DBC layer. It only needs to know *which rows changed*, not
evaluate real SQL - a WHERE clause's job here is "which entry/entries does
this touch", not "does the guard still hold" (see the module docstring for
why `AND col = <old value>` guards are parsed and ignored rather than
evaluated), and only two shapes are understood: `` `entry` = N `` and
`` `entry` IN (...) ``. Anything else is skipped with a `WARNING:` on
stderr rather than guessed at - if you see one, check that migration by
hand.

## Setup

```
pip install -r apps/item-tools/requirements.txt
python3 apps/item-tools/webui/app.py
```

Open `http://localhost:8601/`, or `http://<this machine's LAN IP>:8601/`
from another device on the same network - it binds `0.0.0.0` on purpose.
There's no login, so anyone who can reach that port can write pending SQL
migrations through it; keep it on a trusted home network, same caveat as
dbc-tools/webui.

## Using it

- **Dungeons & raids** (`/dungeons`) - every map in `instance_template`
  (dungeon/raid names are derived from that table's own `script` column,
  e.g. `instance_icecrown_citadel` &rarr; "Icecrown Citadel" - not
  hand-typed, so it can't drift from what the DB actually has), each
  showing how many creatures on it drop an item at or above a quality
  filter. Click through to a map (`/dungeons/<id>`) for the per-creature
  drop list - name, quality badge, ilvl, stat summary, and a link straight
  into that item's edit form. `lib/loot.py` resolves `creature` (spawns)
  &rarr; `creature_template` (lootid) &rarr; `creature_loot_template` (+ one
  level of `Reference` expansion through `reference_loot_template`)
  &rarr; `item_template`, joining that last step against the *same*
  overlay-aware rows `/items` uses - editing an item's stats and coming
  back to its dungeon page shows the edit immediately. The first request
  after starting the app parses all of `creature.sql` (~150k rows) plus
  both loot tables and is slow (several seconds); everything after that is
  served from an in-memory cache.
- **Browse** (`/items`) - search by entry ID or a name substring.
- **Edit** (`/items/<entry>`) - every friendly-grouped field from
  `lib/schema.py`'s sections, plus a required change note. Saving diffs
  your edits against the row as loaded and writes one guarded `UPDATE`
  covering just the columns that actually changed into a new
  `data/sql/updates/pending_db_world/rev_*.sql` - untouched columns never
  appear in the statement.
- **New item** (`/items/new`) - entry defaults to the next free ID in this
  tool's reserved block (`source/ids.yaml`, currently 900000-909999,
  picked clear of both the stock catalog's highest entry and any plausible
  future upstream import - see that file's header). Writes a full-row
  upsert `INSERT`.
- A save **does not** touch a running worldserver's DB. Run
  `.reload item_template` in-game (or restart worldserver) to see it live
  during a playtest.

## Known limitations

- No enum-name dropdowns for raw integer columns (`class`/`subclass`/
  `Quality`/`bonding`/inventory type/.../...) - plain numeric inputs, same
  posture as dbc-tools' spell form for the columns it doesn't model
  specially.
- `item_template_locale` (localized name/description) isn't read or
  written - only the base `item_template` row.
- The base-file WHERE-clause replay in `lib/overlay.py` understands
  `` `entry` = N `` and `` `entry` IN (...) ``  only; anything more exotic
  (a join, a subquery, `BETWEEN`) in a hand-written migration is skipped
  with a warning rather than applied. None of this tool's own output ever
  writes those shapes, so this only matters for interpreting old
  hand-written migrations.
- No concurrent-edit locking (single-user tool, same as dbc-tools/webui) -
  git is the safety net if two edits collide.
- The dungeon/raid browser (`lib/loot.py`) reads `creature`,
  `creature_template`, `creature_loot_template`, and
  `reference_loot_template` from their **base dumps only** - unlike
  `item_template`, it doesn't replay `pending_db_world`/`updates/db_world`
  changes to those four tables. Not an issue yet (no custom loot exists in
  this repo's history), but a pending change to one of them won't show up
  in the dungeon view until it's merged. `item_template` itself is always
  current either way, since the dungeon view joins against
  `lib.overlay.get_rows()`, not a fresh base-only read.
- Loot-group entries (several items competing for one drop slot via
  `creature_loot_template.GroupId`) often show a raw 0% chance - that
  column isn't a plain per-item percentage for grouped drops, and this
  tool doesn't attempt to compute real group odds.
- Gear granted by `ItemRandomProperties`/`ItemRandomSuffix` (`+of the
  Whale`-style suffixes) or `ScalingStatDistribution` (heirlooms) shows
  only the item's base stat rows - the random/scaling component isn't
  resolved.
