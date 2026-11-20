-- Blackrock Depths build WP-D15: Golem Lord Argelmach (8983), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D15, s7 #20; build spec
-- docs/dungeons/blackrock-depths-3-manufactory.md "Golem Lord Argelmach"). His template
-- (boss_golem_lord_argelmach_rework, AIName '', health, DamageModifier, immunity 1972, INSTANCE_BIND: behind
-- BIND_WAVE_2), the golems 300833-300835, the Arcane Orb 300837 and the spells 211330-211348 are apps/dbc-tools
-- source/npcs/blackrock_depths/argelmach.py.
-- Wave 2: this rev belongs with the change that flips BIND_WAVE_2 / kWave2Bound (it drops his SmartAI, which the stock
-- binding still needs while wave 2 is unbound).

-- His 14 SmartAI rows (Lightning Shield, Chain Lightning, Shock, the hall release handshake with instance data 31 /
-- 32): boss_golem_lord_argelmach_rework casts copies of the three spells itself, and the release is gone (ruling 56).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 8983 AND `source_type` = 0;

-- His texts, groups 0-3 and 5-7 (group 4, the console line, is D16's rev): the stock say (group 0, BroadcastTextId
-- 5297) moves to the pull and becomes a yell; the new lines are yells (14) and boss emotes (41). 5 and 6 are the hard
-- mode's (D16 says them).
DELETE FROM `creature_text` WHERE `CreatureID` = 8983 AND `GroupID` IN (0, 1, 2, 3, 5, 6, 7);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(8983, 0, 0, 'Intruders in the Manufactory? My constructs will destroy you!', 14, 0, 100, 0, 0, 0, 5297, 0,
    'Golem Lord Argelmach - Aggro'),
(8983, 1, 0, 'Toxitron, rise! Clean up this mess!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Golem Lord Argelmach - Toxitron wakes (AR4)'),
(8983, 2, 0, 'Electron, online! Bind them together!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Golem Lord Argelmach - Electron wakes (AR4)'),
(8983, 3, 0, 'Arcanoton, feed me power!', 14, 0, 100, 0, 0, 0, 0, 0, 'Golem Lord Argelmach - Arcanoton wakes (AR4)'),
(8983, 5, 0, 'Magmatron begins to Incinerate!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Golem Lord Argelmach - Incineration (AR11, D16)'),
(8983, 6, 0, 'The wreck''s core keeps running!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Golem Lord Argelmach - Salvaged Core (AR13, D16)'),
(8983, 7, 0, 'Lotwil... was right... about me...', 14, 0, 100, 0, 0, 0, 0, 0, 'Golem Lord Argelmach - Death');

-- The golem hall becomes plain trash (handoff s7 #20, ruling 56: no mass release). The six Ragereaver Golems (8906)
-- lose their template Stoned aura (10255) (the heroic copy's addon row is generated from this replayed normal row,
-- lib/dungeon_heroic.py, so it carries '' too); the one Wrath Hammer Construct (8907, guid 45933) loses its
-- spawn's. Bytes and the rest of both rows are kept.
UPDATE `creature_template_addon` SET `auras` = '' WHERE `entry` = 8906;
UPDATE `creature_addon` SET `auras` = '' WHERE `guid` = 45933;

-- The two hall mobs that stood in his chamber (Ragereaver 45932 at (851.8, 13.3), Wrath Hammer 45933 at (856.7, 17.9),
-- 6-10 yd from him) would join his pull as plain trash: they move into the golem hall's open floor (the 20.5 yd disc
-- round (786.2, -10.2), NAVMESH 3.2), by the pack already there. Entry, spawn mask and everything else kept.
UPDATE `creature` SET `position_x` = 786.2, `position_y` = -14.5, `position_z` = -53.65, `orientation` = 1.57
    WHERE `guid` = 45932 AND `id` = 8906;
UPDATE `creature` SET `position_x` = 790.5, `position_y` = -14.0, `position_z` = -53.65, `orientation` = 1.57
    WHERE `guid` = 45933 AND `id` = 8907;

-- 301285-301287 Golem Pedestal: the plinths the three golems stand on (the pedestals do not exist in stock, handoff s7
-- #20). GENERIC (type 5: no lock, no key item, no click), not selectable (addon flags 16), the Dark Iron anvil display
-- 3311 (_visuals GODI_FOURTH_PEDESTAL: D16's fourth pedestal 301288 uses the same, so the four match) at size 0.5
-- (about 3 x 3 x 1 yd; the golem stands on the floor in it: the look is a designer check in game).
-- Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301285, 5, 3311, 'Golem Pedestal', '', '', '', 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, '', '', 0),
(301286, 5, 3311, 'Golem Pedestal', '', '', '', 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, '', '', 0),
(301287, 5, 3311, 'Golem Pedestal', '', '', '', 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`),
    `name` = VALUES(`name`), `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` IN (301285, 301286, 301287);
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301285, 0, 16, 0, 0, 0, 0, 0, 0),
(301286, 0, 16, 0, 0, 0, 0, 0, 0),
(301287, 0, 16, 0, 0, 0, 0, 0, 0);

-- Their spawns (normal and heroic: spawnMask 3) at the pedestal spots P1-P3 (ArgelmachLogic.h kPedestal1-3, NAVMESH
-- 3.2), facing the chamber's middle (851, 22); guids = the entry x 10 (free in the live DB, read-only check
-- 2026-11-17). Rotation = the orientation about z (rotation2 = sin(o/2), rotation3 = cos(o/2)). Permanent props: the
-- golems come and go on them, the plinths stay (kill, wipe, reload).
DELETE FROM `gameobject` WHERE `id` IN (301285, 301286, 301287) AND `guid` IN (3012850, 3012860, 3012870);
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`,
    `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`,
    `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3012850, 301285, 230, 0, 0, 3, 1, 839.2, 37.8, -53.5, 5.3539, 0, 0, 0.44812, -0.893973, 300, 255, 1, '', 0,
    'Blackrock Depths D15: Golem Pedestal P1 (Toxitron)'),
(3012860, 301286, 230, 0, 0, 3, 1, 853.8, 41.2, -53.4, 4.5676, 0, 0, 0.756408, -0.6541, 300, 255, 1, '', 0,
    'Blackrock Depths D15: Golem Pedestal P2 (Electron)'),
(3012870, 301287, 230, 0, 0, 3, 1, 865.8, 24.2, -53.6, 3.2892, 0, 0, 0.997279, -0.073717, 300, 255, 1, '', 0,
    'Blackrock Depths D15: Golem Pedestal P3 (Arcanoton)');
