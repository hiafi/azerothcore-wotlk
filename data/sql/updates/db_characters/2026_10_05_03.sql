-- DB update 2026_10_05_02 -> 2026_10_05_03
-- paladin-rework S3 (Protection): talent reset for every paladin (PLAN B5)
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 2;
-- orphaned Prot rank spells (Player::_LoadTalents asserts before the reset runs, SYSTEMS 9.2)
DELETE FROM `character_talent` WHERE `spell` IN (20265, 20266, 20099, 20100, 20146, 20147, 63649, 63650, 20177, 20179, 20180, 20181, 20182, 31844, 31845, 53519, 20174, 20175, 20487, 20488, 53583, 53585, 53695, 53696);
-- Redoubt buffs are rewritten (Strength + DR instead of block%, no charges)
DELETE FROM `character_aura` WHERE `spell` IN (20128, 20131, 20132) AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 2);
