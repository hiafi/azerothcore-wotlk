-- Stratholme build WP-S15: Baron Rivendare's hard mode, the Ultimatum (heroic only): the rows dbc-tools cannot
-- declare (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.7, s3.5 row S15; build spec
-- docs/dungeons/stratholme-rework.md ST 3709-3747, 3807-3828, 3868-3871). Ysida, Risen 300589 and the spells
-- 206720-206734 are apps/dbc-tools source/npcs/stratholme/baron_hard_mode.py; the fight is
-- modules/mod-dungeon-bosses src/Stratholme/baron_hard_mode.cpp on boss_baron_rivendare_rework (S14).

-- The opt-in (ST "Hard mode trigger"): Ysida Harmon's gossip menu 7091 (text 8344, no options until now) gains one
-- option. Choosing it sets the instance's DATA_ULTIMATUM (20) to 1 through her SmartAI below; the instance refuses it
-- off heroic, without the Baron Run's clock or while the Baron fights or is dead (StratholmeRework.h
-- UltimatumChangeAllowed), and keeps it lit through wipes until the clock runs out or he dies (ruling 60). The box
-- asks once more, since the choice cannot be taken back.
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 7091 AND `OptionID` = 0;
INSERT INTO `gossip_menu_option` (`MenuID`, `OptionID`, `OptionIcon`, `OptionText`, `OptionBroadcastTextID`, `OptionType`, `OptionNpcFlag`, `ActionMenuID`, `ActionPoiID`, `BoxCoded`, `BoxMoney`, `BoxText`, `BoxBroadcastTextID`, `VerifiedBuild`) VALUES
(7091, 0, 0, 'We can face the Baron now, on his terms, but he will turn his blade on you. (The Ultimatum: hard mode)', 0, 1, 1, 0, 0, 0, 0, 'The Baron will execute Ysida during the fight unless someone takes his blows for her. The choice stands until his clock runs out. Accept the Ultimatum?', 0, 0);

-- The option shows only when the instance would take it (handoff s3.7): heroic (49: difficulty 1), the Baron Run's
-- clock running (1: the player carries its aura 27861, effect 0), the hard mode not chosen yet (13: instance data
-- 20 = 0) and the Baron neither fighting nor dead (13: boss state 14 is not IN_PROGRESS (1) and not DONE (3)).
DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 15 AND `SourceGroup` = 7091 AND `SourceEntry` = 0;
INSERT INTO `conditions` (`SourceTypeOrReferenceId`, `SourceGroup`, `SourceEntry`, `SourceId`, `ElseGroup`, `ConditionTypeOrReference`, `ConditionTarget`, `ConditionValue1`, `ConditionValue2`, `ConditionValue3`, `NegativeCondition`, `ErrorType`, `ErrorTextId`, `ScriptName`, `Comment`) VALUES
(15, 7091, 0, 0, 0, 49, 0, 1, 0, 0, 0, 0, 0, '', 'Ysida Harmon - the Ultimatum option: heroic only'),
(15, 7091, 0, 0, 0, 1, 0, 27861, 0, 0, 0, 0, 0, '', 'Ysida Harmon - the Ultimatum option: the Baron Run''s clock is running'),
(15, 7091, 0, 0, 0, 13, 0, 20, 0, 0, 0, 0, 0, '', 'Ysida Harmon - the Ultimatum option: not chosen yet (DATA_ULTIMATUM 0)'),
(15, 7091, 0, 0, 0, 13, 0, 14, 1, 2, 1, 0, 0, '', 'Ysida Harmon - the Ultimatum option: the Baron is not fighting'),
(15, 7091, 0, 0, 0, 13, 0, 14, 3, 2, 1, 0, 0, '', 'Ysida Harmon - the Ultimatum option: the Baron is not dead');

-- Ysida Harmon's SmartAI, rewritten as a full block: rows 0-9 are the stock rows unchanged (her release on the Baron's
-- death, the exit gate, the 5 minute line); rows 10-12 are new: the Ultimatum option sets DATA_ULTIMATUM (SetData(20,
-- 1), the instance's own rule decides), she says line 2 and the gossip closes.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 16031 AND `source_type` = 0;
INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`, `event_type`, `event_phase_mask`, `event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, `event_param4`, `event_param5`, `event_param6`, `action_type`, `action_param1`, `action_param2`, `action_param3`, `action_param4`, `action_param5`, `action_param6`, `target_type`, `target_param1`, `target_param2`, `target_param3`, `target_param4`, `target_x`, `target_y`, `target_z`, `target_o`, `comment`) VALUES
(16031, 0, 0, 0, 38, 0, 100, 769, 1, 1, 0, 0, 0, 0, 67, 1, 7000, 7000, 0, 0, 100, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Ysida Harmon - On Data Set - Create Timed Event'),
(16031, 0, 1, 0, 59, 0, 100, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Ysida Harmon - On Timed Event - Say Line 0'),
(16031, 0, 2, 3, 38, 0, 100, 769, 2, 2, 0, 0, 0, 0, 118, 0, 0, 0, 0, 0, 0, 20, 181071, 50, 0, 0, 0, 0, 0, 0, 'Ysida Harmon - On Data Set - Set Gameobject State'),
(16031, 0, 3, 4, 61, 0, 100, 512, 0, 0, 0, 0, 0, 0, 69, 0, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 4041.38, -3340.82, 115.06, 0, 'Ysida Harmon - On Data Set - Move To Position'),
(16031, 0, 4, 5, 61, 0, 100, 512, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Ysida Harmon - On Data Set - Say Line 1'),
(16031, 0, 5, 6, 61, 0, 100, 512, 0, 0, 0, 0, 0, 0, 33, 16031, 0, 0, 0, 0, 0, 18, 100, 0, 0, 0, 0, 0, 0, 0, 'Ysida Harmon - On Data Set - Killed Monster Credit'),
(16031, 0, 6, 7, 61, 0, 100, 512, 0, 0, 0, 0, 0, 0, 15, 8945, 0, 0, 0, 0, 0, 18, 100, 0, 0, 0, 0, 0, 0, 0, 'Ysida Harmon - On Data Set - Area Explored Or Event Happens'),
(16031, 0, 7, 8, 61, 0, 100, 512, 0, 0, 0, 0, 0, 0, 41, 120000, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Ysida Harmon - On Data Set - Despawn'),
(16031, 0, 8, 0, 61, 0, 100, 512, 0, 0, 0, 0, 0, 0, 118, 0, 0, 0, 0, 0, 0, 20, 176424, 200, 0, 0, 0, 0, 0, 0, 'Ysida Harmon - On Data Set - Set Gameobject State'),
(16031, 0, 9, 0, 25, 0, 100, 512, 0, 0, 0, 0, 0, 0, 59, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Ysida Harmon - On Reset - Set Walk'),
(16031, 0, 10, 11, 62, 0, 100, 0, 7091, 0, 0, 0, 0, 0, 34, 20, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Ysida Harmon - On Gossip Option 0 Selected - Set Instance Data 20 to 1 (the Ultimatum)'),
(16031, 0, 11, 12, 61, 0, 100, 0, 0, 0, 0, 0, 0, 0, 1, 2, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Ysida Harmon - On Gossip Option 0 Selected - Say Line 2'),
(16031, 0, 12, 0, 61, 0, 100, 0, 0, 0, 0, 0, 0, 0, 72, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 'Ysida Harmon - On Gossip Option 0 Selected - Close Gossip');

-- Texts (ST "Text"): the Baron's groups 11-14 (groups 0-10 and 15 are stock or S14's and are not touched here) and
-- Ysida's line 2. The mechanic emotes are boss emotes (41), so they name the mechanic on screen; $n is the marked
-- player.
DELETE FROM `creature_text` WHERE `CreatureID` = 10440 AND `GroupID` IN (11, 12, 13, 14);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10440, 11, 0, 'So be it. She dies for your defiance!', 14, 0, 100, 0, 0, 0, 0, 0, 'Baron Rivendare - the Ultimatum pull'),
(10440, 12, 0, '%s raises his blade toward the prisoner!', 41, 0, 100, 0, 0, 0, 0, 0, 'Baron Rivendare - Execution (HM1)'),
(10440, 13, 0, '%s spurs his Deathcharger toward $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Baron Rivendare - Deathcharger (HM3)'),
(10440, 14, 0, 'Rise, crusader. Your Scourge needs you.', 14, 0, 100, 0, 0, 0, 0, 0, 'Baron Rivendare - Ysida rises');
DELETE FROM `creature_text` WHERE `CreatureID` = 16031 AND `GroupID` = 2;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(16031, 2, 0, 'Don''t wait on me. End him, whatever he does to me.', 12, 0, 100, 0, 0, 0, 0, 0, 'Ysida Harmon - the Ultimatum chosen');
