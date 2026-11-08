-- Shadowfang Keep build WP-S9: Archmage Arugal (4275) and the lair prisoners, the rows dbc-tools cannot declare
-- (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md s3.6 row S9). His template
-- (boss_archmage_arugal_rework, AIName '', health, immunities), the lair prisoners 300513 / 300514, the ward stalker
-- 300515 and the spells are apps/dbc-tools source/npcs/shadowfang_keep/archmage_arugal.py.

-- SmartAI 4275, all of it (WP-S7's request): his fight is the C++ script's; row 0 (On Data Set 1 1, the Fenrus intro
-- 427500) is retired with WP-S7's rev. His creature_text lines 0-2 stay as they are (the Fenrus fight uses them).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 4275 AND `source_type` = 0;

-- The prisoners at the Courtyard Door (SK "Lines", approved): the new farewell (group 8) in place of the stock one
-- (Adamant's line 3 on row 4, Ashcrombe's line 2 on row 2), and the instance learns which prisoner opened the door
-- (DATA_PRISONER 21: 1 Ashcrombe, 2 Adamant), so that prisoner waits at Arugal's lair door. The new row 7 goes in
-- before the despawn (stock row 7 moves to 8: Ashcrombe despawns at once, so a row after it would never run). Both
-- action lists are rewritten in full (sql-guidelines); every other row is the stock row as read live 2026-11-07.
DELETE FROM `smart_scripts` WHERE `entryorguid` IN (384900, 385000) AND `source_type` = 9;
INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`, `event_type`, `event_phase_mask`, `event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, `event_param4`, `event_param5`, `event_param6`, `action_type`, `action_param1`, `action_param2`, `action_param3`, `action_param4`, `action_param5`, `action_param6`, `target_type`, `target_param1`, `target_param2`, `target_param3`, `target_param4`, `target_x`, `target_y`, `target_z`, `target_o`, `comment`) VALUES
(384900, 9, 0, 0, 0, 0, 100, 0, 1000, 1000, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Deathstalker Adamant - Script9 - Say Line 1'),
(384900, 9, 1, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 5, 432, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Deathstalker Adamant - Script9 - Play Emote'),
(384900, 9, 2, 0, 0, 0, 100, 0, 5000, 5000, 0, 0, 0, 0, 1, 2, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Deathstalker Adamant - Script9 - Say Line 2'),
(384900, 9, 3, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 118, 0, 0, 0, 0, 0, 0, 14, 20835, 18895, 0, 0, 0, 0, 0, 0, 'Deathstalker Adamant - Script9 - Set GO State'),
(384900, 9, 4, 0, 0, 0, 100, 0, 3000, 3000, 0, 0, 0, 0, 1, 8, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Deathstalker Adamant - Script9 - Say Line 8 (farewell)'),
(384900, 9, 5, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 34, 0, 3, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Deathstalker Adamant - Script9 - Set Instance Data 0 to 3'),
(384900, 9, 6, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 69, 0, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, -209, 2139.89, 90.63, 0, 'Deathstalker Adamant - Script9 - Move To Pos'),
(384900, 9, 7, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 34, 21, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Deathstalker Adamant - Script9 - Set Instance Data 21 to 2 (the lair prisoner)'),
(384900, 9, 8, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 41, 5000, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Deathstalker Adamant - Script9 - Despawn'),
(385000, 9, 0, 0, 0, 0, 100, 0, 1000, 1000, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Sorcerer Ashcrombe - Script9 - Say Line 1'),
(385000, 9, 1, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 11, 6421, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Sorcerer Ashcrombe - Script9 - Cast Ashcrombe Unlock'),
(385000, 9, 2, 0, 0, 0, 100, 0, 6000, 6000, 0, 0, 0, 0, 1, 8, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Sorcerer Ashcrombe - Script9 - Say Line 8 (farewell)'),
(385000, 9, 3, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 118, 0, 0, 0, 0, 0, 0, 14, 20835, 18895, 0, 0, 0, 0, 0, 0, 'Sorcerer Ashcrombe - Script9 - Set GO State'),
(385000, 9, 4, 0, 0, 0, 100, 0, 7000, 7000, 0, 0, 0, 0, 11, 6422, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Sorcerer Ashcrombe - Script9 - Cast Ashcrombe Teleport'),
(385000, 9, 5, 0, 0, 0, 100, 0, 2000, 2000, 0, 0, 0, 0, 1, 3, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Sorcerer Ashcrombe - Script9 - Say Line 3'),
(385000, 9, 6, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 34, 0, 3, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Sorcerer Ashcrombe - Script9 - Set Instance Data 0 to 3'),
(385000, 9, 7, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 34, 21, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Sorcerer Ashcrombe - Script9 - Set Instance Data 21 to 1 (the lair prisoner)'),
(385000, 9, 8, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 41, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Sorcerer Ashcrombe - Script9 - Despawn');

-- Arugal's new lines (SK "Text", approved): Moonrise (heroic) yell 4 and emote 5 (type 41, center screen).
DELETE FROM `creature_text` WHERE `CreatureID` = 4275 AND `GroupID` IN (4, 5);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(4275, 4, 0, 'The moon rises! Embrace your true selves, my children!', 14, 0, 100, 0, 0, 0, 0, 0, 'Archmage Arugal - Moonrise (AR9, heroic)'),
(4275, 5, 0, '%s calls down the full moon!', 41, 0, 100, 0, 0, 0, 0, 0, 'Archmage Arugal - Moonrise emote (AR9, heroic)');

-- The prisoners' lines (SK "Text", approved): the Courtyard Door farewell on the stock prisoners (group 8); Arugal's
-- pull (group 6) and the Face Him Alone choice (group 7, said by S10's gossip through LairPrisoner.h) on the lair
-- copies 300513 / 300514.
DELETE FROM `creature_text` WHERE `CreatureID` IN (3849, 3850) AND `GroupID` = 8;
DELETE FROM `creature_text` WHERE `CreatureID` IN (300513, 300514) AND `GroupID` IN (6, 7);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(3849, 8, 0, 'Go on ahead. I''ll be there when you face Arugal.', 12, 0, 100, 0, 0, 0, 0, 0, 'Deathstalker Adamant - Courtyard Door farewell (replaces line 3)'),
(3850, 8, 0, 'I will follow when you face Arugal. I would not miss it.', 12, 0, 100, 0, 0, 0, 0, 0, 'Sorcerer Ashcrombe - Courtyard Door farewell (replaces line 2)'),
(300513, 6, 0, 'I can hold back his curse, but not for long. Stand in my wards!', 12, 0, 100, 0, 0, 0, 0, 0, 'Sorcerer Ashcrombe (lair) - Arugal''s pull'),
(300513, 7, 0, 'Then may the Kirin Tor watch over you.', 12, 0, 100, 0, 0, 0, 0, 0, 'Sorcerer Ashcrombe (lair) - Face Him Alone'),
(300514, 6, 0, 'The Dark Lady''s apothecaries taught me a trick or two. Stand in the smoke!', 12, 0, 100, 0, 0, 0, 0, 0, 'Deathstalker Adamant (lair) - Arugal''s pull'),
(300514, 7, 0, 'Your funeral. Try not to come back as a dog.', 12, 0, 100, 0, 0, 0, 0, 0, 'Deathstalker Adamant (lair) - Face Him Alone');

-- The lair prisoners' gossip menus (SK "Gossip", approved): the body text, no option (S10 adds the heroic "Stay
-- behind" option through LairPrisoner.h; the stock menus 21213 / 21214 are unchanged). Menu and text ids are the
-- creature entries (free 2026-11-07: no gossip_menu, npc_text or pending SQL row).
DELETE FROM `npc_text` WHERE `ID` IN (300513, 300514);
INSERT INTO `npc_text` (`ID`, `text0_0`, `text0_1`, `BroadcastTextID0`, `lang0`, `Probability0`, `BroadcastTextID1`, `Probability1`, `BroadcastTextID2`, `Probability2`, `BroadcastTextID3`, `Probability3`, `BroadcastTextID4`, `Probability4`, `BroadcastTextID5`, `Probability5`, `BroadcastTextID6`, `Probability6`, `BroadcastTextID7`, `Probability7`, `VerifiedBuild`) VALUES
(300513, 'Arugal is beyond this door. His curse will take you all if I am not there to hold it back.', 'Arugal is beyond this door. His curse will take you all if I am not there to hold it back.', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(300514, 'The wretch is through there. You want me in there with you, or not?', 'The wretch is through there. You want me in there with you, or not?', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
DELETE FROM `gossip_menu` WHERE `MenuID` IN (300513, 300514);
INSERT INTO `gossip_menu` (`MenuID`, `TextID`) VALUES
(300513, 300513),
(300514, 300514);
