-- Custom: player-chosen shapeshift appearance (docs/bear-form-appearances.md).
-- One row per character per form; Bear Form's choice is stored under form 5 (FORM_BEAR) and also
-- covers Dire Bear Form. Read at login by src/server/scripts/Custom/custom_shapeshift_appearance.cpp.
CREATE TABLE IF NOT EXISTS `character_shapeshift_appearance` (
  `guid` int unsigned NOT NULL COMMENT 'characters.guid',
  `form` tinyint unsigned NOT NULL COMMENT 'ShapeshiftForm',
  `display_id` int unsigned NOT NULL COMMENT 'CreatureDisplayInfo.dbc ID',
  PRIMARY KEY (`guid`, `form`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Custom shapeshift appearances';
