-- death-knight-rework S2: run with the worldserver stopped
-- (character_talent.spell holds the talent RANK spell ids, every rank of the 23 Frost-tab talents S2 re-cells.)
-- Death Knight characters holding a retired Frost/Unholy-era talent: talent reset, drop the retired rank spells and buttons.
UPDATE `characters` SET `at_login` = `at_login` | 4
WHERE `class` = 6 AND `guid` IN (
    SELECT `guid` FROM (
        SELECT DISTINCT `guid` FROM `character_talent`
        WHERE `spell` IN (
    49042, 49786, 49787, 49788, 49789, 49137, 49657, 49140,
    49661, 49662, 49663, 49664, 49796, 49149, 50115, 49184,
    49188, 56822, 59057, 49024, 49538, 49200, 50151, 50152,
    49202, 50127, 50128, 50129, 50130, 49203, 49455, 50147,
    49226, 50137, 50138, 49471, 49790, 49791, 49175, 50031,
    51456, 50187, 50190, 50191, 50880, 50884, 50885, 50886,
    50887, 51123, 51127, 51128, 51129, 51130, 51468, 51472,
    51473, 54639, 54638, 54637, 55610, 50040, 50041, 50043,
    65661, 66191, 66192
        )
    ) AS `dk_talent_guids`
);

DELETE FROM `character_talent`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `spell` IN (
    49042, 49786, 49787, 49788, 49789, 49137, 49657, 49140,
    49661, 49662, 49663, 49664, 49796, 49149, 50115, 49184,
    49188, 56822, 59057, 49024, 49538, 49200, 50151, 50152,
    49202, 50127, 50128, 50129, 50130, 49203, 49455, 50147,
    49226, 50137, 50138, 49471, 49790, 49791, 49175, 50031,
    51456, 50187, 50190, 50191, 50880, 50884, 50885, 50886,
    50887, 51123, 51127, 51128, 51129, 51130, 51468, 51472,
    51473, 54639, 54638, 54637, 55610, 50040, 50041, 50043,
    65661, 66191, 66192
    );

DELETE FROM `character_spell`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `spell` IN (
    49788, 49789, 49663, 49664, 50886, 50887, 58577, 58578,
    51129, 51130, 50129, 50130, 49796, 49203
    );

DELETE FROM `character_action`
WHERE `type` = 0 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `action` IN (
    49788, 49789, 49663, 49664, 50886, 50887, 58577, 58578,
    51129, 51130, 50129, 50130, 49796, 49203
    );

DELETE FROM `character_spell_cooldown`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `spell` IN (
    49788, 49789, 49663, 49664, 50886, 50887, 58577, 58578,
    51129, 51130, 50129, 50130, 49796, 49203
    );

DELETE FROM `character_aura`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `spell` IN (
    49788, 49789, 49663, 49664, 50886, 50887, 58577, 58578,
    51129, 51130, 50129, 50130, 49796, 49203
    );
