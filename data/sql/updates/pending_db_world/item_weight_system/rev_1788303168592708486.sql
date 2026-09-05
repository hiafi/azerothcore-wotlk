--
-- Percentage-allocation itemization system. See docs/itemization-changes.md.
-- Phase 1 (data foundation): schema + reference data. item_budget_curve,
-- item_weapon_dps_curve, and item_armor_curve are intentionally left empty
-- here -- populated once each regression (doc §4.5, §9.3) is reviewed and
-- smoothed. item_budget_template, item_budget_template_name,
-- item_budget_assign and item_budget_variant are content tables, populated
-- during Phase 5.
--
-- item_armor_curve/item_armor_slot_mult/item_armor_quality_mult are Armor's
-- own off-budget curve, same role as item_stamina_curve but with its own
-- slot and quality multipliers -- Armor's real per-slot/per-quality scaling
-- doesn't match the stat budget's item_slot_mult/item_quality_mult at all
-- (confirmed empirically, §9.3).
--

CREATE TABLE IF NOT EXISTS `item_budget_template` (
  `template_id` smallint unsigned NOT NULL,
  `stat_type` tinyint unsigned NOT NULL COMMENT 'ITEM_MOD_* constant',
  `alloc` smallint unsigned NOT NULL COMMENT 'ten-thousandths, sums to 10000 per template',
  PRIMARY KEY (`template_id`, `stat_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Allocation shapes, reusable across many items';

CREATE TABLE IF NOT EXISTS `item_budget_template_name` (
  `template_id` smallint unsigned NOT NULL,
  `name` varchar(64) NOT NULL,
  PRIMARY KEY (`template_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Human label for a template, tooling only';

CREATE TABLE IF NOT EXISTS `item_budget_assign` (
  `entry` int unsigned NOT NULL,
  `template_id` smallint unsigned NOT NULL,
  `budget_mult` float NOT NULL DEFAULT '1',
  `stamina_delta` int NOT NULL DEFAULT '0' COMMENT 'raw stat points, +/-',
  `dps_delta` float NOT NULL DEFAULT '0' COMMENT 'weapon DPS points, +/-',
  `absorbed_spell_slots` tinyint unsigned NOT NULL DEFAULT '0' COMMENT 'bitmask, bit i = clear Spells[i] (spellid_(i+1)) at materialization -- its effect was folded into the stat block instead',
  `armor_delta` int NOT NULL DEFAULT '0' COMMENT 'raw armor points, +/-, added after item_armor_curve -- NOT funded from budget, see 9.3',
  PRIMARY KEY (`entry`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Which item uses which template';

CREATE TABLE IF NOT EXISTS `item_armor_curve` (
  `ilvl` smallint unsigned NOT NULL,
  `armor_class` tinyint unsigned NOT NULL COMMENT 'ItemSubClassArmor: 1=Cloth, 2=Leather, 3=Mail, 4=Plate',
  `armor` int unsigned NOT NULL COMMENT 'value at the Chest/Robe reference slot, Epic quality',
  PRIMARY KEY (`ilvl`, `armor_class`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Off-budget armor by item level and armor class, before slot/quality mult';

CREATE TABLE IF NOT EXISTS `item_armor_slot_mult` (
  `inv_type` tinyint unsigned NOT NULL,
  `mult` float NOT NULL,
  PRIMARY KEY (`inv_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Armor scaling per slot, relative to Chest/Robe = 1.0 -- distinct from item_slot_mult, which is for the stat budget';

CREATE TABLE IF NOT EXISTS `item_armor_quality_mult` (
  `quality` tinyint unsigned NOT NULL,
  `mult` float NOT NULL,
  PRIMARY KEY (`quality`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Armor scaling per quality, Epic=1.0 -- distinct from item_quality_mult, which is for the stat budget';

CREATE TABLE IF NOT EXISTS `item_budget_curve` (
  `ilvl` smallint unsigned NOT NULL,
  `budget` int unsigned NOT NULL,
  PRIMARY KEY (`ilvl`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Stat budget by item level, Epic-baselined';

CREATE TABLE IF NOT EXISTS `item_weapon_dps_curve` (
  `ilvl` smallint unsigned NOT NULL,
  `quality` tinyint unsigned NOT NULL,
  `dps` float NOT NULL,
  PRIMARY KEY (`ilvl`, `quality`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Weapon DPS by item level and quality, speed-independent';

CREATE TABLE IF NOT EXISTS `item_weapon_dps_cost` (
  `id` tinyint unsigned NOT NULL DEFAULT '1',
  `cost` float NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Budget units consumed per point of weapon DPS';

CREATE TABLE IF NOT EXISTS `item_weapon_dps_spread` (
  `id` tinyint unsigned NOT NULL DEFAULT '1',
  `spread` float NOT NULL DEFAULT '0.3',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Damage variance around the average swing';

CREATE TABLE IF NOT EXISTS `item_slot_mult` (
  `inv_type` tinyint unsigned NOT NULL,
  `mult` float NOT NULL,
  PRIMARY KEY (`inv_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Budget multiplier by InventoryType';

CREATE TABLE IF NOT EXISTS `item_quality_mult` (
  `quality` tinyint unsigned NOT NULL,
  `mult` float NOT NULL,
  PRIMARY KEY (`quality`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Budget multiplier by item quality, Epic-baselined';

CREATE TABLE IF NOT EXISTS `item_stat_cost` (
  `stat_type` tinyint unsigned NOT NULL,
  `cost` float NOT NULL,
  `is_primary` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'Str/Agi/Int/Spirit; drives the Uncommon eligibility rule',
  PRIMARY KEY (`stat_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Budget units consumed per point of each stat';

CREATE TABLE IF NOT EXISTS `item_budget_socket_cost` (
  `socket_color` tinyint unsigned NOT NULL COMMENT 'SOCKET_COLOR_* constant',
  `discount` float NOT NULL COMMENT 'e.g. 0.90 = 10% budget reduction per socket',
  PRIMARY KEY (`socket_color`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Per-socket budget_mult discount factor';

CREATE TABLE IF NOT EXISTS `item_budget_set_discount` (
  `id` tinyint unsigned NOT NULL DEFAULT '1',
  `discount` float NOT NULL DEFAULT '0.9',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Flat budget_mult discount for item-set membership';

CREATE TABLE IF NOT EXISTS `item_budget_variant` (
  `entry` int unsigned NOT NULL,
  `base_entry` int unsigned NOT NULL,
  PRIMARY KEY (`entry`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Bookkeeping: links an item-level/quality variant back to its base entry';

CREATE TABLE IF NOT EXISTS `item_budget_version` (
  `id` tinyint unsigned NOT NULL DEFAULT '1',
  `version` int unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Bumped on any budget table change, drives client WDB cache invalidation';

--
-- Reference data. Starting values per docs/itemization-changes.md; balance
-- tuning happens by editing these rows, not by editing item_template.
--

DELETE FROM `item_slot_mult` WHERE `inv_type` IN (1,5,7,17,20,3,6,8,10,2,9,11,12,16,13,14,21,22,23,26);
INSERT INTO `item_slot_mult` (`inv_type`, `mult`) VALUES
(1,1.0),(5,1.0),(7,1.0),(17,1.0),(20,1.0),
(3,0.75),(6,0.75),(8,0.75),(10,0.75),
(2,0.5625),(9,0.5625),(11,0.5625),(12,0.5625),(16,0.5625),(13,0.5625),(14,0.5625),(21,0.5625),(22,0.5625),(23,0.5625),(26,0.5625);

DELETE FROM `item_quality_mult` WHERE `quality` IN (2,3,4);
INSERT INTO `item_quality_mult` (`quality`, `mult`) VALUES
(2,0.70), -- Uncommon
(3,0.90), -- Rare
(4,1.00); -- Epic, baseline

DELETE FROM `item_stat_cost` WHERE `stat_type` IN (4,3,5,7,6,32,36,31,37,44,47,38,45,12,13,14,15);
INSERT INTO `item_stat_cost` (`stat_type`, `cost`, `is_primary`) VALUES
(4,1.0,1),   -- Strength
(3,1.0,1),   -- Agility
(5,1.0,1),   -- Intellect
(7,0.667,0), -- Stamina, off-budget (§9.3), is_primary irrelevant here
(6,1.0,1),   -- Spirit
(32,1.0,0),  -- Crit Rating
(36,1.0,0),  -- Haste Rating
-- 31/37/44/47 are ITEM_MOD_HIT_RATING/EXPERTISE_RATING/ARMOR_PENETRATION_RATING/
-- SPELL_PENETRATION -- their real, unhijacked WotLK meanings, confirmed live
-- and unmodified in src/server/game/Entities/Item/ItemTemplate.h. §5's
-- "hijack" scheme for the four custom stats uses different IDs entirely
-- (22/23/24/33 -- see that section); this table was never touched by it.
(31,1.0,0),  -- Hit Rating
(37,1.0,0),  -- Expertise Rating
(44,1.5,0),  -- Armor Penetration Rating
(47,1.2,0),  -- Spell Penetration
(38,0.5,0),  -- Attack Power
(45,0.855,0),-- Spell Power
-- Defense/Dodge/Parry/Block: added in the itemization-changes.md §4.5
-- revision-3 pass -- present on-equip via real spells (24 of 759 resolved
-- Epic-armor spells grant one of these), previously unpriced and silently
-- dropped by the classifier. Cost 1.0 each, same "no strong reason to
-- differentiate" default as Crit/Haste -- starting values, not final,
-- same as every other row here (§4.3).
(12,1.0,0),  -- Defense Rating
(13,1.0,0),  -- Dodge Rating
(14,1.0,0),  -- Parry Rating
(15,1.0,0);  -- Block Rating

DELETE FROM `item_budget_socket_cost` WHERE `socket_color` IN (1,2,4,8);
INSERT INTO `item_budget_socket_cost` (`socket_color`, `discount`) VALUES
(1,0.90), -- Meta
(2,0.90), -- Red
(4,0.90), -- Yellow
(8,0.90); -- Blue

DELETE FROM `item_budget_set_discount` WHERE `id` = 1;
INSERT INTO `item_budget_set_discount` (`id`, `discount`) VALUES
(1,0.90);

DELETE FROM `item_weapon_dps_cost` WHERE `id` = 1;
INSERT INTO `item_weapon_dps_cost` (`id`, `cost`) VALUES
(1,1.0);

DELETE FROM `item_weapon_dps_spread` WHERE `id` = 1;
INSERT INTO `item_weapon_dps_spread` (`id`, `spread`) VALUES
(1,0.3);

DELETE FROM `item_budget_version` WHERE `id` = 1;
INSERT INTO `item_budget_version` (`id`, `version`) VALUES
(1,1);
