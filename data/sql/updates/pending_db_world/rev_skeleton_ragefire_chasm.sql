-- Ragefire Chasm build WP-S0, the skeleton (.agents/plans/ragefire-chasm-build/ragefire-chasm-build.HANDOFF.md s3.2
-- item 5). The stock SmartAI of the four bosses bound to C++ by apps/dbc-tools source/npcs/ragefire_chasm/
-- (Oggleflint's Cleave, Jergosh's Curse of Weakness and Immolate, Bazzalan's Deadly Poison and Sinister Strike,
-- Taragaman's Uppercut and Fire Nova), so no boss WP deletes them again. AIName '' comes with the dbc-tools rows
-- (boss_columns, next to the ScriptName). None of the four has an action list, a SmartAI condition or a creature_text
-- row (SELECT 2026-11-24). The trash keeps its SmartAI (the Earthborer 11320 included), and so do the Blood Filled
-- Orb 182024 and Zelemar.
DELETE FROM `smart_scripts` WHERE `entryorguid` IN (11517, 11518, 11519, 11520) AND `source_type` = 0;
