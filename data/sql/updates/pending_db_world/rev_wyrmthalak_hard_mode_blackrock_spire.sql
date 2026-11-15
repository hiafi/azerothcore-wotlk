-- Blackrock Spire build WP-B9: Overlord Wyrmthalak's hard mode, the war horn, the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.7, s3.5 row B9; build spec
-- docs/dungeons/blackrock-spire-rework.md SP 2436-2521 rows WT9-WT17). The hard mode's spells 210290-210306 (and their
-- spell_script_names / spell_proc rows) are apps/dbc-tools source/npcs/blackrock_spire/wyrmthalak_hard_mode.py; his
-- texts 7-9 (the horn, Caustic Roar, the spear) are B8's rev_wyrmthalak_blackrock_spire.sql.

-- The Bloodaxe War Horn: a goober (type 10, no lock, no quest, no auto close) bound to go_brs_war_horn, which lights
-- the instance's per-pull DATA_WAR_HORN (heroic, Wyrmthalak neither fighting nor dead) and keeps the object not
-- selectable while it cannot be blown. V-1's look: display 7352 (elventowerSilithusHorn) at size 0.12 (unconfirmed in
-- game; the alternative is 2371, MargolReaverHorn). Upsert: gameobject_template rows are never deleted.
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301255, 10, 7352, 'Bloodaxe War Horn', '', '', '', 0.12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, '', 'go_brs_war_horn', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`),
    `displayId` = VALUES(`displayId`), `name` = VALUES(`name`), `size` = VALUES(`size`), `Data0` = VALUES(`Data0`),
    `Data1` = VALUES(`Data1`), `Data2` = VALUES(`Data2`), `Data3` = VALUES(`Data3`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` = 301255;
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301255, 0, 0, 0, 0, 0, 0, 0, 0);

-- Its spawn: the ramp head on the ledge's south-west shoulder (handoff s3.8 NM 8, BlackrockSpireRework.h kWarHornSpot;
-- `.gps` check in the playtest), facing the ledge (o 0.58: toward Wyrmthalak at (-22.6, -486.2)). Heroic only
-- (spawnMask 2, the Stratholme hard mode objects' convention); guid = entry x 10 (the kit spawns' convention, free in
-- the live DB, read-only check 2026-11-15). Rotation = the orientation about z (rotation2 = sin(o/2),
-- rotation3 = cos(o/2)).
DELETE FROM `gameobject` WHERE `id` = 301255 AND `guid` = 3012550;
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`,
    `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`,
    `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3012550, 301255, 229, 0, 0, 2, 1, -52.5, -503.0, 89.1, 0.58, 0, 0, 0.285952, 0.958244, 7200, 255, 1, '', 0,
    'Blackrock Spire B9: Bloodaxe War Horn (Overlord Wyrmthalak''s hard mode, heroic only, before the pull)');
