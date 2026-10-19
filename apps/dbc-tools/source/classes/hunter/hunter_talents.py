"""
Hunter - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/hunter.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .hunter_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, tab
from .hunter_bm_ranks import arcane_attunement_201832, arcane_attunement_201833, arcane_attunement_201834, beast_cleave_talent_201848, cobra_shot_201849, cobra_shot_201850, cobra_shot_201851, culling_the_herd_201841, culling_the_herd_201842, culling_the_herd_201843, earthshaker_201844, earthshaker_201845, improved_aspect_of_the_beast_201835, improved_aspect_of_the_beast_201836, improved_aspect_of_the_beast_201837, improved_aspect_of_the_dragonhawk_201824, improved_aspect_of_the_dragonhawk_201825, improved_aspect_of_the_viper_201830, improved_aspect_of_the_viper_201831, master_s_command_201852, master_s_command_201853, master_s_command_201854, pack_hunter_201846, pack_hunter_201847, pathfinding_201820, phoenix_s_plume_201826, primal_focus_201821, primal_focus_201822, primal_focus_201823, shark_attack_201839, shark_attack_201840, spiked_collar_201827, spiked_collar_201828, spiked_collar_201829, stomp_talent_201838, the_beast_within_201855, the_beast_within_201856, the_beast_within_201857
from .hunter_bm_spells import command_i_201800, command_ii_201801, stampede_summon_201802
from .hunter_mm_ranks import combat_experience_201982, deadeye_201969, deadeye_201970, deadeye_201971, improved_aimed_shot_201966, improved_aimed_shot_201967, improved_aimed_shot_201968, keen_eye_201972, keen_eye_201973, keen_eye_201974, precision_201963, precision_201964, precision_201965, quick_draw_201960, quick_draw_201961, quick_draw_201962, rain_of_arrows_201979, rain_of_arrows_201980, rapid_killing_201981, triangulation_201976, triangulation_201977, triangulation_201978, trick_shots_201975
from .hunter_mm_spells import falcons_mark_201922, snipers_mark_201920, vipers_mark_201921
from .hunter_spells import aimed_shot_19434, bestial_wrath_19574, chimera_shot_53209, explosive_shot_53301, readiness_23989, scatter_shot_19503, wyvern_sting_19386
from .hunter_sv_ranks import dark_hunting_202107, dark_hunting_202108, deadly_focus_202080, deadly_focus_202081, demolitions_202095, demolitions_202096, demolitions_202097, favored_prey_202082, favored_prey_202083, favored_prey_202084, improved_glaive_toss_202088, improved_glaive_toss_202089, improved_glaive_toss_202090, improved_mantis_strike_202100, improved_mantis_strike_202101, improved_mantis_strike_202102, point_of_no_escape_202106, predators_guard_202092, predators_guard_202093, predators_guard_202094, relentless_202085, relentless_202086, relentless_202087, shrapnel_202098, shrapnel_202099, survival_instincts_202091, volatile_payload_202103, volatile_payload_202104, volatile_payload_202105
from .hunter_sv_spells import cluster_bombs_202051, mantis_strike_202040, tar_bomb_202047, wildfire_bomb_202045
from .hunter_trigger_spells import animal_handler_34453, animal_handler_34454, barrage_19461, barrage_19462, barrage_24691, careful_aim_34482, careful_aim_34483, careful_aim_34484, catlike_reflexes_34462, catlike_reflexes_34464, catlike_reflexes_34465, cobra_strikes_53256, cobra_strikes_53259, cobra_strikes_53260, combat_experience_34475, combat_experience_34476, efficiency_19416, efficiency_19417, efficiency_19418, endurance_training_19583, endurance_training_19584, endurance_training_19585, entrapment_19184, entrapment_19387, entrapment_19388, expose_weakness_34500, expose_weakness_34502, expose_weakness_34503, ferocious_inspiration_34455, ferocious_inspiration_34459, ferocious_inspiration_34460, ferocity_19598, ferocity_19599, ferocity_19600, focused_aim_53620, focused_aim_53621, focused_aim_53622, focused_fire_35029, focused_fire_35030, hunter_vs_wild_56339, hunter_vs_wild_56340, hunter_vs_wild_56341, hunting_party_53290, hunting_party_53291, hunting_party_53292, improved_aspect_of_the_hawk_19552, improved_aspect_of_the_hawk_19553, improved_aspect_of_the_hawk_19554, improved_hunter_s_mark_19421, improved_hunter_s_mark_19422, improved_hunter_s_mark_19423, improved_revive_pet_19575, improved_revive_pet_24443, improved_stings_19464, improved_stings_19465, improved_stings_19466, killer_instinct_19370, killer_instinct_19371, killer_instinct_19373, kindred_spirits_56314, kindred_spirits_56315, kindred_spirits_56316, lethal_shots_19426, lethal_shots_19427, lethal_shots_19429, lightning_reflexes_19168, lightning_reflexes_19180, lightning_reflexes_19181, lock_and_load_56342, lock_and_load_56343, lock_and_load_56344, lone_survivor_19407, lone_survivor_19412, longevity_53262, longevity_53263, longevity_53264, marked_for_death_53241, marked_for_death_53243, marked_for_death_53244, master_marksman_34485, master_marksman_34486, master_marksman_34487, master_tactician_34506, master_tactician_34507, master_tactician_34508, mortal_shots_19485, mortal_shots_19487, mortal_shots_19488, pathfinding_19559, pathfinding_19560, piercing_shots_53234, piercing_shots_53237, piercing_shots_53238, point_of_no_escape_53298, point_of_no_escape_53299, precise_shots_19454, precise_shots_19455, precise_shots_19456, ranged_weapon_specialization_19507, ranged_weapon_specialization_19508, ranged_weapon_specialization_19509, rapid_killing_34948, rapid_killing_34949, resourcefulness_34491, resourcefulness_34492, resourcefulness_34493, serpent_s_swiftness_34466, serpent_s_swiftness_34467, serpent_s_swiftness_34468, sniper_training_53302, sniper_training_53303, sniper_training_53304, surefooted_19290, surefooted_19294, surefooted_24283, survival_instincts_34494, survival_instincts_34496, survival_tactics_19286, survival_tactics_19287, survivalist_19255, survivalist_19256, survivalist_19257, t_n_t_56333, t_n_t_56336, t_n_t_56337, thrill_of_the_hunt_34497, thrill_of_the_hunt_34498, trap_mastery_19376, trap_mastery_63457, trap_mastery_63458, trueshot_aura_19506, unleashed_fury_19616, unleashed_fury_19617, unleashed_fury_19618, wild_quiver_53215, wild_quiver_53216, wild_quiver_53217


beast_mastery_361_tab = tab(
    id=361,
    name='Beast Mastery',
    class_mask=4,
    spell_icon_id=255,
    skill_line=50,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'HunterBeastMastery'},
)


survival_362_tab = tab(
    id=362,
    name='Survival',
    class_mask=4,
    order_index=2,
    spell_icon_id=257,
    skill_line=51,   # Survival: stock SkillLineAbility files 19306/53301/19386/3674/19503 under 51 (S3a A1, 0-verify (c))
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'HunterSurvival'},
)


marksmanship_363_tab = tab(
    id=363,
    name='Marksmanship',
    class_mask=4,
    order_index=1,
    spell_icon_id=126,
    skill_line=163,   # Marksmanship: stock SkillLineAbility files 3044/19434/53209/34490 under 163 (S2a, MM 2.2)
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'HunterMarksmanship'},
)


# SV Lightning Reflexes: moved (5,0) -> (5,3); 24296/24297 orphaned.
granted_by_talent(
    id=1303,
    tab=survival_362_tab,
    tier=5,
    column=3,
    ranks=[lightning_reflexes_19168, lightning_reflexes_19180, lightning_reflexes_19181],
    player_castable=False,
)


# SV Entrapment: moved (1,1) -> (4,2).
granted_by_talent(
    id=1304,
    tab=survival_362_tab,
    tier=4,
    column=2,
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


# SV Lock and Load: moved (3,3) -> (3,2); stock ranks until S3b (seam rule 3).
granted_by_talent(
    id=1306,
    tab=survival_362_tab,
    tier=3,
    column=2,
    ranks=[lock_and_load_56342, lock_and_load_56343, lock_and_load_56344],
    player_castable=False,
)


# SV Survival Tactics: moved (2,3) -> (3,3).
granted_by_talent(
    id=1309,
    tab=survival_362_tab,
    tier=3,
    column=3,
    ranks=[survival_tactics_19286, survival_tactics_19287],
    player_castable=False,
)


# SV Surefooted: moved (1,0) -> (0,1).
granted_by_talent(
    id=1310,
    tab=survival_362_tab,
    tier=0,
    column=1,
    ranks=[surefooted_19290, surefooted_19294, surefooted_24283],
    player_castable=False,
)


# SV Predator's Guard: repurposed (was Deflection (2,2)); 19295/19297/19298 orphaned.
granted_by_talent(
    id=1311,
    tab=survival_362_tab,
    tier=3,
    column=0,
    ranks=[predators_guard_202092, predators_guard_202093, predators_guard_202094],
    player_castable=False,
)


# SV Mantis Strike: repurposed (was Counterattack (4,2)), no prerequisite (was Deflection 3/3); 19306 orphaned.
granted_by_talent(
    id=1312,
    tab=survival_362_tab,
    tier=4,
    column=0,
    ranks=[mantis_strike_202040],
    player_castable=True,
    skill_line_ability_ids=[30547],
    flags=1,
)


# SV Killer Instinct: moved (4,1) -> (5,0).
granted_by_talent(
    id=1321,
    tab=survival_362_tab,
    tier=5,
    column=0,
    ranks=[killer_instinct_19370, killer_instinct_19371, killer_instinct_19373],
    player_castable=False,
)


# SV Tar Bomb: repurposed (was Black Arrow, same cell); 3674 orphaned.
granted_by_talent(
    id=1322,
    tab=survival_362_tab,
    tier=8,
    column=1,
    ranks=[tar_bomb_202047],
    player_castable=True,
    skill_line_ability_ids=[30549],
    flags=1,
)


# SV Wyvern Sting: same cell, no prerequisite (was Killer Instinct 3/3).
granted_by_talent(
    id=1325,
    tab=survival_362_tab,
    tier=6,
    column=1,
    ranks=[wyvern_sting_19386],
    player_castable=True,
    flags=1,
)


# MM Lone Survivor: repurposed (was Improved Concussive Shot (0,0)).
granted_by_talent(
    id=1341,
    tab=marksmanship_363_tab,
    tier=0,
    column=3,
    ranks=[lone_survivor_19407, lone_survivor_19412],
    player_castable=False,
)


# MM Efficiency: 19419/19420 orphaned.
granted_by_talent(
    id=1342,
    tab=marksmanship_363_tab,
    tier=3,
    column=2,
    ranks=[efficiency_19416, efficiency_19417, efficiency_19418],
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


# MM Lethal Shots: moved (0,2) -> (0,0); 19430/19431 orphaned.
granted_by_talent(
    id=1344,
    tab=marksmanship_363_tab,
    tier=0,
    column=0,
    ranks=[lethal_shots_19426, lethal_shots_19427, lethal_shots_19429],
    player_castable=False,
)


# MM Aimed Shot: moved (2,2) -> (2,1), no prerequisite (was Mortal Shots 5/5).
granted_by_talent(
    id=1345,
    tab=marksmanship_363_tab,
    tier=2,
    column=1,
    ranks=[aimed_shot_19434],
    player_castable=True,
    flags=1,
)


# MM Precise Shots: repurposed (was Improved Arcane Shot (2,1)).
granted_by_talent(
    id=1346,
    tab=marksmanship_363_tab,
    tier=2,
    column=2,
    ranks=[precise_shots_19454, precise_shots_19455, precise_shots_19456],
    player_castable=False,
)


# MM Barrage: moved (4,2) -> (4,3).
granted_by_talent(
    id=1347,
    tab=marksmanship_363_tab,
    tier=4,
    column=3,
    ranks=[barrage_19461, barrage_19462, barrage_24691],
    player_castable=False,
)


# MM Improved Stings: moved (3,1) -> (3,3).
granted_by_talent(
    id=1348,
    tab=marksmanship_363_tab,
    tier=3,
    column=3,
    ranks=[improved_stings_19464, improved_stings_19465, improved_stings_19466],
    player_castable=False,
)


# MM Mortal Shots: moved (1,2) -> (1,0); 19489/19490 orphaned.
granted_by_talent(
    id=1349,
    tab=marksmanship_363_tab,
    tier=1,
    column=0,
    ranks=[mortal_shots_19485, mortal_shots_19487, mortal_shots_19488],
    player_castable=False,
)


# MM Keen Eye: repurposed (was Concussive Barrage (4,0)); 35100/35102 orphaned.
granted_by_talent(
    id=1351,
    tab=marksmanship_363_tab,
    tier=4,
    column=2,
    ranks=[keen_eye_201972, keen_eye_201973, keen_eye_201974],
    player_castable=False,
)


# MM Readiness: moved (4,1) -> (5,1).
granted_by_talent(
    id=1353,
    tab=marksmanship_363_tab,
    tier=5,
    column=1,
    ranks=[readiness_23989],
    player_castable=True,
    flags=1,
)


# MM Trueshot Aura: moved (6,1) -> (7,1), no prerequisite (was Readiness).
granted_by_talent(
    id=1361,
    tab=marksmanship_363_tab,
    tier=7,
    column=1,
    ranks=[trueshot_aura_19506],
    player_castable=True,
    flags=1,
)


# MM Ranged Weapon Specialization: moved (5,3) -> (5,2).
granted_by_talent(
    id=1362,
    tab=marksmanship_363_tab,
    tier=5,
    column=2,
    ranks=[ranged_weapon_specialization_19507, ranged_weapon_specialization_19508, ranged_weapon_specialization_19509],
    player_castable=False,
)


granted_by_talent(
    id=1381,
    tab=beast_mastery_361_tab,
    tier=0,
    column=3,
    ranks=[improved_aspect_of_the_dragonhawk_201824, improved_aspect_of_the_dragonhawk_201825],
    player_castable=False,
)


granted_by_talent(
    id=1382,
    tab=beast_mastery_361_tab,
    tier=1,
    column=3,
    ranks=[improved_aspect_of_the_hawk_19552, improved_aspect_of_the_hawk_19553, improved_aspect_of_the_hawk_19554],
    player_castable=False,
)


granted_by_talent(
    id=1384,
    tab=beast_mastery_361_tab,
    tier=0,
    column=0,
    ranks=[pathfinding_19559, pathfinding_19560, pathfinding_201820],
    player_castable=False,
)


granted_by_talent(
    id=1385,
    tab=beast_mastery_361_tab,
    tier=3,
    column=0,
    ranks=[arcane_attunement_201832, arcane_attunement_201833, arcane_attunement_201834],
    player_castable=False,
)


granted_by_talent(
    id=1386,
    tab=beast_mastery_361_tab,
    tier=6,
    column=1,
    ranks=[bestial_wrath_19574],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1387,
    tab=beast_mastery_361_tab,
    tier=4,
    column=1,
    ranks=[command_ii_201801],
    player_castable=True,
    skill_line_ability_ids=[30542],
    flags=1,
)


granted_by_talent(
    id=1388,
    tab=beast_mastery_361_tab,
    tier=4,
    column=2,
    ranks=[shark_attack_201839, shark_attack_201840],
    player_castable=False,
)


granted_by_talent(
    id=1389,
    tab=beast_mastery_361_tab,
    tier=0,
    column=2,
    ranks=[endurance_training_19583, endurance_training_19584, endurance_training_19585],
    player_castable=False,
)


granted_by_talent(
    id=1390,
    tab=beast_mastery_361_tab,
    tier=4,
    column=0,
    ranks=[stomp_talent_201838],
    player_castable=False,
)


granted_by_talent(
    id=1393,
    tab=beast_mastery_361_tab,
    tier=3,
    column=2,
    ranks=[ferocity_19598, ferocity_19599, ferocity_19600],
    player_castable=False,
)


granted_by_talent(
    id=1395,
    tab=beast_mastery_361_tab,
    tier=1,
    column=2,
    ranks=[spiked_collar_201827, spiked_collar_201828, spiked_collar_201829],
    player_castable=False,
)


granted_by_talent(
    id=1396,
    tab=beast_mastery_361_tab,
    tier=2,
    column=2,
    ranks=[unleashed_fury_19616, unleashed_fury_19617, unleashed_fury_19618],
    player_castable=False,
)


granted_by_talent(
    id=1397,
    tab=beast_mastery_361_tab,
    tier=3,
    column=3,
    ranks=[improved_aspect_of_the_beast_201835, improved_aspect_of_the_beast_201836, improved_aspect_of_the_beast_201837],
    player_castable=False,
)


# SV Relentless: repurposed (was Savage Strikes (0,2)); 19159/19160 orphaned.
granted_by_talent(
    id=1621,
    tab=survival_362_tab,
    tier=1,
    column=0,
    ranks=[relentless_202085, relentless_202086, relentless_202087],
    player_castable=False,
)


# SV Survivalist: moved (2,0) -> (2,3); 19258/19259 orphaned.
granted_by_talent(
    id=1622,
    tab=survival_362_tab,
    tier=2,
    column=3,
    ranks=[survivalist_19255, survivalist_19256, survivalist_19257],
    player_castable=False,
)


# SV Favored Prey: repurposed (was Improved Tracking (0,0)); 52783/52785-52788 orphaned.
granted_by_talent(
    id=1623,
    tab=survival_362_tab,
    tier=0,
    column=3,
    ranks=[favored_prey_202082, favored_prey_202083, favored_prey_202084],
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
    column=1,
    ranks=[improved_revive_pet_24443, improved_revive_pet_19575, phoenix_s_plume_201826],
    player_castable=False,
)


granted_by_talent(
    id=1799,
    tab=beast_mastery_361_tab,
    tier=5,
    column=2,
    ranks=[animal_handler_34453, animal_handler_34454],
    player_castable=False,
)


granted_by_talent(
    id=1800,
    tab=beast_mastery_361_tab,
    tier=6,
    column=3,
    ranks=[ferocious_inspiration_34455, ferocious_inspiration_34459, ferocious_inspiration_34460],
    player_castable=False,
)


granted_by_talent(
    id=1801,
    tab=beast_mastery_361_tab,
    tier=6,
    column=0,
    ranks=[catlike_reflexes_34462, catlike_reflexes_34464, catlike_reflexes_34465],
    player_castable=False,
)


granted_by_talent(
    id=1802,
    tab=beast_mastery_361_tab,
    tier=7,
    column=0,
    ranks=[serpent_s_swiftness_34466, serpent_s_swiftness_34467, serpent_s_swiftness_34468],
    player_castable=False,
)


granted_by_talent(
    id=1803,
    tab=beast_mastery_361_tab,
    tier=8,
    column=1,
    ranks=[the_beast_within_201855, the_beast_within_201856, the_beast_within_201857],
    player_castable=False,
)


# MM Combat Experience: + rank 201982.
granted_by_talent(
    id=1804,
    tab=marksmanship_363_tab,
    tier=5,
    column=0,
    ranks=[combat_experience_34475, combat_experience_34476, combat_experience_201982],
    player_castable=False,
)


# MM Careful Aim: moved (1,0) -> (1,3).
granted_by_talent(
    id=1806,
    tab=marksmanship_363_tab,
    tier=1,
    column=3,
    ranks=[careful_aim_34482, careful_aim_34483, careful_aim_34484],
    player_castable=False,
)


# MM Master Marksman: moved (7,1) -> (3,1); 34488/34489 orphaned.
granted_by_talent(
    id=1807,
    tab=marksmanship_363_tab,
    tier=3,
    column=1,
    ranks=[master_marksman_34485, master_marksman_34486, master_marksman_34487],
    player_castable=False,
)


# MM Falcon's Mark: repurposed (was Silencing Shot, same cell; 34490 is a trainer baseline at 14 now), no prerequisite.
granted_by_talent(
    id=1808,
    tab=marksmanship_363_tab,
    tier=8,
    column=1,
    ranks=[falcons_mark_201922],
    player_castable=True,
    skill_line_ability_ids=[30546],
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


# SV Survival Instincts: + rank 202091.
granted_by_talent(
    id=1810,
    tab=survival_362_tab,
    tier=1,
    column=3,
    ranks=[survival_instincts_34494, survival_instincts_34496, survival_instincts_202091],
    player_castable=False,
)


# SV Thrill of the Hunt: 3 -> 2 ranks; 34499 orphaned.
granted_by_talent(
    id=1811,
    tab=survival_362_tab,
    tier=6,
    column=2,
    ranks=[thrill_of_the_hunt_34497, thrill_of_the_hunt_34498],
    player_castable=False,
)


# SV Expose Weakness: moved (6,0) -> (6,3), no prerequisite (was Lightning Reflexes 5/5).
granted_by_talent(
    id=1812,
    tab=survival_362_tab,
    tier=6,
    column=3,
    ranks=[expose_weakness_34500, expose_weakness_34502, expose_weakness_34503],
    player_castable=False,
)


# SV Master Tactician: moved (7,0) -> (7,3); 34838/34839 orphaned.
granted_by_talent(
    id=1813,
    tab=survival_362_tab,
    tier=7,
    column=3,
    ranks=[master_tactician_34506, master_tactician_34507, master_tactician_34508],
    player_castable=False,
)


# SV Scatter Shot: moved (2,1) -> (2,2), the stock row's bogus prerequisite dropped.
granted_by_talent(
    id=1814,
    tab=survival_362_tab,
    tier=2,
    column=2,
    ranks=[scatter_shot_19503],
    player_castable=True,
    flags=1,
)


# MM Improved Aimed Shot: repurposed (was Go for the Throat, same cell); 34950/34954 orphaned.
granted_by_talent(
    id=1818,
    tab=marksmanship_363_tab,
    tier=2,
    column=0,
    ranks=[improved_aimed_shot_201966, improved_aimed_shot_201967, improved_aimed_shot_201968],
    player_castable=False,
)


# MM Rapid Killing: + rank 201981.
granted_by_talent(
    id=1819,
    tab=marksmanship_363_tab,
    tier=2,
    column=3,
    ranks=[rapid_killing_34948, rapid_killing_34949, rapid_killing_201981],
    player_castable=False,
)


# SV Deadly Focus: repurposed (was Hawk Eye (0,1)); 19498-19500 orphaned.
granted_by_talent(
    id=1820,
    tab=survival_362_tab,
    tier=0,
    column=0,
    ranks=[deadly_focus_202080, deadly_focus_202081],
    player_castable=False,
)


# MM Triangulation: repurposed (was Improved Barrage, same cell), no prerequisite; 35104/35110/35111 orphaned.
granted_by_talent(
    id=1821,
    tab=marksmanship_363_tab,
    tier=6,
    column=2,
    ranks=[triangulation_201976, triangulation_201977, triangulation_201978],
    player_castable=False,
)


granted_by_talent(
    id=2130,
    tab=marksmanship_363_tab,
    tier=6,
    column=0,
    ranks=[piercing_shots_53234, piercing_shots_53237, piercing_shots_53238],
    player_castable=False,
)


# MM Trick Shots: repurposed (was Rapid Recuperation (7,2)); 53228/53232 orphaned.
granted_by_talent(
    id=2131,
    tab=marksmanship_363_tab,
    tier=5,
    column=3,
    ranks=[trick_shots_201975],
    player_castable=False,
)


# MM Wild Quiver: moved (8,0) -> (8,2).
granted_by_talent(
    id=2132,
    tab=marksmanship_363_tab,
    tier=8,
    column=2,
    ranks=[wild_quiver_53215, wild_quiver_53216, wild_quiver_53217],
    player_castable=False,
)


# MM Deadeye: repurposed (was Improved Steady Shot (8,2)); 53221/53222/53224 orphaned.
granted_by_talent(
    id=2133,
    tab=marksmanship_363_tab,
    tier=3,
    column=0,
    ranks=[deadeye_201969, deadeye_201970, deadeye_201971],
    player_castable=False,
)


# MM Marked for Death: 53245/53246 orphaned.
granted_by_talent(
    id=2134,
    tab=marksmanship_363_tab,
    tier=9,
    column=1,
    ranks=[marked_for_death_53241, marked_for_death_53243, marked_for_death_53244],
    player_castable=False,
)


granted_by_talent(
    id=2135,
    tab=marksmanship_363_tab,
    tier=10,
    column=1,
    ranks=[chimera_shot_53209],
    player_castable=True,
    flags=1,
)


granted_by_talent(
    id=2136,
    tab=beast_mastery_361_tab,
    tier=7,
    column=2,
    ranks=[master_s_command_201852, master_s_command_201853, master_s_command_201854],
    player_castable=False,
)


granted_by_talent(
    id=2137,
    tab=beast_mastery_361_tab,
    tier=8,
    column=0,
    ranks=[cobra_strikes_53256, cobra_strikes_53259, cobra_strikes_53260],
    player_castable=False,
)


granted_by_talent(
    id=2138,
    tab=beast_mastery_361_tab,
    tier=2,
    column=3,
    ranks=[improved_aspect_of_the_viper_201830, improved_aspect_of_the_viper_201831],
    player_castable=False,
)


granted_by_talent(
    id=2139,
    tab=beast_mastery_361_tab,
    tier=10,
    column=1,
    ranks=[stampede_summon_201802],
    player_castable=True,
    skill_line_ability_ids=[30543],
    flags=1,
)


granted_by_talent(
    id=2140,
    tab=beast_mastery_361_tab,
    tier=8,
    column=2,
    ranks=[longevity_53262, longevity_53263, longevity_53264],
    player_castable=False,
)


# SV Dark Hunting: repurposed (was Noxious Stings (7,1)), no prerequisite (was Wyvern Sting); 53295-53297 orphaned.
granted_by_talent(
    id=2141,
    tab=survival_362_tab,
    tier=9,
    column=1,
    ranks=[dark_hunting_202107, dark_hunting_202108],
    player_castable=False,
)


# SV Point of No Escape: moved (8,0) -> (7,2); + rank 202106.
granted_by_talent(
    id=2142,
    tab=survival_362_tab,
    tier=7,
    column=2,
    ranks=[point_of_no_escape_53298, point_of_no_escape_53299, point_of_no_escape_202106],
    player_castable=False,
)


# MM Sniper Training: moved from Survival (8,3) to Marksmanship (7,2) (MARKSMANSHIP 0.1).
granted_by_talent(
    id=2143,
    tab=marksmanship_363_tab,
    tier=7,
    column=2,
    ranks=[sniper_training_53302, sniper_training_53303, sniper_training_53304],
    player_castable=False,
)


# SV Hunting Party: moved (9,2) -> (9,3), no prerequisite (was Thrill of the Hunt 3/3).
granted_by_talent(
    id=2144,
    tab=survival_362_tab,
    tier=9,
    column=3,
    ranks=[hunting_party_53290, hunting_party_53291, hunting_party_53292],
    player_castable=False,
)


# SV Explosive Shot: moved (10,1) -> (4,1), learn 60 -> 30, no prerequisite (was Black Arrow).
granted_by_talent(
    id=2145,
    tab=survival_362_tab,
    tier=4,
    column=1,
    ranks=[explosive_shot_53301],
    player_castable=True,
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
    ranks=[kindred_spirits_56314, kindred_spirits_56315, kindred_spirits_56316],
    player_castable=False,
)


granted_by_talent(
    id=60200,
    tab=beast_mastery_361_tab,
    tier=0,
    column=1,
    ranks=[primal_focus_201821, primal_focus_201822, primal_focus_201823],
    player_castable=False,
)


granted_by_talent(
    id=60201,
    tab=beast_mastery_361_tab,
    tier=2,
    column=1,
    ranks=[command_i_201800],
    player_castable=True,
    skill_line_ability_ids=[30541],
    flags=1,
)


granted_by_talent(
    id=60202,
    tab=beast_mastery_361_tab,
    tier=4,
    column=3,
    ranks=[culling_the_herd_201841, culling_the_herd_201842, culling_the_herd_201843],
    player_castable=False,
)


granted_by_talent(
    id=60203,
    tab=beast_mastery_361_tab,
    tier=5,
    column=0,
    ranks=[earthshaker_201844, earthshaker_201845],
    player_castable=False,
)


granted_by_talent(
    id=60204,
    tab=beast_mastery_361_tab,
    tier=5,
    column=1,
    ranks=[pack_hunter_201846, pack_hunter_201847],
    player_castable=False,
)


granted_by_talent(
    id=60205,
    tab=beast_mastery_361_tab,
    tier=6,
    column=2,
    ranks=[beast_cleave_talent_201848],
    player_castable=False,
)


granted_by_talent(
    id=60206,
    tab=beast_mastery_361_tab,
    tier=7,
    column=1,
    ranks=[cobra_shot_201849, cobra_shot_201850, cobra_shot_201851],
    player_castable=False,
)


# MM Quick Draw: minted.
granted_by_talent(
    id=60225,
    tab=marksmanship_363_tab,
    tier=0,
    column=2,
    ranks=[quick_draw_201960, quick_draw_201961, quick_draw_201962],
    player_castable=False,
)


# MM Precision: minted.
granted_by_talent(
    id=60226,
    tab=marksmanship_363_tab,
    tier=1,
    column=2,
    ranks=[precision_201963, precision_201964, precision_201965],
    player_castable=False,
)


# MM Sniper's Mark: minted.
granted_by_talent(
    id=60227,
    tab=marksmanship_363_tab,
    tier=4,
    column=1,
    ranks=[snipers_mark_201920],
    player_castable=True,
    skill_line_ability_ids=[30544],
    flags=1,
)


# MM Viper's Mark: minted.
granted_by_talent(
    id=60228,
    tab=marksmanship_363_tab,
    tier=6,
    column=1,
    ranks=[vipers_mark_201921],
    player_castable=True,
    skill_line_ability_ids=[30545],
    flags=1,
)


# MM Rain of Arrows: minted.
granted_by_talent(
    id=60229,
    tab=marksmanship_363_tab,
    tier=6,
    column=3,
    ranks=[rain_of_arrows_201979, rain_of_arrows_201980],
    player_castable=False,
)


# SV Hunter vs. Wild: moved (4,0) -> (4,3), no prerequisite (was Survivalist 5/5).
granted_by_talent(
    id=2228,
    tab=survival_362_tab,
    tier=4,
    column=3,
    ranks=[hunter_vs_wild_56339, hunter_vs_wild_56340, hunter_vs_wild_56341],
    player_castable=False,
)


# SV T.N.T.: moved (3,1) -> (8,2).
granted_by_talent(
    id=2229,
    tab=survival_362_tab,
    tier=8,
    column=2,
    ranks=[t_n_t_56333, t_n_t_56336, t_n_t_56337],
    player_castable=False,
)


# SV Improved Glaive Toss: minted.
granted_by_talent(
    id=60250,
    tab=survival_362_tab,
    tier=1,
    column=1,
    ranks=[improved_glaive_toss_202088, improved_glaive_toss_202089, improved_glaive_toss_202090],
    player_castable=False,
)


# SV Wildfire Bomb: minted.
granted_by_talent(
    id=60251,
    tab=survival_362_tab,
    tier=2,
    column=1,
    ranks=[wildfire_bomb_202045],
    player_castable=True,
    skill_line_ability_ids=[30548],
    flags=1,
)


# SV Demolitions: minted.
granted_by_talent(
    id=60252,
    tab=survival_362_tab,
    tier=3,
    column=1,
    ranks=[demolitions_202095, demolitions_202096, demolitions_202097],
    player_castable=False,
)


# SV Shrapnel: minted.
granted_by_talent(
    id=60253,
    tab=survival_362_tab,
    tier=5,
    column=1,
    ranks=[shrapnel_202098, shrapnel_202099],
    player_castable=False,
)


# SV Improved Mantis Strike: minted.
granted_by_talent(
    id=60254,
    tab=survival_362_tab,
    tier=6,
    column=0,
    ranks=[improved_mantis_strike_202100, improved_mantis_strike_202101, improved_mantis_strike_202102],
    player_castable=False,
)


# SV Volatile Payload: minted.
granted_by_talent(
    id=60255,
    tab=survival_362_tab,
    tier=7,
    column=1,
    ranks=[volatile_payload_202103, volatile_payload_202104, volatile_payload_202105],
    player_castable=False,
)


# SV Cluster Bombs: minted.
granted_by_talent(
    id=60256,
    tab=survival_362_tab,
    tier=10,
    column=1,
    ranks=[cluster_bombs_202051],
    player_castable=True,
    skill_line_ability_ids=[30550],
    flags=1,
)
