-- Zul'Farrak build WP-D4a: the Sandfury Executioner (7274) and the Block, the rows dbc-tools cannot declare
-- (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D4a; build spec
-- docs/dungeons/zul-farrak-rework.md "The Pyramid", Text). His template (boss_sandfury_executioner_rework, AIName '',
-- health, immunity -93 -> 1972), the Pyramid stalker 301019 and the spells 213960-213989 are apps/dbc-tools
-- source/npcs/zul_farrak/sandfury_executioner.py; his SmartAI rows go with rev_skeleton_zul_farrak.sql. His stock lines
-- 0 (aggro) and 1 (kill) stay as they are; his loot (the cage key), spawn and equipment are untouched.

-- PY1 the Block: the yell naming the prisoner as he tears them from the cage, new.
DELETE FROM `creature_text` WHERE `CreatureID` = 7274 AND `GroupID` = 2;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(7274, 2, 0, 'To the block, $n!', 14, 0, 100, 0, 0, 0, 0, 0, 'Sandfury Executioner - the Block (PY1)');
