-- item-tools: 'Cloak of the Hakkari Worshippers' (22711). Test Changed columns: stat_value3 (20 -> 1400).
UPDATE `item_template` SET `stat_value3` = 1400 WHERE `entry` = 22711 AND `stat_value3` = 20;
