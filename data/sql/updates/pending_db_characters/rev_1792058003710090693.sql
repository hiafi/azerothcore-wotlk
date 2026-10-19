-- hunter-rework H0-P2 (PET.md section 6.1): Kill Command 34026 has no aura after H0-P2; a saved stock aura row would
-- recreate one and wake the 34026 hardcodes (PET 6.1). Run with the worldserver stopped, otherwise loaded hunters and
-- pets save the old rows back.
-- Furious Howl (review P1-5): a wolf's own Furious Howl buff is saved in pet_aura with the old AP-sized amount, which
-- would reload as crit on the new crit aura (24604 is now +5% crit); the stale rows are dropped so the aura is recast.
-- All pet_aura 24604 rows are removed without a hunter-pet join: only hunter wolves ever cast it.
-- All statements are idempotent.
DELETE FROM `character_aura` WHERE `spell` IN (34026, 34027) AND `guid` IN (SELECT `guid` FROM (SELECT `guid` FROM `characters` WHERE `class` = 3) AS `hunters`);
DELETE `pa` FROM `pet_aura` AS `pa` JOIN `character_pet` AS `cp` ON `cp`.`id` = `pa`.`guid` WHERE `cp`.`PetType` = 1 AND `pa`.`spell` = 58914;
DELETE FROM `pet_aura` WHERE `spell` = 24604;
