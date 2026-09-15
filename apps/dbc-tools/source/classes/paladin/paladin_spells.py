"""
Paladin - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/paladin.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .paladin_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, School
from lib.dsl.registry import spell


divine_protection_498 = spell(
    id=498,
    name='Divine Protection',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=29,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=73,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 2097152, 'AttributesEx5': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced by $s2%.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 6, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s2% for $d.  Once protected, the target cannot be targeted by Divine Shield, Divine Protection, or Hand of Protection again for $25771d.  Cannot be used within $61987d of using Avenging Wrath.', 'EffectBasePoints_1': -101, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_1': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'ExcludeCasterAuraSpell': 61988, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 4194304, 'SpellClassMask_3': 256, 'SpellClassSet': 10, 'SpellLevel': 6, 'SpellVisualID_1': 11817},
)


lay_on_hands_633 = spell(
    id=633,
    name='Lay on Hands',
    school=School.HOLY,
    attributes=327680,
    category=56,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1200000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    effects=[
        Effect(type=67, base_points=-1, implicit_target_a=21),
        Effect(type=EffectType.ENERGIZE, base_points=249, implicit_target_a=21),
    ],
    spell_icon_id=79,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Heals a friendly target for an amount equal to the Paladin's maximum health.  If used on self, the Paladin cannot be targeted by Divine Shield, Divine Protection, Hand of Protection, or self-targeted Lay on Hands again for $25771d.  Also cannot be used on self within $61987d of using Avenging Wrath.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 32768, 'SpellClassSet': 10, 'SpellLevel': 10, 'SpellVisualID_1': 132, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


holy_light_635 = spell(
    id=635,
    name='Holy Light',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=29,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=49, points_per_level=61.24050632911393, die_sides=11, implicit_target_a=21),
    ],
    spell_icon_id=70,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 13 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 20, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for $s1.', 'EffectBonusMultiplier_1': 1.6790000200271606, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 10, 'SpellLevel': 1, 'SpellVisualID_1': 2936, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hammer_of_justice_853 = spell(
    id=853,
    name='Hammer of Justice',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.STUN,
    attributes=327680,
    category=32,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=10.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=302,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1->covers-60 (anchor rank 4 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 262144, 'AttributesEx6': 8388608, 'AttributesEx7': 2048, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Stuns the target for $d and interrupts non-player spellcasting for $32747d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2048, 'SpellClassSet': 10, 'SpellLevel': 8, 'SpellVisualID_1': 322, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


exorcism_879 = spell(
    id=879,
    name='Exorcism',
    school=School.HOLY,
    attributes=327680,
    category=19,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=15000,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=95, points_per_level=15.616666666666667, die_sides=15, implicit_target_a=6),
    ],
    spell_icon_id=292,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AttributesEx6': 33554432, 'AttributesEx7': 32768, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes ${$m1+0.15*$SPH+0.15*$AP} to ${$M1+0.15*$SPH+0.15*$AP} Holy damage to an enemy target.  If the target is Undead or Demon, it will always critically hit.', 'EffectBonusMultiplier_1': 0.15000000596046448, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 2, 'SpellClassSet': 10, 'SpellLevel': 20, 'SpellVisualID_1': 324, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hand_of_protection_1022 = spell(
    id=1022,
    name='Hand of Protection',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=29,
    attributes=327680,
    category=20,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=300000,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=57, apply_aura=39, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=57, apply_aura=AuraType.MOD_PACIFY),
    ],
    spell_icon_id=303,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 32768, 'AttributesEx2': 2097152, 'AttributesEx5': 4, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to physical attacks.  Cannot attack or use physical abilities.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A targeted party or raid member is protected from all physical attacks for $d, but during that time they cannot attack or use physical abilities.  Players may only have one Hand on them per Paladin at any one time.  Once protected, the target cannot be targeted by Divine Shield, Divine Protection, or Hand of Protection again for $25771d.  Cannot be targeted on players who have used Avenging Wrath within the last $61987d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 61988, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 128, 'SpellClassSet': 10, 'SpellLevel': 10, 'SpellVisualID_1': 302, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hand_of_salvation_1038 = spell(
    id=1038,
    name='Hand of Salvation',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=329728,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=57, apply_aura=227, amplitude=1000, misc_value=127, trigger_spell=53055),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=57, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=305,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces total threat by $53055s1% each second.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Hand on the party or raid member, reducing their total threat by $53055s1% every $t1 sec. for $d.  Players may only have one Hand on them per Paladin at any one time.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 256, 'SpellClassSet': 10, 'SpellLevel': 26, 'SpellVisualID_1': 300, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hand_of_freedom_1044 = spell(
    id=1044,
    name='Hand of Freedom',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=25000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=11),
    ],
    spell_icon_id=80,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 163840, 'AttributesEx5': 8, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to movement impairing effects.', 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Hand on the friendly target, granting immunity to movement impairing effects for $d.  Players may only have one Hand on them per Paladin at any one time.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 16, 'SpellClassSet': 10, 'SpellLevel': 18, 'SpellVisualID_1': 4050, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


purify_1152 = spell(
    id=1152,
    name='Purify',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=3),
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=4),
    ],
    spell_icon_id=300,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Purifies the friendly target, removing $s1 disease effect and $s2 poison effect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 4096, 'SpellClassSet': 10, 'SpellLevel': 8, 'SpellVisualID_1': 312, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


holy_wrath_2812 = spell(
    id=2812,
    name='Holy Wrath',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=35,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=20,
    range_yards=0.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=398, points_per_level=21.966666666666665, die_sides=73, implicit_target_a=22, implicit_target_b=15, radius_yards=10.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.STUN, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_STUN, radius_yards=10.0),
    ],
    spell_icon_id=158,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Sends bolts of holy power in all directions, causing ${$m1+0.07*$SPH+0.07*$AP} to ${$M1+0.07*$SPH+0.07*$AP} Holy damage and stunning all Undead and Demon targets within $a1 yds for $d.', 'EffectBonusMultiplier_1': 0.07000000029802322, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'Speed': 20.0, 'SpellClassMask_2': 2097152, 'SpellClassSet': 10, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 126, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 36},
)


cleanse_4987 = spell(
    id=4987,
    name='Cleanse',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=4),
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=3),
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=1),
    ],
    spell_icon_id=321,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 42, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Cleanses a friendly target, removing $s1 poison effect, $s2 disease effect, and $s3 magic effect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 4096, 'SpellClassSet': 10, 'SpellLevel': 42, 'SpellVisualID_1': 337, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hand_of_sacrifice_6940 = spell(
    id=6940,
    name='Hand of Sacrifice',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=1186,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=57, apply_aura=81, misc_value=127),
    ],
    spell_icon_id=504,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 655360, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Transfers $s1% damage taken to the paladin.', 'BaseLevel': 46, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Hand on the party or raid member, transfering $s1% damage taken to the caster.  Lasts $d or until the caster has transfered $s2% of their maximum health.  Players may only have one Hand on them per Paladin at any one time.', 'EffectBasePoints_2': 99, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 699048, 'SpellClassMask_1': 8192, 'SpellClassSet': 10, 'SpellLevel': 46, 'SpellVisualID_1': 299, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blessing_of_might_19740 = spell(
    id=19740,
    name='Blessing of Might',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, points_per_level=6.973684210526316, implicit_target_a=21, apply_aura=AuraType.MOD_ATTACK_POWER),
        Effect(type=EffectType.APPLY_AURA, base_points=19, points_per_level=6.973684210526316, implicit_target_a=21, apply_aura=124),
    ],
    spell_icon_id=298,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases attack power by $s1.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Blessing on the friendly target, increasing attack power by $s1 for $d.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2, 'SpellClassSet': 10, 'SpellLevel': 4, 'SpellVisualID_1': 9179, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blessing_of_wisdom_19742 = spell(
    id=19742,
    name='Blessing of Wisdom',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=1.2424242424242424, implicit_target_a=21, apply_aura=85),
    ],
    spell_icon_id=306,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 14); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx3': 1, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Restores $s1 mana every 5 seconds.', 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Blessing on the friendly target, restoring $s1 mana every 5 seconds for $d.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 65536, 'SpellClassSet': 10, 'SpellLevel': 14, 'SpellVisualID_1': 5400, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


flash_of_light_19750 = spell(
    id=19750,
    name='Flash of Light',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=80, points_per_level=11.798333334922791, die_sides=13, implicit_target_a=21),
    ],
    spell_icon_id=242,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 33554432, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for $s1.', 'EffectBonusMultiplier_1': 1.0089999437332153, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 10, 'SpellLevel': 20, 'SpellVisualID_1': 6623, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


divine_intervention_19752 = spell(
    id=19752,
    name='Divine Intervention',
    school=School.HOLY,
    attributes=537198592,
    cast_time_ms=0,
    cooldown_ms=600000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    effects=[
        Effect(type=79, base_points=-1, implicit_target_a=57),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=57, trigger_spell=19753),
        Effect(type=1, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=58,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 655360, 'AttributesEx2': 8, 'AttributesEx3': 256, 'AttributesEx4': 65792, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Complete immunity but unable to move.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "The paladin sacrifices $ghimself:herself; to remove the targeted party member from harm's way.  Enemies will stop attacking the protected party member, who will be immune to all harmful attacks but will not be able to take any action for $19753d.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ReagentCount_1': 1, 'Reagent_1': 17033, 'SpellClassSet': 10, 'SpellLevel': 30, 'SpellVisualID_1': 5402, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


seal_of_light_20165 = spell(
    id=20165,
    name='Seal of Light',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=0.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=20167),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=299,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attacks have a chance to heal you.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Fills the Paladin with divine light for $d, giving each melee attack a chance to heal the Paladin for ${0.15*$AP+0.15*$SPH}.  Only one Seal can be active on the Paladin at any one time.\r\n\r\nUnleashing this Seal's energy will deal ${1+0.25*$SPH+0.16*$AP} Holy damage to an enemy.", 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskB_1': 3221225472, 'EffectSpellClassMaskB_2': 16842752, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassMask_2': 33554432, 'SpellClassSet': 10, 'SpellLevel': 30, 'SpellVisualID_1': 8073, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


seal_of_wisdom_20166 = spell(
    id=20166,
    name='Seal of Wisdom',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=0.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=20168),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=206,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attacks have a chance to restore mana.', 'BaseLevel': 38, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Fills the Paladin with divine wisdom for $20166d, giving each melee attack a chance to restore $20168s1% of the paladin's maximum mana.  Only one Seal can be active on the Paladin at any one time.\r\n\r\nUnleashing this Seal's energy will deal ${1+0.25*$SPH+0.16*$AP} Holy damage to an enemy.", 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskB_1': 3223322624, 'EffectSpellClassMaskB_2': 16777216, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassMask_2': 67108864, 'SpellClassSet': 10, 'SpellLevel': 38, 'SpellVisualID_1': 7987, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blessing_of_kings_20217 = spell(
    id=20217,
    name='Blessing of Kings',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=21, apply_aura=137, misc_value=-1),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=166),
    ],
    spell_icon_id=332,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases stats by $s1%.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Blessing on the friendly target, increasing total stats by $s1% for $d.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 16777216, 'SpellClassSet': 10, 'SpellLevel': 20, 'SpellVisualID_1': 9187, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


charger_23214 = spell(
    id=23214,
    name='Charger',
    school=School.HOLY,
    mechanic=21,
    attributes=269844480,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=78, misc_value=14565),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=32),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=1716,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 536870912, 'AttributesEx6': 131072, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases speed by $s2%.', 'BaseLevel': 40, 'CastingTimeIndex': 16, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Charger, which serves as a mount.  This is a very fast mount.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Summon', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 268435456, 'SpellClassSet': 10, 'SpellLevel': 40, 'SpellVisualID_1': 3339},
)


hammer_of_wrath_24275 = spell(
    id=24275,
    name='Hammer of Wrath',
    school=School.HOLY,
    attributes=327680,
    category=1131,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=350, points_per_level=21.88888888888889, die_sides=37, implicit_target_a=6),
    ],
    spell_icon_id=42,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 44); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx4': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 44, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Hurls a hammer that strikes an enemy for ${$m1+0.15*$SPH+0.15*$AP} to ${$M1+0.15*$SPH+0.15*$AP} Holy damage.  Only usable on enemies that have 20% or less health.', 'EffectBonusMultiplier_1': 0.15000000596046448, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 50.0, 'SpellClassMask_2': 128, 'SpellClassSet': 10, 'SpellLevel': 44, 'SpellVisualID_1': 7250, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetAuraState': 2},
)


blessing_of_wisdom_25290 = spell(
    id=25290,
    name='Blessing of Wisdom',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=21, apply_aura=85),
    ],
    spell_icon_id=306,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx3': 1, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Restores $s1 mana every 5 seconds.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Blessing on the friendly target, restoring $s1 mana every 5 seconds for $d.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 65536, 'SpellClassSet': 10, 'SpellLevel': 60, 'SpellVisualID_1': 5400, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blessing_of_might_25291 = spell(
    id=25291,
    name='Blessing of Might',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=231, implicit_target_a=21, apply_aura=AuraType.MOD_ATTACK_POWER),
        Effect(type=EffectType.APPLY_AURA, base_points=231, implicit_target_a=21, apply_aura=124),
    ],
    spell_icon_id=298,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases attack power by $s1.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Blessing on the friendly target, increasing attack power by $s1 for $d.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'MaxLevel': 60, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2, 'SpellClassSet': 10, 'SpellLevel': 60, 'SpellVisualID_1': 9179, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


holy_light_25292 = spell(
    id=25292,
    name='Holy Light',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=29,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=2033, points_per_level=5.800000190734863, die_sides=233, implicit_target_a=21),
    ],
    spell_icon_id=70,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 20, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for $s1.', 'EffectBonusMultiplier_1': 1.6790000200271606, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 65, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 10, 'SpellLevel': 60, 'SpellVisualID_1': 2936, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


greater_blessing_of_might_25782 = spell(
    id=25782,
    name='Greater Blessing of Might',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=40.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=184, points_per_level=13.035714285714286, implicit_target_a=61, apply_aura=AuraType.MOD_ATTACK_POWER, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=184, points_per_level=13.035714285714286, implicit_target_a=61, apply_aura=124, radius_yards=100.0),
    ],
    spell_icon_id=1802,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 52); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases attack power by $s1.', 'BaseLevel': 52, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives all members of the raid or group that share the same class with the target the Greater Blessing of Might, increasing attack power by $s1 for $d.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 21177, 'SpellClassMask_1': 2, 'SpellClassSet': 10, 'SpellLevel': 52, 'SpellVisualID_1': 9179, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


greater_blessing_of_wisdom_25894 = spell(
    id=25894,
    name='Greater Blessing of Wisdom',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=40.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, points_per_level=2.3846153846153846, implicit_target_a=61, apply_aura=85, radius_yards=100.0),
    ],
    spell_icon_id=1805,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 54); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx3': 1, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Restores $s1 mana every 5 seconds.', 'BaseLevel': 54, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives all members of the raid or group that share the same class with the target the Greater Blessing of Wisdom, restoring $s1 mana every 5 seconds for $d.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 21177, 'SpellClassMask_1': 65536, 'SpellClassSet': 10, 'SpellLevel': 54, 'SpellVisualID_1': 5400, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


greater_blessing_of_kings_25898 = spell(
    id=25898,
    name='Greater Blessing of Kings',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=40.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=61, apply_aura=137, misc_value=-1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=61, apply_aura=166, radius_yards=100.0),
    ],
    spell_icon_id=1800,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases stats by $s1%.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives all members of the raid or group that share the same class with the target the Greater Blessing of Kings, increasing total stats by $s1% for $d.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 21177, 'SpellClassMask_1': 16777216, 'SpellClassSet': 10, 'SpellLevel': 60, 'SpellVisualID_1': 9187, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


greater_blessing_of_sanctuary_25899 = spell(
    id=25899,
    name='Greater Blessing of Sanctuary',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=40.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=61, apply_aura=AuraType.DUMMY, misc_value=127, radius_yards=100.0),
    ],
    spell_icon_id=1804,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced by up to $s1%, strength and stamina increased by $s2%, and blocked, parried, and dodged melee attacks cause a gain $57319s1% of maximum displayed mana.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives all members of the raid or group that share the same class with the target the Greater Blessing of Sanctuary, reducing damage taken from all sources by $s1% for $d and increasing strength and stamina by $s2%.  In addition, when the target blocks, parries, or dodges a melee attack the target will gain $57319s1% of maximum displayed mana.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectBasePoints_2': 9, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 40, 'ReagentCount_1': 1, 'Reagent_1': 21177, 'SpellClassMask_1': 268435456, 'SpellClassSet': 10, 'SpellLevel': 60, 'SpellVisualID_1': 7323, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


consecration_26573 = spell(
    id=26573,
    name='Consecration',
    school=School.HOLY,
    attributes=65536,
    category=932,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=8000,
    mana_cost=0,
    mana_cost_pct=22,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=8, points_per_level=1.7333333333333334, implicit_target_a=18, implicit_target_b=16, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=1000, radius_yards=8.0),
    ],
    spell_icon_id=51,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 268435592, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 damage every $t1 $lsecond:seconds;.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Consecrates the land beneath the Paladin, doing ${8*($m1+0.04*$SPH+0.04*$AP)} Holy damage over $d to enemies who enter the area.', 'EffectBonusMultiplier_1': 0.03999999910593033, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 32, 'SpellClassSet': 10, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 5600, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


righteous_defense_31789 = spell(
    id=31789,
    name='Righteous Defense',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=8000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=21, radius_yards=5.0),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=1, trigger_spell=31980),
    ],
    spell_icon_id=2037,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 524288, 'AttributesEx5': 2048, 'AttributesEx6': 8, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 14, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Come to the defense of a friendly target, commanding up to 3 enemies attacking the target to attack the Paladin instead.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 4, 'SpellClassSet': 10, 'SpellLevel': 14, 'SpellVisualID_1': 7893},
)


seal_of_vengeance_31801 = spell(
    id=31801,
    name='Seal of Vengeance',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=0.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=240),
        Effect(type=EffectType.APPLY_AURA, base_points=31803, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2292,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attacks cause Holy damage over $31803d.', 'BaseLevel': 64, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Fills the Paladin with holy power, causing attacks to apply Holy Vengeance, which deals ${(0.013*$SPH+0.025*$AP)*5} additional Holy damage over $31803d.  Holy Vengeance can stack up to $31803u times.  Once stacked to $31803u times, each of the Paladin's attacks also deals $42463s1% weapon damage as additional Holy damage.  Only one Seal can be active on the Paladin at any one time.  Lasts $d.\r\n\r\nUnleashing this Seal's energy will deal ${1+0.22*$SPH+0.14*$AP} Holy damage to an enemy, increased by 10% for each application of Holy Vengeance on the target.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 68, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassMask_2': 2048, 'SpellClassSet': 10, 'SpellLevel': 64, 'SpellVisualID_1': 8062, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


avenging_wrath_31884 = spell(
    id=31884,
    name='Avenging Wrath',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=79, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=136, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=2168,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All damage and healing caused increased by $s1%.', 'BaseLevel': 70, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage and healing caused by $s1% for $d.  Cannot be used within $61987d of being the target of Divine Shield, Divine Protection, or Hand of Protection, or of using Lay on Hands on oneself.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_2': 128, 'EquippedItemClass': -1, 'ExcludeCasterAuraSpell': 61987, 'NameSubtext_Lang_Mask': 16712174, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 8192, 'SpellClassSet': 10, 'SpellLevel': 70, 'SpellVisualID_1': 7880},
)


summon_charger_34767 = spell(
    id=34767,
    name='Summon Charger',
    school=School.HOLY,
    mechanic=21,
    attributes=269844480,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=78, misc_value=20030),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=32),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=1716,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 536870912, 'AttributesEx6': 131072, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases speed by $s2%.', 'BaseLevel': 40, 'CastingTimeIndex': 16, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Charger, which serves as a mount.  This is a very fast mount.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Summon', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 268435456, 'SpellClassSet': 10, 'SpellLevel': 40, 'SpellVisualID_1': 3339},
)


judgement_of_justice_53407 = spell(
    id=53407,
    name='Judgement of Justice',
    school=School.HOLY,
    attributes=327680,
    category=1210,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=10000,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=10.0,
    effects=[
        Effect(type=77, base_points=-1, implicit_target_a=6),
    ],
    spell_icon_id=3013,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 1048576, 'AttributesEx3': 196608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 28, 'CasterAuraState': 5, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Unleashes the energy of a Seal spell to judge an enemy for $20184d, preventing them from fleeing and limiting their movement speed.  Refer to individual Seals for additional Judgement effect.  Only one Judgement per Paladin can be active at any one time.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'SpellClassMask_3': 8, 'SpellClassSet': 10, 'SpellLevel': 28, 'SpellVisualID_1': 11853, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


judgement_of_wisdom_53408 = spell(
    id=53408,
    name='Judgement of Wisdom',
    school=School.HOLY,
    attributes=327680,
    category=1210,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=10000,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=10.0,
    effects=[
        Effect(type=77, base_points=-1, implicit_target_a=6),
    ],
    spell_icon_id=3014,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 1048576, 'AttributesEx3': 196608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CasterAuraState': 5, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Unleashes the energy of a Seal spell to judge an enemy for $20186d, giving each attack a chance to restore $20268s1% of the attacker's base mana.  Refer to individual Seals for additional Judgement effect.  Only one Judgement per Paladin can be active at any one time.", 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'SpellClassMask_1': 8388608, 'SpellClassSet': 10, 'SpellLevel': 12, 'SpellVisualID_1': 11855, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shield_of_righteousness_53600 = spell(
    id=53600,
    name='Shield of Righteousness',
    school=School.HOLY,
    attributes=327680,
    category=1209,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=389, points_per_level=26.0, implicit_target_a=6, chain_targets=1),
    ],
    spell_icon_id=3031,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 75); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 2 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AttributesEx4': 262144, 'AttributesEx6': 256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 75, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Slam the target with your shield, causing Holy damage based on your block value plus an additional $s1.', 'EffectBasePoints_2': 99, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 1048576, 'SpellClassSet': 10, 'SpellLevel': 75, 'SpellVisualID_1': 11792, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


sacred_shield_53601 = spell(
    id=53601,
    name='Sacred Shield',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=40.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=21, apply_aura=AuraType.DUMMY, misc_value=127, trigger_spell=58597),
    ],
    spell_icon_id=3033,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 32, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Each time the target takes damage they gain a Sacred Shield, absorbing $58597s1 damage and increasing the paladin's chance to critically hit with Flash of Light by $58597s2%.   The target cannot gain this effect more than once every $s2 sec.", 'BaseLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Each time the target takes damage they gain a Sacred Shield, absorbing $58597s1 damage and increasing the paladin's chance to critically hit with Flash of Light by $58597s2% for up to $58597d.  They cannot gain this effect more than once every $s2 sec.  Lasts $d.  This spell cannot be on more than one target at any one time.", 'EffectBasePoints_2': 5, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 1081344, 'SpellClassMask_2': 524288, 'SpellClassSet': 10, 'SpellLevel': 80, 'SpellVisualID_1': 11956, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


seal_of_corruption_53736 = spell(
    id=53736,
    name='Seal of Corruption',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=0.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=240),
        Effect(type=EffectType.APPLY_AURA, base_points=53732, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2292,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attacks cause Holy damage over $53742d.', 'BaseLevel': 66, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Fills the Paladin with holy power, causing attacks to apply Blood Corruption, which deals ${(0.013*$SPH+0.025*$AP)*5} additional Holy damage over $31803d.  Once stacked to $31803u times, each of the Paladins attacks also deals $53739s1% weapon damage as additional Holy damage.  Blood Corruption can stack up to $31803u times.  Only one Seal can be active on the Paladin at any one time.  Lasts $d.\r\n\r\nUnleashing this Seal's energy will deal ${1+0.22*$SPH+0.14*$AP} Holy damage to an enemy, increased by 10% for each application of Blood Corruption on the target.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 68, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassMask_2': 2048, 'SpellClassSet': 10, 'SpellLevel': 66, 'SpellVisualID_1': 8062, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


divine_plea_54428 = spell(
    id=54428,
    name='Divine Plea',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=21, amplitude=3000),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=2821,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Gaining $o1% of total mana.\r\nHealing spells reduced by $s2%.', 'BaseLevel': 71, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You gain $o1% of your total mana over $d, but the amount healed by your Flash of Light, Holy Light, and Holy Shock spells is reduced by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 3221225472, 'EffectSpellClassMaskB_2': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 2147500032, 'SpellClassMask_3': 1, 'SpellClassSet': 10, 'SpellLevel': 71, 'SpellPriority': 50, 'SpellVisualID_1': 11947, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hand_of_reckoning_62124 = spell(
    id=62124,
    name='Hand of Reckoning',
    school=School.HOLY,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=8000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=30.0,
    duration_ms=3000,
    effects=[
        Effect(type=114, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_TAUNT),
    ],
    spell_icon_id=3722,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 67108864, 'AttributesEx4': 2048, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunted.', 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Taunts the target to attack you.  If the target is tauntable and not currently targeting you, causes ${1+0.5*$AP} Holy damage.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 1073741824, 'SpellClassSet': 10, 'SpellLevel': 16, 'SpellVisualID_1': 34},
)


holy_shock_20473 = spell(
    id=20473,
    name='Holy Shock',
    school=School.HOLY,
    attributes=327680,
    category=892,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=25),
    ],
    spell_icon_id=156,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 196608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blasts the target with Holy energy, causing $25912s1 Holy damage to an enemy, or $25914s1 healing to an ally.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 161, 'SpellClassMask_1': 2097152, 'SpellClassSet': 10, 'SpellLevel': 40, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


holy_shield_20925 = spell(
    id=20925,
    name='Holy Shield',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=931,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=8000,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=51),
        Effect(type=EffectType.APPLY_AURA, base_points=78, points_per_level=4.875, implicit_target_a=1, apply_aura=43),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=189, misc_value=16),
    ],
    spell_icon_id=453,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 2, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Block chance increased by $s1%.  $s2 Holy damage dealt to attacker when blocked.  $n charges.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases chance to block by $s1% for $d and deals $s2 Holy damage for each attack blocked while active.  Each block expends a charge.  $n charges.', 'EffectBonusMultiplier_2': 0.11699999868869781, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 8, 'ProcTypeMask': 680, 'RangeIndex': 1, 'SpellClassMask_2': 64, 'SpellClassSet': 10, 'SpellLevel': 40, 'SpellVisualID_1': 5620, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


avenger_s_shield_31935 = spell(
    id=31935,
    name="Avenger's Shield",
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=1158,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=26,
    range_yards=30.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=439, points_per_level=22.0, die_sides=97, implicit_target_a=6, chain_targets=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED, chain_targets=3),
    ],
    spell_icon_id=2172,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx4': 262144, 'AttributesEx6': 256, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Dazed.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Hurls a holy shield at the enemy, dealing ${$m1+0.07*$SPH+0.07*$AP} to ${$M1+0.07*$SPH+0.07*$AP} Holy damage, Dazing them and then jumping to additional nearby enemies.  Affects $x1 total targets.  Lasts $d.', 'EffectBonusMultiplier_1': 0.09099999815225601, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 35.0, 'SpellClassMask_1': 16384, 'SpellClassSet': 10, 'SpellLevel': 50, 'SpellVisualID_1': 7886, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


repentance_20066 = spell(
    id=20066,
    name='Repentance',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.KNOCKOUT,
    attributes=1114112,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=20.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=316,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 262144, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Incapacitated.', 'AuraInterruptFlags': 2, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Puts the enemy target in a state of meditation, incapacitating them for up to $d, and removing the effect of Righteous Vengeance.  Any damage caused will awaken the target.  Usable against Demons, Dragonkin, Giants, Humanoids and Undead.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 4, 'SpellClassSet': 10, 'SpellLevel': 20, 'SpellVisualID_1': 5539, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 118},
)


divine_favor_20216 = spell(
    id=20216,
    name='Divine Favor',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=168099840,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=104,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Critical effect chance of next Flash of Light, Holy Light, or Holy Shock spell increased by $s1%.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, gives your next Flash of Light, Holy Light, or Holy Shock spell a $s1% critical effect chance.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3223322624, 'EffectSpellClassMaskA_2': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 81920, 'RangeIndex': 1, 'SpellClassMask_2': 256, 'SpellClassSet': 10, 'SpellVisualID_1': 7424},
)


seal_of_command_20375 = spell(
    id=20375,
    name='Seal of Command',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=0.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=20424),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=20424, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=561,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attacks deal additional Holy damage.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "All melee attacks deal ${0.36*$mw} to ${0.36*$MW} additional Holy damage.  When used with attacks or abilities that strike a single target, this additional Holy damage will strike up to 2 additional targets.  Lasts $d.\r\n\r\nUnleashing this Seal's energy will judge an enemy, instantly causing ${0.19*$mw+0.08*$AP+0.13*$SPH} to ${0.19*$MW+0.08*$AP+0.13*$SPH} Holy damage.", 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 28, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassMask_1': 33554432, 'SpellClassSet': 10, 'SpellLevel': 20, 'SpellVisualID_1': 7992, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blessing_of_sanctuary_20911 = spell(
    id=20911,
    name='Blessing of Sanctuary',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=21, apply_aura=AuraType.DUMMY, misc_value=127),
    ],
    spell_icon_id=19,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced by up to $s1%, strength and stamina increased by $s2%, and blocked, parried, and dodged melee attacks cause a gain $57319s1% of maximum displayed mana.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Blessing on the friendly target, reducing damage taken from all sources by $s1% for $d and increasing strength and stamina by $s2%.  In addition, when the target blocks, parries, or dodges a melee attack the target will gain $57319s1% of maximum displayed mana.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectBasePoints_2': 9, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 40, 'SpellClassMask_1': 268435456, 'SpellClassSet': 10, 'SpellLevel': 30, 'SpellVisualID_1': 7323, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


aura_mastery_31821 = spell(
    id=31821,
    name='Aura Mastery',
    school=School.NORMAL,
    attributes=150994960,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=23),
    ],
    spell_icon_id=2136,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 4096, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Concentration Aura provides immunity to Silence and Interrupt effects.\r\nEffectiveness of all other auras increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes your Concentration Aura to make all affected targets immune to Silence and Interrupt effects and improve the effect of all other auras by $s1%.  Lasts $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67108936, 'EffectSpellClassMaskB_1': 67108864, 'EffectSpellClassMaskC_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, 'SpellVisualID_1': 13619},
)


divine_illumination_31842 = spell(
    id=31842,
    name='Divine Illumination',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=134545408,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=72, misc_value=126),
    ],
    spell_icon_id=2138,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Mana cost of all spells reduced by $s1%.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of all spells by $s1% for $d.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1, 'EffectSpellClassMaskA_1': 2121728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 2147500032, 'SpellClassSet': 10, 'SpellVisualID_1': 7878},
)


crusader_strike_35395 = spell(
    id=35395,
    name='Crusader Strike',
    school=School.NORMAL,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=4000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=5.0,
    duration_ms=1,
    effects=[
        Effect(type=121, base_points=-1, implicit_target_a=6),
        Effect(type=31, base_points=74, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2309,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268435968, 'AttributesEx6': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'An instant strike that causes $m2% weapon damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 32768, 'SpellClassSet': 10, 'SpellLevel': 50, 'SpellVisualID_1': 8316, 'StanceBarOrder': 4294967295, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


divine_storm_53385 = spell(
    id=53385,
    name='Divine Storm',
    school=School.NORMAL,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=109, implicit_target_a=1),
        Effect(type=EffectType.DUMMY, base_points=24, implicit_target_a=1),
        Effect(type=31, base_points=109, implicit_target_a=22, implicit_target_b=15, radius_yards=8.0),
    ],
    spell_icon_id=3027,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 16, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'An instant weapon attack that causes $s1% of weapon damage to up to ${$i-1} enemies within $a3 yards.  The Divine Storm heals up to 3 party or raid members totaling $s2% of the damage caused.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'MaxTargets': 5, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 131072, 'SpellClassSet': 10, 'SpellLevel': 60, 'SpellVisualID_1': 12006, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


beacon_of_light_53563 = spell(
    id=53563,
    name='Beacon of Light',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=537198592,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=35,
    range_yards=60.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=57, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1500, trigger_spell=53651),
    ],
    spell_icon_id=3032,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx4': 524288, 'AttributesEx5': 544, 'AttributesEx6': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Beacon of Light.', 'AuraInterruptFlags': 524288, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The target becomes a Beacon of Light to all members of your party or raid within a 60 yard radius.  Any heals you cast on party or raid members will also heal the Beacon for $s1% of the amount healed.  Only one target can be the Beacon of Light at a time. Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 16777216, 'SpellClassSet': 10, 'SpellLevel': 60, 'SpellVisualID_1': 11876, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hammer_of_the_righteous_53595 = spell(
    id=53595,
    name='Hammer of the Righteous',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=6, chain_targets=3),
    ],
    spell_icon_id=3023,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 512, 'AttributesEx4': 262144, 'AttributesEx6': 256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Hammer the current target and up to ${$x1-1} additional nearby targets, causing $s3 times your main hand damage per second as Holy damage.', 'EffectBasePoints_2': 119, 'EffectBasePoints_3': 3, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 41105, 'FacingCasterFlags': 1, 'MaxLevel': 59, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'Speed': 35.0, 'SpellClassMask_2': 262144, 'SpellClassSet': 10, 'SpellLevel': 50, 'SpellVisualID_1': 11927, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


divine_sacrifice_64205 = spell(
    id=64205,
    name='Divine Sacrifice',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=35, base_points=29, implicit_target_a=1, apply_aura=81, misc_value=127, radius_yards=30.0),
    ],
    spell_icon_id=3837,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 67108864, 'AttributesEx7': 1073741824, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1% of all damage taken by party members redirected to the Paladin.', 'AuraInterruptFlags': 4718592, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "$s1% of all damage taken by party members within $a1 yards is redirected to the Paladin (up to a maximum of $s3% of the Paladin's health times the number of party members).  Damage which reduces the Paladin below $s2% health will break the effect.  Lasts $d.", 'EffectBasePoints_2': 19, 'EffectBasePoints_3': 39, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EffectMultipleValue_1': 1.0, 'EffectSpellClassMaskA_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 699048, 'RangeIndex': 1, 'SpellClassMask_3': 4, 'SpellClassSet': 10, 'SpellVisualID_1': 13597, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
