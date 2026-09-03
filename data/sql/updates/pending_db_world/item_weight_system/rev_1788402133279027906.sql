-- Phase 5 prep (Bucket 4): refits item_budget_curve's ilvl 1-59 range from real
-- armor items -- it was flat at 1 for every ilvl 1-39 (only starts ramping at
-- ilvl 40), which would have gutted real classic itemization (e.g. Mantle of
-- Doan, ilvl 38, target=0.68 vs. its real weightedTotal of 25 -- a 3600%
-- deviation) had Bucket 4 converted against it as-is.
--
-- Root cause: the original regression (docs/itemization-changes.md Sec4.5) used
-- Epic-only data (the QualityMult=1.00 baseline) and Epic items barely exist
-- below ilvl 40 in real Vanilla/early-TBC itemization -- the isotonic fit
-- correctly held flat at its floor for an entirely unobserved range, it wasn't
-- a fitting bug. Fix: same methodology (on-budget stat sum, stamina excluded,
-- on-equip spells resolved and folded in, median per ilvl, PAVA isotonic
-- regression), but pooling Uncommon + Rare + Epic armor items together,
-- normalized back to the Epic/1.00 baseline via item_quality_mult (0.7/0.9/1.0)
-- -- Uncommon population is dense throughout this range (dozens-100+ items per
-- ilvl from ~10 on) where Epic is nearly absent. ilvl 60+ is untouched (already
-- live and validated by Buckets 1-3); the refit was anchored through ilvl 60-65's
-- existing values so the fit connects without a step at the seam. Known-bad test
-- entries excluded per Sec4.5 (19897/22711/22721/22722) plus a name-pattern net
-- for QA/Monster-prefixed junk this bucket's own deviation scan surfaced.

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
