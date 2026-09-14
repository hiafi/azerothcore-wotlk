-- Hand-written migration (not full apps/dbc-tools/generate.py output).
--
-- Fixes: Frostbolt (116), Fireball (133) and Glacial Spike (200002) casting instantly, because
-- their spell_dbc.CastingTimeIndex pointed at custom spellcasttimes_dbc rows (30001/30003) that
-- had been silently dropped - see docs/.master-todo-list.md's 2026-09-12 entry and
-- apps/dbc-tools/lib/reuse.py's ReuseContext.reserved_rows docstring for the generator bug that
-- caused it (fixed in code this same session: generate.py used to feed sql_out only this run's
-- freshly-minted secondary rows while its own SQL unconditionally wiped the whole reserved range,
-- so any run that didn't happen to re-mint a value another, untouched spell still depended on
-- silently deleted that spell's cast time out from under it - this had already happened and been
-- fixed once before, 2026_09_06_02.sql, and regressed again by 2026-09-12).
--
-- Values cross-checked three ways: the two prior known-good migrations that already recreated
-- this exact block (data/sql/updates/db_world/2026_09_04_07.sql, 2026_09_06_02.sql, both agree:
-- 30001/2000ms for Frostbolt, 30003/2500ms for Fireball+Glacial Spike - IDs differ here only
-- because they're freshly re-minted, not because the values differ), apps/dbc-tools's own
-- source/spells/mage.csv (cast_time_ms: Frostbolt 2000, Fireball/Glacial Spike 2500), and a fresh
-- generate.py run with the reuse.py fix applied (same values, different fresh IDs again, for the
-- same reason).
--
-- Deliberately minimal: a full generate.py regen at this point also reports ~374 other spell_dbc
-- edits unrelated to this bug (verified: their CastingTimeIndex/DurationIndex/RangeIndex/
-- EffectRadiusIndex_* already match live exactly - whatever differs there is separate, unreviewed
-- content work, out of scope for this fix) - not applied here.

DELETE FROM `spellcasttimes_dbc` WHERE `ID` IN (30001, 30002);
INSERT INTO `spellcasttimes_dbc` (`ID`, `Base`, `PerLevel`, `Minimum`) VALUES
(30001, 2000, 0, 0),
(30002, 2500, 0, 0);

UPDATE `spell_dbc` SET `CastingTimeIndex` = 30001 WHERE `ID` = 116;
UPDATE `spell_dbc` SET `CastingTimeIndex` = 30002 WHERE `ID` IN (133, 200002);
