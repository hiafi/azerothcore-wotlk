-- warlock-rework Destruction pass: talent reset (PLAN B5, repeated per pass, DESTRUCTION §3 item 5)
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 9;
-- orphaned talent ranks (SHARED §4b: Player::_LoadTalents asserts before the reset runs) - the
-- repurposed rows' old ranks (965 Improved Searing Pain, 1889 Improved Soul Leech) and every
-- trimmed rank in DESTRUCTION §6
DELETE FROM `character_talent` WHERE `spell` IN (17927, 17929, 17930, 54117, 54118, 17802, 17803, 17791, 17792, 17957, 17958, 59740, 59741, 30291, 30292, 47269, 47270);
