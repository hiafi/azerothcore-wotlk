-- Scholomance build WP-S8: The Ravenian (10507) and Master Corvane (300542), the rows dbc-tools cannot declare
-- (.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S8; build spec
-- docs/dungeons/scholomance-rework.md SC 2193-2259). The Ravenian's template (boss_the_ravenian_rework, AIName '',
-- health, DamageModifier 3.5, immunities), Master Corvane 300542 and the spells 206270-206285 are apps/dbc-tools
-- source/npcs/scholomance/the_ravenian.py.

-- SmartAI 10507 (Cleave 20691, Trample 15550, Knock Away 10101, Sundering Cleave 25174, the death's SetData(1,1)) is
-- removed, the whole block (SC "Stock kit", approved): boss_the_ravenian_rework retires Cleave, Trample and Knock Away,
-- casts its one-target copy of Sundering Cleave (206285) itself, and its boss state replaces the instance data call.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10507 AND `source_type` = 0;

-- Texts (SC "Text", approved 2026-10-31; the Ravenian had none, Corvane is new): the Ravenian's line is a boss emote
-- (41), so it names the moment on screen; Corvane's are yells (14). The examiners (S13) say nothing.
DELETE FROM `creature_text` WHERE `CreatureID` IN (10507, 300542);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10507, 0, 0, '%s tears free of its leash!', 41, 0, 100, 0, 0, 0, 0, 0, 'The Ravenian - Master Corvane died first (RV10)'),
(300542, 0, 0, 'Observe, students. Flesh obeys.', 14, 0, 100, 0, 0, 0, 0, 0, 'Master Corvane - Aggro'),
(300542, 1, 0, 'Ravenian! Trample!', 14, 0, 100, 0, 0, 0, 0, 0, 'Master Corvane - Order: Trample (RV1)'),
(300542, 2, 0, 'Ravenian! Sweep!', 14, 0, 100, 0, 0, 0, 0, 0, 'Master Corvane - Order: Sweep (RV2)'),
(300542, 3, 0, 'Ravenian! Smash!', 14, 0, 100, 0, 0, 0, 0, 0, 'Master Corvane - Order: Smash (RV3)'),
(300542, 4, 0, 'Hold together, my beauty. I am coming.', 14, 0, 100, 0, 0, 0, 0, 0, 'Master Corvane - Transition (RV5)'),
(300542, 5, 0, 'My... masterpiece...', 14, 0, 100, 0, 0, 0, 0, 0, 'Master Corvane - Death'),
(300542, 6, 0, 'You broke it! You BROKE it!', 14, 0, 100, 0, 0, 0, 0, 0, 'Master Corvane - The Ravenian died first (RV10)');
