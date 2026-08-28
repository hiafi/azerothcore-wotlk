-- Custom QA vendor in Stormwind (Trade District) selling the custom-stat test items:
-- Betrayer's Boots (19897), Seal of the Gurubashi Berserker (22722),
-- Band of Servitude (22721), Cloak of the Hakkari Worshippers (22711).
REPLACE INTO `creature_template` (`entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`,
    `KillCredit1`, `KillCredit2`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`,
    `faction`, `npcflag`, `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`,
    `dmgschool`, `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`,
    `unit_class`, `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`,
    `pickpocketloot`, `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`,
    `HoverHeight`, `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`,
    `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`, `VerifiedBuild`)
VALUES (900010, 0, 0, 0, 0, 0, 'Quinn Testbury', '<QA Item Vendor>', NULL, 0, 1, 1, 0, 12, 128, 1, 1.14286, 1, 1,
    20, 0, 0, 1, 2000, 2000, 1, 1, 1, 512, 2048, 0, 0, 7, 134217728, 0, 0, 0, 0, 0, 0, 0, '', 0, 1, 1, 1, 1, 1, 0,
    0, 1, 0, 2, '', NULL);

DELETE FROM `creature_template_model` WHERE `CreatureID` = 900010;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`,
    `VerifiedBuild`)
VALUES (900010, 0, 1520, 1, 1, NULL);

DELETE FROM `creature` WHERE `guid` = 900010;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `wander_distance`, `currentwaypoint`,
    `curhealth`, `curmana`, `MovementType`, `npcflag`, `unit_flags`, `dynamicflags`, `ScriptName`, `VerifiedBuild`,
    `CreateObject`, `Comment`)
VALUES (900010, 900010, 0, 0, 0, 1, 1, 0, -8718.03, 480.42, 98.81, 0.9, 300, 0, 0, 100, 0, 0, 0, 0, 0, '', 0, 0,
    'QA vendor for custom item stat testing');

DELETE FROM `npc_vendor` WHERE `entry` = 900010;
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`)
VALUES
(900010, 1, 19897, 0, 0, 0, 0),
(900010, 2, 22722, 0, 0, 0, 0),
(900010, 3, 22721, 0, 0, 0, 0),
(900010, 4, 22711, 0, 0, 0, 0);
