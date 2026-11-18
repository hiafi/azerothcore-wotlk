-- Blackrock Depths build WP-D18: Hurley Blackbreath (9537) and his Blackbreath Cronies (9541), the rows dbc-tools
-- cannot declare (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D18, s7 #13; build
-- spec docs/dungeons/blackrock-depths-4-imperial-seat.md S4 "Hurley Blackbreath"). His and the Cronies' templates
-- (boss_hurley_blackbreath_rework and npc_blackbreath_crony_rework behind the wave switch), the keg 300839, the puddle
-- 300840 and the spells 211430-211445 are apps/dbc-tools source/npcs/blackrock_depths/hurley.py. Wave 2: apply only
-- with the wave switch on (BIND_WAVE_2 / kWave2Bound): the drops below leave the stock SmartAI units without a script.
-- This rev inserts no creature spawn and no SmartAI row (rule 14: nothing for the heroic spawn mask to miss). The keg
-- objects' SmartAI (164911 rows 0-2, the wake-up: SET_DATA 1,1 to 9537 on the third keg) and the escort paths in
-- `waypoints` (entries 9537, 9541, 9541000, 9541001: the C++ carries its own copy, HurleyLogic.h kWakePath) are kept.

-- His SmartAI (S4 "Implementation": clear his smart_scripts rows): rows 0-20 (20 rows, no id 5), the hidden spawn,
-- the wake, the escort, Drunken Rage 14872, the stock Flame Breath 9573, Hamstring 26211, Mortal Strike 16856 and the
-- aggro links. The C++ keeps the wake and fixes the passive arrival.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 9537 AND `source_type` = 0;

-- The Cronies' per-guid SmartAI (s7 #13: C++ for the heroic Bottle Toss): rows 0-15 of each spawn (71997-71999), the
-- hidden spawn, the run, Sinister Strike 15581, Rupture 15583 (now heroic only) and the aggro links. They have no
-- entry-level rows.
DELETE FROM `smart_scripts` WHERE `entryorguid` IN (-71997, -71998, -71999) AND `source_type` = 0;

-- s7 #13: Hurley (guid 72000) and the Cronies (71997-71999) respawned in 300 s; the dungeon's other bosses use 43,200.
UPDATE `creature` SET `spawntimesecs` = 43200 WHERE `id` = 9537 AND `guid` = 72000;
UPDATE `creature` SET `spawntimesecs` = 43200 WHERE `id` = 9541 AND `guid` IN (71997, 71998, 71999);

-- His texts (S4 "Text"): groups 0-1 are the stock wake yell and arrival say and stay. The drink is a boss emote (41:
-- center of the screen) so the stack reads.
DELETE FROM `creature_text` WHERE `CreatureID` = 9537 AND `GroupID` BETWEEN 2 AND 5;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9537, 2, 0, 'All this fighting''s made me thirsty!', 14, 0, 100, 0, 0, 0, 0, 0, 'Hurley Blackbreath - Keg Run (HU3)'),
(9537, 3, 0, '%s drains the keg and roars with Liquid Courage!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Hurley Blackbreath - Liquid Courage (HU4)'),
(9537, 4, 0, 'That was good ale, you fools!', 14, 0, 100, 0, 0, 0, 0, 0, 'Hurley Blackbreath - Keg smashed (HU3)'),
(9537, 5, 0, 'Tell Ragnar... it was... delicious...', 14, 0, 100, 0, 0, 0, 0, 0, 'Hurley Blackbreath - Death');
