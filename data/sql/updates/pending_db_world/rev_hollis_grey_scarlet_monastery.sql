-- Scarlet Monastery build WP-D7: Lector Hollis Grey <Keeper of the Index>, the Librarian (a new boss in the reading
-- hall; build spec docs/dungeons/scarlet-monastery-2-library.md LB1-LB9). His creature_template, his adds, the looks
-- and the spells are dbc-tools' (apps/dbc-tools/source/npcs/scarlet_monastery/hollis_grey.py); this rev adds what
-- dbc-tools cannot declare: his spawn and his texts.

-- His spawn: the pocket (254.8, -389.2) south of the hall's aisle (handoff section 7 #26 A: the doc's (265, -380) is a
-- 3 yd aisle between the tables), floor z of the hall's trash [db], facing north across the hall. Both difficulties
-- (spawnMask 1 | 2, rule 14: the generated heroic rev sorts before this one). Guid 5300913 in the fork's custom-spawn
-- block (5300000+; live MAX 5300776 on 2026-11-20). A day's respawn like the stock bosses (a reset respawns him at
-- once; the kill is saved by the instance).
DELETE FROM `creature` WHERE `guid` = 5300913 AND `id` = 300913;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `wander_distance`, `currentwaypoint`,
    `curhealth`, `curmana`, `MovementType`, `npcflag`, `unit_flags`, `dynamicflags`, `ScriptName`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(5300913, 300913, 189, 0, 0, 3, 1, 0, 254.8, -389.2, 20.49, 0, 86400, 0, 0, 0, 0, 0, 0, 0, 0, '', 0, 0,
    'Lector Hollis Grey - the reading hall pocket (Scarlet Monastery build D7)');

-- His texts (LIB "Text", all new; S0 range 0-7): the pull and the death are yells (14); the six book emotes (LB1, one
-- per story, said at the start of Open the Index) are boss emotes (41) so they read on screen, map-wide (TextRange 3,
-- as Kell's and Doan's: the call is the tell, and a ranged player can stand past the 40 yd emote range).
DELETE FROM `creature_text` WHERE `CreatureID` = 300913 AND `GroupID` BETWEEN 0 AND 7;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(300913, 0, 0, 'Heretics, in my reading hall? Then hear what you came to read!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Lector Hollis Grey - Aggro'),
(300913, 1, 0, '%s opens a forbidden book: War of the Spider!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Lector Hollis Grey - Open the Index: War of the Spider (LB1, LB2)'),
(300913, 2, 0, '%s opens a forbidden book: Archimonde''s Return!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Lector Hollis Grey - Open the Index: Archimonde''s Return (LB1, LB3)'),
(300913, 3, 0, '%s opens a forbidden book: Arathor and the Troll Wars!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Lector Hollis Grey - Open the Index: Arathor and the Troll Wars (LB1, LB4)'),
(300913, 4, 0, '%s opens a forbidden book: Mythology of the Titans!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Lector Hollis Grey - Open the Index: Mythology of the Titans (LB1, LB5)'),
(300913, 5, 0, '%s opens a forbidden book: The World Tree and the Emerald Dream!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Lector Hollis Grey - Open the Index: The World Tree and the Emerald Dream (LB1, LB6)'),
(300913, 6, 0, '%s opens a forbidden book: Aftermath of the Second War!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Lector Hollis Grey - Open the Index: Aftermath of the Second War (LB1, LB7)'),
(300913, 7, 0, 'Burn them... burn them all...', 14, 0, 100, 0, 0, 0, 0, 0, 'Lector Hollis Grey - Death');
