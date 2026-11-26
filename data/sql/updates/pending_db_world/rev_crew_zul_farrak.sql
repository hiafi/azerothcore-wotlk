-- Zul'Farrak build WP-CR: Sergeant Bly's crew (handoff s3.12; s7 #17 A; SP texts). The crew's scripts are bound by
-- rev_skeleton_zul_farrak.sql; this rev only adds what CR owns.

-- s7 #17 A: players may heal the crew. Bly already carries CREATURE_TYPE_FLAG_CAN_ASSIST (4096); Raven, Oro, Weegli and
-- Murta get it. The heroic copies (dungeon difficulties, WP-H; heroic_ids 310518-310522) get it too: the engine reads
-- the difficulty template's type_flags. Each heroic UPDATE is guarded by its name, so a moved id changes nothing.
UPDATE `creature_template` SET `type_flags` = `type_flags` | 4096 WHERE `entry` IN (7605, 7606, 7607, 7608);
UPDATE `creature_template` SET `type_flags` = `type_flags` | 4096 WHERE `entry` = 310518 AND `name` = 'Sergeant Bly';
UPDATE `creature_template` SET `type_flags` = `type_flags` | 4096 WHERE `entry` = 310519 AND `name` = 'Raven';
UPDATE `creature_template` SET `type_flags` = `type_flags` | 4096 WHERE `entry` = 310520 AND `name` = 'Oro Eyegouge';
UPDATE `creature_template` SET `type_flags` = `type_flags` | 4096
    WHERE `entry` = 310521 AND `name` = 'Weegli Blastfuse';
UPDATE `creature_template` SET `type_flags` = `type_flags` | 4096 WHERE `entry` = 310522 AND `name` = 'Murta Grimgut';

-- New text groups (0-based as SP prints them, rule 34; 0-2 are stock). Said by D5 (Bly 3, 4; CR's default yield says
-- 4), D7Ha (Bly 5, Weegli 4) and D4b (Weegli 3). Type 14 yell, 12 say.
DELETE FROM `creature_text` WHERE `CreatureID` = 7604 AND `GroupID` IN (3, 4, 5);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(7604, 3, 0, 'Get $n, lads!', 14, 0, 100, 0, 0, 0, 0, 0, 'Sergeant Bly - Gang Up (BC1)'),
(7604, 4, 0, 'Enough! You''ve proven yourselves. Lead on to the beast, and the treasure''s ours to share!', 12, 0, 100,
    0, 0, 0, 0, 0, 'Sergeant Bly - the Test, all yielded (BC11)'),
(7604, 5, 0, 'Behind me, $n!', 14, 0, 100, 0, 0, 0, 0, 0, 'Sergeant Bly - Storm''s Chosen (GZ17)');

DELETE FROM `creature_text` WHERE `CreatureID` = 7607 AND `GroupID` IN (3, 4);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(7607, 3, 0, 'Fire in the hole! Get off the stairs!', 14, 0, 100, 0, 0, 0, 0, 0, 'Weegli Blastfuse - barrels (PY4)'),
(7607, 4, 0, 'Fire in the hole!', 14, 0, 100, 0, 0, 0, 0, 0, 'Weegli Blastfuse - Blasting Charge (GZ16)');
