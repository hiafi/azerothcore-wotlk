-- Blackrock Spire build WP-B8: Overlord Wyrmthalak (9568), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.5 row B8; build spec
-- docs/dungeons/blackrock-spire-rework.md SP 2436-2521). His template (boss_overlord_wyrmthalak_rework, AIName '',
-- health, DamageModifier 3.5, immunity 1972, INSTANCE_BIND), the champions 300708-300710, the Worg Rider 300711, the
-- tribe thrower 300712 and his spells 210250-210265 are apps/dbc-tools source/npcs/blackrock_spire/wyrmthalak.py.
-- He has no SmartAI (the stock script is C++); his loot rows are L-1's.

-- His texts (SP "Text"). The stock group 0 ("%s calls for help!", the retired 51% summons) is replaced by the pull
-- yell. Yells 14, boss emotes 41. Lines 7-9 belong to the hard mode (WP-B9: the horn, Caustic Roar, the spear).
DELETE FROM `creature_text` WHERE `CreatureID` = 9568 AND `GroupID` BETWEEN 0 AND 9;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9568, 0, 0, 'You stand in the citadel of the Black Flight. The tribes will tear you apart!', 14, 0, 100, 0, 0, 0, 0,
    0, 'Overlord Wyrmthalak - The pull'),
(9568, 1, 0, '%s draws a breath of black flame!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Overlord Wyrmthalak - Black Dragonfire (WT1)'),
(9568, 2, 0, 'Spirestone! Crush them!', 14, 0, 100, 0, 0, 0, 0, 0, 'Overlord Wyrmthalak - Order: Spirestone (WT4)'),
(9568, 3, 0, 'Smolderthorn! Cut them down!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Overlord Wyrmthalak - Order: Smolderthorn (WT4)'),
(9568, 4, 0, 'Bloodaxe! Ride them down!', 14, 0, 100, 0, 0, 0, 0, 0, 'Overlord Wyrmthalak - Order: Bloodaxe (WT4)'),
(9568, 5, 0, '%s bellows for his tribe, but none answer!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Overlord Wyrmthalak - A dead champion''s order (WT4)'),
(9568, 6, 0, 'The general... will hear of this...', 14, 0, 100, 0, 0, 0, 0, 0, 'Overlord Wyrmthalak - Death'),
(9568, 7, 0, 'The war horn echoes through the citadel. The whole Spire musters!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Overlord Wyrmthalak - The war horn (WT9, hard mode)'),
(9568, 8, 0, '%s rears back with a caustic roar!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Overlord Wyrmthalak - Caustic Roar (WT14, hard mode)'),
(9568, 9, 0, '%s hurls his spear at $n!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Overlord Wyrmthalak - Spear Chain (WT15, hard mode)');

-- The champions' weapons: the Spirestone Champion carries the Spirestone Warlord's pair (9216: 5286 x2), the Bloodaxe
-- Champion the Bloodaxe Raider's (9692: 12142). The Smolderthorn Berserker (9268) has none: his champion has none.
DELETE FROM `creature_equip_template` WHERE `CreatureID` IN (300708, 300710);
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
(300708, 1, 5286, 5286, 0, 0),
(300710, 1, 12142, 0, 0, 0);
