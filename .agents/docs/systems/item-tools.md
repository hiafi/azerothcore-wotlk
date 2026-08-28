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
  file is a no-op instead of an error. See
  `data/sql/updates/pending_db_world/rev_1787824212353499531.sql` for a
  real example.
- **A brand-new row**: `INSERT INTO item_template (...) VALUES (...) ON
  DUPLICATE KEY UPDATE col = VALUES(col), ...` - an upsert, both idempotent
  and never needs a `DELETE`. See the `creature_template` precedent this
  was modeled on in
  `data/sql/updates/pending_db_world/rev_1787563173168071680.sql`.

`apps/item-tools/lib/emit.py` generates exactly these two shapes; you
shouldn't need to hand-write either if you're going through the webui.

## Dungeon/raid loot browser

`/dungeons` and `/dungeons/<map_id>` (`lib/loot.py`) join `creature` +
`creature_template` + `creature_loot_template`/`reference_loot_template`
against `item_template` to show what drops where, with a link into each
item's edit form. Those four non-item tables are read from their **base
dumps only** (no pending-SQL replay) - see the README's "Known
limitations" before assuming a change to creature loot shows up there
immediately.
