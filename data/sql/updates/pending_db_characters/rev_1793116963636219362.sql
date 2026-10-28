-- rogue-rework S2: run with the worldserver stopped
-- Rogue characters (class 4): reset talents (AT_LOGIN_RESET_TALENTS = 4) for the new Subtlety tree, and drop the rank
-- and button spells S2 removes: the cut ranks of kept talents (Relentless Strikes 58424-58425, Slaughter from the
-- Shadows 51711-51712, Deadliness 30905-30906, Sinister Calling 31219-31220), Master of Subtlety's old ranks 31221-31223
-- (the talent gets fresh ids) and its stock buff 31665, the ranks of the six retired talents (Master of Deception
-- 13958 / 13970 / 13971, Sleight of Hand 30892-30893, Dirty Tricks 14076 / 14094, Setup 13983 / 14070 / 14071, Dirty
-- Deeds 14082-14083, Filthy Tricks 58414-58415), the old Hemorrhage 16511 and Premeditation 14183 buttons (both talents
-- become passives on new ids), and the talent-taught castables Shadow Dance 51713, Shadowstep 36554 and Preparation
-- 14185 (their talents teach them again). Idempotent: every statement is a no-op on a second run.
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 4;

-- Insurance: the tree moves and retires talents, so no class-4 talent row may survive the reset.
DELETE FROM `character_talent`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);

DELETE FROM `character_spell`
WHERE `spell` IN (13958, 13970, 13971, 13983, 14070, 14071, 14076, 14082, 14083, 14094, 14183, 14185, 16511, 30892,
        30893, 30905, 30906, 31219, 31220, 31221, 31222, 31223, 31665, 36554, 51711, 51712, 51713, 58414, 58415, 58424,
        58425)
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);

DELETE FROM `character_action`
WHERE `type` = 0
    AND `action` IN (13958, 13970, 13971, 13983, 14070, 14071, 14076, 14082, 14083, 14094, 14183, 14185, 16511, 30892,
        30893, 30905, 30906, 31219, 31220, 31221, 31222, 31223, 31665, 36554, 51711, 51712, 51713, 58414, 58415, 58424,
        58425)
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);

-- Saved auras also drop the stock buffs no S2 talent triggers any more: Master of Subtlety's hidden helper 31666 and
-- Honor Among Thieves' combo point buff 52916.
DELETE FROM `character_aura`
WHERE `spell` IN (13958, 13970, 13971, 13983, 14070, 14071, 14076, 14082, 14083, 14094, 14183, 14185, 16511, 30892,
        30893, 30905, 30906, 31219, 31220, 31221, 31222, 31223, 31665, 31666, 36554, 51711, 51712, 51713, 52916, 58414,
        58415, 58424, 58425)
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);

DELETE FROM `character_spell_cooldown`
WHERE `spell` IN (13958, 13970, 13971, 13983, 14070, 14071, 14076, 14082, 14083, 14094, 14183, 14185, 16511, 30892,
        30893, 30905, 30906, 31219, 31220, 31221, 31222, 31223, 31665, 36554, 51711, 51712, 51713, 58414, 58415, 58424,
        58425)
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);
