-- Custom hostile training dummy for spell-damage testing (docs/single-rank-spell-system.md).
--
-- Base entry 30527 ("Training Dummy", npc_training_dummy AI) has faction = 35 (friendly), which
-- makes it un-attackable with harmful spells -- it shows up as an allied unit instead of a hostile
-- one. Rather than patch the base entry, clone it into a new custom entry (900000) with
-- faction = 31 -- the "Critter" faction used by Chicken/Rabbit/Squirrel (creature_template).
-- Reaction to players is exactly Neutral, which is the trick: Unit::_IsValidAttackTarget only
-- blocks a harmful-spell target when the reaction is *above* Neutral, so it stays fully
-- attackable -- while city guards (which only aggro what's hostile to their own faction) leave it
-- alone. faction = 14 (Monster, hostile to both factions) was tried first and works for spell
-- targeting too, but guards in Stormwind treat it as a hostile intruder and attack it on sight.
-- Everything else is copied verbatim from 30527: rank 3 (worldboss, so
-- boss-only trinket/proc rules apply like a real dummy), HealthModifier left absurdly high, and
-- the npc_training_dummy AI, which zeroes the actual HP loss in DamageTaken() *after* the damage
-- number is already computed/logged (see Unit.cpp DealDamage, Xinef's comment) -- so it never
-- dies but real spell-damage numbers still show in the combat log.
--
-- Spawned once, permanently, in Stormwind (zone/area 1519) at the reporter's chosen spot.
-- Guid 5300682 is a fixed value one past the live DB's MAX(guid) at the time this was written.
-- NOTE: creature spawn guids are capped at 0xFFFFFF (ObjectMgr::GenerateCreatureSpawnId,
-- _creatureSpawnId >= 0xFFFFFF) -- a guid above that (e.g. an "obviously out of range" value like
-- 90000000) makes worldserver refuse to start at all ("Creature spawn id overflow") the moment it
-- computes MAX(guid)+1 on boot. Learned the hard way; keep any future custom spawn guid well under
-- 16,777,215 and clear of whatever MAX(guid) actually is at apply time.

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
    (900000, 0, 0, 0, 0, 0,
     'Training Dummy', '', '', 0, 83, 83, 0, 31, 0,
     1, 1.14286, 1, 1, 20, 3, 0,
     35, 2000, 2000, 1, 1, 1,
     0, 2048, 0, 0, 9, 4, 0, 0,
     0, 0, 0, 0, 0, '', 0, 1,
     23809.5, 1, 1, 1, 0, 0,
     1, -26, 262144, 'npc_training_dummy', NULL);

-- Model is a separate table from creature_template in this schema (creature_template_model) --
-- missing this entirely means Creature::Create() can't resolve a display model and silently
-- fails (blocks both .npc add and the DB spawn from ever rendering). Reuse 30527's own model
-- (CreatureDisplayID 3019) verbatim.
DELETE FROM `creature_template_model` WHERE `CreatureID` = 900000;
INSERT INTO `creature_template_model`
    (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`)
VALUES
    (900000, 0, 3019, 1, 1, NULL);

DELETE FROM `creature` WHERE `guid` = 5300682;
INSERT INTO `creature`
    (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
     `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `wander_distance`,
     `currentwaypoint`, `curhealth`, `curmana`, `MovementType`, `npcflag`, `unit_flags`, `dynamicflags`,
     `ScriptName`, `VerifiedBuild`, `CreateObject`, `Comment`)
VALUES
    (5300682, 900000, 0, 1519, 1519, 1, 1, 0,
     -8904, 500, 93.86, 0, 120, 0,
     0, 1, 0, 0, 0, 0, 0,
     '', NULL, 0, 'Custom hostile training dummy for spell-damage testing');
