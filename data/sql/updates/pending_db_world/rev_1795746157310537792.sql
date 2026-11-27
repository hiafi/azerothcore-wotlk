DELETE FROM `spellvisual_dbc` WHERE `ID` BETWEEN 90750 AND 90753;
INSERT INTO `spellvisual_dbc` (`ID`, `PrecastKit`, `CastKit`, `ImpactKit`, `StateKit`, `StateDoneKit`, `ChannelKit`, `HasMissile`, `MissileModel`, `MissilePathType`, `MissileDestinationAttachment`, `MissileSound`, `AnimEventSoundID`, `Flags`, `CasterImpactKit`, `TargetImpactKit`, `MissileAttachment`, `MissileFollowGroundHeight`, `MissileFollowGroundDropSpeed`, `MissileFollowGroundApproach`, `MissileFollowGroundFlags`, `MissileMotion`, `MissileTargetingKit`, `InstantAreaKit`, `ImpactAreaKit`, `PersistentAreaKit`, `MissileCastOffsetX`, `MissileCastOffsetY`, `MissileCastOffsetZ`, `MissileImpactOffsetX`, `MissileImpactOffsetY`, `MissileImpactOffsetZ`) VALUES
(90750, 726, 37, 813, 0, 0, 0, 1, 675, 2, 1, 3015, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
(90751, 0, 0, 0, 90751, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90752, 90752, 6909, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1485, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
(90753, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 90753, 0, 0, 0, 0, 0, 0, 0, 0);

DELETE FROM `creaturemodeldata_dbc` WHERE `ID` BETWEEN 90850 AND 90856;
INSERT INTO `creaturemodeldata_dbc` (`ID`, `Flags`, `ModelName`, `SizeClass`, `ModelScale`, `BloodID`, `FootprintTextureID`, `FootprintTextureLength`, `FootprintTextureWidth`, `FootprintParticleScale`, `FoleyMaterialID`, `FootstepShakeSize`, `DeathThudShakeSize`, `SoundID`, `CollisionWidth`, `CollisionHeight`, `MountHeight`, `GeoBoxMinX`, `GeoBoxMinY`, `GeoBoxMinZ`, `GeoBoxMaxX`, `GeoBoxMaxY`, `GeoBoxMaxZ`, `WorldEffectScale`, `AttachedEffectScale`, `MissileCollisionRadius`, `MissileCollisionPush`, `MissileCollisionRaise`) VALUES
(90850, 0, 'SPELLS\\target_nature_state_projected.mdx', 1, 1.0, 1, 0, 0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 1.0, 0, 0, 0),
(90853, 0, 'SPELLS\\gnomer_numeral_one.mdx', 1, 1.0, 1, 0, 0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 1.0, 0, 0, 0),
(90854, 0, 'SPELLS\\gnomer_numeral_two.mdx', 1, 1.0, 1, 0, 0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 1.0, 0, 0, 0),
(90855, 0, 'SPELLS\\gnomer_numeral_three.mdx', 1, 1.0, 1, 0, 0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 1.0, 0, 0, 0),
(90856, 0, 'SPELLS\\custom_cone_white.mdx', 1, 1.0, 1, 0, 0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 1.0, 0, 0, 0);

DELETE FROM `creaturedisplayinfo_dbc` WHERE `ID` BETWEEN 90850 AND 90856;
INSERT INTO `creaturedisplayinfo_dbc` (`ID`, `ModelID`, `SoundID`, `ExtendedDisplayInfoID`, `CreatureModelScale`, `CreatureModelAlpha`, `TextureVariation_1`, `TextureVariation_2`, `TextureVariation_3`, `PortraitTextureName`, `BloodLevel`, `BloodID`, `NPCSoundID`, `ParticleColorID`, `CreatureGeosetData`, `ObjectEffectPackageID`) VALUES
(90850, 90850, 0, 0, 1.0, 255, '', '', '', '', 1, 0, 0, 0, 0, 0),
(90851, 851, 0, 0, 0.5, 255, 'GnomeSpiderTankSkinGreen', '', '', '', -1, 0, 0, 0, 0, 0),
(90852, 851, 0, 0, 0.5, 255, 'GnomeSpiderTankSkinBlue', '', '', '', -1, 0, 0, 0, 0, 0),
(90853, 90853, 0, 0, 1.0, 255, 'gnomer_numeral_one', '', '', '', 1, 0, 0, 0, 0, 0),
(90854, 90854, 0, 0, 1.0, 255, 'gnomer_numeral_two', '', '', '', 1, 0, 0, 0, 0, 0),
(90855, 90855, 0, 0, 1.0, 255, 'gnomer_numeral_three', '', '', '', 1, 0, 0, 0, 0, 0),
(90856, 90856, 0, 0, 1.0, 255, '', '', '', '', 1, 0, 0, 0, 0, 0);

DELETE FROM `creature_model_info` WHERE `DisplayID` IN (90850, 90851, 90852, 90853, 90854, 90855, 90856);
INSERT INTO `creature_model_info` (`DisplayID`, `BoundingRadius`, `CombatReach`, `Gender`, `DisplayID_Other_Gender`) VALUES
(90850, 0.5, 0.5, 2, 0),
(90851, 0.75, 1.0, 2, 0),
(90852, 0.75, 1.0, 2, 0),
(90853, 0.5, 0.5, 2, 0),
(90854, 0.5, 0.5, 2, 0),
(90855, 0.5, 0.5, 2, 0),
(90856, 0.5, 0.5, 2, 0);
