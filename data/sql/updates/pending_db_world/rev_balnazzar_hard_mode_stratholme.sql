-- Stratholme build WP-S8: Balnazzar's hard mode, the Grand Lie (heroic only), the rows dbc-tools cannot declare
-- (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.7, s3.5 row S8, s7 #7, #9, #10; build spec
-- docs/dungeons/stratholme-rework.md ST 1920-1999, 2107-2120; modules/mod-dungeon-bosses
-- src/Stratholme/balnazzar_hard_mode.cpp). The boss's spells 206575-206584 and the swarm stalker 300609 are
-- apps/dbc-tools source/npcs/stratholme/balnazzar_hard_mode.py; the relics' use spells 206585-206588 are
-- source/items/stratholme_relics.py; the relics' client Item.dbc and server item_dbc rows are source/items.csv
-- (70600-70603). This rev: the texts, the four items' item_template rows, the four gameobjects and their spawns.

-- Texts (ST "Text", handoff s7 #14: the rows go on the entry that speaks). Dathrohan 10812: groups 8 (say, the Letter
-- read to him) and 9 (yell, the hard mode's start). Balnazzar 10813: groups 10-16, the twins' calls (true lines say
-- "the Light", lies never do: ruling 28) and Dread Slumber. S7's groups (10812: 0-4; 10813: 5-7) are untouched. $n is
-- the marked player.
DELETE FROM `creature_text` WHERE `CreatureID` = 10812 AND `GroupID` IN (8, 9);
DELETE FROM `creature_text` WHERE `CreatureID` = 10813 AND `GroupID` BETWEEN 10 AND 16;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10812, 8, 0, 'What is this? A letter?', 12, 0, 100, 0, 0, 0, 0, 0,
    'Grand Crusader Dathrohan - The Letter of Proof read to him (the Grand Lie)'),
(10812, 9, 0, 'Saidan begged the Light for help. None came. Enough of this mask!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Grand Crusader Dathrohan - The Grand Lie begins'),
(10813, 10, 0, 'The Light cleaves the unworthy!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Balnazzar - The Cleave, true (HM1)'),
(10813, 11, 0, 'My blade cleaves the unworthy!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Balnazzar - The Cleave, lie (HM1)'),
(10813, 12, 0, 'The Light burns all who stand near!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Balnazzar - The Ring, true (HM2)'),
(10813, 13, 0, 'None who stand near me will live!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Balnazzar - The Ring, lie (HM2)'),
(10813, 14, 0, '$n, share the Light''s burden!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Balnazzar - The Mark, true (HM3)'),
(10813, 15, 0, '$n, share my burden!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Balnazzar - The Mark, lie (HM3)'),
(10813, 16, 0, 'Sleep, and dream of your failure.', 14, 0, 100, 0, 0, 0, 0, 0,
    'Balnazzar - Dread Slumber (HM8)');

-- The Letter of Proof and the three relics (hand-picked `item` block ids 70600-70603, StratholmeRework.h
-- StratholmeItems). Miscellaneous (class 15 / 4), Bind on Pickup, unique (maxcount 1), Map 329: usable in Stratholme
-- only, and gone when the bearer leaves it (a click on the spot gives a new one). The use spell never consumes the item
-- (spellcharges 0); its cooldown is per copy (ruling 33): Standard 20 s, Holy Water 3 min, Medallion 25 s, the Letter
-- none. The class, subclass, display, material and sheath match the source/items.csv Item.dbc rows (the server's
-- DBC.EnforceItemAttributes resets item_template to them). Upserts: item_template rows are never deleted
-- (codestyle-sql not_delete).
INSERT INTO `item_template` (`entry`, `class`, `subclass`, `SoundOverrideSubclass`, `name`, `displayid`, `Quality`,
    `Flags`, `BuyCount`, `BuyPrice`, `SellPrice`, `InventoryType`, `AllowableClass`, `AllowableRace`, `ItemLevel`,
    `RequiredLevel`, `maxcount`, `stackable`, `spellid_1`, `spelltrigger_1`, `spellcharges_1`, `spellppmRate_1`,
    `spellcooldown_1`, `spellcategory_1`, `spellcategorycooldown_1`, `bonding`, `description`, `Material`, `sheath`,
    `Map`, `VerifiedBuild`) VALUES
(70600, 15, 4, -1, 'Letter of Proof', 3093, 1, 0, 1, 0, 0, 0, -1, -1, 60, 0, 1, 1, 206585, 0, 0, 0, -1, 0, -1, 1,
    'Saidan Dathrohan''s last letter, written as the dreadlord took him.', -1, 0, 329, 0),
(70601, 15, 4, -1, 'Scarlet Standard', 31257, 1, 0, 1, 0, 0, 0, -1, -1, 60, 0, 1, 1, 206587, 0, 0, 0, 20000, 0, -1,
    1, 'The banner of Willey''s guns. The dreadlord''s swarms will not cross its light.', -1, 0, 329, 0),
(70602, 15, 4, -1, 'Blessed Holy Water', 23731, 1, 0, 1, 0, 0, 0, -1, -1, 60, 0, 1, 1, 206586, 0, 0, 0, 180000, 0,
    -1, 1, 'Blessed by the Crusade''s last true priest. It scatters what feeds on the dead.', -1, 0, 329, 0),
(70603, 15, 4, -1, 'Relic of the Medallion', 9857, 1, 0, 1, 0, 0, 0, -1, -1, 60, 0, 1, 1, 206588, 0, 0, 0, 25000, 0,
    -1, 1, 'A light from Malor''s strongbox, kept by the Medallion of Faith. No nightmare holds those it touches.', -1,
    0, 329, 0) ON DUPLICATE KEY UPDATE `class` = VALUES(`class`), `subclass` = VALUES(`subclass`),
    `SoundOverrideSubclass` = VALUES(`SoundOverrideSubclass`), `name` = VALUES(`name`),
    `displayid` = VALUES(`displayid`), `Quality` = VALUES(`Quality`), `Flags` = VALUES(`Flags`),
    `InventoryType` = VALUES(`InventoryType`),
    `ItemLevel` = VALUES(`ItemLevel`), `RequiredLevel` = VALUES(`RequiredLevel`), `maxcount` = VALUES(`maxcount`),
    `stackable` = VALUES(`stackable`), `spellid_1` = VALUES(`spellid_1`), `spelltrigger_1` = VALUES(`spelltrigger_1`),
    `spellcharges_1` = VALUES(`spellcharges_1`), `spellcooldown_1` = VALUES(`spellcooldown_1`),
    `spellcategory_1` = VALUES(`spellcategory_1`), `spellcategorycooldown_1` = VALUES(`spellcategorycooldown_1`),
    `bonding` = VALUES(`bonding`), `description` = VALUES(`description`), `Material` = VALUES(`Material`),
    `sheath` = VALUES(`sheath`), `Map` = VALUES(`Map`);

-- The four gameobjects (ids.yaml reservation `stratholme` 301203-301206; StratholmeRework.h StratholmeGameObjects):
-- goobers (type 10, no lock, no spell, no loot, no despawn) whose script owns the click (go_st_grand_lie_relic, KT-2's
-- RelicDispenserAI: one copy of the spot's item to everyone in the group on the map, bots too). The script hides them
-- (CanBeSeen, not selectable) until their boss is dead on heroic with wave 2 bound (GrandLieLogic.h RelicShown).
-- 301203 Letter of Proof: the Singed Letter's scroll (GODI 220, stock 175704), in the ashes of the Scarlet Archive;
--        after Galford's death; gives the Letter (70600).
-- 301204 Scarlet Standard: a crimson banner (GODI 6389, CrimsonBanner01), on Willey's spot in his yard; after Willey's
--        death; gives the Standard (70601).
-- 301205 Medallion's Light: the holy light well (GODI 6671, G_HolyLightWell, a goober model) beside Malor's Strongbox
--        176112; after Malor's death; gives the Relic of the Medallion (70603).
-- 301206 Blessed Supply Crate: the stock Supply Crate's look (GODI 335, stock 176224) beside the Holy Water crate in
--        Crusaders' Square; from the instance's start; gives Blessed Holy Water (70602).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301203, 10, 220, 'Letter of Proof', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, '', 'go_st_grand_lie_relic', 0),
(301204, 10, 6389, 'Scarlet Standard', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, '', 'go_st_grand_lie_relic', 0),
(301205, 10, 6671, 'Medallion''s Light', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, '', 'go_st_grand_lie_relic', 0),
(301206, 10, 335, 'Blessed Supply Crate', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, '', 'go_st_grand_lie_relic', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`),
    `displayId` = VALUES(`displayId`), `name` = VALUES(`name`), `size` = VALUES(`size`), `Data0` = VALUES(`Data0`),
    `AIName` = VALUES(`AIName`), `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` IN (301203, 301204, 301205, 301206);
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301203, 0, 0, 0, 0, 0, 0, 0, 0),
(301204, 0, 0, 0, 0, 0, 0, 0, 0),
(301205, 0, 0, 0, 0, 0, 0, 0, 0),
(301206, 0, 0, 0, 0, 0, 0, 0, 0);

-- The spawns, heroic only (spawnMask 2), at GrandLieLogic.h's spots (kLetterSpot, kStandardSpot, kMedallionLightSpot,
-- kBlessedCrateSpot; picked from the database rows, checked in game by the playtest). Guids 3012030-3012060 (the entry
-- x 10 convention of the kit spawns; free in the live DB, read-only check 2026-11-09). Rotation = the orientation about
-- z (rotation2 = sin(o/2), rotation3 = cos(o/2)).
DELETE FROM `gameobject` WHERE `id` = 301203 AND `guid` = 3012030;
DELETE FROM `gameobject` WHERE `id` = 301204 AND `guid` = 3012040;
DELETE FROM `gameobject` WHERE `id` = 301205 AND `guid` = 3012050;
DELETE FROM `gameobject` WHERE `id` = 301206 AND `guid` = 3012060;
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`,
    `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`,
    `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3012030, 301203, 329, 0, 0, 2, 1, 3456.3, -3104.9, 136.6, 4.86, 0, 0, 0.653041, -0.757323, 7200, 255, 1, '', 0,
    'Stratholme S8: Letter of Proof (the Grand Lie, heroic only, after Galford)'),
(3012040, 301204, 329, 0, 0, 2, 1, 3573.57, -2937.31, 125.09, 3.79, 0, 0, 0.947905, -0.318554, 7200, 255, 1, '', 0,
    'Stratholme S8: Scarlet Standard (the Grand Lie, heroic only, after Willey)'),
(3012050, 301205, 329, 0, 0, 2, 1, 3618.56, -3129.46, 135.7, 0.81, 0, 0, 0.394019, 0.919102, 7200, 255, 1, '', 0,
    'Stratholme S8: Medallion''s Light (the Grand Lie, heroic only, after Malor)'),
(3012060, 301206, 329, 0, 0, 2, 1, 3664.63, -3182.46, 126.25, 3.14, 0, 0, 1, 0.000796, 7200, 255, 1, '', 0,
    'Stratholme S8: Blessed Supply Crate (the Grand Lie, heroic only)');
