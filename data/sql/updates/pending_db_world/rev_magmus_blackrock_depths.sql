-- Blackrock Depths build WP-D22: Magmus (9938) and the six Ironhand Guardians (8982), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D22; build spec
-- docs/dungeons/blackrock-depths-4-imperial-seat.md "Magmus"). His template (boss_magmus_rework, AIName '', 170k,
-- INSTANCE_BIND), the statues' ScriptName (npc_ironhand_guardian_rework) and spells 211580-211591 are
-- apps/dbc-tools source/npcs/blackrock_depths/magmus.py. Neither unit has a smart_scripts row (live SELECT 2026-11-17:
-- none for 9938 or 8982), so there is nothing to drop; the six statues keep their spawns (guids 47323, 47442, 47466,
-- 47472, 47473, 47474, spawnMask 1: the heroic rollout copies them) and Magmus keeps guid 47477. This rev inserts no
-- creature spawn and no SmartAI row (rule 14: nothing for the heroic spawn mask to miss).

-- His texts (S4 "Text"): group 0 is the stock braziers yell (the instance says it; untouched). Group 1 is a boss emote
-- (type 41, rule 2) as the fist goes up, groups 2 and 3 are yells (the Flame Wall, his death). All map-wide (TextRange
-- 3): the Iron Hall is 170 yd long, a yell's own range is 300 yd but an emote's is 25.
DELETE FROM `creature_text` WHERE `CreatureID` = 9938 AND `GroupID` BETWEEN 1 AND 3;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9938, 1, 0, '%s raises his fist, and the Ironhand Guardians turn!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Magmus - Crossfire (MG3)'),
(9938, 2, 0, 'Burn in the Emperor''s hall!', 14, 0, 100, 0, 0, 0, 0, 3, 'Magmus - Flame Wall (MG4)'),
(9938, 3, 0, 'The Emperor... will not... be disturbed...', 14, 0, 100, 0, 0, 0, 0, 3, 'Magmus - death');
