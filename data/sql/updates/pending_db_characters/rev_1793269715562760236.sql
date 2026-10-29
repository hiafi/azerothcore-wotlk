-- warrior-rework W0a: run with the worldserver stopped
-- Drops the spike-range spells 204869-204899 and the client's unused dev Heroic Leap 6544 from every character, and the
-- spells W0a removes from warriors (694, 20230, 20252) from class-1 characters. No talent reset.

-- All classes: spell 6544 and the 204869-204899 range.
DELETE FROM `character_spell`
WHERE `spell` = 6544 OR `spell` BETWEEN 204869 AND 204899;

DELETE FROM `character_spell_cooldown`
WHERE `spell` = 6544 OR `spell` BETWEEN 204869 AND 204899;

DELETE FROM `character_aura`
WHERE `spell` = 6544 OR `spell` BETWEEN 204869 AND 204899;

DELETE FROM `character_action`
WHERE `type` = 0 AND (`action` = 6544 OR `action` BETWEEN 204869 AND 204899);

-- Class 1 (warrior) only: spells 694, 20230 and 20252.
DELETE FROM `character_spell`
WHERE `spell` IN (694, 20230, 20252)
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 1);

DELETE FROM `character_spell_cooldown`
WHERE `spell` IN (694, 20230, 20252)
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 1);

DELETE FROM `character_aura`
WHERE `spell` IN (694, 20230, 20252)
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 1);

DELETE FROM `character_action`
WHERE `type` = 0
    AND `action` IN (694, 20230, 20252)
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 1);
