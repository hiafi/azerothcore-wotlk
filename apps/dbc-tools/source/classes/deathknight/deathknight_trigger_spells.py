"""
Deathknight - spells that are never directly cast - proc/periodic-tick effects, trigger_spell targets, hidden talent-rank buffs, etc..

Split from a single source/classes/deathknight.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .deathknight_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, School
from lib.dsl.registry import spell


plague_strike_45462 = spell(
    id=45462,
    name='Plague Strike',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=124, points_per_level=10.12, implicit_target_a=6),
        Effect(type=31, base_points=49, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=55078),
    ],
    spell_icon_id=2719,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A vicious strike that deals $<weapon>% weapon damage plus $<bonus> and infects the target with Blood Plague, a disease dealing Shadow damage over time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'RuneCostID': 221, 'SpellClassMask_1': 1, 'SpellClassSet': 15, 'SpellDescriptionVariableID': 81, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 11624, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


icy_touch_45477 = spell(
    id=45477,
    name='Icy Touch',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=126, points_per_level=4.0, die_sides=11, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, points_per_level=4.36, die_sides=0, implicit_target_a=6, trigger_spell=55095),
    ],
    spell_icon_id=2721,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx5': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee and ranged attack speed reduced by $55095s2%.', 'BaseLevel': 2, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Chills the target for $m1 to $M1 Frost damage and  infects them with Frost Fever, a disease that deals periodic damage and reduces melee and ranged attack speed by $55095s2% for $55095d.  Very high threat when in Frost Presence.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 14684919, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'ImplicitTargetA_3': 6, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 241, 'SpellClassMask_1': 2, 'SpellClassSet': 15, 'SpellLevel': 2, 'SpellPriority': 50, 'SpellVisualID_1': 11152, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


chains_of_ice_45524 = spell(
    id=45524,
    name='Chains of Ice',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-96, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=6, apply_aura=226, amplitude=1000),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=180,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx4': 2048, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Slowed by frozen chains.', 'BaseLevel': 22, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shackles the target with frozen chains, reducing their movement by $s1%, and infects them with Frost Fever.  The target regains $s2% of their movement each second for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 261, 'SpellClassMask_1': 4, 'SpellClassMask_2': 49152, 'SpellClassSet': 15, 'SpellLevel': 22, 'SpellVisualID_1': 12328, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 1023},
)


blood_strike_45902 = spell(
    id=45902,
    name='Blood Strike',
    school=School.NORMAL,
    attributes=262160,
    category=1207,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=259, points_per_level=20.16, implicit_target_a=6),
        Effect(type=31, base_points=39, implicit_target_a=6),
    ],
    spell_icon_id=2624,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly strike the enemy, causing $s2% weapon damage plus $<bonus>, total damage increased by ${$m3/2}.1% for each of your diseases on the target.', 'EffectBasePoints_3': 24, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'RuneCostID': 301, 'SpellClassMask_1': 4194304, 'SpellClassSet': 15, 'SpellDescriptionVariableID': 102, 'SpellLevel': 1, 'SpellVisualID_1': 11148, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blood_boil_48721 = spell(
    id=48721,
    name='Blood Boil',
    school=School.SHADOW,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=88, points_per_level=4.136363636363637, die_sides=19, implicit_target_a=18, implicit_target_b=16, radius_yards=10.0),
    ],
    spell_icon_id=2725,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 58); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 24, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Boils the blood of all enemies within $a1 yards, dealing $s1 Shadow damage.  Deals additional damage to targets infected with Blood Plague or Frost Fever.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 22, 'ImplicitTargetA_3': 22, 'ImplicitTargetB_2': 15, 'ImplicitTargetB_3': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 523, 'SpellClassMask_1': 262144, 'SpellClassSet': 15, 'SpellLevel': 24, 'SpellVisualID_1': 11117, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


obliterate_49020 = spell(
    id=49020,
    name='Obliterate',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=247, points_per_level=17.68421052631579, implicit_target_a=6),
        Effect(type=31, base_points=79, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, base_points=24, implicit_target_a=6),
    ],
    spell_icon_id=2639,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 61); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 36, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A brutal instant attack that deals $s2% weapon damage plus ${$m1*$m2/100}, total damage increased ${$m3/2}.1% per each of your diseases on the target, but consumes the diseases.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'RuneCostID': 587, 'SpellClassMask_2': 131072, 'SpellClassSet': 15, 'SpellLevel': 36, 'SpellVisualID_1': 11613, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ferocious_dead_49038 = spell(
    id=49038,
    name='Ferocious Dead',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29999, points_per_level=1000.0, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=999, points_per_level=33.333333333333336, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=170,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Raise Dead lasts an additional $/1000;s1 sec,  Army of the Dead lasts an additional $/1000;s2 sec, and Death Pact grants a heal over time effect for 15 sec equal to 50% of the amount healed.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 2048, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_corpse_explosion_49601 = spell(
    id=49601,
    name='Improved Corpse Explosion',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=10,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, points_per_level=0.4166666666666667, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=1737,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Exploded corpses cause $s1% additional damage.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 32, 'EffectSpellClassMaskB_2': 32, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 32, 'SpellClassSet': 15},
)


death_strike_49998 = spell(
    id=49998,
    name='Death Strike',
    school=School.NORMAL,
    attributes=262160,
    category=1196,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=111, points_per_level=7.708333333333333, implicit_target_a=6),
        Effect(type=31, base_points=74, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, base_points=405, points_per_level=37.666666666666664, implicit_target_a=6),
    ],
    spell_icon_id=2751,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 56); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712172, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A deadly attack that deals $s2% weapon damage plus ${$m1*$m2/100} and heals the Death Knight for $F% of $Ghis:her; maximum health for each of $Ghis:her; diseases on the target.', 'EffectChainAmplitude_1': 5.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 2, 'RuneCostID': 797, 'SpellClassMask_1': 16, 'SpellClassSet': 15, 'SpellLevel': 10, 'SpellPriority': 50, 'SpellVisualID_1': 11831, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blood_gorged_50096 = spell(
    id=50096,
    name='Blood Gorged',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, points_per_level=0.13333333333333333, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=24,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CasterAuraState': 23, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you are above 75% health, you deal $s1% more damage.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 20971521, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


crypt_fever_50508 = spell(
    id=50508,
    name='Crypt Fever',
    school=School.NATURE,
    dispel=DispelType.DISEASE,
    mechanic=22,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=0.3333333333333333, implicit_target_a=6, apply_aura=284, misc_value=22, trigger_spell=65142),
    ],
    spell_icon_id=264,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 1073741824, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases disease damage taken by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your diseases also cause Crypt Fever, which increases disease damage taken by the target by $s1%.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_3': 16, 'SpellClassSet': 15},
)


pestilence_50842 = spell(
    id=50842,
    name='Pestilence',
    school=School.SHADOW,
    dispel=DispelType.DISEASE,
    mechanic=22,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=47, radius_yards=5.0),
        Effect(type=77, die_sides=0, implicit_target_a=87, implicit_target_b=16, radius_yards=10.0),
    ],
    spell_icon_id=97,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx5': 4096, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Spreads existing Blood Plague and Frost Fever infections from your target to all other enemies within $a3 yards.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectRadiusIndex_2': 52, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 2, 'RuneCostID': 844, 'SpellClassMask_2': 65536, 'SpellClassSet': 15, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 11172, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ebon_plague_51726 = spell(
    id=51726,
    name='Ebon Plague',
    school=School.SHADOW,
    dispel=DispelType.DISEASE,
    mechanic=22,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=6, apply_aura=284, misc_value=22, trigger_spell=65142),
        Effect(type=EffectType.APPLY_AURA, base_points=3, points_per_level=0.15254237288135594, implicit_target_a=6, apply_aura=AuraType.DUMMY, misc_value=126),
    ],
    spell_icon_id=1933,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases disease damage taken by $s1%.\r\nIncreases magic damage taken by $s2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Crypt Fever morphs into Ebon Plague, which increases magic damage taken by $s2% in addition to increasing disease damage taken by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712188, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 2048, 'SpellClassMask_3': 64, 'SpellClassSet': 15, 'SpellLevel': 1},
)


blade_barrier_51789 = spell(
    id=51789,
    name='Blade Barrier',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2, points_per_level=-0.1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.DUMMY, base_points=5, implicit_target_a=1),
    ],
    spell_icon_id=85,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1% less damage taken.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Blood Runes are on cooldown, you gain the Blade Barrier effect, which decreases damage taken by $s1% for the next $51789d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 20, 'SpellVisualID_1': 342},
)


on_a_pale_horse_51969 = spell(
    id=51969,
    name='On a Pale Horse',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=0.16666666666666666, implicit_target_a=1, apply_aura=211),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-11, misc_value=5),
    ],
    spell_icon_id=1241,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You become as hard to stop as death itself.  The duration of all Stun and Fear effects used against you is reduced by 10%, and your mounted speed is increased by 10%.  This does not stack with other movement speed increasing effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 67108864, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


on_a_pale_horse_51983 = spell(
    id=51983,
    name='On a Pale Horse',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=0.16666666666666666, implicit_target_a=1, apply_aura=172),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, points_per_level=-0.16666666666666666, implicit_target_a=1, apply_aura=232, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, points_per_level=-0.16666666666666666, implicit_target_a=1, apply_aura=232, misc_value=5),
    ],
    spell_icon_id=1241,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You become as hard to stop as death itself.  The duration of all Stun and Fear effects used against you is reduced by 10%, and your mounted speed is increased by 10%.  This does not stack with other movement speed increasing effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 67108864, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


will_of_the_necropolis_52284 = spell(
    id=52284,
    name='Will of the Necropolis',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, points_per_level=0.16666666666666666, implicit_target_a=1, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=857,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'TEST', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 921, 'SpellClassSet': 15},
)


plague_strike_59133 = spell(
    id=59133,
    name='Plague Strike',
    school=School.SHADOW,
    dispel=DispelType.DISEASE,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=12000,
    effects=[
        Effect(type=121, base_points=36, points_per_level=6.08, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=72, points_per_level=-0.92, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000, misc_value=127),
    ],
    spell_icon_id=2719,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AttributesEx6': 4096, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Deals $o2 Shadow damage over $d.', 'BaseLevel': 55, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A vicious strike that deals weapon damage plus $s1 modified by attack power and plagues the target, dealing $o2 Shadow damage over $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 2, 'RuneCostID': 1426, 'SpellClassMask_1': 1, 'SpellClassMask_2': 2048, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50, 'SpellVisualID_1': 11624, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blood_gorged_61274 = spell(
    id=61274,
    name='Blood Gorged',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, points_per_level=0.13333333333333333, implicit_target_a=1, apply_aura=280),
    ],
    spell_icon_id=24,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712188, 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 20971521, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


death_coil_62900 = spell(
    id=62900,
    name='Death Coil',
    school=School.SHADOW,
    attributes=262144,
    category=633,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=166, points_per_level=11.04, implicit_target_a=25),
    ],
    spell_icon_id=88,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx4': 128, 'AuraDescription_Lang_Mask': 16712172, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fire a blast of unholy energy, causing $s1 Shadow damage to an enemy target or healing ${$m1*1.5} damage from a friendly Undead target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 2331, 'SpellClassMask_1': 8192, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50, 'SpellVisualID_1': 10755, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


death_strike_66188 = spell(
    id=66188,
    name='Death Strike',
    school=School.NORMAL,
    attributes=2359312,
    category=1196,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=121, base_points=55, points_per_level=1.5333333333333334, implicit_target_a=6),
        Effect(type=31, base_points=74, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, base_points=1309, implicit_target_a=6),
    ],
    spell_icon_id=2751,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 17039360, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A deadly attack that deals $s2% offhand weapon damage plus a bonus and heals the Death Knight for $F% of $Ghis:her; maximum health for each of $Ghis:her; diseases on the target.', 'EffectChainAmplitude_1': 5.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RuneCostID': 782, 'SpellClassMask_1': 16, 'SpellClassSet': 15, 'SpellPriority': 50, 'SpellVisualID_1': 11831, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


frost_strike_66196 = spell(
    id=66196,
    name='Frost Strike',
    school=School.FROST,
    attributes=2359312,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=121, base_points=42, points_per_level=1.3666666666666667, implicit_target_a=6),
        Effect(type=31, base_points=54, implicit_target_a=6),
    ],
    spell_icon_id=2740,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 6 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 17039360, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly strike the enemy, causing $s2% offhand weapon damage plus a bonus as Frost damage.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskC_2': 4, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'ImplicitTargetA_3': 6, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RuneCostID': 1824, 'SpellClassMask_2': 4, 'SpellClassSet': 15, 'SpellVisualID_1': 11612, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


obliterate_66198 = spell(
    id=66198,
    name='Obliterate',
    school=School.NORMAL,
    attributes=2359312,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=121, base_points=123, points_per_level=2.8, implicit_target_a=6),
        Effect(type=31, base_points=79, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, base_points=24, implicit_target_a=6),
    ],
    spell_icon_id=2639,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 4 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 17039360, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A brutal instant attack that deals $s2% offhand weapon damage plus a bonus, total damage increased ${$m3/2}.1% per each of your diseases on the target, but consumes the diseases.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RuneCostID': 2330, 'SpellClassMask_2': 131072, 'SpellClassSet': 15, 'SpellVisualID_1': 11613, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blood_strike_66215 = spell(
    id=66215,
    name='Blood Strike',
    school=School.NORMAL,
    attributes=2359312,
    category=1207,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=121, base_points=129, points_per_level=4.2, implicit_target_a=6),
        Effect(type=31, base_points=39, implicit_target_a=6),
    ],
    spell_icon_id=2624,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 6 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 17039360, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly strike the enemy, causing $s2% offhand weapon damage plus a bonus, total damage increased by ${$m3/2}.1% for each of your diseases on the target.', 'EffectBasePoints_3': 24, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RuneCostID': 1844, 'SpellClassMask_1': 4194304, 'SpellClassSet': 15, 'SpellVisualID_1': 11148, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


heart_strike_55050 = spell(
    id=55050,
    name='Heart Strike',
    school=School.NORMAL,
    attributes=262160,
    category=1207,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=249, points_per_level=19.44, implicit_target_a=6, chain_targets=2),
        Effect(type=31, base_points=49, implicit_target_a=6, chain_targets=2),
    ],
    spell_icon_id=3145,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 4096, 'AttributesEx3': 1024, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly strike the target and his nearest ally, causing $m2% weapon damage plus $<bonus> on the primary target, and ${$m2/2}% weapon damage plus ${$<bonus>/2} on the secondary target.  Each target takes $m3% additional damage for each of your diseases active on that target$?s58616[, and movement speed is reduced by by $58617s1% for $58617d.][.]', 'EffectBasePoints_3': 9, 'EffectChainAmplitude_1': 0.5, 'EffectChainAmplitude_2': 0.5, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'ImplicitTargetA_3': 25, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'RuneCostID': 1142, 'SpellClassMask_1': 16777216, 'SpellClassSet': 15, 'SpellDescriptionVariableID': 166, 'SpellLevel': 55, 'SpellVisualID_1': 11148, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


scourge_strike_55090 = spell(
    id=55090,
    name='Scourge Strike',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=339, points_per_level=18.4, implicit_target_a=6),
        Effect(type=31, base_points=69, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, base_points=11, implicit_target_a=6),
    ],
    spell_icon_id=3143,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'CumulativeAura': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'An unholy strike that deals $s2% of weapon damage as Physical damage plus ${$m1*$m2/100}.  In addition, for each of your diseases on your target, you deal an additional $s3% of the Physical damage done as Shadow damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'RuneCostID': 1145, 'SpellClassMask_2': 134217728, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50, 'SpellVisualID_1': 11832, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


virulence_48962 = spell(
    id=48962,
    name='Virulence',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=55, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=208,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to hit with your spells by $s1% and reduces the chance that your damage over time diseases can be cured by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 736225, 'EffectSpellClassMaskA_2': 1098, 'EffectSpellClassMaskB_3': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


morbidity_48963 = spell(
    id=48963,
    name='Morbidity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-5001, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=118,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and healing of Death Coil by $s1% and reduces the cooldown on Death and Decay by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8192, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


ravenous_dead_48965 = spell(
    id=48965,
    name='Ravenous Dead',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3010,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Strength by $s1% and the contribution your Ghouls get from your Strength and Stamina by $s2%.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16, 'EffectSpellClassMaskC_1': 4096, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


bloody_strikes_48977 = spell(
    id=48977,
    name='Bloody Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2624,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of Blood Strike by $s2% and Heart Strike by $s1%, and increases the damage of Blood Boil by $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16777216, 'EffectSpellClassMaskB_1': 4194304, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


bladed_armor_48978 = spell(
    id=48978,
    name='Bladed Armor',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=179, implicit_target_a=1, apply_aura=285, misc_value=1),
        Effect(type=EffectType.DUMMY),
    ],
    spell_icon_id=2653,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your attack power by $s2 for every ${$m1*$m2} armor value you have.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


butchery_48979 = spell(
    id=48979,
    name='Butchery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=85, misc_value=6),
    ],
    spell_icon_id=2664,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you kill an enemy that grants experience or honor, you generate up to 10 runic power.  In addition, you generate 1 runic power per 5 sec while in combat.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_rune_tap_48985 = spell(
    id=48985,
    name='Improved Rune Tap',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-10001, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2726,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 33554432, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 6, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the health provided by Rune Tap by $s1% and lowers its cooldown by $/1000;s2 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EffectSpellClassMaskB_1': 134217728, 'EquippedItemClass': -1, 'MaxLevel': 16, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 582, 'SpellClassMask_1': 262144, 'SpellClassSet': 15, 'SpellLevel': 6, 'SpellVisualID_1': 1225},
)


subversion_48997 = spell(
    id=48997,
    name='Subversion',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-9, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=3009,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of Blood Strike, Scourge Strike, Heart Strike and Obliterate by $s2%, and reduces threat generated while in Blood or Unholy Presence by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8454144, 'EffectSpellClassMaskB_1': 20971520, 'EffectSpellClassMaskB_2': 134348800, 'EffectSpellClassMaskB_3': 128, 'EffectSpellClassMaskC_1': 4194305, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


outbreak_49013 = spell(
    id=49013,
    name='Outbreak',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=97,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of Plague Strike by $s1% and Scourge Strike by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_2': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 584, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


vendetta_49015 = spell(
    id=49015,
    name='Vendetta',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3008,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals you for up to $s1% of your maximum health whenever you kill a target that yields experience or honor.', 'EffectBasePoints_2': -11, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2, 'RangeIndex': 1, 'RuneCostID': 586, 'SpellClassMask_1': 65536, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellVisualID_1': 7578},
)


sudden_doom_49018 = spell(
    id=49018,
    name='Sudden Doom',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1939,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Blood Strikes and Heart Strikes have a $h% chance to launch a free Death Coil at your target.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 5, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 15},
)


might_of_mograine_49023 = spell(
    id=49023,
    name='Might of Mograine',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=2639,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Blood Boil, Blood Strike, Death Strike, and Heart Strike abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 21233680, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


merciless_combat_49024 = spell(
    id=49024,
    name='Merciless Combat',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=112, misc_value=7277),
    ],
    spell_icon_id=2656,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Icy Touch, Howling Blast, Obliterate and Frost Strike do an additional $s1% damage when striking targets with less than 35% health.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskA_2': 131078, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50, 'TargetAuraState': 13},
)


bloodworms_49027 = spell(
    id=49027,
    name='Bloodworms',
    school=School.NATURE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, die_sides=3, implicit_target_a=1, apply_aura=231, misc_value=7252, trigger_spell=50452),
    ],
    spell_icon_id=1987,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your weapon hits have a $h% chance to cause the target to spawn 2-4 Bloodworms.  Bloodworms attack your enemies, healing you as they do damage for 20 sec or until killed.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 3, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15},
)


crypt_fever_49032 = spell(
    id=49032,
    name='Crypt Fever',
    school=School.NATURE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=7282),
    ],
    spell_icon_id=264,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your diseases also cause Crypt Fever, which increases disease damage taken by the target by $50508s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


epidemic_49036 = spell(
    id=49036,
    name='Epidemic',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=234,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of Blood Plague and Frost Fever by $/1000;s1 sec.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 100663296, 'EffectSpellClassMaskA_3': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


endless_winter_49137 = spell(
    id=49137,
    name='Endless Winter',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=164,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your strength is increased by $s1% and the cost of your Mind Freeze is reduced to 10 runic power.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


black_ice_49140 = spell(
    id=49140,
    name='Black Ice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=48),
    ],
    spell_icon_id=154,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Frost and Shadow damage by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2182250279, 'EffectSpellClassMaskA_2': 447, 'EffectSpellClassMaskB_1': 41975808, 'EffectSpellClassMaskB_2': 1024, 'EffectSpellClassMaskC_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


on_a_pale_horse_49146 = spell(
    id=49146,
    name='On a Pale Horse',
    school=School.NORMAL,
    attributes=16777616,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=on_a_pale_horse_51983.id),
        Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=on_a_pale_horse_51969.id),
    ],
    spell_icon_id=3005,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You become as hard to stop as death itself.  The duration of all Stun and Fear effects used against you is reduced by 10%, and your mounted speed is increased by 10%.  This does not stack with other movement speed increasing effects.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskB_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


chill_of_the_grave_49149 = spell(
    id=49149,
    name='Chill of the Grave',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=231, misc_value=10, trigger_spell=50480),
    ],
    spell_icon_id=976,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Chains of Ice, Howling Blast, Icy Touch and Obliterate generate 2.5 additional runic power.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87056, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_icy_touch_49175 = spell(
    id=49175,
    name='Improved Icy Touch',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=2721,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Icy Touch does an additional $s1% damage and your Frost Fever reduces melee and ranged attack speed by an additional $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_2': 67108864, 'EffectSpellClassMaskC_2': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RuneCostID': 642, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


blade_barrier_49182 = spell(
    id=49182,
    name='Blade Barrier',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=blade_barrier_51789.id),
        Effect(type=EffectType.DUMMY, base_points=5),
    ],
    spell_icon_id=85,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Blood Runes are on cooldown, you gain the Blade Barrier effect, which decreases damage taken by $s1% for the next $51789d.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 14684919, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'RuneCostID': 646, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


frigid_dreadplate_49186 = spell(
    id=49186,
    name='Frigid Dreadplate',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=184),
    ],
    spell_icon_id=2738,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the chance melee attacks will hit you by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellPriority': 50},
)


rime_49188 = spell(
    id=49188,
    name='Rime',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=59052),
    ],
    spell_icon_id=56,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Icy Touch and Obliterate by $s1% and casting Obliterate has a $h% chance to reset the cooldown on Howling Blast and cause your next Howling Blast to consume no runes.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskA_2': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 5, 'ProcTypeMask': 69904, 'RangeIndex': 1, 'SpellClassSet': 15},
)


will_of_the_necropolis_49189 = spell(
    id=49189,
    name='Will of the Necropolis',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=34, implicit_target_a=1),
        Effect(type=EffectType.LEARN_SPELL, base_points=14, implicit_target_a=1, trigger_spell=will_of_the_necropolis_52284.id),
    ],
    spell_icon_id=1762,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Damage that would take you below $s1% health or taken while you are at $s1% health is reduced by $52284s1%.', 'EffectBasePoints_3': 4, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 649, 'SpellClassSet': 15},
)


unholy_blight_49194 = spell(
    id=49194,
    name='Unholy Blight',
    school=School.SHADOW,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1494,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taking damage from a vile swarm of unholy insects.  Diseases cannot be dispelled.', 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes the victims of your Death Coil to be surrounded by a vile swarm of unholy insects, taking $49194s1% of the damage done by the Death Coil over $50536d, and preventing any diseases on the victim from being dispelled.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 55},
)


acclimation_49200 = spell(
    id=49200,
    name='Acclimation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=10, trigger_spell=1206),
    ],
    spell_icon_id=1930,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you are hit by a spell, you have a $h% chance to boost your resistance to that type of magic for 18 sec.  Stacks up to 3 times.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3, 'EffectSpellClassMaskB_2': 536870912, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 131072, 'RangeIndex': 1, 'SpellClassSet': 15},
)


tundra_stalker_49202 = spell(
    id=49202,
    name='Tundra Stalker',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=112, misc_value=7277),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=100,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal $s1% more damage to targets infected with Frost Fever.  Also increases your expertise by $s2.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 21242899, 'EffectSpellClassMaskA_2': 773001510, 'EffectSpellClassMaskA_3': 8, 'EffectSpellClassMaskC_2': 131074, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


reaping_49208 = spell(
    id=49208,
    name='Reaping',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=226, amplitude=30000),
    ],
    spell_icon_id=22,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you hit with Blood Strike or Pestilence there is a $h% chance that the Blood Rune becomes a Death Rune when it activates.  Death Runes count as a Blood, Frost or Unholy Rune.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 69648, 'RangeIndex': 1, 'SpellClassSet': 15},
)


wandering_plague_49217 = spell(
    id=49217,
    name='Wandering Plague',
    school=School.NATURE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7288),
    ],
    spell_icon_id=1614,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your diseases damage an enemy, there is a chance equal to your melee critical strike chance that they will cause $s1% additional damage to the target and all enemies within 8 yards.  Ignores any target under the effect of a spell that is cancelled by taking damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1},
)


blood_caked_blade_49219 = spell(
    id=49219,
    name='Blood-Caked Blade',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=50463),
    ],
    spell_icon_id=138,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auto attacks have a $h% chance to cause a Blood-Caked Strike, which hits for $50463s1% weapon damage plus ${$50463m1/2}.1% for each of your diseases on the target.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


dirge_49223 = spell(
    id=49223,
    name='Dirge',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=231, misc_value=10, trigger_spell=51206),
    ],
    spell_icon_id=2206,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Death Strike, Plague Strike and Scourge Strike generate 2.5 additional runic power.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4353, 'EffectSpellClassMaskA_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87056, 'RangeIndex': 1, 'SpellClassSet': 15},
)


magic_suppression_49224 = spell(
    id=49224,
    name='Magic Suppression',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, mechanic=26, implicit_target_a=1, apply_aura=107, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=99,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You take $s2% less damage from all magic.  In addition, your Anti-Magic Shell absorbs an additional $s1% of spell damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcCharges': 1, 'RangeIndex': 1, 'RuneCostID': 655, 'SpellClassSet': 15, 'SpellLevel': 55},
)


bladed_armor_49390 = spell(
    id=49390,
    name='Bladed Armor',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=89, implicit_target_a=1, apply_aura=285, misc_value=1),
        Effect(type=EffectType.DUMMY, base_points=1),
    ],
    spell_icon_id=2653,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your attack power by $s2 for every ${$m1*$m2} armor value you have.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


bladed_armor_49391 = spell(
    id=49391,
    name='Bladed Armor',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=285, misc_value=1),
        Effect(type=EffectType.DUMMY, base_points=2),
    ],
    spell_icon_id=2653,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your attack power by $s2 for every ${$m1*$m2} armor value you have.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


bladed_armor_49392 = spell(
    id=49392,
    name='Bladed Armor',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=44, implicit_target_a=1, apply_aura=285, misc_value=1),
        Effect(type=EffectType.DUMMY, base_points=3),
    ],
    spell_icon_id=2653,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your attack power by $s2 for every ${$m1*$m2} armor value you have.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


bladed_armor_49393 = spell(
    id=49393,
    name='Bladed Armor',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=35, implicit_target_a=1, apply_aura=285, misc_value=1),
        Effect(type=EffectType.DUMMY, base_points=4),
    ],
    spell_icon_id=2653,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your attack power by $s2 for every ${$m1*$m2} armor value you have.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


bloody_strikes_49394 = spell(
    id=49394,
    name='Bloody Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2624,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of Blood Strike by $s2% and Heart Strike by $s1%, and increases the damage of Blood Boil by $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16777216, 'EffectSpellClassMaskB_1': 4194304, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


bloody_strikes_49395 = spell(
    id=49395,
    name='Bloody Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=44, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2624,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of Blood Strike by $s2% and Heart Strike by $s1%, and increases the damage of Blood Boil by $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16777216, 'EffectSpellClassMaskB_1': 4194304, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


runic_power_mastery_49455 = spell(
    id=49455,
    name='Runic Power Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=149, implicit_target_a=1, apply_aura=35, misc_value=6),
    ],
    spell_icon_id=1954,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your maximum Runic Power by ${$m1/10}.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 533504, 'EffectSpellClassMaskA_2': 288, 'EffectSpellClassMaskB_1': 1048576, 'EffectSpellClassMaskC_2': 384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


death_rune_mastery_49467 = spell(
    id=49467,
    name='Death Rune Mastery',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=226, amplitude=30000),
    ],
    spell_icon_id=2622,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you hit with Death Strike or Obliterate there is a $h% chance that the Frost and Unholy Runes will become Death Runes when they activate.  Death Runes count as a Blood, Frost or Unholy Rune.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 87312, 'RangeIndex': 1, 'SpellClassMask_1': 16384, 'SpellClassSet': 15, 'SpellVisualID_1': 10590},
)


glacier_rot_49471 = spell(
    id=49471,
    name='Glacier Rot',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7244),
    ],
    spell_icon_id=196,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Diseased enemies take $s1% more damage from your Icy Touch, Howling Blast and Frost Strike.', 'EffectBasePoints_2': 5, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 1026, 'EffectSpellClassMaskA_2': 4103, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


butchery_49483 = spell(
    id=49483,
    name='Butchery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=199, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=85, misc_value=6),
    ],
    spell_icon_id=2664,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you kill an enemy that grants experience or honor, you generate up to 20 runic power.  In addition, you generate 2 runic power per 5 sec while in combat.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_rune_tap_49488 = spell(
    id=49488,
    name='Improved Rune Tap',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-20001, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2726,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 33554432, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 6, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the health provided by Rune Tap by $s1% and lowers its cooldown by $/1000;s2 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EffectSpellClassMaskB_1': 134217728, 'EquippedItemClass': -1, 'MaxLevel': 16, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 661, 'SpellClassMask_1': 262144, 'SpellClassSet': 15, 'SpellLevel': 6, 'SpellVisualID_1': 1225},
)


improved_rune_tap_49489 = spell(
    id=49489,
    name='Improved Rune Tap',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2726,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 33554432, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 6, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the health provided by Rune Tap by $s1% and lowers its cooldown by $/1000;s2 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EffectSpellClassMaskB_1': 134217728, 'EquippedItemClass': -1, 'MaxLevel': 16, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 662, 'SpellClassMask_1': 262144, 'SpellClassSet': 15, 'SpellLevel': 6, 'SpellVisualID_1': 1225},
)


subversion_49490 = spell(
    id=49490,
    name='Subversion',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-17, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=3009,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of Blood Strike, Scourge Strike, Heart Strike and Obliterate by $s2%, and reduces threat generated while in Blood or Unholy Presence by $s1%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8454144, 'EffectSpellClassMaskB_1': 20971520, 'EffectSpellClassMaskB_2': 134348800, 'EffectSpellClassMaskB_3': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


subversion_49491 = spell(
    id=49491,
    name='Subversion',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=3009,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of Blood Strike, Scourge Strike, Heart Strike and Obliterate by $s2%, and reduces threat generated while in Blood or Unholy Presence by $s1%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8454144, 'EffectSpellClassMaskB_1': 20971520, 'EffectSpellClassMaskB_2': 134348800, 'EffectSpellClassMaskB_3': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


blade_barrier_49500 = spell(
    id=49500,
    name='Blade Barrier',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64855),
        Effect(type=EffectType.DUMMY, base_points=5, implicit_target_a=6),
    ],
    spell_icon_id=85,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Blood Runes are on cooldown, you gain the Blade Barrier effect, which decreases damage taken by $64855s1% for the next $64855d.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 14684919, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 6, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'RuneCostID': 663, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


blade_barrier_49501 = spell(
    id=49501,
    name='Blade Barrier',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64856),
        Effect(type=EffectType.DUMMY, base_points=5, implicit_target_a=6),
    ],
    spell_icon_id=85,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Blood Runes are on cooldown, you gain the Blade Barrier effect, which decreases damage taken by $64856s1% for the next $64856d.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 14684919, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 6, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'RuneCostID': 664, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


sudden_doom_49529 = spell(
    id=49529,
    name='Sudden Doom',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1939,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Blood Strikes and Heart Strikes have a $h% chance to launch a free Death Coil at your target.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 15},
)


sudden_doom_49530 = spell(
    id=49530,
    name='Sudden Doom',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1939,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Blood Strikes and Heart Strikes have a $h% chance to launch a free Death Coil at your target.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 15, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 15},
)


might_of_mograine_49533 = spell(
    id=49533,
    name='Might of Mograine',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=2639,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Blood Boil, Blood Strike, Death Strike, and Heart Strike abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 21233680, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


might_of_mograine_49534 = spell(
    id=49534,
    name='Might of Mograine',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=44, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=2639,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Blood Boil, Blood Strike, Death Strike, and Heart Strike abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 21233680, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


merciless_combat_49538 = spell(
    id=49538,
    name='Merciless Combat',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=112, misc_value=7277),
    ],
    spell_icon_id=2656,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Icy Touch, Howling Blast, Obliterate and Frost Strike do an additional $s1% damage when striking targets with less than 35% health.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskA_2': 131078, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50, 'TargetAuraState': 13},
)


bloodworms_49542 = spell(
    id=49542,
    name='Bloodworms',
    school=School.NATURE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, die_sides=3, implicit_target_a=1, apply_aura=231, misc_value=7252, trigger_spell=50452),
    ],
    spell_icon_id=1987,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your weapon hits have a $h% chance to cause the target to spawn 2-4 Bloodworms.  Bloodworms attack your enemies, healing you as they do damage for 20 sec or until killed.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 6, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15},
)


bloodworms_49543 = spell(
    id=49543,
    name='Bloodworms',
    school=School.NATURE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, die_sides=3, implicit_target_a=1, apply_aura=231, misc_value=7252, trigger_spell=50452),
    ],
    spell_icon_id=1987,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your weapon hits have a $h% chance to cause the target to spawn 2-4 Bloodworms.  Bloodworms attack your enemies, healing you as they do damage for 20 sec or until killed.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 9, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15},
)


epidemic_49562 = spell(
    id=49562,
    name='Epidemic',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=234,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of Blood Plague and Frost Fever by $/1000;s1 sec.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_2': 100663296, 'EffectSpellClassMaskA_3': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


morbidity_49564 = spell(
    id=49564,
    name='Morbidity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-10001, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=118,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and healing of Death Coil by $s1% and reduces the cooldown on Death and Decay by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8192, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


morbidity_49565 = spell(
    id=49565,
    name='Morbidity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-15001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=118,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and healing of Death Coil by $s1% and reduces the cooldown on Death and Decay by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8192, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


virulence_49567 = spell(
    id=49567,
    name='Virulence',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=55, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=19, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=208,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to hit with your spells by $s1% and reduces the chance that your damage over time diseases can be cured by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 736225, 'EffectSpellClassMaskA_2': 1098, 'EffectSpellClassMaskB_3': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


virulence_49568 = spell(
    id=49568,
    name='Virulence',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=55, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=29, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=208,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to hit with your spells by $s1% and reduces the chance that your damage over time diseases can be cured by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 736225, 'EffectSpellClassMaskA_2': 1098, 'EffectSpellClassMaskB_3': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


ravenous_dead_49571 = spell(
    id=49571,
    name='Ravenous Dead',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.DUMMY, base_points=39, implicit_target_a=1),
    ],
    spell_icon_id=3010,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Strength by $s1% and the contribution your Ghouls get from your Strength and Stamina by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16, 'EffectSpellClassMaskC_1': 4096, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


ravenous_dead_49572 = spell(
    id=49572,
    name='Ravenous Dead',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.DUMMY, base_points=59, implicit_target_a=1),
    ],
    spell_icon_id=3010,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Strength by $s1% and the contribution your Ghouls get from your Strength and Stamina by $s2%', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16, 'EffectSpellClassMaskC_1': 4096, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


unholy_command_49588 = spell(
    id=49588,
    name='Unholy Command',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2723,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Death Grip ability by $/1000;s1 sec.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_2': 268435456, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


unholy_command_49589 = spell(
    id=49589,
    name='Unholy Command',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-10001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2723,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Death Grip ability by $/1000;s1 sec.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_2': 268435456, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


dirge_49599 = spell(
    id=49599,
    name='Dirge',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=231, misc_value=10, trigger_spell=51206),
    ],
    spell_icon_id=2206,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Death Strike, Plague Strike and Scourge Strike generate 5 additional runic power.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4353, 'EffectSpellClassMaskA_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 349200, 'RangeIndex': 1, 'SpellClassSet': 15},
)


magic_suppression_49610 = spell(
    id=49610,
    name='Magic Suppression',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=107, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=99,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You take $s2% less damage from all magic.  In addition, your Anti-Magic Shell absorbs an additional $s1% of spell damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 690, 'SpellClassSet': 15, 'SpellLevel': 55},
)


magic_suppression_49611 = spell(
    id=49611,
    name='Magic Suppression',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, mechanic=26, implicit_target_a=1, apply_aura=107, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=99,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You take $s2% less damage from all magic.  In addition, your Anti-Magic Shell absorbs an additional $s1% of spell damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcCharges': 1, 'RangeIndex': 1, 'RuneCostID': 691, 'SpellClassSet': 15, 'SpellLevel': 55},
)


blood_caked_blade_49627 = spell(
    id=49627,
    name='Blood-Caked Blade',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=50463),
    ],
    spell_icon_id=138,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auto attacks have a $h% chance to cause a Blood-Caked Strike, which hits for $50463s1% weapon damage plus ${$50463m1/2}.1% for each of your diseases on the target.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


blood_caked_blade_49628 = spell(
    id=49628,
    name='Blood-Caked Blade',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=50463),
    ],
    spell_icon_id=138,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auto attacks have a $h% chance to cause a Blood-Caked Strike, which hits for $50463s1% weapon damage plus ${$50463m1/2}.1% for each of your diseases on the target.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


crypt_fever_49631 = spell(
    id=49631,
    name='Crypt Fever',
    school=School.NATURE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=7282),
    ],
    spell_icon_id=264,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your diseases also cause Crypt Fever, which increases disease damage taken by the target by $50509s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


crypt_fever_49632 = spell(
    id=49632,
    name='Crypt Fever',
    school=School.NATURE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=7282),
    ],
    spell_icon_id=264,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your diseases also cause Crypt Fever, which increases disease damage taken by the target by $50510s1%.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


wandering_plague_49654 = spell(
    id=49654,
    name='Wandering Plague',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7288),
    ],
    spell_icon_id=1614,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your diseases damage an enemy, there is a chance equal to your melee critical strike chance that they will cause $s1% additional damage to the target and all enemies within 8 yards.  Ignores any target under the effect of a spell that is cancelled by taking damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1},
)


wandering_plague_49655 = spell(
    id=49655,
    name='Wandering Plague',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7288),
    ],
    spell_icon_id=1614,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your diseases damage an enemy, there is a chance equal to your melee critical strike chance that they will cause $s1% additional damage to the target and all enemies within 8 yards.  Ignores any target under the effect of a spell that is cancelled by taking damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1},
)


endless_winter_49657 = spell(
    id=49657,
    name='Endless Winter',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=137, trigger_spell=55095),
        Effect(type=EffectType.APPLY_AURA, base_points=-201, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=164,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your strength is increased by $s1% and your Mind Freeze no longer costs runic power.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


black_ice_49661 = spell(
    id=49661,
    name='Black Ice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=79, misc_value=48),
    ],
    spell_icon_id=154,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Frost and Shadow damage by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2182250279, 'EffectSpellClassMaskA_2': 447, 'EffectSpellClassMaskB_1': 41975808, 'EffectSpellClassMaskB_2': 1024, 'EffectSpellClassMaskC_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


black_ice_49662 = spell(
    id=49662,
    name='Black Ice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=79, misc_value=48),
    ],
    spell_icon_id=154,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Frost and Shadow damage by $s1%.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 2182250279, 'EffectSpellClassMaskA_2': 447, 'EffectSpellClassMaskB_1': 41975808, 'EffectSpellClassMaskB_2': 1024, 'EffectSpellClassMaskC_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


black_ice_49663 = spell(
    id=49663,
    name='Black Ice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=79, misc_value=48),
    ],
    spell_icon_id=154,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Frost and Shadow damage by $s1%.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 2182250279, 'EffectSpellClassMaskA_2': 447, 'EffectSpellClassMaskB_1': 41975808, 'EffectSpellClassMaskB_2': 1024, 'EffectSpellClassMaskC_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


black_ice_49664 = spell(
    id=49664,
    name='Black Ice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=79, misc_value=48),
    ],
    spell_icon_id=154,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Frost and Shadow damage by $s1%.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 2182250279, 'EffectSpellClassMaskA_2': 447, 'EffectSpellClassMaskB_1': 41975808, 'EffectSpellClassMaskB_2': 1024, 'EffectSpellClassMaskC_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


glacier_rot_49790 = spell(
    id=49790,
    name='Glacier Rot',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=12, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7244),
    ],
    spell_icon_id=196,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Diseased enemies take $s1% more damage from your Icy Touch, Howling Blast and Frost Strike.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1026, 'EffectSpellClassMaskA_2': 7, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


glacier_rot_49791 = spell(
    id=49791,
    name='Glacier Rot',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7244),
    ],
    spell_icon_id=196,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Diseased enemies take $s1% more damage from your Icy Touch, Howling Blast and Frost Strike.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1026, 'EffectSpellClassMaskA_2': 7, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_icy_touch_50031 = spell(
    id=50031,
    name='Improved Icy Touch',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=2721,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Icy Touch does an additional $s1% damage and your Frost Fever reduces melee and ranged attack speed by an additional $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_2': 67108864, 'EffectSpellClassMaskC_2': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RuneCostID': 799, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


death_rune_mastery_50033 = spell(
    id=50033,
    name='Death Rune Mastery',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=226, amplitude=30000),
    ],
    spell_icon_id=2622,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you hit with Death Strike or Obliterate there is a $h% chance that the Frost and Unholy Runes will become Death Runes when they activate.  Death Runes count as a Blood, Frost or Unholy Rune.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassMask_1': 16384, 'SpellClassSet': 15, 'SpellVisualID_1': 10590, 'StartRecoveryTime': 1500},
)


death_rune_mastery_50034 = spell(
    id=50034,
    name='Death Rune Mastery',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=226, amplitude=30000),
    ],
    spell_icon_id=2622,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you hit with Death Strike or Obliterate there is a $h% chance that the Frost and Unholy Runes will become Death Runes when they activate.  Death Runes count as a Blood, Frost or Unholy Rune.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassMask_1': 16384, 'SpellClassSet': 15, 'SpellVisualID_1': 10590, 'StartRecoveryTime': 1500},
)


chilblains_50040 = spell(
    id=50040,
    name='Chilblains',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=109, misc_value=1, trigger_spell=50434),
    ],
    spell_icon_id=143,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Victims of your Frost Fever disease are Chilled, reducing movement speed by $50434s1% for $50434d.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 67108864, 'EffectSpellClassMaskB_1': 1048576, 'EffectSpellClassMaskC_1': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


chilblains_50041 = spell(
    id=50041,
    name='Chilblains',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=109, misc_value=1, trigger_spell=50435),
    ],
    spell_icon_id=143,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Victims of your Frost Fever disease are Chilled, reducing movement speed by $50435s1% for $50435d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 67108864, 'EffectSpellClassMaskB_1': 1048576, 'EffectSpellClassMaskC_1': 1048576, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


chilblains_50043 = spell(
    id=50043,
    name='Chilblains',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=109, misc_value=1, trigger_spell=50436),
    ],
    spell_icon_id=143,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Victims of your Frost Fever disease are Chilled, reducing movement speed by $50436s1% for $50436d.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 67108864, 'EffectSpellClassMaskB_1': 1048576, 'EffectSpellClassMaskC_1': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


chill_of_the_grave_50115 = spell(
    id=50115,
    name='Chill of the Grave',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=231, misc_value=10, trigger_spell=50480),
    ],
    spell_icon_id=976,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Chains of Ice, Howling Blast, Icy Touch and Obliterate generate 5 additional runic power.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87056, 'RangeIndex': 1, 'SpellClassSet': 15},
)


rage_of_rivendare_50117 = spell(
    id=50117,
    name='Rage of Rivendare',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=7293),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=2675,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal 2% more damage to targets infected with Blood Plague.  Also increases your expertise by $s2.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 291774739, 'EffectSpellClassMaskA_2': 771948838, 'EffectSpellClassMaskA_3': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


rage_of_rivendare_50118 = spell(
    id=50118,
    name='Rage of Rivendare',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=112, misc_value=7293),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=2675,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal 4% more damage to targets infected with Blood Plague.  Also increases your expertise by $s2.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 23339283, 'EffectSpellClassMaskA_2': 771948838, 'EffectSpellClassMaskA_3': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


rage_of_rivendare_50119 = spell(
    id=50119,
    name='Rage of Rivendare',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=112, misc_value=7293),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=2675,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal 6% more damage to targets infected with Blood Plague.  Also increases your expertise by $s2.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 23339283, 'EffectSpellClassMaskA_2': 771948838, 'EffectSpellClassMaskA_3': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


rage_of_rivendare_50120 = spell(
    id=50120,
    name='Rage of Rivendare',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=7293),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=2675,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal 8% more damage to targets infected with Blood Plague.  Also increases your expertise by $s2.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 24387859, 'EffectSpellClassMaskA_2': 771948838, 'EffectSpellClassMaskA_3': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


rage_of_rivendare_50121 = spell(
    id=50121,
    name='Rage of Rivendare',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=7293),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=2675,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal 10% more damage to targets infected with Blood Plague.  Also increases your expertise by $s2.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 21242131, 'EffectSpellClassMaskA_2': 771948838, 'EffectSpellClassMaskA_3': 9, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


tundra_stalker_50127 = spell(
    id=50127,
    name='Tundra Stalker',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=112, misc_value=7277),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=100,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal $s1% more damage to targets infected with Frost Fever.  Also increases your expertise by $s2.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 21242899, 'EffectSpellClassMaskA_2': 738394406, 'EffectSpellClassMaskA_3': 9, 'EffectSpellClassMaskC_2': 131074, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_1': 131072, 'SpellClassSet': 15},
)


tundra_stalker_50128 = spell(
    id=50128,
    name='Tundra Stalker',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=112, misc_value=7277),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=100,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal $s1% more damage to targets infected with Frost Fever.  Also increases your expertise by $s2.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 21242899, 'EffectSpellClassMaskA_2': 739442982, 'EffectSpellClassMaskA_3': 8, 'EffectSpellClassMaskC_2': 131074, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 131072, 'SpellClassSet': 15},
)


tundra_stalker_50129 = spell(
    id=50129,
    name='Tundra Stalker',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=112, misc_value=7277),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=100,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal $s1% more damage to targets infected with Frost Fever.  Also increases your expertise by $s2.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 21242899, 'EffectSpellClassMaskA_2': 771952934, 'EffectSpellClassMaskA_3': 9, 'EffectSpellClassMaskC_2': 131074, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 131072, 'SpellClassSet': 15},
)


tundra_stalker_50130 = spell(
    id=50130,
    name='Tundra Stalker',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=112, misc_value=7277),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=100,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal $s1% more damage to targets infected with Frost Fever.  Also increases your expertise by $s2.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 21241875, 'EffectSpellClassMaskA_2': 771948838, 'EffectSpellClassMaskA_3': 9, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 131072, 'SpellClassSet': 15},
)


runic_power_mastery_50147 = spell(
    id=50147,
    name='Runic Power Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=299, implicit_target_a=1, apply_aura=35, misc_value=6),
    ],
    spell_icon_id=1954,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your maximum Runic Power by ${$m1/10}.', 'EffectBasePoints_2': 7, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 1048576, 'EffectSpellClassMaskB_1': 1582080, 'EffectSpellClassMaskB_2': 32, 'EffectSpellClassMaskC_2': 384, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


will_of_the_necropolis_50149 = spell(
    id=50149,
    name='Will of the Necropolis',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=34, implicit_target_a=1),
        Effect(type=EffectType.LEARN_SPELL, base_points=14, implicit_target_a=1, trigger_spell=52285),
    ],
    spell_icon_id=1762,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Damage that would take you below $s1% health or taken while you are at $s1% health is reduced by $52285s1%.', 'EffectBasePoints_3': 4, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 801, 'SpellClassSet': 15, 'SpellLevel': 55},
)


will_of_the_necropolis_50150 = spell(
    id=50150,
    name='Will of the Necropolis',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=34, implicit_target_a=1),
        Effect(type=EffectType.LEARN_SPELL, base_points=14, implicit_target_a=1, trigger_spell=52286),
    ],
    spell_icon_id=1762,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Damage that would take you below $s1% health or taken while you are at $s1% health is reduced by $52286s1%.', 'EffectBasePoints_3': 4, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 802, 'SpellClassSet': 15, 'SpellLevel': 55},
)


acclimation_50151 = spell(
    id=50151,
    name='Acclimation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=10, trigger_spell=1206),
    ],
    spell_icon_id=1930,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you are hit by a spell, you have a $h% chance to boost your resistance to that type of magic for 18 sec.  Stacks up to 3 times.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 3, 'EffectSpellClassMaskB_2': 536870912, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 131072, 'RangeIndex': 1, 'SpellClassSet': 15},
)


acclimation_50152 = spell(
    id=50152,
    name='Acclimation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=10, trigger_spell=1206),
    ],
    spell_icon_id=1930,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you are hit by a spell, you have a $h% chance to boost your resistance to that type of magic for 18 sec.  Stacks up to 3 times.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 3, 'EffectSpellClassMaskB_2': 536870912, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'ProcTypeMask': 131072, 'RangeIndex': 1, 'SpellClassSet': 15},
)


vendetta_50154 = spell(
    id=50154,
    name='Vendetta',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3008,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals you for up to $s1% of your maximum health whenever you kill a target that yields experience or honor.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2, 'RangeIndex': 1, 'RuneCostID': 803, 'SpellClassMask_1': 65536, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellVisualID_1': 7578},
)


guile_of_gorefiend_50187 = spell(
    id=50187,
    name='Guile of Gorefiend',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=1999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=1740,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Blood Strike, Frost Strike, Howling Blast and Obliterate abilities by $s1%, and increases the duration of your Icebound Fortitude by $/1000;s2 secs.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EffectSpellClassMaskA_2': 131078, 'EffectSpellClassMaskB_1': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


guile_of_gorefiend_50190 = spell(
    id=50190,
    name='Guile of Gorefiend',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=3999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=1740,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Blood Strike, Frost Strike, Howling Blast and Obliterate abilities by $s1%, and increases the duration of your Icebound Fortitude by $/1000;s2 secs.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EffectSpellClassMaskA_2': 131078, 'EffectSpellClassMaskB_1': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


guile_of_gorefiend_50191 = spell(
    id=50191,
    name='Guile of Gorefiend',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=44, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=5999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=1740,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Blood Strike, Frost Strike, Howling Blast and Obliterate abilities by $s1%, and increases the duration of your Icebound Fortitude by $/1000;s2 secs.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EffectSpellClassMaskA_2': 131078, 'EffectSpellClassMaskB_1': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_blood_presence_50365 = spell(
    id=50365,
    name='Improved Blood Presence',
    school=School.NORMAL,
    attributes=151322688,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=2636,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147483648, 'AttributesEx3': 65536, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Frost Presence or Unholy Presence, you retain $s1% healing from Blood Presence, and healing done to you is increased by $s2% in Blood Presence.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 332116, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_blood_presence_50371 = spell(
    id=50371,
    name='Improved Blood Presence',
    school=School.NORMAL,
    attributes=151322688,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=2636,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147483648, 'AttributesEx3': 65536, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Frost Presence or Unholy Presence, you retain $s1% healing from Blood Presence, and healing done to you is increased by $s2% in Blood Presence.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 332116, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_frost_presence_50384 = spell(
    id=50384,
    name='Improved Frost Presence',
    school=School.NORMAL,
    attributes=151322688,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=2632,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147483648, 'AttributesEx3': 65536, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Blood Presence or Unholy Presence, you retain $s1% stamina from Frost Presence, and damage done to you is decreased by an additional $s2% in Frost Presence.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 32768, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_frost_presence_50385 = spell(
    id=50385,
    name='Improved Frost Presence',
    school=School.NORMAL,
    attributes=151322688,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=2632,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147483648, 'AttributesEx3': 65536, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Blood Presence or Unholy Presence, you retain $s1% stamina from Frost Presence, and damage done to you is decreased by an additional $s2% in Frost Presence.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 32768, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_unholy_presence_50391 = spell(
    id=50391,
    name='Improved Unholy Presence',
    school=School.NORMAL,
    attributes=151322688,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2633,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147483648, 'AttributesEx3': 65536, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Blood Presence or Frost Presence, you retain $s1% increased movement speed from Unholy Presence, and your runes finish their cooldowns $s2% faster in Unholy Presence.', 'EffectBasePoints_2': 4, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_unholy_presence_50392 = spell(
    id=50392,
    name='Improved Unholy Presence',
    school=School.NORMAL,
    attributes=151322688,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2633,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147483648, 'AttributesEx3': 65536, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Blood Presence or Frost Presence, you retain $s1% increased movement speed from Unholy Presence, and your runes finish their cooldowns $s2% faster in Unholy Presence.', 'EffectBasePoints_2': 9, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


icy_talons_50880 = spell(
    id=50880,
    name='Icy Talons',
    school=School.FROST,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=231, trigger_spell=50882),
        Effect(type=EffectType.DUMMY, base_points=3),
    ],
    spell_icon_id=3785,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You leech heat from victims of your Frost Fever, so that when their melee attack speed is reduced, yours increases by $s2% for the next 20 sec.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 4112, 'RuneCostID': 846, 'SpellClassMask_1': 2, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


icy_talons_50884 = spell(
    id=50884,
    name='Icy Talons',
    school=School.FROST,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=231, trigger_spell=58575),
        Effect(type=EffectType.DUMMY, base_points=7),
    ],
    spell_icon_id=3785,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You leech heat from victims of your Frost Fever, so that when their melee attack speed is reduced, yours increases by $s2% for the next 20 sec.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 4112, 'RuneCostID': 847, 'SpellClassMask_1': 2, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


icy_talons_50885 = spell(
    id=50885,
    name='Icy Talons',
    school=School.FROST,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=231, trigger_spell=58576),
        Effect(type=EffectType.DUMMY, base_points=11),
    ],
    spell_icon_id=3785,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You leech heat from victims of your Frost Fever, so that when their melee attack speed is reduced, yours increases by $s2% for the next 20 sec.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 4112, 'RuneCostID': 848, 'SpellClassMask_1': 2, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


icy_talons_50886 = spell(
    id=50886,
    name='Icy Talons',
    school=School.FROST,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=231, trigger_spell=58577),
        Effect(type=EffectType.DUMMY, base_points=15),
    ],
    spell_icon_id=3785,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You leech heat from victims of your Frost Fever, so that when their melee attack speed is reduced, yours increases by $s2% for the next 20 sec.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 4112, 'RuneCostID': 849, 'SpellClassMask_1': 2, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


icy_talons_50887 = spell(
    id=50887,
    name='Icy Talons',
    school=School.FROST,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=231, trigger_spell=58578),
        Effect(type=EffectType.DUMMY, base_points=19),
    ],
    spell_icon_id=3785,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You leech heat from victims of your Frost Fever, so that when their melee attack speed is reduced, yours increases by $s2% for the next 20 sec.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 4112, 'RuneCostID': 850, 'SpellClassMask_1': 2, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


ebon_plaguebringer_51099 = spell(
    id=51099,
    name='Ebon Plaguebringer',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=112, misc_value=7282),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=52, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=57),
    ],
    spell_icon_id=1766,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Crypt Fever morphs into Ebon Plague, which increases magic damage taken by 4% in addition to increasing disease damage taken.  Improves your critical strike chance with weapons and spells by $51099s2% at all times.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


frigid_dreadplate_51108 = spell(
    id=51108,
    name='Frigid Dreadplate',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=184, misc_value=1),
    ],
    spell_icon_id=2738,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the chance melee attacks will hit you by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 40, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellPriority': 50},
)


frigid_dreadplate_51109 = spell(
    id=51109,
    name='Frigid Dreadplate',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=184, misc_value=1),
    ],
    spell_icon_id=2738,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the chance melee attacks will hit you by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 40, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellPriority': 50},
)


killing_machine_51123 = spell(
    id=51123,
    name='Killing Machine',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=51124),
    ],
    spell_icon_id=2702,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee attacks have a chance to make your next Icy Touch, Howling Blast or Frost Strike a critical strike.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


killing_machine_51127 = spell(
    id=51127,
    name='Killing Machine',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=51124),
    ],
    spell_icon_id=2702,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee attacks have a chance to make your next Icy Touch, Howling Blast or Frost Strike a critical strike.  Effect occurs more often than Killing Machine (Rank 1).', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


killing_machine_51128 = spell(
    id=51128,
    name='Killing Machine',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=51124),
    ],
    spell_icon_id=2702,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee attacks have a chance to make your next Icy Touch, Howling Blast or Frost Strike a critical strike.  Effect occurs more often than Killing Machine (Rank 2).', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


killing_machine_51129 = spell(
    id=51129,
    name='Killing Machine',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=51124),
    ],
    spell_icon_id=2702,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee attacks have a chance to make your next Icy Touch, Howling Blast or Frost Strike a critical strike.  Effect occurs more often than Killing Machine (Rank 3).', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


killing_machine_51130 = spell(
    id=51130,
    name='Killing Machine',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=51124),
    ],
    spell_icon_id=2702,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee attacks have a chance to make your next Icy Touch, Howling Blast or Frost Strike a critical strike.  Effect occurs more often than Killing Machine (Rank 4).', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


ebon_plaguebringer_51160 = spell(
    id=51160,
    name='Ebon Plaguebringer',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=7282),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=52),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=57),
    ],
    spell_icon_id=1766,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Crypt Fever morphs into Ebon Plague, which increases magic damage taken by 9% in addition to increasing disease damage taken.  Improves your critical strike chance with weapons and spells by $51160s2% at all times.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


ebon_plaguebringer_51161 = spell(
    id=51161,
    name='Ebon Plaguebringer',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=7282),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=52),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=57),
    ],
    spell_icon_id=1766,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Crypt Fever morphs into Ebon Plague, which increases magic damage taken by 13% in addition to increasing disease damage taken.  Improves your critical strike chance with weapons and spells by $51161s2% at all times.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


on_a_pale_horse_51267 = spell(
    id=51267,
    name='On a Pale Horse',
    school=School.NORMAL,
    attributes=16777616,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=51986),
        Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=51970),
    ],
    spell_icon_id=3005,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You become as hard to stop as death itself.  The duration of all Stun and Fear effects used against you is reduced by 20%, and your mounted speed is increased by 20%.  This does not stack with other movement speed increasing effects.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskB_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_icy_touch_51456 = spell(
    id=51456,
    name='Improved Icy Touch',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=2721,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Icy Touch does an additional $s1% damage and your Frost Fever reduces melee and ranged attack speed by an additional $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_2': 67108864, 'EffectSpellClassMaskC_2': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RuneCostID': 881, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


necrosis_51459 = spell(
    id=51459,
    name='Necrosis',
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2709,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auto attacks deal an additional $s1% Shadow damage.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


necrosis_51462 = spell(
    id=51462,
    name='Necrosis',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2709,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auto attacks deal an additional $s1% Shadow damage.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


necrosis_51463 = spell(
    id=51463,
    name='Necrosis',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2709,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auto attacks deal an additional $s1% Shadow damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


necrosis_51464 = spell(
    id=51464,
    name='Necrosis',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2709,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auto attacks deal an additional $s1% Shadow damage.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


necrosis_51465 = spell(
    id=51465,
    name='Necrosis',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2709,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auto attacks deal an additional $s1% Shadow damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


annihilation_51468 = spell(
    id=51468,
    name='Annihilation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2710,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your melee special abilities by $s2%.  In addition, there is a $s1% chance that your Obliterate will do its damage without consuming diseases.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8454144, 'EffectSpellClassMaskB_1': 20971793, 'EffectSpellClassMaskB_2': 671219716, 'EffectSpellClassMaskC_1': 4194305, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


annihilation_51472 = spell(
    id=51472,
    name='Annihilation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2710,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your melee special abilities by $s2%.  In addition, there is a $s1% chance that your Obliterate will do its damage without consuming diseases.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8454144, 'EffectSpellClassMaskB_1': 20971793, 'EffectSpellClassMaskB_2': 671219716, 'EffectSpellClassMaskC_1': 4194305, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


annihilation_51473 = spell(
    id=51473,
    name='Annihilation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2710,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your melee special abilities by $s2%.  In addition, there is a $s1% chance that your Obliterate will do its damage without consuming diseases.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8454144, 'EffectSpellClassMaskB_1': 20971793, 'EffectSpellClassMaskB_2': 671219716, 'EffectSpellClassMaskC_1': 4194305, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


vicious_strikes_51745 = spell(
    id=51745,
    name='Vicious Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2623,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance by $s2% and critical strike damage bonus by $s1% of your Plague Strike and Scourge Strike.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskA_2': 134217728, 'EffectSpellClassMaskA_3': 128, 'EffectSpellClassMaskB_1': 17, 'EffectSpellClassMaskB_2': 134217728, 'EffectSpellClassMaskB_3': 128, 'EffectSpellClassMaskC_1': 4194305, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


vicious_strikes_51746 = spell(
    id=51746,
    name='Vicious Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2623,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance by $s2% and critical strike damage bonus by $s1% of your Plague Strike and Scourge Strike.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskA_2': 134217728, 'EffectSpellClassMaskA_3': 128, 'EffectSpellClassMaskB_1': 17, 'EffectSpellClassMaskB_2': 134217728, 'EffectSpellClassMaskB_3': 128, 'EffectSpellClassMaskC_1': 4194305, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


master_of_ghouls_52143 = spell(
    id=52143,
    name='Master of Ghouls',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=10,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-60001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=221,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown on Raise Dead by ${$m1/-1000} sec, and the Ghoul summoned by your Raise Dead spell is considered a pet under your control.  Unlike normal Death Knight Ghouls, your pet does not have a limited duration.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_2': 32, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


abomination_s_might_53137 = spell(
    id=53137,
    name="Abomination's Might",
    school=School.NORMAL,
    attributes=80,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=65, base_points=4, implicit_target_a=1, apply_aura=166, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=137),
        Effect(type=65, base_points=4, implicit_target_a=1, apply_aura=167, radius_yards=100.0),
    ],
    spell_icon_id=2729,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases attack power by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the attack power by $53137s1% of party and raid members within $53137a1 yards.  Also increases your total Strength by $53137s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 15},
)


abomination_s_might_53138 = spell(
    id=53138,
    name="Abomination's Might",
    school=School.NORMAL,
    attributes=80,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=65, base_points=9, implicit_target_a=1, apply_aura=166, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137),
        Effect(type=65, base_points=9, implicit_target_a=1, apply_aura=167, radius_yards=100.0),
    ],
    spell_icon_id=2729,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases attack power by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the attack power by $53138s1% of party and raid members within $53138a1 yards.  Also increases your total Strength by $53138s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 15},
)


blood_of_the_north_54637 = spell(
    id=54637,
    name='Blood of the North',
    school=School.SHADOW,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=226, amplitude=30000),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=3041,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Blood Strike and Frost Strike damage by $s2%.  In addition, whenever you hit with Blood Strike or Pestilence there is a $h% chance that the Blood Rune will become a Death Rune when it activates.  Death Runes count as a Blood, Frost or Unholy Rune.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskB_1': 4194304, 'EffectSpellClassMaskB_2': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87312, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellVisualID_1': 10590},
)


blood_of_the_north_54638 = spell(
    id=54638,
    name='Blood of the North',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=226, amplitude=30000),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=3041,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Blood Strike and Frost Strike damage by $s2%.  In addition, whenever you hit with Blood Strike or Pestilence there is a $h% chance that the Blood Rune will become a Death Rune when it activates.  Death Runes count as a Blood, Frost or Unholy Rune.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskB_1': 4194304, 'EffectSpellClassMaskB_2': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 60, 'ProcTypeMask': 87312, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellVisualID_1': 10590},
)


blood_of_the_north_54639 = spell(
    id=54639,
    name='Blood of the North',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=226, amplitude=30000),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=3041,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Blood Strike and Frost Strike damage by $s2%.  In addition, whenever you hit with Blood Strike or Pestilence there is a $h% chance that the Blood Rune will become a Death Rune when it activates.  Death Runes count as a Blood, Frost or Unholy Rune.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskB_1': 4194304, 'EffectSpellClassMaskB_2': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'ProcTypeMask': 87312, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellVisualID_1': 10590},
)


icy_reach_55061 = spell(
    id=55061,
    name='Icy Reach',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=5),
    ],
    spell_icon_id=36,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your Icy Touch,  Chains of Ice and Howling Blast by $s1 yards.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 6, 'EffectSpellClassMaskA_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


icy_reach_55062 = spell(
    id=55062,
    name='Icy Reach',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=5),
    ],
    spell_icon_id=36,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your Icy Touch, Chains of Ice and Howling Blast by $s1 yards.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 6, 'EffectSpellClassMaskA_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


vendetta_55136 = spell(
    id=55136,
    name='Vendetta',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3008,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals you for up to $s1% of your maximum health whenever you kill a target that yields experience or honor.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2, 'RangeIndex': 1, 'RuneCostID': 1147, 'SpellClassMask_1': 65536, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellVisualID_1': 7578},
)


blade_barrier_55225 = spell(
    id=55225,
    name='Blade Barrier',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64858),
        Effect(type=EffectType.DUMMY, base_points=5, implicit_target_a=6),
    ],
    spell_icon_id=85,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Blood Runes are on cooldown, you gain the Blade Barrier effect, which decreases damage taken by $64858s1% for the next $64858d.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 14684919, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 6, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'RuneCostID': 1164, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


blade_barrier_55226 = spell(
    id=55226,
    name='Blade Barrier',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64859),
        Effect(type=EffectType.DUMMY, base_points=5, implicit_target_a=6),
    ],
    spell_icon_id=85,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Blood Runes are on cooldown, you gain the Blade Barrier effect, which decreases damage taken by $64859s1% for the next $64859d.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 14684919, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 6, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'RuneCostID': 1165, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


outbreak_55236 = spell(
    id=55236,
    name='Outbreak',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=12, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=97,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of Plague Strike by $s1% and Scourge Strike by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_2': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 1166, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


outbreak_55237 = spell(
    id=55237,
    name='Outbreak',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=97,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of Plague Strike by $s1% and Scourge Strike by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_2': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 1167, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


improved_icy_talons_55610 = spell(
    id=55610,
    name='Improved Icy Talons',
    school=School.FROST,
    attributes=80,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=65, base_points=19, implicit_target_a=1, apply_aura=138, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=192),
    ],
    spell_icon_id=3785,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases melee haste by $s1%.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the melee haste of all party and raid members within $55610a1 yds by $55610s1% and your haste by an additional $55610s2%.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'RuneCostID': 1205, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


night_of_the_dead_55620 = spell(
    id=55620,
    name='Night of the Dead',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-45001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-120001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2718,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown on Raise Dead by ${$m1/-1000} sec and the cooldown on Army of the Dead by ${$m2/-60000} min.  Also reduces the damage your pet takes from creature area of effect attacks by $s3%.', 'EffectBasePoints_3': 44, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


night_of_the_dead_55623 = spell(
    id=55623,
    name='Night of the Dead',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-90001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-240001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2718,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown on Raise Dead by ${$m1/-1000} sec and the cooldown on Army of the Dead by ${$m2/-60000} min.  Also reduces the damage your pet takes from creature area of effect attacks by $s3%.', 'EffectBasePoints_3': 89, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


desecration_55666 = spell(
    id=55666,
    name='Desecration',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=55741),
    ],
    spell_icon_id=2296,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Plague Strikes and Scourge Strikes cause the Desecrated Ground effect.  Targets in the area are slowed by $55741s1% by the grasping arms of the dead while standing on the unholy ground.  Lasts $55741d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 15, 'SpellPriority': 50, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


desecration_55667 = spell(
    id=55667,
    name='Desecration',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=68766),
    ],
    spell_icon_id=2296,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Plague Strikes and Scourge Strikes cause the Desecrated Ground effect.  Targets in the area are slowed by $68766s1% by the grasping arms of the dead while standing on the unholy ground.  Lasts $68766d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 15, 'SpellPriority': 50, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rime_56822 = spell(
    id=56822,
    name='Rime',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=59052),
    ],
    spell_icon_id=56,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Icy Touch and Obliterate by $s1% and casting Obliterate has a $h% chance to reset the cooldown on Howling Blast and cause your next Howling Blast to consume no runes.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskA_2': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 69904, 'RangeIndex': 1, 'SpellClassSet': 15},
)


reaping_56834 = spell(
    id=56834,
    name='Reaping',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=226, amplitude=30000),
    ],
    spell_icon_id=22,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you hit with Blood Strike or Pestilence there is a $h% chance that the Blood Rune becomes a Death Rune when it activates.  Death Runes count as a Blood, Frost or Unholy Rune.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 69648, 'RangeIndex': 1, 'SpellClassSet': 15},
)


reaping_56835 = spell(
    id=56835,
    name='Reaping',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=226, amplitude=30000),
    ],
    spell_icon_id=22,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you hit with Blood Strike or Pestilence there is a $h% chance that the Blood Rune becomes a Death Rune when it activates.  Death Runes count as a Blood, Frost or Unholy Rune.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69648, 'RangeIndex': 1, 'SpellClassSet': 15},
)


rime_59057 = spell(
    id=59057,
    name='Rime',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=59052),
    ],
    spell_icon_id=56,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Icy Touch and Obliterate by $s1% and casting Obliterate has a $h% chance to reset the cooldown on Howling Blast and cause your next Howling Blast to consume no runes.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskA_2': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 15, 'ProcTypeMask': 69904, 'RangeIndex': 1, 'SpellClassSet': 15},
)


blood_gorged_61154 = spell(
    id=61154,
    name='Blood Gorged',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, base_points=1, implicit_target_a=1, trigger_spell=blood_gorged_50096.id),
        None,
        Effect(type=EffectType.LEARN_SPELL, base_points=1, implicit_target_a=1, trigger_spell=blood_gorged_61274.id),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AttributesEx4': 32768, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When you are above 75% health, you deal $s1% more damage.  In addition, your attacks ignore up to $s3% of your opponent's armor at all times.", 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 20971521, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 15},
)


blood_gorged_61155 = spell(
    id=61155,
    name='Blood Gorged',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, base_points=3, implicit_target_a=1, trigger_spell=50108),
        None,
        Effect(type=EffectType.LEARN_SPELL, base_points=3, implicit_target_a=1, trigger_spell=61275),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AttributesEx4': 32768, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When you are above 75% health, you deal $s1% more damage.  In addition, your attacks ignore up to $s3% of your opponent's armor at all times.", 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 20971521, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


blood_gorged_61156 = spell(
    id=61156,
    name='Blood Gorged',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, base_points=5, implicit_target_a=1, trigger_spell=50109),
        None,
        Effect(type=EffectType.LEARN_SPELL, base_points=5, implicit_target_a=1, trigger_spell=61276),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AttributesEx4': 32768, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When you are above 75% health, you deal $s1% more damage.  In addition, your attacks ignore up to $s3% of your opponent's armor at all times.", 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 20971521, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


blood_gorged_61157 = spell(
    id=61157,
    name='Blood Gorged',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, base_points=7, implicit_target_a=1, trigger_spell=50110),
        None,
        Effect(type=EffectType.LEARN_SPELL, base_points=7, implicit_target_a=1, trigger_spell=61277),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AttributesEx4': 32768, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When you are above 75% health, you deal $s1% more damage.  In addition, your attacks ignore up to $s3% of your opponent's armor at all times.", 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 20971521, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


blood_gorged_61158 = spell(
    id=61158,
    name='Blood Gorged',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, base_points=9, implicit_target_a=1, trigger_spell=50111),
        None,
        Effect(type=EffectType.LEARN_SPELL, base_points=9, implicit_target_a=1, trigger_spell=61278),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AttributesEx4': 32768, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When you are above 75% health, you deal $s1% more damage.  In addition, your attacks ignore up to $s3% of your opponent's armor at all times.", 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 20971521, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_death_strike_62905 = spell(
    id=62905,
    name='Improved Death Strike',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2751,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Death Strike by $s1%, increases its critical strike chance by $s2%, and increases the healing granted by $s3%.', 'EffectBasePoints_3': 24, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskB_1': 16, 'EffectSpellClassMaskC_1': 16, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_death_strike_62908 = spell(
    id=62908,
    name='Improved Death Strike',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2751,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Death Strike by $s1%, increases its critical strike chance by $s2%, and increases the healing granted by $s3%.', 'EffectBasePoints_3': 49, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskB_1': 16, 'EffectSpellClassMaskC_1': 16, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


threat_of_thassarian_65661 = spell(
    id=65661,
    name='Threat of Thassarian',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2023,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When dual-wielding, your Death Strikes, Obliterates, Plague Strikes, Rune Strikes, Blood Strikes and Frost Strikes have a $s1% chance to also deal damage with your offhand weapon.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 41105, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 15},
)


threat_of_thassarian_66191 = spell(
    id=66191,
    name='Threat of Thassarian',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2023,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When dual-wielding, your Death Strikes, Obliterates, Plague Strikes, Rune Strikes, Blood Strikes and Frost Strikes have a $s1% chance to also deal damage with your offhand weapon.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 41105, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 15},
)


threat_of_thassarian_66192 = spell(
    id=66192,
    name='Threat of Thassarian',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.DUMMY, die_sides=0),
    ],
    spell_icon_id=2023,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When dual-wielding, your Death Strikes, Obliterates, Plague Strikes, Rune Strikes, Blood Strikes and Frost Strikes have a $s1% chance to also deal damage with your offhand weapon.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 41105, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 15},
)


desolation_66799 = spell(
    id=66799,
    name='Desolation',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=63583),
    ],
    spell_icon_id=95,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Blood Strikes cause you to deal $63583s1% additional damage with all attacks for the next $63583d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 15, 'SpellPriority': 50, 'StartRecoveryCategory': 133},
)


desolation_66814 = spell(
    id=66814,
    name='Desolation',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=66800),
    ],
    spell_icon_id=95,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Blood Strikes cause you to deal $66800s1% additional damage with all attacks for the next $66800d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 15, 'SpellPriority': 50, 'StartRecoveryCategory': 133},
)


desolation_66815 = spell(
    id=66815,
    name='Desolation',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=66801),
    ],
    spell_icon_id=95,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Blood Strikes cause you to deal $66801s1% additional damage with all attacks for the next $66801d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 15, 'SpellPriority': 50, 'StartRecoveryCategory': 133},
)


desolation_66816 = spell(
    id=66816,
    name='Desolation',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=66802),
    ],
    spell_icon_id=95,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Blood Strikes cause you to deal $66802s1% additional damage with all attacks for the next $66802d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 15, 'SpellPriority': 50, 'StartRecoveryCategory': 133},
)


desolation_66817 = spell(
    id=66817,
    name='Desolation',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=66803),
    ],
    spell_icon_id=95,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Blood Strikes cause you to deal $66803s1% additional damage with all attacks for the next $66803d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 15, 'SpellPriority': 50, 'StartRecoveryCategory': 133},
)
