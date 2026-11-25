-- Ragefire Chasm build WP-D2: Jergosh the Invoker (11518), the rows dbc-tools cannot declare
-- (.agents/plans/ragefire-chasm-build/ragefire-chasm-build.HANDOFF.md s3.5 row D2; build spec
-- docs/dungeons/ragefire-chasm-rework.md "Jergosh the Invoker", Text). His template (boss_jergosh_rework, AIName '',
-- health, DamageModifier 1.95, immunity 1972), the Soul Wisp 300986 and the spells 213580-213589 are apps/dbc-tools
-- source/npcs/ragefire_chasm/jergosh.py; his SmartAI rows go with rev_skeleton_ragefire_chasm.sql. He has no stock
-- text (SELECT 2026-11-24). His loot, spawn and equipment are untouched.

-- The aggro yell (14) and the boss emotes (41: center-screen and in the raid warning area): JR2 Conflagrate, JR4 Drain
-- Soul and JR5 an eaten soul (both heroic).
DELETE FROM `creature_text` WHERE `CreatureID` = 11518 AND `GroupID` BETWEEN 0 AND 3;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(11518, 0, 0, 'The Searing Blade will purge you in fire!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Jergosh the Invoker - Aggro'),
(11518, 1, 0, '%s spreads his hands, and the flames on his victims flare!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Jergosh the Invoker - Conflagrate (JR2)'),
(11518, 2, 0, '%s begins to tear the soul from $n!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Jergosh the Invoker - Drain Soul (JR4, heroic)'),
(11518, 3, 0, 'The Hungerer feeds, and %s grows stronger!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Jergosh the Invoker - An eaten soul (JR5, heroic)');
