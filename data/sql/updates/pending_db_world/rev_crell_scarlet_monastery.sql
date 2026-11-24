-- Scarlet Monastery build WP-D9: Forgemaster Gideon Crell, the Armorer (300940), the rows dbc-tools cannot declare
-- (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D9, s7 #28 A, s7 #29 A; build
-- spec docs/dungeons/scarlet-monastery-3-armory.md "Forgemaster Gideon Crell, the Armorer"). His template (level 37
-- warrior, 54k, immunity 1972, INSTANCE_BIND, display 3278; boss_forgemaster_gideon_crell_rework once wave 2 binds),
-- the Scarlet Recruit 300941 and the spells 212900-212923 are apps/dbc-tools source/npcs/scarlet_monastery/crell.py.
-- He is a new creature, so there is no stock SmartAI to drop. The forge, the anvil and the quench trough are database
-- objects (scenery: the script never touches them; they stand before, during and after the fight). His own spawn and
-- the objects set the heroic bit themselves (spawnMask 3, handoff s3.5 rule 14: the generated heroic rev sorts before
-- rev_<boss>_*).

-- His texts (ARM "Text"; all new). The yells keep the default range; the boss emotes (type 41) are map-wide (TextRange
-- 3: an emote's own range is 25 yd and the storeroom is 70 yd long). Groups 3 (Temper) and 5 (the recruit) are heroic
-- only; heroic orders yell 1 then 2.
DELETE FROM `creature_text` WHERE `CreatureID` = 300940 AND `GroupID` BETWEEN 0 AND 7;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(300940, 0, 0, 'Out of uniform, are we? I''ll fit you myself!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Forgemaster Gideon Crell - aggro'),
(300940, 1, 0, 'A blade for the Crusade!', 14, 0, 100, 0, 0, 0, 0, 0, 'Forgemaster Gideon Crell - Blade order (AR1)'),
(300940, 2, 0, 'Plate for the faithful!', 14, 0, 100, 0, 0, 0, 0, 0, 'Forgemaster Gideon Crell - Plate order (AR1)'),
(300940, 3, 0, '%s begins to temper the piece!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Forgemaster Gideon Crell - Temper (AR5, heroic)'),
(300940, 4, 0, 'Let''s test the edge!', 14, 0, 100, 0, 0, 0, 0, 0, 'Forgemaster Gideon Crell - Proving Strike (AR7)'),
(300940, 5, 0, '%s hands the finished piece to a Scarlet Recruit.', 41, 0, 100, 0, 0, 0, 0, 3,
    'Forgemaster Gideon Crell - the Supply Line (AR6, heroic)'),
(300940, 6, 0, 'Next!', 14, 0, 100, 0, 0, 0, 0, 0, 'Forgemaster Gideon Crell - kill'),
(300940, 7, 0, 'Who... will keep... the stores...', 14, 0, 100, 0, 0, 0, 0, 0, 'Forgemaster Gideon Crell - death');

-- The encounter's objects (display ids: VR, _visuals.py GODI_FORGE / GODI_ANVIL / GODI_TROUGH; pinned by
-- lib/test_scarlet_monastery_crell.py). GENERIC (type 5: no lock, no key item, no click) and not selectable (addon
-- flags 16). 301325 the forge OM_Forge_01 (GODI 7044, 3.7 x 3.7 x 2.1 yd; NEVER 197, a brazier), 301326 the anvil
-- Tradeskill_Anvil_01 (273), 301327 the quench trough, a Cauldron stand-in (216: no trough model exists in the client).
-- Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301325, 5, 7044, 'Crusade Forge', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, '', '', 0),
(301326, 5, 273, 'Crusade Anvil', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, '', '', 0),
(301327, 5, 216, 'Quench Trough', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, '', '', 0)
ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`), `name` = VALUES(`name`),
    `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` BETWEEN 301325 AND 301327;
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301325, 0, 16, 0, 0, 0, 0, 0, 0),
(301326, 0, 16, 0, 0, 0, 0, 0, 0),
(301327, 0, 16, 0, 0, 0, 0, 0, 0);

-- The objects in the storeroom (CrellLogic.h kForge / kAnvil / kTrough; NAVMESH: the anvil spot (1776, -388) has
-- clearance 8.8 and its 8 yd circle is all floor, the trough (1776, -394) clearance 4.1 inside it, the forge 9 yd north
-- of the anvil, out of the circle, facing it). Normal and heroic (spawnMask 3). Guids = entry x 10 (the hand-SQL
-- convention of the Kell and Blackrock Depths revs), free on the live DB 2026-11-20. Literal values only.
DELETE FROM `gameobject` WHERE `id` BETWEEN 301325 AND 301327 AND `guid` IN (3013250, 3013260, 3013270);
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`,
    `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`,
    `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3013250, 301325, 189, 0, 0, 3, 1, 1785.0, -388.0, 8.0, 3.14159, 0, 0, 1, 0, 0, 100, 1, '', 0,
    'Scarlet Monastery D9: Crell''s forge'),
(3013260, 301326, 189, 0, 0, 3, 1, 1776.0, -388.0, 8.0, 0, 0, 0, 0, 1, 0, 100, 1, '', 0,
    'Scarlet Monastery D9: Crell''s anvil'),
(3013270, 301327, 189, 0, 0, 3, 1, 1776.0, -394.0, 8.0, 0, 0, 0, 0, 1, 0, 100, 1, '', 0,
    'Scarlet Monastery D9: Crell''s quench trough');

-- Forgemaster Gideon Crell's spawn, beside the anvil between it and the trough (NAVMESH's proposal (1776, -390, 8.0);
-- CrellLogic.h kCrellSpawn), normal and heroic (spawnMask 3), facing the stairs he is pulled from (south-west). Guid
-- 3009400 = entry x 10, free on the live DB 2026-11-20. A boss's 86400 s respawn. Literal values only.
DELETE FROM `creature` WHERE `id` = 300940 AND `guid` = 3009400;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(3009400, 300940, 189, 0, 0, 3, 1, 0, 1776.0, -390.5, 8.0, 2.46, 86400, 0, 0, 0,
    'Scarlet Monastery D9: Forgemaster Gideon Crell, the storeroom');
