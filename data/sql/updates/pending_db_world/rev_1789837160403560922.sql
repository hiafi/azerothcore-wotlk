-- Healing target dummy for playtest support (companion to the existing damage-testing dummies at
-- entries 900001-900006, cloned from 900001's own row - see data/sql/updates/db_world/ for that
-- migration's own notes). Unlike npc_training_dummy (900001-900006's ScriptName), this dummy has
-- no damage-suppression: real heal numbers land, and a small dedicated AI (npc_healing_dummy,
-- src/server/scripts/Custom/custom_healing_dummy.cpp) pins it at 30% of max health - set on spawn
-- and re-forced every 1 sec regardless of what happened to it in between - so a healer gets a real
-- combat-log heal/overheal number, then the dummy is ready for the next rep with no manual
-- re-damaging needed.
--
-- Changes from the 900001 template this is cloned from, all user-requested (2026-09-19, follow-up
-- to the dummy's initial add):
--   - faction 31 (Critter/neutral) -> 35 (friendly-to-everyone, same convention
--     spell_mage.cpp's npc_mage_frozen_orb::IsSummonedBy comment calls out for this exact meaning)
--     - self-serve damage-then-heal is no longer the design (the AI's own periodic reset replaces
--     it), so there's no more reason to keep it attackable-by-harmful-spells; friendly is both more
--     correct for a "stands there and gets healed" training aid and avoids it being swept up by
--     AoE damage/threat unintentionally.
--   - type_flags 4 -> 4100 (adds CREATURE_TYPE_FLAG_CAN_ASSIST = 0x1000, SharedDefines.h:2701,
--     "original description: Player Can Heal/Buff" per its ProcFlags-style comment at line 2790) -
--     this is the actual gate Unit::_IsValidAssistTarget's "PvC case" branch checks (Unit.cpp
--     ~line 11085): a player can only heal/buff a creature target if it's PLAYER_CONTROLLED,
--     flagged CAN_ASSIST, flagged TREAT_AS_RAID_UNIT, or already PvP-flagged - a plain friendly
--     creature (even at reaction FRIENDLY) still fails that check and can't be healed at all
--     without this flag; the earlier friend/foe gate being satisfied is necessary but not
--     sufficient on its own.
--   - RegenHealth 1 -> 0 - the AI now owns keeping it at 30% every second; disabling passive
--     natural regen avoids that ticking HP up slightly between the AI's own reset windows.
--   - ScriptName '' -> 'npc_healing_dummy' (the new AI described above).
--   - **type 9 (Mechanical) -> 7 (Humanoid)** - bug, not a stylistic choice: 900001 is Mechanical
--     because it's a lifeless prop, and `Creature::IsImmunedToSpellEffect` (Creature.cpp ~line
--     2322) hardcodes `type == CREATURE_TYPE_MECHANICAL && Effect == SPELL_EFFECT_HEAL` as an
--     unconditional immunity - no `CAN_ASSIST`/faction combination can override this, it's checked
--     at effect-application time, after targeting already succeeded. This is why the dummy reported
--     as "immune to healing" despite the CAN_ASSIST fix above. Humanoid carries no such immunity.
--   - **rank 3 (CREATURE_ELITE_WORLDBOSS) -> 0 (CREATURE_ELITE_NORMAL)** - also a bug: rank 3 is
--     what actually drives the client's gold "Boss" health-bar/nameplate styling
--     (`CreatureEliteType`, SharedDefines.h ~line 2967), not a difficulty knob that happened to look
--     wrong - inherited unexamined from 900001 along with `type`, same root cause (cloned a
--     damage-dummy row without reconsidering every field for a healing dummy's very different job).
-- level bumped to 80 (900001 is a fixed level 60) for max-level spellpower-scaling relevance;
-- HealthModifier kept identical to 900001's own (23809.5) - the level bump alone already gives it
-- more total HP than the level-60 damage dummy, appropriate for meaningful heal-crit/overheal
-- numbers at 30% of a large pool.
-- No DELETE here - creature_template is on this repo's SQL linter's do-not-delete list
-- (apps/codestyle/codestyle-sql.py's `not_delete`), matching every other creature_template edit in
-- this project's pending migrations.
INSERT INTO `creature_template` (`entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`, `KillCredit1`, `KillCredit2`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`, `faction`, `npcflag`, `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`, `dmgschool`, `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`, `unit_class`, `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`, `pickpocketloot`, `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`, `HoverHeight`, `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`, `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`, `VerifiedBuild`) VALUES
(900011, 0, 0, 0, 0, 0, 'Healing Training Dummy', 'Level 80', '', 0, 80, 80, 0, 35, 0, 1, 1.14286, 1, 1, 20, 0, 0, 35, 2000, 2000, 1, 1, 1, 0, 2048, 0, 0, 7, 4100, 0, 0, 0, 0, 0, 0, 0, '', 0, 1, 23809.5, 1, 1, 1, 0, 0, 0, -26, 262144, 'npc_healing_dummy', 0) ON DUPLICATE KEY UPDATE `difficulty_entry_1` = VALUES(`difficulty_entry_1`), `difficulty_entry_2` = VALUES(`difficulty_entry_2`), `difficulty_entry_3` = VALUES(`difficulty_entry_3`), `KillCredit1` = VALUES(`KillCredit1`), `KillCredit2` = VALUES(`KillCredit2`), `name` = VALUES(`name`), `subname` = VALUES(`subname`), `IconName` = VALUES(`IconName`), `gossip_menu_id` = VALUES(`gossip_menu_id`), `minlevel` = VALUES(`minlevel`), `maxlevel` = VALUES(`maxlevel`), `exp` = VALUES(`exp`), `faction` = VALUES(`faction`), `npcflag` = VALUES(`npcflag`), `speed_walk` = VALUES(`speed_walk`), `speed_run` = VALUES(`speed_run`), `speed_swim` = VALUES(`speed_swim`), `speed_flight` = VALUES(`speed_flight`), `detection_range` = VALUES(`detection_range`), `rank` = VALUES(`rank`), `dmgschool` = VALUES(`dmgschool`), `DamageModifier` = VALUES(`DamageModifier`), `BaseAttackTime` = VALUES(`BaseAttackTime`), `RangeAttackTime` = VALUES(`RangeAttackTime`), `BaseVariance` = VALUES(`BaseVariance`), `RangeVariance` = VALUES(`RangeVariance`), `unit_class` = VALUES(`unit_class`), `unit_flags` = VALUES(`unit_flags`), `unit_flags2` = VALUES(`unit_flags2`), `dynamicflags` = VALUES(`dynamicflags`), `family` = VALUES(`family`), `type` = VALUES(`type`), `type_flags` = VALUES(`type_flags`), `lootid` = VALUES(`lootid`), `pickpocketloot` = VALUES(`pickpocketloot`), `skinloot` = VALUES(`skinloot`), `PetSpellDataId` = VALUES(`PetSpellDataId`), `VehicleId` = VALUES(`VehicleId`), `mingold` = VALUES(`mingold`), `maxgold` = VALUES(`maxgold`), `AIName` = VALUES(`AIName`), `MovementType` = VALUES(`MovementType`), `HoverHeight` = VALUES(`HoverHeight`), `HealthModifier` = VALUES(`HealthModifier`), `ManaModifier` = VALUES(`ManaModifier`), `ArmorModifier` = VALUES(`ArmorModifier`), `ExperienceModifier` = VALUES(`ExperienceModifier`), `RacialLeader` = VALUES(`RacialLeader`), `movementId` = VALUES(`movementId`), `RegenHealth` = VALUES(`RegenHealth`), `CreatureImmunitiesId` = VALUES(`CreatureImmunitiesId`), `flags_extra` = VALUES(`flags_extra`), `ScriptName` = VALUES(`ScriptName`), `VerifiedBuild` = VALUES(`VerifiedBuild`);

DELETE FROM `creature_template_model` WHERE `CreatureID` = 900011;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`) VALUES
(900011, 0, 3019, 1, 1, 0);

-- Permanent Stormwind spawn, same convention as 900001-900003's own spawns (data/sql/updates/
-- db_world/, guids 5300683-5300685, same map/zone/area). guid 5300686 already exists live in this
-- box's own DB - it was auto-created by `.npc add 900011` (a real permanent spawn insert, not a
-- temp summon) at this exact location during playtesting - this migration just commits that same
-- guid's row to source control (with zoneId/areaId/spawntimesecs normalized to match its siblings)
-- so a fresh DB import gets the same permanent spawn.
DELETE FROM `creature` WHERE `guid` = 5300686;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`, `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `wander_distance`, `currentwaypoint`, `curhealth`, `curmana`, `MovementType`, `npcflag`, `unit_flags`, `dynamicflags`, `ScriptName`, `VerifiedBuild`, `CreateObject`, `Comment`) VALUES
(5300686, 900011, 0, 1519, 1519, 1, 1, 0, -8903.935, 514.4332, 93.83776, 3.727901, 120, 0, 0, 1, 0, 0, 0, 0, 0, '', 0, 0, 'Healing Training Dummy - permanent Stormwind spawn');
