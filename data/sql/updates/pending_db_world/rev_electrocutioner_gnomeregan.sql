-- Gnomeregan build WP-D3: Electrocutioner 6000 (6235), the rows dbc-tools cannot declare
-- (.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.5 row D3, rule 35; build spec
-- docs/dungeons/gnomeregan-rework.md "Electrocutioner 6000", Text). His template (boss_electrocutioner_rework, AIName
-- '', health, DamageModifier 1.7, immunity 1972, flags), the Blast Stalker 301132 and the spells 214380-214393 are
-- apps/dbc-tools source/npcs/gnomeregan/electrocutioner.py; his SmartAI rows and his wander (0) go with WP-S0's
-- rev_skeleton_gnomeregan.sql. His loot (the Workshop Key 6893 at 100%) and equipment are untouched.

-- The texts. The stock group 0 ("Electric justice!", yell, sound 5811, broadcast 6177; SP line 1) stays as it is
-- (rule 35) and moves in use from the aggro to the execution (EL2). New: the aggro yell (SP line 0, group 1) and the
-- boss emotes (type 41: center-screen and in the raid warning area) of the execution, the donut (SP line 2) and the
-- heroic circle (SP line 3).
DELETE FROM `creature_text` WHERE `CreatureID` = 6235 AND `GroupID` BETWEEN 1 AND 3;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(6235, 1, 0, 'Court is in session!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Electrocutioner 6000 - aggro'),
(6235, 2, 0, '%s reaches 6000 volts! Get under the machine!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Electrocutioner 6000 - Electric Justice, the donut (EL2)'),
(6235, 3, 0, '%s overloads! Get away from the machine!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Electrocutioner 6000 - Electric Justice, the circle (EL2, heroic)');
