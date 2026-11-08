-- Scholomance build WP-S10: Lady Illucia Barov (10502), the rows dbc-tools cannot declare
-- (.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S10). Her template
-- (boss_lady_illucia_barov_rework, AIName '', health, DamageModifier 3.5, immunities) and her spells are
-- apps/dbc-tools source/npcs/scholomance/lady_illucia_barov.py.

-- SmartAI 10502 (Fear 12542, Shadow Shock 19460, Silence 15487, Curse of Agony 18266, the death's SetData(1,1)) is
-- removed, the whole block (SC "Stock kit", approved): boss_lady_illucia_barov_rework casts Shadow Shock and Curse of
-- Agony itself, replaces the Fear with its own 2 s Fear 206319 (the scripted run and its end marker), retires Silence,
-- and its boss state replaces the instance data call.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10502 AND `source_type` = 0;

-- Texts (SC "Text", approved 2026-11-01; she had none): the yells name the read player ($n); the Fear line is a boss
-- emote (41), so it names the mechanic on screen.
DELETE FROM `creature_text` WHERE `CreatureID` = 10502;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10502, 0, 0, 'Your thoughts are so very loud.', 14, 0, 100, 0, 0, 0, 0, 0, 'Lady Illucia Barov - Aggro'),
(10502, 1, 0, 'I know where you will go, $n.', 14, 0, 100, 0, 0, 0, 0, 0, 'Lady Illucia Barov - Foresight (IB1)'),
(10502, 2, 0, '%s fills $n\'s mind with dread!', 41, 0, 100, 0, 0, 0, 0, 0, 'Lady Illucia Barov - Fear (IB3)'),
(10502, 3, 0, 'My children... I never saw... it coming...', 14, 0, 100, 0, 0, 0, 0, 0, 'Lady Illucia Barov - Death');
