-- Three level-bracket training dummies for spell-damage testing (docs/single-rank-spell-system.md),
-- alongside the existing entry 900000 (level 83) -- see rev_1787529689976088420.sql for the original
-- "how does an attackable dummy even work" writeup (faction 31 Critter trick, npc_training_dummy AI
-- zeroing HP loss after the damage number is logged, etc.); this migration just clones that same
-- pattern at three more levels.
--
-- Content is locked at level 60 for a while, so testing against the level-83 dummy alone puts every
-- cast through the level-gap partial-resist penalty in Unit::GetEffectiveResistChance (Unit.cpp) --
-- real damage numbers come out well under tooltip and are not representative of live play. These
-- three sit at 60/70/80 so damage can be checked at-level (no artificial resist from the gap) at
-- today's cap and at the two future brackets.
--
-- Guids 5300683-5300685: next three after the existing dummy's 5300682 (MAX(guid) in the live DB at
-- write time). Same 0xFFFFFF cap note applies (ObjectMgr::GenerateCreatureSpawnId) -- keep well
-- under 16,777,215.

REPLACE INTO `creature_template`
    (`entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`, `KillCredit1`, `KillCredit2`,
     `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`, `faction`, `npcflag`,
     `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`, `dmgschool`,
     `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`, `unit_class`,
     `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`, `pickpocketloot`,
     `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`, `HoverHeight`,
     `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`, `movementId`,
     `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`, `VerifiedBuild`)
VALUES
    (900001, 0, 0, 0, 0, 0,
     'Training Dummy', 'Level 60', '', 0, 60, 60, 0, 31, 0,
     1, 1.14286, 1, 1, 20, 3, 0,
     35, 2000, 2000, 1, 1, 1,
     0, 2048, 0, 0, 9, 4, 0, 0,
     0, 0, 0, 0, 0, '', 0, 1,
     23809.5, 1, 1, 1, 0, 0,
     1, -26, 262144, 'npc_training_dummy', NULL),
    (900002, 0, 0, 0, 0, 0,
     'Training Dummy', 'Level 70', '', 0, 70, 70, 0, 31, 0,
     1, 1.14286, 1, 1, 20, 3, 0,
     35, 2000, 2000, 1, 1, 1,
     0, 2048, 0, 0, 9, 4, 0, 0,
     0, 0, 0, 0, 0, '', 0, 1,
     23809.5, 1, 1, 1, 0, 0,
     1, -26, 262144, 'npc_training_dummy', NULL),
    (900003, 0, 0, 0, 0, 0,
     'Training Dummy', 'Level 80', '', 0, 80, 80, 0, 31, 0,
     1, 1.14286, 1, 1, 20, 3, 0,
     35, 2000, 2000, 1, 1, 1,
     0, 2048, 0, 0, 9, 4, 0, 0,
     0, 0, 0, 0, 0, '', 0, 1,
     23809.5, 1, 1, 1, 0, 0,
     1, -26, 262144, 'npc_training_dummy', NULL);

DELETE FROM `creature_template_model` WHERE `CreatureID` IN (900001, 900002, 900003);
INSERT INTO `creature_template_model`
    (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`)
VALUES
    (900001, 0, 3019, 1, 1, NULL),
    (900002, 0, 3019, 1, 1, NULL),
    (900003, 0, 3019, 1, 1, NULL);

-- Spread out around the same Stormwind spot (no longer lined up 3 yards apart -- each one has its
-- own hand-picked position so they don't overlap).
DELETE FROM `creature` WHERE `guid` IN (5300683, 5300684, 5300685);
INSERT INTO `creature`
    (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
     `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `wander_distance`,
     `currentwaypoint`, `curhealth`, `curmana`, `MovementType`, `npcflag`, `unit_flags`, `dynamicflags`,
     `ScriptName`, `VerifiedBuild`, `CreateObject`, `Comment`)
VALUES
    (5300683, 900001, 0, 1519, 1519, 1, 1, 0,
     -8904, 503, 93.8, 0, 120, 0,
     0, 1, 0, 0, 0, 0, 0,
     '', NULL, 0, 'Level 60 training dummy for spell-damage testing'),
    (5300684, 900002, 0, 1519, 1519, 1, 1, 0,
     -8914, 490, 93.8, 0, 120, 0,
     0, 1, 0, 0, 0, 0, 0,
     '', NULL, 0, 'Level 70 training dummy for spell-damage testing'),
    (5300685, 900003, 0, 1519, 1519, 1, 1, 0,
     -8932, 485, 93.8, 0, 120, 0,
     0, 1, 0, 0, 0, 0, 0,
     '', NULL, 0, 'Level 80 training dummy for spell-damage testing');
