-- Water Elemental: Freeze (33395) - FoF-on-immune-target half of Phase 1 item 4
-- (docs/frost-mage-redesign.md sec 2, "Water Elemental: Freeze"): "Against targets immune to
-- freeze effects, grants the owner 1 Fingers of Frost charge instead of applying the freeze."
-- Wires up spell_mage_water_elemental_freeze (src/server/scripts/Spells/spell_mage.cpp). The
-- other half of item 4, autocast removal, needed no change - 33395's pulled AttributesEx already
-- carries SPELL_ATTR1_NO_AUTOCAST_AI (see rev_1787563173168071680.sql's spell_dbc row for this
-- ID, AttributesEx = 131208 = 0x20088), so CharmInfo::InitCharmCreateSpells never lets the pet
-- autocast this spell in the first place.
DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN ((33395, 'spell_mage_water_elemental_freeze'));
INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES
(33395, 'spell_mage_water_elemental_freeze');
