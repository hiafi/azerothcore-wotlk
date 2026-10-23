"""
Shaman - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/shaman.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .shaman_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, retire_talent, tab
from .shaman_restoration import cloudburst_totem_202652, spirit_link_totem_202645, tidal_force_castable_202654, undulating_currents_totem_202647
from .shaman_spells import elemental_mastery_16166, mana_tide_totem_16190, riptide_61295, thunderstorm_51490
from .shaman_trigger_spells import ancestral_awakening_51556, ancestral_awakening_51557, ancestral_awakening_51558, ancestral_healing_16176, ancestral_healing_16235, ancestral_healing_16240, astral_shift_51474, astral_shift_51478, blessing_of_the_eternals_51554, blessing_of_the_eternals_51555, booming_echoes_63370, booming_echoes_63372, call_of_flame_16038, call_of_flame_16160, call_of_flame_16161, call_of_thunder_16041, concussion_16035, concussion_16105, concussion_16106, convection_16039, convection_16109, convection_16110, elemental_devastation_29179, elemental_devastation_29180, elemental_devastation_30160, elemental_focus_16164, elemental_fury_16089, elemental_fury_60184, elemental_fury_60185, elemental_oath_51466, elemental_oath_51470, elemental_precision_30672, elemental_precision_30673, elemental_precision_30674, elemental_reach_28999, elemental_reach_29000, elemental_warding_28996, elemental_warding_28997, elemental_warding_28998, eye_of_the_storm_29062, eye_of_the_storm_29064, eye_of_the_storm_29065, focused_mind_30864, focused_mind_30865, earthen_bulwark_16181, healing_grace_29187, healing_grace_29189, healing_grace_29191, healing_way_29202, healing_way_29205, healing_way_29206, improved_chain_heal_30872, improved_chain_heal_30873, improved_earth_shield_51560, improved_earth_shield_51561, improved_fire_nova_16086, improved_fire_nova_16544, improved_healing_wave_16182, improved_healing_wave_16226, improved_healing_wave_16227, improved_reincarnation_16184, improved_reincarnation_16209, improved_water_shield_16180, improved_water_shield_16196, improved_water_shield_16198, lava_flows_51480, lava_flows_51481, lava_flows_51482, lightning_mastery_16578, lightning_mastery_16579, lightning_mastery_16580, lightning_overload_30675, lightning_overload_30678, lightning_overload_30679, nature_s_blessing_30867, nature_s_blessing_30868, nature_s_blessing_30869, nature_s_guardian_30881, nature_s_guardian_30883, purification_16178, purification_16210, purification_16211, restorative_totems_16187, restorative_totems_16205, restorative_totems_16206, reverberation_16040, reverberation_16113, reverberation_16114, shamanism_62097, shamanism_62098, shamanism_62099, storm_earth_and_fire_51483, storm_earth_and_fire_51485, storm_earth_and_fire_51486, tidal_focus_16179, tidal_focus_16214, tidal_focus_16215, tidal_mastery_16194, tidal_mastery_16218, tidal_mastery_16219, tidal_waves_51562, tidal_waves_51563, tidal_waves_51564, totemic_focus_16173, totemic_focus_16222, totemic_focus_16223, unrelenting_storm_30664, unrelenting_storm_30665, unrelenting_storm_30666


elemental_261_tab = tab(
    id=261,
    name='Elemental',
    class_mask=64,
    spell_icon_id=62,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'ShamanElementalCombat'},
)


restoration_262_tab = tab(
    id=262,
    name='Restoration',
    class_mask=64,
    order_index=2,
    spell_icon_id=13,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'ShamanRestoration'},
)


enhancement_263_tab = tab(
    id=263,
    name='Enhancement',
    class_mask=64,
    order_index=1,
    spell_icon_id=19,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'ShamanEnhancement'},
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
    column=2,
    ranks=[call_of_thunder_16041, 202533, 202534],
    player_castable=False,
)


granted_by_talent(
    id=563,
    tab=elemental_261_tab,
    tier=0,
    column=2,
    ranks=[concussion_16035, concussion_16105, concussion_16106],
    player_castable=False,
)


granted_by_talent(
    id=564,
    tab=elemental_261_tab,
    tier=0,
    column=1,
    ranks=[convection_16039, convection_16109, convection_16110],
    player_castable=False,
)


granted_by_talent(
    id=565,
    tab=elemental_261_tab,
    tier=2,
    column=2,
    ranks=[elemental_fury_16089, elemental_fury_60184, elemental_fury_60185],
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
    flags=1,
)


granted_by_talent(
    id=574,
    tab=elemental_261_tab,
    tier=2,
    column=3,
    ranks=[elemental_focus_16164, 202532],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=575,
    tab=elemental_261_tab,
    tier=2,
    column=0,
    ranks=[reverberation_16040, reverberation_16113, reverberation_16114],
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
    tier=3,
    column=1,
    ranks=[tidal_force_castable_202654],
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
    ranks=[improved_healing_wave_16182, improved_healing_wave_16226, improved_healing_wave_16227],
    player_castable=False,
)


granted_by_talent(
    id=587,
    tab=restoration_262_tab,
    tier=2,
    column=1,
    ranks=[earthen_bulwark_16181],
    player_castable=False,
)


granted_by_talent(
    id=588,
    tab=restoration_262_tab,
    tier=6,
    column=3,
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
    tier=5,
    column=1,
    ranks=[mana_tide_totem_16190],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=592,
    tab=restoration_262_tab,
    tier=5,
    column=2,
    ranks=[purification_16178, purification_16210, purification_16211],
    player_castable=False,
)


granted_by_talent(
    id=593,
    tab=restoration_262_tab,
    tier=1,
    column=2,
    ranks=[tidal_focus_16179, tidal_focus_16214, tidal_focus_16215],
    player_castable=False,
)


granted_by_talent(
    id=594,
    tab=restoration_262_tab,
    tier=3,
    column=2,
    ranks=[tidal_mastery_16194, tidal_mastery_16218, tidal_mastery_16219],
    player_castable=False,
)


granted_by_talent(
    id=595,
    tab=restoration_262_tab,
    tier=0,
    column=2,
    ranks=[totemic_focus_16173, totemic_focus_16222, totemic_focus_16223],
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
    ranks=[16256, 16281, 16282],
    player_castable=False,
)


granted_by_talent(
    id=605,
    tab=enhancement_263_tab,
    tier=1,
    column=2,
    ranks=[16262, 16287],
    player_castable=False,
)


granted_by_talent(
    id=607,
    tab=enhancement_263_tab,
    tier=1,
    column=3,
    ranks=[16261, 16290, 51881],
    player_castable=False,
)


granted_by_talent(
    id=609,
    tab=enhancement_263_tab,
    tier=1,
    column=0,
    ranks=[16258, 16293],
    player_castable=False,
)


granted_by_talent(
    id=610,
    tab=enhancement_263_tab,
    tier=0,
    column=0,
    ranks=[16259, 16295, 52456],
    player_castable=False,
)


granted_by_talent(
    id=611,
    tab=enhancement_263_tab,
    tier=2,
    column=0,
    ranks=[16266, 29079, 29080],
    player_castable=False,
)


granted_by_talent(
    id=613,
    tab=enhancement_263_tab,
    tier=2,
    column=1,
    ranks=[16255, 16302, 16303],
    player_castable=False,
)


granted_by_talent(
    id=614,
    tab=enhancement_263_tab,
    tier=0,
    column=2,
    ranks=[17485, 17486, 17487],
    player_castable=False,
)


granted_by_talent(
    id=615,
    tab=enhancement_263_tab,
    tier=3,
    column=2,
    ranks=[16252, 16306, 16307],
    player_castable=False,
)


granted_by_talent(
    id=616,
    tab=enhancement_263_tab,
    tier=5,
    column=1,
    ranks=[16268, 202373, 202374],
    player_castable=False,
)


granted_by_talent(
    id=617,
    tab=enhancement_263_tab,
    tier=2,
    column=2,
    ranks=[43338, 202371, 202372],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=721,
    tab=elemental_261_tab,
    tier=5,
    column=2,
    ranks=[lightning_mastery_16578, lightning_mastery_16579, lightning_mastery_16580],
    player_castable=False,
)


granted_by_talent(
    id=901,
    tab=enhancement_263_tab,
    tier=6,
    column=2,
    ranks=[17364],
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
    tier=3,
    column=0,
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
    ranks=[29192, 29193],
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
    id=1689,
    tab=enhancement_263_tab,
    tier=5,
    column=0,
    ranks=[30802, 30808, 30809],
    player_castable=False,
)


granted_by_talent(
    id=1691,
    tab=enhancement_263_tab,
    tier=8,
    column=0,
    ranks=[30812, 30813, 30814],
    player_castable=False,
)


granted_by_talent(
    id=1692,
    tab=enhancement_263_tab,
    tier=6,
    column=0,
    ranks=[30816, 30818, 30819],
    player_castable=False,
)


granted_by_talent(
    id=1693,
    tab=enhancement_263_tab,
    tier=8,
    column=1,
    ranks=[30823],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1695,
    tab=restoration_262_tab,
    tier=4,
    column=3,
    ranks=[focused_mind_30864, focused_mind_30865],
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
    column=3,
    ranks=[improved_chain_heal_30872, improved_chain_heal_30873],
    player_castable=False,
)


granted_by_talent(
    id=1699,
    tab=restoration_262_tab,
    tier=6,
    column=0,
    ranks=[nature_s_guardian_30881, nature_s_guardian_30883],
    player_castable=False,
)


granted_by_talent(
    id=2049,
    tab=elemental_261_tab,
    tier=7,
    column=3,
    ranks=[elemental_oath_51466, elemental_oath_51470, 202536],
    player_castable=False,
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
    tier=2,
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
    ranks=[51521, 51522],
    player_castable=False,
)


granted_by_talent(
    id=2055,
    tab=enhancement_263_tab,
    tier=7,
    column=0,
    ranks=[51525, 51526, 51527],
    player_castable=False,
)


granted_by_talent(
    id=2056,
    tab=enhancement_263_tab,
    tier=8,
    column=2,
    ranks=[51523, 51524],
    player_castable=False,
)


granted_by_talent(
    id=2057,
    tab=enhancement_263_tab,
    tier=9,
    column=1,
    ranks=[51528, 51529, 51530],
    player_castable=False,
)


granted_by_talent(
    id=2058,
    tab=enhancement_263_tab,
    tier=10,
    column=1,
    ranks=[51533],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2059,
    tab=restoration_262_tab,
    tier=8,
    column=2,
    ranks=[improved_earth_shield_51560, improved_earth_shield_51561, 202653],
    player_castable=False,
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
    ranks=[tidal_waves_51562, tidal_waves_51563, tidal_waves_51564],
    player_castable=False,
)


granted_by_talent(
    id=2064,
    tab=restoration_262_tab,
    tier=4,
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
    ranks=[51883, 51884, 51885],
    player_castable=False,
)


granted_by_talent(
    id=2101,
    tab=enhancement_263_tab,
    tier=0,
    column=1,
    ranks=[16043, 16130],
    player_castable=False,
)


granted_by_talent(
    id=2249,
    tab=enhancement_263_tab,
    tier=4,
    column=1,
    ranks=[60103],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2252,
    tab=elemental_261_tab,
    tier=9,
    column=1,
    ranks=[shamanism_62097, shamanism_62098, shamanism_62099],
    player_castable=False,
)


granted_by_talent(
    id=2262,
    tab=elemental_261_tab,
    tier=7,
    column=0,
    ranks=[booming_echoes_63370, booming_echoes_63372, 202535],
    player_castable=False,
)


granted_by_talent(
    id=2263,
    tab=enhancement_263_tab,
    tier=5,
    column=3,
    ranks=[63373, 63374, 202375],
    player_castable=False,
)


# S1a: the seven new Elemental talents (Ele talent block 60280-60294; rank spells 202520-202531 are declared in
# shaman_elemental.py and referenced here by bare id: a bare int is always accepted as a rank and avoids an import
# cycle). Call of the Elements' single rank IS the castable (202531): player_castable=False because its
# SkillLineAbility (30690) is a standalone skill_line_ability() row in shaman_elemental.py (shaman tabs carry no
# skill_line). Single-rank rows carry flags=1 like every other single-point talent.
granted_by_talent(
    id=60280,
    tab=elemental_261_tab,
    tier=0,
    column=0,
    ranks=[202520, 202521, 202522],
    player_castable=False,
)


granted_by_talent(
    id=60281,
    tab=elemental_261_tab,
    tier=0,
    column=3,
    ranks=[202523, 202524, 202525],
    player_castable=False,
)


granted_by_talent(
    id=60282,
    tab=elemental_261_tab,
    tier=4,
    column=1,
    ranks=[202526],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=60283,
    tab=elemental_261_tab,
    tier=7,
    column=1,
    ranks=[202527],
    player_castable=False,
    flags=1,
)


# Icefury mints a new talent row; stock 1687 (Totem of Wrath) stays retired below.
granted_by_talent(
    id=60284,
    tab=elemental_261_tab,
    tier=8,
    column=1,
    ranks=[202528],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=60285,
    tab=elemental_261_tab,
    tier=8,
    column=3,
    ranks=[202529, 202530],
    player_castable=False,
)


granted_by_talent(
    id=60286,
    tab=elemental_261_tab,
    tier=10,
    column=1,
    ranks=[202531],
    player_castable=False,
    flags=1,
)


# S2a: Restoration grid (doc section 4). Reused stock rows keep their ids; these eight are new.
granted_by_talent(
    id=60310,
    tab=restoration_262_tab,
    tier=0,
    column=0,
    ranks=[202640, 202641, 202642],
    player_castable=False,
)


granted_by_talent(
    id=60311,
    tab=restoration_262_tab,
    tier=5,
    column=0,
    ranks=[202643, 202644],
    player_castable=False,
)


granted_by_talent(
    id=60312,
    tab=restoration_262_tab,
    tier=6,
    column=1,
    ranks=[spirit_link_totem_202645],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=60313,
    tab=restoration_262_tab,
    tier=7,
    column=1,
    ranks=[202646],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=60314,
    tab=restoration_262_tab,
    tier=8,
    column=1,
    ranks=[undulating_currents_totem_202647],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=60315,
    tab=restoration_262_tab,
    tier=8,
    column=3,
    ranks=[202648, 202649],
    player_castable=False,
)


granted_by_talent(
    id=60316,
    tab=restoration_262_tab,
    tier=9,
    column=2,
    ranks=[202650, 202651],
    player_castable=False,
)


granted_by_talent(
    id=60317,
    tab=restoration_262_tab,
    tier=10,
    column=1,
    ranks=[cloudburst_totem_202652],
    player_castable=False,
    flags=1,
)


# S3a: the six new Enhancement talents (Enh talent block 60295-60309; rank spells 202360-202370 are declared in
# shaman_enhancement.py and referenced by bare id, as in S1a). Living Earth's single rank IS the castable (202361):
# player_castable=False because its SkillLineAbility (30680) is a standalone skill_line_ability() row in
# shaman_enhancement.py (CotE precedent). Elemental Charge, Volcanic Eruption, Ascendance, Molten Fury and Spirit
# Guard ranks are passive markers/carriers. No talent on tab 263 carries depends_on (doc Q19).

granted_by_talent(
    id=60295,
    tab=enhancement_263_tab,
    tier=1,
    column=1,
    ranks=[202360],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=60296,
    tab=enhancement_263_tab,
    tier=4,
    column=3,
    ranks=[202361],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=60297,
    tab=enhancement_263_tab,
    tier=5,
    column=2,
    ranks=[202362, 202363],
    player_castable=False,
)


granted_by_talent(
    id=60298,
    tab=enhancement_263_tab,
    tier=6,
    column=1,
    ranks=[202364],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=60299,
    tab=enhancement_263_tab,
    tier=6,
    column=3,
    ranks=[202365, 202366, 202367],
    player_castable=False,
)


granted_by_talent(
    id=60300,
    tab=enhancement_263_tab,
    tier=7,
    column=1,
    ranks=[202368, 202369, 202370],
    player_castable=False,
)


# SH0a (H6): stock rows whose spells become trained at trainer 210; the rows move to the holding tab.
# S2a: 591 Nature's Swiftness leaves the Restoration tree (cell 4,2 must stay empty).
for _retired in (1687, 1690, 1698, 2084, 591):
    retire_talent(_retired)
