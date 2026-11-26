-- Gnomeregan build WP-D4: the Mobile Alert System (301110), the rows dbc-tools cannot declare
-- (.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.5 row D4, s7 #21 A; build spec
-- docs/dungeons/gnomeregan-rework.md "The Mobile Alert System", Text). His template, the Security Assistant 301111, the
-- Security Defender 301112, the light stalker 301113 and the spells 214420-214428 are apps/dbc-tools
-- source/npcs/gnomeregan/mobile_alert_system.py; his spawn (guid 3011100), the hall's packs and patroller 30205 are
-- WP-S0's rev_skeleton_gnomeregan.sql. The stock alarm bot 7849 (five trash spawns) and its text row stay as they are.

-- The texts, 0-based as SP prints them (rule 35): yells type 14, the boss emotes type 41. Line 0 is 7849's stock line
-- (broadcast 4142) with the alert bot's voice (SoundEntries 5805, _visuals.MA_ALARM_VOICE); lines 4 and 5 are the
-- Alarm-a-bomb 2600's (7897) stock lines (broadcasts 3927, 3949); line 8 is section 7 #21 A's "the cameras" emote.
DELETE FROM `creature_text` WHERE `CreatureID` = 301110 AND `GroupID` BETWEEN 0 AND 8;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(301110, 0, 0, 'Warning! Warning! Intruder alert! Intruder alert!', 14, 0, 100, 0, 0, 5805, 4142, 0,
    'Mobile Alert System - the alarm (pull, patrols)'),
(301110, 1, 0, '%s locks its searchlight on $n!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Mobile Alert System - Searchlight lock-on (MA1)'),
(301110, 2, 0, 'Intruder alert! $n has been spotted!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Mobile Alert System - Spotted (MA3)'),
(301110, 3, 0, '%s reverses its sweep!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Mobile Alert System - Reverse sweep (MA4, heroic)'),
(301110, 4, 0, 'Self-destruct sequence activated.', 14, 0, 100, 0, 0, 0, 3927, 0,
    'Mobile Alert System - Self-destruct on the pull (MA7, heroic; 7897''s line)'),
(301110, 5, 0, 'Anti-escape countermeasures activated. Self-destruct in t-minus 20 seconds....', 14, 0, 100, 0, 0, 0,
    3949, 0, 'Mobile Alert System - Self-destruct at 20 s left (MA7, heroic; 7897''s line)'),
(301110, 6, 0, '%s''s countdown skips ahead!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Mobile Alert System - a Spotted takes 5 s off the clock (MA7, heroic)'),
(301110, 7, 0, 'Alert... canceled. Have a... nice...', 14, 0, 100, 0, 0, 0, 0, 0,
    'Mobile Alert System - death (MA10)'),
(301110, 8, 0, '%s''s cameras catch $n beyond the lights!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Mobile Alert System - Spotted past 30 yd (section 7 #21 A)');

-- The Security Defender's gun: the stock Leprous Defender 6223's equipment row (items 1905 and 2552; SELECT
-- 2026-11-26). The Assistant 7603 has none.
DELETE FROM `creature_equip_template` WHERE `CreatureID` = 301112;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
(301112, 1, 1905, 0, 2552, 0);
