-- DB update 2026_09_05_38 -> 2026_09_19_00
-- Mage VFX pass (docs/reworks/fire-mage-meteor-vfx.md): Meteor's falling-meteor visual creature
-- (NPC_MAGE_METEOR_MISSILE, spell_mage.cpp) and Frozen Orb's model swap to the purpose-built
-- Mage_FrostOrb_Orb model (apps/dbc-tools/patch_mage_vfx_models.py mints the matching
-- CreatureModelData/CreatureDisplayInfo rows at 90002/90003 in the client-patch working copy).

-- 300002 - Meteor Missile. Purely cosmetic, never attacked or attacking - same shape as Frozen
-- Orb's own trigger creature (300001), every field copied verbatim from its row except entry/
-- name/ScriptName. flags_extra (66 = CIVILIAN|NO_XP_AT_KILL) deliberately excludes
-- CREATURE_FLAG_EXTRA_TRIGGER (0x80) from the start - Frozen Orb's own history (see
-- npc_mage_frozen_orb's comment in spell_mage.cpp, and this file's own docs/bugs-and-fixes.md
-- CREATURE_FLAG_EXTRA_TRIGGER entry) shows that bit makes a creature invisible to players
-- regardless of a byte-correct model/DBC pipeline - not something to rediscover a second time.
-- INSERT ... ON DUPLICATE KEY UPDATE (not DELETE+INSERT): the codestyle linter flags any DELETE
-- against creature_template, and this project's own precedent for a brand-new custom entry
-- (300001's own row, data/sql/updates/db_world/2026_09_01_01.sql) already used this same upsert
-- shape for exactly that reason - idempotent without ever deleting from this table.
INSERT INTO `creature_template` (`entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`, `KillCredit1`, `KillCredit2`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`, `faction`, `npcflag`, `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`, `dmgschool`, `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`, `unit_class`, `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`, `pickpocketloot`, `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`, `HoverHeight`, `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`, `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`, `VerifiedBuild`) VALUES
(300002, 0, 0, 0, 0, 0, 'Meteor Missile', '', '', 0, 1, 1, 0, 35, 0, 1, 1, 1, 1, 0, 0, 0, 1, 2000, 2000, 1, 1, 1, 33555200, 2048, 0, 0, 10, 1024, 0, 0, 0, 0, 0, 0, 0, '', 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 66, 'npc_mage_meteor_missile', 0) ON DUPLICATE KEY UPDATE `difficulty_entry_1` = VALUES(`difficulty_entry_1`), `difficulty_entry_2` = VALUES(`difficulty_entry_2`), `difficulty_entry_3` = VALUES(`difficulty_entry_3`), `KillCredit1` = VALUES(`KillCredit1`), `KillCredit2` = VALUES(`KillCredit2`), `name` = VALUES(`name`), `subname` = VALUES(`subname`), `IconName` = VALUES(`IconName`), `gossip_menu_id` = VALUES(`gossip_menu_id`), `minlevel` = VALUES(`minlevel`), `maxlevel` = VALUES(`maxlevel`), `exp` = VALUES(`exp`), `faction` = VALUES(`faction`), `npcflag` = VALUES(`npcflag`), `speed_walk` = VALUES(`speed_walk`), `speed_run` = VALUES(`speed_run`), `speed_swim` = VALUES(`speed_swim`), `speed_flight` = VALUES(`speed_flight`), `detection_range` = VALUES(`detection_range`), `rank` = VALUES(`rank`), `dmgschool` = VALUES(`dmgschool`), `DamageModifier` = VALUES(`DamageModifier`), `BaseAttackTime` = VALUES(`BaseAttackTime`), `RangeAttackTime` = VALUES(`RangeAttackTime`), `BaseVariance` = VALUES(`BaseVariance`), `RangeVariance` = VALUES(`RangeVariance`), `unit_class` = VALUES(`unit_class`), `unit_flags` = VALUES(`unit_flags`), `unit_flags2` = VALUES(`unit_flags2`), `dynamicflags` = VALUES(`dynamicflags`), `family` = VALUES(`family`), `type` = VALUES(`type`), `type_flags` = VALUES(`type_flags`), `lootid` = VALUES(`lootid`), `pickpocketloot` = VALUES(`pickpocketloot`), `skinloot` = VALUES(`skinloot`), `PetSpellDataId` = VALUES(`PetSpellDataId`), `VehicleId` = VALUES(`VehicleId`), `mingold` = VALUES(`mingold`), `maxgold` = VALUES(`maxgold`), `AIName` = VALUES(`AIName`), `MovementType` = VALUES(`MovementType`), `HoverHeight` = VALUES(`HoverHeight`), `HealthModifier` = VALUES(`HealthModifier`), `ManaModifier` = VALUES(`ManaModifier`), `ArmorModifier` = VALUES(`ArmorModifier`), `ExperienceModifier` = VALUES(`ExperienceModifier`), `RacialLeader` = VALUES(`RacialLeader`), `movementId` = VALUES(`movementId`), `RegenHealth` = VALUES(`RegenHealth`), `CreatureImmunitiesId` = VALUES(`CreatureImmunitiesId`), `flags_extra` = VALUES(`flags_extra`), `ScriptName` = VALUES(`ScriptName`), `VerifiedBuild` = VALUES(`VerifiedBuild`);

DELETE FROM `creature_template_model` WHERE `CreatureID` = 300002;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`) VALUES
(300002, 0, 90003, 1, 1, 0);

-- Frozen Orb (300001) model swap: the previous custom row (90001, stock Spells\IceNuke_Missile.mdx
-- reused) to the new purpose-built orb model (90002, Spells\Mage_FrostOrb_Orb.mdx) - same shape as
-- the existing 26753->90001 swap in data/sql/updates/db_world/2026_09_01_01.sql.
UPDATE `creature_template_model` SET `CreatureDisplayID` = 90002 WHERE `CreatureID` = 300001 AND `CreatureDisplayID` = 90001;
