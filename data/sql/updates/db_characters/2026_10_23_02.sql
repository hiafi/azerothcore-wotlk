-- DB update 2026_10_23_01 -> 2026_10_23_02
-- hunter-rework H0: talent reset (PLAN D6). H0 orphans no talent rank, so no character_talent delete.
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 3;
-- saved aspect and proc auras would reload with their old effects
DELETE FROM `character_aura` WHERE `spell` IN (13165, 61846, 61847, 61848, 13161, 61669, 34074, 13163, 60798, 6150, 3045, 19263) AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 3);
-- the retired Aspect of the Beast pet aura
DELETE FROM `pet_aura` WHERE `spell` = 61669;
