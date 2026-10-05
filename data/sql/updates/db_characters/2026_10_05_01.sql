-- DB update 2026_10_05_00 -> 2026_10_05_01
-- paladin-rework S1 follow-up: Redemption is single-rank (7328); drop the higher ranks from characters that learned them
UPDATE `character_action` SET `action` = 7328 WHERE `type` = 0 AND `action` IN (10322, 10324, 20772, 20773, 48949, 48950) AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 2);
DELETE FROM `character_spell` WHERE `spell` IN (10322, 10324, 20772, 20773, 48949, 48950) AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 2);
