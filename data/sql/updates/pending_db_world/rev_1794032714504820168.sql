-- Item variants, Haunted dungeon set: the 16 Haunted quartermasters (user rulings 2026-11-06), four per armor type
-- split by tier, in Darnassus for the Alliance. The creature templates 300480-300495 and their vendor lists come from
-- dbc-tools (source/npcs/haunted_set/vendors.py, source/items/haunted_set.py); this file only spawns them. A Horde spot
-- later is a new spawn of the same entries (faction 35, friendly to everyone).
--
-- The "Normal & Heroic" vendor of each armor type stands on the spot the user picked in game (map 1, phase 1,
-- spawnMask 1). Its three empowered vendors (Molten, Draconic, Chthonic) stand in a tight cluster beside it: 2-3 yd
-- from a neighbour, at least 2 yd from every one, out of the cone in front of the first vendor, on the same floor
-- (the navmesh detail height within 1 yd of the spot's, at least 0.5 yd inside the walkable edge), same orientation.
-- Mail and plate stand about 3 yd apart on two floors (7.6 yd apart in height); each cluster keeps its own floor.
-- Guids: the hand-SQL block above 5300000; 5300723-5300738 are the next free after the Death Knight trainers
-- (5300709-5300722), checked 2026-11-06 against the live DB and every pending SQL file in the shared checkout and the
-- worktrees. Literal values only (no @ variables).
DELETE FROM `creature` WHERE `id` BETWEEN 300480 AND 300495 AND `guid` BETWEEN 5300723 AND 5300738;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`, `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`, `CreateObject`, `Comment`) VALUES
(5300723, 300480, 1, 0, 0, 1, 1, 0, 9726.023, 2304.719, 1333.001, 5.7152934, 300, 0, 12340, 1, 'Haunted Cloth Quartermaster (Normal & Heroic) - Darnassus'),
(5300724, 300484, 1, 0, 0, 1, 1, 0, 9727.555, 2306.005, 1333.47, 5.7152934, 300, 0, 12340, 1, 'Haunted Cloth Quartermaster (Molten Empowered) - Darnassus'),
(5300725, 300485, 1, 0, 0, 1, 1, 0, 9724.491, 2303.433, 1333.07, 5.7152934, 300, 0, 12340, 1, 'Haunted Cloth Quartermaster (Draconic Empowered) - Darnassus'),
(5300726, 300486, 1, 0, 0, 1, 1, 0, 9726.023, 2302.119, 1333.07, 5.7152934, 300, 0, 12340, 1, 'Haunted Cloth Quartermaster (Chthonic Empowered) - Darnassus'),
(5300727, 300481, 1, 0, 0, 1, 1, 0, 9669.639, 2384.201, 1337.57, 4.588205, 300, 0, 12340, 1, 'Haunted Leather Quartermaster (Normal & Heroic) - Darnassus'),
(5300728, 300487, 1, 0, 0, 1, 1, 0, 9671.639, 2384.201, 1338.27, 4.588205, 300, 0, 12340, 1, 'Haunted Leather Quartermaster (Molten Empowered) - Darnassus'),
(5300729, 300488, 1, 0, 0, 1, 1, 0, 9667.669, 2384.548, 1337.87, 4.588205, 300, 0, 12340, 1, 'Haunted Leather Quartermaster (Draconic Empowered) - Darnassus'),
(5300730, 300489, 1, 0, 0, 1, 1, 0, 9666.868, 2382.601, 1337.87, 4.588205, 300, 0, 12340, 1, 'Haunted Leather Quartermaster (Chthonic Empowered) - Darnassus'),
(5300731, 300482, 1, 0, 0, 1, 1, 0, 9701.438, 2332.862, 1331.971, 2.2791462, 300, 0, 12340, 1, 'Haunted Mail Quartermaster (Normal & Heroic) - Darnassus'),
(5300732, 300490, 1, 0, 0, 1, 1, 0, 9702.724, 2334.394, 1332.21, 2.2791462, 300, 0, 12340, 1, 'Haunted Mail Quartermaster (Molten Empowered) - Darnassus'),
(5300733, 300491, 1, 0, 0, 1, 1, 0, 9699.468, 2332.514, 1332.06, 2.2791462, 300, 0, 12340, 1, 'Haunted Mail Quartermaster (Draconic Empowered) - Darnassus'),
(5300734, 300492, 1, 0, 0, 1, 1, 0, 9702.063, 2336.407, 1332.0, 2.2791462, 300, 0, 12340, 1, 'Haunted Mail Quartermaster (Chthonic Empowered) - Darnassus'),
(5300735, 300483, 1, 0, 0, 1, 1, 0, 9698.469, 2331.952, 1339.636, 2.0906394, 300, 0, 12340, 1, 'Haunted Plate Quartermaster (Normal & Heroic) - Darnassus'),
(5300736, 300493, 1, 0, 0, 1, 1, 0, 9699.755, 2333.484, 1339.73, 2.0906394, 300, 0, 12340, 1, 'Haunted Plate Quartermaster (Molten Empowered) - Darnassus'),
(5300737, 300494, 1, 0, 0, 1, 1, 0, 9696.499, 2332.299, 1339.73, 2.0906394, 300, 0, 12340, 1, 'Haunted Plate Quartermaster (Draconic Empowered) - Darnassus'),
(5300738, 300495, 1, 0, 0, 1, 1, 0, 9695.698, 2330.352, 1339.8, 2.0906394, 300, 0, 12340, 1, 'Haunted Plate Quartermaster (Chthonic Empowered) - Darnassus');
