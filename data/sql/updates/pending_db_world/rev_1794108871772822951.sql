-- Deadmines: Cookie (645) no longer patrols. His waypoint path 793440 walked him off the ship to within ~27 yd of
-- Mr. Smite's room, so a Smite pull could add Cookie (bot test run tr-20261108-030549-1 wiped that way). He now stands
-- at his spawn on the ship.
UPDATE `creature` SET `MovementType` = 0, `wander_distance` = 0 WHERE `guid` = 79344 AND `id` = 645;
UPDATE `creature_addon` SET `path_id` = 0 WHERE `guid` = 79344;
