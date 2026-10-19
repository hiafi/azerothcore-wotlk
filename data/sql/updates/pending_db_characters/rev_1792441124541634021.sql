-- shaman-rework SH0a: character data cleanup. Run with the worldserver stopped.
-- imbue temp enchants (Rockbiter/Flametongue/Frostbrand/Windfury/Earthliving ids, T0a report section 7): zero the temp-slot triple
UPDATE `item_instance`
SET `enchantments` = CONCAT(SUBSTRING_INDEX(`enchantments`, ' ', 3), ' 0 0 0 ', REGEXP_REPLACE(`enchantments`, '^(\\d+ ){6}', ''))
WHERE CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(`enchantments`, ' ', 4), ' ', -1) AS UNSIGNED) IN (29, 6, 1, 503, 3021, 3022, 3023, 3024, 3025, 3026, 3027, 3028, 3029, 3030, 3031, 3032, 5, 4, 3, 523, 1665, 1666, 2634, 3779, 3780, 3781, 2, 12, 524, 1667, 1668, 2635, 3782, 3783, 3784, 283, 284, 525, 1669, 2636, 3014, 3785, 3786, 3787, 3345, 3346, 3347, 3348, 3349, 3350);
-- force a talent reset for every shaman
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 7;
-- removed talents
DELETE FROM `character_talent` WHERE `spell` IN (30706, 30798, 974, 51886);
-- removed spells and their action bar buttons
DELETE FROM `character_spell` WHERE `spell` IN (8071, 8075, 8227, 8181, 8184, 5675, 10595, 8512, 6495, 3738, 30706, 526, 66842, 66843, 66844);
DELETE FROM `character_action` WHERE `type` = 0 AND `action` IN (8071, 8075, 8227, 8181, 8184, 5675, 10595, 8512, 6495, 3738, 30706, 526, 66842, 66843, 66844);
-- spells whose cooldown category changed
DELETE FROM `character_spell_cooldown` WHERE `spell` IN (8042, 8050, 8056, 421, 1535);
