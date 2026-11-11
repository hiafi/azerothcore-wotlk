-- Crafting rework C4 pilot: eight stock crafted pieces take their secondaries from a random suffix (ruling A1), so the
-- suffix stats and the Missives can be tested in game before the real catch-up sets (C7). Each piece:
--   - item_itemization (full row, DELETE + INSERT like item-tools writes it): secondary_shape_id 0, so the secondary
--     budget is left unspent and becomes the suffix factor (ItemBudget::GetSuffixFactor), and primary_share 6000 (B1);
--   - item_template: RandomSuffix = its pool (9000 throughput pairs, 9001 tank pairs for the tank-flagged plate chest,
--     rulings D3/E1; pools in apps/dbc-tools/source/world/crafting_suffixes.py), item level 60 (user 2026-11-10), and
--     the stat / armor columns the budget materializes from the new row (apps/item-tools/item_lib/budget.py), so the
--     stored row matches what the server computes at boot.
-- Both statements of an item set constants and run unconditionally, so a rerun changes nothing and an item never ends
-- half switched (a marker row without its pool fails ItemBudget validation; a pool with a real secondary shape is two
-- budgets). Revert: the old values are in the comment above each item.
-- Copies made before this change keep no suffix (randomPropertyId 0) and lose their old secondaries; only the AH bot
-- holds any (checked 2026-11-10).

-- Mooncloth Vest (Tailoring). Was: item level 60, RandomSuffix 0, secondary_shape_id 42, primary_share 10000;
-- stat_value1 22, stat_value2 20, stat_type3 7, stat_value3 14, stat_type4 0, stat_value4 0.
DELETE FROM `item_itemization` WHERE `entry` = 14138;
INSERT INTO `item_itemization` (`entry`, `budget_mult`, `stamina_delta`, `dps_delta`, `absorbed_spell_slots`,
    `armor_delta`, `primary_shape_id`, `secondary_shape_id`, `primary_share`, `block_value_delta`) VALUES (14138, 1, 0,
    0, 0, 0, 8, 0, 6000, 0);
UPDATE `item_template` SET `RandomSuffix` = 9000, `ItemLevel` = 60, `stat_type1` = 5, `stat_value1` = 13, `stat_type2` =
    6, `stat_value2` = 6, `stat_type3` = 45, `stat_value3` = 7, `stat_type4` = 7, `stat_value4` = 14, `stat_type5` = 0,
    `stat_value5` = 0, `stat_type6` = 0, `stat_value6` = 0, `stat_type7` = 0, `stat_value7` = 0, `stat_type8` = 0,
    `stat_value8` = 0, `stat_type9` = 0, `stat_value9` = 0, `stat_type10` = 0, `stat_value10` = 0, `armor` = 85 WHERE
    `entry` = 14138;

-- Mooncloth Gloves (Tailoring). Was: item level 62, RandomSuffix 0, secondary_shape_id 65, primary_share 10000;
-- stat_value1 18, stat_value2 16, stat_type3 7, stat_value3 11, stat_type4 0, stat_value4 0, armor 54.
DELETE FROM `item_itemization` WHERE `entry` = 18409;
INSERT INTO `item_itemization` (`entry`, `budget_mult`, `stamina_delta`, `dps_delta`, `absorbed_spell_slots`,
    `armor_delta`, `primary_shape_id`, `secondary_shape_id`, `primary_share`, `block_value_delta`) VALUES (18409, 1, 0,
    0, 0, 0, 8, 0, 6000, 0);
UPDATE `item_template` SET `RandomSuffix` = 9000, `ItemLevel` = 60, `stat_type1` = 5, `stat_value1` = 9, `stat_type2` =
    6, `stat_value2` = 5, `stat_type3` = 45, `stat_value3` = 6, `stat_type4` = 7, `stat_value4` = 11, `stat_type5` = 0,
    `stat_value5` = 0, `stat_type6` = 0, `stat_value6` = 0, `stat_type7` = 0, `stat_value7` = 0, `stat_type8` = 0,
    `stat_value8` = 0, `stat_type9` = 0, `stat_value9` = 0, `stat_type10` = 0, `stat_value10` = 0, `armor` = 53 WHERE
    `entry` = 18409;

-- Living Breastplate (Leatherworking). Was: item level 60, RandomSuffix 0, secondary_shape_id 45, primary_share 10000;
-- stat_value1 28, stat_value2 16.
DELETE FROM `item_itemization` WHERE `entry` = 15059;
INSERT INTO `item_itemization` (`entry`, `budget_mult`, `stamina_delta`, `dps_delta`, `absorbed_spell_slots`,
    `armor_delta`, `primary_shape_id`, `secondary_shape_id`, `primary_share`, `block_value_delta`) VALUES (15059, 1, 0,
    0, 1, 0, 6, 0, 6000, 0);
UPDATE `item_template` SET `RandomSuffix` = 9000, `ItemLevel` = 60, `stat_type1` = 6, `stat_value1` = 17, `stat_type2` =
    45, `stat_value2` = 10, `stat_type3` = 7, `stat_value3` = 14, `stat_type4` = 0, `stat_value4` = 0, `stat_type5` = 0,
    `stat_value5` = 0, `stat_type6` = 0, `stat_value6` = 0, `stat_type7` = 0, `stat_value7` = 0, `stat_type8` = 0,
    `stat_value8` = 0, `stat_type9` = 0, `stat_value9` = 0, `stat_type10` = 0, `stat_value10` = 0, `armor` = 169 WHERE
    `entry` = 15059;

-- Mongoose Boots (Leatherworking). Was: item level 62, RandomSuffix 0, secondary_shape_id 35, primary_share 10000;
-- stat_value1 34, armor 120.
DELETE FROM `item_itemization` WHERE `entry` = 18506;
INSERT INTO `item_itemization` (`entry`, `budget_mult`, `stamina_delta`, `dps_delta`, `absorbed_spell_slots`,
    `armor_delta`, `primary_shape_id`, `secondary_shape_id`, `primary_share`, `block_value_delta`) VALUES (18506, 1, 0,
    0, 0, 0, 23, 0, 6000, 0);
UPDATE `item_template` SET `RandomSuffix` = 9000, `ItemLevel` = 60, `stat_type1` = 3, `stat_value1` = 19, `stat_type2` =
    7, `stat_value2` = 11, `stat_type3` = 0, `stat_value3` = 0, `stat_type4` = 0, `stat_value4` = 0, `stat_type5` = 0,
    `stat_value5` = 0, `stat_type6` = 0, `stat_value6` = 0, `stat_type7` = 0, `stat_value7` = 0, `stat_type8` = 0,
    `stat_value8` = 0, `stat_type9` = 0, `stat_value9` = 0, `stat_type10` = 0, `stat_value10` = 0, `armor` = 116 WHERE
    `entry` = 18506;

-- Red Dragonscale Breastplate (Leatherworking, mail). Was: item level 61, RandomSuffix 0, secondary_shape_id 37,
-- primary_share 10000; stat_value1 51, stat_type2 7, stat_value2 15, stat_type3 0, stat_value3 0, armor 366.
DELETE FROM `item_itemization` WHERE `entry` = 15047;
INSERT INTO `item_itemization` (`entry`, `budget_mult`, `stamina_delta`, `dps_delta`, `absorbed_spell_slots`,
    `armor_delta`, `primary_shape_id`, `secondary_shape_id`, `primary_share`, `block_value_delta`) VALUES (15047, 1, 0,
    0, 1, 0, 2, 0, 6000, 0);
UPDATE `item_template` SET `RandomSuffix` = 9000, `ItemLevel` = 60, `stat_type1` = 45, `stat_value1` = 20, `stat_type2`
    = 5, `stat_value2` = 8, `stat_type3` = 7, `stat_value3` = 14, `stat_type4` = 0, `stat_value4` = 0, `stat_type5` = 0,
    `stat_value5` = 0, `stat_type6` = 0, `stat_value6` = 0, `stat_type7` = 0, `stat_value7` = 0, `stat_type8` = 0,
    `stat_value8` = 0, `stat_type9` = 0, `stat_value9` = 0, `stat_type10` = 0, `stat_value10` = 0, `armor` = 354 WHERE
    `entry` = 15047;

-- Whitesoul Helm (Blacksmithing). Was: item level 60, RandomSuffix 0, secondary_shape_id 67, primary_share 10000;
-- stat_type1 6, stat_value1 14, stat_type2 5, stat_value2 14, stat_value3 17, armor 510.
DELETE FROM `item_itemization` WHERE `entry` = 12633;
INSERT INTO `item_itemization` (`entry`, `budget_mult`, `stamina_delta`, `dps_delta`, `absorbed_spell_slots`,
    `armor_delta`, `primary_shape_id`, `secondary_shape_id`, `primary_share`, `block_value_delta`) VALUES (12633, 1, 0,
    0, 2, 0, 7, 0, 6000, 0);
UPDATE `item_template` SET `RandomSuffix` = 9000, `ItemLevel` = 60, `stat_type1` = 5, `stat_value1` = 9, `stat_type2` =
    6, `stat_value2` = 8, `stat_type3` = 45, `stat_value3` = 10, `stat_type4` = 7, `stat_value4` = 14, `stat_type5` = 0,
    `stat_value5` = 0, `stat_type6` = 0, `stat_value6` = 0, `stat_type7` = 0, `stat_value7` = 0, `stat_type8` = 0,
    `stat_value8` = 0, `stat_type9` = 0, `stat_value9` = 0, `stat_type10` = 0, `stat_value10` = 0, `armor` = 630 WHERE
    `entry` = 12633;

-- Gloves of the Dawn (Blacksmithing). Was: item level 64, RandomSuffix 0, secondary_shape_id 42, primary_share 10000;
-- stat_value1 34, stat_value2 13, armor 417.
DELETE FROM `item_itemization` WHERE `entry` = 19057;
INSERT INTO `item_itemization` (`entry`, `budget_mult`, `stamina_delta`, `dps_delta`, `absorbed_spell_slots`,
    `armor_delta`, `primary_shape_id`, `secondary_shape_id`, `primary_share`, `block_value_delta`) VALUES (19057, 1, 0,
    0, 0, 0, 22, 0, 6000, 0);
UPDATE `item_template` SET `RandomSuffix` = 9000, `ItemLevel` = 60, `stat_type1` = 4, `stat_value1` = 19, `stat_type2` =
    7, `stat_value2` = 11, `stat_type3` = 0, `stat_value3` = 0, `stat_type4` = 0, `stat_value4` = 0, `stat_type5` = 0,
    `stat_value5` = 0, `stat_type6` = 0, `stat_value6` = 0, `stat_type7` = 0, `stat_value7` = 0, `stat_type8` = 0,
    `stat_value8` = 0, `stat_type9` = 0, `stat_value9` = 0, `stat_type10` = 0, `stat_value10` = 0, `armor` = 392 WHERE
    `entry` = 19057;

-- Enchanted Thorium Breastplate (Blacksmithing, tank-flagged: the tank pool). Was: item level 63, RandomSuffix 0,
-- secondary_shape_id 60, primary_share 4000; stat_value1 22, stat_type2 12, stat_value2 24, stat_type3 7, stat_value3
-- 16, armor 657.
DELETE FROM `item_itemization` WHERE `entry` = 12618;
INSERT INTO `item_itemization` (`entry`, `budget_mult`, `stamina_delta`, `dps_delta`, `absorbed_spell_slots`,
    `armor_delta`, `primary_shape_id`, `secondary_shape_id`, `primary_share`, `block_value_delta`) VALUES (12618, 1, 0,
    0, 1, 0, 22, 0, 6000, 0);
UPDATE `item_template` SET `RandomSuffix` = 9001, `ItemLevel` = 60, `stat_type1` = 4, `stat_value1` = 25, `stat_type2` =
    7, `stat_value2` = 14, `stat_type3` = 0, `stat_value3` = 0, `stat_type4` = 0, `stat_value4` = 0, `stat_type5` = 0,
    `stat_value5` = 0, `stat_type6` = 0, `stat_value6` = 0, `stat_type7` = 0, `stat_value7` = 0, `stat_type8` = 0,
    `stat_value8` = 0, `stat_type9` = 0, `stat_value9` = 0, `stat_type10` = 0, `stat_value10` = 0, `armor` = 627 WHERE
    `entry` = 12618;
