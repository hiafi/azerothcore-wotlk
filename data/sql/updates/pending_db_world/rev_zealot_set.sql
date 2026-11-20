-- Item variants, the Zealot's dungeon set (scarlet-gear WP-ZEALOT): the four Zealot's quartermasters (user ruling
-- 2026-11-19), one per tier (Heroic, Molten, Draconic, Chthonic Empowered), side by side outside the Scarlet
-- Monastery's outer gate in Tirisfal Glades. The creature templates 300890-300893 and their vendor lists come from
-- dbc-tools (source/npcs/zealot_set/vendors.py, source/items/zealot_set.py); this file only spawns them. Faction 35
-- (friendly to both sides).
--
-- Spots picked from the worldserver's navmesh (map 0 tile 0002633), not yet checked in game: the open, flat ground
-- (at most 1 yd of height change within 4 yd, floor in every direction for 5 yd) on the approach between the Meeting
-- Stone (2655.9, -678.2) and the outer grounds, about 25 yd south-east of the static Scarlet Magician at (2779.8,
-- -684.1) and at least 10 yd past every creature and gameobject spawn and every wanderer's wander radius. A line from
-- south-west to north-east, 2.8 yd apart, facing north-west toward the approach; z is the navmesh detail height.
-- Guids: the hand-SQL block above 5300000; 5300773-5300776 are the next free after 5300772 (checked 2026-11-19
-- against the live DB and every SQL file in the shared checkout and the worktrees). Literal values only.
DELETE FROM `creature` WHERE `id` BETWEEN 300890 AND 300893 AND `guid` BETWEEN 5300773 AND 5300776;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`, `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`, `CreateObject`, `Comment`) VALUES
(5300773, 300890, 0, 0, 0, 1, 1, 0, 2782.000, -712.000, 129.130, 2.3562, 300, 0, 12340, 1, 'Zealot''s Quartermaster (Heroic) - Scarlet Monastery'),
(5300774, 300891, 0, 0, 0, 1, 1, 0, 2784.000, -710.000, 129.500, 2.3562, 300, 0, 12340, 1, 'Zealot''s Quartermaster (Molten Empowered) - Scarlet Monastery'),
(5300775, 300892, 0, 0, 0, 1, 1, 0, 2786.000, -708.000, 129.910, 2.3562, 300, 0, 12340, 1, 'Zealot''s Quartermaster (Draconic Empowered) - Scarlet Monastery'),
(5300776, 300893, 0, 0, 0, 1, 1, 0, 2788.000, -706.000, 130.350, 2.3562, 300, 0, 12340, 1, 'Zealot''s Quartermaster (Chthonic Empowered) - Scarlet Monastery');
