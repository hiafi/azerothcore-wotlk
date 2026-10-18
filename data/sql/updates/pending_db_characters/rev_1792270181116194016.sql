-- hunter-rework S3a: SV talent reset, orphaned ranks, saved-aura cleanup. Run with the worldserver stopped.
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 3;
-- rank spells that no longer belong to any tab-362 talent (SURVIVAL.md section 6); Sniper Training (2143) and Lock and Load stay
DELETE FROM `character_talent` WHERE `spell` IN (19498, 19499, 19500, 52783, 52785, 52786, 52787, 52788, 19159, 19160, 19295, 19297, 19298, 19306, 3674, 53295, 53296, 53297, 24296, 24297, 19258, 19259, 34499, 34838, 34839);
-- saved buffs whose effects change
DELETE FROM `character_aura` WHERE `spell` IN (56453, 67544, 34501, 34833, 34834, 34835, 34836, 34837) AND `guid` IN (SELECT `guid` FROM (SELECT `guid` FROM `characters` WHERE `class` = 3) AS `hunters`);
