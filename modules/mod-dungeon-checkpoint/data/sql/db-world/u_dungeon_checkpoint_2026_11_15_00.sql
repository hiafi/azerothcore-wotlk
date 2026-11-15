-- Blackrock Spire: a second entrance checkpoint for the Upper Spire (Blackrock Spire build, user ruling 2026-11-15).
-- The map is one instance for both halves, so the instance entrance (location_index 0, the Lower Spire entrance,
-- areatrigger_teleport 1468) gets a second spot: a player who dies shares the instance's checkpoint order 0 and
-- respawns at the spot nearest their death. This one is the Upper Spire Finder start (lfg_dungeon_template 44,
-- dbc-tools source/world/lfg_classic_heroic.py): 19 yd short of the Dragonspire Hall trigger (areatrigger 2046,
-- radius 10), on standable navmesh. It stands 0.25 yd inside the rework instance's hall box (kDragonspireHall,
-- mod-dungeon-bosses BlackrockSpireRework.h kUbrsFinderStart), so an arrival or a respawn here starts the rune-room
-- self-start about 1 s later, by design (the packs are at rest). Keep the three copies equal: the DT test
-- test_blackrock_spire_kit checks them.
DELETE FROM `dungeon_checkpoint_location` WHERE `map_id` = 229 AND `creature_entry` = 0 AND `location_index` = 1;
INSERT INTO `dungeon_checkpoint_location` (`map_id`, `creature_entry`, `location_index`, `checkpoint_order`, `position_x`, `position_y`, `position_z`, `orientation`, `comment`) VALUES
(229, 0, 1, 0, 98.25, -300.75, 63.1, 4.94, 'Upper Blackrock Spire - Finder start (lfg_dungeon_template 44), short of areatrigger 2046');
