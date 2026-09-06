-- DB update 2026_09_05_30 -> 2026_09_05_31
--
-- Shape-based itemization (docs/itemization-phase-2.md), implementation order steps 5-6.
--
-- *** DO NOT let this file reach a live worldserver restart / DB update on its own. ***
-- This migration renames item_budget_assign (13,455 live rows as of authoring) to
-- item_itemization, drops template_id, and drops item_budget_socket_cost. The CURRENT
-- ItemBudget.cpp still does `SELECT entry, template_id, ... FROM item_budget_assign` and
-- `SELECT socket_color, discount FROM item_budget_socket_cost` -- both queries fail the moment
-- this applies, which silently stops the live budget materializer (LoadItemBudget() treats a
-- failed QueryResult as "nothing to load", not a crash) for every currently-itemized item.
--
-- Tested against a copy of the real table: MySQL backfills the new primary_shape_id/
-- secondary_shape_id columns to 0 for all 13,455 existing rows (shape_id 0 is the null shape,
-- no stat rows) -- so even after applying this AND deploying a rewritten ItemBudget.cpp (step 7)
-- but BEFORE running the real per-item migration (step 11, not yet written), every existing item
-- would materialize with its entire primary+secondary budget unspent -- a silent, total gutting
-- of every stat line on the server, not a crash either.
--
-- Safe to apply only once steps 7 (ItemBudget.cpp rewrite) AND 11 (real per-item
-- primary_shape_id/secondary_shape_id/primary_share backfill) are BOTH also ready to ship in the
-- same restart/DB-update. Until then this is schema preparation only, sitting inert as a pending
-- file like everything else in this directory.
--

RENAME TABLE `item_budget_assign` TO `item_itemization`;

ALTER TABLE `item_itemization`
  DROP COLUMN `template_id`,
  ADD `primary_shape_id`   smallint unsigned NOT NULL DEFAULT '0',
  ADD `secondary_shape_id` smallint unsigned NOT NULL DEFAULT '0',
  ADD `primary_share`      smallint unsigned NOT NULL DEFAULT '6000', -- ten-thousandths
  ADD `block_value_delta`  int NOT NULL DEFAULT '0'; -- shields only, off-budget like armor_delta, §7.4

-- secondary_shape_id: the design doc (§3.2) specifies NOT NULL with no default, matching
-- primary_shape_id's own "no shape assigned yet" placeholder semantics -- given a DEFAULT here
-- explicitly (rather than relying on MySQL's implicit backfill) so the placeholder value is
-- documented, not incidental. Both placeholders point at shape_id 0 (the null shape, zero
-- item_shape_stat rows) purely because it happens to be inert either way -- not because shape 0
-- is a valid secondary shape by design (it's kind=0/primary in item_shape). Step 11 overwrites
-- every real row's value; nothing should read this default in production.

--
-- item_gem_value_curve: budget units one socket is worth at a given ilvl (§7.5, §3.1). Replaces
-- item_budget_socket_cost's multiplicative 0.90-per-socket discount with a flat, ilvl-keyed cost,
-- because a gem grants a FIXED number of stat points while budget SCALES with item level (§7.5's
-- worked comparison: ~32 points from 2 gems at both ilvl 100 and ilvl 300, while 0.90^2 charges
-- 17.3 units at one end and 76.0 at the other).
--
-- A step function, not a ramp -- real gem values are flat within an expansion and jump between
-- them, confirmed for all three tiers: level 60 (Classic) gems give +4 to a rating stat, level 70
-- (TBC) give +8, level 80 (WotLK) give +16 -- doubling each expansion, and none of the three climb
-- across that expansion's OWN raid tiers the way item_budget_curve does (a Naxxramas gem and an
-- ICC gem are both +16, same tier, same value). GemProperties/SpellItemEnchantment aren't
-- populated in this DB (gemproperties_dbc has zero rows here -- gem stat values live in client DBC
-- data, not item_template, so they weren't reachable by querying this database the way MP5/Block
-- Value were, §7.3/§7.4), so all three figures are given values, not independently regressed here.
--
-- ilvl breakpoints (the only judgment call in this table, since content eras overlap somewhat in
-- raw ilvl): ilvl 1-59 = Classic (4), ilvl 60-149 = TBC (8), ilvl 150-300 = WotLK (16). The 59/60
-- boundary matches item_budget_curve's own revision-4 precedent (ilvl 1-59 specially refit as the
-- low end with no real Epic data to regress against, ilvl 60+ is the main Epic-only curve, i.e.
-- TBC onward) -- itemization-changes.md §4.5. The 149/150 boundary has no equally firm precedent
-- elsewhere in this system; picked as roughly where Northrend-tier gear starts, since TBC raid
-- loot (Black Temple/Sunwell) and early WotLK Northrend quest greens both land somewhere in the
-- ilvl 145-165 band in practice.
--
CREATE TABLE IF NOT EXISTS `item_gem_value_curve` (
  `ilvl` smallint unsigned NOT NULL,
  `gem_budget` float NOT NULL COMMENT 'budget units one socket is worth at this ilvl',
  PRIMARY KEY (`ilvl`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Replaces item_budget_socket_cost''s multiplicative discount -- docs/itemization-phase-2.md §7.5';

DELETE FROM `item_gem_value_curve` WHERE `ilvl` BETWEEN 1 AND 300;
INSERT INTO `item_gem_value_curve` (`ilvl`, `gem_budget`) VALUES
  (1,4.0),(2,4.0),(3,4.0),(4,4.0),(5,4.0),(6,4.0),(7,4.0),(8,4.0),
  (9,4.0),(10,4.0),(11,4.0),(12,4.0),(13,4.0),(14,4.0),(15,4.0),(16,4.0),
  (17,4.0),(18,4.0),(19,4.0),(20,4.0),(21,4.0),(22,4.0),(23,4.0),(24,4.0),
  (25,4.0),(26,4.0),(27,4.0),(28,4.0),(29,4.0),(30,4.0),(31,4.0),(32,4.0),
  (33,4.0),(34,4.0),(35,4.0),(36,4.0),(37,4.0),(38,4.0),(39,4.0),(40,4.0),
  (41,4.0),(42,4.0),(43,4.0),(44,4.0),(45,4.0),(46,4.0),(47,4.0),(48,4.0),
  (49,4.0),(50,4.0),(51,4.0),(52,4.0),(53,4.0),(54,4.0),(55,4.0),(56,4.0),
  (57,4.0),(58,4.0),(59,4.0),(60,8.0),(61,8.0),(62,8.0),(63,8.0),(64,8.0),
  (65,8.0),(66,8.0),(67,8.0),(68,8.0),(69,8.0),(70,8.0),(71,8.0),(72,8.0),
  (73,8.0),(74,8.0),(75,8.0),(76,8.0),(77,8.0),(78,8.0),(79,8.0),(80,8.0),
  (81,8.0),(82,8.0),(83,8.0),(84,8.0),(85,8.0),(86,8.0),(87,8.0),(88,8.0),
  (89,8.0),(90,8.0),(91,8.0),(92,8.0),(93,8.0),(94,8.0),(95,8.0),(96,8.0),
  (97,8.0),(98,8.0),(99,8.0),(100,8.0),(101,8.0),(102,8.0),(103,8.0),(104,8.0),
  (105,8.0),(106,8.0),(107,8.0),(108,8.0),(109,8.0),(110,8.0),(111,8.0),(112,8.0),
  (113,8.0),(114,8.0),(115,8.0),(116,8.0),(117,8.0),(118,8.0),(119,8.0),(120,8.0),
  (121,8.0),(122,8.0),(123,8.0),(124,8.0),(125,8.0),(126,8.0),(127,8.0),(128,8.0),
  (129,8.0),(130,8.0),(131,8.0),(132,8.0),(133,8.0),(134,8.0),(135,8.0),(136,8.0),
  (137,8.0),(138,8.0),(139,8.0),(140,8.0),(141,8.0),(142,8.0),(143,8.0),(144,8.0),
  (145,8.0),(146,8.0),(147,8.0),(148,8.0),(149,8.0),(150,16.0),(151,16.0),(152,16.0),
  (153,16.0),(154,16.0),(155,16.0),(156,16.0),(157,16.0),(158,16.0),(159,16.0),(160,16.0),
  (161,16.0),(162,16.0),(163,16.0),(164,16.0),(165,16.0),(166,16.0),(167,16.0),(168,16.0),
  (169,16.0),(170,16.0),(171,16.0),(172,16.0),(173,16.0),(174,16.0),(175,16.0),(176,16.0),
  (177,16.0),(178,16.0),(179,16.0),(180,16.0),(181,16.0),(182,16.0),(183,16.0),(184,16.0),
  (185,16.0),(186,16.0),(187,16.0),(188,16.0),(189,16.0),(190,16.0),(191,16.0),(192,16.0),
  (193,16.0),(194,16.0),(195,16.0),(196,16.0),(197,16.0),(198,16.0),(199,16.0),(200,16.0),
  (201,16.0),(202,16.0),(203,16.0),(204,16.0),(205,16.0),(206,16.0),(207,16.0),(208,16.0),
  (209,16.0),(210,16.0),(211,16.0),(212,16.0),(213,16.0),(214,16.0),(215,16.0),(216,16.0),
  (217,16.0),(218,16.0),(219,16.0),(220,16.0),(221,16.0),(222,16.0),(223,16.0),(224,16.0),
  (225,16.0),(226,16.0),(227,16.0),(228,16.0),(229,16.0),(230,16.0),(231,16.0),(232,16.0),
  (233,16.0),(234,16.0),(235,16.0),(236,16.0),(237,16.0),(238,16.0),(239,16.0),(240,16.0),
  (241,16.0),(242,16.0),(243,16.0),(244,16.0),(245,16.0),(246,16.0),(247,16.0),(248,16.0),
  (249,16.0),(250,16.0),(251,16.0),(252,16.0),(253,16.0),(254,16.0),(255,16.0),(256,16.0),
  (257,16.0),(258,16.0),(259,16.0),(260,16.0),(261,16.0),(262,16.0),(263,16.0),(264,16.0),
  (265,16.0),(266,16.0),(267,16.0),(268,16.0),(269,16.0),(270,16.0),(271,16.0),(272,16.0),
  (273,16.0),(274,16.0),(275,16.0),(276,16.0),(277,16.0),(278,16.0),(279,16.0),(280,16.0),
  (281,16.0),(282,16.0),(283,16.0),(284,16.0),(285,16.0),(286,16.0),(287,16.0),(288,16.0),
  (289,16.0),(290,16.0),(291,16.0),(292,16.0),(293,16.0),(294,16.0),(295,16.0),(296,16.0),
  (297,16.0),(298,16.0),(299,16.0),(300,16.0);

-- item_budget_socket_cost is deliberately NOT dropped here even though it's retired -- ItemBudget.cpp
-- still reads it. Dropping it lands together with step 7's rewrite (which stops querying it), same
-- header warning as above.
