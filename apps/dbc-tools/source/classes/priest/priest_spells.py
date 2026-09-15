"""
Priest - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/priest.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .priest_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, School
from lib.dsl.registry import spell
from .priest_trigger_spells import mind_sear_49821, prayer_of_mending_41635


power_word_shield_17 = spell(
    id=17,
    name='Power Word: Shield',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=19,
    attributes=329728,
    category=56,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=4000,
    mana_cost=0,
    mana_cost_pct=23,
    range_yards=40.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=43, points_per_level=16.6296, implicit_target_a=21, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=566,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 6); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10901, rank 10); coefficient/cast_time_ms/mana_cost_pct from max rank (48066, rank 14); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 2621440, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs damage.', 'BaseLevel': 6, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Draws on the soul of the friendly target to shield them, absorbing $s1 damage.  Lasts $d.  While the shield holds, spellcasting will not be interrupted by damage.  Once shielded, the target cannot be shielded again for $6788d.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 6788, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 1, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 6, 'SpellPriority': 50, 'SpellVisualID_1': 784, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


renew_139 = spell(
    id=139,
    name='Renew',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=40.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, points_per_level=3.5577, implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000),
    ],
    spell_icon_id=321,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1→level-60 slope (anchor rank 25315, rank 10); coefficient/cast_time_ms/mana_cost_pct from max rank (48068, rank 14); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Healing $s1 damage every $t1 seconds.', 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target for $<total> over $d.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 0.37599998712539673, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 64, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellDescriptionVariableID': 30, 'SpellLevel': 8, 'SpellPriority': 50, 'SpellVisualID_1': 280, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mind_soothe_453 = spell(
    id=453,
    name='Mind Soothe',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=40.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=6, apply_aura=91),
    ],
    spell_icon_id=1487,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2228224, 'AttributesEx2': 524288, 'AttributesEx3': 196608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduced distance at which target will attack.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Soothes the target, reducing the range at which it will attack you by $s1 yards.  Only affects Humanoid targets.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_2': 64, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellVisualID_1': 6440, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 64},
)


dispel_magic_527 = spell(
    id=527,
    name='Dispel Magic',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DISPEL, points_per_level=0.0238, implicit_target_a=25, misc_value=1),
    ],
    spell_icon_id=74,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 18); RealPointsPerLevel from rank1→level-60 slope (anchor rank 988, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (988, rank 2); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dispels magic on the target, removing $s1 harmful $lspell:spells; from a friend or $s1 beneficial $lspell:spells; from an enemy.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 160, 'ShapeshiftMask': 134217728, 'SpellClassMask_2': 1, 'SpellClassSet': 6, 'SpellLevel': 18, 'SpellVisualID_1': 86, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


cure_disease_528 = spell(
    id=528,
    name='Cure Disease',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=3),
    ],
    spell_icon_id=330,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Removes $s1 $ldisease:diseases; from the friendly target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 1, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 14, 'SpellVisualID_1': 377, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


abolish_disease_552 = spell(
    id=552,
    name='Abolish Disease',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=329728,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=40.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=3000, trigger_spell=10872),
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=3),
    ],
    spell_icon_id=264,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 32768, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attempts to dispel $10872s1 disease every $t1 seconds.', 'BaseLevel': 32, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Attempts to cure $s2 disease effect on the target, and $10872s1 more disease effect every $t1 seconds for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 1, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 32, 'SpellVisualID_1': 377, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


smite_585 = spell(
    id=585,
    name='Smite',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=12, points_per_level=8.7561, die_sides=5, implicit_target_a=6),
    ],
    spell_icon_id=237,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→top rank's own top level (83, chain has a gap at 60) slope (anchor rank 48123, rank 12); coefficient/cast_time_ms/mana_cost_pct from max rank (48123, rank 12); MaxLevel set to 80",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Smite an enemy for $s1 Holy damage.', 'EffectBonusMultiplier_1': 0.7139999866485596, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'SpellClassMask_1': 128, 'SpellClassSet': 6, 'SpellLevel': 1, 'SpellVisualID_1': 128, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


fade_586 = spell(
    id=586,
    name='Fade',
    school=School.SHADOW,
    attributes=327680,
    category=82,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-90000001, implicit_target_a=1, apply_aura=103),
    ],
    spell_icon_id=331,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduced threat level.', 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fade out, temporarily reducing all your threat for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 16384, 'SpellClassMask_2': 4096, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 8, 'SpellVisualID_1': 72, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


inner_fire_588 = spell(
    id=588,
    name='Inner Fire',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=0.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=314, points_per_level=22.5, implicit_target_a=1, apply_aura=22, misc_value=1),
    ],
    spell_icon_id=51,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 12); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10952, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48168, rank 9); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1.', 'BaseLevel': 12, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A burst of Holy energy fills the caster, increasing armor by $s1.  Each melee or ranged damage hit against the priest will remove one charge.  Lasts $d or until $n charges are used.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 20, 'ProcTypeMask': 680, 'RangeIndex': 1, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 2, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 12, 'SpellVisualID_1': 211, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shadow_word_pain_589 = spell(
    id=589,
    name='Shadow Word: Pain',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=22,
    range_yards=30.0,
    duration_ms=18000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, points_per_level=2.1964, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    spell_icon_id=234,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10894, rank 8); coefficient/cast_time_ms/mana_cost_pct from max rank (48125, rank 12); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx4': 1048576, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Shadow damage every $t1 seconds.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A word of darkness that causes $o1 Shadow damage over $d.', 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 32768, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 4, 'SpellVisualID_1': 71, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prayer_of_healing_596 = spell(
    id=596,
    name='Prayer of Healing',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=48,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=300, points_per_level=23.2, die_sides=21, implicit_target_a=21, implicit_target_b=37, radius_yards=30.0),
    ],
    spell_icon_id=540,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1→level-60 slope (anchor rank 25316, rank 5); coefficient/cast_time_ms/mana_cost_pct from max rank (48072, rank 7); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "A powerful prayer heals the friendly target's party members within $a1 yards for $s1.", 'EffectBonusMultiplier_1': 0.5260000228881836, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 512, 'SpellClassSet': 6, 'SpellLevel': 30, 'SpellVisualID_1': 194, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


power_word_shield_600 = spell(
    id=600,
    name='Power Word: Shield',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=19,
    attributes=327680,
    category=56,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=4000,
    mana_cost=0,
    mana_cost_pct=23,
    range_yards=40.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=157, points_per_level=1.600000023841858, implicit_target_a=21, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=566,
    notes='superseded rank kept in priest.csv: still referenced by item_template 3122 (Codex of Holy Word: Shield III) spellid_2, not creature-only',
    raw_overrides={'AttributesEx2': 2621440, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs damage.', 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Draws on the soul of the friendly target to shield them, absorbing $s1 damage.  Lasts $d.  While the shield holds, spellcasting will not be interrupted by damage.  Once shielded, the target cannot be shielded again for $6788d.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 6788, 'InterruptFlags': 8, 'MaxLevel': 23, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 1, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 18, 'SpellPriority': 50, 'SpellVisualID_1': 784, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mind_control_605 = spell(
    id=605,
    name='Mind Control',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.CHARM,
    attributes=1075118080,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=20.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=31, points_per_level=1.0, implicit_target_a=6, apply_aura=2, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-26, mechanic=8, implicit_target_a=6, apply_aura=138),
    ],
    spell_icon_id=235,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 67248133, 'AttributesEx2': 524352, 'AttributesEx4': 536872960, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Charmed.  Time between attacks increased by $s3%.', 'BaseLevel': 30, 'CastingTimeIndex': 14, 'ChannelInterruptFlags': 27692, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Controls a humanoid mind up to level $s1, but increases the time between its attacks by $s3%.  Lasts up to $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 131072, 'SpellClassSet': 6, 'SpellLevel': 30, 'SpellVisualID_1': 137, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 64},
)


shadow_protection_976 = spell(
    id=976,
    name='Shadow Protection',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=31,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, points_per_level=1.0, implicit_target_a=21, apply_aura=143, misc_value=32),
    ],
    spell_icon_id=207,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10958, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48169, rank 5); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Shadow resistance increased by $s1.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the target's resistance to Shadow spells by $s1 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 256, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 30, 'SpellPriority': 50, 'SpellVisualID_1': 27, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


power_word_fortitude_1243 = spell(
    id=1243,
    name='Power Word: Fortitude',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, points_per_level=0.8644, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=2),
    ],
    spell_icon_id=685,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10938, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48161, rank 8); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Stamina by $s1.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Power infuses the target, increasing their Stamina by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 8, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 1, 'SpellVisualID_1': 278, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


levitate_1706 = spell(
    id=1706,
    name='Levitate',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=30.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=57, apply_aura=105),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=57, apply_aura=106),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=57, apply_aura=104),
    ],
    spell_icon_id=79,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Levitating.', 'AuraInterruptFlags': 131074, 'BaseLevel': 34, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows the friendly party or raid target to levitate, floating a few feet above the ground.  While levitating, the target will fall at a reduced speed and travel over water.  Any damage will cancel the effect.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17056, 'ShapeshiftExclude': 335544320, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 2147483648, 'SpellClassMask_2': 4096, 'SpellClassMask_3': 1025, 'SpellClassSet': 6, 'SpellLevel': 34, 'SpellVisualID_1': 6768, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


resurrection_2006 = spell(
    id=2006,
    name='Resurrection',
    school=School.HOLY,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=60,
    range_yards=30.0,
    effects=[
        Effect(type=113, base_points=69, points_per_level=13.6, misc_value=135),
    ],
    spell_icon_id=121,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1→level-60 slope (anchor rank 20770, rank 5); coefficient/cast_time_ms/mana_cost_pct from max rank (48171, rank 7); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Brings a dead player back to life with $s1 health and $q1 mana.  Cannot be cast when in combat.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 6, 'SpellLevel': 10, 'SpellPriority': 50, 'SpellVisualID_1': 41, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 32768},
)


lesser_heal_2050 = spell(
    id=2050,
    name='Lesser Heal',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=45, points_per_level=6.9286, die_sides=11, implicit_target_a=21),
    ],
    spell_icon_id=682,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→top rank's own top level (15, chain has a gap at 60) slope (anchor rank 2053, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (2053, rank 3); MaxLevel set to 80",
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heal your target for $s1.', 'EffectBonusMultiplier_1': 0.8389999866485596, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 262144, 'SpellClassSet': 6, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 285, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


lesser_heal_2052 = spell(
    id=2052,
    name='Lesser Heal',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=21,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=70, points_per_level=1.100000023841858, die_sides=15, implicit_target_a=21),
    ],
    spell_icon_id=682,
    notes='superseded rank kept in priest.csv: still referenced by item_template 5205 (Sprouted Frond) spellid_1, not creature-only',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 4, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heal your target for $s1.', 'EffectBonusMultiplier_1': 0.4309999942779541, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 9, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 262144, 'SpellClassSet': 6, 'SpellLevel': 4, 'SpellPriority': 50, 'SpellVisualID_1': 285, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


heal_2054 = spell(
    id=2054,
    name='Heal',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=32,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=294, points_per_level=19.087, die_sides=47, implicit_target_a=21),
    ],
    spell_icon_id=104,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 16); RealPointsPerLevel from rank1→top rank's own top level (39, chain has a gap at 60) slope (anchor rank 6064, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (6064, rank 4); MaxLevel set to 80",
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 16, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heal your target for $s1.', 'EffectBonusMultiplier_1': 1.6109999418258667, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 1024, 'SpellClassSet': 6, 'SpellLevel': 16, 'SpellPriority': 50, 'SpellVisualID_1': 135, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


greater_heal_2060 = spell(
    id=2060,
    name='Greater Heal',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=32,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=45, points_per_level=37.8101, die_sides=115, implicit_target_a=21),
    ],
    spell_icon_id=241,
    notes="re-anchored for the Priest heal-line collapse (Lesser Heal/Heal retired from trainers, Greater Heal is now the one heal spell learned at level 1): base_points/BaseLevel/SpellLevel moved from rank1's old level-40 anchor down to Lesser Heal rank1's (2050) level-1 value (45); RealPointsPerLevel recomputed as a straight line from that level-1 value to this spell's own previous level-80 ceiling (898 + 40*53.35 = 3032), so max-level healing is unchanged; die_sides/cast_time_ms/mana_cost_pct/coefficient kept as before (from max rank 48063, rank 9). See docs/.master-todo-list.md.",
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A slow casting spell that heals a single target for $s1.', 'EffectBonusMultiplier_1': 1.6109999418258667, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 4096, 'SpellClassSet': 6, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 57, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


flash_heal_2061 = spell(
    id=2061,
    name='Flash Heal',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=192, points_per_level=15.875, die_sides=45, implicit_target_a=21),
    ],
    spell_icon_id=242,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10917, rank 7); coefficient/cast_time_ms/mana_cost_pct from max rank (48071, rank 11); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for $s1.', 'EffectBonusMultiplier_1': 0.8069999814033508, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 2048, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 3077, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mind_vision_2096 = spell(
    id=2096,
    name='Mind Vision',
    school=School.SHADOW,
    attributes=67174400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=100.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=25, apply_aura=1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=25, apply_aura=68),
    ],
    spell_icon_id=502,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 22); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10909, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (10909, rank 2); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 67773444, 'AttributesEx2': 524300, 'AttributesEx3': 196608, 'AttributesEx4': 65536, 'AttributesEx5': 2097152, 'AttributesEx6': 12, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Sight granted through target's eyes.", 'BaseLevel': 22, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31772, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Allows the caster to see through the target's eyes for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 9, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 67108864, 'SpellClassMask_2': 2147483648, 'SpellClassSet': 6, 'SpellLevel': 22, 'SpellVisualID_1': 4839, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


devouring_plague_2944 = spell(
    id=2944,
    name='Devouring Plague',
    school=School.SHADOW,
    dispel=DispelType.DISEASE,
    mechanic=22,
    attributes=65536,
    category=691,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=25,
    range_yards=30.0,
    duration_ms=24000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=18, points_per_level=2.35, implicit_target_a=6, apply_aura=AuraType.PERIODIC_LEECH, amplitude=3000),
    ],
    spell_icon_id=3789,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor rank 19280, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48300, rank 9); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Causes $s1 damage every $t1 seconds, healing the caster.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Afflicts the target with a disease that causes $o1 Shadow damage over $d. 15% of damage caused by the Devouring Plague heals the caster. This spell can only affect one target at a time.', 'EffectBonusMultiplier_1': 0.1850000023841858, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 0.15000000596046448, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 33554432, 'SpellClassMask_2': 4096, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 346, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


heal_6063 = spell(
    id=6063,
    name='Heal',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=32,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=565, points_per_level=4.0, die_sides=77, implicit_target_a=21),
    ],
    spell_icon_id=684,
    notes='superseded rank kept in priest.csv: still referenced by item_template 8993 (Codex of Shadow Protection II) spellid_2, not creature-only',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 28, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heal your target for $s1.', 'EffectBonusMultiplier_1': 1.6109999418258667, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 33, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 1024, 'SpellClassSet': 6, 'SpellLevel': 28, 'SpellPriority': 50, 'SpellVisualID_1': 135, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


fear_ward_6346 = spell(
    id=6346,
    name='Fear Ward',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=30.0,
    duration_ms=180000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=5),
    ],
    spell_icon_id=158,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Warded against Fear.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Wards the friendly target against Fear.  The next Fear effect used against the target will fail, using up the ward.  Lasts $d.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 139264, 'SpellClassMask_1': 2147483648, 'SpellClassMask_2': 33558528, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellVisualID_1': 343, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mind_blast_8092 = spell(
    id=8092,
    name='Mind Blast',
    school=School.SHADOW,
    attributes=65536,
    category=19,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=8000,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=38, points_per_level=9.38, die_sides=5, implicit_target_a=6),
    ],
    spell_icon_id=95,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10947, rank 9); coefficient/cast_time_ms/mana_cost_pct from max rank (48127, rank 13); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blasts the target for $s1 Shadow damage.', 'EffectBonusMultiplier_1': 0.42899999022483826, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 8192, 'SpellClassSet': 6, 'SpellLevel': 10, 'SpellVisualID_1': 3057, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


psychic_scream_8122 = spell(
    id=8122,
    name='Psychic Scream',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.FEAR,
    attributes=327680,
    category=43,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_FEAR, radius_yards=8.0),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_INCREASE_SPEED, radius_yards=8.0),
    ],
    spell_icon_id=1488,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 14); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10890, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (10890, rank 4); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 524288, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Running in Fear.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The caster lets out a psychic scream, causing $i enemies within $a1 yards to flee for $d.  Damage caused may interrupt the effect.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'MaxTargets': 2, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 65536, 'SpellClassSet': 6, 'SpellLevel': 14, 'SpellPriority': 50, 'SpellVisualID_1': 247, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mana_burn_8129 = spell(
    id=8129,
    name='Mana Burn',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=30.0,
    effects=[
        Effect(type=62, base_points=9, implicit_target_a=6),
    ],
    spell_icon_id=212,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 24, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Destroy $m1% of the target's mana (up to a maximum of ${$m1*2}% of your own maximum mana). For each mana destroyed in this way, the target takes 0.5 Shadow damage.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 0.5, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 29, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 16, 'SpellClassSet': 6, 'SpellLevel': 24, 'SpellVisualID_1': 3076, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shackle_undead_9484 = spell(
    id=9484,
    name='Shackle Undead',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=20,
    attributes=1074855936,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=30.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=27,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10955, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (10955, rank 3); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 262144, 'AttributesEx2': 524288, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Shackled.', 'AuraInterruptFlags': 2, 'BaseLevel': 20, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shackles the target undead enemy for up to $d.  The shackled unit is unable to move, attack or cast spells.  Any damage caused will release the target.  Only one target can be shackled at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 1073741824, 'SpellClassMask_2': 67112960, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellVisualID_1': 1507, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 32},
)


power_word_fortitude_10937 = spell(
    id=10937,
    name='Power Word: Fortitude',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=42, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=2),
    ],
    spell_icon_id=685,
    notes='superseded rank kept in priest.csv: still referenced by quest_template 5217/5220/5223 RewardSpell, not creature-only',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Stamina by $s1.', 'BaseLevel': 48, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Power infuses the target, increasing their Stamina by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 58, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 8, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 48, 'SpellVisualID_1': 278, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


power_word_fortitude_10938 = spell(
    id=10938,
    name='Power Word: Fortitude',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=53, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=2),
    ],
    spell_icon_id=685,
    notes='superseded rank kept in priest.csv: still referenced by quest_template 5226 RewardSpell, not creature-only',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Stamina by $s1.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Power infuses the target, increasing their Stamina by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 70, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 8, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellVisualID_1': 278, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


divine_spirit_14752 = spell(
    id=14752,
    name='Divine Spirit',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=26,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=16, points_per_level=0.7667, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=4),
    ],
    spell_icon_id=1879,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1→level-60 slope (anchor rank 27841, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (48073, rank 6); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Spirit by $s1.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Holy power infuses the target, increasing their Spirit by $s1 for $d.', 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 32, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 30, 'SpellVisualID_1': 193, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


holy_fire_14914 = spell(
    id=14914,
    name='Holy Fire',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=451,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=30.0,
    duration_ms=7000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=101, points_per_level=13.425, die_sides=27, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=2, points_per_level=0.375, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=1000),
    ],
    spell_icon_id=156,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor rank 15261, rank 8); coefficient/cast_time_ms/mana_cost_pct from max rank (48135, rank 11); MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s2 Holy damage every $t2 seconds.', 'BaseLevel': 20, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Consumes the enemy in Holy flames that cause $s1 Holy damage and an additional $o2 Holy damage over $d.', 'EffectBonusMultiplier_1': 0.5709999799728394, 'EffectBonusMultiplier_2': 0.024000000208616257, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'SpellClassMask_1': 1048576, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 3400, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


holy_nova_15237 = spell(
    id=15237,
    name='Holy Nova',
    school=School.HOLY,
    attributes=65536,
    category=431,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=20,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=27, points_per_level=3.825, die_sides=5, implicit_target_a=22, implicit_target_b=15, radius_yards=10.0),
    ],
    spell_icon_id=1874,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor rank 27801, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48078, rank 9); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes an explosion of holy light around the caster, causing $15237s1 Holy damage to all enemy targets within $15237a1 yards and healing all party members within $23455a1 yards for $23455s1.  These effects cause no threat.', 'EffectBonusMultiplier_1': 0.16099999845027924, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassMask_1': 4194304, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellVisualID_1': 3643, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prayer_of_fortitude_21562 = spell(
    id=21562,
    name='Prayer of Fortitude',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=69,
    range_yards=40.0,
    duration_ms=3600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=42, points_per_level=0.9167, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=2, radius_yards=100.0),
    ],
    spell_icon_id=1669,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 48); RealPointsPerLevel from rank1→level-60 slope (anchor rank 21564, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (48162, rank 4); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Stamina by $s1.', 'BaseLevel': 48, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Power infuses all party and raid members, increasing their Stamina by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17028, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 8, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 48, 'SpellVisualID_1': 278, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prayer_of_fortitude_21564 = spell(
    id=21564,
    name='Prayer of Fortitude',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=69,
    range_yards=40.0,
    duration_ms=3600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=53, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=2, radius_yards=100.0),
    ],
    spell_icon_id=1669,
    notes='superseded rank kept in priest.csv: still referenced by item_template 17414 (Codex: Prayer of Fortitude II) spellid_2, not creature-only',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Stamina by $s1.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Power infuses all party and raid members, increasing their Stamina by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 70, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17029, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 8, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellVisualID_1': 278, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


greater_heal_25314 = spell(
    id=25314,
    name='Greater Heal',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=32,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=1965, points_per_level=8.100000381469727, die_sides=229, implicit_target_a=21),
    ],
    spell_icon_id=241,
    notes='superseded rank kept in priest.csv: still referenced by item_template 21284 (Codex of Greater Heal V) spellid_2, not creature-only',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A slow casting spell that heals a single target for $s1.', 'EffectBonusMultiplier_1': 1.6109999418258667, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 65, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 4096, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 57, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


renew_25315 = spell(
    id=25315,
    name='Renew',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=40.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=193, implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000),
    ],
    spell_icon_id=321,
    notes='superseded rank kept in priest.csv: still referenced by item_template 21285 (Codex of Renew X) spellid_2, not creature-only',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Healing $s1 damage every $t1 seconds.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target for $<total> over $d.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 0.37599998712539673, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 65, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 10', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 64, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellDescriptionVariableID': 30, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 280, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prayer_of_healing_25316 = spell(
    id=25316,
    name='Prayer of Healing',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=48,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=996, points_per_level=2.5, die_sides=57, implicit_target_a=21, implicit_target_b=37, radius_yards=30.0),
    ],
    spell_icon_id=540,
    notes='superseded rank kept in priest.csv: still referenced by item_template 21287 (Codex of Prayer of Healing V) spellid_2, not creature-only',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "A powerful prayer heals the friendly target's party members within $a1 yards for $s1.", 'EffectBonusMultiplier_1': 0.5260000228881836, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 69, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 512, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellVisualID_1': 194, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prayer_of_fortitude_25392 = spell(
    id=25392,
    name='Prayer of Fortitude',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=69,
    range_yards=40.0,
    duration_ms=3600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=78, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=2, radius_yards=100.0),
    ],
    spell_icon_id=1669,
    notes='superseded rank kept in priest.csv: still referenced by item_template 29549 (Codex: Prayer of Fortitude III) spellid_2, not creature-only',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Stamina by $s1.', 'BaseLevel': 70, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Power infuses all party and raid members, increasing their Stamina by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17029, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 8, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 70, 'SpellVisualID_1': 278, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prayer_of_spirit_27681 = spell(
    id=27681,
    name='Prayer of Spirit',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=69,
    range_yards=40.0,
    duration_ms=3600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, points_per_level=1.3333, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=4, radius_yards=100.0),
    ],
    spell_icon_id=1870,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1→top rank's own top level (90, chain has a gap at 60) slope (anchor rank 48074, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48074, rank 3); MaxLevel set to 80",
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Spirit by $s1.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Power infuses the target's party and raid members, increasing their Spirit by $s1 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17029, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 32, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellVisualID_1': 193, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prayer_of_shadow_protection_27683 = spell(
    id=27683,
    name='Prayer of Shadow Protection',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=62,
    range_yards=40.0,
    duration_ms=1200000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=56, apply_aura=143, misc_value=32, radius_yards=100.0),
    ],
    spell_icon_id=1869,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 56); RealPointsPerLevel from rank1→level-60 slope (anchor rank 27683, rank 1); coefficient/cast_time_ms/mana_cost_pct from max rank (48170, rank 3); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Shadow Resistance by $s1.', 'BaseLevel': 56, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Power infuses the target's party and raid members, increasing their Shadow resistance by $s1 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17029, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 256, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 56, 'SpellVisualID_1': 27, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mass_dispel_32375 = spell(
    id=32375,
    name='Mass Dispel',
    school=School.HOLY,
    attributes=536936448,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=33,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=31, misc_value=1, radius_yards=15.0),
        Effect(type=EffectType.TRIGGER_SPELL, implicit_target_a=16, trigger_spell=32592, radius_yards=10.0),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=72733, implicit_target_a=1, trigger_spell=72734),
    ],
    spell_icon_id=2267,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 70, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dispels magic in a $32375a1 yard radius, removing $32375s1 harmful $lspell:spells; from each friendly target and $32375s1 beneficial $lspell:spells; from each enemy target.  Affects a maximum of $32375i friendly targets and $32375i enemy targets.  This dispel is potent enough to remove Magic effects that are normally undispellable.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxTargets': 10, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_2': 128, 'SpellClassSet': 6, 'SpellLevel': 70, 'SpellVisualID_1': 8140, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)


shadow_word_death_32379 = spell(
    id=32379,
    name='Shadow Word: Death',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=1169,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=12000,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=449, points_per_level=13.6364, die_sides=73, implicit_target_a=6),
    ],
    spell_icon_id=1980,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 62); RealPointsPerLevel from rank1→top rank's own top level (84, chain has a gap at 60) slope (anchor rank 48158, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (48158, rank 4); MaxLevel set to 80",
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 62, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A word of dark binding that inflicts $s1 Shadow damage to the target.  If the target is not killed by Shadow Word: Death, the caster takes damage equal to the damage inflicted upon the target.', 'EffectBonusMultiplier_1': 0.42899999022483826, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_2': 2, 'SpellClassSet': 6, 'SpellLevel': 62, 'SpellVisualID_1': 8069, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


binding_heal_32546 = spell(
    id=32546,
    name='Binding Heal',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=1041, points_per_level=51.3333, die_sides=297, implicit_target_a=21),
        Effect(type=EffectType.HEAL, base_points=1041, points_per_level=51.3333, die_sides=297, implicit_target_a=1),
    ],
    spell_icon_id=2266,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 64); RealPointsPerLevel from rank1→top rank's own top level (82, chain has a gap at 60) slope (anchor rank 48120, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48120, rank 3); MaxLevel set to 80",
    raw_overrides={'AttributesEx': 524288, 'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 64, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target and the caster for $s1.  Low threat.', 'EffectBonusMultiplier_1': 0.8069999814033508, 'EffectBonusMultiplier_2': 0.8069999814033508, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_2': 4, 'SpellClassSet': 6, 'SpellLevel': 64, 'SpellPriority': 50, 'SpellVisualID_1': 3077, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prayer_of_mending_33076 = spell(
    id=33076,
    name='Prayer of Mending',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=1181,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=40.0,
    effects=[
        Effect(type=142, base_points=799, points_per_level=15.1875, implicit_target_a=57, trigger_spell=prayer_of_mending_41635.id),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=57, trigger_spell=41637),
    ],
    spell_icon_id=2219,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 68); RealPointsPerLevel from rank1→top rank's own top level (84, chain has a gap at 60) slope (anchor rank 48113, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48113, rank 3); MaxLevel set to 80",
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 67108864, 'AttributesEx7': 1073741824, 'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 68, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a spell on the target that heals them for $s1 the next time they take damage.  When the heal occurs, Prayer of Mending jumps to a party or raid member within $41635a1 yards.  Jumps up to $n times and lasts $41635d after each jump.  This spell can only be placed on one target at a time.', 'EffectBonusMultiplier_1': 0.8069999814033508, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 5, 'ProcTypeMask': 699048, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_2': 32, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 68, 'SpellVisualID_1': 8070, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shadowfiend_34433 = spell(
    id=34433,
    name='Shadowfiend',
    school=School.SHADOW,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.SUMMON, die_sides=0, implicit_target_a=53, misc_value=19668),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=1, trigger_spell=41967),
    ],
    spell_icon_id=2296,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268435457, 'AttributesEx2': 524288, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 66, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a shadowy fiend to attack the target.  Caster receives $34650s1% mana when the Shadowfiend attacks. Damage taken by area of effect attacks is reduced. Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1561, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 1073741824, 'SpellClassMask_2': 256, 'SpellClassSet': 6, 'SpellLevel': 66, 'SpellVisualID_1': 8208, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prayer_of_shadow_protection_39374 = spell(
    id=39374,
    name='Prayer of Shadow Protection',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=62,
    range_yards=40.0,
    duration_ms=1200000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=69, implicit_target_a=56, apply_aura=143, misc_value=32, radius_yards=100.0),
    ],
    spell_icon_id=1869,
    notes='superseded rank kept in priest.csv: still referenced by item_template 31837 (Codex: Prayer of Shadow Protection II) spellid_2, not creature-only',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Shadow Resistance by $s1.', 'BaseLevel': 70, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Power infuses the target's party and raid members, increasing their Shadow resistance by $s1 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17029, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 256, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 70, 'SpellVisualID_1': 27, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mind_sear_48045 = spell(
    id=48045,
    name='Mind Sear',
    school=School.SHADOW,
    attributes=4259840,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=28,
    range_yards=30.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=6, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=mind_sear_49821.id),
    ],
    spell_icon_id=2895,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 75); RealPointsPerLevel from rank1→top rank's own top level (84, chain has a gap at 60) slope (anchor rank 53023, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (53023, rank 2); MaxLevel set to 80",
    raw_overrides={'AttributesEx': 132, 'AttributesEx2': 524288, 'AttributesEx5': 8192, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Causing shadow damage to all targets within $49821a1 yards.', 'BaseLevel': 75, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31788, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes an explosion of shadow magic around the enemy target, causing $49821s1 Shadow damage every $T1 sec for $d to all enemies within $49821a1 yards around the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_2': 1048576, 'SpellClassSet': 6, 'SpellLevel': 75, 'SpellVisualID_1': 12121, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


divine_hymn_64843 = spell(
    id=64843,
    name='Divine Hymn',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=480000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=63,
    range_yards=40.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=2000, trigger_spell=64844),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3209,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 536870980, 'AttributesEx2': 1074266116, 'AttributesEx3': 1073741824, 'AttributesEx4': 64, 'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reciting Divine Hymn, healing nearby friendly party or raid targets most in need for $64844s1 every $t1 sec for $d.', 'AuraInterruptFlags': 131072, 'BaseLevel': 80, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31788, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals $64843s2 nearby lowest health friendly party or raid targets within $64844a1 yards for $64844s1 every $64843t1 sec for $64843d, and increases healing done to them by $64844s2% for $64844d. Maximum of $*4;64843s2 heals. The Priest must channel to maintain the spell.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 13, 'MaxLevel': 84, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_2': 4194304, 'SpellClassSet': 6, 'SpellLevel': 80, 'SpellVisualID_1': 10671, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hymn_of_hope_64901 = spell(
    id=64901,
    name='Hymn of Hope',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=360000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=2000, trigger_spell=64904),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2218,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 536870980, 'AttributesEx2': 524288, 'AttributesEx4': 64, 'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reciting Hymn of Hope, restoring $64904s1% mana to nearby friendly party or raid targets most in need every $t1 sec for $d.', 'AuraInterruptFlags': 131072, 'BaseLevel': 80, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31788, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restores $64904s1% mana to $64901s2 nearby low mana friendly party or raid targets every $64901t1 sec for $64901d, and increases their total maximum mana by $64904s2% for $64904d. Maximum of $*4;s2 mana restores. The Priest must channel to maintain the spell.', 'EffectBonusMultiplier_1': 0.12700000405311584, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 13, 'MaxLevel': 84, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'SpellClassMask_3': 16, 'SpellClassSet': 6, 'SpellLevel': 80, 'SpellVisualID_1': 12858, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


lightwell_724 = spell(
    id=724,
    name='Lightwell',
    school=School.HOLY,
    attributes=65536,
    category=1145,
    cast_time_ms=500,
    cooldown_ms=0,
    category_cooldown_ms=180000,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=40.0,
    duration_ms=180000,
    effects=[
        Effect(type=EffectType.SUMMON, implicit_target_a=87, misc_value=31897),
    ],
    spell_icon_id=1878,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1→level-60 slope (anchor rank 27871, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48087, rank 6); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a Holy Lightwell.  Friendly players can click the Lightwell to restore ${$7001m1*3*$<mult>} health over $7001d.  Attacks done to you equal to 30% of your total health will cancel the effect. Lightwell lasts for $d or 10 charges.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1141, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 6, 'SpellDescriptionVariableID': 162, 'SpellLevel': 40, 'SpellVisualID_1': 7550, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)


mind_flay_15407 = spell(
    id=15407,
    name='Mind Flay',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=30.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.APPLY_AURA, base_points=14, points_per_level=2.65, implicit_target_a=1, apply_aura=227, amplitude=1000, trigger_spell=58381),
    ],
    spell_icon_id=548,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor rank 18807, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48156, rank 9); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 67125252, 'AttributesEx2': 524288, 'AttributesEx5': 134225920, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed slowed.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Assault the target's mind with Shadow energy, causing ${$m3*3} Shadow damage over $d and slowing their movement speed by $s2%.", 'EffectBonusMultiplier_3': 0.2709999978542328, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_3': 1088, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellVisualID_1': 12637, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


desperate_prayer_19236 = spell(
    id=19236,
    name='Desperate Prayer',
    school=School.HOLY,
    attributes=65536,
    category=671,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=120000,
    mana_cost=0,
    mana_cost_pct=21,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=262, points_per_level=26.525, die_sides=63, implicit_target_a=1),
    ],
    spell_icon_id=73,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor rank 19243, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48173, rank 9); MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly heals the caster for $s1.', 'EffectBonusMultiplier_1': 0.8069999814033508, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassMask_1': 16777216, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellVisualID_1': 4819, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


circle_of_healing_34861 = spell(
    id=34861,
    name='Circle of Healing',
    school=School.HOLY,
    attributes=65536,
    category=1204,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=21,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=342, points_per_level=11.5, die_sides=37, implicit_target_a=63, implicit_target_b=31, radius_yards=15.0),
    ],
    spell_icon_id=2214,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1→level-60 slope (anchor rank 34864, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48089, rank 7); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx5': 4194304, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals up to $?s55675[6][5] friendly party or raid members within $a1 yards of the target for $s1.', 'EffectBonusMultiplier_1': 0.4020000100135803, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 268435456, 'SpellClassSet': 6, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 8253, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


vampiric_touch_34914 = spell(
    id=34914,
    name='Vampiric Touch',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=30.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=6, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=89, points_per_level=3.0, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2213,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1→level-60 slope (anchor rank 34916, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (48160, rank 5); MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "$s2 Shadow damage every $t2 seconds. Priest's party or raid members gain 1% of their maximum mana per 5 sec when the priest deals damage from Mind Blast.", 'BaseLevel': 50, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes $o2 Shadow damage over $d to your target and causes up to 10 party or raid members to gain 1% of their maximum mana per 5 sec when you deal damage from Mind Blast. In addition, if the Vampiric Touch is dispelled it will cause $*8;s2 damage to the afflicted target.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 0.4000000059604645, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 131072, 'SpellClassMask_2': 1024, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 50, 'SpellVisualID_1': 3582, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


penance_47540 = spell(
    id=47540,
    name='Penance',
    school=School.HOLY,
    attributes=536936704,
    category=1230,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=12000,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=-1, implicit_target_a=25),
    ],
    spell_icon_id=2818,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1→top rank's own top level (84, chain has a gap at 60) slope (anchor rank 53007, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (53007, rank 4); MaxLevel set to 80",
    raw_overrides={'AttributesEx': 268452996, 'AttributesEx4': 134217728, 'AttributesEx5': 8704, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Launches a volley of holy light at the target, causing $47666s1 Holy damage to an enemy, or $47750s1 healing to an ally instantly and every $47758t2 sec for $47758d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 160, 'SpellClassMask_2': 8388608, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 10980, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


power_infusion_10060 = spell(
    id=10060,
    name='Power Infusion',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=30.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=21, apply_aura=65, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=21, apply_aura=72, misc_value=126),
    ],
    spell_icon_id=1872,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell casting speed increased by $s1% and mana cost of spells reduced by $s2%.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Infuses the target with power, increasing spell casting speed by $s1% and reducing the mana cost of all spells by $s2%.  Lasts $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2147483648, 'SpellClassMask_2': 536875008, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 40, 'SpellVisualID_1': 7553},
)


inner_focus_14751 = spell(
    id=14751,
    name='Inner Focus',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=33882112,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=101,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 67108864, 'AttributesEx4': 524352, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'The mana cost of your next spell is reduced by $s1%.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, reduces the mana cost of your next spell by $s1% and increases its critical effect chance by $s2% if it is capable of a critical effect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3612868607, 'EffectSpellClassMaskA_2': 13997559, 'EffectSpellClassMaskA_3': 8256, 'EffectSpellClassMaskB_1': 3386130064, 'EffectSpellClassMaskB_2': 13205558, 'EffectSpellClassMaskB_3': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'ShapeshiftMask': 134217728, 'SpellClassMask_2': 1073745920, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellVisualID_1': 4372},
)


shadowform_15473 = spell(
    id=15473,
    name='Shadowform',
    school=School.SHADOW,
    attributes=184877056,
    category=39,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1500,
    mana_cost=0,
    mana_cost_pct=13,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=36, misc_value=28),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=79, misc_value=32),
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=1552,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 55, 'AttributesEx': 131072, 'AttributesEx4': 2621440, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Shadow damage you deal increased by $s2%.  All damage you take reduced by $s3% and threat generated is reduced by $49868s1%. You may not cast Holy spells except Cure Disease and Abolish Disease.  Grants the periodic damage from your Shadow Word: Pain, Devouring Plague, and Vampiric Touch spells the ability to critically hit for $49868s2% increased damage and grants Devouring Plague and Vampiric Touch the ability to benefit from haste.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Assume a Shadowform, increasing your Shadow damage by $s2%, reducing all damage done to you by $s3% and threat generated by $49868s1%.  However, you may not cast Holy spells while in this form except Cure Disease and Abolish Disease.  Grants the periodic damage from your Shadow Word: Pain, Devouring Plague, and Vampiric Touch spells the ability to critically hit for $49868s2% increased damage and grants Devouring Plague and Vampiric Touch the ability to benefit from haste.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 2147483648, 'SpellClassMask_2': 2048, 'SpellClassSet': 6, 'SpellVisualID_1': 3619, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


silence_15487 = spell(
    id=15487,
    name='Silence',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.SILENCE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=45000,
    category_cooldown_ms=0,
    mana_cost=225,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=6, apply_aura=AuraType.MOD_SILENCE),
    ],
    spell_icon_id=211,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx6': 10485760, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Silenced.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Silences the target, preventing them from casting spells for $d.  Non-player victim spellcasting is also interrupted for $32747d.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_2': 2101248, 'SpellClassSet': 6, 'SpellVisualID_1': 179},
)


pain_suppression_33206 = spell(
    id=33206,
    name='Pain Suppression',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=40.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-41, implicit_target_a=21, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=64, implicit_target_a=21, apply_aura=235),
    ],
    spell_icon_id=2178,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 8, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All damage taken reduced by $s1% and resistance to Dispel mechanics increased by $s2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Instantly reduces a friendly target's threat by $44416s1%, reduces all damage taken by $s1% and increases resistance to Dispel mechanics by $s2% for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 45859183, 'EffectSpellClassMaskB_2': 5705, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 21, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2147483648, 'SpellClassMask_2': 268439552, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellVisualID_1': 8039, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


dispersion_47585 = spell(
    id=47585,
    name='Dispersion',
    school=School.NORMAL,
    attributes=17039376,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-91, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=60),
    ],
    spell_icon_id=2875,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx5': 131080, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces all damage by $s1%, and you regenerate $49766s1% mana every $60069t1 sec for $d.  Cannot attack or cast spells. Immune to snare and movement impairing effects.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You disperse into pure Shadow energy, reducing all damage taken by $47585s1%.  You are unable to attack or cast spells, but you regenerate $49766s1% mana every $60069t1 sec for $d. Dispersion can be cast while stunned, feared or silenced and clears all snare and movement impairing effects when cast, and makes you immune to them while dispersed.', 'EffectBasePoints_2': 5, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 262144, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellVisualID_1': 11005, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


guardian_spirit_47788 = spell(
    id=47788,
    name='Guardian Spirit',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=40.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=21, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=21, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=2873,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increased healing received by $s1% and will prevent 1 killing blow.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Calls upon a guardian spirit to watch over the friendly target. The spirit increases the healing received by the target by $s1%, and also prevents the target from dying by sacrificing itself.  This sacrifice terminates the effect but heals the target of $s2% of their maximum health. Lasts $d.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 2281701376, 'SpellClassMask_1': 3221225472, 'SpellClassMask_3': 3072, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellVisualID_1': 12114},
)


psychic_horror_64044 = spell(
    id=64044,
    name='Psychic Horror',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=30.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=24, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
        Effect(type=EffectType.TRIGGER_SPELL, implicit_target_a=6, trigger_spell=64058),
    ],
    spell_icon_id=2847,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Horrified.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You terrify the target, causing them to tremble in horror for $d and drop their main hand and ranged weapons for $64058d.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectMechanic_3': 24, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': 8192, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellVisualID_1': 13757, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
