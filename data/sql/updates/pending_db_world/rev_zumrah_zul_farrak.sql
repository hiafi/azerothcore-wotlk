-- Zul'Farrak build WP-D3: Witch Doctor Zum'rah (7271), the rows dbc-tools cannot declare
-- (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D3; build spec
-- docs/dungeons/zul-farrak-rework.md "Witch Doctor Zum'rah", Text). His template (boss_zumrah_rework, AIName '',
-- health, immunity 1972), the Skeleton 7786's script, the adds 301010-301013 and the spells 213920-213939 are
-- apps/dbc-tools source/npcs/zul_farrak/zumrah.py; his SmartAI rows go with rev_skeleton_zul_farrak.sql. Groups 0 to
-- 2 are stock (aggro, kill, kill again) and stay; area trigger 962 (faction 37) stays. His loot, spawn and equipment
-- are untouched.

-- The boss emotes (41: center-screen and in the raid warning area): ZR1 Spirit Rend (names the walker) and ZR6 a soul
-- bound to his ward (at most once every 10 s).
DELETE FROM `creature_text` WHERE `CreatureID` = 7271 AND `GroupID` IN (3, 4);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(7271, 3, 0, '%s tears $n''s spirit from $g his:her; body!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Witch Doctor Zum''rah - Spirit Rend (ZR1)'),
(7271, 4, 0, 'A lost soul is bound to %s''s ward!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Witch Doctor Zum''rah - A soul bound (ZR6)');
