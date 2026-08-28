-- item-tools: 'Band of Servitude' (22721). Adding Versatility Changed columns: stat_type3 (0 -> 23), stat_value3 (0 ->
-- 20).
UPDATE `item_template` SET `stat_type3` = 23, `stat_value3` = 20 WHERE `entry` = 22721 AND `stat_type3` = 0 AND `stat_value3` = 0;
