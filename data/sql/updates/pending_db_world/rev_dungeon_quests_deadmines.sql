-- Dungeon quests stage Q1, the Deadmines (.agents/plans/dungeon-quests/dungeon-quests.PLAN.md section 2, ruled by the
-- designer 2026-11-23; handoff dungeon-quests.STAGE-Q1-DEADMINES-HANDOFF.md). The creatures (300431 Scout Harlan, 300432
-- Sergeant Wynne) and their models are apps/dbc-tools source/npcs/deadmines/dungeon_quests.py; the seven reward items
-- are source/items/deadmines_dungeon_quests.py (ids minted in source/items/item_ids.lock, the item_template, item_dbc
-- and Item.dbc rows are the generated rev); the two quest items' client rows are source/items.csv 70900 / 70901. The
-- three Defias Brotherhood epics are source/items/quest_rewards.lock. Everything below is hand-written: the quest rows,
-- the item_template rows of the two quest items, their loot, the givers' spawns and the starter / ender rows.
--
-- Quest ids 90100 and 90101 are the first of the `dungeon_quest` block (source/ids.yaml 90100-90199).

-- 166 The Defias Brotherhood: the Deadmines open-world quest. XP difficulty 7 -> 9 (300% of a normal quest, the tier
-- of PR #154), still Alliance, chain untouched. Its three choices 6087, 2041 and 2042 become epic in quest_rewards.lock.
UPDATE `quest_template` SET `RewardXPDifficulty` = 9 WHERE `ID` = 166 AND `RewardXPDifficulty` = 7;

-- 2040 Underground Assault and 214 Red Silk Bandanas become neutral dungeon quests (AllowableRaces 1101 -> 0). Their
-- stock givers and enders (Shoni the Shilent, Scout Riell) stay; the entrance giver and the ship NPC are added below.
-- 214 loses its prerequisite 155 (the zone chain's step before the open-world quest; designer 2026-11-23).
UPDATE `quest_template` SET `AllowableRaces` = 0 WHERE `ID` IN (2040, 214) AND `AllowableRaces` = 1101;
UPDATE `quest_template_addon` SET `PrevQuestID` = 0 WHERE `ID` = 214 AND `PrevQuestID` = 155;
-- A quest made neutral loses its reputation rewards (designer 2026-11-24): 2040 gave Stormwind (72) and Gnomeregan
-- Exiles (54) reputation, 214 Stormwind. All five faction slots, values and overrides are cleared, guarded on the stock
-- values. 166 stays Alliance and keeps its reward.
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` = 2040 AND `RewardFactionID1` = 72 AND `RewardFactionValue1` = 7 AND `RewardFactionID2` = 54
    AND `RewardFactionValue2` = 7;
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` = 214 AND `RewardFactionID1` = 72 AND `RewardFactionValue1` = 7;

-- The two quest items. Plain white quest items in the stock mold (Head of VanCleef 3637: class 12, Flags 2048, Bind
-- Quest, unique): 70900 drops from Gilnid, 70901 from Edwin VanCleef. Upserts: item_template rows are never deleted
-- (codestyle-sql not_delete). The class, subclass, display, material and sheath match source/items.csv.
INSERT INTO `item_template` (`entry`, `class`, `subclass`, `SoundOverrideSubclass`, `name`, `displayid`, `Quality`,
    `Flags`, `BuyCount`, `BuyPrice`, `SellPrice`, `InventoryType`, `AllowableClass`, `AllowableRace`, `ItemLevel`,
    `RequiredLevel`, `maxcount`, `stackable`, `bonding`, `description`, `Material`, `sheath`, `VerifiedBuild`) VALUES
(70900, 12, 0, -1, 'Juggernaut Casting Plans', 8624, 1, 2048, 1, 0, 0, 0, -1, -1, 20, 0, 1, 1, 4,
    'The Defias Juggernaut''s casting plans, rolled up and stamped with the foundry''s mark.', -1, 0, 0),
(70901, 12, 0, -1, 'Edwin VanCleef''s Ledger', 1134, 1, 2048, 1, 0, 0, 0, -1, -1, 20, 0, 1, 1, 4,
    'Every deal the Brotherhood has struck, in VanCleef''s own hand.', -1, 0, 0)
    ON DUPLICATE KEY UPDATE `class` = VALUES(`class`), `subclass` = VALUES(`subclass`),
    `SoundOverrideSubclass` = VALUES(`SoundOverrideSubclass`), `name` = VALUES(`name`),
    `displayid` = VALUES(`displayid`), `Quality` = VALUES(`Quality`), `Flags` = VALUES(`Flags`),
    `BuyCount` = VALUES(`BuyCount`), `BuyPrice` = VALUES(`BuyPrice`), `SellPrice` = VALUES(`SellPrice`),
    `InventoryType` = VALUES(`InventoryType`), `AllowableClass` = VALUES(`AllowableClass`),
    `AllowableRace` = VALUES(`AllowableRace`), `ItemLevel` = VALUES(`ItemLevel`),
    `RequiredLevel` = VALUES(`RequiredLevel`), `maxcount` = VALUES(`maxcount`), `stackable` = VALUES(`stackable`),
    `bonding` = VALUES(`bonding`), `description` = VALUES(`description`), `Material` = VALUES(`Material`),
    `sheath` = VALUES(`sheath`);

-- Quest loot: 100%, quest-only (QuestRequired 1), ungrouped, like the stock Head of VanCleef row. Normal entries only:
-- the Deadmines hard mode is not a different creature. It is a loot mode (LOOT_MODE_HARD_MODE_1) on the heroic body
-- (difficulty_entry_1 310004 / 310017, level 60), so nothing spawns on normal under another entry. The heroic lootids
-- 310004 and 310017 carry copies of these rows too: dbc-tools derives them from the normal group 0 (like the Head of
-- VanCleef copy) and the generated rev of this stage already writes them.
DELETE FROM `creature_loot_template` WHERE `Entry` = 1763 AND `Item` = 70900;
DELETE FROM `creature_loot_template` WHERE `Entry` = 639 AND `Item` = 70901;
INSERT INTO `creature_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`, `GroupId`,
    `MinCount`, `MaxCount`, `Comment`) VALUES
(1763, 70900, 0, 100, 1, 1, 0, 1, 1, 'Gilnid - Juggernaut Casting Plans'),
(639, 70901, 0, 100, 1, 1, 0, 1, 1, 'Edwin VanCleef - Edwin VanCleef''s Ledger');

-- The two new quests. QuestType 2, Flags 8 (sharable), QuestInfoID 81 (dungeon), QuestSortID 1581 (The Deadmines), like
-- 2040 Underground Assault. Quest level 20 (Gilnid and VanCleef are level 20), minimum level 15 (the Finder's lowest
-- Deadmines level). Neutral (AllowableRaces 0). The objective is the item (RequiredItemId1). Choice rewards are the
-- generated items (minted ids from item_ids.lock). Upsert: quest_template rows are never deleted (codestyle-sql
-- not_delete).
--   90100 The Juggernaut's Casting Plans: XP difficulty 5, three green choices (cloth caster boots, healer belt, tank
--   shield). 90101 The Kingpin's Ledger: XP difficulty 7, four blue choices (tank neck, physical DPS ring, caster ring,
--   healer neck).
INSERT INTO `quest_template` (`ID`, `QuestType`, `QuestLevel`, `MinLevel`, `QuestSortID`, `QuestInfoID`,
    `RewardXPDifficulty`, `Flags`, `RewardChoiceItemID1`, `RewardChoiceItemQuantity1`, `RewardChoiceItemID2`,
    `RewardChoiceItemQuantity2`, `RewardChoiceItemID3`, `RewardChoiceItemQuantity3`, `RewardChoiceItemID4`,
    `RewardChoiceItemQuantity4`, `AllowableRaces`, `LogTitle`, `LogDescription`, `QuestDescription`, `AreaDescription`,
    `QuestCompletionLog`, `RequiredItemId1`, `RequiredItemCount1`, `ObjectiveText1`, `ObjectiveText2`,
    `ObjectiveText3`, `ObjectiveText4`, `VerifiedBuild`) VALUES
(90100, 2, 20, 15, 1581, 81, 5, 8, 74327, 1, 74328, 1, 74329, 1, 0, 0, 0,
    'The Juggernaut''s Casting Plans',
    'Kill Gilnid in the Deadmines foundry and bring back the Juggernaut''s casting plans.',
    'Every plate, cannonball and rivet on the Defias warship comes out of the foundry, $N, and the foundry answers to a goblin named Gilnid. He keeps the Juggernaut''s casting plans on him so nobody else can run the line.$B$BThe People''s Militia cannot take that ship until we know what it was built to carry. Go down into the mines, put Gilnid out of work and bring me those plans.',
    '',
    'Bring the Juggernaut''s casting plans to the militia in the Deadmines.',
    70900, 1, '', '', '', '', 0),
(90101, 2, 20, 15, 1581, 81, 7, 8, 74330, 1, 74331, 1, 74332, 1, 74333, 1,
    0, 'The Kingpin''s Ledger',
    'Kill Edwin VanCleef aboard the Defias warship and bring back his ledger.',
    'Edwin VanCleef keeps his books the way he keeps his word: close, and in his own hand. Every name that took Brotherhood coin, every farm he shook down in Westfall and every merchant who looked the other way is in that ledger.$B$BThe People''s Militia needs those names, $N. Fight your way to the Juggernaut, take VanCleef down and bring his ledger back to us.',
    '',
    'Bring Edwin VanCleef''s ledger to the militia in the Deadmines.',
    70901, 1, '', '', '', '', 0)
    ON DUPLICATE KEY UPDATE `QuestType` = VALUES(`QuestType`), `QuestLevel` = VALUES(`QuestLevel`),
    `MinLevel` = VALUES(`MinLevel`), `QuestSortID` = VALUES(`QuestSortID`), `QuestInfoID` = VALUES(`QuestInfoID`),
    `RewardXPDifficulty` = VALUES(`RewardXPDifficulty`), `Flags` = VALUES(`Flags`),
    `RewardChoiceItemID1` = VALUES(`RewardChoiceItemID1`),
    `RewardChoiceItemQuantity1` = VALUES(`RewardChoiceItemQuantity1`),
    `RewardChoiceItemID2` = VALUES(`RewardChoiceItemID2`),
    `RewardChoiceItemQuantity2` = VALUES(`RewardChoiceItemQuantity2`),
    `RewardChoiceItemID3` = VALUES(`RewardChoiceItemID3`),
    `RewardChoiceItemQuantity3` = VALUES(`RewardChoiceItemQuantity3`),
    `RewardChoiceItemID4` = VALUES(`RewardChoiceItemID4`),
    `RewardChoiceItemQuantity4` = VALUES(`RewardChoiceItemQuantity4`),
    `AllowableRaces` = VALUES(`AllowableRaces`), `LogTitle` = VALUES(`LogTitle`),
    `LogDescription` = VALUES(`LogDescription`), `QuestDescription` = VALUES(`QuestDescription`),
    `AreaDescription` = VALUES(`AreaDescription`), `QuestCompletionLog` = VALUES(`QuestCompletionLog`),
    `RequiredItemId1` = VALUES(`RequiredItemId1`), `RequiredItemCount1` = VALUES(`RequiredItemCount1`);

DELETE FROM `quest_template_addon` WHERE `ID` IN (90100, 90101);
INSERT INTO `quest_template_addon` (`ID`, `SpecialFlags`) VALUES
(90100, 0),
(90101, 0);

DELETE FROM `quest_offer_reward` WHERE `ID` IN (90100, 90101);
INSERT INTO `quest_offer_reward` (`ID`, `Emote1`, `RewardText`, `VerifiedBuild`) VALUES
(90100, 66, 'Good work, $N. With these casting plans the militia can see where the Brotherhood''s iron goes. Take your pick from what the militia has to spare; you have earned it.', 0),
(90101, 66, 'These are the names we have been looking for. Westfall will remember what you did here, $N. Take your pick of what the militia has to give.', 0);

DELETE FROM `quest_request_items` WHERE `ID` IN (90100, 90101);
INSERT INTO `quest_request_items` (`ID`, `EmoteOnComplete`, `EmoteOnIncomplete`, `CompletionText`, `VerifiedBuild`) VALUES
(90100, 6, 6, 'Did Gilnid give up the casting plans? I need to see them before I can sign off, $N.', 0),
(90101, 6, 6, 'Is that VanCleef''s ledger? Let me see it, $N.', 0);

-- The two quest givers' spawns, normal difficulty only (spawnMask 1: heroic is level 60 and has no dungeon quests),
-- guid = 10 x entry like the other dungeon builds' hand spawns. Normal map 36, phase 1, standing still, 300 s respawn.
--   300431 Scout Harlan, the entrance giver: 4.4 yd off the Dungeon Finder arrival point (areatrigger_teleport 78 /
--     Deadmines Entrance: -16.4, -383.07, 61.78), on the cave room's east side, out of the way of the route to the
--     Mysterious Deadmines Chest (180024, 17 yd west at -32.1, -374.6) and facing the arrival point. Navmesh checked:
--     floor, no creature spawn within 3 yd (the nearest, a Rat 79141, is 4 yd north).
--   300432 Sergeant Wynne, the ship NPC: designer-chosen spot 2026-11-24, picked in game (map 36, area 1582 Ironclad
--     Cove, outdoors, ground and navmesh present): -63.444, -904.762, 15.126, o 2.385. Not moved by the measurements
--     below, which are for the record only (navmesh from ac-worldserver's mmtiles, reachable from VanCleef's poly; 3D
--     distance to the nearest point of each `waypoint_data` path segment of a map 36 spawn, closing segment included,
--     and to every other map 36 `creature` spawn):
--       paths: Cookie's 793440 46.5 yd, Defias Pirate 793520 48.3 yd, Captain Greenskin's unused 793330 77 yd,
--              Squallshaper 793220 114 yd
--       spawns: Cookie 79344 51.2 yd, Defias Pirate 79349 53.2 yd (wanders 5 yd), Goblin Shipbuilder 79347 56.4 yd
--       the ship (VanCleef / Greenskin arena box x -109.5 to -37.5, y -842 to -800.5, z 36 and up): 62.8 yd away;
--       VanCleef's spawn 91 yd, Mr. Smite 115 yd.
DELETE FROM `creature` WHERE `id` IN (300431, 300432) AND `guid` IN (3004310, 3004320);
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(3004310, 300431, 36, 0, 0, 1, 1, 0, -12.800, -380.500, 61.900, 3.7600, 300, 0, 12340, 0,
    'Scout Harlan - Deadmines entrance quest giver'),
(3004320, 300432, 36, 0, 0, 1, 1, 0, -63.444, -904.762, 15.126, 2.3850, 300, 0, 12340, 0,
    'Sergeant Wynne - Deadmines ship quest giver');

-- Starters and enders. The entrance giver starts all four dungeon quests (2040 and 214 stock, 90100 and 90101 new);
-- both NPCs end all four. The stock givers and enders (Shoni the Shilent 6579, Scout Riell 820) keep theirs.
DELETE FROM `creature_queststarter` WHERE `id` IN (300431, 300432) AND `quest` IN (2040, 214, 90100, 90101);
INSERT INTO `creature_queststarter` (`id`, `quest`) VALUES
(300431, 2040),
(300431, 214),
(300431, 90100),
(300431, 90101);

DELETE FROM `creature_questender` WHERE `id` IN (300431, 300432) AND `quest` IN (2040, 214, 90100, 90101);
INSERT INTO `creature_questender` (`id`, `quest`) VALUES
(300431, 2040),
(300431, 214),
(300431, 90100),
(300431, 90101),
(300432, 2040),
(300432, 214),
(300432, 90100),
(300432, 90101);
