/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

// This is where scripts' loading functions should be declared:
void AddSC_deathknight_spell_scripts();
void AddSC_druid_spell_scripts();
void AddSC_druid_balance_spell_scripts(); // Custom: druid-rework Balance pass
void AddSC_druid_resto_spell_scripts(); // Custom: druid-rework Resto pass
void AddSC_druid_feral_spell_scripts(); // Custom: druid-rework Feral pass
void AddSC_druid_hooks(); // Custom: druid-rework shared ScriptMgr handlers
void AddSC_generic_spell_scripts();
void AddSC_hunter_spell_scripts();
void AddSC_mage_spell_scripts();
void AddSC_paladin_spell_scripts();
void AddSC_priest_spell_scripts();
void AddSC_priest_new_spell_scripts();
void AddSC_priest_disc_spell_scripts();
void AddSC_priest_holy_spell_scripts();
void AddSC_priest_shadow_spell_scripts();
void AddSC_rogue_spell_scripts();
void AddSC_shaman_spell_scripts();
void AddSC_warlock_spell_scripts();
void AddSC_warlock_affliction_spell_scripts(); // Custom: warlock-rework Affliction pass
void AddSC_warlock_destruction_spell_scripts(); // Custom: warlock-rework Destruction pass
void AddSC_warlock_demonology_spell_scripts(); // Custom: warlock-rework Demonology pass
void AddSC_warlock_hooks(); // Custom: warlock-rework shared ScriptMgr handlers
void AddSC_paladin_seal_spell_scripts(); // Custom: paladin-rework (Retribution)
void AddSC_paladin_retribution_spell_scripts(); // Custom: paladin-rework (Retribution)
void AddSC_paladin_holy_spell_scripts(); // Custom: paladin-rework (Holy)
void AddSC_paladin_protection_spell_scripts(); // Custom: paladin-rework (Protection)
void AddSC_paladin_hooks(); // Custom: paladin-rework (Retribution)
void AddSC_hunter_shared_spell_scripts(); // Custom: hunter-rework
void AddSC_hunter_pet_spell_scripts(); // Custom: hunter-rework
void AddSC_hunter_beast_mastery_spell_scripts(); // Custom: hunter-rework
void AddSC_hunter_marksmanship_spell_scripts(); // Custom: hunter-rework
void AddSC_hunter_survival_spell_scripts(); // Custom: hunter-rework
void AddSC_hunter_hooks(); // Custom: hunter-rework
void AddSC_shaman_shared_spell_scripts(); // Custom: shaman-rework
void AddSC_shaman_hooks(); // Custom: shaman-rework
void AddSC_shaman_totem_spell_scripts(); // Custom: shaman-rework
void AddSC_shaman_elemental_spell_scripts(); // Custom: shaman-rework
void AddSC_shaman_restoration_spell_scripts(); // Custom: shaman-rework
void AddSC_shaman_enhancement_spell_scripts(); // Custom: shaman-rework
void AddSC_deathknight_shared_spell_scripts(); // Custom: death-knight-rework
void AddSC_deathknight_blood_spell_scripts(); // Custom: death-knight-rework
void AddSC_deathknight_frost_spell_scripts(); // Custom: death-knight-rework
void AddSC_deathknight_unholy_spell_scripts(); // Custom: death-knight-rework
void AddSC_deathknight_hooks(); // Custom: death-knight-rework
void AddSC_rogue_shared_spell_scripts(); // Custom: rogue-rework
void AddSC_rogue_hooks(); // Custom: rogue-rework
void AddSC_rogue_assassination_spell_scripts(); // Custom: rogue-rework
void AddSC_rogue_subtlety_spell_scripts(); // Custom: rogue-rework
void AddSC_rogue_combat_spell_scripts(); // Custom: rogue-rework
void AddSC_warrior_spell_scripts();
void AddSC_quest_spell_scripts();
void AddSC_item_spell_scripts();

// The name of this function should match:
// void Add${NameOfDirectory}Scripts()
void AddSpellsScripts()
{
    AddSC_deathknight_spell_scripts();
    AddSC_druid_spell_scripts();
    AddSC_druid_balance_spell_scripts(); // Custom: druid-rework Balance pass
    AddSC_druid_resto_spell_scripts(); // Custom: druid-rework Resto pass
    AddSC_druid_feral_spell_scripts(); // Custom: druid-rework Feral pass
    AddSC_druid_hooks(); // Custom: druid-rework shared ScriptMgr handlers
    AddSC_generic_spell_scripts();
    AddSC_hunter_spell_scripts();
    AddSC_mage_spell_scripts();
    AddSC_paladin_spell_scripts();
    AddSC_priest_spell_scripts();
    AddSC_priest_new_spell_scripts();
    AddSC_priest_disc_spell_scripts();
    AddSC_priest_holy_spell_scripts();
    AddSC_priest_shadow_spell_scripts();
    AddSC_rogue_spell_scripts();
    AddSC_shaman_spell_scripts();
    AddSC_warlock_spell_scripts();
    AddSC_warlock_affliction_spell_scripts(); // Custom: warlock-rework Affliction pass
    AddSC_warlock_destruction_spell_scripts(); // Custom: warlock-rework Destruction pass
    AddSC_warlock_demonology_spell_scripts(); // Custom: warlock-rework Demonology pass
    AddSC_warlock_hooks(); // Custom: warlock-rework shared ScriptMgr handlers
    AddSC_paladin_seal_spell_scripts(); // Custom: paladin-rework (Retribution)
    AddSC_paladin_retribution_spell_scripts(); // Custom: paladin-rework (Retribution)
    AddSC_paladin_holy_spell_scripts(); // Custom: paladin-rework (Holy)
    AddSC_paladin_protection_spell_scripts(); // Custom: paladin-rework (Protection)
    AddSC_paladin_hooks(); // Custom: paladin-rework (Retribution)
    AddSC_hunter_shared_spell_scripts(); // Custom: hunter-rework
    AddSC_hunter_pet_spell_scripts(); // Custom: hunter-rework
    AddSC_hunter_beast_mastery_spell_scripts(); // Custom: hunter-rework
    AddSC_hunter_marksmanship_spell_scripts(); // Custom: hunter-rework
    AddSC_hunter_survival_spell_scripts(); // Custom: hunter-rework
    AddSC_hunter_hooks(); // Custom: hunter-rework
    AddSC_shaman_shared_spell_scripts(); // Custom: shaman-rework
    AddSC_shaman_hooks(); // Custom: shaman-rework
    AddSC_shaman_totem_spell_scripts(); // Custom: shaman-rework
    AddSC_shaman_elemental_spell_scripts(); // Custom: shaman-rework
    AddSC_shaman_restoration_spell_scripts(); // Custom: shaman-rework
    AddSC_shaman_enhancement_spell_scripts(); // Custom: shaman-rework
    AddSC_deathknight_shared_spell_scripts(); // Custom: death-knight-rework
    AddSC_deathknight_blood_spell_scripts(); // Custom: death-knight-rework
    AddSC_deathknight_frost_spell_scripts(); // Custom: death-knight-rework
    AddSC_deathknight_unholy_spell_scripts(); // Custom: death-knight-rework
    AddSC_deathknight_hooks(); // Custom: death-knight-rework
    AddSC_rogue_shared_spell_scripts(); // Custom: rogue-rework
    AddSC_rogue_hooks(); // Custom: rogue-rework
    AddSC_rogue_assassination_spell_scripts(); // Custom: rogue-rework
    AddSC_rogue_subtlety_spell_scripts(); // Custom: rogue-rework
    AddSC_rogue_combat_spell_scripts(); // Custom: rogue-rework
    AddSC_warrior_spell_scripts();
    AddSC_quest_spell_scripts();
    AddSC_item_spell_scripts();
}
