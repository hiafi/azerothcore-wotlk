-- warlock-rework Demonology pass: talent reset (PLAN B5, repeated per pass, DEMONOLOGY §3.5 item 1)
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 9;
-- Curse of Doom removed, replaced by Bane of Doom (DEMONOLOGY §4.6)
DELETE FROM `character_spell` WHERE `spell` = 603;
DELETE FROM `character_action` WHERE `type` = 0 AND `action` = 603;
-- orphaned talent ranks (SHARED §4b: Player::_LoadTalents asserts before the reset runs) - the
-- repurposed rows' old ranks (1224 Improved Health Funnel, 1243 Improved Succubus, 1282 Soul Link -
-- 19028 itself stays a baseline spell, only the talent-granted row is orphaned, 1281 Mana Feed,
-- 1244 Master Demonologist) and every trimmed rank in DEMONOLOGY §6 (Unholy Power r4/r5, Demonic
-- Tactics r4/r5, Demonic Pact r4/r5, Improved Demonic Tactics replaced by new ids)
DELETE FROM `character_talent` WHERE `spell` IN (
    18703, 18704,
    18754, 18755, 18756,
    19028,
    30326,
    23785, 23822, 23823, 23824, 23825,
    18772, 18773,
    30247, 30248,
    47239, 47240,
    54347, 54348, 54349);
