"""
Paladin - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/paladin.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .paladin_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, scripted_by, tab
from .paladin_spells import avenger_s_shield_31935, beacon_of_light_53563, blade_of_justice_201400, blessing_of_sanctuary_20911, divine_illumination_31842, divine_sacrifice_64205, divine_storm_53385, execution_sentence_201410, hammer_of_the_righteous_53595, holy_shield_20925, holy_shock_20473, seal_of_vengeance_31801, wake_of_ashes_201413
from .paladin_trigger_spells import anticipation_20096, anticipation_20097, anticipation_20098, ardent_defender_31850, ardent_defender_31851, ardent_defender_31852, benediction_20101, benediction_20102, benediction_20103, blade_of_wrath_201457, blade_of_wrath_201458, blade_of_wrath_201459, blessed_hands_53660, blessed_hands_53661, combat_expertise_31858, combat_expertise_31859, combat_expertise_31860, conviction_20117, conviction_20118, conviction_20119, crusade_201463, crusade_201464, crusade_201465, crusaders_aegis_201460, crusaders_aegis_201461, crusaders_aegis_201462, divine_guardian_53527, divine_guardian_53530, divine_intellect_20257, divine_intellect_20258, divine_intellect_20259, divine_might_201443, divine_might_201444, divine_might_201445, divine_purpose_201471, divine_purpose_31871, divine_purpose_31872, divine_strength_20262, divine_strength_20263, divine_strength_20264, divinity_63646, divinity_63647, divinity_63648, enlightened_judgements_53556, enlightened_judgements_53557, eye_for_an_eye_201467, eye_for_an_eye_25988, eye_for_an_eye_9799, fanaticism_31879, fanaticism_31880, fanaticism_31881, guarded_by_the_light_53583, guarded_by_the_light_53585, guardian_s_favor_20174, guardian_s_favor_20175, healing_light_20237, healing_light_20238, healing_light_20239, heart_of_the_crusader_20335, heart_of_the_crusader_20336, heart_of_the_crusader_20337, holy_guidance_31837, holy_guidance_31838, holy_guidance_31839, holy_power_5923, holy_power_5924, holy_power_5925, illumination_20210, illumination_20212, illumination_20213, improved_blessing_of_might_20042, improved_blessing_of_might_20045, improved_blessing_of_wisdom_20244, improved_blessing_of_wisdom_20245, improved_concentration_aura_20254, improved_concentration_aura_20255, improved_concentration_aura_20256, improved_crusader_strike_201449, improved_crusader_strike_201450, improved_devotion_aura_20138, improved_devotion_aura_20139, improved_devotion_aura_20140, improved_hammer_of_justice_20487, improved_hammer_of_justice_20488, improved_judgements_201468, improved_judgements_25956, improved_judgements_25957, improved_lay_on_hands_20234, improved_lay_on_hands_20235, improved_righteous_fury_20468, improved_righteous_fury_20469, improved_righteous_fury_20470, infusion_of_light_53569, infusion_of_light_53576, judgements_of_the_just_53695, judgements_of_the_just_53696, judgements_of_the_pure_53671, judgements_of_the_pure_53673, judgements_of_the_pure_54151, judgements_of_the_wise_31876, judgements_of_the_wise_31877, light_s_grace_31833, light_s_grace_31835, light_s_grace_31836, one_handed_weapon_specialization_20196, one_handed_weapon_specialization_20197, one_handed_weapon_specialization_20198, pure_of_heart_31822, pure_of_heart_31823, purify_the_unclean_201451, purify_the_unclean_201452, purify_the_unclean_201453, purifying_power_31825, purifying_power_31826, pursuit_of_justice_26022, pursuit_of_justice_26023, redoubt_20127, redoubt_20130, redoubt_20135, righteous_vengeance_53380, righteous_vengeance_53381, righteous_vengeance_53382, sacred_cleansing_53551, sacred_cleansing_53552, sacred_cleansing_53553, sacred_duty_31848, sacred_duty_31849, sanctified_light_20359, sanctified_light_20360, sanctified_light_20361, sanctified_retribution_201469, sanctified_retribution_201470, sanctified_retribution_31869, sanctified_seals_201454, sanctified_seals_201455, sanctified_seals_201456, sanctified_wrath_53375, sanctified_wrath_53376, sanctity_of_battle_32043, sanctity_of_battle_35396, sanctity_of_battle_35397, sheath_of_light_53501, sheath_of_light_53502, sheath_of_light_53503, shield_of_the_templar_53709, shield_of_the_templar_53710, shield_of_the_templar_53711, smite_evil_31866, smite_evil_31867, smite_evil_31868, spiritual_attunement_31785, spiritual_attunement_33776, spiritual_focus_20205, spiritual_focus_20206, spiritual_focus_20207, stoicism_31844, stoicism_31845, stoicism_53519, strength_of_faith_201446, strength_of_faith_201447, strength_of_faith_201448, swift_retribution_53379, swift_retribution_53484, swift_retribution_53648, the_art_of_war_201472, the_art_of_war_53486, the_art_of_war_53488, touched_by_the_light_53590, touched_by_the_light_53591, touched_by_the_light_53592, toughness_20143, toughness_20144, toughness_20145, two_handed_weapon_specialization_20111, two_handed_weapon_specialization_20112, two_handed_weapon_specialization_20113, unyielding_faith_25836, unyielding_faith_9453, vengeance_20049, vengeance_20056, vengeance_20057, vindication_201466, vindication_26016, vindication_9452, zeal_201440, zeal_201441, zeal_201442
from .paladin_holy_ranks import a_new_dawn_r1_201240, a_new_dawn_r2_201241, a_new_dawn_r3_201242, blessed_crusade_r1_201257, blessed_crusade_r2_201258, blessed_crusade_r3_201259, blessed_hands_talent_r3_201278, dawn_before_dusk_talent_r1_201262, dawn_before_dusk_talent_r2_201263, dawn_before_dusk_talent_r3_201264, enduring_light_r1_201243, enduring_light_r2_201244, enduring_light_r3_201245, glimmer_of_light_talent_r1_201268, glimmer_of_light_talent_r2_201269, glimmer_of_light_talent_r3_201270, illuminated_steel_r1_201246, illuminated_steel_r2_201247, illuminated_steel_r3_201248, light_s_fervor_r1_201260, light_s_fervor_r2_201261, merciful_strikes_talent_r1_201249, merciful_strikes_talent_r2_201250, merciful_strikes_talent_r3_201251, overflowing_light_talent_r1_201274, overflowing_light_talent_r2_201275, overflowing_light_talent_r3_201276, pure_of_heart_talent_r3_201279, radiant_exorcism_talent_r1_201265, radiant_exorcism_talent_r2_201266, radiant_exorcism_talent_r3_201267, shock_and_awe_talent_r1_201271, shock_and_awe_talent_r2_201272, shock_and_awe_talent_r3_201273, sunlight_talent_r1_201254, sunlight_talent_r2_201255, sunlight_talent_r3_201256, unyielding_faith_r3_201277, zealous_exorcism_r1_201252, zealous_exorcism_r2_201253
from .paladin_holy_spells import divine_toll_201203, light_s_hammer_201200
from .paladin_prot_ranks import avenging_light_201353, avenging_light_201354, avenging_light_201355, bulwark_of_faith_201346, bulwark_of_faith_201347, consecrated_shield_201335, consecrated_shield_201336, improved_auras_201320, improved_auras_201321, improved_auras_201322, improved_blessing_of_sanctuary_201337, improved_blessing_of_sanctuary_201338, improved_consecration_201323, improved_consecration_201324, improved_consecration_201325, improved_hammer_of_the_righteous_201331, improved_hammer_of_the_righteous_201332, improved_seal_of_command_201329, improved_seal_of_command_201330, inner_light_201348, inner_light_201349, inner_light_201350, lights_defender_201351, lights_defender_201352, lights_reservoir_201333, lights_reservoir_201334, radiant_bulwark_201343, radiant_bulwark_201344, radiant_bulwark_201345, sanctified_resolve_201326, sanctified_resolve_201327, sanctified_resolve_201328, shield_discipline_201339, shield_discipline_201340, vengeful_bulwark_201341, vengeful_bulwark_201342
from .paladin_prot_spells import guardian_of_ancient_kings_201356


retribution_381_tab = tab(
    id=381,
    name='Retribution',
    class_mask=2,
    order_index=2,
    spell_icon_id=555,
    skill_line=184,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'PaladinCombat'},
)


holy_382_tab = tab(
    id=382,
    name='Holy',
    class_mask=2,
    skill_line=594,
    spell_icon_id=70,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'PaladinHoly'},
)


protection_383_tab = tab(
    id=383,
    name='Protection',
    class_mask=2,
    order_index=1,
    skill_line=267,
    spell_icon_id=291,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 'PaladinProtection'},
)


# ---------------------------------------------------------------------------
# Protection tab 383 - paladin-rework S3 (PROTECTION §2.2 / §5). 36 talents, 84 points, no prerequisite arrows (B6).
# Kept+moved, repurposed in place (1748, 1425, 1521, 1426, 2194, 2200, 1423, 2195) and minted (60125-60132, 60150, 60151).
# Castable-teaching rows keep flags=1 (2196, 1430, 1431, 1754, 2280, 60151); 60151 bundles SkillLineAbility 30520.
# ---------------------------------------------------------------------------


granted_by_talent(
    id=60125,
    tab=protection_383_tab,
    tier=0,
    column=0,
    ranks=[improved_auras_201320, improved_auras_201321, improved_auras_201322],
    player_castable=False,
)


granted_by_talent(
    id=60126,
    tab=protection_383_tab,
    tier=0,
    column=1,
    ranks=[improved_consecration_201323, improved_consecration_201324, improved_consecration_201325],
    player_castable=False,
)


granted_by_talent(
    id=2185,
    tab=protection_383_tab,
    tier=0,
    column=2,
    ranks=[divine_strength_20262, divine_strength_20263, divine_strength_20264],
    player_castable=False,
)


granted_by_talent(
    id=1753,
    tab=protection_383_tab,
    tier=0,
    column=3,
    ranks=[combat_expertise_31858, combat_expertise_31859, combat_expertise_31860],
    player_castable=False,
)


granted_by_talent(
    id=1748,
    tab=protection_383_tab,
    tier=1,
    column=0,
    ranks=[sanctified_resolve_201326, sanctified_resolve_201327, sanctified_resolve_201328],
    player_castable=False,
)


granted_by_talent(
    id=1425,
    tab=protection_383_tab,
    tier=1,
    column=1,
    ranks=[improved_seal_of_command_201329, improved_seal_of_command_201330],
    player_castable=False,
)


granted_by_talent(
    id=1629,
    tab=protection_383_tab,
    tier=1,
    column=2,
    ranks=[anticipation_20096, anticipation_20097, anticipation_20098],
    player_castable=False,
)


granted_by_talent(
    id=2282,
    tab=protection_383_tab,
    tier=1,
    column=3,
    ranks=[spiritual_attunement_31785, spiritual_attunement_33776],
    player_castable=False,
)


granted_by_talent(
    id=2196,
    tab=protection_383_tab,
    tier=2,
    column=1,
    ranks=[hammer_of_the_righteous_53595],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1501,
    tab=protection_383_tab,
    tier=2,
    column=2,
    ranks=[improved_righteous_fury_20468, improved_righteous_fury_20469, improved_righteous_fury_20470],
    player_castable=False,
)


granted_by_talent(
    id=1423,
    tab=protection_383_tab,
    tier=2,
    column=3,
    ranks=[toughness_20143, toughness_20144, toughness_20145],
    player_castable=False,
)


granted_by_talent(
    id=60127,
    tab=protection_383_tab,
    tier=3,
    column=0,
    ranks=[improved_hammer_of_the_righteous_201331, improved_hammer_of_the_righteous_201332],
    player_castable=False,
)


granted_by_talent(
    id=1521,
    tab=protection_383_tab,
    tier=3,
    column=1,
    ranks=[lights_reservoir_201333, lights_reservoir_201334],
    player_castable=False,
)


granted_by_talent(
    id=1422,
    tab=protection_383_tab,
    tier=3,
    column=2,
    ranks=[improved_devotion_aura_20138, improved_devotion_aura_20139, improved_devotion_aura_20140],
    player_castable=False,
)


granted_by_talent(
    id=1431,
    tab=protection_383_tab,
    tier=4,
    column=0,
    ranks=[blessing_of_sanctuary_20911],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1430,
    tab=protection_383_tab,
    tier=4,
    column=1,
    ranks=[holy_shield_20925],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1426,
    tab=protection_383_tab,
    tier=4,
    column=2,
    ranks=[consecrated_shield_201335, consecrated_shield_201336],
    player_castable=False,
)


granted_by_talent(
    id=60128,
    tab=protection_383_tab,
    tier=4,
    column=3,
    ranks=[improved_blessing_of_sanctuary_201337, improved_blessing_of_sanctuary_201338],
    player_castable=False,
)


granted_by_talent(
    id=2195,
    tab=protection_383_tab,
    tier=5,
    column=0,
    ranks=[touched_by_the_light_53590, touched_by_the_light_53591, touched_by_the_light_53592],
    player_castable=False,
)


granted_by_talent(
    id=1421,
    tab=protection_383_tab,
    tier=5,
    column=1,
    ranks=[redoubt_20127, redoubt_20130, redoubt_20135],
    player_castable=False,
)


granted_by_talent(
    id=1750,
    tab=protection_383_tab,
    tier=5,
    column=2,
    ranks=[sacred_duty_31848, sacred_duty_31849],
    player_castable=False,
)


granted_by_talent(
    id=60129,
    tab=protection_383_tab,
    tier=5,
    column=3,
    ranks=[shield_discipline_201339, shield_discipline_201340],
    player_castable=False,
)


granted_by_talent(
    id=1442,
    tab=protection_383_tab,
    tier=6,
    column=0,
    ranks=[divinity_63646, divinity_63647, divinity_63648],
    player_castable=False,
)


granted_by_talent(
    id=1754,
    tab=protection_383_tab,
    tier=6,
    column=1,
    ranks=[avenger_s_shield_31935],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1751,
    tab=protection_383_tab,
    tier=6,
    column=2,
    ranks=[ardent_defender_31850, ardent_defender_31851, ardent_defender_31852],
    player_castable=False,
)


granted_by_talent(
    id=1429,
    tab=protection_383_tab,
    tier=7,
    column=0,
    ranks=[one_handed_weapon_specialization_20196, one_handed_weapon_specialization_20197, one_handed_weapon_specialization_20198],
    player_castable=False,
)


granted_by_talent(
    id=60130,
    tab=protection_383_tab,
    tier=7,
    column=1,
    ranks=[vengeful_bulwark_201341, vengeful_bulwark_201342],
    player_castable=False,
)


granted_by_talent(
    id=60131,
    tab=protection_383_tab,
    tier=8,
    column=0,
    ranks=[radiant_bulwark_201343, radiant_bulwark_201344, radiant_bulwark_201345],
    player_castable=False,
)


granted_by_talent(
    id=2280,
    tab=protection_383_tab,
    tier=8,
    column=1,
    ranks=[divine_sacrifice_64205],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2194,
    tab=protection_383_tab,
    tier=8,
    column=2,
    ranks=[bulwark_of_faith_201346, bulwark_of_faith_201347],
    player_castable=False,
)


granted_by_talent(
    id=60132,
    tab=protection_383_tab,
    tier=8,
    column=3,
    ranks=[inner_light_201348, inner_light_201349, inner_light_201350],
    player_castable=False,
)


granted_by_talent(
    id=2204,
    tab=protection_383_tab,
    tier=9,
    column=0,
    ranks=[shield_of_the_templar_53709, shield_of_the_templar_53710, shield_of_the_templar_53711],
    player_castable=False,
)


granted_by_talent(
    id=60150,
    tab=protection_383_tab,
    tier=9,
    column=1,
    ranks=[lights_defender_201351, lights_defender_201352],
    player_castable=False,
)


granted_by_talent(
    id=2200,
    tab=protection_383_tab,
    tier=9,
    column=2,
    ranks=[avenging_light_201353, avenging_light_201354, avenging_light_201355],
    player_castable=False,
)


granted_by_talent(
    id=2281,
    tab=protection_383_tab,
    tier=9,
    column=3,
    ranks=[divine_guardian_53527, divine_guardian_53530],
    player_castable=False,
)


granted_by_talent(
    id=60151,
    tab=protection_383_tab,
    tier=10,
    column=1,
    ranks=[guardian_of_ancient_kings_201356],
    player_castable=True,
    skill_line_ability_ids=[30520],
    flags=1,
)


# ---------------------------------------------------------------------------
# Retribution tab 381 - paladin-rework S1 (RETRIBUTION §2.2 / §5). 35 talents, 90 points, no prerequisite arrows (B6).
# Repurposed rows: 1403 Deflection -> Divine Might, 1481 Seal of Command -> Seal of Vengeance, 1441 Repentance -> Blade of Justice,
# 1823 Crusader Strike -> Execution Sentence, 1755 Crusade -> Smite Evil. Minted: 60133-60141. 20375 / 20066 / 35395 leave the tree
# (baseline, SHARED); orphaned ranks (20060-64, 20104/05, 20120/21, 31878) are left out of every chain.
# Castable-teaching rows keep flags=1; SkillLineAbility 30530-30532 are bundled here for 201400 / 201410 / 201413.
# ---------------------------------------------------------------------------


granted_by_talent(
    id=60133,
    tab=retribution_381_tab,
    tier=0,
    column=0,
    ranks=[zeal_201440, zeal_201441, zeal_201442],
    player_castable=False,
)


granted_by_talent(
    id=1403,
    tab=retribution_381_tab,
    tier=0,
    column=1,
    ranks=[divine_might_201443, divine_might_201444, divine_might_201445],
    player_castable=False,
)


granted_by_talent(
    id=60134,
    tab=retribution_381_tab,
    tier=0,
    column=2,
    ranks=[strength_of_faith_201446, strength_of_faith_201447, strength_of_faith_201448],
    player_castable=False,
)


granted_by_talent(
    id=1407,
    tab=retribution_381_tab,
    tier=0,
    column=3,
    ranks=[benediction_20101, benediction_20102, benediction_20103],
    player_castable=False,
)


granted_by_talent(
    id=1464,
    tab=retribution_381_tab,
    tier=1,
    column=0,
    ranks=[heart_of_the_crusader_20335, heart_of_the_crusader_20336, heart_of_the_crusader_20337],
    player_castable=False,
)


granted_by_talent(
    id=60135,
    tab=retribution_381_tab,
    tier=1,
    column=1,
    ranks=[improved_crusader_strike_201449, improved_crusader_strike_201450],
    player_castable=False,
)


granted_by_talent(
    id=1755,
    tab=retribution_381_tab,
    tier=1,
    column=2,
    ranks=[smite_evil_31866, smite_evil_31867, smite_evil_31868],
    player_castable=False,
)


granted_by_talent(
    id=1401,
    tab=retribution_381_tab,
    tier=1,
    column=3,
    ranks=[improved_blessing_of_might_20042, improved_blessing_of_might_20045],
    player_castable=False,
)


granted_by_talent(
    id=1411,
    tab=retribution_381_tab,
    tier=2,
    column=0,
    ranks=[conviction_20117, conviction_20118, conviction_20119],
    player_castable=False,
)


granted_by_talent(
    id=1481,
    tab=retribution_381_tab,
    tier=2,
    column=1,
    ranks=[seal_of_vengeance_31801],
    player_castable=True,
    flags=1,
)


granted_by_talent(
    id=1634,
    tab=retribution_381_tab,
    tier=2,
    column=3,
    ranks=[pursuit_of_justice_26022, pursuit_of_justice_26023],
    player_castable=False,
)


granted_by_talent(
    id=60136,
    tab=retribution_381_tab,
    tier=3,
    column=0,
    ranks=[purify_the_unclean_201451, purify_the_unclean_201452, purify_the_unclean_201453],
    player_castable=False,
)


granted_by_talent(
    id=1633,
    tab=retribution_381_tab,
    tier=3,
    column=1,
    ranks=[vindication_9452, vindication_26016, vindication_201466],
    player_castable=False,
)


granted_by_talent(
    id=1761,
    tab=retribution_381_tab,
    tier=3,
    column=2,
    ranks=[sanctity_of_battle_32043, sanctity_of_battle_35396, sanctity_of_battle_35397],
    player_castable=False,
)


granted_by_talent(
    id=1632,
    tab=retribution_381_tab,
    tier=3,
    column=3,
    ranks=[eye_for_an_eye_9799, eye_for_an_eye_25988, eye_for_an_eye_201467],
    player_castable=False,
)


granted_by_talent(
    id=1631,
    tab=retribution_381_tab,
    tier=4,
    column=0,
    ranks=[improved_judgements_25956, improved_judgements_25957, improved_judgements_201468],
    player_castable=False,
)


granted_by_talent(
    id=1441,
    tab=retribution_381_tab,
    tier=4,
    column=1,
    ranks=[blade_of_justice_201400],
    player_castable=True,
    skill_line_ability_ids=[30530],
    flags=1,
)


granted_by_talent(
    id=2179,
    tab=retribution_381_tab,
    tier=4,
    column=2,
    ranks=[sheath_of_light_53501, sheath_of_light_53502, sheath_of_light_53503],
    player_castable=False,
)


granted_by_talent(
    id=1756,
    tab=retribution_381_tab,
    tier=4,
    column=3,
    ranks=[sanctified_retribution_31869, sanctified_retribution_201469, sanctified_retribution_201470],
    player_castable=False,
)


granted_by_talent(
    id=60137,
    tab=retribution_381_tab,
    tier=5,
    column=0,
    ranks=[sanctified_seals_201454, sanctified_seals_201455, sanctified_seals_201456],
    player_castable=False,
)


granted_by_talent(
    id=1410,
    tab=retribution_381_tab,
    tier=5,
    column=1,
    ranks=[two_handed_weapon_specialization_20111, two_handed_weapon_specialization_20112, two_handed_weapon_specialization_20113],
    player_castable=False,
)


granted_by_talent(
    id=1402,
    tab=retribution_381_tab,
    tier=5,
    column=2,
    ranks=[vengeance_20049, vengeance_20056, vengeance_20057],
    player_castable=False,
)


granted_by_talent(
    id=1757,
    tab=retribution_381_tab,
    tier=5,
    column=3,
    ranks=[divine_purpose_31871, divine_purpose_31872, divine_purpose_201471],
    player_castable=False,
)


granted_by_talent(
    id=1758,
    tab=retribution_381_tab,
    tier=6,
    column=0,
    ranks=[judgements_of_the_wise_31876, judgements_of_the_wise_31877],
    player_castable=False,
)


granted_by_talent(
    id=2150,
    tab=retribution_381_tab,
    tier=6,
    column=1,
    ranks=[divine_storm_53385],
    player_castable=True,
    flags=1,
)


granted_by_talent(
    id=60138,
    tab=retribution_381_tab,
    tier=6,
    column=3,
    ranks=[blade_of_wrath_201457, blade_of_wrath_201458, blade_of_wrath_201459],
    player_castable=False,
)


granted_by_talent(
    id=2176,
    tab=retribution_381_tab,
    tier=7,
    column=1,
    ranks=[the_art_of_war_53486, the_art_of_war_53488, the_art_of_war_201472],
    player_castable=False,
)


granted_by_talent(
    id=2147,
    tab=retribution_381_tab,
    tier=7,
    column=2,
    ranks=[sanctified_wrath_53375, sanctified_wrath_53376],
    player_castable=False,
)


granted_by_talent(
    id=1759,
    tab=retribution_381_tab,
    tier=8,
    column=0,
    ranks=[fanaticism_31879, fanaticism_31880, fanaticism_31881],
    player_castable=False,
)


granted_by_talent(
    id=1823,
    tab=retribution_381_tab,
    tier=8,
    column=1,
    ranks=[execution_sentence_201410],
    player_castable=True,
    skill_line_ability_ids=[30531],
    flags=1,
)


granted_by_talent(
    id=2148,
    tab=retribution_381_tab,
    tier=8,
    column=2,
    ranks=[swift_retribution_53379, swift_retribution_53484, swift_retribution_53648],
    player_castable=False,
)


granted_by_talent(
    id=60139,
    tab=retribution_381_tab,
    tier=8,
    column=3,
    ranks=[crusaders_aegis_201460, crusaders_aegis_201461, crusaders_aegis_201462],
    player_castable=False,
)


granted_by_talent(
    id=60140,
    tab=retribution_381_tab,
    tier=9,
    column=0,
    ranks=[crusade_201463, crusade_201464, crusade_201465],
    player_castable=False,
)


granted_by_talent(
    id=2149,
    tab=retribution_381_tab,
    tier=9,
    column=1,
    ranks=[righteous_vengeance_53380, righteous_vengeance_53381, righteous_vengeance_53382],
    player_castable=False,
)


granted_by_talent(
    id=60141,
    tab=retribution_381_tab,
    tier=10,
    column=1,
    ranks=[wake_of_ashes_201413],
    player_castable=True,
    skill_line_ability_ids=[30532],
    flags=1,
)


# ---------------------------------------------------------------------------
# Holy tab 382 - paladin-rework S2 (HOLY §2.2 / §5). 37 talents, 94 points, no prerequisite arrows (B6).
# Repurposed rows: 1463 Seals of the Pure -> Zealous Exorcism, 1435 Aura Mastery -> Light's Hammer, 1433 Divine Favor -> Divine Toll,
# 1744 Blessed Life -> Enduring Light. Minted: 60110-60120. Orphaned ranks (20208/09, 20214/15, 20260/61, 5926/25829, 31840/41,
# 54154/55) are left out of every chain. SkillLineAbility 30510 / 30511 are bundled for Light's Hammer / Divine Toll.
# ---------------------------------------------------------------------------


granted_by_talent(
    id=60110,
    tab=holy_382_tab,
    tier=0,
    column=0,
    ranks=[a_new_dawn_r1_201240, a_new_dawn_r2_201241, a_new_dawn_r3_201242],
    player_castable=False,
)



granted_by_talent(
    id=1432,
    tab=holy_382_tab,
    tier=0,
    column=1,
    ranks=[spiritual_focus_20205, spiritual_focus_20206, spiritual_focus_20207],
    player_castable=False,
)



granted_by_talent(
    id=1744,
    tab=holy_382_tab,
    tier=0,
    column=2,
    ranks=[enduring_light_r1_201243, enduring_light_r2_201244, enduring_light_r3_201245],
    player_castable=False,
)



granted_by_talent(
    id=60111,
    tab=holy_382_tab,
    tier=0,
    column=3,
    ranks=[illuminated_steel_r1_201246, illuminated_steel_r2_201247, illuminated_steel_r3_201248],
    player_castable=False,
)



granted_by_talent(
    id=1444,
    tab=holy_382_tab,
    tier=1,
    column=0,
    ranks=[healing_light_20237, healing_light_20238, healing_light_20239],
    player_castable=False,
)



granted_by_talent(
    id=1449,
    tab=holy_382_tab,
    tier=1,
    column=1,
    ranks=[divine_intellect_20257, divine_intellect_20258, divine_intellect_20259],
    player_castable=False,
)



granted_by_talent(
    id=1628,
    tab=holy_382_tab,
    tier=1,
    column=2,
    ranks=[unyielding_faith_9453, unyielding_faith_25836, unyielding_faith_r3_201277],
    player_castable=False,
)



granted_by_talent(
    id=60112,
    tab=holy_382_tab,
    tier=1,
    column=3,
    ranks=[merciful_strikes_talent_r1_201249, merciful_strikes_talent_r2_201250, merciful_strikes_talent_r3_201251],
    player_castable=False,
)



granted_by_talent(
    id=1461,
    tab=holy_382_tab,
    tier=2,
    column=0,
    ranks=[illumination_20210, illumination_20212, illumination_20213],
    player_castable=False,
)



granted_by_talent(
    id=1435,
    tab=holy_382_tab,
    tier=2,
    column=1,
    ranks=[light_s_hammer_201200],
    player_castable=True,
    skill_line_ability_ids=[30510],
    flags=1,
)



granted_by_talent(
    id=1443,
    tab=holy_382_tab,
    tier=2,
    column=2,
    ranks=[improved_lay_on_hands_20234, improved_lay_on_hands_20235],
    player_castable=False,
)



granted_by_talent(
    id=1463,
    tab=holy_382_tab,
    tier=2,
    column=3,
    ranks=[zealous_exorcism_r1_201252, zealous_exorcism_r2_201253],
    player_castable=False,
)



granted_by_talent(
    id=1450,
    tab=holy_382_tab,
    tier=3,
    column=0,
    ranks=[improved_concentration_aura_20254, improved_concentration_aura_20255, improved_concentration_aura_20256],
    player_castable=False,
)



granted_by_talent(
    id=2198,
    tab=holy_382_tab,
    tier=3,
    column=1,
    ranks=[blessed_hands_53660, blessed_hands_53661, blessed_hands_talent_r3_201278],
    player_castable=False,
)



granted_by_talent(
    id=1446,
    tab=holy_382_tab,
    tier=3,
    column=2,
    ranks=[improved_blessing_of_wisdom_20244, improved_blessing_of_wisdom_20245],
    player_castable=False,
)



granted_by_talent(
    id=60113,
    tab=holy_382_tab,
    tier=3,
    column=3,
    ranks=[sunlight_talent_r1_201254, sunlight_talent_r2_201255, sunlight_talent_r3_201256],
    player_castable=False,
)



granted_by_talent(
    id=1742,
    tab=holy_382_tab,
    tier=4,
    column=0,
    ranks=[pure_of_heart_31822, pure_of_heart_31823, pure_of_heart_talent_r3_201279],
    player_castable=False,
)



granted_by_talent(
    id=1502,
    tab=holy_382_tab,
    tier=4,
    column=1,
    ranks=[holy_shock_20473],
    player_castable=False,
    flags=1,
)



granted_by_talent(
    id=1465,
    tab=holy_382_tab,
    tier=4,
    column=2,
    ranks=[sanctified_light_20359, sanctified_light_20360, sanctified_light_20361],
    player_castable=False,
)



granted_by_talent(
    id=60114,
    tab=holy_382_tab,
    tier=4,
    column=3,
    ranks=[blessed_crusade_r1_201257, blessed_crusade_r2_201258, blessed_crusade_r3_201259],
    player_castable=False,
)



granted_by_talent(
    id=60115,
    tab=holy_382_tab,
    tier=5,
    column=1,
    ranks=[light_s_fervor_r1_201260, light_s_fervor_r2_201261],
    player_castable=False,
)



granted_by_talent(
    id=1627,
    tab=holy_382_tab,
    tier=5,
    column=2,
    ranks=[holy_power_5923, holy_power_5924, holy_power_5925],
    player_castable=False,
)



granted_by_talent(
    id=1743,
    tab=holy_382_tab,
    tier=5,
    column=3,
    ranks=[purifying_power_31825, purifying_power_31826],
    player_castable=False,
)



granted_by_talent(
    id=1745,
    tab=holy_382_tab,
    tier=6,
    column=0,
    ranks=[light_s_grace_31833, light_s_grace_31835, light_s_grace_31836],
    player_castable=False,
)



granted_by_talent(
    id=1747,
    tab=holy_382_tab,
    tier=6,
    column=1,
    ranks=[divine_illumination_31842],
    player_castable=False,
    flags=1,
)



granted_by_talent(
    id=60116,
    tab=holy_382_tab,
    tier=6,
    column=2,
    ranks=[dawn_before_dusk_talent_r1_201262, dawn_before_dusk_talent_r2_201263, dawn_before_dusk_talent_r3_201264],
    player_castable=False,
)



granted_by_talent(
    id=60117,
    tab=holy_382_tab,
    tier=6,
    column=3,
    ranks=[radiant_exorcism_talent_r1_201265, radiant_exorcism_talent_r2_201266, radiant_exorcism_talent_r3_201267],
    player_castable=False,
)



granted_by_talent(
    id=2190,
    tab=holy_382_tab,
    tier=7,
    column=0,
    ranks=[sacred_cleansing_53551, sacred_cleansing_53552, sacred_cleansing_53553],
    player_castable=False,
)



granted_by_talent(
    id=60118,
    tab=holy_382_tab,
    tier=7,
    column=1,
    ranks=[glimmer_of_light_talent_r1_201268, glimmer_of_light_talent_r2_201269, glimmer_of_light_talent_r3_201270],
    player_castable=False,
)



granted_by_talent(
    id=1746,
    tab=holy_382_tab,
    tier=7,
    column=2,
    ranks=[holy_guidance_31837, holy_guidance_31838, holy_guidance_31839],
    player_castable=False,
)



granted_by_talent(
    id=60119,
    tab=holy_382_tab,
    tier=7,
    column=3,
    ranks=[shock_and_awe_talent_r1_201271, shock_and_awe_talent_r2_201272, shock_and_awe_talent_r3_201273],
    player_castable=False,
)



granted_by_talent(
    id=60120,
    tab=holy_382_tab,
    tier=8,
    column=0,
    ranks=[overflowing_light_talent_r1_201274, overflowing_light_talent_r2_201275, overflowing_light_talent_r3_201276],
    player_castable=False,
)



granted_by_talent(
    id=2192,
    tab=holy_382_tab,
    tier=8,
    column=1,
    ranks=[beacon_of_light_53563],
    player_castable=False,
    flags=1,
)



granted_by_talent(
    id=2199,
    tab=holy_382_tab,
    tier=8,
    column=3,
    ranks=[judgements_of_the_pure_53671, judgements_of_the_pure_53673, judgements_of_the_pure_54151],
    player_castable=False,
)



granted_by_talent(
    id=2193,
    tab=holy_382_tab,
    tier=9,
    column=1,
    ranks=[infusion_of_light_53569, infusion_of_light_53576],
    player_castable=False,
)



granted_by_talent(
    id=2191,
    tab=holy_382_tab,
    tier=9,
    column=3,
    ranks=[enlightened_judgements_53556, enlightened_judgements_53557],
    player_castable=False,
)



granted_by_talent(
    id=1433,
    tab=holy_382_tab,
    tier=10,
    column=1,
    ranks=[divine_toll_201203],
    player_castable=True,
    skill_line_ability_ids=[30511],
    flags=1,
)


# ---------------------------------------------------------------------------
# Holy bindings on spells no phase-1 file binds (HOLY §5.1 / §2.7). All additive: stock bindings on these ids stay, and
# 879 keeps spell_pal_seal_builder (bound in paladin_spells.py).
# ---------------------------------------------------------------------------

# Blessed Hands capstone (201238): Hand of Protection / Salvation / Freedom / Sacrifice.
for _hand in (1022, 1038, 1044, 6940):
    scripted_by(_hand, 'spell_pal_blessed_hands_capstone')
# Pure of Heart mana + Sacred Cleansing capstone Glimmer: Cleanse / Purify.
for _cleanse in (4987, 1152):
    scripted_by(_cleanse, 'spell_pal_cleanse_holy')
scripted_by(879, 'spell_pal_exorcism_radiant')  # Radiant Exorcism capstone cleave
scripted_by(25780, 'spell_pal_righteous_fury_shock_and_awe')  # Shock and Awe's threat reduction, beside the stock class
