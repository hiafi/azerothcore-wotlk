-- Scarlet Monastery build WP-D12: Brother Aldous Thorne, the Gardener (300946), the rows dbc-tools cannot declare
-- (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D12, s7 #32 A; build spec
-- docs/dungeons/scarlet-monastery-4-cathedral.md "Brother Aldous Thorne, the Gardener"). His template (level 40
-- paladin, 60k, immunity 1972, INSTANCE_BIND, display 2502; boss_gardener_rework once wave 2 binds), the Seedling
-- 300947, the Briar 300948, the Blessed Bramble 300949 and the spells 213060-213077 are apps/dbc-tools
-- source/npcs/scarlet_monastery/thorne.py. He is a new creature, so there is no stock SmartAI to drop. His spawn sets
-- the heroic bit itself (spawnMask 3, handoff s3.5 rule 14: the generated heroic rev sorts before rev_<boss>_*).

-- His texts (CATH "Text"; all new). The yells and the say keep the default range; the boss emotes (type 41) are
-- map-wide (TextRange 3: an emote's own range is 25 yd and the lower garden is 80 yd across). Group 2 (Bless the
-- Harvest) is heroic only; group 4 is the first bloom of a cycle.
DELETE FROM `creature_text` WHERE `CreatureID` = 300946 AND `GroupID` BETWEEN 0 AND 6;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(300946, 0, 0, 'Weeds in the Light''s garden. I know what to do with weeds.', 14, 0, 100, 0, 0, 0, 0, 0,
    'Brother Aldous Thorne - aggro'),
(300946, 1, 0, 'The furrow is ready. Sow!', 12, 0, 100, 0, 0, 0, 0, 0, 'Brother Aldous Thorne - Sow (GD1)'),
(300946, 2, 0, 'The Light blesses this harvest!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Brother Aldous Thorne - Bless the Harvest (GD3, heroic)'),
(300946, 3, 0, '%s raises the aspergillum!', 41, 0, 100, 0, 0, 0, 0, 3, 'Brother Aldous Thorne - Holy Water (GD2)'),
(300946, 4, 0, 'The untended seed blooms into thorns!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Brother Aldous Thorne - the first bloom of a cycle (GD1c)'),
(300946, 5, 0, 'Pulled up by the root.', 14, 0, 100, 0, 0, 0, 0, 0, 'Brother Aldous Thorne - kill'),
(300946, 6, 0, 'Nothing grows... from tainted soil...', 14, 0, 100, 0, 0, 0, 0, 0, 'Brother Aldous Thorne - death');

-- His scythe: Soul Harvester (item 20536, item display 33087 `Stave_2H_Scythe_C_03`: V's pick, s7 #34; NEVER the doc's
-- 13163 / 5749, a greatsword and a war axe). The spawn's equipment_id 1.
DELETE FROM `creature_equip_template` WHERE `CreatureID` = 300946;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
(300946, 1, 20536, 0, 0, 0);

-- Brother Aldous Thorne's spawn in the lower garden, off the pond (s7 #32 A: (908.2, 1399.2, 19.0), clearance 14.9 yd;
-- the doc's (932, 1400) is in the water; ThorneLogic.h kThorneSpawn), normal and heroic (spawnMask 3), facing west
-- (the doc's facing, along the dry floor's long axis). Guid 3009460 = entry x 10 (the hand-SQL convention of the Kell,
-- Crell and Blackrock Depths revs), free on the live DB 2026-11-20. A boss's 86400 s respawn. Literal values only.
DELETE FROM `creature` WHERE `id` = 300946 AND `guid` = 3009460;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(3009460, 300946, 189, 0, 0, 3, 1, 1, 908.2, 1399.2, 19.0, 1.5708, 86400, 0, 0, 0,
    'Scarlet Monastery D12: Brother Aldous Thorne, the lower garden');

-- The stock Scarlet Centurion that stood on his spot (guid 39953 at (909.231, 1399.03, 18.1066), random movement 5 yd)
-- moves to the garden's west edge (s7 #32 A: "moved to the garden's edge"), 39 yd from him, on the dry edge band (z
-- 18.76 like the corner spawns at y 1437) between the Sorcerer at (894.8, 1437.7) and the Centurion at (931.6, 1437.6).
-- Same guid, same entry, same spawnMask and wander distance (WP-H's generated heroic rev widens the mask); no
-- formation, pool, addon, linked respawn or game event holds it (read-only SELECTs 2026-11-20). ThorneLogic.h
-- kMovedCenturionSpot.
UPDATE `creature` SET `position_x` = 908.5, `position_y` = 1438.0, `position_z` = 18.76
    WHERE `guid` = 39953 AND `id` = 4301;
