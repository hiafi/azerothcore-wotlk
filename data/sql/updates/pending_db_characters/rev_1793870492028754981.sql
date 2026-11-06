-- Remove mod-mythic-plus entirely (dungeon difficulties E0, user decision 2026-11-05): drop its 4 character tables
-- (all empty). Item 70001 "Mythic Plus Keystone" is held by no character (item_instance count 0), so no item rows
-- are touched here.
DROP TABLE IF EXISTS `mythic_plus_char_level`;
DROP TABLE IF EXISTS `mythic_plus_dungeon`;
DROP TABLE IF EXISTS `mythic_plus_dungeon_snapshot`;
DROP TABLE IF EXISTS `mythic_plus_keystone_timer`;
