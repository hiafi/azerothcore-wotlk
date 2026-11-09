-- Scholomance build WP-S11: Darkmaster Gandling (1853), the rows dbc-tools cannot declare
-- (.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S11; build spec
-- docs/dungeons/scholomance-rework.md SC 3034-3101). His template (boss_darkmaster_gandling_rework, AIName '', health,
-- immunities), the Expelled Student 300544, the Ravenian's echo 300545, the lesson and portal stalkers 300546-300547
-- and the spells 206330-206339 are apps/dbc-tools source/npcs/scholomance/darkmaster_gandling.py.

-- SmartAI 1853: twelve dormant rows (the stock C++ AI always won: Arcane Missiles, Curse of the Darkmaster, Shadow
-- Shield, Shadow Portal, the gate and visibility rows) are removed as a full block. The rework casts its own kit, the
-- instance's door data runs the gates and his Reset applies the reveal; the Risen Guardian 11598 is retired.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 1853 AND `source_type` = 0;

-- Texts (SC "Text", approved 2026-11-01; group 0 "School is in session!" is stock and kept). Yells are type 14, the
-- mechanic emotes boss emotes (41), so each names its mechanic on screen. Groups 4 and 5 are the Graduate Exam's
-- (WP-S13 says them). $n is the detained player (group 1). The Volley and Transfer emotes (groups 2 and 3) reach the
-- whole map (TextRange 3): in the Graduate Exam's gauntlet he stays in the study, 59 to 70 yd from the classroom the
-- group fights in, past the 40 yd text emote range (R-C EXAM SF-2).
DELETE FROM `creature_text` WHERE `CreatureID` = 1853 AND `GroupID` BETWEEN 1 AND 6;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(1853, 1, 0, 'Detention, $n!', 14, 0, 100, 0, 0, 0, 0, 0, 'Darkmaster Gandling - Detention (GD1)'),
(1853, 2, 0, '%s tears open portals around the room!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Darkmaster Gandling - Portal Volley (GD4)'),
(1853, 3, 0, '%s shuffles his students through the portals!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Darkmaster Gandling - Transfer (GD4b)'),
(1853, 4, 0, 'Honor students? Try our graduate program.', 14, 0, 100, 0, 0, 0, 0, 0,
    'Darkmaster Gandling - hard mode start (GD5, WP-S13)'),
(1853, 5, 0, 'Final Exam...', 14, 0, 100, 0, 0, 0, 0, 0, 'Darkmaster Gandling - hard mode final phase (GD6, WP-S13)'),
(1853, 6, 0, 'Class... dismissed...', 14, 0, 100, 0, 0, 0, 0, 0, 'Darkmaster Gandling - death');

-- The Expelled Student's rise (SC GD3 "rise emote"; not in the doc's text table, worded by WP-S11): a boss emote naming
-- the student it fixates. The heroic copy 310119 reads its base entry's texts.
DELETE FROM `creature_text` WHERE `CreatureID` = 300544;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(300544, 0, 0, '%s rises from $n\'s failed detention!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Expelled Student - rises on a failed detention (GD3)');
