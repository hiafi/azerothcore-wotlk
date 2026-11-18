-- Blackrock Depths build WP-D19: Phalanx (9502) and the Rowdy Patron (300841), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D19; build spec
-- docs/dungeons/blackrock-depths-4-imperial-seat.md "Phalanx", rulings 63-66). His template (npc_phalanx_rework,
-- AIName '', 160k, stun immune, INSTANCE_BIND), the Rowdy Patron's template and model, and spells 211460-211472 are
-- apps/dbc-tools source/npcs/blackrock_depths/phalanx.py. Phalanx has no smart_scripts row (live SELECT 2026-11-17),
-- so there is nothing to drop; Plugger's death still reaches him through its stock SmartAI row (9499 id 12, SET_FACTION
-- 14 on 9502 within 100 yd: D17's, kept). He keeps his spawn (guid 46615, spawnMask 1: the heroic rollout copies it);
-- the Rowdy Patrons are summoned by his script. This rev inserts no creature spawn and no SmartAI row (rule 14: nothing
-- for the heroic spawn mask to miss).

-- His texts (S4 "Text"): group 0 is the stock wake-up yell ("Violence!  Property damage!  None shall pass!!",
-- untouched). Group 1 is a boss emote (type 41, rule 2) naming the grabbed player ($n: the Talk target), area-wide
-- (TextRange 1: the Grim Guzzler); groups 2-4 are yells at their default range.
DELETE FROM `creature_text` WHERE `CreatureID` = 9502 AND `GroupID` BETWEEN 1 AND 4;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9502, 1, 0, '%s grabs $n by the collar!', 41, 0, 100, 0, 0, 0, 0, 1, 'Phalanx - Throw Out (PH4)'),
(9502, 2, 0, 'Last call! Everybody out!', 14, 0, 100, 0, 0, 0, 0, 0, 'Phalanx - Last Call (PH5)'),
(9502, 3, 0, 'PROPERTY DAMAGE!', 14, 0, 100, 0, 0, 0, 0, 0, 'Phalanx - Property Damage (PH6, heroic)'),
(9502, 4, 0, 'Closing... time...', 14, 0, 100, 0, 0, 0, 0, 0, 'Phalanx - death');

-- The gossip start (ruling 66; handoff section 7 #12: a section 4 Finder group can always open the Bar Door). The stock
-- menu 2283 (text 2973, "I do not enjoy conversation.") on his template gets option 0; npc_phalanx_rework's
-- sGossipSelect wakes him (the stock walk to the door, faction 54 on arrival). Shown only while he is dormant: the
-- instance's DATA_PHALANX_ACTIVATED (44) still NOT_STARTED (the script also drops his gossip flag once he wakes).
DELETE FROM `gossip_menu_option` WHERE `MenuID` = 2283 AND `OptionID` = 0;
INSERT INTO `gossip_menu_option` (`MenuID`, `OptionID`, `OptionIcon`, `OptionText`, `OptionBroadcastTextID`,
    `OptionType`, `OptionNpcFlag`, `ActionMenuID`, `ActionPoiID`, `BoxCoded`, `BoxMoney`, `BoxText`,
    `BoxBroadcastTextID`, `VerifiedBuild`) VALUES
(2283, 0, 0, 'Then let''s skip the talking. I''m here to cause some property damage.', 0, 1, 1, 0, 0, 0, 0, '', 0, 0);
DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 15 AND `SourceGroup` = 2283 AND `SourceEntry` = 0;
INSERT INTO `conditions` (`SourceTypeOrReferenceId`, `SourceGroup`, `SourceEntry`, `SourceId`, `ElseGroup`,
    `ConditionTypeOrReference`, `ConditionTarget`, `ConditionValue1`, `ConditionValue2`, `ConditionValue3`,
    `NegativeCondition`, `ErrorType`, `ErrorTextId`, `ScriptName`, `Comment`) VALUES
(15, 2283, 0, 0, 0, 13, 0, 44, 0, 0, 0, 0, 0, '', 'Phalanx - start a fight: only while dormant (data 44)');
