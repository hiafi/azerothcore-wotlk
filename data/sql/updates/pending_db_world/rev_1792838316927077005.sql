-- death-knight-rework: Death Knight trainers are human (Alliance, 33251) / orc (Horde, 300340) instead of goblins.
-- The creature_template rows and models (33251 -> display 25998, 300340 -> display 25999) come from the generated rev.
-- Literal values only (trainer_state skips files with @ variables).
DELETE FROM `creature_default_trainer` WHERE `CreatureId` = 300340;
INSERT INTO `creature_default_trainer` (`CreatureId`, `TrainerId`) VALUES
(300340, 13);

-- Horde spawns: Orgrimmar, Valley of Trials, Deathknell, Camp Narache, Sunstrider Isle, Undercity.
UPDATE `creature` SET `id` = 300340 WHERE `id` = 33251 AND `guid` IN (5300680, 5300710, 5300713, 5300714, 5300715, 5300720);
