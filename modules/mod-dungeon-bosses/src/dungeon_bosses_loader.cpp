/*
 * mod-dungeon-bosses: script loader. Every boss file's AddSC_ is declared and called here; a boss WP fills its own
 * file and never needs to edit this one. The module needs mod-boss-mechanics (mod-dungeon-bosses.cmake checks it).
 */

// Deadmines (map 36): the shared kit
void AddSC_instance_deadmines_rework();
void AddSC_dungeon_bosses_dmtest_commandscript();

// Deadmines bosses (one file per boss WP)
void AddSC_boss_rhahk_zor_rework();         // B1: boss_rhahk_zor_rework, npc_dm_watchman, npc_dm_evoker
void AddSC_boss_miner_johnson_rework();     // B2: boss_miner_johnson_rework, npc_dm_working_miner
void AddSC_boss_sneed_rework();             // B3: boss_sneeds_shredder_rework, boss_sneed_rework
void AddSC_boss_gilnid_rework();            // B4: boss_gilnid_rework, npc_dm_iron_shot, npc_dm_land_mine
void AddSC_boss_mr_smite_rework();          // B5: boss_mr_smite_rework
void AddSC_boss_cookie_rework();            // B6: boss_cookie_rework
void AddSC_boss_captain_greenskin_rework(); // B7: boss_captain_greenskin_rework, go_dm_harpoon_rope
void AddSC_boss_edwin_vancleef_rework();    // B8: boss_edwin_vancleef_rework, npc_dm_blackguard, npc_dm_shadow_image
void AddSC_vancleef_hard_mode();            // B9: go_dm_powder_keg

// Deadmines hard mode items (item variants IV6): the VanCleef hard mode item effects
void AddSC_dm_hard_mode_items();            // spell_dm_powder_keg_fuse, spell_dm_blackguards_signet,
                                            // spell_dm_lantern_of_the_roaring_flame

// Stratholme hard mode items (wave 1 dungeon items): the Balnazzar and Baron Rivendare hard mode item effects
void AddSC_strat_hard_mode_items();         // spell_strat_dust_of_the_nathrezim, spell_strat_two_faced_tome,
                                            // spell_strat_ysidas_locket, spell_strat_blade_of_the_condemned,
                                            // spell_strat_deathchargers_spur, StratholmeCondemnedDamage

// Shadowfang Keep hard mode items (wave 1 dungeon items): the Archmage Arugal hard mode item effects
void AddSC_sfk_hard_mode_items();           // spell_sfk_arugals_shadow_tome, spell_sfk_arugals_voidwalker

// Scholomance items (wave 1 dungeon items): the scripted Scholomance item effects
void AddSC_scholo_items();                  // spell_scholo_phylactery_shard, spell_scholo_bonechill_blade,
                                            // spell_scholo_transfer_papers, spell_scholo_darkmasters_portal_rod

// Dungeon sets (item variants, Haunted set track): the Haunted set bonuses
void AddSC_haunted_set_bonuses();           // spell_haunted_* bonus scripts, HauntedSetSpellHooks, HauntedSetUnitHooks

void Addmod_dungeon_bossesScripts()
{
    AddSC_instance_deadmines_rework();
    AddSC_boss_rhahk_zor_rework();
    AddSC_boss_miner_johnson_rework();
    AddSC_boss_sneed_rework();
    AddSC_boss_gilnid_rework();
    AddSC_boss_mr_smite_rework();
    AddSC_boss_cookie_rework();
    AddSC_boss_captain_greenskin_rework();
    AddSC_boss_edwin_vancleef_rework();
    AddSC_vancleef_hard_mode();
    AddSC_dm_hard_mode_items();
    AddSC_scholo_items();
    AddSC_strat_hard_mode_items();
    AddSC_sfk_hard_mode_items();
    AddSC_haunted_set_bonuses();
    // after the boss files: they register their `.dmtest` tables from their AddSC_ functions
    AddSC_dungeon_bosses_dmtest_commandscript();
}
