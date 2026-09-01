-- item-tools: 'Seal of the Gurubashi Berserker' (22722). Adding Proc Chance Changed columns: stat_type2 (0 -> 33),
-- stat_value2 (0 -> 20).
UPDATE `item_template` SET `stat_type2` = 33, `stat_value2` = 20 WHERE `entry` = 22722 AND `stat_type2` = 0 AND `stat_value2` = 0;
