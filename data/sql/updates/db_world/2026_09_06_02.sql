-- Bugfix: Frostbolt (and Fireball/Glacial Spike) casting instantly.
--
-- Root cause: 2026_09_04_08.sql (a generate.py run made to fix the Priest heal-line collapse,
-- see its own header comment and docs/dbc-build-pipeline.md) touched `spellcasttimes_dbc` only
-- to mint ID 30017 (Greater Heal's new cast time), but its DELETE was scoped to the whole shared
-- custom range (`ID` BETWEEN 30000 AND 30099) while its INSERT only re-added the one row that
-- run actually needed -- silently dropping the Frost Mage rework's own 30000-30016 block that
-- 2026_09_04_07.sql (and the "Final fixes for frost mage" commit before it) had populated.
-- spell_dbc's CastingTimeIndex columns for Frostbolt (116 -> 30003), Fireball (133 -> 30001) and
-- Glacial Spike (200002 -> 30001) were left pointing at those now-missing rows, so
-- SpellInfo::CalcCastTime's `if (!CastTimeEntry) return 0` fires and all three cast instantly.
--
-- Restores the exact 30000-30016 values from 2026_09_04_07.sql; leaves 30017 (Greater Heal, still
-- correct) alone.
DELETE FROM `spellcasttimes_dbc` WHERE `ID` BETWEEN 30000 AND 30016;
INSERT INTO `spellcasttimes_dbc` (`ID`, `Base`, `PerLevel`, `Minimum`) VALUES
(30000, -1000000, 0, 0),
(30001, 2500, 0, 0),
(30002, 3000, 0, 0),
(30003, 2000, 0, 0),
(30004, 1500, 0, 0),
(30005, 1000, 0, 0),
(30006, 3500, 0, 0),
(30007, 10000, 0, 0),
(30008, 5000, 0, 0),
(30009, 100, 0, 0),
(30010, 4000, 0, 0),
(30011, 2700, 0, 0),
(30012, 500, 0, 0),
(30013, 2200, 0, 0),
(30014, 7000, 0, 0),
(30015, 1700, 0, 0),
(30016, 6000, 0, 0);
