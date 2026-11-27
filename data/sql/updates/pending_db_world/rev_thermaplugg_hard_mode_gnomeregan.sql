-- Gnomeregan build WP-D6Ha: the Whole Workshop, part a (Mekgineer Thermaplugg's heroic hard mode), the rows dbc-tools
-- cannot declare (.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.5 row D6Ha, s3.7, rule 35; build spec
-- docs/dungeons/gnomeregan-rework.md "Hard mode: the Whole Workshop", "Hard mode text"). The spells 214540-214548 and
-- the creatures 301135, 301137 and 301138 are apps/dbc-tools source/npcs/gnomeregan/thermaplugg_hard_mode.py; the
-- engine side is modules/mod-dungeon-bosses src/Gnomeregan/thermaplugg_hard_mode.cpp. WP-S0's
-- rev_skeleton_gnomeregan.sql spawns the console (guid 3013820, heroic only, spawnMask 2): its template is here. This
-- rev inserts no spawn and no SmartAI row.

-- His package line, group 9 (D6's rev writes groups 4-8; 10 and 11 are D6Hb's): the yell on the first schematic (90%),
-- SP's text with no sound (the stock voice 5808 says the whole of stock group 1's line, "... They'll destroy you
-- all!", which is the Override's yell: STAGE-R-1-C Nit-2).
DELETE FROM `creature_text` WHERE `CreatureID` = 7800 AND `GroupID` = 9;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(7800, 9, 0, 'My machines are the future!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Thermaplugg - the first schematic loads (MT15, the Whole Workshop, D6Ha)');

-- The room alarm 301137 (it stands at the Clearance Console): the Reactor Leak's countdown (lines 0-4). Boss emotes
-- (41), map-wide (TextRange 3). The console's "Loading schematic" lines are raid boss emotes from Thermaplugg (D6Hb's
-- form, no rows).
DELETE FROM `creature_text` WHERE `CreatureID` = 301137;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(301137, 0, 0, 'Reactor containment failing: 2 minutes.', 41, 0, 100, 0, 0, 0, 0, 3,
    'Workshop Alarm - the Reactor Leak, 2 minutes left (MT25)'),
(301137, 1, 0, 'Reactor containment failing: 1 minute.', 41, 0, 100, 0, 0, 0, 0, 3,
    'Workshop Alarm - the Reactor Leak, 1 minute left (MT25)'),
(301137, 2, 0, 'Reactor containment failing: 30 seconds.', 41, 0, 100, 0, 0, 0, 0, 3,
    'Workshop Alarm - the Reactor Leak, 30 seconds left (MT25)'),
(301137, 3, 0, 'Reactor containment failing: 10 seconds.', 41, 0, 100, 0, 0, 0, 0, 3,
    'Workshop Alarm - the Reactor Leak, 10 seconds left (MT25)'),
(301137, 4, 0, 'Warning! Reactor containment failure!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Workshop Alarm - the Reactor Leak (MT25)');

-- 301382 Clearance Console: a questgiver (type 2: gossip menu 5300022 in Data3, no lock) wearing the Punchographs'
-- G_GnomeTerminal (GODI 2091, _visuals GODI_CONSOLE) at size 1.5; go_gnomer_clearance_console answers the click
-- (heroic, out of combat, the Prismatic Punch Card 9316 in the bags, kept; never a bot). Upsert: gameobject_template
-- rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301382, 2, 2091, 'Clearance Console', '', '', '', 1.5, 0, 0, 0, 5300022, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, '', 'go_gnomer_clearance_console', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`),
    `displayId` = VALUES(`displayId`), `name` = VALUES(`name`), `size` = VALUES(`size`), `Data0` = VALUES(`Data0`),
    `Data1` = VALUES(`Data1`), `Data2` = VALUES(`Data2`), `Data3` = VALUES(`Data3`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` = 301382;
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301382, 0, 0, 0, 0, 0, 0, 0, 0);

-- The console's screen (npc_text 900029) and its one option (the confirmation box). The script shows the option only
-- when the console would take the card; a refusal reads as a notification.
DELETE FROM `npc_text` WHERE `ID` = 900029;
INSERT INTO `npc_text` (`ID`, `text0_0`, `text0_1`, `BroadcastTextID0`, `lang0`,
    `Probability0`) VALUES
(900029, 'CLEARANCE CONSOLE 9-60$B$BWORKSHOP SCHEMATICS: LOCKED.$B$BInsert a punch card of PRISMATIC clearance to unlock every schematic. The card is read, not kept.$B$BWarning: unlocked schematics load into the Mekgineer''s own frame.',
    'CLEARANCE CONSOLE 9-60$B$BWORKSHOP SCHEMATICS: LOCKED.$B$BInsert a punch card of PRISMATIC clearance to unlock every schematic. The card is read, not kept.$B$BWarning: unlocked schematics load into the Mekgineer''s own frame.',
    0, 0, 1);
DELETE FROM `gossip_menu` WHERE `MenuID` = 5300022;
INSERT INTO `gossip_menu` (`MenuID`, `TextID`) VALUES
(5300022, 900029);
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 5300022;
INSERT INTO `gossip_menu_option` (`MenuID`, `OptionID`, `OptionIcon`, `OptionText`, `OptionBroadcastTextID`,
    `OptionType`, `OptionNpcFlag`, `ActionMenuID`, `ActionPoiID`, `BoxCoded`, `BoxMoney`, `BoxText`,
    `BoxBroadcastTextID`, `VerifiedBuild`) VALUES
(5300022, 0, 0, 'Insert the Prismatic Punch Card.', 0, 1, 1, 0, 0, 0, 0,
    'Unlock every schematic? Mekgineer Thermaplugg will fight with the whole workshop (heroic hard mode). The setting holds until the lockout resets; the card stays with you.',
    0, 0);
