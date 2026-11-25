-- Ragefire Chasm build WP-D4H: Starving, Taragaman's hard mode (heroic only), the rows dbc-tools cannot declare
-- (.agents/plans/ragefire-chasm-build/ragefire-chasm-build.HANDOFF.md s3.7, s7 #15-#18; build spec
-- docs/dungeons/ragefire-chasm-rework.md "Hard mode kit: Starving"). The Blood Globule 300987 and the spells
-- 213690-213695 are apps/dbc-tools source/npcs/ragefire_chasm/taragaman_hard_mode.py; the engine side is
-- modules/mod-dungeon-bosses src/RagefireChasm/taragaman_hard_mode.cpp (spots and ids pinned against
-- RagefireChasmRework.h by lib/test_ragefire_chasm_taragaman_hard_mode.py). No SmartAI row (rule 14).

-- His hard mode lines (SP "Text"; groups 0-6 are WP-D4's rev): 7 phase 2 and 9 the pour are yells, 8 a globule wave is
-- a boss emote (41), map-wide (TextRange 3) as his others.
DELETE FROM `creature_text` WHERE `CreatureID` = 11520 AND `GroupID` BETWEEN 7 AND 9;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(11520, 7, 0, 'The lake bleeds for me! Drink, drink!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Taragaman - the hard mode''s phase 2 (Starving)'),
(11520, 8, 0, 'Blood crawls up from the lake toward %s!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Taragaman - a wave of Blood Globules (TG8, Starving)'),
(11520, 9, 0, 'That taste... MORE! Bring me MORE!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Taragaman - the blood poured: the hard mode set (Starving)');

-- 301340 the Blood Shrine (display 328 WarlockShrine, beside the stock Orb, which stays as it is) and 301341 the pour
-- spot (display 216 Cauldron, at the -x arm's foot): goobers (type 10: no lock, no spell, no despawn) whose use
-- go_rfc_blood_shrine and go_rfc_pour_spot take whole (the engine never handles it). Displays equal ._visuals
-- GODI_HM_OBJECT and GODI_HM_OBJECT_ALT. Upserts: gameobject_template rows are never deleted (codestyle-sql
-- not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301340, 10, 328, 'Blood Shrine', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, '', 'go_rfc_blood_shrine', 0),
(301341, 10, 216, 'Blood-Stained Cauldron', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, '', 'go_rfc_pour_spot', 0)
ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`), `name` = VALUES(`name`),
    `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` IN (301340, 301341);
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301340, 0, 0, 0, 0, 0, 0, 0, 0),
(301341, 0, 0, 0, 0, 0, 0, 0, 0);

-- Their spawns, heroic only (spawnMask 2: the hard mode is heroic only; rule 14), at RagefireChasmRework.h
-- kBloodShrine (3.5 yd from the Orb) and kPourSpot. Guids = the entry x 10 (free in the
-- live DB, read-only check 2026-11-24). Permanent props: inert (not selectable) once the blood is poured or he is dead.
DELETE FROM `gameobject` WHERE `guid` IN (3013400, 3013410) AND `id` IN (301340, 301341);
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`,
    `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`,
    `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3013400, 301340, 389, 0, 0, 2, 1, -367.5, 165, -21, 0, 0, 0, 0, 1, 300, 255, 1, '', 0,
    'Ragefire Chasm D4H: the Blood Shrine (Starving, heroic only)'),
(3013410, 301341, 389, 0, 0, 2, 1, -276.8, 144.8, -22.7, 0, 0, 0, 0, 1, 300, 255, 1, '', 0,
    'Ragefire Chasm D4H: the pour spot (Starving, heroic only)');
