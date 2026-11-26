-- Zul'Farrak build WP-D6: Chief Ukorz Sandscalp (7267) and Ruuzlu (7797), the rows dbc-tools cannot declare
-- (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D6, rule 34; build spec
-- docs/dungeons/zul-farrak-rework.md "Chief Ukorz Sandscalp and Ruuzlu", Build spec "Text"). Their template columns,
-- spells 214070-214093 and the stalkers 301025-301026 are apps/dbc-tools source/npcs/zul_farrak/ukorz.py; their stock
-- smart_scripts rows were dropped by WP-S0's rev_skeleton_zul_farrak.sql. This rev inserts no spawn and no SmartAI row.

-- Ukorz's new lines (groups 0 to 3 are stock and stay: 0 and 3 on a kill, 1 at Frenzy, 2 at the pull). The emote is a
-- boss emote (41), map-wide (TextRange 3): an emote's own range is 25 yd and the mesa is about 80 by 60 yd.
DELETE FROM `creature_text` WHERE `CreatureID` = 7267 AND `GroupID` BETWEEN 4 AND 7;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(7267, 4, 0, 'You spill Sandfury blood? The sands spill yours!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Ukorz - Bladestorm at full Fury (UK3)'),
(7267, 5, 0, 'Not yet, outlander!', 14, 0, 100, 0, 0, 0, 0, 0, 'Ukorz - the 30% hold (UK9, heroic)'),
(7267, 6, 0, 'Sul''thraze! Wake and drink!', 14, 0, 100, 0, 0, 0, 0, 0, 'Ukorz - Call of Sul''thraze (UK10, heroic)'),
(7267, 7, 0, '%s stamps, and the sand opens beneath $n!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Ukorz - Sinking Sands (UK5, at most once every 10 s)');

-- Ruuzlu had no lines.
DELETE FROM `creature_text` WHERE `CreatureID` = 7797 AND `GroupID` BETWEEN 0 AND 2;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(7797, 0, 0, 'For the chief!', 14, 0, 100, 0, 0, 0, 0, 0, 'Ruuzlu - Bladestorm at full Fury (UK3)'),
(7797, 1, 0, 'Not yet!', 14, 0, 100, 0, 0, 0, 0, 0, 'Ruuzlu - the 30% hold (UK9, heroic)'),
(7797, 2, 0, 'Chief! Take it!', 14, 0, 100, 0, 0, 0, 0, 0, 'Ruuzlu - Call of Sul''thraze (UK10, heroic)');
