-- Shadowfang Keep build WP-S6: Deathsworn Captain (3872) (.agents/plans/shadowfang-keep-build/
-- shadowfang-keep-build.HANDOFF.md s3.6 row S6; build spec docs/dungeons/shadowfang-keep-rework.md SK 1044-1083).
-- The rows dbc-tools cannot declare for him; his template columns (ScriptName boss_deathsworn_captain_rework,
-- AIName '', HealthModifier 17, CreatureImmunitiesId 1972) are apps/dbc-tools source/npcs/shadowfang_keep/
-- deathsworn_captain.py.

-- His stock SmartAI goes (read-only SELECTs 2026-11-07: 4 rows, no action lists): id 0 the 85% despawn on AI init
-- (the 15% rare roll is now the instance's, rolled once and saved: DATA_CAPTAIN_ROLL), id 1 Battle Stance 7165, id 2
-- Cleave 15496, id 3 Hamstring 9080. boss_deathsworn_captain_rework replaces them (DC1-DC5). His spawn (134517) and
-- patrol (creature_addon path 1345170) stay.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 3872 AND `source_type` = 0;

-- The mechanic emotes (build spec Text lines 0 and 1; he had no stock lines). Type 41: a boss emote. $n in line 0 is
-- the charge's target.
DELETE FROM `creature_text` WHERE `CreatureID` = 3872 AND `GroupID` IN (0, 1);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(3872, 0, 0, '%s levels his blade at $n and charges!', 41, 0, 100, 0, 0, 0, 0, 0, 'Deathsworn Captain - EMOTE_CAPTAIN_CHARGE (SFK build, DC1)'),
(3872, 1, 0, '%s draws back for a sweeping cleave!', 41, 0, 100, 0, 0, 0, 0, 0, 'Deathsworn Captain - EMOTE_CAPTAIN_CLEAVE (SFK build, DC3)');
