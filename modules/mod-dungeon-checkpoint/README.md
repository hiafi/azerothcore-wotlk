# mod-dungeon-checkpoint

Dungeon checkpoint respawn: dying in a 5-man dungeon after a checkpoint has been reached
resurrects you in place at that checkpoint instead of sending you through the normal
graveyard release / ghost-walk / corpse-run flow.

- At the start of a (configured) dungeon, the checkpoint is the entrance.
- Killing a boss that has a checkpoint configured advances it. Trash deaths are unaffected.
- Dungeons with no rows in `dungeon_checkpoint_location` are completely unaffected - the
  feature is opt-in per dungeon.
- Checkpoint progress is tied to the instance save, and survives a worldserver restart.

## Configuration

See `conf/mod_dungeon_checkpoint.conf.dist` (`DungeonCheckpoint.Enable`).

## Adding checkpoints for a dungeon

Insert rows into `dungeon_checkpoint_location` (world DB): `map_id` + `creature_entry` (the
boss's **normal** `creature_template.entry` - `Creature::GetEntry()` never returns the heroic
`difficulty_entry_*` one, so heroics are covered by the same row) + `checkpoint_order` (higher
wins when multiple bosses are dead) + the resurrect position. Only creatures that carry kill
credit in `instance_encounters` count as bosses. `creature_entry = 0` is the special "entrance"
checkpoint, active as soon as a player first enters a fresh instance - no boss kill required.
See `data/sql/db-world/b_dungeon_checkpoint_location.sql` for a worked example (Utgarde Keep).

Rows that share a `map_id` + `checkpoint_order` are alternative spots for one checkpoint
(distinguished by `location_index`); a player respawns at the one nearest where they died.
That is how split dungeons work: Scarlet Monastery has one entrance row per wing, so a death
in the Cathedral respawns you at the Cathedral entrance, not the Graveyard's.

`data/sql/db-world/u_dungeon_checkpoint_2026_10_11_01.sql` gives every other dungeon and raid
an entrance checkpoint at its `areatrigger_teleport` target (one per wing entrance for Scarlet
Monastery, Stratholme and Dire Maul). Not covered, so it keeps the normal graveyard flow: the
Eye of Eternity (its platform is destroyed in phase 3).
