-- Scholomance build WP-S2: Rattlegore (11622), the rows dbc-tools cannot declare
-- (.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S2; build spec
-- docs/dungeons/scholomance-rework.md SC 733-778). His template (boss_rattlegore_rework, AIName '', health,
-- DamageModifier, immunities), the Loose Part 300531, the Unfinished Construct 300532 and the spells 206130-206141 are
-- apps/dbc-tools source/npcs/scholomance/rattlegore.py.

-- Rattlegore: SmartAI 11622 is removed (SC "Stock kit"): Knock Away 10101 becomes 206140 (no threat cut), Strike 18368
-- is cast by the script, War Stomp 16727 is retired (Ossuary Eruption replaces it).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 11622 AND `source_type` = 0;

-- His emotes (SC "Text"; he has none stock): boss emotes (41), so they name the mechanic on screen. Group 0 has three
-- variants (the part an emote names is flavor only, SC Theme).
DELETE FROM `creature_text` WHERE `CreatureID` = 11622;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(11622, 0, 0, 'A piece of %s cracks loose and skitters across the floor!', 41, 0, 100, 0, 0, 0, 0, 0, 'Rattlegore - Part lands (RG1)'),
(11622, 0, 1, 'An arm of %s cracks loose and skitters across the floor!', 41, 0, 100, 0, 0, 0, 0, 0, 'Rattlegore - Part lands (RG1)'),
(11622, 0, 2, 'A rib of %s cracks loose and skitters across the floor!', 41, 0, 100, 0, 0, 0, 0, 0, 'Rattlegore - Part lands (RG1)'),
(11622, 0, 3, 'The skull plate of %s cracks loose and skitters across the floor!', 41, 0, 100, 0, 0, 0, 0, 0, 'Rattlegore - Part lands (RG1)'),
(11622, 1, 0, '%s stomps, and the ossuary floor heaves!', 41, 0, 100, 0, 0, 0, 0, 0, 'Rattlegore - Ossuary Eruption (RG4)'),
(11622, 2, 0, '%s lumbers toward an unfinished construct!', 41, 0, 100, 0, 0, 0, 0, 0, 'Rattlegore - Salvage (RG5)');

-- The Unfinished Construct 300532 lies in Permanent Feign Death 29266's collapsed pose (VISUALS-REPORT gap 6).
DELETE FROM `creature_template_addon` WHERE `entry` = 300532;
INSERT INTO `creature_template_addon` (`entry`, `path_id`, `mount`, `bytes1`, `bytes2`, `emote`, `visibilityDistanceType`, `auras`) VALUES
(300532, 0, 0, 0, 1, 0, 0, '29266');
