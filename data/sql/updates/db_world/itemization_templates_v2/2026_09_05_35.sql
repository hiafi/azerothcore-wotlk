-- DB update 2026_09_05_34 -> 2026_09_05_35
--
-- Shape-based itemization (docs/itemization-phase-2.md), implementation order step 10: author
-- the secondary shapes. Purely additive -- item_itemization/ItemBudget.cpp are untouched, so
-- this is safe to apply on its own, same as steps 1-4.
--
-- 46 shapes, shape_id 25-70, kind = 1 (secondary). Revision 3 (see the end of this header for
-- what it added). Revision 2 of this migration -- the original
-- pass (60 shapes) authored per §5.3's "pick a stat pool per role" pools as if each pool needed
-- its own physical rows, which produced dozens of byte-for-byte duplicates (Crit-Solo, Even-pair
-- Haste/Mastery, etc. existed 3-4 times over with different shape_ids and cosmetic "Pool: " name
-- prefixes). That was wrong: a shape's identity is (distribution, ordered stat list, rules) --
-- nothing else -- and §6's own rule table already does the real role-gating ("Generic DPS
-- shapes | none | pair with anything"), so a rule-free shape is legitimately reusable by any
-- primary. "Pool" is authoring guidance for step 11's real per-item assignment (which shape_ids
-- suit a caster vs. a tank item), not a schema concept -- it was never meant to force duplicate
-- rows.
--
-- Deduplicated to 40 unique shapes, then 5 more added on review: Weighted-pair (66/33)
-- counterparts for three pairs that only had their Even (50/50) half (Haste/CDH, Crit/Proc,
-- Mastery/Versatility), plus two Lead-plus-two (50/25/25) trios that put a niche stat (Proc,
-- Haste) in the lead slot ahead of two steadier support stats -- 45 total.
--
-- Layout:
--   25-46 (22): Generic, no rule -- Crit/Haste/Mastery/Versatility/CDH/Proc in every Solo/Even/
--                Weighted/Trio/Lead-plus-two combination authored. Usable by any primary shape.
--   47-50 (4):  MP5 -- forbids Spirit (prevents regen double-count, §6). MP5 doesn't exist
--                outside these, so unlike the generic set these can't be built from smaller
--                reusable pieces.
--   51-53 (3):  Armor Pen -- requires_any Str, requires_any Agi (no caster use, §6).
--   54-64 (11): Dodge/Parry/Block -- rules per §6: Dodge (alone or with a non-tank stat)
--                requires Str-or-Agi; anything involving Parry or Block requires Str specifically
--                (druids do not parry; Str approximates shield users). Where a shape mixes stats
--                with different individual constraints (Dodge/Parry, Dodge/Block), it gets the
--                STRICTER combined constraint -- Str only -- not the looser Str-or-Agi, since
--                every stat in the shape has to make sense for whatever primary the item ends up
--                with, and Str already satisfies Dodge's looser test too.
--   65-69 (5):  This review round's additions (see above) -- all generic, no rule.
--
-- Revision 3: +1 shape, id 70, "Parry/Block" (Even, Str-only rule -- same convention as 55/56/
-- 60/61). The one pairwise Dodge/Parry/Block combo the 54-64 range never had: Dodge/Parry (62)
-- and Dodge/Block (63) both exist, but not plain Parry/Block. Confirmed against real data after
-- entry 11931 "Dreadforge Retaliator" led to a broader per-item review: 11 real items historically
-- carried Parry+Block with no Dodge (vs. 222 Dodge+Parry, 25 Dodge+Block) -- without this shape
-- those items' nearest-shape match had to pick among Dodge/Parry, Dodge/Block, or the full trio,
-- none an honest match for "Parry and Block, no Dodge."
--
DELETE FROM `item_shape` WHERE `shape_id` BETWEEN 25 AND 70;
INSERT INTO `item_shape` (`shape_id`, `name`, `kind`, `dist_id`) VALUES
(25, 'Crit (Solo)', 1, 1),
(26, 'Haste (Solo)', 1, 1),
(27, 'Mastery (Solo)', 1, 1),
(28, 'Versatility (Solo)', 1, 1),
(29, 'Crit/Haste', 1, 2),
(30, 'Crit/Mastery', 1, 2),
(31, 'Crit/Mastery, Crit lead', 1, 3),
(32, 'Crit/Versatility', 1, 2),
(33, 'Haste/Mastery', 1, 2),
(34, 'Haste/Mastery, Haste lead', 1, 3),
(35, 'Haste/Versatility', 1, 2),
(36, 'Mastery/Versatility', 1, 2),
(37, 'Crit/CDH', 1, 2),
(38, 'Haste/CDH', 1, 2),
(39, 'Crit/Proc', 1, 2),
(40, 'Haste/Proc', 1, 2),
(41, 'Crit/Haste, Crit lead', 1, 3),
(42, 'Crit/Haste/Mastery', 1, 4),
(43, 'Haste/Mastery/Versatility', 1, 4),
(44, 'Crit/Haste/Versatility', 1, 4),
(45, 'Crit/Mastery/Versatility', 1, 4),
(46, 'Crit/Haste/Mastery, Crit lead', 1, 5),
(47, 'MP5 (Solo)', 1, 1),
(48, 'MP5/Crit', 1, 2),
(49, 'MP5/Haste', 1, 2),
(50, 'MP5/Mastery', 1, 2),
(51, 'Crit/ArmorPen', 1, 2),
(52, 'Haste/ArmorPen', 1, 2),
(53, 'Mastery/ArmorPen', 1, 2),
(54, 'Dodge (Solo)', 1, 1),
(55, 'Parry (Solo)', 1, 1),
(56, 'Block (Solo)', 1, 1),
(57, 'Dodge/Crit', 1, 2),
(58, 'Dodge/Haste', 1, 2),
(59, 'Dodge/Mastery', 1, 2),
(60, 'Parry/Crit', 1, 2),
(61, 'Block/Crit', 1, 2),
(62, 'Dodge/Parry', 1, 2),
(63, 'Dodge/Block', 1, 2),
(64, 'Dodge/Parry/Block', 1, 4),
(65, 'Haste/CDH, Haste lead', 1, 3),
(66, 'Crit/Proc, Crit lead', 1, 3),
(67, 'Mastery/Versatility, Mastery lead', 1, 3),
(68, 'Proc/Crit/Mastery, Proc lead', 1, 5),
(69, 'Haste/CDH/Mastery, Haste lead', 1, 5),
(70, 'Parry/Block', 1, 2);

DELETE FROM `item_shape_stat` WHERE `shape_id` BETWEEN 25 AND 70;
INSERT INTO `item_shape_stat` (`shape_id`, `rank`, `stat_type`) VALUES
  (25,1,32),  -- Crit (Solo)
  (26,1,36),  -- Haste (Solo)
  (27,1,22),  -- Mastery (Solo)
  (28,1,23),  -- Versatility (Solo)
  (29,1,32),(29,2,36),  -- Crit/Haste
  (30,1,32),(30,2,22),  -- Crit/Mastery
  (31,1,32),(31,2,22),  -- Crit/Mastery, Crit lead
  (32,1,32),(32,2,23),  -- Crit/Versatility
  (33,1,36),(33,2,22),  -- Haste/Mastery
  (34,1,36),(34,2,22),  -- Haste/Mastery, Haste lead
  (35,1,36),(35,2,23),  -- Haste/Versatility
  (36,1,22),(36,2,23),  -- Mastery/Versatility
  (37,1,32),(37,2,24),  -- Crit/CDH
  (38,1,36),(38,2,24),  -- Haste/CDH
  (39,1,32),(39,2,33),  -- Crit/Proc
  (40,1,36),(40,2,33),  -- Haste/Proc
  (41,1,32),(41,2,36),  -- Crit/Haste, Crit lead
  (42,1,32),(42,2,36),(42,3,22),  -- Crit/Haste/Mastery
  (43,1,36),(43,2,22),(43,3,23),  -- Haste/Mastery/Versatility
  (44,1,32),(44,2,36),(44,3,23),  -- Crit/Haste/Versatility
  (45,1,32),(45,2,22),(45,3,23),  -- Crit/Mastery/Versatility
  (46,1,32),(46,2,36),(46,3,22),  -- Crit/Haste/Mastery, Crit lead
  (47,1,43),  -- MP5 (Solo)
  (48,1,43),(48,2,32),  -- MP5/Crit
  (49,1,43),(49,2,36),  -- MP5/Haste
  (50,1,43),(50,2,22),  -- MP5/Mastery
  (51,1,32),(51,2,44),  -- Crit/ArmorPen
  (52,1,36),(52,2,44),  -- Haste/ArmorPen
  (53,1,22),(53,2,44),  -- Mastery/ArmorPen
  (54,1,13),  -- Dodge (Solo)
  (55,1,14),  -- Parry (Solo)
  (56,1,15),  -- Block (Solo)
  (57,1,13),(57,2,32),  -- Dodge/Crit
  (58,1,13),(58,2,36),  -- Dodge/Haste
  (59,1,13),(59,2,22),  -- Dodge/Mastery
  (60,1,14),(60,2,32),  -- Parry/Crit
  (61,1,15),(61,2,32),  -- Block/Crit
  (62,1,13),(62,2,14),  -- Dodge/Parry
  (63,1,13),(63,2,15),  -- Dodge/Block
  (64,1,13),(64,2,14),(64,3,15),  -- Dodge/Parry/Block
  (65,1,36),(65,2,24),  -- Haste/CDH, Haste lead
  (66,1,32),(66,2,33),  -- Crit/Proc, Crit lead
  (67,1,22),(67,2,23),  -- Mastery/Versatility, Mastery lead
  (68,1,33),(68,2,32),(68,3,22),  -- Proc/Crit/Mastery, Proc lead
  (69,1,36),(69,2,24),(69,3,22),  -- Haste/CDH/Mastery, Haste lead
  (70,1,14),(70,2,15);  -- Parry/Block

DELETE FROM `item_shape_rule` WHERE `shape_id` BETWEEN 25 AND 70;
INSERT INTO `item_shape_rule` (`shape_id`, `rule_type`, `stat_type`) VALUES
(47,2,6),  -- MP5 (Solo)
(48,2,6),  -- MP5/Crit
(49,2,6),  -- MP5/Haste
(50,2,6),  -- MP5/Mastery
(51,1,4),(51,1,3),  -- Crit/ArmorPen
(52,1,4),(52,1,3),  -- Haste/ArmorPen
(53,1,4),(53,1,3),  -- Mastery/ArmorPen
(54,1,4),(54,1,3),  -- Dodge (Solo)
(55,1,4),  -- Parry (Solo)
(56,1,4),  -- Block (Solo)
(57,1,4),(57,1,3),  -- Dodge/Crit
(58,1,4),(58,1,3),  -- Dodge/Haste
(59,1,4),(59,1,3),  -- Dodge/Mastery
(60,1,4),  -- Parry/Crit
(61,1,4),  -- Block/Crit
(62,1,4),  -- Dodge/Parry
(63,1,4),  -- Dodge/Block
(64,1,4),  -- Dodge/Parry/Block
(70,1,4);  -- Parry/Block
