-- Deadmines Pilot WP-B5, Mr. Smite 646 (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md s3.5 row B5; build
-- spec docs/dungeons/deadmines-rework.md "Mr. Smite"): the rows dbc-tools cannot declare. His script binding,
-- health, immunities and spells are apps/dbc-tools source/npcs/deadmines/mr_smite.py. Stock 646 has no SmartAI rows
-- (it ran the C++ boss_mr_smite, which stays untouched and unbound).

-- The boarding harpoon (build spec: creature_equip_template 646 ID 4 = item 44236, "Monster - Item, Harpoon (2H)",
-- display 7459). IDs 1-3 stay as they are: 2 dual cutlasses (the pull), 3 Smite's Mighty Hammer, 1 unused.
DELETE FROM `creature_equip_template` WHERE `CreatureID` = 646 AND `ID` = 4;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
(646, 4, 44236, 0, 0, 0);

-- The weapon emotes at each swap (build spec Text lines 4 and 5; groups 0-3 are stock and stay).
DELETE FROM `creature_text` WHERE `CreatureID` = 646 AND `GroupID` IN (4, 5);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(646, 4, 0, '%s pulls Smite\'s Mighty Hammer from the chest!', 41, 0, 100, 0, 0, 0, 0, 0, 'Mr. Smite - EMOTE_SMITE_HAMMER (Deadmines Pilot)'),
(646, 5, 0, '%s pulls a boarding harpoon from the chest!', 41, 0, 100, 0, 0, 0, 0, 0, 'Mr. Smite - EMOTE_SMITE_HARPOON (Deadmines Pilot)');

-- No adds (approved 2026-10-28): the two Defias Blackguards by his chest (entry 636, the stock spawns 79345 and 79346)
-- go, with their formation rows (leader 79337, Smite; the leader's own row goes too: he leads nobody now) and their
-- linked_respawn rows to Smite. They had no creature_addon, smart_scripts, pool or game event rows (read-only SELECTs
-- 2026-11-06). VanCleef's Blackguards (79369, 79370) are WP-B8's.
DELETE FROM `creature` WHERE `id` = 636 AND `guid` IN (79345, 79346);
DELETE FROM `creature_formations` WHERE `leaderGUID` = 79337;
DELETE FROM `linked_respawn` WHERE `guid` IN (79345, 79346) AND `linkType` = 0;
