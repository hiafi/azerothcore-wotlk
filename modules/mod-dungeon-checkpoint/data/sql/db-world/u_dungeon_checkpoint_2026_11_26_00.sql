-- Gnomeregan: the section 2 start and two boss checkpoints (Gnomeregan build WP-S0, handoff section 7 #25 A, user
-- ruling 2026-11-26). Ghosts release to Dun Morogh (no graveyard inside) and the map has one entrance row (location
-- index 0, u_dungeon_checkpoint_2026_10_11_01.sql): the walks are 1,198 yd to Electrocutioner and 894 yd from Crowd
-- Pummeler to Thermaplugg [navmesh estimate].
--   1. The Train Depot landing (area trigger 523's target, Finder 320's start): an entrance-type row, "reached only"
--      (reach_radius 25): a Finder section 2 group is teleported onto it, so it counts as reached at once; a full
--      clear never walks there, so its deaths keep the entrance row (the nearer one wins among the reached).
--   2. Electrocutioner 6000 (6235, kill credit 380): once he is dead, deaths respawn at his walkway's mouth, 6 yd from
--      End NPC 1, facing the way on (bearing 75 from the platform's center); never in a live fight.
--   3. Crowd Pummeler 9-60 (6229, kill credit 381): once he is dead, deaths respawn on the pocket's free disc (radius
--      13), 4.8 yd from his chest.
-- Every spot is [navmesh estimate] (mesh z minus the 0.13 baseline; confirm with .gps at the playtest). The header's
-- kCheckpointDepot, kCheckpointDepotReachYd, kCheckpointElectrocutioner and kCheckpointPummeler
-- (modules/mod-dungeon-bosses src/Gnomeregan/GnomereganRework.h) name the same spots (pinned by
-- apps/dbc-tools lib/test_gnomeregan_npcs.py).
-- DRAFT: applied by hand at the deploy with its `updates` row (state MODULE, upper-case sha1); never edited after.
-- Re-runnable (DELETE + INSERT of these three rows).
DELETE FROM `dungeon_checkpoint_location` WHERE `map_id` = 90 AND `creature_entry` = 0 AND `location_index` = 1;
INSERT INTO `dungeon_checkpoint_location` (`map_id`, `creature_entry`, `location_index`, `checkpoint_order`,
    `position_x`, `position_y`, `position_z`, `orientation`, `reach_radius`, `comment`) VALUES
(90, 0, 1, 0, -736.51, 2.71, -249.99, 3.14, 25,
    'Gnomeregan - the Train Depot (areatrigger_teleport 523, Finder 320; reached only)');
DELETE FROM `dungeon_checkpoint_location` WHERE `map_id` = 90 AND `creature_entry` IN (6235, 6229);
INSERT INTO `dungeon_checkpoint_location` (`map_id`, `creature_entry`, `location_index`, `checkpoint_order`,
    `position_x`, `position_y`, `position_z`, `orientation`, `reach_radius`, `comment`) VALUES
(90, 6235, 0, 1, -543.8, 530.9, -216.6, 1.31, 0,
    'Gnomeregan - after Electrocutioner 6000 (the walkway''s mouth)'),
(90, 6229, 0, 2, -898.8, 359.8, -272.4, 3.14, 0,
    'Gnomeregan - after Crowd Pummeler 9-60 (the pocket)');
