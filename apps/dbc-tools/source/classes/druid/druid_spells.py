"""
Druid - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/druid.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .druid_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, School
from lib.dsl.registry import spell
from .druid_trigger_spells import hurricane_42231, starfall_50286, tranquility_44203, typhoon_61391


demoralizing_roar_99 = spell(
    id=99,
    name='Demoralizing Roar',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-32, points_per_level=-5.428571428571429, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_ATTACK_POWER, radius_yards=10.0),
    ],
    spell_icon_id=960,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Decreases melee attack power by $s1.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "The druid roars, decreasing nearby enemies' melee attack power by $s1.  Lasts $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 144, 'SpellClassMask_1': 8, 'SpellClassSet': 7, 'SpellLevel': 10, 'SpellPriority': 50, 'SpellVisualID_1': 3949, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


entangling_roots_339 = spell(
    id=339,
    name='Entangling Roots',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.ROOT,
    attributes=1073807360,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=30.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_ROOT),
        Effect(type=EffectType.APPLY_AURA, base_points=4, points_per_level=0.4807692307692308, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    spell_icon_id=20,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1->covers-60 (anchor rank 6 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx4': 536872960, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Rooted.  Causes $s2 Nature damage every $t2 seconds.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 8, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Roots the target in place and causes $o2 Nature damage over $d.  Damage caused may interrupt the effect.', 'EffectBonusMultiplier_2': 0.10000000149011612, 'EffectBonusMultiplier_3': 0.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'ShapeshiftExclude': 2, 'SpellClassMask_1': 512, 'SpellClassSet': 7, 'SpellLevel': 8, 'SpellVisualID_1': 38, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


thorns_467 = spell(
    id=467,
    name='Thorns',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, points_per_level=0.9459459459459459, implicit_target_a=21, apply_aura=15),
    ],
    spell_icon_id=53,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 6); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Causes $s1 Nature damage to attackers.', 'BaseLevel': 6, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Thorns sprout from the friendly target causing $s1 Nature damage to attackers when hit.  Lasts $d.', 'EffectBonusMultiplier_2': 0.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 256, 'SpellClassSet': 7, 'SpellLevel': 6, 'SpellVisualID_1': 201, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


tranquility_740 = spell(
    id=740,
    name='Tranquility',
    school=School.NATURE,
    attributes=65536,
    category=46,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=480000,
    mana_cost=0,
    mana_cost_pct=70,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=35, base_points=350, points_per_level=53.68, implicit_target_a=29, apply_aura=AuraType.DUMMY, radius_yards=30.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=2000, trigger_spell=tranquility_44203.id),
    ],
    spell_icon_id=100,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 64, 'AttributesEx2': 1074266112, 'AttributesEx3': 128, 'AttributesEx5': 8192, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals nearby party members for $s1 every $t2 seconds.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals all nearby group members for $s1 every $t2 seconds for $d.  Druid must channel to maintain the spell.', 'EffectBonusMultiplier_1': 0.28600001335144043, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 1073741824, 'ShapeshiftMask': 2, 'SpellClassMask_1': 128, 'SpellClassSet': 7, 'SpellLevel': 30, 'SpellVisualID_1': 1283, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


cat_form_768 = spell(
    id=768,
    name='Cat Form',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=35,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=5000),
    ],
    spell_icon_id=493,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 98304, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immunity to Polymorph effects.  Increases melee attack power by $3025s1 plus Agility.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shapeshift into cat form, increasing melee attack power by $3025s1 plus Agility.  Also protects the caster from Polymorph effects and allows the use of various cat abilities.\r\n\r\nThe act of shapeshifting frees the caster of Polymorph and Movement Impairing effects.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Shapeshift', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 1073741826, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellVisualID_1': 4228, 'StanceBarOrder': 2, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


faerie_fire_770 = spell(
    id=770,
    name='Faerie Fire',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=30.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=6, apply_aura=101, misc_value=1),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=186, misc_value=127),
    ],
    spell_icon_id=109,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 98304, 'AttributesEx2': 524288, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Decreases armor by $s1%.  Cannot stealth or turn invisible.', 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Decrease the armor of the target by $s1% for $d.  While affected, the target cannot stealth or turn invisible.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 2, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 1024, 'SpellClassSet': 7, 'SpellLevel': 18, 'SpellVisualID_1': 192, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rejuvenation_774 = spell(
    id=774,
    name='Rejuvenation',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=40.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, points_per_level=3.8214285714285716, implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000),
    ],
    spell_icon_id=64,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60 (anchor rank 11 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx4': 1048576, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals $s1 damage every $t1 seconds.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target for ${$m1*5*$<mult>} over $d.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 0.37599998712539673, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 1073741824, 'ShapeshiftMask': 2, 'SpellClassMask_1': 16, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 176, 'SpellLevel': 4, 'SpellVisualID_1': 32, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


swipe_bear_779 = spell(
    id=779,
    name='Swipe (Bear)',
    school=School.NORMAL,
    attributes=262160,
    category=85,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=8.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=8, points_per_level=1.546875, implicit_target_a=22, implicit_target_b=15, radius_yards=8.0),
    ],
    spell_icon_id=1562,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 16); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Swipe nearby enemies, inflicting $s1 damage.  Damage increased by attack power.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'ShapeshiftMask': 144, 'SpellClassMask_2': 1048576, 'SpellClassSet': 7, 'SpellLevel': 16, 'SpellVisualID_1': 189, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


travel_form_783 = spell(
    id=783,
    name='Travel Form',
    school=School.NORMAL,
    attributes=360464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=13,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
    ],
    spell_icon_id=1476,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 98304, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Polymorph effects.  Movement speed increased by $5419s1%.', 'BaseLevel': 16, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shapeshift into travel form, increasing movement speed by $5419s1%.  Also protects the caster from Polymorph effects.  Only useable outdoors.\r\n\r\nThe act of shapeshifting frees the caster of Polymorph and Movement Impairing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Shapeshift', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 1073741826, 'SpellClassMask_2': 16384, 'SpellClassSet': 7, 'SpellLevel': 16, 'SpellVisualID_1': 4228, 'StanceBarOrder': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


aquatic_form_1066 = spell(
    id=1066,
    name='Aquatic Form',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=13,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=4),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
    ],
    spell_icon_id=1475,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 229376, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Polymorph effects.  Increases swim speed by $5421s1% and allows underwater breathing.', 'AuraInterruptFlags': 256, 'BaseLevel': 16, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shapeshift into aquatic form, increasing swim speed by $5421s1% and allowing the druid to breathe underwater.  Also protects the caster from Polymorph effects.\r\n\r\nThe act of shapeshifting frees the caster of Polymorph and Movement Impairing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Shapeshift', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 1073741826, 'SpellClassMask_1': 536870912, 'SpellClassSet': 7, 'SpellLevel': 16, 'SpellVisualID_1': 775, 'StanceBarOrder': 1, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rip_1079 = spell(
    id=1079,
    name='Rip',
    school=School.NORMAL,
    mechanic=15,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=30,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, points_per_level=0.55, mechanic=15, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
    ],
    spell_icon_id=108,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1049088, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Bleed damage every $t1 seconds.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that causes damage over time.  Damage increases per combo point and by your attack power:\r\n   1 point: ${($m1+$b1*1+0.01*$AP)*$<dur>} damage over $d.\r\n   2 points: ${($m1+$b1*2+0.02*$AP)*$<dur>} damage over $d.\r\n   3 points: ${($m1+$b1*3+0.03*$AP)*$<dur>} damage over $d.\r\n   4 points: ${($m1+$b1*4+0.04*$AP)*$<dur>} damage over $d.\r\n   5 points: ${($m1+$b1*5+0.05*$AP)*$<dur>} damage over $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_1': 4.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_1': 8388608, 'SpellClassMask_3': 2097152, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 165, 'SpellLevel': 20, 'SpellVisualID_1': 3941, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


claw_1082 = spell(
    id=1082,
    name='Claw',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=45,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=26, points_per_level=5.716666666666667, implicit_target_a=6),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=262,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Claw the enemy, causing $s1 additional damage.  Awards $s2 combo $lpoint:points;.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_3': 262144, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellVisualID_1': 3882, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


mark_of_the_wild_1126 = spell(
    id=1126,
    name='Mark of the Wild',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=24,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, points_per_level=9.177215189873417, implicit_target_a=21, apply_aura=22, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=-1),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=21, apply_aura=143, misc_value=126),
    ],
    spell_icon_id=123,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the friendly target's armor by $s1 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 262144, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 212, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rake_1822 = spell(
    id=1822,
    name='Rake',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=40,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=9000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=16, points_per_level=2.8392857142857144, mechanic=15, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=29, points_per_level=5.857142857142857, mechanic=15, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=494,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 24); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 8, 'AttributesEx4': 1048576, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Bleeding for $s2 damage every $t2 seconds.', 'BaseLevel': 24, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Rake the target for ${$AP/100+$m1} bleed damage and an additional ${$m2*3+$AP*0.18} damage over $d.  Awards $s3 combo $lpoint:points;.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_1': 4096, 'SpellClassSet': 7, 'SpellLevel': 24, 'SpellVisualID_1': 750, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


dash_1850 = spell(
    id=1850,
    name='Dash',
    school=School.NORMAL,
    attributes=262160,
    category=44,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=180000,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, points_per_level=0.29411764705882354, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=959,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 26); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases movement speed by $s1% while in Cat Form.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases movement speed by $s1% while in Cat Form for $d.  Does not break prowling.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 8, 'SpellClassSet': 7, 'SpellLevel': 26, 'SpellVisualID_1': 2276},
)


hibernate_2637 = spell(
    id=2637,
    name='Hibernate',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.SLEEP,
    attributes=1074855936,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=30.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=44,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 18); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 262144, 'AttributesEx2': 524288, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Asleep.', 'AuraInterruptFlags': 2, 'BaseLevel': 18, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Forces the enemy target to sleep for up to $d.  Any damage will awaken the target.  Only one target can be forced to hibernate at a time.  Only works on Beasts and Dragonkin.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 2, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 16777216, 'SpellClassMask_2': 131072, 'SpellClassMask_3': 32768, 'SpellClassSet': 7, 'SpellLevel': 18, 'SpellPriority': 50, 'SpellVisualID_1': 4999, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 3},
)


remove_curse_2782 = spell(
    id=2782,
    name='Remove Curse',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=2),
    ],
    spell_icon_id=236,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 24, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dispels $s1 Curse from a friendly target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 4194304, 'SpellClassSet': 7, 'SpellLevel': 24, 'SpellVisualID_1': 186, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


abolish_poison_2893 = spell(
    id=2893,
    name='Abolish Poison',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=67584,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=13,
    range_yards=40.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=3000, trigger_spell=3137),
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=4),
    ],
    spell_icon_id=265,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attempts to cure $3137s1 poison every $t1 seconds.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Attempts to cure $s2 poison effect on the target, and $3137s1 more poison effect every $t1 seconds for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 4, 'SpellClassSet': 7, 'SpellLevel': 26, 'SpellVisualID_1': 3885, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


soothe_animal_2908 = spell(
    id=2908,
    name='Soothe Animal',
    school=School.NATURE,
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
    spell_icon_id=454,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 22); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 2228224, 'AttributesEx2': 524288, 'AttributesEx3': 196608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduced distance at which target will attack.', 'BaseLevel': 22, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Soothes the target beast, reducing the range at which it will attack you by $s1 yards.  Only affects Beast and Dragonkin targets level 40 or lower.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'MaxTargetLevel': 40, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 2, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 16777216, 'SpellClassMask_2': 131072, 'SpellClassMask_3': 8192, 'SpellClassSet': 7, 'SpellLevel': 22, 'SpellPriority': 50, 'SpellVisualID_1': 6439, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 3},
)


starfire_2912 = spell(
    id=2912,
    name='Starfire',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=3500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=120, points_per_level=14.3, die_sides=29, implicit_target_a=6),
    ],
    spell_icon_id=1485,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60 (anchor rank 7 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 22, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes $s1 Arcane damage to the target.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 2, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 4, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 1264, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


wrath_5176 = spell(
    id=5176,
    name='Wrath',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=16, points_per_level=5.111864397081278, die_sides=3, implicit_target_a=6),
    ],
    spell_icon_id=263,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 8 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes $s1 Nature damage to the target.', 'EffectBonusMultiplier_1': 0.5709999799728394, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 2, 'ShapeshiftMask': 1073741824, 'Speed': 20.0, 'SpellClassMask_1': 1, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellVisualID_1': 3860, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


healing_touch_5185 = spell(
    id=5185,
    name='Healing Touch',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=33,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=36, points_per_level=47.144303792639626, die_sides=15, implicit_target_a=21),
    ],
    spell_icon_id=962,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 15 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for $<min> to $<max>.', 'EffectBonusMultiplier_1': 1.6100000143051147, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 1073741824, 'SpellClassMask_1': 32, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 28, 'SpellLevel': 1, 'SpellVisualID_1': 58, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


challenging_roar_5209 = spell(
    id=5209,
    name='Challenging Roar',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_TAUNT, radius_yards=10.0),
    ],
    spell_icon_id=957,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 67108864, 'AttributesEx4': 2048, 'AttributesEx5': 2147483648, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunted.', 'BaseLevel': 28, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Forces all nearby enemies within $a1 yards to focus attacks on you for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 144, 'SpellClassMask_3': 1, 'SpellClassSet': 7, 'SpellLevel': 28, 'SpellVisualID_1': 748, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


bash_5211 = spell(
    id=5211,
    name='Bash',
    school=School.NORMAL,
    mechanic=Mechanic.STUN,
    attributes=262160,
    category=32,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=473,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 14); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134480384, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Stuns the target for $d and interrupts non-player spellcasting for $32747d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 144, 'SpellClassMask_1': 8192, 'SpellClassSet': 7, 'SpellLevel': 14, 'SpellPriority': 50, 'SpellVisualID_1': 3948, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prowl_5215 = spell(
    id=5215,
    name='Prowl',
    school=School.NORMAL,
    dispel=DispelType.STEALTH,
    attributes=437518352,
    category=38,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, points_per_level=5.0, implicit_target_a=1, apply_aura=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=103,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 30, 'AttributesEx': 16, 'AttributesEx2': 2097152, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stealthed.  Movement speed slowed by $s2%.', 'AuraInterruptFlags': 15366, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows the Druid to prowl around, but reduces your movement speed by $s2%.  Lasts until cancelled.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeCasterAuraState': 12, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'ShapeshiftMask': 1, 'SpellClassMask_1': 16384, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellVisualID_1': 184, 'StartRecoveryCategory': 1178},
)


tiger_s_fury_5217 = spell(
    id=5217,
    name="Tiger's Fury",
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=30000,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=1.25, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE, misc_value=1),
    ],
    spell_icon_id=1181,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 24); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases damage done by $s1.', 'BaseLevel': 24, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases damage done by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeCasterAuraSpell': 50334, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 1, 'SpellClassMask_3': 2048, 'SpellClassSet': 7, 'SpellLevel': 24, 'SpellPriority': 50, 'SpellVisualID_1': 200},
)


shred_5221 = spell(
    id=5221,
    name='Shred',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=60,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=23, points_per_level=4.689655172413793, implicit_target_a=6),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
        Effect(type=31, base_points=224, implicit_target_a=6),
    ],
    spell_icon_id=147,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 22); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 1048576, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 22, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shred the target, causing $s3% damage plus 54 to the target.  Must be behind the target.  Awards $s2 combo $lpoint:points;.  Effects which increase Bleed damage also increase Shred damage.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_1': 32768, 'SpellClassSet': 7, 'SpellLevel': 22, 'SpellVisualID_1': 3950, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


enrage_5229 = spell(
    id=5229,
    name='Enrage',
    school=School.NORMAL,
    dispel=9,
    mechanic=31,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.PERIODIC_ENERGIZE, amplitude=1000, misc_value=1),
        Effect(type=EffectType.ENERGIZE, base_points=199, implicit_target_a=1, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=94),
    ],
    spell_icon_id=961,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Gain $/10;s1 rage per second.  Base armor reduced.', 'BaseLevel': 12, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Generates $/10;s2 rage, and then generates an additional $/10;o1 rage over $d, but reduces base armor by 27% in Bear Form and 16% in Dire Bear Form.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 144, 'SpellClassMask_1': 524288, 'SpellClassSet': 7, 'SpellLevel': 12, 'SpellVisualID_1': 249},
)


bear_form_5487 = spell(
    id=5487,
    name='Bear Form',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=35,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
    ],
    spell_icon_id=107,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 98304, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Polymorph effects.  Increases melee attack power by $1178s3, armor contribution from cloth and leather items by $1178s1%, and Stamina by $1178s2%.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shapeshift into bear form, increasing melee attack power by $1178s3, armor contribution from cloth and leather items by $1178s1%, and Stamina by $1178s2%.  Also protects the caster from Polymorph effects and allows the use of various bear abilities.\r\n\r\nThe act of shapeshifting frees the caster of Polymorph and Movement Impairing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 1073741826, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 7, 'SpellLevel': 10, 'SpellVisualID_1': 653, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mark_of_the_wild_6756 = spell(
    id=6756,
    name='Mark of the Wild',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=24,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=104, implicit_target_a=21, apply_aura=22, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=-1),
    ],
    spell_icon_id=123,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by quest_template reward/display spell)',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1 and all attributes by $s2.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the friendly target's armor by $s1 and all attributes by $s2 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 262144, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 212, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ravage_6785 = spell(
    id=6785,
    name='Ravage',
    school=School.NORMAL,
    attributes=2490384,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=60,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=41, points_per_level=8.708333333333334, implicit_target_a=6),
        Effect(type=31, base_points=384, implicit_target_a=6),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=1531,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 32); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 1048576, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 32, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Ravage the target, causing $s2% damage plus ${$m1*$m2/100} to the target.  Must be prowling and behind the target.  Awards $s3 combo $lpoint:points;.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 7, 'SpellLevel': 32, 'SpellPriority': 50, 'SpellVisualID_1': 2275, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


maul_6807 = spell(
    id=6807,
    name='Maul',
    school=School.NORMAL,
    attributes=1044,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=17, points_per_level=8.0, implicit_target_a=6),
    ],
    spell_icon_id=261,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 4096, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A strong attack that increases melee damage by $s1 and causes a high amount of threat.  Effects which increase Bleed damage also increase Maul damage.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 144, 'SpellClassMask_1': 2048, 'SpellClassSet': 7, 'SpellLevel': 10, 'SpellVisualID_1': 166},
)


moonfire_8921 = spell(
    id=8921,
    name='Moonfire',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=21,
    range_yards=30.0,
    duration_ms=9000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, points_per_level=2.5789473684210527, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=6, points_per_level=5.25, die_sides=3, implicit_target_a=6),
    ],
    spell_icon_id=225,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 14 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Arcane damage every $t1 seconds.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Burns the enemy for $s2 Arcane damage and then an additional ${$m1*3*$<mult>} Arcane damage over $d.', 'EffectBonusMultiplier_1': 0.12999999523162842, 'EffectBonusMultiplier_2': 0.15000000596046448, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 2, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 2, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 176, 'SpellLevel': 4, 'SpellVisualID_1': 1263, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


regrowth_8936 = spell(
    id=8936,
    name='Regrowth',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=29,
    range_yards=40.0,
    duration_ms=21000,
    effects=[
        Effect(type=EffectType.HEAL, base_points=83, points_per_level=31.957352932761697, die_sides=15, implicit_target_a=21),
        Effect(type=EffectType.APPLY_AURA, base_points=13, points_per_level=4.720588235294118, implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000),
    ],
    spell_icon_id=197,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 12); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 12 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx4': 1048576, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals $s2 every $t2 seconds.', 'BaseLevel': 12, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for $s1 and another ${$m2*7*$<mult>} over $d.', 'EffectBonusMultiplier_1': 0.5379999876022339, 'EffectBonusMultiplier_2': 0.18799999356269836, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 1073741824, 'ShapeshiftMask': 2, 'SpellClassMask_1': 64, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 176, 'SpellLevel': 12, 'SpellVisualID_1': 58, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


cower_8998 = spell(
    id=8998,
    name='Cower',
    school=School.NORMAL,
    attributes=262160,
    category=84,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.ENERGY,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.THREAT, base_points=-241, points_per_level=-62.26923076923077, implicit_target_a=6),
    ],
    spell_icon_id=958,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 28); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx2': 67108864, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 28, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Cower, causing no damage but lowering your threat a small amount, making the enemy less likely to attack you.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_2': 536870912, 'SpellClassSet': 7, 'SpellLevel': 28, 'SpellVisualID_1': 3883, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


pounce_9005 = spell(
    id=9005,
    name='Pounce',
    school=School.NORMAL,
    attributes=2490384,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.STUN, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=9007),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=495,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 36); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'ActiveIconID': 495, 'AttributesEx': 134218240, 'AttributesEx2': 1048576, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'BaseLevel': 36, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Pounce, stunning the target for $d and causing $9007o1 damage over $9007d.  Must be prowling.  Awards $s3 combo $lpoint:points;.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_1': 131072, 'SpellClassSet': 7, 'SpellLevel': 36, 'SpellPriority': 50, 'SpellVisualID_1': 3942, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


mark_of_the_wild_9884 = spell(
    id=9884,
    name='Mark of the Wild',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=24,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=239, implicit_target_a=21, apply_aura=22, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=-1),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=21, apply_aura=143, misc_value=126),
    ],
    spell_icon_id=123,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by quest_template reward/display spell)',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1, all attributes by $s2 and all resistances by $s3.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the friendly target's armor by $s1, all attributes by $s2 and all resistances by $s3 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 262144, 'SpellClassSet': 7, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 212, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


nature_s_grasp_16689 = spell(
    id=16689,
    name="Nature's Grasp",
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=531,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=45000,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=19975),
    ],
    spell_icon_id=168,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60 (anchor rank 6 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee damage you take has a chance to entangle the enemy.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While active, any time an enemy strikes the caster they have a $h% chance to become afflicted by Entangling Roots (Rank 1). $n charges.  Lasts $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 3, 'ProcTypeMask': 40, 'RangeIndex': 1, 'ShapeshiftMask': 1073741969, 'SpellClassMask_1': 1048576, 'SpellClassMask_3': 4096, 'SpellClassSet': 7, 'SpellLevel': 10, 'SpellVisualID_1': 212, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


faerie_fire_feral_16857 = spell(
    id=16857,
    name='Faerie Fire (Feral)',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=16,
    category=1133,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=6, apply_aura=101, misc_value=1),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=186, misc_value=127),
    ],
    spell_icon_id=109,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 98304, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Decreases armor by $s1%.  Cannot stealth or turn invisible.', 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Decrease the armor of the target by $16857s1% for $16857d.  While affected, the target cannot stealth or turn invisible.  Deals ${$AP*0.15+1} damage and additional threat when used in Bear Form or Dire Bear Form.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 145, 'SpellClassMask_1': 1024, 'SpellClassSet': 7, 'SpellLevel': 18, 'SpellVisualID_1': 192, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


hurricane_16914 = spell(
    id=16914,
    name='Hurricane',
    school=School.NATURE,
    attributes=65536,
    category=571,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=81,
    range_yards=30.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=-1, mechanic=Mechanic.SNARE, implicit_target_a=28, apply_aura=AuraType.MOD_DECREASE_SPEED, radius_yards=8.0),
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=-21, mechanic=8, implicit_target_a=28, apply_aura=138, radius_yards=8.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=hurricane_42231.id),
    ],
    spell_icon_id=220,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 140, 'AttributesEx2': 4718592, 'AttributesEx5': 134225920, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$42231s1 damage every $t3 seconds, and time between attacks increased by $s2%.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a violent storm in the target area causing $42231s1 Nature damage to enemies every $16914t3 sec,$?s54831[ reducing movement speed by $54831s1%, ][ ]and increasing the time between attacks of enemies by $16914s2%.  Lasts $16914d.  Druid must channel to maintain the spell.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 2, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 4194304, 'SpellClassSet': 7, 'SpellLevel': 40, 'SpellVisualID_1': 9489, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)


entangling_roots_19975 = spell(
    id=19975,
    name='Entangling Roots',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.ROOT,
    attributes=1224802304,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_ROOT),
        Effect(type=EffectType.APPLY_AURA, base_points=4, points_per_level=0.4807692307692308, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    spell_icon_id=20,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1->covers-60 (anchor rank 6 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx4': 536872960, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Rooted.  Causes $s2 Nature damage every $t2 seconds.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 8, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Roots the target in place and causes $o2 Nature damage over $d.  Damage caused may interrupt the effect.  Only useable outdoors.', 'EffectBonusMultiplier_2': 0.10000000149011612, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'SpellClassMask_1': 512, 'SpellClassSet': 7, 'SpellLevel': 8, 'SpellVisualID_1': 38, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rebirth_20484 = spell(
    id=20484,
    name='Rebirth',
    school=School.NATURE,
    attributes=65536,
    category=26,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=600000,
    mana_cost=0,
    mana_cost_pct=68,
    range_yards=30.0,
    effects=[
        Effect(type=113, base_points=399, points_per_level=100.0, misc_value=700),
    ],
    spell_icon_id=24,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 16, 'AttributesEx4': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Returns the spirit to the body, restoring a dead target to life with $s1 health and $q mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ReagentCount_1': 1, 'Reagent_1': 17034, 'ShapeshiftExclude': 1073741824, 'SpellClassMask_1': 285212672, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 344, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 32768},
)


gift_of_the_wild_21849 = spell(
    id=21849,
    name='Gift of the Wild',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=64,
    range_yards=40.0,
    duration_ms=3600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=239, points_per_level=17.0, implicit_target_a=56, apply_aura=22, misc_value=1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=0.9, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=-1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=14, points_per_level=1.3, implicit_target_a=56, apply_aura=143, misc_value=126, radius_yards=100.0),
    ],
    spell_icon_id=2435,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1, all attributes by $s2 and all resistances by $s3.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives the Gift of the Wild to all party and raid members, increasing armor by $s1, all attributes by $s2 and all resistances by $s3 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17021, 'SpellClassMask_1': 262144, 'SpellClassSet': 7, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 212, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


gift_of_the_wild_21850 = spell(
    id=21850,
    name='Gift of the Wild',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=64,
    range_yards=40.0,
    duration_ms=3600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=284, implicit_target_a=56, apply_aura=22, misc_value=1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=-1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=56, apply_aura=143, misc_value=126, radius_yards=100.0),
    ],
    spell_icon_id=2435,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1, all attributes by $s2 and all resistances by $s3.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives the Gift of the Wild to all party and raid members, increasing armor by $s1, all attributes by $s2 and all resistances by $s3 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17026, 'SpellClassMask_1': 262144, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 212, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ferocious_bite_22568 = spell(
    id=22568,
    name='Ferocious Bite',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=13, points_per_level=2.2083333333333335, die_sides=17, implicit_target_a=6),
    ],
    spell_icon_id=1680,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 32); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1049088, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 32, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that causes damage per combo point and converts each extra point of energy (up to a maximum of $s2 extra energy) into ${$f1+$AP/410}.1 additional damage.  Damage is increased by your attack power.\r\n   1 point  : ${$m1+$b1*1+0.07*$AP}-${$M1+$b1*1+0.07*$AP} damage\r\n   2 points: ${$m1+$b1*2+0.14*$AP}-${$M1+$b1*2+0.14*$AP} damage\r\n   3 points: ${$m1+$b1*3+0.21*$AP}-${$M1+$b1*3+0.21*$AP} damage\r\n   4 points: ${$m1+$b1*4+0.28*$AP}-${$M1+$b1*4+0.28*$AP} damage\r\n   5 points: ${$m1+$b1*5+0.35*$AP}-${$M1+$b1*5+0.35*$AP} damage', 'EffectBasePoints_2': 29, 'EffectBonusMultiplier_1': 0.0, 'EffectChainAmplitude_1': 0.699999988079071, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectPointsPerCombo_1': 36.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_1': 8388608, 'SpellClassSet': 7, 'SpellLevel': 32, 'SpellVisualID_1': 6587, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


maim_22570 = spell(
    id=22570,
    name='Maim',
    school=School.NORMAL,
    attributes=262160,
    category=33,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=44, points_per_level=1.1666666666666667, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, mechanic=Mechanic.STUN, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=1681,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 62); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 2 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 5505024, 'AttributesEx4': 8388608, 'AttributesEx7': 2048, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'BaseLevel': 62, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that causes damage and stuns the target.  Non-player victim spellcasting is also interrupted for $32747d.  Causes more damage and lasts longer per combo point:\r\n   1 point  : ${$b1*1+$m1+$mw}-${$b1*1+$M1+$MW} damage, 1 sec\r\n   2 points: ${$b1*2+$m1+$mw}-${$b1*2+$M1+$MW} damage, 2 sec\r\n   3 points: ${$b1*3+$m1+$mw}-${$b1*3+$M1+$MW} damage, 3 sec\r\n   4 points: ${$b1*4+$m1+$mw}-${$b1*4+$M1+$MW} damage, 4 sec\r\n   5 points: ${$b1*5+$m1+$mw}-${$b1*5+$M1+$MW} damage, 5 sec', 'DurationIndex': 187, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_1': 84.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_2': 128, 'SpellClassSet': 7, 'SpellLevel': 62, 'SpellVisualID_1': 8148, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


barkskin_22812 = spell(
    id=22812,
    name='Barkskin',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=149, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=50411),
    ],
    spell_icon_id=689,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 131080, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All damage taken is reduced by $s2%.  While protected, damaging attacks will not cause spellcasting delays.', 'BaseLevel': 44, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "The druid's skin becomes as tough as bark.  All damage taken is reduced by $s2%.  While protected, damaging attacks will not cause spellcasting delays.  This spell is usable while stunned, frozen, incapacitated, feared or asleep.  Usable in all forms.  Lasts $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_1': 16777829, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcTypeMask': 40, 'RangeIndex': 1, 'SpellClassMask_2': 262144, 'SpellClassSet': 7, 'SpellLevel': 44, 'SpellVisualID_1': 6662},
)


frenzied_regeneration_22842 = spell(
    id=22842,
    name='Frenzied Regeneration',
    school=School.NORMAL,
    attributes=262160,
    category=1011,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=180000,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=226, amplitude=1000),
        Effect(type=EffectType.DUMMY, base_points=2, implicit_target_a=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=50,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Converting rage into health.', 'BaseLevel': 36, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Converts up to 10 rage per second into health for $d.  Each point of rage is converted into ${$m2/10}.1% of max health.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 144, 'SpellClassMask_2': 1073741824, 'SpellClassSet': 7, 'SpellLevel': 36, 'SpellVisualID_1': 249, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


healing_touch_25297 = spell(
    id=25297,
    name='Healing Touch',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=33,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=1943, points_per_level=6.199999809265137, die_sides=351, implicit_target_a=21),
    ],
    spell_icon_id=962,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for $<min> to $<max>.', 'EffectBonusMultiplier_1': 1.6100000143051147, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 65, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 11', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 1073741824, 'SpellClassMask_1': 32, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 28, 'SpellLevel': 60, 'SpellVisualID_1': 58, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


starfire_25298 = spell(
    id=25298,
    name='Starfire',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=3500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=692, points_per_level=3.0999999046325684, die_sides=125, implicit_target_a=6),
    ],
    spell_icon_id=1485,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 22, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes $s1 Arcane damage to the target.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 66, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 2, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 4, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 1264, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rejuvenation_25299 = spell(
    id=25299,
    name='Rejuvenation',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=40.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=221, implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000),
    ],
    spell_icon_id=64,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx4': 1048576, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals $s1 damage every $t1 seconds.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target for ${$m1*5*$<mult>} over $d.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 0.37599998712539673, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 65, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 11', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 1073741824, 'ShapeshiftMask': 2, 'SpellClassMask_1': 16, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 176, 'SpellLevel': 60, 'SpellVisualID_1': 32, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


gift_of_the_wild_26991 = spell(
    id=26991,
    name='Gift of the Wild',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=64,
    range_yards=40.0,
    duration_ms=3600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=339, implicit_target_a=56, apply_aura=22, misc_value=1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=-1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=56, apply_aura=143, misc_value=126, radius_yards=100.0),
    ],
    spell_icon_id=2435,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1, all attributes by $s2 and all resistances by $s3.', 'BaseLevel': 70, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives the Gift of the Wild to all party and raid members, increasing armor by $s1, all attributes by $s2 and all resistances by $s3 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 22148, 'SpellClassMask_1': 262144, 'SpellClassSet': 7, 'SpellLevel': 70, 'SpellPriority': 50, 'SpellVisualID_1': 212, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


innervate_29166 = spell(
    id=29166,
    name='Innervate',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=224, implicit_target_a=21, apply_aura=AuraType.PERIODIC_ENERGIZE, amplitude=1000),
    ],
    spell_icon_id=62,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx7': 65536, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Regenerating mana.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Causes the target to regenerate mana equal to $s1% of the casting Druid's base mana pool over $d.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 1073741826, 'SpellClassMask_2': 4096, 'SpellClassSet': 7, 'SpellLevel': 40, 'SpellVisualID_1': 3884, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ferocious_bite_31018 = spell(
    id=31018,
    name='Ferocious Bite',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=51, die_sides=61, implicit_target_a=6),
    ],
    spell_icon_id=1680,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx': 1049088, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that causes damage per combo point and converts each extra point of energy (up to a maximum of $s2 extra energy) into ${$f1+$AP/410}.1 additional damage.  Damage is increased by your attack power.\r\n   1 point  : ${$m1+$b1*1+0.07*$AP}-${$M1+$b1*1+0.07*$AP} damage\r\n   2 points: ${$m1+$b1*2+0.14*$AP}-${$M1+$b1*2+0.14*$AP} damage\r\n   3 points: ${$m1+$b1*3+0.21*$AP}-${$M1+$b1*3+0.21*$AP} damage\r\n   4 points: ${$m1+$b1*4+0.28*$AP}-${$M1+$b1*4+0.28*$AP} damage\r\n   5 points: ${$m1+$b1*5+0.35*$AP}-${$M1+$b1*5+0.35*$AP} damage', 'EffectBasePoints_2': 29, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 2.0999999046325684, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectPointsPerCombo_1': 147.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_1': 8388608, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellVisualID_1': 6587, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


cower_31709 = spell(
    id=31709,
    name='Cower',
    school=School.NORMAL,
    attributes=262160,
    category=84,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.ENERGY,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.THREAT, base_points=-801, points_per_level=-1.0, implicit_target_a=6),
    ],
    spell_icon_id=958,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx2': 67108864, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Cower, causing no damage but lowering your threat a large amount, making the enemy less likely to attack you.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 70, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_2': 536870912, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellVisualID_1': 3883, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


lacerate_33745 = spell(
    id=33745,
    name='Lacerate',
    school=School.NORMAL,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=30, points_per_level=2.357142857142857, mechanic=15, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=30, points_per_level=4.071428571428571, implicit_target_a=6),
    ],
    spell_icon_id=2246,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 66); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 3 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 128, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 damage every $t sec', 'BaseLevel': 66, 'CastingTimeIndex': 1, 'CumulativeAura': 5, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Lacerates the enemy target, dealing $s2 damage and making them bleed for $o damage over $d and causing a high amount of threat.  Damage increased by attack power.  This effect stacks up to $u times on the same target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 144, 'SpellClassMask_2': 256, 'SpellClassSet': 7, 'SpellLevel': 66, 'SpellVisualID_1': 8146, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


lifebloom_33763 = spell(
    id=33763,
    name='Lifebloom',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=28,
    range_yards=40.0,
    duration_ms=7000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=31, points_per_level=1.3125, implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=1000),
        Effect(type=EffectType.APPLY_AURA, base_points=479, points_per_level=18.5, implicit_target_a=21, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2101,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 64); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 3 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals $s1 every second and $s2 when effect finishes or is dispelled.', 'BaseLevel': 64, 'CastingTimeIndex': 1, 'CumulativeAura': 3, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target for ${$m1*7*$<mult>} over $d.  When Lifebloom completes its duration or is dispelled, the target instantly heals themself for $s2 and the Druid regains half the cost of the spell.  This effect can stack up to $u times on the same target.', 'EffectBonusMultiplier_1': 0.09520000219345093, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 1073741824, 'ShapeshiftMask': 2, 'SpellClassMask_2': 16, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 176, 'SpellLevel': 64, 'SpellVisualID_1': 8145, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


cyclone_33786 = spell(
    id=33786,
    name='Cyclone',
    school=School.NATURE,
    mechanic=Mechanic.BANISH,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=20.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=39, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=6, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=174,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 65536, 'AttributesEx4': 536872960, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Invulnerable, but unable to act.', 'BaseLevel': 70, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Tosses the enemy target into the air, preventing all action but making them invulnerable for up to $d.  Only one target can be affected by your Cyclone at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 2, 'SpellClassMask_2': 32, 'SpellClassSet': 7, 'SpellLevel': 70, 'SpellVisualID_1': 8206, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mangle_cat_33876 = spell(
    id=33876,
    name='Mangle (Cat)',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=45,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=98, points_per_level=6.133333333333334, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=6, apply_aura=255, misc_value=15),
        Effect(type=31, base_points=199, implicit_target_a=6),
    ],
    spell_icon_id=2312,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All bleed effects cause $s2% additional damage.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Mangle the target for $s3% normal damage plus ${$m1*$m3/100} and causes the target to take $s2% additional damage from bleed effects for $d.  Awards $34071s1 combo $lpoint:points;.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_2': 1024, 'SpellClassSet': 7, 'SpellLevel': 50, 'SpellVisualID_1': 8634, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


mangle_bear_33878 = spell(
    id=33878,
    name='Mangle (Bear)',
    school=School.NORMAL,
    attributes=262160,
    category=971,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    power_type=PowerType.RAGE,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=74, points_per_level=6.166666666666667, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=6, apply_aura=255, misc_value=15),
        Effect(type=31, base_points=114, implicit_target_a=6),
    ],
    spell_icon_id=2312,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All bleed effects cause $s2% additional damage.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Mangle the target for $s3% normal damage plus ${$m1*$m3/100} and causes the target to take $s2% additional damage from bleed effects for $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 128, 'SpellClassMask_2': 64, 'SpellClassSet': 7, 'SpellLevel': 50, 'SpellVisualID_1': 6586, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


flight_form_33943 = spell(
    id=33943,
    name='Flight Form',
    school=School.NORMAL,
    attributes=268795920,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=13,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=29),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=201),
    ],
    spell_icon_id=2274,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 2 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 98304, 'AttributesEx4': 603979776, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Polymorph effects.\r\nMovement speed increased by $33948s2% and allows you to fly.', 'AuraInterruptFlags': 128, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shapeshift into flight form, increasing movement speed by $33948s2% and allowing you to fly.  Cannot use in combat.  Can only use this form in Outland or Northrend.\r\n\r\nThe act of shapeshifting frees the caster of Polymorph and Movement Impairing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 14, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 1073741826, 'SpellClassMask_2': 32768, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellVisualID_1': 8128, 'StanceBarOrder': 5, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


swift_flight_form_40120 = spell(
    id=40120,
    name='Swift Flight Form',
    school=School.NORMAL,
    attributes=268795920,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=13,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=27),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=201),
    ],
    spell_icon_id=2274,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by quest_template reward/display spell)',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 98304, 'AttributesEx4': 603979776, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Polymorph effects.\r\nMovement speed increased by $40121s2% and allows you to fly.', 'AuraInterruptFlags': 128, 'BaseLevel': 70, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shapeshift into swift flight form, increasing movement speed by $40121s2% and allowing you to fly.  Cannot use in combat.  Can only use this form in Outland or Northrend.\r\n\r\nThe act of shapeshifting frees the caster of Polymorph and Movement Impairing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 14, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Shapeshift', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 1073741826, 'SpellClassMask_2': 32768, 'SpellClassSet': 7, 'SpellLevel': 70, 'SpellVisualID_1': 8128, 'StanceBarOrder': 5, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


nourish_50464 = spell(
    id=50464,
    name='Nourish',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=1882, points_per_level=9.699999809265137, die_sides=305, implicit_target_a=21),
    ],
    spell_icon_id=2863,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 80, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for $s1. Heals for an additional 20% if you have a Rejuvenation, Regrowth, Lifebloom, or Wild Growth effect active on the target.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 0.671999990940094, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 85, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 1073741981, 'SpellClassMask_2': 33554432, 'SpellClassSet': 7, 'SpellLevel': 80, 'SpellVisualID_1': 11570, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


revive_50769 = spell(
    id=50769,
    name='Revive',
    school=School.NATURE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=72,
    range_yards=30.0,
    effects=[
        Effect(type=113, base_points=64, points_per_level=25.514705882352942, misc_value=120),
    ],
    spell_icon_id=2256,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 12); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Returns the spirit to the body, restoring a dead target to life with $s1 health and $q1 mana.  Cannot be cast when in combat.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 1073741824, 'SpellClassMask_3': 512, 'SpellClassSet': 7, 'SpellLevel': 12, 'SpellPriority': 50, 'SpellVisualID_1': 344, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 32768},
)


savage_roar_52610 = spell(
    id=52610,
    name='Savage Roar',
    school=School.NORMAL,
    dispel=9,
    mechanic=31,
    attributes=537133072,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=9000,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2865,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 4195328, 'AttributesEx2': 4, 'AttributesEx3': 1342439424, 'AttributesEx4': 16, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Physical damage done increased by $s2%.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 75, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that increases physical damage done by $s2%.  Only useable while in Cat Form.  Lasts longer per combo point:\r\n   1 point  : 14 seconds\r\n   2 points: 19 seconds\r\n   3 points: 24 seconds\r\n   4 points: 29 seconds\r\n   5 points: 34 seconds', 'DurationIndex': 581, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'SpellClassMask_2': 268435456, 'SpellClassSet': 7, 'SpellLevel': 75, 'SpellPriority': 50, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


swipe_cat_62078 = spell(
    id=62078,
    name='Swipe (Cat)',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=31, base_points=249, implicit_target_a=6, chain_targets=1000),
    ],
    spell_icon_id=1562,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 512, 'AttributesEx2': 4096, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 71, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Swipe nearby enemies, inflicting $s1% weapon damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_3': 1024, 'SpellClassSet': 7, 'SpellLevel': 71, 'SpellVisualID_1': 13170, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


insect_swarm_5570 = spell(
    id=5570,
    name='Insect Swarm',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=30.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=23, points_per_level=2.5, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=6, apply_aura=54),
    ],
    spell_icon_id=1771,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Chance to hit with melee and ranged attacks decreased by $s2% and $s1 Nature damage every $t1 sec.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The enemy target is swarmed by insects, decreasing their chance to hit by $s2% and causing $o1 Nature damage over $d.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 0.20000000298023224, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskC_1': 7340807, 'EffectSpellClassMaskC_2': 25166340, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 2, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 2097152, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellVisualID_1': 7333, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


wild_growth_48438 = spell(
    id=48438,
    name='Wild Growth',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=1237,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=23,
    range_yards=40.0,
    duration_ms=7000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=97, points_per_level=5.4, implicit_target_a=63, implicit_target_b=31, apply_aura=AuraType.PERIODIC_HEAL, amplitude=1000, radius_yards=15.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=87, implicit_target_b=31, apply_aura=AuraType.DUMMY, radius_yards=15.0),
    ],
    spell_icon_id=2864,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx4': 1048576, 'AttributesEx5': 4194304, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals $s1 damage every $t1 second.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals up to $s3 friendly party or raid members within $a1 yards of the target for $o1 over $d. The amount healed is applied quickly at first, and slows down as the Wild Growth reaches its full duration.', 'EffectBasePoints_3': 4, 'EffectBonusMultiplier_1': 0.11500000208616257, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_2': 67108864, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 11568, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


starfall_48505 = spell(
    id=48505,
    name='Starfall',
    school=School.ARCANE,
    attributes=65536,
    category=1218,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=90000,
    mana_cost=0,
    mana_cost_pct=35,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=starfall_50286.id),
    ],
    spell_icon_id=2854,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx4': 64, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Summoning stars from the sky.', 'AuraInterruptFlags': 131072, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You summon a flurry of stars from the sky on all targets within $50286a yards of the caster, each dealing $50288s1 Arcane damage. Also causes $50294s1 Arcane damage to all other enemies within $50294a1 yards of the enemy target. Maximum 20 stars. Lasts $48505d.  Shapeshifting into an animal form or mounting cancels the effect. Any effect which causes you to lose control of your character will suppress the starfall effect.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 0.12700000405311584, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 2, 'ShapeshiftMask': 1073741824, 'SpellClassMask_2': 8388608, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellVisualID_1': 11571, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


typhoon_50516 = spell(
    id=50516,
    name='Typhoon',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=1217,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=20000,
    mana_cost=0,
    mana_cost_pct=25,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=89, radius_yards=30.0),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=399, points_per_level=26.333333333333332, trigger_spell=typhoon_61391.id),
    ],
    spell_icon_id=2838,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 268435584, 'AttributesEx2': 524288, 'AttributesEx4': 1, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You summon a violent Typhoon that does $s2 Nature damage when in contact with hostile targets, knocking them back and dazing them for $61391d.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 2, 'ShapeshiftMask': 1073741824, 'Speed': 27.0, 'SpellClassMask_2': 16777216, 'SpellClassSet': 7, 'SpellLevel': 50, 'SpellMissileID': 1267, 'SpellVisualID_1': 9248, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)


nature_s_swiftness_17116 = spell(
    id=17116,
    name="Nature's Swiftness",
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
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=108, misc_value=10),
    ],
    spell_icon_id=112,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 196608, 'AttributesEx4': 64, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Nature spell will be an instant cast spell.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, your next Nature spell with a base casting time less than 10 sec. becomes an instant cast spell.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 268436065, 'EffectSpellClassMaskA_2': 33554464, 'EffectSpellClassMaskA_3': 32768, 'EquippedItemClass': -1, 'InterruptFlags': 4, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'ShapeshiftExclude': 1073741824, 'SpellClassMask_2': 524288, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 4040},
)


swiftmend_18562 = spell(
    id=18562,
    name='Swiftmend',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=15000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, implicit_target_a=21),
    ],
    spell_icon_id=1917,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Consumes a Rejuvenation or Regrowth effect on a friendly target to instantly heal them an amount equal to 12 sec. of Rejuvenation or 18 sec. of Regrowth.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 1073741824, 'ShapeshiftMask': 2, 'SpellClassMask_2': 2, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellVisualID_1': 3884, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetAuraState': 15},
)


moonkin_form_24858 = spell(
    id=24858,
    name='Moonkin Form',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=13,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=31),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=24907),
    ],
    spell_icon_id=111,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 98304, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Polymorph effects.\r\nArmor contribution from items is increased by $24905s1%.\r\nDamage taken while stunned reduced $69366s1%.\r\nSingle target spell criticals have a chance to instantly regenerate $53506s1% of your total mana.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shapeshift into Moonkin Form.  While in this form the armor contribution from items is increased by $24905s1%, damage taken while stunned is reduced by $69366s1%, and all party and raid members within $24907a1 yards have their spell critical chance increased by $24907s1%.  Single target spell critical strikes in this form have a chance to instantly regenerate $53506s1% of your total mana.  The Moonkin can not cast healing or resurrection spells while shapeshifted.\r\n\r\nThe act of shapeshifting frees the caster of Polymorph and Movement Impairing effects.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Shapeshift', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 2, 'SpellClassMask_2': 8192, 'SpellClassSet': 7, 'SpellLevel': 40, 'SpellVisualID_1': 9302, 'StanceBarOrder': 4, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


force_of_nature_33831 = spell(
    id=33831,
    name='Force of Nature',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=30.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=2, implicit_target_a=8, misc_value=1964),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=16, apply_aura=226, amplitude=200, radius_yards=2.0),
    ],
    spell_icon_id=2258,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268436480, 'AttributesEx2': 524288, 'AttributesEx3': 131072, 'AttributesEx6': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons $s1 treants to attack enemy targets for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1562, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 2, 'ShapeshiftMask': 1073741824, 'SpellClassMask_2': 512, 'SpellClassSet': 7, 'SpellLevel': 50, 'SpellVisualID_1': 8111, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)


berserk_50334 = spell(
    id=50334,
    name='Berserk',
    school=School.NORMAL,
    attributes=16,
    category=1208,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=180000,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-6001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=5),
    ],
    spell_icon_id=2852,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 163872, 'AttributesEx5': 131072, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Fear effects.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When activated, this ability causes your Mangle (Bear) ability to hit up to $58923s1 targets and have no cooldown, and reduces the energy cost of all your Cat Form abilities by $s1%.  Lasts $d.  You cannot use Tiger's Fury while Berserk is active. \r\n\r\nClears the effect of Fear and makes you immune to Fear for the duration.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8622080, 'EffectSpellClassMaskA_2': 805307520, 'EffectSpellClassMaskA_3': 263200, 'EffectSpellClassMaskB_2': 64, 'EffectSpellClassMaskC_2': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 64, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellVisualID_1': 11566, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


survival_instincts_61336 = spell(
    id=61336,
    name='Survival Instincts',
    school=School.NORMAL,
    attributes=16,
    category=1251,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=180000,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=14),
    ],
    spell_icon_id=3707,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Health increased by 30% of maximum while in Bear Form, Cat Form, or Dire Bear Form.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, this ability temporarily grants you $s1% of your maximum health for $d while in Bear Form, Cat Form, or Dire Bear Form.  After the effect expires, the health is lost.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8622080, 'EffectSpellClassMaskA_2': 805307520, 'EffectSpellClassMaskA_3': 32, 'EffectSpellClassMaskC_1': 2048, 'EffectSpellClassMaskC_2': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 128, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellVisualID_1': 2758},
)
