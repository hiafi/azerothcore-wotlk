-- Blackrock Spire build WP-S0: the skeleton's rows dbc-tools cannot declare
-- (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.2 item 3, s4.1 row S0). The wave 1 bosses'
-- templates (ScriptName, AIName '', normal health, DamageModifier, immunity 1972, INSTANCE_BIND) are apps/dbc-tools
-- source/npcs/blackrock_spire/<boss>.py.

-- The three wave 1 bosses that ran on SmartAI are bound to C++ scripts with AIName '' by the skeleton, so their
-- smart_scripts rows go now (a row on a creature that is not using SmartAI is skipped with an error at boot):
-- Shadow Hunter Vosh'gajin 9236 (Curse of Blood 16098, Hex 16097), Mother Smolderweb 10596 (Mother's Milk 16468,
-- Crystallize 16104, the death cast of Summon Spire Spiderling 16103) and Gizrul the Slavener 10268 (Fatal Bite 16495,
-- Infected Bite 16128, Frenzy 8269). Their boss WPs (B2, B4, B7) rebuild each fight in C++ (handoff s3.5).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 9236 AND `source_type` = 0;
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10596 AND `source_type` = 0;
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10268 AND `source_type` = 0;
