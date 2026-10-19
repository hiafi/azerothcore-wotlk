-- hunter-rework S2a: MM talent reset, orphaned ranks, Silencing Shot baseline, saved-aura cleanup. Run with the worldserver stopped.
-- (MARKSMANSHIP.md section 10.5; ships in the same db-import as S2a's talent_dbc change, SHARED E2 rule 5.)
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 3;
-- orphaned rank spells of tab 363 plus 34490 (Player::_LoadTalents asserts on them, SHARED E2 rule 1)
DELETE FROM `character_talent` WHERE `spell` IN (19419, 19420, 19430, 19431, 19489, 19490, 34488, 34489, 34490, 34950, 34954, 35100, 35102, 35104, 35110, 35111, 53221, 53222, 53224, 53228, 53232, 53245, 53246);
-- Silencing Shot leaves the tree for the baseline (SHARED E2 rule 2): restore it as a learned spell for hunters at 14+
DELETE FROM `character_spell` WHERE `spell` = 34490 AND `guid` IN (SELECT `guid` FROM (SELECT `guid` FROM `characters` WHERE `class` = 3 AND `level` >= 14) AS `hunters`);
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`) SELECT `guid`, 34490, 255 FROM `characters` WHERE `class` = 3 AND `level` >= 14;
-- saved buffs whose meaning changed (Sniper Training, Rapid Killing, Improved Steady Shot, Rapid Recuperation)
DELETE FROM `character_aura` WHERE `spell` IN (64418, 64419, 64420, 35098, 35099, 53220, 56654, 58882) AND `guid` IN (SELECT `guid` FROM (SELECT `guid` FROM `characters` WHERE `class` = 3) AS `hunters`);
