"""
Deathknight - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/deathknight.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .deathknight_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, retire_talent, tab, unbind_script
from .deathknight_spells import anti_magic_zone_51052, bone_shield_49222, corpse_explosion_49158, dancing_rune_weapon_49028, frost_strike_49143, ghoul_frenzy_63560, howling_blast_49184, hysteria_49016, lichborne_49039, mark_of_blood_49005, rune_tap_48982, summon_gargoyle_49206, unbreakable_armor_51271, vampiric_blood_55233
from .deathknight_trigger_spells import abomination_s_might_53137, abomination_s_might_53138, acclimation_49200, acclimation_50151, acclimation_50152, annihilation_51468, annihilation_51472, annihilation_51473, anticipation_55129, anticipation_55130, anticipation_55131, black_ice_49140, black_ice_49661, black_ice_49662, blade_barrier_49182, blade_barrier_49500, blade_barrier_49501, bladed_armor_48978, bladed_armor_49390, bladed_armor_49391, blood_caked_blade_49219, blood_caked_blade_49627, blood_caked_blade_49628, blood_gorged_61154, blood_gorged_61155, blood_gorged_61156, blood_of_the_north_54637, blood_of_the_north_54638, blood_of_the_north_54639, bloodworms_49027, bloodworms_49542, bloodworms_49543, bloody_strikes_48977, bloody_strikes_49394, bloody_strikes_49395, butchery_48979, butchery_49483, chilblains_50040, chilblains_50041, chilblains_50043, chill_of_the_grave_49149, chill_of_the_grave_50115, crypt_fever_49032, crypt_fever_49631, crypt_fever_49632, death_rune_mastery_49467, death_rune_mastery_50033, death_rune_mastery_50034, desecration_55666, desecration_55667, desolation_66799, desolation_66814, desolation_66815, dirge_49223, dirge_49599, ebon_plaguebringer_51099, ebon_plaguebringer_51160, ebon_plaguebringer_51161, endless_winter_49137, endless_winter_49657, epidemic_49036, epidemic_49562, frigid_dreadplate_49186, frigid_dreadplate_51108, frigid_dreadplate_51109, glacier_rot_49471, glacier_rot_49790, glacier_rot_49791, guile_of_gorefiend_50187, guile_of_gorefiend_50190, guile_of_gorefiend_50191, heart_strike_55050, icy_reach_55061, icy_reach_55062, icy_talons_50880, icy_talons_50884, icy_talons_50885, impurity_49220, impurity_49633, impurity_49635, improved_blood_presence_50365, improved_blood_presence_50371, improved_death_strike_62905, improved_death_strike_62908, improved_frost_presence_50384, improved_frost_presence_50385, improved_icy_touch_49175, improved_icy_touch_50031, improved_icy_touch_51456, improved_rune_tap_48985, improved_rune_tap_49488, improved_rune_tap_49489, improved_unholy_presence_50391, improved_unholy_presence_50392, killing_machine_51123, killing_machine_51127, killing_machine_51128, magic_suppression_49224, magic_suppression_49610, magic_suppression_49611, master_of_ghouls_52143, merciless_combat_49024, merciless_combat_49538, might_of_mograine_49023, might_of_mograine_49533, might_of_mograine_49534, morbidity_48963, morbidity_49564, morbidity_49565, necrosis_51459, necrosis_51462, necrosis_51463, night_of_the_dead_55620, night_of_the_dead_55623, on_a_pale_horse_49146, on_a_pale_horse_51267, outbreak_49013, outbreak_55236, outbreak_55237, rage_of_rivendare_50117, rage_of_rivendare_50118, rage_of_rivendare_50119, ravenous_dead_48965, ravenous_dead_49571, ravenous_dead_49572, reaping_49208, reaping_56834, reaping_56835, rime_49188, rime_56822, rime_59057, runic_power_mastery_49455, runic_power_mastery_50147, scourge_strike_55090, subversion_48997, subversion_49490, subversion_49491, sudden_doom_49018, sudden_doom_49529, sudden_doom_49530, threat_of_thassarian_65661, threat_of_thassarian_66191, threat_of_thassarian_66192, tundra_stalker_49202, tundra_stalker_50127, tundra_stalker_50128, unholy_blight_49194, unholy_command_49588, unholy_command_49589, toughness_49042, toughness_49786, toughness_49787, nerves_of_cold_steel_49226, nerves_of_cold_steel_50137, nerves_of_cold_steel_50138, vendetta_49015, vendetta_50154, vendetta_55136, vicious_strikes_51745, vicious_strikes_51746, virulence_48962, virulence_49567, virulence_49568, wandering_plague_49217, wandering_plague_49654, wandering_plague_49655, will_of_the_necropolis_49189, will_of_the_necropolis_50149, will_of_the_necropolis_50150

from .deathknight_unholy import (
    all_will_serve_203441, all_will_serve_203442, dark_transformation_203448, doomed_bidding_203445,
    doomed_bidding_203446, doomed_bidding_203447, festering_plague_203440, harbinger_of_doom_203453,
    harbinger_of_doom_203454, harbinger_of_doom_203455, infected_claws_203443, infected_claws_203444,
    raise_abomination_203452, rotten_touch_203449, rotten_touch_203450, rotten_touch_203451,
)
from .deathknight_frost import (
    breath_of_sindragosa_203306, enduring_strength_203297, enduring_strength_203298, final_roar_203289, final_roar_203290,
    frostwyrms_wrath_203302, frostwyrms_wrath_203303, glacial_advance_203273, gravefrost_203275, gravefrost_203276,
    gravefrost_203277, koltiras_favor_203278, koltiras_favor_203279, obliteration_203292, pillar_of_frost_203280,
    rage_of_the_frozen_champion_203294, rage_of_the_frozen_champion_203295, runic_attenuation_203270,
    runic_attenuation_203271, seal_of_necrofantasia_203299, seal_of_necrofantasia_203300, seal_of_necrofantasia_203301,
    toravons_whiteout_203285, toravons_whiteout_203286, toravons_whiteout_203287, unleashed_frenzy_203281,
    unleashed_frenzy_203282,
)
from .deathknight_frost_b import deathchill_203308, deathchill_203309, deathchill_203310, hungering_cold_passive_203314
from .deathknight_blood import (
    crimson_resolve_203120, crimson_resolve_203121, crimson_resolve_203122, crimson_scourge_203134, crimson_scourge_203135,
    crimson_scourge_203136, gorefiends_grasp_203127, marrowrend_203123, sanguine_ground_203129, sanguine_ground_203130,
    sanguine_ground_203131, thick_blood_203124, thick_blood_203125, thick_blood_203126,
)
from .deathknight_blood_b import (
    blood_nova_203143, bonestorm_203148, crimson_communion_203141, purgatory_203145, voracious_203138, voracious_203139,
)


blood_398_tab = tab(
    id=398,
    name='Blood',
    class_mask=32,
    spell_icon_id=2636,
    skill_line=770,  # S1a: derives the SkillLineAbility rows of the Blood castables (Marrowrend, ...); not a TalentTab.dbc column
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': -260097, 'BackgroundFile': 'DeathKnightBlood'},
)


frost_399_tab = tab(
    id=399,
    name='Frost',
    class_mask=32,
    order_index=1,
    spell_icon_id=2632,
    skill_line=771,  # S2a: derives the SkillLineAbility rows of the Frost castables (Glacial Advance, Pillar, Breath)
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'DeathKnightFrost'},
)


unholy_400_tab = tab(
    id=400,
    name='Unholy',
    class_mask=32,
    order_index=2,
    spell_icon_id=2633,
    skill_line=772,  # S3a: derives the SkillLineAbility rows of the Unholy castables (Dark Transformation, Raise Abomination)
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'DeathKnightUnholy'},
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
    column=2,
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
    id=1938,
    tab=blood_398_tab,
    tier=1,
    column=0,
    ranks=[bladed_armor_48978, bladed_armor_49390, bladed_armor_49391],
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
    id=1943,
    tab=blood_398_tab,
    tier=2,
    column=2,
    ranks=[48987, 49477, 49478],
    player_castable=False,
)


granted_by_talent(
    id=1944,
    tab=blood_398_tab,
    tier=5,
    column=1,
    ranks=[48988, 49503, 49504],
    player_castable=False,
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
    id=1955,
    tab=blood_398_tab,
    tier=7,
    column=1,
    ranks=[sudden_doom_49018, sudden_doom_49529, sudden_doom_49530],
    player_castable=False,
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
    tier=6,
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
    ranks=[toughness_49042, toughness_49786, toughness_49787],
    player_castable=False,
)


granted_by_talent(
    id=1971,
    tab=frost_399_tab,
    tier=3,
    column=2,
    ranks=[endless_winter_49137, endless_winter_49657],
    player_castable=False,
)


granted_by_talent(
    id=1973,
    tab=frost_399_tab,
    tier=1,
    column=2,
    ranks=[black_ice_49140, black_ice_49661, black_ice_49662],
    player_castable=False,
)




granted_by_talent(
    id=1980,
    tab=frost_399_tab,
    tier=4,
    column=0,
    ranks=[deathchill_203308, deathchill_203309, deathchill_203310],
    player_castable=False,
)


granted_by_talent(
    id=1981,
    tab=frost_399_tab,
    tier=3,
    column=3,
    ranks=[chill_of_the_grave_49149, chill_of_the_grave_50115],
    player_castable=False,
)


granted_by_talent(
    id=1984,
    tab=unholy_400_tab,
    tier=3,
    column=1,
    ranks=[master_of_ghouls_52143],
    player_castable=False,
)


granted_by_talent(
    id=1985,
    tab=unholy_400_tab,
    tier=4,
    column=3,
    ranks=[corpse_explosion_49158],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1989,
    tab=frost_399_tab,
    tier=2,
    column=1,
    ranks=[howling_blast_49184],
    player_castable=False,
    flags=1,
)



granted_by_talent(
    id=1992,
    tab=frost_399_tab,
    tier=3,
    column=1,
    ranks=[rime_49188, rime_56822, rime_59057],
    player_castable=False,
)


granted_by_talent(
    id=1993,
    tab=frost_399_tab,
    tier=5,
    column=2,
    ranks=[merciless_combat_49024, merciless_combat_49538],
    player_castable=False,
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
    column=2,
    ranks=[acclimation_49200, acclimation_50151, acclimation_50152],
    player_castable=False,
)


granted_by_talent(
    id=1998,
    tab=frost_399_tab,
    tier=9,
    column=2,
    ranks=[tundra_stalker_49202, tundra_stalker_50127, tundra_stalker_50128],
    player_castable=False,
)


granted_by_talent(
    id=1999,
    tab=frost_399_tab,
    tier=6,
    column=2,
    ranks=[hungering_cold_passive_203314],
    player_castable=False,
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
    column=0,
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
    ranks=[impurity_49220, impurity_49633, impurity_49635],
    player_castable=False,
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
    ranks=[blade_barrier_49182, blade_barrier_49500, blade_barrier_49501],
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
    tier=8,
    column=1,
    ranks=[vampiric_blood_55233],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2020,
    tab=frost_399_tab,
    tier=0,
    column=3,
    ranks=[runic_power_mastery_49455, runic_power_mastery_50147],
    player_castable=False,
)


granted_by_talent(
    id=2022,
    tab=frost_399_tab,
    tier=6,
    column=0,
    ranks=[nerves_of_cold_steel_49226, nerves_of_cold_steel_50137, nerves_of_cold_steel_50138],
    player_castable=False,
)


granted_by_talent(
    id=2025,
    tab=unholy_400_tab,
    tier=3,
    column=3,
    ranks=[unholy_command_49588, unholy_command_49589],
    player_castable=False,
)



granted_by_talent(
    id=2030,
    tab=frost_399_tab,
    tier=4,
    column=3,
    ranks=[glacier_rot_49471, glacier_rot_49790, glacier_rot_49791],
    player_castable=False,
)


granted_by_talent(
    id=2031,
    tab=frost_399_tab,
    tier=0,
    column=1,
    ranks=[improved_icy_touch_49175, improved_icy_touch_50031, improved_icy_touch_51456],
    player_castable=False,
)


granted_by_talent(
    id=2034,
    tab=blood_398_tab,
    tier=9,
    column=1,
    ranks=[blood_gorged_61154, blood_gorged_61155, blood_gorged_61156],
    player_castable=False,
)



granted_by_talent(
    id=2036,
    tab=unholy_400_tab,
    tier=6,
    column=1,
    ranks=[rage_of_rivendare_50117, rage_of_rivendare_50118, rage_of_rivendare_50119],
    player_castable=False,
)


granted_by_talent(
    id=2039,
    tab=unholy_400_tab,
    tier=3,
    column=0,
    ranks=[on_a_pale_horse_49146, on_a_pale_horse_51267],
    player_castable=False,
)


granted_by_talent(
    id=2040,
    tab=frost_399_tab,
    tier=8,
    column=0,
    ranks=[guile_of_gorefiend_50187, guile_of_gorefiend_50190, guile_of_gorefiend_50191],
    player_castable=False,
)


granted_by_talent(
    id=2042,
    tab=frost_399_tab,
    tier=2,
    column=0,
    ranks=[icy_talons_50880, icy_talons_50884, icy_talons_50885],
    player_castable=False,
)


granted_by_talent(
    id=2043,
    tab=unholy_400_tab,
    tier=9,
    column=1,
    ranks=[ebon_plaguebringer_51099, ebon_plaguebringer_51160, ebon_plaguebringer_51161],
    player_castable=False,
)


granted_by_talent(
    id=2044,
    tab=frost_399_tab,
    tier=3,
    column=0,
    ranks=[killing_machine_51123, killing_machine_51127, killing_machine_51128],
    player_castable=False,
)


granted_by_talent(
    id=2047,
    tab=unholy_400_tab,
    tier=2,
    column=2,
    ranks=[necrosis_51459, necrosis_51462, necrosis_51463],
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
    id=2216,
    tab=unholy_400_tab,
    tier=1,
    column=1,
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
    ranks=[anticipation_55129, anticipation_55130, anticipation_55131],
    player_castable=False,
)



granted_by_talent(
    id=2225,
    tab=unholy_400_tab,
    tier=5,
    column=3,
    ranks=[night_of_the_dead_55620, night_of_the_dead_55623],
    player_castable=False,
)


granted_by_talent(
    id=2226,
    tab=unholy_400_tab,
    tier=5,
    column=2,
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
    tier=1,
    column=1,
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
    tier=7,
    column=2,
    ranks=[desolation_66799, desolation_66814, desolation_66815],
    player_castable=False,
)


# DK0a (A5): the 16 cut talents move to the holding tab (their rank spells stay declared in the sibling files;
# the granted_by_talent blocks are gone so nothing re-links them). Known-hard 14.
for _retired in (1941, 2086, 1942, 1954, 1936, 1957, 2035, 2215, 1990, 2029, 1979, 1975, 2221, 2013, 2085, 2007):
    retire_talent(_retired)

# S2 Frost (user ruling 2026-10-25): Improved Icy Talons (2223, grid cell (5,0)) is removed as a talent; its party/raid melee
# haste (hidden passive 55610) is now the capstone of Icy Talons rank 3, linked in deathknight_trigger_spells.py. The cell stays
# empty and 2223's prerequisite on 2042 goes with the row (retire_talent zeroes PrereqTalent / PrereqRank / SpellRank).
retire_talent(2223)

# DK0a (A5): the three Improved Presence talents are cut, so their stock C++ bindings go (signed live keys:
# 0-verify item 4).
unbind_script(-50365, 'spell_dk_improved_blood_presence')
unbind_script(63611, 'spell_dk_improved_blood_presence_triggered')
unbind_script(-50384, 'spell_dk_improved_frost_presence')
unbind_script(-50391, 'spell_dk_improved_unholy_presence')


# S1a Blood: 11 new talents (ids 60330-60340, tab 398). Castables take a SkillLineAbility (30740-30744, skill 770 from the tab).


granted_by_talent(
    id=60330,
    tab=blood_398_tab,
    tier=0,
    column=3,
    ranks=[crimson_resolve_203120, crimson_resolve_203121, crimson_resolve_203122],
    player_castable=False,
)


granted_by_talent(
    id=60331,
    tab=blood_398_tab,
    tier=2,
    column=1,
    ranks=[marrowrend_203123],
    player_castable=True,
    skill_line_ability_ids=[30740],
    flags=1,
)


granted_by_talent(
    id=60332,
    tab=blood_398_tab,
    tier=3,
    column=0,
    ranks=[thick_blood_203124, thick_blood_203125, thick_blood_203126],
    player_castable=False,
)


granted_by_talent(
    id=60333,
    tab=blood_398_tab,
    tier=4,
    column=1,
    ranks=[gorefiends_grasp_203127],
    player_castable=True,
    skill_line_ability_ids=[30741],
    flags=1,
)


granted_by_talent(
    id=60334,
    tab=blood_398_tab,
    tier=5,
    column=0,
    ranks=[sanguine_ground_203129, sanguine_ground_203130, sanguine_ground_203131],
    player_castable=False,
)


granted_by_talent(
    id=60335,
    tab=blood_398_tab,
    tier=5,
    column=3,
    ranks=[crimson_scourge_203134, crimson_scourge_203135, crimson_scourge_203136],
    player_castable=False,
)


granted_by_talent(
    id=60336,
    tab=blood_398_tab,
    tier=6,
    column=2,
    ranks=[voracious_203138, voracious_203139],
    player_castable=False,
)


granted_by_talent(
    id=60337,
    tab=blood_398_tab,
    tier=6,
    column=3,
    ranks=[crimson_communion_203141],
    player_castable=True,
    skill_line_ability_ids=[30742],
    flags=1,
)


granted_by_talent(
    id=60338,
    tab=blood_398_tab,
    tier=7,
    column=2,
    ranks=[blood_nova_203143],
    player_castable=True,
    skill_line_ability_ids=[30743],
    flags=1,
)


granted_by_talent(
    id=60339,
    tab=blood_398_tab,
    tier=9,
    column=2,
    ranks=[purgatory_203145],
    player_castable=False,
)


granted_by_talent(
    id=60340,
    tab=blood_398_tab,
    tier=10,
    column=1,
    ranks=[bonestorm_203148],
    player_castable=True,
    skill_line_ability_ids=[30744],
    flags=1,
)


# S2a Frost: 14 new talents (ids 60345-60358, tab 399). Castables take a SkillLineAbility (30750-30752, skill 771 from the tab).


granted_by_talent(
    id=60345,
    tab=frost_399_tab,
    tier=1,
    column=3,
    ranks=[runic_attenuation_203270, runic_attenuation_203271],
    player_castable=False,
)


granted_by_talent(
    id=60346,
    tab=frost_399_tab,
    tier=4,
    column=1,
    ranks=[glacial_advance_203273],
    player_castable=True,
    skill_line_ability_ids=[30750],
    flags=1,
)


granted_by_talent(
    id=60347,
    tab=frost_399_tab,
    tier=4,
    column=2,
    ranks=[gravefrost_203275, gravefrost_203276, gravefrost_203277],
    player_castable=False,
)


granted_by_talent(
    id=60348,
    tab=frost_399_tab,
    tier=5,
    column=1,
    ranks=[koltiras_favor_203278, koltiras_favor_203279],
    player_castable=False,
)


granted_by_talent(
    id=60349,
    tab=frost_399_tab,
    tier=6,
    column=1,
    ranks=[pillar_of_frost_203280],
    player_castable=True,
    skill_line_ability_ids=[30751],
    flags=1,
)


granted_by_talent(
    id=60350,
    tab=frost_399_tab,
    tier=6,
    column=3,
    ranks=[unleashed_frenzy_203281, unleashed_frenzy_203282],
    player_castable=False,
)


granted_by_talent(
    id=60351,
    tab=frost_399_tab,
    tier=7,
    column=2,
    ranks=[toravons_whiteout_203285, toravons_whiteout_203286, toravons_whiteout_203287],
    player_castable=False,
)


granted_by_talent(
    id=60352,
    tab=frost_399_tab,
    tier=7,
    column=3,
    ranks=[final_roar_203289, final_roar_203290],
    player_castable=False,
)


granted_by_talent(
    id=60353,
    tab=frost_399_tab,
    tier=8,
    column=1,
    ranks=[obliteration_203292],
    player_castable=False,
)


granted_by_talent(
    id=60354,
    tab=frost_399_tab,
    tier=8,
    column=3,
    ranks=[rage_of_the_frozen_champion_203294, rage_of_the_frozen_champion_203295],
    player_castable=False,
)


granted_by_talent(
    id=60355,
    tab=frost_399_tab,
    tier=9,
    column=0,
    ranks=[enduring_strength_203297, enduring_strength_203298],
    player_castable=False,
)


granted_by_talent(
    id=60356,
    tab=frost_399_tab,
    tier=9,
    column=1,
    ranks=[seal_of_necrofantasia_203299, seal_of_necrofantasia_203300, seal_of_necrofantasia_203301],
    player_castable=False,
)


granted_by_talent(
    id=60357,
    tab=frost_399_tab,
    tier=9,
    column=3,
    ranks=[frostwyrms_wrath_203302, frostwyrms_wrath_203303],
    player_castable=False,
)


granted_by_talent(
    id=60358,
    tab=frost_399_tab,
    tier=10,
    column=1,
    ranks=[breath_of_sindragosa_203306],
    player_castable=True,
    skill_line_ability_ids=[30752],
    flags=1,
)


# S3a Unholy: 8 new talents (ids 60365-60372, tab 400). Castables take a SkillLineAbility (30760-30761, skill 772 from the tab).
# The 13 stock rows that changed cell are moved above; the five 5-rank talents are cut to 3 ranks (the dropped rank spells
# stay declared in deathknight_trigger_spells.py, like S2's cut ranks) and the 0-chars SQL resets the characters that held them.


granted_by_talent(
    id=60365,
    tab=unholy_400_tab,
    tier=2,
    column=1,
    ranks=[festering_plague_203440],
    player_castable=False,
)


granted_by_talent(
    id=60366,
    tab=unholy_400_tab,
    tier=2,
    column=3,
    ranks=[all_will_serve_203441, all_will_serve_203442],
    player_castable=False,
)


granted_by_talent(
    id=60367,
    tab=unholy_400_tab,
    tier=6,
    column=0,
    ranks=[infected_claws_203443, infected_claws_203444],
    player_castable=False,
)


granted_by_talent(
    id=60368,
    tab=unholy_400_tab,
    tier=6,
    column=2,
    ranks=[doomed_bidding_203445, doomed_bidding_203446, doomed_bidding_203447],
    player_castable=False,
)


granted_by_talent(
    id=60369,
    tab=unholy_400_tab,
    tier=6,
    column=3,
    ranks=[dark_transformation_203448],
    player_castable=True,
    skill_line_ability_ids=[30760],
    flags=1,
)


granted_by_talent(
    id=60370,
    tab=unholy_400_tab,
    tier=7,
    column=0,
    ranks=[rotten_touch_203449, rotten_touch_203450, rotten_touch_203451],
    player_castable=False,
)


granted_by_talent(
    id=60371,
    tab=unholy_400_tab,
    tier=8,
    column=1,
    ranks=[raise_abomination_203452],
    player_castable=True,
    skill_line_ability_ids=[30761],
    flags=1,
)


granted_by_talent(
    id=60372,
    tab=unholy_400_tab,
    tier=8,
    column=3,
    ranks=[harbinger_of_doom_203453, harbinger_of_doom_203454, harbinger_of_doom_203455],
    player_castable=False,
)
