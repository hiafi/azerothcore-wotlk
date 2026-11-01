-- dungeon-prereqs S5 (druid): Remove Curse 2782 is retired for players (Nature's Cure, Magic + Poison, replaces it as
-- the druid dispel). Character data cleanup, run with the worldserver stopped.
-- removed spell and its action bar buttons
DELETE FROM `character_spell` WHERE `spell` = 2782;
DELETE FROM `character_action` WHERE `type` = 0 AND `action` = 2782;
