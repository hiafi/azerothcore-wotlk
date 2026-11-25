-- Ragefire Chasm: one "reached only" checkpoint spot on the return route, before the lava lake (Ragefire Chasm build
-- WP-S0, handoff section 7 #14 A, user ruling 2026-11-24). The map has one entrance row (location_index 0,
-- u_dungeon_checkpoint_2026_10_11_01.sql): from it Taragaman is a 770 yd walk, Jergosh 944, Bazzalan 1,091. The new
-- row is a respawn candidate (checkpoint order 0, like the entrance row) only once a living member of the instance has
-- come within 10 yd (3D) of it (the reach_radius column of u_dungeon_checkpoint_2026_11_17_01.sql; the module looks
-- once a second, so 5 yd could be run past; nothing else of the dungeon is inside 10: the den's floor is 17 yd below,
-- the ledges 46 yd off). It is [navmesh estimate] (handoff 3.8; confirm with .gps at the playtest): 621 yd in, on the
-- walked line itself, 47 yd before the lake's foot, off every patrol, free radius 5.0; the two Molten Elementals 48683
-- (13 yd) and 48681 (22 yd, both wander 5) are dead by the time the spot is reached. It faces on along the route.
-- The spiral puts it 17 yd above the den's floor and 36 yd from Oggleflint, so a den wipe of a group that already went
-- up respawns here (a 504 yd walk back) and not at the entrance (441 yd); a group on the ruled order has not been here
-- yet and keeps the entrance. No boss row: one would raise the order and drop the entrance row, and the first three
-- bosses die in any order.
-- Re-runnable (DELETE + INSERT of this one index).
DELETE FROM `dungeon_checkpoint_location` WHERE `map_id` = 389 AND `creature_entry` = 0 AND `location_index` = 1;
INSERT INTO `dungeon_checkpoint_location` (`map_id`, `creature_entry`, `location_index`, `checkpoint_order`,
    `position_x`, `position_y`, `position_z`, `orientation`, `reach_radius`, `comment`) VALUES
(389, 0, 1, 0, -154.8, 70.2, -21.1, 2.68, 10,
    'Ragefire Chasm - the return route before the lava lake, reached only (before Taragaman)');
