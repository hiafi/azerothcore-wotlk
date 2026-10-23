-- DB update 2026_10_23_37 -> 2026_10_23_38
-- Stormwind guard directions to the Death Knight trainer (33251, guid 5300679) in the Old Town barracks.
--
-- Stock 3.3.5 guards have no Death Knight entry in their "Class Trainer" submenus (DKs only trained in Ebon Hold), so
-- this adds one with its own POI, directions menu and text. No broadcast text exists for "Death Knight", so the
-- option text is unlocalized.
DELETE FROM `points_of_interest` WHERE `ID` = 1010;
INSERT INTO `points_of_interest` (`ID`, `PositionX`, `PositionY`, `Icon`, `Flags`, `Importance`, `Name`) VALUES
(1010, -8704.72, 304.28, 7, 99, 0, 'Death Knight Trainer');

DELETE FROM `npc_text` WHERE `ID` = 900021;
INSERT INTO `npc_text` (`ID`, `text0_0`, `text0_1`, `Probability0`) VALUES
(900021, 'A knight of the Ebon Blade trains death knights here in the city. You will find the trainer in the barracks in Old Town.', 'A knight of the Ebon Blade trains death knights here in the city. You will find the trainer in the barracks in Old Town.', 1);

DELETE FROM `gossip_menu` WHERE `MenuID` = 5300005;
INSERT INTO `gossip_menu` (`MenuID`, `TextID`) VALUES
(5300005, 900021);

-- Stormwind City Guard / City Patroller / Harbor Guard (Class Trainer submenu 401) and Stormwind Guard (submenu 3519).
DELETE FROM `gossip_menu_option` WHERE `MenuID` IN (401, 3519) AND `OptionID` = 9;
INSERT INTO `gossip_menu_option` (`MenuID`, `OptionID`, `OptionIcon`, `OptionText`, `OptionBroadcastTextID`, `OptionType`, `OptionNpcFlag`, `ActionMenuID`, `ActionPoiID`, `BoxCoded`, `BoxMoney`, `BoxText`, `BoxBroadcastTextID`, `VerifiedBuild`) VALUES
(401, 9, 0, 'Death Knight', 0, 1, 1, 5300005, 1010, 0, 0, '', 0, 0),
(3519, 9, 0, 'Death Knight', 0, 1, 1, 5300005, 1010, 0, 0, '', 0, 0);
