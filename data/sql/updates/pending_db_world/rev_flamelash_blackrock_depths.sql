-- Blackrock Depths build WP-D20: Ambassador Flamelash (9156), his Burning Spirits (9178) and the Portal Anchor
-- (300842), the rows dbc-tools cannot declare (.agents/plans/blackrock-depths-build/
-- blackrock-depths-build.HANDOFF.md s3.5 row D20; build spec docs/dungeons/blackrock-depths-4-imperial-seat.md
-- "Ambassador Flamelash" S4 740-783). His template (boss_ambassador_flamelash_rework, AIName '', 150k, immunity 1972,
-- INSTANCE_BIND), the Burning Spirit's columns, the Portal Anchor's template and the spells 211490-211499 are apps/
-- dbc-tools source/npcs/blackrock_depths/flamelash.py (the two stock units' columns land when wave 2 binds,
-- BIND_WAVE_2). Neither stock unit has SmartAI rows (both were C++: boss_ambassador_flamelash and npc_burning_spirit),
-- so there is nothing to drop; the Burning Spirit has no spawn (summoned only by the boss script) and the anchor is
-- summoned too. This rev inserts no creature spawn and no SmartAI row (rule 14: nothing for the heroic spawn mask to
-- miss). His loot and the seven rune objects (170578-170584) are untouched: L-2 adds the Dark Keeper Key, the script
-- turns a rune's button on while its anchor stands.

-- His texts (S4 "Text"): group 0 is the stock aggro yell and stays. Line 2 is a boss emote (41: center-screen and in
-- the raid warning area) and map-wide (TextRange 3) so it reads across the 70 yd chamber.
DELETE FROM `creature_text` WHERE `CreatureID` = 9156 AND `GroupID` BETWEEN 1 AND 3;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9156, 1, 0, 'The Firelands answer their master''s call!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Ambassador Flamelash - A portal opens (FL2)'),
(9156, 2, 0, '%s kindles $n!', 41, 0, 100, 0, 0, 0, 0, 3, 'Ambassador Flamelash - Kindling (FL4)'),
(9156, 3, 0, 'Ragnaros... will hear of this...', 14, 0, 100, 0, 0, 0, 0, 0, 'Ambassador Flamelash - Death');
