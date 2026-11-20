-- Blackrock Depths build WP-D16: Golem Lord Argelmach's hard mode, the Prototype (heroic only), the rows dbc-tools
-- cannot declare (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.7 row D16, s3.8, s7 #15;
-- build spec docs/dungeons/blackrock-depths-3-manufactory.md "Hard mode"). Magmatron 300836, the Salvaged Core 300838
-- and the spells 211370-211377 are apps/dbc-tools source/npcs/blackrock_depths/argelmach_hard_mode.py; the engine side
-- is modules/mod-dungeon-bosses src/BlackrockDepths/argelmach_hard_mode.cpp.
-- Wave 2: this rev belongs with the change that flips BIND_WAVE_2 / kWave2Bound (the console arms nothing before it:
-- the instance refuses DATA_CONSOLE_ARMED while wave 2 is unbound).

-- His console line, group 4 (D15's rev writes groups 0-3 and 5-7): a yell as the console arms the Prototype.
DELETE FROM `creature_text` WHERE `CreatureID` = 8983 AND `GroupID` = 4;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(8983, 4, 0, 'The prototype? Oh, you will regret that.', 14, 0, 100, 0, 0, 0, 0, 0,
    'Golem Lord Argelmach - the Activation Console arms the Prototype (D16)');

-- 301284 Activation Console: a goober (type 10: no lock, no key item; go_brd_activation_console answers the click and
-- keeps it unselectable while it cannot be used), the Mole Machine Console display 6424 (GO 188498's, _visuals
-- GODI_ACTIVATION_CONSOLE) at size 1. 301288 Golem Pedestal: the fourth plinth Magmatron stands on, as D15's three
-- (GENERIC, not selectable, the Dark Iron anvil display 3311 at size 0.5, _visuals GODI_FOURTH_PEDESTAL).
-- Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301284, 10, 6424, 'Activation Console', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, '', 'go_brd_activation_console', 0),
(301288, 5, 3311, 'Golem Pedestal', '', '', '', 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`),
    `name` = VALUES(`name`), `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `Data1` = VALUES(`Data1`),
    `Data2` = VALUES(`Data2`), `Data3` = VALUES(`Data3`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` IN (301284, 301288);
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301284, 0, 0, 0, 0, 0, 0, 0, 0),
(301288, 0, 16, 0, 0, 0, 0, 0, 0);

-- Their spawns, heroic only (spawnMask 2, the hard mode objects' convention; rule 14): the console by the passage
-- mouth (ArgelmachHardModeLogic.h kConsole, NAVMESH 3.2), facing the fourth pedestal (o 5.5205); the pedestal at P4
-- (ArgelmachLogic.h kPedestal4), facing the chamber's middle (851, 22) like the other three (o 1.0675). Guids = the
-- entry x 10 (free in the live DB, read-only check 2026-11-17). Rotation = the orientation about z (rotation2 =
-- sin(o/2), rotation3 = cos(o/2)). Permanent props (kill, wipe, reload): the console is a per-pull switch, its script
-- relights it from the instance's flag.
DELETE FROM `gameobject` WHERE `id` IN (301284, 301288) AND `guid` IN (3012840, 3012880);
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`,
    `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`,
    `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3012840, 301284, 230, 0, 0, 2, 1, 832.2, 12.8, -53.7, 5.5205, 0, 0, 0.372162, -0.928168, 300, 255, 1, '', 0,
    'Blackrock Depths D16: Activation Console (Argelmach''s hard mode, heroic only, before the pull)'),
(3012880, 301288, 230, 0, 0, 2, 1, 841.2, 4.2, -53.7, 1.0675, 0, 0, 0.508775, 0.8609, 300, 255, 1, '', 0,
    'Blackrock Depths D16: Golem Pedestal P4 (Magmatron, heroic only)');
