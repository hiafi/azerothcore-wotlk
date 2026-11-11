DROP TABLE IF EXISTS `dungeon_checkpoint_location`;
CREATE TABLE `dungeon_checkpoint_location` (
  `map_id` MEDIUMINT UNSIGNED NOT NULL,
  `creature_entry` MEDIUMINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0 = entrance checkpoint, active as soon as the instance is created',
  `checkpoint_order` TINYINT UNSIGNED NOT NULL DEFAULT 0,
  `position_x` FLOAT NOT NULL,
  `position_y` FLOAT NOT NULL,
  `position_z` FLOAT NOT NULL,
  `orientation` FLOAT NOT NULL,
  `comment` VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`map_id`, `creature_entry`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Utgarde Keep (map 574, normal + heroic share the same map id and layout)
INSERT INTO `dungeon_checkpoint_location` (`map_id`, `creature_entry`, `checkpoint_order`, `position_x`, `position_y`, `position_z`, `orientation`, `comment`) VALUES
(574, 0,     0, 153.789,  -86.548,  12.551, 0.304,   'Utgarde Keep - entrance (areatrigger_teleport 4745)'),
(574, 23953, 1, 193.121,  197.492,  40.815, 0.174533,'Utgarde Keep - after Prince Keleseth (normal)'),
(574, 30748, 1, 193.121,  197.492,  40.815, 0.174533,'Utgarde Keep - after Prince Keleseth (heroic)'),
(574, 24200, 2, 109.516,  -33.658, 118.861, 4.86947, 'Utgarde Keep - after Skarvald/Dalronn (normal, Skarvald)'),
(574, 24201, 2, 109.516,  -33.658, 118.861, 4.86947, 'Utgarde Keep - after Skarvald/Dalronn (normal, Dalronn)'),
(574, 31679, 2, 109.516,  -33.658, 118.861, 4.86947, 'Utgarde Keep - after Skarvald/Dalronn (heroic, Skarvald)'),
(574, 31656, 2, 109.516,  -33.658, 118.861, 4.86947, 'Utgarde Keep - after Skarvald/Dalronn (heroic, Dalronn)'),
(574, 23954, 3, 242.677, -333.595,  180.56, 5.22671, 'Utgarde Keep - after Ingvar the Plunderer (normal)'),
(574, 31673, 3, 242.677, -333.595,  180.56, 5.22671, 'Utgarde Keep - after Ingvar the Plunderer (heroic)');
