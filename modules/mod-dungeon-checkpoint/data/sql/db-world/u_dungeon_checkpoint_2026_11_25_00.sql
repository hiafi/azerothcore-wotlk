-- Zul'Farrak: one boss checkpoint, after Witch Doctor Zum'rah (Zul'Farrak build WP-S0, handoff section 7 #26 A, user
-- ruling 2026-11-25). The map has one entrance row (location_index 0, u_dungeon_checkpoint_2026_10_11_01.sql): from it
-- the Pyramid, the crew, Ukorz and the pool are 985 to 1,170 yd away (811 for the pool). Once Zum'rah (7271, kill
-- credit 597 in instance_encounters; the normal entry covers heroic) is dead, a death respawns at the edge of his bowl,
-- about 250 to 410 yd from each of them. A boss row, not a "reached only" spot: the order is fixed (ruling 5), it keeps
-- the dead out of a live fight, and it drops the entrance row once he is dead (deaths before him still run from the
-- entrance, up to 880 yd). The spot is [navmesh estimate] (handoff 3.8, NAVMESH-REPORT "after Zum'rah"; confirm with
-- .gps at the playtest): (1874.8, 1042.2) on the bowl's floor (mesh z 9.52), free radius 7.2, 43.3 yd from the
-- nearest spawn and 16.4 yd from the nearest patrol line, 37 yd from Zum'rah's tongue, facing the stair foot
-- (orientation 1.50).
-- The header's kCheckpoint (ZulFarrakRework.h) names the same spot (pinned by lib/test_zul_farrak_npcs.py).
-- DRAFT: applied by hand at the deploy with its `updates` row (state MODULE, upper-case sha1); never edited after.
-- Re-runnable (DELETE + INSERT of this one row).
DELETE FROM `dungeon_checkpoint_location` WHERE `map_id` = 209 AND `creature_entry` = 7271 AND `location_index` = 0;
INSERT INTO `dungeon_checkpoint_location` (`map_id`, `creature_entry`, `location_index`, `checkpoint_order`,
    `position_x`, `position_y`, `position_z`, `orientation`, `reach_radius`, `comment`) VALUES
(209, 7271, 0, 1, 1874.8, 1042.2, 9.5, 1.50, 0,
    'Zul''Farrak - after Witch Doctor Zum''rah (the bowl''s edge, facing the stair)');
