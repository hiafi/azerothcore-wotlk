-- Scarlet Monastery build WP-D14: High Inquisitor Whitemane, with Mograine risen (3977, 3976), the rows dbc-tools
-- cannot declare (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D14; build spec
-- docs/dungeons/scarlet-monastery-4-cathedral.md "High Inquisitor Whitemane, with Mograine risen", "Text"). Her
-- template (boss_whitemane_rework behind BIND_WAVE_2, 50k, immunity 1972, INSTANCE_BIND) and spells 213150-213170 are
-- apps/dbc-tools source/npcs/scarlet_monastery/whitemane.py; her SmartAI rows 0-19 and the lists 397700-397701 go with
-- W2-SETUP's rev. This rev inserts no spawn and no SmartAI row (rule 14): her stock spawn (guid 39946) stays in her
-- chamber and the script walks her out to the vigil.

-- Her texts: groups 0-2 are stock (0 the stock intro, split into 3 + 2 and no longer said; 1 the kill; 2 "Arise, my
-- champion!", the rising); 3-5 and 7 are new (D14); 6 is D14H's ("Lies! He is the Crusade's champion!").
DELETE FROM `creature_text` WHERE `CreatureID` = 3977 AND `GroupID` IN (3, 4, 5, 7);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(3977, 3, 0, 'Mograine has fallen! You shall pay for this treachery!', 14, 0, 100, 0, 0, 0, 0, 0,
    'High Inquisitor Whitemane - She walks out to her vigil over Mograine (WM0)'),
(3977, 4, 0, 'Not yet, my love. The Light is not done with you.', 14, 0, 100, 0, 0, 0, 0, 0,
    'High Inquisitor Whitemane - Her save: she channels Scarlet Resurrection over him (WM1a)'),
(3977, 5, 0, 'Together... always...', 12, 0, 100, 0, 0, 0, 0, 0,
    'High Inquisitor Whitemane - The pair dies together'),
(3977, 7, 0, 'The Vigil Flame passes to $n!', 41, 0, 100, 0, 0, 0, 0, 3,
    'High Inquisitor Whitemane - The Vigil Flame passes (WM5, heroic)');

-- His finale lines: group 2 is stock ("At your side, milady!", the rising); 12-13 are new (D13 owns 7-11).
DELETE FROM `creature_text` WHERE `CreatureID` = 3976 AND `GroupID` IN (12, 13);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(3976, 12, 0, 'Not while I stand, milady!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Scarlet Commander Mograine - His save: he lays hands on Whitemane (WM1b)'),
(3976, 13, 0, 'Milady!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Scarlet Commander Mograine - To Her Side: he breaks from the tank and charges to her (WM2)');
