-- Stratholme build WP-S3: Timmy the Cruel (10808), the rows dbc-tools cannot declare
-- (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S3; build spec
-- docs/dungeons/stratholme-rework.md ST 1035-1090). His template (boss_timmy_the_cruel_rework, AIName '', health,
-- DamageModifier 13, immunities, INSTANCE_BIND), the Playmate 300604 and his spells 206460-206468 are
-- apps/dbc-tools source/npcs/stratholme/timmy_the_cruel.py.

-- Timmy the Cruel: SmartAI 10808 is removed, all seven rows (Ravenous Claw and Enrage are cast by the script; the
-- aggro yell is the script's; the respawn hide, the 10 s gate check and the emerge are boss_timmy_the_cruel_rework's),
-- and the emerge actionlist 1080800 (emote state 449, visible, not immune, the 3.5 s wait, patrol path 2472270).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10808 AND `source_type` = 0;
DELETE FROM `smart_scripts` WHERE `entryorguid` = 1080800 AND `source_type` = 9;

-- The gate on the out-of-combat row (SourceGroup = row id + 1 = 7): no living Crimson Guardsman 10418, Conjuror
-- 10419, Initiate 10420 or Gallant 10424 within 70 yd. The script checks the same four entries itself now.
DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 22 AND `SourceEntry` = 10808 AND `SourceId` = 0;

-- His lines (ST "Text"): group 0 "TIMMY!" stays stock; the game yells are type 14, the two mechanic emotes are boss
-- emotes (41), so they name the mechanic on screen. The Playmate's one line.
DELETE FROM `creature_text` WHERE `CreatureID` = 10808 AND `GroupID` BETWEEN 1 AND 6;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10808, 1, 0, 'TIMMY TAG!', 14, 0, 100, 0, 0, 0, 0, 0, 'Timmy the Cruel - Freeze Tag (TC2)'),
(10808, 2, 0, '%s starts clapping his hands together.', 41, 0, 100, 0, 0, 0, 0, 0,
    'Timmy the Cruel - Patty Cake (TC6)'),
(10808, 3, 0, 'TIMMIES!', 14, 0, 100, 0, 0, 0, 0, 0, 'Timmy the Cruel - Guess Who (TC7)'),
(10808, 4, 0, 'JUMP TIM TIM', 14, 0, 100, 0, 0, 0, 0, 0, 'Timmy the Cruel - Jump Rope (TC8)'),
(10808, 5, 0, '%s swings the Grimgore Noose like a jump rope!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Timmy the Cruel - Jump Rope (TC8)'),
(10808, 6, 0, 'Timm... ayyyy...', 14, 0, 100, 0, 0, 0, 0, 0, 'Timmy the Cruel - Death');

DELETE FROM `creature_text` WHERE `CreatureID` = 300604;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(300604, 0, 0, 'TIMMY!', 14, 0, 100, 0, 0, 0, 0, 0, 'Playmate - Burst up (TC7)');
