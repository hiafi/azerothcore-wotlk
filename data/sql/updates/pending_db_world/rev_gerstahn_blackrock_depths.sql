-- Blackrock Depths build WP-D1: High Interrogator Gerstahn (9018), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D1; build spec
-- docs/dungeons/blackrock-depths-1-detention-block.md S1 181-228). Her template
-- (boss_high_interrogator_gerstahn_rework, AIName '', health, DamageModifier 3.5, immunity 1972) and the spells
-- 210720-210733 are apps/dbc-tools source/npcs/blackrock_depths/gerstahn.py. She had no SmartAI rows (stock C++).
-- Her loot (the Prison Cell Key 11140, A Crumpled Up Note 11446) and her spawn are untouched; the Dark Keeper Key row
-- is L-1's.

-- Her texts (S1 "Text"; she had none): yells on the pull, a break and her death (type 14), boss emotes for the
-- Interrogation Circle and Mind Sear (type 41: center-screen and in the raid warning area).
DELETE FROM `creature_text` WHERE `CreatureID` = 9018 AND `GroupID` BETWEEN 0 AND 4;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9018, 0, 0, 'More visitors for my cells? Everyone talks eventually.', 14, 0, 100, 0, 0, 0, 0, 0,
    'High Interrogator Gerstahn - Pull'),
(9018, 1, 0, 'There it is. I knew you would break.', 14, 0, 100, 0, 0, 0, 0, 0,
    'High Interrogator Gerstahn - A break, Knowledge gained (GE1)'),
(9018, 2, 0, '%s begins to interrogate everyone around her!', 41, 0, 100, 0, 0, 0, 0, 0,
    'High Interrogator Gerstahn - Interrogation Circle (GE4)'),
(9018, 3, 0, '%s sears the mind of $n!', 41, 0, 100, 0, 0, 0, 0, 0,
    'High Interrogator Gerstahn - Mind Sear (GE5)'),
(9018, 4, 0, 'The Hammer... will learn... what I could not...', 14, 0, 100, 0, 0, 0, 0, 0,
    'High Interrogator Gerstahn - Death');
