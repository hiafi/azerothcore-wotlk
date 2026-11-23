-- Scarlet Monastery build WP-D8H: Arcanist Doan's hard mode, the Kel'Thuzad Heresy (heroic only), the rows dbc-tools
-- cannot declare (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.7, s3.8 row "D8H pages",
-- s7 #27 A; build spec docs/dungeons/scarlet-monastery-2-library.md "Hard mode: The Kel'Thuzad Heresy"). The Phylactery
-- Shard 300920, the Risen Purged 300921 and the spells 212710-212715 are apps/dbc-tools
-- source/npcs/scarlet_monastery/doan_hard_mode.py; the engine side is modules/mod-dungeon-bosses
-- src/ScarletMonastery/doan_hard_mode.cpp (spots and ids pinned against DoanHardModeLogic.h by
-- lib/test_scarlet_monastery_doan_hard_mode.py).

-- His hard mode lines (LIB "Text": groups 0-1 are the stock rows; 4-5 are D8's). Group 2 the fourth page read, a yell
-- across the Library (TextRange 2, the zone: the readers are anywhere in the wing); group 3 the Risen Purged (HM5).
DELETE FROM `creature_text` WHERE `CreatureID` = 6487 AND `GroupID` BETWEEN 2 AND 3;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(6487, 2, 0, 'Found my secrets, have you? Let me show you the result!', 14, 0, 100, 0, 0, 0, 0, 2,
    'Arcanist Doan - the fourth evidence page read: the Kel''Thuzad Heresy (D8H)'),
(6487, 3, 0, 'Rise, my purged! The Light never wanted you!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Arcanist Doan - the Risen Purged rise after his second bubble (D8H, HM5)');

-- The four pages' text (LIB "Trigger, the evidence trail"; the designer's lines verbatim after a title line). The
-- page_text ids are the gameobject entries.
DELETE FROM `page_text` WHERE `ID` BETWEEN 301320 AND 301323;
INSERT INTO `page_text` (`ID`, `Text`, `NextPageID`,
    `VerifiedBuild`) VALUES
(301320, CONCAT('Kennel ledger of the Library hounds.\n\n',
    'By the Arcanist''s order, six of the purged sent up to the Athenaeum. Unburned.'), 0, 0),
(301321, CONCAT('A page torn from the catalog of Ambrose Kell, Antiquarian.\n\n',
    'Item 113. Phylactery shard, Stratholme. On loan to Arcanist Doan. Not returned.'), 0, 0),
(301322, CONCAT('A page of the Index of Condemned Works, kept by Lector Hollis Grey.\n\n',
    'Kel''Thuzad and the Forming of the Scourge. Condemned, to be burned. Withheld by order of the Arcanist.'), 0, 0),
(301323, CONCAT('Kel''Thuzad and the Forming of the Scourge. Arcanist Doan''s own copy.\n\n',
    'In the margin, in his careful hand:\n\nHe was not wrong.'), 0, 0);

-- 301320-301323 the evidence pages: goobers (type 10: no lock, no spell, no despawn) that show their page_text
-- (Data7 pageId, Data9 pageMaterial 1, parchment) through the engine's own goober use; go_sm_evidence_page counts the
-- read first (the instance's DATA_DOAN_PAGE_READ) and sends the "(n of 4)" emote. The ledger and Doan's copy are a
-- book (GODI 255 G_Book01), the catalog and index pages a scroll (GODI 210 G_Scroll01); both models carry their
-- own sparkle (V). Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301320, 10, 255, 'Kennel Ledger', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 301320, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, '', 'go_sm_evidence_page', 0),
(301321, 10, 210, 'Torn Catalog Page', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 301321, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, '', 'go_sm_evidence_page', 0),
(301322, 10, 210, 'Page of the Index', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 301322, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, '', 'go_sm_evidence_page', 0),
(301323, 10, 255, 'Annotated Kel''Thuzad', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 301323, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, '', 'go_sm_evidence_page', 0)
ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`), `name` = VALUES(`name`),
    `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `Data7` = VALUES(`Data7`), `Data8` = VALUES(`Data8`),
    `Data9` = VALUES(`Data9`), `AIName` = VALUES(`AIName`), `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` BETWEEN 301320 AND 301323;
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301320, 0, 0, 0, 0, 0, 0, 0, 0),
(301321, 0, 0, 0, 0, 0, 0, 0, 0),
(301322, 0, 0, 0, 0, 0, 0, 0, 0),
(301323, 0, 0, 0, 0, 0, 0, 0, 0);

-- Their spawns, heroic only (spawnMask 2: the hard mode is heroic only; rule 14), at the section 7 #27 A spots
-- (DoanHardModeLogic.h kPages): page 1 the kennel hall's real north corner (156, -241, 19.2), page 2 beside the Large
-- Solid Chest of the corridor to the long hall (GO 75299 guid 11899 at (223.9, -292.7): the page 1.2 yd south of it,
-- so a click never takes the chest), page 3 the reading hall's east nook on its floor (276.2, -428.2, 18.7), page 4 the
-- passage before the Athenaeum beside The Scourge of Lordaeron (219, -424; its Monk and Diviner die first). Guids =
-- the entry x 10 (free in the live DB, read-only check 2026-11-20). Facing 0 (rotation2 = sin(0) = 0, rotation3 = 1).
-- Permanent props: read once per instance (the instance's saved page mask), readable again for the text.
DELETE FROM `gameobject` WHERE `id` BETWEEN 301320 AND 301323 AND `guid` IN (3013200, 3013210, 3013220, 3013230);
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`,
    `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`,
    `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3013200, 301320, 189, 0, 0, 2, 1, 156, -241, 19.2, 0, 0, 0, 0, 1, 300, 255, 1, '', 0,
    'Scarlet Monastery D8H: evidence page 1, the kennel ledger (the Heresy, heroic only)'),
(3013210, 301321, 189, 0, 0, 2, 1, 222.7, -292.7, 19.2, 0, 0, 0, 0, 1, 300, 255, 1, '', 0,
    'Scarlet Monastery D8H: evidence page 2, the catalog page (the Heresy, heroic only)'),
(3013220, 301322, 189, 0, 0, 2, 1, 276.2, -428.2, 18.7, 0, 0, 0, 0, 1, 300, 255, 1, '', 0,
    'Scarlet Monastery D8H: evidence page 3, the index page (the Heresy, heroic only)'),
(3013230, 301323, 189, 0, 0, 2, 1, 219, -424, 19.9, 0, 0, 0, 0, 1, 300, 255, 1, '', 0,
    'Scarlet Monastery D8H: evidence page 4, Doan''s own copy (the Heresy, heroic only)');
