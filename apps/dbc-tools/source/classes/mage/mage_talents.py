"""
Mage - talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row.

Split from a single source/classes/mage.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .mage_...` below) resolve.
"""

from lib.dsl.registry import granted_by_talent, skill_line_ability, tab
from .mage_spells import arcane_barrage_44425, flashpoint_200111, arcane_overload_200079, arcane_power_12042, blast_wave_11113, cold_snap_11958, combustion_11129, dragon_s_breath_31661, flurry_200004, focus_magic_54646, frozen_orb_200007, glacial_spike_200002, ice_barrier_11426, icy_veins_12472, living_bomb_44457, pyroblast_11366, summon_water_elemental_31687, temporal_convergence_200078
from .mage_trigger_spells import blazing_speed_200107, burning_soul_200102, fanned_flames_200108, fanned_flames_200109, fanned_flames_200110, impact_crater_200103, impact_crater_200104, lasting_flame_200099, lasting_flame_200100, lasting_flame_200101, scorched_earth_200121, scorched_earth_200122, stoking_the_fire_200124, stoking_the_fire_200125, stoking_the_fire_200126, tinderbox_200105, tinderbox_200106, alacrity_11210, alacrity_12592, alacrity_200071, arcane_concentration_11247, arcane_concentration_12606, arcane_concentration_200076, arcane_empowerment_31579, arcane_empowerment_31582, arcane_empowerment_31583, arcane_flows_44378, arcane_flows_44379, arcane_instability_15058, arcane_instability_15059, arcane_instability_15060, arcane_meditation_11222, arcane_meditation_12839, arcane_meditation_12840, arcane_mind_11232, arcane_mind_12500, arcane_mind_12501, arcane_potency_31571, arcane_potency_31572, arcane_resonance_18462, arcane_resonance_18463, arcane_resonance_18464, arcane_shielding_11252, arcane_shielding_12605, arcane_stability_11237, arcane_stability_12463, arcane_stability_12464, arcane_subtlety_11213, arcane_subtlety_12574, arcane_subtlety_12575, arctic_reach_16757, arctic_reach_16758, arctic_winds_31674, arctic_winds_31675, arctic_winds_31676, biting_cold_200010, biting_cold_200011, biting_cold_200012, blazing_speed_31641, blazing_speed_31642, brain_freeze_44546, brain_freeze_44548, brain_freeze_44549, burning_determination_54747, burning_determination_54749, burning_soul_11083, burning_soul_12351, burnout_44449, burnout_44469, burnout_44470, burnout_44471, burnout_44472, chilled_to_the_bone_44566, chilled_to_the_bone_44567, chilled_to_the_bone_44568, cold_as_ice_55091, cold_as_ice_55092, critical_mass_11115, critical_mass_11367, critical_mass_11368, empowered_fire_31656, empowered_fire_31657, empowered_fire_31658, empowered_frostbolt_31682, empowered_frostbolt_31683, enduring_winter_44557, enduring_winter_44560, enduring_winter_44561, fingers_of_frost_44543, fingers_of_frost_44545, fire_power_11124, fire_power_12378, fire_power_12398, fire_power_12399, fire_power_12400, firestarter_44442, firestarter_44443, flame_throwing_11100, flame_throwing_12353, frost_channeling_11160, frost_channeling_12518, frost_channeling_12519, frost_warding_11189, frost_warding_28332, frostbite_11071, frostbite_12496, frostbite_12497, frozen_core_31667, frozen_core_31668, frozen_core_31669, hot_streak_44445, hot_streak_44446, hot_streak_44448, ice_floes_31670, ice_floes_31672, ice_floes_55094, ice_shards_11207, ice_shards_12672, ice_shards_15047, ignite_11119, ignite_11120, ignite_12846, ignite_12847, ignite_12848, impact_11103, impact_12357, impact_12358, improved_blink_31569, improved_blink_31570, improved_blizzard_11185, improved_blizzard_12487, improved_blizzard_12488, improved_cone_of_cold_11190, improved_cone_of_cold_12489, improved_cone_of_cold_12490, improved_counterspell_11255, improved_counterspell_12598, improved_fire_blast_11078, improved_fire_blast_11080, improved_fireball_11069, improved_fireball_12338, improved_fireball_12339, improved_fireball_12340, improved_fireball_12341, improved_frostbolt_11070, improved_frostbolt_12473, improved_scorch_11095, improved_scorch_12872, improved_scorch_12873, incanter_s_absorption_44394, incanter_s_absorption_44395, incanter_s_absorption_44396, incineration_18459, incineration_18460, incineration_54734, magic_absorption_200075, magic_absorption_29441, magic_absorption_29444, magic_attunement_28574, magic_attunement_54658, master_of_elements_29074, master_of_elements_29075, master_of_elements_29076, mind_mastery_31584, mind_mastery_31585, mind_mastery_31586, missile_barrage_44404, missile_barrage_54486, missile_barrage_54488, molten_fury_31679, molten_fury_31680, molten_shields_11094, molten_shields_13043, netherwind_presence_44400, netherwind_presence_44402, netherwind_presence_44403, permafrost_11175, permafrost_12569, permafrost_12571, piercing_ice_11151, piercing_ice_12952, piercing_ice_12953, playing_with_fire_31638, playing_with_fire_31639, playing_with_fire_31640, precision_29438, precision_29439, precision_29440, prismatic_cloak_31574, prismatic_cloak_31575, pyromaniac_34293, pyromaniac_34295, pyromaniac_34296, shatter_11170, shatter_12982, shatter_12983, shattered_barrier_44745, shattered_barrier_54787, spell_impact_11242, spell_impact_12467, spell_impact_12469, spell_power_200077, spell_power_35578, spell_power_35581, spellblade_200072, spellblade_200073, spellblade_200074, student_of_the_mind_44397, student_of_the_mind_44398, student_of_the_mind_44399, winter_s_chill_11180, winter_s_chill_28592, winter_s_chill_28593, world_in_flames_11108, world_in_flames_12349, world_in_flames_12350


fire_41_tab = tab(
    id=41,
    name='Fire',
    class_mask=128,
    order_index=1,
    spell_icon_id=183,
    skill_line=8,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 332},
)


frost_61_tab = tab(
    id=61,
    name='Frost',
    class_mask=128,
    order_index=2,
    spell_icon_id=188,
    skill_line=6,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 560},
)


arcane_81_tab = tab(
    id=81,
    name='Arcane',
    class_mask=128,
    spell_icon_id=125,
    skill_line=237,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 8},
)


granted_by_talent(
    id=60007,
    tab=arcane_81_tab,
    tier=0,
    column=3,
    ranks=[spellblade_200072, spellblade_200073, spellblade_200074],
    player_castable=False,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (0,3) Burning Soul - moved from (2,3), 3 ranks (was 2).
granted_by_talent(
    id=23,
    tab=fire_41_tab,
    tier=0,
    column=3,
    ranks=[burning_soul_11083, burning_soul_12351, burning_soul_200102],
    player_castable=False,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (7,1) Fanned Flames - REPURPOSED stock talent id 24 (was Molten Shields at (3,1)). See id 27's comment.
granted_by_talent(
    id=24,
    tab=fire_41_tab,
    tier=7,
    column=1,
    ranks=[fanned_flames_200108, fanned_flames_200109, fanned_flames_200110],
    player_castable=False,
)


granted_by_talent(
    id=25,
    tab=fire_41_tab,
    tier=3,
    column=0,
    ranks=[improved_scorch_11095, improved_scorch_12872, improved_scorch_12873],
    player_castable=False,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (0,2) Improved Fireball - 3 ranks (was 5).
granted_by_talent(
    id=26,
    tab=fire_41_tab,
    tier=0,
    column=2,
    ranks=[improved_fireball_11069, improved_fireball_12338, improved_fireball_12339],
    player_castable=False,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (0,1) Lasting Flame - REPURPOSED stock talent id 27 (was Improved Fire Blast at (0,0)):
# DBCDatabaseLoader overlays talent_dbc on the client's Talent.dbc by ID, so a removed talent has to be
# overwritten, not deleted (an absent overlay row leaves the stock talent live).
granted_by_talent(
    id=27,
    tab=fire_41_tab,
    tier=0,
    column=1,
    ranks=[lasting_flame_200099, lasting_flame_200100, lasting_flame_200101],
    player_castable=False,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (2,0) Flame Throwing - rank 2 carries the capstone.
granted_by_talent(
    id=28,
    tab=fire_41_tab,
    tier=2,
    column=0,
    ranks=[flame_throwing_11100, flame_throwing_12353],
    player_castable=False,
)


granted_by_talent(
    id=29,
    tab=fire_41_tab,
    tier=2,
    column=2,
    ranks=[pyroblast_11366],
    player_castable=False,
    flags=1,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (2,1) Impact Crater - REPURPOSED stock talent id 30 (was Impact). See id 27's comment.
granted_by_talent(
    id=30,
    tab=fire_41_tab,
    tier=2,
    column=1,
    ranks=[impact_crater_200103, impact_crater_200104],
    player_castable=False,
)


granted_by_talent(
    id=31,
    tab=fire_41_tab,
    tier=1,
    column=2,
    ranks=[world_in_flames_11108, world_in_flames_12349, world_in_flames_12350],
    player_castable=False,
)


# No depends_on: Pyroblast (29) is 2 tiers above in the same column, with Master of Elements (1639)
# in the intervening cell (3,2) — TalentFrameBase.lua's TalentFrame_DrawLines can't draw a vertical
# prereq line through an occupied cell and throws a Lua error opening the tab (see docs/bugs-and-fixes.md).
granted_by_talent(
    id=32,
    tab=fire_41_tab,
    tier=4,
    column=2,
    ranks=[blast_wave_11113],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=33,
    tab=fire_41_tab,
    tier=4,
    column=1,
    ranks=[critical_mass_11115, critical_mass_11367, critical_mass_11368],
    player_castable=False,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (1,0) Ignite - 3 ranks (was 5). (1,1) is intentionally empty (Burning Determination removed).
granted_by_talent(
    id=34,
    tab=fire_41_tab,
    tier=1,
    column=0,
    ranks=[ignite_11119, ignite_11120, ignite_12846],
    player_castable=False,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (5,2) Fire Power - 3 ranks (was 5).
granted_by_talent(
    id=35,
    tab=fire_41_tab,
    tier=5,
    column=2,
    ranks=[fire_power_11124, fire_power_12378, fire_power_12398],
    player_castable=False,
)


# No depends_on: Critical Mass (33) is 2 tiers above in the same column, with Living Bomb (1852)
# in the intervening cell (5,1) — see id 32's comment above.
granted_by_talent(
    id=36,
    tab=fire_41_tab,
    tier=6,
    column=1,
    ranks=[combustion_11129],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=37,
    tab=frost_61_tab,
    tier=0,
    column=1,
    ranks=[improved_frostbolt_11070, improved_frostbolt_12473],
    player_castable=False,
)


granted_by_talent(
    id=38,
    tab=frost_61_tab,
    tier=0,
    column=0,
    ranks=[frostbite_11071, frostbite_12496, frostbite_12497],
    player_castable=False,
)


granted_by_talent(
    id=61,
    tab=frost_61_tab,
    tier=2,
    column=0,
    ranks=[piercing_ice_11151, piercing_ice_12952, piercing_ice_12953],
    player_castable=False,
)


granted_by_talent(
    id=62,
    tab=frost_61_tab,
    tier=0,
    column=2,
    ranks=[ice_floes_31670, ice_floes_31672, ice_floes_55094],
    player_castable=False,
)


granted_by_talent(
    id=63,
    tab=frost_61_tab,
    tier=3,
    column=0,
    ranks=[improved_blizzard_11185, improved_blizzard_12487, improved_blizzard_12488],
    player_castable=False,
)


granted_by_talent(
    id=64,
    tab=frost_61_tab,
    tier=5,
    column=1,
    ranks=[improved_cone_of_cold_11190, improved_cone_of_cold_12489, improved_cone_of_cold_12490],
    player_castable=False,
)


granted_by_talent(
    id=65,
    tab=frost_61_tab,
    tier=1,
    column=3,
    ranks=[permafrost_11175, permafrost_12569, permafrost_12571],
    player_castable=False,
)


granted_by_talent(
    id=66,
    tab=frost_61_tab,
    tier=2,
    column=1,
    ranks=[frost_channeling_11160, frost_channeling_12518, frost_channeling_12519],
    player_castable=False,
)


granted_by_talent(
    id=67,
    tab=frost_61_tab,
    tier=3,
    column=2,
    ranks=[shatter_11170, shatter_12982, shatter_12983],
    player_castable=False,
)


granted_by_talent(
    id=68,
    tab=frost_61_tab,
    tier=5,
    column=2,
    ranks=[winter_s_chill_11180, winter_s_chill_28592, winter_s_chill_28593],
    player_castable=False,
)


granted_by_talent(
    id=69,
    tab=frost_61_tab,
    tier=2,
    column=2,
    ranks=[icy_veins_12472],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=70,
    tab=frost_61_tab,
    tier=1,
    column=1,
    ranks=[frost_warding_11189, frost_warding_28332],
    player_castable=False,
)


granted_by_talent(
    id=71,
    tab=frost_61_tab,
    tier=6,
    column=1,
    ranks=[ice_barrier_11426],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=72,
    tab=frost_61_tab,
    tier=4,
    column=1,
    ranks=[cold_snap_11958],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=73,
    tab=frost_61_tab,
    tier=4,
    column=0,
    ranks=[ice_shards_11207, ice_shards_12672, ice_shards_15047],
    player_castable=False,
)


granted_by_talent(
    id=74,
    tab=arcane_81_tab,
    tier=0,
    column=0,
    ranks=[alacrity_11210, alacrity_12592, alacrity_200071],
    player_castable=False,
)


granted_by_talent(
    id=75,
    tab=arcane_81_tab,
    tier=1,
    column=1,
    ranks=[arcane_subtlety_11213, arcane_subtlety_12574, arcane_subtlety_12575],
    player_castable=False,
)


granted_by_talent(
    id=76,
    tab=arcane_81_tab,
    tier=0,
    column=1,
    ranks=[arcane_meditation_11222, arcane_meditation_12839, arcane_meditation_12840],
    player_castable=False,
)


granted_by_talent(
    id=77,
    tab=arcane_81_tab,
    tier=4,
    column=3,
    ranks=[arcane_mind_11232, arcane_mind_12500, arcane_mind_12501],
    player_castable=False,
)


granted_by_talent(
    id=80,
    tab=arcane_81_tab,
    tier=0,
    column=2,
    ranks=[arcane_stability_11237, arcane_stability_12463, arcane_stability_12464],
    player_castable=False,
)


granted_by_talent(
    id=81,
    tab=arcane_81_tab,
    tier=1,
    column=2,
    ranks=[spell_impact_11242, spell_impact_12467, spell_impact_12469],
    player_castable=False,
)


granted_by_talent(
    id=82,
    tab=arcane_81_tab,
    tier=2,
    column=0,
    ranks=[arcane_concentration_11247, arcane_concentration_12606, arcane_concentration_200076],
    player_castable=False,
)


granted_by_talent(
    id=83,
    tab=arcane_81_tab,
    tier=3,
    column=0,
    ranks=[arcane_shielding_11252, arcane_shielding_12605],
    player_castable=False,
)


granted_by_talent(
    id=85,
    tab=arcane_81_tab,
    tier=2,
    column=1,
    ranks=[magic_attunement_28574, magic_attunement_54658],
    player_castable=False,
)


granted_by_talent(
    id=86,
    tab=arcane_81_tab,
    tier=4,
    column=1,
    ranks=[arcane_barrage_44425],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=87,
    tab=arcane_81_tab,
    tier=6,
    column=1,
    ranks=[arcane_power_12042],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=88,
    tab=arcane_81_tab,
    tier=3,
    column=1,
    ranks=[improved_counterspell_11255, improved_counterspell_12598],
    player_castable=False,
)


granted_by_talent(
    id=421,
    tab=arcane_81_tab,
    tier=5,
    column=1,
    ranks=[arcane_instability_15058, arcane_instability_15059, arcane_instability_15060],
    player_castable=False,
)


granted_by_talent(
    id=741,
    tab=frost_61_tab,
    tier=3,
    column=1,
    ranks=[arctic_reach_16757, arctic_reach_16758],
    player_castable=False,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (0,0) Incineration - moved from (0,1), absorbs Improved Fire Blast.
granted_by_talent(
    id=1141,
    tab=fire_41_tab,
    tier=0,
    column=0,
    ranks=[incineration_18459, incineration_18460, incineration_54734],
    player_castable=False,
)


granted_by_talent(
    id=1142,
    tab=arcane_81_tab,
    tier=3,
    column=2,
    ranks=[arcane_resonance_18462, arcane_resonance_18463, arcane_resonance_18464],
    player_castable=False,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (3,2) Master of Elements - moved from (3,3); rank 3 carries the capstone.
granted_by_talent(
    id=1639,
    tab=fire_41_tab,
    tier=3,
    column=2,
    ranks=[master_of_elements_29074, master_of_elements_29075, master_of_elements_29076],
    player_castable=False,
)


granted_by_talent(
    id=1649,
    tab=frost_61_tab,
    tier=1,
    column=2,
    ranks=[precision_29438, precision_29439, precision_29440],
    player_castable=False,
)


granted_by_talent(
    id=1650,
    tab=arcane_81_tab,
    tier=1,
    column=0,
    ranks=[magic_absorption_29441, magic_absorption_29444, magic_absorption_200075],
    player_castable=False,
)


granted_by_talent(
    id=1724,
    tab=arcane_81_tab,
    tier=4,
    column=2,
    ranks=[improved_blink_31569, improved_blink_31570],
    player_castable=False,
)


granted_by_talent(
    id=1725,
    tab=arcane_81_tab,
    tier=5,
    column=2,
    ranks=[arcane_potency_31571, arcane_potency_31572],
    player_castable=False,
)


granted_by_talent(
    id=1726,
    tab=arcane_81_tab,
    tier=8,
    column=0,
    ranks=[prismatic_cloak_31574, prismatic_cloak_31575],
    player_castable=False,
)


granted_by_talent(
    id=1727,
    tab=arcane_81_tab,
    tier=6,
    column=0,
    ranks=[arcane_empowerment_31579, arcane_empowerment_31582, arcane_empowerment_31583],
    player_castable=False,
)


granted_by_talent(
    id=1728,
    tab=arcane_81_tab,
    tier=7,
    column=2,
    ranks=[mind_mastery_31584, mind_mastery_31585, mind_mastery_31586],
    player_castable=False,
)


granted_by_talent(
    id=1729,
    tab=arcane_81_tab,
    tier=8,
    column=1,
    ranks=[temporal_convergence_200078],
    player_castable=True,
    skill_line_ability_ids=[30407],
    flags=1,
)


granted_by_talent(
    id=1730,
    tab=fire_41_tab,
    tier=4,
    column=0,
    ranks=[playing_with_fire_31638, playing_with_fire_31639, playing_with_fire_31640],
    player_castable=False,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (7,0) Blazing Speed - moved from (5,0), 3 ranks (was 2); rank 3 carries the capstone.
granted_by_talent(
    id=1731,
    tab=fire_41_tab,
    tier=7,
    column=0,
    ranks=[blazing_speed_31641, blazing_speed_31642, blazing_speed_200107],
    player_castable=False,
)


granted_by_talent(
    id=1732,
    tab=fire_41_tab,
    tier=6,
    column=2,
    ranks=[molten_fury_31679, molten_fury_31680],
    player_castable=False,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (3,1) Pyromaniac - moved from (9,1)
# during the 2026-09-16 tree review (originally moved to (9,1) from (6,0) in the first Phase 2
# pass). (9,1) is now Stoking the Fire, below.
granted_by_talent(
    id=1733,
    tab=fire_41_tab,
    tier=3,
    column=1,
    ranks=[pyromaniac_34293, pyromaniac_34295, pyromaniac_34296],
    player_castable=False,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) 2026-09-16 tree review (1,1) Scorched Earth -
# new talent, 2 ranks. Fresh Talent.dbc id from source/ids.yaml's 60000-60799 block (no removed
# stock talent's id to repurpose at this position - Burning Determination, the old (1,1) resident,
# was already removed in the original Phase 2 pass without keeping its id around).
granted_by_talent(
    id=60008,
    tab=fire_41_tab,
    tier=1,
    column=1,
    ranks=[scorched_earth_200121, scorched_earth_200122],
    player_castable=False,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) 2026-09-16 tree review (9,1) Stoking the Fire
# - new talent, 3 ranks, backfills the slot Pyromaniac vacated above. Fresh Talent.dbc id (60009) -
# Pyromaniac's own stock id (1733) traveled with it to (3,1), so nothing was left behind to reuse
# here either.
granted_by_talent(
    id=60009,
    tab=fire_41_tab,
    tier=9,
    column=1,
    ranks=[stoking_the_fire_200124, stoking_the_fire_200125, stoking_the_fire_200126],
    player_castable=False,
)


granted_by_talent(
    id=1734,
    tab=fire_41_tab,
    tier=7,
    column=2,
    ranks=[empowered_fire_31656, empowered_fire_31657, empowered_fire_31658],
    player_castable=False,
)


# No depends_on: Combustion (36) is 2 tiers above in the same column, with Fanned Flames (24)
# in the intervening cell (7,1) — see id 32's comment above.
granted_by_talent(
    id=1735,
    tab=fire_41_tab,
    tier=8,
    column=1,
    ranks=[dragon_s_breath_31661],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1736,
    tab=frost_61_tab,
    tier=4,
    column=2,
    ranks=[frozen_core_31667, frozen_core_31668, frozen_core_31669],
    player_castable=False,
)


granted_by_talent(
    id=1737,
    tab=frost_61_tab,
    tier=5,
    column=0,
    ranks=[cold_as_ice_55091, cold_as_ice_55092],
    player_castable=False,
)


granted_by_talent(
    id=1738,
    tab=frost_61_tab,
    tier=8,
    column=0,
    ranks=[arctic_winds_31674, arctic_winds_31675, arctic_winds_31676],
    player_castable=False,
)


granted_by_talent(
    id=1740,
    tab=frost_61_tab,
    tier=7,
    column=2,
    ranks=[empowered_frostbolt_31682, empowered_frostbolt_31683],
    player_castable=False,
)


granted_by_talent(
    id=1741,
    tab=frost_61_tab,
    tier=8,
    column=1,
    ranks=[summon_water_elemental_31687],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1826,
    tab=arcane_81_tab,
    tier=4,
    column=0,
    ranks=[spell_power_35578, spell_power_35581, spell_power_200077],
    player_castable=False,
)


granted_by_talent(
    id=1843,
    tab=arcane_81_tab,
    tier=7,
    column=1,
    ranks=[arcane_flows_44378, arcane_flows_44379],
    player_castable=False,
    depends_on={'talent_id': 87, 'rank': 0},
)


granted_by_talent(
    id=1844,
    tab=arcane_81_tab,
    tier=6,
    column=2,
    ranks=[incanter_s_absorption_44394, incanter_s_absorption_44395, incanter_s_absorption_44396],
    player_castable=False,
)


granted_by_talent(
    id=1845,
    tab=arcane_81_tab,
    tier=2,
    column=2,
    ranks=[student_of_the_mind_44397, student_of_the_mind_44398, student_of_the_mind_44399],
    player_castable=False,
)


granted_by_talent(
    id=1846,
    tab=arcane_81_tab,
    tier=9,
    column=1,
    ranks=[netherwind_presence_44400, netherwind_presence_44402, netherwind_presence_44403],
    player_castable=False,
)


granted_by_talent(
    id=1847,
    tab=arcane_81_tab,
    tier=10,
    column=1,
    ranks=[arcane_overload_200079],
    player_castable=True,
    skill_line_ability_ids=[30408],
    flags=1,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (10,1) Flashpoint - REPURPOSED stock talent id 1848 (was Fiery Payback at (7,0)). See id 27's
# comment. Player-castable and talent-granted, hence the SkillLineAbility row (30409, next free in
# source/ids.yaml's 30400-30499 block) that keeps it in the Fire Spellbook tab - fire_41_tab now
# carries skill_line=8 for exactly this (docs/skilllineability-handoff.md).
granted_by_talent(
    id=1848,
    tab=fire_41_tab,
    tier=10,
    column=1,
    ranks=[flashpoint_200111],
    player_castable=True,
    skill_line_ability_ids=[30409],
    flags=1,
)


granted_by_talent(
    id=1849,
    tab=fire_41_tab,
    tier=8,
    column=0,
    ranks=[firestarter_44442, firestarter_44443],
    player_castable=False,
    depends_on={'talent_id': 1735, 'rank': 0},
)


granted_by_talent(
    id=1850,
    tab=fire_41_tab,
    tier=8,
    column=2,
    ranks=[hot_streak_44445, hot_streak_44446, hot_streak_44448],
    player_castable=False,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (6,0) Burnout - moved from (9,1), 3 ranks (was 5); rank 3 carries the capstone. User call 2026-09-15:
# sec 5's tree wins over sec 6's headers (which put Pyromaniac here).
granted_by_talent(
    id=1851,
    tab=fire_41_tab,
    tier=6,
    column=0,
    ranks=[burnout_44449, burnout_44469, burnout_44470],
    player_castable=False,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (5,1) Living Bomb - moved from (10,1).
granted_by_talent(
    id=1852,
    tab=fire_41_tab,
    tier=5,
    column=1,
    ranks=[living_bomb_44457],
    player_castable=False,
    flags=1,
)


granted_by_talent(
    id=1853,
    tab=frost_61_tab,
    tier=2,
    column=3,
    ranks=[fingers_of_frost_44543, fingers_of_frost_44545],
    player_castable=False,
)


granted_by_talent(
    id=1854,
    tab=frost_61_tab,
    tier=6,
    column=2,
    ranks=[brain_freeze_44546, brain_freeze_44548, brain_freeze_44549],
    player_castable=False,
)


granted_by_talent(
    id=1855,
    tab=frost_61_tab,
    tier=8,
    column=2,
    ranks=[enduring_winter_44557, enduring_winter_44560, enduring_winter_44561],
    player_castable=False,
    depends_on={'talent_id': 1741, 'rank': 0},
)


granted_by_talent(
    id=1856,
    tab=frost_61_tab,
    tier=9,
    column=1,
    ranks=[chilled_to_the_bone_44566, chilled_to_the_bone_44567, chilled_to_the_bone_44568],
    player_castable=False,
)


granted_by_talent(
    id=1857,
    tab=frost_61_tab,
    tier=10,
    column=1,
    ranks=[glacial_spike_200002],
    player_castable=True,
    skill_line_ability_ids=[30400],
    flags=1,
)


granted_by_talent(
    id=60001,
    tab=frost_61_tab,
    tier=4,
    column=3,
    ranks=[flurry_200004],
    player_castable=True,
    skill_line_ability_ids=[30401],
    flags=1,
)


granted_by_talent(
    id=60002,
    tab=frost_61_tab,
    tier=7,
    column=1,
    ranks=[frozen_orb_200007],
    player_castable=True,
    skill_line_ability_ids=[30402],
    flags=1,
)


granted_by_talent(
    id=60000,
    tab=frost_61_tab,
    tier=1,
    column=0,
    ranks=[biting_cold_200010, biting_cold_200011, biting_cold_200012],
    player_castable=False,
)


granted_by_talent(
    id=2209,
    tab=arcane_81_tab,
    tier=5,
    column=0,
    ranks=[missile_barrage_44404, missile_barrage_54486, missile_barrage_54488],
    player_castable=False,
)


granted_by_talent(
    id=2211,
    tab=arcane_81_tab,
    tier=2,
    column=3,
    ranks=[focus_magic_54646],
    player_castable=False,
    flags=1,
)


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (5,0) Tinderbox - REPURPOSED stock talent id 2212 (was Burning Determination at (1,1)). See id 27's comment.
granted_by_talent(
    id=2212,
    tab=fire_41_tab,
    tier=5,
    column=0,
    ranks=[tinderbox_200105, tinderbox_200106],
    player_castable=False,
)


granted_by_talent(
    id=2214,
    tab=frost_61_tab,
    tier=6,
    column=0,
    ranks=[shattered_barrier_44745, shattered_barrier_54787],
    player_castable=False,
    depends_on={'talent_id': 71, 'rank': 0},
)


granted_by_talent(
    id=2222,
    tab=arcane_81_tab,
    tier=3,
    column=3,
    ranks=[29447, 55339, 55340],
    player_castable=False,
)


sla_200067_30403 = skill_line_ability(
    id=30403,
    skill_line=237,
    spell_id=200067,
    class_mask=128,
)


sla_200068_30404 = skill_line_ability(
    id=30404,
    skill_line=237,
    spell_id=200068,
    class_mask=128,
)


sla_200069_30405 = skill_line_ability(
    id=30405,
    skill_line=237,
    spell_id=200069,
    class_mask=128,
)


sla_200070_30406 = skill_line_ability(
    id=30406,
    skill_line=237,
    spell_id=200070,
    class_mask=128,
)
