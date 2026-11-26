DELETE FROM `spellvisual_dbc` WHERE `ID` BETWEEN 90700 AND 90707;
INSERT INTO `spellvisual_dbc` (`ID`, `PrecastKit`, `CastKit`, `ImpactKit`, `StateKit`, `StateDoneKit`, `ChannelKit`, `HasMissile`, `MissileModel`, `MissilePathType`, `MissileDestinationAttachment`, `MissileSound`, `AnimEventSoundID`, `Flags`, `CasterImpactKit`, `TargetImpactKit`, `MissileAttachment`, `MissileFollowGroundHeight`, `MissileFollowGroundDropSpeed`, `MissileFollowGroundApproach`, `MissileFollowGroundFlags`, `MissileMotion`, `MissileTargetingKit`, `InstantAreaKit`, `ImpactAreaKit`, `PersistentAreaKit`, `MissileCastOffsetX`, `MissileCastOffsetY`, `MissileCastOffsetZ`, `MissileImpactOffsetX`, `MissileImpactOffsetY`, `MissileImpactOffsetZ`) VALUES
(90700, 0, 0, 0, 90700, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90701, 0, 0, 0, 90701, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90702, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 9161, 0, 0, 0, 0, 0, 0, 0, 0),
(90703, 0, 0, 0, 90703, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90704, 0, 0, 0, 0, 0, 90704, 1, 0, 0, 1, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
(90705, 90705, 90711, 282, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
(90706, 90706, 90712, 813, 0, 0, 0, 1, 675, 0, 1, 3015, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
(90707, 0, 0, 0, 90707, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);

DELETE FROM `creaturemodeldata_dbc` WHERE `ID` BETWEEN 90830 AND 90832;
INSERT INTO `creaturemodeldata_dbc` (`ID`, `Flags`, `ModelName`, `SizeClass`, `ModelScale`, `BloodID`, `FootprintTextureID`, `FootprintTextureLength`, `FootprintTextureWidth`, `FootprintParticleScale`, `FoleyMaterialID`, `FootstepShakeSize`, `DeathThudShakeSize`, `SoundID`, `CollisionWidth`, `CollisionHeight`, `MountHeight`, `GeoBoxMinX`, `GeoBoxMinY`, `GeoBoxMinZ`, `GeoBoxMaxX`, `GeoBoxMaxY`, `GeoBoxMaxZ`, `WorldEffectScale`, `AttachedEffectScale`, `MissileCollisionRadius`, `MissileCollisionPush`, `MissileCollisionRaise`) VALUES
(90830, 0, 'SPELLS\\target_water_state_projected.mdx', 1, 1.0, 1, 0, 0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 1.0, 0, 0, 0),
(90831, 0, 'SPELLS\\target_frost_state_projected.mdx', 1, 1.0, 1, 0, 0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 1.0, 0, 0, 0),
(90832, 0, 'SPELLS\\target_lightning_state_projected.mdx', 1, 1.0, 1, 0, 0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 1.0, 0, 0, 0);

DELETE FROM `creaturedisplayinfo_dbc` WHERE `ID` BETWEEN 90830 AND 90832;
INSERT INTO `creaturedisplayinfo_dbc` (`ID`, `ModelID`, `SoundID`, `ExtendedDisplayInfoID`, `CreatureModelScale`, `CreatureModelAlpha`, `TextureVariation_1`, `TextureVariation_2`, `TextureVariation_3`, `PortraitTextureName`, `BloodLevel`, `BloodID`, `NPCSoundID`, `ParticleColorID`, `CreatureGeosetData`, `ObjectEffectPackageID`) VALUES
(90830, 90830, 0, 0, 1.0, 255, '', '', '', '', 1, 0, 0, 0, 0, 0),
(90831, 90831, 0, 0, 1.0, 255, '', '', '', '', 1, 0, 0, 0, 0, 0),
(90832, 90832, 0, 0, 1.0, 255, '', '', '', '', 1, 0, 0, 0, 0, 0);

DELETE FROM `creature_model_info` WHERE `DisplayID` IN (90830, 90831, 90832);
INSERT INTO `creature_model_info` (`DisplayID`, `BoundingRadius`, `CombatReach`, `Gender`, `DisplayID_Other_Gender`) VALUES
(90830, 0.5, 0.5, 2, 0),
(90831, 0.5, 0.5, 2, 0),
(90832, 0.5, 0.5, 2, 0);
UPDATE `creature_model_info` SET `BoundingRadius` = 0.3672, `CombatReach` = 1.8 WHERE `DisplayID` = 6697;
UPDATE `creature_model_info` SET `BoundingRadius` = 0.7, `CombatReach` = 0.8 WHERE `DisplayID` = 25175;
UPDATE `creature_model_info` SET `BoundingRadius` = 0.306, `CombatReach` = 1.5 WHERE `DisplayID` = 29716;
UPDATE `creature_model_info` SET `BoundingRadius` = 0.3, `CombatReach` = 0.5 WHERE `DisplayID` = 26252;
