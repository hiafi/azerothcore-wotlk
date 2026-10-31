-- DB update 2026_10_31_04 -> 2026_10_31_05
-- death-knight-rework S3: run with the worldserver stopped
-- (character_talent.spell holds the talent RANK spell ids, every rank of the 74 Unholy-tab talents S3 re-cells.)
-- Death Knight characters holding a retired Unholy-era talent: talent reset, drop the dropped rank spells and buttons.
UPDATE `characters` SET `at_login` = `at_login` | 4
WHERE `class` = 6 AND `guid` IN (
    SELECT `guid` FROM (
        SELECT DISTINCT `guid` FROM `character_talent`
        WHERE `spell` IN (
    48962, 48963, 48965, 49013, 49032, 49036, 49146, 49158, 49194, 49206, 49208, 49217, 49219, 49220,
    49223, 49224, 49562, 49564, 49565, 49567, 49568, 49571, 49572, 49588, 49589, 49599, 49610, 49611,
    49627, 49628, 49631, 49632, 49633, 49635, 49636, 49638, 49654, 49655, 50117, 50118, 50119, 50120,
    50121, 51099, 51160, 51161, 51267, 51459, 51462, 51463, 51464, 51465, 51745, 51746, 52143, 55090,
    55129, 55130, 55131, 55132, 55133, 55236, 55237, 55620, 55623, 55666, 55667, 56834, 56835, 66799,
    66814, 66815, 66816, 66817
        )
    ) AS `dk_talent_guids`
);

DELETE FROM `character_talent`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `spell` IN (
    48962, 48963, 48965, 49013, 49032, 49036, 49146, 49158, 49194, 49206, 49208, 49217, 49219, 49220,
    49223, 49224, 49562, 49564, 49565, 49567, 49568, 49571, 49572, 49588, 49589, 49599, 49610, 49611,
    49627, 49628, 49631, 49632, 49633, 49635, 49636, 49638, 49654, 49655, 50117, 50118, 50119, 50120,
    50121, 51099, 51160, 51161, 51267, 51459, 51462, 51463, 51464, 51465, 51745, 51746, 52143, 55090,
    55129, 55130, 55131, 55132, 55133, 55236, 55237, 55620, 55623, 55666, 55667, 56834, 56835, 66799,
    66814, 66815, 66816, 66817
    );

DELETE FROM `character_spell`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `spell` IN (
    55132, 55133, 51464, 51465, 49636, 49638, 50120, 50121,
    66816, 66817
    );

DELETE FROM `character_spell_cooldown`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `spell` IN (
    55132, 55133, 51464, 51465, 49636, 49638, 50120, 50121,
    66816, 66817
    );

DELETE FROM `character_aura`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `spell` IN (
    55132, 55133, 51464, 51465, 49636, 49638, 50120, 50121,
    66816, 66817
    );

DELETE FROM `character_action`
WHERE `type` = 0 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6)
    AND `action` IN (
    55132, 55133, 51464, 51465, 49636, 49638, 50120, 50121,
    66816, 66817
    );
