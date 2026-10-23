-- DB update 2026_10_23_32 -> 2026_10_23_33
-- Alliance Shaman trainer in Stormwind City (Park) and the Stormwind guard directions to it.
--
-- Farseer Umbrua (20407) is the stock Exodar-faction Shaman Trainer (faction 1640, trainer 210 via
-- creature_default_trainer = the same full class trainer the other shaman trainers use). Her only stock spawn
-- (guid 79860, Valley of Heroes) is parked in phaseMask 16384 by mod-progression phase_00 until phase 7, so this adds
-- a second, visible spawn in the Park. Spawn guid follows the fork's custom-spawn block (5300000+).
DELETE FROM `creature` WHERE `id` = 20407 AND `guid` = 5300708;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`, `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `wander_distance`, `currentwaypoint`, `curhealth`, `curmana`, `MovementType`, `npcflag`, `unit_flags`, `dynamicflags`, `ScriptName`, `VerifiedBuild`, `CreateObject`, `Comment`) VALUES
(5300708, 20407, 0, 1519, 1519, 1, 1, 1, -8751.139, 1084.062, 90.78052, 5.133289, 180, 0, 0, 3297, 2434, 0, 0, 0, 0, '', 0, 0, 'Farseer Umbrua - Stormwind Park Shaman trainer');

-- POI 37 ("Farseer Umbrua") is the map pin used by the Shaman guard option. Stock points it at the Valley of Heroes
-- spawn; move it to the new trainer. mod-progression phase_07 re-inserts the guard option (401, 6) pointing at this
-- same POI 37 / menu 8164, so keeping the ids makes that phase harmless.
DELETE FROM `points_of_interest` WHERE `ID` = 37;
INSERT INTO `points_of_interest` (`ID`, `PositionX`, `PositionY`, `Icon`, `Flags`, `Importance`, `Name`) VALUES
(37, -8751.139, 1084.062, 7, 99, 0, 'Farseer Umbrua');

-- Guard directions text (menu 8164) for the new location; the stock text sends players to the Valley of Heroes shore.
DELETE FROM `npc_text` WHERE `ID` = 900020;
INSERT INTO `npc_text` (`ID`, `text0_0`, `text0_1`, `Probability0`) VALUES
(900020, 'A draenei Farseer named Umbrua teaches the ways of the elements here in the city. You will find her in the Park, among the trees.', 'A draenei Farseer named Umbrua teaches the ways of the elements here in the city. You will find her in the Park, among the trees.', 1);

DELETE FROM `gossip_menu` WHERE `MenuID` = 8164;
INSERT INTO `gossip_menu` (`MenuID`, `TextID`) VALUES
(8164, 900020);

-- Stormwind City Guard / City Patroller / Harbor Guard: "Class Trainer" submenu 401 has no Shaman entry in stock
-- (mod-progression phase_00 deletes it and phase_07 adds it); add it, Alliance guards need no condition.
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 401 AND `OptionID` = 6;
INSERT INTO `gossip_menu_option` (`MenuID`, `OptionID`, `OptionIcon`, `OptionText`, `OptionBroadcastTextID`, `OptionType`, `OptionNpcFlag`, `ActionMenuID`, `ActionPoiID`, `BoxCoded`, `BoxMoney`, `BoxText`, `BoxBroadcastTextID`, `VerifiedBuild`) VALUES
(401, 6, 0, 'Shaman', 45410, 1, 1, 8164, 37, 0, 0, '', 0, 0);

-- Stormwind Guard (1423, menu 3506 -> Class Trainer submenu 3519): its Shaman option has a text but no POI; use the
-- same text and POI.
UPDATE `gossip_menu_option` SET `ActionMenuID` = 8164, `ActionPoiID` = 37 WHERE `MenuID` = 3519 AND `OptionID` = 6;
