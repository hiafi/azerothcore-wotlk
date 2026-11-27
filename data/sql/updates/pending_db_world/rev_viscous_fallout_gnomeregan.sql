-- Gnomeregan build WP-D2: Viscous Fallout (7079), the rows dbc-tools cannot declare
-- (.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.5 row D2; build spec
-- docs/dungeons/gnomeregan-rework.md "Viscous Fallout", Text). His template (boss_viscous_fallout_rework, AIName '',
-- health, DamageModifier 1.7, immunity 1972, flags), the pool stalker 301130 and the spells 214340-214356 are
-- apps/dbc-tools source/npcs/gnomeregan/viscous_fallout.py; his SmartAI rows, his move to area C and his dropped path
-- 70790 go with WP-S0's rev_skeleton_gnomeregan.sql. He has no stock text (SELECT 2026-11-26). His loot is L-1's.

-- His addon auras: the stock Immunity: Frost 7940 stays (the stock immunity set -232 carried Frost too; the new set
-- 1972 does not), the stock Corrosive Ooze proc 9460 goes (handoff s3.5 row D2: the glob is the script's now). The
-- spawn's own addon row (guid 30137, auras NULL) wins over the template's (Creature::GetCreatureAddon), so both carry
-- it; the boss script also re-adds 7940 at every reset. The heroic template's addon row (WP-H's 310567) is the write
-- run's copy of the replayed normal row (lib/dungeon_heroic.py SIDE_TABLES), so it reads '7940' from this rev: one
-- source, no join here.
UPDATE `creature_template_addon` SET `auras` = '7940' WHERE `entry` = 7079;
UPDATE `creature_addon` SET `auras` = '7940' WHERE `guid` = 30137;

-- The texts (SP "Text", groups 0-4 as SP prints them, rule 35): boss emotes (type 41: center-screen and in the raid
-- warning area). $n names the player.
DELETE FROM `creature_text` WHERE `CreatureID` = 7079 AND `GroupID` BETWEEN 0 AND 4;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(7079, 0, 0, '%s sloughs off a pool of fallout!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Viscous Fallout - Slough (VF4)'),
(7079, 1, 0, '$n is overcome by Radiation Sickness!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Viscous Fallout - Radiation Sickness (VF2)'),
(7079, 2, 0, '%s begins to decay. Stand close to shed your dose!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Viscous Fallout - Half-Life, heroic (VF9)'),
(7079, 3, 0, '$n is leaking fallout!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Viscous Fallout - Leaking, heroic (VF7)'),
(7079, 4, 0, '$n is melting down!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Viscous Fallout - Meltdown, heroic (VF8)');
