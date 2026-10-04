-- paladin-rework S2 (Holy): talent reset for every paladin (HOLY §12; repeats S1's reset, harmless)
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 2;
-- orphaned / cut Holy talent ranks (Player::_LoadTalents asserts before the reset runs, SYSTEMS 9.2)
DELETE FROM `character_talent` WHERE `spell` IN (20208, 20209, 20224, 20225, 20330, 20331, 20332, 20260, 20261, 31821, 20214, 20215, 20216, 5926, 25829, 31828, 31829, 31830, 31840, 31841, 54154, 54155);
-- removed talent castables: Aura Mastery (31821) and Divine Favor (20216)
DELETE FROM `character_spell` WHERE `spell` IN (31821, 20216);
DELETE FROM `character_action` WHERE `type` = 0 AND `action` IN (31821, 20216);
