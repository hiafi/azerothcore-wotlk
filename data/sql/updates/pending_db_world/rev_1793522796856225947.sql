-- Ironforge Shaman trainer and guard directions, kept clear of mod-progression (same fix as the Stormwind one in
-- this PR).
--
-- Ironforge has no shaman trainer today: mod-progression phase_00 hides every spawn of Farseer Javad (23127, stock
-- guid 1815 at the Great Forge) and deletes the Ironforge Guard's Shaman option (2144, 7); phase_07 brings both back.
-- Nothing the phases touch is used here:
--   * Javad becomes 900019, a copy of 23127 (npc_tools block, hand-written), spawned on the stock spot as guid 5300723
--     (first free guid after the Death Knight trainer block 5300709-5300722);
--   * the stock spawn 1815 is removed, so phase_07 has no second Javad to show;
--   * the Ironforge Guard's "Class Trainer" option (2121, 11) opens 5300014, a copy of submenu 2144 plus Shaman.
-- HealthModifier is the stock 1.25 (phase_00 sets 23127 to 3.1253 and phase_13 back to 1.25).

-- Farseer Javad: same faction, gossip (7357), trainer (210), model, gear and quests as 23127.
INSERT INTO `creature_template` (`entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`,
    `KillCredit1`, `KillCredit2`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`,
    `faction`, `npcflag`, `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`,
    `dmgschool`, `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`,
    `unit_class`, `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`,
    `pickpocketloot`, `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`,
    `HoverHeight`, `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`,
    `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`, `VerifiedBuild`)
VALUES (900019, 0, 0, 0, 0, 0, 'Farseer Javad', 'Shaman Trainer', NULL, 7357, 50, 50, 0, 1638, 51, 1, 1.14286, 1,
    1, 20, 0, 0, 1, 2000, 2000, 1, 1, 2, 33280, 2048, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, '', 0, 1, 1.25, 1, 1, 1, 0, 0,
    1, 0, 2, '', NULL)
    ON DUPLICATE KEY UPDATE `difficulty_entry_1` = VALUES(`difficulty_entry_1`),
    `difficulty_entry_2` = VALUES(`difficulty_entry_2`), `difficulty_entry_3` = VALUES(`difficulty_entry_3`),
    `KillCredit1` = VALUES(`KillCredit1`), `KillCredit2` = VALUES(`KillCredit2`), `name` = VALUES(`name`),
    `subname` = VALUES(`subname`), `IconName` = VALUES(`IconName`), `gossip_menu_id` = VALUES(`gossip_menu_id`),
    `minlevel` = VALUES(`minlevel`), `maxlevel` = VALUES(`maxlevel`), `exp` = VALUES(`exp`),
    `faction` = VALUES(`faction`), `npcflag` = VALUES(`npcflag`), `speed_walk` = VALUES(`speed_walk`),
    `speed_run` = VALUES(`speed_run`), `speed_swim` = VALUES(`speed_swim`), `speed_flight` = VALUES(`speed_flight`),
    `detection_range` = VALUES(`detection_range`), `rank` = VALUES(`rank`), `dmgschool` = VALUES(`dmgschool`),
    `DamageModifier` = VALUES(`DamageModifier`), `BaseAttackTime` = VALUES(`BaseAttackTime`),
    `RangeAttackTime` = VALUES(`RangeAttackTime`), `BaseVariance` = VALUES(`BaseVariance`),
    `RangeVariance` = VALUES(`RangeVariance`), `unit_class` = VALUES(`unit_class`), `unit_flags` = VALUES(`unit_flags`),
    `unit_flags2` = VALUES(`unit_flags2`), `dynamicflags` = VALUES(`dynamicflags`), `family` = VALUES(`family`),
    `type` = VALUES(`type`), `type_flags` = VALUES(`type_flags`), `lootid` = VALUES(`lootid`),
    `pickpocketloot` = VALUES(`pickpocketloot`), `skinloot` = VALUES(`skinloot`),
    `PetSpellDataId` = VALUES(`PetSpellDataId`), `VehicleId` = VALUES(`VehicleId`), `mingold` = VALUES(`mingold`),
    `maxgold` = VALUES(`maxgold`), `AIName` = VALUES(`AIName`), `MovementType` = VALUES(`MovementType`),
    `HoverHeight` = VALUES(`HoverHeight`), `HealthModifier` = VALUES(`HealthModifier`),
    `ManaModifier` = VALUES(`ManaModifier`), `ArmorModifier` = VALUES(`ArmorModifier`),
    `ExperienceModifier` = VALUES(`ExperienceModifier`), `RacialLeader` = VALUES(`RacialLeader`),
    `movementId` = VALUES(`movementId`), `RegenHealth` = VALUES(`RegenHealth`),
    `CreatureImmunitiesId` = VALUES(`CreatureImmunitiesId`), `flags_extra` = VALUES(`flags_extra`),
    `ScriptName` = VALUES(`ScriptName`), `VerifiedBuild` = VALUES(`VerifiedBuild`);

DELETE FROM `creature_template_model` WHERE `CreatureID` = 900019;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`,
    `VerifiedBuild`)
VALUES (900019, 0, 21265, 1, 1, NULL);

DELETE FROM `creature_template_addon` WHERE `entry` = 900019;
INSERT INTO `creature_template_addon` (`entry`, `path_id`, `mount`, `bytes1`, `bytes2`, `emote`,
    `visibilityDistanceType`, `auras`)
VALUES (900019, 0, 0, 0, 1, 0, 0, NULL);

DELETE FROM `creature_equip_template` WHERE `CreatureID` = 900019;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`)
VALUES (900019, 1, 1908, 0, 0, NULL);

DELETE FROM `creature_default_trainer` WHERE `CreatureId` = 900019;
INSERT INTO `creature_default_trainer` (`CreatureId`, `TrainerId`) VALUES (900019, 210);

-- Elemental Mastery, Call of Fire, Call of Water, Call of Air, Relic of the Earthen Ring
DELETE FROM `creature_queststarter` WHERE `id` = 900019;
INSERT INTO `creature_queststarter` (`id`, `quest`) VALUES
(900019, 8410),
(900019, 9462),
(900019, 9502),
(900019, 9547),
(900019, 14111);

-- New spawn on the stock spot; the stock spawn goes.
DELETE FROM `creature` WHERE `id` = 900019 AND `guid` = 5300723;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `wander_distance`, `currentwaypoint`,
    `curhealth`, `curmana`, `MovementType`, `npcflag`, `unit_flags`, `dynamicflags`, `ScriptName`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(5300723, 900019, 0, 0, 0, 1, 1, 1, -4720.26, -1150.07, 502.448, 3.75844, 300, 0, 0, 2215, 1807, 0, 0, 0, 0, '', 0,
    0, 'Farseer Javad - Ironforge Shaman trainer');

DELETE FROM `creature` WHERE `id` = 23127 AND `guid` = 1815;

-- Ironforge Guard: "Class Trainer" (2121, 11) now opens 5300014, a copy of submenu 2144 (same text and options, Death
-- Knight -> 5300007 / POI 1012) plus Shaman -> 8643 / POI 65, the stock directions to Javad at the Great Forge, with
-- the ids phase_07 uses. Menu 2144 itself is left to mod-progression.
DELETE FROM `gossip_menu` WHERE `MenuID` = 5300014;
INSERT INTO `gossip_menu` (`MenuID`, `TextID`) VALUES
(5300014, 2766);

DELETE FROM `gossip_menu_option` WHERE `MenuID` = 5300014;
INSERT INTO `gossip_menu_option` (`MenuID`, `OptionID`, `OptionIcon`, `OptionText`, `OptionBroadcastTextID`,
    `OptionType`, `OptionNpcFlag`, `ActionMenuID`, `ActionPoiID`, `BoxCoded`, `BoxMoney`, `BoxText`,
    `BoxBroadcastTextID`, `VerifiedBuild`) VALUES
(5300014, 0, 0, 'Hunter', 50546, 1, 1, 2147, 61, 0, 0, '', 0, 0),
(5300014, 1, 0, 'Mage', 45404, 1, 1, 2148, 62, 0, 0, '', 0, 0),
(5300014, 2, 0, 'Paladin', 48028, 1, 1, 2150, 62, 0, 0, '', 0, 0),
(5300014, 3, 0, 'Priest', 45405, 1, 1, 2149, 62, 0, 0, '', 0, 0),
(5300014, 4, 0, 'Rogue', 45406, 1, 1, 2151, 63, 0, 0, '', 0, 0),
(5300014, 5, 0, 'Warlock', 45407, 1, 1, 2152, 64, 0, 0, '', 0, 0),
(5300014, 6, 0, 'Warrior', 45408, 1, 1, 2153, 61, 0, 0, '', 0, 0),
(5300014, 7, 0, 'Shaman', 45410, 1, 1, 8643, 65, 0, 0, '', 0, 0),
(5300014, 9, 0, 'Death Knight', 0, 1, 1, 5300007, 1012, 0, 0, '', 0, 0);

UPDATE `gossip_menu_option` SET `ActionMenuID` = 5300014 WHERE `MenuID` = 2121 AND `OptionID` = 11;

-- Ironforge Mountaineer: its "Class Trainer" submenu 3545 has never had a Shaman entry, and mod-progression does not
-- edit it, so the option goes straight in.
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 3545 AND `OptionID` = 7;
INSERT INTO `gossip_menu_option` (`MenuID`, `OptionID`, `OptionIcon`, `OptionText`, `OptionBroadcastTextID`,
    `OptionType`, `OptionNpcFlag`, `ActionMenuID`, `ActionPoiID`, `BoxCoded`, `BoxMoney`, `BoxText`,
    `BoxBroadcastTextID`, `VerifiedBuild`) VALUES
(3545, 7, 0, 'Shaman', 45410, 1, 1, 8643, 65, 0, 0, '', 0, 0);
