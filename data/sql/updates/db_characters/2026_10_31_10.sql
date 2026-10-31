-- DB update 2026_10_31_09 -> 2026_10_31_10
-- rogue-rework S3: run with the worldserver stopped
-- Rogue characters (class 4): reset talents (AT_LOGIN_RESET_TALENTS = 4) for the new Combat tree, and drop the rank and
-- button spells S3 removes: the cut ranks of kept talents (Dual Wield Specialization 13851-13852, Precision
-- 13844-13845, Mace / Weapon Specialization 13802-13803, Hack and Slash 13963-13964, Aggression 61330-61331, Prey on the
-- Weak 51688-51689), the ranks of the six retired talents (Improved Gouge 13741 / 13792 / 13793, Close Quarters Combat
-- 13706 / 13804-13807, Weapon Expertise 30919-30920, Vitality 31122 / 31123 / 61329, Nerves of Steel 31130-31131,
-- Combat Potency 35541 / 35550-35553), and the talent-taught castables Blade Flurry 13877, Adrenaline Rush 13750,
-- Riposte 14251 and Killing Spree 51690 (their talents teach them again). Idempotent: every statement is a no-op on a
-- second run.
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 4;

-- Insurance: the tree moves and retires talents, so no class-4 talent row may survive the reset.
DELETE FROM `character_talent`
WHERE `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);

DELETE FROM `character_spell`
WHERE `spell` IN (13706, 13741, 13750, 13792, 13793, 13802, 13803, 13804, 13805, 13806, 13807, 13844, 13845, 13851,
        13852, 13877, 13963, 13964, 14251, 30919, 30920, 31122, 31123, 31130, 31131, 35541, 35550, 35551, 35552, 35553,
        51688, 51689, 51690, 61329, 61330, 61331)
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);

DELETE FROM `character_action`
WHERE `type` = 0
    AND `action` IN (13706, 13741, 13750, 13792, 13793, 13802, 13803, 13804, 13805, 13806, 13807, 13844, 13845, 13851,
        13852, 13877, 13963, 13964, 14251, 30919, 30920, 31122, 31123, 31130, 31131, 35541, 35550, 35551, 35552, 35553,
        51688, 51689, 51690, 61329, 61330, 61331)
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);

-- Saved auras also drop the stock buffs no S3 talent triggers any more: Combat Potency's energize proc aura 35542 and
-- Killing Spree's +20% damage aura 61851 (its link is removed).
DELETE FROM `character_aura`
WHERE `spell` IN (13706, 13741, 13750, 13792, 13793, 13802, 13803, 13804, 13805, 13806, 13807, 13844, 13845, 13851,
        13852, 13877, 13963, 13964, 14251, 30919, 30920, 31122, 31123, 31130, 31131, 35541, 35542, 35550, 35551, 35552,
        35553, 51688, 51689, 51690, 61329, 61330, 61331, 61851)
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);

DELETE FROM `character_spell_cooldown`
WHERE `spell` IN (13706, 13741, 13750, 13792, 13793, 13802, 13803, 13804, 13805, 13806, 13807, 13844, 13845, 13851,
        13852, 13877, 13963, 13964, 14251, 30919, 30920, 31122, 31123, 31130, 31131, 35541, 35550, 35551, 35552, 35553,
        51688, 51689, 51690, 61329, 61330, 61331)
    AND `guid` IN (SELECT `guid` FROM `characters` WHERE `class` = 4);
