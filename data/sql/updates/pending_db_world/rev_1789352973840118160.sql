--
-- mod-dpssim: a new, sim-exclusive level-60 training dummy (entry 900004), copied from the
-- existing player-facing dummy (900001, data/sql/updates/db_world/2026_09_01_26.sql) except for
-- ScriptName - it points at a new script, npc_dpssim_training_dummy (modules/mod-dpssim/src/
-- SimDummyAI.cpp), instead of the shared npc_training_dummy every real player-facing dummy (900001
-- included) uses.
--
-- Why a new entry instead of just changing 900001/900002/900003's own ScriptName: those three are
-- real, in-world-spawned dummies real players use for testing too (data/sql/updates/db_world/
-- 2026_09_01_26.sql's own `creature` INSERT, guids 5300683-5300685, placed in Stormwind) - changing
-- their AI would change live player-facing behavior, not just this sim's. 900004 (and, once this is
-- confirmed working, 900005/900006 for the 70/80 brackets) has no `creature` spawn row at all -
-- SimTarget::Create() only ever summons it dynamically (Map::SummonCreature()), it's never
-- permanently placed in the world the way 900001-900003 are.
--
-- Why a new AI at all: npc_training_dummy (src/server/scripts/World/npcs_special.cpp) tracks a
-- real 5-second no-damage combat timeout per attacker and calls CombatManager::EndCombat() once it
-- expires - correct behavior for a real player who might step away mid-test, but a bad fit for
-- SimDaemon::RunPlayerbotBatch()'s reused-actor-across-iterations design: confirmed via diagnostic
-- logging (see docs/bugs-and-fixes.md's "iteration 1 lands hits, every iteration after it doesn't"
-- entry) that this timeout expiring across an iteration boundary - and, per further failures after
-- SimBot::ReestablishCombatState()'s Unit::SetInCombatWith() fix, apparently also mid-iteration if
-- the bot's own decision latency plus a cast time exceeds 5 simulated seconds - is what actually
-- breaks the bot's combat state. npc_dpssim_training_dummy is the exact same AI minus that timeout
-- entirely (still zeroes all damage taken, so it never dies) - see its own class doc comment.
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
    (900004, 0, 0, 0, 0, 0,
     'Training Dummy (dpssim)', 'Level 60', '', 0, 60, 60, 0, 31, 0,
     1, 1.14286, 1, 1, 20, 3, 0,
     35, 2000, 2000, 1, 1, 1,
     0, 2048, 0, 0, 9, 4, 0, 0,
     0, 0, 0, 0, 0, '', 0, 1,
     23809.5, 1, 1, 1, 0, 0,
     1, -26, 262144, 'npc_dpssim_training_dummy', NULL);

DELETE FROM `creature_template_model` WHERE `CreatureID` = 900004;
INSERT INTO `creature_template_model`
    (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`)
VALUES
    (900004, 0, 3019, 1, 1, NULL);
