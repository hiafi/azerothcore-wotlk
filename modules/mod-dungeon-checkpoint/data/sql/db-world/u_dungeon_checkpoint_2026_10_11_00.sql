-- Let one checkpoint have several spots (e.g. one per wing entrance of a split dungeon like Scarlet Monastery):
-- rows sharing map_id + checkpoint_order are alternatives, and a player respawns at the one nearest their death.
ALTER TABLE `dungeon_checkpoint_location`
    ADD COLUMN `location_index` TINYINT UNSIGNED NOT NULL DEFAULT 0
        COMMENT 'Distinguishes several spots of one checkpoint' AFTER `creature_entry`,
    DROP PRIMARY KEY,
    ADD PRIMARY KEY (`map_id`, `creature_entry`, `location_index`);
