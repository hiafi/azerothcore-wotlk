--
-- Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): spell_script_names bindings
-- for this pass's new/extended classes in spell_warrior.cpp. spell_script_names supports multiple
-- rows per spell_id (unique key is (spell_id, ScriptName)); none of these spells carry any other
-- script already.
--
-- Also fixes a real gap found while auditing every spell_warr_* class against this table:
-- spell_warr_defensive_stance (added in this rework's Phase 1, spell 71 - Defensive Stance) was
-- written and registered in C++ but never actually bound here, so it has never fired (the same
-- "class exists, binding forgotten" failure mode already hit and fixed for the Frost Mage rework -
-- see data/sql/updates/db_world/2026_09_01_01.sql's spell_mage_biting_cold/spell_mage_frostbite
-- entries). Bound here alongside this phase's own new bindings.
--
DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN ((71, 'spell_warr_defensive_stance'), (50687, 'spell_warr_incite'), (6343, 'spell_warr_thunder_clap'), (20243, 'spell_warr_devastate'), (46968, 'spell_warr_shockwave'), (23920, 'spell_warr_shield_cover_capstone'), (2565, 'spell_warr_shield_cover_capstone'), (6572, 'spell_warr_revenge'), (25288, 'spell_warr_revenge'), (23922, 'spell_warr_shield_slam'));
INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES
(71, 'spell_warr_defensive_stance'),
(50687, 'spell_warr_incite'),
(6343, 'spell_warr_thunder_clap'),
(20243, 'spell_warr_devastate'),
(46968, 'spell_warr_shockwave'),
(23920, 'spell_warr_shield_cover_capstone'),
(2565, 'spell_warr_shield_cover_capstone'),
(6572, 'spell_warr_revenge'),
(25288, 'spell_warr_revenge'),
(23922, 'spell_warr_shield_slam');
