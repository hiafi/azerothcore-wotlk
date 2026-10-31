"""
Warrior - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/warrior.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .warrior_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, retire_talent, tab
from .warrior_spells import bladestorm_46924, bloodthirst_23881, concussion_blow_12809, death_wish_12292, devastate_20243, last_stand_12975, mortal_strike_12294, piercing_howl_12323, shockwave_46968
from .warrior_trigger_spells import armored_to_the_teeth_61216, armored_to_the_teeth_61221, armored_to_the_teeth_61222, blood_and_thunder_200054, blood_and_thunder_200055, blood_frenzy_29836, blood_frenzy_29859, bloodsurge_46913, bloodsurge_46914, bloodsurge_46915, commanding_presence_12318, commanding_presence_12857, critical_block_47294, critical_block_47295, critical_block_47296, damage_shield_58872, damage_shield_58874, deep_wounds_12834, deep_wounds_12849, deep_wounds_12867, dual_wield_specialization_23584, dual_wield_specialization_23585, dual_wield_specialization_23586, dual_wield_specialization_23587, dual_wield_specialization_23588, endless_rage_29623, firm_grip_200038, firm_grip_200039, firm_grip_200040, focused_rage_29787, focused_rage_29790, focused_rage_29792, gag_order_12311, gag_order_12958, heavy_blows_12282, heavy_blows_12663, heavy_blows_12664, impale_16493, impale_16494, improved_berserker_stance_29759, improved_berserker_stance_29760, improved_berserker_stance_29761, improved_berserker_stance_29762, improved_berserker_stance_29763, improved_bloodrage_12301, improved_bloodrage_12818, improved_charge_12285, improved_charge_12697, improved_cleave_12329, improved_cleave_12950, improved_cleave_20496, improved_execute_20502, improved_execute_20503, improved_mortal_strike_35446, improved_mortal_strike_35448, improved_overpower_12290, improved_overpower_12963, improved_rend_12286, improved_rend_12658, improved_revenge_12797, improved_revenge_12799, improved_thunder_clap_12287, improved_thunder_clap_12665, improved_thunder_clap_12666, improved_whirlwind_29721, improved_whirlwind_29776, incite_50685, incite_50686, incite_50687, intensify_rage_46908, intensify_rage_46909, intensify_rage_56924, iron_temper_29593, iron_temper_29594, juggernaut_64976, puncture_12308, puncture_12810, puncture_12811, reprisal_200056, reprisal_200057, resolve_200046, resolve_200047, resolve_200048, safeguard_46945, safeguard_46949, second_wind_29834, second_wind_29838, shield_cover_200041, shield_cover_200042, shield_cover_200043, shield_discipline_200062, shield_discipline_200063, shield_mastery_29598, shield_mastery_29599, shield_specialization_200031, shield_specialization_200032, shield_specialization_200033, storm_s_bulwark_200058, storm_s_bulwark_200059, storm_s_bulwark_200060, sword_and_board_46951, sword_and_board_46952, sword_and_board_46953, taste_for_blood_56636, taste_for_blood_56637, taste_for_blood_56638, the_wall_12312, the_wall_12803, thunderstruck_200051, thunderstruck_200052, thunderstruck_200053, titan_s_grip_46917, unending_fury_56927, unending_fury_56929, unending_fury_56930, unrelenting_200049, unwavering_sentinel_200034, unwavering_sentinel_200035, unwavering_sentinel_200036
from .warrior_fury import rampage_fury_204630
from .warrior_fury_ranks import blood_rush_204677, blood_rush_204678, dance_of_death_204653, dance_of_death_204654, dance_of_death_204655, deathmaker_204671, deathmaker_204672, fresh_meat_204664, fresh_meat_204665, frenzied_blows_204659, frenzied_blows_204660, improved_bloodthirst_204666, improved_bloodthirst_204667, merciless_204656, merciless_204657, merciless_204658, quick_execution_204661, quick_execution_204662, quick_execution_204663, shredding_blows_204673, shredding_blows_204674, shredding_blows_204675, unshackled_fury_204668, unshackled_fury_204669, unshackled_fury_204670, will_of_the_berserker_204676
from .warrior_arms import anger_management_12296, anger_management_204541, anger_management_204542, avatar_204492, battlelord_204533, battlelord_204534, colossus_smash_204490, endless_rage_204544, exploiter_204531, exploiter_204532, improved_rend_204540, improved_sweeping_strikes_204529, improved_sweeping_strikes_204530, juggernaut_204543, lingering_wounds_204526, lingering_wounds_204527, lingering_wounds_204528, martial_prowess_204521, martial_prowess_204522, martial_prowess_204523, momentum_204535, momentum_204536, seismic_reverberation_204538, seismic_reverberation_204539, strength_of_arms_46865, strength_of_arms_46866, sudden_death_29723, sudden_death_29724, sudden_death_29725, sweeping_strikes_arms_204493, trauma_46854, trauma_46855, two_handed_weapon_mastery_204524, two_handed_weapon_mastery_204525, two_handed_weapon_specialization_12163, two_handed_weapon_specialization_12711, two_handed_weapon_specialization_12712, weapon_specialization_12281, weapon_specialization_12812, weapon_specialization_12813, weight_of_the_earth_204537, wrecking_crew_46867, wrecking_crew_56611, wrecking_crew_56612


arms_161_tab = tab(
    id=161,
    name='Arms',
    class_mask=1,
    spell_icon_id=514,
    skill_line=26,  # S2: derives the SkillLineAbility rows of the Arms castables (Sweeping Strikes, Colossus Smash, Avatar); not a TalentTab.dbc column
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'WarriorArms'},
)


protection_163_tab = tab(
    id=163,
    name='Protection',
    class_mask=1,
    order_index=2,
    spell_icon_id=1463,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'WarriorProtection'},
)


fury_164_tab = tab(
    id=164,
    name='Fury',
    class_mask=1,
    order_index=1,
    spell_icon_id=561,
    skill_line=256,  # S3: derives the SkillLineAbility row of the castable Rampage 204630 (SLA 30855); not a TalentTab.dbc column
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'WarriorFury'},
)


granted_by_talent(
    id=121,
    tab=arms_161_tab,
    tier=2,
    column=3,
    ranks=[deep_wounds_12834, deep_wounds_12849, deep_wounds_12867],
    player_castable=False,
)


granted_by_talent(
    id=123,
    tab=arms_161_tab,
    tier=4,
    column=3,
    ranks=[weapon_specialization_12281, weapon_specialization_12812, weapon_specialization_12813],
    player_castable=False,
)


granted_by_talent(
    id=124,
    tab=arms_161_tab,
    tier=0,
    column=0,
    ranks=[heavy_blows_12282, heavy_blows_12663, heavy_blows_12664],
    player_castable=False,
)


granted_by_talent(
    id=126,
    tab=arms_161_tab,
    tier=1,
    column=0,
    ranks=[improved_charge_12285, improved_charge_12697],
    player_castable=False,
)


granted_by_talent(
    id=127,
    tab=arms_161_tab,
    tier=0,
    column=2,
    ranks=[improved_rend_12286, improved_rend_12658, improved_rend_204540],
    player_castable=False,
)


granted_by_talent(
    id=131,
    tab=arms_161_tab,
    tier=3,
    column=0,
    ranks=[improved_overpower_12290, improved_overpower_12963],
    player_castable=False,
)


granted_by_talent(
    id=133,
    tab=arms_161_tab,
    tier=4,
    column=1,
    ranks=[sweeping_strikes_arms_204493],
    player_castable=True,
    skill_line_ability_ids=[30852],
    flags=1,
)


granted_by_talent(
    id=135,
    tab=arms_161_tab,
    tier=2,
    column=1,
    ranks=[mortal_strike_12294],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=136,
    tab=arms_161_tab,
    tier=3,
    column=1,
    ranks=[two_handed_weapon_specialization_12163, two_handed_weapon_specialization_12711, two_handed_weapon_specialization_12712],
    player_castable=False,
)


granted_by_talent(
    id=137,
    tab=arms_161_tab,
    tier=2,
    column=0,
    ranks=[anger_management_12296, anger_management_204541, anger_management_204542],
    player_castable=False,
)


granted_by_talent(
    id=141,
    tab=protection_163_tab,
    tier=0,
    column=2,
    ranks=[improved_thunder_clap_12287, improved_thunder_clap_12665, improved_thunder_clap_12666],
    player_castable=False,
)


granted_by_talent(
    id=142,
    tab=protection_163_tab,
    tier=0,
    column=0,
    ranks=[improved_bloodrage_12301, improved_bloodrage_12818],
    player_castable=False,
)


granted_by_talent(
    id=144,
    tab=protection_163_tab,
    tier=1,
    column=0,
    ranks=[incite_50685, incite_50686, incite_50687],
    player_castable=False,
)


granted_by_talent(
    id=146,
    tab=protection_163_tab,
    tier=3,
    column=2,
    ranks=[puncture_12308, puncture_12810, puncture_12811],
    player_castable=False,
)


granted_by_talent(
    id=147,
    tab=protection_163_tab,
    tier=2,
    column=1,
    ranks=[improved_revenge_12797, improved_revenge_12799],
    player_castable=False,
)


granted_by_talent(
    id=148,
    tab=protection_163_tab,
    tier=6,
    column=1,
    ranks=[50720],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=149,
    tab=protection_163_tab,
    tier=4,
    column=2,
    ranks=[gag_order_12311, gag_order_12958],
    player_castable=False,
)


granted_by_talent(
    id=150,
    tab=protection_163_tab,
    tier=4,
    column=0,
    ranks=[the_wall_12312, the_wall_12803],
    player_castable=False,
)


granted_by_talent(
    id=152,
    tab=protection_163_tab,
    tier=4,
    column=1,
    ranks=[concussion_blow_12809],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=153,
    tab=protection_163_tab,
    tier=2,
    column=0,
    ranks=[last_stand_12975],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=154,
    tab=fury_164_tab,
    tier=2,
    column=3,
    ranks=[commanding_presence_12318, commanding_presence_12857],
    player_castable=False,
)


granted_by_talent(
    id=155,
    tab=fury_164_tab,
    tier=3,
    column=2,
    ranks=[12317, 13045, 13046, 13047, 13048],
    player_castable=False,
)


granted_by_talent(
    id=156,
    tab=fury_164_tab,
    tier=5,
    column=2,
    ranks=[12319, 12971, 12972],
    player_castable=False,
)


granted_by_talent(
    id=157,
    tab=fury_164_tab,
    tier=0,
    column=2,
    ranks=[12320, 12852, 12853],
    player_castable=False,
)


granted_by_talent(
    id=159,
    tab=fury_164_tab,
    tier=1,
    column=2,
    ranks=[12322, 12999],
    player_castable=False,
)


granted_by_talent(
    id=160,
    tab=fury_164_tab,
    tier=5,
    column=1,
    ranks=[piercing_howl_12323],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=165,
    tab=fury_164_tab,
    tier=4,
    column=1,
    ranks=[death_wish_12292],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=166,
    tab=fury_164_tab,
    tier=1,
    column=0,
    ranks=[improved_cleave_12329, improved_cleave_12950, improved_cleave_20496],
    player_castable=False,
)


granted_by_talent(
    id=167,
    tab=fury_164_tab,
    tier=2,
    column=1,
    ranks=[bloodthirst_23881],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=661,
    tab=fury_164_tab,
    tier=2,
    column=2,
    ranks=[16487, 16489, 16492],
    player_castable=False,
)


granted_by_talent(
    id=662,
    tab=arms_161_tab,
    tier=2,
    column=2,
    ranks=[impale_16493, impale_16494],
    player_castable=False,
)


granted_by_talent(
    id=702,
    tab=protection_163_tab,
    tier=5,
    column=1,
    ranks=[16538, 16539, 16540, 16541, 16542],
    player_castable=False,
)


granted_by_talent(
    id=1542,
    tab=fury_164_tab,
    tier=3,
    column=1,
    ranks=[improved_execute_20502, improved_execute_20503],
    player_castable=False,
)


granted_by_talent(
    id=1581,
    tab=fury_164_tab,
    tier=3,
    column=0,
    ranks=[dual_wield_specialization_23584, dual_wield_specialization_23585, dual_wield_specialization_23586, dual_wield_specialization_23587, dual_wield_specialization_23588],
    player_castable=False,
)


granted_by_talent(
    id=1652,
    tab=protection_163_tab,
    tier=5,
    column=0,
    ranks=[iron_temper_29593, iron_temper_29594],
    player_castable=False,
)


granted_by_talent(
    id=1654,
    tab=protection_163_tab,
    tier=2,
    column=2,
    ranks=[shield_mastery_29598, shield_mastery_29599],
    player_castable=False,
)


granted_by_talent(
    id=1655,
    tab=fury_164_tab,
    tier=6,
    column=3,
    ranks=[improved_whirlwind_29721, improved_whirlwind_29776],
    player_castable=False,
)


granted_by_talent(
    id=1658,
    tab=fury_164_tab,
    tier=7,
    column=3,
    ranks=[improved_berserker_stance_29759, improved_berserker_stance_29760, improved_berserker_stance_29761, improved_berserker_stance_29762, improved_berserker_stance_29763],
    player_castable=False,
)


granted_by_talent(
    id=1659,
    tab=fury_164_tab,
    tier=8,
    column=1,
    ranks=[rampage_fury_204630],
    player_castable=True,
    skill_line_ability_ids=[30855],
    flags=1,
)


granted_by_talent(
    id=1660,
    tab=protection_163_tab,
    tier=6,
    column=2,
    ranks=[focused_rage_29787, focused_rage_29790, focused_rage_29792],
    player_castable=False,
)


granted_by_talent(
    id=1661,
    tab=arms_161_tab,
    tier=8,
    column=3,
    ranks=[endless_rage_29623, endless_rage_204544],
    player_castable=False,
)


granted_by_talent(
    id=1662,
    tab=arms_161_tab,
    tier=8,
    column=0,
    ranks=[sudden_death_29723, sudden_death_29725, sudden_death_29724],
    player_castable=False,
)


granted_by_talent(
    id=1663,
    tab=arms_161_tab,
    tier=6,
    column=0,
    ranks=[second_wind_29834, second_wind_29838],
    player_castable=False,
)


granted_by_talent(
    id=1664,
    tab=arms_161_tab,
    tier=8,
    column=2,
    ranks=[blood_frenzy_29836, blood_frenzy_29859],
    player_castable=False,
)


granted_by_talent(
    id=1666,
    tab=protection_163_tab,
    tier=0,
    column=3,
    ranks=[devastate_20243],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1824,
    tab=arms_161_tab,
    tier=7,
    column=1,
    ranks=[improved_mortal_strike_35446, improved_mortal_strike_35448],
    player_castable=False,
)


granted_by_talent(
    id=1859,
    tab=arms_161_tab,
    tier=5,
    column=3,
    ranks=[trauma_46854, trauma_46855],
    player_castable=False,
)


granted_by_talent(
    id=1862,
    tab=arms_161_tab,
    tier=6,
    column=2,
    ranks=[strength_of_arms_46865, strength_of_arms_46866],
    player_castable=False,
)


granted_by_talent(
    id=1863,
    tab=arms_161_tab,
    tier=8,
    column=1,
    ranks=[bladestorm_46924],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1864,
    tab=fury_164_tab,
    tier=6,
    column=0,
    ranks=[intensify_rage_46908, intensify_rage_46909, intensify_rage_56924],
    player_castable=False,
)


granted_by_talent(
    id=1866,
    tab=fury_164_tab,
    tier=8,
    column=2,
    ranks=[bloodsurge_46913, bloodsurge_46914, bloodsurge_46915],
    player_castable=False,
)


granted_by_talent(
    id=1867,
    tab=fury_164_tab,
    tier=10,
    column=1,
    ranks=[titan_s_grip_46917],
    player_castable=False,
)


granted_by_talent(
    id=1870,
    tab=protection_163_tab,
    tier=7,
    column=1,
    ranks=[safeguard_46945, safeguard_46949],
    player_castable=False,
)


granted_by_talent(
    id=1871,
    tab=protection_163_tab,
    tier=9,
    column=1,
    ranks=[sword_and_board_46951, sword_and_board_46952, sword_and_board_46953],
    player_castable=False,
)


granted_by_talent(
    id=1872,
    tab=protection_163_tab,
    tier=10,
    column=1,
    ranks=[shockwave_46968],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1893,
    tab=protection_163_tab,
    tier=6,
    column=0,
    ranks=[critical_block_47294, critical_block_47295, critical_block_47296],
    player_castable=False,
)


granted_by_talent(
    id=2231,
    tab=arms_161_tab,
    tier=9,
    column=1,
    ranks=[wrecking_crew_46867, wrecking_crew_56611, wrecking_crew_56612],
    player_castable=False,
)


granted_by_talent(
    id=2232,
    tab=arms_161_tab,
    tier=3,
    column=2,
    ranks=[taste_for_blood_56636, taste_for_blood_56637, taste_for_blood_56638],
    player_castable=False,
)


granted_by_talent(
    id=2234,
    tab=fury_164_tab,
    tier=9,
    column=1,
    ranks=[unending_fury_56927, unending_fury_56929, unending_fury_56930],
    player_castable=False,
)


granted_by_talent(
    id=2246,
    tab=protection_163_tab,
    tier=9,
    column=2,
    ranks=[damage_shield_58872, damage_shield_58874],
    player_castable=False,
)


granted_by_talent(
    id=2250,
    tab=fury_164_tab,
    tier=0,
    column=0,
    ranks=[armored_to_the_teeth_61216, armored_to_the_teeth_61221, armored_to_the_teeth_61222],
    player_castable=False,
)


granted_by_talent(
    id=2283,
    tab=arms_161_tab,
    tier=7,
    column=0,
    ranks=[juggernaut_64976, juggernaut_204543],
    player_castable=False,
)


granted_by_talent(
    id=1601,
    tab=protection_163_tab,
    tier=0,
    column=1,
    ranks=[shield_specialization_200031, shield_specialization_200032, shield_specialization_200033],
    player_castable=False,
)


granted_by_talent(
    id=138,
    tab=protection_163_tab,
    tier=1,
    column=2,
    ranks=[unwavering_sentinel_200034, unwavering_sentinel_200035, unwavering_sentinel_200036],
    player_castable=False,
)


granted_by_talent(
    id=140,
    tab=protection_163_tab,
    tier=2,
    column=3,
    ranks=[firm_grip_200038, firm_grip_200039, firm_grip_200040],
    player_castable=False,
)


granted_by_talent(
    id=2247,
    tab=protection_163_tab,
    tier=3,
    column=0,
    ranks=[shield_cover_200041, shield_cover_200042, shield_cover_200043],
    player_castable=False,
)


granted_by_talent(
    id=151,
    tab=protection_163_tab,
    tier=9,
    column=0,
    ranks=[thunderstruck_200051, thunderstruck_200052, thunderstruck_200053],
    player_castable=False,
)


granted_by_talent(
    id=1653,
    tab=protection_163_tab,
    tier=7,
    column=0,
    ranks=[resolve_200046, resolve_200047, resolve_200048],
    player_castable=False,
)


granted_by_talent(
    id=2236,
    tab=protection_163_tab,
    tier=8,
    column=1,
    ranks=[unrelenting_200049],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=60003,
    tab=protection_163_tab,
    tier=1,
    column=1,
    ranks=[blood_and_thunder_200054, blood_and_thunder_200055],
    player_castable=False,
)


granted_by_talent(
    id=60004,
    tab=protection_163_tab,
    tier=3,
    column=1,
    ranks=[reprisal_200056, reprisal_200057],
    player_castable=False,
)


granted_by_talent(
    id=60005,
    tab=protection_163_tab,
    tier=6,
    column=3,
    ranks=[storm_s_bulwark_200058, storm_s_bulwark_200059, storm_s_bulwark_200060],
    player_castable=False,
)


granted_by_talent(
    id=60006,
    tab=protection_163_tab,
    tier=8,
    column=2,
    ranks=[shield_discipline_200062, shield_discipline_200063],
    player_castable=False,
)


granted_by_talent(
    id=60450,
    tab=arms_161_tab,
    tier=0,
    column=1,
    ranks=[martial_prowess_204521, martial_prowess_204522, martial_prowess_204523],
    player_castable=False,
)


granted_by_talent(
    id=60451,
    tab=arms_161_tab,
    tier=1,
    column=1,
    ranks=[two_handed_weapon_mastery_204524, two_handed_weapon_mastery_204525],
    player_castable=False,
)


granted_by_talent(
    id=60452,
    tab=arms_161_tab,
    tier=1,
    column=2,
    ranks=[lingering_wounds_204526, lingering_wounds_204527, lingering_wounds_204528],
    player_castable=False,
)


granted_by_talent(
    id=60453,
    tab=arms_161_tab,
    tier=4,
    column=2,
    ranks=[improved_sweeping_strikes_204529, improved_sweeping_strikes_204530],
    player_castable=False,
)


granted_by_talent(
    id=60454,
    tab=arms_161_tab,
    tier=5,
    column=0,
    ranks=[exploiter_204531, exploiter_204532],
    player_castable=False,
)


granted_by_talent(
    id=60455,
    tab=arms_161_tab,
    tier=5,
    column=1,
    ranks=[battlelord_204533, battlelord_204534],
    player_castable=False,
)


granted_by_talent(
    id=60456,
    tab=arms_161_tab,
    tier=6,
    column=1,
    ranks=[colossus_smash_204490],
    player_castable=True,
    skill_line_ability_ids=[30850],
    flags=1,
)


granted_by_talent(
    id=60457,
    tab=arms_161_tab,
    tier=6,
    column=3,
    ranks=[momentum_204535, momentum_204536],
    player_castable=False,
)


granted_by_talent(
    id=60458,
    tab=arms_161_tab,
    tier=7,
    column=2,
    ranks=[weight_of_the_earth_204537],
    player_castable=False,
)


granted_by_talent(
    id=60459,
    tab=arms_161_tab,
    tier=7,
    column=3,
    ranks=[seismic_reverberation_204538, seismic_reverberation_204539],
    player_castable=False,
)


granted_by_talent(
    id=60460,
    tab=arms_161_tab,
    tier=10,
    column=1,
    ranks=[avatar_204492],
    player_castable=True,
    skill_line_ability_ids=[30851],
    flags=1,
)


# warrior-rework S3: eleven new Fury talents (60465-60475, ids.yaml talent block 60450-60489), minted into the cells the
# retired stock talents vacate plus three empty ones. Passive ranks, so no SkillLineAbility rows.
granted_by_talent(
    id=60465,
    tab=fury_164_tab,
    tier=0,
    column=1,
    ranks=[dance_of_death_204653, dance_of_death_204654, dance_of_death_204655],
    player_castable=False,
)


granted_by_talent(
    id=60466,
    tab=fury_164_tab,
    tier=0,
    column=3,
    ranks=[merciless_204656, merciless_204657, merciless_204658],
    player_castable=False,
)


granted_by_talent(
    id=60467,
    tab=fury_164_tab,
    tier=1,
    column=1,
    ranks=[frenzied_blows_204659, frenzied_blows_204660],
    player_castable=False,
)


granted_by_talent(
    id=60468,
    tab=fury_164_tab,
    tier=4,
    column=0,
    ranks=[quick_execution_204661, quick_execution_204662, quick_execution_204663],
    player_castable=False,
)


granted_by_talent(
    id=60469,
    tab=fury_164_tab,
    tier=4,
    column=2,
    ranks=[fresh_meat_204664, fresh_meat_204665],
    player_castable=False,
)


granted_by_talent(
    id=60470,
    tab=fury_164_tab,
    tier=5,
    column=0,
    ranks=[improved_bloodthirst_204666, improved_bloodthirst_204667],
    player_castable=False,
)


granted_by_talent(
    id=60471,
    tab=fury_164_tab,
    tier=6,
    column=1,
    ranks=[unshackled_fury_204668, unshackled_fury_204669, unshackled_fury_204670],
    player_castable=False,
)


granted_by_talent(
    id=60472,
    tab=fury_164_tab,
    tier=7,
    column=0,
    ranks=[deathmaker_204671, deathmaker_204672],
    player_castable=False,
)


granted_by_talent(
    id=60473,
    tab=fury_164_tab,
    tier=7,
    column=1,
    ranks=[shredding_blows_204673, shredding_blows_204674, shredding_blows_204675],
    player_castable=False,
)


granted_by_talent(
    id=60474,
    tab=fury_164_tab,
    tier=8,
    column=0,
    ranks=[will_of_the_berserker_204676],
    player_castable=False,
)


granted_by_talent(
    id=60475,
    tab=fury_164_tab,
    tier=9,
    column=0,
    ranks=[blood_rush_204677, blood_rush_204678],
    player_castable=False,
)


# warrior-rework S2: nine stock Arms talents are cut; they move to the retired tab (their rank rows stay in
# warrior_trigger_spells.py as inert orphans; their bindings are unbound in warrior_arms.py).
retire_talent(125)
retire_talent(128)
retire_talent(129)
retire_talent(130)
retire_talent(132)
retire_talent(134)
retire_talent(641)
retire_talent(1860)
retire_talent(2233)

# warrior-rework S3: seven stock Fury talents are cut; their cells are re-used by the minted talents above. Their rank
# rows stay in warrior_trigger_spells.py as inert orphans (their SpellMods on the shouts / Intercept are inert because no
# talent teaches them). The granted_by_talent() blocks were deleted: a retire_talent() next to a block of the same id
# raises DuplicateIdError.
retire_talent(158)    # Booming Voice
retire_talent(161)    # Improved Demoralizing Shout
retire_talent(1541)   # Improved Berserker Rage
retire_talent(1543)   # Improved Intercept
retire_talent(1657)   # Precision
retire_talent(1865)   # Furious Attacks
retire_talent(1868)   # Heroic Fury
