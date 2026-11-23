-- Scarlet Monastery build WP-D4: Bloodmage Thalnos (4543), the rows dbc-tools cannot declare
-- (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D4; build spec
-- docs/dungeons/scarlet-monastery-1-graveyard.md "Bloodmage Thalnos", Text). His template
-- (boss_bloodmage_thalnos_rework, AIName '', health, DamageModifier 1.7, immunity 1972) and the spells
-- 212440-212459 are apps/dbc-tools source/npcs/scarlet_monastery/thalnos.py; his SmartAI rows 0-7 go with WP-S0's rev
-- (the script keeps the aggro and kill lines and Scorn's summon under game event 120 on normal).
-- His stock texts 0-2 (with their sounds) stay: line 1 now fires at his first empowered spell (normal and heroic) or
-- at the hard mode's 75% teleport (WP-D4H). Group 4 ("Yes... wake them all!") is WP-D4H's rev. His loot and spawn are
-- untouched.

-- The new boss emote (type 41: center-screen and in the raid warning area): TH1, each empowered cast.
DELETE FROM `creature_text` WHERE `CreatureID` = 4543 AND `GroupID` = 3;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(4543, 3, 0, '%s''s hands run red with blood!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Bloodmage Thalnos - Blood Ritual, an empowered cast (TH1)');
