-- Stratholme build WP-S11: Nerub'enkan (10437), the rows dbc-tools cannot declare
-- (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S11; build spec
-- docs/dungeons/stratholme-rework.md ST 2859-2911). His template (boss_nerubenkan_rework, AIName '', health,
-- DamageModifier, immunities, INSTANCE_BIND), the scarab 10876's normal health, the Web Cocoon 300582, the web patch
-- 300583 and the spells 206645-206660 are apps/dbc-tools source/npcs/stratholme/nerubenkan.py.

-- Nerub'enkan: SmartAI 10437 is removed (ST "Stock kit"): Encasing Webs 4962 becomes the Cocoon, Pierce Armor 6016 is
-- cast by the script, Crypt Scarabs 31602 (summons nothing) and Raise Undead Scarab 17235 are retired (scarabs hatch
-- from cocoons and, on heroic, the Brood Call), and the ziggurat write on death (set instance data 2 to 1) is the
-- rework instance's own.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10437 AND `source_type` = 0;

-- The Undead Scarab 10876 (his alone): its out-of-combat "attack the closest player" row goes (the script sends each
-- new scarab at the nearest player); its reset row 0 (Poison Proc 13299) stays.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10876 AND `source_type` = 0 AND `id` = 1;

-- His texts (ST "Text"; he has none stock): yells 14, boss emotes 41 (they name the mechanic on screen).
DELETE FROM `creature_text` WHERE `CreatureID` = 10437;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10437, 0, 0, 'The web trembles. Prey has come.', 14, 0, 100, 0, 0, 0, 0, 0, 'Nerub''enkan - Aggro'),
(10437, 1, 0, '%s spits a web at $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Nerub''enkan - Web Spray (NE1)'),
(10437, 2, 0, '%s wraps $n in a cocoon!', 41, 0, 100, 0, 0, 0, 0, 0, 'Nerub''enkan - Cocoon (NE4)'),
(10437, 3, 0, '%s skitters across his web!', 41, 0, 100, 0, 0, 0, 0, 0, 'Nerub''enkan - Skitter (NE6)'),
(10437, 4, 0, 'Hatch, my children!', 14, 0, 100, 0, 0, 0, 0, 0, 'Nerub''enkan - Brood Call (NE7, heroic)'),
(10437, 5, 0, 'The web... is broken...', 14, 0, 100, 0, 0, 0, 0, 0, 'Nerub''enkan - Death');
