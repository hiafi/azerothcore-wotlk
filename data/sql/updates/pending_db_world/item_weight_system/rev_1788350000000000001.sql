--
-- Phase 5 (content), revision 3: re-convert ilvl 66's Epic armor now that
-- the classifier resolves the full CombatRating bit range (docs/
-- itemization-changes.md §4.5's revision-3 note) instead of just Crit/Haste.
-- Replaces the revision-2 batch (rev_1788350000000000001.sql's original
-- content) in place -- same template_ids reused per item wherever one
-- already existed, so this doesn't orphan any earlier row; one item
-- (Heavy Dark Iron Ring, 18879) newly resolves an on-budget stat (pure
-- Defense Rating, previously invisible) and gets a fresh template_id.
-- 83 items converted now (was 82); 9 left unconverted (was 10) -- see
-- below.
--
-- Each item still gets its own dedicated template rather than being fit
-- against a shared library -- see the original revision-2 note for why.
-- budget_mult is 1.0 for every item, deliberately.
--
-- Skipped (9, left with their original literal stats, no
-- item_budget_assign row): Dark Iron Helm (19148) and Lava Belt (19149) --
-- pure Stamina, no on-budget stat to build a template around; Wrath of
-- Cenarius (21190) -- same; the four Darkmoon Cards (19288/19287/19289/
-- 19290), Earthstrike (21180), and Talisman of Ephemeral Power (18820) --
-- proc/use trinkets whose only value is a spell effect this system
-- doesn't (and shouldn't) fold into a flat stat.
--
-- Per-item stat+spell-effect resolution and percentage weighting use the
-- same method as the curve regression (§4.5) and Arcanist Boots' own
-- conversion. absorbed_spell_slots (last non-comment column before the
-- name comment) clears any on-equip spell slot whose effect got folded
-- into the stat block; a spell left un-absorbed had at least one effect
-- this system doesn't track (a real proc, an untracked resistance, etc.)
-- and was left alone, stat contribution and all.
--

DELETE FROM `item_budget_template` WHERE `template_id` IN (
  3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,
  18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,
  33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,
  48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,
  63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,
  78,79,80,81,82,83,84,85
);
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(3, 5, 4348),
(3, 6, 1610),
(3, 45, 2754),
(3, 31, 1288),
(4, 5, 5462),
(4, 6, 2536),
(4, 45, 2002),
(5, 5, 4715),
(5, 6, 3493),
(5, 45, 1792),
(6, 5, 4972),
(6, 6, 2810),
(6, 45, 2218),
(7, 5, 4246),
(7, 6, 2123),
(7, 45, 3631),
(8, 3, 3019),
(8, 5, 2830),
(8, 6, 1509),
(8, 32, 2642),
(9, 4, 4054),
(9, 13, 3243),
(9, 12, 2703),
(10, 5, 4506),
(10, 6, 1878),
(10, 4, 1690),
(10, 45, 1926),
(11, 3, 3704),
(11, 4, 1111),
(11, 32, 5185),
(12, 5, 3000),
(12, 6, 1637),
(12, 45, 5363),
(13, 5, 5531),
(13, 6, 1317),
(13, 45, 3152),
(14, 5, 5306),
(14, 6, 2653),
(14, 45, 2041),
(15, 5, 5043),
(15, 6, 2801),
(15, 45, 2156),
(16, 5, 5364),
(16, 6, 2208),
(16, 45, 2428),
(17, 3, 4000),
(17, 5, 1250),
(17, 6, 2250),
(17, 31, 2500),
(18, 5, 3686),
(18, 6, 1966),
(18, 4, 2457),
(18, 45, 1891),
(19, 5, 5652),
(19, 6, 2457),
(19, 45, 1891),
(20, 3, 6667),
(20, 4, 769),
(20, 31, 2564),
(21, 4, 4546),
(21, 15, 3030),
(21, 12, 2424),
(22, 4, 4445),
(22, 15, 3333),
(22, 12, 2222),
(23, 3, 4186),
(23, 5, 2558),
(23, 32, 3256),
(24, 5, 4018),
(24, 6, 2488),
(24, 4, 1531),
(24, 45, 1963),
(25, 3, 5472),
(25, 4, 1887),
(25, 32, 2641),
(26, 5, 4765),
(26, 6, 2383),
(26, 45, 2852),
(27, 4, 5122),
(27, 13, 2927),
(27, 12, 1951),
(28, 5, 5542),
(28, 6, 2519),
(28, 45, 1939),
(29, 5, 5883),
(29, 6, 1961),
(29, 45, 2156),
(30, 5, 3741),
(30, 6, 1995),
(30, 45, 4264),
(31, 3, 3077),
(31, 5, 2308),
(31, 6, 1025),
(31, 32, 3590),
(32, 5, 5542),
(32, 6, 2519),
(32, 45, 1939),
(33, 5, 4107),
(33, 6, 1643),
(33, 4, 2670),
(33, 45, 1580),
(34, 3, 4250),
(34, 4, 2250),
(34, 32, 3500),
(35, 5, 3588),
(35, 6, 1560),
(35, 32, 2184),
(35, 45, 2668),
(36, 5, 3003),
(36, 6, 3162),
(36, 32, 2213),
(36, 45, 1622),
(37, 5, 3780),
(37, 6, 4178),
(37, 45, 2042),
(38, 5, 3477),
(38, 6, 1830),
(38, 45, 4693),
(39, 3, 4400),
(39, 5, 1200),
(39, 6, 1600),
(39, 32, 2800),
(40, 5, 3380),
(40, 6, 3380),
(40, 4, 1314),
(40, 45, 1926),
(41, 4, 4444),
(41, 14, 3704),
(41, 12, 1852),
(42, 3, 5790),
(42, 4, 1754),
(42, 32, 2456),
(43, 5, 4423),
(43, 6, 3686),
(43, 45, 1891),
(44, 5, 2892),
(44, 6, 2273),
(44, 32, 2892),
(44, 45, 1943),
(45, 5, 4423),
(45, 6, 3686),
(45, 45, 1891),
(46, 3, 5000),
(46, 4, 5000),
(47, 5, 3642),
(47, 6, 4202),
(47, 45, 2156),
(48, 5, 2519),
(48, 6, 5542),
(48, 45, 1939),
(49, 5, 4168),
(49, 45, 5832),
(50, 3, 7600),
(50, 6, 2400),
(51, 5, 3449),
(51, 6, 2653),
(51, 4, 1857),
(51, 45, 2041),
(52, 3, 10000),
(53, 4, 6522),
(53, 12, 3478),
(54, 5, 4799),
(54, 6, 1919),
(54, 45, 3282),
(55, 5, 3714),
(55, 6, 2286),
(55, 32, 4000),
(56, 4, 10000),
(57, 5, 4357),
(57, 6, 4046),
(57, 45, 1597),
(58, 5, 5131),
(58, 6, 3320),
(58, 45, 1549),
(59, 5, 3653),
(59, 6, 2656),
(59, 45, 3691),
(60, 3, 5600),
(60, 5, 2400),
(60, 6, 2000),
(61, 5, 2759),
(61, 6, 3793),
(61, 4, 3448),
(62, 3, 10000),
(63, 5, 3987),
(63, 6, 2848),
(63, 45, 3165),
(64, 5, 4057),
(64, 6, 2705),
(64, 45, 3238),
(65, 5, 4423),
(65, 6, 3686),
(65, 45, 1891),
(66, 5, 2616),
(66, 6, 3018),
(66, 32, 2817),
(66, 45, 1549),
(67, 5, 3356),
(67, 6, 1790),
(67, 32, 3132),
(67, 45, 1722),
(68, 4, 5500),
(68, 31, 2500),
(68, 12, 2000),
(69, 3, 3750),
(69, 31, 6250),
(70, 5, 3979),
(70, 6, 3979),
(70, 45, 2042),
(71, 5, 3212),
(71, 6, 2998),
(71, 4, 2142),
(71, 45, 1648),
(72, 3, 4500),
(72, 4, 3000),
(72, 31, 2500),
(85, 12, 10000),
(73, 5, 3714),
(73, 6, 2286),
(73, 32, 4000),
(74, 45, 10000),
(75, 32, 10000),
(76, 5, 4573),
(76, 6, 1829),
(76, 45, 3598),
(77, 5, 4775),
(77, 6, 3184),
(77, 45, 2041),
(78, 5, 4202),
(78, 6, 2023),
(78, 32, 2179),
(78, 45, 1596),
(79, 5, 5113),
(79, 45, 2842),
(79, 31, 2045),
(80, 45, 10000),
(81, 5, 2064),
(81, 6, 1376),
(81, 32, 3854),
(81, 45, 2706),
(82, 5, 4976),
(82, 6, 3133),
(82, 45, 1891),
(83, 5, 2210),
(83, 6, 1263),
(83, 45, 4318),
(83, 32, 2209),
(84, 5, 3199),
(84, 45, 4475),
(84, 31, 2326);

DELETE FROM `item_budget_template_name` WHERE `template_id` IN (
  3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,
  18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,
  33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,
  48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,
  63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,
  78,79,80,81,82,83,84,85
);
INSERT INTO `item_budget_template_name` (`template_id`, `name`) VALUES
(3, 'Arcanist Crown shape'),
(4, 'Cenarion Helm shape'),
(5, 'Circlet of Prophecy shape'),
(6, 'Earthfury Helmet shape'),
(7, 'Felheart Horns shape'),
(8, 'Giantstalker\'s Helmet shape'),
(9, 'Helm of Might shape'),
(10, 'Lawbringer Helm shape'),
(11, 'Nightslayer Cover shape'),
(12, 'Jin\'do\'s Evil Eye shape'),
(13, 'Arcanist Mantle shape'),
(14, 'Cenarion Spaulders shape'),
(15, 'Earthfury Epaulets shape'),
(16, 'Felheart Shoulder Pads shape'),
(17, 'Giantstalker\'s Epaulets shape'),
(18, 'Lawbringer Spaulders shape'),
(19, 'Mantle of Prophecy shape'),
(20, 'Nightslayer Shoulder Pads shape'),
(21, 'Pauldrons of Might shape'),
(22, 'Breastplate of Might shape'),
(23, 'Giantstalker\'s Breastplate shape'),
(24, 'Lawbringer Chestguard shape'),
(25, 'Nightslayer Chestpiece shape'),
(26, 'Arcanist Belt shape'),
(27, 'Belt of Might shape'),
(28, 'Cenarion Belt shape'),
(29, 'Earthfury Belt shape'),
(30, 'Felheart Belt shape'),
(31, 'Giantstalker\'s Belt shape'),
(32, 'Girdle of Prophecy shape'),
(33, 'Lawbringer Belt shape'),
(34, 'Nightslayer Belt shape'),
(35, 'Arcanist Leggings shape'),
(36, 'Cenarion Leggings shape'),
(37, 'Earthfury Legguards shape'),
(38, 'Felheart Pants shape'),
(39, 'Giantstalker\'s Leggings shape'),
(40, 'Lawbringer Legplates shape'),
(41, 'Legplates of Might shape'),
(42, 'Nightslayer Pants shape'),
(43, 'Pants of Prophecy shape'),
(44, 'Arcanist Boots shape'),
(45, 'Boots of Prophecy shape'),
(46, 'Boots of the Vanguard shape'),
(47, 'Cenarion Boots shape'),
(48, 'Earthfury Boots shape'),
(49, 'Felheart Slippers shape'),
(50, 'Giantstalker\'s Boots shape'),
(51, 'Lawbringer Boots shape'),
(52, 'Nightslayer Boots shape'),
(53, 'Sabatons of Might shape'),
(54, 'Arcanist Bindings shape'),
(55, 'Blacklight Bracer shape'),
(56, 'Bracers of Might shape'),
(57, 'Cenarion Bracers shape'),
(58, 'Earthfury Bracers shape'),
(59, 'Felheart Bracers shape'),
(60, 'Giantstalker\'s Bracers shape'),
(61, 'Lawbringer Bracers shape'),
(62, 'Nightslayer Bracelets shape'),
(63, 'Vambraces of Prophecy shape'),
(64, 'Arcanist Gloves shape'),
(65, 'Cenarion Gloves shape'),
(66, 'Earthfury Gauntlets shape'),
(67, 'Felheart Gloves shape'),
(68, 'Gauntlets of Might shape'),
(69, 'Giantstalker\'s Gloves shape'),
(70, 'Gloves of Prophecy shape'),
(71, 'Lawbringer Gauntlets shape'),
(72, 'Nightslayer Gloves shape'),
(85, 'Heavy Dark Iron Ring shape'),
(73, 'Ring of Entropy shape'),
(74, 'Ring of Spell Power shape'),
(75, 'Eskhandar\'s Pelt shape'),
(76, 'Arcanist Robes shape'),
(77, 'Cenarion Vestments shape'),
(78, 'Earthfury Vestments shape'),
(79, 'Felheart Robes shape'),
(80, 'Flarecore Robe shape'),
(81, 'Robe of Volatile Power shape'),
(82, 'Robes of Prophecy shape'),
(83, 'Vestments of the Shifting Sands shape'),
(84, 'Jin\'do\'s Bag of Whammies shape');

-- entry -> name (template_id, deviation from curve[66]=52 at budget_mult=1.0):
--   16795 Arcanist Crown (template 3, +19.4%)
--   16834 Cenarion Helm (template 4, -1.4%)
--   16813 Circlet of Prophecy (template 5, +10.1%)
--   16842 Earthfury Helmet (template 6, -11.0%)
--   16808 Felheart Horns (template 7, -9.4%)
--   16846 Giantstalker's Helmet (template 8, +1.9%)
--   16866 Helm of Might (template 9, -28.8%)
--   16854 Lawbringer Helm (template 10, +2.4%)
--   16821 Nightslayer Cover (template 11, +3.8%)
--   19885 Jin'do's Evil Eye (template 12, +25.4%)
--   16797 Arcanist Mantle (template 13, -2.6%)
--   16836 Cenarion Spaulders (template 14, -3.3%)
--   16844 Earthfury Epaulets (template 15, -8.5%)
--   16807 Felheart Shoulder Pads (template 16, -18.7%)
--   16848 Giantstalker's Epaulets (template 17, +2.6%)
--   16856 Lawbringer Spaulders (template 18, +4.3%)
--   16816 Mantle of Prophecy (template 19, +4.3%)
--   16823 Nightslayer Shoulder Pads (template 20, +0.0%)
--   16868 Pauldrons of Might (template 21, -15.4%)
--   16865 Breastplate of Might (template 22, -13.5%)
--   16845 Giantstalker's Breastplate (template 23, -17.3%)
--   16853 Lawbringer Chestguard (template 24, +0.5%)
--   16820 Nightslayer Chestpiece (template 25, +1.9%)
--   16802 Arcanist Belt (template 26, +7.6%)
--   16864 Belt of Might (template 27, +5.1%)
--   16828 Cenarion Belt (template 28, +1.8%)
--   16838 Earthfury Belt (template 29, -8.5%)
--   16806 Felheart Belt (template 30, +2.8%)
--   16851 Giantstalker's Belt (template 31, +0.0%)
--   16817 Girdle of Prophecy (template 32, +1.8%)
--   16858 Lawbringer Belt (template 33, +24.9%)
--   16827 Nightslayer Belt (template 34, +2.6%)
--   16796 Arcanist Leggings (template 35, +23.3%)
--   16835 Cenarion Leggings (template 36, +21.7%)
--   16843 Earthfury Legguards (template 37, -3.3%)
--   16810 Felheart Pants (template 38, +5.1%)
--   16847 Giantstalker's Leggings (template 39, -3.8%)
--   16855 Lawbringer Legplates (template 40, +2.4%)
--   16867 Legplates of Might (template 41, +3.8%)
--   16822 Nightslayer Pants (template 42, +9.6%)
--   16814 Pants of Prophecy (template 43, +4.3%)
--   16800 Arcanist Boots (template 44, +24.1%)
--   16811 Boots of Prophecy (template 45, +4.3%)
--   21493 Boots of the Vanguard (template 46, +12.8%)
--   16829 Cenarion Boots (template 47, -8.5%)
--   16837 Earthfury Boots (template 48, +1.8%)
--   16803 Felheart Slippers (template 49, -32.3%)
--   16849 Giantstalker's Boots (template 50, -35.9%)
--   16859 Lawbringer Boots (template 51, -3.3%)
--   16824 Nightslayer Boots (template 52, -33.3%)
--   16862 Sabatons of Might (template 53, -41.0%)
--   16799 Arcanist Bindings (template 54, +6.9%)
--   19135 Blacklight Bracer (template 55, +19.7%)
--   16861 Bracers of Might (template 56, -62.4%)
--   16830 Cenarion Bracers (template 57, +9.8%)
--   16840 Earthfury Bracers (template 58, +13.3%)
--   16804 Felheart Bracers (template 59, +3.0%)
--   16850 Giantstalker's Bracers (template 60, -14.5%)
--   16857 Lawbringer Bracers (template 61, -0.9%)
--   16825 Nightslayer Bracelets (template 62, -31.6%)
--   16819 Vambraces of Prophecy (template 63, +20.1%)
--   16801 Arcanist Gloves (template 64, -5.2%)
--   16831 Cenarion Gloves (template 65, +4.3%)
--   16839 Earthfury Gauntlets (template 66, +27.4%)
--   16805 Felheart Gloves (template 67, +14.6%)
--   16863 Gauntlets of Might (template 68, +2.6%)
--   16852 Giantstalker's Gloves (template 69, -17.9%)
--   16812 Gloves of Prophecy (template 70, -3.3%)
--   16860 Lawbringer Gauntlets (template 71, +19.7%)
--   16826 Nightslayer Gloves (template 72, +2.6%)
--   18879 Heavy Dark Iron Ring (template 85, -72.6%)
--   18543 Ring of Entropy (template 73, +19.7%)
--   19147 Ring of Spell Power (template 74, -3.5%)
--   18204 Eskhandar's Pelt (template 75, -52.1%)
--   16798 Arcanist Robes (template 76, +5.1%)
--   16833 Cenarion Vestments (template 77, -3.3%)
--   16841 Earthfury Vestments (template 78, +23.6%)
--   16809 Felheart Robes (template 79, -24.8%)
--   19156 Flarecore Robe (template 80, -62.2%)
--   19145 Robe of Volatile Power (template 81, +39.7%)
--   16815 Robes of Prophecy (template 82, +4.3%)
--   21499 Vestments of the Shifting Sands (template 83, +21.8%)
--   19891 Jin'do's Bag of Whammies (template 84, +17.6%)

DELETE FROM `item_budget_assign` WHERE `entry` IN (
  16795,16834,16813,16842,16808,16846,16866,16854,16821,19885,16797,16836,16844,16807,16848,
  16856,16816,16823,16868,16865,16845,16853,16820,16802,16864,16828,16838,16806,16851,16817,
  16858,16827,16796,16835,16843,16810,16847,16855,16867,16822,16814,16800,16811,21493,16829,
  16837,16803,16849,16859,16824,16862,16799,19135,16861,16830,16840,16804,16850,16857,16825,
  16819,16801,16831,16839,16805,16863,16852,16812,16860,16826,18879,18543,19147,18204,16798,
  16833,16841,16809,19156,19145,16815,21499,19891
);
INSERT INTO `item_budget_assign`
  (`entry`, `template_id`, `budget_mult`, `stamina_delta`, `dps_delta`, `absorbed_spell_slots`, `armor_delta`)
VALUES
(16795, 3, 1.0, 0, 0.0, 3, 0),
(16834, 4, 1.0, 0, 0.0, 1, 0),
(16813, 5, 1.0, 0, 0.0, 1, 0),
(16842, 6, 1.0, 0, 0.0, 2, 0),
(16808, 7, 1.0, 0, 0.0, 1, 0),
(16846, 8, 1.0, 0, 0.0, 1, 0),
(16866, 9, 1.0, 0, 0.0, 3, 0),
(16854, 10, 1.0, 0, 0.0, 2, 0),
(16821, 11, 1.0, 0, 0.0, 1, 0),
(19885, 12, 1.0, 0, 0.0, 1, 0),
(16797, 13, 1.0, 0, 0.0, 2, 0),
(16836, 14, 1.0, 0, 0.0, 2, 0),
(16844, 15, 1.0, 0, 0.0, 2, 0),
(16807, 16, 1.0, 0, 0.0, 1, 0),
(16848, 17, 1.0, 0, 0.0, 1, 0),
(16856, 18, 1.0, 0, 0.0, 1, 0),
(16816, 19, 1.0, 0, 0.0, 1, 0),
(16823, 20, 1.0, 0, 0.0, 1, 0),
(16868, 21, 1.0, 0, 0.0, 3, 0),
(16865, 22, 1.0, 0, 0.0, 3, 0),
(16845, 23, 1.0, 0, 0.0, 1, 0),
(16853, 24, 1.0, 0, 0.0, 1, 0),
(16820, 25, 1.0, 0, 0.0, 1, 0),
(16802, 26, 1.0, 0, 0.0, 1, 0),
(16864, 27, 1.0, 0, 0.0, 3, 0),
(16828, 28, 1.0, 0, 0.0, 2, 0),
(16838, 29, 1.0, 0, 0.0, 2, 0),
(16806, 30, 1.0, 0, 0.0, 1, 0),
(16851, 31, 1.0, 0, 0.0, 1, 0),
(16817, 32, 1.0, 0, 0.0, 2, 0),
(16858, 33, 1.0, 0, 0.0, 1, 0),
(16827, 34, 1.0, 0, 0.0, 1, 0),
(16796, 35, 1.0, 0, 0.0, 3, 0),
(16835, 36, 1.0, 0, 0.0, 5, 0),
(16843, 37, 1.0, 0, 0.0, 2, 0),
(16810, 38, 1.0, 0, 0.0, 1, 0),
(16847, 39, 1.0, 0, 0.0, 1, 0),
(16855, 40, 1.0, 0, 0.0, 2, 0),
(16867, 41, 1.0, 0, 0.0, 3, 0),
(16822, 42, 1.0, 0, 0.0, 1, 0),
(16814, 43, 1.0, 0, 0.0, 2, 0),
(16800, 44, 1.0, 0, 0.0, 3, 0),
(16811, 45, 1.0, 0, 0.0, 1, 0),
(21493, 46, 1.0, 0, 0.0, 0, 0),
(16829, 47, 1.0, 0, 0.0, 2, 0),
(16837, 48, 1.0, 0, 0.0, 1, 0),
(16803, 49, 1.0, 0, 0.0, 1, 0),
(16849, 50, 1.0, 0, 0.0, 0, 0),
(16859, 51, 1.0, 0, 0.0, 2, 0),
(16824, 52, 1.0, 0, 0.0, 0, 0),
(16862, 53, 1.0, 0, 0.0, 1, 0),
(16799, 54, 1.0, 0, 0.0, 1, 0),
(19135, 55, 1.0, 0, 0.0, 1, 0),
(16861, 56, 1.0, 0, 0.0, 0, 0),
(16830, 57, 1.0, 0, 0.0, 1, 0),
(16840, 58, 1.0, 0, 0.0, 1, 0),
(16804, 59, 1.0, 0, 0.0, 1, 0),
(16850, 60, 1.0, 0, 0.0, 0, 0),
(16857, 61, 1.0, 0, 0.0, 0, 0),
(16825, 62, 1.0, 0, 0.0, 0, 0),
(16819, 63, 1.0, 0, 0.0, 2, 0),
(16801, 64, 1.0, 0, 0.0, 2, 0),
(16831, 65, 1.0, 0, 0.0, 1, 0),
(16839, 66, 1.0, 0, 0.0, 3, 0),
(16805, 67, 1.0, 0, 0.0, 3, 0),
(16863, 68, 1.0, 0, 0.0, 3, 0),
(16852, 69, 1.0, 0, 0.0, 1, 0),
(16812, 70, 1.0, 0, 0.0, 2, 0),
(16860, 71, 1.0, 0, 0.0, 1, 0),
(16826, 72, 1.0, 0, 0.0, 1, 0),
(18879, 85, 1.0, 0, 0.0, 1, 0),
(18543, 73, 1.0, 0, 0.0, 1, 0),
(19147, 74, 1.0, 0, 0.0, 1, 0),
(18204, 75, 1.0, 0, 0.0, 1, 0),
(16798, 76, 1.0, 0, 0.0, 1, 0),
(16833, 77, 1.0, 0, 0.0, 2, 0),
(16841, 78, 1.0, 0, 0.0, 3, 0),
(16809, 79, 1.0, 0, 0.0, 3, 0),
(19156, 80, 1.0, 0, 0.0, 1, 0),
(19145, 81, 1.0, 0, 0.0, 2, 0),
(16815, 82, 1.0, 0, 0.0, 1, 0),
(21499, 83, 1.0, 0, 0.0, 3, 0),
(19891, 84, 1.0, 0, 0.0, 3, 0);
