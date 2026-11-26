-- Gnomeregan build WP-S0, the skeleton (.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.2 items 3 and 8,
-- s7 #15 A, #16 B, #18 A, #19 A, #20 A, #22 A, #23 A, #34 A, #38 m A, s10 the Pummeler window). The stock instance is
-- replaced at load by modules/mod-dungeon-bosses src/Gnomeregan/instance_gnomeregan_rework.cpp (same script name); the
-- stock scripts in src/server/scripts/EasternKingdoms/Gnomeregan/ stay registered (npc_kernobee keeps working).
-- Spawn guids from 3011050 (creatures) and 3013800 (game objects), checked free 2026-11-26.

-- The stock SmartAI of every unit the rework scripts, so no boss WP deletes them again: Viscous Fallout 7079,
-- Electrocutioner 6000 6235, Crowd Pummeler 9-60 6229, Mekgineer Thermaplugg 7800 (s3.2 item 8). Their AIName '' comes
-- with the dbc-tools rows (boss_columns, next to the ScriptName: one owner per column). None has an action list
-- (source type 9) or a SmartAI condition (SELECT 2026-11-26). The Walking Bomb 7915's rows stay (it is never summoned
-- again: the faces' rows below were its only summoner).
DELETE FROM `smart_scripts` WHERE `source_type` = 0 AND `entryorguid` IN (7079, 6235, 6229, 7800);

-- The six Gnome Faces 142208-142213 (five rows each: open on spell 11518, shut on data 1, the bomb chute) and the six
-- Buttons 142214-142219 (one row each: set data 1 on their face), with the faces' phase conditions (source type 22,
-- group 5, six rows). D6 drives the faces by script; the Buttons become unclickable scenery (s7 #38 m A: not
-- selectable, GO_FLAG_NOT_SELECTABLE 0x10; their addon rows exist with flags 0). Spell 11518's six target conditions
-- (source type 13) and its spell_linked_spell row stay, unused (handoff s6).
DELETE FROM `smart_scripts` WHERE `source_type` = 1 AND `entryorguid` BETWEEN 142208 AND 142219;
DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 22 AND `SourceId` = 1
    AND `SourceEntry` BETWEEN 142208 AND 142219;
UPDATE `gameobject_template` SET `AIName` = '' WHERE `entry` BETWEEN 142208 AND 142219;
UPDATE `gameobject_template_addon` SET `flags` = `flags` | 16 WHERE `entry` BETWEEN 142214 AND 142219;

-- Blastmaster Emi Shortfuse's event is cut (ruling 2, s7 #18 A): her spawn (guid 30136, its addon row), her 66
-- SmartAI rows, her 21 summon group rows (groups 1 to 4: the Ambushers, Chomper, Grubbis) and her 15 waypoints (path
-- 7998). Her template, texts and gossip stay with no spawn; the two Cave Ins 146085 / 146086 stay shut as scenery.
DELETE FROM `creature_addon` WHERE `guid` = 30136;
DELETE FROM `creature` WHERE `id` = 7998 AND `guid` = 30136;
DELETE FROM `smart_scripts` WHERE `source_type` = 0 AND `entryorguid` = 7998;
DELETE FROM `creature_summon_groups` WHERE `summonerId` = 7998 AND `summonerType` = 0;
DELETE FROM `waypoints` WHERE `entry` = 7998;

-- The Alert hall's two packs (ruling 28, s7 #22 A; FACTS-STOCK 6.1): pack A 33423, 33426, 33427, 33428 (Leprous
-- Assistants), 33429 (Mechanized Sentry), 33444 (Machinesmith), 30390 (Mechano-Frostwalker); pack B 33438, 33439,
-- 33440, 33441 (Assistants), 33442, 33488 (Machinesmiths), 30304 (Mechano-Frostwalker); and the lone Machinesmith 30205
-- whose path 302050 crosses the boss spot. No formation, linked respawn, pool or game event names them (SELECT
-- 2026-11-26). The far pack C stays.
DELETE FROM `creature_addon` WHERE `guid` IN (33423, 33426, 33427, 33428, 33429, 33444, 30390, 33438, 33439, 33440,
    33441, 33442, 33488, 30304, 30205);
DELETE FROM `creature` WHERE `id` = 7603 AND `guid` IN (33423, 33426, 33427, 33428, 33438, 33439, 33440, 33441);
DELETE FROM `creature` WHERE `id` = 6233 AND `guid` = 33429;
DELETE FROM `creature` WHERE `id` = 6224 AND `guid` IN (33444, 33442, 33488, 30205);
DELETE FROM `creature` WHERE `id` = 6227 AND `guid` IN (30390, 30304);
DELETE FROM `waypoint_data` WHERE `id` = 302050;

-- The three patrols through Crowd Pummeler's pocket (s7 #23 A) stand still at their own spawns outside the pocket:
-- the stock Mobile Alert System 30141 (path 301410), Mechano-Frostwalker 30305 (path 303050), Mechano-Flamewalker
-- 30391 (path 303910). Their waypoint rows stay unused (reversible). The three units under the window stay.
UPDATE `creature_addon` SET `path_id` = 0 WHERE `guid` IN (30141, 30305, 30391);
UPDATE `creature` SET `MovementType` = 0, `wander_distance` = 0 WHERE `id` = 7849 AND `guid` = 30141;
UPDATE `creature` SET `MovementType` = 0, `wander_distance` = 0 WHERE `id` = 6227 AND `guid` = 30305;
UPDATE `creature` SET `MovementType` = 0, `wander_distance` = 0 WHERE `id` = 6226 AND `guid` = 30391;

-- Viscous Fallout stands at area C, the far end of his own patrol (s7 #19 A, ruling 14): (-391, 132), mesh floor -209.0
-- (DB z one baseline under), facing the cave's mouth; his path 70790 goes. The three mobs within 30 yd of C stay (the
-- bots pre-clear them, DC).
UPDATE `creature_addon` SET `path_id` = 0 WHERE `guid` = 30137;
UPDATE `creature` SET `position_x` = -391, `position_y` = 132, `position_z` = -209.1, `orientation` = 3.95,
    `MovementType` = 0, `wander_distance` = 0 WHERE `id` = 7079 AND `guid` = 30137;
DELETE FROM `waypoint_data` WHERE `id` = 70790;

-- Electrocutioner 6000 no longer wanders (s7 #20 A): he is pulled at his spawn, 2.3 yd from the platform's center.
UPDATE `creature` SET `MovementType` = 0, `wander_distance` = 0 WHERE `id` = 6235 AND `guid` = 30133;

-- Crowd Pummeler 9-60 floats in the green glass window (s10, the designer's in-game spot), about 4.8 yd under the
-- pocket floor; boss_crowd_pummeler_rework sets gravity off, the root and the reach at Reset. The movement row
-- (Flight 1 = gravity off, Rooted 1) covers the gap before the first Reset, so the body never drops at spawn
-- (FACTS-FRAMEWORK A.4 #3); his heroic copy (WP-H's entry, set by the write run's rev, which sorts before this file)
-- gets the same row.
UPDATE `creature` SET `position_x` = -883.5655, `position_y` = 363.25467, `position_z` = -277.38113,
    `orientation` = 2.9751785 WHERE `id` = 6229 AND `guid` = 30121;
DELETE FROM `creature_template_movement` WHERE `CreatureId` = 6229;
INSERT INTO `creature_template_movement` (`CreatureId`, `Ground`, `Swim`, `Flight`, `Rooted`) VALUES (6229, 1, 1, 1, 1);
SET @PUMMELER_HEROIC := (SELECT `difficulty_entry_1` FROM `creature_template` WHERE `entry` = 6229);
DELETE FROM `creature_template_movement` WHERE `CreatureId` = @PUMMELER_HEROIC AND @PUMMELER_HEROIC <> 0;
INSERT INTO `creature_template_movement` (`CreatureId`, `Ground`, `Swim`, `Flight`, `Rooted`)
    SELECT `difficulty_entry_1`, 1, 1, 1, 1 FROM `creature_template` WHERE `entry` = 6229 AND `difficulty_entry_1` <> 0;

-- The new bosses' spawns (normal and heroic, spawnMask 3; s3.5 rule 21): Techbot 301105 in his dish (ruling 61) and
-- the Mobile Alert System 301110 in the hall (ruling 66). Their templates are S0's stub rows in apps/dbc-tools
-- source/npcs/gnomeregan/techbot.py and mobile_alert_system.py (D1's and D4's now).
DELETE FROM `creature` WHERE `id` = 301105 AND `guid` = 3011050;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(3011050, 301105, 90, 0, 0, 3, 1, 0, -519.92, -107.67, -155.87, 2.01, 86400, 0, 0, 0,
    'Gnomeregan build: Techbot (ruling 61)');
DELETE FROM `creature` WHERE `id` = 301110 AND `guid` = 3011100;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(3011100, 301110, 90, 0, 0, 3, 1, 0, -756.67, 224.55, -273.08, 3.82, 86400, 0, 0, 0,
    'Gnomeregan build: the Mobile Alert System (ruling 66)');

-- Matrix Punchograph 3005-A inside (ruling 62, s7 #34 A): a copy of the stock map 0 object (entry 142345, its gossip
-- and spell chain unchanged), 3.4 yd from the designer's spot, with 3.5 yd of floor all round; normal and heroic (the
-- hard mode's card chain). Respawn 180 s as the stock copies. Rotation from the orientation (z axis).
DELETE FROM `gameobject` WHERE `id` = 142345 AND `guid` = 3013800;
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`,
    `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`,
    `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3013800, 142345, 90, 0, 0, 3, 1, -502.5, 67.2, -154.8, 5.70, 0, 0, -0.287478, 0.957787, 180, 100, 1, '', 0,
    'Gnomeregan build: Matrix Punchograph 3005-A copy (ruling 62)');

-- The Clearance Console (ruling 63, s7 #32 A) on Thermaplugg's south entrance, facing the room's center; heroic only
-- (spawnMask 2: the hard mode is heroic only). Its template (301382), gossip and texts are D6Ha's rev.
DELETE FROM `gameobject` WHERE `id` = 301382 AND `guid` = 3013820;
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`,
    `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`,
    `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3013820, 301382, 90, 0, 0, 2, 1, -580.0, 681.49, -327.08, 6.06, 0, 0, -0.111361, 0.99378, 300, 100, 1, '', 0,
    'Gnomeregan build: the Clearance Console (ruling 63)');

-- The Workshop Door 90858 (s7 #15 A, #16 B): keyless (GO_FLAG_LOCKED 0x2 cleared, NODESPAWN 0x20 kept; lock 92 goes
-- too: the 3.3.5 client enforces a door's lock from the query data even without the flag, the Scarlet Monastery
-- precedent; one spawn, on map 90). go_gnomer_workshop_door (instance_gnomeregan_rework.cpp) reports a player's open;
-- the instance keeps it sealed and not selectable until Electrocutioner is DONE, then unlocked, and opens it when the
-- Alert System is DONE. The Workshop Key 6893 still drops (ruling 58).
UPDATE `gameobject_template_addon` SET `flags` = `flags` & ~2 WHERE `entry` = 90858;
UPDATE `gameobject_template` SET `Data1` = 0, `ScriptName` = 'go_gnomer_workshop_door' WHERE `entry` = 90858;
