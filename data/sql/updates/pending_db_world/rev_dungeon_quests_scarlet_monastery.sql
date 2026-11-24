-- Dungeon quests stage Q3, Scarlet Monastery (.agents/plans/dungeon-quests/dungeon-quests.PLAN.md section 5, ruled by
-- the designer 2026-11-23; handoff dungeon-quests.STAGE-Q3-SM-HANDOFF.md). The four creatures (300923-300926, the
-- Argent Dawn agents) and their models are apps/dbc-tools source/npcs/scarlet_monastery/dungeon_quests.py; the four new
-- reward items (74336 Galewhisper Dirk, 74337 Argent Skirmisher's Leggings, 74338 Argent Vanguard's Greaves, 74339
-- Argent Mender's Gloves; minted in source/items/item_ids.lock) are source/items/scarlet_monastery_dungeon_quests.py;
-- the 6804 and 6806 epic upgrade is source/items/quest_rewards.lock. The item_template, item_dbc and Item.dbc rows are
-- the generated rev. No new quest and no quest item: Scarlet Monastery needs none (the hearts, books and kills exist).
-- Everything below is hand-written: the five stock quests' edits, the Test of Lore chain's two edits, the agents'
-- spawns and the starter and ender rows.

-- ---------------------------------------------------------------------------------------------------------------------
-- Open world: the Test of Lore chain (1149 -> ... -> 1160 -> 6628 -> 1394), stays Horde and stock.
-- ---------------------------------------------------------------------------------------------------------------------

-- 1160 Test of Lore (The Beginnings of the Undead Threat, from the Library, to Parqual Fintallas): the dungeon step of
-- the chain pays XP difficulty 9, 300% of a normal quest (designer 2026-11-23). Difficulty 9 exists since PR #154.
UPDATE `quest_template` SET `RewardXPDifficulty` = 9 WHERE `ID` = 1160 AND `RewardXPDifficulty` = 7;

-- 1394 Final Passage (Dorn Plainstalker, the chain's last quest): its choices 6804 Windstorm Hammer (Str) and 6806
-- Dancing Flame (Int) go blue -> epic in quest_rewards.lock (item level 41 stays), and a third choice is added, the
-- Agility epic 74336 Galewhisper Dirk (item level 41). Str, Int, Agi.
UPDATE `quest_template` SET `RewardChoiceItemID3` = 74336, `RewardChoiceItemQuantity3` = 1
    WHERE `ID` = 1394 AND `RewardChoiceItemID3` = 0 AND `RewardChoiceItemQuantity3` = 0;

-- ---------------------------------------------------------------------------------------------------------------------
-- Dungeon quests: neutral, no reputation, no prerequisite where it was zone context, neutral text.
-- ---------------------------------------------------------------------------------------------------------------------

-- 1048 Into The Scarlet Monastery (Horde, Varimathras), 1053 In the Name of the Light (Alliance, Raleigh the Devout),
-- 1113 Hearts of Zeal (Horde, Master Apothecary Faranell), 1049 Compendium of the Fallen (Horde, Sage Truthseeker),
-- 1050 Mythology of the Titans (Alliance, Librarian Mae Paledust) become neutral dungeon quests (AllowableRaces -> 0;
-- the stock Horde masks are 690 and 674, the Alliance mask 1101). Their stock givers and enders stay: a player of the
-- stock faction can still pick each up in town, and the Argent Dawn agents below give and end them for everyone.
UPDATE `quest_template` SET `AllowableRaces` = 0 WHERE `ID` IN (1048, 1113) AND `AllowableRaces` = 690;
UPDATE `quest_template` SET `AllowableRaces` = 0 WHERE `ID` = 1049 AND `AllowableRaces` = 674;
UPDATE `quest_template` SET `AllowableRaces` = 0 WHERE `ID` IN (1050, 1053) AND `AllowableRaces` = 1101;

-- A quest made neutral loses its reputation rewards (designer 2026-11-24): 1048 and 1113 gave Undercity (68), 1053
-- Stormwind (72), 1049 Thunder Bluff (81), 1050 Ironforge (47), 7 points each. All five faction slots, values and
-- overrides are cleared, guarded on the stock values (slots 2-5 and every override are 0 live).
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` IN (1048, 1113) AND `RewardFactionID1` = 68 AND `RewardFactionValue1` = 7;
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` = 1053 AND `RewardFactionID1` = 72 AND `RewardFactionValue1` = 7;
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` = 1049 AND `RewardFactionID1` = 81 AND `RewardFactionValue1` = 7;
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` = 1050 AND `RewardFactionID1` = 47 AND `RewardFactionValue1` = 7;

-- Prerequisites that were only zone context (designer 2026-11-23): 1053 loses Down the Scarlet Path (1052, chain of
-- three) and 1113 loses Going, Going, Guano! (1109), so the agents at the entrance can give them. 1052 and 1109 stay as
-- they are (neither points forward: NextQuestID 0).
UPDATE `quest_template_addon` SET `PrevQuestID` = 0 WHERE `ID` = 1053 AND `PrevQuestID` = 1052;
UPDATE `quest_template_addon` SET `PrevQuestID` = 0 WHERE `ID` = 1113 AND `PrevQuestID` = 1109;

-- The kills split by wing (designer 2026-11-23). Stock, 1048 and 1053 both asked for all four (3977 High Inquisitor
-- Whitemane, 3976 Scarlet Commander Mograine, 3975 Herod, 3974 Houndmaster Loksey). 1048 keeps Loksey (Library) and
-- Herod (Armory): two wing runs. 1053 keeps Mograine and Whitemane (Cathedral): one. Every credit entry is the normal
-- body's (see the report: the Last Stand's and Whitemane's fights end in a real kill with the player as the killer).
UPDATE `quest_template` SET `RequiredNpcOrGo1` = 3974, `RequiredNpcOrGoCount1` = 1,
    `RequiredNpcOrGo2` = 3975, `RequiredNpcOrGoCount2` = 1,
    `RequiredNpcOrGo3` = 0, `RequiredNpcOrGoCount3` = 0,
    `RequiredNpcOrGo4` = 0, `RequiredNpcOrGoCount4` = 0
    WHERE `ID` = 1048 AND `RequiredNpcOrGo1` = 3977 AND `RequiredNpcOrGo2` = 3976 AND `RequiredNpcOrGo3` = 3975
    AND `RequiredNpcOrGo4` = 3974;
UPDATE `quest_template` SET `RequiredNpcOrGo1` = 3976, `RequiredNpcOrGoCount1` = 1,
    `RequiredNpcOrGo2` = 3977, `RequiredNpcOrGoCount2` = 1,
    `RequiredNpcOrGo3` = 0, `RequiredNpcOrGoCount3` = 0,
    `RequiredNpcOrGo4` = 0, `RequiredNpcOrGoCount4` = 0
    WHERE `ID` = 1053 AND `RequiredNpcOrGo1` = 3977 AND `RequiredNpcOrGo2` = 3976 AND `RequiredNpcOrGo3` = 3975
    AND `RequiredNpcOrGo4` = 3974;

-- 1113 Hearts of Zeal: the hearts needed go 20 -> 6 and the minimum level 30 -> 27 (designer 2026-11-24). The Graveyard
-- holds 15 heart-dropping spawns at most (11.2 expected hearts), so 20 could not be finished there, and 27 is the
-- Graveyard Finder floor, so the Graveyard agent offers it to every player of the wing.
UPDATE `quest_template` SET `RequiredItemCount1` = 6, `MinLevel` = 27
    WHERE `ID` = 1113 AND `RequiredItemId1` = 5805 AND `RequiredItemCount1` = 20 AND `MinLevel` = 30;

-- 1048 Into The Scarlet Monastery: the quest level 42 -> 38 (designer 2026-11-24): it now asks for Loksey (34) and
-- Herod (37) only. The stock blue rewards stay (item level 47).
UPDATE `quest_template` SET `QuestLevel` = 38 WHERE `ID` = 1048 AND `QuestLevel` = 42;

-- The Library book chests were faction-locked to their stock quest's side (19283 Compendium of the Fallen: Thunder
-- Bluff 104; 19284 Mythology of the Titans: Ironforge 55). `GameObject::ActivateToQuest` never activates a chest whose
-- faction is hostile to the player, so the now neutral 1049 and 1050 could not be looted by the other side. Faction 0
-- with flags 4 is what the Shadowfang Keep Book of Ur chest (36738) uses. The Test of Lore chest 20726 (faction 83,
-- Horde) stays: 1160 stays Horde.
UPDATE `gameobject_template_addon` SET `faction` = 0 WHERE `entry` = 19283 AND `faction` = 104;
UPDATE `gameobject_template_addon` SET `faction` = 0 WHERE `entry` = 19284 AND `faction` = 55;

-- 1113 Hearts of Zeal pays nothing today: it gets a green choice (designer 2026-11-23), item level 38 (quest level 33 +
-- 5), one secondary each, the roles the other Scarlet Monastery rewards cover least (they hold no body armor at all):
-- 74337 Argent Skirmisher's Leggings (leather, Agility / Haste), 74338 Argent Vanguard's Greaves (plate, Strength /
-- Parry, tank), 74339 Argent Mender's Gloves (cloth, Spirit / Haste, healer).
UPDATE `quest_template` SET `RewardChoiceItemID1` = 74337, `RewardChoiceItemQuantity1` = 1,
    `RewardChoiceItemID2` = 74338, `RewardChoiceItemQuantity2` = 1,
    `RewardChoiceItemID3` = 74339, `RewardChoiceItemQuantity3` = 1
    WHERE `ID` = 1113 AND `RewardChoiceItemID1` = 0 AND `RewardChoiceItemID2` = 0 AND `RewardChoiceItemID3` = 0;

-- ---------------------------------------------------------------------------------------------------------------------
-- Neutral text (designer 2026-11-24: faction-voiced stock text is rewritten neutral). The Dark Lady, the Forsaken,
-- Cairne, the Explorers' League and the Undercity / Stormwind errand lines go; the facts of each quest stay, the
-- objective and turn-in lines name the Argent Dawn agent beside the stock giver. Each UPDATE is guarded on the stock
-- text. Locale rows (quest_template_locale and the other `_locale` tables) are not touched.
-- ---------------------------------------------------------------------------------------------------------------------

UPDATE `quest_template` SET `LogDescription` = 'Kill Houndmaster Loksey in the Library and Herod in the Armory, then report to the Argent Dawn agent at the entrance of either wing, or to Varimathras in the Undercity.',
    `QuestDescription` = 'The Scarlet Crusade has made the Monastery in Tirisfal Glades its fortress, $N, and its commanders hold the inner halls. Houndmaster Loksey keeps his hounds in the Library wing, and Herod, the Scarlet Champion, holds the Armory.$b$bTravel to the Monastery, $c, and lay waste to them both.',
    `QuestCompletionLog` = 'Return to the Argent Dawn agent at the Library or Armory entrance of the Scarlet Monastery, or to Varimathras at the Royal Quarter in the Undercity.'
    WHERE `ID` = 1048 AND `LogDescription` = 'Kill High Inquisitor Whitemane, Scarlet Commander Mograine, Herod, the Scarlet Champion and Houndmaster Loksey and then report back to Varimathras in the Undercity.' AND `QuestCompletionLog` = 'Return to Varimathras at the Royal Quarter in the Undercity.';
UPDATE `quest_request_items` SET `CompletionText` = 'Is it done, $c? Houndmaster Loksey and Herod, the Scarlet Champion, must both fall.$B$BSlaughter Loksey and his filthy mutts. Lay waste to Herod. And do not come back until it is done.'
    WHERE `ID` = 1048 AND `CompletionText` = 'Perhaps I was not explicit in my orders, $c. I want High Inquisitor Whitemane killed once and for all. And while you''re at it, take out her top brass as well.$B$BKill that zealot, Scarlet Commander Mograine. Lay waste to Herod, the Scarlet Champion. And slaughter Houndmaster Loksey and his filthy mutts too.$B$BNow begone!';
UPDATE `quest_offer_reward` SET `RewardText` = 'Well done, $c. ''Twas no small task I asked of you.$b$bThe Crusade''s grip on the Library and the Armory is broken, and your tenacity in combat will be remembered.'
    WHERE `ID` = 1048 AND `RewardText` = 'You have served the Dark Lady well, $c. ''Twas no small task I asked of you.$b$bYour loyalty to the Forsaken has been noted. And your tenacity in combat will be remembered.';

UPDATE `quest_template` SET `LogDescription` = 'Kill Scarlet Commander Mograine and High Inquisitor Whitemane in the Cathedral, then report to the Argent Dawn agent at the Cathedral entrance, or to Raleigh the Devout in Southshore.',
    `QuestDescription` = 'Many who served the Scarlet Crusade did so with honor, loyalty and pride. They believed its cause to be a noble one: to rid Azeroth of the undead.$b$bBut as the Crusade settled into the Monastery in Tirisfal Glades its grasp on reality slipped. It now thinks everyone is plagued who doesn''t wear its tabard, and innocent men and women have been tortured because they were supposedly plagued.$b$bThe Scarlet Crusade must be crushed in the name of the Light. At its head, in the Cathedral, stand Scarlet Commander Mograine and High Inquisitor Whitemane. You, $n, must put an end to them.',
    `QuestCompletionLog` = 'Return to the Argent Dawn agent at the Cathedral entrance of the Scarlet Monastery, or to Raleigh the Devout at Southshore in Hillsbrad Foothills.'
    WHERE `ID` = 1053 AND `LogDescription` = 'Kill High Inquisitor Whitemane, Scarlet Commander Mograine,  Herod, the Scarlet Champion and Houndmaster Loksey and then report back to Raleigh the Devout in Southshore.' AND `QuestCompletionLog` = 'Return to Raleigh the Devout at Southshore in Hillsbrad Foothills.';
UPDATE `quest_request_items` SET `CompletionText` = 'The corruption in the Monastery will not end until the highest ranking officials have been removed.$b$bIn the name of the Light, slay Scarlet Commander Mograine and High Inquisitor Whitemane. Once they have fallen, perhaps the true cause can be rekindled. Until then, anyone who crosses the path of the Crusade lies in peril.'
    WHERE `ID` = 1053 AND `CompletionText` = 'The corruption in the Monastery will not end until the highest ranking officials have been removed.$b$bIn the name of the Light, slay High Inquisitor Whitemane, Scarlet Commander Mograine,  Herod, the Scarlet Champion and Houndmaster Loksey. Once they have fallen, perhaps the true cause can be rekindled. Until then, anyone who crosses the path of the Crusade lies in peril.$b$bVenture forth from Southshore and make it so!';

UPDATE `quest_template` SET `LogDescription` = 'Collect 6 Hearts of Zeal in the Scarlet Monastery and bring them to the Argent Dawn agent at the entrance of any wing, or to Master Apothecary Faranell in the Undercity.',
    `QuestDescription` = 'The zeal of the Scarlet Crusade burns past reason, $N, and there is something worth studying in the heart of a true fanatic. I am gathering them for an experiment: six hearts, no fewer.$b$bThe Scarlet Monastery is full of the crazed disciples of the Crusade, in every wing, inside and outside the halls. Which you slay matters not, any of them may have the heart I need.',
    `QuestCompletionLog` = 'Return to the Argent Dawn agent at the entrance of any wing of the Scarlet Monastery, or to Master Apothecary Faranell at the Apothecarium in Undercity.'
    WHERE `ID` = 1113 AND `LogDescription` = 'Master Apothecary Faranell in the Undercity wants 20 Hearts of Zeal.' AND `QuestCompletionLog` = 'Return to Master Apothecary Faranell at the Apothecarium in Undercity.';
UPDATE `quest_request_items` SET `CompletionText` = 'Have you gathered the hearts from the Scarlet Monastery, $N? I will need all six for my work.'
    WHERE `ID` = 1113 AND `CompletionText` = 'Have you returned from the Scarlet Monastery? I''ll need many hearts for this delightful experiment!$b$bNo doubt, Varimathras and the Dark Lady will be pleased to be rid of the Scarlet Scum as well...';
UPDATE `quest_offer_reward` SET `RewardText` = 'My what an abundance of gore you have brought me, $N! Your efforts have been most excellent! Take your pick of what we can spare.'
    WHERE `ID` = 1113 AND `RewardText` = 'My what an abundance of gore you have brought me, $N! Your efforts have been most excellent!';

UPDATE `quest_template` SET `LogDescription` = 'Retrieve the Compendium of the Fallen from the Library of the Scarlet Monastery and return it to the Argent Dawn agent at the Library entrance, or to Sage Truthseeker in Thunder Bluff.',
    `QuestDescription` = 'Too many pacts are struck in haste, $N, and I would rather know the facts for myself.$b$bDeep within the Scarlet Monastery lies the Compendium of the Fallen, guarded by crazed human zealots. Their method is forged from insanity but their research might prove useful.',
    `QuestCompletionLog` = 'Return to the Argent Dawn agent at the Library entrance of the Scarlet Monastery, or to Sage Truthseeker in Thunder Bluff.'
    WHERE `ID` = 1049 AND `LogDescription` = 'Retrieve the Compendium of the Fallen from the Monastery in Tirisfal Glades and return to Sage Truthseeker in Thunder Bluff.' AND `QuestCompletionLog` = 'Return to Sage Truthseeker in Thunder Bluff.';
UPDATE `quest_request_items` SET `CompletionText` = 'I do not trust what I cannot read for myself. Once I have a chance to gather all the knowledge available I can offer sound counsel to those who need it.$b$bHave you had a chance to travel to the Scarlet Monastery? The Compendium of the Fallen is just one piece in this complicated puzzle...'
    WHERE `ID` = 1049 AND `CompletionText` = 'Cairne is a brave and noble leader and I would trust him with my own life. But it is others that I do not trust in this political climate.$b$bOnce I have a chance to gather all the knowledge available I can provide sound council to the Chieftain.$b$bHave you had a chance to travel to Tirisfal Glades? To the Scarlet Monastery? The Compendium of the Fallen is just one piece in this complicated puzzle...';
UPDATE `quest_offer_reward` SET `RewardText` = 'The Compendium of the Fallen! I was beginning to wonder if the very book existed!$b$bYou have done a great service to everyone who studies the Crusade, $N. Your dedication shall not be forgotten.'
    WHERE `ID` = 1049 AND `RewardText` = 'The Compendium of the Fallen! I was beginning to wonder if the very book existed!$b$bYou have served the Tauren of Thunder Bluff well, $N. Your dedication shall not be forgotten.';

UPDATE `quest_template` SET `LogDescription` = 'Retrieve Mythology of the Titans from the Library of the Scarlet Monastery and bring it to the Argent Dawn agent at the Library entrance, or to Librarian Mae Paledust in Ironforge.',
    `QuestCompletionLog` = 'Return to the Argent Dawn agent at the Library entrance of the Scarlet Monastery, or to Librarian Mae Paledust at the Hall of Explorers in Ironforge.'
    WHERE `ID` = 1050 AND `LogDescription` = 'Retrieve Mythology of the Titans from the Monastery and bring it to Librarian Mae Paledust in Ironforge.' AND `QuestCompletionLog` = 'Return to Librarian Mae Paledust at the Hall of Explorers in Ironforge.';
UPDATE `quest_request_items` SET `CompletionText` = 'The Monastery was a seminary for Paladins-in-training. Once a stronghold of the Light, it fell into the hands of the crazed zealots of the Scarlet Crusade.$b$bThe Crusade believed their goal a noble one: to purify the land of the undead plague. But insanity tainted their plight and now they stand enemies to all.$b$bBring Mythology of the Titans to me so I can study it and keep it safe.$b$bThe corrupt halls of the Monastery are no place for such a historical treasure.'
    WHERE `ID` = 1050 AND `CompletionText` = 'The Monastery was a seminary for Paladins-in-training. Once a stronghold of the Light, it fell into the hands of the crazed zealots of the Scarlet Crusade.$b$bThe Crusade believed their goal a noble one: to purify the land of the undead plague. But insanity tainted their plight and now they stand enemies to all.$b$bBring Mythology of the Titans to me so I can study it and house it here in Ironforge.$b$bThe corrupt halls of the Monastery are no place for such a historical treasure.';
UPDATE `quest_offer_reward` SET `RewardText` = 'You have rescued the sacred text!$b$bYour journey was long and acquiring the book was undoubtedly no easy task. But everyone who studies the past stands to benefit from your success.$b$bThank you, $N.'
    WHERE `ID` = 1050 AND `RewardText` = 'You have rescued the sacred text!$b$bYour journey was long and acquiring the book was undoubtedly no easy task. But  the dwarves of Ironforge stand to benefit from your success.$b$bThank you, $N, on behalf of the Explorers'' League.';

-- ---------------------------------------------------------------------------------------------------------------------
-- The four Argent Dawn agents: spawns, starters and enders.
-- ---------------------------------------------------------------------------------------------------------------------

-- Spawns, normal difficulty only (spawnMask 1: heroic is level 60 and has no dungeon quests), guid = 10 x entry like
-- the other dungeon builds' hand spawns. Map 189, phase 1, standing still, 300 s respawn. The positions are the
-- designer's in-game spots (2026-11-24; z is the floor), not moved by the measurements below, which are for the
-- record only: the Dungeon Finder arrival point of each wing (areatrigger_teleport, Section starts of the dungeon
-- doc), the nearest spawns (3D, normal spawns on map 189, hostile = hostile to a Human or an Orc player by
-- FactionTemplate) and the nearest waypoint-path segment (every `waypoint_data` path of a map 189 spawn: its
-- creature_addon path_id, or guid x 10, closing last-to-first segment included). No spot is on a patrol path.
--   300923 Agent Corwin Hale, Graveyard: 1703.27, 1053.02, 18.49, o 2.37. 14.3 yd east of the arrival point
--     (areatrigger 45: 1688.99, 1053.48, 18.68). Nearest spawn and nearest hostile: Scarlet Sentry 27438 at 55.3 yd
--     (and 11.6 yd below him); nearest waypoint path Scarlet Torturer 27440's (path 274400) at 89.1 yd.
--   300924 Archivist Tobias Merrow, Library: 271.19, -207.38, 19.20, o 3.86. 15.9 yd from the arrival point
--     (areatrigger 614: 255.35, -209.09, 18.68). Nearest hostile spawns: Scarlet Gallants 40072 and 40071 at 26.4 and
--     26.6 yd, then 37.6 yd; nearest waypoint path Scarlet Adept 40058's (path 400580) at 25.7 yd.
--   300925 Captain Dorrin Ashe, Armory: 1624.68, -311.39, 18.01, o 4.75. 18.4 yd from the arrival point (areatrigger
--     612: 1610.83, -323.43, 18.67). Nearest hostile spawns: Scarlet Soldiers 40131 at 23.2 yd and 40126 at 30.5 yd,
--     then 50.7 yd; nearest waypoint path Scarlet Soldier 40129's (path 401290) at 51.4 yd.
--   300926 Father Anselm Gray, Cathedral: 870.82, 1309.63, 18.01, o 1.59. 19.2 yd from the arrival point (areatrigger
--     610: 855.68, 1321.5, 18.67). Nearest hostile spawn: Scarlet Myrmidon 39945 at 14.2 yd (21.1 yd from the arrival
--     point), the next ones 50 yd or more; the wing has no waypoint path (the nearest of the map is 905 yd away).
DELETE FROM `creature` WHERE `id` = 300923 AND `guid` = 3009230;
DELETE FROM `creature` WHERE `id` = 300924 AND `guid` = 3009240;
DELETE FROM `creature` WHERE `id` = 300925 AND `guid` = 3009250;
DELETE FROM `creature` WHERE `id` = 300926 AND `guid` = 3009260;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(3009230, 300923, 189, 0, 0, 1, 1, 0, 1703.270, 1053.020, 18.490, 2.3700, 300, 0, 12340, 0,
    'Agent Corwin Hale - Scarlet Monastery Graveyard quest giver'),
(3009240, 300924, 189, 0, 0, 1, 1, 0, 271.190, -207.380, 19.200, 3.8600, 300, 0, 12340, 0,
    'Archivist Tobias Merrow - Scarlet Monastery Library quest giver'),
(3009250, 300925, 189, 0, 0, 1, 1, 0, 1624.680, -311.390, 18.010, 4.7500, 300, 0, 12340, 0,
    'Captain Dorrin Ashe - Scarlet Monastery Armory quest giver'),
(3009260, 300926, 189, 0, 0, 1, 1, 0, 870.820, 1309.630, 18.010, 1.5900, 300, 0, 12340, 0,
    'Father Anselm Gray - Scarlet Monastery Cathedral quest giver');

-- Starters and enders: each agent gives and ends only the quests with an objective in its wing (the plan's table).
-- Hearts of Zeal (1113) at all four (6 hearts, dropped in every wing); Into The Scarlet Monastery (1048) at the Library
-- (Loksey) and the Armory (Herod); In the Name of the Light (1053) at the Cathedral (Mograine, Whitemane); Compendium
-- of the Fallen (1049) and Mythology of the Titans (1050) at the Library (their chests). The stock givers and enders
-- (Master Apothecary Faranell 2055, Varimathras 2425, Raleigh the Devout 3980, Sage Truthseeker 3978, Librarian Mae
-- Paledust 3979) keep theirs: the agents are friendly to both factions (35), so a quest taken at either end can be
-- handed in at the entrance, whichever the stock ender's faction is.
DELETE FROM `creature_queststarter` WHERE `id` IN (300923, 300924, 300925, 300926);
INSERT INTO `creature_queststarter` (`id`, `quest`) VALUES
(300923, 1113),
(300924, 1113),
(300924, 1049),
(300924, 1050),
(300924, 1048),
(300925, 1113),
(300925, 1048),
(300926, 1113),
(300926, 1053);

DELETE FROM `creature_questender` WHERE `id` IN (300923, 300924, 300925, 300926);
INSERT INTO `creature_questender` (`id`, `quest`) VALUES
(300923, 1113),
(300924, 1113),
(300924, 1049),
(300924, 1050),
(300924, 1048),
(300925, 1113),
(300925, 1048),
(300926, 1113),
(300926, 1053);
