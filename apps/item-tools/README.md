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
row an upsert `INSERT ... ON DUPLICATE KEY UPDATE` - see `item_lib/emit.py`'s
docstring for the exact shapes, both already established by hand elsewhere
in this repo's `pending_db_world` history before this tool existed.

## How "current state" is computed

No live database connection, no auth, no build step - same LAN-tool shape
as dbc-tools/webui. Every table item-tools reads (`item_template`, the
itemization tables, and the dungeon browser's `creature`/`creature_template`/
loot/instance tables) is replayed by `item_lib/replay.py` from:

1. `data/sql/base/db_world/<table>.sql` - the stock dump (none for the
   itemization tables, which migrations create);
2. every `data/sql/updates/db_world/**.sql` that names the table, including
   subdirectories such as `itemization_templates_v2/`, sorted by bare file
   name the way DBUpdater keys them, with mod-progression's frozen phase 0
   (`apps/dbc-tools/replay/frozen/`) spliced in where it ran;
3. every `data/sql/updates/pending_db_world/**.sql`, `data/sql/custom/db_world/**.sql`
   and module SQL file (`modules/*/data/sql/db-world/**`) that names it,
   all together by bare file name: DBUpdater's second pass, so a module file
   named `2016_...` runs before a pending `rev_...`.

The list is dbc-tools' `trainer_state.update_files()`, shared by both tools.

The parser is dbc-tools' (`apps/dbc-tools/lib/sql_dump.py`), shared rather
than copied (item-tools had its own narrower copy until item-tools-replay).
It applies statements in order with MySQL's semantics: an `UPDATE`'s guard
(`AND col = <old value>`, or a float column's `BETWEEN x-0.01 AND x+0.01` / older `ABS(col - x) < 0.01`) is
evaluated, so an UPDATE whose guard no longer holds changes nothing; `DELETE`
and `INSERT` interleave as written; an `INSERT ... ON DUPLICATE KEY UPDATE` on
an existing row changes only the clause's columns; session variables, expressions,
`INSERT IGNORE`, `TRUNCATE`, `ALTER TABLE` and `RENAME TABLE`
(`item_budget_assign` -> `item_itemization`) are read. What it reads and what
it still cannot: `.agents/docs/systems/dbc-tools.md`, "What the SQL replay
reads, the skip log, and the whole-table check".

**No skip is silent.** A statement the replay cannot apply is skipped, never
guessed at, and recorded in dbc-tools' skip log; each fresh load prints
`WARNING: replay: N SQL statement(s) could not be replayed ...` and one line
per table to stderr. Treat one on a table you are editing as a bug.

**Speed.** The replay of the immutable files (base dump, promoted, frozen) is
cached on disk per table under `var/item-tools-cache/` (dbc-tools' snapshot
cache, keyed by file content hashes and the parser's code), so only pending
and module SQL is replayed after the first load. Measured cold (first load,
or first after a parser change) / warm: `item_template` ~18 s / ~3 s, the
itemization tables ~11 s / ~6 s, the dungeon browser's tables ~2.5 min /
~20 s (`creature` alone is ~150k rows over ~700 files). Inside a dbc-tools
`generate.py` run the overlay uses generate's own corpus and cache.

**Checking it against live.** `replay_check.py` replays every table item-tools
reads over the files the live `updates` table lists and compares every row
and cell with the live world DB (read-only `SELECT`s; dbc-tools'
whole-table comparison). Explained differences live in
`replay/ALLOWED_TABLE_DIFFS` with a reason each; it exits 1 on anything else,
on a duplicate replayed key or on a stale entry:

```
apps/dbc-tools/.venv/bin/python3 apps/item-tools/replay_check.py \
    --mysql "docker exec -i <ac-database container> sh -c 'exec mysql -uroot -p\"\$MYSQL_ROOT_PASSWORD\" \"\$@\"' sh"
```

Add `--modules <main checkout>/modules` when running from a worktree that
lacks the live server's modules, and `--also rev_x.sql` to replay a pending
file not imported yet (e.g. one written to capture live state). Tests:
`apps/dbc-tools/.venv/bin/python3 -m unittest discover -s apps/item-tools/tests`.

## Setup

`webui/app.py` defines this as the `items` Flask Blueprint; in production
it's served alongside dbc-tools' webui by **apps/wow-tools-webui**
(`../wow-tools-webui/README.md`), at `/items/` on that combined app's port.
For quick dev/debugging it can still run standalone, unprefixed, on its own
port:

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

- **Shapes** (`/shapes`) - read-only browse of the shape-based itemization
  system's fixed catalog (`item_shape`/`item_shape_stat`/`item_shape_rule`/
  `item_alloc_dist`, see `docs/itemization-phase-2.md` &sect;3-&sect;6):
  every primary shape (role-lock stats - Str/Agi/Int/Spirit/SpellPower/AP)
  and secondary shape (universal stats - Crit/Haste/Mastery/Versatility/
  CDH/Proc/MP5/ArmorPen/Dodge/Parry/Block), its distribution, stat/percentage
  breakdown, and any eligibility rule. Not editable here - unlike the old
  percentage-allocation system's hand-authored templates, shapes are a fixed
  catalog edited by hand-written regression-backed migrations, same posture
  as the reference/curve tables below.
  - An item's edit page (`/items/<entry>`) gets an **Itemization** section
    right after its basic identity fields (name/type): which primary shape,
    secondary shape, and primary/secondary split (`primary_share`) it uses,
    plus `budget_mult`/`stamina_delta`/`dps_delta`/`armor_delta`/
    `block_value_delta` and a checkbox per on-equip spell to fold into the
    stat block (`absorbed_spell_slots`). The secondary-shape dropdown
    client-side filters to whatever the selected primary shape's rules
    actually allow (`webui/static/item-form.js`), same pattern as the
    class/subclass filter above it - the server re-validates the actual
    choice on save regardless. **Preview** computes and shows the resulting
    stat/stamina/armor/block/DPS line without writing anything; **Save &
    regenerate** writes the itemization row plus a guarded `item_template`
    UPDATE for the real computed stats - the same math
    `src/server/game/Globals/ItemBudget.cpp`'s `ResolveBudget()` runs at
    server startup, ported to Python in `item_lib/budget.py` (kept in sync with
    the C++ by hand - see that file's docstring) and cross-checked against
    an independent reference computation for every one of the 13,455 real
    assigned items with zero mismatches (materialization itself is in-memory
    only - `item_template` rows in the database are never overwritten by it -
    so this couldn't be a literal diff against a live DB dump; the live
    worldserver boot separately confirmed all 13,455 items materialize with
    zero validation errors against the same shape/delta data this tool reads).
  - The reference/curve tables themselves (`item_budget_curve`,
    `item_stat_cost`, `item_slot_mult`, ...) are read-only here - they're
    edited by hand-written regression-derived migrations, not through this
    tool.
- **Dungeons & raids** (`/dungeons`) - every map in `instance_template`
  (dungeon/raid names are derived from that table's own `script` column,
  e.g. `instance_icecrown_citadel` &rarr; "Icecrown Citadel" - not
  hand-typed, so it can't drift from what the DB actually has), each
  showing how many creatures on it drop an item at or above a quality
  filter. Click through to a map (`/dungeons/<id>`) for the drop list - name,
  quality badge, ilvl, stat summary, and a link straight into that item's
  edit form. A creature is classified as a boss - keeping its own block -
  if it's a real tracked encounter in `instance_encounters` (achievement/
  kill-credit data - not `rank`: a dungeon's own boss is rank Elite,
  identical to its trash, so rank alone can't tell them apart the way it
  can for a raid's rank-WORLDBOSS bosses, which count too as a second
  signal). Everything else is pooled into one "Trash Drops" list per
  unique item (with which creatures drop it), rather than one block per
  trash creature - a dungeon's trash list is usually large and
  overlapping, and per-creature blocks for it aren't "at a glance".
  `item_lib/loot.py` resolves `creature` (spawns)
  &rarr; `creature_template` (lootid) &rarr; `creature_loot_template` (+ one
  level of `Reference` expansion through `reference_loot_template`)
  &rarr; `item_template`, all replayed like `item_template` (base dump plus
  every migration, pending and module file), so a pending loot or spawn
  change shows up too. The first load replays ~150k spawns and both loot
  tables and is slow (see "Speed" above; seconds once the disk cache is
  warm); everything after that is served from an in-memory cache until a
  SQL file changes.
- **Browse** (`/items`) - search by entry ID or a name substring. The
  `subclass` column reads as "Type" and only shows a name (weapon type for
  class Weapon, armor type for class Armor) for those two classes - a
  subclass number doesn't mean "type" for anything else, so it's left
  blank there rather than shown as a number that isn't a type.
- **Edit** (`/items/<entry>`) - every friendly-grouped field from
  `item_lib/schema.py`'s sections, plus a required change note. Saving diffs
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

- `class`, `subclass`, `InventoryType`, and the 10 `stat_typeN` slots are
  dropdowns with real names (`item_lib/item_enums.py`, read from this repo's own
  `ItemTemplate.h` - including the stat types this fork has repurposed,
  22/23/24/33, labeled "(custom)"). Picking a class filters the subclass
  list client-side, but only in response to actually changing the class
  field - on page load an existing row's value is never touched, even if
  it's a (class, subclass) combination, stat type, or inventory type
  outside the known table (a handful of real rows are - shows as
  "(unrecognized)", stays selected, saves back unchanged unless you
  deliberately edit it). Every other raw integer column (`Quality`,
  `bonding`, ...) is still a plain numeric input, same posture as
  dbc-tools' spell form
  for the columns it doesn't model specially.
- `item_template_locale` (localized name/description) isn't read or
  written - only the base `item_template` row.
- The replay (`item_lib/replay.py`) cannot read subqueries, function calls
  other than the `ABS()` float guard, `INSERT ... SELECT` or an `UPDATE`
  with a join; such a statement is skipped with a warning (see "No skip is
  silent" above). None of this tool's own output writes those shapes.
- Rows that exist only live (written by a pending file that was deleted
  before commit, or by hand) cannot be replayed; `replay_check.py` lists
  them in `replay/ALLOWED_TABLE_DIFFS`.
- No concurrent-edit locking (single-user tool, same as dbc-tools/webui) -
  git is the safety net if two edits collide.
- Boss detection (`item_lib/loot._boss_creature_entries`) only knows what
  `instance_encounters` (achievement/kill-credit data) and
  `CREATURE_ELITE_WORLDBOSS` rank actually cover. A boss with no
  `instance_encounters` row, a `CAST_SPELL`-credited one (no creature
  entry to point at), or one summoned dynamically by a script rather than
  placed as a static `creature` spawn (ICC's Sindragosa and Valithria
  Dreamwalker, for example - `creatures_on_map()` never sees those rows
  either way) won't show up under "Bosses"; a handful of real encounters
  fall into one of these and are simply missing from the dungeon view
  entirely, not misclassified as trash.
- Loot-group entries (several items competing for one drop slot via
  `creature_loot_template.GroupId`) often show a raw 0% chance - that
  column isn't a plain per-item percentage for grouped drops, and this
  tool doesn't attempt to compute real group odds.
- Gear granted by `ItemRandomProperties`/`ItemRandomSuffix` (`+of the
  Whale`-style suffixes) or `ScalingStatDistribution` (heirlooms) shows
  only the item's base stat rows - the random/scaling component isn't
  resolved.
