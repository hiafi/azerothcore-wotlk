-- Stratholme build WP-S13: Ramstein the Gorger (10439), the rows dbc-tools cannot declare
-- (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S13; build spec
-- docs/dungeons/stratholme-rework.md ST 3432-3483). His template (boss_ramstein_the_gorger_rework, AIName '', health,
-- DamageModifier, immunities), the meat 11030's columns (npc_st_meat, AIName '', level 57, health), the Half-Digested
-- Corpse 300586, the gut puddle stalker 300587 and the spells 206685-206695 are apps/dbc-tools
-- source/npcs/stratholme/ramstein_the_gorger.py.

-- Ramstein: SmartAI 10439 is removed (ST "Stock kit"): Knockout 17307 becomes 206695 (no stun), Trample 5568 becomes
-- the 206692 circle and the 206694 tank hit, Flurry 15088 is cast by the script at the pull, and the walk-in action
-- list 1043900 (home position, door 175405, line 0, attack start) is the script's.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10439 AND `source_type` = 0;
DELETE FROM `smart_scripts` WHERE `entryorguid` = 1043900 AND `source_type` = 9;

-- The Mindless Undead 11030 (his meat since the slaughter event lost its Mindless stage): its one "attack start" row
-- goes, the script walks it to him and it never attacks.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 11030 AND `source_type` = 0;

-- His texts (ST "Text"): line 0 is the stock walk-in yell and stays. The bite and the tear are boss emotes (41), so
-- they name the mechanic on screen; the death yell is a yell (14).
DELETE FROM `creature_text` WHERE `CreatureID` = 10439 AND `GroupID` IN (1, 2, 3);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10439, 1, 0, '%s gorges on the dead!', 41, 0, 100, 0, 0, 0, 0, 0, 'Ramstein the Gorger - Gorge (RG2)'),
(10439, 2, 0, '%s''s stitches tear open!', 41, 0, 100, 0, 0, 0, 0, 0, 'Ramstein the Gorger - Bursting at the Seams (RG3)'),
(10439, 3, 0, 'Ramstein... still... hungry...', 14, 0, 100, 0, 0, 0, 0, 0, 'Ramstein the Gorger - Death');
