-- Ragefire Chasm build WP-D1: Oggleflint (11517), the rows dbc-tools cannot declare
-- (.agents/plans/ragefire-chasm-build/ragefire-chasm-build.HANDOFF.md s3.5 row D1; build spec
-- docs/dungeons/ragefire-chasm-rework.md "Oggleflint", Text). His template (boss_oggleflint_rework, AIName '', health,
-- DamageModifier 2.2, immunity 1972, flags), the Borer 300985 and the spells 213550-213557 are apps/dbc-tools
-- source/npcs/ragefire_chasm/oggleflint.py; his SmartAI row goes with WP-S0's rev_skeleton_ragefire_chasm.sql. He has
-- no stock text (SELECT 2026-11-24). His loot, spawn and equipment (item 3350) are untouched.

-- The boss emotes (type 41: center-screen and in the raid warning area): OG1 Borer Hunt (the hunted player), OG3 Club
-- Swing's wind-up and OG4 the Beating (heroic, the beaten player).
DELETE FROM `creature_text` WHERE `CreatureID` = 11517 AND `GroupID` BETWEEN 0 AND 2;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(11517, 0, 0, '%s bellows, and the ground churns toward $n!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Oggleflint - Borer Hunt (OG1)'),
(11517, 1, 0, '%s raises his club high!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Oggleflint - Club Swing (OG3)'),
(11517, 2, 0, '%s glares at $n and hefts his club!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Oggleflint - The Beating (OG4, heroic)');
