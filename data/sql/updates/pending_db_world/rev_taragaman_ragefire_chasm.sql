-- Ragefire Chasm build WP-D4: Taragaman the Hungerer (11520) and the Searing Spike, the rows dbc-tools cannot declare
-- (.agents/plans/ragefire-chasm-build/ragefire-chasm-build.HANDOFF.md s3.5 row D4, s7 #19 A; build spec
-- docs/dungeons/ragefire-chasm-rework.md "Taragaman the Hungerer"). His template columns and spells 213650-213668 are
-- apps/dbc-tools source/npcs/ragefire_chasm/taragaman.py; his stock smart_scripts rows were dropped by WP-S0's
-- rev_skeleton_ragefire_chasm.sql. This rev inserts no spawn and no SmartAI row (rule 14: nothing for the heroic spawn
-- mask to miss). Groups 7 to 9 are WP-D4H's.

-- His texts (SP "Text"; he had none). Group 0 is said by the instance when the third lieutenant dies: a zone yell
-- (TextRange 2), so it carries over the lake from any room. The emotes are boss emotes (41) and map-wide (TextRange 3):
-- an emote's own range is 25 yd and the plateau's arms are 35 to 42 yd long.
DELETE FROM `creature_text` WHERE `CreatureID` = 11520 AND `GroupID` BETWEEN 0 AND 6;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(11520, 0, 0, 'Three servants burned, and still you smell of fear. Come, little meat!', 14, 0, 100, 0, 0, 0, 0, 2,
    'Taragaman - the gate opens (TG0, said by the instance)'),
(11520, 1, 0, 'The Hungerer feeds!', 14, 0, 100, 0, 0, 0, 0, 0, 'Taragaman - aggro'),
(11520, 2, 0, '%s smells blood on $n!', 41, 0, 100, 0, 0, 0, 0, 3, 'Taragaman - Feast (TG1)'),
(11520, 3, 0, '%s raises his blade and begins to spin!', 41, 0, 100, 0, 0, 0, 0, 3, 'Taragaman - Felstorm (TG3)'),
(11520, 4, 0, '%s leaps to the center stone, and spikes of rock heave from the plateau!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Taragaman - Searing Nova (TG6)'),
(11520, 5, 0, '%s begins to devour $n!', 41, 0, 100, 0, 0, 0, 0, 3, 'Taragaman - Devour (TG2, heroic)'),
(11520, 6, 0, 'The hunger... never ends...', 14, 0, 100, 0, 0, 0, 0, 0, 'Taragaman - death');

-- 301342 Searing Spike (display 5073 Stalagmite01, size 2.0 on both difficulties: s7 #19 A, a shadow at least 4.5 yd
-- wide 16 yd out at any yaw; the fallback is display 3711 Lavarock at size 0.8): GENERIC (type 5: no lock, no key item,
-- no click) and not selectable (addon flags 16), summoned by the script at each Nova and deleted when it ends. Its
-- collision model blocks line of sight (the BM Hide kind judges with IsWithinLOSInMap): unconfirmed in game. Display
-- and size equal ._visuals GODI_SEARING_SPIKE / SEARING_SPIKE_SIZE and RagefireChasmRework.h kSpikeGoSize
-- (lib/test_ragefire_chasm_taragaman.py).
-- Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301342, 5, 5073, 'Searing Spike', '', '', '', 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`),
    `name` = VALUES(`name`), `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` = 301342;
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301342, 0, 16, 0, 0, 0, 0, 0, 0);
