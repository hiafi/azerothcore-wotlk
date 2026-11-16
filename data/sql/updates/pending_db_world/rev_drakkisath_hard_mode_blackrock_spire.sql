-- Blackrock Spire build WP-B15: General Drakkisath's hard mode, the General's Army, the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.7, s3.5 row B15; build spec
-- docs/dungeons/blackrock-spire-rework.md SP 3990-4082 rows DR10-DR19). The hard mode's creatures 300736-300741 and its
-- spells 210560-210586 (and their spell_script_names rows) are apps/dbc-tools
-- source/npcs/blackrock_spire/drakkisath_hard_mode.py. Nefarius's insult lines (the arena copy 300732, lines 18-19) are
-- B12's rev_rend_gyth_blackrock_spire.sql; his lines 0-8 are B14's rev_drakkisath_blackrock_spire.sql.

-- Drakkisath's line 9 (DR11, the herald's "Let them come") and the herald's line 0 (as it runs to the alcove).
DELETE FROM `creature_text` WHERE `CreatureID` = 10363 AND `GroupID` = 9;
DELETE FROM `creature_text` WHERE `CreatureID` = 300740 AND `GroupID` = 0;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10363, 9, 0, 'So you are the ones who mocked Lord Victor. My legions will grind you to dust!', 14, 0, 100, 0, 0, 0, 0,
    0, 'General Drakkisath - The General''s Army armed (DR11, hard mode)'),
(300740, 0, 0, 'As you wish. The legions of the black flight are coming for you!', 12, 0, 100, 0, 0, 0, 0, 0,
    'Black Dragonkin Herald - Let them come (DR11)');

-- The herald's gossip (SP "Text"): the body, "Let them come." and the option's conditions, which mirror the arming rule
-- (DrakkisathHardModeLogic.h HeraldRefusalFor; the instance's GeneralsArmyChangeAllowed decides again on the click):
-- heroic, the insult saved (DATA_NEF_INSULTED 30 = 1), not armed yet (DATA_GENERALS_ARMY 34 = 0), Drakkisath (boss
-- state 13) neither in progress (1) nor done (3).
DELETE FROM `gossip_menu` WHERE `MenuID` = 300740;
INSERT INTO `gossip_menu` (`MenuID`, `TextID`) VALUES
(300740, 300740);
DELETE FROM `npc_text` WHERE `ID` = 300740;
INSERT INTO `npc_text` (`ID`, `text0_0`, `BroadcastTextID0`, `lang0`, `Probability0`) VALUES
(300740, 'Lord Victor has heard your insolence. The general''s legions await your word.', 0, 0, 1);
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 300740;
INSERT INTO `gossip_menu_option` (`MenuID`, `OptionID`, `OptionIcon`, `OptionText`, `OptionBroadcastTextID`,
    `OptionType`, `OptionNpcFlag`, `ActionMenuID`, `ActionPoiID`, `BoxCoded`, `BoxMoney`, `BoxText`,
    `BoxBroadcastTextID`, `VerifiedBuild`) VALUES
(300740, 0, 0, 'Let them come.', 0, 1, 1, 0, 0, 0, 0, '', 0, 0);
DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 15 AND `SourceGroup` = 300740;
INSERT INTO `conditions` (`SourceTypeOrReferenceId`, `SourceGroup`, `SourceEntry`, `SourceId`, `ElseGroup`,
    `ConditionTypeOrReference`, `ConditionTarget`, `ConditionValue1`, `ConditionValue2`, `ConditionValue3`,
    `NegativeCondition`, `ErrorType`, `ErrorTextId`, `ScriptName`, `Comment`) VALUES
(15, 300740, 0, 0, 0, 49, 0, 1, 0, 0, 0, 0, 0, '', 'Black Dragonkin Herald - Let them come: heroic only'),
(15, 300740, 0, 0, 0, 13, 0, 30, 1, 0, 0, 0, 0, '', 'Black Dragonkin Herald - Let them come: Nefarius insulted'),
(15, 300740, 0, 0, 0, 13, 0, 34, 0, 0, 0, 0, 0, '', 'Black Dragonkin Herald - Let them come: not armed yet'),
(15, 300740, 0, 0, 0, 13, 0, 13, 1, 2, 1, 0, 0, '', 'Black Dragonkin Herald - Let them come: Drakkisath not fighting'),
(15, 300740, 0, 0, 0, 13, 0, 13, 3, 2, 1, 0, 0, '', 'Black Dragonkin Herald - Let them come: Drakkisath alive');

-- The squads' weapons: the stock Rage Talon units' (creature_equip_template 9096, 10371, 10372, 10366).
DELETE FROM `creature_equip_template` WHERE `CreatureID` BETWEEN 300736 AND 300739;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
(300736, 1, 2179, 0, 0, 0),
(300737, 1, 6680, 0, 0, 0),
(300738, 1, 5304, 0, 0, 0),
(300739, 1, 2183, 1984, 0, 0);

-- The herald's spawn: the throne room's south end (DrakkisathHardModeLogic.h kHeraldEntrance, a placeholder: NM 13
-- could not tell whether y -325 is a wall or the way in; `.gps` check in the playtest), facing his alcove. Heroic only
-- (spawnMask 2, the hard mode objects' convention); its AI hides it without the insult and while he fights or is dead.
-- guid = entry x 10 (the kit spawns' convention, free in the live DB, read-only check 2026-11-15).
DELETE FROM `creature` WHERE `id` = 300740 AND `guid` = 3007400;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(3007400, 300740, 229, 0, 0, 2, 1, 0, 5.0, -320.0, 111.04, 0.79, 7200, 0, 0, 0,
    'Blackrock Spire B15: Black Dragonkin Herald (Drakkisath''s hard mode, heroic only, after the insult)');
