-- Blackrock Depths build WP-D3: Houndmaster Grebmar (9319), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D3; build spec
-- docs/dungeons/blackrock-depths-1-detention-block.md S1 "Houndmaster Grebmar"). His template
-- (boss_houndmaster_grebmar_rework, AIName '', 95k, immunity 1972, INSTANCE_BIND), the Kennel Hound 300781 and spells
-- 210780-210796 are apps/dbc-tools source/npcs/blackrock_depths/grebmar.py; his three stock smart_scripts rows are
-- dropped by WP-S0's rev_blackrock_depths_skeleton.sql. This rev inserts no spawn and no SmartAI row (rule 14: nothing
-- for the heroic spawn mask to miss).

-- The five stock Bloodhounds (8921) within 7 yd of him (S1 Implementation): the script summons four Kennel Hounds at
-- their spots instead. The other Bloodhounds of the cavern stay trash. Their creature_addon rows go with them (no
-- formation, pool, game event or SmartAI rows name them, read-only check 2026-11-17).
DELETE FROM `creature` WHERE `id` = 8921 AND `guid` IN (46271, 46273, 46281, 46297, 46298);
DELETE FROM `creature_addon` WHERE `guid` IN (46271, 46273, 46281, 46297, 46298);

-- The three rim Bloodhounds (8921) standing on the Kennel Horn doors and the Fetch exit (R-1-A m3; orchestrator ruling
-- 2026-11-17, F-2: delete): 46301 (574.7, -196.6), 46302 (581.1, -190.5), 46607 (581.4, -175.4). Their creature_addon
-- rows go with them (aura 8279 only; no formation, pool, linked respawn, game event or SmartAI row names them,
-- read-only check 2026-11-17). The other rim Bloodhounds stay trash.
DELETE FROM `creature` WHERE `id` = 8921 AND `guid` IN (46301, 46302, 46607);
DELETE FROM `creature_addon` WHERE `guid` IN (46301, 46302, 46607);

-- His texts (S1 "Text"; he had none): the pull, the three commands named as he whistles, the 30% finale and the death
-- are yells (14); the horn is a boss emote (41) so it reads on screen.
DELETE FROM `creature_text` WHERE `CreatureID` = 9319 AND `GroupID` BETWEEN 0 AND 6;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9319, 0, 0, 'Escaped prisoners! My pups are hungry!', 14, 0, 100, 0, 0, 0, 0, 0, 'Houndmaster Grebmar - Pull'),
(9319, 1, 0, 'Sic ''em!', 14, 0, 100, 0, 0, 0, 0, 0, 'Houndmaster Grebmar - Whistle: Sic ''em (GR2, GR3)'),
(9319, 2, 0, 'Fetch!', 14, 0, 100, 0, 0, 0, 0, 0, 'Houndmaster Grebmar - Whistle: Fetch (GR2, GR5)'),
(9319, 3, 0, 'Heel!', 14, 0, 100, 0, 0, 0, 0, 0, 'Houndmaster Grebmar - Whistle: Heel (GR2, GR6)'),
(9319, 4, 0, 'Release the hounds! All of them!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Houndmaster Grebmar - Release the hounds (GR8, 30%)'),
(9319, 5, 0, '%s blows his kennel horn!', 41, 0, 100, 0, 0, 0, 0, 0, 'Houndmaster Grebmar - Kennel Horn (GR1)'),
(9319, 6, 0, 'Who... will feed... my pups...', 14, 0, 100, 0, 0, 0, 0, 0, 'Houndmaster Grebmar - Death');
