-- DB update 2026_09_04_04 -> 2026_09_04_05
--
-- De-gate class abilities from quest-only rewards: make them purchasable from the class
-- trainer directly. Every trainer_spell row below teaches a spell that, on this server, was
-- previously obtainable only by completing a specific quest (see docs/bugs-and-fixes.md-style
-- reasoning in the conversation that produced this migration - quest_template.RewardSpell
-- casts a wrapper 'Teach X' spell whose own SPELL_EFFECT_LEARN_SPELL effects grant the real
-- ability). Paladin's and Warlock's mount-teaching quests (Summon Warhorse/Charger, Summon
-- Felsteed/Dreadsteed) are deliberately excluded per user direction - those stay quest-only.
-- The underlying quests are left untouched (still completable, still reward the same spells -
-- redundant, but harmless once the trainer offers the same thing).
--
-- Warrior
DELETE FROM `trainer_spell` WHERE (`TrainerId` = 1 AND `SpellId` = 71) OR (`TrainerId` = 1 AND `SpellId` = 7386) OR (`TrainerId` = 1 AND `SpellId` = 355) OR (`TrainerId` = 1 AND `SpellId` = 2458) OR (`TrainerId` = 2 AND `SpellId` = 71) OR (`TrainerId` = 2 AND `SpellId` = 7386) OR (`TrainerId` = 2 AND `SpellId` = 355) OR (`TrainerId` = 2 AND `SpellId` = 2458) OR (`TrainerId` = 2 AND `SpellId` = 20252) OR (`TrainerId` = 200 AND `SpellId` = 71) OR (`TrainerId` = 200 AND `SpellId` = 7386) OR (`TrainerId` = 200 AND `SpellId` = 355) OR (`TrainerId` = 200 AND `SpellId` = 2458) OR (`TrainerId` = 200 AND `SpellId` = 20252) OR (`TrainerId` = 201 AND `SpellId` = 71) OR (`TrainerId` = 201 AND `SpellId` = 7386) OR (`TrainerId` = 201 AND `SpellId` = 355) OR (`TrainerId` = 201 AND `SpellId` = 2458) OR (`TrainerId` = 201 AND `SpellId` = 20252);
INSERT INTO `trainer_spell` (`TrainerId`, `SpellId`, `MoneyCost`, `ReqSkillLine`, `ReqSkillRank`, `ReqAbility1`, `ReqAbility2`, `ReqAbility3`, `ReqLevel`, `VerifiedBuild`) VALUES
(1, 71, 600, 0, 0, 0, 0, 0, 10, 0),
(1, 7386, 600, 0, 0, 0, 0, 0, 10, 0),
(1, 355, 600, 0, 0, 0, 0, 0, 10, 0),
(1, 2458, 10000, 0, 0, 0, 0, 0, 30, 0),
(2, 71, 600, 0, 0, 0, 0, 0, 10, 0),
(2, 7386, 600, 0, 0, 0, 0, 0, 10, 0),
(2, 355, 600, 0, 0, 0, 0, 0, 10, 0),
(2, 2458, 10000, 0, 0, 0, 0, 0, 30, 0),
(2, 20252, 10000, 0, 0, 0, 0, 0, 30, 0),
(200, 71, 600, 0, 0, 0, 0, 0, 10, 0),
(200, 7386, 600, 0, 0, 0, 0, 0, 10, 0),
(200, 355, 600, 0, 0, 0, 0, 0, 10, 0),
(200, 2458, 10000, 0, 0, 0, 0, 0, 30, 0),
(200, 20252, 10000, 0, 0, 0, 0, 0, 30, 0),
(201, 71, 600, 0, 0, 0, 0, 0, 10, 0),
(201, 7386, 600, 0, 0, 0, 0, 0, 10, 0),
(201, 355, 600, 0, 0, 0, 0, 0, 10, 0),
(201, 2458, 10000, 0, 0, 0, 0, 0, 30, 0),
(201, 20252, 10000, 0, 0, 0, 0, 0, 30, 0);

-- Paladin
DELETE FROM `trainer_spell` WHERE (`TrainerId` = 3 AND `SpellId` = 7328) OR (`TrainerId` = 4 AND `SpellId` = 7328) OR (`TrainerId` = 202 AND `SpellId` = 7328) OR (`TrainerId` = 202 AND `SpellId` = 5502) OR (`TrainerId` = 203 AND `SpellId` = 7328) OR (`TrainerId` = 203 AND `SpellId` = 5502);
INSERT INTO `trainer_spell` (`TrainerId`, `SpellId`, `MoneyCost`, `ReqSkillLine`, `ReqSkillRank`, `ReqAbility1`, `ReqAbility2`, `ReqAbility3`, `ReqLevel`, `VerifiedBuild`) VALUES
(3, 7328, 1000, 0, 0, 0, 0, 0, 12, 0),
(4, 7328, 1000, 0, 0, 0, 0, 0, 12, 0),
(202, 7328, 1000, 0, 0, 0, 0, 0, 12, 0),
(202, 5502, 4000, 0, 0, 0, 0, 0, 20, 0),
(203, 7328, 1000, 0, 0, 0, 0, 0, 12, 0),
(203, 5502, 4000, 0, 0, 0, 0, 0, 20, 0);

-- Hunter
DELETE FROM `trainer_spell` WHERE (`TrainerId` = 7 AND `SpellId` = 1515) OR (`TrainerId` = 7 AND `SpellId` = 883) OR (`TrainerId` = 7 AND `SpellId` = 2641) OR (`TrainerId` = 7 AND `SpellId` = 6991) OR (`TrainerId` = 7 AND `SpellId` = 982) OR (`TrainerId` = 8 AND `SpellId` = 1515) OR (`TrainerId` = 8 AND `SpellId` = 883) OR (`TrainerId` = 8 AND `SpellId` = 2641) OR (`TrainerId` = 8 AND `SpellId` = 6991) OR (`TrainerId` = 8 AND `SpellId` = 982) OR (`TrainerId` = 204 AND `SpellId` = 1515) OR (`TrainerId` = 204 AND `SpellId` = 883) OR (`TrainerId` = 204 AND `SpellId` = 2641) OR (`TrainerId` = 204 AND `SpellId` = 6991) OR (`TrainerId` = 204 AND `SpellId` = 982) OR (`TrainerId` = 205 AND `SpellId` = 1515) OR (`TrainerId` = 205 AND `SpellId` = 883) OR (`TrainerId` = 205 AND `SpellId` = 2641) OR (`TrainerId` = 205 AND `SpellId` = 6991) OR (`TrainerId` = 205 AND `SpellId` = 982);
INSERT INTO `trainer_spell` (`TrainerId`, `SpellId`, `MoneyCost`, `ReqSkillLine`, `ReqSkillRank`, `ReqAbility1`, `ReqAbility2`, `ReqAbility3`, `ReqLevel`, `VerifiedBuild`) VALUES
(7, 1515, 600, 0, 0, 0, 0, 0, 10, 0),
(7, 883, 600, 0, 0, 0, 0, 0, 10, 0),
(7, 2641, 600, 0, 0, 0, 0, 0, 10, 0),
(7, 6991, 600, 0, 0, 0, 0, 0, 10, 0),
(7, 982, 600, 0, 0, 0, 0, 0, 10, 0),
(8, 1515, 600, 0, 0, 0, 0, 0, 10, 0),
(8, 883, 600, 0, 0, 0, 0, 0, 10, 0),
(8, 2641, 600, 0, 0, 0, 0, 0, 10, 0),
(8, 6991, 600, 0, 0, 0, 0, 0, 10, 0),
(8, 982, 600, 0, 0, 0, 0, 0, 10, 0),
(204, 1515, 600, 0, 0, 0, 0, 0, 10, 0),
(204, 883, 600, 0, 0, 0, 0, 0, 10, 0),
(204, 2641, 600, 0, 0, 0, 0, 0, 10, 0),
(204, 6991, 600, 0, 0, 0, 0, 0, 10, 0),
(204, 982, 600, 0, 0, 0, 0, 0, 10, 0),
(205, 1515, 600, 0, 0, 0, 0, 0, 10, 0),
(205, 883, 600, 0, 0, 0, 0, 0, 10, 0),
(205, 2641, 600, 0, 0, 0, 0, 0, 10, 0),
(205, 6991, 600, 0, 0, 0, 0, 0, 10, 0),
(205, 982, 600, 0, 0, 0, 0, 0, 10, 0);

-- Rogue
DELETE FROM `trainer_spell` WHERE (`TrainerId` = 9 AND `SpellId` = 2842) OR (`TrainerId` = 10 AND `SpellId` = 2842) OR (`TrainerId` = 206 AND `SpellId` = 2842) OR (`TrainerId` = 207 AND `SpellId` = 2842);
INSERT INTO `trainer_spell` (`TrainerId`, `SpellId`, `MoneyCost`, `ReqSkillLine`, `ReqSkillRank`, `ReqAbility1`, `ReqAbility2`, `ReqAbility3`, `ReqLevel`, `VerifiedBuild`) VALUES
(9, 2842, 4000, 0, 0, 0, 0, 0, 20, 0),
(10, 2842, 4000, 0, 0, 0, 0, 0, 20, 0),
(206, 2842, 4000, 0, 0, 0, 0, 0, 20, 0),
(207, 2842, 4000, 0, 0, 0, 0, 0, 20, 0);

-- Shaman
DELETE FROM `trainer_spell` WHERE (`TrainerId` = 14 AND `SpellId` = 8071) OR (`TrainerId` = 14 AND `SpellId` = 3599) OR (`TrainerId` = 14 AND `SpellId` = 5394) OR (`TrainerId` = 15 AND `SpellId` = 8071) OR (`TrainerId` = 15 AND `SpellId` = 3599) OR (`TrainerId` = 15 AND `SpellId` = 5394) OR (`TrainerId` = 210 AND `SpellId` = 8071) OR (`TrainerId` = 210 AND `SpellId` = 3599) OR (`TrainerId` = 210 AND `SpellId` = 5394) OR (`TrainerId` = 211 AND `SpellId` = 8071) OR (`TrainerId` = 211 AND `SpellId` = 3599) OR (`TrainerId` = 211 AND `SpellId` = 5394);
INSERT INTO `trainer_spell` (`TrainerId`, `SpellId`, `MoneyCost`, `ReqSkillLine`, `ReqSkillRank`, `ReqAbility1`, `ReqAbility2`, `ReqAbility3`, `ReqLevel`, `VerifiedBuild`) VALUES
(14, 8071, 100, 0, 0, 0, 0, 0, 4, 0),
(14, 3599, 600, 0, 0, 0, 0, 0, 10, 0),
(14, 5394, 4000, 0, 0, 0, 0, 0, 20, 0),
(15, 8071, 100, 0, 0, 0, 0, 0, 4, 0),
(15, 3599, 600, 0, 0, 0, 0, 0, 10, 0),
(15, 5394, 4000, 0, 0, 0, 0, 0, 20, 0),
(210, 8071, 100, 0, 0, 0, 0, 0, 4, 0),
(210, 3599, 600, 0, 0, 0, 0, 0, 10, 0),
(210, 5394, 4000, 0, 0, 0, 0, 0, 20, 0),
(211, 8071, 100, 0, 0, 0, 0, 0, 4, 0),
(211, 3599, 600, 0, 0, 0, 0, 0, 10, 0),
(211, 5394, 4000, 0, 0, 0, 0, 0, 20, 0);

-- Warlock
DELETE FROM `trainer_spell` WHERE (`TrainerId` = 31 AND `SpellId` = 697) OR (`TrainerId` = 31 AND `SpellId` = 712) OR (`TrainerId` = 31 AND `SpellId` = 691) OR (`TrainerId` = 31 AND `SpellId` = 1122) OR (`TrainerId` = 31 AND `SpellId` = 18540) OR (`TrainerId` = 32 AND `SpellId` = 697) OR (`TrainerId` = 32 AND `SpellId` = 712) OR (`TrainerId` = 32 AND `SpellId` = 691) OR (`TrainerId` = 32 AND `SpellId` = 1122) OR (`TrainerId` = 32 AND `SpellId` = 18540) OR (`TrainerId` = 214 AND `SpellId` = 688) OR (`TrainerId` = 214 AND `SpellId` = 697) OR (`TrainerId` = 214 AND `SpellId` = 712) OR (`TrainerId` = 214 AND `SpellId` = 691) OR (`TrainerId` = 214 AND `SpellId` = 1122) OR (`TrainerId` = 214 AND `SpellId` = 18540) OR (`TrainerId` = 215 AND `SpellId` = 688) OR (`TrainerId` = 215 AND `SpellId` = 697) OR (`TrainerId` = 215 AND `SpellId` = 712) OR (`TrainerId` = 215 AND `SpellId` = 691) OR (`TrainerId` = 215 AND `SpellId` = 1122) OR (`TrainerId` = 215 AND `SpellId` = 18540);
INSERT INTO `trainer_spell` (`TrainerId`, `SpellId`, `MoneyCost`, `ReqSkillLine`, `ReqSkillRank`, `ReqAbility1`, `ReqAbility2`, `ReqAbility3`, `ReqLevel`, `VerifiedBuild`) VALUES
(31, 697, 600, 0, 0, 0, 0, 0, 10, 0),
(31, 712, 4000, 0, 0, 0, 0, 0, 20, 0),
(31, 691, 10000, 0, 0, 0, 0, 0, 30, 0),
(31, 1122, 36000, 0, 0, 0, 0, 0, 50, 0),
(31, 18540, 30000, 0, 0, 0, 0, 0, 60, 0),
(32, 697, 600, 0, 0, 0, 0, 0, 10, 0),
(32, 712, 4000, 0, 0, 0, 0, 0, 20, 0),
(32, 691, 10000, 0, 0, 0, 0, 0, 30, 0),
(32, 1122, 36000, 0, 0, 0, 0, 0, 50, 0),
(32, 18540, 30000, 0, 0, 0, 0, 0, 60, 0),
(214, 688, 10, 0, 0, 0, 0, 0, 1, 0),
(214, 697, 600, 0, 0, 0, 0, 0, 10, 0),
(214, 712, 4000, 0, 0, 0, 0, 0, 20, 0),
(214, 691, 10000, 0, 0, 0, 0, 0, 30, 0),
(214, 1122, 36000, 0, 0, 0, 0, 0, 50, 0),
(214, 18540, 30000, 0, 0, 0, 0, 0, 60, 0),
(215, 688, 10, 0, 0, 0, 0, 0, 1, 0),
(215, 697, 600, 0, 0, 0, 0, 0, 10, 0),
(215, 712, 4000, 0, 0, 0, 0, 0, 20, 0),
(215, 691, 10000, 0, 0, 0, 0, 0, 30, 0),
(215, 1122, 36000, 0, 0, 0, 0, 0, 50, 0),
(215, 18540, 30000, 0, 0, 0, 0, 0, 60, 0);

-- Death Knight
DELETE FROM `trainer_spell` WHERE (`TrainerId` = 13 AND `SpellId` = 53428) OR (`TrainerId` = 13 AND `SpellId` = 48778) OR (`TrainerId` = 13 AND `SpellId` = 33391) OR (`TrainerId` = 13 AND `SpellId` = 50977);
INSERT INTO `trainer_spell` (`TrainerId`, `SpellId`, `MoneyCost`, `ReqSkillLine`, `ReqSkillRank`, `ReqAbility1`, `ReqAbility2`, `ReqAbility3`, `ReqLevel`, `VerifiedBuild`) VALUES
(13, 53428, 50000, 0, 0, 0, 0, 0, 55, 0),
(13, 48778, 50000, 0, 0, 0, 0, 0, 55, 0),
(13, 33391, 50000, 0, 0, 0, 0, 0, 55, 0),
(13, 50977, 50000, 0, 0, 0, 0, 0, 55, 0);

-- Druid
DELETE FROM `trainer_spell` WHERE (`TrainerId` = 33 AND `SpellId` = 5487) OR (`TrainerId` = 33 AND `SpellId` = 6795) OR (`TrainerId` = 33 AND `SpellId` = 6807) OR (`TrainerId` = 33 AND `SpellId` = 8946) OR (`TrainerId` = 33 AND `SpellId` = 40120) OR (`TrainerId` = 34 AND `SpellId` = 5487) OR (`TrainerId` = 34 AND `SpellId` = 6795) OR (`TrainerId` = 34 AND `SpellId` = 6807) OR (`TrainerId` = 34 AND `SpellId` = 8946) OR (`TrainerId` = 34 AND `SpellId` = 1066) OR (`TrainerId` = 34 AND `SpellId` = 40120) OR (`TrainerId` = 216 AND `SpellId` = 5487) OR (`TrainerId` = 216 AND `SpellId` = 6795) OR (`TrainerId` = 216 AND `SpellId` = 6807) OR (`TrainerId` = 216 AND `SpellId` = 8946) OR (`TrainerId` = 216 AND `SpellId` = 1066) OR (`TrainerId` = 216 AND `SpellId` = 40120) OR (`TrainerId` = 217 AND `SpellId` = 5487) OR (`TrainerId` = 217 AND `SpellId` = 6795) OR (`TrainerId` = 217 AND `SpellId` = 6807) OR (`TrainerId` = 217 AND `SpellId` = 8946) OR (`TrainerId` = 217 AND `SpellId` = 1066) OR (`TrainerId` = 217 AND `SpellId` = 40120);
INSERT INTO `trainer_spell` (`TrainerId`, `SpellId`, `MoneyCost`, `ReqSkillLine`, `ReqSkillRank`, `ReqAbility1`, `ReqAbility2`, `ReqAbility3`, `ReqLevel`, `VerifiedBuild`) VALUES
(33, 5487, 600, 0, 0, 0, 0, 0, 10, 0),
(33, 6795, 600, 0, 0, 0, 0, 0, 10, 0),
(33, 6807, 600, 0, 0, 0, 0, 0, 10, 0),
(33, 8946, 1500, 0, 0, 0, 0, 0, 14, 0),
(33, 40120, 400000, 0, 0, 0, 0, 0, 70, 0),
(34, 5487, 600, 0, 0, 0, 0, 0, 10, 0),
(34, 6795, 600, 0, 0, 0, 0, 0, 10, 0),
(34, 6807, 600, 0, 0, 0, 0, 0, 10, 0),
(34, 8946, 1500, 0, 0, 0, 0, 0, 14, 0),
(34, 1066, 2000, 0, 0, 0, 0, 0, 16, 0),
(34, 40120, 400000, 0, 0, 0, 0, 0, 70, 0),
(216, 5487, 600, 0, 0, 0, 0, 0, 10, 0),
(216, 6795, 600, 0, 0, 0, 0, 0, 10, 0),
(216, 6807, 600, 0, 0, 0, 0, 0, 10, 0),
(216, 8946, 1500, 0, 0, 0, 0, 0, 14, 0),
(216, 1066, 2000, 0, 0, 0, 0, 0, 16, 0),
(216, 40120, 400000, 0, 0, 0, 0, 0, 70, 0),
(217, 5487, 600, 0, 0, 0, 0, 0, 10, 0),
(217, 6795, 600, 0, 0, 0, 0, 0, 10, 0),
(217, 6807, 600, 0, 0, 0, 0, 0, 10, 0),
(217, 8946, 1500, 0, 0, 0, 0, 0, 14, 0),
(217, 1066, 2000, 0, 0, 0, 0, 0, 16, 0),
(217, 40120, 400000, 0, 0, 0, 0, 0, 70, 0);
