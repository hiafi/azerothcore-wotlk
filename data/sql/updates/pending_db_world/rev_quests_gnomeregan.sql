-- Gnomeregan build, the quests WP (Q; .agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md 4.Q and section 7
-- #45-#50, all ruled "as recommended" 2026-11-26; spec the dungeon doc's Dungeon quests section and
-- docs/dungeons/boss-rework-systems.md section 14). The creature (301190 Tinkmaster Fizzbolt) and its four displays are
-- apps/dbc-tools source/npcs/gnomeregan/dungeon_quests.py; the eleven reward items are
-- source/items/gnomeregan_dungeon_quests.py (the item_template, item_dbc and Item.dbc rows, the creature_template row
-- and the item ids are the deploy's write run; this file is named so it sorts after every `rev_<digits>.sql`).
-- Everything below is hand-written: the quests' changes, the neutral text, the two static spawns, the starter and ender
-- rows, the Prismatic Punch Card's duration. No new quest id (nothing in 90100-90199), no new item_template row of its
-- own. The reward items are set by id, never looked up by name (Ragefire Chasm R-Q-m1): the ids are the ones the write
-- run mints for the `gnq_*` keys of apps/dbc-tools/source/items/item_ids.lock (75013-75023 at the time of writing: the
-- lock's next ids after the Zul'Farrak quest rewards), and apps/dbc-tools/lib/test_gnomeregan_dungeon_quests.py pins
-- them against the lock once the write run has minted them (the deploy gate: run it between the write run and
-- db-import, with GNQ_REQUIRE_MINTED=1). Each reward UPDATE also carries a fail-closed name guard: it applies only
-- when item_template.entry N already has the expected name, so a shifted id leaves the quest unchanged instead of
-- paying another item. The guard is a check, not a lookup: the id is still a literal.
--
-- The matrix Punchograph 3005-A copy inside (ruling 62, s7 #34 A: (-502.5, 67.2, -154.8, o 5.70), GO guid 3013800) is
-- WP-S0's rev_skeleton_gnomeregan.sql, not repeated here. The two End spots (-538.76, 527.40, -216.27, o 3.89) and
-- (-607.63, 677.98, -327.04, o 6.21) are summoned by the instance (instance_gnomeregan_rework.cpp, NPC_EXILE) on
-- normal only and restored after a restart; they have no row here.

-- The Prismatic Punch Card (9316, the Data Rescue objective and the Whole Workshop's console key) expires after 20
-- hours of real time (ruling 43; stock: no duration). `duration` is in seconds; `flagsCustom` bit 1
-- (ITEM_FLAGS_CU_DURATION_REAL_TIME) keeps the clock running while the player is offline (the stock REAL_DURATION flag
-- 0x10000 is not implemented in this core). Data Rescue still turns in with the card: the quest's required-item check
-- counts the item in the bags whatever its duration, `TurnInQuest` destroys it by entry, and an expired card is
-- destroyed (the quest goes incomplete again, as for any quest item that is lost). Testers clear Cache\WDB (the item
-- query carries the duration).
UPDATE `item_template` SET `duration` = 72000, `flagsCustom` = `flagsCustom` | 1
    WHERE `entry` = 9316 AND `duration` = 0;

-- The six dungeon quests become neutral (AllowableRaces 1101, the five Alliance races, or 690, the Horde races, -> 0).
-- 2945 is neutral already. 2922 Save Techbot's Brain!, 2924, 2928, 2930 and 2929 were Alliance, 2841 Rig Wars Horde.
UPDATE `quest_template` SET `AllowableRaces` = 0
    WHERE `ID` IN (2922, 2924, 2928, 2929, 2930) AND `AllowableRaces` = 1101;
UPDATE `quest_template` SET `AllowableRaces` = 0 WHERE `ID` = 2841 AND `AllowableRaces` = 690;

-- A quest made neutral loses its reputation rewards (designer 2026-11-24): 2922 gave Gnomeregan Exiles (54) 6; 2924,
-- 2929 and 2930 gave Gnomeregan Exiles 7; 2928 gave Stormwind (72) 7 and Gnomeregan Exiles 7; 2841 gave Orgrimmar (76)
-- 7. All five faction slots, values and overrides are cleared, guarded on the stock values. 2945 gives none.
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` = 2922 AND `RewardFactionID1` = 54 AND `RewardFactionValue1` = 6;
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` IN (2924, 2929, 2930) AND `RewardFactionID1` = 54 AND `RewardFactionValue1` = 7;
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` = 2928 AND `RewardFactionID1` = 72 AND `RewardFactionValue1` = 7
    AND `RewardFactionID2` = 54 AND `RewardFactionValue2` = 7;
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` = 2841 AND `RewardFactionID1` = 76 AND `RewardFactionValue1` = 7;

-- Minimum level inside the Finder band (walkthrough check 5): the dungeon's levels are 23 to 33, and 2924 (24), 2930
-- (25), 2841 (25), 2929 (25) and 2945 (28) shut out the first levels. All five come down to 23; the Grime-Encrusted
-- Ring itself (9326, the starter, RequiredLevel 28) with 2945, or a level 23 to 27 player could not use it.
-- 2922 (20) and 2928 (20) are inside the band already.
UPDATE `quest_template` SET `MinLevel` = 23 WHERE `ID` IN (2841, 2924, 2929, 2930, 2945) AND `MinLevel` > 23;
UPDATE `item_template` SET `RequiredLevel` = 23 WHERE `entry` = 9326 AND `RequiredLevel` = 28;

-- 2922 Save Techbot's Brain!: the breadcrumb Tinkmaster Overspark (2923) stops being a prerequisite (zone context
-- only). 2923's RewardNextQuest 2922 stays, so the Stormwind flow still hands out 2922 the stock way. The Memory Core
-- (9277) drops from the new Techbot (301105, 100%, QuestRequired 1: WP-L-1's rev_loot_gnomeregan.sql) and stays on the
-- outside Techbot (6231).
UPDATE `quest_template_addon` SET `PrevQuestID` = 0 WHERE `ID` = 2922 AND `PrevQuestID` = 2923;

-- Breadcrumbs (designer call DQ1 B, orchestrator ruling 2026-11-26). 2923 Tinkmaster Overspark is the stock breadcrumb
-- of 2922, 2925 Klockmort's Essentials of 2924 and 2931 Castpipe's Task of 2930 (all Alliance only).
-- Player::SatisfyQuestBreadcrumb refuses a quest while one of its breadcrumbs is incomplete, complete or failed, and
-- CanSeeStartQuest calls it too: an Alliance player who picked up 2923, 2925 or 2931 in the world would see no "!" for
-- 2922, 2924 or 2930 at the exile until they abandoned it or turned it in. All three stop being breadcrumbs and become
-- plain lead-ins (their RewardNextQuest 2922, 2924 and 2930 stay, so the stock flow is unchanged). Stock values read
-- from the live quest_template_addon: 2923 -> 2922, 2925 -> 2924, 2931 -> 2930 (no other row names an exile quest).
-- A plain lead-in stays takeable after its target quest is done (only a breadcrumb is hidden then): harmless.
UPDATE `quest_template_addon` SET `BreadcrumbForQuestId` = 0 WHERE `ID` = 2923 AND `BreadcrumbForQuestId` = 2922;
UPDATE `quest_template_addon` SET `BreadcrumbForQuestId` = 0 WHERE `ID` = 2925 AND `BreadcrumbForQuestId` = 2924;
UPDATE `quest_template_addon` SET `BreadcrumbForQuestId` = 0 WHERE `ID` = 2931 AND `BreadcrumbForQuestId` = 2930;

-- 2924 Essential Artificials: 12 -> 4 (the 47 Artificial Extrapolator chests, 24 above the Workshop and 23 below; 5
-- players x 12 = 60 was more than the dungeon holds).
UPDATE `quest_template` SET `RequiredItemCount1` = 4
    WHERE `ID` = 2924 AND `RequiredItemId1` = 9278 AND `RequiredItemCount1` = 12;

-- 2945 Grime-Encrusted Ring: the Sparklematic 5200 (GO 142487) stops starting Return of the Ring (2947 Alliance, 2949
-- Horde; section 7 #47 A): 2945 rewards its own blue ring, a second blue would be a second ring for one grime. The
-- Sparklematic keeps ending 2945 and starting and ending the three Sparklematic quests (2951, 2952, 2953). Unreachable
-- for new players afterwards (rows stay, nothing else starts them): 2947, 2948 (Talvash's Gold Ring), 2949 and 2950
-- (Nogg's Ring Redo, Horde, PrevQuestID 2949) with their rewards 9362, 9538 and 9588 (Nogg's Gold Ring). Players who
-- already hold 2947 or 2949 still finish: the enders stay.
DELETE FROM `gameobject_queststarter` WHERE `id` = 142487 AND `quest` IN (2947, 2949);

-- Reward choices (section 7 #46 A). 2922: a green choice of three wrists (item level 31); 2924: a healer cloak (green,
-- 35); 2945: a blue ring (39); 2841 Rig Wars: a blue choice (40) of a bow, Intellect cloth gloves and tank plate
-- gloves, replacing the three shared blues 9623, 9624 and 9625; 2929 The Grand Betrayal: a blue choice (40) of three
-- legs, replacing the same three. 2928 and 2930 keep their stock rewards (9608 and 9609 to choose from; 9605 and 9604
-- as fixed items). Each UPDATE is guarded on the stock values and on the expected names of the new items (EXISTS: a
-- shifted id changes nothing). 9623, 9624 and 9625 have no other source (no loot, reference, vendor or other quest
-- gives them), so they become unreachable once 2841 and 2929 stop paying them; their quest_rewards.lock lines stay and
-- do nothing.
UPDATE `quest_template` SET
    `RewardChoiceItemID1` = 75013,
    `RewardChoiceItemQuantity1` = 1,
    `RewardChoiceItemID2` = 75014,
    `RewardChoiceItemQuantity2` = 1,
    `RewardChoiceItemID3` = 75015,
    `RewardChoiceItemQuantity3` = 1
    WHERE `ID` = 2922 AND `RewardChoiceItemID1` = 0 AND `RewardChoiceItemID2` = 0 AND `RewardChoiceItemID3` = 0
    AND EXISTS (SELECT 1 FROM `item_template` WHERE `entry` = 75013 AND `name` = 'Memory Keeper''s Wraps')
    AND EXISTS (SELECT 1 FROM `item_template` WHERE `entry` = 75014 AND `name` = 'Memory Keeper''s Bracers')
    AND EXISTS (SELECT 1 FROM `item_template` WHERE `entry` = 75015 AND `name` = 'Memory Keeper''s Vambraces');
UPDATE `quest_template` SET
    `RewardChoiceItemID1` = 75016,
    `RewardChoiceItemQuantity1` = 1
    WHERE `ID` = 2924 AND `RewardChoiceItemID1` = 0
    AND EXISTS (SELECT 1 FROM `item_template` WHERE `entry` = 75016 AND `name` = 'Extrapolator''s Cloak');
UPDATE `quest_template` SET
    `RewardChoiceItemID1` = 75017,
    `RewardChoiceItemQuantity1` = 1
    WHERE `ID` = 2945 AND `RewardChoiceItemID1` = 0
    AND EXISTS (SELECT 1 FROM `item_template` WHERE `entry` = 75017 AND `name` = 'Sparklematic Signet');
UPDATE `quest_template` SET
    `RewardChoiceItemID1` = 75018,
    `RewardChoiceItemQuantity1` = 1,
    `RewardChoiceItemID2` = 75019,
    `RewardChoiceItemQuantity2` = 1,
    `RewardChoiceItemID3` = 75020,
    `RewardChoiceItemQuantity3` = 1
    WHERE `ID` = 2841 AND `RewardChoiceItemID1` = 9623 AND `RewardChoiceItemID2` = 9624
    AND `RewardChoiceItemID3` = 9625
    AND EXISTS (SELECT 1 FROM `item_template` WHERE `entry` = 75018 AND `name` = 'Rigrunner''s Longbow')
    AND EXISTS (SELECT 1 FROM `item_template` WHERE `entry` = 75019 AND `name` = 'Blueprint Reader''s Mitts')
    AND EXISTS (SELECT 1 FROM `item_template` WHERE `entry` = 75020 AND `name` = 'Rigbreaker Gauntlets');
UPDATE `quest_template` SET
    `RewardChoiceItemID1` = 75021,
    `RewardChoiceItemQuantity1` = 1,
    `RewardChoiceItemID2` = 75022,
    `RewardChoiceItemQuantity2` = 1,
    `RewardChoiceItemID3` = 75023,
    `RewardChoiceItemQuantity3` = 1
    WHERE `ID` = 2929 AND `RewardChoiceItemID1` = 9623 AND `RewardChoiceItemID2` = 9624
    AND `RewardChoiceItemID3` = 9625
    AND EXISTS (SELECT 1 FROM `item_template` WHERE `entry` = 75021 AND `name` = 'Retaker''s Legplates')
    AND EXISTS (SELECT 1 FROM `item_template` WHERE `entry` = 75022 AND `name` = 'Retaker''s Leggings')
    AND EXISTS (SELECT 1 FROM `item_template` WHERE `entry` = 75023 AND `name` = 'Retaker''s Pants');

-- Text (section 7 #50 A). The faction-voiced and city-directing lines are rewritten neutral and light: the log and
-- completion lines name the exile instead of an Ironforge, Stormwind or Orgrimmar giver, and a few sentences lose the
-- Alliance or goblin voice. Everything else stays stock (the stock givers still hand the quests out and in). Each
-- UPDATE is guarded on the stock text. Locale rows (the `_locale` tables) are not touched.
-- 2922 Save Techbot's Brain!
UPDATE `quest_template` SET `LogDescription` = 'Bring Techbot''s Memory Core to Tinkmaster Fizzbolt in Gnomeregan.',
    `QuestCompletionLog` = 'Return to Tinkmaster Fizzbolt in Gnomeregan.'
    WHERE `ID` = 2922 AND `LogDescription` = 'Bring Techbot''s Memory Core to Tinkmaster Overspark in Ironforge.'
    AND `QuestCompletionLog` = 'Return to Tinkmaster Overspark at Tinker Town in Ironforge.';
-- 2924 Essential Artificials
UPDATE `quest_template` SET `LogDescription` = 'Bring 4 Essential Artificials to Tinkmaster Fizzbolt in Gnomeregan.',
    `QuestCompletionLog` = 'Return to Tinkmaster Fizzbolt in Gnomeregan.'
    WHERE `ID` = 2924 AND `LogDescription` = 'Bring 12 Essential Artificials to Klockmort Spannerspan in Ironforge.'
    AND `QuestCompletionLog` = 'Return to Klockmort Spannerspan at Tinker Town in Ironforge.';
-- 2928 Gyrodrillmatic Excavationators
UPDATE `quest_template` SET `LogDescription` = 'Bring twenty-four Robo-mechanical Guts to Tinkmaster Fizzbolt in Gnomeregan.',
    `QuestCompletionLog` = 'Return to Tinkmaster Fizzbolt in Gnomeregan.',
    `QuestDescription` = 'It''s terrible, $N. We are not going to have enough parts to get our fleet of gyrodrillmatic excavationators running.$B$BWhat we need are spare parts, $N. What better place to get the spare parts for our vehicles than Gnomeregan? I hear that bots and mechs roam around that place like cattle on an open range.$B$BWhat I need you to do is go to Gnomeregan and tear apart those robots. Bring me back their robot guts. Two dozen should be sufficient.$B'
    WHERE `ID` = 2928 AND `LogDescription` = 'Bring twenty-four Robo-mechanical Guts to Shoni in Stormwind.'
    AND `QuestCompletionLog` = 'Return to Shoni the Shilent at the Dwarven District in Stormwind.'
    AND `QuestDescription` = 'It''s terrible, $N. We are not going to have enough parts to get our fleet of gyrodrillmatic excavationators to Dun Morogh.$B$BWhat we need are spare parts, $N. What better place to get the spare parts for our vehicles than Gnomeregan? I hear that bots and mechs roam around that place like cattle on an open range.$B$BWhat I need you to do is go to Gnomeregan and tear apart those robots. Bring me back their robot guts. Two dozen should be sufficient.$B';
-- 2930 Data Rescue
UPDATE `quest_template` SET `LogDescription` = 'Bring a Prismatic Punch Card to Tinkmaster Fizzbolt in Gnomeregan.',
    `QuestCompletionLog` = 'Return to Tinkmaster Fizzbolt in Gnomeregan.'
    WHERE `ID` = 2930 AND `LogDescription` = 'Bring a Prismatic Punch Card to Master Mechanic Castpipe in Ironforge.'
    AND `QuestCompletionLog` = 'Return to Master Mechanic Castpipe at Tinker Town in Ironforge.';
-- 2841 Rig Wars
UPDATE `quest_template` SET `LogDescription` = 'Retrieve the Rig Blueprints and Thermaplugg''s Safe Combination from Gnomeregan and bring them to Tinkmaster Fizzbolt.$B',
    `QuestCompletionLog` = 'Return to Tinkmaster Fizzbolt in Gnomeregan.',
    `QuestDescription` = 'Gnome technology - two years ago its most common use was as a punch line. Times certainly have changed. Now they''ve got a new rig built that''s better than any shredder or gyrocopter on the road. I need the blueprints, $N!$B$BUnfortunately, the plans are locked away in a safe near Mekgineer Thermaplugg. To make matters worse, the combination to the safe is only known by Mekgineer Thermaplugg.$B$BDo whatever you have to do to get that combination, $N. Then crack open that safe and bring back those blueprints!$B'
    WHERE `ID` = 2841 AND `LogDescription` = 'Retrieve the Rig Blueprints and Thermaplugg''s Safe Combination from Gnomeregan and bring them to Nogg in Orgrimmar.$B'
    AND `QuestCompletionLog` = 'Return to Nogg in Orgrimmar.'
    AND `QuestDescription` = 'Gnome technology - two years ago its most common use was as a punch line. Times certainly have changed. Now they''ve got a new rig built that''s better than all our shredder models combined. I need the blueprints, $N!$B$BUnfortunately, the plans are locked away in a safe near Mekgineer Thermaplugg. To make matters worse, the combination to the safe is only known by Mekgineer Thermaplugg.$B$BDo whatever you have to do to get that combination, $N. Then crack open that safe and bring back those blueprints!$B';
-- 2929 The Grand Betrayal
UPDATE `quest_template` SET `LogDescription` = 'Venture to Gnomeregan and kill Mekgineer Thermaplugg. Return to Tinkmaster Fizzbolt when the task is complete.',
    `QuestCompletionLog` = 'Return to Tinkmaster Fizzbolt in Gnomeregan.',
    `QuestDescription` = 'Every gnome trusted Thermaplugg, $r. Never did we expect that he would betray the entire gnomish people. And for what? Power? Wealth? All things that he would have had in time. Now we have been displaced from our home and that madman is in charge. The king of nothing....$B$BWe will retake Gnomeregan, $N. We will not stop until the city is back in our control. If you wish to join in our fight, a simple task I ask of you: Kill the betrayer. Destroy Mekgineer Thermaplugg.'
    WHERE `ID` = 2929 AND `LogDescription` = 'Venture to Gnomeregan and kill Mekgineer Thermaplugg. Return to High Tinker Mekkatorque when the task is complete.'
    AND `QuestCompletionLog` = 'Return to High Tinker Mekkatorque at Tinker Town in Ironforge.'
    AND `QuestDescription` = 'I trusted Thermaplugg, $r. Never did I expect that he would betray me and the entire gnomish people. And for what? Power? Wealth? All things that he would have had in time. Now we have been displaced from our home and that madman is in charge. The king of nothing....$B$BWe will retake Gnomeregan, $N. We will not stop until the city is back in our control. If you wish to join in our fight, a simple task I ask of you: Kill the betrayer. Destroy Mekgineer Thermaplugg.';
UPDATE `quest_offer_reward` SET `RewardText` = 'I knew you could do it, $N! Some of the others had their doubts.$B$B<The tinker clears his throat.>$B$BNow that we have the blueprints in our possession, it is only a matter of time before we figure out every innovation that went into the creation of the rig and put it to good use.'
    WHERE `ID` = 2841 AND `RewardText` = 'I knew you could do it, $N! Sovik on the other hand, he had his doubts.$B$B<Nogg clears his throat.>$B$BNow that we have the blueprints in our possession, it is only a matter of time before we figure out all of the gnomish innovations that went into the creation of the rig and make them goblin innovations for our new shredder models.';
UPDATE `quest_offer_reward` SET `RewardText` = 'You place the ring inside the Sparklematic 5200 and deposit three silver coins into the slot.$B$BPainful grinding noises emanate from the machine as it begins to jerk around violently.  One can only guess what is happening with the ring inside the machine...$B$BThe machine suddenly stops, trumpeting its cessation with a simple "Ding!"  The item receptacle opens up to reveal your ring, scrubbed clean and gleaming.  It would appear that the Sparklematic 5200 does fine work!'
    WHERE `ID` = 2945 AND `RewardText` = 'You place the ring inside the Sparklematic 5200 and deposit a silver coin into the slot.$B$BPainful grinding noises emanate from the machine as it begins to jerk around violently.  One can only guess what is happening with the ring inside the machine...$B$BThe machine suddenly stops, trumpeting its cessation with a simple "Ding!"  The item receptacle opens up to reveal a small box that is neatly wrapped with a red bow.  It would appear that the Sparklematic 5200 also gift wraps!';

-- Tinkmaster Fizzbolt, the exile quest giver (301190), the two static spawns (normal difficulty only, `spawnMask` 1:
-- heroic is level 60 and has no dungeon quests; `normal_only_creatures` of source/world/dungeons/gnomeregan.py keeps
-- the heroic mask off them), guid = 10 x entry and the next. Map 90, phase 1, standing still, 300 s respawn.
--   3011900 the entrance: -338.12, -6.55, -152.85, o 1.16. The designer's in-game spot (2026-11-24; z is the floor as
--     given), not moved by the measurements below, which are for the record only. Dungeon Finder arrival point:
--     areatrigger_teleport 324 Gnomeregan Entrance (-329.10, -3.21, -152.85, o 2.97): the spot is 9.6 yd from it (3D).
--     Measured (3D, live creature table 2026-11-26) to the nearest spawns: Irradiated Pillager 31796 81.9 yd, 30398
--     85.5 yd, Caverndeep Ambusher 30213 91.0 yd (the patroller of path 302130, whose closest segment is 86.7 yd
--     away): no spawn within 80 yd, nothing in aggro range. No gameobject within 100 yd.
--   3011901 the Workshop: -753.00, -4.04, -252.22, o 1.40. Section 2's Finder start, areatrigger_teleport 523
--     Gnomeregan Train Depot Entrance (-736.51, 2.71, -249.99, o 3.14): 17.9 yd from it. Nearest spawns:
--     Mechano-Flamewalker 30309 57.4 yd, Mechanized Sentry 30206 58.8 yd, Leprous Machinesmith 30303 61.2 yd (all
--     outside their aggro range of 18 to 20); nearest patrol path 301930 (Mechano-Frostwalker 30193, 12 points) 88.8
--     yd; no gameobject within 150 yd.
--   The two End spots are summoned, not spawned here; the same measurements (live table, 3D): End 1 (-538.76, 527.40,
--     -216.27, o 3.89) is 27.9 yd from Electrocutioner 6000 (30133; the instance summons the End NPC when he dies), the
--     nearest other spawn is 57.8 yd away (Leprous Technician 30383), path 302780 57.1 yd; End 2 (-607.63, 677.98,
--     -327.04, o 6.21) is 13.9 yd from Mechanized Guardian 30332 and 15.7 to 19.9 yd from four Leprous Machinesmiths
--     and a second Guardian (the console pack, cleared on the way in), path 334960 41.1 yd.
DELETE FROM `creature` WHERE `id` = 301190 AND `guid` IN (3011900, 3011901);
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(3011900, 301190, 90, 0, 0, 1, 1, 0, -338.12, -6.55, -152.85, 1.16, 300, 0, 12340, 0,
    'Tinkmaster Fizzbolt - Gnomeregan entrance quest giver'),
(3011901, 301190, 90, 0, 0, 1, 1, 0, -753.00, -4.04, -252.22, 1.40, 300, 0, 12340, 0,
    'Tinkmaster Fizzbolt - Gnomeregan Workshop quest giver');

-- Starters and enders. One entry for all four spots, so every spot gives and ends the same six dungeon quests. The
-- stock givers and enders (Tinkmaster Overspark 7944, Klockmort Spannerspan 6169, Shoni 6579, Master Mechanic Castpipe
-- 7950, Nogg 3412, High Tinker Mekkatorque 7937) keep theirs. 2945 is ended by the Sparklematic 5200 only (the quest
-- is cleaning the ring there, and the ring drops in both sections, section 7 #44 A).
DELETE FROM `creature_queststarter` WHERE `id` = 301190 AND `quest` IN (2922, 2924, 2928, 2930, 2841, 2929);
INSERT INTO `creature_queststarter` (`id`, `quest`) VALUES
(301190, 2922),
(301190, 2924),
(301190, 2928),
(301190, 2930),
(301190, 2841),
(301190, 2929);

DELETE FROM `creature_questender` WHERE `id` = 301190 AND `quest` IN (2922, 2924, 2928, 2930, 2841, 2929);
INSERT INTO `creature_questender` (`id`, `quest`) VALUES
(301190, 2922),
(301190, 2924),
(301190, 2928),
(301190, 2930),
(301190, 2841),
(301190, 2929);
