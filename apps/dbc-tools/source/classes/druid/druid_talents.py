"""
Druid - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/druid.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .druid_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, tab
from .druid_spells import berserk_50334, force_of_nature_33831, insect_swarm_5570, moonkin_form_24858, nature_s_swiftness_17116, starfall_48505, survival_instincts_61336, swiftmend_18562, typhoon_50516, wild_growth_48438
from .druid_trigger_spells import balance_of_power_33592, balance_of_power_33596, brambles_16836, brambles_16839, brambles_16840, brutal_impact_16940, brutal_impact_16941, celestial_focus_16850, celestial_focus_16923, celestial_focus_16924, dreamstate_33597, dreamstate_33599, dreamstate_33956, earth_and_moon_48506, earth_and_moon_48510, earth_and_moon_48511, eclipse_48516, eclipse_48521, eclipse_48525, empowered_rejuvenation_33886, empowered_rejuvenation_33887, empowered_rejuvenation_33888, empowered_rejuvenation_33889, empowered_rejuvenation_33890, empowered_touch_33879, empowered_touch_33880, feral_aggression_16858, feral_aggression_16859, feral_aggression_16860, feral_aggression_16861, feral_aggression_16862, feral_instinct_16947, feral_instinct_16948, feral_instinct_16949, feral_swiftness_17002, feral_swiftness_24866, ferocity_16934, ferocity_16935, ferocity_16936, ferocity_16937, ferocity_16938, furor_17056, furor_17058, furor_17059, furor_17060, furor_17061, gale_winds_48488, gale_winds_48514, genesis_57810, genesis_57811, genesis_57812, genesis_57813, genesis_57814, gift_of_nature_17104, gift_of_nature_24943, gift_of_nature_24944, gift_of_nature_24945, gift_of_nature_24946, gift_of_the_earthmother_51179, gift_of_the_earthmother_51180, gift_of_the_earthmother_51181, gift_of_the_earthmother_51182, gift_of_the_earthmother_51183, improved_barkskin_63410, improved_barkskin_63411, improved_faerie_fire_33600, improved_faerie_fire_33601, improved_faerie_fire_33602, improved_insect_swarm_57849, improved_insect_swarm_57850, improved_insect_swarm_57851, improved_leader_of_the_pack_34297, improved_leader_of_the_pack_34300, improved_mangle_48489, improved_mangle_48491, improved_mangle_48532, improved_mark_of_the_wild_17050, improved_mark_of_the_wild_17051, improved_moonfire_16821, improved_moonfire_16822, improved_moonkin_form_48384, improved_moonkin_form_48395, improved_moonkin_form_48396, improved_rejuvenation_17111, improved_rejuvenation_17112, improved_rejuvenation_17113, improved_tranquility_17123, improved_tranquility_17124, improved_tree_of_life_48535, improved_tree_of_life_48536, improved_tree_of_life_48537, infected_wounds_48483, infected_wounds_48484, infected_wounds_48485, intensity_17106, intensity_17107, intensity_17108, king_of_the_jungle_48492, king_of_the_jungle_48494, king_of_the_jungle_48495, leader_of_the_pack_17007, living_seed_48496, living_seed_48499, living_seed_48500, living_spirit_34151, living_spirit_34152, living_spirit_34153, lunar_guidance_33589, lunar_guidance_33590, lunar_guidance_33591, moonfury_16896, moonfury_16897, moonfury_16899, moonglow_16845, moonglow_16846, moonglow_16847, natural_perfection_33881, natural_perfection_33882, natural_perfection_33883, natural_reaction_57878, natural_reaction_57880, natural_reaction_57881, natural_shapeshifter_16833, natural_shapeshifter_16834, natural_shapeshifter_16835, naturalist_17069, naturalist_17070, naturalist_17071, naturalist_17072, naturalist_17073, nature_s_bounty_17074, nature_s_bounty_17075, nature_s_bounty_17076, nature_s_bounty_17077, nature_s_bounty_17078, nature_s_focus_17063, nature_s_focus_17065, nature_s_focus_17066, nature_s_grace_16880, nature_s_grace_61345, nature_s_grace_61346, nature_s_majesty_35363, nature_s_majesty_35364, nature_s_reach_16819, nature_s_reach_16820, nature_s_splendor_57865, nurturing_instinct_33872, nurturing_instinct_33873, omen_of_clarity_16864, predatory_instincts_33859, predatory_instincts_33866, predatory_instincts_33867, predatory_strikes_16972, predatory_strikes_16974, predatory_strikes_16975, primal_gore_63503, primal_precision_48409, primal_precision_48410, primal_tenacity_33851, primal_tenacity_33852, primal_tenacity_33957, protector_of_the_pack_57873, protector_of_the_pack_57876, protector_of_the_pack_57877, rend_and_tear_48432, rend_and_tear_48433, rend_and_tear_48434, rend_and_tear_51268, rend_and_tear_51269, revitalize_48539, revitalize_48544, revitalize_48545, savage_fury_16998, savage_fury_16999, shredding_attacks_16966, shredding_attacks_16968, starlight_wrath_16814, starlight_wrath_16815, starlight_wrath_16816, starlight_wrath_16817, starlight_wrath_16818, subtlety_17118, subtlety_17119, subtlety_17120, survival_of_the_fittest_33853, survival_of_the_fittest_33855, survival_of_the_fittest_33856, tranquil_spirit_24968, tranquil_spirit_24969, tranquil_spirit_24970, tranquil_spirit_24971, tranquil_spirit_24972, vengeance_16909, vengeance_16910, vengeance_16911, vengeance_16912, vengeance_16913, wrath_of_cenarius_33603, wrath_of_cenarius_33604, wrath_of_cenarius_33605, wrath_of_cenarius_33606, wrath_of_cenarius_33607


feral_combat_281_tab = tab(
    id=281,
    name='Feral Combat',
    class_mask=1024,
    order_index=1,
    spell_icon_id=107,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 431},
)


restoration_282_tab = tab(
    id=282,
    name='Restoration',
    class_mask=1024,
    order_index=2,
    spell_icon_id=962,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 661},
)


balance_283_tab = tab(
    id=283,
    name='Balance',
    class_mask=1024,
    spell_icon_id=225,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 137},
)


granted_by_talent(
    id=762,
    tab=balance_283_tab,
    tier=0,
    column=1,
    ranks=[starlight_wrath_16814, starlight_wrath_16815, starlight_wrath_16816, starlight_wrath_16817, starlight_wrath_16818],
    player_castable=False,
)


granted_by_talent(
    id=763,
    tab=balance_283_tab,
    tier=1,
    column=3,
    ranks=[improved_moonfire_16821, improved_moonfire_16822],
    player_castable=False,
)


granted_by_talent(
    id=764,
    tab=balance_283_tab,
    tier=2,
    column=3,
    ranks=[nature_s_reach_16819, nature_s_reach_16820],
    player_castable=False,
)


granted_by_talent(
    id=782,
    tab=balance_283_tab,
    tier=2,
    column=0,
    ranks=[brambles_16836, brambles_16839, brambles_16840],
    player_castable=False,
)


granted_by_talent(
    id=783,
    tab=balance_283_tab,
    tier=1,
    column=0,
    ranks=[moonglow_16845, moonglow_16846, moonglow_16847],
    player_castable=False,
)


granted_by_talent(
    id=784,
    tab=balance_283_tab,
    tier=3,
    column=2,
    ranks=[celestial_focus_16850, celestial_focus_16923, celestial_focus_16924],
    player_castable=False,
)


granted_by_talent(
    id=788,
    tab=balance_283_tab,
    tier=4,
    column=1,
    ranks=[insect_swarm_5570],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=789,
    tab=balance_283_tab,
    tier=2,
    column=1,
    ranks=[nature_s_grace_16880, nature_s_grace_61345, nature_s_grace_61346],
    player_castable=False,
    depends_on={'talent_id': 1822, 'rank': 1},
)


granted_by_talent(
    id=790,
    tab=balance_283_tab,
    tier=5,
    column=1,
    ranks=[moonfury_16896, moonfury_16897, moonfury_16899],
    player_castable=False,
)


granted_by_talent(
    id=792,
    tab=balance_283_tab,
    tier=3,
    column=1,
    ranks=[vengeance_16909, vengeance_16910, vengeance_16911, vengeance_16912, vengeance_16913],
    player_castable=False,
)


granted_by_talent(
    id=793,
    tab=balance_283_tab,
    tier=6,
    column=1,
    ranks=[moonkin_form_24858],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=794,
    tab=feral_combat_281_tab,
    tier=1,
    column=2,
    ranks=[16929, 16930, 16931],
    player_castable=False,
)


granted_by_talent(
    id=795,
    tab=feral_combat_281_tab,
    tier=0,
    column=2,
    ranks=[feral_aggression_16858, feral_aggression_16859, feral_aggression_16860, feral_aggression_16861, feral_aggression_16862],
    player_castable=False,
)


granted_by_talent(
    id=796,
    tab=feral_combat_281_tab,
    tier=0,
    column=1,
    ranks=[ferocity_16934, ferocity_16935, ferocity_16936, ferocity_16937, ferocity_16938],
    player_castable=False,
)


granted_by_talent(
    id=797,
    tab=feral_combat_281_tab,
    tier=4,
    column=0,
    ranks=[brutal_impact_16940, brutal_impact_16941],
    player_castable=False,
)


granted_by_talent(
    id=798,
    tab=feral_combat_281_tab,
    tier=2,
    column=2,
    ranks=[16942, 16943, 16944],
    player_castable=False,
)


granted_by_talent(
    id=799,
    tab=feral_combat_281_tab,
    tier=1,
    column=0,
    ranks=[feral_instinct_16947, feral_instinct_16948, feral_instinct_16949],
    player_castable=False,
)


granted_by_talent(
    id=801,
    tab=feral_combat_281_tab,
    tier=3,
    column=2,
    ranks=[37116, 37117],
    player_castable=False,
    depends_on={'talent_id': 798, 'rank': 2},
)


granted_by_talent(
    id=802,
    tab=feral_combat_281_tab,
    tier=3,
    column=0,
    ranks=[shredding_attacks_16966, shredding_attacks_16968],
    player_castable=False,
)


granted_by_talent(
    id=803,
    tab=feral_combat_281_tab,
    tier=3,
    column=1,
    ranks=[predatory_strikes_16972, predatory_strikes_16974, predatory_strikes_16975],
    player_castable=False,
)


granted_by_talent(
    id=804,
    tab=feral_combat_281_tab,
    tier=4,
    column=2,
    ranks=[49377],
    player_castable=False,
)


granted_by_talent(
    id=805,
    tab=feral_combat_281_tab,
    tier=1,
    column=1,
    ranks=[savage_fury_16998, savage_fury_16999],
    player_castable=False,
)


granted_by_talent(
    id=807,
    tab=feral_combat_281_tab,
    tier=2,
    column=0,
    ranks=[feral_swiftness_17002, feral_swiftness_24866],
    player_castable=False,
)


granted_by_talent(
    id=808,
    tab=feral_combat_281_tab,
    tier=5,
    column=1,
    ranks=[17003, 17004, 17005, 17006, 24894],
    player_castable=False,
    depends_on={'talent_id': 803, 'rank': 2},
)


granted_by_talent(
    id=809,
    tab=feral_combat_281_tab,
    tier=6,
    column=1,
    ranks=[leader_of_the_pack_17007],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=821,
    tab=restoration_282_tab,
    tier=0,
    column=0,
    ranks=[improved_mark_of_the_wild_17050, improved_mark_of_the_wild_17051],
    player_castable=False,
)


granted_by_talent(
    id=822,
    tab=restoration_282_tab,
    tier=0,
    column=2,
    ranks=[furor_17056, furor_17058, furor_17059, furor_17060, furor_17061],
    player_castable=False,
)


granted_by_talent(
    id=823,
    tab=restoration_282_tab,
    tier=0,
    column=1,
    ranks=[nature_s_focus_17063, nature_s_focus_17065, nature_s_focus_17066],
    player_castable=False,
)


granted_by_talent(
    id=824,
    tab=restoration_282_tab,
    tier=1,
    column=0,
    ranks=[naturalist_17069, naturalist_17070, naturalist_17071, naturalist_17072, naturalist_17073],
    player_castable=False,
)


granted_by_talent(
    id=825,
    tab=restoration_282_tab,
    tier=5,
    column=2,
    ranks=[nature_s_bounty_17074, nature_s_bounty_17075, nature_s_bounty_17076, nature_s_bounty_17077, nature_s_bounty_17078],
    player_castable=False,
    depends_on={'talent_id': 830, 'rank': 2},
)


granted_by_talent(
    id=826,
    tab=restoration_282_tab,
    tier=1,
    column=2,
    ranks=[natural_shapeshifter_16833, natural_shapeshifter_16834, natural_shapeshifter_16835],
    player_castable=False,
)


granted_by_talent(
    id=827,
    tab=restoration_282_tab,
    tier=2,
    column=1,
    ranks=[omen_of_clarity_16864],
    player_castable=False,
)


granted_by_talent(
    id=828,
    tab=restoration_282_tab,
    tier=4,
    column=1,
    ranks=[gift_of_nature_17104, gift_of_nature_24943, gift_of_nature_24944, gift_of_nature_24945, gift_of_nature_24946],
    player_castable=False,
)


granted_by_talent(
    id=829,
    tab=restoration_282_tab,
    tier=2,
    column=0,
    ranks=[intensity_17106, intensity_17107, intensity_17108],
    player_castable=False,
)


granted_by_talent(
    id=830,
    tab=restoration_282_tab,
    tier=3,
    column=2,
    ranks=[improved_rejuvenation_17111, improved_rejuvenation_17112, improved_rejuvenation_17113],
    player_castable=False,
)


granted_by_talent(
    id=831,
    tab=restoration_282_tab,
    tier=4,
    column=0,
    ranks=[nature_s_swiftness_17116],
    player_castable=False,
    depends_on={'talent_id': 829, 'rank': 2},
    flags=1,
)


granted_by_talent(
    id=841,
    tab=restoration_282_tab,
    tier=1,
    column=1,
    ranks=[subtlety_17118, subtlety_17119, subtlety_17120],
    player_castable=False,
)


granted_by_talent(
    id=842,
    tab=restoration_282_tab,
    tier=4,
    column=3,
    ranks=[improved_tranquility_17123, improved_tranquility_17124],
    player_castable=False,
)


granted_by_talent(
    id=843,
    tab=restoration_282_tab,
    tier=3,
    column=1,
    ranks=[tranquil_spirit_24968, tranquil_spirit_24969, tranquil_spirit_24970, tranquil_spirit_24971, tranquil_spirit_24972],
    player_castable=False,
)


granted_by_talent(
    id=844,
    tab=restoration_282_tab,
    tier=6,
    column=1,
    ranks=[swiftmend_18562],
    player_castable=False,
    depends_on={'talent_id': 828, 'rank': 4},
    flags=1,
)


granted_by_talent(
    id=1162,
    tab=feral_combat_281_tab,
    tier=2,
    column=1,
    ranks=[survival_instincts_61336],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1782,
    tab=balance_283_tab,
    tier=4,
    column=0,
    ranks=[lunar_guidance_33589, lunar_guidance_33590, lunar_guidance_33591],
    player_castable=False,
)


granted_by_talent(
    id=1783,
    tab=balance_283_tab,
    tier=5,
    column=2,
    ranks=[balance_of_power_33592, balance_of_power_33596],
    player_castable=False,
)


granted_by_talent(
    id=1784,
    tab=balance_283_tab,
    tier=5,
    column=0,
    ranks=[dreamstate_33597, dreamstate_33599, dreamstate_33956],
    player_castable=False,
)


granted_by_talent(
    id=1785,
    tab=balance_283_tab,
    tier=6,
    column=3,
    ranks=[improved_faerie_fire_33600, improved_faerie_fire_33601, improved_faerie_fire_33602],
    player_castable=False,
)


granted_by_talent(
    id=1786,
    tab=balance_283_tab,
    tier=7,
    column=2,
    ranks=[wrath_of_cenarius_33603, wrath_of_cenarius_33604, wrath_of_cenarius_33605, wrath_of_cenarius_33606, wrath_of_cenarius_33607],
    player_castable=False,
)


granted_by_talent(
    id=1787,
    tab=balance_283_tab,
    tier=8,
    column=2,
    ranks=[force_of_nature_33831],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1788,
    tab=restoration_282_tab,
    tier=5,
    column=0,
    ranks=[empowered_touch_33879, empowered_touch_33880],
    player_castable=False,
)


granted_by_talent(
    id=1789,
    tab=restoration_282_tab,
    tier=7,
    column=1,
    ranks=[empowered_rejuvenation_33886, empowered_rejuvenation_33887, empowered_rejuvenation_33888, empowered_rejuvenation_33889, empowered_rejuvenation_33890],
    player_castable=False,
)


granted_by_talent(
    id=1790,
    tab=restoration_282_tab,
    tier=6,
    column=2,
    ranks=[natural_perfection_33881, natural_perfection_33882, natural_perfection_33883],
    player_castable=False,
)


granted_by_talent(
    id=1791,
    tab=restoration_282_tab,
    tier=8,
    column=1,
    ranks=[65139],
    player_castable=False,
    depends_on={'talent_id': 1789, 'rank': 4},
    flags=1,
)


granted_by_talent(
    id=1792,
    tab=feral_combat_281_tab,
    tier=4,
    column=3,
    ranks=[nurturing_instinct_33872, nurturing_instinct_33873],
    player_castable=False,
)


granted_by_talent(
    id=1793,
    tab=feral_combat_281_tab,
    tier=6,
    column=3,
    ranks=[primal_tenacity_33851, primal_tenacity_33852, primal_tenacity_33957],
    player_castable=False,
)


granted_by_talent(
    id=1794,
    tab=feral_combat_281_tab,
    tier=5,
    column=2,
    ranks=[survival_of_the_fittest_33853, survival_of_the_fittest_33855, survival_of_the_fittest_33856],
    player_castable=False,
)


granted_by_talent(
    id=1795,
    tab=feral_combat_281_tab,
    tier=7,
    column=2,
    ranks=[predatory_instincts_33859, predatory_instincts_33866, predatory_instincts_33867],
    player_castable=False,
)


granted_by_talent(
    id=1796,
    tab=feral_combat_281_tab,
    tier=8,
    column=1,
    ranks=[33917],
    player_castable=False,
    depends_on={'talent_id': 809, 'rank': 0},
)


granted_by_talent(
    id=1797,
    tab=restoration_282_tab,
    tier=6,
    column=0,
    ranks=[living_spirit_34151, living_spirit_34152, living_spirit_34153],
    player_castable=False,
)


granted_by_talent(
    id=1798,
    tab=feral_combat_281_tab,
    tier=6,
    column=2,
    ranks=[improved_leader_of_the_pack_34297, improved_leader_of_the_pack_34300],
    player_castable=False,
    depends_on={'talent_id': 809, 'rank': 0},
)


granted_by_talent(
    id=1822,
    tab=balance_283_tab,
    tier=1,
    column=1,
    ranks=[nature_s_majesty_35363, nature_s_majesty_35364],
    player_castable=False,
)


granted_by_talent(
    id=1912,
    tab=balance_283_tab,
    tier=6,
    column=2,
    ranks=[improved_moonkin_form_48384, improved_moonkin_form_48395, improved_moonkin_form_48396],
    player_castable=False,
    depends_on={'talent_id': 793, 'rank': 0},
)


granted_by_talent(
    id=1913,
    tab=balance_283_tab,
    tier=7,
    column=0,
    ranks=[48389, 48392, 48393],
    player_castable=False,
    depends_on={'talent_id': 793, 'rank': 0},
)


granted_by_talent(
    id=1914,
    tab=feral_combat_281_tab,
    tier=3,
    column=3,
    ranks=[primal_precision_48409, primal_precision_48410],
    player_castable=False,
    depends_on={'talent_id': 798, 'rank': 2},
)


granted_by_talent(
    id=1915,
    tab=restoration_282_tab,
    tier=2,
    column=2,
    ranks=[48411, 48412],
    player_castable=False,
    depends_on={'talent_id': 826, 'rank': 2},
)


granted_by_talent(
    id=1916,
    tab=restoration_282_tab,
    tier=9,
    column=2,
    ranks=[gift_of_the_earthmother_51179, gift_of_the_earthmother_51180, gift_of_the_earthmother_51181, gift_of_the_earthmother_51182, gift_of_the_earthmother_51183],
    player_castable=False,
)


granted_by_talent(
    id=1917,
    tab=restoration_282_tab,
    tier=10,
    column=1,
    ranks=[wild_growth_48438],
    player_castable=False,
    depends_on={'talent_id': 1791, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=1918,
    tab=feral_combat_281_tab,
    tier=9,
    column=1,
    ranks=[rend_and_tear_48432, rend_and_tear_48433, rend_and_tear_48434, rend_and_tear_51268, rend_and_tear_51269],
    player_castable=False,
)


granted_by_talent(
    id=1919,
    tab=feral_combat_281_tab,
    tier=7,
    column=3,
    ranks=[infected_wounds_48483, infected_wounds_48484, infected_wounds_48485],
    player_castable=False,
)


granted_by_talent(
    id=1920,
    tab=feral_combat_281_tab,
    tier=8,
    column=2,
    ranks=[improved_mangle_48532, improved_mangle_48489, improved_mangle_48491],
    player_castable=False,
    depends_on={'talent_id': 1796, 'rank': 0},
)


granted_by_talent(
    id=1921,
    tab=feral_combat_281_tab,
    tier=8,
    column=0,
    ranks=[king_of_the_jungle_48492, king_of_the_jungle_48494, king_of_the_jungle_48495],
    player_castable=False,
)


granted_by_talent(
    id=1922,
    tab=restoration_282_tab,
    tier=7,
    column=2,
    ranks=[living_seed_48496, living_seed_48499, living_seed_48500],
    player_castable=False,
)


granted_by_talent(
    id=1923,
    tab=balance_283_tab,
    tier=8,
    column=1,
    ranks=[typhoon_50516],
    player_castable=False,
    depends_on={'talent_id': 793, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=1924,
    tab=balance_283_tab,
    tier=8,
    column=0,
    ranks=[eclipse_48516, eclipse_48521, eclipse_48525],
    player_castable=False,
)


granted_by_talent(
    id=1925,
    tab=balance_283_tab,
    tier=8,
    column=3,
    ranks=[gale_winds_48488, gale_winds_48514],
    player_castable=False,
)


granted_by_talent(
    id=1926,
    tab=balance_283_tab,
    tier=10,
    column=1,
    ranks=[starfall_48505],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1927,
    tab=feral_combat_281_tab,
    tier=10,
    column=1,
    ranks=[berserk_50334],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1928,
    tab=balance_283_tab,
    tier=9,
    column=1,
    ranks=[earth_and_moon_48506, earth_and_moon_48510, earth_and_moon_48511],
    player_castable=False,
)


granted_by_talent(
    id=1929,
    tab=restoration_282_tab,
    tier=8,
    column=0,
    ranks=[revitalize_48539, revitalize_48544, revitalize_48545],
    player_castable=False,
)


granted_by_talent(
    id=1930,
    tab=restoration_282_tab,
    tier=8,
    column=2,
    ranks=[improved_tree_of_life_48535, improved_tree_of_life_48536, improved_tree_of_life_48537],
    player_castable=False,
    depends_on={'talent_id': 1791, 'rank': 0},
)


granted_by_talent(
    id=2238,
    tab=balance_283_tab,
    tier=0,
    column=2,
    ranks=[genesis_57810, genesis_57811, genesis_57812, genesis_57813, genesis_57814],
    player_castable=False,
)


granted_by_talent(
    id=2239,
    tab=balance_283_tab,
    tier=4,
    column=2,
    ranks=[improved_insect_swarm_57849, improved_insect_swarm_57850, improved_insect_swarm_57851],
    player_castable=False,
    depends_on={'talent_id': 788, 'rank': 0},
)


granted_by_talent(
    id=2240,
    tab=balance_283_tab,
    tier=2,
    column=2,
    ranks=[nature_s_splendor_57865],
    player_castable=False,
    depends_on={'talent_id': 1822, 'rank': 1},
)


granted_by_talent(
    id=2241,
    tab=feral_combat_281_tab,
    tier=7,
    column=0,
    ranks=[protector_of_the_pack_57873, protector_of_the_pack_57876, protector_of_the_pack_57877],
    player_castable=False,
    depends_on={'talent_id': 809, 'rank': 0},
)


granted_by_talent(
    id=2242,
    tab=feral_combat_281_tab,
    tier=5,
    column=0,
    ranks=[natural_reaction_57878, natural_reaction_57880, natural_reaction_57881],
    player_castable=False,
)


granted_by_talent(
    id=2264,
    tab=restoration_282_tab,
    tier=9,
    column=0,
    ranks=[improved_barkskin_63410, improved_barkskin_63411],
    player_castable=False,
)


granted_by_talent(
    id=2266,
    tab=feral_combat_281_tab,
    tier=9,
    column=2,
    ranks=[primal_gore_63503],
    player_castable=False,
    depends_on={'talent_id': 1918, 'rank': 4},
)
