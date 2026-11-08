-- Scholomance build WP-S9: Lord Alexei Barov (10504), the rows dbc-tools cannot declare
-- (.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S9; build spec
-- docs/dungeons/scholomance-rework.md SC 2460-2533). His template (boss_lord_alexei_barov_rework, AIName '', health,
-- DamageModifier 6.0, immunities), the Barov Fortune 300543 and the spells 206290-206302 are apps/dbc-tools
-- source/npcs/scholomance/lord_alexei_barov.py.

-- SmartAI 10504 (Unholy Aura 17467 on reset, Immolate 20294, Veil of Shadow 17820, the death's SetData(1, 1)) is
-- removed (SC "Stock kit", approved). The C++ casts Unholy Aura on aggro (not on reset) and Veil of Shadow as a
-- tank-only copy (206302); Immolate is retired; the boss state replaces the stock death counter (Gandling's reveal).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10504 AND `source_type` = 0;

-- His Risen Guards leave the fight (SC "Encounter": "Removed from his formation"): formation 48863 (leader) with
-- members 48862 and 48864, and their linked respawn on him.
DELETE FROM `creature_formations` WHERE `leaderGUID` = 48863 OR `memberGUID` IN (48862, 48863, 48864);
DELETE FROM `linked_respawn` WHERE `guid` IN (48862, 48864) AND `linkType` = 0;

-- ... and stand guard at the vault door as trash (SC design: "Unlink them: they stand guard at the vault door as
-- trash"; user ruling 2, 2026-11-08). Stock they stood 4-5 yd from him, so faction 233's call for help still pulled
-- them in. Now they flank the gate corridor (the navmesh's walkable strip there is x 179.8-182.8, floor z 75.6), 6 yd
-- inside gate 177373 (181.1, -21.3), facing the study: 35.5 yd from AlexeiArena()'s center (182.5, -63; radius 33),
-- 63 yd from him, 30 yd from the Risen Warriors, 22 yd from Gandling, far from the detention landing
-- (179.1, -91.1), and outside the dungeon-clear sealed boxes of Alexei (y -97 to -32) and Gandling (y -22 to 20).
UPDATE `creature` SET `position_x` = 180.0, `position_y` = -27.5, `position_z` = 75.6, `orientation` = 1.5708
WHERE `guid` = 48862 AND `id` = 10489;
UPDATE `creature` SET `position_x` = 182.5, `position_y` = -27.5, `position_z` = 75.6, `orientation` = 1.5708
WHERE `guid` = 48864 AND `id` = 10489;

-- Texts (SC "Text"; he has none stock): the aggro and death yells, one yell per rule (4 is Out of bounds, 5 and 6 the
-- heroic rules), and the Demerit as a boss emote (41, center screen; $n is the punished player).
DELETE FROM `creature_text` WHERE `CreatureID` = 10504;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10504, 0, 0, 'Out of your rooms after curfew? The dean will see to you personally.', 14, 0, 100, 0, 0, 0, 0, 0, 'Lord Alexei Barov - aggro'),
(10504, 1, 0, 'No running in the halls!', 14, 0, 100, 0, 0, 0, 0, 0, 'Lord Alexei Barov - No running (AB2)'),
(10504, 2, 0, 'Assembly!', 14, 0, 100, 0, 0, 0, 0, 0, 'Lord Alexei Barov - Assembly (AB3)'),
(10504, 3, 0, 'Keep your distance!', 14, 0, 100, 0, 0, 0, 0, 0, 'Lord Alexei Barov - Keep your distance (AB4)'),
(10504, 4, 0, 'Go to the corner!', 14, 0, 100, 0, 0, 0, 0, 0, 'Lord Alexei Barov - Out of bounds (AB5)'),
(10504, 5, 0, 'Line up!', 14, 0, 100, 0, 0, 0, 0, 0, 'Lord Alexei Barov - Line up (AB6, heroic)'),
(10504, 6, 0, 'To your desks!', 14, 0, 100, 0, 0, 0, 0, 0, 'Lord Alexei Barov - To your desks (AB7, heroic)'),
(10504, 7, 0, '%s marks a demerit against $n.', 41, 0, 100, 0, 0, 0, 0, 0, 'Lord Alexei Barov - Demerit (AB9)'),
(10504, 8, 0, 'Detention for you all...', 14, 0, 100, 0, 0, 0, 0, 0, 'Lord Alexei Barov - death');
