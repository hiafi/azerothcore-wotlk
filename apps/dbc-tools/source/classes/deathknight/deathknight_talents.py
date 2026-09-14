"""
Deathknight - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/deathknight.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .deathknight_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, tab
from .deathknight_spells import anti_magic_zone_51052, bone_shield_49222, corpse_explosion_49158, dancing_rune_weapon_49028, deathchill_49796, frost_strike_49143, ghoul_frenzy_63560, howling_blast_49184, hungering_cold_49203, hysteria_49016, lichborne_49039, mark_of_blood_49005, rune_tap_48982, summon_gargoyle_49206, unbreakable_armor_51271, vampiric_blood_55233
from .deathknight_trigger_spells import abomination_s_might_53137, abomination_s_might_53138, acclimation_49200, acclimation_50151, acclimation_50152, annihilation_51468, annihilation_51472, annihilation_51473, black_ice_49140, black_ice_49661, black_ice_49662, black_ice_49663, black_ice_49664, blade_barrier_49182, blade_barrier_49500, blade_barrier_49501, blade_barrier_55225, blade_barrier_55226, bladed_armor_48978, bladed_armor_49390, bladed_armor_49391, bladed_armor_49392, bladed_armor_49393, blood_caked_blade_49219, blood_caked_blade_49627, blood_caked_blade_49628, blood_gorged_61154, blood_gorged_61155, blood_gorged_61156, blood_gorged_61157, blood_gorged_61158, blood_of_the_north_54637, blood_of_the_north_54638, blood_of_the_north_54639, bloodworms_49027, bloodworms_49542, bloodworms_49543, bloody_strikes_48977, bloody_strikes_49394, bloody_strikes_49395, butchery_48979, butchery_49483, chilblains_50040, chilblains_50041, chilblains_50043, chill_of_the_grave_49149, chill_of_the_grave_50115, crypt_fever_49032, crypt_fever_49631, crypt_fever_49632, death_rune_mastery_49467, death_rune_mastery_50033, death_rune_mastery_50034, desecration_55666, desecration_55667, desolation_66799, desolation_66814, desolation_66815, desolation_66816, desolation_66817, dirge_49223, dirge_49599, ebon_plaguebringer_51099, ebon_plaguebringer_51160, ebon_plaguebringer_51161, endless_winter_49137, endless_winter_49657, epidemic_49036, epidemic_49562, frigid_dreadplate_49186, frigid_dreadplate_51108, frigid_dreadplate_51109, glacier_rot_49471, glacier_rot_49790, glacier_rot_49791, guile_of_gorefiend_50187, guile_of_gorefiend_50190, guile_of_gorefiend_50191, heart_strike_55050, icy_reach_55061, icy_reach_55062, icy_talons_50880, icy_talons_50884, icy_talons_50885, icy_talons_50886, icy_talons_50887, improved_blood_presence_50365, improved_blood_presence_50371, improved_death_strike_62905, improved_death_strike_62908, improved_frost_presence_50384, improved_frost_presence_50385, improved_icy_talons_55610, improved_icy_touch_49175, improved_icy_touch_50031, improved_icy_touch_51456, improved_rune_tap_48985, improved_rune_tap_49488, improved_rune_tap_49489, improved_unholy_presence_50391, improved_unholy_presence_50392, killing_machine_51123, killing_machine_51127, killing_machine_51128, killing_machine_51129, killing_machine_51130, magic_suppression_49224, magic_suppression_49610, magic_suppression_49611, master_of_ghouls_52143, merciless_combat_49024, merciless_combat_49538, might_of_mograine_49023, might_of_mograine_49533, might_of_mograine_49534, morbidity_48963, morbidity_49564, morbidity_49565, necrosis_51459, necrosis_51462, necrosis_51463, necrosis_51464, necrosis_51465, night_of_the_dead_55620, night_of_the_dead_55623, on_a_pale_horse_49146, on_a_pale_horse_51267, outbreak_49013, outbreak_55236, outbreak_55237, rage_of_rivendare_50117, rage_of_rivendare_50118, rage_of_rivendare_50119, rage_of_rivendare_50120, rage_of_rivendare_50121, ravenous_dead_48965, ravenous_dead_49571, ravenous_dead_49572, reaping_49208, reaping_56834, reaping_56835, rime_49188, rime_56822, rime_59057, runic_power_mastery_49455, runic_power_mastery_50147, scourge_strike_55090, subversion_48997, subversion_49490, subversion_49491, sudden_doom_49018, sudden_doom_49529, sudden_doom_49530, threat_of_thassarian_65661, threat_of_thassarian_66191, threat_of_thassarian_66192, tundra_stalker_49202, tundra_stalker_50127, tundra_stalker_50128, tundra_stalker_50129, tundra_stalker_50130, unholy_blight_49194, unholy_command_49588, unholy_command_49589, vendetta_49015, vendetta_50154, vendetta_55136, vicious_strikes_51745, vicious_strikes_51746, virulence_48962, virulence_49567, virulence_49568, wandering_plague_49217, wandering_plague_49654, wandering_plague_49655, will_of_the_necropolis_49189, will_of_the_necropolis_50149, will_of_the_necropolis_50150


blood_398_tab = tab(
    id=398,
    name='Blood',
    class_mask=32,
    spell_icon_id=2636,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 4294707199, 'BackgroundFile': 231},
)


frost_399_tab = tab(
    id=399,
    name='Frost',
    class_mask=32,
    order_index=1,
    spell_icon_id=2632,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 543},
)


unholy_400_tab = tab(
    id=400,
    name='Unholy',
    class_mask=32,
    order_index=2,
    spell_icon_id=2633,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 766},
)


granted_by_talent(
    id=1932,
    tab=unholy_400_tab,
    tier=0,
    column=1,
    ranks=[virulence_48962, virulence_49567, virulence_49568],
    player_castable=False,
)


granted_by_talent(
    id=1933,
    tab=unholy_400_tab,
    tier=1,
    column=1,
    ranks=[morbidity_48963, morbidity_49564, morbidity_49565],
    player_castable=False,
)


granted_by_talent(
    id=1934,
    tab=unholy_400_tab,
    tier=1,
    column=3,
    ranks=[ravenous_dead_48965, ravenous_dead_49571, ravenous_dead_49572],
    player_castable=False,
)


granted_by_talent(
    id=1936,
    tab=blood_398_tab,
    tier=6,
    column=2,
    ranks=[improved_blood_presence_50365, improved_blood_presence_50371],
    player_castable=False,
)


granted_by_talent(
    id=1938,
    tab=blood_398_tab,
    tier=1,
    column=0,
    ranks=[bladed_armor_48978, bladed_armor_49390, bladed_armor_49391, bladed_armor_49392, bladed_armor_49393],
    player_castable=False,
)


granted_by_talent(
    id=1939,
    tab=blood_398_tab,
    tier=0,
    column=0,
    ranks=[butchery_48979, butchery_49483],
    player_castable=False,
)


granted_by_talent(
    id=1941,
    tab=blood_398_tab,
    tier=2,
    column=0,
    ranks=[rune_tap_48982],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1942,
    tab=blood_398_tab,
    tier=3,
    column=0,
    ranks=[improved_rune_tap_48985, improved_rune_tap_49488, improved_rune_tap_49489],
    player_castable=False,
    depends_on={'talent_id': 1941, 'rank': 0},
)


granted_by_talent(
    id=1943,
    tab=blood_398_tab,
    tier=2,
    column=1,
    ranks=[48987, 49477, 49478, 49479, 49480],
    player_castable=False,
)


granted_by_talent(
    id=1944,
    tab=blood_398_tab,
    tier=5,
    column=1,
    ranks=[48988, 49503, 49504],
    player_castable=False,
    depends_on={'talent_id': 1943, 'rank': 4},
)


granted_by_talent(
    id=1945,
    tab=blood_398_tab,
    tier=0,
    column=1,
    ranks=[subversion_48997, subversion_49490, subversion_49491],
    player_castable=False,
)


granted_by_talent(
    id=1948,
    tab=blood_398_tab,
    tier=1,
    column=1,
    ranks=[49004, 49508, 49509],
    player_castable=False,
)


granted_by_talent(
    id=1949,
    tab=blood_398_tab,
    tier=4,
    column=3,
    ranks=[mark_of_blood_49005],
    player_castable=False,
    depends_on={'talent_id': 0, 'rank': 1},
    flags=1,
)


granted_by_talent(
    id=1950,
    tab=blood_398_tab,
    tier=4,
    column=2,
    ranks=[49006, 49526, 50029],
    player_castable=False,
)


granted_by_talent(
    id=1953,
    tab=blood_398_tab,
    tier=3,
    column=3,
    ranks=[vendetta_49015, vendetta_50154, vendetta_55136],
    player_castable=False,
)


granted_by_talent(
    id=1954,
    tab=blood_398_tab,
    tier=6,
    column=1,
    ranks=[hysteria_49016],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1955,
    tab=blood_398_tab,
    tier=7,
    column=1,
    ranks=[sudden_doom_49018, sudden_doom_49529, sudden_doom_49530],
    player_castable=False,
)


granted_by_talent(
    id=1957,
    tab=blood_398_tab,
    tier=8,
    column=1,
    ranks=[heart_strike_55050],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1958,
    tab=blood_398_tab,
    tier=8,
    column=2,
    ranks=[might_of_mograine_49023, might_of_mograine_49533, might_of_mograine_49534],
    player_castable=False,
)


granted_by_talent(
    id=1959,
    tab=blood_398_tab,
    tier=8,
    column=0,
    ranks=[will_of_the_necropolis_49189, will_of_the_necropolis_50149, will_of_the_necropolis_50150],
    player_castable=False,
)


granted_by_talent(
    id=1960,
    tab=blood_398_tab,
    tier=6,
    column=0,
    ranks=[bloodworms_49027, bloodworms_49542, bloodworms_49543],
    player_castable=False,
)


granted_by_talent(
    id=1961,
    tab=blood_398_tab,
    tier=10,
    column=1,
    ranks=[dancing_rune_weapon_49028],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1962,
    tab=unholy_400_tab,
    tier=7,
    column=1,
    ranks=[crypt_fever_49032, crypt_fever_49631, crypt_fever_49632],
    player_castable=False,
)


granted_by_talent(
    id=1963,
    tab=unholy_400_tab,
    tier=1,
    column=0,
    ranks=[epidemic_49036, epidemic_49562],
    player_castable=False,
)


granted_by_talent(
    id=1968,
    tab=frost_399_tab,
    tier=0,
    column=2,
    ranks=[49042, 49786, 49787, 49788, 49789],
    player_castable=False,
)


granted_by_talent(
    id=1971,
    tab=frost_399_tab,
    tier=3,
    column=3,
    ranks=[endless_winter_49137, endless_winter_49657],
    player_castable=False,
)


granted_by_talent(
    id=1973,
    tab=frost_399_tab,
    tier=1,
    column=2,
    ranks=[black_ice_49140, black_ice_49661, black_ice_49662, black_ice_49663, black_ice_49664],
    player_castable=False,
)


granted_by_talent(
    id=1975,
    tab=frost_399_tab,
    tier=8,
    column=1,
    ranks=[frost_strike_49143],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1979,
    tab=frost_399_tab,
    tier=7,
    column=2,
    ranks=[unbreakable_armor_51271],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1980,
    tab=frost_399_tab,
    tier=4,
    column=3,
    ranks=[deathchill_49796],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1981,
    tab=frost_399_tab,
    tier=3,
    column=2,
    ranks=[chill_of_the_grave_49149, chill_of_the_grave_50115],
    player_castable=False,
)


granted_by_talent(
    id=1984,
    tab=unholy_400_tab,
    tier=5,
    column=3,
    ranks=[master_of_ghouls_52143],
    player_castable=False,
    depends_on={'talent_id': 2225, 'rank': 1},
)


granted_by_talent(
    id=1985,
    tab=unholy_400_tab,
    tier=2,
    column=2,
    ranks=[corpse_explosion_49158],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1989,
    tab=frost_399_tab,
    tier=10,
    column=1,
    ranks=[howling_blast_49184],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1990,
    tab=frost_399_tab,
    tier=4,
    column=1,
    ranks=[frigid_dreadplate_49186, frigid_dreadplate_51108, frigid_dreadplate_51109],
    player_castable=False,
)


granted_by_talent(
    id=1992,
    tab=frost_399_tab,
    tier=5,
    column=2,
    ranks=[rime_49188, rime_56822, rime_59057],
    player_castable=False,
)


granted_by_talent(
    id=1993,
    tab=frost_399_tab,
    tier=5,
    column=1,
    ranks=[merciless_combat_49024, merciless_combat_49538],
    player_castable=False,
    depends_on={'talent_id': 1994, 'rank': 0},
)


granted_by_talent(
    id=1996,
    tab=unholy_400_tab,
    tier=4,
    column=0,
    ranks=[unholy_blight_49194],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1997,
    tab=frost_399_tab,
    tier=8,
    column=0,
    ranks=[acclimation_49200, acclimation_50151, acclimation_50152],
    player_castable=False,
)


granted_by_talent(
    id=1998,
    tab=frost_399_tab,
    tier=9,
    column=1,
    ranks=[tundra_stalker_49202, tundra_stalker_50127, tundra_stalker_50128, tundra_stalker_50129, tundra_stalker_50130],
    player_castable=False,
)


granted_by_talent(
    id=1999,
    tab=frost_399_tab,
    tier=6,
    column=1,
    ranks=[hungering_cold_49203],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2000,
    tab=unholy_400_tab,
    tier=10,
    column=1,
    ranks=[summon_gargoyle_49206],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2001,
    tab=unholy_400_tab,
    tier=5,
    column=2,
    ranks=[reaping_49208, reaping_56834, reaping_56835],
    player_castable=False,
)


granted_by_talent(
    id=2003,
    tab=unholy_400_tab,
    tier=8,
    column=0,
    ranks=[wandering_plague_49217, wandering_plague_49654, wandering_plague_49655],
    player_castable=False,
)


granted_by_talent(
    id=2004,
    tab=unholy_400_tab,
    tier=3,
    column=2,
    ranks=[blood_caked_blade_49219, blood_caked_blade_49627, blood_caked_blade_49628],
    player_castable=False,
)


granted_by_talent(
    id=2005,
    tab=unholy_400_tab,
    tier=4,
    column=1,
    ranks=[49220, 49633, 49635, 49636, 49638],
    player_castable=False,
)


granted_by_talent(
    id=2007,
    tab=unholy_400_tab,
    tier=7,
    column=2,
    ranks=[bone_shield_49222],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2008,
    tab=unholy_400_tab,
    tier=2,
    column=0,
    ranks=[outbreak_49013, outbreak_55236, outbreak_55237],
    player_castable=False,
)


granted_by_talent(
    id=2009,
    tab=unholy_400_tab,
    tier=5,
    column=1,
    ranks=[magic_suppression_49224, magic_suppression_49610, magic_suppression_49611],
    player_castable=False,
)


granted_by_talent(
    id=2011,
    tab=unholy_400_tab,
    tier=4,
    column=2,
    ranks=[dirge_49223, dirge_49599],
    player_castable=False,
)


granted_by_talent(
    id=2013,
    tab=unholy_400_tab,
    tier=6,
    column=2,
    ranks=[improved_unholy_presence_50391, improved_unholy_presence_50392],
    player_castable=False,
)


granted_by_talent(
    id=2015,
    tab=blood_398_tab,
    tier=4,
    column=0,
    ranks=[bloody_strikes_48977, bloody_strikes_49394, bloody_strikes_49395],
    player_castable=False,
)


granted_by_talent(
    id=2017,
    tab=blood_398_tab,
    tier=0,
    column=2,
    ranks=[blade_barrier_49182, blade_barrier_49500, blade_barrier_49501, blade_barrier_55225, blade_barrier_55226],
    player_castable=False,
)


granted_by_talent(
    id=2018,
    tab=blood_398_tab,
    tier=3,
    column=2,
    ranks=[49145, 49495, 49497],
    player_castable=False,
)


granted_by_talent(
    id=2019,
    tab=blood_398_tab,
    tier=7,
    column=2,
    ranks=[vampiric_blood_55233],
    player_castable=False,
    depends_on={'talent_id': 0, 'rank': 4},
    flags=1,
)


granted_by_talent(
    id=2020,
    tab=frost_399_tab,
    tier=0,
    column=1,
    ranks=[runic_power_mastery_49455, runic_power_mastery_50147],
    player_castable=False,
)


granted_by_talent(
    id=2022,
    tab=frost_399_tab,
    tier=1,
    column=3,
    ranks=[49226, 50137, 50138],
    player_castable=False,
)


granted_by_talent(
    id=2025,
    tab=unholy_400_tab,
    tier=1,
    column=2,
    ranks=[unholy_command_49588, unholy_command_49589],
    player_castable=False,
)


granted_by_talent(
    id=2029,
    tab=frost_399_tab,
    tier=6,
    column=2,
    ranks=[improved_frost_presence_50384, improved_frost_presence_50385],
    player_castable=False,
)


granted_by_talent(
    id=2030,
    tab=frost_399_tab,
    tier=4,
    column=2,
    ranks=[glacier_rot_49471, glacier_rot_49790, glacier_rot_49791],
    player_castable=False,
)


granted_by_talent(
    id=2031,
    tab=frost_399_tab,
    tier=0,
    column=0,
    ranks=[improved_icy_touch_49175, improved_icy_touch_50031, improved_icy_touch_51456],
    player_castable=False,
)


granted_by_talent(
    id=2034,
    tab=blood_398_tab,
    tier=9,
    column=1,
    ranks=[blood_gorged_61154, blood_gorged_61155, blood_gorged_61156, blood_gorged_61157, blood_gorged_61158],
    player_castable=False,
)


granted_by_talent(
    id=2035,
    tab=frost_399_tab,
    tier=1,
    column=1,
    ranks=[icy_reach_55061, icy_reach_55062],
    player_castable=False,
)


granted_by_talent(
    id=2036,
    tab=unholy_400_tab,
    tier=9,
    column=1,
    ranks=[rage_of_rivendare_50117, rage_of_rivendare_50118, rage_of_rivendare_50119, rage_of_rivendare_50120, rage_of_rivendare_50121],
    player_castable=False,
)


granted_by_talent(
    id=2039,
    tab=unholy_400_tab,
    tier=3,
    column=1,
    ranks=[on_a_pale_horse_49146, on_a_pale_horse_51267],
    player_castable=False,
)


granted_by_talent(
    id=2040,
    tab=frost_399_tab,
    tier=8,
    column=2,
    ranks=[guile_of_gorefiend_50187, guile_of_gorefiend_50190, guile_of_gorefiend_50191],
    player_castable=False,
)


granted_by_talent(
    id=2042,
    tab=frost_399_tab,
    tier=2,
    column=0,
    ranks=[icy_talons_50880, icy_talons_50884, icy_talons_50885, icy_talons_50886, icy_talons_50887],
    player_castable=False,
    depends_on={'talent_id': 2031, 'rank': 2},
)


granted_by_talent(
    id=2043,
    tab=unholy_400_tab,
    tier=8,
    column=1,
    ranks=[ebon_plaguebringer_51099, ebon_plaguebringer_51160, ebon_plaguebringer_51161],
    player_castable=False,
    depends_on={'talent_id': 1962, 'rank': 2},
)


granted_by_talent(
    id=2044,
    tab=frost_399_tab,
    tier=3,
    column=1,
    ranks=[killing_machine_51123, killing_machine_51127, killing_machine_51128, killing_machine_51129, killing_machine_51130],
    player_castable=False,
)


granted_by_talent(
    id=2047,
    tab=unholy_400_tab,
    tier=2,
    column=1,
    ranks=[necrosis_51459, necrosis_51462, necrosis_51463, necrosis_51464, necrosis_51465],
    player_castable=False,
)


granted_by_talent(
    id=2048,
    tab=frost_399_tab,
    tier=2,
    column=2,
    ranks=[annihilation_51468, annihilation_51472, annihilation_51473],
    player_castable=False,
)


granted_by_talent(
    id=2082,
    tab=unholy_400_tab,
    tier=0,
    column=0,
    ranks=[vicious_strikes_51745, vicious_strikes_51746],
    player_castable=False,
)


granted_by_talent(
    id=2085,
    tab=unholy_400_tab,
    tier=6,
    column=3,
    ranks=[ghoul_frenzy_63560],
    player_castable=False,
    depends_on={'talent_id': 1984, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=2086,
    tab=blood_398_tab,
    tier=2,
    column=2,
    ranks=[death_rune_mastery_49467, death_rune_mastery_50033, death_rune_mastery_50034],
    player_castable=False,
)


granted_by_talent(
    id=2105,
    tab=blood_398_tab,
    tier=5,
    column=2,
    ranks=[abomination_s_might_53137, abomination_s_might_53138],
    player_castable=False,
)


granted_by_talent(
    id=2210,
    tab=frost_399_tab,
    tier=7,
    column=1,
    ranks=[blood_of_the_north_54639, blood_of_the_north_54638, blood_of_the_north_54637],
    player_castable=False,
)


granted_by_talent(
    id=2215,
    tab=frost_399_tab,
    tier=2,
    column=1,
    ranks=[lichborne_49039],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2216,
    tab=unholy_400_tab,
    tier=8,
    column=2,
    ranks=[scourge_strike_55090],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2217,
    tab=blood_398_tab,
    tier=1,
    column=2,
    ranks=[55107, 55108],
    player_castable=False,
)


granted_by_talent(
    id=2218,
    tab=unholy_400_tab,
    tier=0,
    column=2,
    ranks=[55129, 55130, 55131, 55132, 55133],
    player_castable=False,
)


granted_by_talent(
    id=2221,
    tab=unholy_400_tab,
    tier=6,
    column=1,
    ranks=[anti_magic_zone_51052],
    player_castable=False,
    depends_on={'talent_id': 2009, 'rank': 2},
    flags=1,
)


granted_by_talent(
    id=2223,
    tab=frost_399_tab,
    tier=5,
    column=0,
    ranks=[improved_icy_talons_55610],
    player_castable=False,
    depends_on={'talent_id': 2042, 'rank': 4},
)


granted_by_talent(
    id=2225,
    tab=unholy_400_tab,
    tier=3,
    column=3,
    ranks=[night_of_the_dead_55620, night_of_the_dead_55623],
    player_castable=False,
)


granted_by_talent(
    id=2226,
    tab=unholy_400_tab,
    tier=5,
    column=0,
    ranks=[desecration_55666, desecration_55667],
    player_castable=False,
)


granted_by_talent(
    id=2259,
    tab=blood_398_tab,
    tier=7,
    column=0,
    ranks=[improved_death_strike_62905, improved_death_strike_62908],
    player_castable=False,
)


granted_by_talent(
    id=2260,
    tab=frost_399_tab,
    tier=6,
    column=0,
    ranks=[chilblains_50040, chilblains_50041, chilblains_50043],
    player_castable=False,
)


granted_by_talent(
    id=2284,
    tab=frost_399_tab,
    tier=7,
    column=0,
    ranks=[threat_of_thassarian_65661, threat_of_thassarian_66191, threat_of_thassarian_66192],
    player_castable=False,
)


granted_by_talent(
    id=2285,
    tab=unholy_400_tab,
    tier=6,
    column=0,
    ranks=[desolation_66799, desolation_66814, desolation_66815, desolation_66816, desolation_66817],
    player_castable=False,
)
