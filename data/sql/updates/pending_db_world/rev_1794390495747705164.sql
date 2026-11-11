-- Restore the city guard directions mod-progression phase 0 deleted (frozen in apps/dbc-tools/replay/frozen/
-- 2026_09_02_mod_progression_phase_00/phase_00-gossip_menu_option.sql). progression-slim WP-D2 un-hid the NPCs and
-- objects these options point at (Inscription trainers, barbers, Draenei Shaman and Blood Elf Paladin trainers in the
-- other race's capitals, the Thunder Bluff zeppelin master, the Lexicon of Power) but left the options deleted, so
-- guards never sent anyone to them. Rows are the stock ones from data/sql/base/db_world/gossip_menu_option.sql.
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 401 AND `OptionID` = 6;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 421 AND `OptionID` = 8;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 435 AND `OptionID` = 12;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 721 AND `OptionID` = 12;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 751 AND `OptionID` = 7;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 1942 AND `OptionID` = 8;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 1949 AND `OptionID` = 7;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 1951 AND `OptionID` = 11;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 1951 AND `OptionID` = 14;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 2121 AND `OptionID` = 10;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 2144 AND `OptionID` = 7;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 2168 AND `OptionID` = 8;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 2351 AND `OptionID` = 6;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 2352 AND `OptionID` = 11;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 2847 AND `OptionID` = 8;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 2848 AND `OptionID` = 1;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 2849 AND `OptionID` = 2;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 7667 AND `OptionID` = 8;
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 7788 AND `OptionID` = 7;
INSERT INTO `gossip_menu_option` (`MenuID`, `OptionID`, `OptionIcon`, `OptionText`, `OptionBroadcastTextID`,
    `OptionType`, `OptionNpcFlag`, `ActionMenuID`, `ActionPoiID`, `BoxCoded`, `BoxMoney`, `BoxText`,
    `BoxBroadcastTextID`, `VerifiedBuild`) VALUES
(401, 6, 0, 'Shaman', 45410, 1, 1, 8164, 37, 0, 0, '', 0, 0),                 -- Stormwind guard: class trainer
(421, 8, 0, 'Inscription', 48811, 1, 1, 10010, 13, 0, 0, '', 0, 0),           -- Stormwind guard: profession trainer
(435, 12, 0, 'Barber', 45376, 1, 1, 10011, 30, 0, 0, '', 0, 0),               -- Stormwind guard
(721, 12, 0, 'The zeppelin master', 0, 1, 1, 10596, 284, 0, 0, '', 0, 0),     -- Bluffwatcher
(751, 7, 0, 'Inscription', 48811, 1, 1, 10021, 296, 0, 0, '', 0, 0),          -- Bluffwatcher: profession trainer
(1942, 8, 0, 'Inscription', 48811, 1, 1, 10017, 189, 0, 0, '', 0, 0),         -- Orgrimmar Grunt: profession trainer
(1949, 7, 0, 'Paladin', 48028, 1, 1, 8644, 303, 0, 0, '', 0, 0),              -- Orgrimmar Grunt: class trainer
(1951, 11, 0, 'Barber', 45376, 1, 1, 10018, 188, 0, 0, '', 0, 0),             -- Orgrimmar Grunt
(1951, 14, 0, 'Lexicon of Power', 32998, 1, 1, 10205, 189, 0, 0, '', 0, 0),   -- Orgrimmar Grunt
(2121, 10, 0, 'Barber', 45376, 1, 1, 10014, 60, 0, 0, '', 0, 0),              -- Ironforge Guard
(2144, 7, 0, 'Shaman', 45410, 1, 1, 8643, 65, 0, 0, '', 0, 0),                -- Ironforge Guard: class trainer
(2168, 8, 0, 'Inscription', 48811, 1, 1, 10013, 72, 0, 0, '', 0, 0),          -- Ironforge Guard: profession trainer
(2351, 6, 0, 'Inscription', 48811, 1, 1, 10015, 107, 0, 0, '', 0, 0),         -- Darnassus Sentinel: profession trainer
(2352, 11, 0, 'Lexicon of Power', 32998, 1, 1, 10205, 107, 0, 0, '', 0, 0),   -- Darnassus Sentinel
(2847, 8, 0, 'Inscription', 48811, 1, 1, 10019, 344, 0, 0, NULL, 0, NULL),    -- Undercity Guardian: profession trainer
(2848, 1, 0, 'Paladin', 48028, 1, 1, 8165, 330, 0, 0, NULL, 0, NULL),         -- Undercity Guardian: class trainer
(2849, 2, 0, 'Barber', 45376, 1, 1, 10020, 320, 0, 0, '', 0, 0),              -- Undercity Guardian
(7667, 8, 0, 'Inscription', 48811, 1, 1, 10022, 376, 0, 0, '', 0, 0),         -- Silvermoon guard: profession trainer
(7788, 7, 0, 'Inscription', 48811, 1, 1, 10016, 212, 0, 0, '', 0, 0);         -- Exodar guard: profession trainer
