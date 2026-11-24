-- Dungeon quests stage Q4, Blackrock Depths (.agents/plans/dungeon-quests/dungeon-quests.PLAN.md section 8, ruled by the
-- designer 2026-11-23; handoff dungeon-quests.STAGE-Q4-BRD-HANDOFF.md). The two creatures (300797 Kragen Ashvein,
-- 300798 Durn Cinderbrew) and their models are apps/dbc-tools source/npcs/blackrock_depths/dungeon_quests.py; the four
-- new reward items (Mountainheart Band, Oralius's Lucky Sash, Cipherblade, Jailbreaker's Bulwark; minted in
-- source/items/item_ids.lock) are source/items/blackrock_depths_dungeon_quests.py; the epic upgrade of 12543, 12544,
-- 12545 and 12548 and the blue upgrade of 12061 and 12062 are source/items/quest_rewards.lock. The item_template,
-- item_dbc and Item.dbc rows are the generated rev. Marshal Windsor's escort (Jail Break!) is the C++ script
-- npc_brd_marshal_windsor (modules/mod-dungeon-bosses src/BlackrockDepths/npc_marshal_windsor_escort.cpp), bound
-- below. No new quest and no quest item. Everything below is hand-written.

-- ---------------------------------------------------------------------------------------------------------------------
-- Open world: the Princess Moira rescue, one chain per faction (stock chains and factions).
-- ---------------------------------------------------------------------------------------------------------------------

-- 4003 The Royal Rescue (Horde) and 4362 The Fate of the Kingdom (Alliance), the Emperor kill, pay XP difficulty 9,
-- 300% of a normal quest (designer 2026-11-23; difficulty 9 exists since PR #154). Their follow-ups 4004 and 4363 offer
-- the epic choices (quest_rewards.lock).
UPDATE `quest_template` SET `RewardXPDifficulty` = 9 WHERE `ID` IN (4003, 4362) AND `RewardXPDifficulty` = 7;

-- ---------------------------------------------------------------------------------------------------------------------
-- Dungeon quests: neutral, no reputation, no prerequisite where it was zone context, neutral text.
-- ---------------------------------------------------------------------------------------------------------------------

-- Neutral (AllowableRaces -> 0): 4081 and 4082 KILL ON SIGHT (Horde, mask 690); 4263 Incendius!, 4286 The Good Stuff
-- and the Jail Break! chain 4264, 4282, 4322 (Alliance, mask 1101). 3802, 4123, 4136 and 4134 are neutral already.
-- Their stock givers and enders stay; the Thorium Brotherhood NPCs below give and end them for everyone.
UPDATE `quest_template` SET `AllowableRaces` = 0 WHERE `ID` IN (4081, 4082) AND `AllowableRaces` = 690;
UPDATE `quest_template` SET `AllowableRaces` = 0
    WHERE `ID` IN (4263, 4286, 4264, 4282, 4322) AND `AllowableRaces` = 1101;

-- A quest made neutral loses its reputation rewards (designer 2026-11-24): 4081 and 4082 gave Orgrimmar (76), 4263
-- Gnomeregan Exiles (54), 4286 Ironforge (47), 4264, 4282 and 4322 Stormwind (72). Only slot 1 is set live (5 or 7
-- points; every other slot and every override is 0); all five slots are cleared, guarded on the stock slot 1.
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` IN (4081, 4082) AND `RewardFactionID1` = 76 AND `RewardFactionValue1` = 7;
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` = 4263 AND `RewardFactionID1` = 54 AND `RewardFactionValue1` = 7;
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` = 4286 AND `RewardFactionID1` = 47 AND `RewardFactionValue1` = 7;
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` IN (4264, 4282, 4322) AND `RewardFactionID1` = 72 AND `RewardFactionValue1` IN (5, 7);

-- Prerequisites that were only zone context (designer 2026-11-23), so the NPCs inside can give the quests:
--   3802 Dark Iron Legacy loses 3801 (the talk step with Franclorn Forgewright's ghost). Nothing else requires 3801:
--     no PrevQuestID, NextQuestID or condition names it; 3801 itself stays, and still offers 3802 (RewardNextQuest).
--   4263 Incendius! loses 4262 Overmaster Pyron (Jalinda Sprig, Burning Steppes).
--   4136 Ribbly Screwspigot loses 4324 Yuka Screwspigot (its breadcrumb, BreadcrumbForQuestId 4136: still hidden
--     once 4136 is taken).
--   4134 Lost Thunderbrew Recipe loses 4133 Vivian Lagrave (its breadcrumb, BreadcrumbForQuestId 4134).
--   4264 A Crumpled Up Note loses 4242 Abandoned Hope (Burning Steppes; it has no giver since the attunement went).
-- 4082 keeps 4081 (both inside); 4282 keeps 4264 and 4322 keeps 4282 (the chain, all at Windsor's cell).
UPDATE `quest_template_addon` SET `PrevQuestID` = 0 WHERE `ID` = 3802 AND `PrevQuestID` = 3801;
UPDATE `quest_template_addon` SET `PrevQuestID` = 0 WHERE `ID` = 4263 AND `PrevQuestID` = 4262;
UPDATE `quest_template_addon` SET `PrevQuestID` = 0 WHERE `ID` = 4136 AND `PrevQuestID` = 4324;
UPDATE `quest_template_addon` SET `PrevQuestID` = 0 WHERE `ID` = 4134 AND `PrevQuestID` = 4133;
UPDATE `quest_template_addon` SET `PrevQuestID` = 0 WHERE `ID` = 4264 AND `PrevQuestID` = 4242;

-- The merged pairs (designer 2026-11-23): the neutral quest and its stock faction twin share an ExclusiveGroup, so a
-- player gets one of the two, never both. A positive group is one-of (Player::SatisfyQuestExclusiveGroup: a quest of
-- the group cannot be taken while another one is in the log or rewarded); a negative one is all-of. The group value is
-- the neutral quest's id (unused live: no quest_template_addon row has ExclusiveGroup 4263 or 4134).
--   4263 Incendius! (neutral) + 3907 Disharmony of Fire (Horde, Thunderheart; stays stock, still after 3906).
--   4134 Lost Thunderbrew Recipe (neutral) + 4126 Hurley Blackbreath (Alliance, Ragnar Thunderbrew; still after 4128).
-- Both pairs ask for the same objective (Lord Incendius 9017; the Lost Thunderbrew Recipe 11312). A player holding the
-- twin keeps it and can finish it; only taking the other one is refused. No character holds or has done any of the
-- four (character_queststatus and character_queststatus_rewarded, 2026-11-24).
UPDATE `quest_template_addon` SET `ExclusiveGroup` = 4263 WHERE `ID` IN (4263, 3907) AND `ExclusiveGroup` = 0;
UPDATE `quest_template_addon` SET `ExclusiveGroup` = 4134 WHERE `ID` IN (4134, 4126) AND `ExclusiveGroup` = 0;

-- Jail Break! (4322) becomes shareable (Flags 2 -> 10, QUEST_FLAGS_SHARABLE; designer 2026-11-24). Its stock
-- PARTY_ACCEPT bit (2) already offers the quest to every group member in reward range who can take it when one player
-- accepts at Windsor (WorldSession::HandleQuestgiverAcceptQuestOpcode -> SendQuestConfirmAccept); sharing is the
-- fallback for a member who was out of range or closed that box during the escort's start delay. The share still
-- checks 4282 rewarded.
UPDATE `quest_template` SET `Flags` = 10 WHERE `ID` = 4322 AND `Flags` = 2;

-- ---------------------------------------------------------------------------------------------------------------------
-- The Jail Break! chain inside: A Crumpled Up Note (4264) -> A Shred of Hope (4282) -> Jail Break! (4322).
-- ---------------------------------------------------------------------------------------------------------------------

-- The note (11446) starts 4264 again (startquest 0 since the attunement went). It drops at 25% from 102 loot entries
-- (normal and heroic), 752 spawns on map 230, gated by 102 `conditions` rows asking for 4242 Abandoned Hope rewarded,
-- which nobody can get: those rows go, so it drops for everyone. LootItem::AllowedForPlayer hides a quest starter item
-- from a player whose StartQuest is taken or rewarded, or who already holds MaxCount (1) of it; with the prerequisite
-- gone that is the whole gate. Its other fields stay: Bind on Pickup, unique, RequiredLevel 50 (4264's MinLevel is 50
-- too), Flags 2048 (one copy per group member). 6402 and 6403 (the dead Onyxia attunement) stay dead: no giver, and
-- 4322 points at nothing (NextQuestID 0, RewardNextQuest 0); 6402's PrevQuestID 4322 opens nothing without a giver.
UPDATE `item_template` SET `startquest` = 4264 WHERE `entry` = 11446 AND `startquest` = 0;
DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 1 AND `SourceEntry` = 11446 AND `ConditionTypeOrReference` = 8
    AND `ConditionValue1` = 4242;

-- A Shred of Hope (4282) becomes a talk step at Windsor (designer 2026-11-24): its stock objective, Marshal Windsor's
-- Lost Information (11464 from General Angerforge, 11465 from Golem Lord Argelmach, both in the Manufactory), is
-- dropped so the whole chain stays in the Detention Block. With no objective left, 4282 is complete the moment it is
-- accepted and is handed straight back to Windsor. The two items' loot rows (QuestRequired 1) stay; no quest needs
-- them now, so they no longer drop. Windsor offers the next step at each turn-in (RewardNextQuest): the note (4264)
-- -> A Shred of Hope (4282) -> Jail Break! (4322); both had RewardNextQuest 0.
UPDATE `quest_template` SET `RequiredItemId1` = 0, `RequiredItemCount1` = 0, `RequiredItemId2` = 0,
    `RequiredItemCount2` = 0
    WHERE `ID` = 4282 AND `RequiredItemId1` = 11464 AND `RequiredItemCount1` = 1 AND `RequiredItemId2` = 11465
    AND `RequiredItemCount2` = 1;
UPDATE `quest_template` SET `RewardNextQuest` = 4282 WHERE `ID` = 4264 AND `RewardNextQuest` = 0;
UPDATE `quest_template` SET `RewardNextQuest` = 4322 WHERE `ID` = 4282 AND `RewardNextQuest` = 0;

-- Marshal Windsor (9023): ends 4264 and 4282, gives 4282 and 4322 (none of these rows exists live), and runs the
-- escort script. His faction stays the stock 534 (Alliance Generic: friendly to Alliance, neutral to Horde, hostile to
-- nobody) with unit_flags 320 (immune to players): a Horde player can talk to him, and nobody can attack him. The
-- script sets the escort faction (250) for the run.
UPDATE `creature_template` SET `ScriptName` = 'npc_brd_marshal_windsor' WHERE `entry` = 9023 AND `ScriptName` = '';
DELETE FROM `creature_queststarter` WHERE `id` = 9023 AND `quest` IN (4282, 4322);
INSERT INTO `creature_queststarter` (`id`, `quest`) VALUES
(9023, 4282),
(9023, 4322);
DELETE FROM `creature_questender` WHERE `id` = 9023 AND `quest` IN (4264, 4282);
INSERT INTO `creature_questender` (`id`, `quest`) VALUES
(9023, 4264),
(9023, 4282);

-- The escort's lines (npc_brd_marshal_windsor; the original's, from TrinityCore 22413c016e by Blaymoira, with the last
-- one rewritten for the entrance turn-in, and four new ones: groups 1, 2 and 22, and 21's new text) and the three
-- prisoners who speak when freed. No creature_text row exists for any of them live.
DELETE FROM `creature_text` WHERE `CreatureID` IN (9023, 9022, 9677, 9679);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9023, 0, 0, 'You locked up the wrong Marshal. Prepare to be destroyed!', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - aggro'),
(9023, 0, 1, 'I bet you''re sorry now, aren''t you?!', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - aggro'),
(9023, 0, 2, 'You better hold me back, $N, or they are going to feel some prison house beatings.', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - aggro'),
(9023, 1, 0, 'Not yet, $N. Gerstahn, Roccor and Grebmar still hold the cell block. Clear them out, then come back for me.', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - a Detention Block boss is alive'),
(9023, 2, 0, 'Then let''s not waste a moment. Gather your friends, $N. Once this cell is open, there is no going back.', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - accepted, start delay'),
(9023, 3, 0, 'Let''s get a move on. My gear should be in the storage area up this way...', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - start'),
(9023, 4, 0, 'Check that cell, $N. If someone is alive in there, we need to get them out.', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - Dughal''s cell'),
(9023, 5, 0, 'Get him out of there!', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - Dughal''s and Tobias''s cells'),
(9023, 6, 0, 'Good work! We''re almost there, $N. This way.', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - Dughal freed'),
(9023, 7, 0, 'This is it, $N. My stuff should be in that room. Cover me, I''m going in!', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - supply room'),
(9023, 8, 0, 'Ah, there it is!', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - his gear'),
(9023, 9, 0, 'Can you feel the power, $N??? It''s time to ROCK!', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - geared'),
(9023, 10, 0, 'Now we just have to free Tobias and we can get out of here. This way!', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - geared'),
(9023, 11, 0, 'Open it.', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - Jaz and Ograbisi''s cell'),
(9023, 12, 0, 'I never did like those two. Let''s get moving.', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - Jaz and Ograbisi dead'),
(9023, 13, 0, 'Open it and be careful this time!', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - Shill Dinger''s cell'),
(9023, 14, 0, 'That intolerant dirtbag finally got what was coming to him. Good riddance!', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - Shill Dinger dead'),
(9023, 15, 0, 'Alright, let''s go.', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - Shill Dinger dead'),
(9023, 16, 0, 'Open it. We need to hurry up. I can smell those Dark Irons coming a mile away and I can tell you one thing, they''re COMING!', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - Crest Killer''s cell'),
(9023, 17, 0, 'Administering fists of fury on Crest Killer!', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - Crest Killer fight'),
(9023, 18, 0, 'He has to be in the last cell. Unless... they killed him.', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - Crest Killer dead'),
(9023, 19, 0, 'Excellent work, $N. Let''s find the exit. I think I know the way. Follow me!', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - Tobias freed'),
(9023, 20, 0, 'We made it!', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - the exit'),
(9023, 21, 0, 'Give your report to the Thorium Brotherhood, $N. They will see that these tablets reach the right hands. I have business in Stormwind.', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - the exit, leaving'),
(9023, 22, 0, 'Stand back. I''ll open it myself.', 12, 0, 100, 0, 0, 0, 0, 0, 'Marshal Windsor - forces a cell door'),
(9022, 0, 0, 'Thank you, $N! I''m free!!!', 12, 0, 100, 0, 0, 0, 0, 0, 'Dughal Stormwing - freed (Jail Break!)'),
(9679, 0, 0, 'Thank you! I will run for safety immediately!', 12, 0, 100, 0, 0, 0, 0, 0, 'Tobias Seecher - freed (Jail Break!)'),
(9677, 0, 0, 'Ograbisi needs new hat.', 12, 0, 100, 0, 0, 0, 0, 0, 'Ograbisi - cell opened (Jail Break!)');

-- ---------------------------------------------------------------------------------------------------------------------
-- Rewards (the item rows are the generated rev).
-- ---------------------------------------------------------------------------------------------------------------------

-- 4123 The Heart of the Mountain (stock: 8.5 gold only): the new blue ring, Mountainheart Band (74340).
UPDATE `quest_template` SET `RewardChoiceItemID1` = 74340, `RewardChoiceItemQuantity1` = 1
    WHERE `ID` = 4123 AND `RewardChoiceItemID1` = 0 AND `RewardChoiceItemQuantity1` = 0;
-- 4286 The Good Stuff: the stock Dingy Fanny Pack (RewardItem1 11883) stays, plus the new healer green, Oralius's Lucky
-- Sash (74341), as a second fixed reward (a single item: no choice to make).
UPDATE `quest_template` SET `RewardItem2` = 74341, `RewardAmount2` = 1
    WHERE `ID` = 4286 AND `RewardItem1` = 11883 AND `RewardItem2` = 0 AND `RewardAmount2` = 0;
-- 4322 Jail Break!: the choices 12061 Blade of Reckoning and 12062 Skilled Fighting Blade (blue now, quest_rewards.lock)
-- gain the caster and tank blues, Cipherblade (74342) and Jailbreaker's Bulwark (74343). Ward of the Elements (12065,
-- the fixed reward) stays.
UPDATE `quest_template` SET `RewardChoiceItemID3` = 74342, `RewardChoiceItemQuantity3` = 1,
    `RewardChoiceItemID4` = 74343, `RewardChoiceItemQuantity4` = 1
    WHERE `ID` = 4322 AND `RewardChoiceItemID1` = 12061 AND `RewardChoiceItemID2` = 12062 AND `RewardChoiceItemID3` = 0
    AND `RewardChoiceItemID4` = 0;

-- ---------------------------------------------------------------------------------------------------------------------
-- Neutral text (faction-voiced or zone-bound stock lines rewritten; every guard is the exact stock text). Each quest log
-- line names the inside NPC and the stock giver. Left stock: 3802's log, progress and turn-in (the shrine's), 4123's
-- details (Maxwort's first person, no faction), 4136's details and turn-in (Yuka's), 4286's details and turn-in
-- (Oralius'), 4282's progress line (Windsor's), 4264's note, and every *_locale row.
-- ---------------------------------------------------------------------------------------------------------------------

UPDATE `quest_template` SET `LogDescription` = 'Venture to Blackrock Depths and destroy the vile aggressors!$B$BKill 15 Anvilrage Guardsmen, 10 Anvilrage Wardens and 5 Anvilrage Footmen, then report to the Thorium Brotherhood at the entrance of Blackrock Depths, or to Warlord Goretooth in Kargath.$B',
    `QuestDescription` = 'A bounty, posted for anyone with the nerve to collect it:$B$BAny and all of General Angerforge''s forces within Blackrock Depths must be annihilated.$B$BAngerforge''s men are ruthless killers, responsible for the mass murder of the 109th division of the Kargath Expeditionary Force and of every other force that has tried the mountain. Heroes are warned to exercise extreme caution when confronting these brutes.$B$BAny person who destroys the first line of General Angerforge''s forces in Blackrock Depths shall receive a tribute.',
    `QuestCompletionLog` = 'Return to Kragen Ashvein of the Thorium Brotherhood at the entrance of Blackrock Depths, or to Warlord Goretooth at Kargath in Badlands.'
    WHERE `ID` = 4081 AND `LogDescription` = 'Venture to Blackrock Depths and destroy the vile aggressors!$B$BWarlord Goretooth wants you to kill 15 Anvilrage Guardsmen, 10 Anvilrage Wardens and 5 Anvilrage Footmen. Return to him once your task is complete.$B' AND `QuestDescription` = 'By order of Warlord Goretooth, commander of the Kargath Expeditionary Force:$B$BAny and all of General Angerforge''s forces within Blackrock Depths must be annihilated.$B$BAngerforge''s men are ruthless killers, responsible for the mass murder of the 109th division of the Kargath Expeditionary Force. Heroes are warned to exercise extreme caution when confronting these brutes.$B$BAny person who destroys the first line of General Angerforge''s forces in Blackrock Depths shall receive a tribute.' AND `QuestCompletionLog` = 'Return to Warlord Goretooth at Kargath in Badlands.';
UPDATE `quest_offer_reward` SET `RewardText` = 'This first strike should put a crease in Angerforge''s pants. Now, move along soldier. I have work to complete, battles to plan, enemies to crush!$B$BThere is more work where that came from.'
    WHERE `ID` = 4081 AND `RewardText` = 'This first strike should put a crease in Angerforge''s pants. Now, move along soldier. I have work to complete, battles to plan, enemies to crush!$B$BCheck the wanted signs for more work.';
UPDATE `quest_template` SET `LogDescription` = 'Venture to Blackrock Depths and destroy the vile aggressors!$B$BKill 10 Anvilrage Medics, 10 Anvilrage Soldiers and 10 Anvilrage Officers, then report to the Thorium Brotherhood at the entrance of Blackrock Depths, or to Warlord Goretooth in Kargath.',
    `QuestDescription` = 'A second bounty, for those who answered the first:$B$BScouts have returned with news of the whereabouts of high ranking Dark Iron officials. Through locked gate, near the heart of the city, they train their forces to snuff out any who stand against the mountain. Travel to Blackrock Depths and destroy them!$B$BCompletion of this mission will result in a tribute.$B',
    `QuestCompletionLog` = 'Return to Kragen Ashvein of the Thorium Brotherhood at the entrance of Blackrock Depths, or to Warlord Goretooth at Kargath in Badlands.'
    WHERE `ID` = 4082 AND `LogDescription` = 'Venture to Blackrock Depths and destroy the vile aggressors!$B$BWarlord Goretooth wants you to kill 10 Anvilrage Medics, 10 Anvilrage Soldiers and 10 Anvilrage Officers. Return to him once your task is complete.' AND `QuestDescription` = 'By order of Warlord Goretooth, commander of the Kargath Expeditionary Force:$B$BHead of the K.E.F. reconnaissance division, Grandmaster Lexlort, has returned with news of the whereabouts of high ranking Dark Iron officials. Through locked gate, near the heart of the city, they train their forces to snuff out our men. Travel to Blackrock Depths and destroy them!$B$BCompletion of this mission will result in a tribute.$B' AND `QuestCompletionLog` = 'Return to Warlord Goretooth at Kargath in Badlands.';
UPDATE `quest_offer_reward` SET `RewardText` = 'Angerforge is undoubtedly... angry. Good. An angry general makes mistakes, and those who mean to finish him will want to hear of this. I cannot go into any detail of what that entails, but rest assured, it involves somebody dying.'
    WHERE `ID` = 4082 AND `RewardText` = 'Angerforge is undoubtedly... angry. Return to me when you receive a third tribute and we shall proceed with Operation: Death to Angerforge. I cannot go into any detail of what this entails, but rest assured, it involves somebody dying.';
UPDATE `quest_template` SET `QuestDescription` = 'Franclorn Forgewright built the greatest works of this city, and his great hammer, Ironfel, was stolen from him. You will find Fineous Darkvire beyond the Ring of Law, in the Hall of Crafting. Kill the miserable cur and recover Ironfel.$B$BTake Ironfel to the Shrine of Thaurissan and place the hammer in its rightful place: in the hands of the statue erected in Franclorn''s honor.$B$BWhen this is done, the compartment in which he stored the master key will open. More importantly, Ironfel will remain forever in his grasp. Should they make an attempt to remove the hammer, both the statue and hammer will shatter, lost forever.'
    WHERE `ID` = 3802 AND `QuestDescription` = 'You will find Fineous Darkvire beyond the Ring of Law, in the Hall of Crafting. Kill the miserable cur and recover Ironfel.$B$BTake Ironfel to the Shrine of Thaurissan and place the hammer in its rightful place: In the hands of the statue erected in my honor.$B$BWhen this is done, the compartment in which I stored the master key will open. More importantly, Ironfel will remain forever in my grasp. Should they make an attempt to remove the hammer; both the statue and hammer will shatter, lost forever.';
UPDATE `quest_template` SET `LogDescription` = 'Bring the Heart of the Mountain to Kragen Ashvein of the Thorium Brotherhood at the entrance of Blackrock Depths, or to Maxwort Uberglint in the Burning Steppes.',
    `QuestCompletionLog` = 'Return to Kragen Ashvein of the Thorium Brotherhood at the entrance of Blackrock Depths, or to Maxwort Uberglint in Burning Steppes.'
    WHERE `ID` = 4123 AND `LogDescription` = 'Bring the Heart of the Mountain to Maxwort Uberglint in the Burning Steppes.' AND `QuestCompletionLog` = 'Return to Maxwort Uberglint in Burning Steppes.';
UPDATE `quest_template` SET `QuestDescription` = 'Lord Incendius is purported to be a minion of Ragnaros! Whenever Overmaster Pyron falls at the mountain''s gate, Incendius raises him from the ashes. Oh dear, oh dear... whatever will we do?$B$BDo you think you can handle this mission? I don''t have anybody else to send, $N!$B$BWe will never get a team in if Incendius continues to raise Pyron from the ashes.$B$BYou''ll have to find and destroy Lord Incendius!$B',
    `QuestCompletionLog` = 'Return to Kragen Ashvein of the Thorium Brotherhood at the entrance of Blackrock Depths, or to Jalinda Sprig at Morgan''s Vigil in the Burning Steppes.'
    WHERE `ID` = 4263 AND `QuestDescription` = 'Are you sure Pyron said ''Incendius'' when he died?$B$B<Jalinda swallows hard.>$B$BLord Incendius is purported to be a minion of Ragnaros! Oh dear, oh dear... whatever will we do?$B$BDo you think you can handle another mission? I don''t have anybody else to send, $N!$B$BWe will never get a team in if Incendius continues to raise Pyron from the ashes.$B$BYou''ll have to find and destroy Lord Incendius!$B' AND `QuestCompletionLog` = 'Return to Jalinda Sprig at Morgan''s Vigil in the Burning Steppes.';
UPDATE `quest_offer_reward` SET `RewardText` = 'Incendius is dead? And he spoke of Ragnaros?$b$bOh dear. That is grave news indeed. Take this, $N, with my thanks.'
    WHERE `ID` = 4263 AND `RewardText` = 'Oh dear! Are you sure Incendius said ''Ragnaros?''$b$b<Jalinda hands you something and pats you on the wrist as she fades deep into thought.>';
UPDATE `quest_template` SET `LogDescription` = 'Bring Ribbly''s Head to Durn Cinderbrew in the Grim Guzzler of Blackrock Depths, or to Yuka Screwspigot in the Burning Steppes.',
    `QuestCompletionLog` = 'Return to Durn Cinderbrew in the Grim Guzzler of Blackrock Depths, or to Yuka Screwspigot in the Burning Steppes.'
    WHERE `ID` = 4136 AND `LogDescription` = 'Bring Ribbly''s Head to Yuka Screwspigot in the Burning Steppes.' AND `QuestCompletionLog` = 'Return to Yuka Screwspigot in the Burning Steppes.';
UPDATE `quest_template` SET `LogDescription` = 'Bring the Lost Thunderbrew Recipe to Durn Cinderbrew in the Grim Guzzler of Blackrock Depths, or to Vivian Lagrave in Kargath.',
    `QuestDescription` = 'It is rumored that the Dark Iron Hurley Blackbreath has stolen a recipe for ale.  This ale, Thunderbrew Lager, is said to infuse its imbiber with great strength and courage.  We wish to study the drink.  Perhaps we will find other applications for its virtues.$B$BDelve into Blackrock Depths, find Hurley, take from him the recipe for Thunderbrew lager and bring it to me.$B$BAnd to find him, you may have to entice him by threatening his precious ale.',
    `QuestCompletionLog` = 'Return to Durn Cinderbrew in the Grim Guzzler of Blackrock Depths, or to Shadowmage Vivian Lagrave at Kargath in Badlands.'
    WHERE `ID` = 4134 AND `LogDescription` = 'Bring the Lost Thunderbrew Recipe to Vivian Lagrave in Kargath.' AND `QuestDescription` = 'It is rumored that the Dark Iron Hurley Blackbreath has stolen a recipe for ale.  This ale, Thunderbrew Lager, is said to infuse its imbiber with great strength and courage.  We wish to study the drink.  Perhaps, we will find other applications for its virtues... applications more in line with Forsaken objectives.$B$BDelve into Blackrock Depths, find Hurley, take from him the recipe for Thunderbrew lager and bring it to me.$B$BAnd to find him, you may have to entice him by threatening his precious ale.' AND `QuestCompletionLog` = 'Return to Shadowmage Vivian Lagrave at Kargath in Badlands.';
UPDATE `quest_offer_reward` SET `RewardText` = 'Very good. This recipe will be studied, and in time its secrets will be unlocked.$b$bThe Dark Irons stole it from the Thunderbrews, and now you have stolen it back from the Dark Irons. I find that terribly amusing.'
    WHERE `ID` = 4134 AND `RewardText` = 'Very good. I will send this recipe to the Apothecarium to be studied, and in time we will unlock its secrets. One day, the dwarves of the Alliance may find the virtues of this drink used against them!$b$bI find that terribly amusing. Perhaps death has an affect on one''s sense of humor... do you think?';
UPDATE `quest_template` SET `LogDescription` = 'Collect 20 Dark Iron Fanny Packs and bring them to Durn Cinderbrew in the Grim Guzzler of Blackrock Depths, or to Oralius in the Burning Steppes.',
    `QuestCompletionLog` = 'Return to Durn Cinderbrew in the Grim Guzzler of Blackrock Depths, or to Oralius at Morgan''s Vigil in the Burning Steppes.'
    WHERE `ID` = 4286 AND `LogDescription` = 'Collect 20 Dark Iron Fanny Packs.' AND `QuestCompletionLog` = 'Return to Oralius at Morgan''s Vigil in the Burning Steppes.';
UPDATE `quest_template` SET `LogDescription` = 'You may have just stumbled on to something that Marshal Windsor would be interested in seeing. He is held in a cell of the Detention Block. There may be hope, after all.'
    WHERE `ID` = 4264 AND `LogDescription` = 'You may have just stumbled on to something that Marshal Windsor would be interested in seeing. There may be hope, after all.';
UPDATE `quest_template` SET `LogDescription` = 'Hear Marshal Windsor out in his cell in the Detention Block of Blackrock Depths.',
    `QuestDescription` = '<Marshal Windsor shakes the note excitedly.>$B$BDo you realize what this means, $N?$B$BPerhaps all is not lost! Argelmach has not finished decrypting my tablets, and the Dark Irons keep them with the rest of my gear, in the supply room of this very block.$B$BGet me out of this cell and we take back everything they stole. I hope you are ready to battle.',
    `QuestCompletionLog` = 'Speak to Marshal Windsor in the Detention Block of Blackrock Depths.'
    WHERE `ID` = 4282 AND `LogDescription` = 'Return Marshal Windsor''s Lost Information.$B$BMarshal Windsor believes that the information is being held by Golem Lord Argelmach and General Angerforge.' AND `QuestDescription` = '<Marshal Windsor shakes the note excitedly.>$B$BDo you realize what this means, $N?$B$BPerhaps all is not lost! From what I can ascertain, the information is being held by two Dark Iron dwarves: General Angerforge and the golem lord, Argelmach. I have a feeling that they won''t just hand over the information if we ask nicely.$B$BI hope you are ready to battle.$B$BVenture forth and find these two villains! Destroy them and return my lost information.' AND `QuestCompletionLog` = 'Return to Marshal Windsor in Blackrock Depths.';
UPDATE `quest_offer_reward` SET `RewardText` = '<Marshal Windsor grips the bars of his cell.>$B$BThen there is no time to lose. We need to get out of here!'
    WHERE `ID` = 4282 AND `RewardText` = '<Marshal Windsor snatches the two tablets from your hands.>$B$BWe need to get out of here!';
UPDATE `quest_template` SET `LogDescription` = 'Help Marshal Windsor get his gear back and free his friends, then see him out of the Detention Block. Report to the Thorium Brotherhood at the entrance of Blackrock Depths if you succeed.',
    `QuestDescription` = 'We need to get out of here, $N. Help me get my gear back from the supply area and free my friends. If we make it out of here, report to the Thorium Brotherhood watch at the entrance. They will see that my tablets reach the right hands.',
    `QuestCompletionLog` = 'Report to Kragen Ashvein of the Thorium Brotherhood at the entrance of Blackrock Depths.'
    WHERE `ID` = 4322 AND `LogDescription` = 'Help Marshal Windsor get his gear back and free his friends. Return to Marshal Maxwell if you succeed.' AND `QuestDescription` = 'We need to get out of here, $N. Help me get my gear back from the supply area and free my friends. If we make it out of here, you are to proceed to Morgan''s Vigil and speak with Marshal Maxwell. He will give you further instruction.' AND `QuestCompletionLog` = 'Return to Marshal Maxwell at Morgan''s Vigil in Burning Steppes.';
UPDATE `quest_request_items` SET `CompletionText` = 'You look exhausted, $n. Sit a moment; the Brotherhood keeps watch here.'
    WHERE `ID` = 4322 AND `CompletionText` = 'You look exhausted, $n. Perhaps you should have a seat by the fire and relax.';
UPDATE `quest_offer_reward` SET `RewardText` = 'Amazing, $N. Simply amazing. Windsor stormed past this post not five minutes ago, his tablets under his arm. He makes some grand claims but purports that they are supported by his evidence. He is on his way to Stormwind now to confront Bolvar and ... Lady Prestor.'
    WHERE `ID` = 4322 AND `RewardText` = 'Amazing, $N. Simply amazing. Windsor stormed through here not five minutes ago. He makes some grand claims but purports that they are supported by his evidence. He is on his way to Stormwind now to confront Bolvar and ... Lady Prestor.';

-- ---------------------------------------------------------------------------------------------------------------------
-- The two Thorium Brotherhood NPCs: spawns, starters and enders.
-- ---------------------------------------------------------------------------------------------------------------------

-- Spawns, normal difficulty only (spawnMask 1: heroic is level 60 and has no dungeon quests), guid = 10 x entry like
-- the other dungeon builds' hand spawns. Map 230, phase 1, standing still, 300 s respawn. The positions are the
-- designer's in-game spots (2026-11-24; z is the floor), not moved by the measurements below, which are for the record
-- only: the nearest spawns (3D, map 230; hostile = hostile to a Human or an Orc player by FactionTemplate), the nearest
-- waypoint-path segment (every `waypoint_data` path of a map 230 spawn, creature_addon path_id or guid x 10, closing
-- segment included) and the map 230 navmesh (mmtiles of ac-worldserver, detail surface). Neither spot is on a path.
--   300797 Kragen Ashvein, the Detention Block entrance: 448.15, 26.09, -70.40, o 0.01. On the navmesh (detail z
--     -70.28). 12.1 yd from the zone-in point (areatrigger_teleport 1466: 456.93, 34.09, -68.09), 10.2 yd from the
--     Detention Block Finder start (458.32, 26.52, -70.67), 5.7 yd from where Windsor's escort ends. Nearest spawns: two
--     friendly Slaves (10116) at 41.2 and 43.5 yd; nearest hostile: the Anvilrage Overseers 45928 and 45927 at 54.0
--     and 56.0 yd, then 80.9 yd; nearest path: Blazing Fireguard 47795 (path 477950) at 61.5 yd.
--   300798 Durn Cinderbrew, the Grim Guzzler: 841.44, -147.21, -49.75, o 5.23. On the navmesh (detail z -49.69). 20.7 yd
--     from the Imperial Seat Finder start (843.8, -167.8, -49.7). Nearest spawns: Grim Patrons (9545, faction 674,
--     not hostile) from 13.5 yd; nearest hostile: Hurley Blackbreath's Cronies (9541) at 35.8 yd and Hurley (9537) at
--     37.1 yd, both hidden and passive until the third Thunderbrew Lager Keg; nearest path: Plugger Spazzring 47703
--     (path 477030) at 49.4 yd, then Coren Direbrew (Brewfest only) at 49.8 yd and Mistress Nagmara at 56.5 yd.
--     The bar's hostility events set faction 14 by entry only (Plugger's death on 9554, 9545, 9547 and Phalanx 9502;
--     the theft on 9545 and 9547 within 7 yd of Plugger; Ribbly's gossip on his Cronies 10043), and faction 14 and the
--     Dark Iron factions are not hostile to faction 35: Durn is never attacked or despawned by them.
DELETE FROM `creature` WHERE `id` = 300797 AND `guid` = 3007970;
DELETE FROM `creature` WHERE `id` = 300798 AND `guid` = 3007980;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(3007970, 300797, 230, 0, 0, 1, 1, 0, 448.150, 26.090, -70.400, 0.0100, 300, 0, 12340, 0,
    'Kragen Ashvein - Blackrock Depths entrance quest giver'),
(3007980, 300798, 230, 0, 0, 1, 1, 0, 841.440, -147.210, -49.750, 5.2300, 300, 0, 12340, 0,
    'Durn Cinderbrew - Blackrock Depths Grim Guzzler quest giver');

-- Starters and enders (the plan's table). Kragen Ashvein gives 4081, 4082, 3802, 4123 and 4263 and ends 4081, 4082,
-- 4123, 4263 and 4322 Jail Break!. 3802 Dark Iron Legacy is not his to end: its objective is placing Ironfel on the
-- Monument of Franclorn Forgewright (GO 164689), which ends it and opens the compartment holding the Shadowforge Key.
-- Durn Cinderbrew gives and ends 4136, 4134 and 4286. The stock givers and enders keep theirs; both NPCs are friendly
-- to both factions (35), so a quest taken at either end can be handed in inside.
DELETE FROM `creature_queststarter` WHERE `id` IN (300797, 300798);
INSERT INTO `creature_queststarter` (`id`, `quest`) VALUES
(300797, 4081),
(300797, 4082),
(300797, 3802),
(300797, 4123),
(300797, 4263),
(300798, 4136),
(300798, 4134),
(300798, 4286);

DELETE FROM `creature_questender` WHERE `id` IN (300797, 300798);
INSERT INTO `creature_questender` (`id`, `quest`) VALUES
(300797, 4081),
(300797, 4082),
(300797, 4123),
(300797, 4263),
(300797, 4322),
(300798, 4136),
(300798, 4134),
(300798, 4286);
