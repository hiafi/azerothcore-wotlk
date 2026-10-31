-- Testpri (guid 1146, level 60 priest) predates the heal-line collapse and never got Greater Heal 2060 (the level-1
-- baseline heal). Apply with worldserver STOPPED: character data is cached while the character is online.
DELETE FROM `character_spell` WHERE `guid` = 1146 AND `spell` = 2060;
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`) VALUES (1146, 2060, 255);
