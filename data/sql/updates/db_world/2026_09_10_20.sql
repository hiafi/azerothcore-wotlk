-- DB update 2026_09_05_38 -> 2026_09_10_20
--
-- Death Knights start at level 1 on this server (StartHeroicPlayerLevel = 1), but
-- `player_class_stats` only ever had DK (Class 6) rows from stock's level 55 onward, since
-- stock WotLK never lets a DK exist below 55. ObjectMgr::LoadPlayerInfo() treats a class missing
-- stats at its configured start level as fatal and exits the worldserver at boot.
--
-- Values are Warrior's (Class 1) levels 1-54 verbatim, not invented: DK's actual level 55 stats
-- (Str 108, Agi 73, Sta 99, Int 29, Spirit 42, BaseHP 1359, BaseMana 0) are within 1-2 points of
-- Warrior's level 55 row on every stat and match exactly by level 57 onward, so Warrior is
-- already the closest analog in this table (both Strength-primary, Stamina-secondary, 0 base
-- mana, plate melee) and reusing its curve verbatim gives a smooth, discontinuity-free ramp into
-- DK's real level 55 row rather than an invented one.
--
DELETE FROM `player_class_stats` WHERE `Class` = 6 AND `Level` BETWEEN 1 AND 54;
INSERT INTO `player_class_stats` (`Class`, `Level`, `BaseHP`, `BaseMana`, `Strength`, `Agility`, `Stamina`, `Intellect`, `Spirit`) VALUES
(6, 1, 20, 0, 23, 20, 22, 20, 20),
(6, 2, 29, 0, 24, 21, 23, 20, 20),
(6, 3, 38, 0, 25, 21, 24, 20, 21),
(6, 4, 47, 0, 26, 22, 25, 20, 21),
(6, 5, 56, 0, 28, 23, 26, 20, 21),
(6, 6, 65, 0, 29, 24, 27, 21, 21),
(6, 7, 74, 0, 30, 24, 28, 21, 22),
(6, 8, 83, 0, 31, 25, 29, 21, 22),
(6, 9, 92, 0, 32, 26, 30, 21, 22),
(6, 10, 97, 0, 33, 26, 31, 21, 23),
(6, 11, 103, 0, 35, 27, 33, 21, 23),
(6, 12, 109, 0, 36, 28, 34, 21, 23),
(6, 13, 118, 0, 37, 29, 35, 21, 24),
(6, 14, 128, 0, 39, 30, 36, 22, 24),
(6, 15, 139, 0, 40, 30, 37, 22, 24),
(6, 16, 151, 0, 41, 31, 38, 22, 25),
(6, 17, 154, 0, 42, 32, 40, 22, 25),
(6, 18, 168, 0, 44, 33, 41, 22, 25),
(6, 19, 183, 0, 45, 34, 42, 22, 26),
(6, 20, 199, 0, 47, 35, 43, 22, 26),
(6, 21, 206, 0, 48, 35, 45, 23, 26),
(6, 22, 224, 0, 49, 36, 46, 23, 27),
(6, 23, 243, 0, 51, 37, 47, 23, 27),
(6, 24, 253, 0, 52, 38, 49, 23, 28),
(6, 25, 274, 0, 54, 39, 50, 23, 28),
(6, 26, 296, 0, 55, 40, 51, 23, 28),
(6, 27, 309, 0, 57, 41, 53, 23, 29),
(6, 28, 333, 0, 58, 42, 54, 24, 29),
(6, 29, 348, 0, 60, 43, 56, 24, 30),
(6, 30, 374, 0, 62, 44, 57, 24, 30),
(6, 31, 401, 0, 63, 45, 58, 24, 30),
(6, 32, 419, 0, 65, 46, 60, 24, 31),
(6, 33, 448, 0, 66, 47, 61, 24, 31),
(6, 34, 468, 0, 68, 48, 63, 25, 32),
(6, 35, 499, 0, 70, 49, 64, 25, 32),
(6, 36, 521, 0, 72, 50, 66, 25, 33),
(6, 37, 545, 0, 73, 51, 68, 25, 33),
(6, 38, 581, 0, 75, 52, 69, 25, 33),
(6, 39, 609, 0, 77, 53, 71, 26, 34),
(6, 40, 649, 0, 79, 54, 72, 26, 34),
(6, 41, 681, 0, 80, 56, 74, 26, 35),
(6, 42, 715, 0, 82, 57, 76, 26, 35),
(6, 43, 761, 0, 84, 58, 77, 26, 36),
(6, 44, 799, 0, 86, 59, 79, 26, 36),
(6, 45, 839, 0, 88, 60, 81, 27, 37),
(6, 46, 881, 0, 90, 61, 83, 27, 37),
(6, 47, 935, 0, 92, 63, 84, 27, 38),
(6, 48, 981, 0, 94, 64, 86, 27, 38),
(6, 49, 1029, 0, 96, 65, 88, 28, 39),
(6, 50, 1079, 0, 98, 66, 90, 28, 39),
(6, 51, 1131, 0, 100, 68, 92, 28, 40),
(6, 52, 1185, 0, 102, 69, 94, 28, 40),
(6, 53, 1241, 0, 104, 70, 96, 28, 41),
(6, 54, 1299, 0, 106, 72, 98, 29, 42);
