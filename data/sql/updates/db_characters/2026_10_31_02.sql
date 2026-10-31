-- DB update 2026_10_31_01 -> 2026_10_31_02
-- death-knight-rework S1: run with the worldserver stopped
-- Death Knight characters: talent reset (insurance), drop the retired rank spells and their passives.
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 6;

DELETE FROM `character_talent` WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6);

DELETE FROM `character_spell`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `spell` IN (
    55225, 55226, 49392, 49393, 49479, 49480, 61157, 61158,
    50110, 50111, 61277, 61278, 64858, 64859
    );

DELETE FROM `character_action`
WHERE `type` = 0 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `action` IN (
    55225, 55226, 49392, 49393, 49479, 49480, 61157, 61158,
    50110, 50111, 61277, 61278, 64858, 64859
    );

DELETE FROM `character_spell_cooldown`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `spell` IN (
    55225, 55226, 49392, 49393, 49479, 49480, 61157, 61158,
    50110, 50111, 61277, 61278, 64858, 64859
    );

DELETE FROM `character_aura`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `spell` IN (
    55225, 55226, 49392, 49393, 49479, 49480, 61157, 61158,
    50110, 50111, 61277, 61278, 64858, 64859
    );
