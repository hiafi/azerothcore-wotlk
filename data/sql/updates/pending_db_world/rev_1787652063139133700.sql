-- Frost talent tree content gap, found via live playtest: 12 of the tree's 31 rows (Frostbite,
-- Ice Floes, Frost Warding, Precision, Permafrost, Piercing Ice, Shatter, Cold Snap, Winter's
-- Chill, Shattered Barrier, Summon Water Elemental, Enduring Winter) were content-complete per
-- docs/frost-mage-talent-tree-content-handoff.md's table but never actually got a `talent_dbc`
-- DELETE+INSERT committed to any pending SQL migration - only 19 of 31 rows ever landed here
-- (rev_1787601592241065984.sql and rev_1787603921304223061.sql cover the other 19). Without an
-- SQL overlay row, DBCDatabaseLoader falls back to whatever position these reused stock talent
-- IDs held in the base client Talent.dbc, so the server and the regenerated client patch
-- (var/dbc-patch/) disagreed about where these 12 talents live in the tree.
--
-- Values below are lifted directly from var/dbc-patch/DBFilesClient/Talent.dbc (parsed as raw
-- WDBC), not re-derived by hand - that file already has the correct, complete 31-row Frost table
-- (verified: all 31 IDs present, correctly positioned, matching apps/dbc-tools/source/talents/
-- mage.yaml), so it's the authoritative source for what SQL should have shipped alongside it.
DELETE FROM `talent_dbc` WHERE `ID` IN (38, 61, 62, 65, 67, 68, 70, 72, 1649, 1741, 1855, 2214);
INSERT INTO `talent_dbc` (`ID`, `TabID`, `TierID`, `ColumnIndex`, `SpellRank_1`, `SpellRank_2`, `SpellRank_3`, `SpellRank_4`, `SpellRank_5`, `SpellRank_6`, `SpellRank_7`, `SpellRank_8`, `SpellRank_9`, `PrereqTalent_1`, `PrereqTalent_2`, `PrereqTalent_3`, `PrereqRank_1`, `PrereqRank_2`, `PrereqRank_3`, `Flags`, `RequiredSpellID`, `CategoryMask_1`, `CategoryMask_2`) VALUES
(38, 61, 0, 0, 11071, 12496, 12497, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(61, 61, 2, 0, 11151, 12952, 12953, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(62, 61, 0, 2, 31670, 31672, 55094, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(65, 61, 1, 3, 11175, 12569, 12571, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(67, 61, 3, 2, 11170, 12982, 12983, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(68, 61, 5, 2, 11180, 28592, 28593, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(70, 61, 1, 1, 11189, 28332, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(72, 61, 4, 1, 11958, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0),
(1649, 61, 1, 2, 29438, 29439, 29440, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(1741, 61, 8, 1, 31687, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0),
(1855, 61, 8, 2, 44557, 44560, 44561, 0, 0, 0, 0, 0, 0, 1741, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(2214, 61, 6, 0, 44745, 54787, 0, 0, 0, 0, 0, 0, 0, 71, 0, 0, 0, 0, 0, 0, 0, 0, 0);
