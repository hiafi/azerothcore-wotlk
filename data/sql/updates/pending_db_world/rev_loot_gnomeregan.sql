-- Gnomeregan build WP-L-1: the loot the DSL cannot declare (apps/dbc-tools' loot DSL writes creature list groups and
-- row cuts only; the lists, the hard mode group, the shared rare list's removal and the cut rows are
-- apps/dbc-tools source/items/gnomeregan_loot.py). Handoff s7 #42 A, #43 A and #44 A, gear ruling G27 A;
-- docs/dungeons/gnomeregan-rework.md "Loot".

-- Techbot (301105, the new boss; lootid 301105 is set in source/npcs/gnomeregan/techbot.py): a copy of the outside
-- Techbot's (6231) ungrouped rows and world pool, less the CPU Shell (it is on his list now) and the three 0.04% rows
-- of moved items (cut). The Memory Core (quest 2922) and the Guts (quest 2928) drop at 100% to a player on the quest;
-- the two creature_questitem rows are the loot window glow (the heroic body 310575 needs no row of its own: a heroic
-- creature keeps its normal entry as its object entry, so the client queries 301105). His list is group 1 (the DSL).
-- The deletes name the groups this rev owns, so the DSL's group 1 is never touched whichever file runs first.
DELETE FROM `creature_loot_template` WHERE `Entry` = 301105 AND `GroupId` IN (0, 5);
INSERT INTO `creature_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`,
    `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES
(301105, 4363, 0, 1.3502, 0, 1, 0, 1, 1, 'Techbot - Copper Modulator'),
(301105, 4364, 0, 1.7, 0, 1, 0, 1, 1, 'Techbot - Coarse Blasting Powder'),
(301105, 4371, 0, 1.5, 0, 1, 0, 1, 1, 'Techbot - Bronze Tube'),
(301105, 4377, 0, 3.4599, 0, 1, 0, 1, 1, 'Techbot - Heavy Blasting Powder'),
(301105, 4382, 0, 1.34, 0, 1, 0, 1, 1, 'Techbot - Bronze Framework'),
(301105, 9277, 0, 100, 1, 1, 0, 1, 1, 'Techbot - Techbot''s Memory Core'),
(301105, 9309, 0, 100, 1, 1, 0, 1, 1, 'Techbot - Robo-mechanical Guts'),
(301105, 1, 1000026, 0, 0, 1, 5, 1, 1, 'Techbot - (ReferenceTable)');
DELETE FROM `creature_questitem` WHERE `CreatureEntry` = 301105;
INSERT INTO `creature_questitem` (`CreatureEntry`, `Idx`, `ItemId`, `VerifiedBuild`) VALUES
(301105, 0, 9277, 0),
(301105, 1, 9309, 0);

-- Crowd Pummeler 9-60 (6229): his body carries nothing (#42 A), so his table is deleted and his lootid and gold are
-- zeroed (a creature naming a deleted table is a boot ERROR and a log line per kill; his heroic copy reads the
-- replayed normal row). His chest holds the list and the three rows his body held (Guts 5% for quest 2928, the DELTA
-- card 1%, Schematic: Lil' Smoky 50%): GO 301380 on normal (D5's template, Data1 = the GO's own id) at the Normal tier
-- and 301381 on heroic at the Heroic tier. gameobject_loot_template is keyed (Entry, Item): every item once per chest.
DELETE FROM `creature_loot_template` WHERE `Entry` = 6229;
UPDATE `creature_template` SET `lootid` = 0, `mingold` = 0, `maxgold` = 0 WHERE `entry` = 6229;
DELETE FROM `gameobject_loot_template` WHERE `Entry` IN (301380, 301381);
INSERT INTO `gameobject_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`,
    `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES
(301380, 9449, 0, 0, 0, 1, 1, 1, 1, 'Pummeler Prize Strongbox - Manual Crowd Pummeler (Normal)'),
(301380, 9450, 0, 0, 0, 1, 1, 1, 1, 'Pummeler Prize Strongbox - Gnomebot Operating Boots (Normal)'),
(301380, 9490, 0, 0, 0, 1, 1, 1, 1, 'Pummeler Prize Strongbox - Gizmotron Megachopper (Normal)'),
(301380, 74908, 0, 0, 0, 1, 1, 1, 1, 'Pummeler Prize Strongbox - Piston-driven Legplates (Normal)'),
(301380, 74913, 0, 0, 0, 1, 1, 1, 1, 'Pummeler Prize Strongbox - Shock Absorber Pads (Normal)'),
(301380, 74918, 0, 0, 0, 1, 1, 1, 1, 'Pummeler Prize Strongbox - Grease Monkey''s Jerkin (Normal)'),
(301380, 74923, 0, 0, 0, 1, 1, 1, 1, 'Pummeler Prize Strongbox - Piston Fist (Normal)'),
(301380, 74928, 0, 0, 0, 1, 1, 1, 1, 'Pummeler Prize Strongbox - Ringside Bell (Normal)'),
(301380, 9309, 0, 5, 1, 1, 0, 8, 10, 'Pummeler Prize Strongbox - Robo-mechanical Guts'),
(301380, 9327, 0, 1, 0, 1, 0, 1, 1, 'Pummeler Prize Strongbox - Security DELTA Data Access Card'),
(301380, 11827, 0, 50, 0, 1, 0, 1, 1, 'Pummeler Prize Strongbox - Schematic: Lil'' Smoky'),
(301381, 74896, 0, 0, 0, 1, 1, 1, 1, 'Pummeler Prize Strongbox (heroic) - Manual Crowd Pummeler (Heroic)'),
(301381, 74900, 0, 0, 0, 1, 1, 1, 1, 'Pummeler Prize Strongbox (heroic) - Gnomebot Operating Boots (Heroic)'),
(301381, 74904, 0, 0, 0, 1, 1, 1, 1, 'Pummeler Prize Strongbox (heroic) - Gizmotron Megachopper (Heroic)'),
(301381, 74909, 0, 0, 0, 1, 1, 1, 1, 'Pummeler Prize Strongbox (heroic) - Piston-driven Legplates (Heroic)'),
(301381, 74914, 0, 0, 0, 1, 1, 1, 1, 'Pummeler Prize Strongbox (heroic) - Shock Absorber Pads (Heroic)'),
(301381, 74919, 0, 0, 0, 1, 1, 1, 1, 'Pummeler Prize Strongbox (heroic) - Grease Monkey''s Jerkin (Heroic)'),
(301381, 74924, 0, 0, 0, 1, 1, 1, 1, 'Pummeler Prize Strongbox (heroic) - Piston Fist (Heroic)'),
(301381, 74929, 0, 0, 0, 1, 1, 1, 1, 'Pummeler Prize Strongbox (heroic) - Ringside Bell (Heroic)'),
(301381, 9309, 0, 5, 1, 1, 0, 8, 10, 'Pummeler Prize Strongbox (heroic) - Robo-mechanical Guts'),
(301381, 9327, 0, 1, 0, 1, 0, 1, 1, 'Pummeler Prize Strongbox (heroic) - Security DELTA Data Access Card'),
(301381, 11827, 0, 50, 0, 1, 0, 1, 1, 'Pummeler Prize Strongbox (heroic) - Schematic: Lil'' Smoky');

-- G27 A: the Gnomeregan Amulet (10299) is the Mobile Alert System boss's list item; the 1.1% in the Sparklematic-
-- Wrapped Box (ilvl 1, with the Gnomeregan Band) goes. The Band stays.
DELETE FROM `item_loot_template` WHERE `Entry` = 9363 AND `Item` = 10299;

-- #43 A: the White Punch Card (9279, the start of the hard mode's chain) at its stock 10% from the four inside kin of
-- the five stock droppers (all five stand outside the dungeon): the Irradiated Pillager, Caverndeep Burrower,
-- Caverndeep Reaver and Caverndeep Ambusher, 90 spawns, about 9 cards a section 1 clear.
DELETE FROM `creature_loot_template` WHERE `Entry` IN (6206, 6207, 6211, 6329) AND `Item` = 9279;
INSERT INTO `creature_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`,
    `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES
(6329, 9279, 0, 10, 0, 1, 0, 1, 1, 'Irradiated Pillager - White Punch Card'),
(6206, 9279, 0, 10, 0, 1, 0, 1, 1, 'Caverndeep Burrower - White Punch Card'),
(6211, 9279, 0, 10, 0, 1, 0, 1, 1, 'Caverndeep Reaver - White Punch Card'),
(6207, 9279, 0, 10, 0, 1, 0, 1, 1, 'Caverndeep Ambusher - White Punch Card');

-- #44 A: the Grime-Encrusted Ring (9326, starts quest 2945) also drops at the Dark Iron Agent's stock 8% from the
-- Caverndeep Burrower and Reaver (38 spawns in section 1), so a section 1 run can do the quest end to end. The Agents
-- (section 2) keep theirs.
DELETE FROM `creature_loot_template` WHERE `Entry` IN (6206, 6211) AND `Item` = 9326;
INSERT INTO `creature_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`,
    `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES
(6206, 9326, 0, 8, 0, 1, 0, 1, 1, 'Caverndeep Burrower - Grime-Encrusted Ring'),
(6211, 9326, 0, 8, 0, 1, 0, 1, 1, 'Caverndeep Reaver - Grime-Encrusted Ring');
