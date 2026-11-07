-- Item variants wave 1: the two-secondary shape Stratholme's Ysida's Locket needs ("Cooldown Haste, Versatility").
--
-- Shape (modeled exactly on the existing two-secondary Even rows, 29-40: dist 2 "Even", two stats, no rules; the
-- order follows the name, like Crit/CDH 37 and Mastery/Versatility 36):
--   74  CDH/Versatility  kind 1 (secondary)  stats 24 (CDH), 23 (Versatility)
-- Re-runnable: DELETE then INSERT on the one id.
--
DELETE FROM `item_shape` WHERE `shape_id` = 74;
INSERT INTO `item_shape` (`shape_id`, `name`, `kind`, `dist_id`) VALUES
(74, 'CDH/Versatility', 1, 2);

DELETE FROM `item_shape_stat` WHERE `shape_id` = 74;
INSERT INTO `item_shape_stat` (`shape_id`, `rank`, `stat_type`) VALUES
(74, 1, 24),  -- CDH
(74, 2, 23);  -- Versatility

DELETE FROM `item_shape_rule` WHERE `shape_id` = 74;
