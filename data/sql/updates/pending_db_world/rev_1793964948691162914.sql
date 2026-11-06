-- Deadmines Pilot WP-B4: Gilnid (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md s3.5 row B4; build spec
-- docs/dungeons/deadmines-rework.md "Gilnid", Text table). The rows dbc-tools cannot declare; Gilnid's template
-- columns, the iron shot, the land mine and the spells are apps/dbc-tools source/npcs/deadmines/gilnid.py.

-- SmartAI 1763 is replaced by boss_gilnid_rework (modules/mod-dungeon-bosses): Molten Metal on the victim and the out
-- of combat say every 120 s move into C++; the Foundry Door (guid 26182) opens through instance_deadmines_rework's
-- door data on BOSS_GILNID DONE. The whole block goes (dbc-tools already sets AIName '').
DELETE FROM `smart_scripts` WHERE `entryorguid` = 1763 AND `source_type` = 0;

-- Texts: group 0 (the stock out of combat say, two lines) stays as it is; groups 1-5 are new (build spec Text table,
-- approved 2026-10-28). Line 1 has two variants, picked at random.
DELETE FROM `creature_text` WHERE `CreatureID` = 1763 AND `GroupID` BETWEEN 1 AND 5;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(1763, 1, 0, 'Shot''s ready! Roll it out!', 14, 0, 100, 0, 0, 0, 0, 0, 'Gilnid - Roll Out the Shot'),
(1763, 1, 1, 'Load ''em up, it''s going to the ship!', 14, 0, 100, 0, 0, 0, 0, 0, 'Gilnid - Roll Out the Shot'),
(1763, 2, 0, 'Double shift, you lazy oafs!', 14, 0, 100, 0, 0, 0, 0, 0, 'Gilnid - Double shift (heroic, below 50%)'),
(1763, 3, 0, '%s tosses a landmine!', 41, 0, 100, 0, 0, 0, 0, 0, 'Gilnid - Landmine (heroic)'),
(1763, 4, 0, 'Back to work! And somebody deal with these intruders!', 14, 0, 100, 0, 0, 0, 0, 0, 'Gilnid - Aggro'),
(1763, 5, 0, 'Watch where you roll those!', 14, 0, 100, 0, 0, 0, 0, 0, 'Gilnid - Bowled Over');
