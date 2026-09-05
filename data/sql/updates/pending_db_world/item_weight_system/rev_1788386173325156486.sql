-- Phase 5 content, Bucket 1 (ilvl 60-100): converts every remaining Rare/Epic armor and weapon item in this ilvl range
-- (trinkets and already-converted ilvl66 items excluded) to the budget-template system. 54 literal debug/test items
-- excluded by name. Weapon secondary stats are role-classified (physical/caster/tank, by dominant on-budget stat -- see
-- docs/itemization-changes.md's Bucket 1 note) and corrected via a per-item budget_mult so e.g. a caster Main Hand
-- weapon isn't computed against the same slot_mult tier as a dual-wielder's One-Hand piece; item_slot_mult itself is
-- unchanged except for adding Ranged(15)/Thrown(25)/Relic(28), which had no row at all before this. Each item gets its
-- own dedicated template (no consolidation classifier yet), template_id 86-2444.

DELETE FROM `item_budget_template` WHERE `template_id` = 86;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(86, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 87;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(87, 5, 6429),
(87, 6, 3571);

DELETE FROM `item_budget_template` WHERE `template_id` = 88;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(88, 6, 4348),
(88, 5, 5652);

DELETE FROM `item_budget_template` WHERE `template_id` = 89;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(89, 3, 2500),
(89, 5, 2500),
(89, 6, 2500),
(89, 4, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 90;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(90, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 91;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(91, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 92;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(92, 6, 2675),
(92, 5, 3209),
(92, 45, 4116);

DELETE FROM `item_budget_template` WHERE `template_id` = 93;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(93, 6, 3959),
(93, 5, 1979),
(93, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 94;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(94, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 95;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(95, 6, 3200),
(95, 5, 3600),
(95, 31, 3200);

DELETE FROM `item_budget_template` WHERE `template_id` = 96;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(96, 31, 5000),
(96, 32, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 97;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(97, 5, 2652),
(97, 6, 1516),
(97, 45, 5832);

DELETE FROM `item_budget_template` WHERE `template_id` = 98;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(98, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 99;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(99, 6, 1516),
(99, 5, 2652),
(99, 45, 5832);

DELETE FROM `item_budget_template` WHERE `template_id` = 100;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(100, 4, 3000),
(100, 32, 7000);

DELETE FROM `item_budget_template` WHERE `template_id` = 101;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(101, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 102;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(102, 4, 3171),
(102, 32, 6829);

DELETE FROM `item_budget_template` WHERE `template_id` = 103;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(103, 5, 3577),
(103, 45, 6423);

DELETE FROM `item_budget_template` WHERE `template_id` = 104;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(104, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 105;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(105, 3, 7500),
(105, 31, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 106;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(106, 6, 2072),
(106, 5, 5802),
(106, 45, 2126);

DELETE FROM `item_budget_template` WHERE `template_id` = 107;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(107, 5, 5811),
(107, 6, 1835),
(107, 45, 2354);

DELETE FROM `item_budget_template` WHERE `template_id` = 108;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(108, 4, 4800),
(108, 12, 5200);

DELETE FROM `item_budget_template` WHERE `template_id` = 109;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(109, 4, 6250),
(109, 12, 3750);

DELETE FROM `item_budget_template` WHERE `template_id` = 110;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(110, 4, 4800),
(110, 12, 5200);

DELETE FROM `item_budget_template` WHERE `template_id` = 111;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(111, 6, 3244),
(111, 5, 3243),
(111, 45, 3513);

DELETE FROM `item_budget_template` WHERE `template_id` = 112;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(112, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 113;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(113, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 114;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(114, 4, 6250),
(114, 31, 3750);

DELETE FROM `item_budget_template` WHERE `template_id` = 115;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(115, 14, 5882),
(115, 32, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 116;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(116, 4, 2727),
(116, 32, 4243),
(116, 31, 3030);

DELETE FROM `item_budget_template` WHERE `template_id` = 117;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(117, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 118;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(118, 5, 4167),
(118, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 119;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(119, 6, 4588),
(119, 5, 3059),
(119, 45, 2353);

DELETE FROM `item_budget_template` WHERE `template_id` = 120;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(120, 4, 2453),
(120, 32, 5283),
(120, 13, 2264);

DELETE FROM `item_budget_template` WHERE `template_id` = 121;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(121, 4, 2222),
(121, 32, 7778);

DELETE FROM `item_budget_template` WHERE `template_id` = 122;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(122, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 123;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(123, 4, 6667),
(123, 3, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 124;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(124, 3, 7857),
(124, 4, 2143);

DELETE FROM `item_budget_template` WHERE `template_id` = 125;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(125, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 126;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(126, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 127;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(127, 4, 1923),
(127, 31, 2692),
(127, 32, 5385);

DELETE FROM `item_budget_template` WHERE `template_id` = 128;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(128, 4, 3514),
(128, 32, 6486);

DELETE FROM `item_budget_template` WHERE `template_id` = 129;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(129, 31, 4167),
(129, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 130;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(130, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 131;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(131, 4, 2222),
(131, 32, 7778);

DELETE FROM `item_budget_template` WHERE `template_id` = 132;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(132, 5, 4222),
(132, 6, 5778);

DELETE FROM `item_budget_template` WHERE `template_id` = 133;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(133, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 134;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(134, 5, 4936),
(134, 45, 5064);

DELETE FROM `item_budget_template` WHERE `template_id` = 135;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(135, 3, 5000),
(135, 31, 2083),
(135, 32, 2917);

DELETE FROM `item_budget_template` WHERE `template_id` = 136;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(136, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 137;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(137, 6, 3317),
(137, 5, 3316),
(137, 45, 3367);

DELETE FROM `item_budget_template` WHERE `template_id` = 138;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(138, 4, 2000),
(138, 3, 4000),
(138, 31, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 139;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(139, 5, 2273),
(139, 32, 7727);

DELETE FROM `item_budget_template` WHERE `template_id` = 140;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(140, 5, 3530),
(140, 6, 3529),
(140, 31, 2941);

DELETE FROM `item_budget_template` WHERE `template_id` = 141;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(141, 6, 4681),
(141, 5, 5319);

DELETE FROM `item_budget_template` WHERE `template_id` = 142;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(142, 6, 2113),
(142, 5, 2466),
(142, 45, 5421);

DELETE FROM `item_budget_template` WHERE `template_id` = 143;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(143, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 144;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(144, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 145;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(145, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 146;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(146, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 147;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(147, 4, 3750),
(147, 12, 6250);

DELETE FROM `item_budget_template` WHERE `template_id` = 148;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(148, 4, 3261),
(148, 6, 3478),
(148, 3, 3261);

DELETE FROM `item_budget_template` WHERE `template_id` = 149;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(149, 5, 6154),
(149, 6, 3846);

DELETE FROM `item_budget_template` WHERE `template_id` = 150;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(150, 3, 1923),
(150, 5, 1539),
(150, 6, 6538);

DELETE FROM `item_budget_template` WHERE `template_id` = 151;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(151, 4, 2500),
(151, 6, 2500),
(151, 5, 2500),
(151, 3, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 152;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(152, 5, 4772),
(152, 6, 2290),
(152, 45, 2938);

DELETE FROM `item_budget_template` WHERE `template_id` = 153;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(153, 6, 5238),
(153, 5, 4762);

DELETE FROM `item_budget_template` WHERE `template_id` = 154;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(154, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 155;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(155, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 156;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(156, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 157;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(157, 3, 8462),
(157, 5, 1538);

DELETE FROM `item_budget_template` WHERE `template_id` = 158;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(158, 6, 5000),
(158, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 159;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(159, 5, 4828),
(159, 6, 5172);

DELETE FROM `item_budget_template` WHERE `template_id` = 160;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(160, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 161;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(161, 4, 6000),
(161, 31, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 162;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(162, 5, 6762),
(162, 45, 3238);

DELETE FROM `item_budget_template` WHERE `template_id` = 163;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(163, 4, 3913),
(163, 32, 6087);

DELETE FROM `item_budget_template` WHERE `template_id` = 164;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(164, 3, 1666),
(164, 4, 4167),
(164, 14, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 165;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(165, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 166;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(166, 4, 2831),
(166, 5, 3538),
(166, 45, 3631);

DELETE FROM `item_budget_template` WHERE `template_id` = 167;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(167, 6, 3315),
(167, 5, 3094),
(167, 45, 3591);

DELETE FROM `item_budget_template` WHERE `template_id` = 168;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(168, 5, 2158),
(168, 45, 7842);

DELETE FROM `item_budget_template` WHERE `template_id` = 169;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(169, 3, 5200),
(169, 13, 4800);

DELETE FROM `item_budget_template` WHERE `template_id` = 170;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(170, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 171;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(171, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 172;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(172, 6, 3395),
(172, 5, 3703),
(172, 45, 2902);

DELETE FROM `item_budget_template` WHERE `template_id` = 173;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(173, 5, 3134),
(173, 6, 1994),
(173, 45, 4872);

DELETE FROM `item_budget_template` WHERE `template_id` = 174;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(174, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 175;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(175, 6, 4000),
(175, 5, 6000);

DELETE FROM `item_budget_template` WHERE `template_id` = 176;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(176, 6, 6762),
(176, 45, 3238);

DELETE FROM `item_budget_template` WHERE `template_id` = 177;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(177, 6, 4854),
(177, 5, 2774),
(177, 45, 2372);

DELETE FROM `item_budget_template` WHERE `template_id` = 178;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(178, 6, 2609),
(178, 3, 3043),
(178, 31, 4348);

DELETE FROM `item_budget_template` WHERE `template_id` = 179;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(179, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 180;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(180, 5, 7500),
(180, 6, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 181;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(181, 3, 5172),
(181, 4, 4828);

DELETE FROM `item_budget_template` WHERE `template_id` = 182;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(182, 6, 1753),
(182, 5, 1753),
(182, 45, 6494);

DELETE FROM `item_budget_template` WHERE `template_id` = 183;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(183, 4, 5000),
(183, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 184;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(184, 6, 4324),
(184, 5, 2433),
(184, 13, 3243);

DELETE FROM `item_budget_template` WHERE `template_id` = 185;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(185, 5, 3503),
(185, 6, 3502),
(185, 45, 2995);

DELETE FROM `item_budget_template` WHERE `template_id` = 186;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(186, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 187;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(187, 6, 2672),
(187, 5, 3266),
(187, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 188;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(188, 5, 7083),
(188, 6, 2917);

DELETE FROM `item_budget_template` WHERE `template_id` = 189;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(189, 6, 2351),
(189, 5, 1069),
(189, 45, 6580);

DELETE FROM `item_budget_template` WHERE `template_id` = 190;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(190, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 191;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(191, 6, 4000),
(191, 5, 6000);

DELETE FROM `item_budget_template` WHERE `template_id` = 192;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(192, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 193;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(193, 6, 3750),
(193, 5, 6250);

DELETE FROM `item_budget_template` WHERE `template_id` = 194;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(194, 6, 2027),
(194, 45, 7973);

DELETE FROM `item_budget_template` WHERE `template_id` = 195;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(195, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 196;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(196, 4, 6667),
(196, 3, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 197;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(197, 6, 2903),
(197, 5, 7097);

DELETE FROM `item_budget_template` WHERE `template_id` = 198;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(198, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 199;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(199, 3, 2500),
(199, 4, 2500),
(199, 5, 2500),
(199, 6, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 200;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(200, 6, 2335),
(200, 5, 4670),
(200, 45, 2995);

DELETE FROM `item_budget_template` WHERE `template_id` = 201;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(201, 6, 5000),
(201, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 202;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(202, 5, 5323),
(202, 6, 2129),
(202, 45, 2548);

DELETE FROM `item_budget_template` WHERE `template_id` = 203;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(203, 5, 5559),
(203, 6, 2223),
(203, 45, 2218);

DELETE FROM `item_budget_template` WHERE `template_id` = 204;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(204, 6, 8500),
(204, 5, 1500);

DELETE FROM `item_budget_template` WHERE `template_id` = 205;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(205, 3, 5333),
(205, 4, 4667);

DELETE FROM `item_budget_template` WHERE `template_id` = 206;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(206, 5, 3305),
(206, 6, 3305),
(206, 45, 3390);

DELETE FROM `item_budget_template` WHERE `template_id` = 207;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(207, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 208;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(208, 4, 5238),
(208, 3, 4762);

DELETE FROM `item_budget_template` WHERE `template_id` = 209;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(209, 6, 2468),
(209, 5, 3798),
(209, 45, 3734);

DELETE FROM `item_budget_template` WHERE `template_id` = 210;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(210, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 211;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(211, 5, 2984),
(211, 45, 7016);

DELETE FROM `item_budget_template` WHERE `template_id` = 212;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(212, 4, 2632),
(212, 32, 7368);

DELETE FROM `item_budget_template` WHERE `template_id` = 213;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(213, 5, 6071),
(213, 6, 3929);

DELETE FROM `item_budget_template` WHERE `template_id` = 214;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(214, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 215;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(215, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 216;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(216, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 217;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(217, 5, 7037),
(217, 31, 2963);

DELETE FROM `item_budget_template` WHERE `template_id` = 218;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(218, 3, 1724),
(218, 4, 3448),
(218, 32, 4828);

DELETE FROM `item_budget_template` WHERE `template_id` = 219;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(219, 6, 6250),
(219, 5, 3750);

DELETE FROM `item_budget_template` WHERE `template_id` = 220;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(220, 4, 5172),
(220, 32, 4828);

DELETE FROM `item_budget_template` WHERE `template_id` = 221;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(221, 6, 7500),
(221, 5, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 222;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(222, 5, 8148),
(222, 6, 1852);

DELETE FROM `item_budget_template` WHERE `template_id` = 223;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(223, 4, 2571),
(223, 32, 4000),
(223, 13, 3429);

DELETE FROM `item_budget_template` WHERE `template_id` = 224;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(224, 3, 3103),
(224, 31, 6897);

DELETE FROM `item_budget_template` WHERE `template_id` = 225;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(225, 5, 4006),
(225, 45, 5994);

DELETE FROM `item_budget_template` WHERE `template_id` = 226;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(226, 3, 6667),
(226, 31, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 227;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(227, 5, 3126),
(227, 45, 6874);

DELETE FROM `item_budget_template` WHERE `template_id` = 228;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(228, 5, 5000),
(228, 6, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 229;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(229, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 230;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(230, 5, 5128),
(230, 6, 4872);

DELETE FROM `item_budget_template` WHERE `template_id` = 231;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(231, 5, 6071),
(231, 6, 3929);

DELETE FROM `item_budget_template` WHERE `template_id` = 232;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(232, 5, 6053),
(232, 6, 3947);

DELETE FROM `item_budget_template` WHERE `template_id` = 233;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(233, 5, 2174),
(233, 6, 1739),
(233, 32, 6087);

DELETE FROM `item_budget_template` WHERE `template_id` = 234;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(234, 5, 1993),
(234, 45, 5681),
(234, 32, 2326);

DELETE FROM `item_budget_template` WHERE `template_id` = 235;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(235, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 236;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(236, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 237;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(237, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 238;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(238, 4, 2500),
(238, 3, 7500);

DELETE FROM `item_budget_template` WHERE `template_id` = 239;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(239, 5, 2500),
(239, 6, 2500),
(239, 4, 2500),
(239, 3, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 240;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(240, 6, 2779),
(240, 5, 5558),
(240, 45, 1663);

DELETE FROM `item_budget_template` WHERE `template_id` = 241;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(241, 4, 6000),
(241, 12, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 242;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(242, 6, 3684),
(242, 5, 6316);

DELETE FROM `item_budget_template` WHERE `template_id` = 243;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(243, 6, 2353),
(243, 5, 7647);

DELETE FROM `item_budget_template` WHERE `template_id` = 244;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(244, 5, 4890),
(244, 45, 5110);

DELETE FROM `item_budget_template` WHERE `template_id` = 245;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(245, 38, 2609),
(245, 31, 2609),
(245, 32, 2608),
(245, 3, 2174);

DELETE FROM `item_budget_template` WHERE `template_id` = 246;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(246, 5, 5385),
(246, 6, 4615);

DELETE FROM `item_budget_template` WHERE `template_id` = 247;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(247, 5, 5839),
(247, 45, 4161);

DELETE FROM `item_budget_template` WHERE `template_id` = 248;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(248, 6, 3827),
(248, 5, 2649),
(248, 45, 3524);

DELETE FROM `item_budget_template` WHERE `template_id` = 249;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(249, 6, 2946),
(249, 45, 7054);

DELETE FROM `item_budget_template` WHERE `template_id` = 250;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(250, 4, 5000),
(250, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 251;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(251, 5, 6552),
(251, 6, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 252;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(252, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 253;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(253, 5, 3191),
(253, 4, 2128),
(253, 6, 2128),
(253, 13, 2553);

DELETE FROM `item_budget_template` WHERE `template_id` = 254;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(254, 5, 3572),
(254, 4, 3571),
(254, 3, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 255;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(255, 5, 2727),
(255, 3, 3637),
(255, 4, 3636);

DELETE FROM `item_budget_template` WHERE `template_id` = 256;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(256, 5, 3030),
(256, 4, 2727),
(256, 32, 4243);

DELETE FROM `item_budget_template` WHERE `template_id` = 257;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(257, 5, 2632),
(257, 4, 2368),
(257, 3, 2368),
(257, 31, 2632);

DELETE FROM `item_budget_template` WHERE `template_id` = 258;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(258, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 259;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(259, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 260;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(260, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 261;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(261, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 262;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(262, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 263;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(263, 6, 3891),
(263, 5, 3891),
(263, 45, 2218);

DELETE FROM `item_budget_template` WHERE `template_id` = 264;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(264, 6, 3889),
(264, 5, 6111);

DELETE FROM `item_budget_template` WHERE `template_id` = 265;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(265, 5, 3521),
(265, 6, 3168),
(265, 45, 3311);

DELETE FROM `item_budget_template` WHERE `template_id` = 266;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(266, 5, 6000),
(266, 6, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 267;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(267, 5, 5500),
(267, 6, 4500);

DELETE FROM `item_budget_template` WHERE `template_id` = 268;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(268, 4, 5000),
(268, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 269;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(269, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 270;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(270, 38, 7143),
(270, 31, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 271;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(271, 38, 7105),
(271, 32, 2895);

DELETE FROM `item_budget_template` WHERE `template_id` = 272;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(272, 6, 6762),
(272, 45, 3238);

DELETE FROM `item_budget_template` WHERE `template_id` = 273;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(273, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 274;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(274, 4, 2083),
(274, 3, 2083),
(274, 5, 1945),
(274, 6, 1945),
(274, 32, 1944);

DELETE FROM `item_budget_template` WHERE `template_id` = 275;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(275, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 276;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(276, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 277;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(277, 5, 6818),
(277, 6, 3182);

DELETE FROM `item_budget_template` WHERE `template_id` = 278;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(278, 5, 5000),
(278, 6, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 279;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(279, 3, 5000),
(279, 4, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 280;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(280, 6, 7073),
(280, 5, 2927);

DELETE FROM `item_budget_template` WHERE `template_id` = 281;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(281, 5, 5000),
(281, 6, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 282;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(282, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 283;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(283, 5, 2262),
(283, 45, 7738);

DELETE FROM `item_budget_template` WHERE `template_id` = 284;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(284, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 285;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(285, 5, 2500),
(285, 6, 2500),
(285, 4, 2500),
(285, 3, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 286;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(286, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 287;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(287, 6, 3704),
(287, 5, 6296);

DELETE FROM `item_budget_template` WHERE `template_id` = 288;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(288, 5, 5938),
(288, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 289;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(289, 6, 3000),
(289, 5, 7000);

DELETE FROM `item_budget_template` WHERE `template_id` = 290;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(290, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 291;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(291, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 292;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(292, 4, 3079),
(292, 3, 1283),
(292, 5, 1283),
(292, 6, 1283),
(292, 45, 3072);

DELETE FROM `item_budget_template` WHERE `template_id` = 293;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(293, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 294;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(294, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 295;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(295, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 296;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(296, 4, 5000),
(296, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 297;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(297, 3, 6250),
(297, 4, 3750);

DELETE FROM `item_budget_template` WHERE `template_id` = 298;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(298, 5, 5357),
(298, 4, 1786),
(298, 6, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 299;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(299, 3, 6087),
(299, 5, 3913);

DELETE FROM `item_budget_template` WHERE `template_id` = 300;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(300, 3, 3684),
(300, 13, 6316);

DELETE FROM `item_budget_template` WHERE `template_id` = 301;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(301, 3, 7727),
(301, 4, 2273);

DELETE FROM `item_budget_template` WHERE `template_id` = 302;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(302, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 303;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(303, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 304;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(304, 4, 6154),
(304, 3, 3846);

DELETE FROM `item_budget_template` WHERE `template_id` = 305;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(305, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 306;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(306, 4, 6129),
(306, 3, 1936),
(306, 6, 1935);

DELETE FROM `item_budget_template` WHERE `template_id` = 307;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(307, 4, 5357),
(307, 5, 2500),
(307, 3, 2143);

DELETE FROM `item_budget_template` WHERE `template_id` = 308;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(308, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 309;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(309, 5, 3572),
(309, 4, 3214),
(309, 6, 3214);

DELETE FROM `item_budget_template` WHERE `template_id` = 310;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(310, 4, 5000),
(310, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 311;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(311, 5, 5882),
(311, 32, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 312;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(312, 6, 3536),
(312, 5, 2873),
(312, 45, 3591);

DELETE FROM `item_budget_template` WHERE `template_id` = 313;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(313, 5, 5938),
(313, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 314;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(314, 5, 3478),
(314, 6, 3478),
(314, 32, 3044);

DELETE FROM `item_budget_template` WHERE `template_id` = 315;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(315, 3, 4815),
(315, 32, 5185);

DELETE FROM `item_budget_template` WHERE `template_id` = 316;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(316, 13, 5455),
(316, 31, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 317;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(317, 4, 2000),
(317, 32, 8000);

DELETE FROM `item_budget_template` WHERE `template_id` = 318;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(318, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 319;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(319, 4, 2254),
(319, 3, 1560),
(319, 5, 1387),
(319, 45, 2372),
(319, 32, 2427);

DELETE FROM `item_budget_template` WHERE `template_id` = 320;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(320, 4, 2106),
(320, 3, 2105),
(320, 5, 1579),
(320, 6, 2105),
(320, 13, 2105);

DELETE FROM `item_budget_template` WHERE `template_id` = 321;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(321, 4, 2334),
(321, 3, 2334),
(321, 6, 2334),
(321, 5, 1401),
(321, 45, 1597);

DELETE FROM `item_budget_template` WHERE `template_id` = 322;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(322, 3, 2071),
(322, 4, 2071),
(322, 5, 2071),
(322, 6, 1694),
(322, 45, 2093);

DELETE FROM `item_budget_template` WHERE `template_id` = 323;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(323, 3, 4400),
(323, 32, 5600);

DELETE FROM `item_budget_template` WHERE `template_id` = 324;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(324, 3, 3158),
(324, 32, 3684),
(324, 13, 3158);

DELETE FROM `item_budget_template` WHERE `template_id` = 325;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(325, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 326;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(326, 3, 5000),
(326, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 327;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(327, 4, 5294),
(327, 3, 4706);

DELETE FROM `item_budget_template` WHERE `template_id` = 328;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(328, 4, 3103),
(328, 3, 2069),
(328, 32, 4828);

DELETE FROM `item_budget_template` WHERE `template_id` = 329;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(329, 4, 2000),
(329, 32, 8000);

DELETE FROM `item_budget_template` WHERE `template_id` = 330;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(330, 4, 5385),
(330, 3, 4615);

DELETE FROM `item_budget_template` WHERE `template_id` = 331;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(331, 4, 2903),
(331, 3, 2581),
(331, 32, 4516);

DELETE FROM `item_budget_template` WHERE `template_id` = 332;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(332, 4, 5294),
(332, 3, 4706);

DELETE FROM `item_budget_template` WHERE `template_id` = 333;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(333, 4, 2000),
(333, 32, 8000);

DELETE FROM `item_budget_template` WHERE `template_id` = 334;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(334, 4, 3333),
(334, 3, 3333),
(334, 5, 1945),
(334, 6, 1389);

DELETE FROM `item_budget_template` WHERE `template_id` = 335;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(335, 5, 3046),
(335, 6, 1306),
(335, 45, 3907),
(335, 31, 1741);

DELETE FROM `item_budget_template` WHERE `template_id` = 336;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(336, 5, 6552),
(336, 6, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 337;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(337, 5, 6053),
(337, 6, 3947);

DELETE FROM `item_budget_template` WHERE `template_id` = 338;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(338, 5, 2994),
(338, 6, 1247),
(338, 45, 5759);

DELETE FROM `item_budget_template` WHERE `template_id` = 339;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(339, 5, 2607),
(339, 6, 920),
(339, 32, 2147),
(339, 45, 4326);

DELETE FROM `item_budget_template` WHERE `template_id` = 340;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(340, 6, 1436),
(340, 5, 2871),
(340, 45, 3683),
(340, 32, 2010);

DELETE FROM `item_budget_template` WHERE `template_id` = 341;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(341, 5, 2607),
(341, 6, 920),
(341, 32, 2147),
(341, 45, 4326);

DELETE FROM `item_budget_template` WHERE `template_id` = 342;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(342, 5, 3625),
(342, 6, 1209),
(342, 45, 5166);

DELETE FROM `item_budget_template` WHERE `template_id` = 343;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(343, 5, 6552),
(343, 6, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 344;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(344, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 345;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(345, 5, 7143),
(345, 6, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 346;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(346, 4, 4060),
(346, 3, 3857),
(346, 45, 2083);

DELETE FROM `item_budget_template` WHERE `template_id` = 347;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(347, 4, 2141),
(347, 3, 2141),
(347, 6, 1682),
(347, 5, 1682),
(347, 45, 2354);

DELETE FROM `item_budget_template` WHERE `template_id` = 348;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(348, 4, 2857),
(348, 3, 2143),
(348, 5, 1786),
(348, 6, 1547),
(348, 32, 1667);

DELETE FROM `item_budget_template` WHERE `template_id` = 349;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(349, 3, 2102),
(349, 4, 2213),
(349, 5, 1659),
(349, 6, 774),
(349, 32, 1549),
(349, 45, 1703);

DELETE FROM `item_budget_template` WHERE `template_id` = 350;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(350, 4, 2978),
(350, 3, 1668),
(350, 5, 1548),
(350, 45, 2139),
(350, 32, 1667);

DELETE FROM `item_budget_template` WHERE `template_id` = 351;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(351, 3, 5200),
(351, 32, 2800),
(351, 31, 2000);

DELETE FROM `item_budget_template` WHERE `template_id` = 352;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(352, 3, 5882),
(352, 32, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 353;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(353, 3, 5294),
(353, 32, 2745),
(353, 31, 1961);

DELETE FROM `item_budget_template` WHERE `template_id` = 354;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(354, 3, 4426),
(354, 31, 3279),
(354, 32, 2295);

DELETE FROM `item_budget_template` WHERE `template_id` = 355;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(355, 3, 6774),
(355, 31, 3226);

DELETE FROM `item_budget_template` WHERE `template_id` = 356;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(356, 4, 6341),
(356, 3, 3659);

DELETE FROM `item_budget_template` WHERE `template_id` = 357;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(357, 4, 2872),
(357, 5, 1595),
(357, 6, 1595),
(357, 3, 1755),
(357, 45, 2183);

DELETE FROM `item_budget_template` WHERE `template_id` = 358;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(358, 3, 6552),
(358, 4, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 359;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(359, 3, 7407),
(359, 5, 2593);

DELETE FROM `item_budget_template` WHERE `template_id` = 360;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(360, 3, 4865),
(360, 5, 2432),
(360, 31, 2703);

DELETE FROM `item_budget_template` WHERE `template_id` = 361;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(361, 3, 4375),
(361, 5, 1250),
(361, 32, 4375);

DELETE FROM `item_budget_template` WHERE `template_id` = 362;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(362, 5, 4390),
(362, 3, 4390),
(362, 4, 1220);

DELETE FROM `item_budget_template` WHERE `template_id` = 363;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(363, 3, 4694),
(363, 5, 2449),
(363, 32, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 364;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(364, 3, 4694),
(364, 5, 2449),
(364, 32, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 365;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(365, 3, 4694),
(365, 5, 2449),
(365, 32, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 366;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(366, 3, 4737),
(366, 5, 2632),
(366, 31, 2631);

DELETE FROM `item_budget_template` WHERE `template_id` = 367;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(367, 4, 7778),
(367, 5, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 368;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(368, 6, 3333),
(368, 5, 3333),
(368, 4, 1667),
(368, 3, 1667);

DELETE FROM `item_budget_template` WHERE `template_id` = 369;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(369, 4, 3750),
(369, 5, 3333),
(369, 32, 2917);

DELETE FROM `item_budget_template` WHERE `template_id` = 370;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(370, 4, 3305),
(370, 5, 3305),
(370, 45, 3390);

DELETE FROM `item_budget_template` WHERE `template_id` = 371;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(371, 4, 2749),
(371, 5, 2619),
(371, 32, 1833),
(371, 45, 2799);

DELETE FROM `item_budget_template` WHERE `template_id` = 372;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(372, 4, 2749),
(372, 5, 2619),
(372, 32, 1833),
(372, 45, 2799);

DELETE FROM `item_budget_template` WHERE `template_id` = 373;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(373, 4, 2699),
(373, 5, 2295),
(373, 45, 3116),
(373, 32, 1890);

DELETE FROM `item_budget_template` WHERE `template_id` = 374;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(374, 4, 3387),
(374, 5, 3175),
(374, 45, 3438);

DELETE FROM `item_budget_template` WHERE `template_id` = 375;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(375, 4, 3636),
(375, 3, 3182),
(375, 32, 3182);

DELETE FROM `item_budget_template` WHERE `template_id` = 376;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(376, 4, 6667),
(376, 32, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 377;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(377, 4, 3448),
(377, 32, 4828),
(377, 31, 1724);

DELETE FROM `item_budget_template` WHERE `template_id` = 378;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(378, 4, 4091),
(378, 3, 3636),
(378, 31, 2273);

DELETE FROM `item_budget_template` WHERE `template_id` = 379;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(379, 4, 7083),
(379, 3, 2917);

DELETE FROM `item_budget_template` WHERE `template_id` = 380;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(380, 4, 6757),
(380, 3, 3243);

DELETE FROM `item_budget_template` WHERE `template_id` = 381;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(381, 4, 4500),
(381, 3, 3000),
(381, 31, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 382;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(382, 4, 5882),
(382, 32, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 383;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(383, 5, 5938),
(383, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 384;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(384, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 385;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(385, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 386;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(386, 6, 3704),
(386, 5, 6296);

DELETE FROM `item_budget_template` WHERE `template_id` = 387;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(387, 5, 3478),
(387, 6, 3478),
(387, 32, 3044);

DELETE FROM `item_budget_template` WHERE `template_id` = 388;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(388, 6, 3536),
(388, 5, 2873),
(388, 45, 3591);

DELETE FROM `item_budget_template` WHERE `template_id` = 389;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(389, 5, 5882),
(389, 32, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 390;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(390, 5, 5938),
(390, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 391;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(391, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 392;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(392, 4, 3079),
(392, 5, 1283),
(392, 3, 1283),
(392, 6, 1283),
(392, 45, 3072);

DELETE FROM `item_budget_template` WHERE `template_id` = 393;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(393, 5, 5357),
(393, 4, 1786),
(393, 6, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 394;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(394, 4, 5000),
(394, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 395;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(395, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 396;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(396, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 397;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(397, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 398;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(398, 3, 6250),
(398, 4, 3750);

DELETE FROM `item_budget_template` WHERE `template_id` = 399;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(399, 4, 2334),
(399, 3, 2334),
(399, 6, 2334),
(399, 5, 1401),
(399, 45, 1597);

DELETE FROM `item_budget_template` WHERE `template_id` = 400;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(400, 4, 2106),
(400, 3, 2105),
(400, 6, 2105),
(400, 5, 1579),
(400, 13, 2105);

DELETE FROM `item_budget_template` WHERE `template_id` = 401;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(401, 3, 2071),
(401, 4, 2071),
(401, 5, 2071),
(401, 6, 1694),
(401, 45, 2093);

DELETE FROM `item_budget_template` WHERE `template_id` = 402;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(402, 4, 2254),
(402, 3, 1560),
(402, 5, 1387),
(402, 32, 2427),
(402, 45, 2372);

DELETE FROM `item_budget_template` WHERE `template_id` = 403;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(403, 3, 4815),
(403, 32, 5185);

DELETE FROM `item_budget_template` WHERE `template_id` = 404;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(404, 13, 5455),
(404, 31, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 405;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(405, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 406;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(406, 4, 2000),
(406, 32, 8000);

DELETE FROM `item_budget_template` WHERE `template_id` = 407;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(407, 4, 6154),
(407, 3, 3846);

DELETE FROM `item_budget_template` WHERE `template_id` = 408;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(408, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 409;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(409, 4, 6129),
(409, 3, 1936),
(409, 6, 1935);

DELETE FROM `item_budget_template` WHERE `template_id` = 410;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(410, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 411;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(411, 4, 3103),
(411, 3, 2069),
(411, 32, 4828);

DELETE FROM `item_budget_template` WHERE `template_id` = 412;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(412, 4, 5294),
(412, 3, 4706);

DELETE FROM `item_budget_template` WHERE `template_id` = 413;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(413, 4, 2000),
(413, 32, 8000);

DELETE FROM `item_budget_template` WHERE `template_id` = 414;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(414, 4, 5385),
(414, 3, 4615);

DELETE FROM `item_budget_template` WHERE `template_id` = 415;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(415, 3, 7727),
(415, 4, 2273);

DELETE FROM `item_budget_template` WHERE `template_id` = 416;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(416, 5, 4552),
(416, 45, 5448);

DELETE FROM `item_budget_template` WHERE `template_id` = 417;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(417, 5, 2393),
(417, 4, 2052),
(417, 45, 5555);

DELETE FROM `item_budget_template` WHERE `template_id` = 418;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(418, 5, 6071),
(418, 4, 2500),
(418, 6, 1429);

DELETE FROM `item_budget_template` WHERE `template_id` = 419;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(419, 5, 2903),
(419, 4, 2581),
(419, 32, 4516);

DELETE FROM `item_budget_template` WHERE `template_id` = 420;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(420, 5, 5882),
(420, 32, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 421;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(421, 5, 2943),
(421, 3, 1338),
(421, 45, 5719);

DELETE FROM `item_budget_template` WHERE `template_id` = 422;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(422, 5, 4978),
(422, 4, 1660),
(422, 3, 1659),
(422, 45, 1703);

DELETE FROM `item_budget_template` WHERE `template_id` = 423;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(423, 3, 4400),
(423, 32, 5600);

DELETE FROM `item_budget_template` WHERE `template_id` = 424;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(424, 3, 5000),
(424, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 425;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(425, 3, 3158),
(425, 32, 3684),
(425, 13, 3158);

DELETE FROM `item_budget_template` WHERE `template_id` = 426;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(426, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 427;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(427, 3, 6087),
(427, 5, 3913);

DELETE FROM `item_budget_template` WHERE `template_id` = 428;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(428, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 429;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(429, 3, 3684),
(429, 13, 6316);

DELETE FROM `item_budget_template` WHERE `template_id` = 430;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(430, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 431;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(431, 5, 2607),
(431, 6, 920),
(431, 32, 2147),
(431, 45, 4326);

DELETE FROM `item_budget_template` WHERE `template_id` = 432;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(432, 6, 1436),
(432, 5, 2871),
(432, 45, 3683),
(432, 32, 2010);

DELETE FROM `item_budget_template` WHERE `template_id` = 433;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(433, 5, 2607),
(433, 6, 920),
(433, 32, 2147),
(433, 45, 4326);

DELETE FROM `item_budget_template` WHERE `template_id` = 434;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(434, 5, 3625),
(434, 6, 1209),
(434, 45, 5166);

DELETE FROM `item_budget_template` WHERE `template_id` = 435;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(435, 5, 6053),
(435, 6, 3947);

DELETE FROM `item_budget_template` WHERE `template_id` = 436;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(436, 5, 6552),
(436, 6, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 437;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(437, 5, 3046),
(437, 6, 1306),
(437, 45, 3907),
(437, 31, 1741);

DELETE FROM `item_budget_template` WHERE `template_id` = 438;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(438, 5, 2994),
(438, 6, 1247),
(438, 45, 5759);

DELETE FROM `item_budget_template` WHERE `template_id` = 439;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(439, 4, 3636),
(439, 3, 3182),
(439, 32, 3182);

DELETE FROM `item_budget_template` WHERE `template_id` = 440;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(440, 4, 6667),
(440, 32, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 441;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(441, 4, 3448),
(441, 32, 4828),
(441, 31, 1724);

DELETE FROM `item_budget_template` WHERE `template_id` = 442;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(442, 4, 4091),
(442, 3, 3636),
(442, 31, 2273);

DELETE FROM `item_budget_template` WHERE `template_id` = 443;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(443, 4, 4500),
(443, 3, 3000),
(443, 31, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 444;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(444, 4, 7083),
(444, 3, 2917);

DELETE FROM `item_budget_template` WHERE `template_id` = 445;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(445, 4, 6757),
(445, 3, 3243);

DELETE FROM `item_budget_template` WHERE `template_id` = 446;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(446, 4, 5882),
(446, 32, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 447;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(447, 4, 2978),
(447, 3, 1668),
(447, 5, 1548),
(447, 45, 2139),
(447, 32, 1667);

DELETE FROM `item_budget_template` WHERE `template_id` = 448;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(448, 3, 2102),
(448, 4, 2213),
(448, 5, 1659),
(448, 6, 774),
(448, 45, 1703),
(448, 32, 1549);

DELETE FROM `item_budget_template` WHERE `template_id` = 449;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(449, 3, 2141),
(449, 4, 2141),
(449, 6, 1682),
(449, 5, 1682),
(449, 45, 2354);

DELETE FROM `item_budget_template` WHERE `template_id` = 450;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(450, 4, 2857),
(450, 3, 2143),
(450, 6, 1547),
(450, 5, 1786),
(450, 32, 1667);

DELETE FROM `item_budget_template` WHERE `template_id` = 451;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(451, 5, 6552),
(451, 6, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 452;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(452, 4, 2872),
(452, 5, 1595),
(452, 3, 1755),
(452, 6, 1595),
(452, 45, 2183);

DELETE FROM `item_budget_template` WHERE `template_id` = 453;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(453, 4, 4060),
(453, 3, 3857),
(453, 45, 2083);

DELETE FROM `item_budget_template` WHERE `template_id` = 454;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(454, 5, 7143),
(454, 6, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 455;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(455, 4, 6341),
(455, 3, 3659);

DELETE FROM `item_budget_template` WHERE `template_id` = 456;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(456, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 457;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(457, 3, 6552),
(457, 4, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 458;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(458, 3, 5882),
(458, 32, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 459;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(459, 3, 5294),
(459, 31, 1961),
(459, 32, 2745);

DELETE FROM `item_budget_template` WHERE `template_id` = 460;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(460, 3, 6774),
(460, 31, 3226);

DELETE FROM `item_budget_template` WHERE `template_id` = 461;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(461, 3, 5200),
(461, 31, 2000),
(461, 32, 2800);

DELETE FROM `item_budget_template` WHERE `template_id` = 462;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(462, 3, 4426),
(462, 31, 3279),
(462, 32, 2295);

DELETE FROM `item_budget_template` WHERE `template_id` = 463;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(463, 3, 4694),
(463, 5, 2449),
(463, 32, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 464;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(464, 3, 4694),
(464, 5, 2449),
(464, 32, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 465;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(465, 3, 4694),
(465, 5, 2449),
(465, 32, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 466;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(466, 3, 4737),
(466, 5, 2632),
(466, 31, 2631);

DELETE FROM `item_budget_template` WHERE `template_id` = 467;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(467, 3, 4865),
(467, 5, 2432),
(467, 31, 2703);

DELETE FROM `item_budget_template` WHERE `template_id` = 468;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(468, 3, 7407),
(468, 5, 2593);

DELETE FROM `item_budget_template` WHERE `template_id` = 469;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(469, 3, 4375),
(469, 5, 1250),
(469, 32, 4375);

DELETE FROM `item_budget_template` WHERE `template_id` = 470;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(470, 5, 4390),
(470, 3, 4390),
(470, 4, 1220);

DELETE FROM `item_budget_template` WHERE `template_id` = 471;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(471, 5, 4985),
(471, 45, 5015);

DELETE FROM `item_budget_template` WHERE `template_id` = 472;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(472, 5, 3542),
(472, 4, 3542),
(472, 32, 2916);

DELETE FROM `item_budget_template` WHERE `template_id` = 473;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(473, 5, 6250),
(473, 6, 2500),
(473, 4, 1250);

DELETE FROM `item_budget_template` WHERE `template_id` = 474;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(474, 6, 5000),
(474, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 475;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(475, 5, 3466),
(475, 4, 1560),
(475, 32, 3640),
(475, 45, 1334);

DELETE FROM `item_budget_template` WHERE `template_id` = 476;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(476, 5, 3237),
(476, 4, 1874),
(476, 32, 3578),
(476, 45, 1311);

DELETE FROM `item_budget_template` WHERE `template_id` = 477;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(477, 5, 3105),
(477, 45, 3116),
(477, 32, 3779);

DELETE FROM `item_budget_template` WHERE `template_id` = 478;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(478, 5, 3121),
(478, 4, 2947),
(478, 3, 1560),
(478, 45, 2372);

DELETE FROM `item_budget_template` WHERE `template_id` = 479;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(479, 5, 5000),
(479, 6, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 480;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(480, 5, 5476),
(480, 6, 2857),
(480, 4, 1667);

DELETE FROM `item_budget_template` WHERE `template_id` = 481;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(481, 6, 3774),
(481, 5, 2830),
(481, 4, 2264),
(481, 3, 1132);

DELETE FROM `item_budget_template` WHERE `template_id` = 482;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(482, 5, 5556),
(482, 6, 2222),
(482, 4, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 483;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(483, 3, 3684),
(483, 5, 3421),
(483, 6, 1579),
(483, 4, 1316);

DELETE FROM `item_budget_template` WHERE `template_id` = 484;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(484, 3, 4667),
(484, 5, 3333),
(484, 6, 2000);

DELETE FROM `item_budget_template` WHERE `template_id` = 485;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(485, 3, 5000),
(485, 6, 3333),
(485, 4, 1667);

DELETE FROM `item_budget_template` WHERE `template_id` = 486;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(486, 3, 4211),
(486, 5, 3684),
(486, 6, 2105);

DELETE FROM `item_budget_template` WHERE `template_id` = 487;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(487, 5, 8571),
(487, 6, 1429);

DELETE FROM `item_budget_template` WHERE `template_id` = 488;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(488, 6, 5122),
(488, 5, 4878);

DELETE FROM `item_budget_template` WHERE `template_id` = 489;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(489, 5, 7949),
(489, 6, 2051);

DELETE FROM `item_budget_template` WHERE `template_id` = 490;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(490, 5, 7857),
(490, 6, 2143);

DELETE FROM `item_budget_template` WHERE `template_id` = 491;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(491, 5, 6154),
(491, 6, 3846);

DELETE FROM `item_budget_template` WHERE `template_id` = 492;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(492, 5, 6154),
(492, 6, 3846);

DELETE FROM `item_budget_template` WHERE `template_id` = 493;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(493, 6, 6053),
(493, 5, 3947);

DELETE FROM `item_budget_template` WHERE `template_id` = 494;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(494, 5, 7000),
(494, 6, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 495;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(495, 5, 6571),
(495, 6, 3429);

DELETE FROM `item_budget_template` WHERE `template_id` = 496;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(496, 6, 6000),
(496, 5, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 497;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(497, 5, 6176),
(497, 6, 3824);

DELETE FROM `item_budget_template` WHERE `template_id` = 498;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(498, 5, 6250),
(498, 6, 3750);

DELETE FROM `item_budget_template` WHERE `template_id` = 499;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(499, 5, 5000),
(499, 6, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 500;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(500, 3, 5263),
(500, 38, 3421),
(500, 32, 1316);

DELETE FROM `item_budget_template` WHERE `template_id` = 501;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(501, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 502;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(502, 3, 6757),
(502, 4, 3243);

DELETE FROM `item_budget_template` WHERE `template_id` = 503;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(503, 6, 3077),
(503, 5, 6923);

DELETE FROM `item_budget_template` WHERE `template_id` = 504;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(504, 5, 2642),
(504, 6, 2641),
(504, 4, 2453),
(504, 3, 2264);

DELETE FROM `item_budget_template` WHERE `template_id` = 505;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(505, 5, 4348),
(505, 6, 4348),
(505, 4, 1304);

DELETE FROM `item_budget_template` WHERE `template_id` = 506;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(506, 3, 6842),
(506, 31, 3158);

DELETE FROM `item_budget_template` WHERE `template_id` = 507;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(507, 5, 4324),
(507, 4, 3514),
(507, 6, 2162);

DELETE FROM `item_budget_template` WHERE `template_id` = 508;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(508, 4, 3023),
(508, 5, 3256),
(508, 6, 2326),
(508, 3, 1395);

DELETE FROM `item_budget_template` WHERE `template_id` = 509;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(509, 4, 4081),
(509, 5, 2449),
(509, 6, 1837),
(509, 3, 1633);

DELETE FROM `item_budget_template` WHERE `template_id` = 510;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(510, 5, 3793),
(510, 4, 3104),
(510, 6, 1724),
(510, 3, 1379);

DELETE FROM `item_budget_template` WHERE `template_id` = 511;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(511, 4, 4839),
(511, 3, 3226),
(511, 6, 1935);

DELETE FROM `item_budget_template` WHERE `template_id` = 512;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(512, 4, 4688),
(512, 3, 2812),
(512, 6, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 513;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(513, 4, 6053),
(513, 3, 2895),
(513, 6, 1052);

DELETE FROM `item_budget_template` WHERE `template_id` = 514;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(514, 4, 5500),
(514, 3, 4500);

DELETE FROM `item_budget_template` WHERE `template_id` = 515;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(515, 5, 3798),
(515, 6, 2468),
(515, 45, 3734);

DELETE FROM `item_budget_template` WHERE `template_id` = 516;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(516, 3, 5814),
(516, 4, 1395),
(516, 13, 2791);

DELETE FROM `item_budget_template` WHERE `template_id` = 517;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(517, 5, 3342),
(517, 6, 2273),
(517, 32, 1871),
(517, 45, 2514);

DELETE FROM `item_budget_template` WHERE `template_id` = 518;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(518, 5, 3150),
(518, 6, 2038),
(518, 32, 2594),
(518, 45, 2218);

DELETE FROM `item_budget_template` WHERE `template_id` = 519;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(519, 5, 3598),
(519, 6, 2840),
(519, 45, 3562);

DELETE FROM `item_budget_template` WHERE `template_id` = 520;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(520, 5, 5553),
(520, 6, 2150),
(520, 45, 2297);

DELETE FROM `item_budget_template` WHERE `template_id` = 521;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(521, 5, 4048),
(521, 6, 2491),
(521, 45, 3461);

DELETE FROM `item_budget_template` WHERE `template_id` = 522;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(522, 5, 4792),
(522, 6, 2282),
(522, 45, 2926);

DELETE FROM `item_budget_template` WHERE `template_id` = 523;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(523, 5, 5114),
(523, 6, 2224),
(523, 45, 2662);

DELETE FROM `item_budget_template` WHERE `template_id` = 524;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(524, 5, 3538),
(524, 6, 2831),
(524, 45, 3631);

DELETE FROM `item_budget_template` WHERE `template_id` = 525;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(525, 3, 3611),
(525, 4, 1667),
(525, 32, 1944),
(525, 31, 2778);

DELETE FROM `item_budget_template` WHERE `template_id` = 526;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(526, 3, 5814),
(526, 4, 1395),
(526, 13, 2791);

DELETE FROM `item_budget_template` WHERE `template_id` = 527;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(527, 3, 5128),
(527, 4, 4872);

DELETE FROM `item_budget_template` WHERE `template_id` = 528;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(528, 3, 4500),
(528, 4, 3167),
(528, 32, 2333);

DELETE FROM `item_budget_template` WHERE `template_id` = 529;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(529, 3, 5968),
(529, 4, 1774),
(529, 32, 2258);

DELETE FROM `item_budget_template` WHERE `template_id` = 530;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(530, 3, 4255),
(530, 4, 2766),
(530, 32, 2979);

DELETE FROM `item_budget_template` WHERE `template_id` = 531;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(531, 3, 6970),
(531, 31, 3030);

DELETE FROM `item_budget_template` WHERE `template_id` = 532;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(532, 5, 3260),
(532, 6, 2037),
(532, 45, 4703);

DELETE FROM `item_budget_template` WHERE `template_id` = 533;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(533, 5, 3013),
(533, 6, 1130),
(533, 32, 2637),
(533, 45, 3220);

DELETE FROM `item_budget_template` WHERE `template_id` = 534;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(534, 5, 4307),
(534, 6, 1160),
(534, 45, 4533);

DELETE FROM `item_budget_template` WHERE `template_id` = 535;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(535, 5, 3768),
(535, 6, 698),
(535, 45, 3580),
(535, 32, 1954);

DELETE FROM `item_budget_template` WHERE `template_id` = 536;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(536, 5, 3450),
(536, 6, 1061),
(536, 32, 1858),
(536, 45, 3631);

DELETE FROM `item_budget_template` WHERE `template_id` = 537;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(537, 5, 3026),
(537, 6, 2794),
(537, 45, 4180);

DELETE FROM `item_budget_template` WHERE `template_id` = 538;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(538, 5, 3822),
(538, 6, 2039),
(538, 45, 4139);

DELETE FROM `item_budget_template` WHERE `template_id` = 539;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(539, 5, 3384),
(539, 6, 3383),
(539, 45, 3233);

DELETE FROM `item_budget_template` WHERE `template_id` = 540;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(540, 5, 3343),
(540, 6, 2173),
(540, 32, 2340),
(540, 45, 2144);

DELETE FROM `item_budget_template` WHERE `template_id` = 541;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(541, 5, 3790),
(541, 6, 3089),
(541, 45, 3121);

DELETE FROM `item_budget_template` WHERE `template_id` = 542;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(542, 5, 3314),
(542, 6, 3313),
(542, 45, 3373);

DELETE FROM `item_budget_template` WHERE `template_id` = 543;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(543, 5, 3933),
(543, 6, 2331),
(543, 45, 3736);

DELETE FROM `item_budget_template` WHERE `template_id` = 544;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(544, 5, 5003),
(544, 6, 2602),
(544, 45, 2395);

DELETE FROM `item_budget_template` WHERE `template_id` = 545;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(545, 5, 5536),
(545, 6, 1916),
(545, 45, 2548);

DELETE FROM `item_budget_template` WHERE `template_id` = 546;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(546, 5, 2929),
(546, 6, 3604),
(546, 45, 3467);

DELETE FROM `item_budget_template` WHERE `template_id` = 547;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(547, 5, 3985),
(547, 6, 1406),
(547, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 548;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(548, 5, 3587),
(548, 45, 3066),
(548, 32, 3347);

DELETE FROM `item_budget_template` WHERE `template_id` = 549;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(549, 5, 3241),
(549, 6, 1216),
(549, 45, 5543);

DELETE FROM `item_budget_template` WHERE `template_id` = 550;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(550, 5, 2999),
(550, 6, 750),
(550, 45, 6251);

DELETE FROM `item_budget_template` WHERE `template_id` = 551;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(551, 5, 2448),
(551, 6, 1224),
(551, 32, 2142),
(551, 45, 4186);

DELETE FROM `item_budget_template` WHERE `template_id` = 552;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(552, 5, 3362),
(552, 6, 1552),
(552, 45, 5086);

DELETE FROM `item_budget_template` WHERE `template_id` = 553;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(553, 5, 1620),
(553, 6, 1215),
(553, 32, 2836),
(553, 45, 4329);

DELETE FROM `item_budget_template` WHERE `template_id` = 554;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(554, 5, 3688),
(554, 6, 2012),
(554, 45, 4300);

DELETE FROM `item_budget_template` WHERE `template_id` = 555;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(555, 3, 5714),
(555, 5, 2143),
(555, 6, 2143);

DELETE FROM `item_budget_template` WHERE `template_id` = 556;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(556, 3, 2692),
(556, 5, 2500),
(556, 6, 2116),
(556, 32, 2692);

DELETE FROM `item_budget_template` WHERE `template_id` = 557;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(557, 3, 3556),
(557, 5, 2889),
(557, 6, 1333),
(557, 31, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 558;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(558, 3, 3088),
(558, 5, 2206),
(558, 6, 1176),
(558, 31, 1471),
(558, 32, 2059);

DELETE FROM `item_budget_template` WHERE `template_id` = 559;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(559, 3, 3214),
(559, 5, 2857),
(559, 6, 1429),
(559, 32, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 560;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(560, 3, 2979),
(560, 5, 2766),
(560, 6, 1276),
(560, 32, 2979);

DELETE FROM `item_budget_template` WHERE `template_id` = 561;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(561, 3, 6250),
(561, 5, 1875),
(561, 6, 1875);

DELETE FROM `item_budget_template` WHERE `template_id` = 562;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(562, 3, 4035),
(562, 5, 2456),
(562, 6, 1053),
(562, 32, 2456);

DELETE FROM `item_budget_template` WHERE `template_id` = 563;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(563, 5, 6400),
(563, 6, 3600);

DELETE FROM `item_budget_template` WHERE `template_id` = 564;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(564, 5, 3274),
(564, 6, 2001),
(564, 32, 2547),
(564, 45, 2178);

DELETE FROM `item_budget_template` WHERE `template_id` = 565;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(565, 5, 4359),
(565, 6, 2051),
(565, 32, 3590);

DELETE FROM `item_budget_template` WHERE `template_id` = 566;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(566, 5, 2344),
(566, 6, 2604),
(566, 32, 1823),
(566, 45, 3229);

DELETE FROM `item_budget_template` WHERE `template_id` = 567;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(567, 5, 3873),
(567, 6, 1936),
(567, 32, 2259),
(567, 45, 1932);

DELETE FROM `item_budget_template` WHERE `template_id` = 568;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(568, 5, 4135),
(568, 6, 3162),
(568, 45, 2703);

DELETE FROM `item_budget_template` WHERE `template_id` = 569;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(569, 5, 3259),
(569, 6, 3258),
(569, 45, 3483);

DELETE FROM `item_budget_template` WHERE `template_id` = 570;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(570, 5, 4650),
(570, 6, 2400),
(570, 45, 2950);

DELETE FROM `item_budget_template` WHERE `template_id` = 571;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(571, 5, 2814),
(571, 6, 2501),
(571, 4, 2814),
(571, 45, 1871);

DELETE FROM `item_budget_template` WHERE `template_id` = 572;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(572, 5, 3727),
(572, 6, 1118),
(572, 4, 1491),
(572, 45, 3664);

DELETE FROM `item_budget_template` WHERE `template_id` = 573;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(573, 5, 3173),
(573, 6, 1360),
(573, 4, 2947),
(573, 45, 2520);

DELETE FROM `item_budget_template` WHERE `template_id` = 574;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(574, 5, 4569),
(574, 6, 846),
(574, 4, 1692),
(574, 45, 2893);

DELETE FROM `item_budget_template` WHERE `template_id` = 575;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(575, 5, 3135),
(575, 6, 818),
(575, 4, 2317),
(575, 45, 3730);

DELETE FROM `item_budget_template` WHERE `template_id` = 576;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(576, 5, 4462),
(576, 6, 1339),
(576, 4, 1338),
(576, 45, 2861);

DELETE FROM `item_budget_template` WHERE `template_id` = 577;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(577, 5, 2778),
(577, 6, 1588),
(577, 4, 2580),
(577, 45, 3054);

DELETE FROM `item_budget_template` WHERE `template_id` = 578;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(578, 5, 3313),
(578, 6, 789),
(578, 4, 2525),
(578, 45, 3373);

DELETE FROM `item_budget_template` WHERE `template_id` = 579;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(579, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 580;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(580, 4, 4445),
(580, 15, 3333),
(580, 12, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 581;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(581, 4, 5652),
(581, 12, 4348);

DELETE FROM `item_budget_template` WHERE `template_id` = 582;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(582, 4, 3220),
(582, 13, 4068),
(582, 12, 2712);

DELETE FROM `item_budget_template` WHERE `template_id` = 583;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(583, 4, 5152),
(583, 12, 4848);

DELETE FROM `item_budget_template` WHERE `template_id` = 584;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(584, 4, 3333),
(584, 14, 4445),
(584, 12, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 585;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(585, 4, 5652),
(585, 12, 4348);

DELETE FROM `item_budget_template` WHERE `template_id` = 586;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(586, 4, 5152),
(586, 12, 4848);

DELETE FROM `item_budget_template` WHERE `template_id` = 587;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(587, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 588;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(588, 6, 5000),
(588, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 589;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(589, 13, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 590;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(590, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 591;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(591, 3, 6000),
(591, 4, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 592;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(592, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 593;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(593, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 594;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(594, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 595;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(595, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 596;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(596, 3, 3750),
(596, 31, 6250);

DELETE FROM `item_budget_template` WHERE `template_id` = 597;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(597, 4, 2727),
(597, 13, 3637),
(597, 12, 3636);

DELETE FROM `item_budget_template` WHERE `template_id` = 598;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(598, 15, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 599;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(599, 6, 4231),
(599, 5, 5769);

DELETE FROM `item_budget_template` WHERE `template_id` = 600;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(600, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 601;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(601, 5, 1718),
(601, 32, 2406),
(601, 45, 5876);

DELETE FROM `item_budget_template` WHERE `template_id` = 602;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(602, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 603;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(603, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 604;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(604, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 605;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(605, 5, 5868),
(605, 45, 4132);

DELETE FROM `item_budget_template` WHERE `template_id` = 606;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(606, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 607;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(607, 5, 1993),
(607, 32, 2326),
(607, 45, 5681);

DELETE FROM `item_budget_template` WHERE `template_id` = 608;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(608, 5, 3187),
(608, 45, 6813);

DELETE FROM `item_budget_template` WHERE `template_id` = 609;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(609, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 610;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(610, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 611;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(611, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 612;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(612, 5, 2826),
(612, 6, 2825),
(612, 45, 4349);

DELETE FROM `item_budget_template` WHERE `template_id` = 613;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(613, 5, 5000),
(613, 6, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 614;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(614, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 615;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(615, 5, 3471),
(615, 45, 6529);

DELETE FROM `item_budget_template` WHERE `template_id` = 616;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(616, 5, 4801),
(616, 45, 5199);

DELETE FROM `item_budget_template` WHERE `template_id` = 617;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(617, 6, 3000),
(617, 5, 7000);

DELETE FROM `item_budget_template` WHERE `template_id` = 618;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(618, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 619;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(619, 6, 3704),
(619, 5, 6296);

DELETE FROM `item_budget_template` WHERE `template_id` = 620;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(620, 5, 5938),
(620, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 621;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(621, 5, 5938),
(621, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 622;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(622, 5, 5938),
(622, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 623;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(623, 5, 5938),
(623, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 624;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(624, 5, 5938),
(624, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 625;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(625, 5, 3519),
(625, 45, 6481);

DELETE FROM `item_budget_template` WHERE `template_id` = 626;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(626, 5, 5938),
(626, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 627;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(627, 5, 5938),
(627, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 628;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(628, 6, 3704),
(628, 5, 6296);

DELETE FROM `item_budget_template` WHERE `template_id` = 629;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(629, 6, 3000),
(629, 5, 7000);

DELETE FROM `item_budget_template` WHERE `template_id` = 630;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(630, 5, 5938),
(630, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 631;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(631, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 632;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(632, 5, 4673),
(632, 45, 5327);

DELETE FROM `item_budget_template` WHERE `template_id` = 633;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(633, 5, 3752),
(633, 45, 6248);

DELETE FROM `item_budget_template` WHERE `template_id` = 634;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(634, 5, 4430),
(634, 45, 5570);

DELETE FROM `item_budget_template` WHERE `template_id` = 635;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(635, 5, 4673),
(635, 45, 5327);

DELETE FROM `item_budget_template` WHERE `template_id` = 636;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(636, 5, 6552),
(636, 6, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 637;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(637, 5, 3690),
(637, 45, 6310);

DELETE FROM `item_budget_template` WHERE `template_id` = 638;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(638, 5, 1896),
(638, 45, 8104);

DELETE FROM `item_budget_template` WHERE `template_id` = 639;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(639, 5, 6053),
(639, 6, 3947);

DELETE FROM `item_budget_template` WHERE `template_id` = 640;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(640, 5, 3690),
(640, 45, 6310);

DELETE FROM `item_budget_template` WHERE `template_id` = 641;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(641, 5, 6552),
(641, 6, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 642;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(642, 5, 1896),
(642, 45, 8104);

DELETE FROM `item_budget_template` WHERE `template_id` = 643;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(643, 5, 6053),
(643, 6, 3947);

DELETE FROM `item_budget_template` WHERE `template_id` = 644;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(644, 5, 4430),
(644, 45, 5570);

DELETE FROM `item_budget_template` WHERE `template_id` = 645;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(645, 5, 4673),
(645, 45, 5327);

DELETE FROM `item_budget_template` WHERE `template_id` = 646;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(646, 5, 4673),
(646, 45, 5327);

DELETE FROM `item_budget_template` WHERE `template_id` = 647;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(647, 5, 3752),
(647, 45, 6248);

DELETE FROM `item_budget_template` WHERE `template_id` = 648;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(648, 5, 5938),
(648, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 649;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(649, 6, 3000),
(649, 5, 7000);

DELETE FROM `item_budget_template` WHERE `template_id` = 650;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(650, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 651;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(651, 6, 3704),
(651, 5, 6296);

DELETE FROM `item_budget_template` WHERE `template_id` = 652;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(652, 5, 5938),
(652, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 653;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(653, 5, 2873),
(653, 6, 3536),
(653, 45, 3591);

DELETE FROM `item_budget_template` WHERE `template_id` = 654;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(654, 5, 5938),
(654, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 655;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(655, 5, 5938),
(655, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 656;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(656, 5, 4981),
(656, 45, 5019);

DELETE FROM `item_budget_template` WHERE `template_id` = 657;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(657, 5, 4342),
(657, 45, 5658);

DELETE FROM `item_budget_template` WHERE `template_id` = 658;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(658, 5, 4834),
(658, 45, 5166);

DELETE FROM `item_budget_template` WHERE `template_id` = 659;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(659, 5, 4981),
(659, 45, 5019);

DELETE FROM `item_budget_template` WHERE `template_id` = 660;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(660, 5, 6552),
(660, 6, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 661;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(661, 5, 4779),
(661, 45, 5221);

DELETE FROM `item_budget_template` WHERE `template_id` = 662;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(662, 5, 3980),
(662, 45, 6020);

DELETE FROM `item_budget_template` WHERE `template_id` = 663;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(663, 5, 6053),
(663, 6, 3947);

DELETE FROM `item_budget_template` WHERE `template_id` = 664;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(664, 5, 5938),
(664, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 665;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(665, 5, 2873),
(665, 6, 3536),
(665, 45, 3591);

DELETE FROM `item_budget_template` WHERE `template_id` = 666;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(666, 5, 5938),
(666, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 667;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(667, 5, 5938),
(667, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 668;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(668, 6, 3704),
(668, 5, 6296);

DELETE FROM `item_budget_template` WHERE `template_id` = 669;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(669, 6, 3000),
(669, 5, 7000);

DELETE FROM `item_budget_template` WHERE `template_id` = 670;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(670, 5, 5938),
(670, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 671;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(671, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 672;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(672, 5, 4779),
(672, 45, 5221);

DELETE FROM `item_budget_template` WHERE `template_id` = 673;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(673, 5, 6552),
(673, 6, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 674;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(674, 5, 3980),
(674, 45, 6020);

DELETE FROM `item_budget_template` WHERE `template_id` = 675;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(675, 5, 6053),
(675, 6, 3947);

DELETE FROM `item_budget_template` WHERE `template_id` = 676;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(676, 5, 4834),
(676, 45, 5166);

DELETE FROM `item_budget_template` WHERE `template_id` = 677;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(677, 5, 4981),
(677, 45, 5019);

DELETE FROM `item_budget_template` WHERE `template_id` = 678;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(678, 5, 4981),
(678, 45, 5019);

DELETE FROM `item_budget_template` WHERE `template_id` = 679;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(679, 5, 4342),
(679, 45, 5658);

DELETE FROM `item_budget_template` WHERE `template_id` = 680;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(680, 5, 5556),
(680, 6, 4444);

DELETE FROM `item_budget_template` WHERE `template_id` = 681;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(681, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 682;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(682, 5, 2946),
(682, 45, 7054);

DELETE FROM `item_budget_template` WHERE `template_id` = 683;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(683, 5, 5097),
(683, 45, 4903);

DELETE FROM `item_budget_template` WHERE `template_id` = 684;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(684, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 685;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(685, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 686;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(686, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 687;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(687, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 688;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(688, 13, 4615),
(688, 32, 5385);

DELETE FROM `item_budget_template` WHERE `template_id` = 689;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(689, 5, 3748),
(689, 6, 2307),
(689, 45, 3945);

DELETE FROM `item_budget_template` WHERE `template_id` = 690;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(690, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 691;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(691, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 692;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(692, 4, 3030),
(692, 6, 2727),
(692, 32, 4243);

DELETE FROM `item_budget_template` WHERE `template_id` = 693;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(693, 5, 3030),
(693, 6, 2727),
(693, 32, 4243);

DELETE FROM `item_budget_template` WHERE `template_id` = 694;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(694, 5, 3030),
(694, 6, 2727),
(694, 32, 4243);

DELETE FROM `item_budget_template` WHERE `template_id` = 695;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(695, 5, 3030),
(695, 6, 2727),
(695, 32, 4243);

DELETE FROM `item_budget_template` WHERE `template_id` = 696;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(696, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 697;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(697, 5, 4380),
(697, 6, 1314),
(697, 45, 4306);

DELETE FROM `item_budget_template` WHERE `template_id` = 698;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(698, 3, 5000),
(698, 4, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 699;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(699, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 700;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(700, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 701;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(701, 3, 2963),
(701, 4, 2593),
(701, 13, 4444);

DELETE FROM `item_budget_template` WHERE `template_id` = 702;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(702, 5, 3376),
(702, 6, 2110),
(702, 3, 1266),
(702, 45, 3248);

DELETE FROM `item_budget_template` WHERE `template_id` = 703;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(703, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 704;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(704, 4, 3947),
(704, 3, 2369),
(704, 32, 3684);

DELETE FROM `item_budget_template` WHERE `template_id` = 705;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(705, 3, 6000),
(705, 12, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 706;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(706, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 707;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(707, 4, 5152),
(707, 5, 1818),
(707, 12, 3030);

DELETE FROM `item_budget_template` WHERE `template_id` = 708;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(708, 5, 3164),
(708, 6, 1217),
(708, 45, 5619);

DELETE FROM `item_budget_template` WHERE `template_id` = 709;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(709, 5, 5153),
(709, 45, 4847);

DELETE FROM `item_budget_template` WHERE `template_id` = 710;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(710, 5, 5172),
(710, 32, 4828);

DELETE FROM `item_budget_template` WHERE `template_id` = 711;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(711, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 712;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(712, 5, 4789),
(712, 45, 5211);

DELETE FROM `item_budget_template` WHERE `template_id` = 713;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(713, 5, 4255),
(713, 6, 2766),
(713, 32, 2979);

DELETE FROM `item_budget_template` WHERE `template_id` = 714;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(714, 5, 4801),
(714, 45, 5199);

DELETE FROM `item_budget_template` WHERE `template_id` = 715;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(715, 37, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 716;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(716, 3, 3784),
(716, 5, 2432),
(716, 32, 3784);

DELETE FROM `item_budget_template` WHERE `template_id` = 717;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(717, 5, 4471),
(717, 6, 2981),
(717, 45, 2548);

DELETE FROM `item_budget_template` WHERE `template_id` = 718;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(718, 5, 4381),
(718, 45, 5619);

DELETE FROM `item_budget_template` WHERE `template_id` = 719;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(719, 5, 5882),
(719, 6, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 720;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(720, 5, 6364),
(720, 6, 3636);

DELETE FROM `item_budget_template` WHERE `template_id` = 721;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(721, 3, 6364),
(721, 4, 3636);

DELETE FROM `item_budget_template` WHERE `template_id` = 722;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(722, 5, 3750),
(722, 6, 1875),
(722, 32, 4375);

DELETE FROM `item_budget_template` WHERE `template_id` = 723;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(723, 3, 3333),
(723, 31, 2778),
(723, 32, 3889);

DELETE FROM `item_budget_template` WHERE `template_id` = 724;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(724, 5, 6410),
(724, 32, 3590);

DELETE FROM `item_budget_template` WHERE `template_id` = 725;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(725, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 726;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(726, 5, 2805),
(726, 45, 7195);

DELETE FROM `item_budget_template` WHERE `template_id` = 727;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(727, 5, 5161),
(727, 6, 4839);

DELETE FROM `item_budget_template` WHERE `template_id` = 728;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(728, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 729;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(729, 4, 6818),
(729, 32, 3182);

DELETE FROM `item_budget_template` WHERE `template_id` = 730;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(730, 3, 3962),
(730, 5, 1698),
(730, 6, 1698),
(730, 32, 2642);

DELETE FROM `item_budget_template` WHERE `template_id` = 731;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(731, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 732;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(732, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 733;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(733, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 734;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(734, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 735;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(735, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 736;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(736, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 737;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(737, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 738;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(738, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 739;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(739, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 740;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(740, 5, 7368),
(740, 6, 2632);

DELETE FROM `item_budget_template` WHERE `template_id` = 741;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(741, 5, 6757),
(741, 6, 3243);

DELETE FROM `item_budget_template` WHERE `template_id` = 742;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(742, 5, 2809),
(742, 6, 1686),
(742, 32, 2622),
(742, 45, 2883);

DELETE FROM `item_budget_template` WHERE `template_id` = 743;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(743, 4, 5172),
(743, 6, 1724),
(743, 12, 3104);

DELETE FROM `item_budget_template` WHERE `template_id` = 744;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(744, 5, 2826),
(744, 6, 2825),
(744, 45, 4349);

DELETE FROM `item_budget_template` WHERE `template_id` = 745;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(745, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 746;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(746, 5, 4167),
(746, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 747;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(747, 5, 3808),
(747, 6, 2285),
(747, 45, 3907);

DELETE FROM `item_budget_template` WHERE `template_id` = 748;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(748, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 749;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(749, 15, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 750;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(750, 3, 6000),
(750, 31, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 751;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(751, 14, 6667),
(751, 12, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 752;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(752, 4, 5161),
(752, 12, 4839);

DELETE FROM `item_budget_template` WHERE `template_id` = 753;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(753, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 754;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(754, 37, 4615),
(754, 32, 5385);

DELETE FROM `item_budget_template` WHERE `template_id` = 755;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(755, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 756;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(756, 5, 3640),
(756, 6, 2730),
(756, 45, 3630);

DELETE FROM `item_budget_template` WHERE `template_id` = 757;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(757, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 758;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(758, 5, 3471),
(758, 45, 6529);

DELETE FROM `item_budget_template` WHERE `template_id` = 759;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(759, 3, 5862),
(759, 13, 4138);

DELETE FROM `item_budget_template` WHERE `template_id` = 760;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(760, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 761;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(761, 4, 5862),
(761, 13, 4138);

DELETE FROM `item_budget_template` WHERE `template_id` = 762;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(762, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 763;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(763, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 764;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(764, 3, 3415),
(764, 5, 3171),
(764, 32, 3414);

DELETE FROM `item_budget_template` WHERE `template_id` = 765;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(765, 5, 3959),
(765, 6, 1979),
(765, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 766;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(766, 5, 4186),
(766, 6, 2558),
(766, 32, 3256);

DELETE FROM `item_budget_template` WHERE `template_id` = 767;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(767, 5, 1511),
(767, 6, 1511),
(767, 45, 6978);

DELETE FROM `item_budget_template` WHERE `template_id` = 768;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(768, 5, 3441),
(768, 6, 2815),
(768, 45, 3744);

DELETE FROM `item_budget_template` WHERE `template_id` = 769;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(769, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 770;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(770, 3, 4000),
(770, 5, 1600),
(770, 4, 1600),
(770, 32, 2800);

DELETE FROM `item_budget_template` WHERE `template_id` = 771;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(771, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 772;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(772, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 773;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(773, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 774;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(774, 5, 2561),
(774, 6, 1281),
(774, 32, 2561),
(774, 45, 3597);

DELETE FROM `item_budget_template` WHERE `template_id` = 775;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(775, 4, 4717),
(775, 32, 5283);

DELETE FROM `item_budget_template` WHERE `template_id` = 776;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(776, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 777;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(777, 4, 2592),
(777, 3, 3704),
(777, 14, 3704);

DELETE FROM `item_budget_template` WHERE `template_id` = 778;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(778, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 779;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(779, 5, 3822),
(779, 6, 2229),
(779, 45, 3949);

DELETE FROM `item_budget_template` WHERE `template_id` = 780;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(780, 5, 4746),
(780, 6, 2657),
(780, 45, 2597);

DELETE FROM `item_budget_template` WHERE `template_id` = 781;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(781, 3, 3500),
(781, 4, 3500),
(781, 12, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 782;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(782, 5, 2608),
(782, 6, 1009),
(782, 32, 2355),
(782, 45, 4028);

DELETE FROM `item_budget_template` WHERE `template_id` = 783;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(783, 5, 3930),
(783, 45, 6070);

DELETE FROM `item_budget_template` WHERE `template_id` = 784;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(784, 5, 2079),
(784, 6, 2079),
(784, 45, 5842);

DELETE FROM `item_budget_template` WHERE `template_id` = 785;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(785, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 786;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(786, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 787;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(787, 5, 4834),
(787, 45, 5166);

DELETE FROM `item_budget_template` WHERE `template_id` = 788;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(788, 5, 2243),
(788, 6, 2243),
(788, 45, 5514);

DELETE FROM `item_budget_template` WHERE `template_id` = 789;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(789, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 790;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(790, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 791;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(791, 3, 6786),
(791, 5, 3214);

DELETE FROM `item_budget_template` WHERE `template_id` = 792;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(792, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 793;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(793, 14, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 794;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(794, 5, 3385),
(794, 45, 6615);

DELETE FROM `item_budget_template` WHERE `template_id` = 795;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(795, 5, 3640),
(795, 6, 2730),
(795, 45, 3630);

DELETE FROM `item_budget_template` WHERE `template_id` = 796;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(796, 5, 8500),
(796, 6, 1500);

DELETE FROM `item_budget_template` WHERE `template_id` = 797;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(797, 5, 2984),
(797, 45, 7016);

DELETE FROM `item_budget_template` WHERE `template_id` = 798;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(798, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 799;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(799, 5, 3488),
(799, 32, 6512);

DELETE FROM `item_budget_template` WHERE `template_id` = 800;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(800, 3, 5200),
(800, 13, 4800);

DELETE FROM `item_budget_template` WHERE `template_id` = 801;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(801, 5, 5745),
(801, 6, 1988),
(801, 45, 2267);

DELETE FROM `item_budget_template` WHERE `template_id` = 802;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(802, 4, 5714),
(802, 6, 4286);

DELETE FROM `item_budget_template` WHERE `template_id` = 803;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(803, 5, 4000),
(803, 6, 2500),
(803, 32, 3500);

DELETE FROM `item_budget_template` WHERE `template_id` = 804;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(804, 5, 1895),
(804, 6, 1895),
(804, 45, 6210);

DELETE FROM `item_budget_template` WHERE `template_id` = 805;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(805, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 806;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(806, 6, 2805),
(806, 45, 7195);

DELETE FROM `item_budget_template` WHERE `template_id` = 807;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(807, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 808;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(808, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 809;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(809, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 810;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(810, 5, 3236),
(810, 45, 6764);

DELETE FROM `item_budget_template` WHERE `template_id` = 811;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(811, 3, 7500),
(811, 31, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 812;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(812, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 813;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(813, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 814;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(814, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 815;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(815, 5, 3703),
(815, 6, 3395),
(815, 45, 2902);

DELETE FROM `item_budget_template` WHERE `template_id` = 816;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(816, 5, 5217),
(816, 6, 4783);

DELETE FROM `item_budget_template` WHERE `template_id` = 817;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(817, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 818;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(818, 4, 7059),
(818, 12, 2941);

DELETE FROM `item_budget_template` WHERE `template_id` = 819;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(819, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 820;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(820, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 821;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(821, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 822;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(822, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 823;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(823, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 824;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(824, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 825;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(825, 5, 2694),
(825, 6, 2309),
(825, 32, 2694),
(825, 45, 2303);

DELETE FROM `item_budget_template` WHERE `template_id` = 826;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(826, 5, 4226),
(826, 6, 1780),
(826, 45, 3994);

DELETE FROM `item_budget_template` WHERE `template_id` = 827;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(827, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 828;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(828, 5, 2390),
(828, 6, 1991),
(828, 45, 5619);

DELETE FROM `item_budget_template` WHERE `template_id` = 829;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(829, 5, 5294),
(829, 6, 4706);

DELETE FROM `item_budget_template` WHERE `template_id` = 830;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(830, 3, 5429),
(830, 5, 1714),
(830, 31, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 831;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(831, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 832;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(832, 5, 1941),
(832, 45, 8059);

DELETE FROM `item_budget_template` WHERE `template_id` = 833;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(833, 5, 1957),
(833, 6, 1956),
(833, 32, 6087);

DELETE FROM `item_budget_template` WHERE `template_id` = 834;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(834, 4, 2632),
(834, 32, 7368);

DELETE FROM `item_budget_template` WHERE `template_id` = 835;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(835, 4, 6885),
(835, 37, 3115);

DELETE FROM `item_budget_template` WHERE `template_id` = 836;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(836, 4, 3658),
(836, 37, 2927),
(836, 32, 3415);

DELETE FROM `item_budget_template` WHERE `template_id` = 837;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(837, 5, 4775),
(837, 6, 3184),
(837, 45, 2041);

DELETE FROM `item_budget_template` WHERE `template_id` = 838;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(838, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 839;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(839, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 840;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(840, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 841;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(841, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 842;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(842, 5, 2541),
(842, 6, 1483),
(842, 45, 5976);

DELETE FROM `item_budget_template` WHERE `template_id` = 843;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(843, 4, 6500),
(843, 32, 3500);

DELETE FROM `item_budget_template` WHERE `template_id` = 844;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(844, 4, 6500),
(844, 32, 3500);

DELETE FROM `item_budget_template` WHERE `template_id` = 845;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(845, 4, 2813),
(845, 3, 2812),
(845, 32, 4375);

DELETE FROM `item_budget_template` WHERE `template_id` = 846;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(846, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 847;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(847, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 848;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(848, 5, 3730),
(848, 6, 1411),
(848, 32, 1411),
(848, 45, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 849;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(849, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 850;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(850, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 851;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(851, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 852;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(852, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 853;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(853, 4, 6000),
(853, 13, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 854;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(854, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 855;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(855, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 856;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(856, 4, 6500),
(856, 32, 3500);

DELETE FROM `item_budget_template` WHERE `template_id` = 857;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(857, 4, 6500),
(857, 32, 3500);

DELETE FROM `item_budget_template` WHERE `template_id` = 858;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(858, 4, 6500),
(858, 32, 3500);

DELETE FROM `item_budget_template` WHERE `template_id` = 859;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(859, 5, 5189),
(859, 6, 1557),
(859, 45, 3254);

DELETE FROM `item_budget_template` WHERE `template_id` = 860;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(860, 4, 6500),
(860, 32, 3500);

DELETE FROM `item_budget_template` WHERE `template_id` = 861;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(861, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 862;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(862, 5, 2284),
(862, 6, 1688),
(862, 45, 6028);

DELETE FROM `item_budget_template` WHERE `template_id` = 863;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(863, 5, 2284),
(863, 6, 1688),
(863, 45, 6028);

DELETE FROM `item_budget_template` WHERE `template_id` = 864;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(864, 5, 3775),
(864, 45, 6225);

DELETE FROM `item_budget_template` WHERE `template_id` = 865;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(865, 4, 6500),
(865, 32, 3500);

DELETE FROM `item_budget_template` WHERE `template_id` = 866;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(866, 4, 6500),
(866, 32, 3500);

DELETE FROM `item_budget_template` WHERE `template_id` = 867;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(867, 5, 4985),
(867, 45, 5015);

DELETE FROM `item_budget_template` WHERE `template_id` = 868;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(868, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 869;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(869, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 870;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(870, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 871;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(871, 13, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 872;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(872, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 873;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(873, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 874;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(874, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 875;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(875, 3, 2800),
(875, 4, 7200);

DELETE FROM `item_budget_template` WHERE `template_id` = 876;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(876, 3, 5000),
(876, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 877;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(877, 3, 4762),
(877, 4, 5238);

DELETE FROM `item_budget_template` WHERE `template_id` = 878;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(878, 5, 3939),
(878, 45, 6061);

DELETE FROM `item_budget_template` WHERE `template_id` = 879;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(879, 3, 2800),
(879, 4, 7200);

DELETE FROM `item_budget_template` WHERE `template_id` = 880;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(880, 3, 5000),
(880, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 881;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(881, 3, 4762),
(881, 4, 5238);

DELETE FROM `item_budget_template` WHERE `template_id` = 882;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(882, 5, 3939),
(882, 45, 6061);

DELETE FROM `item_budget_template` WHERE `template_id` = 883;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(883, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 884;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(884, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 885;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(885, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 886;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(886, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 887;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(887, 5, 5551),
(887, 45, 4449);

DELETE FROM `item_budget_template` WHERE `template_id` = 888;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(888, 5, 5551),
(888, 45, 4449);

DELETE FROM `item_budget_template` WHERE `template_id` = 889;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(889, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 890;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(890, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 891;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(891, 5, 2560),
(891, 45, 7440);

DELETE FROM `item_budget_template` WHERE `template_id` = 892;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(892, 3, 6176),
(892, 4, 3824);

DELETE FROM `item_budget_template` WHERE `template_id` = 893;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(893, 3, 4667),
(893, 4, 5333);

DELETE FROM `item_budget_template` WHERE `template_id` = 894;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(894, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 895;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(895, 5, 4936),
(895, 45, 5064);

DELETE FROM `item_budget_template` WHERE `template_id` = 896;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(896, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 897;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(897, 5, 6250),
(897, 6, 3750);

DELETE FROM `item_budget_template` WHERE `template_id` = 898;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(898, 3, 4783),
(898, 4, 5217);

DELETE FROM `item_budget_template` WHERE `template_id` = 899;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(899, 3, 5333),
(899, 4, 4667);

DELETE FROM `item_budget_template` WHERE `template_id` = 900;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(900, 5, 3385),
(900, 45, 6615);

DELETE FROM `item_budget_template` WHERE `template_id` = 901;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(901, 5, 2677),
(901, 45, 7323);

DELETE FROM `item_budget_template` WHERE `template_id` = 902;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(902, 5, 2032),
(902, 6, 1887),
(902, 45, 6081);

DELETE FROM `item_budget_template` WHERE `template_id` = 903;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(903, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 904;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(904, 5, 4094),
(904, 32, 3184),
(904, 45, 2722);

DELETE FROM `item_budget_template` WHERE `template_id` = 905;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(905, 5, 3114),
(905, 45, 4161),
(905, 32, 2725);

DELETE FROM `item_budget_template` WHERE `template_id` = 906;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(906, 4, 5636),
(906, 32, 2546),
(906, 31, 1818);

DELETE FROM `item_budget_template` WHERE `template_id` = 907;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(907, 5, 6970),
(907, 6, 3030);

DELETE FROM `item_budget_template` WHERE `template_id` = 908;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(908, 5, 3596),
(908, 45, 6404);

DELETE FROM `item_budget_template` WHERE `template_id` = 909;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(909, 5, 6907),
(909, 45, 3093);

DELETE FROM `item_budget_template` WHERE `template_id` = 910;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(910, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 911;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(911, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 912;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(912, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 913;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(913, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 914;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(914, 5, 3619),
(914, 45, 6381);

DELETE FROM `item_budget_template` WHERE `template_id` = 915;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(915, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 916;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(916, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 917;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(917, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 918;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(918, 4, 7143),
(918, 32, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 919;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(919, 14, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 920;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(920, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 921;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(921, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 922;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(922, 5, 2732),
(922, 45, 7268);

DELETE FROM `item_budget_template` WHERE `template_id` = 923;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(923, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 924;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(924, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 925;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(925, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 926;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(926, 4, 4043),
(926, 32, 5957);

DELETE FROM `item_budget_template` WHERE `template_id` = 927;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(927, 32, 5833),
(927, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 928;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(928, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 929;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(929, 4, 5625),
(929, 12, 4375);

DELETE FROM `item_budget_template` WHERE `template_id` = 930;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(930, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 931;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(931, 5, 2370),
(931, 45, 7630);

DELETE FROM `item_budget_template` WHERE `template_id` = 932;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(932, 5, 4240),
(932, 6, 1496),
(932, 45, 4264);

DELETE FROM `item_budget_template` WHERE `template_id` = 933;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(933, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 934;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(934, 37, 3103),
(934, 14, 6897);

DELETE FROM `item_budget_template` WHERE `template_id` = 935;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(935, 3, 5000),
(935, 4, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 936;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(936, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 937;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(937, 4, 3443),
(937, 14, 6557);

DELETE FROM `item_budget_template` WHERE `template_id` = 938;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(938, 5, 3814),
(938, 6, 1621),
(938, 45, 4565);

DELETE FROM `item_budget_template` WHERE `template_id` = 939;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(939, 5, 1975),
(939, 6, 1226),
(939, 32, 1907),
(939, 45, 4892);

DELETE FROM `item_budget_template` WHERE `template_id` = 940;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(940, 4, 4559),
(940, 5, 2941),
(940, 6, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 941;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(941, 4, 4909),
(941, 32, 5091);

DELETE FROM `item_budget_template` WHERE `template_id` = 942;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(942, 5, 1840),
(942, 6, 818),
(942, 45, 7342);

DELETE FROM `item_budget_template` WHERE `template_id` = 943;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(943, 3, 6400),
(943, 4, 3600);

DELETE FROM `item_budget_template` WHERE `template_id` = 944;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(944, 4, 4815),
(944, 32, 5185);

DELETE FROM `item_budget_template` WHERE `template_id` = 945;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(945, 5, 3690),
(945, 45, 6310);

DELETE FROM `item_budget_template` WHERE `template_id` = 946;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(946, 5, 7005),
(946, 45, 2995);

DELETE FROM `item_budget_template` WHERE `template_id` = 947;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(947, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 948;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(948, 5, 2727),
(948, 6, 7273);

DELETE FROM `item_budget_template` WHERE `template_id` = 949;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(949, 5, 3550),
(949, 45, 6450);

DELETE FROM `item_budget_template` WHERE `template_id` = 950;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(950, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 951;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(951, 4, 5000),
(951, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 952;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(952, 3, 5313),
(952, 5, 4687);

DELETE FROM `item_budget_template` WHERE `template_id` = 953;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(953, 5, 3162),
(953, 31, 2108),
(953, 45, 4730);

DELETE FROM `item_budget_template` WHERE `template_id` = 954;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(954, 5, 2640),
(954, 6, 990),
(954, 45, 3291),
(954, 32, 3079);

DELETE FROM `item_budget_template` WHERE `template_id` = 955;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(955, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 956;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(956, 3, 7143),
(956, 31, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 957;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(957, 5, 3690),
(957, 45, 6310);

DELETE FROM `item_budget_template` WHERE `template_id` = 958;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(958, 5, 3158),
(958, 6, 3158),
(958, 32, 3684);

DELETE FROM `item_budget_template` WHERE `template_id` = 959;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(959, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 960;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(960, 5, 2276),
(960, 6, 2276),
(960, 45, 5448);

DELETE FROM `item_budget_template` WHERE `template_id` = 961;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(961, 3, 5833),
(961, 12, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 962;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(962, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 963;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(963, 5, 1411),
(963, 6, 2822),
(963, 45, 4121),
(963, 32, 1646);

DELETE FROM `item_budget_template` WHERE `template_id` = 964;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(964, 13, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 965;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(965, 3, 4000),
(965, 4, 4000),
(965, 31, 2000);

DELETE FROM `item_budget_template` WHERE `template_id` = 966;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(966, 5, 4082),
(966, 6, 2653),
(966, 31, 3265);

DELETE FROM `item_budget_template` WHERE `template_id` = 967;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(967, 5, 5882),
(967, 32, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 968;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(968, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 969;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(969, 4, 3333),
(969, 5, 2833),
(969, 6, 2167),
(969, 3, 1667);

DELETE FROM `item_budget_template` WHERE `template_id` = 970;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(970, 4, 2496),
(970, 5, 2496),
(970, 6, 2340),
(970, 45, 2668);

DELETE FROM `item_budget_template` WHERE `template_id` = 971;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(971, 3, 3846),
(971, 4, 3846),
(971, 13, 2308);

DELETE FROM `item_budget_template` WHERE `template_id` = 972;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(972, 13, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 973;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(973, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 974;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(974, 5, 5641),
(974, 6, 4359);

DELETE FROM `item_budget_template` WHERE `template_id` = 975;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(975, 5, 2862),
(975, 45, 7138);

DELETE FROM `item_budget_template` WHERE `template_id` = 976;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(976, 5, 3143),
(976, 6, 1714),
(976, 32, 4000),
(976, 31, 1143);

DELETE FROM `item_budget_template` WHERE `template_id` = 977;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(977, 4, 4179),
(977, 3, 3284),
(977, 5, 2537);

DELETE FROM `item_budget_template` WHERE `template_id` = 978;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(978, 5, 3162),
(978, 31, 2108),
(978, 45, 4730);

DELETE FROM `item_budget_template` WHERE `template_id` = 979;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(979, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 980;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(980, 5, 2862),
(980, 45, 7138);

DELETE FROM `item_budget_template` WHERE `template_id` = 981;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(981, 6, 2984),
(981, 45, 7016);

DELETE FROM `item_budget_template` WHERE `template_id` = 982;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(982, 5, 4168),
(982, 45, 5832);

DELETE FROM `item_budget_template` WHERE `template_id` = 983;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(983, 4, 3529),
(983, 3, 6471);

DELETE FROM `item_budget_template` WHERE `template_id` = 984;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(984, 3, 5862),
(984, 5, 4138);

DELETE FROM `item_budget_template` WHERE `template_id` = 985;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(985, 5, 2063),
(985, 45, 7937);

DELETE FROM `item_budget_template` WHERE `template_id` = 986;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(986, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 987;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(987, 3, 5000),
(987, 4, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 988;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(988, 5, 2298),
(988, 6, 2298),
(988, 45, 5404);

DELETE FROM `item_budget_template` WHERE `template_id` = 989;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(989, 5, 2489),
(989, 45, 5852),
(989, 31, 1659);

DELETE FROM `item_budget_template` WHERE `template_id` = 990;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(990, 3, 6552),
(990, 4, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 991;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(991, 4, 5217),
(991, 3, 4783);

DELETE FROM `item_budget_template` WHERE `template_id` = 992;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(992, 4, 5217),
(992, 3, 4783);

DELETE FROM `item_budget_template` WHERE `template_id` = 993;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(993, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 994;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(994, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 995;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(995, 6, 4006),
(995, 45, 5994);

DELETE FROM `item_budget_template` WHERE `template_id` = 996;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(996, 6, 4006),
(996, 45, 5994);

DELETE FROM `item_budget_template` WHERE `template_id` = 997;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(997, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 998;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(998, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 999;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(999, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1000;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1000, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1001;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1001, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1002;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1002, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1003;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1003, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1004;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1004, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1005;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1005, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1006;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1006, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1007;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1007, 3, 3158),
(1007, 4, 3684),
(1007, 12, 3158);

DELETE FROM `item_budget_template` WHERE `template_id` = 1008;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1008, 3, 3334),
(1008, 4, 3333),
(1008, 12, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1009;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1009, 3, 2286),
(1009, 4, 2286),
(1009, 15, 2857),
(1009, 12, 2571);

DELETE FROM `item_budget_template` WHERE `template_id` = 1010;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1010, 4, 7037),
(1010, 3, 2963);

DELETE FROM `item_budget_template` WHERE `template_id` = 1011;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1011, 5, 5333),
(1011, 6, 4667);

DELETE FROM `item_budget_template` WHERE `template_id` = 1012;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1012, 4, 3810),
(1012, 5, 2857),
(1012, 6, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1013;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1013, 4, 4000),
(1013, 5, 2400),
(1013, 6, 3600);

DELETE FROM `item_budget_template` WHERE `template_id` = 1014;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1014, 3, 6333),
(1014, 4, 3667);

DELETE FROM `item_budget_template` WHERE `template_id` = 1015;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1015, 4, 4000),
(1015, 5, 2400),
(1015, 6, 3600);

DELETE FROM `item_budget_template` WHERE `template_id` = 1016;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1016, 5, 3045),
(1016, 6, 4351),
(1016, 45, 2604);

DELETE FROM `item_budget_template` WHERE `template_id` = 1017;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1017, 5, 2788),
(1017, 6, 4530),
(1017, 45, 2682);

DELETE FROM `item_budget_template` WHERE `template_id` = 1018;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1018, 5, 2788),
(1018, 6, 4530),
(1018, 45, 2682);

DELETE FROM `item_budget_template` WHERE `template_id` = 1019;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1019, 5, 2366),
(1019, 6, 2070),
(1019, 45, 5564);

DELETE FROM `item_budget_template` WHERE `template_id` = 1020;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1020, 5, 4549),
(1020, 6, 2729),
(1020, 45, 2722);

DELETE FROM `item_budget_template` WHERE `template_id` = 1021;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1021, 5, 4530),
(1021, 6, 2788),
(1021, 45, 2682);

DELETE FROM `item_budget_template` WHERE `template_id` = 1022;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1022, 5, 4530),
(1022, 6, 2788),
(1022, 45, 2682);

DELETE FROM `item_budget_template` WHERE `template_id` = 1023;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1023, 5, 3690),
(1023, 45, 6310);

DELETE FROM `item_budget_template` WHERE `template_id` = 1024;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1024, 5, 4006),
(1024, 45, 5994);

DELETE FROM `item_budget_template` WHERE `template_id` = 1025;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1025, 5, 4006),
(1025, 45, 5994);

DELETE FROM `item_budget_template` WHERE `template_id` = 1026;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1026, 4, 2857),
(1026, 5, 3810),
(1026, 6, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1027;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1027, 4, 2400),
(1027, 5, 4000),
(1027, 6, 3600);

DELETE FROM `item_budget_template` WHERE `template_id` = 1028;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1028, 4, 2400),
(1028, 5, 4000),
(1028, 6, 3600);

DELETE FROM `item_budget_template` WHERE `template_id` = 1029;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1029, 4, 2857),
(1029, 5, 3810),
(1029, 6, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1030;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1030, 4, 2400),
(1030, 5, 4000),
(1030, 6, 3600);

DELETE FROM `item_budget_template` WHERE `template_id` = 1031;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1031, 4, 1132),
(1031, 5, 1887),
(1031, 6, 1698),
(1031, 32, 5283);

DELETE FROM `item_budget_template` WHERE `template_id` = 1032;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1032, 3, 6667),
(1032, 4, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1033;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1033, 3, 7143),
(1033, 4, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 1034;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1034, 3, 7143),
(1034, 4, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 1035;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1035, 3, 6667),
(1035, 5, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1036;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1036, 3, 7143),
(1036, 5, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 1037;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1037, 3, 6250),
(1037, 5, 3750);

DELETE FROM `item_budget_template` WHERE `template_id` = 1038;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1038, 5, 2496),
(1038, 31, 3072),
(1038, 45, 4432);

DELETE FROM `item_budget_template` WHERE `template_id` = 1039;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1039, 5, 1315),
(1039, 31, 1753),
(1039, 45, 6932);

DELETE FROM `item_budget_template` WHERE `template_id` = 1040;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1040, 5, 3976),
(1040, 31, 1988),
(1040, 45, 4036);

DELETE FROM `item_budget_template` WHERE `template_id` = 1041;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1041, 3, 7619),
(1041, 31, 2381);

DELETE FROM `item_budget_template` WHERE `template_id` = 1042;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1042, 3, 3333),
(1042, 31, 6667);

DELETE FROM `item_budget_template` WHERE `template_id` = 1043;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1043, 3, 5833),
(1043, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 1044;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1044, 4, 3696),
(1044, 5, 3478),
(1044, 6, 2826);

DELETE FROM `item_budget_template` WHERE `template_id` = 1045;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1045, 4, 3714),
(1045, 5, 3429),
(1045, 6, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 1046;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1046, 3, 2432),
(1046, 32, 7568);

DELETE FROM `item_budget_template` WHERE `template_id` = 1047;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1047, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1048;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1048, 3, 4167),
(1048, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 1049;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1049, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1050;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1050, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1051;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1051, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1052;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1052, 4, 5227),
(1052, 3, 3409),
(1052, 12, 1364);

DELETE FROM `item_budget_template` WHERE `template_id` = 1053;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1053, 4, 6410),
(1053, 32, 3590);

DELETE FROM `item_budget_template` WHERE `template_id` = 1054;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1054, 4, 5000),
(1054, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1055;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1055, 4, 3393),
(1055, 5, 2857),
(1055, 6, 1250),
(1055, 32, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 1056;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1056, 4, 3202),
(1056, 5, 2402),
(1056, 3, 2001),
(1056, 45, 2395);

DELETE FROM `item_budget_template` WHERE `template_id` = 1057;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1057, 5, 3018),
(1057, 4, 3622),
(1057, 3, 1811),
(1057, 45, 1549);

DELETE FROM `item_budget_template` WHERE `template_id` = 1058;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1058, 5, 2583),
(1058, 45, 5006),
(1058, 32, 2411);

DELETE FROM `item_budget_template` WHERE `template_id` = 1059;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1059, 5, 6718),
(1059, 45, 3282);

DELETE FROM `item_budget_template` WHERE `template_id` = 1060;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1060, 5, 4974),
(1060, 45, 5026);

DELETE FROM `item_budget_template` WHERE `template_id` = 1061;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1061, 3, 5769),
(1061, 5, 4231);

DELETE FROM `item_budget_template` WHERE `template_id` = 1062;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1062, 5, 2667),
(1062, 3, 3111),
(1062, 6, 2000),
(1062, 31, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 1063;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1063, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1064;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1064, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1065;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1065, 3, 4762),
(1065, 4, 2857),
(1065, 31, 2381);

DELETE FROM `item_budget_template` WHERE `template_id` = 1066;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1066, 3, 6087),
(1066, 4, 3913);

DELETE FROM `item_budget_template` WHERE `template_id` = 1067;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1067, 5, 3847),
(1067, 6, 3686),
(1067, 45, 2467);

DELETE FROM `item_budget_template` WHERE `template_id` = 1068;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1068, 5, 5271),
(1068, 6, 3012),
(1068, 45, 1717);

DELETE FROM `item_budget_template` WHERE `template_id` = 1069;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1069, 5, 3322),
(1069, 6, 3322),
(1069, 45, 3356);

DELETE FROM `item_budget_template` WHERE `template_id` = 1070;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1070, 5, 4872),
(1070, 6, 3045),
(1070, 45, 2083);

DELETE FROM `item_budget_template` WHERE `template_id` = 1071;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1071, 5, 4549),
(1071, 6, 2729),
(1071, 45, 2722);

DELETE FROM `item_budget_template` WHERE `template_id` = 1072;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1072, 5, 3224),
(1072, 6, 3518),
(1072, 45, 3258);

DELETE FROM `item_budget_template` WHERE `template_id` = 1073;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1073, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1074;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1074, 5, 5090),
(1074, 6, 2423),
(1074, 45, 2487);

DELETE FROM `item_budget_template` WHERE `template_id` = 1075;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1075, 5, 3441),
(1075, 6, 2815),
(1075, 45, 3744);

DELETE FROM `item_budget_template` WHERE `template_id` = 1076;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1076, 5, 3690),
(1076, 45, 6310);

DELETE FROM `item_budget_template` WHERE `template_id` = 1077;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1077, 5, 6494),
(1077, 45, 3506);

DELETE FROM `item_budget_template` WHERE `template_id` = 1078;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1078, 4, 7059),
(1078, 12, 2941);

DELETE FROM `item_budget_template` WHERE `template_id` = 1079;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1079, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1080;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1080, 5, 2655),
(1080, 45, 5221),
(1080, 31, 2124);

DELETE FROM `item_budget_template` WHERE `template_id` = 1081;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1081, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1082;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1082, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1083;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1083, 12, 5000),
(1083, 15, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1084;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1084, 5, 3656),
(1084, 6, 2437),
(1084, 45, 3907);

DELETE FROM `item_budget_template` WHERE `template_id` = 1085;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1085, 5, 3471),
(1085, 45, 6529);

DELETE FROM `item_budget_template` WHERE `template_id` = 1086;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1086, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1087;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1087, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1088;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1088, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1089;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1089, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1090;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1090, 6, 2722),
(1090, 5, 2042),
(1090, 45, 5236);

DELETE FROM `item_budget_template` WHERE `template_id` = 1091;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1091, 12, 5200),
(1091, 13, 4800);

DELETE FROM `item_budget_template` WHERE `template_id` = 1092;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1092, 4, 3333),
(1092, 3, 2963),
(1092, 12, 3704);

DELETE FROM `item_budget_template` WHERE `template_id` = 1093;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1093, 5, 3333),
(1093, 32, 6667);

DELETE FROM `item_budget_template` WHERE `template_id` = 1094;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1094, 5, 5000),
(1094, 6, 2500),
(1094, 31, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 1095;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1095, 6, 3445),
(1095, 5, 3445),
(1095, 45, 3110);

DELETE FROM `item_budget_template` WHERE `template_id` = 1096;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1096, 4, 5000),
(1096, 3, 3438),
(1096, 12, 1562);

DELETE FROM `item_budget_template` WHERE `template_id` = 1097;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1097, 5, 2037),
(1097, 31, 3260),
(1097, 45, 4703);

DELETE FROM `item_budget_template` WHERE `template_id` = 1098;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1098, 5, 2220),
(1098, 45, 7780);

DELETE FROM `item_budget_template` WHERE `template_id` = 1099;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1099, 3, 4898),
(1099, 5, 2245),
(1099, 32, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 1100;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1100, 12, 6667),
(1100, 15, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1101;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1101, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1102;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1102, 5, 1953),
(1102, 45, 5009),
(1102, 32, 3038);

DELETE FROM `item_budget_template` WHERE `template_id` = 1103;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1103, 6, 3429),
(1103, 5, 3429),
(1103, 45, 3142);

DELETE FROM `item_budget_template` WHERE `template_id` = 1104;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1104, 5, 3649),
(1104, 31, 2919),
(1104, 45, 3432);

DELETE FROM `item_budget_template` WHERE `template_id` = 1105;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1105, 4, 4595),
(1105, 12, 2162),
(1105, 13, 3243);

DELETE FROM `item_budget_template` WHERE `template_id` = 1106;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1106, 5, 4552),
(1106, 45, 5448);

DELETE FROM `item_budget_template` WHERE `template_id` = 1107;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1107, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1108;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1108, 6, 2417),
(1108, 5, 2417),
(1108, 45, 5166);

DELETE FROM `item_budget_template` WHERE `template_id` = 1109;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1109, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1110;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1110, 6, 3914),
(1110, 5, 2740),
(1110, 45, 3346);

DELETE FROM `item_budget_template` WHERE `template_id` = 1111;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1111, 5, 6111),
(1111, 32, 3889);

DELETE FROM `item_budget_template` WHERE `template_id` = 1112;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1112, 5, 2318),
(1112, 6, 1738),
(1112, 45, 5944);

DELETE FROM `item_budget_template` WHERE `template_id` = 1113;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1113, 5, 5172),
(1113, 32, 4828);

DELETE FROM `item_budget_template` WHERE `template_id` = 1114;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1114, 5, 6190),
(1114, 31, 3810);

DELETE FROM `item_budget_template` WHERE `template_id` = 1115;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1115, 3, 6774),
(1115, 31, 3226);

DELETE FROM `item_budget_template` WHERE `template_id` = 1116;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1116, 3, 5652),
(1116, 31, 4348);

DELETE FROM `item_budget_template` WHERE `template_id` = 1117;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1117, 37, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1118;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1118, 6, 4643),
(1118, 5, 2521),
(1118, 45, 2836);

DELETE FROM `item_budget_template` WHERE `template_id` = 1119;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1119, 15, 4545),
(1119, 13, 5455);

DELETE FROM `item_budget_template` WHERE `template_id` = 1120;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1120, 3, 5333),
(1120, 12, 4667);

DELETE FROM `item_budget_template` WHERE `template_id` = 1121;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1121, 5, 5294),
(1121, 6, 4706);

DELETE FROM `item_budget_template` WHERE `template_id` = 1122;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1122, 3, 6774),
(1122, 5, 3226);

DELETE FROM `item_budget_template` WHERE `template_id` = 1123;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1123, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1124;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1124, 37, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1125;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1125, 32, 5771),
(1125, 45, 4229);

DELETE FROM `item_budget_template` WHERE `template_id` = 1126;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1126, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1127;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1127, 3, 5833),
(1127, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 1128;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1128, 6, 5111),
(1128, 5, 4889);

DELETE FROM `item_budget_template` WHERE `template_id` = 1129;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1129, 5, 6471),
(1129, 6, 3529);

DELETE FROM `item_budget_template` WHERE `template_id` = 1130;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1130, 5, 3822),
(1130, 6, 2548),
(1130, 45, 3630);

DELETE FROM `item_budget_template` WHERE `template_id` = 1131;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1131, 6, 2260),
(1131, 5, 2260),
(1131, 45, 3672),
(1131, 31, 1808);

DELETE FROM `item_budget_template` WHERE `template_id` = 1132;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1132, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1133;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1133, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1134;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1134, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1135;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1135, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1136;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1136, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1137;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1137, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1138;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1138, 4, 4667),
(1138, 12, 5333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1139;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1139, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1140;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1140, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1141;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1141, 31, 5333),
(1141, 32, 4667);

DELETE FROM `item_budget_template` WHERE `template_id` = 1142;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1142, 6, 3647),
(1142, 5, 3495),
(1142, 45, 2858);

DELETE FROM `item_budget_template` WHERE `template_id` = 1143;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1143, 31, 2574),
(1143, 45, 7426);

DELETE FROM `item_budget_template` WHERE `template_id` = 1144;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1144, 5, 4357),
(1144, 31, 1452),
(1144, 45, 4191);

DELETE FROM `item_budget_template` WHERE `template_id` = 1145;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1145, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1146;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1146, 4, 5484),
(1146, 32, 4516);

DELETE FROM `item_budget_template` WHERE `template_id` = 1147;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1147, 4, 3846),
(1147, 5, 2564),
(1147, 32, 3590);

DELETE FROM `item_budget_template` WHERE `template_id` = 1148;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1148, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1149;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1149, 5, 5484),
(1149, 32, 4516);

DELETE FROM `item_budget_template` WHERE `template_id` = 1150;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1150, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1151;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1151, 5, 5484),
(1151, 32, 4516);

DELETE FROM `item_budget_template` WHERE `template_id` = 1152;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1152, 5, 1877),
(1152, 32, 4379),
(1152, 45, 3744);

DELETE FROM `item_budget_template` WHERE `template_id` = 1153;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1153, 4, 5385),
(1153, 3, 4615);

DELETE FROM `item_budget_template` WHERE `template_id` = 1154;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1154, 4, 4118),
(1154, 3, 3529),
(1154, 5, 2353);

DELETE FROM `item_budget_template` WHERE `template_id` = 1155;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1155, 3, 5556),
(1155, 5, 4444);

DELETE FROM `item_budget_template` WHERE `template_id` = 1156;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1156, 3, 5556),
(1156, 5, 4444);

DELETE FROM `item_budget_template` WHERE `template_id` = 1157;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1157, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1158;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1158, 3, 5000),
(1158, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1159;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1159, 5, 4381),
(1159, 45, 5619);

DELETE FROM `item_budget_template` WHERE `template_id` = 1160;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1160, 3, 4516),
(1160, 5, 5484);

DELETE FROM `item_budget_template` WHERE `template_id` = 1161;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1161, 4, 2895),
(1161, 3, 2631),
(1161, 5, 4474);

DELETE FROM `item_budget_template` WHERE `template_id` = 1162;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1162, 4, 5143),
(1162, 3, 4857);

DELETE FROM `item_budget_template` WHERE `template_id` = 1163;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1163, 4, 4000),
(1163, 3, 3778),
(1163, 5, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 1164;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1164, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1165;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1165, 3, 5000),
(1165, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1166;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1166, 5, 6236),
(1166, 45, 3764);

DELETE FROM `item_budget_template` WHERE `template_id` = 1167;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1167, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1168;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1168, 5, 1369),
(1168, 32, 3833),
(1168, 45, 4798);

DELETE FROM `item_budget_template` WHERE `template_id` = 1169;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1169, 45, 6469),
(1169, 32, 3531);

DELETE FROM `item_budget_template` WHERE `template_id` = 1170;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1170, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1171;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1171, 4, 2203),
(1171, 6, 2034),
(1171, 32, 5763);

DELETE FROM `item_budget_template` WHERE `template_id` = 1172;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1172, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1173;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1173, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1174;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1174, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1175;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1175, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1176;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1176, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1177;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1177, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1178;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1178, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1179;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1179, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1180;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1180, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1181;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1181, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1182;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1182, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1183;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1183, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1184;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1184, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1185;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1185, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1186;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1186, 3, 5556),
(1186, 5, 4444);

DELETE FROM `item_budget_template` WHERE `template_id` = 1187;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1187, 3, 4516),
(1187, 5, 5484);

DELETE FROM `item_budget_template` WHERE `template_id` = 1188;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1188, 5, 4381),
(1188, 45, 5619);

DELETE FROM `item_budget_template` WHERE `template_id` = 1189;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1189, 5, 1877),
(1189, 32, 4379),
(1189, 45, 3744);

DELETE FROM `item_budget_template` WHERE `template_id` = 1190;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1190, 3, 5000),
(1190, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1191;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1191, 5, 5484),
(1191, 32, 4516);

DELETE FROM `item_budget_template` WHERE `template_id` = 1192;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1192, 3, 5000),
(1192, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1193;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1193, 5, 6236),
(1193, 45, 3764);

DELETE FROM `item_budget_template` WHERE `template_id` = 1194;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1194, 4, 3846),
(1194, 5, 2564),
(1194, 32, 3590);

DELETE FROM `item_budget_template` WHERE `template_id` = 1195;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1195, 4, 4118),
(1195, 3, 3529),
(1195, 5, 2353);

DELETE FROM `item_budget_template` WHERE `template_id` = 1196;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1196, 4, 4000),
(1196, 3, 3778),
(1196, 5, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 1197;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1197, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1198;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1198, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1199;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1199, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1200;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1200, 5, 5484),
(1200, 32, 4516);

DELETE FROM `item_budget_template` WHERE `template_id` = 1201;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1201, 3, 5556),
(1201, 5, 4444);

DELETE FROM `item_budget_template` WHERE `template_id` = 1202;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1202, 4, 2895),
(1202, 3, 2631),
(1202, 5, 4474);

DELETE FROM `item_budget_template` WHERE `template_id` = 1203;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1203, 4, 5484),
(1203, 32, 4516);

DELETE FROM `item_budget_template` WHERE `template_id` = 1204;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1204, 4, 5385),
(1204, 3, 4615);

DELETE FROM `item_budget_template` WHERE `template_id` = 1205;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1205, 4, 5143),
(1205, 3, 4857);

DELETE FROM `item_budget_template` WHERE `template_id` = 1206;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1206, 4, 7667),
(1206, 3, 2333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1207;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1207, 45, 6469),
(1207, 32, 3531);

DELETE FROM `item_budget_template` WHERE `template_id` = 1208;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1208, 6, 2414),
(1208, 3, 3793),
(1208, 5, 3793);

DELETE FROM `item_budget_template` WHERE `template_id` = 1209;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1209, 3, 3846),
(1209, 4, 3590),
(1209, 31, 2564);

DELETE FROM `item_budget_template` WHERE `template_id` = 1210;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1210, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1211;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1211, 5, 1369),
(1211, 32, 3833),
(1211, 45, 4798);

DELETE FROM `item_budget_template` WHERE `template_id` = 1212;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1212, 4, 2500),
(1212, 5, 2250),
(1212, 32, 5250);

DELETE FROM `item_budget_template` WHERE `template_id` = 1213;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1213, 5, 3690),
(1213, 45, 6310);

DELETE FROM `item_budget_template` WHERE `template_id` = 1214;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1214, 4, 5172),
(1214, 32, 4828);

DELETE FROM `item_budget_template` WHERE `template_id` = 1215;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1215, 4, 2601),
(1215, 5, 2600),
(1215, 6, 2427),
(1215, 45, 2372);

DELETE FROM `item_budget_template` WHERE `template_id` = 1216;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1216, 3, 4445),
(1216, 4, 2222),
(1216, 13, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1217;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1217, 5, 5938),
(1217, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 1218;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1218, 4, 5116),
(1218, 3, 4884);

DELETE FROM `item_budget_template` WHERE `template_id` = 1219;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1219, 5, 3049),
(1219, 45, 6951);

DELETE FROM `item_budget_template` WHERE `template_id` = 1220;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1220, 5, 5391),
(1220, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 1221;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1221, 5, 5128),
(1221, 45, 4872);

DELETE FROM `item_budget_template` WHERE `template_id` = 1222;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1222, 3, 5135),
(1222, 4, 4865);

DELETE FROM `item_budget_template` WHERE `template_id` = 1223;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1223, 3, 5135),
(1223, 4, 4865);

DELETE FROM `item_budget_template` WHERE `template_id` = 1224;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1224, 3, 5185),
(1224, 4, 4815);

DELETE FROM `item_budget_template` WHERE `template_id` = 1225;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1225, 3, 5102),
(1225, 4, 4898);

DELETE FROM `item_budget_template` WHERE `template_id` = 1226;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1226, 3, 5135),
(1226, 4, 4865);

DELETE FROM `item_budget_template` WHERE `template_id` = 1227;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1227, 3, 5102),
(1227, 4, 4898);

DELETE FROM `item_budget_template` WHERE `template_id` = 1228;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1228, 3, 5135),
(1228, 4, 4865);

DELETE FROM `item_budget_template` WHERE `template_id` = 1229;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1229, 3, 5102),
(1229, 4, 4898);

DELETE FROM `item_budget_template` WHERE `template_id` = 1230;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1230, 3, 5185),
(1230, 4, 4815);

DELETE FROM `item_budget_template` WHERE `template_id` = 1231;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1231, 3, 5185),
(1231, 4, 4815);

DELETE FROM `item_budget_template` WHERE `template_id` = 1232;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1232, 4, 4815),
(1232, 3, 5185);

DELETE FROM `item_budget_template` WHERE `template_id` = 1233;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1233, 3, 5333),
(1233, 4, 4667);

DELETE FROM `item_budget_template` WHERE `template_id` = 1234;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1234, 3, 5238),
(1234, 4, 4762);

DELETE FROM `item_budget_template` WHERE `template_id` = 1235;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1235, 5, 6128),
(1235, 45, 3872);

DELETE FROM `item_budget_template` WHERE `template_id` = 1236;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1236, 5, 7105),
(1236, 6, 2895);

DELETE FROM `item_budget_template` WHERE `template_id` = 1237;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1237, 5, 7143),
(1237, 6, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 1238;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1238, 6, 2895),
(1238, 5, 7105);

DELETE FROM `item_budget_template` WHERE `template_id` = 1239;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1239, 5, 7115),
(1239, 6, 2885);

DELETE FROM `item_budget_template` WHERE `template_id` = 1240;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1240, 6, 2895),
(1240, 5, 7105);

DELETE FROM `item_budget_template` WHERE `template_id` = 1241;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1241, 6, 5000),
(1241, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1242;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1242, 5, 7105),
(1242, 6, 2895);

DELETE FROM `item_budget_template` WHERE `template_id` = 1243;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1243, 5, 7115),
(1243, 6, 2885);

DELETE FROM `item_budget_template` WHERE `template_id` = 1244;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1244, 6, 2857),
(1244, 5, 7143);

DELETE FROM `item_budget_template` WHERE `template_id` = 1245;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1245, 5, 7143),
(1245, 6, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 1246;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1246, 5, 7115),
(1246, 6, 2885);

DELETE FROM `item_budget_template` WHERE `template_id` = 1247;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1247, 5, 7500),
(1247, 6, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 1248;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1248, 5, 7143),
(1248, 6, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 1249;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1249, 3, 5172),
(1249, 5, 4828);

DELETE FROM `item_budget_template` WHERE `template_id` = 1250;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1250, 3, 3570),
(1250, 5, 3569),
(1250, 45, 2861);

DELETE FROM `item_budget_template` WHERE `template_id` = 1251;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1251, 3, 3592),
(1251, 5, 3592),
(1251, 45, 2816);

DELETE FROM `item_budget_template` WHERE `template_id` = 1252;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1252, 3, 3623),
(1252, 5, 3623),
(1252, 45, 2754);

DELETE FROM `item_budget_template` WHERE `template_id` = 1253;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1253, 5, 3488),
(1253, 32, 6512);

DELETE FROM `item_budget_template` WHERE `template_id` = 1254;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1254, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1255;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1255, 15, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1256;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1256, 13, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1257;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1257, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1258;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1258, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1259;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1259, 38, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1260;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1260, 5, 2984),
(1260, 45, 7016);

DELETE FROM `item_budget_template` WHERE `template_id` = 1261;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1261, 5, 2141),
(1261, 6, 2140),
(1261, 45, 5719);

DELETE FROM `item_budget_template` WHERE `template_id` = 1262;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1262, 4, 3103),
(1262, 14, 6897);

DELETE FROM `item_budget_template` WHERE `template_id` = 1263;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1263, 3, 5500),
(1263, 5, 2667),
(1263, 6, 1833);

DELETE FROM `item_budget_template` WHERE `template_id` = 1264;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1264, 5, 4094),
(1264, 45, 5906);

DELETE FROM `item_budget_template` WHERE `template_id` = 1265;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1265, 4, 4706),
(1265, 12, 5294);

DELETE FROM `item_budget_template` WHERE `template_id` = 1266;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1266, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1267;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1267, 5, 5000),
(1267, 6, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1268;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1268, 3, 6000),
(1268, 37, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1269;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1269, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1270;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1270, 5, 4006),
(1270, 45, 5994);

DELETE FROM `item_budget_template` WHERE `template_id` = 1271;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1271, 5, 1362),
(1271, 6, 1362),
(1271, 45, 7276);

DELETE FROM `item_budget_template` WHERE `template_id` = 1272;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1272, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1273;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1273, 5, 2453),
(1273, 45, 5094),
(1273, 32, 2453);

DELETE FROM `item_budget_template` WHERE `template_id` = 1274;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1274, 4, 1722),
(1274, 5, 2410),
(1274, 6, 1894),
(1274, 45, 3974);

DELETE FROM `item_budget_template` WHERE `template_id` = 1275;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1275, 4, 2371),
(1275, 3, 1897),
(1275, 5, 2529),
(1275, 6, 1581),
(1275, 45, 1622);

DELETE FROM `item_budget_template` WHERE `template_id` = 1276;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1276, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1277;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1277, 5, 1546),
(1277, 45, 4847),
(1277, 32, 3607);

DELETE FROM `item_budget_template` WHERE `template_id` = 1278;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1278, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1279;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1279, 5, 2350),
(1279, 6, 1958),
(1279, 45, 5692);

DELETE FROM `item_budget_template` WHERE `template_id` = 1280;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1280, 5, 2829),
(1280, 6, 1258),
(1280, 45, 5913);

DELETE FROM `item_budget_template` WHERE `template_id` = 1281;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1281, 4, 5714),
(1281, 12, 4286);

DELETE FROM `item_budget_template` WHERE `template_id` = 1282;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1282, 5, 3826),
(1282, 6, 2355),
(1282, 4, 1177),
(1282, 45, 2642);

DELETE FROM `item_budget_template` WHERE `template_id` = 1283;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1283, 4, 2444),
(1283, 3, 1467),
(1283, 5, 2567),
(1283, 6, 1955),
(1283, 45, 1567);

DELETE FROM `item_budget_template` WHERE `template_id` = 1284;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1284, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1285;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1285, 5, 2364),
(1285, 45, 7636);

DELETE FROM `item_budget_template` WHERE `template_id` = 1286;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1286, 4, 7073),
(1286, 3, 2927);

DELETE FROM `item_budget_template` WHERE `template_id` = 1287;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1287, 3, 5000),
(1287, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1288;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1288, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1289;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1289, 5, 5391),
(1289, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 1290;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1290, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1291;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1291, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1292;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1292, 5, 6780),
(1292, 45, 3220);

DELETE FROM `item_budget_template` WHERE `template_id` = 1293;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1293, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1294;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1294, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1295;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1295, 5, 3690),
(1295, 45, 6310);

DELETE FROM `item_budget_template` WHERE `template_id` = 1296;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1296, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1297;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1297, 5, 3506),
(1297, 45, 6494);

DELETE FROM `item_budget_template` WHERE `template_id` = 1298;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1298, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1299;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1299, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1300;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1300, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1301;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1301, 3, 5000),
(1301, 4, 2667),
(1301, 5, 2333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1302;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1302, 4, 3636),
(1302, 32, 6364);

DELETE FROM `item_budget_template` WHERE `template_id` = 1303;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1303, 5, 1896),
(1303, 45, 8104);

DELETE FROM `item_budget_template` WHERE `template_id` = 1304;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1304, 5, 1799),
(1304, 45, 8201);

DELETE FROM `item_budget_template` WHERE `template_id` = 1305;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1305, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1306;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1306, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1307;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1307, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1308;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1308, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1309;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1309, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1310;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1310, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1311;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1311, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1312;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1312, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1313;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1313, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1314;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1314, 4, 3891),
(1314, 5, 3891),
(1314, 45, 2218);

DELETE FROM `item_budget_template` WHERE `template_id` = 1315;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1315, 4, 2500),
(1315, 5, 2500),
(1315, 3, 2500),
(1315, 6, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 1316;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1316, 5, 3846),
(1316, 3, 6154);

DELETE FROM `item_budget_template` WHERE `template_id` = 1317;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1317, 5, 5006),
(1317, 45, 4994);

DELETE FROM `item_budget_template` WHERE `template_id` = 1318;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1318, 3, 6786),
(1318, 4, 3214);

DELETE FROM `item_budget_template` WHERE `template_id` = 1319;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1319, 5, 1780),
(1319, 45, 8220);

DELETE FROM `item_budget_template` WHERE `template_id` = 1320;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1320, 5, 1511),
(1320, 6, 1511),
(1320, 45, 6978);

DELETE FROM `item_budget_template` WHERE `template_id` = 1321;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1321, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1322;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1322, 3, 6316),
(1322, 4, 3684);

DELETE FROM `item_budget_template` WHERE `template_id` = 1323;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1323, 37, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1324;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1324, 5, 3175),
(1324, 6, 977),
(1324, 45, 5848);

DELETE FROM `item_budget_template` WHERE `template_id` = 1325;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1325, 4, 6481),
(1325, 3, 3519);

DELETE FROM `item_budget_template` WHERE `template_id` = 1326;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1326, 5, 2805),
(1326, 45, 7195);

DELETE FROM `item_budget_template` WHERE `template_id` = 1327;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1327, 5, 3636),
(1327, 32, 6364);

DELETE FROM `item_budget_template` WHERE `template_id` = 1328;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1328, 4, 2000),
(1328, 32, 4667),
(1328, 31, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1329;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1329, 5, 3834),
(1329, 32, 2440),
(1329, 45, 3726);

DELETE FROM `item_budget_template` WHERE `template_id` = 1330;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1330, 4, 6552),
(1330, 3, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 1331;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1331, 5, 5651),
(1331, 45, 4349);

DELETE FROM `item_budget_template` WHERE `template_id` = 1332;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1332, 45, 7426),
(1332, 31, 2574);

DELETE FROM `item_budget_template` WHERE `template_id` = 1333;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1333, 3, 6000),
(1333, 31, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1334;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1334, 45, 5498),
(1334, 32, 4502);

DELETE FROM `item_budget_template` WHERE `template_id` = 1335;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1335, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1336;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1336, 4, 5556),
(1336, 12, 4444);

DELETE FROM `item_budget_template` WHERE `template_id` = 1337;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1337, 4, 5789),
(1337, 12, 4211);

DELETE FROM `item_budget_template` WHERE `template_id` = 1338;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1338, 4, 5714),
(1338, 12, 4286);

DELETE FROM `item_budget_template` WHERE `template_id` = 1339;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1339, 4, 5714),
(1339, 12, 4286);

DELETE FROM `item_budget_template` WHERE `template_id` = 1340;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1340, 4, 5652),
(1340, 12, 4348);

DELETE FROM `item_budget_template` WHERE `template_id` = 1341;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1341, 3, 5833),
(1341, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 1342;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1342, 3, 6000),
(1342, 31, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1343;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1343, 3, 6296),
(1343, 31, 3704);

DELETE FROM `item_budget_template` WHERE `template_id` = 1344;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1344, 3, 6296),
(1344, 31, 3704);

DELETE FROM `item_budget_template` WHERE `template_id` = 1345;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1345, 3, 6429),
(1345, 31, 3571);

DELETE FROM `item_budget_template` WHERE `template_id` = 1346;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1346, 5, 2805),
(1346, 45, 7195);

DELETE FROM `item_budget_template` WHERE `template_id` = 1347;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1347, 5, 2984),
(1347, 45, 7016);

DELETE FROM `item_budget_template` WHERE `template_id` = 1348;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1348, 5, 2723),
(1348, 45, 7277);

DELETE FROM `item_budget_template` WHERE `template_id` = 1349;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1349, 5, 2646),
(1349, 45, 7354);

DELETE FROM `item_budget_template` WHERE `template_id` = 1350;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1350, 5, 2732),
(1350, 45, 7268);

DELETE FROM `item_budget_template` WHERE `template_id` = 1351;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1351, 5, 4167),
(1351, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 1352;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1352, 32, 5833),
(1352, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 1353;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1353, 38, 4545),
(1353, 12, 5455);

DELETE FROM `item_budget_template` WHERE `template_id` = 1354;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1354, 15, 5200),
(1354, 12, 4800);

DELETE FROM `item_budget_template` WHERE `template_id` = 1355;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1355, 5, 2579),
(1355, 45, 5077),
(1355, 31, 1250),
(1355, 32, 1094);

DELETE FROM `item_budget_template` WHERE `template_id` = 1356;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1356, 5, 2697),
(1356, 45, 7303);

DELETE FROM `item_budget_template` WHERE `template_id` = 1357;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1357, 3, 3214),
(1357, 4, 5179),
(1357, 12, 1607);

DELETE FROM `item_budget_template` WHERE `template_id` = 1358;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1358, 3, 3077),
(1358, 4, 3846),
(1358, 12, 1154),
(1358, 31, 1923);

DELETE FROM `item_budget_template` WHERE `template_id` = 1359;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1359, 3, 3582),
(1359, 4, 5075),
(1359, 12, 1343);

DELETE FROM `item_budget_template` WHERE `template_id` = 1360;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1360, 3, 2877),
(1360, 4, 4520),
(1360, 12, 1233),
(1360, 31, 1370);

DELETE FROM `item_budget_template` WHERE `template_id` = 1361;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1361, 3, 3864),
(1361, 4, 4773),
(1361, 12, 1363);

DELETE FROM `item_budget_template` WHERE `template_id` = 1362;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1362, 5, 2327),
(1362, 6, 958),
(1362, 45, 4799),
(1362, 32, 1916);

DELETE FROM `item_budget_template` WHERE `template_id` = 1363;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1363, 5, 2344),
(1363, 6, 852),
(1363, 45, 5100),
(1363, 31, 1704);

DELETE FROM `item_budget_template` WHERE `template_id` = 1364;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1364, 5, 3155),
(1364, 6, 1183),
(1364, 45, 3822),
(1364, 32, 1840);

DELETE FROM `item_budget_template` WHERE `template_id` = 1365;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1365, 5, 2992),
(1365, 6, 748),
(1365, 45, 3518),
(1365, 32, 1745),
(1365, 31, 997);

DELETE FROM `item_budget_template` WHERE `template_id` = 1366;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1366, 5, 3726),
(1366, 6, 699),
(1366, 45, 5575);

DELETE FROM `item_budget_template` WHERE `template_id` = 1367;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1367, 5, 2974),
(1367, 6, 905),
(1367, 45, 4311),
(1367, 32, 1810);

DELETE FROM `item_budget_template` WHERE `template_id` = 1368;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1368, 5, 2834),
(1368, 6, 1133),
(1368, 45, 4522),
(1368, 31, 1511);

DELETE FROM `item_budget_template` WHERE `template_id` = 1369;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1369, 5, 2881),
(1369, 6, 960),
(1369, 45, 6159);

DELETE FROM `item_budget_template` WHERE `template_id` = 1370;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1370, 5, 3374),
(1370, 6, 1038),
(1370, 45, 3772),
(1370, 32, 1816);

DELETE FROM `item_budget_template` WHERE `template_id` = 1371;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1371, 5, 2784),
(1371, 6, 1392),
(1371, 45, 3272),
(1371, 32, 1624),
(1371, 31, 928);

DELETE FROM `item_budget_template` WHERE `template_id` = 1372;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1372, 5, 3145),
(1372, 6, 2288),
(1372, 45, 3423),
(1372, 31, 1144);

DELETE FROM `item_budget_template` WHERE `template_id` = 1373;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1373, 5, 3620),
(1373, 6, 2556),
(1373, 45, 3824);

DELETE FROM `item_budget_template` WHERE `template_id` = 1374;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1374, 5, 4435),
(1374, 6, 1774),
(1374, 45, 3791);

DELETE FROM `item_budget_template` WHERE `template_id` = 1375;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1375, 5, 3031),
(1375, 6, 1749),
(1375, 45, 3588),
(1375, 32, 1632);

DELETE FROM `item_budget_template` WHERE `template_id` = 1376;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1376, 5, 3625),
(1376, 6, 2114),
(1376, 45, 4261);

DELETE FROM `item_budget_template` WHERE `template_id` = 1377;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1377, 3, 1224),
(1377, 4, 1529),
(1377, 5, 2243),
(1377, 6, 1223),
(1377, 45, 2354),
(1377, 32, 1427);

DELETE FROM `item_budget_template` WHERE `template_id` = 1378;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1378, 3, 2150),
(1378, 4, 2304),
(1378, 5, 1997),
(1378, 6, 922),
(1378, 45, 2627);

DELETE FROM `item_budget_template` WHERE `template_id` = 1379;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1379, 3, 2093),
(1379, 4, 1932),
(1379, 5, 2255),
(1379, 6, 966),
(1379, 45, 2754);

DELETE FROM `item_budget_template` WHERE `template_id` = 1380;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1380, 3, 1303),
(1380, 4, 1303),
(1380, 5, 2389),
(1380, 6, 978),
(1380, 45, 2507),
(1380, 32, 1520);

DELETE FROM `item_budget_template` WHERE `template_id` = 1381;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1381, 3, 1072),
(1381, 4, 1161),
(1381, 5, 2144),
(1381, 6, 983),
(1381, 45, 2139),
(1381, 32, 2501);

DELETE FROM `item_budget_template` WHERE `template_id` = 1382;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1382, 3, 5200),
(1382, 4, 2800),
(1382, 31, 2000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1383;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1383, 3, 3718),
(1383, 4, 3205),
(1383, 32, 1795),
(1383, 31, 1282);

DELETE FROM `item_budget_template` WHERE `template_id` = 1384;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1384, 3, 4909),
(1384, 4, 3273),
(1384, 31, 1818);

DELETE FROM `item_budget_template` WHERE `template_id` = 1385;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1385, 3, 5429),
(1385, 4, 2571),
(1385, 32, 2000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1386;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1386, 3, 4625),
(1386, 4, 2375),
(1386, 32, 1750),
(1386, 31, 1250);

DELETE FROM `item_budget_template` WHERE `template_id` = 1387;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1387, 3, 5233),
(1387, 5, 1994),
(1387, 6, 1495),
(1387, 45, 1278);

DELETE FROM `item_budget_template` WHERE `template_id` = 1388;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1388, 3, 2768),
(1388, 5, 2491),
(1388, 6, 1384),
(1388, 32, 1937),
(1388, 45, 1420);

DELETE FROM `item_budget_template` WHERE `template_id` = 1389;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1389, 3, 4600),
(1389, 5, 2811),
(1389, 6, 1278),
(1389, 45, 1311);

DELETE FROM `item_budget_template` WHERE `template_id` = 1390;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1390, 3, 3443),
(1390, 5, 2009),
(1390, 6, 1435),
(1390, 32, 2009),
(1390, 45, 1104);

DELETE FROM `item_budget_template` WHERE `template_id` = 1391;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1391, 3, 3731),
(1391, 5, 2152),
(1391, 6, 1004),
(1391, 32, 2009),
(1391, 45, 1104);

DELETE FROM `item_budget_template` WHERE `template_id` = 1392;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1392, 3, 839),
(1392, 4, 1259),
(1392, 5, 2307),
(1392, 6, 1258),
(1392, 45, 2869),
(1392, 32, 1468);

DELETE FROM `item_budget_template` WHERE `template_id` = 1393;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1393, 3, 1505),
(1393, 4, 2006),
(1393, 5, 2341),
(1393, 6, 1003),
(1393, 45, 3145);

DELETE FROM `item_budget_template` WHERE `template_id` = 1394;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1394, 3, 898),
(1394, 4, 988),
(1394, 5, 2155),
(1394, 6, 988),
(1394, 45, 2457),
(1394, 32, 2514);

DELETE FROM `item_budget_template` WHERE `template_id` = 1395;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1395, 3, 960),
(1395, 4, 1279),
(1395, 5, 2346),
(1395, 6, 1279),
(1395, 45, 2643),
(1395, 32, 1493);

DELETE FROM `item_budget_template` WHERE `template_id` = 1396;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1396, 3, 1589),
(1396, 4, 1589),
(1396, 5, 2065),
(1396, 6, 953),
(1396, 45, 3804);

DELETE FROM `item_budget_template` WHERE `template_id` = 1397;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1397, 3, 1204),
(1397, 4, 2007),
(1397, 5, 2207),
(1397, 6, 1204),
(1397, 45, 1973),
(1397, 32, 1405);

DELETE FROM `item_budget_template` WHERE `template_id` = 1398;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1398, 3, 2064),
(1398, 4, 2859),
(1398, 5, 2223),
(1398, 6, 953),
(1398, 45, 1901);

DELETE FROM `item_budget_template` WHERE `template_id` = 1399;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1399, 3, 1058),
(1399, 4, 2029),
(1399, 5, 2117),
(1399, 6, 970),
(1399, 45, 1357),
(1399, 32, 2469);

DELETE FROM `item_budget_template` WHERE `template_id` = 1400;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1400, 3, 1309),
(1400, 4, 2290),
(1400, 5, 2400),
(1400, 6, 982),
(1400, 45, 1492),
(1400, 32, 1527);

DELETE FROM `item_budget_template` WHERE `template_id` = 1401;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1401, 3, 2223),
(1401, 4, 2859),
(1401, 5, 2064),
(1401, 6, 953),
(1401, 45, 1901);

DELETE FROM `item_budget_template` WHERE `template_id` = 1402;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1402, 4, 5556),
(1402, 3, 2222),
(1402, 12, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 1403;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1403, 4, 4400),
(1403, 32, 5600);

DELETE FROM `item_budget_template` WHERE `template_id` = 1404;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1404, 4, 4412),
(1404, 3, 2647),
(1404, 31, 2941);

DELETE FROM `item_budget_template` WHERE `template_id` = 1405;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1405, 4, 5625),
(1405, 5, 4375);

DELETE FROM `item_budget_template` WHERE `template_id` = 1406;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1406, 4, 3418),
(1406, 5, 3417),
(1406, 45, 3165);

DELETE FROM `item_budget_template` WHERE `template_id` = 1407;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1407, 4, 4783),
(1407, 5, 5217);

DELETE FROM `item_budget_template` WHERE `template_id` = 1408;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1408, 5, 1468),
(1408, 4, 1142),
(1408, 45, 7390);

DELETE FROM `item_budget_template` WHERE `template_id` = 1409;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1409, 4, 2091),
(1409, 3, 2352),
(1409, 5, 2875),
(1409, 45, 2682);

DELETE FROM `item_budget_template` WHERE `template_id` = 1410;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1410, 5, 3614),
(1410, 4, 3058),
(1410, 45, 3328);

DELETE FROM `item_budget_template` WHERE `template_id` = 1411;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1411, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1412;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1412, 3, 6190),
(1412, 5, 3810);

DELETE FROM `item_budget_template` WHERE `template_id` = 1413;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1413, 3, 5455),
(1413, 31, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 1414;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1414, 3, 4688),
(1414, 4, 2187),
(1414, 31, 3125);

DELETE FROM `item_budget_template` WHERE `template_id` = 1415;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1415, 3, 6207),
(1415, 4, 3793);

DELETE FROM `item_budget_template` WHERE `template_id` = 1416;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1416, 3, 6429),
(1416, 31, 3571);

DELETE FROM `item_budget_template` WHERE `template_id` = 1417;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1417, 38, 1838),
(1417, 3, 1837),
(1417, 5, 1837),
(1417, 45, 4488);

DELETE FROM `item_budget_template` WHERE `template_id` = 1418;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1418, 4, 2857),
(1418, 5, 2286),
(1418, 3, 2857),
(1418, 6, 2000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1419;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1419, 5, 2155),
(1419, 4, 2586),
(1419, 3, 1724),
(1419, 6, 1508),
(1419, 45, 2027);

DELETE FROM `item_budget_template` WHERE `template_id` = 1420;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1420, 5, 2114),
(1420, 45, 7886);

DELETE FROM `item_budget_template` WHERE `template_id` = 1421;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1421, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1422;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1422, 5, 3876),
(1422, 6, 3046),
(1422, 45, 3078);

DELETE FROM `item_budget_template` WHERE `template_id` = 1423;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1423, 5, 2749),
(1423, 31, 1375),
(1423, 45, 5876);

DELETE FROM `item_budget_template` WHERE `template_id` = 1424;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1424, 45, 5236),
(1424, 32, 4764);

DELETE FROM `item_budget_template` WHERE `template_id` = 1425;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1425, 5, 2962),
(1425, 6, 1974),
(1425, 45, 5064);

DELETE FROM `item_budget_template` WHERE `template_id` = 1426;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1426, 5, 1219),
(1426, 45, 8781);

DELETE FROM `item_budget_template` WHERE `template_id` = 1427;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1427, 32, 4121),
(1427, 45, 3524),
(1427, 31, 2355);

DELETE FROM `item_budget_template` WHERE `template_id` = 1428;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1428, 5, 3690),
(1428, 45, 6310);

DELETE FROM `item_budget_template` WHERE `template_id` = 1429;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1429, 5, 2085),
(1429, 6, 1269),
(1429, 45, 4651),
(1429, 32, 1269),
(1429, 31, 726);

DELETE FROM `item_budget_template` WHERE `template_id` = 1430;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1430, 5, 4549),
(1430, 4, 2729),
(1430, 45, 2722);

DELETE FROM `item_budget_template` WHERE `template_id` = 1431;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1431, 5, 4549),
(1431, 4, 2729),
(1431, 45, 2722);

DELETE FROM `item_budget_template` WHERE `template_id` = 1432;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1432, 4, 3818),
(1432, 3, 4364),
(1432, 31, 1818);

DELETE FROM `item_budget_template` WHERE `template_id` = 1433;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1433, 4, 3637),
(1433, 13, 3636),
(1433, 12, 2727);

DELETE FROM `item_budget_template` WHERE `template_id` = 1434;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1434, 4, 6364),
(1434, 3, 3636);

DELETE FROM `item_budget_template` WHERE `template_id` = 1435;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1435, 5, 4654),
(1435, 4, 2560),
(1435, 45, 2786);

DELETE FROM `item_budget_template` WHERE `template_id` = 1436;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1436, 3, 3182),
(1436, 4, 2273),
(1436, 31, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 1437;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1437, 4, 3387),
(1437, 3, 1774),
(1437, 14, 3226),
(1437, 12, 1613);

DELETE FROM `item_budget_template` WHERE `template_id` = 1438;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1438, 5, 2190),
(1438, 6, 1095),
(1438, 45, 4799),
(1438, 32, 1916);

DELETE FROM `item_budget_template` WHERE `template_id` = 1439;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1439, 5, 5518),
(1439, 45, 4482);

DELETE FROM `item_budget_template` WHERE `template_id` = 1440;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1440, 3, 3704),
(1440, 5, 1852),
(1440, 32, 2592),
(1440, 31, 1852);

DELETE FROM `item_budget_template` WHERE `template_id` = 1441;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1441, 5, 4006),
(1441, 45, 5994);

DELETE FROM `item_budget_template` WHERE `template_id` = 1442;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1442, 5, 1352),
(1442, 32, 2704),
(1442, 45, 5944);

DELETE FROM `item_budget_template` WHERE `template_id` = 1443;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1443, 3, 5833),
(1443, 4, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 1444;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1444, 5, 3754),
(1444, 6, 1752),
(1444, 45, 4494);

DELETE FROM `item_budget_template` WHERE `template_id` = 1445;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1445, 5, 3782),
(1445, 45, 6218);

DELETE FROM `item_budget_template` WHERE `template_id` = 1446;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1446, 5, 3519),
(1446, 6, 3199),
(1446, 45, 3282);

DELETE FROM `item_budget_template` WHERE `template_id` = 1447;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1447, 5, 2002),
(1447, 45, 4494),
(1447, 32, 3504);

DELETE FROM `item_budget_template` WHERE `template_id` = 1448;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1448, 6, 2093),
(1448, 5, 4046),
(1448, 45, 1908),
(1448, 32, 1953);

DELETE FROM `item_budget_template` WHERE `template_id` = 1449;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1449, 3, 6944),
(1449, 4, 3056);

DELETE FROM `item_budget_template` WHERE `template_id` = 1450;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1450, 4, 3318),
(1450, 5, 3144),
(1450, 3, 1746),
(1450, 45, 1792);

DELETE FROM `item_budget_template` WHERE `template_id` = 1451;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1451, 4, 2656),
(1451, 5, 2988),
(1451, 3, 1660),
(1451, 45, 2696);

DELETE FROM `item_budget_template` WHERE `template_id` = 1452;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1452, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1453;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1453, 4, 3571),
(1453, 14, 4762),
(1453, 12, 1667);

DELETE FROM `item_budget_template` WHERE `template_id` = 1454;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1454, 3, 5455),
(1454, 5, 2424),
(1454, 6, 2121);

DELETE FROM `item_budget_template` WHERE `template_id` = 1455;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1455, 4, 5000),
(1455, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1456;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1456, 4, 2706),
(1456, 5, 4209),
(1456, 45, 3085);

DELETE FROM `item_budget_template` WHERE `template_id` = 1457;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1457, 5, 2932),
(1457, 32, 4561),
(1457, 45, 2507);

DELETE FROM `item_budget_template` WHERE `template_id` = 1458;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1458, 5, 5802),
(1458, 6, 2072),
(1458, 45, 2126);

DELETE FROM `item_budget_template` WHERE `template_id` = 1459;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1459, 4, 5500),
(1459, 12, 4500);

DELETE FROM `item_budget_template` WHERE `template_id` = 1460;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1460, 5, 3654),
(1460, 4, 2233),
(1460, 3, 2030),
(1460, 45, 2083);

DELETE FROM `item_budget_template` WHERE `template_id` = 1461;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1461, 5, 3730),
(1461, 4, 1243),
(1461, 45, 2126),
(1461, 32, 2901);

DELETE FROM `item_budget_template` WHERE `template_id` = 1462;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1462, 5, 3619),
(1462, 6, 2844),
(1462, 45, 3537);

DELETE FROM `item_budget_template` WHERE `template_id` = 1463;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1463, 4, 4500),
(1463, 3, 3000),
(1463, 31, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 1464;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1464, 3, 6000),
(1464, 4, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1465;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1465, 4, 7000),
(1465, 3, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1466;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1466, 5, 3196),
(1466, 45, 3363),
(1466, 32, 3441);

DELETE FROM `item_budget_template` WHERE `template_id` = 1467;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1467, 4, 4167),
(1467, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 1468;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1468, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1469;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1469, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1470;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1470, 5, 5744),
(1470, 45, 4256);

DELETE FROM `item_budget_template` WHERE `template_id` = 1471;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1471, 3, 5769),
(1471, 4, 4231);

DELETE FROM `item_budget_template` WHERE `template_id` = 1472;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1472, 3, 6957),
(1472, 5, 3043);

DELETE FROM `item_budget_template` WHERE `template_id` = 1473;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1473, 4, 7083),
(1473, 12, 2917);

DELETE FROM `item_budget_template` WHERE `template_id` = 1474;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1474, 5, 3596),
(1474, 45, 6404);

DELETE FROM `item_budget_template` WHERE `template_id` = 1475;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1475, 4, 7000),
(1475, 12, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1476;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1476, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1477;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1477, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1478;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1478, 4, 5909),
(1478, 3, 4091);

DELETE FROM `item_budget_template` WHERE `template_id` = 1479;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1479, 5, 1273),
(1479, 6, 990),
(1479, 45, 7737);

DELETE FROM `item_budget_template` WHERE `template_id` = 1480;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1480, 3, 5909),
(1480, 4, 4091);

DELETE FROM `item_budget_template` WHERE `template_id` = 1481;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1481, 5, 1713),
(1481, 6, 1591),
(1481, 45, 6696);

DELETE FROM `item_budget_template` WHERE `template_id` = 1482;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1482, 5, 3832),
(1482, 45, 6168);

DELETE FROM `item_budget_template` WHERE `template_id` = 1483;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1483, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1484;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1484, 3, 5750),
(1484, 5, 4250);

DELETE FROM `item_budget_template` WHERE `template_id` = 1485;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1485, 5, 5006),
(1485, 45, 4994);

DELETE FROM `item_budget_template` WHERE `template_id` = 1486;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1486, 3, 5667),
(1486, 4, 4333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1487;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1487, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1488;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1488, 4, 5932),
(1488, 32, 2373),
(1488, 31, 1695);

DELETE FROM `item_budget_template` WHERE `template_id` = 1489;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1489, 5, 4098),
(1489, 45, 5902);

DELETE FROM `item_budget_template` WHERE `template_id` = 1490;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1490, 5, 3247),
(1490, 6, 1894),
(1490, 45, 4859);

DELETE FROM `item_budget_template` WHERE `template_id` = 1491;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1491, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1492;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1492, 5, 2746),
(1492, 45, 5790),
(1492, 31, 1464);

DELETE FROM `item_budget_template` WHERE `template_id` = 1493;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1493, 32, 5833),
(1493, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 1494;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1494, 5, 3337),
(1494, 4, 2054),
(1494, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 1495;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1495, 5, 3782),
(1495, 45, 6218);

DELETE FROM `item_budget_template` WHERE `template_id` = 1496;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1496, 5, 7419),
(1496, 31, 2581);

DELETE FROM `item_budget_template` WHERE `template_id` = 1497;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1497, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1498;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1498, 5, 1871),
(1498, 32, 2911),
(1498, 31, 1663),
(1498, 45, 3555);

DELETE FROM `item_budget_template` WHERE `template_id` = 1499;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1499, 4, 2242),
(1499, 3, 2241),
(1499, 14, 3448),
(1499, 12, 2069);

DELETE FROM `item_budget_template` WHERE `template_id` = 1500;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1500, 3, 4151),
(1500, 5, 3208),
(1500, 32, 2641);

DELETE FROM `item_budget_template` WHERE `template_id` = 1501;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1501, 5, 3953),
(1501, 45, 6047);

DELETE FROM `item_budget_template` WHERE `template_id` = 1502;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1502, 3, 4800),
(1502, 12, 5200);

DELETE FROM `item_budget_template` WHERE `template_id` = 1503;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1503, 3, 3902),
(1503, 4, 3659),
(1503, 31, 2439);

DELETE FROM `item_budget_template` WHERE `template_id` = 1504;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1504, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1505;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1505, 5, 2329),
(1505, 6, 2096),
(1505, 45, 5575);

DELETE FROM `item_budget_template` WHERE `template_id` = 1506;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1506, 3, 5385),
(1506, 4, 4615);

DELETE FROM `item_budget_template` WHERE `template_id` = 1507;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1507, 4, 2646),
(1507, 5, 2802),
(1507, 3, 2023),
(1507, 45, 2529);

DELETE FROM `item_budget_template` WHERE `template_id` = 1508;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1508, 4, 2232),
(1508, 3, 2060),
(1508, 5, 2919),
(1508, 45, 2789);

DELETE FROM `item_budget_template` WHERE `template_id` = 1509;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1509, 5, 1188),
(1509, 45, 5485),
(1509, 32, 3327);

DELETE FROM `item_budget_template` WHERE `template_id` = 1510;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1510, 5, 3226),
(1510, 6, 2330),
(1510, 45, 4444);

DELETE FROM `item_budget_template` WHERE `template_id` = 1511;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1511, 5, 4445),
(1511, 45, 5555);

DELETE FROM `item_budget_template` WHERE `template_id` = 1512;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1512, 5, 3519),
(1512, 45, 6481);

DELETE FROM `item_budget_template` WHERE `template_id` = 1513;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1513, 3, 5098),
(1513, 5, 2549),
(1513, 31, 2353);

DELETE FROM `item_budget_template` WHERE `template_id` = 1514;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1514, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1515;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1515, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1516;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1516, 5, 4522),
(1516, 45, 5478);

DELETE FROM `item_budget_template` WHERE `template_id` = 1517;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1517, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1518;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1518, 6, 2912),
(1518, 5, 2730),
(1518, 45, 4358);

DELETE FROM `item_budget_template` WHERE `template_id` = 1519;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1519, 4, 5610),
(1519, 3, 4390);

DELETE FROM `item_budget_template` WHERE `template_id` = 1520;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1520, 5, 5868),
(1520, 45, 4132);

DELETE FROM `item_budget_template` WHERE `template_id` = 1521;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1521, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1522;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1522, 4, 4063),
(1522, 3, 3125),
(1522, 12, 2812);

DELETE FROM `item_budget_template` WHERE `template_id` = 1523;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1523, 5, 848),
(1523, 45, 7456),
(1523, 32, 1696);

DELETE FROM `item_budget_template` WHERE `template_id` = 1524;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1524, 4, 2284),
(1524, 5, 1979),
(1524, 6, 1522),
(1524, 45, 2083),
(1524, 32, 2132);

DELETE FROM `item_budget_template` WHERE `template_id` = 1525;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1525, 4, 2056),
(1525, 5, 1909),
(1525, 6, 1468),
(1525, 45, 2511),
(1525, 32, 2056);

DELETE FROM `item_budget_template` WHERE `template_id` = 1526;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1526, 5, 6298),
(1526, 45, 3702);

DELETE FROM `item_budget_template` WHERE `template_id` = 1527;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1527, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1528;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1528, 4, 3056),
(1528, 12, 3611),
(1528, 13, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1529;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1529, 3, 6296),
(1529, 4, 3704);

DELETE FROM `item_budget_template` WHERE `template_id` = 1530;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1530, 5, 4319),
(1530, 45, 5681);

DELETE FROM `item_budget_template` WHERE `template_id` = 1531;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1531, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1532;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1532, 5, 2632),
(1532, 32, 7368);

DELETE FROM `item_budget_template` WHERE `template_id` = 1533;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1533, 4, 5484),
(1533, 3, 4516);

DELETE FROM `item_budget_template` WHERE `template_id` = 1534;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1534, 5, 4102),
(1534, 45, 5898);

DELETE FROM `item_budget_template` WHERE `template_id` = 1535;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1535, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1536;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1536, 3, 6522),
(1536, 4, 3478);

DELETE FROM `item_budget_template` WHERE `template_id` = 1537;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1537, 5, 2063),
(1537, 45, 7937);

DELETE FROM `item_budget_template` WHERE `template_id` = 1538;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1538, 4, 1172),
(1538, 5, 2996),
(1538, 45, 4009),
(1538, 32, 1823);

DELETE FROM `item_budget_template` WHERE `template_id` = 1539;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1539, 5, 3393),
(1539, 45, 4541),
(1539, 32, 2066);

DELETE FROM `item_budget_template` WHERE `template_id` = 1540;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1540, 5, 3414),
(1540, 6, 2524),
(1540, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 1541;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1541, 5, 3048),
(1541, 6, 1434),
(1541, 45, 5518);

DELETE FROM `item_budget_template` WHERE `template_id` = 1542;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1542, 3, 3448),
(1542, 4, 4828),
(1542, 31, 1724);

DELETE FROM `item_budget_template` WHERE `template_id` = 1543;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1543, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1544;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1544, 4, 3800),
(1544, 3, 3600),
(1544, 12, 2600);

DELETE FROM `item_budget_template` WHERE `template_id` = 1545;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1545, 3, 3617),
(1545, 4, 2128),
(1545, 14, 4255);

DELETE FROM `item_budget_template` WHERE `template_id` = 1546;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1546, 5, 3640),
(1546, 45, 6360);

DELETE FROM `item_budget_template` WHERE `template_id` = 1547;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1547, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1548;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1548, 5, 6552),
(1548, 45, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 1549;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1549, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1550;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1550, 3, 6613),
(1550, 4, 3387);

DELETE FROM `item_budget_template` WHERE `template_id` = 1551;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1551, 5, 6552),
(1551, 45, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 1552;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1552, 3, 6296),
(1552, 4, 3704);

DELETE FROM `item_budget_template` WHERE `template_id` = 1553;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1553, 5, 3593),
(1553, 4, 1796),
(1553, 3, 1078),
(1553, 45, 3533);

DELETE FROM `item_budget_template` WHERE `template_id` = 1554;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1554, 5, 4005),
(1554, 4, 1201),
(1554, 45, 4794);

DELETE FROM `item_budget_template` WHERE `template_id` = 1555;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1555, 5, 4642),
(1555, 45, 5358);

DELETE FROM `item_budget_template` WHERE `template_id` = 1556;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1556, 4, 4545),
(1556, 3, 3182),
(1556, 31, 2273);

DELETE FROM `item_budget_template` WHERE `template_id` = 1557;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1557, 5, 2880),
(1557, 45, 4432),
(1557, 32, 2688);

DELETE FROM `item_budget_template` WHERE `template_id` = 1558;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1558, 5, 5058),
(1558, 45, 4942);

DELETE FROM `item_budget_template` WHERE `template_id` = 1559;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1559, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1560;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1560, 4, 5778),
(1560, 3, 4222);

DELETE FROM `item_budget_template` WHERE `template_id` = 1561;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1561, 3, 3958),
(1561, 4, 3542),
(1561, 13, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 1562;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1562, 5, 3000),
(1562, 6, 3530),
(1562, 45, 3470);

DELETE FROM `item_budget_template` WHERE `template_id` = 1563;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1563, 4, 3438),
(1563, 13, 3750),
(1563, 12, 2812);

DELETE FROM `item_budget_template` WHERE `template_id` = 1564;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1564, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1565;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1565, 5, 4006),
(1565, 45, 5994);

DELETE FROM `item_budget_template` WHERE `template_id` = 1566;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1566, 5, 3975),
(1566, 45, 6025);

DELETE FROM `item_budget_template` WHERE `template_id` = 1567;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1567, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1568;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1568, 4, 3750),
(1568, 3, 3438),
(1568, 12, 2812);

DELETE FROM `item_budget_template` WHERE `template_id` = 1569;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1569, 3, 4324),
(1569, 4, 2973),
(1569, 31, 2703);

DELETE FROM `item_budget_template` WHERE `template_id` = 1570;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1570, 5, 3456),
(1570, 4, 2514),
(1570, 45, 4030);

DELETE FROM `item_budget_template` WHERE `template_id` = 1571;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1571, 3, 2055),
(1571, 4, 2569),
(1571, 5, 2740),
(1571, 45, 2636);

DELETE FROM `item_budget_template` WHERE `template_id` = 1572;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1572, 3, 1751),
(1572, 4, 2627),
(1572, 5, 2627),
(1572, 45, 2995);

DELETE FROM `item_budget_template` WHERE `template_id` = 1573;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1573, 4, 4286),
(1573, 3, 2857),
(1573, 12, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 1574;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1574, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1575;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1575, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1576;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1576, 5, 1315),
(1576, 45, 6932),
(1576, 31, 1753);

DELETE FROM `item_budget_template` WHERE `template_id` = 1577;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1577, 3, 7027),
(1577, 4, 2973);

DELETE FROM `item_budget_template` WHERE `template_id` = 1578;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1578, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1579;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1579, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1580;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1580, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1581;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1581, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1582;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1582, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1583;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1583, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1584;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1584, 5, 4006),
(1584, 45, 5994);

DELETE FROM `item_budget_template` WHERE `template_id` = 1585;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1585, 32, 5391),
(1585, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 1586;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1586, 5, 3666),
(1586, 45, 3483),
(1586, 32, 2851);

DELETE FROM `item_budget_template` WHERE `template_id` = 1587;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1587, 5, 3666),
(1587, 32, 2851),
(1587, 45, 3483);

DELETE FROM `item_budget_template` WHERE `template_id` = 1588;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1588, 4, 6154),
(1588, 12, 3846);

DELETE FROM `item_budget_template` WHERE `template_id` = 1589;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1589, 5, 3387),
(1589, 4, 3175),
(1589, 45, 3438);

DELETE FROM `item_budget_template` WHERE `template_id` = 1590;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1590, 4, 2500),
(1590, 32, 4375),
(1590, 31, 3125);

DELETE FROM `item_budget_template` WHERE `template_id` = 1591;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1591, 5, 3905),
(1591, 6, 2386),
(1591, 45, 3709);

DELETE FROM `item_budget_template` WHERE `template_id` = 1592;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1592, 4, 6066),
(1592, 32, 2295),
(1592, 31, 1639);

DELETE FROM `item_budget_template` WHERE `template_id` = 1593;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1593, 45, 6042),
(1593, 32, 3958);

DELETE FROM `item_budget_template` WHERE `template_id` = 1594;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1594, 37, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1595;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1595, 45, 6158),
(1595, 31, 3842);

DELETE FROM `item_budget_template` WHERE `template_id` = 1596;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1596, 5, 1833),
(1596, 45, 8167);

DELETE FROM `item_budget_template` WHERE `template_id` = 1597;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1597, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1598;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1598, 5, 5909),
(1598, 6, 4091);

DELETE FROM `item_budget_template` WHERE `template_id` = 1599;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1599, 5, 5769),
(1599, 6, 4231);

DELETE FROM `item_budget_template` WHERE `template_id` = 1600;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1600, 5, 5556),
(1600, 6, 4444);

DELETE FROM `item_budget_template` WHERE `template_id` = 1601;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1601, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1602;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1602, 5, 4073),
(1602, 4, 2444),
(1602, 45, 3483);

DELETE FROM `item_budget_template` WHERE `template_id` = 1603;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1603, 5, 3871),
(1603, 4, 2323),
(1603, 45, 3806);

DELETE FROM `item_budget_template` WHERE `template_id` = 1604;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1604, 4, 4412),
(1604, 3, 2647),
(1604, 12, 2941);

DELETE FROM `item_budget_template` WHERE `template_id` = 1605;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1605, 4, 6667),
(1605, 31, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1606;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1606, 4, 5000),
(1606, 3, 2778),
(1606, 12, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 1607;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1607, 4, 4773),
(1607, 3, 2954),
(1607, 31, 2273);

DELETE FROM `item_budget_template` WHERE `template_id` = 1608;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1608, 4, 5714),
(1608, 32, 4286);

DELETE FROM `item_budget_template` WHERE `template_id` = 1609;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1609, 4, 5625),
(1609, 32, 4375);

DELETE FROM `item_budget_template` WHERE `template_id` = 1610;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1610, 4, 5682),
(1610, 3, 2500),
(1610, 12, 1818);

DELETE FROM `item_budget_template` WHERE `template_id` = 1611;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1611, 4, 5000),
(1611, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1612;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1612, 3, 6296),
(1612, 4, 3704);

DELETE FROM `item_budget_template` WHERE `template_id` = 1613;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1613, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1614;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1614, 3, 6818),
(1614, 4, 3182);

DELETE FROM `item_budget_template` WHERE `template_id` = 1615;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1615, 3, 4906),
(1615, 4, 2453),
(1615, 32, 2641);

DELETE FROM `item_budget_template` WHERE `template_id` = 1616;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1616, 3, 6486),
(1616, 4, 3514);

DELETE FROM `item_budget_template` WHERE `template_id` = 1617;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1617, 3, 6250),
(1617, 4, 3750);

DELETE FROM `item_budget_template` WHERE `template_id` = 1618;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1618, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1619;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1619, 3, 6078),
(1619, 31, 3922);

DELETE FROM `item_budget_template` WHERE `template_id` = 1620;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1620, 3, 5238),
(1620, 5, 4762);

DELETE FROM `item_budget_template` WHERE `template_id` = 1621;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1621, 3, 6875),
(1621, 5, 3125);

DELETE FROM `item_budget_template` WHERE `template_id` = 1622;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1622, 3, 4054),
(1622, 5, 3243),
(1622, 31, 2703);

DELETE FROM `item_budget_template` WHERE `template_id` = 1623;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1623, 3, 3438),
(1623, 5, 3437),
(1623, 38, 3125);

DELETE FROM `item_budget_template` WHERE `template_id` = 1624;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1624, 3, 4444),
(1624, 5, 5556);

DELETE FROM `item_budget_template` WHERE `template_id` = 1625;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1625, 3, 6786),
(1625, 5, 3214);

DELETE FROM `item_budget_template` WHERE `template_id` = 1626;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1626, 3, 3864),
(1626, 5, 2954),
(1626, 32, 3182);

DELETE FROM `item_budget_template` WHERE `template_id` = 1627;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1627, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1628;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1628, 5, 4246),
(1628, 6, 2123),
(1628, 45, 3631);

DELETE FROM `item_budget_template` WHERE `template_id` = 1629;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1629, 5, 5034),
(1629, 6, 2097),
(1629, 45, 2869);

DELETE FROM `item_budget_template` WHERE `template_id` = 1630;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1630, 6, 2275),
(1630, 5, 3640),
(1630, 45, 4085);

DELETE FROM `item_budget_template` WHERE `template_id` = 1631;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1631, 5, 4006),
(1631, 6, 2244),
(1631, 45, 1507),
(1631, 32, 2243);

DELETE FROM `item_budget_template` WHERE `template_id` = 1632;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1632, 6, 2385),
(1632, 5, 3253),
(1632, 31, 1952),
(1632, 45, 2410);

DELETE FROM `item_budget_template` WHERE `template_id` = 1633;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1633, 6, 2189),
(1633, 5, 4816),
(1633, 45, 2995);

DELETE FROM `item_budget_template` WHERE `template_id` = 1634;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1634, 5, 5364),
(1634, 6, 2208),
(1634, 45, 2428);

DELETE FROM `item_budget_template` WHERE `template_id` = 1635;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1635, 5, 5243),
(1635, 6, 1888),
(1635, 45, 2869);

DELETE FROM `item_budget_template` WHERE `template_id` = 1636;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1636, 5, 6093),
(1636, 45, 3907);

DELETE FROM `item_budget_template` WHERE `template_id` = 1637;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1637, 5, 6369),
(1637, 45, 3631);

DELETE FROM `item_budget_template` WHERE `template_id` = 1638;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1638, 5, 6055),
(1638, 45, 3945);

DELETE FROM `item_budget_template` WHERE `template_id` = 1639;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1639, 5, 6093),
(1639, 45, 3907);

DELETE FROM `item_budget_template` WHERE `template_id` = 1640;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1640, 5, 5254),
(1640, 45, 2995),
(1640, 31, 1751);

DELETE FROM `item_budget_template` WHERE `template_id` = 1641;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1641, 5, 4756),
(1641, 45, 2218),
(1641, 32, 3026);

DELETE FROM `item_budget_template` WHERE `template_id` = 1642;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1642, 5, 5771),
(1642, 45, 4229);

DELETE FROM `item_budget_template` WHERE `template_id` = 1643;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1643, 5, 4003),
(1643, 31, 2574),
(1643, 45, 3423);

DELETE FROM `item_budget_template` WHERE `template_id` = 1644;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1644, 5, 3687),
(1644, 6, 3403),
(1644, 45, 2910);

DELETE FROM `item_budget_template` WHERE `template_id` = 1645;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1645, 5, 3376),
(1645, 6, 3376),
(1645, 45, 3248);

DELETE FROM `item_budget_template` WHERE `template_id` = 1646;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1646, 5, 3014),
(1646, 6, 2837),
(1646, 45, 1667),
(1646, 32, 2482);

DELETE FROM `item_budget_template` WHERE `template_id` = 1647;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1647, 6, 3229),
(1647, 5, 4223),
(1647, 45, 2548);

DELETE FROM `item_budget_template` WHERE `template_id` = 1648;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1648, 5, 3687),
(1648, 6, 3403),
(1648, 45, 2910);

DELETE FROM `item_budget_template` WHERE `template_id` = 1649;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1649, 5, 4786),
(1649, 6, 2610),
(1649, 45, 2604);

DELETE FROM `item_budget_template` WHERE `template_id` = 1650;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1650, 6, 3403),
(1650, 5, 3687),
(1650, 45, 2910);

DELETE FROM `item_budget_template` WHERE `template_id` = 1651;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1651, 5, 3528),
(1651, 6, 3024),
(1651, 45, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 1652;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1652, 5, 3519),
(1652, 4, 3199),
(1652, 45, 3282);

DELETE FROM `item_budget_template` WHERE `template_id` = 1653;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1653, 5, 2711),
(1653, 4, 2711),
(1653, 6, 2260),
(1653, 45, 2318);

DELETE FROM `item_budget_template` WHERE `template_id` = 1654;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1654, 5, 3623),
(1654, 4, 3623),
(1654, 45, 2754);

DELETE FROM `item_budget_template` WHERE `template_id` = 1655;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1655, 5, 2395),
(1655, 4, 2254),
(1655, 6, 1691),
(1655, 45, 1687),
(1655, 32, 1973);

DELETE FROM `item_budget_template` WHERE `template_id` = 1656;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1656, 5, 2378),
(1656, 4, 2162),
(1656, 32, 3242),
(1656, 45, 2218);

DELETE FROM `item_budget_template` WHERE `template_id` = 1657;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1657, 4, 2254),
(1657, 5, 2395),
(1657, 6, 1691),
(1657, 45, 1687),
(1657, 32, 1973);

DELETE FROM `item_budget_template` WHERE `template_id` = 1658;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1658, 4, 3053),
(1658, 5, 3244),
(1658, 6, 1908),
(1658, 45, 1795);

DELETE FROM `item_budget_template` WHERE `template_id` = 1659;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1659, 5, 3519),
(1659, 4, 3199),
(1659, 45, 3282);

DELETE FROM `item_budget_template` WHERE `template_id` = 1660;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1660, 5, 3623),
(1660, 6, 3623),
(1660, 45, 2754);

DELETE FROM `item_budget_template` WHERE `template_id` = 1661;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1661, 4, 2711),
(1661, 5, 2711),
(1661, 6, 2260),
(1661, 45, 2318);

DELETE FROM `item_budget_template` WHERE `template_id` = 1662;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1662, 5, 3561),
(1662, 6, 2035),
(1662, 45, 2030),
(1662, 32, 2374);

DELETE FROM `item_budget_template` WHERE `template_id` = 1663;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1663, 5, 3519),
(1663, 4, 3199),
(1663, 45, 3282);

DELETE FROM `item_budget_template` WHERE `template_id` = 1664;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1664, 4, 2769),
(1664, 5, 4153),
(1664, 45, 3078);

DELETE FROM `item_budget_template` WHERE `template_id` = 1665;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1665, 6, 3053),
(1665, 5, 3244),
(1665, 4, 1908),
(1665, 45, 1795);

DELETE FROM `item_budget_template` WHERE `template_id` = 1666;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1666, 5, 2666),
(1666, 6, 2424),
(1666, 4, 2423),
(1666, 45, 2487);

DELETE FROM `item_budget_template` WHERE `template_id` = 1667;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1667, 5, 2395),
(1667, 6, 2254),
(1667, 4, 1691),
(1667, 32, 1973),
(1667, 45, 1687);

DELETE FROM `item_budget_template` WHERE `template_id` = 1668;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1668, 5, 3078),
(1668, 6, 2052),
(1668, 4, 1539),
(1668, 3, 1796),
(1668, 45, 1535);

DELETE FROM `item_budget_template` WHERE `template_id` = 1669;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1669, 6, 1984),
(1669, 5, 2381),
(1669, 4, 2380),
(1669, 3, 1389),
(1669, 45, 1866);

DELETE FROM `item_budget_template` WHERE `template_id` = 1670;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1670, 5, 3606),
(1670, 4, 1803),
(1670, 3, 1803),
(1670, 6, 1503),
(1670, 45, 1285);

DELETE FROM `item_budget_template` WHERE `template_id` = 1671;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1671, 5, 2440),
(1671, 6, 2296),
(1671, 4, 2009),
(1671, 3, 1292),
(1671, 45, 1963);

DELETE FROM `item_budget_template` WHERE `template_id` = 1672;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1672, 6, 1991),
(1672, 5, 2352),
(1672, 3, 1810),
(1672, 4, 1990),
(1672, 45, 1857);

DELETE FROM `item_budget_template` WHERE `template_id` = 1673;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1673, 5, 2269),
(1673, 6, 2269),
(1673, 4, 2269),
(1673, 3, 1945),
(1673, 45, 1248);

DELETE FROM `item_budget_template` WHERE `template_id` = 1674;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1674, 5, 3798),
(1674, 6, 1899),
(1674, 4, 1899),
(1674, 3, 1187),
(1674, 45, 1217);

DELETE FROM `item_budget_template` WHERE `template_id` = 1675;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1675, 5, 2566),
(1675, 6, 2113),
(1675, 4, 2415),
(1675, 3, 1358),
(1675, 45, 1548);

DELETE FROM `item_budget_template` WHERE `template_id` = 1676;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1676, 5, 5191),
(1676, 45, 4809);

DELETE FROM `item_budget_template` WHERE `template_id` = 1677;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1677, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1678;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1678, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1679;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1679, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1680;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1680, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1681;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1681, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1682;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1682, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1683;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1683, 15, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1684;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1684, 4, 4737),
(1684, 3, 5263);

DELETE FROM `item_budget_template` WHERE `template_id` = 1685;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1685, 3, 5172),
(1685, 5, 2069),
(1685, 31, 2759);

DELETE FROM `item_budget_template` WHERE `template_id` = 1686;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1686, 5, 4936),
(1686, 45, 5064);

DELETE FROM `item_budget_template` WHERE `template_id` = 1687;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1687, 5, 6923),
(1687, 31, 3077);

DELETE FROM `item_budget_template` WHERE `template_id` = 1688;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1688, 3, 6774),
(1688, 31, 3226);

DELETE FROM `item_budget_template` WHERE `template_id` = 1689;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1689, 6, 3336),
(1689, 5, 3336),
(1689, 45, 3328);

DELETE FROM `item_budget_template` WHERE `template_id` = 1690;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1690, 5, 3126),
(1690, 45, 6874);

DELETE FROM `item_budget_template` WHERE `template_id` = 1691;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1691, 5, 1884),
(1691, 45, 6442),
(1691, 31, 1674);

DELETE FROM `item_budget_template` WHERE `template_id` = 1692;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1692, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1693;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1693, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1694;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1694, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1695;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1695, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1696;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1696, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1697;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1697, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1698;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1698, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1699;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1699, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1700;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1700, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1701;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1701, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1702;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1702, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1703;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1703, 4, 2941),
(1703, 3, 7059);

DELETE FROM `item_budget_template` WHERE `template_id` = 1704;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1704, 5, 2946),
(1704, 45, 7054);

DELETE FROM `item_budget_template` WHERE `template_id` = 1705;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1705, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1706;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1706, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1707;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1707, 5, 3000),
(1707, 32, 7000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1708;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1708, 5, 3775),
(1708, 6, 3356),
(1708, 45, 2869);

DELETE FROM `item_budget_template` WHERE `template_id` = 1709;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1709, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1710;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1710, 45, 2591),
(1710, 31, 2694),
(1710, 32, 4715);

DELETE FROM `item_budget_template` WHERE `template_id` = 1711;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1711, 5, 5789),
(1711, 31, 4211);

DELETE FROM `item_budget_template` WHERE `template_id` = 1712;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1712, 4, 4118),
(1712, 12, 5882);

DELETE FROM `item_budget_template` WHERE `template_id` = 1713;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1713, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1714;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1714, 5, 3939),
(1714, 45, 6061);

DELETE FROM `item_budget_template` WHERE `template_id` = 1715;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1715, 5, 2624),
(1715, 6, 2249),
(1715, 45, 5127);

DELETE FROM `item_budget_template` WHERE `template_id` = 1716;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1716, 5, 2291),
(1716, 45, 5876),
(1716, 31, 1833);

DELETE FROM `item_budget_template` WHERE `template_id` = 1717;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1717, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1718;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1718, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1719;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1719, 31, 3690),
(1719, 45, 6310);

DELETE FROM `item_budget_template` WHERE `template_id` = 1720;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1720, 3, 6000),
(1720, 31, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1721;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1721, 5, 4006),
(1721, 45, 5994);

DELETE FROM `item_budget_template` WHERE `template_id` = 1722;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1722, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1723;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1723, 3, 2857),
(1723, 31, 7143);

DELETE FROM `item_budget_template` WHERE `template_id` = 1724;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1724, 4, 6875),
(1724, 31, 3125);

DELETE FROM `item_budget_template` WHERE `template_id` = 1725;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1725, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1726;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1726, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1727;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1727, 5, 2597),
(1727, 45, 7403);

DELETE FROM `item_budget_template` WHERE `template_id` = 1728;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1728, 5, 2597),
(1728, 45, 7403);

DELETE FROM `item_budget_template` WHERE `template_id` = 1729;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1729, 31, 4167),
(1729, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 1730;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1730, 4, 4688),
(1730, 31, 3125),
(1730, 32, 2187);

DELETE FROM `item_budget_template` WHERE `template_id` = 1731;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1731, 5, 3390),
(1731, 6, 2938),
(1731, 45, 3672);

DELETE FROM `item_budget_template` WHERE `template_id` = 1732;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1732, 5, 3376),
(1732, 31, 3376),
(1732, 45, 3248);

DELETE FROM `item_budget_template` WHERE `template_id` = 1733;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1733, 5, 3395),
(1733, 6, 3703),
(1733, 45, 2902);

DELETE FROM `item_budget_template` WHERE `template_id` = 1734;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1734, 6, 2862),
(1734, 45, 7138);

DELETE FROM `item_budget_template` WHERE `template_id` = 1735;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1735, 5, 2910),
(1735, 6, 2687),
(1735, 45, 4403);

DELETE FROM `item_budget_template` WHERE `template_id` = 1736;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1736, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1737;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1737, 5, 2408),
(1737, 6, 2208),
(1737, 45, 2574),
(1737, 32, 2810);

DELETE FROM `item_budget_template` WHERE `template_id` = 1738;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1738, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1739;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1739, 4, 4118),
(1739, 31, 5882);

DELETE FROM `item_budget_template` WHERE `template_id` = 1740;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1740, 5, 6369),
(1740, 45, 3631);

DELETE FROM `item_budget_template` WHERE `template_id` = 1741;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1741, 4, 2876),
(1741, 12, 2740),
(1741, 13, 1644),
(1741, 31, 2740);

DELETE FROM `item_budget_template` WHERE `template_id` = 1742;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1742, 4, 4259),
(1742, 12, 3519),
(1742, 13, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 1743;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1743, 4, 3889),
(1743, 13, 2222),
(1743, 12, 3889);

DELETE FROM `item_budget_template` WHERE `template_id` = 1744;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1744, 4, 4103),
(1744, 31, 2564),
(1744, 12, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1745;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1745, 4, 3750),
(1745, 12, 3250),
(1745, 13, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1746;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1746, 4, 3954),
(1746, 12, 3023),
(1746, 15, 3023);

DELETE FROM `item_budget_template` WHERE `template_id` = 1747;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1747, 4, 4348),
(1747, 15, 2826),
(1747, 12, 2826);

DELETE FROM `item_budget_template` WHERE `template_id` = 1748;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1748, 4, 6667),
(1748, 12, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1749;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1749, 5, 5230),
(1749, 45, 4770);

DELETE FROM `item_budget_template` WHERE `template_id` = 1750;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1750, 5, 4284),
(1750, 45, 3781),
(1750, 32, 1935);

DELETE FROM `item_budget_template` WHERE `template_id` = 1751;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1751, 5, 5884),
(1751, 45, 4116);

DELETE FROM `item_budget_template` WHERE `template_id` = 1752;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1752, 5, 4858),
(1752, 32, 2194),
(1752, 45, 2948);

DELETE FROM `item_budget_template` WHERE `template_id` = 1753;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1753, 5, 3764),
(1753, 45, 4209),
(1753, 32, 2027);

DELETE FROM `item_budget_template` WHERE `template_id` = 1754;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1754, 5, 3849),
(1754, 32, 2695),
(1754, 45, 3456);

DELETE FROM `item_budget_template` WHERE `template_id` = 1755;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1755, 5, 3543),
(1755, 45, 3702),
(1755, 32, 2755);

DELETE FROM `item_budget_template` WHERE `template_id` = 1756;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1756, 5, 6176),
(1756, 45, 3824);

DELETE FROM `item_budget_template` WHERE `template_id` = 1757;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1757, 45, 4018),
(1757, 32, 5982);

DELETE FROM `item_budget_template` WHERE `template_id` = 1758;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1758, 3, 4348),
(1758, 5, 2174),
(1758, 31, 1449),
(1758, 32, 2029);

DELETE FROM `item_budget_template` WHERE `template_id` = 1759;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1759, 3, 5385),
(1759, 5, 1923),
(1759, 32, 2692);

DELETE FROM `item_budget_template` WHERE `template_id` = 1760;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1760, 3, 3443),
(1760, 5, 1967),
(1760, 32, 4590);

DELETE FROM `item_budget_template` WHERE `template_id` = 1761;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1761, 3, 4545),
(1761, 5, 2273),
(1761, 32, 3182);

DELETE FROM `item_budget_template` WHERE `template_id` = 1762;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1762, 3, 5500),
(1762, 5, 2000),
(1762, 31, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 1763;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1763, 3, 3556),
(1763, 5, 3333),
(1763, 32, 3111);

DELETE FROM `item_budget_template` WHERE `template_id` = 1764;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1764, 3, 3077),
(1764, 5, 2308),
(1764, 31, 1923),
(1764, 32, 2692);

DELETE FROM `item_budget_template` WHERE `template_id` = 1765;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1765, 3, 6429),
(1765, 31, 3571);

DELETE FROM `item_budget_template` WHERE `template_id` = 1766;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1766, 5, 5391),
(1766, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 1767;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1767, 5, 5230),
(1767, 45, 4770);

DELETE FROM `item_budget_template` WHERE `template_id` = 1768;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1768, 5, 4936),
(1768, 45, 5064);

DELETE FROM `item_budget_template` WHERE `template_id` = 1769;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1769, 5, 5025),
(1769, 45, 4975);

DELETE FROM `item_budget_template` WHERE `template_id` = 1770;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1770, 5, 5938),
(1770, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 1771;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1771, 5, 6328),
(1771, 45, 3672);

DELETE FROM `item_budget_template` WHERE `template_id` = 1772;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1772, 5, 5706),
(1772, 45, 4294);

DELETE FROM `item_budget_template` WHERE `template_id` = 1773;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1773, 5, 5391),
(1773, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 1774;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1774, 3, 5000),
(1774, 4, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1775;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1775, 32, 7368),
(1775, 31, 2632);

DELETE FROM `item_budget_template` WHERE `template_id` = 1776;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1776, 3, 3678),
(1776, 4, 3563),
(1776, 32, 1609),
(1776, 31, 1150);

DELETE FROM `item_budget_template` WHERE `template_id` = 1777;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1777, 3, 3488),
(1777, 4, 2093),
(1777, 31, 1163),
(1777, 32, 3256);

DELETE FROM `item_budget_template` WHERE `template_id` = 1778;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1778, 3, 3235),
(1778, 4, 3235),
(1778, 32, 2059),
(1778, 31, 1471);

DELETE FROM `item_budget_template` WHERE `template_id` = 1779;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1779, 31, 4167),
(1779, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 1780;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1780, 31, 4167),
(1780, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 1781;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1781, 3, 3934),
(1781, 4, 3771),
(1781, 32, 2295);

DELETE FROM `item_budget_template` WHERE `template_id` = 1782;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1782, 3, 6500),
(1782, 32, 3500);

DELETE FROM `item_budget_template` WHERE `template_id` = 1783;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1783, 6, 2438),
(1783, 5, 3722),
(1783, 45, 3840);

DELETE FROM `item_budget_template` WHERE `template_id` = 1784;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1784, 6, 2634),
(1784, 5, 3425),
(1784, 45, 3941);

DELETE FROM `item_budget_template` WHERE `template_id` = 1785;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1785, 6, 2471),
(1785, 5, 3831),
(1785, 45, 3698);

DELETE FROM `item_budget_template` WHERE `template_id` = 1786;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1786, 6, 2134),
(1786, 5, 3913),
(1786, 45, 3953);

DELETE FROM `item_budget_template` WHERE `template_id` = 1787;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1787, 5, 3612),
(1787, 6, 2528),
(1787, 45, 3860);

DELETE FROM `item_budget_template` WHERE `template_id` = 1788;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1788, 6, 2583),
(1788, 5, 3552),
(1788, 45, 3865);

DELETE FROM `item_budget_template` WHERE `template_id` = 1789;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1789, 5, 3893),
(1789, 6, 2200),
(1789, 45, 3907);

DELETE FROM `item_budget_template` WHERE `template_id` = 1790;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1790, 5, 4712),
(1790, 45, 5288);

DELETE FROM `item_budget_template` WHERE `template_id` = 1791;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1791, 5, 3027),
(1791, 45, 4506),
(1791, 31, 897),
(1791, 32, 1570);

DELETE FROM `item_budget_template` WHERE `template_id` = 1792;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1792, 6, 1200),
(1792, 5, 3120),
(1792, 31, 960),
(1792, 45, 4720);

DELETE FROM `item_budget_template` WHERE `template_id` = 1793;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1793, 5, 2586),
(1793, 45, 3365),
(1793, 31, 900),
(1793, 32, 3149);

DELETE FROM `item_budget_template` WHERE `template_id` = 1794;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1794, 5, 3115),
(1794, 6, 1558),
(1794, 45, 5327);

DELETE FROM `item_budget_template` WHERE `template_id` = 1795;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1795, 6, 1516),
(1795, 5, 2730),
(1795, 32, 2123),
(1795, 45, 3631);

DELETE FROM `item_budget_template` WHERE `template_id` = 1796;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1796, 5, 3178),
(1796, 6, 1673),
(1796, 45, 5149);

DELETE FROM `item_budget_template` WHERE `template_id` = 1797;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1797, 6, 1589),
(1797, 5, 3336),
(1797, 45, 3804),
(1797, 31, 1271);

DELETE FROM `item_budget_template` WHERE `template_id` = 1798;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1798, 5, 3939),
(1798, 45, 6061);

DELETE FROM `item_budget_template` WHERE `template_id` = 1799;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1799, 5, 2511),
(1799, 31, 913),
(1799, 45, 4978),
(1799, 32, 1598);

DELETE FROM `item_budget_template` WHERE `template_id` = 1800;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1800, 5, 3539),
(1800, 32, 1982),
(1800, 45, 4479);

DELETE FROM `item_budget_template` WHERE `template_id` = 1801;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1801, 5, 2802),
(1801, 45, 3163),
(1801, 32, 3138),
(1801, 31, 897);

DELETE FROM `item_budget_template` WHERE `template_id` = 1802;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1802, 5, 2363),
(1802, 31, 1575),
(1802, 45, 6062);

DELETE FROM `item_budget_template` WHERE `template_id` = 1803;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1803, 5, 2789),
(1803, 45, 4770),
(1803, 32, 2441);

DELETE FROM `item_budget_template` WHERE `template_id` = 1804;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1804, 5, 3194),
(1804, 32, 2630),
(1804, 45, 4176);

DELETE FROM `item_budget_template` WHERE `template_id` = 1805;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1805, 5, 2179),
(1805, 45, 5279),
(1805, 32, 2542);

DELETE FROM `item_budget_template` WHERE `template_id` = 1806;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1806, 5, 4159),
(1806, 45, 5841);

DELETE FROM `item_budget_template` WHERE `template_id` = 1807;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1807, 6, 2725),
(1807, 5, 3503),
(1807, 45, 3772);

DELETE FROM `item_budget_template` WHERE `template_id` = 1808;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1808, 6, 3336),
(1808, 5, 3098),
(1808, 45, 3566);

DELETE FROM `item_budget_template` WHERE `template_id` = 1809;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1809, 6, 2813),
(1809, 5, 2813),
(1809, 45, 4374);

DELETE FROM `item_budget_template` WHERE `template_id` = 1810;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1810, 6, 2927),
(1810, 5, 3099),
(1810, 45, 3974);

DELETE FROM `item_budget_template` WHERE `template_id` = 1811;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1811, 6, 2378),
(1811, 5, 4025),
(1811, 45, 3597);

DELETE FROM `item_budget_template` WHERE `template_id` = 1812;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1812, 6, 3609),
(1812, 5, 3445),
(1812, 45, 2946);

DELETE FROM `item_budget_template` WHERE `template_id` = 1813;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1813, 5, 3696),
(1813, 6, 2732),
(1813, 45, 3572);

DELETE FROM `item_budget_template` WHERE `template_id` = 1814;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1814, 5, 3003),
(1814, 6, 3403),
(1814, 45, 3594);

DELETE FROM `item_budget_template` WHERE `template_id` = 1815;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1815, 4, 5385),
(1815, 32, 2692),
(1815, 31, 1923);

DELETE FROM `item_budget_template` WHERE `template_id` = 1816;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1816, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1817;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1817, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1818;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1818, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1819;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1819, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1820;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1820, 5, 5034),
(1820, 45, 4966);

DELETE FROM `item_budget_template` WHERE `template_id` = 1821;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1821, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1822;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1822, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1823;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1823, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1824;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1824, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1825;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1825, 6, 3909),
(1825, 5, 3584),
(1825, 45, 2507);

DELETE FROM `item_budget_template` WHERE `template_id` = 1826;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1826, 4, 4000),
(1826, 3, 6000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1827;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1827, 4, 5000),
(1827, 12, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1828;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1828, 4, 5294),
(1828, 12, 4706);

DELETE FROM `item_budget_template` WHERE `template_id` = 1829;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1829, 4, 4615),
(1829, 12, 5385);

DELETE FROM `item_budget_template` WHERE `template_id` = 1830;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1830, 4, 5385),
(1830, 32, 2692),
(1830, 31, 1923);

DELETE FROM `item_budget_template` WHERE `template_id` = 1831;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1831, 3, 5932),
(1831, 32, 2373),
(1831, 31, 1695);

DELETE FROM `item_budget_template` WHERE `template_id` = 1832;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1832, 4, 2456),
(1832, 5, 3860),
(1832, 32, 3684);

DELETE FROM `item_budget_template` WHERE `template_id` = 1833;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1833, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1834;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1834, 5, 4936),
(1834, 45, 5064);

DELETE FROM `item_budget_template` WHERE `template_id` = 1835;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1835, 5, 3300),
(1835, 45, 6700);

DELETE FROM `item_budget_template` WHERE `template_id` = 1836;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1836, 6, 2451),
(1836, 5, 3881),
(1836, 45, 3668);

DELETE FROM `item_budget_template` WHERE `template_id` = 1837;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1837, 3, 4545),
(1837, 5, 2273),
(1837, 32, 3182);

DELETE FROM `item_budget_template` WHERE `template_id` = 1838;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1838, 4, 5263),
(1838, 12, 4737);

DELETE FROM `item_budget_template` WHERE `template_id` = 1839;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1839, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1840;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1840, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1841;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1841, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1842;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1842, 5, 2338),
(1842, 45, 7662);

DELETE FROM `item_budget_template` WHERE `template_id` = 1843;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1843, 5, 4006),
(1843, 45, 5994);

DELETE FROM `item_budget_template` WHERE `template_id` = 1844;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1844, 4, 4419),
(1844, 32, 3256),
(1844, 31, 2325);

DELETE FROM `item_budget_template` WHERE `template_id` = 1845;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1845, 3, 5758),
(1845, 32, 4242);

DELETE FROM `item_budget_template` WHERE `template_id` = 1846;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1846, 5, 2202),
(1846, 45, 7798);

DELETE FROM `item_budget_template` WHERE `template_id` = 1847;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1847, 3, 5238),
(1847, 31, 4762);

DELETE FROM `item_budget_template` WHERE `template_id` = 1848;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1848, 5, 2788),
(1848, 6, 2603),
(1848, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 1849;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1849, 5, 3140),
(1849, 45, 6860);

DELETE FROM `item_budget_template` WHERE `template_id` = 1850;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1850, 5, 1550),
(1850, 32, 2412),
(1850, 45, 6038);

DELETE FROM `item_budget_template` WHERE `template_id` = 1851;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1851, 5, 2291),
(1851, 45, 5876),
(1851, 31, 1833);

DELETE FROM `item_budget_template` WHERE `template_id` = 1852;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1852, 12, 4054),
(1852, 13, 3243),
(1852, 31, 2703);

DELETE FROM `item_budget_template` WHERE `template_id` = 1853;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1853, 3, 6667),
(1853, 32, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1854;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1854, 4, 3039),
(1854, 3, 1381),
(1854, 6, 1243),
(1854, 5, 3038),
(1854, 45, 1299);

DELETE FROM `item_budget_template` WHERE `template_id` = 1855;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1855, 5, 3589),
(1855, 6, 1889),
(1855, 45, 4522);

DELETE FROM `item_budget_template` WHERE `template_id` = 1856;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1856, 3, 5932),
(1856, 32, 2373),
(1856, 31, 1695);

DELETE FROM `item_budget_template` WHERE `template_id` = 1857;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1857, 3, 6667),
(1857, 32, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1858;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1858, 4, 3039),
(1858, 3, 1381),
(1858, 6, 1243),
(1858, 5, 3038),
(1858, 45, 1299);

DELETE FROM `item_budget_template` WHERE `template_id` = 1859;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1859, 5, 3589),
(1859, 6, 1889),
(1859, 45, 4522);

DELETE FROM `item_budget_template` WHERE `template_id` = 1860;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1860, 4, 3164),
(1860, 32, 2109),
(1860, 31, 1507),
(1860, 45, 3220);

DELETE FROM `item_budget_template` WHERE `template_id` = 1861;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1861, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1862;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1862, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1863;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1863, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1864;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1864, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1865;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1865, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1866;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1866, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1867;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1867, 4, 4167),
(1867, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 1868;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1868, 5, 1859),
(1868, 45, 6461),
(1868, 32, 1680);

DELETE FROM `item_budget_template` WHERE `template_id` = 1869;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1869, 5, 1915),
(1869, 31, 1022),
(1869, 45, 6169),
(1869, 32, 894);

DELETE FROM `item_budget_template` WHERE `template_id` = 1870;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1870, 5, 3187),
(1870, 45, 6813);

DELETE FROM `item_budget_template` WHERE `template_id` = 1871;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1871, 3, 4000),
(1871, 32, 3500),
(1871, 31, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 1872;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1872, 5, 1417),
(1872, 45, 8583);

DELETE FROM `item_budget_template` WHERE `template_id` = 1873;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1873, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1874;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1874, 3, 5000),
(1874, 4, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1875;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1875, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1876;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1876, 5, 719),
(1876, 45, 7303),
(1876, 31, 719),
(1876, 32, 1259);

DELETE FROM `item_budget_template` WHERE `template_id` = 1877;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1877, 32, 5833),
(1877, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 1878;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1878, 5, 4451),
(1878, 45, 5549);

DELETE FROM `item_budget_template` WHERE `template_id` = 1879;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1879, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1880;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1880, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1881;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1881, 38, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1882;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1882, 4, 6056),
(1882, 32, 3944);

DELETE FROM `item_budget_template` WHERE `template_id` = 1883;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1883, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1884;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1884, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1885;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1885, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1886;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1886, 5, 2677),
(1886, 45, 7323);

DELETE FROM `item_budget_template` WHERE `template_id` = 1887;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1887, 5, 2771),
(1887, 45, 4062),
(1887, 31, 3167);

DELETE FROM `item_budget_template` WHERE `template_id` = 1888;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1888, 32, 5058),
(1888, 45, 4942);

DELETE FROM `item_budget_template` WHERE `template_id` = 1889;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1889, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1890;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1890, 4, 3026),
(1890, 5, 1396),
(1890, 3, 1396),
(1890, 6, 1396),
(1890, 45, 2786);

DELETE FROM `item_budget_template` WHERE `template_id` = 1891;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1891, 5, 4579),
(1891, 45, 5421);

DELETE FROM `item_budget_template` WHERE `template_id` = 1892;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1892, 5, 4800),
(1892, 4, 5200);

DELETE FROM `item_budget_template` WHERE `template_id` = 1893;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1893, 4, 5263),
(1893, 3, 4737);

DELETE FROM `item_budget_template` WHERE `template_id` = 1894;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1894, 5, 5562),
(1894, 45, 4438);

DELETE FROM `item_budget_template` WHERE `template_id` = 1895;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1895, 5, 3244),
(1895, 45, 4161),
(1895, 31, 2595);

DELETE FROM `item_budget_template` WHERE `template_id` = 1896;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1896, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1897;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1897, 4, 4063),
(1897, 3, 3125),
(1897, 5, 2812);

DELETE FROM `item_budget_template` WHERE `template_id` = 1898;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1898, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1899;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1899, 5, 1822),
(1899, 45, 8178);

DELETE FROM `item_budget_template` WHERE `template_id` = 1900;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1900, 5, 2638),
(1900, 32, 4104),
(1900, 45, 3258);

DELETE FROM `item_budget_template` WHERE `template_id` = 1901;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1901, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1902;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1902, 5, 2178),
(1902, 45, 7822);

DELETE FROM `item_budget_template` WHERE `template_id` = 1903;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1903, 5, 3939),
(1903, 45, 6061);

DELETE FROM `item_budget_template` WHERE `template_id` = 1904;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1904, 4, 6000),
(1904, 32, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1905;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1905, 4, 3000),
(1905, 32, 7000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1906;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1906, 3, 2445),
(1906, 5, 1333),
(1906, 32, 6222);

DELETE FROM `item_budget_template` WHERE `template_id` = 1907;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1907, 3, 2445),
(1907, 5, 1333),
(1907, 32, 6222);

DELETE FROM `item_budget_template` WHERE `template_id` = 1908;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1908, 5, 3674),
(1908, 4, 3469),
(1908, 32, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 1909;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1909, 4, 2037),
(1909, 3, 1880),
(1909, 5, 1880),
(1909, 32, 2194),
(1909, 45, 2009);

DELETE FROM `item_budget_template` WHERE `template_id` = 1910;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1910, 4, 1792),
(1910, 3, 1792),
(1910, 6, 747),
(1910, 5, 1792),
(1910, 32, 2090),
(1910, 45, 1787);

DELETE FROM `item_budget_template` WHERE `template_id` = 1911;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1911, 32, 5833),
(1911, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 1912;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1912, 32, 5833),
(1912, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 1913;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1913, 5, 3519),
(1913, 45, 6481);

DELETE FROM `item_budget_template` WHERE `template_id` = 1914;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1914, 5, 4552),
(1914, 45, 5448);

DELETE FROM `item_budget_template` WHERE `template_id` = 1915;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1915, 5, 3151),
(1915, 6, 926),
(1915, 45, 3328),
(1915, 32, 2595);

DELETE FROM `item_budget_template` WHERE `template_id` = 1916;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1916, 5, 4834),
(1916, 45, 5166);

DELETE FROM `item_budget_template` WHERE `template_id` = 1917;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1917, 5, 4552),
(1917, 45, 5448);

DELETE FROM `item_budget_template` WHERE `template_id` = 1918;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1918, 5, 3151),
(1918, 6, 926),
(1918, 32, 2595),
(1918, 45, 3328);

DELETE FROM `item_budget_template` WHERE `template_id` = 1919;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1919, 5, 3472),
(1919, 45, 3668),
(1919, 32, 2860);

DELETE FROM `item_budget_template` WHERE `template_id` = 1920;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1920, 4, 6316),
(1920, 32, 3684);

DELETE FROM `item_budget_template` WHERE `template_id` = 1921;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1921, 5, 3187),
(1921, 45, 6813);

DELETE FROM `item_budget_template` WHERE `template_id` = 1922;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1922, 12, 3125),
(1922, 13, 3750),
(1922, 31, 3125);

DELETE FROM `item_budget_template` WHERE `template_id` = 1923;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1923, 5, 2387),
(1923, 6, 2604),
(1923, 45, 5009);

DELETE FROM `item_budget_template` WHERE `template_id` = 1924;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1924, 4, 4737),
(1924, 12, 5263);

DELETE FROM `item_budget_template` WHERE `template_id` = 1925;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1925, 5, 1216),
(1925, 6, 1419),
(1925, 45, 7365);

DELETE FROM `item_budget_template` WHERE `template_id` = 1926;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1926, 5, 2505),
(1926, 45, 7495);

DELETE FROM `item_budget_template` WHERE `template_id` = 1927;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1927, 6, 5000),
(1927, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1928;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1928, 6, 2596),
(1928, 5, 2596),
(1928, 45, 4808);

DELETE FROM `item_budget_template` WHERE `template_id` = 1929;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1929, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1930;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1930, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1931;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1931, 15, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1932;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1932, 5, 2022),
(1932, 45, 5619),
(1932, 32, 2359);

DELETE FROM `item_budget_template` WHERE `template_id` = 1933;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1933, 5, 1380),
(1933, 45, 8620);

DELETE FROM `item_budget_template` WHERE `template_id` = 1934;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1934, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1935;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1935, 4, 6522),
(1935, 32, 2029),
(1935, 31, 1449);

DELETE FROM `item_budget_template` WHERE `template_id` = 1936;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1936, 5, 3418),
(1936, 6, 3076),
(1936, 45, 3506);

DELETE FROM `item_budget_template` WHERE `template_id` = 1937;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1937, 32, 5833),
(1937, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 1938;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1938, 5, 2946),
(1938, 45, 7054);

DELETE FROM `item_budget_template` WHERE `template_id` = 1939;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1939, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1940;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1940, 4, 5000),
(1940, 12, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1941;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1941, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1942;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1942, 5, 2561),
(1942, 32, 3259),
(1942, 45, 4180);

DELETE FROM `item_budget_template` WHERE `template_id` = 1943;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1943, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1944;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1944, 45, 4494),
(1944, 31, 2002),
(1944, 32, 3504);

DELETE FROM `item_budget_template` WHERE `template_id` = 1945;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1945, 13, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1946;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1946, 5, 2452),
(1946, 6, 2656),
(1946, 45, 4892);

DELETE FROM `item_budget_template` WHERE `template_id` = 1947;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1947, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1948;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1948, 45, 7937),
(1948, 31, 2063);

DELETE FROM `item_budget_template` WHERE `template_id` = 1949;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1949, 5, 5771),
(1949, 45, 4229);

DELETE FROM `item_budget_template` WHERE `template_id` = 1950;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1950, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1951;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1951, 4, 7021),
(1951, 32, 2979);

DELETE FROM `item_budget_template` WHERE `template_id` = 1952;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1952, 5, 3550),
(1952, 45, 6450);

DELETE FROM `item_budget_template` WHERE `template_id` = 1953;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1953, 6, 2225),
(1953, 5, 2448),
(1953, 45, 5327);

DELETE FROM `item_budget_template` WHERE `template_id` = 1954;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1954, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1955;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1955, 32, 5833),
(1955, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 1956;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1956, 3, 6522),
(1956, 31, 3478);

DELETE FROM `item_budget_template` WHERE `template_id` = 1957;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1957, 15, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1958;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1958, 3, 2500),
(1958, 32, 4375),
(1958, 31, 3125);

DELETE FROM `item_budget_template` WHERE `template_id` = 1959;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1959, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1960;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1960, 5, 2617),
(1960, 45, 7383);

DELETE FROM `item_budget_template` WHERE `template_id` = 1961;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1961, 5, 1532),
(1961, 45, 4256),
(1961, 32, 2680),
(1961, 31, 1532);

DELETE FROM `item_budget_template` WHERE `template_id` = 1962;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1962, 5, 1992),
(1962, 45, 4025),
(1962, 32, 2535),
(1962, 31, 1448);

DELETE FROM `item_budget_template` WHERE `template_id` = 1963;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1963, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1964;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1964, 5, 926),
(1964, 45, 9074);

DELETE FROM `item_budget_template` WHERE `template_id` = 1965;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1965, 5, 1464),
(1965, 45, 2681),
(1965, 32, 5855);

DELETE FROM `item_budget_template` WHERE `template_id` = 1966;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1966, 5, 6667),
(1966, 6, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 1967;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1967, 13, 4444),
(1967, 12, 5556);

DELETE FROM `item_budget_template` WHERE `template_id` = 1968;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1968, 3, 4000),
(1968, 4, 4000),
(1968, 31, 2000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1969;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1969, 5, 2817),
(1969, 6, 2817),
(1969, 45, 4366);

DELETE FROM `item_budget_template` WHERE `template_id` = 1970;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1970, 5, 2014),
(1970, 45, 5166),
(1970, 32, 2820);

DELETE FROM `item_budget_template` WHERE `template_id` = 1971;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1971, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1972;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1972, 5, 3259),
(1972, 6, 3258),
(1972, 45, 3483);

DELETE FROM `item_budget_template` WHERE `template_id` = 1973;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1973, 5, 4834),
(1973, 45, 5166);

DELETE FROM `item_budget_template` WHERE `template_id` = 1974;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1974, 5, 4834),
(1974, 45, 5166);

DELETE FROM `item_budget_template` WHERE `template_id` = 1975;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1975, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1976;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1976, 4, 6000),
(1976, 32, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1977;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1977, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1978;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1978, 5, 1758),
(1978, 45, 4725),
(1978, 32, 3517);

DELETE FROM `item_budget_template` WHERE `template_id` = 1979;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1979, 3, 4189),
(1979, 4, 2027),
(1979, 32, 3784);

DELETE FROM `item_budget_template` WHERE `template_id` = 1980;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1980, 4, 5200),
(1980, 32, 2800),
(1980, 31, 2000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1981;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1981, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1982;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1982, 5, 3091),
(1982, 32, 3606),
(1982, 45, 3303);

DELETE FROM `item_budget_template` WHERE `template_id` = 1983;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1983, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1984;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1984, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1985;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1985, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1986;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1986, 5, 1792),
(1986, 6, 1255),
(1986, 45, 4444),
(1986, 32, 2509);

DELETE FROM `item_budget_template` WHERE `template_id` = 1987;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1987, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1988;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1988, 5, 5058),
(1988, 45, 4942);

DELETE FROM `item_budget_template` WHERE `template_id` = 1989;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1989, 4, 5000),
(1989, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 1990;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1990, 5, 5058),
(1990, 45, 4942);

DELETE FROM `item_budget_template` WHERE `template_id` = 1991;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1991, 5, 3031),
(1991, 6, 4378),
(1991, 45, 2591);

DELETE FROM `item_budget_template` WHERE `template_id` = 1992;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1992, 5, 6282),
(1992, 45, 3718);

DELETE FROM `item_budget_template` WHERE `template_id` = 1993;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1993, 4, 3231),
(1993, 3, 3077),
(1993, 32, 2154),
(1993, 31, 1538);

DELETE FROM `item_budget_template` WHERE `template_id` = 1994;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1994, 5, 2954),
(1994, 45, 7046);

DELETE FROM `item_budget_template` WHERE `template_id` = 1995;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1995, 4, 5882),
(1995, 32, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 1996;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1996, 5, 2086),
(1996, 45, 4994),
(1996, 32, 2920);

DELETE FROM `item_budget_template` WHERE `template_id` = 1997;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1997, 32, 5833),
(1997, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 1998;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1998, 4, 5484),
(1998, 32, 4516);

DELETE FROM `item_budget_template` WHERE `template_id` = 1999;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1999, 4, 4667),
(1999, 32, 3111),
(1999, 31, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 2000;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2000, 3, 2449),
(2000, 5, 1837),
(2000, 32, 5714);

DELETE FROM `item_budget_template` WHERE `template_id` = 2001;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2001, 3, 4615),
(2001, 32, 5385);

DELETE FROM `item_budget_template` WHERE `template_id` = 2002;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2002, 3, 1781),
(2002, 4, 2374),
(2002, 5, 2374),
(2002, 6, 1187),
(2002, 45, 2284);

DELETE FROM `item_budget_template` WHERE `template_id` = 2003;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2003, 4, 2502),
(2003, 3, 1251),
(2003, 6, 1251),
(2003, 5, 2501),
(2003, 45, 2495);

DELETE FROM `item_budget_template` WHERE `template_id` = 2004;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2004, 5, 3603),
(2004, 45, 3594),
(2004, 32, 2803);

DELETE FROM `item_budget_template` WHERE `template_id` = 2005;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2005, 5, 3489),
(2005, 45, 2754),
(2005, 32, 3757);

DELETE FROM `item_budget_template` WHERE `template_id` = 2006;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2006, 32, 5833),
(2006, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 2007;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2007, 32, 5833),
(2007, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 2008;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2008, 5, 3721),
(2008, 4, 1395),
(2008, 32, 4884);

DELETE FROM `item_budget_template` WHERE `template_id` = 2009;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2009, 5, 2391),
(2009, 4, 1196),
(2009, 45, 3066),
(2009, 32, 3347);

DELETE FROM `item_budget_template` WHERE `template_id` = 2010;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2010, 5, 5006),
(2010, 45, 4994);

DELETE FROM `item_budget_template` WHERE `template_id` = 2011;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2011, 5, 4673),
(2011, 45, 5327);

DELETE FROM `item_budget_template` WHERE `template_id` = 2012;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2012, 5, 3217),
(2012, 6, 1072),
(2012, 32, 2502),
(2012, 45, 3209);

DELETE FROM `item_budget_template` WHERE `template_id` = 2013;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2013, 5, 2630),
(2013, 6, 957),
(2013, 45, 3066),
(2013, 32, 3347);

DELETE FROM `item_budget_template` WHERE `template_id` = 2014;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2014, 4, 3375),
(2014, 5, 2382),
(2014, 45, 4243);

DELETE FROM `item_budget_template` WHERE `template_id` = 2015;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2015, 4, 3504),
(2015, 5, 2336),
(2015, 45, 4160);

DELETE FROM `item_budget_template` WHERE `template_id` = 2016;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2016, 4, 4615),
(2016, 32, 5385);

DELETE FROM `item_budget_template` WHERE `template_id` = 2017;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2017, 4, 3259),
(2017, 5, 3258),
(2017, 45, 3483);

DELETE FROM `item_budget_template` WHERE `template_id` = 2018;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2018, 4, 3446),
(2018, 5, 2298),
(2018, 45, 4256);

DELETE FROM `item_budget_template` WHERE `template_id` = 2019;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2019, 4, 3581),
(2019, 5, 2046),
(2019, 45, 4373);

DELETE FROM `item_budget_template` WHERE `template_id` = 2020;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2020, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2021;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2021, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2022;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2022, 4, 4063),
(2022, 3, 3125),
(2022, 5, 2812);

DELETE FROM `item_budget_template` WHERE `template_id` = 2023;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2023, 4, 3026),
(2023, 5, 1396),
(2023, 3, 1396),
(2023, 6, 1396),
(2023, 45, 2786);

DELETE FROM `item_budget_template` WHERE `template_id` = 2024;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2024, 5, 1822),
(2024, 45, 8178);

DELETE FROM `item_budget_template` WHERE `template_id` = 2025;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2025, 5, 4579),
(2025, 45, 5421);

DELETE FROM `item_budget_template` WHERE `template_id` = 2026;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2026, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2027;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2027, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2028;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2028, 4, 5263),
(2028, 3, 4737);

DELETE FROM `item_budget_template` WHERE `template_id` = 2029;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2029, 5, 2178),
(2029, 45, 7822);

DELETE FROM `item_budget_template` WHERE `template_id` = 2030;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2030, 5, 5562),
(2030, 45, 4438);

DELETE FROM `item_budget_template` WHERE `template_id` = 2031;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2031, 5, 3939),
(2031, 45, 6061);

DELETE FROM `item_budget_template` WHERE `template_id` = 2032;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2032, 5, 3244),
(2032, 45, 4161),
(2032, 31, 2595);

DELETE FROM `item_budget_template` WHERE `template_id` = 2033;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2033, 3, 2445),
(2033, 5, 1333),
(2033, 32, 6222);

DELETE FROM `item_budget_template` WHERE `template_id` = 2034;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2034, 3, 2445),
(2034, 5, 1333),
(2034, 32, 6222);

DELETE FROM `item_budget_template` WHERE `template_id` = 2035;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2035, 4, 2037),
(2035, 3, 1880),
(2035, 5, 1880),
(2035, 32, 2194),
(2035, 45, 2009);

DELETE FROM `item_budget_template` WHERE `template_id` = 2036;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2036, 4, 1792),
(2036, 3, 1792),
(2036, 6, 747),
(2036, 5, 1792),
(2036, 32, 2090),
(2036, 45, 1787);

DELETE FROM `item_budget_template` WHERE `template_id` = 2037;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2037, 5, 3519),
(2037, 45, 6481);

DELETE FROM `item_budget_template` WHERE `template_id` = 2038;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2038, 5, 4834),
(2038, 45, 5166);

DELETE FROM `item_budget_template` WHERE `template_id` = 2039;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2039, 32, 5833),
(2039, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 2040;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2040, 32, 5833),
(2040, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 2041;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2041, 4, 6000),
(2041, 32, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2042;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2042, 4, 3000),
(2042, 32, 7000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2043;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2043, 5, 4552),
(2043, 45, 5448);

DELETE FROM `item_budget_template` WHERE `template_id` = 2044;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2044, 5, 4552),
(2044, 45, 5448);

DELETE FROM `item_budget_template` WHERE `template_id` = 2045;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2045, 5, 3151),
(2045, 6, 926),
(2045, 45, 3328),
(2045, 32, 2595);

DELETE FROM `item_budget_template` WHERE `template_id` = 2046;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2046, 5, 3151),
(2046, 6, 926),
(2046, 32, 2595),
(2046, 45, 3328);

DELETE FROM `item_budget_template` WHERE `template_id` = 2047;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2047, 3, 2449),
(2047, 5, 1837),
(2047, 32, 5714);

DELETE FROM `item_budget_template` WHERE `template_id` = 2048;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2048, 3, 4615),
(2048, 32, 5385);

DELETE FROM `item_budget_template` WHERE `template_id` = 2049;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2049, 3, 1781),
(2049, 4, 2374),
(2049, 5, 2374),
(2049, 6, 1187),
(2049, 45, 2284);

DELETE FROM `item_budget_template` WHERE `template_id` = 2050;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2050, 4, 2502),
(2050, 3, 1251),
(2050, 6, 1251),
(2050, 5, 2501),
(2050, 45, 2495);

DELETE FROM `item_budget_template` WHERE `template_id` = 2051;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2051, 5, 3603),
(2051, 45, 3594),
(2051, 32, 2803);

DELETE FROM `item_budget_template` WHERE `template_id` = 2052;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2052, 5, 3489),
(2052, 45, 2754),
(2052, 32, 3757);

DELETE FROM `item_budget_template` WHERE `template_id` = 2053;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2053, 32, 5833),
(2053, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 2054;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2054, 32, 5833),
(2054, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 2055;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2055, 4, 4667),
(2055, 32, 3111),
(2055, 31, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 2056;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2056, 4, 5484),
(2056, 32, 4516);

DELETE FROM `item_budget_template` WHERE `template_id` = 2057;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2057, 5, 5006),
(2057, 45, 4994);

DELETE FROM `item_budget_template` WHERE `template_id` = 2058;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2058, 5, 4673),
(2058, 45, 5327);

DELETE FROM `item_budget_template` WHERE `template_id` = 2059;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2059, 5, 3217),
(2059, 6, 1072),
(2059, 32, 2502),
(2059, 45, 3209);

DELETE FROM `item_budget_template` WHERE `template_id` = 2060;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2060, 5, 2630),
(2060, 6, 957),
(2060, 45, 3066),
(2060, 32, 3347);

DELETE FROM `item_budget_template` WHERE `template_id` = 2061;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2061, 4, 1818),
(2061, 3, 1818),
(2061, 32, 6364);

DELETE FROM `item_budget_template` WHERE `template_id` = 2062;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2062, 4, 3409),
(2062, 32, 3182),
(2062, 13, 3409);

DELETE FROM `item_budget_template` WHERE `template_id` = 2063;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2063, 5, 957),
(2063, 45, 7367),
(2063, 32, 1676);

DELETE FROM `item_budget_template` WHERE `template_id` = 2064;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2064, 5, 4834),
(2064, 45, 5166);

DELETE FROM `item_budget_template` WHERE `template_id` = 2065;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2065, 5, 3359),
(2065, 6, 3359),
(2065, 45, 3282);

DELETE FROM `item_budget_template` WHERE `template_id` = 2066;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2066, 5, 1164),
(2066, 45, 8836);

DELETE FROM `item_budget_template` WHERE `template_id` = 2067;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2067, 5, 5391),
(2067, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 2068;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2068, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2069;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2069, 5, 5391),
(2069, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 2070;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2070, 5, 957),
(2070, 45, 7367),
(2070, 32, 1676);

DELETE FROM `item_budget_template` WHERE `template_id` = 2071;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2071, 5, 1164),
(2071, 45, 8836);

DELETE FROM `item_budget_template` WHERE `template_id` = 2072;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2072, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2073;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2073, 5, 4834),
(2073, 45, 5166);

DELETE FROM `item_budget_template` WHERE `template_id` = 2074;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2074, 5, 1164),
(2074, 45, 8836);

DELETE FROM `item_budget_template` WHERE `template_id` = 2075;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2075, 5, 5391),
(2075, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 2076;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2076, 5, 957),
(2076, 45, 7367),
(2076, 32, 1676);

DELETE FROM `item_budget_template` WHERE `template_id` = 2077;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2077, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2078;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2078, 5, 4834),
(2078, 45, 5166);

DELETE FROM `item_budget_template` WHERE `template_id` = 2079;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2079, 5, 3359),
(2079, 6, 3359),
(2079, 45, 3282);

DELETE FROM `item_budget_template` WHERE `template_id` = 2080;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2080, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2081;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2081, 37, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2082;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2082, 5, 4586),
(2082, 45, 5414);

DELETE FROM `item_budget_template` WHERE `template_id` = 2083;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2083, 5, 3219),
(2083, 45, 3408),
(2083, 32, 2146),
(2083, 31, 1227);

DELETE FROM `item_budget_template` WHERE `template_id` = 2084;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2084, 5, 3278),
(2084, 45, 3322),
(2084, 32, 3400);

DELETE FROM `item_budget_template` WHERE `template_id` = 2085;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2085, 4, 3336),
(2085, 5, 3336),
(2085, 45, 3328);

DELETE FROM `item_budget_template` WHERE `template_id` = 2086;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2086, 5, 2572),
(2086, 4, 2723),
(2086, 32, 2118),
(2086, 45, 2587);

DELETE FROM `item_budget_template` WHERE `template_id` = 2087;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2087, 5, 2277),
(2087, 4, 2277),
(2087, 45, 2410),
(2087, 32, 3036);

DELETE FROM `item_budget_template` WHERE `template_id` = 2088;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2088, 32, 5018),
(2088, 45, 4982);

DELETE FROM `item_budget_template` WHERE `template_id` = 2089;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2089, 5, 2112),
(2089, 45, 5073),
(2089, 32, 2815);

DELETE FROM `item_budget_template` WHERE `template_id` = 2090;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2090, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2091;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2091, 5, 4936),
(2091, 45, 5064);

DELETE FROM `item_budget_template` WHERE `template_id` = 2092;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2092, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2093;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2093, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2094;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2094, 4, 5098),
(2094, 5, 4902);

DELETE FROM `item_budget_template` WHERE `template_id` = 2095;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2095, 3, 5946),
(2095, 5, 4054);

DELETE FROM `item_budget_template` WHERE `template_id` = 2096;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2096, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2097;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2097, 5, 3391),
(2097, 6, 2260),
(2097, 45, 4349);

DELETE FROM `item_budget_template` WHERE `template_id` = 2098;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2098, 4, 5455),
(2098, 32, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 2099;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2099, 5, 3606),
(2099, 6, 3091),
(2099, 45, 3303);

DELETE FROM `item_budget_template` WHERE `template_id` = 2100;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2100, 5, 5814),
(2100, 45, 4186);

DELETE FROM `item_budget_template` WHERE `template_id` = 2101;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2101, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2102;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2102, 4, 4242),
(2102, 12, 5758);

DELETE FROM `item_budget_template` WHERE `template_id` = 2103;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2103, 5, 3806),
(2103, 32, 1791),
(2103, 45, 4403);

DELETE FROM `item_budget_template` WHERE `template_id` = 2104;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2104, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2105;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2105, 5, 4412),
(2105, 6, 2118),
(2105, 45, 3470);

DELETE FROM `item_budget_template` WHERE `template_id` = 2106;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2106, 3, 4815),
(2106, 5, 5185);

DELETE FROM `item_budget_template` WHERE `template_id` = 2107;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2107, 4, 5172),
(2107, 3, 4828);

DELETE FROM `item_budget_template` WHERE `template_id` = 2108;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2108, 5, 3937),
(2108, 4, 3937),
(2108, 45, 2126);

DELETE FROM `item_budget_template` WHERE `template_id` = 2109;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2109, 5, 5230),
(2109, 45, 4770);

DELETE FROM `item_budget_template` WHERE `template_id` = 2110;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2110, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2111;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2111, 5, 5000),
(2111, 6, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2112;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2112, 4, 5000),
(2112, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2113;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2113, 5, 4381),
(2113, 45, 5619);

DELETE FROM `item_budget_template` WHERE `template_id` = 2114;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2114, 38, 5091),
(2114, 3, 4909);

DELETE FROM `item_budget_template` WHERE `template_id` = 2115;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2115, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2116;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2116, 5, 4936),
(2116, 45, 5064);

DELETE FROM `item_budget_template` WHERE `template_id` = 2117;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2117, 5, 3248),
(2117, 31, 2088),
(2117, 6, 1392),
(2117, 45, 3272);

DELETE FROM `item_budget_template` WHERE `template_id` = 2118;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2118, 32, 6000),
(2118, 31, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2119;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2119, 5, 1948),
(2119, 31, 1391),
(2119, 45, 6661);

DELETE FROM `item_budget_template` WHERE `template_id` = 2120;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2120, 5, 3551),
(2120, 32, 2604),
(2120, 45, 3845);

DELETE FROM `item_budget_template` WHERE `template_id` = 2121;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2121, 4, 5532),
(2121, 3, 4468);

DELETE FROM `item_budget_template` WHERE `template_id` = 2122;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2122, 4, 5593),
(2122, 5, 4407);

DELETE FROM `item_budget_template` WHERE `template_id` = 2123;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2123, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2124;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2124, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2125;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2125, 5, 1784),
(2125, 6, 1646),
(2125, 45, 6570);

DELETE FROM `item_budget_template` WHERE `template_id` = 2126;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2126, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2127;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2127, 5, 3030),
(2127, 6, 3408),
(2127, 45, 3562);

DELETE FROM `item_budget_template` WHERE `template_id` = 2128;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2128, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2129;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2129, 5, 2430),
(2129, 45, 7570);

DELETE FROM `item_budget_template` WHERE `template_id` = 2130;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2130, 4, 5758),
(2130, 3, 4242);

DELETE FROM `item_budget_template` WHERE `template_id` = 2131;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2131, 4, 5000),
(2131, 3, 3500),
(2131, 31, 1500);

DELETE FROM `item_budget_template` WHERE `template_id` = 2132;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2132, 5, 7117),
(2132, 45, 2883);

DELETE FROM `item_budget_template` WHERE `template_id` = 2133;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2133, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2134;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2134, 5, 5264),
(2134, 6, 1620),
(2134, 45, 3116);

DELETE FROM `item_budget_template` WHERE `template_id` = 2135;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2135, 5, 3714),
(2135, 6, 2476),
(2135, 45, 3810);

DELETE FROM `item_budget_template` WHERE `template_id` = 2136;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2136, 5, 4378),
(2136, 6, 2627),
(2136, 45, 2995);

DELETE FROM `item_budget_template` WHERE `template_id` = 2137;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2137, 5, 2747),
(2137, 6, 1570),
(2137, 32, 2159),
(2137, 45, 3524);

DELETE FROM `item_budget_template` WHERE `template_id` = 2138;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2138, 3, 7105),
(2138, 31, 2895);

DELETE FROM `item_budget_template` WHERE `template_id` = 2139;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2139, 5, 3478),
(2139, 6, 2981),
(2139, 45, 3541);

DELETE FROM `item_budget_template` WHERE `template_id` = 2140;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2140, 3, 6061),
(2140, 31, 3939);

DELETE FROM `item_budget_template` WHERE `template_id` = 2141;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2141, 5, 2658),
(2141, 6, 1898),
(2141, 31, 2847),
(2141, 45, 2597);

DELETE FROM `item_budget_template` WHERE `template_id` = 2142;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2142, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2143;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2143, 5, 4169),
(2143, 6, 1588),
(2143, 45, 4243);

DELETE FROM `item_budget_template` WHERE `template_id` = 2144;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2144, 5, 1791),
(2144, 31, 1536),
(2144, 45, 6673);

DELETE FROM `item_budget_template` WHERE `template_id` = 2145;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2145, 3, 3429),
(2145, 13, 6571);

DELETE FROM `item_budget_template` WHERE `template_id` = 2146;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2146, 5, 3430),
(2146, 6, 2940),
(2146, 45, 3630);

DELETE FROM `item_budget_template` WHERE `template_id` = 2147;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2147, 4, 8205),
(2147, 31, 1795);

DELETE FROM `item_budget_template` WHERE `template_id` = 2148;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2148, 4, 4359),
(2148, 5, 5641);

DELETE FROM `item_budget_template` WHERE `template_id` = 2149;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2149, 4, 5758),
(2149, 5, 4242);

DELETE FROM `item_budget_template` WHERE `template_id` = 2150;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2150, 5, 2996),
(2150, 6, 3457),
(2150, 45, 3547);

DELETE FROM `item_budget_template` WHERE `template_id` = 2151;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2151, 4, 5319),
(2151, 32, 4681);

DELETE FROM `item_budget_template` WHERE `template_id` = 2152;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2152, 5, 3166),
(2152, 32, 2322),
(2152, 45, 4512);

DELETE FROM `item_budget_template` WHERE `template_id` = 2153;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2153, 4, 4706),
(2153, 12, 5294);

DELETE FROM `item_budget_template` WHERE `template_id` = 2154;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2154, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2155;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2155, 5, 4750),
(2155, 32, 5250);

DELETE FROM `item_budget_template` WHERE `template_id` = 2156;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2156, 13, 5676),
(2156, 31, 4324);

DELETE FROM `item_budget_template` WHERE `template_id` = 2157;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2157, 5, 3400),
(2157, 6, 2078),
(2157, 45, 4522);

DELETE FROM `item_budget_template` WHERE `template_id` = 2158;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2158, 5, 2298),
(2158, 6, 2298),
(2158, 45, 5404);

DELETE FROM `item_budget_template` WHERE `template_id` = 2159;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2159, 4, 5088),
(2159, 3, 4912);

DELETE FROM `item_budget_template` WHERE `template_id` = 2160;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2160, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2161;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2161, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2162;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2162, 5, 5097),
(2162, 45, 4903);

DELETE FROM `item_budget_template` WHERE `template_id` = 2163;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2163, 3, 6389),
(2163, 31, 3611);

DELETE FROM `item_budget_template` WHERE `template_id` = 2164;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2164, 32, 4972),
(2164, 5, 2810),
(2164, 45, 2218);

DELETE FROM `item_budget_template` WHERE `template_id` = 2165;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2165, 5, 5589),
(2165, 45, 4411);

DELETE FROM `item_budget_template` WHERE `template_id` = 2166;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2166, 4, 6087),
(2166, 3, 3913);

DELETE FROM `item_budget_template` WHERE `template_id` = 2167;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2167, 32, 5000),
(2167, 31, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2168;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2168, 32, 4962),
(2168, 45, 5038);

DELETE FROM `item_budget_template` WHERE `template_id` = 2169;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2169, 32, 4962),
(2169, 45, 5038);

DELETE FROM `item_budget_template` WHERE `template_id` = 2170;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2170, 4, 6087),
(2170, 3, 3913);

DELETE FROM `item_budget_template` WHERE `template_id` = 2171;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2171, 32, 5000),
(2171, 31, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2172;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2172, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2173;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2173, 4, 3378),
(2173, 5, 3231),
(2173, 45, 3391);

DELETE FROM `item_budget_template` WHERE `template_id` = 2174;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2174, 5, 3378),
(2174, 32, 3231),
(2174, 45, 3391);

DELETE FROM `item_budget_template` WHERE `template_id` = 2175;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2175, 5, 2543),
(2175, 6, 2542),
(2175, 32, 2415),
(2175, 45, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 2176;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2176, 5, 2768),
(2176, 32, 2648),
(2176, 6, 1805),
(2176, 45, 2779);

DELETE FROM `item_budget_template` WHERE `template_id` = 2177;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2177, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2178;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2178, 5, 4936),
(2178, 45, 5064);

DELETE FROM `item_budget_template` WHERE `template_id` = 2179;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2179, 5, 4936),
(2179, 45, 5064);

DELETE FROM `item_budget_template` WHERE `template_id` = 2180;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2180, 4, 5128),
(2180, 3, 4872);

DELETE FROM `item_budget_template` WHERE `template_id` = 2181;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2181, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2182;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2182, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2183;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2183, 5, 2869),
(2183, 32, 2701),
(2183, 6, 1688),
(2183, 45, 2742);

DELETE FROM `item_budget_template` WHERE `template_id` = 2184;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2184, 12, 4800),
(2184, 31, 5200);

DELETE FROM `item_budget_template` WHERE `template_id` = 2185;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2185, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2186;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2186, 6, 1334),
(2186, 5, 1445),
(2186, 45, 7221);

DELETE FROM `item_budget_template` WHERE `template_id` = 2187;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2187, 4, 5152),
(2187, 3, 4848);

DELETE FROM `item_budget_template` WHERE `template_id` = 2188;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2188, 5, 4985),
(2188, 45, 5015);

DELETE FROM `item_budget_template` WHERE `template_id` = 2189;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2189, 32, 2576),
(2189, 5, 2899),
(2189, 6, 1771),
(2189, 45, 2754);

DELETE FROM `item_budget_template` WHERE `template_id` = 2190;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2190, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2191;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2191, 5, 3379),
(2191, 32, 3154),
(2191, 45, 3467);

DELETE FROM `item_budget_template` WHERE `template_id` = 2192;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2192, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2193;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2193, 5, 3379),
(2193, 32, 3154),
(2193, 45, 3467);

DELETE FROM `item_budget_template` WHERE `template_id` = 2194;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2194, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2195;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2195, 5, 1868),
(2195, 45, 8132);

DELETE FROM `item_budget_template` WHERE `template_id` = 2196;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2196, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2197;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2197, 5, 3543),
(2197, 31, 2755),
(2197, 45, 3702);

DELETE FROM `item_budget_template` WHERE `template_id` = 2198;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2198, 3, 5946),
(2198, 5, 4054);

DELETE FROM `item_budget_template` WHERE `template_id` = 2199;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2199, 4, 5581),
(2199, 5, 4419);

DELETE FROM `item_budget_template` WHERE `template_id` = 2200;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2200, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2201;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2201, 4, 5397),
(2201, 32, 4603);

DELETE FROM `item_budget_template` WHERE `template_id` = 2202;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2202, 5, 4962),
(2202, 45, 5038);

DELETE FROM `item_budget_template` WHERE `template_id` = 2203;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2203, 3, 5946),
(2203, 14, 4054);

DELETE FROM `item_budget_template` WHERE `template_id` = 2204;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2204, 4, 3225),
(2204, 5, 3405),
(2204, 45, 3370);

DELETE FROM `item_budget_template` WHERE `template_id` = 2205;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2205, 5, 2790),
(2205, 31, 2367),
(2205, 45, 4843);

DELETE FROM `item_budget_template` WHERE `template_id` = 2206;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2206, 3, 5385),
(2206, 31, 4615);

DELETE FROM `item_budget_template` WHERE `template_id` = 2207;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2207, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2208;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2208, 5, 4712),
(2208, 45, 5288);

DELETE FROM `item_budget_template` WHERE `template_id` = 2209;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2209, 4, 3547),
(2209, 5, 3724),
(2209, 45, 2729);

DELETE FROM `item_budget_template` WHERE `template_id` = 2210;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2210, 4, 6389),
(2210, 3, 3611);

DELETE FROM `item_budget_template` WHERE `template_id` = 2211;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2211, 5, 2705),
(2211, 6, 1709),
(2211, 32, 2421),
(2211, 45, 3165);

DELETE FROM `item_budget_template` WHERE `template_id` = 2212;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2212, 3, 5926),
(2212, 31, 4074);

DELETE FROM `item_budget_template` WHERE `template_id` = 2213;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2213, 37, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2214;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2214, 4, 5000),
(2214, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2215;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2215, 3, 5000),
(2215, 31, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2216;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2216, 31, 2941),
(2216, 32, 4118),
(2216, 3, 2941);

DELETE FROM `item_budget_template` WHERE `template_id` = 2217;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2217, 5, 5771),
(2217, 45, 4229);

DELETE FROM `item_budget_template` WHERE `template_id` = 2218;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2218, 4, 4545),
(2218, 3, 3485),
(2218, 31, 1970);

DELETE FROM `item_budget_template` WHERE `template_id` = 2219;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2219, 4, 2848),
(2219, 5, 2978),
(2219, 6, 2071),
(2219, 45, 2103);

DELETE FROM `item_budget_template` WHERE `template_id` = 2220;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2220, 5, 2807),
(2220, 6, 3540),
(2220, 45, 3653);

DELETE FROM `item_budget_template` WHERE `template_id` = 2221;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2221, 5, 4132),
(2221, 6, 2817),
(2221, 45, 3051);

DELETE FROM `item_budget_template` WHERE `template_id` = 2222;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2222, 5, 2248),
(2222, 6, 2714),
(2222, 45, 5038);

DELETE FROM `item_budget_template` WHERE `template_id` = 2223;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2223, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2224;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2224, 3, 6053),
(2224, 5, 3947);

DELETE FROM `item_budget_template` WHERE `template_id` = 2225;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2225, 3, 5918),
(2225, 31, 4082);

DELETE FROM `item_budget_template` WHERE `template_id` = 2226;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2226, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2227;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2227, 3, 5667),
(2227, 32, 4333);

DELETE FROM `item_budget_template` WHERE `template_id` = 2228;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2228, 5, 5025),
(2228, 45, 4975);

DELETE FROM `item_budget_template` WHERE `template_id` = 2229;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2229, 4, 5366),
(2229, 32, 4634);

DELETE FROM `item_budget_template` WHERE `template_id` = 2230;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2230, 5, 5000),
(2230, 32, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2231;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2231, 4, 5208),
(2231, 5, 2292),
(2231, 32, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 2232;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2232, 5, 2601),
(2232, 4, 2600),
(2232, 3, 2427),
(2232, 45, 2372);

DELETE FROM `item_budget_template` WHERE `template_id` = 2233;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2233, 3, 4750),
(2233, 32, 2250),
(2233, 5, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2234;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2234, 3, 5102),
(2234, 32, 2245),
(2234, 5, 2653);

DELETE FROM `item_budget_template` WHERE `template_id` = 2235;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2235, 5, 1765),
(2235, 4, 3530),
(2235, 3, 1235),
(2235, 45, 3470);

DELETE FROM `item_budget_template` WHERE `template_id` = 2236;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2236, 5, 4067),
(2236, 45, 5933);

DELETE FROM `item_budget_template` WHERE `template_id` = 2237;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2237, 3, 6053),
(2237, 32, 3947);

DELETE FROM `item_budget_template` WHERE `template_id` = 2238;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2238, 5, 3014),
(2238, 32, 2637),
(2238, 45, 4349);

DELETE FROM `item_budget_template` WHERE `template_id` = 2239;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2239, 4, 5952),
(2239, 32, 4048);

DELETE FROM `item_budget_template` WHERE `template_id` = 2240;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2240, 4, 7391),
(2240, 32, 2609);

DELETE FROM `item_budget_template` WHERE `template_id` = 2241;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2241, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2242;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2242, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2243;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2243, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2244;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2244, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2245;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2245, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2246;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2246, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2247;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2247, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2248;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2248, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2249;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2249, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2250;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2250, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2251;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2251, 5, 3349),
(2251, 6, 3348),
(2251, 45, 3303);

DELETE FROM `item_budget_template` WHERE `template_id` = 2252;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2252, 5, 2818),
(2252, 32, 2617),
(2252, 6, 1811),
(2252, 45, 2754);

DELETE FROM `item_budget_template` WHERE `template_id` = 2253;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2253, 4, 3415),
(2253, 3, 3414),
(2253, 31, 3171);

DELETE FROM `item_budget_template` WHERE `template_id` = 2254;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2254, 3, 5000),
(2254, 31, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2255;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2255, 6, 1372),
(2255, 5, 1783),
(2255, 32, 1920),
(2255, 45, 4925);

DELETE FROM `item_budget_template` WHERE `template_id` = 2256;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2256, 4, 5098),
(2256, 3, 4902);

DELETE FROM `item_budget_template` WHERE `template_id` = 2257;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2257, 5, 2058),
(2257, 32, 1920),
(2257, 6, 1097),
(2257, 45, 4925);

DELETE FROM `item_budget_template` WHERE `template_id` = 2258;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2258, 4, 5714),
(2258, 32, 2222),
(2258, 31, 2064);

DELETE FROM `item_budget_template` WHERE `template_id` = 2259;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2259, 5, 2067),
(2259, 4, 2225),
(2259, 45, 5708);

DELETE FROM `item_budget_template` WHERE `template_id` = 2260;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2260, 5, 4815),
(2260, 3, 5185);

DELETE FROM `item_budget_template` WHERE `template_id` = 2261;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2261, 5, 2609),
(2261, 4, 7391);

DELETE FROM `item_budget_template` WHERE `template_id` = 2262;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2262, 5, 2404),
(2262, 32, 1602),
(2262, 45, 5994);

DELETE FROM `item_budget_template` WHERE `template_id` = 2263;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2263, 4, 5173),
(2263, 3, 2069),
(2263, 31, 1379),
(2263, 13, 1379);

DELETE FROM `item_budget_template` WHERE `template_id` = 2264;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2264, 5, 2036),
(2264, 32, 1527),
(2264, 6, 1358),
(2264, 45, 5079);

DELETE FROM `item_budget_template` WHERE `template_id` = 2265;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2265, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2266;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2266, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2267;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2267, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2268;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2268, 32, 6154),
(2268, 31, 3846);

DELETE FROM `item_budget_template` WHERE `template_id` = 2269;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2269, 31, 3339),
(2269, 45, 6661);

DELETE FROM `item_budget_template` WHERE `template_id` = 2270;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2270, 4, 5000),
(2270, 32, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2271;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2271, 5, 2817),
(2271, 32, 2817),
(2271, 45, 4366);

DELETE FROM `item_budget_template` WHERE `template_id` = 2272;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2272, 3, 7297),
(2272, 32, 2703);

DELETE FROM `item_budget_template` WHERE `template_id` = 2273;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2273, 4, 4028),
(2273, 3, 2977),
(2273, 45, 2995);

DELETE FROM `item_budget_template` WHERE `template_id` = 2274;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2274, 5, 3550),
(2274, 45, 6450);

DELETE FROM `item_budget_template` WHERE `template_id` = 2275;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2275, 3, 4445),
(2275, 5, 3333),
(2275, 32, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 2276;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2276, 4, 4068),
(2276, 32, 3729),
(2276, 5, 2203);

DELETE FROM `item_budget_template` WHERE `template_id` = 2277;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2277, 5, 2469),
(2277, 32, 3704),
(2277, 45, 3827);

DELETE FROM `item_budget_template` WHERE `template_id` = 2278;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2278, 5, 5021),
(2278, 45, 4979);

DELETE FROM `item_budget_template` WHERE `template_id` = 2279;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2279, 5, 2194),
(2279, 32, 3919),
(2279, 45, 3887);

DELETE FROM `item_budget_template` WHERE `template_id` = 2280;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2280, 4, 4678),
(2280, 32, 2903),
(2280, 5, 2419);

DELETE FROM `item_budget_template` WHERE `template_id` = 2281;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2281, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2282;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2282, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2283;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2283, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2284;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2284, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2285;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2285, 5, 4890),
(2285, 45, 5110);

DELETE FROM `item_budget_template` WHERE `template_id` = 2286;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2286, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2287;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2287, 3, 5217),
(2287, 31, 4783);

DELETE FROM `item_budget_template` WHERE `template_id` = 2288;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2288, 31, 4783),
(2288, 3, 5217);

DELETE FROM `item_budget_template` WHERE `template_id` = 2289;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2289, 5, 655),
(2289, 32, 1250),
(2289, 45, 8095);

DELETE FROM `item_budget_template` WHERE `template_id` = 2290;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2290, 5, 710),
(2290, 32, 1243),
(2290, 45, 8047);

DELETE FROM `item_budget_template` WHERE `template_id` = 2291;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2291, 12, 6667),
(2291, 31, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 2292;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2292, 12, 6957),
(2292, 31, 3043);

DELETE FROM `item_budget_template` WHERE `template_id` = 2293;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2293, 12, 5294),
(2293, 37, 4706);

DELETE FROM `item_budget_template` WHERE `template_id` = 2294;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2294, 5, 811),
(2294, 45, 9189);

DELETE FROM `item_budget_template` WHERE `template_id` = 2295;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2295, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2296;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2296, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2297;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2297, 4, 7692),
(2297, 5, 2308);

DELETE FROM `item_budget_template` WHERE `template_id` = 2298;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2298, 5, 4051),
(2298, 32, 1620),
(2298, 45, 4329);

DELETE FROM `item_budget_template` WHERE `template_id` = 2299;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2299, 5, 3978),
(2299, 32, 1836),
(2299, 45, 4186);

DELETE FROM `item_budget_template` WHERE `template_id` = 2300;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2300, 5, 3368),
(2300, 6, 3032),
(2300, 45, 3600);

DELETE FROM `item_budget_template` WHERE `template_id` = 2301;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2301, 12, 3913),
(2301, 13, 6087);

DELETE FROM `item_budget_template` WHERE `template_id` = 2302;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2302, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2303;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2303, 5, 3456),
(2303, 6, 2514),
(2303, 45, 4030);

DELETE FROM `item_budget_template` WHERE `template_id` = 2304;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2304, 32, 4617),
(2304, 45, 5383);

DELETE FROM `item_budget_template` WHERE `template_id` = 2305;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2305, 4, 4225),
(2305, 12, 3240),
(2305, 32, 2535);

DELETE FROM `item_budget_template` WHERE `template_id` = 2306;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2306, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2307;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2307, 3, 3582),
(2307, 31, 2836),
(2307, 13, 3582);

DELETE FROM `item_budget_template` WHERE `template_id` = 2308;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2308, 5, 3383),
(2308, 31, 3242),
(2308, 45, 3375);

DELETE FROM `item_budget_template` WHERE `template_id` = 2309;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2309, 5, 4991),
(2309, 45, 5009);

DELETE FROM `item_budget_template` WHERE `template_id` = 2310;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2310, 5, 4259),
(2310, 32, 2350),
(2310, 45, 3391);

DELETE FROM `item_budget_template` WHERE `template_id` = 2311;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2311, 32, 2560),
(2311, 45, 7440);

DELETE FROM `item_budget_template` WHERE `template_id` = 2312;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2312, 6, 7229),
(2312, 45, 2771);

DELETE FROM `item_budget_template` WHERE `template_id` = 2313;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2313, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2314;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2314, 32, 788),
(2314, 5, 2364),
(2314, 45, 6848);

DELETE FROM `item_budget_template` WHERE `template_id` = 2315;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2315, 5, 4800),
(2315, 4, 5200);

DELETE FROM `item_budget_template` WHERE `template_id` = 2316;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2316, 5, 2638),
(2316, 32, 4104),
(2316, 45, 3258);

DELETE FROM `item_budget_template` WHERE `template_id` = 2317;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2317, 5, 3674),
(2317, 4, 3469),
(2317, 32, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 2318;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2318, 5, 3472),
(2318, 45, 3668),
(2318, 32, 2860);

DELETE FROM `item_budget_template` WHERE `template_id` = 2319;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2319, 5, 3721),
(2319, 4, 1395),
(2319, 32, 4884);

DELETE FROM `item_budget_template` WHERE `template_id` = 2320;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2320, 5, 2391),
(2320, 4, 1196),
(2320, 45, 3066),
(2320, 32, 3347);

DELETE FROM `item_budget_template` WHERE `template_id` = 2321;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2321, 4, 4615),
(2321, 32, 5385);

DELETE FROM `item_budget_template` WHERE `template_id` = 2322;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2322, 4, 3259),
(2322, 5, 3258),
(2322, 45, 3483);

DELETE FROM `item_budget_template` WHERE `template_id` = 2323;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2323, 4, 3375),
(2323, 5, 2382),
(2323, 45, 4243);

DELETE FROM `item_budget_template` WHERE `template_id` = 2324;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2324, 4, 3504),
(2324, 5, 2336),
(2324, 45, 4160);

DELETE FROM `item_budget_template` WHERE `template_id` = 2325;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2325, 4, 3446),
(2325, 5, 2298),
(2325, 45, 4256);

DELETE FROM `item_budget_template` WHERE `template_id` = 2326;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2326, 4, 3581),
(2326, 5, 2046),
(2326, 45, 4373);

DELETE FROM `item_budget_template` WHERE `template_id` = 2327;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2327, 5, 4985),
(2327, 45, 5015);

DELETE FROM `item_budget_template` WHERE `template_id` = 2328;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2328, 5, 3542),
(2328, 4, 3542),
(2328, 32, 2916);

DELETE FROM `item_budget_template` WHERE `template_id` = 2329;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2329, 5, 3105),
(2329, 45, 3116),
(2329, 32, 3779);

DELETE FROM `item_budget_template` WHERE `template_id` = 2330;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2330, 5, 3466),
(2330, 4, 1560),
(2330, 32, 3640),
(2330, 45, 1334);

DELETE FROM `item_budget_template` WHERE `template_id` = 2331;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2331, 5, 3237),
(2331, 4, 1874),
(2331, 32, 3578),
(2331, 45, 1311);

DELETE FROM `item_budget_template` WHERE `template_id` = 2332;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2332, 5, 3121),
(2332, 4, 2947),
(2332, 3, 1560),
(2332, 45, 2372);

DELETE FROM `item_budget_template` WHERE `template_id` = 2333;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2333, 4, 3305),
(2333, 5, 3305),
(2333, 45, 3390);

DELETE FROM `item_budget_template` WHERE `template_id` = 2334;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2334, 4, 3750),
(2334, 5, 3333),
(2334, 32, 2917);

DELETE FROM `item_budget_template` WHERE `template_id` = 2335;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2335, 4, 2699),
(2335, 5, 2295),
(2335, 45, 3116),
(2335, 32, 1890);

DELETE FROM `item_budget_template` WHERE `template_id` = 2336;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2336, 4, 2749),
(2336, 5, 2619),
(2336, 32, 1833),
(2336, 45, 2799);

DELETE FROM `item_budget_template` WHERE `template_id` = 2337;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2337, 4, 2749),
(2337, 5, 2619),
(2337, 32, 1833),
(2337, 45, 2799);

DELETE FROM `item_budget_template` WHERE `template_id` = 2338;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2338, 4, 3387),
(2338, 5, 3175),
(2338, 45, 3438);

DELETE FROM `item_budget_template` WHERE `template_id` = 2339;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2339, 3, 6383),
(2339, 31, 3617);

DELETE FROM `item_budget_template` WHERE `template_id` = 2340;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2340, 5, 2963),
(2340, 6, 2190),
(2340, 45, 4847);

DELETE FROM `item_budget_template` WHERE `template_id` = 2341;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2341, 32, 5952),
(2341, 5, 4048);

DELETE FROM `item_budget_template` WHERE `template_id` = 2342;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2342, 4, 5769),
(2342, 3, 2116),
(2342, 12, 2115);

DELETE FROM `item_budget_template` WHERE `template_id` = 2343;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2343, 3, 6944),
(2343, 5, 3056);

DELETE FROM `item_budget_template` WHERE `template_id` = 2344;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2344, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2345;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2345, 4, 5333),
(2345, 3, 4667);

DELETE FROM `item_budget_template` WHERE `template_id` = 2346;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2346, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2347;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2347, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2348;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2348, 4, 2456),
(2348, 5, 3860),
(2348, 32, 3684);

DELETE FROM `item_budget_template` WHERE `template_id` = 2349;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2349, 4, 3164),
(2349, 32, 2109),
(2349, 31, 1507),
(2349, 45, 3220);

DELETE FROM `item_budget_template` WHERE `template_id` = 2350;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2350, 4, 5068),
(2350, 31, 4932);

DELETE FROM `item_budget_template` WHERE `template_id` = 2351;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2351, 5, 958),
(2351, 32, 899),
(2351, 45, 8143);

DELETE FROM `item_budget_template` WHERE `template_id` = 2352;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2352, 3, 5556),
(2352, 37, 4444);

DELETE FROM `item_budget_template` WHERE `template_id` = 2353;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2353, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2354;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2354, 4, 5349),
(2354, 3, 4651);

DELETE FROM `item_budget_template` WHERE `template_id` = 2355;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2355, 4, 2831),
(2355, 5, 2585),
(2355, 32, 1847),
(2355, 45, 2737);

DELETE FROM `item_budget_template` WHERE `template_id` = 2356;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2356, 3, 7179),
(2356, 31, 2821);

DELETE FROM `item_budget_template` WHERE `template_id` = 2357;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2357, 5, 3447),
(2357, 32, 2010),
(2357, 45, 4543);

DELETE FROM `item_budget_template` WHERE `template_id` = 2358;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2358, 4, 3919),
(2358, 32, 6081);

DELETE FROM `item_budget_template` WHERE `template_id` = 2359;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2359, 4, 6441),
(2359, 14, 3559);

DELETE FROM `item_budget_template` WHERE `template_id` = 2360;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2360, 4, 5952),
(2360, 5, 4048);

DELETE FROM `item_budget_template` WHERE `template_id` = 2361;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2361, 5, 3619),
(2361, 45, 6381);

DELETE FROM `item_budget_template` WHERE `template_id` = 2362;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2362, 32, 6154),
(2362, 31, 3846);

DELETE FROM `item_budget_template` WHERE `template_id` = 2363;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2363, 5, 2596),
(2363, 31, 2360),
(2363, 45, 5044);

DELETE FROM `item_budget_template` WHERE `template_id` = 2364;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2364, 32, 2051),
(2364, 45, 7949);

DELETE FROM `item_budget_template` WHERE `template_id` = 2365;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2365, 4, 5676),
(2365, 32, 4324);

DELETE FROM `item_budget_template` WHERE `template_id` = 2366;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2366, 4, 2889),
(2366, 3, 2778),
(2366, 5, 1556),
(2366, 6, 1222),
(2366, 31, 1555);

DELETE FROM `item_budget_template` WHERE `template_id` = 2367;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2367, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2368;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2368, 3, 4894),
(2368, 13, 2766),
(2368, 31, 2340);

DELETE FROM `item_budget_template` WHERE `template_id` = 2369;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2369, 5, 2194),
(2369, 32, 3218),
(2369, 31, 1462),
(2369, 45, 3126);

DELETE FROM `item_budget_template` WHERE `template_id` = 2370;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2370, 5, 2744),
(2370, 6, 4358),
(2370, 45, 2898);

DELETE FROM `item_budget_template` WHERE `template_id` = 2371;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2371, 4, 6250),
(2371, 32, 3750);

DELETE FROM `item_budget_template` WHERE `template_id` = 2372;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2372, 4, 6364),
(2372, 5, 3636);

DELETE FROM `item_budget_template` WHERE `template_id` = 2373;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2373, 4, 5333),
(2373, 37, 4667);

DELETE FROM `item_budget_template` WHERE `template_id` = 2374;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2374, 4, 6000),
(2374, 5, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2375;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2375, 32, 5991),
(2375, 45, 4009);

DELETE FROM `item_budget_template` WHERE `template_id` = 2376;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2376, 4, 5082),
(2376, 3, 2951),
(2376, 31, 1967);

DELETE FROM `item_budget_template` WHERE `template_id` = 2377;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2377, 5, 5476),
(2377, 32, 4524);

DELETE FROM `item_budget_template` WHERE `template_id` = 2378;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2378, 4, 3433),
(2378, 3, 3134),
(2378, 5, 1791),
(2378, 6, 1642);

DELETE FROM `item_budget_template` WHERE `template_id` = 2379;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2379, 5, 5802),
(2379, 45, 4198);

DELETE FROM `item_budget_template` WHERE `template_id` = 2380;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2380, 12, 4706),
(2380, 15, 5294);

DELETE FROM `item_budget_template` WHERE `template_id` = 2381;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2381, 5, 3535),
(2381, 32, 2893),
(2381, 45, 3572);

DELETE FROM `item_budget_template` WHERE `template_id` = 2382;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2382, 4, 4000),
(2382, 3, 3500),
(2382, 5, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 2383;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2383, 12, 5918),
(2383, 32, 4082);

DELETE FROM `item_budget_template` WHERE `template_id` = 2384;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2384, 32, 4617),
(2384, 45, 5383);

DELETE FROM `item_budget_template` WHERE `template_id` = 2385;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2385, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2386;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2386, 4, 5500),
(2386, 32, 4500);

DELETE FROM `item_budget_template` WHERE `template_id` = 2387;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2387, 4, 4049),
(2387, 5, 2640),
(2387, 45, 3311);

DELETE FROM `item_budget_template` WHERE `template_id` = 2388;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2388, 4, 5246),
(2388, 5, 4754);

DELETE FROM `item_budget_template` WHERE `template_id` = 2389;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2389, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2390;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2390, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2391;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2391, 5, 3090),
(2391, 45, 6910);

DELETE FROM `item_budget_template` WHERE `template_id` = 2392;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2392, 32, 4822),
(2392, 45, 5178);

DELETE FROM `item_budget_template` WHERE `template_id` = 2393;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2393, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2394;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2394, 38, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2395;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2395, 5, 2928),
(2395, 6, 3533),
(2395, 45, 3539);

DELETE FROM `item_budget_template` WHERE `template_id` = 2396;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2396, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2397;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2397, 5, 3608),
(2397, 6, 2658),
(2397, 45, 3734);

DELETE FROM `item_budget_template` WHERE `template_id` = 2398;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2398, 5, 2703),
(2398, 6, 2510),
(2398, 45, 4787);

DELETE FROM `item_budget_template` WHERE `template_id` = 2399;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2399, 5, 2849),
(2399, 32, 2848),
(2399, 45, 4303);

DELETE FROM `item_budget_template` WHERE `template_id` = 2400;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2400, 5, 994),
(2400, 45, 9006);

DELETE FROM `item_budget_template` WHERE `template_id` = 2401;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2401, 5, 2525),
(2401, 6, 2121),
(2401, 45, 5354);

DELETE FROM `item_budget_template` WHERE `template_id` = 2402;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2402, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2403;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2403, 5, 2252),
(2403, 32, 2101),
(2403, 45, 5647);

DELETE FROM `item_budget_template` WHERE `template_id` = 2404;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2404, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2405;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2405, 5, 2851),
(2405, 45, 7149);

DELETE FROM `item_budget_template` WHERE `template_id` = 2406;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2406, 3, 3559),
(2406, 4, 6441);

DELETE FROM `item_budget_template` WHERE `template_id` = 2407;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2407, 5, 4801),
(2407, 45, 5199);

DELETE FROM `item_budget_template` WHERE `template_id` = 2408;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2408, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2409;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2409, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2410;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2410, 32, 3541),
(2410, 5, 1678),
(2410, 45, 4781);

DELETE FROM `item_budget_template` WHERE `template_id` = 2411;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2411, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2412;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2412, 4, 5128),
(2412, 3, 4872);

DELETE FROM `item_budget_template` WHERE `template_id` = 2413;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2413, 32, 5128),
(2413, 31, 4872);

DELETE FROM `item_budget_template` WHERE `template_id` = 2414;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2414, 5, 3409),
(2414, 6, 3239),
(2414, 45, 3352);

DELETE FROM `item_budget_template` WHERE `template_id` = 2415;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2415, 32, 5042),
(2415, 45, 4958);

DELETE FROM `item_budget_template` WHERE `template_id` = 2416;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2416, 5, 5042),
(2416, 45, 4958);

DELETE FROM `item_budget_template` WHERE `template_id` = 2417;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2417, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2418;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2418, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2419;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2419, 31, 4783),
(2419, 3, 5217);

DELETE FROM `item_budget_template` WHERE `template_id` = 2420;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2420, 6, 3852),
(2420, 45, 6148);

DELETE FROM `item_budget_template` WHERE `template_id` = 2421;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2421, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2422;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2422, 31, 4762),
(2422, 3, 5238);

DELETE FROM `item_budget_template` WHERE `template_id` = 2423;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2423, 4, 4889),
(2423, 31, 5111);

DELETE FROM `item_budget_template` WHERE `template_id` = 2424;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2424, 4, 7143),
(2424, 31, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 2425;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2425, 4, 5116),
(2425, 32, 4884);

DELETE FROM `item_budget_template` WHERE `template_id` = 2426;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2426, 4, 5745),
(2426, 32, 4255);

DELETE FROM `item_budget_template` WHERE `template_id` = 2427;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2427, 4, 6957),
(2427, 31, 3043);

DELETE FROM `item_budget_template` WHERE `template_id` = 2428;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2428, 4, 6970),
(2428, 31, 3030);

DELETE FROM `item_budget_template` WHERE `template_id` = 2429;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2429, 4, 5172),
(2429, 32, 4828);

DELETE FROM `item_budget_template` WHERE `template_id` = 2430;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2430, 4, 6591),
(2430, 14, 3409);

DELETE FROM `item_budget_template` WHERE `template_id` = 2431;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2431, 4, 5000),
(2431, 32, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2432;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2432, 4, 5313),
(2432, 3, 4687);

DELETE FROM `item_budget_template` WHERE `template_id` = 2433;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2433, 4, 7188),
(2433, 31, 2812);

DELETE FROM `item_budget_template` WHERE `template_id` = 2434;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2434, 4, 6522),
(2434, 3, 3478);

DELETE FROM `item_budget_template` WHERE `template_id` = 2435;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2435, 4, 5714),
(2435, 32, 4286);

DELETE FROM `item_budget_template` WHERE `template_id` = 2436;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2436, 4, 5000),
(2436, 32, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2437;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2437, 4, 7500),
(2437, 31, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 2438;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2438, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2439;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2439, 4, 5172),
(2439, 32, 4828);

DELETE FROM `item_budget_template` WHERE `template_id` = 2440;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2440, 4, 5172),
(2440, 32, 4828);

DELETE FROM `item_budget_template` WHERE `template_id` = 2441;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2441, 4, 7143),
(2441, 31, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 2442;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2442, 6, 1326),
(2442, 32, 2062),
(2442, 45, 6612);

DELETE FROM `item_budget_template` WHERE `template_id` = 2443;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2443, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 2444;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2444, 31, 6111),
(2444, 32, 3889);

DELETE FROM `item_budget_template_name` WHERE `template_id` IN (
  86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100,
  101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115,
  116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130,
  131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145,
  146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160,
  161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175,
  176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190,
  191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205,
  206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220,
  221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235,
  236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250,
  251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265,
  266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280,
  281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295,
  296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310,
  311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325,
  326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340,
  341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355,
  356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370,
  371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385,
  386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400,
  401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415,
  416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430,
  431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445,
  446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460,
  461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475,
  476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490,
  491, 492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505,
  506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516, 517, 518, 519, 520,
  521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534, 535,
  536, 537, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550,
  551, 552, 553, 554, 555, 556, 557, 558, 559, 560, 561, 562, 563, 564, 565,
  566, 567, 568, 569, 570, 571, 572, 573, 574, 575, 576, 577, 578, 579, 580,
  581, 582, 583, 584, 585, 586, 587, 588, 589, 590, 591, 592, 593, 594, 595,
  596, 597, 598, 599, 600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610,
  611, 612, 613, 614, 615, 616, 617, 618, 619, 620, 621, 622, 623, 624, 625,
  626, 627, 628, 629, 630, 631, 632, 633, 634, 635, 636, 637, 638, 639, 640,
  641, 642, 643, 644, 645, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655,
  656, 657, 658, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670,
  671, 672, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684, 685,
  686, 687, 688, 689, 690, 691, 692, 693, 694, 695, 696, 697, 698, 699, 700,
  701, 702, 703, 704, 705, 706, 707, 708, 709, 710, 711, 712, 713, 714, 715,
  716, 717, 718, 719, 720, 721, 722, 723, 724, 725, 726, 727, 728, 729, 730,
  731, 732, 733, 734, 735, 736, 737, 738, 739, 740, 741, 742, 743, 744, 745,
  746, 747, 748, 749, 750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 760,
  761, 762, 763, 764, 765, 766, 767, 768, 769, 770, 771, 772, 773, 774, 775,
  776, 777, 778, 779, 780, 781, 782, 783, 784, 785, 786, 787, 788, 789, 790,
  791, 792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804, 805,
  806, 807, 808, 809, 810, 811, 812, 813, 814, 815, 816, 817, 818, 819, 820,
  821, 822, 823, 824, 825, 826, 827, 828, 829, 830, 831, 832, 833, 834, 835,
  836, 837, 838, 839, 840, 841, 842, 843, 844, 845, 846, 847, 848, 849, 850,
  851, 852, 853, 854, 855, 856, 857, 858, 859, 860, 861, 862, 863, 864, 865,
  866, 867, 868, 869, 870, 871, 872, 873, 874, 875, 876, 877, 878, 879, 880,
  881, 882, 883, 884, 885, 886, 887, 888, 889, 890, 891, 892, 893, 894, 895,
  896, 897, 898, 899, 900, 901, 902, 903, 904, 905, 906, 907, 908, 909, 910,
  911, 912, 913, 914, 915, 916, 917, 918, 919, 920, 921, 922, 923, 924, 925,
  926, 927, 928, 929, 930, 931, 932, 933, 934, 935, 936, 937, 938, 939, 940,
  941, 942, 943, 944, 945, 946, 947, 948, 949, 950, 951, 952, 953, 954, 955,
  956, 957, 958, 959, 960, 961, 962, 963, 964, 965, 966, 967, 968, 969, 970,
  971, 972, 973, 974, 975, 976, 977, 978, 979, 980, 981, 982, 983, 984, 985,
  986, 987, 988, 989, 990, 991, 992, 993, 994, 995, 996, 997, 998, 999, 1000,
  1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014, 1015,
  1016, 1017, 1018, 1019, 1020, 1021, 1022, 1023, 1024, 1025, 1026, 1027, 1028, 1029, 1030,
  1031, 1032, 1033, 1034, 1035, 1036, 1037, 1038, 1039, 1040, 1041, 1042, 1043, 1044, 1045,
  1046, 1047, 1048, 1049, 1050, 1051, 1052, 1053, 1054, 1055, 1056, 1057, 1058, 1059, 1060,
  1061, 1062, 1063, 1064, 1065, 1066, 1067, 1068, 1069, 1070, 1071, 1072, 1073, 1074, 1075,
  1076, 1077, 1078, 1079, 1080, 1081, 1082, 1083, 1084, 1085, 1086, 1087, 1088, 1089, 1090,
  1091, 1092, 1093, 1094, 1095, 1096, 1097, 1098, 1099, 1100, 1101, 1102, 1103, 1104, 1105,
  1106, 1107, 1108, 1109, 1110, 1111, 1112, 1113, 1114, 1115, 1116, 1117, 1118, 1119, 1120,
  1121, 1122, 1123, 1124, 1125, 1126, 1127, 1128, 1129, 1130, 1131, 1132, 1133, 1134, 1135,
  1136, 1137, 1138, 1139, 1140, 1141, 1142, 1143, 1144, 1145, 1146, 1147, 1148, 1149, 1150,
  1151, 1152, 1153, 1154, 1155, 1156, 1157, 1158, 1159, 1160, 1161, 1162, 1163, 1164, 1165,
  1166, 1167, 1168, 1169, 1170, 1171, 1172, 1173, 1174, 1175, 1176, 1177, 1178, 1179, 1180,
  1181, 1182, 1183, 1184, 1185, 1186, 1187, 1188, 1189, 1190, 1191, 1192, 1193, 1194, 1195,
  1196, 1197, 1198, 1199, 1200, 1201, 1202, 1203, 1204, 1205, 1206, 1207, 1208, 1209, 1210,
  1211, 1212, 1213, 1214, 1215, 1216, 1217, 1218, 1219, 1220, 1221, 1222, 1223, 1224, 1225,
  1226, 1227, 1228, 1229, 1230, 1231, 1232, 1233, 1234, 1235, 1236, 1237, 1238, 1239, 1240,
  1241, 1242, 1243, 1244, 1245, 1246, 1247, 1248, 1249, 1250, 1251, 1252, 1253, 1254, 1255,
  1256, 1257, 1258, 1259, 1260, 1261, 1262, 1263, 1264, 1265, 1266, 1267, 1268, 1269, 1270,
  1271, 1272, 1273, 1274, 1275, 1276, 1277, 1278, 1279, 1280, 1281, 1282, 1283, 1284, 1285,
  1286, 1287, 1288, 1289, 1290, 1291, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300,
  1301, 1302, 1303, 1304, 1305, 1306, 1307, 1308, 1309, 1310, 1311, 1312, 1313, 1314, 1315,
  1316, 1317, 1318, 1319, 1320, 1321, 1322, 1323, 1324, 1325, 1326, 1327, 1328, 1329, 1330,
  1331, 1332, 1333, 1334, 1335, 1336, 1337, 1338, 1339, 1340, 1341, 1342, 1343, 1344, 1345,
  1346, 1347, 1348, 1349, 1350, 1351, 1352, 1353, 1354, 1355, 1356, 1357, 1358, 1359, 1360,
  1361, 1362, 1363, 1364, 1365, 1366, 1367, 1368, 1369, 1370, 1371, 1372, 1373, 1374, 1375,
  1376, 1377, 1378, 1379, 1380, 1381, 1382, 1383, 1384, 1385, 1386, 1387, 1388, 1389, 1390,
  1391, 1392, 1393, 1394, 1395, 1396, 1397, 1398, 1399, 1400, 1401, 1402, 1403, 1404, 1405,
  1406, 1407, 1408, 1409, 1410, 1411, 1412, 1413, 1414, 1415, 1416, 1417, 1418, 1419, 1420,
  1421, 1422, 1423, 1424, 1425, 1426, 1427, 1428, 1429, 1430, 1431, 1432, 1433, 1434, 1435,
  1436, 1437, 1438, 1439, 1440, 1441, 1442, 1443, 1444, 1445, 1446, 1447, 1448, 1449, 1450,
  1451, 1452, 1453, 1454, 1455, 1456, 1457, 1458, 1459, 1460, 1461, 1462, 1463, 1464, 1465,
  1466, 1467, 1468, 1469, 1470, 1471, 1472, 1473, 1474, 1475, 1476, 1477, 1478, 1479, 1480,
  1481, 1482, 1483, 1484, 1485, 1486, 1487, 1488, 1489, 1490, 1491, 1492, 1493, 1494, 1495,
  1496, 1497, 1498, 1499, 1500, 1501, 1502, 1503, 1504, 1505, 1506, 1507, 1508, 1509, 1510,
  1511, 1512, 1513, 1514, 1515, 1516, 1517, 1518, 1519, 1520, 1521, 1522, 1523, 1524, 1525,
  1526, 1527, 1528, 1529, 1530, 1531, 1532, 1533, 1534, 1535, 1536, 1537, 1538, 1539, 1540,
  1541, 1542, 1543, 1544, 1545, 1546, 1547, 1548, 1549, 1550, 1551, 1552, 1553, 1554, 1555,
  1556, 1557, 1558, 1559, 1560, 1561, 1562, 1563, 1564, 1565, 1566, 1567, 1568, 1569, 1570,
  1571, 1572, 1573, 1574, 1575, 1576, 1577, 1578, 1579, 1580, 1581, 1582, 1583, 1584, 1585,
  1586, 1587, 1588, 1589, 1590, 1591, 1592, 1593, 1594, 1595, 1596, 1597, 1598, 1599, 1600,
  1601, 1602, 1603, 1604, 1605, 1606, 1607, 1608, 1609, 1610, 1611, 1612, 1613, 1614, 1615,
  1616, 1617, 1618, 1619, 1620, 1621, 1622, 1623, 1624, 1625, 1626, 1627, 1628, 1629, 1630,
  1631, 1632, 1633, 1634, 1635, 1636, 1637, 1638, 1639, 1640, 1641, 1642, 1643, 1644, 1645,
  1646, 1647, 1648, 1649, 1650, 1651, 1652, 1653, 1654, 1655, 1656, 1657, 1658, 1659, 1660,
  1661, 1662, 1663, 1664, 1665, 1666, 1667, 1668, 1669, 1670, 1671, 1672, 1673, 1674, 1675,
  1676, 1677, 1678, 1679, 1680, 1681, 1682, 1683, 1684, 1685, 1686, 1687, 1688, 1689, 1690,
  1691, 1692, 1693, 1694, 1695, 1696, 1697, 1698, 1699, 1700, 1701, 1702, 1703, 1704, 1705,
  1706, 1707, 1708, 1709, 1710, 1711, 1712, 1713, 1714, 1715, 1716, 1717, 1718, 1719, 1720,
  1721, 1722, 1723, 1724, 1725, 1726, 1727, 1728, 1729, 1730, 1731, 1732, 1733, 1734, 1735,
  1736, 1737, 1738, 1739, 1740, 1741, 1742, 1743, 1744, 1745, 1746, 1747, 1748, 1749, 1750,
  1751, 1752, 1753, 1754, 1755, 1756, 1757, 1758, 1759, 1760, 1761, 1762, 1763, 1764, 1765,
  1766, 1767, 1768, 1769, 1770, 1771, 1772, 1773, 1774, 1775, 1776, 1777, 1778, 1779, 1780,
  1781, 1782, 1783, 1784, 1785, 1786, 1787, 1788, 1789, 1790, 1791, 1792, 1793, 1794, 1795,
  1796, 1797, 1798, 1799, 1800, 1801, 1802, 1803, 1804, 1805, 1806, 1807, 1808, 1809, 1810,
  1811, 1812, 1813, 1814, 1815, 1816, 1817, 1818, 1819, 1820, 1821, 1822, 1823, 1824, 1825,
  1826, 1827, 1828, 1829, 1830, 1831, 1832, 1833, 1834, 1835, 1836, 1837, 1838, 1839, 1840,
  1841, 1842, 1843, 1844, 1845, 1846, 1847, 1848, 1849, 1850, 1851, 1852, 1853, 1854, 1855,
  1856, 1857, 1858, 1859, 1860, 1861, 1862, 1863, 1864, 1865, 1866, 1867, 1868, 1869, 1870,
  1871, 1872, 1873, 1874, 1875, 1876, 1877, 1878, 1879, 1880, 1881, 1882, 1883, 1884, 1885,
  1886, 1887, 1888, 1889, 1890, 1891, 1892, 1893, 1894, 1895, 1896, 1897, 1898, 1899, 1900,
  1901, 1902, 1903, 1904, 1905, 1906, 1907, 1908, 1909, 1910, 1911, 1912, 1913, 1914, 1915,
  1916, 1917, 1918, 1919, 1920, 1921, 1922, 1923, 1924, 1925, 1926, 1927, 1928, 1929, 1930,
  1931, 1932, 1933, 1934, 1935, 1936, 1937, 1938, 1939, 1940, 1941, 1942, 1943, 1944, 1945,
  1946, 1947, 1948, 1949, 1950, 1951, 1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 1960,
  1961, 1962, 1963, 1964, 1965, 1966, 1967, 1968, 1969, 1970, 1971, 1972, 1973, 1974, 1975,
  1976, 1977, 1978, 1979, 1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990,
  1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005,
  2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020,
  2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035,
  2036, 2037, 2038, 2039, 2040, 2041, 2042, 2043, 2044, 2045, 2046, 2047, 2048, 2049, 2050,
  2051, 2052, 2053, 2054, 2055, 2056, 2057, 2058, 2059, 2060, 2061, 2062, 2063, 2064, 2065,
  2066, 2067, 2068, 2069, 2070, 2071, 2072, 2073, 2074, 2075, 2076, 2077, 2078, 2079, 2080,
  2081, 2082, 2083, 2084, 2085, 2086, 2087, 2088, 2089, 2090, 2091, 2092, 2093, 2094, 2095,
  2096, 2097, 2098, 2099, 2100, 2101, 2102, 2103, 2104, 2105, 2106, 2107, 2108, 2109, 2110,
  2111, 2112, 2113, 2114, 2115, 2116, 2117, 2118, 2119, 2120, 2121, 2122, 2123, 2124, 2125,
  2126, 2127, 2128, 2129, 2130, 2131, 2132, 2133, 2134, 2135, 2136, 2137, 2138, 2139, 2140,
  2141, 2142, 2143, 2144, 2145, 2146, 2147, 2148, 2149, 2150, 2151, 2152, 2153, 2154, 2155,
  2156, 2157, 2158, 2159, 2160, 2161, 2162, 2163, 2164, 2165, 2166, 2167, 2168, 2169, 2170,
  2171, 2172, 2173, 2174, 2175, 2176, 2177, 2178, 2179, 2180, 2181, 2182, 2183, 2184, 2185,
  2186, 2187, 2188, 2189, 2190, 2191, 2192, 2193, 2194, 2195, 2196, 2197, 2198, 2199, 2200,
  2201, 2202, 2203, 2204, 2205, 2206, 2207, 2208, 2209, 2210, 2211, 2212, 2213, 2214, 2215,
  2216, 2217, 2218, 2219, 2220, 2221, 2222, 2223, 2224, 2225, 2226, 2227, 2228, 2229, 2230,
  2231, 2232, 2233, 2234, 2235, 2236, 2237, 2238, 2239, 2240, 2241, 2242, 2243, 2244, 2245,
  2246, 2247, 2248, 2249, 2250, 2251, 2252, 2253, 2254, 2255, 2256, 2257, 2258, 2259, 2260,
  2261, 2262, 2263, 2264, 2265, 2266, 2267, 2268, 2269, 2270, 2271, 2272, 2273, 2274, 2275,
  2276, 2277, 2278, 2279, 2280, 2281, 2282, 2283, 2284, 2285, 2286, 2287, 2288, 2289, 2290,
  2291, 2292, 2293, 2294, 2295, 2296, 2297, 2298, 2299, 2300, 2301, 2302, 2303, 2304, 2305,
  2306, 2307, 2308, 2309, 2310, 2311, 2312, 2313, 2314, 2315, 2316, 2317, 2318, 2319, 2320,
  2321, 2322, 2323, 2324, 2325, 2326, 2327, 2328, 2329, 2330, 2331, 2332, 2333, 2334, 2335,
  2336, 2337, 2338, 2339, 2340, 2341, 2342, 2343, 2344, 2345, 2346, 2347, 2348, 2349, 2350,
  2351, 2352, 2353, 2354, 2355, 2356, 2357, 2358, 2359, 2360, 2361, 2362, 2363, 2364, 2365,
  2366, 2367, 2368, 2369, 2370, 2371, 2372, 2373, 2374, 2375, 2376, 2377, 2378, 2379, 2380,
  2381, 2382, 2383, 2384, 2385, 2386, 2387, 2388, 2389, 2390, 2391, 2392, 2393, 2394, 2395,
  2396, 2397, 2398, 2399, 2400, 2401, 2402, 2403, 2404, 2405, 2406, 2407, 2408, 2409, 2410,
  2411, 2412, 2413, 2414, 2415, 2416, 2417, 2418, 2419, 2420, 2421, 2422, 2423, 2424, 2425,
  2426, 2427, 2428, 2429, 2430, 2431, 2432, 2433, 2434, 2435, 2436, 2437, 2438, 2439, 2440,
  2441, 2442, 2443, 2444
);
INSERT INTO `item_budget_template_name` (`template_id`, `name`) VALUES
(86, 'Elemental Mage Staff shape'),
(87, 'Jeweled Amulet of Cainwyn shape'),
(88, 'Hand of Edward the Odd shape'),
(89, 'Blade of Hanna shape'),
(90, 'Scarlet Kris shape'),
(91, 'Earthborn Kilt shape'),
(92, 'Robes of the Royal Crown shape'),
(93, 'Thaurissan''s Royal Scepter shape'),
(94, 'The Emperor''s New Cape shape'),
(95, 'Star of Mystaria shape'),
(96, 'Seal of Ascension shape'),
(97, 'Songstone of Ironforge shape'),
(98, 'Thrall''s Resolve shape'),
(99, 'Eye of Orgrimmar shape'),
(100, 'Magni''s Will shape'),
(101, 'Grand Marshal''s Longsword shape'),
(102, 'Eye of Rend shape'),
(103, 'Dustfeather Sash shape'),
(104, 'Draconian Deflector shape'),
(105, 'Nightbrace Tunic shape'),
(106, 'Starfire Tiara shape'),
(107, 'Crystallized Girdle shape'),
(108, 'Enchanted Thorium Breastplate shape'),
(109, 'Enchanted Thorium Leggings shape'),
(110, 'Enchanted Thorium Helm shape'),
(111, 'Whitesoul Helm shape'),
(112, 'Chiselbrand Girdle shape'),
(113, 'Helm of the Great Chief shape'),
(114, 'Backusarian Gauntlets shape'),
(115, 'Stronghold Gauntlets shape'),
(116, 'Lionheart Helm shape'),
(117, 'Invulnerable Mail shape'),
(118, 'Cap of the Scarlet Savant shape'),
(119, 'Leggings of Arcana shape'),
(120, 'Breastplate of Bloodthirst shape'),
(121, 'Heartseeker shape'),
(122, 'Hammer of the Titans shape'),
(123, 'Breastplate of the Chromatic Flight shape'),
(124, 'Legguards of the Chromatic Defier shape'),
(125, 'Flaming Band shape'),
(126, 'Truestrike Shoulders shape'),
(127, 'Emberfury Talisman shape'),
(128, 'Warmaster Legguards shape'),
(129, 'Battleborn Armbraces shape'),
(130, 'Dal''Rend''s Tribal Guardian shape'),
(131, 'Dal''Rend''s Sacred Charge shape'),
(132, 'Legplates of the Chromatic Defier shape'),
(133, 'Gyth''s Skull shape'),
(134, 'Tribal War Feathers shape'),
(135, 'Blademaster Leggings shape'),
(136, 'Tristam Legguards shape'),
(137, 'Spiritshroud Leggings shape'),
(138, 'Blackmist Armguards shape'),
(139, 'Bloodmoon Cloak shape'),
(140, 'Frostweaver Cape shape'),
(141, 'Staff of Hale Magefire shape'),
(142, 'Maiden''s Circle shape'),
(143, 'Mass of McGowan shape'),
(144, 'Serathil shape'),
(145, 'Eaglehorn Long Bow shape'),
(146, 'Bludstone Hammer shape'),
(147, 'Stonegrip Gauntlets shape'),
(148, 'Direwing Legguards shape'),
(149, 'Widow''s Clutch shape'),
(150, 'Garrett Family Crest shape'),
(151, 'Breastplate of the Chosen shape'),
(152, 'Dragonstalker Tunic shape'),
(153, 'Band of the Hierophant shape'),
(154, 'Painweaver Band shape'),
(155, 'Magiskull Cuffs shape'),
(156, 'Feathermoon Headdress shape'),
(157, 'Spaulders of the Unseen shape'),
(158, 'Dreamwalker Armor shape'),
(159, 'Drakesfire Epaulets shape'),
(160, 'Tooth of Gnarr shape'),
(161, 'Brigam Girdle shape'),
(162, 'Trindlehaven Staff shape'),
(163, 'Reiver Claws shape'),
(164, 'Relentless Scythe shape'),
(165, 'Fist of Omokk shape'),
(166, 'Plate of the Shaman King shape'),
(167, 'Tressermane Leggings shape'),
(168, 'Skyshroud Leggings shape'),
(169, 'Talisman of Evasion shape'),
(170, 'Rosewine Circle shape'),
(171, 'Brazecore Armguards shape'),
(172, 'Fallbrush Handgrips shape'),
(173, 'Sunderseer Mantle shape'),
(174, 'Bashguuder shape'),
(175, 'Rhombeard Protector shape'),
(176, 'Wolfshear Leggings shape'),
(177, 'Bleak Howler Armguards shape'),
(178, 'Slashclaw Bracers shape'),
(179, 'Gilded Gauntlets shape'),
(180, 'Argent Crusader shape'),
(181, 'Cloudrunner Girdle shape'),
(182, 'Hands of Power shape'),
(183, 'Ribsteel Footguards shape'),
(184, 'Wind Dancer Boots shape'),
(185, 'Alanna''s Embrace shape'),
(186, 'Cape of the Black Baron shape'),
(187, 'Dracorian Gauntlets shape'),
(188, 'Seal of Rivendare shape'),
(189, 'Robes of the Exalted shape'),
(190, 'Scepter of the Unholy shape'),
(191, 'Book of the Dead shape'),
(192, 'Wyrmtongue Shoulders shape'),
(193, 'Gift of the Elven Magi shape'),
(194, 'Fire Striders shape'),
(195, 'Slavedriver''s Cane shape'),
(196, 'Band of Flesh shape'),
(197, 'Soulstealer Mantle shape'),
(198, 'Master Cannoneer Boots shape'),
(199, 'Tome of Knowledge shape'),
(200, 'The Postmaster''s Tunic shape'),
(201, 'The Postmaster''s Trousers shape'),
(202, 'The Postmaster''s Band shape'),
(203, 'The Postmaster''s Treads shape'),
(204, 'The Postmaster''s Seal shape'),
(205, 'Stoneskin Gargoyle Cape shape'),
(206, 'Boots of the Shrieker shape'),
(207, 'Handcrafted Mastersmith Leggings shape'),
(208, 'Handcrafted Mastersmith Girdle shape'),
(209, 'Dreadmaster''s Shroud shape'),
(210, 'Headmaster''s Charge shape'),
(211, 'Bonecreeper Stylus shape'),
(212, 'Tombstone Breastplate shape'),
(213, 'Detention Strap shape'),
(214, 'Vigorsteel Vambraces shape'),
(215, 'Verdant Footpads shape'),
(216, 'Stoneform Shoulders shape'),
(217, 'Clutch of Andros shape'),
(218, 'Gargoyle Slashers shape'),
(219, 'Wyrmthalak''s Shackles shape'),
(220, 'Omokk''s Girth Restrainer shape'),
(221, 'Heart of the Fiend shape'),
(222, 'Halycon''s Muzzle shape'),
(223, 'Vosh''gajin''s Strand shape'),
(224, 'Voone''s Vice Grips shape'),
(225, 'Witchblade shape'),
(226, 'Windreaver Greaves shape'),
(227, 'Loomguard Armbraces shape'),
(228, 'Crown of Caer Darrow shape'),
(229, 'Darrowshire Strongguard shape'),
(230, 'Mooncloth Vest shape'),
(231, 'Mooncloth Shoulders shape'),
(232, 'Mooncloth Circlet shape'),
(233, 'Gloves of Spell Mastery shape'),
(234, 'Robe of the Archmage shape'),
(235, 'Robe of the Void shape'),
(236, 'Truefaith Vestments shape'),
(237, 'Freezing Lich Robes shape'),
(238, 'Frostbite Girdle shape'),
(239, 'Death''s Clutch shape'),
(240, 'Maelstrom Leggings shape'),
(241, 'Boneclenched Gauntlets shape'),
(242, 'Rattlecage Buckler shape'),
(243, 'Bonebrace Hauberk shape'),
(244, 'Deadwalker Mantle shape'),
(245, 'Bone Ring Helm shape'),
(246, 'Darkshade Gloves shape'),
(247, 'Ghostloom Leggings shape'),
(248, 'Royal Cap Spaulders shape'),
(249, 'Sash of Mercy shape'),
(250, 'Cloudkeeper Legplates shape'),
(251, 'Lady Maye''s Pendant shape'),
(252, 'Skullsmoke Pants shape'),
(253, 'Bloodmail Hauberk shape'),
(254, 'Bloodmail Legguards shape'),
(255, 'Bloodmail Belt shape'),
(256, 'Bloodmail Gauntlets shape'),
(257, 'Bloodmail Boots shape'),
(258, 'Deathbone Girdle shape'),
(259, 'Deathbone Sabatons shape'),
(260, 'Deathbone Gauntlets shape'),
(261, 'Deathbone Legguards shape'),
(262, 'Deathbone Chestplate shape'),
(263, 'Necropile Robe shape'),
(264, 'Necropile Cuffs shape'),
(265, 'Necropile Boots shape'),
(266, 'Necropile Leggings shape'),
(267, 'Necropile Mantle shape'),
(268, 'Cadaverous Armor shape'),
(269, 'Red Dragonscale Breastplate shape'),
(270, 'Black Dragonscale Shoulders shape'),
(271, 'Black Dragonscale Leggings shape'),
(272, 'Living Breastplate shape'),
(273, 'Devilsaur Leggings shape'),
(274, 'Onyxia Scale Breastplate shape'),
(275, 'Mark of Fordring shape'),
(276, 'Ornate Adamantium Breastplate shape'),
(277, 'Shroud of the Exile shape'),
(278, 'Penelope''s Rose shape'),
(279, 'Mirah''s Song shape'),
(280, 'Dancing Sliver shape'),
(281, 'Archlight Talisman shape'),
(282, 'Flawless Arcanite Rifle shape'),
(283, 'Fordring''s Seal shape'),
(284, 'Senior Sergeant''s Insignia shape'),
(285, 'Sergeant Major''s Cape shape'),
(286, 'High Warlord''s Blade shape'),
(287, 'Knight-Captain''s Silk Sash shape'),
(288, 'Knight-Lieutenant''s Silk Boots shape'),
(289, 'Knight-Captain''s Silk Cuffs shape'),
(290, 'Knight-Lieutenant''s Silk Gloves shape'),
(291, 'Knight-Lieutenant''s Leather Boots shape'),
(292, 'Knight-Lieutenant''s Dragonhide Footwraps shape'),
(293, 'Knight-Captain''s Leather Bracers shape'),
(294, 'Knight-Captain''s Dragonhide Armsplints shape'),
(295, 'Knight-Lieutenant''s Leather Gauntlets shape'),
(296, 'Knight-Lieutenant''s Dragonhide Gloves shape'),
(297, 'Knight-Captain''s Leather Belt shape'),
(298, 'Knight-Captain''s Dragonhide Girdle shape'),
(299, 'Knight-Captain''s Chain Girdle shape'),
(300, 'Knight-Lieutenant''s Chain Boots shape'),
(301, 'Knight-Captain''s Chain Armguards shape'),
(302, 'Knight-Lieutenant''s Chain Gauntlets shape'),
(303, 'Knight-Captain''s Plate Wristguards shape'),
(304, 'Knight-Lieutenant''s Plate Boots shape'),
(305, 'Knight-Lieutenant''s Plate Gauntlets shape'),
(306, 'Knight-Captain''s Plate Girdle shape'),
(307, 'Knight-Lieutenant''s Lamellar Sabatons shape'),
(308, 'Knight-Lieutenant''s Lamellar Gauntlets shape'),
(309, 'Knight-Captain''s Lamellar Cinch shape'),
(310, 'Knight-Captain''s Lamellar Armsplints shape'),
(311, 'Knight-Captain''s Silk Raiment shape'),
(312, 'Knight-Captain''s Silk Leggings shape'),
(313, 'Lieutenant Commander''s Silk Spaulders shape'),
(314, 'Lieutenant Commander''s Crown shape'),
(315, 'Knight-Captain''s Leather Armor shape'),
(316, 'Lieutenant Commander''s Leather Veil shape'),
(317, 'Knight-Captain''s Leather Legguards shape'),
(318, 'Lieutenant Commander''s Leather Spaulders shape'),
(319, 'Knight-Captain''s Dragonhide Tunic shape'),
(320, 'Knight-Captain''s Dragonhide Leggings shape'),
(321, 'Lieutenant Commander''s Dragonhide Epaulets shape'),
(322, 'Lieutenant Commander''s Dragonhide Shroud shape'),
(323, 'Knight-Captain''s Chain Hauberk shape'),
(324, 'Knight-Captain''s Chain Leggings shape'),
(325, 'Lieutenant Commander''s Chain Pauldrons shape'),
(326, 'Lieutenant Commander''s Chain Helmet shape'),
(327, 'Lieutenant Commander''s Plate Helm shape'),
(328, 'Knight-Captain''s Plate Chestguard shape'),
(329, 'Knight-Captain''s Plate Leggings shape'),
(330, 'Lieutenant Commander''s Plate Pauldrons shape'),
(331, 'Knight-Captain''s Lamellar Breastplate shape'),
(332, 'Lieutenant Commander''s Lamellar Headguard shape'),
(333, 'Knight-Captain''s Lamellar Leggings shape'),
(334, 'Lieutenant Commander''s Lamellar Shoulders shape'),
(335, 'Marshal''s Silk Footwraps shape'),
(336, 'Marshal''s Silk Bracers shape'),
(337, 'Marshal''s Silk Sash shape'),
(338, 'Marshal''s Silk Gloves shape'),
(339, 'Field Marshal''s Coronet shape'),
(340, 'Marshal''s Silk Leggings shape'),
(341, 'Field Marshal''s Silk Vestments shape'),
(342, 'Field Marshal''s Silk Spaulders shape'),
(343, 'Marshal''s Dragonhide Bracers shape'),
(344, 'Marshal''s Leather Footguards shape'),
(345, 'Marshal''s Dragonhide Waistguard shape'),
(346, 'Marshal''s Dragonhide Gauntlets shape'),
(347, 'Field Marshal''s Dragonhide Spaulders shape'),
(348, 'Marshal''s Dragonhide Legguards shape'),
(349, 'Field Marshal''s Dragonhide Helmet shape'),
(350, 'Field Marshal''s Dragonhide Breastplate shape'),
(351, 'Field Marshal''s Leather Chestpiece shape'),
(352, 'Marshal''s Leather Handgrips shape'),
(353, 'Field Marshal''s Leather Mask shape'),
(354, 'Marshal''s Leather Leggings shape'),
(355, 'Field Marshal''s Leather Epaulets shape'),
(356, 'Marshal''s Leather Cinch shape'),
(357, 'Marshal''s Dragonhide Boots shape'),
(358, 'Marshal''s Leather Armsplints shape'),
(359, 'Marshal''s Chain Bracers shape'),
(360, 'Marshal''s Chain Boots shape'),
(361, 'Marshal''s Chain Grips shape'),
(362, 'Marshal''s Chain Girdle shape'),
(363, 'Field Marshal''s Chain Helm shape'),
(364, 'Field Marshal''s Chain Breastplate shape'),
(365, 'Marshal''s Chain Legguards shape'),
(366, 'Field Marshal''s Chain Spaulders shape'),
(367, 'Marshal''s Lamellar Armguards shape'),
(368, 'Marshal''s Lamellar Belt shape'),
(369, 'Marshal''s Lamellar Gloves shape'),
(370, 'Marshal''s Lamellar Boots shape'),
(371, 'Field Marshal''s Lamellar Chestplate shape'),
(372, 'Field Marshal''s Lamellar Faceguard shape'),
(373, 'Marshal''s Lamellar Legplates shape'),
(374, 'Field Marshal''s Lamellar Pauldrons shape'),
(375, 'Field Marshal''s Plate Armor shape'),
(376, 'Field Marshal''s Plate Helm shape'),
(377, 'Marshal''s Plate Legguards shape'),
(378, 'Field Marshal''s Plate Shoulderguards shape'),
(379, 'Marshal''s Plate Bracers shape'),
(380, 'Marshal''s Plate Girdle shape'),
(381, 'Marshal''s Plate Boots shape'),
(382, 'Marshal''s Plate Gauntlets shape'),
(383, 'Blood Guard''s Silk Footwraps shape'),
(384, 'First Sergeant''s Silk Cuffs shape'),
(385, 'Blood Guard''s Silk Gloves shape'),
(386, 'Legionnaire''s Silk Belt shape'),
(387, 'Champion''s Silk Hood shape'),
(388, 'Legionnaire''s Silk Pants shape'),
(389, 'Legionnaire''s Silk Robes shape'),
(390, 'Champion''s Silk Shoulderpads shape'),
(391, 'Legionnaire''s Dragonhide Armguards shape'),
(392, 'Blood Guard''s Dragonhide Boots shape'),
(393, 'Legionnaire''s Dragonhide Waistband shape'),
(394, 'Blood Guard''s Dragonhide Gauntlets shape'),
(395, 'First Sergeant''s Leather Armguards shape'),
(396, 'Blood Guard''s Leather Treads shape'),
(397, 'Blood Guard''s Leather Vices shape'),
(398, 'Legionnaire''s Leather Girdle shape'),
(399, 'Champion''s Dragonhide Spaulders shape'),
(400, 'Legionnaire''s Dragonhide Trousers shape'),
(401, 'Champion''s Dragonhide Helm shape'),
(402, 'Legionnaire''s Dragonhide Breastplate shape'),
(403, 'Legionnaire''s Leather Hauberk shape'),
(404, 'Champion''s Leather Headguard shape'),
(405, 'Champion''s Leather Mantle shape'),
(406, 'Legionnaire''s Leather Leggings shape'),
(407, 'Blood Guard''s Plate Boots shape'),
(408, 'Blood Guard''s Plate Gloves shape'),
(409, 'Legionnaire''s Plate Cinch shape'),
(410, 'Legionnaire''s Plate Bracers shape'),
(411, 'Legionnaire''s Plate Armor shape'),
(412, 'Champion''s Plate Headguard shape'),
(413, 'Legionnaire''s Plate Legguards shape'),
(414, 'Champion''s Plate Pauldrons shape'),
(415, 'Legionnaire''s Chain Bracers shape'),
(416, 'Blood Guard''s Mail Walkers shape'),
(417, 'Blood Guard''s Mail Grips shape'),
(418, 'Legionnaire''s Mail Cinch shape'),
(419, 'Champion''s Mail Helm shape'),
(420, 'Legionnaire''s Mail Chestpiece shape'),
(421, 'Legionnaire''s Mail Leggings shape'),
(422, 'Champion''s Mail Shoulders shape'),
(423, 'Legionnaire''s Chain Breastplate shape'),
(424, 'Champion''s Chain Headguard shape'),
(425, 'Legionnaire''s Chain Leggings shape'),
(426, 'Champion''s Chain Pauldrons shape'),
(427, 'Legionnaire''s Chain Girdle shape'),
(428, 'Blood Guard''s Chain Gauntlets shape'),
(429, 'Blood Guard''s Chain Boots shape'),
(430, 'First Sergeant''s Mail Wristguards shape'),
(431, 'Warlord''s Silk Cowl shape'),
(432, 'General''s Silk Trousers shape'),
(433, 'Warlord''s Silk Raiment shape'),
(434, 'Warlord''s Silk Amice shape'),
(435, 'General''s Silk Sash shape'),
(436, 'General''s Silk Cuffs shape'),
(437, 'General''s Silk Boots shape'),
(438, 'General''s Silk Handguards shape'),
(439, 'Warlord''s Plate Armor shape'),
(440, 'Warlord''s Plate Headpiece shape'),
(441, 'General''s Plate Leggings shape'),
(442, 'Warlord''s Plate Shoulders shape'),
(443, 'General''s Plate Boots shape'),
(444, 'General''s Plate Armguards shape'),
(445, 'General''s Plate Girdle shape'),
(446, 'General''s Plate Gauntlets shape'),
(447, 'Warlord''s Dragonhide Hauberk shape'),
(448, 'Warlord''s Dragonhide Helmet shape'),
(449, 'Warlord''s Dragonhide Epaulets shape'),
(450, 'General''s Dragonhide Leggings shape'),
(451, 'General''s Dragonhide Bracers shape'),
(452, 'General''s Dragonhide Boots shape'),
(453, 'General''s Dragonhide Gloves shape'),
(454, 'General''s Dragonhide Belt shape'),
(455, 'General''s Leather Girdle shape'),
(456, 'General''s Leather Treads shape'),
(457, 'General''s Leather Armsplints shape'),
(458, 'General''s Leather Mitts shape'),
(459, 'Warlord''s Leather Helm shape'),
(460, 'Warlord''s Leather Spaulders shape'),
(461, 'Warlord''s Leather Breastplate shape'),
(462, 'General''s Leather Legguards shape'),
(463, 'Warlord''s Chain Chestpiece shape'),
(464, 'Warlord''s Chain Helmet shape'),
(465, 'General''s Chain Legguards shape'),
(466, 'Warlord''s Chain Shoulders shape'),
(467, 'General''s Chain Boots shape'),
(468, 'General''s Chain Wristguards shape'),
(469, 'General''s Chain Gloves shape'),
(470, 'General''s Chain Girdle shape'),
(471, 'General''s Mail Boots shape'),
(472, 'General''s Mail Gauntlets shape'),
(473, 'General''s Mail Waistband shape'),
(474, 'General''s Mail Bracers shape'),
(475, 'Warlord''s Mail Armor shape'),
(476, 'Warlord''s Mail Helm shape'),
(477, 'General''s Mail Leggings shape'),
(478, 'Warlord''s Mail Spaulders shape'),
(479, 'Vest of Elements shape'),
(480, 'Coif of Elements shape'),
(481, 'Kilt of Elements shape'),
(482, 'Pauldrons of Elements shape'),
(483, 'Beaststalker''s Tunic shape'),
(484, 'Beaststalker''s Cap shape'),
(485, 'Beaststalker''s Pants shape'),
(486, 'Beaststalker''s Mantle shape'),
(487, 'Magister''s Crown shape'),
(488, 'Magister''s Leggings shape'),
(489, 'Magister''s Robes shape'),
(490, 'Magister''s Mantle shape'),
(491, 'Devout Robe shape'),
(492, 'Devout Crown shape'),
(493, 'Devout Skirt shape'),
(494, 'Devout Mantle shape'),
(495, 'Dreadmist Mask shape'),
(496, 'Dreadmist Leggings shape'),
(497, 'Dreadmist Robe shape'),
(498, 'Dreadmist Mantle shape'),
(499, 'Wildheart Vest shape'),
(500, 'Shadowcraft Cap shape'),
(501, 'Shadowcraft Spaulders shape'),
(502, 'Shadowcraft Pants shape'),
(503, 'Wildheart Spaulders shape'),
(504, 'Wildheart Kilt shape'),
(505, 'Wildheart Cowl shape'),
(506, 'Shadowcraft Tunic shape'),
(507, 'Lightforge Breastplate shape'),
(508, 'Lightforge Helm shape'),
(509, 'Lightforge Legplates shape'),
(510, 'Lightforge Spaulders shape'),
(511, 'Breastplate of Valor shape'),
(512, 'Helm of Valor shape'),
(513, 'Legplates of Valor shape'),
(514, 'Spaulders of Valor shape'),
(515, 'Netherwind Belt shape'),
(516, 'Bloodfang Spaulders shape'),
(517, 'Stormrage Chestguard shape'),
(518, 'Stormrage Boots shape'),
(519, 'Stormrage Handguards shape'),
(520, 'Stormrage Cover shape'),
(521, 'Stormrage Legguards shape'),
(522, 'Stormrage Pauldrons shape'),
(523, 'Stormrage Belt shape'),
(524, 'Stormrage Bracers shape'),
(525, 'Bloodfang Chestpiece shape'),
(526, 'Bloodfang Boots shape'),
(527, 'Bloodfang Gloves shape'),
(528, 'Bloodfang Hood shape'),
(529, 'Bloodfang Pants shape'),
(530, 'Bloodfang Belt shape'),
(531, 'Bloodfang Bracers shape'),
(532, 'Netherwind Boots shape'),
(533, 'Netherwind Gloves shape'),
(534, 'Netherwind Crown shape'),
(535, 'Netherwind Pants shape'),
(536, 'Netherwind Robes shape'),
(537, 'Netherwind Mantle shape'),
(538, 'Netherwind Bindings shape'),
(539, 'Boots of Transcendence shape'),
(540, 'Handguards of Transcendence shape'),
(541, 'Halo of Transcendence shape'),
(542, 'Leggings of Transcendence shape'),
(543, 'Robes of Transcendence shape'),
(544, 'Pauldrons of Transcendence shape'),
(545, 'Belt of Transcendence shape'),
(546, 'Bindings of Transcendence shape'),
(547, 'Nemesis Boots shape'),
(548, 'Nemesis Gloves shape'),
(549, 'Nemesis Skullcap shape'),
(550, 'Nemesis Leggings shape'),
(551, 'Nemesis Robes shape'),
(552, 'Nemesis Spaulders shape'),
(553, 'Nemesis Belt shape'),
(554, 'Nemesis Bracers shape'),
(555, 'Dragonstalker''s Bracers shape'),
(556, 'Dragonstalker''s Belt shape'),
(557, 'Dragonstalker''s Spaulders shape'),
(558, 'Dragonstalker''s Legguards shape'),
(559, 'Dragonstalker''s Helm shape'),
(560, 'Dragonstalker''s Gauntlets shape'),
(561, 'Dragonstalker''s Greaves shape'),
(562, 'Dragonstalker''s Breastplate shape'),
(563, 'Bracers of Ten Storms shape'),
(564, 'Belt of Ten Storms shape'),
(565, 'Epaulets of Ten Storms shape'),
(566, 'Legplates of Ten Storms shape'),
(567, 'Helmet of Ten Storms shape'),
(568, 'Gauntlets of Ten Storms shape'),
(569, 'Greaves of Ten Storms shape'),
(570, 'Breastplate of Ten Storms shape'),
(571, 'Judgement Bindings shape'),
(572, 'Judgement Belt shape'),
(573, 'Judgement Spaulders shape'),
(574, 'Judgement Legplates shape'),
(575, 'Judgement Crown shape'),
(576, 'Judgement Gauntlets shape'),
(577, 'Judgement Sabatons shape'),
(578, 'Judgement Breastplate shape'),
(579, 'Bracelets of Wrath shape'),
(580, 'Waistband of Wrath shape'),
(581, 'Pauldrons of Wrath shape'),
(582, 'Legplates of Wrath shape'),
(583, 'Helm of Wrath shape'),
(584, 'Gauntlets of Wrath shape'),
(585, 'Sabatons of Wrath shape'),
(586, 'Breastplate of Wrath shape'),
(587, 'Flarecore Gloves shape'),
(588, 'Flarecore Mantle shape'),
(589, 'Molten Helm shape'),
(590, 'Fiery Chain Shoulders shape'),
(591, 'Gorewood Bow shape'),
(592, 'Stormrager shape'),
(593, 'Sacred Protector shape'),
(594, 'Dark Iron Destroyer shape'),
(595, 'Blood of the Martyr shape'),
(596, 'Band of Accuria shape'),
(597, 'Medallion of Steadfast Might shape'),
(598, 'Drillborer Disk shape'),
(599, 'Ancient Cornerstone Grimoire shape'),
(600, 'Striker''s Mark shape'),
(601, 'Fang of the Mystics shape'),
(602, 'Blastershot Launcher shape'),
(603, 'Bonereaver''s Edge shape'),
(604, 'Crimson Shocker shape'),
(605, 'Sapphiron Drape shape'),
(606, 'Cloak of the Shrouded Mists shape'),
(607, 'Azuresong Mageblade shape'),
(608, 'Aurastone Hammer shape'),
(609, 'Malistar''s Defender shape'),
(610, 'Dragon''s Blood Cape shape'),
(611, 'Mark of Deflection shape'),
(612, 'Choker of Enlightenment shape'),
(613, 'Seal of the Archmagus shape'),
(614, 'Blazefury Medallion shape'),
(615, 'Amberseal Keeper shape'),
(616, 'Knight-Lieutenant''s Dreadweave Boots shape'),
(617, 'Knight-Captain''s Dreadweave Bracers shape'),
(618, 'Knight-Lieutenant''s Dreadweave Gloves shape'),
(619, 'Knight-Captain''s Dreadweave Belt shape'),
(620, 'Lieutenant Commander''s Headguard shape'),
(621, 'Knight-Captain''s Dreadweave Leggings shape'),
(622, 'Knight-Captain''s Dreadweave Robe shape'),
(623, 'Lieutenant Commander''s Dreadweave Mantle shape'),
(624, 'Champion''s Dreadweave Hood shape'),
(625, 'Legionnaire''s Dreadweave Leggings shape'),
(626, 'Legionnaire''s Dreadweave Robe shape'),
(627, 'Champion''s Dreadweave Shoulders shape'),
(628, 'Legionnaire''s Dreadweave Belt shape'),
(629, 'Legionnaire''s Dreadweave Bracers shape'),
(630, 'Blood Guard''s Dreadweave Boots shape'),
(631, 'Blood Guard''s Dreadweave Gloves shape'),
(632, 'Field Marshal''s Coronal shape'),
(633, 'Marshal''s Dreadweave Leggings shape'),
(634, 'Field Marshal''s Dreadweave Shoulders shape'),
(635, 'Field Marshal''s Dreadweave Robe shape'),
(636, 'Marshal''s Dreadweave Cuffs shape'),
(637, 'Marshal''s Dreadweave Boots shape'),
(638, 'Marshal''s Dreadweave Gloves shape'),
(639, 'Marshal''s Dreadweave Sash shape'),
(640, 'General''s Dreadweave Boots shape'),
(641, 'General''s Dreadweave Bracers shape'),
(642, 'General''s Dreadweave Gloves shape'),
(643, 'General''s Dreadweave Belt shape'),
(644, 'Warlord''s Dreadweave Mantle shape'),
(645, 'Warlord''s Dreadweave Hood shape'),
(646, 'Warlord''s Dreadweave Robe shape'),
(647, 'General''s Dreadweave Pants shape'),
(648, 'Knight-Lieutenant''s Satin Boots shape'),
(649, 'Knight-Captain''s Satin Cuffs shape'),
(650, 'Knight-Lieutenant''s Satin Gloves shape'),
(651, 'Knight-Captain''s Satin Cord shape'),
(652, 'Lieutenant Commander''s Diadem shape'),
(653, 'Knight-Captain''s Satin Leggings shape'),
(654, 'Knight-Captain''s Satin Robes shape'),
(655, 'Lieutenant Commander''s Satin Amice shape'),
(656, 'Field Marshal''s Headdress shape'),
(657, 'Marshal''s Satin Pants shape'),
(658, 'Field Marshal''s Satin Mantle shape'),
(659, 'Field Marshal''s Satin Vestments shape'),
(660, 'Marshal''s Satin Bracers shape'),
(661, 'Marshal''s Satin Sandals shape'),
(662, 'Marshal''s Satin Gloves shape'),
(663, 'Marshal''s Satin Sash shape'),
(664, 'Champion''s Satin Cowl shape'),
(665, 'Legionnaire''s Satin Trousers shape'),
(666, 'Legionnaire''s Satin Vestments shape'),
(667, 'Champion''s Satin Shoulderpads shape'),
(668, 'Legionnaire''s Satin Sash shape'),
(669, 'Legionnaire''s Satin Cuffs shape'),
(670, 'Blood Guard''s Satin Boots shape'),
(671, 'Blood Guard''s Satin Gloves shape'),
(672, 'General''s Satin Boots shape'),
(673, 'General''s Satin Bracers shape'),
(674, 'General''s Satin Gloves shape'),
(675, 'General''s Satin Cinch shape'),
(676, 'Warlord''s Satin Mantle shape'),
(677, 'Warlord''s Satin Cowl shape'),
(678, 'Warlord''s Satin Robes shape'),
(679, 'General''s Satin Leggings shape'),
(680, 'Royal Seal of Alexis shape'),
(681, 'Flame Walkers shape'),
(682, 'Mastersmith''s Hammer shape'),
(683, 'Dragonrider Boots shape'),
(684, 'Band of Rumination shape'),
(685, 'Feralsurge Girdle shape'),
(686, 'Eskhandar''s Left Claw shape'),
(687, 'Eskhandar''s Right Claw shape'),
(688, 'Eskhandar''s Collar shape'),
(689, 'Drape of Benediction shape'),
(690, 'Flarecore Wraps shape'),
(691, 'Core Marksman Rifle shape'),
(692, 'Gordok''s Handguards shape'),
(693, 'Gordok''s Gauntlets shape'),
(694, 'Gordok''s Gloves shape'),
(695, 'Gordok''s Handwraps shape'),
(696, 'Blade of the New Moon shape'),
(697, 'Chestplate of Tranquility shape'),
(698, 'Flamescarred Shoulders shape'),
(699, 'Bracers of the Eclipse shape'),
(700, 'Timeworn Mace shape'),
(701, 'Quickdraw Gloves shape'),
(702, 'Silvermoon Leggings shape'),
(703, 'Odious Greaves shape'),
(704, 'Eldritch Reinforced Legplates shape'),
(705, 'Evil Eye Pendant shape'),
(706, 'Force Imbued Gauntlets shape'),
(707, 'Bile-etched Spaulders shape'),
(708, 'Robe of Everlasting Night shape'),
(709, 'Padre''s Trousers shape'),
(710, 'Brightspark Gloves shape'),
(711, 'Stoneshatter shape'),
(712, 'Cloak of the Cosmos shape'),
(713, 'Tanglemoss Leggings shape'),
(714, 'Eyestalk Cord shape'),
(715, 'Distracting Dagger shape'),
(716, 'Warpwood Binding shape'),
(717, 'Emerald Flame Ring shape'),
(718, 'Mind Carver shape'),
(719, 'Elder Magus Pendant shape'),
(720, 'Tidal Loop shape'),
(721, 'Ocean''s Breeze shape'),
(722, 'Dragonslayer''s Signet shape'),
(723, 'Onyxia Tooth Pendant shape'),
(724, 'Belt of the Archmage shape'),
(725, 'Felcloth Gloves shape'),
(726, 'Inferno Gloves shape'),
(727, 'Mooncloth Gloves shape'),
(728, 'Cloak of Warding shape'),
(729, 'Bonecrusher shape'),
(730, 'Backwood Helm shape'),
(731, 'Sedge Boots shape'),
(732, 'First Sergeant''s Plate Bracers shape'),
(733, 'First Sergeant''s Dragonhide Armguards shape'),
(734, 'Master Sergeant''s Insignia shape'),
(735, 'Sergeant Major''s Plate Wristguards shape'),
(736, 'Sergeant Major''s Chain Armguards shape'),
(737, 'Sergeant Major''s Leather Armsplints shape'),
(738, 'Sergeant Major''s Dragonhide Armsplints shape'),
(739, 'Sergeant Major''s Silk Cuffs shape'),
(740, 'Observer''s Shield shape'),
(741, 'Mooncloth Robe shape'),
(742, 'Insightful Hood shape'),
(743, 'Bulky Iron Spaulders shape'),
(744, 'Denwatcher''s Shoulders shape'),
(745, 'Redoubt Cloak shape'),
(746, 'Heliotrope Cloak shape'),
(747, 'Sublime Wristguards shape'),
(748, 'Hedgecutter shape'),
(749, 'Barrier Shield shape'),
(750, 'Tarnished Elven Ring shape'),
(751, 'Monstrous Glaive shape'),
(752, 'Kromcrush''s Chestplate shape'),
(753, 'Girdle of Insight shape'),
(754, 'Mugger''s Belt shape'),
(755, 'Mongoose Boots shape'),
(756, 'Boots of the Full Moon shape'),
(757, 'Chromatic Cloak shape'),
(758, 'Hide of the Wild shape'),
(759, 'Shifting Cloak shape'),
(760, 'Barbarous Blade shape'),
(761, 'Grimy Metal Boots shape'),
(762, 'Band of the Ogre King shape'),
(763, 'Brightly Glowing Stone shape'),
(764, 'Leggings of Destruction shape'),
(765, 'Bracers of Prosperity shape'),
(766, 'Crown of the Ogre King shape'),
(767, 'Harmonious Gauntlets shape'),
(768, 'Cyclone Spaulders shape'),
(769, 'Elemental Plate Girdle shape'),
(770, 'Ogre Forged Hauberk shape'),
(771, 'Unyielding Maul shape'),
(772, 'Mindsurge Robe shape'),
(773, 'Gordok Bracers of Power shape'),
(774, 'Rod of the Ogre Magi shape'),
(775, 'Treant''s Bane shape'),
(776, 'Puissant Cape shape'),
(777, 'Typhoon shape'),
(778, 'Doomhide Gauntlets shape'),
(779, 'Leggings of Arcane Supremacy shape'),
(780, 'Infernal Headcage shape'),
(781, 'Unmelting Ice Girdle shape'),
(782, 'Benediction shape'),
(783, 'Anathema shape'),
(784, 'Sash of the Windreaver shape'),
(785, 'Tempestria''s Frozen Necklace shape'),
(786, 'Ancient Bone Bow shape'),
(787, 'Burial Shawl shape'),
(788, 'Ghoul Skin Leggings shape'),
(789, 'Hammer of the Vesper shape'),
(790, 'Dimly Opalescent Ring shape'),
(791, 'Bone Golem Shoulders shape'),
(792, 'Phantasmal Cloak shape'),
(793, 'Wraithplate Leggings shape'),
(794, 'Dark Advisor''s Pendant shape'),
(795, 'Shivery Handwraps shape'),
(796, 'Spellbound Tome shape'),
(797, 'Belt of the Ordained shape'),
(798, 'Rhok''delar, Longbow of the Ancient Keepers shape'),
(799, 'Lok''delar, Stave of the Ancient Keepers shape'),
(800, 'Ash Covered Boots shape'),
(801, 'Hammer of the Grand Crusader shape'),
(802, 'Grand Crusader''s Helm shape'),
(803, 'Shroud of the Nathrezim shape'),
(804, 'Barrage Girdle shape'),
(805, 'Death Grips shape'),
(806, 'Animated Chain Necklace shape'),
(807, 'Anastari Heirloom shape'),
(808, 'Shadowy Laced Handwraps shape'),
(809, 'Pale Moon Cloak shape'),
(810, 'Maleki''s Footwraps shape'),
(811, 'Plaguehound Leggings shape'),
(812, 'Bone Slicing Hatchet shape'),
(813, 'Carapace Spine Crossbow shape'),
(814, 'Chitinous Plate Legguards shape'),
(815, 'Thuzadin Sash shape'),
(816, 'Morlune''s Bracer shape'),
(817, 'Stratholme Militia Shoulderguard shape'),
(818, 'Fel Hardened Bracers shape'),
(819, 'Xorothian Firestick shape'),
(820, 'Dreadguard''s Protector shape'),
(821, 'Oblivion''s Touch shape'),
(822, 'Finkle''s Lava Dredger shape'),
(823, 'Core Hound Tooth shape'),
(824, 'Core Forged Greaves shape'),
(825, 'Helm of Latent Power shape'),
(826, 'Gloves of the Hypnotic Flame shape'),
(827, 'Sash of Whispered Secrets shape'),
(828, 'Wild Growth Spaulders shape'),
(829, 'Fireproof Cloak shape'),
(830, 'Wristguards of True Flight shape'),
(831, 'Ring of Binding shape'),
(832, 'Choker of the Fire Lord shape'),
(833, 'Crown of Destruction shape'),
(834, 'Quick Strike Ring shape'),
(835, 'Obsidian Edged Blade shape'),
(836, 'Aged Core Leather Gloves shape'),
(837, 'Magma Tempered Boots shape'),
(838, 'Grand Marshal''s Aegis shape'),
(839, 'High Warlord''s Shield Wall shape'),
(840, 'Grand Marshal''s Handaxe shape'),
(841, 'High Warlord''s Cleaver shape'),
(842, 'Deep Earth Spaulders shape'),
(843, 'Grand Marshal''s Sunderer shape'),
(844, 'High Warlord''s Battle Axe shape'),
(845, 'Brutality Blade shape'),
(846, 'Grand Marshal''s Dirk shape'),
(847, 'High Warlord''s Razor shape'),
(848, 'Staff of Dominance shape'),
(849, 'Grand Marshal''s Right Hand Blade shape'),
(850, 'High Warlord''s Right Claw shape'),
(851, 'Grand Marshal''s Left Hand Blade shape'),
(852, 'High Warlord''s Left Claw shape'),
(853, 'Flamewaker Legplates shape'),
(854, 'Grand Marshal''s Punisher shape'),
(855, 'High Warlord''s Bludgeon shape'),
(856, 'Grand Marshal''s Battle Hammer shape'),
(857, 'High Warlord''s Pulverizer shape'),
(858, 'Grand Marshal''s Glaive shape'),
(859, 'Helm of the Lifegiver shape'),
(860, 'High Warlord''s Pig Sticker shape'),
(861, 'Manastorm Leggings shape'),
(862, 'Grand Marshal''s Stave shape'),
(863, 'High Warlord''s War Staff shape'),
(864, 'Salamander Scale Pants shape'),
(865, 'Grand Marshal''s Claymore shape'),
(866, 'High Warlord''s Greatsword shape'),
(867, 'Sorcerous Dagger shape'),
(868, 'Timbermaw Brawlers shape'),
(869, 'Mantle of the Timbermaw shape'),
(870, 'Gloves of the Dawn shape'),
(871, 'Golden Mantle of the Dawn shape'),
(872, 'Argent Shoulders shape'),
(873, 'Frostwolf Advisor''s Cloak shape'),
(874, 'Stormpike Sage''s Cloak shape'),
(875, 'Frostwolf Plate Belt shape'),
(876, 'Frostwolf Mail Belt shape'),
(877, 'Frostwolf Leather Belt shape'),
(878, 'Frostwolf Cloth Belt shape'),
(879, 'Stormpike Plate Girdle shape'),
(880, 'Stormpike Mail Girdle shape'),
(881, 'Stormpike Leather Girdle shape'),
(882, 'Stormpike Cloth Girdle shape'),
(883, 'Frostwolf Advisor''s Pendant shape'),
(884, 'Stormpike Sage''s Pendant shape'),
(885, 'Glacial Blade shape'),
(886, 'Electrified Dagger shape'),
(887, 'Whiteout Staff shape'),
(888, 'Crackling Staff shape'),
(889, 'Frostbite shape'),
(890, 'Stormstrike Hammer shape'),
(891, 'Frost Runed Headdress shape'),
(892, 'Ice Barbed Spear shape'),
(893, 'Bloodseeker shape'),
(894, 'Wand of Biting Cold shape'),
(895, 'Deep Rooted Ring shape'),
(896, 'Cold Forged Blade shape'),
(897, 'Winteraxe Epaulets shape'),
(898, 'Frozen Steel Vambraces shape'),
(899, 'Yeti Hide Bracers shape'),
(900, 'Cold Snap shape'),
(901, 'Snowblind Shoes shape'),
(902, 'Crystal Adorned Crown shape'),
(903, 'Fel Infused Leggings shape'),
(904, 'Flayed Doomguard Belt shape'),
(905, 'Mana Igniting Cord shape'),
(906, 'Onslaught Girdle shape'),
(907, 'Band of Sulfuras shape'),
(908, 'Cauterizing Band shape'),
(909, 'Fire Runed Grimoire shape'),
(910, 'Flameguard Gauntlets shape'),
(911, 'Sabatons of the Flamewalker shape'),
(912, 'Wristguards of Stability shape'),
(913, 'Chromatic Gauntlets shape'),
(914, 'Corehound Belt shape'),
(915, 'Molten Belt shape'),
(916, 'Dark Iron Gauntlets shape'),
(917, 'Flarecore Leggings shape'),
(918, 'Blackfury shape'),
(919, 'Blackguard shape'),
(920, 'Tome of Arcane Domination shape'),
(921, 'Tome of Shadow Force shape'),
(922, 'Tome of the Ice Lord shape'),
(923, 'Tome of Fiery Arcana shape'),
(924, 'Lei of the Lifegiver shape'),
(925, 'Therazane''s Touch shape'),
(926, 'The Unstoppable Force shape'),
(927, 'Don Julio''s Band shape'),
(928, 'The Untamed Blade shape'),
(929, 'Spineshatter shape'),
(930, 'Dragonfang Blade shape'),
(931, 'Claw of Chromaggus shape'),
(932, 'Red Dragonscale Protector shape'),
(933, 'Elementium Reinforced Bulwark shape'),
(934, 'Maladath, Runed Blade of the Black Flight shape'),
(935, 'Chromatically Tempered Sword shape'),
(936, 'Drake Talon Cleaver shape'),
(937, 'Draconic Avenger shape'),
(938, 'Shadow Wing Focus Staff shape'),
(939, 'Staff of the Shadow Flame shape'),
(940, 'Herald of Woe shape'),
(941, 'Draconic Maul shape'),
(942, 'Lok''amir il Romathis shape'),
(943, 'Doom''s Edge shape'),
(944, 'Claw of the Black Drake shape'),
(945, 'Master Dragonslayer''s Orb shape'),
(946, 'Dragon''s Touch shape'),
(947, 'Dragonbreath Hand Cannon shape'),
(948, 'Gloves of Rapid Evolution shape'),
(949, 'Mantle of the Blackwing Cabal shape'),
(950, 'Pendant of the Fallen Dragon shape'),
(951, 'Helm of Endless Rage shape'),
(952, 'Black Brood Pauldrons shape'),
(953, 'Bracers of Arcane Accuracy shape'),
(954, 'Mish''undare, Circlet of the Mind Flayer shape'),
(955, 'Archimtiros'' Ring of Reckoning shape'),
(956, 'Prestor''s Talisman of Connivery shape'),
(957, 'Cloak of the Brood Lord shape'),
(958, 'Therazane''s Link shape'),
(959, 'Boots of the Shadow Flame shape'),
(960, 'Pure Elementium Band shape'),
(961, 'Master Dragonslayer''s Medallion shape'),
(962, 'Master Dragonslayer''s Ring shape'),
(963, 'Empowered Leggings shape'),
(964, 'Elementium Threaded Cloak shape'),
(965, 'Chromatic Boots shape'),
(966, 'Angelista''s Grasp shape'),
(967, 'Taut Dragonhide Gloves shape'),
(968, 'Shimmering Geta shape'),
(969, 'Girdle of the Fallen Crusader shape'),
(970, 'Primalist''s Linked Waistguard shape'),
(971, 'Drake Talon Pauldrons shape'),
(972, 'Taut Dragonhide Belt shape'),
(973, 'Ring of Blackrock shape'),
(974, 'Black Ash Robe shape'),
(975, 'Firemaw''s Clutch shape'),
(976, 'Primalist''s Linked Legguards shape'),
(977, 'Legguards of the Fallen Crusader shape'),
(978, 'Band of Forced Concentration shape'),
(979, 'Malfurion''s Blessed Bulwark shape'),
(980, 'Ebony Flame Gloves shape'),
(981, 'Orb of the Darkmoon shape'),
(982, 'Shroud of Pure Thought shape'),
(983, 'Circle of Applied Force shape'),
(984, 'Emberweave Leggings shape'),
(985, 'Band of Dark Dominion shape'),
(986, 'Essence Gatherer shape'),
(987, 'Cloak of Draconic Might shape'),
(988, 'Boots of Pure Thought shape'),
(989, 'Ringo''s Blizzard Boots shape'),
(990, 'Amulet of the Darkmoon shape'),
(991, 'Legionnaire''s Band shape'),
(992, 'Protector''s Band shape'),
(993, 'Advisor''s Ring shape'),
(994, 'Lorekeeper''s Ring shape'),
(995, 'Battle Healer''s Cloak shape'),
(996, 'Caretaker''s Cape shape'),
(997, 'Scout''s Medallion shape'),
(998, 'Sentinel''s Medallion shape'),
(999, 'Scout''s Blade shape'),
(1000, 'Sentinel''s Blade shape'),
(1001, 'Legionnaire''s Sword shape'),
(1002, 'Protector''s Sword shape'),
(1003, 'Outrider''s Bow shape'),
(1004, 'Outrunner''s Bow shape'),
(1005, 'Advisor''s Gnarled Staff shape'),
(1006, 'Lorekeeper''s Staff shape'),
(1007, 'Strength of Mugamba shape'),
(1008, 'Strength of Mugamba shape'),
(1009, 'Rage of Mugamba shape'),
(1010, 'Berserker Bracers shape'),
(1011, 'Windtalker''s Wristguards shape'),
(1012, 'Heathen''s Brand shape'),
(1013, 'Heathen''s Brand shape'),
(1014, 'Forest Stalker''s Bracers shape'),
(1015, 'Hero''s Brand shape'),
(1016, 'The Eye of Zuldazar shape'),
(1017, 'The Eye of Zuldazar shape'),
(1018, 'The All-Seeing Eye of Zuldazar shape'),
(1019, 'Dryad''s Wrist Bindings shape'),
(1020, 'Pebble of Kajaro shape'),
(1021, 'Pebble of Kajaro shape'),
(1022, 'Jewel of Kajaro shape'),
(1023, 'Kezan''s Taint shape'),
(1024, 'Kezan''s Taint shape'),
(1025, 'Kezan''s Unstoppable Taint shape'),
(1026, 'Vision of Voodress shape'),
(1027, 'Vision of Voodress shape'),
(1028, 'Unmarred Vision of Voodress shape'),
(1029, 'Enchanted South Seas Kelp shape'),
(1030, 'Enchanted South Seas Kelp shape'),
(1031, 'Pristine Enchanted South Seas Kelp shape'),
(1032, 'Zandalarian Shadow Talisman shape'),
(1033, 'Zandalarian Shadow Talisman shape'),
(1034, 'Zandalarian Shadow Mastery Talisman shape'),
(1035, 'Maelstrom''s Tendril shape'),
(1036, 'Maelstrom''s Tendril shape'),
(1037, 'Maelstrom''s Wrath shape'),
(1038, 'Bloodvine Vest shape'),
(1039, 'Bloodvine Leggings shape'),
(1040, 'Bloodvine Boots shape'),
(1041, 'Primal Batskin Jerkin shape'),
(1042, 'Primal Batskin Gloves shape'),
(1043, 'Primal Batskin Bracers shape'),
(1044, 'Blood Tiger Breastplate shape'),
(1045, 'Blood Tiger Shoulders shape'),
(1046, 'Bloodsoul Breastplate shape'),
(1047, 'Bloodsoul Shoulders shape'),
(1048, 'Bloodsoul Gauntlets shape'),
(1049, 'Darksoul Breastplate shape'),
(1050, 'Darksoul Leggings shape'),
(1051, 'Darksoul Shoulders shape'),
(1052, 'Zandalar Vindicator''s Breastplate shape'),
(1053, 'Zandalar Vindicator''s Belt shape'),
(1054, 'Zandalar Vindicator''s Armguards shape'),
(1055, 'Zandalar Freethinker''s Breastplate shape'),
(1056, 'Zandalar Freethinker''s Belt shape'),
(1057, 'Zandalar Freethinker''s Armguards shape'),
(1058, 'Zandalar Augur''s Hauberk shape'),
(1059, 'Zandalar Augur''s Belt shape'),
(1060, 'Zandalar Augur''s Bracers shape'),
(1061, 'Zandalar Predator''s Mantle shape'),
(1062, 'Zandalar Predator''s Belt shape'),
(1063, 'Zandalar Predator''s Bracers shape'),
(1064, 'Zandalar Madcap''s Tunic shape'),
(1065, 'Zandalar Madcap''s Mantle shape'),
(1066, 'Zandalar Madcap''s Bracers shape'),
(1067, 'Zandalar Haruspex''s Tunic shape'),
(1068, 'Zandalar Haruspex''s Belt shape'),
(1069, 'Zandalar Haruspex''s Bracers shape'),
(1070, 'Zandalar Confessor''s Mantle shape'),
(1071, 'Zandalar Confessor''s Bindings shape'),
(1072, 'Zandalar Confessor''s Wraps shape'),
(1073, 'Zandalar Illusionist''s Robe DEPRECATED shape'),
(1074, 'Zandalar Illusionist''s Mantle shape'),
(1075, 'Zandalar Illusionist''s Wraps shape'),
(1076, 'Zandalar Demoniac''s Wraps shape'),
(1077, 'Zandalar Demoniac''s Mantle shape'),
(1078, 'Bloodsoaked Legplates shape'),
(1079, 'The Eye of Hakkar shape'),
(1080, 'Cloak of Consumption shape'),
(1081, 'Fang of the Faceless shape'),
(1082, 'Touch of Chaos shape'),
(1083, 'Aegis of the Blood God shape'),
(1084, 'Primalist''s Seal shape'),
(1085, 'Bloodcaller shape'),
(1086, 'Warblade of the Hakkari shape'),
(1087, 'Bloodlord''s Defender shape'),
(1088, 'Mandokir''s Sting DEPRECATED shape'),
(1089, 'Blooddrenched Grips shape'),
(1090, 'Hakkari Loa Cloak shape'),
(1091, 'Talisman of Protection shape'),
(1092, 'Overlord''s Crimson Band shape'),
(1093, 'Bloodstained Coif shape'),
(1094, 'Soul Corrupter''s Necklace shape'),
(1095, 'Animist''s Leggings shape'),
(1096, 'Bloodsoaked Pauldrons shape'),
(1097, 'Jin''do''s Judgement shape'),
(1098, 'The Hexxer''s Cover shape'),
(1099, 'Bloodstained Legplates shape'),
(1100, 'Overlord''s Embrace shape'),
(1101, 'Blooddrenched Leggings shape'),
(1102, 'Jin''do''s Hexxer shape'),
(1103, 'Animist''s Boots shape'),
(1104, 'Zanzil''s Seal shape'),
(1105, 'Bloodsoaked Gauntlets shape'),
(1106, 'Bloodtinged Kilt shape'),
(1107, 'Thekal''s Grasp shape'),
(1108, 'Betrayer''s Boots shape'),
(1109, 'Seal of Jin shape'),
(1110, 'Ritualistic Legguards shape'),
(1111, 'Zulian Stone Axe shape'),
(1112, 'Fang of Venoxis shape'),
(1113, 'Runed Bloodstained Hauberk shape'),
(1114, 'Zanzil''s Band shape'),
(1115, 'Blooddrenched Footpads shape'),
(1116, 'Zulian Tigerhide Cloak shape'),
(1117, 'Sceptre of Smiting shape'),
(1118, 'Will of Arlokk shape'),
(1119, 'Overlord''s Onyx Band shape'),
(1120, 'Bloodsoaked Greaves shape'),
(1121, 'Zulian Defender shape'),
(1122, 'Bloodstained Greaves shape'),
(1123, 'Primalist''s Band shape'),
(1124, 'Zulian Hacker shape'),
(1125, 'Arlokk''s Hoodoo Stick shape'),
(1126, 'Jeklik''s Opaline Talisman shape'),
(1127, 'Band of Jin shape'),
(1128, 'Flowing Ritual Robes DEPRECATED shape'),
(1129, 'Mar''li''s Touch shape'),
(1130, 'Animist''s Spaulders shape'),
(1131, 'Bloodtinged Gloves shape'),
(1132, 'Nat Pagle''s Fish Terminator shape'),
(1133, 'Foror''s Eyepatch shape'),
(1134, 'Tigule''s Harpoon shape'),
(1135, 'Renataki''s Soul Conduit shape'),
(1136, 'Wushoolay''s Poker shape'),
(1137, 'Thrice Strung Longbow DEPRECATED shape'),
(1138, 'Fiery Retributer shape'),
(1139, 'Hoodoo Hunting Bow shape'),
(1140, 'Bloodvine Lens shape'),
(1141, 'Bloodvine Goggles shape'),
(1142, 'Flowing Ritual Robes shape'),
(1143, 'Zandalar Demoniac''s Robe shape'),
(1144, 'Zandalar Illusionist''s Robe shape'),
(1145, 'Mandokir''s Sting shape'),
(1146, 'Highlander''s Plate Girdle shape'),
(1147, 'Highlander''s Lamellar Girdle shape'),
(1148, 'Highlander''s Chain Girdle shape'),
(1149, 'Highlander''s Mail Girdle shape'),
(1150, 'Highlander''s Leather Girdle shape'),
(1151, 'Highlander''s Lizardhide Girdle shape'),
(1152, 'Highlander''s Cloth Girdle shape'),
(1153, 'Highlander''s Plate Greaves shape'),
(1154, 'Highlander''s Lamellar Greaves shape'),
(1155, 'Highlander''s Chain Greaves shape'),
(1156, 'Highlander''s Mail Greaves shape'),
(1157, 'Highlander''s Leather Boots shape'),
(1158, 'Highlander''s Lizardhide Boots shape'),
(1159, 'Highlander''s Cloth Boots shape'),
(1160, 'Highlander''s Chain Pauldrons shape'),
(1161, 'Highlander''s Mail Pauldrons shape'),
(1162, 'Highlander''s Plate Spaulders shape'),
(1163, 'Highlander''s Lamellar Spaulders shape'),
(1164, 'Highlander''s Leather Shoulders shape'),
(1165, 'Highlander''s Lizardhide Shoulders shape'),
(1166, 'Highlander''s Epaulets shape'),
(1167, 'Deathguard''s Cloak shape'),
(1168, 'Ironbark Staff shape'),
(1169, 'Sageclaw shape'),
(1170, 'Cloak of the Honor Guard shape'),
(1171, 'Skyfury Helm shape'),
(1172, '90 Epic Warrior Bracelets shape'),
(1173, '90 Epic Warrior Breastplate shape'),
(1174, '90 Epic Warrior Gauntlets shape'),
(1175, '90 Epic Warrior Helm shape'),
(1176, '90 Epic Warrior Legplates shape'),
(1177, '90 Epic Warrior Pauldrons shape'),
(1178, '90 Epic Warrior Sabatons shape'),
(1179, '90 Epic Warrior Waistband shape'),
(1180, '90 Epic Warrior Neck shape'),
(1181, '90 Epic Warrior Ring shape'),
(1182, '90 Epic Warrior Cloak shape'),
(1183, '90 Epic Warrior Gun shape'),
(1184, '90 Epic Warrior Axe shape'),
(1185, 'Defiler''s Chain Girdle shape'),
(1186, 'Defiler''s Chain Greaves shape'),
(1187, 'Defiler''s Chain Pauldrons shape'),
(1188, 'Defiler''s Cloth Boots shape'),
(1189, 'Defiler''s Cloth Girdle shape'),
(1190, 'Defiler''s Lizardhide Boots shape'),
(1191, 'Defiler''s Lizardhide Girdle shape'),
(1192, 'Defiler''s Lizardhide Shoulders shape'),
(1193, 'Defiler''s Epaulets shape'),
(1194, 'Defiler''s Lamellar Girdle shape'),
(1195, 'Defiler''s Lamellar Greaves shape'),
(1196, 'Defiler''s Lamellar Spaulders shape'),
(1197, 'Defiler''s Leather Boots shape'),
(1198, 'Defiler''s Leather Girdle shape'),
(1199, 'Defiler''s Leather Shoulders shape'),
(1200, 'Defiler''s Mail Girdle shape'),
(1201, 'Defiler''s Mail Greaves shape'),
(1202, 'Defiler''s Mail Pauldrons shape'),
(1203, 'Defiler''s Plate Girdle shape'),
(1204, 'Defiler''s Plate Greaves shape'),
(1205, 'Defiler''s Plate Spaulders shape'),
(1206, 'Belt of Shrunken Heads shape'),
(1207, 'Mindfang shape'),
(1208, 'Belt of Shriveled Heads shape'),
(1209, 'Belt of Preserved Heads shape'),
(1210, 'Belt of Tiny Heads shape'),
(1211, 'Ironbark Staff shape'),
(1212, 'Seafury Gauntlets shape'),
(1213, 'Zulian Ceremonial Staff shape'),
(1214, 'Shadow Panther Hide Gloves shape'),
(1215, 'Seafury Leggings shape'),
(1216, 'Shadow Panther Hide Belt shape'),
(1217, 'Seafury Boots shape'),
(1218, 'Gurubashi Helm shape'),
(1219, 'Peacekeeper Gauntlets shape'),
(1220, 'Peacekeeper Boots shape'),
(1221, 'Peacekeeper Leggings shape'),
(1222, '90 Epic Rogue Belt shape'),
(1223, '90 Epic Rogue Boots shape'),
(1224, '90 Epic Rogue Bracers shape'),
(1225, '90 Epic Rogue Cap shape'),
(1226, '90 Epic Rogue Gloves shape'),
(1227, '90 Epic Rogue Pants shape'),
(1228, '90 Epic Rogue Spaulders shape'),
(1229, '90 Epic Rogue Tunic shape'),
(1230, '90 Epic Rogue Neck shape'),
(1231, '90 Epic Rogue Cloak shape'),
(1232, '90 Epic Rogue Ring shape'),
(1233, '90 Epic Rogue Bow shape'),
(1234, '90 Epic Rogue Dagger shape'),
(1235, 'Blue Dragonscale Leggings shape'),
(1236, '90 Epic Frost Belt shape'),
(1237, '90 Epic Frost Bindings shape'),
(1238, '90 Epic Frost Boots shape'),
(1239, '90 Epic Frost Crown shape'),
(1240, '90 Epic Frost Gloves shape'),
(1241, '90 Epic Frost Leggings shape'),
(1242, '90 Epic Frost Mantle shape'),
(1243, '90 Epic Frost Robes shape'),
(1244, '90 Epic Frost Neck shape'),
(1245, '90 Epic Frost Ring shape'),
(1246, '90 Epic Frost Staff shape'),
(1247, '90 Epic Frost Wand shape'),
(1248, '90 Epic Frost Shroud shape'),
(1249, 'Dreamscale Breastplate shape'),
(1250, 'Spitfire Breastplate shape'),
(1251, 'Spitfire Gauntlets shape'),
(1252, 'Spitfire Bracers shape'),
(1253, 'Lok''delar, Stave of the Ancient Keepers DEP shape'),
(1254, 'Rhok''delar, Longbow of the Ancient Keepers DEP shape'),
(1255, 'Darkrune Gauntlets shape'),
(1256, 'Darkrune Breastplate shape'),
(1257, 'Darkrune Helm shape'),
(1258, 'Emerald Dragonfang shape'),
(1259, 'Hammer of Bestial Fury shape'),
(1260, 'Staff of Rampant Growth shape'),
(1261, 'Trance Stone shape'),
(1262, 'Dragonbone Wristguards shape'),
(1263, 'Ancient Corroded Leggings shape'),
(1264, 'Gloves of Delusional Power shape'),
(1265, 'Acid Inscribed Greaves shape'),
(1266, 'Boots of the Endless Moor shape'),
(1267, 'Dragonheart Necklace shape'),
(1268, 'Circlet of Restless Dreams shape'),
(1269, 'Ring of the Unliving shape'),
(1270, 'Belt of the Dark Bog shape'),
(1271, 'Black Bark Wristbands shape'),
(1272, 'Dark Heart Pants shape'),
(1273, 'Deviate Growth Cap shape'),
(1274, 'Malignant Footguards shape'),
(1275, 'Gauntlets of the Shining Light shape'),
(1276, 'Mendicant''s Slippers shape'),
(1277, 'Mindtear Band shape'),
(1278, 'Unnatural Leather Spaulders shape'),
(1279, 'Boots of Fright shape'),
(1280, 'Jade Inlaid Vestments shape'),
(1281, 'Acid Inscribed Pauldrons shape'),
(1282, 'Leggings of the Demented Mind shape'),
(1283, 'Strangely Glyphed Legplates shape'),
(1284, 'Cold Forged Hammer shape'),
(1285, 'Amethyst War Staff shape'),
(1286, 'Stonecutting Glaive shape'),
(1287, 'Deep Strike Bow shape'),
(1288, 'Abyssal Leather Leggings shape'),
(1289, 'Hardened Steel Warhammer shape'),
(1290, 'Abyssal Mail Legguards shape'),
(1291, 'Abyssal Plate Legguards shape'),
(1292, 'Sparkling Crystal Wand shape'),
(1293, 'Abyssal Cloth Pants shape'),
(1294, 'Abyssal Mail Pauldrons shape'),
(1295, 'Elemental Focus Band shape'),
(1296, 'Abyssal Plate Epaulets shape'),
(1297, 'Wavefront Necklace shape'),
(1298, 'Abyssal Cloth Amice shape'),
(1299, 'Earthen Guard shape'),
(1300, 'Abyssal Leather Shoulders shape'),
(1301, 'Windshear Cape shape'),
(1302, 'Crystal Spiked Maul shape'),
(1303, 'Crystalline Threaded Cape shape'),
(1304, 'Elemental Attuned Blade shape'),
(1305, 'Cenarion Reservist''s Legplates shape'),
(1306, 'Cenarion Reservist''s Legplates shape'),
(1307, 'Cenarion Reservist''s Legguards shape'),
(1308, 'Cenarion Reservist''s Legguards shape'),
(1309, 'Cenarion Reservist''s Leggings shape'),
(1310, 'Cenarion Reservist''s Pants shape'),
(1311, 'Cenarion Reservist''s Pants shape'),
(1312, 'Cenarion Reservist''s Pants shape'),
(1313, 'Crystal Encrusted Greaves shape'),
(1314, 'Crystal Lined Greaves shape'),
(1315, 'Wastewalker''s Gauntlets shape'),
(1316, 'Desertstalkers''s Gauntlets shape'),
(1317, 'Sandstorm Boots shape'),
(1318, 'Dunestalker''s Boots shape'),
(1319, 'Sandworm Skin Gloves shape'),
(1320, 'Desert Bloom Gloves shape'),
(1321, 'Dark Whisper Blade shape'),
(1322, 'Band of the Cultist shape'),
(1323, 'Death''s Sting shape'),
(1324, 'Staff of the Qiraji Prophets shape'),
(1325, 'Dark Edge of Insanity shape'),
(1326, 'Gloves of Earthen Power shape'),
(1327, 'Band of Earthen Wrath shape'),
(1328, 'Band of Earthen Might shape'),
(1329, 'Earthpower Vest shape'),
(1330, 'Deeprock Bracers shape'),
(1331, 'Earthcalm Orb shape'),
(1332, 'Rockfury Bracers shape'),
(1333, 'Earthweave Cloak shape'),
(1334, 'Fist of Cenarius shape'),
(1335, 'Might of Cenarius shape'),
(1336, 'Signet Ring of the Bronze Dragonflight shape'),
(1337, 'Signet Ring of the Bronze Dragonflight shape'),
(1338, 'Signet Ring of the Bronze Dragonflight shape'),
(1339, 'Signet Ring of the Bronze Dragonflight shape'),
(1340, 'Signet Ring of the Bronze Dragonflight shape'),
(1341, 'Signet Ring of the Bronze Dragonflight shape'),
(1342, 'Signet Ring of the Bronze Dragonflight shape'),
(1343, 'Signet Ring of the Bronze Dragonflight shape'),
(1344, 'Signet Ring of the Bronze Dragonflight shape'),
(1345, 'Signet Ring of the Bronze Dragonflight shape'),
(1346, 'Signet Ring of the Bronze Dragonflight shape'),
(1347, 'Signet Ring of the Bronze Dragonflight shape'),
(1348, 'Signet Ring of the Bronze Dragonflight shape'),
(1349, 'Signet Ring of the Bronze Dragonflight shape'),
(1350, 'Signet Ring of the Bronze Dragonflight shape'),
(1351, 'Blessed Qiraji War Axe shape'),
(1352, 'Blessed Qiraji Pugio shape'),
(1353, 'Blessed Qiraji War Hammer shape'),
(1354, 'Blessed Qiraji Bulwark shape'),
(1355, 'Blessed Qiraji Acolyte Staff shape'),
(1356, 'Blessed Qiraji Augur Staff shape'),
(1357, 'Conqueror''s Crown shape'),
(1358, 'Conqueror''s Spaulders shape'),
(1359, 'Conqueror''s Breastplate shape'),
(1360, 'Conqueror''s Legguards shape'),
(1361, 'Conqueror''s Greaves shape'),
(1362, 'Doomcaller''s Robes shape'),
(1363, 'Doomcaller''s Mantle shape'),
(1364, 'Doomcaller''s Trousers shape'),
(1365, 'Doomcaller''s Circlet shape'),
(1366, 'Doomcaller''s Footwraps shape'),
(1367, 'Enigma Robes shape'),
(1368, 'Enigma Boots shape'),
(1369, 'Enigma Shoulderpads shape'),
(1370, 'Enigma Leggings shape'),
(1371, 'Enigma Circlet shape'),
(1372, 'Tiara of the Oracle shape'),
(1373, 'Footwraps of the Oracle shape'),
(1374, 'Mantle of the Oracle shape'),
(1375, 'Vestments of the Oracle shape'),
(1376, 'Trousers of the Oracle shape'),
(1377, 'Genesis Helm shape'),
(1378, 'Genesis Shoulderpads shape'),
(1379, 'Genesis Boots shape'),
(1380, 'Genesis Trousers shape'),
(1381, 'Genesis Vest shape'),
(1382, 'Deathdealer''s Boots shape'),
(1383, 'Deathdealer''s Helm shape'),
(1384, 'Deathdealer''s Spaulders shape'),
(1385, 'Deathdealer''s Leggings shape'),
(1386, 'Deathdealer''s Vest shape'),
(1387, 'Striker''s Footguards shape'),
(1388, 'Striker''s Diadem shape'),
(1389, 'Striker''s Pauldrons shape'),
(1390, 'Striker''s Leggings shape'),
(1391, 'Striker''s Hauberk shape'),
(1392, 'Stormcaller''s Diadem shape'),
(1393, 'Stormcaller''s Footguards shape'),
(1394, 'Stormcaller''s Hauberk shape'),
(1395, 'Stormcaller''s Leggings shape'),
(1396, 'Stormcaller''s Pauldrons shape'),
(1397, 'Avenger''s Crown shape'),
(1398, 'Avenger''s Greaves shape'),
(1399, 'Avenger''s Breastplate shape'),
(1400, 'Avenger''s Legguards shape'),
(1401, 'Avenger''s Pauldrons shape'),
(1402, 'Sickle of Unyielding Strength shape'),
(1403, 'Signet of Unyielding Strength shape'),
(1404, 'Drape of Unyielding Strength shape'),
(1405, 'Blade of Eternal Justice shape'),
(1406, 'Ring of Eternal Justice shape'),
(1407, 'Cape of Eternal Justice shape'),
(1408, 'Hammer of the Gathering Storm shape'),
(1409, 'Ring of the Gathering Storm shape'),
(1410, 'Cloak of the Gathering Storm shape'),
(1411, 'Scythe of the Unseen Path shape'),
(1412, 'Signet of the Unseen Path shape'),
(1413, 'Cloak of the Unseen Path shape'),
(1414, 'Dagger of Veiled Shadows shape'),
(1415, 'Band of Veiled Shadows shape'),
(1416, 'Cloak of Veiled Shadows shape'),
(1417, 'Mace of Unending Life shape'),
(1418, 'Band of Unending Life shape'),
(1419, 'Cloak of Unending Life shape'),
(1420, 'Gavel of Infinite Wisdom shape'),
(1421, 'Ring of Infinite Wisdom shape'),
(1422, 'Shroud of Infinite Wisdom shape'),
(1423, 'Blade of Vaulted Secrets shape'),
(1424, 'Band of Vaulted Secrets shape'),
(1425, 'Drape of Vaulted Secrets shape'),
(1426, 'Kris of Unspoken Names shape'),
(1427, 'Ring of Unspoken Names shape'),
(1428, 'Shroud of Unspoken Names shape'),
(1429, 'Staff of the Ruins shape'),
(1430, 'Mantle of the Horusath shape'),
(1431, 'Runic Stone Shoulders shape'),
(1432, 'Southwind Helm shape'),
(1433, 'Sandstorm Cloak shape'),
(1434, 'Bracers of Brutality shape'),
(1435, 'Gauntlets of New Life shape'),
(1436, 'Crossbow of Imminent Doom shape'),
(1437, 'Helm of Domination shape'),
(1438, 'Leggings of the Black Blizzard shape'),
(1439, 'Gloves of Dark Wisdom shape'),
(1440, 'Ossirian''s Binding shape'),
(1441, 'Shackles of the Unscarred shape'),
(1442, 'Stinger of Ayamiss shape'),
(1443, 'Thick Silithid Chestguard shape'),
(1444, 'Mantle of Maz''Nadir shape'),
(1445, 'Gauntlets of Southwind shape'),
(1446, 'Cloak of the Savior shape'),
(1447, 'Talon of Furious Concentration shape'),
(1448, 'Dustwind Turban shape'),
(1449, 'Chitinous Shoulderguards shape'),
(1450, 'Legplates of the Destroyer shape'),
(1451, 'Obsidian Scaled Leggings shape'),
(1452, 'Ring of Fury shape'),
(1453, 'Gauntlets of the Immovable shape'),
(1454, 'Scaled Silithid Gauntlets shape'),
(1455, 'Boots of the Desert Protector shape'),
(1456, 'Boots of the Fiery Sands shape'),
(1457, 'Ring of the Desert Winds shape'),
(1458, 'Helm of Regrowth shape'),
(1459, 'Buru''s Skull Fragment shape'),
(1460, 'Gloves of the Swarm shape'),
(1461, 'Slimy Scaled Gauntlets shape'),
(1462, 'Quicksand Waders shape'),
(1463, 'Slime Kickers shape'),
(1464, 'Scaled Bracers of the Gorger shape'),
(1465, 'Manslayer of the Qiraji shape'),
(1466, 'Southwind''s Grasp shape'),
(1467, 'Legplates of the Qiraji Command shape'),
(1468, 'Bracers of Qiraji Command shape'),
(1469, 'Boots of the Qiraji General shape'),
(1470, 'Belt of the Inquisition shape'),
(1471, 'Toughened Silithid Hide Gloves shape'),
(1472, 'Sand Reaver Wristguards shape'),
(1473, 'Belt of the Sand Reaver shape'),
(1474, 'Charm of the Shifting Sands shape'),
(1475, 'Pendant of the Shifting Sands shape'),
(1476, 'Amulet of the Shifting Sands shape'),
(1477, 'Gnomish Turban of Psychic Might shape'),
(1478, 'Ravencrest''s Legacy shape'),
(1479, 'Runesword of the Red shape'),
(1480, 'Shadowsong''s Sorrow shape'),
(1481, 'Fang of Korialstrasz shape'),
(1482, 'Darkwater Robes shape'),
(1483, 'Amulet of Shadow Shielding shape'),
(1484, 'Onyx Embedded Leggings shape'),
(1485, 'Drake Tooth Necklace shape'),
(1486, 'Drudge Boots shape'),
(1487, 'Don Rodrigo''s Band shape'),
(1488, 'Gauntlets of Annihilation shape'),
(1489, 'Grasp of the Old God shape'),
(1490, 'Cloak of Clarity shape'),
(1491, 'Bracers of Eternal Reckoning shape'),
(1492, 'Dark Storm Gauntlets shape'),
(1493, 'Belt of Never-ending Agony shape'),
(1494, 'Wristguards of Castigation shape'),
(1495, 'Wristguards of Elemental Fury shape'),
(1496, 'Bracers of the Fallen Son shape'),
(1497, 'Ring of the Godslayer shape'),
(1498, 'Royal Scepter of Vek''lor shape'),
(1499, 'Royal Qiraji Belt shape'),
(1500, 'Vek''lor''s Gloves of Devastation shape'),
(1501, 'Boots of Epiphany shape'),
(1502, 'Ring of Emperor Vek''lor shape'),
(1503, 'Qiraji Execution Bracers shape'),
(1504, 'Wand of Qiraji Nobility shape'),
(1505, 'Bracelets of Royal Redemption shape'),
(1506, 'Gloves of the Hidden Temple shape'),
(1507, 'Belt of the Fallen Emperor shape'),
(1508, 'Grasp of the Fallen Emperor shape'),
(1509, 'Amulet of Vek''nilash shape'),
(1510, 'Regenerating Belt of Vek''nilash shape'),
(1511, 'Wormscale Blocker shape'),
(1512, 'Burrower Bracers shape'),
(1513, 'Wormscale Stompers shape'),
(1514, 'Wormhide Boots shape'),
(1515, 'Wormhide Protector shape'),
(1516, 'Don Rigoberto''s Lost Hat shape'),
(1517, 'Huhuran''s Stinger shape'),
(1518, 'Wasphide Gauntlets shape'),
(1519, 'Hive Defiler Wristguards shape'),
(1520, 'Gloves of the Messiah shape'),
(1521, 'Ring of the Martyr shape'),
(1522, 'Cloak of the Golden Hive shape'),
(1523, 'Sharpened Silithid Femur shape'),
(1524, 'Gauntlets of the Righteous Champion shape'),
(1525, 'Gauntlets of Kalimdor shape'),
(1526, 'Slime-coated Leggings shape'),
(1527, 'Barb of the Sand Reaver shape'),
(1528, 'Pauldrons of the Unrelenting shape'),
(1529, 'Hive Tunneler''s Boots shape'),
(1530, 'Recomposed Boots shape'),
(1531, 'Ancient Qiraji Ripper shape'),
(1532, 'Scaled Sand Reaver Leggings shape'),
(1533, 'Silithid Carapace Chestguard shape'),
(1534, 'Robes of the Guardian Saint shape'),
(1535, 'Barbed Choker shape'),
(1536, 'Mantle of Wicked Revenge shape'),
(1537, 'Sartura''s Might shape'),
(1538, 'Legplates of Blazing Light shape'),
(1539, 'Scaled Leggings of Qiraji Fury shape'),
(1540, 'Creeping Vine Helm shape'),
(1541, 'Robes of the Battleguard shape'),
(1542, 'Gloves of Enforcement shape'),
(1543, 'Silithid Claw shape'),
(1544, 'Gauntlets of Steadfast Determination shape'),
(1545, 'Thick Qirajihide Belt shape'),
(1546, 'Leggings of the Festering Swarm shape'),
(1547, 'Ring of the Qiraji Fury shape'),
(1548, 'Necklace of Purity shape'),
(1549, 'Kalimdor''s Revenge shape'),
(1550, 'Vest of Swift Execution shape'),
(1551, 'Ring of the Devoured shape'),
(1552, 'Bile-Covered Gauntlets shape'),
(1553, 'Mantle of the Desert Crusade shape'),
(1554, 'Mantle of the Desert''s Fury shape'),
(1555, 'Mantle of Phrenic Power shape'),
(1556, 'Boots of the Fallen Hero shape'),
(1557, 'Gloves of Ebru shape'),
(1558, 'Angelista''s Charm shape'),
(1559, 'Ooze-ridden Gauntlets shape'),
(1560, 'Triad Girdle shape'),
(1561, 'Guise of the Devourer shape'),
(1562, 'Ternary Mantle shape'),
(1563, 'Angelista''s Touch shape'),
(1564, 'Robes of the Triumvirate shape'),
(1565, 'Cape of the Trinity shape'),
(1566, 'Leggings of Immersion shape'),
(1567, 'Barrage Shoulders shape'),
(1568, 'Pendant of the Qiraji Guardian shape'),
(1569, 'Cloak of Concentrated Hatred shape'),
(1570, 'Hammer of Ji''zhi shape'),
(1571, 'Boots of the Redeemed Prophecy shape'),
(1572, 'Boots of the Fallen Prophet shape'),
(1573, 'Boots of the Unwavering Will shape'),
(1574, 'Ring of Swarming Thought shape'),
(1575, 'Beetle Scaled Wristguards shape'),
(1576, 'Ring of the Fallen God shape'),
(1577, 'Cloak of the Fallen God shape'),
(1578, 'Amulet of the Fallen God shape'),
(1579, 'Sand Polished Hammer shape'),
(1580, 'Band of Natural Fire shape'),
(1581, 'Blood Crown shape'),
(1582, 'Necklace of the Diamond Tower shape'),
(1583, 'Silithid Husked Launcher shape'),
(1584, 'Antenna of Invigoration shape'),
(1585, 'The Lost Kris of Zedd shape'),
(1586, 'Helm of the Holy Avenger shape'),
(1587, 'Coif of Elemental Fury shape'),
(1588, 'Polished Obsidian Pauldrons shape'),
(1589, 'Gavel of Qiraji Authority shape'),
(1590, 'Fury of the Forgotten Swarm shape'),
(1591, 'Treads of the Wandering Nomad shape'),
(1592, 'Breastplate of Annihilation shape'),
(1593, 'Ritssyn''s Ring of Chaos shape'),
(1594, 'Anubisath Warhammer shape'),
(1595, 'Garb of Royal Ascension shape'),
(1596, 'Scepter of the False Prophet shape'),
(1597, 'Neretzek, The Blood Drinker shape'),
(1598, 'Soulcloth Gloves shape'),
(1599, 'Soulcloth Shoulders shape'),
(1600, 'Soulcloth Vest shape'),
(1601, 'Gloves of the Immortal shape'),
(1602, 'Gloves of the Redeemed Prophecy shape'),
(1603, 'Gloves of the Fallen Prophet shape'),
(1604, 'Belt of Heroism shape'),
(1605, 'Boots of Heroism shape'),
(1606, 'Bracers of Heroism shape'),
(1607, 'Breastplate of Heroism shape'),
(1608, 'Gauntlets of Heroism shape'),
(1609, 'Helm of Heroism shape'),
(1610, 'Legplates of Heroism shape'),
(1611, 'Spaulders of Heroism shape'),
(1612, 'Darkmantle Belt shape'),
(1613, 'Darkmantle Boots shape'),
(1614, 'Darkmantle Bracers shape'),
(1615, 'Darkmantle Cap shape'),
(1616, 'Darkmantle Gloves shape'),
(1617, 'Darkmantle Pants shape'),
(1618, 'Darkmantle Spaulders shape'),
(1619, 'Darkmantle Tunic shape'),
(1620, 'Beastmaster''s Belt shape'),
(1621, 'Beastmaster''s Bindings shape'),
(1622, 'Beastmaster''s Cap shape'),
(1623, 'Beastmaster''s Gloves shape'),
(1624, 'Beastmaster''s Mantle shape'),
(1625, 'Beastmaster''s Pants shape'),
(1626, 'Beastmaster''s Tunic shape'),
(1627, 'Beastmaster''s Boots shape'),
(1628, 'Sorcerer''s Belt shape'),
(1629, 'Sorcerer''s Bindings shape'),
(1630, 'Sorcerer''s Boots shape'),
(1631, 'Sorcerer''s Crown shape'),
(1632, 'Sorcerer''s Gloves shape'),
(1633, 'Sorcerer''s Leggings shape'),
(1634, 'Sorcerer''s Mantle shape'),
(1635, 'Sorcerer''s Robes shape'),
(1636, 'Deathmist Belt shape'),
(1637, 'Deathmist Bracers shape'),
(1638, 'Deathmist Leggings shape'),
(1639, 'Deathmist Mantle shape'),
(1640, 'Deathmist Mask shape'),
(1641, 'Deathmist Robe shape'),
(1642, 'Deathmist Sandals shape'),
(1643, 'Deathmist Wraps shape'),
(1644, 'Virtuous Belt shape'),
(1645, 'Virtuous Bracers shape'),
(1646, 'Virtuous Crown shape'),
(1647, 'Virtuous Gloves shape'),
(1648, 'Virtuous Mantle shape'),
(1649, 'Virtuous Robe shape'),
(1650, 'Virtuous Sandals shape'),
(1651, 'Virtuous Skirt shape'),
(1652, 'Soulforge Belt shape'),
(1653, 'Soulforge Boots shape'),
(1654, 'Soulforge Bracers shape'),
(1655, 'Soulforge Breastplate shape'),
(1656, 'Soulforge Gauntlets shape'),
(1657, 'Soulforge Helm shape'),
(1658, 'Soulforge Legplates shape'),
(1659, 'Soulforge Spaulders shape'),
(1660, 'Bindings of The Five Thunders shape'),
(1661, 'Boots of The Five Thunders shape'),
(1662, 'Coif of The Five Thunders shape'),
(1663, 'Cord of The Five Thunders shape'),
(1664, 'Gauntlets of The Five Thunders shape'),
(1665, 'Kilt of The Five Thunders shape'),
(1666, 'Pauldrons of The Five Thunders shape'),
(1667, 'Vest of The Five Thunders shape'),
(1668, 'Feralheart Belt shape'),
(1669, 'Feralheart Boots shape'),
(1670, 'Feralheart Bracers shape'),
(1671, 'Feralheart Cowl shape'),
(1672, 'Feralheart Gloves shape'),
(1673, 'Feralheart Kilt shape'),
(1674, 'Feralheart Spaulders shape'),
(1675, 'Feralheart Vest shape'),
(1676, 'Beads of Ogre Mojo shape'),
(1677, 'Beads of Ogre Might shape'),
(1678, 'Obsidian Mail Tunic shape'),
(1679, 'Black Grasp of the Destroyer shape'),
(1680, 'Light Obsidian Belt shape'),
(1681, 'Thick Obsidian Breastplate shape'),
(1682, 'Heavy Obsidian Belt shape'),
(1683, 'Jagged Obsidian Shield shape'),
(1684, 'Wristguards of Renown shape'),
(1685, 'Sash of the Grand Hunt shape'),
(1686, 'Dragonskin Cowl shape'),
(1687, 'Kayser''s Boots of Precision shape'),
(1688, 'Marksman''s Girdle shape'),
(1689, 'Faith Healer''s Boots shape'),
(1690, 'Tome of the Lost shape'),
(1691, 'Spellweaver''s Turban shape'),
(1692, 'Shadow Prowler''s Cloak shape'),
(1693, 'Ironweave Robe shape'),
(1694, 'Ironweave Cowl shape'),
(1695, 'Ironweave Pants shape'),
(1696, 'Ironweave Gloves shape'),
(1697, 'Ironweave Mantle shape'),
(1698, 'Ironweave Belt shape'),
(1699, 'Ironweave Boots shape'),
(1700, 'Ironweave Bracers shape'),
(1701, 'Huntsman''s Harpoon shape'),
(1702, 'Hammer of Revitalization shape'),
(1703, 'Lefty''s Brass Knuckle shape'),
(1704, 'Tome of Divine Right shape'),
(1705, 'The Jaw Breaker shape'),
(1706, 'Belt of the Trickster shape'),
(1707, 'Amalgam''s Band shape'),
(1708, 'Amulet of the Redeemed shape'),
(1709, 'Legplates of Vigilance shape'),
(1710, 'Scepter of Interminable Focus shape'),
(1711, 'Shroud of Arcane Mastery shape'),
(1712, 'Band of the Steadfast Hero shape'),
(1713, 'Blade of Necromancy shape'),
(1714, 'Hammer of Divine Might shape'),
(1715, 'Band of Mending shape'),
(1716, 'Lord Valthalak''s Staff of Command shape'),
(1717, 'Draconian Aegis of the Legion shape'),
(1718, 'Shroud of Domination shape'),
(1719, 'Rune Band of Wizardry shape'),
(1720, 'Pendant of Celerity shape'),
(1721, 'Leggings of Torment shape'),
(1722, 'Handguards of Savagery shape'),
(1723, 'Fahrad''s Reloading Repeater shape'),
(1724, 'Doomulus Prime shape'),
(1725, 'The Thunderwood Poker shape'),
(1726, 'Shivsprocket''s Shiv shape'),
(1727, 'Simone''s Cultivating Hammer shape'),
(1728, 'Sageblade shape'),
(1729, 'Persuader shape'),
(1730, 'Titanic Leggings shape'),
(1731, 'Staff of Metanoia shape'),
(1732, 'Diana''s Pearl Necklace shape'),
(1733, 'Mantle of the Scarlet Crusade shape'),
(1734, 'Redemption shape'),
(1735, 'Helm of the New Moon shape'),
(1736, 'Ritssyn''s Wand of Bad Mojo shape'),
(1737, 'Tunic of the Crescent Moon shape'),
(1738, 'Gauntlets of Deftness shape'),
(1739, 'Helm of the Executioner shape'),
(1740, 'Thuzadin Mantle shape'),
(1741, 'Dreadnaught Breastplate shape'),
(1742, 'Dreadnaught Legplates shape'),
(1743, 'Dreadnaught Helmet shape'),
(1744, 'Dreadnaught Pauldrons shape'),
(1745, 'Dreadnaught Sabatons shape'),
(1746, 'Dreadnaught Gauntlets shape'),
(1747, 'Dreadnaught Waistguard shape'),
(1748, 'Dreadnaught Bracers shape'),
(1749, 'Redemption Wristguards shape'),
(1750, 'Redemption Tunic shape'),
(1751, 'Redemption Handguards shape'),
(1752, 'Redemption Legguards shape'),
(1753, 'Redemption Headpiece shape'),
(1754, 'Redemption Spaulders shape'),
(1755, 'Redemption Boots shape'),
(1756, 'Redemption Girdle shape'),
(1757, 'Don Mauricio''s Band of Domination shape'),
(1758, 'Cryptstalker Tunic shape'),
(1759, 'Cryptstalker Legguards shape'),
(1760, 'Cryptstalker Headpiece shape'),
(1761, 'Cryptstalker Spaulders shape'),
(1762, 'Cryptstalker Boots shape'),
(1763, 'Cryptstalker Handguards shape'),
(1764, 'Cryptstalker Girdle shape'),
(1765, 'Cryptstalker Wristguards shape'),
(1766, 'Earthshatter Tunic shape'),
(1767, 'Earthshatter Legguards shape'),
(1768, 'Earthshatter Headpiece shape'),
(1769, 'Earthshatter Spaulders shape'),
(1770, 'Earthshatter Boots shape'),
(1771, 'Earthshatter Handguards shape'),
(1772, 'Earthshatter Girdle shape'),
(1773, 'Earthshatter Wristguards shape'),
(1774, 'Boots of Ferocity shape'),
(1775, 'Bonescythe Breastplate shape'),
(1776, 'Bonescythe Legplates shape'),
(1777, 'Bonescythe Helmet shape'),
(1778, 'Bonescythe Pauldrons shape'),
(1779, 'Bonescythe Sabatons shape'),
(1780, 'Bonescythe Gauntlets shape'),
(1781, 'Bonescythe Waistguard shape'),
(1782, 'Bonescythe Bracers shape'),
(1783, 'Dreamwalker Tunic shape'),
(1784, 'Dreamwalker Legguards shape'),
(1785, 'Dreamwalker Headpiece shape'),
(1786, 'Dreamwalker Spaulders shape'),
(1787, 'Dreamwalker Boots shape'),
(1788, 'Dreamwalker Handguards shape'),
(1789, 'Dreamwalker Girdle shape'),
(1790, 'Dreamwalker Wristguards shape'),
(1791, 'Frostfire Robe shape'),
(1792, 'Frostfire Leggings shape'),
(1793, 'Frostfire Circlet shape'),
(1794, 'Frostfire Shoulderpads shape'),
(1795, 'Frostfire Sandals shape'),
(1796, 'Frostfire Gloves shape'),
(1797, 'Frostfire Belt shape'),
(1798, 'Frostfire Bindings shape'),
(1799, 'Plagueheart Robe shape'),
(1800, 'Plagueheart Leggings shape'),
(1801, 'Plagueheart Circlet shape'),
(1802, 'Plagueheart Shoulderpads shape'),
(1803, 'Plagueheart Sandals shape'),
(1804, 'Plagueheart Gloves shape'),
(1805, 'Plagueheart Belt shape'),
(1806, 'Plagueheart Bindings shape'),
(1807, 'Robe of Faith shape'),
(1808, 'Leggings of Faith shape'),
(1809, 'Circlet of Faith shape'),
(1810, 'Shoulderpads of Faith shape'),
(1811, 'Sandals of Faith shape'),
(1812, 'Gloves of Faith shape'),
(1813, 'Belt of Faith shape'),
(1814, 'Bindings of Faith shape'),
(1815, 'Outrider''s Plate Legguards shape'),
(1816, 'Glacial Vest shape'),
(1817, 'Glacial Gloves shape'),
(1818, 'Glacial Wrists shape'),
(1819, 'The Purifier shape'),
(1820, 'Amulet of the Dawn shape'),
(1821, 'Medallion of the Dawn shape'),
(1822, 'Polar Tunic shape'),
(1823, 'Polar Gloves shape'),
(1824, 'Polar Bracers shape'),
(1825, 'Bracers of Hope shape'),
(1826, 'Bracers of Subterfuge shape'),
(1827, 'Icebane Breastplate shape'),
(1828, 'Icebane Gauntlets shape'),
(1829, 'Icebane Bracers shape'),
(1830, 'Sentinel''s Plate Legguards shape'),
(1831, 'Outrider''s Chain Leggings shape'),
(1832, 'Outrider''s Mail Leggings shape'),
(1833, 'Band of Resolution shape'),
(1834, 'Band of Piety shape'),
(1835, 'Verimonde''s Last Resort shape'),
(1836, 'Sanctified Leather Helm shape'),
(1837, 'Leggings of the Plague Hunter shape'),
(1838, 'Icebane Leggings shape'),
(1839, 'Glacial Leggings shape'),
(1840, 'Polar Leggings shape'),
(1841, 'Icy Scale Leggings shape'),
(1842, 'Cloak of the Hakkari Worshippers shape'),
(1843, 'Zulian Scepter of Rites shape'),
(1844, 'Sacrificial Gauntlets shape'),
(1845, 'Gloves of the Tormented shape'),
(1846, 'Belt of Untapped Power shape'),
(1847, 'Blooddrenched Mask shape'),
(1848, 'Zulian Headdress shape'),
(1849, 'Band of Servitude shape'),
(1850, 'Eyestalk Waist Cord shape'),
(1851, 'Cloak of the Devoured shape'),
(1852, 'Mark of C''Thun shape'),
(1853, 'Outrider''s Leather Pants shape'),
(1854, 'Outrider''s Lizardhide Pants shape'),
(1855, 'Outrider''s Silk Leggings shape'),
(1856, 'Sentinel''s Chain Leggings shape'),
(1857, 'Sentinel''s Leather Pants shape'),
(1858, 'Sentinel''s Lizardhide Pants shape'),
(1859, 'Sentinel''s Silk Leggings shape'),
(1860, 'Sentinel''s Lamellar Legguards shape'),
(1861, 'Sylvan Vest shape'),
(1862, 'Sylvan Crown shape'),
(1863, 'Sylvan Shoulders shape'),
(1864, 'Ironvine Breastplate shape'),
(1865, 'Ironvine Gloves shape'),
(1866, 'Ironvine Belt shape'),
(1867, 'Might of Menethil shape'),
(1868, 'Soulseeker shape'),
(1869, 'Brimstone Staff shape'),
(1870, 'Spire of Twilight shape'),
(1871, 'Kingsfall shape'),
(1872, 'Midnight Haze shape'),
(1873, 'Maexxna''s Fang shape'),
(1874, 'Naxxramas Sword 1H 1 [PH] shape'),
(1875, 'Widow''s Remorse shape'),
(1876, 'Wraith Blade shape'),
(1877, 'The Castigator shape'),
(1878, 'Maul of the Redeemed Crusader shape'),
(1879, 'Soulstring shape'),
(1880, 'Nerubian Slavemaker shape'),
(1881, 'Naxxramas Sword 2H 2 [PH] shape'),
(1882, 'Severance shape'),
(1883, 'Hatchet of Sundered Bone shape'),
(1884, 'Naxxramas Polearm [PH] shape'),
(1885, 'The Plague Bearer shape'),
(1886, 'Shield of Condemnation shape'),
(1887, 'Wand of Fates shape'),
(1888, 'Doomfinger shape'),
(1889, 'Blood Guard''s Chain Greaves shape'),
(1890, 'Blood Guard''s Dragonhide Treads shape'),
(1891, 'Blood Guard''s Dreadweave Walkers shape'),
(1892, 'Blood Guard''s Mail Greaves shape'),
(1893, 'Blood Guard''s Plate Greaves shape'),
(1894, 'Blood Guard''s Satin Walkers shape'),
(1895, 'Blood Guard''s Silk Walkers shape'),
(1896, 'Blood Guard''s Chain Vices shape'),
(1897, 'Blood Guard''s Dragonhide Grips shape'),
(1898, 'Blood Guard''s Leather Grips shape'),
(1899, 'Blood Guard''s Dreadweave Handwraps shape'),
(1900, 'Blood Guard''s Mail Vices shape'),
(1901, 'Blood Guard''s Plate Gauntlets shape'),
(1902, 'Blood Guard''s Satin Handwraps shape'),
(1903, 'Blood Guard''s Silk Handwraps shape'),
(1904, 'Legionnaire''s Plate Hauberk shape'),
(1905, 'Legionnaire''s Plate Leggings shape'),
(1906, 'Legionnaire''s Chain Hauberk shape'),
(1907, 'Legionnaire''s Chain Legguards shape'),
(1908, 'Legionnaire''s Mail Hauberk shape'),
(1909, 'Legionnaire''s Dragonhide Chestpiece shape'),
(1910, 'Legionnaire''s Dragonhide Leggings shape'),
(1911, 'Legionnaire''s Leather Chestpiece shape'),
(1912, 'Legionnaire''s Leather Legguards shape'),
(1913, 'Legionnaire''s Dreadweave Legguards shape'),
(1914, 'Legionnaire''s Satin Legguards shape'),
(1915, 'Legionnaire''s Silk Legguards shape'),
(1916, 'Legionnaire''s Dreadweave Tunic shape'),
(1917, 'Legionnaire''s Satin Tunic shape'),
(1918, 'Legionnaire''s Silk Tunic shape'),
(1919, 'Legionnaire''s Mail Legguards shape'),
(1920, 'Wristguards of Vengeance shape'),
(1921, 'Gem of Nerubis shape'),
(1922, 'Cryptfiend Silk Cloak shape'),
(1923, 'Band of Unanswered Prayers shape'),
(1924, 'Icebane Pauldrons shape'),
(1925, 'The Widow''s Embrace shape'),
(1926, 'Malice Stone Pendant shape'),
(1927, 'Pendant of Forgotten Names shape'),
(1928, 'Cloak of Suturing shape'),
(1929, 'Band of Reanimation shape'),
(1930, 'Glacial Mantle shape'),
(1931, 'Gluth''s Missing Collar shape'),
(1932, 'Rime Covered Mantle shape'),
(1933, 'The End of Dreams shape'),
(1934, 'Digested Hand of Power shape'),
(1935, 'Plated Abomination Ribcage shape'),
(1936, 'Wand of the Whispering Dead shape'),
(1937, 'Iblis, Blade of the Fallen Seraph shape'),
(1938, 'Veil of Eclipse shape'),
(1939, 'Signet of the Fallen Defender shape'),
(1940, 'Icebane Helmet shape'),
(1941, 'Polar Helmet shape'),
(1942, 'The Soul Harvester''s Bindings shape'),
(1943, 'Sadist''s Collar shape'),
(1944, 'Seal of the Damned shape'),
(1945, 'Hailstone Band shape'),
(1946, 'Noth''s Frigid Heart shape'),
(1947, 'Cloak of the Scourge shape'),
(1948, 'Band of the Inevitable shape'),
(1949, 'Glacial Headdress shape'),
(1950, 'Icy Scale Coif shape'),
(1951, 'Nax PH Crit Plate Shoulders shape'),
(1952, 'Preceptor''s Hat shape'),
(1953, 'Necklace of Necropsy shape'),
(1954, 'Ring of Spiritual Fervor shape'),
(1955, 'Band of Unnatural Forces shape'),
(1956, 'The Eye of Nerub shape'),
(1957, 'The Face of Death shape'),
(1958, 'Harbinger of Doom shape'),
(1959, 'Shroud of Dominion shape'),
(1960, 'Sapphiron''s Right Eye shape'),
(1961, 'Sapphiron''s Left Eye shape'),
(1962, 'Cloak of the Necropolis shape'),
(1963, 'Stormrage''s Talisman of Seething shape'),
(1964, 'Hammer of the Twisting Nether shape'),
(1965, 'Gem of Trapped Innocents shape'),
(1966, 'Life Channeling Necklace shape'),
(1967, 'Ring of the Dreadnaught shape'),
(1968, 'Bonescythe Ring shape'),
(1969, 'Ring of Faith shape'),
(1970, 'Frostfire Ring shape'),
(1971, 'Plagueheart Ring shape'),
(1972, 'Ring of the Dreamwalker shape'),
(1973, 'Ring of the Earthshatterer shape'),
(1974, 'Ring of Redemption shape'),
(1975, 'Ring of the Cryptstalker shape'),
(1976, 'Legplates of Carnage shape'),
(1977, 'Necro-Knight''s Garb shape'),
(1978, 'Leggings of Polarity shape'),
(1979, 'Leggings of Apocalypse shape'),
(1980, 'Fists of the Unrelenting shape'),
(1981, 'Boots of Displacement shape'),
(1982, 'Death''s Bargain shape'),
(1983, 'Gloves of Undead Cleansing shape'),
(1984, 'Robe of Undead Cleansing shape'),
(1985, 'Bracers of Undead Cleansing shape'),
(1986, 'Staff of Balzaphon shape'),
(1987, 'Chains of the Lich shape'),
(1988, 'Waistband of Balzaphon shape'),
(1989, 'Cloak of Revanchion shape'),
(1990, 'The Shadow''s Grasp shape'),
(1991, 'Bracers of Mending shape'),
(1992, 'Blackwood''s Thigh shape'),
(1993, 'Girdle of the Mentor shape'),
(1994, 'Crystal Webbed Robe shape'),
(1995, 'Ghoul Skin Tunic shape'),
(1996, 'Ring of the Eternal Flame shape'),
(1997, 'Claw of the Frost Wyrm shape'),
(1998, 'Champion''s Plate Shoulders shape'),
(1999, 'Champion''s Plate Helm shape'),
(2000, 'Champion''s Chain Helm shape'),
(2001, 'Champion''s Chain Shoulders shape'),
(2002, 'Champion''s Dragonhide Headguard shape'),
(2003, 'Champion''s Dragonhide Shoulders shape'),
(2004, 'Champion''s Dreadweave Cowl shape'),
(2005, 'Champion''s Dreadweave Spaulders shape'),
(2006, 'Champion''s Leather Helm shape'),
(2007, 'Champion''s Leather Shoulders shape'),
(2008, 'Champion''s Mail Headguard shape'),
(2009, 'Champion''s Mail Pauldrons shape'),
(2010, 'Champion''s Satin Hood shape'),
(2011, 'Champion''s Satin Mantle shape'),
(2012, 'Champion''s Silk Cowl shape'),
(2013, 'Champion''s Silk Mantle shape'),
(2014, 'Knight-Captain''s Lamellar Breastplate shape'),
(2015, 'Knight-Captain''s Lamellar Leggings shape'),
(2016, 'Knight-Lieutenant''s Lamellar Gauntlets shape'),
(2017, 'Knight-Lieutenant''s Lamellar Sabatons shape'),
(2018, 'Lieutenant Commander''s Lamellar Headguard shape'),
(2019, 'Lieutenant Commander''s Lamellar Shoulders shape'),
(2020, 'Knight-Lieutenant''s Chain Greaves shape'),
(2021, 'Knight-Lieutenant''s Chain Vices shape'),
(2022, 'Knight-Lieutenant''s Dragonhide Grips shape'),
(2023, 'Knight-Lieutenant''s Dragonhide Treads shape'),
(2024, 'Knight-Lieutenant''s Dreadweave Handwraps shape'),
(2025, 'Knight-Lieutenant''s Dreadweave Walkers shape'),
(2026, 'Knight-Lieutenant''s Leather Grips shape'),
(2027, 'Knight-Lieutenant''s Plate Gauntlets shape'),
(2028, 'Knight-Lieutenant''s Plate Greaves shape'),
(2029, 'Knight-Lieutenant''s Satin Handwraps shape'),
(2030, 'Knight-Lieutenant''s Satin Walkers shape'),
(2031, 'Knight-Lieutenant''s Silk Handwraps shape'),
(2032, 'Knight-Lieutenant''s Silk Walkers shape'),
(2033, 'Knight-Captain''s Chain Hauberk shape'),
(2034, 'Knight-Captain''s Chain Legguards shape'),
(2035, 'Knight-Captain''s Dragonhide Chestpiece shape'),
(2036, 'Knight-Captain''s Dragonhide Leggings shape'),
(2037, 'Knight-Captain''s Dreadweave Legguards shape'),
(2038, 'Knight-Captain''s Dreadweave Tunic shape'),
(2039, 'Knight-Captain''s Leather Chestpiece shape'),
(2040, 'Knight-Captain''s Leather Legguards shape'),
(2041, 'Knight-Captain''s Plate Hauberk shape'),
(2042, 'Knight-Captain''s Plate Leggings shape'),
(2043, 'Knight-Captain''s Satin Legguards shape'),
(2044, 'Knight-Captain''s Satin Tunic shape'),
(2045, 'Knight-Captain''s Silk Legguards shape'),
(2046, 'Knight-Captain''s Silk Tunic shape'),
(2047, 'Lieutenant Commander''s Chain Helm shape'),
(2048, 'Lieutenant Commander''s Chain Shoulders shape'),
(2049, 'Lieutenant Commander''s Dragonhide Headguard shape'),
(2050, 'Lieutenant Commander''s Dragonhide Shoulders shape'),
(2051, 'Lieutenant Commander''s Dreadweave Cowl shape'),
(2052, 'Lieutenant Commander''s Dreadweave Spaulders shape'),
(2053, 'Lieutenant Commander''s Leather Helm shape'),
(2054, 'Lieutenant Commander''s Leather Shoulders shape'),
(2055, 'Lieutenant Commander''s Plate Helmet shape'),
(2056, 'Lieutenant Commander''s Plate Shoulders shape'),
(2057, 'Lieutenant Commander''s Satin Hood shape'),
(2058, 'Lieutenant Commander''s Satin Mantle shape'),
(2059, 'Lieutenant Commander''s Silk Cowl shape'),
(2060, 'Lieutenant Commander''s Silk Mantle shape'),
(2061, 'Hammer of the Sun shape'),
(2062, 'Titanic Breastplate shape'),
(2063, 'Grand Marshal''s Mageblade shape'),
(2064, 'Grand Marshal''s Tome of Power shape'),
(2065, 'Grand Marshal''s Tome of Restoration shape'),
(2066, 'Grand Marshal''s Warhammer shape'),
(2067, 'Grand Marshal''s Demolisher shape'),
(2068, 'Grand Marshal''s Swiftblade shape'),
(2069, 'High Warlord''s Destroyer shape'),
(2070, 'High Warlord''s Spellblade shape'),
(2071, 'High Warlord''s Battle Mace shape'),
(2072, 'High Warlord''s Quickblade shape'),
(2073, 'High Warlord''s Tome of Destruction shape'),
(2074, 'High Warlord''s Battle Mace shape'),
(2075, 'High Warlord''s Destroyer shape'),
(2076, 'High Warlord''s Spellblade shape'),
(2077, 'High Warlord''s Quickblade shape'),
(2078, 'High Warlord''s Tome of Destruction shape'),
(2079, 'High Warlord''s Tome of Mending shape'),
(2080, 'Larvae of the Great Worm shape'),
(2081, 'The Hungering Cold shape'),
(2082, 'Girdle of Elemental Fury shape'),
(2083, 'Pauldrons of Elemental Fury shape'),
(2084, 'Leggings of Elemental Fury shape'),
(2085, 'Belt of the Grand Crusader shape'),
(2086, 'Spaulders of the Grand Crusader shape'),
(2087, 'Leggings of the Grand Crusader shape'),
(2088, 'Power Amplification Goggles shape'),
(2089, 'Gnomish Power Goggles shape'),
(2090, 'Gnomish Battle Goggles shape'),
(2091, 'Foreman''s Enchanted Helmet shape'),
(2092, 'Foreman''s Reinforced Helmet shape'),
(2093, 'Shadowrend Longblade shape'),
(2094, 'Light-Touched Breastplate shape'),
(2095, 'Scale Leggings of the Skirmisher shape'),
(2096, 'Bracers of Finesse shape'),
(2097, 'Pauldrons of Arcane Rage shape'),
(2098, 'Hellreaver shape'),
(2099, 'Band of Renewal shape'),
(2100, 'Kilt of Rolling Thunders shape'),
(2101, 'Shifting Sash of Midnight shape'),
(2102, 'Ironsole Clompers shape'),
(2103, 'Crystalfire Staff shape'),
(2104, 'Garrote-String Necklace shape'),
(2105, 'Lifegiver Britches shape'),
(2106, 'Bloodstained Ravager Gauntlets shape'),
(2107, 'Tenacious Defender shape'),
(2108, 'Heart Fire Warhammer shape'),
(2109, 'Heartblood Prayer Beads shape'),
(2110, 'Coronet of Verdant Flame shape'),
(2111, 'Circlet of Arcane Might shape'),
(2112, 'PH Plate Ramparts Reward shape'),
(2113, 'Witching Band shape'),
(2114, 'Ursol''s Claw shape'),
(2115, 'Wastewalker Shiv shape'),
(2116, 'Vest of Living Lightning shape'),
(2117, 'Princely Reign Leggings shape'),
(2118, 'Tracker''s Belt shape'),
(2119, 'Spellfire Longsword shape'),
(2120, 'Spore-Soaked Vaneer shape'),
(2121, 'Unscarred Breastplate shape'),
(2122, 'Azureplate Greaves shape'),
(2123, 'Deft Handguards shape'),
(2124, 'Scorpid-Sting Mantle shape'),
(2125, 'Coilfang Hammer of Renewal shape'),
(2126, 'Bogstrok Scale Cloak shape'),
(2127, 'Calming Spore Reed shape'),
(2128, 'Coilfang Needler shape'),
(2129, 'Diamond-Core Sledgemace shape'),
(2130, 'Pendant of Battle-Lust shape'),
(2131, 'Ironblade Gauntlets shape'),
(2132, 'Girdle of the Gale Storm shape'),
(2133, 'Legion Blunderbuss shape'),
(2134, 'Kilt of the Night Strider shape'),
(2135, 'Arcing Bracers shape'),
(2136, 'Bloody Surgeon''s Mitts shape'),
(2137, 'Mindfire Waistband shape'),
(2138, 'Vest of Vengeance shape'),
(2139, 'Raiments of Divine Authority shape'),
(2140, 'Mantle of the Dusk-Dweller shape'),
(2141, 'Manaspark Gloves shape'),
(2142, 'Lykul Bloodbands shape'),
(2143, 'Starlight Gauntlets shape'),
(2144, 'Zangartooth Shortblade shape'),
(2145, 'Cloak of Enduring Swiftness shape'),
(2146, 'Tunic of the Nightwatcher shape'),
(2147, 'Greaves of the Iron Guardian shape'),
(2148, 'Truth Bearer Shoulderguards shape'),
(2149, 'Studded Girdle of Virtue shape'),
(2150, 'Cloak of Healing Rays shape'),
(2151, 'Hatebringer shape'),
(2152, 'Luminous Pearls of Insight shape'),
(2153, 'Pauldrons of Brute Force shape'),
(2154, 'The Stalker''s Fangs shape'),
(2155, 'Shamblehide Chestguard shape'),
(2156, 'Skulldugger''s Leggings shape'),
(2157, 'Robes of the Augurer shape'),
(2158, 'Sporeggar Smasher shape'),
(2159, 'Hewing Axe of the Marsh shape'),
(2160, 'Sporeling Claw shape'),
(2161, 'Dark Cloak of the Marsh shape'),
(2162, 'Cenarion Ring of Casting shape'),
(2163, 'Earthen Mark of Razing shape'),
(2164, 'Earthen Mark of Power shape'),
(2165, 'Earthen Mark of Health shape'),
(2166, 'Lantresor''s Warblade shape'),
(2167, 'Burning Blade Devotee''s Cinch shape'),
(2168, 'Burning Blade Cultist Band shape'),
(2169, 'Burning Blade Cultist Band shape'),
(2170, 'Lantresor''s Warblade shape'),
(2171, 'Burning Blade Devotee''s Cinch shape'),
(2172, 'Netherfury Boots shape'),
(2173, 'Breastplate of Retribution shape'),
(2174, 'Scaled Legs of Ruination shape'),
(2175, 'Moonkin Headdress shape'),
(2176, 'Deadly Borer Leggings shape'),
(2177, 'Perfectly Balanced Cape shape'),
(2178, 'Holy Healing Band shape'),
(2179, 'Crimson Pendant of Clarity shape'),
(2180, 'Jade Warrior Pauldrons shape'),
(2181, 'Handguards of Precision shape'),
(2182, 'Sure-Step Boots shape'),
(2183, 'Mantle of Magical Might shape'),
(2184, 'Crystalline Kopesh shape'),
(2185, 'Hungering Bone Cudgel shape'),
(2186, 'Azure Lightblade shape'),
(2187, 'Ogre Slayer''s Band shape'),
(2188, 'Ogre Slayer''s Pendant shape'),
(2189, 'Ogre Slayer''s Cover shape'),
(2190, 'Grunt''s Waraxe shape'),
(2191, 'Farseer''s Band shape'),
(2192, 'Footman''s Longsword shape'),
(2193, 'Sage''s Band shape'),
(2194, 'Petrified Lichen Guard shape'),
(2195, 'Preserver''s Cudgel shape'),
(2196, 'Warden''s Hauberk shape'),
(2197, 'Voidfire Wand shape'),
(2198, 'Boots of the Outlander shape'),
(2199, 'Faith Bearer''s Gauntlets shape'),
(2200, 'Creepjacker shape'),
(2201, 'Shaarde the Greater shape'),
(2202, 'Cloak of Revival shape'),
(2203, 'Nethershade Boots shape'),
(2204, 'Lightning-Rod Pauldrons shape'),
(2205, 'Staff of Polarities shape'),
(2206, 'Scimitar of the Nexus-Stalkers shape'),
(2207, 'Ethereal Warp-Bow shape'),
(2208, 'Sigil of Shaffar shape'),
(2209, 'Mask of the Howling Storm shape'),
(2210, 'Nexus-Bracers of Vigor shape'),
(2211, 'Ethereal Boots of the Skystrider shape'),
(2212, 'Longstrider''s Loop shape'),
(2213, 'Shaarde the Lesser shape'),
(2214, 'Eagle Crested Pauldrons shape'),
(2215, 'Shalassi Sentry''s Epaulets shape'),
(2216, 'Rapscallion''s Touch shape'),
(2217, 'Shalassi Oracle''s Sandals shape'),
(2218, 'Hope Bearer Helm shape'),
(2219, 'Raven-Heart Headdress shape'),
(2220, 'Collar of Command shape'),
(2221, 'Slippers of Serenity shape'),
(2222, 'Ironstaff of Regeneration shape'),
(2223, 'Ring of the Exarchs shape'),
(2224, 'Mok''Nathal Beast-Mask shape'),
(2225, 'Darkguard Face Mask shape'),
(2226, 'Needle Shrike shape'),
(2227, 'Shadowstalker''s Sash shape'),
(2228, 'Hierophant''s Sash shape'),
(2229, 'Slayer''s Waistguard shape'),
(2230, 'Stormbreaker''s Girdle shape'),
(2231, 'Avenger''s Waistguard shape'),
(2232, 'Dreamstalker Sash shape'),
(2233, 'Marksman''s Belt shape'),
(2234, 'Marksman''s Legguards shape'),
(2235, 'Dreamstalker Leggings shape'),
(2236, 'Hierophant''s Leggings shape'),
(2237, 'Shadowstalker''s Leggings shape'),
(2238, 'Stormbreaker''s Leggings shape'),
(2239, 'Slayer''s Leggings shape'),
(2240, 'Avenger''s Legplates shape'),
(2241, 'Circlet of the Victor shape'),
(2242, 'Band of the Victor shape'),
(2243, 'Band of the Victor shape'),
(2244, 'Circlet of the Victor shape'),
(2245, 'Terminal Edge shape'),
(2246, 'Terminal Edge shape'),
(2247, 'Splintermark shape'),
(2248, 'Splintermark shape'),
(2249, 'Incendic Rod shape'),
(2250, 'Incendic Rod shape'),
(2251, 'Goldenvine Wraps shape'),
(2252, 'Spell-slinger''s Protector shape'),
(2253, 'Nomad''s Woven Cloak shape'),
(2254, 'Delicate Green Poncho shape'),
(2255, 'Sacred Feather Vest shape'),
(2256, 'Jerkin of the Untamed Spirit shape'),
(2257, 'Goldweave Tunic shape'),
(2258, 'Fleshripper''s Bladed Chestplate shape'),
(2259, 'Gilded Crimson Chestplate shape'),
(2260, 'Bonechewer Berserker''s Vest shape'),
(2261, 'Golden Cenarion Greaves shape'),
(2262, 'Verdant Handwraps shape'),
(2263, 'Studded Green Anklewraps shape'),
(2264, 'Destroyers'' Mantle shape'),
(2265, 'Shield of the Void shape'),
(2266, 'Band of Triumph shape'),
(2267, 'Band of Dominance shape'),
(2268, 'Band of the Exorcist shape'),
(2269, 'Seal of the Exorcist shape'),
(2270, 'Exorcist''s Plate Helm shape'),
(2271, 'Exorcist''s Lamellar Helm shape'),
(2272, 'Exorcist''s Leather Helm shape'),
(2273, 'Exorcist''s Dragonhide Helm shape'),
(2274, 'Exorcist''s Wyrmhide Helm shape'),
(2275, 'Exorcist''s Chain Helm shape'),
(2276, 'Exorcist''s Linked Helm shape'),
(2277, 'Exorcist''s Mail Helm shape'),
(2278, 'Exorcist''s Dreadweave Hood shape'),
(2279, 'Exorcist''s Silk Hood shape'),
(2280, 'Exorcist''s Scaled Helm shape'),
(2281, 'Flightblade Throwing Axe shape'),
(2282, 'Guile of Khoraazi shape'),
(2283, 'Vindicator''s Brand shape'),
(2284, 'Retainer''s Blade shape'),
(2285, 'Sporeling''s Firestick shape'),
(2286, 'Hardened Stone Shard shape'),
(2287, 'Veteran''s Musket shape'),
(2288, 'Marksman''s Bow shape'),
(2289, 'Blade of the Archmage shape'),
(2290, 'Stormcaller shape'),
(2291, 'Honor''s Call shape'),
(2292, 'Warbringer shape'),
(2293, 'Earthwarden shape'),
(2294, 'Gavel of Pure Light shape'),
(2295, 'Riftmaker shape'),
(2296, 'Assassin''s Throwing Axe shape'),
(2297, 'Cover of Righteous Fury shape'),
(2298, 'Earthbreaker''s Greaves shape'),
(2299, 'Leggings of the Third Coin shape'),
(2300, 'Gloves of Penitence shape'),
(2301, 'Flesh Beast''s Metal Greaves shape'),
(2302, 'Consortium Mantle of Phasing shape'),
(2303, 'Cryo-mitts shape'),
(2304, 'Consortium Prince''s Wrap shape'),
(2305, 'The Exarch''s Protector shape'),
(2306, 'Auchenai Tracker''s Hauberk shape'),
(2307, 'Auchenai Monk''s Tunic shape'),
(2308, 'Auchenai Anchorite''s Robe shape'),
(2309, 'Consortium Plated Legguards shape'),
(2310, 'Haramad''s Leggings of the Third Coin shape'),
(2311, 'Haramad''s Linked Chain Pantaloons shape'),
(2312, 'Haramad''s Leg Wraps shape'),
(2313, 'Gift of the Ethereal shape'),
(2314, 'Nethershard shape'),
(2315, 'Knight-Lieutenant''s Mail Greaves shape'),
(2316, 'Knight-Lieutenant''s Mail Vices shape'),
(2317, 'Knight-Captain''s Mail Hauberk shape'),
(2318, 'Knight-Captain''s Mail Legguards shape'),
(2319, 'Lieutenant Commander''s Mail Headguard shape'),
(2320, 'Lieutenant Commander''s Mail Pauldrons shape'),
(2321, 'Blood Guard''s Lamellar Gauntlets shape'),
(2322, 'Blood Guard''s Lamellar Sabatons shape'),
(2323, 'Legionnaire''s Lamellar Breastplate shape'),
(2324, 'Legionnaire''s Lamellar Leggings shape'),
(2325, 'Champion''s Lamellar Headguard shape'),
(2326, 'Champion''s Lamellar Shoulders shape'),
(2327, 'Marshal''s Mail Boots shape'),
(2328, 'Marshal''s Mail Gauntlets shape'),
(2329, 'Marshal''s Mail Leggings shape'),
(2330, 'Field Marshal''s Mail Armor shape'),
(2331, 'Field Marshal''s Mail Helm shape'),
(2332, 'Field Marshal''s Mail Spaulders shape'),
(2333, 'General''s Lamellar Boots shape'),
(2334, 'General''s Lamellar Gloves shape'),
(2335, 'General''s Lamellar Legplates shape'),
(2336, 'Warlord''s Lamellar Chestplate shape'),
(2337, 'Warlord''s Lamellar Faceguard shape'),
(2338, 'Warlord''s Lamellar Pauldrons shape'),
(2339, 'Primalstorm Breastplate shape'),
(2340, 'Living Crystal Breastplate shape'),
(2341, 'Golden Dragonstrike Breastplate shape'),
(2342, 'Heavy Earthforged Breastplate shape'),
(2343, 'Stormforged Hauberk shape'),
(2344, 'Windforged Rapier shape'),
(2345, 'Stoneforged Claymore shape'),
(2346, 'Stormforged Axe shape'),
(2347, 'Skyforged Great Axe shape'),
(2348, 'Sentinel''s Mail Leggings shape'),
(2349, 'Outrider''s Lamellar Legguards shape'),
(2350, 'Trident of the Outcast Tribe shape'),
(2351, 'Gavel of Unearthed Secrets shape'),
(2352, 'Shapeshifter''s Signet shape'),
(2353, 'Boots of the Decimator shape'),
(2354, 'Gloves of Ferocity shape'),
(2355, 'Hauberk of Totemic Rage shape'),
(2356, 'Sash of Silent Blades shape'),
(2357, 'Leggings of Concentrated Darkness shape'),
(2358, 'Blade of Misfortune shape'),
(2359, 'Breastplate of Blade Turning shape'),
(2360, 'Gauntlets of Purification shape'),
(2361, 'Storm Lord''s Girdle shape'),
(2362, 'Fist of Reckoning shape'),
(2363, 'Cloak of Entropy shape'),
(2364, 'Blade of Trapped Knowledge shape'),
(2365, 'Shroud of Frenzy shape'),
(2366, 'Headdress of the Sleeper shape'),
(2367, 'Pendant of Cunning shape'),
(2368, 'Demon Hide Spaulders shape'),
(2369, 'Gloves of Pandemonium shape'),
(2370, 'Gloves of Piety shape'),
(2371, 'Girdle of Siege shape'),
(2372, 'Chestguard of Illumination shape'),
(2373, 'Axe of the Legion shape'),
(2374, 'Boots of Savagery shape'),
(2375, 'Amulet of Unstable Power shape'),
(2376, 'Gauntlets of the Skullsplitter shape'),
(2377, 'Boots of the Pathfinder shape'),
(2378, 'The Dreamer''s Shoulderpads shape'),
(2379, 'Amulet of Sanctification shape'),
(2380, 'Shield of the Wayward Footman shape'),
(2381, 'Girdle of Divine Blessing shape'),
(2382, 'Headdress of Inner Rage shape'),
(2383, 'Leggings of the Sly shape'),
(2384, 'Abyss Walker''s Boots shape'),
(2385, 'Band of Impenetrable Defenses shape'),
(2386, 'Chestguard of Exile shape'),
(2387, 'Choker of Repentance shape'),
(2388, 'The Hammer of Destiny shape'),
(2389, 'Truestrike Ring shape'),
(2390, 'Leggings of Beast Mastery shape'),
(2391, 'Lifegiving Cloak shape'),
(2392, 'Lightning Crown shape'),
(2393, 'The Night Watchman shape'),
(2394, 'Staff of Natural Fury shape'),
(2395, 'Pants of Living Growth shape'),
(2396, 'Blade of Wizardry shape'),
(2397, 'Charlotte''s Ivy shape'),
(2398, 'Lola''s Eve shape'),
(2399, 'Will of Edward the Odd shape'),
(2400, 'The Ancient Scepter of Sue-Min shape'),
(2401, 'Kamaei''s Cerulean Skirt shape'),
(2402, 'Iceguard Helm shape'),
(2403, 'Shadowcast Tunic shape'),
(2404, 'Darkstorm Tunic shape'),
(2405, 'Stormstrike Vest shape'),
(2406, 'Battlemaster''s Breastplate shape'),
(2407, 'Necklace of Bloodied Feathers shape'),
(2408, 'Choker of Bloodied Feathers shape'),
(2409, 'Dib''Muad''s Crysknife shape'),
(2410, 'Revered Mother''s Crysknife shape'),
(2411, 'Shani''s Crysknife shape'),
(2412, 'Nexus-Prince''s Ring of Balance shape'),
(2413, 'Shaffar''s Band of Brutality shape'),
(2414, 'Yor''s Collapsing Band shape'),
(2415, 'Ring of Conflict Survival shape'),
(2416, 'Band of the Crystalline Void shape'),
(2417, 'Yor''s Revenge shape'),
(2418, 'Necklace of the Deep shape'),
(2419, 'Crystalline Crossbow shape'),
(2420, 'Brilliant Pearl Band shape'),
(2421, 'The Black Pearl shape'),
(2422, 'Spinesever shape'),
(2423, 'Massacre Sword shape'),
(2424, 'Greatsword of the Ebon Blade shape'),
(2425, 'Greataxe of the Ebon Blade shape'),
(2426, 'Greathelm of the Scourge Champion shape'),
(2427, 'Bladed Ebon Amulet shape'),
(2428, 'Blood-soaked Saronite Plated Spaulders shape'),
(2429, 'Sky Darkener''s Shroud of the Unholy shape'),
(2430, 'Saronite War Plate shape'),
(2431, 'Plated Saronite Bracers shape'),
(2432, 'Bloodbane''s Gauntlets of Command shape'),
(2433, 'The Plaguebringer''s Girdle shape'),
(2434, 'Engraved Saronite Legplates shape'),
(2435, 'Greaves of the Slaughter shape'),
(2436, 'Valanar''s Signet Ring shape'),
(2437, 'Keleseth''s Signet Ring shape'),
(2438, 'Runed Soulblade shape'),
(2439, 'Sky Darkener''s Shroud of Blood shape'),
(2440, 'Shroud of the North Wind shape'),
(2441, 'Keleseth''s Persuader shape'),
(2442, 'Staff of the Shadow Flame (Purple Enchant) shape'),
(2443, 'Hellfire Tome shape'),
(2444, 'Book of Clever Tricks shape');

DELETE FROM `item_budget_assign` WHERE `entry` IN (
  944, 1443, 2243, 2801, 5267, 9402, 11924, 11928, 11930, 12103, 12344, 12543, 12544, 12545, 12548,
  12584, 12587, 12589, 12602, 12603, 12604, 12606, 12618, 12619, 12620, 12633, 12634, 12636, 12637, 12639,
  12640, 12641, 12752, 12756, 12757, 12783, 12796, 12895, 12903, 12926, 12927, 12929, 12935, 12936, 12939,
  12940, 12945, 12952, 12960, 12963, 12964, 12965, 12966, 12967, 12968, 13000, 13001, 13006, 13015, 13023,
  13028, 13072, 13075, 13080, 13083, 13090, 13092, 13096, 13098, 13107, 13113, 13116, 13123, 13133, 13141,
  13142, 13161, 13162, 13163, 13167, 13168, 13169, 13170, 13177, 13178, 13179, 13184, 13185, 13204, 13205,
  13206, 13208, 13211, 13244, 13249, 13252, 13253, 13259, 13260, 13314, 13340, 13344, 13345, 13346, 13349,
  13353, 13358, 13360, 13369, 13372, 13373, 13374, 13381, 13385, 13388, 13389, 13390, 13391, 13392, 13397,
  13398, 13498, 13502, 13936, 13937, 13938, 13944, 13950, 13951, 13954, 13955, 13956, 13957, 13958, 13959,
  13960, 13961, 13962, 13963, 13964, 13967, 13969, 13986, 14002, 14138, 14139, 14140, 14146, 14152, 14153,
  14154, 14340, 14502, 14503, 14522, 14525, 14528, 14536, 14538, 14539, 14543, 14545, 14548, 14553, 14554,
  14558, 14577, 14611, 14612, 14614, 14615, 14616, 14620, 14621, 14622, 14623, 14624, 14626, 14629, 14631,
  14632, 14633, 14637, 15047, 15051, 15052, 15059, 15062, 15141, 15411, 15413, 15421, 15805, 15806, 15854,
  15856, 16007, 16058, 16335, 16337, 16345, 16367, 16369, 16370, 16391, 16392, 16393, 16394, 16395, 16396,
  16397, 16398, 16399, 16400, 16401, 16402, 16403, 16404, 16405, 16406, 16407, 16409, 16410, 16411, 16412,
  16413, 16414, 16415, 16416, 16417, 16418, 16419, 16420, 16421, 16422, 16423, 16424, 16425, 16426, 16427,
  16428, 16429, 16430, 16431, 16432, 16433, 16434, 16435, 16436, 16437, 16438, 16439, 16440, 16441, 16442,
  16443, 16444, 16445, 16446, 16447, 16448, 16449, 16450, 16451, 16452, 16453, 16454, 16455, 16456, 16457,
  16458, 16459, 16460, 16461, 16462, 16463, 16464, 16465, 16466, 16467, 16468, 16469, 16470, 16471, 16472,
  16473, 16474, 16475, 16476, 16477, 16478, 16479, 16480, 16481, 16482, 16483, 16484, 16485, 16486, 16487,
  16488, 16489, 16490, 16491, 16492, 16493, 16494, 16495, 16496, 16497, 16498, 16499, 16500, 16501, 16502,
  16503, 16504, 16505, 16506, 16507, 16508, 16509, 16510, 16511, 16512, 16513, 16514, 16515, 16516, 16517,
  16518, 16519, 16520, 16521, 16522, 16523, 16524, 16525, 16526, 16527, 16528, 16529, 16530, 16531, 16532,
  16533, 16534, 16535, 16536, 16537, 16538, 16539, 16540, 16541, 16542, 16543, 16544, 16545, 16546, 16547,
  16548, 16549, 16550, 16551, 16552, 16553, 16554, 16555, 16556, 16557, 16558, 16559, 16560, 16561, 16562,
  16563, 16564, 16565, 16566, 16567, 16568, 16569, 16570, 16571, 16572, 16573, 16574, 16575, 16576, 16577,
  16578, 16579, 16580, 16666, 16667, 16668, 16669, 16674, 16677, 16678, 16679, 16686, 16687, 16688, 16689,
  16690, 16693, 16694, 16695, 16698, 16699, 16700, 16701, 16706, 16707, 16708, 16709, 16718, 16719, 16720,
  16721, 16726, 16727, 16728, 16729, 16730, 16731, 16732, 16733, 16818, 16832, 16897, 16898, 16899, 16900,
  16901, 16902, 16903, 16904, 16905, 16906, 16907, 16908, 16909, 16910, 16911, 16912, 16913, 16914, 16915,
  16916, 16917, 16918, 16919, 16920, 16921, 16922, 16923, 16924, 16925, 16926, 16927, 16928, 16929, 16930,
  16931, 16932, 16933, 16934, 16935, 16936, 16937, 16938, 16939, 16940, 16941, 16942, 16943, 16944, 16945,
  16946, 16947, 16948, 16949, 16950, 16951, 16952, 16953, 16954, 16955, 16956, 16957, 16958, 16959, 16960,
  16961, 16962, 16963, 16964, 16965, 16966, 16979, 16980, 16983, 16988, 16996, 16997, 16998, 17016, 17045,
  17063, 17065, 17066, 17067, 17069, 17070, 17072, 17076, 17077, 17078, 17102, 17103, 17105, 17106, 17107,
  17108, 17109, 17110, 17111, 17113, 17562, 17563, 17564, 17565, 17566, 17567, 17568, 17569, 17570, 17571,
  17572, 17573, 17574, 17575, 17576, 17577, 17578, 17579, 17580, 17581, 17582, 17583, 17584, 17585, 17586,
  17587, 17588, 17589, 17590, 17591, 17592, 17593, 17594, 17595, 17596, 17597, 17598, 17599, 17600, 17601,
  17602, 17603, 17604, 17605, 17606, 17607, 17608, 17609, 17610, 17611, 17612, 17613, 17614, 17615, 17616,
  17617, 17618, 17619, 17620, 17621, 17622, 17623, 17624, 17625, 18022, 18047, 18048, 18102, 18103, 18104,
  18202, 18203, 18205, 18208, 18263, 18282, 18366, 18367, 18368, 18369, 18372, 18373, 18374, 18375, 18376,
  18377, 18378, 18379, 18380, 18381, 18383, 18384, 18385, 18386, 18387, 18388, 18389, 18390, 18391, 18392,
  18393, 18395, 18396, 18397, 18398, 18399, 18403, 18404, 18405, 18407, 18408, 18409, 18413, 18420, 18421,
  18424, 18429, 18434, 18443, 18445, 18448, 18452, 18454, 18456, 18485, 18486, 18490, 18493, 18494, 18495,
  18496, 18497, 18498, 18499, 18500, 18502, 18503, 18504, 18505, 18506, 18507, 18509, 18510, 18511, 18520,
  18521, 18522, 18523, 18524, 18525, 18526, 18527, 18528, 18529, 18530, 18531, 18532, 18533, 18534, 18538,
  18541, 18542, 18544, 18545, 18546, 18547, 18608, 18609, 18676, 18678, 18680, 18681, 18682, 18683, 18684,
  18686, 18689, 18690, 18691, 18693, 18695, 18702, 18713, 18715, 18716, 18717, 18718, 18720, 18721, 18722,
  18723, 18728, 18730, 18734, 18735, 18736, 18737, 18738, 18739, 18740, 18741, 18742, 18754, 18755, 18756,
  18761, 18803, 18805, 18806, 18807, 18808, 18809, 18810, 18811, 18812, 18813, 18814, 18817, 18821, 18822,
  18823, 18824, 18825, 18826, 18827, 18828, 18829, 18830, 18831, 18832, 18838, 18840, 18842, 18843, 18844,
  18847, 18848, 18861, 18865, 18866, 18867, 18868, 18869, 18870, 18871, 18872, 18873, 18874, 18875, 18876,
  18877, 18878, 19049, 19050, 19057, 19058, 19059, 19085, 19086, 19087, 19088, 19089, 19090, 19091, 19092,
  19093, 19094, 19096, 19098, 19099, 19100, 19101, 19102, 19103, 19104, 19105, 19106, 19107, 19108, 19109,
  19110, 19111, 19112, 19113, 19130, 19131, 19132, 19133, 19134, 19136, 19137, 19138, 19140, 19142, 19143,
  19144, 19146, 19157, 19162, 19163, 19164, 19165, 19167, 19168, 19308, 19309, 19310, 19311, 19312, 19315,
  19323, 19325, 19334, 19335, 19346, 19347, 19348, 19349, 19351, 19352, 19353, 19354, 19355, 19356, 19357,
  19358, 19360, 19362, 19365, 19366, 19367, 19368, 19369, 19370, 19371, 19372, 19373, 19374, 19375, 19376,
  19377, 19378, 19380, 19381, 19382, 19383, 19384, 19385, 19386, 19387, 19388, 19390, 19391, 19392, 19393,
  19394, 19396, 19397, 19399, 19400, 19401, 19402, 19403, 19405, 19407, 19426, 19430, 19432, 19433, 19434,
  19435, 19436, 19437, 19438, 19491, 19510, 19514, 19518, 19522, 19526, 19530, 19534, 19538, 19542, 19546,
  19550, 19554, 19558, 19562, 19566, 19570, 19575, 19576, 19577, 19578, 19582, 19585, 19586, 19587, 19588,
  19592, 19593, 19594, 19595, 19599, 19600, 19601, 19603, 19604, 19605, 19607, 19608, 19609, 19611, 19612,
  19613, 19615, 19616, 19617, 19619, 19620, 19621, 19682, 19683, 19684, 19685, 19686, 19687, 19688, 19689,
  19690, 19691, 19692, 19693, 19694, 19695, 19822, 19823, 19824, 19825, 19826, 19827, 19828, 19829, 19830,
  19831, 19832, 19833, 19834, 19835, 19836, 19838, 19839, 19840, 19841, 19842, 19843, 19844, 19845, 19846,
  19848, 19849, 19855, 19856, 19857, 19859, 19861, 19862, 19863, 19864, 19865, 19867, 19868, 19869, 19870,
  19871, 19873, 19875, 19876, 19877, 19878, 19884, 19886, 19887, 19888, 19889, 19890, 19892, 19893, 19894,
  19895, 19896, 19897, 19898, 19899, 19900, 19903, 19904, 19905, 19906, 19907, 19908, 19909, 19912, 19913,
  19915, 19919, 19920, 19921, 19922, 19923, 19925, 19926, 19927, 19928, 19929, 19944, 19945, 19946, 19964,
  19965, 19966, 19968, 19993, 19998, 19999, 20032, 20033, 20034, 20038, 20041, 20042, 20043, 20044, 20045,
  20046, 20047, 20048, 20049, 20050, 20051, 20052, 20053, 20054, 20055, 20056, 20057, 20058, 20059, 20060,
  20061, 20068, 20069, 20070, 20073, 20134, 20135, 20136, 20137, 20138, 20139, 20140, 20141, 20142, 20143,
  20144, 20145, 20146, 20149, 20150, 20154, 20158, 20159, 20163, 20167, 20171, 20175, 20176, 20177, 20181,
  20184, 20186, 20190, 20194, 20195, 20199, 20203, 20204, 20208, 20212, 20213, 20214, 20215, 20216, 20217,
  20220, 20257, 20258, 20259, 20260, 20261, 20262, 20263, 20264, 20265, 20266, 20267, 20268, 20269, 20270,
  20271, 20272, 20273, 20274, 20275, 20276, 20277, 20278, 20279, 20295, 20324, 20325, 20326, 20327, 20328,
  20329, 20330, 20331, 20332, 20333, 20334, 20335, 20336, 20380, 20479, 20480, 20481, 20487, 20488, 20549,
  20550, 20551, 20578, 20580, 20581, 20582, 20616, 20617, 20618, 20619, 20621, 20622, 20623, 20624, 20625,
  20626, 20627, 20628, 20629, 20630, 20631, 20632, 20633, 20634, 20635, 20637, 20638, 20639, 20648, 20654,
  20660, 20663, 20665, 20666, 20668, 20671, 20672, 20674, 20680, 20682, 20683, 20685, 20686, 20688, 20689,
  20691, 20696, 20697, 20698, 20699, 20700, 20701, 20702, 20704, 20705, 20706, 20707, 20710, 20711, 20712,
  20713, 20714, 20715, 20716, 20717, 20720, 20721, 21126, 21128, 21134, 21178, 21179, 21182, 21183, 21184,
  21185, 21186, 21187, 21188, 21189, 21196, 21197, 21198, 21199, 21200, 21201, 21202, 21203, 21204, 21205,
  21206, 21207, 21208, 21209, 21210, 21242, 21244, 21268, 21269, 21273, 21275, 21329, 21330, 21331, 21332,
  21333, 21334, 21335, 21336, 21337, 21338, 21343, 21344, 21345, 21346, 21347, 21348, 21349, 21350, 21351,
  21352, 21353, 21354, 21355, 21356, 21357, 21359, 21360, 21361, 21362, 21364, 21365, 21366, 21367, 21368,
  21370, 21372, 21373, 21374, 21375, 21376, 21387, 21388, 21389, 21390, 21391, 21392, 21393, 21394, 21395,
  21396, 21397, 21398, 21399, 21400, 21401, 21402, 21403, 21404, 21405, 21406, 21407, 21408, 21409, 21410,
  21411, 21412, 21413, 21414, 21415, 21416, 21417, 21418, 21452, 21453, 21454, 21455, 21456, 21457, 21458,
  21459, 21460, 21461, 21462, 21463, 21464, 21466, 21467, 21468, 21469, 21470, 21471, 21472, 21474, 21475,
  21476, 21477, 21479, 21480, 21481, 21482, 21483, 21484, 21485, 21486, 21487, 21489, 21490, 21491, 21492,
  21494, 21495, 21496, 21497, 21500, 21501, 21502, 21503, 21504, 21506, 21507, 21517, 21520, 21521, 21522,
  21523, 21527, 21529, 21530, 21531, 21532, 21563, 21581, 21582, 21583, 21584, 21585, 21586, 21587, 21588,
  21594, 21596, 21597, 21598, 21599, 21600, 21601, 21602, 21603, 21604, 21605, 21606, 21607, 21608, 21609,
  21610, 21611, 21612, 21613, 21614, 21615, 21616, 21617, 21618, 21619, 21620, 21621, 21622, 21623, 21624,
  21626, 21635, 21639, 21645, 21648, 21650, 21651, 21652, 21663, 21664, 21665, 21666, 21667, 21668, 21669,
  21671, 21672, 21673, 21674, 21675, 21676, 21677, 21678, 21679, 21680, 21681, 21682, 21683, 21684, 21686,
  21688, 21689, 21690, 21691, 21692, 21693, 21694, 21695, 21696, 21697, 21698, 21699, 21700, 21701, 21703,
  21704, 21705, 21706, 21707, 21708, 21709, 21710, 21712, 21715, 21779, 21780, 21792, 21800, 21801, 21802,
  21803, 21804, 21805, 21806, 21809, 21810, 21814, 21836, 21837, 21838, 21839, 21856, 21863, 21864, 21865,
  21888, 21889, 21890, 21994, 21995, 21996, 21997, 21998, 21999, 22000, 22001, 22002, 22003, 22004, 22005,
  22006, 22007, 22008, 22009, 22010, 22011, 22013, 22015, 22016, 22017, 22060, 22061, 22062, 22063, 22064,
  22065, 22066, 22067, 22068, 22069, 22070, 22071, 22072, 22073, 22074, 22075, 22076, 22077, 22078, 22079,
  22080, 22081, 22082, 22083, 22084, 22085, 22086, 22087, 22088, 22089, 22090, 22091, 22092, 22093, 22095,
  22096, 22097, 22098, 22099, 22100, 22101, 22102, 22106, 22107, 22108, 22109, 22110, 22111, 22112, 22113,
  22149, 22150, 22191, 22194, 22195, 22196, 22197, 22198, 22204, 22207, 22225, 22231, 22232, 22247, 22253,
  22267, 22269, 22301, 22302, 22303, 22304, 22305, 22306, 22311, 22313, 22314, 22315, 22317, 22319, 22322,
  22325, 22326, 22327, 22328, 22329, 22330, 22331, 22332, 22333, 22334, 22335, 22336, 22337, 22339, 22340,
  22342, 22343, 22347, 22348, 22377, 22379, 22380, 22383, 22384, 22385, 22394, 22403, 22405, 22406, 22407,
  22408, 22409, 22410, 22411, 22412, 22416, 22417, 22418, 22419, 22420, 22421, 22422, 22423, 22424, 22425,
  22426, 22427, 22428, 22429, 22430, 22431, 22433, 22436, 22437, 22438, 22439, 22440, 22441, 22442, 22443,
  22464, 22465, 22466, 22467, 22468, 22469, 22470, 22471, 22472, 22476, 22477, 22478, 22479, 22480, 22481,
  22482, 22483, 22488, 22489, 22490, 22491, 22492, 22493, 22494, 22495, 22496, 22497, 22498, 22499, 22500,
  22501, 22502, 22503, 22504, 22505, 22506, 22507, 22508, 22509, 22510, 22511, 22512, 22513, 22514, 22515,
  22516, 22517, 22518, 22519, 22651, 22652, 22654, 22655, 22656, 22657, 22659, 22661, 22662, 22663, 22667,
  22668, 22669, 22670, 22671, 22672, 22673, 22676, 22680, 22681, 22688, 22689, 22690, 22699, 22700, 22701,
  22702, 22711, 22713, 22714, 22715, 22716, 22718, 22720, 22721, 22730, 22731, 22732, 22740, 22741, 22747,
  22748, 22749, 22750, 22752, 22753, 22756, 22757, 22758, 22762, 22763, 22764, 22798, 22799, 22800, 22801,
  22802, 22803, 22804, 22805, 22806, 22807, 22808, 22809, 22811, 22812, 22814, 22815, 22816, 22817, 22818,
  22819, 22820, 22821, 22843, 22852, 22855, 22857, 22858, 22859, 22860, 22862, 22863, 22864, 22865, 22867,
  22868, 22869, 22870, 22872, 22873, 22874, 22875, 22876, 22877, 22878, 22879, 22880, 22881, 22882, 22883,
  22884, 22885, 22886, 22887, 22936, 22937, 22938, 22939, 22940, 22942, 22943, 22947, 22960, 22961, 22968,
  22981, 22983, 22988, 22994, 23000, 23009, 23014, 23017, 23018, 23019, 23020, 23021, 23023, 23025, 23028,
  23029, 23030, 23031, 23032, 23033, 23034, 23035, 23036, 23037, 23038, 23039, 23043, 23044, 23045, 23048,
  23049, 23050, 23053, 23056, 23057, 23058, 23059, 23060, 23061, 23062, 23063, 23064, 23065, 23066, 23067,
  23068, 23069, 23070, 23071, 23072, 23073, 23075, 23084, 23085, 23091, 23124, 23125, 23126, 23127, 23128,
  23129, 23156, 23219, 23220, 23226, 23237, 23242, 23243, 23244, 23251, 23252, 23253, 23254, 23255, 23256,
  23257, 23258, 23259, 23260, 23261, 23262, 23263, 23264, 23272, 23273, 23274, 23275, 23276, 23277, 23278,
  23279, 23280, 23281, 23282, 23283, 23284, 23286, 23287, 23288, 23289, 23290, 23291, 23292, 23293, 23294,
  23295, 23296, 23297, 23298, 23299, 23300, 23301, 23302, 23303, 23304, 23305, 23306, 23307, 23308, 23309,
  23310, 23311, 23312, 23313, 23314, 23315, 23316, 23317, 23318, 23319, 23362, 23363, 23451, 23452, 23453,
  23454, 23455, 23456, 23457, 23458, 23459, 23461, 23462, 23464, 23465, 23466, 23467, 23468, 23469, 23557,
  23577, 23663, 23664, 23665, 23666, 23667, 23668, 23761, 23828, 23829, 23838, 23839, 24020, 24021, 24022,
  24023, 24024, 24044, 24045, 24046, 24063, 24064, 24069, 24073, 24083, 24090, 24091, 24094, 24096, 24122,
  24123, 24137, 24154, 24155, 24356, 24357, 24359, 24360, 24361, 24362, 24363, 24364, 24365, 24366, 24378,
  24379, 24380, 24381, 24384, 24385, 24387, 24388, 24389, 24391, 24392, 24393, 24395, 24396, 24397, 24398,
  24450, 24451, 24452, 24453, 24454, 24455, 24456, 24457, 24458, 24459, 24461, 24462, 24463, 24464, 24465,
  24466, 24481, 25536, 25537, 25538, 25540, 25541, 25562, 25563, 25564, 25603, 25605, 25606, 25607, 25608,
  25609, 25693, 25701, 25702, 25710, 25711, 25712, 25713, 25714, 25715, 25716, 25717, 25718, 25772, 25773,
  25774, 25775, 25776, 25777, 25823, 25824, 25825, 25826, 25828, 25836, 25838, 25939, 25941, 25942, 25943,
  25944, 25945, 25946, 25947, 25950, 25952, 25953, 25954, 25955, 25956, 25957, 25962, 25964, 25967, 25968,
  25969, 25970, 27408, 27409, 27410, 27411, 27412, 27413, 27414, 27415, 27631, 27637, 27638, 27639, 27643,
  27644, 27645, 27646, 27647, 27648, 27649, 27650, 27652, 27653, 27654, 27830, 27832, 27833, 27834, 27928,
  27929, 27930, 27931, 27939, 27942, 28029, 28030, 28031, 28032, 28050, 28051, 28052, 28054, 28055, 28057,
  28069, 28070, 28074, 28075, 28166, 28246, 28247, 28553, 28555, 28559, 28560, 28561, 28574, 28575, 28576,
  28577, 28758, 28759, 28760, 28761, 28972, 29121, 29124, 29125, 29149, 29150, 29151, 29152, 29153, 29155,
  29156, 29165, 29171, 29175, 29182, 29210, 29312, 29313, 29314, 29315, 29325, 29326, 29327, 29328, 29337,
  29339, 29340, 29341, 29342, 29343, 29344, 29345, 29456, 29457, 29594, 29595, 29596, 29597, 29598, 29599,
  29600, 29601, 29602, 29603, 29604, 29605, 29606, 29607, 29608, 29609, 29610, 29611, 29612, 29613, 29614,
  29615, 29616, 29617, 29973, 29974, 29975, 30074, 30076, 30077, 30086, 30087, 30088, 30497, 30498, 30830,
  30832, 30834, 31125, 31126, 31127, 31131, 31133, 31134, 31136, 31137, 31138, 31139, 31140, 31142, 31143,
  31145, 31147, 31148, 31149, 31150, 31151, 31152, 31153, 31173, 31178, 31180, 31187, 31190, 31196, 31200,
  31202, 31222, 31226, 31230, 31319, 31320, 31321, 31322, 31326, 31328, 31329, 31330, 31333, 31334, 31335,
  31336, 31338, 31339, 31340, 31342, 31343, 31371, 31717, 31718, 31719, 31720, 31726, 31727, 31756, 31758,
  31759, 31919, 31920, 31921, 31922, 31923, 31924, 32508, 32645, 32772, 32774, 34622, 34661, 38632, 38633,
  38661, 38662, 38663, 38664, 38665, 38666, 38667, 38668, 38669, 38670, 38671, 38672, 38707, 39320, 39322,
  39370, 41342, 43666, 43667
);
INSERT INTO `item_budget_assign` (`entry`, `template_id`, `budget_mult`, `stamina_delta`, `dps_delta`, `absorbed_spell_slots`, `armor_delta`) VALUES
(944, 86, 1.015, 0, 0.0, 1, 0),
(1443, 87, 1, 0, 0.0, 0, 0),
(2243, 88, 0.507, 0, 0.0, 0, 0),
(2801, 89, 0.791, 0, 0.0, 0, 0),
(5267, 90, 0.445, 0, 0.0, 0, 0),
(9402, 91, 1, 0, 0.0, 0, 0),
(11924, 92, 1, 0, 0.0, 1, 0),
(11928, 93, 0.965, 0, 0.0, 1, 0),
(11930, 94, 1, 0, 0.0, 0, 0),
(12103, 95, 1, 0, 0.0, 0, 0),
(12344, 96, 1, 0, 0.0, 0, 0),
(12543, 97, 1, 0, 0.0, 1, 0),
(12544, 98, 1, 0, 0.0, 0, 0),
(12545, 99, 1, 0, 0.0, 1, 0),
(12548, 100, 1, 0, 0.0, 0, 0),
(12584, 101, 0.445, 0, 0.0, 1, 0),
(12587, 102, 1, 0, 0.0, 1, 0),
(12589, 103, 1, 0, 0.0, 1, 0),
(12602, 104, 0.422, 0, 0.0, 1, 0),
(12603, 105, 1, 0, 0.0, 0, 0),
(12604, 106, 1, 0, 0.0, 1, 0),
(12606, 107, 1, 0, 0.0, 1, 0),
(12618, 108, 1, 0, 0.0, 1, 0),
(12619, 109, 1, 0, 0.0, 1, 0),
(12620, 110, 1, 0, 0.0, 1, 0),
(12633, 111, 1, 0, 0.0, 2, 0),
(12634, 112, 1, 0, 0.0, 0, 0),
(12636, 113, 1, 0, 0.0, 0, 0),
(12637, 114, 1, 0, 0.0, 0, 0),
(12639, 115, 1, 0, 0.0, 7, 0),
(12640, 116, 1, 0, 0.0, 3, 0),
(12641, 117, 1, 0, 0.0, 4, 0),
(12752, 118, 1, 0, 0.0, 1, 0),
(12756, 119, 1, 0, 0.0, 1, 0),
(12757, 120, 1, 0, 0.0, 3, 0),
(12783, 121, 0.445, 0, 0.0, 1, 0),
(12796, 122, 0.791, 0, 0.0, 0, 0),
(12895, 123, 1, 0, 0.0, 0, 0),
(12903, 124, 1, 0, 0.0, 0, 0),
(12926, 125, 1, 0, 0.0, 1, 0),
(12927, 126, 1, 0, 0.0, 1, 0),
(12929, 127, 1, 0, 0.0, 1, 0),
(12935, 128, 1, 0, 0.0, 0, 0),
(12936, 129, 1, 0, 0.0, 3, 0),
(12939, 130, 0.387, 0, 0.0, 1, 0),
(12940, 131, 0.453, 0, 0.0, 1, 0),
(12945, 132, 1, 0, 0.0, 0, 0),
(12952, 133, 1, 0, 0.0, 1, 0),
(12960, 134, 1, 0, 0.0, 1, 0),
(12963, 135, 1, 0, 0.0, 3, 0),
(12964, 136, 1, 0, 0.0, 0, 0),
(12965, 137, 1, 0, 0.0, 1, 0),
(12966, 138, 1, 0, 0.0, 1, 0),
(12967, 139, 1, 0, 0.0, 0, 0),
(12968, 140, 1, 0, 0.0, 0, 0),
(13000, 141, 1.015, 0, 0.0, 0, 0),
(13001, 142, 1, 0, 0.0, 1, 0),
(13006, 143, 0.445, 0, 0.0, 0, 0),
(13015, 144, 0.445, 0, 0.0, 0, 0),
(13023, 145, 0.405, 0, 0.0, 0, 0),
(13028, 146, 0.507, 0, 0.0, 0, 0),
(13072, 147, 1, 0, 0.0, 1, 0),
(13075, 148, 1, 0, 0.0, 0, 0),
(13080, 149, 1, 0, 0.0, 0, 0),
(13083, 150, 0.766, 0, 0.0, 0, 0),
(13090, 151, 1, 0, 0.0, 0, 0),
(13092, 152, 1, 0, 0.0, 1, 0),
(13096, 153, 1, 0, 0.0, 0, 0),
(13098, 154, 1, 0, 0.0, 1, 0),
(13107, 155, 1, 0, 0.0, 0, 0),
(13113, 156, 1, 0, 0.0, 0, 0),
(13116, 157, 1, 0, 0.0, 0, 0),
(13123, 158, 1, 0, 0.0, 0, 0),
(13133, 159, 1, 0, 0.0, 0, 0),
(13141, 160, 1, 0, 0.0, 0, 0),
(13142, 161, 1, 0, 0.0, 0, 0),
(13161, 162, 1.015, 0, 0.0, 1, 0),
(13162, 163, 1, 0, 0.0, 1, 0),
(13163, 164, 0.884, 0, 0.0, 1, 0),
(13167, 165, 0.791, 0, 0.0, 0, 0),
(13168, 166, 1, 0, 0.0, 1, 0),
(13169, 167, 1, 0, 0.0, 1, 0),
(13170, 168, 1, 0, 0.0, 1, 0),
(13177, 169, 1, 0, 0.0, 1, 0),
(13178, 170, 1, 0, 0.0, 2, 0),
(13179, 171, 1, 0, 0.0, 0, 0),
(13184, 172, 1, 0, 0.0, 1, 0),
(13185, 173, 1, 0, 0.0, 1, 0),
(13204, 174, 0.445, 0, 0.0, 0, 0),
(13205, 175, 0.766, 0, 0.0, 0, 0),
(13206, 176, 1, 0, 0.0, 1, 0),
(13208, 177, 1, 0, 0.0, 1, 0),
(13211, 178, 1, 0, 0.0, 1, 0),
(13244, 179, 1, 0, 0.0, 0, 0),
(13249, 180, 1.015, 0, 0.0, 0, 0),
(13252, 181, 1, 0, 0.0, 0, 0),
(13253, 182, 1, 0, 0.0, 1, 0),
(13259, 183, 1, 0, 0.0, 0, 0),
(13260, 184, 1, 0, 0.0, 1, 0),
(13314, 185, 1, 0, 0.0, 1, 0),
(13340, 186, 1, 0, 0.0, 0, 0),
(13344, 187, 1, 0, 0.0, 1, 0),
(13345, 188, 1, 0, 0.0, 0, 0),
(13346, 189, 1, 0, 0.0, 1, 0),
(13349, 190, 0.507, 0, 0.0, 1, 0),
(13353, 191, 0.965, 0, 0.0, 0, 0),
(13358, 192, 1, 0, 0.0, 0, 0),
(13360, 193, 0.507, 0, 0.0, 0, 0),
(13369, 194, 1, 0, 0.0, 1, 0),
(13372, 195, 0.791, 0, 0.0, 0, 0),
(13373, 196, 1, 0, 0.0, 0, 0),
(13374, 197, 1, 0, 0.0, 0, 0),
(13381, 198, 1, 0, 0.0, 0, 0),
(13385, 199, 0.987, 0, 0.0, 0, 0),
(13388, 200, 1, 0, 0.0, 1, 0),
(13389, 201, 1, 0, 0.0, 0, 0),
(13390, 202, 1, 0, 0.0, 1, 0),
(13391, 203, 1, 0, 0.0, 1, 0),
(13392, 204, 1, 0, 0.0, 0, 0),
(13397, 205, 1, 0, 0.0, 0, 0),
(13398, 206, 1, 0, 0.0, 1, 0),
(13498, 207, 1, 0, 0.0, 0, 0),
(13502, 208, 1, 0, 0.0, 0, 0),
(13936, 209, 1, 0, 0.0, 1, 0),
(13937, 210, 1.015, 0, 0.0, 0, 0),
(13938, 211, 0.516, 0, 0.0, 1, 0),
(13944, 212, 1, 0, 0.0, 1, 0),
(13950, 213, 1, 0, 0.0, 0, 0),
(13951, 214, 1, 0, 0.0, 0, 0),
(13954, 215, 1, 0, 0.0, 1, 0),
(13955, 216, 1, 0, 0.0, 2, 0),
(13956, 217, 1, 0, 0.0, 1, 0),
(13957, 218, 1, 0, 0.0, 1, 0),
(13958, 219, 1, 0, 0.0, 0, 0),
(13959, 220, 1, 0, 0.0, 1, 0),
(13960, 221, 1, 0, 0.0, 0, 0),
(13961, 222, 1, 0, 0.0, 0, 0),
(13962, 223, 1, 0, 0.0, 3, 0),
(13963, 224, 1, 0, 0.0, 1, 0),
(13964, 225, 1.931, 0, 0.0, 1, 0),
(13967, 226, 1, 0, 0.0, 1, 0),
(13969, 227, 1, 0, 0.0, 1, 0),
(13986, 228, 1, 0, 0.0, 0, 0),
(14002, 229, 0.766, 0, 0.0, 0, 0),
(14138, 230, 1, 0, 0.0, 0, 0),
(14139, 231, 1, 0, 0.0, 0, 0),
(14140, 232, 1, 0, 0.0, 0, 0),
(14146, 233, 1, 0, 0.0, 1, 0),
(14152, 234, 1, 0, 0.0, 3, 0),
(14153, 235, 1, 0, 0.0, 1, 0),
(14154, 236, 1, 0, 0.0, 5, 0),
(14340, 237, 1, 0, 0.0, 1, 0),
(14502, 238, 1, 0, 0.0, 0, 0),
(14503, 239, 1, 0, 0.0, 0, 0),
(14522, 240, 1, 0, 0.0, 1, 0),
(14525, 241, 1, 0, 0.0, 1, 0),
(14528, 242, 0.766, 0, 0.0, 0, 0),
(14536, 243, 1, 0, 0.0, 0, 0),
(14538, 244, 1, 0, 0.0, 1, 0),
(14539, 245, 1, 0, 0.0, 0, 0),
(14543, 246, 1, 0, 0.0, 0, 0),
(14545, 247, 1, 0, 0.0, 0, 0),
(14548, 248, 1, 0, 0.0, 1, 0),
(14553, 249, 1, 0, 0.0, 1, 0),
(14554, 250, 1, 0, 0.0, 0, 0),
(14558, 251, 1, 0, 0.0, 0, 0),
(14577, 252, 1, 0, 0.0, 0, 0),
(14611, 253, 1, 0, 0.0, 1, 0),
(14612, 254, 1, 0, 0.0, 0, 0),
(14614, 255, 1, 0, 0.0, 0, 0),
(14615, 256, 1, 0, 0.0, 1, 0),
(14616, 257, 1, 0, 0.0, 1, 0),
(14620, 258, 1, 0, 0.0, 1, 0),
(14621, 259, 1, 0, 0.0, 2, 0),
(14622, 260, 1, 0, 0.0, 1, 0),
(14623, 261, 1, 0, 0.0, 2, 0),
(14624, 262, 1, 0, 0.0, 1, 0),
(14626, 263, 1, 0, 0.0, 1, 0),
(14629, 264, 1, 0, 0.0, 0, 0),
(14631, 265, 1, 0, 0.0, 1, 0),
(14632, 266, 1, 0, 0.0, 0, 0),
(14633, 267, 1, 0, 0.0, 0, 0),
(14637, 268, 1, 0, 0.0, 0, 0),
(15047, 269, 1, 0, 0.0, 1, 0),
(15051, 270, 1, 0, 0.0, 0, 0),
(15052, 271, 1, 0, 0.0, 0, 0),
(15059, 272, 1, 0, 0.0, 1, 0),
(15062, 273, 1, 0, 0.0, 2, 0),
(15141, 274, 1, 0, 0.0, 2, 0),
(15411, 275, 1, 0, 0.0, 1, 0),
(15413, 276, 1, 0, 0.0, 1, 0),
(15421, 277, 1, 0, 0.0, 0, 0),
(15805, 278, 0.965, 0, 0.0, 0, 0),
(15806, 279, 0.445, 0, 0.0, 0, 0),
(15854, 280, 1.015, 0, 0.0, 0, 0),
(15856, 281, 1, 0, 0.0, 0, 0),
(16007, 282, 0.415, 0, 0.0, 0, 0),
(16058, 283, 1, 0, 0.0, 1, 0),
(16335, 284, 1, 0, 0.0, 0, 0),
(16337, 285, 1, 0, 0.0, 0, 0),
(16345, 286, 0.445, 0, 0.0, 1, 0),
(16367, 287, 1, 0, 0.0, 0, 0),
(16369, 288, 1, 0, 0.0, 1, 0),
(16370, 289, 1, 0, 0.0, 0, 0),
(16391, 290, 1, 0, 0.0, 2, 0),
(16392, 291, 1, 0, 0.0, 0, 0),
(16393, 292, 1, 0, 0.0, 1, 0),
(16394, 293, 1, 0, 0.0, 0, 0),
(16395, 294, 1, 0, 0.0, 0, 0),
(16396, 295, 1, 0, 0.0, 0, 0),
(16397, 296, 1, 0, 0.0, 0, 0),
(16398, 297, 1, 0, 0.0, 0, 0),
(16399, 298, 1, 0, 0.0, 0, 0),
(16400, 299, 1, 0, 0.0, 0, 0),
(16401, 300, 1, 0, 0.0, 1, 0),
(16402, 301, 1, 0, 0.0, 0, 0),
(16403, 302, 1, 0, 0.0, 1, 0),
(16404, 303, 1, 0, 0.0, 0, 0),
(16405, 304, 1, 0, 0.0, 0, 0),
(16406, 305, 1, 0, 0.0, 1, 0),
(16407, 306, 1, 0, 0.0, 0, 0),
(16409, 307, 1, 0, 0.0, 0, 0),
(16410, 308, 1, 0, 0.0, 0, 0),
(16411, 309, 1, 0, 0.0, 0, 0),
(16412, 310, 1, 0, 0.0, 0, 0),
(16413, 311, 1, 0, 0.0, 1, 0),
(16414, 312, 1, 0, 0.0, 1, 0),
(16415, 313, 1, 0, 0.0, 1, 0),
(16416, 314, 1, 0, 0.0, 1, 0),
(16417, 315, 1, 0, 0.0, 1, 0),
(16418, 316, 1, 0, 0.0, 5, 0),
(16419, 317, 1, 0, 0.0, 1, 0),
(16420, 318, 1, 0, 0.0, 0, 0),
(16421, 319, 1, 0, 0.0, 3, 0),
(16422, 320, 1, 0, 0.0, 1, 0),
(16423, 321, 1, 0, 0.0, 1, 0),
(16424, 322, 1, 0, 0.0, 2, 0),
(16425, 323, 1, 0, 0.0, 2, 0),
(16426, 324, 1, 0, 0.0, 3, 0),
(16427, 325, 1, 0, 0.0, 0, 0),
(16428, 326, 1, 0, 0.0, 0, 0),
(16429, 327, 1, 0, 0.0, 0, 0),
(16430, 328, 1, 0, 0.0, 1, 0),
(16431, 329, 1, 0, 0.0, 1, 0),
(16432, 330, 1, 0, 0.0, 0, 0),
(16433, 331, 1, 0, 0.0, 1, 0),
(16434, 332, 1, 0, 0.0, 0, 0),
(16435, 333, 1, 0, 0.0, 1, 0),
(16436, 334, 1, 0, 0.0, 0, 0),
(16437, 335, 1, 0, 0.0, 3, 0),
(16438, 336, 1, 0, 0.0, 0, 0),
(16439, 337, 1, 0, 0.0, 0, 0),
(16440, 338, 1, 0, 0.0, 1, 0),
(16441, 339, 1, 0, 0.0, 3, 0),
(16442, 340, 1, 0, 0.0, 3, 0),
(16443, 341, 1, 0, 0.0, 3, 0),
(16444, 342, 1, 0, 0.0, 3, 0),
(16445, 343, 1, 0, 0.0, 0, 0),
(16446, 344, 1, 0, 0.0, 0, 0),
(16447, 345, 1, 0, 0.0, 0, 0),
(16448, 346, 1, 0, 0.0, 2, 0),
(16449, 347, 1, 0, 0.0, 1, 0),
(16450, 348, 1, 0, 0.0, 1, 0),
(16451, 349, 1, 0, 0.0, 3, 0),
(16452, 350, 1, 0, 0.0, 3, 0),
(16453, 351, 1, 0, 0.0, 3, 0),
(16454, 352, 1, 0, 0.0, 1, 0),
(16455, 353, 1, 0, 0.0, 3, 0),
(16456, 354, 1, 0, 0.0, 3, 0),
(16457, 355, 1, 0, 0.0, 1, 0),
(16458, 356, 1, 0, 0.0, 0, 0),
(16459, 357, 1, 0, 0.0, 1, 0),
(16460, 358, 1, 0, 0.0, 0, 0),
(16461, 359, 1, 0, 0.0, 0, 0),
(16462, 360, 1, 0, 0.0, 1, 0),
(16463, 361, 1, 0, 0.0, 2, 0),
(16464, 362, 1, 0, 0.0, 0, 0),
(16465, 363, 1, 0, 0.0, 1, 0),
(16466, 364, 1, 0, 0.0, 2, 0),
(16467, 365, 1, 0, 0.0, 1, 0),
(16468, 366, 1, 0, 0.0, 1, 0),
(16469, 367, 1, 0, 0.0, 0, 0),
(16470, 368, 1, 0, 0.0, 0, 0),
(16471, 369, 1, 0, 0.0, 2, 0),
(16472, 370, 1, 0, 0.0, 1, 0),
(16473, 371, 1, 0, 0.0, 3, 0),
(16474, 372, 1, 0, 0.0, 3, 0),
(16475, 373, 1, 0, 0.0, 3, 0),
(16476, 374, 1, 0, 0.0, 1, 0),
(16477, 375, 1, 0, 0.0, 1, 0),
(16478, 376, 1, 0, 0.0, 1, 0),
(16479, 377, 1, 0, 0.0, 3, 0),
(16480, 378, 1, 0, 0.0, 1, 0),
(16481, 379, 1, 0, 0.0, 0, 0),
(16482, 380, 1, 0, 0.0, 0, 0),
(16483, 381, 1, 0, 0.0, 1, 0),
(16484, 382, 1, 0, 0.0, 3, 0),
(16485, 383, 1, 0, 0.0, 1, 0),
(16486, 384, 1, 0, 0.0, 0, 0),
(16487, 385, 1, 0, 0.0, 2, 0),
(16488, 386, 1, 0, 0.0, 0, 0),
(16489, 387, 1, 0, 0.0, 1, 0),
(16490, 388, 1, 0, 0.0, 1, 0),
(16491, 389, 1, 0, 0.0, 1, 0),
(16492, 390, 1, 0, 0.0, 1, 0),
(16493, 391, 1, 0, 0.0, 0, 0),
(16494, 392, 1, 0, 0.0, 1, 0),
(16495, 393, 1, 0, 0.0, 0, 0),
(16496, 394, 1, 0, 0.0, 0, 0),
(16497, 395, 1, 0, 0.0, 0, 0),
(16498, 396, 1, 0, 0.0, 0, 0),
(16499, 397, 1, 0, 0.0, 0, 0),
(16500, 398, 1, 0, 0.0, 0, 0),
(16501, 399, 1, 0, 0.0, 1, 0),
(16502, 400, 1, 0, 0.0, 1, 0),
(16503, 401, 1, 0, 0.0, 2, 0),
(16504, 402, 1, 0, 0.0, 3, 0),
(16505, 403, 1, 0, 0.0, 1, 0),
(16506, 404, 1, 0, 0.0, 3, 0),
(16507, 405, 1, 0, 0.0, 0, 0),
(16508, 406, 1, 0, 0.0, 1, 0),
(16509, 407, 1, 0, 0.0, 0, 0),
(16510, 408, 1, 0, 0.0, 1, 0),
(16511, 409, 1, 0, 0.0, 0, 0),
(16512, 410, 1, 0, 0.0, 0, 0),
(16513, 411, 1, 0, 0.0, 1, 0),
(16514, 412, 1, 0, 0.0, 0, 0),
(16515, 413, 1, 0, 0.0, 1, 0),
(16516, 414, 1, 0, 0.0, 0, 0),
(16517, 415, 1, 0, 0.0, 0, 0),
(16518, 416, 1, 0, 0.0, 1, 0),
(16519, 417, 1, 0, 0.0, 1, 0),
(16520, 418, 1, 0, 0.0, 0, 0),
(16521, 419, 1, 0, 0.0, 1, 0),
(16522, 420, 1, 0, 0.0, 1, 0),
(16523, 421, 1, 0, 0.0, 1, 0),
(16524, 422, 1, 0, 0.0, 1, 0),
(16525, 423, 1, 0, 0.0, 2, 0),
(16526, 424, 1, 0, 0.0, 0, 0),
(16527, 425, 1, 0, 0.0, 3, 0),
(16528, 426, 1, 0, 0.0, 0, 0),
(16529, 427, 1, 0, 0.0, 0, 0),
(16530, 428, 1, 0, 0.0, 1, 0),
(16531, 429, 1, 0, 0.0, 1, 0),
(16532, 430, 1, 0, 0.0, 0, 0),
(16533, 431, 1, 0, 0.0, 3, 0),
(16534, 432, 1, 0, 0.0, 3, 0),
(16535, 433, 1, 0, 0.0, 3, 0),
(16536, 434, 1, 0, 0.0, 3, 0),
(16537, 435, 1, 0, 0.0, 0, 0),
(16538, 436, 1, 0, 0.0, 0, 0),
(16539, 437, 1, 0, 0.0, 3, 0),
(16540, 438, 1, 0, 0.0, 2, 0),
(16541, 439, 1, 0, 0.0, 1, 0),
(16542, 440, 1, 0, 0.0, 1, 0),
(16543, 441, 1, 0, 0.0, 3, 0),
(16544, 442, 1, 0, 0.0, 1, 0),
(16545, 443, 1, 0, 0.0, 1, 0),
(16546, 444, 1, 0, 0.0, 0, 0),
(16547, 445, 1, 0, 0.0, 0, 0),
(16548, 446, 1, 0, 0.0, 3, 0),
(16549, 447, 1, 0, 0.0, 3, 0),
(16550, 448, 1, 0, 0.0, 3, 0),
(16551, 449, 1, 0, 0.0, 1, 0),
(16552, 450, 1, 0, 0.0, 1, 0),
(16553, 451, 1, 0, 0.0, 0, 0),
(16554, 452, 1, 0, 0.0, 1, 0),
(16555, 453, 1, 0, 0.0, 2, 0),
(16556, 454, 1, 0, 0.0, 0, 0),
(16557, 455, 1, 0, 0.0, 0, 0),
(16558, 456, 1, 0, 0.0, 0, 0),
(16559, 457, 1, 0, 0.0, 0, 0),
(16560, 458, 1, 0, 0.0, 1, 0),
(16561, 459, 1, 0, 0.0, 3, 0),
(16562, 460, 1, 0, 0.0, 1, 0),
(16563, 461, 1, 0, 0.0, 3, 0),
(16564, 462, 1, 0, 0.0, 3, 0),
(16565, 463, 1, 0, 0.0, 2, 0),
(16566, 464, 1, 0, 0.0, 1, 0),
(16567, 465, 1, 0, 0.0, 1, 0),
(16568, 466, 1, 0, 0.0, 1, 0),
(16569, 467, 1, 0, 0.0, 1, 0),
(16570, 468, 1, 0, 0.0, 0, 0),
(16571, 469, 1, 0, 0.0, 2, 0),
(16572, 470, 1, 0, 0.0, 0, 0),
(16573, 471, 1, 0, 0.0, 2, 0),
(16574, 472, 1, 0, 0.0, 1, 0),
(16575, 473, 1, 0, 0.0, 0, 0),
(16576, 474, 1, 0, 0.0, 0, 0),
(16577, 475, 1, 0, 0.0, 4, 0),
(16578, 476, 1, 0, 0.0, 4, 0),
(16579, 477, 1, 0, 0.0, 7, 0),
(16580, 478, 1, 0, 0.0, 1, 0),
(16666, 479, 1, 0, 0.0, 0, 0),
(16667, 480, 1, 0, 0.0, 0, 0),
(16668, 481, 1, 0, 0.0, 0, 0),
(16669, 482, 1, 0, 0.0, 0, 0),
(16674, 483, 1, 0, 0.0, 0, 0),
(16677, 484, 1, 0, 0.0, 0, 0),
(16678, 485, 1, 0, 0.0, 0, 0),
(16679, 486, 1, 0, 0.0, 0, 0),
(16686, 487, 1, 0, 0.0, 0, 0),
(16687, 488, 1, 0, 0.0, 0, 0),
(16688, 489, 1, 0, 0.0, 0, 0),
(16689, 490, 1, 0, 0.0, 0, 0),
(16690, 491, 1, 0, 0.0, 0, 0),
(16693, 492, 1, 0, 0.0, 0, 0),
(16694, 493, 1, 0, 0.0, 0, 0),
(16695, 494, 1, 0, 0.0, 0, 0),
(16698, 495, 1, 0, 0.0, 0, 0),
(16699, 496, 1, 0, 0.0, 0, 0),
(16700, 497, 1, 0, 0.0, 0, 0),
(16701, 498, 1, 0, 0.0, 0, 0),
(16706, 499, 1, 0, 0.0, 0, 0),
(16707, 500, 1, 0, 0.0, 0, 0),
(16708, 501, 1, 0, 0.0, 0, 0),
(16709, 502, 1, 0, 0.0, 0, 0),
(16718, 503, 1, 0, 0.0, 0, 0),
(16719, 504, 1, 0, 0.0, 0, 0),
(16720, 505, 1, 0, 0.0, 0, 0),
(16721, 506, 1, 0, 0.0, 0, 0),
(16726, 507, 1, 0, 0.0, 0, 0),
(16727, 508, 1, 0, 0.0, 0, 0),
(16728, 509, 1, 0, 0.0, 0, 0),
(16729, 510, 1, 0, 0.0, 0, 0),
(16730, 511, 1, 0, 0.0, 0, 0),
(16731, 512, 1, 0, 0.0, 0, 0),
(16732, 513, 1, 0, 0.0, 0, 0),
(16733, 514, 1, 0, 0.0, 0, 0),
(16818, 515, 1, 0, 0.0, 1, 0),
(16832, 516, 1, 0, 0.0, 1, 0),
(16897, 517, 1, 0, 0.0, 3, 0),
(16898, 518, 1, 0, 0.0, 3, 0),
(16899, 519, 1, 0, 0.0, 1, 0),
(16900, 520, 1, 0, 0.0, 2, 0),
(16901, 521, 1, 0, 0.0, 1, 0),
(16902, 522, 1, 0, 0.0, 1, 0),
(16903, 523, 1, 0, 0.0, 1, 0),
(16904, 524, 1, 0, 0.0, 1, 0),
(16905, 525, 1, 0, 0.0, 3, 0),
(16906, 526, 1, 0, 0.0, 1, 0),
(16907, 527, 1, 0, 0.0, 1, 0),
(16908, 528, 1, 0, 0.0, 1, 0),
(16909, 529, 1, 0, 0.0, 1, 0),
(16910, 530, 1, 0, 0.0, 1, 0),
(16911, 531, 1, 0, 0.0, 1, 0),
(16912, 532, 1, 0, 0.0, 1, 0),
(16913, 533, 1, 0, 0.0, 3, 0),
(16914, 534, 1, 0, 0.0, 2, 0),
(16915, 535, 1, 0, 0.0, 3, 0),
(16916, 536, 1, 0, 0.0, 3, 0),
(16917, 537, 1, 0, 0.0, 2, 0),
(16918, 538, 1, 0, 0.0, 1, 0),
(16919, 539, 1, 0, 0.0, 1, 0),
(16920, 540, 1, 0, 0.0, 3, 0),
(16921, 541, 1, 0, 0.0, 1, 0),
(16922, 542, 1, 0, 0.0, 1, 0),
(16923, 543, 1, 0, 0.0, 1, 0),
(16924, 544, 1, 0, 0.0, 1, 0),
(16925, 545, 1, 0, 0.0, 1, 0),
(16926, 546, 1, 0, 0.0, 1, 0),
(16927, 547, 1, 0, 0.0, 1, 0),
(16928, 548, 1, 0, 0.0, 6, 0),
(16929, 549, 1, 0, 0.0, 2, 0),
(16930, 550, 1, 0, 0.0, 1, 0),
(16931, 551, 1, 0, 0.0, 3, 0),
(16932, 552, 1, 0, 0.0, 2, 0),
(16933, 553, 1, 0, 0.0, 3, 0),
(16934, 554, 1, 0, 0.0, 1, 0),
(16935, 555, 1, 0, 0.0, 0, 0),
(16936, 556, 1, 0, 0.0, 1, 0),
(16937, 557, 1, 0, 0.0, 1, 0),
(16938, 558, 1, 0, 0.0, 3, 0),
(16939, 559, 1, 0, 0.0, 1, 0),
(16940, 560, 1, 0, 0.0, 1, 0),
(16941, 561, 1, 0, 0.0, 0, 0),
(16942, 562, 1, 0, 0.0, 1, 0),
(16943, 563, 1, 0, 0.0, 0, 0),
(16944, 564, 1, 0, 0.0, 3, 0),
(16945, 565, 1, 0, 0.0, 1, 0),
(16946, 566, 1, 0, 0.0, 3, 0),
(16947, 567, 1, 0, 0.0, 3, 0),
(16948, 568, 1, 0, 0.0, 2, 0),
(16949, 569, 1, 0, 0.0, 1, 0),
(16950, 570, 1, 0, 0.0, 1, 0),
(16951, 571, 1, 0, 0.0, 1, 0),
(16952, 572, 1, 0, 0.0, 1, 0),
(16953, 573, 1, 0, 0.0, 2, 0),
(16954, 574, 1, 0, 0.0, 1, 0),
(16955, 575, 1, 0, 0.0, 1, 0),
(16956, 576, 1, 0, 0.0, 2, 0),
(16957, 577, 1, 0, 0.0, 1, 0),
(16958, 578, 1, 0, 0.0, 2, 0),
(16959, 579, 1, 0, 0.0, 0, 0),
(16960, 580, 1, 0, 0.0, 3, 0),
(16961, 581, 1, 0, 0.0, 2, 0),
(16962, 582, 1, 0, 0.0, 3, 0),
(16963, 583, 1, 0, 0.0, 1, 0),
(16964, 584, 1, 0, 0.0, 3, 0),
(16965, 585, 1, 0, 0.0, 2, 0),
(16966, 586, 1, 0, 0.0, 1, 0),
(16979, 587, 1, 0, 0.0, 0, 0),
(16980, 588, 1, 0, 0.0, 0, 0),
(16983, 589, 1, 0, 0.0, 1, 0),
(16988, 590, 1, 0, 0.0, 0, 0),
(16996, 591, 0.405, 0, 0.0, 0, 0),
(16997, 592, 0.516, 0, 0.0, 0, 0),
(16998, 593, 0.766, 0, 0.0, 0, 0),
(17016, 594, 0.445, 0, 0.0, 0, 0),
(17045, 595, 1, 0, 0.0, 0, 0),
(17063, 596, 1, 0, 0.0, 1, 0),
(17065, 597, 1, 0, 0.0, 3, 0),
(17066, 598, 0.422, 0, 0.0, 2, 0),
(17067, 599, 0.965, 0, 0.0, 0, 0),
(17069, 600, 0.405, 0, 0.0, 2, 0),
(17070, 601, 1.931, 0, 0.0, 5, 0),
(17072, 602, 0.415, 0, 0.0, 1, 0),
(17076, 603, 0.791, 0, 0.0, 2, 0),
(17077, 604, 0.516, 0, 0.0, 0, 0),
(17078, 605, 1, 0, 0.0, 1, 0),
(17102, 606, 1, 0, 0.0, 0, 0),
(17103, 607, 1.931, 0, 0.0, 3, 0),
(17105, 608, 1.931, 0, 0.0, 2, 0),
(17106, 609, 0.766, 0, 0.0, 0, 0),
(17107, 610, 1, 0, 0.0, 0, 0),
(17108, 611, 1, 0, 0.0, 0, 0),
(17109, 612, 1, 0, 0.0, 1, 0),
(17110, 613, 1, 0, 0.0, 0, 0),
(17111, 614, 1, 0, 0.0, 1, 0),
(17113, 615, 1.015, 0, 0.0, 2, 0),
(17562, 616, 1, 0, 0.0, 1, 0),
(17563, 617, 1, 0, 0.0, 0, 0),
(17564, 618, 1, 0, 0.0, 0, 0),
(17565, 619, 1, 0, 0.0, 0, 0),
(17566, 620, 1, 0, 0.0, 1, 0),
(17567, 621, 1, 0, 0.0, 1, 0),
(17568, 622, 1, 0, 0.0, 1, 0),
(17569, 623, 1, 0, 0.0, 1, 0),
(17570, 624, 1, 0, 0.0, 1, 0),
(17571, 625, 1, 0, 0.0, 1, 0),
(17572, 626, 1, 0, 0.0, 1, 0),
(17573, 627, 1, 0, 0.0, 1, 0),
(17574, 628, 1, 0, 0.0, 0, 0),
(17575, 629, 1, 0, 0.0, 0, 0),
(17576, 630, 1, 0, 0.0, 1, 0),
(17577, 631, 1, 0, 0.0, 2, 0),
(17578, 632, 1, 0, 0.0, 1, 0),
(17579, 633, 1, 0, 0.0, 1, 0),
(17580, 634, 1, 0, 0.0, 1, 0),
(17581, 635, 1, 0, 0.0, 1, 0),
(17582, 636, 1, 0, 0.0, 0, 0),
(17583, 637, 1, 0, 0.0, 1, 0),
(17584, 638, 1, 0, 0.0, 2, 0),
(17585, 639, 1, 0, 0.0, 0, 0),
(17586, 640, 1, 0, 0.0, 1, 0),
(17587, 641, 1, 0, 0.0, 0, 0),
(17588, 642, 1, 0, 0.0, 2, 0),
(17589, 643, 1, 0, 0.0, 0, 0),
(17590, 644, 1, 0, 0.0, 1, 0),
(17591, 645, 1, 0, 0.0, 1, 0),
(17592, 646, 1, 0, 0.0, 1, 0),
(17593, 647, 1, 0, 0.0, 1, 0),
(17594, 648, 1, 0, 0.0, 1, 0),
(17595, 649, 1, 0, 0.0, 0, 0),
(17596, 650, 1, 0, 0.0, 2, 0),
(17597, 651, 1, 0, 0.0, 0, 0),
(17598, 652, 1, 0, 0.0, 1, 0),
(17599, 653, 1, 0, 0.0, 1, 0),
(17600, 654, 1, 0, 0.0, 1, 0),
(17601, 655, 1, 0, 0.0, 1, 0),
(17602, 656, 1, 0, 0.0, 1, 0),
(17603, 657, 1, 0, 0.0, 1, 0),
(17604, 658, 1, 0, 0.0, 1, 0),
(17605, 659, 1, 0, 0.0, 1, 0),
(17606, 660, 1, 0, 0.0, 0, 0),
(17607, 661, 1, 0, 0.0, 1, 0),
(17608, 662, 1, 0, 0.0, 1, 0),
(17609, 663, 1, 0, 0.0, 0, 0),
(17610, 664, 1, 0, 0.0, 1, 0),
(17611, 665, 1, 0, 0.0, 1, 0),
(17612, 666, 1, 0, 0.0, 1, 0),
(17613, 667, 1, 0, 0.0, 1, 0),
(17614, 668, 1, 0, 0.0, 0, 0),
(17615, 669, 1, 0, 0.0, 0, 0),
(17616, 670, 1, 0, 0.0, 1, 0),
(17617, 671, 1, 0, 0.0, 2, 0),
(17618, 672, 1, 0, 0.0, 1, 0),
(17619, 673, 1, 0, 0.0, 0, 0),
(17620, 674, 1, 0, 0.0, 2, 0),
(17621, 675, 1, 0, 0.0, 0, 0),
(17622, 676, 1, 0, 0.0, 1, 0),
(17623, 677, 1, 0, 0.0, 1, 0),
(17624, 678, 1, 0, 0.0, 1, 0),
(17625, 679, 1, 0, 0.0, 1, 0),
(18022, 680, 1, 0, 0.0, 0, 0),
(18047, 681, 1, 0, 0.0, 0, 0),
(18048, 682, 1.931, 0, 0.0, 1, 0),
(18102, 683, 1, 0, 0.0, 1, 0),
(18103, 684, 1, 0, 0.0, 2, 0),
(18104, 685, 1, 0, 0.0, 0, 0),
(18202, 686, 0.437, 0, 0.0, 0, 0),
(18203, 687, 0.453, 0, 0.0, 0, 0),
(18205, 688, 1, 0, 0.0, 3, 0),
(18208, 689, 1, 0, 0.0, 1, 0),
(18263, 690, 1, 0, 0.0, 0, 0),
(18282, 691, 0.415, 0, 0.0, 2, 0),
(18366, 692, 1, 0, 0.0, 1, 0),
(18367, 693, 1, 0, 0.0, 1, 0),
(18368, 694, 1, 0, 0.0, 1, 0),
(18369, 695, 1, 0, 0.0, 1, 0),
(18372, 696, 0.507, 0, 0.0, 1, 0),
(18373, 697, 1, 0, 0.0, 1, 0),
(18374, 698, 1, 0, 0.0, 0, 0),
(18375, 699, 1, 0, 0.0, 0, 0),
(18376, 700, 0.445, 0, 0.0, 0, 0),
(18377, 701, 1, 0, 0.0, 1, 0),
(18378, 702, 1, 0, 0.0, 1, 0),
(18379, 703, 1, 0, 0.0, 0, 0),
(18380, 704, 1, 0, 0.0, 1, 0),
(18381, 705, 1, 0, 0.0, 1, 0),
(18383, 706, 1, 0, 0.0, 1, 0),
(18384, 707, 1, 0, 0.0, 1, 0),
(18385, 708, 1, 0, 0.0, 1, 0),
(18386, 709, 1, 0, 0.0, 2, 0),
(18387, 710, 1, 0, 0.0, 0, 0),
(18388, 711, 0.415, 0, 0.0, 0, 0),
(18389, 712, 1, 0, 0.0, 1, 0),
(18390, 713, 1, 0, 0.0, 1, 0),
(18391, 714, 1, 0, 0.0, 1, 0),
(18392, 715, 0.437, 0, 0.0, 0, 0),
(18393, 716, 1, 0, 0.0, 1, 0),
(18395, 717, 1, 0, 0.0, 1, 0),
(18396, 718, 1.931, 0, 0.0, 1, 0),
(18397, 719, 1, 0, 0.0, 0, 0),
(18398, 720, 1, 0, 0.0, 0, 0),
(18399, 721, 1, 0, 0.0, 0, 0),
(18403, 722, 1, 0, 0.0, 1, 0),
(18404, 723, 1, 0, 0.0, 3, 0),
(18405, 724, 1, 0, 0.0, 1, 0),
(18407, 725, 1, 0, 0.0, 1, 0),
(18408, 726, 1, 0, 0.0, 1, 0),
(18409, 727, 1, 0, 0.0, 0, 0),
(18413, 728, 1, 0, 0.0, 1, 0),
(18420, 729, 0.791, 0, 0.0, 1, 0),
(18421, 730, 1, 0, 0.0, 1, 0),
(18424, 731, 1, 0, 0.0, 0, 0),
(18429, 732, 1, 0, 0.0, 0, 0),
(18434, 733, 1, 0, 0.0, 0, 0),
(18443, 734, 1, 0, 0.0, 0, 0),
(18445, 735, 1, 0, 0.0, 0, 0),
(18448, 736, 1, 0, 0.0, 0, 0),
(18452, 737, 1, 0, 0.0, 0, 0),
(18454, 738, 1, 0, 0.0, 0, 0),
(18456, 739, 1, 0, 0.0, 0, 0),
(18485, 740, 0.766, 0, 0.0, 0, 0),
(18486, 741, 1, 0, 0.0, 0, 0),
(18490, 742, 1, 0, 0.0, 3, 0),
(18493, 743, 1, 0, 0.0, 1, 0),
(18494, 744, 1, 0, 0.0, 1, 0),
(18495, 745, 1, 0, 0.0, 1, 0),
(18496, 746, 1, 0, 0.0, 1, 0),
(18497, 747, 1, 0, 0.0, 1, 0),
(18498, 748, 0.445, 0, 0.0, 0, 0),
(18499, 749, 0.422, 0, 0.0, 1, 0),
(18500, 750, 1, 0, 0.0, 1, 0),
(18502, 751, 0.884, 0, 0.0, 3, 0),
(18503, 752, 1, 0, 0.0, 1, 0),
(18504, 753, 1, 0, 0.0, 0, 0),
(18505, 754, 1, 0, 0.0, 1, 0),
(18506, 755, 1, 0, 0.0, 0, 0),
(18507, 756, 1, 0, 0.0, 1, 0),
(18509, 757, 1, 0, 0.0, 1, 0),
(18510, 758, 1, 0, 0.0, 1, 0),
(18511, 759, 1, 0, 0.0, 1, 0),
(18520, 760, 0.791, 0, 0.0, 1, 0),
(18521, 761, 1, 0, 0.0, 1, 0),
(18522, 762, 1, 0, 0.0, 0, 0),
(18523, 763, 0.965, 0, 0.0, 1, 0),
(18524, 764, 1, 0, 0.0, 1, 0),
(18525, 765, 1, 0, 0.0, 1, 0),
(18526, 766, 1, 0, 0.0, 1, 0),
(18527, 767, 1, 0, 0.0, 1, 0),
(18528, 768, 1, 0, 0.0, 1, 0),
(18529, 769, 1, 0, 0.0, 0, 0),
(18530, 770, 1, 0, 0.0, 1, 0),
(18531, 771, 0.884, 0, 0.0, 1, 0),
(18532, 772, 1, 0, 0.0, 0, 0),
(18533, 773, 1, 0, 0.0, 0, 0),
(18534, 774, 1.015, 0, 0.0, 3, 0),
(18538, 775, 0.791, 0, 0.0, 1, 0),
(18541, 776, 1, 0, 0.0, 2, 0),
(18542, 777, 0.884, 0, 0.0, 1, 0),
(18544, 778, 1, 0, 0.0, 0, 0),
(18545, 779, 1, 0, 0.0, 1, 0),
(18546, 780, 1, 0, 0.0, 1, 0),
(18547, 781, 1, 0, 0.0, 1, 0),
(18608, 782, 1.015, 0, 0.0, 4, 0),
(18609, 783, 1.015, 0, 0.0, 4, 0),
(18676, 784, 1, 0, 0.0, 1, 0),
(18678, 785, 1, 0, 0.0, 0, 0),
(18680, 786, 0.405, 0, 0.0, 0, 0),
(18681, 787, 1, 0, 0.0, 1, 0),
(18682, 788, 1, 0, 0.0, 1, 0),
(18683, 789, 0.445, 0, 0.0, 0, 0),
(18684, 790, 1, 0, 0.0, 0, 0),
(18686, 791, 1, 0, 0.0, 0, 0),
(18689, 792, 1, 0, 0.0, 0, 0),
(18690, 793, 1, 0, 0.0, 1, 0),
(18691, 794, 1, 0, 0.0, 1, 0),
(18693, 795, 1, 0, 0.0, 1, 0),
(18695, 796, 0.965, 0, 0.0, 0, 0),
(18702, 797, 1, 0, 0.0, 1, 0),
(18713, 798, 0.405, 0, 0.0, 2, 0),
(18715, 799, 1.015, 0, 0.0, 2, 0),
(18716, 800, 1, 0, 0.0, 1, 0),
(18717, 801, 1.015, 0, 0.0, 1, 0),
(18718, 802, 1, 0, 0.0, 0, 0),
(18720, 803, 1, 0, 0.0, 1, 0),
(18721, 804, 1, 0, 0.0, 1, 0),
(18722, 805, 1, 0, 0.0, 1, 0),
(18723, 806, 1, 0, 0.0, 1, 0),
(18728, 807, 1, 0, 0.0, 1, 0),
(18730, 808, 1, 0, 0.0, 0, 0),
(18734, 809, 1, 0, 0.0, 0, 0),
(18735, 810, 1, 0, 0.0, 1, 0),
(18736, 811, 1, 0, 0.0, 1, 0),
(18737, 812, 0.445, 0, 0.0, 0, 0),
(18738, 813, 0.415, 0, 0.0, 0, 0),
(18739, 814, 1, 0, 0.0, 0, 0),
(18740, 815, 1, 0, 0.0, 1, 0),
(18741, 816, 1, 0, 0.0, 0, 0),
(18742, 817, 1, 0, 0.0, 0, 0),
(18754, 818, 1, 0, 0.0, 1, 0),
(18755, 819, 0.415, 0, 0.0, 0, 0),
(18756, 820, 0.399, 0, 0.0, 0, 0),
(18761, 821, 0.516, 0, 0.0, 0, 0),
(18803, 822, 1.015, 0, 0.0, 0, 0),
(18805, 823, 0.445, 0, 0.0, 1, 0),
(18806, 824, 1, 0, 0.0, 1, 0),
(18807, 825, 1, 0, 0.0, 3, 0),
(18808, 826, 1, 0, 0.0, 1, 0),
(18809, 827, 1, 0, 0.0, 1, 0),
(18810, 828, 1, 0, 0.0, 1, 0),
(18811, 829, 1, 0, 0.0, 0, 0),
(18812, 830, 1, 0, 0.0, 1, 0),
(18813, 831, 1, 0, 0.0, 1, 0),
(18814, 832, 1, 0, 0.0, 1, 0),
(18817, 833, 1, 0, 0.0, 0, 0),
(18821, 834, 1, 0, 0.0, 1, 0),
(18822, 835, 0.791, 0, 0.0, 0, 0),
(18823, 836, 1, 0, 0.0, 1, 0),
(18824, 837, 1, 0, 0.0, 1, 0),
(18825, 838, 0.399, 0, 0.0, 1, 0),
(18826, 839, 0.399, 0, 0.0, 1, 0),
(18827, 840, 0.445, 0, 0.0, 1, 0),
(18828, 841, 0.445, 0, 0.0, 1, 0),
(18829, 842, 1, 0, 0.0, 1, 0),
(18830, 843, 0.791, 0, 0.0, 1, 0),
(18831, 844, 0.791, 0, 0.0, 1, 0),
(18832, 845, 0.445, 0, 0.0, 1, 0),
(18838, 846, 0.445, 0, 0.0, 1, 0),
(18840, 847, 0.445, 0, 0.0, 1, 0),
(18842, 848, 1.015, 0, 0.0, 3, 0),
(18843, 849, 0.453, 0, 0.0, 1, 0),
(18844, 850, 0.453, 0, 0.0, 1, 0),
(18847, 851, 0.437, 0, 0.0, 1, 0),
(18848, 852, 0.437, 0, 0.0, 1, 0),
(18861, 853, 1, 0, 0.0, 1, 0),
(18865, 854, 0.445, 0, 0.0, 1, 0),
(18866, 855, 0.445, 0, 0.0, 1, 0),
(18867, 856, 0.791, 0, 0.0, 1, 0),
(18868, 857, 0.791, 0, 0.0, 1, 0),
(18869, 858, 0.791, 0, 0.0, 1, 0),
(18870, 859, 1, 0, 0.0, 1, 0),
(18871, 860, 0.791, 0, 0.0, 1, 0),
(18872, 861, 1, 0, 0.0, 0, 0),
(18873, 862, 1.015, 0, 0.0, 1, 0),
(18874, 863, 1.015, 0, 0.0, 1, 0),
(18875, 864, 1, 0, 0.0, 1, 0),
(18876, 865, 0.791, 0, 0.0, 1, 0),
(18877, 866, 0.791, 0, 0.0, 1, 0),
(18878, 867, 1.931, 0, 0.0, 1, 0),
(19049, 868, 1, 0, 0.0, 0, 0),
(19050, 869, 1, 0, 0.0, 0, 0),
(19057, 870, 1, 0, 0.0, 0, 0),
(19058, 871, 1, 0, 0.0, 1, 0),
(19059, 872, 1, 0, 0.0, 0, 0),
(19085, 873, 1, 0, 0.0, 1, 0),
(19086, 874, 1, 0, 0.0, 1, 0),
(19087, 875, 1, 0, 0.0, 0, 0),
(19088, 876, 1, 0, 0.0, 0, 0),
(19089, 877, 1, 0, 0.0, 0, 0),
(19090, 878, 1, 0, 0.0, 1, 0),
(19091, 879, 1, 0, 0.0, 0, 0),
(19092, 880, 1, 0, 0.0, 0, 0),
(19093, 881, 1, 0, 0.0, 0, 0),
(19094, 882, 1, 0, 0.0, 1, 0),
(19096, 883, 1, 0, 0.0, 0, 0),
(19098, 884, 1, 0, 0.0, 0, 0),
(19099, 885, 0.445, 0, 0.0, 0, 0),
(19100, 886, 0.445, 0, 0.0, 0, 0),
(19101, 887, 1.015, 0, 0.0, 1, 0),
(19102, 888, 1.015, 0, 0.0, 1, 0),
(19103, 889, 0.445, 0, 0.0, 0, 0),
(19104, 890, 0.445, 0, 0.0, 0, 0),
(19105, 891, 1, 0, 0.0, 1, 0),
(19106, 892, 0.791, 0, 0.0, 0, 0),
(19107, 893, 0.415, 0, 0.0, 0, 0),
(19108, 894, 0.516, 0, 0.0, 1, 0),
(19109, 895, 1, 0, 0.0, 1, 0),
(19110, 896, 0.445, 0, 0.0, 0, 0),
(19111, 897, 1, 0, 0.0, 0, 0),
(19112, 898, 1, 0, 0.0, 0, 0),
(19113, 899, 1, 0, 0.0, 0, 0),
(19130, 900, 0.516, 0, 0.0, 1, 0),
(19131, 901, 1, 0, 0.0, 1, 0),
(19132, 902, 1, 0, 0.0, 1, 0),
(19133, 903, 1, 0, 0.0, 1, 0),
(19134, 904, 1, 0, 0.0, 3, 0),
(19136, 905, 1, 0, 0.0, 3, 0),
(19137, 906, 1, 0, 0.0, 3, 0),
(19138, 907, 1, 0, 0.0, 0, 0),
(19140, 908, 1, 0, 0.0, 1, 0),
(19142, 909, 0.965, 0, 0.0, 1, 0),
(19143, 910, 1, 0, 0.0, 1, 0),
(19144, 911, 1, 0, 0.0, 0, 0),
(19146, 912, 1, 0, 0.0, 0, 0),
(19157, 913, 1, 0, 0.0, 0, 0),
(19162, 914, 1, 0, 0.0, 1, 0),
(19163, 915, 1, 0, 0.0, 0, 0),
(19164, 916, 1, 0, 0.0, 0, 0),
(19165, 917, 1, 0, 0.0, 1, 0),
(19167, 918, 0.791, 0, 0.0, 1, 0),
(19168, 919, 0.627, 0, 0.0, 1, 0),
(19308, 920, 0.965, 0, 0.0, 1, 0),
(19309, 921, 0.965, 0, 0.0, 1, 0),
(19310, 922, 0.965, 0, 0.0, 1, 0),
(19311, 923, 0.965, 0, 0.0, 1, 0),
(19312, 924, 0.965, 0, 0.0, 1, 0),
(19315, 925, 0.965, 0, 0.0, 1, 0),
(19323, 926, 0.791, 0, 0.0, 1, 0),
(19325, 927, 1, 0, 0.0, 3, 0),
(19334, 928, 0.791, 0, 0.0, 0, 0),
(19335, 929, 0.627, 0, 0.0, 1, 0),
(19346, 930, 0.445, 0, 0.0, 0, 0),
(19347, 931, 1.931, 0, 0.0, 1, 0),
(19348, 932, 0.766, 0, 0.0, 1, 0),
(19349, 933, 0.422, 0, 0.0, 2, 0),
(19351, 934, 0.627, 0, 0.0, 1, 0),
(19352, 935, 0.445, 0, 0.0, 0, 0),
(19353, 936, 0.791, 0, 0.0, 0, 0),
(19354, 937, 0.884, 0, 0.0, 1, 0),
(19355, 938, 1.015, 0, 0.0, 1, 0),
(19356, 939, 1.015, 0, 0.0, 3, 0),
(19357, 940, 1.015, 0, 0.0, 0, 0),
(19358, 941, 0.791, 0, 0.0, 1, 0),
(19360, 942, 1.931, 0, 0.0, 1, 0),
(19362, 943, 0.445, 0, 0.0, 0, 0),
(19365, 944, 0.453, 0, 0.0, 1, 0),
(19366, 945, 0.965, 0, 0.0, 1, 0),
(19367, 946, 0.516, 0, 0.0, 1, 0),
(19368, 947, 0.415, 0, 0.0, 0, 0),
(19369, 948, 1, 0, 0.0, 0, 0),
(19370, 949, 1, 0, 0.0, 1, 0),
(19371, 950, 1, 0, 0.0, 0, 0),
(19372, 951, 1, 0, 0.0, 0, 0),
(19373, 952, 1, 0, 0.0, 0, 0),
(19374, 953, 1, 0, 0.0, 3, 0),
(19375, 954, 1, 0, 0.0, 3, 0),
(19376, 955, 1, 0, 0.0, 0, 0),
(19377, 956, 1, 0, 0.0, 1, 0),
(19378, 957, 1, 0, 0.0, 1, 0),
(19380, 958, 1, 0, 0.0, 2, 0),
(19381, 959, 1, 0, 0.0, 2, 0),
(19382, 960, 1, 0, 0.0, 1, 0),
(19383, 961, 1, 0, 0.0, 1, 0),
(19384, 962, 1, 0, 0.0, 2, 0),
(19385, 963, 1, 0, 0.0, 3, 0),
(19386, 964, 1, 0, 0.0, 1, 0),
(19387, 965, 1, 0, 0.0, 1, 0),
(19388, 966, 1, 0, 0.0, 1, 0),
(19390, 967, 1, 0, 0.0, 1, 0),
(19391, 968, 1, 0, 0.0, 0, 0),
(19392, 969, 1, 0, 0.0, 0, 0),
(19393, 970, 1, 0, 0.0, 1, 0),
(19394, 971, 1, 0, 0.0, 1, 0),
(19396, 972, 1, 0, 0.0, 2, 0),
(19397, 973, 1, 0, 0.0, 1, 0),
(19399, 974, 1, 0, 0.0, 0, 0),
(19400, 975, 1, 0, 0.0, 1, 0),
(19401, 976, 1, 0, 0.0, 3, 0),
(19402, 977, 1, 0, 0.0, 0, 0),
(19403, 978, 1, 0, 0.0, 3, 0),
(19405, 979, 1, 0, 0.0, 0, 0),
(19407, 980, 1, 0, 0.0, 1, 0),
(19426, 981, 1, 0, 0.0, 1, 0),
(19430, 982, 1, 0, 0.0, 1, 0),
(19432, 983, 1, 0, 0.0, 0, 0),
(19433, 984, 1, 0, 0.0, 0, 0),
(19434, 985, 1, 0, 0.0, 1, 0),
(19435, 986, 0.516, 0, 0.0, 0, 0),
(19436, 987, 1, 0, 0.0, 0, 0),
(19437, 988, 1, 0, 0.0, 1, 0),
(19438, 989, 1, 0, 0.0, 3, 0),
(19491, 990, 1, 0, 0.0, 0, 0),
(19510, 991, 1, 0, 0.0, 0, 0),
(19514, 992, 1, 0, 0.0, 0, 0),
(19518, 993, 1, 0, 0.0, 1, 0),
(19522, 994, 1, 0, 0.0, 1, 0),
(19526, 995, 1, 0, 0.0, 1, 0),
(19530, 996, 1, 0, 0.0, 1, 0),
(19534, 997, 1, 0, 0.0, 0, 0),
(19538, 998, 1, 0, 0.0, 0, 0),
(19542, 999, 0.445, 0, 0.0, 0, 0),
(19546, 1000, 0.445, 0, 0.0, 0, 0),
(19550, 1001, 0.445, 0, 0.0, 0, 0),
(19554, 1002, 0.445, 0, 0.0, 0, 0),
(19558, 1003, 0.405, 0, 0.0, 0, 0),
(19562, 1004, 0.405, 0, 0.0, 0, 0),
(19566, 1005, 1.015, 0, 0.0, 0, 0),
(19570, 1006, 1.015, 0, 0.0, 0, 0),
(19575, 1007, 1, 0, 0.0, 1, 0),
(19576, 1008, 1, 0, 0.0, 1, 0),
(19577, 1009, 1, 0, 0.0, 5, 0),
(19578, 1010, 1, 0, 0.0, 0, 0),
(19582, 1011, 1, 0, 0.0, 0, 0),
(19585, 1012, 1, 0, 0.0, 0, 0),
(19586, 1013, 1, 0, 0.0, 0, 0),
(19587, 1014, 1, 0, 0.0, 0, 0),
(19588, 1015, 1, 0, 0.0, 0, 0),
(19592, 1016, 1, 0, 0.0, 1, 0),
(19593, 1017, 1, 0, 0.0, 1, 0),
(19594, 1018, 1, 0, 0.0, 1, 0),
(19595, 1019, 1, 0, 0.0, 1, 0),
(19599, 1020, 1, 0, 0.0, 1, 0),
(19600, 1021, 1, 0, 0.0, 1, 0),
(19601, 1022, 1, 0, 0.0, 3, 0),
(19603, 1023, 1, 0, 0.0, 1, 0),
(19604, 1024, 1, 0, 0.0, 1, 0),
(19605, 1025, 1, 0, 0.0, 1, 0),
(19607, 1026, 1, 0, 0.0, 0, 0),
(19608, 1027, 1, 0, 0.0, 0, 0),
(19609, 1028, 1, 0, 0.0, 1, 0),
(19611, 1029, 1, 0, 0.0, 0, 0),
(19612, 1030, 1, 0, 0.0, 0, 0),
(19613, 1031, 1, 0, 0.0, 1, 0),
(19615, 1032, 1, 0, 0.0, 0, 0),
(19616, 1033, 1, 0, 0.0, 0, 0),
(19617, 1034, 1, 0, 0.0, 1, 0),
(19619, 1035, 1, 0, 0.0, 0, 0),
(19620, 1036, 1, 0, 0.0, 0, 0),
(19621, 1037, 1, 0, 0.0, 1, 0),
(19682, 1038, 1, 0, 0.0, 3, 0),
(19683, 1039, 1, 0, 0.0, 3, 0),
(19684, 1040, 1, 0, 0.0, 3, 0),
(19685, 1041, 1, 0, 0.0, 1, 0),
(19686, 1042, 1, 0, 0.0, 1, 0),
(19687, 1043, 1, 0, 0.0, 1, 0),
(19688, 1044, 1, 0, 0.0, 0, 0),
(19689, 1045, 1, 0, 0.0, 0, 0),
(19690, 1046, 1, 0, 0.0, 1, 0),
(19691, 1047, 1, 0, 0.0, 0, 0),
(19692, 1048, 1, 0, 0.0, 1, 0),
(19693, 1049, 1, 0, 0.0, 1, 0),
(19694, 1050, 1, 0, 0.0, 1, 0),
(19695, 1051, 1, 0, 0.0, 1, 0),
(19822, 1052, 1, 0, 0.0, 1, 0),
(19823, 1053, 1, 0, 0.0, 1, 0),
(19824, 1054, 1, 0, 0.0, 0, 0),
(19825, 1055, 1, 0, 0.0, 1, 0),
(19826, 1056, 1, 0, 0.0, 1, 0),
(19827, 1057, 1, 0, 0.0, 1, 0),
(19828, 1058, 1, 0, 0.0, 3, 0),
(19829, 1059, 1, 0, 0.0, 1, 0),
(19830, 1060, 1, 0, 0.0, 1, 0),
(19831, 1061, 1, 0, 0.0, 0, 0),
(19832, 1062, 1, 0, 0.0, 1, 0),
(19833, 1063, 1, 0, 0.0, 0, 0),
(19834, 1064, 1, 0, 0.0, 1, 0),
(19835, 1065, 1, 0, 0.0, 1, 0),
(19836, 1066, 1, 0, 0.0, 0, 0),
(19838, 1067, 1, 0, 0.0, 1, 0),
(19839, 1068, 1, 0, 0.0, 1, 0),
(19840, 1069, 1, 0, 0.0, 1, 0),
(19841, 1070, 1, 0, 0.0, 1, 0),
(19842, 1071, 1, 0, 0.0, 1, 0),
(19843, 1072, 1, 0, 0.0, 1, 0),
(19844, 1073, 1, 0, 0.0, 0, 0),
(19845, 1074, 1, 0, 0.0, 1, 0),
(19846, 1075, 1, 0, 0.0, 1, 0),
(19848, 1076, 1, 0, 0.0, 1, 0),
(19849, 1077, 1, 0, 0.0, 1, 0),
(19855, 1078, 1, 0, 0.0, 1, 0),
(19856, 1079, 1, 0, 0.0, 1, 0),
(19857, 1080, 1, 0, 0.0, 3, 0),
(19859, 1081, 0.445, 0, 0.0, 1, 0),
(19861, 1082, 0.516, 0, 0.0, 1, 0),
(19862, 1083, 0.422, 0, 0.0, 6, 0),
(19863, 1084, 1, 0, 0.0, 1, 0),
(19864, 1085, 1.931, 0, 0.0, 1, 0),
(19865, 1086, 0.453, 0, 0.0, 2, 0),
(19867, 1087, 0.627, 0, 0.0, 1, 0),
(19868, 1088, 0.415, 0, 0.0, 0, 0),
(19869, 1089, 1, 0, 0.0, 2, 0),
(19870, 1090, 1, 0, 0.0, 1, 0),
(19871, 1091, 1, 0, 0.0, 3, 0),
(19873, 1092, 1, 0, 0.0, 1, 0),
(19875, 1093, 1, 0, 0.0, 1, 0),
(19876, 1094, 1, 0, 0.0, 1, 0),
(19877, 1095, 1, 0, 0.0, 1, 0),
(19878, 1096, 1, 0, 0.0, 1, 0),
(19884, 1097, 1.015, 0, 0.0, 5, 0),
(19886, 1098, 1, 0, 0.0, 1, 0),
(19887, 1099, 1, 0, 0.0, 1, 0),
(19888, 1100, 1, 0, 0.0, 3, 0),
(19889, 1101, 1, 0, 0.0, 0, 0),
(19890, 1102, 1.931, 0, 0.0, 3, 0),
(19892, 1103, 1, 0, 0.0, 1, 0),
(19893, 1104, 1, 0, 0.0, 3, 0),
(19894, 1105, 1, 0, 0.0, 3, 0),
(19895, 1106, 1, 0, 0.0, 1, 0),
(19896, 1107, 0.453, 0, 0.0, 1, 0),
(19897, 1108, 1, 0, 0.0, 1, 0),
(19898, 1109, 1, 0, 0.0, 1, 0),
(19899, 1110, 1, 0, 0.0, 1, 0),
(19900, 1111, 1.015, 0, 0.0, 2, 0),
(19903, 1112, 1.931, 0, 0.0, 1, 0),
(19904, 1113, 1, 0, 0.0, 2, 0),
(19905, 1114, 1, 0, 0.0, 1, 0),
(19906, 1115, 1, 0, 0.0, 1, 0),
(19907, 1116, 1, 0, 0.0, 1, 0),
(19908, 1117, 0.445, 0, 0.0, 0, 0),
(19909, 1118, 1.015, 0, 0.0, 1, 0),
(19912, 1119, 1, 0, 0.0, 3, 0),
(19913, 1120, 1, 0, 0.0, 1, 0),
(19915, 1121, 0.766, 0, 0.0, 0, 0),
(19919, 1122, 1, 0, 0.0, 0, 0),
(19920, 1123, 1, 0, 0.0, 0, 0),
(19921, 1124, 0.445, 0, 0.0, 0, 0),
(19922, 1125, 0.965, 0, 0.0, 3, 0),
(19923, 1126, 1, 0, 0.0, 1, 0),
(19925, 1127, 1, 0, 0.0, 1, 0),
(19926, 1128, 1, 0, 0.0, 0, 0),
(19927, 1129, 0.516, 0, 0.0, 0, 0),
(19928, 1130, 1, 0, 0.0, 1, 0),
(19929, 1131, 1, 0, 0.0, 3, 0),
(19944, 1132, 0.791, 0, 0.0, 0, 0),
(19945, 1133, 1, 0, 0.0, 1, 0),
(19946, 1134, 0.791, 0, 0.0, 1, 0),
(19964, 1135, 1.931, 0, 0.0, 1, 0),
(19965, 1136, 1.931, 0, 0.0, 1, 0),
(19966, 1137, 0.415, 0, 0.0, 0, 0),
(19968, 1138, 0.627, 0, 0.0, 3, 0),
(19993, 1139, 0.405, 0, 0.0, 0, 0),
(19998, 1140, 1, 0, 0.0, 1, 0),
(19999, 1141, 1, 0, 0.0, 3, 0),
(20032, 1142, 1, 0, 0.0, 1, 0),
(20033, 1143, 1, 0, 0.0, 3, 0),
(20034, 1144, 1, 0, 0.0, 3, 0),
(20038, 1145, 0.405, 0, 0.0, 0, 0),
(20041, 1146, 1, 0, 0.0, 1, 0),
(20042, 1147, 1, 0, 0.0, 1, 0),
(20043, 1148, 1, 0, 0.0, 1, 0),
(20044, 1149, 1, 0, 0.0, 1, 0),
(20045, 1150, 1, 0, 0.0, 1, 0),
(20046, 1151, 1, 0, 0.0, 1, 0),
(20047, 1152, 1, 0, 0.0, 3, 0),
(20048, 1153, 1, 0, 0.0, 0, 0),
(20049, 1154, 1, 0, 0.0, 0, 0),
(20050, 1155, 1, 0, 0.0, 0, 0),
(20051, 1156, 1, 0, 0.0, 0, 0),
(20052, 1157, 1, 0, 0.0, 0, 0),
(20053, 1158, 1, 0, 0.0, 0, 0),
(20054, 1159, 1, 0, 0.0, 2, 0),
(20055, 1160, 1, 0, 0.0, 0, 0),
(20056, 1161, 1, 0, 0.0, 0, 0),
(20057, 1162, 1, 0, 0.0, 0, 0),
(20058, 1163, 1, 0, 0.0, 0, 0),
(20059, 1164, 1, 0, 0.0, 0, 0),
(20060, 1165, 1, 0, 0.0, 0, 0),
(20061, 1166, 1, 0, 0.0, 1, 0),
(20068, 1167, 1, 0, 0.0, 0, 0),
(20069, 1168, 1.015, 0, 0.0, 3, 0),
(20070, 1169, 1.931, 0, 0.0, 3, 0),
(20073, 1170, 1, 0, 0.0, 0, 0),
(20134, 1171, 1, 0, 0.0, 0, 0),
(20135, 1172, 1, 0, 0.0, 0, 0),
(20136, 1173, 1, 0, 0.0, 0, 0),
(20137, 1174, 1, 0, 0.0, 0, 0),
(20138, 1175, 1, 0, 0.0, 0, 0),
(20139, 1176, 1, 0, 0.0, 0, 0),
(20140, 1177, 1, 0, 0.0, 0, 0),
(20141, 1178, 1, 0, 0.0, 0, 0),
(20142, 1179, 1, 0, 0.0, 0, 0),
(20143, 1180, 1, 0, 0.0, 0, 0),
(20144, 1181, 1, 0, 0.0, 0, 0),
(20145, 1182, 1, 0, 0.0, 0, 0),
(20146, 1183, 0.415, 0, 0.0, 0, 0),
(20149, 1184, 0.791, 0, 0.0, 0, 0),
(20150, 1185, 1, 0, 0.0, 1, 0),
(20154, 1186, 1, 0, 0.0, 0, 0),
(20158, 1187, 1, 0, 0.0, 0, 0),
(20159, 1188, 1, 0, 0.0, 2, 0),
(20163, 1189, 1, 0, 0.0, 3, 0),
(20167, 1190, 1, 0, 0.0, 0, 0),
(20171, 1191, 1, 0, 0.0, 1, 0),
(20175, 1192, 1, 0, 0.0, 0, 0),
(20176, 1193, 1, 0, 0.0, 1, 0),
(20177, 1194, 1, 0, 0.0, 1, 0),
(20181, 1195, 1, 0, 0.0, 0, 0),
(20184, 1196, 1, 0, 0.0, 0, 0),
(20186, 1197, 1, 0, 0.0, 0, 0),
(20190, 1198, 1, 0, 0.0, 1, 0),
(20194, 1199, 1, 0, 0.0, 0, 0),
(20195, 1200, 1, 0, 0.0, 1, 0),
(20199, 1201, 1, 0, 0.0, 0, 0),
(20203, 1202, 1, 0, 0.0, 0, 0),
(20204, 1203, 1, 0, 0.0, 1, 0),
(20208, 1204, 1, 0, 0.0, 0, 0),
(20212, 1205, 1, 0, 0.0, 0, 0),
(20213, 1206, 1, 0, 0.0, 0, 0),
(20214, 1207, 1.931, 0, 0.0, 3, 0),
(20215, 1208, 1, 0, 0.0, 0, 0),
(20216, 1209, 1, 0, 0.0, 1, 0),
(20217, 1210, 1, 0, 0.0, 0, 0),
(20220, 1211, 1.015, 0, 0.0, 3, 0),
(20257, 1212, 1, 0, 0.0, 0, 0),
(20258, 1213, 1.015, 0, 0.0, 1, 0),
(20259, 1214, 1, 0, 0.0, 1, 0),
(20260, 1215, 1, 0, 0.0, 1, 0),
(20261, 1216, 1, 0, 0.0, 1, 0),
(20262, 1217, 1, 0, 0.0, 1, 0),
(20263, 1218, 1, 0, 0.0, 0, 0),
(20264, 1219, 1, 0, 0.0, 1, 0),
(20265, 1220, 1, 0, 0.0, 2, 0),
(20266, 1221, 1, 0, 0.0, 1, 0),
(20267, 1222, 1, 0, 0.0, 0, 0),
(20268, 1223, 1, 0, 0.0, 0, 0),
(20269, 1224, 1, 0, 0.0, 0, 0),
(20270, 1225, 1, 0, 0.0, 0, 0),
(20271, 1226, 1, 0, 0.0, 0, 0),
(20272, 1227, 1, 0, 0.0, 0, 0),
(20273, 1228, 1, 0, 0.0, 0, 0),
(20274, 1229, 1, 0, 0.0, 0, 0),
(20275, 1230, 1, 0, 0.0, 0, 0),
(20276, 1231, 1, 0, 0.0, 0, 0),
(20277, 1232, 1, 0, 0.0, 0, 0),
(20278, 1233, 0.405, 0, 0.0, 0, 0),
(20279, 1234, 0.445, 0, 0.0, 0, 0),
(20295, 1235, 1, 0, 0.0, 0, 0),
(20324, 1236, 1, 0, 0.0, 0, 0),
(20325, 1237, 1, 0, 0.0, 0, 0),
(20326, 1238, 1, 0, 0.0, 0, 0),
(20327, 1239, 1, 0, 0.0, 0, 0),
(20328, 1240, 1, 0, 0.0, 0, 0),
(20329, 1241, 1, 0, 0.0, 0, 0),
(20330, 1242, 1, 0, 0.0, 0, 0),
(20331, 1243, 1, 0, 0.0, 0, 0),
(20332, 1244, 1, 0, 0.0, 0, 0),
(20333, 1245, 1, 0, 0.0, 0, 0),
(20334, 1246, 1.015, 0, 0.0, 0, 0),
(20335, 1247, 0.516, 0, 0.0, 0, 0),
(20336, 1248, 1, 0, 0.0, 0, 0),
(20380, 1249, 1, 0, 0.0, 0, 0),
(20479, 1250, 1, 0, 0.0, 2, 0),
(20480, 1251, 1, 0, 0.0, 2, 0),
(20481, 1252, 1, 0, 0.0, 2, 0),
(20487, 1253, 1.015, 0, 0.0, 2, 0),
(20488, 1254, 0.405, 0, 0.0, 2, 0),
(20549, 1255, 1, 0, 0.0, 1, 0),
(20550, 1256, 1, 0, 0.0, 1, 0),
(20551, 1257, 1, 0, 0.0, 1, 0),
(20578, 1258, 0.445, 0, 0.0, 0, 0),
(20580, 1259, 0.445, 0, 0.0, 0, 0),
(20581, 1260, 1.015, 0, 0.0, 1, 0),
(20582, 1261, 0.965, 0, 0.0, 1, 0),
(20616, 1262, 1, 0, 0.0, 1, 0),
(20617, 1263, 1, 0, 0.0, 0, 0),
(20618, 1264, 1, 0, 0.0, 2, 0),
(20619, 1265, 1, 0, 0.0, 1, 0),
(20621, 1266, 1, 0, 0.0, 0, 0),
(20622, 1267, 1, 0, 0.0, 0, 0),
(20623, 1268, 1, 0, 0.0, 0, 0),
(20624, 1269, 1, 0, 0.0, 0, 0),
(20625, 1270, 1, 0, 0.0, 1, 0),
(20626, 1271, 1, 0, 0.0, 1, 0),
(20627, 1272, 1, 0, 0.0, 1, 0),
(20628, 1273, 1, 0, 0.0, 5, 0),
(20629, 1274, 1, 0, 0.0, 1, 0),
(20630, 1275, 1, 0, 0.0, 1, 0),
(20631, 1276, 1, 0, 0.0, 0, 0),
(20632, 1277, 1, 0, 0.0, 3, 0),
(20633, 1278, 1, 0, 0.0, 0, 0),
(20634, 1279, 1, 0, 0.0, 1, 0),
(20635, 1280, 1, 0, 0.0, 1, 0),
(20637, 1281, 1, 0, 0.0, 1, 0),
(20638, 1282, 1, 0, 0.0, 1, 0),
(20639, 1283, 1, 0, 0.0, 1, 0),
(20648, 1284, 0.507, 0, 0.0, 0, 0),
(20654, 1285, 1.015, 0, 0.0, 1, 0),
(20660, 1286, 0.791, 0, 0.0, 0, 0),
(20663, 1287, 0.405, 0, 0.0, 0, 0),
(20665, 1288, 1, 0, 0.0, 1, 0),
(20666, 1289, 1.931, 0, 0.0, 1, 0),
(20668, 1290, 1, 0, 0.0, 1, 0),
(20671, 1291, 1, 0, 0.0, 1, 0),
(20672, 1292, 0.516, 0, 0.0, 1, 0),
(20674, 1293, 1, 0, 0.0, 1, 0),
(20680, 1294, 1, 0, 0.0, 1, 0),
(20682, 1295, 1, 0, 0.0, 1, 0),
(20683, 1296, 1, 0, 0.0, 1, 0),
(20685, 1297, 1, 0, 0.0, 2, 0),
(20686, 1298, 1, 0, 0.0, 1, 0),
(20688, 1299, 0.422, 0, 0.0, 1, 0),
(20689, 1300, 1, 0, 0.0, 1, 0),
(20691, 1301, 1, 0, 0.0, 0, 0),
(20696, 1302, 0.791, 0, 0.0, 1, 0),
(20697, 1303, 1, 0, 0.0, 1, 0),
(20698, 1304, 1.931, 0, 0.0, 1, 0),
(20699, 1305, 1, 0, 0.0, 1, 0),
(20700, 1306, 1, 0, 0.0, 0, 0),
(20701, 1307, 1, 0, 0.0, 0, 0),
(20702, 1308, 1, 0, 0.0, 0, 0),
(20704, 1309, 1, 0, 0.0, 1, 0),
(20705, 1310, 1, 0, 0.0, 1, 0),
(20706, 1311, 1, 0, 0.0, 1, 0),
(20707, 1312, 1, 0, 0.0, 1, 0),
(20710, 1313, 1, 0, 0.0, 1, 0),
(20711, 1314, 1, 0, 0.0, 1, 0),
(20712, 1315, 1, 0, 0.0, 0, 0),
(20713, 1316, 1, 0, 0.0, 0, 0),
(20714, 1317, 1, 0, 0.0, 1, 0),
(20715, 1318, 1, 0, 0.0, 0, 0),
(20716, 1319, 1, 0, 0.0, 1, 0),
(20717, 1320, 1, 0, 0.0, 1, 0),
(20720, 1321, 1.931, 0, 0.0, 1, 0),
(20721, 1322, 1, 0, 0.0, 0, 0),
(21126, 1323, 0.445, 0, 0.0, 0, 0),
(21128, 1324, 1.015, 0, 0.0, 1, 0),
(21134, 1325, 0.791, 0, 0.0, 0, 0),
(21178, 1326, 1, 0, 0.0, 1, 0),
(21179, 1327, 1, 0, 0.0, 1, 0),
(21182, 1328, 1, 0, 0.0, 3, 0),
(21183, 1329, 1, 0, 0.0, 3, 0),
(21184, 1330, 1, 0, 0.0, 0, 0),
(21185, 1331, 0.965, 0, 0.0, 2, 0),
(21186, 1332, 1, 0, 0.0, 3, 0),
(21187, 1333, 1, 0, 0.0, 1, 0),
(21188, 1334, 1.015, 0, 0.0, 3, 0),
(21189, 1335, 1, 0, 0.0, 2, 0),
(21196, 1336, 1, 0, 0.0, 1, 0),
(21197, 1337, 1, 0, 0.0, 1, 0),
(21198, 1338, 1, 0, 0.0, 1, 0),
(21199, 1339, 1, 0, 0.0, 1, 0),
(21200, 1340, 1, 0, 0.0, 1, 0),
(21201, 1341, 1, 0, 0.0, 1, 0),
(21202, 1342, 1, 0, 0.0, 1, 0),
(21203, 1343, 1, 0, 0.0, 1, 0),
(21204, 1344, 1, 0, 0.0, 1, 0),
(21205, 1345, 1, 0, 0.0, 1, 0),
(21206, 1346, 1, 0, 0.0, 1, 0),
(21207, 1347, 1, 0, 0.0, 1, 0),
(21208, 1348, 1, 0, 0.0, 1, 0),
(21209, 1349, 1, 0, 0.0, 1, 0),
(21210, 1350, 1, 0, 0.0, 1, 0),
(21242, 1351, 0.507, 0, 0.0, 1, 0),
(21244, 1352, 0.445, 0, 0.0, 3, 0),
(21268, 1353, 0.627, 0, 0.0, 2, 0),
(21269, 1354, 0.422, 0, 0.0, 5, 0),
(21273, 1355, 1.015, 0, 0.0, 7, 0),
(21275, 1356, 1.015, 0, 0.0, 1, 0),
(21329, 1357, 1, 0, 0.0, 1, 0),
(21330, 1358, 1, 0, 0.0, 3, 0),
(21331, 1359, 1, 0, 0.0, 1, 0),
(21332, 1360, 1, 0, 0.0, 3, 0),
(21333, 1361, 1, 0, 0.0, 1, 0),
(21334, 1362, 1, 0, 0.0, 7, 0),
(21335, 1363, 1, 0, 0.0, 7, 0),
(21336, 1364, 1, 0, 0.0, 3, 0),
(21337, 1365, 1, 0, 0.0, 7, 0),
(21338, 1366, 1, 0, 0.0, 3, 0),
(21343, 1367, 1, 0, 0.0, 7, 0),
(21344, 1368, 1, 0, 0.0, 3, 0),
(21345, 1369, 1, 0, 0.0, 3, 0),
(21346, 1370, 1, 0, 0.0, 3, 0),
(21347, 1371, 1, 0, 0.0, 7, 0),
(21348, 1372, 1, 0, 0.0, 5, 0),
(21349, 1373, 1, 0, 0.0, 1, 0),
(21350, 1374, 1, 0, 0.0, 5, 0),
(21351, 1375, 1, 0, 0.0, 7, 0),
(21352, 1376, 1, 0, 0.0, 1, 0),
(21353, 1377, 1, 0, 0.0, 3, 0),
(21354, 1378, 1, 0, 0.0, 1, 0),
(21355, 1379, 1, 0, 0.0, 5, 0),
(21356, 1380, 1, 0, 0.0, 3, 0),
(21357, 1381, 1, 0, 0.0, 7, 0),
(21359, 1382, 1, 0, 0.0, 1, 0),
(21360, 1383, 1, 0, 0.0, 3, 0),
(21361, 1384, 1, 0, 0.0, 1, 0),
(21362, 1385, 1, 0, 0.0, 1, 0),
(21364, 1386, 1, 0, 0.0, 3, 0),
(21365, 1387, 1, 0, 0.0, 1, 0),
(21366, 1388, 1, 0, 0.0, 3, 0),
(21367, 1389, 1, 0, 0.0, 1, 0),
(21368, 1390, 1, 0, 0.0, 3, 0),
(21370, 1391, 1, 0, 0.0, 3, 0),
(21372, 1392, 1, 0, 0.0, 3, 0),
(21373, 1393, 1, 0, 0.0, 3, 0),
(21374, 1394, 1, 0, 0.0, 7, 0),
(21375, 1395, 1, 0, 0.0, 3, 0),
(21376, 1396, 1, 0, 0.0, 1, 0),
(21387, 1397, 1, 0, 0.0, 3, 0),
(21388, 1398, 1, 0, 0.0, 1, 0),
(21389, 1399, 1, 0, 0.0, 7, 0),
(21390, 1400, 1, 0, 0.0, 3, 0),
(21391, 1401, 1, 0, 0.0, 1, 0),
(21392, 1402, 0.445, 0, 0.0, 1, 0),
(21393, 1403, 1, 0, 0.0, 1, 0),
(21394, 1404, 1, 0, 0.0, 1, 0),
(21395, 1405, 0.445, 0, 0.0, 0, 0),
(21396, 1406, 1, 0, 0.0, 1, 0),
(21397, 1407, 1, 0, 0.0, 0, 0),
(21398, 1408, 1.931, 0, 0.0, 1, 0),
(21399, 1409, 1, 0, 0.0, 1, 0),
(21400, 1410, 1, 0, 0.0, 1, 0),
(21401, 1411, 0.445, 0, 0.0, 0, 0),
(21402, 1412, 1, 0, 0.0, 0, 0),
(21403, 1413, 1, 0, 0.0, 1, 0),
(21404, 1414, 0.445, 0, 0.0, 1, 0),
(21405, 1415, 1, 0, 0.0, 0, 0),
(21406, 1416, 1, 0, 0.0, 1, 0),
(21407, 1417, 1.015, 0, 0.0, 0, 0),
(21408, 1418, 1, 0, 0.0, 0, 0),
(21409, 1419, 1, 0, 0.0, 1, 0),
(21410, 1420, 1.931, 0, 0.0, 2, 0),
(21411, 1421, 1, 0, 0.0, 0, 0),
(21412, 1422, 1, 0, 0.0, 1, 0),
(21413, 1423, 1.931, 0, 0.0, 3, 0),
(21414, 1424, 1, 0, 0.0, 3, 0),
(21415, 1425, 1, 0, 0.0, 1, 0),
(21416, 1426, 1.931, 0, 0.0, 1, 0),
(21417, 1427, 1, 0, 0.0, 7, 0),
(21418, 1428, 1, 0, 0.0, 1, 0),
(21452, 1429, 1.015, 0, 0.0, 7, 0),
(21453, 1430, 1, 0, 0.0, 1, 0),
(21454, 1431, 1, 0, 0.0, 1, 0),
(21455, 1432, 1, 0, 0.0, 1, 0),
(21456, 1433, 1, 0, 0.0, 3, 0),
(21457, 1434, 1, 0, 0.0, 0, 0),
(21458, 1435, 1, 0, 0.0, 1, 0),
(21459, 1436, 0.415, 0, 0.0, 1, 0),
(21460, 1437, 1, 0, 0.0, 3, 0),
(21461, 1438, 1, 0, 0.0, 3, 0),
(21462, 1439, 1, 0, 0.0, 1, 0),
(21463, 1440, 1, 0, 0.0, 3, 0),
(21464, 1441, 1, 0, 0.0, 3, 0),
(21466, 1442, 1.931, 0, 0.0, 3, 0),
(21467, 1443, 1, 0, 0.0, 0, 0),
(21468, 1444, 1, 0, 0.0, 1, 0),
(21469, 1445, 1, 0, 0.0, 1, 0),
(21470, 1446, 1, 0, 0.0, 1, 0),
(21471, 1447, 0.965, 0, 0.0, 3, 0),
(21472, 1448, 1, 0, 0.0, 3, 0),
(21474, 1449, 1, 0, 0.0, 0, 0),
(21475, 1450, 1, 0, 0.0, 1, 0),
(21476, 1451, 1, 0, 0.0, 1, 0),
(21477, 1452, 1, 0, 0.0, 1, 0),
(21479, 1453, 1, 0, 0.0, 3, 0),
(21480, 1454, 1, 0, 0.0, 0, 0),
(21481, 1455, 1, 0, 0.0, 0, 0),
(21482, 1456, 1, 0, 0.0, 2, 0),
(21483, 1457, 1, 0, 0.0, 5, 0),
(21484, 1458, 1, 0, 0.0, 1, 0),
(21485, 1459, 0.422, 0, 0.0, 1, 0),
(21486, 1460, 1, 0, 0.0, 1, 0),
(21487, 1461, 1, 0, 0.0, 3, 0),
(21489, 1462, 1, 0, 0.0, 1, 0),
(21490, 1463, 1, 0, 0.0, 1, 0),
(21491, 1464, 1, 0, 0.0, 0, 0),
(21492, 1465, 0.791, 0, 0.0, 0, 0),
(21494, 1466, 1, 0, 0.0, 3, 0),
(21495, 1467, 1, 0, 0.0, 1, 0),
(21496, 1468, 1, 0, 0.0, 0, 0),
(21497, 1469, 1, 0, 0.0, 0, 0),
(21500, 1470, 1, 0, 0.0, 1, 0),
(21501, 1471, 1, 0, 0.0, 0, 0),
(21502, 1472, 1, 0, 0.0, 0, 0),
(21503, 1473, 1, 0, 0.0, 1, 0),
(21504, 1474, 1, 0, 0.0, 1, 0),
(21506, 1475, 1, 0, 0.0, 1, 0),
(21507, 1476, 1, 0, 0.0, 1, 0),
(21517, 1477, 1, 0, 0.0, 2, 0),
(21520, 1478, 0.445, 0, 0.0, 0, 0),
(21521, 1479, 1.931, 0, 0.0, 1, 0),
(21522, 1480, 0.445, 0, 0.0, 0, 0),
(21523, 1481, 1.931, 0, 0.0, 1, 0),
(21527, 1482, 1, 0, 0.0, 1, 0),
(21529, 1483, 1, 0, 0.0, 0, 0),
(21530, 1484, 1, 0, 0.0, 0, 0),
(21531, 1485, 1, 0, 0.0, 1, 0),
(21532, 1486, 1, 0, 0.0, 0, 0),
(21563, 1487, 1, 0, 0.0, 3, 0),
(21581, 1488, 1, 0, 0.0, 3, 0),
(21582, 1489, 1, 0, 0.0, 1, 0),
(21583, 1490, 1, 0, 0.0, 1, 0),
(21584, 1491, 1, 0, 0.0, 0, 0),
(21585, 1492, 1, 0, 0.0, 3, 0),
(21586, 1493, 1, 0, 0.0, 6, 0),
(21587, 1494, 1, 0, 0.0, 1, 0),
(21588, 1495, 1, 0, 0.0, 1, 0),
(21594, 1496, 1, 0, 0.0, 0, 0),
(21596, 1497, 1, 0, 0.0, 0, 0),
(21597, 1498, 0.965, 0, 0.0, 7, 0),
(21598, 1499, 1, 0, 0.0, 3, 0),
(21599, 1500, 1, 0, 0.0, 1, 0),
(21600, 1501, 1, 0, 0.0, 1, 0),
(21601, 1502, 1, 0, 0.0, 1, 0),
(21602, 1503, 1, 0, 0.0, 1, 0),
(21603, 1504, 0.516, 0, 0.0, 1, 0),
(21604, 1505, 1, 0, 0.0, 1, 0),
(21605, 1506, 1, 0, 0.0, 0, 0),
(21606, 1507, 1, 0, 0.0, 1, 0),
(21607, 1508, 1, 0, 0.0, 1, 0),
(21608, 1509, 1, 0, 0.0, 3, 0),
(21609, 1510, 1, 0, 0.0, 1, 0),
(21610, 1511, 0.766, 0, 0.0, 1, 0),
(21611, 1512, 1, 0, 0.0, 1, 0),
(21612, 1513, 1, 0, 0.0, 0, 0),
(21613, 1514, 1, 0, 0.0, 0, 0),
(21614, 1515, 1, 0, 0.0, 0, 0),
(21615, 1516, 1, 0, 0.0, 1, 0),
(21616, 1517, 0.405, 0, 0.0, 0, 0),
(21617, 1518, 1, 0, 0.0, 1, 0),
(21618, 1519, 1, 0, 0.0, 0, 0),
(21619, 1520, 1, 0, 0.0, 1, 0),
(21620, 1521, 1, 0, 0.0, 1, 0),
(21621, 1522, 1, 0, 0.0, 1, 0),
(21622, 1523, 1.931, 0, 0.0, 3, 0),
(21623, 1524, 1, 0, 0.0, 3, 0),
(21624, 1525, 1, 0, 0.0, 3, 0),
(21626, 1526, 1, 0, 0.0, 1, 0),
(21635, 1527, 0.791, 0, 0.0, 0, 0),
(21639, 1528, 1, 0, 0.0, 3, 0),
(21645, 1529, 1, 0, 0.0, 0, 0),
(21648, 1530, 1, 0, 0.0, 1, 0),
(21650, 1531, 0.445, 0, 0.0, 1, 0),
(21651, 1532, 1, 0, 0.0, 2, 0),
(21652, 1533, 1, 0, 0.0, 0, 0),
(21663, 1534, 1, 0, 0.0, 1, 0),
(21664, 1535, 1, 0, 0.0, 1, 0),
(21665, 1536, 1, 0, 0.0, 0, 0),
(21666, 1537, 0.965, 0, 0.0, 1, 0),
(21667, 1538, 1, 0, 0.0, 3, 0),
(21668, 1539, 1, 0, 0.0, 3, 0),
(21669, 1540, 1, 0, 0.0, 1, 0),
(21671, 1541, 1, 0, 0.0, 3, 0),
(21672, 1542, 1, 0, 0.0, 1, 0),
(21673, 1543, 0.453, 0, 0.0, 1, 0),
(21674, 1544, 1, 0, 0.0, 1, 0),
(21675, 1545, 1, 0, 0.0, 1, 0),
(21676, 1546, 1, 0, 0.0, 1, 0),
(21677, 1547, 1, 0, 0.0, 2, 0),
(21678, 1548, 1, 0, 0.0, 1, 0),
(21679, 1549, 0.791, 0, 0.0, 0, 0),
(21680, 1550, 1, 0, 0.0, 0, 0),
(21681, 1551, 1, 0, 0.0, 2, 0),
(21682, 1552, 1, 0, 0.0, 0, 0),
(21683, 1553, 1, 0, 0.0, 1, 0),
(21684, 1554, 1, 0, 0.0, 1, 0),
(21686, 1555, 1, 0, 0.0, 1, 0),
(21688, 1556, 1, 0, 0.0, 1, 0),
(21689, 1557, 1, 0, 0.0, 3, 0),
(21690, 1558, 1, 0, 0.0, 1, 0),
(21691, 1559, 1, 0, 0.0, 0, 0),
(21692, 1560, 1, 0, 0.0, 0, 0),
(21693, 1561, 1, 0, 0.0, 1, 0),
(21694, 1562, 1, 0, 0.0, 1, 0),
(21695, 1563, 1, 0, 0.0, 3, 0),
(21696, 1564, 1, 0, 0.0, 0, 0),
(21697, 1565, 1, 0, 0.0, 1, 0),
(21698, 1566, 1, 0, 0.0, 1, 0),
(21699, 1567, 1, 0, 0.0, 0, 0),
(21700, 1568, 1, 0, 0.0, 1, 0),
(21701, 1569, 1, 0, 0.0, 1, 0),
(21703, 1570, 1.015, 0, 0.0, 1, 0),
(21704, 1571, 1, 0, 0.0, 1, 0),
(21705, 1572, 1, 0, 0.0, 1, 0),
(21706, 1573, 1, 0, 0.0, 1, 0),
(21707, 1574, 1, 0, 0.0, 3, 0),
(21708, 1575, 1, 0, 0.0, 0, 0),
(21709, 1576, 1, 0, 0.0, 3, 0),
(21710, 1577, 1, 0, 0.0, 0, 0),
(21712, 1578, 1, 0, 0.0, 1, 0),
(21715, 1579, 0.445, 0, 0.0, 1, 0),
(21779, 1580, 1, 0, 0.0, 1, 0),
(21780, 1581, 1, 0, 0.0, 1, 0),
(21792, 1582, 1, 0, 0.0, 1, 0),
(21800, 1583, 0.415, 0, 0.0, 0, 0),
(21801, 1584, 0.516, 0, 0.0, 2, 0),
(21802, 1585, 1.931, 0, 0.0, 3, 0),
(21803, 1586, 1, 0, 0.0, 3, 0),
(21804, 1587, 1, 0, 0.0, 3, 0),
(21805, 1588, 1, 0, 0.0, 1, 0),
(21806, 1589, 1.015, 0, 0.0, 1, 0),
(21809, 1590, 1, 0, 0.0, 3, 0),
(21810, 1591, 1, 0, 0.0, 1, 0),
(21814, 1592, 1, 0, 0.0, 3, 0),
(21836, 1593, 1, 0, 0.0, 3, 0),
(21837, 1594, 0.445, 0, 0.0, 0, 0),
(21838, 1595, 1, 0, 0.0, 3, 0),
(21839, 1596, 1.931, 0, 0.0, 1, 0),
(21856, 1597, 0.791, 0, 0.0, 0, 0),
(21863, 1598, 1, 0, 0.0, 0, 0),
(21864, 1599, 1, 0, 0.0, 0, 0),
(21865, 1600, 1, 0, 0.0, 0, 0),
(21888, 1601, 1, 0, 0.0, 0, 0),
(21889, 1602, 1, 0, 0.0, 1, 0),
(21890, 1603, 1, 0, 0.0, 1, 0),
(21994, 1604, 1, 0, 0.0, 1, 0),
(21995, 1605, 1, 0, 0.0, 1, 0),
(21996, 1606, 1, 0, 0.0, 1, 0),
(21997, 1607, 1, 0, 0.0, 1, 0),
(21998, 1608, 1, 0, 0.0, 0, 0),
(21999, 1609, 1, 0, 0.0, 1, 0),
(22000, 1610, 1, 0, 0.0, 1, 0),
(22001, 1611, 1, 0, 0.0, 0, 0),
(22002, 1612, 1, 0, 0.0, 0, 0),
(22003, 1613, 1, 0, 0.0, 0, 0),
(22004, 1614, 1, 0, 0.0, 0, 0),
(22005, 1615, 1, 0, 0.0, 1, 0),
(22006, 1616, 1, 0, 0.0, 0, 0),
(22007, 1617, 1, 0, 0.0, 0, 0),
(22008, 1618, 1, 0, 0.0, 0, 0),
(22009, 1619, 1, 0, 0.0, 1, 0),
(22010, 1620, 1, 0, 0.0, 0, 0),
(22011, 1621, 1, 0, 0.0, 0, 0),
(22013, 1622, 1, 0, 0.0, 1, 0),
(22015, 1623, 1, 0, 0.0, 0, 0),
(22016, 1624, 1, 0, 0.0, 0, 0),
(22017, 1625, 1, 0, 0.0, 0, 0),
(22060, 1626, 1, 0, 0.0, 2, 0),
(22061, 1627, 1, 0, 0.0, 0, 0),
(22062, 1628, 1, 0, 0.0, 1, 0),
(22063, 1629, 1, 0, 0.0, 1, 0),
(22064, 1630, 1, 0, 0.0, 1, 0),
(22065, 1631, 1, 0, 0.0, 3, 0),
(22066, 1632, 1, 0, 0.0, 0, 0),
(22067, 1633, 1, 0, 0.0, 1, 0),
(22068, 1634, 1, 0, 0.0, 1, 0),
(22069, 1635, 1, 0, 0.0, 3, 0),
(22070, 1636, 1, 0, 0.0, 1, 0),
(22071, 1637, 1, 0, 0.0, 1, 0),
(22072, 1638, 1, 0, 0.0, 1, 0),
(22073, 1639, 1, 0, 0.0, 1, 0),
(22074, 1640, 1, 0, 0.0, 3, 0),
(22075, 1641, 1, 0, 0.0, 3, 0),
(22076, 1642, 1, 0, 0.0, 1, 0),
(22077, 1643, 1, 0, 0.0, 0, 0),
(22078, 1644, 1, 0, 0.0, 1, 0),
(22079, 1645, 1, 0, 0.0, 1, 0),
(22080, 1646, 1, 0, 0.0, 5, 0),
(22081, 1647, 1, 0, 0.0, 0, 0),
(22082, 1648, 1, 0, 0.0, 1, 0),
(22083, 1649, 1, 0, 0.0, 1, 0),
(22084, 1650, 1, 0, 0.0, 1, 0),
(22085, 1651, 1, 0, 0.0, 1, 0),
(22086, 1652, 1, 0, 0.0, 1, 0),
(22087, 1653, 1, 0, 0.0, 1, 0),
(22088, 1654, 1, 0, 0.0, 1, 0),
(22089, 1655, 1, 0, 0.0, 3, 0),
(22090, 1656, 1, 0, 0.0, 0, 0),
(22091, 1657, 1, 0, 0.0, 3, 0),
(22092, 1658, 1, 0, 0.0, 1, 0),
(22093, 1659, 1, 0, 0.0, 1, 0),
(22095, 1660, 1, 0, 0.0, 1, 0),
(22096, 1661, 1, 0, 0.0, 1, 0),
(22097, 1662, 1, 0, 0.0, 3, 0),
(22098, 1663, 1, 0, 0.0, 1, 0),
(22099, 1664, 1, 0, 0.0, 0, 0),
(22100, 1665, 1, 0, 0.0, 1, 0),
(22101, 1666, 1, 0, 0.0, 1, 0),
(22102, 1667, 1, 0, 0.0, 3, 0),
(22106, 1668, 1, 0, 0.0, 1, 0),
(22107, 1669, 1, 0, 0.0, 1, 0),
(22108, 1670, 1, 0, 0.0, 1, 0),
(22109, 1671, 1, 0, 0.0, 1, 0),
(22110, 1672, 1, 0, 0.0, 0, 0),
(22111, 1673, 1, 0, 0.0, 1, 0),
(22112, 1674, 1, 0, 0.0, 1, 0),
(22113, 1675, 1, 0, 0.0, 1, 0),
(22149, 1676, 1, 0, 0.0, 1, 0),
(22150, 1677, 1, 0, 0.0, 2, 0),
(22191, 1678, 1, 0, 0.0, 6, 0),
(22194, 1679, 1, 0, 0.0, 2, 0),
(22195, 1680, 1, 0, 0.0, 2, 0),
(22196, 1681, 1, 0, 0.0, 0, 0),
(22197, 1682, 1, 0, 0.0, 0, 0),
(22198, 1683, 0.422, 0, 0.0, 1, 0),
(22204, 1684, 1, 0, 0.0, 0, 0),
(22207, 1685, 1, 0, 0.0, 0, 0),
(22225, 1686, 1, 0, 0.0, 1, 0),
(22231, 1687, 1, 0, 0.0, 1, 0),
(22232, 1688, 1, 0, 0.0, 1, 0),
(22247, 1689, 1, 0, 0.0, 1, 0),
(22253, 1690, 0.965, 0, 0.0, 1, 0),
(22267, 1691, 1, 0, 0.0, 3, 0),
(22269, 1692, 1, 0, 0.0, 0, 0),
(22301, 1693, 1, 0, 0.0, 0, 0),
(22302, 1694, 1, 0, 0.0, 0, 0),
(22303, 1695, 1, 0, 0.0, 0, 0),
(22304, 1696, 1, 0, 0.0, 0, 0),
(22305, 1697, 1, 0, 0.0, 0, 0),
(22306, 1698, 1, 0, 0.0, 0, 0),
(22311, 1699, 1, 0, 0.0, 0, 0),
(22313, 1700, 1, 0, 0.0, 0, 0),
(22314, 1701, 0.791, 0, 0.0, 0, 0),
(22315, 1702, 1.931, 0, 0.0, 1, 0),
(22317, 1703, 0.445, 0, 0.0, 0, 0),
(22319, 1704, 0.965, 0, 0.0, 1, 0),
(22322, 1705, 0.445, 0, 0.0, 1, 0),
(22325, 1706, 1, 0, 0.0, 0, 0),
(22326, 1707, 1, 0, 0.0, 1, 0),
(22327, 1708, 1, 0, 0.0, 1, 0),
(22328, 1709, 1, 0, 0.0, 2, 0),
(22329, 1710, 0.965, 0, 0.0, 7, 0),
(22330, 1711, 1, 0, 0.0, 1, 0),
(22331, 1712, 1, 0, 0.0, 1, 0),
(22332, 1713, 0.445, 0, 0.0, 1, 0),
(22333, 1714, 1.015, 0, 0.0, 1, 0),
(22334, 1715, 1, 0, 0.0, 1, 0),
(22335, 1716, 1.015, 0, 0.0, 3, 0),
(22336, 1717, 0.766, 0, 0.0, 1, 0),
(22337, 1718, 1, 0, 0.0, 0, 0),
(22339, 1719, 1, 0, 0.0, 3, 0),
(22340, 1720, 1, 0, 0.0, 1, 0),
(22342, 1721, 1, 0, 0.0, 1, 0),
(22343, 1722, 1, 0, 0.0, 0, 0),
(22347, 1723, 0.415, 0, 0.0, 1, 0),
(22348, 1724, 0.791, 0, 0.0, 1, 0),
(22377, 1725, 0.445, 0, 0.0, 0, 0),
(22379, 1726, 1.931, 0, 0.0, 1, 0),
(22380, 1727, 1.931, 0, 0.0, 1, 0),
(22383, 1728, 1.931, 0, 0.0, 3, 0),
(22384, 1729, 0.445, 0, 0.0, 3, 0),
(22385, 1730, 1, 0, 0.0, 3, 0),
(22394, 1731, 1.015, 0, 0.0, 1, 0),
(22403, 1732, 1, 0, 0.0, 3, 0),
(22405, 1733, 1, 0, 0.0, 1, 0),
(22406, 1734, 1.015, 0, 0.0, 1, 0),
(22407, 1735, 1, 0, 0.0, 1, 0),
(22408, 1736, 0.516, 0, 0.0, 1, 0),
(22409, 1737, 1, 0, 0.0, 3, 0),
(22410, 1738, 1, 0, 0.0, 0, 0),
(22411, 1739, 1, 0, 0.0, 1, 0),
(22412, 1740, 1, 0, 0.0, 1, 0),
(22416, 1741, 1, 0, 0.0, 7, 0),
(22417, 1742, 1, 0, 0.0, 3, 0),
(22418, 1743, 1, 0, 0.0, 3, 0),
(22419, 1744, 1, 0, 0.0, 5, 0),
(22420, 1745, 1, 0, 0.0, 3, 0),
(22421, 1746, 1, 0, 0.0, 3, 0),
(22422, 1747, 1, 0, 0.0, 6, 0),
(22423, 1748, 1, 0, 0.0, 1, 0),
(22424, 1749, 1, 0, 0.0, 1, 0),
(22425, 1750, 1, 0, 0.0, 3, 0),
(22426, 1751, 1, 0, 0.0, 2, 0),
(22427, 1752, 1, 0, 0.0, 3, 0),
(22428, 1753, 1, 0, 0.0, 3, 0),
(22429, 1754, 1, 0, 0.0, 3, 0),
(22430, 1755, 1, 0, 0.0, 3, 0),
(22431, 1756, 1, 0, 0.0, 1, 0),
(22433, 1757, 1, 0, 0.0, 3, 0),
(22436, 1758, 1, 0, 0.0, 3, 0),
(22437, 1759, 1, 0, 0.0, 1, 0),
(22438, 1760, 1, 0, 0.0, 1, 0),
(22439, 1761, 1, 0, 0.0, 1, 0),
(22440, 1762, 1, 0, 0.0, 1, 0),
(22441, 1763, 1, 0, 0.0, 1, 0),
(22442, 1764, 1, 0, 0.0, 3, 0),
(22443, 1765, 1, 0, 0.0, 1, 0),
(22464, 1766, 1, 0, 0.0, 1, 0),
(22465, 1767, 1, 0, 0.0, 1, 0),
(22466, 1768, 1, 0, 0.0, 1, 0),
(22467, 1769, 1, 0, 0.0, 1, 0),
(22468, 1770, 1, 0, 0.0, 1, 0),
(22469, 1771, 1, 0, 0.0, 1, 0),
(22470, 1772, 1, 0, 0.0, 2, 0),
(22471, 1773, 1, 0, 0.0, 1, 0),
(22472, 1774, 1, 0, 0.0, 0, 0),
(22476, 1775, 1, 0, 0.0, 5, 0),
(22477, 1776, 1, 0, 0.0, 3, 0),
(22478, 1777, 1, 0, 0.0, 3, 0),
(22479, 1778, 1, 0, 0.0, 3, 0),
(22480, 1779, 1, 0, 0.0, 3, 0),
(22481, 1780, 1, 0, 0.0, 5, 0),
(22482, 1781, 1, 0, 0.0, 2, 0),
(22483, 1782, 1, 0, 0.0, 1, 0),
(22488, 1783, 1, 0, 0.0, 1, 0),
(22489, 1784, 1, 0, 0.0, 1, 0),
(22490, 1785, 1, 0, 0.0, 1, 0),
(22491, 1786, 1, 0, 0.0, 2, 0),
(22492, 1787, 1, 0, 0.0, 1, 0),
(22493, 1788, 1, 0, 0.0, 1, 0),
(22494, 1789, 1, 0, 0.0, 1, 0),
(22495, 1790, 1, 0, 0.0, 1, 0),
(22496, 1791, 1, 0, 0.0, 15, 0),
(22497, 1792, 1, 0, 0.0, 3, 0),
(22498, 1793, 1, 0, 0.0, 7, 0),
(22499, 1794, 1, 0, 0.0, 1, 0),
(22500, 1795, 1, 0, 0.0, 3, 0),
(22501, 1796, 1, 0, 0.0, 1, 0),
(22502, 1797, 1, 0, 0.0, 3, 0),
(22503, 1798, 1, 0, 0.0, 3, 0),
(22504, 1799, 1, 0, 0.0, 7, 0),
(22505, 1800, 1, 0, 0.0, 7, 0),
(22506, 1801, 1, 0, 0.0, 7, 0),
(22507, 1802, 1, 0, 0.0, 3, 0),
(22508, 1803, 1, 0, 0.0, 3, 0),
(22509, 1804, 1, 0, 0.0, 3, 0),
(22510, 1805, 1, 0, 0.0, 3, 0),
(22511, 1806, 1, 0, 0.0, 1, 0),
(22512, 1807, 1, 0, 0.0, 1, 0),
(22513, 1808, 1, 0, 0.0, 1, 0),
(22514, 1809, 1, 0, 0.0, 1, 0),
(22515, 1810, 1, 0, 0.0, 1, 0),
(22516, 1811, 1, 0, 0.0, 2, 0),
(22517, 1812, 1, 0, 0.0, 1, 0),
(22518, 1813, 1, 0, 0.0, 1, 0),
(22519, 1814, 1, 0, 0.0, 1, 0),
(22651, 1815, 1, 0, 0.0, 3, 0),
(22652, 1816, 1, 0, 0.0, 1, 0),
(22654, 1817, 1, 0, 0.0, 1, 0),
(22655, 1818, 1, 0, 0.0, 1, 0),
(22656, 1819, 0.415, 0, 0.0, 1, 0),
(22657, 1820, 1, 0, 0.0, 1, 0),
(22659, 1821, 1, 0, 0.0, 2, 0),
(22661, 1822, 1, 0, 0.0, 0, 0),
(22662, 1823, 1, 0, 0.0, 0, 0),
(22663, 1824, 1, 0, 0.0, 0, 0),
(22667, 1825, 1, 0, 0.0, 1, 0),
(22668, 1826, 1, 0, 0.0, 0, 0),
(22669, 1827, 1, 0, 0.0, 1, 0),
(22670, 1828, 1, 0, 0.0, 1, 0),
(22671, 1829, 1, 0, 0.0, 1, 0),
(22672, 1830, 1, 0, 0.0, 3, 0),
(22673, 1831, 1, 0, 0.0, 3, 0),
(22676, 1832, 1, 0, 0.0, 0, 0),
(22680, 1833, 1, 0, 0.0, 1, 0),
(22681, 1834, 1, 0, 0.0, 1, 0),
(22688, 1835, 1.931, 0, 0.0, 1, 0),
(22689, 1836, 1, 0, 0.0, 1, 0),
(22690, 1837, 1, 0, 0.0, 1, 0),
(22699, 1838, 1, 0, 0.0, 1, 0),
(22700, 1839, 1, 0, 0.0, 1, 0),
(22701, 1840, 1, 0, 0.0, 0, 0),
(22702, 1841, 1, 0, 0.0, 0, 0),
(22711, 1842, 1, 0, 0.0, 1, 0),
(22713, 1843, 1.931, 0, 0.0, 1, 0),
(22714, 1844, 1, 0, 0.0, 3, 0),
(22715, 1845, 1, 0, 0.0, 1, 0),
(22716, 1846, 1, 0, 0.0, 1, 0),
(22718, 1847, 1, 0, 0.0, 1, 0),
(22720, 1848, 1, 0, 0.0, 1, 0),
(22721, 1849, 1, 0, 0.0, 1, 0),
(22730, 1850, 1, 0, 0.0, 3, 0),
(22731, 1851, 1, 0, 0.0, 3, 0),
(22732, 1852, 1, 0, 0.0, 7, 0),
(22740, 1853, 1, 0, 0.0, 1, 0),
(22741, 1854, 1, 0, 0.0, 1, 0),
(22747, 1855, 1, 0, 0.0, 1, 0),
(22748, 1856, 1, 0, 0.0, 3, 0),
(22749, 1857, 1, 0, 0.0, 1, 0),
(22750, 1858, 1, 0, 0.0, 1, 0),
(22752, 1859, 1, 0, 0.0, 1, 0),
(22753, 1860, 1, 0, 0.0, 7, 0),
(22756, 1861, 1, 0, 0.0, 1, 0),
(22757, 1862, 1, 0, 0.0, 1, 0),
(22758, 1863, 1, 0, 0.0, 1, 0),
(22762, 1864, 1, 0, 0.0, 1, 0),
(22763, 1865, 1, 0, 0.0, 1, 0),
(22764, 1866, 1, 0, 0.0, 1, 0),
(22798, 1867, 0.791, 0, 0.0, 2, 0),
(22799, 1868, 1.015, 0, 0.0, 7, 0),
(22800, 1869, 1.015, 0, 0.0, 7, 0),
(22801, 1870, 1.015, 0, 0.0, 2, 0),
(22802, 1871, 0.445, 0, 0.0, 6, 0),
(22803, 1872, 1.931, 0, 0.0, 1, 0),
(22804, 1873, 0.445, 0, 0.0, 2, 0),
(22805, 1874, 0.445, 0, 0.0, 0, 0),
(22806, 1875, 0.445, 0, 0.0, 1, 0),
(22807, 1876, 1.931, 0, 0.0, 7, 0),
(22808, 1877, 0.445, 0, 0.0, 3, 0),
(22809, 1878, 1.015, 0, 0.0, 2, 0),
(22811, 1879, 0.405, 0, 0.0, 1, 0),
(22812, 1880, 0.415, 0, 0.0, 2, 0),
(22814, 1881, 0.791, 0, 0.0, 0, 0),
(22815, 1882, 0.791, 0, 0.0, 1, 0),
(22816, 1883, 0.445, 0, 0.0, 2, 0),
(22817, 1884, 0.791, 0, 0.0, 0, 0),
(22818, 1885, 0.422, 0, 0.0, 1, 0),
(22819, 1886, 0.766, 0, 0.0, 2, 0),
(22820, 1887, 0.516, 0, 0.0, 3, 0),
(22821, 1888, 0.516, 0, 0.0, 3, 0),
(22843, 1889, 1, 0, 0.0, 0, 0),
(22852, 1890, 1, 0, 0.0, 1, 0),
(22855, 1891, 1, 0, 0.0, 1, 0),
(22857, 1892, 1, 0, 0.0, 0, 0),
(22858, 1893, 1, 0, 0.0, 0, 0),
(22859, 1894, 1, 0, 0.0, 1, 0),
(22860, 1895, 1, 0, 0.0, 3, 0),
(22862, 1896, 1, 0, 0.0, 0, 0),
(22863, 1897, 1, 0, 0.0, 0, 0),
(22864, 1898, 1, 0, 0.0, 2, 0),
(22865, 1899, 1, 0, 0.0, 2, 0),
(22867, 1900, 1, 0, 0.0, 3, 0),
(22868, 1901, 1, 0, 0.0, 1, 0),
(22869, 1902, 1, 0, 0.0, 2, 0),
(22870, 1903, 1, 0, 0.0, 2, 0),
(22872, 1904, 1, 0, 0.0, 1, 0),
(22873, 1905, 1, 0, 0.0, 1, 0),
(22874, 1906, 1, 0, 0.0, 1, 0),
(22875, 1907, 1, 0, 0.0, 1, 0),
(22876, 1908, 1, 0, 0.0, 1, 0),
(22877, 1909, 1, 0, 0.0, 3, 0),
(22878, 1910, 1, 0, 0.0, 3, 0),
(22879, 1911, 1, 0, 0.0, 3, 0),
(22880, 1912, 1, 0, 0.0, 3, 0),
(22881, 1913, 1, 0, 0.0, 1, 0),
(22882, 1914, 1, 0, 0.0, 1, 0),
(22883, 1915, 1, 0, 0.0, 3, 0),
(22884, 1916, 1, 0, 0.0, 1, 0),
(22885, 1917, 1, 0, 0.0, 1, 0),
(22886, 1918, 1, 0, 0.0, 3, 0),
(22887, 1919, 1, 0, 0.0, 3, 0),
(22936, 1920, 1, 0, 0.0, 1, 0),
(22937, 1921, 0.965, 0, 0.0, 3, 0),
(22938, 1922, 1, 0, 0.0, 7, 0),
(22939, 1923, 1, 0, 0.0, 1, 0),
(22940, 1924, 1, 0, 0.0, 1, 0),
(22942, 1925, 1.931, 0, 0.0, 1, 0),
(22943, 1926, 1, 0, 0.0, 3, 0),
(22947, 1927, 1, 0, 0.0, 0, 0),
(22960, 1928, 1, 0, 0.0, 1, 0),
(22961, 1929, 1, 0, 0.0, 0, 0),
(22968, 1930, 1, 0, 0.0, 1, 0),
(22981, 1931, 1, 0, 0.0, 1, 0),
(22983, 1932, 1, 0, 0.0, 3, 0),
(22988, 1933, 1.931, 0, 0.0, 1, 0),
(22994, 1934, 0.965, 0, 0.0, 0, 0),
(23000, 1935, 1, 0, 0.0, 3, 0),
(23009, 1936, 0.516, 0, 0.0, 1, 0),
(23014, 1937, 0.445, 0, 0.0, 3, 0),
(23017, 1938, 1, 0, 0.0, 3, 0),
(23018, 1939, 1, 0, 0.0, 2, 0),
(23019, 1940, 1, 0, 0.0, 1, 0),
(23020, 1941, 1, 0, 0.0, 0, 0),
(23021, 1942, 1, 0, 0.0, 3, 0),
(23023, 1943, 1, 0, 0.0, 1, 0),
(23025, 1944, 1, 0, 0.0, 7, 0),
(23028, 1945, 1, 0, 0.0, 1, 0),
(23029, 1946, 0.965, 0, 0.0, 1, 0),
(23030, 1947, 1, 0, 0.0, 2, 0),
(23031, 1948, 1, 0, 0.0, 3, 0),
(23032, 1949, 1, 0, 0.0, 1, 0),
(23033, 1950, 1, 0, 0.0, 0, 0),
(23034, 1951, 1, 0, 0.0, 0, 0),
(23035, 1952, 1, 0, 0.0, 1, 0),
(23036, 1953, 1, 0, 0.0, 1, 0),
(23037, 1954, 1, 0, 0.0, 0, 0),
(23038, 1955, 1, 0, 0.0, 3, 0),
(23039, 1956, 0.791, 0, 0.0, 0, 0),
(23043, 1957, 0.422, 0, 0.0, 1, 0),
(23044, 1958, 0.445, 0, 0.0, 3, 0),
(23045, 1959, 1, 0, 0.0, 1, 0),
(23048, 1960, 0.965, 0, 0.0, 1, 0),
(23049, 1961, 0.965, 0, 0.0, 7, 0),
(23050, 1962, 1, 0, 0.0, 7, 0),
(23053, 1963, 1, 0, 0.0, 1, 0),
(23056, 1964, 1.931, 0, 0.0, 1, 0),
(23057, 1965, 1, 0, 0.0, 3, 0),
(23058, 1966, 1, 0, 0.0, 0, 0),
(23059, 1967, 1, 0, 0.0, 3, 0),
(23060, 1968, 1, 0, 0.0, 1, 0),
(23061, 1969, 1, 0, 0.0, 1, 0),
(23062, 1970, 1, 0, 0.0, 3, 0),
(23063, 1971, 1, 0, 0.0, 1, 0),
(23064, 1972, 1, 0, 0.0, 1, 0),
(23065, 1973, 1, 0, 0.0, 1, 0),
(23066, 1974, 1, 0, 0.0, 1, 0),
(23067, 1975, 1, 0, 0.0, 0, 0),
(23068, 1976, 1, 0, 0.0, 1, 0),
(23069, 1977, 1, 0, 0.0, 1, 0),
(23070, 1978, 1, 0, 0.0, 3, 0),
(23071, 1979, 1, 0, 0.0, 1, 0),
(23072, 1980, 1, 0, 0.0, 7, 0),
(23073, 1981, 1, 0, 0.0, 0, 0),
(23075, 1982, 0.766, 0, 0.0, 3, 0),
(23084, 1983, 1, 0, 0.0, 0, 0),
(23085, 1984, 1, 0, 0.0, 0, 0),
(23091, 1985, 1, 0, 0.0, 0, 0),
(23124, 1986, 1.015, 0, 0.0, 3, 0),
(23125, 1987, 1, 0, 0.0, 1, 0),
(23126, 1988, 1, 0, 0.0, 1, 0),
(23127, 1989, 1, 0, 0.0, 0, 0),
(23128, 1990, 1, 0, 0.0, 1, 0),
(23129, 1991, 1, 0, 0.0, 1, 0),
(23156, 1992, 0.965, 0, 0.0, 1, 0),
(23219, 1993, 1, 0, 0.0, 3, 0),
(23220, 1994, 1, 0, 0.0, 1, 0),
(23226, 1995, 1, 0, 0.0, 1, 0),
(23237, 1996, 1, 0, 0.0, 3, 0),
(23242, 1997, 0.437, 0, 0.0, 3, 0),
(23243, 1998, 1, 0, 0.0, 1, 0),
(23244, 1999, 1, 0, 0.0, 3, 0),
(23251, 2000, 1, 0, 0.0, 1, 0),
(23252, 2001, 1, 0, 0.0, 1, 0),
(23253, 2002, 1, 0, 0.0, 1, 0),
(23254, 2003, 1, 0, 0.0, 1, 0),
(23255, 2004, 1, 0, 0.0, 3, 0),
(23256, 2005, 1, 0, 0.0, 3, 0),
(23257, 2006, 1, 0, 0.0, 3, 0),
(23258, 2007, 1, 0, 0.0, 6, 0),
(23259, 2008, 1, 0, 0.0, 0, 0),
(23260, 2009, 1, 0, 0.0, 3, 0),
(23261, 2010, 1, 0, 0.0, 1, 0),
(23262, 2011, 1, 0, 0.0, 1, 0),
(23263, 2012, 1, 0, 0.0, 3, 0),
(23264, 2013, 1, 0, 0.0, 3, 0),
(23272, 2014, 1, 0, 0.0, 1, 0),
(23273, 2015, 1, 0, 0.0, 1, 0),
(23274, 2016, 1, 0, 0.0, 2, 0),
(23275, 2017, 1, 0, 0.0, 1, 0),
(23276, 2018, 1, 0, 0.0, 1, 0),
(23277, 2019, 1, 0, 0.0, 1, 0),
(23278, 2020, 1, 0, 0.0, 0, 0),
(23279, 2021, 1, 0, 0.0, 0, 0),
(23280, 2022, 1, 0, 0.0, 0, 0),
(23281, 2023, 1, 0, 0.0, 1, 0),
(23282, 2024, 1, 0, 0.0, 2, 0),
(23283, 2025, 1, 0, 0.0, 1, 0),
(23284, 2026, 1, 0, 0.0, 2, 0),
(23286, 2027, 1, 0, 0.0, 1, 0),
(23287, 2028, 1, 0, 0.0, 0, 0),
(23288, 2029, 1, 0, 0.0, 2, 0),
(23289, 2030, 1, 0, 0.0, 1, 0),
(23290, 2031, 1, 0, 0.0, 2, 0),
(23291, 2032, 1, 0, 0.0, 3, 0),
(23292, 2033, 1, 0, 0.0, 1, 0),
(23293, 2034, 1, 0, 0.0, 1, 0),
(23294, 2035, 1, 0, 0.0, 3, 0),
(23295, 2036, 1, 0, 0.0, 3, 0),
(23296, 2037, 1, 0, 0.0, 1, 0),
(23297, 2038, 1, 0, 0.0, 1, 0),
(23298, 2039, 1, 0, 0.0, 3, 0),
(23299, 2040, 1, 0, 0.0, 3, 0),
(23300, 2041, 1, 0, 0.0, 1, 0),
(23301, 2042, 1, 0, 0.0, 1, 0),
(23302, 2043, 1, 0, 0.0, 1, 0),
(23303, 2044, 1, 0, 0.0, 1, 0),
(23304, 2045, 1, 0, 0.0, 3, 0),
(23305, 2046, 1, 0, 0.0, 3, 0),
(23306, 2047, 1, 0, 0.0, 1, 0),
(23307, 2048, 1, 0, 0.0, 1, 0),
(23308, 2049, 1, 0, 0.0, 1, 0),
(23309, 2050, 1, 0, 0.0, 1, 0),
(23310, 2051, 1, 0, 0.0, 3, 0),
(23311, 2052, 1, 0, 0.0, 3, 0),
(23312, 2053, 1, 0, 0.0, 3, 0),
(23313, 2054, 1, 0, 0.0, 6, 0),
(23314, 2055, 1, 0, 0.0, 3, 0),
(23315, 2056, 1, 0, 0.0, 1, 0),
(23316, 2057, 1, 0, 0.0, 1, 0),
(23317, 2058, 1, 0, 0.0, 1, 0),
(23318, 2059, 1, 0, 0.0, 3, 0),
(23319, 2060, 1, 0, 0.0, 3, 0),
(23362, 2061, 0.453, 0, 0.0, 0, 0),
(23363, 2062, 1, 0, 0.0, 0, 0),
(23451, 2063, 1.931, 0, 0.0, 3, 0),
(23452, 2064, 0.965, 0, 0.0, 1, 0),
(23453, 2065, 0.965, 0, 0.0, 1, 0),
(23454, 2066, 1.931, 0, 0.0, 1, 0),
(23455, 2067, 1.015, 0, 0.0, 2, 0),
(23456, 2068, 0.445, 0, 0.0, 1, 0),
(23457, 2069, 1.015, 0, 0.0, 2, 0),
(23458, 2070, 1.931, 0, 0.0, 3, 0),
(23459, 2071, 1.931, 0, 0.0, 1, 0),
(23461, 2072, 0.445, 0, 0.0, 1, 0),
(23462, 2073, 0.965, 0, 0.0, 1, 0),
(23464, 2074, 1.931, 0, 0.0, 1, 0),
(23465, 2075, 1.015, 0, 0.0, 2, 0),
(23466, 2076, 1.931, 0, 0.0, 3, 0),
(23467, 2077, 0.445, 0, 0.0, 1, 0),
(23468, 2078, 0.965, 0, 0.0, 1, 0),
(23469, 2079, 0.965, 0, 0.0, 1, 0),
(23557, 2080, 0.415, 0, 0.0, 1, 0),
(23577, 2081, 0.445, 0, 0.0, 0, 0),
(23663, 2082, 1, 0, 0.0, 1, 0),
(23664, 2083, 1, 0, 0.0, 7, 0),
(23665, 2084, 1, 0, 0.0, 3, 0),
(23666, 2085, 1, 0, 0.0, 1, 0),
(23667, 2086, 1, 0, 0.0, 6, 0),
(23668, 2087, 1, 0, 0.0, 3, 0),
(23761, 2088, 1, 0, 0.0, 1, 0),
(23828, 2089, 1, 0, 0.0, 3, 0),
(23829, 2090, 1, 0, 0.0, 2, 0),
(23838, 2091, 1, 0, 0.0, 2, 0),
(23839, 2092, 1, 0, 0.0, 0, 0),
(24020, 2093, 0.445, 0, 0.0, 0, 0),
(24021, 2094, 1, 0, 0.0, 0, 0),
(24022, 2095, 1, 0, 0.0, 0, 0),
(24023, 2096, 1, 0, 0.0, 0, 0),
(24024, 2097, 1, 0, 0.0, 1, 0),
(24044, 2098, 0.791, 0, 0.0, 0, 0),
(24045, 2099, 1, 0, 0.0, 1, 0),
(24046, 2100, 1, 0, 0.0, 2, 0),
(24063, 2101, 1, 0, 0.0, 0, 0),
(24064, 2102, 1, 0, 0.0, 0, 0),
(24069, 2103, 1.015, 0, 0.0, 1, 0),
(24073, 2104, 1, 0, 0.0, 0, 0),
(24083, 2105, 1, 0, 0.0, 1, 0),
(24090, 2106, 1, 0, 0.0, 0, 0),
(24091, 2107, 1, 0, 0.0, 0, 0),
(24094, 2108, 1.015, 0, 0.0, 1, 0),
(24096, 2109, 1, 0, 0.0, 2, 0),
(24122, 2110, 1, 0, 0.0, 0, 0),
(24123, 2111, 1, 0, 0.0, 0, 0),
(24137, 2112, 1, 0, 0.0, 0, 0),
(24154, 2113, 1, 0, 0.0, 1, 0),
(24155, 2114, 0.791, 0, 0.0, 0, 0),
(24356, 2115, 0.445, 0, 0.0, 0, 0),
(24357, 2116, 1, 0, 0.0, 1, 0),
(24359, 2117, 1, 0, 0.0, 1, 0),
(24360, 2118, 1, 0, 0.0, 0, 0),
(24361, 2119, 1.931, 0, 0.0, 1, 0),
(24362, 2120, 1, 0, 0.0, 1, 0),
(24363, 2121, 1, 0, 0.0, 0, 0),
(24364, 2122, 1, 0, 0.0, 0, 0),
(24365, 2123, 1, 0, 0.0, 0, 0),
(24366, 2124, 1, 0, 0.0, 0, 0),
(24378, 2125, 1.931, 0, 0.0, 1, 0),
(24379, 2126, 1, 0, 0.0, 0, 0),
(24380, 2127, 0.516, 0, 0.0, 1, 0),
(24381, 2128, 0.415, 0, 0.0, 0, 0),
(24384, 2129, 1.931, 0, 0.0, 1, 0),
(24385, 2130, 1, 0, 0.0, 0, 0),
(24387, 2131, 1, 0, 0.0, 0, 0),
(24388, 2132, 1, 0, 0.0, 2, 0),
(24389, 2133, 0.415, 0, 0.0, 0, 0),
(24391, 2134, 1, 0, 0.0, 2, 0),
(24392, 2135, 1, 0, 0.0, 1, 0),
(24393, 2136, 1, 0, 0.0, 1, 0),
(24395, 2137, 1, 0, 0.0, 1, 0),
(24396, 2138, 1, 0, 0.0, 0, 0),
(24397, 2139, 1, 0, 0.0, 1, 0),
(24398, 2140, 1, 0, 0.0, 0, 0),
(24450, 2141, 1, 0, 0.0, 1, 0),
(24451, 2142, 1, 0, 0.0, 0, 0),
(24452, 2143, 1, 0, 0.0, 1, 0),
(24453, 2144, 1.931, 0, 0.0, 1, 0),
(24454, 2145, 1, 0, 0.0, 0, 0),
(24455, 2146, 1, 0, 0.0, 1, 0),
(24456, 2147, 1, 0, 0.0, 0, 0),
(24457, 2148, 1, 0, 0.0, 0, 0),
(24458, 2149, 1, 0, 0.0, 0, 0),
(24459, 2150, 1, 0, 0.0, 1, 0),
(24461, 2151, 0.791, 0, 0.0, 0, 0),
(24462, 2152, 1, 0, 0.0, 1, 0),
(24463, 2153, 1, 0, 0.0, 0, 0),
(24464, 2154, 0.445, 0, 0.0, 0, 0),
(24465, 2155, 1, 0, 0.0, 0, 0),
(24466, 2156, 1, 0, 0.0, 0, 0),
(24481, 2157, 1, 0, 0.0, 1, 0),
(25536, 2158, 1.931, 0, 0.0, 1, 0),
(25537, 2159, 0.791, 0, 0.0, 0, 0),
(25538, 2160, 0.445, 0, 0.0, 0, 0),
(25540, 2161, 1, 0, 0.0, 0, 0),
(25541, 2162, 1, 0, 0.0, 1, 0),
(25562, 2163, 1, 0, 0.0, 0, 0),
(25563, 2164, 1, 0, 0.0, 1, 0),
(25564, 2165, 1, 0, 0.0, 1, 0),
(25603, 2166, 0.791, 0, 0.0, 0, 0),
(25605, 2167, 1, 0, 0.0, 0, 0),
(25606, 2168, 1, 0, 0.0, 1, 0),
(25607, 2169, 1, 0, 0.0, 1, 0),
(25608, 2170, 0.791, 0, 0.0, 0, 0),
(25609, 2171, 1, 0, 0.0, 0, 0),
(25693, 2172, 1, 0, 0.0, 1, 0),
(25701, 2173, 1, 0, 0.0, 1, 0),
(25702, 2174, 1, 0, 0.0, 1, 0),
(25710, 2175, 1, 0, 0.0, 1, 0),
(25711, 2176, 1, 0, 0.0, 1, 0),
(25712, 2177, 1, 0, 0.0, 0, 0),
(25713, 2178, 1, 0, 0.0, 1, 0),
(25714, 2179, 1, 0, 0.0, 2, 0),
(25715, 2180, 1, 0, 0.0, 0, 0),
(25716, 2181, 1, 0, 0.0, 0, 0),
(25717, 2182, 1, 0, 0.0, 0, 0),
(25718, 2183, 1, 0, 0.0, 1, 0),
(25772, 2184, 0.627, 0, 0.0, 0, 0),
(25773, 2185, 0.445, 0, 0.0, 0, 0),
(25774, 2186, 1.931, 0, 0.0, 1, 0),
(25775, 2187, 1, 0, 0.0, 0, 0),
(25776, 2188, 1, 0, 0.0, 1, 0),
(25777, 2189, 1, 0, 0.0, 1, 0),
(25823, 2190, 0.445, 0, 0.0, 0, 0),
(25824, 2191, 1, 0, 0.0, 1, 0),
(25825, 2192, 0.445, 0, 0.0, 0, 0),
(25826, 2193, 1, 0, 0.0, 1, 0),
(25828, 2194, 0.399, 0, 0.0, 0, 0),
(25836, 2195, 1.931, 0, 0.0, 1, 0),
(25838, 2196, 1, 0, 0.0, 0, 0),
(25939, 2197, 0.516, 0, 0.0, 1, 0),
(25941, 2198, 1, 0, 0.0, 0, 0),
(25942, 2199, 1, 0, 0.0, 0, 0),
(25943, 2200, 0.453, 0, 0.0, 0, 0),
(25944, 2201, 0.791, 0, 0.0, 0, 0),
(25945, 2202, 1, 0, 0.0, 2, 0),
(25946, 2203, 1, 0, 0.0, 0, 0),
(25947, 2204, 1, 0, 0.0, 2, 0),
(25950, 2205, 1.015, 0, 0.0, 1, 0),
(25952, 2206, 0.445, 0, 0.0, 0, 0),
(25953, 2207, 0.405, 0, 0.0, 0, 0),
(25954, 2208, 1, 0, 0.0, 1, 0),
(25955, 2209, 1, 0, 0.0, 1, 0),
(25956, 2210, 1, 0, 0.0, 0, 0),
(25957, 2211, 1, 0, 0.0, 1, 0),
(25962, 2212, 1, 0, 0.0, 0, 0),
(25964, 2213, 0.445, 0, 0.0, 0, 0),
(25967, 2214, 1, 0, 0.0, 0, 0),
(25968, 2215, 1, 0, 0.0, 0, 0),
(25969, 2216, 1, 0, 0.0, 0, 0),
(25970, 2217, 1, 0, 0.0, 1, 0),
(27408, 2218, 1, 0, 0.0, 0, 0),
(27409, 2219, 1, 0, 0.0, 1, 0),
(27410, 2220, 1, 0, 0.0, 1, 0),
(27411, 2221, 1, 0, 0.0, 1, 0),
(27412, 2222, 1.015, 0, 0.0, 1, 0),
(27413, 2223, 1, 0, 0.0, 0, 0),
(27414, 2224, 1, 0, 0.0, 0, 0),
(27415, 2225, 1, 0, 0.0, 0, 0),
(27631, 2226, 0.389, 0, 0.0, 0, 0),
(27637, 2227, 1, 0, 0.0, 0, 0),
(27638, 2228, 1, 0, 0.0, 1, 0),
(27639, 2229, 1, 0, 0.0, 0, 0),
(27643, 2230, 1, 0, 0.0, 0, 0),
(27644, 2231, 1, 0, 0.0, 0, 0),
(27645, 2232, 1, 0, 0.0, 1, 0),
(27646, 2233, 1, 0, 0.0, 0, 0),
(27647, 2234, 1, 0, 0.0, 0, 0),
(27648, 2235, 1, 0, 0.0, 1, 0),
(27649, 2236, 1, 0, 0.0, 1, 0),
(27650, 2237, 1, 0, 0.0, 0, 0),
(27652, 2238, 1, 0, 0.0, 1, 0),
(27653, 2239, 1, 0, 0.0, 0, 0),
(27654, 2240, 1, 0, 0.0, 0, 0),
(27830, 2241, 1, 0, 0.0, 0, 0),
(27832, 2242, 1, 0, 0.0, 0, 0),
(27833, 2243, 1, 0, 0.0, 0, 0),
(27834, 2244, 1, 0, 0.0, 0, 0),
(27928, 2245, 0.389, 0, 0.0, 0, 0),
(27929, 2246, 0.389, 0, 0.0, 0, 0),
(27930, 2247, 0.405, 0, 0.0, 0, 0),
(27931, 2248, 0.405, 0, 0.0, 0, 0),
(27939, 2249, 0.516, 0, 0.0, 1, 0),
(27942, 2250, 0.516, 0, 0.0, 1, 0),
(28029, 2251, 1, 0, 0.0, 1, 0),
(28030, 2252, 1, 0, 0.0, 1, 0),
(28031, 2253, 1, 0, 0.0, 0, 0),
(28032, 2254, 1, 0, 0.0, 0, 0),
(28050, 2255, 1, 0, 0.0, 1, 0),
(28051, 2256, 1, 0, 0.0, 0, 0),
(28052, 2257, 1, 0, 0.0, 1, 0),
(28054, 2258, 1, 0, 0.0, 0, 0),
(28055, 2259, 1, 0, 0.0, 1, 0),
(28057, 2260, 1, 0, 0.0, 0, 0),
(28069, 2261, 1, 0, 0.0, 0, 0),
(28070, 2262, 1, 0, 0.0, 1, 0),
(28074, 2263, 1, 0, 0.0, 0, 0),
(28075, 2264, 1, 0, 0.0, 1, 0),
(28166, 2265, 0.422, 0, 0.0, 0, 0),
(28246, 2266, 1, 0, 0.0, 0, 0),
(28247, 2267, 1, 0, 0.0, 1, 0),
(28553, 2268, 1, 0, 0.0, 0, 0),
(28555, 2269, 1, 0, 0.0, 1, 0),
(28559, 2270, 1, 0, 0.0, 0, 0),
(28560, 2271, 1, 0, 0.0, 1, 0),
(28561, 2272, 1, 0, 0.0, 0, 0),
(28574, 2273, 1, 0, 0.0, 1, 0),
(28575, 2274, 1, 0, 0.0, 1, 0),
(28576, 2275, 1, 0, 0.0, 0, 0),
(28577, 2276, 1, 0, 0.0, 0, 0),
(28758, 2277, 1, 0, 0.0, 1, 0),
(28759, 2278, 1, 0, 0.0, 1, 0),
(28760, 2279, 1, 0, 0.0, 1, 0),
(28761, 2280, 1, 0, 0.0, 0, 0),
(28972, 2281, 0.389, 0, 0.0, 0, 0),
(29121, 2282, 0.445, 0, 0.0, 0, 0),
(29124, 2283, 0.445, 0, 0.0, 0, 0),
(29125, 2284, 0.445, 0, 0.0, 0, 0),
(29149, 2285, 0.516, 0, 0.0, 1, 0),
(29150, 2286, 0.445, 0, 0.0, 0, 0),
(29151, 2287, 0.415, 0, 0.0, 0, 0),
(29152, 2288, 0.405, 0, 0.0, 0, 0),
(29153, 2289, 1.931, 0, 0.0, 1, 0),
(29155, 2290, 1.931, 0, 0.0, 1, 0),
(29156, 2291, 0.627, 0, 0.0, 0, 0),
(29165, 2292, 0.627, 0, 0.0, 0, 0),
(29171, 2293, 0.884, 0, 0.0, 0, 0),
(29175, 2294, 1.931, 0, 0.0, 1, 0),
(29182, 2295, 0.445, 0, 0.0, 0, 0),
(29210, 2296, 0.389, 0, 0.0, 0, 0),
(29312, 2297, 1, 0, 0.0, 0, 0),
(29313, 2298, 1, 0, 0.0, 2, 0),
(29314, 2299, 1, 0, 0.0, 1, 0),
(29315, 2300, 1, 0, 0.0, 1, 0),
(29325, 2301, 1, 0, 0.0, 0, 0),
(29326, 2302, 1, 0, 0.0, 0, 0),
(29327, 2303, 1, 0, 0.0, 1, 0),
(29328, 2304, 1, 0, 0.0, 3, 0),
(29337, 2305, 1, 0, 0.0, 0, 0),
(29339, 2306, 1, 0, 0.0, 0, 0),
(29340, 2307, 1, 0, 0.0, 0, 0),
(29341, 2308, 1, 0, 0.0, 1, 0),
(29342, 2309, 1, 0, 0.0, 1, 0),
(29343, 2310, 1, 0, 0.0, 1, 0),
(29344, 2311, 1, 0, 0.0, 1, 0),
(29345, 2312, 1, 0, 0.0, 1, 0),
(29456, 2313, 0.445, 0, 0.0, 0, 0),
(29457, 2314, 1.931, 0, 0.0, 1, 0),
(29594, 2315, 1, 0, 0.0, 0, 0),
(29595, 2316, 1, 0, 0.0, 3, 0),
(29596, 2317, 1, 0, 0.0, 1, 0),
(29597, 2318, 1, 0, 0.0, 3, 0),
(29598, 2319, 1, 0, 0.0, 0, 0),
(29599, 2320, 1, 0, 0.0, 3, 0),
(29600, 2321, 1, 0, 0.0, 2, 0),
(29601, 2322, 1, 0, 0.0, 1, 0),
(29602, 2323, 1, 0, 0.0, 1, 0),
(29603, 2324, 1, 0, 0.0, 1, 0),
(29604, 2325, 1, 0, 0.0, 1, 0),
(29605, 2326, 1, 0, 0.0, 1, 0),
(29606, 2327, 1, 0, 0.0, 2, 0),
(29607, 2328, 1, 0, 0.0, 1, 0),
(29608, 2329, 1, 0, 0.0, 7, 0),
(29609, 2330, 1, 0, 0.0, 4, 0),
(29610, 2331, 1, 0, 0.0, 4, 0),
(29611, 2332, 1, 0, 0.0, 1, 0),
(29612, 2333, 1, 0, 0.0, 1, 0),
(29613, 2334, 1, 0, 0.0, 2, 0),
(29614, 2335, 1, 0, 0.0, 3, 0),
(29615, 2336, 1, 0, 0.0, 3, 0),
(29616, 2337, 1, 0, 0.0, 3, 0),
(29617, 2338, 1, 0, 0.0, 1, 0),
(29973, 2339, 1, 0, 0.0, 0, 0),
(29974, 2340, 1, 0, 0.0, 1, 0),
(29975, 2341, 1, 0, 0.0, 0, 0),
(30074, 2342, 1, 0, 0.0, 0, 0),
(30076, 2343, 1, 0, 0.0, 0, 0),
(30077, 2344, 0.445, 0, 0.0, 0, 0),
(30086, 2345, 0.791, 0, 0.0, 0, 0),
(30087, 2346, 0.445, 0, 0.0, 0, 0),
(30088, 2347, 0.791, 0, 0.0, 0, 0),
(30497, 2348, 1, 0, 0.0, 0, 0),
(30498, 2349, 1, 0, 0.0, 7, 0),
(30830, 2350, 0.791, 0, 0.0, 0, 0),
(30832, 2351, 1.931, 0, 0.0, 1, 0),
(30834, 2352, 1, 0, 0.0, 0, 0),
(31125, 2353, 1, 0, 0.0, 0, 0),
(31126, 2354, 1, 0, 0.0, 0, 0),
(31127, 2355, 1, 0, 0.0, 1, 0),
(31131, 2356, 1, 0, 0.0, 0, 0),
(31133, 2357, 1, 0, 0.0, 1, 0),
(31134, 2358, 0.791, 0, 0.0, 0, 0),
(31136, 2359, 1, 0, 0.0, 0, 0),
(31137, 2360, 1, 0, 0.0, 0, 0),
(31138, 2361, 1, 0, 0.0, 1, 0),
(31139, 2362, 0.445, 0, 0.0, 0, 0),
(31140, 2363, 1, 0, 0.0, 1, 0),
(31142, 2364, 1.931, 0, 0.0, 1, 0),
(31143, 2365, 1, 0, 0.0, 0, 0),
(31145, 2366, 1, 0, 0.0, 0, 0),
(31147, 2367, 1, 0, 0.0, 0, 0),
(31148, 2368, 1, 0, 0.0, 0, 0),
(31149, 2369, 1, 0, 0.0, 1, 0),
(31150, 2370, 1, 0, 0.0, 1, 0),
(31151, 2371, 1, 0, 0.0, 0, 0),
(31152, 2372, 1, 0, 0.0, 0, 0),
(31153, 2373, 0.445, 0, 0.0, 0, 0),
(31173, 2374, 1, 0, 0.0, 0, 0),
(31178, 2375, 1, 0, 0.0, 1, 0),
(31180, 2376, 1, 0, 0.0, 0, 0),
(31187, 2377, 1, 0, 0.0, 0, 0),
(31190, 2378, 1, 0, 0.0, 0, 0),
(31196, 2379, 1, 0, 0.0, 1, 0),
(31200, 2380, 0.422, 0, 0.0, 0, 0),
(31202, 2381, 1, 0, 0.0, 1, 0),
(31222, 2382, 1, 0, 0.0, 0, 0),
(31226, 2383, 1, 0, 0.0, 0, 0),
(31230, 2384, 1, 0, 0.0, 1, 0),
(31319, 2385, 1, 0, 0.0, 0, 0),
(31320, 2386, 1, 0, 0.0, 0, 0),
(31321, 2387, 1, 0, 0.0, 1, 0),
(31322, 2388, 0.791, 0, 0.0, 0, 0),
(31326, 2389, 1, 0, 0.0, 0, 0),
(31328, 2390, 1, 0, 0.0, 0, 0),
(31329, 2391, 1, 0, 0.0, 1, 0),
(31330, 2392, 1, 0, 0.0, 1, 0),
(31333, 2393, 1, 0, 0.0, 0, 0),
(31334, 2394, 0.791, 0, 0.0, 2, 0),
(31335, 2395, 1, 0, 0.0, 1, 0),
(31336, 2396, 1.931, 0, 0.0, 1, 0),
(31338, 2397, 1, 0, 0.0, 1, 0),
(31339, 2398, 1, 0, 0.0, 1, 0),
(31340, 2399, 1, 0, 0.0, 1, 0),
(31342, 2400, 1.931, 0, 0.0, 1, 0),
(31343, 2401, 1, 0, 0.0, 1, 0),
(31371, 2402, 1, 0, 0.0, 0, 0),
(31717, 2403, 1, 0, 0.0, 1, 0),
(31718, 2404, 1, 0, 0.0, 0, 0),
(31719, 2405, 1, 0, 0.0, 1, 0),
(31720, 2406, 1, 0, 0.0, 0, 0),
(31726, 2407, 1, 0, 0.0, 1, 0),
(31727, 2408, 1, 0, 0.0, 0, 0),
(31756, 2409, 0.445, 0, 0.0, 0, 0),
(31758, 2410, 1.931, 0, 0.0, 1, 0),
(31759, 2411, 0.445, 0, 0.0, 0, 0),
(31919, 2412, 1, 0, 0.0, 0, 0),
(31920, 2413, 1, 0, 0.0, 0, 0),
(31921, 2414, 1, 0, 0.0, 1, 0),
(31922, 2415, 1, 0, 0.0, 1, 0),
(31923, 2416, 1, 0, 0.0, 1, 0),
(31924, 2417, 1, 0, 0.0, 0, 0),
(32508, 2418, 1, 0, 0.0, 0, 0),
(32645, 2419, 0.415, 0, 0.0, 0, 0),
(32772, 2420, 1, 0, 0.0, 1, 0),
(32774, 2421, 1, 0, 0.0, 1, 0),
(34622, 2422, 0.389, 0, 0.0, 0, 0),
(34661, 2423, 0.791, 0, 0.0, 0, 0),
(38632, 2424, 0.791, 0, 0.0, 0, 0),
(38633, 2425, 0.791, 0, 0.0, 0, 0),
(38661, 2426, 1, 0, 0.0, 0, 0),
(38662, 2427, 1, 0, 0.0, 0, 0),
(38663, 2428, 1, 0, 0.0, 0, 0),
(38664, 2429, 1, 0, 0.0, 0, 0),
(38665, 2430, 1, 0, 0.0, 0, 0),
(38666, 2431, 1, 0, 0.0, 0, 0),
(38667, 2432, 1, 0, 0.0, 0, 0),
(38668, 2433, 1, 0, 0.0, 0, 0),
(38669, 2434, 1, 0, 0.0, 0, 0),
(38670, 2435, 1, 0, 0.0, 0, 0),
(38671, 2436, 1, 0, 0.0, 0, 0),
(38672, 2437, 1, 0, 0.0, 0, 0),
(38707, 2438, 0.791, 0, 0.0, 0, 0),
(39320, 2439, 1, 0, 0.0, 0, 0),
(39322, 2440, 1, 0, 0.0, 0, 0),
(39370, 2441, 0.791, 0, 0.0, 0, 0),
(41342, 2442, 1.015, 0, 0.0, 0, 0),
(43666, 2443, 0.965, 0, 0.0, 0, 0),
(43667, 2444, 0.987, 0, 0.0, 0, 0);

