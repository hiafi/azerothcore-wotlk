-- Shadowfang Keep build WP-S7: Fenrus the Devourer
-- (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md s3.6 row S7). The rows dbc-tools cannot
-- declare: the stock SmartAI the C++ replaces, and Fenrus's new emote.
--
-- Fenrus 4274 (boss_fenrus_the_devourer_rework) and Arugal's Voidwalker 4627 (npc_sfk_voidwalker) already have
-- AIName '' (apps/dbc-tools source/npcs/shadowfang_keep/fenrus_the_devourer.py), so these rows are inert; dropped so
-- nothing reads them again. Archmage Arugal's intro action list 427500 (pull line, Focus animation, the stock summon
-- group 4275/1) is retired: the Fenrus script drives Arugal's lines through the instance. Arugal's own block (4275,
-- source 0, including row 0 "On Data Set 1 1 - Start Script 427500") is WP-S9's full-block removal; nothing sets that
-- data any more (4274's rows are gone). creature_summon_groups 4275 group 1 stays, unused.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 4274 AND `source_type` = 0;
DELETE FROM `smart_scripts` WHERE `entryorguid` = 4627 AND `source_type` = 0;
DELETE FROM `smart_scripts` WHERE `entryorguid` = 427500 AND `source_type` = 9;

-- FN6 (heroic): the Shadow Leap warning, a raid boss emote (type 41, center screen). Arugal's lines 0-2 are stock.
DELETE FROM `creature_text` WHERE `CreatureID` = 4274 AND `GroupID` = 0;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(4274, 0, 0, '%s crouches, eyes fixed on the farthest prey!', 41, 0, 100, 0, 0, 0, 0, 0, 'Fenrus the Devourer - Shadow Leap (heroic)');
