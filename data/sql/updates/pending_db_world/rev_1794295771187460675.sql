-- Odo the Blindwatcher's Alarm Bells (301101, guids 3011010-3011012) moved to the playtest's points
-- (2026-11-09; ShadowfangKeepRework.h kBellSpots): 1 by Odo, 2 mid-room, 3 by the door.
UPDATE `gameobject` SET `position_x` = -247.4, `position_y` = 2153.0, `position_z` = 100.3, `Comment` = 'Shadowfang Keep: Alarm Bell 1 (Odo, by him)' WHERE `guid` = 3011010 AND `id` = 301101;
UPDATE `gameobject` SET `position_x` = -239.3, `position_y` = 2131.1, `position_z` = 100.0, `Comment` = 'Shadowfang Keep: Alarm Bell 2 (Odo, mid-room)' WHERE `guid` = 3011011 AND `id` = 301101;
UPDATE `gameobject` SET `position_x` = -251.4, `position_y` = 2117.9, `position_z` = 100.0, `Comment` = 'Shadowfang Keep: Alarm Bell 3 (Odo, by the door)' WHERE `guid` = 3011012 AND `id` = 301101;
