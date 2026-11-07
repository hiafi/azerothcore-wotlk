-- Deadmines Pilot WP-B1 (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md s3.5 row B1): Rhahk'Zor, the
-- boss-kit Watchman and Evoker. The creature rows, spells and script bindings are apps/dbc-tools
-- source/npcs/deadmines/rhahk_zor.py; the C++ is modules/mod-dungeon-bosses boss_rhahk_zor_rework.cpp.

-- Rhahk'Zor's stock SmartAI (yell, Slam, Factory Door, instance data) is replaced by boss_rhahk_zor_rework.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 644 AND `source_type` = 0;

-- The two stock Defias Watchmen (1725) beside him become the boss kit: 79165 the Watchman, 79167 the Evoker. The
-- stock 1725 / 1729 SmartAI rows stay for the other spawns of those entries.
UPDATE `creature` SET `id` = 300420 WHERE `guid` = 79165 AND `id` = 1725;
UPDATE `creature` SET `id` = 300421 WHERE `guid` = 79167 AND `id` = 1725;

-- Build spec "Text": Rhahk'Zor lines 1-2 (line 0, the stock aggro yell, is kept), the Evoker's and the Watchman's
-- heroic line 0. Boss emotes (41), %s = the speaker.
DELETE FROM `creature_text` WHERE `CreatureID` = 644 AND `GroupID` IN (1, 2);
DELETE FROM `creature_text` WHERE `CreatureID` IN (300420, 300421) AND `GroupID` = 0;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(644, 1, 0, '%s slams his hammer into the ceiling supports!', 41, 0, 100, 0, 0, 0, 0, 0, 'Rhahk''Zor - Cave In (RZ1)'),
(644, 2, 0, '%s begins to spin!', 41, 0, 100, 0, 0, 0, 0, 0, 'Rhahk''Zor - Whirlwind (RZ4)'),
(300420, 0, 0, '%s shouts directions to Rhahk''Zor!', 41, 0, 100, 0, 0, 0, 0, 0, 'Defias Watchman (Rhahk''Zor boss kit) - Lookout (RZ10, heroic)'),
(300421, 0, 0, '%s begins to gather flame!', 41, 0, 100, 0, 0, 0, 0, 0, 'Defias Evoker (Rhahk''Zor boss kit) - Fireball Volley (RZ8, heroic)');
