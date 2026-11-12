-- Crafting rework C6, material squish (user 2026-11-11; .agents/plans/crafting-rework/crafting-rework.C6-RESEARCH.md
-- sections 5 and 6, decisions 13a-13f). Vanilla only: Outland and Northrend entries stay stock until their gates open.
--
-- Disenchanting: one dust, one lesser and one greater essence for the whole of vanilla (the level-60 survivors
-- Illusion Dust 16204, Lesser Eternal Essence 16202, Greater Eternal Essence 16203). Greens by item level band:
-- 1-30 (entries 1-4 / 21-24) 1 dust or 1 lesser essence; 31-50 (5-8 / 25-28) 1-3 dust, 1-2 lesser or 1 greater;
-- 51+ (9-11 / 29-31) 2-4 dust, 1-4 lesser or 1-2 greater. Armor (1-11) leans to dust, weapons (21-31) to essence, as
-- stock. Blues: Small Brilliant Shard 14343 to item level 50 (41-46), Large Brilliant Shard 14344 from 51 (47-49,
-- 18). Epics: Nexus Crystal 20725, 1 up to item level 80 (61-65, and 17, whose only user is an epic), 1-2 above
-- (new entry 70; stock epics above 80 move to it below, minted items get it from apps/dbc-tools/lib/disenchant.py).
-- One group per entry: exactly one result.
-- Old rows: the base dump data/sql/base/db_world/disenchant_loot_template.sql (re-run those entries to revert).
DELETE FROM `disenchant_loot_template` WHERE `Entry` IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 17, 18, 21);
DELETE FROM `disenchant_loot_template` WHERE `Entry` IN (22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 41, 42, 43, 44);
DELETE FROM `disenchant_loot_template` WHERE `Entry` IN (45, 46, 47, 48, 49, 61, 62, 63, 64, 65, 70);
INSERT INTO `disenchant_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`,
    `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES
(1, 16204, 0, 75, 0, 1, 1, 1, 1, 'Illusion Dust'),
(1, 16202, 0, 25, 0, 1, 1, 1, 1, 'Lesser Eternal Essence'),
(2, 16204, 0, 75, 0, 1, 1, 1, 1, 'Illusion Dust'),
(2, 16202, 0, 25, 0, 1, 1, 1, 1, 'Lesser Eternal Essence'),
(3, 16204, 0, 75, 0, 1, 1, 1, 1, 'Illusion Dust'),
(3, 16202, 0, 25, 0, 1, 1, 1, 1, 'Lesser Eternal Essence'),
(4, 16204, 0, 75, 0, 1, 1, 1, 1, 'Illusion Dust'),
(4, 16202, 0, 25, 0, 1, 1, 1, 1, 'Lesser Eternal Essence'),
(5, 16204, 0, 75, 0, 1, 1, 1, 3, 'Illusion Dust'),
(5, 16202, 0, 20, 0, 1, 1, 1, 2, 'Lesser Eternal Essence'),
(5, 16203, 0, 5, 0, 1, 1, 1, 1, 'Greater Eternal Essence'),
(6, 16204, 0, 75, 0, 1, 1, 1, 3, 'Illusion Dust'),
(6, 16202, 0, 20, 0, 1, 1, 1, 2, 'Lesser Eternal Essence'),
(6, 16203, 0, 5, 0, 1, 1, 1, 1, 'Greater Eternal Essence'),
(7, 16204, 0, 75, 0, 1, 1, 1, 3, 'Illusion Dust'),
(7, 16202, 0, 20, 0, 1, 1, 1, 2, 'Lesser Eternal Essence'),
(7, 16203, 0, 5, 0, 1, 1, 1, 1, 'Greater Eternal Essence'),
(8, 16204, 0, 75, 0, 1, 1, 1, 3, 'Illusion Dust'),
(8, 16202, 0, 20, 0, 1, 1, 1, 2, 'Lesser Eternal Essence'),
(8, 16203, 0, 5, 0, 1, 1, 1, 1, 'Greater Eternal Essence'),
(9, 16204, 0, 75, 0, 1, 1, 2, 4, 'Illusion Dust'),
(9, 16202, 0, 15, 0, 1, 1, 1, 4, 'Lesser Eternal Essence'),
(9, 16203, 0, 10, 0, 1, 1, 1, 2, 'Greater Eternal Essence'),
(10, 16204, 0, 75, 0, 1, 1, 2, 4, 'Illusion Dust'),
(10, 16202, 0, 15, 0, 1, 1, 1, 4, 'Lesser Eternal Essence'),
(10, 16203, 0, 10, 0, 1, 1, 1, 2, 'Greater Eternal Essence'),
(11, 16204, 0, 75, 0, 1, 1, 2, 4, 'Illusion Dust'),
(11, 16202, 0, 15, 0, 1, 1, 1, 4, 'Lesser Eternal Essence'),
(11, 16203, 0, 10, 0, 1, 1, 1, 2, 'Greater Eternal Essence'),
(17, 20725, 0, 100, 0, 1, 1, 1, 1, 'Nexus Crystal'),
(18, 14344, 0, 100, 0, 1, 1, 1, 1, 'Large Brilliant Shard'),
(21, 16202, 0, 75, 0, 1, 1, 1, 1, 'Lesser Eternal Essence'),
(21, 16204, 0, 25, 0, 1, 1, 1, 1, 'Illusion Dust'),
(22, 16202, 0, 75, 0, 1, 1, 1, 1, 'Lesser Eternal Essence'),
(22, 16204, 0, 25, 0, 1, 1, 1, 1, 'Illusion Dust'),
(23, 16202, 0, 75, 0, 1, 1, 1, 1, 'Lesser Eternal Essence'),
(23, 16204, 0, 25, 0, 1, 1, 1, 1, 'Illusion Dust'),
(24, 16202, 0, 75, 0, 1, 1, 1, 1, 'Lesser Eternal Essence'),
(24, 16204, 0, 25, 0, 1, 1, 1, 1, 'Illusion Dust'),
(25, 16202, 0, 55, 0, 1, 1, 1, 2, 'Lesser Eternal Essence'),
(25, 16203, 0, 20, 0, 1, 1, 1, 1, 'Greater Eternal Essence'),
(25, 16204, 0, 25, 0, 1, 1, 1, 3, 'Illusion Dust'),
(26, 16202, 0, 55, 0, 1, 1, 1, 2, 'Lesser Eternal Essence'),
(26, 16203, 0, 20, 0, 1, 1, 1, 1, 'Greater Eternal Essence'),
(26, 16204, 0, 25, 0, 1, 1, 1, 3, 'Illusion Dust'),
(27, 16202, 0, 55, 0, 1, 1, 1, 2, 'Lesser Eternal Essence'),
(27, 16203, 0, 20, 0, 1, 1, 1, 1, 'Greater Eternal Essence'),
(27, 16204, 0, 25, 0, 1, 1, 1, 3, 'Illusion Dust'),
(28, 16202, 0, 55, 0, 1, 1, 1, 2, 'Lesser Eternal Essence'),
(28, 16203, 0, 20, 0, 1, 1, 1, 1, 'Greater Eternal Essence'),
(28, 16204, 0, 25, 0, 1, 1, 1, 3, 'Illusion Dust'),
(29, 16202, 0, 40, 0, 1, 1, 1, 4, 'Lesser Eternal Essence'),
(29, 16203, 0, 35, 0, 1, 1, 1, 2, 'Greater Eternal Essence'),
(29, 16204, 0, 25, 0, 1, 1, 2, 4, 'Illusion Dust'),
(30, 16202, 0, 40, 0, 1, 1, 1, 4, 'Lesser Eternal Essence'),
(30, 16203, 0, 35, 0, 1, 1, 1, 2, 'Greater Eternal Essence'),
(30, 16204, 0, 25, 0, 1, 1, 2, 4, 'Illusion Dust'),
(31, 16202, 0, 40, 0, 1, 1, 1, 4, 'Lesser Eternal Essence'),
(31, 16203, 0, 35, 0, 1, 1, 1, 2, 'Greater Eternal Essence'),
(31, 16204, 0, 25, 0, 1, 1, 2, 4, 'Illusion Dust'),
(41, 14343, 0, 100, 0, 1, 1, 1, 1, 'Small Brilliant Shard'),
(42, 14343, 0, 100, 0, 1, 1, 1, 1, 'Small Brilliant Shard'),
(43, 14343, 0, 100, 0, 1, 1, 1, 1, 'Small Brilliant Shard'),
(44, 14343, 0, 100, 0, 1, 1, 1, 1, 'Small Brilliant Shard'),
(45, 14343, 0, 100, 0, 1, 1, 1, 1, 'Small Brilliant Shard'),
(46, 14343, 0, 100, 0, 1, 1, 1, 1, 'Small Brilliant Shard'),
(47, 14344, 0, 100, 0, 1, 1, 1, 1, 'Large Brilliant Shard'),
(48, 14344, 0, 100, 0, 1, 1, 1, 1, 'Large Brilliant Shard'),
(49, 14344, 0, 100, 0, 1, 1, 1, 1, 'Large Brilliant Shard'),
(61, 20725, 0, 100, 0, 1, 1, 1, 1, 'Nexus Crystal'),
(62, 20725, 0, 100, 0, 1, 1, 1, 1, 'Nexus Crystal'),
(63, 20725, 0, 100, 0, 1, 1, 1, 1, 'Nexus Crystal'),
(64, 20725, 0, 100, 0, 1, 1, 1, 1, 'Nexus Crystal'),
(65, 20725, 0, 100, 0, 1, 1, 1, 1, 'Nexus Crystal'),
(70, 20725, 0, 100, 0, 1, 1, 1, 2, 'Nexus Crystal');

-- Stock epics above item level 80 (AQ40 and the T3 tier) disenchant into 1-2 Nexus Crystals (entry 70). Revert:
-- DisenchantID back to 65 for these rows.
UPDATE `item_template` SET `DisenchantID` = 70 WHERE `Quality` = 4 AND `DisenchantID` = 65 AND `ItemLevel` > 80;

-- Milling: pigments by the herb's color, not its level (user 2026-11-11, decision 13d B). Every vanilla herb mills into
-- 2-4 of its color's pigment, plus a 10% chance at the single rare pigment, Indigo Pigment 43105. Red Ruby
-- Pigment 43106, yellow Golden Pigment 39338, blue Sapphire Pigment 43107, green Emerald Pigment 39339; the inks are
-- Fiery Ink, Lion's Ink, Ink of the Sky, Jadefire Ink and the rare Royal Ink (recipes in
-- apps/dbc-tools/source/world/crafting_squish.py). Old rows: one reference row per herb (base dump
-- milling_loot_template.sql); the stock reference_loot_template rows are left in place.
DELETE FROM `milling_loot_template` WHERE `Entry` IN (765, 785, 2447, 2449, 2450, 2452, 2453, 3355, 3356, 3357);
DELETE FROM `milling_loot_template` WHERE `Entry` IN (3358, 3369, 3818, 3819, 3820, 3821, 4625, 8831, 8836, 8838);
DELETE FROM `milling_loot_template` WHERE `Entry` IN (8839, 8845, 8846, 13463, 13464, 13465, 13466, 13467);
INSERT INTO `milling_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`,
    `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES
(2450, 43106, 0, 100, 0, 1, 0, 2, 4, 'Briarthorn - Ruby Pigment'),
(2450, 43105, 0, 10, 0, 1, 0, 1, 1, 'Briarthorn - Indigo Pigment'),
(2453, 43106, 0, 100, 0, 1, 0, 2, 4, 'Bruiseweed - Ruby Pigment'),
(2453, 43105, 0, 10, 0, 1, 0, 1, 1, 'Bruiseweed - Indigo Pigment'),
(3356, 43106, 0, 100, 0, 1, 0, 2, 4, 'Kingsblood - Ruby Pigment'),
(3356, 43105, 0, 10, 0, 1, 0, 1, 1, 'Kingsblood - Indigo Pigment'),
(4625, 43106, 0, 100, 0, 1, 0, 2, 4, 'Firebloom - Ruby Pigment'),
(4625, 43105, 0, 10, 0, 1, 0, 1, 1, 'Firebloom - Indigo Pigment'),
(8846, 43106, 0, 100, 0, 1, 0, 2, 4, 'Gromsblood - Ruby Pigment'),
(8846, 43105, 0, 10, 0, 1, 0, 1, 1, 'Gromsblood - Indigo Pigment'),
(765, 39338, 0, 100, 0, 1, 0, 2, 4, 'Silverleaf - Golden Pigment'),
(765, 43105, 0, 10, 0, 1, 0, 1, 1, 'Silverleaf - Indigo Pigment'),
(2449, 39338, 0, 100, 0, 1, 0, 2, 4, 'Earthroot - Golden Pigment'),
(2449, 43105, 0, 10, 0, 1, 0, 1, 1, 'Earthroot - Indigo Pigment'),
(3355, 39338, 0, 100, 0, 1, 0, 2, 4, 'Wild Steelbloom - Golden Pigment'),
(3355, 43105, 0, 10, 0, 1, 0, 1, 1, 'Wild Steelbloom - Indigo Pigment'),
(3821, 39338, 0, 100, 0, 1, 0, 2, 4, 'Goldthorn - Golden Pigment'),
(3821, 43105, 0, 10, 0, 1, 0, 1, 1, 'Goldthorn - Indigo Pigment'),
(8838, 39338, 0, 100, 0, 1, 0, 2, 4, 'Sungrass - Golden Pigment'),
(8838, 43105, 0, 10, 0, 1, 0, 1, 1, 'Sungrass - Indigo Pigment'),
(13464, 39338, 0, 100, 0, 1, 0, 2, 4, 'Golden Sansam - Golden Pigment'),
(13464, 43105, 0, 10, 0, 1, 0, 1, 1, 'Golden Sansam - Indigo Pigment'),
(785, 43107, 0, 100, 0, 1, 0, 2, 4, 'Mageroyal - Sapphire Pigment'),
(785, 43105, 0, 10, 0, 1, 0, 1, 1, 'Mageroyal - Indigo Pigment'),
(3820, 43107, 0, 100, 0, 1, 0, 2, 4, 'Stranglekelp - Sapphire Pigment'),
(3820, 43105, 0, 10, 0, 1, 0, 1, 1, 'Stranglekelp - Indigo Pigment'),
(3818, 43107, 0, 100, 0, 1, 0, 2, 4, 'Fadeleaf - Sapphire Pigment'),
(3818, 43105, 0, 10, 0, 1, 0, 1, 1, 'Fadeleaf - Indigo Pigment'),
(3819, 43107, 0, 100, 0, 1, 0, 2, 4, 'Wintersbite - Sapphire Pigment'),
(3819, 43105, 0, 10, 0, 1, 0, 1, 1, 'Wintersbite - Indigo Pigment'),
(8831, 43107, 0, 100, 0, 1, 0, 2, 4, 'Purple Lotus - Sapphire Pigment'),
(8831, 43105, 0, 10, 0, 1, 0, 1, 1, 'Purple Lotus - Indigo Pigment'),
(8836, 43107, 0, 100, 0, 1, 0, 2, 4, 'Arthas'' Tears - Sapphire Pigment'),
(8836, 43105, 0, 10, 0, 1, 0, 1, 1, 'Arthas'' Tears - Indigo Pigment'),
(8845, 43107, 0, 100, 0, 1, 0, 2, 4, 'Ghost Mushroom - Sapphire Pigment'),
(8845, 43105, 0, 10, 0, 1, 0, 1, 1, 'Ghost Mushroom - Indigo Pigment'),
(13465, 43107, 0, 100, 0, 1, 0, 2, 4, 'Mountain Silversage - Sapphire Pigment'),
(13465, 43105, 0, 10, 0, 1, 0, 1, 1, 'Mountain Silversage - Indigo Pigment'),
(13467, 43107, 0, 100, 0, 1, 0, 2, 4, 'Icecap - Sapphire Pigment'),
(13467, 43105, 0, 10, 0, 1, 0, 1, 1, 'Icecap - Indigo Pigment'),
(2447, 39339, 0, 100, 0, 1, 0, 2, 4, 'Peacebloom - Emerald Pigment'),
(2447, 43105, 0, 10, 0, 1, 0, 1, 1, 'Peacebloom - Indigo Pigment'),
(2452, 39339, 0, 100, 0, 1, 0, 2, 4, 'Swiftthistle - Emerald Pigment'),
(2452, 43105, 0, 10, 0, 1, 0, 1, 1, 'Swiftthistle - Indigo Pigment'),
(3369, 39339, 0, 100, 0, 1, 0, 2, 4, 'Grave Moss - Emerald Pigment'),
(3369, 43105, 0, 10, 0, 1, 0, 1, 1, 'Grave Moss - Indigo Pigment'),
(3357, 39339, 0, 100, 0, 1, 0, 2, 4, 'Liferoot - Emerald Pigment'),
(3357, 43105, 0, 10, 0, 1, 0, 1, 1, 'Liferoot - Indigo Pigment'),
(3358, 39339, 0, 100, 0, 1, 0, 2, 4, 'Khadgar''s Whisker - Emerald Pigment'),
(3358, 43105, 0, 10, 0, 1, 0, 1, 1, 'Khadgar''s Whisker - Indigo Pigment'),
(8839, 39339, 0, 100, 0, 1, 0, 2, 4, 'Blindweed - Emerald Pigment'),
(8839, 43105, 0, 10, 0, 1, 0, 1, 1, 'Blindweed - Indigo Pigment'),
(13463, 39339, 0, 100, 0, 1, 0, 2, 4, 'Dreamfoil - Emerald Pigment'),
(13463, 43105, 0, 10, 0, 1, 0, 1, 1, 'Dreamfoil - Indigo Pigment'),
(13466, 39339, 0, 100, 0, 1, 0, 2, 4, 'Plaguebloom - Emerald Pigment'),
(13466, 43105, 0, 10, 0, 1, 0, 1, 1, 'Plaguebloom - Indigo Pigment');

-- Quests that ask for a squished-out material take its survivor (review 2026-11-11): Salve via Disenchanting (4107,
-- 4112, 5886, 5891; was Lesser Nether Essence 11174) takes Lesser Eternal Essence 16202; Scrying Materials (8779,
-- 8807; was Large Radiant Shard 11178) takes Small Brilliant Shard 14343, the survivor of every Glimmering, Glowing
-- and Radiant shard. Revert: the old ids back.
UPDATE `quest_template` SET `RequiredItemId1` = 16202
    WHERE `ID` IN (4107, 4112, 5886, 5891) AND `RequiredItemId1` = 11174;
UPDATE `quest_template` SET `RequiredItemId2` = 14343 WHERE `ID` IN (8779, 8807) AND `RequiredItemId2` = 11178;
