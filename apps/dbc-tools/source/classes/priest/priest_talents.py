"""
Priest - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/priest.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .priest_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, tab
from .priest_spells import apotheosis_200225, circle_of_healing_34861, desperate_prayer_19236, dispersion_47585, guardian_spirit_47788, holy_word_chastise_200223, holy_word_sanctify_200198, holy_word_serenity_200197, inner_focus_14751, lightwell_724, mind_flay_15407, pain_suppression_33206, penance_47540, power_infusion_10060, psychic_horror_64044, shadowform_15473, silence_15487, spirit_shell_200166, vampiric_touch_34914
from .priest_trigger_spells import absolution_33167, absolution_33171, absolution_33172, answered_prayers_200179, answered_prayers_200180, answered_prayers_200181, aspiration_47507, aspiration_47508, blessed_recovery_27811, blessed_recovery_27815, blessed_recovery_27816, blessed_warding_200203, blessed_warding_200204, blessed_warding_200205, body_and_soul_64127, body_and_soul_64129, borrowed_time_52795, borrowed_time_52797, borrowed_time_52798, copious_power_200147, copious_power_200148, copious_power_200149, darkness_15259, darkness_15307, darkness_15308, darkness_15309, darkness_15310, divine_aegis_47509, divine_aegis_47511, divine_fury_18530, divine_fury_18531, divine_fury_18533, divine_providence_47562, divine_providence_47564, divine_providence_47565, divine_touch_200174, divine_touch_200175, echo_of_light_200215, echo_of_light_200216, echo_of_light_200217, empowered_healing_33158, empowered_healing_33159, empowered_healing_33160, empowered_healing_33161, empowered_healing_33162, empowered_renew_63534, empowered_renew_63542, empowered_renew_63543, enlightenment_34908, enlightenment_34909, enlightenment_34910, epiphany_of_light_200220, epiphany_of_light_200221, epiphany_of_light_200222, focused_mind_33213, focused_mind_33214, focused_mind_33215, focused_power_33186, focused_power_33190, focused_will_45234, focused_will_45243, focused_will_45244, grace_200163, grace_47516, grace_47517, guiding_star_200156, guiding_star_200157, healing_focus_14913, healing_focus_15012, healing_prayers_14911, healing_prayers_15018, holy_concentration_34753, holy_concentration_34859, holy_concentration_34860, holy_reach_27789, holy_reach_27790, holy_specialization_14889, holy_specialization_15008, holy_specialization_15009, holy_specialization_15010, holy_specialization_15011, holy_wrath_200210, holy_wrath_200211, holy_wrath_200212, improved_devouring_plague_63625, improved_devouring_plague_63626, improved_devouring_plague_63627, improved_flash_heal_63504, improved_flash_heal_63505, improved_flash_heal_63506, improved_healing_14912, improved_healing_15013, improved_healing_15014, improved_holy_nova_200183, improved_holy_nova_200184, improved_inner_fire_14747, improved_inner_fire_14770, improved_inner_fire_14771, improved_mind_blast_15273, improved_mind_blast_15312, improved_mind_blast_15313, improved_mind_blast_15314, improved_mind_blast_15316, improved_power_word_fortitude_14749, improved_power_word_fortitude_14767, improved_power_word_shield_14748, improved_power_word_shield_14768, improved_power_word_shield_14769, improved_prayer_of_mending_200195, improved_prayer_of_mending_200196, improved_psychic_scream_15392, improved_psychic_scream_15448, improved_renew_14908, improved_renew_15020, improved_renew_17191, improved_shadow_word_pain_15275, improved_shadow_word_pain_15317, improved_shadowform_47569, improved_shadowform_47570, improved_spirit_tap_15337, improved_spirit_tap_15338, improved_vampiric_embrace_27839, improved_vampiric_embrace_27840, inspiration_14892, inspiration_15362, inspiration_15363, kindled_faith_200187, kindled_faith_200188, kindled_faith_200189, martyrdom_14531, martyrdom_14774, meditation_14521, meditation_14776, meditation_14777, mental_agility_14520, mental_agility_14780, mental_agility_14781, mental_strength_18551, mental_strength_18552, mental_strength_18553, mind_melt_14910, mind_melt_33371, misery_33191, misery_33192, misery_33193, pain_and_suffering_47580, pain_and_suffering_47581, pain_and_suffering_47582, radiant_fury_200207, radiant_fury_200208, radiant_fury_200209, rapture_47535, rapture_47536, rapture_47537, reflective_shield_33201, reflective_shield_33202, renewed_hope_57470, renewed_hope_57472, reprieve_200142, reprieve_200143, reprieve_200144, searing_light_14909, searing_light_15017, searing_light_200186, serendipity_63730, serendipity_63733, serendipity_63737, shadow_affinity_15272, shadow_affinity_15318, shadow_affinity_15320, shadow_focus_15260, shadow_focus_15327, shadow_focus_15328, shadow_power_33221, shadow_power_33222, shadow_power_33223, shadow_power_33224, shadow_power_33225, shadow_reach_17322, shadow_reach_17323, shadow_weaving_15257, shadow_weaving_15331, shadow_weaving_15332, soul_warding_200154, soul_warding_63574, spirit_of_redemption_20711, spirit_of_redemption_200191, spirit_of_redemption_200192, spiritual_guidance_14901, spiritual_guidance_15028, spiritual_guidance_15029, spiritual_guidance_15030, spiritual_guidance_15031, spiritual_healing_14898, spiritual_healing_15349, spiritual_healing_15354, spiritual_healing_15355, spiritual_healing_15356, surge_of_light_33150, surge_of_light_33154, test_of_faith_47558, test_of_faith_47559, test_of_faith_47560, twin_disciplines_47586, twin_disciplines_47587, twin_disciplines_47588, twin_disciplines_52802, twin_disciplines_52803, twisted_faith_47573, twisted_faith_47577, twisted_faith_47578, twisted_faith_51166, twisted_faith_51167, vampiric_embrace_15286, veiled_shadows_15274, veiled_shadows_15311


discipline_201_tab = tab(
    id=201,
    name='Discipline',
    class_mask=16,
    spell_icon_id=685,
    skill_line=613,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 80},
)


holy_202_tab = tab(
    id=202,
    name='Holy',
    class_mask=16,
    order_index=1,
    spell_icon_id=2873,
    skill_line=56,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 377},
)


shadow_203_tab = tab(
    id=203,
    name='Shadow',
    class_mask=16,
    order_index=2,
    spell_icon_id=234,
    skill_line=78,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 618},
)


# Priest Discipline rework (.agents/plans/priest-rework/priest-rework.DISC.md). Tree changes in this
# file, in one place so the diff reads as a tree layout rather than as scattered edits:
#   * MOVES: Improved Power Word: Fortitude 344 (1,2)->(0,1), Martyrdom 321 (1,3)->(1,2),
#     Penance 1897 (10,1)->(5,1).
#   * REPURPOSED stock talent ids (overwritten in place, never deleted - DBCDatabaseLoader overlays
#     by ID, so an absent overlay row would leave the stock talent live; PLAN §3.1):
#     352 Silent Resolve -> Reprieve (1,0), 350 Improved Mana Burn -> Copious Power (2,3),
#     342 Unbreakable Will -> Guiding Star (5,3).
#   * MINTED: 60010 Spirit Shell (10,1), the next free id in source/ids.yaml's talent block.
#   * RANK TRIMS: Mental Strength 1201 5->3, Borrowed Time 1202 5->3, Divine Aegis 1895 3->2;
#     Soul Warding 351 1->2 and Grace 1901 2->3 grow instead.
#   * Every `depends_on` in the Discipline tree is dropped (PLAN §2): the client's
#     TalentFrame_DrawLines cannot draw the arrows the new layout would need, and both stock
#     Discipline prerequisites are impossible anyway after the rank trims (Power Infusion needed
#     Mental Strength rank 4; Soul Warding needed Improved Power Word: Shield rank 2, which still
#     exists but is dropped for consistency with the tree-wide rule). Holy/Shadow talents in this
#     file keep theirs - they belong to the later passes.

granted_by_talent(
    id=321,
    tab=discipline_201_tab,
    tier=1,
    column=2,
    ranks=[martyrdom_14531, martyrdom_14774],
    player_castable=False,
)


granted_by_talent(
    id=322,
    tab=discipline_201_tab,
    tier=6,
    column=1,
    ranks=[power_infusion_10060],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=341,
    tab=discipline_201_tab,
    tier=3,
    column=2,
    ranks=[mental_agility_14520, mental_agility_14780, mental_agility_14781],
    player_castable=False,
)


# REPURPOSED: was Unbreakable Will, a 5-rank (0,1) talent. Now Guiding Star at (5,3).
granted_by_talent(
    id=342,
    tab=discipline_201_tab,
    tier=5,
    column=3,
    ranks=[guiding_star_200156, guiding_star_200157],
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
    tier=0,
    column=1,
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
    ranks=[meditation_14521, meditation_14776, meditation_14777],
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


# REPURPOSED: was Improved Mana Burn, a 2-rank (3,3) talent. Now Copious Power at (2,3).
granted_by_talent(
    id=350,
    tab=discipline_201_tab,
    tier=2,
    column=3,
    ranks=[copious_power_200147, copious_power_200148, copious_power_200149],
    player_castable=False,
)


granted_by_talent(
    id=351,
    tab=discipline_201_tab,
    tier=4,
    column=2,
    ranks=[soul_warding_63574, soul_warding_200154],
    player_castable=False,
    flags=1,
)


# REPURPOSED: was Silent Resolve. Now Reprieve, same (1,0) slot, new rank spells.
granted_by_talent(
    id=352,
    tab=discipline_201_tab,
    tier=1,
    column=0,
    ranks=[reprieve_200142, reprieve_200143, reprieve_200144],
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


# HOLY.md (0,2): trimmed from 5 ranks to 3 (2/4/6%, was 1..5%) - 15010/15011 orphaned (still valid
# spell_dbc rows, just no longer referenced by any talent - same pattern as Divine Fury below).
granted_by_talent(
    id=401,
    tab=holy_202_tab,
    tier=0,
    column=2,
    ranks=[holy_specialization_14889, holy_specialization_15008, holy_specialization_15009],
    player_castable=False,
)


# HOLY.md (4,2): trimmed from 5 ranks to 3 (8/16/25% of Spirit, was 5/10/15/20/25%) - 15030/15031
# orphaned.
granted_by_talent(
    id=402,
    tab=holy_202_tab,
    tier=4,
    column=2,
    ranks=[spiritual_guidance_14901, spiritual_guidance_15028, spiritual_guidance_15029],
    player_castable=False,
)


# HOLY.md (3,2): now 3 ranks (200186 is the new rank 3); depends_on dropped tree-wide (PLAN §2 -
# Divine Fury rank 4 no longer exists after its own trim below, so this arrow was impossible anyway).
granted_by_talent(
    id=403,
    tab=holy_202_tab,
    tier=3,
    column=2,
    ranks=[searing_light_14909, searing_light_15017, searing_light_200186],
    player_castable=False,
)


# HOLY.md (5,2): trimmed from 5 ranks to 3 (3/6/10%, was 2/4/6/8/10%) - 15355/15356 orphaned.
granted_by_talent(
    id=404,
    tab=holy_202_tab,
    tier=5,
    column=2,
    ranks=[spiritual_healing_14898, spiritual_healing_15349, spiritual_healing_15354],
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


# REPURPOSED (HOLY.md, PLAN §4.2): was Spell Warding at (1,1). Now Blessed Warding at (6,2) - new
# rank spells 200203-200205 (spell_warding_27900-27904 are now orphaned stock rows).
granted_by_talent(
    id=411,
    tab=holy_202_tab,
    tier=6,
    column=2,
    ranks=[blessed_warding_200203, blessed_warding_200204, blessed_warding_200205],
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


# HOLY.md (1,2): trimmed from 5 ranks to 3 (18534/18535 orphaned) - this talent's own effect data
# was already repurposed (crit chance + Holy-damage-vs-your-HF-target) in priest_trigger_spells.py;
# this rank-count trim was missed on the first pass here and is fixed as part of the same edit
# (the master brief's claim that this talent "already sits at" 3 ranks in this file did not match
# what was actually read from disk before this pass - the live row here had all 5 stock ranks).
granted_by_talent(
    id=1181,
    tab=holy_202_tab,
    tier=1,
    column=2,
    ranks=[divine_fury_18530, divine_fury_18531, divine_fury_18533],
    player_castable=False,
)


granted_by_talent(
    id=1201,
    tab=discipline_201_tab,
    tier=4,
    column=1,
    ranks=[mental_strength_18551, mental_strength_18552, mental_strength_18553],
    player_castable=False,
)


granted_by_talent(
    id=1202,
    tab=discipline_201_tab,
    tier=9,
    column=1,
    ranks=[borrowed_time_52795, borrowed_time_52797, borrowed_time_52798],
    player_castable=False,
)


# HOLY.md (4,1): now 3 ranks - 20711 (r1, Spirit% only, DUMMY removed so Unit::Kill's hardcode
# finds nothing) plus new ranks 200191/200192 (r3 carries the capstone absorb).
granted_by_talent(
    id=1561,
    tab=holy_202_tab,
    tier=4,
    column=1,
    ranks=[spirit_of_redemption_20711, spirit_of_redemption_200191, spirit_of_redemption_200192],
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


# HOLY.md move: Blessed Recovery (2,1) -> (1,1) (PLAN §8 accepted-risk #3).
granted_by_talent(
    id=1636,
    tab=holy_202_tab,
    tier=1,
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


# REPURPOSED (HOLY.md, PLAN §4.2): was Blessed Resilience at (6,2). Now Radiant Fury at (6,3) -
# new rank spells 200207-200209 (blessed_resilience_33142/45/46 are now orphaned stock rows).
granted_by_talent(
    id=1765,
    tab=holy_202_tab,
    tier=6,
    column=3,
    ranks=[radiant_fury_200207, radiant_fury_200208, radiant_fury_200209],
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


# HOLY.md (7,1): trimmed from 5 ranks to 3 (8/16/25%, was 7/15/23/31/39% - the effective 8/16/24
# after the die_sides=1 stored-minus-1 convention) - 33161/33162 orphaned.
granted_by_talent(
    id=1767,
    tab=holy_202_tab,
    tier=7,
    column=1,
    ranks=[empowered_healing_33158, empowered_healing_33159, empowered_healing_33160],
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
    column=1,
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
    ranks=[focused_will_45234, focused_will_45243, focused_will_45244],
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
    ranks=[divine_aegis_47509, divine_aegis_47511],
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
    tier=5,
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
    ranks=[grace_47516, grace_47517, grace_200163],
    player_castable=False,
)


granted_by_talent(
    id=1902,
    tab=holy_202_tab,
    tier=8,
    column=0,
    ranks=[empowered_renew_63534, empowered_renew_63542, empowered_renew_63543],
    player_castable=False,
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


# HOLY.md move: Divine Providence (9,1) -> (9,0), AND trimmed from 5 ranks to 3 (matching the
# design doc's "Divine Providence (3)" label) - 47566/47567 orphaned.
granted_by_talent(
    id=1905,
    tab=holy_202_tab,
    tier=9,
    column=0,
    ranks=[divine_providence_47562, divine_providence_47564, divine_providence_47565],
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


# HOLY.md move: Guardian Spirit (10,1) -> (9,1) - spell/effects unchanged, position only.
granted_by_talent(
    id=1911,
    tab=holy_202_tab,
    tier=9,
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


# MINTED: Spirit Shell, the new Discipline capstone at (10,1) - the slot Penance vacated when it
# moved to (5,1). 60010 is the next free id in source/ids.yaml's talent block (60000-60799;
# 60000-60009 were taken by the Mage rework). player_castable=True derives the SkillLineAbility row
# (30417, next free in the 30400-30499 block) that keeps Spirit Shell in the Discipline spellbook
# tab instead of "General" - that derivation needs discipline_201_tab.skill_line, which is set to
# the real Priest Discipline SkillLine 613 above. flags=1 matches every other single-point active
# talent in this file.
granted_by_talent(
    id=60010,
    tab=discipline_201_tab,
    tier=10,
    column=1,
    ranks=[spirit_shell_200166],
    player_castable=True,
    skill_line_ability_ids=[30417],
    flags=1,
)


# Priest Holy rework (.agents/plans/priest-rework/priest-rework.HOLY.md, PLAN §4.2): 12 new
# talents, all minted ids (60011-60022, the next free block after Discipline's 60010) - none of
# these repurpose a stock talent row (the two Holy repurposes, 411 and 1765, are edited in place
# above, next to their old declarations, per PLAN §3.1). All hidden proc/aura ranks pass
# player_castable=False; the four Holy Word/Apotheosis talents grant a brand-new player-castable
# spell and pass player_castable=True + skill_line_ability_ids (30418-30421, the next free ids in
# the 30400-30499 block after Spirit Shell's 30417) - holy_202_tab.skill_line is already set to the
# real Priest Holy SkillLine 56 (Disc pass).

granted_by_talent(
    id=60011,
    tab=holy_202_tab,
    tier=1,
    column=0,
    ranks=[divine_touch_200174, divine_touch_200175],
    player_castable=False,
)


granted_by_talent(
    id=60012,
    tab=holy_202_tab,
    tier=2,
    column=1,
    ranks=[answered_prayers_200179, answered_prayers_200180, answered_prayers_200181],
    player_castable=False,
)


granted_by_talent(
    id=60013,
    tab=holy_202_tab,
    tier=2,
    column=2,
    ranks=[improved_holy_nova_200183, improved_holy_nova_200184],
    player_castable=False,
)


granted_by_talent(
    id=60014,
    tab=holy_202_tab,
    tier=3,
    column=3,
    ranks=[kindled_faith_200187, kindled_faith_200188, kindled_faith_200189],
    player_castable=False,
)


granted_by_talent(
    id=60015,
    tab=holy_202_tab,
    tier=4,
    column=3,
    ranks=[improved_prayer_of_mending_200195, improved_prayer_of_mending_200196],
    player_castable=False,
)


# Single-rank, player-castable, brand-new spell - same shape as Discipline's Spirit Shell (60010)
# above.
granted_by_talent(
    id=60016,
    tab=holy_202_tab,
    tier=5,
    column=1,
    ranks=[holy_word_serenity_200197],
    player_castable=True,
    skill_line_ability_ids=[30418],
    flags=1,
)


granted_by_talent(
    id=60017,
    tab=holy_202_tab,
    tier=5,
    column=3,
    ranks=[holy_word_sanctify_200198],
    player_castable=True,
    skill_line_ability_ids=[30419],
    flags=1,
)


granted_by_talent(
    id=60018,
    tab=holy_202_tab,
    tier=7,
    column=3,
    ranks=[holy_wrath_200210, holy_wrath_200211, holy_wrath_200212],
    player_castable=False,
)


granted_by_talent(
    id=60019,
    tab=holy_202_tab,
    tier=8,
    column=3,
    ranks=[echo_of_light_200215, echo_of_light_200216, echo_of_light_200217],
    player_castable=False,
)


granted_by_talent(
    id=60020,
    tab=holy_202_tab,
    tier=9,
    column=2,
    ranks=[epiphany_of_light_200220, epiphany_of_light_200221, epiphany_of_light_200222],
    player_castable=False,
)


granted_by_talent(
    id=60021,
    tab=holy_202_tab,
    tier=9,
    column=3,
    ranks=[holy_word_chastise_200223],
    player_castable=True,
    skill_line_ability_ids=[30420],
    flags=1,
)


granted_by_talent(
    id=60022,
    tab=holy_202_tab,
    tier=10,
    column=1,
    ranks=[apotheosis_200225],
    player_castable=True,
    skill_line_ability_ids=[30421],
    flags=1,
)
