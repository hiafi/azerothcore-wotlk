DROP TABLE IF EXISTS `dungeon_checkpoint_instance`;
CREATE TABLE `dungeon_checkpoint_instance` (
  `instance_id` INT UNSIGNED NOT NULL COMMENT 'instance.id this checkpoint progress belongs to',
  `map_id` MEDIUMINT UNSIGNED NOT NULL,
  `position_x` FLOAT NOT NULL,
  `position_y` FLOAT NOT NULL,
  `position_z` FLOAT NOT NULL,
  `orientation` FLOAT NOT NULL,
  `checkpoint_order` TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`instance_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
