-- Blackrock Depths build WP-IT: the event items (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md
-- s3.3, s3.7, s7 #15 / #17; build spec docs/dungeons/blackrock-depths-2-shadowforge-city.md "Loot" (Vault Treasure
-- Bag, Cinder of the Firelord), "Fineous Darkvire" (the Guzzler rope), "Relic Coffer" keys; rulings 32-36, 43-45, 67,
-- 81-84). The items' table is apps/dbc-tools source/items/blackrock_depths_event_items.py, their client Item.dbc and
-- server item_dbc rows source/items.csv 70620-70623, the use spells 211260 / 211261 source/npcs/blackrock_depths/
-- event_items.py. The class, subclass, display, material and sheath below match the items.csv rows (the server's
-- DBC.EnforceItemAttributes resets item_template to them). Upserts: item_template rows are never deleted
-- (codestyle-sql not_delete).

-- Vault Treasure Bag 70620 (normal Vault) and 70623 (heroic Vault), Cinder of the Firelord 70621, Guzzler Rope 70622.
-- The bags are Flags 4 (ITEM_FLAG_HAS_LOOT, they open with a right click) like the stock Fat Sack of Coins 11937 and
-- Sack of Gems 11938, green so the group rolls on them, 20 to 60 gold (minMoneyLoot / maxMoneyLoot, copper); the
-- heroic bag is its own entry because an item's loot cannot know the difficulty it dropped on (its second gem is the
-- spec's "heroic 2"). The Cinder: green, unique (maxcount 1), Bind none, not map-limited (a group keeps it for a later
-- run), use spell 211260, consumed on use (spellcharges_1 -1). The rope: white (anyone may loot it), unique, Map 230 so
-- it leaves with its owner, use spell 211261, consumed on use.
INSERT INTO `item_template` (`entry`, `class`, `subclass`, `SoundOverrideSubclass`, `name`, `displayid`, `Quality`,
    `Flags`, `BuyCount`, `BuyPrice`, `SellPrice`, `InventoryType`, `AllowableClass`, `AllowableRace`, `ItemLevel`,
    `RequiredLevel`, `maxcount`, `stackable`, `spellid_1`, `spelltrigger_1`, `spellcharges_1`, `spellppmRate_1`,
    `spellcooldown_1`, `spellcategory_1`, `spellcategorycooldown_1`, `bonding`, `description`, `Material`, `sheath`,
    `minMoneyLoot`, `maxMoneyLoot`, `Map`, `VerifiedBuild`) VALUES
(70620, 15, 0, -1, 'Vault Treasure Bag', 1168, 2, 4, 1, 0,
    100, 0, -1, -1, 55, 0, 0, 1, 0, 0, 0, 0, -1, 0, -1, 0,
    'The Black Vault''s spoils, heavy and sealed. Open it for gold and a cut gem.',
    3, 0, 200000, 600000, 0, 0),
(70621, 15, 4, -1, 'Cinder of the Firelord', 12736, 2, 0, 1, 0,
    0, 0, -1, -1, 60, 0, 1, 1, 211260, 0, -1, 0, -1, 0, -1, 0,
    'A coal of the fire that will not die. Cast it into the lava at Lord Incendius''s island.',
    -1, 0, 0, 0, 0, 0),
(70622, 15, 4, -1, 'Guzzler Rope', 10301, 1, 0, 1, 0,
    0, 0, -1, -1, 55, 0, 1, 1, 211261, 0, -1, 0, -1, 0, -1, 0,
    'A coil of climbing rope from the Grim Guzzler''s supplies. It needs a place to hang.',
    -1, 0, 0, 0, 230, 0),
(70623, 15, 0, -1, 'Vault Treasure Bag', 4056, 2, 4, 1, 0,
    100, 0, -1, -1, 60, 0, 0, 1, 0, 0, 0, 0, -1, 0, -1, 0,
    'The Black Vault''s spoils, heavy and sealed. Open it for gold and two cut gems.',
    3, 0, 200000, 600000, 0, 0)
    ON DUPLICATE KEY UPDATE `class` = VALUES(`class`), `subclass` = VALUES(`subclass`),
    `SoundOverrideSubclass` = VALUES(`SoundOverrideSubclass`), `name` = VALUES(`name`),
    `displayid` = VALUES(`displayid`), `Quality` = VALUES(`Quality`), `Flags` = VALUES(`Flags`),
    `SellPrice` = VALUES(`SellPrice`), `InventoryType` = VALUES(`InventoryType`), `ItemLevel` = VALUES(`ItemLevel`),
    `RequiredLevel` = VALUES(`RequiredLevel`), `maxcount` = VALUES(`maxcount`), `stackable` = VALUES(`stackable`),
    `spellid_1` = VALUES(`spellid_1`), `spelltrigger_1` = VALUES(`spelltrigger_1`),
    `spellcharges_1` = VALUES(`spellcharges_1`), `spellcooldown_1` = VALUES(`spellcooldown_1`),
    `spellcategory_1` = VALUES(`spellcategory_1`), `spellcategorycooldown_1` = VALUES(`spellcategorycooldown_1`),
    `bonding` = VALUES(`bonding`), `description` = VALUES(`description`), `Material` = VALUES(`Material`),
    `sheath` = VALUES(`sheath`), `minMoneyLoot` = VALUES(`minMoneyLoot`), `maxMoneyLoot` = VALUES(`maxMoneyLoot`),
    `Map` = VALUES(`Map`);

-- The bags' gems: one shared pool, reference 1701100 (ids.yaml event_loot_reference), one gem per roll, every roll
-- equal over the 37 C5 rare cuts (Chance 0 rows share the group equally; apps/dbc-tools lib/crafting_gems_data.py
-- items 70720-70756). The normal bag rolls the pool once, the heroic bag twice (MaxCount 2 on a reference row is the
-- number of rolls; the same gem can come up twice). item_loot_template's key is (Entry, Item), so the same gem cannot
-- sit in two groups of one bag. Gold is item_template min / max money loot.
DELETE FROM `reference_loot_template` WHERE `Entry` = 1701100;
INSERT INTO `reference_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`, `GroupId`,
    `MinCount`, `MaxCount`, `Comment`) VALUES
(1701100, 70720, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Bold Star Ruby'),
(1701100, 70721, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Delicate Star Ruby'),
(1701100, 70722, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Brilliant Star Ruby'),
(1701100, 70723, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Sparkling Star Ruby'),
(1701100, 70724, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Smooth Azerothian Diamond'),
(1701100, 70725, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Quick Azerothian Diamond'),
(1701100, 70726, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Fractured Azerothian Diamond'),
(1701100, 70727, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Mystic Azerothian Diamond'),
(1701100, 70728, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Fortunate Blue Sapphire'),
(1701100, 70729, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Tireless Blue Sapphire'),
(1701100, 70730, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Lustrous Blue Sapphire'),
(1701100, 70731, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Shielded Blue Sapphire'),
(1701100, 70732, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Subtle Blue Sapphire'),
(1701100, 70733, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Flashing Blue Sapphire'),
(1701100, 70734, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Inscribed Large Opal'),
(1701100, 70735, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Fierce Large Opal'),
(1701100, 70736, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Etched Large Opal'),
(1701100, 70737, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Deadly Large Opal'),
(1701100, 70738, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Deft Large Opal'),
(1701100, 70739, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Glinting Large Opal'),
(1701100, 70740, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Potent Large Opal'),
(1701100, 70741, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Reckless Large Opal'),
(1701100, 70742, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Luminous Large Opal'),
(1701100, 70743, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Stalwart Dusk Amethyst'),
(1701100, 70744, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Defender''s Dusk Amethyst'),
(1701100, 70745, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Nimble Dusk Amethyst'),
(1701100, 70746, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Regal Dusk Amethyst'),
(1701100, 70747, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Royal Dusk Amethyst'),
(1701100, 70748, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Purified Dusk Amethyst'),
(1701100, 70749, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Jagged Huge Emerald'),
(1701100, 70750, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Forceful Huge Emerald'),
(1701100, 70751, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Radiant Huge Emerald'),
(1701100, 70752, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Vivid Huge Emerald'),
(1701100, 70753, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Misty Huge Emerald'),
(1701100, 70754, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Energized Huge Emerald'),
(1701100, 70755, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Intricate Huge Emerald'),
(1701100, 70756, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag gems - Steady Huge Emerald');
DELETE FROM `item_loot_template` WHERE `Entry` IN (70620, 70623);
INSERT INTO `item_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`, `GroupId`,
    `MinCount`, `MaxCount`, `Comment`) VALUES
(70620, 1701100, 1701100, 100, 0, 1, 0, 1, 1, 'Vault Treasure Bag - one gem (reference 1701100)'),
(70623, 1701100, 1701100, 100, 0, 1, 0, 2, 2, 'Vault Treasure Bag (heroic) - two gems (reference 1701100)');

-- The stock keys (ruling 35). Quality green (2) so the group rolls on them; they still do not bind and stack to 20 / 1
-- as before. Quality is no Item.dbc field, so there is no client patch. Relic Coffer Key 11078 drops at 1% from every
-- stock source (the stock 2 to 10.4% on 30 creature loot rows), except the six Dark Keepers, who drop one at 100%
-- instead of the Dark Keeper Key (ruling 36; their 11197 rows go). The 5% Dark Keeper Key rows on the eleven Dark Iron
-- dwarf bosses and the Emperor hard mode's 100% row are L-1's.
UPDATE `item_template` SET `Quality` = 2 WHERE `entry` IN (11078, 11197);
-- The Dark Keeper Key is not used up by opening the Dark Coffer (user 2026-11-17): the instance takes it from the
-- opener only when the Vault completes. Stock -1 charges made spell 13564 consume it on use.
UPDATE `item_template` SET `spellcharges_1` = 0 WHERE `entry` = 11197;
UPDATE `creature_loot_template` SET `Chance` = 1 WHERE `Item` = 11078 AND `Reference` = 0
    AND `Entry` NOT IN (9437, 9438, 9439, 9441, 9442, 9443);
UPDATE `creature_loot_template` SET `Chance` = 100 WHERE `Item` = 11078 AND `Reference` = 0
    AND `Entry` IN (9437, 9438, 9439, 9441, 9442, 9443);
DELETE FROM `creature_loot_template` WHERE `Item` = 11197 AND `Entry` IN (9437, 9438, 9439, 9441, 9442, 9443);
