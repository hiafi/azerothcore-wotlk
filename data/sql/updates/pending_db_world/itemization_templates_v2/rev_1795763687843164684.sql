-- Uldaman gear (the 49 list items): the two shapes the item file needs
-- (docs/dungeons/uldaman-rework.md "Loot", dungeon-loot-vanilla.md "Uldaman": Glass-black Greaves carries Parry,
-- Mastery and Versatility and Stoneslayer carries Mastery, Versatility and Proc Chance, two stat lines the existing
-- catalogue lacks).
--
-- Shapes (modeled exactly on the existing secondary rows: dist 4 "Even" for three stats, the order follows the name;
-- the Parry trio carries the same Strength primary rule as Parry/Mastery 76, Dodge/Parry/Mastery 100 and
-- Dodge/Parry/Block 64; the Proc trio has no rule, like Haste/Mastery/Proc 95):
--   102  Parry/Mastery/Versatility  kind 1  stats 14 (Parry), 22 (Mastery), 23 (Versatility)   needs a Strength
--                                   primary (dist 4; Glass-black Greaves)
--   103  Mastery/Versatility/Proc   kind 1  stats 22 (Mastery), 23 (Versatility), 33 (Proc Chance)   no rule
--                                   (dist 4; Stoneslayer)
-- Re-runnable: DELETE then INSERT on the ids.
--
DELETE FROM `item_shape` WHERE `shape_id` IN (102, 103);
INSERT INTO `item_shape` (`shape_id`, `name`, `kind`, `dist_id`) VALUES
(102, 'Parry/Mastery/Versatility', 1, 4),
(103, 'Mastery/Versatility/Proc', 1, 4);

DELETE FROM `item_shape_stat` WHERE `shape_id` IN (102, 103);
INSERT INTO `item_shape_stat` (`shape_id`, `rank`, `stat_type`) VALUES
(102, 1, 14),  -- Parry
(102, 2, 22),  -- Mastery
(102, 3, 23),  -- Versatility
(103, 1, 22),  -- Mastery
(103, 2, 23),  -- Versatility
(103, 3, 33);  -- Proc Chance

DELETE FROM `item_shape_rule` WHERE `shape_id` = 102;
INSERT INTO `item_shape_rule` (`shape_id`, `rule_type`, `stat_type`) VALUES
(102, 1, 4);  -- Parry/Mastery/Versatility: Strength primary
