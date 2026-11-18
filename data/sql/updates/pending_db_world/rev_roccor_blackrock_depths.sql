-- Blackrock Depths build WP-D2: Lord Roccor (9025), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D2; build spec
-- docs/dungeons/blackrock-depths-1-detention-block.md S1 362-410). His template (boss_lord_roccor_rework, AIName '',
-- health, DamageModifier, immunity 1972, INSTANCE_BIND, speed_walk 0.6), Loosed Earth 300780 and the spells
-- 210750-210763 are apps/dbc-tools source/npcs/blackrock_depths/roccor.py; the S0 rev drops his three SmartAI rows.

-- RO1 Restless March: his patrol 473040 (spawn 47304, creature_addon path_id 473040, MovementType 2) was a 728 yd
-- loop at 3.9 yd/s. It becomes the 61.8 yd stretch of road through his spawn, out and back at 1.5 yd/s
-- (RoccorLogic.h kRoadWest / kRoadEast, the velocity on each node so the heroic template's speed_walk does not
-- matter). In combat the script walks the same two points.
DELETE FROM `waypoint_data` WHERE `id` = 473040;
INSERT INTO `waypoint_data` (`id`, `point`, `position_x`, `position_y`, `position_z`, `orientation`, `velocity`,
    `delay`, `smoothTransition`, `move_type`, `action`, `action_chance`, `wpguid`) VALUES
(473040, 1, 580.0, -282.3, -80.9, NULL, 1.5, 0, 0, 0, 0, 100, 0),
(473040, 2, 637.0, -258.4, -82.7, NULL, 1.5, 0, 0, 0, 0, 100, 0);

-- His texts (S1 Build spec "Text"; he has none stock): boss emotes 41.
DELETE FROM `creature_text` WHERE `CreatureID` = 9025;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9025, 0, 0, 'The halls tremble beneath %s''s stride.', 41, 0, 100, 0, 0, 0, 0, 0, 'Lord Roccor - Pull (RO1)'),
(9025, 1, 0, '%s rears up and Rampages down the road!', 41, 0, 100, 0, 0, 0, 0, 0, 'Lord Roccor - Rampage (RO3)'),
(9025, 2, 0, 'The ground heaves around %s, and the stone stands up!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Lord Roccor - Loosed Earth (RO4)'),
(9025, 3, 0, '%s crumbles back into the mountain.', 41, 0, 100, 0, 0, 0, 0, 0, 'Lord Roccor - Death');
