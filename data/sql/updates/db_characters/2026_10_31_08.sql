-- DB update 2026_10_31_07 -> 2026_10_31_08
-- rogue-rework S1: run with the worldserver stopped
-- Rogue characters (class 4): reset talents (AT_LOGIN_RESET_TALENTS = 4) for the new Assassination tree, and drop the
-- rank and buff spells S1 removes: the cut ranks of kept talents (Malice 14141-14142, Lethality 14136-14137, Improved
-- Poisons 14116-14117, Seal Fate 14194-14195), stock Overkill 58426 and its aura 58427, and the ranks of the five retired
-- talents (Improved Eviscerate 14162-14164, Improved Expose Armor 14168-14169, Improved Kidney Shot 14174-14176, Turn the
-- Tables 51627-51629, Cut to the Chase 51664-51665, 51667-51669). Idempotent: every statement is a no-op on a second run.
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 4;

-- Insurance: the tree moves and retires talents, so no class-4 talent row may survive the reset.
DELETE FROM `character_talent`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);

DELETE FROM `character_spell`
WHERE `spell` IN (14116, 14117, 14136, 14137, 14141, 14142, 14162, 14163, 14164, 14168, 14169, 14174, 14175, 14176,
        14194, 14195, 51627, 51628, 51629, 51664, 51665, 51667, 51668, 51669, 58426, 58427)
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);

DELETE FROM `character_action`
WHERE `type` = 0
    AND `action` IN (14116, 14117, 14136, 14137, 14141, 14142, 14162, 14163, 14164, 14168, 14169, 14174, 14175, 14176,
        14194, 14195, 51627, 51628, 51629, 51664, 51665, 51667, 51668, 51669, 58426, 58427)
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);

-- Saved auras also drop the stock buffs no S1 talent triggers any more: Remorseless Attacks 14143 / 14149 and Turn the
-- Tables 52910 / 52914 / 52915.
DELETE FROM `character_aura`
WHERE `spell` IN (14116, 14117, 14136, 14137, 14141, 14142, 14143, 14149, 14162, 14163, 14164, 14168, 14169, 14174,
        14175, 14176, 14194, 14195, 51627, 51628, 51629, 51664, 51665, 51667, 51668, 51669, 52910, 52914, 52915, 58426,
        58427)
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);

DELETE FROM `character_spell_cooldown`
WHERE `spell` IN (14116, 14117, 14136, 14137, 14141, 14142, 14162, 14163, 14164, 14168, 14169, 14174, 14175, 14176,
        14194, 14195, 51627, 51628, 51629, 51664, 51665, 51667, 51668, 51669, 58426, 58427)
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);
