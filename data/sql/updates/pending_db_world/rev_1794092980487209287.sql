-- Shadowfang Keep build WP-S2: Razorclaw the Butcher (3886), the rows dbc-tools cannot declare
-- (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md s3.6 row S2). His template (boss_razorclaw_rework,
-- AIName '', health, DamageModifier 2.0, immunities) and spells are apps/dbc-tools
-- source/npcs/shadowfang_keep/razorclaw.py.

-- SmartAI 3886 (Butcher Drain 7485, a mana drain on a random target within 5 yd) is removed (SK "Stock kit", approved);
-- boss_razorclaw_rework replaces it.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 3886 AND `source_type` = 0;

-- Texts (he had none; SK "Text", approved). The two mechanic emotes are boss emotes (41), so they name the mechanic on
-- screen; $n is the (first) hooked player.
DELETE FROM `creature_text` WHERE `CreatureID` = 3886;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(3886, 0, 0, 'Fresh meat for the block!', 14, 0, 100, 0, 0, 0, 0, 0, 'Razorclaw the Butcher - Aggro'),
(3886, 1, 0, '%s hurls a meat hook at $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Razorclaw the Butcher - Meat Hook (RC1)'),
(3886, 2, 0, '%s raises his cleaver high!', 41, 0, 100, 0, 0, 0, 0, 0, 'Razorclaw the Butcher - Butcher''s Cut (RC3)');

-- 301103 Offal Slick: the blood pools dressing the heroic Offal Slick (RC4; handoff s3.10 gap 8 top pick). Stock Blood
-- of Heroes display 4211 (BloodOfHeroes.mdx, 4.75 x 5.25 yd at size 1) at size 0.6, GENERIC (type 5, no data, no
-- script) and not selectable (gameobject_template_addon flags 16 = GO_FLAG_NOT_SELECTABLE). Summoned three per Cut by
-- boss_razorclaw_rework for the slick's 30 s. Upserts: gameobject_template rows are never deleted (codestyle-sql
-- not_delete). The id is WP-S2's pick from the spare 301103-301149 (orchestrator to confirm in ShadowfangKeepRework.h).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`, `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`, `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`, `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301103, 5, 4211, 'Offal Slick', '', '', '', 0.6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`), `name` = VALUES(`name`), `size` = VALUES(`size`), `AIName` = VALUES(`AIName`), `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` = 301103;
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`, `artkit2`, `artkit3`) VALUES
(301103, 0, 16, 0, 0, 0, 0, 0, 0);
