-- Scholomance build WP-S13: Darkmaster Gandling's hard mode, "the Graduate Exam" (heroic only): the honors program
-- paper and its spawn, the Graduate Examiners' ghost tint and their copied texts
-- (.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S13; build spec
-- docs/dungeons/scholomance-rework.md SC 2909-3006, 3046-3063; modules/mod-dungeon-bosses
-- src/Scholomance/graduate_exam.cpp). The examiners 300548-300554 and the Passing Grade auras 206365-206370 are
-- apps/dbc-tools source/npcs/scholomance/graduate_exam.py.

-- 301153 The Honors Program (go_sc_honors_paper): a goober (type 10, the stock quest scroll shape) whose script owns
-- the click, so the stock goober use never runs. The glowing scroll G_Scroll01 (GODI 210, WP-V's pick for gap 16). A
-- click signs the honors program (DATA_GANDLING_HARD_MODE) once every instructor has Passing Grades from 3 players,
-- and starts the gauntlet; otherwise it says what is missing. Upsert: gameobject_template rows are never deleted
-- (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`, `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`, `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`, `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301153, 10, 210, 'The Honors Program', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', 'go_sc_honors_paper', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`), `name` = VALUES(`name`), `size` = VALUES(`size`), `AIName` = VALUES(`AIName`), `ScriptName` = VALUES(`ScriptName`);

-- Its spawn, heroic only (spawnMask 2: the hard mode is heroic only), on the z 115.8 floor over the study beside "The
-- Birth of the Lich King" (ScholomanceRework.h kHonorsPaper; the route up is unchecked: handoff s7 #17, check in game,
-- kHonorsPaperAlt is the fallback). Guid 3011530 (the entry x 10 convention of S12's keepsake spawns; free in the live
-- DB, read-only check 2026-11-08). Orientation 0 (rotation2 = sin(o/2), rotation3 = cos(o/2)).
DELETE FROM `gameobject` WHERE `id` = 301153 AND `guid` = 3011530;
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`, `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`, `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3011530, 301153, 289, 0, 0, 2, 1, 171.0, 8.0, 116.0, 0, 0, 0, 0, 1, 7200, 255, 1, '', 0, 'Scholomance S13: The Honors Program (Gandling hard mode, heroic only)');

-- The Graduate Examiners' look (SC "a Graduate Examiner tint for the seven examiners", WP-V: Ghost Visual 9617, SV 886)
-- on every examiner from its spawn, and the instructors' wide visibility (visibilityDistanceType 3, as their stock
-- rows). Corvane's examiner too (his examiner Ravenian seats him).
DELETE FROM `creature_template_addon` WHERE (`entry`) IN ((300548), (300549), (300550), (300551), (300552), (300553), (300554));
INSERT INTO `creature_template_addon` (`entry`, `path_id`, `mount`, `bytes1`, `bytes2`, `emote`, `visibilityDistanceType`, `auras`) VALUES
(300548, 0, 0, 0, 0, 0, 3, '9617'),
(300549, 0, 0, 0, 0, 0, 3, '9617'),
(300550, 0, 0, 0, 0, 0, 3, '9617'),
(300551, 0, 0, 0, 0, 0, 3, '9617'),
(300552, 0, 0, 0, 0, 0, 3, '9617'),
(300553, 0, 0, 0, 0, 0, 3, '9617'),
(300554, 0, 0, 0, 0, 0, 3, '9617');

-- The examiners' texts (STAGE-S6 and STAGE-S9 hand-offs): Krastinov's examiner says his mechanic emotes (11261 groups
-- 4-7) and Alexei's his rule yells and the Demerit emote (10504 groups 1-7; his aggro 0 and death 8 are not used in
-- examiner mode). Both AIs talk only through TextExist, so without these rows they stay silent. Malicia, Polkelt, the
-- Ravenian, Corvane and Illucia say nothing as examiners.
DELETE FROM `creature_text` WHERE `CreatureID` = 300549 AND `GroupID` BETWEEN 4 AND 7;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(300549, 4, 0, '%s goes into a frenzy!', 41, 0, 100, 0, 0, 0, 1191, 0,
    'Graduate Examiner Krastinov - Grafted hands, Killing Frenzy (KR6)'),
(300549, 5, 0, '%s straps $n to the Work Bench!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Graduate Examiner Krastinov - Operation (KR1)'),
(300549, 6, 0, '%s stitches new eyes into his skull!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Graduate Examiner Krastinov - Grafted eyes (KR6)'),
(300549, 7, 0, '%s sews a fresh heart into his chest!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Graduate Examiner Krastinov - Grafted heart (KR6)');

DELETE FROM `creature_text` WHERE `CreatureID` = 300553 AND `GroupID` BETWEEN 1 AND 7;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(300553, 1, 0, 'No running in the halls!', 14, 0, 100, 0, 0, 0, 0, 0, 'Graduate Examiner Alexei - No running (AB2)'),
(300553, 2, 0, 'Assembly!', 14, 0, 100, 0, 0, 0, 0, 0, 'Graduate Examiner Alexei - Assembly (AB3)'),
(300553, 3, 0, 'Keep your distance!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Graduate Examiner Alexei - Keep your distance (AB4)'),
(300553, 4, 0, 'Go to the corner!', 14, 0, 100, 0, 0, 0, 0, 0, 'Graduate Examiner Alexei - Out of bounds (AB5)'),
(300553, 5, 0, 'Line up!', 14, 0, 100, 0, 0, 0, 0, 0, 'Graduate Examiner Alexei - Line up (AB6)'),
(300553, 6, 0, 'To your desks!', 14, 0, 100, 0, 0, 0, 0, 0, 'Graduate Examiner Alexei - To your desks (AB7)'),
(300553, 7, 0, '%s marks a demerit against $n.', 41, 0, 100, 0, 0, 0, 0, 0,
    'Graduate Examiner Alexei - Demerit (AB9)');
