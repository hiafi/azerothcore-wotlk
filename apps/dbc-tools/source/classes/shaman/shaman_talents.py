"""
Shaman - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/shaman.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .shaman_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, tab
from .shaman_spells import cleanse_spirit_51886, earth_shield_974, elemental_mastery_16166, feral_spirit_51533, lava_lash_60103, mana_tide_totem_16190, nature_s_swiftness_16188, riptide_61295, shamanistic_rage_30823, stormstrike_17364, thunderstorm_51490, tidal_force_55198, totem_of_wrath_30706
from .shaman_trigger_spells import ancestral_awakening_51556, ancestral_awakening_51557, ancestral_awakening_51558, ancestral_healing_16176, ancestral_healing_16235, ancestral_healing_16240, astral_shift_51474, astral_shift_51478, blessing_of_the_eternals_51554, blessing_of_the_eternals_51555, booming_echoes_63370, booming_echoes_63372, call_of_flame_16038, call_of_flame_16160, call_of_flame_16161, call_of_thunder_16041, concussion_16035, concussion_16105, concussion_16106, concussion_16107, concussion_16108, convection_16039, convection_16109, convection_16110, convection_16111, convection_16112, earth_s_grasp_16043, earth_s_grasp_16130, earthen_power_51523, earthen_power_51524, elemental_devastation_29179, elemental_devastation_29180, elemental_devastation_30160, elemental_focus_16164, elemental_fury_16089, elemental_fury_60184, elemental_fury_60185, elemental_fury_60187, elemental_fury_60188, elemental_oath_51466, elemental_oath_51470, elemental_precision_30672, elemental_precision_30673, elemental_precision_30674, elemental_reach_28999, elemental_reach_29000, elemental_warding_28996, elemental_warding_28997, elemental_warding_28998, elemental_weapons_16266, elemental_weapons_29079, elemental_weapons_29080, enhancing_totems_16259, enhancing_totems_16295, enhancing_totems_52456, eye_of_the_storm_29062, eye_of_the_storm_29064, eye_of_the_storm_29065, focused_mind_30864, focused_mind_30865, focused_mind_30866, frozen_power_63373, frozen_power_63374, guardian_totems_16258, guardian_totems_16293, healing_focus_16181, healing_focus_16230, healing_focus_16232, healing_grace_29187, healing_grace_29189, healing_grace_29191, healing_way_29202, healing_way_29205, healing_way_29206, improved_chain_heal_30872, improved_chain_heal_30873, improved_earth_shield_51560, improved_earth_shield_51561, improved_fire_nova_16086, improved_fire_nova_16544, improved_ghost_wolf_16262, improved_ghost_wolf_16287, improved_healing_wave_16182, improved_healing_wave_16226, improved_healing_wave_16227, improved_healing_wave_16228, improved_healing_wave_16229, improved_reincarnation_16184, improved_reincarnation_16209, improved_shields_16261, improved_shields_16290, improved_shields_51881, improved_stormstrike_51521, improved_stormstrike_51522, improved_water_shield_16180, improved_water_shield_16196, improved_water_shield_16198, improved_windfury_totem_29192, improved_windfury_totem_29193, lava_flows_51480, lava_flows_51481, lava_flows_51482, lightning_mastery_16578, lightning_mastery_16579, lightning_mastery_16580, lightning_mastery_16581, lightning_mastery_16582, lightning_overload_30675, lightning_overload_30678, lightning_overload_30679, maelstrom_weapon_51528, maelstrom_weapon_51529, maelstrom_weapon_51530, maelstrom_weapon_51531, maelstrom_weapon_51532, mental_dexterity_51883, mental_dexterity_51884, mental_dexterity_51885, mental_quickness_30812, mental_quickness_30813, mental_quickness_30814, nature_s_blessing_30867, nature_s_blessing_30868, nature_s_blessing_30869, nature_s_guardian_30881, nature_s_guardian_30883, nature_s_guardian_30884, nature_s_guardian_30885, nature_s_guardian_30886, purification_16178, purification_16210, purification_16211, purification_16212, purification_16213, restorative_totems_16187, restorative_totems_16205, restorative_totems_16206, reverberation_16040, reverberation_16113, reverberation_16114, reverberation_16115, reverberation_16116, shamanism_62097, shamanism_62098, shamanism_62099, shamanism_62100, shamanism_62101, shamanistic_focus_43338, static_shock_51525, static_shock_51526, static_shock_51527, storm_earth_and_fire_51483, storm_earth_and_fire_51485, storm_earth_and_fire_51486, tidal_focus_16179, tidal_focus_16214, tidal_focus_16215, tidal_focus_16216, tidal_focus_16217, tidal_mastery_16194, tidal_mastery_16218, tidal_mastery_16219, tidal_mastery_16220, tidal_mastery_16221, tidal_waves_51562, tidal_waves_51563, tidal_waves_51564, tidal_waves_51565, tidal_waves_51566, totemic_focus_16173, totemic_focus_16222, totemic_focus_16223, totemic_focus_16224, totemic_focus_16225, unrelenting_storm_30664, unrelenting_storm_30665, unrelenting_storm_30666


elemental_261_tab = tab(
    id=261,
    name='Elemental',
    class_mask=64,
    spell_icon_id=62,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 107},
)


restoration_262_tab = tab(
    id=262,
    name='Restoration',
    class_mask=64,
    order_index=2,
    spell_icon_id=13,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 643},
)


enhancement_263_tab = tab(
    id=263,
    name='Enhancement',
    class_mask=64,
    order_index=1,
    spell_icon_id=19,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 400},
)


granted_by_talent(
    id=561,
    tab=elemental_261_tab,
    tier=1,
    column=0,
    ranks=[call_of_flame_16038, call_of_flame_16160, call_of_flame_16161],
    player_castable=False,
)


granted_by_talent(
    id=562,
    tab=elemental_261_tab,
    tier=4,
    column=1,
    ranks=[call_of_thunder_16041],
    player_castable=False,
    depends_on={'talent_id': 574, 'rank': 0},
)


granted_by_talent(
    id=563,
    tab=elemental_261_tab,
    tier=0,
    column=2,
    ranks=[concussion_16035, concussion_16105, concussion_16106, concussion_16107, concussion_16108],
    player_castable=False,
)


granted_by_talent(
    id=564,
    tab=elemental_261_tab,
    tier=0,
    column=1,
    ranks=[convection_16039, convection_16109, convection_16110, convection_16111, convection_16112],
    player_castable=False,
)


granted_by_talent(
    id=565,
    tab=elemental_261_tab,
    tier=2,
    column=2,
    ranks=[elemental_fury_16089, elemental_fury_60184, elemental_fury_60185, elemental_fury_60187, elemental_fury_60188],
    player_castable=False,
)


granted_by_talent(
    id=567,
    tab=elemental_261_tab,
    tier=3,
    column=0,
    ranks=[improved_fire_nova_16086, improved_fire_nova_16544],
    player_castable=False,
)


granted_by_talent(
    id=573,
    tab=elemental_261_tab,
    tier=6,
    column=1,
    ranks=[elemental_mastery_16166],
    player_castable=False,
    depends_on={'talent_id': 562, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=574,
    tab=elemental_261_tab,
    tier=2,
    column=1,
    ranks=[elemental_focus_16164],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=575,
    tab=elemental_261_tab,
    tier=2,
    column=0,
    ranks=[reverberation_16040, reverberation_16113, reverberation_16114, reverberation_16115, reverberation_16116],
    player_castable=False,
)


granted_by_talent(
    id=581,
    tab=restoration_262_tab,
    tier=2,
    column=3,
    ranks=[ancestral_healing_16176, ancestral_healing_16235, ancestral_healing_16240],
    player_castable=False,
)


granted_by_talent(
    id=582,
    tab=restoration_262_tab,
    tier=2,
    column=2,
    ranks=[tidal_force_55198],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=583,
    tab=restoration_262_tab,
    tier=2,
    column=0,
    ranks=[improved_water_shield_16180, improved_water_shield_16196, improved_water_shield_16198],
    player_castable=False,
)


granted_by_talent(
    id=586,
    tab=restoration_262_tab,
    tier=0,
    column=1,
    ranks=[improved_healing_wave_16182, improved_healing_wave_16226, improved_healing_wave_16227, improved_healing_wave_16228, improved_healing_wave_16229],
    player_castable=False,
)


granted_by_talent(
    id=587,
    tab=restoration_262_tab,
    tier=2,
    column=1,
    ranks=[healing_focus_16181, healing_focus_16230, healing_focus_16232],
    player_castable=False,
)


granted_by_talent(
    id=588,
    tab=restoration_262_tab,
    tier=3,
    column=1,
    ranks=[restorative_totems_16187, restorative_totems_16205, restorative_totems_16206],
    player_castable=False,
)


granted_by_talent(
    id=589,
    tab=restoration_262_tab,
    tier=1,
    column=0,
    ranks=[improved_reincarnation_16184, improved_reincarnation_16209],
    player_castable=False,
)


granted_by_talent(
    id=590,
    tab=restoration_262_tab,
    tier=6,
    column=1,
    ranks=[mana_tide_totem_16190],
    player_castable=False,
    depends_on={'talent_id': 588, 'rank': 2},
    flags=1,
)


granted_by_talent(
    id=591,
    tab=restoration_262_tab,
    tier=4,
    column=2,
    ranks=[nature_s_swiftness_16188],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=592,
    tab=restoration_262_tab,
    tier=5,
    column=2,
    ranks=[purification_16178, purification_16210, purification_16211, purification_16212, purification_16213],
    player_castable=False,
)


granted_by_talent(
    id=593,
    tab=restoration_262_tab,
    tier=1,
    column=2,
    ranks=[tidal_focus_16179, tidal_focus_16214, tidal_focus_16215, tidal_focus_16216, tidal_focus_16217],
    player_castable=False,
)


granted_by_talent(
    id=594,
    tab=restoration_262_tab,
    tier=3,
    column=2,
    ranks=[tidal_mastery_16194, tidal_mastery_16218, tidal_mastery_16219, tidal_mastery_16220, tidal_mastery_16221],
    player_castable=False,
)


granted_by_talent(
    id=595,
    tab=restoration_262_tab,
    tier=0,
    column=2,
    ranks=[totemic_focus_16173, totemic_focus_16222, totemic_focus_16223, totemic_focus_16224, totemic_focus_16225],
    player_castable=False,
)


granted_by_talent(
    id=601,
    tab=enhancement_263_tab,
    tier=2,
    column=3,
    ranks=[16254, 16271, 16272],
    player_castable=False,
)


granted_by_talent(
    id=602,
    tab=enhancement_263_tab,
    tier=3,
    column=1,
    ranks=[16256, 16281, 16282, 16283, 16284],
    player_castable=False,
    depends_on={'talent_id': 613, 'rank': 4},
)


granted_by_talent(
    id=605,
    tab=enhancement_263_tab,
    tier=1,
    column=2,
    ranks=[improved_ghost_wolf_16262, improved_ghost_wolf_16287],
    player_castable=False,
)


granted_by_talent(
    id=607,
    tab=enhancement_263_tab,
    tier=1,
    column=3,
    ranks=[improved_shields_16261, improved_shields_16290, improved_shields_51881],
    player_castable=False,
)


granted_by_talent(
    id=609,
    tab=enhancement_263_tab,
    tier=1,
    column=0,
    ranks=[guardian_totems_16258, guardian_totems_16293],
    player_castable=False,
)


granted_by_talent(
    id=610,
    tab=enhancement_263_tab,
    tier=0,
    column=0,
    ranks=[enhancing_totems_16259, enhancing_totems_16295, enhancing_totems_52456],
    player_castable=False,
)


granted_by_talent(
    id=611,
    tab=enhancement_263_tab,
    tier=2,
    column=0,
    ranks=[elemental_weapons_16266, elemental_weapons_29079, elemental_weapons_29080],
    player_castable=False,
)


granted_by_talent(
    id=613,
    tab=enhancement_263_tab,
    tier=1,
    column=1,
    ranks=[16255, 16302, 16303, 16304, 16305],
    player_castable=False,
)


granted_by_talent(
    id=614,
    tab=enhancement_263_tab,
    tier=0,
    column=2,
    ranks=[17485, 17486, 17487, 17488, 17489],
    player_castable=False,
)


granted_by_talent(
    id=615,
    tab=enhancement_263_tab,
    tier=3,
    column=2,
    ranks=[16252, 16306, 16307, 16308, 16309],
    player_castable=False,
)


granted_by_talent(
    id=616,
    tab=enhancement_263_tab,
    tier=4,
    column=1,
    ranks=[16268],
    player_castable=False,
)


granted_by_talent(
    id=617,
    tab=enhancement_263_tab,
    tier=2,
    column=2,
    ranks=[shamanistic_focus_43338],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=721,
    tab=elemental_261_tab,
    tier=5,
    column=2,
    ranks=[lightning_mastery_16578, lightning_mastery_16579, lightning_mastery_16580, lightning_mastery_16581, lightning_mastery_16582],
    player_castable=False,
    depends_on={'talent_id': 565, 'rank': 4},
)


granted_by_talent(
    id=901,
    tab=enhancement_263_tab,
    tier=6,
    column=2,
    ranks=[stormstrike_17364],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1640,
    tab=elemental_261_tab,
    tier=1,
    column=1,
    ranks=[elemental_warding_28996, elemental_warding_28997, elemental_warding_28998],
    player_castable=False,
)


granted_by_talent(
    id=1641,
    tab=elemental_261_tab,
    tier=4,
    column=0,
    ranks=[elemental_reach_28999, elemental_reach_29000],
    player_castable=False,
)


granted_by_talent(
    id=1642,
    tab=elemental_261_tab,
    tier=3,
    column=3,
    ranks=[eye_of_the_storm_29062, eye_of_the_storm_29064, eye_of_the_storm_29065],
    player_castable=False,
)


granted_by_talent(
    id=1643,
    tab=enhancement_263_tab,
    tier=5,
    column=2,
    ranks=[29082, 29084, 29086],
    player_castable=False,
)


granted_by_talent(
    id=1645,
    tab=elemental_261_tab,
    tier=1,
    column=2,
    ranks=[elemental_devastation_30160, elemental_devastation_29179, elemental_devastation_29180],
    player_castable=False,
)


granted_by_talent(
    id=1646,
    tab=restoration_262_tab,
    tier=1,
    column=1,
    ranks=[healing_grace_29187, healing_grace_29189, healing_grace_29191],
    player_castable=False,
)


granted_by_talent(
    id=1647,
    tab=enhancement_263_tab,
    tier=4,
    column=0,
    ranks=[improved_windfury_totem_29192, improved_windfury_totem_29193],
    player_castable=False,
)


granted_by_talent(
    id=1648,
    tab=restoration_262_tab,
    tier=4,
    column=0,
    ranks=[healing_way_29206, healing_way_29205, healing_way_29202],
    player_castable=False,
)


granted_by_talent(
    id=1682,
    tab=elemental_261_tab,
    tier=4,
    column=3,
    ranks=[unrelenting_storm_30664, unrelenting_storm_30665, unrelenting_storm_30666],
    player_castable=False,
)


granted_by_talent(
    id=1685,
    tab=elemental_261_tab,
    tier=5,
    column=0,
    ranks=[elemental_precision_30672, elemental_precision_30673, elemental_precision_30674],
    player_castable=False,
)


granted_by_talent(
    id=1686,
    tab=elemental_261_tab,
    tier=7,
    column=2,
    ranks=[lightning_overload_30675, lightning_overload_30678, lightning_overload_30679],
    player_castable=False,
)


granted_by_talent(
    id=1687,
    tab=elemental_261_tab,
    tier=8,
    column=1,
    ranks=[totem_of_wrath_30706],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1689,
    tab=enhancement_263_tab,
    tier=5,
    column=0,
    ranks=[30802, 30808, 30809],
    player_castable=False,
)


granted_by_talent(
    id=1690,
    tab=enhancement_263_tab,
    tier=6,
    column=1,
    ranks=[30798],
    player_castable=False,
    depends_on={'talent_id': 616, 'rank': 0},
)


granted_by_talent(
    id=1691,
    tab=enhancement_263_tab,
    tier=8,
    column=0,
    ranks=[mental_quickness_30812, mental_quickness_30813, mental_quickness_30814],
    player_castable=False,
)


granted_by_talent(
    id=1692,
    tab=enhancement_263_tab,
    tier=6,
    column=0,
    ranks=[30816, 30818, 30819],
    player_castable=False,
    depends_on={'talent_id': 1690, 'rank': 0},
)


granted_by_talent(
    id=1693,
    tab=enhancement_263_tab,
    tier=8,
    column=1,
    ranks=[shamanistic_rage_30823],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1695,
    tab=restoration_262_tab,
    tier=4,
    column=3,
    ranks=[focused_mind_30864, focused_mind_30865, focused_mind_30866],
    player_castable=False,
)


granted_by_talent(
    id=1696,
    tab=restoration_262_tab,
    tier=7,
    column=2,
    ranks=[nature_s_blessing_30867, nature_s_blessing_30868, nature_s_blessing_30869],
    player_castable=False,
)


granted_by_talent(
    id=1697,
    tab=restoration_262_tab,
    tier=7,
    column=1,
    ranks=[improved_chain_heal_30872, improved_chain_heal_30873],
    player_castable=False,
)


granted_by_talent(
    id=1698,
    tab=restoration_262_tab,
    tier=8,
    column=1,
    ranks=[earth_shield_974],
    player_castable=False,
    depends_on={'talent_id': 0, 'rank': 2},
    flags=1,
)


granted_by_talent(
    id=1699,
    tab=restoration_262_tab,
    tier=6,
    column=0,
    ranks=[nature_s_guardian_30881, nature_s_guardian_30883, nature_s_guardian_30884, nature_s_guardian_30885, nature_s_guardian_30886],
    player_castable=False,
)


granted_by_talent(
    id=2049,
    tab=elemental_261_tab,
    tier=7,
    column=1,
    ranks=[elemental_oath_51466, elemental_oath_51470],
    player_castable=False,
    depends_on={'talent_id': 573, 'rank': 0},
)


granted_by_talent(
    id=2050,
    tab=elemental_261_tab,
    tier=8,
    column=0,
    ranks=[astral_shift_51474, astral_shift_51478, 51479],
    player_castable=False,
)


granted_by_talent(
    id=2051,
    tab=elemental_261_tab,
    tier=8,
    column=2,
    ranks=[lava_flows_51480, lava_flows_51481, lava_flows_51482],
    player_castable=False,
)


granted_by_talent(
    id=2052,
    tab=elemental_261_tab,
    tier=6,
    column=2,
    ranks=[storm_earth_and_fire_51483, storm_earth_and_fire_51485, storm_earth_and_fire_51486],
    player_castable=False,
)


granted_by_talent(
    id=2053,
    tab=elemental_261_tab,
    tier=10,
    column=1,
    ranks=[thunderstorm_51490],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2054,
    tab=enhancement_263_tab,
    tier=7,
    column=2,
    ranks=[improved_stormstrike_51521, improved_stormstrike_51522],
    player_castable=False,
    depends_on={'talent_id': 901, 'rank': 0},
)


granted_by_talent(
    id=2055,
    tab=enhancement_263_tab,
    tier=7,
    column=0,
    ranks=[static_shock_51525, static_shock_51526, static_shock_51527],
    player_castable=False,
)


granted_by_talent(
    id=2056,
    tab=enhancement_263_tab,
    tier=8,
    column=2,
    ranks=[earthen_power_51523, earthen_power_51524],
    player_castable=False,
)


granted_by_talent(
    id=2057,
    tab=enhancement_263_tab,
    tier=9,
    column=1,
    ranks=[maelstrom_weapon_51528, maelstrom_weapon_51529, maelstrom_weapon_51530, maelstrom_weapon_51531, maelstrom_weapon_51532],
    player_castable=False,
)


granted_by_talent(
    id=2058,
    tab=enhancement_263_tab,
    tier=10,
    column=1,
    ranks=[feral_spirit_51533],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2059,
    tab=restoration_262_tab,
    tier=8,
    column=2,
    ranks=[improved_earth_shield_51560, improved_earth_shield_51561],
    player_castable=False,
    depends_on={'talent_id': 1698, 'rank': 0},
)


granted_by_talent(
    id=2060,
    tab=restoration_262_tab,
    tier=7,
    column=0,
    ranks=[blessing_of_the_eternals_51554, blessing_of_the_eternals_51555],
    player_castable=False,
)


granted_by_talent(
    id=2061,
    tab=restoration_262_tab,
    tier=8,
    column=0,
    ranks=[ancestral_awakening_51556, ancestral_awakening_51557, ancestral_awakening_51558],
    player_castable=False,
)


granted_by_talent(
    id=2063,
    tab=restoration_262_tab,
    tier=9,
    column=1,
    ranks=[tidal_waves_51562, tidal_waves_51563, tidal_waves_51564, tidal_waves_51565, tidal_waves_51566],
    player_castable=False,
)


granted_by_talent(
    id=2064,
    tab=restoration_262_tab,
    tier=10,
    column=1,
    ranks=[riptide_61295],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2083,
    tab=enhancement_263_tab,
    tier=4,
    column=2,
    ranks=[mental_dexterity_51883, mental_dexterity_51884, mental_dexterity_51885],
    player_castable=False,
)


granted_by_talent(
    id=2084,
    tab=restoration_262_tab,
    tier=6,
    column=2,
    ranks=[cleanse_spirit_51886],
    player_castable=False,
    depends_on={'talent_id': 592, 'rank': 4},
    flags=1,
)


granted_by_talent(
    id=2101,
    tab=enhancement_263_tab,
    tier=0,
    column=1,
    ranks=[earth_s_grasp_16043, earth_s_grasp_16130],
    player_castable=False,
)


granted_by_talent(
    id=2249,
    tab=enhancement_263_tab,
    tier=7,
    column=1,
    ranks=[lava_lash_60103],
    player_castable=False,
    depends_on={'talent_id': 1690, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=2252,
    tab=elemental_261_tab,
    tier=9,
    column=1,
    ranks=[shamanism_62097, shamanism_62098, shamanism_62099, shamanism_62100, shamanism_62101],
    player_castable=False,
)


granted_by_talent(
    id=2262,
    tab=elemental_261_tab,
    tier=7,
    column=0,
    ranks=[booming_echoes_63370, booming_echoes_63372],
    player_castable=False,
)


granted_by_talent(
    id=2263,
    tab=enhancement_263_tab,
    tier=5,
    column=3,
    ranks=[frozen_power_63373, frozen_power_63374],
    player_castable=False,
)
