-- Scarlet Monastery build WP-D4H: Bloodmage Thalnos's hard mode, the Desecration (heroic only), the rows dbc-tools
-- cannot declare (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.7 row D4H, s7 #18 A;
-- build spec docs/dungeons/scarlet-monastery-1-graveyard.md "Hard mode" and "Build spec", Text;
-- modules/mod-dungeon-bosses src/ScarletMonastery/thalnos_hard_mode.cpp). The risen 300903-300906, the banner 300907
-- and the spells 212480-212496 are apps/dbc-tools source/npcs/scarlet_monastery/thalnos_hard_mode.py.

-- The texts (GY "Text"): Thalnos's group 4 (0-2 stock, 3 WP-D4's rev), the risen's group 0. Thalnos yells from the
-- crypt when the stones are answered on the lawn above (a yell's default range, 70-130 yd). The risen's boss emotes
-- (type 41) are map-wide (TextRange 3: an emote's own range is 25 yd and the lawn fight is 40 yd across).
DELETE FROM `creature_text` WHERE `CreatureID` = 4543 AND `GroupID` = 4;
DELETE FROM `creature_text` WHERE `CreatureID` IN (300903, 300906) AND `GroupID` = 0;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(4543, 4, 0, 'Yes... wake them all!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Bloodmage Thalnos - the Desecration answered (D4H)'),
(300903, 0, 0, '%s plants the banner of the Crusade!', 41, 0, 100, 0, 0, 0, 0, 3,
    'High Commander Galvar Pureblood (risen) - Rallying Banner (RH1)'),
(300906, 0, 0, '%s begins to spin!', 41, 0, 100, 0, 0, 0, 0, 3,
    'High Commander Goodchilde (risen) - Whirlwind wind-up (RH6)');

-- The objects (ids.yaml reservation `scarlet_monastery` 301310-301339; ScarletMonasteryRework.h SmGameObjects). Goobers
-- (type 10) whose script owns the click (GameObjectAI::GossipHello), so the stock goober use never runs.
-- 301310-301313 the four gravestones (go_sm_desecration_stone; Galvar, Fairbell, Voss, Goodchilde by entry):
--        TombStone02 (GODI 499, from A Conspicuous Gravestone 148504, VR GODI_GRAVESTONE). The gossip shows the
--        epitaph and, while a touch is allowed, "Disturb the Grave." (a 2 s cast of the player's, 212487).
-- 301314 the blood rite (go_sm_blood_rite): WantedPosterScroll01 (GODI 15, VR GODI_BLOOD_RITE; it hangs on a wall),
--        readable by gossip.
-- Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301310, 10, 499, 'Weathered Gravestone', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, '', 'go_sm_desecration_stone', 0),
(301311, 10, 499, 'Weathered Gravestone', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, '', 'go_sm_desecration_stone', 0),
(301312, 10, 499, 'Weathered Gravestone', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, '', 'go_sm_desecration_stone', 0),
(301313, 10, 499, 'Weathered Gravestone', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, '', 'go_sm_desecration_stone', 0),
(301314, 10, 15, 'Blood-Written Rite', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, '', 'go_sm_blood_rite', 0)
ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`), `name` = VALUES(`name`),
    `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` BETWEEN 301310 AND 301314;
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301310, 0, 0, 0, 0, 0, 0, 0, 0),
(301311, 0, 0, 0, 0, 0, 0, 0, 0),
(301312, 0, 0, 0, 0, 0, 0, 0, 0),
(301313, 0, 0, 0, 0, 0, 0, 0, 0),
(301314, 0, 0, 0, 0, 0, 0, 0, 0);

-- The gossip texts (ids = the objects' entries, ThalnosHardModeLogic.h EpitaphTextId / kRiteTextId; free in the live
-- DB, read-only check 2026-11-20). The epitaphs name each hero by deed, not by name; the rite names the order in other
-- words, so the reader has to match them (GY "Trigger: the Desecration").
DELETE FROM `npc_text` WHERE `ID` BETWEEN 301310 AND 301314;
INSERT INTO `npc_text` (`ID`, `text0_0`, `text0_1`, `BroadcastTextID0`, `lang0`, `Probability0`, `BroadcastTextID1`,
    `Probability1`, `BroadcastTextID2`, `Probability2`, `BroadcastTextID3`, `Probability3`, `BroadcastTextID4`,
    `Probability4`, `BroadcastTextID5`, `Probability5`, `BroadcastTextID6`, `Probability6`, `BroadcastTextID7`,
    `Probability7`, `VerifiedBuild`) VALUES
(301310,
    'The name is worn away. The epitaph remains:$B$B"He marched the armies of the Crusade from Tirisfal '
    'to Hearthglen."',
    'The name is worn away. The epitaph remains:$B$B"He marched the armies of the Crusade from Tirisfal '
    'to Hearthglen."',
    0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(301311,
    'The name is worn away. The epitaph remains:$B$B"He put the question to Gilneas, and the city '
    'answered in fire."',
    'The name is worn away. The epitaph remains:$B$B"He put the question to Gilneas, and the city '
    'answered in fire."',
    0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(301312,
    'The name is worn away. The epitaph remains:$B$B"Shepherd of the Crusade''s souls. Slain by his own '
    'blood."',
    'The name is worn away. The epitaph remains:$B$B"Shepherd of the Crusade''s souls. Slain by his own '
    'blood."',
    0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(301313,
    'The name is worn away. The epitaph remains:$B$B"Last to lead the Crusade, last to stand."',
    'The name is worn away. The epitaph remains:$B$B"Last to lead the Crusade, last to stand."',
    0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(301314,
    'A rite is written on the wall in old blood:$B$B"Wake first the general of the long march. Wake '
    'second the questioner of the burning city. Wake third the father slain by his daughter. Wake last '
    'the last of their captains."',
    'A rite is written on the wall in old blood:$B$B"Wake first the general of the long march. Wake '
    'second the questioner of the burning city. Wake third the father slain by his daughter. Wake last '
    'the last of their captains."',
    0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);

-- The spawns, heroic only (spawnMask 2: the Desecration is heroic only, hub ruling 7), section 7 #18 A: the stones on
-- the lawn disc (1796.5, 1369.5) at NAVMESH's four spots (11.4 yd apart, each facing the disc's center), the rite in
-- the z 0 court at the crypt stair's head, facing south into the court (all [navmesh estimate]; `.gps` in game).
-- Guids 3013100-3013140 (entry x 10, the hand-SQL convention; free in the live DB, read-only check 2026-11-20).
-- Rotation = the orientation about z (rotation2 = sin(o/2), rotation3 = cos(o/2)). A long respawn is never needed:
-- the stones' state is the instance's (the touch order per attempt, the flag saved), so a cold load is whole (RB-2).
DELETE FROM `gameobject` WHERE `guid` BETWEEN 3013100 AND 3013140 AND `id` BETWEEN 301310 AND 301314;
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`,
    `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`,
    `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3013100, 301310, 189, 0, 0, 2, 1, 1802.2, 1375.2, 18.8, 3.92699, 0, 0, 0.92388, -0.382683, 7200, 255, 1, '', 0,
    'Scarlet Monastery D4H: the gravestone of Galvar (the Desecration, heroic only)'),
(3013110, 301311, 189, 0, 0, 2, 1, 1790.8, 1375.2, 18.8, 5.49779, 0, 0, 0.382683, -0.92388, 7200, 255, 1, '', 0,
    'Scarlet Monastery D4H: the gravestone of Fairbell (the Desecration, heroic only)'),
(3013120, 301312, 189, 0, 0, 2, 1, 1790.8, 1363.8, 18.7, 0.785398, 0, 0, 0.382683, 0.92388, 7200, 255, 1, '', 0,
    'Scarlet Monastery D4H: the gravestone of Voss (the Desecration, heroic only)'),
(3013130, 301313, 189, 0, 0, 2, 1, 1802.2, 1363.8, 18.4, 2.35619, 0, 0, 0.92388, 0.382683, 7200, 255, 1, '', 0,
    'Scarlet Monastery D4H: the gravestone of Goodchilde (the Desecration, heroic only)'),
(3013140, 301314, 189, 0, 0, 2, 1, 1788.5, 1417.0, 0.3, 3.14159, 0, 0, 1, 0, 7200, 255, 1, '', 0,
    'Scarlet Monastery D4H: the blood rite (the Desecration, heroic only)');

-- Section 7 #18 A: the Anguished Dead standing 1.2 yd from the rite (guid 39906, random movement 2 yd) moves 10 yd
-- west along the court (x 1780-1790, y 1402-1432; 5.7 yd from the other Anguished Dead 39944) so a reader is not
-- pulled at the wall. Its entry and spawn mask are untouched ([navmesh estimate]; `.gps` in game).
UPDATE `creature` SET `position_x` = 1787.0, `position_y` = 1427.0 WHERE `guid` = 39906 AND `id` = 6426;
