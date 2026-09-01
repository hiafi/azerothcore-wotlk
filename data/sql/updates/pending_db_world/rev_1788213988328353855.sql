-- Frozen Orb Pulse (200008, spell_mage.cpp) damage/threat/combat-log attribution fix, found via
-- live playtest (2026-08-31): the pulse was cast by the orb creature on itself
-- (TARGET_UNIT_SRC_AREA_ENEMY resolves relative to the caster), so every hit was attributed to an
-- unnamed creature instead of the owning player - Fingers of Frost procced and the pulse showed
-- in the combat log, but never in the player's own damage meter. Fixed on the C++ side
-- (spell_mage.cpp: npc_mage_frozen_orb now has the owning player cast 200008 directly, once per
-- second, at an explicit dest = the orb's live position) which requires both of 200008's effects
-- to use a DEST-based area target instead of SRC, since SRC always resolves relative to whoever
-- is actually casting. TARGET_UNIT_DEST_AREA_ENEMY (16) keeps the AoE centered on the orb's
-- moving position while letting the player be the real caster (also fixes spell-power scaling,
-- which was previously reading off the orb's own nonexistent spell power instead of the player's).
UPDATE `spell_dbc` SET `ImplicitTargetA_1` = 16 WHERE `ID` = 200008 AND `ImplicitTargetA_1` = 15;
UPDATE `spell_dbc` SET `ImplicitTargetA_2` = 16 WHERE `ID` = 200008 AND `ImplicitTargetA_2` = 15;
