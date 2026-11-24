-- Scarlet Monastery build WP-D1: Interrogator Vishas (3983), the rows dbc-tools cannot declare
-- (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D1; build spec
-- docs/dungeons/scarlet-monastery-1-graveyard.md "Interrogator Vishas", Text). His template
-- (boss_interrogator_vishas_rework, AIName '', health, DamageModifier 2.0, immunity 1972) and the spells
-- 212320-212327 are apps/dbc-tools source/npcs/scarlet_monastery/vishas.py; his SmartAI rows 0-5 go with WP-S0's rev.
-- His stock texts 0-3 (with their sounds) stay: lines 1 and 2 now fire at exactly 70 / 30% (the script). His loot,
-- spawn and equipment (the Hot Iron Poker the script equips at 70%) are untouched; Vorrel's line 0 is stock.

-- The new boss emotes (type 41: center-screen and in the raid warning area): VI1 Interrogation, the phase 2 iron and
-- VI4 Torment (heroic).
DELETE FROM `creature_text` WHERE `CreatureID` = 3983 AND `GroupID` BETWEEN 4 AND 6;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(3983, 4, 0, '%s demands a confession from $n!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Interrogator Vishas - Interrogation (VI1)'),
(3983, 5, 0, '%s takes a branding iron from the coals.', 41, 0, 100, 0, 0, 0, 0, 0,
    'Interrogator Vishas - Phase 2, Hot Irons'),
(3983, 6, 0, '%s turns his torments on $n!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Interrogator Vishas - Torment (VI4, heroic)');
