-- Shadowfang Keep build WP-S3: Baron Silverlaine (3887) and his echoes (300503-300505), the rows dbc-tools cannot
-- declare (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md s3.6 row S3). His template
-- (boss_baron_silverlaine_rework, AIName '', health, immunities), the echoes' templates and the spells are
-- apps/dbc-tools source/npcs/shadowfang_keep/baron_silverlaine.py.

-- SmartAI 3887 goes: the aggro yell (line 0) is kept in C++; Veil of Shadow 7068 on the tank is replaced by Accursed
-- Veil on a random non-tank (SK "Stock kit", approved).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 3887 AND `source_type` = 0;

-- Silverlaine's new yells (SK "Text", approved); the stock line 0 ("Leave this accursed place at once!", broadcast
-- 48821) stays as it is. Lines 1-3 name the echo as it bursts in (the echoes come on timers, user ruling handoff s10),
-- line 4 is the heroic The Night Ends.
DELETE FROM `creature_text` WHERE `CreatureID` = 3887 AND `GroupID` BETWEEN 1 AND 4;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(3887, 1, 0, 'The beasts are loose in the cells! Bar the gates!', 14, 0, 100, 0, 0, 0, 0, 0, 'Baron Silverlaine - Echo of Rethilgore (BS1)'),
(3887, 2, 0, 'The kitchens... they butchered my servants!', 14, 0, 100, 0, 0, 0, 0, 0, 'Baron Silverlaine - Echo of Razorclaw (BS1)'),
(3887, 3, 0, 'The blind one hunts by sound! Run!', 14, 0, 100, 0, 0, 0, 0, 0, 'Baron Silverlaine - Echo of Odo (BS1)'),
(3887, 4, 0, 'It is the same night. It is always the same night!', 14, 0, 100, 0, 0, 0, 0, 0, 'Baron Silverlaine - The Night Ends (BS7, heroic)');

-- The echoes' mechanic emotes (type 41, center screen; $n is the player): the drain, the hook (said by MeatHook's cast
-- bar) and the hunt.
DELETE FROM `creature_text` WHERE `CreatureID` IN (300503, 300504, 300505);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(300503, 0, 0, '%s drains $n''s soul!', 41, 0, 100, 0, 0, 0, 0, 0, 'Echo of Rethilgore - Soul Drain (BS2)'),
(300504, 0, 0, '%s hurls a spectral hook at $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Echo of Razorclaw - Meat Hook (BS4)'),
(300505, 0, 0, '%s sniffs the air... and turns toward $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Echo of Odo - The Hunt (BS5)');
