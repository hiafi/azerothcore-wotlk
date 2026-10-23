-- DB update 2026_10_23_34 -> 2026_10_23_35
-- Shaman P0 spike teardown: drop the spike's two throwaway totem creatures (no spawns, no spells, no scripts left).
DELETE FROM `creature_template_spell` WHERE `CreatureID` IN (300298, 300299);
DELETE FROM `creature_template_model` WHERE `CreatureID` IN (300298, 300299);
DELETE FROM `creature_template` WHERE `entry` IN (300298, 300299);
