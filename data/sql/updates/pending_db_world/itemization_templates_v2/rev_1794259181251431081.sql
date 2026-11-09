-- Quest reward itemization, round 6 (docs/plans/quest-reward-itemization/, stage QR1c): the three shapes the
-- designer's hand review needs (REQUIREMENTS rulings 29).
--
-- Shapes:
--   81  Spell Power (Solo)          kind 0 (primary)    stat 45 (Spell Power)   like the Solo primaries 22-24, 71
--                                                                              (dist 1): Master Dragonslayer's Orb
--                                                                              and Azurite Fists ("no Intellect").
--   82  Attack Power (Solo)         kind 0 (primary)    stat 38 (Attack Power)  same: Leafblade Dagger and Ebon Mask
--                                                                              ("no Strength").
--   83  Parry/Versatility (Any)     kind 1 (secondary)  stats 14 (Parry),       like the Even pairs (dist 2); no
--                                                       23 (Versatility)        rule, so it also takes the Null
--                                                                              primary (Onyxia Blood Talisman keeps
--                                                                              its Parry). Precedent: 80 Dodge (Solo,
--                                                                              Any), the rule-free copy of 54.
-- Re-runnable: DELETE then INSERT on the three ids.
--
DELETE FROM `item_shape` WHERE `shape_id` BETWEEN 81 AND 83;
INSERT INTO `item_shape` (`shape_id`, `name`, `kind`, `dist_id`) VALUES
(81, 'Spell Power (Solo)', 0, 1),
(82, 'Attack Power (Solo)', 0, 1),
(83, 'Parry/Versatility (Any)', 1, 2);

DELETE FROM `item_shape_stat` WHERE `shape_id` BETWEEN 81 AND 83;
INSERT INTO `item_shape_stat` (`shape_id`, `rank`, `stat_type`) VALUES
(81, 1, 45),  -- Spell Power
(82, 1, 38),  -- Attack Power
(83, 1, 14),  -- Parry
(83, 2, 23);  -- Versatility

DELETE FROM `item_shape_rule` WHERE `shape_id` BETWEEN 81 AND 83;
