"""
Druid - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/druid.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .druid_...` below) resolve.
"""

from lib.dsl.constants import ShapeshiftForm
from lib.dsl.registry import (
    custom_attr, granted_by_talent, leave_spell_group, linked_spell, procs_on, scripted_by,
    shapeshift_form, spell_group, spell_group_rule, tab, trained_by, unbind_script, unlink_spell, untrain,
)
from ._masks import (
    EM_TRIGGER, ENTANGLING_ROOTS, INSECT_SWARM, MOONGLOW_SPELLS, NG_TRIGGER,
    PROC_ATTR_TRIGGERED_CAN_PROC, PROC_FLAG_DONE_MELEE_AUTO_ATTACK, PROC_FLAG_DONE_PERIODIC,
    PROC_FLAG_DONE_RANGED_AUTO_ATTACK, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG,
    PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS,
    PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG, PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS,
    PROC_FLAG_TAKEN_DAMAGE, PROC_HIT_CRITICAL, PROC_SPELL_PHASE_CAST, PROC_SPELL_PHASE_HIT,
    PROC_SPELL_TYPE_DAMAGE, PROC_SPELL_TYPE_HEAL,
)
from .druid_spells import (
    berserk_50334, bloom_200560, cenarion_ward_200562, flourish_200564, force_of_nature_33831,
    fury_of_elune_200336, insect_swarm_5570, lifebloom_33763, mass_entanglement_200334,
    moonkin_form_24858, natural_alacrity_17116, solar_beam_200335, starfall_48505, starsurge_200333,
    survival_instincts_61336, swiftmend_18562, tranquility_740, typhoon_50516, wild_growth_48438,
)
# druid-rework FERAL WP-A (FERAL §4/§5/§7): this pass's stock and new spells referenced below.
from ._masks import INFECTED_WOUNDS_TRIGGER, PROC_HIT_NORMAL
from .druid_spells import (
    barkskin_22812, bear_form_5487, bestial_fury_200425, dire_bear_form_9634,
    feral_charge_bear_16979, feral_charge_cat_49376, ferocious_bite_22568, frenzied_regeneration_22842,
    faerie_fire_feral_16857, healing_touch_5185, maim_22570, mangle_bear_33878, mangle_cat_33876,
    pounce_9005, rake_1822, ravage_6785, regrowth_8936, rip_1079, savage_roar_52610, shred_5221,
    thrash_200423, tiger_s_fury_5217,
)
from .druid_trigger_spells import (
    bear_form_passive_1178, bestial_fury_rage_200437, bloodletting_200454, bloodletting_200455,
    bonebreaker_200456, bonebreaker_200457, bonebreaker_200458, dire_bear_form_passive_9635,
    elder_hide_200440, elder_hide_200441, elder_hide_200442, flesh_render_200446, flesh_render_200447,
    flesh_render_200448, fury_swipes_200451, fury_swipes_200452, fury_swipes_200453,
    heart_of_the_wild_17003, heart_of_the_wild_17004, heart_of_the_wild_17005, iron_hide_200467,
    iron_hide_200468, iron_hide_200469, leader_of_the_pack_24932, primal_attunement_200443,
    primal_attunement_200444, primal_attunement_200445, primal_fury_37116, primal_fury_37117,
    primal_gore_200470, primal_gore_200471, rending_swipes_200449, rending_swipes_200450,
    sabertooth_200461, sabertooth_200462, sabertooth_200463, savage_defense_200459,
    savage_defense_200460, savage_defense_62606, sharpened_claws_16942, sharpened_claws_16943,
    sharpened_claws_16944, splintering_blows_200464, splintering_blows_200465, splintering_blows_200466,
)
# druid-rework RESTO WP-A: this pass's own new/rewritten talent-rank and standalone spells
# (druid_trigger_spells.py) that druid_talents.py's granted_by_talent()/scripted_by()/procs_on()
# calls below need.
from .druid_trigger_spells import (
    deep_roots_200583, deep_roots_200584, deep_roots_200585, natural_shapeshifter_16833,
    natural_shapeshifter_16834, natural_shapeshifter_16835, natures_mending_200580,
    natures_mending_200581, natures_mending_200582, natures_resilience_200577,
    natures_resilience_200578, natures_resilience_200579, omen_of_clarity_200600,
    omen_of_clarity_200601, perennial_200589, perennial_200590, perennial_200591,
    photosynthesis_200595, photosynthesis_200596, photosynthesis_200597, proliferation_200592,
    proliferation_200593, proliferation_200594, unstoppable_growth_200598, unstoppable_growth_200599,
    yseras_gift_200586, yseras_gift_200587, yseras_gift_200588,
)
from .druid_trigger_spells import astral_crit_200354, astral_crit_200355, astral_crit_200356, astral_surge_200344, astral_surge_200345, astral_surge_200346, balance_of_power_33592, balance_of_power_33596, balance_of_power_buff_200347, brambles_16836, starfire_cleave_200337, fury_of_elune_splash_200339, owlkin_frenzy_48389, owlkin_frenzy_48392, owlkin_frenzy_48393, brambles_16839, brambles_16840, brutal_impact_16940, brutal_impact_16941, celestial_attunement_200320, celestial_attunement_200321, celestial_attunement_200322, celestial_focus_16850, celestial_focus_16923, celestial_focus_16924, dreamstate_33597, dreamstate_33599, dreamstate_33956, earth_and_moon_48506, earth_and_moon_48510, earth_and_moon_48511, eclipse_48516, eclipse_48521, eclipse_48525, empowered_rejuvenation_33886, empowered_rejuvenation_33887, empowered_rejuvenation_33888, empowered_rejuvenation_33889, empowered_rejuvenation_33890, empowered_touch_33879, empowered_touch_33880, feral_aggression_16858, feral_aggression_16859, feral_aggression_16860, feral_aggression_16861, feral_aggression_16862, feral_instinct_16947, feral_instinct_16948, feral_instinct_16949, feral_swiftness_17002, feral_swiftness_24866, ferocity_16934, ferocity_16935, ferocity_16936, ferocity_16937, ferocity_16938, furor_17056, furor_17058, furor_17059, furor_17060, furor_17061, gale_winds_48488, gale_winds_48514, gale_winds_stack_200351, genesis_57810, genesis_57811, genesis_57812, genesis_57813, genesis_57814, gift_of_nature_17104, gift_of_nature_24943, gift_of_nature_24944, gift_of_nature_24945, gift_of_nature_24946, gift_of_the_earthmother_51179, gift_of_the_earthmother_51180, gift_of_the_earthmother_51181, gift_of_the_earthmother_51182, gift_of_the_earthmother_51183, improved_barkskin_63410, improved_barkskin_63411, improved_faerie_fire_33600, improved_faerie_fire_33601, improved_faerie_fire_33602, improved_insect_swarm_57849, improved_insect_swarm_57850, improved_insect_swarm_57851, improved_leader_of_the_pack_34297, improved_leader_of_the_pack_34300, improved_mangle_48489, improved_mangle_48491, improved_mangle_48532, improved_mark_of_the_wild_17050, improved_mark_of_the_wild_17051, improved_moonfire_16821, improved_moonfire_16822, improved_moonfire_200323, improved_moonkin_form_48384, improved_moonkin_form_48395, improved_moonkin_form_48396, improved_rejuvenation_17111, improved_rejuvenation_17112, improved_rejuvenation_17113, improved_tranquility_17123, improved_tranquility_17124, improved_tree_of_life_48535, improved_tree_of_life_48536, improved_tree_of_life_48537, infected_wounds_48483, infected_wounds_48484, infected_wounds_48485, intensity_17106, intensity_17107, intensity_17108, king_of_the_jungle_48492, king_of_the_jungle_48494, king_of_the_jungle_48495, leader_of_the_pack_17007, living_seed_48496, living_seed_48499, living_seed_48500, living_spirit_34151, living_spirit_34152, living_spirit_34153, lunar_guidance_33589, lunar_guidance_33590, lunar_guidance_33591, moonfury_16896, moonfury_16897, moonfury_16899, moonglow_16845, moonglow_16846, moonglow_16847, moonglow_buff_200348, moonglow_buff_200349, moonglow_buff_200350, natural_perfection_33881, natural_perfection_33882, natural_perfection_33883, natural_reaction_57878, natural_reaction_57880, natural_reaction_57881, natural_shapeshifter_16833, natural_shapeshifter_16834, natural_shapeshifter_16835, naturalist_17069, naturalist_17070, naturalist_17071, naturalist_17072, naturalist_17073, nature_s_bounty_17074, nature_s_bounty_17075, nature_s_bounty_17076, nature_s_bounty_17077, nature_s_bounty_17078, nature_s_focus_17063, nature_s_focus_17065, nature_s_focus_17066, nature_s_grace_16880, nature_s_grace_61345, nature_s_grace_61346, nature_s_majesty_35363, nature_s_majesty_35364, nature_s_reach_16819, nature_s_reach_16820, nature_s_splendor_200324, nature_s_splendor_200325, nature_s_splendor_200326, nurturing_instinct_33872, nurturing_instinct_33873, omen_of_clarity_16864, predatory_instincts_33859, predatory_instincts_33866, predatory_instincts_33867, predatory_strikes_16972, predatory_strikes_16974, predatory_strikes_16975, primal_gore_63503, primal_precision_48409, primal_precision_48410, primal_tenacity_33851, primal_tenacity_33852, primal_tenacity_33957, protector_of_the_pack_57873, protector_of_the_pack_57876, protector_of_the_pack_57877, rend_and_tear_48432, rend_and_tear_48433, rend_and_tear_48434, rend_and_tear_51268, rend_and_tear_51269, revitalize_48539, revitalize_48544, revitalize_48545, savage_fury_16998, savage_fury_16999, shredding_attacks_16966, shredding_attacks_16968, starlight_wrath_16814, starlight_wrath_16815, starlight_wrath_16816, starlight_wrath_16817, starlight_wrath_16818, starweaver_200327, starweaver_200328, starweaver_200329, subtlety_17118, subtlety_17119, subtlety_17120, survival_of_the_fittest_33853, survival_of_the_fittest_33855, survival_of_the_fittest_33856, swarming_rot_200330, swarming_rot_200331, swarming_rot_200332, tranquil_spirit_24968, tranquil_spirit_24969, tranquil_spirit_24970, tranquil_spirit_24971, tranquil_spirit_24972, vengeance_16909, vengeance_16910, vengeance_16911, vengeance_16912, vengeance_16913, vengeful_soul_200343, wrath_of_cenarius_33603, wrath_of_cenarius_33604, wrath_of_cenarius_33605, wrath_of_cenarius_33606, wrath_of_cenarius_33607


feral_combat_281_tab = tab(
    id=281,
    name='Feral Combat',
    class_mask=1024,
    order_index=1,
    spell_icon_id=107,
    skill_line=134,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 431},
)


restoration_282_tab = tab(
    id=282,
    name='Restoration',
    class_mask=1024,
    order_index=2,
    spell_icon_id=962,
    skill_line=573,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 661},
)


balance_283_tab = tab(
    id=283,
    name='Balance',
    class_mask=1024,
    spell_icon_id=225,
    skill_line=574,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 137},
)


granted_by_talent(
    id=762,
    tab=balance_283_tab,
    tier=0,
    column=1,
    ranks=[starlight_wrath_16814, starlight_wrath_16815, starlight_wrath_16816],
    player_castable=False,
)


granted_by_talent(
    id=763,
    tab=balance_283_tab,
    tier=1,
    column=2,
    ranks=[improved_moonfire_16821, improved_moonfire_16822, improved_moonfire_200323],
    player_castable=False,
)


granted_by_talent(
    id=764,
    tab=balance_283_tab,
    tier=2,
    column=3,
    ranks=[nature_s_reach_16819, nature_s_reach_16820],
    player_castable=False,
)


granted_by_talent(
    id=782,
    tab=balance_283_tab,
    tier=4,
    column=3,
    ranks=[brambles_16836, brambles_16839, brambles_16840],
    player_castable=False,
)


granted_by_talent(
    id=783,
    tab=balance_283_tab,
    tier=1,
    column=0,
    ranks=[moonglow_16845, moonglow_16846, moonglow_16847],
    player_castable=False,
)


granted_by_talent(
    id=784,
    tab=balance_283_tab,
    tier=3,
    column=2,
    ranks=[celestial_focus_16850, celestial_focus_16923],
    player_castable=False,
)


granted_by_talent(
    id=788,
    tab=balance_283_tab,
    tier=2,
    column=1,
    ranks=[insect_swarm_5570],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=789,
    tab=balance_283_tab,
    tier=2,
    column=0,
    ranks=[nature_s_grace_16880, nature_s_grace_61345, nature_s_grace_61346],
    player_castable=False,
)


granted_by_talent(
    id=790,
    tab=balance_283_tab,
    tier=5,
    column=1,
    ranks=[moonfury_16896, moonfury_16897, moonfury_16899],
    player_castable=False,
)


granted_by_talent(
    id=792,
    tab=balance_283_tab,
    tier=6,
    column=3,
    ranks=[vengeance_16909, vengeance_16910, vengeance_16911],
    player_castable=False,
)


granted_by_talent(
    id=793,
    tab=balance_283_tab,
    tier=6,
    column=1,
    ranks=[moonkin_form_24858],
    player_castable=False,
    flags=1,
)


# druid-rework FERAL §7 (0,1) now (0,2): repurposed Thick Hide (1,2) -> Elder Hide (3 ranks, capstone r3). Old ranks
# 16929-16931 are orphaned.
granted_by_talent(
    id=794,
    tab=feral_combat_281_tab,
    tier=0,
    column=2,
    ranks=[elder_hide_200440, elder_hide_200441, elder_hide_200442],
    player_castable=False,
)


# druid-rework FERAL §7 (1,3) now (1,2): Feral Aggression moved from (0,2), trimmed 5 -> 3 ranks (16861/16862
# orphaned).
granted_by_talent(
    id=795,
    tab=feral_combat_281_tab,
    tier=1,
    column=2,
    ranks=[feral_aggression_16858, feral_aggression_16859, feral_aggression_16860],
    player_castable=False,
)


# druid-rework FERAL §7 (0,0) now (0,1): Ferocity moved from (0,1).
granted_by_talent(
    id=796,
    tab=feral_combat_281_tab,
    tier=0,
    column=1,
    ranks=[ferocity_16934, ferocity_16935, ferocity_16936, ferocity_16937, ferocity_16938],
    player_castable=False,
)


# druid-rework FERAL §7 (5,3): repurposed Brutal Impact (4,0) -> Bonebreaker (capstone r3). 16940/16941 orphaned.
granted_by_talent(
    id=797,
    tab=feral_combat_281_tab,
    tier=5,
    column=3,
    ranks=[bonebreaker_200456, bonebreaker_200457, bonebreaker_200458],
    player_castable=False,
)


# druid-rework FERAL §7 (2,2): Sharpened Claws, crit with all spells and abilities.
granted_by_talent(
    id=798,
    tab=feral_combat_281_tab,
    tier=2,
    column=2,
    ranks=[sharpened_claws_16942, sharpened_claws_16943, sharpened_claws_16944],
    player_castable=False,
)


# druid-rework FERAL §7 (1,0) now (1,1): Feral Instinct.
granted_by_talent(
    id=799,
    tab=feral_combat_281_tab,
    tier=1,
    column=1,
    ranks=[feral_instinct_16947, feral_instinct_16948, feral_instinct_16949],
    player_castable=False,
)


# druid-rework FERAL §7 (3,2) now (3,3): Primal Fury, tooltip only; prerequisite arrow dropped (PLAN §2).
granted_by_talent(
    id=801,
    tab=feral_combat_281_tab,
    tier=3,
    column=3,
    ranks=[primal_fury_37116, primal_fury_37117],
    player_castable=False,
)


# druid-rework FERAL §7 (3,0): Shredding Attacks (capstone r2).
granted_by_talent(
    id=802,
    tab=feral_combat_281_tab,
    tier=3,
    column=0,
    ranks=[shredding_attacks_16966, shredding_attacks_16968],
    player_castable=False,
)


# druid-rework FERAL §7 (3,1): Predatory Strikes (the stock feral-AP block goes inert, CORE-AUDIT row 35).
granted_by_talent(
    id=803,
    tab=feral_combat_281_tab,
    tier=3,
    column=1,
    ranks=[predatory_strikes_16972, predatory_strikes_16974, predatory_strikes_16975],
    player_castable=False,
)


# druid-rework FERAL §7 (2,3) now (0,3) + §0.16: repurposed Feral Charge (4,2) -> Bestial Fury (Feral Charge is
# baseline, its learner 49377 is orphaned); teaches the player-castable form 200425, so it bundles
# SkillLineAbility 30438.
granted_by_talent(
    id=804,
    tab=feral_combat_281_tab,
    tier=0,
    column=3,
    ranks=[bestial_fury_200425],
    player_castable=True,
    skill_line_ability_ids=[30438],
    flags=1,
)


# druid-rework FERAL §7 (1,1) now (1,0): Savage Fury.
granted_by_talent(
    id=805,
    tab=feral_combat_281_tab,
    tier=1,
    column=0,
    ranks=[savage_fury_16998, savage_fury_16999],
    player_castable=False,
)


# druid-rework FERAL §7 (2,0): Feral Swiftness (capstone r2: Stampede).
granted_by_talent(
    id=807,
    tab=feral_combat_281_tab,
    tier=2,
    column=0,
    ranks=[feral_swiftness_17002, feral_swiftness_24866],
    player_castable=False,
)


# druid-rework FERAL §7 (5,1): Heart of the Wild trimmed 5 -> 3 ranks (17006/24894 orphaned, capstone r3);
# prerequisite arrow dropped.
granted_by_talent(
    id=808,
    tab=feral_combat_281_tab,
    tier=5,
    column=1,
    ranks=[heart_of_the_wild_17003, heart_of_the_wild_17004, heart_of_the_wild_17005],
    player_castable=False,
)


# druid-rework FERAL §7 (6,1): Leader of the Pack.
granted_by_talent(
    id=809,
    tab=feral_combat_281_tab,
    tier=6,
    column=1,
    ranks=[leader_of_the_pack_17007],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=821,
    tab=restoration_282_tab,
    tier=0,
    column=0,
    ranks=[improved_mark_of_the_wild_17050, improved_mark_of_the_wild_17051],
    player_castable=False,
)


granted_by_talent(
    id=822,
    tab=restoration_282_tab,
    tier=0,
    column=3,
    ranks=[natures_resilience_200577, natures_resilience_200578, natures_resilience_200579],
    player_castable=False,
)


granted_by_talent(
    id=823,
    tab=restoration_282_tab,
    tier=0,
    column=1,
    ranks=[nature_s_focus_17063, nature_s_focus_17065],
    player_castable=False,
)


granted_by_talent(
    id=824,
    tab=restoration_282_tab,
    tier=4,
    column=0,
    ranks=[naturalist_17069, naturalist_17070, naturalist_17071],
    player_castable=False,
)


granted_by_talent(
    id=825,
    tab=restoration_282_tab,
    tier=5,
    column=2,
    ranks=[nature_s_bounty_17074, nature_s_bounty_17075, nature_s_bounty_17076],
    player_castable=False,
)


granted_by_talent(
    id=826,
    tab=restoration_282_tab,
    tier=0,
    column=2,
    ranks=[natural_shapeshifter_16833, natural_shapeshifter_16834, natural_shapeshifter_16835],
    player_castable=False,
)


granted_by_talent(
    id=827,
    tab=restoration_282_tab,
    tier=2,
    column=1,
    ranks=[omen_of_clarity_16864, omen_of_clarity_200600, omen_of_clarity_200601],
    player_castable=False,
)


granted_by_talent(
    id=828,
    tab=restoration_282_tab,
    tier=4,
    column=1,
    ranks=[gift_of_nature_17104, gift_of_nature_24943, gift_of_nature_24944],
    player_castable=False,
)


granted_by_talent(
    id=829,
    tab=restoration_282_tab,
    tier=2,
    column=0,
    ranks=[intensity_17106, intensity_17107, intensity_17108],
    player_castable=False,
)


granted_by_talent(
    id=830,
    tab=restoration_282_tab,
    tier=3,
    column=2,
    ranks=[improved_rejuvenation_17111, improved_rejuvenation_17112, improved_rejuvenation_17113],
    player_castable=False,
)


granted_by_talent(
    id=831,
    tab=restoration_282_tab,
    tier=6,
    column=1,
    ranks=[bloom_200560],
    player_castable=True,
    skill_line_ability_ids=[30447],
    flags=1,
)


granted_by_talent(
    id=841,
    tab=restoration_282_tab,
    tier=1,
    column=1,
    ranks=[deep_roots_200583, deep_roots_200584, deep_roots_200585],
    player_castable=False,
)


granted_by_talent(
    id=842,
    tab=restoration_282_tab,
    tier=4,
    column=3,
    ranks=[improved_tranquility_17123, improved_tranquility_17124],
    player_castable=False,
)


granted_by_talent(
    id=843,
    tab=restoration_282_tab,
    tier=3,
    column=1,
    ranks=[tranquil_spirit_24968, tranquil_spirit_24969, tranquil_spirit_24970],
    player_castable=False,
)


granted_by_talent(
    id=844,
    tab=restoration_282_tab,
    tier=2,
    column=2,
    ranks=[swiftmend_18562],
    player_castable=False,
    flags=1,
)


# druid-rework FERAL §7 (2,1): Survival Instincts.
granted_by_talent(
    id=1162,
    tab=feral_combat_281_tab,
    tier=2,
    column=1,
    ranks=[survival_instincts_61336],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1782,
    tab=balance_283_tab,
    tier=4,
    column=0,
    ranks=[lunar_guidance_33589, lunar_guidance_33590, lunar_guidance_33591],
    player_castable=False,
)


granted_by_talent(
    id=1783,
    tab=balance_283_tab,
    tier=5,
    column=2,
    ranks=[balance_of_power_33592, balance_of_power_33596],
    player_castable=False,
)


granted_by_talent(
    id=1784,
    tab=balance_283_tab,
    tier=5,
    column=0,
    ranks=[dreamstate_33597, dreamstate_33599, dreamstate_33956],
    player_castable=False,
)


granted_by_talent(
    id=1785,
    tab=balance_283_tab,
    tier=0,
    column=0,
    ranks=[celestial_attunement_200320, celestial_attunement_200321, celestial_attunement_200322],
    player_castable=False,
)


granted_by_talent(
    id=1786,
    tab=balance_283_tab,
    tier=7,
    column=2,
    ranks=[wrath_of_cenarius_33603, wrath_of_cenarius_33604, wrath_of_cenarius_33605],
    player_castable=False,
)


granted_by_talent(
    id=1787,
    tab=balance_283_tab,
    tier=4,
    column=1,
    ranks=[force_of_nature_33831],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1788,
    tab=restoration_282_tab,
    tier=5,
    column=0,
    ranks=[empowered_touch_33879, empowered_touch_33880],
    player_castable=False,
)


granted_by_talent(
    id=1789,
    tab=restoration_282_tab,
    tier=5,
    column=1,
    ranks=[empowered_rejuvenation_33886, empowered_rejuvenation_33887, empowered_rejuvenation_33888],
    player_castable=False,
)


granted_by_talent(
    id=1790,
    tab=restoration_282_tab,
    tier=6,
    column=2,
    ranks=[natural_perfection_33881, natural_perfection_33882, natural_perfection_33883],
    player_castable=False,
)


granted_by_talent(
    id=1791,
    tab=restoration_282_tab,
    tier=8,
    column=1,
    ranks=[65139],
    player_castable=False,
    flags=1,
)


# druid-rework FERAL §7 (4,3) now (4,1): Nurturing Instinct.
granted_by_talent(
    id=1792,
    tab=feral_combat_281_tab,
    tier=4,
    column=1,
    ranks=[nurturing_instinct_33872, nurturing_instinct_33873],
    player_castable=False,
)


# druid-rework FERAL §7 (6,0) now (6,2): repurposed Primal Tenacity (6,3) -> Savage Defense (now a talent).
# 33851/33852/33957 orphaned.
granted_by_talent(
    id=1793,
    tab=feral_combat_281_tab,
    tier=6,
    column=2,
    ranks=[savage_defense_200459, savage_defense_200460],
    player_castable=False,
)


# druid-rework FERAL §7 (5,2): Survival of the Fittest.
granted_by_talent(
    id=1794,
    tab=feral_combat_281_tab,
    tier=5,
    column=2,
    ranks=[survival_of_the_fittest_33853, survival_of_the_fittest_33855, survival_of_the_fittest_33856],
    player_castable=False,
)


# druid-rework FERAL §7 (7,2) now (7,0): Predatory Instincts.
granted_by_talent(
    id=1795,
    tab=feral_combat_281_tab,
    tier=7,
    column=0,
    ranks=[predatory_instincts_33859, predatory_instincts_33866, predatory_instincts_33867],
    player_castable=False,
)


# druid-rework FERAL §7 (8,3): repurposed Mangle (8,1) -> Splintering Blows (Mangle is baseline, its learner
# 33917 is orphaned); prerequisite arrow dropped.
granted_by_talent(
    id=1796,
    tab=feral_combat_281_tab,
    tier=8,
    column=3,
    ranks=[splintering_blows_200464, splintering_blows_200465, splintering_blows_200466],
    player_castable=False,
)


granted_by_talent(
    id=1797,
    tab=restoration_282_tab,
    tier=6,
    column=0,
    ranks=[living_spirit_34151, living_spirit_34152, living_spirit_34153],
    player_castable=False,
)


# druid-rework FERAL §7 (6,3) now (6,0): repurposed Improved Leader of the Pack (6,2) -> Sabertooth. 34297/34300
# orphaned; prerequisite arrow dropped.
granted_by_talent(
    id=1798,
    tab=feral_combat_281_tab,
    tier=6,
    column=0,
    ranks=[sabertooth_200461, sabertooth_200462, sabertooth_200463],
    player_castable=False,
)


granted_by_talent(
    id=1822,
    tab=balance_283_tab,
    tier=1,
    column=1,
    ranks=[nature_s_majesty_35363, nature_s_majesty_35364],
    player_castable=False,
)


granted_by_talent(
    id=1912,
    tab=balance_283_tab,
    tier=6,
    column=2,
    ranks=[improved_moonkin_form_48384, improved_moonkin_form_48395, improved_moonkin_form_48396],
    player_castable=False,
)


granted_by_talent(
    id=1913,
    tab=balance_283_tab,
    tier=7,
    column=0,
    ranks=[owlkin_frenzy_48389, owlkin_frenzy_48392, owlkin_frenzy_48393],
    player_castable=False,
)


# druid-rework FERAL §7 (3,3) now (3,2): Primal Precision (capstone r2); prerequisite arrow dropped.
granted_by_talent(
    id=1914,
    tab=feral_combat_281_tab,
    tier=3,
    column=2,
    ranks=[primal_precision_48409, primal_precision_48410],
    player_castable=False,
)


granted_by_talent(
    id=1915,
    tab=restoration_282_tab,
    tier=1,
    column=0,
    ranks=[natures_mending_200580, natures_mending_200581, natures_mending_200582],
    player_castable=False,
)


granted_by_talent(
    id=1916,
    tab=restoration_282_tab,
    tier=9,
    column=2,
    ranks=[gift_of_the_earthmother_51179, gift_of_the_earthmother_51180, gift_of_the_earthmother_51181],
    player_castable=False,
)


granted_by_talent(
    id=1917,
    tab=restoration_282_tab,
    tier=4,
    column=2,
    ranks=[wild_growth_48438],
    player_castable=False,
    flags=1,
)


# druid-rework FERAL §7 (9,1) now (9,0): Rend and Tear trimmed 5 -> 3 ranks (51268/51269 orphaned).
granted_by_talent(
    id=1918,
    tab=feral_combat_281_tab,
    tier=9,
    column=0,
    ranks=[rend_and_tear_48432, rend_and_tear_48433, rend_and_tear_48434],
    player_castable=False,
)


# druid-rework FERAL §7 (7,3) now (7,1): Infected Wounds.
granted_by_talent(
    id=1919,
    tab=feral_combat_281_tab,
    tier=7,
    column=1,
    ranks=[infected_wounds_48483, infected_wounds_48484, infected_wounds_48485],
    player_castable=False,
)


# druid-rework FERAL §7 (8,2): Improved Mangle trimmed 3 -> 2 ranks (48491 orphaned, capstone r2);
# prerequisite arrow dropped.
granted_by_talent(
    id=1920,
    tab=feral_combat_281_tab,
    tier=8,
    column=2,
    ranks=[improved_mangle_48532, improved_mangle_48489],
    player_castable=False,
)


# druid-rework FERAL §7 (8,0) + §0.16 Q3: King of the Jungle, no capstone.
granted_by_talent(
    id=1921,
    tab=feral_combat_281_tab,
    tier=8,
    column=0,
    ranks=[king_of_the_jungle_48492, king_of_the_jungle_48494, king_of_the_jungle_48495],
    player_castable=False,
)


granted_by_talent(
    id=1922,
    tab=restoration_282_tab,
    tier=7,
    column=2,
    ranks=[living_seed_48496, living_seed_48499, living_seed_48500],
    player_castable=False,
)


granted_by_talent(
    id=1923,
    tab=balance_283_tab,
    tier=10,
    column=1,
    ranks=[fury_of_elune_200336],
    player_castable=True,
    skill_line_ability_ids=[30427],
    flags=1,
)


granted_by_talent(
    id=1924,
    tab=balance_283_tab,
    tier=8,
    column=0,
    ranks=[eclipse_48516, eclipse_48521, eclipse_48525],
    player_castable=False,
)


granted_by_talent(
    id=1925,
    tab=balance_283_tab,
    tier=8,
    column=3,
    ranks=[gale_winds_48488, gale_winds_48514],
    player_castable=False,
)


granted_by_talent(
    id=1926,
    tab=balance_283_tab,
    tier=8,
    column=1,
    ranks=[starfall_48505],
    player_castable=False,
    flags=1,
)


# druid-rework FERAL §7 (10,1): Berserk.
granted_by_talent(
    id=1927,
    tab=feral_combat_281_tab,
    tier=10,
    column=1,
    ranks=[berserk_50334],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1928,
    tab=balance_283_tab,
    tier=9,
    column=1,
    ranks=[earth_and_moon_48506, earth_and_moon_48510, earth_and_moon_48511],
    player_castable=False,
)


granted_by_talent(
    id=1929,
    tab=restoration_282_tab,
    tier=8,
    column=0,
    ranks=[revitalize_48539, revitalize_48544, revitalize_48545],
    player_castable=False,
)


granted_by_talent(
    id=1930,
    tab=restoration_282_tab,
    tier=8,
    column=2,
    ranks=[photosynthesis_200595, photosynthesis_200596, photosynthesis_200597],
    player_castable=False,
)


granted_by_talent(
    id=2238,
    tab=balance_283_tab,
    tier=0,
    column=2,
    ranks=[genesis_57810, genesis_57811, genesis_57812],
    player_castable=False,
)


granted_by_talent(
    id=2239,
    tab=balance_283_tab,
    tier=4,
    column=2,
    ranks=[improved_insect_swarm_57849, improved_insect_swarm_57850, improved_insect_swarm_57851],
    player_castable=False,
)


granted_by_talent(
    id=2240,
    tab=balance_283_tab,
    tier=2,
    column=2,
    ranks=[nature_s_splendor_200324, nature_s_splendor_200325, nature_s_splendor_200326],
    player_castable=False,
)


granted_by_talent(
    id=60026,
    tab=balance_283_tab,
    tier=3,
    column=0,
    ranks=[starweaver_200327, starweaver_200328, starweaver_200329],
    player_castable=False,
)


granted_by_talent(
    id=60027,
    tab=balance_283_tab,
    tier=3,
    column=1,
    ranks=[swarming_rot_200330, swarming_rot_200331, swarming_rot_200332],
    player_castable=False,
)


# druid-rework FERAL §7 (7,0) now (7,2): Protector of the Pack; prerequisite arrow dropped.
granted_by_talent(
    id=2241,
    tab=feral_combat_281_tab,
    tier=7,
    column=2,
    ranks=[protector_of_the_pack_57873, protector_of_the_pack_57876, protector_of_the_pack_57877],
    player_castable=False,
)


# druid-rework FERAL §7 (5,0) now (4,2): Natural Reaction.
granted_by_talent(
    id=2242,
    tab=feral_combat_281_tab,
    tier=4,
    column=2,
    ranks=[natural_reaction_57878, natural_reaction_57880, natural_reaction_57881],
    player_castable=False,
)


granted_by_talent(
    id=2264,
    tab=restoration_282_tab,
    tier=9,
    column=0,
    ranks=[unstoppable_growth_200598, unstoppable_growth_200599],
    player_castable=False,
)


# druid-rework FERAL §7 (9,2) now (9,1): Primal Gore grows 1 -> 3 ranks (capstone r3); prerequisite arrow dropped.
granted_by_talent(
    id=2266,
    tab=feral_combat_281_tab,
    tier=9,
    column=1,
    ranks=[primal_gore_63503, primal_gore_200470, primal_gore_200471],
    player_castable=False,
)


# --- druid-rework RESTO WP-A: new talents (RESTO §2.2/§8) ---

granted_by_talent(
    id=60055,
    tab=restoration_282_tab,
    tier=1,
    column=2,
    ranks=[yseras_gift_200586, yseras_gift_200587, yseras_gift_200588],
    player_castable=False,
)

granted_by_talent(
    id=60056,
    tab=restoration_282_tab,
    tier=1,
    column=3,
    ranks=[perennial_200589, perennial_200590, perennial_200591],
    player_castable=False,
)

granted_by_talent(
    id=60057,
    tab=restoration_282_tab,
    tier=7,
    column=1,
    ranks=[proliferation_200592, proliferation_200593, proliferation_200594],
    player_castable=False,
)

granted_by_talent(
    id=60058,
    tab=restoration_282_tab,
    tier=10,
    column=1,
    ranks=[flourish_200564],
    player_castable=True,
    skill_line_ability_ids=[30448],
    flags=1,
)


# --- druid-rework FERAL WP-A: minted talents (FERAL §2/§7, PLAN §4.2 - 60040-60045) ---

# (0,2) Primal Attunement
granted_by_talent(
    id=60040,
    tab=feral_combat_281_tab,
    tier=0,
    column=0,
    ranks=[primal_attunement_200443, primal_attunement_200444, primal_attunement_200445],
    player_castable=False,
)

# (1,2) Flesh Render
granted_by_talent(
    id=60041,
    tab=feral_combat_281_tab,
    tier=1,
    column=3,
    ranks=[flesh_render_200446, flesh_render_200447, flesh_render_200448],
    player_castable=False,
)

# (4,0) Rending Swipes
granted_by_talent(
    id=60042,
    tab=feral_combat_281_tab,
    tier=4,
    column=3,
    ranks=[rending_swipes_200449, rending_swipes_200450],
    player_castable=False,
)

# (4,1) Fury Swipes
granted_by_talent(
    id=60043,
    tab=feral_combat_281_tab,
    tier=4,
    column=0,
    ranks=[fury_swipes_200451, fury_swipes_200452, fury_swipes_200453],
    player_castable=False,
)

# (4,2) Bloodletting (capstone r2)
granted_by_talent(
    id=60044,
    tab=feral_combat_281_tab,
    tier=5,
    column=0,
    ranks=[bloodletting_200454, bloodletting_200455],
    player_castable=False,
)

# (9,0) Iron Hide
granted_by_talent(
    id=60045,
    tab=feral_combat_281_tab,
    tier=9,
    column=2,
    ranks=[iron_hide_200467, iron_hide_200468, iron_hide_200469],
    player_castable=False,
)


# --- druid-rework Balance WP-A: scripted_by bindings (BALANCE.md §6 "scripted_by bindings WP-A
# must add" table) - every SpellScript/AuraScript class WP-B adds in spell_druid_balance.cpp,
# druid_hooks.cpp or DruidMechanics.cpp needs its spell_script_names row declared here. ---

scripted_by(starfire_cleave_200337, 'spell_dru_starfall_aoe')
scripted_by(fury_of_elune_splash_200339, 'spell_dru_starfall_aoe')
scripted_by(improved_moonfire_200323, 'spell_dru_improved_moonfire_capstone')
scripted_by(nature_s_reach_16820, 'spell_dru_natures_reach_moonfire_spread')
scripted_by(swarming_rot_200332, 'spell_dru_swarming_rot')
scripted_by(insect_swarm_5570, 'spell_dru_insect_swarm_cast')
scripted_by(brambles_16840, 'spell_dru_brambles_silence')
scripted_by(owlkin_frenzy_48389, 'spell_dru_owlkin_frenzy_proc')
scripted_by(owlkin_frenzy_48392, 'spell_dru_owlkin_frenzy_proc')
scripted_by(owlkin_frenzy_48393, 'spell_dru_owlkin_frenzy_proc')
scripted_by(vengeful_soul_200343, 'spell_dru_vengeful_soul')
scripted_by(5176, 'spell_dru_wrath_of_cenarius_capstone')  # AfterHit on Wrath (5176), not Starfire
scripted_by(dreamstate_33597, 'spell_dru_dreamstate')
scripted_by(dreamstate_33599, 'spell_dru_dreamstate')
scripted_by(dreamstate_33956, 'spell_dru_dreamstate')
scripted_by(29166, 'spell_dru_dreamstate_innervate')  # stock Innervate; spell_dru_innervate stays bound too
scripted_by(42231, 'spell_dru_hurricane_tick')
scripted_by(16914, 'spell_dru_hurricane_channel')
scripted_by(force_of_nature_33831, 'spell_dru_force_of_nature')
# Astral Surge slots + Balance of Power buff - percent-of-spell-power DoEffectCalcAmount
# (CORE-AUDIT row 6 / corrections item 2). Missing until code review caught it: without this
# binding the buffs fall back to their static DBC base_points instead of scaling with spell power.
scripted_by(astral_surge_200344, 'spell_dru_astral_surge_sp')
scripted_by(astral_surge_200345, 'spell_dru_astral_surge_sp')
scripted_by(astral_surge_200346, 'spell_dru_astral_surge_sp')
scripted_by(balance_of_power_buff_200347, 'spell_dru_astral_surge_sp')

# --- Corrected stock-class replacements (Corrections item 4 in the WP-A brief) - unbind the stock
# binding, rebind the exact same spell id to a new fork class in spell_druid_balance.cpp. Naming is
# load-bearing: WP-B must use these four class names verbatim or the binding silently never fires. ---

unbind_script(-48516, 'spell_dru_eclipse')
scripted_by(-48516, 'spell_dru_eclipse_balance')

unbind_script(24905, 'spell_dru_moonkin_form_passive_proc')
scripted_by(24905, 'spell_dru_moonkin_form_proc_balance')

unbind_script(50419, 'spell_dru_brambles_treant')
scripted_by(50419, 'spell_dru_brambles_treant_balance')

unbind_script(35669, 'spell_dru_treant_scaling')
scripted_by(35669, 'spell_dru_treant_scaling_balance')
unbind_script(35670, 'spell_dru_treant_scaling')
scripted_by(35670, 'spell_dru_treant_scaling_balance')
unbind_script(35671, 'spell_dru_treant_scaling')
scripted_by(35671, 'spell_dru_treant_scaling_balance')
unbind_script(35672, 'spell_dru_treant_scaling')
scripted_by(35672, 'spell_dru_treant_scaling_balance')

unbind_script(69366, 'spell_dru_moonkin_form_passive')  # CORE-AUDIT row 10


# --- procs_on() declarations (BALANCE.md §6 talent-table rows + §7) ---

# (1,0) Moonglow - negative whole-chain row (all 3 ranks share the stock -16845 key)
procs_on(-16845, proc_flags=0x14000, family_name=7, family_mask=MOONGLOW_SPELLS,
         spell_phase_mask=PROC_SPELL_PHASE_CAST, chance=5, disable_effects_mask=0x1)

# (2,0) Nature's Grace - negative whole-chain row; chance=0 falls back to each rank's own DBC
# ProcChance (33/66/100)
procs_on(-16880, proc_flags=0x14000, family_name=7, family_mask=NG_TRIGGER, spell_type_mask=3,
         spell_phase_mask=PROC_SPELL_PHASE_CAST, hit_mask=PROC_HIT_CRITICAL, chance=0)

# (1,2) Improved Moonfire capstone - final rank only
procs_on(improved_moonfire_200323, proc_flags=0x10000, school_mask=64,
         spell_type_mask=PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=PROC_SPELL_PHASE_HIT,
         hit_mask=PROC_HIT_CRITICAL, chance=100, cooldown_ms=1500)

# (2,3) Nature's Reach capstone - final rank only
procs_on(nature_s_reach_16820, proc_flags=0x10000, school_mask=64,
         spell_type_mask=PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=PROC_SPELL_PHASE_HIT,
         chance=100, cooldown_ms=6000)

# (3,2) Celestial Focus capstone (Shooting Stars) - final rank only. PROC_FLAG_DONE_PERIODIC is in
# both SPELL_PROC_FLAG_MASK and DONE_HIT_PROC_FLAG_MASK (SpellMgr.h), so REQ_SPELL_PHASE_PROC_FLAG_MASK
# requires spell_phase_mask here or the proc is silently never triggered (SpellMgr.cpp:2112/917-921).
procs_on(celestial_focus_16923, proc_flags=0x40000, family_name=7, family_mask=(0x200002, 0, 0),
         spell_type_mask=PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=PROC_SPELL_PHASE_HIT, chance=5,
         cooldown_ms=10000, disable_effects_mask=0x3)

# (3,1) Swarming Rot capstone - final rank only. Same PROC_FLAG_DONE_PERIODIC phase requirement as
# Celestial Focus above.
procs_on(swarming_rot_200332, proc_flags=0x40000, family_name=7, family_mask=(INSECT_SWARM, 0, 0),
         spell_type_mask=PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=PROC_SPELL_PHASE_HIT, chance=100)

# (4,3) Brambles capstone - final rank only
procs_on(brambles_16840, proc_flags=0x10000, family_name=7, family_mask=(ENTANGLING_ROOTS, 0, 0),
         spell_phase_mask=PROC_SPELL_PHASE_HIT, chance=100, cooldown_ms=10000)

# (7,0) Owlkin Frenzy - negative whole-chain row
procs_on(-48389, proc_flags=0x10028, spell_phase_mask=PROC_SPELL_PHASE_CAST | PROC_SPELL_PHASE_HIT,
         chance=100)

# (6,1) Moonkin Form direct-cast mana proc - overrides the stock 15%/crit/HIT row
procs_on(24905, proc_flags=0x10000, spell_phase_mask=PROC_SPELL_PHASE_CAST, chance=33)

# (6,3) Vengeance capstone - final rank only; triggered spells allowed (Starfall/Hurricane/Fury of
# Elune crits can roll it)
procs_on(vengeance_16911, proc_flags=0x10000, school_mask=72,
         spell_type_mask=PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=PROC_SPELL_PHASE_HIT,
         hit_mask=PROC_HIT_CRITICAL, attributes_mask=PROC_ATTR_TRIGGERED_CAN_PROC, chance=15,
         cooldown_ms=10000, disable_effects_mask=0x1)

# (8,0) Eclipse - negative whole-chain row, overrides the stock -48516 row
procs_on(-48516, proc_flags=0x10000, family_name=7, family_mask=(0x5, 0, 0),
         spell_type_mask=PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=PROC_SPELL_PHASE_HIT, chance=100)

# (9,1) Earth and Moon - negative whole-chain row
procs_on(-48506, proc_flags=0x10000, family_name=7, family_mask=EM_TRIGGER,
         spell_type_mask=PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=PROC_SPELL_PHASE_HIT, chance=100,
         disable_effects_mask=0x2)


# --- World-SQL declarations (BALANCE.md §3 item 6 / PLAN §5.0, via WP-T's helpers) ---

linked_spell(200326, 57865, type=2, comment="Nature's Splendor r3 capstone durations")
linked_spell(16821, 200354, type=2, comment='Improved Moonfire r1 Astral crit')  # CORE-AUDIT row 5
linked_spell(16822, 200355, type=2, comment='Improved Moonfire r2 Astral crit')
linked_spell(improved_moonfire_200323.id, 200356, type=2, comment='Improved Moonfire r3 Astral crit')

spell_group(1054, 50171, 50172)  # re-add Improved Moonkin Form's raid-haste ranks to the Haste
# Buffs group - the single-rank migration dropped them from it (PLAN §3 item 18)
leave_spell_group(1107, 48391)  # Owlkin Frenzy out of "Temporary Damage Increases" (judgment call
# 12.13, default: remove - the spec gives Owlkin Frenzy no "does not stack" clause)

# A7: Moonglow's buffs and Intensity (rank 1, 17106) don't stack - take the max, not the sum
# (EXCLUSIVE_SAME_EFFECT). Group id 1200 is source/ids.yaml's spell_group block's first free id
# (block starts at 1200, nothing else in this rework has minted one yet).
spell_group(1200, moonglow_buff_200348, moonglow_buff_200349, moonglow_buff_200350, 17106)
spell_group_rule(1200, 3, 'Druid - regen while casting (max, not sum)')


# ============================================================================
# druid-rework RESTO WP-A (RESTO §10 "scripted_by bindings WP-A must add" / "World-SQL
# declarations"). Bloom (200560), Cenarion Ward (200562), Flourish (200564) and Swiftmend (18562)
# are already bound next to their spell() declarations in druid_spells.py.
# ============================================================================

scripted_by(774, 'spell_dru_rejuvenation')
scripted_by(200568, 'spell_dru_rejuvenation')
scripted_by(lifebloom_33763, 'spell_dru_lifebloom_target_limit')
scripted_by(5185, 'spell_dru_empowered_touch_capstone', 'spell_dru_photosynthesis_capstone', 'spell_dru_revitalize_capstone')
scripted_by(8936, 'spell_dru_photosynthesis_capstone')
scripted_by(8936, 'spell_dru_regrowth')  # WP-B coordination: a new AuraScript for Regrowth's own crit-chance/coefficient math (CORE-AUDIT rows 13-14), beyond RESTO.md's own class list

# Harmony/Nature's Mending/Waking Dream/Omen-capstone direct-heal multiplier (CORE-AUDIT row 11) -
# bound to all 7 direct-heal spell ids per WP-B's confirmed class list.
scripted_by(5185, 'spell_dru_harmony_direct')
scripted_by(8936, 'spell_dru_harmony_direct')
scripted_by(18562, 'spell_dru_harmony_direct')
scripted_by(200560, 'spell_dru_harmony_direct')
scripted_by(200561, 'spell_dru_harmony_direct')
scripted_by(44203, 'spell_dru_harmony_direct')
scripted_by(200569, 'spell_dru_harmony_direct')
scripted_by(17076, 'spell_dru_natures_bounty_capstone')
scripted_by(33883, 'spell_dru_natural_perfection_capstone')
scripted_by(200586, 'spell_dru_yseras_gift')
scripted_by(200587, 'spell_dru_yseras_gift')
scripted_by(200588, 'spell_dru_yseras_gift')
scripted_by(34153, 'spell_dru_living_spirit_capstone')
scripted_by(740, 'spell_dru_natures_focus_capstone')

# --- Corrected stock-class replacements (Corrections item 1 in the WP-A brief: RESTO §10's own
# "Stock scripts touched" section is wrong as literally written - CORE-AUDIT/upstream-merge.md
# forbid editing a stock class in place, so WP-B replaces each with a new class in
# spell_druid_resto.cpp, named "<stock ScriptName>_resto" (reconcile the exact name with WP-B's own
# report before this pass finishes; these six pairs are WP-A's half of that displacement). ---

unbind_script(-48496, 'spell_dru_living_seed')
scripted_by(48496, 'spell_dru_living_seed_resto')
scripted_by(48499, 'spell_dru_living_seed_resto')
scripted_by(48500, 'spell_dru_living_seed_resto')

unbind_script(-48539, 'spell_dru_revitalize')
scripted_by(48539, 'spell_dru_revitalize_resto')
scripted_by(48544, 'spell_dru_revitalize_resto')
scripted_by(48545, 'spell_dru_revitalize_resto')

unbind_script(-33763, 'spell_dru_lifebloom')
scripted_by(33763, 'spell_dru_lifebloom_resto')

unbind_script(-48438, 'spell_dru_wild_growth')
scripted_by(48438, 'spell_dru_wild_growth_resto')  # RegisterSpellAndAuraScriptPair covers the aura half under this same name

unbind_script(16864, 'spell_dru_omen_of_clarity')
scripted_by(16864, 'spell_dru_omen_of_clarity_resto')
scripted_by(200600, 'spell_dru_omen_of_clarity_resto')
scripted_by(200601, 'spell_dru_omen_of_clarity_resto')


# --- procs_on() declarations (RESTO §6/§8) not already declared next to their spell in
# druid_trigger_spells.py (Nature's Bounty 17076, Proliferation 200592-4, Revitalize -48539) ---

# Cenarion Ward release - any damage taken (melee, spell or periodic) consumes the ward
procs_on(cenarion_ward_200562, proc_flags=PROC_FLAG_TAKEN_DAMAGE, chance=100)

# Intensity (2,0): the stock Enrage-rage proc row is dead weight on this server - neutralise it
# rather than leave an orphaned positive/negative mismatch (mage -44445 precedent)
procs_on(-17106, proc_flags=0)

# Omen of Clarity (2,1): direct damage (incl. auto attacks), direct Nature heals, and Lifebloom's
# periodic heal only - the broad DONE_* mask below is what the DBC ProcTypeMask used to carry;
# CheckProc (spell_dru_omen_of_clarity_resto) still filters to the exact three qualifying cases.
_OMEN_PROC_FLAGS = (
    PROC_FLAG_DONE_MELEE_AUTO_ATTACK | PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS
    | PROC_FLAG_DONE_RANGED_AUTO_ATTACK | PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS
    | PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS
    | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG | PROC_FLAG_DONE_PERIODIC
)
procs_on(16864, proc_flags=_OMEN_PROC_FLAGS, spell_phase_mask=PROC_SPELL_PHASE_HIT, chance=2, cooldown_ms=2000)
procs_on(omen_of_clarity_200600, proc_flags=_OMEN_PROC_FLAGS, spell_phase_mask=PROC_SPELL_PHASE_HIT, chance=4, cooldown_ms=2000)
procs_on(omen_of_clarity_200601, proc_flags=_OMEN_PROC_FLAGS, spell_phase_mask=PROC_SPELL_PHASE_HIT, chance=6, cooldown_ms=2000)

# Natural Perfection (6,2) capstone - negative whole-chain row (stock -33881 precedent); direct
# Nature heal crits only (Heal::IsDirectNatureHeal, checked in spell_dru_natural_perfection_capstone)
procs_on(-33881, proc_flags=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, spell_type_mask=PROC_SPELL_TYPE_HEAL,
         spell_phase_mask=PROC_SPELL_PHASE_HIT, hit_mask=PROC_HIT_CRITICAL, chance=100)

# Living Seed (7,2) - negative whole-chain row; chance=0 falls back to each rank's own DBC
# ProcChance (33/66/100, unchanged)
procs_on(-48496, proc_flags=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, family_name=0,
         spell_type_mask=PROC_SPELL_TYPE_HEAL, spell_phase_mask=PROC_SPELL_PHASE_HIT,
         hit_mask=PROC_HIT_CRITICAL, chance=0)


# --- World-SQL declarations (RESTO §0.1/§0.13 Q15, CORE-AUDIT row 38; PLAN B11, via WP-T's helpers) ---

# Tree of Life is a transform buff, not a shapeshift form: 5420's bonuses (HoT cost, Healing Touch
# cast time, Regrowth crit) ride along with 33891 via an aura link instead of ShapeshiftMask.
linked_spell(33891, 5420, type=2, comment='Tree of Life buff carries its passive bonuses')


# ============================================================================
# druid-rework FERAL WP-A: script bindings, displaced stock bindings, procs and world SQL (FERAL-WP-BRIEF §1/§2,
# FERAL §3 item 8 with §0.15/§0.16; PLAN B11 - no hand-written pending_db_world). Bindings for the new castables
# (200420-200423, 200425), Swell 200426, Fury Swipe 200429, Maul 6807 and Lacerate 33745 sit next to their
# spell() declarations. Names are load-bearing: they match the classes in spell_druid_feral.cpp (WP-BRIEF §1).
# ============================================================================

scripted_by(ferocious_bite_22568, 'spell_dru_ferocious_bite')  # Sabertooth
for _finisher in (rip_1079, ferocious_bite_22568, savage_roar_52610, maim_22570):
    scripted_by(_finisher, 'spell_dru_primal_precision')  # capstone: finishers take 3 sec off Berserk
scripted_by(rake_1822, 'spell_dru_rake')  # Bloodletting capstone
scripted_by(shred_5221, 'spell_dru_shredding_attacks')  # Shredded Defense
scripted_by(ravage_6785, 'spell_dru_shredding_attacks')
scripted_by(ravage_6785, 'spell_dru_ravage')  # stealth check unless Stampede (Cat); data drops ONLY_STEALTHED
scripted_by(mangle_cat_33876, 'spell_dru_mangle')  # Infected Wounds slow; Improved Mangle capstone (33878 branch)
scripted_by(mangle_bear_33878, 'spell_dru_mangle')
scripted_by(feral_charge_bear_16979, 'spell_dru_feral_charge')  # Stampede
scripted_by(feral_charge_cat_49376, 'spell_dru_feral_charge')
for _builder in (shred_5221, rake_1822, mangle_cat_33876, ravage_6785, pounce_9005):
    scripted_by(_builder, 'spell_dru_berserk_combo_points')  # CORE-AUDIT row 33: +4 combo points under Berserk
scripted_by(savage_defense_200459, 'spell_dru_savage_defense_talent')
scripted_by(savage_defense_200460, 'spell_dru_savage_defense_talent')
scripted_by(regrowth_8936, 'spell_dru_nurturing_instinct_empower')
scripted_by(healing_touch_5185, 'spell_dru_nurturing_instinct_empower')
# Protector of the Pack: damage reduction off in Bestial Fury
for _rank in (protector_of_the_pack_57873, protector_of_the_pack_57876, protector_of_the_pack_57877):
    scripted_by(_rank, 'spell_dru_protector_of_the_pack')
# Survival of the Fittest: AP % only in Bestial Fury
for _rank in (survival_of_the_fittest_33853, survival_of_the_fittest_33855, survival_of_the_fittest_33856):
    scripted_by(_rank, 'spell_dru_survival_of_the_fittest')
# Predatory Instincts: crit damage only in Cat Form
for _rank in (predatory_instincts_33859, predatory_instincts_33866, predatory_instincts_33867):
    scripted_by(_rank, 'spell_dru_predatory_instincts')
for _rank in (splintering_blows_200464, splintering_blows_200465, splintering_blows_200466):
    scripted_by(_rank, 'spell_dru_splintering_blows')  # CORE-AUDIT row 23
for _rank in (bonebreaker_200456, bonebreaker_200457, bonebreaker_200458):
    scripted_by(_rank, 'spell_dru_bonebreaker')  # CORE-AUDIT row 25
scripted_by(heart_of_the_wild_17005, 'spell_dru_heart_of_the_wild_mastery')  # CORE-AUDIT row 29, 5 sec check
scripted_by(barkskin_22812, 'spell_dru_barkskin_floor')  # B7 / CORE-AUDIT row 34; stock spell_dru_barkskin stays bound

# Stock classes replaced by spell_druid_feral.cpp classes (stock class left in place, unbound - CORE-AUDIT §5 item 10).
unbind_script(frenzied_regeneration_22842, 'spell_dru_frenzied_regeneration')
scripted_by(frenzied_regeneration_22842, 'spell_dru_frenzied_regeneration_feral')
unbind_script(-5217, 'spell_dru_tiger_s_fury')
scripted_by(tiger_s_fury_5217, 'spell_dru_tiger_s_fury_feral')
unbind_script(berserk_50334, 'spell_dru_berserk')
scripted_by(berserk_50334, 'spell_dru_berserk_feral')
unbind_script(leader_of_the_pack_24932, 'spell_dru_leader_of_the_pack')
scripted_by(leader_of_the_pack_24932, 'spell_dru_leader_of_the_pack_feral')
unbind_script(savage_defense_62606, 'spell_dru_savage_defense')  # 62606 is now a plain absorb, no script

# FERAL §3 item 8: stock classes whose behaviour is gone.
unbind_script(bear_form_passive_1178, 'spell_dru_bear_form_passive')  # Enrage's armor penalty
unbind_script(dire_bear_form_passive_9635, 'spell_dru_bear_form_passive')
unbind_script(-16972, 'spell_dru_predatory_strikes')  # feral AP from level/weapon (CORE-AUDIT row 35)
unbind_script(-33872, 'spell_dru_nurturing_instinct')  # the old cat healing-taken buff 47179/47180
unbind_script(-17002, 'spell_dru_feral_swiftness')  # replaced by the 24867 form boost
unbind_script(bear_form_5487, 'spell_dru_feral_swiftness')
unbind_script(dire_bear_form_9634, 'spell_dru_feral_swiftness')

# (7,3) Infected Wounds - negative whole-chain row (the stock -48483 row exists; a positive rank row would be
# silently dropped - FERAL §10 "Proc rows"). Shred, Maul, Swipe and Mangle hits, 10% (x Proc Chance, applied
# automatically). Natural Reaction's stock spell_proc -57878 is kept as is.
procs_on(-48483, proc_flags=PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS, family_name=7,
         family_mask=INFECTED_WOUNDS_TRIGGER, spell_type_mask=PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=PROC_SPELL_PHASE_HIT, hit_mask=PROC_HIT_NORMAL | PROC_HIT_CRITICAL, chance=10)

# --- World SQL (FERAL-WP-BRIEF §2) ---

# Bestial Fury (FERAL §0.16): its hidden aura (+50% rage from damage, Polymorph immunity) rides with the form.
linked_spell(bestial_fury_200425.id, bestial_fury_rage_200437.id, type=2,
             comment='Bestial Fury - rage from damage and Polymorph immunity')
# Bestial Fury's 3.5 sec swing: Player::InitDataForForm reads the form row (CORE-AUDIT row 31).
shapeshift_form(ShapeshiftForm.BEAR, attackSpeed=3500)
# Positive despite its armor/threat penalties, so it shows as a buff and can be right-click cancelled (FERAL §0.7).
SPELL_ATTR0_CU_POSITIVE_EFF0 = 0x02000000  # SpellInfo.h SpellCustomAttributes
SPELL_ATTR0_CU_POSITIVE_EFF1 = 0x04000000
SPELL_ATTR0_CU_POSITIVE_EFF2 = 0x08000000
custom_attr(bestial_fury_200425,
            attributes=SPELL_ATTR0_CU_POSITIVE_EFF0 | SPELL_ATTR0_CU_POSITIVE_EFF1 | SPELL_ATTR0_CU_POSITIVE_EFF2)

# Thrash's -5% armor must not stack with caster Faerie Fire 770 (PLAN B5): stock group 1016 "Faerie Fire",
# stack rule 3 (EXCLUSIVE_SAME_EFFECT).
spell_group(1016, thrash_200423)
# SpellMgr::LoadSpellGroupStackRules picks a rule-3 group's shared aura as the MOST FREQUENT aura type among its
# members. With Faerie Fire (Feral) 16857 left in the group after losing its armor effect, the members are 770
# {101, 186}, 16857 {186}, Thrash {3, 101} - a 2-2 tie between armor (101) and stealth-reveal (186) that an
# unordered_multiset iteration breaks arbitrarily; if 186 wins, Thrash and Faerie Fire armor stack. 16857 no
# longer carries anything this group exists for, so it leaves it (770 {101, 186} + Thrash {3, 101} -> 101).
leave_spell_group(1016, faerie_fire_feral_16857)

# Berserk no longer makes Mangle (Bear) hit 3 targets (FERAL §7 (10,1)). The stock row is type 2 (aura link) -
# data/sql/base/db_world/spell_linked_spell.sql: (50334,58923,2,'Berserk - modify target number aura').
unlink_spell(50334, 58923, type=2)

# The old Savage Defense passive is retired (it's a talent now). Trainer 33 is the only one teaching it
# (WP-BRIEF §2: 216/217 and every mod-progression phase file don't); character_spell cleanup is the
# hand-written pending_db_characters file from WP-0.
untrain(62600, trainer_ids=[33])

# Claw 1082 is retired; Shred takes its place at Claw's level 20 with no behind-the-target requirement.
# Both trainers teach both spells (live DB: 33 and 216); character_spell cleanup (Claw -> Shred) is the
# hand-written pending_db_characters file. The stock spell_custom_attr row (5221, 0x20000
# SPELL_ATTR0_CU_REQ_CASTER_BEHIND_TARGET) is what enforced "must be behind"; 0 replaces it with no flags.
untrain(1082, trainer_ids=[33, 216])
trained_by(shred_5221, trainer_id=216, req_level=20, money_cost=2000)
custom_attr(shred_5221, attributes=0)
