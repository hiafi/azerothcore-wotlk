-- Blackrock Depths: three entrance checkpoints, one per new Dungeon Finder start (Blackrock Depths build WP-H, handoff
-- 3.8 and 7.1 #12). The map is one instance for all four sections, so the entrance row (location_index 0, the
-- dungeon entrance, areatrigger_teleport 1466, section 1) gets three more spots at checkpoint order 0: a player who
-- dies shares the instance's checkpoint order 0 and respawns at the nearest spot it may use (3D). The starts are the
-- lfg_dungeon_template rows of dbc-tools source/world/lfg_classic_sections.py (keep them equal):
--   index 1 S2a  Section 2 Shadowforge City (LFG 308 / heroic 311): the open table hall north of the Ring (595, -92)
--   index 2 S3   Section 3 Manufactory (LFG 309 / heroic 312): the Shadowforge Lock lever room (607.2, -47.8)
--   index 3 S4b  Section 4 Imperial Seat (LFG 276 / heroic 313): the lower Guzzler floor (843.8, -167.8)
-- u_dungeon_checkpoint_2026_11_17_01.sql then makes the three "reached only" (reach_radius 25): a start is a respawn
-- candidate only once a member of the instance has been near it, so a death in one section never respawns the group
-- at another section's start. Re-runnable (DELETE + INSERT).
DELETE FROM `dungeon_checkpoint_location`
    WHERE `map_id` = 230 AND `creature_entry` = 0 AND `location_index` IN (1, 2, 3);
INSERT INTO `dungeon_checkpoint_location` (`map_id`, `creature_entry`, `location_index`, `checkpoint_order`,
    `position_x`, `position_y`, `position_z`, `orientation`, `comment`) VALUES
(230, 0, 1, 0, 595, -92, -45, 1.89,
    'Blackrock Depths - Section 2 Finder start S2a (lfg_dungeon_template 308)'),
(230, 0, 2, 0, 607.2, -47.8, -59.8, 6.05,
    'Blackrock Depths - Section 3 Finder start, Shadowforge Lock lever room (lfg_dungeon_template 309)'),
(230, 0, 3, 0, 843.8, -167.8, -49.7, 4.64,
    'Blackrock Depths - Section 4 Finder start S4b, lower Guzzler floor (lfg_dungeon_template 276)');
