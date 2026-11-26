-- Gnomeregan build WP-D6: Mekgineer Thermaplugg (7800), the rows dbc-tools cannot declare
-- (.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.5 row D6, rule 35; build spec
-- docs/dungeons/gnomeregan-rework.md "Mekgineer Thermaplugg", Build spec "Text"). His template columns, spells
-- 214490-214511 and the boss kit 301120-301127 are apps/dbc-tools source/npcs/gnomeregan/thermaplugg.py; the stock
-- smart_scripts rows of 7800 and the twelve faces and buttons were dropped by WP-S0's rev_skeleton_gnomeregan.sql. This
-- rev inserts no spawn and no SmartAI row.

-- The stock groups stay (rule 35) and are cut to SP's table: group 1 keeps only "My machines are the future!" (5808,
-- now the Override's), group 2 is "Explosions! MORE explosions!" (5809, now the mines'), group 3 "And STAY dead!"
-- (5810, now a player's death). The second row of stock group 1 (5809 again, broadcast 0) goes.
DELETE FROM `creature_text` WHERE `CreatureID` = 7800 AND `GroupID` = 1 AND `ID` = 1;

-- The new lines (groups 4-8). The emotes are boss emotes (41), map-wide (TextRange 3): the room is about 130 by 90 yd.
-- Groups 9-11 are the hard mode packages' (D6Ha, D6Hb).
DELETE FROM `creature_text` WHERE `CreatureID` = 7800 AND `GroupID` BETWEEN 4 AND 8;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(7800, 4, 0, '%s opens a bomb chute!', 41, 0, 100, 0, 0, 0, 0, 3, 'Thermaplugg - a face opens (MT1)'),
(7800, 5, 0, '%s overrides the bomb chutes!', 41, 0, 100, 0, 0, 0, 0, 3, 'Thermaplugg - Override (MT6)'),
(7800, 6, 0, 'A Sticky Bomb latches onto $n!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Thermaplugg - Sticky Bomb (MT12, heroic)'),
(7800, 7, 0, 'The Big One rolls out. Share the blast!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Thermaplugg - The Big One (MT13, heroic)'),
(7800, 8, 0, '%s reaches for his detonator!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Thermaplugg - Remote Detonator (MT14, heroic)');
