-- Scarlet Monastery build WP-D5: Houndmaster Loksey (3974), the rows dbc-tools cannot declare
-- (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D5; build spec
-- docs/dungeons/scarlet-monastery-2-library.md "Houndmaster Loksey"). His template (boss_houndmaster_loksey_rework,
-- AIName '', 38k, immunity 1972, INSTANCE_BIND), Loksey's Tracking Hound 300908, the Kennel Pup 300909 and spells
-- 212540-212551 are apps/dbc-tools source/npcs/scarlet_monastery/loksey.py; his two SmartAI rows are dropped by
-- WP-S0's rev_skeleton_scarlet_monastery.sql. This rev inserts no spawn and no SmartAI row (rule 14: nothing for the
-- heroic spawn mask to miss).

-- The three stock Scarlet Tracking Hounds (4304) at his feet, guids 40089-40091 (LIB "Build spec": "Three, at the spots
-- of guids 40089 to 40091 (which go)"): the script summons three Loksey's Tracking Hounds on the same spots instead
-- (boss_houndmaster_loksey_rework.cpp, LokseyLogic.h kPackSpots). The other four 4304 spawns stay with the Beastmasters
-- (guids 40054, 40060, 40070, 40079). No creature_addon, formation, pool, linked respawn, game event, movement or
-- SmartAI row names them (read-only check 2026-11-20), so the creature rows are all there is.
DELETE FROM `creature` WHERE `id` = 4304 AND `guid` IN (40089, 40090, 40091);
DELETE FROM `creature_addon` WHERE `guid` IN (40089, 40090, 40091);

-- His texts (LIB "Text"): group 0 is the stock yell "Release the hounds!" (creature_text 3974 / 0, kept as is: the pull
-- and every Release). Groups 1-4 are new boss emotes (type 41, so they read on screen): the Mark, Heel and Fetch
-- whistles and his own frenzy. Map-wide (TextRange 3, as Kell's and Doan's): the Scent carrier 22 yd out or a ranged
-- player can stand past the 40 yd emote range when the whistle is the tell.
DELETE FROM `creature_text` WHERE `CreatureID` = 3974 AND `GroupID` BETWEEN 1 AND 4;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(3974, 1, 0, '%s whistles: Mark!', 41, 0, 100, 0, 0, 0, 0, 3, 'Houndmaster Loksey - Whistle: Mark (LK3)'),
(3974, 2, 0, '%s whistles: Heel!', 41, 0, 100, 0, 0, 0, 0, 3, 'Houndmaster Loksey - Whistle: Heel (LK4)'),
(3974, 3, 0, '%s works himself into a frenzy!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Houndmaster Loksey - Frenzy, no dog alive (LK4)'),
(3974, 4, 0, '%s whistles: Fetch!', 41, 0, 100, 0, 0, 0, 0, 3, 'Houndmaster Loksey - Whistle: Fetch (LK6, heroic)');
