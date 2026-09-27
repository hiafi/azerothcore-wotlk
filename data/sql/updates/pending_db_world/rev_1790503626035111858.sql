-- Druid SpellVisual overlay (apps/dbc-tools/patch_druid_vfx_models.py --sql-out): Starsurge/Fury of Elune
-- (90018-90020, unchanged) plus the Resto Flourish/Bloom visuals (90021-90024).
DELETE FROM `spellvisual_dbc` WHERE `ID` BETWEEN 90018 AND 90024;
INSERT INTO `spellvisual_dbc` (`ID`, `PrecastKit`, `CastKit`, `ImpactKit`, `StateKit`, `StateDoneKit`, `ChannelKit`, `HasMissile`, `MissileModel`, `MissilePathType`, `MissileDestinationAttachment`, `MissileSound`, `AnimEventSoundID`, `Flags`, `CasterImpactKit`, `TargetImpactKit`, `MissileAttachment`, `MissileFollowGroundHeight`, `MissileFollowGroundDropSpeed`, `MissileFollowGroundApproach`, `MissileFollowGroundFlags`, `MissileMotion`, `MissileTargetingKit`, `InstantAreaKit`, `ImpactAreaKit`, `PersistentAreaKit`, `MissileCastOffsetX`, `MissileCastOffsetY`, `MissileCastOffsetZ`, `MissileImpactOffsetX`, `MissileImpactOffsetY`, `MissileImpactOffsetZ`) VALUES
(90018, 90018, 90019, 0, 0, 0, 0, 1, 90018, 0, 34, 0, 0, 512, 0, 90020, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90019, 0, 90021, 0, 90022, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90020, 0, 0, 90023, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90021, 0, 183, 10691, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90022, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 90024, 0, 0, 0, 0, 0, 0),
(90023, 0, 183, 10693, 0, 0, 0, 1, 90023, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 224, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90024, 0, 0, 10693, 0, 0, 0, 1, 90023, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 224, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
