-- DB update 2026_09_01_23 -> 2026_09_01_24
-- Tanks crit immune baseline: bind the new AuraScript classes that apply/remove the shared
-- "Critical Strike Immunity" aura (spell 200000, see apps/dbc-tools/source/spells/generic.csv)
-- when Defensive Stance / Righteous Fury / Bear Form / Dire Bear Form are (de)activated.
-- Frost Presence needs no new row here: it's already bound to spell_dk_presence (48263,
-- 'spell_dk_presence'), which was extended in C++ to also apply/remove the same aura.
-- 5487/9634 already carry an unrelated script (spell_dru_feral_swiftness) - spell_script_names
-- supports multiple rows per spell_id (its unique key is (spell_id, ScriptName)), so this adds
-- to, rather than replaces, what's already registered for those two IDs.
DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN ((71, 'spell_warr_defensive_stance'), (25780, 'spell_pal_righteous_fury'), (5487, 'spell_dru_bear_form_crit_immunity'), (9634, 'spell_dru_bear_form_crit_immunity'));
INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES
(71, 'spell_warr_defensive_stance'),
(25780, 'spell_pal_righteous_fury'),
(5487, 'spell_dru_bear_form_crit_immunity'),
(9634, 'spell_dru_bear_form_crit_immunity');
