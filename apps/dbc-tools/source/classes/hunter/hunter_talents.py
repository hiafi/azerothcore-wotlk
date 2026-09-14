"""
Hunter - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/hunter.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .hunter_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, tab
from .hunter_spells import aimed_shot_19434, bestial_wrath_19574, black_arrow_3674, chimera_shot_53209, counterattack_19306, explosive_shot_53301, intimidation_19577, readiness_23989, scatter_shot_19503, silencing_shot_34490, wyvern_sting_19386
from .hunter_trigger_spells import animal_handler_34453, animal_handler_34454, aspect_mastery_53265, barrage_19461, barrage_19462, barrage_24691, beast_mastery_53270, bestial_discipline_19590, bestial_discipline_19592, careful_aim_34482, careful_aim_34483, careful_aim_34484, catlike_reflexes_34462, catlike_reflexes_34464, catlike_reflexes_34465, cobra_strikes_53256, cobra_strikes_53259, cobra_strikes_53260, combat_experience_34475, combat_experience_34476, concussive_barrage_35100, concussive_barrage_35102, efficiency_19416, efficiency_19417, efficiency_19418, efficiency_19419, efficiency_19420, endurance_training_19583, endurance_training_19584, endurance_training_19585, endurance_training_19586, endurance_training_19587, entrapment_19184, entrapment_19387, entrapment_19388, expose_weakness_34500, expose_weakness_34502, expose_weakness_34503, ferocious_inspiration_34455, ferocious_inspiration_34459, ferocious_inspiration_34460, ferocity_19598, ferocity_19599, ferocity_19600, ferocity_19601, ferocity_19602, focused_aim_53620, focused_aim_53621, focused_aim_53622, focused_fire_35029, focused_fire_35030, frenzy_19621, frenzy_19622, frenzy_19623, frenzy_19624, frenzy_19625, go_for_the_throat_34950, go_for_the_throat_34954, hawk_eye_19498, hawk_eye_19499, hawk_eye_19500, hunter_vs_wild_56339, hunter_vs_wild_56340, hunter_vs_wild_56341, hunting_party_53290, hunting_party_53291, hunting_party_53292, improved_arcane_shot_19454, improved_arcane_shot_19455, improved_arcane_shot_19456, improved_aspect_of_the_hawk_19552, improved_aspect_of_the_hawk_19553, improved_aspect_of_the_hawk_19554, improved_aspect_of_the_hawk_19555, improved_aspect_of_the_hawk_19556, improved_aspect_of_the_monkey_19549, improved_aspect_of_the_monkey_19550, improved_aspect_of_the_monkey_19551, improved_barrage_35104, improved_barrage_35110, improved_barrage_35111, improved_concussive_shot_19407, improved_concussive_shot_19412, improved_hunter_s_mark_19421, improved_hunter_s_mark_19422, improved_hunter_s_mark_19423, improved_mend_pet_19572, improved_mend_pet_19573, improved_revive_pet_19575, improved_revive_pet_24443, improved_steady_shot_53221, improved_steady_shot_53222, improved_steady_shot_53224, improved_stings_19464, improved_stings_19465, improved_stings_19466, improved_tracking_52783, improved_tracking_52785, improved_tracking_52786, improved_tracking_52787, improved_tracking_52788, invigoration_53252, invigoration_53253, kindred_spirits_56314, kindred_spirits_56315, kindred_spirits_56316, kindred_spirits_56317, kindred_spirits_56318, lock_and_load_56342, lock_and_load_56343, lock_and_load_56344, longevity_53262, longevity_53263, longevity_53264, marked_for_death_53241, marked_for_death_53243, marked_for_death_53244, marked_for_death_53245, marked_for_death_53246, master_marksman_34485, master_marksman_34486, master_marksman_34487, master_marksman_34488, master_marksman_34489, master_tactician_34506, master_tactician_34507, master_tactician_34508, master_tactician_34838, master_tactician_34839, mortal_shots_19485, mortal_shots_19487, mortal_shots_19488, mortal_shots_19489, mortal_shots_19490, noxious_stings_53295, noxious_stings_53296, noxious_stings_53297, pathfinding_19559, pathfinding_19560, piercing_shots_53234, piercing_shots_53237, piercing_shots_53238, point_of_no_escape_53298, point_of_no_escape_53299, rapid_killing_34948, rapid_killing_34949, rapid_recuperation_53228, rapid_recuperation_53232, resourcefulness_34491, resourcefulness_34492, resourcefulness_34493, savage_strikes_19159, savage_strikes_19160, serpent_s_swiftness_34466, serpent_s_swiftness_34467, serpent_s_swiftness_34468, serpent_s_swiftness_34469, serpent_s_swiftness_34470, sniper_training_53302, sniper_training_53303, sniper_training_53304, surefooted_19290, surefooted_19294, surefooted_24283, survival_instincts_34494, survival_instincts_34496, survival_tactics_19286, survival_tactics_19287, survivalist_19255, survivalist_19256, survivalist_19257, survivalist_19258, survivalist_19259, t_n_t_56333, t_n_t_56336, t_n_t_56337, the_beast_within_34692, thick_hide_19609, thick_hide_19610, thick_hide_19612, thrill_of_the_hunt_34497, thrill_of_the_hunt_34498, thrill_of_the_hunt_34499, trap_mastery_19376, trap_mastery_63457, trap_mastery_63458, trueshot_aura_19506, unleashed_fury_19616, unleashed_fury_19617, unleashed_fury_19618, unleashed_fury_19619, unleashed_fury_19620, wild_quiver_53215, wild_quiver_53216, wild_quiver_53217


beast_mastery_361_tab = tab(
    id=361,
    name='Beast Mastery',
    class_mask=4,
    spell_icon_id=255,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 189},
)


survival_362_tab = tab(
    id=362,
    name='Survival',
    class_mask=4,
    order_index=2,
    spell_icon_id=257,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 718},
)


marksmanship_363_tab = tab(
    id=363,
    name='Marksmanship',
    class_mask=4,
    order_index=1,
    spell_icon_id=126,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 489},
)


granted_by_talent(
    id=1303,
    tab=survival_362_tab,
    tier=5,
    column=0,
    ranks=[19168, 19180, 19181, 24296, 24297],
    player_castable=False,
)


granted_by_talent(
    id=1304,
    tab=survival_362_tab,
    tier=1,
    column=1,
    ranks=[entrapment_19184, entrapment_19387, entrapment_19388],
    player_castable=False,
)


granted_by_talent(
    id=1305,
    tab=survival_362_tab,
    tier=1,
    column=2,
    ranks=[trap_mastery_19376, trap_mastery_63457, trap_mastery_63458],
    player_castable=False,
)


granted_by_talent(
    id=1306,
    tab=survival_362_tab,
    tier=3,
    column=3,
    ranks=[lock_and_load_56342, lock_and_load_56343, lock_and_load_56344],
    player_castable=False,
)


granted_by_talent(
    id=1309,
    tab=survival_362_tab,
    tier=2,
    column=3,
    ranks=[survival_tactics_19286, survival_tactics_19287],
    player_castable=False,
)


granted_by_talent(
    id=1310,
    tab=survival_362_tab,
    tier=1,
    column=0,
    ranks=[surefooted_19290, surefooted_19294, surefooted_24283],
    player_castable=False,
)


granted_by_talent(
    id=1311,
    tab=survival_362_tab,
    tier=2,
    column=2,
    ranks=[19295, 19297, 19298],
    player_castable=False,
)


granted_by_talent(
    id=1312,
    tab=survival_362_tab,
    tier=4,
    column=2,
    ranks=[counterattack_19306],
    player_castable=False,
    depends_on={'talent_id': 1311, 'rank': 2},
    flags=1,
)


granted_by_talent(
    id=1321,
    tab=survival_362_tab,
    tier=4,
    column=1,
    ranks=[19370, 19371, 19373],
    player_castable=False,
)


granted_by_talent(
    id=1322,
    tab=survival_362_tab,
    tier=8,
    column=1,
    ranks=[black_arrow_3674],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1325,
    tab=survival_362_tab,
    tier=6,
    column=1,
    ranks=[wyvern_sting_19386],
    player_castable=False,
    depends_on={'talent_id': 1321, 'rank': 2},
    flags=1,
)


granted_by_talent(
    id=1341,
    tab=marksmanship_363_tab,
    tier=0,
    column=0,
    ranks=[improved_concussive_shot_19407, improved_concussive_shot_19412],
    player_castable=False,
)


granted_by_talent(
    id=1342,
    tab=marksmanship_363_tab,
    tier=3,
    column=2,
    ranks=[efficiency_19416, efficiency_19417, efficiency_19418, efficiency_19419, efficiency_19420],
    player_castable=False,
)


granted_by_talent(
    id=1343,
    tab=marksmanship_363_tab,
    tier=1,
    column=1,
    ranks=[improved_hunter_s_mark_19421, improved_hunter_s_mark_19422, improved_hunter_s_mark_19423],
    player_castable=False,
)


granted_by_talent(
    id=1344,
    tab=marksmanship_363_tab,
    tier=0,
    column=2,
    ranks=[19426, 19427, 19429, 19430, 19431],
    player_castable=False,
)


granted_by_talent(
    id=1345,
    tab=marksmanship_363_tab,
    tier=2,
    column=2,
    ranks=[aimed_shot_19434],
    player_castable=False,
    depends_on={'talent_id': 1349, 'rank': 4},
    flags=1,
)


granted_by_talent(
    id=1346,
    tab=marksmanship_363_tab,
    tier=2,
    column=1,
    ranks=[improved_arcane_shot_19454, improved_arcane_shot_19455, improved_arcane_shot_19456],
    player_castable=False,
)


granted_by_talent(
    id=1347,
    tab=marksmanship_363_tab,
    tier=4,
    column=2,
    ranks=[barrage_19461, barrage_19462, barrage_24691],
    player_castable=False,
)


granted_by_talent(
    id=1348,
    tab=marksmanship_363_tab,
    tier=3,
    column=1,
    ranks=[improved_stings_19464, improved_stings_19465, improved_stings_19466],
    player_castable=False,
)


granted_by_talent(
    id=1349,
    tab=marksmanship_363_tab,
    tier=1,
    column=2,
    ranks=[mortal_shots_19485, mortal_shots_19487, mortal_shots_19488, mortal_shots_19489, mortal_shots_19490],
    player_castable=False,
)


granted_by_talent(
    id=1351,
    tab=marksmanship_363_tab,
    tier=4,
    column=0,
    ranks=[concussive_barrage_35100, concussive_barrage_35102],
    player_castable=False,
)


granted_by_talent(
    id=1353,
    tab=marksmanship_363_tab,
    tier=4,
    column=1,
    ranks=[readiness_23989],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1361,
    tab=marksmanship_363_tab,
    tier=6,
    column=1,
    ranks=[trueshot_aura_19506],
    player_castable=False,
    depends_on={'talent_id': 1353, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=1362,
    tab=marksmanship_363_tab,
    tier=5,
    column=3,
    ranks=[19507, 19508, 19509],
    player_castable=False,
)


granted_by_talent(
    id=1381,
    tab=beast_mastery_361_tab,
    tier=1,
    column=1,
    ranks=[improved_aspect_of_the_monkey_19549, improved_aspect_of_the_monkey_19550, improved_aspect_of_the_monkey_19551],
    player_castable=False,
)


granted_by_talent(
    id=1382,
    tab=beast_mastery_361_tab,
    tier=0,
    column=1,
    ranks=[improved_aspect_of_the_hawk_19552, improved_aspect_of_the_hawk_19553, improved_aspect_of_the_hawk_19554, improved_aspect_of_the_hawk_19555, improved_aspect_of_the_hawk_19556],
    player_castable=False,
)


granted_by_talent(
    id=1384,
    tab=beast_mastery_361_tab,
    tier=2,
    column=0,
    ranks=[pathfinding_19559, pathfinding_19560],
    player_castable=False,
)


granted_by_talent(
    id=1385,
    tab=beast_mastery_361_tab,
    tier=3,
    column=1,
    ranks=[improved_mend_pet_19572, improved_mend_pet_19573],
    player_castable=False,
)


granted_by_talent(
    id=1386,
    tab=beast_mastery_361_tab,
    tier=6,
    column=1,
    ranks=[bestial_wrath_19574],
    player_castable=False,
    depends_on={'talent_id': 1387, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=1387,
    tab=beast_mastery_361_tab,
    tier=4,
    column=1,
    ranks=[intimidation_19577],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1388,
    tab=beast_mastery_361_tab,
    tier=4,
    column=0,
    ranks=[19578, 20895],
    player_castable=False,
)


granted_by_talent(
    id=1389,
    tab=beast_mastery_361_tab,
    tier=0,
    column=2,
    ranks=[endurance_training_19583, endurance_training_19584, endurance_training_19585, endurance_training_19586, endurance_training_19587],
    player_castable=False,
)


granted_by_talent(
    id=1390,
    tab=beast_mastery_361_tab,
    tier=4,
    column=3,
    ranks=[bestial_discipline_19590, bestial_discipline_19592],
    player_castable=False,
)


granted_by_talent(
    id=1393,
    tab=beast_mastery_361_tab,
    tier=3,
    column=2,
    ranks=[ferocity_19598, ferocity_19599, ferocity_19600, ferocity_19601, ferocity_19602],
    player_castable=False,
)


granted_by_talent(
    id=1395,
    tab=beast_mastery_361_tab,
    tier=1,
    column=2,
    ranks=[thick_hide_19609, thick_hide_19610, thick_hide_19612],
    player_castable=False,
)


granted_by_talent(
    id=1396,
    tab=beast_mastery_361_tab,
    tier=2,
    column=2,
    ranks=[unleashed_fury_19616, unleashed_fury_19617, unleashed_fury_19618, unleashed_fury_19619, unleashed_fury_19620],
    player_castable=False,
)


granted_by_talent(
    id=1397,
    tab=beast_mastery_361_tab,
    tier=5,
    column=2,
    ranks=[frenzy_19621, frenzy_19622, frenzy_19623, frenzy_19624, frenzy_19625],
    player_castable=False,
    depends_on={'talent_id': 1393, 'rank': 4},
)


granted_by_talent(
    id=1621,
    tab=survival_362_tab,
    tier=0,
    column=2,
    ranks=[savage_strikes_19159, savage_strikes_19160],
    player_castable=False,
)


granted_by_talent(
    id=1622,
    tab=survival_362_tab,
    tier=2,
    column=0,
    ranks=[survivalist_19255, survivalist_19256, survivalist_19257, survivalist_19258, survivalist_19259],
    player_castable=False,
)


granted_by_talent(
    id=1623,
    tab=survival_362_tab,
    tier=0,
    column=0,
    ranks=[improved_tracking_52783, improved_tracking_52785, improved_tracking_52786, improved_tracking_52787, improved_tracking_52788],
    player_castable=False,
)


granted_by_talent(
    id=1624,
    tab=beast_mastery_361_tab,
    tier=1,
    column=0,
    ranks=[focused_fire_35029, focused_fire_35030],
    player_castable=False,
)


granted_by_talent(
    id=1625,
    tab=beast_mastery_361_tab,
    tier=1,
    column=3,
    ranks=[improved_revive_pet_24443, improved_revive_pet_19575],
    player_castable=False,
)


granted_by_talent(
    id=1799,
    tab=beast_mastery_361_tab,
    tier=5,
    column=0,
    ranks=[animal_handler_34453, animal_handler_34454],
    player_castable=False,
)


granted_by_talent(
    id=1800,
    tab=beast_mastery_361_tab,
    tier=6,
    column=0,
    ranks=[ferocious_inspiration_34455, ferocious_inspiration_34459, ferocious_inspiration_34460],
    player_castable=False,
)


granted_by_talent(
    id=1801,
    tab=beast_mastery_361_tab,
    tier=6,
    column=2,
    ranks=[catlike_reflexes_34462, catlike_reflexes_34464, catlike_reflexes_34465],
    player_castable=False,
)


granted_by_talent(
    id=1802,
    tab=beast_mastery_361_tab,
    tier=7,
    column=2,
    ranks=[serpent_s_swiftness_34466, serpent_s_swiftness_34467, serpent_s_swiftness_34468, serpent_s_swiftness_34469, serpent_s_swiftness_34470],
    player_castable=False,
)


granted_by_talent(
    id=1803,
    tab=beast_mastery_361_tab,
    tier=8,
    column=1,
    ranks=[the_beast_within_34692],
    player_castable=False,
    depends_on={'talent_id': 1386, 'rank': 0},
)


granted_by_talent(
    id=1804,
    tab=marksmanship_363_tab,
    tier=5,
    column=0,
    ranks=[combat_experience_34475, combat_experience_34476],
    player_castable=False,
)


granted_by_talent(
    id=1806,
    tab=marksmanship_363_tab,
    tier=1,
    column=0,
    ranks=[careful_aim_34482, careful_aim_34483, careful_aim_34484],
    player_castable=False,
)


granted_by_talent(
    id=1807,
    tab=marksmanship_363_tab,
    tier=7,
    column=1,
    ranks=[master_marksman_34485, master_marksman_34486, master_marksman_34487, master_marksman_34488, master_marksman_34489],
    player_castable=False,
)


granted_by_talent(
    id=1808,
    tab=marksmanship_363_tab,
    tier=8,
    column=1,
    ranks=[silencing_shot_34490],
    player_castable=False,
    depends_on={'talent_id': 1807, 'rank': 4},
    flags=1,
)


granted_by_talent(
    id=1809,
    tab=survival_362_tab,
    tier=5,
    column=2,
    ranks=[resourcefulness_34491, resourcefulness_34492, resourcefulness_34493],
    player_castable=False,
)


granted_by_talent(
    id=1810,
    tab=survival_362_tab,
    tier=1,
    column=3,
    ranks=[survival_instincts_34494, survival_instincts_34496],
    player_castable=False,
)


granted_by_talent(
    id=1811,
    tab=survival_362_tab,
    tier=6,
    column=2,
    ranks=[thrill_of_the_hunt_34497, thrill_of_the_hunt_34498, thrill_of_the_hunt_34499],
    player_castable=False,
)


granted_by_talent(
    id=1812,
    tab=survival_362_tab,
    tier=6,
    column=0,
    ranks=[expose_weakness_34500, expose_weakness_34502, expose_weakness_34503],
    player_castable=False,
    depends_on={'talent_id': 1303, 'rank': 4},
)


granted_by_talent(
    id=1813,
    tab=survival_362_tab,
    tier=7,
    column=0,
    ranks=[master_tactician_34506, master_tactician_34507, master_tactician_34508, master_tactician_34838, master_tactician_34839],
    player_castable=False,
)


granted_by_talent(
    id=1814,
    tab=survival_362_tab,
    tier=2,
    column=1,
    ranks=[scatter_shot_19503],
    player_castable=False,
    depends_on={'talent_id': 0, 'rank': 4},
    flags=1,
)


granted_by_talent(
    id=1818,
    tab=marksmanship_363_tab,
    tier=2,
    column=0,
    ranks=[go_for_the_throat_34950, go_for_the_throat_34954],
    player_castable=False,
)


granted_by_talent(
    id=1819,
    tab=marksmanship_363_tab,
    tier=2,
    column=3,
    ranks=[rapid_killing_34948, rapid_killing_34949],
    player_castable=False,
)


granted_by_talent(
    id=1820,
    tab=survival_362_tab,
    tier=0,
    column=1,
    ranks=[hawk_eye_19498, hawk_eye_19499, hawk_eye_19500],
    player_castable=False,
)


granted_by_talent(
    id=1821,
    tab=marksmanship_363_tab,
    tier=6,
    column=2,
    ranks=[improved_barrage_35104, improved_barrage_35110, improved_barrage_35111],
    player_castable=False,
    depends_on={'talent_id': 1347, 'rank': 2},
)


granted_by_talent(
    id=2130,
    tab=marksmanship_363_tab,
    tier=6,
    column=0,
    ranks=[piercing_shots_53234, piercing_shots_53237, piercing_shots_53238],
    player_castable=False,
)


granted_by_talent(
    id=2131,
    tab=marksmanship_363_tab,
    tier=7,
    column=2,
    ranks=[rapid_recuperation_53228, rapid_recuperation_53232],
    player_castable=False,
)


granted_by_talent(
    id=2132,
    tab=marksmanship_363_tab,
    tier=8,
    column=0,
    ranks=[wild_quiver_53215, wild_quiver_53216, wild_quiver_53217],
    player_castable=False,
)


granted_by_talent(
    id=2133,
    tab=marksmanship_363_tab,
    tier=8,
    column=2,
    ranks=[improved_steady_shot_53221, improved_steady_shot_53222, improved_steady_shot_53224],
    player_castable=False,
)


granted_by_talent(
    id=2134,
    tab=marksmanship_363_tab,
    tier=9,
    column=1,
    ranks=[marked_for_death_53241, marked_for_death_53243, marked_for_death_53244, marked_for_death_53245, marked_for_death_53246],
    player_castable=False,
)


granted_by_talent(
    id=2135,
    tab=marksmanship_363_tab,
    tier=10,
    column=1,
    ranks=[chimera_shot_53209],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2136,
    tab=beast_mastery_361_tab,
    tier=7,
    column=0,
    ranks=[invigoration_53252, invigoration_53253],
    player_castable=False,
    depends_on={'talent_id': 1800, 'rank': 2},
)


granted_by_talent(
    id=2137,
    tab=beast_mastery_361_tab,
    tier=8,
    column=2,
    ranks=[cobra_strikes_53256, cobra_strikes_53259, cobra_strikes_53260],
    player_castable=False,
    depends_on={'talent_id': 1802, 'rank': 4},
)


granted_by_talent(
    id=2138,
    tab=beast_mastery_361_tab,
    tier=2,
    column=1,
    ranks=[aspect_mastery_53265],
    player_castable=False,
)


granted_by_talent(
    id=2139,
    tab=beast_mastery_361_tab,
    tier=10,
    column=1,
    ranks=[beast_mastery_53270],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2140,
    tab=beast_mastery_361_tab,
    tier=8,
    column=0,
    ranks=[longevity_53262, longevity_53263, longevity_53264],
    player_castable=False,
)


granted_by_talent(
    id=2141,
    tab=survival_362_tab,
    tier=7,
    column=1,
    ranks=[noxious_stings_53295, noxious_stings_53296, noxious_stings_53297],
    player_castable=False,
    depends_on={'talent_id': 1325, 'rank': 0},
)


granted_by_talent(
    id=2142,
    tab=survival_362_tab,
    tier=8,
    column=0,
    ranks=[point_of_no_escape_53298, point_of_no_escape_53299],
    player_castable=False,
)


granted_by_talent(
    id=2143,
    tab=survival_362_tab,
    tier=8,
    column=3,
    ranks=[sniper_training_53302, sniper_training_53303, sniper_training_53304],
    player_castable=False,
)


granted_by_talent(
    id=2144,
    tab=survival_362_tab,
    tier=9,
    column=2,
    ranks=[hunting_party_53290, hunting_party_53291, hunting_party_53292],
    player_castable=False,
    depends_on={'talent_id': 1811, 'rank': 2},
)


granted_by_talent(
    id=2145,
    tab=survival_362_tab,
    tier=10,
    column=1,
    ranks=[explosive_shot_53301],
    player_castable=False,
    depends_on={'talent_id': 1322, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=2197,
    tab=marksmanship_363_tab,
    tier=0,
    column=1,
    ranks=[focused_aim_53620, focused_aim_53621, focused_aim_53622],
    player_castable=False,
)


granted_by_talent(
    id=2227,
    tab=beast_mastery_361_tab,
    tier=9,
    column=1,
    ranks=[kindred_spirits_56314, kindred_spirits_56315, kindred_spirits_56316, kindred_spirits_56317, kindred_spirits_56318],
    player_castable=False,
)


granted_by_talent(
    id=2228,
    tab=survival_362_tab,
    tier=4,
    column=0,
    ranks=[hunter_vs_wild_56339, hunter_vs_wild_56340, hunter_vs_wild_56341],
    player_castable=False,
    depends_on={'talent_id': 1622, 'rank': 4},
)


granted_by_talent(
    id=2229,
    tab=survival_362_tab,
    tier=3,
    column=1,
    ranks=[t_n_t_56333, t_n_t_56336, t_n_t_56337],
    player_castable=False,
)
