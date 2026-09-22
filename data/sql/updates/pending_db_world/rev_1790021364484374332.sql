-- Fix the four custom-stat QA test rings (Mastery/Versatility/Cooldown Haste/Proc
-- Chance) to actually read 100% of their stat instead of the placeholder 700 rating
-- they were hand-authored with, which only worked out to 25%/50% depending on the
-- stat's rating->percent curve (see docs/itemization-changes.md §5 and
-- Player::GetRatingMultiplier's comment for why these four stats aren't 1:1 with
-- raw rating): Mastery/Versatility share Crit Melee's curve (700 rating = 25% at
-- level 60), Cooldown Haste/Proc Chance are tuned at 2x that rate (700 rating = 50%).
UPDATE `item_template` SET `stat_value1` = 2800 WHERE `entry` = 70100 AND `stat_value1` = 700; -- Ring of Mastery
UPDATE `item_template` SET `stat_value1` = 2800 WHERE `entry` = 70101 AND `stat_value1` = 700; -- Ring of Versatility
UPDATE `item_template` SET `stat_value1` = 1400 WHERE `entry` = 70102 AND `stat_value1` = 700; -- Ring of Swiftness
UPDATE `item_template` SET `stat_value1` = 1400 WHERE `entry` = 70103 AND `stat_value1` = 700; -- Ring of Luck

-- These 4 rings were also enrolled in the shape-based itemization budget system
-- (item_itemization), which recomputes and overwrites an assigned item's stats from a
-- two-stat "shape" every worldserver startup (ItemBudget::LoadAndApply), unconditionally
-- clobbering the single-stat values set above. None of the assigned shapes even matched
-- the ring's name (70100/Mastery got shape 34 Haste/Mastery, 70101/Versatility got shape
-- 35 Haste/Versatility, 70102/Swiftness got shape 36 Mastery/Versatility with no Cooldown
-- Haste at all, 70103/Luck got shape 37 Crit/CDH with no Proc Chance at all) - this is what
-- was actually behind these items showing the wrong stats after a reload/restart. Removing
-- their item_itemization rows takes them out of the budget system entirely, so it leaves
-- the hand-set stat_type1/stat_value1 above alone.
DELETE FROM `item_itemization` WHERE `entry` IN (70100, 70101, 70102, 70103);
