-- Scarlet Monastery build WP-D11H: Herod's hard mode, Call to Arms (heroic only), the rows dbc-tools cannot declare
-- (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.7, s3.5 row D11H, s7 #31 A; build spec
-- docs/dungeons/scarlet-monastery-3-armory.md "Hard mode: Call to Arms" and the Build spec's Text table). The Garrison
-- Trainee 300944, the planted Ravager 300945 and the spells 213020-213029 are apps/dbc-tools
-- source/npcs/scarlet_monastery/herod_hard_mode.py; the engine side is modules/mod-dungeon-bosses
-- src/ScarletMonastery/herod_hard_mode.cpp (the rack's spot pinned against HerodHardModeLogic.h by
-- lib/test_scarlet_monastery_herod_hard_mode.py).

-- His hard mode lines (ARM "Text": groups 0-4 are the stock rows, D11's telegraphs). Group 5 the /taunt answered on
-- heroic (yell), 6 the /taunt on normal or in combat (say; the script's 30 s cooldown), 7 his rising from the prayer
-- (yell), 8 the door bursting open for the garrison (a boss emote, type 41). Group 9 is D11's (normal and heroic,
-- carried here as Herod's one text rev): the seal's boss emote as Herod's Door shuts 3 s after the pull (section 7 #22
-- A, F-2c), said again at the hard mode's re-seal.
DELETE FROM `creature_text` WHERE `CreatureID` = 3975 AND `GroupID` BETWEEN 5 AND 9;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(3975, 5, 0, 'You mock the Champion of the Crusade? Then you will face all of it!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Herod - the /taunt answered on heroic: Call to Arms (D11H, HM0)'),
(3975, 6, 0, 'Words. Show me steel.', 12, 0, 100, 0, 0, 0, 0, 0,
    'Herod - a /taunt on normal or in combat (D11H, HM0)'),
(3975, 7, 0, 'The Crusade answers!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Herod - rising from the prayer (D11H, HM2)'),
(3975, 8, 0, 'Herod''s Door bursts open! The garrison marches to its champion!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Herod - the door bursts open for the garrison (D11H, HM2)'),
(3975, 9, 0, 'Herod''s Door slams shut! None leave until the Champion falls.', 41, 0, 100, 0, 0, 0, 0, 0,
    'Herod - the seal: his door shuts 3 s after the pull (D11, HB0)');

-- 301328 Herod's wall rack (GODI 130 GeneralWeaponrack01, V's GODI_RAVAGER_RACK): scenery the Crusader's blade comes
-- from at his rising. 301329 the planted Ravager's prop (GODI 8494, the stock stuck orc axe ORCAXE02, V's
-- GODI_PLANTED_RAVAGER, first pick; size 1.5 as the stock Stuck Axe 301250): summoned by the planted Ravager 300945 at
-- the pit's center for the second half, never spawned. GENERIC (type 5), not selectable (flags 16). Upserts:
-- gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301328, 5, 130, 'Herod''s Weapon Rack', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, '', '', 0),
(301329, 5, 8494, 'Ravager', '', '', '', 1.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, '', '', 0)
ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`), `name` = VALUES(`name`),
    `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` BETWEEN 301328 AND 301329;
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301328, 0, 16, 0, 0, 0, 0, 0, 0),
(301329, 0, 16, 0, 0, 0, 0, 0, 0);

-- The rack's spawn, heroic only (spawnMask 2: the hard mode is heroic only; rule 14), against the pit's east wall
-- (HerodHardModeLogic.h kRackSpot: the pit floor ends at y -445.5 there, navmesh/maps3.txt), facing the pit's center
-- (west: orientation pi / 2, rotation2 = sin(pi / 4), rotation3 = cos(pi / 4)); clear of the garrison's lanes (y -429.8
-- to -433.4), the Fine Chairs (97801-97803, 12 yd and more away) and the lap on the ledge. Guid 3013280 = the entry x
-- 10 (the hand-SQL convention of the Kell and Crell revs), free in the live DB (read-only check 2026-11-20).
DELETE FROM `gameobject` WHERE `id` = 301328 AND `guid` = 3013280;
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`,
    `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`,
    `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3013280, 301328, 189, 0, 0, 2, 1, 1961.9, -444.0, 6.3, 1.5708, 0, 0, 0.707107, 0.707107, 0, 100, 1, '', 0,
    'Scarlet Monastery D11H: Herod''s wall rack (Call to Arms, heroic only)');
