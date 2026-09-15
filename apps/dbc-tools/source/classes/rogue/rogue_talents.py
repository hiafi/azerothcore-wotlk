"""
Rogue - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/rogue.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .rogue_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, tab
from .rogue_spells import adrenaline_rush_13750, blade_flurry_13877, cold_blood_14177, ghostly_strike_14278, hemorrhage_16511, hunger_for_blood_51662, killing_spree_51690, mutilate_1329, premeditation_14183, preparation_14185, riposte_14251, shadow_dance_51713, shadowstep_36554
from .rogue_trigger_spells import aggression_18427, aggression_18428, aggression_18429, aggression_61330, aggression_61331, blade_twisting_31124, blade_twisting_31126, blood_spatter_51632, blood_spatter_51633, camouflage_13975, camouflage_14062, camouflage_14063, cheat_death_31228, cheat_death_31229, cheat_death_31230, combat_potency_35541, combat_potency_35550, combat_potency_35551, combat_potency_35552, combat_potency_35553, cut_to_the_chase_51664, cut_to_the_chase_51665, cut_to_the_chase_51667, cut_to_the_chase_51668, cut_to_the_chase_51669, deadened_nerves_31380, deadened_nerves_31382, deadened_nerves_31383, deadly_brew_51625, deadly_brew_51626, dirty_deeds_14082, dirty_deeds_14083, dirty_tricks_14076, dirty_tricks_14094, dual_wield_specialization_13715, dual_wield_specialization_13848, dual_wield_specialization_13849, dual_wield_specialization_13851, dual_wield_specialization_13852, elusiveness_13981, elusiveness_14066, endurance_13742, endurance_13872, filthy_tricks_58414, filthy_tricks_58415, find_weakness_31234, find_weakness_31235, find_weakness_31236, improved_ambush_14079, improved_ambush_14080, improved_eviscerate_14162, improved_eviscerate_14163, improved_eviscerate_14164, improved_expose_armor_14168, improved_expose_armor_14169, improved_gouge_13741, improved_gouge_13792, improved_gouge_13793, improved_kick_13754, improved_kick_13867, improved_kidney_shot_14174, improved_kidney_shot_14175, improved_kidney_shot_14176, improved_poisons_14113, improved_poisons_14114, improved_poisons_14115, improved_poisons_14116, improved_poisons_14117, improved_sinister_strike_13732, improved_sinister_strike_13863, improved_slice_and_dice_14165, improved_slice_and_dice_14166, improved_sprint_13743, improved_sprint_13875, initiative_13976, initiative_13979, initiative_13980, lethality_14128, lethality_14132, lethality_14135, lethality_14136, lethality_14137, master_of_subtlety_31223, master_poisoner_31226, master_poisoner_31227, master_poisoner_58410, murder_14158, murder_14159, opportunity_14057, opportunity_14072, puncturing_wounds_13733, puncturing_wounds_13865, puncturing_wounds_13866, quick_recovery_31244, quick_recovery_31245, relentless_strikes_14179, relentless_strikes_58422, relentless_strikes_58423, relentless_strikes_58424, relentless_strikes_58425, ruthlessness_14156, ruthlessness_14160, ruthlessness_14161, savage_combat_51682, savage_combat_58413, seal_fate_14186, seal_fate_14190, seal_fate_14193, seal_fate_14194, seal_fate_14195, serrated_blades_14171, serrated_blades_14172, serrated_blades_14173, sinister_calling_31216, sinister_calling_31217, sinister_calling_31218, sinister_calling_31219, sinister_calling_31220, slaughter_from_the_shadows_51708, slaughter_from_the_shadows_51709, slaughter_from_the_shadows_51710, slaughter_from_the_shadows_51711, slaughter_from_the_shadows_51712, sleight_of_hand_30892, sleight_of_hand_30893, surprise_attacks_32601, throwing_specialization_51679, throwing_specialization_5952, vigor_14983, vile_poisons_16513, vile_poisons_16514, vile_poisons_16515, waylay_51692, waylay_51696


combat_181_tab = tab(
    id=181,
    name='Combat',
    class_mask=8,
    order_index=1,
    spell_icon_id=243,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 365},
)


assassination_182_tab = tab(
    id=182,
    name='Assassination',
    class_mask=8,
    spell_icon_id=514,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 50},
)


subtlety_183_tab = tab(
    id=183,
    name='Subtlety',
    class_mask=8,
    order_index=2,
    spell_icon_id=250,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 597},
)


granted_by_talent(
    id=181,
    tab=combat_181_tab,
    tier=1,
    column=3,
    ranks=[13705, 13832, 13843, 13844, 13845],
    player_castable=False,
)


granted_by_talent(
    id=182,
    tab=combat_181_tab,
    tier=2,
    column=2,
    ranks=[13706, 13804, 13805, 13806, 13807],
    player_castable=False,
    depends_on={'talent_id': 221, 'rank': 4},
)


granted_by_talent(
    id=184,
    tab=combat_181_tab,
    tier=4,
    column=0,
    ranks=[13709, 13800, 13801, 13802, 13803],
    player_castable=False,
)


granted_by_talent(
    id=186,
    tab=combat_181_tab,
    tier=3,
    column=2,
    ranks=[13712, 13788, 13789],
    player_castable=False,
)


granted_by_talent(
    id=187,
    tab=combat_181_tab,
    tier=1,
    column=1,
    ranks=[13713, 13853, 13854],
    player_castable=False,
)


granted_by_talent(
    id=201,
    tab=combat_181_tab,
    tier=0,
    column=1,
    ranks=[improved_sinister_strike_13732, improved_sinister_strike_13863],
    player_castable=False,
)


granted_by_talent(
    id=203,
    tab=combat_181_tab,
    tier=0,
    column=0,
    ranks=[improved_gouge_13741, improved_gouge_13793, improved_gouge_13792],
    player_castable=False,
)


granted_by_talent(
    id=204,
    tab=combat_181_tab,
    tier=2,
    column=0,
    ranks=[endurance_13742, endurance_13872],
    player_castable=False,
)


granted_by_talent(
    id=205,
    tab=combat_181_tab,
    tier=6,
    column=1,
    ranks=[adrenaline_rush_13750],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=206,
    tab=combat_181_tab,
    tier=3,
    column=0,
    ranks=[improved_kick_13754, improved_kick_13867],
    player_castable=False,
)


granted_by_talent(
    id=221,
    tab=combat_181_tab,
    tier=0,
    column=2,
    ranks=[dual_wield_specialization_13715, dual_wield_specialization_13848, dual_wield_specialization_13849, dual_wield_specialization_13851, dual_wield_specialization_13852],
    player_castable=False,
)


granted_by_talent(
    id=222,
    tab=combat_181_tab,
    tier=3,
    column=1,
    ranks=[improved_sprint_13743, improved_sprint_13875],
    player_castable=False,
)


granted_by_talent(
    id=223,
    tab=combat_181_tab,
    tier=4,
    column=1,
    ranks=[blade_flurry_13877],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=241,
    tab=subtlety_183_tab,
    tier=0,
    column=1,
    ranks=[13958, 13970, 13971],
    player_castable=False,
)


granted_by_talent(
    id=242,
    tab=combat_181_tab,
    tier=4,
    column=2,
    ranks=[13960, 13961, 13962, 13963, 13964],
    player_castable=False,
)


granted_by_talent(
    id=244,
    tab=subtlety_183_tab,
    tier=1,
    column=2,
    ranks=[camouflage_13975, camouflage_14062, camouflage_14063],
    player_castable=False,
)


granted_by_talent(
    id=245,
    tab=subtlety_183_tab,
    tier=3,
    column=1,
    ranks=[initiative_13976, initiative_13979, initiative_13980],
    player_castable=False,
)


granted_by_talent(
    id=246,
    tab=subtlety_183_tab,
    tier=3,
    column=0,
    ranks=[13983, 14070, 14071],
    player_castable=False,
)


granted_by_talent(
    id=247,
    tab=subtlety_183_tab,
    tier=2,
    column=0,
    ranks=[elusiveness_13981, elusiveness_14066],
    player_castable=False,
)


granted_by_talent(
    id=261,
    tab=subtlety_183_tab,
    tier=0,
    column=2,
    ranks=[opportunity_14057, opportunity_14072],
    player_castable=False,
)


granted_by_talent(
    id=262,
    tab=subtlety_183_tab,
    tier=1,
    column=1,
    ranks=[dirty_tricks_14076, dirty_tricks_14094],
    player_castable=False,
)


granted_by_talent(
    id=263,
    tab=subtlety_183_tab,
    tier=3,
    column=2,
    ranks=[improved_ambush_14079, improved_ambush_14080],
    player_castable=False,
)


granted_by_talent(
    id=265,
    tab=subtlety_183_tab,
    tier=4,
    column=2,
    ranks=[dirty_deeds_14082, dirty_deeds_14083],
    player_castable=False,
)


granted_by_talent(
    id=268,
    tab=assassination_182_tab,
    tier=3,
    column=2,
    ranks=[improved_poisons_14113, improved_poisons_14114, improved_poisons_14115, improved_poisons_14116, improved_poisons_14117],
    player_castable=False,
)


granted_by_talent(
    id=269,
    tab=assassination_182_tab,
    tier=2,
    column=2,
    ranks=[lethality_14128, lethality_14132, lethality_14135, lethality_14136, lethality_14137],
    player_castable=False,
    depends_on={'talent_id': 270, 'rank': 4},
)


granted_by_talent(
    id=270,
    tab=assassination_182_tab,
    tier=0,
    column=2,
    ranks=[14138, 14139, 14140, 14141, 14142],
    player_castable=False,
)


granted_by_talent(
    id=272,
    tab=assassination_182_tab,
    tier=0,
    column=1,
    ranks=[14144, 14148],
    player_castable=False,
)


granted_by_talent(
    id=273,
    tab=assassination_182_tab,
    tier=1,
    column=0,
    ranks=[ruthlessness_14156, ruthlessness_14160, ruthlessness_14161],
    player_castable=False,
)


granted_by_talent(
    id=274,
    tab=assassination_182_tab,
    tier=5,
    column=2,
    ranks=[murder_14158, murder_14159],
    player_castable=False,
)


granted_by_talent(
    id=276,
    tab=assassination_182_tab,
    tier=0,
    column=0,
    ranks=[improved_eviscerate_14162, improved_eviscerate_14163, improved_eviscerate_14164],
    player_castable=False,
)


granted_by_talent(
    id=277,
    tab=assassination_182_tab,
    tier=1,
    column=3,
    ranks=[puncturing_wounds_13733, puncturing_wounds_13865, puncturing_wounds_13866],
    player_castable=False,
)


granted_by_talent(
    id=278,
    tab=assassination_182_tab,
    tier=2,
    column=1,
    ranks=[improved_expose_armor_14168, improved_expose_armor_14169],
    player_castable=False,
)


granted_by_talent(
    id=279,
    tab=assassination_182_tab,
    tier=4,
    column=2,
    ranks=[improved_kidney_shot_14174, improved_kidney_shot_14175, improved_kidney_shot_14176],
    player_castable=False,
)


granted_by_talent(
    id=280,
    tab=assassination_182_tab,
    tier=4,
    column=1,
    ranks=[cold_blood_14177],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=281,
    tab=assassination_182_tab,
    tier=6,
    column=1,
    ranks=[58426],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=283,
    tab=assassination_182_tab,
    tier=5,
    column=1,
    ranks=[seal_fate_14186, seal_fate_14190, seal_fate_14193, seal_fate_14194, seal_fate_14195],
    player_castable=False,
    depends_on={'talent_id': 280, 'rank': 0},
)


granted_by_talent(
    id=284,
    tab=subtlety_183_tab,
    tier=4,
    column=1,
    ranks=[preparation_14185],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=301,
    tab=combat_181_tab,
    tier=2,
    column=1,
    ranks=[riposte_14251],
    player_castable=False,
    depends_on={'talent_id': 187, 'rank': 2},
    flags=1,
)


granted_by_talent(
    id=303,
    tab=subtlety_183_tab,
    tier=2,
    column=1,
    ranks=[ghostly_strike_14278],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=381,
    tab=subtlety_183_tab,
    tier=6,
    column=1,
    ranks=[premeditation_14183],
    player_castable=False,
    depends_on={'talent_id': 284, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=382,
    tab=assassination_182_tab,
    tier=2,
    column=0,
    ranks=[vigor_14983],
    player_castable=False,
)


granted_by_talent(
    id=681,
    tab=subtlety_183_tab,
    tier=4,
    column=3,
    ranks=[hemorrhage_16511],
    player_castable=False,
    depends_on={'talent_id': 1123, 'rank': 2},
    flags=1,
)


granted_by_talent(
    id=682,
    tab=assassination_182_tab,
    tier=3,
    column=1,
    ranks=[vile_poisons_16513, vile_poisons_16514, vile_poisons_16515],
    player_castable=False,
)


granted_by_talent(
    id=1122,
    tab=combat_181_tab,
    tier=3,
    column=3,
    ranks=[aggression_18427, aggression_18428, aggression_18429, aggression_61330, aggression_61331],
    player_castable=False,
)


granted_by_talent(
    id=1123,
    tab=subtlety_183_tab,
    tier=2,
    column=2,
    ranks=[serrated_blades_14171, serrated_blades_14172, serrated_blades_14173],
    player_castable=False,
)


granted_by_talent(
    id=1700,
    tab=subtlety_183_tab,
    tier=1,
    column=0,
    ranks=[sleight_of_hand_30892, sleight_of_hand_30893],
    player_castable=False,
)


granted_by_talent(
    id=1701,
    tab=subtlety_183_tab,
    tier=4,
    column=0,
    ranks=[30894, 30895],
    player_castable=False,
)


granted_by_talent(
    id=1702,
    tab=subtlety_183_tab,
    tier=5,
    column=2,
    ranks=[30902, 30903, 30904, 30905, 30906],
    player_castable=False,
)


granted_by_talent(
    id=1703,
    tab=combat_181_tab,
    tier=5,
    column=1,
    ranks=[30919, 30920],
    player_castable=False,
    depends_on={'talent_id': 223, 'rank': 0},
)


granted_by_talent(
    id=1705,
    tab=combat_181_tab,
    tier=6,
    column=0,
    ranks=[31122, 31123, 61329],
    player_castable=False,
)


granted_by_talent(
    id=1706,
    tab=combat_181_tab,
    tier=5,
    column=2,
    ranks=[blade_twisting_31124, blade_twisting_31126],
    player_castable=False,
)


granted_by_talent(
    id=1707,
    tab=combat_181_tab,
    tier=6,
    column=2,
    ranks=[31130, 31131],
    player_castable=False,
)


granted_by_talent(
    id=1709,
    tab=combat_181_tab,
    tier=8,
    column=1,
    ranks=[surprise_attacks_32601],
    player_castable=False,
    depends_on={'talent_id': 205, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=1711,
    tab=subtlety_183_tab,
    tier=6,
    column=0,
    ranks=[31211, 31212, 31213],
    player_castable=False,
)


granted_by_talent(
    id=1712,
    tab=subtlety_183_tab,
    tier=7,
    column=1,
    ranks=[sinister_calling_31216, sinister_calling_31217, sinister_calling_31218, sinister_calling_31219, sinister_calling_31220],
    player_castable=False,
    depends_on={'talent_id': 381, 'rank': 0},
)


granted_by_talent(
    id=1713,
    tab=subtlety_183_tab,
    tier=5,
    column=0,
    ranks=[31221, 31222, master_of_subtlety_31223],
    player_castable=False,
)


granted_by_talent(
    id=1714,
    tab=subtlety_183_tab,
    tier=8,
    column=1,
    ranks=[shadowstep_36554],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1715,
    tab=assassination_182_tab,
    tier=8,
    column=0,
    ranks=[master_poisoner_31226, master_poisoner_31227, master_poisoner_58410],
    player_castable=False,
)


granted_by_talent(
    id=1718,
    tab=assassination_182_tab,
    tier=7,
    column=2,
    ranks=[find_weakness_31234, find_weakness_31235, find_weakness_31236],
    player_castable=False,
)


granted_by_talent(
    id=1719,
    tab=assassination_182_tab,
    tier=8,
    column=1,
    ranks=[mutilate_1329],
    player_castable=False,
    depends_on={'talent_id': 281, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=1721,
    tab=assassination_182_tab,
    tier=4,
    column=0,
    ranks=[31208, 31209],
    player_castable=False,
)


granted_by_talent(
    id=1722,
    tab=subtlety_183_tab,
    tier=6,
    column=2,
    ranks=[cheat_death_31228, cheat_death_31229, cheat_death_31230],
    player_castable=False,
)


granted_by_talent(
    id=1723,
    tab=assassination_182_tab,
    tier=6,
    column=2,
    ranks=[deadened_nerves_31380, deadened_nerves_31382, deadened_nerves_31383],
    player_castable=False,
)


granted_by_talent(
    id=1762,
    tab=assassination_182_tab,
    tier=4,
    column=3,
    ranks=[quick_recovery_31244, quick_recovery_31245],
    player_castable=False,
)


granted_by_talent(
    id=1825,
    tab=combat_181_tab,
    tier=7,
    column=2,
    ranks=[combat_potency_35541, combat_potency_35550, combat_potency_35551, combat_potency_35552, combat_potency_35553],
    player_castable=False,
)


granted_by_talent(
    id=1827,
    tab=combat_181_tab,
    tier=1,
    column=0,
    ranks=[improved_slice_and_dice_14165, improved_slice_and_dice_14166],
    player_castable=False,
)


granted_by_talent(
    id=2065,
    tab=assassination_182_tab,
    tier=6,
    column=0,
    ranks=[deadly_brew_51625, deadly_brew_51626],
    player_castable=False,
)


granted_by_talent(
    id=2066,
    tab=assassination_182_tab,
    tier=8,
    column=2,
    ranks=[51627, 51628, 51629],
    player_castable=False,
)


granted_by_talent(
    id=2068,
    tab=assassination_182_tab,
    tier=1,
    column=1,
    ranks=[blood_spatter_51632, blood_spatter_51633],
    player_castable=False,
)


granted_by_talent(
    id=2069,
    tab=assassination_182_tab,
    tier=7,
    column=0,
    ranks=[51634, 51635, 51636],
    player_castable=False,
)


granted_by_talent(
    id=2070,
    tab=assassination_182_tab,
    tier=9,
    column=1,
    ranks=[cut_to_the_chase_51664, cut_to_the_chase_51665, cut_to_the_chase_51667, cut_to_the_chase_51668, cut_to_the_chase_51669],
    player_castable=False,
)


granted_by_talent(
    id=2071,
    tab=assassination_182_tab,
    tier=10,
    column=1,
    ranks=[hunger_for_blood_51662],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2072,
    tab=combat_181_tab,
    tier=7,
    column=0,
    ranks=[throwing_specialization_5952, throwing_specialization_51679],
    player_castable=False,
)


granted_by_talent(
    id=2073,
    tab=combat_181_tab,
    tier=8,
    column=0,
    ranks=[51672, 51674],
    player_castable=False,
)


granted_by_talent(
    id=2074,
    tab=combat_181_tab,
    tier=8,
    column=2,
    ranks=[savage_combat_51682, savage_combat_58413],
    player_castable=False,
)


granted_by_talent(
    id=2075,
    tab=combat_181_tab,
    tier=9,
    column=1,
    ranks=[51685, 51686, 51687, 51688, 51689],
    player_castable=False,
)


granted_by_talent(
    id=2076,
    tab=combat_181_tab,
    tier=10,
    column=1,
    ranks=[killing_spree_51690],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2077,
    tab=subtlety_183_tab,
    tier=7,
    column=2,
    ranks=[waylay_51692, waylay_51696],
    player_castable=False,
)


granted_by_talent(
    id=2078,
    tab=subtlety_183_tab,
    tier=8,
    column=0,
    ranks=[51698, 51700, 51701],
    player_castable=False,
)


granted_by_talent(
    id=2079,
    tab=subtlety_183_tab,
    tier=8,
    column=2,
    ranks=[filthy_tricks_58414, filthy_tricks_58415],
    player_castable=False,
)


granted_by_talent(
    id=2080,
    tab=subtlety_183_tab,
    tier=9,
    column=1,
    ranks=[slaughter_from_the_shadows_51708, slaughter_from_the_shadows_51709, slaughter_from_the_shadows_51710, slaughter_from_the_shadows_51711, slaughter_from_the_shadows_51712],
    player_castable=False,
)


granted_by_talent(
    id=2081,
    tab=subtlety_183_tab,
    tier=10,
    column=1,
    ranks=[shadow_dance_51713],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2244,
    tab=subtlety_183_tab,
    tier=0,
    column=0,
    ranks=[relentless_strikes_14179, relentless_strikes_58422, relentless_strikes_58423, relentless_strikes_58424, relentless_strikes_58425],
    player_castable=False,
)
