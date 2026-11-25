-- Ragefire Chasm build WP-D3: Bazzalan (11519), the rows dbc-tools cannot declare
-- (.agents/plans/ragefire-chasm-build/ragefire-chasm-build.HANDOFF.md s3.5 row D3; build spec
-- docs/dungeons/ragefire-chasm-rework.md "Bazzalan", Text). His template (boss_bazzalan_rework, AIName '', health,
-- DamageModifier 2.2, immunity 1972) and the spells 213610-213624 are apps/dbc-tools
-- source/npcs/ragefire_chasm/bazzalan.py; his SmartAI rows go with WP-S0's rev. He has no stock creature_text row
-- (SELECT 2026-11-24). His loot, spawn and equipment (the scimitar 2179) are untouched.

-- The aggro yell (type 14) and the boss emotes (type 41: center-screen and in the raid warning area): one per finisher
-- (BZ3-BZ6) and one per Shadowstep landing (BZ7, heroic).
DELETE FROM `creature_text` WHERE `CreatureID` = 11519 AND `GroupID` BETWEEN 0 AND 5;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(11519, 0, 0, 'Thrall''s pups come sniffing? The Blade cuts both ways!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Bazzalan - Aggro'),
(11519, 1, 0, '%s readies an Eviscerate!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Bazzalan - Eviscerate (BZ3)'),
(11519, 2, 0, '%s readies a Rupture on $n!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Bazzalan - Rupture (BZ4)'),
(11519, 3, 0, '%s readies a Fan of Knives!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Bazzalan - Fan of Knives (BZ5)'),
(11519, 4, 0, '%s readies an Envenom!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Bazzalan - Envenom (BZ6, heroic)'),
(11519, 5, 0, '%s vanishes and appears behind $n!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Bazzalan - Shadowstep (BZ7, heroic)');
