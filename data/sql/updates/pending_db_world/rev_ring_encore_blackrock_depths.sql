-- Blackrock Depths build WP-D6: the Ring of Law's hard mode, the Encore (Theldren 16059, Korv 16053, Lefty 16049,
-- Volida 16058, Malgen Longspear 16052), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D6, s3.7; build spec
-- docs/dungeons/blackrock-depths-1-detention-block.md "Hard mode: the Encore"). The five templates' ScriptName /
-- AIName, Theldren's immunity, Korv's totems 300789-300791 and the spells 210960-210999 are apps/dbc-tools
-- source/npcs/blackrock_depths/ring_encore.py; their heroic health is WP-H's.

-- The five members' stock SmartAI (16059 rows 0-5, 16053 rows 0-3, 16049 rows 0-2, 16058 rows 0-2, 16052 rows 0-1):
-- ring_encore_hard_mode.cpp runs them now. The four stock members the Encore no longer uses (16050, 16051, 16054,
-- 16055) keep theirs (summoned nowhere since Grimstone's rework).
DELETE FROM `smart_scripts` WHERE `entryorguid` IN (16049, 16052, 16053, 16058, 16059) AND `source_type` = 0;

-- Theldren's lines: group 0 his three stock yells (unused in stock, now the leap); group 1 new, his real death.
DELETE FROM `creature_text` WHERE `CreatureID` = 16059 AND `GroupID` = 1;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(16059, 1, 0, 'The title... is yours...', 14, 0, 100, 0, 0, 0, 0, 0, 'Theldren - death (BRD D6, the Encore)');

-- 301280 Banner of Provocation, the Encore's banner (handoff s3.3: the stock 181058 is GENERIC, type 5, and cannot be
-- clicked): a goober (type 10, no lock, no spell, no loot) with the stock banner's display 6663 (ArenaFlag.mdx,
-- V-1's GODI_ARENA_BANNER), whose script owns the click (go_brd_encore_banner: DATA_BANNER_BURNED, Grimstone line 11,
-- the banner burns and is gone). Grimstone's Encore script summons it at Favor 10 on heroic (no spawn row).
-- Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301280, 10, 6663, 'Banner of Provocation', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, '', 'go_brd_encore_banner', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`),
    `displayId` = VALUES(`displayId`), `name` = VALUES(`name`), `size` = VALUES(`size`), `Data0` = VALUES(`Data0`),
    `AIName` = VALUES(`AIName`), `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` = 301280;
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301280, 0, 0, 0, 0, 0, 0, 0, 0);
