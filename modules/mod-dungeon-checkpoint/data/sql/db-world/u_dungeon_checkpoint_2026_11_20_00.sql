-- Scarlet Monastery: one "reached only" checkpoint spot per wing, short of the wing's end boss (Scarlet Monastery build
-- WP-H, handoff 7 #23 B, user ruling 2026-11-20). The map is one instance for all four wings and the four entrance rows
-- (location_index 0-3, u_dungeon_checkpoint_2026_10_11_01.sql) are the Dungeon Finder starts, so a wipe at an end boss
-- is a 66-88 s run-back. Each new row is a respawn candidate (checkpoint order 0, like the entrance rows) only once a
-- living member of the instance has come within 15 yd (3D) of it (the reach_radius column of
-- u_dungeon_checkpoint_2026_11_17_01.sql), so the nearest-spot rule never pulls a wipe forward to a wing's far end
-- before someone has been there. The wings are 600+ yd apart, so no spot is ever nearer to another wing's death.
-- Every spot is a [navmesh estimate] (handoff 3.8; confirm with .gps at the playtest) and is at least 35 yd from every
-- boss fight spot of its wing:
--   index 4  Graveyard: the crypt ramp top on the lawn (1797, 1384, 19), facing Thalnos's crypt (40 yd from him, 35 yd
--            from the council's lawn (1798.5, 1348.5), 98 yd from Ironspine's home on the lawn); nearest spawn 21 yd
--   index 5  Library: the Athenaeum outer hall's east end, short of Doan's doorway (204, -430, 19.3; z between the
--            hall's spawn rows at 18.94 and the east passage at 19.9), facing the doorway; 22 yd from the nearest
--            outer hall spawn (Monks and Diviners at x 174-185), 56 yd from Doan
--   index 6  Armory: the cross hall before Herod's Door (1898, -431, 18.76, the hall's spawn rows), facing the door
--            (36 yd away); 19 yd from the nearest spawn, Halden's chamber is 38 yd off, Herod's pit 67 yd
--   index 7  Cathedral: the landing before the Chapel Door (1058, 1399, 30.85, the door guards' floor), facing it
--            (12 yd away), between the garden's Defender (15 yd) and the four door Centurions (13-19 yd); the Last
--            Stand's crossing restart re-arms the stand when a wiped group walks back in
-- Re-runnable (DELETE + INSERT of these four indexes).
DELETE FROM `dungeon_checkpoint_location`
    WHERE `map_id` = 189 AND `creature_entry` = 0 AND `location_index` IN (4, 5, 6, 7);
INSERT INTO `dungeon_checkpoint_location` (`map_id`, `creature_entry`, `location_index`, `checkpoint_order`,
    `position_x`, `position_y`, `position_z`, `orientation`, `reach_radius`, `comment`) VALUES
(189, 0, 4, 0, 1797, 1384, 19, 0.95, 15,
    'Scarlet Monastery - Graveyard end: the crypt ramp top, reached only (before Thalnos)'),
(189, 0, 5, 0, 204, -430, 19.3, 3.12, 15,
    'Scarlet Monastery - Library end: the Athenaeum outer hall, reached only (before Doan)'),
(189, 0, 6, 0, 1898, -431, 18.76, 6.26, 15,
    'Scarlet Monastery - Armory end: the cross hall before Herod''s Door, reached only (before Herod)'),
(189, 0, 7, 0, 1058, 1399, 30.85, 0.01, 15,
    'Scarlet Monastery - Cathedral end: the landing before the Chapel Door, reached only (before the Last Stand)');
