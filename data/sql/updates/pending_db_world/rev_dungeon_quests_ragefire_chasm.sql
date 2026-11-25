-- Ragefire Chasm build, the quests WP (Q; .agents/plans/ragefire-chasm-build/ragefire-chasm-build.HANDOFF.md 4.Q and
-- section 7 #38-#40, all ruled "as recommended" 2026-11-24; spec .agents/plans/dungeon-quests/dungeon-quests.PLAN.md
-- section 1, ruled by the designer 2026-11-23). The creature (300989 Grunt Dranok) and its model are apps/dbc-tools
-- source/npcs/ragefire_chasm/dungeon_quests.py; the seven reward items are
-- source/items/ragefire_chasm_dungeon_quests.py and the green -> blue edit of 15449-15451 is in quest_rewards.lock (the
-- item_template, item_dbc and Item.dbc rows and the item ids are the deploy's generated rev: this file is named so it
-- sorts after every `rev_<digits>.sql`). Everything below is hand-written: the
-- quests' changes, the neutral text, the giver's spawn and weapon, the starter / ender rows. No new quest id (nothing
-- in 90100-90199), no new item_template row (every quest item is stock).
--
-- 5728 Hidden Enemies (open world, stays Horde, chain 5726 -> 5727 -> 5728 -> 5729) is touched twice only: XP
-- difficulty 7 -> 9 (300% of a normal quest, `questxp_dbc`) and a new epic choice. 14356 (the unspawned duplicate of
-- 5725) is untouched, but it shares the three legs 15449-15451, which turn blue for it too.

-- The five dungeon quests become neutral (AllowableRaces 690, the Horde races, -> 0). 5722 and 5724 are the Satchel
-- pair (5724's PrevQuestID 5722 and 5722's RewardNextQuest 5724 stay: the pair is a stock chain). Rewards, XP
-- difficulty and stock givers and enders stay: Varimathras (2425) still starts and ends 5725, Neeru Fireblade (3216)
-- still starts and ends 5761 (and ends 5729), Rahauro (11833) still starts 5722 and 5723 and ends 5723 and 5724, Maur
-- Grimtotem's corpse (11834) still ends 5722 and starts 5724. None has an exclusive group.
UPDATE `quest_template` SET `AllowableRaces` = 0 WHERE `ID` IN (5722, 5723, 5724, 5725, 5761) AND `AllowableRaces` = 690;

-- A quest made neutral loses its reputation rewards (designer 2026-11-24): 5723 and 5724 gave Thunder Bluff (81) 7 and
-- 5725 gave Undercity (68) 7; 5722 and 5761 give none. All five faction slots, values and overrides are cleared,
-- guarded on the stock values. 5728 keeps its Orgrimmar (76) 7: it stays a Horde quest.
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` IN (5723, 5724) AND `RewardFactionID1` = 81 AND `RewardFactionValue1` = 7;
UPDATE `quest_template` SET `RewardFactionID1` = 0, `RewardFactionValue1` = 0, `RewardFactionOverride1` = 0,
    `RewardFactionID2` = 0, `RewardFactionValue2` = 0, `RewardFactionOverride2` = 0,
    `RewardFactionID3` = 0, `RewardFactionValue3` = 0, `RewardFactionOverride3` = 0,
    `RewardFactionID4` = 0, `RewardFactionValue4` = 0, `RewardFactionOverride4` = 0,
    `RewardFactionID5` = 0, `RewardFactionValue5` = 0, `RewardFactionOverride5` = 0
    WHERE `ID` = 5725 AND `RewardFactionID1` = 68 AND `RewardFactionValue1` = 7;

-- 5728 Hidden Enemies: XP difficulty 7 -> 9 (stock 1,750 base at level 16 -> 3,450, about 2x), and the epic choice,
-- three waist pieces at item level 26 (Str mail, Agi leather, Int cloth; section 7 #39 A). The stock reward is 8 silver
-- (RewardMoney 800), which stays. The items are the minted ids of
-- item_ids.lock (rfcq_*; the test pins them). Each UPDATE is guarded on the stock values.
UPDATE `quest_template` SET `RewardXPDifficulty` = 9 WHERE `ID` = 5728 AND `RewardXPDifficulty` = 7;
UPDATE `quest_template` SET
    `RewardChoiceItemID1` = 74463,
    `RewardChoiceItemQuantity1` = 1,
    `RewardChoiceItemID2` = 74464,
    `RewardChoiceItemQuantity2` = 1,
    `RewardChoiceItemID3` = 74465,
    `RewardChoiceItemQuantity3` = 1
    WHERE `ID` = 5728 AND `RewardChoiceItemID1` = 0 AND `RewardChoiceItemID2` = 0 AND `RewardChoiceItemID3` = 0;

-- 5761 Slaying the Beast: a choice of two blues, Agility leather boots or a tank shield (the stock reward is 8 silver
-- only, which stays). 5723 Testing an Enemy's Strength: a choice of two greens, Strength mail gloves or healer cloth
-- gloves (the stock reward is 7 silver only, which stays). Same minted ids and guard as above.
UPDATE `quest_template` SET
    `RewardChoiceItemID1` = 74466,
    `RewardChoiceItemQuantity1` = 1,
    `RewardChoiceItemID2` = 74467,
    `RewardChoiceItemQuantity2` = 1
    WHERE `ID` = 5761 AND `RewardChoiceItemID1` = 0 AND `RewardChoiceItemID2` = 0;
UPDATE `quest_template` SET
    `RewardChoiceItemID1` = 74468,
    `RewardChoiceItemQuantity1` = 1,
    `RewardChoiceItemID2` = 74469,
    `RewardChoiceItemQuantity2` = 1
    WHERE `ID` = 5723 AND `RewardChoiceItemID1` = 0 AND `RewardChoiceItemID2` = 0;

-- Neutral text (designer 2026-11-24 build ruling; handoff section 7 #40 A). The stock text is in the Horde's voice (the
-- Dark Lady, Thrall, "our orc brethren", Magatha's diplomats) and the quest log lines send the player to Thunder Bluff,
-- the Undercity or Orgrimmar, but the quests are now also handed in at the orc at the entrance (and an Alliance
-- player reaches only him). The story facts stay (the troggs, the Searing Blade, the books, the Felguard's heart, the
-- satchel). The log lines name both enders. 5725's QuestCompletionLog also loses a stock error (Varimathras is in the
-- Undercity, not at Lordamere Lake in Silverpine Forest). No text sends the player to a Horde city to find the Chasm:
-- whoever reads it at the orc is already in it. 5725's progress text was Varimathras's haughty voice and is now plain
-- (both enders share it). 5722's log text and 5761's progress text are already neutral and stay. Each UPDATE is
-- guarded on the stock text. Locale rows (the `_locale` tables) are not touched.
UPDATE `quest_template` SET `LogDescription` = 'Bring the books Spells of Shadow and Incantations from the Nether to Grunt Dranok at the entrance to Ragefire Chasm, or to Varimathras in the Undercity.',
    `QuestDescription` = 'Many denizens of the Legion bestow gifts on their followers, as you may well know. Some of those gifts are better off in careful hands than in the hands of those with... lesser vision.$B$BA sect of the Shadow Council hidden in the caverns below Orgrimmar, the Searing Blade, is a prime example. Its members have come into possession of two powerful spell books, and there are those who would like to "borrow" them. You will get them.',
    `QuestCompletionLog` = 'Return to Grunt Dranok at the entrance to Ragefire Chasm, or to Varimathras in the Undercity.'
    WHERE `ID` = 5725 AND `LogDescription` = 'Bring the books Spells of Shadow and Incantations from the Nether to Varimathras in Undercity.';
UPDATE `quest_template` SET `LogDescription` = 'Enter Ragefire Chasm and slay Taragaman the Hungerer, then bring his heart back to Grunt Dranok at the entrance, or to Neeru Fireblade in Orgrimmar.',
    `QuestDescription` = 'The task set upon me is to root out the creatures responsible for infesting this great city with demonic influence. The Burning Blade is one threat, but there are others; the Searing Blade for instance, who make their home in Ragefire Chasm, secretly attempting to subvert innocent folk.$B$BIf they are to be stopped, then their leader must be slain--a Felguard named Taragaman the Hungerer.$B$BKill him and bring me his heart. It will prove the Searing Blade has lost its master, and that is worth a reward.',
    `QuestCompletionLog` = 'Return to Grunt Dranok at the entrance to Ragefire Chasm, or to Neeru Fireblade in Orgrimmar.'
    WHERE `ID` = 5761 AND `LogDescription` = 'Enter Ragefire Chasm and slay Taragaman the Hungerer, then bring his heart back to Neeru Fireblade in Orgrimmar.';
UPDATE `quest_template` SET `QuestDescription` = 'A tauren named Maur Grimtotem went into Ragefire Chasm to speak to the troggs, and he never came out. The Grimtotem have heard word that he found something peculiar down there, but he never made it back to show them. They want his body found--if it still exists--and any sign of what he found.$B$BBring back any items of interest, and I''m sure they will be very generous in their reward.$B$BSearch the depths of Ragefire Chasm.'
    WHERE `ID` = 5722 AND `QuestDescription` = 'The troggs are not the only thing that interested Magatha in Ragefire Chasm. She has heard word that one of her servants, a Maur Grimtotem, found something peculiar while in the Chasm, but he never made it out to show her what. She''d like Maur''s body found--if it still exists--and any signs of what he found while attempting to speak to the troggs.$B$BReturn to Magatha any items of interest, and I''m sure she would be very generous in her reward.$B$BAgain, seek the Chasm in the darkest areas of Orgrimmar.';
UPDATE `quest_template` SET `LogDescription` = 'Take the Grimtotem Satchel to Grunt Dranok at the entrance to Ragefire Chasm, or to Rahauro in Thunder Bluff.',
    `QuestDescription` = 'You find a satchel under the body of the tauren. It is still gripped tightly in his arms as though he was trying to protect it while being attacked by the troggs.$B$BRemoving the satchel from his vice-like grip, you stow it with your own equipment and prepare to make your way out of the tunnels, to the entrance of the Chasm or back to Rahauro in Thunder Bluff.',
    `QuestCompletionLog` = 'Return to Grunt Dranok at the entrance to Ragefire Chasm, or to Rahauro at Elder Rise in Thunder Bluff.'
    WHERE `ID` = 5724 AND `LogDescription` = 'Take the Grimtotem Satchel to Rahauro in Thunder Bluff.';
UPDATE `quest_template` SET `LogDescription` = 'Kill 8 Ragefire Troggs and 8 Ragefire Shaman in Ragefire Chasm, then return to Grunt Dranok at the entrance, or to Rahauro in Thunder Bluff.',
    `QuestDescription` = 'Beneath the city of Orgrimmar, stout creatures known as troggs have started coming to the surface from deep below the lava filled tunnels. The tauren sought peace with them, but the troggs turned on their diplomats and killed them. The tauren will not allow such treatment of their people, and now consider the creatures a threat to everyone who lives above.$B$BGo into Ragefire Chasm and put an end to this trogg threat before it overwhelms the city above.',
    `QuestCompletionLog` = 'Return to Grunt Dranok at the entrance to Ragefire Chasm, or to Rahauro at Elder Rise in Thunder Bluff.'
    WHERE `ID` = 5723 AND `LogDescription` = 'Search Orgrimmar for Ragefire Chasm, then kill 8 Ragefire Troggs and 8 Ragefire Shaman before returning to Rahauro in Thunder Bluff.';
UPDATE `quest_offer_reward` SET `RewardText` = 'Good, $c. You have served well. These books are in better hands now than the Searing Blade''s, and your perseverance and ambition will be of great use to those who know what to do with them.$B$BPerhaps there will be other tasks for you in the future.'
    WHERE `ID` = 5725 AND `RewardText` = 'Good, $c. You have done well in serving the Dark Lady. Your continued perseverance and ambition will be of great use to the Lady''s subjects. Return to me again in the future. Perhaps I will have other tasks for you that will aid the Dark Lady in her attempts at overtaking the Lich King and completely freeing the Scourge.';
UPDATE `quest_offer_reward` SET `RewardText` = 'Ha! You''ve done it! This city is safer for it.$B$BI will see that this heart is taken care of properly. For now though, you must celebrate your victory. Word of your success will be passed along.$B$BThank you for your aid, $c.'
    WHERE `ID` = 5761 AND `RewardText` = 'Ha! You''ve done it! Thrall will be so pleased.$b$bI will ensure this heart is taken care of properly.$b$bFor now though, you must celebrate your victory. I will inform Thrall of your success.$b$bThank you for your aid, $c.';
UPDATE `quest_offer_reward` SET `RewardText` = 'The body looks seriously beaten by clubs or fists, but most of the corpse''s clothing and equipment still looks present. It seems the troggs do not overly care much for material wealth.$B$BYou begin to search the body for anything of interest that might help the Grimtotem.'
    WHERE `ID` = 5722 AND `RewardText` = 'The body looks seriously beaten by clubs or fists, but most of the corpse''s clothing and equipment still looks present. It seems the troggs do not overly care much for material wealth.$B$BYou begin to search the body for anything of interest that might help Magatha.';
UPDATE `quest_offer_reward` SET `RewardText` = 'Excellent, $N. Thank you.$B$BThe Grimtotem asked that whoever found their clansman be given this. Please, take it in thanks.'
    WHERE `ID` = 5724 AND `RewardText` = 'Excellent, $N. Thank you.$b$bMagatha told me that if you were successful in finding her clansman that you be given this. Please, take it in thanks.';
UPDATE `quest_offer_reward` SET `RewardText` = 'I am glad to see you took this task seriously. Thank you, $N. I''m sure the troggs will have a harder time coming to the surface with their numbers so greatly reduced.$B$BPerhaps in the future we can take time to figure out where such creatures came from, and what they really want.'
    WHERE `ID` = 5723 AND `RewardText` = 'I am glad to see you took Magatha''s task seriously. Thank you, $N. I''m sure the troggs will have a harder time coming to the surface with their numbers so greatly reduced.$B$BPerhaps in the future we can take time to figure out where such creatures came from, and what they really want.';
UPDATE `quest_request_items` SET `CompletionText` = 'You have the books, $c? Both of them? Let me see.'
    WHERE `ID` = 5725 AND `CompletionText` = 'There are a hundred other tasks awaiting my attention, $C. Do you have the books?';
UPDATE `quest_request_items` SET `CompletionText` = 'Were you able to find anything, $N? Any clues as to why one of the Grimtotem had to die needlessly would be helpful.'
    WHERE `ID` = 5724 AND `CompletionText` = 'Were you able to find anything, $N? Any clues as to why one of her clansman had to die needlessly would be helpful.';
UPDATE `quest_request_items` SET `CompletionText` = 'How goes the hunt in the Chasm? And the troggs?$B$BThe threat cannot be allowed to persist--it will only injure those who live above if it continues.'
    WHERE `ID` = 5723 AND `CompletionText` = 'How goes your search for the Chasm? And the troggs?$B$BThe threat cannot be allowed to persist--it will only injure our orc brethren if it continues.';

-- Grunt Dranok's weapon: a two-handed axe with a pick (Monster - Axe 5289), as a stock orc grunt stands. Equipment id 1
-- is the creature's own row (CreatureID 300989, ID 1).
DELETE FROM `creature_equip_template` WHERE `CreatureID` = 300989;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
(300989, 1, 5289, 0, 0, 0);

-- The entrance giver's spawn, normal difficulty only (spawnMask 1: heroic is level 60 and has no dungeon quests; the
-- dungeon's `normal_only_creatures` keeps the heroic mask off it), guid = 10 x entry like the other dungeon builds'
-- hand spawns. Map 389, phase 1, standing still, 300 s respawn.
--   300989 Grunt Dranok, the entrance giver: 8.24, -22.39, -19.71, o 2.89. The designer's in-game spot (2026-11-24;
--     z is the floor as given: the navmesh reads -17.44 there, NAVMESH-REPORT misfit 7, section 7 #26 A), not moved by
--     the measurements below, which are for the record only. Dungeon Finder arrival point: areatrigger_teleport 2230
--     Ragefire Chasm - Ogrimmar Instance (3.81, -14.82, -17.84, o 4.39): the spot is 9.0 yd from it (3D). Measured
--     (3D) to the nearest spawns: Earthborer 38043 36.9 yd (wanders 5 yd, detection 20), Molten Elemental 38042
--     48.9 yd, Earthborer 38045 51.1 yd, Earthborer 38041 53.6 yd; the nearest hostile can reach no nearer than 32 yd
--     and is outside its own aggro range. Nearest waypoint path (the closing segment included, 3D point to segment):
--     path 486480 (Ragefire Trogg 48648) 158.9 yd, 486690 (Ragefire Shaman 48669) 213.4 yd, 486550 227.7 yd, 487070
--     273.5 yd: on no patrol path. Nearest gameobject: a purple brazier (guid 28517) at 45.9 yd. No hostility event,
--     scripted brawl or SmartAI in range.
DELETE FROM `creature` WHERE `id` = 300989 AND `guid` = 3009890;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `MovementType`, `VerifiedBuild`,
    `CreateObject`, `Comment`) VALUES
(3009890, 300989, 389, 0, 0, 1, 1, 1, 8.24, -22.39, -19.71, 2.89, 300, 0, 12340, 0,
    'Grunt Dranok - Ragefire Chasm entrance quest giver');

-- Starters and enders. The entrance giver starts 5725, 5761, 5722 and 5723 and ends 5725, 5761, 5724 and 5723. He does
-- not end 5722 (Maur Grimtotem's corpse, 11834, stays its ender: the search is the objective) and does not start
-- 5724 (the corpse starts it, as stock; the Satchel quest item 14381 is its StartItem). The stock givers and enders
-- (Varimathras 2425, Neeru Fireblade 3216, Rahauro 11833, Maur Grimtotem 11834) keep theirs.
DELETE FROM `creature_queststarter` WHERE `id` = 300989 AND `quest` IN (5725, 5761, 5722, 5723);
INSERT INTO `creature_queststarter` (`id`, `quest`) VALUES
(300989, 5725),
(300989, 5761),
(300989, 5722),
(300989, 5723);

DELETE FROM `creature_questender` WHERE `id` = 300989 AND `quest` IN (5725, 5761, 5724, 5723);
INSERT INTO `creature_questender` (`id`, `quest`) VALUES
(300989, 5725),
(300989, 5761),
(300989, 5724),
(300989, 5723);
