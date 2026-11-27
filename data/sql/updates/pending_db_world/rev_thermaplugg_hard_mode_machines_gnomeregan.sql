-- Gnomeregan build WP-D6Hb: the Whole Workshop, part b (Mekgineer Thermaplugg's heroic hard mode: the Electrocutioner,
-- Alert System and Pummeler schematics), the rows dbc-tools cannot declare
-- (.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.5 row D6Hb, s3.7; build spec
-- docs/dungeons/gnomeregan-rework.md "Hard mode: the Whole Workshop", MT22, MT24 and its text table). The spells
-- 214580-214586 and the Pummeler's Fist 301136 are apps/dbc-tools
-- source/npcs/gnomeregan/thermaplugg_hard_mode_machines.py; the script is thermaplugg_hard_mode_machines.cpp (the
-- package SchematicsB of Thermaplugg's fight).

-- His hard mode texts, lines 10 and 11 (ThermapluggHardModeMachinesLogic.h SchematicsTexts; D6's groups 0-8 stay, 9 is
-- D6Ha's yell). Emotes, type 41 (rule 2), the whole map (TextRange 3, as D6's). The machines say them: the Voltage
-- machine at each Electric Justice bar, the combination machine at each fist combination's call.
DELETE FROM `creature_text` WHERE `CreatureID` = 7800 AND `GroupID` IN (10, 11);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(7800, 10, 0, '%s overloads the room. Get to him!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Thermaplugg - Electric Justice, the Whole Workshop (MT22)'),
(7800, 11, 0, 'A giant fist winds up inside a Gnome Face!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Thermaplugg - Fist Combination, the Whole Workshop (MT24)');
