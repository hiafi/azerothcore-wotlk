-- Stratholme build WP-S12: Maleki the Pallid (10438), the rows dbc-tools cannot declare
-- (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S12; build spec
-- docs/dungeons/stratholme-rework.md ST 3160-3211). His template (boss_maleki_the_pallid_rework, AIName '', health,
-- DamageModifier 3.5, immunities, flags_extra), the Ice Tomb 300584, the eye stalker 300585 and his spells are
-- apps/dbc-tools source/npcs/stratholme/maleki_the_pallid.py.

-- SmartAI 10438 (Frostbolt 17503, Ice Tomb 16869, Drain Life 17238, Banshee Curse 16867, and on death instance data 3
-- set to 1) is removed (ST "Stock kit", approved, ruling 50): boss_maleki_the_pallid_rework keeps Frostbolt, reworks
-- Ice Tomb (MK4) and Drain Life (MK3), and retires Banshee Curse; the rework instance writes the third ziggurat's data
-- on his death itself (instance_stratholme_rework, WP-S0).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10438 AND `source_type` = 0;

-- Texts (ST "Text"; none stock): yells are 14, the mechanic lines boss emotes (41), so they name the mechanic on
-- screen. $n is the cursed player (1), the Siphon's carrier (2) and the frozen player (4).
DELETE FROM `creature_text` WHERE `CreatureID` = 10438;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10438, 0, 0, 'Come closer. You are all so very warm.', 14, 0, 100, 0, 0, 0, 0, 0, 'Maleki the Pallid - aggro'),
(10438, 1, 0, '%s whispers a frozen curse at $n.', 41, 0, 100, 0, 0, 0, 0, 0, 'Maleki the Pallid - Icy Death (MK1)'),
(10438, 2, 0, '%s turns his staff on $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Maleki the Pallid - The Siphon (MK3)'),
(10438, 3, 0, 'Let the cold take you!', 14, 0, 100, 0, 0, 0, 0, 0, 'Maleki the Pallid - Eye of the Blizzard (MK5)'),
(10438, 4, 0, '$n is frozen solid!', 41, 0, 100, 0, 0, 0, 0, 0, 'Maleki the Pallid - Ice Tomb (MK4)'),
(10438, 5, 0, 'Kel''Thuzad... promised...', 14, 0, 100, 0, 0, 0, 0, 0, 'Maleki the Pallid - death');
