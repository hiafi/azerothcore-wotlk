-- Blackrock Spire build WP-B11: Solakar Flamewreath (10264), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.5 row B11; build spec
-- docs/dungeons/blackrock-spire-rework.md SP 3037-3110). His template (boss_solakar_flamewreath_rework, AIName '',
-- health, DamageModifier 3.5, immunity 1972, INSTANCE_BIND), the Rookery Guardian's and Hatcher's (C++, level 60,
-- 30,000 / 25,000 at 5 players), the flame whelp 300731 and his spells 210390-210414 are apps/dbc-tools
-- source/npcs/blackrock_spire/solakar.py. His loot rows are L-2's.

-- The pair is bound to C++ (SK2, SK3): the Guardian keeps Strike 15580 and Sunder Armor 15572 on the same timers and
-- adds Ground Stomp; the Hatcher keeps them too and stops hatching eggs on a timer (it snatches the flame instead).
-- Their "start attacking" row is the AIs' zone-in.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10258 AND `source_type` = 0;
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10683 AND `source_type` = 0;

-- The flame players toss (SK5; R-2 ruling 2026-11-15): Father Flame 70610, a new bag item (InventoryType 0, so it
-- is used from the bags: the stock 13371 is an off-hand the server will not use from the bags), its on-use the toss
-- 210391. Bind on Pickup, unique, Map 229 (the server takes it from anyone who leaves Blackrock Spire). The stock
-- 13371 stays untouched as the loot keepsake. The class, subclass, display, material and sheath match the
-- source/items.csv Item.dbc row (the server's DBC.EnforceItemAttributes resets item_template to them); both are
-- checked against apps/dbc-tools source/world/blackrock_spire_father_flame.py FATHER_FLAME. An upsert: item_template
-- rows are never deleted (codestyle-sql not_delete).
INSERT INTO `item_template` (`entry`, `class`, `subclass`, `SoundOverrideSubclass`, `name`, `displayid`, `Quality`,
    `Flags`, `BuyCount`, `BuyPrice`, `SellPrice`, `InventoryType`, `AllowableClass`, `AllowableRace`, `ItemLevel`,
    `RequiredLevel`, `maxcount`, `stackable`, `spellid_1`, `spelltrigger_1`, `spellcharges_1`, `spellppmRate_1`,
    `spellcooldown_1`, `spellcategory_1`, `spellcategorycooldown_1`, `bonding`, `description`, `Material`, `sheath`,
    `Map`, `VerifiedBuild`) VALUES
(70610, 15, 4, -1, 'Father Flame', 24061, 1, 0, 1, 0, 0, 0, -1, -1, 60, 0, 1, 1, 210391, 0, 0, 0, -1, 0, -1, 1,
    'The stolen flame of the Rookery. It burns the hand that holds it: toss it to an ally.', -1, 0, 229, 0)
    ON DUPLICATE KEY UPDATE `class` = VALUES(`class`), `subclass` = VALUES(`subclass`),
    `SoundOverrideSubclass` = VALUES(`SoundOverrideSubclass`), `name` = VALUES(`name`),
    `displayid` = VALUES(`displayid`), `Quality` = VALUES(`Quality`), `Flags` = VALUES(`Flags`),
    `InventoryType` = VALUES(`InventoryType`),
    `ItemLevel` = VALUES(`ItemLevel`), `RequiredLevel` = VALUES(`RequiredLevel`), `maxcount` = VALUES(`maxcount`),
    `stackable` = VALUES(`stackable`), `spellid_1` = VALUES(`spellid_1`), `spelltrigger_1` = VALUES(`spelltrigger_1`),
    `spellcharges_1` = VALUES(`spellcharges_1`), `spellcooldown_1` = VALUES(`spellcooldown_1`),
    `spellcategory_1` = VALUES(`spellcategory_1`), `spellcategorycooldown_1` = VALUES(`spellcategorycooldown_1`),
    `bonding` = VALUES(`bonding`), `description` = VALUES(`description`), `Material` = VALUES(`Material`),
    `sheath` = VALUES(`sheath`), `Map` = VALUES(`Map`);

-- Father Flame 175245 (SK1): taking it gives the flame (the holder aura and the item, no loot roll) and starts the
-- event; the stock go_father_flame stays registered, unbound by this row.
UPDATE `gameobject_template` SET `ScriptName` = 'go_brs_father_flame' WHERE `entry` = 175245;

-- His texts (SP "Text"; he had none, his stock Talk(0) had no row). The arrival is a yell (14); the rest are boss
-- emotes (41). The Hatcher keeps its stock line 0 and gains line 1.
DELETE FROM `creature_text` WHERE `CreatureID` = 10264 AND `GroupID` BETWEEN 0 AND 4;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10264, 0, 0, 'Thieves in the Rookery! Return the Father Flame, or burn with it!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Solakar Flamewreath - Arrival (SK1)'),
(10264, 1, 0, '%s hunts the flame!', 41, 0, 100, 0, 0, 0, 0, 0, 'Solakar Flamewreath - The Warden''s Hunt (SK9)'),
(10264, 2, 0, '%s reclaims Father Flame!', 41, 0, 100, 0, 0, 0, 0, 0, 'Solakar Flamewreath - Reclaim (SK8)'),
(10264, 3, 0, '%s is wreathed in flame!', 41, 0, 100, 0, 0, 0, 0, 0, 'Solakar Flamewreath - Wreathed in Flame (SK8)'),
(10264, 4, 0, '%s''s spear returns to him, bloodied.', 41, 0, 100, 0, 0, 0, 0, 0,
    'Solakar Flamewreath - Spear Wound torn (SK11)');

DELETE FROM `creature_text` WHERE `CreatureID` = 10683 AND `GroupID` = 1;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10683, 1, 0, '%s snatches Father Flame!', 41, 0, 100, 0, 0, 0, 0, 0, 'Rookery Hatcher - Snatch the Flame (SK2)');
