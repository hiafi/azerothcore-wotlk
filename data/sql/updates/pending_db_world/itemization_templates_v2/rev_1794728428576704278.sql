-- Blackrock gear (Blackrock Spire, Blackrock Depths and the Molten set): the twelve shapes the three item files need
-- (docs/dungeons/blackrock-spire-rework.md and blackrock-depths-rework.md "Loot", dungeon-loot-vanilla.md "Dungeon sets
-- (level 60)": secondary pairs the existing catalogue lacks, the tank swaps of the Molten pieces).
--
-- Shapes (modeled exactly on the existing secondary rows: dist 2 "Even" for a pair, dist 4 "Even trio" for three stats,
-- the order follows the name; the avoidance shapes carry the same primary rules as the stock ones: Dodge needs an
-- Agility or Strength primary like 57-59, Parry and Block a Strength primary like 60 and 61):
--   84  Mastery/CDH            kind 1  stats 22 (Mastery), 24 (CDH)            no rule
--   85  Versatility/Proc       kind 1  stats 23 (Versatility), 33 (Proc)       no rule
--   86  Proc/CDH               kind 1  stats 33 (Proc), 24 (CDH)               no rule
--   87  Dodge/Versatility      kind 1  stats 13 (Dodge), 23 (Versatility)      needs an Agility or Strength primary
--   88  Dodge/CDH              kind 1  stats 13 (Dodge), 24 (CDH)              needs an Agility or Strength primary
--   89  Dodge/Mastery (Any)    kind 1  stats 13 (Dodge), 22 (Mastery)          no rule (the rule-free copy of 59, like
--                                                                              80 Dodge (Solo, Any); Heartstone)
--   90  Parry/Haste            kind 1  stats 14 (Parry), 36 (Haste)            needs a Strength primary
--   91  Block/Versatility      kind 1  stats 15 (Block), 23 (Versatility)      needs a Strength primary
--   92  Block/CDH              kind 1  stats 15 (Block), 24 (CDH)              needs a Strength primary
--   93  Block/Mastery          kind 1  stats 15 (Block), 22 (Mastery)          needs a Strength primary
--   94  Block/Haste            kind 1  stats 15 (Block), 36 (Haste)            needs a Strength primary
--   95  Haste/Mastery/Proc     kind 1  stats 36 (Haste), 22 (Mastery), 33 (Proc)  no rule (dist 4, like 42)
-- Re-runnable: DELETE then INSERT on the twelve ids.
--
DELETE FROM `item_shape` WHERE `shape_id` BETWEEN 84 AND 95;
INSERT INTO `item_shape` (`shape_id`, `name`, `kind`, `dist_id`) VALUES
(84, 'Mastery/CDH', 1, 2),
(85, 'Versatility/Proc', 1, 2),
(86, 'Proc/CDH', 1, 2),
(87, 'Dodge/Versatility', 1, 2),
(88, 'Dodge/CDH', 1, 2),
(89, 'Dodge/Mastery (Any)', 1, 2),
(90, 'Parry/Haste', 1, 2),
(91, 'Block/Versatility', 1, 2),
(92, 'Block/CDH', 1, 2),
(93, 'Block/Mastery', 1, 2),
(94, 'Block/Haste', 1, 2),
(95, 'Haste/Mastery/Proc', 1, 4);

DELETE FROM `item_shape_stat` WHERE `shape_id` BETWEEN 84 AND 95;
INSERT INTO `item_shape_stat` (`shape_id`, `rank`, `stat_type`) VALUES
(84, 1, 22),  -- Mastery
(84, 2, 24),  -- CDH
(85, 1, 23),  -- Versatility
(85, 2, 33),  -- Proc Chance
(86, 1, 33),  -- Proc Chance
(86, 2, 24),  -- CDH
(87, 1, 13),  -- Dodge
(87, 2, 23),  -- Versatility
(88, 1, 13),  -- Dodge
(88, 2, 24),  -- CDH
(89, 1, 13),  -- Dodge
(89, 2, 22),  -- Mastery
(90, 1, 14),  -- Parry
(90, 2, 36),  -- Haste
(91, 1, 15),  -- Block
(91, 2, 23),  -- Versatility
(92, 1, 15),  -- Block
(92, 2, 24),  -- CDH
(93, 1, 15),  -- Block
(93, 2, 22),  -- Mastery
(94, 1, 15),  -- Block
(94, 2, 36),  -- Haste
(95, 1, 36),  -- Haste
(95, 2, 22),  -- Mastery
(95, 3, 33);  -- Proc Chance

DELETE FROM `item_shape_rule` WHERE `shape_id` BETWEEN 84 AND 95;
INSERT INTO `item_shape_rule` (`shape_id`, `rule_type`, `stat_type`) VALUES
(87, 1, 3),  -- Dodge/Versatility: Agility primary
(87, 1, 4),  -- Dodge/Versatility: or Strength primary
(88, 1, 3),  -- Dodge/CDH: Agility primary
(88, 1, 4),  -- Dodge/CDH: or Strength primary
(90, 1, 4),  -- Parry/Haste: Strength primary
(91, 1, 4),  -- Block/Versatility: Strength primary
(92, 1, 4),  -- Block/CDH: Strength primary
(93, 1, 4),  -- Block/Mastery: Strength primary
(94, 1, 4);  -- Block/Haste: Strength primary
