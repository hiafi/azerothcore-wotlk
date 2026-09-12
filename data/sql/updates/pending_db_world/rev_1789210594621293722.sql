-- Hand-written migration (not apps/dbc-tools/generate.py output).
-- Fixes: 10 Arcane Mage rework talent slots that were authored correctly in
-- apps/dbc-tools/source/talents/mage.yaml and visible in the client's talent UI, but were
-- never inserted into the live talent_dbc table - see docs/.master-todo-list.md's 2026-09-12
-- entry for the root cause (var/extractors/dbc/Talent.dbc was hand-edited to already contain
-- this rework's row/column layout, so generate.py's stock-vs-live diff treats these 10 rows as
-- already there and never emits SQL for them). Row content built via the same
-- build.build_talent_row() the generator itself uses, from the same source/talents/mage.yaml
-- entries, so this is byte-for-byte what a correct generate.py run would emit for just these
-- 10 ids - not hand-transcribed. Affected talents: Arcane Meditation (76), Arcane Shielding
-- (83), Improved Counterspell (88), Arcane Resonance (1142), Arcane Empowerment (1727), Arcane
-- Flows (1843), Incanter's Absorption (1844), Student of the Mind (1845), Netherwind Presence
-- (1846), Focus Magic (2211).

DELETE FROM `talent_dbc` WHERE `ID` IN (76, 83, 88, 1142, 1727, 1843, 1844, 1845, 1846, 2211);
INSERT INTO `talent_dbc` (`ID`, `TabID`, `TierID`, `ColumnIndex`, `SpellRank_1`, `SpellRank_2`, `SpellRank_3`, `SpellRank_4`, `SpellRank_5`, `SpellRank_6`, `SpellRank_7`, `SpellRank_8`, `SpellRank_9`, `PrereqTalent_1`, `PrereqTalent_2`, `PrereqTalent_3`, `PrereqRank_1`, `PrereqRank_2`, `PrereqRank_3`, `Flags`, `RequiredSpellID`, `CategoryMask_1`, `CategoryMask_2`) VALUES
(76, 81, 0, 1, 11222, 12839, 12840, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(83, 81, 3, 0, 11252, 12605, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(88, 81, 3, 1, 11255, 12598, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(1142, 81, 3, 2, 18462, 18463, 18464, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(1727, 81, 6, 0, 31579, 31582, 31583, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(1843, 81, 7, 1, 44378, 44379, 0, 0, 0, 0, 0, 0, 0, 87, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(1844, 81, 6, 2, 44394, 44395, 44396, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(1845, 81, 2, 2, 44397, 44398, 44399, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(1846, 81, 9, 1, 44400, 44402, 44403, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
(2211, 81, 2, 3, 54646, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0);
