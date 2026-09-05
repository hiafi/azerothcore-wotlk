-- Phase 5 content, Bucket 2: reverts entry 40832 (ObsoleteSigil of Pestilential Touch) back to its original stats -- its
-- socketColor_1 (14, a Prismatic-like value only 3 other items in the whole DB use, all three also named "Obsolete..."/a
-- joke test item) has no item_budget_socket_cost entry, which the worldserver's own ItemBudget::LoadItemBudget()
-- validation correctly flagged at boot ("socket color 14 missing from item_budget_socket_cost") and refused to
-- materialize. Rather than inventing a socket_cost tier for content that's dead/unused everywhere else in the DB, this
-- excludes the one item from the budget system entirely, same precedent as Bucket 1's negative-literal-stat exclusions
-- -- left completely untouched.
UPDATE `item_template` SET `stat_type1` = 7, `stat_value1` = 23, `stat_type2` = 4, `stat_value2` = 15, `stat_type3` = 32, `stat_value3` = 10, `stat_type4` = 31, `stat_value4` = 10 WHERE `entry` = 40832 AND `stat_type1` = 4 AND `stat_value1` = 35 AND `stat_type2` = 32 AND `stat_value2` = 23 AND `stat_type3` = 31 AND `stat_value3` = 23 AND `stat_type4` = 7 AND `stat_value4` = 28;
