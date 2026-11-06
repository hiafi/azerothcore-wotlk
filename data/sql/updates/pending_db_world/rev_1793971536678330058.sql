DELETE FROM `spellvisual_dbc` WHERE `ID` BETWEEN 90340 AND 90344;
INSERT INTO `spellvisual_dbc` (`ID`, `PrecastKit`, `CastKit`, `ImpactKit`, `StateKit`, `StateDoneKit`, `ChannelKit`, `HasMissile`, `MissileModel`, `MissilePathType`, `MissileDestinationAttachment`, `MissileSound`, `AnimEventSoundID`, `Flags`, `CasterImpactKit`, `TargetImpactKit`, `MissileAttachment`, `MissileFollowGroundHeight`, `MissileFollowGroundDropSpeed`, `MissileFollowGroundApproach`, `MissileFollowGroundFlags`, `MissileMotion`, `MissileTargetingKit`, `InstantAreaKit`, `ImpactAreaKit`, `PersistentAreaKit`, `MissileCastOffsetX`, `MissileCastOffsetY`, `MissileCastOffsetZ`, `MissileImpactOffsetX`, `MissileImpactOffsetY`, `MissileImpactOffsetZ`) VALUES
(90340, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 90340, 0, 0, 0, 0, 0, 0),
(90341, 0, 0, 0, 90341, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90342, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 90342, 0, 0, 0, 0, 0, 0),
(90343, 0, 0, 0, 90343, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90344, 10205, 0, 90344, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);

DELETE FROM `creaturemodeldata_dbc` WHERE `ID` BETWEEN 90700 AND 90700;
INSERT INTO `creaturemodeldata_dbc` (`ID`, `Flags`, `ModelName`, `SizeClass`, `ModelScale`, `BloodID`, `FootprintTextureID`, `FootprintTextureLength`, `FootprintTextureWidth`, `FootprintParticleScale`, `FoleyMaterialID`, `FootstepShakeSize`, `DeathThudShakeSize`, `SoundID`, `CollisionWidth`, `CollisionHeight`, `MountHeight`, `GeoBoxMinX`, `GeoBoxMinY`, `GeoBoxMinZ`, `GeoBoxMaxX`, `GeoBoxMaxY`, `GeoBoxMaxZ`, `WorldEffectScale`, `AttachedEffectScale`, `MissileCollisionRadius`, `MissileCollisionPush`, `MissileCollisionRaise`) VALUES
(90700, 0, 'Creature\\DemolisherCannonball\\DemolisherCannonball.mdx', 1, 1.0, 1, 0, 0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 1.0, 0, 0, 0);

DELETE FROM `creaturedisplayinfo_dbc` WHERE `ID` BETWEEN 90700 AND 90700;
INSERT INTO `creaturedisplayinfo_dbc` (`ID`, `ModelID`, `SoundID`, `ExtendedDisplayInfoID`, `CreatureModelScale`, `CreatureModelAlpha`, `TextureVariation_1`, `TextureVariation_2`, `TextureVariation_3`, `PortraitTextureName`, `BloodLevel`, `BloodID`, `NPCSoundID`, `ParticleColorID`, `CreatureGeosetData`, `ObjectEffectPackageID`) VALUES
(90700, 90700, 0, 0, 1.0, 255, '', '', '', '', 1, 0, 0, 0, 0, 0);

DELETE FROM `gameobjectdisplayinfo_dbc` WHERE `ID` BETWEEN 90020 AND 90020;
INSERT INTO `gameobjectdisplayinfo_dbc` (`ID`, `ModelName`, `Sound_1`, `Sound_2`, `Sound_3`, `Sound_4`, `Sound_5`, `Sound_6`, `Sound_7`, `Sound_8`, `Sound_9`, `Sound_10`, `GeoBoxMinX`, `GeoBoxMinY`, `GeoBoxMinZ`, `GeoBoxMaxX`, `GeoBoxMaxY`, `GeoBoxMaxZ`, `ObjectEffectPackageID`) VALUES
(90020, 'World\\Expansion02\\Doodads\\DaggerCap\\BurningShip\\HF_BurningShip_Mast.M2', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -3.0151, -3.4469, -9.6157, 3.0151, 3.4469, 9.6158, 0);

DELETE FROM `creature_model_info` WHERE `DisplayID` = 90700;
INSERT INTO `creature_model_info` (`DisplayID`, `BoundingRadius`, `CombatReach`, `Gender`, `DisplayID_Other_Gender`) VALUES
(90700, 0.85, 1.0, 2, 0);
