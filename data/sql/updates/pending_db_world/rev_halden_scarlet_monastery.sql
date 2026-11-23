-- Scarlet Monastery build WP-D10: Drillmaster Corin Halden, the Master-at-Arms (300942), the rows dbc-tools cannot
-- declare (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D10, s7 #30 A; build spec
-- docs/dungeons/scarlet-monastery-3-armory.md "Drillmaster Corin Halden, the Master-at-Arms"). His template (level 37
-- warrior, 60k, immunity 1972, INSTANCE_BIND, display 2514; boss_drillmaster_corin_halden_rework once wave 2 binds),
-- the Drill Recruit 300943 and the spells 212950-212958 are apps/dbc-tools source/npcs/scarlet_monastery/halden.py.
-- He is a new creature, so there is no stock SmartAI to drop. The recruits are HIS summons (rebuilt in rank at every
-- reset, gone with his death): no recruit spawn here. His own spawn sets the heroic bit itself (spawnMask 3, handoff
-- s3.5 rule 14: the generated heroic rev sorts before rev_<boss>_*).

-- His texts (ARM "Text"; all new). The yells keep the default range; the boss emote (type 41) is map-wide (TextRange
-- 3). Groups 8 and 9 (the pairs) are heroic only; group 5 (the fumble) is normal only.
DELETE FROM `creature_text` WHERE `CreatureID` = 300942 AND `GroupID` BETWEEN 0 AND 9;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(300942, 0, 0, 'Fall in! Today''s lesson is live targets!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Drillmaster Corin Halden - aggro'),
(300942, 1, 0, 'Charge!', 14, 0, 100, 0, 0, 0, 0, 0, 'Drillmaster Corin Halden - Charge (MA1)'),
(300942, 2, 0, 'Spears, level!', 14, 0, 100, 0, 0, 0, 0, 0, 'Drillmaster Corin Halden - Spears (MA2)'),
(300942, 3, 0, 'Javelins!', 14, 0, 100, 0, 0, 0, 0, 0, 'Drillmaster Corin Halden - Javelins (MA3)'),
(300942, 4, 0, 'Close ranks!', 14, 0, 100, 0, 0, 0, 0, 0, 'Drillmaster Corin Halden - Close Ranks (MA4)'),
(300942, 5, 0, 'The recruits fumble their javelins!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Drillmaster Corin Halden - Javelins interrupted (MA3, normal)'),
(300942, 6, 0, 'Dismissed.', 14, 0, 100, 0, 0, 0, 0, 0, 'Drillmaster Corin Halden - kill'),
(300942, 7, 0, 'Hold... the line...', 14, 0, 100, 0, 0, 0, 0, 0, 'Drillmaster Corin Halden - death'),
(300942, 8, 0, 'Charge, then spears!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Drillmaster Corin Halden - Charge and Spears pair (MA0, heroic)'),
(300942, 9, 0, 'Javelins, then close ranks!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Drillmaster Corin Halden - Javelins and Close Ranks pair (MA0, heroic)');

-- Drillmaster Corin Halden's spawn, mid-way in the middle chamber of the upper hall's three rooms (NAVMESH's proposal
-- (1875, -400, 18.7), clearance 6.2; ScarletMonasteryRework.h kHaldenSpot), normal and heroic (spawnMask 3), facing
-- south toward the storeroom the group comes up from (his rank then stands north of him at x 1883, along the
-- chamber's 40 yd axis: s7 #30 A). Guid 3009420 = entry x 10, free on the live DB 2026-11-20. A boss's 86400 s respawn.
-- Literal values only.
DELETE FROM `creature` WHERE `id` = 300942 AND `guid` = 3009420;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(3009420, 300942, 189, 0, 0, 3, 1, 0, 1875.0, -400.0, 18.7, 3.14159, 86400, 0, 0, 0,
    'Scarlet Monastery D10: Drillmaster Corin Halden, the upper hall');
