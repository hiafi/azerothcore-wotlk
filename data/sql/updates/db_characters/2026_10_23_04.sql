-- DB update 2026_10_23_03 -> 2026_10_23_04
-- hunter-rework H0-P1 (PET.md section 10): reset hunter pet spells, auras, cooldowns, talents, happiness and action bars.
-- Joined on hunter pets only (character_pet.PetType = 1); pets relearn the right spells on their next summon through
-- the new level-up sets. Run with the worldserver stopped, otherwise loaded pets save the old rows back.
-- The character_talent delete is a 0-row guard (pet ranks live in pet_spell, SHARED E2 rule 1): it keeps a retired
-- pet talent row on the holding tab from leaving orphaned rank rows behind.
-- No at_login | 4 here: H0-P changes no class talent (SHARED E2 rule 7).
DROP TEMPORARY TABLE IF EXISTS `hunter_pet_reset`;
CREATE TEMPORARY TABLE `hunter_pet_reset` (
    `spell` INT UNSIGNED NOT NULL,
    PRIMARY KEY (`spell`)
) ENGINE=InnoDB;
DELETE FROM `hunter_pet_reset`;
INSERT INTO `hunter_pet_reset` (`spell`) VALUES
-- (a) talent rank spells, kept (stock ranks of the 22 kept pet talents)
(61686),
(61687),
(61688),
(61689),
(61690),
(53203),
(53204),
(53205),
(53481),
(53482),
(53175),
(53176),
(19596),
(53409),
(53411),
(53427),
(53429),
(53430),
(53450),
(53451),
(53483),
(53485),
(53186),
(53187),
-- (a) talent rank spells, new (PET block 201700-201799)
(201750),
(201751),
-- (a) talent rank spells, retired / orphaned (every rank of the 30 rows moved to holding tab 60800)
(61682),
(61683),
(61685),
(53182),
(53183),
(53184),
(61680),
(61681),
(52858),
(53178),
(53179),
(63900),
(53477),
(53480),
(53476),
(62764),
(62765),
(62758),
(62762),
(23145),
(53180),
(53181),
(52825),
(55709),
(53401),
(53426),
(53434),
(62759),
(62760),
(53554),
(53555),
(53514),
(53516),
(54044),
(52234),
(53497),
(53511),
(53512),
(53508),
(53517),
-- (b) retired family specials of PET.md 4.6 (33 spells; Kill Command's 58914 ships in H0-P2)
(35290),
(50519),
(50256),
(24423),
(24450),
(59881),
(50245),
(50433),
(26090),
(50271),
(50541),
(50498),
(50871),
(24640),
(4167),
(50285),
(26064),
(24844),
(34889),
(50479),
(35346),
(50518),
(35387),
(50274),
(50318),
(54644),
(54680),
(54706),
(55749),
(56626),
(57386),
(58604),
(61193),
-- (c) re-homed actives, relearned by SkillLineAbility
(61684),
(53478),
(53490),
(1742),
(17253),
(16827),
(49966);

DELETE `ps` FROM `pet_spell` AS `ps` JOIN `character_pet` AS `cp` ON `cp`.`id` = `ps`.`guid` WHERE `cp`.`PetType` = 1 AND `ps`.`spell` IN (SELECT `spell` FROM `hunter_pet_reset`);
DELETE `pa` FROM `pet_aura` AS `pa` JOIN `character_pet` AS `cp` ON `cp`.`id` = `pa`.`guid` WHERE `cp`.`PetType` = 1 AND `pa`.`spell` IN (SELECT `spell` FROM `hunter_pet_reset`);
DELETE `pc` FROM `pet_spell_cooldown` AS `pc` JOIN `character_pet` AS `cp` ON `cp`.`id` = `pc`.`guid` WHERE `cp`.`PetType` = 1;
UPDATE `character_pet` SET `abdata` = '', `curhappiness` = 1050000 WHERE `PetType` = 1;
-- AT_LOGIN_RESET_PET_TALENTS (stabled pets too)
UPDATE `characters` SET `at_login` = `at_login` | 16 WHERE `class` = 3;

-- Furious Howl 24604 changed from +AP to +5% crit: a saved old aura would keep its AP-sized amount as crit
DELETE FROM `character_aura` WHERE `spell` = 24604;

-- T1-8: rows retired to tab 60800 sit on a valid tab, so the cleaner keeps their character_talent rows (0-row guard)
DELETE FROM `character_talent` WHERE `spell` IN (61682, 61683, 61685, 53182, 53183, 53184, 61680, 61681, 52858, 53178, 53179, 63900, 53477, 53480, 53476, 62764, 62765, 62758, 62762, 23145, 53180, 53181, 52825, 55709, 53401, 53426, 53434, 62759, 62760, 53554, 53555, 53514, 53516, 54044, 52234, 53497, 53511, 53512, 53508, 53517, 53478, 53490, 61684);

DROP TEMPORARY TABLE IF EXISTS `hunter_pet_reset`;
