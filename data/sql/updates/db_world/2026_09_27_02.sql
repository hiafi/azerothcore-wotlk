-- DB update 2026_09_27_01 -> 2026_09_27_02
-- Squash (2026-09-25) of the druid-rework branch's non-generate.py world migrations, in their
-- original order: Bear/Cat/Moonkin Form appearance models + NPC 900012, Healing Training Dummy
-- 900013/900014, and the Starsurge/Fury of Elune SpellVisual rows (patch_druid_vfx_models.py).
-- The generate.py half of the squash is the sibling rev_1790396279551431424.sql.

-- ---- from rev_1790197894438593876.sql ----
DELETE FROM `creaturemodeldata_dbc` WHERE `ID` BETWEEN 90100 AND 90199;
INSERT INTO `creaturemodeldata_dbc` (`ID`, `Flags`, `ModelName`, `SizeClass`, `ModelScale`, `BloodID`, `FootprintTextureID`, `FootprintTextureLength`, `FootprintTextureWidth`, `FootprintParticleScale`, `FoleyMaterialID`, `FootstepShakeSize`, `DeathThudShakeSize`, `SoundID`, `CollisionWidth`, `CollisionHeight`, `MountHeight`, `GeoBoxMinX`, `GeoBoxMinY`, `GeoBoxMinZ`, `GeoBoxMaxX`, `GeoBoxMaxY`, `GeoBoxMaxZ`, `WorldEffectScale`, `AttachedEffectScale`, `MissileCollisionRadius`, `MissileCollisionPush`, `MissileCollisionRaise`) VALUES
(90100, 4112, 'CREATURE\\DRUIDBEARTROLL\\DRUIDBEARTROLL.M2', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111119985580444, 2.031280040740967, 1.7614699602127075, 3218462097, 3211516262, 3190562291, 1071500136, 1063003735, 1073457450, 1065353216, 1065353216, 0, 0, 0),
(90101, 4112, 'CREATURE\\DRUIDBEARTROLL\\DRUIDBEARTROLLEPIC.M2', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111119985580444, 2.031280040740967, 0.0, 3219366389, 3215565007, 3190562291, 1073081305, 1068113823, 1074096452, 1065353216, 1065353216, 0, 0, 0),
(90102, 16, 'Creature\\druidbear2\\druidbear2_artifact1.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220474859, 3213799205, 3170372039, 1070278084, 1065866850, 1072828053, 1065353216, 1065353216, 0, 0, 0),
(90103, 16, 'Creature\\druidbear2\\druidbear2_artifact2.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3221366443, 3214280208, 3159739257, 1071762196, 1066766361, 1075293423, 1065353216, 1065353216, 0, 0, 0),
(90104, 16, 'Creature\\druidbear2\\druidbear2_artifact3.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220179245, 3213628245, 3171643833, 1072254608, 1066057356, 1077432434, 1065353216, 1065353216, 0, 0, 0),
(90105, 16, 'Creature\\druidbear2\\druidbear2_artifact4.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220498767, 3212570727, 3163724879, 1072183472, 1065045237, 1076268599, 1065353216, 1065353216, 0, 0, 0),
(90106, 16, 'Creature\\druidbear2\\druidbear2_artifact5.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220667462, 3212688235, 3163829891, 1071926026, 1064998462, 1074205337, 1065353216, 1065353216, 0, 0, 0),
(90107, 16, 'Creature\\druidbear2\\druidbear2_artifact6.mdx', 1, 1.0, 1, 7, 1106247680, 1101004800, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3222514424, 3224303001, 3191078694, 1078376110, 1076032837, 1084002224, 1065353216, 1065353216, 0, 0, 0),
(90108, 16, 'Creature\\druidbear2\\druidbear2_artifact7.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220498767, 3212570727, 3163724879, 1072183472, 1065045237, 1076268599, 1065353216, 1065353216, 0, 0, 0),
(90109, 16, 'Creature\\druidbear2\\druidbear2_artifact8.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220498767, 3212570727, 3163724879, 1072183472, 1065045237, 1076268599, 1065353216, 1065353216, 0, 0, 0),
(90110, 16, 'Creature\\druidbear2\\druidbear2_artifact9.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220498767, 3212570727, 3163724879, 1072183472, 1065045237, 1076268599, 1065353216, 1065353216, 0, 0, 0),
(90111, 16, 'Creature\\druidbear2\\druidbear2_artifact10.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220179245, 3213628245, 3171643833, 1072254608, 1066057356, 1077432434, 1065353216, 1065353216, 0, 0, 0),
(90112, 16, 'Creature\\druidbear2\\druidbear2_artifact11.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220179245, 3213628245, 3171643833, 1072254608, 1066057356, 1077432434, 1065353216, 1065353216, 0, 0, 0),
(90113, 16, 'Creature\\druidbear2\\druidbear2_artifact12.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220179245, 3213628245, 3171643833, 1072254608, 1066057356, 1077432434, 1065353216, 1065353216, 0, 0, 0),
(90114, 16, 'Creature\\druidbearkultiran\\druidbearkultiran.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3219738256, 3214625147, 3171150153, 1071057553, 1067118934, 1074411529, 1065353216, 1065353216, 0, 0, 0),
(90115, 4112, 'creature\\druidbearzandalaritroll\\druidbearzandalaritroll.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 6512, 0, 2.031280040740967, 1.0, 0.0, 3219811404, 3217385838, 3161053732, 1072241186, 1069843722, 1075575322, 1065353216, 1065353216, 1065353216, 0, 0),
(90116, 16, 'Creature\\druidbearzandalaritroll_noarmor\\druidbearzandalaritroll_noarmor.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3219811404, 3217385838, 3161053732, 1071456683, 1069843722, 1075575322, 1065353216, 1065353216, 0, 0, 0);

DELETE FROM `creaturedisplayinfo_dbc` WHERE `ID` BETWEEN 90100 AND 90199;
INSERT INTO `creaturedisplayinfo_dbc` (`ID`, `ModelID`, `SoundID`, `ExtendedDisplayInfoID`, `CreatureModelScale`, `CreatureModelAlpha`, `TextureVariation_1`, `TextureVariation_2`, `TextureVariation_3`, `PortraitTextureName`, `BloodLevel`, `BloodID`, `NPCSoundID`, `ParticleColorID`, `CreatureGeosetData`, `ObjectEffectPackageID`) VALUES
(90100, 90100, 0, 0, 1.0, 255, 'DruidBearTrollBlue', NULL, NULL, NULL, 1, 0, 0, 0, 0, 0),
(90101, 90100, 0, 0, 1.0, 255, 'DruidBearTrollPurple', NULL, NULL, NULL, 1, 0, 0, 0, 0, 0),
(90102, 90100, 0, 0, 1.0, 255, 'DruidBearTrollRed', NULL, NULL, NULL, 1, 0, 0, 0, 0, 0),
(90103, 90100, 0, 0, 1.0, 255, 'DruidBearTrollWhite', NULL, NULL, NULL, 1, 0, 0, 0, 0, 0),
(90104, 90100, 0, 0, 1.0, 255, 'DruidBearTrollYellow', NULL, NULL, NULL, 1, 0, 0, 0, 0, 0),
(90105, 90101, 0, 0, 1.0, 255, 'DruidBearTrollBlue', 'DruidFormsEpicArmorHordeTrollBear', NULL, NULL, 1, 0, 0, 0, 0, 0),
(90106, 90101, 0, 0, 1.0, 255, 'DruidBearTrollPurple', 'DruidFormsEpicArmorHordeTrollBear', NULL, NULL, 1, 0, 0, 0, 0, 0),
(90107, 90101, 0, 0, 1.0, 255, 'DruidBearTrollRed', 'DruidFormsEpicArmorHordeTrollBear', NULL, NULL, 1, 0, 0, 0, 0, 0),
(90108, 90101, 0, 0, 1.0, 255, 'DruidBearTrollWhite', 'DruidFormsEpicArmorHordeTrollBear', NULL, NULL, 1, 0, 0, 0, 0, 0),
(90109, 90101, 0, 0, 1.0, 255, 'DruidBearTrollYellow', 'DruidFormsEpicArmorHordeTrollBear', NULL, NULL, 1, 0, 0, 0, 0, 0),
(90110, 90102, 0, 0, 1.0, 255, 'druidbear2_artifact1_black', 'druidbear2_artifact1_armor_black', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90111, 90102, 0, 0, 1.0, 255, 'druidbear2_artifact1_blue', 'druidbear2_artifact1_armor_blue', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90112, 90102, 0, 0, 1.0, 255, 'druidbear2_artifact1_brown', 'druidbear2_artifact1_armor_brown', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90113, 90102, 0, 0, 1.0, 255, 'druidbear2_artifact1_burgundy', 'druidbear2_artifact1_armor_burgundy', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90114, 90102, 0, 0, 1.0, 255, 'druidbear2_artifact1_gold', 'druidbear2_artifact1_armor_gold', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90115, 90102, 0, 0, 1.0, 255, 'druidbear2_artifact1_purple', 'druidbear2_artifact1_armor_purple', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90116, 90102, 0, 0, 1.0, 255, 'druidbear2_artifact1_white', 'druidbear2_artifact1_armor_white', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90117, 90102, 0, 0, 1.0, 255, 'druidbear2_artifact1_valsharah', 'druidbear2_artifact1_armor_valsharah', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90118, 90103, 0, 0, 1.0, 255, 'druidbear2_artifact2_cool', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90119, 90103, 0, 0, 1.0, 255, 'druidbear2_artifact2_dark', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90120, 90103, 0, 0, 1.0, 255, 'druidbear2_artifact2_green', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90121, 90103, 0, 0, 1.0, 255, 'druidbear2_artifact2_pink', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90122, 90104, 0, 0, 1.0, 255, 'druidbear2_artifact3_blue', 'druidbear2_artifact3_armor_blue', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90123, 90111, 0, 0, 1.0, 255, 'druidbear2_artifact3_green', 'druidbear2_artifact3_armor_green', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90124, 90112, 0, 0, 1.0, 255, 'druidbear2_artifact3_purple', 'druidbear2_artifact3_armor_purple', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90125, 90113, 0, 0, 1.0, 255, 'druidbear2_artifact3_red', 'druidbear2_artifact3_armor_red', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90126, 90109, 0, 0, 1.0, 255, 'druidbear2_artifact4_blue', 'druidbear2_artifact4_fx_blue', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90127, 90110, 0, 0, 1.0, 255, 'druidbear2_artifact4_brown', 'druidbear2_artifact4_fx_brown', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90128, 90108, 0, 0, 1.0, 255, 'druidbear2_artifact4_green', 'druidbear2_artifact4_fx_green', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90129, 90105, 0, 0, 1.0, 255, 'druidbear2_artifact4_red', 'druidbear2_artifact4_fx_red', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90130, 90106, 0, 0, 1.0, 255, 'druidbear2_artifact5_black', 'druidbear2_artifact5_armor_black', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90131, 90106, 0, 0, 1.0, 255, 'druidbear2_artifact5_brown', 'druidbear2_artifact5_armor_brown', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90132, 90106, 0, 0, 1.0, 255, 'druidbear2_artifact5_red', 'druidbear2_artifact5_armor_red', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90133, 90106, 0, 0, 1.0, 255, 'druidbear2_artifact5_white', 'druidbear2_artifact5_armor_white', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90134, 90107, 0, 0, 0.5, 255, 'druidbear2_artifact6_white', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90135, 90107, 0, 0, 0.5, 255, 'druidbear2_artifact6_brown', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90136, 90107, 0, 0, 0.5, 255, 'druidbear2_artifact6_blonde', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90137, 90107, 0, 0, 0.5, 255, 'druidbear2_artifact6_black', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90138, 90114, 0, 0, 1.0, 255, 'druidbearkultiran_brown', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90139, 90114, 0, 0, 1.0, 255, 'druidbearkultiran_dark', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90140, 90114, 0, 0, 1.0, 255, 'druidbearkultiran_green', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90141, 90114, 0, 0, 1.0, 255, 'druidbearkultiran_light', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90142, 90115, 0, 0, 1.0, 255, 'druidbearzandalaritroll_blue', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90143, 90115, 0, 0, 1.0, 255, 'druidbearzandalaritroll_dark', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90144, 90115, 0, 0, 1.0, 255, 'druidbearzandalaritroll_green', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90145, 90115, 0, 0, 1.0, 255, 'druidbearzandalaritroll_white', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90146, 90116, 0, 0, 1.0, 255, 'druidbearzandalaritroll_noarmor_black', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90147, 90116, 0, 0, 1.0, 255, 'druidbearzandalaritroll_noarmor_blue', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90148, 90116, 0, 0, 1.0, 255, 'druidbearzandalaritroll_noarmor_green', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90149, 90116, 0, 0, 1.0, 255, 'druidbearzandalaritroll_noarmor_white', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0);

-- ---- from rev_1790198077088457589.sql ----
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

-- ---- from rev_1790219222774681405.sql ----
DELETE FROM `creaturemodeldata_dbc` WHERE `ID` BETWEEN 90100 AND 90399;
INSERT INTO `creaturemodeldata_dbc` (`ID`, `Flags`, `ModelName`, `SizeClass`, `ModelScale`, `BloodID`, `FootprintTextureID`, `FootprintTextureLength`, `FootprintTextureWidth`, `FootprintParticleScale`, `FoleyMaterialID`, `FootstepShakeSize`, `DeathThudShakeSize`, `SoundID`, `CollisionWidth`, `CollisionHeight`, `MountHeight`, `GeoBoxMinX`, `GeoBoxMinY`, `GeoBoxMinZ`, `GeoBoxMaxX`, `GeoBoxMaxY`, `GeoBoxMaxZ`, `WorldEffectScale`, `AttachedEffectScale`, `MissileCollisionRadius`, `MissileCollisionPush`, `MissileCollisionRaise`) VALUES
(90100, 4112, 'CREATURE\\DRUIDBEARTROLL\\DRUIDBEARTROLL.M2', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111119985580444, 2.031280040740967, 1.7614699602127075, 3218462097, 3211516262, 3190562291, 1071500136, 1063003735, 1073457450, 1065353216, 1065353216, 0, 0, 0),
(90101, 4112, 'CREATURE\\DRUIDBEARTROLL\\DRUIDBEARTROLLEPIC.M2', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111119985580444, 2.031280040740967, 0.0, 3219366389, 3215565007, 3190562291, 1073081305, 1068113823, 1074096452, 1065353216, 1065353216, 0, 0, 0),
(90102, 16, 'Creature\\druidbear2\\druidbear2_artifact1.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220474859, 3213799205, 3170372039, 1070278084, 1065866850, 1072828053, 1065353216, 1065353216, 0, 0, 0),
(90103, 16, 'Creature\\druidbear2\\druidbear2_artifact2.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3221366443, 3214280208, 3159739257, 1071762196, 1066766361, 1075293423, 1065353216, 1065353216, 0, 0, 0),
(90104, 16, 'Creature\\druidbear2\\druidbear2_artifact3.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220179245, 3213628245, 3171643833, 1072254608, 1066057356, 1077432434, 1065353216, 1065353216, 0, 0, 0),
(90105, 16, 'Creature\\druidbear2\\druidbear2_artifact4.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220498767, 3212570727, 3163724879, 1072183472, 1065045237, 1076268599, 1065353216, 1065353216, 0, 0, 0),
(90106, 16, 'Creature\\druidbear2\\druidbear2_artifact5.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220667462, 3212688235, 3163829891, 1071926026, 1064998462, 1074205337, 1065353216, 1065353216, 0, 0, 0),
(90107, 16, 'Creature\\druidbear2\\druidbear2_artifact6.mdx', 1, 1.0, 1, 7, 1106247680, 1101004800, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3222514424, 3224303001, 3191078694, 1078376110, 1076032837, 1084002224, 1065353216, 1065353216, 0, 0, 0),
(90108, 16, 'Creature\\druidbear2\\druidbear2_artifact7.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220498767, 3212570727, 3163724879, 1072183472, 1065045237, 1076268599, 1065353216, 1065353216, 0, 0, 0),
(90109, 16, 'Creature\\druidbear2\\druidbear2_artifact8.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220498767, 3212570727, 3163724879, 1072183472, 1065045237, 1076268599, 1065353216, 1065353216, 0, 0, 0),
(90110, 16, 'Creature\\druidbear2\\druidbear2_artifact9.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220498767, 3212570727, 3163724879, 1072183472, 1065045237, 1076268599, 1065353216, 1065353216, 0, 0, 0),
(90111, 16, 'Creature\\druidbear2\\druidbear2_artifact10.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220179245, 3213628245, 3171643833, 1072254608, 1066057356, 1077432434, 1065353216, 1065353216, 0, 0, 0),
(90112, 16, 'Creature\\druidbear2\\druidbear2_artifact11.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220179245, 3213628245, 3171643833, 1072254608, 1066057356, 1077432434, 1065353216, 1065353216, 0, 0, 0),
(90113, 16, 'Creature\\druidbear2\\druidbear2_artifact12.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3220179245, 3213628245, 3171643833, 1072254608, 1066057356, 1077432434, 1065353216, 1065353216, 0, 0, 0),
(90114, 16, 'Creature\\druidbearkultiran\\druidbearkultiran.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3219738256, 3214625147, 3171150153, 1071057553, 1067118934, 1074411529, 1065353216, 1065353216, 0, 0, 0),
(90115, 4112, 'creature\\druidbearzandalaritroll\\druidbearzandalaritroll.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 6512, 0, 2.031280040740967, 1.0, 0.0, 3219811404, 3217385838, 3161053732, 1072241186, 1069843722, 1075575322, 1065353216, 1065353216, 1065353216, 0, 0),
(90116, 16, 'Creature\\druidbearzandalaritroll_noarmor\\druidbearzandalaritroll_noarmor.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 3022, 0.6111000180244446, 2.0309998989105225, 0.0, 3219811404, 3217385838, 3161053732, 1071456683, 1069843722, 1075575322, 1065353216, 1065353216, 0, 0, 0),
(90200, 4096, 'CREATURE\\DRUIDCATTROLL\\DRUIDCATTROLL.M2', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 1089, 0.6111119985580444, 2.031280040740967, 1.2413699626922607, 3224236773, 3210528789, 3174550452, 1067836160, 1058319301, 1070334959, 1065353216, 1065353216, 0, 0, 0),
(90201, 4096, 'CREATURE\\DRUIDCATTROLL\\DRUIDCATTROLLEPIC.M2', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 1089, 0.6111119985580444, 2.031280040740967, 1.2413699626922607, 3224236773, 3211145201, 3173332829, 1067119773, 1064833911, 1070949676, 1065353216, 1065353216, 0, 0, 0),
(90202, 16, 'Creature\\druidcat2\\druidcat2_artifact1.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 1088, 0.6111000180244446, 2.0309998989105225, 0.0, 3226592503, 3215290783, 3190198158, 1065911142, 1065358669, 1069985741, 1065353216, 1065353216, 0, 0, 0),
(90203, 16, 'Creature\\druidcat2\\druidcat2_artifact2.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 1088, 0.6111000180244446, 2.0309998989105225, 0.0, 3226592503, 3215290700, 3188475541, 1065911142, 1065358669, 1069985741, 1065353216, 1065353216, 0, 0, 0),
(90204, 16, 'Creature\\druidcat2\\druidcat2_artifact3.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 1088, 0.6111000180244446, 2.0309998989105225, 0.0, 3226592461, 3215290700, 3190198360, 1065911142, 1065358669, 1071893814, 1065353216, 1065353216, 0, 0, 0),
(90205, 16, 'Creature\\druidcat2\\druidcat2_artifact4.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 1088, 0.6111000180244446, 2.0309998989105225, 0.0, 3226592503, 3215290783, 3190198158, 1065911142, 1065358669, 1071590649, 1065353216, 1065353216, 0, 0, 0),
(90206, 16, 'Creature\\druidcat2\\druidcat2_artifact5.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 1088, 0.6111000180244446, 2.0309998989105225, 0.0, 3226592503, 3215290783, 3190198158, 1065911142, 1065358669, 1069985741, 1065353216, 1065353216, 0, 0, 0),
(90207, 16, 'Creature\\druidcat2\\druidcat2_artifact6.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 1088, 0.6111000180244446, 2.0309998989105225, 0.0, 3226592503, 3215290700, 3188475541, 1065911142, 1065358669, 1069985741, 1065353216, 1065353216, 0, 0, 0),
(90208, 16, 'Creature\\druidcat2\\druidcat2_artifact7.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 1088, 0.6111000180244446, 2.0309998989105225, 0.0, 3226592503, 3215290700, 3188475541, 1065911142, 1065358669, 1069985741, 1065353216, 1065353216, 0, 0, 0),
(90209, 16, 'Creature\\druidcat2\\druidcat2_artifact8.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 1088, 0.6111000180244446, 2.0309998989105225, 0.0, 3226592503, 3215290700, 3188475541, 1065911142, 1065358669, 1069985741, 1065353216, 1065353216, 0, 0, 0),
(90210, 4096, 'creature\\druidcatkultiran\\druidcatkultiran.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 6488, 0, 2.031280040740967, 1.0, 0.0, 3223901186, 3209341448, 3164082757, 1066396591, 1060321611, 1070407352, 1065353216, 1065353216, 1065353216, 0, 0),
(90211, 16, 'Creature\\druidcatkultiran_noarmor\\druidcatkultiran_noarmor.mdx', 1, 1.0, 1, 7, 1099956224, 1094713344, 1065353216, 0, 0, 0, 1088, 0.6111000180244446, 2.0309998989105225, 0.0, 3223901186, 3209341448, 3164082757, 1066396591, 1060321611, 1070407352, 1065353216, 1065353216, 0, 0, 0),
(90212, 4112, 'creature\\druidcatzandalaritroll\\druidcatzandalaritroll.mdx', 1, 1.0, 1, 7, 1094713344, 1090519040, 1065353216, 0, 0, 6514, 0, 2.031280040740967, 1.25, 0.0, 3226897178, 3205779327, 3166409771, 1068612610, 1057793688, 1072666740, 1065353216, 1065353216, 1065353216, 0, 0),
(90213, 16, 'Creature\\druidcatzandalaritroll_noarmor\\druidcatzandalaritroll_noarmor.mdx', 1, 1.0, 1, 7, 1094713344, 1090519040, 1065353216, 0, 0, 0, 1088, 0.6111000180244446, 2.0309998989105225, 0.0, 3226897178, 3205779327, 3166409771, 1068612610, 1057793688, 1072666740, 1065353216, 1065353216, 0, 0, 0),
(90214, 4096, 'creature\\druidcat2\\druidcat2_tree.mdx', 1, 1.0, 1, 7, 1094713344, 1090519040, 1065353216, 0, 0, 0, 5143, 2.031280040740967, 1.25, 0.0, 3224242141, 3210420727, 3179819075, 1066057104, 1058316281, 1070187655, 1065353216, 1065353216, 1065353216, 0, 0),
(90300, 0, 'Creature\\druidowlbear2\\druidowlbear2.mdx', 1, 1.0, 1, 5, 1106247680, 1101004800, 1065353216, 0, 0, 0, 4324, 0.6111000180244446, 2.0309998989105225, 0.0, 3212472614, 3218304307, 3132238989, 1063422729, 1070801281, 1081981786, 1065353216, 1065353216, 0, 0, 0),
(90301, 0, 'Creature\\druidowlbear2\\druidowlbearepic2.mdx', 1, 1.0, 1, 5, 1106247680, 1101004800, 1065353216, 0, 0, 0, 4324, 0.6111000180244446, 2.0309998989105225, 0.0, 3213973353, 3219642626, 3180386279, 1063917053, 1072206877, 1081981786, 1065353216, 1065353216, 0, 0, 0),
(90302, 128, 'Creature\\druidowlbearhmtauren2\\druidowlbearhmtauren2.mdx', 1, 1.0, 1, 5, 1106247680, 1101004800, 1065353216, 0, 0, 0, 4324, 0.6111000180244446, 2.0309998989105225, 0.0, 3212472597, 3218304307, 3132240793, 1063422729, 1070801281, 1080606432, 1065353216, 1065353216, 1065353216, 0, 0),
(90303, 0, 'Creature\\druidowlbearhmtaurenepic2\\druidowlbearhmtaurenepic2.mdx', 1, 1.0, 1, 5, 1106247680, 1101004800, 1065353216, 0, 0, 0, 4324, 0.6111000180244446, 2.0309998989105225, 0.0, 3213973353, 3219642626, 3180386333, 1063917053, 1072206877, 1080606432, 1065353216, 1065353216, 0, 0, 0),
(90304, 128, 'Creature\\druidowlbearkultiranepic2\\druidowlbearkultiranepic2.mdx', 1, 1.0, 1, 5, 1106247680, 1101004800, 1065353216, 0, 0, 0, 2095, 0.6111000180244446, 2.0309998989105225, 0.0, 3213505268, 3216221164, 3161638921, 1060237054, 1068711931, 1079383373, 1065353216, 1065353216, 0, 0, 0),
(90305, 128, 'Creature\\druidowlbearzandalariepic2\\druidowlbearzandalariepic2.mdx', 3, 1.0, 1, 5, 1096810496, 1092616192, 1065353216, 0, 0, 0, 2095, 0.6111000180244446, 2.0309998989105225, 2.7451300621032715, 3210571520, 3205133136, 3157327740, 1058000870, 1058372166, 1072589061, 1065353216, 1065353216, 0, 0, 0),
(90306, 128, 'creature\\tindralmoonkin\\blue_tindralmoonkin.mdx', 1, 1.0, 1, 7, 1106247680, 1101004800, 1065353216, 0, 0, 0, 2095, 2.031280040740967, 1.0, 0.0, 3212484224, 3216221164, 3150115116, 1060237054, 1068711931, 1079303429, 1065353216, 1065353216, 1065353216, 0, 0),
(90307, 128, 'creature\\tindralmoonkin\\green_tindralmoonkin.mdx', 1, 1.0, 1, 5, 1106247680, 1101004800, 1065353216, 0, 0, 0, 2095, 2.031280040740967, 1.0, 0.0, 3212484224, 3216221164, 3150115116, 1060237054, 1068711931, 1079303429, 1065353216, 1065353216, 1065353216, 0, 0),
(90308, 128, 'creature\\tindralmoonkin\\purple_tindralmoonkin.mdx', 1, 1.0, 1, 5, 1106247680, 1101004800, 1065353216, 0, 0, 0, 2095, 2.031280040740967, 1.0, 0.0, 3212484224, 3216221164, 3150115116, 1060237054, 1068711931, 1079303429, 1065353216, 1065353216, 1065353216, 0, 0),
(90309, 128, 'creature\\tindralmoonkin\\red_tindralmoonkin.mdx', 1, 1.0, 1, 5, 1106247680, 1101004800, 1065353216, 0, 0, 0, 2095, 2.031280040740967, 1.0, 0.0, 3212484224, 3216221164, 3150115116, 1060237054, 1068711931, 1079303429, 1065353216, 1065353216, 1065353216, 0, 0),
(90310, 128, 'creature\\tindralmoonkin\\yellow_tindralmoonkin.mdx', 1, 1.0, 1, 5, 1106247680, 1101004800, 1065353216, 0, 0, 0, 2095, 2.031280040740967, 1.0, 0.0, 3212484224, 3216221164, 3150115116, 1060237054, 1068711931, 1079303429, 1065353216, 1065353216, 1065353216, 0, 0);

DELETE FROM `creaturedisplayinfo_dbc` WHERE `ID` BETWEEN 90100 AND 90399;
INSERT INTO `creaturedisplayinfo_dbc` (`ID`, `ModelID`, `SoundID`, `ExtendedDisplayInfoID`, `CreatureModelScale`, `CreatureModelAlpha`, `TextureVariation_1`, `TextureVariation_2`, `TextureVariation_3`, `PortraitTextureName`, `BloodLevel`, `BloodID`, `NPCSoundID`, `ParticleColorID`, `CreatureGeosetData`, `ObjectEffectPackageID`) VALUES
(90100, 90100, 0, 0, 1.0, 255, 'DruidBearTrollBlue', NULL, NULL, NULL, 1, 0, 0, 0, 0, 0),
(90101, 90100, 0, 0, 1.0, 255, 'DruidBearTrollPurple', NULL, NULL, NULL, 1, 0, 0, 0, 0, 0),
(90102, 90100, 0, 0, 1.0, 255, 'DruidBearTrollRed', NULL, NULL, NULL, 1, 0, 0, 0, 0, 0),
(90103, 90100, 0, 0, 1.0, 255, 'DruidBearTrollWhite', NULL, NULL, NULL, 1, 0, 0, 0, 0, 0),
(90104, 90100, 0, 0, 1.0, 255, 'DruidBearTrollYellow', NULL, NULL, NULL, 1, 0, 0, 0, 0, 0),
(90105, 90101, 0, 0, 1.0, 255, 'DruidBearTrollBlue', 'DruidFormsEpicArmorHordeTrollBear', NULL, NULL, 1, 0, 0, 0, 0, 0),
(90106, 90101, 0, 0, 1.0, 255, 'DruidBearTrollPurple', 'DruidFormsEpicArmorHordeTrollBear', NULL, NULL, 1, 0, 0, 0, 0, 0),
(90107, 90101, 0, 0, 1.0, 255, 'DruidBearTrollRed', 'DruidFormsEpicArmorHordeTrollBear', NULL, NULL, 1, 0, 0, 0, 0, 0),
(90108, 90101, 0, 0, 1.0, 255, 'DruidBearTrollWhite', 'DruidFormsEpicArmorHordeTrollBear', NULL, NULL, 1, 0, 0, 0, 0, 0),
(90109, 90101, 0, 0, 1.0, 255, 'DruidBearTrollYellow', 'DruidFormsEpicArmorHordeTrollBear', NULL, NULL, 1, 0, 0, 0, 0, 0),
(90110, 90102, 0, 0, 1.0, 255, 'druidbear2_artifact1_black', 'druidbear2_artifact1_armor_black', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90111, 90102, 0, 0, 1.0, 255, 'druidbear2_artifact1_blue', 'druidbear2_artifact1_armor_blue', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90112, 90102, 0, 0, 1.0, 255, 'druidbear2_artifact1_brown', 'druidbear2_artifact1_armor_brown', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90113, 90102, 0, 0, 1.0, 255, 'druidbear2_artifact1_burgundy', 'druidbear2_artifact1_armor_burgundy', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90114, 90102, 0, 0, 1.0, 255, 'druidbear2_artifact1_gold', 'druidbear2_artifact1_armor_gold', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90115, 90102, 0, 0, 1.0, 255, 'druidbear2_artifact1_purple', 'druidbear2_artifact1_armor_purple', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90116, 90102, 0, 0, 1.0, 255, 'druidbear2_artifact1_white', 'druidbear2_artifact1_armor_white', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90117, 90102, 0, 0, 1.0, 255, 'druidbear2_artifact1_valsharah', 'druidbear2_artifact1_armor_valsharah', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90118, 90103, 0, 0, 1.0, 255, 'druidbear2_artifact2_cool', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90119, 90103, 0, 0, 1.0, 255, 'druidbear2_artifact2_dark', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90120, 90103, 0, 0, 1.0, 255, 'druidbear2_artifact2_green', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90121, 90103, 0, 0, 1.0, 255, 'druidbear2_artifact2_pink', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90122, 90104, 0, 0, 1.0, 255, 'druidbear2_artifact3_blue', 'druidbear2_artifact3_armor_blue', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90123, 90111, 0, 0, 1.0, 255, 'druidbear2_artifact3_green', 'druidbear2_artifact3_armor_green', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90124, 90112, 0, 0, 1.0, 255, 'druidbear2_artifact3_purple', 'druidbear2_artifact3_armor_purple', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90125, 90113, 0, 0, 1.0, 255, 'druidbear2_artifact3_red', 'druidbear2_artifact3_armor_red', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90126, 90109, 0, 0, 1.0, 255, 'druidbear2_artifact4_blue', 'druidbear2_artifact4_fx_blue', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90127, 90110, 0, 0, 1.0, 255, 'druidbear2_artifact4_brown', 'druidbear2_artifact4_fx_brown', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90128, 90108, 0, 0, 1.0, 255, 'druidbear2_artifact4_green', 'druidbear2_artifact4_fx_green', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90129, 90105, 0, 0, 1.0, 255, 'druidbear2_artifact4_red', 'druidbear2_artifact4_fx_red', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90130, 90106, 0, 0, 1.0, 255, 'druidbear2_artifact5_black', 'druidbear2_artifact5_armor_black', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90131, 90106, 0, 0, 1.0, 255, 'druidbear2_artifact5_brown', 'druidbear2_artifact5_armor_brown', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90132, 90106, 0, 0, 1.0, 255, 'druidbear2_artifact5_red', 'druidbear2_artifact5_armor_red', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90133, 90106, 0, 0, 1.0, 255, 'druidbear2_artifact5_white', 'druidbear2_artifact5_armor_white', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90134, 90107, 0, 0, 0.5, 255, 'druidbear2_artifact6_white', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90135, 90107, 0, 0, 0.5, 255, 'druidbear2_artifact6_brown', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90136, 90107, 0, 0, 0.5, 255, 'druidbear2_artifact6_blonde', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90137, 90107, 0, 0, 0.5, 255, 'druidbear2_artifact6_black', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90138, 90114, 0, 0, 1.0, 255, 'druidbearkultiran_brown', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90139, 90114, 0, 0, 1.0, 255, 'druidbearkultiran_dark', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90140, 90114, 0, 0, 1.0, 255, 'druidbearkultiran_green', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90141, 90114, 0, 0, 1.0, 255, 'druidbearkultiran_light', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90142, 90115, 0, 0, 1.0, 255, 'druidbearzandalaritroll_blue', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90143, 90115, 0, 0, 1.0, 255, 'druidbearzandalaritroll_dark', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90144, 90115, 0, 0, 1.0, 255, 'druidbearzandalaritroll_green', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90145, 90115, 0, 0, 1.0, 255, 'druidbearzandalaritroll_white', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90146, 90116, 0, 0, 1.0, 255, 'druidbearzandalaritroll_noarmor_black', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90147, 90116, 0, 0, 1.0, 255, 'druidbearzandalaritroll_noarmor_blue', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90148, 90116, 0, 0, 1.0, 255, 'druidbearzandalaritroll_noarmor_green', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90149, 90116, 0, 0, 1.0, 255, 'druidbearzandalaritroll_noarmor_white', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90200, 90200, 0, 0, 1.0, 255, 'DruidCatTrollSkinBlack', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90201, 90200, 0, 0, 1.0, 255, 'DruidCatTrollSkinBlue', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90202, 90200, 0, 0, 1.0, 255, 'DruidCatTrollSkinGreen', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90203, 90200, 0, 0, 1.0, 255, 'DruidCatTrollSkinRed', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90204, 90200, 0, 0, 1.0, 255, 'DruidCatTrollSkinWhite', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90205, 90201, 0, 0, 1.0, 255, 'DruidCatTrollSkinBlack', 'DruidFormsEpicArmorHordeTrollCat', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90206, 90201, 0, 0, 1.0, 255, 'DruidCatTrollSkinBlue', 'DruidFormsEpicArmorHordeTrollCat', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90207, 90201, 0, 0, 1.0, 255, 'DruidCatTrollSkinGreen', 'DruidFormsEpicArmorHordeTrollCat', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90208, 90201, 0, 0, 1.0, 255, 'DruidCatTrollSkinRed', 'DruidFormsEpicArmorHordeTrollCat', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90209, 90201, 0, 0, 1.0, 255, 'DruidCatTrollSkinWhite', 'DruidFormsEpicArmorHordeTrollCat', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90210, 90202, 0, 0, 1.0, 255, 'druidcat2_artifact1_black', 'druidcat2_artifact1armor_black', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90211, 90202, 0, 0, 1.0, 255, 'druidcat2_artifact1_blue', 'druidcat2_artifact1armor_blue', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90212, 90202, 0, 0, 1.0, 255, 'druidcat2_artifact1_brown', 'druidcat2_artifact1armor_brown', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90213, 90202, 0, 0, 1.0, 255, 'druidcat2_artifact1_orange', 'druidcat2_artifact1armor_greybrown', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90214, 90202, 0, 0, 1.0, 255, 'druidcat2_artifact1_purple', 'druidcat2_artifact1armor_purple', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90215, 90202, 0, 0, 1.0, 255, 'druidcat2_artifact1_valsharah', 'druidcat2_artifact1armor_valsharah', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90216, 90202, 0, 0, 1.0, 255, 'druidcat2_artifact1_white', 'druidcat2_artifact1armor_white', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90217, 90203, 0, 0, 1.0, 255, 'druidcat2_artifact2_blue', 'druidcat2_artifact2fx_blue', 'druidcat2_artifact2armor_blue', NULL, -1, 0, 0, 0, 0, 0),
(90218, 90207, 0, 0, 1.0, 255, 'druidcat2_artifact2_green', 'druidcat2_artifact2fx_green', 'druidcat2_artifact2armor_green', NULL, -1, 0, 0, 0, 0, 0),
(90219, 90208, 0, 0, 1.0, 255, 'druidcat2_artifact2_purple', 'druidcat2_artifact2fx_purple', 'druidcat2_artifact2armor_purple', NULL, -1, 0, 0, 0, 0, 0),
(90220, 90209, 0, 0, 1.0, 255, 'druidcat2_artifact2_red', 'druidcat2_artifact2fx_red', 'druidcat2_artifact2armor_red', NULL, -1, 0, 0, 0, 0, 0),
(90221, 90204, 0, 0, 1.0, 255, 'druidcat2_artifact3_blue', 'druidcat2_artifact3_glow_blue', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90222, 90204, 0, 0, 1.0, 255, 'druidcat2_artifact3_green', 'druidcat2_artifact3_glow_green', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90223, 90204, 0, 0, 1.0, 255, 'druidcat2_artifact3_orange', 'druidcat2_artifact3_glow_orange', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90224, 90204, 0, 0, 1.0, 255, 'druidcat2_artifact3_white', 'druidcat2_artifact3_glow_white', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90225, 90205, 0, 0, 1.0, 255, 'druidcat2_artifact4_green', 'druidcat2_artifact4armor_green', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90226, 90205, 0, 0, 1.0, 255, 'druidcat2_artifact4_orange', 'druidcat2_artifact4armor_orange', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90227, 90205, 0, 0, 1.0, 255, 'druidcat2_artifact4_purple', 'druidcat2_artifact4armor_purple', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90228, 90205, 0, 0, 1.0, 255, 'druidcat2_artifact4_white', 'druidcat2_artifact4armor_white', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90229, 90206, 0, 0, 1.0, 255, 'druidcat2_artifact5_blue', 'druidcat2_artifact5armor_blue', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90230, 90206, 0, 0, 1.0, 255, 'druidcat2_artifact5_green', 'druidcat2_artifact5armor_green', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90231, 90206, 0, 0, 1.0, 255, 'druidcat2_artifact5_orange', 'druidcat2_artifact5armor_orange', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90232, 90206, 0, 0, 1.0, 255, 'druidcat2_artifact5_red', 'druidcat2_artifact5armor_red', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90233, 90210, 0, 0, 1.0, 255, 'druidcatkultiran_brown', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90234, 90210, 0, 0, 1.0, 255, 'druidcatkultiran_dark', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90235, 90210, 0, 0, 1.0, 255, 'druidcatkultiran_green', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90236, 90210, 0, 0, 1.0, 255, 'druidcatkultiran_light', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90237, 90211, 0, 0, 1.0, 255, 'druidcatkultiran_noarmor_brown', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90238, 90211, 0, 0, 1.0, 255, 'druidcatkultiran_noarmor_dark', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90239, 90211, 0, 0, 1.0, 255, 'druidcatkultiran_noarmor_green', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90240, 90211, 0, 0, 1.0, 255, 'druidcatkultiran_noarmor_light', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90241, 90212, 0, 0, 1.0, 255, 'druidcatzandalaritroll_black', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90242, 90212, 0, 0, 1.0, 255, 'druidcatzandalaritroll_blue', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90243, 90212, 0, 0, 1.0, 255, 'druidcatzandalaritroll_green', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90244, 90212, 0, 0, 1.0, 255, 'druidcatzandalaritroll_white', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90245, 90213, 0, 0, 1.0, 255, 'druidcatzandalaritroll_noarmor_black', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90246, 90213, 0, 0, 1.0, 255, 'druidcatzandalaritroll_noarmor_blue', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90247, 90213, 0, 0, 1.0, 255, 'druidcatzandalaritroll_noarmor_green', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90248, 90213, 0, 0, 1.0, 255, 'druidcatzandalaritroll_noarmor_white', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90249, 90214, 0, 0, 1.0, 255, 'druidcat2_treeskin', NULL, NULL, NULL, 0, 0, 0, 0, 0, 0),
(90250, 3143, 0, 0, 1.0, 255, 'lynxskinpainted', 'LynxEyeGlow', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90300, 90300, 0, 0, 1.0, 255, 'druidowlbear2_ne', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90301, 90300, 0, 0, 1.0, 255, 'druidowlbear2_black', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90302, 90300, 0, 0, 1.0, 255, 'druidowlbear2_blue', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90303, 90300, 0, 0, 1.0, 255, 'druidowlbear2_raven', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90304, 90300, 0, 0, 1.0, 255, 'druidowlbear2_red', NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90305, 90301, 0, 0, 1.0, 255, 'druidowlbear2_ne', 'druidformsepicarmorallianceowlbear', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90306, 90301, 0, 0, 1.0, 255, 'druidowlbear2_black', 'druidformsepicarmorallianceowlbear', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90307, 90301, 0, 0, 1.0, 255, 'druidowlbear2_blue', 'druidformsepicarmorhordeowlbear', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90308, 90301, 0, 0, 1.0, 255, 'druidowlbear2_raven', 'druidformsepicarmorhordeowlbear', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90309, 90301, 0, 0, 1.0, 255, 'druidowlbear2_red', 'druidformsepicarmorhordeowlbear', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90310, 90302, 0, 0, 1.0, 255, NULL, NULL, NULL, NULL, -1, 0, 0, 0, 0, 0),
(90311, 90303, 0, 0, 1.0, 255, 'druidowlbear2_hmt', 'druidformsepicarmorhordeowlbear', 'druidowlbear2_hmt_horns', NULL, -1, 0, 0, 0, 0, 0),
(90312, 90304, 0, 0, 1.0, 255, 'druidowlbearkultiranepic2_body_black', 'druidowlbearkultiranepic2_armor_black', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90313, 90304, 0, 0, 1.0, 255, 'druidowlbearkultiranepic2_body_green', 'druidowlbearkultiranepic2_armor_green', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90314, 90304, 0, 0, 1.0, 255, 'druidowlbearkultiranepic2_body_pale', 'druidowlbearkultiranepic2_armor_pale', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90315, 90304, 0, 0, 1.0, 255, 'druidowlbearkultiranepic2_body_red', 'druidowlbearkultiranepic2_armor_red', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90316, 90305, 0, 0, 1.2000000476837158, 255, 'druidowlbearzandalariepic2_body', 'druidowlbearzandalariepic2_armor', NULL, NULL, -1, 0, 0, 0, 0, 0),
(90317, 90306, 0, 0, 1.0, 255, 'tindralmoonkin_body_blue', 'tindralmoonkin_antlers_5369290', 'tindralmoonkin_jewelry_blue', NULL, 0, 0, 0, 0, 0, 0),
(90318, 90307, 0, 0, 1.0, 255, 'tindralmoonkin_body_green', 'tindralmoonkin_antlers_5369295', 'tindralmoonkin_jewelry_green', NULL, 0, 0, 0, 0, 0, 0),
(90319, 90308, 0, 0, 1.0, 255, 'tindralmoonkin_body_blue', 'tindralmoonkin_antlers_5369293', 'tindralmoonkin_jewelry_blue', NULL, 0, 0, 0, 0, 0, 0),
(90320, 90309, 0, 0, 1.0, 255, 'tindralmoonkin_body_red', 'tindralmoonkin_antlers_5369291', 'tindralmoonkin_jewelry_red', NULL, 0, 0, 0, 0, 0, 0),
(90321, 90310, 0, 0, 1.0, 255, 'tindralmoonkin_body_gold', 'tindralmoonkin_antlers_5369294', 'tindralmoonkin_jewelry_gold', NULL, 0, 0, 0, 0, 0, 0);

-- ---- from rev_1790219389383634454.sql ----
-- Custom: the Bear Form appearance NPC (900012) now also offers Cat and Moonkin Form, under a generic script
-- (npc_shapeshift_appearance, src/server/scripts/Custom/custom_shapeshift_appearance.cpp).
UPDATE `creature_template` SET `subname` = 'Shapeshift Appearances', `ScriptName` = 'npc_shapeshift_appearance'
WHERE `entry` = 900012;

DELETE FROM `npc_text` WHERE `ID` = 900012;
INSERT INTO `npc_text` (`ID`, `text0_0`, `text0_1`, `Probability0`)
VALUES (900012, 'The wild wears many coats, and so may you. Choose the shape each of your forms will take.$B$BIf you speak to me while already shifted, you will see each choice as you make it.',
    'The wild wears many coats, and so may you. Choose the shape each of your forms will take.$B$BIf you speak to me while already shifted, you will see each choice as you make it.', 1);

-- ---- from rev_1790332047188777271.sql ----
-- Healing Training Dummy, combat variant (900013) + its invisible combat anchor (900014).
-- 900013 is 900011 with a different subname/ScriptName: healing it puts the healer in combat for
-- 2 minutes (src/server/scripts/Custom/custom_healing_dummy.cpp). 900014 is summoned by it on
-- demand - a hostile (faction 14), unattackable, unselectable, invisible (model 11686),
-- civilian+trigger passive creature that only exists to hold the PvE combat reference, since a
-- friendly creature can't be in combat with a player. type 10 (Not specified) - never healed.
-- No spawn: place 900013 with `.npc add 900013`.
-- No DELETE on creature_template (codestyle-sql.py `not_delete` list) - upsert instead.
INSERT INTO `creature_template` (`entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`, `KillCredit1`, `KillCredit2`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`, `faction`, `npcflag`, `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`, `dmgschool`, `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`, `unit_class`, `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`, `pickpocketloot`, `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`, `HoverHeight`, `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`, `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`, `VerifiedBuild`) VALUES
(900013, 0, 0, 0, 0, 0, 'Healing Training Dummy', 'In Combat (2 min)', '', 0, 80, 80, 0, 35, 0, 1, 1.14286, 1, 1, 20, 0, 0, 35, 2000, 2000, 1, 1, 1, 0, 2048, 0, 0, 7, 4100, 0, 0, 0, 0, 0, 0, 0, '', 0, 1, 23809.5, 1, 1, 1, 0, 0, 0, -26, 262144, 'npc_healing_dummy_combat', 0),
(900014, 0, 0, 0, 0, 0, 'Healing Dummy Combat Anchor', '', '', 0, 80, 80, 0, 14, 0, 1, 1.14286, 1, 1, 0, 0, 0, 35, 2000, 2000, 1, 1, 1, 33554946, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, '', 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 130, 'npc_healing_dummy_combat_anchor', 0) ON DUPLICATE KEY UPDATE `difficulty_entry_1` = VALUES(`difficulty_entry_1`), `difficulty_entry_2` = VALUES(`difficulty_entry_2`), `difficulty_entry_3` = VALUES(`difficulty_entry_3`), `KillCredit1` = VALUES(`KillCredit1`), `KillCredit2` = VALUES(`KillCredit2`), `name` = VALUES(`name`), `subname` = VALUES(`subname`), `IconName` = VALUES(`IconName`), `gossip_menu_id` = VALUES(`gossip_menu_id`), `minlevel` = VALUES(`minlevel`), `maxlevel` = VALUES(`maxlevel`), `exp` = VALUES(`exp`), `faction` = VALUES(`faction`), `npcflag` = VALUES(`npcflag`), `speed_walk` = VALUES(`speed_walk`), `speed_run` = VALUES(`speed_run`), `speed_swim` = VALUES(`speed_swim`), `speed_flight` = VALUES(`speed_flight`), `detection_range` = VALUES(`detection_range`), `rank` = VALUES(`rank`), `dmgschool` = VALUES(`dmgschool`), `DamageModifier` = VALUES(`DamageModifier`), `BaseAttackTime` = VALUES(`BaseAttackTime`), `RangeAttackTime` = VALUES(`RangeAttackTime`), `BaseVariance` = VALUES(`BaseVariance`), `RangeVariance` = VALUES(`RangeVariance`), `unit_class` = VALUES(`unit_class`), `unit_flags` = VALUES(`unit_flags`), `unit_flags2` = VALUES(`unit_flags2`), `dynamicflags` = VALUES(`dynamicflags`), `family` = VALUES(`family`), `type` = VALUES(`type`), `type_flags` = VALUES(`type_flags`), `lootid` = VALUES(`lootid`), `pickpocketloot` = VALUES(`pickpocketloot`), `skinloot` = VALUES(`skinloot`), `PetSpellDataId` = VALUES(`PetSpellDataId`), `VehicleId` = VALUES(`VehicleId`), `mingold` = VALUES(`mingold`), `maxgold` = VALUES(`maxgold`), `AIName` = VALUES(`AIName`), `MovementType` = VALUES(`MovementType`), `HoverHeight` = VALUES(`HoverHeight`), `HealthModifier` = VALUES(`HealthModifier`), `ManaModifier` = VALUES(`ManaModifier`), `ArmorModifier` = VALUES(`ArmorModifier`), `ExperienceModifier` = VALUES(`ExperienceModifier`), `RacialLeader` = VALUES(`RacialLeader`), `movementId` = VALUES(`movementId`), `RegenHealth` = VALUES(`RegenHealth`), `CreatureImmunitiesId` = VALUES(`CreatureImmunitiesId`), `flags_extra` = VALUES(`flags_extra`), `ScriptName` = VALUES(`ScriptName`), `VerifiedBuild` = VALUES(`VerifiedBuild`);

DELETE FROM `creature_template_model` WHERE `CreatureID` IN (900013, 900014);
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`) VALUES
(900013, 0, 3019, 1, 1, 0),
(900014, 0, 11686, 1, 1, 0);

-- ---- from rev_1790370889460479803.sql ----
DELETE FROM `spellvisual_dbc` WHERE `ID` BETWEEN 90018 AND 90020;
INSERT INTO `spellvisual_dbc` (`ID`, `PrecastKit`, `CastKit`, `ImpactKit`, `StateKit`, `StateDoneKit`, `ChannelKit`, `HasMissile`, `MissileModel`, `MissilePathType`, `MissileDestinationAttachment`, `MissileSound`, `AnimEventSoundID`, `Flags`, `CasterImpactKit`, `TargetImpactKit`, `MissileAttachment`, `MissileFollowGroundHeight`, `MissileFollowGroundDropSpeed`, `MissileFollowGroundApproach`, `MissileFollowGroundFlags`, `MissileMotion`, `MissileTargetingKit`, `InstantAreaKit`, `ImpactAreaKit`, `PersistentAreaKit`, `MissileCastOffsetX`, `MissileCastOffsetY`, `MissileCastOffsetZ`, `MissileImpactOffsetX`, `MissileImpactOffsetY`, `MissileImpactOffsetZ`) VALUES
(90018, 90018, 90019, 0, 0, 0, 0, 1, 90018, 0, 34, 0, 0, 512, 0, 90020, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90019, 0, 90021, 0, 90022, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90020, 0, 0, 90023, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);

-- ---- carried over from the squashed generate.py files ----
-- Pruned in an unapplied generate.py file after an applied one had inserted it; the regenerated
-- file no longer knows the row ever existed, so the DELETE has to be kept by hand.
DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN ((1082, 'spell_dru_berserk_combo_points'));
-- Ferocity (796) was moved by an earlier generate.py file and has since been moved back to its stock
-- position, which generate.py treats as "unchanged" and no longer emits - the stale override row
-- would otherwise stay live. Dropping it lets the stock Talent.dbc row apply.
DELETE FROM `talent_dbc` WHERE `ID` = 796;
