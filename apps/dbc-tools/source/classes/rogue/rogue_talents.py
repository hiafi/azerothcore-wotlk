"""
Rogue - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/rogue.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .rogue_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, retire_talent, tab
from .rogue_spells import adrenaline_rush_13750, blade_flurry_13877, cold_blood_14177, ghostly_strike_14278, hunger_for_blood_51662, killing_spree_51690, mutilate_1329, preparation_14185, riposte_14251, shadow_dance_51713, shadowstep_36554
from .rogue_combat import accuracy_203953, accuracy_203954, accuracy_203955, between_the_eyes_learn_203956, blade_rush_203980, celerity_203977, celerity_203978, coup_de_grace_203970, coup_de_grace_203971, coup_de_grace_203972, deft_maneuvers_203973, deft_maneuvers_203974, en_garde_203969, grappling_hook_203963, hair_trigger_203975, hair_trigger_203976, improved_feint_203979, improved_riposte_203966, improved_riposte_203967, improved_riposte_203968, quick_draw_203964, quick_reflexes_203950, quick_reflexes_203951, quick_reflexes_203952, reinforced_leather_203960, reinforced_leather_203961, reinforced_leather_203962, restless_blades_203965, surprise_attacks_203981, surprise_attacks_203982
from .rogue_trigger_spells import hack_and_slash_13960, hack_and_slash_13961, hack_and_slash_13962, lightning_reflexes_13712, lightning_reflexes_13788, lightning_reflexes_13789, precision_13705, precision_13832, precision_13843, prey_on_the_weak_51685, prey_on_the_weak_51686, prey_on_the_weak_51687, unfair_advantage_51672, unfair_advantage_51674, weapon_specialization_13709, weapon_specialization_13800, weapon_specialization_13801, aggression_18427, aggression_18428, aggression_18429, blade_twisting_31124, blade_twisting_31126, blood_spatter_51632, blood_spatter_51633, camouflage_13975, camouflage_14062, camouflage_14063, cheat_death_31228, cheat_death_31229, cheat_death_31230, deadened_nerves_31380, deadened_nerves_31382, deadened_nerves_31383, deadly_brew_51625, deadly_brew_51626, dual_wield_specialization_13715, dual_wield_specialization_13848, dual_wield_specialization_13849, elusiveness_13981, elusiveness_14066, endurance_13742, endurance_13872, find_weakness_31234, find_weakness_31235, find_weakness_31236, fleet_footed_31208, fleet_footed_31209, focused_attacks_51634, focused_attacks_51635, focused_attacks_51636, improved_ambush_14079, improved_ambush_14080, improved_kick_13754, improved_kick_13867, improved_poisons_14113, improved_poisons_14114, improved_poisons_14115, improved_sinister_strike_13732, improved_sinister_strike_13863, improved_slice_and_dice_14165, improved_slice_and_dice_14166, improved_sprint_13743, improved_sprint_13875, initiative_13976, initiative_13979, initiative_13980, lethality_14128, lethality_14132, lethality_14135, malice_14138, malice_14139, malice_14140, master_poisoner_31226, master_poisoner_31227, master_poisoner_58410, murder_14158, murder_14159, opportunity_14057, opportunity_14072, puncturing_wounds_13733, puncturing_wounds_13865, puncturing_wounds_13866, quick_recovery_31244, quick_recovery_31245, relentless_strikes_14179, relentless_strikes_58422, relentless_strikes_58423, remorseless_attacks_14144, remorseless_attacks_14148, ruthlessness_14156, ruthlessness_14160, ruthlessness_14161, savage_combat_51682, savage_combat_58413, seal_fate_14186, seal_fate_14190, seal_fate_14193, serrated_blades_14171, serrated_blades_14172, serrated_blades_14173, sinister_calling_31216, sinister_calling_31217, sinister_calling_31218, slaughter_from_the_shadows_51708, slaughter_from_the_shadows_51709, slaughter_from_the_shadows_51710, surprise_attacks_32601, throwing_specialization_51679, throwing_specialization_5952, vigor_14983, vile_poisons_16513, vile_poisons_16514, vile_poisons_16515, waylay_51692, waylay_51696
from .rogue_assassination import blindside_203805, blindside_203806, cut_throat_203814, cut_throat_203815, dashing_scoundrel_203820, dashing_scoundrel_203821, doomblade_203803, doomblade_203804, fleet_footed_203824, indiscriminate_carnage_203818, indiscriminate_carnage_203819, kingsbane_203822, overkill_203825, overkill_203826, poison_bomb_203807, quick_pace_203800, quick_pace_203801, quick_pace_203802, shattering_vial_203808, toxic_blade_203816, toxic_blade_203817, venomous_fan_203809, venomous_fan_203810, vigor_203823, zoldyck_recipe_203811, zoldyck_recipe_203812, zoldyck_recipe_203813
from .rogue_subtlety import akaaris_echo_204144, akaaris_echo_204145, death_from_above_204148, deepening_shadows_204130, deepening_shadows_204131, deepening_shadows_204132, executioner_204142, executioner_204143, finality_204140, finality_204141, hemorrhage_204152, lingering_shadow_204138, lingering_shadow_204139, mark_of_the_master_assassin_204146, mark_of_the_master_assassin_204147, master_of_subtlety_204149, master_of_subtlety_204150, master_of_subtlety_204151, premeditation_204153, second_volley_204136, second_volley_204137, shadow_resolve_204133, shadow_resolve_204134, shadow_resolve_204135


combat_181_tab = tab(
    id=181,
    name='Combat',
    class_mask=8,
    order_index=1,
    spell_icon_id=243,
    skill_line=38,  # S3a: derives the SkillLineAbility rows of the Combat castables (Grappling Hook, En Garde, Blade Rush); not a TalentTab.dbc column
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'RogueCombat'},
)


assassination_182_tab = tab(
    id=182,
    name='Assassination',
    class_mask=8,
    spell_icon_id=514,
    skill_line=253,  # S1a: derives the SkillLineAbility rows of the Assassination castables (Poison Bomb, Kingsbane); not a TalentTab.dbc column
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'RogueAssassination'},
)


subtlety_183_tab = tab(
    id=183,
    name='Subtlety',
    class_mask=8,
    order_index=2,
    spell_icon_id=250,
    skill_line=39,  # S2a: derives the SkillLineAbility row of the Subtlety castable (Death from Above); not a TalentTab.dbc column
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'RogueSubtlety'},
)


granted_by_talent(
    id=181,
    tab=combat_181_tab,
    tier=1,
    column=3,
    ranks=[precision_13705, precision_13832, precision_13843],
    player_castable=False,
)


granted_by_talent(
    id=184,
    tab=combat_181_tab,
    tier=4,
    column=0,
    ranks=[weapon_specialization_13709, weapon_specialization_13800, weapon_specialization_13801],
    player_castable=False,
)


granted_by_talent(
    id=186,
    tab=combat_181_tab,
    tier=3,
    column=2,
    ranks=[lightning_reflexes_13712, lightning_reflexes_13788, lightning_reflexes_13789],
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
    tier=1,
    column=2,
    ranks=[improved_kick_13754, improved_kick_13867],
    player_castable=False,
)


granted_by_talent(
    id=221,
    tab=combat_181_tab,
    tier=0,
    column=2,
    ranks=[dual_wield_specialization_13715, dual_wield_specialization_13848, dual_wield_specialization_13849],
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
    id=242,
    tab=combat_181_tab,
    tier=4,
    column=2,
    ranks=[hack_and_slash_13960, hack_and_slash_13961, hack_and_slash_13962],
    player_castable=False,
)


granted_by_talent(
    id=244,
    tab=subtlety_183_tab,
    tier=1,
    column=0,
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
    column=0,
    ranks=[opportunity_14057, opportunity_14072],
    player_castable=False,
)


granted_by_talent(
    id=263,
    tab=subtlety_183_tab,
    tier=3,
    column=0,
    ranks=[improved_ambush_14079, improved_ambush_14080],
    player_castable=False,
)


granted_by_talent(
    id=268,
    tab=assassination_182_tab,
    tier=3,
    column=3,
    ranks=[improved_poisons_14113, improved_poisons_14114, improved_poisons_14115],
    player_castable=False,
)


granted_by_talent(
    id=269,
    tab=assassination_182_tab,
    tier=2,
    column=0,
    ranks=[lethality_14128, lethality_14132, lethality_14135],
    player_castable=False,
)


granted_by_talent(
    id=270,
    tab=assassination_182_tab,
    tier=0,
    column=1,
    ranks=[malice_14138, malice_14139, malice_14140],
    player_castable=False,
)


granted_by_talent(
    id=272,
    tab=assassination_182_tab,
    tier=0,
    column=2,
    ranks=[remorseless_attacks_14144, remorseless_attacks_14148],
    player_castable=False,
)


granted_by_talent(
    id=273,
    tab=assassination_182_tab,
    tier=1,
    column=1,
    ranks=[ruthlessness_14156, ruthlessness_14160, ruthlessness_14161],
    player_castable=False,
)


granted_by_talent(
    id=274,
    tab=assassination_182_tab,
    tier=5,
    column=3,
    ranks=[murder_14158, murder_14159],
    player_castable=False,
)


granted_by_talent(
    id=277,
    tab=assassination_182_tab,
    tier=1,
    column=0,
    ranks=[puncturing_wounds_13733, puncturing_wounds_13865, puncturing_wounds_13866],
    player_castable=False,
)


granted_by_talent(
    id=280,
    tab=assassination_182_tab,
    tier=4,
    column=0,
    ranks=[cold_blood_14177],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=281,
    tab=assassination_182_tab,
    tier=6,
    column=0,
    ranks=[overkill_203825, overkill_203826],
    player_castable=False,
)


granted_by_talent(
    id=283,
    tab=assassination_182_tab,
    tier=5,
    column=0,
    ranks=[seal_fate_14186, seal_fate_14190, seal_fate_14193],
    player_castable=False,
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
    column=3,
    ranks=[riposte_14251],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=381,
    tab=subtlety_183_tab,
    tier=6,
    column=0,
    ranks=[premeditation_204153],
    player_castable=False,
)


granted_by_talent(
    id=382,
    tab=assassination_182_tab,
    tier=2,
    column=3,
    ranks=[vigor_14983, vigor_203823],
    player_castable=False,
)


granted_by_talent(
    id=681,
    tab=subtlety_183_tab,
    tier=4,
    column=3,
    ranks=[hemorrhage_204152],
    player_castable=False,
)


granted_by_talent(
    id=682,
    tab=assassination_182_tab,
    tier=5,
    column=1,
    ranks=[vile_poisons_16513, vile_poisons_16514, vile_poisons_16515],
    player_castable=False,
)


granted_by_talent(
    id=1122,
    tab=combat_181_tab,
    tier=3,
    column=3,
    ranks=[aggression_18427, aggression_18428, aggression_18429],
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
    column=3,
    ranks=[30902, 30903, 30904],
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
    id=1709,
    tab=combat_181_tab,
    tier=8,
    column=3,
    ranks=[surprise_attacks_32601, surprise_attacks_203981, surprise_attacks_203982],
    player_castable=False,
)


granted_by_talent(
    id=1711,
    tab=subtlety_183_tab,
    tier=1,
    column=3,
    ranks=[31211, 31212, 31213],
    player_castable=False,
)


granted_by_talent(
    id=1712,
    tab=subtlety_183_tab,
    tier=7,
    column=2,
    ranks=[sinister_calling_31216, sinister_calling_31217, sinister_calling_31218],
    player_castable=False,
)


granted_by_talent(
    id=1713,
    tab=subtlety_183_tab,
    tier=6,
    column=1,
    ranks=[master_of_subtlety_204149, master_of_subtlety_204150, master_of_subtlety_204151],
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
    tier=6,
    column=1,
    ranks=[master_poisoner_31226, master_poisoner_31227, master_poisoner_58410],
    player_castable=False,
)


granted_by_talent(
    id=1718,
    tab=assassination_182_tab,
    tier=7,
    column=3,
    ranks=[find_weakness_31234, find_weakness_31235, find_weakness_31236],
    player_castable=False,
)


granted_by_talent(
    id=1719,
    tab=assassination_182_tab,
    tier=2,
    column=1,
    ranks=[mutilate_1329],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1721,
    tab=assassination_182_tab,
    tier=4,
    column=3,
    ranks=[fleet_footed_31208, fleet_footed_31209, fleet_footed_203824],
    player_castable=False,
)


granted_by_talent(
    id=1722,
    tab=subtlety_183_tab,
    tier=6,
    column=3,
    ranks=[cheat_death_31228, cheat_death_31229, cheat_death_31230],
    player_castable=False,
)


granted_by_talent(
    id=1723,
    tab=assassination_182_tab,
    tier=6,
    column=3,
    ranks=[deadened_nerves_31380, deadened_nerves_31382, deadened_nerves_31383],
    player_castable=False,
)


granted_by_talent(
    id=1762,
    tab=assassination_182_tab,
    tier=3,
    column=1,
    ranks=[quick_recovery_31244, quick_recovery_31245],
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
    column=2,
    ranks=[deadly_brew_51625, deadly_brew_51626],
    player_castable=False,
)


granted_by_talent(
    id=2068,
    tab=assassination_182_tab,
    tier=1,
    column=2,
    ranks=[blood_spatter_51632, blood_spatter_51633],
    player_castable=False,
)


granted_by_talent(
    id=2069,
    tab=assassination_182_tab,
    tier=7,
    column=0,
    ranks=[focused_attacks_51634, focused_attacks_51635, focused_attacks_51636],
    player_castable=False,
)


granted_by_talent(
    id=2071,
    tab=assassination_182_tab,
    tier=8,
    column=1,
    ranks=[hunger_for_blood_51662],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2072,
    tab=subtlety_183_tab,
    tier=5,
    column=2,
    ranks=[throwing_specialization_5952, throwing_specialization_51679],
    player_castable=False,
)


granted_by_talent(
    id=2073,
    tab=combat_181_tab,
    tier=8,
    column=0,
    ranks=[unfair_advantage_51672, unfair_advantage_51674],
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
    ranks=[prey_on_the_weak_51685, prey_on_the_weak_51686, prey_on_the_weak_51687],
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
    column=1,
    ranks=[waylay_51692, waylay_51696],
    player_castable=False,
)


granted_by_talent(
    id=2078,
    tab=subtlety_183_tab,
    tier=8,
    column=2,
    ranks=[51698, 51700, 51701],
    player_castable=False,
)


granted_by_talent(
    id=2080,
    tab=subtlety_183_tab,
    tier=2,
    column=3,
    ranks=[slaughter_from_the_shadows_51708, slaughter_from_the_shadows_51709, slaughter_from_the_shadows_51710],
    player_castable=False,
)


granted_by_talent(
    id=2081,
    tab=subtlety_183_tab,
    tier=2,
    column=1,
    ranks=[shadow_dance_51713],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2244,
    tab=subtlety_183_tab,
    tier=0,
    column=2,
    ranks=[relentless_strikes_14179, relentless_strikes_58422, relentless_strikes_58423],
    player_castable=False,
)


# rogue-rework S1a: 12 new Assassination talents (ids 60390-60401). Poison Bomb and Kingsbane are castables (SkillLineAbility 30800 / 30801, skill 253 from the tab).
granted_by_talent(
    id=60390,
    tab=assassination_182_tab,
    tier=0,
    column=0,
    ranks=[quick_pace_203800, quick_pace_203801, quick_pace_203802],
    player_castable=False,
)


granted_by_talent(
    id=60391,
    tab=assassination_182_tab,
    tier=2,
    column=2,
    ranks=[doomblade_203803, doomblade_203804],
    player_castable=False,
)


granted_by_talent(
    id=60392,
    tab=assassination_182_tab,
    tier=3,
    column=0,
    ranks=[blindside_203805, blindside_203806],
    player_castable=False,
)


granted_by_talent(
    id=60393,
    tab=assassination_182_tab,
    tier=4,
    column=1,
    ranks=[poison_bomb_203807],
    player_castable=True,
    skill_line_ability_ids=[30800],
    flags=1,
)


granted_by_talent(
    id=60394,
    tab=assassination_182_tab,
    tier=4,
    column=2,
    ranks=[shattering_vial_203808],
    player_castable=False,
)


granted_by_talent(
    id=60395,
    tab=assassination_182_tab,
    tier=5,
    column=2,
    ranks=[venomous_fan_203809, venomous_fan_203810],
    player_castable=False,
)


granted_by_talent(
    id=60396,
    tab=assassination_182_tab,
    tier=7,
    column=1,
    ranks=[zoldyck_recipe_203811, zoldyck_recipe_203812, zoldyck_recipe_203813],
    player_castable=False,
)


granted_by_talent(
    id=60397,
    tab=assassination_182_tab,
    tier=7,
    column=2,
    ranks=[cut_throat_203814, cut_throat_203815],
    player_castable=False,
)


granted_by_talent(
    id=60398,
    tab=assassination_182_tab,
    tier=8,
    column=0,
    ranks=[toxic_blade_203816, toxic_blade_203817],
    player_castable=False,
)


granted_by_talent(
    id=60399,
    tab=assassination_182_tab,
    tier=8,
    column=2,
    ranks=[indiscriminate_carnage_203818, indiscriminate_carnage_203819],
    player_castable=False,
)


granted_by_talent(
    id=60400,
    tab=assassination_182_tab,
    tier=9,
    column=1,
    ranks=[dashing_scoundrel_203820, dashing_scoundrel_203821],
    player_castable=False,
)


granted_by_talent(
    id=60401,
    tab=assassination_182_tab,
    tier=10,
    column=1,
    ranks=[kingsbane_203822],
    player_castable=True,
    skill_line_ability_ids=[30801],
    flags=1,
)


# rogue-rework S2a: nine new Subtlety talents (the stock rows were cut or moved above).


granted_by_talent(
    id=60425,
    tab=subtlety_183_tab,
    tier=0,
    column=1,
    ranks=[deepening_shadows_204130, deepening_shadows_204131, deepening_shadows_204132],
    player_castable=False,
)


granted_by_talent(
    id=60426,
    tab=subtlety_183_tab,
    tier=1,
    column=1,
    ranks=[shadow_resolve_204133, shadow_resolve_204134, shadow_resolve_204135],
    player_castable=False,
)


granted_by_talent(
    id=60427,
    tab=subtlety_183_tab,
    tier=3,
    column=2,
    ranks=[second_volley_204136, second_volley_204137],
    player_castable=False,
)


granted_by_talent(
    id=60428,
    tab=subtlety_183_tab,
    tier=3,
    column=3,
    ranks=[lingering_shadow_204138, lingering_shadow_204139],
    player_castable=False,
)


granted_by_talent(
    id=60429,
    tab=subtlety_183_tab,
    tier=4,
    column=2,
    ranks=[finality_204140, finality_204141],
    player_castable=False,
)


granted_by_talent(
    id=60430,
    tab=subtlety_183_tab,
    tier=5,
    column=1,
    ranks=[executioner_204142, executioner_204143],
    player_castable=False,
)


granted_by_talent(
    id=60431,
    tab=subtlety_183_tab,
    tier=8,
    column=0,
    ranks=[akaaris_echo_204144, akaaris_echo_204145],
    player_castable=False,
)


granted_by_talent(
    id=60432,
    tab=subtlety_183_tab,
    tier=9,
    column=1,
    ranks=[mark_of_the_master_assassin_204146, mark_of_the_master_assassin_204147],
    player_castable=False,
)


granted_by_talent(
    id=60433,
    tab=subtlety_183_tab,
    tier=10,
    column=1,
    ranks=[death_from_above_204148],
    player_castable=True,
    skill_line_ability_ids=[30825],
    flags=1,
)


# rogue-rework S3a: 15 new Combat talents (ids 60405-60419). Between the Eyes is the LEARN rank 203956 (it teaches Pistol Shot, Between the Eyes and the marker); Grappling Hook, En Garde and Blade Rush are castables (SkillLineAbility 30812-30814, skill 38 from the tab).

granted_by_talent(
    id=60405,
    tab=combat_181_tab,
    tier=0,
    column=0,
    ranks=[quick_reflexes_203950, quick_reflexes_203951, quick_reflexes_203952],
    player_castable=False,
)


granted_by_talent(
    id=60406,
    tab=combat_181_tab,
    tier=0,
    column=3,
    ranks=[accuracy_203953, accuracy_203954, accuracy_203955],
    player_castable=False,
)


granted_by_talent(
    id=60407,
    tab=combat_181_tab,
    tier=2,
    column=1,
    ranks=[between_the_eyes_learn_203956],
    player_castable=False,
)


granted_by_talent(
    id=60408,
    tab=combat_181_tab,
    tier=2,
    column=2,
    ranks=[reinforced_leather_203960, reinforced_leather_203961, reinforced_leather_203962],
    player_castable=False,
)


granted_by_talent(
    id=60409,
    tab=combat_181_tab,
    tier=3,
    column=0,
    ranks=[grappling_hook_203963],
    player_castable=True,
    skill_line_ability_ids=[30812],
    flags=1,
)


granted_by_talent(
    id=60410,
    tab=combat_181_tab,
    tier=4,
    column=3,
    ranks=[quick_draw_203964],
    player_castable=False,
)


granted_by_talent(
    id=60411,
    tab=combat_181_tab,
    tier=5,
    column=0,
    ranks=[restless_blades_203965],
    player_castable=False,
)


granted_by_talent(
    id=60412,
    tab=combat_181_tab,
    tier=5,
    column=1,
    ranks=[improved_riposte_203966, improved_riposte_203967, improved_riposte_203968],
    player_castable=False,
)


granted_by_talent(
    id=60413,
    tab=combat_181_tab,
    tier=5,
    column=3,
    ranks=[en_garde_203969],
    player_castable=True,
    skill_line_ability_ids=[30813],
    flags=1,
)


granted_by_talent(
    id=60414,
    tab=combat_181_tab,
    tier=6,
    column=0,
    ranks=[coup_de_grace_203970, coup_de_grace_203971, coup_de_grace_203972],
    player_castable=False,
)


granted_by_talent(
    id=60415,
    tab=combat_181_tab,
    tier=6,
    column=2,
    ranks=[deft_maneuvers_203973, deft_maneuvers_203974],
    player_castable=False,
)


granted_by_talent(
    id=60416,
    tab=combat_181_tab,
    tier=6,
    column=3,
    ranks=[hair_trigger_203975, hair_trigger_203976],
    player_castable=False,
)


granted_by_talent(
    id=60417,
    tab=combat_181_tab,
    tier=7,
    column=2,
    ranks=[celerity_203977, celerity_203978],
    player_castable=False,
)


granted_by_talent(
    id=60418,
    tab=combat_181_tab,
    tier=7,
    column=3,
    ranks=[improved_feint_203979],
    player_castable=False,
)


granted_by_talent(
    id=60419,
    tab=combat_181_tab,
    tier=8,
    column=1,
    ranks=[blade_rush_203980],
    player_castable=True,
    skill_line_ability_ids=[30814],
    flags=1,
)


# rogue-rework S2a: six stock Subtlety talents are cut; they move to the retired tab (their bindings are unbound in rogue_trigger_spells.py).
retire_talent(241)
retire_talent(1700)
retire_talent(262)
retire_talent(246)
retire_talent(265)
retire_talent(2079)


# RG0b: Ghostly Strike (talent 303) is cut; it becomes a level 10 trainer spell (rogue_trainers.py).
retire_talent(303)


# rogue-rework S1a: five stock Assassination talents are cut; they move to the retired tab (their bindings are unbound in rogue_trigger_spells.py).
retire_talent(276)
retire_talent(278)
retire_talent(279)
retire_talent(2066)
retire_talent(2070)


# rogue-rework S3a: six stock Combat talents are cut; they move to the retired tab (their bindings are unbound in rogue_trigger_spells.py).
retire_talent(203)
retire_talent(182)
retire_talent(1703)
retire_talent(1705)
retire_talent(1707)
retire_talent(1825)
