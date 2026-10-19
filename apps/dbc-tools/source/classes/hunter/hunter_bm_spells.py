"""
Hunter - Beast Mastery S1a helper and commanded-pet spells (hunter-rework BEAST-MASTERY.md 2.1 / 4.3-4.11).

Skeleton written by S1a 0-dsl (variable stems and Names frozen for HunterData.h), completed by S1a WP-A1. S1b (WP-A1)
adds 201802 Stampede, 201803 Steady Shot (Nature), 201809 the pet proc carrier, the Stampede guardians 300200-300207,
the S1b proc rows / script bindings, and the PT-5 Command display passives 201858-201873. EquippedItemClass -1 on
every row (L1).
"""

from lib.dsl import AuraType, Effect, EffectType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import (
    const, creature_model, creature_template, custom_attr, linked_spell, pot_text, procs_on, product, scripted_by,
    spell, spell_group, spell_group_rule, talent_mult, tooltip_vars, unbind_script,
)
from . import _masks as m
from .hunter_pet import PET_AP_FROM_RAP_PCT, PET_AP_FROM_SP_PCT

# ---- constants (BEAST-MASTERY.md 13; the C++ header names are the strings) ----
STAMPEDE_BEAST_COUNT = const('STAMPEDE_BEAST_COUNT', 3, 'Beasts Stampede summons (BM 13).')
STAMPEDE_SPREAD_YD = const('STAMPEDE_SPREAD_YD', 3.0, 'Stampede ring radius around the destination, yards (BM 13).')
KILL_COMMAND_BW_REDUCTION_MS = const('KILL_COMMAND_BW_REDUCTION_MS', 5000, 'Kill Command cut to the Bestial Wrath cooldown, ms (BM 13).')
BEAST_CLEAVE_RADIUS_YD = const('BEAST_CLEAVE_RADIUS_YD', 8.0, 'Beast Cleave splash radius around the victim, yards (BM 13).')
SPIKED_COLLAR_MAX_TARGETS = const('SPIKED_COLLAR_MAX_TARGETS', 2, 'Spiked Collar extra targets (BM 13).')
SPIKED_COLLAR_RADIUS_YD = const('SPIKED_COLLAR_RADIUS_YD', 8.0, 'Spiked Collar splash radius around the target, yards (BM 13).')
IAOTV_CAPSTONE_MANA_PCT = const('IAOTV_CAPSTONE_MANA_PCT', 1, 'Improved Aspect of the Viper capstone mana, percent of max mana (BM 13).')
PHOENIX_PLUME_REVIVE_PCT = const('PHOENIX_PLUME_REVIVE_PCT', 50, "Phoenix's Plume revive health, percent (BM 13).")
PHOENIX_PLUME_REVIVE_DELAY_MS = const('PHOENIX_PLUME_REVIVE_DELAY_MS', 1000, "Phoenix's Plume revive delay, ms (BM 13).")

SWIPE_SPLASH_PCT = const('SWIPE_SPLASH_PCT', 50, 'Swipe command splash share of the primary hit, percent.')
COMMAND_DISPLAY_OFFSET = const(
    'COMMAND_DISPLAY_OFFSET', 138,
    'PT-5: the pet-spellbook display passive of commanded spell N is N + this (201720..201735 -> 201858..201873).',
)

# ---- tooltip_vars (BM 5.3; rank spell ids are bare because hunter_bm_ranks.py / pulled ranks resolve by id) ----
bm_steady_shot_1150 = tooltip_vars(
    1150, "Talents on Steady Shot",
    fi=talent_mult([34455, 34459, 34460], effect=3),
    # S2a (MARKSMANSHIP 5.12, R2-6): MM's Precise Shots and Ranged Weapon Specialization, appended in place.
    ps=talent_mult([19454, 19455, 19456], effect=1),
    rws=talent_mult([19507, 19508, 19509], effect=1),
    steady=product('fi', 'ps', 'rws'),
)
bm_dragonhawk_1155 = tooltip_vars(
    1155, "Improved Dragonhawk on the explosion",
    idh=talent_mult([201824, 201825], effect=2),
)
bm_kill_command_1160 = tooltip_vars(
    1160, "BM talents on Kill Command",
    ff=talent_mult([35029, 35030], effect=2),
    cat=talent_mult([34462, 34464, 34465], effect=1),
    kc=product('ff', 'cat'),
)
bm_stomp_1161 = tooltip_vars(
    1161, "Earthshaker on Stomp",
    es=talent_mult([201844, 201845], effect=1),
)

# ---- helpers ----

_PET_SCALING = (PET_AP_FROM_RAP_PCT['value'], PET_AP_FROM_SP_PCT['value'])

# Command presses (BM 4.3 / S1a A1): hunter button, d2 b21, IS_ABILITY (0x10) so 201562 hastes it, AttributesEx 0 (a press
# must never swap Auto Shot for melee), GCD 1500 / category 133. Taught by talent rows 60201 / 1387 (no trainer, L13).
command_i_201800 = spell(
    id=201800,
    name='Command I',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=0, implicit_target_a=6),
    ],
    spell_icon_id=3487,
    notes='S1a BM 4.3 / A1: Command I. DUMMY on the target (spell_hun_command), 30 s, 3% base mana, 40 yd, d2 b21 (COMMAND_PRESS), GCD 1500/133, AttributesEx 0.',
    raw_overrides={
        'EquippedItemClass': -1, 'SpellLevel': 20, 'BaseLevel': 20, 'DefenseType': 0, 'SpellClassSet': 9,
        'SpellClassMask_3': m.COMMAND_PRESS, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500,
        # Stock instants use SpellCastTimes row 1; the DSL's default 0 has no row in the client's SpellCastTimes.dbc.
        'CastingTimeIndex': 1,
        'Description_Lang_enUS': 'Commands your pet to use its first command on your target. Requires a pet.',
    },
)

command_ii_201801 = spell(
    id=201801,
    name='Command II',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=0, implicit_target_a=6),
    ],
    spell_icon_id=2318,
    notes='S1a BM 4.3 / A1: Command II. As Command I: 60 s, 4% base mana, learn level 30.',
    raw_overrides={
        'EquippedItemClass': -1, 'SpellLevel': 30, 'BaseLevel': 30, 'DefenseType': 0, 'SpellClassSet': 9,
        'SpellClassMask_3': m.COMMAND_PRESS, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500,
        # Stock instants use SpellCastTimes row 1; the DSL's default 0 has no row in the client's SpellCastTimes.dbc.
        'CastingTimeIndex': 1,
        'Description_Lang_enUS': 'Commands your pet to use its second command on your target. Requires a pet.',
    },
)

# Stomp 201804 (BM 4.7): pet-cast AoE, data only in S1a. Visual 7429 = Thunderstomp 63900. Attributes copied from Bite (the
# commanded-spell template); only the radius/area effect differs.
stomp_pet_201804 = spell(
    id=201804,
    name='Stomp',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=40.0, potency_kind='direct',
               implicit_target_a=53, implicit_target_b=16, radius_yards=8.0),
    ],
    pet_owner_scaling=_PET_SCALING,
    spell_icon_id=129,
    tooltip_vars=bm_stomp_1161,
    notes='S1a BM 4.7 / 0.1: pet-cast Stomp, data only (S1b casts it). ap_potency 40 (guess, M tunes), 8 yd around the target, d1 b28 + d2 b24 (STOMP_CARRIER; Earthshaker reads d2 b24). Visual 7429 from Thunderstomp 63900.',
    raw_overrides={
        'EquippedItemClass': -1, 'SpellLevel': 30, 'DefenseType': 2, 'PreventionType': 2, 'AttributesEx': 0x200,
        'SpellClassSet': 9, 'SpellClassMask_2': m.STOMP_CARRIER[1], 'SpellClassMask_3': m.STOMP_CARRIER[2],
        'SpellVisualID_1': 7429,
        'Description_Lang_enUS': 'Deals {pot1*es} Physical damage to all enemies within $a1 yards.',
    },
)

# Spiked Collar / Beast Cleave copies (BM 4.8 / 4.9, 0.5): Physical, family 0, share of final damage via script BP, no caster
# mods / crit / procs, ignore armor (custom_attr 0x8000), 50000 yd (triggered casts are range-checked, L6).
_COPY_RAW = {
    'EquippedItemClass': -1, 'DefenseType': 0, 'SpellClassSet': 0,
    'AttributesEx2': 0x20000000, 'AttributesEx3': 0x20000000 | 0x10000 | 0x40000,
}

spiked_collar_strike_201805 = spell(
    id=201805,
    name='Spiked Collar',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=6,
               potency_excluded='share of final Kill Command damage; BP from script (BM 4.9, PLAN 2)'),
    ],
    spell_icon_id=2934,
    notes='S1a BM 4.9: hunter-cast extra Kill Command hit (Spiked Collar r3), script BP. Physical, family 0, CANT_CRIT, IGNORE_CASTER_MODIFIERS | SUPPRESS_CASTER_PROCS | ALWAYS_HIT, custom attr IGNORE_ARMOR | NO_POSITIVE_TAKEN_BONUS (0x208000, S1a-3).',
    raw_overrides={**_COPY_RAW, 'SpellLevel': 15},
)

beast_cleave_buff_201806 = spell(
    id=201806,
    name='Beast Cleave',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),   # marker on the hunter
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=5, apply_aura=AuraType.DUMMY),   # pet: 50% share
    ],
    spell_icon_id=90235,
    notes='S1a BM 4.8 / A5: 12 s buff. eff0 marker on the hunter (bp -1), eff1 proc carrier on the pet (TargetA 5, bp 49 = 50%, the one place the share lives). procs_on: flags 0x10114, spell phase 0x2 (HIT), 100%, attributes_mask 0x2 (TRIGGERED_CAN_PROC) so triggered commands reach it (L8).',
    raw_overrides={
        'EquippedItemClass': -1, 'SpellLevel': 40, 'ProcTypeMask': 0x10114, 'ProcChance': 100,
        'AuraDescription_Lang_enUS': "Your pet's attacks also hit nearby enemies.",
    },
)
procs_on(beast_cleave_buff_201806, proc_flags=0x10114, spell_phase_mask=0x2, chance=100.0, attributes_mask=0x2)

beast_cleave_strike_201807 = spell(
    id=201807,
    name='Beast Cleave',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=6,
               potency_excluded='share of final pet/Kill Command damage; BP from script (PLAN 2, C30)'),
    ],
    spell_icon_id=90235,
    notes='S1a BM 4.8: Beast Cleave copy damage (pet- or hunter-cast), script BP. Physical, family 0, CANT_CRIT, IGNORE_CASTER_MODIFIERS | SUPPRESS_CASTER_PROCS | ALWAYS_HIT, custom attr IGNORE_ARMOR | NO_POSITIVE_TAKEN_BONUS (0x208000, S1a-3).',
    raw_overrides={**_COPY_RAW, 'SpellLevel': 40},
)

culling_the_herd_buff_201808 = spell(
    id=201808,
    name='Culling the Herd',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
    ],
    spell_icon_id=4115,
    notes='S1a BM 4.9: 10 s damage buff, cast by spell_hun_bm_pet_procs (S1b). Target 1 lands on the caster, so the hunter and the pet each cast their own copy (B4). Amount from the rank by script (SPELLVALUE_BASE_POINT0). S1b brief #9: the aura text prints no number (3.3.5 sends no aura amounts, so $s1 would show the DBC 1).',
    raw_overrides={
        'EquippedItemClass': -1, 'SpellLevel': 30,
        'AuraDescription_Lang_enUS': 'Damage dealt increased.',
    },
)

phoenix_s_plume_lockout_201810 = spell(
    id=201810,
    name="Phoenix's Plume",
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2787,
    notes='S1a BM 4.10: 10 min lockout marker on the hunter, data only (S1b). Negative (custom attr 0x1000), AttributesEx3 DEATH_PERSISTENT (0x100000), Dispel 0.',
    raw_overrides={
        'EquippedItemClass': -1, 'SpellLevel': 15, 'AttributesEx3': 0x100000,
        'AuraDescription_Lang_enUS': 'Your pet cannot rise again yet.',
    },
)

# Passives (BM 4.11). Stored = live - 1 for SpellMods. Cobra Shot's transform is live -2000 ms, stored -2001 (S1b PT-2):
# SpellInfo::CalcCastTime adds 500 ms to every ranged-slot shot before mods, so Steady Shot's real base is its index + 500.
cobra_shot_transform_201811 = spell(
    id=201811,
    name='Cobra Shot',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1,
               apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CASTING_TIME),
    ],
    spell_icon_id=2236,
    notes='S1a BM 4.11, S1b PT-2: hidden passive, Steady Shot cast time live -2000 ms (stored -2001), mask (0,0,0x20000000) in EffectSpellClassMaskA_3. CalcCastTime adds 500 ms to the ranged-slot Steady Shot before mods (live base 1000 ms index + 500 = 1500 after PT-3), so -2000 reaches 0 whatever the index. Granted by linked_spell(201851, 201811, 2); spell group 1231 (exclusive transforms).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 9, 'EffectSpellClassMaskA_3': m.STEADY_SHOT_MASK[2]},
)

beast_within_mastery_201812 = spell(
    id=201812,
    name='The Beast Within',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1,
               apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1,
               apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000),
    ],
    spell_icon_id=2229,
    notes='S1a BM 4.11 / A7: hidden passive, Kill Command +Mastery %. eff0 SPELLMOD_DAMAGE on (0,0x800,0) = KC_READER (EffectSpellClassMaskA_2), amount set by spell_hun_tbw_mastery; eff1 PERIODIC_DUMMY 1000 ms refresh tick. Granted by linked_spell(201857, 201812, 2).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 9, 'EffectSpellClassMaskA_2': m.KC_READER[1]},
)

pathfinding_capstone_201813 = spell(
    id=201813,
    name='Pathfinding',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1,
               apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.EFFECT1),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1,
               apply_aura=AuraType.MOD_MOUNTED_SPEED_NOT_STACK),
    ],
    spell_icon_id=1181,
    notes='S1a BM 4.11: hidden capstone passive. eff0 SPELLMOD_EFFECT1 live +10 on (0x200000,0,0) (Cheetah / Pack, EffectSpellClassMaskA_1), eff1 mounted speed +10% (aura 172). Granted by linked_spell(201820, 201813, 2).',
    raw_overrides={
        'EquippedItemClass': -1, 'SpellClassSet': 9,
        'EffectSpellClassMaskA_1': m.ASPECT_OF_THE_CHEETAH_PACK,
    },
)


# --- commanded pet spells 201720-201736 (BEAST-MASTERY 4.5, PET 4.9, S1a A2) ---
# Common: pet-cast, instant, no cost/cooldown/GCD, never learned. Attributes from Bite 17253 (0x50010, Ex 0x200, Ex2-7 0),
# d1 b28 + d2 b22 (COMMANDED_PET_SPELLS_CARRIER), SpellLevel 1, Dispel 0, SCHOOL_DAMAGE / PERIODIC_DAMAGE only (never a
# weapon-damage effect). Real ranges: CheckPetCanAct reads them. DefenseType is the DBC DmgClass column: 2 melee, 3 ranged.

def _cmd_raw(visual, dmg_class=2, prevention=2):
    return {
        'EquippedItemClass': -1, 'BaseLevel': 1, 'SpellLevel': 1, 'AttributesEx': 0x200,
        'DefenseType': dmg_class, 'PreventionType': prevention, 'SpellClassSet': 9,
        'SpellClassMask_2': m.COMMANDED_PET_SPELLS_CARRIER[1], 'SpellClassMask_3': m.COMMANDED_PET_SPELLS_CARRIER[2],
        'SpellVisualID_1': visual,
    }


def _direct(potency, **kw):
    return Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=potency, potency_kind='direct', implicit_target_a=6, **kw)


def _dot(rate, amplitude, **kw):
    return Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, ap_potency=rate,
                  potency_kind='periodic', amplitude=amplitude, **kw)


lunge_command_201720 = spell(
    id=201720,
    name='Lunge',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=25.0,
    effects=[
        Effect(type=41, implicit_target_a=6),    # SPELL_EFFECT_JUMP to the target
        _direct(360.0),
    ],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: Wolf I. eff0 JUMP (41) to the target, eff1 360 Physical (TUNE1: was 400). 25 yd (the jump reach) but DmgClass MELEE (B16). Visual 519 from pet Charge 61685. If the one-spell Lunge fails the playtest, split 201737 (not built).',
    raw_overrides={**_cmd_raw(519),
                   'Description_Lang_enUS': 'Leap to the target and strike it for {pot2} Physical damage.'},
)

rip_throat_command_201721 = spell(
    id=201721,
    name='Rip Throat',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[_direct(850.0)],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: Wolf II, 850 Physical (TUNE1: was 1000), melee. Visual 2275 from Ravage 6785.',
    raw_overrides={**_cmd_raw(2275), 'RangeIndex': 2,
                   'Description_Lang_enUS': "Tear at the target's throat, causing {pot1} Physical damage."},
)

rake_command_201722 = spell(
    id=201722,
    name='Rake',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=9000,
    effects=[
        _direct(200.0),
        _dot(50.0, 3000, mechanic=15, implicit_target_a=6),
    ],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: Cat I. eff0 200 direct, eff1 PERIODIC_DAMAGE 50/tick (rate, 0.15), amplitude 3000, 9 s (= 300 bleed), Mechanic 15. Visual 750 from Rake 1822.',
    raw_overrides={**_cmd_raw(750), 'RangeIndex': 2, 'SpellIconID': 494,
                   'AuraDescription_Lang_enUS': 'Bleeding for $s2 damage every $t2 sec.',
                   'Description_Lang_enUS': 'Rake the target for {pot1} Physical damage and an additional {pot2.total} '
                                            'Physical damage over $d.'},
)

pounce_command_201723 = spell(
    id=201723,
    name='Pounce',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[_direct(800.0)],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: Cat II, 800 Physical, melee, no stun. Visual 3942 from Pounce 9005.',
    raw_overrides={**_cmd_raw(3942), 'RangeIndex': 2,
                   'Description_Lang_enUS': 'Pounce on the target, causing {pot1} Physical damage.'},
)

savage_rend_command_201724 = spell(
    id=201724,
    name='Savage Rend',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[_direct(450.0)],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: Raptor I, 450 Physical, melee. Visual 372 from Savage Rend 50498.',
    raw_overrides={**_cmd_raw(372), 'RangeIndex': 2,
                   'Description_Lang_enUS': 'Savagely rend the target, causing {pot1} Physical damage.'},
)

_LEAPING_TEAR_CHAIN_AMP = 0.5   # second target's share of the hit; the tooltip reads it (BM-C7)

leaping_tear_command_201725 = spell(
    id=201725,
    name='Leaping Tear',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[_direct(900.0, chain_targets=2)],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: Raptor II, 900 Physical melee, chain_targets 2 with EffectChainAmplitude_1 0.5 (the second target takes 50%). Visual 11039 from Feral Charge - Cat 49376.',
    raw_overrides={**_cmd_raw(11039), 'RangeIndex': 2, 'EffectChainAmplitude_1': _LEAPING_TEAR_CHAIN_AMP,
                   'Description_Lang_enUS': 'Tear into the target and one nearby enemy, causing {pot1} Physical damage. '
                                            'The second enemy takes ' + str(round(_LEAPING_TEAR_CHAIN_AMP * 100))
                                            + '% damage.'},
)

swipe_command_201726 = spell(
    id=201726,
    name='Swipe',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        _direct(600.0),
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=600.0, potency_kind='direct',
               implicit_target_a=53, implicit_target_b=16, radius_yards=8.0),
    ],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: Bear I. eff0 600 on the target (TargetA 6); eff1 to enemies within 8 yd of the target (A 53 / B 16), the primary removed by spell_hun_command_splash. DEVIATION: BM 4.5 says eff1 300 (50%), but the DSL/engine allows ONE direct AP coefficient per spell (D6, spell_bonus_data.ap_bonus), so eff1 carries 600 too; the 50% extra-target rule needs a script halving (SetHitDamage on EFFECT_1) or a split spell. Ruling: eff1 stays 600 and spell_hun_swipe_command_splash (2nd binding) scales EFFECT_1 damage by SWIPE_SPLASH_PCT (50). Visual 189 from Swipe 779.',
    raw_overrides={**_cmd_raw(189), 'RangeIndex': 2,
                   'Description_Lang_enUS': 'Swipe the target and all enemies within $a2 yards, causing {pot1} Physical '
                                            'damage. Enemies other than the target take ' + str(SWIPE_SPLASH_PCT['value'])
                                            + '% damage.'},
)

maul_command_201727 = spell(
    id=201727,
    name='Maul',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[_direct(1000.0)],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: Bear II, 1000 Physical, melee. Visual 166 from Maul 6807.',
    raw_overrides={**_cmd_raw(166), 'RangeIndex': 2,
                   'Description_Lang_enUS': 'Maul the target, causing {pot1} Physical damage.'},
)

venom_bite_command_201728 = spell(
    id=201728,
    name='Venom Bite',
    school=School.NATURE,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=6000,
    effects=[
        _direct(600.0),
        _dot(75.0, 2000, implicit_target_a=6),
    ],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: Spider I, Nature. eff0 600 direct, eff1 PERIODIC_DAMAGE 75/tick (rate), amplitude 2000, 6 s (= 300). Dispel 0. Melee range and DmgClass MELEE. Visual 7910 from Poison Spit 35387.',
    raw_overrides={**_cmd_raw(7910), 'RangeIndex': 2, 'SpellIconID': 68,
                   'AuraDescription_Lang_enUS': 'Nature damage inflicted every $t2 sec.',
                   'Description_Lang_enUS': 'Bite the target for {pot1} Nature damage and poison it for an additional '
                                            '{pot2.total} Nature damage over $d.'},
)

# Venomous Cloud's per-tick rates: the splash 201736 carries half the primary (PET 4.9's flat AoE rule); the tooltip
# reads the ratio from these two numbers.
_VENOMOUS_CLOUD_RATE = 337.5
_VENOMOUS_CLOUD_SPLASH_RATE = 168.75
_VENOMOUS_CLOUD_SPLASH_PCT = round(100 * _VENOMOUS_CLOUD_SPLASH_RATE / _VENOMOUS_CLOUD_RATE)

venomous_cloud_command_201729 = spell(
    id=201729,
    name='Venomous Cloud',
    school=School.NATURE,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=8000,
    effects=[
        _dot(_VENOMOUS_CLOUD_RATE, 2000, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, trigger_spell=201736, implicit_target_a=6),
    ],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: Spider II, Nature, 30 yd, DmgClass RANGED (d1 b28 inverted lint). eff0 PERIODIC_DAMAGE 337.5/tick, amplitude 2000, 8 s (= 1800); eff1 TRIGGER_SPELL -> 201736 with TargetA 6 so the splash receives the primary as its explicit target (0-verify 8b). Visual 10409 from Spore Cloud 50274.',
    raw_overrides={**_cmd_raw(10409, dmg_class=3, prevention=1), 'SpellIconID': 2681,
                   'AuraDescription_Lang_enUS': 'Nature damage inflicted every $t1 sec.',
                   'Description_Lang_enUS': 'Spit a cloud of venom at the target, poisoning it and all enemies within $201736a1 '
                                            'yards for {pot1.total} Nature damage over $d. Enemies other than the target take '
                                            + str(_VENOMOUS_CLOUD_SPLASH_PCT) + '% damage.'},
)

savage_strikes_command_201730 = spell(
    id=201730,
    name='Savage Strikes',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[_direct(400.0)],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: Ferocity default I, 400 Physical, melee. Visual 6762 from Claw 16827.',
    raw_overrides={**_cmd_raw(6762), 'RangeIndex': 2,
                   'Description_Lang_enUS': 'Strike the target savagely, causing {pot1} Physical damage.'},
)

savage_pounce_command_201731 = spell(
    id=201731,
    name='Savage Pounce',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[_direct(1000.0)],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: Ferocity default II, 1000 Physical, melee. Visual 3942 from Pounce 9005.',
    raw_overrides={**_cmd_raw(3942), 'RangeIndex': 2,
                   'Description_Lang_enUS': 'Pounce on the target, causing {pot1} Physical damage.'},
)

thrash_command_201732 = spell(
    id=201732,
    name='Thrash',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[_direct(600.0)],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: Tenacity default I, 600 Physical, melee. Visual 189 from Swipe 779.',
    raw_overrides={**_cmd_raw(189), 'RangeIndex': 2,
                   'Description_Lang_enUS': 'Claw the enemy, causing {pot1} Physical damage.'},
)

crushing_blow_command_201733 = spell(
    id=201733,
    name='Crushing Blow',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[_direct(1000.0)],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: Tenacity default II, 1000 Physical, melee. Visual 166 from Maul 6807.',
    raw_overrides={**_cmd_raw(166), 'RangeIndex': 2,
                   'Description_Lang_enUS': 'Maul the target, causing {pot1} Physical damage.'},
)

feint_strike_command_201734 = spell(
    id=201734,
    name='Feint Strike',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[_direct(900.0)],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: Cunning default I, 900 Physical, 30 yd, DmgClass RANGED. Visual 398 from Snatch 50541.',
    raw_overrides={**_cmd_raw(398, dmg_class=3, prevention=1),
                   'Description_Lang_enUS': 'Strike the target from range, causing {pot1} Physical damage.'},
)

ambush_command_201735 = spell(
    id=201735,
    name='Ambush',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[_direct(1800.0)],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: Cunning default II, 1800 Physical, 30 yd, DmgClass RANGED. Visual 398 from Snatch 50541.',
    raw_overrides={**_cmd_raw(398, dmg_class=3, prevention=1),
                   'Description_Lang_enUS': 'Ambush the target, causing {pot1} Physical damage.'},
)

venomous_cloud_splash_201736 = spell(
    id=201736,
    name='Venomous Cloud (Splash)',
    school=School.NATURE,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=8000,
    effects=[
        _dot(_VENOMOUS_CLOUD_SPLASH_RATE, 2000, implicit_target_a=53, implicit_target_b=16, radius_yards=8.0),
    ],
    pet_owner_scaling=_PET_SCALING,
    notes='S1a A2 / BM 4.5: triggered by 201729 eff1. Nature, PERIODIC_DAMAGE 168.75/tick (rate), amplitude 2000, 8 s (= 900), A 53 / B 16 radius 8, the primary removed by spell_hun_command_splash. 50000 yd (triggered), DmgClass RANGED. Visual 10409 from Spore Cloud 50274.',
    raw_overrides={**_cmd_raw(10409, dmg_class=3, prevention=1), 'SpellIconID': 2681,
                   'AuraDescription_Lang_enUS': 'Nature damage inflicted every $t1 sec.'},
)


# ---- script bindings, links, groups, custom attrs (BM 5.2). Positive keys only (L7) ----
scripted_by(command_i_201800, 'spell_hun_command')
scripted_by(command_ii_201801, 'spell_hun_command')
scripted_by(swipe_command_201726, 'spell_hun_command_splash')
scripted_by(swipe_command_201726, 'spell_hun_swipe_command_splash')   # second class: eff1 SetHitDamage(SWIPE_SPLASH_PCT %)
scripted_by(venomous_cloud_splash_201736, 'spell_hun_command_splash')
scripted_by(34026, 'spell_hun_kill_command_bm')              # PET keeps spell_hun_kill_command_rework
scripted_by(beast_cleave_buff_201806, 'spell_hun_beast_cleave')
scripted_by(19574, 'spell_hun_bestial_wrath_bm')             # stock spell_hun_bestial_wrath stays
scripted_by(beast_within_mastery_201812, 'spell_hun_tbw_mastery')
unbind_script(-53256, 'spell_hun_cobra_strikes')             # exact live key; the new bind is S1b

linked_spell(201820, 201813, 2)    # Pathfinding r3 -> capstone
linked_spell(201851, 201811, 2)    # Cobra Shot r3 -> transform
linked_spell(201857, 201812, 2)    # The Beast Within r3 -> Mastery passive
linked_spell(56316, 53270, 2)      # Kindred Spirits r3 -> exotic tame + 4 pet points (stock Beast Mastery 53270)

spell_group(1231, cobra_shot_transform_201811)
spell_group_rule(1231, stack_rule=1, description='Hunter Steady Shot transforms (exclusive)')

# One row per spell (custom_attr is keyed on the spell id), so every bit of a spell goes into its one call.
# 0x8000 SPELL_ATTR0_CU_IGNORE_ARMOR (0.5); 0x200000 SPELL_ATTR0_CU_NO_POSITIVE_TAKEN_BONUS (S1a-3: the copy's BP is the
# final, post-taken damage, so the victim's damage-taken increases must not apply a second time).
custom_attr(beast_cleave_strike_201807, attributes=0x208000)
custom_attr(spiked_collar_strike_201805, attributes=0x208000)
custom_attr(phoenix_s_plume_lockout_201810, attributes=0x1000)  # SPELL_ATTR0_CU_NEGATIVE_EFF0


# ---- S1b ----
# Variable stems frozen by 0-dsl (HunterData::SPELL_STAMPEDE_SUMMON / SPELL_STEADY_SHOT_NATURE / SPELL_BM_PET_PROCS).
# SPELL_STAMPEDE is the stock rhino 57386: never use it for 201802.

# Stampede 201802 (BM 4.4, S1b B6, T29): talent (10,1) button, SLA 30543. No family bit (SpellClassSet 0: no hunter
# SpellMod or stock Readiness reaches it, Q16), no IS_ABILITY (a bit-less IS_ABILITY button is a gcd_haste error; its
# GCD is core-hasted, X16), AttributesEx 0. eff0 SUMMON at the target; spell_hun_stampede prevents it and summons
# STAMPEDE_BEAST_COUNT beasts itself (misc 300205 is the Ferocity default, MiscValueB 1021 the guardian properties).
stampede_summon_201802 = spell(
    id=201802,
    name='Stampede',
    school=School.NORMAL,
    attributes=0x50000,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=0, implicit_target_a=53, misc_value=300205),
    ],
    spell_icon_id=3519,
    notes='S1b B6 / BM 4.4: Stampede. eff0 SUMMON (28) TargetA 53 (DEST_TARGET_ENEMY), misc 300205, MiscValueB 1021, 15 s; spell_hun_stampede (OnEffectHit EFFECT_0 SUMMON, PreventHitDefaultEffect) summons the family beast 300200-300207. 120 s (Cooldown Haste eligible by rule), 40 yd, 0 mana, GCD 1500/133, DefenseType 0, no family bit, no IS_ABILITY, AttributesEx 0. T29 text (no Capstone label).',
    raw_overrides={
        'EquippedItemClass': -1, 'SpellLevel': 60, 'DefenseType': 0, 'SpellClassSet': 0, 'AttributesEx': 0,
        'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'EffectMiscValueB_1': 1021,
        'Description_Lang_enUS': 'Summons ' + str(STAMPEDE_BEAST_COUNT['value']) + " beasts of your pet's family to "
                                 'attack your target for $d. The beasts benefit from every effect that increases '
                                 "your pet's damage.",
    },
)

# Steady Shot (Nature) 201803 (BM 4.2, S1b B1): one per Steady Shot hit, BP from spell_hun_steady_shot_nature.
steady_shot_nature_201803 = spell(
    id=201803,
    name='Steady Shot',
    school=School.NATURE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=6,
               potency_excluded='percent of the Steady Shot hit (CORE-AUDIT C40); BP from spell_hun_steady_shot_nature'),
    ],
    spell_icon_id=2225,
    notes='S1b B1 / BM 4.2: hunter-cast triggered Nature hit, BP = (Serpent\'s Swiftness + Cobra Shot) % of the Steady Shot hit\'s pre-armor damage (script). Family 0, CANT_CRIT, IGNORE_CASTER_MODIFIERS | SUPPRESS_CASTER_PROCS | ALWAYS_HIT, 50000 yd, TargetA 6. No custom attr: the target-side damage-taken debuffs (Curse of the Elements, ...) must still apply to the Nature hit (BM 4.2; S1b R-data M2 reversed brief #3).',
    raw_overrides={
        'EquippedItemClass': -1, 'SpellLevel': 45, 'DefenseType': 0, 'SpellClassSet': 0,
        'AttributesEx2': 0x20000000,                       # CANT_CRIT
        'AttributesEx3': 0x20000000 | 0x10000 | 0x40000,   # IGNORE_CASTER_MODIFIERS | SUPPRESS_CASTER_PROCS | ALWAYS_HIT
        'Description_Lang_enUS': 'Deals Nature damage.',
    },
)

# Hunter Pet Talent Procs 201809 (BM 4.9, S1b B4): hidden passive DUMMY the hunter adds to the real pet
# (Hunter::ApplyBmPetAuras, owner as caster, L5). Culling the Herd + Improved Aspect of the Viper capstone carrier.
bm_pet_procs_201809 = spell(
    id=201809,
    name='Hunter Pet Talent Procs',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    notes='S1b B4 / BM 4.9: hidden passive (464) on the pet, eff0 DUMMY target 1, ProcTypeMask 0x10110, ProcChance 100. procs_on: d2 b22 | b23 (commanded spells + basic attacks, no d1 b28), HIT phase, crits only, attributes_mask 0x2 (TRIGGERED_CAN_PROC, L8: the commands are TRIGGERED_FULL_MASK casts). spell_hun_bm_pet_procs.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 0, 'ProcTypeMask': 0x10110, 'ProcChance': 100},
)


# ---- PT-5: Command display passives 201858-201873 (S1b brief decision 1) ----
# One per commanded spell: display id = commanded id + COMMAND_DISPLAY_OFFSET. Passive (0x150: PASSIVE, no
# DO_NOT_DISPLAY 0x80, so the pet spellbook shows it), never castable, no script, no family bit, never in a tree, no
# trainer. eff0 DUMMY on the pet itself. Hunter::SeatDefaultPetBar learns the current kit's two (ACT_PASSIVE) and
# removes the other 14. The tooltip quotes the commanded spell through pot_text() and $<id> tokens.

def _display(commanded, slot, icon, text):
    press = command_i_201800 if slot == 'I' else command_ii_201801
    text += f' {press.cooldown_ms // 1000} sec cooldown.'
    return spell(
        id=commanded.id + COMMAND_DISPLAY_OFFSET['value'],
        name=f'Command {slot}: {commanded.name}',
        school=commanded.school,
        attributes=0x150,
        cast_time_ms=0,
        cooldown_ms=0,
        category_cooldown_ms=0,
        mana_cost=0,
        mana_cost_pct=0,
        range_yards=RANGE_SELF,
        duration_ms=-1,
        effects=[
            Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        ],
        spell_icon_id=icon,
        notes=f'S1b PT-5: pet-spellbook display of Command {slot} -> {commanded.name} {commanded.id}. Passive DUMMY, '
              f'no script, never castable; seated and swapped by Hunter::SeatDefaultPetBar.',
        raw_overrides={
            'EquippedItemClass': -1, 'SpellClassSet': 0, 'NameSubtext_Lang_enUS': '',
            'Description_Lang_enUS': text,
        },
    )


_SPLASH_TAIL = '% damage.'

lunge_display_201858 = _display(
    lunge_command_201720, 'I', 1559,     # pet Charge 61685 (Lunge has no icon)
    'Leap to the target and strike it for ' + pot_text(lunge_command_201720, effect=2) + ' Physical damage.',
)
rip_throat_display_201859 = _display(
    rip_throat_command_201721, 'II', 1531,   # Ravage 6785
    "Tear at the target's throat, causing " + pot_text(rip_throat_command_201721) + ' Physical damage.',
)
rake_display_201860 = _display(
    rake_command_201722, 'I', 494,
    'Rake the target for ' + pot_text(rake_command_201722) + ' Physical damage and an additional '
    + pot_text(rake_command_201722, effect=2, variant='total') + ' Physical damage over $201722d.',
)
pounce_display_201861 = _display(
    pounce_command_201723, 'II', 495,    # Pounce 9005
    'Pounce on the target, causing ' + pot_text(pounce_command_201723) + ' Physical damage.',
)
savage_rend_display_201862 = _display(
    savage_rend_command_201724, 'I', 245,    # Savage Rend 50498
    'Savagely rend the target, causing ' + pot_text(savage_rend_command_201724) + ' Physical damage.',
)
leaping_tear_display_201863 = _display(
    leaping_tear_command_201725, 'II', 3930,     # Feral Charge - Cat 49376
    'Tear into the target and one nearby enemy, causing ' + pot_text(leaping_tear_command_201725)
    + ' Physical damage. The second enemy takes ' + str(round(_LEAPING_TEAR_CHAIN_AMP * 100)) + _SPLASH_TAIL,
)
swipe_display_201864 = _display(
    swipe_command_201726, 'I', 1562,     # Swipe (Bear) 779
    'Swipe the target and all enemies within $201726a2 yards, causing ' + pot_text(swipe_command_201726)
    + ' Physical damage. Enemies other than the target take ' + str(SWIPE_SPLASH_PCT['value']) + _SPLASH_TAIL,
)
maul_display_201865 = _display(
    maul_command_201727, 'II', 261,      # Maul 6807
    'Maul the target, causing ' + pot_text(maul_command_201727) + ' Physical damage.',
)
venom_bite_display_201866 = _display(
    venom_bite_command_201728, 'I', 68,
    'Bite the target for ' + pot_text(venom_bite_command_201728) + ' Nature damage and poison it for an additional '
    + pot_text(venom_bite_command_201728, effect=2, variant='total') + ' Nature damage over $201728d.',
)
venomous_cloud_display_201867 = _display(
    venomous_cloud_command_201729, 'II', 2681,
    'Spit a cloud of venom at the target, poisoning it and all enemies within $201736a1 yards for '
    + pot_text(venomous_cloud_command_201729, variant='total') + ' Nature damage over $201729d. Enemies other than '
    'the target take ' + str(_VENOMOUS_CLOUD_SPLASH_PCT) + _SPLASH_TAIL,
)
savage_strikes_display_201868 = _display(
    savage_strikes_command_201730, 'I', 262,     # Claw 16827
    'Strike the target savagely, causing ' + pot_text(savage_strikes_command_201730) + ' Physical damage.',
)
savage_pounce_display_201869 = _display(
    savage_pounce_command_201731, 'II', 495,     # Pounce 9005
    'Pounce on the target, causing ' + pot_text(savage_pounce_command_201731) + ' Physical damage.',
)
thrash_display_201870 = _display(
    thrash_command_201732, 'I', 1562,    # Swipe (Bear) 779
    'Claw the enemy, causing ' + pot_text(thrash_command_201732) + ' Physical damage.',
)
crushing_blow_display_201871 = _display(
    crushing_blow_command_201733, 'II', 261,     # Maul 6807
    'Maul the target, causing ' + pot_text(crushing_blow_command_201733) + ' Physical damage.',
)
feint_strike_display_201872 = _display(
    feint_strike_command_201734, 'I', 168,   # Snatch 50541
    'Strike the target from range, causing ' + pot_text(feint_strike_command_201734) + ' Physical damage.',
)
ambush_display_201873 = _display(
    ambush_command_201735, 'II', 168,    # Snatch 50541
    'Ambush the target, causing ' + pot_text(ambush_command_201735) + ' Physical damage.',
)


# ---- Stampede guardians 300200-300207 (BM 4.6, S1b B6) ----
# Warlock _GUARDIAN_COMMON shape with type 1 (beast). Inside PET's STAMPEDE_ENTRY_MIN/MAX (300200-300219), which
# GetPassthroughKind reads. `family` drives the per-type swing and white scale (PET's OnInitStatsForLevel). Level,
# faction and react state come from the summon (Guardian::InitStats, the AI). Three models each, probability 1.0.
_STAMPEDE_GUARDIAN_COMMON = dict(
    faction=35, unit_class=1, unit_flags=33554434, type=1, flags_extra=66,
    DamageModifier=1, BaseAttackTime=2000, RegenHealth=0, detection_range=0,
    minlevel=1, maxlevel=1, ScriptName='npc_hun_stampede_beast',
)


# DisplayScale per display for models whose native scale is far from 1.0 (4734 FelBat 0.15, 8808 0.30); others 1.0.
_STAMPEDE_DISPLAY_SCALE = {4734: 3.0, 8808: 1.5}


def _stampede_beast(entry, name, family, displays):
    row = creature_template(entry, name, family=family, **_STAMPEDE_GUARDIAN_COMMON)
    for idx, display_id in enumerate(displays):
        creature_model(entry, display_id=display_id, idx=idx, probability=1.0,
                       scale=_STAMPEDE_DISPLAY_SCALE.get(display_id, 1.0))
    return row


stampeding_wolf_300200 = _stampede_beast(300200, 'Stampeding Wolf', 1, (1100, 165, 741))
stampeding_cat_300201 = _stampede_beast(300201, 'Stampeding Cat', 2, (1056, 1059, 1973))
stampeding_raptor_300202 = _stampede_beast(300202, 'Stampeding Raptor', 11, (1747, 180, 4442))
stampeding_bear_300203 = _stampede_beast(300203, 'Stampeding Bear', 4, (1006, 3201, 820))
stampeding_spider_300204 = _stampede_beast(300204, 'Stampeding Spider', 3, (1103, 1989, 6808))
stampeding_beast_ferocity_300205 = _stampede_beast(300205, 'Stampeding Beast', 25, (1536, 2710, 2609))   # Hyena
stampeding_beast_tenacity_300206 = _stampede_beast(300206, 'Stampeding Beast', 5, (193, 381, 607))       # Boar
stampeding_beast_cunning_300207 = _stampede_beast(300207, 'Stampeding Beast', 24, (8808, 4734, 14562))   # Bat


# ---- S1b proc rows (BM 7.1, S1b B1 / B4). Positive keys only (L7); chance 0 = the DBC ProcChance (CR4) ----
# Steady Shot's Nature hit (spell_hun_steady_shot_nature, Serpent's Swiftness only): one row per rank (harness ruling: replaces BM 7.1's single
# -34466 row, so only Serpent's Swiftness rank 3 sees the CAST phase, for its Kill Command cut). Steady Shot d2 b29 only.
_STEADY_SHOT_NATURE_RANKS = (
    (34466, 0x2), (34467, 0x2), (34468, 0x3),       # Serpent's Swiftness r1-r3 (r3: CAST for the KC cut + HIT)
)
for _rank, _phase in _STEADY_SHOT_NATURE_RANKS:
    procs_on(_rank, proc_flags=0x100, family_name=9, family_mask=m.STEADY_SHOT_MASK, spell_phase_mask=_phase,
             hit_mask=0, chance=0.0)

# Culling the Herd + Improved Viper capstone carrier: pet basic attacks (d2 b23) and commanded spells (d2 b22), HIT,
# crits only, TRIGGERED_CAN_PROC so the TRIGGERED_FULL_MASK commands reach it (L8).
procs_on(bm_pet_procs_201809, proc_flags=0x10110, family_name=9, family_mask=m.BM_PET_PROC_MASK,
         spell_phase_mask=0x2, hit_mask=0x2, attributes_mask=0x2, chance=0.0)


# ---- S1b script bindings (S1b brief class table). Positive keys only (L7) ----
for _rank, _phase in _STEADY_SHOT_NATURE_RANKS:
    scripted_by(_rank, 'spell_hun_steady_shot_nature')
for _rank in (53256, 53259, 53260):                      # Cobra Strikes r1-r3 (the -53256 unbind above stays)
    scripted_by(_rank, 'spell_hun_cobra_strikes_bm')
scripted_by(3044, 'spell_hun_arcane_shot_bm')            # Stomp trigger; SHARED keeps spell_hun_shot_mana on 3044
scripted_by(bm_pet_procs_201809, 'spell_hun_bm_pet_procs')
scripted_by(stampede_summon_201802, 'spell_hun_stampede')
