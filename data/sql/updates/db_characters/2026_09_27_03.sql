-- DB update 2026_09_27_02 -> 2026_09_27_03
-- Custom: druid-rework Feral pass (.agents/plans/druid-rework/druid-rework.FERAL.md §3 item 7, PLAN B10).
-- The only hand-written SQL in this pass - every world-DB row goes through dbc-tools (WP-T, PLAN B11).
-- The Feral tree moves/cuts/adds talents, so existing druids need another talent reset; the old
-- trainer-taught Savage Defense passive (62600) is retired (Savage Defense is now a talent, 6,0).
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 11;
DELETE FROM `character_spell` WHERE `spell` = 62600;
