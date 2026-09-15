"""
Warrior - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/warrior.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .warrior_...` below) resolve.
"""

from lib.dsl import AuraType, Effect, EffectType, Mechanic, PowerType, School
from lib.dsl.registry import spell


shield_bash_72 = spell(
    id=72,
    name='Shield Bash',
    school=School.NORMAL,
    attributes=327696,
    category=88,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=12000,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.INTERRUPT_CAST, base_points=-1, mechanic=26, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=6, trigger_spell=29703),
    ],
    spell_icon_id=280,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 8, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Bash the target with your shield dazing them and interrupting spellcasting, which prevents any spell in that school from being cast for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 196608, 'SpellClassMask_1': 2048, 'SpellClassSet': 4, 'SpellLevel': 12, 'SpellPriority': 50, 'SpellVisualID_1': 42},
)


heroic_strike_78 = spell(
    id=78,
    name='Heroic Strike',
    school=School.NORMAL,
    attributes=327700,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=10, points_per_level=6.1265822784810124, implicit_target_a=6),
    ],
    spell_icon_id=856,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 13 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A strong attack that increases melee damage by $s1 and causes a high amount of threat.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 64, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 39},
)


charge_100 = spell(
    id=100,
    name='Charge',
    school=School.NORMAL,
    attributes=805634064,
    category=1219,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=15000,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=25.0,
    effects=[
        Effect(type=96, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, base_points=89, points_per_level=1.0714285714285714, implicit_target_a=1, radius_yards=0.0),
        Effect(type=EffectType.TRIGGER_SPELL, points_per_level=-0.017857142857142856, die_sides=0, implicit_target_a=6, trigger_spell=7922),
    ],
    spell_icon_id=457,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx6': 8388608, 'AttributesEx7': 262144, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 4, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Charge an enemy, generate $/10;s2 rage, and stun it for $7922d.  Cannot be used in combat.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectRadiusIndex_2': 36, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 65219, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 95, 'ShapeshiftMask': 65536, 'SpellClassMask_1': 1, 'SpellClassSet': 4, 'SpellLevel': 4, 'SpellPriority': 50, 'SpellVisualID_1': 867, 'StartRecoveryCategory': 1178},
)


commanding_shout_469 = spell(
    id=469,
    name='Commanding Shout',
    school=School.NORMAL,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1079, points_per_level=97.91666666666667, implicit_target_a=56, apply_aura=230, radius_yards=30.0),
    ],
    spell_icon_id=1934,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 68); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 3 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Maximum health increased by $s1.', 'BaseLevel': 68, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases maximum health of all party and raid members within $a1 yards by $s1.  Lasts $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 128, 'SpellClassSet': 4, 'SpellLevel': 68, 'SpellVisualID_1': 246, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


disarm_676 = spell(
    id=676,
    name='Disarm',
    school=School.NORMAL,
    mechanic=3,
    attributes=327696,
    category=109,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_DISARM),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=278),
    ],
    spell_icon_id=560,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx4': 536872960, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Disarmed!', 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Disarm the enemy's main hand and ranged weapons for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 131072, 'SpellClassMask_1': 512, 'SpellClassSet': 4, 'SpellLevel': 18, 'SpellPriority': 50, 'SpellVisualID_1': 398, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mocking_blow_694 = spell(
    id=694,
    name='Mocking Blow',
    school=School.NORMAL,
    attributes=327696,
    category=40,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=6000,
    effects=[
        Effect(type=121, base_points=-1, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_TAUNT),
        Effect(type=114, base_points=-1, implicit_target_a=6),
    ],
    spell_icon_id=1477,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AttributesEx4': 2048, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunted.', 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A mocking attack that causes a moderate amount of threat and forces the target to focus attacks on you for $d.  If the target is tauntable, also deals weapon damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 196608, 'SpellClassMask_1': 134217728, 'SpellClassSet': 4, 'SpellLevel': 16, 'SpellVisualID_1': 39, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rend_772 = spell(
    id=772,
    name='Rend',
    school=School.NORMAL,
    mechanic=15,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, points_per_level=0.9342105263157895, mechanic=15, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    spell_icon_id=245,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Bleeding for $s1 plus a percentage of weapon damage every $t1 seconds.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Wounds the target causing them to bleed for $o1 damage plus an additional ${0.2*5*(($MWB+$mwb)/2+$AP/14*$MWS)} (based on weapon damage) over $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 196608, 'SpellClassMask_1': 32, 'SpellClassSet': 4, 'SpellLevel': 4, 'SpellVisualID_1': 372, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


cleave_845 = spell(
    id=845,
    name='Cleave',
    school=School.NORMAL,
    attributes=327700,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=14, points_per_level=3.45, implicit_target_a=6, chain_targets=2),
    ],
    spell_icon_id=277,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AttributesEx2': 4096, 'AttributesEx3': 1024, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A sweeping attack that does your weapon damage plus $s1 to the target and his $?s58366[two nearest allies][nearest ally].', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 4194304, 'SpellClassSet': 4, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 219},
)


shield_wall_871 = spell(
    id=871,
    name='Shield Wall',
    school=School.NORMAL,
    attributes=327696,
    category=132,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=12000,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-61, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=281,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All damage taken reduced by $s1%.', 'BaseLevel': 28, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1% for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 131072, 'SpellClassMask_1': 8192, 'SpellClassSet': 4, 'SpellLevel': 28, 'SpellPriority': 50, 'SpellVisualID_1': 345},
)


demoralizing_shout_1160 = spell(
    id=1160,
    name='Demoralizing Shout',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-36, points_per_level=-5.696969696969697, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_ATTACK_POWER, radius_yards=10.0),
    ],
    spell_icon_id=282,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 14); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces melee attack power by $s1.', 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the melee attack power of all enemies within $a1 yards by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 131072, 'SpellClassSet': 4, 'SpellLevel': 14, 'SpellVisualID_1': 210, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


challenging_shout_1161 = spell(
    id=1161,
    name='Challenging Shout',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_TAUNT, radius_yards=10.0),
    ],
    spell_icon_id=50,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 67108864, 'AttributesEx4': 2048, 'AttributesEx5': 2147483648, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunted.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Forces all enemies within $a1 yards to focus attacks on you for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 524288, 'SpellClassSet': 4, 'SpellLevel': 26, 'SpellVisualID_1': 209, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


slam_1464 = spell(
    id=1464,
    name='Slam',
    school=School.NORMAL,
    attributes=2425104,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=31, points_per_level=4.36, implicit_target_a=6),
    ],
    spell_icon_id=559,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 131072, 'AttributesEx3': 197632, 'AttributesEx6': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 16, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Slams the opponent, causing weapon damage plus $s1.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'InterruptFlags': 13, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 2097152, 'SpellClassSet': 4, 'SpellLevel': 30, 'SpellVisualID_1': 1165, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


whirlwind_1680 = spell(
    id=1680,
    name='Whirlwind',
    school=School.NORMAL,
    attributes=327696,
    category=891,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.RAGE,
    mana_cost=250,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=121, base_points=-1, implicit_target_a=22, implicit_target_b=15, radius_yards=8.0),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=22, trigger_spell=44949),
    ],
    spell_icon_id=83,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 16, 'AttributesEx3': 1024, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 36, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'In a whirlwind of steel you attack up to $i enemies within $a1 yards, causing weapon damage from both melee weapons to each enemy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'MaxTargets': 4, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 1, 'ShapeshiftMask': 262144, 'SpellClassMask_2': 4, 'SpellClassSet': 4, 'SpellLevel': 36, 'SpellVisualID_1': 223, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hamstring_1715 = spell(
    id=1715,
    name='Hamstring',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=23,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1032, 'AttributesEx6': 10485760, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement slowed by $s1%.', 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Maims the enemy, reducing movement speed by $s1% for $d$?s58372[, and has a $58372h% chance to immobilize the target for $58373d.][.]', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 327680, 'SpellClassMask_1': 2, 'SpellClassSet': 4, 'SpellLevel': 8, 'SpellPriority': 50, 'SpellVisualID_1': 556, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


recklessness_1719 = spell(
    id=1719,
    name='Recklessness',
    school=School.NORMAL,
    dispel=9,
    mechanic=31,
    attributes=327696,
    category=132,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=12000,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=5),
    ],
    spell_icon_id=138,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Special ability attacks have an additional $s1% chance to critically hit but all damage taken is increased by $s2%.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next $n special ability attacks have an additional $s1% to critically hit but all damage taken is increased by $s2%.  Lasts $d.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 778044484, 'EffectSpellClassMaskA_2': 4212549, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcCharges': 3, 'ProcTypeMask': 4368, 'RangeIndex': 1, 'ShapeshiftMask': 262144, 'SpellClassMask_1': 16, 'SpellClassSet': 4, 'SpellLevel': 50, 'SpellVisualID_1': 236, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shield_block_2565 = spell(
    id=2565,
    name='Shield Block',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=51),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=150),
    ],
    spell_icon_id=28,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 2, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Block chance and block value increased by $s1%.', 'BaseLevel': 16, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to block and block value by $s1% for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_2': 512, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 131072, 'SpellClassMask_1': 4096, 'SpellClassSet': 4, 'SpellLevel': 16, 'SpellVisualID_1': 3442},
)


bloodrage_2687 = spell(
    id=2687,
    name='Bloodrage',
    school=School.NORMAL,
    dispel=9,
    mechanic=31,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.HEALTH,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=199, implicit_target_a=1, misc_value=1),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=2, implicit_target_a=1, trigger_spell=29131),
    ],
    spell_icon_id=86,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Generates $/10;2687s1 rage at the cost of health, and then generates an additional $?s12296[${$29131m1*$29131d/10+$m2}][$/10;29131o1] rage over $29131d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 256, 'SpellClassSet': 4, 'SpellLevel': 10},
)


intervene_3411 = spell(
    id=3411,
    name='Intervene',
    school=School.NORMAL,
    attributes=536870928,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=25.0,
    duration_ms=10000,
    effects=[
        Effect(type=96, base_points=-1, implicit_target_a=57),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=57, apply_aura=111, radius_yards=10.0),
    ],
    spell_icon_id=2205,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 2048, 'AttributesEx6': 67108864, 'AttributesEx7': 262144, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'The next melee or ranged attack made against you will be made against the intervening warrior instead.', 'BaseLevel': 70, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Run at high speed towards a party member, intercepting the next melee or ranged attack made against them as well as reducing their total threat by $59667s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 65219, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 680, 'RangeIndex': 95, 'ShapeshiftMask': 131072, 'SpellClassMask_2': 65536, 'SpellClassSet': 4, 'SpellLevel': 70, 'SpellVisualID_1': 9107},
)


intimidating_shout_5246 = spell(
    id=5246,
    name='Intimidating Shout',
    school=School.NORMAL,
    mechanic=Mechanic.FEAR,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=250,
    mana_cost_pct=0,
    range_yards=8.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=20511),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_FEAR, radius_yards=8.0),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_INCREASE_SPEED, radius_yards=8.0),
    ],
    spell_icon_id=148,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 136, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Intimidated.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 22, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The warrior shouts, causing up to $5246i enemies within $5246a2 yards to cower in fear.  The targeted enemy will be unable to move while cowering.  Lasts $5246d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxTargets': 5, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'SpellClassMask_1': 262144, 'SpellClassSet': 4, 'SpellLevel': 22, 'SpellPriority': 50, 'SpellVisualID_1': 247, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


execute_5308 = spell(
    id=5308,
    name='Execute',
    school=School.NORMAL,
    attributes=327952,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=92, points_per_level=24.339285714285715, implicit_target_a=6),
    ],
    spell_icon_id=1648,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 24); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AttributesEx4': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 24, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Attempt to finish off a wounded foe, causing ${$m1+$AP*0.2} damage and converting each extra point of rage into $*10;F1 additional damage (up to a maximum cost of 30 rage).  Only usable on enemies that have less than 20% health.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 0.30000001192092896, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 2, 'ShapeshiftMask': 327680, 'SpellClassMask_1': 536870912, 'SpellClassSet': 4, 'SpellLevel': 24, 'SpellPriority': 50, 'SpellVisualID_1': 250, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetAuraState': 2},
)


thunder_clap_6343 = spell(
    id=6343,
    name='Thunder Clap',
    school=School.NORMAL,
    attributes=327696,
    category=49,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    power_type=PowerType.RAGE,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=14, points_per_level=3.8513513513513513, implicit_target_a=22, implicit_target_b=15, radius_yards=8.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, mechanic=8, implicit_target_a=22, implicit_target_b=15, apply_aura=138, radius_yards=8.0),
    ],
    spell_icon_id=199,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 6); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Time between attacks increased by $s2%.', 'BaseLevel': 6, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blasts nearby enemies increasing the time between their attacks by $s2% for $d and doing $s1 damage to them.  Damage increased by attack power.  This ability causes additional threat.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'RangeIndex': 1, 'ShapeshiftMask': 196608, 'SpellClassMask_1': 128, 'SpellClassSet': 4, 'SpellLevel': 6, 'SpellVisualID_1': 145, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


pummel_6552 = spell(
    id=6552,
    name='Pummel',
    school=School.NORMAL,
    attributes=327696,
    category=88,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.INTERRUPT_CAST, die_sides=0, mechanic=26, implicit_target_a=6),
    ],
    spell_icon_id=756,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 8, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 38, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Pummel the target, interrupting spellcasting and preventing any spell in that school from being cast for $d.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 262144, 'SpellClassMask_1': 8, 'SpellClassSet': 4, 'SpellLevel': 38, 'SpellVisualID_1': 1023},
)


revenge_6572 = spell(
    id=6572,
    name='Revenge',
    school=School.NORMAL,
    attributes=327696,
    category=65,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=3000,
    power_type=PowerType.RAGE,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=98, points_per_level=23.28787878787879, die_sides=23, implicit_target_a=6),
    ],
    spell_icon_id=562,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 14); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AttributesEx4': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 14, 'CasterAuraState': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly counterattack an enemy for ${$m1+$AP*0.310} to ${$M1+$AP*0.310} damage.   Revenge is only usable after the warrior blocks, dodges or parries an attack.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 131072, 'SpellClassMask_1': 1024, 'SpellClassSet': 4, 'SpellLevel': 14, 'SpellPriority': 50, 'SpellVisualID_1': 342, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


battle_shout_6673 = spell(
    id=6673,
    name='Battle Shout',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, points_per_level=6.772151898734177, implicit_target_a=56, apply_aura=AuraType.MOD_ATTACK_POWER, radius_yards=30.0),
        Effect(type=EffectType.APPLY_AURA, base_points=14, points_per_level=6.772151898734177, implicit_target_a=56, apply_aura=124, radius_yards=30.0),
    ],
    spell_icon_id=456,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases your attack power by $s1.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The warrior shouts, increasing attack power of all raid and party members within $a1 yards by $s1.  Lasts $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 246, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


overpower_7384 = spell(
    id=7384,
    name='Overpower',
    school=School.NORMAL,
    attributes=2424848,
    category=65,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=5000,
    power_type=PowerType.RAGE,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=1,
    effects=[
        Effect(type=121, base_points=-1, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=26,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1477444096, 'AttributesEx3': 1024, 'AttributesEx4': 512, 'AttributesEx6': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly overpower the enemy, causing weapon damage.  Only useable after the target dodges.  The Overpower cannot be blocked, dodged or parried.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 65536, 'SpellClassMask_1': 4, 'SpellClassSet': 4, 'SpellLevel': 12, 'SpellVisualID_1': 39, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


pummel_13491 = spell(
    id=13491,
    name='Pummel',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.INTERRUPT_CAST, points_per_level=0.5540540540540541, die_sides=0, mechanic=26, implicit_target_a=6),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=3, points_per_level=-0.04054054054054054, implicit_target_a=6),
    ],
    spell_icon_id=756,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 6); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 3 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 6, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Pummel the target for $s2 damage and interrupt the spell being cast for $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 65536, 'SpellClassSet': 4, 'SpellLevel': 6, 'SpellVisualID_1': 1023, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


berserker_rage_18499 = spell(
    id=18499,
    name='Berserker Rage',
    school=School.NORMAL,
    dispel=9,
    mechanic=31,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=30),
    ],
    spell_icon_id=1465,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 32768, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Fear, Sap and Incapacitate effects.  Generating extra rage when taking damage.', 'BaseLevel': 32, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The warrior enters a berserker rage, removing and granting immunity to Fear, Sap and Incapacitate effects and generating extra rage when taking damage.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 139944, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 4, 'SpellLevel': 32, 'SpellVisualID_1': 47, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


retaliation_20230 = spell(
    id=20230,
    name='Retaliation',
    school=School.NORMAL,
    attributes=327696,
    category=132,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=12000,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=278,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 512, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Counterattacking all melee attacks.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly counterattack any enemy that strikes you in melee for $20230d.  Melee attacks made from behind cannot be counterattacked.  A maximum of $20230n attacks will cause retaliation.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcCharges': 20, 'ProcTypeMask': 40, 'RangeIndex': 1, 'ShapeshiftMask': 65536, 'SpellClassMask_2': 8, 'SpellClassSet': 4, 'SpellLevel': 20, 'SpellVisualID_1': 7395, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


intercept_20252 = spell(
    id=20252,
    name='Intercept',
    school=School.NORMAL,
    attributes=537198608,
    category=1158,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=25.0,
    effects=[
        Effect(type=96, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=20253),
    ],
    spell_icon_id=516,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx6': 8388608, 'AttributesEx7': 262144, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Charge an enemy, causing ${$AP*0.12} damage (based on attack power) and stunning it for $20253d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 65219, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 95, 'ShapeshiftMask': 262144, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 4, 'SpellLevel': 30, 'SpellVisualID_1': 29},
)


spell_reflection_23920 = spell(
    id=23920,
    name='Spell Reflection',
    school=School.NORMAL,
    attributes=134545424,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=28),
    ],
    spell_icon_id=1935,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108866, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reflects the next spell cast on you.', 'BaseLevel': 64, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Raise your shield, reflecting the next spell cast on you.  Lasts $d.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 139936, 'RangeIndex': 1, 'ShapeshiftMask': 196608, 'SpellClassMask_2': 2, 'SpellClassSet': 4, 'SpellLevel': 64, 'SpellVisualID_1': 7962},
)


shield_slam_23922 = spell(
    id=23922,
    name='Shield Slam',
    school=School.NORMAL,
    attributes=327696,
    category=1209,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    power_type=PowerType.RAGE,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=6, misc_value=1),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=293, points_per_level=17.4, die_sides=15, implicit_target_a=6),
    ],
    spell_icon_id=413,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Slam the target with your shield, causing $s2 damage, modified by your shield block value, and dispels $s1 magic effect on the target.  Also causes a high amount of threat.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 512, 'SpellClassSet': 4, 'SpellLevel': 40, 'SpellVisualID_1': 42, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


heroic_strike_25286 = spell(
    id=25286,
    name='Heroic Strike',
    school=School.NORMAL,
    attributes=327700,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=200, implicit_target_a=6),
    ],
    spell_icon_id=856,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A strong attack that increases melee damage by $s1 and causes a high amount of threat.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 64, 'SpellClassSet': 4, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 39},
)


revenge_25288 = spell(
    id=25288,
    name='Revenge',
    school=School.NORMAL,
    attributes=327696,
    category=65,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=5000,
    power_type=PowerType.RAGE,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=722, die_sides=161, implicit_target_a=6),
    ],
    spell_icon_id=562,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AttributesEx4': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CasterAuraState': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly counterattack an enemy for ${$m1+$AP*0.310} to ${$M1+$AP*0.310} damage.   Revenge is only usable after the warrior blocks, dodges or parries an attack.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 131072, 'SpellClassMask_1': 1024, 'SpellClassSet': 4, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 342, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


battle_shout_25289 = spell(
    id=25289,
    name='Battle Shout',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=231, points_per_level=1.0, implicit_target_a=56, apply_aura=AuraType.MOD_ATTACK_POWER, radius_yards=30.0),
        Effect(type=EffectType.APPLY_AURA, base_points=231, points_per_level=1.0, implicit_target_a=56, apply_aura=124, radius_yards=30.0),
    ],
    spell_icon_id=456,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases your attack power by $s1.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The warrior shouts, increasing attack power of all raid and party members within $a1 yards by $s1.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 68, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 4, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 246, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


cleave_30213 = spell(
    id=30213,
    name='Cleave',
    school=School.NORMAL,
    attributes=327696,
    category=40,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=31, points_per_level=3.066666666666667, implicit_target_a=6, chain_targets=2),
    ],
    spell_icon_id=277,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AttributesEx2': 4096, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "A sweeping attack that does the Felguard's weapon damage plus $s1 to the target and his nearest ally.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 4194304, 'SpellClassSet': 4, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 219, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


enraged_regeneration_55694 = spell(
    id=55694,
    name='Enraged Regeneration',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=20, amplitude=1000),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=31),
    ],
    spell_icon_id=2008,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 98304, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Regenerates $s1% of your total health every $t1 sec.', 'BaseLevel': 75, 'CasterAuraState': 17, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You regenerate $o1% of your total health over $d.  This ability requires an Enrage effect, consumes all Enrage effects and prevents any from affecting you for the full duration.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 131072, 'SpellClassSet': 4, 'SpellLevel': 75, 'SpellPriority': 50, 'SpellVisualID_1': 12582, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


heroic_throw_57755 = spell(
    id=57755,
    name='Heroic Throw',
    school=School.NORMAL,
    attributes=2424848,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=11, implicit_target_a=6),
    ],
    spell_icon_id=3182,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 512, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Throws your weapon at the enemy causing ${$m1+$AP*.50} damage (based on attack power).  This ability causes high threat.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'Speed': 50.0, 'SpellClassMask_2': 1, 'SpellClassSet': 4, 'SpellLevel': 80, 'SpellVisualID_1': 13222, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shattering_throw_64382 = spell(
    id=64382,
    name='Shattering Throw',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=1500,
    cooldown_ms=300000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=250,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=11, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=6, apply_aura=101, misc_value=1),
    ],
    spell_icon_id=3998,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 512, 'AttributesEx3': 1024, 'AttributesEx7': 25165824, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Armor reduced by $s2%.', 'BaseLevel': 71, 'CastingTimeIndex': 16, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Throws your weapon at the enemy causing ${$64382m1+$AP*.50} damage (based on attack power), reducing the armor on the target by $64382s2% for $64382d or removing any invulnerabilities.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'InterruptFlags': 9, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ShapeshiftMask': 65536, 'Speed': 50.0, 'SpellClassMask_2': 4194304, 'SpellClassSet': 4, 'SpellLevel': 71, 'SpellVisualID_1': 13222, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mortal_strike_12294 = spell(
    id=12294,
    name='Mortal Strike',
    school=School.NORMAL,
    attributes=327696,
    category=971,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    power_type=PowerType.RAGE,
    mana_cost=300,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=6, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
        Effect(type=121, base_points=84, points_per_level=7.375, implicit_target_a=6),
    ],
    spell_icon_id=564,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Healing effects reduced by $s1%.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A vicious strike that deals weapon damage plus $s2 and wounds the target, reducing the effectiveness of any healing by $s1% for $d.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 2, 'SpellClassMask_1': 33554432, 'SpellClassSet': 4, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 39, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


devastate_20243 = spell(
    id=20243,
    name='Devastate',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        None,
        Effect(type=31, base_points=119, implicit_target_a=6),
        Effect(type=121, base_points=57, points_per_level=6.133333333333334, implicit_target_a=6),
    ],
    spell_icon_id=1508,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Armor decreased by $s1.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'CumulativeAura': 5, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Sunder the target's armor causing the Sunder Armor effect.  In addition, causes $s2% of weapon damage plus $s3 for each application of Sunder Armor on the target.  The Sunder Armor effect can stack up to $u times.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'FacingCasterFlags': 1, 'ImplicitTargetA_1': 6, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 64, 'SpellClassSet': 4, 'SpellLevel': 50, 'SpellVisualID_1': 12295, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


death_wish_12292 = spell(
    id=12292,
    name='Death Wish',
    school=School.NORMAL,
    dispel=9,
    mechanic=31,
    attributes=134479888,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=79, misc_value=1),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=169,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 98304, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases physical damage by $s1%.  Increases all damage taken by $s3%.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated you become enraged, increasing your physical damage by $s1% but increasing all damage taken by $s3%.  Lasts $d.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 1048576, 'SpellClassSet': 4, 'SpellLevel': 30, 'SpellPriority': 50, 'SpellVisualID_1': 4599, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


piercing_howl_12323 = spell(
    id=12323,
    name='Piercing Howl',
    school=School.NORMAL,
    mechanic=Mechanic.SNARE,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_DECREASE_SPEED, radius_yards=10.0),
    ],
    spell_icon_id=134,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Dazed.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes all enemies within $a1 yards to be Dazed, reducing movement speed by $s1% for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 32, 'SpellClassSet': 4, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 2677, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


sweeping_strikes_12328 = spell(
    id=12328,
    name='Sweeping Strikes',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=300,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=515,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next $n melee attacks strike an additional nearby opponent.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next $n melee attacks strike an additional nearby opponent.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcCharges': 5, 'ProcTypeMask': 20, 'RangeIndex': 1, 'ShapeshiftMask': 327680, 'SpellClassMask_2': 1048576, 'SpellClassSet': 4, 'SpellLevel': 30, 'SpellPriority': 50, 'SpellVisualID_1': 211},
)


concussion_blow_12809 = spell(
    id=12809,
    name='Concussion Blow',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.STUN, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
        Effect(type=EffectType.SCHOOL_DAMAGE, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, base_points=37, implicit_target_a=6),
    ],
    spell_icon_id=25,
    notes='Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Concussion Blow (12809) - was left as an untouched "pulled from existing data" reference copy',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Stuns the opponent for $d and deals ${$m3/100*$AP} damage (based on attack power). Targets that cannot be stunned are instead Concussed, dealing 15% reduced damage for 10 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 67108864, 'SpellClassSet': 4, 'SpellLevel': 30, 'SpellVisualID_1': 2719, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


last_stand_12975 = spell(
    id=12975,
    name='Last Stand',
    school=School.NORMAL,
    attributes=262160,
    category=1251,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=180000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=29, implicit_target_a=1),
    ],
    spell_icon_id=177,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, this ability temporarily grants you $s1% of your maximum health for $12976d.  After the effect expires, the health is lost.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 524288, 'SpellClassSet': 4, 'SpellLevel': 20, 'SpellPriority': 50},
)


bloodthirst_23881 = spell(
    id=23881,
    name='Bloodthirst',
    school=School.NORMAL,
    attributes=327696,
    category=971,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=4000,
    power_type=PowerType.RAGE,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=49, implicit_target_a=6),
        Effect(type=EffectType.DUMMY),
    ],
    spell_icon_id=38,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly attack the target causing ${$AP*$m1/100} damage.  In addition, the next $23885n successful melee attacks will restore $m2% of max health.  This effect lasts $23885d.  Damage is based on your attack power.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 1024, 'SpellClassSet': 4, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 372, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


bladestorm_46924 = spell(
    id=46924,
    name='Bladestorm',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=90000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=250,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=50622),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=147, misc_value=1733),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=263),
    ],
    spell_icon_id=2782,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 32784, 'AttributesEx3': 1024, 'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'You cannot be stopped and perform a Whirlwind every $t1 sec.  No other abilities can be used.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly Whirlwind up to $50622i nearby targets and for the next $d you will perform a whirlwind attack every $t1 sec.  While under the effects of Bladestorm, you can move but cannot perform any other abilities but you do not feel pity or remorse or fear and you cannot be stopped unless killed.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_2': 4, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 16384, 'SpellClassSet': 4, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 10704, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shockwave_46968 = spell(
    id=46968,
    name='Shockwave',
    school=School.NORMAL,
    attributes=327696,
    category=1201,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=20000,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.STUN, implicit_target_a=104, apply_aura=AuraType.MOD_STUN, radius_yards=10.0),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=-1, implicit_target_a=104, radius_yards=10.0),
        Effect(type=EffectType.DUMMY, base_points=74),
    ],
    spell_icon_id=2777,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Sends a wave of force in front of the warrior, causing ${$m3/100*$AP} damage (based on attack power) and stunning all enemy targets within $a1 yards in a frontal cone for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 32768, 'SpellClassSet': 4, 'SpellLevel': 60, 'SpellVisualID_1': 10703, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
