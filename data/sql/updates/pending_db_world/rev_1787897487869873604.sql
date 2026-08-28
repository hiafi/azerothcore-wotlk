-- item-tools: 'Cloak of the Hakkari Worshippers' (22711). Adding CDR Changed columns: stat_type3 (0 -> 24), stat_value3
-- (0 -> 20).
UPDATE `item_template` SET `stat_type3` = 24, `stat_value3` = 20 WHERE `entry` = 22711 AND `stat_type3` = 0 AND `stat_value3` = 0;
