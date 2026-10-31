-- DB update 2026_10_31_54 -> 2026_10_31_55
-- Warrior rework (user, 2026-10-30): Shockwave (talent 1872) moves back to its stock cell (tier 10, column 1).
-- dbc-tools skips a declared talent that equals stock, so it neither re-emits nor deletes the talent_dbc override
-- the S1 rev wrote at (10, 0). Remove that stale override; the server then reads the stock Talent.dbc row.
DELETE FROM `talent_dbc` WHERE `ID` = 1872;
