-- Shadowfang Keep build WP-S4 (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md s3.6 row S4):
-- Commander Springvale and his three Risen Guardsmen. The creature rows, spells and script bindings are apps/dbc-tools
-- source/npcs/shadowfang_keep/commander_springvale.py; the C++ is modules/mod-dungeon-bosses
-- src/ShadowfangKeep/boss_commander_springvale_rework.cpp.

-- Springvale's stock SmartAI (Hammer of Justice 5588, Holy Light 1026, Divine Shield 33581, the aggro and death
-- yells) is replaced by boss_commander_springvale_rework, which keeps the two yells.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 4278 AND `source_type` = 0;

-- Build spec "Text": Springvale lines 2-5 (0 and 1, the stock yells, are kept); the Guardsman of the Hammer's Hammer
-- emote (group 0, the line 2 text from the guardsman). Boss emotes (41) are center screen; %s = the speaker,
-- $n = the marked player.
DELETE FROM `creature_text` WHERE `CreatureID` = 4278 AND `GroupID` IN (2, 3, 4, 5);
DELETE FROM `creature_text` WHERE `CreatureID` = 300507 AND `GroupID` = 0;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(4278, 2, 0, '%s hurls his hammer at $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Commander Springvale - Hammer of Judgement (SP1)'),
(4278, 3, 0, 'Rise, my brothers! The watch is not ended!', 14, 0, 100, 0, 0, 0, 0, 0, 'Commander Springvale - Unbreakable Oath (SP6)'),
(4278, 4, 0, 'By the Light, I will purge this keep of every intruder!', 14, 0, 100, 0, 0, 0, 0, 0, 'Commander Springvale - Wrath of God (SP8, heroic)'),
(4278, 5, 0, '%s''s prayer nears its end!', 41, 0, 100, 0, 0, 0, 0, 0, 'Commander Springvale - Wrath of God, 10 s left (SP8, heroic)'),
(300507, 0, 0, '%s hurls his hammer at $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Risen Guardsman of the Hammer (Springvale boss kit) - Hammer of Judgement (SP1, heroic)');

-- The guardsmen carry the Wailing Guardsman 3877's weapon (item 3432, its stock row ID 1).
DELETE FROM `creature_equip_template` WHERE `CreatureID` IN (300506, 300507, 300508) AND `ID` = 1;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
(300506, 1, 3432, 0, 0, 0),
(300507, 1, 3432, 0, 0, 0),
(300508, 1, 3432, 0, 0, 0);
