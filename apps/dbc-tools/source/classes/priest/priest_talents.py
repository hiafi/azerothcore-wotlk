"""
Priest - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/priest.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .priest_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, tab
from .priest_spells import circle_of_healing_34861, desperate_prayer_19236, dispersion_47585, guardian_spirit_47788, inner_focus_14751, lightwell_724, mind_flay_15407, pain_suppression_33206, penance_47540, power_infusion_10060, psychic_horror_64044, shadowform_15473, silence_15487, vampiric_touch_34914
from .priest_trigger_spells import absolution_33167, absolution_33171, absolution_33172, aspiration_47507, aspiration_47508, blessed_recovery_27811, blessed_recovery_27815, blessed_recovery_27816, blessed_resilience_33142, blessed_resilience_33145, blessed_resilience_33146, body_and_soul_64127, body_and_soul_64129, borrowed_time_52795, borrowed_time_52797, borrowed_time_52798, borrowed_time_52799, borrowed_time_52800, darkness_15259, darkness_15307, darkness_15308, darkness_15309, darkness_15310, divine_aegis_47509, divine_aegis_47511, divine_aegis_47515, divine_fury_18530, divine_fury_18531, divine_fury_18533, divine_fury_18534, divine_fury_18535, divine_providence_47562, divine_providence_47564, divine_providence_47565, divine_providence_47566, divine_providence_47567, empowered_healing_33158, empowered_healing_33159, empowered_healing_33160, empowered_healing_33161, empowered_healing_33162, empowered_renew_63534, empowered_renew_63542, empowered_renew_63543, enlightenment_34908, enlightenment_34909, enlightenment_34910, focused_mind_33213, focused_mind_33214, focused_mind_33215, focused_power_33186, focused_power_33190, grace_47516, grace_47517, healing_focus_14913, healing_focus_15012, healing_prayers_14911, healing_prayers_15018, holy_concentration_34753, holy_concentration_34859, holy_concentration_34860, holy_reach_27789, holy_reach_27790, holy_specialization_14889, holy_specialization_15008, holy_specialization_15009, holy_specialization_15010, holy_specialization_15011, improved_devouring_plague_63625, improved_devouring_plague_63626, improved_devouring_plague_63627, improved_flash_heal_63504, improved_flash_heal_63505, improved_flash_heal_63506, improved_healing_14912, improved_healing_15013, improved_healing_15014, improved_inner_fire_14747, improved_inner_fire_14770, improved_inner_fire_14771, improved_mana_burn_14750, improved_mana_burn_14772, improved_mind_blast_15273, improved_mind_blast_15312, improved_mind_blast_15313, improved_mind_blast_15314, improved_mind_blast_15316, improved_power_word_fortitude_14749, improved_power_word_fortitude_14767, improved_power_word_shield_14748, improved_power_word_shield_14768, improved_power_word_shield_14769, improved_psychic_scream_15392, improved_psychic_scream_15448, improved_renew_14908, improved_renew_15020, improved_renew_17191, improved_shadow_word_pain_15275, improved_shadow_word_pain_15317, improved_shadowform_47569, improved_shadowform_47570, improved_spirit_tap_15337, improved_spirit_tap_15338, improved_vampiric_embrace_27839, improved_vampiric_embrace_27840, inspiration_14892, inspiration_15362, inspiration_15363, mental_agility_14520, mental_agility_14780, mental_agility_14781, mind_melt_14910, mind_melt_33371, misery_33191, misery_33192, misery_33193, pain_and_suffering_47580, pain_and_suffering_47581, pain_and_suffering_47582, rapture_47535, rapture_47536, rapture_47537, reflective_shield_33201, reflective_shield_33202, renewed_hope_57470, renewed_hope_57472, searing_light_14909, searing_light_15017, serendipity_63730, serendipity_63733, serendipity_63737, shadow_affinity_15272, shadow_affinity_15318, shadow_affinity_15320, shadow_focus_15260, shadow_focus_15327, shadow_focus_15328, shadow_power_33221, shadow_power_33222, shadow_power_33223, shadow_power_33224, shadow_power_33225, shadow_reach_17322, shadow_reach_17323, shadow_weaving_15257, shadow_weaving_15331, shadow_weaving_15332, silent_resolve_14523, silent_resolve_14784, silent_resolve_14785, soul_warding_63574, spell_warding_27900, spell_warding_27901, spell_warding_27902, spell_warding_27903, spell_warding_27904, spirit_of_redemption_20711, spiritual_guidance_14901, spiritual_guidance_15028, spiritual_guidance_15029, spiritual_guidance_15030, spiritual_guidance_15031, spiritual_healing_14898, spiritual_healing_15349, spiritual_healing_15354, spiritual_healing_15355, spiritual_healing_15356, surge_of_light_33150, surge_of_light_33154, test_of_faith_47558, test_of_faith_47559, test_of_faith_47560, twin_disciplines_47586, twin_disciplines_47587, twin_disciplines_47588, twin_disciplines_52802, twin_disciplines_52803, twisted_faith_47573, twisted_faith_47577, twisted_faith_47578, twisted_faith_51166, twisted_faith_51167, vampiric_embrace_15286, veiled_shadows_15274, veiled_shadows_15311


discipline_201_tab = tab(
    id=201,
    name='Discipline',
    class_mask=16,
    spell_icon_id=685,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 80},
)


holy_202_tab = tab(
    id=202,
    name='Holy',
    class_mask=16,
    order_index=1,
    spell_icon_id=2873,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 377},
)


shadow_203_tab = tab(
    id=203,
    name='Shadow',
    class_mask=16,
    order_index=2,
    spell_icon_id=234,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 618},
)


granted_by_talent(
    id=321,
    tab=discipline_201_tab,
    tier=1,
    column=3,
    ranks=[14531, 14774],
    player_castable=False,
)


granted_by_talent(
    id=322,
    tab=discipline_201_tab,
    tier=6,
    column=1,
    ranks=[power_infusion_10060],
    player_castable=False,
    depends_on={'talent_id': 1201, 'rank': 4},
    flags=1,
)


granted_by_talent(
    id=341,
    tab=discipline_201_tab,
    tier=3,
    column=1,
    ranks=[mental_agility_14520, mental_agility_14780, mental_agility_14781],
    player_castable=False,
)


granted_by_talent(
    id=342,
    tab=discipline_201_tab,
    tier=0,
    column=1,
    ranks=[14522, 14788, 14789, 14790, 14791],
    player_castable=False,
)


granted_by_talent(
    id=343,
    tab=discipline_201_tab,
    tier=2,
    column=2,
    ranks=[improved_power_word_shield_14748, improved_power_word_shield_14768, improved_power_word_shield_14769],
    player_castable=False,
)


granted_by_talent(
    id=344,
    tab=discipline_201_tab,
    tier=1,
    column=2,
    ranks=[improved_power_word_fortitude_14749, improved_power_word_fortitude_14767],
    player_castable=False,
)


granted_by_talent(
    id=346,
    tab=discipline_201_tab,
    tier=1,
    column=1,
    ranks=[improved_inner_fire_14747, improved_inner_fire_14770, improved_inner_fire_14771],
    player_castable=False,
)


granted_by_talent(
    id=347,
    tab=discipline_201_tab,
    tier=2,
    column=0,
    ranks=[14521, 14776, 14777],
    player_castable=False,
)


granted_by_talent(
    id=348,
    tab=discipline_201_tab,
    tier=2,
    column=1,
    ranks=[inner_focus_14751],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=350,
    tab=discipline_201_tab,
    tier=3,
    column=3,
    ranks=[improved_mana_burn_14750, improved_mana_burn_14772],
    player_castable=False,
)


granted_by_talent(
    id=351,
    tab=discipline_201_tab,
    tier=4,
    column=2,
    ranks=[soul_warding_63574],
    player_castable=False,
    depends_on={'talent_id': 343, 'rank': 2},
    flags=1,
)


granted_by_talent(
    id=352,
    tab=discipline_201_tab,
    tier=1,
    column=0,
    ranks=[silent_resolve_14523, silent_resolve_14784, silent_resolve_14785],
    player_castable=False,
)


granted_by_talent(
    id=361,
    tab=holy_202_tab,
    tier=2,
    column=3,
    ranks=[inspiration_14892, inspiration_15362, inspiration_15363],
    player_castable=False,
)


granted_by_talent(
    id=401,
    tab=holy_202_tab,
    tier=0,
    column=2,
    ranks=[holy_specialization_14889, holy_specialization_15008, holy_specialization_15009, holy_specialization_15010, holy_specialization_15011],
    player_castable=False,
)


granted_by_talent(
    id=402,
    tab=holy_202_tab,
    tier=4,
    column=2,
    ranks=[spiritual_guidance_14901, spiritual_guidance_15028, spiritual_guidance_15029, spiritual_guidance_15030, spiritual_guidance_15031],
    player_castable=False,
)


granted_by_talent(
    id=403,
    tab=holy_202_tab,
    tier=3,
    column=2,
    ranks=[searing_light_14909, searing_light_15017],
    player_castable=False,
    depends_on={'talent_id': 1181, 'rank': 4},
)


granted_by_talent(
    id=404,
    tab=holy_202_tab,
    tier=5,
    column=2,
    ranks=[spiritual_healing_14898, spiritual_healing_15349, spiritual_healing_15354, spiritual_healing_15355, spiritual_healing_15356],
    player_castable=False,
)


granted_by_talent(
    id=406,
    tab=holy_202_tab,
    tier=0,
    column=1,
    ranks=[improved_renew_14908, improved_renew_15020, improved_renew_17191],
    player_castable=False,
)


granted_by_talent(
    id=408,
    tab=holy_202_tab,
    tier=3,
    column=1,
    ranks=[improved_healing_14912, improved_healing_15013, improved_healing_15014],
    player_castable=False,
)


granted_by_talent(
    id=410,
    tab=holy_202_tab,
    tier=0,
    column=0,
    ranks=[healing_focus_14913, healing_focus_15012],
    player_castable=False,
)


granted_by_talent(
    id=411,
    tab=holy_202_tab,
    tier=1,
    column=1,
    ranks=[spell_warding_27900, spell_warding_27901, spell_warding_27902, spell_warding_27903, spell_warding_27904],
    player_castable=False,
)


granted_by_talent(
    id=413,
    tab=holy_202_tab,
    tier=4,
    column=0,
    ranks=[healing_prayers_14911, healing_prayers_15018],
    player_castable=False,
)


granted_by_talent(
    id=442,
    tab=holy_202_tab,
    tier=2,
    column=0,
    ranks=[desperate_prayer_19236],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=461,
    tab=shadow_203_tab,
    tier=3,
    column=3,
    ranks=[shadow_weaving_15257, shadow_weaving_15331, shadow_weaving_15332],
    player_castable=False,
)


granted_by_talent(
    id=462,
    tab=shadow_203_tab,
    tier=0,
    column=2,
    ranks=[darkness_15259, darkness_15307, darkness_15308, darkness_15309, darkness_15310],
    player_castable=False,
)


granted_by_talent(
    id=463,
    tab=shadow_203_tab,
    tier=1,
    column=2,
    ranks=[shadow_focus_15260, shadow_focus_15327, shadow_focus_15328],
    player_castable=False,
)


granted_by_talent(
    id=465,
    tab=shadow_203_tab,
    tier=0,
    column=0,
    ranks=[15270, 15335, 15336],
    player_castable=False,
)


granted_by_talent(
    id=466,
    tab=shadow_203_tab,
    tier=1,
    column=0,
    ranks=[shadow_affinity_15318, shadow_affinity_15272, shadow_affinity_15320],
    player_castable=False,
)


granted_by_talent(
    id=481,
    tab=shadow_203_tab,
    tier=2,
    column=1,
    ranks=[improved_mind_blast_15273, improved_mind_blast_15312, improved_mind_blast_15313, improved_mind_blast_15314, improved_mind_blast_15316],
    player_castable=False,
)


granted_by_talent(
    id=482,
    tab=shadow_203_tab,
    tier=1,
    column=1,
    ranks=[improved_shadow_word_pain_15275, improved_shadow_word_pain_15317],
    player_castable=False,
)


granted_by_talent(
    id=483,
    tab=shadow_203_tab,
    tier=3,
    column=1,
    ranks=[veiled_shadows_15274, veiled_shadows_15311],
    player_castable=False,
)


granted_by_talent(
    id=484,
    tab=shadow_203_tab,
    tier=4,
    column=1,
    ranks=[vampiric_embrace_15286],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=501,
    tab=shadow_203_tab,
    tier=2,
    column=2,
    ranks=[mind_flay_15407],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=521,
    tab=shadow_203_tab,
    tier=6,
    column=1,
    ranks=[shadowform_15473],
    player_castable=False,
    depends_on={'talent_id': 484, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=541,
    tab=shadow_203_tab,
    tier=4,
    column=0,
    ranks=[silence_15487],
    player_castable=False,
    depends_on={'talent_id': 542, 'rank': 1},
    flags=1,
)


granted_by_talent(
    id=542,
    tab=shadow_203_tab,
    tier=2,
    column=0,
    ranks=[improved_psychic_scream_15392, improved_psychic_scream_15448],
    player_castable=False,
)


granted_by_talent(
    id=881,
    tab=shadow_203_tab,
    tier=3,
    column=2,
    ranks=[shadow_reach_17322, shadow_reach_17323],
    player_castable=False,
)


granted_by_talent(
    id=1181,
    tab=holy_202_tab,
    tier=1,
    column=2,
    ranks=[divine_fury_18530, divine_fury_18531, divine_fury_18533, divine_fury_18534, divine_fury_18535],
    player_castable=False,
)


granted_by_talent(
    id=1201,
    tab=discipline_201_tab,
    tier=4,
    column=1,
    ranks=[18551, 18552, 18553, 18554, 18555],
    player_castable=False,
)


granted_by_talent(
    id=1202,
    tab=discipline_201_tab,
    tier=9,
    column=1,
    ranks=[borrowed_time_52795, borrowed_time_52797, borrowed_time_52798, borrowed_time_52799, borrowed_time_52800],
    player_castable=False,
)


granted_by_talent(
    id=1561,
    tab=holy_202_tab,
    tier=4,
    column=1,
    ranks=[spirit_of_redemption_20711],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1635,
    tab=holy_202_tab,
    tier=3,
    column=0,
    ranks=[holy_reach_27789, holy_reach_27790],
    player_castable=False,
)


granted_by_talent(
    id=1636,
    tab=holy_202_tab,
    tier=2,
    column=1,
    ranks=[blessed_recovery_27811, blessed_recovery_27815, blessed_recovery_27816],
    player_castable=False,
)


granted_by_talent(
    id=1637,
    tab=holy_202_tab,
    tier=6,
    column=1,
    ranks=[lightwell_724],
    player_castable=False,
    depends_on={'talent_id': 1561, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=1638,
    tab=shadow_203_tab,
    tier=4,
    column=2,
    ranks=[improved_vampiric_embrace_27839, improved_vampiric_embrace_27840],
    player_castable=False,
    depends_on={'talent_id': 484, 'rank': 0},
)


granted_by_talent(
    id=1765,
    tab=holy_202_tab,
    tier=6,
    column=2,
    ranks=[blessed_resilience_33142, blessed_resilience_33145, blessed_resilience_33146],
    player_castable=False,
)


granted_by_talent(
    id=1766,
    tab=holy_202_tab,
    tier=5,
    column=0,
    ranks=[surge_of_light_33150, surge_of_light_33154],
    player_castable=False,
)


granted_by_talent(
    id=1767,
    tab=holy_202_tab,
    tier=7,
    column=1,
    ranks=[empowered_healing_33158, empowered_healing_33159, empowered_healing_33160, empowered_healing_33161, empowered_healing_33162],
    player_castable=False,
)


granted_by_talent(
    id=1768,
    tab=holy_202_tab,
    tier=6,
    column=0,
    ranks=[holy_concentration_34753, holy_concentration_34859, holy_concentration_34860],
    player_castable=False,
)


granted_by_talent(
    id=1769,
    tab=discipline_201_tab,
    tier=3,
    column=0,
    ranks=[absolution_33167, absolution_33171, absolution_33172],
    player_castable=False,
)


granted_by_talent(
    id=1771,
    tab=discipline_201_tab,
    tier=5,
    column=0,
    ranks=[focused_power_33186, focused_power_33190],
    player_castable=False,
)


granted_by_talent(
    id=1772,
    tab=discipline_201_tab,
    tier=5,
    column=2,
    ranks=[enlightenment_34908, enlightenment_34909, enlightenment_34910],
    player_castable=False,
)


granted_by_talent(
    id=1773,
    tab=discipline_201_tab,
    tier=6,
    column=2,
    ranks=[improved_flash_heal_63504, improved_flash_heal_63505, improved_flash_heal_63506],
    player_castable=False,
)


granted_by_talent(
    id=1774,
    tab=discipline_201_tab,
    tier=8,
    column=1,
    ranks=[pain_suppression_33206],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1777,
    tab=shadow_203_tab,
    tier=4,
    column=3,
    ranks=[focused_mind_33213, focused_mind_33214, focused_mind_33215],
    player_castable=False,
)


granted_by_talent(
    id=1778,
    tab=shadow_203_tab,
    tier=6,
    column=2,
    ranks=[shadow_power_33221, shadow_power_33222, shadow_power_33223, shadow_power_33224, shadow_power_33225],
    player_castable=False,
)


granted_by_talent(
    id=1779,
    tab=shadow_203_tab,
    tier=8,
    column=1,
    ranks=[vampiric_touch_34914],
    player_castable=False,
    depends_on={'talent_id': 521, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=1781,
    tab=shadow_203_tab,
    tier=5,
    column=0,
    ranks=[mind_melt_14910, mind_melt_33371],
    player_castable=False,
)


granted_by_talent(
    id=1815,
    tab=holy_202_tab,
    tier=8,
    column=1,
    ranks=[circle_of_healing_34861],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1816,
    tab=shadow_203_tab,
    tier=7,
    column=2,
    ranks=[misery_33191, misery_33192, misery_33193],
    player_castable=False,
)


granted_by_talent(
    id=1858,
    tab=discipline_201_tab,
    tier=6,
    column=0,
    ranks=[45234, 45243, 45244],
    player_castable=False,
)


granted_by_talent(
    id=1894,
    tab=discipline_201_tab,
    tier=7,
    column=2,
    ranks=[aspiration_47507, aspiration_47508],
    player_castable=False,
)


granted_by_talent(
    id=1895,
    tab=discipline_201_tab,
    tier=8,
    column=0,
    ranks=[divine_aegis_47509, divine_aegis_47511, divine_aegis_47515],
    player_castable=False,
)


granted_by_talent(
    id=1896,
    tab=discipline_201_tab,
    tier=7,
    column=1,
    ranks=[rapture_47535, rapture_47536, rapture_47537],
    player_castable=False,
)


granted_by_talent(
    id=1897,
    tab=discipline_201_tab,
    tier=10,
    column=1,
    ranks=[penance_47540],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1898,
    tab=discipline_201_tab,
    tier=0,
    column=2,
    ranks=[twin_disciplines_47586, twin_disciplines_47587, twin_disciplines_47588, twin_disciplines_52802, twin_disciplines_52803],
    player_castable=False,
)


granted_by_talent(
    id=1901,
    tab=discipline_201_tab,
    tier=8,
    column=2,
    ranks=[grace_47516, grace_47517],
    player_castable=False,
)


granted_by_talent(
    id=1902,
    tab=holy_202_tab,
    tier=8,
    column=0,
    ranks=[empowered_renew_63534, empowered_renew_63542, empowered_renew_63543],
    player_castable=False,
    depends_on={'talent_id': 0, 'rank': 2},
)


granted_by_talent(
    id=1903,
    tab=holy_202_tab,
    tier=8,
    column=2,
    ranks=[test_of_faith_47558, test_of_faith_47559, test_of_faith_47560],
    player_castable=False,
)


granted_by_talent(
    id=1904,
    tab=holy_202_tab,
    tier=7,
    column=2,
    ranks=[serendipity_63730, serendipity_63733, serendipity_63737],
    player_castable=False,
)


granted_by_talent(
    id=1905,
    tab=holy_202_tab,
    tier=9,
    column=1,
    ranks=[divine_providence_47562, divine_providence_47564, divine_providence_47565, divine_providence_47566, divine_providence_47567],
    player_castable=False,
)


granted_by_talent(
    id=1906,
    tab=shadow_203_tab,
    tier=7,
    column=0,
    ranks=[improved_shadowform_47569, improved_shadowform_47570],
    player_castable=False,
    depends_on={'talent_id': 521, 'rank': 0},
)


granted_by_talent(
    id=1907,
    tab=shadow_203_tab,
    tier=9,
    column=2,
    ranks=[twisted_faith_47573, twisted_faith_47577, twisted_faith_47578, twisted_faith_51166, twisted_faith_51167],
    player_castable=False,
)


granted_by_talent(
    id=1908,
    tab=shadow_203_tab,
    tier=8,
    column=0,
    ranks=[psychic_horror_64044],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1909,
    tab=shadow_203_tab,
    tier=8,
    column=2,
    ranks=[pain_and_suffering_47580, pain_and_suffering_47581, pain_and_suffering_47582],
    player_castable=False,
)


granted_by_talent(
    id=1910,
    tab=shadow_203_tab,
    tier=10,
    column=1,
    ranks=[dispersion_47585],
    player_castable=False,
    depends_on={'talent_id': 1779, 'rank': 0},
    flags=1,
)


granted_by_talent(
    id=1911,
    tab=holy_202_tab,
    tier=10,
    column=1,
    ranks=[guardian_spirit_47788],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=2027,
    tab=shadow_203_tab,
    tier=0,
    column=1,
    ranks=[improved_spirit_tap_15337, improved_spirit_tap_15338],
    player_castable=False,
    depends_on={'talent_id': 465, 'rank': 2},
)


granted_by_talent(
    id=2235,
    tab=discipline_201_tab,
    tier=7,
    column=0,
    ranks=[renewed_hope_57470, renewed_hope_57472],
    player_castable=False,
)


granted_by_talent(
    id=2267,
    tab=shadow_203_tab,
    tier=5,
    column=2,
    ranks=[improved_devouring_plague_63625, improved_devouring_plague_63626, improved_devouring_plague_63627],
    player_castable=False,
)


granted_by_talent(
    id=2268,
    tab=discipline_201_tab,
    tier=4,
    column=0,
    ranks=[reflective_shield_33201, reflective_shield_33202],
    player_castable=False,
)


granted_by_talent(
    id=2279,
    tab=holy_202_tab,
    tier=7,
    column=0,
    ranks=[body_and_soul_64127, body_and_soul_64129],
    player_castable=False,
)
