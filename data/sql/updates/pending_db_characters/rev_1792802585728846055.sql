-- death-knight-rework DK0a: run with the worldserver stopped
-- Death Knight characters: talent reset, drop retired spells, bar entries, auras, spike spells (203680-203699).
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 6;

DELETE FROM `character_talent` WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6);

DELETE FROM `character_spell`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND (`spell` IN (
    45902, 48263, 48265, 48982, 48985, 49016, 49039, 49143, 49186, 49222, 49467, 49488,
    49489, 50033, 50034, 50365, 50371, 50384, 50385, 50391, 50392, 51052, 51108, 51109,
    51271, 55050, 55061, 55062, 63560
    ) OR `spell` BETWEEN 203680 AND 203699);

DELETE FROM `character_action`
WHERE `type` = 0 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND (`action` IN (
    45902, 48263, 48265, 48982, 48985, 49016, 49039, 49143, 49186, 49222, 49467, 49488,
    49489, 50033, 50034, 50365, 50371, 50384, 50385, 50391, 50392, 51052, 51108, 51109,
    51271, 55050, 55061, 55062, 63560
    ) OR `action` BETWEEN 203680 AND 203699);

DELETE FROM `character_spell_cooldown`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND (`spell` IN (
    45902, 48263, 48265, 48982, 48985, 49016, 49039, 49143, 49186, 49222, 49467, 49488,
    49489, 50033, 50034, 50365, 50371, 50384, 50385, 50391, 50392, 51052, 51108, 51109,
    51271, 55050, 55061, 55062, 63560
    ) OR `spell` BETWEEN 203680 AND 203699);

DELETE FROM `character_aura`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND (`spell` IN (48263, 48265, 63611) OR `spell` BETWEEN 203680 AND 203699);

DELETE FROM `pet_aura`
WHERE `spell` BETWEEN 203680 AND 203699
    AND `guid` IN (SELECT `id` FROM `character_pet` WHERE `owner` IN (
        SELECT `guid` FROM `characters` WHERE `class` = 6));

DELETE FROM `pet_spell`
WHERE `spell` BETWEEN 203680 AND 203699
    AND `guid` IN (SELECT `id` FROM `character_pet` WHERE `owner` IN (
        SELECT `guid` FROM `characters` WHERE `class` = 6));
