-- Deadmines Pilot WP-K (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md s3.2 item 4, s3.3, s7 #2, #5, #7):
-- the rows dbc-tools cannot declare for the shared kit. The boss WPs' own rows (smart_scripts removals, spawns,
-- formations, creature_text, the keg's spawn) are in their own revs.

-- Map 36 runs the module's instance script (modules/mod-dungeon-bosses, instance_deadmines_rework.cpp); the stock
-- instance_deadmines stays registered and unbound.
UPDATE `instance_template` SET `script` = 'instance_deadmines_rework' WHERE `map` = 36 AND `script` = 'instance_deadmines';

-- -229 plus STUN: the reworked bosses are immune to player stuns (designer 2026-10-28) but still silenceable, so the
-- heroic class tool pass's silence interrupts keep working (handoff s7 #5; -273 would add SILENCE). -229 is
-- MechanicsMask 1217817766 (comment mask 0x244B3653); STUN is mechanic 12, stored bit 1 << 12 = 4096 (set 1971 "Immune
-- to Stun" is exactly that bit): 1217817766 + 4096 = 1217821862 (comment mask 0x244B3E53). Checked 2026-11-06 with
-- read-only SELECTs: no set has that mask, 1972 is the first free positive id. Used by every Deadmines boss except
-- Rhahk'Zor (-159), on the normal rows (apps/dbc-tools source/npcs/deadmines/) and the heroic rows (deadmines.py).
DELETE FROM `creature_immunities` WHERE `ID` = 1972;
INSERT INTO `creature_immunities` (`ID`, `SchoolMask`, `DispelTypeMask`, `MechanicsMask`, `Effects`, `Auras`, `ImmuneAoE`, `ImmuneChain`, `Comment`) VALUES
(1972, 0, 0, 1217821862, '', '', 0, 0, 'Deadmines Pilot bosses: -229 + STUN, mech=0x244B3E53(CHARM|DISORIENTED|FEAR|ROOT|SLEEP|SNARE|STUN|FREEZE|KNOCKOUT|POLYMORPH|BANISH|SHACKLE|TURN|DAZE|SAPPED)');

-- The boss-kit gameobjects (ids.yaml block `gameobject`, reservation `deadmines` 301000-301099). Upserts:
-- gameobject_template rows are never deleted (codestyle-sql not_delete).
-- 301000 Powder Keg: VanCleef's hard mode trigger (go_dm_powder_keg, WP-B9), the stock Deadmines powder keg model
--        (display 436, as gameobject 193640), clickable (GOOBER, no lock); its heroic-only spawn is WP-B9's SQL.
-- 301001 Harpoon Rope: Greenskin's rope (go_dm_harpoon_rope, WP-B7), the rope coil display 7538 of the clickable
--        stock Rope Pile 186905 (GOOBER, no lock, no spell: the script cuts the rope), summoned at the rope's midpoint.
-- 301002 Burning Mainmast: the hard mode's fallen mast (WP-B9), summoned lying across the deck, no script.
--        TODO(WP-V): display 90020 is the reserved GameObjectDisplayInfo row for the burning ship mast
--        (HF_BurningShip_Mast.M2, handoff s3.10 gap 6); until WP-V ships it the mast shows no model.
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`, `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`, `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`, `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301000, 10, 436, 'Powder Keg', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', 'go_dm_powder_keg', 0),
(301001, 10, 7538, 'Harpoon Rope', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', 'go_dm_harpoon_rope', 0),
(301002, 5, 90020, 'Burning Mainmast', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`), `name` = VALUES(`name`), `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `Data10` = VALUES(`Data10`), `AIName` = VALUES(`AIName`), `ScriptName` = VALUES(`ScriptName`);

-- Equipment of the boss-kit copies (apps/dbc-tools source/npcs/deadmines/): the stock creatures' rows, ID 1.
-- 300420 Watchman = 1725, 300421 Evoker = 1729, 300422 Working Miner = 598 (the pick), 300426 Blackguard = 636.
DELETE FROM `creature_equip_template` WHERE `CreatureID` IN (300420, 300421, 300422, 300426) AND `ID` = 1;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
(300420, 1, 5281, 0, 5259, 0),
(300421, 1, 1907, 0, 0, 0),
(300422, 1, 1910, 0, 0, 0),
(300426, 1, 5285, 0, 0, 0);
