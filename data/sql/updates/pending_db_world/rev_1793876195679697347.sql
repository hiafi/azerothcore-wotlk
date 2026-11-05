-- progression-slim WP-D2: mod-content-gate bundles. Each bundle with spawns owns one always-on game event
-- (200-215, ids.yaml block game_event_bundle 200-255); the module disables the event while the bundle is closed.
-- Members (quests, loot) are applied as disables while closed. Classification: progression-slim.D2-TABLE.md,
-- signed off 2026-11-05 (decision 2 changed: Ogri'la and Skyguard ride with `outland`).
-- The two content_gate_* tables come from modules/mod-content-gate/data/sql/db-world/base/content_gate_tables.sql
-- (module SQL; its file name sorts before every rev_* file, so db-import creates them first).

-- Rows that become bundle members must leave `disables` (an existing DB key cannot be overridden in memory)
DELETE FROM `disables` WHERE `sourceType` = 1 AND `entry` IN (11009, 11130, 11481);
DELETE FROM `disables` WHERE `sourceType` = 10 AND `entry` IN (21877, 27859, 27860, 31952);

-- Bundle events: always on (occurence = length, start_time keeps its default 2000-01-01 18:00:00, end far
-- ahead); holiday, holidayStage and world_event keep their default 0; announce 0
DELETE FROM `game_event` WHERE `eventEntry` BETWEEN 200 AND 215;
INSERT INTO `game_event` (`eventEntry`, `end_time`, `occurence`, `length`, `description`, `announce`) VALUES
(200, '2037-12-31 00:00:00', 525600, 525600, 'Content gate bundle: molten_core', 0),
(201, '2037-12-31 00:00:00', 525600, 525600, 'Content gate bundle: onyxia', 0),
(202, '2037-12-31 00:00:00', 525600, 525600, 'Content gate bundle: zul_gurub', 0),
(203, '2037-12-31 00:00:00', 525600, 525600, 'Content gate bundle: blackwing_lair', 0),
(204, '2037-12-31 00:00:00', 525600, 525600, 'Content gate bundle: ahn_qiraj', 0),
(205, '2037-12-31 00:00:00', 525600, 525600, 'Content gate bundle: arenas', 0),
(206, '2037-12-31 00:00:00', 525600, 525600, 'Content gate bundle: outland', 0),
(207, '2037-12-31 00:00:00', 525600, 525600, 'Content gate bundle: caverns_of_time', 0),
(208, '2037-12-31 00:00:00', 525600, 525600, 'Content gate bundle: karazhan', 0),
(209, '2037-12-31 00:00:00', 525600, 525600, 'Content gate bundle: zul_aman', 0),
(210, '2037-12-31 00:00:00', 525600, 525600, 'Content gate bundle: black_temple', 0),
(211, '2037-12-31 00:00:00', 525600, 525600, 'Content gate bundle: sunwell', 0),
(212, '2037-12-31 00:00:00', 525600, 525600, 'Content gate bundle: northrend', 0),
(213, '2037-12-31 00:00:00', 525600, 525600, 'Content gate bundle: wotlk_t7', 0),
(214, '2037-12-31 00:00:00', 525600, 525600, 'Content gate bundle: wotlk_t8', 0),
(215, '2037-12-31 00:00:00', 525600, 525600, 'Content gate bundle: wotlk_t9', 0);

-- molten_core (event 200): 1 creatures, 1 gameobjects, phaseMask 1, presence by the event
UPDATE `creature` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (14387)
    AND `guid` IN (3328);
DELETE FROM `game_event_creature` WHERE `eventEntry` = 200;
INSERT INTO `game_event_creature` (`eventEntry`, `guid`) VALUES
(200, 3328);
UPDATE `gameobject` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (179553)
    AND `guid` IN (43133);
DELETE FROM `game_event_gameobject` WHERE `eventEntry` = 200;
INSERT INTO `game_event_gameobject` (`eventEntry`, `guid`) VALUES
(200, 43133);

-- onyxia (event 201): 2 creatures, 1 gameobjects, phaseMask 1, presence by the event
UPDATE `creature` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (10182, 10321)
    AND `guid` IN (29113, 31041);
DELETE FROM `game_event_creature` WHERE `eventEntry` = 201;
INSERT INTO `game_event_creature` (`eventEntry`, `guid`) VALUES
(201, 29113), (201, 31041);
UPDATE `gameobject` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (185321)
    AND `guid` IN (7013);
DELETE FROM `game_event_gameobject` WHERE `eventEntry` = 201;
INSERT INTO `game_event_gameobject` (`eventEntry`, `guid`) VALUES
(201, 7013);

-- zul_gurub (event 202): 24 creatures, 3 gameobjects, phaseMask 1, presence by the event
UPDATE `creature` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (6109, 12397, 14875, 14876, 14902, 14903, 14904, 14905, 14910, 14911, 14912, 14921, 15070, 15076, 15080)
    AND `guid` IN (
        280, 281, 282, 283, 284, 285, 286, 287, 288, 309, 310, 311, 312, 314, 366, 385, 386, 391, 436, 723, 2368,
        52349, 200615, 5300002);
DELETE FROM `game_event_creature` WHERE `eventEntry` = 202;
INSERT INTO `game_event_creature` (`eventEntry`, `guid`) VALUES
(202, 280), (202, 281), (202, 282), (202, 283), (202, 284), (202, 285), (202, 286), (202, 287),
(202, 288), (202, 309), (202, 310), (202, 311), (202, 312), (202, 314), (202, 366), (202, 385),
(202, 386), (202, 391), (202, 436), (202, 723), (202, 2368), (202, 52349), (202, 200615), (202, 5300002);
UPDATE `gameobject` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (180104, 180367, 180375)
    AND `guid` IN (10089, 11027, 99897);
DELETE FROM `game_event_gameobject` WHERE `eventEntry` = 202;
INSERT INTO `game_event_gameobject` (`eventEntry`, `guid`) VALUES
(202, 10089), (202, 11027), (202, 99897);

-- blackwing_lair (event 203): 4 creatures, 2 gameobjects, phaseMask 1, presence by the event
UPDATE `creature` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (14887, 14888, 14889, 14890)
    AND `guid` IN (4256, 32343, 50012, 52350);
DELETE FROM `game_event_creature` WHERE `eventEntry` = 203;
INSERT INTO `game_event_creature` (`eventEntry`, `guid`) VALUES
(203, 4256), (203, 32343), (203, 50012), (203, 52350);
UPDATE `gameobject` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (179879, 179880)
    AND `guid` IN (4510, 35869);
DELETE FROM `game_event_gameobject` WHERE `eventEntry` = 203;
INSERT INTO `game_event_gameobject` (`eventEntry`, `guid`) VALUES
(203, 4510), (203, 35869);

-- ahn_qiraj (event 204): 1 creatures, 1 gameobjects, phaseMask 1, presence by the event
UPDATE `creature` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (15481)
    AND `guid` IN (35867);
DELETE FROM `game_event_creature` WHERE `eventEntry` = 204;
INSERT INTO `game_event_creature` (`eventEntry`, `guid`) VALUES
(204, 35867);
UPDATE `gameobject` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (180717)
    AND `guid` IN (49451);
DELETE FROM `game_event_gameobject` WHERE `eventEntry` = 204;
INSERT INTO `game_event_gameobject` (`eventEntry`, `guid`) VALUES
(204, 49451);

-- arenas (event 205): 11 creatures, 0 gameobjects, phaseMask 1, presence by the event
UPDATE `creature` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (19859, 19860, 19861, 19909, 19911, 19912, 19915, 20497, 20499, 30610, 30611)
    AND `guid` IN (81, 4762, 23278, 23279, 23280, 24709, 32069, 46187, 68938, 137651, 137652);
DELETE FROM `game_event_creature` WHERE `eventEntry` = 205;
INSERT INTO `game_event_creature` (`eventEntry`, `guid`) VALUES
(205, 81), (205, 4762), (205, 23278), (205, 23279), (205, 23280), (205, 24709), (205, 32069), (205, 46187),
(205, 68938), (205, 137651), (205, 137652);

-- outland (event 206): 108 creatures, 30 gameobjects, phaseMask 1, presence by the event
UPDATE `creature` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (
        20613, 20616, 20807, 20808, 21432, 21905, 21906, 22264, 22266, 22270, 22271, 22836, 22982, 22987, 23016,
        23038, 23042, 23048, 23110, 23112, 23115, 23120, 23208, 23233, 23253, 23256, 23257, 23300, 23306, 23316,
        23334, 23335, 23347, 23362, 23367, 23392, 23413, 23415, 23428, 23449, 23473, 30721, 30722, 30734, 30735,
        33608, 33609, 33610, 33611, 33612, 33613, 33614, 33615, 33616, 33617, 33618, 33619, 33621, 33623, 33630,
        33631, 33634, 33635, 33636, 33638, 33639, 33641, 33674, 33675, 33677, 33678, 33679, 33681, 33683, 33684,
        34999, 35000, 35093, 35099, 35100, 35101)
    AND `guid` IN (
        3414, 10497, 34034, 40266, 40510, 40516, 40517, 40518, 40601, 40602, 40603, 41320, 41674, 41723, 41775,
        41779, 41780, 44254, 44255, 44256, 44257, 47642, 47646, 47651, 48165, 48166, 48167, 52535, 72880, 72884,
        73498, 73499, 74807, 75088, 75089, 76643, 76644, 78262, 78263, 78264, 78265, 78266, 78267, 79004, 79005,
        79007, 79008, 79009, 79010, 79011, 79012, 79013, 79014, 79015, 79021, 79022, 79023, 79024, 79025, 79026,
        79027, 79028, 79030, 79031, 79032, 79033, 79487, 79497, 79503, 79512, 84645, 88165, 88166, 88252, 88254,
        88259, 88260, 88261, 88262, 88263, 88264, 88265, 88269, 88270, 88271, 88272, 88273, 91780, 91781, 91782,
        91783, 91784, 91785, 91786, 91787, 91788, 91789, 91790, 91791, 91792, 91793, 91795, 91796, 91797, 96666,
        135120, 202334, 203518);
DELETE FROM `game_event_creature` WHERE `eventEntry` = 206;
INSERT INTO `game_event_creature` (`eventEntry`, `guid`) VALUES
(206, 3414), (206, 10497), (206, 34034), (206, 40266), (206, 40510), (206, 40516), (206, 40517), (206, 40518),
(206, 40601), (206, 40602), (206, 40603), (206, 41320), (206, 41674), (206, 41723), (206, 41775), (206, 41779),
(206, 41780), (206, 44254), (206, 44255), (206, 44256), (206, 44257), (206, 47642), (206, 47646), (206, 47651),
(206, 48165), (206, 48166), (206, 48167), (206, 52535), (206, 72880), (206, 72884), (206, 73498), (206, 73499),
(206, 74807), (206, 75088), (206, 75089), (206, 76643), (206, 76644), (206, 78262), (206, 78263), (206, 78264),
(206, 78265), (206, 78266), (206, 78267), (206, 79004), (206, 79005), (206, 79007), (206, 79008), (206, 79009),
(206, 79010), (206, 79011), (206, 79012), (206, 79013), (206, 79014), (206, 79015), (206, 79021), (206, 79022),
(206, 79023), (206, 79024), (206, 79025), (206, 79026), (206, 79027), (206, 79028), (206, 79030), (206, 79031),
(206, 79032), (206, 79033), (206, 79487), (206, 79497), (206, 79503), (206, 79512), (206, 84645), (206, 88165),
(206, 88166), (206, 88252), (206, 88254), (206, 88259), (206, 88260), (206, 88261), (206, 88262), (206, 88263),
(206, 88264), (206, 88265), (206, 88269), (206, 88270), (206, 88271), (206, 88272), (206, 88273), (206, 91780),
(206, 91781), (206, 91782), (206, 91783), (206, 91784), (206, 91785), (206, 91786), (206, 91787), (206, 91788),
(206, 91789), (206, 91790), (206, 91791), (206, 91792), (206, 91793), (206, 91795), (206, 91796), (206, 91797),
(206, 96666), (206, 135120), (206, 202334), (206, 203518);
UPDATE `gameobject` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (178764, 178765, 181310, 181664, 183421, 183930, 184146, 185544, 185602, 185906, 185965, 187299, 193981)
    AND `guid` IN (
        929, 14130, 14134, 21637, 24779, 27636, 27637, 27638, 27639, 42953, 42954, 50675, 50676, 50677, 50678,
        50679, 50680, 50681, 50682, 50683, 50684, 50685, 50686, 50687, 50688, 50689, 50690, 50691, 50692, 100257);
DELETE FROM `game_event_gameobject` WHERE `eventEntry` = 206;
INSERT INTO `game_event_gameobject` (`eventEntry`, `guid`) VALUES
(206, 929), (206, 14130), (206, 14134), (206, 21637), (206, 24779), (206, 27636), (206, 27637), (206, 27638),
(206, 27639), (206, 42953), (206, 42954), (206, 50675), (206, 50676), (206, 50677), (206, 50678), (206, 50679),
(206, 50680), (206, 50681), (206, 50682), (206, 50683), (206, 50684), (206, 50685), (206, 50686), (206, 50687),
(206, 50688), (206, 50689), (206, 50690), (206, 50691), (206, 50692), (206, 100257);

-- caverns_of_time (event 207): 0 creatures, 1 gameobjects, phaseMask 1, presence by the event
UPDATE `gameobject` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (182560)
    AND `guid` IN (17269);
DELETE FROM `game_event_gameobject` WHERE `eventEntry` = 207;
INSERT INTO `game_event_gameobject` (`eventEntry`, `guid`) VALUES
(207, 17269);

-- karazhan (event 208): 3 creatures, 1 gameobjects, phaseMask 1, presence by the event
UPDATE `creature` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (17711, 18728, 23948)
    AND `guid` IN (84633, 94503, 96999);
DELETE FROM `game_event_creature` WHERE `eventEntry` = 208;
INSERT INTO `game_event_creature` (`eventEntry`, `guid`) VALUES
(208, 84633), (208, 94503), (208, 96999);
UPDATE `gameobject` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (184463)
    AND `guid` IN (14003);
DELETE FROM `game_event_gameobject` WHERE `eventEntry` = 208;
INSERT INTO `game_event_gameobject` (`eventEntry`, `guid`) VALUES
(208, 14003);

-- zul_aman (event 209): 37 creatures, 1 gameobjects, phaseMask 1, presence by the event
UPDATE `creature` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (23559, 23560, 23718, 23724, 23745, 23747, 23748, 23761, 23762, 23764, 23766, 23858, 24851, 25145)
    AND `guid` IN (
        139263, 139264, 139273, 139274, 139275, 139326, 139327, 139328, 139329, 139330, 139331, 139332, 139333,
        139334, 139335, 139336, 139337, 139338, 139339, 139340, 139341, 139342, 139343, 139344, 139345, 139346,
        139347, 139348, 139349, 139350, 139351, 139352, 139353, 139354, 139355, 139356, 139357);
DELETE FROM `game_event_creature` WHERE `eventEntry` = 209;
INSERT INTO `game_event_creature` (`eventEntry`, `guid`) VALUES
(209, 139263), (209, 139264), (209, 139273), (209, 139274), (209, 139275), (209, 139326), (209, 139327), (209, 139328),
(209, 139329), (209, 139330), (209, 139331), (209, 139332), (209, 139333), (209, 139334), (209, 139335), (209, 139336),
(209, 139337), (209, 139338), (209, 139339), (209, 139340), (209, 139341), (209, 139342), (209, 139343), (209, 139344),
(209, 139345), (209, 139346), (209, 139347), (209, 139348), (209, 139349), (209, 139350), (209, 139351), (209, 139352),
(209, 139353), (209, 139354), (209, 139355), (209, 139356), (209, 139357);
UPDATE `gameobject` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (186251)
    AND `guid` IN (100514);
DELETE FROM `game_event_gameobject` WHERE `eventEntry` = 209;
INSERT INTO `game_event_gameobject` (`eventEntry`, `guid`) VALUES
(209, 100514);

-- black_temple (event 210): 9 creatures, 1 gameobjects, phaseMask 1, presence by the event
UPDATE `creature` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (21700, 21701, 21826, 21962, 22820)
    AND `guid` IN (75728, 75729, 75730, 75731, 75732, 75733, 76414, 138997, 153158);
DELETE FROM `game_event_creature` WHERE `eventEntry` = 210;
INSERT INTO `game_event_creature` (`eventEntry`, `guid`) VALUES
(210, 75728), (210, 75729), (210, 75730), (210, 75731), (210, 75732), (210, 75733), (210, 76414), (210, 138997),
(210, 153158);
UPDATE `gameobject` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (185474)
    AND `guid` IN (265632);
DELETE FROM `game_event_gameobject` WHERE `eventEntry` = 210;
INSERT INTO `game_event_gameobject` (`eventEntry`, `guid`) VALUES
(210, 265632);

-- sunwell (event 211): 67 creatures, 1 gameobjects, phaseMask 1, presence by the event
UPDATE `creature` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (
        5202, 18594, 19202, 19216, 19475, 25134, 25135, 25136, 25137, 25138, 25140, 25141, 25142, 25143, 25153,
        25155, 25167, 25885)
    AND `guid` IN (
        34137, 34138, 34139, 66758, 96590, 96591, 96592, 96594, 96595, 96596, 96597, 96598, 96599, 96600, 96601,
        96602, 96603, 96604, 96605, 96606, 96607, 96608, 96609, 96610, 96611, 96612, 96613, 96614, 96615, 96616,
        96617, 96618, 96619, 96620, 96621, 96622, 96623, 96624, 96625, 96626, 96627, 96628, 96629, 96630, 96631,
        96632, 96633, 96634, 96635, 96636, 96637, 96638, 96639, 96640, 96641, 96642, 96643, 96644, 96645, 96646,
        96647, 96648, 96649, 96650, 96651, 96652, 96653);
DELETE FROM `game_event_creature` WHERE `eventEntry` = 211;
INSERT INTO `game_event_creature` (`eventEntry`, `guid`) VALUES
(211, 34137), (211, 34138), (211, 34139), (211, 66758), (211, 96590), (211, 96591), (211, 96592), (211, 96594),
(211, 96595), (211, 96596), (211, 96597), (211, 96598), (211, 96599), (211, 96600), (211, 96601), (211, 96602),
(211, 96603), (211, 96604), (211, 96605), (211, 96606), (211, 96607), (211, 96608), (211, 96609), (211, 96610),
(211, 96611), (211, 96612), (211, 96613), (211, 96614), (211, 96615), (211, 96616), (211, 96617), (211, 96618),
(211, 96619), (211, 96620), (211, 96621), (211, 96622), (211, 96623), (211, 96624), (211, 96625), (211, 96626),
(211, 96627), (211, 96628), (211, 96629), (211, 96630), (211, 96631), (211, 96632), (211, 96633), (211, 96634),
(211, 96635), (211, 96636), (211, 96637), (211, 96638), (211, 96639), (211, 96640), (211, 96641), (211, 96642),
(211, 96643), (211, 96644), (211, 96645), (211, 96646), (211, 96647), (211, 96648), (211, 96649), (211, 96650),
(211, 96651), (211, 96652), (211, 96653);
UPDATE `gameobject` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (183435)
    AND `guid` IN (24341);
DELETE FROM `game_event_gameobject` WHERE `eventEntry` = 211;
INSERT INTO `game_event_gameobject` (`eventEntry`, `guid`) VALUES
(211, 24341);

-- northrend (event 212): 14 creatures, 1 gameobjects, phaseMask 1, presence by the event
UPDATE `creature` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (23745, 23762, 23764, 23766, 35596, 35597, 35598, 35599, 35600, 35601, 35602, 35603, 35611, 35612)
    AND `guid` IN (
        63451, 63452, 63453, 88243, 88245, 88248, 88251, 114137, 115711, 115887, 116141, 137647, 137648, 202481);
DELETE FROM `game_event_creature` WHERE `eventEntry` = 212;
INSERT INTO `game_event_creature` (`eventEntry`, `guid`) VALUES
(212, 63451), (212, 63452), (212, 63453), (212, 88243), (212, 88245), (212, 88248), (212, 88251), (212, 114137),
(212, 115711), (212, 115887), (212, 116141), (212, 137647), (212, 137648), (212, 202481);
UPDATE `gameobject` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (187299)
    AND `guid` IN (59749);
DELETE FROM `game_event_gameobject` WHERE `eventEntry` = 212;
INSERT INTO `game_event_gameobject` (`eventEntry`, `guid`) VALUES
(212, 59749);

-- wotlk_t7 (event 213): 2 creatures, 0 gameobjects, phaseMask 1, presence by the event
UPDATE `creature` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (31579, 31581)
    AND `guid` IN (104206, 104241);
DELETE FROM `game_event_creature` WHERE `eventEntry` = 213;
INSERT INTO `game_event_creature` (`eventEntry`, `guid`) VALUES
(213, 104206), (213, 104241);

-- wotlk_t8 (event 214): 10 creatures, 0 gameobjects, phaseMask 1, presence by the event
UPDATE `creature` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (33963, 33964, 33993, 34015, 35013, 35143, 35494, 35495)
    AND `guid` IN (85217, 85224, 86928, 86929, 202593, 202594, 202595, 202596, 202597, 202598);
DELETE FROM `game_event_creature` WHERE `eventEntry` = 214;
INSERT INTO `game_event_creature` (`eventEntry`, `guid`) VALUES
(214, 85217), (214, 85224), (214, 86928), (214, 86929), (214, 202593), (214, 202594), (214, 202595), (214, 202596),
(214, 202597), (214, 202598);

-- wotlk_t9 (event 215): 10 creatures, 0 gameobjects, phaseMask 1, presence by the event
UPDATE `creature` SET `phaseMask` = 1 WHERE `phaseMask` = 16384
    AND `id` IN (37523, 37527, 37776, 37780, 37941, 37942, 38433, 38482)
    AND `guid` IN (4761, 43498, 101236, 133649, 202582, 202600, 202605, 202606, 1976590, 1976591);
DELETE FROM `game_event_creature` WHERE `eventEntry` = 215;
INSERT INTO `game_event_creature` (`eventEntry`, `guid`) VALUES
(215, 4761), (215, 43498), (215, 101236), (215, 133649), (215, 202582), (215, 202600), (215, 202605), (215, 202606),
(215, 1976590), (215, 1976591);

-- Bundles (gameEvent 0 = quest/loot members only)
DELETE FROM `content_gate_bundle` WHERE `name` = 'molten_core';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('molten_core', 200, 'map:409:N', 'Molten Core: Lothos Riftwaker, Core Fragment');
DELETE FROM `content_gate_bundle` WHERE `name` = 'onyxia';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('onyxia', 201, 'map:249:N', 'Onyxia\'s Lair: Rokaro, Emberstrife, meeting stone, Warlord\'s Command');
DELETE FROM `content_gate_bundle` WHERE `name` = 'zul_gurub';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('zul_gurub', 202, 'map:309:N', 'Zul\'Gurub: Yojamba Isle camp, Azuregos, Lord Kazzak, Confront Yeh\'kinya');
DELETE FROM `content_gate_bundle` WHERE `name` = 'blackwing_lair';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('blackwing_lair', 203, 'map:469:N', 'BWL: Orb of Command, Drakkisath\'s Brand, Emerald Dragons, quest loot');
DELETE FROM `content_gate_bundle` WHERE `name` = 'ahn_qiraj';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('ahn_qiraj', 204, 'map:509:N', 'Ahn\'Qiraj: Spirit of Azuregos, Scarab Gong, 31 AQ quests');
DELETE FROM `content_gate_bundle` WHERE `name` = 'arenas';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('arenas', 205, 'bg:6', 'Arena battlemasters and organizers');
DELETE FROM `content_gate_bundle` WHERE `name` = 'outland';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('outland', 206, 'outland', 'Outland: Shattrath and Hellfire services, Ogri\'la, Skyguard, Outland loot');
DELETE FROM `content_gate_bundle` WHERE `name` = 'caverns_of_time';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('caverns_of_time', 207, 'map:560:N', 'Caverns of Time meeting stone');
DELETE FROM `content_gate_bundle` WHERE `name` = 'karazhan';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('karazhan', 208, 'map:532:N', 'Karazhan: meeting stone, Tasserel, Doomwalker, Doom Lord Kazzak');
DELETE FROM `content_gate_bundle` WHERE `name` = 'zul_aman';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('zul_aman', 209, 'map:568:N', 'Zul\'Aman: Budd Nedreck\'s camp, meeting stone, Oooh, Shinies!');
DELETE FROM `content_gate_bundle` WHERE `name` = 'black_temple';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('black_temple', 210, 'map:564:N', 'Black Temple: Akama chain, The Warden\'s Cage');
DELETE FROM `content_gate_bundle` WHERE `name` = 'sunwell';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('sunwell', 211, 'map:580:N', 'Sunwell: Shattered Sun Offensive, Crisis at the Sunwell');
DELETE FROM `content_gate_bundle` WHERE `name` = 'northrend';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('northrend', 212, 'northrend', 'Northrend: Wintergrasp Battle-Mages, Grizzly Hills crew, Dalaran vault');
DELETE FROM `content_gate_bundle` WHERE `name` = 'wotlk_t7';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('wotlk_t7', 213, 'map:533:10N', 'WotLK T7: Emblem of Valor quartermasters');
DELETE FROM `content_gate_bundle` WHERE `name` = 'wotlk_t8';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('wotlk_t8', 214, 'map:603:10N', 'WotLK T8: Conquest and Triumph quartermasters, Emalon, Koralon');
DELETE FROM `content_gate_bundle` WHERE `name` = 'wotlk_t9';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('wotlk_t9', 215, 'map:631:10N', 'WotLK T9: Frost QMs, Toravon, ICC intro, Quel\'Delar chain');
DELETE FROM `content_gate_bundle` WHERE `name` = 'hyjal';
INSERT INTO `content_gate_bundle` (`name`, `gameEvent`, `opensWith`, `comment`) VALUES
('hyjal', 0, 'map:534:N', 'Hyjal Summit: the four pledges, The Vials of Eternity (quests only)');

-- Bundle members: disabled while the bundle is closed (sourceType 1 quest, 10 loot)
DELETE FROM `content_gate_bundle_disable` WHERE `bundle` = 'onyxia';
INSERT INTO `content_gate_bundle_disable` (`bundle`, `sourceType`, `entry`, `comment`) VALUES
('onyxia', 1, 4903, 'Warlord\'s Command');
DELETE FROM `content_gate_bundle_disable` WHERE `bundle` = 'zul_gurub';
INSERT INTO `content_gate_bundle_disable` (`bundle`, `sourceType`, `entry`, `comment`) VALUES
('zul_gurub', 1, 8181, 'Confront Yeh\'kinya');
DELETE FROM `content_gate_bundle_disable` WHERE `bundle` = 'ahn_qiraj';
INSERT INTO `content_gate_bundle_disable` (`bundle`, `sourceType`, `entry`, `comment`) VALUES
('ahn_qiraj', 1, 8286, 'What Tomorrow Brings'),
('ahn_qiraj', 1, 8556, 'Signet of Unyielding Strength'),
('ahn_qiraj', 1, 8557, 'Drape of Unyielding Strength'),
('ahn_qiraj', 1, 8558, 'Sickle of Unyielding Strength'),
('ahn_qiraj', 1, 8689, 'Shroud of Infinite Wisdom'),
('ahn_qiraj', 1, 8690, 'Cloak of the Gathering Storm'),
('ahn_qiraj', 1, 8691, 'Drape of Vaulted Secrets'),
('ahn_qiraj', 1, 8692, 'Cloak of Unending Life'),
('ahn_qiraj', 1, 8693, 'Cloak of Veiled Shadows'),
('ahn_qiraj', 1, 8694, 'Shroud of Unspoken Names'),
('ahn_qiraj', 1, 8695, 'Cape of Eternal Justice'),
('ahn_qiraj', 1, 8696, 'Cloak of the Unseen Path'),
('ahn_qiraj', 1, 8697, 'Ring of Infinite Wisdom'),
('ahn_qiraj', 1, 8698, 'Ring of the Gathering Storm'),
('ahn_qiraj', 1, 8699, 'Band of Vaulted Secrets'),
('ahn_qiraj', 1, 8700, 'Band of Unending Life'),
('ahn_qiraj', 1, 8701, 'Band of Veiled Shadows'),
('ahn_qiraj', 1, 8702, 'Ring of Unspoken Names'),
('ahn_qiraj', 1, 8703, 'Ring of Eternal Justice'),
('ahn_qiraj', 1, 8704, 'Signet of the Unseen Path'),
('ahn_qiraj', 1, 8705, 'Gavel of Infinite Wisdom'),
('ahn_qiraj', 1, 8706, 'Hammer of the Gathering Storm'),
('ahn_qiraj', 1, 8707, 'Blade of Vaulted Secrets'),
('ahn_qiraj', 1, 8708, 'Mace of Unending Life'),
('ahn_qiraj', 1, 8709, 'Dagger of Veiled Shadows'),
('ahn_qiraj', 1, 8710, 'Kris of Unspoken Names'),
('ahn_qiraj', 1, 8711, 'Blade of Eternal Justice'),
('ahn_qiraj', 1, 8712, 'Scythe of the Unseen Path'),
('ahn_qiraj', 1, 8800, 'Cenarion Battlegear'),
('ahn_qiraj', 1, 9023, 'The Perfect Poison'),
('ahn_qiraj', 1, 9248, 'A Humble Offering');
DELETE FROM `content_gate_bundle_disable` WHERE `bundle` = 'blackwing_lair';
INSERT INTO `content_gate_bundle_disable` (`bundle`, `sourceType`, `entry`, `comment`) VALUES
('blackwing_lair', 10, 18563, 'Bindings of the Windseeker'),
('blackwing_lair', 10, 18564, 'Bindings of the Windseeker'),
('blackwing_lair', 10, 18646, 'The Eye of Divinity'),
('blackwing_lair', 10, 18665, 'The Eye of Shadow'),
('blackwing_lair', 10, 18705, 'Mature Black Dragon Sinew'),
('blackwing_lair', 10, 18987, 'Blackhand\'s Command');
DELETE FROM `content_gate_bundle_disable` WHERE `bundle` = 'outland';
INSERT INTO `content_gate_bundle_disable` (`bundle`, `sourceType`, `entry`, `comment`) VALUES
('outland', 1, 11009, 'Ogre Heaven'),
('outland', 10, 21877, 'Netherweave Cloth'),
('outland', 10, 27859, 'Zangar Caps'),
('outland', 10, 27860, 'Purified Draenic Water'),
('outland', 10, 31952, 'Khorium Lockbox');
DELETE FROM `content_gate_bundle_disable` WHERE `bundle` = 'zul_aman';
INSERT INTO `content_gate_bundle_disable` (`bundle`, `sourceType`, `entry`, `comment`) VALUES
('zul_aman', 1, 11130, 'Oooh, Shinies!');
DELETE FROM `content_gate_bundle_disable` WHERE `bundle` = 'black_temple';
INSERT INTO `content_gate_bundle_disable` (`bundle`, `sourceType`, `entry`, `comment`) VALUES
('black_temple', 1, 10575, 'The Warden\'s Cage'),
('black_temple', 1, 10686, 'The Warden\'s Cage');
DELETE FROM `content_gate_bundle_disable` WHERE `bundle` = 'sunwell';
INSERT INTO `content_gate_bundle_disable` (`bundle`, `sourceType`, `entry`, `comment`) VALUES
('sunwell', 1, 11481, 'Crisis at the Sunwell');
DELETE FROM `content_gate_bundle_disable` WHERE `bundle` = 'hyjal';
INSERT INTO `content_gate_bundle_disable` (`bundle`, `sourceType`, `entry`, `comment`) VALUES
('hyjal', 1, 10460, 'Defender\'s Pledge'),
('hyjal', 1, 10461, 'Restorer\'s Pledge'),
('hyjal', 1, 10462, 'Champion\'s Pledge'),
('hyjal', 1, 10463, 'Sage\'s Pledge'),
('hyjal', 1, 13432, 'The Vials of Eternity');
