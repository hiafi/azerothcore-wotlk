"""
Hunter - pet spells (H0-P1 owns the pulled stock rows and the first new pet-spell rows; later stages append).

Sources: .agents/plans/hunter-rework/hunter-rework.PET.md 2.1 (id table), 4 (kit and commands), 5.3 (stat
inheritance), 7 (pet tree).

Ids P1 uses: 201710, 201711, 201715-201718, 201750, 201751; pulled stock rows 61689, 61690, 53203-53205,
53175, 53176, 53450, 53451, 53186, 53187, 54131; SkillLineAbility 30560-30605.
Reserved ids: 201700-201709 (H0-P2), 201720-201749 (S1, built in hunter_bm_spells.py), 201753.

PET.md 4.9 command stems (S1 builds these; every commanded spell gets a `_command_` stem, never a short
stem a retired special owns):

| Id | DSL stem |
|---|---|
| 201720 | `lunge_command_201720` |
| 201721 | `rip_throat_command_201721` |
| 201722 | `rake_command_201722` |
| 201723 | `pounce_command_201723` |
| 201724 | `savage_rend_command_201724` |
| 201725 | `leaping_tear_command_201725` |
| 201726 | `swipe_command_201726` |
| 201727 | `maul_command_201727` |
| 201728 | `venom_bite_command_201728` |
| 201729 | `venomous_cloud_command_201729` |
| 201736 | `venomous_cloud_splash_201736` |
| 201730 | `savage_strikes_command_201730` |
| 201731 | `savage_pounce_command_201731` |
| 201732 | `thrash_command_201732` |
| 201733 | `crushing_blow_command_201733` |
| 201734 | `feint_strike_command_201734` |
| 201735 | `ambush_command_201735` |
| 201737 | `lunge_leap_command_201737` |

Import rule: this file imports no sibling spell module; stock rows are named by bare id. It imports only the
`_masks` constants module and the `_pet_kits` helpers (hunter-pet-families F0).
"""

from lib.dsl import AuraType, Effect, EffectType, PowerType, School
from lib.dsl.registry import const, custom_attr, retire_pet_spell, scripted_by, skill_line_ability, spell, spell_group, unbind_script
from . import _masks as m
from . import _pet_kits as kits


# ---- constants (PET.md 5.3; the C++ header names are the strings) ----
PET_AP_FROM_RAP_PCT = const('PET_AP_FROM_RAP_PCT', 100, 'Pet attack power per owner ranged attack power, percent (PET 5.3).')
PET_AP_FROM_SP_PCT = const('PET_AP_FROM_SP_PCT', 100, 'Pet attack power per owner spell power, percent (PET 5.3).')
PET_STAMINA_PCT = const('PET_STAMINA_PCT', 45, 'Pet stamina inherited from owner stamina, percent (PET 5.3).')
PET_TENACITY_STAMINA_BONUS_PCT = const('PET_TENACITY_STAMINA_BONUS_PCT', 20, 'Extra stamina percent for Tenacity pets (PET 5.3).')
PET_VERSATILITY_SHARE_PCT = const('PET_VERSATILITY_SHARE_PCT', 100, 'Share of owner versatility the pet inherits, percent (PET 5.3).')
PET_CRIT_SHARE_PCT = const('PET_CRIT_SHARE_PCT', 100, 'Share of owner crit the pet inherits, percent (PET 5.3).')
PET_HASTE_SHARE_PCT = const('PET_HASTE_SHARE_PCT', 100, 'Share of owner haste the pet inherits, percent (PET 5.3).')
PET_WHITE_SCALE_PCT = const('PET_WHITE_SCALE_PCT', 25, 'Pet white-damage scale, percent (PET 5.3).')
PET_SWING_MS_FEROCITY = const('PET_SWING_MS_FEROCITY', 1500, 'Ferocity pet swing timer, ms (PET 5.3).')
PET_SWING_MS_TENACITY = const('PET_SWING_MS_TENACITY', 2500, 'Tenacity pet swing timer, ms (PET 5.3).')
PET_SWING_MS_CUNNING = const('PET_SWING_MS_CUNNING', 2000, 'Cunning pet swing timer, ms (PET 5.3).')
STAMPEDE_ENTRY_MIN = const('STAMPEDE_ENTRY_MIN', 300200, 'First creature_template entry of the Stampede pet block (PET X6).')
STAMPEDE_ENTRY_MAX = const('STAMPEDE_ENTRY_MAX', 300219, 'Last creature_template entry of the Stampede pet block (PET X6).')


natural_armor_61689 = spell(
    id=61689,
    name='Natural Armor',
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_RESISTANCE_PCT, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=133),
    ],
    spell_icon_id=198,
    notes='pulled from existing data. H0-P1 (PET.md 7.1): armor bp 9 (10%), new eff1 aura 133 MOD_INCREASE_HEALTH_PERCENT bp 2 (+3% max health)',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's armor by $s1% and its maximum health by $s2%.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


natural_armor_61690 = spell(
    id=61690,
    name='Natural Armor',
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.MOD_RESISTANCE_PCT, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=133),
    ],
    spell_icon_id=198,
    notes='pulled from existing data. H0-P1 (PET.md 7.1): armor bp 19 (20%), new eff1 aura 133 MOD_INCREASE_HEALTH_PERCENT bp 5 (+6% max health)',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's armor by $s1% and its maximum health by $s2%.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


spider_s_bite_53203 = spell(
    id=53203,
    name="Spider's Bite",
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=1586,
    notes='pulled from existing data. H0-P1 (PET.md 7.1): aura 52 MOD_WEAPON_CRIT_PERCENT -> 290 MOD_CRIT_PCT (misc 127 dropped, the handler ignores it), values kept',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 2, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's critical strike chance by $s1%.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 17, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


spider_s_bite_53204 = spell(
    id=53204,
    name="Spider's Bite",
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=1586,
    notes='pulled from existing data. H0-P1 (PET.md 7.1): aura 52 MOD_WEAPON_CRIT_PERCENT -> 290 MOD_CRIT_PCT (misc 127 dropped, the handler ignores it), values kept',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 2, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's critical strike chance by $s1%.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 17, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


spider_s_bite_53205 = spell(
    id=53205,
    name="Spider's Bite",
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=1586,
    notes='pulled from existing data. H0-P1 (PET.md 7.1): aura 52 MOD_WEAPON_CRIT_PERCENT -> 290 MOD_CRIT_PCT (misc 127 dropped, the handler ignores it), values kept',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 2, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's critical strike chance by $s1%.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 17, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


pet_barding_53175 = spell(
    id=53175,
    name='Pet Barding',
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.MOD_RESISTANCE_PCT, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_DODGE_PERCENT),
    ],
    spell_icon_id=2927,
    notes='pulled from existing data. H0-P1 (PET.md 7.1): dodge bp 0 -> 1 (2%)',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's armor by $s1% and its chance to dodge by $s2%.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


pet_barding_53176 = spell(
    id=53176,
    name='Pet Barding',
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_RESISTANCE_PCT, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_DODGE_PERCENT),
    ],
    spell_icon_id=2927,
    notes='pulled from existing data. H0-P1 (PET.md 7.1): dodge bp 1 -> 3 (4%)',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's armor by $s1% and its chance to dodge by $s2%.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


grace_of_the_mantis_53450 = spell(
    id=53450,
    name='Grace of the Mantis',
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACKER_SPELL_AND_WEAPON_CRIT_CHANCE),
    ],
    spell_icon_id=1791,
    notes='pulled from existing data. H0-P1 (PET.md 7.1): aura 187 -> 197 MOD_ATTACKER_SPELL_AND_WEAPON_CRIT_CHANCE, bp -3 -> -4',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectDieSides_2': 1, 'EffectBasePoints_2': -1, 'ImplicitTargetA_2': 1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the chance your pet will be critically hit by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


grace_of_the_mantis_53451 = spell(
    id=53451,
    name='Grace of the Mantis',
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACKER_SPELL_AND_WEAPON_CRIT_CHANCE),
    ],
    spell_icon_id=1791,
    notes='pulled from existing data. H0-P1 (PET.md 7.1): aura 187 -> 197 MOD_ATTACKER_SPELL_AND_WEAPON_CRIT_CHANCE, bp -5 -> -7',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectDieSides_2': 1, 'EffectBasePoints_2': -1, 'ImplicitTargetA_2': 1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the chance your pet will be critically hit by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


bloodthirsty_53186 = spell(
    id=53186,
    name='Bloodthirsty',
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=54131),
        Effect(type=EffectType.DUMMY, base_points=9, implicit_target_a=1),
    ],
    spell_icon_id=2253,
    notes='pulled from existing data. H0-P1 (PET.md 7.1): ProcChance 100 (spell_hun_pet_bloodthirsty rolls the real chance from EFFECT_1 = DUMMY bp 9, shown 10%); eff0 mask and SpellClassSet 17 cleared',
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 69972, 'ProcChance': 100, 'DurationIndex': 0, 'RangeIndex': 2, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your pet's attacks have a $s2% chance to heal it for 5% of its total health.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


bloodthirsty_53187 = spell(
    id=53187,
    name='Bloodthirsty',
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=2, trigger_spell=54131),
        Effect(type=EffectType.DUMMY, base_points=19, implicit_target_a=1),
    ],
    spell_icon_id=2253,
    notes='pulled from existing data. H0-P1 (PET.md 7.1): ProcChance 100 (spell_hun_pet_bloodthirsty rolls the real chance from EFFECT_1 = DUMMY bp 19, shown 20%); eff0 mask and SpellClassSet 17 cleared',
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 69972, 'ProcChance': 100, 'DurationIndex': 0, 'RangeIndex': 2, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your pet's attacks have a $s2% chance to heal it for 5% of its total health.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


bloodthirsty_54131 = spell(
    id=54131,
    name='Bloodthirsty',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=5000,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=20, amplitude=1000),
    ],
    spell_icon_id=2253,
    notes='pulled from existing data. H0-P1 (PET.md 7.1): eff0 (happiness energize, aura 21) removed, eff1 OBS_MOD_HEALTH 1%/s x 5 s kept',
    raw_overrides={'AttributesEx': 1024, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 15374, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 3439, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': "Your pet's attacks have a chance to heal it for 5% of its total health.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Healing 1% of health per sec.', 'AuraDescription_Lang_Mask': 16712190, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


# ---- new spells (PET.md 2.1, 4.3, 4.4, 7.1). EquippedItemClass -1 on every row (L1). ----

_SPIT_RAW = {
    'AttributesEx': 512, 'BaseLevel': 1, 'SpellLevel': 1, 'DefenseType': 3, 'PreventionType': 1,
    'SpellClassSet': 9, 'SpellClassMask_2': m.PET_BASIC_ATTACKS_CARRIER[1], 'SpellClassMask_3': m.PET_BASIC_ATTACKS_CARRIER[2],
    'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'FacingCasterFlags': 1, 'InterruptFlags': 8,
    'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'ProcChance': 101,
}

venom_spit_201710 = spell(
    id=201710,
    name='Venom Spit',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=kits.basic_potency(33.0, 'Cunning'), potency_kind='direct',
               implicit_target_a=6),
    ],
    pet_owner_scaling=(PET_AP_FROM_RAP_PCT['value'], PET_AP_FROM_SP_PCT['value']),
    spell_icon_id=68,
    notes='H0-P1 (PET.md 4.3): Spider basic. Visual 7910 / Speed 40 and icon 68 from Poison Spit 35387, field shape from Acid Spit 55749 (direct hit). Ruling 23 (user 2026-11-13, hunter-pet-families): ap_potency 33.0 -> x0.39 (kits.basic_potency, Cunning damage scale). Ranged DmgClass 3 so it crits via GetUnitCriticalChance; d1 b28 + d2 b23 carrier; 0 Focus, 6 s cooldown, GCD 1500/133.',
    raw_overrides={**_SPIT_RAW, 'SpellVisualID_1': 7910, 'Speed': 40.0,
                   'Description_Lang_enUS': 'Spit venom at the enemy, causing {pot1} Nature damage.'},
)


cunning_spit_201711 = spell(
    id=201711,
    name='Spit',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=kits.basic_potency(33.0, 'Cunning'), potency_kind='direct',
               implicit_target_a=6),
    ],
    pet_owner_scaling=(PET_AP_FROM_RAP_PCT['value'], PET_AP_FROM_SP_PCT['value']),
    spell_icon_id=636,
    notes='H0-P1 (PET.md 4.3): Cunning placeholder basic. Visual 854 / Speed 24 and icon 636 from Acid Spit 55749; same numbers as Venom Spit 201710. Ruling 23 (user 2026-11-13, hunter-pet-families): ap_potency 33.0 -> x0.39 (kits.basic_potency, Cunning damage scale).',
    raw_overrides={**_SPIT_RAW, 'SpellVisualID_1': 854, 'Speed': 24.0,
                   'Description_Lang_enUS': 'Spit at an enemy, causing {pot1} Nature damage.'},
)


roar_of_courage_201715 = spell(
    id=201715,
    name='Roar of Courage',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=40000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=2.0714285714285716, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=0, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=2.0714285714285716, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=1, radius_yards=100.0),
    ],
    spell_icon_id=1573,
    notes='H0-P1 (PET.md 4.4): Cat utility. Effects copied from Strength of Earth 8076 (Str/Agi, bp 9, 2.0714/level, BaseLevel 10, MaxLevel 80), retargeted to CASTER_AREA_RAID 100 yd. Group 1088.',
    raw_overrides={'AttributesEx': 512, 'BaseLevel': 10, 'MaxLevel': 80, 'SpellLevel': 10, 'RangeIndex': 1, 'DefenseType': 2, 'PreventionType': 2,
                   'SpellClassSet': 9, 'SpellClassMask_2': m.PET_ABILITY | m.PET_UTILITY, 'EquippedItemClass': -1,
                   'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0,
                   'AuraDescription_Lang_enUS': 'Increases Strength and Agility by $s1.',
                   'Description_Lang_enUS': 'Your pet roars, increasing the Strength and Agility of all party and raid members by $s1. Does not stack with Strength of Earth Totem or Horn of Winter.'},
)


tear_armor_201716 = spell(
    id=201716,
    name='Tear Armor',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=6, apply_aura=AuraType.MOD_RESISTANCE_PCT, misc_value=1),
    ],
    spell_icon_id=565,
    notes='H0-P1 (PET.md 4.4): Raptor utility. -20% armor (Expose Armor 8647 value), 30 s, 5 yd. Group 1015.',
    raw_overrides={'AttributesEx': 512, 'SpellLevel': 1, 'BaseLevel': 1, 'DefenseType': 2, 'PreventionType': 2, 'FacingCasterFlags': 1,
                   'SpellClassSet': 9, 'SpellClassMask_2': m.PET_ABILITY | m.PET_UTILITY, 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0,
                   'AuraDescription_Lang_enUS': 'Armor decreased by ${$m1*-1}%.',
                   'Description_Lang_enUS': "Tears at the target's armor, reducing it by ${$m1*-1}% for $d. Does not stack with Sunder Armor, Expose Armor or Acid Spit."},
)


menacing_roar_201717 = spell(
    id=201717,
    name='Menacing Roar',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-36, points_per_level=-5.696969696969697, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_ATTACK_POWER, radius_yards=10.0),
    ],
    spell_icon_id=960,
    notes='H0-P1 (PET.md 4.4): Bear utility. Effect copied from Demoralizing Shout 1160 (bp -36, -5.697/level, BaseLevel 14, MaxLevel 80, TargetA 22 / TargetB 15, 10 yd). Group 1062.',
    raw_overrides={'AttributesEx': 512, 'BaseLevel': 14, 'MaxLevel': 80, 'SpellLevel': 14, 'RangeIndex': 1, 'DefenseType': 1, 'PreventionType': 1,
                   'AttributesEx6': 8388608, 'SpellClassSet': 9, 'SpellClassMask_2': m.PET_ABILITY | m.PET_UTILITY, 'EquippedItemClass': -1,
                   'EffectChainAmplitude_1': 1.0,
                   'AuraDescription_Lang_enUS': 'Reduces melee attack power by $s1.',
                   'Description_Lang_enUS': 'Your pet roars, reducing the attack power of all enemies within $a1 yards by $s1 for $d. Does not stack with Demoralizing Shout, Demoralizing Roar, Vindication or Curse of Weakness.'},
)


# Boar's Speed ranks 2 and 3 (PET.md 7.1): clones of the built 19596 row (hunter_trigger_spells.py), differing only in id and bp.
boar_s_speed_201750 = spell(
    id=201750,
    name="Boar's Speed",
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED, misc_value=8),
    ],
    spell_icon_id=1578,
    notes="H0-P1 (PET.md 7.1): talent rank 2 (+20%), clone of 19596 with bp 19.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's movement speed by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 268435456, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


boar_s_speed_201751 = spell(
    id=201751,
    name="Boar's Speed",
    school=School.NORMAL,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED, misc_value=8),
    ],
    spell_icon_id=1578,
    notes="H0-P1 (PET.md 7.1): talent rank 3 (+30%), clone of 19596 with bp 29.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's movement speed by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 268435456, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9},
)


web_pull_201718 = spell(
    id=201718,
    name='Web Pull',
    school=School.NORMAL,
    mechanic=6,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=6),
    ],
    spell_icon_id=272,
    notes='H0-P1 (PET.md 4.4): Spider utility. DUMMY on an enemy, 30 yd, 30 s, Mechanic GRIP (6); spell_hun_pet_web_pull makes the target cast Death Grip jump 57604 at the pet. Visual 684 and icon 272 from Web 4167.',
    raw_overrides={'AttributesEx': 512, 'SpellLevel': 1, 'BaseLevel': 1, 'DefenseType': 1, 'PreventionType': 1, 'FacingCasterFlags': 1,
                   'SpellVisualID_1': 684, 'SpellClassSet': 9, 'SpellClassMask_2': m.PET_ABILITY | m.PET_UTILITY, 'EquippedItemClass': -1,
                   'EffectChainAmplitude_1': 1.0,
                   'Description_Lang_enUS': 'Spin a web at the target, pulling it to your pet. Does not work on bosses. 30 sec cooldown.'},
)


# =====================================================================================================
# hunter-pet-families F0 (PLAN §3, §4.1, §5.3; F0.HANDOFF §5): the five finished kits under the new rules.
# Slot 3 for Wolf / Cat / Raptor / Bear (201983-201986), slot 2 for Spider (201753; Web Pull moves to its slot 3).
# Every slot 2 / 3 utility carries d1 b28 + b29 (kits.utility_raw). Unlock levels follow the class equivalents:
# Frenzied Regeneration 36 (druid), Prowl 20 (druid), Sticky Webbing 26 (Curse of Tongues); Lick Your Wounds shares
# Frenzied Regeneration's shape and level; Tail Sweep has no class equivalent (30).
# =====================================================================================================

LICK_YOUR_WOUNDS_LEVEL = 36
PROWL_LEVEL = 20
TAIL_SWEEP_LEVEL = 30
FRENZIED_REGENERATION_LEVEL = 36
STICKY_WEBBING_LEVEL = 26

# Aura types the DSL enum doesn't name (SpellAuraDefines.h).
_AURA_MOD_STEALTH = 16
_AURA_OBS_MOD_HEALTH = 20            # percent of max health per tick (FE 9g)
_AURA_HASTE_SPELLS = 216             # casting time (Curse of Tongues, Mind-numbing Poison)

lick_your_wounds_201983 = spell(
    id=201983,
    name='Lick Your Wounds',
    school=School.NORMAL,
    attributes=kits.UTILITY_ATTRIBUTES,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=kits.UTILITY_POWER_TYPE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=_AURA_OBS_MOD_HEALTH,
               amplitude=1000),
    ],
    spell_icon_id=267,
    notes='hunter-pet-families F0: Wolf slot 3. Aura 20 OBS_MOD_HEALTH 6% of max health per 1 s for 5 s (30%), on the '
          'pet, not channeled (stock 53426 channels), manual, 1 min. Visual 12983 / icon 267 from Lick Your Wounds 53426.',
    raw_overrides=kits.utility_raw(
        LICK_YOUR_WOUNDS_LEVEL, RangeIndex=1, DefenseType=0, PreventionType=2, SpellVisualID_1=12983,
        AuraDescription_Lang_enUS='Regaining health.',
        Description_Lang_enUS='Your pet licks its wounds, healing itself for $o1% of its maximum health over $d.'),
)

# Prowl: a clone of stock 24450 (retired from pets, PET 4.6) as a new id, with AuraInterruptFlags |= 0x1000
# (AURA_INTERRUPT_FLAG_MELEE_ATTACK): the pet's next white swing breaks it. Commands are triggered casts
# (IGNORE_AURA_INTERRUPT_FLAGS), so the first command lands from stealth with the +20% (FE 7, note 7).
_PROWL_AURA_INTERRUPT_FLAGS = 0x22403 | 0x1000
prowl_201984 = spell(
    id=201984,
    name='Prowl',
    school=School.NORMAL,
    dispel=5,
    attributes=0x1A150010,
    category=38,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=kits.UTILITY_POWER_TYPE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=149, points_per_level=5.0, implicit_target_a=1,
               apply_aura=_AURA_MOD_STEALTH),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1,
               apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1,
               apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=65),
    ],
    spell_icon_id=495,
    notes='hunter-pet-families F0: Cat slot 3. Clone of stock Prowl 24450 (stealth 150 + 5/level to MaxLevel 30, '
          '-50% speed, +20% damage done to schools 65, out of combat only, 10 s category 38 cooldown, '
          'StartRecoveryCategory 1178, the stock proc flags / charge) with AuraInterruptFlags 0x22403 | 0x1000 '
          '(MELEE_ATTACK). Manual. Visual 184 / icon 495 / active icon 252 from 24450.',
    raw_overrides=kits.utility_raw(
        PROWL_LEVEL, BaseLevel=1, MaxLevel=30, AttributesEx=0x10, AttributesEx2=0x200000, RangeIndex=1,
        ExcludeCasterAuraState=12, AuraInterruptFlags=_PROWL_AURA_INTERRUPT_FLAGS, ProcTypeMask=332116,
        ProcChance=101, ProcCharges=1, StartRecoveryCategory=1178, ActiveIconID=252, SpellVisualID_1=184,
        EffectBonusMultiplier_3=1.0,
        AuraDescription_Lang_enUS='Stealthed. Movement speed slowed.',
        Description_Lang_enUS="Your pet enters stealth, moving ${$m2*-1}% slower. Its first command or Kill Command "
                              "from stealth deals $s3% more damage. Any attack breaks stealth. Usable only out of "
                              "combat."),
)

tail_sweep_201985 = spell(
    id=201985,
    name='Tail Sweep',
    school=School.NORMAL,
    mechanic=0,
    attributes=kits.UTILITY_ATTRIBUTES,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=kits.UTILITY_POWER_TYPE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.KNOCK_BACK, base_points=149, implicit_target_a=6, misc_value=300),
    ],
    spell_icon_id=1525,
    notes='hunter-pet-families F0: Raptor slot 3. eff0 KNOCK_BACK (98) on the target, the stock Tail Sweep 15847 '
          'values (MiscValue 300 = 30 horizontal, bp 149 = 15 vertical), no damage, 5 yd melee, manual, 30 s. The core '
          'skips world / dungeon bosses, knockback-immune creatures, Giants, vehicles and rooted targets (FE 8a). '
          'Visual 3879 / icon 1525 from 15847.',
    raw_overrides=kits.utility_raw(
        TAIL_SWEEP_LEVEL, enemy_target=True, RangeIndex=2, DefenseType=2, PreventionType=2, FacingCasterFlags=1,
        SpellVisualID_1=3879,
        Description_Lang_enUS='Your pet sweeps its tail, knocking the target back. Does not work on bosses.'),
)

frenzied_regeneration_201986 = spell(
    id=201986,
    name='Frenzied Regeneration',
    school=School.NORMAL,
    attributes=kits.UTILITY_ATTRIBUTES,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=kits.UTILITY_POWER_TYPE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=_AURA_OBS_MOD_HEALTH,
               amplitude=1000),
    ],
    spell_icon_id=50,
    notes='hunter-pet-families F0: Bear slot 3. Aura 20 OBS_MOD_HEALTH 3% of max health per 1 s for 10 s (30%), on '
          'the pet, manual, 1 min. Visual 249 / icon 50 from Frenzied Regeneration 22842.',
    raw_overrides=kits.utility_raw(
        FRENZIED_REGENERATION_LEVEL, RangeIndex=1, DefenseType=0, PreventionType=2, SpellVisualID_1=249,
        AuraDescription_Lang_enUS='Regaining health.',
        Description_Lang_enUS='Your pet heals itself for $o1% of its maximum health over $d.'),
)

sticky_webbing_201753 = spell(
    id=201753,
    name='Sticky Webbing',
    school=School.NATURE,
    attributes=kits.UTILITY_ATTRIBUTES,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=kits.UTILITY_POWER_TYPE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=6, apply_aura=_AURA_HASTE_SPELLS),
    ],
    spell_icon_id=174,
    notes='hunter-pet-families F0: Spider slot 2 (Web Pull 201718 moves to slot 3). Aura 216 HASTE_SPELLS -25% '
          '(Curse of Tongues 1714 at the same level, live -25), single enemy, 30 yd, 30 s, 10 s cooldown, autocast '
          '(Tear Armor shape). Group 1096 Cast Time Debuffs (rule 4, highest per aura type: Curse of Tongues, '
          'Mind-numbing Poison). Visual 684 from Web 4167, icon 174 (Encasing Webs; Web Pull has 272).',
    raw_overrides=kits.utility_raw(
        STICKY_WEBBING_LEVEL, enemy_target=True, DefenseType=1, PreventionType=1, FacingCasterFlags=1,
        SpellVisualID_1=684,
        AuraDescription_Lang_enUS='Casting time increased.',
        Description_Lang_enUS="Spits sticky webbing at the target, increasing the casting time of its spells by "
                              "${$m1*-1}% for $d. Does not stack with Curse of Tongues or Mind-numbing Poison."),
)

# Kit v2 marker (CORE-AUDIT 3.2): a pet without it gets one re-seat of its bar to basic / slot 2 / slot 3 / Growl
# (Hunter::SeatDefaultPetBar), then learns it; the player's own order stands from then on. Same template as 201703.
hunter_pet_kit_v2_marker_202014 = spell(
    id=202014,
    name='Hunter Pet Kit Marker',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=0,
    notes="hunter-pet-families F0: hidden no-op passive, learned once by a hunter pet in the pass where "
          "Hunter::SeatDefaultPetBar re-seats its bar to the kit v2 layout (basic, slot 2, slot 3, Growl). Existing pets "
          "lack it and re-seat once on their next summon (no abdata SQL). Family 0, no effect (201703's template).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712188,
                   'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'EquippedItemClass': -1,
                   'EffectChainAmplitude_1': 1.0},
)


# ---- SkillLineAbility rows 30560-30605 (PET.md 4.4), AcquireMethod 2, ClassMask 0 ----
_FEROCITY_LINES = [208, 209, 217, 213, 654, 781, 787, 218, 788, 775, 785]            # 11 Ferocity lines
_TENACITY_PLACEHOLDER_LINES = [211, 212, 251, 766, 784, 214, 236, 215, 786]          # Tenacity minus Bear 210
_CUNNING_PLACEHOLDER_LINES = [653, 655, 656, 763, 767, 765, 764, 768, 780, 783]      # Cunning minus Spider 203

# 30561-30571 (Cower on the Ferocity lines) dropped by hunter-pet-families F0: Cower leaves every kit. 30560 (Dash on
# skill 270), 30572-30580 (Last Stand on the Tenacity lines) and 30581-30590 (Bullheaded on the Cunning lines) dropped
# by F3: every family has its own kit, so the placeholders leave every kit (PLAN §5.3). The freed ids stay unused (PLAN
# §4: a client may have them cached). The two line lists stay for Spit (the Cunning basic) and the tests.
_sla_rows = [(30591 + i, line, 201711) for i, line in enumerate(_CUNNING_PLACEHOLDER_LINES)]       # Spit
_sla_rows += [(30601, 203, 201710), (30602, 209, 201715), (30603, 217, 201716), (30604, 210, 201717),
              (30605, 203, 201718)]
# hunter-pet-families F0 (PLAN §4.1 F0 column): the five finished families' new utilities, learned at SpellLevel.
_sla_rows += [(30551, 208, lick_your_wounds_201983.id), (30552, 209, prowl_201984.id),
              (30553, 217, tail_sweep_201985.id), (30554, 210, frenzied_regeneration_201986.id),
              (30555, 203, sticky_webbing_201753.id)]
assert len(_sla_rows) == 20 and sorted(r[0] for r in _sla_rows) == [*range(30551, 30556), *range(30591, 30606)]
for _sla_id, _line, _spell_id in _sla_rows:
    skill_line_ability(id=_sla_id, skill_line=_line, spell_id=_spell_id, class_mask=0, acquire_method=2)


# ---- Retired stock family specials and Cunning basics (PET.md 4.6) ----
# 33 specials, every family (Prowl 24450 covers both its rows; Rake 59881, Ravage 50518 and Tendon Rip 50271 are
# NPC-used: retired from pets, potency kept).
for _special in (35290, 50519, 50256, 24423, 24450, 59881, 50245, 50433, 26090, 50271, 50541, 50498, 50871,
                 24640, 4167, 50285, 26064, 24844, 34889, 50479, 35346, 50518, 35387, 50274, 50318, 54644,
                 54680, 54706, 55749, 56626, 57386, 58604, 61193):
    retire_pet_spell(_special)

# 11 Cunning basics replaced by Spit / Venom Spit, family-scoped (Bite 8 rows, Claw 2, Smack 1).
retire_pet_spell(17253, families=[3, 24, 27, 30, 31, 34, 35, 38])
retire_pet_spell(16827, families=[26, 41])
retire_pet_spell(49966, families=[33])

# hunter-pet-families F0 (PLAN §1, CORE-AUDIT 3.2): Cower leaves every kit. Every family: the stock 270 row (SLA
# 13012) and any family-line row get AcquireMethod 0, and Cower is stripped from every family's CreatureSpellData
# record (it was still a default on the Ferocity families). Existing pets: pending_db_characters (worldserver stopped).
retire_pet_spell(1742)

# hunter-pet-families F3 (PLAN §5.3, §5.4): the placeholders Dash 61684, Last Stand 53478 and Bullheaded 53490 leave
# every kit now that every family has its own. Dropping their SkillLineAbility rows 30560 / 30572-30590 above is the
# whole retirement: no retire_pet_spell call, because there is nothing else to retire (checked 2026-11-13). Every stock
# SkillLineAbility row that names them (Dash 20673-20702 on the family lines, Last Stand 18141 / Bullheaded 18148 on
# 270) is already AcquireMethod 0, and no CreatureSpellData record holds them, so Pet::InitLevelupSpellsForLevel has no
# default to teach them again (a retire_pet_spell call would match nothing, which the pet data test reports as a wrong
# id). Existing pets lose them through pending_db_characters (worldserver stopped).


# ---- Spell groups (PET.md 2.5; spell_group accepts stock ids) ----
spell_group(1025, 24604)            # Furious Howl: Physical Crit Buffs
spell_group(1088, roar_of_courage_201715)    # Strength and Agility Buffs
spell_group(1015, tear_armor_201716)         # Major Armor Debuffs
spell_group(1062, menacing_roar_201717)      # AP Debuffs
spell_group(1096, sticky_webbing_201753)     # Cast Time Debuffs (F0)


# ---- Script bindings (PET.md 8.2 as corrected by H0-P-HANDOFF: positive keys for Bloodthirsty) ----
scripted_by(53186, 'spell_hun_pet_bloodthirsty')
scripted_by(53187, 'spell_hun_pet_bloodthirsty')
unbind_script(-24604, 'spell_hun_target_self_and_pet')   # X2: Furious Howl's raid retarget; 53434 stays bound, inert
scripted_by(web_pull_201718, 'spell_hun_pet_web_pull')


# =====================================================================================================
# H0-P2 (PET.md 2.1, 4.5, 5.2, 6.2, 8.2): mirror auras, Kill Command helpers, per-type kit auras, bindings
# =====================================================================================================

hunter_pet_versatility_201700 = spell(
    id=201700,
    name='Hunter Pet Versatility',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT),
    ],
    spell_icon_id=0,
    notes="H0-P2 PET 5.2: hidden mirror aura on the hunter pet / beast. Amounts stored 0, set by spell_hun_pet_passthrough (eff0 +V done, eff1 -V/2 taken, eff2 +V healing done). Family 0. custom_attr POSITIVE (eff1 negative would classify it negative, warlock 200854 precedent).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)

custom_attr(hunter_pet_versatility_201700, attributes=0x0E000000)


hunter_pet_crit_haste_201701 = spell(
    id=201701,
    name='Hunter Pet Crit and Haste',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
    ],
    spell_icon_id=0,
    notes="H0-P2 PET 5.2: hidden mirror aura. eff0 MOD_CRIT_PCT (290), eff1 MELEE_SLOW (193, haste). Amounts stored 0, set by spell_hun_pet_passthrough. Family 0.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


hunter_pet_damage_hook_201702 = spell(
    id=201702,
    name='Hunter Pet Damage Hook',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER),
    ],
    spell_icon_id=0,
    notes="H0-P2 PET 5.2: hidden mirror aura. eff0 MOD_DAMAGE_PERCENT_DONE 127 (S1 term on the pet, pet-multiplier copy on beasts), eff1 MOD_ATTACK_POWER (beasts only, 0 on the pet). Amounts stored 0, set by spell_hun_pet_passthrough. Family 0.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


hunter_pet_autocast_marker_201703 = spell(
    id=201703,
    name='Hunter Pet Autocast Marker',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=0,
    notes="H0-P2 review W1: hidden no-op passive learned once by a hunter pet (Hunter::SeatDefaultPetBar) right after it turns autocast on for the basic and the utility. Pet spells are saved UNCHANGED before the first tick (tame paths save at once), so the PETSPELL_NEW state can't mark 'autocast not yet applied'; a learned spell persists in pet_spell. Family 0, no effect.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0},
)



hunter_pet_utility_marker_201752 = spell(
    id=201752,
    name='Hunter Pet Utility Autocast Marker',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=0,
    notes="H0-P2 review C2-1: second hidden no-op passive, learned once by a hunter pet right after Hunter::SeatDefaultPetBar turns autocast on for its buff/debuff utility. Separate from 201703 (the basic's marker) because Roar of Courage (pet level 10) and Menacing Roar (14) are learned later than the basic. Family 0, no effect.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0},
)


kill_command_teleport_201704 = spell(
    id=201704,
    name='Kill Command (Teleport)',
    school=School.NORMAL,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=5, base_points=0, die_sides=0, implicit_target_a=1, implicit_target_b=65, radius_yards=2.0),
    ],
    spell_icon_id=0,
    notes='H0-P2 PET 2.1/6.2: pet-cast helper, family 0 (no SpellClassSet). eff0 TELEPORT_UNITS (5) A=1 caster, B=65 TARGET_DEST_TARGET_BACK, radius 2 yd, RangeIndex 13 - 36563 (Shadowstep) shape. Instant, no cost, no GCD, not passive. AttributesEx2 0x4 IGNORE_LINE_OF_SIGHT (as on 36563; triggered casts still run the LoS checks, review RD-1) and AttributesEx3 0x10000 SUPPRESS_CASTER_PROCS. Cast by spell_hun_kill_command_rework.',
    raw_overrides={'RangeIndex': 13, 'AttributesEx2': 0x4, 'AttributesEx3': 0x10000, 'CastingTimeIndex': 1, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0},
)


kill_command_strike_201705 = spell(
    id=201705,
    name='Kill Command (Strike)',
    school=School.NORMAL,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=6),
    ],
    spell_icon_id=0,
    notes='H0-P2 PET 2.1/6.2: pet-cast cosmetic strike, family 0, eff0 DUMMY on the target, no damage. AttributesEx3 0x10000 SUPPRESS_CASTER_PROCS. SpellVisualID_1 6762 (Claw 16827). range_yards 50000.0: triggered casts are range-checked strictly (Spell.cpp:6247-6251, :7336).',
    raw_overrides={'AttributesEx3': 0x10000, 'SpellVisualID_1': 6762, 'CastingTimeIndex': 1, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0},
)


ferocity_kit_201706 = spell(
    id=201706,
    name='Ferocity Kit',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
    ],
    spell_icon_id=0,
    notes="H0-P2 PET 4.5: hidden hunter aura, live +0 ms cooldown / +0% damage (the basics' DBC values are Ferocity's). eff0 SPELLMOD_COOLDOWN, eff1 SPELLMOD_DAMAGE, both masked to PET_BASIC_READER (0,0,0x800000): EffectSpellClassMaskA_3 (effect 1, dword 3) and EffectSpellClassMaskB_3 (effect 2, dword 3); nothing on d1 (a d1 b28 bit would reach every pet ability). Stored = live - 1.",
    raw_overrides={'SpellClassSet': 9, 'EffectSpellClassMaskA_3': m.PET_BASIC_READER[2], 'EffectSpellClassMaskB_3': m.PET_BASIC_READER[2], 'AuraDescription_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)


tenacity_kit_201707 = spell(
    id=201707,
    name='Tenacity Kit',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5999, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=193, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
    ],
    spell_icon_id=0,
    notes="H0-P2 PET 4.5: hidden hunter aura, live +6000 ms cooldown (stored 5999) / +194% damage (stored 193): Bite 4 s -> 10 s, 25.5 -> 75 potency. eff0 SPELLMOD_COOLDOWN, eff1 SPELLMOD_DAMAGE, both masked to PET_BASIC_READER (0,0,0x800000): EffectSpellClassMaskA_3 (effect 1, dword 3) and EffectSpellClassMaskB_3 (effect 2, dword 3); nothing on d1 (a d1 b28 bit would reach every pet ability). Stored = live - 1.",
    raw_overrides={'SpellClassSet': 9, 'EffectSpellClassMaskA_3': m.PET_BASIC_READER[2], 'EffectSpellClassMaskB_3': m.PET_BASIC_READER[2], 'AuraDescription_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)


cunning_kit_201708 = spell(
    id=201708,
    name='Cunning Kit',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
    ],
    spell_icon_id=0,
    notes="H0-P2 PET 4.5: hidden hunter aura, live 0 / 0 (reserved for Cunning families that keep a melee basic). eff0 SPELLMOD_COOLDOWN, eff1 SPELLMOD_DAMAGE, both masked to PET_BASIC_READER (0,0,0x800000): EffectSpellClassMaskA_3 (effect 1, dword 3) and EffectSpellClassMaskB_3 (effect 2, dword 3); nothing on d1 (a d1 b28 bit would reach every pet ability). Stored = live - 1.",
    raw_overrides={'SpellClassSet': 9, 'EffectSpellClassMaskA_3': m.PET_BASIC_READER[2], 'EffectSpellClassMaskB_3': m.PET_BASIC_READER[2], 'AuraDescription_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)


# ---- H0-P2 script bindings (PET.md 8.2) ----
unbind_script(34902, 'spell_hun_generic_scaling')    # 34903/34904 keep the stock class
scripted_by(34902, 'spell_hun_pet_scaling_rework')
scripted_by(hunter_pet_versatility_201700, 'spell_hun_pet_passthrough')
scripted_by(hunter_pet_crit_haste_201701, 'spell_hun_pet_passthrough')
scripted_by(hunter_pet_damage_hook_201702, 'spell_hun_pet_passthrough')
unbind_script(34026, 'spell_hun_kill_command')
scripted_by(34026, 'spell_hun_kill_command_rework')
