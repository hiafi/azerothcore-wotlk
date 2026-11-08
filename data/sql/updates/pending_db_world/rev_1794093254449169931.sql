-- Shadowfang Keep build WP-S5: Odo the Blindwatcher (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md
-- s3.5 rows OD, s3.6 row S5, s7 #24; modules/mod-dungeon-bosses boss_odo_the_blindwatcher_rework.cpp). The rows
-- dbc-tools cannot declare.

-- Odo's stock SmartAI goes: Call for Help (on aggro, 40 yd) is removed by the build spec; Howling Rage 7481 / 7483 /
-- 7484 at 70 / 50 / 30% is kept in C++ (apps/dbc-tools odo_the_blindwatcher.py sets AIName '' and the ScriptName).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 4279 AND `source_type` = 0;

-- Odo's texts (SK "Text"; he has no stock lines). Mechanic emotes are type 41 (raid boss emote, center screen).
DELETE FROM `creature_text` WHERE `CreatureID` = 4279;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(4279, 0, 0, '%s sniffs the air... and turns toward $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Odo the Blindwatcher - The Hunt'),
(4279, 1, 0, '%s whirls toward the ringing bell!', 41, 0, 100, 0, 0, 0, 0, 0, 'Odo the Blindwatcher - Bell landing'),
(4279, 2, 0, '%s''s frenzy grows!', 41, 0, 100, 0, 0, 0, 0, 0, 'Odo the Blindwatcher - Blood Frenzy (heroic)');

-- The three Alarm Bells (gameobject_template 301101, go_sfk_alarm_bell, WP-K's rev) in Odo's room, at the navmesh
-- report's points (handoff s7 #24; ShadowfangKeepRework.h kBellSpots): 1 by Odo at the SSW wall, 2 mid-room, 3 in the
-- far ESE alcove, at least 19 yd apart. Normal and heroic (spawnMask 3), along the room's long axis (orientation
-- 1.195). Guids 3011010-3011012 (gameobject id x 10, the Deadmines powder keg's convention; none used, read-only check
-- 2026-11-07). The bell model's height over its spot is checked in game (WP-P, .gps).
DELETE FROM `gameobject` WHERE `id` = 301101 AND `guid` BETWEEN 3011010 AND 3011012;
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`, `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`, `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3011010, 301101, 33, 0, 0, 3, 1, -248.8, 2148.2, 100.7, 1.195, 0, 0, 0.562577, 0.826745, 7200, 255, 1, '', 0, 'Shadowfang Keep: Alarm Bell 1 (Odo, by him)'),
(3011011, 301101, 33, 0, 0, 3, 1, -245.8, 2129.2, 101.3, 1.195, 0, 0, 0.562577, 0.826745, 7200, 255, 1, '', 0, 'Shadowfang Keep: Alarm Bell 2 (Odo, mid-room)'),
(3011012, 301101, 33, 0, 0, 3, 1, -260.8, 2117.2, 101.1, 1.195, 0, 0, 0.562577, 0.826745, 7200, 255, 1, '', 0, 'Shadowfang Keep: Alarm Bell 3 (Odo, far alcove)');
