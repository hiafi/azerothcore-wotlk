-- DB update 2026_09_27_03 -> 2026_09_27_04
-- Custom: druid-rework Feral follow-up. Claw (1082) is retired and Shred (5221) takes its place (learned at
-- level 20, no behind-the-target requirement). Every druid who knew Claw gets Shred, Claw action buttons
-- become Shred, and Claw is dropped from the spellbook.
INSERT IGNORE INTO `character_spell` (`guid`, `spell`, `specMask`)
SELECT `guid`, 5221, `specMask` FROM `character_spell` WHERE `spell` = 1082;
UPDATE `character_action` SET `action` = 5221 WHERE `action` = 1082 AND `type` = 0;
DELETE FROM `character_spell` WHERE `spell` = 1082;
