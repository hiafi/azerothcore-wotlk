-- Paladin trainers in the capitals, kept clear of mod-progression (same fix as the shaman trainers in this PR).
--
-- Stormwind, Ironforge, Exodar and Silvermoon have stock paladin trainers that mod-progression never hides, and
-- Thunder Bluff has none in 3.3.5. The other three capitals lose theirs: phase_00 hides every spawn of Master
-- Pyreanor (23128, Orgrimmar) and Champion Cyssa Dawnrose (20406, Undercity) until phase_07 and of Rukua (35281,
-- Darnassus) until phase_13, and deletes the Orgrimmar Grunt (1949, 7) and Undercity Guardian (2848, 1) Paladin
-- options until phase_07. Nothing the phases touch is used here:
--   * each trainer becomes a hand-written copy in the npc_tools block (900020-900022), spawned on the stock spot as
--     guids 5300724-5300726, and the stock spawn is removed so a later phase has nothing to show;
--   * the Orgrimmar Grunt and Undercity Guardian "A class trainer" options open 5300015 / 5300016, copies of submenus
--     1949 / 2848 plus the Paladin option with the ids phase_07 uses. The Darnassus Sentinel already has a Paladin
--     option (2343, 3) that no phase edits.

-- Orgrimmar paladin trainer: copy of 23128.
INSERT INTO `creature_template` (`entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`,
    `KillCredit1`, `KillCredit2`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`,
    `faction`, `npcflag`, `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`,
    `dmgschool`, `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`,
    `unit_class`, `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`,
    `pickpocketloot`, `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`,
    `HoverHeight`, `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`,
    `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`, `VerifiedBuild`)
VALUES (900020, 0, 0, 0, 0, 0, 'Master Pyreanor', 'Paladin Trainer', NULL, 6647, 70, 70, 1, 1695, 49, 1, 1.14286, 1, 1,
    20, 0, 0, 1, 2000, 2000, 1, 1, 1, 32768, 2048, 0, 0, 7, 0, 0, 0, 0, 0, 0, 1, 603, '', 1, 1, 1, 1, 1, 1, 0, 0, 1, 0,
    2, '', NULL)
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

DELETE FROM `creature_template_model` WHERE `CreatureID` = 900020;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`,
    `VerifiedBuild`)
VALUES (900020, 0, 21264, 1, 1, NULL);

DELETE FROM `creature_equip_template` WHERE `CreatureID` = 900020;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`)
VALUES (900020, 1, 29403, 27406, 0, NULL);

DELETE FROM `creature_default_trainer` WHERE `CreatureId` = 900020;
INSERT INTO `creature_default_trainer` (`CreatureId`, `TrainerId`) VALUES (900020, 202);

-- Grommash Hold, the stock spot; the stock spawn goes.
DELETE FROM `creature` WHERE `id` = 900020 AND `guid` = 5300724;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `wander_distance`, `currentwaypoint`,
    `curhealth`, `curmana`, `MovementType`, `npcflag`, `unit_flags`, `dynamicflags`, `ScriptName`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(5300724, 900020, 1, 0, 0, 1, 1, 1, 1939.69, -4133.33, 41.2444, 4.17134, 300, 0, 0, 6986, 0, 0, 0, 0, 0, '', 0, 0,
    'Master Pyreanor - Orgrimmar paladin trainer');

DELETE FROM `creature_addon` WHERE `guid` = 5300724;
INSERT INTO `creature_addon` (`guid`, `path_id`, `mount`, `bytes1`, `bytes2`, `emote`, `visibilityDistanceType`,
    `auras`)
VALUES (5300724, 0, 0, 0, 1, 0, 0, NULL);

DELETE FROM `creature` WHERE `id` = 23128 AND `guid` = 6503;

-- Undercity paladin trainer: copy of 20406.
INSERT INTO `creature_template` (`entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`,
    `KillCredit1`, `KillCredit2`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`,
    `faction`, `npcflag`, `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`,
    `dmgschool`, `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`,
    `unit_class`, `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`,
    `pickpocketloot`, `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`,
    `HoverHeight`, `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`,
    `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`, `VerifiedBuild`)
VALUES (900021, 0, 0, 0, 0, 0, 'Champion Cyssa Dawnrose', 'Paladin Trainer', NULL, 61025, 60, 60, 0, 1604, 51, 1,
    1.14286, 1, 1, 20, 0, 0, 1, 2000, 2000, 1, 1, 1, 37376, 2048, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, '', 1, 1, 1.35, 1, 1,
    1, 0, 0, 1, 0, 2, '', NULL)
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

DELETE FROM `creature_template_model` WHERE `CreatureID` = 900021;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`,
    `VerifiedBuild`)
VALUES (900021, 0, 19596, 1, 1, NULL);

DELETE FROM `creature_equip_template` WHERE `CreatureID` = 900021;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`)
VALUES (900021, 1, 27405, 27406, 0, NULL);

DELETE FROM `creature_default_trainer` WHERE `CreatureId` = 900021;
INSERT INTO `creature_default_trainer` (`CreatureId`, `TrainerId`) VALUES (900021, 202);

DELETE FROM `creature_queststarter` WHERE `id` = 900021;
INSERT INTO `creature_queststarter` (`id`, `quest`) VALUES
(900021, 9601);

-- Royal Quarter, the stock spot; the stock spawn goes.
DELETE FROM `creature` WHERE `id` = 900021 AND `guid` = 5300725;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `wander_distance`, `currentwaypoint`,
    `curhealth`, `curmana`, `MovementType`, `npcflag`, `unit_flags`, `dynamicflags`, `ScriptName`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(5300725, 900021, 0, 0, 0, 1, 1, 1, 1298.99, 316.802, -58.4492, 6.0912, 300, 0, 0, 6722, 0, 0, 0, 0, 0, '', 0, 0,
    'Champion Cyssa Dawnrose - Undercity paladin trainer');

DELETE FROM `creature_addon` WHERE `guid` = 5300725;
INSERT INTO `creature_addon` (`guid`, `path_id`, `mount`, `bytes1`, `bytes2`, `emote`, `visibilityDistanceType`,
    `auras`)
VALUES (5300725, 0, 0, 0, 0, 0, 0, NULL);

DELETE FROM `creature` WHERE `id` = 20406 AND `guid` = 32066;

-- Darnassus paladin trainer: copy of 35281.
INSERT INTO `creature_template` (`entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`,
    `KillCredit1`, `KillCredit2`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`,
    `faction`, `npcflag`, `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`,
    `dmgschool`, `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`,
    `unit_class`, `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`,
    `pickpocketloot`, `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`,
    `HoverHeight`, `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`,
    `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`, `VerifiedBuild`)
VALUES (900022, 0, 0, 0, 0, 0, 'Rukua', 'Paladin Trainer', '', 7260, 70, 70, 1, 1694, 49, 1, 1.14286, 1, 1, 20, 0, 0, 1,
    2000, 2000, 1, 1, 1, 32768, 2048, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, '', 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, '', NULL)
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

DELETE FROM `creature_template_model` WHERE `CreatureID` = 900022;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`,
    `VerifiedBuild`)
VALUES (900022, 0, 29735, 1, 1, NULL);

DELETE FROM `creature_template_addon` WHERE `entry` = 900022;
INSERT INTO `creature_template_addon` (`entry`, `path_id`, `mount`, `bytes1`, `bytes2`, `emote`,
    `visibilityDistanceType`, `auras`)
VALUES (900022, 0, 0, 0, 1, 0, 0, NULL);

DELETE FROM `creature_equip_template` WHERE `CreatureID` = 900022;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`)
VALUES (900022, 1, 31743, 29642, 0, NULL);

DELETE FROM `creature_default_trainer` WHERE `CreatureId` = 900022;
INSERT INTO `creature_default_trainer` (`CreatureId`, `TrainerId`) VALUES (900022, 202);

-- Temple of the Moon, the stock spot; the stock spawn goes.
DELETE FROM `creature` WHERE `id` = 900022 AND `guid` = 5300726;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `wander_distance`, `currentwaypoint`,
    `curhealth`, `curmana`, `MovementType`, `npcflag`, `unit_flags`, `dynamicflags`, `ScriptName`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(5300726, 900022, 1, 0, 0, 1, 1, 1, 9664.62, 2529.99, 1360.08, 5.70723, 120, 0, 0, 1, 0, 0, 0, 0, 0, '', 0, 0,
    'Rukua - Darnassus paladin trainer');

DELETE FROM `creature` WHERE `id` = 35281 AND `guid` = 137653;

-- Orgrimmar Grunt: "A class trainer" (1951, 12) opens 5300015, a copy of 1949 plus Paladin -> 8644 / POI 303.
DELETE FROM `gossip_menu` WHERE `MenuID` = 5300015;
INSERT INTO `gossip_menu` (`MenuID`, `TextID`) VALUES
(5300015, 2599);

DELETE FROM `gossip_menu_option` WHERE `MenuID` = 5300015;
INSERT INTO `gossip_menu_option` (`MenuID`, `OptionID`, `OptionIcon`, `OptionText`, `OptionBroadcastTextID`,
    `OptionType`, `OptionNpcFlag`, `ActionMenuID`, `ActionPoiID`, `BoxCoded`, `BoxMoney`, `BoxText`,
    `BoxBroadcastTextID`, `VerifiedBuild`) VALUES
(5300015, 0, 0, 'Hunter', 50546, 1, 1, 1906, 300, 0, 0, '', 0, 0),
(5300015, 1, 0, 'Mage', 45404, 1, 1, 1907, 301, 0, 0, '', 0, 0),
(5300015, 2, 0, 'Priest', 45405, 1, 1, 1908, 302, 0, 0, '', 0, 0),
(5300015, 3, 0, 'Shaman', 45410, 1, 1, 1909, 303, 0, 0, '', 0, 0),
(5300015, 4, 0, 'Rogue', 45406, 1, 1, 1910, 304, 0, 0, '', 0, 0),
(5300015, 5, 0, 'Warlock', 45407, 1, 1, 1911, 305, 0, 0, '', 0, 0),
(5300015, 6, 0, 'Warrior', 45408, 1, 1, 1912, 306, 0, 0, '', 0, 0),
(5300015, 7, 0, 'Paladin', 48028, 1, 1, 8644, 303, 0, 0, '', 0, 0),
(5300015, 9, 0, 'Death Knight', 0, 1, 1, 5300006, 1011, 0, 0, '', 0, 0);

UPDATE `gossip_menu_option` SET `ActionMenuID` = 5300015 WHERE `MenuID` = 1951 AND `OptionID` = 12;

-- Undercity Guardian: "A class trainer" (2849, 12) opens 5300016, a copy of 2848 plus Paladin -> 8165 / POI 330.
DELETE FROM `gossip_menu` WHERE `MenuID` = 5300016;
INSERT INTO `gossip_menu` (`MenuID`, `TextID`) VALUES
(5300016, 3542);

DELETE FROM `gossip_menu_option` WHERE `MenuID` = 5300016;
INSERT INTO `gossip_menu_option` (`MenuID`, `OptionID`, `OptionIcon`, `OptionText`, `OptionBroadcastTextID`,
    `OptionType`, `OptionNpcFlag`, `ActionMenuID`, `ActionPoiID`, `BoxCoded`, `BoxMoney`, `BoxText`,
    `BoxBroadcastTextID`, `VerifiedBuild`) VALUES
(5300016, 0, 0, 'Mage', 45404, 1, 1, 2821, 331, 0, 0, '', 0, 0),
(5300016, 1, 0, 'Paladin', 48028, 1, 1, 8165, 330, 0, 0, '', 0, 0),
(5300016, 2, 0, 'Priest', 45405, 1, 1, 2829, 332, 0, 0, '', 0, 0),
(5300016, 3, 0, 'Rogue', 45406, 1, 1, 2830, 333, 0, 0, '', 0, 0),
(5300016, 4, 0, 'Warlock', 45407, 1, 1, 2832, 334, 0, 0, '', 0, 0),
(5300016, 5, 0, 'Warrior', 45408, 1, 1, 2833, 335, 0, 0, '', 0, 0),
(5300016, 9, 0, 'Death Knight', 0, 1, 1, 5300010, 1015, 0, 0, '', 0, 0);

UPDATE `gossip_menu_option` SET `ActionMenuID` = 5300016 WHERE `MenuID` = 2849 AND `OptionID` = 12;
