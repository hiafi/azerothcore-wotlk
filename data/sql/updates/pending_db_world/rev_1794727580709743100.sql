-- Item variants, Molten dungeon set (blackrock-gear WP-MOLTEN): the 16 Molten quartermasters (user ruling 2026-11-14),
-- four per armor type split by tier, each spawned in both Ironforge and Orgrimmar (32 spawns). The creature templates
-- 300670-300685 and their vendor lists come from dbc-tools (source/npcs/molten_set/vendors.py, source/items/
-- molten_set.py); this file only spawns them. Faction 35 (friendly to everyone), so one template serves both cities.
--
-- Spots picked from the worldserver's navmesh (map 0 tiles 0004133 / 0004134 / 0004033 / 0004233, map 1 tiles 0012840
-- / 0012841 / 0012842), not yet checked in game: each armor type's four vendors stand in a line along a straight wall,
-- 2-3 yd apart, 0.6-1.6 yd from the walkable edge, at least 7 yd (Orgrimmar) or 10 yd (Ironforge) of open floor in
-- front of them, facing away from the wall, at least 2.5 yd from every creature and gameobject spawn; z is the navmesh
-- detail height. Ironforge: The Commons south-west of the bank (about -4914 to -4970, -927 to -968, floor
-- 501.8-502.0), near the Steelfury weapon merchants and the Stormpike recruiter. Orgrimmar: the Valley of Honor plaza
-- (about 2050 to 2101, -4749 to -4798, floor 22.1-26.9), beside its armorsmiths and weapon vendors.
-- Guids: the hand-SQL block above 5300000; 5300741-5300772 are the next free after 5300740 (checked 2026-11-14 against
-- the live DB and every SQL file in the shared checkout and the worktrees). Literal values only (no @ variables).
DELETE FROM `creature` WHERE `id` BETWEEN 300670 AND 300685 AND `guid` BETWEEN 5300741 AND 5300772;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`, `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`, `CreateObject`, `Comment`) VALUES
(5300741, 300670, 0, 0, 0, 1, 1, 0, -4920.000, -931.000, 501.920, 5.3014, 300, 0, 12340, 1, 'Molten Cloth Quartermaster (Normal & Heroic) - Ironforge'),
(5300742, 300674, 0, 0, 0, 1, 1, 0, -4918.000, -929.000, 501.960, 5.1051, 300, 0, 12340, 1, 'Molten Cloth Quartermaster (Molten Empowered) - Ironforge'),
(5300743, 300675, 0, 0, 0, 1, 1, 0, -4916.000, -928.000, 501.960, 4.9087, 300, 0, 12340, 1, 'Molten Cloth Quartermaster (Draconic Empowered) - Ironforge'),
(5300744, 300676, 0, 0, 0, 1, 1, 0, -4914.000, -927.000, 501.960, 5.3014, 300, 0, 12340, 1, 'Molten Cloth Quartermaster (Chthonic Empowered) - Ironforge'),
(5300745, 300671, 0, 0, 0, 1, 1, 0, -4945.000, -952.000, 501.860, 5.3014, 300, 0, 12340, 1, 'Molten Leather Quartermaster (Normal & Heroic) - Ironforge'),
(5300746, 300677, 0, 0, 0, 1, 1, 0, -4944.000, -950.000, 501.880, 5.3014, 300, 0, 12340, 1, 'Molten Leather Quartermaster (Molten Empowered) - Ironforge'),
(5300747, 300678, 0, 0, 0, 1, 1, 0, -4942.000, -949.000, 501.850, 5.3014, 300, 0, 12340, 1, 'Molten Leather Quartermaster (Draconic Empowered) - Ironforge'),
(5300748, 300679, 0, 0, 0, 1, 1, 0, -4940.000, -947.000, 501.810, 5.1051, 300, 0, 12340, 1, 'Molten Leather Quartermaster (Chthonic Empowered) - Ironforge'),
(5300749, 300672, 0, 0, 0, 1, 1, 0, -4955.000, -962.000, 501.890, 5.3014, 300, 0, 12340, 1, 'Molten Mail Quartermaster (Normal & Heroic) - Ironforge'),
(5300750, 300680, 0, 0, 0, 1, 1, 0, -4957.000, -964.000, 501.900, 5.3014, 300, 0, 12340, 1, 'Molten Mail Quartermaster (Molten Empowered) - Ironforge'),
(5300751, 300681, 0, 0, 0, 1, 1, 0, -4958.000, -966.000, 501.860, 5.4978, 300, 0, 12340, 1, 'Molten Mail Quartermaster (Draconic Empowered) - Ironforge'),
(5300752, 300682, 0, 0, 0, 1, 1, 0, -4960.000, -968.000, 501.840, 5.4978, 300, 0, 12340, 1, 'Molten Mail Quartermaster (Chthonic Empowered) - Ironforge'),
(5300753, 300673, 0, 0, 0, 1, 1, 0, -4970.000, -960.000, 501.810, 2.1598, 300, 0, 12340, 1, 'Molten Plate Quartermaster (Normal & Heroic) - Ironforge'),
(5300754, 300683, 0, 0, 0, 1, 1, 0, -4969.000, -958.000, 501.880, 2.1598, 300, 0, 12340, 1, 'Molten Plate Quartermaster (Molten Empowered) - Ironforge'),
(5300755, 300684, 0, 0, 0, 1, 1, 0, -4967.000, -956.000, 501.990, 2.1598, 300, 0, 12340, 1, 'Molten Plate Quartermaster (Draconic Empowered) - Ironforge'),
(5300756, 300685, 0, 0, 0, 1, 1, 0, -4965.000, -954.000, 501.990, 2.1598, 300, 0, 12340, 1, 'Molten Plate Quartermaster (Chthonic Empowered) - Ironforge'),
(5300757, 300670, 1, 0, 0, 1, 1, 0, 2050.000, -4768.000, 26.620, 1.1781, 300, 0, 12340, 1, 'Molten Cloth Quartermaster (Normal & Heroic) - Orgrimmar'),
(5300758, 300674, 1, 0, 0, 1, 1, 0, 2052.000, -4769.000, 26.330, 0.7854, 300, 0, 12340, 1, 'Molten Cloth Quartermaster (Molten Empowered) - Orgrimmar'),
(5300759, 300675, 1, 0, 0, 1, 1, 0, 2054.000, -4770.000, 26.060, 0.7854, 300, 0, 12340, 1, 'Molten Cloth Quartermaster (Draconic Empowered) - Orgrimmar'),
(5300760, 300676, 1, 0, 0, 1, 1, 0, 2056.000, -4771.000, 25.870, 0.7854, 300, 0, 12340, 1, 'Molten Cloth Quartermaster (Chthonic Empowered) - Orgrimmar'),
(5300761, 300671, 1, 0, 0, 1, 1, 0, 2054.000, -4758.000, 26.510, 5.6941, 300, 0, 12340, 1, 'Molten Leather Quartermaster (Normal & Heroic) - Orgrimmar'),
(5300762, 300677, 1, 0, 0, 1, 1, 0, 2055.000, -4755.000, 26.640, 6.0868, 300, 0, 12340, 1, 'Molten Leather Quartermaster (Molten Empowered) - Orgrimmar'),
(5300763, 300678, 1, 0, 0, 1, 1, 0, 2055.000, -4752.000, 26.760, 5.8905, 300, 0, 12340, 1, 'Molten Leather Quartermaster (Draconic Empowered) - Orgrimmar'),
(5300764, 300679, 1, 0, 0, 1, 1, 0, 2055.000, -4749.000, 26.880, 5.8905, 300, 0, 12340, 1, 'Molten Leather Quartermaster (Chthonic Empowered) - Orgrimmar'),
(5300765, 300672, 1, 0, 0, 1, 1, 0, 2090.000, -4790.000, 22.380, 3.1416, 300, 0, 12340, 1, 'Molten Mail Quartermaster (Normal & Heroic) - Orgrimmar'),
(5300766, 300680, 1, 0, 0, 1, 1, 0, 2091.000, -4792.000, 22.130, 3.1416, 300, 0, 12340, 1, 'Molten Mail Quartermaster (Molten Empowered) - Orgrimmar'),
(5300767, 300681, 1, 0, 0, 1, 1, 0, 2091.000, -4795.000, 22.190, 3.3379, 300, 0, 12340, 1, 'Molten Mail Quartermaster (Draconic Empowered) - Orgrimmar'),
(5300768, 300682, 1, 0, 0, 1, 1, 0, 2091.000, -4798.000, 22.290, 3.1416, 300, 0, 12340, 1, 'Molten Mail Quartermaster (Chthonic Empowered) - Orgrimmar'),
(5300769, 300673, 1, 0, 0, 1, 1, 0, 2099.000, -4772.000, 22.750, 3.1416, 300, 0, 12340, 1, 'Molten Plate Quartermaster (Normal & Heroic) - Orgrimmar'),
(5300770, 300683, 1, 0, 0, 1, 1, 0, 2100.000, -4774.000, 22.550, 3.1416, 300, 0, 12340, 1, 'Molten Plate Quartermaster (Molten Empowered) - Orgrimmar'),
(5300771, 300684, 1, 0, 0, 1, 1, 0, 2100.000, -4777.000, 22.380, 3.3379, 300, 0, 12340, 1, 'Molten Plate Quartermaster (Draconic Empowered) - Orgrimmar'),
(5300772, 300685, 1, 0, 0, 1, 1, 0, 2101.000, -4779.000, 22.180, 3.1416, 300, 0, 12340, 1, 'Molten Plate Quartermaster (Chthonic Empowered) - Orgrimmar');
