-- DB update 2026_09_05_38 -> 2026_09_10_00
-- Death Gate (50977) down from level 20 to 10, matching the first runeforge access on the same
-- trainer (TrainerId 13): Runeforging (53428) and Rune of Razorice (53343) both unlock at 10. No
-- reason to gate the trip to Ebon Hold later than the ability to actually use a runeforge once
-- there -- see docs/bugs-and-fixes.md's Death Knight trainer entry.
UPDATE `trainer_spell` SET `ReqLevel` = 10 WHERE `TrainerId` = 13 AND `SpellId` = 50977 AND `ReqLevel` = 20;
