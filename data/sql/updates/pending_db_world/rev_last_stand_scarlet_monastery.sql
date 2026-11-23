-- Scarlet Monastery build WP-D13: the Last Stand, Scarlet Commander Mograine (3976), the rows dbc-tools cannot declare
-- (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D13, s7 #19 A, #20 A; build spec
-- docs/dungeons/scarlet-monastery-4-cathedral.md "The Last Stand"). His template (boss_mograine_rework behind
-- BIND_WAVE_2, 55k, immunity 1972, no INSTANCE_BIND), the companies 300950-300955 and spells 213100-213121 are
-- apps/dbc-tools source/npcs/scarlet_monastery/last_stand.py; his SmartAI rows 0-28 and the lists 397600-397602 go
-- with W2-SETUP's rev. This rev inserts no spawn and no SmartAI row (rule 14: nothing for the heroic spawn mask to
-- miss): the companies and the chest are summoned by the script.

-- Section 7 #19 A: every stock spawn in the nave and crossing box (x 1073-1172, z 29.5 and up) goes; the companies
-- replace them. Read-only SELECT 2026-11-20: 44 spawns in the box, of which Mograine (guid 40029) and Fairbanks (guid
-- 40039, the Torch's hard mode trigger) stay: 42 go (Chaplains 4299 x5, Wizards 4300 x6, Centurions 4301 x8,
-- Champions 4302 x9, Abbots 4303 x5, Monks 4540 x9). The landing and the gardens keep theirs (the four door Centurions
-- at x 1063-1065 included). No formation, pool, linked respawn or game event row names them.
DELETE FROM `creature` WHERE `id` IN (4299, 4300, 4301, 4302, 4303, 4540) AND `guid` IN (
    40000, 40001, 40003, 40004, 40005, 40006, 40007, 40008, 40009, 40010, 40011, 40012, 40013, 40014,
    40015, 40016, 40017, 40018, 40019, 40020, 40021, 40022, 40023, 40024, 40025, 40026, 40027, 40028,
    40030, 40031, 40032, 40033, 40034, 40035, 40036, 40037, 40038, 40040, 40041, 40042, 40043, 40044
);
DELETE FROM `creature_addon` WHERE `guid` IN (
    40000, 40001, 40003, 40004, 40005, 40006, 40007, 40008, 40009, 40010, 40011, 40012, 40013, 40014,
    40015, 40016, 40017, 40018, 40019, 40020, 40021, 40022, 40023, 40024, 40025, 40026, 40027, 40028,
    40030, 40031, 40032, 40033, 40034, 40035, 40036, 40037, 40038, 40040, 40041, 40042, 40043, 40044
);

-- Their patrols: four of the nine Cathedral guid path scripts (FACTS-STOCK s3.3) belong to nave spawns (the other five,
-- guids 39959, 39967, 39978, 39980 and 39998, walk the gardens and the landing's stairs and stay): the guid SmartAI
-- rows "start path" (source 0, one row each), their SmartAI waypoint paths, and the two creature_addon paths of guids
-- 40015 and 40034 (waypoint_data).
DELETE FROM `smart_scripts` WHERE `source_type` = 0 AND `entryorguid` IN (-40008, -40015, -40019, -40034);
DELETE FROM `waypoints` WHERE `entry` IN (4000800, 4001500, 4001900, 4003400);
DELETE FROM `waypoint_data` WHERE `id` IN (400150, 400340);

-- His texts (CATH "Text"): groups 0-6 are stock (0 the descent's yell, 1 the kill, 2 D14's rising, 3-6 the Ashbringer
-- event; 4-5 also D14H's); 7-11 are new yells; 12-13 are D14's.
DELETE FROM `creature_text` WHERE `CreatureID` = 3976 AND `GroupID` BETWEEN 7 AND 11;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(3976, 7, 0, 'The heretics are at the door! Brothers, sisters, the Crusade stands here!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Scarlet Commander Mograine - The Chapel Door opens (LS0)'),
(3976, 8, 0, 'Chapel Guard, hold them!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Scarlet Commander Mograine - Company 1, the Chapel Guard (LS1)'),
(3976, 9, 0, 'Brethren of the Pyre, burn them out!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Scarlet Commander Mograine - Company 2, the Pyre Brethren (LS1)'),
(3976, 10, 0, 'Clergy, to the line! The Light is with us!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Scarlet Commander Mograine - Company 3, the Clergy (LS1)'),
(3976, 11, 0, 'To me! The Crusade stands here!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Scarlet Commander Mograine - The Last Reserve at 50% (LS7, heroic)');

-- Section 7 #20 A: the Last Stand's chest, normal 301330 and heroic 301331 (CHEST, lock 57, consumable, group loot:
-- the BRD Chest of The Seven 169243's values; its display 1387). The script summons the entry of the difficulty at the
-- altar steps (1158.0, 1391.0, 32.35) when Mograine falls, for a day or until looted; no spawn row (the heroic rollout
-- widens every spawn of map 189 to both difficulties). Data1 is the loot entry, the GO's own id.
-- Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301330, 3, 1387, 'Chest of the Last Stand', '', '', '', 1, 57, 301330, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0,
    0, 0, 0, 0, 0, 0, '', '', 0),
(301331, 3, 1387, 'Chest of the Last Stand', '', '', '', 1, 57, 301331, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0,
    0, 0, 0, 0, 0, 0, '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`),
    `name` = VALUES(`name`), `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `Data1` = VALUES(`Data1`),
    `Data3` = VALUES(`Data3`), `Data11` = VALUES(`Data11`), `Data15` = VALUES(`Data15`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` IN (301330, 301331);
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301330, 0, 0, 0, 0, 0, 0, 0, 0),
(301331, 0, 0, 0, 0, 0, 0, 0, 0);

-- The chests' loot (Normal tier on 301330, Heroic tier on 301331; HUB "Boss lists") is WP L-2's
-- rev_loot_wave_2_scarlet_monastery.sql, which sorts after this rev.
