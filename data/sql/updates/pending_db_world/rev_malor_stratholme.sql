-- Stratholme build WP-S4: Malor the Zealous (11032), the rows dbc-tools cannot declare
-- (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S4; build spec
-- docs/dungeons/stratholme-rework.md ST 1239-1289). His template (boss_malor_the_zealous_rework, AIName '', health,
-- DamageModifier 3.5, immunities, INSTANCE_BIND), the Medallion stalker 300605 and his spells 206480-206493 are
-- apps/dbc-tools source/npcs/stratholme/malor_the_zealous.py.

-- SmartAI 11032 (Ground Smash 12734, Head Crack 16172, Holy Light 15493 below 50% health, Lay on Hands 10310 below 10%)
-- is removed (ST "Stock kit", approved 2026-11-03): boss_malor_the_zealous_rework reworks the Smash (MZ7), makes Holy
-- Light his own interruptible cast (MZ9), turns Lay on Hands into the Miracle (MZ10) and retires Head Crack.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 11032 AND `source_type` = 0;

-- Texts (ST "Text"; none stock): the yells are type 14; the two mechanic lines are boss emotes (41), so each names the
-- moment on screen.
DELETE FROM `creature_text` WHERE `CreatureID` = 11032;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(11032, 0, 0, 'You will not lay a hand on the medallion! The Light protects its own!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Malor the Zealous - Aggro'),
(11032, 1, 0, 'The Medallion of Faith blazes with holy light!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Malor the Zealous - The blaze (MZ1)'),
(11032, 2, 0, 'Unclean! I can smell the plague on you!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Malor the Zealous - Unclean (MZ5)'),
(11032, 3, 0, '%s raises his warhammer high!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Malor the Zealous - Ground Smash (MZ7)'),
(11032, 4, 0, 'Light, grant me strength!', 14, 0, 100, 0, 0, 0, 0, 0, 'Malor the Zealous - Miracle (MZ10)'),
(11032, 5, 0, 'My faith... was... true...', 14, 0, 100, 0, 0, 0, 0, 0, 'Malor the Zealous - Death');
