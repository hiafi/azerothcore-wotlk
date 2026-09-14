"""
Paladin - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/paladin.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .paladin_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, tab
from .paladin_spells import aura_mastery_31821, avenger_s_shield_31935, beacon_of_light_53563, blessing_of_sanctuary_20911, crusader_strike_35395, divine_favor_20216, divine_illumination_31842, divine_sacrifice_64205, divine_storm_53385, hammer_of_the_righteous_53595, holy_shield_20925, holy_shock_20473, repentance_20066, seal_of_command_20375
from .paladin_trigger_spells import ardent_defender_31850, ardent_defender_31851, ardent_defender_31852, benediction_20101, benediction_20102, benediction_20103, benediction_20104, benediction_20105, blessed_hands_53660, blessed_hands_53661, blessed_life_31828, blessed_life_31829, blessed_life_31830, combat_expertise_31858, combat_expertise_31859, combat_expertise_31860, divine_guardian_53527, divine_guardian_53530, enlightened_judgements_53556, enlightened_judgements_53557, fanaticism_31879, fanaticism_31880, fanaticism_31881, guarded_by_the_light_53583, guarded_by_the_light_53585, guardian_s_favor_20174, guardian_s_favor_20175, healing_light_20237, healing_light_20238, healing_light_20239, heart_of_the_crusader_20335, heart_of_the_crusader_20336, heart_of_the_crusader_20337, holy_guidance_31837, holy_guidance_31838, holy_guidance_31839, holy_guidance_31840, holy_guidance_31841, illumination_20210, illumination_20212, illumination_20213, illumination_20214, illumination_20215, improved_blessing_of_might_20042, improved_blessing_of_might_20045, improved_blessing_of_wisdom_20244, improved_blessing_of_wisdom_20245, improved_concentration_aura_20254, improved_concentration_aura_20255, improved_concentration_aura_20256, improved_devotion_aura_20138, improved_devotion_aura_20139, improved_devotion_aura_20140, improved_hammer_of_justice_20487, improved_hammer_of_justice_20488, improved_judgements_25956, improved_judgements_25957, improved_lay_on_hands_20234, improved_lay_on_hands_20235, improved_righteous_fury_20468, improved_righteous_fury_20469, improved_righteous_fury_20470, infusion_of_light_53569, infusion_of_light_53576, judgements_of_the_just_53695, judgements_of_the_just_53696, judgements_of_the_pure_53671, judgements_of_the_pure_53673, judgements_of_the_pure_54151, judgements_of_the_pure_54154, judgements_of_the_pure_54155, judgements_of_the_wise_31876, judgements_of_the_wise_31877, judgements_of_the_wise_31878, light_s_grace_31833, light_s_grace_31835, light_s_grace_31836, pure_of_heart_31822, pure_of_heart_31823, purifying_power_31825, purifying_power_31826, righteous_vengeance_53380, righteous_vengeance_53381, righteous_vengeance_53382, sacred_cleansing_53551, sacred_cleansing_53552, sacred_cleansing_53553, sacred_duty_31848, sacred_duty_31849, sanctified_light_20359, sanctified_light_20360, sanctified_light_20361, sanctified_retribution_31869, sanctified_wrath_53375, sanctified_wrath_53376, sanctity_of_battle_32043, sanctity_of_battle_35396, sanctity_of_battle_35397, seals_of_the_pure_20224, seals_of_the_pure_20225, seals_of_the_pure_20330, seals_of_the_pure_20331, seals_of_the_pure_20332, sheath_of_light_53501, sheath_of_light_53502, sheath_of_light_53503, shield_of_the_templar_53709, shield_of_the_templar_53710, shield_of_the_templar_53711, spiritual_attunement_31785, spiritual_attunement_33776, spiritual_focus_20205, spiritual_focus_20206, spiritual_focus_20207, spiritual_focus_20208, spiritual_focus_20209, stoicism_31844, stoicism_31845, stoicism_53519, swift_retribution_53379, swift_retribution_53484, swift_retribution_53648, the_art_of_war_53486, the_art_of_war_53488, touched_by_the_light_53590, touched_by_the_light_53591, touched_by_the_light_53592


retribution_381_tab = tab(
    id=381,
    name='Retribution',
    class_mask=2,
    order_index=2,
    spell_icon_id=555,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 745},
)


holy_382_tab = tab(
    id=382,
    name='Holy',
    class_mask=2,
    spell_icon_id=70,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 213},
)


protection_383_tab = tab(
    id=383,
    name='Protection',
    class_mask=2,
    order_index=1,
    spell_icon_id=291,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 519},
)


granted_by_talent(
    id=1401,
    tab=retribution_381_tab,
    tier=1,
    column=2,
    ranks=[improved_blessing_of_might_20042, improved_blessing_of_might_20045],
    player_castable=False,
)


granted_by_talent(
    id=1402,
    tab=retribution_381_tab,
    tier=5,
    column=1,
    ranks=[20049, 20056, 20057],
    player_castable=False,
    depends_on={'talent_id': 1411, 'rank': 4},
)


granted_by_talent(
    id=1403,
    tab=retribution_381_tab,
    tier=0,
    column=1,
    ranks=[20060, 20061, 20062, 20063, 20064],
    player_castable=False,
)


granted_by_talent(
    id=1407,
    tab=retribution_381_tab,
    tier=0,
    column=2,
    ranks=[benediction_20101, benediction_20102, benediction_20103, benediction_20104, benediction_20105],
    player_castable=False,
)


granted_by_talent(
    id=1410,
    tab=retribution_381_tab,
    tier=4,
    column=0,
    ranks=[20111, 20112, 20113],
    player_castable=False,
)


granted_by_talent(
    id=1411,
    tab=retribution_381_tab,
    tier=2,
    column=1,
    ranks=[20117, 20118, 20119, 20120, 20121],
    player_castable=False,
)


granted_by_talent(
    id=1421,
    tab=protection_383_tab,
    tier=7,
    column=0,
    ranks=[20127, 20130, 20135],
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
    id=1423,
    tab=protection_383_tab,
    tier=2,
    column=2,
    ranks=[20143, 20144, 20145, 20146, 20147],
    player_castable=False,
)


granted_by_talent(
    id=1425,
    tab=protection_383_tab,
    tier=1,
    column=1,
    ranks=[guardian_s_favor_20174, guardian_s_favor_20175],
    player_castable=False,
)


granted_by_talent(
    id=1426,
    tab=protection_383_tab,
    tier=4,
    column=2,
    ranks=[20177, 20179, 20181, 20180, 20182],
    player_castable=False,
)


granted_by_talent(
    id=1429,
    tab=protection_383_tab,
    tier=5,
    column=2,
    ranks=[20196, 20197, 20198],
    player_castable=False,
)


granted_by_talent(
    id=1430,
    tab=protection_383_tab,
    tier=6,
    column=1,
    ranks=[holy_shield_20925],
    player_castable=False,
    depends_on={'talent_id': 1431, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=1431,
    tab=protection_383_tab,
    tier=4,
    column=1,
    ranks=[blessing_of_sanctuary_20911],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1432,
    tab=holy_382_tab,
    tier=0,
    column=1,
    ranks=[spiritual_focus_20205, spiritual_focus_20206, spiritual_focus_20207, spiritual_focus_20209, spiritual_focus_20208],
    player_castable=False,
)


granted_by_talent(
    id=1433,
    tab=holy_382_tab,
    tier=4,
    column=1,
    ranks=[divine_favor_20216],
    player_castable=False,
    depends_on={'talent_id': 1461, 'rank': 4},
    flags=1,
)


granted_by_talent(
    id=1435,
    tab=holy_382_tab,
    tier=2,
    column=0,
    ranks=[aura_mastery_31821],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1441,
    tab=retribution_381_tab,
    tier=6,
    column=1,
    ranks=[repentance_20066],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1442,
    tab=protection_383_tab,
    tier=0,
    column=1,
    ranks=[63646, 63647, 63648, 63649, 63650],
    player_castable=False,
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
    id=1444,
    tab=holy_382_tab,
    tier=1,
    column=0,
    ranks=[healing_light_20237, healing_light_20238, healing_light_20239],
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
    id=1449,
    tab=holy_382_tab,
    tier=1,
    column=1,
    ranks=[20257, 20258, 20259, 20260, 20261],
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
    id=1461,
    tab=holy_382_tab,
    tier=2,
    column=1,
    ranks=[illumination_20210, illumination_20212, illumination_20213, illumination_20214, illumination_20215],
    player_castable=False,
)


granted_by_talent(
    id=1463,
    tab=holy_382_tab,
    tier=0,
    column=2,
    ranks=[seals_of_the_pure_20224, seals_of_the_pure_20225, seals_of_the_pure_20330, seals_of_the_pure_20331, seals_of_the_pure_20332],
    player_castable=False,
)


granted_by_talent(
    id=1464,
    tab=retribution_381_tab,
    tier=1,
    column=1,
    ranks=[heart_of_the_crusader_20335, heart_of_the_crusader_20336, heart_of_the_crusader_20337],
    player_castable=False,
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
    id=1481,
    tab=retribution_381_tab,
    tier=2,
    column=2,
    ranks=[seal_of_command_20375],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1501,
    tab=protection_383_tab,
    tier=2,
    column=1,
    ranks=[improved_righteous_fury_20468, improved_righteous_fury_20469, improved_righteous_fury_20470],
    player_castable=False,
)


granted_by_talent(
    id=1502,
    tab=holy_382_tab,
    tier=6,
    column=1,
    ranks=[holy_shock_20473],
    player_castable=False,
    depends_on={'talent_id': 1433, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=1521,
    tab=protection_383_tab,
    tier=3,
    column=1,
    ranks=[improved_hammer_of_justice_20487, improved_hammer_of_justice_20488],
    player_castable=False,
)


granted_by_talent(
    id=1627,
    tab=holy_382_tab,
    tier=5,
    column=2,
    ranks=[5923, 5924, 5925, 5926, 25829],
    player_castable=False,
)


granted_by_talent(
    id=1628,
    tab=holy_382_tab,
    tier=1,
    column=2,
    ranks=[9453, 25836],
    player_castable=False,
)


granted_by_talent(
    id=1629,
    tab=protection_383_tab,
    tier=1,
    column=2,
    ranks=[20096, 20097, 20098, 20099, 20100],
    player_castable=False,
)


granted_by_talent(
    id=1631,
    tab=retribution_381_tab,
    tier=1,
    column=0,
    ranks=[improved_judgements_25956, improved_judgements_25957],
    player_castable=False,
)


granted_by_talent(
    id=1632,
    tab=retribution_381_tab,
    tier=3,
    column=0,
    ranks=[9799, 25988],
    player_castable=False,
)


granted_by_talent(
    id=1633,
    tab=retribution_381_tab,
    tier=2,
    column=0,
    ranks=[9452, 26016],
    player_castable=False,
)


granted_by_talent(
    id=1634,
    tab=retribution_381_tab,
    tier=2,
    column=3,
    ranks=[26022, 26023],
    player_castable=False,
)


granted_by_talent(
    id=1742,
    tab=holy_382_tab,
    tier=4,
    column=0,
    ranks=[pure_of_heart_31822, pure_of_heart_31823],
    player_castable=False,
)


granted_by_talent(
    id=1743,
    tab=holy_382_tab,
    tier=5,
    column=0,
    ranks=[purifying_power_31825, purifying_power_31826],
    player_castable=False,
)


granted_by_talent(
    id=1744,
    tab=holy_382_tab,
    tier=6,
    column=2,
    ranks=[blessed_life_31828, blessed_life_31829, blessed_life_31830],
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
    id=1746,
    tab=holy_382_tab,
    tier=7,
    column=2,
    ranks=[holy_guidance_31837, holy_guidance_31838, holy_guidance_31839, holy_guidance_31840, holy_guidance_31841],
    player_castable=False,
)


granted_by_talent(
    id=1747,
    tab=holy_382_tab,
    tier=8,
    column=0,
    ranks=[divine_illumination_31842],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1748,
    tab=protection_383_tab,
    tier=1,
    column=0,
    ranks=[stoicism_31844, stoicism_31845, stoicism_53519],
    player_castable=False,
)


granted_by_talent(
    id=1750,
    tab=protection_383_tab,
    tier=5,
    column=0,
    ranks=[sacred_duty_31848, sacred_duty_31849],
    player_castable=False,
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
    id=1753,
    tab=protection_383_tab,
    tier=7,
    column=2,
    ranks=[combat_expertise_31858, combat_expertise_31859, combat_expertise_31860],
    player_castable=False,
)


granted_by_talent(
    id=1754,
    tab=protection_383_tab,
    tier=8,
    column=1,
    ranks=[avenger_s_shield_31935],
    player_castable=False,
    depends_on={'talent_id': 1430, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=1755,
    tab=retribution_381_tab,
    tier=3,
    column=3,
    ranks=[31866, 31867, 31868],
    player_castable=False,
)


granted_by_talent(
    id=1756,
    tab=retribution_381_tab,
    tier=4,
    column=2,
    ranks=[sanctified_retribution_31869],
    player_castable=False,
    depends_on={'talent_id': 1409, 'rank': 0},
)


granted_by_talent(
    id=1757,
    tab=retribution_381_tab,
    tier=5,
    column=2,
    ranks=[31871, 31872],
    player_castable=False,
)


granted_by_talent(
    id=1758,
    tab=retribution_381_tab,
    tier=6,
    column=2,
    ranks=[judgements_of_the_wise_31876, judgements_of_the_wise_31877, judgements_of_the_wise_31878],
    player_castable=False,
)


granted_by_talent(
    id=1759,
    tab=retribution_381_tab,
    tier=7,
    column=1,
    ranks=[fanaticism_31879, fanaticism_31880, fanaticism_31881],
    player_castable=False,
    depends_on={'talent_id': 1441, 'rank': 0},
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
    id=1823,
    tab=retribution_381_tab,
    tier=8,
    column=1,
    ranks=[crusader_strike_35395],
    player_castable=False,
    flags=1,
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
    id=2148,
    tab=retribution_381_tab,
    tier=8,
    column=0,
    ranks=[swift_retribution_53379, swift_retribution_53484, swift_retribution_53648],
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
    id=2150,
    tab=retribution_381_tab,
    tier=10,
    column=1,
    ranks=[divine_storm_53385],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2176,
    tab=retribution_381_tab,
    tier=6,
    column=0,
    ranks=[the_art_of_war_53486, the_art_of_war_53488],
    player_castable=False,
)


granted_by_talent(
    id=2179,
    tab=retribution_381_tab,
    tier=8,
    column=2,
    ranks=[sheath_of_light_53501, sheath_of_light_53502, sheath_of_light_53503],
    player_castable=False,
)


granted_by_talent(
    id=2185,
    tab=protection_383_tab,
    tier=0,
    column=2,
    ranks=[20262, 20263, 20264, 20265, 20266],
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
    id=2191,
    tab=holy_382_tab,
    tier=9,
    column=2,
    ranks=[enlightened_judgements_53556, enlightened_judgements_53557],
    player_castable=False,
)


granted_by_talent(
    id=2192,
    tab=holy_382_tab,
    tier=10,
    column=1,
    ranks=[beacon_of_light_53563],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2193,
    tab=holy_382_tab,
    tier=9,
    column=1,
    ranks=[infusion_of_light_53569, infusion_of_light_53576],
    player_castable=False,
    depends_on={'talent_id': 1502, 'rank': 0},
)


granted_by_talent(
    id=2194,
    tab=protection_383_tab,
    tier=8,
    column=2,
    ranks=[guarded_by_the_light_53583, guarded_by_the_light_53585],
    player_castable=False,
)


granted_by_talent(
    id=2195,
    tab=protection_383_tab,
    tier=8,
    column=0,
    ranks=[touched_by_the_light_53590, touched_by_the_light_53591, touched_by_the_light_53592],
    player_castable=False,
)


granted_by_talent(
    id=2196,
    tab=protection_383_tab,
    tier=10,
    column=1,
    ranks=[hammer_of_the_righteous_53595],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2198,
    tab=holy_382_tab,
    tier=3,
    column=3,
    ranks=[blessed_hands_53660, blessed_hands_53661],
    player_castable=False,
)


granted_by_talent(
    id=2199,
    tab=holy_382_tab,
    tier=8,
    column=2,
    ranks=[judgements_of_the_pure_53671, judgements_of_the_pure_53673, judgements_of_the_pure_54151, judgements_of_the_pure_54154, judgements_of_the_pure_54155],
    player_castable=False,
)


granted_by_talent(
    id=2200,
    tab=protection_383_tab,
    tier=9,
    column=2,
    ranks=[judgements_of_the_just_53695, judgements_of_the_just_53696],
    player_castable=False,
)


granted_by_talent(
    id=2204,
    tab=protection_383_tab,
    tier=9,
    column=1,
    ranks=[shield_of_the_templar_53709, shield_of_the_templar_53710, shield_of_the_templar_53711],
    player_castable=False,
    depends_on={'talent_id': 1754, 'rank': 0},
)


granted_by_talent(
    id=2280,
    tab=protection_383_tab,
    tier=2,
    column=0,
    ranks=[divine_sacrifice_64205],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2281,
    tab=protection_383_tab,
    tier=3,
    column=0,
    ranks=[divine_guardian_53527, divine_guardian_53530],
    player_castable=False,
    depends_on={'talent_id': 2280, 'rank': 0},
)


granted_by_talent(
    id=2282,
    tab=protection_383_tab,
    tier=6,
    column=0,
    ranks=[spiritual_attunement_31785, spiritual_attunement_33776],
    player_castable=False,
)
