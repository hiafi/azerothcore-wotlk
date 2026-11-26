-- Zul'Farrak build WP-D1: Theka the Martyr (7272), the rows dbc-tools cannot declare
-- (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D1, s7 #21 A; build spec
-- docs/dungeons/zul-farrak-rework.md "Theka the Martyr", Text). His template (boss_theka_rework, AIName '', health,
-- DamageModifier 2.4, immunity 1972, flags), the two swarms 301005 / 301006 and the spells 213860-213874 are
-- apps/dbc-tools source/npcs/zul_farrak/theka.py; his SmartAI rows go with WP-S0's rev_skeleton_zul_farrak.sql. He has
-- no stock text (SELECT 2026-11-25). His loot and equipment (item 2559) are untouched.

-- Section 7 #21 A: he stands at his spawn (stock walks path 814630, a 114 yd loop through his own rise points). The
-- path's waypoint rows stay (nothing else uses them); his three walking escorts (81457, 81456, 45710) keep theirs and
-- are pre-cleared.
UPDATE `creature` SET `MovementType` = 0, `wander_distance` = 0 WHERE `guid` = 81463 AND `id` = 7272;
UPDATE `creature_addon` SET `path_id` = 0 WHERE `guid` = 81463 AND `path_id` = 814630;

-- The texts: the aggro and rising yells, the boss emotes (type 41: center-screen and in the raid warning area) of TK1
-- the swarm, TK2 the arrival and TK6 the hunt (the hunted player).
DELETE FROM `creature_text` WHERE `CreatureID` = 7272 AND `GroupID` BETWEEN 0 AND 4;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(7272, 0, 0, 'Who disturbs da Martyr''s tomb?', 14, 0, 100, 0, 0, 0, 0, 0,
    'Theka the Martyr - aggro'),
(7272, 1, 0, '%s cries out, and his persecutors stir in the sand!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Theka the Martyr - Persecutors'' Swarm (TK1)'),
(7272, 2, 0, 'The persecutors swarm over %s!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Theka the Martyr - the swarm reaches him (TK2)'),
(7272, 3, 0, 'Ya cannot kill a martyr twice!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Theka the Martyr - Martyr''s Rising (TK5)'),
(7272, 4, 0, 'A penitent swarm burrows toward $n!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Theka the Martyr - Penitent Hunt (TK6)');
