-- item-tools: "Betrayer's Boots" (19897). Adding Mastery Changed columns: stat_type4 (0 -> 22), stat_value4 (0 -> 20).
UPDATE `item_template` SET `stat_type4` = 22, `stat_value4` = 20 WHERE `entry` = 19897 AND `stat_type4` = 0 AND `stat_value4` = 0;
