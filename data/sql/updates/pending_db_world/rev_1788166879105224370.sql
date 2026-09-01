-- item-tools: 'Cloak of the Hakkari Worshippers' (22711). Testing Changed columns: stat_value3 (1400 -> 700).
UPDATE `item_template` SET `stat_value3` = 700 WHERE `entry` = 22711 AND `stat_value3` = 1400;
