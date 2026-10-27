-- rogue-rework RG0a: run with the worldserver stopped
-- Rogue characters: talent reset, retire the Poisons spell 2842 and the spike spells 204370-204399, strip poison
-- enchants, pull the poison items off the auction house.

-- Talent reset for every rogue (insurance, 0 rows today).
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 4;

DELETE FROM `character_talent`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);

-- Poisons 2842 and the spike range, all classes (the spike reached GM druids).
DELETE FROM `character_spell`
WHERE `spell` = 2842 OR `spell` BETWEEN 204370 AND 204399;

DELETE FROM `character_spell_cooldown`
WHERE `spell` = 2842 OR `spell` BETWEEN 204370 AND 204399;

DELETE FROM `character_aura`
WHERE `spell` = 2842 OR `spell` BETWEEN 204370 AND 204399;

DELETE FROM `character_action`
WHERE `type` = 0 AND (`action` = 2842 OR `action` BETWEEN 204370 AND 204399);

-- Temp-slot enchant (numbers 4-6 of `enchantments`) strip for the 29 poison enchants.
UPDATE `item_instance` SET `enchantments` =
    CONCAT(SUBSTRING_INDEX(`enchantments`, ' ', 3), ' 0 0 0 ',
        SUBSTRING(`enchantments`, LENGTH(SUBSTRING_INDEX(`enchantments`, ' ', 6)) + 2))
WHERE `enchantments` <> ''
    AND (SUBSTRING_INDEX(
    SUBSTRING_INDEX(`enchantments`, ' ', 4), ' ', -1)) IN
    (7, 8, 22, 35, 323, 324, 325, 623, 624, 625, 626, 627, 703, 704, 705, 706, 2630, 2640, 2641, 2642, 2643, 2644,
     3768, 3769, 3770, 3771, 3772, 3773, 3774);

-- AH listings of the 29 poison items: the auction row and its item_instance row in one statement (joined on itemguid).
-- Items in bags and mail stay.
DELETE `ah`, `ii` FROM `auctionhouse` `ah`
INNER JOIN `item_instance` `ii` ON `ii`.`guid` = `ah`.`itemguid`
WHERE `ii`.`itemEntry` IN
    (6947, 6949, 6950, 8926, 8927, 8928, 21927, 43230, 43231, 2892, 2893, 8984, 8985, 20844, 22053, 22054, 43232,
     43233, 10918, 10920, 10921, 10922, 22055, 43234, 43235, 3775, 5237, 21835, 43237);
