-- warlock-rework Affliction pass: talent reset (PLAN B5) and Soul Shard item cleanup (PLAN B9)
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 9;
-- orphaned talent ranks (SHARED §4b: Player::_LoadTalents asserts before the reset runs)
DELETE FROM `character_talent` WHERE `spell` IN (17813, 17814, 32393, 32394, 18274, 18275, 30063, 30064, 47204, 47205, 18174, 18175, 18176, 53754, 53759, 18288, 18223, 18220, 30054, 30057, 18708);
DELETE FROM `character_inventory` WHERE `item` IN (SELECT `guid` FROM `item_instance` WHERE `itemEntry` = 6265);
DELETE FROM `mail_items` WHERE `item_guid` IN (SELECT `guid` FROM `item_instance` WHERE `itemEntry` = 6265);
DELETE FROM `item_instance` WHERE `itemEntry` = 6265;
