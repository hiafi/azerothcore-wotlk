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
    // after the boss files: they register their `.dmtest` tables from their AddSC_ functions
    AddSC_dungeon_bosses_dmtest_commandscript();
}
