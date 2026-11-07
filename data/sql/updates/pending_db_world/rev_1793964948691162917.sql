-- Deadmines Pilot WP-B7: Captain Greenskin (647), the rows dbc-tools cannot declare (.agents/plans/deadmines-pilot/
-- deadmines-pilot.HANDOFF.md s3.5 row B7). His template (boss_captain_greenskin_rework, AIName '', health, immunities),
-- the rope anchor 300425 and his spells are apps/dbc-tools source/npcs/deadmines/captain_greenskin.py; the rope object
-- 301001 is WP-K's rev. His patrol (creature 79333, creature_addon path 793330) and his formation (leader 79333,
-- members 79334 and 79335) stay as they are.

-- SmartAI 647 (Cleave, Poisoned Harpoon) is replaced by boss_captain_greenskin_rework: the whole block goes.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 647 AND `source_type` = 0;

-- Texts (Greenskin had none). The harpoon emote is a boss emote (41) naming the target ($n).
DELETE FROM `creature_text` WHERE `CreatureID` = 647;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(647, 0, 0, 'Fire on my mark!', 14, 0, 100, 0, 0, 0, 0, 0, 'Captain Greenskin - Fire on My Mark'),
(647, 1, 0, '%s harpoons $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Captain Greenskin - Reel ''Em In - harpoon'),
(647, 2, 0, 'Reel ''em in, boys!', 14, 0, 100, 0, 0, 0, 0, 0, 'Captain Greenskin - Reel ''Em In - reeled'),
(647, 3, 0, 'Who let landlubbers on my deck?', 14, 0, 100, 0, 0, 0, 0, 0, 'Captain Greenskin - Aggro');
