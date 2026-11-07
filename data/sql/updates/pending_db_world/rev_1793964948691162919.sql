-- Deadmines Pilot WP-B9: VanCleef's hard mode, Burn It Down (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md
-- s3.7; modules/mod-dungeon-bosses vancleef_hard_mode.cpp). The rows dbc-tools cannot declare.
--
-- The powder keg (gameobject_template 301000, go_dm_powder_keg, WP-K's rev): heroic only (spawnMask 2), on the main
-- deck against the sterncastle face (DeadminesRework.h kPowderKegSpot (-55, -820), kPowderKegZ 42.5; handoff s3.8 /
-- s7 #10: the fire front's first stripe starts here), facing the bow (orientation pi). The instance stores it in
-- ObjectData (DATA_POWDER_KEG_GUID). Guid 3010000: no gameobject spawn uses 2135532-5299999 (read-only check
-- 2026-11-06).
-- The mainmast (301002) has no spawn: the script summons it at 2:04. VanCleef's texts 7-9 are WP-B8's rev.
DELETE FROM `gameobject` WHERE `id` = 301000 AND `guid` = 3010000;
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`, `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`, `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3010000, 301000, 36, 0, 0, 2, 1, -55, -820, 42.5, 3.14159, 0, 0, 1, 0, 7200, 255, 1, '', 0, 'Deadmines Pilot: Powder Keg (VanCleef hard mode, heroic only)');
