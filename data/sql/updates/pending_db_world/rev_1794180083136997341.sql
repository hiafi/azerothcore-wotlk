-- Scholomance build WP-S12: Ras Frostwhisper's hard mode, "the Torn Keepsake" (heroic only): the keepsake gameobjects,
-- their spawns and Ras's hard mode start emote (.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row
-- S12 and s10, the user's spots; modules/mod-dungeon-bosses src/Scholomance/ras_hard_mode.cpp). The Ice Tomb 300535 and
-- the spells 206190-206197 are apps/dbc-tools source/npcs/scholomance/ras_hard_mode.py.

-- The keepsake gameobjects (ids.yaml reservation `scholomance` 301150-301199; ScholomanceRework.h
-- ScholomanceGameObjects). All goobers (type 10, the stock quest scroll shape) whose script owns the click, so the stock
-- goober use never runs. Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
-- 301150 Torn Page (go_sc_torn_page): a flat paper scrap with no glow (GODI 7752, UldamanScrollDebris03, WP-V's pick
--        for gap 4: the hunt is the puzzle). A click collects the page its spawn spot names (DATA_KEEPSAKE_PAGE).
-- 301151 Frostwhisper's Keepsake (go_sc_keepsake_book): the empty book, the Keepsake of Remembrance look (GODI 4431,
--        BookMedium07 as stock GO 176630) at size 2.5 so it reads on the floor. A click tells the page count; with all
--        three it binds the keepsake (DATA_KEEPSAKE_BOUND).
-- 301152 Bound Keepsake (go_sc_keepsake_book): the bound book, the glowing closed black book (GODI 6893, G_Book01_Black
--        as stock GO 183983). Spawned beside 301151 on the same spot: the script shows one at a time.
-- 301154 Frostwhisper's Apparatus (go_sc_alchemy_table): the alchemy set on the lab hall's alchemy table (GODI 345,
--        G_AlchemySet01, a goober model), user ruling 2026-11-08: a click here lights the hard mode
--        (DATA_RAS_HARD_MODE), not the Embalming Fluid. Selectable only with the bound keepsake, while Ras neither
--        fights nor is dead.
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`, `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`, `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`, `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301150, 10, 7752, 'Torn Page', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', 'go_sc_torn_page', 0),
(301151, 10, 4431, 'Frostwhisper''s Keepsake', '', '', '', 2.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', 'go_sc_keepsake_book', 0),
(301152, 10, 6893, 'Bound Keepsake', '', '', '', 2.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', 'go_sc_keepsake_book', 0),
(301154, 10, 345, 'Frostwhisper''s Apparatus', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', 'go_sc_alchemy_table', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`), `name` = VALUES(`name`), `size` = VALUES(`size`), `AIName` = VALUES(`AIName`), `ScriptName` = VALUES(`ScriptName`);

-- The spawns, heroic only (spawnMask 2: the keepsake does nothing on normal), at the user's measured spots (handoff s10,
-- ScholomanceRework.h kKeepsakePages, kKeepsakeBook, kHardModeTable; exact). Guids 3011500-3011540 (the entry x 10
-- convention of the Deadmines and SFK kit spawns; free in the live DB, read-only check 2026-11-08). Rotation = the
-- orientation about z (rotation2 = sin(o/2), rotation3 = cos(o/2)). The book's two gameobjects share one spot.
DELETE FROM `gameobject` WHERE `id` = 301150 AND `guid` IN (3011500, 3011501, 3011502);
DELETE FROM `gameobject` WHERE `id` = 301151 AND `guid` = 3011510;
DELETE FROM `gameobject` WHERE `id` = 301152 AND `guid` = 3011520;
DELETE FROM `gameobject` WHERE `id` = 301154 AND `guid` = 3011540;
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`, `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`, `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3011500, 301150, 289, 0, 0, 2, 1, 233.51549, 4.6665864, 116.66063, 2.3726962, 0, 0, 0.927006, 0.375048, 7200, 255, 1, '', 0, 'Scholomance S12: Torn Page 1 (Ras hard mode, heroic only)'),
(3011501, 301150, 289, 0, 0, 2, 1, 211.28065, 174.21268, 109.67556, 5.677647, 0, 0, 0.298165, -0.954514, 7200, 255, 1, '', 0, 'Scholomance S12: Torn Page 2 (Ras hard mode, heroic only)'),
(3011502, 301150, 289, 0, 0, 2, 1, 152.4498, 109.95338, 105.6674, 4.173605, 0, 0, 0.869797, -0.49341, 7200, 255, 1, '', 0, 'Scholomance S12: Torn Page 3 (Ras hard mode, heroic only)'),
(3011510, 301151, 289, 0, 0, 2, 1, 42.15418, 121.35609, 83.54561, 4.7194448, 0, 0, 0.704608, -0.709597, 7200, 255, 1, '', 0, 'Scholomance S12: Frostwhisper''s Keepsake, empty (Ras hard mode, heroic only)'),
(3011520, 301152, 289, 0, 0, 2, 1, 42.15418, 121.35609, 83.54561, 4.7194448, 0, 0, 0.704608, -0.709597, 7200, 255, 1, '', 0, 'Scholomance S12: Bound Keepsake (Ras hard mode, heroic only)'),
(3011540, 301154, 289, 0, 0, 2, 1, 41.380466, 161.82669, 86.786736, 0.59217954, 0, 0, 0.291782, 0.956485, 7200, 255, 1, '', 0, 'Scholomance S12: Frostwhisper''s Apparatus (lights Ras hard mode, heroic only)');

-- Ras's hard mode start (go_sc_alchemy_table, ScholoRasHardMode::EMOTE_RAS_KEEPSAKE_LIT): a boss emote (41) heard on
-- the whole map (TextRange 3), since the table is about 80 yd from his study. Groups 0-2 are WP-S4's rev.
DELETE FROM `creature_text` WHERE `CreatureID` = 10508 AND `GroupID` = 3;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10508, 3, 0, '%s remembers the mortal he was.', 41, 0, 100, 0, 0, 0, 0, 3, 'Ras Frostwhisper - the Torn Keepsake lit (hard mode)');
