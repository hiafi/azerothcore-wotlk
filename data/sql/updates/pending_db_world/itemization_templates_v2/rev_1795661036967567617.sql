-- Gnomeregan gear (the 48 list items): the one shape the item file needs
-- (docs/dungeons/gnomeregan-rework.md "Loot", dungeon-loot-vanilla.md "Gnomeregan": Mechbuilder's Overalls carries
-- Crit, Cooldown Haste and Versatility, a stat line the existing catalogue lacks).
--
-- Shape (modeled exactly on Crit/Haste/Versatility 44, the same three-stat Even trio with no primary rule; the order
-- follows the name):
--   101  Crit/CDH/Versatility  kind 1  stats 32 (Crit), 24 (CDH), 23 (Versatility)   no rule (dist 4;
--                              Mechbuilder's Overalls)
-- Re-runnable: DELETE then INSERT on the id.
--
DELETE FROM `item_shape` WHERE `shape_id` = 101;
INSERT INTO `item_shape` (`shape_id`, `name`, `kind`, `dist_id`) VALUES
(101, 'Crit/CDH/Versatility', 1, 4);

DELETE FROM `item_shape_stat` WHERE `shape_id` = 101;
INSERT INTO `item_shape_stat` (`shape_id`, `rank`, `stat_type`) VALUES
(101, 1, 32),  -- Crit
(101, 2, 24),  -- CDH
(101, 3, 23);  -- Versatility
