-- hunter-pet-families F3 (PLAN section 5.3, 5.4, CORE-AUDIT 3.3): every hunter pet family has its own kit, so the
-- placeholders Dash 61684, Last Stand 53478 and Bullheaded 53490 leave every kit. The DSL drops their SkillLineAbility
-- rows (30560, 30572-30590; no stock row or CreatureSpellData record teaches them), but a spell already in pet_spell is
-- not unlearned by the engine (Pet::_LoadSpells adds every saved row), so existing pets lose them here, with their buff
-- auras (Last Stand 53479, Bullheaded 63896) and saved cooldowns.
-- Hunter pets only (character_pet.PetType = 1), bot pets included. Run with the worldserver stopped, otherwise loaded
-- pets save the old rows back. No abdata reset: Pet::CleanupActionBar empties the bar slot of a spell the pet no longer
-- knows on its next load, and the family's slot 2 / slot 3 spells take a free slot (Hunter::SeatDefaultPetBar's
-- newly-learned rule).
DELETE `ps` FROM `pet_spell` AS `ps` JOIN `character_pet` AS `cp` ON `cp`.`id` = `ps`.`guid`
    WHERE `cp`.`PetType` = 1 AND `ps`.`spell` IN (61684, 53478, 53490);
DELETE `pa` FROM `pet_aura` AS `pa` JOIN `character_pet` AS `cp` ON `cp`.`id` = `pa`.`guid`
    WHERE `cp`.`PetType` = 1 AND `pa`.`spell` IN (61684, 53478, 53479, 53490, 63896);
DELETE `pc` FROM `pet_spell_cooldown` AS `pc` JOIN `character_pet` AS `cp` ON `cp`.`id` = `pc`.`guid`
    WHERE `cp`.`PetType` = 1 AND `pc`.`spell` IN (61684, 53478, 53479, 53490, 63896);
