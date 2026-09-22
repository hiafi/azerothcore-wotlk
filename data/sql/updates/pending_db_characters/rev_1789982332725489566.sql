--
-- Priest Discipline rework (docs/reworks/priest-disc-rework.md): talent tree shape changes and
-- several stock talent IDs are repurposed into new talents, so points left in a repurposed row
-- are not safe to keep. Force a talent reset for every Priest on next login.
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 5;
