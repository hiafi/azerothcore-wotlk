-- Stratholme build WP-S6: Archivist Galford (10811), the rows dbc-tools cannot declare
-- (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S6; build spec
-- docs/dungeons/stratholme-rework.md ST 1707-1765). His template (boss_archivist_galford_rework, AIName '', health,
-- DamageModifier 3.5, immunities, INSTANCE_BIND), the stalkers 300606-300607 and his spells 206520-206535 are
-- apps/dbc-tools source/npcs/stratholme/archivist_galford.py. The Scarlet Archive 176245 and his book (creature_equip
-- 12742) are untouched.

-- SmartAI 10811 (Burning Winds 17293, Fire Nova 17366, Pyroblast 17274) is removed (ST "Stock kit", approved
-- 2026-11-03): boss_archivist_galford_rework reworks all three (GF3, GF5, GF11).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10811 AND `source_type` = 0;

-- Texts (ST "Text"; none stock): the yells are type 14; the Fire Nova line is a boss emote (41), so it names the
-- moment on screen.
DELETE FROM `creature_text` WHERE `CreatureID` = 10811;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10811, 0, 0, 'Heretics in the archive!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Archivist Galford - Aggro, the walls light (GF10)'),
(10811, 1, 0, '%s''s robes kindle with holy flame!', 41, 0, 100, 0, 0, 0, 0, 0, 'Archivist Galford - Fire Nova (GF5)'),
(10811, 2, 0, 'The Light''s fire feeds me!', 14, 0, 100, 0, 0, 0, 0, 0, 'Archivist Galford - First Kindled (GF9)'),
(10811, 3, 0, 'Burn, heretic!', 14, 0, 100, 0, 0, 0, 0, 0, 'Archivist Galford - Pyroblast (GF3)'),
(10811, 4, 0, 'Not the archive!', 14, 0, 100, 0, 0, 0, 0, 0, 'Archivist Galford - First puddle in the archive'),
(10811, 5, 0, 'Winds, carry them to the Pyre!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Archivist Galford - Burning Winds (GF11, heroic)'),
(10811, 6, 0, 'My records... all ash...', 14, 0, 100, 0, 0, 0, 0, 0, 'Archivist Galford - Death');
