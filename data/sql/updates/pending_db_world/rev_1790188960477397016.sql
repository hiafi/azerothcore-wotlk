-- Priest Shadow rework (docs/reworks/priest-shadow-rework.md sec 4.1) - Tentacle of Madness
-- (300102) visual scale retune: 0.5 -> 0.3 of the Eye Tentacle model's native size, per user
-- request (creature_template/creature_template_model aren't part of apps/dbc-tools' generate.py
-- pipeline - hand-written, same as the original DisplayScale row in
-- rev_1790124445361169072.sql, which this supersedes rather than edits in place).

DELETE FROM `creature_template_model` WHERE `CreatureID` = 300102;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`) VALUES
(300102, 0, 15788, 0.3, 1, 0);
