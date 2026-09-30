-- DB update 2026_09_29_00 -> 2026_09_29_01
-- warlock-rework B9 item_template updates (apps/item-tools, not DSL-declarable)
-- warlock-rework B9 - Soul Pouch is an ordinary bag now (Soul Shard items removed)
UPDATE `item_template` SET `BagFamily` = 0 WHERE `entry` = 21340 AND `BagFamily` = 4;
-- warlock-rework B9 - Felcloth Bag is an ordinary bag now (Soul Shard items removed)
UPDATE `item_template` SET `BagFamily` = 0 WHERE `entry` = 21341 AND `BagFamily` = 4;
-- warlock-rework B9 - Core Felcloth Bag is an ordinary bag now (Soul Shard items removed)
UPDATE `item_template` SET `BagFamily` = 0 WHERE `entry` = 21342 AND `BagFamily` = 4;
-- warlock-rework B9 - Ebon Shadowbag is an ordinary bag now (Soul Shard items removed)
UPDATE `item_template` SET `BagFamily` = 0 WHERE `entry` = 21872 AND `BagFamily` = 4;
-- warlock-rework B9 - Small Soul Pouch is an ordinary bag now (Soul Shard items removed)
UPDATE `item_template` SET `BagFamily` = 0 WHERE `entry` = 22243 AND `BagFamily` = 4;
-- warlock-rework B9 - Box of Souls is an ordinary bag now (Soul Shard items removed)
UPDATE `item_template` SET `BagFamily` = 0 WHERE `entry` = 22244 AND `BagFamily` = 4;
-- warlock-rework B9 - Abyssal Bag is an ordinary bag now (Soul Shard items removed)
UPDATE `item_template` SET `BagFamily` = 0 WHERE `entry` = 41597 AND `BagFamily` = 4;

-- warlock-rework VFX: Hand of Gul'dan / Burning Rush spell visuals (apps/dbc-tools/patch_warlock_vfx_models.py --sql-out)
DELETE FROM `spellvisual_dbc` WHERE `ID` BETWEEN 90025 AND 90026;
INSERT INTO `spellvisual_dbc` (`ID`, `PrecastKit`, `CastKit`, `ImpactKit`, `StateKit`, `StateDoneKit`, `ChannelKit`, `HasMissile`, `MissileModel`, `MissilePathType`, `MissileDestinationAttachment`, `MissileSound`, `AnimEventSoundID`, `Flags`, `CasterImpactKit`, `TargetImpactKit`, `MissileAttachment`, `MissileFollowGroundHeight`, `MissileFollowGroundDropSpeed`, `MissileFollowGroundApproach`, `MissileFollowGroundFlags`, `MissileMotion`, `MissileTargetingKit`, `InstantAreaKit`, `ImpactAreaKit`, `PersistentAreaKit`, `MissileCastOffsetX`, `MissileCastOffsetY`, `MissileCastOffsetZ`, `MissileImpactOffsetX`, `MissileImpactOffsetY`, `MissileImpactOffsetZ`) VALUES
(90025, 6818, 6778, 90025, 0, 0, 0, 0, 0, 0, -1, 0, 0, 512, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(90026, 0, 0, 696, 235, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
