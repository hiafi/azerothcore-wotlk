/*
 * mod-dungeon-bosses: script loader. Every boss file's AddSC_ is declared and called here; a boss WP fills its own
 * file and never needs to edit this one. The module needs mod-boss-mechanics (mod-dungeon-bosses.cmake checks it).
 */

// The shared dungeon kit (KT-1): spell_dungeon_refflat_damage / spell_dungeon_refflat_periodic
void AddSC_dungeon_kit_spells();

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

// Shadowfang Keep (map 33): the SFK layer (WP-K): the instance (registered under the stock name
// instance_shadowfang_keep, replacing the stock one) and the `.sfktest` shell
void AddSC_instance_shadowfang_keep_rework();
void AddSC_dungeon_bosses_sfktest_commandscript();

// Shadowfang Keep bosses (one file per boss WP)
void AddSC_boss_rethilgore_rework();            // S1: boss_rethilgore_rework
void AddSC_boss_razorclaw_rework();             // S2: boss_razorclaw_rework
void AddSC_boss_baron_silverlaine_rework();     // S3: boss_baron_silverlaine_rework
void AddSC_boss_commander_springvale_rework();  // S4: boss_commander_springvale_rework
void AddSC_boss_odo_the_blindwatcher_rework();  // S5: boss_odo_the_blindwatcher_rework, go_sfk_alarm_bell
void AddSC_boss_deathsworn_captain_rework();    // S6: boss_deathsworn_captain_rework
void AddSC_boss_fenrus_the_devourer_rework();   // S7: boss_fenrus_the_devourer_rework
void AddSC_boss_wolf_master_nandos_rework();    // S8: boss_wolf_master_nandos_rework
void AddSC_boss_archmage_arugal_rework();       // S9: boss_archmage_arugal_rework, npc_sfk_lair_prisoner
void AddSC_sfk_face_him_alone();                // S10: Arugal's hard mode (`.sfktest hardmode`)

// Scholomance (map 289): the Scholomance kit (WP-KS): the instance (registered under the stock name
// instance_scholomance, replacing the stock one; the stock Kirtonos, Kormok and Occultist AIs keep working) and the
// `.dbtest scholo` shell
void AddSC_instance_scholomance_rework();
void AddSC_dungeon_bosses_scholo_commandscript();

// Scholomance bosses (one file per boss WP)
void AddSC_boss_jandice_barov_rework();             // S1: boss_jandice_barov_rework
void AddSC_boss_rattlegore_rework();                // S2: boss_rattlegore_rework
void AddSC_boss_marduk_vectus_rework();             // S3: boss_marduk_blackpool_rework, boss_vectus_rework
void AddSC_boss_ras_frostwhisper_rework();          // S4: boss_ras_frostwhisper_rework
void AddSC_boss_instructor_malicia_rework();        // S5: boss_instructor_malicia_rework
void AddSC_boss_doctor_theolen_krastinov_rework();  // S6: boss_doctor_theolen_krastinov_rework
void AddSC_boss_lorekeeper_polkelt_rework();        // S7: boss_lorekeeper_polkelt_rework
void AddSC_boss_the_ravenian_rework();              // S8: boss_the_ravenian_rework
void AddSC_boss_lord_alexei_barov_rework();         // S9: boss_lord_alexei_barov_rework
void AddSC_boss_lady_illucia_barov_rework();        // S10: boss_lady_illucia_barov_rework
void AddSC_boss_darkmaster_gandling_rework();       // S11: boss_darkmaster_gandling_rework
void AddSC_scholo_ras_hard_mode();                  // S12: Ras's hard mode (`.dbtest scholo keepsake`)
void AddSC_scholo_graduate_exam();                  // S13: Gandling's hard mode (`.dbtest scholo exam`)

// Stratholme (map 329): the Stratholme skeleton (WP-S0): the instance (registered under the stock name
// instance_stratholme, replacing the stock one; the stock Jarien, Sothos and scarlet thread scripts keep working) and
// the `.dbtest strat` shell
void AddSC_instance_stratholme_rework();
void AddSC_dungeon_bosses_strat_commandscript();

// Stratholme bosses (one file per boss WP). Wave 1, the Service Entrance:
void AddSC_boss_magistrate_barthilas_rework();      // S9: boss_magistrate_barthilas_rework
void AddSC_boss_baroness_anastari_rework();         // S10: boss_baroness_anastari_rework
void AddSC_boss_nerubenkan_rework();                // S11: boss_nerubenkan_rework
void AddSC_boss_maleki_the_pallid_rework();         // S12: boss_maleki_the_pallid_rework
void AddSC_boss_ramstein_the_gorger_rework();       // S13: boss_ramstein_the_gorger_rework
void AddSC_boss_baron_rivendare_rework();           // S14: boss_baron_rivendare_rework
void AddSC_strat_baron_hard_mode();                 // S15: the Baron's hard mode (`.dbtest strat ultimatum`)
// Wave 2, the Main Gate (registered, bound to nothing until wave 2 flips kWave2Bound / BIND_WAVE_2):
void AddSC_boss_the_unforgiven_rework();            // S1: boss_the_unforgiven_rework
void AddSC_boss_hearthsinger_forresten_rework();    // S2: boss_hearthsinger_forresten_rework
void AddSC_boss_timmy_the_cruel_rework();           // S3: boss_timmy_the_cruel_rework
void AddSC_boss_malor_the_zealous_rework();         // S4: boss_malor_the_zealous_rework
void AddSC_boss_cannon_master_willey_rework();      // S5: boss_cannon_master_willey_rework
void AddSC_boss_archivist_galford_rework();         // S6: boss_archivist_galford_rework
void AddSC_boss_dathrohan_balnazzar_rework();       // S7: boss_dathrohan_balnazzar_rework (10812 and 10813)
void AddSC_strat_balnazzar_hard_mode();             // S8: Balnazzar's hard mode (`.dbtest strat grandlie`)

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
    AddSC_dungeon_kit_spells();
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
    AddSC_instance_shadowfang_keep_rework();
    AddSC_boss_rethilgore_rework();
    AddSC_boss_razorclaw_rework();
    AddSC_boss_baron_silverlaine_rework();
    AddSC_boss_commander_springvale_rework();
    AddSC_boss_odo_the_blindwatcher_rework();
    AddSC_boss_deathsworn_captain_rework();
    AddSC_boss_fenrus_the_devourer_rework();
    AddSC_boss_wolf_master_nandos_rework();
    AddSC_boss_archmage_arugal_rework();
    AddSC_sfk_face_him_alone();
    AddSC_instance_scholomance_rework();
    AddSC_boss_jandice_barov_rework();
    AddSC_boss_rattlegore_rework();
    AddSC_boss_marduk_vectus_rework();
    AddSC_boss_ras_frostwhisper_rework();
    AddSC_boss_instructor_malicia_rework();
    AddSC_boss_doctor_theolen_krastinov_rework();
    AddSC_boss_lorekeeper_polkelt_rework();
    AddSC_boss_the_ravenian_rework();
    AddSC_boss_lord_alexei_barov_rework();
    AddSC_boss_lady_illucia_barov_rework();
    AddSC_boss_darkmaster_gandling_rework();
    AddSC_scholo_ras_hard_mode();
    AddSC_scholo_graduate_exam();
    AddSC_scholo_items();
    AddSC_instance_stratholme_rework();
    AddSC_boss_magistrate_barthilas_rework();
    AddSC_boss_baroness_anastari_rework();
    AddSC_boss_nerubenkan_rework();
    AddSC_boss_maleki_the_pallid_rework();
    AddSC_boss_ramstein_the_gorger_rework();
    AddSC_boss_baron_rivendare_rework();
    AddSC_strat_baron_hard_mode();
    AddSC_boss_the_unforgiven_rework();
    AddSC_boss_hearthsinger_forresten_rework();
    AddSC_boss_timmy_the_cruel_rework();
    AddSC_boss_malor_the_zealous_rework();
    AddSC_boss_cannon_master_willey_rework();
    AddSC_boss_archivist_galford_rework();
    AddSC_boss_dathrohan_balnazzar_rework();
    AddSC_strat_balnazzar_hard_mode();
    AddSC_strat_hard_mode_items();
    AddSC_sfk_hard_mode_items();
    AddSC_haunted_set_bonuses();
    // after the boss files: they register their `.dmtest` / `.sfktest` / `.dbtest scholo` / `.dbtest strat` tables
    // from their AddSC_ functions
    AddSC_dungeon_bosses_dmtest_commandscript();
    AddSC_dungeon_bosses_sfktest_commandscript();
    AddSC_dungeon_bosses_scholo_commandscript();
    AddSC_dungeon_bosses_strat_commandscript();
}
