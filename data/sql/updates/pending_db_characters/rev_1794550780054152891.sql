-- hunter-pet-families F0 (PLAN section 5.4, CORE-AUDIT 3.3): Cower 1742 leaves every hunter pet kit. The DSL retires
-- its SkillLineAbility rows and strips it from every family's CreatureSpellData record, but a spell already in pet_spell
-- is not unlearned by the engine (Pet::_LoadSpells adds every saved row), so existing pets lose it here.
-- Hunter pets only (character_pet.PetType = 1), bot pets included. Run with the worldserver stopped, otherwise loaded
-- pets save the old rows back. No abdata reset: the kit v2 marker 202014 re-seats every pet's bar once on its next
-- summon (Hunter::SeatDefaultPetBar), and Pet::CleanupActionBar drops the unknown Cower slot on load.
-- Dash 61684, Last Stand 53478 and Bullheaded 53490 stay until F3 (the 27 families' placeholders).
DELETE `ps` FROM `pet_spell` AS `ps` JOIN `character_pet` AS `cp` ON `cp`.`id` = `ps`.`guid` WHERE `cp`.`PetType` = 1 AND `ps`.`spell` = 1742;
DELETE `pa` FROM `pet_aura` AS `pa` JOIN `character_pet` AS `cp` ON `cp`.`id` = `pa`.`guid` WHERE `cp`.`PetType` = 1 AND `pa`.`spell` = 1742;
DELETE `pc` FROM `pet_spell_cooldown` AS `pc` JOIN `character_pet` AS `cp` ON `cp`.`id` = `pc`.`guid` WHERE `cp`.`PetType` = 1 AND `pc`.`spell` = 1742;
