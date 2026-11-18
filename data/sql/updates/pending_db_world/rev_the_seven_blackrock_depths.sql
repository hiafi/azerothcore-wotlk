-- Blackrock Depths build WP-D21: The Seven (Anger'rel 9035, Seeth'rel 9038, Dope'rel 9040, Gloom'rel 9037, Vile'rel
-- 9036, Hate'rel 9034, Doom'rel 9039), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D21; build spec
-- docs/dungeons/blackrock-depths-4-imperial-seat.md "The Seven"). Their templates (boss_the_seven_rework, AIName '',
-- the shared pool's HealthModifier, INSTANCE_BIND) and spells 211520-211557 are apps/dbc-tools
-- source/npcs/blackrock_depths/the_seven.py. This rev inserts no creature spawn and no SmartAI row (rule 14: nothing
-- for the heroic spawn mask to miss); the seven spawns (guids 91020-91026, spawnMask 1) stay as they are.

-- 1. The SmartAI of the five ghosts that ran it (S0 report section 5 item 2; live SELECT 2026-11-17: 9034 5 rows, 9035
--    5, 9036 5, 9038 6, 9040 6, all source_type 0; 9037 and 9039 had none, their stock C++ boss_gloomrel /
--    boss_doomrel is replaced by the binding; no actionlist and no guid rows). The one AI re-creates what the spec
--    keeps (TheSevenLogic.h kKit) and drops the rest (Frost Ward, Hate'rel's Strike and his dead self-targeted bolt,
--    Prayer of Healing, Heal; the 5 s "zone in combat" rows: every ghost is in combat from the challenge on).
DELETE FROM `smart_scripts` WHERE `source_type` = 0 AND `entryorguid` IN (9034, 9035, 9036, 9038, 9040);

-- 2. Their texts (S4 "Text", section 8 #24): a rise line and a mood line per ghost, yells. Doom'rel's group 0 is his
--    stock challenge (a say at the gossip start), kept; his rise and mood lines are groups 1 and 2. The tomb is about
--    95 x 120 yd: a yell's own range covers it (TextRange 0).
DELETE FROM `creature_text` WHERE `CreatureID` IN (9034, 9035, 9036, 9037, 9038, 9040) AND `GroupID` BETWEEN 0 AND 1;
DELETE FROM `creature_text` WHERE `CreatureID` = 9039 AND `GroupID` BETWEEN 1 AND 2;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9035, 0, 0, 'Anger''rel stands sentry no longer!', 14, 0, 100, 0, 0, 0, 0, 0, 'Anger''rel - rise (TS1)'),
(9035, 1, 0, 'I''ll run you down!', 14, 0, 100, 0, 0, 0, 0, 0, 'Anger''rel - Furious Charge (TS3)'),
(9038, 0, 0, 'The cold of the tomb rises with me.', 14, 0, 100, 0, 0, 0, 0, 0, 'Seeth''rel - rise (TS1)'),
(9038, 1, 0, 'Freeze with us!', 14, 0, 100, 0, 0, 0, 0, 0, 'Seeth''rel - Seething Cold (TS4)'),
(9040, 0, 0, 'Heh... where was I?', 14, 0, 100, 0, 0, 0, 0, 0, 'Dope''rel - rise (TS1)'),
(9040, 1, 0, 'Hold still, hold still!', 14, 0, 100, 0, 0, 0, 0, 0, 'Dope''rel - Dopey Haze (TS5)'),
(9037, 0, 0, 'Again... always again.', 14, 0, 100, 0, 0, 0, 0, 0, 'Gloom''rel - rise (TS1)'),
(9037, 1, 0, 'There is no hope here.', 14, 0, 100, 0, 0, 0, 0, 0, 'Gloom''rel - Gloom (TS6)'),
(9036, 0, 0, 'The Seven endure.', 14, 0, 100, 0, 0, 0, 0, 0, 'Vile''rel - rise (TS1)'),
(9036, 1, 0, 'Brothers, take my strength!', 14, 0, 100, 0, 0, 0, 0, 0, 'Vile''rel - Vile Communion (TS7)'),
(9034, 0, 0, 'I hate you all.', 14, 0, 100, 0, 0, 0, 0, 0, 'Hate''rel - rise (TS1)'),
(9034, 1, 0, 'Get away from each other... or burn!', 14, 0, 100, 0, 0, 0, 0, 0, 'Hate''rel - Hatred (TS8)'),
(9039, 1, 0, 'Our doom is yours now.', 14, 0, 100, 0, 0, 0, 0, 0, 'Doom''rel - rise (TS1)'),
(9039, 2, 0, 'Your doom is sealed!', 14, 0, 100, 0, 0, 0, 0, 0, 'Doom''rel - Doom (TS9)');
