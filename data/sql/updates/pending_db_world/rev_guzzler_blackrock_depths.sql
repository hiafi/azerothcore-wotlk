-- Blackrock Depths build WP-D17: the Grim Guzzler room, the SmartAI rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D17; build spec
-- docs/dungeons/blackrock-depths-4-imperial-seat.md S4 66-216, 428-435, 635-641; rulings 61-69).
-- The room stays on SmartAI. Their templates (health, DamageModifier, immunity 1972 on Ribbly and Plugger) and the two
-- spell copies below (211410, 211411) are apps/dbc-tools source/npcs/blackrock_depths/guzzler.py; the numbers are
-- GuzzlerLogic.h. Only five rows change, the rest of every block is the live stock row (event_flags kept as stock; no
-- row is new, so rule 14's `event_flags | 4` does not apply). The credit rows 240 / 241 are WP-H's.
--
--   9543 Ribbly Screwspigot  id 4  Gouge 12540 -> the 2 s copy 211410 (S4 ruling 62; it lands on the tank every 10 s)
--   9499 Plugger Spazzring   id 3  Shadow Bolt 12739 repeat 3-4 s -> 8-10 s (ruling 69, the patron change of ruling 65)
--   9545 Grim Patron         id 0  Kick 15610 -> the 3 s lockout copy 211411 (ruling 65: the stock spell may be shared)
--   9547 Guzzling Patron     id 1  Shadow Bolt 20825 repeat 3-4 s -> 8-10 s (ruling 65)
--   9554 Hammered Patron     id 0  Backhand 6253 repeat 5-8 s -> 10-12 s (ruling 65)
--
-- Ribbly's Cronies 10043 (Eviscerate, Sinister Strike), Plugger's Curse of Tongues / Immolate / Demon Armor, the theft
-- counter, the actionlist 949900, the death faction rows (9499 ids 9-12) and the patrons' ale formation rows are
-- untouched.

-- Ribbly Screwspigot 9543 (6 rows)
DELETE FROM `smart_scripts` WHERE `entryorguid` = 9543 AND `source_type` = 0;
INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`, `event_type`, `event_phase_mask`,
    `event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, `event_param4`, `event_param5`,
    `event_param6`, `action_type`, `action_param1`, `action_param2`, `action_param3`, `action_param4`, `action_param5`,
    `action_param6`, `target_type`, `target_param1`, `target_param2`, `target_param3`, `target_param4`, `target_x`,
    `target_y`, `target_z`, `target_o`, `comment`) VALUES
(9543, 0, 0, 1, 62, 0, 100, 512, 1970, 0, 0, 0, 0, 0, 2, 14, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'On Gossip Select - Set Faction'),
(9543, 0, 1, 2, 61, 0, 100, 512, 0, 0, 0, 0, 0, 0, 2, 14, 0, 0, 0, 0, 0, 11, 10043, 30, 0, 0, 0, 0, 0, 0,
    'On Gossip Select - Set Faction'),
(9543, 0, 2, 3, 61, 0, 100, 512, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'On Gossip Select - Talk'),
(9543, 0, 3, 0, 61, 0, 100, 512, 0, 0, 0, 0, 0, 0, 49, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0,
    'On Gossip Select - Attack Start'),
(9543, 0, 4, 0, 0, 0, 100, 0, 3000, 3000, 10000, 10000, 0, 0, 11, 211410, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,
    'IC Update - cast Gouge (2 s copy, 211410) on victim'),
(9543, 0, 5, 0, 0, 0, 100, 0, 1000, 1000, 5000, 5000, 0, 0, 11, 9080, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,
    'IC Update - cast spell on victim');

-- Plugger Spazzring 9499 (15 rows)
DELETE FROM `smart_scripts` WHERE `entryorguid` = 9499 AND `source_type` = 0;
INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`, `event_type`, `event_phase_mask`,
    `event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, `event_param4`, `event_param5`,
    `event_param6`, `action_type`, `action_param1`, `action_param2`, `action_param3`, `action_param4`, `action_param5`,
    `action_param6`, `target_type`, `target_param1`, `target_param2`, `target_param3`, `target_param4`, `target_x`,
    `target_y`, `target_z`, `target_o`, `comment`) VALUES
(9499, 0, 0, 0, 1, 0, 100, 0, 7000, 15000, 35000, 45000, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Plugger Spazzring - OOC - Say text 1'),
(9499, 0, 1, 0, 0, 0, 100, 0, 3000, 5000, 15000, 18000, 0, 0, 11, 13338, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,
    'Plugger Spazzring - In Combat - Cast ''Curse of Tongues'''),
(9499, 0, 2, 0, 0, 0, 100, 0, 5000, 7000, 12000, 15000, 0, 0, 11, 12742, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,
    'Plugger Spazzring - In Combat - Cast ''Immolate'''),
(9499, 0, 3, 0, 0, 0, 100, 0, 1000, 2000, 8000, 10000, 0, 0, 11, 12739, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,
    'Plugger Spazzring - In Combat - Cast ''Shadow Bolt'' (repeat 8-10 s)'),
(9499, 0, 4, 0, 23, 0, 100, 0, 13787, 0, 10000, 10000, 0, 0, 11, 13787, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Plugger Spazzring - On aura missing - Cast ''Demon Armor'''),
(9499, 0, 5, 0, 4, 0, 100, 0, 0, 0, 0, 0, 0, 0, 1, 3, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0,
    'Plugger Spazzring - On aggro - Say text 4'),
(9499, 0, 6, 7, 38, 0, 100, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Plugger Spazzring - On Data set - Say text 2'),
(9499, 0, 7, 0, 61, 0, 100, 512, 0, 0, 0, 0, 0, 0, 63, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Plugger Spazzring - On Data set - Increment counter1'),
(9499, 0, 8, 0, 77, 0, 100, 512, 1, 3, 0, 0, 0, 0, 80, 949900, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Plugger Spazzring - On counter set- Actionlist'),
(9499, 0, 9, 0, 6, 0, 100, 512, 0, 0, 0, 0, 0, 0, 2, 14, 0, 0, 0, 0, 0, 11, 9554, 100, 0, 0, 0, 0, 0, 0,
    'Plugger Spazzring - On Death  - Set faction'),
(9499, 0, 10, 0, 6, 0, 100, 512, 0, 0, 0, 0, 0, 0, 2, 14, 0, 0, 0, 0, 0, 11, 9545, 100, 0, 0, 0, 0, 0, 0,
    'Plugger Spazzring - On Death  - Set faction'),
(9499, 0, 11, 0, 6, 0, 100, 512, 0, 0, 0, 0, 0, 0, 2, 14, 0, 0, 0, 0, 0, 11, 9547, 100, 0, 0, 0, 0, 0, 0,
    'Plugger Spazzring - On Death  - Set faction'),
(9499, 0, 12, 0, 6, 0, 100, 512, 0, 0, 0, 0, 0, 0, 2, 14, 0, 0, 0, 0, 0, 11, 9502, 100, 0, 0, 0, 0, 0, 0,
    'Plugger Spazzring - On Death  - Set faction'),
(9499, 0, 13, 0, 4, 0, 100, 0, 0, 0, 0, 0, 0, 0, 83, 130, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Plugger Spazzring - On Aggro - Remove Npc Flags Questgiver & Vendor'),
(9499, 0, 14, 0, 25, 0, 100, 0, 0, 0, 0, 0, 0, 0, 82, 130, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Plugger Spazzring - On Reset - Add Npc Flags Questgiver & Vendor');

-- Grim Patron 9545 (14 rows)
DELETE FROM `smart_scripts` WHERE `entryorguid` = 9545 AND `source_type` = 0;
INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`, `event_type`, `event_phase_mask`,
    `event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, `event_param4`, `event_param5`,
    `event_param6`, `action_type`, `action_param1`, `action_param2`, `action_param3`, `action_param4`, `action_param5`,
    `action_param6`, `target_type`, `target_param1`, `target_param2`, `target_param3`, `target_param4`, `target_x`,
    `target_y`, `target_z`, `target_o`, `comment`) VALUES
(9545, 0, 0, 0, 105, 0, 25, 0, 3000, 5000, 5000, 8000, 0, 5, 11, 211411, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0,
    'Grim Patron - In Combat - Cast ''Kick'' (3 s lockout copy, 211411)'),
(9545, 0, 1, 0, 2, 0, 100, 1, 0, 30, 0, 0, 0, 0, 11, 14822, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Grim Patron - Between 0-30% Health - Cast ''Drunken Rage'' (No Repeat)'),
(9545, 0, 2, 0, 1, 0, 55, 0, 7000, 15000, 7000, 15000, 0, 0, 10, 1, 4, 11, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Grim Patron - OOC - Play Random Emotes'),
(9545, 0, 3, 0, 38, 0, 100, 0, 1, 1, 0, 0, 0, 0, 49, 0, 0, 0, 0, 0, 0, 21, 30, 0, 0, 0, 0, 0, 0, 0,
    'Grim Patron - On Data Set 1 1 - Start Attack'),
(9545, 0, 4, 0, 38, 0, 100, 512, 1, 4, 0, 0, 0, 0, 80, 954501, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Grim Patron - On Data Set 1 4 - Wait Before Moving to Dark Iron Ale Mug'),
(9545, 0, 5, 8, 4, 0, 100, 0, 0, 0, 0, 0, 0, 0, 83, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Grim Patron - On Aggro - Remove Npc Flags Gossip'),
(9545, 0, 6, 8, 25, 0, 100, 0, 0, 0, 0, 0, 0, 0, 82, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Grim Patron - On Reset - Add Npc Flags Gossip'),
(9545, 0, 7, 0, 34, 0, 100, 0, 8, 1, 0, 0, 0, 0, 80, 954500, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Grim Patron - On Reached Dark Iron Ale Mug - Run Action List'),
(9545, 0, 8, 14, 61, 0, 100, 0, 0, 0, 0, 0, 0, 0, 45, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Grim Patron - On Linked Event - Clear Dark Iron Ale State'),
(9545, 0, 10, 0, 25, 0, 100, 0, 0, 0, 0, 0, 0, 0, 35, 101, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Grim Patron - On Reset - Reform Patron Group'),
(9545, 0, 11, 0, 21, 0, 100, 0, 0, 0, 0, 0, 0, 0, 35, 103, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Grim Patron - On Reached Home - Restore Emote State'),
(9545, 0, 12, 0, 25, 0, 100, 0, 0, 0, 0, 0, 0, 0, 80, 0, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Grim Patron - On Reset - Cancel Drink Sequence'),
(9545, 0, 13, 0, 6, 0, 100, 0, 0, 0, 0, 0, 0, 0, 80, 0, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Grim Patron - On Death - Cancel Drink Sequence'),
(9545, 0, 14, 0, 61, 0, 100, 0, 0, 0, 0, 0, 0, 0, 80, 0, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Grim Patron - On Linked Event - Cancel Drink Sequence');

-- Guzzling Patron 9547 (15 rows)
DELETE FROM `smart_scripts` WHERE `entryorguid` = 9547 AND `source_type` = 0;
INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`, `event_type`, `event_phase_mask`,
    `event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, `event_param4`, `event_param5`,
    `event_param6`, `action_type`, `action_param1`, `action_param2`, `action_param3`, `action_param4`, `action_param5`,
    `action_param6`, `target_type`, `target_param1`, `target_param2`, `target_param3`, `target_param4`, `target_x`,
    `target_y`, `target_z`, `target_o`, `comment`) VALUES
(9547, 0, 0, 0, 0, 0, 100, 0, 1000, 2000, 15000, 15000, 0, 0, 11, 14868, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,
    'Guzzling Patron - In Combat - Cast ''Curse of Agony'''),
(9547, 0, 1, 0, 0, 0, 100, 0, 3000, 4000, 8000, 10000, 0, 0, 11, 20825, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,
    'Guzzling Patron - In Combat - Cast ''Shadow Bolt'' (repeat 8-10 s)'),
(9547, 0, 2, 0, 2, 0, 100, 1, 0, 30, 0, 0, 0, 0, 11, 14822, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Guzzling Patron - Between 0-30% Health - Cast ''Drunken Rage'' (No Repeat)'),
(9547, 0, 3, 0, 1, 0, 55, 0, 7000, 15000, 7000, 15000, 0, 0, 10, 1, 4, 11, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Guzzling Patron - OOC - Play Random Emotes'),
(9547, 0, 4, 0, 38, 0, 100, 0, 1, 1, 0, 0, 0, 0, 49, 0, 0, 0, 0, 0, 0, 21, 30, 0, 0, 0, 0, 0, 0, 0,
    'Guzzling Patron - On Data Set 1 1 - Start Attack'),
(9547, 0, 5, 0, 38, 0, 100, 512, 1, 4, 0, 0, 0, 0, 80, 954701, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Guzzling Patron - On Data Set 1 4 - Wait Before Moving to Dark Iron Ale Mug'),
(9547, 0, 6, 9, 4, 0, 100, 0, 0, 0, 0, 0, 0, 0, 83, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Guzzling Patron - On Aggro - Remove Npc Flags Gossip'),
(9547, 0, 7, 9, 25, 0, 100, 0, 0, 0, 0, 0, 0, 0, 82, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Guzzling Patron - On Reset - Add Npc Flags Gossip'),
(9547, 0, 8, 0, 34, 0, 100, 0, 8, 1, 0, 0, 0, 0, 80, 954700, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Guzzling Patron - On Reached Dark Iron Ale Mug - Run Action List'),
(9547, 0, 9, 15, 61, 0, 100, 0, 0, 0, 0, 0, 0, 0, 45, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Guzzling Patron - On Linked Event - Clear Dark Iron Ale State'),
(9547, 0, 11, 0, 25, 0, 100, 0, 0, 0, 0, 0, 0, 0, 35, 101, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Guzzling Patron - On Reset - Reform Patron Group'),
(9547, 0, 12, 0, 21, 0, 100, 0, 0, 0, 0, 0, 0, 0, 35, 103, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Guzzling Patron - On Reached Home - Restore Emote State'),
(9547, 0, 13, 0, 25, 0, 100, 0, 0, 0, 0, 0, 0, 0, 80, 0, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Guzzling Patron - On Reset - Cancel Drink Sequence'),
(9547, 0, 14, 0, 6, 0, 100, 0, 0, 0, 0, 0, 0, 0, 80, 0, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Guzzling Patron - On Death - Cancel Drink Sequence'),
(9547, 0, 15, 0, 61, 0, 100, 0, 0, 0, 0, 0, 0, 0, 80, 0, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Guzzling Patron - On Linked Event - Cancel Drink Sequence');

-- Hammered Patron 9554 (13 rows)
DELETE FROM `smart_scripts` WHERE `entryorguid` = 9554 AND `source_type` = 0;
INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`, `event_type`, `event_phase_mask`,
    `event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, `event_param4`, `event_param5`,
    `event_param6`, `action_type`, `action_param1`, `action_param2`, `action_param3`, `action_param4`, `action_param5`,
    `action_param6`, `target_type`, `target_param1`, `target_param2`, `target_param3`, `target_param4`, `target_x`,
    `target_y`, `target_z`, `target_o`, `comment`) VALUES
(9554, 0, 0, 0, 0, 0, 100, 0, 3000, 5000, 10000, 12000, 0, 0, 11, 6253, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,
    'Hammered Patron - In Combat - Cast ''Backhand'' (repeat 10-12 s)'),
(9554, 0, 1, 0, 2, 0, 100, 1, 0, 30, 0, 0, 0, 0, 11, 14822, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Hammered Patron - Between 0-30% Health - Cast ''Drunken Rage'' (No Repeat)'),
(9554, 0, 2, 7, 4, 0, 100, 0, 0, 0, 0, 0, 0, 0, 83, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Hammered Patron - On Aggro - Remove Npc Flags Gossip'),
(9554, 0, 3, 0, 1, 0, 55, 0, 7000, 15000, 7000, 15000, 0, 0, 10, 1, 4, 11, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Hammered Patron - OOC - Play Random Emotes'),
(9554, 0, 4, 0, 38, 0, 100, 512, 1, 4, 0, 0, 0, 0, 80, 955401, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Hammered Patron - On Data Set 1 4 - Wait Before Moving to Dark Iron Ale Mug'),
(9554, 0, 5, 7, 25, 0, 100, 0, 0, 0, 0, 0, 0, 0, 82, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Hammered Patron - On Reset - Add Npc Flags Gossip'),
(9554, 0, 6, 0, 34, 0, 100, 0, 8, 1, 0, 0, 0, 0, 80, 955400, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Hammered Patron - On Reached Dark Iron Ale Mug - Run Action List'),
(9554, 0, 7, 13, 61, 0, 100, 0, 0, 0, 0, 0, 0, 0, 45, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Hammered Patron - On Linked Event - Clear Dark Iron Ale State'),
(9554, 0, 9, 0, 25, 0, 100, 0, 0, 0, 0, 0, 0, 0, 35, 101, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Hammered Patron - On Reset - Reform Patron Group'),
(9554, 0, 10, 0, 21, 0, 100, 0, 0, 0, 0, 0, 0, 0, 35, 103, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Hammered Patron - On Reached Home - Restore Emote State'),
(9554, 0, 11, 0, 25, 0, 100, 0, 0, 0, 0, 0, 0, 0, 80, 0, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Hammered Patron - On Reset - Cancel Drink Sequence'),
(9554, 0, 12, 0, 6, 0, 100, 0, 0, 0, 0, 0, 0, 0, 80, 0, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Hammered Patron - On Death - Cancel Drink Sequence'),
(9554, 0, 13, 0, 61, 0, 100, 0, 0, 0, 0, 0, 0, 0, 80, 0, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Hammered Patron - On Linked Event - Cancel Drink Sequence');
