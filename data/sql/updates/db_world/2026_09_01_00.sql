-- DB update 2026_08_21_01 -> 2026_09_01_00
-- ==================================================================
-- Merged migration: Custom secondary-stat system (Mastery/Versatility/CDR/Proc combat ratings)
-- Consolidates 13 pending_db_world revisions into one file, kept in
-- original chronological order with no content changes. Each section below is
-- reproduced verbatim from its original rev_*.sql file for traceability.
-- ==================================================================

-- ---------------------------------------------------------------
-- originally rev_1787377390451498201.sql
-- ---------------------------------------------------------------
-- Custom: repurpose the (previously-unused) CR_WEAPON_SKILL_MAINHAND/OFFHAND/RANGED combat rating
-- slots (ids 20/21/22) into CR_MASTERY/CR_VERSATILITY/CR_COOLDOWN_REDUCTION - see Unit.h.
-- Their old `gtcombatratings_dbc` curves are shaped for converting rating into weapon-skill points,
-- not a percent, so they are overwritten here with a copy of the CR_CRIT_MELEE (id 8) percentage
-- curve, giving the 3 new stats a sane, already level-tuned percent-per-rating baseline. Balance can
-- be retuned later by editing `Data` directly - no code change needed.
-- `gtoctclasscombatratingscalar_dbc` needs no change: its rows for ids 20/21/22 are already a flat
-- `1` scalar per class, identical to CR_CRIT_MELEE's own scalar rows.
DELETE FROM `gtcombatratings_dbc` WHERE `ID` BETWEEN 2000 AND 2099;
INSERT INTO `gtcombatratings_dbc` (`ID`, `Data`) SELECT `ID` + 1200, `Data` FROM `gtcombatratings_dbc` WHERE `ID` BETWEEN 800 AND 899;
DELETE FROM `gtcombatratings_dbc` WHERE `ID` BETWEEN 2100 AND 2199;
INSERT INTO `gtcombatratings_dbc` (`ID`, `Data`) SELECT `ID` + 1300, `Data` FROM `gtcombatratings_dbc` WHERE `ID` BETWEEN 800 AND 899;
DELETE FROM `gtcombatratings_dbc` WHERE `ID` BETWEEN 2200 AND 2299;
INSERT INTO `gtcombatratings_dbc` (`ID`, `Data`) SELECT `ID` + 1400, `Data` FROM `gtcombatratings_dbc` WHERE `ID` BETWEEN 800 AND 899;

-- ---------------------------------------------------------------
-- originally rev_1787897259858855912.sql
-- ---------------------------------------------------------------
-- item-tools: "Betrayer's Boots" (19897). Adding Mastery Changed columns: stat_type4 (0 -> 22), stat_value4 (0 -> 20).
UPDATE `item_template` SET `stat_type4` = 22, `stat_value4` = 20 WHERE `entry` = 19897 AND `stat_type4` = 0 AND `stat_value4` = 0;

-- ---------------------------------------------------------------
-- originally rev_1787897446305627526.sql
-- ---------------------------------------------------------------
-- item-tools: 'Band of Servitude' (22721). Adding Versatility Changed columns: stat_type3 (0 -> 23), stat_value3 (0 ->
-- 20).
UPDATE `item_template` SET `stat_type3` = 23, `stat_value3` = 20 WHERE `entry` = 22721 AND `stat_type3` = 0 AND `stat_value3` = 0;

-- ---------------------------------------------------------------
-- originally rev_1787897487869873604.sql
-- ---------------------------------------------------------------
-- item-tools: 'Cloak of the Hakkari Worshippers' (22711). Adding CDR Changed columns: stat_type3 (0 -> 24), stat_value3
-- (0 -> 20).
UPDATE `item_template` SET `stat_type3` = 24, `stat_value3` = 20 WHERE `entry` = 22711 AND `stat_type3` = 0 AND `stat_value3` = 0;

-- ---------------------------------------------------------------
-- originally rev_1787897526828359633.sql
-- ---------------------------------------------------------------
-- item-tools: 'Seal of the Gurubashi Berserker' (22722). Adding Proc Chance Changed columns: stat_type2 (0 -> 33),
-- stat_value2 (0 -> 20).
UPDATE `item_template` SET `stat_type2` = 33, `stat_value2` = 20 WHERE `entry` = 22722 AND `stat_type2` = 0 AND `stat_value2` = 0;

-- ---------------------------------------------------------------
-- originally rev_1787897871776266721.sql
-- ---------------------------------------------------------------
-- Custom QA vendor in Stormwind (Trade District) selling the custom-stat test items:
-- Betrayer's Boots (19897), Seal of the Gurubashi Berserker (22722),
-- Band of Servitude (22721), Cloak of the Hakkari Worshippers (22711).
REPLACE INTO `creature_template` (`entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`,
    `KillCredit1`, `KillCredit2`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`,
    `faction`, `npcflag`, `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`, `rank`,
    `dmgschool`, `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`, `BaseVariance`, `RangeVariance`,
    `unit_class`, `unit_flags`, `unit_flags2`, `dynamicflags`, `family`, `type`, `type_flags`, `lootid`,
    `pickpocketloot`, `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`, `MovementType`,
    `HoverHeight`, `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`, `RacialLeader`,
    `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`, `VerifiedBuild`)
VALUES (900010, 0, 0, 0, 0, 0, 'Quinn Testbury', '<QA Item Vendor>', NULL, 0, 1, 1, 0, 12, 128, 1, 1.14286, 1, 1,
    20, 0, 0, 1, 2000, 2000, 1, 1, 1, 512, 2048, 0, 0, 7, 134217728, 0, 0, 0, 0, 0, 0, 0, '', 0, 1, 1, 1, 1, 1, 0,
    0, 1, 0, 2, '', NULL);

DELETE FROM `creature_template_model` WHERE `CreatureID` = 900010;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`,
    `VerifiedBuild`)
VALUES (900010, 0, 1520, 1, 1, NULL);

DELETE FROM `creature` WHERE `guid` = 900010;
INSERT INTO `creature` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
    `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`, `wander_distance`, `currentwaypoint`,
    `curhealth`, `curmana`, `MovementType`, `npcflag`, `unit_flags`, `dynamicflags`, `ScriptName`, `VerifiedBuild`,
    `CreateObject`, `Comment`)
VALUES (900010, 900010, 0, 0, 0, 1, 1, 0, -8718.03, 480.42, 98.81, 0.9, 300, 0, 0, 100, 0, 0, 0, 0, 0, '', 0, 0,
    'QA vendor for custom item stat testing');

DELETE FROM `npc_vendor` WHERE `entry` = 900010;
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`)
VALUES
(900010, 1, 19897, 0, 0, 0, 0),
(900010, 2, 22722, 0, 0, 0, 0),
(900010, 3, 22721, 0, 0, 0, 0),
(900010, 4, 22711, 0, 0, 0, 0);

-- ---------------------------------------------------------------
-- originally rev_1787946043819236756.sql
-- ---------------------------------------------------------------
-- Rework the custom secondary-stat rating curves (Mastery, Versatility, Cooldown
-- Reduction, Proc Chance) in gtcombatratings_dbc to intentionally-designed values
-- instead of the inherited weapon-skill/hit-taken-melee curves they came with from
-- repurposing unused CombatRating slots (see Unit.h CR_MASTERY/CR_VERSATILITY/
-- CR_COOLDOWN_REDUCTION/CR_PROC_CHANCE comments).
--
-- New design (per-class scalar is 1.0 for all classes on these slots, confirmed via
-- gtoctclasscombatratingscalar_dbc, so this table alone fully controls the curve):
--   Mastery             = same curve as Crit Rating (CR_CRIT_SPELL)
--   Cooldown Reduction  = same curve as Crit Rating (CR_CRIT_SPELL)
--   Proc Chance         = Crit Rating curve x 0.5 (scales 2x as fast, i.e. cheaper)
--   Versatility         = Crit Rating curve x 2.0 (scales 0.5x as fast, i.e. pricier)
--
-- ID layout in gtcombatratings_dbc: ID = CombatRating * 100 + (level - 1).
-- CR_PROC_CHANCE=11, CR_MASTERY=20, CR_VERSATILITY=21, CR_COOLDOWN_REDUCTION=22,
-- CR_CRIT_SPELL=10 (source curve, left untouched).

-- Mastery (CR=20, x1.0 of Crit Rating)
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2000;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2001;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2002;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2003;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2004;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2005;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2006;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2007;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2008;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2009;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.807692 WHERE `ID` = 2010;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.07692 WHERE `ID` = 2011;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.34615 WHERE `ID` = 2012;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.61539 WHERE `ID` = 2013;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.88461 WHERE `ID` = 2014;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.15385 WHERE `ID` = 2015;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.42308 WHERE `ID` = 2016;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.69231 WHERE `ID` = 2017;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.96154 WHERE `ID` = 2018;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.23077 WHERE `ID` = 2019;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.5 WHERE `ID` = 2020;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.76923 WHERE `ID` = 2021;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.03846 WHERE `ID` = 2022;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.30769 WHERE `ID` = 2023;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.57692 WHERE `ID` = 2024;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.84615 WHERE `ID` = 2025;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.11539 WHERE `ID` = 2026;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.38461 WHERE `ID` = 2027;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.65385 WHERE `ID` = 2028;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.92308 WHERE `ID` = 2029;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.19231 WHERE `ID` = 2030;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.46154 WHERE `ID` = 2031;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.73077 WHERE `ID` = 2032;
UPDATE `gtcombatratings_dbc` SET `Data` = 7 WHERE `ID` = 2033;
UPDATE `gtcombatratings_dbc` SET `Data` = 7.26923 WHERE `ID` = 2034;
UPDATE `gtcombatratings_dbc` SET `Data` = 7.53846 WHERE `ID` = 2035;
UPDATE `gtcombatratings_dbc` SET `Data` = 7.80769 WHERE `ID` = 2036;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.07692 WHERE `ID` = 2037;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.34615 WHERE `ID` = 2038;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.61538 WHERE `ID` = 2039;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.88461 WHERE `ID` = 2040;
UPDATE `gtcombatratings_dbc` SET `Data` = 9.15385 WHERE `ID` = 2041;
UPDATE `gtcombatratings_dbc` SET `Data` = 9.42308 WHERE `ID` = 2042;
UPDATE `gtcombatratings_dbc` SET `Data` = 9.69231 WHERE `ID` = 2043;
UPDATE `gtcombatratings_dbc` SET `Data` = 9.96154 WHERE `ID` = 2044;
UPDATE `gtcombatratings_dbc` SET `Data` = 10.2308 WHERE `ID` = 2045;
UPDATE `gtcombatratings_dbc` SET `Data` = 10.5 WHERE `ID` = 2046;
UPDATE `gtcombatratings_dbc` SET `Data` = 10.7692 WHERE `ID` = 2047;
UPDATE `gtcombatratings_dbc` SET `Data` = 11.0385 WHERE `ID` = 2048;
UPDATE `gtcombatratings_dbc` SET `Data` = 11.3077 WHERE `ID` = 2049;
UPDATE `gtcombatratings_dbc` SET `Data` = 11.5769 WHERE `ID` = 2050;
UPDATE `gtcombatratings_dbc` SET `Data` = 11.8462 WHERE `ID` = 2051;
UPDATE `gtcombatratings_dbc` SET `Data` = 12.1154 WHERE `ID` = 2052;
UPDATE `gtcombatratings_dbc` SET `Data` = 12.3846 WHERE `ID` = 2053;
UPDATE `gtcombatratings_dbc` SET `Data` = 12.6538 WHERE `ID` = 2054;
UPDATE `gtcombatratings_dbc` SET `Data` = 12.9231 WHERE `ID` = 2055;
UPDATE `gtcombatratings_dbc` SET `Data` = 13.1923 WHERE `ID` = 2056;
UPDATE `gtcombatratings_dbc` SET `Data` = 13.4615 WHERE `ID` = 2057;
UPDATE `gtcombatratings_dbc` SET `Data` = 13.7308 WHERE `ID` = 2058;
UPDATE `gtcombatratings_dbc` SET `Data` = 14 WHERE `ID` = 2059;
UPDATE `gtcombatratings_dbc` SET `Data` = 14.5316 WHERE `ID` = 2060;
UPDATE `gtcombatratings_dbc` SET `Data` = 15.1053 WHERE `ID` = 2061;
UPDATE `gtcombatratings_dbc` SET `Data` = 15.726 WHERE `ID` = 2062;
UPDATE `gtcombatratings_dbc` SET `Data` = 16.4 WHERE `ID` = 2063;
UPDATE `gtcombatratings_dbc` SET `Data` = 17.1343 WHERE `ID` = 2064;
UPDATE `gtcombatratings_dbc` SET `Data` = 17.9375 WHERE `ID` = 2065;
UPDATE `gtcombatratings_dbc` SET `Data` = 18.8197 WHERE `ID` = 2066;
UPDATE `gtcombatratings_dbc` SET `Data` = 19.7931 WHERE `ID` = 2067;
UPDATE `gtcombatratings_dbc` SET `Data` = 20.8727 WHERE `ID` = 2068;
UPDATE `gtcombatratings_dbc` SET `Data` = 22.0769 WHERE `ID` = 2069;
UPDATE `gtcombatratings_dbc` SET `Data` = 23.7537 WHERE `ID` = 2070;
UPDATE `gtcombatratings_dbc` SET `Data` = 25.5579 WHERE `ID` = 2071;
UPDATE `gtcombatratings_dbc` SET `Data` = 27.4991 WHERE `ID` = 2072;
UPDATE `gtcombatratings_dbc` SET `Data` = 29.5877 WHERE `ID` = 2073;
UPDATE `gtcombatratings_dbc` SET `Data` = 31.8349 WHERE `ID` = 2074;
UPDATE `gtcombatratings_dbc` SET `Data` = 34.2529 WHERE `ID` = 2075;
UPDATE `gtcombatratings_dbc` SET `Data` = 36.8545 WHERE `ID` = 2076;
UPDATE `gtcombatratings_dbc` SET `Data` = 39.6536 WHERE `ID` = 2077;
UPDATE `gtcombatratings_dbc` SET `Data` = 42.6654 WHERE `ID` = 2078;
UPDATE `gtcombatratings_dbc` SET `Data` = 45.906 WHERE `ID` = 2079;
UPDATE `gtcombatratings_dbc` SET `Data` = 49.3927 WHERE `ID` = 2080;
UPDATE `gtcombatratings_dbc` SET `Data` = 53.1441 WHERE `ID` = 2081;
UPDATE `gtcombatratings_dbc` SET `Data` = 57.1806 WHERE `ID` = 2082;
UPDATE `gtcombatratings_dbc` SET `Data` = 61.5236 WHERE `ID` = 2083;
UPDATE `gtcombatratings_dbc` SET `Data` = 66.1964 WHERE `ID` = 2084;
UPDATE `gtcombatratings_dbc` SET `Data` = 71.2242 WHERE `ID` = 2085;
UPDATE `gtcombatratings_dbc` SET `Data` = 76.6339 WHERE `ID` = 2086;
UPDATE `gtcombatratings_dbc` SET `Data` = 82.4544 WHERE `ID` = 2087;
UPDATE `gtcombatratings_dbc` SET `Data` = 88.717 WHERE `ID` = 2088;
UPDATE `gtcombatratings_dbc` SET `Data` = 95.4553 WHERE `ID` = 2089;
UPDATE `gtcombatratings_dbc` SET `Data` = 102.705 WHERE `ID` = 2090;
UPDATE `gtcombatratings_dbc` SET `Data` = 110.506 WHERE `ID` = 2091;
UPDATE `gtcombatratings_dbc` SET `Data` = 118.899 WHERE `ID` = 2092;
UPDATE `gtcombatratings_dbc` SET `Data` = 127.93 WHERE `ID` = 2093;
UPDATE `gtcombatratings_dbc` SET `Data` = 137.647 WHERE `ID` = 2094;
UPDATE `gtcombatratings_dbc` SET `Data` = 148.101 WHERE `ID` = 2095;
UPDATE `gtcombatratings_dbc` SET `Data` = 159.35 WHERE `ID` = 2096;
UPDATE `gtcombatratings_dbc` SET `Data` = 171.453 WHERE `ID` = 2097;
UPDATE `gtcombatratings_dbc` SET `Data` = 184.475 WHERE `ID` = 2098;
UPDATE `gtcombatratings_dbc` SET `Data` = 198.486 WHERE `ID` = 2099;

-- Versatility (CR=21, x2.0 of Crit Rating)
UPDATE `gtcombatratings_dbc` SET `Data` = 1.07692 WHERE `ID` = 2100;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.07692 WHERE `ID` = 2101;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.07692 WHERE `ID` = 2102;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.07692 WHERE `ID` = 2103;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.07692 WHERE `ID` = 2104;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.07692 WHERE `ID` = 2105;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.07692 WHERE `ID` = 2106;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.07692 WHERE `ID` = 2107;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.07692 WHERE `ID` = 2108;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.07692 WHERE `ID` = 2109;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.61538 WHERE `ID` = 2110;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.15384 WHERE `ID` = 2111;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.6923 WHERE `ID` = 2112;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.23078 WHERE `ID` = 2113;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.76922 WHERE `ID` = 2114;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.3077 WHERE `ID` = 2115;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.84616 WHERE `ID` = 2116;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.38462 WHERE `ID` = 2117;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.92308 WHERE `ID` = 2118;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.46154 WHERE `ID` = 2119;
UPDATE `gtcombatratings_dbc` SET `Data` = 7 WHERE `ID` = 2120;
UPDATE `gtcombatratings_dbc` SET `Data` = 7.53846 WHERE `ID` = 2121;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.07692 WHERE `ID` = 2122;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.61538 WHERE `ID` = 2123;
UPDATE `gtcombatratings_dbc` SET `Data` = 9.15384 WHERE `ID` = 2124;
UPDATE `gtcombatratings_dbc` SET `Data` = 9.6923 WHERE `ID` = 2125;
UPDATE `gtcombatratings_dbc` SET `Data` = 10.2308 WHERE `ID` = 2126;
UPDATE `gtcombatratings_dbc` SET `Data` = 10.7692 WHERE `ID` = 2127;
UPDATE `gtcombatratings_dbc` SET `Data` = 11.3077 WHERE `ID` = 2128;
UPDATE `gtcombatratings_dbc` SET `Data` = 11.8462 WHERE `ID` = 2129;
UPDATE `gtcombatratings_dbc` SET `Data` = 12.3846 WHERE `ID` = 2130;
UPDATE `gtcombatratings_dbc` SET `Data` = 12.9231 WHERE `ID` = 2131;
UPDATE `gtcombatratings_dbc` SET `Data` = 13.4615 WHERE `ID` = 2132;
UPDATE `gtcombatratings_dbc` SET `Data` = 14 WHERE `ID` = 2133;
UPDATE `gtcombatratings_dbc` SET `Data` = 14.5385 WHERE `ID` = 2134;
UPDATE `gtcombatratings_dbc` SET `Data` = 15.0769 WHERE `ID` = 2135;
UPDATE `gtcombatratings_dbc` SET `Data` = 15.6154 WHERE `ID` = 2136;
UPDATE `gtcombatratings_dbc` SET `Data` = 16.1538 WHERE `ID` = 2137;
UPDATE `gtcombatratings_dbc` SET `Data` = 16.6923 WHERE `ID` = 2138;
UPDATE `gtcombatratings_dbc` SET `Data` = 17.2308 WHERE `ID` = 2139;
UPDATE `gtcombatratings_dbc` SET `Data` = 17.7692 WHERE `ID` = 2140;
UPDATE `gtcombatratings_dbc` SET `Data` = 18.3077 WHERE `ID` = 2141;
UPDATE `gtcombatratings_dbc` SET `Data` = 18.8462 WHERE `ID` = 2142;
UPDATE `gtcombatratings_dbc` SET `Data` = 19.3846 WHERE `ID` = 2143;
UPDATE `gtcombatratings_dbc` SET `Data` = 19.9231 WHERE `ID` = 2144;
UPDATE `gtcombatratings_dbc` SET `Data` = 20.4616 WHERE `ID` = 2145;
UPDATE `gtcombatratings_dbc` SET `Data` = 21 WHERE `ID` = 2146;
UPDATE `gtcombatratings_dbc` SET `Data` = 21.5384 WHERE `ID` = 2147;
UPDATE `gtcombatratings_dbc` SET `Data` = 22.077 WHERE `ID` = 2148;
UPDATE `gtcombatratings_dbc` SET `Data` = 22.6154 WHERE `ID` = 2149;
UPDATE `gtcombatratings_dbc` SET `Data` = 23.1538 WHERE `ID` = 2150;
UPDATE `gtcombatratings_dbc` SET `Data` = 23.6924 WHERE `ID` = 2151;
UPDATE `gtcombatratings_dbc` SET `Data` = 24.2308 WHERE `ID` = 2152;
UPDATE `gtcombatratings_dbc` SET `Data` = 24.7692 WHERE `ID` = 2153;
UPDATE `gtcombatratings_dbc` SET `Data` = 25.3076 WHERE `ID` = 2154;
UPDATE `gtcombatratings_dbc` SET `Data` = 25.8462 WHERE `ID` = 2155;
UPDATE `gtcombatratings_dbc` SET `Data` = 26.3846 WHERE `ID` = 2156;
UPDATE `gtcombatratings_dbc` SET `Data` = 26.923 WHERE `ID` = 2157;
UPDATE `gtcombatratings_dbc` SET `Data` = 27.4616 WHERE `ID` = 2158;
UPDATE `gtcombatratings_dbc` SET `Data` = 28 WHERE `ID` = 2159;
UPDATE `gtcombatratings_dbc` SET `Data` = 29.0632 WHERE `ID` = 2160;
UPDATE `gtcombatratings_dbc` SET `Data` = 30.2106 WHERE `ID` = 2161;
UPDATE `gtcombatratings_dbc` SET `Data` = 31.452 WHERE `ID` = 2162;
UPDATE `gtcombatratings_dbc` SET `Data` = 32.8 WHERE `ID` = 2163;
UPDATE `gtcombatratings_dbc` SET `Data` = 34.2686 WHERE `ID` = 2164;
UPDATE `gtcombatratings_dbc` SET `Data` = 35.875 WHERE `ID` = 2165;
UPDATE `gtcombatratings_dbc` SET `Data` = 37.6394 WHERE `ID` = 2166;
UPDATE `gtcombatratings_dbc` SET `Data` = 39.5862 WHERE `ID` = 2167;
UPDATE `gtcombatratings_dbc` SET `Data` = 41.7454 WHERE `ID` = 2168;
UPDATE `gtcombatratings_dbc` SET `Data` = 44.1538 WHERE `ID` = 2169;
UPDATE `gtcombatratings_dbc` SET `Data` = 47.5074 WHERE `ID` = 2170;
UPDATE `gtcombatratings_dbc` SET `Data` = 51.1158 WHERE `ID` = 2171;
UPDATE `gtcombatratings_dbc` SET `Data` = 54.9982 WHERE `ID` = 2172;
UPDATE `gtcombatratings_dbc` SET `Data` = 59.1754 WHERE `ID` = 2173;
UPDATE `gtcombatratings_dbc` SET `Data` = 63.6698 WHERE `ID` = 2174;
UPDATE `gtcombatratings_dbc` SET `Data` = 68.5058 WHERE `ID` = 2175;
UPDATE `gtcombatratings_dbc` SET `Data` = 73.709 WHERE `ID` = 2176;
UPDATE `gtcombatratings_dbc` SET `Data` = 79.3072 WHERE `ID` = 2177;
UPDATE `gtcombatratings_dbc` SET `Data` = 85.3308 WHERE `ID` = 2178;
UPDATE `gtcombatratings_dbc` SET `Data` = 91.812 WHERE `ID` = 2179;
UPDATE `gtcombatratings_dbc` SET `Data` = 98.7854 WHERE `ID` = 2180;
UPDATE `gtcombatratings_dbc` SET `Data` = 106.288 WHERE `ID` = 2181;
UPDATE `gtcombatratings_dbc` SET `Data` = 114.361 WHERE `ID` = 2182;
UPDATE `gtcombatratings_dbc` SET `Data` = 123.047 WHERE `ID` = 2183;
UPDATE `gtcombatratings_dbc` SET `Data` = 132.393 WHERE `ID` = 2184;
UPDATE `gtcombatratings_dbc` SET `Data` = 142.448 WHERE `ID` = 2185;
UPDATE `gtcombatratings_dbc` SET `Data` = 153.268 WHERE `ID` = 2186;
UPDATE `gtcombatratings_dbc` SET `Data` = 164.909 WHERE `ID` = 2187;
UPDATE `gtcombatratings_dbc` SET `Data` = 177.434 WHERE `ID` = 2188;
UPDATE `gtcombatratings_dbc` SET `Data` = 190.911 WHERE `ID` = 2189;
UPDATE `gtcombatratings_dbc` SET `Data` = 205.41 WHERE `ID` = 2190;
UPDATE `gtcombatratings_dbc` SET `Data` = 221.012 WHERE `ID` = 2191;
UPDATE `gtcombatratings_dbc` SET `Data` = 237.798 WHERE `ID` = 2192;
UPDATE `gtcombatratings_dbc` SET `Data` = 255.86 WHERE `ID` = 2193;
UPDATE `gtcombatratings_dbc` SET `Data` = 275.294 WHERE `ID` = 2194;
UPDATE `gtcombatratings_dbc` SET `Data` = 296.202 WHERE `ID` = 2195;
UPDATE `gtcombatratings_dbc` SET `Data` = 318.7 WHERE `ID` = 2196;
UPDATE `gtcombatratings_dbc` SET `Data` = 342.906 WHERE `ID` = 2197;
UPDATE `gtcombatratings_dbc` SET `Data` = 368.95 WHERE `ID` = 2198;
UPDATE `gtcombatratings_dbc` SET `Data` = 396.972 WHERE `ID` = 2199;

-- Cooldown Reduction (CR=22, x1.0 of Crit Rating)
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2200;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2201;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2202;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2203;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2204;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2205;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2206;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2207;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2208;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.538462 WHERE `ID` = 2209;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.807692 WHERE `ID` = 2210;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.07692 WHERE `ID` = 2211;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.34615 WHERE `ID` = 2212;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.61539 WHERE `ID` = 2213;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.88461 WHERE `ID` = 2214;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.15385 WHERE `ID` = 2215;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.42308 WHERE `ID` = 2216;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.69231 WHERE `ID` = 2217;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.96154 WHERE `ID` = 2218;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.23077 WHERE `ID` = 2219;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.5 WHERE `ID` = 2220;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.76923 WHERE `ID` = 2221;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.03846 WHERE `ID` = 2222;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.30769 WHERE `ID` = 2223;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.57692 WHERE `ID` = 2224;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.84615 WHERE `ID` = 2225;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.11539 WHERE `ID` = 2226;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.38461 WHERE `ID` = 2227;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.65385 WHERE `ID` = 2228;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.92308 WHERE `ID` = 2229;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.19231 WHERE `ID` = 2230;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.46154 WHERE `ID` = 2231;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.73077 WHERE `ID` = 2232;
UPDATE `gtcombatratings_dbc` SET `Data` = 7 WHERE `ID` = 2233;
UPDATE `gtcombatratings_dbc` SET `Data` = 7.26923 WHERE `ID` = 2234;
UPDATE `gtcombatratings_dbc` SET `Data` = 7.53846 WHERE `ID` = 2235;
UPDATE `gtcombatratings_dbc` SET `Data` = 7.80769 WHERE `ID` = 2236;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.07692 WHERE `ID` = 2237;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.34615 WHERE `ID` = 2238;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.61538 WHERE `ID` = 2239;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.88461 WHERE `ID` = 2240;
UPDATE `gtcombatratings_dbc` SET `Data` = 9.15385 WHERE `ID` = 2241;
UPDATE `gtcombatratings_dbc` SET `Data` = 9.42308 WHERE `ID` = 2242;
UPDATE `gtcombatratings_dbc` SET `Data` = 9.69231 WHERE `ID` = 2243;
UPDATE `gtcombatratings_dbc` SET `Data` = 9.96154 WHERE `ID` = 2244;
UPDATE `gtcombatratings_dbc` SET `Data` = 10.2308 WHERE `ID` = 2245;
UPDATE `gtcombatratings_dbc` SET `Data` = 10.5 WHERE `ID` = 2246;
UPDATE `gtcombatratings_dbc` SET `Data` = 10.7692 WHERE `ID` = 2247;
UPDATE `gtcombatratings_dbc` SET `Data` = 11.0385 WHERE `ID` = 2248;
UPDATE `gtcombatratings_dbc` SET `Data` = 11.3077 WHERE `ID` = 2249;
UPDATE `gtcombatratings_dbc` SET `Data` = 11.5769 WHERE `ID` = 2250;
UPDATE `gtcombatratings_dbc` SET `Data` = 11.8462 WHERE `ID` = 2251;
UPDATE `gtcombatratings_dbc` SET `Data` = 12.1154 WHERE `ID` = 2252;
UPDATE `gtcombatratings_dbc` SET `Data` = 12.3846 WHERE `ID` = 2253;
UPDATE `gtcombatratings_dbc` SET `Data` = 12.6538 WHERE `ID` = 2254;
UPDATE `gtcombatratings_dbc` SET `Data` = 12.9231 WHERE `ID` = 2255;
UPDATE `gtcombatratings_dbc` SET `Data` = 13.1923 WHERE `ID` = 2256;
UPDATE `gtcombatratings_dbc` SET `Data` = 13.4615 WHERE `ID` = 2257;
UPDATE `gtcombatratings_dbc` SET `Data` = 13.7308 WHERE `ID` = 2258;
UPDATE `gtcombatratings_dbc` SET `Data` = 14 WHERE `ID` = 2259;
UPDATE `gtcombatratings_dbc` SET `Data` = 14.5316 WHERE `ID` = 2260;
UPDATE `gtcombatratings_dbc` SET `Data` = 15.1053 WHERE `ID` = 2261;
UPDATE `gtcombatratings_dbc` SET `Data` = 15.726 WHERE `ID` = 2262;
UPDATE `gtcombatratings_dbc` SET `Data` = 16.4 WHERE `ID` = 2263;
UPDATE `gtcombatratings_dbc` SET `Data` = 17.1343 WHERE `ID` = 2264;
UPDATE `gtcombatratings_dbc` SET `Data` = 17.9375 WHERE `ID` = 2265;
UPDATE `gtcombatratings_dbc` SET `Data` = 18.8197 WHERE `ID` = 2266;
UPDATE `gtcombatratings_dbc` SET `Data` = 19.7931 WHERE `ID` = 2267;
UPDATE `gtcombatratings_dbc` SET `Data` = 20.8727 WHERE `ID` = 2268;
UPDATE `gtcombatratings_dbc` SET `Data` = 22.0769 WHERE `ID` = 2269;
UPDATE `gtcombatratings_dbc` SET `Data` = 23.7537 WHERE `ID` = 2270;
UPDATE `gtcombatratings_dbc` SET `Data` = 25.5579 WHERE `ID` = 2271;
UPDATE `gtcombatratings_dbc` SET `Data` = 27.4991 WHERE `ID` = 2272;
UPDATE `gtcombatratings_dbc` SET `Data` = 29.5877 WHERE `ID` = 2273;
UPDATE `gtcombatratings_dbc` SET `Data` = 31.8349 WHERE `ID` = 2274;
UPDATE `gtcombatratings_dbc` SET `Data` = 34.2529 WHERE `ID` = 2275;
UPDATE `gtcombatratings_dbc` SET `Data` = 36.8545 WHERE `ID` = 2276;
UPDATE `gtcombatratings_dbc` SET `Data` = 39.6536 WHERE `ID` = 2277;
UPDATE `gtcombatratings_dbc` SET `Data` = 42.6654 WHERE `ID` = 2278;
UPDATE `gtcombatratings_dbc` SET `Data` = 45.906 WHERE `ID` = 2279;
UPDATE `gtcombatratings_dbc` SET `Data` = 49.3927 WHERE `ID` = 2280;
UPDATE `gtcombatratings_dbc` SET `Data` = 53.1441 WHERE `ID` = 2281;
UPDATE `gtcombatratings_dbc` SET `Data` = 57.1806 WHERE `ID` = 2282;
UPDATE `gtcombatratings_dbc` SET `Data` = 61.5236 WHERE `ID` = 2283;
UPDATE `gtcombatratings_dbc` SET `Data` = 66.1964 WHERE `ID` = 2284;
UPDATE `gtcombatratings_dbc` SET `Data` = 71.2242 WHERE `ID` = 2285;
UPDATE `gtcombatratings_dbc` SET `Data` = 76.6339 WHERE `ID` = 2286;
UPDATE `gtcombatratings_dbc` SET `Data` = 82.4544 WHERE `ID` = 2287;
UPDATE `gtcombatratings_dbc` SET `Data` = 88.717 WHERE `ID` = 2288;
UPDATE `gtcombatratings_dbc` SET `Data` = 95.4553 WHERE `ID` = 2289;
UPDATE `gtcombatratings_dbc` SET `Data` = 102.705 WHERE `ID` = 2290;
UPDATE `gtcombatratings_dbc` SET `Data` = 110.506 WHERE `ID` = 2291;
UPDATE `gtcombatratings_dbc` SET `Data` = 118.899 WHERE `ID` = 2292;
UPDATE `gtcombatratings_dbc` SET `Data` = 127.93 WHERE `ID` = 2293;
UPDATE `gtcombatratings_dbc` SET `Data` = 137.647 WHERE `ID` = 2294;
UPDATE `gtcombatratings_dbc` SET `Data` = 148.101 WHERE `ID` = 2295;
UPDATE `gtcombatratings_dbc` SET `Data` = 159.35 WHERE `ID` = 2296;
UPDATE `gtcombatratings_dbc` SET `Data` = 171.453 WHERE `ID` = 2297;
UPDATE `gtcombatratings_dbc` SET `Data` = 184.475 WHERE `ID` = 2298;
UPDATE `gtcombatratings_dbc` SET `Data` = 198.486 WHERE `ID` = 2299;

-- Proc Chance (CR=11, x0.5 of Crit Rating)
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 1100;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 1101;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 1102;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 1103;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 1104;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 1105;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 1106;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 1107;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 1108;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 1109;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.403846 WHERE `ID` = 1110;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.53846 WHERE `ID` = 1111;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.673075 WHERE `ID` = 1112;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.807695 WHERE `ID` = 1113;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.942305 WHERE `ID` = 1114;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.07692 WHERE `ID` = 1115;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.21154 WHERE `ID` = 1116;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.34615 WHERE `ID` = 1117;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.48077 WHERE `ID` = 1118;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.61539 WHERE `ID` = 1119;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.75 WHERE `ID` = 1120;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.88461 WHERE `ID` = 1121;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.01923 WHERE `ID` = 1122;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.15385 WHERE `ID` = 1123;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.28846 WHERE `ID` = 1124;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.42307 WHERE `ID` = 1125;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.55769 WHERE `ID` = 1126;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.69231 WHERE `ID` = 1127;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.82693 WHERE `ID` = 1128;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.96154 WHERE `ID` = 1129;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.09615 WHERE `ID` = 1130;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.23077 WHERE `ID` = 1131;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.36538 WHERE `ID` = 1132;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.5 WHERE `ID` = 1133;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.63462 WHERE `ID` = 1134;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.76923 WHERE `ID` = 1135;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.90385 WHERE `ID` = 1136;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.03846 WHERE `ID` = 1137;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.17307 WHERE `ID` = 1138;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.30769 WHERE `ID` = 1139;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.44231 WHERE `ID` = 1140;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.57693 WHERE `ID` = 1141;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.71154 WHERE `ID` = 1142;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.84616 WHERE `ID` = 1143;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.98077 WHERE `ID` = 1144;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.1154 WHERE `ID` = 1145;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.25 WHERE `ID` = 1146;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.3846 WHERE `ID` = 1147;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.51925 WHERE `ID` = 1148;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.65385 WHERE `ID` = 1149;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.78845 WHERE `ID` = 1150;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.9231 WHERE `ID` = 1151;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.0577 WHERE `ID` = 1152;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.1923 WHERE `ID` = 1153;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.3269 WHERE `ID` = 1154;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.46155 WHERE `ID` = 1155;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.59615 WHERE `ID` = 1156;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.73075 WHERE `ID` = 1157;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.8654 WHERE `ID` = 1158;
UPDATE `gtcombatratings_dbc` SET `Data` = 7 WHERE `ID` = 1159;
UPDATE `gtcombatratings_dbc` SET `Data` = 7.2658 WHERE `ID` = 1160;
UPDATE `gtcombatratings_dbc` SET `Data` = 7.55265 WHERE `ID` = 1161;
UPDATE `gtcombatratings_dbc` SET `Data` = 7.863 WHERE `ID` = 1162;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.2 WHERE `ID` = 1163;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.56715 WHERE `ID` = 1164;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.96875 WHERE `ID` = 1165;
UPDATE `gtcombatratings_dbc` SET `Data` = 9.40985 WHERE `ID` = 1166;
UPDATE `gtcombatratings_dbc` SET `Data` = 9.89655 WHERE `ID` = 1167;
UPDATE `gtcombatratings_dbc` SET `Data` = 10.4363 WHERE `ID` = 1168;
UPDATE `gtcombatratings_dbc` SET `Data` = 11.0384 WHERE `ID` = 1169;
UPDATE `gtcombatratings_dbc` SET `Data` = 11.8768 WHERE `ID` = 1170;
UPDATE `gtcombatratings_dbc` SET `Data` = 12.779 WHERE `ID` = 1171;
UPDATE `gtcombatratings_dbc` SET `Data` = 13.7495 WHERE `ID` = 1172;
UPDATE `gtcombatratings_dbc` SET `Data` = 14.7939 WHERE `ID` = 1173;
UPDATE `gtcombatratings_dbc` SET `Data` = 15.9175 WHERE `ID` = 1174;
UPDATE `gtcombatratings_dbc` SET `Data` = 17.1264 WHERE `ID` = 1175;
UPDATE `gtcombatratings_dbc` SET `Data` = 18.4273 WHERE `ID` = 1176;
UPDATE `gtcombatratings_dbc` SET `Data` = 19.8268 WHERE `ID` = 1177;
UPDATE `gtcombatratings_dbc` SET `Data` = 21.3327 WHERE `ID` = 1178;
UPDATE `gtcombatratings_dbc` SET `Data` = 22.953 WHERE `ID` = 1179;
UPDATE `gtcombatratings_dbc` SET `Data` = 24.6963 WHERE `ID` = 1180;
UPDATE `gtcombatratings_dbc` SET `Data` = 26.5721 WHERE `ID` = 1181;
UPDATE `gtcombatratings_dbc` SET `Data` = 28.5903 WHERE `ID` = 1182;
UPDATE `gtcombatratings_dbc` SET `Data` = 30.7618 WHERE `ID` = 1183;
UPDATE `gtcombatratings_dbc` SET `Data` = 33.0982 WHERE `ID` = 1184;
UPDATE `gtcombatratings_dbc` SET `Data` = 35.6121 WHERE `ID` = 1185;
UPDATE `gtcombatratings_dbc` SET `Data` = 38.3169 WHERE `ID` = 1186;
UPDATE `gtcombatratings_dbc` SET `Data` = 41.2272 WHERE `ID` = 1187;
UPDATE `gtcombatratings_dbc` SET `Data` = 44.3585 WHERE `ID` = 1188;
UPDATE `gtcombatratings_dbc` SET `Data` = 47.7276 WHERE `ID` = 1189;
UPDATE `gtcombatratings_dbc` SET `Data` = 51.3525 WHERE `ID` = 1190;
UPDATE `gtcombatratings_dbc` SET `Data` = 55.253 WHERE `ID` = 1191;
UPDATE `gtcombatratings_dbc` SET `Data` = 59.4495 WHERE `ID` = 1192;
UPDATE `gtcombatratings_dbc` SET `Data` = 63.965 WHERE `ID` = 1193;
UPDATE `gtcombatratings_dbc` SET `Data` = 68.8235 WHERE `ID` = 1194;
UPDATE `gtcombatratings_dbc` SET `Data` = 74.0505 WHERE `ID` = 1195;
UPDATE `gtcombatratings_dbc` SET `Data` = 79.675 WHERE `ID` = 1196;
UPDATE `gtcombatratings_dbc` SET `Data` = 85.7265 WHERE `ID` = 1197;
UPDATE `gtcombatratings_dbc` SET `Data` = 92.2375 WHERE `ID` = 1198;
UPDATE `gtcombatratings_dbc` SET `Data` = 99.243 WHERE `ID` = 1199;

-- ---------------------------------------------------------------
-- originally rev_1788156116888309569.sql
-- ---------------------------------------------------------------
-- item-tools: "Betrayer's Boots" (19897). Upping to 100% mastery for testing Changed columns: stat_value4 (20 -> 1400).
UPDATE `item_template` SET `stat_value4` = 1400 WHERE `entry` = 19897 AND `stat_value4` = 20;

-- ---------------------------------------------------------------
-- originally rev_1788156193646087050.sql
-- ---------------------------------------------------------------
-- item-tools: 'Band of Servitude' (22721). Testing Changed columns: stat_value3 (20 -> 1400).
UPDATE `item_template` SET `stat_value3` = 1400 WHERE `entry` = 22721 AND `stat_value3` = 20;

-- ---------------------------------------------------------------
-- originally rev_1788156235356043756.sql
-- ---------------------------------------------------------------
-- item-tools: 'Seal of the Gurubashi Berserker' (22722). Testing Changed columns: stat_value2 (20 -> 1400).
UPDATE `item_template` SET `stat_value2` = 1400 WHERE `entry` = 22722 AND `stat_value2` = 20;

-- ---------------------------------------------------------------
-- originally rev_1788156276423963642.sql
-- ---------------------------------------------------------------
-- item-tools: 'Cloak of the Hakkari Worshippers' (22711). Test Changed columns: stat_value3 (20 -> 1400).
UPDATE `item_template` SET `stat_value3` = 1400 WHERE `entry` = 22711 AND `stat_value3` = 20;

-- ---------------------------------------------------------------
-- originally rev_1788166879105224370.sql
-- ---------------------------------------------------------------
-- item-tools: 'Cloak of the Hakkari Worshippers' (22711). Testing Changed columns: stat_value3 (1400 -> 700).
UPDATE `item_template` SET `stat_value3` = 700 WHERE `entry` = 22711 AND `stat_value3` = 1400;

-- ---------------------------------------------------------------
-- originally rev_1788195067344804929.sql
-- ---------------------------------------------------------------
-- Cooldown Reduction stat rework (see Player::AddSpellAndCategoryCooldowns, Player.cpp): the
-- stat is now applied as a "cooldown haste" (rec / (1 + CDR%/100)) instead of a flat percentage
-- cut (rec * (1 - CDR%/100)), so 100% CDR only halves a cooldown, 200% takes it to a third, and
-- so on - no finite amount of rating can reduce a cooldown to zero. To keep that curve feeling
-- worthwhile per point (diminishing returns bite immediately once you're doing division instead
-- of subtraction), CR_COOLDOWN_REDUCTION's `gtcombatratings_dbc` curve (id 22, rows 2200-2299) is
-- retuned from x1.0 of Crit Rating (CR_CRIT_SPELL) down to x0.5 - twice the percent per point,
-- same multiplier CR_PROC_CHANCE already uses (see rev_1787946043819236756.sql) - which is why
-- these values are identical to that migration's Proc Chance block (ids 1100-1199), just shifted
-- to the Cooldown Reduction id range.
-- `gtoctclasscombatratingscalar_dbc` needs no change: id 22's per-class scalar is already a flat
-- `1` for every class, same as every other custom stat slot.
-- Remember to also regenerate the client-facing patch-Y.mpq via
-- apps/dbc-tools/patch_gt_tables.py once this is applied (its tooltip math reads a copy of these
-- same two DBCs - see that script's docstring for why).
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2200;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2201;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2202;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2203;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2204;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2205;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2206;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2207;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2208;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.269231 WHERE `ID` = 2209;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.403846 WHERE `ID` = 2210;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.53846 WHERE `ID` = 2211;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.673075 WHERE `ID` = 2212;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.807695 WHERE `ID` = 2213;
UPDATE `gtcombatratings_dbc` SET `Data` = 0.942305 WHERE `ID` = 2214;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.07692 WHERE `ID` = 2215;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.21154 WHERE `ID` = 2216;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.34615 WHERE `ID` = 2217;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.48077 WHERE `ID` = 2218;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.61539 WHERE `ID` = 2219;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.75 WHERE `ID` = 2220;
UPDATE `gtcombatratings_dbc` SET `Data` = 1.88461 WHERE `ID` = 2221;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.01923 WHERE `ID` = 2222;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.15385 WHERE `ID` = 2223;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.28846 WHERE `ID` = 2224;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.42307 WHERE `ID` = 2225;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.55769 WHERE `ID` = 2226;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.69231 WHERE `ID` = 2227;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.82693 WHERE `ID` = 2228;
UPDATE `gtcombatratings_dbc` SET `Data` = 2.96154 WHERE `ID` = 2229;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.09615 WHERE `ID` = 2230;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.23077 WHERE `ID` = 2231;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.36538 WHERE `ID` = 2232;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.5 WHERE `ID` = 2233;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.63462 WHERE `ID` = 2234;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.76923 WHERE `ID` = 2235;
UPDATE `gtcombatratings_dbc` SET `Data` = 3.90385 WHERE `ID` = 2236;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.03846 WHERE `ID` = 2237;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.17307 WHERE `ID` = 2238;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.30769 WHERE `ID` = 2239;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.44231 WHERE `ID` = 2240;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.57693 WHERE `ID` = 2241;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.71154 WHERE `ID` = 2242;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.84616 WHERE `ID` = 2243;
UPDATE `gtcombatratings_dbc` SET `Data` = 4.98077 WHERE `ID` = 2244;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.1154 WHERE `ID` = 2245;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.25 WHERE `ID` = 2246;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.3846 WHERE `ID` = 2247;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.51925 WHERE `ID` = 2248;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.65385 WHERE `ID` = 2249;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.78845 WHERE `ID` = 2250;
UPDATE `gtcombatratings_dbc` SET `Data` = 5.9231 WHERE `ID` = 2251;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.0577 WHERE `ID` = 2252;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.1923 WHERE `ID` = 2253;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.3269 WHERE `ID` = 2254;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.46155 WHERE `ID` = 2255;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.59615 WHERE `ID` = 2256;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.73075 WHERE `ID` = 2257;
UPDATE `gtcombatratings_dbc` SET `Data` = 6.8654 WHERE `ID` = 2258;
UPDATE `gtcombatratings_dbc` SET `Data` = 7 WHERE `ID` = 2259;
UPDATE `gtcombatratings_dbc` SET `Data` = 7.2658 WHERE `ID` = 2260;
UPDATE `gtcombatratings_dbc` SET `Data` = 7.55265 WHERE `ID` = 2261;
UPDATE `gtcombatratings_dbc` SET `Data` = 7.863 WHERE `ID` = 2262;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.2 WHERE `ID` = 2263;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.56715 WHERE `ID` = 2264;
UPDATE `gtcombatratings_dbc` SET `Data` = 8.96875 WHERE `ID` = 2265;
UPDATE `gtcombatratings_dbc` SET `Data` = 9.40985 WHERE `ID` = 2266;
UPDATE `gtcombatratings_dbc` SET `Data` = 9.89655 WHERE `ID` = 2267;
UPDATE `gtcombatratings_dbc` SET `Data` = 10.4363 WHERE `ID` = 2268;
UPDATE `gtcombatratings_dbc` SET `Data` = 11.0384 WHERE `ID` = 2269;
UPDATE `gtcombatratings_dbc` SET `Data` = 11.8768 WHERE `ID` = 2270;
UPDATE `gtcombatratings_dbc` SET `Data` = 12.779 WHERE `ID` = 2271;
UPDATE `gtcombatratings_dbc` SET `Data` = 13.7495 WHERE `ID` = 2272;
UPDATE `gtcombatratings_dbc` SET `Data` = 14.7939 WHERE `ID` = 2273;
UPDATE `gtcombatratings_dbc` SET `Data` = 15.9175 WHERE `ID` = 2274;
UPDATE `gtcombatratings_dbc` SET `Data` = 17.1264 WHERE `ID` = 2275;
UPDATE `gtcombatratings_dbc` SET `Data` = 18.4273 WHERE `ID` = 2276;
UPDATE `gtcombatratings_dbc` SET `Data` = 19.8268 WHERE `ID` = 2277;
UPDATE `gtcombatratings_dbc` SET `Data` = 21.3327 WHERE `ID` = 2278;
UPDATE `gtcombatratings_dbc` SET `Data` = 22.953 WHERE `ID` = 2279;
UPDATE `gtcombatratings_dbc` SET `Data` = 24.6963 WHERE `ID` = 2280;
UPDATE `gtcombatratings_dbc` SET `Data` = 26.5721 WHERE `ID` = 2281;
UPDATE `gtcombatratings_dbc` SET `Data` = 28.5903 WHERE `ID` = 2282;
UPDATE `gtcombatratings_dbc` SET `Data` = 30.7618 WHERE `ID` = 2283;
UPDATE `gtcombatratings_dbc` SET `Data` = 33.0982 WHERE `ID` = 2284;
UPDATE `gtcombatratings_dbc` SET `Data` = 35.6121 WHERE `ID` = 2285;
UPDATE `gtcombatratings_dbc` SET `Data` = 38.3169 WHERE `ID` = 2286;
UPDATE `gtcombatratings_dbc` SET `Data` = 41.2272 WHERE `ID` = 2287;
UPDATE `gtcombatratings_dbc` SET `Data` = 44.3585 WHERE `ID` = 2288;
UPDATE `gtcombatratings_dbc` SET `Data` = 47.7276 WHERE `ID` = 2289;
UPDATE `gtcombatratings_dbc` SET `Data` = 51.3525 WHERE `ID` = 2290;
UPDATE `gtcombatratings_dbc` SET `Data` = 55.253 WHERE `ID` = 2291;
UPDATE `gtcombatratings_dbc` SET `Data` = 59.4495 WHERE `ID` = 2292;
UPDATE `gtcombatratings_dbc` SET `Data` = 63.965 WHERE `ID` = 2293;
UPDATE `gtcombatratings_dbc` SET `Data` = 68.8235 WHERE `ID` = 2294;
UPDATE `gtcombatratings_dbc` SET `Data` = 74.0505 WHERE `ID` = 2295;
UPDATE `gtcombatratings_dbc` SET `Data` = 79.675 WHERE `ID` = 2296;
UPDATE `gtcombatratings_dbc` SET `Data` = 85.7265 WHERE `ID` = 2297;
UPDATE `gtcombatratings_dbc` SET `Data` = 92.2375 WHERE `ID` = 2298;
UPDATE `gtcombatratings_dbc` SET `Data` = 99.243 WHERE `ID` = 2299;

