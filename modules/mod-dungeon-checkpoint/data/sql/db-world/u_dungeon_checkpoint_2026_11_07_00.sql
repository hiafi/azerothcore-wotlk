-- Deadmines boss checkpoints (user 2026-11-07): after Rhahk'Zor, Sneed, Gilnid and Mr. Smite. Each respawn spot is
-- the boss's own spawn point (Sneed: his Shredder's spawn, since Sneed is summoned out of it). The normal entries
-- cover heroic too (Creature::GetEntry() is the normal entry); all four carry kill credit in instance_encounters.
DELETE FROM `dungeon_checkpoint_location` WHERE `map_id` = 36 AND `creature_entry` IN (644, 643, 1763, 646);
INSERT INTO `dungeon_checkpoint_location` (`map_id`, `creature_entry`, `location_index`, `checkpoint_order`, `position_x`, `position_y`, `position_z`, `orientation`, `comment`) VALUES
(36, 644, 0, 1, -192.915, -448.211, 54.4339, 1.66886, 'Deadmines - after Rhahk''Zor'),
(36, 643, 0, 2, -289.453, -513.009, 49.6785, 3.78367, 'Deadmines - after Sneed'),
(36, 1763, 0, 3, -177.362, -574.458, 19.3113, 0.092073, 'Deadmines - after Gilnid'),
(36, 646, 0, 4, -22.8471, -797.283, 20.3745, 1.0472, 'Deadmines - after Mr. Smite');
