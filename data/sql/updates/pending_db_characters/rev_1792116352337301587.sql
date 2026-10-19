-- hunter-rework S1b: (10,1) becomes Stampede; talent reset. Run with the worldserver stopped.
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 3;
-- talent row 2139 no longer names 53270 (Kindred Spirits' linked spell still grants it as an aura)
DELETE FROM `character_talent` WHERE `spell` = 53270;
