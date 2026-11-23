DELETE FROM `spellvisual_dbc` WHERE `ID` BETWEEN 90550 AND 90564;
INSERT INTO `spellvisual_dbc` (`ID`, `PrecastKit`, `CastKit`, `ImpactKit`, `StateKit`, `StateDoneKit`, `ChannelKit`, `HasMissile`, `MissileModel`, `MissilePathType`, `MissileDestinationAttachment`, `MissileSound`, `AnimEventSoundID`, `Flags`, `CasterImpactKit`, `TargetImpactKit`, `MissileAttachment`, `MissileFollowGroundHeight`, `MissileFollowGroundDropSpeed`, `MissileFollowGroundApproach`, `MissileFollowGroundFlags`, `MissileMotion`, `MissileTargetingKit`, `InstantAreaKit`, `ImpactAreaKit`, `PersistentAreaKit`, `MissileCastOffsetX`, `MissileCastOffsetY`, `MissileCastOffsetZ`, `MissileImpactOffsetX`, `MissileImpactOffsetY`, `MissileImpactOffsetZ`) VALUES
(90550, 0, 0, 0, 90550, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90551, 0, 0, 0, 90551, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90552, 0, 0, 0, 90552, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90553, 0, 0, 0, 90553, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90554, 0, 0, 0, 90554, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90555, 0, 0, 0, 90555, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90556, 0, 0, 0, 90556, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90557, 0, 0, 0, 90557, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90558, 0, 0, 0, 90558, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90559, 0, 0, 0, 90559, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90560, 0, 0, 0, 90560, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90561, 0, 0, 0, 90561, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90562, 0, 0, 0, 90562, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90563, 0, 0, 0, 90563, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90564, 0, 0, 0, 90564, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);

DELETE FROM `creaturemodeldata_dbc` WHERE `ID` BETWEEN 90805 AND 90807;
INSERT INTO `creaturemodeldata_dbc` (`ID`, `Flags`, `ModelName`, `SizeClass`, `ModelScale`, `BloodID`, `FootprintTextureID`, `FootprintTextureLength`, `FootprintTextureWidth`, `FootprintParticleScale`, `FoleyMaterialID`, `FootstepShakeSize`, `DeathThudShakeSize`, `SoundID`, `CollisionWidth`, `CollisionHeight`, `MountHeight`, `GeoBoxMinX`, `GeoBoxMinY`, `GeoBoxMinZ`, `GeoBoxMaxX`, `GeoBoxMaxY`, `GeoBoxMaxZ`, `WorldEffectScale`, `AttachedEffectScale`, `MissileCollisionRadius`, `MissileCollisionPush`, `MissileCollisionRaise`) VALUES
(90805, 0, 'World\\Generic\\Human\\Passive Doodads\\Books\\BookLargeOpen02.mdx', 1, 1.0, 1, 0, 0, 0, 1.0, 0, 0, 0, 0, 0.9, 0.3, 0, 0, 0, 0, 0, 0, 0, 1.0, 1.0, 0, 0, 0),
(90806, 0, 'World\\Generic\\Human\\Passive Doodads\\Banners\\CrimsonBanner01.mdx', 1, 1.0, 1, 0, 0, 0, 1.0, 0, 0, 0, 0, 0.5, 4.6, 0, 0, 0, 0, 0, 0, 0, 1.0, 1.0, 0, 0, 0),
(90807, 0, 'Item\\ObjectComponents\\Weapon\\Axe_2H_War_C_01.mdx', 1, 1.0, 1, 0, 0, 0, 1.0, 0, 0, 0, 0, 0.5, 1.8, 0, 0, 0, 0, 0, 0, 0, 1.0, 1.0, 0, 0, 0);

DELETE FROM `creaturedisplayinfo_dbc` WHERE `ID` BETWEEN 90800 AND 90807;
INSERT INTO `creaturedisplayinfo_dbc` (`ID`, `ModelID`, `SoundID`, `ExtendedDisplayInfoID`, `CreatureModelScale`, `CreatureModelAlpha`, `TextureVariation_1`, `TextureVariation_2`, `TextureVariation_3`, `PortraitTextureName`, `BloodLevel`, `BloodID`, `NPCSoundID`, `ParticleColorID`, `CreatureGeosetData`, `ObjectEffectPackageID`) VALUES
(90800, 49, 0, 17548, 1.0, 128, '', '', '', '', 1, 0, 0, 0, 0, 0),
(90801, 49, 0, 17492, 1.0, 128, '', '', '', '', 1, 0, 0, 0, 0, 0),
(90802, 49, 0, 7338, 1.0, 128, '', '', '', '', 0, 0, 0, 0, 0, 0),
(90803, 49, 0, 17491, 1.0, 128, '', '', '', '', 1, 0, 0, 0, 0, 0),
(90804, 2254, 428, 0, 1.5, 140, 'MountedDeathKnightGoldRed_01', 'MountedDeathKnightGoldRed_02', 'MountedDeathKnightGoldRed_03', '', -1, 0, 0, 0, 0, 0),
(90805, 90805, 0, 0, 1.0, 255, '', '', '', '', 1, 0, 0, 0, 0, 0),
(90806, 90806, 0, 0, 1.0, 255, '', '', '', '', 1, 0, 0, 0, 0, 0),
(90807, 90807, 0, 0, 1.0, 255, '', '', '', '', 1, 0, 0, 0, 0, 0);

DELETE FROM `creature_model_info` WHERE `DisplayID` IN (90800, 90801, 90802, 90803, 90804, 90805, 90806, 90807);
INSERT INTO `creature_model_info` (`DisplayID`, `BoundingRadius`, `CombatReach`, `Gender`, `DisplayID_Other_Gender`) VALUES
(90800, 0.306, 1.5, 0, 0),
(90801, 0.306, 1.5, 0, 0),
(90802, 0.306, 1.5, 0, 0),
(90803, 0.306, 1.5, 0, 0),
(90804, 1.2, 3.0, 0, 0),
(90805, 0.5, 0.5, 2, 0),
(90806, 0.5, 1.0, 2, 0),
(90807, 0.5, 0.5, 2, 0);
