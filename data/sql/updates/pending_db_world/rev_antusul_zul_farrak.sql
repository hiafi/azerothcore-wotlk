-- Zul'Farrak build WP-D2: Antu'sul (8127), the rows dbc-tools cannot declare
-- (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D2; build spec
-- docs/dungeons/zul-farrak-rework.md "Antu'sul", Text). His template (boss_antusul_rework, AIName '', health, immunity
-- 1972), the Servant's (npc_antusul_servant_rework, type 1) and the spells 213890-213919 are apps/dbc-tools
-- source/npcs/zul_farrak/antusul.py; his and the Servant's SmartAI rows go with rev_skeleton_zul_farrak.sql. Area
-- trigger 1447's SmartAI (his wake, s7 #25 A) and the Earthgrab Totem 6066's (seven other creatures still cast 8376)
-- stay. His stock lines 0-2 stay as they are (their use is new: 1 the aggro, 2 every rise after the pull's, 0 the first
-- time three Servants are alive); his loot, spawn and equipment are untouched.

-- AS8 Earthen Shockwave's emote (41: center-screen and in the raid warning area), new.
DELETE FROM `creature_text` WHERE `CreatureID` = 8127 AND `GroupID` = 3;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(8127, 3, 0, '%s draws the stone beneath his feet!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Antu''sul - Earthen Shockwave (AS8)');
