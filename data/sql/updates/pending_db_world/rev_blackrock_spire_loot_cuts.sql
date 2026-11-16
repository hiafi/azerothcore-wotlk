-- Blackrock Spire build WP-L-1: the loot cut dbc-tools cannot declare (apps/dbc-tools source/items/
-- blackrock_spire_loot.py declares the boss lists, tokens and the creature loot cuts).
--
-- The Roughshod Pike 12533 (SP ruling 39: Urok's summon needs no item, "the Roughshod Pike drops go") is not a creature
-- drop: it is the loot of the five Scarshield camp objects 175886 (gameobject_loot_template 13340, one row at 100%).
-- With the row gone the objects would be empty chests, so their five spawns go with it. The gameobject_template stays.
DELETE FROM `gameobject_loot_template` WHERE `Entry` = 13340 AND `Item` = 12533;

DELETE FROM `gameobject` WHERE `id` = 175886 AND `guid` IN (87942, 87943, 87944, 87945, 87946);
