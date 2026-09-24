-- Custom: druid-rework Balance pass (.agents/plans/druid-rework/druid-rework.PLAN.md §5.1 WP-0,
-- B10/A10). The only hand-written SQL in this pass - every world-DB row goes through dbc-tools
-- (WP-T, PLAN B11). Talent reset for every druid so the new Balance tree loads clean; Lesser Heal
-- (2050) and Heal (2054) cleanup for any priest who learned/bound them before A10 removed both.
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 11;
DELETE FROM `character_spell` WHERE `spell` IN (2050, 2054);
DELETE FROM `character_action` WHERE `type` = 0 AND `action` IN (2050, 2054);
