-- Scholomance build WP-S5: Instructor Malicia (10505), the rows dbc-tools cannot declare
-- (.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S5; build spec
-- docs/dungeons/scholomance-rework.md SC 1431-1488). Her template (boss_instructor_malicia_rework, AIName '', health,
-- DamageModifier 3.5, immunities), Malicia's Shade 300536, the Loose Soul 300537 and the spells 206205-206217 are
-- apps/dbc-tools source/npcs/scholomance/instructor_malicia.py.

-- SmartAI 10505 (Call of the Grave 12020, Corruption 18376, Renew 8362, Flash Heal 17843, Heal 15586, Slow 13747 and
-- the death row's SetData(1, 1)) is removed as a full block (SC "Stock kit", approved): boss_instructor_malicia_rework
-- casts Corruption and Slow itself, Shadow Heal replaces Heal, and Call of the Grave, Renew and Flash Heal are retired.
-- Gandling's reveal reads the six instructor boss states (WP-KS), not the stock death row's counter. The Coven's
-- Scholomance Occultists (10472) keep their stock AI (npc_scholomance_occultist and their own SmartAI rows).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10505 AND `source_type` = 0;

-- Texts (SC "Text"; she has none stock): boss emotes (41), so each names its mechanic on screen. $n is the drained
-- player (line 0, normal).
DELETE FROM `creature_text` WHERE `CreatureID` = 10505;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10505, 0, 0, '%s tears the soul from $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Instructor Malicia - Soul Drain (MA2)'),
(10505, 1, 0, '%s tears at the souls of the whole class!', 41, 0, 100, 0, 0, 0, 0, 0, 'Instructor Malicia - Soul Drain, heroic (MA2)'),
(10505, 2, 0, '%s calls a student\'s soul to the front of the class!', 41, 0, 100, 0, 0, 0, 0, 0, 'Instructor Malicia - Call a Student (MA4)'),
(10505, 3, 0, '%s unleashes a storm of souls!', 41, 0, 100, 0, 0, 0, 0, 0, 'Instructor Malicia - Soulstorm (MA6)');
