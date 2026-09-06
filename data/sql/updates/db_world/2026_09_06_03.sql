-- Add Death Knight class trainers in Stormwind and Orgrimmar, reachable without going through
-- Ebon Hold.
--
-- Reuses creature_template 33251 ("Death Knight Trainer and Runeforge") -- it exists in the base
-- data but was never actually wired up: npcflag was 0 (no Gossip/Trainer/TrainerClass bits) and it
-- has zero spawns anywhere in the game, so it has never functioned as a trainer. TrainerId 13 is
-- the Death Knight class trainer record (trainer.Requirement = 6) and already carries a full
-- ReqLevel-gated rank curve in trainer_spell, but no creature_default_trainer row ever pointed a
-- creature at it either. See docs/bugs-and-fixes.md.
--
-- Fixing the template's npcflag makes every future spawn of 33251 (including one added later in
-- Ebon Hold) a working trainer; there's no existing Ebon Hold spawn today for this to disturb.
UPDATE `creature_template` SET `npcflag` = 49 WHERE `entry` = 33251 AND `npcflag` = 0;

-- UNIT_NPC_FLAG_GOSSIP (1) | UNIT_NPC_FLAG_TRAINER (16) | UNIT_NPC_FLAG_TRAINER_CLASS (32) = 49,
-- matching the flag combination used by every other class trainer (e.g. Warrior Trainer, entry 911).

DELETE FROM `creature_default_trainer` WHERE `CreatureId` = 33251;
INSERT INTO `creature_default_trainer` (`CreatureId`, `TrainerId`) VALUES
(33251, 13);

-- Stormwind + Orgrimmar spawns. guids 5300679-5300680 are the base db_world AUTO_INCREMENT value
-- (data/sql/base/db_world/creature.sql) and the one after it; neither is referenced by any other
-- update, so both are free.
DELETE FROM `creature` WHERE `guid` IN (5300679, 5300680);
INSERT INTO `creature`
    (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
     `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`,
     `VerifiedBuild`, `CreateObject`, `Comment`)
VALUES
    (5300679, 33251, 0, 1519, 1519, 1, 1, 0,
     -8704.72, 304.28, 93.35, 1.3, 300, 0,
     12340, 1, 'Death Knight Trainer - Stormwind (early DK access)'),
    (5300680, 33251, 1, 1637, 1637, 1, 1, 0,
     1846.54, -4325.67, -15.37, 3.8, 300, 0,
     12340, 1, 'Death Knight Trainer - Orgrimmar (early DK access)');
