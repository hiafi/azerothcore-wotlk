"""
Mage - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/mage.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .mage_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, School, SpellModOp
from lib.dsl.registry import bonus_coefficients, scripted_by, skill_line_ability, spell, trained_by
from .mage_trigger_spells import arcane_blast_debuff, arcane_missile_7268, blizzard_42208, meteor_impact_200096, molten_armor_34913


blizzard_10 = spell(
    id=10,
    name='Blizzard',
    school=School.FROST,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=74,
    range_yards=30.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=24, points_per_level=3.1, implicit_target_a=28, apply_aura=AuraType.DUMMY, radius_yards=8.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=blizzard_42208.id),
    ],
    spell_icon_id=285,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 268435596, 'AttributesEx2': 4194304, 'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$42208s1 Frost damage every $42208t1 $lsecond:seconds;.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31788, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Ice shards pelt the target area doing ${$42208m1*8*$<mult>} Frost damage over $10d.', 'EffectBonusMultiplier_1': 0.11900000274181366, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'SpellClassMask_1': 524416, 'SpellClassSet': 3, 'SpellDescriptionVariableID': 167, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 9490, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)


invisibility_66 = spell(
    id=66,
    name='Invisibility',
    school=School.ARCANE,
    dispel=DispelType.INVISIBILITY,
    attributes=1114112,
    category=1162,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=0.0,
    duration_ms=3000,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=35009),
    ],
    spell_icon_id=2308,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 1073741824, 'AttributesEx4': 64, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Fading.', 'AuraInterruptFlags': 660484, 'BaseLevel': 58, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': '$?s54354[Instantly makes the caster invisible, reducing all threat.][Fades the caster to invisibility over $66d, reducing threat each second.]  The effect is cancelled if you perform any actions.  While invisible, you can only see other invisible targets and those who can see invisible.  Lasts $32612d.', 'EffectBasePoints_3': 99, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'ExcludeCasterAuraState': 12, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 2147483648, 'SpellClassMask_2': 262144, 'SpellClassSet': 3, 'SpellLevel': 58, 'SpellPriority': 50, 'SpellVisualID_1': 7964, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


frostbolt_116 = spell(
    id=116,
    name='Frostbolt',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=30.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-41, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=17, points_per_level=7.5464, die_sides=3, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=188,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement slowed by $s1%.', 'BaseLevel': 4, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Launches a bolt of frost at the enemy, causing ${$m2*$<mult>} to ${$M2*$<mult>} Frost damage and slowing movement speed by $s1% for $d.', 'EffectBonusMultiplier_2': 0.8569999933242798, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 28.0, 'SpellClassMask_1': 32, 'SpellClassSet': 3, 'SpellDescriptionVariableID': 167, 'SpellLevel': 4, 'SpellPriority': 50, 'SpellVisualID_1': 13, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


polymorph_118 = spell(
    id=118,
    name='Polymorph',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.POLYMORPH,
    attributes=1074855936,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=30.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_CONFUSE),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.TRANSFORM, misc_value=16372),
    ],
    spell_icon_id=82,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 262144, 'AttributesEx2': 64, 'AttributesEx4': 1610612736, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Cannot attack or cast spells.  Increased regeneration.', 'AuraInterruptFlags': 524290, 'BaseLevel': 8, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Transforms the enemy into a sheep, forcing it to wander around for up to $d.  While wandering, the sheep cannot attack or cast spells but will regenerate very quickly.  Any damage will transform the target back into its normal form.  Only one target can be polymorphed at a time.  Only works on Beasts, Humanoids and Critters.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 16777216, 'SpellClassSet': 3, 'SpellLevel': 8, 'SpellPriority': 50, 'SpellVisualID_1': 12978, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 193},
)


cone_of_cold_120 = spell(
    id=120,
    name='Cone of Cold',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=50,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    mana_cost=0,
    mana_cost_pct=25,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=104, apply_aura=AuraType.MOD_DECREASE_SPEED, radius_yards=10.0),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=195, points_per_level=14.1176, die_sides=21, implicit_target_a=104, radius_yards=10.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=104, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127, radius_yards=10.0),
    ],
    spell_icon_id=35,
    notes='EDITED for docs/frost-mage-redesign.md sec 2 (Cone of Cold): 2x damage, 2x spell power coefficient. base_points/die_sides/points_per_level and the legacy EffectBonusMultiplier_2 raw field all doubled in place (this spell predates spell_bonus_data and still uses the per-effect DBC coefficient, so doubling it there - not adding a spell_bonus_data row - is the minimal correct edit). single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 26); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement slowed by $s1%.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Targets in a cone in front of the caster take ${$m2*$<mult>} to ${$M2*$<mult>} Frost damage and are slowed by $s1% for $d.', 'EffectBonusMultiplier_2': 0.428, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 512, 'SpellClassSet': 3, 'SpellDescriptionVariableID': 167, 'SpellLevel': 26, 'SpellPriority': 50, 'SpellVisualID_1': 1007, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


frost_nova_122 = spell(
    id=122,
    name='Frost Nova',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    attributes=1073807360,
    category=35,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=25000,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=18, points_per_level=6.92, die_sides=3, implicit_target_a=22, implicit_target_b=15, radius_yards=10.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.ROOT, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_ROOT, radius_yards=10.0),
    ],
    spell_icon_id=193,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx4': 1073741824, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Frozen in place.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blasts enemies near the caster for ${$m1*$<mult>} to ${$M1*$<mult>} Frost damage and freezes them in place for up to $d.  Damage caused may interrupt the effect.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 0.19300000369548798, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'SpellClassMask_1': 64, 'SpellClassSet': 3, 'SpellDescriptionVariableID': 167, 'SpellLevel': 10, 'SpellPriority': 50, 'SpellVisualID_1': 17, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


slow_fall_130 = spell(
    id=130,
    name='Slow Fall',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=57, apply_aura=105),
    ],
    spell_icon_id=505,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Slows falling speed.', 'BaseLevel': 12, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Slows friendly party or raid target's falling speed for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17056, 'SpellClassMask_1': 2147483648, 'SpellClassMask_2': 8388608, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 12, 'SpellPriority': 50, 'SpellVisualID_1': 63, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


fireball_133 = spell(
    id=133,
    name='Fireball',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=19,
    range_yards=35.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=13, points_per_level=9.2712, die_sides=9, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, points_per_level=0.2881, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
    ],
    spell_icon_id=185,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s2 Fire damage every $t2 seconds.', 'BaseLevel': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Hurls a fiery ball that causes $s1 Fire damage and an additional $o2 Fire damage over $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 24.0, 'SpellClassMask_1': 1, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 67, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


frost_armor_168 = spell(
    id=168,
    name='Frost Armor',
    school=School.FROST,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=24,
    range_yards=0.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=22, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=6136),
    ],
    spell_icon_id=181,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx4': 524288, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Armor by $s1 and may slow attackers.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Armor by $s1.  If an enemy strikes the caster, they may have their movement slowed by $6136s1% and the time between their attacks increased by $6136s2% for $6136d.  Only one type of Armor spell can be active on the Mage at any time.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 40, 'RangeIndex': 1, 'SpellClassMask_1': 34078720, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 124, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


remove_curse_475 = spell(
    id=475,
    name='Remove Curse',
    school=School.ARCANE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=2),
    ],
    spell_icon_id=195,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Removes $m1 Curse from a friendly target.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2147483648, 'SpellClassMask_2': 16777216, 'SpellClassSet': 3, 'SpellLevel': 18, 'SpellVisualID_1': 186, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


khadgar_s_unlocking_491 = spell(
    id=491,
    name="Khadgar's Unlocking",
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.OPEN_LOCK, base_points=14, points_per_level=5.0, implicit_target_a=26, misc_value=1),
    ],
    spell_icon_id=1098,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 18); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 18, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Magically unlocks treasure chests and other locked items.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 5517, 'SpellClassSet': 3, 'SpellLevel': 18, 'SpellVisualID_1': 181, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


fire_ward_543 = spell(
    id=543,
    name='Fire Ward',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=56,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=164, points_per_level=17.75, implicit_target_a=1, apply_aura=69, misc_value=4),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=74, misc_value=4),
    ],
    spell_icon_id=16,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs Fire damage.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Absorbs $s1 Fire damage.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_2': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 8, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 20, 'SpellVisualID_1': 290, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


conjure_food_587 = spell(
    id=587,
    name='Conjure Food',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=40,
    range_yards=0.0,
    effects=[
        Effect(type=24, base_points=1, points_per_level=0.2963, implicit_target_a=1),
    ],
    spell_icon_id=1437,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 6); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 6, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Conjures $s1 $lmuffin:muffins;, providing the mage and $ghis:her; allies with something to eat.\r\n\r\nConjured items disappear if logged out for more than 15 minutes.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 5349, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 3, 'SpellLevel': 6, 'SpellVisualID_1': 563, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


dampen_magic_604 = spell(
    id=604,
    name='Dampen Magic',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=30.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=21, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=263,
    notes='EDITED for docs/frost-mage-redesign.md sec 2: converted from a 10-minute ally buff (MOD_DAMAGE_TAKEN + MOD_HEALING, target=party) to a 2-minute-cooldown, 10-second single-target debuff-taken REDUCTION (single MOD_DAMAGE_PERCENT_TAKEN effect) matching the spec\'s "Target -> Increases/Decreases magic damage taken by X% for 10 seconds". target=ally (implicit_target_a 21, TARGET_UNIT_TARGET_ALLY) - a damage-taken *decrease* is defensive, so unlike Amplify Magic (1008, its enemy-targeted opposite-sign sibling) this one has to be castable on friendlies or the caster can never use it. Was wrongly left at target=enemy (6) alongside Amplify Magic through a copy/paste of that row\'s targeting - see 2026-08-31 fix. The old healing-taken effect is dropped - the spec only mentions damage taken. Grep before touching further: boss_illidari_council.cpp hardcodes a *different* Dampen Magic ID (41478, unaffected by this edit). single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 12); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Decreases magic damage taken by 30%.', 'BaseLevel': 44, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Decreases magic damage taken by the target by 30% for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 8192, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 44, 'SpellVisualID_1': 970, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


sleep_700 = spell(
    id=700,
    name='Sleep',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.SLEEP,
    attributes=1074855936,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=44,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 262144, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Asleep.', 'AuraInterruptFlags': 2, 'BaseLevel': 8, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Puts the enemy target to sleep for up to $d.  Any damage caused will awaken the target.  Only one target can be asleep at a time. Unreliable on targets above level 30.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellLevel': 8, 'SpellVisualID_1': 87, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


conjure_mana_gem_759 = spell(
    id=759,
    name='Conjure Mana Gem',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=75,
    range_yards=0.0,
    effects=[
        Effect(type=24, implicit_target_a=1),
        Effect(type=EffectType.DUMMY, base_points=54413, implicit_target_a=1),
    ],
    spell_icon_id=1036,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 28); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 28, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Conjures a mana agate that can be used to instantly restore $5405s1 mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 5514, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 3, 'SpellLevel': 28, 'SpellVisualID_1': 161, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


amplify_magic_1008 = spell(
    id=1008,
    name='Amplify Magic',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=30.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=6, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=242,
    notes='EDITED for docs/frost-mage-redesign.md sec 2: converted from a 10-minute ally buff (MOD_DAMAGE_TAKEN + MOD_HEALING, target=party) to a 2-minute-cooldown, 10-second enemy debuff (single MOD_DAMAGE_PERCENT_TAKEN effect) matching the spec\'s "Target -> Increases/Decreases magic damage taken by X% for 10 seconds". target=enemy (implicit_target_a 6, TARGET_UNIT_TARGET_ENEMY) - a damage-taken *increase* is an offensive debuff, correctly enemy-only. Its opposite-sign sibling Dampen Magic (604) is a damage-taken *decrease* and must instead be ally-only (see its own row\'s note, fixed 2026-08-31 after it had wrongly inherited this same enemy targeting via copy/paste). The old healing-taken effect is dropped - the spec only mentions damage taken. Grep before touching further: boss_illidari_council.cpp hardcodes a *different* Dampen Magic ID (41478, unaffected by this edit). single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 18); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases magic damage taken by 10%.', 'BaseLevel': 54, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases magic damage taken by the target by 10% for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 8192, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 54, 'SpellVisualID_1': 969, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


sleep_1090 = spell(
    id=1090,
    name='Sleep',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.SLEEP,
    attributes=1074855936,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=90,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=44,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by creature_template_spell, item_spellid, not creature-only',
    raw_overrides={'AttributesEx': 262144, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Asleep.', 'AuraInterruptFlags': 2, 'BaseLevel': 20, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Puts the enemy target to sleep for up to $d.  Any damage caused will awaken the target.  Only one target can be asleep at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellLevel': 20, 'SpellVisualID_1': 87, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


arcane_explosion_1449 = spell(
    id=1449,
    name='Arcane Explosion',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=22,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=31, points_per_level=11.0, die_sides=5, implicit_target_a=22, implicit_target_b=15, radius_yards=10.0),
    ],
    spell_icon_id=122,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 14); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes an explosion of arcane magic around the caster, causing $s1 Arcane damage to all targets within $a1 yards.', 'EffectBonusMultiplier_1': 0.21400000154972076, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 4096, 'SpellClassSet': 3, 'SpellLevel': 14, 'SpellVisualID_1': 965, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


arcane_intellect_1459 = spell(
    id=1459,
    name='Arcane Intellect',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=31,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, points_per_level=0.4915, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=3),
    ],
    spell_icon_id=125,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Intellect by $s1.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the target's Intellect by $s1 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 1024, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellVisualID_1': 158, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


arcane_intellect_1460 = spell(
    id=1460,
    name='Arcane Intellect',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=31,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=3),
    ],
    spell_icon_id=125,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by quest_reward_spell, not creature-only',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Intellect by $s1.', 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the target's Intellect by $s1 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 24, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 1024, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 14, 'SpellVisualID_1': 158, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mana_shield_1463 = spell(
    id=1463,
    name='Mana Shield',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=0.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=119, points_per_level=11.25, implicit_target_a=1, apply_aura=97, misc_value=127),
    ],
    spell_icon_id=209,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs damage, draining mana instead.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Absorbs $s1 damage, draining mana instead.  Drains $e mana per damage absorbed.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.5, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcTypeMask': 139944, 'RangeIndex': 1, 'SpellClassMask_1': 32768, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 20, 'SpellVisualID_1': 968, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blink_1953 = spell(
    id=1953,
    name='Blink',
    school=School.ARCANE,
    attributes=65536,
    category=44,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=15000,
    mana_cost=0,
    mana_cost_pct=21,
    range_yards=0.0,
    duration_ms=1000,
    effects=[
        Effect(type=29, die_sides=0, implicit_target_a=1, implicit_target_b=55, radius_yards=20.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=7),
    ],
    spell_icon_id=1499,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 32768, 'AttributesEx4': 64, 'AttributesEx7': 1048576, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Blinking.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teleports the caster $a1 yards forward, unless something is in the way.  Also frees the caster from stuns and bonds.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 3, 'SpellLevel': 20, 'SpellVisualID_1': 263, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


flamestrike_2120 = spell(
    id=2120,
    name='Flamestrike',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=30,
    range_yards=30.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=51, points_per_level=7.4955, die_sides=17, implicit_target_a=16, radius_yards=5.0),
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=11, points_per_level=1.6591, implicit_target_a=28, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000, radius_yards=5.0),
    ],
    spell_icon_id=37,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 16); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 268435592, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s2 Fire damage every $t2 seconds.', 'BaseLevel': 16, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Calls down a pillar of fire, burning all enemies within the area for $s1 Fire damage and an additional $o2 Fire damage over $d.', 'EffectBonusMultiplier_1': 0.24300000071525574, 'EffectBonusMultiplier_2': 0.12200000137090683, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 4, 'SpellClassSet': 3, 'SpellLevel': 16, 'SpellPriority': 50, 'SpellVisualID_1': 10383, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)


fire_blast_2136 = spell(
    id=2136,
    name='Fire Blast',
    school=School.FIRE,
    attributes=65536,
    category=19,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=12000,
    mana_cost=0,
    mana_cost_pct=21,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=23, points_per_level=16.6852, die_sides=9, implicit_target_a=6),
    ],
    spell_icon_id=12,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 sec 3.1: category cooldown 12 sec (was 8). 'Always critically strikes' is Mage::ApplySpellCritChanceMods (Phase 3) - there is no DBC attribute for a guaranteed crit.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 6, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blasts the enemy for $s1 Fire damage. Always critically strikes.', 'EffectBonusMultiplier_1': 0.42899999022483826, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2, 'SpellClassSet': 3, 'SpellLevel': 6, 'SpellPriority': 50, 'SpellVisualID_1': 143, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


counterspell_2139 = spell(
    id=2139,
    name='Counterspell',
    school=School.ARCANE,
    mechanic=26,
    category=88,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=24000,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=30.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.INTERRUPT_CAST, base_points=-1, implicit_target_a=6),
    ],
    spell_icon_id=17,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 24, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Counters the enemy's spellcast, preventing any spell from that school of magic from being cast for $d.  Generates a high amount of threat.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 16384, 'SpellClassSet': 3, 'SpellLevel': 24, 'SpellPriority': 50, 'SpellVisualID_1': 239},
)


scorch_2948 = spell(
    id=2948,
    name='Scorch',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=52, points_per_level=4.8474, die_sides=13, implicit_target_a=6),
    ],
    spell_icon_id=816,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 22); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 22, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Scorch the enemy for $s1 Fire damage.', 'EffectBonusMultiplier_1': 0.42899999022483826, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 16, 'SpellClassSet': 3, 'SpellLevel': 22, 'SpellPriority': 50, 'SpellVisualID_1': 945, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


teleport_stormwind_3561 = spell(
    id=3561,
    name='Teleport: Stormwind',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    effects=[
        Effect(type=5, base_points=-1, implicit_target_a=1, implicit_target_b=17),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=1491,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 1073741824, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teleports the caster to Stormwind.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 17031, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 263, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


teleport_ironforge_3562 = spell(
    id=3562,
    name='Teleport: Ironforge',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    effects=[
        Effect(type=5, base_points=-1, implicit_target_a=1, implicit_target_b=17),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=1489,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 1073741824, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teleports the caster to Ironforge.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 17031, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 263, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


teleport_undercity_3563 = spell(
    id=3563,
    name='Teleport: Undercity',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    effects=[
        Effect(type=5, base_points=-1, implicit_target_a=1, implicit_target_b=17),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=1493,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 1073741824, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teleports the caster to Undercity.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 17031, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 263, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


teleport_darnassus_3565 = spell(
    id=3565,
    name='Teleport: Darnassus',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    effects=[
        Effect(type=5, base_points=-1, implicit_target_a=1, implicit_target_b=17),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=1486,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 1073741824, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teleports the caster to Darnassus.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 17031, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 30, 'SpellPriority': 50, 'SpellVisualID_1': 263, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


teleport_thunder_bluff_3566 = spell(
    id=3566,
    name='Teleport: Thunder Bluff',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    effects=[
        Effect(type=5, base_points=-1, implicit_target_a=1, implicit_target_b=17),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=1492,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 1073741824, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teleports the caster to Thunder Bluff.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 17031, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 30, 'SpellPriority': 50, 'SpellVisualID_1': 263, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


teleport_orgrimmar_3567 = spell(
    id=3567,
    name='Teleport: Orgrimmar',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    effects=[
        Effect(type=5, base_points=-1, implicit_target_a=1, implicit_target_b=17),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=1490,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 1073741824, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teleports the caster to Orgrimmar.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 17031, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 263, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


arcane_missiles_5143 = spell(
    id=5143,
    name='Arcane Missiles',
    school=School.ARCANE,
    attributes=536936704,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=31,
    range_yards=30.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=arcane_missile_7268.id),
    ],
    spell_icon_id=225,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80 | Bugfix (2026-09-09): duration_ms was left at rank 1\'s own value (3000 = 3 ticks) instead of being carried over from max rank (25345, this file - duration_ms 5000 = 5 ticks) like coefficient/cast_time_ms/mana_cost_pct were - rank 1 only fired 3 of the intended 5 missiles. Fixed to 5000.\n5405,Replenish Mana,1,0,0,0,100,0,0,60000,0,0,0,0.0,,,{""amplitude"": 0',
    raw_overrides={'AttributesEx': 335561860, 'AttributesEx4': 134217728, 'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 8, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Launches Arcane Missiles at the enemy, causing $7268s1 Arcane damage every $5143t2 sec for $5143d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2048, 'SpellClassSet': 3, 'SpellLevel': 8, 'SpellPriority': 50, 'SpellVisualID_1': 262, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


conjure_water_5504 = spell(
    id=5504,
    name='Conjure Water',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=40,
    range_yards=0.0,
    effects=[
        Effect(type=24, base_points=1, points_per_level=0.1429, implicit_target_a=1),
    ],
    spell_icon_id=1357,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 4, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Conjures $s1 $lbottle:bottles; of water, providing the mage and $ghis:her; allies with something to drink.\r\n\r\nConjured items disappear if logged out for more than 15 minutes.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 5350, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 3, 'SpellLevel': 4, 'SpellVisualID_1': 564, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mage_armor_6117 = spell(
    id=6117,
    name='Mage Armor',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=26,
    range_yards=0.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=22, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=134),
    ],
    spell_icon_id=1711,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 34); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Resistance to all magic schools increased by $s1 and allows $s2% of your mana regeneration to continue while casting.', 'BaseLevel': 34, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your resistance to all magic by $s1 and allows $s2% of your mana regeneration to continue while casting.  Only one type of Armor spell can be active on the Mage at any time.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 3, 'SpellLevel': 34, 'SpellPriority': 50, 'SpellVisualID_1': 284, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


frost_ward_6143 = spell(
    id=6143,
    name='Frost Ward',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=56,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=164, points_per_level=18.6842, implicit_target_a=1, apply_aura=69, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=74, misc_value=16),
    ],
    spell_icon_id=501,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 22); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs Frost damage.', 'BaseLevel': 22, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Absorbs $s1 Frost damage.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_2': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 256, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 22, 'SpellVisualID_1': 291, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ice_armor_7302 = spell(
    id=7302,
    name='Ice Armor',
    school=School.FROST,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=24,
    range_yards=0.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=289, implicit_target_a=1, apply_aura=22, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=7321),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=22, misc_value=16),
    ],
    spell_icon_id=181,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx4': 524288, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Armor by $s1, Frost resistance by $s3 and may slow attackers.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Armor by $s1 and Frost resistance by $s3.   If an enemy strikes the caster, they may have their movement slowed by $7321s1% and the time between their attacks increased by $7321s2% for $7321d.  Only one type of Armor spell can be active on the Mage at any time.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 40, 'RangeIndex': 1, 'SpellClassMask_1': 34078720, 'SpellClassSet': 3, 'SpellLevel': 30, 'SpellPriority': 50, 'SpellVisualID_1': 706, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


replenish_mana_10052 = spell(
    id=10052,
    name='Replenish Mana',
    school=School.NORMAL,
    category=100,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=584, die_sides=31, implicit_target_a=1),
    ],
    spell_icon_id=283,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by item_spellid2, not creature-only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 38, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restores $s1 mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 256, 'SpellClassSet': 3, 'SpellLevel': 38, 'SpellVisualID_1': 240},
)


replenish_mana_10057 = spell(
    id=10057,
    name='Replenish Mana',
    school=School.NORMAL,
    category=100,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=828, die_sides=43, implicit_target_a=1),
    ],
    spell_icon_id=283,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by item_spellid2, not creature-only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 48, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restores $s1 mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 256, 'SpellClassSet': 3, 'SpellLevel': 48, 'SpellVisualID_1': 240},
)


replenish_mana_10058 = spell(
    id=10058,
    name='Replenish Mana',
    school=School.NORMAL,
    category=100,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=1072, die_sides=55, implicit_target_a=1),
    ],
    spell_icon_id=283,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by item_spellid2, not creature-only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 58, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restores $s1 mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 256, 'SpellClassSet': 3, 'SpellLevel': 58, 'SpellVisualID_1': 240},
)


portal_stormwind_10059 = spell(
    id=10059,
    name='Portal: Stormwind',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=10.0,
    duration_ms=60000,
    effects=[
        Effect(type=50, base_points=-1, implicit_target_a=47, misc_value=176296, radius_yards=3.0),
    ],
    spell_icon_id=1482,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566528, 'AttributesEx3': 1073741824, 'AttributesEx4': 134217728, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a portal, teleporting group members that use it to Stormwind.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17032, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 2186, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


conjure_water_10140 = spell(
    id=10140,
    name='Conjure Water',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=40,
    range_yards=0.0,
    effects=[
        Effect(type=24, base_points=9, points_per_level=2.0, implicit_target_a=1),
    ],
    spell_icon_id=1687,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by quest_reward_display, not creature-only',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Conjures $s1 $lbottle:bottles; of crystal water, providing the mage and $ghis:her; allies with something to drink.\r\n\r\nConjured items disappear if logged out for more than 15 minutes.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 8079, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 65, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 3, 'SpellLevel': 60, 'SpellVisualID_1': 564, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


portal_ironforge_11416 = spell(
    id=11416,
    name='Portal: Ironforge',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=10.0,
    duration_ms=60000,
    effects=[
        Effect(type=50, base_points=-1, implicit_target_a=47, misc_value=176497, radius_yards=3.0),
    ],
    spell_icon_id=1480,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566528, 'AttributesEx3': 1073741824, 'AttributesEx4': 134217728, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a portal, teleporting group members that use it to Ironforge.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17032, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 2738, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


portal_orgrimmar_11417 = spell(
    id=11417,
    name='Portal: Orgrimmar',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=10.0,
    duration_ms=60000,
    effects=[
        Effect(type=50, base_points=-1, implicit_target_a=47, misc_value=176499, radius_yards=3.0),
    ],
    spell_icon_id=1481,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566528, 'AttributesEx3': 1073741824, 'AttributesEx4': 134217728, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a portal, teleporting group members that use it to Orgrimmar.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17032, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 2739, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


portal_undercity_11418 = spell(
    id=11418,
    name='Portal: Undercity',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=10.0,
    duration_ms=60000,
    effects=[
        Effect(type=50, base_points=-1, implicit_target_a=47, misc_value=176501, radius_yards=3.0),
    ],
    spell_icon_id=1484,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566528, 'AttributesEx3': 1073741824, 'AttributesEx4': 134217728, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a portal, teleporting group members that use it to Undercity.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17032, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 2741, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


portal_darnassus_11419 = spell(
    id=11419,
    name='Portal: Darnassus',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=10.0,
    duration_ms=60000,
    effects=[
        Effect(type=50, base_points=-1, implicit_target_a=47, misc_value=176498, radius_yards=3.0),
    ],
    spell_icon_id=1479,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566528, 'AttributesEx3': 1073741824, 'AttributesEx4': 134217728, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a portal, teleporting group members that use it to Darnassus.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17032, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 2254, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


portal_thunder_bluff_11420 = spell(
    id=11420,
    name='Portal: Thunder Bluff',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=10.0,
    duration_ms=60000,
    effects=[
        Effect(type=50, base_points=-1, implicit_target_a=47, misc_value=176500, radius_yards=3.0),
    ],
    spell_icon_id=1483,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566528, 'AttributesEx3': 1073741824, 'AttributesEx4': 134217728, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a portal, teleporting group members that use it to Thunder Bluff.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17032, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 2740, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


evocation_12051 = spell(
    id=12051,
    name='Evocation',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=21, amplitude=2000),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=20, amplitude=2000),
    ],
    spell_icon_id=47,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 64, 'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Gain $s1% of total mana every $t1 sec.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While channeling this spell, you gain $o1% of your total mana over $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 67108864, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 2756, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


arcane_brilliance_23028 = spell(
    id=23028,
    name='Arcane Brilliance',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=81,
    range_yards=40.0,
    duration_ms=3600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=30, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=3, radius_yards=100.0),
    ],
    spell_icon_id=1694,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 56); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Intellect by $s1.', 'BaseLevel': 56, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Infuses all  party and raid members with brilliance, increasing their Intellect by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 1024, 'SpellClassSet': 3, 'SpellLevel': 56, 'SpellVisualID_1': 158, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


frostbolt_25304 = spell(
    id=25304,
    name='Frostbolt',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=30.0,
    duration_ms=9000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-41, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=514, points_per_level=3.200000047683716, die_sides=41, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=188,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by item_spellid2, not creature-only',
    raw_overrides={'AttributesEx6': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement slowed by $s1%.', 'BaseLevel': 60, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Launches a bolt of frost at the enemy, causing ${$m2*$<mult>} to ${$M2*$<mult>} Frost damage and slowing movement speed by $s1% for $d.', 'EffectBonusMultiplier_2': 0.8569999933242798, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 64, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 11', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 28.0, 'SpellClassMask_1': 32, 'SpellClassSet': 3, 'SpellDescriptionVariableID': 167, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 13, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


fireball_25306 = spell(
    id=25306,
    name='Fireball',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=3500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=19,
    range_yards=35.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=595, points_per_level=3.799999952316284, die_sides=165, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=18, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
    ],
    spell_icon_id=185,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by item_spellid2, not creature-only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s2 Fire damage every $t2 seconds.', 'BaseLevel': 60, 'CastingTimeIndex': 22, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Hurls a fiery ball that causes $s1 Fire damage and an additional $o2 Fire damage over $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 64, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 12', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 24.0, 'SpellClassMask_1': 1, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 67, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


arcane_missiles_25345 = spell(
    id=25345,
    name='Arcane Missiles',
    school=School.ARCANE,
    attributes=536936704,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=31,
    range_yards=30.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=25346),
    ],
    spell_icon_id=225,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by item_spellid2, not creature-only',
    raw_overrides={'AttributesEx': 335561860, 'AttributesEx4': 134217728, 'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Launches Arcane Missiles at the enemy, causing $25346s1 Arcane damage every $25345t2 sec for $25345d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 64, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 8', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2048, 'SpellClassSet': 3, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 262, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


conjure_water_27090 = spell(
    id=27090,
    name='Conjure Water',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=40,
    range_yards=0.0,
    effects=[
        Effect(type=24, base_points=9, points_per_level=2.0, implicit_target_a=1),
    ],
    spell_icon_id=1844,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by item_spellid2, not creature-only',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 70, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Conjures $s1 $lskin:skin; of glacier water, providing the mage and $ghis:her; allies with something to drink.\r\n\r\nConjured items disappear if logged out for more than 15 minutes.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 22018, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 75, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 3, 'SpellLevel': 70, 'SpellVisualID_1': 564, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


replenish_mana_27103 = spell(
    id=27103,
    name='Replenish Mana',
    school=School.NORMAL,
    category=100,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=2339, die_sides=121, implicit_target_a=1),
    ],
    spell_icon_id=283,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by item_spellid2, not creature-only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 68, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restores $s1 mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 256, 'SpellClassSet': 3, 'SpellLevel': 68, 'SpellVisualID_1': 240},
)


arcane_intellect_27126 = spell(
    id=27126,
    name='Arcane Intellect',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=31,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=3),
    ],
    spell_icon_id=125,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by item_requiredspell, not creature-only',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Intellect by $s1.', 'BaseLevel': 70, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the target's Intellect by $s1 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 1024, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 70, 'SpellVisualID_1': 158, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


arcane_brilliance_27127 = spell(
    id=27127,
    name='Arcane Brilliance',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=81,
    range_yards=40.0,
    duration_ms=3600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=3, radius_yards=100.0),
    ],
    spell_icon_id=1694,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by item_requiredspell, item_spellid2, not creature-only',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Intellect by $s1.', 'BaseLevel': 70, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Infuses all  party and raid members with brilliance, increasing their Intellect by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17020, 'SpellClassMask_1': 1024, 'SpellClassSet': 3, 'SpellLevel': 70, 'SpellVisualID_1': 158, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


frost_ward_28609 = spell(
    id=28609,
    name='Frost Ward',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=56,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=874, implicit_target_a=1, apply_aura=69, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=74, misc_value=16),
    ],
    spell_icon_id=501,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by item_spellid2, not creature-only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs Frost damage.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Absorbs $s1 Frost damage.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_2': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 69, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 256, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 60, 'SpellVisualID_1': 291, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


conjure_food_28612 = spell(
    id=28612,
    name='Conjure Food',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=40,
    range_yards=0.0,
    effects=[
        Effect(type=24, base_points=9, points_per_level=2.0, implicit_target_a=1),
    ],
    spell_icon_id=1911,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by item_spellid2, not creature-only',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Conjures $s1 $lcinnamon roll:cinnamon rolls;, providing the mage and $ghis:her; allies with something to eat.\r\n\r\nConjured items disappear if logged out for more than 15 minutes.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 22895, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 65, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 3, 'SpellLevel': 60, 'SpellVisualID_1': 563, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


spellsteal_30449 = spell(
    id=30449,
    name='Spellsteal',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=20,
    range_yards=30.0,
    effects=[
        Effect(type=126, implicit_target_a=6, misc_value=1),
    ],
    spell_icon_id=1961,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 70, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Steals a beneficial magic effect from the target.  This effect lasts a maximum of 2 min.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 16, 'SpellClassSet': 3, 'SpellLevel': 70, 'SpellVisualID_1': 7747, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


arcane_blast = spell(
    id=30451,
    name='Arcane Blast',
    school=School.ARCANE,
    attributes=262144,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=60, points_per_level=15.4, die_sides=137, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=1, trigger_spell=arcane_blast_debuff.id),
    ],
    spell_icon_id=2294,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md): learn level dropped 64->10 ("Now learnable at level 10"). Placeholder scaling curve rebased to the new low anchor - base_points 60 (live 61) at level 10, points_per_level 15.4 so the value at level 80 (~1139) roughly matches the pre-rework level-84 total (842 + 16*18.55 ~= 1139) rather than being invented from scratch. Flagged in Open Items as needing real tuning during the Phase 4 playtest, per the user\'s resolution ("placeholder now, tune via playtest").',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 10, 'CastingTimeIndex': 19, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blasts the target with energy, dealing $s1 Arcane damage.  Each time you cast Arcane Blast, the damage of all Arcane spells is increased by $36032s1% and mana cost of Arcane Blast is increased by $36032s2%.  Effect stacks up to $36032u times and lasts $36032d or until any Arcane damage spell except Arcane Blast is cast.', 'EffectBonusMultiplier_1': 0.7139999866485596, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 536870912, 'EffectSpellClassMaskC_1': 536870912, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 536870912, 'SpellClassSet': 3, 'SpellLevel': 10, 'SpellVisualID_1': 7749, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ice_lance_30455 = spell(
    id=30455,
    name='Ice Lance',
    school=School.FROST,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=45, points_per_level=2.5, die_sides=10, implicit_target_a=6),
    ],
    spell_icon_id=186,
    notes='EDITED for docs/frost-mage-redesign.md sec 2 (Ice Lance): "Now learnable at level 15, will need to create scaling for it." BaseLevel/SpellLevel 66->15; base_points/points_per_level rescaled to keep the same level-80 ceiling the old 66-anchored single-rank bootstrap landed on (~217 before spell power) - a real balance pass should replace this placeholder slope. single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 66); RealPointsPerLevel from rank1→top rank\'s own top level (82, chain has a gap at 60) slope (anchor rank 42914, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (42914, rank 3); MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 15, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals ${$m1*$<mult>} to ${$M1*$<mult>} Frost damage to an enemy target.  Causes triple damage against Frozen targets.', 'EffectBonusMultiplier_1': 0.14300000667572021, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 38.0, 'SpellClassMask_1': 131072, 'SpellClassSet': 3, 'SpellDescriptionVariableID': 167, 'SpellLevel': 15, 'SpellVisualID_1': 7906, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


molten_armor_30482 = spell(
    id=30482,
    name='Molten Armor',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=28,
    range_yards=0.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=molten_armor_34913.id),
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=197),
        Effect(type=EffectType.APPLY_AURA, base_points=34, implicit_target_a=1, apply_aura=220, misc_value=1792),
    ],
    spell_icon_id=2307,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 62); RealPointsPerLevel from rank1→top rank's own top level (80, chain has a gap at 60) slope (anchor rank 43046, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (43046, rank 3); MaxLevel set to 80",
    raw_overrides={'AttributesEx4': 524288, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Causes $34913s1 Fire damage to attackers.  Chance to receive a critical hit reduced by $s2%.  Critical strike rating increased by $s3% of Spirit.', 'BaseLevel': 62, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes $34913s1 Fire damage when hit, increases your critical strike rating by $30482s3% of your Spirit, and reduces the chance you are critically hit by $30482s2%.  Only one type of Armor spell can be active on the Mage at any time.  Lasts $30482d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_3': 4, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 139944, 'RangeIndex': 1, 'SpellClassMask_1': 262144, 'SpellClassSet': 3, 'SpellLevel': 62, 'SpellPriority': 50, 'SpellVisualID_1': 7757, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


portal_exodar_32266 = spell(
    id=32266,
    name='Portal: Exodar',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=10.0,
    duration_ms=60000,
    effects=[
        Effect(type=50, base_points=-1, implicit_target_a=47, misc_value=182351, radius_yards=3.0),
    ],
    spell_icon_id=2122,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566528, 'AttributesEx3': 1073741824, 'AttributesEx4': 134217728, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a portal, teleporting group members that use it to Exodar.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17032, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 2738, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


portal_silvermoon_32267 = spell(
    id=32267,
    name='Portal: Silvermoon',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=10.0,
    duration_ms=60000,
    effects=[
        Effect(type=50, base_points=-1, implicit_target_a=47, misc_value=182352, radius_yards=3.0),
    ],
    spell_icon_id=2123,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566528, 'AttributesEx3': 1073741824, 'AttributesEx4': 134217728, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a portal, teleporting group members that use it to Silvermoon.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17032, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 2738, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


teleport_exodar_32271 = spell(
    id=32271,
    name='Teleport: Exodar',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    effects=[
        Effect(type=5, base_points=-1, implicit_target_a=1, implicit_target_b=17),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=2124,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 1073741824, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teleports the caster to Exodar.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 17031, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 263, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


teleport_silvermoon_32272 = spell(
    id=32272,
    name='Teleport: Silvermoon',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    effects=[
        Effect(type=5, base_points=-1, implicit_target_a=1, implicit_target_b=17),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=2125,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 1073741824, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teleports the caster to Silvermoon.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 17031, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 263, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


teleport_shattrath_33690 = spell(
    id=33690,
    name='Teleport: Shattrath',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    effects=[
        Effect(type=5, base_points=-1, implicit_target_a=1, implicit_target_b=17),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=2175,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 1073741824, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teleports the caster to Shattrath.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 17031, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 263, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


portal_shattrath_33691 = spell(
    id=33691,
    name='Portal: Shattrath',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=10.0,
    duration_ms=60000,
    effects=[
        Effect(type=50, base_points=-1, implicit_target_a=47, misc_value=183384, radius_yards=3.0),
    ],
    spell_icon_id=2174,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566528, 'AttributesEx3': 1073741824, 'AttributesEx4': 134217728, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 65, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a portal, teleporting group members that use it to Shattrath.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17032, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 65, 'SpellPriority': 50, 'SpellVisualID_1': 2738, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


conjure_food_33717 = spell(
    id=33717,
    name='Conjure Food',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=40,
    range_yards=0.0,
    effects=[
        Effect(type=24, base_points=9, points_per_level=2.0, implicit_target_a=1),
    ],
    spell_icon_id=1842,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by item_spellid2, not creature-only',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 70, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Conjures $s1 $lcroissant:croissants;, providing the mage and $ghis:her; allies with something to eat.\r\n\r\nConjured items disappear if logged out for more than 15 minutes.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 22019, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 75, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 8', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 3, 'SpellLevel': 70, 'SpellVisualID_1': 563, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


teleport_shattrath_35715 = spell(
    id=35715,
    name='Teleport: Shattrath',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    effects=[
        Effect(type=5, base_points=-1, implicit_target_a=1, implicit_target_b=17),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=2175,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 1073741824, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teleports the caster to Shattrath.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 17031, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 263, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


portal_shattrath_35717 = spell(
    id=35717,
    name='Portal: Shattrath',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=10.0,
    duration_ms=60000,
    effects=[
        Effect(type=50, base_points=-1, implicit_target_a=47, misc_value=184594, radius_yards=3.0),
    ],
    spell_icon_id=2174,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566528, 'AttributesEx3': 1073741824, 'AttributesEx4': 134217728, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 65, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a portal, teleporting group members that use it to Shattrath.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17032, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 65, 'SpellPriority': 50, 'SpellVisualID_1': 2738, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


conjure_refreshment_42955 = spell(
    id=42955,
    name='Conjure Refreshment',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=40,
    range_yards=0.0,
    effects=[
        Effect(type=24, base_points=19, implicit_target_a=1),
    ],
    spell_icon_id=2966,
    notes="overridden post-bootstrap (playtest bugfix): the single-rank bootstrap kept rank 1's original learn level (75, since Conjure Refreshment replaces Conjure Food/Water - see docs/frost-mage-redesign.md sec 2 - which were learnable around level 8-20). BaseLevel/SpellLevel dropped to 10 so the spell is actually learnable early, matching the retired Conjure Food/Water's role; trainer_spell.ReqLevel updated to match in the accompanying pending SQL. RealPointsPerLevel from rank1→top rank's own top level (80, chain has a gap at 60) slope (anchor rank 42956, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (42956, rank 2); MaxLevel set to 80",
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Conjures $s1 Mana Pies providing the mage and $ghis:her; allies with something to eat.\r\n\r\nConjured items disappear if logged out for more than 15 minutes.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 43518, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 3, 'SpellLevel': 10, 'SpellVisualID_1': 563, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


replenish_mana_42987 = spell(
    id=42987,
    name='Replenish Mana',
    school=School.NORMAL,
    category=100,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=3329, die_sides=171, implicit_target_a=1),
    ],
    spell_icon_id=283,
    notes='pulled from existing data | superseded rank kept in mage.csv: still referenced by item_spellid2, not creature-only',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 77, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restores $s1 mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 256, 'SpellClassSet': 3, 'SpellLevel': 77, 'SpellVisualID_1': 240},
)


ritual_of_refreshment_43987 = spell(
    id=43987,
    name='Ritual of Refreshment',
    school=School.ARCANE,
    attributes=33619968,
    category=1177,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=300000,
    mana_cost=0,
    mana_cost_pct=80,
    range_yards=30.0,
    duration_ms=60000,
    effects=[
        Effect(type=50, implicit_target_a=47, misc_value=186811, radius_yards=5.0),
    ],
    spell_icon_id=2267,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 70); RealPointsPerLevel from rank1→top rank's own top level (80, chain has a gap at 60) slope (anchor rank 58659, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (58659, rank 2); MaxLevel set to 80",
    raw_overrides={'AttributesEx': 131076, 'AttributesEx3': 1073741824, 'AttributesEx5': 8194, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 70, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 48142, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Begins a ritual that creates a refreshment table.  Raid members can click the table to acquire Conjured Mana Biscuits.  The tables lasts for $43985d or 50 charges.  Requires the caster and 2 additional party members to complete the ritual.  In order to participate, all players must right-click the refreshment portal and not move until the ritual is complete.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 2, 'Reagent_1': 17020, 'SpellClassSet': 3, 'SpellLevel': 70, 'SpellPriority': 50, 'SpellVisualID_1': 9860, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


frostfire_bolt_44614 = spell(
    id=44614,
    name='Frostfire Bolt',
    school=School.FIRE | School.FROST,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=40.0,
    duration_ms=9000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-41, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=628, points_per_level=12.3333, die_sides=103, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=19, points_per_level=1.1111, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    spell_icon_id=2946,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 75); RealPointsPerLevel from rank1→top rank's own top level (84, chain has a gap at 60) slope (anchor rank 47610, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (47610, rank 2); MaxLevel set to 80",
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement slowed by $s1%.  $s3 Frostfire damage every $t3 sec.', 'BaseLevel': 75, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Launches a bolt of frostfire at the enemy, causing ${$m2*$<mult>} to ${$M2*$<mult>} Frostfire damage, slowing movement speed by $s1% and causing an additional $o3 Frostfire damage over $d. This spell will be checked against the lower of the target's Frost and Fire resists.", 'EffectBonusMultiplier_2': 0.8569999933242798, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 28.0, 'SpellClassMask_2': 4096, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellDescriptionVariableID': 167, 'SpellLevel': 75, 'SpellPriority': 50, 'SpellVisualID_1': 12253, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ice_block_45438 = spell(
    id=45438,
    name='Ice Block',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    mechanic=29,
    attributes=327680,
    category=37,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=300000,
    mana_cost=15,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_STUN),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=39, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=39, misc_value=126),
    ],
    spell_icon_id=14,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 32768, 'AttributesEx2': 2097152, 'AttributesEx7': 1048576, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to all attacks and spells.  Cannot attack, move or use spells.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You become encased in a block of ice, protecting you from all physical attacks and spells for $d, but during that time you cannot attack, move or cast spells.  Also causes Hypothermia, preventing you from recasting Ice Block for $41425d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeCasterAuraSpell': 41425, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 128, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 30, 'SpellVisualID_1': 4325, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


teleport_stonard_49358 = spell(
    id=49358,
    name='Teleport: Stonard',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    effects=[
        Effect(type=5, base_points=-1, implicit_target_a=1, implicit_target_b=17),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=2660,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 1073741824, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 35, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teleports the caster to Stonard.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 17031, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 35, 'SpellPriority': 50, 'SpellVisualID_1': 263, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


teleport_theramore_49359 = spell(
    id=49359,
    name='Teleport: Theramore',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    effects=[
        Effect(type=5, base_points=-1, implicit_target_a=1, implicit_target_b=17),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=2661,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 1073741824, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 35, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teleports the caster to Theramore.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 17031, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 35, 'SpellPriority': 50, 'SpellVisualID_1': 263, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


portal_theramore_49360 = spell(
    id=49360,
    name='Portal: Theramore',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=850,
    mana_cost_pct=0,
    range_yards=10.0,
    duration_ms=60000,
    effects=[
        Effect(type=50, base_points=-1, implicit_target_a=47, misc_value=189993, radius_yards=3.0),
    ],
    spell_icon_id=2662,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566528, 'AttributesEx3': 1073741824, 'AttributesEx4': 134217728, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 35, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a portal, teleporting group members that use it to Theramore.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17032, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 35, 'SpellPriority': 50, 'SpellVisualID_1': 11460, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


portal_stonard_49361 = spell(
    id=49361,
    name='Portal: Stonard',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=10.0,
    duration_ms=60000,
    effects=[
        Effect(type=50, base_points=-1, implicit_target_a=47, misc_value=189994, radius_yards=3.0),
    ],
    spell_icon_id=2659,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566528, 'AttributesEx4': 134217728, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 35, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a portal, teleporting group members that use it to Stonard.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17032, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 35, 'SpellPriority': 50, 'SpellVisualID_1': 2739, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


teleport_dalaran_53140 = spell(
    id=53140,
    name='Teleport: Dalaran',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    effects=[
        Effect(type=5, base_points=-1, implicit_target_a=1, implicit_target_b=17),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=3167,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 1073741824, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 71, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teleports the caster to Dalaran.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 17031, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 71, 'SpellPriority': 50, 'SpellVisualID_1': 263, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


portal_dalaran_53142 = spell(
    id=53142,
    name='Portal: Dalaran',
    school=School.ARCANE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=10.0,
    duration_ms=60000,
    effects=[
        Effect(type=50, base_points=-1, implicit_target_a=47, misc_value=191164, radius_yards=3.0),
    ],
    spell_icon_id=3051,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566528, 'AttributesEx3': 1073741824, 'AttributesEx4': 134217728, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 74, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a portal, teleporting group members that use it to Dalaran.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17032, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 74, 'SpellPriority': 50, 'SpellVisualID_1': 2738, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mirror_image_55342 = spell(
    id=55342,
    name='Mirror Image',
    school=School.ARCANE,
    attributes=2147549184,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-90000001, implicit_target_a=1, apply_aura=103),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=2, implicit_target_a=1, trigger_spell=58832),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=226, amplitude=1000, trigger_spell=58836),
    ],
    spell_icon_id=331,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx5': 402653184, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Copies of the caster that attack on their own.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 80, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Creates $<images> copies of the caster nearby, which cast spells and attack the mage's enemies.  Lasts $55342d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 32, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 2097152, 'SpellClassSet': 3, 'SpellDescriptionVariableID': 86, 'SpellLevel': 80, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


glacial_spike_200002 = spell(
    id=200002,
    name='Glacial Spike',
    school=School.FROST,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=6),
    ],
    spell_icon_id=1236,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 1, Glacial Spike): the button/cast-bar spell only now - no damage and no travel of its own (effect1 is a no-op DUMMY, Speed removed). On hit (instant, since this row no longer travels), spell_mage_glacial_spike::LaunchImpact (spell_mage.cpp) immediately casts the real damage-dealing 200027 at the real target - no post-cast delay. Playtest feedback (2026-09-18, first pass): the icicles-converging visual originally played as a ~800ms post-cast cosmetic ramp (200025 then 200026, both since orphaned - see their own notes) after the cast bar had already finished, which looked wrong; moved to a WorldEffect on this spell's own CastKit instead (SpellVisualID_1 90005 -> KIT_GLACIALSPIKE_CAST, patch_mage_vfx_models.py). Playtest feedback (2026-09-18, second pass): that WorldEffect (cfx_mage_glacialspike_convergingmissiles) still played at cast completion together with the bolt launch, not throughout the cast - the asset itself was wrong, not the mechanism (verified against real stock data that CastKit's WorldEffect sustains for a full multi-second cast bar, e.g. boss telegraphs like Ground Tremor/Staggering Roar/Dreadful Roar). Swapped WorldEffect to cfx_mage_glacialspike_dummyholdmissile (Ascension's naming suggests a held/loop state model vs. convergingmissiles' one-shot 'snap together' transition) and added LeftHandEffect=Ice Cast Low Hand (stock effect 421, the same one Frostbolt's own real CastKit uses for its live-proven 'hand glows blue for the whole cast' - guarantees a working glow alongside the untested custom RightHandEffect). 5-Icicle requirement still gates the cast here (OnCheckCast); Icicle/Fingers-of-Frost consumption and the Arctic Winds shatter-cleave live on 200027 (spell_mage_glacial_spike_impact), since that's the stage that represents the spell actually landing. SpellIconID 1236 (Spell_Frost_IceShard, from apps/dbc-tools/var/spell_icon_names.csv). SpellVisualID_1 90005 (patch_mage_vfx_models.py): a real CastKit (not a PrecastKit) since this is the one spell in this VFX pass with an actual 2.5s cast bar - LeftHandEffect=Ice Cast Low Hand (stock 421) + RightHandEffect=cfx_mage_glacialspike_statehand + WorldEffect=cfx_mage_glacialspike_dummyholdmissile, AnimID/SoundID reused verbatim from stock kit 172 (spell 7479's own CastKit).",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'EquippedItemClass': -1, 'PreventionType': 1, 'ProcChance': 101, 'StartRecoveryCategory': 133, 'SpellPriority': 50, 'Description_Lang_enUS': 'Consumes all Icicles to hurl a massive spike of ice at the target, dealing Frost damage.', 'InterruptFlags': 15, 'ChannelInterruptFlags': 0, 'FacingCasterFlags': 1, 'DefenseType': 1, 'SpellVisualID_1': 90005},
)


flurry_200004 = spell(
    id=200004,
    name='Flurry',
    school=School.FROST,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=15000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=6),
    ],
    spell_icon_id=187,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 1, Flurry): the button spell only now - no damage and no travel of its own (effect1 is a no-op DUMMY, Speed removed). Playtest feedback (2026-09-18): originally 3 SPELL_EFFECT_SCHOOL_DAMAGE effects landing simultaneously on this one instant cast (one visible missile carrying 3x damage); redesigned into 3 separate sequential bolts, 0.2s apart, via spell_mage_flurry::FireBolts (spell_mage.cpp) casting the new 200037 (Flurry Bolt) three times on OnHit - see 200037's own notes for the damage/bonus split and the Shattering Cold timing this enabled. Generates no Icicles and can't trigger Fingers of Frost (spec) - true for free today since Icicle generation and FoF's proc are both keyed off other spell IDs (see spell_mage.cpp) and were never wired to this one; the FoF exclusion will need an explicit family-mask check once the real Row 3 Fingers of Frost proc (not yet built) replaces the legacy sync mechanism. SpellIconID 187 (Spell_Frost_ChillingBlast, apps/dbc-tools/var/spell_icon_names.csv). SpellVisualID_1 90009 (patch_mage_vfx_models.py): now just PrecastKit=KIT_FROST_PRECAST_HAND (the cast flourish) - the missile/impact visual moved to 200037's own SpellVisualID_1 (90010) since that's what actually travels and hits now.",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Launches a flurry of ice bolts at the target, dealing Frost damage and applying Shattering Cold.', 'EquippedItemClass': -1, 'PreventionType': 1, 'ProcChance': 101, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellPriority': 50, 'InterruptFlags': 15, 'FacingCasterFlags': 1, 'DefenseType': 1, 'SpellVisualID_1': 90009},
)


frozen_orb_200007 = spell(
    id=200007,
    name='Frozen Orb',
    school=School.FROST,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=45000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=20,
    effects=[
        Effect(type=77, implicit_target_a=1),
    ],
    spell_icon_id=2132,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 1, Frozen Orb): SPELL_EFFECT_SCRIPT_EFFECT (type 77), self-targeted, instant, 45s cooldown, 20% of base mana (mana_cost_pct). No damage or aura of its own - spell_mage_frozen_orb (spell_mage.cpp) summons the orb trigger creature (NPC_MAGE_FROZEN_ORB, 300001) at the caster\'s position on hit; the creature\'s own AI (npc_mage_frozen_orb) drives movement, the periodic pulse (200009 -> 200008), and the Fingers of Frost grant chain. See docs/frost-mage-implementation-plan.md\'s dedicated "Frozen Orb Implementation" section for the full design and gotchas (faction, movement, damage attribution). Arctic Reach (travel-distance talent) is not yet built - see the Frost talent tree item in docs/frost-mage-handoff.md. SpellIconID 2132 (Spell_Frost_FrozenCore, apps/dbc-tools/var/spell_icon_names.csv - the real spell\'s own icon). SpellVisualID_1 90004 (patch_mage_vfx_models.py): PrecastKit-only flourish (stock kit 171) on this self-targeted instant cast - separate from the orb creature\'s own display model, which is CreatureDisplayInfo 90002 (Mage_FrostOrb_Orb, swapped from the previous 90001/IceNuke_Missile reuse via pending SQL) on creature_template_model for entry 300001. See docs/reworks/fire-mage-meteor-vfx.md.',
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Launches a frozen orb forward, dealing Frost damage to enemies in its path and chilling them.  Each enemy struck has a chance to grant you Fingers of Frost.', 'EquippedItemClass': -1, 'PreventionType': 1, 'ProcChance': 101, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellPriority': 50, 'InterruptFlags': 15, 'SpellVisualID_1': 90004},
)


presence_of_mind_12043 = spell(
    id=12043,
    name='Presence of Mind',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=33882112,
    category=1151,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=1500,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=108, misc_value=10),
    ],
    spell_icon_id=139,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Baseline Changes): moved from mage_talents.csv - "Now baseline", learn level 40. Old talent slot (tab 81/Arcane, tier 4, col 1) is superseded by the new tree\'s Arcane Barrage in Phase 2 - see docs/arcane-mage-rework-design.md\'s talent tree.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Mage spell with a casting time less than 10 sec will be an instant cast spell.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, your next Mage spell with a casting time less than 10 sec becomes an instant cast spell.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1631584309, 'EffectSpellClassMaskA_2': 4096, 'EquippedItemClass': -1, 'ExcludeCasterAuraSpell': 12042, 'InterruptFlags': 12, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassMask_2': 32, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 4600, 'BaseLevel': 40},
)


slow_31589 = spell(
    id=31589,
    name='Slow',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=30.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-61, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.APPLY_AURA, base_points=-61, implicit_target_a=6, apply_aura=218),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=6, apply_aura=216),
    ],
    spell_icon_id=27,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Baseline Changes): moved from mage_talents.csv - "Now baseline", learn level 24. Old talent slot (tab 81/Arcane, tier 8, col 1) is superseded by the new tree\'s Temporal Convergence in Phase 2 - see docs/arcane-mage-rework-design.md\'s talent tree.',
    raw_overrides={'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed reduced by $s1%.  Time between ranged attacks increased by $s2%.  Casting time increased by $s3%.', 'BaseLevel': 24, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces target's movement speed by $s1%, increases the time between ranged attacks by $s2% and increases casting time by $s3%.  Lasts $d.  Slow can only affect one target at a time.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 14684919, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 3, 'SpellLevel': 24, 'SpellPriority': 50, 'SpellVisualID_1': 68, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


brilliance_aura_200067 = spell(
    id=200067,
    name='Brilliance Aura',
    school=School.ARCANE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=56, apply_aura=226, amplitude=1000, radius_yards=40.0),
    ],
    spell_icon_id=54,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, New Spells): "Restores 2% of missing mana every 1 second to all party and raid members within 40 yards of you for 15 seconds." SPELL_AURA_PERIODIC_DUMMY (226, effect1) at 1000ms amplitude - "2% of missing mana" isn\'t stock aura math (stock periodic-energize is a flat amount, not a percent-of-missing), so the real tick amount is computed in C++ (spell_mage_brilliance_aura, spell_mage.cpp) reading GetMaxPower(POWER_MANA) - GetPower(POWER_MANA) per target on each pulse, same idiom as spell_mage_refreshment\'s OnEffectCalcAmount (Frost Mage rework) reading live max health/mana instead of a DBC-expressible constant. implicit_target_a 56 / radius 40yd mirrors Bloodlust (2825)\'s own raid-AOE-self-cast targeting. SpellIconID 54 (Spell_Nature_Brilliance).',
    raw_overrides={'AttributesEx': 131072, 'BaseLevel': 52, 'SpellLevel': 52, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restores 2% of missing mana every 1 sec to all party and raid members within 40 yards.  Lasts 15 sec.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Restoring mana.', 'SpellClassMask_3': 1},
)


arcane_ward_200068 = spell(
    id=200068,
    name='Arcane Ward',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=56,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=164, points_per_level=17.75, implicit_target_a=1, apply_aura=69, misc_value=64),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=74, misc_value=64),
    ],
    spell_icon_id=1918,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, New Spells): "Baseline for all Mages. Mirrors Fire Ward and Frost Ward in level learned, cooldown, absorb amount and rank progression, applied to the Arcane school." Row is a straight copy of Fire Ward (543)\'s structure/numbers with school and effect misc_value (school-absorb target mask) swapped from Fire (4) to Arcane (64) - single rank, matching Fire Ward\'s own single-rank-bootstrap shape (BaseLevel/SpellLevel 20, MaxLevel 80). effect2 (Reflect Spells School, base_points -1 -> live 0%) is inert dead data inherited unchanged from Fire Ward\'s own pulled row - not this rework\'s concern to fix. SpellIconID 1918 (Spell_Arcane_ArcaneResilience, talent-tooltip-audit 2026-09-17: was 72/Spell_Nature_GuardianWard, a generic placeholder used because no dedicated "Arcane Ward" icon was known to exist in the client) - Fire (16)/Frost (14) already use their own school-specific icons, this now does too.',
    raw_overrides={'BaseLevel': 20, 'SpellLevel': 20, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellClassMask_1': 8, 'SpellClassMask_3': 8, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Absorbs $s1 Arcane damage.  Lasts $d.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs Arcane damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_2': 1.0},
)


mass_invisibility_200069 = spell(
    id=200069,
    name='Mass Invisibility',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=56, radius_yards=40.0),
    ],
    spell_icon_id=337,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, New Spells): "You and your allies within 40 yards instantly become invisible for 12 sec... Does not affect allies in combat." SPELL_EFFECT_DUMMY (3, effect1) targeted natively at TARGET_UNIT_CASTER_AREA_RAID (56, 40yd radius) - same native raid-AOE targeting idiom as Bloodlust/Time Warp (2825/200070), rather than a self-targeted script effect with a hand-rolled range search. spell_mage_mass_invisibility (spell_mage.cpp) filters out in-combat allies via OnObjectAreaTargetSelect (mirrors spell_sha_bloodlust\'s own RemoveInvalidTargets idiom) and CastSpell()s the real Invisibility (66) on each surviving target via OnEffectHitTarget - reuses 66\'s existing fade-on-action behavior instead of reimplementing it. SpellIconID 337 (Spell_Nature_InvisibilityTotem) - distinct from plain Invisibility\'s own icon (2308, Ability_Mage_Invisibility).',
    raw_overrides={'BaseLevel': 66, 'SpellLevel': 66, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You and your allies within 40 yards instantly become invisible for 12 sec.  Taking any action will cancel the effect.  Does not affect allies in combat.'},
)


time_warp_200070 = spell(
    id=200070,
    name='Time Warp',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=26,
    range_yards=0.0,
    duration_ms=40000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=56, apply_aura=192, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=56, apply_aura=61, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=56, apply_aura=65, radius_yards=100.0),
    ],
    spell_icon_id=58,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, New Spells): "[Same as Bloodlust]" - row is a straight copy of Bloodlust (2825)\'s 3-effect haste structure (melee+ranged / ranged / spell casting speed, all +30%, 100yd raid radius, same attribute flags) with school changed to Arcane (64, was Nature 8) and BaseLevel/SpellLevel set to 60. The Sated (57724) / Exhaustion (57723) lockout itself is not a DBC effect on Bloodlust either - it\'s applied via C++ (spell_shaman_bloodlust, spell_shaman.cpp AfterHit). spell_mage_time_warp (spell_mage.cpp) mirrors that same pattern against the *same* two spell IDs, so Time Warp and Bloodlust/Heroism share one lockout with zero changes to spell_shaman.cpp. SpellIconID 58 (Spell_Nature_TimeStop).',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 256, 'BaseLevel': 60, 'SpellLevel': 60, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Warp the flow of time, increasing haste by 30% for all party and raid members for 40 sec.  Allies will be unable to benefit from Bloodlust, Heroism, or Time Warp again for 10 min.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee, ranged, and spell casting speed increased by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


blast_wave_11113 = spell(
    id=11113,
    name='Blast Wave',
    school=School.FIRE,
    attributes=65536,
    category=250,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=153, points_per_level=10.2667, die_sides=33, implicit_target_a=22, implicit_target_b=15, radius_yards=10.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_DECREASE_SPEED, radius_yards=10.0),
    ],
    spell_icon_id=292,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 sec 3.2: knockback effect (stock Effect_3) removed, daze kept, self-centered 10 yd, 30 sec cooldown unchanged. spell_mage_blast_wave's glyph-knockback hook now simply never fires.",
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Dazed.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A wave of flame radiates outward from the caster, damaging all enemies caught within the blast for $s1 Fire damage and dazing them for $d.', 'EffectBonusMultiplier_1': 0.19300000369548798, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 64, 'SpellClassSet': 3, 'SpellLevel': 30, 'SpellPriority': 50, 'SpellVisualID_1': 963, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


pyroblast_11366 = spell(
    id=11366,
    name='Pyroblast',
    school=School.FIRE,
    attributes=65536,
    category=290,
    cast_time_ms=5000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=22,
    range_yards=35.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=140, points_per_level=12.105, die_sides=47, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=13, points_per_level=1.075, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    spell_icon_id=184,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s2 Fire damage every $t2 seconds.', 'BaseLevel': 20, 'CastingTimeIndex': 6, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Hurls an immense fiery boulder that causes $s1 Fire damage and an additional $o2 Fire damage over $d.', 'EffectBonusMultiplier_1': 1.149999976158142, 'EffectBonusMultiplier_2': 0.05000000074505806, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 24.0, 'SpellClassMask_1': 4194304, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 2253, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ice_barrier_11426 = spell(
    id=11426,
    name='Ice Barrier',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=471,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=21,
    range_yards=0.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1999, implicit_target_a=1, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=32,
    coeff_weight=1.0,
    notes='EDITED for docs/frost-mage-redesign.md sec 2 (Ice Barrier): "Flat absorb value replaced with a scaling formula: 2000 base plus 1.0 spell power coefficient, modified by Versatility." base_points -> 1999 (2000, -1 convention), old per-level-only growth (points_per_level 19.4) zeroed out now that spell power coefficient carries scaling instead. Coefficient applied via spell_bonus_data (direct_bonus=1.0) in the accompanying pending SQL, same mechanism as Glacial Spike/Flurry. "Modified by Versatility" is not verified here - per project memory Versatility is already wired as a general stat, but confirm it actually touches SPELL_AURA_SCHOOL_ABSORB during playtest; if not, that\'s a small follow-up, not a data change. single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs damage.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly shields you, absorbing $s1 damage.  Lasts $d.  While the shield holds, spellcasting will not be delayed by damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 1, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 4302, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


dragon_s_breath_31661 = spell(
    id=31661,
    name="Dragon's Breath",
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    attributes=1114112,
    category=1215,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=20000,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=0.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=369, points_per_level=9.04, die_sides=61, implicit_target_a=104, radius_yards=10.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.DISORIENTED, implicit_target_a=104, apply_aura=AuraType.MOD_CONFUSE, radius_yards=10.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=104, apply_aura=AuraType.MOD_DECREASE_SPEED, radius_yards=10.0),
    ],
    spell_icon_id=1548,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Disoriented.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Targets in a cone in front of the caster take $s1 Fire damage and are Disoriented for $d.  Any direct damaging attack will revive targets.  Turns off your attack when used.', 'EffectBonusMultiplier_1': 0.19300000369548798, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 139944, 'RangeIndex': 1, 'SpellClassMask_1': 8388608, 'SpellClassSet': 3, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 7860, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


arcane_barrage_44425 = spell(
    id=44425,
    name='Arcane Barrage',
    school=School.ARCANE,
    attributes=65536,
    category=1189,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=3000,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=385, points_per_level=22.5385, die_sides=85, implicit_target_a=6, chain_targets=5),
    ],
    spell_icon_id=3376,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1→top rank's own top level (86, chain has a gap at 60) slope (anchor rank 44781, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (44781, rank 3); MaxLevel set to 80",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Launches several missiles at the enemy target, causing $s1 Arcane damage. Each stack of Arcane Blast on you causes Arcane Barrage to hit an additional target. Consumes all stacks of Arcane Blast and restores 2.5% of your maximum mana per stack consumed.', 'EffectBonusMultiplier_1': 0.7139999866485596, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 24.0, 'SpellClassMask_2': 32768, 'SpellClassSet': 3, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 9947, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


living_bomb_44457 = spell(
    id=44457,
    name='Living Bomb',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    attributes=67174400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=22,
    range_yards=35.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=152, points_per_level=7.3846, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.APPLY_AURA, base_points=44460, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3000,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1→top rank's own top level (86, chain has a gap at 60) slope (anchor rank 55360, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (55360, rank 3); MaxLevel set to 80 | effect2 (explosion spell-ID reference) excluded from the formula -- see Gotchas: embedded spell-ID base_points",
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Causes $s1 Fire damage every $t1 sec.  After $d or when the spell is dispelled, the target explodes causing $44461s1 Fire damage to all enemies within $44461a1 yards.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The target becomes a Living Bomb, taking $o1 Fire damage over $d.  After $d or when the spell is dispelled, the target explodes dealing $44461s1 Fire damage to all enemies within $44461a1 yards.', 'EffectBonusMultiplier_1': 0.20000000298023224, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12582935, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 131072, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 10692, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


deep_freeze_44572 = spell(
    id=44572,
    name='Deep Freeze',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=1221,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=30.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.STUN, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=2939,
    notes='MOVED from npc.csv to mage.csv for docs/frost-mage-redesign.md sec 2 (Deep Freeze: "Converted from a talent to a learnable spell. Damage component removed."). No data change needed - cooldown (30000ms), stun duration (5000ms), and the frozen-only usability gate (TargetAuraState=4, i.e. AURA_STATE_FROZEN - native engine check in SpellInfo.cpp, CheckCasterAuraStates) already match the spec exactly as pulled from live data. Two real gaps remain, both C++/wiring, not spell-row data: (1) reachability - nothing teaches this spell any more once it leaves the old Talent.dbc row, fixed via the trainer_spell row (level 42) in the accompanying pending SQL; (2) the native TargetAuraState check only recognizes the *global* AURA_STATE_FROZEN flag (a real freeze), not FrostMageRework::IsFrozenFor\'s Fingers-of-Frost/Shattering-Cold cases (spell_mage.cpp) - needs a CheckCast override to accept those too, same as the spec\'s Interaction Rules intend. "No longer deals damage to stun-immune targets": the existing spell_mage_deep_freeze_immunity_state script (71761 -> 71757, already registered in spell_mage.cpp) is what currently provides that damage fallback for the *old* talent - not verified whether/how 71761 actually attaches to a Deep Freeze cast (no field on 44572 itself points at it), so left unresolved rather than guessed; needs checking before assuming the new instance is damage-free. pulled from existing data',
    raw_overrides={'AttributesEx4': 512, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned and Frozen.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Stuns the target for $d.  Only usable on Frozen targets.  Deals ${$71757m1*$<mult>} to ${$71757M1*$<mult>} damage to targets permanently immune to stuns.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 1048576, 'SpellClassSet': 3, 'SpellDescriptionVariableID': 167, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 9963, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetAuraState': 4},
)


combustion_11129 = spell(
    id=11129,
    name='Combustion',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    attributes=33816832,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CRIT_DAMAGE_BONUS),
        Effect(type=EffectType.APPLY_AURA, base_points=9, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=33,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (6,1): fully replaces the stock charge-based version - fixed 10 sec duration (was until 3 crits), Effect_2 is a flat +10% crit SpellMod on the same Fire classmask Effect_1's crit-damage bonus already used (EffectSpellClassMaskB_* = A_*), no more 28682 stacking trigger / ProcCharges. spell_mage_combustion (the 3-crit remover) is unbound in Phase 3. 2 min RecoveryTime -> Cooldown Haste applies. Bugfix (talent-tooltip-audit, 2026-09-17): base_points was 10, displaying as 11% ($s2 = base_points+1) against the design doc's 10% - dropped to 9.",
    raw_overrides={'AttributesEx': 268435456, 'AttributesEx3': 67108864, 'AttributesEx4': 524352, 'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, increases your critical strike chance with Fire spells by $s2% and your critical strike damage bonus with Fire spells by $s1% for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 146800663, 'EffectSpellClassMaskA_2': 200776, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 67108864, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 7634, 'StanceBarOrder': 4294967295, 'EffectSpellClassMaskB_1': 146800663, 'EffectSpellClassMaskB_2': 200776, 'AuraDescription_Lang_enUS': 'Critical strike chance with Fire spells increased by $s2%, critical strike damage bonus with Fire spells increased by $s1%.'},
)


cold_snap_11958 = spell(
    id=11958,
    name='Cold Snap',
    school=School.FROST,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=480000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=133,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, this spell finishes the cooldown on all Frost spells you recently cast.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 12, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 4, 'SpellClassSet': 3, 'SpellLevel': 30, 'SpellPriority': 50, 'SpellVisualID_1': 2760},
)


arcane_power_12042 = spell(
    id=12042,
    name='Arcane Power',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=1151,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=15000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=62,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increased damage and mana cost for your spells.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, your spells deal $s1% more damage while costing $s2% more mana to cast.  This effect lasts $D.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 685904631, 'EffectSpellClassMaskA_2': 102472, 'EffectSpellClassMaskB_1': 549591799, 'EffectSpellClassMaskB_2': 168000, 'EffectSpellClassMaskC_1': 4194437, 'EffectSpellClassMaskC_2': 4096, 'EquippedItemClass': -1, 'ExcludeCasterAuraSpell': 12043, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 524288, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 4370},
)


icy_veins_12472 = spell(
    id=12472,
    name='Icy Veins',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=65, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=9),
    ],
    spell_icon_id=2162,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Casting speed of all spells increased by $s1% and reduces pushback suffered by damaging attacks while casting by $s2%.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Hastens your spellcasting, increasing spell casting speed by $s1% and reduces the pushback suffered from damaging attacks while casting by $s2%.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 1698695349, 'EffectSpellClassMaskB_2': 528640, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 16384, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 10148},
)


summon_water_elemental_31687 = spell(
    id=31687,
    name='Summon Water Elemental',
    school=School.FROST,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=47),
    ],
    spell_icon_id=2134,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summon a Water Elemental to fight for the caster$?(s70937)[][ for $70907d].', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 2048, 'SpellClassSet': 3, 'SpellLevel': 50, 'SpellVisualID_1': 7866, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


focus_magic_54646 = spell(
    id=54646,
    name='Focus Magic',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=21, apply_aura=57, misc_value=126),
        Effect(type=EffectType.DUMMY, die_sides=0),
    ],
    spell_icon_id=2158,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): retuned in place, same slot (2,3) - the real stock Focus Magic already grants exactly "3% crit to target, reciprocal 3% to caster on target\'s crit" (SPELL_AURA_MOD_SPELL_CRIT_CHANCE, misc_value 126), matching the design doc\'s numbers as-is; only cosmetic retune (name/notes), no value change. Existing spell_mage_focus_magic script (spell_mage.cpp) is untouched.',
    raw_overrides={'AttributesEx': 524288, 'AttributesEx2': 8, 'AttributesEx3': 67108864, 'AttributesEx5': 32, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Chance to critically hit with spells increased by $s1%.  When a critical hit occurs, the caster's chance to critically hit is increased.", 'AuraInterruptFlags': 4718592, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the target's chance to critically hit with spells by $s1%.  When the target critically hits the caster's chance to critically hit with spells is increased by $54648s1% for $54648d.  Cannot be cast on self.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 87040, 'SpellClassMask_1': 2147483648, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 20, 'SpellVisualID_1': 11998, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


temporal_convergence_200078 = spell(
    id=200078,
    name='Temporal Convergence',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=45000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=1),
    ],
    spell_icon_id=1952,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 8): shell only - icon/cost/cooldown (SPELL_EFFECT_DUMMY effect1, Phase 3 hook). The stack-consume + variable Evocation/Arcane Power CD reduction is a live Arcane Blast stack-count read at cast time, not DBC-expressible - see deferred list. SpellIconID 1952 (Spell_Arcane_Arcane04) - no dedicated Temporal Convergence icon exists in the client.',
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Consumes all stacks of Arcane Blast, reducing the remaining cooldown of Evocation and Arcane Power by 5 sec per stack consumed.'},
)


arcane_overload_200079 = spell(
    id=200079,
    name='Arcane Overload',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, implicit_target_a=53, implicit_target_b=16, radius_yards=10.0),
    ],
    spell_icon_id=2210,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 10): shell only - icon/cost/cooldown (SPELL_EFFECT_DUMMY effect1, Phase 3 hook). Variable mana-spend AoE damage, the %-of-max-mana regen tick (same live-read need as Brilliance Aura) and the +10% spell damage buff are all one coherent Phase 3 CastCustomSpell implementation - see deferred list. SpellIconID 145 (Spell_Frost_ManaBurn) - no dedicated Arcane Overload icon exists in the client (Cata-era spell, this fork is WotLK 3.3.5a).',
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 6, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Expend up to 30% of your maximum mana to annihilate your enemy target and nearby enemies for damage equal to the mana spent plus a spell power coefficient. Deals reduced damage beyond 5 targets. For 15 sec afterward, restore 3% of your maximum mana every 1 sec and your spell damage is increased by 10%.'},
)


# ---------------------------------------------------------------------------------------------
# Fire Mage rework (docs/reworks/fire-mage-rework.md) - Phase 1: net-new baseline spells.
#
# Custom SpellClassMask_3 (family-flags dword 2) bits, so talents can scope SpellMods and procs to
# exactly these spells. Stock Mage data uses dword-2 bits 0-4 only; everything from bit 5 up is
# ours (checked across all of source/classes/mage/ before picking):
#   0x20  Meteor (200095 cast + 200096 impact/burn)
#   0x40  Ignite tick (200098) - so a script can tell "Ignite's own payout" apart from a real
#         player-cast Fire spell by mask instead of by id
# ---------------------------------------------------------------------------------------------

meteor_200095 = spell(
    id=200095,
    name='Meteor',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=45000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=40.0,
    radius_yards=8.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=87, radius_yards=8.0),
    ],
    spell_icon_id=1516,
    notes="Fire Mage rework sec 2 - Meteor. Ground-targeted (Targets 0x40 = TARGET_FLAG_DEST_LOCATION, effect target 87 = TARGET_DEST_DEST) instant; spell_mage_meteor schedules Meteor Impact (200096) at the stored destination 3 sec later (an m_Events lambda on the caster - there's no DBC way to express a fixed-delay ground impact, a missile's flight time scales with distance). Learned at 58 from the Mage class trainer (TrainerId 212). SpellIconID 1516 (Spell_Fire_MeteorStorm). 45s RecoveryTime is >= CUSTOM_COOLDOWN_HASTE_MIN_BASE_COOLDOWN_MS so Cooldown Haste applies (sec 8). SpellVisualID_1 90002 (patch_mage_vfx_models.py): PrecastKit-only flourish (stock kit 171) on this instant cast - the falling meteor itself is a temporary summoned creature (NPC_MAGE_METEOR_MISSILE, spell_mage_meteor::HandleDummy), not a SpellVisual missile (see docs/reworks/fire-mage-meteor-vfx.md's 'Meteor's fall uses a temporary summoned creature' scope decision), so it isn't wired through this spell's own SpellVisualID at all.",
    raw_overrides={'BaseLevel': 58, 'SpellLevel': 58, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'FacingCasterFlags': 0, 'InterruptFlags': 8, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellClassMask_3': 32, 'SpellPriority': 50, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Calls down a meteor which lands at the target location after 3 sec, dealing $200096s1 Fire damage to all enemies within $200096a1 yards, and burns the ground, dealing $200096o2 Fire damage over $200096d to all enemies in the area.', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'SpellVisualID_1': 90002},
)
scripted_by(meteor_200095, 'spell_mage_meteor')
# First real user of trained_by() - 212 is the TrainerId every other level-58+ Mage spell on this
# deployment is taught from (data/sql/updates/db_world/2026_09_10_13.sql). Cost matches
# Invisibility's (66) level-58 row.
trained_by(meteor_200095, trainer_id=212, req_level=58, money_cost=200000)
# Bug found via playtest 2026-09-16/17: Meteor never showed up in the trainer window at all,
# despite the trainer_spell row and spell_dbc data being confirmed correct end-to-end (server-side
# debug logging showed the server did include SpellId 200095 in the outgoing SMSG_TRAINER_LIST
# packet as Usable/Available - the client was silently dropping it from render). This is the
# documented "new custom spell IDs need their own SkillLineAbility row" gap (docs/bugs-and-fixes.md
# "New custom spell IDs granted by a talent show up in the Spellbook's 'General' tab instead of the
# class's own tab") - it's previously only been seen affecting the Spellbook window (miscategorized
# into General), but the same missing row apparently makes the client drop a fully-custom,
# player-cast spell ID from the Trainer window's list entirely rather than just misfiling it.
# Meteor is a brand-new baseline (non-talent) player-cast spell with a fully custom ID, so it needs
# this row like Arcane's baseline 200067-200070 (skilllineability 30403-30406) did.
skill_line_ability(id=30410, skill_line=8, spell_id=200095, class_mask=128)
bonus_coefficients(meteor_impact_200096, direct=0.3, dot=0.15,
                   comment='Mage - Meteor impact / ground burn (fire-mage-rework.md sec 2; dot is per tick, same convention as Flamestrike)')


flashpoint_200111 = spell(
    id=200111,
    name='Flashpoint',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=45000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=2, implicit_target_a=6),
    ],
    spell_icon_id=1197,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (10,1): new talent on repurposed stock talent id 1848 (Fiery Payback) - the tree's single 50-point capstone ability. Shell only: instant, 45 sec RecoveryTime (Cooldown Haste applies), 10% base mana (spec gives no cost - user-adjustable), Effect_1 DUMMY on the enemy target. EFFECT_0's BasePoints (2, -1 convention -> CalcValue() 3) is the Ignite multiplier spell_mage_flashpoint (spell_mage.cpp) reads via GetEffectValue() - baked into spell data instead of a C++ constant so retuning the multiplier is a data change, not a rebuild. Phase 3's spell_mage_flashpoint consumes the target's whole Ignite bank (Mage::ConsumeIgnite) and deals that multiplier x the bank, half that to enemies within 8 yd, neither able to crit. Custom dword-2 bit 0x80. Icon 1197 (Cataclysm). Player-castable and talent-granted -> SkillLineAbility 30409 in mage_talents.py. SpellVisualID_1 90001 (patch_mage_vfx_models.py): PrecastKit-only flourish (stock kit 171, reused - see docs/reworks/fire-mage-meteor-vfx.md's 'Casting animation' section) since this is a 0-cast-time spell with no cast bar to loop a real CastKit over.",
    raw_overrides={'BaseLevel': 60, 'SpellLevel': 60, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellClassMask_3': 128, 'SpellPriority': 50, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Detonates your Ignite on the target, dealing 5 times its remaining damage instantly and half that amount to all enemies within 8 yards. This damage cannot be a critical strike.', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'SpellVisualID_1': 90001},
)


flashpoint_damage_200119 = spell(
    id=200119,
    name='Flashpoint',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    range_yards=50000.0,
    radius_yards=8.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=6),
        Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=53, implicit_target_b=16, radius_yards=8.0),
    ],
    spell_icon_id=1197,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 3 (10,1) - the actual detonation, cast by spell_mage_flashpoint (200111's SpellScript). EFFECT_0 = 5x the consumed Ignite bank on the explicit target (SPELLVALUE_BASE_POINT0); EFFECT_1 = half that (2.5x) to enemies within 8 yd of the target (SPELLVALUE_BASE_POINT1), same target-centered AoE pair as Living Bomb's explosion (44461) and this rework's own Burnout explosion (200116) - naturally also hits the primary target at 0 yards, matching 'dealing 5x...and half that amount to all enemies within 8 yards' read as inclusive. 'This damage cannot be a critical strike' (sec 10,1) -> CANT_CRIT; damage is the already-fully-modified banked amount -> IGNORE_CASTER_MODIFIERS + ALWAYS_HIT, same reasoning as the Ignite tick vehicle (200098).",
    raw_overrides={'AttributesEx2': 536870912, 'AttributesEx3': 537133056, 'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Detonates Ignite.', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
bonus_coefficients(flashpoint_damage_200119, direct=0.0, comment='Mage - Flashpoint detonation (fire-mage-rework.md sec 6, (10,1)): pure multiplier of the already-scaled Ignite bank, no independent SP scaling')


scripted_by(fireball_133, 'spell_mage_fireball')
scripted_by(scorch_2948, 'spell_mage_scorch')
scripted_by(flamestrike_2120, 'spell_mage_flamestrike')
scripted_by(flashpoint_200111, 'spell_mage_flashpoint')
scripted_by(pyroblast_11366, 'spell_mage_pyroblast')
