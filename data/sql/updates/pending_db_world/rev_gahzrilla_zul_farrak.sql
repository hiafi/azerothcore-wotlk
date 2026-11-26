-- Zul'Farrak build WP-D7: Hydromancer Velratha (7795) and Gahz'rilla (7273), the rows dbc-tools cannot declare
-- (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D7, s7 #21 A; build spec
-- docs/dungeons/zul-farrak-rework.md "Hydromancer Velratha and Gahz'rilla", Text). Their templates (the scripts,
-- AIName '', health, immunity 1972), the pool's stalker 301030 and the spells 214110-214129 are apps/dbc-tools
-- source/npcs/zul_farrak/gahzrilla.py; their SmartAI rows and the gong's go with rev_skeleton_zul_farrak.sql. Neither
-- has stock text (SELECT 2026-11-25). Their loot and Velratha's spawn position are untouched.

-- The yells (14) and the boss emote (41: center-screen and in the raid warning area). Gahz'rilla's groups 1 and 2 are
-- the hard mode packages' (D7Hb's Deluge, D7Ha's crew death).
DELETE FROM `creature_text` WHERE `CreatureID` = 7795 AND `GroupID` IN (0, 1);
DELETE FROM `creature_text` WHERE `CreatureID` = 7273 AND `GroupID` = 0;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(7795, 0, 0, 'The sacred pool is not for outlanders!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Hydromancer Velratha - Aggro'),
(7795, 1, 0, 'Rise, Gahz''rilla! The waters are yours!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Hydromancer Velratha - Strikes the gong (GZ10)'),
(7273, 0, 0, '%s''s scales crackle with building charge!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Gahz''rilla - Static Discharge (GZ3)');

-- Section 7 #21 A: Velratha stands at her spawn (her stock patrol 815700 circles the pool and would start the fight
-- with the gong 60 yd away). The path rows stay (unused).
UPDATE `creature` SET `MovementType` = 0, `wander_distance` = 0 WHERE `guid` = 81570 AND `id` = 7795;
UPDATE `creature_addon` SET `path_id` = 0 WHERE `guid` = 81570 AND `path_id` = 815700;
