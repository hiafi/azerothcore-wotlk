-- Dungeon quests stage Q2, Shadowfang Keep (.agents/plans/dungeon-quests/dungeon-quests.PLAN.md section 3, ruled by the
-- designer 2026-11-23; handoff dungeon-quests.STAGE-Q2-SFK-HANDOFF.md). The creature (300517 Magus Aldren Voss) and
-- its model are apps/dbc-tools source/npcs/shadowfang_keep/dungeon_quests.py; the two reward items are
-- source/items/shadowfang_keep_dungeon_quests.py (ids minted in source/items/item_ids.lock, the item_template,
-- item_dbc and Item.dbc rows are the generated rev); the quest item's client row is source/items.csv 70910.
-- Everything below is hand-written: the three stock quests' changes, the quest item's item_template row, its loot,
-- the new quest with its text, the giver's spawn and the starter / ender rows.
--
-- Quest id 90110 is the first of Shadowfang Keep's slice (source/ids.yaml `dungeon_quest`, 90110-90119).

-- 1098 Deathstalkers in Shadowfang, 1013 The Book of Ur and 1014 Arugal Must Die become neutral dungeon quests
-- (AllowableRaces 690, the Horde races, -> 0). No open-world quest for Shadowfang Keep (designer 2026-11-23): all
-- three are dungeon quests. Rewards, XP difficulty (7), text and stock givers and enders stay: Keeper Bel'dugur
-- (2934, Undercity) still ends 1013, Dalar Dawnweaver (1938, Silverpine) still starts and ends 1014, High Executor
-- Hadrec (1952) still starts 1098. 1098 keeps Deathstalker Vincent (4444, inside, spawn 16260) as its only ender
-- (designer 2026-11-23). None of the three has a prerequisite, a next quest or an exclusive group.
UPDATE `quest_template` SET `AllowableRaces` = 0 WHERE `ID` IN (1098, 1013, 1014) AND `AllowableRaces` = 690;
-- A quest made neutral loses its reputation rewards (designer 2026-11-24): each of the three gave Undercity (68)
-- reputation, 7 points. All five faction slots, values and overrides are cleared, guarded on the stock values.
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` IN (1098, 1013, 1014) AND `RewardFactionID1` = 68 AND `RewardFactionValue1` = 7;

-- Deathstalker Vincent (4444), 1098's only ender, is faction 714 (Horde Generic: hostile to Alliance players,
-- friendly to Horde). 1098 is now neutral, so an Alliance player who takes it at the entrance could only hand it in
-- by beating him to 1% health first (the stock SmartAI 4444 sets faction 35 at 1%), which nothing in the quest tells
-- them. Faction 35 (friendly to both) makes him a plain quest giver for everyone, as the entrance giver is (plan rule
-- 4). His SmartAI stays as it is: its aggro / 1% health events (remove the dead stand state, invincible at 1%, say
-- "Arrgh!", set home position, set faction 35) can no longer fire from a player attack, because a friendly unit
-- cannot be attacked, and the faction 35 action is a no-op. He keeps lying dead (stand state set on reset), npcflag 2
-- and civilian flags_extra. Guarded on the stock faction. His heroic spawn uses the same template
-- (`difficulty_entry_1` 0), so heroic follows.
UPDATE `creature_template` SET `faction` = 35 WHERE `entry` = 4444 AND `faction` = 714;

-- 1013 The Book of Ur and 1014 Arugal Must Die: neutral text (designer 2026-11-24, option B). The stock text is in the
-- Forsaken's voice ("We of the Forsaken", "the Dark Lady") and the quest log lines send the player to Keeper Bel'dugur
-- in the Undercity and Dalar Dawnweaver in Silverpine, but the quest is now also handed in at the Kirin Tor mage at the
-- entrance. The story facts stay (Ur, the book, Arugal's head and spells). The log lines name both enders. 1013's
-- progress text (quest_request_items) is already neutral and stays. Each UPDATE is guarded on the stock text.
-- Locale rows (quest_template_locale and the other `_locale` tables) are not touched.
UPDATE `quest_template` SET `LogDescription` = 'Find the Book of Ur in Shadowfang Keep and bring it to the Kirin Tor mage at the entrance, or to Keeper Bel''dugur at the Apothecarium in the Undercity.',
    `QuestCompletionLog` = 'Return to the Kirin Tor mage at the entrance to Shadowfang Keep, or to Keeper Bel''dugur at the Apothecarium in the Undercity.'
    WHERE `ID` = 1013 AND `LogDescription` = 'Bring the Book of Ur to Keeper Bel''dugur at the Apothecarium in the Undercity.'
    AND `QuestCompletionLog` = 'Return to Keeper Bel''dugur at Apothecarium in the Undercity.';
UPDATE `quest_template` SET `LogDescription` = 'Kill Arugal in Shadowfang Keep and bring his head to the Kirin Tor mage at the entrance, or to Dalar Dawnweaver at the Sepulcher in Silverpine Forest.',
    `QuestCompletionLog` = 'Return to the Kirin Tor mage at the entrance to Shadowfang Keep, or to Dalar Dawnweaver at the Sepulcher in Silverpine Forest.'
    WHERE `ID` = 1014 AND `LogDescription` = 'Kill Arugal and bring his head to Dalar Dawnweaver at the Sepulcher.'
    AND `QuestCompletionLog` = 'Return to Dalar Dawnweaver at The Sepulcher in Silverpine Forest.';
UPDATE `quest_offer_reward` SET `RewardText` = 'Very good. This book will add nicely to the record of the workings of Ur. His knowledge was great, but his conscience held him back from true power. And so when the Scourge came and his strength was tested, it failed.$B$BThose of us who remain cannot afford such weakness, if we are to survive...'
    WHERE `ID` = 1013 AND `RewardText` = 'Very good. This book will add nicely to my collections of the workings of Ur. His knowledge was great, but his conscience held him from true power. And so when the Scourge came and his strength was tested, it failed.$B$BWe of the Forsaken cannot afford such weakness, if we are to survive...';
UPDATE `quest_offer_reward` SET `RewardText` = 'Silverpine Forest is finally free from the vice of that wretch Arugal. You have done a great service to everyone who lives in his shadow, $N. Your tenacity shall be rewarded.'
    WHERE `ID` = 1014 AND `RewardText` = 'Silverpine Forest is finally free from the vice of that wretch Arugal. You have done the Dark Lady a great service, $N. Your tenacity shall be rewarded.';
UPDATE `quest_request_items` SET `CompletionText` = 'With Arugal dead, the lands around his keep can finally be held against the worgen. Do you have his head, $N?'
    WHERE `ID` = 1014 AND `CompletionText` = 'With Arugal''s death we stand to increase the Dark Lady''s stronghold on Lordaeron.';

-- The quest item. A plain white quest item in the stock mold (Head of VanCleef 3637, Mistmantle Family Ring 3629:
-- class 12, Flags 2048, Bind Quest, unique): 70910 drops from Baron Silverlaine. The look is the Mistmantle Family
-- Ring's (display 6538). Upsert: item_template rows are never deleted (codestyle-sql not_delete). The class,
-- subclass, display, material and sheath match source/items.csv.
INSERT INTO `item_template` (`entry`, `class`, `subclass`, `SoundOverrideSubclass`, `name`, `displayid`, `Quality`,
    `Flags`, `BuyCount`, `BuyPrice`, `SellPrice`, `InventoryType`, `AllowableClass`, `AllowableRace`, `ItemLevel`,
    `RequiredLevel`, `maxcount`, `stackable`, `bonding`, `description`, `Material`, `sheath`, `VerifiedBuild`) VALUES
(70910, 12, 0, -1, 'Silverlaine Signet', 6538, 1, 2048, 1, 0, 0, 0, -1, -1, 25, 0, 1, 1, 4,
    'The signet of the house of Silverlaine, black with age.', -1, 0, 0)
    ON DUPLICATE KEY UPDATE `class` = VALUES(`class`), `subclass` = VALUES(`subclass`),
    `SoundOverrideSubclass` = VALUES(`SoundOverrideSubclass`), `name` = VALUES(`name`),
    `displayid` = VALUES(`displayid`), `Quality` = VALUES(`Quality`), `Flags` = VALUES(`Flags`),
    `BuyCount` = VALUES(`BuyCount`), `BuyPrice` = VALUES(`BuyPrice`), `SellPrice` = VALUES(`SellPrice`),
    `InventoryType` = VALUES(`InventoryType`), `AllowableClass` = VALUES(`AllowableClass`),
    `AllowableRace` = VALUES(`AllowableRace`), `ItemLevel` = VALUES(`ItemLevel`),
    `RequiredLevel` = VALUES(`RequiredLevel`), `maxcount` = VALUES(`maxcount`), `stackable` = VALUES(`stackable`),
    `bonding` = VALUES(`bonding`), `description` = VALUES(`description`), `Material` = VALUES(`Material`),
    `sheath` = VALUES(`sheath`);

-- Quest loot: 100%, quest-only (QuestRequired 1), ungrouped (group 0, beside Silverlaine's cloth and food rows), like
-- the stock Head of Arugal row. Normal entry only: Shadowfang Keep's hard mode (Face Him Alone, Archmage Arugal) is a
-- gossip choice on the lair prisoner and a loot mode on the heroic body, and no hard mode spawns Baron Silverlaine
-- under another entry: his normal spawn (guid 16254, spawnMask 3) has difficulty_entry_1 310047, which is the level
-- 60 heroic body (it drops from its own lootid 310047). The heroic lootid carries a copy of this row too: dbc-tools
-- derives it from the normal group 0 (as it does Archmage Arugal's Head of Arugal) and the generated rev of this
-- stage writes it.
DELETE FROM `creature_loot_template` WHERE `Entry` = 3887 AND `Item` = 70910;
INSERT INTO `creature_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`, `GroupId`,
    `MinCount`, `MaxCount`, `Comment`) VALUES
(3887, 70910, 0, 100, 1, 1, 0, 1, 1, 'Baron Silverlaine - Silverlaine Signet');

-- The new quest. QuestType 2, Flags 8 (sharable), QuestInfoID 81 (dungeon), QuestSortID 209 (Shadowfang Keep), like
-- the stock 1098 / 1013 / 1014. Quest level 25 (Baron Silverlaine is level 20, the dungeon's bosses 20 to 21; the
-- designer's ruling 2026-11-24, first 24), minimum level 16 (the Finder's lowest Shadowfang Keep level, the stock
-- quests start at 16 to 18), XP difficulty 7 (as the other three). Neutral (AllowableRaces 0). No money (as stock
-- 1013 / 1014). The objective is the item (RequiredItemId1 70910); the kill is the drop. Choice rewards are the two
-- generated items (minted ids from item_ids.lock: 74334 Silverlaine Retainer's Gloves, 74335 Silverlaine Houseguard's
-- Helm). Upsert: quest_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `quest_template` (`ID`, `QuestType`, `QuestLevel`, `MinLevel`, `QuestSortID`, `QuestInfoID`,
    `RewardXPDifficulty`, `Flags`, `RewardChoiceItemID1`, `RewardChoiceItemQuantity1`, `RewardChoiceItemID2`,
    `RewardChoiceItemQuantity2`, `AllowableRaces`, `LogTitle`, `LogDescription`, `QuestDescription`, `AreaDescription`,
    `QuestCompletionLog`, `RequiredItemId1`, `RequiredItemCount1`, `ObjectiveText1`, `ObjectiveText2`,
    `ObjectiveText3`, `ObjectiveText4`, `VerifiedBuild`) VALUES
(90110, 2, 25, 16, 209, 81, 7, 8, 74334, 1, 74335, 1, 0,
    'The Baron''s Rest',
    'Kill Baron Silverlaine in Shadowfang Keep and bring back the Silverlaine signet.',
    'Arugal was one of ours once, $N, and the Kirin Tor has never stopped answering for what he did here. Baron Silverlaine and his household were among the first his worgen took, and the Baron has relived that night ever since, bound to his hall by the signet of his house.$B$BGo into the keep and give him the rest he was denied. Bring me his signet, so the Kirin Tor can close his line in the records of Dalaran as it deserves.',
    '',
    'Bring the Silverlaine signet to the Kirin Tor mage at the entrance to Shadowfang Keep.',
    70910, 1, '', '', '', '', 0)
    ON DUPLICATE KEY UPDATE `QuestType` = VALUES(`QuestType`), `QuestLevel` = VALUES(`QuestLevel`),
    `MinLevel` = VALUES(`MinLevel`), `QuestSortID` = VALUES(`QuestSortID`), `QuestInfoID` = VALUES(`QuestInfoID`),
    `RewardXPDifficulty` = VALUES(`RewardXPDifficulty`), `Flags` = VALUES(`Flags`),
    `RewardChoiceItemID1` = VALUES(`RewardChoiceItemID1`),
    `RewardChoiceItemQuantity1` = VALUES(`RewardChoiceItemQuantity1`),
    `RewardChoiceItemID2` = VALUES(`RewardChoiceItemID2`),
    `RewardChoiceItemQuantity2` = VALUES(`RewardChoiceItemQuantity2`),
    `AllowableRaces` = VALUES(`AllowableRaces`), `LogTitle` = VALUES(`LogTitle`),
    `LogDescription` = VALUES(`LogDescription`), `QuestDescription` = VALUES(`QuestDescription`),
    `AreaDescription` = VALUES(`AreaDescription`), `QuestCompletionLog` = VALUES(`QuestCompletionLog`),
    `RequiredItemId1` = VALUES(`RequiredItemId1`), `RequiredItemCount1` = VALUES(`RequiredItemCount1`);

DELETE FROM `quest_template_addon` WHERE `ID` = 90110;
INSERT INTO `quest_template_addon` (`ID`, `SpecialFlags`) VALUES
(90110, 0);

DELETE FROM `quest_offer_reward` WHERE `ID` = 90110;
INSERT INTO `quest_offer_reward` (`ID`, `Emote1`, `RewardText`, `VerifiedBuild`) VALUES
(90110, 1, 'Baron Silverlaine''s line ends in peace, and the Kirin Tor will see it written. Thank you, $N. Take what the Council sets aside for those who walk this keep.', 0);

DELETE FROM `quest_request_items` WHERE `ID` = 90110;
INSERT INTO `quest_request_items` (`ID`, `EmoteOnComplete`, `EmoteOnIncomplete`, `CompletionText`,
    `VerifiedBuild`) VALUES
(90110, 1, 0, 'Has the Baron been laid to rest? I cannot record it without his signet, $N.', 0);

-- The entrance giver's spawn, normal difficulty only (spawnMask 1: heroic is level 60 and has no dungeon quests),
-- guid = 10 x entry like the other dungeon builds' hand spawns. Normal map 33, phase 1, standing still, 300 s
-- respawn.
--   300517 Magus Aldren Voss, the entrance giver: -230.170, 2118.133, 78.332, o 4.881. The designer's in-game spot
--     (2026-11-24; indoors, FloorZ 78.332 is a raised floor, GroundZ 76.96), not moved by the measurements below,
--     which are for the record only. Dungeon Finder arrival point: areatrigger_teleport 145 Shadowfang Keep Entrance
--     (-229.135, 2109.18, 76.89, o 1.267; Shadowfang Keep has no lfg_dungeon_template row of its own, the Crown
--     Chemical Co. row at 288 is the holiday boss): the spot is 9.1 yd north of it, on the walkway that climbs to the
--     courtyard. Navmesh (mmtiles read from ac-worldserver): on the mesh, floor 79.29 there. Measured (3D) to the
--     nearest spawns: Black Rat 16234 6.9 yd (a critter that wanders 5 yd), Bleak Worg 3478 10.9 yd but 8.8 yd above
--     him (z 87.1, the floor above), Sorcerer Ashcrombe 3850 12.0 yd and Deathstalker Adamant 3849 14.5 yd (the cell
--     level, z 81.3), the nearest hostile spawn on the same floor Bleak Worg 2114 23.1 yd, Rethilgore 22.7 yd;
--     nearest waypoint path segment Tormented Officer 16445's (path 164450, z 97.5, the floor above) 21.8 yd,
--     Deathsworn Captain 134517's (path 1345170) 23.0 yd; nearest object a cell door (guid 33219) at 19.2 yd. On no
--     patrol path.
DELETE FROM `creature` WHERE `id` = 300517 AND `guid` = 3005170;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(3005170, 300517, 33, 0, 0, 1, 1, 0, -230.170, 2118.133, 78.332, 4.8810, 300, 0, 12340, 0,
    'Magus Aldren Voss - Shadowfang Keep entrance quest giver');

-- Starters and enders. The entrance giver starts all four dungeon quests (1098, 1013 and 1014 stock, 90110 new) and
-- ends 1013, 1014 and 90110. Not 1098: Deathstalker Vincent (4444) stays its only ender, so no creature_questender
-- row for (300517, 1098). The stock givers and enders (High Executor Hadrec 1952, Keeper Bel'dugur 2934, Dalar
-- Dawnweaver 1938, Deathstalker Vincent 4444) keep theirs.
DELETE FROM `creature_queststarter` WHERE `id` = 300517 AND `quest` IN (1098, 1013, 1014, 90110);
INSERT INTO `creature_queststarter` (`id`, `quest`) VALUES
(300517, 1098),
(300517, 1013),
(300517, 1014),
(300517, 90110);

DELETE FROM `creature_questender` WHERE `id` = 300517 AND `quest` IN (1098, 1013, 1014, 90110);
INSERT INTO `creature_questender` (`id`, `quest`) VALUES
(300517, 1013),
(300517, 1014),
(300517, 90110);
