-- Dual Spec: reduce cost from 1000g (10000000 copper) to 10g (100000 copper).
-- OptionType 18 = GOSSIP_OPTION_LEARNDUALSPEC, the only feature that uses BoxMoney this way.
UPDATE `gossip_menu_option` SET `BoxMoney` = 100000 WHERE `OptionType` = 18 AND `BoxMoney` = 10000000;

-- Riding: Apprentice Riding (33388) down from 90g/level 40 to 1g/level 20.
-- Journeyman Riding (33391) down from 900g/level 60 to 100g/level 40.
-- Scoped to the generic riding trainers (TrainerId 35-46); leaves the Death Knight starter
-- trainer's bundled Journeyman Riding row (TrainerId 13) alone, it's a different context.
UPDATE `trainer_spell` SET `MoneyCost` = 10000, `ReqLevel` = 20
    WHERE `SpellId` = 33388 AND `TrainerId` BETWEEN 35 AND 46 AND `MoneyCost` = 900000 AND `ReqLevel` = 40;
UPDATE `trainer_spell` SET `MoneyCost` = 1000000, `ReqLevel` = 40
    WHERE `SpellId` = 33391 AND `TrainerId` BETWEEN 35 AND 46 AND `MoneyCost` = 9000000 AND `ReqLevel` = 60;
