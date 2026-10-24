-- death-knight-rework DK0b: run with the worldserver stopped
-- Death Knight characters: retire Runeforging and the 8 cut runes, move Obliterate 49020 -> 203054, drop rune buffs.
DELETE FROM `character_spell`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `spell` IN (53428, 53341, 53331, 53342, 54447, 53323, 54446, 62158, 70164);

DELETE FROM `character_action`
WHERE `type` = 0 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `action` IN (53428, 53341, 53331, 53342, 54447, 53323, 54446, 62158, 70164);

DELETE FROM `character_skills`
WHERE `skill` = 776 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6);

DELETE FROM `character_spell_cooldown`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `spell` IN (53428, 53341, 53331, 53342, 54447, 53323, 54446, 62158, 70164);

-- U2: Obliterate becomes the new spell 203054; holders keep their spec mask and their bar slot.
UPDATE `character_spell` SET `spell` = 203054
WHERE `spell` = 49020 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6);

DELETE FROM `character_spell`
WHERE `spell` = 49020 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6);

UPDATE `character_action` SET `action` = 203054
WHERE `type` = 0 AND `action` = 49020
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6);

DELETE FROM `character_spell_cooldown`
WHERE `spell` = 49020 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6);

-- Buffs and procs of the retired runes (Fallen Crusader 53365 and Razorice 50401/51714 stay).
DELETE FROM `character_aura`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `spell` IN (53387, 56903, 53362, 53386, 54448, 54449, 62157, 70163);

-- A21: strip every runeforge permanent enchant (slot 0 = first three numbers: id, duration, charges) on all items.
UPDATE `item_instance` SET `enchantments` =
    CONCAT('0 0 0 ', SUBSTRING(`enchantments`, LENGTH(SUBSTRING_INDEX(`enchantments`, ' ', 3)) + 2))
WHERE `enchantments` LIKE '3365 %' OR `enchantments` LIKE '3366 %' OR `enchantments` LIKE '3367 %'
    OR `enchantments` LIKE '3368 %' OR `enchantments` LIKE '3369 %' OR `enchantments` LIKE '3370 %'
    OR `enchantments` LIKE '3594 %' OR `enchantments` LIKE '3595 %' OR `enchantments` LIKE '3847 %'
    OR `enchantments` LIKE '3883 %';
