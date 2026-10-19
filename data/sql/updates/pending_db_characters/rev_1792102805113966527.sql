-- hunter-rework S1a: BM talent reset, orphaned ranks, Intimidation baseline, saved-aura cleanup. Run with the worldserver stopped.
-- (BEAST-MASTERY.md section 3 item 7 without 53270: row 2139 stays stock Beast Mastery in S1a, S1b deletes 53270.)
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 3;
DELETE FROM `character_talent` WHERE `spell` IN (19549, 19550, 19551, 19555, 19556, 19572, 19573, 19577, 19578, 19586, 19587, 19590, 19592, 19601, 19602, 19609, 19610, 19612, 19619, 19620, 19621, 19622, 19623, 19624, 19625, 20895, 34469, 34470, 34692, 53252, 53253, 53265, 56317, 56318);
-- Intimidation leaves the tree (SHARED E2.2): restore it as a learned spell for hunters at 30+
DELETE FROM `character_spell` WHERE `spell` = 19577 AND `guid` IN (SELECT `guid` FROM (SELECT `guid` FROM `characters` WHERE `class` = 3 AND `level` >= 30) AS `hunters`);
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`) SELECT `guid`, 19577, 255 FROM `characters` WHERE `class` = 3 AND `level` >= 30;
-- saved buffs whose effects change (19574 lives on the pet only, so it is in the pet_aura list)
DELETE FROM `character_aura` WHERE `spell` = 34471 AND `guid` IN (SELECT `guid` FROM (SELECT `guid` FROM `characters` WHERE `class` = 3) AS `hunters`);
-- 53257 (Cobra Strikes buff) is granted by nothing after S1a
DELETE `pa` FROM `pet_aura` AS `pa` JOIN `character_pet` AS `cp` ON `cp`.`id` = `pa`.`guid` WHERE `cp`.`PetType` = 1 AND `pa`.`spell` IN (19574, 35060, 35061, 53257, 57447, 57452, 57453, 57483, 57484, 57485, 75593);
