-- Jewelcrafting trainers in Stormwind and Orgrimmar (user 2026-11-11). 3.3.5 only trains Jewelcrafting in Silvermoon,
-- Exodar, Outland and Northrend; Cataclysm added Theresa Denman (Stormwind) and Lugrah (Orgrimmar), placed here on the
-- user's chosen spots. Both teach the stock Jewelcrafting Trainer list (trainer 113, the Silvermoon/Exodar one: up
-- to Artisan, which covers the profession cap of 300). The Cataclysm models are not in the 3.3.5 client, so they
-- wear stock ones from trainers behind the closed Outland gate: Tatiana (18774, Honor Hold Jewelcrafting) and
-- Neferatti (30722).
-- The Stormwind and Orgrimmar guards' Profession Trainer menus gain Jewelcrafting in alphabetical place (the stock
-- Leatherworking..Tailoring options move down one OptionID, values unchanged), with a map marker on each trainer.
-- Ids: creature 900023-900024 (npc_tools block, hand-written like 900010/900012; 900018-900022 are claimed by the
-- unmerged fix-sw-shaman-trainer-progression branch), guids 5300739-5300740 (next free in the hand-SQL block after
-- the Haunted quartermasters), gossip menus 5300020-5300021, npc_text 900027-900028, points_of_interest 1020-1021.
-- Checked unused 2026-11-11 against the live DB, every pending file in the shared checkout and worktrees, and every
-- remote branch.

-- Theresa Denman (Stormwind) and Lugrah (Orgrimmar): Catarina Stanford's template (30713) with a new name, title
-- and faction (Lugrah: 29, Orgrimmar).
INSERT INTO `creature_template` (`entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`,
    `KillCredit1`, `KillCredit2`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`,
    `faction`, `npcflag`, `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`,
    `dmgschool`, `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`, `unit_class`,
    `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`, `pickpocketloot`, `skinloot`,
    `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`, `HoverHeight`, `HealthModifier`,
    `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`, `movementId`, `RegenHealth`,
    `CreatureImmunitiesId`, `flags_extra`, `ScriptName`, `VerifiedBuild`) VALUES
(900023, 0, 0, 0, 0, 0, 'Theresa Denman', 'Jewelcrafting Trainer', '', 0, 35, 35, 0, 12, 80, 1, 1.14286, 1, 1, 20, 0, 0,
    1, 2000, 2000, 1, 1, 8, 32768, 2048, 0, 0, 7, 4096, 0, 0, 0, 0, 0, 0, 0, '', 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, '', 0)
    ON DUPLICATE KEY UPDATE
    `difficulty_entry_1` = VALUES(`difficulty_entry_1`), `difficulty_entry_2` = VALUES(`difficulty_entry_2`),
    `difficulty_entry_3` = VALUES(`difficulty_entry_3`), `KillCredit1` = VALUES(`KillCredit1`),
    `KillCredit2` = VALUES(`KillCredit2`), `name` = VALUES(`name`), `subname` = VALUES(`subname`),
    `IconName` = VALUES(`IconName`), `gossip_menu_id` = VALUES(`gossip_menu_id`), `minlevel` = VALUES(`minlevel`),
    `maxlevel` = VALUES(`maxlevel`), `exp` = VALUES(`exp`), `faction` = VALUES(`faction`),
    `npcflag` = VALUES(`npcflag`), `speed_walk` = VALUES(`speed_walk`), `speed_run` = VALUES(`speed_run`),
    `speed_swim` = VALUES(`speed_swim`), `speed_flight` = VALUES(`speed_flight`),
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
INSERT INTO `creature_template` (`entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`,
    `KillCredit1`, `KillCredit2`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`,
    `faction`, `npcflag`, `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`,
    `dmgschool`, `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`, `unit_class`,
    `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`, `pickpocketloot`, `skinloot`,
    `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`, `HoverHeight`, `HealthModifier`,
    `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`, `movementId`, `RegenHealth`,
    `CreatureImmunitiesId`, `flags_extra`, `ScriptName`, `VerifiedBuild`) VALUES
(900024, 0, 0, 0, 0, 0, 'Lugrah', 'Jewelcrafting Trainer', '', 0, 35, 35, 0, 29, 80, 1, 1.14286, 1, 1, 20, 0, 0, 1,
    2000, 2000, 1, 1, 8, 32768, 2048, 0, 0, 7, 4096, 0, 0, 0, 0, 0, 0, 0, '', 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, '', 0)
    ON DUPLICATE KEY UPDATE
    `difficulty_entry_1` = VALUES(`difficulty_entry_1`), `difficulty_entry_2` = VALUES(`difficulty_entry_2`),
    `difficulty_entry_3` = VALUES(`difficulty_entry_3`), `KillCredit1` = VALUES(`KillCredit1`),
    `KillCredit2` = VALUES(`KillCredit2`), `name` = VALUES(`name`), `subname` = VALUES(`subname`),
    `IconName` = VALUES(`IconName`), `gossip_menu_id` = VALUES(`gossip_menu_id`), `minlevel` = VALUES(`minlevel`),
    `maxlevel` = VALUES(`maxlevel`), `exp` = VALUES(`exp`), `faction` = VALUES(`faction`),
    `npcflag` = VALUES(`npcflag`), `speed_walk` = VALUES(`speed_walk`), `speed_run` = VALUES(`speed_run`),
    `speed_swim` = VALUES(`speed_swim`), `speed_flight` = VALUES(`speed_flight`),
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
DELETE FROM `creature_template_model` WHERE `CreatureID` IN (900023, 900024);
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`,
    `VerifiedBuild`) VALUES
(900023, 0, 18173, 1, 1, 0),
(900024, 0, 27285, 1, 1, 0);
DELETE FROM `creature_default_trainer` WHERE `CreatureId` IN (900023, 900024);
INSERT INTO `creature_default_trainer` (`CreatureId`, `TrainerId`) VALUES
(900023, 113),
(900024, 113);

-- Spawns on the user's .gps spots.
DELETE FROM `creature` WHERE `id` IN (900023, 900024) AND `guid` IN (5300739, 5300740);
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`, `position_x`,
    `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`, `CreateObject`,
    `Comment`) VALUES
(5300739, 900023, 0, 0, 0, 1, 1, 0, -8717.277, 604.5082, 101.071884, 5.781767, 300, 0, 0, 1, 'Theresa Denman'),
(5300740, 900024, 1, 0, 0, 1, 1, 0, 1778.3109, -4503.0903, 27.745693, 3.9607036, 300, 0, 0, 1, 'Lugrah');

-- Guard directions: text (text0_1 only, like stock 9346, the Silvermoon one), map marker, and the option.
DELETE FROM `npc_text` WHERE `ID` IN (900027, 900028);
INSERT INTO `npc_text` (`ID`, `text0_1`, `BroadcastTextID0`, `lang0`, `Probability0`) VALUES
(900027, 'Theresa Denman teaches jewelcrafting here in Stormwind. I''ve marked her shop on your map.', 0, 0, 1),
(900028, 'Lugrah teaches jewelcrafting here in Orgrimmar. I''ve marked her shop on your map.', 0, 0, 1);
DELETE FROM `points_of_interest` WHERE `ID` IN (1020, 1021);
INSERT INTO `points_of_interest` (`ID`, `PositionX`, `PositionY`, `Icon`, `Flags`, `Importance`, `Name`) VALUES
(1020, -8717.277, 604.5082, 7, 99, 0, 'Stormwind Jewelcrafting'),
(1021, 1778.3109, -4503.0903, 7, 99, 0, 'Orgrimmar Jewelcrafting');
DELETE FROM `gossip_menu` WHERE `MenuID` IN (5300020, 5300021);
INSERT INTO `gossip_menu` (`MenuID`, `TextID`) VALUES
(5300020, 900027),
(5300021, 900028);
-- Stormwind City Guard (421) and Orgrimmar Grunt (1942) Profession Trainer menus, options 9-13.
DELETE FROM `gossip_menu_option` WHERE `MenuID` IN (421, 1942) AND `OptionID` BETWEEN 9 AND 13;
INSERT INTO `gossip_menu_option` (`MenuID`, `OptionID`, `OptionIcon`, `OptionText`, `OptionBroadcastTextID`,
    `OptionType`, `OptionNpcFlag`, `ActionMenuID`, `ActionPoiID`, `BoxCoded`, `BoxMoney`, `BoxText`,
    `BoxBroadcastTextID`, `VerifiedBuild`) VALUES
(421, 9, 0, 'Jewelcrafting', 45758, 1, 1, 5300020, 1020, 0, 0, '', 0, 0),
(421, 10, 0, 'Leatherworking', 52071, 1, 1, 428, 47, 0, 0, '', 0, 0),
(421, 11, 0, 'Mining', 51348, 1, 1, 430, 48, 0, 0, '', 0, 0),
(421, 12, 0, 'Skinning', 52076, 1, 1, 431, 47, 0, 0, '', 0, 0),
(421, 13, 0, 'Tailoring', 52077, 1, 1, 432, 49, 0, 0, '', 0, 0),
(1942, 9, 0, 'Jewelcrafting', 45758, 1, 1, 5300021, 1021, 0, 0, '', 0, 0),
(1942, 10, 0, 'Leatherworking', 52071, 1, 1, 1866, 316, 0, 0, '', 0, 0),
(1942, 11, 0, 'Mining', 51348, 1, 1, 1868, 315, 0, 0, '', 0, 0),
(1942, 12, 0, 'Skinning', 52076, 1, 1, 1869, 316, 0, 0, '', 0, 0),
(1942, 13, 0, 'Tailoring', 52077, 1, 1, 1871, 317, 0, 0, '', 0, 0);
