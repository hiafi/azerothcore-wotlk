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

// Blackrock Spire (map 229): the Blackrock Spire skeleton (WP-S0): the instance (registered under the stock name
// instance_blackrock_spire, replacing the stock one; the stock Valthalak, Mor Grayhoof, Vaelastrasz, Father Flame and
// area trigger scripts keep working) and the `.dbtest brs` shell
void AddSC_instance_blackrock_spire_rework();
void AddSC_dungeon_bosses_brs_commandscript();
// Blackrock Spire bosses (one file per boss WP). Wave 1, Lower Blackrock Spire:
void AddSC_boss_highlord_omokk_rework();            // B1: boss_highlord_omokk_rework
void AddSC_boss_shadow_hunter_voshgajin_rework();   // B2: boss_shadow_hunter_voshgajin_rework
void AddSC_boss_warmaster_voone_rework();           // B3: boss_warmaster_voone_rework
void AddSC_boss_mother_smolderweb_rework();         // B4: boss_mother_smolderweb_rework
void AddSC_boss_urok_doomhowl_rework();             // B5: boss_urok_doomhowl_rework
void AddSC_boss_quartermaster_zigris_rework();      // B6: boss_quartermaster_zigris_rework
void AddSC_boss_halycon_gizrul_rework();            // B7: boss_halycon_gizrul_rework (10220 and 10268)
void AddSC_boss_overlord_wyrmthalak_rework();       // B8: boss_overlord_wyrmthalak_rework
void AddSC_brs_wyrmthalak_hard_mode();              // B9: Wyrmthalak's hard mode (`.dbtest brs warhorn`)
// Wave 2, Upper Blackrock Spire (AIs registered only once wave 2 flips kWave2Bound / BIND_WAVE_2):
void AddSC_boss_pyroguard_emberseer_rework();       // B10: boss_pyroguard_emberseer_rework
void AddSC_boss_solakar_flamewreath_rework();       // B11: boss_solakar_flamewreath_rework
void AddSC_boss_rend_blackhand_rework();            // B12: boss_rend_blackhand_rework
void AddSC_boss_gyth_rework();                      // B12: boss_gyth_rework
void AddSC_boss_the_beast_rework();                 // B13: boss_the_beast_rework
void AddSC_boss_drakkisath_rework();                // B14: boss_drakkisath_rework
void AddSC_brs_drakkisath_hard_mode();              // B15: Drakkisath's hard mode (`.dbtest brs army`)
// Blackrock Depths (map 230): the Blackrock Depths skeleton (WP-S0): the instance (registered under the stock name
// instance_blackrock_depths, replacing the stock one; Rocknot, Nagmara, the braziers, at_ring_of_law, Grimstone,
// Phalanx, the Tomb and the stock bosses of the wave not yet bound keep working) and the `.dbtest brd` shell
void AddSC_instance_blackrock_depths_rework();
void AddSC_dungeon_bosses_brd_commandscript();
// Blackrock Depths bosses (one file per boss WP). Wave 1, Detention Block and Shadowforge City:
void AddSC_boss_high_interrogator_gerstahn_rework();    // D1: boss_high_interrogator_gerstahn_rework
void AddSC_boss_lord_roccor_rework();                   // D2: boss_lord_roccor_rework
void AddSC_boss_houndmaster_grebmar_rework();           // D3: boss_houndmaster_grebmar_rework
void AddSC_npc_grimstone_rework();                      // D4: npc_grimstone_rework (registered once D4 binds it)
void AddSC_npc_ring_beast_rework();                     // D4: npc_ring_beast_rework (idem)
void AddSC_boss_ring_champions_rework();                // D5: the six boss_<champion>_rework (once D5 binds them)
void AddSC_brd_ring_encore_hard_mode();                 // D6: the Encore (`.dbtest brd encore`)
void AddSC_boss_pyromancer_loregrain_rework();          // D7: boss_pyromancer_loregrain_rework
void AddSC_boss_warder_stilgiss_rework();               // D8: boss_warder_stilgiss_rework, npc_verek_rework
void AddSC_boss_watchman_doomgrip_rework();             // D9: boss_watchman_doomgrip_rework
void AddSC_npc_fineous_darkvire_rework();               // D10: npc_fineous_darkvire_rework
void AddSC_boss_lord_incendius_rework();                // D11: boss_lord_incendius_rework
void AddSC_brd_incendius_hard_mode();                   // D12: Lord of the Lake (`.dbtest brd lake`)
void AddSC_boss_baelgar_rework();                       // D13: boss_baelgar_rework
// Wave 2, Manufactory and Imperial Seat (AIs registered only once wave 2 flips kWave2Bound / BIND_WAVE_2; D17 is
// data only):
void AddSC_boss_general_angerforge_rework();            // D14: boss_general_angerforge_rework
void AddSC_boss_golem_lord_argelmach_rework();          // D15: boss_golem_lord_argelmach_rework
void AddSC_brd_argelmach_hard_mode();                   // D16: the Prototype (`.dbtest brd prototype`)
void AddSC_boss_hurley_blackbreath_rework();            // D18: Hurley and npc_blackbreath_crony_rework
void AddSC_npc_phalanx_rework();                        // D19: npc_phalanx_rework
void AddSC_boss_ambassador_flamelash_rework();          // D20: Flamelash and npc_burning_spirit_rework
void AddSC_boss_the_seven_rework();                     // D21: boss_the_seven_rework (all seven)
void AddSC_boss_magmus_rework();                        // D22: boss_magmus_rework, npc_ironhand_guardian_rework
void AddSC_boss_emperor_dagran_thaurissan_rework();     // D23: boss_emperor_dagran_thaurissan_rework
void AddSC_boss_moira_bronzebeard_rework();             // D23: boss_moira_bronzebeard_rework (8929 and 10076)
void AddSC_brd_emperor_hard_mode();                     // D24: the Avatar of Ragnaros (`.dbtest brd avatar`)
void AddSC_npc_brd_marshal_windsor();                  // dungeon quests Q4: the Jail Break! escort (9023)
// Scarlet Monastery (map 189): the Scarlet Monastery skeleton (WP-S0): the instance (registered under the stock name
// instance_scarlet_monastery, replacing the stock one; the stock Ashbringer spell scripts and the Horseman keep
// working), go_sm_chapel_door, go_sm_wing_portal, and the `.dbtest sm` shell
void AddSC_instance_scarlet_monastery_rework();
void AddSC_dungeon_bosses_sm_commandscript();
// Scarlet Monastery bosses (one file per boss WP). Wave 1, the Graveyard and the Library:
void AddSC_boss_interrogator_vishas_rework();           // D1: boss_interrogator_vishas_rework
void AddSC_boss_ironspine_rework();                     // D2: boss_ironspine_rework
void AddSC_boss_azshir_fallen_champion_rework();        // D3: boss_fallen_champion_rework, boss_azshir_*_rework
void AddSC_boss_bloodmage_thalnos_rework();             // D4: boss_bloodmage_thalnos_rework
void AddSC_sm_thalnos_hard_mode();                      // D4H: the Desecration (`.dbtest sm desecration`)
void AddSC_boss_houndmaster_loksey_rework();            // D5: boss_houndmaster_loksey_rework
void AddSC_boss_ambrose_kell_rework();                  // D6: boss_ambrose_kell_rework (registered once D6 binds it)
void AddSC_boss_lector_hollis_grey_rework();            // D7: boss_lector_hollis_grey_rework (idem, D7)
void AddSC_boss_arcanist_doan_rework();                 // D8: boss_arcanist_doan_rework
void AddSC_sm_doan_hard_mode();                         // D8H: the Kel'Thuzad Heresy (`.dbtest sm heresy`)
// Wave 2, the Armory and the Cathedral (AIs registered only once wave 2 flips kWave2Bound / BIND_WAVE_2):
void AddSC_boss_forgemaster_gideon_crell_rework();      // D9: boss_forgemaster_gideon_crell_rework
void AddSC_boss_drillmaster_corin_halden_rework();      // D10: boss_drillmaster_corin_halden_rework
void AddSC_boss_herod_rework();                         // D11: boss_herod_rework
void AddSC_sm_herod_hard_mode();                        // D11H: Call to Arms (`.dbtest sm calltoarms`)
void AddSC_boss_gardener_rework();                      // D12: boss_gardener_rework (Brother Aldous Thorne)
void AddSC_boss_mograine_rework();                      // D13: boss_mograine_rework (the Last Stand)
void AddSC_boss_whitemane_rework();                     // D14: boss_whitemane_rework
void AddSC_sm_whitemane_hard_mode();                    // D14H: The Truth (`.dbtest sm truth`)
// Ragefire Chasm (map 389): the Ragefire Chasm skeleton (WP-S0): the bosses (one file per boss WP), the instance
// (registered under the stock name instance_ragefire_chasm, replacing the empty stock one) and the `.dbtest rfc` shell
void AddSC_boss_oggleflint_rework();        // D1: boss_oggleflint_rework, npc_rfc_borer
void AddSC_boss_jergosh_rework();           // D2: boss_jergosh_rework, npc_rfc_soul_wisp
void AddSC_boss_bazzalan_rework();          // D3: boss_bazzalan_rework
void AddSC_boss_taragaman_rework();         // D4: boss_taragaman_rework
void AddSC_rfc_taragaman_hard_mode();       // D4H: Starving: go_rfc_blood_shrine, go_rfc_pour_spot,
                                            // npc_rfc_blood_globule (`.dbtest rfc starving`)
void AddSC_instance_ragefire_chasm_rework();
void AddSC_dungeon_bosses_rfc_commandscript();
// Stratholme hard mode items (wave 1 dungeon items): the Balnazzar and Baron Rivendare hard mode item effects
void AddSC_strat_hard_mode_items();         // spell_strat_dust_of_the_nathrezim, spell_strat_two_faced_tome,
                                            // spell_strat_ysidas_locket, spell_strat_blade_of_the_condemned,
                                            // spell_strat_deathchargers_spur, StratholmeCondemnedDamage

// Shadowfang Keep hard mode items (wave 1 dungeon items): the Archmage Arugal hard mode item effects
void AddSC_sfk_hard_mode_items();           // spell_sfk_arugals_shadow_tome, spell_sfk_arugals_voidwalker

// Scholomance items (wave 1 dungeon items): the scripted Scholomance item effects
void AddSC_scholo_items();                  // spell_scholo_phylactery_shard, spell_scholo_bonechill_blade,
                                            // spell_scholo_transfer_papers, spell_scholo_darkmasters_portal_rod

// Blackrock Spire hard mode items (wave 2 dungeon items): the Wyrmthalak and Drakkisath hard mode item effects
void AddSC_brs_hard_mode_items();           // spell_brs_ward_of_the_three_tribes, spell_brs_champions_mark

// Blackrock Depths hard mode items (wave 2 dungeon items): the Encore, Incendius, Argelmach and Emperor items
void AddSC_brd_hard_mode_items();           // BrdExecutionerDamage, spell_brd_korvs_spirit_fetish,
                                            // spell_brd_scepter_of_the_molten_lake, spell_brd_lava_spawn,
                                            // spell_brd_prototype_power_core, spell_brd_golemwrights_mending_rod,
                                            // spell_brd_mending_servo, spell_brd_electrons_lethal_coil,
                                            // spell_brd_volcanic_heartstone, spell_brd_orb_of_the_sorcerer_thane

// Scarlet Monastery hard mode items (scarlet gear): the Thalnos, Doan, Herod and Whitemane items
void AddSC_sm_hard_mode_items();            // spell_sm_pureblood_rallying_standard, spell_sm_one_roll_per_cast,
                                            // spell_sm_fathers_verdict, spell_sm_inquisitors_rosary

// Ragefire Chasm hard mode items (ragefire gear): the Taragaman, Starving items
void AddSC_rfc_hard_mode_items();           // spell_rfc_taragamans_fang, spell_rfc_hungering_bite,
                                            // spell_rfc_heart_of_the_starving, spell_rfc_one_roll_per_cast

// Dungeon sets (item variants, Haunted set track): the Haunted set bonuses
void AddSC_haunted_set_bonuses();           // spell_haunted_* bonus scripts, HauntedSetSpellHooks, HauntedSetUnitHooks

// Dungeon sets (blackrock gear): the Molten set bonuses
void AddSC_molten_set_bonuses();            // spell_molten_* bonus scripts (Heat, eruptions, cooldown hooks)

// Dungeon sets (scarlet gear): the Zealot's set bonuses
void AddSC_zealot_set_bonuses();            // spell_zealot_* bonus scripts, ZealotSetUnitHooks

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
    AddSC_instance_blackrock_spire_rework();
    AddSC_boss_highlord_omokk_rework();
    AddSC_boss_shadow_hunter_voshgajin_rework();
    AddSC_boss_warmaster_voone_rework();
    AddSC_boss_mother_smolderweb_rework();
    AddSC_boss_urok_doomhowl_rework();
    AddSC_boss_quartermaster_zigris_rework();
    AddSC_boss_halycon_gizrul_rework();
    AddSC_boss_overlord_wyrmthalak_rework();
    AddSC_brs_wyrmthalak_hard_mode();
    AddSC_boss_pyroguard_emberseer_rework();
    AddSC_boss_solakar_flamewreath_rework();
    AddSC_boss_rend_blackhand_rework();
    AddSC_boss_gyth_rework();
    AddSC_boss_the_beast_rework();
    AddSC_boss_drakkisath_rework();
    AddSC_brs_drakkisath_hard_mode();
    AddSC_instance_blackrock_depths_rework();
    AddSC_boss_high_interrogator_gerstahn_rework();
    AddSC_boss_lord_roccor_rework();
    AddSC_boss_houndmaster_grebmar_rework();
    AddSC_npc_grimstone_rework();
    AddSC_npc_ring_beast_rework();
    AddSC_boss_ring_champions_rework();
    AddSC_brd_ring_encore_hard_mode();
    AddSC_boss_pyromancer_loregrain_rework();
    AddSC_boss_warder_stilgiss_rework();
    AddSC_boss_watchman_doomgrip_rework();
    AddSC_npc_fineous_darkvire_rework();
    AddSC_boss_lord_incendius_rework();
    AddSC_brd_incendius_hard_mode();
    AddSC_boss_baelgar_rework();
    AddSC_boss_general_angerforge_rework();
    AddSC_boss_golem_lord_argelmach_rework();
    AddSC_brd_argelmach_hard_mode();
    AddSC_boss_hurley_blackbreath_rework();
    AddSC_npc_phalanx_rework();
    AddSC_boss_ambassador_flamelash_rework();
    AddSC_boss_the_seven_rework();
    AddSC_boss_magmus_rework();
    AddSC_boss_emperor_dagran_thaurissan_rework();
    AddSC_boss_moira_bronzebeard_rework();
    AddSC_brd_emperor_hard_mode();
    AddSC_npc_brd_marshal_windsor();
    AddSC_instance_scarlet_monastery_rework();
    AddSC_boss_interrogator_vishas_rework();
    AddSC_boss_ironspine_rework();
    AddSC_boss_azshir_fallen_champion_rework();
    AddSC_boss_bloodmage_thalnos_rework();
    AddSC_sm_thalnos_hard_mode();
    AddSC_boss_houndmaster_loksey_rework();
    AddSC_boss_ambrose_kell_rework();
    AddSC_boss_lector_hollis_grey_rework();
    AddSC_boss_arcanist_doan_rework();
    AddSC_sm_doan_hard_mode();
    AddSC_boss_forgemaster_gideon_crell_rework();
    AddSC_boss_drillmaster_corin_halden_rework();
    AddSC_boss_herod_rework();
    AddSC_sm_herod_hard_mode();
    AddSC_boss_gardener_rework();
    AddSC_boss_mograine_rework();
    AddSC_boss_whitemane_rework();
    AddSC_sm_whitemane_hard_mode();
    AddSC_boss_oggleflint_rework();
    AddSC_boss_jergosh_rework();
    AddSC_boss_bazzalan_rework();
    AddSC_boss_taragaman_rework();
    AddSC_rfc_taragaman_hard_mode();
    AddSC_instance_ragefire_chasm_rework();
    AddSC_strat_hard_mode_items();
    AddSC_sfk_hard_mode_items();
    AddSC_brs_hard_mode_items();
    AddSC_brd_hard_mode_items();
    AddSC_sm_hard_mode_items();
    AddSC_rfc_hard_mode_items();
    AddSC_haunted_set_bonuses();
    AddSC_molten_set_bonuses();
    AddSC_zealot_set_bonuses();
    // after the boss files: they register their `.dmtest` / `.sfktest` / `.dbtest scholo` / `.dbtest strat` /
    // `.dbtest brs` / `.dbtest brd` / `.dbtest sm` / `.dbtest rfc` tables from their AddSC_ functions
    AddSC_dungeon_bosses_dmtest_commandscript();
    AddSC_dungeon_bosses_sfktest_commandscript();
    AddSC_dungeon_bosses_scholo_commandscript();
    AddSC_dungeon_bosses_strat_commandscript();
    AddSC_dungeon_bosses_brs_commandscript();
    AddSC_dungeon_bosses_brd_commandscript();
    AddSC_dungeon_bosses_sm_commandscript();
    AddSC_dungeon_bosses_rfc_commandscript();
}
