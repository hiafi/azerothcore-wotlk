-- DB update 2026_09_05_29 -> 2026_09_05_30
--
-- Shape-based itemization (docs/itemization-phase-2.md), implementation order steps 3-4:
-- create the shape tables and populate the 4 distributions plus the 24 primary shapes.
-- Purely additive -- item_budget_assign/ItemBudget.cpp are untouched by this migration, so the
-- live budget-template system keeps working exactly as it does today.
--

CREATE TABLE IF NOT EXISTS `item_alloc_dist` (
  `dist_id` tinyint unsigned NOT NULL,
  `rank` tinyint unsigned NOT NULL COMMENT '1..n',
  `alloc` smallint unsigned NOT NULL COMMENT 'ten-thousandths, sums to 10000 per dist_id',
  PRIMARY KEY (`dist_id`, `rank`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Distribution vocabulary shared by primary and secondary shapes -- docs/itemization-phase-2.md §5.1';

CREATE TABLE IF NOT EXISTS `item_alloc_dist_name` (
  `dist_id` tinyint unsigned NOT NULL,
  `name` varchar(32) NOT NULL,
  PRIMARY KEY (`dist_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Human label for a distribution, tooling only';

CREATE TABLE IF NOT EXISTS `item_shape` (
  `shape_id` smallint unsigned NOT NULL,
  `name` varchar(64) NOT NULL,
  `kind` tinyint unsigned NOT NULL COMMENT '0 = primary, 1 = secondary',
  `dist_id` tinyint unsigned NOT NULL,
  PRIMARY KEY (`shape_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='An ordered stat list plus a distribution -- docs/itemization-phase-2.md §2';

CREATE TABLE IF NOT EXISTS `item_shape_stat` (
  `shape_id` smallint unsigned NOT NULL,
  `rank` tinyint unsigned NOT NULL COMMENT '1..n, matched positionally against item_alloc_dist',
  `stat_type` tinyint unsigned NOT NULL COMMENT 'FK item_stat_cost',
  PRIMARY KEY (`shape_id`, `rank`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='A shape''s ordered stat list';

CREATE TABLE IF NOT EXISTS `item_shape_rule` (
  `shape_id` smallint unsigned NOT NULL,
  `rule_type` tinyint unsigned NOT NULL COMMENT '1 = requires_any, 2 = forbids',
  `stat_type` tinyint unsigned NOT NULL COMMENT 'FK item_stat_cost, must have shape_side = 1',
  PRIMARY KEY (`shape_id`, `rule_type`, `stat_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Pairing constraints on SECONDARY shapes, evaluated against the item''s PRIMARY shape stat set -- §6. Empty until step 10 (secondary shapes not authored yet).';

--
-- 5.1 Distributions -- fixed vocabulary of 4, shared by primary and secondary shapes alike.
--
DELETE FROM `item_alloc_dist` WHERE `dist_id` IN (1,2,3,4,5);
INSERT INTO `item_alloc_dist` (`dist_id`, `rank`, `alloc`) VALUES
(1,1,10000),                    -- Solo
(2,1,5000),(2,2,5000),          -- Even pair
(3,1,6667),(3,2,3333),          -- Weighted pair
(4,1,3334),(4,2,3333),(4,3,3333), -- Even trio
(5,1,5000),(5,2,2500),(5,3,2500); -- Lead plus two

DELETE FROM `item_alloc_dist_name` WHERE `dist_id` IN (1,2,3,4,5);
INSERT INTO `item_alloc_dist_name` (`dist_id`, `name`) VALUES
(1,'Solo'),
(2,'Even pair'),
(3,'Weighted pair'),
(4,'Even trio'),
(5,'Lead plus two');

--
-- 5.2 Primary shapes (kind = 0) -- 24 shapes plus shape_id 0, the null shape (no item_shape_stat
-- rows, used by rings/necks: primary_shape_id = 0 at primary_share = 0, §2/§8 check 8).
--
-- The three hybrid trio sets ({Int,Spirit,SpellPower}, {Str,Int,SpellPower}, {Agi,Int,SpellPower})
-- use 1 Even trio shape + 2 Lead plus two shapes each, not "3 leads" of Lead plus two (see §5.2's
-- revised note -- the doc previously had this unreconciled). SpellPower is always the fixed 25% in
-- the Lead plus two shapes; the set's other two stats trade off which one takes the 50% lead. Which
-- stat gets Even trio's fractionally-larger rank 1 (3334 vs 3333) is immaterial -- a 1-in-10000
-- difference -- so it's just the first-listed stat in each set for consistency.
--
DELETE FROM `item_shape` WHERE `shape_id` BETWEEN 0 AND 24;
INSERT INTO `item_shape` (`shape_id`, `name`, `kind`, `dist_id`) VALUES
(0,  'Null (jewelry, 100% secondary)',        0, 1),
(1,  'Int/SpellPower, Even',                  0, 2),
(2,  'Int/SpellPower, SpellPower lead',       0, 3),
(3,  'Int/SpellPower, Int lead',              0, 3),
(4,  'Spirit/SpellPower, Even',               0, 2),
(5,  'Spirit/SpellPower, SpellPower lead',    0, 3),
(6,  'Spirit/SpellPower, Spirit lead',        0, 3),
(7,  'Int/Spirit/SpellPower, Even trio',      0, 4),
(8,  'Int/Spirit/SpellPower, Int lead',       0, 5),
(9,  'Int/Spirit/SpellPower, Spirit lead',    0, 5),
(10, 'Str/AttackPower, Even',                 0, 2),
(11, 'Str/AttackPower, AttackPower lead',     0, 3),
(12, 'Str/AttackPower, Str lead',             0, 3),
(13, 'Agi/AttackPower, Even',                 0, 2),
(14, 'Agi/AttackPower, AttackPower lead',     0, 3),
(15, 'Agi/AttackPower, Agi lead',             0, 3),
(16, 'Str/Int/SpellPower, Even trio',         0, 4),
(17, 'Str/Int/SpellPower, Str lead',          0, 5),
(18, 'Str/Int/SpellPower, Int lead',          0, 5),
(19, 'Agi/Int/SpellPower, Even trio',         0, 4),
(20, 'Agi/Int/SpellPower, Agi lead',          0, 5),
(21, 'Agi/Int/SpellPower, Int lead',          0, 5),
(22, 'Strength (Solo)',                       0, 1),
(23, 'Agility (Solo)',                        0, 1),
(24, 'Intellect (Solo)',                      0, 1);

DELETE FROM `item_shape_stat` WHERE `shape_id` BETWEEN 1 AND 24;
INSERT INTO `item_shape_stat` (`shape_id`, `rank`, `stat_type`) VALUES
-- 1-3: {Int(5), SpellPower(45)}
(1,1,5),(1,2,45),
(2,1,45),(2,2,5),
(3,1,5),(3,2,45),
-- 4-6: {Spirit(6), SpellPower(45)}
(4,1,6),(4,2,45),
(5,1,45),(5,2,6),
(6,1,6),(6,2,45),
-- 7-9: {Int(5), Spirit(6), SpellPower(45)} -- SpellPower fixed at rank 3 (25%) in the lead shapes
(7,1,5),(7,2,6),(7,3,45),
(8,1,5),(8,2,6),(8,3,45),
(9,1,6),(9,2,5),(9,3,45),
-- 10-12: {Str(4), AttackPower(38)}
(10,1,4),(10,2,38),
(11,1,38),(11,2,4),
(12,1,4),(12,2,38),
-- 13-15: {Agi(3), AttackPower(38)}
(13,1,3),(13,2,38),
(14,1,38),(14,2,3),
(15,1,3),(15,2,38),
-- 16-18: {Str(4), Int(5), SpellPower(45)} -- SpellPower fixed at rank 3 (25%) in the lead shapes
(16,1,4),(16,2,5),(16,3,45),
(17,1,4),(17,2,5),(17,3,45),
(18,1,5),(18,2,4),(18,3,45),
-- 19-21: {Agi(3), Int(5), SpellPower(45)} -- SpellPower fixed at rank 3 (25%) in the lead shapes
(19,1,3),(19,2,5),(19,3,45),
(20,1,3),(20,2,5),(20,3,45),
(21,1,5),(21,2,3),(21,3,45),
-- 22-24: Solo
(22,1,4),
(23,1,3),
(24,1,5);
