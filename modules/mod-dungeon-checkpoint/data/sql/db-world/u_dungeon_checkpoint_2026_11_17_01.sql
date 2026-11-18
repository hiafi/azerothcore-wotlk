-- "Reached only" checkpoint spots (user ruling 2026-11-17, Blackrock Depths build). A row with reach_radius > 0 is a
-- respawn candidate only once a living member of the instance has come within that many yards (3D) of it; 0, the
-- default, keeps every existing row exactly as it was. The reached set is per instance (characters DB table
-- dungeon_checkpoint_reached). Without this, the three Blackrock Depths Dungeon Finder starts added by
-- u_dungeon_checkpoint_2026_11_17_00.sql pulled a wipe in section 1 to S2a and a section 2 wipe to S4b by nearest
-- distance. A group the Finder teleports to a start is within the radius at once, so its own start works from the
-- first second. 25 yd keeps every start clear of the nearest boss (Ribbly Screwspigot is 35 yd from S4b).
-- Re-runnable (R-1-FW MAJ-1): the live worldserver applies module SQL itself at boot (Updates.EnableDatabases), so a
-- file applied by hand and then again by the updater must not abort the boot on "Duplicate column name". The column is
-- added only when information_schema does not list it yet (the upstream pattern of archive/db_world/2025_12_29_12.sql;
-- MySQL 8.4 has no ADD COLUMN IF NOT EXISTS).
DROP PROCEDURE IF EXISTS `dc_add_reach_radius`;
DELIMITER //
CREATE PROCEDURE `dc_add_reach_radius`()
BEGIN
IF NOT EXISTS (SELECT 1 FROM `information_schema`.`COLUMNS` WHERE `TABLE_SCHEMA` = DATABASE()
    AND `TABLE_NAME` = 'dungeon_checkpoint_location' AND `COLUMN_NAME` = 'reach_radius') THEN
    ALTER TABLE `dungeon_checkpoint_location` ADD COLUMN `reach_radius` FLOAT NOT NULL DEFAULT 0
        COMMENT '0 = always a respawn candidate, >0 = only once an instance member has been within this many yards'
        AFTER `orientation`;
END IF;
END //
DELIMITER ;
CALL `dc_add_reach_radius`();
DROP PROCEDURE `dc_add_reach_radius`;

UPDATE `dungeon_checkpoint_location` SET `reach_radius` = 25
    WHERE `map_id` = 230 AND `creature_entry` = 0 AND `location_index` IN (1, 2, 3);

-- Upper Blackrock Spire's Finder start (u_dungeon_checkpoint_2026_11_15_00.sql) gets the same rule (user 2026-11-17):
-- a Lower Spire wipe no longer respawns the group at the Upper Spire start until someone has been there.
UPDATE `dungeon_checkpoint_location` SET `reach_radius` = 25
    WHERE `map_id` = 229 AND `creature_entry` = 0 AND `location_index` = 1;
