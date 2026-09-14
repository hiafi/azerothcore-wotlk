"""
Auto-converted from source/spells/mage*.csv + source/talents/mage.yaml by csv_to_dsl.py
(.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md's Phase 4) - not yet hand-cleaned. See csv_to_dsl.py's docstring for what "mechanical, not hand-authored-quality" means here.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, School
from lib.dsl.registry import spell
from lib.dsl.registry import granted_by_talent, tab
from lib.dsl.registry import skill_line_ability

# --- spells trained outright (source/spells/mage.csv) ---

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
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=42208),
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
    category_cooldown_ms=8000,
    mana_cost=0,
    mana_cost_pct=21,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=23, points_per_level=16.6852, die_sides=9, implicit_target_a=6),
    ],
    spell_icon_id=12,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 6); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 6, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blasts the enemy for $s1 Fire damage.', 'EffectBonusMultiplier_1': 0.42899999022483826, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2, 'SpellClassSet': 3, 'SpellLevel': 6, 'SpellPriority': 50, 'SpellVisualID_1': 143, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
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
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=7268),
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

arcane_missile_7268 = spell(
    id=7268,
    name='Arcane Missile',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=23, points_per_level=3.3, implicit_target_a=77),
    ],
    spell_icon_id=225,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80 | Bugfix (playtest report, 2026-09-08): SpellVisualID_1 was left at rank 1\'s own value (268) instead of being carried over from the max rank\'s damage sub-spell (25346, mage.csv/npc.csv - SpellVisualID_1 270) like every other field in this bootstrap was - "arcane missiles has the rank 1 model instead of the max rank model for its missiles". Fixed to 270.',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Launches Arcane Missiles at the enemy, causing $7268s1 Arcane damage every $5143t2 sec for $5143d.', 'EffectBonusMultiplier_1': 0.28600001335144043, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 20.0, 'SpellClassMask_1': 2097152, 'SpellClassSet': 3, 'SpellLevel': 8, 'SpellPriority': 50, 'SpellVisualID_1': 270},
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

chilled_12484 = spell(
    id=12484,
    name='Chilled',
    school=School.FROST,
    mechanic=Mechanic.SNARE,
    attributes=256,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=1500,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=285,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement Slowed.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Chills the target for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 1048576, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellVisualID_1': 2640},
)

silenced_improved_counterspell_18469 = spell(
    id=18469,
    name='Silenced - Improved Counterspell',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.SILENCE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=6, apply_aura=AuraType.MOD_SILENCE),
    ],
    spell_icon_id=17,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 4, 'AttributesEx3': 1073872896, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Silenced.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Silences the target for $d.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 1073741824, 'SpellClassSet': 3},
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

arcane_blast_30451 = spell(
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
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=1, trigger_spell=36032),
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=34913),
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

molten_armor_34913 = spell(
    id=34913,
    name='Molten Armor',
    school=School.FIRE,
    attributes=150994944,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=74, points_per_level=5.2778, implicit_target_a=6),
    ],
    spell_icon_id=2307,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 62); RealPointsPerLevel from rank1→top rank's own top level (80, chain has a gap at 60) slope (anchor rank 43044, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (43044, rank 3); MaxLevel set to 80",
    raw_overrides={'AttributesEx': 168, 'AttributesEx2': 16388, 'AttributesEx4': 16512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 62, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes $34913s1 Fire damage when hit, increases your chance to critically hit with spells by $30482s3% of your Spirit, and reduces the chance you are critically hit by $30482s2%.  Only one type of Armor spell can be active on the Mage at any time.  Lasts $30482d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 8, 'SpellClassSet': 3, 'SpellLevel': 62},
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

blizzard_42208 = spell(
    id=42208,
    name='Blizzard',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=35, points_per_level=4.4, implicit_target_a=76, implicit_target_b=16, radius_yards=8.0),
    ],
    spell_icon_id=285,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 1073741824, 'AttributesEx3': 1073741824, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Ice shards pelt the target area doing ${$42208m1*8*$<mult>} Frost damage over $10d.', 'EffectBonusMultiplier_1': 0.14300000667572021, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 135, 'SpellClassMask_1': 524416, 'SpellClassSet': 3, 'SpellDescriptionVariableID': 167, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 9487, 'StartRecoveryCategory': 133},
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

fiery_payback_44440 = spell(
    id=44440,
    name='Fiery Payback',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-1751, implicit_target_a=1, apply_aura=107, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=2499, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=3189,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CasterAuraState': 13, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When below 35% health all damage taken is reduced by $s1% and your Pyroblast spell's cast time is reduced by ${$44440m2/-1000}.2 secs while the cooldown is increased by ${$44440m3/-1000}.1 secs.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 8, 'EffectSpellClassMaskB_1': 4194304, 'EffectSpellClassMaskC_1': 4194304, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

living_bomb_44461 = spell(
    id=44461,
    name='Living Bomb',
    school=School.FIRE,
    attributes=159711232,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=305, points_per_level=14.7692, implicit_target_a=53, implicit_target_b=16, radius_yards=10.0),
    ],
    spell_icon_id=3000,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1→top rank's own top level (86, chain has a gap at 60) slope (anchor rank 55362, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (55362, rank 3); MaxLevel set to 80",
    raw_overrides={'AttributesEx2': 1073741824, 'AttributesEx5': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The target becomes a Living Bomb, taking $44457o1 Fire damage over $44457d.  After $44457d or when the spell is dispelled, the target explodes dealing $44461s1 Fire damage to all enemies within $44461a1 yards.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 0.4000000059604645, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 12582935, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 65536, 'SpellClassSet': 3, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 10693},
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

icicles_200001 = spell(
    id=200001,
    name='Icicles',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=35,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 1, Icicles): stacking (CumulativeAura=5) caster buff, no fixed duration (cleared explicitly by spell_mage_icicles on combat-leave or by Glacial Spike on cast). Generation gated in C++ on the caster knowing SPELL_MAGE_GLACIAL_SPIKE (200002), granted by Frostbolt/Frostfire Bolt casts and every 4th Blizzard tick - see spell_mage.cpp. SpellIconID 35 (Spell_Frost_Glacier, from apps/dbc-tools/var/spell_icon_names.csv).',
    raw_overrides={'AttributesEx3': 1073741824, 'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Frost energy has gathered around you. Stacks up to 5 times; consumed by Glacial Spike.', 'CumulativeAura': 5, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Frost energy has gathered around you. Stacks up to 5 times; consumed by Glacial Spike.', 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellPriority': 50, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 0},
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
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 1, Glacial Spike): the button/cast-bar spell only now - no damage and no travel of its own (effect1 is a no-op DUMMY, Speed removed). Redesigned as a 3-stage 'ramp-up' missile chain to fake mid-flight acceleration, since Spell.dbc only exposes one constant Speed per spell and the engine has no acceleration field (see docs/frost-mage-handoff.md's art-pass discussion). On hit (instant, since this row no longer travels), spell_mage_glacial_spike::BeginRamp (spell_mage.cpp) fires two short cosmetic hops toward the real target - 200025 (Speed 1, ~0.5yd) then 200026 (Speed 5, ~1.5yd), both dest-targeted (TARGET_DEST_DEST) at a position computed in C++ via GetFirstCollisionPosition, recomputed fresh per stage - then casts the real damage-dealing 200027 (Speed 30) at the real target ~800ms later. Target is carried across the ~800ms ramp by GUID + ObjectAccessor (re-resolved and alive-checked at each stage), not via the native SPELL_EFFECT_TRIGGER_MISSILE_SPELL DBC chain - that mechanism always re-targets the *real* caster-to-enemy distance for a unit-targeted trigger, which is exactly what a short controlled hop distance can't use (see 200025/200026/200027's own notes and the C++ class comment). 5-Icicle requirement still gates the cast here (OnCheckCast); Icicle/Fingers-of-Frost consumption and the Arctic Winds shatter-cleave moved to 200027 (spell_mage_glacial_spike_impact), since that's the stage that represents the spell actually landing. SpellIconID 1236 (Spell_Frost_IceShard, from apps/dbc-tools/var/spell_icon_names.csv).",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'EquippedItemClass': -1, 'PreventionType': 1, 'ProcChance': 101, 'StartRecoveryCategory': 133, 'SpellPriority': 50, 'Description_Lang_enUS': 'Consumes all Icicles to hurl a massive spike of ice at the target, dealing Frost damage.', 'InterruptFlags': 15, 'ChannelInterruptFlags': 0, 'FacingCasterFlags': 1, 'DefenseType': 1},
)

shattering_cold_200003 = spell(
    id=200003,
    name='Shattering Cold',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    range_yards=40.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2945,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 1, Shattering Cold): target-side debuff applied by Flurry (spell_mage_flurry, spell_mage.cpp) on bolt impact. Not dispellable (dispel=DispelType.NONE). Caster-scoping ("only the applying caster benefits") and the frozen-state check are done in C++ via target->HasAura(SPELL_MAGE_SHATTERING_COLD, casterGuid) - see FrostMageRework::IsFrozenFor in spell_mage.cpp - deliberately not via CasterAuraState/AURA_STATE_FROZEN, which is a global (not per-caster) flag in this engine; see docs/frost-mage-implementation-plan.md\'s correction. SpellIconID 2945 (Ability_Mage_ShatterShield, from apps/dbc-tools/var/spell_icon_names.csv). SpellVisualID still unset pending an art pass. Playtest bugfix (2026-08-27, user report): range_yards was left null, which reuse.py\'s range_index() maps to RangeIndex 0 - not "unlimited", but the real client\'s near-zero/self-only SpellRange.dbc row 0 (Spell.cpp\'s CheckCast only special-cases RangeEntry->ID == 1 for triggered 0-range spells, not 0). Every Flurry cast\'s caster->CastSpell(target, 200003, true) silently failed SPELL_FAILED_OUT_OF_RANGE against a non-self target, so the debuff never applied - confirmed live via temporary LOG_ERROR tracing. Set to 40yd to match Flurry\'s own range (200004), since Shattering Cold can only ever be triggered on whatever Flurry already hit.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': "This target's frozen state is being exploited by the caster's spells and abilities.", 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "This target's frozen state is being exploited by the caster's spells and abilities.", 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellPriority': 50, 'StartRecoveryCategory': 133},
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
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=99, implicit_target_a=6),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=99, implicit_target_a=6),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=99, implicit_target_a=6),
    ],
    spell_icon_id=187,
    coeff_weight=0.3,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 1, Flurry): 3 separate SPELL_EFFECT_SCHOOL_DAMAGE effects (100 base each, EffectBasePoints stored as 99), all sharing one spell_bonus_data row (direct_bonus=0.3) - Unit::SpellDamageBonusDone/-Taken look up spell_bonus_data by spell ID and apply the same coefficient to every SCHOOL_DAMAGE effect on the entry, so 3 effects + 1 bonus row is enough to get 3 independently-scaled bolts without a triggered sub-spell. Shattering Cold application (200003) is NOT a DBC effect on this row - it\'s applied once via OnHit in spell_mage_flurry (spell_mage.cpp), specifically because OnHit runs after all of this cast\'s own damage effects resolve, which is what makes "Flurry\'s own bolts do not benefit from Shattering Cold" true without any extra guard logic. Generates no Icicles and can\'t trigger Fingers of Frost (spec) - true for free today since Icicle generation and FoF\'s proc are both keyed off other spell IDs (see spell_mage.cpp) and were never wired to this one; the FoF exclusion will need an explicit family-mask check once the real Row 3 Fingers of Frost proc (not yet built) replaces the legacy sync mechanism. SpellIconID 187 (Spell_Frost_ChillingBlast, apps/dbc-tools/var/spell_icon_names.csv). SpellVisualID_1 set to 14819 (reused from "Ice Lance Volley", spell 70464 - a rapid multi-bolt ice missile kit, thematically closest to "a flurry of ice bolts") - a first pick, not visually confirmed in-game yet; easy to swap by editing this raw_overrides key and rerunning generate.py.',
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Launches a flurry of ice bolts at the target, dealing Frost damage and applying Shattering Cold.', 'EquippedItemClass': -1, 'PreventionType': 1, 'ProcChance': 101, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellPriority': 50, 'InterruptFlags': 15, 'FacingCasterFlags': 1, 'Speed': 38.0, 'DefenseType': 1, 'SpellVisualID_1': 14819},
)

glacial_spike_windup_1_200025 = spell(
    id=200025,
    name='Glacial Spike (Windup 1)',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    range_yards=10.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=87),
    ],
    spell_icon_id=1236,
    notes="Frost Mage rework - internal plumbing spell, not player-facing (never cast by a player directly). First of two cosmetic wind-up hops in Glacial Spike's 3-stage acceleration ramp - see 200002's notes and spell_mage_glacial_spike::BeginRamp in spell_mage.cpp. A short (~0.5yd) dest-targeted (implicit_target_a 87 = TARGET_DEST_DEST, a pure passthrough of whatever x/y/z the caller supplies via CastSpell(x,y,z,spellId,true) - see Spell::SelectImplicitDestDestTargets) no-op DUMMY effect fired toward the real target's direction, at Speed 1.0 so the hop takes ~0.5s. Purely visual - no gameplay effect, no OnHit script of its own, and doesn't know or care who the real target is (the destination position is computed and passed explicitly by the caller each time). Reuses Glacial Spike's own icon/visual (SpellIconID 1236, SpellVisualID 10582) for a consistent look across all 3 stages of the ramp.",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'EquippedItemClass': -1, 'PreventionType': 1, 'ProcChance': 101, 'SpellPriority': 50, 'Description_Lang_enUS': 'Internal: first cosmetic wind-up hop for Glacial Spike.', 'Speed': 1.0, 'SpellVisualID_1': 10582},
)

glacial_spike_windup_2_200026 = spell(
    id=200026,
    name='Glacial Spike (Windup 2)',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    range_yards=10.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=87),
    ],
    spell_icon_id=1236,
    notes="Frost Mage rework - internal plumbing spell, not player-facing. Second of two cosmetic wind-up hops in Glacial Spike's ramp (see 200025's notes - same mechanism, TARGET_DEST_DEST). Covers ~1.5yd at Speed 5.0 (~0.3s), fired by spell_mage_glacial_spike::BeginRamp ~500ms after the cast completes (right as the first hop's own travel finishes). Purely visual, same as 200025.",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'EquippedItemClass': -1, 'PreventionType': 1, 'ProcChance': 101, 'SpellPriority': 50, 'Description_Lang_enUS': 'Internal: second cosmetic wind-up hop for Glacial Spike.', 'Speed': 5.0, 'SpellVisualID_1': 10582},
)

glacial_spike_impact_200027 = spell(
    id=200027,
    name='Glacial Spike (Impact)',
    school=School.FROST,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=1499, implicit_target_a=6),
    ],
    spell_icon_id=1236,
    coeff_weight=1.2,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 1, Glacial Spike): the real, damage-dealing final leg of the 3-stage ramp - same flat 1500 base Frost damage (EffectBasePoints stored as 1499) with a 1.2 spell power coefficient this row carried under ID 200002 before the ramp redesign (see that row's notes and docs/frost-mage-handoff.md's art-pass discussion). The spell_bonus_data row (direct_bonus=1.2) moved here from 200002 - see the accompanying pending_db_world SQL. Fired via caster->CastSpell(target, 200027, true) from spell_mage_glacial_spike::BeginRamp (spell_mage.cpp) ~800ms after the player's cast completes (200002 -> 200025 -> 200026 -> here). Icicle consumption, Fingers-of-Frost-charge consumption, and the Arctic Winds R3 shatter-cleave (spell_mage_glacial_spike_impact::ConsumeIciclesAndFrostCharge) all moved here too, since this is the stage that represents the spell actually landing - not yet implemented is Arctic Winds R3's cleave depending on the Row 9 Arctic Winds talent, same TODO as before. SpellIconID 1236 (Spell_Frost_IceShard, from apps/dbc-tools/var/spell_icon_names.csv). Speed 30 (down from the old single-leg row's 38, per the ramp's own design - the first two legs already cover the 'slow start' part).",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'EquippedItemClass': -1, 'PreventionType': 1, 'ProcChance': 101, 'SpellPriority': 50, 'Description_Lang_enUS': 'Consumes all Icicles to hurl a massive spike of ice at the target, dealing Frost damage.', 'DefenseType': 1, 'Speed': 30.0, 'SpellVisualID_1': 10582},
)

restore_mana_200005 = spell(
    id=200005,
    name='Restore Mana',
    school=School.NORMAL,
    attributes=402653440,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    effects=[
        Effect(type=137, base_points=29, implicit_target_a=1),
    ],
    spell_icon_id=1036,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 2, Conjure Mana Gem): "the new item should restore 30% of maximum mana." SPELL_EFFECT_ENERGIZE_PCT (type 137) is a real, native effect (Spell::EffectEnergizePct, SpellEffects.cpp:1995 - CalculatePct(maxPower, damage)) - no C++ needed, unlike what an earlier pass of the implementation plan assumed. base_points=29 -> 30% (-1 convention, die_sides=1). Wired to item 5514 (Mana Agate)\'s spellid_2 slot in the accompanying pending SQL, replacing the old flat spell 5405; 5405 itself is left untouched since it\'s shared with unrelated items 36799/9397.',
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restores 30% of maximum mana.', 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellPriority': 50, 'SpellClassMask_3': 16},
)

refreshment_200006 = spell(
    id=200006,
    name='Refreshment',
    school=School.NORMAL,
    attributes=402653440,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=84),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=85),
    ],
    spell_icon_id=358,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 2, Conjure Refreshment): item 43518 ("Conjured Mana Pie") repointed to this spell in the accompanying pending SQL (spellid_1, was the real pulled-data spell 61828 "Refreshment", a flat-value wrapper around 61829 "Food"/61830 "Drink"). Built on the same native Food/Drink mechanism those real IDs use - SPELL_AURA_MOD_REGEN (84) and SPELL_AURA_MOD_POWER_REGEN (85), MiscValue POWER_MANA (0) on effect 2 - rather than a dedicated periodic aura, so the real client "eating/drinking" emote (Player.cpp keys it off these two aura types specifically) comes for free. Per-tick amount is still computed in C++ (spell_mage_refreshment, spell_mage.cpp) via OnEffectCalcAmount reading GetMaxHealth()/GetMaxPower(POWER_MANA) - no DBC field can express "percent of current max" - targeting 105%, not 100%, of max over the 30s duration to comfortably outrun MOD_REGEN\'s health tick-count imprecision (it only ticks on the player\'s global un-reset-on-apply 2-sec regen timer); RegenerateHealth()/Regenerate(POWER_MANA) both clamp at max already, so overshooting the math costs nothing beyond wasted regen once full. AuraInterruptFlags reuses the real spells\' NOT_SEATED|NOT_ABOVEWATER combo (262272) - the engine auto-sits the player on apply and drops the aura on standing (Unit.cpp), so no extra stand-state handling is needed. SpellIconID 358 (the native Food/Drink icon, same one 61828/61829/61830 use).',
    raw_overrides={'SpellClassSet': 0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restores health and mana over $d.  Must remain seated while eating.', 'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Restoring health and mana.', 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellPriority': 50, 'AuraInterruptFlags': 262272, 'InterruptFlags': 1, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
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
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 1, Frozen Orb): SPELL_EFFECT_SCRIPT_EFFECT (type 77), self-targeted, instant, 45s cooldown, 20% of base mana (mana_cost_pct). No damage or aura of its own - spell_mage_frozen_orb (spell_mage.cpp) summons the orb trigger creature (NPC_MAGE_FROZEN_ORB, 300001) at the caster\'s position on hit; the creature\'s own AI (npc_mage_frozen_orb) drives movement, the periodic pulse (200009 -> 200008), and the Fingers of Frost grant chain. See docs/frost-mage-implementation-plan.md\'s dedicated "Frozen Orb Implementation" section for the full design and gotchas (faction, movement, damage attribution). Arctic Reach (travel-distance talent) is not yet built - see the Frost talent tree item in docs/frost-mage-handoff.md. SpellIconID 2132 (Spell_Frost_FrozenCore, apps/dbc-tools/var/spell_icon_names.csv - the real spell\'s own icon). SpellVisualID/creature display still unset pending an art pass.',
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Launches a frozen orb forward, dealing Frost damage to enemies in its path and chilling them.  Each enemy struck has a chance to grant you Fingers of Frost.', 'EquippedItemClass': -1, 'PreventionType': 1, 'ProcChance': 101, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellPriority': 50, 'InterruptFlags': 15},
)

frozen_orb_pulse_200008 = spell(
    id=200008,
    name='Frozen Orb Pulse',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    radius_yards=10.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=199, implicit_target_a=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, mechanic=Mechanic.SNARE, implicit_target_a=16, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=2132,
    coeff_weight=0.15,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 1, Frozen Orb\'s pulse): "Every 1 sec, deals 200 Frost damage plus 0.15 spell power coefficient to all enemies within 10 yards, and applies a chill reducing movement speed by 30% for 4 sec." Two effects on one row, same shape as the real Cone of Cold (120): SCHOOL_DAMAGE (base_points 199, -1 convention) + APPLY_AURA MOD_DECREASE_SPEED (base_points -31, -1 convention for -30%, EffectMechanic MECHANIC_SNARE=11), both TARGET_UNIT_DEST_AREA_ENEMY (16, not the SRC variant this row originally shipped with - see "Cast by" below for why). Neither effect JSON sets its own "radius_yards" key (build.py only falls back to the row\'s top-level radius_yards when the per-effect key is absent, not when it\'s present-but-null - learned the hard way diffing a hand-built row against generate.py\'s actual output), so both inherit the row\'s radius_yards (10, -> EffectRadiusIndex 13, the same row Cone of Cold\'s own radius already reuses) and duration_ms (4000, -> DurationIndex 35, the same row Shattering Cold/200003 already reuses). Coefficient (0.15) goes through spell_bonus_data like every other new spell this session - see the accompanying pending SQL. Cast by the OWNING PLAYER (not the orb) at an explicit dest = the orb\'s live position, once per second, from npc_mage_frozen_orb::UpdateAI (spell_mage.cpp) - a deliberate change from the original SRC-based "orb self-casts via a periodic aura (200009)" design, which silently attributed all damage/threat/combat-log entries to the orb instead of the player (root-caused via live playtest: FoF procced and the pulse showed in the combat log, but never in the player\'s own damage meter). TARGET_UNIT_DEST_AREA_ENEMY lets the player be the actual spell caster (correct attribution *and* correct spell-power scaling off the player\'s own stats) while still centering the AoE on the orb\'s moving position rather than the stationary player. 200009 (Frozen Orb Periodic) is no longer cast by anything - left as an orphaned row rather than deleted, see spell_mage.cpp\'s own notes. spell_mage_frozen_orb_pulse (spell_mage.cpp) still exists for BoostChillEffect (Chilled to the Bone) and to tell the orb\'s AI a pulse landed (halts movement, starts the FoF grant chain) - it does not touch the damage/slow itself, both of which are native DBC effects needing no script. Attributes=0 and no player-facing name/description text (Description_Lang_Mask=0) - never cast directly by a player action, never shown in a spellbook/tooltip.',
    raw_overrides={'SpellClassSet': 0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 0, 'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Movement speed reduced.', 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellPriority': 50},
)

frozen_orb_periodic_200009 = spell(
    id=200009,
    name='Frozen Orb Periodic',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=200008),
    ],
    spell_icon_id=2132,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 1, Frozen Orb): the orb\'s own self-buff, cast on itself once by npc_mage_frozen_orb::IsSummonedBy (spell_mage.cpp) right after summon. SPELL_AURA_PERIODIC_TRIGGER_SPELL (apply_aura 23) at 1000ms amplitude, triggering 200008 (Frozen Orb Pulse) - docs/frost-mage-implementation-plan.md\'s Frozen Orb section: "Put a self-cast aura on the orb using SPELL_AURA_PERIODIC_TRIGGER_SPELL at a 1000ms amplitude." duration_ms=10000 (DurationIndex 1) matches both the spec\'s "10 sec" travel time and the orb\'s own TEMPSUMMON_TIMED_DESPAWN lifetime, so exactly 10 pulses land before everything cleans up together. Attributes=0, no player-facing text - never cast by a player.',
    raw_overrides={'SpellClassSet': 0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 0, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellPriority': 50},
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
    spell_icon_id=72,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, New Spells): "Baseline for all Mages. Mirrors Fire Ward and Frost Ward in level learned, cooldown, absorb amount and rank progression, applied to the Arcane school." Row is a straight copy of Fire Ward (543)\'s structure/numbers with school and effect misc_value (school-absorb target mask) swapped from Fire (4) to Arcane (64) - single rank, matching Fire Ward\'s own single-rank-bootstrap shape (BaseLevel/SpellLevel 20, MaxLevel 80). effect2 (Reflect Spells School, base_points -1 -> live 0%) is inert dead data inherited unchanged from Fire Ward\'s own pulled row - not this rework\'s concern to fix. SpellIconID 72 (Spell_Nature_GuardianWard) - no dedicated "Arcane Ward" icon exists in the client (Blizzard never shipped one); Fire (16)/Frost (14) already use their own school-specific icons so a generic ward icon keeps this one visually distinct from both.',
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

arcane_blast_36032 = spell(
    id=36032,
    name='Arcane Blast',
    school=School.ARCANE,
    attributes=67371008,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=79, misc_value=64),
        Effect(type=EffectType.APPLY_AURA, base_points=174, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=2294,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3) - moved from npc.csv, where pull.py\'s file-guess heuristic first landed it (same misfile pattern as earlier batches). Real stock \'Arcane Blast\' stacking self-buff (effect1: +15%/stack Arcane dmg, raw_overrides.CumulativeAura=4 max stack; effect2: raises Arcane Blast\'s own mana cost per stack, self-scoped classmask) - cast as Arcane Blast (30451)\'s trigger spell by the existing spell_mage_arcane_blast::HandleAfterCast (spell_mage.cpp). Content untouched, reference only - several Phase 3 items (Arcane Resonance, Arcane Barrage, Arcane Overload, Temporal Convergence) read its live stack count via caster->GetAura(36032)->GetStackAmount(). Bugfix (playtest report, 2026-09-08/09): dropped ProcChance/ProcCharges/ProcTypeMask (100/1/65536) added here in Phase 3 Batch A - they were never needed (stacking is driven entirely by HandleAfterCast\'s CastSpell, not native procs) and turned out to be live: `spell_proc`\'s own explicit row for 36032 has ProcFlags=0, which SpellMgr::LoadSpellProcs() treats as a sentinel and falls back to these DBC fields, making the buff a real (if narrowly classmask-scoped) proc-consumable aura. Confirmed via live debug instrumentation this was firing on every Arcane Barrage cast (redundant with spell_mage_arcane_barrage\'s own intentional removal) and, through a still-unconfirmed adjacent code path, on Arcane Missiles casts too - \\Arcane Missiles still consumes the Arcane Blast debuff\\". Reverting to inert (all three 0/unset',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx2': 268435456, 'AttributesEx3': 196608, 'AttributesEx4': 8388737, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Arcane spell damage increased by $s1% and mana cost of Arcane Blast increased by $s2%.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'CumulativeAura': 4, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blasts the target with energy, dealing Arcane damage.  Each time you cast Arcane Blast, the damage of all Arcane spells is increased by $36032s1% and mana cost of Arcane Blast is increased by $36032s2%.  Effect stacks up to $36032u times and lasts $36032d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536870912, 'EffectSpellClassMaskB_1': 536870912, 'EffectSpellClassMaskC_1': 536870912, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassMask_3': 12, 'SpellClassSet': 3, 'SpellLevel': 1},
)


# --- spells granted by a talent point (source/spells/mage_talents.csv) ---

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
        Effect(type=EffectType.KNOCK_BACK, base_points=79, implicit_target_a=22, implicit_target_b=15, misc_value=100, radius_yards=10.0),
    ],
    spell_icon_id=292,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Dazed.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A wave of flame radiates outward from the caster, damaging all enemies caught within the blast for $s1 Fire damage, knocking them back and dazing them for $d.', 'EffectBonusMultiplier_1': 0.19300000369548798, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 64, 'SpellClassSet': 3, 'SpellLevel': 30, 'SpellPriority': 50, 'SpellVisualID_1': 963, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
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

improved_fireball_11069 = spell(
    id=11069,
    name='Improved Fireball',
    school=School.FIRE,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=185,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Fireball spell by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_frostbolt_11070 = spell(
    id=11070,
    name='Improved Frostbolt',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=188,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Frostbolt and Ice Lance spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131104, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

frostbite_11071 = spell(
    id=11071,
    name='Frostbite',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12494),
    ],
    spell_icon_id=119,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dealing direct Frost damage has a $s1% chance to freeze the target for $12494d.  The freeze breaks on damage. \n\n|cFF9D9D9DCapstone Bonus: Increases the damage of your Frost spells against frozen targets based on your Mastery.|r', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 4096, 'EffectSpellClassMaskB_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 5, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassMask_2': 512, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_fire_blast_11078 = spell(
    id=11078,
    name='Improved Fire Blast',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=12,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Fire Blast spell by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_fire_blast_11080 = spell(
    id=11080,
    name='Improved Fire Blast',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=12,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Fire Blast spell by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

burning_soul_11083 = spell(
    id=11083,
    name='Burning Soul',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=34, implicit_target_a=1, apply_aura=108, misc_value=9),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=4),
    ],
    spell_icon_id=11,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the pushback suffered from damaging attacks while casting Fire spells by $s1% and reduces the threat caused by your Fire spells by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EffectSpellClassMaskA_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

molten_shields_11094 = spell(
    id=11094,
    name='Molten Shields',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=16,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes your Fire Ward and Frost Ward spells to have a $s1% chance to reflect the warded spell while active. In addition, your Molten Armor has a 50% chance to affect ranged and spell attacks.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 264, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_scorch_11095 = spell(
    id=11095,
    name='Improved Scorch',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=22959),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=816,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to critically hit with Scorch, Fireball and Frostfire Bolt by an additional $s2% and your damaging Scorch spells have a $h% chance to cause your target to be vulnerable to spell damage, increasing spell critical strike chance against that target by $22959s1% and lasts $22959d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskB_1': 17, 'EffectSpellClassMaskB_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50},
)

flame_throwing_11100 = spell(
    id=11100,
    name='Flame Throwing',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=5),
    ],
    spell_icon_id=136,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of all Fire spells except Frostfire Bolt by $s1 yards.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194327, 'EffectSpellClassMaskA_2': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

impact_11103 = spell(
    id=11103,
    name='Impact',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64343),
    ],
    spell_icon_id=45,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 136, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your damaging spells a $h% chance to cause the next Fire Blast you cast to stun the target for $12355d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 4, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

world_in_flames_11108 = spell(
    id=11108,
    name='World in Flames',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2948,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your Flamestrike, Pyroblast, Blast Wave, Dragon's Breath, Living Bomb, Blizzard and Arcane Explosion spells by $s1%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12587140, 'EffectSpellClassMaskA_2': 65600, 'EffectSpellClassMaskB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

critical_mass_11115 = spell(
    id=11115,
    name='Critical Mass',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=71, misc_value=4),
    ],
    spell_icon_id=117,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Fire spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12582935, 'EffectSpellClassMaskA_2': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

ignite_11119 = spell(
    id=11119,
    name='Ignite',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=937,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical strikes from Fire damage spells cause the target to burn for an additional 8% of your spell's damage over $12654d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

ignite_11120 = spell(
    id=11120,
    name='Ignite',
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
    spell_icon_id=937,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical strikes from Fire damage spells cause the target to burn for an additional 16% of your spell's damage over $12654d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

fire_power_11124 = spell(
    id=11124,
    name='Fire Power',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=31,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Fire spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12845079, 'EffectSpellClassMaskA_2': 69704, 'EffectSpellClassMaskB_1': 4194309, 'EffectSpellClassMaskB_2': 135168, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
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
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=1, trigger_spell=28682),
    ],
    spell_icon_id=33,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268435456, 'AttributesEx3': 67108864, 'AttributesEx4': 524352, 'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, this spell increases your critical strike damage bonus with Fire damage spells by $s1%, and causes each of your Fire damage spell hits to increase your critical strike chance with Fire damage spells by $28682s1%.  This effect lasts until you have caused $11129n non-periodic critical strikes with Fire spells.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 146800663, 'EffectSpellClassMaskA_2': 200776, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 3, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassMask_2': 67108864, 'SpellClassMask_3': 8, 'SpellClassSet': 3, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 7634, 'StanceBarOrder': 4294967295},
)

piercing_ice_11151 = spell(
    id=11151,
    name='Piercing Ice',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=176,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Frost spells by $s1%.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 131808, 'EffectSpellClassMaskB_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

frost_channeling_11160 = spell(
    id=11160,
    name='Frost Channeling',
    school=School.FROST,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=72, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=16),
    ],
    spell_icon_id=15,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Frost spells and abilities by $s1% and reduces the threat caused by $s2%. |cFF9D9D9DAt max rank, killing an enemy that yields experience or honor with Frost damage restores 12% of your mana.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1, 'EffectSpellClassMaskA_1': 655360, 'EffectSpellClassMaskA_2': 2049, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

shatter_11170 = spell(
    id=11170,
    name='Shatter',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=112, misc_value=849),
    ],
    spell_icon_id=976,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of all your spells against frozen targets by 17%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 552211063, 'EffectSpellClassMaskA_2': 1151048, 'EffectSpellClassMaskA_3': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

permafrost_11175 = spell(
    id=11175,
    name='Permafrost',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=107, misc_value=3),
    ],
    spell_icon_id=143,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 2, Permafrost). Base effect kept the pulled data\'s own numbers (already matched spec\'s 1/2/3 sec duration + 4/7/10% additional slow via the stored+1 convention) but rescoped from the old talent\'s actual shape -- a target-side debuff (duration/slow/heal-received-reduction applied to whoever the mage\'s Frostbolt/Cone of Cold/Frost Nova hit) -- to a caster-side SpellMod pair (SPELLMOD_DURATION + SPELLMOD_EFFECT1, classmask 544 = Frostbolt|Cone of Cold in word A) boosting the caster\'s own cast of those spells, matching every other \'duration+value modifier\' talent this project has built (Arctic Reach, Chilled to the Bone). The old effect3 (SPELLMOD_EFFECT3, -8/-14/-21, confirmed via the Chilled npc-caster spells 6136/7321\'s own effect3 = SPELL_AURA_MOD_HEALING_PCT to be the dropped tooltip\'s \'reduces healing received\' clause) is not in the new spec and was removed outright, not carried forward. \'Frost Shock\' in the redesign\'s talent text was dropped per user decision (2026-08-24) -- not a real Mage spell (Shaman-only in this game), most likely a stray copy-paste word; scoped to Cone of Cold/Frostbolt/Ice Armor only. Ice Armor\'s own melee-reactive slow (6136 Frost Armor / 7321 Ice Armor\'s \'Chilled\' trigger spells, npc.csv) has no SpellFamilyFlags of its own -- same classmask-unreachable shape as Frozen Orb hit this project before -- so it\'s boosted live in spell_mage_chilled (spell_mage.cpp) instead, same \'read the mage\'s own SpellMod amount and fold it in\' idiom as spell_mage_frozen_orb_pulse\'s Chilled to the Bone fix. Capstone (rank 3 only): see effect3. Playtest bugfix (2026-08-27, user report - "Permafrost reduces the effects of everything by 10%, not just move speed"): the SPELLMOD_EFFECT1 modifier\'s classmask (544, Frostbolt|Cone of Cold) was stored under EffectSpellClassMaskA_2, which the naming convention suggests is "effect index 2\'s word A" but which spell_dbc/DBCStructure.h actually reads as "effect index 0(=A)\'s word 2" - dword-major, not effect-major, unlike every other _1/_2/_3-suffixed field in this schema. That left the real target, effect index 1\'s own classmask, all-zero, and SpellInfo::IsAffected treats an all-zero classmask as matching every spell in the family - so the -4/-7/-10% modifier applied unconditionally to EFFECT_0 of every mage spell (including Evocation\'s mana-restore %) instead of just Frostbolt/Cone of Cold. Fixed by moving the value to EffectSpellClassMaskB_1 (effect index 1(=B)\'s word 1), which is what the engine actually reads for effect 1\'s classmask. See data/sql/updates/pending_db_world/frost_mage_rework.sql (merged Frost Mage rework migration; originally rev_1787820084006262155.sql) for the original diagnosis (that migration was a live DB-only patch of the affected rows; this is the matching source-of-truth fix so future full regenerations don\'t reintroduce it).',
    raw_overrides={'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the duration of your Cone of Cold and Frostbolt slow effects by ${{$m1/1000}}.1 sec, and reduces the target's speed by an additional $s2%. Also affects Ice Armor's chilling effect. |cFF9D9D9DAt max rank: each 1 sec you spend moving grants Permafrost, increasing the damage of your next Ice Lance by 20%. Stacks up to 5 times.|r", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 544, 'EffectSpellClassMaskB_1': 544, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

winter_s_chill_11180 = spell(
    id=11180,
    name="Winter's Chill",
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12579),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=187,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your chance to critically hit with Frostbolt by an additional $s2% and gives your Frost damage spells a $h% chance to apply the Winter's Chill effect, which increases the chance spells will critically hit the target by $12579s1% for $12579d.  Stacks up to $12579u times.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_blizzard_11185 = spell(
    id=11185,
    name='Improved Blizzard',
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
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=112, misc_value=836),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-13, implicit_target_a=1, apply_aura=108, misc_value=19),
    ],
    spell_icon_id=285,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Adds a chill effect to your Blizzard spell.  This effect lowers the target's movement speed by $12484s1%.  Lasts $12484d.  Also reduces the mana cost of Blizzard by $s2% and its periodic interval by $s3%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 128, 'EffectSpellClassMaskA_1': 128, 'EffectSpellClassMaskA_2': 524416, 'EffectSpellClassMaskA_3': 524416, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

frost_warding_11189 = spell(
    id=11189,
    name='Frost Warding',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.DUMMY, base_points=14),
    ],
    spell_icon_id=501,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the armor and resistances given by your Frost Armor and Ice Armor spells by $s1%.  In addition, gives your Frost Ward and Fire Ward a $s2% chance to negate the warded damage spell and restore mana equal to the damage caused. |cFF9D9D9DAt max rank, while Frost Armor or Ice Armor is active, physical damage taken is reduced by an additional 20%.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_cone_of_cold_11190 = spell(
    id=11190,
    name='Improved Cone of Cold',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=74396),
    ],
    spell_icon_id=35,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 6, Improved Cone of Cold). effect1 (dmg%) kept the pulled data's mechanic/scope (ADD_PCT_MODIFIER, SPELLMOD_DAMAGE, classmask already Cone-of-Cold-only) but retuned 14/24/34 -> 19/39/59 (stored+1 = 20/40/60%, spec's value; old data was a stale/different tuning). effect2 (new, all 3 ranks): FoF-chance-on-hit, same shape as Improved Blizzard's own FoF grant -- native PROC_TRIGGER_SPELL straight to the Fingers of Frost charge spell (74396), 33/66/100% (literal, not stored+1 -- ProcChance convention). ",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage dealt by your Cone of Cold spell by $s1%, and gives it a $h% chance to grant Fingers of Frost. |cFF9D9D9DAt max rank, after casting Cone of Cold, your Blizzard channels twice as fast.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 512, 'EffectSpellClassMaskA_1': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 65536, 'EffectSpellClassMaskA_2': 512},
)

ice_shards_11207 = spell(
    id=11207,
    name='Ice Shards',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=1236,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Frost spells by $s1%. |cFF9D9D9DAt max rank, increases damage against frozen targets by 6%.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131808, 'EffectSpellClassMaskA_2': 1052672, 'EffectSpellClassMaskA_3': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

alacrity_11210 = spell(
    id=11210,
    name='Alacrity',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=306, misc_value=4194304),
    ],
    spell_icon_id=2022,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): repoints stock Arcane Subtlety\'s slot (id 74) to (0,0). "Increases your cooldown reduction by 5/10/15%." SPELL_AURA_MOD_CUSTOM_STAT_PCT (306), misc_value 1<<CR_COOLDOWN_HASTE (4194304). raw_overrides fully replaced (not merged) - the earlier version of this edit left stale classmask/attribute fields from the real Arcane Subtlety talent this slot used to hold; caught and fixed. Bugfix (playtest report, 2026-09-08): tooltip retitled "Cooldown Haste" to match the actual stat name (docs/itemization-changes.md) rather than the generic "cooldown reduction" phrasing - the underlying mechanic (GetCooldownHastePercentage()) was already correct.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Cooldown Haste by 5%.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_subtlety_11213 = spell(
    id=11213,
    name='Arcane Subtlety',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=72, misc_value=64),
    ],
    spell_icon_id=74,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): repoints stock Arcane Concentration\'s slot (id 75) to (1,1), trimmed to 3 ranks. "Increases the range of your damaging spells with a channeling or cast time by 2/4/6 yards." effect1 SPELL_AURA_ADD_FLAT_MODIFIER (107)/SPELLMOD_RANGE (5), EffectSpellClassMaskA_1 (raw_override, NOT the friendly effect misc_value) covering Frostbolt|Fireball|Arcane Blast|Blizzard|Pyroblast|Arcane Missiles - individually verified live via the DB overlay; not exhaustive (Frostfire Bolt, Cone of Cold, a few others not yet verified), flagged for a follow-up data pass. "Reduces the mana cost of your Arcane Spells by 4/8/12%" - effect2 SPELL_AURA_MOD_POWER_COST_SCHOOL_PCT (72), misc_value 64 (Arcane school, not classmask - no scoping risk). Capstone (rank 3 only, "threat reduced by 30%") - effect3 SPELL_AURA_MOD_THREAT (10), misc_value 64. Corrected from an earlier broken version of this edit: the range effect\'s classmask was accidentally written into the friendly effect1 JSON blob instead of raw_overrides (silently ignored there), and stale trigger_spell/classmask/attribute fields from the real Arcane Concentration data this slot used to hold survived a merge instead of being cleared - both caught by generate.py\'s lint WARNING and fixed here with a full (non-merging) rewrite.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your damaging spells with a channeling or cast time by 2 yards. Reduces the mana cost of your Arcane Spells by 4%. \n\n|cFF9D9D9DCapstone Bonus: All threat generated is reduced by 30%.|r', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 541591713},
)

arcane_meditation_11222 = spell(
    id=11222,
    name='Arcane Meditation',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=192),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=216),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=134),
    ],
    spell_icon_id=2894,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): repoints stock Arcane Focus\'s slot (id 76) to (0,1). "Increases spell, ranged and melee haste by 2/4/6%. Allows 25% of your mana regeneration to continue while casting." effect1 SPELL_AURA_MOD_MELEE_RANGED_HASTE (192), effect2 SPELL_AURA_HASTE_SPELLS (216), effect3 SPELL_AURA_MOD_MANA_REGEN_INTERRUPT (134, flat 25% every rank - the real stock mechanism, capped/applied directly by Player::UpdateManaRegen()). raw_overrides fully replaced (not merged) - the earlier version left stale classmask fields from Arcane Focus; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell, ranged and melee haste by 2%. Allows 25% of your mana regeneration to continue while casting.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_stability_11237 = spell(
    id=11237,
    name='Arcane Stability',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=9),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=306, misc_value=2048),
    ],
    spell_icon_id=225,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): retuned in place (same talent, same slot, tab 81 tier 0 col 2). "Increases your Proc Chance by 3/6/9%. Reduces spell pushback suffered from damaging attacks by 100%." effect1 (pushback, pre-existing SPELLMOD via apply_aura 108/misc_value 9, classmask-scoped to Arcane Missiles/Blast) retuned to a flat 100% on all 3 ranks (was 20/40/60/80/100% across 5 ranks - trimmed to 3, ranks 4/5\'s rows (16769/16770) left orphaned/unedited). effect2 is new: SPELL_AURA_MOD_CUSTOM_STAT_PCT (306), misc_value = 1<<CR_PROC_CHANCE (2048). Bugfix (playtest report, 2026-09-08): the Proc Chance clause was added as effect2 but never made it into the tooltip text - Description_Lang_enUS now states it explicitly, per rank.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Proc Chance by 3%. Reduces the pushback suffered from damaging attacks while casting Arcane Missiles and Arcane Blast by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536872960, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

spell_impact_11242 = spell(
    id=11242,
    name='Spell Impact',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=122,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): retuned in place, same slot, moved from stock (2,1) to (1,2). Kept the existing correct classmask (EffectSpellClassMaskA_1 537006611 / _A_2 64 - Arcane Explosion, Arcane Blast, Blast Wave, Fire Blast, Scorch, Fireball, Ice Lance, Cone of Cold) rather than guessing at bits for the design doc's expanded list (Arcane Barrage, Arcane Orb, Arcane Overload, Pyroblast) - deferred to Phase 3/a follow-up data pass. Values retuned to 3/6/9% per the design doc.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Arcane Explosion, Arcane Blast, Arcane Barrage, Arcane Overload, Blast Wave, Fire Blast, Scorch, Pyroblast, Ice Lance and Cone of Cold spells by an additional $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 541200914, 'EffectSpellClassMaskA_2': 32832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_3': 2},
)

arcane_concentration_11247 = spell(
    id=11247,
    name='Arcane Concentration',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12536),
    ],
    spell_icon_id=212,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): repoints stock Magic Attunement\'s slot (id 82) to (2,0). "Gives you a 5/10/15% chance of entering a Clearcasting state after casting a damaging spell." effect1 SPELL_AURA_PROC_TRIGGER_SPELL (42) triggering the real stock Clearcasting buff (12536), ProcTypeMask 87376 ("damaging spell hits", same as the real stock Arcane Concentration talent) - proc chance is the spell\'s own ProcChance column, not an effect value. No classmask on the trigger itself (ProcTypeMask already scopes it; the real talent\'s own classmask appears to be additional narrowing not needed here). "...and increases its damage by your Mastery" NOT built this phase - needs a live Player::GetMasteryPercentage() read when Clearcasting is consumed, likely extending spell_mage_clearcasting; deferred to Phase 3. raw_overrides/effects fully replaced (not merged) - the earlier version left stale classmask fields from Magic Attunement; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a 5% chance of entering a Clearcasting state after casting a damaging spell.', 'ProcChance': 5, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 87376},
)

arcane_shielding_11252 = spell(
    id=11252,
    name='Arcane Shielding',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=209,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 3): repoints stock Arcane Shielding\'s slot (id 83) to (3,0) - real content (Mana Shield/Mage Armor synergy) doesn\'t match this design, fully replaced. "Increases the amount absorbed by your Fire Ward, Frost Ward and Arcane Ward by 15/30%." "...your damage dealt is increased by 5/10% for 10 sec" on absorb built in Phase 3 (spell_mage_arcane_shielding_proc, spell_mage.cpp). Bugfix (2026-09-09, see docs/bugs-and-fixes.md "Missile Barrage\'s -50% still computed to -65%..."): effect1 used to be a classmask-scoped SPELLMOD_EFFECT1 (the only dword all three Wards share, 8, also happens to be part of Missile Barrage\'s (44401) own real family flags - a genuine, unfixable-by-relocating collision, not a wrong-slot mistake). Reimplemented as a plain SPELL_AURA_DUMMY marker (matching effect2\'s existing rank-lookup marker) read directly by a new DoEffectCalcAmount hook on spell_mage_arcane_shielding_proc (bound to 543/6143/28609/200068, same as its existing post-absorb damage-buff trigger) - no classmask involved at all, so no collision is possible.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount absorbed by your Fire Ward, Frost Ward and Arcane Ward by 15%. Each time one of these effects absorbs damage, your damage dealt is increased by 5% for 10 seconds.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_counterspell_11255 = spell(
    id=11255,
    name='Improved Counterspell',
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
    spell_icon_id=17,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 3): repoints stock Improved Counterspell\'s slot (id 88) to (3,1) - real content (silence-on-cast proc only, no CD reduction) replaced. "Reduce the cooldown of your Counterspell ability by 5/10 seconds." effect1 SPELL_AURA_ADD_FLAT_MODIFIER (107)/SPELLMOD_COOLDOWN (11), EffectSpellClassMaskA_1 = 16384 (Counterspell, 2139 - verified live via the DB overlay) in raw_overrides. Capstone ("Counterspell now silences the target for 2 sec", rank 2) NOT built this phase - adds a wholly new effect to Counterspell, not expressible as a SpellMod; may also need a spell_proc/spell_proc_event row outside dbc-tools\' pipeline. Deferred to Phase 3. raw_overrides fully replaced (not merged) - the earlier version left a stale AttributesEx3 flag from the real silence-proc data; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Counterspell ability by 5 seconds. \n\n|cFF9D9D9DCapstone Bonus: Your Counterspell ability now silences the target for 2 sec.|r', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 16384},
)

critical_mass_11367 = spell(
    id=11367,
    name='Critical Mass',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=71, misc_value=4),
    ],
    spell_icon_id=117,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Fire spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12582935, 'EffectSpellClassMaskA_2': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 2, 'SpellPriority': 50},
)

critical_mass_11368 = spell(
    id=11368,
    name='Critical Mass',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=71, misc_value=4),
    ],
    spell_icon_id=117,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Fire spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12582935, 'EffectSpellClassMaskA_2': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 2, 'SpellPriority': 50},
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

improved_fireball_12338 = spell(
    id=12338,
    name='Improved Fireball',
    school=School.FIRE,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-201, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=185,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Fireball spell by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_fireball_12339 = spell(
    id=12339,
    name='Improved Fireball',
    school=School.FIRE,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-301, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=185,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Fireball spell by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_fireball_12340 = spell(
    id=12340,
    name='Improved Fireball',
    school=School.FIRE,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-401, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=185,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Fireball spell by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_fireball_12341 = spell(
    id=12341,
    name='Improved Fireball',
    school=School.FIRE,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-501, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=185,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Fireball spell by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

world_in_flames_12349 = spell(
    id=12349,
    name='World in Flames',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2948,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your Flamestrike, Pyroblast, Blast Wave, Dragon's Breath, Living Bomb, Blizzard and Arcane Explosion spells by $s1%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12587140, 'EffectSpellClassMaskA_2': 65600, 'EffectSpellClassMaskB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

world_in_flames_12350 = spell(
    id=12350,
    name='World in Flames',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2948,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your Flamestrike, Pyroblast, Blast Wave, Dragon's Breath, Living Bomb, Blizzard and Arcane Explosion spells by $s1%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12587140, 'EffectSpellClassMaskA_2': 65600, 'EffectSpellClassMaskB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

burning_soul_12351 = spell(
    id=12351,
    name='Burning Soul',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=69, implicit_target_a=1, apply_aura=108, misc_value=9),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=4),
    ],
    spell_icon_id=11,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the pushback suffered from damaging attacks while casting Fire spells by $s1% and reduces the threat caused by your Fire spells by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EffectSpellClassMaskA_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

flame_throwing_12353 = spell(
    id=12353,
    name='Flame Throwing',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=5),
    ],
    spell_icon_id=136,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of all Fire spells except Frostfire Bolt by $s1 yards.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194327, 'EffectSpellClassMaskA_2': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

impact_12357 = spell(
    id=12357,
    name='Impact',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64343),
    ],
    spell_icon_id=45,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 136, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your damaging spells a $h% chance to cause the next Fire Blast you cast to stun the target for $12355d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 7, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

impact_12358 = spell(
    id=12358,
    name='Impact',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64343),
    ],
    spell_icon_id=45,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 136, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your damaging spells a $h% chance to cause the next Fire Blast you cast to stun the target for $12355d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

fire_power_12378 = spell(
    id=12378,
    name='Fire Power',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=31,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Fire spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12845079, 'EffectSpellClassMaskA_2': 69704, 'EffectSpellClassMaskB_1': 4194309, 'EffectSpellClassMaskB_2': 135168, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

fire_power_12398 = spell(
    id=12398,
    name='Fire Power',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=31,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Fire spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12845079, 'EffectSpellClassMaskA_2': 69704, 'EffectSpellClassMaskB_1': 4194309, 'EffectSpellClassMaskB_2': 135168, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

fire_power_12399 = spell(
    id=12399,
    name='Fire Power',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=31,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Fire spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12845079, 'EffectSpellClassMaskA_2': 69704, 'EffectSpellClassMaskB_1': 4194309, 'EffectSpellClassMaskB_2': 135168, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

fire_power_12400 = spell(
    id=12400,
    name='Fire Power',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=31,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Fire spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12845079, 'EffectSpellClassMaskA_2': 69704, 'EffectSpellClassMaskB_1': 4194309, 'EffectSpellClassMaskB_2': 135168, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_stability_12463 = spell(
    id=12463,
    name='Arcane Stability',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=9),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=306, misc_value=2048),
    ],
    spell_icon_id=225,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): retuned in place (same talent, same slot, tab 81 tier 0 col 2). "Increases your Proc Chance by 3/6/9%. Reduces spell pushback suffered from damaging attacks by 100%." effect1 (pushback, pre-existing SPELLMOD via apply_aura 108/misc_value 9, classmask-scoped to Arcane Missiles/Blast) retuned to a flat 100% on all 3 ranks (was 20/40/60/80/100% across 5 ranks - trimmed to 3, ranks 4/5\'s rows (16769/16770) left orphaned/unedited). effect2 is new: SPELL_AURA_MOD_CUSTOM_STAT_PCT (306), misc_value = 1<<CR_PROC_CHANCE (2048).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Proc Chance by 6%. Reduces the pushback suffered from damaging attacks while casting Arcane Missiles and Arcane Blast by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536872960, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_stability_12464 = spell(
    id=12464,
    name='Arcane Stability',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=9),
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=306, misc_value=2048),
    ],
    spell_icon_id=225,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): retuned in place (same talent, same slot, tab 81 tier 0 col 2). "Increases your Proc Chance by 3/6/9%. Reduces spell pushback suffered from damaging attacks by 100%." effect1 (pushback, pre-existing SPELLMOD via apply_aura 108/misc_value 9, classmask-scoped to Arcane Missiles/Blast) retuned to a flat 100% on all 3 ranks (was 20/40/60/80/100% across 5 ranks - trimmed to 3, ranks 4/5\'s rows (16769/16770) left orphaned/unedited). effect2 is new: SPELL_AURA_MOD_CUSTOM_STAT_PCT (306), misc_value = 1<<CR_PROC_CHANCE (2048).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Proc Chance by 9%. Reduces the pushback suffered from damaging attacks while casting Arcane Missiles and Arcane Blast by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536872960, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

spell_impact_12467 = spell(
    id=12467,
    name='Spell Impact',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=122,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): retuned in place, same slot, moved from stock (2,1) to (1,2). Kept the existing correct classmask (EffectSpellClassMaskA_1 537006611 / _A_2 64 - Arcane Explosion, Arcane Blast, Blast Wave, Fire Blast, Scorch, Fireball, Ice Lance, Cone of Cold) rather than guessing at bits for the design doc's expanded list (Arcane Barrage, Arcane Orb, Arcane Overload, Pyroblast) - deferred to Phase 3/a follow-up data pass. Values retuned to 3/6/9% per the design doc.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Arcane Explosion, Arcane Blast, Arcane Barrage, Arcane Overload, Blast Wave, Fire Blast, Scorch, Pyroblast, Ice Lance and Cone of Cold spells by an additional $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 541200914, 'EffectSpellClassMaskA_2': 32832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_3': 2},
)

spell_impact_12469 = spell(
    id=12469,
    name='Spell Impact',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=122,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): retuned in place, same slot, moved from stock (2,1) to (1,2). Kept the existing correct classmask (EffectSpellClassMaskA_1 537006611 / _A_2 64 - Arcane Explosion, Arcane Blast, Blast Wave, Fire Blast, Scorch, Fireball, Ice Lance, Cone of Cold) rather than guessing at bits for the design doc's expanded list (Arcane Barrage, Arcane Orb, Arcane Overload, Pyroblast) - deferred to Phase 3/a follow-up data pass. Values retuned to 3/6/9% per the design doc.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Arcane Explosion, Arcane Blast, Arcane Barrage, Arcane Overload, Blast Wave, Fire Blast, Scorch, Pyroblast, Ice Lance and Cone of Cold spells by an additional $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 541200914, 'EffectSpellClassMaskA_2': 32832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_3': 2},
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

improved_frostbolt_12473 = spell(
    id=12473,
    name='Improved Frostbolt',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=188,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Frostbolt and Ice Lance spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131104, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_blizzard_12487 = spell(
    id=12487,
    name='Improved Blizzard',
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
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=112, misc_value=988),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=19),
    ],
    spell_icon_id=285,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Adds a chill effect to your Blizzard spell.  This effect lowers the target's movement speed by $12484s1%.  Lasts $12484d.  Also reduces the mana cost of Blizzard by $s2% and its periodic interval by $s3%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 128, 'EffectSpellClassMaskA_1': 128, 'EffectSpellClassMaskA_2': 524416, 'EffectSpellClassMaskA_3': 524416, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_blizzard_12488 = spell(
    id=12488,
    name='Improved Blizzard',
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
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=112, misc_value=989),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-29, implicit_target_a=1, apply_aura=108, misc_value=19),
    ],
    spell_icon_id=285,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Adds a chill effect to your Blizzard spell.  This effect lowers the target's movement speed by $12484s1%.  Lasts $12484d.  Also reduces the mana cost of Blizzard by $s2% and its periodic interval by $s3%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 128, 'EffectSpellClassMaskA_1': 128, 'EffectSpellClassMaskA_2': 524416, 'EffectSpellClassMaskA_3': 524416, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_cone_of_cold_12489 = spell(
    id=12489,
    name='Improved Cone of Cold',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=74396),
    ],
    spell_icon_id=35,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 6, Improved Cone of Cold). effect1 (dmg%) kept the pulled data's mechanic/scope (ADD_PCT_MODIFIER, SPELLMOD_DAMAGE, classmask already Cone-of-Cold-only) but retuned 14/24/34 -> 19/39/59 (stored+1 = 20/40/60%, spec's value; old data was a stale/different tuning). effect2 (new, all 3 ranks): FoF-chance-on-hit, same shape as Improved Blizzard's own FoF grant -- native PROC_TRIGGER_SPELL straight to the Fingers of Frost charge spell (74396), 33/66/100% (literal, not stored+1 -- ProcChance convention). ",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage dealt by your Cone of Cold spell by $s1%, and gives it a $h% chance to grant Fingers of Frost. |cFF9D9D9DAt max rank, after casting Cone of Cold, your Blizzard channels twice as fast.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 512, 'EffectSpellClassMaskA_1': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 65536, 'EffectSpellClassMaskA_2': 512},
)

improved_cone_of_cold_12490 = spell(
    id=12490,
    name='Improved Cone of Cold',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=74396),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200020),
    ],
    spell_icon_id=35,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 6, Improved Cone of Cold). effect1 (dmg%) kept the pulled data's mechanic/scope (ADD_PCT_MODIFIER, SPELLMOD_DAMAGE, classmask already Cone-of-Cold-only) but retuned 14/24/34 -> 19/39/59 (stored+1 = 20/40/60%, spec's value; old data was a stale/different tuning). effect2 (new, all 3 ranks): FoF-chance-on-hit, same shape as Improved Blizzard's own FoF grant -- native PROC_TRIGGER_SPELL straight to the Fingers of Frost charge spell (74396), 33/66/100% (literal, not stored+1 -- ProcChance convention). effect3 (rank 3 only, capstone): 'your Blizzard channels twice as fast' after casting Cone of Cold -- a new buff (200020, ADD_PCT_MODIFIER/SPELLMOD_ACTIVATION_TIME -50%, classmask Blizzard-only, ProcCharges=1) auto-consumed by the native SpellMod charge system on the next Blizzard cast (Player::ApplySpellMod's charge-consumption path, no script needed) -- duration window (15 sec) is a first-pass assumption since the redesign text doesn't give one, flagged for playtest.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage dealt by your Cone of Cold spell by $s1%, and gives it a $h% chance to grant Fingers of Frost. After casting Cone of Cold, your Blizzard channels twice as fast.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 512, 'EffectSpellClassMaskA_1': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 65536, 'EffectSpellClassMaskA_2': 512, 'EffectSpellClassMaskA_3': 512},
)

frostbite_12496 = spell(
    id=12496,
    name='Frostbite',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12494),
    ],
    spell_icon_id=119,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dealing direct Frost damage has a $s1% chance to freeze the target for $12494d.  The freeze breaks on damage. \n\n|cFF9D9D9DCapstone Bonus: Increases the damage of your Frost spells against frozen targets based on your Mastery.|r', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 4096, 'EffectSpellClassMaskB_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassMask_2': 512, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

frostbite_12497 = spell(
    id=12497,
    name='Frostbite',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12494),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=119,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dealing direct Frost damage has a $s1% chance to freeze the target for $12494d.  The freeze breaks on damage. \n\nCapstone Bonus: Increases the damage of your Frost spells against frozen targets based on your Mastery.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 4096, 'EffectSpellClassMaskB_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 15, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassMask_2': 512, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

frost_channeling_12518 = spell(
    id=12518,
    name='Frost Channeling',
    school=School.FROST,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-9, implicit_target_a=1, apply_aura=72, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=16),
    ],
    spell_icon_id=15,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Frost spells and abilities by $s1% and reduces the threat caused by $s2%. |cFF9D9D9DAt max rank, killing an enemy that yields experience or honor with Frost damage restores 12% of your mana.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1, 'EffectSpellClassMaskA_1': 655360, 'EffectSpellClassMaskA_2': 2049, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

frost_channeling_12519 = spell(
    id=12519,
    name='Frost Channeling',
    school=School.FROST,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-13, implicit_target_a=1, apply_aura=72, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=15,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Frost spells and abilities by $s1% and reduces the threat caused by $s2%.  Killing an enemy that yields experience or honor with Frost damage restores 12% of your mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1, 'EffectSpellClassMaskA_1': 655360, 'EffectSpellClassMaskA_2': 2049, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

permafrost_12569 = spell(
    id=12569,
    name='Permafrost',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-8, implicit_target_a=1, apply_aura=107, misc_value=3),
    ],
    spell_icon_id=143,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 2, Permafrost). Base effect kept the pulled data\'s own numbers (already matched spec\'s 1/2/3 sec duration + 4/7/10% additional slow via the stored+1 convention) but rescoped from the old talent\'s actual shape -- a target-side debuff (duration/slow/heal-received-reduction applied to whoever the mage\'s Frostbolt/Cone of Cold/Frost Nova hit) -- to a caster-side SpellMod pair (SPELLMOD_DURATION + SPELLMOD_EFFECT1, classmask 544 = Frostbolt|Cone of Cold in word A) boosting the caster\'s own cast of those spells, matching every other \'duration+value modifier\' talent this project has built (Arctic Reach, Chilled to the Bone). The old effect3 (SPELLMOD_EFFECT3, -8/-14/-21, confirmed via the Chilled npc-caster spells 6136/7321\'s own effect3 = SPELL_AURA_MOD_HEALING_PCT to be the dropped tooltip\'s \'reduces healing received\' clause) is not in the new spec and was removed outright, not carried forward. \'Frost Shock\' in the redesign\'s talent text was dropped per user decision (2026-08-24) -- not a real Mage spell (Shaman-only in this game), most likely a stray copy-paste word; scoped to Cone of Cold/Frostbolt/Ice Armor only. Ice Armor\'s own melee-reactive slow (6136 Frost Armor / 7321 Ice Armor\'s \'Chilled\' trigger spells, npc.csv) has no SpellFamilyFlags of its own -- same classmask-unreachable shape as Frozen Orb hit this project before -- so it\'s boosted live in spell_mage_chilled (spell_mage.cpp) instead, same \'read the mage\'s own SpellMod amount and fold it in\' idiom as spell_mage_frozen_orb_pulse\'s Chilled to the Bone fix. Capstone (rank 3 only): see effect3. Playtest bugfix (2026-08-27, user report - "Permafrost reduces the effects of everything by 10%, not just move speed"): the SPELLMOD_EFFECT1 modifier\'s classmask (544, Frostbolt|Cone of Cold) was stored under EffectSpellClassMaskA_2, which the naming convention suggests is "effect index 2\'s word A" but which spell_dbc/DBCStructure.h actually reads as "effect index 0(=A)\'s word 2" - dword-major, not effect-major, unlike every other _1/_2/_3-suffixed field in this schema. That left the real target, effect index 1\'s own classmask, all-zero, and SpellInfo::IsAffected treats an all-zero classmask as matching every spell in the family - so the -4/-7/-10% modifier applied unconditionally to EFFECT_0 of every mage spell (including Evocation\'s mana-restore %) instead of just Frostbolt/Cone of Cold. Fixed by moving the value to EffectSpellClassMaskB_1 (effect index 1(=B)\'s word 1), which is what the engine actually reads for effect 1\'s classmask. See data/sql/updates/pending_db_world/frost_mage_rework.sql (merged Frost Mage rework migration; originally rev_1787820084006262155.sql) for the original diagnosis (that migration was a live DB-only patch of the affected rows; this is the matching source-of-truth fix so future full regenerations don\'t reintroduce it).',
    raw_overrides={'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the duration of your Cone of Cold and Frostbolt slow effects by ${{$m1/1000}}.1 sec, and reduces the target's speed by an additional $s2%. Also affects Ice Armor's chilling effect. |cFF9D9D9DAt max rank: each 1 sec you spend moving grants Permafrost, increasing the damage of your next Ice Lance by 20%. Stacks up to 5 times.|r", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 544, 'EffectSpellClassMaskB_1': 544, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

permafrost_12571 = spell(
    id=12571,
    name='Permafrost',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=226, amplitude=1000),
    ],
    spell_icon_id=143,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 2, Permafrost). Base effect kept the pulled data\'s own numbers (already matched spec\'s 1/2/3 sec duration + 4/7/10% additional slow via the stored+1 convention) but rescoped from the old talent\'s actual shape -- a target-side debuff (duration/slow/heal-received-reduction applied to whoever the mage\'s Frostbolt/Cone of Cold/Frost Nova hit) -- to a caster-side SpellMod pair (SPELLMOD_DURATION + SPELLMOD_EFFECT1, classmask 544 = Frostbolt|Cone of Cold in word A) boosting the caster\'s own cast of those spells, matching every other \'duration+value modifier\' talent this project has built (Arctic Reach, Chilled to the Bone). The old effect3 (SPELLMOD_EFFECT3, -8/-14/-21, confirmed via the Chilled npc-caster spells 6136/7321\'s own effect3 = SPELL_AURA_MOD_HEALING_PCT to be the dropped tooltip\'s \'reduces healing received\' clause) is not in the new spec and was removed outright, not carried forward. \'Frost Shock\' in the redesign\'s talent text was dropped per user decision (2026-08-24) -- not a real Mage spell (Shaman-only in this game), most likely a stray copy-paste word; scoped to Cone of Cold/Frostbolt/Ice Armor only. Ice Armor\'s own melee-reactive slow (6136 Frost Armor / 7321 Ice Armor\'s \'Chilled\' trigger spells, npc.csv) has no SpellFamilyFlags of its own -- same classmask-unreachable shape as Frozen Orb hit this project before -- so it\'s boosted live in spell_mage_chilled (spell_mage.cpp) instead, same \'read the mage\'s own SpellMod amount and fold it in\' idiom as spell_mage_frozen_orb_pulse\'s Chilled to the Bone fix. Capstone (rank 3 only): see effect3. Playtest bugfix (2026-08-27, user report - "Permafrost reduces the effects of everything by 10%, not just move speed"): the SPELLMOD_EFFECT1 modifier\'s classmask (544, Frostbolt|Cone of Cold) was stored under EffectSpellClassMaskA_2, which the naming convention suggests is "effect index 2\'s word A" but which spell_dbc/DBCStructure.h actually reads as "effect index 0(=A)\'s word 2" - dword-major, not effect-major, unlike every other _1/_2/_3-suffixed field in this schema. That left the real target, effect index 1\'s own classmask, all-zero, and SpellInfo::IsAffected treats an all-zero classmask as matching every spell in the family - so the -4/-7/-10% modifier applied unconditionally to EFFECT_0 of every mage spell (including Evocation\'s mana-restore %) instead of just Frostbolt/Cone of Cold. Fixed by moving the value to EffectSpellClassMaskB_1 (effect index 1(=B)\'s word 1), which is what the engine actually reads for effect 1\'s classmask. See data/sql/updates/pending_db_world/frost_mage_rework.sql (merged Frost Mage rework migration; originally rev_1787820084006262155.sql) for the original diagnosis (that migration was a live DB-only patch of the affected rows; this is the matching source-of-truth fix so future full regenerations don\'t reintroduce it).',
    raw_overrides={'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the duration of your Cone of Cold and Frostbolt slow effects by ${{$m1/1000}}.1 sec, and reduces the target's speed by an additional $s2%. Also affects Ice Armor's chilling effect. Each 1 sec you spend moving grants Permafrost, increasing the damage of your next Ice Lance by 20%. Stacks up to 5 times.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 544, 'EffectSpellClassMaskB_1': 544, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_subtlety_12574 = spell(
    id=12574,
    name='Arcane Subtlety',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=-9, implicit_target_a=1, apply_aura=72, misc_value=64),
    ],
    spell_icon_id=74,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): repoints stock Arcane Concentration\'s slot (id 75) to (1,1), trimmed to 3 ranks. "Increases the range of your damaging spells with a channeling or cast time by 2/4/6 yards." effect1 SPELL_AURA_ADD_FLAT_MODIFIER (107)/SPELLMOD_RANGE (5), EffectSpellClassMaskA_1 (raw_override, NOT the friendly effect misc_value) covering Frostbolt|Fireball|Arcane Blast|Blizzard|Pyroblast|Arcane Missiles - individually verified live via the DB overlay; not exhaustive (Frostfire Bolt, Cone of Cold, a few others not yet verified), flagged for a follow-up data pass. "Reduces the mana cost of your Arcane Spells by 4/8/12%" - effect2 SPELL_AURA_MOD_POWER_COST_SCHOOL_PCT (72), misc_value 64 (Arcane school, not classmask - no scoping risk). Capstone (rank 3 only, "threat reduced by 30%") - effect3 SPELL_AURA_MOD_THREAT (10), misc_value 64. Corrected from an earlier broken version of this edit: the range effect\'s classmask was accidentally written into the friendly effect1 JSON blob instead of raw_overrides (silently ignored there), and stale trigger_spell/classmask/attribute fields from the real Arcane Concentration data this slot used to hold survived a merge instead of being cleared - both caught by generate.py\'s lint WARNING and fixed here with a full (non-merging) rewrite.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your damaging spells with a channeling or cast time by 4 yards. Reduces the mana cost of your Arcane Spells by 8%. \n\n|cFF9D9D9DCapstone Bonus: All threat generated is reduced by 30%.|r', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 541591713},
)

arcane_subtlety_12575 = spell(
    id=12575,
    name='Arcane Subtlety',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=-13, implicit_target_a=1, apply_aura=72, misc_value=64),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=64),
    ],
    spell_icon_id=74,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): repoints stock Arcane Concentration\'s slot (id 75) to (1,1), trimmed to 3 ranks. "Increases the range of your damaging spells with a channeling or cast time by 2/4/6 yards." effect1 SPELL_AURA_ADD_FLAT_MODIFIER (107)/SPELLMOD_RANGE (5), EffectSpellClassMaskA_1 (raw_override, NOT the friendly effect misc_value) covering Frostbolt|Fireball|Arcane Blast|Blizzard|Pyroblast|Arcane Missiles - individually verified live via the DB overlay; not exhaustive (Frostfire Bolt, Cone of Cold, a few others not yet verified), flagged for a follow-up data pass. "Reduces the mana cost of your Arcane Spells by 4/8/12%" - effect2 SPELL_AURA_MOD_POWER_COST_SCHOOL_PCT (72), misc_value 64 (Arcane school, not classmask - no scoping risk). Capstone (rank 3 only, "threat reduced by 30%") - effect3 SPELL_AURA_MOD_THREAT (10), misc_value 64. Corrected from an earlier broken version of this edit: the range effect\'s classmask was accidentally written into the friendly effect1 JSON blob instead of raw_overrides (silently ignored there), and stale trigger_spell/classmask/attribute fields from the real Arcane Concentration data this slot used to hold survived a merge instead of being cleared - both caught by generate.py\'s lint WARNING and fixed here with a full (non-merging) rewrite.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your damaging spells with a channeling or cast time by 6 yards. Reduces the mana cost of your Arcane Spells by 12%. \n\nCapstone Bonus: All threat generated is reduced by 30%.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 541591713},
)

arcane_concentration_12576 = spell(
    id=12576,
    name='Arcane Concentration',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12536),
    ],
    spell_icon_id=212,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 8388608, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a $h% chance of entering a Clearcasting state after any damage spell hits a target.  The Clearcasting state reduces the mana cost of your next damage spell by $/10;12536s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 128, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 8, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_concentration_12577 = spell(
    id=12577,
    name='Arcane Concentration',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12536),
    ],
    spell_icon_id=212,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 8388608, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a $h% chance of entering a Clearcasting state after any damage spell hits a target.  The Clearcasting state reduces the mana cost of your next damage spell by $/10;12536s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 128, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

alacrity_12592 = spell(
    id=12592,
    name='Alacrity',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=306, misc_value=4194304),
    ],
    spell_icon_id=2022,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): repoints stock Arcane Subtlety\'s slot (id 74) to (0,0). "Increases your cooldown reduction by 5/10/15%." SPELL_AURA_MOD_CUSTOM_STAT_PCT (306), misc_value 1<<CR_COOLDOWN_HASTE (4194304). raw_overrides fully replaced (not merged) - the earlier version of this edit left stale classmask/attribute fields from the real Arcane Subtlety talent this slot used to hold; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Cooldown Haste by 10%.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_counterspell_12598 = spell(
    id=12598,
    name='Improved Counterspell',
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
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=17,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 3): repoints stock Improved Counterspell\'s slot (id 88) to (3,1) - real content (silence-on-cast proc only, no CD reduction) replaced. "Reduce the cooldown of your Counterspell ability by 5/10 seconds." effect1 SPELL_AURA_ADD_FLAT_MODIFIER (107)/SPELLMOD_COOLDOWN (11), EffectSpellClassMaskA_1 = 16384 (Counterspell, 2139 - verified live via the DB overlay) in raw_overrides. Capstone ("Counterspell now silences the target for 2 sec", rank 2) NOT built this phase - adds a wholly new effect to Counterspell, not expressible as a SpellMod; may also need a spell_proc/spell_proc_event row outside dbc-tools\' pipeline. Deferred to Phase 3. raw_overrides fully replaced (not merged) - the earlier version left a stale AttributesEx3 flag from the real silence-proc data; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Counterspell ability by 10 seconds. \n\nCapstone Bonus: Your Counterspell ability now silences the target for 2 sec.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 16384},
)

arcane_shielding_12605 = spell(
    id=12605,
    name='Arcane Shielding',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=209,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 3): repoints stock Arcane Shielding\'s slot (id 83) to (3,0) - real content (Mana Shield/Mage Armor synergy) doesn\'t match this design, fully replaced. "Increases the amount absorbed by your Fire Ward, Frost Ward and Arcane Ward by 15/30%." "...your damage dealt is increased by 5/10% for 10 sec" on absorb built in Phase 3 (spell_mage_arcane_shielding_proc, spell_mage.cpp). Bugfix (2026-09-09, see docs/bugs-and-fixes.md "Missile Barrage\'s -50% still computed to -65%..."): effect1 used to be a classmask-scoped SPELLMOD_EFFECT1 (the only dword all three Wards share, 8, also happens to be part of Missile Barrage\'s (44401) own real family flags - a genuine, unfixable-by-relocating collision, not a wrong-slot mistake). Reimplemented as a plain SPELL_AURA_DUMMY marker (matching effect2\'s existing rank-lookup marker) read directly by a new DoEffectCalcAmount hook on spell_mage_arcane_shielding_proc (bound to 543/6143/28609/200068, same as its existing post-absorb damage-buff trigger) - no classmask involved at all, so no collision is possible.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount absorbed by your Fire Ward, Frost Ward and Arcane Ward by 30%. Each time one of these effects absorbs damage, your damage dealt is increased by 10% for 10 seconds.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_concentration_12606 = spell(
    id=12606,
    name='Arcane Concentration',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12536),
    ],
    spell_icon_id=212,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): repoints stock Magic Attunement\'s slot (id 82) to (2,0). "Gives you a 5/10/15% chance of entering a Clearcasting state after casting a damaging spell." effect1 SPELL_AURA_PROC_TRIGGER_SPELL (42) triggering the real stock Clearcasting buff (12536), ProcTypeMask 87376 ("damaging spell hits", same as the real stock Arcane Concentration talent) - proc chance is the spell\'s own ProcChance column, not an effect value. No classmask on the trigger itself (ProcTypeMask already scopes it; the real talent\'s own classmask appears to be additional narrowing not needed here). "...and increases its damage by your Mastery" NOT built this phase - needs a live Player::GetMasteryPercentage() read when Clearcasting is consumed, likely extending spell_mage_clearcasting; deferred to Phase 3. raw_overrides/effects fully replaced (not merged) - the earlier version left stale classmask fields from Magic Attunement; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a 10% chance of entering a Clearcasting state after casting a damaging spell.', 'ProcChance': 10, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 87376},
)

ice_shards_12672 = spell(
    id=12672,
    name='Ice Shards',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=69, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=1236,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Frost spells by $s1%. |cFF9D9D9DAt max rank, increases damage against frozen targets by 6%.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131808, 'EffectSpellClassMaskA_2': 1052672, 'EffectSpellClassMaskA_3': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_meditation_12839 = spell(
    id=12839,
    name='Arcane Meditation',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=192),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=216),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=134),
    ],
    spell_icon_id=2894,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): repoints stock Arcane Focus\'s slot (id 76) to (0,1). "Increases spell, ranged and melee haste by 2/4/6%. Allows 25% of your mana regeneration to continue while casting." effect1 SPELL_AURA_MOD_MELEE_RANGED_HASTE (192), effect2 SPELL_AURA_HASTE_SPELLS (216), effect3 SPELL_AURA_MOD_MANA_REGEN_INTERRUPT (134, flat 25% every rank - the real stock mechanism, capped/applied directly by Player::UpdateManaRegen()). raw_overrides fully replaced (not merged) - the earlier version left stale classmask fields from Arcane Focus; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell, ranged and melee haste by 4%. Allows 25% of your mana regeneration to continue while casting.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_meditation_12840 = spell(
    id=12840,
    name='Arcane Meditation',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=192),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=216),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=134),
    ],
    spell_icon_id=2894,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): repoints stock Arcane Focus\'s slot (id 76) to (0,1). "Increases spell, ranged and melee haste by 2/4/6%. Allows 25% of your mana regeneration to continue while casting." effect1 SPELL_AURA_MOD_MELEE_RANGED_HASTE (192), effect2 SPELL_AURA_HASTE_SPELLS (216), effect3 SPELL_AURA_MOD_MANA_REGEN_INTERRUPT (134, flat 25% every rank - the real stock mechanism, capped/applied directly by Player::UpdateManaRegen()). raw_overrides fully replaced (not merged) - the earlier version left stale classmask fields from Arcane Focus; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell, ranged and melee haste by 6%. Allows 25% of your mana regeneration to continue while casting.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

ignite_12846 = spell(
    id=12846,
    name='Ignite',
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
    spell_icon_id=937,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical strikes from Fire damage spells cause the target to burn for an additional 24% of your spell's damage over $12654d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

ignite_12847 = spell(
    id=12847,
    name='Ignite',
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
    spell_icon_id=937,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical strikes from Fire damage spells cause the target to burn for an additional 32% of your spell's damage over $12654d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

ignite_12848 = spell(
    id=12848,
    name='Ignite',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=937,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical strikes from Fire damage spells cause the target to burn for an additional 40% of your spell's damage over $12654d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_scorch_12872 = spell(
    id=12872,
    name='Improved Scorch',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=22959),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=816,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to critically hit with Scorch, Fireball and Frostfire Bolt by an additional $s2% and your damaging Scorch spells have a $h% chance to cause your target to be vulnerable to spell damage, increasing spell critical strike chance against that target by $22959s1% and lasts $22959d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskB_1': 17, 'EffectSpellClassMaskB_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50},
)

improved_scorch_12873 = spell(
    id=12873,
    name='Improved Scorch',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=22959),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=816,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to critically hit with Scorch, Fireball and Frostfire Bolt by an additional $s2% and your damaging Scorch spells have a $h% chance to cause your target to be vulnerable to spell damage, increasing spell critical strike chance against that target by $22959s1% and lasts $22959d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskB_1': 17, 'EffectSpellClassMaskB_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50},
)

piercing_ice_12952 = spell(
    id=12952,
    name='Piercing Ice',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=176,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Frost spells by $s1%.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 131808, 'EffectSpellClassMaskB_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

piercing_ice_12953 = spell(
    id=12953,
    name='Piercing Ice',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=176,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Frost spells by $s1%.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 131808, 'EffectSpellClassMaskB_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

shatter_12982 = spell(
    id=12982,
    name='Shatter',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=112, misc_value=910),
    ],
    spell_icon_id=976,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of all your spells against frozen targets by 34%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 552211063, 'EffectSpellClassMaskA_2': 1151048, 'EffectSpellClassMaskA_3': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

shatter_12983 = spell(
    id=12983,
    name='Shatter',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=112, misc_value=911),
    ],
    spell_icon_id=976,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of all your spells against frozen targets by 50%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 552211063, 'EffectSpellClassMaskA_2': 1151048, 'EffectSpellClassMaskA_3': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

molten_shields_13043 = spell(
    id=13043,
    name='Molten Shields',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=16,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes your Fire Ward and Frost Ward spells to have a $s1% chance to reflect the warded spell while active. In addition, your Molten Armor has a 100% chance to affect ranged and spell attacks.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 264, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

ice_shards_15047 = spell(
    id=15047,
    name='Ice Shards',
    school=School.FROST,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1236,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Frost spells by $s1%.  Increases damage against frozen targets by 6%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131808, 'EffectSpellClassMaskA_2': 1052672, 'EffectSpellClassMaskA_3': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_instability_15058 = spell(
    id=15058,
    name='Arcane Instability',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=79, misc_value=64),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=71, misc_value=127),
    ],
    spell_icon_id=87,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your spells and your critical strike chance by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 14947063, 'EffectSpellClassMaskB_1': 4194437, 'EffectSpellClassMaskC_1': 14684919, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

arcane_instability_15059 = spell(
    id=15059,
    name='Arcane Instability',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=64),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=71, misc_value=127),
    ],
    spell_icon_id=87,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your spells and your critical strike chance by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 14947063, 'EffectSpellClassMaskB_1': 4194437, 'EffectSpellClassMaskC_1': 14684919, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

arcane_instability_15060 = spell(
    id=15060,
    name='Arcane Instability',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=64),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=71, misc_value=127),
    ],
    spell_icon_id=87,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your spells and your critical strike chance by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 14947063, 'EffectSpellClassMaskB_1': 4194437, 'EffectSpellClassMaskC_1': 14684919, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

arctic_reach_16757 = spell(
    id=16757,
    name='Arctic Reach',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=6),
    ],
    spell_icon_id=154,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the range of your Frostbolt, Ice Lance, Deep Freeze and Blizzard spells by $s1 yards and the radius of your Frost Nova and Cone of Cold spells by $s2%. |cFF9D9D9DAt max rank, your Frost damage is increased by up to 10% based on the target's distance, reaching full effect at 30 yards or more.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131232, 'EffectSpellClassMaskA_2': 1048576, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

arctic_reach_16758 = spell(
    id=16758,
    name='Arctic Reach',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=154,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the range of your Frostbolt, Ice Lance, Deep Freeze and Blizzard spells by $s1 yards and the radius of your Frost Nova and Cone of Cold spells by $s2%.  Your Frost damage is increased by up to 10% based on the target's distance, reaching full effect at 30 yards or more.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131232, 'EffectSpellClassMaskA_2': 1048576, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

arcane_stability_16769 = spell(
    id=16769,
    name='Arcane Stability',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=79, implicit_target_a=1, apply_aura=108, misc_value=9),
    ],
    spell_icon_id=225,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the pushback suffered from damaging attacks while casting Arcane Missiles and Arcane Blast by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536872960, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_stability_16770 = spell(
    id=16770,
    name='Arcane Stability',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=9),
    ],
    spell_icon_id=225,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the pushback suffered from damaging attacks while casting Arcane Missiles and Arcane Blast by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536872960, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

incineration_18459 = spell(
    id=18459,
    name='Incineration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=678,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Fire Blast, Scorch, Arcane Blast and Cone of Cold spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536871442, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

incineration_18460 = spell(
    id=18460,
    name='Incineration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=678,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Fire Blast, Scorch, Arcane Blast and Cone of Cold spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536871442, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

frost_warding_28332 = spell(
    id=28332,
    name='Frost Warding',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.DUMMY, base_points=29),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=501,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the armor and resistances given by your Frost Armor and Ice Armor spells by $s1%.  In addition, gives your Frost Ward and Fire Ward a $s2% chance to negate the warded damage spell and restore mana equal to the damage caused.  While Frost Armor or Ice Armor is active, physical damage taken is reduced by an additional 20%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

winter_s_chill_28592 = spell(
    id=28592,
    name="Winter's Chill",
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12579),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=187,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your chance to critically hit with Frostbolt by an additional $s2% and gives your Frost damage spells a $h% chance to apply the Winter's Chill effect, which increases the chance spells will critically hit the target by $12579s1% for $12579d.  Stacks up to $12579u times.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

winter_s_chill_28593 = spell(
    id=28593,
    name="Winter's Chill",
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12579),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=187,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your chance to critically hit with Frostbolt by an additional $s2% and gives your Frost damage spells a $h% chance to apply the Winter's Chill effect, which increases the chance spells will critically hit the target by $12579s1% for $12579d.  Stacks up to $12579u times.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

master_of_elements_29074 = spell(
    id=29074,
    name='Master of Elements',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1920,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell criticals will refund $s1% of their base mana cost.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

master_of_elements_29075 = spell(
    id=29075,
    name='Master of Elements',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1920,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell criticals will refund $s1% of their base mana cost.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

master_of_elements_29076 = spell(
    id=29076,
    name='Master of Elements',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1920,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell criticals will refund $s1% of their base mana cost.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

precision_29438 = spell(
    id=29438,
    name='Precision',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=71, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=72, misc_value=126),
    ],
    spell_icon_id=172,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with Frost spells by $s1% and reduces the mana cost of your spells by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_2': 1, 'EffectSpellClassMaskA_2': 69640, 'EffectSpellClassMaskB_2': 1, 'EffectSpellClassMaskC_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

precision_29439 = spell(
    id=29439,
    name='Precision',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=71, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=72, misc_value=126),
    ],
    spell_icon_id=172,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with Frost spells by $s1% and reduces the mana cost of your spells by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_2': 1, 'EffectSpellClassMaskA_2': 69640, 'EffectSpellClassMaskC_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

precision_29440 = spell(
    id=29440,
    name='Precision',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=71, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=72, misc_value=126),
    ],
    spell_icon_id=172,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with Frost spells by $s1% and reduces the mana cost of your spells by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_2': 1, 'EffectSpellClassMaskA_2': 69640, 'EffectSpellClassMaskC_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

magic_absorption_29441 = spell(
    id=29441,
    name='Magic Absorption',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=79, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=459,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): repoints stock Magic Absorption\'s slot (id 1650) to (1,0) - unrelated coordinate shuffle; the real Magic Absorption (resist-per-level + mana-on-full-resist) doesn\'t match this design\'s wording, so content is fully replaced. "Increases magic damage done by 1/2/3%. Reduces magic damage taken by 1/2/3%." effect1 SPELL_AURA_MOD_DAMAGE_PERCENT_DONE (79), effect2 SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN (87), both misc_value 126 (all magic schools). "Increases mana from Mana Gems by 15/30/45%" NOT built this phase - Mana Gems are items (SPELLFAMILY_GENERIC); a classmask-scoped SpellMod only matches within the caster\'s own spell family, so this needs a different mechanism - deferred to Phase 3. raw_overrides/effects fully replaced (not merged) - the earlier version left a stale points_per_level 0.5 and other fields from the real Magic Absorption data; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases magic damage done by 1% and reduces magic damage taken by 1%. Increases the mana you gain from Mana Gems by 15%.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_3': 16},
)

magic_absorption_29444 = spell(
    id=29444,
    name='Magic Absorption',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=459,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): repoints stock Magic Absorption\'s slot (id 1650) to (1,0) - unrelated coordinate shuffle; the real Magic Absorption (resist-per-level + mana-on-full-resist) doesn\'t match this design\'s wording, so content is fully replaced. "Increases magic damage done by 1/2/3%. Reduces magic damage taken by 1/2/3%." effect1 SPELL_AURA_MOD_DAMAGE_PERCENT_DONE (79), effect2 SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN (87), both misc_value 126 (all magic schools). "Increases mana from Mana Gems by 15/30/45%" NOT built this phase - Mana Gems are items (SPELLFAMILY_GENERIC); a classmask-scoped SpellMod only matches within the caster\'s own spell family, so this needs a different mechanism - deferred to Phase 3. raw_overrides/effects fully replaced (not merged) - the earlier version left a stale points_per_level 0.5 and other fields from the real Magic Absorption data; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases magic damage done by 2% and reduces magic damage taken by 2%. Increases the mana you gain from Mana Gems by 30%.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_3': 16},
)

improved_blink_31569 = spell(
    id=31569,
    name='Improved Blink',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-2501, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=1499,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of Blink by $47000s1 sec and its mana cost by $s1%. \n\n|cFF9D9D9DCapstone Bonus: After casting Blink all damage taken is reduced by 20% for 3 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskB_1': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_blink_31570 = spell(
    id=31570,
    name='Improved Blink',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-5001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1499,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of Blink by $47000s1 sec and its mana cost by $s1%. \n\nCapstone Bonus: After casting Blink all damage taken is reduced by 20% for 3 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskB_1': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_potency_31571 = spell(
    id=31571,
    name='Arcane Potency',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
    ],
    spell_icon_id=2120,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your next damaging spell by $s1% after gaining Clearcasting or Presence of Mind.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 34, 'EffectSpellClassMaskB_1': 2099200, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_potency_31572 = spell(
    id=31572,
    name='Arcane Potency',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
    ],
    spell_icon_id=2120,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your next damaging spell by $s1% after gaining Clearcasting or Presence of Mind.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 34, 'EffectSpellClassMaskB_1': 2099200, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

prismatic_cloak_31574 = spell(
    id=31574,
    name='Prismatic Cloak',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-1501, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=2126,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1% and reduces the fade time of your Invisibility spell by ${$m2/-1000} sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

prismatic_cloak_31575 = spell(
    id=31575,
    name='Prismatic Cloak',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-3001, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=2126,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1% and reduces the fade time of your Invisibility spell by ${$m2/-1000} sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_empowerment_31579 = spell(
    id=31579,
    name='Arcane Empowerment',
    school=School.NORMAL,
    attributes=80,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108),
        Effect(type=65, implicit_target_a=1, apply_aura=79, misc_value=127, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=225,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases all damage by $s2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Arcane Blast and Arcane Barrage spells by $s1% and the damage of your Arcane Missiles by $s3%. In addition, increases the damage of all party and raid members within 100 yds by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536870912, 'EffectSpellClassMaskA_2': 32768, 'EffectSpellClassMaskC_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_empowerment_31582 = spell(
    id=31582,
    name='Arcane Empowerment',
    school=School.NORMAL,
    attributes=80,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
        Effect(type=65, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=127, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=225,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases all damage by $s2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Arcane Blast and Arcane Barrage spells by $s1% and the damage of your Arcane Missiles by $s3%. In addition, increases the damage of all party and raid members within 100 yds by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536870912, 'EffectSpellClassMaskA_2': 32768, 'EffectSpellClassMaskC_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_empowerment_31583 = spell(
    id=31583,
    name='Arcane Empowerment',
    school=School.NORMAL,
    attributes=80,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108),
        Effect(type=65, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=127, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=225,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases all damage by $s2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Arcane Blast and Arcane Barrage spells by $s1% and the damage of your Arcane Missiles by $s3%. In addition, increases the damage of all party and raid members within 100 yds by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536870912, 'EffectSpellClassMaskA_2': 32768, 'EffectSpellClassMaskC_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

mind_mastery_31584 = spell(
    id=31584,
    name='Mind Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=72, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=1999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=2121,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power by $s1% of your total Intellect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_1': 4043439104, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskC_3': 1},
)

mind_mastery_31585 = spell(
    id=31585,
    name='Mind Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=72, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=3999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=2121,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power by $s1% of your total Intellect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_1': 4043439104, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskC_3': 1},
)

mind_mastery_31586 = spell(
    id=31586,
    name='Mind Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=72, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=5999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=2121,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power by $s1% of your total Intellect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_1': 4043439104, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskC_3': 1},
)

mind_mastery_31587 = spell(
    id=31587,
    name='Mind Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=174, misc_value=126),
    ],
    spell_icon_id=2121,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power by $s1% of your total Intellect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_1': 4043439104, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

mind_mastery_31588 = spell(
    id=31588,
    name='Mind Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=174, misc_value=126),
    ],
    spell_icon_id=2121,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power by $s1% of your total Intellect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_1': 4043439104, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

playing_with_fire_31638 = spell(
    id=31638,
    name='Playing with Fire',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=79, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=2130,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all spell damage caused by $s1% and all spell damage taken by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

playing_with_fire_31639 = spell(
    id=31639,
    name='Playing with Fire',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=2130,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all spell damage caused by $s1% and all spell damage taken by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

playing_with_fire_31640 = spell(
    id=31640,
    name='Playing with Fire',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=2130,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all spell damage caused by $s1% and all spell damage taken by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

blazing_speed_31641 = spell(
    id=31641,
    name='Blazing Speed',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18350),
    ],
    spell_icon_id=2127,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a $h% chance when hit by a melee or ranged attack to increase your movement speed by $31643s1% and dispel all movement impairing effects.  This effect lasts $31643d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 5, 'ProcTypeMask': 680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

blazing_speed_31642 = spell(
    id=31642,
    name='Blazing Speed',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18350),
    ],
    spell_icon_id=2127,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a $h% chance when hit by a melee or ranged attack to increase your movement speed by $31643s1% and dispel all movement impairing effects.  This effect lasts $31643d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

empowered_fire_31656 = spell(
    id=31656,
    name='Empowered Fire',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=185,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Fireball, Frostfire Bolt and Pyroblast spells by an amount equal to $s1% of your spell power.  In addition, each time your Ignite talent causes damage, you have a $h% chance to regain $67545s1% of your base mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194305, 'EffectSpellClassMaskA_2': 4096, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

empowered_fire_31657 = spell(
    id=31657,
    name='Empowered Fire',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=185,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Fireball, Frostfire Bolt and Pyroblast spells by an amount equal to $s1% of your spell power.  In addition, each time your Ignite talent causes damage, you have a $h% chance to regain $67545s1% of your base mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194305, 'EffectSpellClassMaskA_2': 4096, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 67, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

empowered_fire_31658 = spell(
    id=31658,
    name='Empowered Fire',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=185,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Fireball, Frostfire Bolt and Pyroblast spells by an amount equal to $s1% of your spell power.  In addition, each time your Ignite talent causes damage, you have a $h% chance to regain $67545s1% of your base mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194305, 'EffectSpellClassMaskA_2': 4096, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

frozen_core_31667 = spell(
    id=31667,
    name='Frozen Core',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200016),
    ],
    spell_icon_id=2132,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 5, Frozen Core). effect1 (magic dmg taken -2/4/6%) needed zero changes -- pulled data already matched spec exactly. effect2 (new, all 3 ranks): native SPELL_AURA_PROC_TRIGGER_SPELL, \'taking magic damage grants Frozen Core, +2/4/6% Frost damage for 8 sec\' -- pure data, one small dedicated buff spell per rank (200016/17/18) since the % scales by rank and each rank only ever triggers its own. ProcTypeMask = PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG | PROC_FLAG_TAKEN_PERIODIC (131072|524288) so it reacts to any class\'s direct or DoT magic damage, not just Mage-family sources. Playtest bugfix (2026-08-27/28, user call, "Frozen Core does nothing at all"): this spell has no explicit spell_proc row, so SpellMgr::LoadSpellProcs\'s fallback generator builds one from the DBC data itself -- and that generator ORs together the SpellClassMask of *every* trigger-aura effect on the entry (not just the proc-relevant ones) into a single spell-wide SpellFamilyMask, via SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN (effect1\'s aura type) itself being in SpellMgr\'s isTriggerAura[] table. Effect1\'s EffectSpellClassMaskA_1/B_1 (160/576) were leftover cruft from the pre-rework spell this ID used to be (\\"pulled from existing data\\" above) -- harmless for effect1 itself (a plain percent-taken modifier, not proc-scoped), but they got sucked into the generated procEntry\'s SpellFamilyMask and silently required every trigger spell family-mask-affect *that specific leftover mask*, which nothing (not a mob\'s fireball, not even the mage\'s own Ice Lance) ever matches. Confirmed live via temporary LOG_ERROR tracing in Aura::GetProcEffectMask/CanSpellTriggerProcOnEvent (SpellAuras.cpp/SpellMgr.cpp) -- procEntry.SpellFamilyName resolved to 3 (Mage) and SpellFamilyMask to the leftover value, failing IsAffected() for every real event. Removed EffectSpellClassMaskA_1/B_1 entirely (all 3 ranks) so the fallback procEntry\'s SpellFamilyMask stays 0/unrestricted, matching the documented intent.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the damage taken from all spells by $s1%. |cFF9D9D9DAt max rank, your Ice Lance critical strikes against frozen targets pierce to the target's core, dealing Frost damage over 8 sec. Does not stack, and refreshes on reapplication.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'ProcTypeMask': 655360},
)

frozen_core_31668 = spell(
    id=31668,
    name='Frozen Core',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200017),
    ],
    spell_icon_id=2132,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 5, Frozen Core). effect1 (magic dmg taken -2/4/6%) needed zero changes -- pulled data already matched spec exactly. effect2 (new, all 3 ranks): native SPELL_AURA_PROC_TRIGGER_SPELL, \'taking magic damage grants Frozen Core, +2/4/6% Frost damage for 8 sec\' -- pure data, one small dedicated buff spell per rank (200016/17/18) since the % scales by rank and each rank only ever triggers its own. ProcTypeMask = PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG | PROC_FLAG_TAKEN_PERIODIC (131072|524288) so it reacts to any class\'s direct or DoT magic damage, not just Mage-family sources. Playtest bugfix (2026-08-27/28, user call, "Frozen Core does nothing at all"): this spell has no explicit spell_proc row, so SpellMgr::LoadSpellProcs\'s fallback generator builds one from the DBC data itself -- and that generator ORs together the SpellClassMask of *every* trigger-aura effect on the entry (not just the proc-relevant ones) into a single spell-wide SpellFamilyMask, via SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN (effect1\'s aura type) itself being in SpellMgr\'s isTriggerAura[] table. Effect1\'s EffectSpellClassMaskA_1/B_1 (160/576) were leftover cruft from the pre-rework spell this ID used to be (\\"pulled from existing data\\" above) -- harmless for effect1 itself (a plain percent-taken modifier, not proc-scoped), but they got sucked into the generated procEntry\'s SpellFamilyMask and silently required every trigger spell family-mask-affect *that specific leftover mask*, which nothing (not a mob\'s fireball, not even the mage\'s own Ice Lance) ever matches. Confirmed live via temporary LOG_ERROR tracing in Aura::GetProcEffectMask/CanSpellTriggerProcOnEvent (SpellAuras.cpp/SpellMgr.cpp) -- procEntry.SpellFamilyName resolved to 3 (Mage) and SpellFamilyMask to the leftover value, failing IsAffected() for every real event. Removed EffectSpellClassMaskA_1/B_1 entirely (all 3 ranks) so the fallback procEntry\'s SpellFamilyMask stays 0/unrestricted, matching the documented intent.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the damage taken from all spells by $s1%. |cFF9D9D9DAt max rank, your Ice Lance critical strikes against frozen targets pierce to the target's core, dealing Frost damage over 8 sec. Does not stack, and refreshes on reapplication.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'ProcTypeMask': 655360},
)

frozen_core_31669 = spell(
    id=31669,
    name='Frozen Core',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200018),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200019),
    ],
    spell_icon_id=2132,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 5, Frozen Core). effect1 (magic dmg taken -2/4/6%) needed zero changes -- pulled data already matched spec exactly. effect2 (new, all 3 ranks): native SPELL_AURA_PROC_TRIGGER_SPELL, \'taking magic damage grants Frozen Core, +2/4/6% Frost damage for 8 sec\' -- pure data, one small dedicated buff spell per rank (200016/17/18) since the % scales by rank and each rank only ever triggers its own. ProcTypeMask = PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG | PROC_FLAG_TAKEN_PERIODIC (131072|524288) so it reacts to any class\'s direct or DoT magic damage, not just Mage-family sources. Playtest bugfix (2026-08-27/28, user call, "Frozen Core does nothing at all"): this spell has no explicit spell_proc row, so SpellMgr::LoadSpellProcs\'s fallback generator builds one from the DBC data itself -- and that generator ORs together the SpellClassMask of *every* trigger-aura effect on the entry (not just the proc-relevant ones) into a single spell-wide SpellFamilyMask, via SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN (effect1\'s aura type) itself being in SpellMgr\'s isTriggerAura[] table. Effect1\'s EffectSpellClassMaskA_1/B_1 (160/576) were leftover cruft from the pre-rework spell this ID used to be (\\"pulled from existing data\\" above) -- harmless for effect1 itself (a plain percent-taken modifier, not proc-scoped), but they got sucked into the generated procEntry\'s SpellFamilyMask and silently required every trigger spell family-mask-affect *that specific leftover mask*, which nothing (not a mob\'s fireball, not even the mage\'s own Ice Lance) ever matches. Confirmed live via temporary LOG_ERROR tracing in Aura::GetProcEffectMask/CanSpellTriggerProcOnEvent (SpellAuras.cpp/SpellMgr.cpp) -- procEntry.SpellFamilyName resolved to 3 (Mage) and SpellFamilyMask to the leftover value, failing IsAffected() for every real event. Removed EffectSpellClassMaskA_1/B_1 entirely (all 3 ranks) so the fallback procEntry\'s SpellFamilyMask stays 0/unrestricted, matching the documented intent. effect3 (rank 3 only, capstone): \'Ice Lance crit vs frozen -> DoT (200019), no stack, refresh on reapply.\' Native aura reapplication already gives \'does not stack, refreshes\' for free (same-spell-ID single-target apply). Real gating (Ice Lance only + must crit + target frozen) lives entirely in spell_mage_frozen_core (spell_mage.cpp), not in the DBC row: effect2 and effect3 share this spell\'s one spell-wide ProcFlags/SchoolMask/SpellFamilyMask (confirmed by reading Aura::GetProcEffectMask/CanSpellTriggerProcOnEvent), so a script has to discriminate \'taken\' (effect2) from \'done+crit+frozen\' (effect3) per event rather than two independently-scoped native effects.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the damage taken from all spells by $s1%.  Your Ice Lance critical strikes against frozen targets pierce to the target's core, dealing Frost damage over 8 sec. Does not stack, and refreshes on reapplication.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'ProcTypeMask': 720896},
)

ice_floes_31670 = spell(
    id=31670,
    name='Ice Floes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-12, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=2133,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Frost Nova, Cone of Cold, Ice Block and Icy Veins spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 576, 'EffectSpellClassMaskA_2': 16512, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

ice_floes_31672 = spell(
    id=31672,
    name='Ice Floes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-23, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=2133,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Frost Nova, Cone of Cold, Ice Block and Icy Veins spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 576, 'EffectSpellClassMaskA_2': 16512, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

arctic_winds_31674 = spell(
    id=31674,
    name='Arctic Winds',
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
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=79, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=2131,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% and Frost damage you deal by $s3%. |cFF9D9D9DAt max rank, your Glacial Spike shatters on impact, striking up to 5 additional enemies within 8 yards.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

arctic_winds_31675 = spell(
    id=31675,
    name='Arctic Winds',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=2131,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% and Frost damage you deal by $s3%. |cFF9D9D9DAt max rank, your Glacial Spike shatters on impact, striking up to 5 additional enemies within 8 yards.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

arctic_winds_31676 = spell(
    id=31676,
    name='Arctic Winds',
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
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2131,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% and Frost damage you deal by $s3%.  Your Glacial Spike shatters on impact, striking up to 5 additional enemies within 8 yards.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

molten_fury_31679 = spell(
    id=31679,
    name='Molten Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=112, misc_value=4919),
    ],
    spell_icon_id=2129,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases damage of all spells against targets with less than 35% health by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 102472, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

molten_fury_31680 = spell(
    id=31680,
    name='Molten Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=112, misc_value=4920),
    ],
    spell_icon_id=2129,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases damage of all spells against targets with less than 35% health by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 102472, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

empowered_frostbolt_31682 = spell(
    id=31682,
    name='Empowered Frostbolt',
    school=School.FROST,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200023),
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=188,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 8, Empowering Frostbolt). effect2 (cast time -0.1/0.2 sec, SPELLMOD_CASTING_TIME) needed zero changes -- matched spec exactly already. effect1 was the OLD \'Empowered Frostbolt\' mechanic (a direct SPELLMOD_BONUS_MULTIPLIER damage bonus on Frostbolt itself) -- a different shape than the new spec\'s post-cast buff, replaced outright: native PROC_TRIGGER_SPELL (100%, on casting Frostbolt) to a new buff (200023/200024): crit-damage-bonus +7/14% (ADD_PCT_MODIFIER, SPELLMOD_CRIT_DAMAGE_BONUS, empty classmask = \'of your spells\' broadly, same convention as Winter\'s Chill\'s own crit% effect) + Frost damage +3/5% (MOD_DAMAGE_PERCENT_DONE, Frost school mask), 8 sec, pure data. Playtest bugfix (2026-08-27, second recurrence found via an automated sweep of every spell/talent CSV, built through lib/build.py and checked for a SPELLMOD-type effect whose own classmask came out all-zero): the SPELLMOD_CASTING_TIME modifier lives on effect index 1 (the second effect, letter B), but its Frostbolt-only classmask (32) was stored under EffectSpellClassMaskA_1 - effect index 0 (letter A, the PROC_TRIGGER_SPELL effect, which doesn\'t need one at all) - leaving effect 1\'s real classmask all-zero, i.e. "matches every mage spell," same root cause as Permafrost/Chilled to the Bone (frost_mage_rework.sql (merged Frost Mage rework migration; originally rev_1787820084006262155.sql) / docs/dbc-build-pipeline.md "Bug 3"). Moved to EffectSpellClassMaskB_1, which is what the engine actually reads for effect index 1.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Frostbolt spell by an amount equal to $s1% of your spell power and reduces the cast time by ${$m2/-1000}.1 sec.', 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 65536, 'EffectSpellClassMaskB_1': 32},
)

empowered_frostbolt_31683 = spell(
    id=31683,
    name='Empowered Frostbolt',
    school=School.FROST,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200024),
        Effect(type=EffectType.APPLY_AURA, base_points=-201, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=188,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 8, Empowering Frostbolt). effect2 (cast time -0.1/0.2 sec, SPELLMOD_CASTING_TIME) needed zero changes -- matched spec exactly already. effect1 was the OLD \'Empowered Frostbolt\' mechanic (a direct SPELLMOD_BONUS_MULTIPLIER damage bonus on Frostbolt itself) -- a different shape than the new spec\'s post-cast buff, replaced outright: native PROC_TRIGGER_SPELL (100%, on casting Frostbolt) to a new buff (200023/200024): crit-damage-bonus +7/14% (ADD_PCT_MODIFIER, SPELLMOD_CRIT_DAMAGE_BONUS, empty classmask = \'of your spells\' broadly, same convention as Winter\'s Chill\'s own crit% effect) + Frost damage +3/5% (MOD_DAMAGE_PERCENT_DONE, Frost school mask), 8 sec, pure data. Playtest bugfix (2026-08-27, second recurrence found via an automated sweep of every spell/talent CSV, built through lib/build.py and checked for a SPELLMOD-type effect whose own classmask came out all-zero): the SPELLMOD_CASTING_TIME modifier lives on effect index 1 (the second effect, letter B), but its Frostbolt-only classmask (32) was stored under EffectSpellClassMaskA_1 - effect index 0 (letter A, the PROC_TRIGGER_SPELL effect, which doesn\'t need one at all) - leaving effect 1\'s real classmask all-zero, i.e. "matches every mage spell," same root cause as Permafrost/Chilled to the Bone (frost_mage_rework.sql (merged Frost Mage rework migration; originally rev_1787820084006262155.sql) / docs/dbc-build-pipeline.md "Bug 3"). Moved to EffectSpellClassMaskB_1, which is what the engine actually reads for effect index 1.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Frostbolt spell by an amount equal to $s1% of your spell power and reduces the cast time by ${$m2/-1000}.1 sec.', 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 65536, 'EffectSpellClassMaskB_1': 32},
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

pyromaniac_34293 = spell(
    id=34293,
    name='Pyromaniac',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=71, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=16, implicit_target_a=1, apply_aura=134, misc_value=4),
    ],
    spell_icon_id=2128,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases chance to critically hit by $s1% and allows $s2% of your mana regeneration to continue while casting.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12582935, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

pyromaniac_34295 = spell(
    id=34295,
    name='Pyromaniac',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=71, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=134, misc_value=4),
    ],
    spell_icon_id=2128,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases chance to critically hit by $s1% and allows $s2% of your mana regeneration to continue while casting.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12582935, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

pyromaniac_34296 = spell(
    id=34296,
    name='Pyromaniac',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=71, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=134, misc_value=4),
    ],
    spell_icon_id=2128,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases chance to critically hit by $s1% and allows $s2% of your mana regeneration to continue while casting.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12582935, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

backlash_34935 = spell(
    id=34935,
    name='Backlash',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=34936),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=57),
    ],
    spell_icon_id=2130,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with spells by an additional $s2% and gives you a $h% chance when hit by a physical attack to reduce the cast time of your next Shadow Bolt or Incinerate spell by $34936s1%.  This effect lasts $34936d and will not occur more than once every 8 seconds.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 8, 'ProcTypeMask': 680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

backlash_34938 = spell(
    id=34938,
    name='Backlash',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=34936),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=57),
    ],
    spell_icon_id=2130,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with spells by an additional $s2% and gives you a $h% chance when hit by a physical attack to reduce the cast time of your next Shadow Bolt or Incinerate spell by $34936s1%.  This effect lasts $34936d and will not occur more than once every 8 seconds.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 16, 'ProcTypeMask': 680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

backlash_34939 = spell(
    id=34939,
    name='Backlash',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=34936),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=57),
    ],
    spell_icon_id=2130,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with spells by an additional $s2% and gives you a $h% chance when hit by a physical attack to reduce the cast time of your next Shadow Bolt or Incinerate spell by $34936s1%.  This effect lasts $34936d and will not occur more than once every 8 seconds.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 25, 'ProcTypeMask': 680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

spell_power_35578 = spell(
    id=35578,
    name='Spell Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=2281,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases critical strike damage bonus of all spells by $s1%. \n\n|cFF9D9D9DCapstone Bonus: Dealing direct critical damage with a spell while your mana is below 50% taps into raw power, restoring 1% of your total mana each second and increasing your magic damage by 10% and Arcane damage by another 5%. This effect lasts for 10 seconds and can only occur once every 30 seconds.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 102472, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

spell_power_35581 = spell(
    id=35581,
    name='Spell Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=74, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=2281,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases critical strike damage bonus of all spells by $s1%. \n\n|cFF9D9D9DCapstone Bonus: Dealing direct critical damage with a spell while your mana is below 50% taps into raw power, restoring 1% of your total mana each second and increasing your magic damage by 10% and Arcane damage by another 5%. This effect lasts for 10 seconds and can only occur once every 30 seconds.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 102472, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_flows_44378 = spell(
    id=44378,
    name='Arcane Flows',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=108, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-15001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2940,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Presence of Mind, Arcane Power and Invisibility spells by $s1% and the cooldown of your Evocation spell by $/1000;s2 sec. \n\n|cFF9D9D9DCapstone Bonus: Your Arcane Power increases your magic damage dealt by an additional 5%.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 4, 'EffectSpellClassMaskA_2': 786464, 'EffectSpellClassMaskB_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'EffectSpellClassMaskA_3': 2},
)

arcane_flows_44379 = spell(
    id=44379,
    name='Arcane Flows',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=108, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2940,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Presence of Mind, Arcane Power and Invisibility spells by $s1% and the cooldown of your Evocation spell by $/1000;s2 sec. \n\nCapstone Bonus: Your Arcane Power increases your magic damage dealt by an additional 5%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 4, 'EffectSpellClassMaskA_2': 786464, 'EffectSpellClassMaskB_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'EffectSpellClassMaskA_3': 2},
)

netherwind_presence_44400 = spell(
    id=44400,
    name='Netherwind Presence',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2943,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell haste by $s1%. \n\n|cFF9D9D9DCapstone Bonus: Casting Slow while Netherwind Presence is fully stacked increases your movement speed by 50% for 5 sec. This effect cannot occur more than once every 30 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'ProcTypeMask': 65536, 'ProcCharges': 0},
)

netherwind_presence_44402 = spell(
    id=44402,
    name='Netherwind Presence',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2943,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell haste by $s1%. \n\n|cFF9D9D9DCapstone Bonus: Casting Slow while Netherwind Presence is fully stacked increases your movement speed by 50% for 5 sec. This effect cannot occur more than once every 30 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'ProcTypeMask': 65536, 'ProcCharges': 0},
)

netherwind_presence_44403 = spell(
    id=44403,
    name='Netherwind Presence',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2943,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell haste by $s1%. \n\nCapstone Bonus: Casting Slow while Netherwind Presence is fully stacked increases your movement speed by 50% for 5 sec. This effect cannot occur more than once every 30 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'ProcTypeMask': 65536, 'ProcCharges': 0},
)

missile_barrage_44404 = spell(
    id=44404,
    name='Missile Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=44401),
    ],
    spell_icon_id=3261,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Arcane Blast a $h% chance, and your Arcane Barrage, Fireball, Frostbolt and Frostfire Bolt spells a ${$h/2}% chance to reduce the channeled duration of the next Arcane Missiles spell by $44401s1%, reduce the mana cost by $44401s3%, and missiles will fire every .5 secs.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 12, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3},
)

firestarter_44442 = spell(
    id=44442,
    name='Firestarter',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=6971, trigger_spell=54741),
    ],
    spell_icon_id=3262,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your damaging Blast Wave and Dragon's Breath spells have a $h% chance to make your next Flamestrike spell instant cast and cost no mana.  Lasts $54741d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8388612, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

firestarter_44443 = spell(
    id=44443,
    name='Firestarter',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=6970, trigger_spell=54741),
    ],
    spell_icon_id=3262,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your damaging Blast Wave and Dragon's Breath spells have a $h% chance to make your next Flamestrike spell instant cast and cost no mana.  Lasts $54741d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8388612, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

hot_streak_44445 = spell(
    id=44445,
    name='Hot Streak',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2999,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Any time you score 2 non-periodic spell criticals in a row using Fireball, Fire Blast, Scorch, Living Bomb, or Frostfire Bolt, you have a $m1% chance the next Pyroblast spell cast within $48108d will be instant cast.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 8, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

hot_streak_44446 = spell(
    id=44446,
    name='Hot Streak',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2999,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Any time you score 2 non-periodic spell criticals in a row using Fireball, Fire Blast, Scorch, Living Bomb, or Frostfire Bolt, you have a $m1% chance the next Pyroblast spell cast within $48108d will be instant cast.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 8, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

hot_streak_44448 = spell(
    id=44448,
    name='Hot Streak',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2999,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Any time you score 2 non-periodic spell criticals in a row using Fireball, Fire Blast, Scorch, Living Bomb, or Frostfire Bolt, you have a $m1% chance the next Pyroblast spell cast within $48108d will be instant cast.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 8, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

burnout_44449 = spell(
    id=44449,
    name='Burnout',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2998,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your spell critical damage bonus with all spells by $s1% but your non-periodic spell criticals cost an additional $s2% of the spell's cost.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 233544, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

burnout_44469 = spell(
    id=44469,
    name='Burnout',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2998,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your spell critical damage bonus with all spells by $s1% but your non-periodic spell criticals cost an additional $s2% of the spell's cost.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 233544, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

burnout_44470 = spell(
    id=44470,
    name='Burnout',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2998,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your spell critical damage bonus with all spells by $s1% but your non-periodic spell criticals cost an additional $s2% of the spell's cost.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 233544, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

burnout_44471 = spell(
    id=44471,
    name='Burnout',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2998,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your spell critical damage bonus with all spells by $s1% but your non-periodic spell criticals cost an additional $s2% of the spell's cost.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 233544, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

burnout_44472 = spell(
    id=44472,
    name='Burnout',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2998,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your spell critical damage bonus with all spells by $s1% but your non-periodic spell criticals cost an additional $s2% of the spell's cost.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 233544, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

fingers_of_frost_44543 = spell(
    id=44543,
    name='Fingers of Frost',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=44544),
    ],
    spell_icon_id=2947,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Chill effects a $s1% chance to grant you the Fingers of Frost effect, which treats your next $44544s1 spells cast as if the target were Frozen.  Lasts $44544d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

fingers_of_frost_44545 = spell(
    id=44545,
    name='Fingers of Frost',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=44544),
    ],
    spell_icon_id=2947,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Chill effects a $s1% chance to grant you the Fingers of Frost effect, which treats your next $44544s1 spells cast as if the target were Frozen.  Lasts $44544d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

brain_freeze_44546 = spell(
    id=44546,
    name='Brain Freeze',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=23, trigger_spell=57761),
    ],
    spell_icon_id=2938,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Frost damage spells with chilling effects have a $h% chance to cause your next Fireball or Frostfire Bolt spell to be instant cast and cost no mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskA_2': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 5, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

brain_freeze_44548 = spell(
    id=44548,
    name='Brain Freeze',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=23, trigger_spell=57761),
    ],
    spell_icon_id=2938,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Frost damage spells with chilling effects have a $h% chance to cause your next Fireball or Frostfire Bolt spell to be instant cast and cost no mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskA_2': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

brain_freeze_44549 = spell(
    id=44549,
    name='Brain Freeze',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=23, trigger_spell=57761),
    ],
    spell_icon_id=2938,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Frost damage spells with chilling effects have a $h% chance to cause your next Fireball or Frostfire Bolt spell to be instant cast and cost no mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskA_2': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 15, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

enduring_winter_44557 = spell(
    id=44557,
    name='Enduring Winter',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=8, trigger_spell=57669),
    ],
    spell_icon_id=2134,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 9, Enduring Winter). effect1's duration bonus (5/10/15s) already matched spec exactly but was completely unscoped in the pulled data (no EffectSpellClassMask at all on this effect) -- SpellInfo::IsAffected treats an all-zero classmask as matching every spell in the family, which would have extended the duration of every Mage aura-bearing spell, not just Summon Water Elemental. Scoped explicitly to word B = 2048, Summon Water Elemental's (31687) own identity flag. effect2 (Replenishment proc) needed zero changes -- matches spec exactly already, including the existing base spell_proc row's 6-sec ICE (confirmed pre-existing, not part of this migration).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Summon Water Elemental spell by $/1000;s1 sec and your Frostbolt spell has a $h% chance to grant up to 10 party or raid members mana regeneration equal to 1% of their maximum mana per 5 sec for $57669d.  This effect cannot occur more often than once every $m2 sec. |cFF9D9D9DAt max rank, while your Water Elemental is active, each Frostbolt you cast extends its duration by 2 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EffectSpellClassMaskB_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskB_1': 2048},
)

enduring_winter_44560 = spell(
    id=44560,
    name='Enduring Winter',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=8, trigger_spell=57669),
    ],
    spell_icon_id=2134,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 9, Enduring Winter). effect1's duration bonus (5/10/15s) already matched spec exactly but was completely unscoped in the pulled data (no EffectSpellClassMask at all on this effect) -- SpellInfo::IsAffected treats an all-zero classmask as matching every spell in the family, which would have extended the duration of every Mage aura-bearing spell, not just Summon Water Elemental. Scoped explicitly to word B = 2048, Summon Water Elemental's (31687) own identity flag. effect2 (Replenishment proc) needed zero changes -- matches spec exactly already, including the existing base spell_proc row's 6-sec ICE (confirmed pre-existing, not part of this migration).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Summon Water Elemental spell by $/1000;s1 sec and your Frostbolt spell has a $h% chance to grant up to 10 party or raid members mana regeneration equal to 1% of their maximum mana per 5 sec for $57669d.  This effect cannot occur more often than once every $m2 sec. |cFF9D9D9DAt max rank, while your Water Elemental is active, each Frostbolt you cast extends its duration by 2 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EffectSpellClassMaskB_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskB_1': 2048},
)

enduring_winter_44561 = spell(
    id=44561,
    name='Enduring Winter',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=8, trigger_spell=57669),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2134,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 9, Enduring Winter). effect1's duration bonus (5/10/15s) already matched spec exactly but was completely unscoped in the pulled data (no EffectSpellClassMask at all on this effect) -- SpellInfo::IsAffected treats an all-zero classmask as matching every spell in the family, which would have extended the duration of every Mage aura-bearing spell, not just Summon Water Elemental. Scoped explicitly to word B = 2048, Summon Water Elemental's (31687) own identity flag. effect2 (Replenishment proc) needed zero changes -- matches spec exactly already, including the existing base spell_proc row's 6-sec ICE (confirmed pre-existing, not part of this migration). effect3 (rank 3 only, capstone): new SPELL_AURA_DUMMY read by spell_mage_enduring_winter (OnEffectProc, spell_mage.cpp) -- extends the caster's active Water Elemental's despawn timer by 2 sec per qualifying Frostbolt cast (TempSummon::SetTimer; Pet inherits this directly through Guardian/Minion/TempSummon). No-ops if the pet is the permanent-glyph variant (no despawn timer to extend) or not summoned at all.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Summon Water Elemental spell by $/1000;s1 sec and your Frostbolt spell has a $h% chance to grant up to 10 party or raid members mana regeneration equal to 1% of their maximum mana per 5 sec for $57669d.  This effect cannot occur more often than once every $m2 sec.  While your Water Elemental is active, each Frostbolt you cast extends its duration by 2 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EffectSpellClassMaskB_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskB_1': 2048},
)

chilled_to_the_bone_44566 = spell(
    id=44566,
    name='Chilled to the Bone',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=107, misc_value=3),
    ],
    spell_icon_id=2965,
    notes='pulled from existing data EffectSpellClassMaskA_2/B_1 override on effect index 1 (SPELLMOD_EFFECT1, -4/-7/-10, classmask 544 = Frostbolt|Cone of Cold) added on top of the pulled data to scope the movement- speed modifier to just those two spells. Playtest bugfix (2026-08-27, user report - "Permafrost reduces the effects of everything by 10%, not just move speed" - same root cause hit Chilled to the Bone too): the classmask was stored under EffectSpellClassMaskA_2, which spell_dbc/DBCStructure.h actually reads as effect index 0\'s second word, not effect index 1\'s first word - leaving effect 1\'s real classmask all-zero, which SpellInfo::IsAffected treats as matching every spell in the family. Moved to EffectSpellClassMaskB_1 (effect index 1(=B)\'s word 1), which is what the engine actually reads. See data/sql/updates/pending_db_world/frost_mage_rework.sql (merged Frost Mage rework migration; originally rev_1787820084006262155.sql) for the original diagnosis.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% and reduces the movement speed of targets affected by your Frostbolt, Cone of Cold and Frozen Orb by an additional $s2%. |cFF9D9D9DAt max rank, your Frostbolt and Ice Lance casts versus monsters reduce the cooldown of your Frozen Orb by 1 sec, and your Blizzard reduces it by 1 sec every 3 ticks.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 544, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

chilled_to_the_bone_44567 = spell(
    id=44567,
    name='Chilled to the Bone',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-8, implicit_target_a=1, apply_aura=107, misc_value=3),
    ],
    spell_icon_id=2965,
    notes='pulled from existing data EffectSpellClassMaskA_2/B_1 override on effect index 1 (SPELLMOD_EFFECT1, -4/-7/-10, classmask 544 = Frostbolt|Cone of Cold) added on top of the pulled data to scope the movement- speed modifier to just those two spells. Playtest bugfix (2026-08-27, user report - "Permafrost reduces the effects of everything by 10%, not just move speed" - same root cause hit Chilled to the Bone too): the classmask was stored under EffectSpellClassMaskA_2, which spell_dbc/DBCStructure.h actually reads as effect index 0\'s second word, not effect index 1\'s first word - leaving effect 1\'s real classmask all-zero, which SpellInfo::IsAffected treats as matching every spell in the family. Moved to EffectSpellClassMaskB_1 (effect index 1(=B)\'s word 1), which is what the engine actually reads. See data/sql/updates/pending_db_world/frost_mage_rework.sql (merged Frost Mage rework migration; originally rev_1787820084006262155.sql) for the original diagnosis.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% and reduces the movement speed of targets affected by your Frostbolt, Cone of Cold and Frozen Orb by an additional $s2%. |cFF9D9D9DAt max rank, your Frostbolt and Ice Lance casts versus monsters reduce the cooldown of your Frozen Orb by 1 sec, and your Blizzard reduces it by 1 sec every 3 ticks.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 544, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

chilled_to_the_bone_44568 = spell(
    id=44568,
    name='Chilled to the Bone',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2965,
    notes='pulled from existing data EffectSpellClassMaskA_2/B_1 override on effect index 1 (SPELLMOD_EFFECT1, -4/-7/-10, classmask 544 = Frostbolt|Cone of Cold) added on top of the pulled data to scope the movement- speed modifier to just those two spells. Playtest bugfix (2026-08-27, user report - "Permafrost reduces the effects of everything by 10%, not just move speed" - same root cause hit Chilled to the Bone too): the classmask was stored under EffectSpellClassMaskA_2, which spell_dbc/DBCStructure.h actually reads as effect index 0\'s second word, not effect index 1\'s first word - leaving effect 1\'s real classmask all-zero, which SpellInfo::IsAffected treats as matching every spell in the family. Moved to EffectSpellClassMaskB_1 (effect index 1(=B)\'s word 1), which is what the engine actually reads. See data/sql/updates/pending_db_world/frost_mage_rework.sql (merged Frost Mage rework migration; originally rev_1787820084006262155.sql) for the original diagnosis.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% and reduces the movement speed of targets affected by your Frostbolt, Cone of Cold and Frozen Orb by an additional $s2%.  Your Frostbolt and Ice Lance casts versus monsters reduce the cooldown of your Frozen Orb by 1 sec, and your Blizzard reduces it by 1 sec every 3 ticks.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 544, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'AttributesEx3': 67633152, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

shattered_barrier_44745 = spell(
    id=44745,
    name='Shattered Barrier',
    school=School.FROST,
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
    spell_icon_id=2945,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 7, Shattered Barrier). Old pulled data ('% chance to freeze all enemies when Ice Barrier is destroyed') is a different mechanic than the new spec entirely, not a retune -- rebuilt from scratch. effect1: SPELL_AURA_DUMMY (2/4%), read live in Mage::ApplyDoneDamagePctMods (MageMechanics.cpp) gated on caster->HasAura(Ice Barrier) -- same 'live armor-state check, not a static aura' idiom as Frost Warding's capstone, chosen for the same reason (Ice Barrier gets applied/consumed independently of this talent, a cached mod would go stale).",
    raw_overrides={'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While your Ice Barrier is active, your damage is increased by $s1%. |cFF9D9D9DAt max rank, your Ice Barrier shatters when destroyed, slowing all enemies within 10 yards by 70% for 4 sec and granting you 8% haste for 8 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellPriority': 50},
)

owlkin_frenzy_48389 = spell(
    id=48389,
    name='Owlkin Frenzy',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=48391),
    ],
    spell_icon_id=2853,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Attacks done to you while in Moonkin form have a $h% chance to cause you to go into a Frenzy, increasing your damage by $48391s2%, cause you to be immune to pushback while casting Balance spells and restore $48391s3% base mana every $48391T3 sec. Lasts $48391d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 5, 'ProcTypeMask': 131752, 'RangeIndex': 1, 'ShapeshiftMask': 1073741824, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

owlkin_frenzy_48392 = spell(
    id=48392,
    name='Owlkin Frenzy',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=48391),
    ],
    spell_icon_id=2853,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Attacks done to you while in Moonkin form have a $h% chance to cause you to go into a Frenzy, increasing your damage by $48391s2%, cause you to be immune to pushback while casting Balance spells and restore $48391s3% base mana every $48391T3 sec. Lasts $48391d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 131752, 'RangeIndex': 1, 'ShapeshiftMask': 1073741824, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

owlkin_frenzy_48393 = spell(
    id=48393,
    name='Owlkin Frenzy',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=48391),
    ],
    spell_icon_id=2853,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Attacks done to you while in Moonkin form have a $h% chance to cause you to go into a Frenzy, increasing your damage by $48391s2%, cause you to be immune to pushback while casting Balance spells and restore $48391s3% base mana every $48391T3 sec. Lasts $48391d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 15, 'ProcTypeMask': 131752, 'RangeIndex': 1, 'ShapeshiftMask': 1073741824, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

prismatic_cloak_54354 = spell(
    id=54354,
    name='Prismatic Cloak',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-3001, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=2126,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1% and reduces the fade time of your Invisibility spell by ${$m2/-1000} sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 538972160, 'EffectSpellClassMaskB_2': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

missile_barrage_54486 = spell(
    id=54486,
    name='Missile Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=44401),
    ],
    spell_icon_id=3261,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Arcane Blast a $h% chance, and your Arcane Barrage, Fireball, Frostbolt and Frostfire Bolt spells a ${$h/2}% chance to reduce the channeled duration of the next Arcane Missiles spell by $44401s1%, reduce the mana cost by $44401s3%, and missiles will fire every .5 secs.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 23, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3},
)

missile_barrage_54488 = spell(
    id=54488,
    name='Missile Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=44401),
    ],
    spell_icon_id=3261,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Arcane Blast a $h% chance, and your Arcane Barrage, Fireball, Frostbolt and Frostfire Bolt spells a ${$h/2}% chance to reduce the channeled duration of the next Arcane Missiles spell by $44401s1%, reduce the mana cost by $44401s3%, and missiles will fire every .5 secs.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 35, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3},
)

missile_barrage_54489 = spell(
    id=54489,
    name='Missile Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=44401),
    ],
    spell_icon_id=3261,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Arcane Blast a $h% chance, and your Arcane Barrage, Fireball, Frostbolt and Frostfire Bolt spells a ${$h/2}% chance to reduce the channeled duration of the next Arcane Missiles spell by $44401s1%, reduce the mana cost by $44401s3%, and missiles will fire every .5 secs.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 32, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3},
)

missile_barrage_54490 = spell(
    id=54490,
    name='Missile Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=44401),
    ],
    spell_icon_id=3261,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Arcane Blast a $h% chance, and your Arcane Barrage, Fireball, Frostbolt and Frostfire Bolt spells a ${$h/2}% chance to reduce the channeled duration of the next Arcane Missiles spell by $44401s1%, reduce the mana cost by $44401s3%, and missiles will fire every .5 secs.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 40, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3},
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

incineration_54734 = spell(
    id=54734,
    name='Incineration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=678,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Fire Blast, Scorch, Arcane Blast and Cone of Cold spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536871442, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

burning_determination_54747 = spell(
    id=54747,
    name='Burning Determination',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=6971, trigger_spell=54748),
    ],
    spell_icon_id=2019,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx7': 1073741824, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When Interrupted or Silenced you have a $h% chance to become immune to the next Interrupt or Silence mechanic.  Lasts $54748d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8388612, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 139808, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

burning_determination_54749 = spell(
    id=54749,
    name='Burning Determination',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=6971, trigger_spell=54748),
    ],
    spell_icon_id=2019,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx7': 1073741824, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When Interrupted or Silenced you have a $h% chance to become immune to the next Interrupt or Silence mechanic.  Lasts $54748d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8388612, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 139808, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

shattered_barrier_54787 = spell(
    id=54787,
    name='Shattered Barrier',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2945,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 7, Shattered Barrier). Old pulled data ('% chance to freeze all enemies when Ice Barrier is destroyed') is a different mechanic than the new spec entirely, not a retune -- rebuilt from scratch. effect1: SPELL_AURA_DUMMY (2/4%), read live in Mage::ApplyDoneDamagePctMods (MageMechanics.cpp) gated on caster->HasAura(Ice Barrier) -- same 'live armor-state check, not a static aura' idiom as Frost Warding's capstone, chosen for the same reason (Ice Barrier gets applied/consumed independently of this talent, a cached mod would go stale). effect2 (rank 2 only): capstone marker (SPELL_AURA_DUMMY, EFFECT_1), read by spell_mage_ice_barrier_aura's new AfterEffectAbsorb hook -- when the shield's remaining amount hits 0 (destroyed by damage, not merely expiring), casts a new AoE slow (200021, 10 yd, -70% for 4 sec) and a new self-haste buff (200022, 8%, 8 sec, same aura type as Icy Veins' own cast-speed effect).",
    raw_overrides={'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While your Ice Barrier is active, your damage is increased by $s1%.  Your Ice Barrier shatters when destroyed, slowing all enemies within 10 yards by 70% for 4 sec and granting you 8% haste for 8 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellPriority': 50},
)

cold_as_ice_55091 = spell(
    id=55091,
    name='Cold as Ice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=3260,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Cold Snap, Ice Barrier and Summon Water Elemental spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2053, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

cold_as_ice_55092 = spell(
    id=55092,
    name='Cold as Ice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=3260,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Cold Snap, Ice Barrier and Summon Water Elemental spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2053, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

ice_floes_55094 = spell(
    id=55094,
    name='Ice Floes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-34, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=2133,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Frost Nova, Cone of Cold, Ice Block and Icy Veins spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 576, 'EffectSpellClassMaskA_2': 16512, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)

biting_cold_200010 = spell(
    id=200010,
    name='Biting Cold',
    school=School.FROST,
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
    spell_icon_id=189,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 2, Biting Cold): base effect only (the +2/4/6% Frost damage vs. chilled targets) - a SPELL_AURA_DUMMY read by a new SPELLFAMILY_MAGE case in Unit::SpellDamageBonusDone (Unit.cpp), matched by SpellIconID 189 (Spell_Frost_ChillingBolt) at EFFECT_0, same idiom as the Warlock/Hunter 'Torment the Weak' dummy lookup already in that function. 'Chilled' is read the same non-caster-scoped way Torment the Weak already does (Unit::HasAuraWithMechanic(MECHANIC_SNARE)) rather than a new caster-scoped check, for consistency with the existing idiom - see docs/frost-mage-talent-tree-handoff.md. The rank 3 capstone (bite a nearby chilled-enemy-triggered bounce) is a separate effect only on 200012, see that row's notes.",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Frost damage against targets affected by your chill effects is increased by 2%. |cFF9D9D9DAt max rank, dealing direct Frost damage to a chilled enemy has a 15% chance to bite into a nearby enemy within 8 yards, dealing Frost damage and chilling them. Cannot occur more than once every 6 sec.|r', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'SpellLevel': 1},
)

biting_cold_200011 = spell(
    id=200011,
    name='Biting Cold',
    school=School.FROST,
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
    spell_icon_id=189,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 2, Biting Cold): base effect only (the +2/4/6% Frost damage vs. chilled targets) - a SPELL_AURA_DUMMY read by a new SPELLFAMILY_MAGE case in Unit::SpellDamageBonusDone (Unit.cpp), matched by SpellIconID 189 (Spell_Frost_ChillingBolt) at EFFECT_0, same idiom as the Warlock/Hunter 'Torment the Weak' dummy lookup already in that function. 'Chilled' is read the same non-caster-scoped way Torment the Weak already does (Unit::HasAuraWithMechanic(MECHANIC_SNARE)) rather than a new caster-scoped check, for consistency with the existing idiom - see docs/frost-mage-talent-tree-handoff.md. The rank 3 capstone (bite a nearby chilled-enemy-triggered bounce) is a separate effect only on 200012, see that row's notes.",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Frost damage against targets affected by your chill effects is increased by 4%. |cFF9D9D9DAt max rank, dealing direct Frost damage to a chilled enemy has a 15% chance to bite into a nearby enemy within 8 yards, dealing Frost damage and chilling them. Cannot occur more than once every 6 sec.|r', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'SpellLevel': 1},
)

biting_cold_200012 = spell(
    id=200012,
    name='Biting Cold',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200013),
    ],
    spell_icon_id=189,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 2, Biting Cold): base effect only (the +2/4/6% Frost damage vs. chilled targets) - a SPELL_AURA_DUMMY read by a new SPELLFAMILY_MAGE case in Unit::SpellDamageBonusDone (Unit.cpp), matched by SpellIconID 189 (Spell_Frost_ChillingBolt) at EFFECT_0, same idiom as the Warlock/Hunter 'Torment the Weak' dummy lookup already in that function. 'Chilled' is read the same non-caster-scoped way Torment the Weak already does (Unit::HasAuraWithMechanic(MECHANIC_SNARE)) rather than a new caster-scoped check, for consistency with the existing idiom - see docs/frost-mage-talent-tree-handoff.md. The rank 3 capstone (bite a nearby chilled-enemy-triggered bounce) is a separate effect only on 200012, see that row's notes. Capstone (EFFECT_1): apply_aura 42 = SPELL_AURA_PROC_TRIGGER_SPELL, trigger_spell 200013 (Icy Bite) - AttributesEx3/ProcTypeMask copied from Brain Freeze (44546), the same 'direct Frost/spell damage, not periodic' gate already proven elsewhere in this rework; ProcChance retuned to 15 (Brain Freeze's own 5 doesn't apply here). Script overrides the default trigger target (PreventDefaultAction) to pick a nearby enemy near the struck target instead of the struck target itself, gates on the target already being chilled, and enforces the 6 sec internal cooldown via a std::chrono::steady_clock member - same idiom as spell_pal_sacred_shield_dummy (spell_paladin.cpp).",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Frost damage against targets affected by your chill effects is increased by 6%. Dealing direct Frost damage to a chilled enemy has a 15% chance to bite into a nearby enemy within 8 yards, dealing Frost damage and chilling them. Cannot occur more than once every 6 sec.', 'EquippedItemClass': -1, 'ProcChance': 15, 'SpellPriority': 50, 'SpellLevel': 1, 'AttributesEx3': 67633152, 'ProcTypeMask': 65536},
)

icy_bite_200013 = spell(
    id=200013,
    name='Icy Bite',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=49, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=189,
    coeff_weight=0.15,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 2, Biting Cold capstone). Triggered only (spell_mage_biting_cold, spell_mage.cpp) - never learned directly, same shape as Frozen Orb Pulse/Periodic (200008/200009). effect1: SPELL_EFFECT_SCHOOL_DAMAGE, 50 base + spell_bonus_data coeff_weight 0.15 (modest - a bonus proc, not a primary nuke; first-pass tuning value). effect2: SPELL_AURA_MOD_DECREASE_SPEED, mechanic 11 (MECHANIC_SNARE, matches Frostbolt's own slow so it also satisfies Unit::HasAuraWithMechanic(MECHANIC_SNARE) checks - including Biting Cold's own base effect), 20% slow for 3 sec, first-pass tuning value. Cast via caster->CastSpell(bounceTarget, 200013, true) so damage/threat attribute to the mage, not an unnamed source.",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Frost damage and a chill effect, bitten into a nearby enemy by Biting Cold.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'SpellLevel': 1, 'AuraDescription_Lang_enUS': 'Movement slowed by 30% and time between attacks increased by 25%.', 'AuraDescription_Lang_Mask': 16712190},
)

icy_shatter_200014 = spell(
    id=200014,
    name='Icy Shatter',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=1499, implicit_target_a=6),
    ],
    spell_icon_id=1236,
    coeff_weight=1.2,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 9 / sec 1 Glacial Spike, Arctic Winds capstone). Triggered only (spell_mage_glacial_spike::ConsumeIciclesAndFrostCharge, spell_mage.cpp) - never learned directly, same shape as Icy Bite (200013). Mirrors Glacial Spike's (200002) own damage exactly - 1500 base + 1.2 SP coeff (spell_bonus_data, same as 200002) - rather than re-triggering Glacial Spike itself against each additional target, which would re-run icicle/Fingers-of-Frost consumption per hit. Cast via caster->CastSpell(shatterTarget, 200014, true) for up to 5 nearby enemies within 8 yards, gated on Arctic Winds rank 3 (talent 1738, icon 2131 EFFECT_2).",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Frost damage, shattered onto a nearby enemy by Glacial Spike.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'SpellLevel': 1},
)

permafrost_200015 = spell(
    id=200015,
    name='Permafrost',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=143,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 2, Permafrost capstone). Triggered only (spell_mage_permafrost, spell_mage.cpp), granted once per second of continuous movement. Max 5 stacks (CumulativeAura). Duration bumped 3->10 sec (playtest bugfix, 2026-08-26): the original 3 sec first-pass guess decayed the whole stack before a mage could realistically stop and cast Ice Lance, making the bonus statistically undetectable in an actual playtest (5-stack vs 0-stack Ice Lance damage came back identical). 10 sec is a deliberate user call, not derived from the redesign text (which doesn't specify decay at all). Consumption also changed this pass: Ice Lance now clears the *entire* stack in one cast (spell_mage_ice_lance::ConsumePermafrost, RemoveAurasDueToSpell not ModStackAmount(-1)), and the damage bonus scales per stack consumed (20% * stack count, up to 100% at 5 stacks - Mage::ApplyDoneDamagePctMods) rather than a flat 20% regardless of banked stacks - both deliberate user calls resolving the ambiguity the previous notes flagged ('stacks read as banked charges... not fully disambiguated').",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your next Ice Lance by 20% per stack. Stacks up to 5 times, and are all consumed by your next Ice Lance.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'SpellLevel': 1, 'CumulativeAura': 5, 'AuraDescription_Lang_enUS': 'Increases the damage of your next Ice Lance by 20% per stack.', 'AuraDescription_Lang_Mask': 16712190},
)

frozen_core_200016 = spell(
    id=200016,
    name='Frozen Core',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=2132,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 5, Frozen Core). Triggered only (native PROC_TRIGGER_SPELL on the talent's own 31667), granted on taking magic damage. One dedicated spell per rank rather than a shared spell with a scripted value, since each talent rank only ever triggers its own and the % doesn't need runtime computation.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases Frost damage dealt by 2%.', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Frost damage dealt by 2%.', 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

frozen_core_200017 = spell(
    id=200017,
    name='Frozen Core',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=2132,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 5, Frozen Core). Triggered only (native PROC_TRIGGER_SPELL on the talent's own 31668), granted on taking magic damage. One dedicated spell per rank rather than a shared spell with a scripted value, since each talent rank only ever triggers its own and the % doesn't need runtime computation.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases Frost damage dealt by 4%.', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Frost damage dealt by 4%.', 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

frozen_core_200018 = spell(
    id=200018,
    name='Frozen Core',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=2132,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 5, Frozen Core). Triggered only (native PROC_TRIGGER_SPELL on the talent's own 31669), granted on taking magic damage. One dedicated spell per rank rather than a shared spell with a scripted value, since each talent rank only ever triggers its own and the % doesn't need runtime computation.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases Frost damage dealt by 6%.', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Frost damage dealt by 6%.', 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

frozen_core_piercing_cold_200019 = spell(
    id=200019,
    name='Frozen Core: Piercing Cold',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    range_yards=40.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=79, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
    ],
    spell_icon_id=2132,
    coeff_weight=0.05,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 5, Frozen Core capstone). Triggered only (spell_mage_frozen_core, spell_mage.cpp) on an Ice Lance critical strike against a frozen target. 80 base damage/tick (EffectBasePoints stored 79) + 0.05 SP coeff/tick (spell_bonus_data dot_bonus), 4 ticks over 8 sec -- modest, first-pass tuning value like this session\'s other new proc-only spells. \'Does not stack, refreshes on reapplication\' is free from native single-target same-spell-ID reapplication, no extra data needed. Playtest bugfix (2026-08-27, user call): range_yards was left blank, which reuse.py\'s range_index() defaults to RangeIndex 0 (self-only/no-range sentinel) - same root cause as the Shattering Cold bug found the same session. Since this is cast at the enemy target (not self), that silently blocked the DoT from ever landing. Set to 40 to match the other enemy-targeted triggered spells in this file (Glacial Spike, Shattering Cold, Flurry, Icy Bite/Shatter). Playtest bugfix #2 (2026-08-28, user call, "DoT lands on the caster, not the target"): effect1\'s implicit_target_a was 1 (TARGET_UNIT_CASTER/self) - wrong for an effect meant to land on the enemy target that caster->CastSpell(target, ...) in spell_mage_frozen_core (spell_mage.cpp) explicitly passes in; a self-implicit-target effect ignores the explicit CastSpell target and always resolves to the caster regardless. Set to 6 (TARGET_UNIT_TARGET_ENEMY) to match every other enemy-targeted triggered spell in this file.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': "Frost damage over time, pierced into the target's core.", 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Frost damage over time, pierced into the target's core.", 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_cone_of_cold_200020 = spell(
    id=200020,
    name='Improved Cone of Cold',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=108, misc_value=19),
    ],
    spell_icon_id=35,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 6, Improved Cone of Cold capstone). Triggered only (native PROC_TRIGGER_SPELL on 12490, rank 3), granted after landing Cone of Cold. ProcCharges=1 so the native SpellMod charge system consumes it on the very next Blizzard cast (Player::ApplySpellMod) with no script needed; the 15-sec duration is just a safety window in case Blizzard is never cast, not a real balance number -- redesign text doesn't specify one, flagged for playtest.",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Blizzard channels twice as fast.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'SpellLevel': 1, 'EffectSpellClassMaskA_1': 524416, 'ProcCharges': 1, 'AuraDescription_Lang_enUS': 'Your Blizzard channels twice as fast.', 'AuraDescription_Lang_Mask': 16712190},
)

shattered_barrier_200021 = spell(
    id=200021,
    name='Shattered Barrier',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    radius_yards=10.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-71, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED, radius_yards=10.0),
    ],
    spell_icon_id=2945,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 7, Shattered Barrier capstone). Triggered only (spell_mage_ice_barrier_aura::AfterEffectAbsorb, spell_mage.cpp), cast on the caster (TARGET_UNIT_SRC_AREA_ENEMY, implicit_target_a=6 -- same area-enemy shape as Frozen Orb Pulse/Icy Bite/Icy Shatter) when Ice Barrier's shield is destroyed by damage, not merely expiring. -70% movement speed for 4 sec, 10 yd radius, matches spec exactly.",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Movement speed reduced.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'SpellLevel': 1},
)

shattered_barrier_200022 = spell(
    id=200022,
    name='Shattered Barrier',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=65, misc_value=127),
    ],
    spell_icon_id=2945,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 7, Shattered Barrier capstone). Companion to 200021, same trigger. 8% for 8 sec -- reuses Icy Veins' own aura type (SPELL_AURA_MOD_CASTING_SPEED_NOT_STACK) for consistency ('haste' read as spell cast speed for a Mage, same as this project's other haste-flavored effects).",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell casting speed by 8%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'SpellLevel': 1, 'AuraDescription_Lang_enUS': 'Increases spell casting speed by 8%.', 'AuraDescription_Lang_Mask': 16712190},
)

empowering_frostbolt_200023 = spell(
    id=200023,
    name='Empowering Frostbolt',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=188,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 8, Empowering Frostbolt). Triggered only (native PROC_TRIGGER_SPELL on 31682), granted after casting Frostbolt. effect1: ADD_PCT_MODIFIER/SPELLMOD_CRIT_DAMAGE_BONUS, empty classmask ('of your spells', same convention as Ice Shards/Winter's Chill's own broad crit-related effects). effect2: MOD_DAMAGE_PERCENT_DONE, Frost school mask. 8 sec, matches spec exactly.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases critical strike damage bonus and Frost damage dealt.', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases critical strike damage bonus and Frost damage dealt.', 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

empowering_frostbolt_200024 = spell(
    id=200024,
    name='Empowering Frostbolt',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=188,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 8, Empowering Frostbolt). Triggered only (native PROC_TRIGGER_SPELL on 31683), granted after casting Frostbolt. effect1: ADD_PCT_MODIFIER/SPELLMOD_CRIT_DAMAGE_BONUS, empty classmask ('of your spells', same convention as Ice Shards/Winter's Chill's own broad crit-related effects). effect2: MOD_DAMAGE_PERCENT_DONE, Frost school mask. 8 sec, matches spec exactly.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases critical strike damage bonus and Frost damage dealt.', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases critical strike damage bonus and Frost damage dealt.', 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

alacrity_200071 = spell(
    id=200071,
    name='Alacrity',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=306, misc_value=4194304),
    ],
    spell_icon_id=2022,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): Alacrity rank 3 - the stock Arcane Subtlety slot this talent reuses only had 2 ranks, so this rank is a newly-minted row (reserved block) rather than an edit to an existing spell.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Cooldown Haste by 15%.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

spellblade_200072 = spell(
    id=200072,
    name='Spellblade',
    school=School.ARCANE,
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
    spell_icon_id=3006,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): Spellblade shell only - "Your melee attacks have a 12% chance to restore 20% of your base mana and grant Replenishment. Capstone: weave melee attacks between casts with no reset." Deferred to Phase 3 in full (see the design doc\'s Deferred list): "20% of base mana" needs a live read (mana pools scale with gear, not just level - not DBC-expressible), and the capstone is a combat-mechanics change. This rank\'s row is a plain SPELL_AURA_DUMMY marker (SpellIconID 3006, unique to this talent) for Phase 3 to key off via GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 3006, EFFECT_0) - no real proc wired yet. *Classless server only* per the design doc - this fork has no existing mechanism for gating a talent to one realm only; flagged for the user rather than guessed at.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee attacks have a 12% chance to restore 20% of your base mana and grant Replenishment.', 'ProcChance': 4, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 4, 'ProcCharges': 0},
)

spellblade_200073 = spell(
    id=200073,
    name='Spellblade',
    school=School.ARCANE,
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
    spell_icon_id=3006,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): Spellblade shell only - "Your melee attacks have a 12% chance to restore 20% of your base mana and grant Replenishment. Capstone: weave melee attacks between casts with no reset." Deferred to Phase 3 in full (see the design doc\'s Deferred list): "20% of base mana" needs a live read (mana pools scale with gear, not just level - not DBC-expressible), and the capstone is a combat-mechanics change. This rank\'s row is a plain SPELL_AURA_DUMMY marker (SpellIconID 3006, unique to this talent) for Phase 3 to key off via GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 3006, EFFECT_0) - no real proc wired yet. *Classless server only* per the design doc - this fork has no existing mechanism for gating a talent to one realm only; flagged for the user rather than guessed at.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee attacks have a 12% chance to restore 20% of your base mana and grant Replenishment.', 'ProcChance': 8, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 4, 'ProcCharges': 0},
)

spellblade_200074 = spell(
    id=200074,
    name='Spellblade',
    school=School.ARCANE,
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
    spell_icon_id=3006,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): Spellblade shell only - "Your melee attacks have a 12% chance to restore 20% of your base mana and grant Replenishment. Capstone: weave melee attacks between casts with no reset." Deferred to Phase 3 in full (see the design doc\'s Deferred list): "20% of base mana" needs a live read (mana pools scale with gear, not just level - not DBC-expressible), and the capstone is a combat-mechanics change. This rank\'s row is a plain SPELL_AURA_DUMMY marker (SpellIconID 3006, unique to this talent) for Phase 3 to key off via GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 3006, EFFECT_0) - no real proc wired yet. *Classless server only* per the design doc - this fork has no existing mechanism for gating a talent to one realm only; flagged for the user rather than guessed at.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee attacks have a 12% chance to restore 20% of your base mana and grant Replenishment.', 'ProcChance': 12, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 4, 'ProcCharges': 0},
)

magic_absorption_200075 = spell(
    id=200075,
    name='Magic Absorption',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=44, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=459,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): Magic Absorption rank 3 - the stock talent this reuses (id 1650) only had 2 ranks, so this rank is a newly-minted row rather than an edit to an existing spell.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all magic damage done by 3% and reduces all magic damage taken by 3%. Increases the mana you gain from Mana Gems by 45%.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_3': 16},
)

arcane_concentration_200076 = spell(
    id=200076,
    name='Arcane Concentration',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12536),
    ],
    spell_icon_id=212,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): Arcane Concentration rank 3 - the stock talent this reuses (id 82, Magic Attunement) only had 2 ranks, so this rank is a newly-minted row rather than an edit to an existing spell.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a 15% chance of entering a Clearcasting state after casting a damaging spell.', 'ProcChance': 15, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

magic_attunement_28574 = spell(
    id=28574,
    name='Magic Attunement',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-15001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=1880,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): repoints stock talent id 85 (never pulled in before) to (2,1), trimmed to 2 ranks (54659 orphaned). "Increases the effect of your Amplify Magic and Dampen Magic spells by 25/50% and reduces their cooldown by 15/30 seconds." Both spells (1008, 604) share SpellClassMask_1 8192 (verified live via the DB overlay). effect1 SPELL_AURA_ADD_PCT_MODIFIER (108)/SPELLMOD_EFFECT1 (3), effect2 SPELL_AURA_ADD_FLAT_MODIFIER (107)/SPELLMOD_COOLDOWN (11), both with EffectSpellClassMaskA_1 = 8192 in raw_overrides. Fresh row - id 28574/54658 had never been pulled into any source CSV before (an earlier pass of this edit tried to edit a row that didn\'t exist yet, a silent no-op; caught by checking the generated SQL for these IDs and finding them absent, fixed by adding them as new rows instead).',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Amplify Magic and Dampen Magic spells by 25% and reduces their cooldown by 15 seconds.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 8192, 'EffectSpellClassMaskB_1': 8192},
)

magic_attunement_54658 = spell(
    id=54658,
    name='Magic Attunement',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=1880,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): repoints stock talent id 85 (never pulled in before) to (2,1), trimmed to 2 ranks (54659 orphaned). "Increases the effect of your Amplify Magic and Dampen Magic spells by 25/50% and reduces their cooldown by 15/30 seconds." Both spells (1008, 604) share SpellClassMask_1 8192 (verified live via the DB overlay). effect1 SPELL_AURA_ADD_PCT_MODIFIER (108)/SPELLMOD_EFFECT1 (3), effect2 SPELL_AURA_ADD_FLAT_MODIFIER (107)/SPELLMOD_COOLDOWN (11), both with EffectSpellClassMaskA_1 = 8192 in raw_overrides. Fresh row - id 28574/54658 had never been pulled into any source CSV before (an earlier pass of this edit tried to edit a row that didn\'t exist yet, a silent no-op; caught by checking the generated SQL for these IDs and finding them absent, fixed by adding them as new rows instead).',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Amplify Magic and Dampen Magic spells by 50% and reduces their cooldown by 30 seconds.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 8192, 'EffectSpellClassMaskB_1': 8192},
)

student_of_the_mind_44397 = spell(
    id=44397,
    name='Student of the Mind',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=219, misc_value=3),
    ],
    spell_icon_id=1873,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): repoints stock talent id 1845 (never pulled in) to (2,2), same rank count. "You regenerate mana equal to 5/10/15% of your Intellect every 5 seconds. This regeneration continues while casting." Fully data-only - SPELL_AURA_MOD_MANA_REGEN_FROM_STAT (219), misc_value STAT_INTELLECT (3); Player::UpdateManaRegen() (StatSystem.cpp) computes GetStat(stat) * Amount / 500 as flat mp5 and applies it unconditionally to both the normal and while-casting regen fields - no live check/script needed. Fresh row - id 44397/44398/44399 had never been pulled into any source CSV before (an earlier pass of this edit tried to edit rows that didn\'t exist yet, a silent no-op; caught and fixed the same way as Magic Attunement above).',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You regenerate mana equal to 5% of your Intellect every 5 sec. This regeneration continues while casting.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

student_of_the_mind_44398 = spell(
    id=44398,
    name='Student of the Mind',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=219, misc_value=3),
    ],
    spell_icon_id=1873,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): repoints stock talent id 1845 (never pulled in) to (2,2), same rank count. "You regenerate mana equal to 5/10/15% of your Intellect every 5 seconds. This regeneration continues while casting." Fully data-only - SPELL_AURA_MOD_MANA_REGEN_FROM_STAT (219), misc_value STAT_INTELLECT (3); Player::UpdateManaRegen() (StatSystem.cpp) computes GetStat(stat) * Amount / 500 as flat mp5 and applies it unconditionally to both the normal and while-casting regen fields - no live check/script needed. Fresh row - id 44397/44398/44399 had never been pulled into any source CSV before (an earlier pass of this edit tried to edit rows that didn\'t exist yet, a silent no-op; caught and fixed the same way as Magic Attunement above).',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You regenerate mana equal to 10% of your Intellect every 5 sec. This regeneration continues while casting.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

student_of_the_mind_44399 = spell(
    id=44399,
    name='Student of the Mind',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=74, implicit_target_a=1, apply_aura=219, misc_value=3),
    ],
    spell_icon_id=1873,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): repoints stock talent id 1845 (never pulled in) to (2,2), same rank count. "You regenerate mana equal to 5/10/15% of your Intellect every 5 seconds. This regeneration continues while casting." Fully data-only - SPELL_AURA_MOD_MANA_REGEN_FROM_STAT (219), misc_value STAT_INTELLECT (3); Player::UpdateManaRegen() (StatSystem.cpp) computes GetStat(stat) * Amount / 500 as flat mp5 and applies it unconditionally to both the normal and while-casting regen fields - no live check/script needed. Fresh row - id 44397/44398/44399 had never been pulled into any source CSV before (an earlier pass of this edit tried to edit rows that didn\'t exist yet, a silent no-op; caught and fixed the same way as Magic Attunement above).',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You regenerate mana equal to 15% of your Intellect every 5 sec. This regeneration continues while casting.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_resonance_18462 = spell(
    id=18462,
    name='Arcane Resonance',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3007,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 3): repoints stock talent id 1142 (never pulled in) to (3,2). Whole talent deferred to Phase 3 (see the design doc's Deferred list) - needs a live 4-stacks-of-Arcane-Blast read at damage-calc time, mirroring Frost's Frostbite/Ice Shards MageMechanics pattern. Shell only: SPELL_AURA_DUMMY marker (SpellIconID 3007) per SKILL.md Phase 3's marker-aura-by-icon idiom. Fresh row - id 18462/18463/18464 had never been pulled into any source CSV before (same silent-no-op bug as Magic Attunement/Student of the Mind above, caught and fixed).",
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While you have 4 stacks of Arcane Blast, your Arcane damage is increased by $s1%. Spells that consume your Arcane Blast stacks benefit from this bonus.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_resonance_18463 = spell(
    id=18463,
    name='Arcane Resonance',
    school=School.ARCANE,
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
    spell_icon_id=3007,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 3): repoints stock talent id 1142 (never pulled in) to (3,2). Whole talent deferred to Phase 3 (see the design doc's Deferred list) - needs a live 4-stacks-of-Arcane-Blast read at damage-calc time, mirroring Frost's Frostbite/Ice Shards MageMechanics pattern. Shell only: SPELL_AURA_DUMMY marker (SpellIconID 3007) per SKILL.md Phase 3's marker-aura-by-icon idiom. Fresh row - id 18462/18463/18464 had never been pulled into any source CSV before (same silent-no-op bug as Magic Attunement/Student of the Mind above, caught and fixed).",
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While you have 4 stacks of Arcane Blast, your Arcane damage is increased by $s1%. Spells that consume your Arcane Blast stacks benefit from this bonus.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_resonance_18464 = spell(
    id=18464,
    name='Arcane Resonance',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3007,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 3): repoints stock talent id 1142 (never pulled in) to (3,2). Whole talent deferred to Phase 3 (see the design doc's Deferred list) - needs a live 4-stacks-of-Arcane-Blast read at damage-calc time, mirroring Frost's Frostbite/Ice Shards MageMechanics pattern. Shell only: SPELL_AURA_DUMMY marker (SpellIconID 3007) per SKILL.md Phase 3's marker-aura-by-icon idiom. Fresh row - id 18462/18463/18464 had never been pulled into any source CSV before (same silent-no-op bug as Magic Attunement/Student of the Mind above, caught and fixed).",
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While you have 4 stacks of Arcane Blast, your Arcane damage is increased by $s1%. Spells that consume your Arcane Blast stacks benefit from this bonus.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_mind_11232 = spell(
    id=11232,
    name='Arcane Mind',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=137, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=71,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Intellect by $s1%. Your magic damage is increased by up to $s2%, scaling with your current mana percentage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_mind_12500 = spell(
    id=12500,
    name='Arcane Mind',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=137, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=71,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Intellect by $s1%. Your magic damage is increased by up to $s2%, scaling with your current mana percentage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_mind_12501 = spell(
    id=12501,
    name='Arcane Mind',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=137, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=71,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Intellect by $s1%. Your magic damage is increased by up to $s2%, scaling with your current mana percentage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_mind_12502 = spell(
    id=12502,
    name='Arcane Mind',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=137, misc_value=3),
    ],
    spell_icon_id=71,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Intellect by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellLevel': 1, 'SpellPriority': 50},
)

arcane_mind_12503 = spell(
    id=12503,
    name='Arcane Mind',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=137, misc_value=3),
    ],
    spell_icon_id=71,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Intellect by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellLevel': 1, 'SpellPriority': 50},
)

incanter_s_absorption_44394 = spell(
    id=44394,
    name="Incanter's Absorption",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=44413),
        Effect(type=EffectType.APPLY_AURA, base_points=-1001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2941,
    notes='pulled from existing data | Bugfix (playtest report, 2026-09-08): Description_Lang_enUS still read as the unmodified real-game tooltip ("does not have the right tooltip and looks like its the old version") even though Phase 2/3 added the Spellsteal CD (effect2) and shield-grant proc (spell_mage_incanters_absorption_shield, spell_mage.cpp) on top of the pre-existing ward-absorb clause (kept working, untouched) - text now describes all three.',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Mana Shield, Frost Ward, Fire Ward, or Ice Barrier absorbs damage your spell damage is increased by $s1% of the amount absorbed for $44413d. Reduces the cooldown of Spellsteal by 1 sec. Casting a direct damaging Arcane spell with a cast time, or Arcane Missiles while Missile Barrage is active, grants you a shield that absorbs a small amount of damage. \n\n|cFF9D9D9DCapstone Bonus: Your Spellsteal also steals an additional spell from the target.|r', 'DurationIndex': 0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'ProcTypeMask': 65536, 'ProcCharges': 0},
)

incanter_s_absorption_44395 = spell(
    id=44395,
    name="Incanter's Absorption",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2941,
    notes="pulled from existing data | Bugfix (playtest report, 2026-09-08): Description_Lang_enUS now describes the Spellsteal CD (effect2) and shield-grant proc alongside the pre-existing ward-absorb clause - see 44394's note.",
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Mana Shield, Frost Ward, Fire Ward, or Ice Barrier absorbs damage your spell damage is increased by $s1% of the amount absorbed for $44413d. Reduces the cooldown of Spellsteal by 2 sec. Casting a direct damaging Arcane spell with a cast time, or Arcane Missiles while Missile Barrage is active, grants you a shield that absorbs a small amount of damage. \n\n|cFF9D9D9DCapstone Bonus: Your Spellsteal also steals an additional spell from the target.|r', 'DurationIndex': 0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'ProcTypeMask': 65536, 'ProcCharges': 0},
)

incanter_s_absorption_44396 = spell(
    id=44396,
    name="Incanter's Absorption",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-3001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2941,
    notes="pulled from existing data | Bugfix (playtest report, 2026-09-08): Description_Lang_enUS now describes the Spellsteal CD (effect2), shield-grant proc, and rank-3 capstone (effect3 marker, read by spell_mage_spellsteal for an extra steal) alongside the pre-existing ward-absorb clause - see 44394's note.",
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Mana Shield, Frost Ward, Fire Ward, or Ice Barrier absorbs damage your spell damage is increased by $s1% of the amount absorbed for $44413d. Reduces the cooldown of Spellsteal by 3 sec. Casting a direct damaging Arcane spell with a cast time, or Arcane Missiles while Missile Barrage is active, grants you a shield that absorbs a small amount of damage. \n\nCapstone Bonus: Your Spellsteal also steals an additional spell from the target.', 'DurationIndex': 0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'ProcTypeMask': 65536, 'ProcCharges': 0},
)

spell_power_200077 = spell(
    id=200077,
    name='Spell Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2281,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 4) - new spell, 3rd rank of Spell Power (id 1826), minted from source/ids.yaml's reserved spell block. Mirrors ranks 1-2's structure exactly.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases critical strike damage bonus of all spells by $s1%. \n\nCapstone Bonus: Dealing direct critical damage with a spell while your mana is below 50% taps into raw power, restoring 1% of your total mana each second and increasing your magic damage by 10% and Arcane damage by another 5%. This effect lasts for 10 seconds and can only occur once every 30 seconds.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 102472, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 65536, 'ProcCharges': 0},
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

spell_power_200080 = spell(
    id=200080,
    name='Spell Power',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_ENERGIZE, amplitude=1000),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=79, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=79, misc_value=64),
    ],
    spell_icon_id=2281,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch B) - Spell Power's (4,0) capstone buff, granted by spell_mage_spell_power_capstone (spell_mage.cpp) on a direct spell crit while below 50% mana, ICD 30s. effect1's mana-per-second amount is computed live from the caster's max mana at grant time (same CastCustomSpell idiom as spell_mage_magic_absorption), not a live per-tick read - matches the design's 'restoring 1% of your total mana each second' as a snapshot at proc time, not a moving target.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restoring 1% of your total mana each second, and your magic damage is increased by 10% (Arcane damage by an additional 5%).', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Restoring 1% of your total mana each second, and your magic damage is increased by 10% (Arcane damage by an additional 5%).'},
)

improved_blink_200081 = spell(
    id=200081,
    name='Improved Blink',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=1499,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch B) - Improved Blink's (4,2) capstone buff, granted by spell_mage_blink (spell_mage.cpp) after casting Blink (1953), rank 2 only.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'All damage taken is reduced by 20%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced.'},
)

arcane_shielding_200082 = spell(
    id=200082,
    name='Arcane Shielding',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=209,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch B) - Arcane Shielding's (3,0) rank 1 proc buff, granted by spell_mage_arcane_shielding_proc (spell_mage.cpp) each time Fire Ward/Frost Ward/Arcane Ward absorbs damage - same AfterEffectAbsorb hook as Incanter's Absorption's existing base script, shared spell_script_names row.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Damage dealt increased by 5%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage dealt increased.'},
)

arcane_shielding_200083 = spell(
    id=200083,
    name='Arcane Shielding',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=209,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch B) - Arcane Shielding's (3,0) rank 2 proc buff - see 200082's notes.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Damage dealt increased by 10%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage dealt increased.'},
)

improved_counterspell_200084 = spell(
    id=200084,
    name='Improved Counterspell',
    school=School.ARCANE,
    mechanic=Mechanic.SILENCE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, mechanic=Mechanic.SILENCE, implicit_target_a=6, apply_aura=AuraType.MOD_SILENCE),
    ],
    spell_icon_id=17,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch B) - Improved Counterspell's (3,1) capstone debuff, cast on Counterspell's (2139) target by spell_mage_counterspell (spell_mage.cpp) when the caster has rank 2's marker - a new debuff rather than a raw Counterspell DBC edit, so players without the talent aren't silenced.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Silenced.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Silenced.'},
)

arcane_mastery_200085 = spell(
    id=200085,
    name='Arcane Mastery',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=1500,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1976,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch C) - shared marker for Arcane Concentration\'s (2,0) and Missile Barrage\'s (5,0) Mastery clause (System Rulings: one shared hook). base_points computed live at grant time (player->GetMasteryPercentage() * 0.5, matching System Rulings\' "roughly half the coefficient of Fire\'s/Frost\'s single hook" - Frost\'s own Frostbite capstone applies GetMasteryPercentage() at full weight, unscaled), read in MageMechanics.cpp::ApplyDoneDamagePctMods. die_sides=0 so the CastCustomSpell-injected value is used exactly as passed.',
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Damage of your next spell increased by your Mastery.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Empowered by Mastery.'},
)

incanter_s_absorption_200086 = spell(
    id=200086,
    name="Incanter's Absorption",
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=2941,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch C) - Incanter\'s Absorption\'s (6,2) new "100% chance to grant a shield" proc, granted by spell_mage_incanters_absorption_shield (spell_mage.cpp) off a cast-time-bearing Arcane spell or Arcane Missiles while Missile Barrage is active. Absorb amount computed live at grant time (caster->SpellBaseDamageBonusDone(SPELL_SCHOOL_MASK_ARCANE) * 0.15, a placeholder coefficient - \'a small amount\', flagged for Phase 4 playtest tuning same as Arcane Overload\'s own coefficient). die_sides=0 so the CastCustomSpell-injected value is used exactly as passed. Separate from the existing ward-absorb-scaling mechanism (spell_mage_incanters_absorbtion_base_AuraScript) - that one is untouched.',
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Absorbs a small amount of damage.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Shielded.'},
)

spellblade_200087 = spell(
    id=200087,
    name='Spellblade',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    effects=[
        Effect(type=EffectType.ENERGIZE, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=3006,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch C) - Spellblade\'s (0,3) mana-restore clause, granted by spell_mage_spellblade (spell_mage.cpp) on a melee auto-attack proc (native ProcTypeMask 4/rank-scaled ProcChance added to 200072-200074 this batch). SPELL_EFFECT_ENERGIZE (type 30, flat amount, not the %-based ENERGIZE_PCT=137) - base_points computed live via CalculatePct(caster->GetCreateMana(), 20) (GetCreateMana() = UNIT_FIELD_BASE_MANA, the class/level base pool before Intellect scaling - matches "20% of your BASE mana" literally, distinct from max/missing mana used elsewhere in this rework). Replenishment (real stock 57669) is cast separately, alongside this, straight off its own native raid-AOE targeting (same TARGET_UNIT_CASTER_AREA_RAID/100yd shape as Brilliance Aura) - no new spell needed for that half of the clause.',
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restores mana.'},
)

netherwind_presence_200088 = spell(
    id=200088,
    name='Netherwind Presence',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=65),
    ],
    spell_icon_id=2943,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch D) - Netherwind Presence's (9,1) stacking haste buff, granted by spell_mage_netherwind_presence (spell_mage.cpp) off casting Arcane Missiles/Barrage/Blast/Starfire/Moonfire (Arcane Orb/Starsurge omitted - don't exist in this WotLK ruleset). CumulativeAura=3 (max stack) - the engine multiplies base_points by current stack count natively, same idiom as Frost's own Permafrost stacks.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'CumulativeAura': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your haste by $s1%, stacking up to 3 times.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Haste increased by $s1%.'},
)

netherwind_presence_200089 = spell(
    id=200089,
    name='Netherwind Presence',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=65),
    ],
    spell_icon_id=2943,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch D) - Netherwind Presence's (9,1) stacking haste buff, granted by spell_mage_netherwind_presence (spell_mage.cpp) off casting Arcane Missiles/Barrage/Blast/Starfire/Moonfire (Arcane Orb/Starsurge omitted - don't exist in this WotLK ruleset). CumulativeAura=3 (max stack) - the engine multiplies base_points by current stack count natively, same idiom as Frost's own Permafrost stacks.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'CumulativeAura': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your haste by $s1%, stacking up to 3 times.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Haste increased by $s1%.'},
)

netherwind_presence_200090 = spell(
    id=200090,
    name='Netherwind Presence',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=65),
    ],
    spell_icon_id=2943,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch D) - Netherwind Presence's (9,1) stacking haste buff, granted by spell_mage_netherwind_presence (spell_mage.cpp) off casting Arcane Missiles/Barrage/Blast/Starfire/Moonfire (Arcane Orb/Starsurge omitted - don't exist in this WotLK ruleset). CumulativeAura=3 (max stack) - the engine multiplies base_points by current stack count natively, same idiom as Frost's own Permafrost stacks.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'CumulativeAura': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your haste by $s1%, stacking up to 3 times.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Haste increased by $s1%.'},
)

netherwind_presence_200091 = spell(
    id=200091,
    name='Netherwind Presence',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2943,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch D) - Netherwind Presence capstone\'s internal cooldown marker ("cannot occur more than once every 30 sec"), applied to self by spell_mage_slow and checked via HasAura() before re-triggering. AttributesEx 131072 hides it from the buff bar, same flag already used on Brilliance Aura/Time Warp for their own utility auras.',
    raw_overrides={'AttributesEx': 131072, 'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190},
)

arcane_overload_200092 = spell(
    id=200092,
    name='Arcane Overload',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, die_sides=0, implicit_target_a=6, misc_value=6),
    ],
    spell_icon_id=2210,
    notes="Bugfix (playtest report, 2026-09-08) - implicit_target_a was 1 (TARGET_UNIT_CASTER), a leftover default that made this sub-spell always hit the caster instead of the passed CastCustomSpell target ('Arcane Overload deals damage to you and not the target'); fixed to 6 (TARGET_UNIT_TARGET_ENEMY). misc_value (the SPELL_EFFECT_SCHOOL_DAMAGE school index, 0=Physical/6=Arcane - distinct from the row's own SchoolMask column, which was already 64/Arcane) was left at its 0 default, so the hit rolled as Physical damage ('needs to be in the Arcane School'); fixed to 6. Original note: Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch D) - Arcane Overload's (10,1) actual damage-dealing sub-spell, hit once per target (primary + AoE-around-caster, apps/dbc-tools' own 200079 effect2) by spell_mage_arcane_overload. die_sides=0 so the CastCustomSpell-injected value (mana spent + placeholder spell power coefficient, with falloff beyond 5 targets) is used exactly as passed.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 6, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Arcane damage.', 'SpellClassMask_3': 2},
)

arcane_overload_200093 = spell(
    id=200093,
    name='Arcane Overload',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_ENERGIZE, amplitude=1000),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=79, misc_value=126),
    ],
    spell_icon_id=2210,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch D) - Arcane Overload's (10,1) 15s follow-up buff, granted by spell_mage_arcane_overload after the damage resolves.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restoring 3% of your maximum mana every 1 sec, and your spell damage is increased by 10%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Rapidly regenerating mana.'},
)

netherwind_presence_200094 = spell(
    id=200094,
    name='Netherwind Presence',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=2943,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch D) - Netherwind Presence's (9,1) capstone speed buff, granted by spell_mage_slow when Slow is cast while fully stacked (rank 3 only), gated by a 30s ICD (200091).",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Movement speed increased by 50%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed increased.'},
)


# --- talent tabs (source/talents/mage.yaml) ---

fire_41_tab = tab(
    id=41,
    name='Fire',
    class_mask=128,
    order_index=1,
    spell_icon_id=183,
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


# --- talents (source/talents/mage.yaml) ---

granted_by_talent(
    id=60007,
    tab=arcane_81_tab,
    tier=0,
    column=3,
    ranks=[spellblade_200072, spellblade_200073, spellblade_200074],
    player_castable=False,
)

granted_by_talent(
    id=23,
    tab=fire_41_tab,
    tier=2,
    column=3,
    ranks=[burning_soul_11083, burning_soul_12351],
    player_castable=False,
)

granted_by_talent(
    id=24,
    tab=fire_41_tab,
    tier=3,
    column=1,
    ranks=[molten_shields_11094, molten_shields_13043],
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

granted_by_talent(
    id=26,
    tab=fire_41_tab,
    tier=0,
    column=2,
    ranks=[improved_fireball_11069, improved_fireball_12338, improved_fireball_12339, improved_fireball_12340, improved_fireball_12341],
    player_castable=False,
)

granted_by_talent(
    id=27,
    tab=fire_41_tab,
    tier=0,
    column=0,
    ranks=[improved_fire_blast_11078, improved_fire_blast_11080],
    player_castable=False,
)

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

granted_by_talent(
    id=30,
    tab=fire_41_tab,
    tier=2,
    column=1,
    ranks=[impact_11103, impact_12357, impact_12358],
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

granted_by_talent(
    id=32,
    tab=fire_41_tab,
    tier=4,
    column=2,
    ranks=[blast_wave_11113],
    player_castable=False,
    depends_on={'talent_id': 29, 'rank': 0},
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

granted_by_talent(
    id=34,
    tab=fire_41_tab,
    tier=1,
    column=0,
    ranks=[ignite_11119, ignite_11120, ignite_12846, ignite_12847, ignite_12848],
    player_castable=False,
)

granted_by_talent(
    id=35,
    tab=fire_41_tab,
    tier=5,
    column=2,
    ranks=[fire_power_11124, fire_power_12378, fire_power_12398, fire_power_12399, fire_power_12400],
    player_castable=False,
)

granted_by_talent(
    id=36,
    tab=fire_41_tab,
    tier=6,
    column=1,
    ranks=[combustion_11129],
    player_castable=False,
    depends_on={'talent_id': 33, 'rank': 2},
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

granted_by_talent(
    id=1141,
    tab=fire_41_tab,
    tier=0,
    column=1,
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

granted_by_talent(
    id=1639,
    tab=fire_41_tab,
    tier=3,
    column=3,
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

granted_by_talent(
    id=1731,
    tab=fire_41_tab,
    tier=5,
    column=0,
    ranks=[blazing_speed_31641, blazing_speed_31642],
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

granted_by_talent(
    id=1733,
    tab=fire_41_tab,
    tier=6,
    column=0,
    ranks=[pyromaniac_34293, pyromaniac_34295, pyromaniac_34296],
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

granted_by_talent(
    id=1735,
    tab=fire_41_tab,
    tier=8,
    column=1,
    ranks=[dragon_s_breath_31661],
    player_castable=False,
    depends_on={'talent_id': 36, 'rank': 0},
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

granted_by_talent(
    id=1848,
    tab=fire_41_tab,
    tier=7,
    column=0,
    ranks=[64353, 64357],
    player_castable=False,
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

granted_by_talent(
    id=1851,
    tab=fire_41_tab,
    tier=9,
    column=1,
    ranks=[burnout_44449, burnout_44469, burnout_44470, burnout_44471, burnout_44472],
    player_castable=False,
)

granted_by_talent(
    id=1852,
    tab=fire_41_tab,
    tier=10,
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

granted_by_talent(
    id=2212,
    tab=fire_41_tab,
    tier=1,
    column=1,
    ranks=[burning_determination_54747, burning_determination_54749],
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


# --- SkillLineAbility rows not granted by any talent above (baseline player-castable spells) ---

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
