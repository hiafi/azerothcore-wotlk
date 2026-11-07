-- Shadowfang Keep build WP-K (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md s3.3, s7 #1, #9,
-- #10): the rows dbc-tools cannot declare for the SFK layer. The boss WPs' own rows (smart_scripts removals, texts,
-- spawns, gossip) are in their own revs.
--
-- instance_template is not touched (s7 #1): map 33 keeps `instance_shadowfang_keep`, which mod-dungeon-bosses
-- (instance_shadowfang_keep_rework.cpp) now registers under the same name, replacing the stock script at load.

-- The boss-kit gameobjects (ids.yaml reservation `shadowfang_keep` 301100-301149). Upserts: gameobject_template rows
-- are never deleted (codestyle-sql not_delete).
-- 301100 Cell Key: Rethilgore's key ring (WP-S1), the look of a DungeonKit::Pickups spot (a goEntry, no script, not
--        clickable: GENERIC). TODO(WP-V): display 90030 is the reserved GameObjectDisplayInfo row for the Ascension
--        key ring (handoff s3.10 gap 1); until WP-V ships it the key shows no model.
-- 301101 Alarm Bell: Odo's bells (WP-S5, go_sfk_alarm_bell), a copy of the Booty Bay Alarm Bell 175948 (GOOBER,
--        display 4052, data3 3000) at size 0.55 (the stock model is 3.4 x 7.2 x 4.4 yd at size 1; s3.10). Its three
--        spawns are WP-S5's rev.
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`, `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`, `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`, `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301100, 5, 90030, 'Cell Key', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '', 0),
(301101, 10, 4052, 'Alarm Bell', '', '', '', 0.55, 0, 0, 0, 3000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', 'go_sfk_alarm_bell', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`), `name` = VALUES(`name`), `size` = VALUES(`size`), `Data3` = VALUES(`Data3`), `AIName` = VALUES(`AIName`), `ScriptName` = VALUES(`ScriptName`);

-- Equipment of the lair prisoner copies (apps/dbc-tools source/npcs/shadowfang_keep/archmage_arugal.py): the stock
-- rows, ID 1. 300514 Deathstalker Adamant = 3849 (item 1899); 300513 Sorcerer Ashcrombe = 3850 has none.
DELETE FROM `creature_equip_template` WHERE `CreatureID` = 300514 AND `ID` = 1;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
(300514, 1, 1899, 0, 0, 0);
