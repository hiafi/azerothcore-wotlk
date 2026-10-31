-- DB update 2026_10_31_03 -> 2026_10_31_04
-- death-knight-rework S2 (user ruling 2026-10-25): run with the worldserver stopped
-- Improved Icy Talons (talent 2223, rank spell 55610) is removed as a talent: its party/raid melee haste is now a hidden
-- aura linked to Icy Talons rank 3. Death Knight characters holding the old rank: talent reset at login, drop the rank.
UPDATE `characters` SET `at_login` = `at_login` | 4
WHERE `class` = 6 AND `guid` IN (
    SELECT `guid` FROM (
        SELECT `guid` FROM `character_talent` WHERE `spell` = 55610
        UNION
        SELECT `guid` FROM `character_spell` WHERE `spell` = 55610
    ) AS `improved_icy_talons_guids`
);

DELETE FROM `character_talent`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6) AND `spell` = 55610;

DELETE FROM `character_spell`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6) AND `spell` = 55610;

DELETE FROM `character_action`
WHERE `type` = 0 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6) AND `action` = 55610;

DELETE FROM `character_aura`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 6) AND `spell` = 55610;
