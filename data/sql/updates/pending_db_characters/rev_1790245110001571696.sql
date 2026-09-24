-- Custom: druid-rework Resto pass (.agents/plans/druid-rework/druid-rework.RESTO.md §3 item 9,
-- PLAN §5.0 item 5 "one hand-written line per pass" / §6 item 9 "repeated per pass", B10/A10).
-- The Resto tree moves/cuts/adds talents, so existing druids need another reset on top of the
-- Balance pass's; Nourish (50464) is removed this pass, so unlearn it from any existing character.
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 11;
DELETE FROM `character_spell` WHERE `spell` = 50464;
