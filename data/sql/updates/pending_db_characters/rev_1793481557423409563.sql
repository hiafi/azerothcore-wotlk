-- dungeon-prereqs S2: Priest Cure Disease 528 and Abolish Disease 552 are retired for players (Dispel Magic stays the
-- priest's Magic dispel). Character data cleanup, run with the worldserver stopped.
-- removed spells and their action bar buttons
DELETE FROM `character_spell` WHERE `spell` IN (528, 552);
DELETE FROM `character_action` WHERE `type` = 0 AND `action` IN (528, 552);
