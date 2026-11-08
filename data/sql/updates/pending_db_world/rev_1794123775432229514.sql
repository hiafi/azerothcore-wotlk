-- Scholomance build WP-S1: Jandice Barov (10503), the rows dbc-tools cannot declare
-- (.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S1; build spec SC 546-601). Her template
-- (boss_jandice_barov_rework, AIName '', health, DamageModifier, immunities), the Shell Game copy 11439's columns, the
-- Reflection 300530 and the spells are apps/dbc-tools source/npcs/scholomance/jandice_barov.py.

-- SmartAI 10503 goes (Curse of Blood 16098, Banish 8994, Summon Illusions 17773, the invisibility rows): the build spec
-- retires Banish and Summon Illusions and folds the invisibility into the Shell Game. boss_jandice_barov_rework keeps
-- the death emote (text group 0, stock) and the journal 26096. 11439 has no SmartAI rows.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10503 AND `source_type` = 0;

-- Texts: group 0 (the stock death emote, type 16) stays; the mechanic emotes are boss emotes (41), so they name the
-- mechanic on screen.
DELETE FROM `creature_text` WHERE `CreatureID` = 10503 AND `GroupID` IN (1, 2, 3);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10503, 1, 0, '%s vanishes into a crowd of her own reflections!', 41, 0, 100, 0, 0, 0, 0, 0, 'Jandice Barov - The Shell Game (JB2)'),
(10503, 2, 0, '%s calls her reflections to draw their sigils!', 41, 0, 100, 0, 0, 0, 0, 0, 'Jandice Barov - Blood Sigil (JB1)'),
(10503, 3, 0, '%s''s reflections line the wall, blood pooling in their hands!', 41, 0, 100, 0, 0, 0, 0, 0, 'Jandice Barov - Bloodlines (JB6)');

-- The Reflection of Jandice Barov 300530 holds her journal (item 12866, as 10503 and 11439 do): ID 1. The boss loads
-- it on a real reflection and clears it on the heroic decoy (LoadEquipment(0)); the Shell Game copies clear theirs.
DELETE FROM `creature_equip_template` WHERE `CreatureID` = 300530 AND `ID` = 1;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
(300530, 1, 12866, 0, 0, 0);
