-- Remove mod-mythic-plus entirely (dungeon difficulties E0, user decision 2026-11-05): its 7 world tables, its 3
-- commands, its two creature templates (200005 "Mythic Plus", 200006 "Lightning"; no spawns, loot, vendor, quest or
-- script references) and item 70001 "Mythic Plus Keystone" (0 held, no loot/vendor/quest references).
-- The module directory leaves modules/ at the same deploy, so nothing re-creates these.
DROP TABLE IF EXISTS `mythic_plus_affix`;
DROP TABLE IF EXISTS `mythic_plus_capable_dungeon`;
DROP TABLE IF EXISTS `mythic_plus_ignore_multiply_affix`;
DROP TABLE IF EXISTS `mythic_plus_level`;
DROP TABLE IF EXISTS `mythic_plus_level_rewards`;
DROP TABLE IF EXISTS `mythic_plus_map_scale`;
DROP TABLE IF EXISTS `mythic_plus_spell_override`;

DELETE FROM `command` WHERE `name` IN ('mythic', 'mythic info', 'mythic reload');

DELETE FROM `creature_template_model` WHERE `CreatureID` IN (200005, 200006);
DELETE FROM `creature_template` WHERE `entry` IN (200005, 200006);

DELETE FROM `item_dbc` WHERE `ID` = 70001;
DELETE FROM `item_template` WHERE `entry` = 70001;
