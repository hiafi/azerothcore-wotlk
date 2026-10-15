"""
Hunter - spells and bindings shared across the rework passes (H0 WP-0 owns the six new spell rows;
later stages append binding rows).

Sources: .agents/plans/hunter-rework/hunter-rework.SHARED.md B6.4 (201601), B6.5 (201602), B6.7 (201603),
B6.6 (201604, 201605), B9.3 (201600). Ids: 201600 Glaive Toss, 201601 Aspect of the Dragonhawk explosion,
201602 Aspect of the Viper poison, 201603 Aspect of the Beast pet buff, 201604 Aspect of the Monkey
Versatility buff, 201605 Aspect of the Monkey pet proc aura.

Stock rows are named by bare id in the binding calls below; this file never imports from
hunter_spells.py / hunter_trigger_spells.py. The scripted_by / procs_on / trained_by /
skill_line_ability / creature_template bindings follow the spell rows below.
"""

from lib.dsl import AuraType, CombatRating, Effect, EffectType, School
from lib.dsl.registry import (creature_template, custom_attr, leave_spell_group, procs_on, scripted_by,
                              skill_line_ability, spell, trained_by, unbind_script, unlink_spell)


glaive_toss_201600 = spell(
    id=201600, name='Glaive Toss', school=School.NORMAL,
    cast_time_ms=0, cooldown_ms=15000, range_yards=20.0, mana_cost_pct=4,   # mana placeholder, M (§0.6)
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=60.0, potency_kind='direct',
                    implicit_target_a=6, chain_targets=3)],
    spell_icon_id=85,   # stock Ability_UpgradeMoonGlaive
    raw_overrides={'SpellLevel': 12, 'DefenseType': 3, 'SpellClassSet': 9, 'SpellClassMask_3': 0x40,
                   'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'FacingCasterFlags': 1,
                   'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1,
                   'SpellVisualID_1': 9044,   # stock 39635 "Throw Glaive" (the glaives of Azzinoth); Speed left 0, V1
                   'Description_Lang_enUS': 'Throw a glaive at the target, dealing {pot1} Physical damage to it and to up to ${$x1-1} other nearby enemies in combat with you.'},
)

aspect_of_the_dragonhawk_explosion_201601 = spell(
    id=201601, name='Aspect of the Dragonhawk', school=School.FIRE,
    cast_time_ms=0, range_yards=50000.0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=60.0, potency_kind='direct', time_basis_ms=1500,
                    implicit_target_a=53, implicit_target_b=16, radius_yards=5.0)],   # placeholder, M (§0.5)
    spell_icon_id=2328,
    raw_overrides={'SpellLevel': 16, 'DefenseType': 3, 'SpellClassSet': 9, 'SpellClassMask_3': 0x2000000,
                   'AttributesEx3': 0x10000, 'EquippedItemClass': -1,
                   'Description_Lang_enUS': 'Explodes for {pot1} Fire damage to the target and all enemies within $a1 yards.'},
)

aspect_of_the_viper_poison_201602 = spell(
    id=201602, name='Aspect of the Viper', school=School.NATURE, dispel=0,   # Dispel 0: never a "sting" (§2)
    duration_ms=6000, range_yards=50000.0,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000,
                    base_points=4, implicit_target_a=6)],   # live 5 = 0.5% max mana per tick, placeholder M (§0.3)
    spell_icon_id=2227,
    raw_overrides={'SpellLevel': 20, 'DefenseType': 0, 'SpellClassSet': 9, 'SpellClassMask_3': 0x4000000,
                   'AttributesEx3': 0x10000, 'EquippedItemClass': -1,
                   'AuraDescription_Lang_enUS': 'Leaking mana to the hunter.'},
)

aspect_of_the_beast_pet_buff_201603 = spell(
    id=201603, name='Aspect of the Beast', duration_ms=10000, range_yards=50000.0,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127,
                    base_points=14, implicit_target_a=5)],   # live +15%
    spell_icon_id=1510, raw_overrides={'SpellLevel': 20, 'AuraDescription_Lang_enUS': 'Damage increased by $s1%.'},
)

aspect_of_the_monkey_versatility_201604 = spell(
    id=201604, name='Aspect of the Monkey', duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT,
                    misc_value=1 << CombatRating.VERSATILITY, base_points=2, implicit_target_a=1)],  # live 3%, §0.4
    spell_icon_id=1549, raw_overrides={'SpellLevel': 4, 'AuraDescription_Lang_enUS': 'Versatility increased by $s1%.'},
)

aspect_of_the_monkey_pet_201605 = spell(
    id=201605, name='Aspect of the Monkey', duration_ms=-1, range_yards=50000.0,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=-1, implicit_target_a=5)],
    spell_icon_id=1549,
    raw_overrides={'SpellLevel': 4, 'Attributes': 0x80,   # DO_NOT_DISPLAY: hidden on the pet frame
                   'AttributesEx3': 0x100000,   # ALLOW_AURA_WHILE_DEAD: persists through pet death
                   'AttributesEx2': 0x1,        # ALLOW_DEAD_TARGET: lands on a dead pet
                   'ProcTypeMask': 0x100000, 'ProcChance': 100},
)


# --- Trainer rows (SHARED B1; money_cost is ignored on trainers 204 / 205) ---
trained_by(56641, 205, req_level=8)
trained_by(34477, 204, req_level=20)
trained_by(34600, 204, req_level=30)
trained_by(53351, 204, req_level=40)
trained_by(60192, 204, req_level=46)
trained_by(61846, 204, req_level=16)
trained_by(13161, 204, req_level=20)   # replaces the live @30 row (same key)
trained_by(53271, 204, req_level=56)
trained_by(62757, 204, req_level=10)
# Silencing Shot 34490 / Intimidation 19577 are still talent spells (LoadTrainers drops them): the baseline grant moves to
# S1 (Intimidation) / S2 (Silencing Shot), user 2026-10-14.
trained_by(glaive_toss_201600, 204, req_level=12)

# --- Glaive Toss spellbook entry (B9.3) ---
skill_line_ability(id=30540, skill_line=51, spell_id=201600, class_mask=4)

# --- Aspect spell_proc rows (B6.1) ---
procs_on(-13165, proc_flags=0x140, family_name=9, spell_phase_mask=0x3, hit_mask=0x2, cooldown_ms=30000)   # Hawk
procs_on(-61846, proc_flags=0x140, family_name=9, spell_phase_mask=0x3, cooldown_ms=3000)    # Dragonhawk
procs_on(13161, proc_flags=0x140, family_name=9, spell_phase_mask=0x3, cooldown_ms=30000)    # Beast
procs_on(34074, proc_flags=0x140, family_name=9, spell_phase_mask=0x3)                       # Viper (was type 1 / HIT)
procs_on(13163, proc_flags=0x100000, cooldown_ms=20000)   # Monkey (was HitMask DODGE)
procs_on(aspect_of_the_monkey_pet_201605, proc_flags=0x100000, chance=100.0)   # the real roll is scripted

# --- B13 interim re-keys: d1 b0 -> d2 b29 (every other column copied from the live row) ---
procs_on(-53290, proc_flags=0, family_name=9, family_mask=(0x800, 0, 0x20000200),
         spell_type_mask=1, spell_phase_mask=2, hit_mask=2, attributes_mask=2)             # Hunting Party
procs_on(-53256, proc_flags=0, family_name=9, family_mask=(0x800, 0x800000, 0x20000000),
         spell_phase_mask=2, hit_mask=2)                                                   # Cobra Strikes
procs_on(-53234, proc_flags=0, family_name=9, family_mask=(0x20000, 0, 0x20000001),
         spell_phase_mask=2, hit_mask=2)                                                   # Piercing Shots
procs_on(-53221, proc_flags=0, family_name=9, family_mask=(0, 0, 0x20000000),
         spell_phase_mask=2)                                                               # Improved Steady Shot
procs_on(-34497, proc_flags=0, family_name=9, family_mask=(0x60800, 0x800000, 0x20000201),
         spell_type_mask=1, spell_phase_mask=2, hit_mask=2)                                # Thrill of the Hunt

# --- Viper loses effect 1 (B6): the stock row 34074 = 0x0E000000 (POSITIVE_EFF0|1|2) would log "no EFFECT_1/2" at boot ---
custom_attr(34074, attributes=0x02000000)   # SPELL_ATTR0_CU_POSITIVE_EFF0

# --- Dragonhawk's dodge rider is retired (B6.1) ---
unlink_spell(61846, 61848, type=2)

# SHARED 5: Scorpid Sting is now a plain damage-dealt debuff; no exclusivity with other classes' debuffs. Live group 1060
# "Hit Chance Debuffs" (stack rule 3) still lists 3043 with Insect Swarm 5570 and would stop two hunters' stings stacking.
leave_spell_group(1060, 3043)

# --- Script bindings (B6.8, B2/B3/B9.1) ---
scripted_by(13165, "spell_hun_aspect_proc")
scripted_by(61846, "spell_hun_aspect_proc")
scripted_by(13161, "spell_hun_aspect_proc")
scripted_by(34074, "spell_hun_aspect_proc")
scripted_by(13163, "spell_hun_aspect_of_the_monkey")
scripted_by(aspect_of_the_monkey_pet_201605, "spell_hun_aspect_of_the_monkey_pet")
scripted_by(aspect_of_the_dragonhawk_explosion_201601, "spell_hun_aspect_of_the_dragonhawk_explosion")
scripted_by(aspect_of_the_viper_poison_201602, "spell_hun_aspect_of_the_viper_poison")
scripted_by(glaive_toss_201600, "spell_hun_glaive_toss")
scripted_by(56641, "spell_hun_shot_mana")
scripted_by(3044, "spell_hun_shot_mana")
scripted_by(2973, "spell_hun_shot_mana")
unbind_script(13161, "spell_hun_aspect_of_the_beast")
unbind_script(61669, "spell_hun_aspect_of_the_beast")
unbind_script(34074, "spell_hun_ascpect_of_the_viper")

# --- Snake Trap snakes rebound to the rework AI (B11) ---
creature_template(19921, "Viper", ScriptName="npc_pet_hunter_snake_trap_rework", minlevel=30, maxlevel=60)
creature_template(19833, "Venomous Snake", ScriptName="npc_pet_hunter_snake_trap_rework", minlevel=30, maxlevel=60)
