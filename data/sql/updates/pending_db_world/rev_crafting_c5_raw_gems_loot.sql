-- Crafting rework C5 follow-up (user 2026-11-11): where the new raw gems drop.
-- - Ruby (70826), the red leveling raw: Iron, Gold, Mithril and Truesilver veins (5%, gem group 1, beside Citrine and
--   Aquamarine) and Iron/Mithril Ore prospecting. It takes Star Ruby's place in the Mithril/Truesilver veins and the
--   Iron/Mithril prospecting rows, so Star Ruby (7910) drops only from Thorium veins, Thorium Ore prospecting and its
--   stock world drops.
-- - Dusk Amethyst (70827), the purple rare raw (replacing Arcane Crystal as the purple cut's reagent): Thorium vein
--   reference 12900 at 12% (Arcane Crystal 40 -> 28) and Thorium Ore prospecting at 15% (Star Ruby 30 -> 15).
-- Old values, to revert: gameobject_loot_template 1742, 5045, 13961 and 17938 had (7910, chance 5, group 1, 1-1);
-- 1505, 1506 and 17939 had no Ruby; prospecting 2772 had (7910, 5, group 1, 1-1), 3858 (7910, 30, group 1, 1-2),
-- 10620 Star Ruby 30 and no Dusk Amethyst; reference 12900 Arcane Crystal 40 and no Dusk Amethyst.

-- Veins: Iron Deposit 1505, Gold Vein 1506, Mithril Deposit 1742, Truesilver Deposit 5045, and the Felwood copies
-- Mithril Deposit 13961, Truesilver Deposit 17938, Gold Vein 17939. Treasure chests keep their stock gems.
DELETE FROM `gameobject_loot_template` WHERE `Entry` IN (1505, 1506, 1742, 5045) AND `Item` IN (7910, 70826);
DELETE FROM `gameobject_loot_template` WHERE `Entry` IN (13961, 17938, 17939) AND `Item` IN (7910, 70826);
INSERT INTO `gameobject_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`, `GroupId`,
    `MinCount`, `MaxCount`, `Comment`) VALUES
(1505, 70826, 0, 5, 0, 1, 1, 1, 1, 'Iron Deposit - Ruby'),
(1506, 70826, 0, 5, 0, 1, 1, 1, 1, 'Gold Vein - Ruby'),
(1742, 70826, 0, 5, 0, 1, 1, 1, 1, 'Mithril Deposit - Ruby'),
(5045, 70826, 0, 5, 0, 1, 1, 1, 1, 'Truesilver Deposit - Ruby'),
(13961, 70826, 0, 5, 0, 1, 1, 1, 1, 'Mithril Deposit - Ruby'),
(17938, 70826, 0, 5, 0, 1, 1, 1, 1, 'Truesilver Deposit - Ruby'),
(17939, 70826, 0, 5, 0, 1, 1, 1, 1, 'Gold Vein - Ruby');

-- Prospecting: Iron Ore 2772 and Mithril Ore 3858 give Ruby instead of Star Ruby; Thorium Ore 10620 splits Star Ruby's
-- 30% with Dusk Amethyst.
DELETE FROM `prospecting_loot_template` WHERE `Entry` = 10620 AND `Item` IN (7910, 70827);
DELETE FROM `prospecting_loot_template` WHERE `Entry` IN (2772, 3858) AND `Item` IN (7910, 70826);
INSERT INTO `prospecting_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`, `GroupId`,
    `MinCount`, `MaxCount`, `Comment`) VALUES
(2772, 70826, 0, 5, 0, 1, 1, 1, 1, 'Ruby'),
(3858, 70826, 0, 30, 0, 1, 1, 1, 2, 'Ruby'),
(10620, 7910, 0, 15, 0, 1, 1, 1, 2, 'Star Ruby'),
(10620, 70827, 0, 15, 0, 1, 1, 1, 2, 'Dusk Amethyst');

-- Thorium vein gem reference 12900 (one gem from a 100% group): Dusk Amethyst 12, Arcane Crystal 28.
DELETE FROM `reference_loot_template` WHERE `Entry` = 12900 AND `Item` IN (12363, 70827);
INSERT INTO `reference_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`, `GroupId`,
    `MinCount`, `MaxCount`, `Comment`) VALUES
(12900, 12363, 0, 28, 0, 1, 1, 1, 1, 'Arcane Crystal'),
(12900, 70827, 0, 12, 0, 1, 1, 1, 1, 'Dusk Amethyst');
