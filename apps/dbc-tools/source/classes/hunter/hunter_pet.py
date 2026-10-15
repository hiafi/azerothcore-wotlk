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
`_masks` constants module.
"""

from lib.dsl import AuraType, Effect, EffectType, PowerType, School
from lib.dsl.registry import const, retire_pet_spell, scripted_by, skill_line_ability, spell, spell_group, unbind_script
from . import _masks as m


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
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's armor by $s1% and chance to Dodge by $s2%.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
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
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's armor by $s1% and chance to Dodge by $s2%.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
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
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 69972, 'ProcChance': 100, 'DurationIndex': 0, 'RangeIndex': 2, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your pet's attacks have a $s2% chance to heal it for 5% of its total health over 5 sec.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
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
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 69972, 'ProcChance': 100, 'DurationIndex': 0, 'RangeIndex': 2, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your pet's attacks have a $s2% chance to heal it for 5% of its total health over 5 sec.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
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
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=33.0, potency_kind='direct', implicit_target_a=6),
    ],
    pet_owner_scaling=(PET_AP_FROM_RAP_PCT['value'], PET_AP_FROM_SP_PCT['value']),
    spell_icon_id=68,
    notes='H0-P1 (PET.md 4.3): Spider basic. Visual 7910 / Speed 40 and icon 68 from Poison Spit 35387, field shape from Acid Spit 55749 (direct hit). Ranged DmgClass 3 so it crits via GetUnitCriticalChance; d1 b28 + d2 b23 carrier; 0 Focus, 6 s cooldown, GCD 1500/133.',
    raw_overrides={**_SPIT_RAW, 'SpellVisualID_1': 7910, 'Speed': 40.0,
                   'Description_Lang_enUS': 'Spit venom at an enemy, causing {pot1} Nature damage.'},
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
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=33.0, potency_kind='direct', implicit_target_a=6),
    ],
    pet_owner_scaling=(PET_AP_FROM_RAP_PCT['value'], PET_AP_FROM_SP_PCT['value']),
    spell_icon_id=636,
    notes='H0-P1 (PET.md 4.3): Cunning placeholder basic. Visual 854 / Speed 24 and icon 636 from Acid Spit 55749; same numbers as Venom Spit 201710.',
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
                   'SpellClassSet': 9, 'SpellClassMask_2': m.PET_ABILITY, 'EquippedItemClass': -1,
                   'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0,
                   'AuraDescription_Lang_enUS': 'Increases Strength and Agility by $s1.',
                   'Description_Lang_enUS': 'Your pet roars, increasing the Strength and Agility of party and raid members within 100 yards by $s1 for $d. Does not stack with Strength of Earth Totem or Horn of Winter.'},
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
                   'SpellClassSet': 9, 'SpellClassMask_2': m.PET_ABILITY, 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0,
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
                   'AttributesEx6': 8388608, 'SpellClassSet': 9, 'SpellClassMask_2': m.PET_ABILITY, 'EquippedItemClass': -1,
                   'EffectChainAmplitude_1': 1.0,
                   'AuraDescription_Lang_enUS': 'Reduces melee attack power by $s1.',
                   'Description_Lang_enUS': 'Your pet roars, reducing the melee attack power of enemies within 10 yards by $s1 for $d. Does not stack with Demoralizing Shout, Demoralizing Roar, Vindication or Curse of Weakness.'},
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
                   'SpellVisualID_1': 684, 'SpellClassSet': 9, 'SpellClassMask_2': m.PET_ABILITY, 'EquippedItemClass': -1,
                   'EffectChainAmplitude_1': 1.0,
                   'Description_Lang_enUS': 'Shoots a web at an enemy up to 30 yards away and pulls it to your pet. Does not work on bosses.'},
)


# ---- SkillLineAbility rows 30560-30605 (PET.md 4.4), AcquireMethod 2, ClassMask 0 ----
_FEROCITY_LINES = [208, 209, 217, 213, 654, 781, 787, 218, 788, 775, 785]            # 11 Ferocity lines
_TENACITY_PLACEHOLDER_LINES = [211, 212, 251, 766, 784, 214, 236, 215, 786]          # Tenacity minus Bear 210
_CUNNING_PLACEHOLDER_LINES = [653, 655, 656, 763, 767, 765, 764, 768, 780, 783]      # Cunning minus Spider 203

_sla_rows = [(30560, 270, 61684)]                                                    # Dash, every family
_sla_rows += [(30561 + i, line, 1742) for i, line in enumerate(_FEROCITY_LINES)]                  # Cower, Ferocity
_sla_rows += [(30572 + i, line, 53478) for i, line in enumerate(_TENACITY_PLACEHOLDER_LINES)]      # Last Stand
_sla_rows += [(30581 + i, line, 53490) for i, line in enumerate(_CUNNING_PLACEHOLDER_LINES)]       # Bullheaded
_sla_rows += [(30591 + i, line, 201711) for i, line in enumerate(_CUNNING_PLACEHOLDER_LINES)]      # Spit
_sla_rows += [(30601, 203, 201710), (30602, 209, 201715), (30603, 217, 201716), (30604, 210, 201717),
              (30605, 203, 201718)]
assert len(_sla_rows) == 46 and [r[0] for r in _sla_rows] == list(range(30560, 30606))
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

# Cower off skill 270 for the 21 non-Ferocity families; the shared 270 row (SLA 13012) is retired for everyone and
# the Ferocity families relearn it from rows 30561-30571.
retire_pet_spell(1742, families=[4, 5, 6, 8, 9, 20, 21, 32, 42, 43,
                                 3, 24, 26, 27, 30, 31, 33, 34, 35, 38, 41], shared_lines=True)


# ---- Spell groups (PET.md 2.5; spell_group accepts stock ids) ----
spell_group(1025, 24604)            # Furious Howl: Physical Crit Buffs
spell_group(1088, roar_of_courage_201715)    # Strength and Agility Buffs
spell_group(1015, tear_armor_201716)         # Major Armor Debuffs
spell_group(1062, menacing_roar_201717)      # AP Debuffs


# ---- Script bindings (PET.md 8.2 as corrected by H0-P-HANDOFF: positive keys for Bloodthirsty) ----
scripted_by(53186, 'spell_hun_pet_bloodthirsty')
scripted_by(53187, 'spell_hun_pet_bloodthirsty')
unbind_script(-24604, 'spell_hun_target_self_and_pet')   # X2: Furious Howl's raid retarget; 53434 stays bound, inert
scripted_by(web_pull_201718, 'spell_hun_pet_web_pull')
