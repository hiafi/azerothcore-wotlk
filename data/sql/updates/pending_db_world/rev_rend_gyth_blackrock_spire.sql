-- Blackrock Spire build WP-B12: Warchief Rend Blackhand (10429), Gyth (10339) and Lord Victor Nefarius's Blackrock
-- Spire copy (300732), the rows dbc-tools cannot declare (.agents/plans/blackrock-spire-build/blackrock-spire-build.
-- HANDOFF.md s3.5 row B12; build spec docs/dungeons/blackrock-spire-rework.md "Warchief Rend Blackhand and Gyth").
-- Their templates (the C++ bindings, health, the copy, the Banner 300733, the frost wall 300734) and spells
-- 210430-210452 are apps/dbc-tools source/npcs/blackrock_spire/rend_gyth.py. Their loot rows are L-2's.

-- The Nefarius copy takes the Blackrock Spire spawn (137967 at (163.17, -444.17, 122.06), the balcony); Blackwing
-- Lair's 10162 keeps its own spawn (85785, map 469), its script and its texts. It also spawns on heroic (spawnMask bit
-- 2) here: the dbc-tools heroic rev sorts before this file, so its id-gated spawn mask update still sees 10162.
UPDATE `creature` SET `id` = 300732, `spawnMask` = `spawnMask` | 2 WHERE `guid` = 137967 AND `id` IN (10162, 300732);

-- His staff (the stock equipment of 10162, the spawn's equipment_id 1) and his visibility row (stock: far).
DELETE FROM `creature_equip_template` WHERE `CreatureID` = 300732;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
(300732, 1, 19404, 0, 0, 0);
DELETE FROM `creature_template_addon` WHERE `entry` = 300732;
INSERT INTO `creature_template_addon` (`entry`, `path_id`, `mount`, `bytes1`, `bytes2`, `emote`,
    `visibilityDistanceType`, `auras`) VALUES
(300732, 0, 0, 0, 0, 0, 3, NULL);

-- The copy's texts: groups 0-11 are 10162's stock lines (copied with their broadcast texts and emotes; 3 stays unused),
-- 12-17 the rounds, 18-19 the insult (DR10: Drakkisath's hard mode trigger, said by the copy's ReceiveEmote; B15 reads
-- the saved flag). Yells 14, boss emotes 41 (map range: he speaks from the balcony), a say 12.
DELETE FROM `creature_text` WHERE `CreatureID` = 300732 AND `GroupID` BETWEEN 0 AND 19;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(300732, 0, 0, 'Excellent... it would appear as if the meddlesome insects have arrived just in time to '
    'feed my legion. Welcome, mortals!',
    14, 0, 100, 22, 0, 0, 5635, 0,
    'Lord Victor Nefarius (Blackrock Spire) - The trigger (RG1)'),
(300732, 1, 0, 'Let not even a drop of their blood remain upon the arena floor, my children. Feast on '
    'their souls!',
    14, 0, 100, 22, 0, 0, 5640, 0,
    'Lord Victor Nefarius (Blackrock Spire) - Group 1 (RG1)'),
(300732, 2, 0, 'Foolsss... Kill the one in the dress!', 14, 0, 100, 22, 0, 0, 5665, 0,
    'Lord Victor Nefarius (Blackrock Spire) - Kill the one in the dress (RG5)'),
(300732, 3, 0, 'Inconceivable!', 14, 0, 100, 22, 0, 0, 21235, 0,
    'Lord Victor Nefarius (Blackrock Spire) - Unused (stock)'),
(300732, 4, 0, 'Your efforts will prove fruitless. None shall stand in our way!', 14, 0, 100, 22, 0, 0, 5668, 0,
    'Lord Victor Nefarius (Blackrock Spire) - The bored host, step 2 (RG4)'),
(300732, 5, 0, 'Do not force my hand, children! I shall use your hides to line my boots.',
    14, 0, 100, 22, 0, 0, 5667, 0,
    'Lord Victor Nefarius (Blackrock Spire) - The bored host, step 1 (RG4)'),
(300732, 6, 0, 'Use the freezing breath, imbecile!', 14, 0, 100, 22, 0, 0, 5664, 0,
    'Lord Victor Nefarius (Blackrock Spire) - Freezing Sweep (RG6)'),
(300732, 7, 0, 'THIS CANNOT BE!!! Rend, deal with these insects.', 14, 0, 100, 0, 0, 0, 5709, 0,
    'Lord Victor Nefarius (Blackrock Spire) - Act 3 on the timer (RG3)'),
(300732, 8, 0, 'The Warchief shall make quick work of you, mortals. Prepare yourselves!', 14, 0, 100, 25, 0, 0, 5720, 0,
    'Lord Victor Nefarius (Blackrock Spire) - Act 2 (RG2)'),
(300732, 9, 0, 'Taste in my power!', 14, 0, 100, 0, 0, 0, 5726, 0,
    'Lord Victor Nefarius (Blackrock Spire) - Taste in my power (RG7)'),
(300732, 10, 0, 'Your victory shall be short lived. The days of both the Alliance and Horde are coming to '
    'an end! The next time we meet shall be the last.',
    14, 0, 100, 5, 0, 0, 5824, 0,
    'Lord Victor Nefarius (Blackrock Spire) - Rend''s death (RG3)'),
(300732, 11, 0, 'The mortals have fallen! The new age of the Blackrock legion is at hand!',
    14, 0, 100, 22, 0, 0, 5710, 0,
    'Lord Victor Nefarius (Blackrock Spire) - A wipe (RG15)'),
(300732, 12, 0, 'Must I do everything myself?', 14, 0, 100, 0, 0, 0, 0, 0,
    'Lord Victor Nefarius (Blackrock Spire) - Freezing Sweep with Gyth dead (RG6)'),
(300732, 13, 0, 'This one bores me. Share the fate, if you are so fond of it!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Lord Victor Nefarius (Blackrock Spire) - Thumbs Down (RG8, heroic)'),
(300732, 14, 0, 'Whelps hunt $n!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Lord Victor Nefarius (Blackrock Spire) - Kill the one in the dress (RG5)'),
(300732, 15, 0, 'A wall of frost sweeps the arena!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Lord Victor Nefarius (Blackrock Spire) - Freezing Sweep (RG6)'),
(300732, 16, 0, 'Shadowflame rains on the arena!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Lord Victor Nefarius (Blackrock Spire) - Taste in my power (RG7)'),
(300732, 17, 0, 'Nefarius turns his thumb down on $n!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Lord Victor Nefarius (Blackrock Spire) - Thumbs Down (RG8, heroic)'),
(300732, 18, 0, 'You dare mock me, insect? Drakkisath will answer for my honor, with every soldier I '
    'command.',
    14, 0, 100, 0, 0, 0, 0, 0,
    'Lord Victor Nefarius (Blackrock Spire) - The insult (DR10, Drakkisath''s hard mode)'),
(300732, 19, 0, 'Your insolence is noted. Drakkisath will see to you.', 12, 0, 100, 0, 0, 0, 0, 0,
    'Lord Victor Nefarius (Blackrock Spire) - A later insult (DR10)');

-- Rend's new lines (0-2 stock, kept): the Mark and the banner, boss emotes 41 (map range: in act 2 he rides out of
-- sight, so the emote names him from his balcony spot).
DELETE FROM `creature_text` WHERE `CreatureID` = 10429 AND `GroupID` BETWEEN 3 AND 4;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10429, 3, 0, '%s points his polearm at $n!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Warchief Rend Blackhand - Rend''s Mark (RG9)'),
(10429, 4, 0, '%s plants the banner of the Dark Horde!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Warchief Rend Blackhand - Banner of the Dark Horde (RG12)');

-- RG13: the Dragon Handler mends Gyth while he lives (stock Mend Dragon 16637, instant). Its stock row (event 0, any
-- difficulty, the closest friendly) stays for act 1; this row adds Gyth as the target (SMART_TARGET_CLOSEST_CREATURE
-- 19, entry 10339, 100 yd), every 10-14 s after 6-10 s. event_flags 0 (every difficulty): no heroic widening needed.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10742 AND `source_type` = 0 AND `id` = 1;
INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`, `event_type`, `event_phase_mask`,
    `event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, `event_param4`, `event_param5`,
    `event_param6`, `action_type`, `action_param1`, `action_param2`, `action_param3`, `action_param4`,
    `action_param5`, `action_param6`, `target_type`, `target_param1`, `target_param2`, `target_param3`,
    `target_param4`, `target_x`, `target_y`, `target_z`, `target_o`, `comment`) VALUES
(10742, 0, 1, 0, 0, 0, 100, 0, 6000, 10000, 10000, 14000, 0, 0, 11, 16637, 0, 0, 0, 0, 0, 19, 10339, 100, 0, 0, 0, 0, 0,
    0, 'Blackhand Dragon Handler - In Combat - Cast ''Mend Dragon'' on Gyth (Blackrock Spire build RG13)');
