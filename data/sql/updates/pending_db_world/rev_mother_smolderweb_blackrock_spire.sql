-- Blackrock Spire build WP-B4: Mother Smolderweb (10596), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.5 row B4; build spec
-- docs/dungeons/blackrock-spire-rework.md SP 1231-1469). Her template (boss_mother_smolderweb_rework, AIName '',
-- health, DamageModifier 5.75, immunity 1972), the Smolderweb Broodling 300705 and the spells 210120-210130 are
-- apps/dbc-tools source/npcs/blackrock_spire/smolderweb.py. Her SmartAI rows went in rev_blackrock_spire_skeleton.sql.
-- Her loot, the cave's twelve quest eggs (gameobject 175606, quest 4862) and Ragged John's gossip (menu 2061,
-- quest 4866) are untouched.

-- Her texts (SP "Text"; she had none): one emote per Lay Egg round, per Brood Call (heroic) and at her death (type 41,
-- a boss emote: center-screen and in the raid warning area).
DELETE FROM `creature_text` WHERE `CreatureID` = 10596 AND `GroupID` BETWEEN 0 AND 2;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10596, 0, 0, '%s lays her eggs!', 41, 0, 100, 0, 0, 0, 0, 0, 'Mother Smolderweb - Lay Egg (SW2)'),
(10596, 1, 0, '%s calls to her brood!', 41, 0, 100, 0, 0, 0, 0, 0, 'Mother Smolderweb - Brood Call, heroic (SW7)'),
(10596, 2, 0, '%s spits her last milk across the cave!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Mother Smolderweb - Last Milk (SW8)');

-- 301251 Smolderweb Egg (display 364 SpiderEggSack04, ruling 36): GENERIC (type 5: no lock, no key item, no click) and
-- not selectable (addon flags 16), so an egg cannot be targeted or looted (SP: "they cannot be attacked") and is only
-- ever hatched by a step. The script summons the starting eight at the pull and one for each Lay Egg marker, deletes
-- an egg when it hatches (or on a Brood Call, a reset or her death), and its own timed despawn is a backstop. Size 1.5
-- is a guess for a 4 yd Mine (the marker ring carries the hitbox): tune after the first sight of it.
-- Upsert: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301251, 5, 364, 'Smolderweb Egg', '', '', '', 1.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`),
    `name` = VALUES(`name`), `size` = VALUES(`size`), `Data1` = VALUES(`Data1`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` = 301251;
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301251, 0, 16, 0, 0, 0, 0, 0, 0);
