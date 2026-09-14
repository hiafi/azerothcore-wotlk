"""
Warlock - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/warlock.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .warlock_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, tab
from .warlock_spells import chaos_bolt_50796, conflagrate_17962, curse_of_exhaustion_18223, demonic_empowerment_47193, fel_domination_18708, haunt_48181, shadowburn_17877, shadowfury_30283, soul_link_19028, summon_felguard_30146, unstable_affliction_30108
from .warlock_trigger_spells import aftermath_18119, aftermath_18120, amplify_curse_18288, backdraft_47258, backdraft_47259, backdraft_47260, bane_17788, bane_17789, bane_17790, bane_17791, bane_17792, cataclysm_17778, cataclysm_17779, cataclysm_17780, contagion_30060, contagion_30061, contagion_30062, contagion_30063, contagion_30064, dark_pact_18220, death_s_embrace_47198, death_s_embrace_47199, death_s_embrace_47200, decimation_63156, decimation_63158, demonic_aegis_30143, demonic_aegis_30144, demonic_aegis_30145, demonic_brutality_18705, demonic_brutality_18706, demonic_brutality_18707, demonic_knowledge_35691, demonic_knowledge_35692, demonic_knowledge_35693, demonic_pact_47236, demonic_pact_47237, demonic_pact_47238, demonic_pact_47239, demonic_pact_47240, demonic_power_18126, demonic_power_18127, demonic_resilience_30319, demonic_resilience_30320, demonic_resilience_30321, demonic_tactics_30242, demonic_tactics_30245, demonic_tactics_30246, demonic_tactics_30247, demonic_tactics_30248, destructive_reach_17917, destructive_reach_17918, devastation_18130, emberstorm_17954, emberstorm_17955, emberstorm_17956, emberstorm_17957, emberstorm_17958, empowered_corruption_32381, empowered_corruption_32382, empowered_corruption_32383, empowered_imp_47220, empowered_imp_47221, empowered_imp_47223, eradication_47195, eradication_47196, eradication_47197, everlasting_affliction_47201, everlasting_affliction_47202, everlasting_affliction_47203, everlasting_affliction_47204, everlasting_affliction_47205, fel_concentration_17783, fel_concentration_17784, fel_concentration_17785, fel_synergy_47230, fel_synergy_47231, fel_vitality_18731, fel_vitality_18743, fel_vitality_18744, fire_and_brimstone_47266, fire_and_brimstone_47267, fire_and_brimstone_47268, fire_and_brimstone_47269, fire_and_brimstone_47270, grim_reach_18218, grim_reach_18219, improved_corruption_17810, improved_corruption_17811, improved_corruption_17812, improved_corruption_17813, improved_corruption_17814, improved_curse_of_agony_18827, improved_curse_of_agony_18829, improved_curse_of_weakness_18179, improved_curse_of_weakness_18180, improved_demonic_tactics_54347, improved_demonic_tactics_54348, improved_demonic_tactics_54349, improved_drain_soul_18213, improved_drain_soul_18372, improved_fear_53754, improved_fear_53759, improved_felhunter_54037, improved_felhunter_54038, improved_health_funnel_18703, improved_health_funnel_18704, improved_healthstone_18692, improved_healthstone_18693, improved_howl_of_terror_30054, improved_howl_of_terror_30057, improved_immolate_17815, improved_immolate_17833, improved_immolate_17834, improved_imp_18694, improved_imp_18695, improved_imp_18696, improved_life_tap_18182, improved_life_tap_18183, improved_searing_pain_17927, improved_searing_pain_17929, improved_searing_pain_17930, improved_shadow_bolt_17793, improved_shadow_bolt_17796, improved_shadow_bolt_17801, improved_shadow_bolt_17802, improved_shadow_bolt_17803, improved_soul_leech_54117, improved_soul_leech_54118, improved_succubus_18754, improved_succubus_18755, improved_succubus_18756, intensity_18135, intensity_18136, malediction_32477, malediction_32483, malediction_32484, mana_feed_30326, master_conjuror_18767, master_conjuror_18768, master_summoner_18709, master_summoner_18710, metamorphosis_59672, molten_core_47245, molten_core_47246, molten_core_47247, nemesis_63117, nemesis_63121, nemesis_63123, nether_protection_30299, nether_protection_30301, nether_protection_30302, nightfall_18094, nightfall_18095, pandemic_58435, pyroclasm_18073, pyroclasm_18096, pyroclasm_63245, ruin_17959, ruin_59738, ruin_59739, ruin_59740, ruin_59741, shadow_and_flame_30288, shadow_and_flame_30289, shadow_and_flame_30290, shadow_and_flame_30291, shadow_and_flame_30292, shadow_embrace_32385, shadow_embrace_32387, shadow_embrace_32392, shadow_embrace_32393, shadow_embrace_32394, shadow_mastery_18271, shadow_mastery_18272, shadow_mastery_18273, shadow_mastery_18274, shadow_mastery_18275, siphon_life_63108, soul_leech_30293, soul_leech_30295, soul_leech_30296, soul_siphon_17804, soul_siphon_17805, suppression_18174, suppression_18175, suppression_18176, unholy_power_18769, unholy_power_18770, unholy_power_18771, unholy_power_18772, unholy_power_18773


destruction_301_tab = tab(
    id=301,
    name='Destruction',
    class_mask=256,
    order_index=2,
    spell_icon_id=547,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 690},
)


affliction_302_tab = tab(
    id=302,
    name='Affliction',
    class_mask=256,
    spell_icon_id=88,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 161},
)


demonology_303_tab = tab(
    id=303,
    name='Demonology',
    class_mask=256,
    order_index=1,
    spell_icon_id=90,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 459},
)


granted_by_talent(
    id=941,
    tab=destruction_301_tab,
    tier=1,
    column=2,
    ranks=[cataclysm_17778, cataclysm_17779, cataclysm_17780],
    player_castable=False,
)


granted_by_talent(
    id=943,
    tab=destruction_301_tab,
    tier=0,
    column=2,
    ranks=[bane_17788, bane_17789, bane_17790, bane_17791, bane_17792],
    player_castable=False,
)


granted_by_talent(
    id=944,
    tab=destruction_301_tab,
    tier=0,
    column=1,
    ranks=[improved_shadow_bolt_17793, improved_shadow_bolt_17796, improved_shadow_bolt_17801, improved_shadow_bolt_17802, improved_shadow_bolt_17803],
    player_castable=False,
)


granted_by_talent(
    id=961,
    tab=destruction_301_tab,
    tier=4,
    column=1,
    ranks=[improved_immolate_17815, improved_immolate_17833, improved_immolate_17834],
    player_castable=False,
)


granted_by_talent(
    id=963,
    tab=destruction_301_tab,
    tier=2,
    column=1,
    ranks=[shadowburn_17877],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=964,
    tab=destruction_301_tab,
    tier=3,
    column=1,
    ranks=[destructive_reach_17917, destructive_reach_17918],
    player_castable=False,
)


granted_by_talent(
    id=965,
    tab=destruction_301_tab,
    tier=3,
    column=3,
    ranks=[improved_searing_pain_17927, improved_searing_pain_17929, improved_searing_pain_17930],
    player_castable=False,
)


granted_by_talent(
    id=966,
    tab=destruction_301_tab,
    tier=5,
    column=2,
    ranks=[emberstorm_17954, emberstorm_17955, emberstorm_17956, emberstorm_17957, emberstorm_17958],
    player_castable=False,
)


granted_by_talent(
    id=967,
    tab=destruction_301_tab,
    tier=2,
    column=2,
    ranks=[ruin_17959, ruin_59738, ruin_59739, ruin_59740, ruin_59741],
    player_castable=False,
)


granted_by_talent(
    id=968,
    tab=destruction_301_tab,
    tier=6,
    column=1,
    ranks=[conflagrate_17962],
    player_castable=False,
    depends_on={'talent_id': 961, 'rank': 2},
    flags=1,
)


granted_by_talent(
    id=981,
    tab=destruction_301_tab,
    tier=4,
    column=2,
    ranks=[devastation_18130],
    player_castable=False,
    depends_on={'talent_id': 967, 'rank': 4},
)


granted_by_talent(
    id=982,
    tab=destruction_301_tab,
    tier=1,
    column=0,
    ranks=[aftermath_18119, aftermath_18120],
    player_castable=False,
)


granted_by_talent(
    id=983,
    tab=destruction_301_tab,
    tier=2,
    column=0,
    ranks=[demonic_power_18126, demonic_power_18127],
    player_castable=False,
)


granted_by_talent(
    id=985,
    tab=destruction_301_tab,
    tier=3,
    column=0,
    ranks=[intensity_18135, intensity_18136],
    player_castable=False,
)


granted_by_talent(
    id=986,
    tab=destruction_301_tab,
    tier=6,
    column=3,
    ranks=[pyroclasm_18096, pyroclasm_18073, pyroclasm_63245],
    player_castable=False,
    depends_on={'talent_id': 0, 'rank': 1},
)


granted_by_talent(
    id=1001,
    tab=affliction_302_tab,
    tier=2,
    column=1,
    ranks=[fel_concentration_17783, fel_concentration_17784, fel_concentration_17785],
    player_castable=False,
)


granted_by_talent(
    id=1002,
    tab=affliction_302_tab,
    tier=3,
    column=1,
    ranks=[nightfall_18094, nightfall_18095],
    player_castable=False,
)


granted_by_talent(
    id=1003,
    tab=affliction_302_tab,
    tier=0,
    column=2,
    ranks=[improved_corruption_17810, improved_corruption_17811, improved_corruption_17812, improved_corruption_17813, improved_corruption_17814],
    player_castable=False,
)


granted_by_talent(
    id=1004,
    tab=affliction_302_tab,
    tier=1,
    column=3,
    ranks=[soul_siphon_17804, soul_siphon_17805],
    player_castable=False,
)


granted_by_talent(
    id=1005,
    tab=affliction_302_tab,
    tier=0,
    column=1,
    ranks=[suppression_18174, suppression_18175, suppression_18176],
    player_castable=False,
)


granted_by_talent(
    id=1006,
    tab=affliction_302_tab,
    tier=1,
    column=0,
    ranks=[improved_curse_of_weakness_18179, improved_curse_of_weakness_18180],
    player_castable=False,
)


granted_by_talent(
    id=1007,
    tab=affliction_302_tab,
    tier=1,
    column=2,
    ranks=[improved_life_tap_18182, improved_life_tap_18183],
    player_castable=False,
)


granted_by_talent(
    id=1021,
    tab=affliction_302_tab,
    tier=3,
    column=0,
    ranks=[grim_reach_18218, grim_reach_18219],
    player_castable=False,
)


granted_by_talent(
    id=1022,
    tab=affliction_302_tab,
    tier=6,
    column=2,
    ranks=[dark_pact_18220],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1041,
    tab=affliction_302_tab,
    tier=4,
    column=1,
    ranks=[siphon_life_63108],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1042,
    tab=affliction_302_tab,
    tier=5,
    column=1,
    ranks=[shadow_mastery_18271, shadow_mastery_18272, shadow_mastery_18273, shadow_mastery_18274, shadow_mastery_18275],
    player_castable=False,
    depends_on={'talent_id': 1041, 'rank': 0},
)


granted_by_talent(
    id=1061,
    tab=affliction_302_tab,
    tier=2,
    column=2,
    ranks=[amplify_curse_18288],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1081,
    tab=affliction_302_tab,
    tier=4,
    column=2,
    ranks=[curse_of_exhaustion_18223],
    player_castable=False,
    depends_on={'talent_id': 1061, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=1101,
    tab=affliction_302_tab,
    tier=1,
    column=1,
    ranks=[improved_drain_soul_18213, improved_drain_soul_18372],
    player_castable=False,
)


granted_by_talent(
    id=1221,
    tab=demonology_303_tab,
    tier=0,
    column=0,
    ranks=[improved_healthstone_18692, improved_healthstone_18693],
    player_castable=False,
)


granted_by_talent(
    id=1222,
    tab=demonology_303_tab,
    tier=0,
    column=1,
    ranks=[improved_imp_18694, improved_imp_18695, improved_imp_18696],
    player_castable=False,
)


granted_by_talent(
    id=1223,
    tab=demonology_303_tab,
    tier=0,
    column=2,
    ranks=[18697, 18698, 18699],
    player_castable=False,
)


granted_by_talent(
    id=1224,
    tab=demonology_303_tab,
    tier=1,
    column=0,
    ranks=[improved_health_funnel_18703, improved_health_funnel_18704],
    player_castable=False,
)


granted_by_talent(
    id=1225,
    tab=demonology_303_tab,
    tier=1,
    column=1,
    ranks=[demonic_brutality_18705, demonic_brutality_18706, demonic_brutality_18707],
    player_castable=False,
)


granted_by_talent(
    id=1226,
    tab=demonology_303_tab,
    tier=2,
    column=2,
    ranks=[fel_domination_18708],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1227,
    tab=demonology_303_tab,
    tier=3,
    column=2,
    ranks=[master_summoner_18709, master_summoner_18710],
    player_castable=False,
    depends_on={'talent_id': 1226, 'rank': 0},
)


granted_by_talent(
    id=1242,
    tab=demonology_303_tab,
    tier=1,
    column=2,
    ranks=[fel_vitality_18731, fel_vitality_18743, fel_vitality_18744],
    player_castable=False,
)


granted_by_talent(
    id=1243,
    tab=demonology_303_tab,
    tier=2,
    column=0,
    ranks=[improved_succubus_18754, improved_succubus_18755, improved_succubus_18756],
    player_castable=False,
)


granted_by_talent(
    id=1244,
    tab=demonology_303_tab,
    tier=5,
    column=1,
    ranks=[23785, 23822, 23823, 23824, 23825],
    player_castable=False,
    depends_on={'talent_id': 1262, 'rank': 4},
)


granted_by_talent(
    id=1261,
    tab=demonology_303_tab,
    tier=4,
    column=2,
    ranks=[master_conjuror_18767, master_conjuror_18768],
    player_castable=False,
)


granted_by_talent(
    id=1262,
    tab=demonology_303_tab,
    tier=3,
    column=1,
    ranks=[unholy_power_18769, unholy_power_18770, unholy_power_18771, unholy_power_18772, unholy_power_18773],
    player_castable=False,
    depends_on={'talent_id': 1282, 'rank': 0},
)


granted_by_talent(
    id=1263,
    tab=demonology_303_tab,
    tier=6,
    column=2,
    ranks=[demonic_knowledge_35691, demonic_knowledge_35692, demonic_knowledge_35693],
    player_castable=False,
)


granted_by_talent(
    id=1281,
    tab=demonology_303_tab,
    tier=4,
    column=0,
    ranks=[mana_feed_30326],
    player_castable=False,
    depends_on={'talent_id': 1262, 'rank': 4},
    flags=1,
)


granted_by_talent(
    id=1282,
    tab=demonology_303_tab,
    tier=2,
    column=1,
    ranks=[soul_link_19028],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1283,
    tab=demonology_303_tab,
    tier=5,
    column=2,
    ranks=[molten_core_47245, molten_core_47246, molten_core_47247],
    player_castable=False,
)


granted_by_talent(
    id=1284,
    tab=affliction_302_tab,
    tier=0,
    column=0,
    ranks=[improved_curse_of_agony_18827, improved_curse_of_agony_18829],
    player_castable=False,
)


granted_by_talent(
    id=1667,
    tab=affliction_302_tab,
    tier=7,
    column=2,
    ranks=[malediction_32477, malediction_32483, malediction_32484],
    player_castable=False,
)


granted_by_talent(
    id=1668,
    tab=affliction_302_tab,
    tier=7,
    column=0,
    ranks=[improved_howl_of_terror_30054, improved_howl_of_terror_30057],
    player_castable=False,
)


granted_by_talent(
    id=1669,
    tab=affliction_302_tab,
    tier=6,
    column=1,
    ranks=[contagion_30060, contagion_30061, contagion_30062, contagion_30063, contagion_30064],
    player_castable=False,
)


granted_by_talent(
    id=1670,
    tab=affliction_302_tab,
    tier=8,
    column=1,
    ranks=[unstable_affliction_30108],
    player_castable=False,
    depends_on={'talent_id': 1669, 'rank': 4},
    flags=1,
)


granted_by_talent(
    id=1671,
    tab=demonology_303_tab,
    tier=2,
    column=3,
    ranks=[demonic_aegis_30143, demonic_aegis_30144, demonic_aegis_30145],
    player_castable=False,
)


granted_by_talent(
    id=1672,
    tab=demonology_303_tab,
    tier=8,
    column=1,
    ranks=[summon_felguard_30146],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1673,
    tab=demonology_303_tab,
    tier=7,
    column=1,
    ranks=[demonic_tactics_30242, demonic_tactics_30245, demonic_tactics_30246, demonic_tactics_30247, demonic_tactics_30248],
    player_castable=False,
)


granted_by_talent(
    id=1676,
    tab=destruction_301_tab,
    tier=8,
    column=1,
    ranks=[shadowfury_30283],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1677,
    tab=destruction_301_tab,
    tier=7,
    column=1,
    ranks=[shadow_and_flame_30288, shadow_and_flame_30289, shadow_and_flame_30290, shadow_and_flame_30291, shadow_and_flame_30292],
    player_castable=False,
)


granted_by_talent(
    id=1678,
    tab=destruction_301_tab,
    tier=6,
    column=2,
    ranks=[soul_leech_30293, soul_leech_30295, soul_leech_30296],
    player_castable=False,
)


granted_by_talent(
    id=1679,
    tab=destruction_301_tab,
    tier=5,
    column=0,
    ranks=[nether_protection_30299, nether_protection_30301, nether_protection_30302],
    player_castable=False,
)


granted_by_talent(
    id=1680,
    tab=demonology_303_tab,
    tier=6,
    column=0,
    ranks=[demonic_resilience_30319, demonic_resilience_30320, demonic_resilience_30321],
    player_castable=False,
)


granted_by_talent(
    id=1763,
    tab=affliction_302_tab,
    tier=4,
    column=0,
    ranks=[shadow_embrace_32385, shadow_embrace_32387, shadow_embrace_32392, shadow_embrace_32393, shadow_embrace_32394],
    player_castable=False,
)


granted_by_talent(
    id=1764,
    tab=affliction_302_tab,
    tier=3,
    column=3,
    ranks=[empowered_corruption_32381, empowered_corruption_32382, empowered_corruption_32383],
    player_castable=False,
)


granted_by_talent(
    id=1817,
    tab=destruction_301_tab,
    tier=4,
    column=0,
    ranks=[34935, 34938, 34939],
    player_castable=False,
    depends_on={'talent_id': 985, 'rank': 1},
)


granted_by_talent(
    id=1873,
    tab=affliction_302_tab,
    tier=5,
    column=0,
    ranks=[improved_felhunter_54037, improved_felhunter_54038],
    player_castable=False,
)


granted_by_talent(
    id=1875,
    tab=affliction_302_tab,
    tier=8,
    column=0,
    ranks=[death_s_embrace_47198, death_s_embrace_47199, death_s_embrace_47200],
    player_castable=False,
)


granted_by_talent(
    id=1876,
    tab=affliction_302_tab,
    tier=9,
    column=1,
    ranks=[everlasting_affliction_47201, everlasting_affliction_47202, everlasting_affliction_47203, everlasting_affliction_47204, everlasting_affliction_47205],
    player_castable=False,
)


granted_by_talent(
    id=1878,
    tab=affliction_302_tab,
    tier=6,
    column=0,
    ranks=[eradication_47195, eradication_47196, eradication_47197],
    player_castable=False,
)


granted_by_talent(
    id=1880,
    tab=demonology_303_tab,
    tier=6,
    column=1,
    ranks=[demonic_empowerment_47193],
    player_castable=False,
    depends_on={'talent_id': 1244, 'rank': 4},
    flags=1,
)


granted_by_talent(
    id=1882,
    tab=demonology_303_tab,
    tier=8,
    column=0,
    ranks=[improved_demonic_tactics_54347, improved_demonic_tactics_54348, improved_demonic_tactics_54349],
    player_castable=False,
    depends_on={'talent_id': 1673, 'rank': 4},
)


granted_by_talent(
    id=1883,
    tab=demonology_303_tab,
    tier=0,
    column=3,
    ranks=[fel_synergy_47230, fel_synergy_47231],
    player_castable=False,
)


granted_by_talent(
    id=1884,
    tab=demonology_303_tab,
    tier=8,
    column=2,
    ranks=[nemesis_63117, nemesis_63121, nemesis_63123],
    player_castable=False,
)


granted_by_talent(
    id=1885,
    tab=demonology_303_tab,
    tier=9,
    column=1,
    ranks=[demonic_pact_47236, demonic_pact_47237, demonic_pact_47238, demonic_pact_47239, demonic_pact_47240],
    player_castable=False,
)


granted_by_talent(
    id=1886,
    tab=demonology_303_tab,
    tier=10,
    column=1,
    ranks=[metamorphosis_59672],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1887,
    tab=destruction_301_tab,
    tier=1,
    column=1,
    ranks=[63349, 63350, 63351],
    player_castable=False,
)


granted_by_talent(
    id=1888,
    tab=destruction_301_tab,
    tier=8,
    column=0,
    ranks=[backdraft_47258, backdraft_47259, backdraft_47260],
    player_castable=False,
    depends_on={'talent_id': 968, 'rank': 0},
)


granted_by_talent(
    id=1889,
    tab=destruction_301_tab,
    tier=7,
    column=2,
    ranks=[improved_soul_leech_54117, improved_soul_leech_54118],
    player_castable=False,
    depends_on={'talent_id': 1678, 'rank': 2},
)


granted_by_talent(
    id=1890,
    tab=destruction_301_tab,
    tier=9,
    column=1,
    ranks=[fire_and_brimstone_47266, fire_and_brimstone_47267, fire_and_brimstone_47268, fire_and_brimstone_47269, fire_and_brimstone_47270],
    player_castable=False,
)


granted_by_talent(
    id=1891,
    tab=destruction_301_tab,
    tier=10,
    column=1,
    ranks=[chaos_bolt_50796],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2041,
    tab=affliction_302_tab,
    tier=10,
    column=1,
    ranks=[haunt_48181],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2045,
    tab=destruction_301_tab,
    tier=8,
    column=2,
    ranks=[empowered_imp_47220, empowered_imp_47221, empowered_imp_47223],
    player_castable=False,
)


granted_by_talent(
    id=2205,
    tab=affliction_302_tab,
    tier=2,
    column=0,
    ranks=[improved_fear_53754, improved_fear_53759],
    player_castable=False,
)


granted_by_talent(
    id=2245,
    tab=affliction_302_tab,
    tier=8,
    column=2,
    ranks=[pandemic_58435],
    player_castable=False,
    depends_on={'talent_id': 1670, 'rank': 0},
)


granted_by_talent(
    id=2261,
    tab=demonology_303_tab,
    tier=7,
    column=2,
    ranks=[decimation_63156, decimation_63158],
    player_castable=False,
)
