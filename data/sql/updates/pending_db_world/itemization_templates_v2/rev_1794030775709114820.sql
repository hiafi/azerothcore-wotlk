-- Item variants, Haunted dungeon set: the four two-secondary shapes the set pieces need (docs/dungeons/
-- dungeon-loot-vanilla.md "Haunted set bonuses", Stats: waist and feet carry Mastery and Proc Chance; tanks swap the
-- first stat of each pair for their avoidance, Plate Tank Parry and Leather Tank Dodge).
--
-- Shapes (modeled exactly on the existing two-secondary Even rows, 29-40 and 57-63: dist 2 "Even", two stats, the
-- order follows the name; the avoidance shapes carry the same primary rules as the stock ones, Parry/Crit 60 and
-- Dodge/Crit 57):
--   75  Mastery/Proc   kind 1 (secondary)  stats 22 (Mastery), 33 (Proc Chance)   no rule
--   76  Parry/Mastery  kind 1 (secondary)  stats 14 (Parry), 22 (Mastery)        needs a Strength primary
--   77  Parry/Proc     kind 1 (secondary)  stats 14 (Parry), 33 (Proc Chance)    needs a Strength primary
--   78  Dodge/Proc     kind 1 (secondary)  stats 13 (Dodge), 33 (Proc Chance)    needs an Agility or Strength primary
-- Re-runnable: DELETE then INSERT on the four ids.
--
DELETE FROM `item_shape` WHERE `shape_id` BETWEEN 75 AND 78;
INSERT INTO `item_shape` (`shape_id`, `name`, `kind`, `dist_id`) VALUES
(75, 'Mastery/Proc', 1, 2),
(76, 'Parry/Mastery', 1, 2),
(77, 'Parry/Proc', 1, 2),
(78, 'Dodge/Proc', 1, 2);

DELETE FROM `item_shape_stat` WHERE `shape_id` BETWEEN 75 AND 78;
INSERT INTO `item_shape_stat` (`shape_id`, `rank`, `stat_type`) VALUES
(75, 1, 22),  -- Mastery
(75, 2, 33),  -- Proc Chance
(76, 1, 14),  -- Parry
(76, 2, 22),  -- Mastery
(77, 1, 14),  -- Parry
(77, 2, 33),  -- Proc Chance
(78, 1, 13),  -- Dodge
(78, 2, 33);  -- Proc Chance

DELETE FROM `item_shape_rule` WHERE `shape_id` BETWEEN 75 AND 78;
INSERT INTO `item_shape_rule` (`shape_id`, `rule_type`, `stat_type`) VALUES
(76, 1, 4),  -- Parry/Mastery: Strength primary
(77, 1, 4),  -- Parry/Proc: Strength primary
(78, 1, 3),  -- Dodge/Proc: Agility primary
(78, 1, 4);  -- Dodge/Proc: or Strength primary
