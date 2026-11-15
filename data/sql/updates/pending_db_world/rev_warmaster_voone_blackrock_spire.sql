-- Blackrock Spire build WP-B3: War Master Voone (9237), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.5 row B3; build spec
-- docs/dungeons/blackrock-spire-rework.md SP "War Master Voone"). His template (boss_warmaster_voone_rework, AIName '',
-- health, DamageModifier 3.5, immunity 1972, INSTANCE_BIND), the Chain Anchor 300704 and his spells 210090-210101 are
-- apps/dbc-tools source/npcs/blackrock_spire/voone.py. He has no SmartAI (the stock script is C++), and the Mor
-- Grayhoof trigger 45841 and brazier are untouched.

-- His texts (SP "Text"; he had none). Yells (14); the Recall line is a boss emote (41) so it names the mechanic on
-- screen.
DELETE FROM `creature_text` WHERE `CreatureID` = 9237 AND `GroupID` BETWEEN 0 AND 5;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9237, 0, 0, 'You come into Voone''s house? We take this outside!', 14, 0, 100, 0, 0, 0, 0, 0,
    'War Master Voone - The pull (VO1)'),
(9237, 1, 0, 'Voone gonna crack some skulls!', 14, 0, 100, 0, 0, 0, 0, 0, 'War Master Voone - Brawler (VO2)'),
(9237, 2, 0, 'Feel da bite of da axe!', 14, 0, 100, 0, 0, 0, 0, 0, 'War Master Voone - Thrasher (VO2)'),
(9237, 3, 0, 'Blood! Voone want more blood!', 14, 0, 100, 0, 0, 0, 0, 0, 'War Master Voone - War Master (VO2)'),
(9237, 4, 0, '%s calls his axes home!', 41, 0, 100, 0, 0, 0, 0, 0, 'War Master Voone - Recall (VO7)'),
(9237, 5, 0, 'Da Horde... gonna fall apart... without Voone...', 14, 0, 100, 0, 0, 0, 0, 0,
    'War Master Voone - Death');

-- 301250 Stuck Axe: the axe in the floor where a throw landed (display 8494, ORCAXE02), GENERIC (type 5: no lock, no
-- key item, no click), not selectable. Voone summons it for each axe and removes it when the Recall brings the axe
-- home; the summon's own timer is only a safety net. Upserts: gameobject_template rows are never deleted (codestyle-sql
-- not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301250, 5, 8494, 'Stuck Axe', '', '', '', 1.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`),
    `name` = VALUES(`name`), `size` = VALUES(`size`), `Data1` = VALUES(`Data1`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` = 301250;
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301250, 0, 16, 0, 0, 0, 0, 0, 0);
