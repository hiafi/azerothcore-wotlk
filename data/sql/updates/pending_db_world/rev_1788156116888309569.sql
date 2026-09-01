-- item-tools: "Betrayer's Boots" (19897). Upping to 100% mastery for testing Changed columns: stat_value4 (20 -> 1400).
UPDATE `item_template` SET `stat_value4` = 1400 WHERE `entry` = 19897 AND `stat_value4` = 20;
