-- progression-slim PS3 D1: restore the vendor stock mod-progression phase 00 stripped (ungated, ruling 2026-11-05).
-- Rows: every (entry, item, ExtendedCost) that phases 07-18 re-inserted (MP 8c765a1,
-- src/phase_NN/sql/phase_NN-npc_vendor.sql) and that the live table lacks, plus the 4 stripped rows no phase
-- re-inserted (vendor 32172 items 48954-48957). Values (slot, maxcount, incrtime,
-- VerifiedBuild) are the STOCK ones: data/sql/base/db_world/npc_vendor.sql with the db_world updates
-- 2026_01_20_00, 2026_02_10_03, 2026_02_13_01, 2026_04_26_01, 2026_04_26_05 and 2026_09_24_01 applied.
-- Left out on purpose: the 220 rogue poison rows (items retired by 2026_10_31_25, rogue-rework RG0a), and every
-- ammo row (item class 6: arrows and shots; ammo is being dropped, user 2026-11-05), and Burkrum's (6028) 3 quivers
-- and ammo pouches (user 2026-11-05).
-- Every item below exists in item_template (checked against the live table, 0 missing).
-- Idempotent: each vendor's rows are deleted by (entry, item) before the insert.

-- Tharynn Bouden <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 66 AND `item` IN (10648, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(66, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(66, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Karm Ironquill <Mining Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 372 AND `item` IN (20815, 20824);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(372, 0, 20815, 0, 0, 0, 0), -- Jeweler's Kit
(372, 0, 20824, 0, 0, 0, 0); -- Simple Grinder

-- Elaine Trias <Mistress of Cheese>
DELETE FROM `npc_vendor` WHERE `entry` = 483 AND `item` IN (27857, 33443, 35952);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(483, 0, 27857, 0, 0, 0, 0), -- Garadar Sharp
(483, 0, 33443, 0, 0, 0, 0), -- Sour Goat Cheese
(483, 0, 35952, 0, 0, 0, 0); -- Briny Hardcheese

-- Amy Davenport <Tradeswoman>
DELETE FROM `npc_vendor` WHERE `entry` = 777 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(777, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Karen Taylor <Blacksmithing & Mining Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 790 AND `item` IN (20815, 20824);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(790, 0, 20815, 0, 0, 0, 0), -- Jeweler's Kit
(790, 0, 20824, 0, 0, 0, 0); -- Simple Grinder

-- Gina MacGregor <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 843 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(843, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Antonio Perelli <Traveling Salesman>
DELETE FROM `npc_vendor` WHERE `entry` = 844 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(844, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(844, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Dawn Brightstar <Arcane Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 958 AND `item` IN (18256, 22147, 22148, 37201, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(958, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(958, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(958, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(958, 0, 37201, 0, 0, 0, 0), -- Corpse Dust
(958, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Gunder Thornbush <Tradesman>
DELETE FROM `npc_vendor` WHERE `entry` = 960 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(960, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Thultazor <Alchemy Supplies & Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 983 AND `item` IN (18256, 22147, 22148, 37201, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(983, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(983, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(983, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(983, 0, 37201, 0, 0, 0, 0), -- Corpse Dust
(983, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Banalash <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 989 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(989, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Nerrist <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 1148 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1148, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Drake Lindgren <General & Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 1250 AND `item` IN (10648, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1250, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(1250, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Keldric Boucher <Alchemy Supplies & Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 1257 AND `item` IN (18256, 22147, 22148, 37201, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1257, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(1257, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(1257, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(1257, 0, 37201, 0, 0, 0, 0), -- Corpse Dust
(1257, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Kyra Boucher <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 1275 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1275, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(1275, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(1275, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Edna Mullby <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 1286 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1286, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Charys Yserian <Arcane Trinkets Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 1307 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1307, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(1307, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(1307, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Owen Vaughn <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 1308 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1308, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(1308, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(1308, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Maria Lumere <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 1313 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1313, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(1313, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Adair Gilroy <Librarian>
DELETE FROM `npc_vendor` WHERE `entry` = 1316 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1316, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Alexandra Bolero <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 1347 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1347, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Brother Cassius <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 1351 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1351, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(1351, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(1351, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Neal Allen <Engineering Supplies & General Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 1448 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1448, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(1448, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(1448, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Dewin Shimmerdawn <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 1453 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1453, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(1453, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Jennabink Powerseam <Tailoring Supplies & Specialty Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 1454 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1454, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Kersok Prond <Tradesman>
DELETE FROM `npc_vendor` WHERE `entry` = 1456 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1456, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Falkan Armonis <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 1463 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1463, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(1463, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(1463, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Drac Roughcut <Tradesman>
DELETE FROM `npc_vendor` WHERE `entry` = 1465 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1465, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Rann Flamespinner <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 1474 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1474, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Lohgan Eva <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 1672 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1672, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Alyssa Eva <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 1673 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1673, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(1673, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(1673, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Golorn Frostbeard <Tradesman>
DELETE FROM `npc_vendor` WHERE `entry` = 1692 AND `item` IN (10648, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1692, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(1692, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Loslor Rudge <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 1694 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(1694, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(1694, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(1694, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Abigail Shiel <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2118 AND `item` IN (10648, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2118, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(2118, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Nandar Branson <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2380 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2380, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(2380, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Micha Yance <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 2381 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2381, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Christoph Jeffcoat <Tradesman>
DELETE FROM `npc_vendor` WHERE `entry` = 2393 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2393, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Mallen Swain <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2394 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2394, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Bro'kin <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2480 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2480, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(2480, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Bliztik <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2481 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2481, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(2481, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Danielle Zipstitch <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2668 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2668, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Sheri Zipstitch <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2669 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2669, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Xizk Goodstitch <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2670 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2670, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Cowardly Crosby <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2672 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2672, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Fradd Swiftgear <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2682 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2682, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(2682, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(2682, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Namdo Bizzfizzle <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2683 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2683, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(2683, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(2683, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Rizz Loosebolt <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2684 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2684, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(2684, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(2684, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Mazk Snipeshot <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2685 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2685, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(2685, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(2685, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Gnaz Blunderflame <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2687 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2687, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(2687, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(2687, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Ruppo Zipcoil <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2688 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2688, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(2688, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(2688, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Clyde Ranthal <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2697 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2697, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- George Candarte <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2698 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2698, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Rikqiz <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2699 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2699, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Deneb Walker <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 2805 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2805, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(2805, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(2805, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Hammon Karwn <Superior Tradesman>
DELETE FROM `npc_vendor` WHERE `entry` = 2810 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2810, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Drovnar Strongbrew <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2812 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2812, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(2812, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Androd Fadran <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2816 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2816, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Tunkk <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2819 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2819, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Keena <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 2821 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2821, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Blixrez Goodstitch <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2846 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2846, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Glyx Brewright <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 2848 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(2848, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(2848, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Kurm Stonehoof <Mining Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3002 AND `item` IN (20815, 20824);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3002, 0, 20815, 0, 0, 0, 0), -- Jeweler's Kit
(3002, 0, 20824, 0, 0, 0, 0); -- Simple Grinder

-- Fyr Mistrunner <Bread Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 3003 AND `item` IN (27855, 33449, 35950);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3003, 0, 27855, 0, 0, 0, 0), -- Mag'har Grainbread
(3003, 0, 33449, 0, 0, 0, 0), -- Crusty Flatbread
(3003, 0, 35950, 0, 0, 0, 0); -- Sweet Potato Bread

-- Mahu <Leatherworking & Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3005 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3005, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Mani Winterhoof <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3010 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3010, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(3010, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Nida Winterhoof <Herbalism Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3014 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3014, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(3014, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Nan Mistrunner <Fruit Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 3017 AND `item` IN (27856, 35948, 35949);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3017, 0, 27856, 0, 0, 0, 0), -- Skethyl Berries
(3017, 0, 35948, 0, 0, 0, 0), -- Savory Snowplum
(3017, 0, 35949, 0, 0, 0, 0); -- Tundra Berries

-- Kaga Mistrunner <Meat Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 3025 AND `item` IN (27854, 33454, 35953);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3025, 0, 27854, 0, 0, 0, 0), -- Smoked Talbuk Venison
(3025, 0, 33454, 0, 0, 0, 0), -- Salted Venison
(3025, 0, 35953, 0, 0, 0, 0); -- Mead Basted Caribou

-- Wunna Darkmane <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 3081 AND `item` IN (10648, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3081, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(3081, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Franklin Hamar <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3091 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3091, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Captured Servant of Azora <Specialist Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3096 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3096, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Herble Baubbletump <Engineering & Mining Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3133 AND `item` IN (10648, 20815, 20824, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3133, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(3133, 0, 20815, 0, 0, 0, 0), -- Jeweler's Kit
(3133, 0, 20824, 0, 0, 0, 0), -- Simple Grinder
(3133, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(3133, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Wuark <Armorer & Shieldcrafter>
DELETE FROM `npc_vendor` WHERE `entry` = 3167 AND `item` IN (20815, 20824);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3167, 0, 20815, 0, 0, 0, 0), -- Jeweler's Kit
(3167, 0, 20824, 0, 0, 0, 0); -- Simple Grinder

-- Flakk <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3168 AND `item` IN (10648, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3168, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(3168, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Tai'tasi <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3187 AND `item` IN (10648, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3187, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(3187, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Olvia <Meat Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 3312 AND `item` IN (27854, 33454, 35953);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3312, 0, 27854, 0, 0, 0, 0), -- Smoked Talbuk Venison
(3312, 0, 33454, 0, 0, 0, 0), -- Salted Venison
(3312, 0, 35953, 0, 0, 0, 0); -- Mead Basted Caribou

-- Horthus <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 3323 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3323, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(3323, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(3323, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Kor'jus <Mushroom Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 3329 AND `item` IN (27859, 33452, 35947);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3329, 0, 27859, 0, 0, 0, 0), -- Zangar Caps
(3329, 0, 33452, 0, 0, 0, 0), -- Honey-Spiced Lichen
(3329, 0, 35947, 0, 0, 0, 0); -- Sparkling Frostcap

-- Hagrus <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 3335 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3335, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(3335, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(3335, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Shan'ti <Fruit Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 3342 AND `item` IN (27856, 35948, 35949);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3342, 0, 27856, 0, 0, 0, 0), -- Skethyl Berries
(3342, 0, 35948, 0, 0, 0, 0), -- Savory Snowplum
(3342, 0, 35949, 0, 0, 0, 0); -- Tundra Berries

-- Kor'geld <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3348 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3348, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(3348, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Magenius <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 3351 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3351, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(3351, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(3351, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Gorina <Mining Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3358 AND `item` IN (20815, 20824);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3358, 0, 20815, 0, 0, 0, 0), -- Jeweler's Kit
(3358, 0, 20824, 0, 0, 0, 0); -- Simple Grinder

-- Borya <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3364 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3364, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Tamar <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3366 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3366, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Felika <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3367 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3367, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Borstan <Meat Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 3368 AND `item` IN (27854, 33454, 35953);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3368, 0, 27854, 0, 0, 0, 0), -- Smoked Talbuk Venison
(3368, 0, 33454, 0, 0, 0, 0), -- Salted Venison
(3368, 0, 35953, 0, 0, 0, 0); -- Mead Basted Caribou

-- Prospector Khazgorm <Explorers' League>
DELETE FROM `npc_vendor` WHERE `entry` = 3392 AND `item` IN (20815, 20824);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3392, 0, 20815, 0, 0, 0, 0), -- Jeweler's Kit
(3392, 0, 20824, 0, 0, 0, 0); -- Simple Grinder

-- Zeal'aya <Herbalism Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3405 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3405, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(3405, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Sovik <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3413 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3413, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(3413, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(3413, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Tari'qa <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3482 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3482, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Wrahk <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3485 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3485, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Hula'mahi <Reagents, Herbs & Poison Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3490 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3490, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(3490, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(3490, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Gagsprocket <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3495 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3495, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(3495, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(3495, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Ranik <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3499 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3499, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Tarhus <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 3500 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3500, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(3500, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(3500, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Thomas Miller <Baker>
DELETE FROM `npc_vendor` WHERE `entry` = 3518 AND `item` IN (27855, 33449, 35950);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3518, 0, 27855, 0, 0, 0, 0), -- Mag'har Grainbread
(3518, 0, 33449, 0, 0, 0, 0), -- Crusty Flatbread
(3518, 0, 35950, 0, 0, 0, 0); -- Sweet Potato Bread

-- Jaysin Lanyda <Poisons & Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 3542 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3542, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(3542, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(3542, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Selina Weston <Alchemy & Herbalism Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3548 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3548, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(3548, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Andrew Hilbert <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3556 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3556, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Alaindia <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 3562 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3562, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(3562, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(3562, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Dalaran Miner
DELETE FROM `npc_vendor` WHERE `entry` = 3578 AND `item` IN (20815, 20824);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3578, 0, 20815, 0, 0, 0, 0), -- Jeweler's Kit
(3578, 0, 20824, 0, 0, 0, 0); -- Simple Grinder

-- Narret Shadowgrove <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3614 AND `item` IN (10648, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3614, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(3614, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Jadenvis Seawatcher <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 3700 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3700, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(3700, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(3700, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Syurana <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3779 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3779, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Dalria <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 3954 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3954, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Shandrina <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 3955 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3955, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Harklan Moongrove <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3956 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3956, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(3956, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Lardan <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3958 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3958, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Llana <Reagent Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 3970 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(3970, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(3970, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(3970, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Jeeda <Apprentice Witch Doctor>
DELETE FROM `npc_vendor` WHERE `entry` = 4083 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4083, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(4083, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(4083, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Elynna <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4168 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4168, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Jaeana <Meat Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 4169 AND `item` IN (27854, 28399, 33444, 33445, 33454, 35953, 35954);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4169, 0, 27854, 0, 0, 0, 0), -- Smoked Talbuk Venison
(4169, 0, 28399, 0, 0, 0, 0), -- Filtered Draenic Water
(4169, 0, 33444, 0, 0, 0, 0), -- Pungent Seal Whey
(4169, 0, 33445, 0, 0, 0, 0), -- Honeymint Tea
(4169, 0, 33454, 0, 0, 0, 0), -- Salted Venison
(4169, 0, 35953, 0, 0, 0, 0), -- Mead Basted Caribou
(4169, 0, 35954, 0, 0, 0, 0); -- Sweetened Goat's Milk

-- Valdaron <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4189 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4189, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Ullanna <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4194 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4194, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Chardryn <Herbalism Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4216 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4216, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(4216, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Cyroen <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 4220 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4220, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(4220, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(4220, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Talaelar <Fish Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 4221 AND `item` IN (33451, 35951);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4221, 0, 33451, 0, 0, 0, 0), -- Fillet of Icefin
(4221, 0, 35951, 0, 0, 0, 0); -- Poached Emperor Salmon

-- Saenorion <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4225 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4225, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Ulthir <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4226 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4226, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(4226, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Mythrin'dir <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4229 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4229, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Golnir Bouldertoe <Mining Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4256 AND `item` IN (20815, 20824);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4256, 0, 20815, 0, 0, 0, 0), -- Jeweler's Kit
(4256, 0, 20824, 0, 0, 0, 0); -- Simple Grinder

-- Wizzle Brassbolts
DELETE FROM `npc_vendor` WHERE `entry` = 4453 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4453, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(4453, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(4453, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Tawny Grisette <Mushroom Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 4554 AND `item` IN (27859, 28399, 33444, 33445, 33452, 35947, 35954);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4554, 0, 27859, 0, 0, 0, 0), -- Zangar Caps
(4554, 0, 28399, 0, 0, 0, 0), -- Filtered Draenic Water
(4554, 0, 33444, 0, 0, 0, 0), -- Pungent Seal Whey
(4554, 0, 33445, 0, 0, 0, 0), -- Honeymint Tea
(4554, 0, 33452, 0, 0, 0, 0), -- Honey-Spiced Lichen
(4554, 0, 35947, 0, 0, 0, 0), -- Sparkling Frostcap
(4554, 0, 35954, 0, 0, 0, 0); -- Sweetened Goat's Milk

-- Daniel Bartlett <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4561 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4561, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Thomas Mordan <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 4562 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4562, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(4562, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(4562, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Morley Bates <Fungus Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 4571 AND `item` IN (27859, 28399, 33444, 33445, 33452, 35947, 35954);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4571, 0, 27859, 0, 0, 0, 0), -- Zangar Caps
(4571, 0, 28399, 0, 0, 0, 0), -- Filtered Draenic Water
(4571, 0, 33444, 0, 0, 0, 0), -- Pungent Seal Whey
(4571, 0, 33445, 0, 0, 0, 0), -- Honeymint Tea
(4571, 0, 33452, 0, 0, 0, 0), -- Honey-Spiced Lichen
(4571, 0, 35947, 0, 0, 0, 0), -- Sparkling Frostcap
(4571, 0, 35954, 0, 0, 0, 0); -- Sweetened Goat's Milk

-- Hannah Akeley <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 4575 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4575, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(4575, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(4575, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Millie Gregorian <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4577 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4577, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Salazar Bloch <Book Dealer>
DELETE FROM `npc_vendor` WHERE `entry` = 4581 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4581, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Elizabeth Van Talen <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4587 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4587, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(4587, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(4587, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Joseph Moore <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4589 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4589, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Sarah Killian <Mining Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4599 AND `item` IN (20815, 20824);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4599, 0, 20815, 0, 0, 0, 0), -- Jeweler's Kit
(4599, 0, 20824, 0, 0, 0, 0); -- Simple Grinder

-- Algernon <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4610 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4610, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(4610, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Katrina Alliestar <Herbalism Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4615 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4615, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(4615, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Felicia Doan <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4775 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4775, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Jandia <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4877 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4877, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Montarr <Lorekeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 4878 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4878, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(4878, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(4878, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Helenia Olden <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4897 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4897, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Uma Bartulm <Herbalism & Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 4899 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4899, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(4899, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Ben Trias <Apprentice of Cheese>
DELETE FROM `npc_vendor` WHERE `entry` = 4981 AND `item` IN (27857, 28399, 33443, 33444, 33445, 35952, 35954);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(4981, 0, 27857, 0, 0, 0, 0), -- Garadar Sharp
(4981, 0, 28399, 0, 0, 0, 0), -- Filtered Draenic Water
(4981, 0, 33443, 0, 0, 0, 0), -- Sour Goat Cheese
(4981, 0, 33444, 0, 0, 0, 0), -- Pungent Seal Whey
(4981, 0, 33445, 0, 0, 0, 0), -- Honeymint Tea
(4981, 0, 35952, 0, 0, 0, 0), -- Briny Hardcheese
(4981, 0, 35954, 0, 0, 0, 0); -- Sweetened Goat's Milk

-- Lyesa Steelbrow <Tabard Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 5049 AND `item` IN (15196, 15198, 19032, 19506, 23999, 31774, 31775, 31776);
DELETE FROM `npc_vendor` WHERE `entry` = 5049 AND `item` IN (31777, 31778, 31779, 31780, 31781, 31804, 32445, 32828);
DELETE FROM `npc_vendor` WHERE `entry` = 5049 AND `item` IN (35221);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5049, 0, 15196, 0, 0, 1007, 0), -- Private's Tabard
(5049, 0, 15198, 0, 0, 1006, 0), -- Knight's Colors
(5049, 0, 19032, 0, 0, 1003, 0), -- Stormpike Battle Tabard
(5049, 0, 19506, 0, 0, 2969, 0), -- Silverwing Battle Tabard
(5049, 0, 23999, 0, 0, 0, 0), -- Honor Hold Tabard
(5049, 0, 31774, 0, 0, 0, 0), -- Kurenai Tabard
(5049, 0, 31775, 0, 0, 1994, 0), -- Sporeggar Tabard
(5049, 0, 31776, 0, 0, 0, 0), -- Consortium Tabard
(5049, 0, 31777, 0, 0, 0, 0), -- Keepers of Time Tabard
(5049, 0, 31778, 0, 0, 0, 0), -- Lower City Tabard
(5049, 0, 31779, 0, 0, 0, 0), -- Aldor Tabard
(5049, 0, 31780, 0, 0, 0, 0), -- Scryers Tabard
(5049, 0, 31781, 0, 0, 0, 0), -- Sha'tar Tabard
(5049, 0, 31804, 0, 0, 0, 0), -- Cenarion Expedition Tabard
(5049, 0, 32445, 0, 0, 0, 0), -- Skyguard Tabard
(5049, 0, 32828, 0, 0, 1958, 0), -- Ogri'la Tabard
(5049, 0, 35221, 0, 0, 0, 0); -- Tabard of the Shattered Sun

-- Fillius Fizzlespinner <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 5100 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5100, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Myra Tyrngaarde <Bread Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 5109 AND `item` IN (27855, 33449, 35950);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5109, 0, 27855, 0, 0, 0, 0), -- Mag'har Grainbread
(5109, 0, 33449, 0, 0, 0, 0), -- Crusty Flatbread
(5109, 0, 35950, 0, 0, 0, 0); -- Sweet Potato Bread

-- Barim Jurgenstaad <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 5110 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5110, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(5110, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(5110, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Innkeeper Firebrew <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 5111 AND `item` IN (27854, 28399, 33444, 33445, 33454, 35953, 35954);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5111, 0, 27854, 0, 0, 0, 0), -- Smoked Talbuk Venison
(5111, 0, 28399, 0, 0, 0, 0), -- Filtered Draenic Water
(5111, 0, 33444, 0, 0, 0, 0), -- Pungent Seal Whey
(5111, 0, 33445, 0, 0, 0, 0), -- Honeymint Tea
(5111, 0, 33454, 0, 0, 0, 0), -- Salted Venison
(5111, 0, 35953, 0, 0, 0, 0), -- Mead Basted Caribou
(5111, 0, 35954, 0, 0, 0, 0); -- Sweetened Goat's Milk

-- Sognar Cliffbeard <Meat Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 5124 AND `item` IN (27854, 33454, 35953);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5124, 0, 27854, 0, 0, 0, 0), -- Smoked Talbuk Venison
(5124, 0, 33454, 0, 0, 0, 0), -- Salted Venison
(5124, 0, 35953, 0, 0, 0, 0); -- Mead Basted Caribou

-- Bombus Finespindle <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 5128 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5128, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Gwina Stonebranch <Herbalism Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 5138 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5138, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(5138, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Ginny Longberry <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 5151 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5151, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(5151, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(5151, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Poranna Snowbraid <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 5154 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5154, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Burbik Gearspanner <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 5163 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5163, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Gearcutter Cogspinner <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 5175 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5175, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(5175, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(5175, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Soolie Berryfizz <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 5178 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5178, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(5178, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Garyl <Tabard Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 5188 AND `item` IN (15197, 15199, 19031, 19505, 24004, 31773, 31775, 31776);
DELETE FROM `npc_vendor` WHERE `entry` = 5188 AND `item` IN (31777, 31778, 31779, 31780, 31781, 31804, 32445, 32828);
DELETE FROM `npc_vendor` WHERE `entry` = 5188 AND `item` IN (35221);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5188, 0, 15197, 0, 0, 1007, 0), -- Scout's Tabard
(5188, 0, 15199, 0, 0, 1006, 0), -- Stone Guard's Herald
(5188, 0, 19031, 0, 0, 1003, 0), -- Frostwolf Battle Tabard
(5188, 0, 19505, 0, 0, 2969, 0), -- Warsong Battle Tabard
(5188, 0, 24004, 0, 0, 0, 0), -- Thrallmar Tabard
(5188, 0, 31773, 0, 0, 0, 0), -- Mag'har Tabard
(5188, 0, 31775, 0, 0, 1994, 0), -- Sporeggar Tabard
(5188, 0, 31776, 0, 0, 0, 0), -- Consortium Tabard
(5188, 0, 31777, 0, 0, 0, 0), -- Keepers of Time Tabard
(5188, 0, 31778, 0, 0, 0, 0), -- Lower City Tabard
(5188, 0, 31779, 0, 0, 0, 0), -- Aldor Tabard
(5188, 0, 31780, 0, 0, 0, 0), -- Scryers Tabard
(5188, 0, 31781, 0, 0, 0, 0), -- Sha'tar Tabard
(5188, 0, 31804, 0, 0, 0, 0), -- Cenarion Expedition Tabard
(5188, 0, 32445, 0, 0, 0, 0), -- Skyguard Tabard
(5188, 0, 32828, 0, 0, 1958, 0), -- Ogri'la Tabard
(5188, 0, 35221, 0, 0, 0, 0); -- Tabard of the Shattered Sun

-- Thrumn <Tabard Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 5189 AND `item` IN (15197, 15199, 19031, 19505, 24004, 31773, 31775, 31776);
DELETE FROM `npc_vendor` WHERE `entry` = 5189 AND `item` IN (31777, 31778, 31779, 31780, 31781, 31804, 32445, 32828);
DELETE FROM `npc_vendor` WHERE `entry` = 5189 AND `item` IN (35221);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5189, 0, 15197, 0, 0, 1007, 0), -- Scout's Tabard
(5189, 0, 15199, 0, 0, 1006, 0), -- Stone Guard's Herald
(5189, 0, 19031, 0, 0, 1003, 0), -- Frostwolf Battle Tabard
(5189, 0, 19505, 0, 0, 2969, 0), -- Warsong Battle Tabard
(5189, 0, 24004, 0, 0, 0, 0), -- Thrallmar Tabard
(5189, 0, 31773, 0, 0, 0, 0), -- Mag'har Tabard
(5189, 0, 31775, 0, 0, 1994, 0), -- Sporeggar Tabard
(5189, 0, 31776, 0, 0, 0, 0), -- Consortium Tabard
(5189, 0, 31777, 0, 0, 0, 0), -- Keepers of Time Tabard
(5189, 0, 31778, 0, 0, 0, 0), -- Lower City Tabard
(5189, 0, 31779, 0, 0, 0, 0), -- Aldor Tabard
(5189, 0, 31780, 0, 0, 0, 0), -- Scryers Tabard
(5189, 0, 31781, 0, 0, 0, 0), -- Sha'tar Tabard
(5189, 0, 31804, 0, 0, 0, 0), -- Cenarion Expedition Tabard
(5189, 0, 32445, 0, 0, 0, 0), -- Skyguard Tabard
(5189, 0, 32828, 0, 0, 1958, 0), -- Ogri'la Tabard
(5189, 0, 35221, 0, 0, 0, 0); -- Tabard of the Shattered Sun

-- Merill Pleasance <Tabard Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 5190 AND `item` IN (15197, 15199, 19031, 19505, 24004, 31773, 31775, 31776);
DELETE FROM `npc_vendor` WHERE `entry` = 5190 AND `item` IN (31777, 31778, 31779, 31780, 31781, 31804, 32445, 32828);
DELETE FROM `npc_vendor` WHERE `entry` = 5190 AND `item` IN (35221);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5190, 0, 15197, 0, 0, 1007, 0), -- Scout's Tabard
(5190, 0, 15199, 0, 0, 1006, 0), -- Stone Guard's Herald
(5190, 0, 19031, 0, 0, 1003, 0), -- Frostwolf Battle Tabard
(5190, 0, 19505, 0, 0, 2969, 0), -- Warsong Battle Tabard
(5190, 0, 24004, 0, 0, 0, 0), -- Thrallmar Tabard
(5190, 0, 31773, 0, 0, 0, 0), -- Mag'har Tabard
(5190, 0, 31775, 0, 0, 1994, 0), -- Sporeggar Tabard
(5190, 0, 31776, 0, 0, 0, 0), -- Consortium Tabard
(5190, 0, 31777, 0, 0, 0, 0), -- Keepers of Time Tabard
(5190, 0, 31778, 0, 0, 0, 0), -- Lower City Tabard
(5190, 0, 31779, 0, 0, 0, 0), -- Aldor Tabard
(5190, 0, 31780, 0, 0, 0, 0), -- Scryers Tabard
(5190, 0, 31781, 0, 0, 0, 0), -- Sha'tar Tabard
(5190, 0, 31804, 0, 0, 0, 0), -- Cenarion Expedition Tabard
(5190, 0, 32445, 0, 0, 0, 0), -- Skyguard Tabard
(5190, 0, 32828, 0, 0, 1958, 0), -- Ogri'la Tabard
(5190, 0, 35221, 0, 0, 0, 0); -- Tabard of the Shattered Sun

-- Shalumon <Tabard Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 5191 AND `item` IN (15196, 15198, 19032, 19506, 23999, 31774, 31775, 31776);
DELETE FROM `npc_vendor` WHERE `entry` = 5191 AND `item` IN (31777, 31778, 31779, 31780, 31781, 31804, 32445, 32828);
DELETE FROM `npc_vendor` WHERE `entry` = 5191 AND `item` IN (35221);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5191, 0, 15196, 0, 0, 1007, 0), -- Private's Tabard
(5191, 0, 15198, 0, 0, 1006, 0), -- Knight's Colors
(5191, 0, 19032, 0, 0, 1003, 0), -- Stormpike Battle Tabard
(5191, 0, 19506, 0, 0, 2969, 0), -- Silverwing Battle Tabard
(5191, 0, 23999, 0, 0, 0, 0), -- Honor Hold Tabard
(5191, 0, 31774, 0, 0, 0, 0), -- Kurenai Tabard
(5191, 0, 31775, 0, 0, 1994, 0), -- Sporeggar Tabard
(5191, 0, 31776, 0, 0, 0, 0), -- Consortium Tabard
(5191, 0, 31777, 0, 0, 0, 0), -- Keepers of Time Tabard
(5191, 0, 31778, 0, 0, 0, 0), -- Lower City Tabard
(5191, 0, 31779, 0, 0, 0, 0), -- Aldor Tabard
(5191, 0, 31780, 0, 0, 0, 0), -- Scryers Tabard
(5191, 0, 31781, 0, 0, 0, 0), -- Sha'tar Tabard
(5191, 0, 31804, 0, 0, 0, 0), -- Cenarion Expedition Tabard
(5191, 0, 32445, 0, 0, 0, 0), -- Skyguard Tabard
(5191, 0, 32828, 0, 0, 1958, 0), -- Ogri'la Tabard
(5191, 0, 35221, 0, 0, 0, 0); -- Tabard of the Shattered Sun

-- Rebecca Laughlin <Tabard Designer>
DELETE FROM `npc_vendor` WHERE `entry` = 5193 AND `item` IN (15196, 15198, 19032, 19506, 23999, 31774, 31775, 31776);
DELETE FROM `npc_vendor` WHERE `entry` = 5193 AND `item` IN (31777, 31778, 31779, 31780, 31781, 31804, 32445, 32828);
DELETE FROM `npc_vendor` WHERE `entry` = 5193 AND `item` IN (35221);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5193, 0, 15196, 0, 0, 1007, 0), -- Private's Tabard
(5193, 0, 15198, 0, 0, 1006, 0), -- Knight's Colors
(5193, 0, 19032, 0, 0, 1003, 0), -- Stormpike Battle Tabard
(5193, 0, 19506, 0, 0, 2969, 0), -- Silverwing Battle Tabard
(5193, 0, 23999, 0, 0, 0, 0), -- Honor Hold Tabard
(5193, 0, 31774, 0, 0, 0, 0), -- Kurenai Tabard
(5193, 0, 31775, 0, 0, 1994, 0), -- Sporeggar Tabard
(5193, 0, 31776, 0, 0, 0, 0), -- Consortium Tabard
(5193, 0, 31777, 0, 0, 0, 0), -- Keepers of Time Tabard
(5193, 0, 31778, 0, 0, 0, 0), -- Lower City Tabard
(5193, 0, 31779, 0, 0, 0, 0), -- Aldor Tabard
(5193, 0, 31780, 0, 0, 0, 0), -- Scryers Tabard
(5193, 0, 31781, 0, 0, 0, 0), -- Sha'tar Tabard
(5193, 0, 31804, 0, 0, 0, 0), -- Cenarion Expedition Tabard
(5193, 0, 32445, 0, 0, 0, 0), -- Skyguard Tabard
(5193, 0, 32828, 0, 0, 1958, 0), -- Ogri'la Tabard
(5193, 0, 35221, 0, 0, 0, 0); -- Tabard of the Shattered Sun

-- Eldraeith <Herbalism Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 5503 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5503, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(5503, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Brooke Stonebraid <Mining Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 5514 AND `item` IN (20815, 20824);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5514, 0, 20815, 0, 0, 0, 0), -- Jeweler's Kit
(5514, 0, 20824, 0, 0, 0, 0); -- Simple Grinder

-- Billibub Cogspinner <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 5519 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5519, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(5519, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(5519, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Jillian Tanner <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 5565 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5565, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Alchemist Pestlezugg <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 5594 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5594, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(5594, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Kalldan Felmoon <Specialist Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 5783 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5783, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Shimra <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 5817 AND `item` IN (10648, 18256, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5817, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(5817, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(5817, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Yonada <Tailoring & Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 5944 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(5944, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Thelgrum Stonehammer <Mining Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 6298 AND `item` IN (20815, 20824);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(6298, 0, 20815, 0, 0, 0, 0), -- Jeweler's Kit
(6298, 0, 20824, 0, 0, 0, 0); -- Simple Grinder

-- Gorbold Steelhand <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 6301 AND `item` IN (18256, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(6301, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(6301, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Ghok'kah <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 6567 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(6567, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Vizzklick <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 6568 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(6568, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Jun'ha <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 6574 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(6574, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Brienna Starglow <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 6576 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(6576, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Jinky Twizzlefixxit <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 6730 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(6730, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(6730, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(6730, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Harlown Darkweave <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 6731 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(6731, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Innkeeper Saelienne <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 6735 AND `item` IN (27856, 28399, 33444, 33445, 35948, 35949, 35954);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(6735, 0, 27856, 0, 0, 0, 0), -- Skethyl Berries
(6735, 0, 28399, 0, 0, 0, 0), -- Filtered Draenic Water
(6735, 0, 33444, 0, 0, 0, 0), -- Pungent Seal Whey
(6735, 0, 33445, 0, 0, 0, 0), -- Honeymint Tea
(6735, 0, 35948, 0, 0, 0, 0), -- Savory Snowplum
(6735, 0, 35949, 0, 0, 0, 0), -- Tundra Berries
(6735, 0, 35954, 0, 0, 0, 0); -- Sweetened Goat's Milk

-- Innkeeper Allison <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 6740 AND `item` IN (27855, 27856, 28399, 33444, 33445, 33449, 35948, 35949);
DELETE FROM `npc_vendor` WHERE `entry` = 6740 AND `item` IN (35950, 35954);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(6740, 0, 27855, 0, 0, 0, 0), -- Mag'har Grainbread
(6740, 0, 27856, 0, 0, 0, 0), -- Skethyl Berries
(6740, 0, 28399, 0, 0, 0, 0), -- Filtered Draenic Water
(6740, 0, 33444, 0, 0, 0, 0), -- Pungent Seal Whey
(6740, 0, 33445, 0, 0, 0, 0), -- Honeymint Tea
(6740, 0, 33449, 0, 0, 0, 0), -- Crusty Flatbread
(6740, 0, 35948, 0, 0, 0, 0), -- Savory Snowplum
(6740, 0, 35949, 0, 0, 0, 0), -- Tundra Berries
(6740, 0, 35950, 0, 0, 0, 0), -- Sweet Potato Bread
(6740, 0, 35954, 0, 0, 0, 0); -- Sweetened Goat's Milk

-- Innkeeper Norman <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 6741 AND `item` IN (27859, 28399, 33444, 33445, 33452, 35947, 35954);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(6741, 0, 27859, 0, 0, 0, 0), -- Zangar Caps
(6741, 0, 28399, 0, 0, 0, 0), -- Filtered Draenic Water
(6741, 0, 33444, 0, 0, 0, 0), -- Pungent Seal Whey
(6741, 0, 33445, 0, 0, 0, 0), -- Honeymint Tea
(6741, 0, 33452, 0, 0, 0, 0), -- Honey-Spiced Lichen
(6741, 0, 35947, 0, 0, 0, 0), -- Sparkling Frostcap
(6741, 0, 35954, 0, 0, 0, 0); -- Sweetened Goat's Milk

-- Innkeeper Pala <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 6746 AND `item` IN (27857, 28399, 33443, 33444, 33445, 35952, 35954);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(6746, 0, 27857, 0, 0, 0, 0), -- Garadar Sharp
(6746, 0, 28399, 0, 0, 0, 0), -- Filtered Draenic Water
(6746, 0, 33443, 0, 0, 0, 0), -- Sour Goat Cheese
(6746, 0, 33444, 0, 0, 0, 0), -- Pungent Seal Whey
(6746, 0, 33445, 0, 0, 0, 0), -- Honeymint Tea
(6746, 0, 35952, 0, 0, 0, 0), -- Briny Hardcheese
(6746, 0, 35954, 0, 0, 0, 0); -- Sweetened Goat's Milk

-- Zan Shivsproket <Speciality Engineer>
DELETE FROM `npc_vendor` WHERE `entry` = 6777 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(6777, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(6777, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(6777, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Innkeeper Gryshka <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 6929 AND `item` IN (27854, 28399, 33444, 33445, 33454, 35953, 35954);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(6929, 0, 27854, 0, 0, 0, 0), -- Smoked Talbuk Venison
(6929, 0, 28399, 0, 0, 0, 0), -- Filtered Draenic Water
(6929, 0, 33444, 0, 0, 0, 0), -- Pungent Seal Whey
(6929, 0, 33445, 0, 0, 0, 0), -- Honeymint Tea
(6929, 0, 33454, 0, 0, 0, 0), -- Salted Venison
(6929, 0, 35953, 0, 0, 0, 0), -- Mead Basted Caribou
(6929, 0, 35954, 0, 0, 0, 0); -- Sweetened Goat's Milk

-- Pratt McGrubben <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 7852 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(7852, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Jangdor Swiftstrider <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 7854 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(7854, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Darnall <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 7940 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(7940, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Vivianna <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 7947 AND `item` IN (18256, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(7947, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(7947, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Bimble Longberry <Fruit Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 7978 AND `item` IN (27856, 35948, 35949);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(7978, 0, 27856, 0, 0, 0, 0), -- Skethyl Berries
(7978, 0, 35948, 0, 0, 0, 0), -- Savory Snowplum
(7978, 0, 35949, 0, 0, 0, 0); -- Tundra Berries

-- Sheendra Tallgrass <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 8145 AND `item` IN (18256, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(8145, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(8145, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Logannas <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 8157 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(8157, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(8157, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Bronk <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 8158 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(8158, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(8158, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Nioma <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 8160 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(8160, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Rartar <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 8177 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(8177, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(8177, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Nina Lightbrew <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 8178 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(8178, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(8178, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Kixxle <Potions & Herbs>
DELETE FROM `npc_vendor` WHERE `entry` = 8305 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(8305, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(8305, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Chepi <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 8361 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(8361, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(8361, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(8361, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Shadi Mistrunner <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 8363 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(8363, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Jubie Gadgetspring <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 8678 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(8678, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(8678, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(8678, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Knaz Blunderflame <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 8679 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(8679, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(8679, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(8679, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Outfitter Eric <Speciality Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 8681 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(8681, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Christopher Hewen <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 8934 AND `item` IN (10648, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(8934, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(8934, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Yuka Screwspigot
DELETE FROM `npc_vendor` WHERE `entry` = 9544 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(9544, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(9544, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(9544, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Kireena <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 9636 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(9636, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Xizzer Fizzbolt <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 11185 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(11185, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(11185, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(11185, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Lunnix Sprocketslip <Mining Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 11186 AND `item` IN (20815, 20824);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(11186, 0, 20815, 0, 0, 0, 0), -- Jeweler's Kit
(11186, 0, 20824, 0, 0, 0, 0); -- Simple Grinder

-- Evie Whirlbrew <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 11188 AND `item` IN (18256, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(11188, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(11188, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Qia <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 11189 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(11189, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Meilosh
DELETE FROM `npc_vendor` WHERE `entry` = 11557 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(11557, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Masat T'andr <Superior Leatherworker>
DELETE FROM `npc_vendor` WHERE `entry` = 11874 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(11874, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Lorelae Wintersong <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 12022 AND `item` IN (18256, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(12022, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(12022, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Lah'Mawhani <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 12028 AND `item` IN (18256, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(12028, 0, 18256, 0, 0, 0, 0), -- Imbued Vial
(12028, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Kulwia <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 12043 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(12043, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Vendor-Tron 1000
DELETE FROM `npc_vendor` WHERE `entry` = 12245 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(12245, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Jase Farlane <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 12941 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(12941, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Leonard Porter <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 12942 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(12942, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Werg Thickblade <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 12943 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(12943, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Zannok Hidepiercer <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 12956 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(12956, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Blimo Gadgetspring <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 12957 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(12957, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Gigget Zipcoil <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 12958 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(12958, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Balai Lok'Wein <Potions, Scrolls & Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 13476 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(13476, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(13476, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(13476, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Zorbin Fandazzle
DELETE FROM `npc_vendor` WHERE `entry` = 14637 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(14637, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(14637, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(14637, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Mystic Yayo'jin <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 14739 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(14739, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(14739, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(14739, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Haughty Modiste <Fashion Designer>
DELETE FROM `npc_vendor` WHERE `entry` = 15165 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(15165, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Khur Hornstriker <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 15175 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(15175, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(15175, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(15175, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Mishta <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 15179 AND `item` IN (18256);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(15179, 0, 18256, 0, 0, 0, 0); -- Imbued Vial

-- Vi'el <Exotic Reagent Merchant>
DELETE FROM `npc_vendor` WHERE `entry` = 16015 AND `item` IN (22147, 22148, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16015, 0, 22147, 0, 0, 0, 0), -- Flintweed Seed
(16015, 0, 22148, 0, 0, 0, 0), -- Wild Quillvine
(16015, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Rathis Tomber <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 16224 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16224, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Sathiel <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 16261 AND `item` IN (10648, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16261, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(16261, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Landraelanis <Tradesman>
DELETE FROM `npc_vendor` WHERE `entry` = 16262 AND `item` IN (10648, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16262, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(16262, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Sempstress Ambershine <Tailoring Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 16366 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16366, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Botanist Tyniarrel <Herbalism Trainer & Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 16367 AND `item` IN (40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16367, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Apothecary Antonivich <Master Alchemy Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 16588 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16588, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Floyd Pinkus <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 16602 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16602, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Kredis <Tabard Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 16610 AND `item` IN (15197, 15199, 19031, 19505, 24004, 31773, 31775, 31776);
DELETE FROM `npc_vendor` WHERE `entry` = 16610 AND `item` IN (31777, 31778, 31779, 31780, 31781, 31804, 32445, 32828);
DELETE FROM `npc_vendor` WHERE `entry` = 16610 AND `item` IN (35221);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16610, 0, 15197, 0, 0, 1007, 0), -- Scout's Tabard
(16610, 0, 15199, 0, 0, 1006, 0), -- Stone Guard's Herald
(16610, 0, 19031, 0, 0, 1003, 0), -- Frostwolf Battle Tabard
(16610, 0, 19505, 0, 0, 2969, 0), -- Warsong Battle Tabard
(16610, 0, 24004, 0, 0, 0, 0), -- Thrallmar Tabard
(16610, 0, 31773, 0, 0, 0, 0), -- Mag'har Tabard
(16610, 0, 31775, 0, 0, 1994, 0), -- Sporeggar Tabard
(16610, 0, 31776, 0, 0, 0, 0), -- Consortium Tabard
(16610, 0, 31777, 0, 0, 0, 0), -- Keepers of Time Tabard
(16610, 0, 31778, 0, 0, 0, 0), -- Lower City Tabard
(16610, 0, 31779, 0, 0, 0, 0), -- Aldor Tabard
(16610, 0, 31780, 0, 0, 0, 0), -- Scryers Tabard
(16610, 0, 31781, 0, 0, 0, 0), -- Sha'tar Tabard
(16610, 0, 31804, 0, 0, 0, 0), -- Cenarion Expedition Tabard
(16610, 0, 32445, 0, 0, 0, 0), -- Skyguard Tabard
(16610, 0, 32828, 0, 0, 1958, 0), -- Ogri'la Tabard
(16610, 0, 35221, 0, 0, 0, 0); -- Tabard of the Shattered Sun

-- Zalle <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 16611 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16611, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Velanni <Alchemy Supplies & Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 16612 AND `item` IN (37201, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16612, 0, 37201, 0, 0, 0, 0), -- Corpse Dust
(16612, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Innkeeper Velandra <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 16618 AND `item` IN (33444, 33445, 33451, 33454, 35951, 35953, 35954);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16618, 0, 33444, 0, 0, 0, 0), -- Pungent Seal Whey
(16618, 0, 33445, 0, 0, 0, 0), -- Honeymint Tea
(16618, 0, 33451, 0, 0, 0, 0), -- Fillet of Icefin
(16618, 0, 33454, 0, 0, 0, 0), -- Salted Venison
(16618, 0, 35951, 0, 0, 0, 0), -- Poached Emperor Salmon
(16618, 0, 35953, 0, 0, 0, 0), -- Mead Basted Caribou
(16618, 0, 35954, 0, 0, 0, 0); -- Sweetened Goat's Milk

-- Deynna <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 16638 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16638, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Melaris <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 16641 AND `item` IN (40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16641, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Feera <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 16657 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16657, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(16657, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(16657, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Zaralda <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 16689 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16689, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Altaa <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 16705 AND `item` IN (40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16705, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Musal <Alchemy Supplies & Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 16706 AND `item` IN (37201, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16706, 0, 37201, 0, 0, 0, 0), -- Corpse Dust
(16706, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Caregiver Breel <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 16739 AND `item` IN (33444, 33445, 33449, 33451, 33454, 35950, 35951, 35953);
DELETE FROM `npc_vendor` WHERE `entry` = 16739 AND `item` IN (35954);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16739, 0, 33444, 0, 0, 0, 0), -- Pungent Seal Whey
(16739, 0, 33445, 0, 0, 0, 0), -- Honeymint Tea
(16739, 0, 33449, 0, 0, 0, 0), -- Crusty Flatbread
(16739, 0, 33451, 0, 0, 0, 0), -- Fillet of Icefin
(16739, 0, 33454, 0, 0, 0, 0), -- Salted Venison
(16739, 0, 35950, 0, 0, 0, 0), -- Sweet Potato Bread
(16739, 0, 35951, 0, 0, 0, 0), -- Poached Emperor Salmon
(16739, 0, 35953, 0, 0, 0, 0), -- Mead Basted Caribou
(16739, 0, 35954, 0, 0, 0, 0); -- Sweetened Goat's Milk

-- Haferet <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 16748 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16748, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Bildine <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 16757 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16757, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Issca <Tabard Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 16766 AND `item` IN (15196, 15198, 19032, 19506, 23999, 31774, 31775, 31776);
DELETE FROM `npc_vendor` WHERE `entry` = 16766 AND `item` IN (31777, 31778, 31779, 31780, 31781, 31804, 32445, 32828);
DELETE FROM `npc_vendor` WHERE `entry` = 16766 AND `item` IN (35221);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16766, 0, 15196, 0, 0, 1007, 0), -- Private's Tabard
(16766, 0, 15198, 0, 0, 1006, 0), -- Knight's Colors
(16766, 0, 19032, 0, 0, 1003, 0), -- Stormpike Battle Tabard
(16766, 0, 19506, 0, 0, 2969, 0), -- Silverwing Battle Tabard
(16766, 0, 23999, 0, 0, 0, 0), -- Honor Hold Tabard
(16766, 0, 31774, 0, 0, 0, 0), -- Kurenai Tabard
(16766, 0, 31775, 0, 0, 1994, 0), -- Sporeggar Tabard
(16766, 0, 31776, 0, 0, 0, 0), -- Consortium Tabard
(16766, 0, 31777, 0, 0, 0, 0), -- Keepers of Time Tabard
(16766, 0, 31778, 0, 0, 0, 0), -- Lower City Tabard
(16766, 0, 31779, 0, 0, 0, 0), -- Aldor Tabard
(16766, 0, 31780, 0, 0, 0, 0), -- Scryers Tabard
(16766, 0, 31781, 0, 0, 0, 0), -- Sha'tar Tabard
(16766, 0, 31804, 0, 0, 0, 0), -- Cenarion Expedition Tabard
(16766, 0, 32445, 0, 0, 0, 0), -- Skyguard Tabard
(16766, 0, 32828, 0, 0, 1958, 0), -- Ogri'la Tabard
(16766, 0, 35221, 0, 0, 0, 0); -- Tabard of the Shattered Sun

-- Neii <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 16767 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16767, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Yatheon <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 16782 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16782, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(16782, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(16782, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Sid Limbardi <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 16826 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16826, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Magus Zabraxis <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 16829 AND `item` IN (37201, 40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(16829, 0, 37201, 0, 0, 0, 0), -- Corpse Dust
(16829, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Artificer Daelo <Engineering Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 17222 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(17222, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(17222, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(17222, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Clopper Wizbang <Explorers' League>
DELETE FROM `npc_vendor` WHERE `entry` = 17421 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(17421, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(17421, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(17421, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Ergh of the Stillpine <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 17490 AND `item` IN (10648, 39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(17490, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(17490, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Innkeeper Jovia <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 17630 AND `item` IN (27854, 27855, 27856, 27857, 33443, 33444, 33445, 33449);
DELETE FROM `npc_vendor` WHERE `entry` = 17630 AND `item` IN (33454, 35948, 35949, 35950, 35952, 35953, 35954);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(17630, 0, 27854, 0, 0, 0, 0), -- Smoked Talbuk Venison
(17630, 0, 27855, 0, 0, 0, 0), -- Mag'har Grainbread
(17630, 0, 27856, 0, 0, 0, 0), -- Skethyl Berries
(17630, 0, 27857, 0, 0, 0, 0), -- Garadar Sharp
(17630, 0, 33443, 0, 0, 0, 0), -- Sour Goat Cheese
(17630, 0, 33444, 0, 0, 0, 0), -- Pungent Seal Whey
(17630, 0, 33445, 0, 0, 0, 0), -- Honeymint Tea
(17630, 0, 33449, 0, 0, 0, 0), -- Crusty Flatbread
(17630, 0, 33454, 0, 0, 0, 0), -- Salted Venison
(17630, 0, 35948, 0, 0, 0, 0), -- Savory Snowplum
(17630, 0, 35949, 0, 0, 0, 0), -- Tundra Berries
(17630, 0, 35950, 0, 0, 0, 0), -- Sweet Potato Bread
(17630, 0, 35952, 0, 0, 0, 0), -- Briny Hardcheese
(17630, 0, 35953, 0, 0, 0, 0), -- Mead Basted Caribou
(17630, 0, 35954, 0, 0, 0, 0); -- Sweetened Goat's Milk

-- Haalrun <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 18005 AND `item` IN (40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18005, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Noraani <Reagent Merchant>
DELETE FROM `npc_vendor` WHERE `entry` = 18006 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18006, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Gambarinka <Tradesman>
DELETE FROM `npc_vendor` WHERE `entry` = 18015 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18015, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Seer Janidi <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 18017 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18017, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Timothy Daniels <The Specialist>
DELETE FROM `npc_vendor` WHERE `entry` = 18019 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18019, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Lorti <Merchant>
DELETE FROM `npc_vendor` WHERE `entry` = 18243 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18243, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Kinamisa <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 18277 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18277, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Pilot Marsha <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 18278 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18278, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(18278, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(18278, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Terellia <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 18426 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18426, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Fazu <Tradesman>
DELETE FROM `npc_vendor` WHERE `entry` = 18427 AND `item` IN (39354);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18427, 0, 39354, 0, 0, 0, 0); -- Light Parchment

-- Wind Trader Lathrai
DELETE FROM `npc_vendor` WHERE `entry` = 18484 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18484, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(18484, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(18484, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- G'eras
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (29266, 29267, 29268, 29269, 29270, 29271, 29272, 29273);
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (29274, 29275, 29367, 29368, 29369, 29370, 29373, 29374);
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (29375, 29376, 29379, 29381, 29382, 29383, 29384, 29385);
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (29386, 29387, 29388, 29389, 29390, 30761, 30762, 30763);
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (30764, 30766, 30767, 30768, 30769, 30770, 30772, 30773);
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (30774, 30776, 30778, 30779, 30780, 32083, 32084, 32085);
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (32086, 32087, 32088, 32089, 32090, 33192, 33207, 33222);
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (33279, 33280, 33287, 33291, 33296, 33304, 33324, 33325);
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (33331, 33333, 33334, 33386, 33484, 33501, 33502, 33503);
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (33504, 33505, 33506, 33507, 33508, 33509, 33510, 33512);
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (33513, 33514, 33515, 33516, 33517, 33518, 33519, 33520);
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (33522, 33523, 33524, 33527, 33528, 33529, 33530, 33531);
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (33532, 33534, 33535, 33536, 33537, 33538, 33539, 33540);
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (33552, 33557, 33559, 33566, 33577, 33578, 33579, 33580);
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (33582, 33583, 33584, 33585, 33586, 33587, 33588, 33589);
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (33593, 33810, 33832, 33965, 33970, 33972, 33973, 33974);
DELETE FROM `npc_vendor` WHERE `entry` = 18525 AND `item` IN (34049, 34050, 34162, 34163, 35321, 35324, 35326);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18525, 0, 29266, 0, 0, 1037, 0), -- Azure-Shield of Coldarra
(18525, 0, 29267, 0, 0, 1037, 0), -- Light-Bearer's Faith Shield
(18525, 0, 29268, 0, 0, 1037, 0), -- Mazthoril Honor Shield
(18525, 0, 29269, 0, 0, 1015, 0), -- Sapphiron's Wing Bone
(18525, 0, 29270, 0, 0, 1015, 0), -- Flametongue Seal
(18525, 0, 29271, 0, 0, 1015, 0), -- Talisman of Kalecgos
(18525, 0, 29272, 0, 0, 1015, 0), -- Orb of the Soul-Eater
(18525, 0, 29273, 0, 0, 1015, 0), -- Khadgar's Knapsack
(18525, 0, 29274, 0, 0, 1015, 0), -- Tears of Heaven
(18525, 0, 29275, 0, 0, 1040, 0), -- Searing Sunblade
(18525, 0, 29367, 0, 0, 1015, 0), -- Ring of Cryptic Dreams
(18525, 0, 29368, 0, 0, 1015, 0), -- Manasurge Pendant
(18525, 0, 29369, 0, 0, 1015, 0), -- Shawl of Shifting Probabilities
(18525, 0, 29370, 0, 0, 1027, 0), -- Icon of the Silver Crescent
(18525, 0, 29373, 0, 0, 1015, 0), -- Band of Halos
(18525, 0, 29374, 0, 0, 1015, 0), -- Necklace of Eternal Hope
(18525, 0, 29375, 0, 0, 1015, 0), -- Bishop's Cloak
(18525, 0, 29376, 0, 0, 1027, 0), -- Essence of the Martyr
(18525, 0, 29379, 0, 0, 1015, 0), -- Ring of Arathi Warlords
(18525, 0, 29381, 0, 0, 1015, 0), -- Choker of Vile Intent
(18525, 0, 29382, 0, 0, 1015, 0), -- Blood Knight War Cloak
(18525, 0, 29383, 0, 0, 1027, 0), -- Bloodlust Brooch
(18525, 0, 29384, 0, 0, 1015, 0), -- Ring of Unyielding Force
(18525, 0, 29385, 0, 0, 1015, 0), -- Farstrider Defender's Cloak
(18525, 0, 29386, 0, 0, 1015, 0), -- Necklace of the Juggernaut
(18525, 0, 29387, 0, 0, 1027, 0), -- Gnomeregan Auto-Blocker 600
(18525, 0, 29388, 0, 0, 1642, 0), -- Libram of Repentance
(18525, 0, 29389, 0, 0, 1642, 0), -- Totem of the Pulsing Earth
(18525, 0, 29390, 0, 0, 1642, 0), -- Everbloom Idol
(18525, 0, 30761, 0, 0, 1454, 0), -- Infernoweave Leggings
(18525, 0, 30762, 0, 0, 1454, 0), -- Infernoweave Robe
(18525, 0, 30763, 0, 0, 1452, 0), -- Infernoweave Boots
(18525, 0, 30764, 0, 0, 1452, 0), -- Infernoweave Gloves
(18525, 0, 30766, 0, 0, 1454, 0), -- Inferno Tempered Leggings
(18525, 0, 30767, 0, 0, 1452, 0), -- Inferno Tempered Gauntlets
(18525, 0, 30768, 0, 0, 1452, 0), -- Inferno Tempered Boots
(18525, 0, 30769, 0, 0, 1454, 0), -- Inferno Tempered Chestguard
(18525, 0, 30770, 0, 0, 1452, 0), -- Inferno Forged Boots
(18525, 0, 30772, 0, 0, 1454, 0), -- Inferno Forged Leggings
(18525, 0, 30773, 0, 0, 1454, 0), -- Inferno Forged Hauberk
(18525, 0, 30774, 0, 0, 1452, 0), -- Inferno Forged Gloves
(18525, 0, 30776, 0, 0, 1454, 0), -- Inferno Hardened Chestguard
(18525, 0, 30778, 0, 0, 1454, 0), -- Inferno Hardened Leggings
(18525, 0, 30779, 0, 0, 1452, 0), -- Inferno Hardened Boots
(18525, 0, 30780, 0, 0, 1452, 0), -- Inferno Hardened Gloves
(18525, 0, 32083, 0, 0, 1040, 0), -- Faceguard of Determination
(18525, 0, 32084, 0, 0, 1040, 0), -- Helmet of the Steadfast Champion
(18525, 0, 32085, 0, 0, 1040, 0), -- Warpstalker Helm
(18525, 0, 32086, 0, 0, 1040, 0), -- Storm Master's Helmet
(18525, 0, 32087, 0, 0, 1040, 0), -- Mask of the Deceiver
(18525, 0, 32088, 0, 0, 1040, 0), -- Cowl of Beastly Rage
(18525, 0, 32089, 0, 0, 1040, 0), -- Mana-Binders Cowl
(18525, 0, 32090, 0, 0, 1040, 0), -- Cowl of Naaru Blessings
(18525, 0, 33192, 0, 0, 1015, 0), -- Carved Witch Doctor's Stick
(18525, 0, 33207, 0, 0, 2059, 0), -- Implacable Guardian Sabatons
(18525, 0, 33222, 0, 0, 2059, 0), -- Nyn'jah's Tabi Boots
(18525, 0, 33279, 0, 0, 2059, 0), -- Iron-tusk Girdle
(18525, 0, 33280, 0, 0, 2059, 0), -- War-Feathered Loop
(18525, 0, 33287, 0, 0, 2059, 0), -- Gnarled Ironwood Pauldrons
(18525, 0, 33291, 0, 0, 2059, 0), -- Voodoo-woven Belt
(18525, 0, 33296, 0, 0, 2060, 0), -- Brooch of Deftness
(18525, 0, 33304, 0, 0, 2059, 0), -- Cloak of Subjugated Power
(18525, 0, 33324, 0, 0, 2059, 0), -- Treads of the Life Path
(18525, 0, 33325, 0, 0, 2060, 0), -- Voodoo Shaker
(18525, 0, 33331, 0, 0, 2059, 0), -- Chain of Unleashed Rage
(18525, 0, 33333, 0, 0, 2059, 0), -- Kharmaa's Shroud of Hope
(18525, 0, 33334, 0, 0, 2060, 0), -- Fetish of the Primal Gods
(18525, 0, 33386, 0, 0, 2059, 0), -- Man'kin'do's Belt
(18525, 0, 33484, 0, 0, 2059, 0), -- Dory's Embrace
(18525, 0, 33501, 0, 0, 2049, 0), -- Bloodthirster's Wargreaves
(18525, 0, 33502, 0, 0, 1452, 0), -- Libram of Mending
(18525, 0, 33503, 0, 0, 1452, 0), -- Libram of Divine Judgement
(18525, 0, 33504, 0, 0, 1452, 0), -- Libram of Divine Purpose
(18525, 0, 33505, 0, 0, 1452, 0), -- Totem of Living Water
(18525, 0, 33506, 0, 0, 1452, 0), -- Skycall Totem
(18525, 0, 33507, 0, 0, 1452, 0), -- Stonebreaker's Totem
(18525, 0, 33508, 0, 0, 1452, 0), -- Idol of Budding Life
(18525, 0, 33509, 0, 0, 1452, 0), -- Idol of Terror
(18525, 0, 33510, 0, 0, 1452, 0), -- Idol of the Unseen Moon
(18525, 0, 33512, 0, 0, 2059, 0), -- Furious Deathgrips
(18525, 0, 33513, 0, 0, 2060, 0), -- Eternium Rage-shackles
(18525, 0, 33514, 0, 0, 2059, 0), -- Pauldrons of Gruesome Fate
(18525, 0, 33515, 0, 0, 2049, 0), -- Unwavering Legguards
(18525, 0, 33516, 0, 0, 2060, 0), -- Bracers of the Ancient Phalanx
(18525, 0, 33517, 0, 0, 2059, 0), -- Bonefist Gauntlets
(18525, 0, 33518, 0, 0, 2049, 0), -- High Justicar's Legplates
(18525, 0, 33519, 0, 0, 2059, 0), -- Handguards of the Templar
(18525, 0, 33520, 0, 0, 2060, 0), -- Vambraces of the Naaru
(18525, 0, 33522, 0, 0, 2049, 0), -- Chestguard of the Stoic Guardian
(18525, 0, 33523, 0, 0, 2059, 0), -- Sabatons of the Righteous Defender
(18525, 0, 33524, 0, 0, 2059, 0), -- Girdle of the Protector
(18525, 0, 33527, 0, 0, 2049, 0), -- Shifting Camouflage Pants
(18525, 0, 33528, 0, 0, 2059, 0), -- Gauntlets of Sniping
(18525, 0, 33529, 0, 0, 2060, 0), -- Steadying Bracers
(18525, 0, 33530, 0, 0, 2049, 0), -- Natural Life Leggings
(18525, 0, 33531, 0, 0, 2059, 0), -- Polished Waterscale Gloves
(18525, 0, 33532, 0, 0, 2060, 0), -- Gleaming Earthen Bracers
(18525, 0, 33534, 0, 0, 2059, 0), -- Grips of Nature's Wrath
(18525, 0, 33535, 0, 0, 2060, 0), -- Earthquake Bracers
(18525, 0, 33536, 0, 0, 2059, 0), -- Stormwrap
(18525, 0, 33537, 0, 0, 2059, 0), -- Treads of Booming Thunder
(18525, 0, 33538, 0, 0, 2049, 0), -- Shallow-grave Trousers
(18525, 0, 33539, 0, 0, 2059, 0), -- Trickster's Stickyfingers
(18525, 0, 33540, 0, 0, 2060, 0), -- Master Assassin Wristwraps
(18525, 0, 33552, 0, 0, 2049, 0), -- Pants of Splendid Recovery
(18525, 0, 33557, 0, 0, 2060, 0), -- Gargon's Bracers of Peaceful Slumber
(18525, 0, 33559, 0, 0, 2059, 0), -- Starfire Waistband
(18525, 0, 33566, 0, 0, 2049, 0), -- Blessed Elunite Coverings
(18525, 0, 33577, 0, 0, 2059, 0), -- Moon-walkers
(18525, 0, 33578, 0, 0, 2060, 0), -- Armwraps of the Kaldorei Protector
(18525, 0, 33579, 0, 0, 2049, 0), -- Vestments of Hibernation
(18525, 0, 33580, 0, 0, 2060, 0), -- Band of the Swift Paw
(18525, 0, 33582, 0, 0, 2059, 0), -- Footwraps of Wild Encroachment
(18525, 0, 33583, 0, 0, 2059, 0), -- Waistguard of the Great Beast
(18525, 0, 33584, 0, 0, 2049, 0), -- Pantaloons of Arcane Annihilation
(18525, 0, 33585, 0, 0, 2049, 0), -- Achromic Trousers of the Naaru
(18525, 0, 33586, 0, 0, 2059, 0), -- Studious Wraps
(18525, 0, 33587, 0, 0, 2059, 0), -- Light-Blessed Bonds
(18525, 0, 33588, 0, 0, 2060, 0), -- Runed Spell-cuffs
(18525, 0, 33589, 0, 0, 2060, 0), -- Wristguards of Tranquil Thought
(18525, 0, 33593, 0, 0, 2060, 0), -- Slikk's Cloak of Placation
(18525, 0, 33810, 0, 0, 2049, 0), -- Amani Mask of Death
(18525, 0, 33832, 0, 0, 2049, 0), -- Battlemaster's Determination
(18525, 0, 33965, 0, 0, 2049, 0), -- Hauberk of the Furious Elements
(18525, 0, 33970, 0, 0, 2059, 0), -- Pauldrons of the Furious Elements
(18525, 0, 33972, 0, 0, 2049, 0), -- Mask of Primal Power
(18525, 0, 33973, 0, 0, 2059, 0), -- Pauldrons of Tribal Fury
(18525, 0, 33974, 0, 0, 2059, 0), -- Grasp of the Moonkin
(18525, 0, 34049, 0, 0, 2049, 0), -- Battlemaster's Audacity
(18525, 0, 34050, 0, 0, 2049, 0), -- Battlemaster's Perseverance
(18525, 0, 34162, 0, 0, 2049, 0), -- Battlemaster's Depravity
(18525, 0, 34163, 0, 0, 2049, 0), -- Battlemaster's Cruelty
(18525, 0, 35321, 0, 0, 2059, 0), -- Cloak of Arcane Alacrity
(18525, 0, 35324, 0, 0, 2059, 0), -- Cloak of Swift Reprieve
(18525, 0, 35326, 0, 0, 2049, 0); -- Battlemaster's Alacrity

-- Dalinna <Master Tailoring Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 18749 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18749, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Zebig <Master Engineering Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 18752 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18752, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(18752, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(18752, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Barim Spilthoof <Master Leatherworking Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 18754 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18754, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Brumman <Master Leatherworking Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 18771 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18771, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Hama <Master Tailoring Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 18772 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18772, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Lebowski <Master Engineering Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 18775 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18775, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(18775, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(18775, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Alchemist Gribble <Master Alchemy Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 18802 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18802, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Innkeeper Coryth Stoktron <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 18907 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18907, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Rungor <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 18960 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18960, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Lursa Sunfallow <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 18998 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(18998, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Vodesiin <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 19004 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19004, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Vanteg <Reagents & Poison Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 19013 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19013, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Ogir <Reagents & Poison Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 19014 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19014, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Mathar G'ochar <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 19015 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19015, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Borto <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 19017 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19017, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Leeli Longhaggle <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 19042 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19042, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Skreah <Alchemy Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 19074 AND `item` IN (40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19074, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Ernie Packwell <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 19194 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19194, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Cro Threadstrong <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 19196 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19196, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Eral <General Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 19197 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19197, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Eiin <Specialty Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 19213 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19213, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Innkeeper Haelthol <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 19232 AND `item` IN (27857);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19232, 0, 27857, 0, 0, 0, 0); -- Garadar Sharp

-- Amshesha Stilldark <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 19235 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19235, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Innkeeper Biribi <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 19296 AND `item` IN (27857);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19296, 0, 27857, 0, 0, 0, 0); -- Garadar Sharp

-- Kalara <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 19345 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19345, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Oran Blusterbrew <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 19372 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19372, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Captured Gnome <Item Repair>
DELETE FROM `npc_vendor` WHERE `entry` = 19383 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19383, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(19383, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(19383, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Pol Snowhoof <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 19450 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19450, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Caoileann <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 19497 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19497, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Arrond <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 19521 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19521, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Dearny <Leatherworking Merchant>
DELETE FROM `npc_vendor` WHERE `entry` = 19532 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19532, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Dealer Aljaan <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 19533 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19533, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Dealer Zijaad <Arcane Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 19535 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19535, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Peon Bolgar <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 19562 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19562, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Dash <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 19573 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19573, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Qiff <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 19575 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19575, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Viggz Shinesparked <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 19661 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19661, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Fantei <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 19678 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19678, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- "Slim" <Shady Dealer>
DELETE FROM `npc_vendor` WHERE `entry` = 19679 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19679, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Provisioner Tsaalt
DELETE FROM `npc_vendor` WHERE `entry` = 19718 AND `item` IN (27857, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19718, 0, 27857, 0, 0, 0, 0), -- Garadar Sharp
(19718, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Muheru the Weaver <Tailoring Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 19722 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19722, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Daga Ramba <Potions>
DELETE FROM `npc_vendor` WHERE `entry` = 19837 AND `item` IN (40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(19837, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Galgrom <Provisioner>
DELETE FROM `npc_vendor` WHERE `entry` = 20080 AND `item` IN (27857, 28399);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(20080, 0, 27857, 0, 0, 0, 0), -- Garadar Sharp
(20080, 0, 28399, 0, 0, 0, 0); -- Filtered Draenic Water

-- Bortega <Reagents & Poison Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 20081 AND `item` IN (10648, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(20081, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(20081, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Dealer Hazzin <General Provisioner>
DELETE FROM `npc_vendor` WHERE `entry` = 20092 AND `item` IN (10648, 37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(20092, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(20092, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Dealer Dunar <General Provisioner>
DELETE FROM `npc_vendor` WHERE `entry` = 20194 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(20194, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Rashere Pridehoof <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 20250 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(20250, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Siflaed Coldhammer <Tinker>
DELETE FROM `npc_vendor` WHERE `entry` = 20890 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(20890, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(20890, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(20890, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Skraa <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 20891 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(20891, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Noko Moonwhisper <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 20915 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(20915, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Xerintha Ravenoak <Food & Drink>
DELETE FROM `npc_vendor` WHERE `entry` = 20916 AND `item` IN (27857);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(20916, 0, 27857, 0, 0, 0, 0); -- Garadar Sharp

-- Dealer Sadaqat <Potent Potables>
DELETE FROM `npc_vendor` WHERE `entry` = 20989 AND `item` IN (40411);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(20989, 0, 40411, 0, 0, 0, 0); -- Enchanted Vial

-- Erool <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 21083 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(21083, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Ragar <Leatherworking Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 21085 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(21085, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Fizit "Doc" Clocktock <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 21110 AND `item` IN (27857);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(21110, 0, 27857, 0, 0, 0, 0); -- Garadar Sharp

-- Bossi Pentapiston <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 21112 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(21112, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Sassa Weldwell <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 21113 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(21113, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Roldemar <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 21744 AND `item` IN (27857);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(21744, 0, 27857, 0, 0, 0, 0); -- Garadar Sharp

-- Caretaker Aluuro <Innkeeper>
DELETE FROM `npc_vendor` WHERE `entry` = 21746 AND `item` IN (27857);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(21746, 0, 27857, 0, 0, 0, 0); -- Garadar Sharp

-- Wyrmcult Provisioner
DELETE FROM `npc_vendor` WHERE `entry` = 22099 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(22099, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Ogri'la Grubgiver <Food Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 22266 AND `item` IN (27857);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(22266, 0, 27857, 0, 0, 0, 0); -- Garadar Sharp

-- Ogri'la Trader <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 22271 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(22271, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Sab'aoth <Reagents & Poison Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 22479 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(22479, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Mingo <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 23112 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(23112, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Rumpus <Reagents & Poison Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 23145 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(23145, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Sahaak <Keeper of Scrolls>
DELETE FROM `npc_vendor` WHERE `entry` = 23363 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(23363, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Mortog Steamhead
DELETE FROM `npc_vendor` WHERE `entry` = 23373 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(23373, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Anne Summers <Cheese Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 23521 AND `item` IN (27857);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(23521, 0, 27857, 0, 0, 0, 0); -- Garadar Sharp

-- Arlen Lochlan <Bread Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 23522 AND `item` IN (27855);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(23522, 0, 27855, 0, 0, 0, 45613); -- Mag'har Grainbread

-- Provisioner Ameenah <Reagents>
DELETE FROM `npc_vendor` WHERE `entry` = 23560 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(23560, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Uta Roughdough <Bread Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 23603 AND `item` IN (27855);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(23603, 0, 27855, 0, 0, 0, 45613); -- Mag'har Grainbread

-- Agnes Farwithers <Cheese Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 23604 AND `item` IN (27857);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(23604, 0, 27857, 0, 0, 0, 45613); -- Garadar Sharp

-- Tradesman Portanuus <Trade Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 25034 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(25034, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Kaalif <Reagent Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 25039 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(25039, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Technician Halmaha <Engineering Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 27711 AND `item` IN (10648, 39684, 40533);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(27711, 0, 10648, 0, 0, 0, 0), -- Common Parchment
(27711, 0, 39684, 0, 0, 0, 0), -- Hair Trigger
(27711, 0, 40533, 0, 0, 0, 0); -- Walnut Stock

-- Tiffany Cartier <Jewelcrafting Supplies>
DELETE FROM `npc_vendor` WHERE `entry` = 28721 AND `item` IN (43597);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(28721, 0, 43597, 0, 0, 2558, 0); -- Design: Titanium Frostguard Ring

-- Paldesse <Cloth Armor Merchant>
DELETE FROM `npc_vendor` WHERE `entry` = 28995 AND `item` IN (39491, 39492, 39493, 39494, 39495, 39496, 39497, 39498);
DELETE FROM `npc_vendor` WHERE `entry` = 28995 AND `item` IN (39499, 39500, 39514, 39515, 39517, 39518, 39519, 39521);
DELETE FROM `npc_vendor` WHERE `entry` = 28995 AND `item` IN (39523, 39528, 39529, 39530, 40415, 40416, 40417, 40418);
DELETE FROM `npc_vendor` WHERE `entry` = 28995 AND `item` IN (40419, 40420, 40421, 40422, 40423, 40424, 40445, 40447);
DELETE FROM `npc_vendor` WHERE `entry` = 28995 AND `item` IN (40448, 40449, 40450, 40454, 40456, 40457, 40458, 40459);
DELETE FROM `npc_vendor` WHERE `entry` = 28995 AND `item` IN (40696, 40697, 40740, 40750, 40751, 45365, 45367, 45368);
DELETE FROM `npc_vendor` WHERE `entry` = 28995 AND `item` IN (45369, 45386, 45387, 45388, 45389, 45390, 45391, 45392);
DELETE FROM `npc_vendor` WHERE `entry` = 28995 AND `item` IN (45393, 45394, 45395, 45417, 45419, 45420, 45421, 45422);
DELETE FROM `npc_vendor` WHERE `entry` = 28995 AND `item` IN (45831, 45840, 45848, 46129, 46130, 46131, 46132, 46133);
DELETE FROM `npc_vendor` WHERE `entry` = 28995 AND `item` IN (46134, 46135, 46136, 46137, 46139, 46140, 46163, 46165);
DELETE FROM `npc_vendor` WHERE `entry` = 28995 AND `item` IN (46168, 46170, 46172, 46188, 46190, 46193, 46195, 46197);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(28995, 0, 39491, 0, 0, 2487, 0), -- Heroes' Frostfire Circlet
(28995, 0, 39492, 0, 0, 2485, 0), -- Heroes' Frostfire Robe
(28995, 0, 39493, 0, 0, 2488, 0), -- Heroes' Frostfire Leggings
(28995, 0, 39494, 0, 0, 2489, 0), -- Heroes' Frostfire Shoulderpads
(28995, 0, 39495, 0, 0, 2486, 0), -- Heroes' Frostfire Gloves
(28995, 0, 39496, 0, 0, 2490, 0), -- Heroes' Plagueheart Circlet
(28995, 0, 39497, 0, 0, 2491, 0), -- Heroes' Plagueheart Robe
(28995, 0, 39498, 0, 0, 2492, 0), -- Heroes' Plagueheart Leggings
(28995, 0, 39499, 0, 0, 2493, 0), -- Heroes' Plagueheart Shoulderpads
(28995, 0, 39500, 0, 0, 2494, 0), -- Heroes' Plagueheart Gloves
(28995, 0, 39514, 0, 0, 2490, 0), -- Heroes' Crown of Faith
(28995, 0, 39515, 0, 0, 2491, 0), -- Heroes' Robe of Faith
(28995, 0, 39517, 0, 0, 2492, 0), -- Heroes' Leggings of Faith
(28995, 0, 39518, 0, 0, 2493, 0), -- Heroes' Shoulderpads of Faith
(28995, 0, 39519, 0, 0, 2494, 0), -- Heroes' Gloves of Faith
(28995, 0, 39521, 0, 0, 2490, 0), -- Heroes' Circlet of Faith
(28995, 0, 39523, 0, 0, 2491, 0), -- Heroes' Raiments of Faith
(28995, 0, 39528, 0, 0, 2492, 0), -- Heroes' Pants of Faith
(28995, 0, 39529, 0, 0, 2493, 0), -- Heroes' Mantle of Faith
(28995, 0, 39530, 0, 0, 2494, 0), -- Heroes' Handwraps of Faith
(28995, 0, 40415, 0, 0, 2515, 0), -- Valorous Frostfire Gloves
(28995, 0, 40416, 0, 0, 2514, 0), -- Valorous Frostfire Circlet
(28995, 0, 40417, 0, 0, 2516, 0), -- Valorous Frostfire Leggings
(28995, 0, 40418, 0, 0, 2513, 0), -- Valorous Frostfire Robe
(28995, 0, 40419, 0, 0, 2517, 0), -- Valorous Frostfire Shoulderpads
(28995, 0, 40420, 0, 0, 2503, 0), -- Valorous Plagueheart Gloves
(28995, 0, 40421, 0, 0, 2505, 0), -- Valorous Plagueheart Circlet
(28995, 0, 40422, 0, 0, 2506, 0), -- Valorous Plagueheart Leggings
(28995, 0, 40423, 0, 0, 2504, 0), -- Valorous Plagueheart Robe
(28995, 0, 40424, 0, 0, 2507, 0), -- Valorous Plagueheart Shoulderpads
(28995, 0, 40445, 0, 0, 2503, 0), -- Valorous Gloves of Faith
(28995, 0, 40447, 0, 0, 2505, 0), -- Valorous Crown of Faith
(28995, 0, 40448, 0, 0, 2506, 0), -- Valorous Leggings of Faith
(28995, 0, 40449, 0, 0, 2504, 0), -- Valorous Robe of Faith
(28995, 0, 40450, 0, 0, 2507, 0), -- Valorous Shoulderpads of Faith
(28995, 0, 40454, 0, 0, 2503, 0), -- Valorous Handwraps of Faith
(28995, 0, 40456, 0, 0, 2505, 0), -- Valorous Circlet of Faith
(28995, 0, 40457, 0, 0, 2506, 0), -- Valorous Pants of Faith
(28995, 0, 40458, 0, 0, 2504, 0), -- Valorous Raiments of Faith
(28995, 0, 40459, 0, 0, 2507, 0), -- Valorous Mantle of Faith
(28995, 0, 40696, 0, 0, 2524, 0), -- Plush Sash of Guzbah
(28995, 0, 40697, 0, 0, 2524, 0), -- Elegant Temple Gardens' Girdle
(28995, 0, 40740, 0, 0, 2537, 0), -- Wraps of the Astral Traveler
(28995, 0, 40750, 0, 0, 2536, 0), -- Xintor's Expeditionary Boots
(28995, 0, 40751, 0, 0, 2536, 0), -- Slippers of the Holy Light
(28995, 0, 45365, 0, 0, 2668, 0), -- Valorous Kirin Tor Hood
(28995, 0, 45367, 0, 0, 2664, 0), -- Valorous Kirin Tor Leggings
(28995, 0, 45368, 0, 0, 2666, 0), -- Valorous Kirin Tor Tunic
(28995, 0, 45369, 0, 0, 2662, 0), -- Valorous Kirin Tor Shoulderpads
(28995, 0, 45386, 0, 0, 2648, 0), -- Valorous Cowl of Sanctification
(28995, 0, 45387, 0, 0, 2640, 0), -- Valorous Gloves of Sanctification
(28995, 0, 45388, 0, 0, 2644, 0), -- Valorous Leggings of Sanctification
(28995, 0, 45389, 0, 0, 2646, 0), -- Valorous Robe of Sanctification
(28995, 0, 45390, 0, 0, 2642, 0), -- Valorous Shoulderpads of Sanctification
(28995, 0, 45391, 0, 0, 2648, 0), -- Valorous Circlet of Sanctification
(28995, 0, 45392, 0, 0, 2640, 0), -- Valorous Handwraps of Sanctification
(28995, 0, 45393, 0, 0, 2642, 0), -- Valorous Mantle of Sanctification
(28995, 0, 45394, 0, 0, 2644, 0), -- Valorous Pants of Sanctification
(28995, 0, 45395, 0, 0, 2646, 0), -- Valorous Raiments of Sanctification
(28995, 0, 45417, 0, 0, 2648, 0), -- Valorous Deathbringer Hood
(28995, 0, 45419, 0, 0, 2640, 0), -- Valorous Deathbringer Gloves
(28995, 0, 45420, 0, 0, 2644, 0), -- Valorous Deathbringer Leggings
(28995, 0, 45421, 0, 0, 2646, 0), -- Valorous Deathbringer Robe
(28995, 0, 45422, 0, 0, 2642, 0), -- Valorous Deathbringer Shoulderpads
(28995, 0, 45831, 0, 0, 2607, 0), -- Sash of Potent Incantations
(28995, 0, 45840, 0, 0, 2607, 0), -- Touch of the Occult
(28995, 0, 45848, 0, 0, 2630, 0), -- Legwraps of the Master Conjurer
(28995, 0, 46129, 0, 0, 2669, 0), -- Conqueror's Kirin Tor Hood
(28995, 0, 46130, 0, 0, 2667, 0), -- Conqueror's Kirin Tor Tunic
(28995, 0, 46131, 0, 0, 2660, 0), -- Valorous Kirin Tor Gauntlets
(28995, 0, 46132, 0, 0, 2661, 0), -- Conqueror's Kirin Tor Gauntlets
(28995, 0, 46133, 0, 0, 2665, 0), -- Conqueror's Kirin Tor Leggings
(28995, 0, 46134, 0, 0, 2663, 0), -- Conqueror's Kirin Tor Shoulderpads
(28995, 0, 46135, 0, 0, 2641, 0), -- Conqueror's Deathbringer Gloves
(28995, 0, 46136, 0, 0, 2643, 0), -- Conqueror's Deathbringer Shoulderpads
(28995, 0, 46137, 0, 0, 2647, 0), -- Conqueror's Deathbringer Robe
(28995, 0, 46139, 0, 0, 2645, 0), -- Conqueror's Deathbringer Leggings
(28995, 0, 46140, 0, 0, 2649, 0), -- Conqueror's Deathbringer Hood
(28995, 0, 46163, 0, 0, 2641, 0), -- Conqueror's Handwraps of Sanctification
(28995, 0, 46165, 0, 0, 2643, 0), -- Conqueror's Mantle of Sanctification
(28995, 0, 46168, 0, 0, 2647, 0), -- Conqueror's Raiments of Sanctification
(28995, 0, 46170, 0, 0, 2645, 0), -- Conqueror's Pants of Sanctification
(28995, 0, 46172, 0, 0, 2649, 0), -- Conqueror's Circlet of Sanctification
(28995, 0, 46188, 0, 0, 2641, 0), -- Conqueror's Gloves of Sanctification
(28995, 0, 46190, 0, 0, 2643, 0), -- Conqueror's Shoulderpads of Sanctification
(28995, 0, 46193, 0, 0, 2647, 0), -- Conqueror's Robe of Sanctification
(28995, 0, 46195, 0, 0, 2645, 0), -- Conqueror's Leggings of Sanctification
(28995, 0, 46197, 0, 0, 2649, 0); -- Conqueror's Cowl of Sanctification

-- Fester <Trade Goods>
DELETE FROM `npc_vendor` WHERE `entry` = 29208 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(29208, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Norvin Alderman <Cloaks>
DELETE FROM `npc_vendor` WHERE `entry` = 29495 AND `item` IN (40721, 40722, 40723, 40724);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(29495, 0, 40721, 0, 0, 2534, 0), -- Hammerhead Sharkskin Cloak
(29495, 0, 40722, 0, 0, 2534, 0), -- Platinum Mesh Cloak
(29495, 0, 40723, 0, 0, 2534, 0), -- Disguise of the Kumiho
(29495, 0, 40724, 0, 0, 2534, 0); -- Cloak of Kea Feathers

-- Ninsianna <Relics>
DELETE FROM `npc_vendor` WHERE `entry` = 29529 AND `item` IN (39728, 39757, 40191, 40207, 40267, 40268, 40321, 40322);
DELETE FROM `npc_vendor` WHERE `entry` = 29529 AND `item` IN (40337, 40342);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(29529, 0, 39728, 0, 0, 2534, 0), -- Totem of Misery
(29529, 0, 39757, 0, 0, 2534, 0), -- Idol of Worship
(29529, 0, 40191, 0, 0, 2534, 0), -- Libram of Radiance
(29529, 0, 40207, 0, 0, 2534, 0), -- Sigil of Awareness
(29529, 0, 40267, 0, 0, 2534, 0), -- Totem of Hex
(29529, 0, 40268, 0, 0, 2534, 0), -- Libram of Tolerance
(29529, 0, 40321, 0, 0, 2534, 0), -- Idol of the Shooting Star
(29529, 0, 40322, 0, 0, 2534, 0), -- Totem of Dueling
(29529, 0, 40337, 0, 0, 2534, 0), -- Libram of Resurgence
(29529, 0, 40342, 0, 0, 2534, 0); -- Idol of Awakening

-- Sheddle Glossgleam <Cobbler>
DELETE FROM `npc_vendor` WHERE `entry` = 29703 AND `item` IN (40742, 40743, 40745, 40746, 40747, 40748, 40749, 40750);
DELETE FROM `npc_vendor` WHERE `entry` = 29703 AND `item` IN (40751);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(29703, 0, 40742, 0, 0, 2536, 0), -- Bladed Steelboots
(29703, 0, 40743, 0, 0, 2536, 0), -- Kyzoc's Ground Stompers
(29703, 0, 40745, 0, 0, 2536, 0), -- Sabatons of Rapid Recovery
(29703, 0, 40746, 0, 0, 2536, 0), -- Pack-Ice Striders
(29703, 0, 40747, 0, 0, 2536, 0), -- Treads of Coastal Wandering
(29703, 0, 40748, 0, 0, 2536, 0), -- Boots of Captain Ellis
(29703, 0, 40749, 0, 0, 2536, 0), -- Rainey's Chewed Boots
(29703, 0, 40750, 0, 0, 2536, 0), -- Xintor's Expeditionary Boots
(29703, 0, 40751, 0, 0, 2536, 0); -- Slippers of the Holy Light

-- Harold Winston <Jewelry Vendor>
DELETE FROM `npc_vendor` WHERE `entry` = 32172 AND `item` IN (40585, 40586, 40717, 40718, 40719, 40720, 44934, 44935);
DELETE FROM `npc_vendor` WHERE `entry` = 32172 AND `item` IN (45688, 45689, 45690, 45691, 45819, 45820, 45821, 45822);
DELETE FROM `npc_vendor` WHERE `entry` = 32172 AND `item` IN (45823, 47729, 47730, 47731, 47732, 47733, 48954, 48955);
DELETE FROM `npc_vendor` WHERE `entry` = 32172 AND `item` IN (48956, 48957, 51557, 51558, 51559, 51560);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(32172, 0, 40585, 0, 0, 0, 0), -- Signet of the Kirin Tor
(32172, 0, 40586, 0, 0, 0, 0), -- Band of the Kirin Tor
(32172, 0, 40717, 0, 0, 2534, 0), -- Ring of Invincibility
(32172, 0, 40718, 0, 0, 2534, 0), -- Signet of the Impregnable Fortress
(32172, 0, 40719, 0, 0, 2534, 0), -- Band of Channeled Magic
(32172, 0, 40720, 0, 0, 2534, 0), -- Renewal of Life
(32172, 0, 44934, 0, 0, 0, 0), -- Loop of the Kirin Tor
(32172, 0, 44935, 0, 0, 0, 0), -- Ring of the Kirin Tor
(32172, 0, 45688, 0, 0, 2592, 0), -- Inscribed Band of the Kirin Tor
(32172, 0, 45689, 0, 0, 2593, 0), -- Inscribed Loop of the Kirin Tor
(32172, 0, 45690, 0, 0, 2594, 0), -- Inscribed Ring of the Kirin Tor
(32172, 0, 45691, 0, 0, 2595, 0), -- Inscribed Signet of the Kirin Tor
(32172, 0, 45819, 0, 0, 2606, 0), -- Spiked Battleguard Choker
(32172, 0, 45820, 0, 0, 2606, 0), -- Broach of the Wailing Night
(32172, 0, 45821, 0, 0, 2606, 0), -- Shard of the Crystal Forest
(32172, 0, 45822, 0, 0, 2606, 0), -- Evoker's Charm
(32172, 0, 45823, 0, 0, 2606, 0), -- Frozen Tear of Elune
(32172, 0, 47729, 0, 0, 2685, 0), -- Bloodshed Band
(32172, 0, 47730, 0, 0, 2685, 0), -- Dexterous Brightstone Ring
(32172, 0, 47731, 0, 0, 2685, 0), -- Clutch of Fortification
(32172, 0, 47732, 0, 0, 2685, 0), -- Band of the Invoker
(32172, 0, 47733, 0, 0, 2685, 0), -- Heartmender Circle
(32172, 0, 48954, 0, 0, 2702, 0), -- Etched Band of the Kirin Tor
(32172, 0, 48955, 0, 0, 2703, 0), -- Etched Loop of the Kirin Tor
(32172, 0, 48956, 0, 0, 2704, 0), -- Etched Ring of the Kirin Tor
(32172, 0, 48957, 0, 0, 2705, 0), -- Etched Signet of the Kirin Tor
(32172, 0, 51557, 0, 0, 2735, 0), -- Runed Signet of the Kirin Tor
(32172, 0, 51558, 0, 0, 2737, 0), -- Runed Loop of the Kirin Tor
(32172, 0, 51559, 0, 0, 2736, 0), -- Runed Ring of the Kirin Tor
(32172, 0, 51560, 0, 0, 2738, 0); -- Runed Band of the Kirin Tor

-- Knight Dameron <Wintergrasp Quartermaster>
DELETE FROM `npc_vendor` WHERE `entry` = 32294 AND `item` IN (44891, 44892, 44893, 44894, 44895, 44896, 44897, 44898);
DELETE FROM `npc_vendor` WHERE `entry` = 32294 AND `item` IN (44899, 44900, 44901, 44902, 44903, 44904, 44905, 44906);
DELETE FROM `npc_vendor` WHERE `entry` = 32294 AND `item` IN (44907, 44908, 44909, 44910, 44912, 44914, 46057, 46058);
DELETE FROM `npc_vendor` WHERE `entry` = 32294 AND `item` IN (46059, 46060, 46061, 46062, 46063, 46064, 46065, 46066);
DELETE FROM `npc_vendor` WHERE `entry` = 32294 AND `item` IN (46071, 46072, 46073, 46074, 46075, 46076, 46077, 46078);
DELETE FROM `npc_vendor` WHERE `entry` = 32294 AND `item` IN (46079, 46080, 46081, 46082, 46083, 46084, 46085, 46086);
DELETE FROM `npc_vendor` WHERE `entry` = 32294 AND `item` IN (46087, 46088, 48974, 48975, 48976, 48977, 48978, 48979);
DELETE FROM `npc_vendor` WHERE `entry` = 32294 AND `item` IN (48980, 48981, 48982, 48983, 48987, 48988, 48990, 48991);
DELETE FROM `npc_vendor` WHERE `entry` = 32294 AND `item` IN (48992, 48993, 48994, 48997, 48998, 48999, 49000);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(32294, 0, 44891, 0, 0, 2577, 0), -- Titan-Forged Boots of Dominance
(32294, 0, 44892, 0, 0, 2577, 0), -- Titan-Forged Boots of Salvation
(32294, 0, 44893, 0, 0, 2577, 0), -- Titan-Forged Boots of Triumph
(32294, 0, 44894, 0, 0, 2577, 0), -- Titan-Forged Greaves of Salvation
(32294, 0, 44895, 0, 0, 2577, 0), -- Titan-Forged Greaves of Triumph
(32294, 0, 44896, 0, 0, 2577, 0), -- Titan-Forged Sabatons of Dominance
(32294, 0, 44897, 0, 0, 2577, 0), -- Titan-Forged Sabatons of Salvation
(32294, 0, 44898, 0, 0, 2577, 0), -- Titan-Forged Sabatons of Triumph
(32294, 0, 44899, 0, 0, 2577, 0), -- Titan-Forged Slippers of Dominance
(32294, 0, 44900, 0, 0, 2577, 0), -- Titan-Forged Slippers of Salvation
(32294, 0, 44901, 0, 0, 2579, 0), -- Titan-Forged Plate Headcover of Salvation
(32294, 0, 44902, 0, 0, 2579, 0), -- Titan-Forged Plate Helm of Triumph
(32294, 0, 44903, 0, 0, 2579, 0), -- Titan-Forged Chain Helm of Triumph
(32294, 0, 44904, 0, 0, 2579, 0), -- Titan-Forged Mail Helm of Dominance
(32294, 0, 44905, 0, 0, 2579, 0), -- Titan-Forged Ringmail Helm of Salvation
(32294, 0, 44906, 0, 0, 2579, 0), -- Titan-Forged Leather Helm of Salvation
(32294, 0, 44907, 0, 0, 2579, 0), -- Titan-Forged Leather Helm of Dominance
(32294, 0, 44908, 0, 0, 2579, 0), -- Titan-Forged Leather Helm of Triumph
(32294, 0, 44909, 0, 0, 2579, 0), -- Titan-Forged Hood of Salvation
(32294, 0, 44910, 0, 0, 2579, 0), -- Titan-Forged Hood of Dominance
(32294, 0, 44912, 0, 0, 2578, 0), -- Flow of Knowledge
(32294, 0, 44914, 0, 0, 2578, 0), -- Anvil of Titans
(32294, 0, 46057, 0, 0, 2579, 0), -- Titan-Forged Chestguard of Salvation
(32294, 0, 46058, 0, 0, 2579, 0), -- Titan-Forged Breastplate of Triumph
(32294, 0, 46059, 0, 0, 2579, 0), -- Titan-Forged Chain Armor of Triumph
(32294, 0, 46060, 0, 0, 2579, 0), -- Titan-Forged Ringmail of Salvation
(32294, 0, 46061, 0, 0, 2579, 0), -- Titan-Forged Mail Armor of Domination
(32294, 0, 46062, 0, 0, 2579, 0), -- Titan-Forged Leather Tunic of Triumph
(32294, 0, 46063, 0, 0, 2579, 0), -- Titan-Forged Leather Chestguard of Salvation
(32294, 0, 46064, 0, 0, 2579, 0), -- Titan-Forged Leather Chestguard of Dominance
(32294, 0, 46065, 0, 0, 2579, 0), -- Titan-Forged Raiment of Dominance
(32294, 0, 46066, 0, 0, 2579, 0), -- Titan-Forged Raiment of Salvation
(32294, 0, 46071, 0, 0, 2577, 0), -- Titan-Forged Girdle of Salvation
(32294, 0, 46072, 0, 0, 2577, 0), -- Titan-Forged Girdle of Triumph
(32294, 0, 46073, 0, 0, 2577, 0), -- Titan-Forged Waistguard of Dominance
(32294, 0, 46074, 0, 0, 2577, 0), -- Titan-Forged Waistguard of Salvation
(32294, 0, 46075, 0, 0, 2577, 0), -- Titan-Forged Waistguard of Triumph
(32294, 0, 46076, 0, 0, 2577, 0), -- Titan-Forged Belt of Dominance
(32294, 0, 46077, 0, 0, 2577, 0), -- Titan-Forged Belt of Salvation
(32294, 0, 46078, 0, 0, 2577, 0), -- Titan-Forged Belt of Triumph
(32294, 0, 46079, 0, 0, 2577, 0), -- Titan-Forged Cord of Dominance
(32294, 0, 46080, 0, 0, 2577, 0), -- Titan-Forged Cord of Salvation
(32294, 0, 46081, 0, 0, 2578, 0), -- Titan-Forged Rune of Audacity
(32294, 0, 46082, 0, 0, 2578, 0), -- Titan-Forged Rune of Determination
(32294, 0, 46083, 0, 0, 2578, 0), -- Titan-Forged Rune of Accuracy
(32294, 0, 46084, 0, 0, 2578, 0), -- Titan-Forged Rune of Cruelty
(32294, 0, 46085, 0, 0, 2578, 0), -- Titan-Forged Rune of Alacrity
(32294, 0, 46086, 0, 0, 2578, 0), -- Platinum Disks of Battle
(32294, 0, 46087, 0, 0, 2578, 0), -- Platinum Disks of Sorcery
(32294, 0, 46088, 0, 0, 2578, 0), -- Platinum Disks of Swiftness
(32294, 0, 48974, 0, 0, 2577, 0), -- Titan-Forged Armwraps of Dominance
(32294, 0, 48975, 0, 0, 2577, 0), -- Titan-Forged Armwraps of Salvation
(32294, 0, 48976, 0, 0, 2577, 0), -- Titan-Forged Armwraps of Triumph
(32294, 0, 48977, 0, 0, 2577, 0), -- Titan-Forged Bracers of Salvation
(32294, 0, 48978, 0, 0, 2577, 0), -- Titan-Forged Bracers of Triumph
(32294, 0, 48979, 0, 0, 2577, 0), -- Titan-Forged Cuffs of Salvation
(32294, 0, 48980, 0, 0, 2577, 0), -- Titan-Forged Wristguards of Dominance
(32294, 0, 48981, 0, 0, 2577, 0), -- Titan-Forged Wristguards of Salvation
(32294, 0, 48982, 0, 0, 2577, 0), -- Titan-Forged Wristguards of Triumph
(32294, 0, 48983, 0, 0, 2579, 0), -- Titan-Forged Chain Leggings of Triumph
(32294, 0, 48987, 0, 0, 2579, 0), -- Titan-Forged Leather Legguards of Salvation
(32294, 0, 48988, 0, 0, 2579, 0), -- Titan-Forged Leather Legguards of Triumph
(32294, 0, 48990, 0, 0, 2579, 0), -- Titan-Forged Mail Leggings of Dominance
(32294, 0, 48991, 0, 0, 2579, 0), -- Titan-Forged Cloth Leggings of Salvation
(32294, 0, 48992, 0, 0, 2579, 0), -- Titan-Forged Plate Legguards of Salvation
(32294, 0, 48993, 0, 0, 2579, 0), -- Titan-Forged Plate Legguards of Triumph
(32294, 0, 48994, 0, 0, 2579, 0), -- Titan-Forged Ringmail Leggings of Salvation
(32294, 0, 48997, 0, 0, 2579, 0), -- Titan-Forged Cloth Trousers of Domination
(32294, 0, 48998, 0, 0, 2579, 0), -- Titan-Forged Leather Legguards of Dominance
(32294, 0, 48999, 0, 0, 2577, 0), -- Titan-Forged Band of Ascendancy
(32294, 0, 49000, 0, 0, 2577, 0); -- Titan-Forged Band of Victory

-- Stone Guard Mukar <Wintergrasp Quartermaster>
DELETE FROM `npc_vendor` WHERE `entry` = 32296 AND `item` IN (44891, 44892, 44893, 44894, 44895, 44896, 44897, 44898);
DELETE FROM `npc_vendor` WHERE `entry` = 32296 AND `item` IN (44899, 44900, 44901, 44902, 44903, 44904, 44905, 44906);
DELETE FROM `npc_vendor` WHERE `entry` = 32296 AND `item` IN (44907, 44908, 44909, 44910, 44912, 44914, 46057, 46058);
DELETE FROM `npc_vendor` WHERE `entry` = 32296 AND `item` IN (46059, 46060, 46061, 46062, 46063, 46064, 46065, 46066);
DELETE FROM `npc_vendor` WHERE `entry` = 32296 AND `item` IN (46071, 46072, 46073, 46074, 46075, 46076, 46077, 46078);
DELETE FROM `npc_vendor` WHERE `entry` = 32296 AND `item` IN (46079, 46080, 46081, 46082, 46083, 46084, 46085, 46086);
DELETE FROM `npc_vendor` WHERE `entry` = 32296 AND `item` IN (46087, 46088, 48974, 48975, 48976, 48977, 48978, 48979);
DELETE FROM `npc_vendor` WHERE `entry` = 32296 AND `item` IN (48980, 48981, 48982, 48983, 48987, 48988, 48990, 48991);
DELETE FROM `npc_vendor` WHERE `entry` = 32296 AND `item` IN (48992, 48993, 48994, 48997, 48998, 48999, 49000);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(32296, 0, 44891, 0, 0, 2577, 0), -- Titan-Forged Boots of Dominance
(32296, 0, 44892, 0, 0, 2577, 0), -- Titan-Forged Boots of Salvation
(32296, 0, 44893, 0, 0, 2577, 0), -- Titan-Forged Boots of Triumph
(32296, 0, 44894, 0, 0, 2577, 0), -- Titan-Forged Greaves of Salvation
(32296, 0, 44895, 0, 0, 2577, 0), -- Titan-Forged Greaves of Triumph
(32296, 0, 44896, 0, 0, 2577, 0), -- Titan-Forged Sabatons of Dominance
(32296, 0, 44897, 0, 0, 2577, 0), -- Titan-Forged Sabatons of Salvation
(32296, 0, 44898, 0, 0, 2577, 0), -- Titan-Forged Sabatons of Triumph
(32296, 0, 44899, 0, 0, 2577, 0), -- Titan-Forged Slippers of Dominance
(32296, 0, 44900, 0, 0, 2577, 0), -- Titan-Forged Slippers of Salvation
(32296, 0, 44901, 0, 0, 2579, 0), -- Titan-Forged Plate Headcover of Salvation
(32296, 0, 44902, 0, 0, 2579, 0), -- Titan-Forged Plate Helm of Triumph
(32296, 0, 44903, 0, 0, 2579, 0), -- Titan-Forged Chain Helm of Triumph
(32296, 0, 44904, 0, 0, 2579, 0), -- Titan-Forged Mail Helm of Dominance
(32296, 0, 44905, 0, 0, 2579, 0), -- Titan-Forged Ringmail Helm of Salvation
(32296, 0, 44906, 0, 0, 2579, 0), -- Titan-Forged Leather Helm of Salvation
(32296, 0, 44907, 0, 0, 2579, 0), -- Titan-Forged Leather Helm of Dominance
(32296, 0, 44908, 0, 0, 2579, 0), -- Titan-Forged Leather Helm of Triumph
(32296, 0, 44909, 0, 0, 2579, 0), -- Titan-Forged Hood of Salvation
(32296, 0, 44910, 0, 0, 2579, 0), -- Titan-Forged Hood of Dominance
(32296, 0, 44912, 0, 0, 2578, 0), -- Flow of Knowledge
(32296, 0, 44914, 0, 0, 2578, 0), -- Anvil of Titans
(32296, 0, 46057, 0, 0, 2579, 0), -- Titan-Forged Chestguard of Salvation
(32296, 0, 46058, 0, 0, 2579, 0), -- Titan-Forged Breastplate of Triumph
(32296, 0, 46059, 0, 0, 2579, 0), -- Titan-Forged Chain Armor of Triumph
(32296, 0, 46060, 0, 0, 2579, 0), -- Titan-Forged Ringmail of Salvation
(32296, 0, 46061, 0, 0, 2579, 0), -- Titan-Forged Mail Armor of Domination
(32296, 0, 46062, 0, 0, 2579, 0), -- Titan-Forged Leather Tunic of Triumph
(32296, 0, 46063, 0, 0, 2579, 0), -- Titan-Forged Leather Chestguard of Salvation
(32296, 0, 46064, 0, 0, 2579, 0), -- Titan-Forged Leather Chestguard of Dominance
(32296, 0, 46065, 0, 0, 2579, 0), -- Titan-Forged Raiment of Dominance
(32296, 0, 46066, 0, 0, 2579, 0), -- Titan-Forged Raiment of Salvation
(32296, 0, 46071, 0, 0, 2577, 0), -- Titan-Forged Girdle of Salvation
(32296, 0, 46072, 0, 0, 2577, 0), -- Titan-Forged Girdle of Triumph
(32296, 0, 46073, 0, 0, 2577, 0), -- Titan-Forged Waistguard of Dominance
(32296, 0, 46074, 0, 0, 2577, 0), -- Titan-Forged Waistguard of Salvation
(32296, 0, 46075, 0, 0, 2577, 0), -- Titan-Forged Waistguard of Triumph
(32296, 0, 46076, 0, 0, 2577, 0), -- Titan-Forged Belt of Dominance
(32296, 0, 46077, 0, 0, 2577, 0), -- Titan-Forged Belt of Salvation
(32296, 0, 46078, 0, 0, 2577, 0), -- Titan-Forged Belt of Triumph
(32296, 0, 46079, 0, 0, 2577, 0), -- Titan-Forged Cord of Dominance
(32296, 0, 46080, 0, 0, 2577, 0), -- Titan-Forged Cord of Salvation
(32296, 0, 46081, 0, 0, 2578, 0), -- Titan-Forged Rune of Audacity
(32296, 0, 46082, 0, 0, 2578, 0), -- Titan-Forged Rune of Determination
(32296, 0, 46083, 0, 0, 2578, 0), -- Titan-Forged Rune of Accuracy
(32296, 0, 46084, 0, 0, 2578, 0), -- Titan-Forged Rune of Cruelty
(32296, 0, 46085, 0, 0, 2578, 0), -- Titan-Forged Rune of Alacrity
(32296, 0, 46086, 0, 0, 2578, 0), -- Platinum Disks of Battle
(32296, 0, 46087, 0, 0, 2578, 0), -- Platinum Disks of Sorcery
(32296, 0, 46088, 0, 0, 2578, 0), -- Platinum Disks of Swiftness
(32296, 0, 48974, 0, 0, 2577, 0), -- Titan-Forged Armwraps of Dominance
(32296, 0, 48975, 0, 0, 2577, 0), -- Titan-Forged Armwraps of Salvation
(32296, 0, 48976, 0, 0, 2577, 0), -- Titan-Forged Armwraps of Triumph
(32296, 0, 48977, 0, 0, 2577, 0), -- Titan-Forged Bracers of Salvation
(32296, 0, 48978, 0, 0, 2577, 0), -- Titan-Forged Bracers of Triumph
(32296, 0, 48979, 0, 0, 2577, 0), -- Titan-Forged Cuffs of Salvation
(32296, 0, 48980, 0, 0, 2577, 0), -- Titan-Forged Wristguards of Dominance
(32296, 0, 48981, 0, 0, 2577, 0), -- Titan-Forged Wristguards of Salvation
(32296, 0, 48982, 0, 0, 2577, 0), -- Titan-Forged Wristguards of Triumph
(32296, 0, 48983, 0, 0, 2579, 0), -- Titan-Forged Chain Leggings of Triumph
(32296, 0, 48987, 0, 0, 2579, 0), -- Titan-Forged Leather Legguards of Salvation
(32296, 0, 48988, 0, 0, 2579, 0), -- Titan-Forged Leather Legguards of Triumph
(32296, 0, 48990, 0, 0, 2579, 0), -- Titan-Forged Mail Leggings of Dominance
(32296, 0, 48991, 0, 0, 2579, 0), -- Titan-Forged Cloth Leggings of Salvation
(32296, 0, 48992, 0, 0, 2579, 0), -- Titan-Forged Plate Legguards of Salvation
(32296, 0, 48993, 0, 0, 2579, 0), -- Titan-Forged Plate Legguards of Triumph
(32296, 0, 48994, 0, 0, 2579, 0), -- Titan-Forged Ringmail Leggings of Salvation
(32296, 0, 48997, 0, 0, 2579, 0), -- Titan-Forged Cloth Trousers of Domination
(32296, 0, 48998, 0, 0, 2579, 0), -- Titan-Forged Leather Legguards of Dominance
(32296, 0, 48999, 0, 0, 2577, 0), -- Titan-Forged Band of Ascendancy
(32296, 0, 49000, 0, 0, 2577, 0); -- Titan-Forged Band of Victory

-- Aelthin <Master Alchemy Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 33630 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(33630, 0, 37201, 0, 0, 0, 53788); -- Corpse Dust

-- Enchantress Andiala <Master Enchanting Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 33633 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(33633, 0, 37201, 0, 0, 0, 53788); -- Corpse Dust

-- Engineer Sinbei <Master Engineering Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 33634 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(33634, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Daenril <Master Leatherworking Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 33635 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(33635, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Miralisse <Master Tailoring Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 33636 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(33636, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Alchemist Kanhu <Master Alchemy Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 33674 AND `item` IN (37201);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(33674, 0, 37201, 0, 0, 0, 0); -- Corpse Dust

-- Technician Mihila <Master Engineering Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 33677 AND `item` IN (10648);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(33677, 0, 10648, 0, 0, 0, 0); -- Common Parchment

-- Korim <Master Leatherworking Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 33681 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(33681, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Weaver Aoa <Master Tailoring Trainer>
DELETE FROM `npc_vendor` WHERE `entry` = 33684 AND `item` IN (38426);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(33684, 0, 38426, 0, 0, 0, 0); -- Eternium Thread

-- Rueben Lauren <Cloth Armor Merchant>
DELETE FROM `npc_vendor` WHERE `entry` = 35496 AND `item` IN (47748, 47749, 47750, 47751, 47752, 47773, 47774, 47775);
DELETE FROM `npc_vendor` WHERE `entry` = 35496 AND `item` IN (47776, 47777, 47783, 47784, 47785, 47786, 47787, 47798);
DELETE FROM `npc_vendor` WHERE `entry` = 35496 AND `item` IN (47799, 47800, 47801, 47802, 47914, 47936, 47980, 47981);
DELETE FROM `npc_vendor` WHERE `entry` = 35496 AND `item` IN (47982, 48067, 48068, 48069, 48070, 48071, 48072, 48073);
DELETE FROM `npc_vendor` WHERE `entry` = 35496 AND `item` IN (48074, 48075, 48076, 48097, 48098, 48099, 48100, 48101);
DELETE FROM `npc_vendor` WHERE `entry` = 35496 AND `item` IN (50240, 50241, 50242, 50243, 50244, 50275, 50276, 50277);
DELETE FROM `npc_vendor` WHERE `entry` = 35496 AND `item` IN (50278, 50279, 50391, 50392, 50393, 50394, 50396, 50765);
DELETE FROM `npc_vendor` WHERE `entry` = 35496 AND `item` IN (50766, 50767, 50768, 50769, 51155, 51156, 51157, 51158);
DELETE FROM `npc_vendor` WHERE `entry` = 35496 AND `item` IN (51159, 51175, 51176, 51177, 51178, 51179, 51180, 51181);
DELETE FROM `npc_vendor` WHERE `entry` = 35496 AND `item` IN (51182, 51183, 51184, 51205, 51206, 51207, 51208, 51209);
DELETE FROM `npc_vendor` WHERE `entry` = 35496 AND `item` IN (51230, 51231, 51232, 51233, 51234, 51255, 51256, 51257);
DELETE FROM `npc_vendor` WHERE `entry` = 35496 AND `item` IN (51258, 51259, 51260, 51261, 51262, 51263, 51264, 51280);
DELETE FROM `npc_vendor` WHERE `entry` = 35496 AND `item` IN (51281, 51282, 51283, 51284);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(35496, 0, 47748, 0, 0, 2686, 0), -- Khadgar's Hood of Conquest
(35496, 0, 47749, 0, 0, 2686, 0), -- Khadgar's Robe of Conquest
(35496, 0, 47750, 0, 0, 2686, 0), -- Khadgar's Leggings of Conquest
(35496, 0, 47751, 0, 0, 2687, 0), -- Khadgar's Shoulderpads of Conquest
(35496, 0, 47752, 0, 0, 2687, 0), -- Khadgar's Gauntlets of Conquest
(35496, 0, 47773, 0, 0, 2687, 0), -- Sunstrider's Gauntlets of Conquest
(35496, 0, 47774, 0, 0, 2686, 0), -- Sunstrider's Hood of Conquest
(35496, 0, 47775, 0, 0, 2686, 0), -- Sunstrider's Leggings of Conquest
(35496, 0, 47776, 0, 0, 2686, 0), -- Sunstrider's Robe of Conquest
(35496, 0, 47777, 0, 0, 2687, 0), -- Sunstrider's Shoulderpads of Conquest
(35496, 0, 47783, 0, 0, 2687, 0), -- Kel'Thuzad's Gloves of Conquest
(35496, 0, 47784, 0, 0, 2686, 0), -- Kel'Thuzad's Hood of Conquest
(35496, 0, 47785, 0, 0, 2686, 0), -- Kel'Thuzad's Leggings of Conquest
(35496, 0, 47786, 0, 0, 2686, 0), -- Kel'Thuzad's Robe of Conquest
(35496, 0, 47787, 0, 0, 2687, 0), -- Kel'Thuzad's Shoulderpads of Conquest
(35496, 0, 47798, 0, 0, 2687, 0), -- Gul'dan's Shoulderpads of Conquest
(35496, 0, 47799, 0, 0, 2686, 0), -- Gul'dan's Robe of Conquest
(35496, 0, 47800, 0, 0, 2686, 0), -- Gul'dan's Leggings of Conquest
(35496, 0, 47801, 0, 0, 2686, 0), -- Gul'dan's Hood of Conquest
(35496, 0, 47802, 0, 0, 2687, 0), -- Gul'dan's Gloves of Conquest
(35496, 0, 47914, 0, 0, 2686, 0), -- Velen's Cowl of Conquest
(35496, 0, 47936, 0, 0, 2686, 0), -- Velen's Robe of Conquest
(35496, 0, 47980, 0, 0, 2686, 0), -- Velen's Leggings of Conquest
(35496, 0, 47981, 0, 0, 2687, 0), -- Velen's Shoulderpads of Conquest
(35496, 0, 47982, 0, 0, 2687, 0), -- Velen's Gloves of Conquest
(35496, 0, 48067, 0, 0, 2687, 0), -- Zabra's Gloves of Conquest
(35496, 0, 48068, 0, 0, 2686, 0), -- Zabra's Cowl of Conquest
(35496, 0, 48069, 0, 0, 2686, 0), -- Zabra's Leggings of Conquest
(35496, 0, 48070, 0, 0, 2686, 0), -- Zabra's Robe of Conquest
(35496, 0, 48071, 0, 0, 2687, 0), -- Zabra's Shoulderpads of Conquest
(35496, 0, 48072, 0, 0, 2687, 0), -- Velen's Handwraps of Conquest
(35496, 0, 48073, 0, 0, 2686, 0), -- Velen's Circlet of Conquest
(35496, 0, 48074, 0, 0, 2686, 0), -- Velen's Pants of Conquest
(35496, 0, 48075, 0, 0, 2686, 0), -- Velen's Raiments of Conquest
(35496, 0, 48076, 0, 0, 2687, 0), -- Velen's Mantle of Conquest
(35496, 0, 48097, 0, 0, 2687, 0), -- Zabra's Handwraps of Conquest
(35496, 0, 48098, 0, 0, 2686, 0), -- Zabra's Circlet of Conquest
(35496, 0, 48099, 0, 0, 2686, 0), -- Zabra's Pants of Conquest
(35496, 0, 48100, 0, 0, 2686, 0), -- Zabra's Raiments of Conquest
(35496, 0, 48101, 0, 0, 2687, 0), -- Zabra's Mantle of Conquest
(35496, 0, 50240, 0, 0, 2740, 0), -- Dark Coven Gloves
(35496, 0, 50241, 0, 0, 2742, 0), -- Dark Coven Hood
(35496, 0, 50242, 0, 0, 2742, 0), -- Dark Coven Leggings
(35496, 0, 50243, 0, 0, 2742, 0), -- Dark Coven Robe
(35496, 0, 50244, 0, 0, 2740, 0), -- Dark Coven Shoulderpads
(35496, 0, 50275, 0, 0, 2740, 0), -- Bloodmage Gloves
(35496, 0, 50276, 0, 0, 2742, 0), -- Bloodmage Hood
(35496, 0, 50277, 0, 0, 2742, 0), -- Bloodmage Leggings
(35496, 0, 50278, 0, 0, 2742, 0), -- Bloodmage Robe
(35496, 0, 50279, 0, 0, 2740, 0), -- Bloodmage Shoulderpads
(35496, 0, 50391, 0, 0, 2740, 0), -- Crimson Acolyte Handwraps
(35496, 0, 50392, 0, 0, 2742, 0), -- Crimson Acolyte Cowl
(35496, 0, 50393, 0, 0, 2742, 0), -- Crimson Acolyte Pants
(35496, 0, 50394, 0, 0, 2742, 0), -- Crimson Acolyte Raiments
(35496, 0, 50396, 0, 0, 2740, 0), -- Crimson Acolyte Mantle
(35496, 0, 50765, 0, 0, 2742, 0), -- Crimson Acolyte Hood
(35496, 0, 50766, 0, 0, 2740, 0), -- Crimson Acolyte Gloves
(35496, 0, 50767, 0, 0, 2740, 0), -- Crimson Acolyte Shoulderpads
(35496, 0, 50768, 0, 0, 2742, 0), -- Crimson Acolyte Robe
(35496, 0, 50769, 0, 0, 2742, 0), -- Crimson Acolyte Leggings
(35496, 0, 51155, 0, 0, 2745, 0), -- Sanctified Bloodmage Shoulderpads
(35496, 0, 51156, 0, 0, 2746, 0), -- Sanctified Bloodmage Robe
(35496, 0, 51157, 0, 0, 2747, 0), -- Sanctified Bloodmage Leggings
(35496, 0, 51158, 0, 0, 2748, 0), -- Sanctified Bloodmage Hood
(35496, 0, 51159, 0, 0, 2749, 0), -- Sanctified Bloodmage Gloves
(35496, 0, 51175, 0, 0, 2855, 0), -- Sanctified Crimson Acolyte Shoulderpads
(35496, 0, 51176, 0, 0, 2856, 0), -- Sanctified Crimson Acolyte Robe
(35496, 0, 51177, 0, 0, 2857, 0), -- Sanctified Crimson Acolyte Leggings
(35496, 0, 51178, 0, 0, 2858, 0), -- Sanctified Crimson Acolyte Hood
(35496, 0, 51179, 0, 0, 2859, 0), -- Sanctified Crimson Acolyte Gloves
(35496, 0, 51180, 0, 0, 2865, 0), -- Sanctified Crimson Acolyte Raiments
(35496, 0, 51181, 0, 0, 2866, 0), -- Sanctified Crimson Acolyte Pants
(35496, 0, 51182, 0, 0, 2867, 0), -- Sanctified Crimson Acolyte Mantle
(35496, 0, 51183, 0, 0, 2868, 0), -- Sanctified Crimson Acolyte Handwraps
(35496, 0, 51184, 0, 0, 2869, 0), -- Sanctified Crimson Acolyte Cowl
(35496, 0, 51205, 0, 0, 2845, 0), -- Sanctified Dark Coven Shoulderpads
(35496, 0, 51206, 0, 0, 2846, 0), -- Sanctified Dark Coven Robe
(35496, 0, 51207, 0, 0, 2847, 0), -- Sanctified Dark Coven Leggings
(35496, 0, 51208, 0, 0, 2848, 0), -- Sanctified Dark Coven Hood
(35496, 0, 51209, 0, 0, 2849, 0), -- Sanctified Dark Coven Gloves
(35496, 0, 51230, 0, 0, 2850, 0), -- Sanctified Dark Coven Gloves
(35496, 0, 51231, 0, 0, 2851, 0), -- Sanctified Dark Coven Hood
(35496, 0, 51232, 0, 0, 2852, 0), -- Sanctified Dark Coven Leggings
(35496, 0, 51233, 0, 0, 2853, 0), -- Sanctified Dark Coven Robe
(35496, 0, 51234, 0, 0, 2854, 0), -- Sanctified Dark Coven Shoulderpads
(35496, 0, 51255, 0, 0, 2870, 0), -- Sanctified Crimson Acolyte Cowl
(35496, 0, 51256, 0, 0, 2871, 0), -- Sanctified Crimson Acolyte Handwraps
(35496, 0, 51257, 0, 0, 2872, 0), -- Sanctified Crimson Acolyte Mantle
(35496, 0, 51258, 0, 0, 2873, 0), -- Sanctified Crimson Acolyte Pants
(35496, 0, 51259, 0, 0, 2874, 0), -- Sanctified Crimson Acolyte Raiments
(35496, 0, 51260, 0, 0, 2860, 0), -- Sanctified Crimson Acolyte Gloves
(35496, 0, 51261, 0, 0, 2861, 0), -- Sanctified Crimson Acolyte Hood
(35496, 0, 51262, 0, 0, 2862, 0), -- Sanctified Crimson Acolyte Leggings
(35496, 0, 51263, 0, 0, 2863, 0), -- Sanctified Crimson Acolyte Robe
(35496, 0, 51264, 0, 0, 2864, 0), -- Sanctified Crimson Acolyte Shoulderpads
(35496, 0, 51280, 0, 0, 2750, 0), -- Sanctified Bloodmage Gloves
(35496, 0, 51281, 0, 0, 2751, 0), -- Sanctified Bloodmage Hood
(35496, 0, 51282, 0, 0, 2752, 0), -- Sanctified Bloodmage Leggings
(35496, 0, 51283, 0, 0, 2753, 0), -- Sanctified Bloodmage Robe
(35496, 0, 51284, 0, 0, 2754, 0); -- Sanctified Bloodmage Shoulderpads

-- Marshal Magruder <Wintergrasp Quartermaster>
DELETE FROM `npc_vendor` WHERE `entry` = 39172 AND `item` IN (51568, 51569, 51570, 51571, 51572, 51573, 51574, 51575);
DELETE FROM `npc_vendor` WHERE `entry` = 39172 AND `item` IN (51576, 51577, 51578, 51579, 51580, 51581);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(39172, 0, 51568, 0, 0, 2578, 0), -- Titan-Forged Pendant of Ascendancy
(39172, 0, 51569, 0, 0, 2578, 0), -- Titan-Forged Pendant of Victory
(39172, 0, 51570, 0, 0, 2578, 0), -- Titan-Forged Cloak of Ascendancy
(39172, 0, 51571, 0, 0, 2578, 0), -- Titan-Forged Cloak of Victory
(39172, 0, 51572, 0, 0, 2579, 0), -- Titan-Forged Shoulderpads of Salvation
(39172, 0, 51573, 0, 0, 2579, 0), -- Titan-Forged Shoulderpads of Domination
(39172, 0, 51574, 0, 0, 2579, 0), -- Titan-Forged Spaulders of Dominance
(39172, 0, 51575, 0, 0, 2579, 0), -- Titan-Forged Spaulders of Salvation
(39172, 0, 51576, 0, 0, 2579, 0), -- Titan-Forged Spaulders of Triumph
(39172, 0, 51577, 0, 0, 2579, 0), -- Titan-Forged Shoulders of Triumph
(39172, 0, 51578, 0, 0, 2579, 0), -- Titan-Forged Shoulders of Dominance
(39172, 0, 51579, 0, 0, 2579, 0), -- Titan-Forged Shoulders of Salvation
(39172, 0, 51580, 0, 0, 2579, 0), -- Titan-Forged Shoulderplates of Triumph
(39172, 0, 51581, 0, 0, 2579, 0); -- Titan-Forged Shoulderplates of Salvation

-- Champion Ros'slai <Wintergrasp Quartermaster>
DELETE FROM `npc_vendor` WHERE `entry` = 39173 AND `item` IN (51568, 51569, 51570, 51571, 51572, 51573, 51574, 51575);
DELETE FROM `npc_vendor` WHERE `entry` = 39173 AND `item` IN (51576, 51577, 51578, 51579, 51580, 51581);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`) VALUES
(39173, 0, 51568, 0, 0, 2578, 0), -- Titan-Forged Pendant of Ascendancy
(39173, 0, 51569, 0, 0, 2578, 0), -- Titan-Forged Pendant of Victory
(39173, 0, 51570, 0, 0, 2578, 0), -- Titan-Forged Cloak of Ascendancy
(39173, 0, 51571, 0, 0, 2578, 0), -- Titan-Forged Cloak of Victory
(39173, 0, 51572, 0, 0, 2579, 0), -- Titan-Forged Shoulderpads of Salvation
(39173, 0, 51573, 0, 0, 2579, 0), -- Titan-Forged Shoulderpads of Domination
(39173, 0, 51574, 0, 0, 2579, 0), -- Titan-Forged Spaulders of Dominance
(39173, 0, 51575, 0, 0, 2579, 0), -- Titan-Forged Spaulders of Salvation
(39173, 0, 51576, 0, 0, 2579, 0), -- Titan-Forged Spaulders of Triumph
(39173, 0, 51577, 0, 0, 2579, 0), -- Titan-Forged Shoulders of Triumph
(39173, 0, 51578, 0, 0, 2579, 0), -- Titan-Forged Shoulders of Dominance
(39173, 0, 51579, 0, 0, 2579, 0), -- Titan-Forged Shoulders of Salvation
(39173, 0, 51580, 0, 0, 2579, 0), -- Titan-Forged Shoulderplates of Triumph
(39173, 0, 51581, 0, 0, 2579, 0); -- Titan-Forged Shoulderplates of Salvation
