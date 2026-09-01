-- Frozen Orb's projectile creature (300001, npc_mage_frozen_orb - spell_mage.cpp) previously
-- borrowed the "Charged Sphere" model (CreatureDisplayID 26753, lifted from Ulduar's Summon
-- Charged Sphere - see rev_1787850093039268564.sql) as a stand-in. Swapping to the real "Ice Nuke
-- Missile" model (spells\IceNuke_Missile.mdx) real Frozen Orb itself flies as - that .mdx is
-- already a stock 3.3.5a asset (used by SpellVisualEffectName rows 4525/4526/4527, all "Ice Nuke
-- Missile" variants), but no stock CreatureModelData row points a *creature* at it, so - unlike
-- the SpellVisualID swap this session did for Glacial Spike - this one genuinely needs new IDs and
-- a client-side DBC patch (CreatureModelData.dbc/CreatureDisplayInfo.dbc are looked up client-side
-- by the raw DisplayID the server sends over the wire; there's no existing ID to just point at).
-- New IDs (90001/90001, clear of both tables' real max of 3440/32754 at the time this was written)
-- and the client patch itself came from apps/dbc-tools/patch_frozen_orb_model.py - see that
-- script's docstring for the full reasoning and how to regenerate this SQL.
DELETE FROM `creaturemodeldata_dbc` WHERE `ID` = 90001;
INSERT INTO `creaturemodeldata_dbc` (`ID`, `Flags`, `ModelName`, `SizeClass`, `ModelScale`, `BloodID`, `FootprintTextureID`, `FootprintTextureLength`, `FootprintTextureWidth`, `FootprintParticleScale`, `FoleyMaterialID`, `FootstepShakeSize`, `DeathThudShakeSize`, `SoundID`, `CollisionWidth`, `CollisionHeight`, `MountHeight`, `GeoBoxMinX`, `GeoBoxMinY`, `GeoBoxMinZ`, `GeoBoxMaxX`, `GeoBoxMaxY`, `GeoBoxMaxZ`, `WorldEffectScale`, `AttachedEffectScale`, `MissileCollisionRadius`, `MissileCollisionPush`, `MissileCollisionRaise`) VALUES (90001, 0, 'Spells\\IceNuke_Missile.mdx', 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);

DELETE FROM `creaturedisplayinfo_dbc` WHERE `ID` = 90001;
INSERT INTO `creaturedisplayinfo_dbc` (`ID`, `ModelID`, `SoundID`, `ExtendedDisplayInfoID`, `CreatureModelScale`, `CreatureModelAlpha`, `TextureVariation_1`, `TextureVariation_2`, `TextureVariation_3`, `PortraitTextureName`, `BloodLevel`, `BloodID`, `NPCSoundID`, `ParticleColorID`, `CreatureGeosetData`, `ObjectEffectPackageID`) VALUES (90001, 90001, 0, 0, 1.0, 255, NULL, NULL, NULL, NULL, 0, 0, 0, 0, 0, 0);

-- CollisionWidth/Height/MountHeight left at 0 (purely cosmetic display - the pulse damage is
-- spell-radius-based, not creature-collision-based; see 200008 Frozen Orb Pulse in mage.csv).
UPDATE `creature_template_model` SET `CreatureDisplayID` = 90001 WHERE `CreatureID` = 300001 AND `CreatureDisplayID` = 26753;
