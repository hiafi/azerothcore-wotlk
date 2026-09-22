-- Repair for a live-DB regression introduced by renaming already-applied db_world migrations
-- 2026_09_05_00.sql..03.sql to 2026_09_05_00b.sql..03b.sql (to dodge the updater's "duplicate
-- filename" fatal against upstream's unrelated files of the same names). UpdateFetcher.cpp's
-- rename detection only treats a hash match as a safe rename when the OLD filename is gone from
-- the available file set; here the old name still exists (as upstream's own new file), so it
-- logged "renamed, but the old file is still there! Treating it as a new file!" and re-applied
-- 00b-03b in full, which stomped three later migrations' updates to the same tables. See
-- docs/bugs-and-fixes.md ("Resolving an upstream filename collision by renaming an
-- already-applied db_world migration re-runs it on every existing DB") and
-- .agents/plans/disc-review-fixes/disc-review-fixes.PLAN.md sec 2 finding #2 for the full
-- writeup. This migration re-asserts the three clobbered blocks verbatim from the migrations
-- that originally set them, so it is a no-op on a DB that was never hit by the bug and idempotent
-- on one that was.

-- Restore from db_world/itemization_templates_v2/2026_09_05_29.sql (shape_side), clobbered back
-- to the column default (0) by 2026_09_05_00b.sql's item_stat_cost INSERT, which predates the
-- shape_side column and so has no value for it.
UPDATE `item_stat_cost` SET `shape_side` = 1 WHERE `stat_type` IN (3,4,5,6,38,45);
-- Agility, Strength, Intellect, Spirit, Attack Power, Spell Power

UPDATE `item_stat_cost` SET `shape_side` = 2 WHERE `stat_type` IN (13,14,15,22,23,24,32,33,36,44);
-- Dodge, Parry, Block (rating), Mastery, Versatility, Cooldown Haste, Crit, Proc Chance, Haste,
-- Armor Penetration

-- Restore from db_world/itemization_templates_v2/2026_09_05_22.sql (ilvl 1-59 retune), clobbered
-- by 2026_09_05_01b.sql's item_budget_curve INSERT (the original, flat-at-1 pre-retune values).
DELETE FROM `item_budget_curve` WHERE `ilvl` BETWEEN 1 AND 59;
INSERT INTO `item_budget_curve` (`ilvl`, `budget`) VALUES
(1, 1),
(2, 1),
(3, 1),
(4, 1),
(5, 1),
(6, 1),
(7, 1),
(8, 1),
(9, 1),
(10, 1),
(11, 1),
(12, 3),
(13, 3),
(14, 3),
(15, 5),
(16, 5),
(17, 6),
(18, 7),
(19, 7),
(20, 8),
(21, 8),
(22, 10),
(23, 11),
(24, 12),
(25, 12),
(26, 12),
(27, 13),
(28, 13),
(29, 14),
(30, 15),
(31, 15),
(32, 17),
(33, 17),
(34, 18),
(35, 19),
(36, 20),
(37, 20),
(38, 20),
(39, 20),
(40, 21),
(41, 22),
(42, 22),
(43, 22),
(44, 27),
(45, 27),
(46, 27),
(47, 27),
(48, 27),
(49, 27),
(50, 29),
(51, 31),
(52, 32),
(53, 32),
(54, 32),
(55, 34),
(56, 34),
(57, 35),
(58, 36),
(59, 39);

-- Restore from db_world/itemization_templates_v2/2026_09_05_05.sql (item 16800 Arcanist Boots ->
-- template 44), clobbered by 2026_09_05_03b.sql's item_budget_assign INSERT (a stale template 2
-- smoke-test assignment that predates the real conversion).
DELETE FROM `item_budget_assign` WHERE `entry` = 16800;
INSERT INTO `item_budget_assign` (`entry`, `template_id`, `budget_mult`, `stamina_delta`, `dps_delta`, `absorbed_spell_slots`, `armor_delta`) VALUES
(16800, 44, 1.0, 0, 0.0, 3, 0);
