"""
Auto-converted from source/spells/warrior*.csv + source/talents/warrior.yaml by csv_to_dsl.py
(.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md's Phase 4) - not yet hand-cleaned. See csv_to_dsl.py's docstring for what "mechanical, not hand-authored-quality" means here.
"""

from lib.dsl import AuraType, Effect, EffectType, Mechanic, PowerType, School
from lib.dsl.registry import spell
from lib.dsl.registry import granted_by_talent, tab

# --- spells trained outright (source/spells/warrior.csv) ---

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

defiance_12303 = spell(
    id=12303,
    name='Defiance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, points_per_level=0.1694915254237288, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=1, points_per_level=0.06779661016949153, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=561,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the threat generated by your attacks by $s1% while in Defensive Stance and increases your expertise by $s2.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 4096, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 131072, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_inner_rage_12325 = spell(
    id=12325,
    name='Improved Inner Rage',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-40001, points_per_level=-1355.9322033898304, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=561,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Inner Rage ability by $/1000;s1 secs.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 1048576, 'EffectSpellClassMaskA_1': 1048576, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_challenging_shout_12327 = spell(
    id=12327,
    name='Improved Challenging Shout',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-120001, points_per_level=-1016.9491525423729, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=278,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Challenging Shout ability by $/60000;s1 mins.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 524288, 'EffectSpellClassMaskA_1': 524288, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

stance_mastery_12678 = spell(
    id=12678,
    name='Stance Mastery',
    school=School.NORMAL,
    attributes=80,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=139,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You retain up to $s1 of your rage points when you change stances.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Passive', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 20, 'SpellPriority': 50},
)

flurry_12966 = spell(
    id=12966,
    name='Flurry',
    school=School.NORMAL,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, points_per_level=0.3389830508474576, implicit_target_a=1, apply_aura=138),
    ],
    spell_icon_id=108,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attack speed increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your attack speed by $12966s1% for your next 3 swings after dealing a melee critical strike.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcCharges': 3, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 12379},
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

improved_intimidating_shout_19870 = spell(
    id=19870,
    name='Improved Intimidating Shout',
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
        Effect(type=EffectType.APPLY_AURA, base_points=999, points_per_level=16.666666666666668, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=148,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Intimidating Shout by $/1000;s1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 262144, 'EffectSpellClassMaskA_1': 262144, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
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

defensive_tactics_29559 = spell(
    id=29559,
    name='Defensive Tactics',
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
        Effect(type=EffectType.APPLY_AURA, base_points=32, points_per_level=1.1355932203389831, implicit_target_a=1, apply_aura=112, misc_value=831),
    ],
    spell_icon_id=291,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You retain up to $s1% of your rage when you change from Defensive Stance to any other stance.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8388608, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

second_wind_29841 = spell(
    id=29841,
    name='Second Wind',
    school=School.NORMAL,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, points_per_level=0.3389830508474576, implicit_target_a=1, apply_aura=AuraType.PERIODIC_ENERGIZE, amplitude=2000, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, points_per_level=0.01694915254237288, implicit_target_a=1, apply_aura=20, amplitude=2000),
    ],
    spell_icon_id=1697,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Generates $/10;s1 rage and heals $s2% of your total health every $t1 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you are struck by a Stun or Immobilize effect you will generate $/10;29841o1 rage and $29841o2% of your total health over $29841d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8208, 'EffectSpellClassMaskA_2': 8, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
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

victory_rush_34428 = spell(
    id=34428,
    name='Victory Rush',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=44, implicit_target_a=6),
    ],
    spell_icon_id=2053,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx4': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 6, 'CasterAuraState': 10, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly attack the target causing ${$AP*$m1/100} damage.  Can only be used within $32216d after you kill an enemy that yields experience or honor.  Damage is based on your attack power.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 327680, 'SpellClassMask_2': 256, 'SpellClassSet': 4, 'SpellLevel': 6, 'SpellPriority': 50, 'SpellVisualID_1': 372, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
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

storm_s_bulwark_200028 = spell(
    id=200028,
    name="Storm's Bulwark",
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=1941,
    notes="New for the Protection Warrior rework (docs/prot_warrior_rework.md, New Spells/Auras: Storm's Bulwark). Absorbs damage of any school (misc_value 127 = all schools, SPELL_AURA_SCHOOL_ABSORB). Multiple sources stack additively into one pool capped at 50% of max HP and refresh the 15s duration via the GrantStormsBulwark() helper in spell_warrior.cpp; base_points is always 0 here since the real amount is supplied per-cast as custom basepoints. Self-cast only (implicit_target_a 1), so the null range_yards is safe (see docs/dbc-build-pipeline.md's range_yards gotcha for non-self casts). Which talents grant it (Incite, Reprisal, the Storm's Bulwark talent, Shockwave) and their mastery scaling are phase 2/3 work; this spell is only the shared absorb pool they all feed.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Absorbs damage.', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Absorbs damage. All sources of Storm's Bulwark stack and refresh the duration. You can have up to 50% of your maximum health in Storm's Bulwark.", 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 4, 'SpellPriority': 50, 'StartRecoveryCategory': 133},
)

concussed_200029 = spell(
    id=200029,
    name='Concussed',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    range_yards=5.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-15, implicit_target_a=6, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=2112,
    notes='New for the Protection Warrior rework (docs/prot_warrior_rework.md, New Spells/Auras: Concussed). Target deals 15% reduced damage of all types (misc_value 127 = all schools, SPELL_AURA_MOD_DAMAGE_PERCENT_DONE) for 10s. range_yards set explicitly to 5.0 (melee range) since this is cast on an enemy target - leaving it null maps to RangeIndex 0, which is not unlimited and silently fails non-self casts (see docs/dbc-build-pipeline.md). Applied by Concussion Blow (Row 5 talent) to targets that cannot be stunned; wiring that branch into spell_warr_concussion_blow is phase 3 work - this spell is just the debuff itself.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Deals 15% reduced damage of all types.', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals 15% reduced damage of all types for $d.', 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 4, 'SpellPriority': 50, 'StartRecoveryCategory': 133},
)

bloodstorm_200030 = spell(
    id=200030,
    name='Bloodstorm',
    school=School.NORMAL,
    mechanic=15,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    range_yards=10.0,
    duration_ms=9000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, mechanic=15, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    spell_icon_id=2774,
    notes="New for the Protection Warrior rework (docs/prot_warrior_rework.md, New Spells/Auras: Bloodstorm). Bleed DoT dealing 15/30% of Thunder Clap's damage over 9s, ticking every 3s (matches Rend's tick cadence). base_points is always 0 here since the real per-tick amount is supplied per-cast as custom basepoints once the total is split across ticks. A separate effect from Rend (distinct spell id, no CumulativeAura) and stacks alongside it; not applied or refreshed by the Thunderstruck echo. range_yards set explicitly to 10.0 (covers Thunder Clap's own 8yd radius) since this is cast on an enemy target - leaving it null maps to RangeIndex 0, which silently fails non-self casts (see docs/dbc-build-pipeline.md). Applying it from Thunder Clap when Blood and Thunder is talented, and excluding the Thunderstruck echo cast, is phase 3 work - this spell is just the DoT itself.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': "Bleeding for a percentage of Thunder Clap's damage.", 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Bleeding for a percentage of Thunder Clap's damage over $d.", 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 4, 'SpellPriority': 50, 'StartRecoveryCategory': 133},
)


# --- spells granted by a talent point (source/spells/warrior_talents.csv) ---

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

improved_heroic_strike_12282 = spell(
    id=12282,
    name='Improved Heroic Strike',
    school=School.NORMAL,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=856,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cost of your Heroic Strike ability by $/10;s1 rage point.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_charge_12285 = spell(
    id=12285,
    name='Improved Charge',
    school=School.NORMAL,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=457,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount of rage generated by your Charge ability by $/10;s1.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_rend_12286 = spell(
    id=12286,
    name='Improved Rend',
    school=School.NORMAL,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=3),
    ],
    spell_icon_id=245,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the bleed damage done by your Rend ability by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_thunder_clap_12287 = spell(
    id=12287,
    name='Improved Thunder Clap',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=42,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Improved Thunder Clap rank 1 - dropped slow-% effect, rage cost/damage already correct',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cost of your Thunder Clap ability by 1 rage point and increases its damage by 10%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 128, 'EffectSpellClassMaskB_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_hamstring_12289 = spell(
    id=12289,
    name='Improved Hamstring',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=23694),
    ],
    spell_icon_id=23,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Hamstring ability a $h% chance to immobilize the target for $23694d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 5, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_overpower_12290 = spell(
    id=12290,
    name='Improved Overpower',
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
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=1464,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Overpower ability by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 4, 'EffectSpellClassMaskA_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
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

tactical_mastery_12295 = spell(
    id=12295,
    name='Tactical Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=20, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=20, implicit_target_a=1, apply_aura=108, misc_value=2),
    ],
    spell_icon_id=139,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You retain up to an additional $s1 of your rage points when you change stances.  Also greatly increases the threat generated by your Bloodthirst and Mortal Strike abilities when you are in Defensive Stance.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 512, 'EffectSpellClassMaskB_1': 33554432, 'EffectSpellClassMaskC_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 131072, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_bloodrage_12301 = spell(
    id=12301,
    name='Improved Bloodrage',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=1),
    ],
    spell_icon_id=86,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Improved Bloodrage rank 1 - added Def-Stance dmg reduction',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the rage generated by your Bloodrage ability by 25%. While in Defensive Stance, reduces damage taken by 2%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 131072, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

puncture_12308 = spell(
    id=12308,
    name='Puncture',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=280),
    ],
    spell_icon_id=565,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Puncture rank - rage cost unchanged, retargeted to Devastate only, added armor-pen. Fixed 2026-09-04: EffectSpellClassMaskA_1 (dword 1) never matched Devastate, whose own SpellClassMask lives in dword 2 (SpellClassMask_2=64, confirmed against 200045 Devastate: Extra Target\'s own correctly-scoped row) - the classmask-dword gotcha from docs/dbc-build-pipeline.md Bug 3"',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the rage cost of your Devastate ability by 1. Your attacks ignore an additional 4% of your target's armor.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

gag_order_12311 = spell(
    id=12311,
    name='Gag Order',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=18498),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=12),
    ],
    spell_icon_id=280,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Gag Order rank 1 - values already matched, description only',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Shield Bash and Heroic Throw abilities a 50% chance to silence the target for 3 sec and increases the damage of your Shield Slam ability by 5%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_disciplines_12312 = spell(
    id=12312,
    name='Improved Disciplines',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-20001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=281,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Improved Disciplines rank 1 - 20s',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Shield Wall, Retaliation and Recklessness abilities by 20 secs.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 8208, 'EffectSpellClassMaskA_2': 8, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_disarm_12313 = spell(
    id=12313,
    name='Improved Disarm',
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
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=560,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Disarm ability by $/1000;s1 sec and causes the target to take an additional $s2% damage while disarmed.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 512, 'EffectSpellClassMaskB_1': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

commanding_presence_12318 = spell(
    id=12318,
    name='Commanding Presence',
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
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=2014,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the melee attack power bonus of your Battle Shout and the health bonus of your Commanding Shout by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskA_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

booming_voice_12321 = spell(
    id=12321,
    name='Booming Voice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108, misc_value=6),
    ],
    spell_icon_id=47,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the area of effect and duration of your Battle Shout, Demoralizing Shout and Commanding Shout by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 196608, 'EffectSpellClassMaskA_2': 128, 'EffectSpellClassMaskB_1': 196608, 'EffectSpellClassMaskB_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
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

improved_demoralizing_shout_12324 = spell(
    id=12324,
    name='Improved Demoralizing Shout',
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
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=282,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the melee attack power reduction of your Demoralizing Shout by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 131072, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
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

improved_cleave_12329 = spell(
    id=12329,
    name='Improved Cleave',
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
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=277,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the bonus damage done by your Cleave ability by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 4194304, 'EffectSpellClassMaskA_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_slam_12330 = spell(
    id=12330,
    name='Improved Slam',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1001, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=559,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Decreases the swing time of your Slam ability by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2097152, 'EffectSpellClassMaskB_1': 2097152, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_rend_12658 = spell(
    id=12658,
    name='Improved Rend',
    school=School.NORMAL,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=3),
    ],
    spell_icon_id=245,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the bleed damage done by your Rend ability by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_heroic_strike_12663 = spell(
    id=12663,
    name='Improved Heroic Strike',
    school=School.NORMAL,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=856,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cost of your Heroic Strike ability by $/10;s1 rage points.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 64, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_heroic_strike_12664 = spell(
    id=12664,
    name='Improved Heroic Strike',
    school=School.NORMAL,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=856,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cost of your Heroic Strike ability by $/10;s1 rage points.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 64, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_thunder_clap_12665 = spell(
    id=12665,
    name='Improved Thunder Clap',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=42,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Improved Thunder Clap rank 2 - dropped slow-% effect',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cost of your Thunder Clap ability by 2 rage points and increases its damage by 20%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 128, 'EffectSpellClassMaskB_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_thunder_clap_12666 = spell(
    id=12666,
    name='Improved Thunder Clap',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=42,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Improved Thunder Clap rank 3 - dropped slow-% effect. Fixed 2026-09-04: base_points was -41 (a 4-rage reduction) instead of -31 (3 rage',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cost of your Thunder Clap ability by 3 rage points and increases its damage by 30%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 128, 'EffectSpellClassMaskB_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_hamstring_12668 = spell(
    id=12668,
    name='Improved Hamstring',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=23694),
    ],
    spell_icon_id=23,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Hamstring ability a $h% chance to immobilize the target for $23694d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

tactical_mastery_12676 = spell(
    id=12676,
    name='Tactical Mastery',
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
        Effect(type=EffectType.APPLY_AURA, base_points=41, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=41, implicit_target_a=1, apply_aura=108, misc_value=2),
    ],
    spell_icon_id=139,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You retain up to an additional $s1 of your rage points when you change stances.  Also greatly increases the threat generated by your Bloodthirst and Mortal Strike abilities when you are in Defensive Stance (More effective than Rank 1).', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 512, 'EffectSpellClassMaskB_1': 33554432, 'EffectSpellClassMaskC_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 131072, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

tactical_mastery_12677 = spell(
    id=12677,
    name='Tactical Mastery',
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
        Effect(type=EffectType.APPLY_AURA, base_points=62, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=62, implicit_target_a=1, apply_aura=108, misc_value=2),
    ],
    spell_icon_id=139,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You retain up to an additional $s1 of your rage points when you change stances.  Also greatly increases the threat generated by your Bloodthirst and Mortal Strike abilities when you are in Defensive Stance (More effective than Rank 2).', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 512, 'EffectSpellClassMaskB_1': 33554432, 'EffectSpellClassMaskC_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 131072, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_charge_12697 = spell(
    id=12697,
    name='Improved Charge',
    school=School.NORMAL,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=457,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount of rage generated by your Charge ability by $/10;s1.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_revenge_12797 = spell(
    id=12797,
    name='Improved Revenge',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=200045),
    ],
    spell_icon_id=562,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Improved Revenge rank 1 - now unconditional (was chance-based) Fixed 2026-09-04: capstone tooltip text now shown on every rank (gray/|cFF9D9D9D on non-final ranks',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases damage of your Revenge ability by 15%. After using Revenge your next Devastate within 8 sec will strike an additional target. \n\n|cFF9D9D9DCapstone Bonus: Your Revenge strikes 2 additional targets.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 25, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_revenge_12799 = spell(
    id=12799,
    name='Improved Revenge',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=200045),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=17),
    ],
    spell_icon_id=562,
    notes="Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Improved Revenge rank 2 + capstone (unconditional +2 Revenge targets) - PLAYTEST, novel combo of proven primitives Fixed 2026-09-04: capstone tooltip text now shown on every rank (gray/|cFF9D9D9D on non-final ranks, normal color on the final rank), separated from the base text by two newlines, matching the pattern already used by the Frost Mage rework's pulled-from-Blizzard capstone talents (e.g. Frostbite).",
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases damage of your Revenge ability by 30%. After using Revenge your next Devastate within 8 sec will strike an additional target. \n\nCapstone Bonus: Your Revenge strikes 2 additional targets.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EffectSpellClassMaskB_1': 1024, 'EffectSpellClassMaskC_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_disciplines_12803 = spell(
    id=12803,
    name='Improved Disciplines',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-40001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=281,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Improved Disciplines rank 2 - 40s',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Shield Wall, Retaliation and Recklessness abilities by 40 secs.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 8208, 'EffectSpellClassMaskA_2': 8, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_disarm_12804 = spell(
    id=12804,
    name='Improved Disarm',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-20001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=560,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Disarm ability by $/1000;s1 sec and causes the target to take an additional $s2% damage while disarmed.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 512, 'EffectSpellClassMaskB_1': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
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

puncture_12810 = spell(
    id=12810,
    name='Puncture',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=280),
    ],
    spell_icon_id=565,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Puncture rank - rage cost unchanged, retargeted to Devastate only, added armor-pen. Fixed 2026-09-04: EffectSpellClassMaskA_1 (dword 1) never matched Devastate, whose own SpellClassMask lives in dword 2 (SpellClassMask_2=64, confirmed against 200045 Devastate: Extra Target\'s own correctly-scoped row) - the classmask-dword gotcha from docs/dbc-build-pipeline.md Bug 3"',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the rage cost of your Devastate ability by 2. Your attacks ignore an additional 8% of your target's armor.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

puncture_12811 = spell(
    id=12811,
    name='Puncture',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=280),
    ],
    spell_icon_id=565,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Puncture rank - rage cost unchanged, retargeted to Devastate only, added armor-pen. Fixed 2026-09-04: EffectSpellClassMaskA_1 (dword 1) never matched Devastate, whose own SpellClassMask lives in dword 2 (SpellClassMask_2=64, confirmed against 200045 Devastate: Extra Target\'s own correctly-scoped row) - the classmask-dword gotcha from docs/dbc-build-pipeline.md Bug 3"',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the rage cost of your Devastate ability by 3. Your attacks ignore an additional 12% of your target's armor.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_bloodrage_12818 = spell(
    id=12818,
    name='Improved Bloodrage',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=1),
    ],
    spell_icon_id=86,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Improved Bloodrage rank 2 - added Def-Stance dmg reduction',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the rage generated by your Bloodrage ability by 50%. While in Defensive Stance, reduces damage taken by 4%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 131072, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

deep_wounds_12834 = spell(
    id=12834,
    name='Deep Wounds',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12162),
    ],
    spell_icon_id=243,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 2, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical strikes cause the opponent to bleed, dealing 16% of your melee weapon's average damage over $12721d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69972, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

booming_voice_12835 = spell(
    id=12835,
    name='Booming Voice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=6),
    ],
    spell_icon_id=47,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the area of effect and duration of your Battle Shout, Demoralizing Shout and Commanding Shout by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 196608, 'EffectSpellClassMaskA_2': 128, 'EffectSpellClassMaskB_1': 196608, 'EffectSpellClassMaskB_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

deep_wounds_12849 = spell(
    id=12849,
    name='Deep Wounds',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12850),
    ],
    spell_icon_id=243,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 2, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical strikes cause the opponent to bleed, dealing 32% of your melee weapon's average damage over $12721d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69972, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

commanding_presence_12857 = spell(
    id=12857,
    name='Commanding Presence',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=2014,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the melee attack power bonus of your Battle Shout and the health bonus of your Commanding Shout by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskA_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

commanding_presence_12858 = spell(
    id=12858,
    name='Commanding Presence',
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
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=2014,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the melee attack power bonus of your Battle Shout and the health bonus of your Commanding Shout by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskA_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

commanding_presence_12860 = spell(
    id=12860,
    name='Commanding Presence',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=2014,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the melee attack power bonus of your Battle Shout and the health bonus of your Commanding Shout by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskA_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

commanding_presence_12861 = spell(
    id=12861,
    name='Commanding Presence',
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
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=2014,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the melee attack power bonus of your Battle Shout and the health bonus of your Commanding Shout by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskA_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_slam_12862 = spell(
    id=12862,
    name='Improved Slam',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-501, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=559,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Decreases the swing time of your Slam ability by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2097152, 'EffectSpellClassMaskB_1': 2097152, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

deep_wounds_12867 = spell(
    id=12867,
    name='Deep Wounds',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12868),
    ],
    spell_icon_id=243,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108866, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical strikes cause the opponent to bleed, dealing 48% of your melee weapon's average damage over $12721d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69972, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_demoralizing_shout_12876 = spell(
    id=12876,
    name='Improved Demoralizing Shout',
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
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=282,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the melee attack power reduction of your Demoralizing Shout by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 131072, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_demoralizing_shout_12877 = spell(
    id=12877,
    name='Improved Demoralizing Shout',
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
        Effect(type=EffectType.APPLY_AURA, base_points=23, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=282,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the melee attack power reduction of your Demoralizing Shout by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 131072, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_demoralizing_shout_12878 = spell(
    id=12878,
    name='Improved Demoralizing Shout',
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
        Effect(type=EffectType.APPLY_AURA, base_points=31, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=282,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the melee attack power reduction of your Demoralizing Shout by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 131072, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_demoralizing_shout_12879 = spell(
    id=12879,
    name='Improved Demoralizing Shout',
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
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=282,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the melee attack power reduction of your Demoralizing Shout by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 131072, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_cleave_12950 = spell(
    id=12950,
    name='Improved Cleave',
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
        Effect(type=EffectType.APPLY_AURA, base_points=79, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=277,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the bonus damage done by your Cleave ability by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 4194304, 'EffectSpellClassMaskA_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

gag_order_12958 = spell(
    id=12958,
    name='Gag Order',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=18498),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=12),
    ],
    spell_icon_id=280,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Gag Order rank 2 - 100% silence chance, 10% Shield Slam dmg',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Shield Bash and Heroic Throw abilities a 100% chance to silence the target for 3 sec and increases the damage of your Shield Slam ability by 10%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_overpower_12963 = spell(
    id=12963,
    name='Improved Overpower',
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
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=1464,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Overpower ability by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 4, 'EffectSpellClassMaskA_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
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

impale_16493 = spell(
    id=16493,
    name='Impale',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=105,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3999288558, 'EffectSpellClassMaskA_2': 51013, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
)

impale_16494 = spell(
    id=16494,
    name='Impale',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=105,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3999288558, 'EffectSpellClassMaskA_2': 51013, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
)

improved_cleave_20496 = spell(
    id=20496,
    name='Improved Cleave',
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
        Effect(type=EffectType.APPLY_AURA, base_points=119, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=277,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the bonus damage done by your Cleave ability by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 4194304, 'EffectSpellClassMaskA_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_berserker_rage_20500 = spell(
    id=20500,
    name='Improved Berserker Rage',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=23690),
    ],
    spell_icon_id=1465,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The Berserker Rage ability will generate $/10;23690s1 rage when used.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 4},
)

improved_berserker_rage_20501 = spell(
    id=20501,
    name='Improved Berserker Rage',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=23691),
    ],
    spell_icon_id=1465,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The Berserker Rage ability will generate $/10;23691s1 rage when used.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 4},
)

improved_execute_20502 = spell(
    id=20502,
    name='Improved Execute',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=1648,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the rage cost of your Execute ability by $/10;s1.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 536870912, 'EffectSpellClassMaskA_1': 536870912, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
)

improved_execute_20503 = spell(
    id=20503,
    name='Improved Execute',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=1648,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the rage cost of your Execute ability by $/10;s1.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 536870912, 'EffectSpellClassMaskA_1': 536870912, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
)

weapon_mastery_20504 = spell(
    id=20504,
    name='Weapon Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=248, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=1, apply_aura=234, misc_value=3),
    ],
    spell_icon_id=1976,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the chance for your attacks to be dodged by $s1% and reduces the duration of all Disarm effects used against you by $s2%.  This does not stack with other Disarm duration reducing effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
)

dual_wield_specialization_23584 = spell(
    id=23584,
    name='Dual Wield Specialization',
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
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=122),
    ],
    spell_icon_id=533,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your offhand weapon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
)

dual_wield_specialization_23585 = spell(
    id=23585,
    name='Dual Wield Specialization',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=122),
    ],
    spell_icon_id=533,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your offhand weapon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
)

dual_wield_specialization_23586 = spell(
    id=23586,
    name='Dual Wield Specialization',
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
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=122),
    ],
    spell_icon_id=533,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your offhand weapon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
)

dual_wield_specialization_23587 = spell(
    id=23587,
    name='Dual Wield Specialization',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=122),
    ],
    spell_icon_id=533,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your offhand weapon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
)

dual_wield_specialization_23588 = spell(
    id=23588,
    name='Dual Wield Specialization',
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
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=122),
    ],
    spell_icon_id=533,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your offhand weapon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
)

improved_hamstring_23695 = spell(
    id=23695,
    name='Improved Hamstring',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=23694),
    ],
    spell_icon_id=23,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Hamstring ability a $h% chance to immobilize the target for $23694d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 15, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
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

shield_mastery_29598 = spell(
    id=29598,
    name='Shield Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=150),
        Effect(type=EffectType.APPLY_AURA, base_points=-10001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2007,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Shield Mastery rank 1 - confirmed already matching design, no numeric change',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your block value by 15% and reduces the cooldown of your Shield Block ability by 10 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

shield_mastery_29599 = spell(
    id=29599,
    name='Shield Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=150),
        Effect(type=EffectType.APPLY_AURA, base_points=-20001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2007,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Shield Mastery rank 2 - confirmed already matching design, no numeric change',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your block value by 30% and reduces the cooldown of your Shield Block ability by 20 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

endless_rage_29623 = spell(
    id=29623,
    name='Endless Rage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=213),
    ],
    spell_icon_id=1962,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You generate $s1% more rage from damage dealt.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 1048576, 'SpellClassSet': 4},
)

improved_whirlwind_29721 = spell(
    id=29721,
    name='Improved Whirlwind',
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
    ],
    spell_icon_id=83,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Whirlwind ability by $s1%.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 4, 'EffectSpellClassMaskB_2': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_berserker_stance_29759 = spell(
    id=29759,
    name='Improved Berserker Stance',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=84,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Strength by $s1% and reduces threat caused by $s2% while in Berserker Stance.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 262144, 'SpellClassSet': 4},
)

improved_berserker_stance_29760 = spell(
    id=29760,
    name='Improved Berserker Stance',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=84,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Strength by $s1% and reduces threat caused by $s2% while in Berserker Stance.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 262144, 'SpellClassSet': 4},
)

improved_berserker_stance_29761 = spell(
    id=29761,
    name='Improved Berserker Stance',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=84,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Strength by $s1% and reduces threat caused by $s2% while in Berserker Stance.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 262144, 'SpellClassSet': 4},
)

improved_berserker_stance_29762 = spell(
    id=29762,
    name='Improved Berserker Stance',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.APPLY_AURA, base_points=-9, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=84,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Strength by $s1% and reduces threat caused by $s2% while in Berserker Stance.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 262144, 'SpellClassSet': 4},
)

improved_berserker_stance_29763 = spell(
    id=29763,
    name='Improved Berserker Stance',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=84,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Strength by $s1% and reduces threat caused by $s2% while in Berserker Stance.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 262144, 'SpellClassSet': 4},
)

improved_whirlwind_29776 = spell(
    id=29776,
    name='Improved Whirlwind',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=83,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Whirlwind ability by $s1%.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 4, 'EffectSpellClassMaskB_2': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

focused_rage_29787 = spell(
    id=29787,
    name='Focused Rage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=2008,
    notes="Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Focused Rage rank - repositioned only, values already match. Capstone deferred to phase 3. Fixed 2026-09-04: capstone tooltip text now shown on every rank (gray/|cFF9D9D9D on non-final ranks, normal color on the final rank), separated from the base text by two newlines, matching the pattern already used by the Frost Mage rework's pulled-from-Blizzard capstone talents (e.g. Frostbite).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the rage cost of your offensive abilities by $/10;s1. \n\n|cFF9D9D9DCapstone Bonus: You gain 5 rage every time the target of your Vigilance takes damage. This effect can only occur once every second.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1852722926, 'EffectSpellClassMaskA_2': 4253284, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

focused_rage_29790 = spell(
    id=29790,
    name='Focused Rage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=2008,
    notes="Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Focused Rage rank - repositioned only, values already match. Capstone deferred to phase 3. Fixed 2026-09-04: capstone tooltip text now shown on every rank (gray/|cFF9D9D9D on non-final ranks, normal color on the final rank), separated from the base text by two newlines, matching the pattern already used by the Frost Mage rework's pulled-from-Blizzard capstone talents (e.g. Frostbite).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the rage cost of your offensive abilities by $/10;s1. \n\n|cFF9D9D9DCapstone Bonus: You gain 5 rage every time the target of your Vigilance takes damage. This effect can only occur once every second.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1852722926, 'EffectSpellClassMaskA_2': 4253284, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

focused_rage_29792 = spell(
    id=29792,
    name='Focused Rage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=2008,
    notes="Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Focused Rage rank - repositioned only, values already match. Capstone deferred to phase 3. Fixed 2026-09-04: capstone tooltip text now shown on every rank (gray/|cFF9D9D9D on non-final ranks, normal color on the final rank), separated from the base text by two newlines, matching the pattern already used by the Frost Mage rework's pulled-from-Blizzard capstone talents (e.g. Frostbite).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the rage cost of your offensive abilities by $/10;s1. \n\nCapstone Bonus: You gain 5 rage every time the target of your Vigilance takes damage. This effect can only occur once every second.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1852722926, 'EffectSpellClassMaskA_2': 4253284, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

rampage_29801 = spell(
    id=29801,
    name='Rampage',
    school=School.NORMAL,
    attributes=80,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=65, base_points=4, implicit_target_a=1, apply_aura=52, radius_yards=100.0),
    ],
    spell_icon_id=2006,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 1073741824, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases ranged and melee critical hit chance by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases ranged and melee critical hit chance of all party and raid members within $29801a1 yds by $29801s1%.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Passive', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1},
)

second_wind_29834 = spell(
    id=29834,
    name='Second Wind',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1697,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you are struck by a Stun or Immobilize effect you will generate $/10;29841o1 rage and $29841o2% of your total health over $29841d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8208, 'EffectSpellClassMaskA_2': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 174760, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

blood_frenzy_29836 = spell(
    id=29836,
    name='Blood Frenzy',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=109, trigger_spell=30069),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=138),
    ],
    spell_icon_id=2005,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your melee attack speed by $s2%.  In addition your Rend and Deep Wounds abilities also increase all physical damage caused to that target by $30069s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 32, 'EffectSpellClassMaskA_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

second_wind_29838 = spell(
    id=29838,
    name='Second Wind',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1697,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you are struck by a Stun or Immobilize effect you will generate $/10;29842o1 rage and $29842o2% of your total health over $29842d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8208, 'EffectSpellClassMaskA_2': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 699048, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

blood_frenzy_29859 = spell(
    id=29859,
    name='Blood Frenzy',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=109, trigger_spell=30070),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=138),
    ],
    spell_icon_id=2005,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your melee attack speed by $s2%.  In addition your Rend and Deep Wounds abilities also increase all physical damage caused to that target by $30070s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 32, 'EffectSpellClassMaskA_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_intercept_29888 = spell(
    id=29888,
    name='Improved Intercept',
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
    spell_icon_id=516,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Intercept ability by $/1000;s1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1073741824, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_intercept_29889 = spell(
    id=29889,
    name='Improved Intercept',
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
    spell_icon_id=516,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Intercept ability by $/1000;s1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1073741824, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
)

improved_mortal_strike_35446 = spell(
    id=35446,
    name='Improved Mortal Strike',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-334, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=564,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage caused by your Mortal Strike ability by $s1% and reduces the cooldown by $/1000;S2 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_mortal_strike_35448 = spell(
    id=35448,
    name='Improved Mortal Strike',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-667, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=564,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage caused by your Mortal Strike ability by $s1% and reduces the cooldown by $/1000;S2 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_mortal_strike_35449 = spell(
    id=35449,
    name='Improved Mortal Strike',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=564,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage caused by your Mortal Strike ability by $s1% and reduces the cooldown by $/1000;S2 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

unrelenting_assault_46859 = spell(
    id=46859,
    name='Unrelenting Assault',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2775,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Overpower and Revenge abilities by $/1000;s1 secs and increases the damage done by both abilities by $s2%.  In addition, if you strike a player with Overpower while they are casting, their magical damage and healing will be reduced by $64849s1% for $64849d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1028, 'EffectSpellClassMaskB_1': 1028, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

unrelenting_assault_46860 = spell(
    id=46860,
    name='Unrelenting Assault',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-501, implicit_target_a=1, apply_aura=107, misc_value=21),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2775,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Overpower and Revenge abilities by $/1000;s1 secs and increases the damage done by both abilities by $s3%.  In addition, if you strike a player with Overpower while they are casting, their magical damage and healing will be reduced by $64850s1% for $64850d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1028, 'EffectSpellClassMaskB_1': 1028, 'EffectSpellClassMaskC_1': 1028, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

intensify_rage_46908 = spell(
    id=46908,
    name='Intensify Rage',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-12, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=1962,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Bloodrage, Berserker Rage, Recklessness and Death Wish abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1, 'EffectSpellClassMaskA_1': 269484304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
)

intensify_rage_46909 = spell(
    id=46909,
    name='Intensify Rage',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-23, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=1962,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Bloodrage, Berserker Rage, Recklessness and Death Wish abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1, 'EffectSpellClassMaskA_1': 269484304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
)

bloodsurge_46913 = spell(
    id=46913,
    name='Bloodsurge',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=127, trigger_spell=46916),
    ],
    spell_icon_id=2767,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Heroic Strike, Bloodthirst, and Whirlwind hits have a $h% chance of making your next Slam instant for $46916d.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 7, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 4},
)

bloodsurge_46914 = spell(
    id=46914,
    name='Bloodsurge',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=127, trigger_spell=46916),
    ],
    spell_icon_id=2767,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Heroic Strike, Bloodthirst, and Whirlwind hits have a $h% chance of making your next Slam instant for $46916d.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 13, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 4},
)

bloodsurge_46915 = spell(
    id=46915,
    name='Bloodsurge',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=127, trigger_spell=46916),
    ],
    spell_icon_id=2767,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Heroic Strike, Bloodthirst, and Whirlwind hits have a $h% chance of making your next Slam instant for $46916d.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 4},
)

titan_s_grip_46917 = spell(
    id=46917,
    name="Titan's Grip",
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=155, die_sides=0, implicit_target_a=1, misc_value=49152),
        Effect(type=140, die_sides=0, implicit_target_a=1, trigger_spell=50483),
    ],
    spell_icon_id=2750,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows you to equip two-handed axes, maces and swords in one hand.  While you have a two-handed weapon equipped in one hand, your physical damage done is reduced by $49152s1%.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskC_1': 778044516, 'EffectSpellClassMaskC_2': 17733, 'EquippedItemClass': 2, 'EquippedItemInvTypes': 6291456, 'EquippedItemSubclass': 41395, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
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

safeguard_46945 = spell(
    id=46945,
    name='Safeguard',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=46946),
    ],
    spell_icon_id=2781,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces damage taken by the target of your Intervene ability by $46946s1% for $46946d.', 'EffectBasePoints_1': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_1': 1, 'EffectSpellClassMaskA_1': 1073741825, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 1024, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

safeguard_46949 = spell(
    id=46949,
    name='Safeguard',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=46947),
    ],
    spell_icon_id=2781,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces damage taken by the target of your Intervene ability by $46947s1% for $46947d.', 'EffectBasePoints_1': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_1': 1, 'EffectSpellClassMaskA_1': 1073741825, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 1024, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

sword_and_board_46951 = spell(
    id=46951,
    name='Sword and Board',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=1, trigger_spell=50227),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2780,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Sword and Board rank - retuned Devastate crit%',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of Devastate by 5%. Casting an ability that costs rage has a chance to reset the cooldown of Shield Slam, make it cost no rage and increase its damage by 10%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

sword_and_board_46952 = spell(
    id=46952,
    name='Sword and Board',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=1, trigger_spell=50227),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2780,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Sword and Board rank - retuned Devastate crit%',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of Devastate by 10%. Casting an ability that costs rage has a chance to reset the cooldown of Shield Slam, make it cost no rage and increase its damage by 10%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

sword_and_board_46953 = spell(
    id=46953,
    name='Sword and Board',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=1, trigger_spell=50227),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2780,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Sword and Board rank - retuned Devastate crit%',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of Devastate by 15%. Casting an ability that costs rage has a chance to reset the cooldown of Shield Slam, make it cost no rage and increase its damage by 10%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
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

critical_block_47294 = spell(
    id=47294,
    name='Critical Block',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2778,
    notes='Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Critical Block rank - added guaranteed 8% block-damage-reduction marker (WarriorMechanics.cpp)',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your successful blocks reduce the damage you take from the blocked hit by 8%. Increases your chance to critically hit with your Shield Slam ability by 4%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

critical_block_47295 = spell(
    id=47295,
    name='Critical Block',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2778,
    notes='Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Critical Block rank - added guaranteed 16% block-damage-reduction marker (WarriorMechanics.cpp)',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your successful blocks reduce the damage you take from the blocked hit by 16%. Increases your chance to critically hit with your Shield Slam ability by 7%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

critical_block_47296 = spell(
    id=47296,
    name='Critical Block',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2778,
    notes='Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Critical Block rank - added guaranteed 25% block-damage-reduction marker (WarriorMechanics.cpp)',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your successful blocks reduce the damage you take from the blocked hit by 25%. Increases your chance to critically hit with your Shield Slam ability by 10%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

incite_50685 = spell(
    id=50685,
    name='Incite',
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
    ],
    spell_icon_id=2841,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Incite - retargeted from HS/Cleave/TC to Revenge; capstone deferred to phase 3 Fixed 2026-09-04: capstone tooltip text now shown on every rank (gray/|cFF9D9D9D on non-final ranks',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your Revenge by 10%. \n\n|cFF9D9D9DCapstone Bonus: Critical strikes with Revenge add an amount equal to 1.5% of your maximum health to your Storm's Bulwark shield increased by your mastery, up to its maximum. This does not extend the shield's duration.|r", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

incite_50686 = spell(
    id=50686,
    name='Incite',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2841,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Incite - retargeted from HS/Cleave/TC to Revenge; capstone deferred to phase 3 Fixed 2026-09-04: capstone tooltip text now shown on every rank (gray/|cFF9D9D9D on non-final ranks',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your Revenge by 20%. \n\n|cFF9D9D9DCapstone Bonus: Critical strikes with Revenge add an amount equal to 1.5% of your maximum health to your Storm's Bulwark shield increased by your mastery, up to its maximum. This does not extend the shield's duration.|r", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

incite_50687 = spell(
    id=50687,
    name='Incite',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2841,
    notes='Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Incite rank 3 - added capstone proc marker (spell_warr_incite) Fixed 2026-09-04: capstone tooltip text now shown on every rank (gray/|cFF9D9D9D on non-final ranks',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your Revenge by 30%. \n\nCapstone Bonus: Critical strikes with Revenge add an amount equal to 1.5% of your maximum health to your Storm's Bulwark shield increased by your mastery, up to its maximum. This does not extend the shield's duration.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

taste_for_blood_56636 = spell(
    id=56636,
    name='Taste for Blood',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=11, trigger_spell=60503),
    ],
    spell_icon_id=2961,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 64, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Rend ability causes damage, you have a $h% chance of allowing the use of your Overpower ability for $60503d.  1 charge.  This effect will not occur more than once every 6 sec.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

taste_for_blood_56637 = spell(
    id=56637,
    name='Taste for Blood',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=11, trigger_spell=60503),
    ],
    spell_icon_id=2961,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 64, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Rend ability causes damage, you have a $h% chance of allowing the use of your Overpower ability for $60503d.  1 charge.  This effect will not occur more than once every 6 sec.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

taste_for_blood_56638 = spell(
    id=56638,
    name='Taste for Blood',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=11, trigger_spell=60503),
    ],
    spell_icon_id=2961,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 64, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Rend ability causes damage, you have a $h% chance of allowing the use of your Overpower ability for $60503d.  1 charge.  This effect will not occur more than once every 6 sec.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

intensify_rage_56924 = spell(
    id=56924,
    name='Intensify Rage',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-34, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=1962,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Bloodrage, Berserker Rage, Recklessness and Death Wish abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1, 'EffectSpellClassMaskA_1': 269484304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
)

unending_fury_56927 = spell(
    id=56927,
    name='Unending Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2729,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Slam, Whirlwind and Bloodthirst abilities by $s2%.', 'EffectBasePoints_1': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_1': 1, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_1': 2097152, 'EffectSpellClassMaskB_2': 1028, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

unending_fury_56929 = spell(
    id=56929,
    name='Unending Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2729,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Slam, Whirlwind and Bloodthirst abilities by $s2%.', 'EffectBasePoints_1': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_1': 1, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_1': 2097152, 'EffectSpellClassMaskB_2': 1028, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

unending_fury_56930 = spell(
    id=56930,
    name='Unending Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2729,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Slam, Whirlwind and Bloodthirst abilities by $s2%.', 'EffectBasePoints_1': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_1': 1, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_1': 2097152, 'EffectSpellClassMaskB_2': 1028, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

unending_fury_56931 = spell(
    id=56931,
    name='Unending Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2729,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Slam, Whirlwind and Bloodthirst abilities by $s2%.', 'EffectBasePoints_1': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_1': 1, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_1': 2097152, 'EffectSpellClassMaskB_2': 1028, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

unending_fury_56932 = spell(
    id=56932,
    name='Unending Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2729,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Slam, Whirlwind and Bloodthirst abilities by $s2%.', 'EffectBasePoints_1': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_1': 1, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_1': 2097152, 'EffectSpellClassMaskB_2': 1028, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

warbringer_57499 = spell(
    id=57499,
    name='Warbringer',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=262, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=275),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=6953),
    ],
    spell_icon_id=3518,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Charge, Intercept and Intervene abilities are now usable while in combat and in any stance.  In addition, your Intervene ability will remove all movement impairing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1073741825, 'EffectSpellClassMaskB_2': 65536, 'EffectSpellClassMaskC_2': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellPriority': 50},
)

damage_shield_58872 = spell(
    id=58872,
    name='Damage Shield',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=1),
    ],
    spell_icon_id=3214,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 2, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you take damage from or block a melee attack you cause damage equal to $s1% of your block value.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 40, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

damage_shield_58874 = spell(
    id=58874,
    name='Damage Shield',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=1),
    ],
    spell_icon_id=3214,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 2, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you take damage from or block a melee attack you cause damage equal to $s1% of your block value.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 40, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

improved_spell_reflection_59088 = spell(
    id=59088,
    name='Improved Spell Reflection',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=186, misc_value=126),
    ],
    spell_icon_id=1935,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the chance you'll be hit by spells by $s3% and when the ability is used it will reflect the first spell cast against the $s2 closest party members within 20 yards.", 'EffectBasePoints_1': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_1': 1, 'EffectSpellClassMaskA_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
)

improved_spell_reflection_59089 = spell(
    id=59089,
    name='Improved Spell Reflection',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=186, misc_value=126),
    ],
    spell_icon_id=1935,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the chance you'll be hit by spells by $s3% and when the ability is used it will reflect the first spell cast against the $s2 closest party members within 20 yards.", 'EffectBasePoints_1': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_1': 1, 'EffectSpellClassMaskA_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4},
)

armored_to_the_teeth_61216 = spell(
    id=61216,
    name='Armored to the Teeth',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=107, implicit_target_a=1, apply_aura=285, misc_value=1),
        Effect(type=EffectType.DUMMY),
    ],
    spell_icon_id=3516,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your attack power by $s2 for every ${$m1*$m2} armor value you have.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 196608, 'EffectSpellClassMaskA_2': 128, 'EffectSpellClassMaskB_1': 196608, 'EffectSpellClassMaskB_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

armored_to_the_teeth_61221 = spell(
    id=61221,
    name='Armored to the Teeth',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=53, implicit_target_a=1, apply_aura=285, misc_value=1),
        Effect(type=EffectType.DUMMY, base_points=1),
    ],
    spell_icon_id=3516,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your attack power by $s2 for every ${$m1*$m2} armor value you have.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 196608, 'EffectSpellClassMaskA_2': 128, 'EffectSpellClassMaskB_1': 196608, 'EffectSpellClassMaskB_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

armored_to_the_teeth_61222 = spell(
    id=61222,
    name='Armored to the Teeth',
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
        Effect(type=EffectType.DUMMY, base_points=2),
    ],
    spell_icon_id=3516,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your attack power by $s2 for every ${$m1*$m2} armor value you have.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 196608, 'EffectSpellClassMaskA_2': 128, 'EffectSpellClassMaskB_1': 196608, 'EffectSpellClassMaskB_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

juggernaut_64976 = spell(
    id=64976,
    name='Juggernaut',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=262, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=7, trigger_spell=65156),
        Effect(type=EffectType.APPLY_AURA, base_points=4999, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2769,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Charge ability is now usable while in combat, but the cooldown on Charge is increased by ${$m3/1000} sec. Following a Charge, your next Slam or Mortal Strike has an additional $65156s1% chance to critically hit if used within $65156d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 2097152, 'EffectSpellClassMaskC_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 4096, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellPriority': 50},
)

iron_temper_29593 = spell(
    id=29593,
    name='Iron Temper',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200050),
    ],
    spell_icon_id=2024,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Improved Defensive Stance rank 1 - fixed crit-taken aura type, repointed Enrage to flat-6% copy. Reworked 2026-09-04 into Iron Temper: crit-taken reduction removed (now baseline elsewhere), talent is now just the Block/Parry/Dodge->Enrage proc; icon -> Spell_Nature_ShamanRage (2024).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you Block, Parry or Dodge an attack you have a 50% chance to become Enraged, increasing Physical damage caused by 6% and take 6% reduced damage. for 12 sec.', 'DurationIndex': 0, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 174760, 'RangeIndex': 1, 'ShapeshiftMask': 131072},
)

iron_temper_29594 = spell(
    id=29594,
    name='Iron Temper',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200050),
    ],
    spell_icon_id=2024,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Improved Defensive Stance rank 2 - fixed crit-taken aura type, repointed Enrage to flat-6% copy. Reworked 2026-09-04 into Iron Temper: crit-taken reduction removed (now baseline elsewhere), talent is now just the Block/Parry/Dodge->Enrage proc; icon -> Spell_Nature_ShamanRage (2024).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you Block, Parry or Dodge an attack you have a 100% chance to become Enraged, increasing Physical damage caused by 6% and take 6% reduced damage. for 12 sec.', 'DurationIndex': 0, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 174760, 'RangeIndex': 1, 'ShapeshiftMask': 131072},
)

vigilance_59665 = spell(
    id=59665,
    name='Vigilance',
    school=School.NORMAL,
    attributes=151322640,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=130, base_points=14, implicit_target_a=57),
    ],
    spell_icon_id=2834,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Vigilance threat-redirect 10%->15% (spell_warr_vigilance_redirect_threat already handles the rest)',
    raw_overrides={'AttributesEx2': 4, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Focus your protective gaze on a group or raid target, reducing their damage taken by $50720s1% and transfers $50720s3% of the threat they cause to you.  In addition, each time they are hit by an attack your Taunt cooldown is refreshed.  Lasts $50720d.  This effect can only be on one target at a time.', 'DurationIndex': 0, 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101},
)

shield_specialization_200031 = spell(
    id=200031,
    name='Shield Specialization',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=51),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=23602),
    ],
    spell_icon_id=280,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Shield Specialization rank (new override, was unmodified 5-rank base data)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases your chance to block attacks with a shield by 4%. You have a 33% chance to generate 5 rage when a block, dodge, or parry occurs.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to block attacks with a shield by 4%. You have a 33% chance to generate 5 rage when a block, dodge, or parry occurs.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Shield Specialization', 'ProcChance': 33, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

shield_specialization_200032 = spell(
    id=200032,
    name='Shield Specialization',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=51),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=23602),
    ],
    spell_icon_id=280,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Shield Specialization rank (new override, was unmodified 5-rank base data)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases your chance to block attacks with a shield by 7%. You have a 66% chance to generate 5 rage when a block, dodge, or parry occurs.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to block attacks with a shield by 7%. You have a 66% chance to generate 5 rage when a block, dodge, or parry occurs.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Shield Specialization', 'ProcChance': 66, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

shield_specialization_200033 = spell(
    id=200033,
    name='Shield Specialization',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=51),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=23602),
    ],
    spell_icon_id=280,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Shield Specialization rank (new override, was unmodified 5-rank base data)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases your chance to block attacks with a shield by 10%. You have a 100% chance to generate 5 rage when a block, dodge, or parry occurs.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to block attacks with a shield by 10%. You have a 100% chance to generate 5 rage when a block, dodge, or parry occurs.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Shield Specialization', 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

unbridled_wrath_200034 = spell(
    id=200034,
    name='Unbridled Wrath',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=23602),
    ],
    spell_icon_id=2005,
    notes="Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Unbridled Wrath rank (new copy of Fury's 12322/12999-13002; donor untouched)",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'You have a 10% chance to generate 5 rage when you deal melee damage. This effect can only occur once per ability use.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a 10% chance to generate 5 rage when you deal melee damage. This effect can only occur once per ability use.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Unbridled Wrath', 'ProcChance': 10, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

unbridled_wrath_200035 = spell(
    id=200035,
    name='Unbridled Wrath',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=23602),
    ],
    spell_icon_id=2005,
    notes="Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Unbridled Wrath rank (new copy of Fury's 12322/12999-13002; donor untouched)",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'You have a 20% chance to generate 5 rage when you deal melee damage. This effect can only occur once per ability use.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a 20% chance to generate 5 rage when you deal melee damage. This effect can only occur once per ability use.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Unbridled Wrath', 'ProcChance': 20, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

unbridled_wrath_200036 = spell(
    id=200036,
    name='Unbridled Wrath',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=23602),
    ],
    spell_icon_id=2005,
    notes="Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Unbridled Wrath rank (new copy of Fury's 12322/12999-13002; donor untouched)",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'You have a 30% chance to generate 5 rage when you deal melee damage. This effect can only occur once per ability use.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a 30% chance to generate 5 rage when you deal melee damage. This effect can only occur once per ability use.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Unbridled Wrath', 'ProcChance': 30, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

devastate_extra_target_200045 = spell(
    id=200045,
    name='Devastate: Extra Target',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=107, misc_value=17),
    ],
    spell_icon_id=1508,
    notes="Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Improved Revenge's charge-buff - no script needed, see Player::ApplySpellMod",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Your next Devastate will strike an additional target.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next Devastate will strike an additional target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Devastate: Extra Target', 'ProcChance': 101, 'ProcCharges': 1, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

firm_grip_200038 = spell(
    id=200038,
    name='Firm Grip',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=142, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=137, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=150),
    ],
    spell_icon_id=134,
    notes="Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Firm Grip rank (new; armor% only active while a Shield is equipped, matching Toughness's own item-gating convention)",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases your armor value from your equipped Shield by 10%. Increases your Stamina by 1%. Increases your block value by 2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your armor value from your equipped Shield by 10%. Increases your Stamina by 1%. Increases your block value by 2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Firm Grip', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

firm_grip_200039 = spell(
    id=200039,
    name='Firm Grip',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=142, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=150),
    ],
    spell_icon_id=134,
    notes="Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Firm Grip rank (new; armor% only active while a Shield is equipped, matching Toughness's own item-gating convention)",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases your armor value from your equipped Shield by 20%. Increases your Stamina by 2%. Increases your block value by 4%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your armor value from your equipped Shield by 20%. Increases your Stamina by 2%. Increases your block value by 4%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Firm Grip', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

firm_grip_200040 = spell(
    id=200040,
    name='Firm Grip',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=142, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=137, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=150),
    ],
    spell_icon_id=134,
    notes="Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Firm Grip rank (new; armor% only active while a Shield is equipped, matching Toughness's own item-gating convention)",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases your armor value from your equipped Shield by 30%. Increases your Stamina by 3%. Increases your block value by 6%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your armor value from your equipped Shield by 30%. Increases your Stamina by 3%. Increases your block value by 6%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Firm Grip', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

shield_cover_200041 = spell(
    id=200041,
    name='Shield Cover',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=150),
        Effect(type=EffectType.APPLY_AURA, base_points=-3001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=1935,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Shield Cover rank - CD reduction scoped to Spell Reflection (classmask dword2). Capstone deferred to phase 3 - all 3 effect slots already used by the base kit. Fixed 2026-09-04: capstone tooltip text now shown on every rank (gray/|cFF9D9D9D on non-final ranks',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Reduces your damage taken by 1%. Increases your block value by 4%. Reduces the cooldown of Spell Reflection by 3 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces your damage taken by 1%. Increases your block value by 4%. Reduces the cooldown of Spell Reflection by 3 sec. \n\n|cFF9D9D9DCapstone Bonus: Using Spell Reflection or Shield Block also reduces all Magic damage taken by 30% for 3 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Shield Cover', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

shield_cover_200042 = spell(
    id=200042,
    name='Shield Cover',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=150),
        Effect(type=EffectType.APPLY_AURA, base_points=-3001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=1935,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Shield Cover rank - CD reduction scoped to Spell Reflection (classmask dword2). Capstone deferred to phase 3 - all 3 effect slots already used by the base kit. Fixed 2026-09-04: capstone tooltip text now shown on every rank (gray/|cFF9D9D9D on non-final ranks',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Reduces your damage taken by 2%. Increases your block value by 7%. Reduces the cooldown of Spell Reflection by 3 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces your damage taken by 2%. Increases your block value by 7%. Reduces the cooldown of Spell Reflection by 3 sec. \n\n|cFF9D9D9DCapstone Bonus: Using Spell Reflection or Shield Block also reduces all Magic damage taken by 30% for 3 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Shield Cover', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

shield_cover_200043 = spell(
    id=200043,
    name='Shield Cover',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=150),
        Effect(type=EffectType.APPLY_AURA, base_points=-3001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=1935,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Shield Cover rank - CD reduction scoped to Spell Reflection (classmask dword2). Capstone deferred to phase 3 - all 3 effect slots already used by the base kit. Fixed 2026-09-04: capstone tooltip text now shown on every rank (gray/|cFF9D9D9D on non-final ranks',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Reduces your damage taken by 3%. Increases your block value by 10%. Reduces the cooldown of Spell Reflection by 3 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces your damage taken by 3%. Increases your block value by 10%. Reduces the cooldown of Spell Reflection by 3 sec. \n\nCapstone Bonus: Using Spell Reflection or Shield Block also reduces all Magic damage taken by 30% for 3 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Shield Cover', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

enrage_iron_temper_200050 = spell(
    id=200050,
    name='Enrage (Iron Temper)',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=79, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=1710,
    notes="Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): shared Enrage buff for Improved Defensive Stance's (now Iron Temper's) proc (donor Enrage 57514/57516 give 5%/10%, design wants flat 6%). Reworked 2026-09-04: added effect2 (SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN, -6%, all schools) alongside the existing +6% physical damage, matching Iron Temper's new 'and take 6% reduced damage' text.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases Physical damage caused by 6% and reduces damage taken by 6%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Physical damage caused by 6% and reduces damage taken by 6%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Enrage (Iron Temper)', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

resolve_200046 = spell(
    id=200046,
    name='Resolve',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=137, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=306, misc_value=2097152),
    ],
    spell_icon_id=2007,
    notes="Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Resolve rank (new copy of 'Vitality' 29140/29143/29144, Expertise->Versatility; Str/Sta already matched donor exactly). Versatility rating-per-% was originally a level-80 estimate from GtCombatRatings/GtOCTClassCombatRatingScalar, which made the talent give more than 2/4/6% below 80 and worse the more you leveled. A flat, level-independent Player::GetRatingMultiplier override was tried and reverted - it silently broke every existing item's Versatility/Mastery/Cooldown Haste rating too, since the shared rating pool has no way to tell gear-sourced points from talent-sourced ones apart (confirmed live: a 700-rating ring went from +25% to +358%, quadrupling Devastate damage). A per-level-cap base_points retune (55/111/167 for the level-60 cap) was tried next and also reverted before shipping - it would have needed re-deriving by hand every time the progression cap advances. Final fix: apply_aura is now 306 (SPELL_AURA_MOD_CUSTOM_STAT_PCT, see that aura's comment in SpellAuraDefines.h) instead of 189 (SPELL_AURA_MOD_RATING) - a dedicated flat-percentage aura that never touches PLAYER_FIELD_COMBAT_RATING at all, so it can't collide with gear and needs no level-cap-dependent math. base_points are plain percentage points again (1/3/5, +1 tooltip convention -> 2/4/6%), same mechanism real crit-chance talents use (SPELL_AURA_MOD_CRIT_PCT) to grant a flat % alongside (not through) the rating system. misc_value stays 2097152 (1 << CR_VERSATILITY) - same bit Player::GetVersatilityPercentage() reads via GetTotalAuraModifierByMiscMask.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases your Strength by 2%, Stamina by 3% and your Versatility by 2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Strength by 2%, Stamina by 3% and your Versatility by 2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Resolve', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

resolve_200047 = spell(
    id=200047,
    name='Resolve',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=137, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=306, misc_value=2097152),
    ],
    spell_icon_id=2007,
    notes="Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Resolve rank (new copy of 'Vitality' 29140/29143/29144, Expertise->Versatility; Str/Sta already matched donor exactly). Versatility rating-per-% was originally a level-80 estimate from GtCombatRatings/GtOCTClassCombatRatingScalar, which made the talent give more than 2/4/6% below 80 and worse the more you leveled. A flat, level-independent Player::GetRatingMultiplier override was tried and reverted - it silently broke every existing item's Versatility/Mastery/Cooldown Haste rating too, since the shared rating pool has no way to tell gear-sourced points from talent-sourced ones apart (confirmed live: a 700-rating ring went from +25% to +358%, quadrupling Devastate damage). A per-level-cap base_points retune (55/111/167 for the level-60 cap) was tried next and also reverted before shipping - it would have needed re-deriving by hand every time the progression cap advances. Final fix: apply_aura is now 306 (SPELL_AURA_MOD_CUSTOM_STAT_PCT, see that aura's comment in SpellAuraDefines.h) instead of 189 (SPELL_AURA_MOD_RATING) - a dedicated flat-percentage aura that never touches PLAYER_FIELD_COMBAT_RATING at all, so it can't collide with gear and needs no level-cap-dependent math. base_points are plain percentage points again (1/3/5, +1 tooltip convention -> 2/4/6%), same mechanism real crit-chance talents use (SPELL_AURA_MOD_CRIT_PCT) to grant a flat % alongside (not through) the rating system. misc_value stays 2097152 (1 << CR_VERSATILITY) - same bit Player::GetVersatilityPercentage() reads via GetTotalAuraModifierByMiscMask.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases your Strength by 4%, Stamina by 6% and your Versatility by 4%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Strength by 4%, Stamina by 6% and your Versatility by 4%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Resolve', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

resolve_200048 = spell(
    id=200048,
    name='Resolve',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=137, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=306, misc_value=2097152),
    ],
    spell_icon_id=2007,
    notes="Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Resolve rank (new copy of 'Vitality' 29140/29143/29144, Expertise->Versatility; Str/Sta already matched donor exactly). Versatility rating-per-% was originally a level-80 estimate from GtCombatRatings/GtOCTClassCombatRatingScalar, which made the talent give more than 2/4/6% below 80 and worse the more you leveled. A flat, level-independent Player::GetRatingMultiplier override was tried and reverted - it silently broke every existing item's Versatility/Mastery/Cooldown Haste rating too, since the shared rating pool has no way to tell gear-sourced points from talent-sourced ones apart (confirmed live: a 700-rating ring went from +25% to +358%, quadrupling Devastate damage). A per-level-cap base_points retune (55/111/167 for the level-60 cap) was tried next and also reverted before shipping - it would have needed re-deriving by hand every time the progression cap advances. Final fix: apply_aura is now 306 (SPELL_AURA_MOD_CUSTOM_STAT_PCT, see that aura's comment in SpellAuraDefines.h) instead of 189 (SPELL_AURA_MOD_RATING) - a dedicated flat-percentage aura that never touches PLAYER_FIELD_COMBAT_RATING at all, so it can't collide with gear and needs no level-cap-dependent math. base_points are plain percentage points again (1/3/5, +1 tooltip convention -> 2/4/6%), same mechanism real crit-chance talents use (SPELL_AURA_MOD_CRIT_PCT) to grant a flat % alongside (not through) the rating system. misc_value stays 2097152 (1 << CR_VERSATILITY) - same bit Player::GetVersatilityPercentage() reads via GetTotalAuraModifierByMiscMask.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases your Strength by 6%, Stamina by 9% and your Versatility by 6%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Strength by 6%, Stamina by 9% and your Versatility by 6%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Resolve', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

unrelenting_200049 = spell(
    id=200049,
    name='Unrelenting',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=262, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=275),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=6953),
    ],
    spell_icon_id=2065,
    notes="Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Unrelenting (new copy of 'Warbringer' 57499, donor untouched). 'Each Revenge cast reduces Last Stand's cooldown by 1s' clause deferred to phase 3.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Your Charge, Intercept, and Intervene abilities are usable while in combat and in any stance.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Charge, Intercept, and Intervene abilities are usable while in combat and in any stance.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1073741825, 'EffectSpellClassMaskB_2': 65536, 'EffectSpellClassMaskC_2': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Unrelenting', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

thunderstruck_200051 = spell(
    id=200051,
    name='Thunderstruck',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=329, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=1936,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Thunderstruck rank (new). Capstone (delayed Thunder Clap echo) deferred to phase 3. Fixed 2026-09-04: capstone tooltip text now shown on every rank (gray/|cFF9D9D9D on non-final ranks',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases the damage and threat of Shockwave and Thunder Clap by 10%. Increases the duration of Shockwave by 0.33 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and threat of Shockwave and Thunder Clap by 10%. Increases the duration of Shockwave by 0.33 sec. \n\n|cFF9D9D9DCapstone Bonus: 3 sec after casting Thunder Clap, a second Thunder Clap occurs at the same location at 50% effectiveness.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 128, 'EffectSpellClassMaskA_2': 32768, 'EffectSpellClassMaskB_1': 128, 'EffectSpellClassMaskB_2': 32768, 'EffectSpellClassMaskC_2': 32768, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Thunderstruck', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

thunderstruck_200052 = spell(
    id=200052,
    name='Thunderstruck',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=659, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=1936,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Thunderstruck rank (new). Capstone (delayed Thunder Clap echo) deferred to phase 3. Fixed 2026-09-04: capstone tooltip text now shown on every rank (gray/|cFF9D9D9D on non-final ranks',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases the damage and threat of Shockwave and Thunder Clap by 20%. Increases the duration of Shockwave by 0.66 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and threat of Shockwave and Thunder Clap by 20%. Increases the duration of Shockwave by 0.66 sec. \n\n|cFF9D9D9DCapstone Bonus: 3 sec after casting Thunder Clap, a second Thunder Clap occurs at the same location at 50% effectiveness.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 128, 'EffectSpellClassMaskA_2': 32768, 'EffectSpellClassMaskB_1': 128, 'EffectSpellClassMaskB_2': 32768, 'EffectSpellClassMaskC_2': 32768, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Thunderstruck', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

thunderstruck_200053 = spell(
    id=200053,
    name='Thunderstruck',
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
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=1936,
    notes='Protection Warrior rework phase 2 (docs/prot_warrior_rework.md): Thunderstruck rank (new). Capstone (delayed Thunder Clap echo) deferred to phase 3. Fixed 2026-09-04: capstone tooltip text now shown on every rank (gray/|cFF9D9D9D on non-final ranks',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases the damage and threat of Shockwave and Thunder Clap by 30%. Increases the duration of Shockwave by 1.0 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and threat of Shockwave and Thunder Clap by 30%. Increases the duration of Shockwave by 1.0 sec. \n\nCapstone Bonus: 3 sec after casting Thunder Clap, a second Thunder Clap occurs at the same location at 50% effectiveness.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 128, 'EffectSpellClassMaskA_2': 32768, 'EffectSpellClassMaskB_1': 128, 'EffectSpellClassMaskB_2': 32768, 'EffectSpellClassMaskC_2': 32768, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Thunderstruck', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

blood_and_thunder_200054 = spell(
    id=200054,
    name='Blood and Thunder',
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
    ],
    spell_icon_id=245,
    notes='Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Blood and Thunder rank (15%) - marker read by spell_warr_thunder_clap',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Your Thunder Clap causes targets to bleed for 15% of the damage dealt over 9 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Thunder Clap causes targets to bleed for 15% of the damage dealt over 9 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Blood and Thunder', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

blood_and_thunder_200055 = spell(
    id=200055,
    name='Blood and Thunder',
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
    spell_icon_id=245,
    notes='Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Blood and Thunder rank (30%) - marker read by spell_warr_thunder_clap',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Your Thunder Clap causes targets to bleed for 30% of the damage dealt over 9 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Thunder Clap causes targets to bleed for 30% of the damage dealt over 9 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Blood and Thunder', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

reprisal_200056 = spell(
    id=200056,
    name='Reprisal',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=558,
    notes='Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Reprisal rank (0.5%, stored as tenths) - marker read by spell_warr_devastate',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': "Your Devastate adds an amount equal to 0.5% of your maximum health to your Storm's Bulwark shield, increased by your mastery. This amount is increased by 20% for each application of Sunder Armor on the target.", 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Devastate adds an amount equal to 0.5% of your maximum health to your Storm's Bulwark shield, increased by your mastery. This amount is increased by 20% for each application of Sunder Armor on the target.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Reprisal', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

reprisal_200057 = spell(
    id=200057,
    name='Reprisal',
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
    ],
    spell_icon_id=558,
    notes='Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Reprisal rank (1%, stored as tenths) - marker read by spell_warr_devastate',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': "Your Devastate adds an amount equal to 1% of your maximum health to your Storm's Bulwark shield, increased by your mastery. This amount is increased by 20% for each application of Sunder Armor on the target.", 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Devastate adds an amount equal to 1% of your maximum health to your Storm's Bulwark shield, increased by your mastery. This amount is increased by 20% for each application of Sunder Armor on the target.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Reprisal', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

storm_s_bulwark_200058 = spell(
    id=200058,
    name="Storm's Bulwark",
    school=School.NORMAL,
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
    spell_icon_id=1941,
    notes="Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Storm's Bulwark talent rank (2%) - marker read by spell_warr_thunder_clap",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Your Thunder Clap grants you an absorb shield equal to 2% of your maximum health, increased by your mastery, plus an additional 1% for each target struck. Lasts 15 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Thunder Clap grants you an absorb shield equal to 2% of your maximum health, increased by your mastery, plus an additional 1% for each target struck. Lasts 15 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': "Storm's Bulwark", 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

storm_s_bulwark_200059 = spell(
    id=200059,
    name="Storm's Bulwark",
    school=School.NORMAL,
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
    spell_icon_id=1941,
    notes="Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Storm's Bulwark talent rank (4%) - marker read by spell_warr_thunder_clap",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Your Thunder Clap grants you an absorb shield equal to 4% of your maximum health, increased by your mastery, plus an additional 1% for each target struck. Lasts 15 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Thunder Clap grants you an absorb shield equal to 4% of your maximum health, increased by your mastery, plus an additional 1% for each target struck. Lasts 15 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': "Storm's Bulwark", 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

storm_s_bulwark_200060 = spell(
    id=200060,
    name="Storm's Bulwark",
    school=School.NORMAL,
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
    spell_icon_id=1941,
    notes="Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Storm's Bulwark talent rank (6%) - marker read by spell_warr_thunder_clap",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Your Thunder Clap grants you an absorb shield equal to 6% of your maximum health, increased by your mastery, plus an additional 1% for each target struck. Lasts 15 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Thunder Clap grants you an absorb shield equal to 6% of your maximum health, increased by your mastery, plus an additional 1% for each target struck. Lasts 15 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': "Storm's Bulwark", 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

shield_cover_200061 = spell(
    id=200061,
    name='Shield Cover',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=1935,
    notes='Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Shield Cover capstone buff - cast by spell_warr_shield_cover_capstone',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Reduces Magic damage taken by 30% for 3 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces Magic damage taken by 30% for 3 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Shield Cover', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

shield_discipline_200062 = spell(
    id=200062,
    name='Shield Discipline',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=28,
    notes='Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Shield Discipline rank (25%) - marker read by spell_warr_shield_slam',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Your Shield Slam increases the absorb granted by your next Thunder Clap by 25%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Shield Slam increases the absorb granted by your next Thunder Clap by 25%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Shield Discipline', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

shield_discipline_200063 = spell(
    id=200063,
    name='Shield Discipline',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=28,
    notes='Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Shield Discipline rank (50%) - marker read by spell_warr_shield_slam',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Your Shield Slam increases the absorb granted by your next Thunder Clap by 50%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Shield Slam increases the absorb granted by your next Thunder Clap by 50%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Shield Discipline', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

shield_discipline_200064 = spell(
    id=200064,
    name='Shield Discipline',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1935,
    notes="Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Shield Discipline's internal charge buff - basepoints set per-cast, see spell_warr_shield_slam",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': "Your next Thunder Clap's absorb is increased.", 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your next Thunder Clap's absorb is increased.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Shield Discipline', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

thunder_clap_echo_200065 = spell(
    id=200065,
    name='Thunder Clap Echo',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=6, points_per_level=1.9256756756756757, implicit_target_a=22, implicit_target_b=15, radius_yards=8.0),
    ],
    spell_icon_id=1936,
    notes="Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Thunderstruck capstone echo - ~50% of Thunder Clap's own damage formula, fired by 200066's native periodic trigger; deliberately damage-only (no slow, no Blood and Thunder/Storm's Bulwark re-trigger). Fixed 2026-09-03: effect1 was type 6 (APPLY_AURA) / apply_aura 2 (SPELL_AURA_MOD_POSSESS) instead of type 2 (SCHOOL_DAMAGE) - caused the echo to possess the target instead of damaging it.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': '', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': '', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Thunder Clap Echo', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)

thunderstruck_200066 = spell(
    id=200066,
    name='Thunderstruck',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=3000, trigger_spell=200065),
    ],
    spell_icon_id=1936,
    notes="Protection Warrior rework phase 3 (docs/prot_warrior_rework.md): Thunderstruck capstone's delay holder - pure PERIODIC_TRIGGER_SPELL, no script; cast on self by spell_warr_thunder_clap only when Thunderstruck rank 3 (200053) is talented",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': '', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': '', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'Name_Lang_enUS': 'Thunderstruck', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 4, 'SpellLevel': 1, 'SpellPriority': 50},
)


# --- talent tabs (source/talents/warrior.yaml) ---

arms_161_tab = tab(
    id=161,
    name='Arms',
    class_mask=1,
    spell_icon_id=514,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 24},
)

protection_163_tab = tab(
    id=163,
    name='Protection',
    class_mask=1,
    order_index=2,
    spell_icon_id=1463,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 570},
)

fury_164_tab = tab(
    id=164,
    name='Fury',
    class_mask=1,
    order_index=1,
    spell_icon_id=561,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 346},
)


# --- talents (source/talents/warrior.yaml) ---

granted_by_talent(
    id=121,
    tab=arms_161_tab,
    tier=2,
    column=3,
    ranks=[deep_wounds_12834, deep_wounds_12849, deep_wounds_12867],
    player_castable=False,
    depends_on={'talent_id': 662, 'rank': 1},
)

granted_by_talent(
    id=123,
    tab=arms_161_tab,
    tier=4,
    column=3,
    ranks=[12281, 12812, 12813, 12814, 12815],
    player_castable=False,
)

granted_by_talent(
    id=124,
    tab=arms_161_tab,
    tier=0,
    column=0,
    ranks=[improved_heroic_strike_12282, improved_heroic_strike_12663, improved_heroic_strike_12664],
    player_castable=False,
)

granted_by_talent(
    id=125,
    tab=arms_161_tab,
    tier=4,
    column=2,
    ranks=[12284, 12701, 12702, 12703, 12704],
    player_castable=False,
)

granted_by_talent(
    id=126,
    tab=arms_161_tab,
    tier=1,
    column=0,
    ranks=[improved_charge_12285, improved_charge_12697],
    player_castable=False,
)

granted_by_talent(
    id=127,
    tab=arms_161_tab,
    tier=0,
    column=2,
    ranks=[improved_rend_12286, improved_rend_12658],
    player_castable=False,
)

granted_by_talent(
    id=128,
    tab=arms_161_tab,
    tier=1,
    column=2,
    ranks=[tactical_mastery_12295, tactical_mastery_12676, tactical_mastery_12677],
    player_castable=False,
)

granted_by_talent(
    id=129,
    tab=arms_161_tab,
    tier=5,
    column=2,
    ranks=[improved_hamstring_12289, improved_hamstring_12668, improved_hamstring_23695],
    player_castable=False,
)

granted_by_talent(
    id=130,
    tab=arms_161_tab,
    tier=0,
    column=1,
    ranks=[16462, 16463, 16464, 16465, 16466],
    player_castable=False,
)

granted_by_talent(
    id=131,
    tab=arms_161_tab,
    tier=2,
    column=0,
    ranks=[improved_overpower_12290, improved_overpower_12963],
    player_castable=False,
)

granted_by_talent(
    id=132,
    tab=arms_161_tab,
    tier=4,
    column=0,
    ranks=[12700, 12781, 12783, 12784, 12785],
    player_castable=False,
)

granted_by_talent(
    id=133,
    tab=arms_161_tab,
    tier=4,
    column=1,
    ranks=[sweeping_strikes_12328],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=134,
    tab=arms_161_tab,
    tier=5,
    column=0,
    ranks=[weapon_mastery_20504, 20505],
    player_castable=False,
)

granted_by_talent(
    id=135,
    tab=arms_161_tab,
    tier=6,
    column=1,
    ranks=[mortal_strike_12294],
    player_castable=False,
    depends_on={'talent_id': 133, 'rank': 0},
    flags=1,
)

granted_by_talent(
    id=136,
    tab=arms_161_tab,
    tier=3,
    column=1,
    ranks=[12163, 12711, 12712],
    player_castable=False,
)

granted_by_talent(
    id=137,
    tab=arms_161_tab,
    tier=2,
    column=1,
    ranks=[12296],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=141,
    tab=protection_163_tab,
    tier=0,
    column=2,
    ranks=[improved_thunder_clap_12287, improved_thunder_clap_12665, improved_thunder_clap_12666],
    player_castable=False,
)

granted_by_talent(
    id=142,
    tab=protection_163_tab,
    tier=0,
    column=0,
    ranks=[improved_bloodrage_12301, improved_bloodrage_12818],
    player_castable=False,
)

granted_by_talent(
    id=144,
    tab=protection_163_tab,
    tier=1,
    column=0,
    ranks=[incite_50685, incite_50686, incite_50687],
    player_castable=False,
)

granted_by_talent(
    id=146,
    tab=protection_163_tab,
    tier=3,
    column=1,
    ranks=[puncture_12308, puncture_12810, puncture_12811],
    player_castable=False,
)

granted_by_talent(
    id=147,
    tab=protection_163_tab,
    tier=2,
    column=1,
    ranks=[improved_revenge_12797, improved_revenge_12799],
    player_castable=False,
)

granted_by_talent(
    id=148,
    tab=protection_163_tab,
    tier=6,
    column=1,
    ranks=[50720],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=149,
    tab=protection_163_tab,
    tier=4,
    column=2,
    ranks=[gag_order_12311, gag_order_12958],
    player_castable=False,
)

granted_by_talent(
    id=150,
    tab=protection_163_tab,
    tier=4,
    column=0,
    ranks=[improved_disciplines_12312, improved_disciplines_12803],
    player_castable=False,
)

granted_by_talent(
    id=152,
    tab=protection_163_tab,
    tier=4,
    column=1,
    ranks=[concussion_blow_12809],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=153,
    tab=protection_163_tab,
    tier=2,
    column=0,
    ranks=[last_stand_12975],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=154,
    tab=fury_164_tab,
    tier=2,
    column=3,
    ranks=[commanding_presence_12318, commanding_presence_12857, commanding_presence_12858, commanding_presence_12860, commanding_presence_12861],
    player_castable=False,
)

granted_by_talent(
    id=155,
    tab=fury_164_tab,
    tier=3,
    column=2,
    ranks=[12317, 13045, 13046, 13047, 13048],
    player_castable=False,
)

granted_by_talent(
    id=156,
    tab=fury_164_tab,
    tier=5,
    column=2,
    ranks=[12319, 12971, 12972, 12973, 12974],
    player_castable=False,
)

granted_by_talent(
    id=157,
    tab=fury_164_tab,
    tier=0,
    column=2,
    ranks=[12320, 12852, 12853, 12855, 12856],
    player_castable=False,
)

granted_by_talent(
    id=158,
    tab=fury_164_tab,
    tier=0,
    column=1,
    ranks=[booming_voice_12321, booming_voice_12835],
    player_castable=False,
)

granted_by_talent(
    id=159,
    tab=fury_164_tab,
    tier=1,
    column=2,
    ranks=[12322, 12999, 13000, 13001, 13002],
    player_castable=False,
)

granted_by_talent(
    id=160,
    tab=fury_164_tab,
    tier=2,
    column=1,
    ranks=[piercing_howl_12323],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=161,
    tab=fury_164_tab,
    tier=1,
    column=1,
    ranks=[improved_demoralizing_shout_12324, improved_demoralizing_shout_12876, improved_demoralizing_shout_12877, improved_demoralizing_shout_12878, improved_demoralizing_shout_12879],
    player_castable=False,
)

granted_by_talent(
    id=165,
    tab=fury_164_tab,
    tier=4,
    column=1,
    ranks=[death_wish_12292],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=166,
    tab=fury_164_tab,
    tier=2,
    column=0,
    ranks=[improved_cleave_12329, improved_cleave_12950, improved_cleave_20496],
    player_castable=False,
)

granted_by_talent(
    id=167,
    tab=fury_164_tab,
    tier=6,
    column=1,
    ranks=[bloodthirst_23881],
    player_castable=False,
    depends_on={'talent_id': 165, 'rank': 0},
    flags=1,
)

granted_by_talent(
    id=641,
    tab=arms_161_tab,
    tier=1,
    column=1,
    ranks=[12300, 12959, 12960],
    player_castable=False,
)

granted_by_talent(
    id=661,
    tab=fury_164_tab,
    tier=2,
    column=2,
    ranks=[16487, 16489, 16492],
    player_castable=False,
)

granted_by_talent(
    id=662,
    tab=arms_161_tab,
    tier=2,
    column=2,
    ranks=[impale_16493, impale_16494],
    player_castable=False,
)

granted_by_talent(
    id=702,
    tab=protection_163_tab,
    tier=5,
    column=1,
    ranks=[16538, 16539, 16540, 16541, 16542],
    player_castable=False,
)

granted_by_talent(
    id=1541,
    tab=fury_164_tab,
    tier=5,
    column=0,
    ranks=[improved_berserker_rage_20500, improved_berserker_rage_20501],
    player_castable=False,
)

granted_by_talent(
    id=1542,
    tab=fury_164_tab,
    tier=3,
    column=1,
    ranks=[improved_execute_20502, improved_execute_20503],
    player_castable=False,
)

granted_by_talent(
    id=1543,
    tab=fury_164_tab,
    tier=4,
    column=2,
    ranks=[improved_intercept_29888, improved_intercept_29889],
    player_castable=False,
)

granted_by_talent(
    id=1581,
    tab=fury_164_tab,
    tier=3,
    column=0,
    ranks=[dual_wield_specialization_23584, dual_wield_specialization_23585, dual_wield_specialization_23586, dual_wield_specialization_23587, dual_wield_specialization_23588],
    player_castable=False,
)

granted_by_talent(
    id=1652,
    tab=protection_163_tab,
    tier=5,
    column=0,
    ranks=[iron_temper_29593, iron_temper_29594],
    player_castable=False,
)

granted_by_talent(
    id=1654,
    tab=protection_163_tab,
    tier=2,
    column=2,
    ranks=[shield_mastery_29598, shield_mastery_29599],
    player_castable=False,
)

granted_by_talent(
    id=1655,
    tab=fury_164_tab,
    tier=6,
    column=3,
    ranks=[improved_whirlwind_29721, improved_whirlwind_29776],
    player_castable=False,
)

granted_by_talent(
    id=1657,
    tab=fury_164_tab,
    tier=4,
    column=0,
    ranks=[29590, 29591, 29592],
    player_castable=False,
)

granted_by_talent(
    id=1658,
    tab=fury_164_tab,
    tier=7,
    column=3,
    ranks=[improved_berserker_stance_29759, improved_berserker_stance_29760, improved_berserker_stance_29761, improved_berserker_stance_29762, improved_berserker_stance_29763],
    player_castable=False,
)

granted_by_talent(
    id=1659,
    tab=fury_164_tab,
    tier=8,
    column=1,
    ranks=[rampage_29801],
    player_castable=False,
    depends_on={'talent_id': 167, 'rank': 0},
    flags=1,
)

granted_by_talent(
    id=1660,
    tab=protection_163_tab,
    tier=6,
    column=2,
    ranks=[focused_rage_29787, focused_rage_29790, focused_rage_29792],
    player_castable=False,
)

granted_by_talent(
    id=1661,
    tab=arms_161_tab,
    tier=8,
    column=1,
    ranks=[endless_rage_29623],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=1662,
    tab=arms_161_tab,
    tier=8,
    column=0,
    ranks=[29723, 29725, 29724],
    player_castable=False,
)

granted_by_talent(
    id=1663,
    tab=arms_161_tab,
    tier=6,
    column=0,
    ranks=[second_wind_29834, second_wind_29838],
    player_castable=False,
)

granted_by_talent(
    id=1664,
    tab=arms_161_tab,
    tier=8,
    column=2,
    ranks=[blood_frenzy_29836, blood_frenzy_29859],
    player_castable=False,
)

granted_by_talent(
    id=1666,
    tab=protection_163_tab,
    tier=0,
    column=3,
    ranks=[devastate_20243],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=1824,
    tab=arms_161_tab,
    tier=7,
    column=1,
    ranks=[improved_mortal_strike_35446, improved_mortal_strike_35448, improved_mortal_strike_35449],
    player_castable=False,
    depends_on={'talent_id': 135, 'rank': 0},
)

granted_by_talent(
    id=1859,
    tab=arms_161_tab,
    tier=5,
    column=3,
    ranks=[46854, 46855],
    player_castable=False,
)

granted_by_talent(
    id=1860,
    tab=arms_161_tab,
    tier=7,
    column=2,
    ranks=[unrelenting_assault_46859, unrelenting_assault_46860],
    player_castable=False,
)

granted_by_talent(
    id=1862,
    tab=arms_161_tab,
    tier=6,
    column=2,
    ranks=[46865, 46866],
    player_castable=False,
)

granted_by_talent(
    id=1863,
    tab=arms_161_tab,
    tier=10,
    column=1,
    ranks=[bladestorm_46924],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=1864,
    tab=fury_164_tab,
    tier=6,
    column=0,
    ranks=[intensify_rage_46908, intensify_rage_46909, intensify_rage_56924],
    player_castable=False,
)

granted_by_talent(
    id=1865,
    tab=fury_164_tab,
    tier=7,
    column=0,
    ranks=[46910, 46911],
    player_castable=False,
)

granted_by_talent(
    id=1866,
    tab=fury_164_tab,
    tier=8,
    column=2,
    ranks=[bloodsurge_46913, bloodsurge_46914, bloodsurge_46915],
    player_castable=False,
    depends_on={'talent_id': 167, 'rank': 0},
)

granted_by_talent(
    id=1867,
    tab=fury_164_tab,
    tier=10,
    column=1,
    ranks=[titan_s_grip_46917],
    player_castable=False,
)

granted_by_talent(
    id=1868,
    tab=fury_164_tab,
    tier=8,
    column=0,
    ranks=[60970],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=1870,
    tab=protection_163_tab,
    tier=7,
    column=1,
    ranks=[safeguard_46945, safeguard_46949],
    player_castable=False,
)

granted_by_talent(
    id=1871,
    tab=protection_163_tab,
    tier=9,
    column=0,
    ranks=[sword_and_board_46951, sword_and_board_46952, sword_and_board_46953],
    player_castable=False,
)

granted_by_talent(
    id=1872,
    tab=protection_163_tab,
    tier=10,
    column=1,
    ranks=[shockwave_46968],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=1893,
    tab=protection_163_tab,
    tier=6,
    column=0,
    ranks=[critical_block_47294, critical_block_47295, critical_block_47296],
    player_castable=False,
)

granted_by_talent(
    id=2231,
    tab=arms_161_tab,
    tier=9,
    column=1,
    ranks=[46867, 56611, 56612, 56613, 56614],
    player_castable=False,
)

granted_by_talent(
    id=2232,
    tab=arms_161_tab,
    tier=3,
    column=2,
    ranks=[taste_for_blood_56636, taste_for_blood_56637, taste_for_blood_56638],
    player_castable=False,
)

granted_by_talent(
    id=2233,
    tab=arms_161_tab,
    tier=6,
    column=3,
    ranks=[improved_slam_12862, improved_slam_12330],
    player_castable=False,
)

granted_by_talent(
    id=2234,
    tab=fury_164_tab,
    tier=9,
    column=1,
    ranks=[unending_fury_56927, unending_fury_56929, unending_fury_56930, unending_fury_56931, unending_fury_56932],
    player_castable=False,
)

granted_by_talent(
    id=2246,
    tab=protection_163_tab,
    tier=9,
    column=1,
    ranks=[damage_shield_58872, damage_shield_58874],
    player_castable=False,
)

granted_by_talent(
    id=2250,
    tab=fury_164_tab,
    tier=0,
    column=0,
    ranks=[armored_to_the_teeth_61216, armored_to_the_teeth_61221, armored_to_the_teeth_61222],
    player_castable=False,
)

granted_by_talent(
    id=2283,
    tab=arms_161_tab,
    tier=7,
    column=0,
    ranks=[juggernaut_64976],
    player_castable=False,
)

granted_by_talent(
    id=1601,
    tab=protection_163_tab,
    tier=0,
    column=1,
    ranks=[shield_specialization_200031, shield_specialization_200032, shield_specialization_200033],
    player_castable=False,
)

granted_by_talent(
    id=138,
    tab=protection_163_tab,
    tier=1,
    column=2,
    ranks=[unbridled_wrath_200034, unbridled_wrath_200035, unbridled_wrath_200036],
    player_castable=False,
)

granted_by_talent(
    id=140,
    tab=protection_163_tab,
    tier=2,
    column=3,
    ranks=[firm_grip_200038, firm_grip_200039, firm_grip_200040],
    player_castable=False,
)

granted_by_talent(
    id=2247,
    tab=protection_163_tab,
    tier=3,
    column=2,
    ranks=[shield_cover_200041, shield_cover_200042, shield_cover_200043],
    player_castable=False,
)

granted_by_talent(
    id=151,
    tab=protection_163_tab,
    tier=9,
    column=2,
    ranks=[thunderstruck_200051, thunderstruck_200052, thunderstruck_200053],
    player_castable=False,
)

granted_by_talent(
    id=1653,
    tab=protection_163_tab,
    tier=7,
    column=0,
    ranks=[resolve_200046, resolve_200047, resolve_200048],
    player_castable=False,
)

granted_by_talent(
    id=2236,
    tab=protection_163_tab,
    tier=8,
    column=0,
    ranks=[unrelenting_200049],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=60003,
    tab=protection_163_tab,
    tier=1,
    column=1,
    ranks=[blood_and_thunder_200054, blood_and_thunder_200055],
    player_castable=False,
)

granted_by_talent(
    id=60004,
    tab=protection_163_tab,
    tier=3,
    column=0,
    ranks=[reprisal_200056, reprisal_200057],
    player_castable=False,
)

granted_by_talent(
    id=60005,
    tab=protection_163_tab,
    tier=5,
    column=2,
    ranks=[storm_s_bulwark_200058, storm_s_bulwark_200059, storm_s_bulwark_200060],
    player_castable=False,
)

granted_by_talent(
    id=60006,
    tab=protection_163_tab,
    tier=8,
    column=1,
    ranks=[shield_discipline_200062, shield_discipline_200063],
    player_castable=False,
)
