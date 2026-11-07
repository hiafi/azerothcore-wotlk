-- Item variants wave 1 follow-ups (plan s13, user 2026-11-07): the two solo secondary shapes that let Scholomance's
-- Ghoul Skin Leggings and Spare Rib carry their approved stats (docs/dungeons/dungeon-loot-vanilla.md).
--
-- Shapes (modeled exactly on the existing solo secondaries 47 MP5 (Solo) and 54 Dodge (Solo): kind 1, dist 1, one
-- stat; only the rules differ):
--   79  MP5 (Solo, Spirit)  kind 1 (secondary)  stat 43 (MP5)    needs a Spirit primary. The stock MP5 shapes
--                                                                47-50 forbid a Spirit primary; this one is the
--                                                                deliberate Spirit + MP5 pairing ("Spirit, MP5").
--   80  Dodge (Solo, Any)   kind 1 (secondary)  stat 13 (Dodge)  no rule: also takes the Null primary (a tank
--                                                                trinket with Dodge alone). The stock Dodge shapes
--                                                                54-59 need an Agility or Strength primary.
-- Re-runnable: DELETE then INSERT on the two ids.
--
DELETE FROM `item_shape` WHERE `shape_id` IN (79, 80);
INSERT INTO `item_shape` (`shape_id`, `name`, `kind`, `dist_id`) VALUES
(79, 'MP5 (Solo, Spirit)', 1, 1),
(80, 'Dodge (Solo, Any)', 1, 1);

DELETE FROM `item_shape_stat` WHERE `shape_id` IN (79, 80);
INSERT INTO `item_shape_stat` (`shape_id`, `rank`, `stat_type`) VALUES
(79, 1, 43),  -- MP5
(80, 1, 13);  -- Dodge

DELETE FROM `item_shape_rule` WHERE `shape_id` IN (79, 80);
INSERT INTO `item_shape_rule` (`shape_id`, `rule_type`, `stat_type`) VALUES
(79, 1, 6);  -- MP5 (Solo, Spirit): Spirit primary
