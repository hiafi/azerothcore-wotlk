"""
Hunter - spells and bindings shared across the rework passes (H0 WP-0 owns the six new spell rows;
later stages append binding rows).

Sources: .agents/plans/hunter-rework/hunter-rework.SHARED.md B6.4 (201601), B6.5 (201602), B6.7 (201603),
B6.6 (201604, 201605), B9.3 (201600). Ids: 201600 Glaive Toss, 201601 Aspect of the Dragonhawk explosion,
201602 Aspect of the Viper poison, 201603 Aspect of the Beast pet buff, 201604 Aspect of the Monkey
Versatility buff, 201605 Aspect of the Monkey pet proc aura.

Stock rows are named by bare id in the binding calls below; this file never imports from
hunter_spells.py / hunter_trigger_spells.py. The scripted_by / procs_on / trained_by /
skill_line_ability / creature_template bindings follow the spell rows below. One stock row is
declared here in full: the every-hunter passive 34082 (S2b, user ruling 2026-10-16), a SHARED
class-wide edit that belongs to no spec file; it needs no import.
"""

from lib.dsl import AuraType, CombatRating, Effect, EffectType, School
from lib.dsl.registry import (creature_template, custom_attr, leave_spell_group, procs_on, scripted_by,
                              skill_line_ability, spell, trained_by, unbind_script, unlink_spell, untrain)
from . import _masks as m
from .hunter_bm_spells import bm_dragonhawk_1155
from .hunter_sv_spells import sv_glaive_1154


glaive_toss_201600 = spell(
    id=201600, name='Glaive Toss', school=School.NORMAL,
    cast_time_ms=0, cooldown_ms=15000, range_yards=20.0, mana_cost_pct=4,   # mana placeholder, M (§0.6)
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=60.0, potency_kind='direct',
                    implicit_target_a=6, chain_targets=3)],
    spell_icon_id=85,   # stock Ability_UpgradeMoonGlaive
    # hunter-rework S3a A15 (X18): Improved Glaive Toss's % through tooltip_vars 1154 (`igt`); `${$x1-1}` stays, the
    # capstone's JUMP_TARGETS mod changes the bounce count. TOOLTIP-RECONCILE (a) wording.
    tooltip_vars=sv_glaive_1154,
    raw_overrides={'SpellLevel': 12, 'DefenseType': 3, 'SpellClassSet': 9, 'SpellClassMask_3': 0x40,
                   'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'FacingCasterFlags': 1,
                   'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1,
                   'SpellVisualID_1': 90090, 'Speed': 40.0,   # patch_hunter_vfx_models.py: stock SV 9044 (39635 "Throw Glaive") with the twilight-glaive missile model; Speed 40 so it flies
                   'Description_Lang_enUS': 'Throw a glaive that strikes the target and bounces to ${$x1-1} nearby enemies in combat with you, dealing {pot1*igt} Physical damage to each.'},
)

aspect_of_the_dragonhawk_explosion_201601 = spell(
    id=201601, name='Aspect of the Dragonhawk', school=School.FIRE,
    cast_time_ms=0, range_yards=50000.0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=60.0, potency_kind='direct', time_basis_ms=1500,
                    implicit_target_a=53, implicit_target_b=16, radius_yards=5.0)],   # placeholder, M (§0.5)
    spell_icon_id=2328,
    tooltip_vars=bm_dragonhawk_1155,
    raw_overrides={'SpellLevel': 16, 'DefenseType': 3, 'SpellClassSet': 9, 'SpellClassMask_3': 0x2000000,
                   'AttributesEx3': 0x10000, 'EquippedItemClass': -1,
                   'Description_Lang_enUS': 'Explodes for {pot1*idh} Fire damage to the target and all enemies within $a1 yards.'},
)

aspect_of_the_viper_poison_201602 = spell(
    id=201602, name='Aspect of the Viper', school=School.NATURE, dispel=0,   # Dispel 0: never a "sting" (§2)
    duration_ms=6000, range_yards=50000.0,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000,
                    base_points=49, implicit_target_a=6)],   # live 50 = 0.50% max mana per tick, in hundredths of a percent (the C++ divides by 100)
    spell_icon_id=2227,
    raw_overrides={'SpellLevel': 20, 'DefenseType': 0, 'SpellClassSet': 9, 'SpellClassMask_3': 0x4000000,
                   'AttributesEx3': 0x10000, 'EquippedItemClass': -1,
                   'AuraDescription_Lang_enUS': 'Leaking mana to the hunter.'},
)

aspect_of_the_beast_pet_buff_201603 = spell(
    id=201603, name='Aspect of the Beast', duration_ms=10000, range_yards=50000.0,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127,
                    base_points=14, implicit_target_a=5)],   # live +15%
    spell_icon_id=1510, raw_overrides={'SpellLevel': 20, 'EquippedItemClass': -1, 'AuraDescription_Lang_enUS': 'Damage increased by $s1%.'},
)

# S1b-FIX F-2: the hunter-side marker of a Beast proc (visible, no effect). Applied and removed with 201603 by
# spell_hun_aspect_beast_pet_buff; the tooltip reads 201603's own value. ID from the BM block (PLAN 4.1), after the PT-5 display passives (201858-201874: 201874 is the reserved splash display).
aspect_of_the_beast_marker_201875 = spell(
    id=201875, name='Aspect of the Beast', duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, implicit_target_a=1)],
    spell_icon_id=1510,
    raw_overrides={'SpellLevel': 20, 'EquippedItemClass': -1,
                   'AuraDescription_Lang_enUS': 'Your pet deals $201603s1% more damage.',
                   'Description_Lang_enUS': 'Your pet deals $201603s1% more damage.'},
    notes='S1b-FIX F-2: visible hunter marker of the Beast proc. DUMMY, not passive, no consolidate flag, 10 s as 201603.',
)

aspect_of_the_monkey_versatility_201604 = spell(
    id=201604, name='Aspect of the Monkey', duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT,
                    misc_value=1 << CombatRating.VERSATILITY, base_points=2, implicit_target_a=1)],  # live 3%, §0.4
    spell_icon_id=1549, raw_overrides={'SpellLevel': 4, 'EquippedItemClass': -1, 'AuraDescription_Lang_enUS': 'Versatility increased by $s1%.'},
)

aspect_of_the_monkey_pet_201605 = spell(
    id=201605, name='Aspect of the Monkey', duration_ms=-1, range_yards=50000.0,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=-1, implicit_target_a=5)],
    spell_icon_id=1549,
    raw_overrides={'SpellLevel': 4, 'EquippedItemClass': -1, 'Attributes': 0x80,   # DO_NOT_DISPLAY: hidden on the pet frame
                   'AttributesEx3': 0x100000,   # ALLOW_AURA_WHILE_DEAD: persists through pet death
                   'AttributesEx2': 0x1,        # ALLOW_DEAD_TARGET: lands on a dead pet
                   'ProcTypeMask': 0x100000, 'ProcChance': 100},
)

# User ruling 2026-10-16 (S2b-HANDOFF "drop the hunter's hidden 15% ranged haste", S2b-0VERIFY finding 1): stock
# passive 34082 (every hunter: SkillLine 183, ClassMask 4, AcquireMethod 2), pulled with pull_dsl.py. Its 0-based eff1
# MOD_RANGED_HASTE (140) bp 14 (live 15%) is removed; eff0 PROC_TRIGGER_SPELL -> 34084 (a server-only inert DUMMY,
# no script) is kept as stock, the minimal edit. Knock-on: base hunter GCD back to 1.5 s, Steady Shot 1.5 s and Aimed
# Shot 2.0 s live casts at zero gear haste, Auto Shot 15% slower (the balance stage rebalances).
advantaged_state_dnd_34082 = spell(
    id=34082,
    name='Advantaged State (DND)',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL,
               trigger_spell=34084),
        None,   # was APPLY_AURA MOD_RANGED_HASTE (140) bp 14: removed (user ruling 2026-10-16)
    ],
    spell_icon_id=28,
    notes='pulled from existing data (pull_dsl.py 34082). hunter-rework S2b A1 (user ruling 2026-10-16): eff1 '
          'MOD_RANGED_HASTE 15% removed; eff0 PROC_TRIGGER_SPELL -> 34084 and every other column kept as stock.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 65876, 'ProcChance': 100, 'DurationIndex': 0, 'RangeIndex': 1,
                   'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172,
                   'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188,
                   'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
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
trained_by(19577, trainer_id=204, req_level=30)   # Intimidation: baseline since row 1387 became Command II (S1a A12); SpellLevel 30 unchanged
trained_by(34490, trainer_id=204, req_level=14)   # Silencing Shot: baseline since row 1808 became Falcon's Mark (S2a A21); SpellLevel 14
trained_by(glaive_toss_201600, 204, req_level=12)

# Mail (8737) is granted automatically at login by Custom_WeaponProficiency (dungeon-prereqs S1), so the level-40
# trainer row goes. The Shaman row (trainer 210) is retired in the shaman files.
untrain(8737, [204])

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
# hunter-rework S3a A11 (SURVIVAL 8.1): the B13 interim row, edited in place (the only -53290 row): HUNTING_PARTY_PROC,
# HIT, crit, no TRIGGERED_CAN_PROC, the eff1 Agility / eff2 RAP auras disabled; chance 0 = DBC ProcChance 100.
procs_on(-53290, proc_flags=0x100, family_name=9, family_mask=m.HUNTING_PARTY_PROC,
         spell_type_mask=1, spell_phase_mask=0x2, hit_mask=0x2, attributes_mask=0, disable_effects_mask=0x6,
         chance=0)                                                                         # Hunting Party
procs_on(-53256, proc_flags=0x100, family_name=9, family_mask=(0, 0, 0x20000000),
         spell_phase_mask=0x1, hit_mask=0, chance=0)   # Cobra Strikes: S1b resets Arcane Shot on a CAST-phase Steady Shot
# S2a (MARKSMANSHIP 8, WP brief resolution 2): -53234 narrowed in place to Steady + Aimed crits (Chimera's d2 b0
# dropped), ProcFlags 0x100 (= the ranks' DBC ProcTypeMask) and SpellTypeMask DAMAGE written out; the other columns
# keep the live row's 0. This is the only -53234 row (hunter_mm_spells.py must not declare one).
procs_on(-53234, proc_flags=0x100, family_name=9, family_mask=(0x20000, 0, 0x20000000),
         spell_type_mask=1, spell_phase_mask=0x2, hit_mask=0x2)                            # Piercing Shots
procs_on(-53221, proc_flags=0, family_name=9, family_mask=(0, 0, 0x20000000),
         spell_phase_mask=2)                                                               # Improved Steady Shot
# hunter-rework S3a A12 (SURVIVAL 8.1, SV-B1): the H0 row, edited in place (the only -34497 row): THRILL_PROC (no d2 b9,
# the blasts), CAST phase, crit, the eff1 cut DUMMY disabled; chance 0 = DBC ProcChance 50 / 100, Proc Chance applies.
procs_on(-34497, proc_flags=0x100, family_name=9, family_mask=m.THRILL_PROC,
         spell_type_mask=1, spell_phase_mask=0x1, hit_mask=0x2, attributes_mask=0, disable_effects_mask=0x2,
         chance=0)                                                                         # Thrill of the Hunt

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
scripted_by(aspect_of_the_beast_pet_buff_201603, "spell_hun_aspect_beast_pet_buff")
scripted_by(aspect_of_the_dragonhawk_explosion_201601, "spell_hun_aspect_of_the_dragonhawk_explosion")
scripted_by(aspect_of_the_viper_poison_201602, "spell_hun_aspect_of_the_viper_poison")
scripted_by(glaive_toss_201600, "spell_hun_glaive_toss")
scripted_by(3044, "spell_hun_shot_mana")
scripted_by(2973, "spell_hun_shot_mana")
unbind_script(13161, "spell_hun_aspect_of_the_beast")
unbind_script(61669, "spell_hun_aspect_of_the_beast")
unbind_script(34074, "spell_hun_ascpect_of_the_viper")

# --- Snake Trap snakes rebound to the rework AI (B11) ---
creature_template(19921, "Viper", ScriptName="npc_pet_hunter_snake_trap_rework", minlevel=30, maxlevel=60)
creature_template(19833, "Venomous Snake", ScriptName="npc_pet_hunter_snake_trap_rework", minlevel=30, maxlevel=60)
