--
-- mod-dpssim: extends the sim-exclusive, no-combat-timeout training dummy (see
-- rev_1789352973840118160.sql's entry 900004 for the level-60 bracket and its own doc comment for
-- the full rationale) to the level-70 and level-80 brackets: entries 900005 and 900006, copied from
-- 900002/900003 respectively (data/sql/updates/db_world/2026_09_01_26.sql) except for ScriptName,
-- which points at npc_dpssim_training_dummy (modules/mod-dpssim/src/SimDummyAI.cpp) instead of the
-- shared npc_training_dummy every real player-facing dummy uses.
--
-- 900004 alone was validated first (a full stat-weights batch - 10 container boots, 0 zero-cast
-- failures, see docs/bugs-and-fixes.md) before extending the fix to these two brackets, per plan.
-- Same reasoning as 900004 for why these are new entries rather than edits to 900002/900003
-- themselves: those two are real, permanently world-spawned dummies real players use for testing
-- too (2026_09_01_26.sql's own `creature` INSERT, guids 5300684/5300685) - changing their AI would
-- change live player-facing behavior, not just this sim's. Like 900004, 900005/900006 have no
-- `creature` spawn row - SimTarget::Create() only ever summons them dynamically.
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
    (900005, 0, 0, 0, 0, 0,
     'Training Dummy (dpssim)', 'Level 70', '', 0, 70, 70, 0, 31, 0,
     1, 1.14286, 1, 1, 20, 3, 0,
     35, 2000, 2000, 1, 1, 1,
     0, 2048, 0, 0, 9, 4, 0, 0,
     0, 0, 0, 0, 0, '', 0, 1,
     23809.5, 1, 1, 1, 0, 0,
     1, -26, 262144, 'npc_dpssim_training_dummy', NULL),
    (900006, 0, 0, 0, 0, 0,
     'Training Dummy (dpssim)', 'Level 80', '', 0, 80, 80, 0, 31, 0,
     1, 1.14286, 1, 1, 20, 3, 0,
     35, 2000, 2000, 1, 1, 1,
     0, 2048, 0, 0, 9, 4, 0, 0,
     0, 0, 0, 0, 0, '', 0, 1,
     23809.5, 1, 1, 1, 0, 0,
     1, -26, 262144, 'npc_dpssim_training_dummy', NULL);

DELETE FROM `creature_template_model` WHERE `CreatureID` IN (900005, 900006);
INSERT INTO `creature_template_model`
    (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`)
VALUES
    (900005, 0, 3019, 1, 1, NULL),
    (900006, 0, 3019, 1, 1, NULL);
