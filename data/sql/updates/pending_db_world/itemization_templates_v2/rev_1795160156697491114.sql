-- Scarlet Monastery gear (the 64 boss list items and the Zealot's dungeon set): the four shapes the item files need
-- (docs/dungeons/scarlet-monastery-rework.md "Loot", dungeon-loot-vanilla.md "Scarlet Monastery": stat lines the
-- existing catalogue lacks).
--
-- Shapes (modeled exactly on the existing secondary rows: dist 2 "Even" for a pair, dist 4 "Even trio" for three stats,
-- the order follows the name; the avoidance shapes carry the same primary rules as the stock ones: Parry and Block a
-- Strength primary like 60 and 61, the Dodge/Versatility (Any) copy no rule like 89 and 80):
--   96  Block/Parry/Versatility  kind 1  stats 15 (Block), 14 (Parry), 23 (Versatility)   needs a Strength primary
--                                (dist 4; Aegis of the Scarlet Commander)
--   97  Block/Mastery/Versatility  kind 1  stats 15 (Block), 22 (Mastery), 23 (Versatility)  needs a Strength primary
--                                (dist 4; Captain's Legguards)
--   98  Dodge/Versatility (Any)  kind 1  stats 13 (Dodge), 23 (Versatility)   no rule (dist 2, the rule-free copy of
--                                87; Deadman's Hand, a trinket-like ring with no primary)
--   99  Parry/CDH                kind 1  stats 14 (Parry), 24 (CDH)           needs a Strength primary (dist 2, the
--                                Parry/Haste 90 pattern; the Zealot's Last Stand pauldrons)
-- Re-runnable: DELETE then INSERT on the four ids.
--
DELETE FROM `item_shape` WHERE `shape_id` BETWEEN 96 AND 99;
INSERT INTO `item_shape` (`shape_id`, `name`, `kind`, `dist_id`) VALUES
(96, 'Block/Parry/Versatility', 1, 4),
(97, 'Block/Mastery/Versatility', 1, 4),
(98, 'Dodge/Versatility (Any)', 1, 2),
(99, 'Parry/CDH', 1, 2);

DELETE FROM `item_shape_stat` WHERE `shape_id` BETWEEN 96 AND 99;
INSERT INTO `item_shape_stat` (`shape_id`, `rank`, `stat_type`) VALUES
(96, 1, 15),  -- Block
(96, 2, 14),  -- Parry
(96, 3, 23),  -- Versatility
(97, 1, 15),  -- Block
(97, 2, 22),  -- Mastery
(97, 3, 23),  -- Versatility
(98, 1, 13),  -- Dodge
(98, 2, 23),  -- Versatility
(99, 1, 14),  -- Parry
(99, 2, 24);  -- CDH

DELETE FROM `item_shape_rule` WHERE `shape_id` BETWEEN 96 AND 99;
INSERT INTO `item_shape_rule` (`shape_id`, `rule_type`, `stat_type`) VALUES
(96, 1, 4),  -- Block/Parry/Versatility: Strength primary
(97, 1, 4),  -- Block/Mastery/Versatility: Strength primary
(99, 1, 4);  -- Parry/CDH: Strength primary
