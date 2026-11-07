-- Item variants IV0: the three single-stat shapes the Deadmines list needs.
--
-- Shapes (each modeled exactly on the existing Solo rows, 22-28: dist 1 "Solo", one stat, no rules):
--   71  Spirit (Solo)  kind 0 (primary)    stat 6   -- like Strength / Agility / Intellect (Solo), 22-24
--   72  CDH (Solo)     kind 1 (secondary)  stat 24  -- like Crit / Haste / Mastery / Versatility (Solo), 25-28
--   73  Proc (Solo)    kind 1 (secondary)  stat 33
-- Emberstone Staff adopts its live row (plan decision 1), so no Int/Spirit shape is added.
--
-- The item_budget_variant.tier column is in its own file (the next one), so this file's re-runnable DELETE/INSERTs
-- can be re-applied without failing on a duplicate column (item variants R1 N7).
--
DELETE FROM `item_shape` WHERE `shape_id` BETWEEN 71 AND 73;
INSERT INTO `item_shape` (`shape_id`, `name`, `kind`, `dist_id`) VALUES
(71, 'Spirit (Solo)', 0, 1),
(72, 'CDH (Solo)', 1, 1),
(73, 'Proc (Solo)', 1, 1);

DELETE FROM `item_shape_stat` WHERE `shape_id` BETWEEN 71 AND 73;
INSERT INTO `item_shape_stat` (`shape_id`, `rank`, `stat_type`) VALUES
(71, 1, 6),  -- Spirit (Solo)
(72, 1, 24),  -- CDH (Solo)
(73, 1, 33);  -- Proc (Solo)

DELETE FROM `item_shape_rule` WHERE `shape_id` BETWEEN 71 AND 73;
