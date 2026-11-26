-- Zul'Farrak build, the quests WP (Q; .agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md 4.Q and section 7
-- #50-#55, all ruled "as recommended" 2026-11-25; spec .agents/plans/dungeon-quests/dungeon-quests.PLAN.md section 7,
-- ruled by the designer 2026-11-23). The creature (301090 Kizzi Fuseboot) and its model are apps/dbc-tools
-- source/npcs/zul_farrak/dungeon_quests.py; the sixteen reward items are source/items/zul_farrak_dungeon_quests.py (the
-- item_template, item_dbc and Item.dbc rows and the item ids are the deploy's write run; this file is named so it
-- sorts after every `rev_<digits>.sql`). Everything below is hand-written: the quests' changes, the log text, the
-- giver's spawn and weapon, the starter / ender rows. No new quest id (nothing in 90100-90199), no new item_template
-- row of its own. The reward items are set by id, never looked up by name (Ragefire Chasm R-Q-m1): the ids are the
-- ones the write run mints for the `zfq_*` keys of apps/dbc-tools/source/items/item_ids.lock (74997-75012 at the time
-- of writing: the lock's next ids after the gear and the Gnomeregan tail), and
-- apps/dbc-tools/lib/test_zul_farrak_dungeon_quests.py pins them against the lock once the write run has minted them.
--
-- The five dungeon quests (2865, 3042, 2846, 2768, 2770) were already neutral (AllowableRaces 0), with no prerequisite
-- and no exclusive group, and their stock givers and enders stay (Tran'rek 7876, Trenton Lighthammer 7804, Tabetha
-- 6546, Chief Engineer Bilgewhizzle 7407, Wizzle Brassbolts 4453); so only their text and rewards change. Reputation
-- stays: 2865 and 2768 pay Gadgetzan (369) 7, a faction both sides can earn (section 7 #52 A). Money stays as the stock
-- copper (section 7 #50 A): 2865 6,500 (65 silver), 3042 19,500 (1 gold 95 silver), 2846 6,500, 2770 7,500; the plan
-- read copper as gold. The three open-world quests keep their stock giver, ender, chain and faction (3527 after 3520
-- and before 4787, 2936 after 2935 and before 2937, 2991 after 2990 and before 2992) and their reputation.

-- XP difficulty (RewardXPDifficulty N reads questxp_dbc Difficulty_(N+1)): 3527 The Prophecy of Mosh'aru 7 -> 9
-- (9,050 at level 47 -> 18,120: 3x difficulty 5, the capstone's), 2991 Nekrum's Medallion 7 -> 8 (9,050 -> 12,080) and
-- 2936 The Spider God 7 -> 8 (8,300 -> 11,080 at level 45).
UPDATE `quest_template` SET `RewardXPDifficulty` = 9 WHERE `ID` = 3527 AND `RewardXPDifficulty` = 7;
UPDATE `quest_template` SET `RewardXPDifficulty` = 8 WHERE `ID` IN (2936, 2991) AND `RewardXPDifficulty` = 7;

-- Reward choices (section 7 #54 A). 3527: an epic choice of three shoulders (Str plate, Agi leather, Int cloth), item
-- level 57 (user 2026-11-26); the stock reward is nothing. 2936 (Horde) and 2991 (Alliance): a blue choice of three
-- wrists each (Str plate, Agi leather, Int cloth), item level 52 both (user 2026-11-26); the stock reward is nothing
-- (2991 keeps its 70 silver).
-- 2865 Scarab Shells: a green choice, an Agility leather belt or a Strength plate belt, item level 50. 3042 Troll
-- Temper: a green choice, an Intellect cloth or a Spirit (healer) cloth pair of boots, item level 50. 2768 Divino-matic
-- Rod: the stock blues 9533 and 9534 stay in slots 1 and 2, three blues join them (Str plate legs, Agi leather
-- shoulders, tank plate boots), item level 52. 2846 (Spellshifter Rod 9527) and 2770 (Carrot on a Stick 11122) keep
-- their stock reward item. Each UPDATE is guarded on the stock values.
UPDATE `quest_template` SET
    `RewardChoiceItemID1` = 74997,
    `RewardChoiceItemQuantity1` = 1,
    `RewardChoiceItemID2` = 74998,
    `RewardChoiceItemQuantity2` = 1,
    `RewardChoiceItemID3` = 74999,
    `RewardChoiceItemQuantity3` = 1
    WHERE `ID` = 3527 AND `RewardChoiceItemID1` = 0 AND `RewardChoiceItemID2` = 0 AND `RewardChoiceItemID3` = 0;
UPDATE `quest_template` SET
    `RewardChoiceItemID1` = 75000,
    `RewardChoiceItemQuantity1` = 1,
    `RewardChoiceItemID2` = 75001,
    `RewardChoiceItemQuantity2` = 1,
    `RewardChoiceItemID3` = 75002,
    `RewardChoiceItemQuantity3` = 1
    WHERE `ID` = 2936 AND `RewardChoiceItemID1` = 0 AND `RewardChoiceItemID2` = 0 AND `RewardChoiceItemID3` = 0;
UPDATE `quest_template` SET
    `RewardChoiceItemID1` = 75003,
    `RewardChoiceItemQuantity1` = 1,
    `RewardChoiceItemID2` = 75004,
    `RewardChoiceItemQuantity2` = 1,
    `RewardChoiceItemID3` = 75005,
    `RewardChoiceItemQuantity3` = 1
    WHERE `ID` = 2991 AND `RewardChoiceItemID1` = 0 AND `RewardChoiceItemID2` = 0 AND `RewardChoiceItemID3` = 0;
UPDATE `quest_template` SET
    `RewardChoiceItemID1` = 75006,
    `RewardChoiceItemQuantity1` = 1,
    `RewardChoiceItemID2` = 75007,
    `RewardChoiceItemQuantity2` = 1
    WHERE `ID` = 2865 AND `RewardChoiceItemID1` = 0 AND `RewardChoiceItemID2` = 0;
UPDATE `quest_template` SET
    `RewardChoiceItemID1` = 75008,
    `RewardChoiceItemQuantity1` = 1,
    `RewardChoiceItemID2` = 75009,
    `RewardChoiceItemQuantity2` = 1
    WHERE `ID` = 3042 AND `RewardChoiceItemID1` = 0 AND `RewardChoiceItemID2` = 0;
UPDATE `quest_template` SET
    `RewardChoiceItemID3` = 75010,
    `RewardChoiceItemQuantity3` = 1,
    `RewardChoiceItemID4` = 75011,
    `RewardChoiceItemQuantity4` = 1,
    `RewardChoiceItemID5` = 75012,
    `RewardChoiceItemQuantity5` = 1
    WHERE `ID` = 2768 AND `RewardChoiceItemID1` = 9533 AND `RewardChoiceItemID2` = 9534
    AND `RewardChoiceItemID3` = 0 AND `RewardChoiceItemID4` = 0 AND `RewardChoiceItemID5` = 0;

-- Text (section 7 #55 A). The stock texts stay except the two log lines that send a Finder player to a town: the quests
-- are now also given and handed in at the goblin at the entrance, so `LogDescription` and `QuestCompletionLog` of the
-- five dungeon quests name her first and the stock ender second. The giver / ender, objective and reward text are the
-- stock lines (they are already neutral Gadgetzan and open-world voices). The three open-world quests keep their text.
-- Each UPDATE is guarded on the stock text. Locale rows (the `_locale` tables) are not touched.
UPDATE `quest_template` SET `LogDescription` = 'Bring 5 Uncracked Scarab Shells to Kizzi Fuseboot at the entrance to Zul''Farrak, or to Tran''rek in Gadgetzan.',
    `QuestCompletionLog` = 'Return to Kizzi Fuseboot at the entrance to Zul''Farrak, or to Tran''rek in Tanaris.'
    WHERE `ID` = 2865 AND `LogDescription` = 'Bring 5 Uncracked Scarab Shells to Tran''rek in Gadgetzan.';
UPDATE `quest_template` SET `LogDescription` = 'Bring 20 Vials of Troll Temper to Kizzi Fuseboot at the entrance to Zul''Farrak, or to Trenton Lighthammer in Gadgetzan.',
    `QuestCompletionLog` = 'Return to Kizzi Fuseboot at the entrance to Zul''Farrak, or to Trenton Lighthammer in Tanaris.'
    WHERE `ID` = 3042 AND `LogDescription` = 'Bring 20 Vials of Troll Temper to Trenton Lighthammer in Gadgetzan.';
UPDATE `quest_template` SET `LogDescription` = 'Bring the Tiara of the Deep to Kizzi Fuseboot at the entrance to Zul''Farrak, or to Tabetha in Dustwallow Marsh.',
    `QuestCompletionLog` = 'Return to Kizzi Fuseboot at the entrance to Zul''Farrak, or to Tabetha at The Quagmire in Dustwallow Marsh.'
    WHERE `ID` = 2846 AND `LogDescription` = 'Bring the Tiara of the Deep to Tabetha in Dustwallow Marsh.';
UPDATE `quest_template` SET `LogDescription` = 'Bring the Divino-matic Rod to Kizzi Fuseboot at the entrance to Zul''Farrak, or to Chief Engineer Bilgewhizzle in Gadgetzan.',
    `QuestCompletionLog` = 'Return to Kizzi Fuseboot at the entrance to Zul''Farrak, or to Chief Engineer Bilgewhizzle in Tanaris.'
    WHERE `ID` = 2768 AND `LogDescription` = 'Bring the Divino-matic Rod to Chief Engineer Bilgewhizzle in Gadgetzan.';
UPDATE `quest_template` SET `LogDescription` = 'Bring Gahz''rilla''s Electrified Scale to Kizzi Fuseboot at the entrance to Zul''Farrak, or to Wizzle Brassbolts in the Shimmering Flats.',
    `QuestCompletionLog` = 'Return to Kizzi Fuseboot at the entrance to Zul''Farrak, or to Wizzle Brassbolts at Mirage Raceway in Thousand Needles.'
    WHERE `ID` = 2770 AND `LogDescription` = 'Bring Gahz''rilla''s Electrified Scale to Wizzle Brassbolts in the Shimmering Flats.';

-- Kizzi Fuseboot's weapon and off-hand: Tran'rek's own pair (a basic metal hammer, a red bag), as the Gadgetzan goblin
-- she is modeled on stands. Equipment id 1 is the creature's own row (CreatureID 301090, ID 1).
DELETE FROM `creature_equip_template` WHERE `CreatureID` = 301090;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
(301090, 1, 1903, 12857, 0, 0);

-- The entrance giver's spawn, normal difficulty only (spawnMask 1: heroic is level 60 and has no dungeon quests; the
-- dungeon's `normal_only_creatures` keeps the heroic mask off it), guid = 10 x entry like the other dungeon builds'
-- hand spawns. Map 209, phase 1, standing still, 300 s respawn.
--   301090 Kizzi Fuseboot, the entrance giver: 1219.16, 848.49, 10.05, o 4.71. The designer's in-game spot
--     (2026-11-24; z is the floor as given: the floor mesh reads 11.68 and the terrain 10.1, section 7 #53 A, the
--     playtest guide checks it), not moved by the measurements below, which are for the record only. Dungeon Finder
--     arrival point: areatrigger_teleport 924 Zul'Farrak Entrance (1213.52, 841.59, 8.93, o 6.09): the spot is 9.0 yd
--     from it (3D). Measured (3D, live creature table 2026-11-25) to the nearest spawns: Sandfury Blood Drinker 38006
--     42.4 yd (standing still, detection 20), Sandfury Shadowcaster 38003 43.6 yd and 38007 47.4 yd (standing still);
--     each is outside its own aggro range. Nearest waypoint path (the closing segment included, 3D point to segment):
--     path 426020 (Sandfury Shadowcaster 42602) 66.9 yd, every other patrol within 150 yd farther: on no patrol path.
--     No gameobject within 40 yd. No hostility event, scripted brawl or SmartAI in range.
DELETE FROM `creature` WHERE `id` = 301090 AND `guid` = 3010900;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(3010900, 301090, 209, 0, 0, 1, 1, 1, 1219.16, 848.49, 10.05, 4.71, 300, 0, 12340, 0,
    'Kizzi Fuseboot - Zul''Farrak entrance quest giver');

-- Starters and enders. The entrance giver starts and ends the five dungeon quests. The stock givers and enders
-- (Tran'rek 7876, Trenton Lighthammer 7804, Tabetha 6546, Chief Engineer Bilgewhizzle 7407, Wizzle Brassbolts 4453)
-- keep theirs.
-- She starts and ends none of the three open-world quests: 3527, 2936 and 2991 are turned in at their stock enders
-- (Yeh'kinya 8579, Master Gadrin 3188, Thadius Grimshade 8022).
DELETE FROM `creature_queststarter` WHERE `id` = 301090 AND `quest` IN (2865, 3042, 2846, 2768, 2770);
INSERT INTO `creature_queststarter` (`id`, `quest`) VALUES
(301090, 2865),
(301090, 3042),
(301090, 2846),
(301090, 2768),
(301090, 2770);

DELETE FROM `creature_questender` WHERE `id` = 301090 AND `quest` IN (2865, 3042, 2846, 2768, 2770);
INSERT INTO `creature_questender` (`id`, `quest`) VALUES
(301090, 2865),
(301090, 3042),
(301090, 2846),
(301090, 2768),
(301090, 2770);
