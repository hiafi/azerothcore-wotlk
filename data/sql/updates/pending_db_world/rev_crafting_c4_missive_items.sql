-- Crafting rework C4: the nine Missive items (hand-picked `item` block ids 70710-70718, Item.dbc rows in
-- apps/dbc-tools/source/items.csv). Each one's Use spell is its Missive buff (207000-207008, declared in
-- apps/dbc-tools/source/world/crafting_suffixes.py, which also declares the Inscription recipes that make them).
-- Scroll-shaped like the stock Scroll of Stamina 1180 (class 0 / 4, Material 7, BagFamily 16 = Inscription bags):
-- common, stacks to 20, no level requirement, tradeable, sells for 10 silver. The item is spent on use
-- (spellcharges -1) unless the buff's script refuses the cast (a Missive is already active). Upsert:
-- item_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `item_template` (`entry`, `class`, `subclass`, `SoundOverrideSubclass`, `name`, `displayid`, `Quality`,
    `Flags`, `BuyCount`, `BuyPrice`, `SellPrice`, `InventoryType`, `AllowableClass`, `AllowableRace`, `ItemLevel`,
    `RequiredLevel`, `maxcount`, `stackable`, `spellid_1`, `spelltrigger_1`, `spellcharges_1`, `spellcooldown_1`,
    `spellcategory_1`, `spellcategorycooldown_1`, `spellcooldown_2`, `spellcategorycooldown_2`, `spellcooldown_3`,
    `spellcategorycooldown_3`, `spellcooldown_4`, `spellcategorycooldown_4`, `spellcooldown_5`,
    `spellcategorycooldown_5`, `bonding`, `description`, `Material`, `sheath`, `BagFamily`, `RequiredDisenchantSkill`,
    `VerifiedBuild`) VALUES
(70710, 0, 4, -1, 'Missive of Critical Strike', 3018, 1, 0, 1, 0, 1000, 0, -1, -1, 1, 0, 0, 20, 207000, 0, -1, -1, 0,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, '', 7, 0, 16, -1, 0),
(70711, 0, 4, -1, 'Missive of Haste', 3018, 1, 0, 1, 0, 1000, 0, -1, -1, 1, 0, 0, 20, 207001, 0, -1, -1, 0, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, 0, '', 7, 0, 16, -1, 0),
(70712, 0, 4, -1, 'Missive of Mastery', 3018, 1, 0, 1, 0, 1000, 0, -1, -1, 1, 0, 0, 20, 207002, 0, -1, -1, 0, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, 0, '', 7, 0, 16, -1, 0),
(70713, 0, 4, -1, 'Missive of Versatility', 3018, 1, 0, 1, 0, 1000, 0, -1, -1, 1, 0, 0, 20, 207003, 0, -1, -1, 0, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, 0, '', 7, 0, 16, -1, 0),
(70714, 0, 4, -1, 'Missive of Cooldown Haste', 3018, 1, 0, 1, 0, 1000, 0, -1, -1, 1, 0, 0, 20, 207004, 0, -1, -1, 0,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, '', 7, 0, 16, -1, 0),
(70715, 0, 4, -1, 'Missive of Proc Chance', 3018, 1, 0, 1, 0, 1000, 0, -1, -1, 1, 0, 0, 20, 207005, 0, -1, -1, 0, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, 0, '', 7, 0, 16, -1, 0),
(70716, 0, 4, -1, 'Missive of Block', 3018, 1, 0, 1, 0, 1000, 0, -1, -1, 1, 0, 0, 20, 207006, 0, -1, -1, 0, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, 0, '', 7, 0, 16, -1, 0),
(70717, 0, 4, -1, 'Missive of Dodge', 3018, 1, 0, 1, 0, 1000, 0, -1, -1, 1, 0, 0, 20, 207007, 0, -1, -1, 0, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, 0, '', 7, 0, 16, -1, 0),
(70718, 0, 4, -1, 'Missive of Parry', 3018, 1, 0, 1, 0, 1000, 0, -1, -1, 1, 0, 0, 20, 207008, 0, -1, -1, 0, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, 0, '', 7, 0, 16, -1, 0)
ON DUPLICATE KEY UPDATE `class` = VALUES(`class`), `subclass` = VALUES(`subclass`), `SoundOverrideSubclass` =
    VALUES(`SoundOverrideSubclass`), `name` = VALUES(`name`), `displayid` = VALUES(`displayid`), `Quality` =
    VALUES(`Quality`), `Flags` = VALUES(`Flags`), `BuyCount` = VALUES(`BuyCount`), `BuyPrice` = VALUES(`BuyPrice`),
    `SellPrice` = VALUES(`SellPrice`), `InventoryType` = VALUES(`InventoryType`), `AllowableClass` =
    VALUES(`AllowableClass`), `AllowableRace` = VALUES(`AllowableRace`), `ItemLevel` = VALUES(`ItemLevel`),
    `RequiredLevel` = VALUES(`RequiredLevel`), `maxcount` = VALUES(`maxcount`), `stackable` = VALUES(`stackable`),
    `spellid_1` = VALUES(`spellid_1`), `spelltrigger_1` = VALUES(`spelltrigger_1`), `spellcharges_1` =
    VALUES(`spellcharges_1`), `spellcooldown_1` = VALUES(`spellcooldown_1`), `spellcategory_1` =
    VALUES(`spellcategory_1`), `spellcategorycooldown_1` = VALUES(`spellcategorycooldown_1`), `spellcooldown_2` =
    VALUES(`spellcooldown_2`), `spellcategorycooldown_2` = VALUES(`spellcategorycooldown_2`), `spellcooldown_3` =
    VALUES(`spellcooldown_3`), `spellcategorycooldown_3` = VALUES(`spellcategorycooldown_3`), `spellcooldown_4` =
    VALUES(`spellcooldown_4`), `spellcategorycooldown_4` = VALUES(`spellcategorycooldown_4`), `spellcooldown_5` =
    VALUES(`spellcooldown_5`), `spellcategorycooldown_5` = VALUES(`spellcategorycooldown_5`), `bonding` =
    VALUES(`bonding`), `description` = VALUES(`description`), `Material` = VALUES(`Material`), `sheath` =
    VALUES(`sheath`), `BagFamily` = VALUES(`BagFamily`), `RequiredDisenchantSkill` =
    VALUES(`RequiredDisenchantSkill`), `VerifiedBuild` = VALUES(`VerifiedBuild`);
