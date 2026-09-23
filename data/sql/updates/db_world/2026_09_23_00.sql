-- DB update 2026_09_05_38 -> 2026_09_23_00
-- Priest baseline rework (docs/reworks/priest-new-spells.md) - hand-written world-DB content for
-- two of the new spells (creature_template/creature_template_model/gameobject_template aren't part
-- of apps/dbc-tools' generate.py pipeline, same as Frost Mage's Frozen Orb before this).

-- Divine Star's travelling pulse creature (300100, npc_pri_divine_star in spell_priest_new.cpp),
-- summoned by spell 200133. Same "invisible-stalker trigger creature" template Frozen Orb's own
-- projectile (300001, data/sql/updates/db_world/2026_09_01_01.sql) already established in this
-- repo: unit_flags = NOT_SELECTABLE | IMMUNE_TO_PC | IMMUNE_TO_NPC (33555200). faction=35
-- (friendly-to-everyone) is only the spawn default - npc_pri_divine_star::IsSummonedBy immediately
-- overrides it to the owner's faction, same reason Frozen Orb's own comment gives (a plain trigger
-- left on faction 35 can't find hostile targets for its own pulses). Display 90004 is a real model
-- - CreatureDisplayInfo/CreatureModelData rows minted by apps/dbc-tools/patch_priest_vfx_models.py,
-- wrapping Priest_DivineStar_Missile_Yellow.M2 (mined from the Ascension client backup, see that
-- script's own docstring) - replaces the earlier placeholder (1126, the same stock
-- invisible-stalker model Frozen Orb's own row used before its own art pass).
-- flags_extra = CIVILIAN | NO_XP (66), deliberately NOT including CREATURE_FLAG_EXTRA_TRIGGER
-- (0x80) - live-playtest bug 2026-09-20: this row originally shipped with flags_extra=194
-- (TRIGGER | CIVILIAN | NO_XP), which is exactly docs/bugs-and-fixes.md's
-- `CREATURE_FLAG_EXTRA_TRIGGER` entry (Unit::BuildValuesUpdateForPlayerWithFlag force-overrides
-- UNIT_FIELD_DISPLAYID to the invisible model for every non-GM observer, completely bypassing
-- creature_template_model) - the exact same bug already root-caused and fixed for Frozen Orb
-- (300001) and deliberately avoided for Meteor Missile (300002, data/sql/updates/db_world/
-- 2026_09_19_00.sql) by never including this bit in the first place. Rediscovered a third time
-- here; cleared for good.
-- No DELETE here - creature_template is on this repo's SQL linter's do-not-delete list
-- (apps/codestyle/codestyle-sql.py's `not_delete`), and this is a first-time INSERT, not an edit to
-- an existing row, so there's no matching UPDATE...WHERE to fall back on either. An upsert is both
-- idempotent and never deletes.
INSERT INTO `creature_template` (`entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`, `KillCredit1`, `KillCredit2`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`, `faction`, `npcflag`, `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`, `dmgschool`, `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`, `unit_class`, `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`, `pickpocketloot`, `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`, `HoverHeight`, `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`, `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`, `VerifiedBuild`) VALUES
(300100, 0, 0, 0, 0, 0, 'Divine Star', '', '', 0, 1, 1, 0, 35, 0, 1, 1, 1, 1, 0, 0, 0, 1, 2000, 2000, 1, 1, 1, 33555200, 2048, 0, 0, 10, 1024, 0, 0, 0, 0, 0, 0, 0, '', 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 66, 'npc_pri_divine_star', 0) ON DUPLICATE KEY UPDATE `difficulty_entry_1` = VALUES(`difficulty_entry_1`), `difficulty_entry_2` = VALUES(`difficulty_entry_2`), `difficulty_entry_3` = VALUES(`difficulty_entry_3`), `KillCredit1` = VALUES(`KillCredit1`), `KillCredit2` = VALUES(`KillCredit2`), `name` = VALUES(`name`), `subname` = VALUES(`subname`), `IconName` = VALUES(`IconName`), `gossip_menu_id` = VALUES(`gossip_menu_id`), `minlevel` = VALUES(`minlevel`), `maxlevel` = VALUES(`maxlevel`), `exp` = VALUES(`exp`), `faction` = VALUES(`faction`), `npcflag` = VALUES(`npcflag`), `speed_walk` = VALUES(`speed_walk`), `speed_run` = VALUES(`speed_run`), `speed_swim` = VALUES(`speed_swim`), `speed_flight` = VALUES(`speed_flight`), `detection_range` = VALUES(`detection_range`), `rank` = VALUES(`rank`), `dmgschool` = VALUES(`dmgschool`), `DamageModifier` = VALUES(`DamageModifier`), `BaseAttackTime` = VALUES(`BaseAttackTime`), `RangeAttackTime` = VALUES(`RangeAttackTime`), `BaseVariance` = VALUES(`BaseVariance`), `RangeVariance` = VALUES(`RangeVariance`), `unit_class` = VALUES(`unit_class`), `unit_flags` = VALUES(`unit_flags`), `unit_flags2` = VALUES(`unit_flags2`), `dynamicflags` = VALUES(`dynamicflags`), `family` = VALUES(`family`), `type` = VALUES(`type`), `type_flags` = VALUES(`type_flags`), `lootid` = VALUES(`lootid`), `pickpocketloot` = VALUES(`pickpocketloot`), `skinloot` = VALUES(`skinloot`), `PetSpellDataId` = VALUES(`PetSpellDataId`), `VehicleId` = VALUES(`VehicleId`), `mingold` = VALUES(`mingold`), `maxgold` = VALUES(`maxgold`), `AIName` = VALUES(`AIName`), `MovementType` = VALUES(`MovementType`), `HoverHeight` = VALUES(`HoverHeight`), `HealthModifier` = VALUES(`HealthModifier`), `ManaModifier` = VALUES(`ManaModifier`), `ArmorModifier` = VALUES(`ArmorModifier`), `ExperienceModifier` = VALUES(`ExperienceModifier`), `RacialLeader` = VALUES(`RacialLeader`), `movementId` = VALUES(`movementId`), `RegenHealth` = VALUES(`RegenHealth`), `CreatureImmunitiesId` = VALUES(`CreatureImmunitiesId`), `flags_extra` = VALUES(`flags_extra`), `ScriptName` = VALUES(`ScriptName`), `VerifiedBuild` = VALUES(`VerifiedBuild`);

DELETE FROM `creature_template_model` WHERE `CreatureID` = 300100;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`) VALUES
(300100, 0, 90004, 1, 1, 0);

-- Angelic Feather's trap GameObject (300101, gameobject_template.trap fields per GameObjectData.h),
-- summoned at the target's ground-click position by spell 200130. type=6 (GAMEOBJECT_TYPE_TRAP),
-- Data6 (autoCloseTime) = -1 with an owner set is what makes GameObject.cpp's Update() take the
-- "environmental trap" branch (AnyPlayerInObjectRangeCheck - fires for ANY nearby player, ally or
-- enemy) instead of the hostile-only hunter-trap branch (NearestAttackableNoTotemUnitInObjectRangeCheck)
-- - the triggered spell (200131, TARGET_UNIT_TARGET_ALLY) is what actually restricts the speed
-- buff to allies, see that spell's own notes in priest_trigger_spells.py. Data4 (trap.type) = 1
-- ("despawns after cast") for the "first ally to walk through it" single-use behavior. Data2
-- (diameter) = 6 -> GameObject.cpp computes activation radius = diameter * 0.5 = 3 yards. Display
-- 90001 is a real feather model - GameObjectDisplayInfo row minted by
-- apps/dbc-tools/patch_priest_vfx_models.py, wrapping Priest_AngelicFeather_State.M2 (mined from
-- the Ascension client backup) - replaces the earlier placeholder (1287, stock "Rune" model reused
-- from real trap-type GOs like Rune of the Defiler/153204).
-- No DELETE here - gameobject_template is on this repo's SQL linter's do-not-delete list, same
-- reasoning as creature_template above.
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`, `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`, `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`, `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(300101, 6, 90001, 'Angelic Feather', '', '', '', 1, 0, 0, 6, 200131, 1, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`), `name` = VALUES(`name`), `IconName` = VALUES(`IconName`), `castBarCaption` = VALUES(`castBarCaption`), `unk1` = VALUES(`unk1`), `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `Data1` = VALUES(`Data1`), `Data2` = VALUES(`Data2`), `Data3` = VALUES(`Data3`), `Data4` = VALUES(`Data4`), `Data5` = VALUES(`Data5`), `Data6` = VALUES(`Data6`), `Data7` = VALUES(`Data7`), `Data8` = VALUES(`Data8`), `Data9` = VALUES(`Data9`), `Data10` = VALUES(`Data10`), `Data11` = VALUES(`Data11`), `Data12` = VALUES(`Data12`), `Data13` = VALUES(`Data13`), `Data14` = VALUES(`Data14`), `Data15` = VALUES(`Data15`), `Data16` = VALUES(`Data16`), `Data17` = VALUES(`Data17`), `Data18` = VALUES(`Data18`), `Data19` = VALUES(`Data19`), `Data20` = VALUES(`Data20`), `Data21` = VALUES(`Data21`), `Data22` = VALUES(`Data22`), `Data23` = VALUES(`Data23`), `AIName` = VALUES(`AIName`), `ScriptName` = VALUES(`ScriptName`), `VerifiedBuild` = VALUES(`VerifiedBuild`);
