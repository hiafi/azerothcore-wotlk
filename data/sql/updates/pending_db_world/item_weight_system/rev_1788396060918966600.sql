-- Phase 5 content, Bucket 1: re-regenerates the 9 items whose original guarded UPDATE (from the ilvl 60-100 batch,
-- before lib/emit.py's _guard_term fix) silently affected 0 rows -- same root cause as the Two-Hand DPS boost incident
-- (docs/bugs-and-fixes.md), just hit by an *original* (not computed) dmg_min1/dmg_max1 value that happened to not be
-- exactly float32-representable. This regenerate now uses the fixed guard.

UPDATE `item_template` SET `dmg_min1` = 141.6471, `dmg_max1` = 263.0589 WHERE `entry` = 20660 AND ABS(`dmg_min1` - 141.647) < 0.01 AND ABS(`dmg_max1` - 263.059) < 0.01;
UPDATE `item_template` SET `dmg_min1` = 203.3255, `dmg_max1` = 377.60450000000003 WHERE `entry` = 21134 AND ABS(`dmg_min1` - 203.326) < 0.01 AND ABS(`dmg_max1` - 377.604) < 0.01;
UPDATE `item_template` SET `dmg_min1` = 159.8436, `dmg_max1` = 296.85240000000005 WHERE `entry` = 21492 AND ABS(`dmg_min1` - 159.844) < 0.01 AND ABS(`dmg_max1` - 296.852) < 0.01;
UPDATE `item_template` SET `stat_type1` = 5, `stat_value1` = 7, `stat_type2` = 45, `stat_value2` = 64, `stat_type3` = 7, `stat_value3` = 14, `dmg_min1` = 120.74439999999998, `dmg_max1` = 224.2396, `spellid_1` = 0, `spelltrigger_1` = 0 WHERE `entry` = 23459 AND `stat_type1` = 7 AND `stat_value1` = 14 AND `stat_type2` = 5 AND `stat_value2` = 8 AND `stat_type3` = 0 AND `stat_value3` = 0 AND ABS(`dmg_min1` - 68.8) < 0.01 AND ABS(`dmg_max1` - 172.8) < 0.01 AND `spellid_1` = 29369 AND `spelltrigger_1` = 1;
UPDATE `item_template` SET `dmg_max1` = 290.39400000000006 WHERE `entry` = 25537 AND ABS(`dmg_max1` - 290.394) < 0.01;
UPDATE `item_template` SET `dmg_min1` = 180.45719999999997, `dmg_max1` = 335.1348 WHERE `entry` = 30086 AND ABS(`dmg_min1` - 180.457) < 0.01 AND ABS(`dmg_max1` - 335.135) < 0.01;
