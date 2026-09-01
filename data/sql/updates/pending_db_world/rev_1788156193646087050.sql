-- item-tools: 'Band of Servitude' (22721). Testing Changed columns: stat_value3 (20 -> 1400).
UPDATE `item_template` SET `stat_value3` = 1400 WHERE `entry` = 22721 AND `stat_value3` = 20;
