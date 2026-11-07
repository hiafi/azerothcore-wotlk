-- Deadmines Pilot, playtest 1 fixes (2026-11-06).
--
-- Captain Greenskin (spawn 79333) stands still: no waypoint patrol. The path rows (waypoint_data 793330) stay unused;
-- his formation (leader 79333, members 79334 and 79335, groupAI 512, no assist flags) stays: with a leader who never
-- moves the two pirates keep their own spawns and wander.
UPDATE `creature` SET `MovementType` = 0 WHERE `id` = 647 AND `guid` = 79333;
UPDATE `creature_addon` SET `path_id` = 0 WHERE `guid` = 79333;
-- VanCleef hard mode: the Powder Keg (gameobject 301000, guid 3010000, heroic only: spawnMask 2) moves to the user's
-- spot on the stern walkway (orientation 4.482139; rotation = its yaw quaternion).
UPDATE `gameobject` SET `position_x` = -48.148335, `position_y` = -812.0548, `position_z` = 42.69199,
    `orientation` = 4.482139, `rotation0` = 0, `rotation1` = 0, `rotation2` = -0.783652, `rotation3` = 0.6212001
    WHERE `id` = 301000 AND `guid` = 3010000;
