-- shaman-rework SH0b: character data cleanup. Run with the worldserver stopped.
-- Stoneclaw Totem retired
DELETE FROM `character_spell` WHERE `spell` = 5730;
DELETE FROM `character_action` WHERE `type` = 0 AND `action` = 5730;
-- Magma Totem moves to the new player spell 202268 (drop the old row first if the character already has the new one)
DELETE `cs` FROM `character_spell` `cs` JOIN `character_spell` `n` ON `n`.`guid` = `cs`.`guid` AND `n`.`spell` = 202268 WHERE `cs`.`spell` = 8190;
UPDATE `character_spell` SET `spell` = 202268 WHERE `spell` = 8190;
UPDATE `character_action` SET `action` = 202268 WHERE `type` = 0 AND `action` = 8190;
-- spells whose cooldown category changed
DELETE FROM `character_spell_cooldown` WHERE `spell` IN (2062, 2894, 2484, 8177, 5730, 8190);
