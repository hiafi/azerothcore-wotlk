-- Item variants IV0: the three single-stat shapes the Deadmines list needs, and the item_budget_variant tier column.
--
-- Shapes (each modeled exactly on the existing Solo rows, 22-28: dist 1 "Solo", one stat, no rules):
--   71  Spirit (Solo)  kind 0 (primary)    stat 6   -- like Strength / Agility / Intellect (Solo), 22-24
--   72  CDH (Solo)     kind 1 (secondary)  stat 24  -- like Crit / Haste / Mastery / Versatility (Solo), 25-28
--   73  Proc (Solo)    kind 1 (secondary)  stat 33
-- Emberstone Staff adopts its live row (plan decision 1), so no Int/Spirit shape is added.
--
-- item_budget_variant.tier: the variant's rung on its ladder, 0 = the base tier itself (Normal), 1 = Heroic,
-- 2.. = the empowered tiers, so the empowered module can look up (base_entry, tier) -> entry from the database.
-- ItemBudget.cpp reads the table as "SELECT entry, base_entry", so an extra column changes nothing at boot.
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

ALTER TABLE `item_budget_variant`
  ADD COLUMN `tier` tinyint unsigned NOT NULL DEFAULT '0'
    COMMENT 'ladder rung: 0 = base (Normal), 1 = Heroic, 2.. = empowered tiers'
    AFTER `base_entry`;
