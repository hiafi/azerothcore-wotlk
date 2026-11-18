-- Blackrock Depths build WP-D11: Lord Incendius (9017), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D11; build spec
-- docs/dungeons/blackrock-depths-2-shadowforge-city.md "Lord Incendius", Text). His template
-- (boss_lord_incendius_rework, AIName '', health, DamageModifier, immunity 1973, INSTANCE_BIND), the Ember of
-- Incendius 300794 and the spells 211140-211155 are apps/dbc-tools source/npcs/blackrock_depths/incendius.py; the S0
-- rev drops his five SmartAI rows;
-- his patrol (path 477330) is kept as it is.

-- His texts, groups 0-7 (D12 owns 8-9 and deletes only those): the stock death say (group 0, BroadcastTextId 5061)
-- becomes the shatter yell; the new lines are yells (14) and boss emotes (41). 4, 6 and 7 are the hard mode's (D12
-- says them). The emotes are map-wide (TextRange 3, R-1-B n1): a boss emote reaches 40 yd from him and the hard mode's
-- giant stands 28 yd off the causeway, so the far neck would miss the crumble and Arm Sweep warnings.
DELETE FROM `creature_text` WHERE `CreatureID` = 9017 AND `GroupID` BETWEEN 0 AND 7;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9017, 0, 0, 'I cannot be destroyed! By the will of Ragnaros, I shall be reborn!', 14, 0, 100, 0, 0, 0, 5061, 0,
    'Lord Incendius - Shatter (IN6)'),
(9017, 1, 0, 'The anvil remakes me!', 14, 0, 100, 0, 0, 0, 0, 0, 'Lord Incendius - Reborn (IN7)'),
(9017, 2, 0, 'The island''s edge crumbles into the fire!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Lord Incendius - The trap closes (IN8)'),
(9017, 3, 0, 'Ragnaros... I have... failed...', 14, 0, 100, 0, 0, 0, 0, 0, 'Lord Incendius - Death'),
(9017, 4, 0, 'The Firelord''s own flame! Now you face me as I truly am!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Lord Incendius - Lord of the Lake (IN9, D12)'),
(9017, 5, 0, 'The island''s edge cracks!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Lord Incendius - Crumble warning (IN8 / IN13)'),
(9017, 6, 0, '%s raises his arm over the island!', 41, 0, 100, 0, 0, 0, 0, 3, 'Lord Incendius - Arm Sweep (IN11, D12)'),
(9017, 7, 0, '%s finds no one within reach and breathes fire across the island!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Lord Incendius - Firelord''s Breath (IN14, D12)');
