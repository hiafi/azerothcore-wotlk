-- Death Knight rework DK0a: Death Knight class trainers (33251, trainer 13) in the eight racial start areas and three
-- capitals (Ironforge, Darnassus, Undercity), plus guard directions to them. Exodar, Thunder Bluff and Silvermoon get
-- none, for role-play reasons (user ruling 2026-10-23).
--
-- Spawns: guids 5300709-5300718 and 5300720 (DK0 ID sub-block). Start areas: each 4-4.5 yd from the stock class
-- trainer, same floor, orientation, map and phaseMask. Capitals: spots the user picked in game (.gps, 2026-10-23).
-- Stormwind (5300679) and Orgrimmar (5300680) already have one (2026_09_06_03). The Orgrimmar guards get directions
-- to the existing one.
--
-- Guard directions follow 2026_10_23_38: stock 3.3.5 guards have no Death Knight entry in their "Class Trainer"
-- submenus, so each gets one option (OptionID 9, clear of the ids mod-progression adds there) with its own POI,
-- directions menu and text. No broadcast text exists for "Death Knight", so the option text is unlocalized.
-- Literal values only (trainer_state skips files with @ variables).
DELETE FROM `creature` WHERE `id` = 33251 AND `guid` IN (5300709, 5300710, 5300711, 5300712, 5300713, 5300714, 5300715, 5300716, 5300717, 5300718, 5300719, 5300720, 5300721, 5300722);
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`, `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`, `CreateObject`, `Comment`) VALUES
(5300709, 33251, 0, 0, 0, 1, 1, 0, -8922.18, -210.8, 82.31, 6.06, 300, 0, 12340, 1, 'Death Knight Trainer - Human, Northshire (start area)'),
(5300710, 33251, 1, 0, 0, 1, 1, 0, -643.73, -4231.2, 38.56, 5.72, 300, 0, 12340, 1, 'Death Knight Trainer - Orc/Troll, Valley of Trials (start area)'),
(5300711, 33251, 0, 0, 0, 1, 1, 0, -6083.53, 378.34, 395.63, 3.46, 300, 0, 12340, 1, 'Death Knight Trainer - Dwarf/Gnome, Coldridge Valley (start area)'),
(5300712, 33251, 1, 0, 0, 1, 1, 0, 10531.07, 778.63, 1329.68, 2.48, 300, 0, 12340, 1, 'Death Knight Trainer - Night Elf, Shadowglen (start area)'),
(5300713, 33251, 0, 0, 0, 1, 1, 0, 1858.0, 1555.7, 94.88, 2.5, 300, 0, 12340, 1, 'Death Knight Trainer - Undead, Deathknell (start area)'),
(5300714, 33251, 1, 0, 0, 1, 1, 0, -2883.38, -209.62, 54.9, 4.64, 300, 0, 12340, 1, 'Death Knight Trainer - Tauren, Camp Narache (start area)'),
(5300715, 33251, 530, 0, 0, 1, 1, 0, 10369.38, -6434.5, 38.62, 0.73, 300, 0, 12340, 1, 'Death Knight Trainer - Blood Elf, Sunstrider Isle (start area)'),
(5300716, 33251, 530, 0, 0, 1, 1, 0, -4140.52, -13740.27, 74.64, 5.6, 300, 0, 12340, 1, 'Death Knight Trainer - Draenei, Ammen Vale (start area)'),
(5300717, 33251, 0, 0, 0, 1, 1, 0, -5051.818, -1170.501, 503.681, 0.507, 300, 0, 12340, 1, 'Death Knight Trainer - Ironforge (capital)'),
(5300718, 33251, 1, 0, 0, 1, 1, 0, 9888.831, 2321.559, 1327.953, 3.63, 300, 0, 12340, 1, 'Death Knight Trainer - Darnassus (capital)'),
(5300720, 33251, 0, 0, 0, 1, 1, 0, 1769.996, 412.711, -57.198, 0.789, 300, 0, 12340, 1, 'Death Knight Trainer - Undercity (capital)');

DELETE FROM `points_of_interest` WHERE `ID` BETWEEN 1011 AND 1017;
INSERT INTO `points_of_interest` (`ID`, `PositionX`, `PositionY`, `Icon`, `Flags`, `Importance`, `Name`) VALUES
(1011, 1846.54, -4325.67, 7, 99, 0, 'Death Knight Trainer'),
(1012, -5051.818, -1170.501, 7, 99, 0, 'Death Knight Trainer'),
(1013, 9888.831, 2321.559, 7, 99, 0, 'Death Knight Trainer'),
(1015, 1769.996, 412.711, 7, 99, 0, 'Death Knight Trainer');

DELETE FROM `npc_text` WHERE `ID` BETWEEN 900022 AND 900028;
INSERT INTO `npc_text` (`ID`, `text0_0`, `text0_1`, `Probability0`) VALUES
(900022, 'A knight of the Ebon Blade trains death knights here in the city. You will find the trainer beneath the city in the Cleft of Shadow, near the entrance to Ragefire Chasm.', 'A knight of the Ebon Blade trains death knights here in the city. You will find the trainer beneath the city in the Cleft of Shadow, near the entrance to Ragefire Chasm.', 1),
(900023, 'A knight of the Ebon Blade trains death knights in Ironforge. I have marked the spot on your map.', 'A knight of the Ebon Blade trains death knights in Ironforge. I have marked the spot on your map.', 1),
(900024, 'A knight of the Ebon Blade trains death knights in Darnassus. I have marked the spot on your map.', 'A knight of the Ebon Blade trains death knights in Darnassus. I have marked the spot on your map.', 1),
(900026, 'A knight of the Ebon Blade trains death knights here in the city. You will find the trainer near the warrior trainers.', 'A knight of the Ebon Blade trains death knights here in the city. You will find the trainer near the warrior trainers.', 1);

DELETE FROM `gossip_menu` WHERE `MenuID` BETWEEN 5300006 AND 5300012;
INSERT INTO `gossip_menu` (`MenuID`, `TextID`) VALUES
(5300006, 900022),
(5300007, 900023),
(5300008, 900024),
(5300010, 900026);

-- Guard "Class Trainer" submenus: Orgrimmar Grunt 1949, Ironforge Guard 2144 and Mountaineer 3545, Darnassus
-- Sentinel 2343, Undercity Guardian 2848.
DELETE FROM `gossip_menu_option` WHERE `MenuID` IN (1949, 2144, 3545, 2343, 2848) AND `OptionID` = 9;
INSERT INTO `gossip_menu_option` (`MenuID`, `OptionID`, `OptionIcon`, `OptionText`, `OptionBroadcastTextID`, `OptionType`, `OptionNpcFlag`, `ActionMenuID`, `ActionPoiID`, `BoxCoded`, `BoxMoney`, `BoxText`, `BoxBroadcastTextID`, `VerifiedBuild`) VALUES
(1949, 9, 0, 'Death Knight', 0, 1, 1, 5300006, 1011, 0, 0, '', 0, 0),
(2144, 9, 0, 'Death Knight', 0, 1, 1, 5300007, 1012, 0, 0, '', 0, 0),
(3545, 9, 0, 'Death Knight', 0, 1, 1, 5300007, 1012, 0, 0, '', 0, 0),
(2343, 9, 0, 'Death Knight', 0, 1, 1, 5300008, 1013, 0, 0, '', 0, 0),
(2848, 9, 0, 'Death Knight', 0, 1, 1, 5300010, 1015, 0, 0, '', 0, 0);
