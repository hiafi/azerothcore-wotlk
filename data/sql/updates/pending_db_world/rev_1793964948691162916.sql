-- Deadmines Pilot WP-B6: Cookie (645), the rows dbc-tools cannot declare (.agents/plans/deadmines-pilot/
-- deadmines-pilot.HANDOFF.md s3.5 row B6). His template (boss_cookie_rework, AIName '', health, immunities) and spells
-- are apps/dbc-tools source/npcs/deadmines/cookie.py; his patrol (creature 79344, creature_addon path 793440) stays.

-- SmartAI 645 (Acid Splash, Cookie's Cooking) is replaced by boss_cookie_rework: the whole block goes.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 645 AND `source_type` = 0;

-- Texts (Cookie had none). Talk() picks a random line within a group, so the build spec's "line 0" (one feed emote
-- per dish) is one group per dish: 0 Fire Pepper Chowder (the kit's EMOTE_COOKIE_FEED), 2 Week-Old Fish Stew,
-- 3 Gut Bomb; 1 is the aggro yell. The feed emotes are boss emotes (41) aimed at the eater ($n).
DELETE FROM `creature_text` WHERE `CreatureID` = 645;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(645, 0, 0, '%s feeds $n his Fire Pepper Chowder!', 41, 0, 100, 0, 0, 0, 0, 0, 'Cookie - Taste Test - Fire Pepper Chowder'),
(645, 1, 0, 'Mrglglgl! Eat! EAT!', 14, 0, 100, 0, 0, 0, 0, 0, 'Cookie - Aggro'),
(645, 2, 0, '%s feeds $n his Week-Old Fish Stew!', 41, 0, 100, 0, 0, 0, 0, 0, 'Cookie - Taste Test - Week-Old Fish Stew'),
(645, 3, 0, '%s feeds $n his Gut Bomb!', 41, 0, 100, 0, 0, 0, 0, 0, 'Cookie - Taste Test - Gut Bomb');
