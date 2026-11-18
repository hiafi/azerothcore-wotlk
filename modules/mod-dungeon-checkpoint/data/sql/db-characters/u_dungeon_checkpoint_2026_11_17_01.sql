-- Per-instance "reached only" checkpoint spots a member of the instance has been near (dungeon_checkpoint_location
-- .reach_radius). Keyed like the instance row: it belongs to the instance save and is pruned with it.
CREATE TABLE IF NOT EXISTS `dungeon_checkpoint_reached` (
  `instance_id` INT UNSIGNED NOT NULL COMMENT 'instance.id this belongs to',
  `map_id` MEDIUMINT UNSIGNED NOT NULL,
  `checkpoint_order` TINYINT UNSIGNED NOT NULL DEFAULT 0,
  `location_index` TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`instance_id`, `checkpoint_order`, `location_index`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
