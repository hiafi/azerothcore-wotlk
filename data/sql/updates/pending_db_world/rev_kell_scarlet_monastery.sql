-- Scarlet Monastery build WP-D6: Ambrose Kell, the Antiquarian (300910), the rows dbc-tools cannot declare
-- (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D6, s7 #25 A; build spec
-- docs/dungeons/scarlet-monastery-2-library.md "Ambrose Kell, the Antiquarian"). His template
-- (boss_ambrose_kell_rework, AIName '', level 34 mage, 44k, immunity 1972, INSTANCE_BIND, display 2524), the relic
-- trigger 300911, the Gallery Skeleton 300912 and the spells 212570-212587 are apps/dbc-tools
-- source/npcs/scarlet_monastery/kell.py. He is a new creature, so there is no stock SmartAI to drop. The six cases (a
-- pedestal 301315 and a relic 301316-301318 each) are objects HE summons at his reset (no gameobject spawn: a woken
-- relic is deleted at the shatter, a wipe rebuilds all six, his death takes them away), so this rev inserts no object
-- spawn. His own spawn sets the heroic bit itself (spawnMask 3, handoff s3.5 rule 14: the generated heroic rev sorts
-- before rev_<boss>_*).

-- His texts (LIB "Text"; all new). The yells keep the default range; the boss emotes (type 41) are map-wide (TextRange
-- 3: an emote's own range is 25 yd and the hall is 66 yd long). Group 4 (the Trophy Power yell) and group 5 (the
-- Torrent) are heroic only.
DELETE FROM `creature_text` WHERE `CreatureID` = 300910 AND `GroupID` BETWEEN 0 AND 6;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(300910, 0, 0, 'Hands off the collection!', 14, 0, 100, 0, 0, 0, 0, 0, 'Ambrose Kell - aggro'),
(300910, 1, 0, '%s unseals the Plague Cask!', 41, 0, 100, 0, 0, 0, 0, 3, 'Ambrose Kell - Unseal (AN1, cask)'),
(300910, 2, 0, '%s unseals the Kirin Tor Staff!', 41, 0, 100, 0, 0, 0, 0, 3, 'Ambrose Kell - Unseal (AN1, staff)'),
(300910, 3, 0, '%s unseals the Necromancer''s Skull!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Ambrose Kell - Unseal (AN1, skull)'),
(300910, 4, 0, 'Yes... I hear it now. Its power is mine!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Ambrose Kell - Trophy Power (AN5, heroic)'),
(300910, 5, 0, '%s begins to channel the staff''s power!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Ambrose Kell - Arcane Torrent (AN5b, heroic)'),
(300910, 6, 0, 'The collection... must be... preserved...', 14, 0, 100, 0, 0, 0, 0, 0, 'Ambrose Kell - death');

-- The case objects (display ids: VR; one C++ constant each, KellLogic.h kPedestalDisplay / kCaskDisplay / kStaffDisplay
-- / kSkullDisplay, re-applied at the summon and pinned equal by lib/test_scarlet_monastery_kell.py). GENERIC (type 5:
-- no lock, no key item, no click) and not selectable (addon flags 16): scenery the boss summons and deletes.
-- 301315 BattlemasterPedestal (GODI 7695, 1.9 x 1.9 x 1.2 yd; NEVER the Karazhan Pedestal 7273, 5.2 yd tall),
-- 301316 Barrel02 (288), 301317 BrambleStaff (1708; the alternate is HumanStaff02 2455), 301318
-- BattleGladeSkullHumanDark (217; the alternate is BlastedLandsSkull02 226).
-- Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301315, 5, 7695, 'Relic Pedestal', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, '', '', 0),
(301316, 5, 288, 'Plague Cask', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, '', '', 0),
(301317, 5, 1708, 'Kirin Tor Staff', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, '', '', 0),
(301318, 5, 217, 'Necromancer''s Skull', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, '', '', 0)
ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`), `name` = VALUES(`name`),
    `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` BETWEEN 301315 AND 301318;
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301315, 0, 16, 0, 0, 0, 0, 0, 0),
(301316, 0, 16, 0, 0, 0, 0, 0, 0),
(301317, 0, 16, 0, 0, 0, 0, 0, 0),
(301318, 0, 16, 0, 0, 0, 0, 0, 0);

-- Ambrose Kell's spawn, mid-aisle of the long hall (section 3.8, NAVMESH: clearance 9.5, floor z 18.9), normal and
-- heroic (spawnMask 3). He faces +y (west, the side the corridor from the kennel hall enters by: unconfirmed in game).
-- Guid 3009100 = entry x 10 (the hand-SQL convention of the Blackrock Depths rev), free on the live DB 2026-11-20.
-- A boss's 86400 s respawn, as Azshir's after S0. Literal values only.
DELETE FROM `creature` WHERE `id` = 300910 AND `guid` = 3009100;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(3009100, 300910, 189, 0, 0, 3, 1, 0, 242.8, -329.2, 18.9, 1.5708, 86400, 0, 0, 0,
    'Scarlet Monastery D6: Ambrose Kell, the long hall');
