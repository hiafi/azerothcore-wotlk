-- Random Classic Heroic rewards (lfg-classic-heroic, .agents/plans/lfg-classic-heroic/lfg-classic-heroic.PLAN.md
-- ruling 4). The finder entries themselves (random 300, heroic entries 301-305, the Classic Heroic section) are
-- apps/dbc-tools source/world/lfg_classic_heroic.py; the satchel's client Item.dbc and server item_dbc rows are
-- source/items.csv 70700. This rev: the satchel's item_template row and loot, the two reward quests and the
-- lfg_dungeon_rewards row.

-- Satchel of Helpful Goods, the heroic one (hand-picked `item` block id 70700): a copy of 52003 Satchel of Helpful Goods (class 15 /
-- 0, display 56915, Material 4, Flags 4 = ITEM_FLAG_HAS_LOOT so it opens with a right click, Bind on Pickup), item
-- level 60, Rare like the stock finder satchels. The class, subclass, display and material match the
-- source/items.csv Item.dbc row (DBC.EnforceItemAttributes). Upsert: item_template rows are never deleted
-- (codestyle-sql not_delete).
INSERT INTO `item_template` (`entry`, `class`, `subclass`, `SoundOverrideSubclass`, `name`, `displayid`, `Quality`,
    `Flags`, `BuyCount`, `BuyPrice`, `SellPrice`, `InventoryType`, `AllowableClass`, `AllowableRace`, `ItemLevel`,
    `RequiredLevel`, `maxcount`, `stackable`, `spellcooldown_1`, `spellcategorycooldown_1`, `spellcooldown_2`,
    `spellcategorycooldown_2`, `spellcooldown_3`, `spellcategorycooldown_3`, `spellcooldown_4`,
    `spellcategorycooldown_4`, `spellcooldown_5`, `spellcategorycooldown_5`, `bonding`, `description`, `Material`,
    `sheath`, `RequiredDisenchantSkill`, `VerifiedBuild`) VALUES
(70700, 15, 0, -1, 'Satchel of Helpful Goods', 56915, 3, 4, 1, 0, 0, 0, -1, -1, 60, 0, 0, 1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, 1, 'Spoils of a heroic dungeon: consumables and trade goods.', 4, 0, -1, 0)
    ON DUPLICATE KEY UPDATE `class` = VALUES(`class`), `subclass` = VALUES(`subclass`),
    `SoundOverrideSubclass` = VALUES(`SoundOverrideSubclass`), `name` = VALUES(`name`),
    `displayid` = VALUES(`displayid`), `Quality` = VALUES(`Quality`), `Flags` = VALUES(`Flags`),
    `InventoryType` = VALUES(`InventoryType`), `ItemLevel` = VALUES(`ItemLevel`),
    `RequiredLevel` = VALUES(`RequiredLevel`), `maxcount` = VALUES(`maxcount`), `stackable` = VALUES(`stackable`),
    `bonding` = VALUES(`bonding`), `description` = VALUES(`description`), `Material` = VALUES(`Material`),
    `sheath` = VALUES(`sheath`);

-- The satchel's loot: two groups, one item from each (LootGroup: the explicit-chance rows roll first, the Chance 0 rows
-- share what is left equally).
-- Group 1, consumables. Cut gems: the uncommon item level 60 gems (the vanilla-tier ones; this server's sockets take
-- stock gems), primary, crit and mana stats only (no Stamina gems by design, no Hit, Defense or Spell Penetration).
-- Major potions. Flasks are rarer: 3% each, 9% in all.
-- Group 2, crafting goods of the 55-60 tier: Runecloth, Thorium and Enchanted Thorium Bars (Arcanite rarer), uncut gems
-- (Huge Emerald rarer), enchanting dust, essence and shards, Rugged Leather and Hide, the 55-60 herbs (Black Lotus
-- rarer).
DELETE FROM `item_loot_template` WHERE `Entry` = 70700;
INSERT INTO `item_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`, `GroupId`,
    `MinCount`, `MaxCount`, `Comment`) VALUES
(70700, 23095, 0, 0, 0, 1, 1, 1, 1, 'Satchel of Helpful Goods (heroic) - Bold Blood Garnet'),
(70700, 23097, 0, 0, 0, 1, 1, 1, 1, 'Satchel of Helpful Goods (heroic) - Delicate Blood Garnet'),
(70700, 23113, 0, 0, 0, 1, 1, 1, 1, 'Satchel of Helpful Goods (heroic) - Brilliant Golden Draenite'),
(70700, 23119, 0, 0, 0, 1, 1, 1, 1, 'Satchel of Helpful Goods (heroic) - Sparkling Azure Moonstone'),
(70700, 28290, 0, 0, 0, 1, 1, 1, 1, 'Satchel of Helpful Goods (heroic) - Smooth Golden Draenite'),
(70700, 23098, 0, 0, 0, 1, 1, 1, 1, 'Satchel of Helpful Goods (heroic) - Inscribed Flame Spessarite'),
(70700, 23099, 0, 0, 0, 1, 1, 1, 1, 'Satchel of Helpful Goods (heroic) - Luminous Flame Spessarite'),
(70700, 23101, 0, 0, 0, 1, 1, 1, 1, 'Satchel of Helpful Goods (heroic) - Potent Flame Spessarite'),
(70700, 31869, 0, 0, 0, 1, 1, 1, 1, 'Satchel of Helpful Goods (heroic) - Wicked Flame Spessarite'),
(70700, 23106, 0, 0, 0, 1, 1, 1, 1, 'Satchel of Helpful Goods (heroic) - Dazzling Deep Peridot'),
(70700, 23109, 0, 0, 0, 1, 1, 1, 1, 'Satchel of Helpful Goods (heroic) - Royal Shadow Draenite'),
(70700, 31864, 0, 0, 0, 1, 1, 1, 1, 'Satchel of Helpful Goods (heroic) - Infused Shadow Draenite'),
(70700, 13446, 0, 0, 0, 1, 1, 2, 4, 'Satchel of Helpful Goods (heroic) - Major Healing Potion'),
(70700, 13444, 0, 0, 0, 1, 1, 2, 4, 'Satchel of Helpful Goods (heroic) - Major Mana Potion'),
(70700, 18253, 0, 0, 0, 1, 1, 1, 2, 'Satchel of Helpful Goods (heroic) - Major Rejuvenation Potion'),
(70700, 13442, 0, 0, 0, 1, 1, 1, 2, 'Satchel of Helpful Goods (heroic) - Mighty Rage Potion'),
(70700, 13455, 0, 0, 0, 1, 1, 1, 2, 'Satchel of Helpful Goods (heroic) - Greater Stoneshield Potion'),
(70700, 13510, 0, 3, 0, 1, 1, 1, 1, 'Satchel of Helpful Goods (heroic) - Flask of the Titans'),
(70700, 13511, 0, 3, 0, 1, 1, 1, 1, 'Satchel of Helpful Goods (heroic) - Flask of Distilled Wisdom'),
(70700, 13512, 0, 3, 0, 1, 1, 1, 1, 'Satchel of Helpful Goods (heroic) - Flask of Supreme Power'),
(70700, 14047, 0, 0, 0, 1, 2, 6, 10, 'Satchel of Helpful Goods (heroic) - Runecloth'),
(70700, 12359, 0, 0, 0, 1, 2, 3, 5, 'Satchel of Helpful Goods (heroic) - Thorium Bar'),
(70700, 12655, 0, 0, 0, 1, 2, 1, 2, 'Satchel of Helpful Goods (heroic) - Enchanted Thorium Bar'),
(70700, 12360, 0, 4, 0, 1, 2, 1, 1, 'Satchel of Helpful Goods (heroic) - Arcanite Bar'),
(70700, 12361, 0, 0, 0, 1, 2, 1, 1, 'Satchel of Helpful Goods (heroic) - Blue Sapphire'),
(70700, 12799, 0, 0, 0, 1, 2, 1, 1, 'Satchel of Helpful Goods (heroic) - Large Opal'),
(70700, 7910, 0, 0, 0, 1, 2, 1, 1, 'Satchel of Helpful Goods (heroic) - Star Ruby'),
(70700, 12800, 0, 0, 0, 1, 2, 1, 1, 'Satchel of Helpful Goods (heroic) - Azerothian Diamond'),
(70700, 12364, 0, 3, 0, 1, 2, 1, 1, 'Satchel of Helpful Goods (heroic) - Huge Emerald'),
(70700, 16204, 0, 0, 0, 1, 2, 2, 4, 'Satchel of Helpful Goods (heroic) - Illusion Dust'),
(70700, 16203, 0, 0, 0, 1, 2, 1, 2, 'Satchel of Helpful Goods (heroic) - Greater Eternal Essence'),
(70700, 14343, 0, 0, 0, 1, 2, 1, 2, 'Satchel of Helpful Goods (heroic) - Small Brilliant Shard'),
(70700, 14344, 0, 0, 0, 1, 2, 1, 1, 'Satchel of Helpful Goods (heroic) - Large Brilliant Shard'),
(70700, 8170, 0, 0, 0, 1, 2, 4, 8, 'Satchel of Helpful Goods (heroic) - Rugged Leather'),
(70700, 8171, 0, 0, 0, 1, 2, 1, 2, 'Satchel of Helpful Goods (heroic) - Rugged Hide'),
(70700, 13463, 0, 0, 0, 1, 2, 3, 5, 'Satchel of Helpful Goods (heroic) - Dreamfoil'),
(70700, 13464, 0, 0, 0, 1, 2, 3, 5, 'Satchel of Helpful Goods (heroic) - Golden Sansam'),
(70700, 13465, 0, 0, 0, 1, 2, 3, 5, 'Satchel of Helpful Goods (heroic) - Mountain Silversage'),
(70700, 13466, 0, 0, 0, 1, 2, 3, 5, 'Satchel of Helpful Goods (heroic) - Plaguebloom'),
(70700, 13467, 0, 0, 0, 1, 2, 2, 4, 'Satchel of Helpful Goods (heroic) - Icecap'),
(70700, 13468, 0, 2, 0, 1, 2, 1, 1, 'Satchel of Helpful Goods (heroic) - Black Lotus');

-- The reward quests (custom quest ids from ids.yaml's `quest` block), modeled on 24886 / 24894 Classic Random 56-60
-- (1st) / (Nth): QuestType 2, Flags 136, SpecialFlags 9 (repeatable, dungeon finder quest). No XP: gold only (user 2026-11-10).
-- Ruling 4 starting values (tunable): first run of the day 3g, 3 Badges of Justice (29434) and the satchel; repeat
-- runs half the gold, 1 Badge and the satchel. Upsert: quest_template rows are never deleted (codestyle-sql
-- not_delete).
INSERT INTO `quest_template` (`ID`, `QuestType`, `QuestLevel`, `MinLevel`, `RewardXPDifficulty`, `RewardMoney`,
    `Flags`, `RewardItem1`, `RewardAmount1`, `RewardItem2`, `RewardAmount2`, `LogTitle`, `LogDescription`,
    `QuestDescription`, `AreaDescription`, `ObjectiveText1`, `ObjectiveText2`, `ObjectiveText3`, `ObjectiveText4`,
    `VerifiedBuild`) VALUES
(90000, 2, 60, 60, 0, 30000, 136, 70700, 1, 29434, 3, 'Classic Random Heroic (1st)', '', '', '', '', '', '', '', 0),
(90001, 2, 60, 60, 0, 15000, 136, 70700, 1, 29434, 1, 'Classic Random Heroic (Nth)', '', '', '', '', '', '', '', 0)
    ON DUPLICATE KEY UPDATE `QuestType` = VALUES(`QuestType`), `QuestLevel` = VALUES(`QuestLevel`),
    `MinLevel` = VALUES(`MinLevel`), `RewardXPDifficulty` = VALUES(`RewardXPDifficulty`),
    `RewardMoney` = VALUES(`RewardMoney`), `Flags` = VALUES(`Flags`), `RewardItem1` = VALUES(`RewardItem1`),
    `RewardAmount1` = VALUES(`RewardAmount1`), `RewardItem2` = VALUES(`RewardItem2`),
    `RewardAmount2` = VALUES(`RewardAmount2`), `LogTitle` = VALUES(`LogTitle`);

DELETE FROM `quest_template_addon` WHERE `ID` IN (90000, 90001);
INSERT INTO `quest_template_addon` (`ID`, `SpecialFlags`) VALUES
(90000, 9),
(90001, 9);

-- The finder reward of random 300 (lfg_dungeon_rewards: the row with the lowest maxLevel at or above the player's
-- level; the queue is 60-62, so one row at 62).
DELETE FROM `lfg_dungeon_rewards` WHERE `dungeonId` = 300;
INSERT INTO `lfg_dungeon_rewards` (`dungeonId`, `maxLevel`, `firstQuestId`, `otherQuestId`) VALUES
(300, 62, 90000, 90001);

-- Badge of Justice is a level 60 currency on this server (user 2026-11-10): the finder and empowered chests pay it at
-- 60, so it no longer needs level 70 to use.
UPDATE `item_template` SET `RequiredLevel` = 60 WHERE `entry` = 29434;
