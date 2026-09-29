-- DB update 2026_09_27_04 -> 2026_09_29_00
-- warlock-rework (Affliction/Destruction/Demonology passes, squashed)
-- talent reset for every Warlock (PLAN B5)
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 9;

-- orphaned talent ranks (SHARED §4b: Player::_LoadTalents asserts before the reset runs)
-- Affliction: repurposed/trimmed ranks
DELETE FROM `character_talent` WHERE `spell` IN (17813, 17814, 32393, 32394, 18274, 18275, 30063, 30064, 47204, 47205, 18174, 18175, 18176, 53754, 53759, 18288, 18223, 18220, 30054, 30057, 18708);
-- Destruction: the repurposed rows' old ranks (965 Improved Searing Pain, 1889 Improved Soul Leech) and every
-- trimmed rank in DESTRUCTION §6
DELETE FROM `character_talent` WHERE `spell` IN (17927, 17929, 17930, 54117, 54118, 17802, 17803, 17791, 17792, 17957, 17958, 59740, 59741, 30291, 30292, 47269, 47270);
-- Demonology: the repurposed rows' old ranks (1224 Improved Health Funnel, 1243 Improved Succubus, 1282 Soul Link -
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

-- Curse of Doom removed, replaced by Bane of Doom (DEMONOLOGY §4.6)
DELETE FROM `character_spell` WHERE `spell` = 603;
DELETE FROM `character_action` WHERE `type` = 0 AND `action` = 603;

-- Soul Shard item cleanup (PLAN B9)
DELETE FROM `character_inventory` WHERE `item` IN (SELECT `guid` FROM `item_instance` WHERE `itemEntry` = 6265);
DELETE FROM `mail_items` WHERE `item_guid` IN (SELECT `guid` FROM `item_instance` WHERE `itemEntry` = 6265);
DELETE FROM `item_instance` WHERE `itemEntry` = 6265;
