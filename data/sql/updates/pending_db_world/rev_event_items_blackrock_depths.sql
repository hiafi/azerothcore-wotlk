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

-- The bags' gems: each gem is its own roll (LootGroup), every roll equal over the 37 C5 rare cuts (Chance 0 rows share
-- the group equally; apps/dbc-tools lib/crafting_gems_data.py items 70720-70756). The normal bag has one group, the
-- heroic bag two (the same gem can come up twice). Gold is item_template min / max money loot.
DELETE FROM `item_loot_template` WHERE `Entry` IN (70620, 70623);
INSERT INTO `item_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`, `GroupId`,
    `MinCount`, `MaxCount`, `Comment`) VALUES
(70620, 70720, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Bold Star Ruby'),
(70620, 70721, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Delicate Star Ruby'),
(70620, 70722, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Brilliant Star Ruby'),
(70620, 70723, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Sparkling Star Ruby'),
(70620, 70724, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Smooth Azerothian Diamond'),
(70620, 70725, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Quick Azerothian Diamond'),
(70620, 70726, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Fractured Azerothian Diamond'),
(70620, 70727, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Mystic Azerothian Diamond'),
(70620, 70728, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Fortunate Blue Sapphire'),
(70620, 70729, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Tireless Blue Sapphire'),
(70620, 70730, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Lustrous Blue Sapphire'),
(70620, 70731, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Shielded Blue Sapphire'),
(70620, 70732, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Subtle Blue Sapphire'),
(70620, 70733, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Flashing Blue Sapphire'),
(70620, 70734, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Inscribed Large Opal'),
(70620, 70735, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Fierce Large Opal'),
(70620, 70736, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Etched Large Opal'),
(70620, 70737, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Deadly Large Opal'),
(70620, 70738, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Deft Large Opal'),
(70620, 70739, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Glinting Large Opal'),
(70620, 70740, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Potent Large Opal'),
(70620, 70741, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Reckless Large Opal'),
(70620, 70742, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Luminous Large Opal'),
(70620, 70743, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Stalwart Dusk Amethyst'),
(70620, 70744, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Defender''s Dusk Amethyst'),
(70620, 70745, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Nimble Dusk Amethyst'),
(70620, 70746, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Regal Dusk Amethyst'),
(70620, 70747, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Royal Dusk Amethyst'),
(70620, 70748, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Purified Dusk Amethyst'),
(70620, 70749, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Jagged Huge Emerald'),
(70620, 70750, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Forceful Huge Emerald'),
(70620, 70751, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Radiant Huge Emerald'),
(70620, 70752, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Vivid Huge Emerald'),
(70620, 70753, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Misty Huge Emerald'),
(70620, 70754, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Energized Huge Emerald'),
(70620, 70755, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Intricate Huge Emerald'),
(70620, 70756, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag - Steady Huge Emerald'),
(70623, 70720, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Bold Star Ruby (gem 1)'),
(70623, 70721, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Delicate Star Ruby (gem 1)'),
(70623, 70722, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Brilliant Star Ruby (gem 1)'),
(70623, 70723, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Sparkling Star Ruby (gem 1)'),
(70623, 70724, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Smooth Azerothian Diamond (gem 1)'),
(70623, 70725, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Quick Azerothian Diamond (gem 1)'),
(70623, 70726, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Fractured Azerothian Diamond (gem 1)'),
(70623, 70727, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Mystic Azerothian Diamond (gem 1)'),
(70623, 70728, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Fortunate Blue Sapphire (gem 1)'),
(70623, 70729, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Tireless Blue Sapphire (gem 1)'),
(70623, 70730, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Lustrous Blue Sapphire (gem 1)'),
(70623, 70731, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Shielded Blue Sapphire (gem 1)'),
(70623, 70732, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Subtle Blue Sapphire (gem 1)'),
(70623, 70733, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Flashing Blue Sapphire (gem 1)'),
(70623, 70734, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Inscribed Large Opal (gem 1)'),
(70623, 70735, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Fierce Large Opal (gem 1)'),
(70623, 70736, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Etched Large Opal (gem 1)'),
(70623, 70737, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Deadly Large Opal (gem 1)'),
(70623, 70738, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Deft Large Opal (gem 1)'),
(70623, 70739, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Glinting Large Opal (gem 1)'),
(70623, 70740, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Potent Large Opal (gem 1)'),
(70623, 70741, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Reckless Large Opal (gem 1)'),
(70623, 70742, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Luminous Large Opal (gem 1)'),
(70623, 70743, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Stalwart Dusk Amethyst (gem 1)'),
(70623, 70744, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Defender''s Dusk Amethyst (gem 1)'),
(70623, 70745, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Nimble Dusk Amethyst (gem 1)'),
(70623, 70746, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Regal Dusk Amethyst (gem 1)'),
(70623, 70747, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Royal Dusk Amethyst (gem 1)'),
(70623, 70748, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Purified Dusk Amethyst (gem 1)'),
(70623, 70749, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Jagged Huge Emerald (gem 1)'),
(70623, 70750, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Forceful Huge Emerald (gem 1)'),
(70623, 70751, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Radiant Huge Emerald (gem 1)'),
(70623, 70752, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Vivid Huge Emerald (gem 1)'),
(70623, 70753, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Misty Huge Emerald (gem 1)'),
(70623, 70754, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Energized Huge Emerald (gem 1)'),
(70623, 70755, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Intricate Huge Emerald (gem 1)'),
(70623, 70756, 0, 0, 0, 1, 1, 1, 1, 'Vault Treasure Bag (heroic) - Steady Huge Emerald (gem 1)'),
(70623, 70720, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Bold Star Ruby (gem 2)'),
(70623, 70721, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Delicate Star Ruby (gem 2)'),
(70623, 70722, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Brilliant Star Ruby (gem 2)'),
(70623, 70723, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Sparkling Star Ruby (gem 2)'),
(70623, 70724, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Smooth Azerothian Diamond (gem 2)'),
(70623, 70725, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Quick Azerothian Diamond (gem 2)'),
(70623, 70726, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Fractured Azerothian Diamond (gem 2)'),
(70623, 70727, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Mystic Azerothian Diamond (gem 2)'),
(70623, 70728, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Fortunate Blue Sapphire (gem 2)'),
(70623, 70729, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Tireless Blue Sapphire (gem 2)'),
(70623, 70730, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Lustrous Blue Sapphire (gem 2)'),
(70623, 70731, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Shielded Blue Sapphire (gem 2)'),
(70623, 70732, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Subtle Blue Sapphire (gem 2)'),
(70623, 70733, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Flashing Blue Sapphire (gem 2)'),
(70623, 70734, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Inscribed Large Opal (gem 2)'),
(70623, 70735, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Fierce Large Opal (gem 2)'),
(70623, 70736, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Etched Large Opal (gem 2)'),
(70623, 70737, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Deadly Large Opal (gem 2)'),
(70623, 70738, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Deft Large Opal (gem 2)'),
(70623, 70739, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Glinting Large Opal (gem 2)'),
(70623, 70740, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Potent Large Opal (gem 2)'),
(70623, 70741, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Reckless Large Opal (gem 2)'),
(70623, 70742, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Luminous Large Opal (gem 2)'),
(70623, 70743, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Stalwart Dusk Amethyst (gem 2)'),
(70623, 70744, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Defender''s Dusk Amethyst (gem 2)'),
(70623, 70745, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Nimble Dusk Amethyst (gem 2)'),
(70623, 70746, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Regal Dusk Amethyst (gem 2)'),
(70623, 70747, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Royal Dusk Amethyst (gem 2)'),
(70623, 70748, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Purified Dusk Amethyst (gem 2)'),
(70623, 70749, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Jagged Huge Emerald (gem 2)'),
(70623, 70750, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Forceful Huge Emerald (gem 2)'),
(70623, 70751, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Radiant Huge Emerald (gem 2)'),
(70623, 70752, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Vivid Huge Emerald (gem 2)'),
(70623, 70753, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Misty Huge Emerald (gem 2)'),
(70623, 70754, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Energized Huge Emerald (gem 2)'),
(70623, 70755, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Intricate Huge Emerald (gem 2)'),
(70623, 70756, 0, 0, 0, 1, 2, 1, 1, 'Vault Treasure Bag (heroic) - Steady Huge Emerald (gem 2)');

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
