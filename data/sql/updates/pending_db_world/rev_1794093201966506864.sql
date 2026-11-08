-- Shadowfang Keep build WP-S1: Rethilgore (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md s3.6
-- row S1, s2.5). The rows dbc-tools cannot declare; his creature columns, spells and boss-kit creatures are
-- apps/dbc-tools source/npcs/shadowfang_keep/rethilgore.py.

-- Rethilgore 3914: the stock SmartAI goes (Soul Drain 7295 on a random player, the prisoners' data set on death).
-- boss_rethilgore_rework replaces it and keeps the on-death SetData(1, 1) on Ashcrombe 3850 and SetData(1, 2) on
-- Adamant 3849, so their stock escort still opens the Courtyard Door.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 3914 AND `source_type` = 0;

-- The three cell levers (18900, 18901, 101811): action 9 (ACTIVATE_GOBJECT, a toggle) becomes action 118
-- (GO_SET_GO_STATE, state 0 = open), so a pull only ever opens its cell door. Rethilgore's death opens every cell door,
-- and mod-dungeon-clear's courtyard event then pulls a lever: the toggle would close the prisoner back in (s2.5).
DELETE FROM `smart_scripts` WHERE `entryorguid` IN (18900, 18901, 101811) AND `source_type` = 1;
INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`, `event_type`, `event_phase_mask`, `event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, `event_param4`, `event_param5`, `event_param6`, `action_type`, `action_param1`, `action_param2`, `action_param3`, `action_param4`, `action_param5`, `action_param6`, `target_type`, `target_param1`, `target_param2`, `target_param3`, `target_param4`, `target_x`, `target_y`, `target_z`, `target_o`, `comment`) VALUES
(18900, 1, 0, 0, 70, 0, 100, 0, 2, 0, 0, 0, 0, 0, 118, 0, 0, 0, 0, 0, 0, 14, 32445, 18934, 0, 0, 0, 0, 0, 0, 'Lever - On Gameobject State Changed - Set Gameobject State Active (open only)'),
(18901, 1, 0, 0, 70, 0, 100, 0, 2, 0, 0, 0, 0, 0, 118, 0, 0, 0, 0, 0, 0, 14, 33219, 18936, 0, 0, 0, 0, 0, 0, 'Lever - On Gameobject State Changed - Set Gameobject State Active (open only)'),
(101811, 1, 0, 0, 70, 0, 100, 0, 2, 0, 0, 0, 0, 0, 118, 0, 0, 0, 0, 0, 0, 14, 32446, 18935, 0, 0, 0, 0, 0, 0, 'Lever - On Gameobject State Changed - Set Gameobject State Active (open only)');

-- Texts (SK Rethilgore "Text"). Rethilgore: 0 aggro yell, 1 Lock-Up emote ($n the target), 2 the key emote; the
-- mechanic emotes are type 41 (RAID_BOSS_EMOTE, center screen). The cell occupants speak (say, universal language)
-- when a player lands in their cell: Deathstalker Adamant 5, Sorcerer Ashcrombe 5 (their stock groups 0-4 stay),
-- Landen Stilwell 0 (he has no text).
DELETE FROM `creature_text` WHERE `CreatureID` = 3914 AND `GroupID` IN (0, 1, 2);
DELETE FROM `creature_text` WHERE `CreatureID` IN (3849, 3850) AND `GroupID` = 5;
DELETE FROM `creature_text` WHERE `CreatureID` = 17822 AND `GroupID` = 0;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(3914, 0, 0, 'More meat for the cells!', 14, 0, 100, 0, 0, 0, 0, 0, 'Rethilgore - aggro'),
(3914, 1, 0, '%s lunges for $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Rethilgore - Lock-Up (RG1)'),
(3914, 2, 0, '%s''s key ring clatters across the floor!', 41, 0, 100, 0, 0, 0, 0, 0, 'Rethilgore - Cell Key (RG3)'),
(3849, 5, 0, 'Company. Don''t just stand there, break that door!', 12, 0, 100, 0, 0, 0, 0, 0, 'Deathstalker Adamant - a player lands in her cell (Rethilgore RG1)'),
(3850, 5, 0, 'Another guest? Mind the straw. He keeps the bones under it.', 12, 0, 100, 0, 0, 0, 0, 0, 'Sorcerer Ashcrombe - a player lands in his cell (Rethilgore RG1)'),
(17822, 0, 0, 'Stay back! The sickness... I can feel it coming again.', 12, 0, 100, 0, 0, 0, 0, 0, 'Landen Stilwell - a player lands in his cell (Rethilgore RG1)');
