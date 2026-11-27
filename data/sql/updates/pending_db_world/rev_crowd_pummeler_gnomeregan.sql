-- Gnomeregan build WP-D5: Crowd Pummeler 9-60 (6229) in the glass window, the rows dbc-tools cannot declare
-- (.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.5 row D5, s7 #29 A, #38 k A, s10 the window ruling;
-- build spec docs/dungeons/gnomeregan-rework.md "Crowd Pummeler 9-60"). His template columns, model row (scale 5),
-- spells 214460-214489 and the frame stalker 301115 are apps/dbc-tools source/npcs/gnomeregan/crowd_pummeler.py; his
-- script boss_crowd_pummeler_rework; his spawn's move into the glass and its movement row are
-- rev_skeleton_gnomeregan.sql.

-- His texts (CrowdPummelerLogic.h PummelerTexts; none stock: SmartAI 6229 had no text). Emotes, type 41 (rule 2).
-- Line 3 is section 7 #29 A's ("goes dark behind the glass": nothing to slump over under the window ruling).
DELETE FROM `creature_text` WHERE `CreatureID` = 6229 AND `GroupID` IN (0, 1, 2, 3);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(6229, 0, 0, '%s winds up a combination!', 41, 0, 100, 0, 0, 0, 0, 0, 'Crowd Pummeler 9-60 - the Combo (CP1)'),
(6229, 1, 0, 'The bell rings. Round two!', 41, 0, 100, 0, 0, 0, 0, 0, 'Crowd Pummeler 9-60 - round two at 66% (CP1)'),
(6229, 2, 0, 'The bell rings. Final round!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Crowd Pummeler 9-60 - the final round at 33% (CP1)'),
(6229, 3, 0, '%s shudders, sparks, and goes dark behind the glass.', 41, 0, 100, 0, 0, 0, 0, 0,
    'Crowd Pummeler 9-60 - death (s7 #29 A)');

-- His chest (ruling 36, s7 #38 k A): normal 301380 and heroic 301381 (CHEST, lock 57 = no key, consumable, the loot
-- window keeps it closed, group loot: the Zul'Farrak crew stash's and the Scarlet Monastery Last Stand chest's values).
-- Data1 is the loot entry, the GO's own id: L-1 fills gameobject_loot_template 301380 / 301381 (his body carries
-- nothing, s7 #42 A). The display is V's GODI_CHEST 3014 (DarkIronSafe). The instance (instance_gnomeregan_rework.cpp)
-- places the entry of the map's difficulty at kPummelerChestSpot (-899.0, 365.0) when slot 4 goes DONE and again after
-- a reload until it is emptied; this rev inserts no spawn.
-- Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301380, 3, 3014, 'Pummeler Prize Strongbox', '', '', '', 1, 57, 301380, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1,
    0, 0, 0, 0, 0, 0, 0, 0, '', '', 0),
(301381, 3, 3014, 'Pummeler Prize Strongbox', '', '', '', 1, 57, 301381, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1,
    0, 0, 0, 0, 0, 0, 0, 0, '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`),
    `displayId` = VALUES(`displayId`), `name` = VALUES(`name`), `size` = VALUES(`size`), `Data0` = VALUES(`Data0`),
    `Data1` = VALUES(`Data1`), `Data3` = VALUES(`Data3`), `Data11` = VALUES(`Data11`), `Data15` = VALUES(`Data15`),
    `AIName` = VALUES(`AIName`), `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` IN (301380, 301381);
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301380, 0, 0, 0, 0, 0, 0, 0, 0),
(301381, 0, 0, 0, 0, 0, 0, 0, 0);
