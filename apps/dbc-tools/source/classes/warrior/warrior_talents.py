"""
Warrior - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/warrior.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .warrior_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, tab
from .warrior_spells import bladestorm_46924, bloodthirst_23881, concussion_blow_12809, death_wish_12292, devastate_20243, last_stand_12975, mortal_strike_12294, piercing_howl_12323, shockwave_46968, sweeping_strikes_12328
from .warrior_trigger_spells import armored_to_the_teeth_61216, armored_to_the_teeth_61221, armored_to_the_teeth_61222, blood_and_thunder_200054, blood_and_thunder_200055, blood_frenzy_29836, blood_frenzy_29859, bloodsurge_46913, bloodsurge_46914, bloodsurge_46915, booming_voice_12321, booming_voice_12835, commanding_presence_12318, commanding_presence_12857, commanding_presence_12858, commanding_presence_12860, commanding_presence_12861, critical_block_47294, critical_block_47295, critical_block_47296, damage_shield_58872, damage_shield_58874, deep_wounds_12834, deep_wounds_12849, deep_wounds_12867, dual_wield_specialization_23584, dual_wield_specialization_23585, dual_wield_specialization_23586, dual_wield_specialization_23587, dual_wield_specialization_23588, endless_rage_29623, firm_grip_200038, firm_grip_200039, firm_grip_200040, focused_rage_29787, focused_rage_29790, focused_rage_29792, gag_order_12311, gag_order_12958, impale_16493, impale_16494, improved_berserker_rage_20500, improved_berserker_rage_20501, improved_berserker_stance_29759, improved_berserker_stance_29760, improved_berserker_stance_29761, improved_berserker_stance_29762, improved_berserker_stance_29763, improved_bloodrage_12301, improved_bloodrage_12818, improved_charge_12285, improved_charge_12697, improved_cleave_12329, improved_cleave_12950, improved_cleave_20496, improved_demoralizing_shout_12324, improved_demoralizing_shout_12876, improved_demoralizing_shout_12877, improved_demoralizing_shout_12878, improved_demoralizing_shout_12879, improved_disciplines_12312, improved_disciplines_12803, improved_execute_20502, improved_execute_20503, improved_hamstring_12289, improved_hamstring_12668, improved_hamstring_23695, improved_heroic_strike_12282, improved_heroic_strike_12663, improved_heroic_strike_12664, improved_intercept_29888, improved_intercept_29889, improved_mortal_strike_35446, improved_mortal_strike_35448, improved_mortal_strike_35449, improved_overpower_12290, improved_overpower_12963, improved_rend_12286, improved_rend_12658, improved_revenge_12797, improved_revenge_12799, improved_slam_12330, improved_slam_12862, improved_thunder_clap_12287, improved_thunder_clap_12665, improved_thunder_clap_12666, improved_whirlwind_29721, improved_whirlwind_29776, incite_50685, incite_50686, incite_50687, intensify_rage_46908, intensify_rage_46909, intensify_rage_56924, iron_temper_29593, iron_temper_29594, juggernaut_64976, puncture_12308, puncture_12810, puncture_12811, rampage_29801, reprisal_200056, reprisal_200057, resolve_200046, resolve_200047, resolve_200048, safeguard_46945, safeguard_46949, second_wind_29834, second_wind_29838, shield_cover_200041, shield_cover_200042, shield_cover_200043, shield_discipline_200062, shield_discipline_200063, shield_mastery_29598, shield_mastery_29599, shield_specialization_200031, shield_specialization_200032, shield_specialization_200033, storm_s_bulwark_200058, storm_s_bulwark_200059, storm_s_bulwark_200060, sword_and_board_46951, sword_and_board_46952, sword_and_board_46953, tactical_mastery_12295, tactical_mastery_12676, tactical_mastery_12677, taste_for_blood_56636, taste_for_blood_56637, taste_for_blood_56638, thunderstruck_200051, thunderstruck_200052, thunderstruck_200053, titan_s_grip_46917, unbridled_wrath_200034, unbridled_wrath_200035, unbridled_wrath_200036, unending_fury_56927, unending_fury_56929, unending_fury_56930, unending_fury_56931, unending_fury_56932, unrelenting_200049, unrelenting_assault_46859, unrelenting_assault_46860, weapon_mastery_20504


arms_161_tab = tab(
    id=161,
    name='Arms',
    class_mask=1,
    spell_icon_id=514,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 24},
)


protection_163_tab = tab(
    id=163,
    name='Protection',
    class_mask=1,
    order_index=2,
    spell_icon_id=1463,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 570},
)


fury_164_tab = tab(
    id=164,
    name='Fury',
    class_mask=1,
    order_index=1,
    spell_icon_id=561,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 346},
)


granted_by_talent(
    id=121,
    tab=arms_161_tab,
    tier=2,
    column=3,
    ranks=[deep_wounds_12834, deep_wounds_12849, deep_wounds_12867],
    player_castable=False,
    depends_on={'talent_id': 662, 'rank': 1},
)


granted_by_talent(
    id=123,
    tab=arms_161_tab,
    tier=4,
    column=3,
    ranks=[12281, 12812, 12813, 12814, 12815],
    player_castable=False,
)


granted_by_talent(
    id=124,
    tab=arms_161_tab,
    tier=0,
    column=0,
    ranks=[improved_heroic_strike_12282, improved_heroic_strike_12663, improved_heroic_strike_12664],
    player_castable=False,
)


granted_by_talent(
    id=125,
    tab=arms_161_tab,
    tier=4,
    column=2,
    ranks=[12284, 12701, 12702, 12703, 12704],
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
    ranks=[improved_rend_12286, improved_rend_12658],
    player_castable=False,
)


granted_by_talent(
    id=128,
    tab=arms_161_tab,
    tier=1,
    column=2,
    ranks=[tactical_mastery_12295, tactical_mastery_12676, tactical_mastery_12677],
    player_castable=False,
)


granted_by_talent(
    id=129,
    tab=arms_161_tab,
    tier=5,
    column=2,
    ranks=[improved_hamstring_12289, improved_hamstring_12668, improved_hamstring_23695],
    player_castable=False,
)


granted_by_talent(
    id=130,
    tab=arms_161_tab,
    tier=0,
    column=1,
    ranks=[16462, 16463, 16464, 16465, 16466],
    player_castable=False,
)


granted_by_talent(
    id=131,
    tab=arms_161_tab,
    tier=2,
    column=0,
    ranks=[improved_overpower_12290, improved_overpower_12963],
    player_castable=False,
)


granted_by_talent(
    id=132,
    tab=arms_161_tab,
    tier=4,
    column=0,
    ranks=[12700, 12781, 12783, 12784, 12785],
    player_castable=False,
)


granted_by_talent(
    id=133,
    tab=arms_161_tab,
    tier=4,
    column=1,
    ranks=[sweeping_strikes_12328],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=134,
    tab=arms_161_tab,
    tier=5,
    column=0,
    ranks=[weapon_mastery_20504, 20505],
    player_castable=False,
)


granted_by_talent(
    id=135,
    tab=arms_161_tab,
    tier=6,
    column=1,
    ranks=[mortal_strike_12294],
    player_castable=False,
    depends_on={'talent_id': 133, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=136,
    tab=arms_161_tab,
    tier=3,
    column=1,
    ranks=[12163, 12711, 12712],
    player_castable=False,
)


granted_by_talent(
    id=137,
    tab=arms_161_tab,
    tier=2,
    column=1,
    ranks=[12296],
    player_castable=False,
    flags=1,
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
    column=1,
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
    ranks=[improved_disciplines_12312, improved_disciplines_12803],
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
    ranks=[commanding_presence_12318, commanding_presence_12857, commanding_presence_12858, commanding_presence_12860, commanding_presence_12861],
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
    ranks=[12319, 12971, 12972, 12973, 12974],
    player_castable=False,
)


granted_by_talent(
    id=157,
    tab=fury_164_tab,
    tier=0,
    column=2,
    ranks=[12320, 12852, 12853, 12855, 12856],
    player_castable=False,
)


granted_by_talent(
    id=158,
    tab=fury_164_tab,
    tier=0,
    column=1,
    ranks=[booming_voice_12321, booming_voice_12835],
    player_castable=False,
)


granted_by_talent(
    id=159,
    tab=fury_164_tab,
    tier=1,
    column=2,
    ranks=[12322, 12999, 13000, 13001, 13002],
    player_castable=False,
)


granted_by_talent(
    id=160,
    tab=fury_164_tab,
    tier=2,
    column=1,
    ranks=[piercing_howl_12323],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=161,
    tab=fury_164_tab,
    tier=1,
    column=1,
    ranks=[improved_demoralizing_shout_12324, improved_demoralizing_shout_12876, improved_demoralizing_shout_12877, improved_demoralizing_shout_12878, improved_demoralizing_shout_12879],
    player_castable=False,
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
    tier=2,
    column=0,
    ranks=[improved_cleave_12329, improved_cleave_12950, improved_cleave_20496],
    player_castable=False,
)


granted_by_talent(
    id=167,
    tab=fury_164_tab,
    tier=6,
    column=1,
    ranks=[bloodthirst_23881],
    player_castable=False,
    depends_on={'talent_id': 165, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=641,
    tab=arms_161_tab,
    tier=1,
    column=1,
    ranks=[12300, 12959, 12960],
    player_castable=False,
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
    id=1541,
    tab=fury_164_tab,
    tier=5,
    column=0,
    ranks=[improved_berserker_rage_20500, improved_berserker_rage_20501],
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
    id=1543,
    tab=fury_164_tab,
    tier=4,
    column=2,
    ranks=[improved_intercept_29888, improved_intercept_29889],
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
    id=1657,
    tab=fury_164_tab,
    tier=4,
    column=0,
    ranks=[29590, 29591, 29592],
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
    ranks=[rampage_29801],
    player_castable=False,
    depends_on={'talent_id': 167, 'rank': 0},
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
    column=1,
    ranks=[endless_rage_29623],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1662,
    tab=arms_161_tab,
    tier=8,
    column=0,
    ranks=[29723, 29725, 29724],
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
    ranks=[improved_mortal_strike_35446, improved_mortal_strike_35448, improved_mortal_strike_35449],
    player_castable=False,
    depends_on={'talent_id': 135, 'rank': 0},
)


granted_by_talent(
    id=1859,
    tab=arms_161_tab,
    tier=5,
    column=3,
    ranks=[46854, 46855],
    player_castable=False,
)


granted_by_talent(
    id=1860,
    tab=arms_161_tab,
    tier=7,
    column=2,
    ranks=[unrelenting_assault_46859, unrelenting_assault_46860],
    player_castable=False,
)


granted_by_talent(
    id=1862,
    tab=arms_161_tab,
    tier=6,
    column=2,
    ranks=[46865, 46866],
    player_castable=False,
)


granted_by_talent(
    id=1863,
    tab=arms_161_tab,
    tier=10,
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
    id=1865,
    tab=fury_164_tab,
    tier=7,
    column=0,
    ranks=[46910, 46911],
    player_castable=False,
)


granted_by_talent(
    id=1866,
    tab=fury_164_tab,
    tier=8,
    column=2,
    ranks=[bloodsurge_46913, bloodsurge_46914, bloodsurge_46915],
    player_castable=False,
    depends_on={'talent_id': 167, 'rank': 0},
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
    id=1868,
    tab=fury_164_tab,
    tier=8,
    column=0,
    ranks=[60970],
    player_castable=False,
    flags=1,
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
    column=0,
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
    ranks=[46867, 56611, 56612, 56613, 56614],
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
    id=2233,
    tab=arms_161_tab,
    tier=6,
    column=3,
    ranks=[improved_slam_12862, improved_slam_12330],
    player_castable=False,
)


granted_by_talent(
    id=2234,
    tab=fury_164_tab,
    tier=9,
    column=1,
    ranks=[unending_fury_56927, unending_fury_56929, unending_fury_56930, unending_fury_56931, unending_fury_56932],
    player_castable=False,
)


granted_by_talent(
    id=2246,
    tab=protection_163_tab,
    tier=9,
    column=1,
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
    ranks=[juggernaut_64976],
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
    ranks=[unbridled_wrath_200034, unbridled_wrath_200035, unbridled_wrath_200036],
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
    column=2,
    ranks=[shield_cover_200041, shield_cover_200042, shield_cover_200043],
    player_castable=False,
)


granted_by_talent(
    id=151,
    tab=protection_163_tab,
    tier=9,
    column=2,
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
    column=0,
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
    column=0,
    ranks=[reprisal_200056, reprisal_200057],
    player_castable=False,
)


granted_by_talent(
    id=60005,
    tab=protection_163_tab,
    tier=5,
    column=2,
    ranks=[storm_s_bulwark_200058, storm_s_bulwark_200059, storm_s_bulwark_200060],
    player_castable=False,
)


granted_by_talent(
    id=60006,
    tab=protection_163_tab,
    tier=8,
    column=1,
    ranks=[shield_discipline_200062, shield_discipline_200063],
    player_castable=False,
)
