-- rogue-rework RG0b: run with the worldserver stopped
-- Rogue characters: reset talents (AT_LOGIN_RESET_TALENTS = 4), move stock Shiv 5938 -> new Shiv 203725.
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 4;

-- Insurance: Ghostly Strike's talent (303) leaves the tree, so no class-4 talent row may survive.
DELETE FROM `character_talent`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);

-- Characters that already hold 203725 just lose the old row.
DELETE `old` FROM `character_spell` AS `old`
INNER JOIN `character_spell` AS `new` ON `new`.`guid` = `old`.`guid` AND `new`.`spell` = 203725
WHERE `old`.`spell` = 5938 AND `old`.`guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);

UPDATE `character_spell` SET `spell` = 203725
WHERE `spell` = 5938 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);

UPDATE `character_action` SET `action` = 203725
WHERE `type` = 0 AND `action` = 5938
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);
