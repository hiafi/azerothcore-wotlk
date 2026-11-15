-- Blackrock Spire build WP-B6: Quartermaster Zigris (9736), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.5 row B6; build spec
-- docs/dungeons/blackrock-spire-rework.md SP 1690-1903). His template (boss_quartermaster_zigris_rework, AIName '',
-- health, DamageModifier 3.5 (stock), immunity 1972), the Clockwork Sheep 300707 and the spells 210180-210191 are
-- apps/dbc-tools source/npcs/blackrock_spire/zigris.py. He has no SmartAI (the stock boss is C++ only) and no text.

-- His texts (SP "Text"; he had none): the pull and death yells, and one emote per fall back and per gadget (type 41, a
-- boss emote: center-screen and in the raid warning area). Line 4 is heroic only (the sheep).
DELETE FROM `creature_text` WHERE `CreatureID` = 9736 AND `GroupID` BETWEEN 0 AND 5;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9736, 0, 0, 'Hands off the legion''s stores!', 14, 0, 100, 0, 0, 0, 0, 0, 'Quartermaster Zigris - Aggro'),
(9736, 1, 0, '%s throws down a smoke bomb and falls back!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Quartermaster Zigris - Fall Back (ZG2)'),
(9736, 2, 0, '%s rolls out the powder kegs!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Quartermaster Zigris - Restock 1: Powder Keg (ZG3)'),
(9736, 3, 0, '%s sets up a mortar on the crates!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Quartermaster Zigris - Restock 2: Mortar (ZG3)'),
(9736, 4, 0, '%s winds up the clockwork sheep!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Quartermaster Zigris - Restock 3: Explosive Sheep, heroic (ZG3)'),
(9736, 5, 0, 'That... was... signed out...', 14, 0, 100, 0, 0, 0, 0, 0, 'Quartermaster Zigris - Death');

-- 301252 Supply Crate (display 5271 OrcCrate06), 301253 Net Trap (display 7529 G_BearTrap), 301254 Powder Keg (display
-- 457 Orcbarrel01): GENERIC (type 5: no lock, no key item, no click) and not selectable (addon flags 16), so a crate
-- cannot be broken or looted (ruling 41), a trap is not a click target and the keg is a prop. The script summons the
-- traps and the kegs for their fight and plays the trap's open / trigger / close animations (SendCustomAnim).
-- Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301252, 5, 5271, 'Supply Crate', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    '', '', 0),
(301253, 5, 7529, 'Net Trap', '', '', '', 1.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    '', '', 0),
(301254, 5, 457, 'Powder Keg', '', '', '', 1.2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`),
    `name` = VALUES(`name`), `size` = VALUES(`size`), `Data1` = VALUES(`Data1`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` IN (301252, 301253, 301254);
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301252, 0, 16, 0, 0, 0, 0, 0, 0),
(301253, 0, 16, 0, 0, 0, 0, 0, 0),
(301254, 0, 16, 0, 0, 0, 0, 0, 0);

-- The three supply crates stand on the ledge for good (set pieces, normal and heroic: spawnMask 3), at ZigrisLogic.h's
-- kZigrisCrates (NAVMESH-REPORT section 6: wall-side, at least 27.9 yd apart; the second is the mortar's) at the
-- ledge's floor heights 88.3 / 88.3 / 88.0, each turned toward the middle of the ledge. Guids 3012520-3012522 (the
-- entry x 10 convention of the kit spawns; free in the live DB, read-only check 2026-11-15). Rotation = the
-- orientation about z (rotation2 = sin(o/2), rotation3 = cos(o/2)). The script finds nothing by guid: the crates have
-- no behavior of their own.
DELETE FROM `gameobject` WHERE `id` = 301252 AND `guid` IN (3012520, 3012521, 3012522);
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`,
    `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`,
    `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3012520, 301252, 229, 0, 0, 3, 1, -203.8, -487.8, 88.3, 1.25, 0, 0, 0.58471, 0.811242, 7200, 255, 1, '', 0,
    'Blackrock Spire B6: Supply Crate 1 (Quartermaster Zigris, the Powder Keg restock)'),
(3012521, 301252, 229, 0, 0, 3, 1, -210.8, -460.8, 88.3, 5.8, 0, 0, 0.241052, -0.970512, 7200, 255, 1, '', 0,
    'Blackrock Spire B6: Supply Crate 2 (Quartermaster Zigris, the Mortar restock; the mortar stands here)'),
(3012522, 301252, 229, 0, 0, 3, 1, -184.8, -450.8, 88.0, 4.09, 0, 0, 0.890169, -0.455631, 7200, 255, 1, '', 0,
    'Blackrock Spire B6: Supply Crate 3 (Quartermaster Zigris, the Explosive Sheep restock, heroic)');
