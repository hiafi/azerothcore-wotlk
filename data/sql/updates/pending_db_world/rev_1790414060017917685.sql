-- Earth Shock back to stock (2026-09-26). mod-progression's phase_00 overrode every rank to also
-- interrupt spellcasting, as a stand-in until Wind Shear at its phase 13. Player spells no longer
-- change with the progression phase, so that edit is removed from the module and its override rows
-- are dropped here, letting the stock Spell.dbc rows apply.
DELETE FROM `spell_dbc` WHERE `ID` IN (8042, 8044, 8045, 8046, 10412, 10413, 10414, 25454, 49230, 49231);
