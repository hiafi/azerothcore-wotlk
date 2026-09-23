-- Custom: Bear Form appearance NPC (docs/bear-form-appearances.md). Gossip-only, friendly to
-- everyone, script npc_bear_appearance (src/server/scripts/Custom/custom_shapeshift_appearance.cpp).
REPLACE INTO `creature_template` (`entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`,
    `KillCredit1`, `KillCredit2`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`,
    `faction`, `npcflag`, `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`,
    `dmgschool`, `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`,
    `unit_class`, `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`,
    `pickpocketloot`, `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`,
    `HoverHeight`, `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`,
    `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`, `VerifiedBuild`)
VALUES (900012, 0, 0, 0, 0, 0, 'Ursana Thornhide', 'Bear Form Appearances', NULL, 0, 80, 80, 2, 35, 1, 1, 1.14286,
    1, 1, 20, 0, 0, 1, 2000, 2000, 1, 1, 1, 768, 2048, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, '', 0, 1, 1, 1, 1, 1, 0, 0,
    1, 0, 2, 'npc_bear_appearance', NULL);

-- Rabine Saturna's model (Night Elf druid, Nighthaven)
DELETE FROM `creature_template_model` WHERE `CreatureID` = 900012;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`,
    `VerifiedBuild`)
VALUES (900012, 0, 11768, 1, 1, NULL);

DELETE FROM `npc_text` WHERE `ID` = 900012;
INSERT INTO `npc_text` (`ID`, `text0_0`, `text0_1`, `Probability0`)
VALUES (900012, 'Ursoc wears many coats, and so may you. Choose the shape your bear form will take.$B$BIf you speak to me while already shifted, you will see each choice as you make it.',
    'Ursoc wears many coats, and so may you. Choose the shape your bear form will take.$B$BIf you speak to me while already shifted, you will see each choice as you make it.', 1);

-- One spawn in Stormwind City (spot picked in-game by the user)
DELETE FROM `creature` WHERE `id` = 900012 AND `guid` = 5300700;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `wander_distance`, `currentwaypoint`,
    `curhealth`, `curmana`, `MovementType`, `npcflag`, `unit_flags`, `dynamicflags`, `ScriptName`, `VerifiedBuild`,
    `CreateObject`, `Comment`)
VALUES (5300700, 900012, 0, 1519, 1519, 1, 1, 0, -8765.475, 1135.0663, 92.52016, 5.7693214, 300, 0, 0, 100, 0, 0,
    0, 0, 0, '', 0, 0, 'Bear Form appearance NPC');
