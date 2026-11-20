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

### "Reached only" spots

An entrance-type row (`creature_entry = 0`) can be made opt-in with `dungeon_checkpoint_location.reach_radius`
(yards, default 0 = no effect). A row with `reach_radius > 0` is only a respawn candidate once a living member of the
instance has been within that distance (3D) of it; until then the nearest-spot pick skips it. The check runs from the
map update hook, once a second, and only on maps that have such a row; the reached set is per instance and persists in
`dungeon_checkpoint_reached` (characters DB), pruned and reset with the instance. Used by Blackrock Depths, whose three
Dungeon Finder section starts would otherwise catch a wipe in a different section: a Finder group is teleported onto its
start, so it counts as reached at once. Keep the dungeon's main entrance row at 0 so a candidate always exists.
Upper Blackrock Spire's Finder start (map 229, `location_index` 1) is reached-only too (25 yd, user 2026-11-17): a
Lower Spire wipe no longer respawns the group there. Caveat: Lower and Upper Spire share one instance, so a Lower Spire
group that walks past the Upper Spire start marks it reached, and later Lower Spire deaths near it may respawn there.

Threads: the reached check runs from `AllMapScript::OnMapUpdate` and reads the manager's per-instance maps without a
lock. That is safe only with `MapUpdate.Threads = 1` (the live setting); with more map threads, guard the manager's
maps (a `std::shared_mutex`) first.

Deploy: the worldserver does not run database updates in this Docker setup. The image sets
`AC_UPDATES_ENABLE_DATABASES=0` (`apps/docker/Dockerfile`), which overrides `Updates.EnableDatabases` in
`worldserver.conf`, and the `ac-db-import` image only sees the `modules/` tree it was built with (the override mounts
`./data` alone). So module SQL is applied by hand, before the new worldserver boots: pipe each file through the mysql
CLI (`DELIMITER` in world `_01` is a client command, so never paste it through another runner), in this order, world
`_00`, world `_01`, characters `_01`:

    cd modules/mod-dungeon-checkpoint/data/sql
    docker exec -i ac-database mysql -uroot -p<pw> acore_world < db-world/u_dungeon_checkpoint_2026_11_17_00.sql
    docker exec -i ac-database mysql -uroot -p<pw> acore_world < db-world/u_dungeon_checkpoint_2026_11_17_01.sql
    docker exec -i ac-database mysql -uroot -p<pw> acore_characters \
        < db-characters/u_dungeon_checkpoint_2026_11_17_01.sql

then record each in that database's `updates` table: `name` = the file name, `hash` = the file's exact `sha1sum` in
upper case, `state` = `MODULE` (like the `_2026_11_07_00` and `_2026_11_15_00` rows). The rows matter: a later
db-import image that bakes this tree must not replay `_00` alone (DELETE + INSERT without the column resets
`reach_radius` to 0). The files are safe to run twice (a column added only when missing, `CREATE TABLE IF NOT
EXISTS`). Without the column the boot aborts: the loader selects `reach_radius`, MySQL answers `ER_BAD_FIELD_ERROR`
(and `ER_NO_SUCH_TABLE` without `dungeon_checkpoint_reached`), which the core treats as an outdated schema and
`ABORT()`s, so the worldserver crash-loops. The alternative is rebuilding the `ac-db-import` image so it bakes the new
`modules/` tree, then running it.
