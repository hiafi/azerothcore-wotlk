-- Blackrock Depths build WP-D4: the Ring of Law's frame (High Justice Grimstone 10096) and its wave mobs, the rows
-- dbc-tools cannot declare (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D4; build
-- spec docs/dungeons/blackrock-depths-1-detention-block.md S1 "Ring of Law"). Grimstone's binding
-- (npc_grimstone_rework), the wave mobs' (npc_ring_beast_rework, AIName '', health) and spells 210810-210838 are
-- apps/dbc-tools source/npcs/blackrock_depths/ring_of_law.py. This rev inserts no spawn and no SmartAI row (rule 14:
-- nothing for the heroic spawn mask to miss).

-- The six wave mobs' SmartAI (14 rows: the opening debuffs, Poison, Venom Spit, Cleave, Sonic Burst, Lizard Bolt,
-- Thunderclap, Pierce Armor, Web): npc_ring_beast_rework runs them now (Sonic Burst, Web and the stock Thunderclap
-- retired). They are summoned only by Grimstone; no spawn names them.
DELETE FROM `smart_scripts` WHERE `entryorguid` IN (8925, 8926, 8927, 8928, 8932, 8933) AND `source_type` = 0;

-- Grimstone's new lines (S1 "Text"; groups 0-5 are the stock rows, kept: 3 "Good riddance!" now ends the won run).
-- The Sentences, the title holder, the banner burned and the Encore are yells (14); the banner thrown and the crowd's
-- roar and jeers are boss emotes (41) so they read on screen.
DELETE FROM `creature_text` WHERE `CreatureID` = 10096 AND `GroupID` BETWEEN 6 AND 14;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10096, 6, 0, 'Trial by fire! Let the Ring burn beneath your feet!', 14, 0, 100, 0, 0, 0, 0, 0,
    'High Justice Grimstone - Sentence: Trial by Fire (RL4)'),
(10096, 7, 0, 'Trial by beasts! Leave the cages open!', 14, 0, 100, 0, 0, 0, 0, 0,
    'High Justice Grimstone - Sentence: Trial by Beasts (RL5)'),
(10096, 8, 0, 'Trial by the crowd! Let the people judge you!', 14, 0, 100, 0, 0, 0, 0, 0,
    'High Justice Grimstone - Sentence: Trial by the Crowd (RL6)'),
(10096, 9, 0, 'The challenger falls! Now face the reigning champion of the Ring!', 14, 0, 100, 0, 0, 0, 0, 0,
    'High Justice Grimstone - The title holder (CH1)'),
(10096, 10, 0, 'The crowd hurls a Banner of Provocation into the arena!', 41, 0, 100, 0, 0, 0, 0, 0,
    'High Justice Grimstone - Favor 10 on heroic: the banner (EN1)'),
(10096, 11, 0, 'You burn the banner? You challenge the champions themselves? So be it!', 14, 0, 100, 0, 0, 0, 0, 0,
    'High Justice Grimstone - The banner burned (EN1, said for WP-D6)'),
(10096, 12, 0, 'Theldren! Show these fools how the Ring is won!', 14, 0, 100, 0, 0, 0, 0, 0,
    'High Justice Grimstone - The Encore'),
(10096, 13, 0, 'The crowd roars for you!', 41, 0, 100, 0, 0, 0, 0, 0,
    'High Justice Grimstone - Favor reaches 8 (RL2)'),
(10096, 14, 0, 'The crowd jeers!', 41, 0, 100, 0, 0, 0, 0, 0,
    'High Justice Grimstone - Favor drops to 2 (RL3)');
