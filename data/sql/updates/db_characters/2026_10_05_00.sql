-- DB update 2026_09_29_00 -> 2026_10_05_00
-- paladin-rework S1: talent reset for every paladin (PLAN B5)
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 2;
-- orphaned talent ranks (Player::_LoadTalents asserts before the reset, Player.cpp:15610-15626)
DELETE FROM `character_talent` WHERE `spell` IN (20060, 20061, 20062, 20063, 20064, 20375, 20066, 35395, 20104, 20105, 20120, 20121, 31878);
-- Judgement of Light -> Judgement (+ Deliverance from 20); old castables and Seal of Corruption gone
DELETE FROM `character_spell` WHERE `spell` = 201060;
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`) SELECT `guid`, 201060, `specMask` FROM `character_spell` WHERE `spell` = 20271;
DELETE FROM `character_spell` WHERE `spell` = 201061;
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`) SELECT `cs`.`guid`, 201061, `cs`.`specMask` FROM `character_spell` `cs` JOIN `characters` `c` ON `c`.`guid` = `cs`.`guid` WHERE `cs`.`spell` = 20271 AND `c`.`level` >= 20;
UPDATE `character_action` SET `action` = 201060 WHERE `type` = 0 AND `action` = 20271;
DELETE FROM `character_spell` WHERE `spell` IN (20271, 53407, 53408, 53736, 20154);
DELETE FROM `character_action` WHERE `type` = 0 AND `action` IN (53407, 53408, 53736, 20154);
-- review-2 (S-M3): talent-taught Seal of Command / Repentance were TEMPORARY spells; restore them as baseline (real players; bots are regenerated)
DELETE FROM `character_spell` WHERE `spell` = 20375;
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`) SELECT `guid`, 20375, 255 FROM `characters` WHERE `class` = 2 AND `level` >= 20;
DELETE FROM `character_spell` WHERE `spell` = 20066;
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`) SELECT `guid`, 20066, 255 FROM `characters` WHERE `class` = 2 AND `level` >= 22;
-- review-2: saved seal auras would reload with the new effects / 30-min durations; stale SoR rank and SoC auras
DELETE FROM `character_aura` WHERE `spell` IN (21084, 20154, 20164, 20165, 20166, 20375, 31801, 53736, 20170, 20167, 20168) AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 2);
-- paladin-rework S1, SHARED Part C: Resistance Aura collapse (Frost 19888 / Fire 19891 -> 19876)
DELETE FROM `character_spell` WHERE `spell` = 19876 AND `guid` IN (SELECT `guid` FROM (SELECT DISTINCT `guid` FROM `character_spell` WHERE `spell` IN (19888, 19891)) AS `old_resist`);
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`) SELECT DISTINCT `guid`, 19876, 255 FROM `character_spell` WHERE `spell` IN (19888, 19891);
DELETE FROM `character_spell` WHERE `spell` IN (19888, 19891);
UPDATE `character_action` SET `action` = 19876 WHERE `type` = 0 AND `action` IN (19888, 19891);
-- saved aura amounts would reload stale: Concentration 149 -> 85 (35 would read as 35 mp5), Resistance misc 32 -> 52
-- Righteous Fury gains eff2 (C3): _LoadAuras re-applies the saved effectMask, so a saved 25780 would never get it;
-- 57340 goes too (else it reloads orphaned); Frost Presence re-adds its own 57340 on load via the 48263 aura link
-- 63514 (old Improved Devotion Aura effect): nothing removes a saved one once -20138's script is unbound (C1.7)
DELETE FROM `character_aura` WHERE `spell` IN (19746, 19876, 19888, 19891, 25780, 57340, 63514);
