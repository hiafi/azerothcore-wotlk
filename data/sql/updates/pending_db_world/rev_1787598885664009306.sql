-- Frost Mage rework (docs/frost-mage-talent-tree-handoff.md Part 1, gap A2: "No longer deals
-- damage to stun-immune targets").
--
-- Cleanup, not a fix: traced spell_mage_deep_freeze_immunity_state (spell_script_names row added
-- in data/sql/updates/db_world/2026_06_14_01.sql, supporting spell_proc/spell_proc_event rows
-- added in data/sql/updates/db_world/2026_02_18_01.sql) and confirmed spell ID 71761 has NO
-- `spell_dbc` row anywhere in this repo - base or overlay. It's a from-scratch ID with no real
-- spell behind it (several unrelated pieces of base content elsewhere in the world DB happen to
-- reuse the same numeric ID for a completely unrelated, much later expansion's NPC; not the same
-- "spell"). A script/proc/proc_event set can be
-- registered against a spell ID that was never actually defined; the aura can then never exist on
-- a unit, so none of it can ever fire. Confirmed no C++ file references
-- spell_mage_deep_freeze_immunity_state any more (removed alongside this migration).
--
-- Net effect for the redesign's requirement: Deep Freeze already deals no damage to stun-immune
-- targets today, just because this fallback mechanism was dead on arrival, not by design. This
-- migration only removes the orphaned rows; it changes no live behavior.

DELETE FROM `spell_script_names` WHERE `spell_id` = 71761 AND `ScriptName` = 'spell_mage_deep_freeze_immunity_state';
DELETE FROM `spell_proc` WHERE `SpellId` = 71761;
DELETE FROM `spell_proc_event` WHERE `entry` = 71761;
