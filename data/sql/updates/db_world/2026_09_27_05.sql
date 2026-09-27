-- DB update 2026_09_27_04 -> 2026_09_27_05
-- Healing Training Dummy combat variant fixes.
-- 1) Anchor 900014: drop CREATURE_FLAG_EXTRA_TRIGGER (flags_extra 130 -> 2, CIVILIAN only).
--    NullCreatureAI's constructor calls SetIsCombatDisallowed(true) on every trigger creature
--    (src/server/game/AI/CoreAI/PassiveAI.cpp), so CombatManager::CanBeginCombat refused every
--    anchor<->healer combat and healing 900013 never put anyone in combat. The anchor stays
--    unselectable/unattackable via its own unit_flags and invisible via model 11686.
UPDATE `creature_template` SET `flags_extra` = 2 WHERE `entry` = 900014;

-- 2) Replace the plain 900011 Stormwind spawn with 900013 at the same spot (reusing guid 5300686),
--    and drop the ad-hoc `.npc add 900013` spawn (guid 5300701) placed next to it.
DELETE FROM `creature` WHERE `guid` = 5300686 AND `id` = 900011;
DELETE FROM `creature` WHERE `guid` = 5300701 AND `id` = 900013;
DELETE FROM `creature` WHERE `guid` = 5300686 AND `id` = 900013;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`, `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `wander_distance`, `currentwaypoint`, `curhealth`, `curmana`, `MovementType`, `npcflag`, `unit_flags`, `dynamicflags`, `ScriptName`, `VerifiedBuild`, `CreateObject`, `Comment`) VALUES
(5300686, 900013, 0, 1519, 1519, 1, 1, 0, -8903.93, 514.433, 93.8378, 3.7279, 120, 0, 0, 1, 0, 0, 0, 0, 0, '', 0, 0, 'Healing Training Dummy (combat variant) - permanent Stormwind spawn');
