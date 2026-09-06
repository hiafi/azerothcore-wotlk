-- Death Knight trainer (TrainerId 13) level curve: spread its abilities across 1-60 instead of
-- 55-80, for a DK that starts at level 1 (see docs/bugs-and-fixes.md and the Stormwind/Orgrimmar
-- trainer spawns added in rev_1788687658359759602.sql).
--
-- Only the base/first rank of each ability moves. Existing higher-rank rows (chained via
-- ReqAbility1, e.g. Plague Strike rank 2 at 49917) are untouched -- they still require their
-- prerequisite rank plus their own ReqLevel, same as before.
--
-- Five abilities aren't touched here despite being on the level list (Blood Strike, Plague Strike,
-- Icy Touch, Death Coil, Death Grip's *replacement* isn't needed -- see below): they're granted
-- automatically via SkillLineAbility.dbc (AcquireMethod = "learned with skill line"), not through
-- this trainer at all. This migration adds them here anyway as real trainer_spell rows so
-- TrainerId 13 is the single source of truth for the whole curve; the pre-existing free grant via
-- the skill line is a separate, harder lever (would need a new PlayerScript::OnPlayerLevelChanged
-- hook plus new dbc-tools support) intentionally left alone for now.

-- Existing rows: retune ReqLevel only (MoneyCost/ReqAbility1 left as-is -- a separate pass, since
-- the old costs were priced for a 55-80 curve and are now too expensive for their new level).
UPDATE `trainer_spell` SET `ReqLevel` = 40 WHERE `TrainerId` = 13 AND `SpellId` = 3714 AND `ReqLevel` = 61;      -- Path of Frost
UPDATE `trainer_spell` SET `ReqLevel` = 60 WHERE `TrainerId` = 13 AND `SpellId` = 42650 AND `ReqLevel` = 80;     -- Army of the Dead
UPDATE `trainer_spell` SET `ReqLevel` = 30 WHERE `TrainerId` = 13 AND `SpellId` = 43265 AND `ReqLevel` = 60;     -- Death and Decay
UPDATE `trainer_spell` SET `ReqLevel` = 22 WHERE `TrainerId` = 13 AND `SpellId` = 45524 AND `ReqLevel` = 58;     -- Chains of Ice
UPDATE `trainer_spell` SET `ReqLevel` = 26 WHERE `TrainerId` = 13 AND `SpellId` = 45529 AND `ReqLevel` = 64;     -- Blood Tap
UPDATE `trainer_spell` SET `ReqLevel` = 12 WHERE `TrainerId` = 13 AND `SpellId` = 46584 AND `ReqLevel` = 56;     -- Raise Dead
UPDATE `trainer_spell` SET `ReqLevel` = 28 WHERE `TrainerId` = 13 AND `SpellId` = 47476 AND `ReqLevel` = 59;     -- Strangulate
UPDATE `trainer_spell` SET `ReqLevel` = 18 WHERE `TrainerId` = 13 AND `SpellId` = 47528 AND `ReqLevel` = 57;     -- Mind Freeze
UPDATE `trainer_spell` SET `ReqLevel` = 54 WHERE `TrainerId` = 13 AND `SpellId` = 47568 AND `ReqLevel` = 75;     -- Empower Rune Weapon
UPDATE `trainer_spell` SET `ReqLevel` = 10 WHERE `TrainerId` = 13 AND `SpellId` = 48263 AND `ReqLevel` = 57;     -- Frost Presence
UPDATE `trainer_spell` SET `ReqLevel` = 40 WHERE `TrainerId` = 13 AND `SpellId` = 48265 AND `ReqLevel` = 70;     -- Unholy Presence
UPDATE `trainer_spell` SET `ReqLevel` = 46 WHERE `TrainerId` = 13 AND `SpellId` = 48707 AND `ReqLevel` = 68;     -- Anti-Magic Shell
UPDATE `trainer_spell` SET `ReqLevel` = 24 WHERE `TrainerId` = 13 AND `SpellId` = 48721 AND `ReqLevel` = 58;     -- Blood Boil
UPDATE `trainer_spell` SET `ReqLevel` = 38 WHERE `TrainerId` = 13 AND `SpellId` = 48743 AND `ReqLevel` = 66;     -- Death Pact
UPDATE `trainer_spell` SET `ReqLevel` = 40 WHERE `TrainerId` = 13 AND `SpellId` = 48792 AND `ReqLevel` = 62;     -- Icebound Fortitude
UPDATE `trainer_spell` SET `ReqLevel` = 36 WHERE `TrainerId` = 13 AND `SpellId` = 49020 AND `ReqLevel` = 61;     -- Obliterate
UPDATE `trainer_spell` SET `ReqLevel` = 10 WHERE `TrainerId` = 13 AND `SpellId` = 49998 AND `ReqLevel` = 56;     -- Death Strike
UPDATE `trainer_spell` SET `ReqLevel` = 20 WHERE `TrainerId` = 13 AND `SpellId` = 50842 AND `ReqLevel` = 56;     -- Pestilence
UPDATE `trainer_spell` SET `ReqLevel` = 50 WHERE `TrainerId` = 13 AND `SpellId` = 53323 AND `ReqLevel` = 63;     -- Rune of Swordshattering
UPDATE `trainer_spell` SET `ReqLevel` = 32 WHERE `TrainerId` = 13 AND `SpellId` = 53331 AND `ReqLevel` = 60;     -- Rune of Lichbane
UPDATE `trainer_spell` SET `ReqLevel` = 14 WHERE `TrainerId` = 13 AND `SpellId` = 53341 AND `ReqLevel` = 55;     -- Rune of Cinderglacier
UPDATE `trainer_spell` SET `ReqLevel` = 34 WHERE `TrainerId` = 13 AND `SpellId` = 53342 AND `ReqLevel` = 57;     -- Rune of Spellshattering
UPDATE `trainer_spell` SET `ReqLevel` = 10 WHERE `TrainerId` = 13 AND `SpellId` = 53343 AND `ReqLevel` = 55;     -- Rune of Razorice
UPDATE `trainer_spell` SET `ReqLevel` = 60 WHERE `TrainerId` = 13 AND `SpellId` = 53344 AND `ReqLevel` = 70;     -- Rune of the Fallen Crusader
UPDATE `trainer_spell` SET `ReqLevel` = 50 WHERE `TrainerId` = 13 AND `SpellId` = 54446 AND `ReqLevel` = 63;     -- Rune of Swordbreaking
UPDATE `trainer_spell` SET `ReqLevel` = 40 WHERE `TrainerId` = 13 AND `SpellId` = 54447 AND `ReqLevel` = 57;     -- Rune of Spellbreaking
UPDATE `trainer_spell` SET `ReqLevel` = 10 WHERE `TrainerId` = 13 AND `SpellId` = 56222 AND `ReqLevel` = 65;     -- Dark Command
UPDATE `trainer_spell` SET `ReqLevel` = 14 WHERE `TrainerId` = 13 AND `SpellId` = 56815 AND `ReqLevel` = 67;     -- Rune Strike
UPDATE `trainer_spell` SET `ReqLevel` = 8  WHERE `TrainerId` = 13 AND `SpellId` = 57330 AND `ReqLevel` = 65;     -- Horn of Winter
UPDATE `trainer_spell` SET `ReqLevel` = 50 WHERE `TrainerId` = 13 AND `SpellId` = 61999 AND `ReqLevel` = 72;     -- Raise Ally

-- New rows: abilities TrainerId 13 doesn't teach at all today. MoneyCost is a placeholder
-- (ReqLevel * 100 copper, matching the cheapest existing non-chained rows) -- retune separately.
DELETE FROM `trainer_spell` WHERE `TrainerId` = 13 AND `SpellId` IN (48266, 45462, 45902, 45477, 47541, 53428, 49576, 50977);
INSERT INTO `trainer_spell` (`TrainerId`, `SpellId`, `MoneyCost`, `ReqSkillLine`, `ReqSkillRank`, `ReqAbility1`, `ReqAbility2`, `ReqAbility3`, `ReqLevel`) VALUES
(13, 48266, 100, 0, 0, 0, 0, 0, 1),    -- Blood Presence
(13, 45462, 100, 0, 0, 0, 0, 0, 1),    -- Plague Strike
(13, 45902, 100, 0, 0, 0, 0, 0, 1),    -- Blood Strike
(13, 45477, 200, 0, 0, 0, 0, 0, 2),    -- Icy Touch
(13, 47541, 400, 0, 0, 0, 0, 0, 4),    -- Death Coil
(13, 53428, 1000, 0, 0, 0, 0, 0, 10),  -- Runeforging
(13, 49576, 1600, 0, 0, 0, 0, 0, 16),  -- Death Grip
(13, 50977, 2000, 0, 0, 0, 0, 0, 20);  -- Death Gate
