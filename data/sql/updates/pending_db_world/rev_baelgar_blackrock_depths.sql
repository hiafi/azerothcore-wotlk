-- Blackrock Depths build WP-D13: Bael'Gar (9016) and the Fallen Boulder, the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D13; build spec
-- docs/dungeons/blackrock-depths-2-shadowforge-city.md "Bael'Gar"). His template (boss_baelgar_rework, AIName '', 200k,
-- immunity 1973, INSTANCE_BIND) and spells 211230-211242 are apps/dbc-tools source/npcs/blackrock_depths/baelgar.py;
-- his five stock smart_scripts rows (the four health-event Summon Spawn of Bael'Gar 13895 casts and Magma Splash) were
-- dropped by WP-S0's rev_blackrock_depths_skeleton.sql. The Spawn of Bael'Gar 9436 has no spawns and goes unused.
-- This rev inserts no creature spawn and no SmartAI row (rule 14: nothing for the heroic spawn mask to miss).

-- His texts (S2 "Text"; he had none): the Furnace is a boss emote (41) so it reads on screen, the melt, the Fissure and
-- the Falling Boulder are emotes (16). All four are map-wide (TextRange 3): an emote's own range is 25 yd and the
-- cavern is wider. Group 3 is the Falling Boulder line (handoff gap 38).
DELETE FROM `creature_text` WHERE `CreatureID` = 9016 AND `GroupID` BETWEEN 0 AND 3;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9016, 0, 0, '%s stokes the Molten Furnace! Get out of sight!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Bael''Gar - Molten Furnace (BG4)'),
(9016, 1, 0, 'The boulders melt into slag!', 16, 0, 100, 0, 0, 0, 0, 3, 'Bael''Gar - The Boulders melt (BG5)'),
(9016, 2, 0, '%s slams the ground and the floor cracks open!', 16, 0, 100, 0, 0, 0, 0, 3,
    'Bael''Gar - Fissure (BG6)'),
(9016, 3, 0, 'A boulder tears loose from the ceiling!', 16, 0, 100, 0, 0, 0, 0, 3,
    'Bael''Gar - Falling Boulder (BG3)');

-- 301281 Fallen Boulder (display 3711 Lavarock01, size 1.0: about 5 by 5 yd and 10 yd tall; the fallback is 5736
-- Lavarock02): GENERIC (type 5: no lock, no key item, no click) and not selectable (addon flags 16), summoned by the
-- script at each Falling Boulder impact and deleted when the Furnace's wave ends (BG5). Its collision model blocks
-- line of sight (the BM Hide kind judges with IsWithinLOSInMap): unconfirmed in game. The display here must equal
-- BaelgarLogic.h kBoulderDisplay (the script re-applies that constant at the summon, so one C++ constant is the swap;
-- lib/test_blackrock_depths_baelgar.py keeps the two equal).
-- Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301281, 5, 3711, 'Fallen Boulder', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`),
    `name` = VALUES(`name`), `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` = 301281;
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301281, 0, 16, 0, 0, 0, 0, 0, 0);
