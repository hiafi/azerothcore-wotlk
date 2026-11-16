-- Blackrock Spire build WP-B14: General Drakkisath (10363), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.5 row B14; build spec
-- docs/dungeons/blackrock-spire-rework.md SP 3990-4082). His template (boss_drakkisath_rework, AIName '', health,
-- DamageModifier 3.5, immunity 1972, INSTANCE_BIND), the Chromatic Elite Guard's (npc_brs_chromatic_elite_guard,
-- AIName '', level 60, 25,000 at 5 players) and his spells 210520-210538 are apps/dbc-tools
-- source/npcs/blackrock_spire/drakkisath.py. He has no SmartAI (the stock script is C++); his loot rows are L-2's.

-- The Chromatic Elite Guards are bound to C++ (DR1, DR8; SP: "Guard AI in the same file"): their three SmartAI rows
-- go (Mortal Strike 15708 and Strike 15580 move into npc_brs_chromatic_elite_guard with the same timers; Knockdown
-- 16790 is retired, a stun on the tank).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10814 AND `source_type` = 0;

-- His texts (SP "Text"; he has none in stock). Yells 14, boss emotes 41. Lines 3-7 are said by the hard mode (WP-B15);
-- line 9 (the herald's arming) is B15's own row.
DELETE FROM `creature_text` WHERE `CreatureID` = 10363 AND `GroupID` BETWEEN 0 AND 8;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10363, 0, 0, 'You stand before Nefarian''s champion. Kneel, and take my mark!', 14, 0, 100, 0, 0, 0, 0, 0,
    'General Drakkisath - Aggro (DR1)'),
(10363, 1, 0, '%s burns a Searing Brand into $n!', 41, 0, 100, 0, 0, 0, 0, 0,
    'General Drakkisath - Searing Brand (DR2)'),
(10363, 2, 0, '%s burns a Collapsing Brand into $n!', 41, 0, 100, 0, 0, 0, 0, 0,
    'General Drakkisath - Collapsing Brand (DR3)'),
(10363, 3, 0, 'Enough! I will finish this myself.', 14, 0, 100, 0, 0, 0, 0, 0,
    'General Drakkisath - Phase 2 (DR16, hard mode)'),
(10363, 4, 0, 'Who among you will face me? Step forward, champion!', 14, 0, 100, 0, 0, 0, 0, 0,
    'General Drakkisath - The Champion''s Call (DR17, hard mode)'),
(10363, 5, 0, 'Cowards! Your fear is my trophy.', 14, 0, 100, 0, 0, 0, 0, 0,
    'General Drakkisath - The Call unanswered (DR17, hard mode)'),
(10363, 6, 0, 'You... fight well, for an insect.', 14, 0, 100, 0, 0, 0, 0, 0,
    'General Drakkisath - The Challenge won (DR18, hard mode)'),
(10363, 7, 0, 'Another trophy for the black flight!', 14, 0, 100, 0, 0, 0, 0, 0,
    'General Drakkisath - The Challenge lost (DR18, hard mode)'),
(10363, 8, 0, 'The master... will avenge me...', 14, 0, 100, 0, 0, 0, 0, 0, 'General Drakkisath - Death');
