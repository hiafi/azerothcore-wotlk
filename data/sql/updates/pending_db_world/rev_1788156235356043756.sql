-- item-tools: 'Seal of the Gurubashi Berserker' (22722). Testing Changed columns: stat_value2 (20 -> 1400).
UPDATE `item_template` SET `stat_value2` = 1400 WHERE `entry` = 22722 AND `stat_value2` = 20;
