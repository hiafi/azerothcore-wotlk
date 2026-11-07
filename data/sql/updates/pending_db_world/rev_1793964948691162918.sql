-- Deadmines Pilot WP-B8: Edwin VanCleef (639), the rows dbc-tools cannot declare (.agents/plans/deadmines-pilot/
-- deadmines-pilot.HANDOFF.md s3.5 row B8; build spec docs/dungeons/deadmines-rework.md "Edwin VanCleef"). His template
-- (boss_edwin_vancleef_rework, AIName '', health, immunities), the Blackguard 300426, the shadow image 300427 and his
-- spells are apps/dbc-tools source/npcs/deadmines/edwin_vancleef.py. His spawn 79336 stays (mod-dungeon-clear's
-- roster; the instance hides him until Greenskin is DONE), and so does his creature_template_addon (Thrash 3417).

-- SmartAI 639 (Dual Wield, lines 0-5, VanCleef's Allies 5200) is replaced by boss_edwin_vancleef_rework: the whole
-- block goes. Stock 636's SmartAI stays (the entry is no longer spawned in the dungeon; the Blackguard is 300426).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 639 AND `source_type` = 0;

-- He arrives alone: the two Defias Blackguards beside him (entry 636, spawns 79369 and 79370) go, with their
-- formation rows (leader 79336, VanCleef; his own leader row goes too: he leads nobody now) and 79370's linked_respawn
-- row to him (79369 has none; the other rows linked to 79336 are Greenskin's crew and trash, kept). They had no
-- creature_addon, smart_scripts, pool or game event rows (read-only SELECTs 2026-11-06).
DELETE FROM `creature` WHERE `id` = 636 AND `guid` IN (79369, 79370);
DELETE FROM `creature_formations` WHERE `leaderGUID` = 79336;
DELETE FROM `linked_respawn` WHERE `guid` IN (79369, 79370) AND `linkType` = 0;

-- Texts 6-10 (groups 0-5 are stock and stay). 6 names VC1 as a boss emote; 7-9 are the hard mode's (WP-B9); 10 is the
-- arrival yell the instance plays on Greenskin's DONE (ruling 26).
DELETE FROM `creature_text` WHERE `CreatureID` = 639 AND `GroupID` BETWEEN 6 AND 10;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(639, 6, 0, '%s vanishes into the rigging!', 41, 0, 100, 0, 0, 0, 0, 0, 'Edwin VanCleef - Ambush from the Rigging (Deadmines Pilot)'),
(639, 7, 0, 'You fools, you''ll kill us all!', 14, 0, 100, 0, 0, 0, 0, 0, 'Edwin VanCleef - hard mode fuse (Deadmines Pilot)'),
(639, 8, 0, 'The mast! Get clear of the mast!', 14, 0, 100, 0, 0, 0, 0, 0, 'Edwin VanCleef - hard mode mainmast (Deadmines Pilot)'),
(639, 9, 0, 'Get off my ship!', 14, 0, 100, 0, 0, 0, 0, 0, 'Edwin VanCleef - hard mode 2:45 (Deadmines Pilot)'),
(639, 10, 0, 'Greenskin, you fool! Must I do everything myself?', 14, 0, 100, 0, 0, 0, 0, 0, 'Edwin VanCleef - arrival (Deadmines Pilot)');
