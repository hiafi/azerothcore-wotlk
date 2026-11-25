-- Zul'Farrak gear (the 62 list items): the one shape the item file needs
-- (docs/dungeons/zul-farrak-rework.md "Loot", dungeon-loot-vanilla.md "Zul'Farrak": Sergeant's Dented Breastplate
-- carries Dodge, Parry and Mastery, a stat line the existing catalogue lacks).
--
-- Shape (modeled exactly on the existing secondary rows: dist 4 "Even" for three stats, the order follows the name; the
-- avoidance trio carries the same primary rule as Dodge/Parry/Block 64 and Block/Mastery/Versatility 97, a Strength
-- primary):
--   100  Dodge/Parry/Mastery  kind 1  stats 13 (Dodge), 14 (Parry), 22 (Mastery)   needs a Strength primary
--                             (dist 4; Sergeant's Dented Breastplate)
-- Re-runnable: DELETE then INSERT on the id.
--
DELETE FROM `item_shape` WHERE `shape_id` = 100;
INSERT INTO `item_shape` (`shape_id`, `name`, `kind`, `dist_id`) VALUES
(100, 'Dodge/Parry/Mastery', 1, 4);

DELETE FROM `item_shape_stat` WHERE `shape_id` = 100;
INSERT INTO `item_shape_stat` (`shape_id`, `rank`, `stat_type`) VALUES
(100, 1, 13),  -- Dodge
(100, 2, 14),  -- Parry
(100, 3, 22);  -- Mastery

DELETE FROM `item_shape_rule` WHERE `shape_id` = 100;
INSERT INTO `item_shape_rule` (`shape_id`, `rule_type`, `stat_type`) VALUES
(100, 1, 4);  -- Dodge/Parry/Mastery: Strength primary
