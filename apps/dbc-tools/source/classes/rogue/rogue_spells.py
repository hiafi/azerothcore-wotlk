"""
Rogue - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/rogue.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .rogue_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, School
from lib.dsl.registry import spell
from .rogue_trigger_spells import mutilate_27576, mutilate_5374, vanish_11327


backstab_53 = spell(
    id=53,
    name='Backstab',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=60,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=9, points_per_level=2.5, implicit_target_a=6),
        Effect(type=31, base_points=149, implicit_target_a=6),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=243,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1→level-60 slope (anchor 25300, rank 9); coefficient/cast_time_ms/mana_cost_pct from max rank (48657, rank 12); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 1048576, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Backstab the target, causing $m2% weapon damage plus ${$m1*1.5} to the target.  Must be behind the target.  Requires a dagger in the main hand.  Awards $s3 combo $lpoint:points;.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 32768, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 8388612, 'SpellClassSet': 8, 'SpellLevel': 4, 'SpellPriority': 50, 'SpellVisualID_1': 155, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


kidney_shot_408 = spell(
    id=408,
    name='Kidney Shot',
    school=School.NORMAL,
    mechanic=Mechanic.STUN,
    attributes=327696,
    category=270,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=20000,
    power_type=PowerType.ENERGY,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=499,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1→level-60 slope (anchor 8643, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (8643, rank 2); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 4456960, 'AttributesEx3': 1024, 'AttributesEx4': 2056, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that stuns the target.  Lasts longer per combo point:\r\n   1 point  : 1 second\r\n   2 points: 2 seconds\r\n   3 points: 3 seconds\r\n   4 points: 4 seconds\r\n   5 points: 5 seconds', 'DurationIndex': 187, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 2097152, 'SpellClassSet': 8, 'SpellLevel': 30, 'SpellVisualID_1': 679, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


garrote_703 = spell(
    id=703,
    name='Garrote',
    school=School.NORMAL,
    mechanic=15,
    attributes=2555920,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=18000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, points_per_level=1.108695652173913, mechanic=15, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=1330),
    ],
    spell_icon_id=498,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 14); RealPointsPerLevel from rank1→level-60 slope (anchor 11290, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48676, rank 10); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana); effect3 (Garrote - Silence trigger, spell 1330) added: absent from rank 1, introduced at rank 7 (26839) and present at every rank through max; preserved on the survivor per explicit decision, flat (single-rank data point, no growth to derive a slope from)',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 1048576, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 damage every $t1 seconds.', 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Garrote the enemy, causing ${($m1+$AP*0.07)*6} damage over $d, increased by your attack power.  Must be stealthed and behind the target.  Awards $s2 combo $lpoint:points;.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 536870912, 'SpellClassMask_1': 256, 'SpellClassSet': 8, 'SpellLevel': 14, 'SpellVisualID_1': 757, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


distract_1725 = spell(
    id=1725,
    name='Distract',
    school=School.NORMAL,
    mechanic=4,
    attributes=1074003984,
    category=22,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    power_type=PowerType.ENERGY,
    mana_cost=30,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=69, base_points=9, implicit_target_a=16, radius_yards=10.0),
    ],
    spell_icon_id=1478,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 132384, 'AttributesEx3': 131072, 'AuraDescription_Lang_Mask': 16712188, 'AuraInterruptFlags': 3, 'BaseLevel': 22, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Throws a distraction, attracting the attention of all nearby monsters for $s1 seconds.  Does not break stealth.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 4096, 'SpellClassSet': 8, 'SpellLevel': 22, 'SpellVisualID_1': 261, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'Targets': 64},
)


sinister_strike_1752 = spell(
    id=1752,
    name='Sinister Strike',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=45,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=2, points_per_level=1.1016949152542372, implicit_target_a=6),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=130,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope (anchor 11294, rank 8); coefficient/cast_time_ms/mana_cost_pct from max rank (48638, rank 12); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'An instant strike that causes $m1 damage in addition to $<percent>% of your normal weapon damage.  Awards $s2 combo $lpoint:points;.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 8388610, 'SpellClassSet': 8, 'SpellDescriptionVariableID': 171, 'SpellLevel': 1, 'SpellVisualID_1': 253, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


kick_1766 = spell(
    id=1766,
    name='Kick',
    school=School.NORMAL,
    attributes=327696,
    category=88,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.ENERGY,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.INTERRUPT_CAST, die_sides=0, mechanic=26, implicit_target_a=6),
    ],
    spell_icon_id=246,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 8, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A quick kick that interrupts spellcasting and prevents any spell in that school from being cast for $d.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 16, 'SpellClassSet': 8, 'SpellLevel': 12, 'SpellVisualID_1': 90},
)


gouge_1776 = spell(
    id=1776,
    name='Gouge',
    school=School.NORMAL,
    attributes=1376272,
    category=33,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.ENERGY,
    mana_cost=45,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=6),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, mechanic=Mechanic.KNOCKOUT, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=245,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134479872, 'AttributesEx3': 1032, 'AttributesEx4': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Incapacitated.', 'AuraInterruptFlags': 2, 'BaseLevel': 6, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes ${1+0.21*$AP} damage, incapacitating the opponent for $d, and turns off your attack.  Target must be facing you.  Any damage caused will revive the target.  Awards $s2 combo $lpoint:points;.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 8, 'SpellClassSet': 8, 'SpellLevel': 6, 'SpellVisualID_1': 256, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


stealth_1784 = spell(
    id=1784,
    name='Stealth',
    school=School.NORMAL,
    dispel=DispelType.STEALTH,
    attributes=437583888,
    category=38,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=30),
        Effect(type=EffectType.APPLY_AURA, base_points=4, points_per_level=5.0, implicit_target_a=1, apply_aura=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=250,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 30, 'AttributesEx': 16, 'AttributesEx2': 2097152, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stealthed.  Movement slowed by $s3%.', 'AuraInterruptFlags': 146436, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows the rogue to sneak around, but reduces your speed by $s3%.  Lasts until cancelled.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeCasterAuraState': 12, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'SpellClassMask_1': 4194304, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellVisualID_1': 184, 'StartRecoveryCategory': 1178},
)


pick_lock_1804 = spell(
    id=1804,
    name='Pick Lock',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=5000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.OPEN_LOCK, base_points=4, points_per_level=5.0, implicit_target_a=26, misc_value=1),
    ],
    spell_icon_id=106,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 6, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows opening of locked chests and doors.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'EquippedItemSubclass': -1, 'InterruptFlags': 31, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 16384, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellVisualID_1': 104},
)


cheap_shot_1833 = spell(
    id=1833,
    name='Cheap Shot',
    school=School.NORMAL,
    mechanic=Mechanic.STUN,
    attributes=2555920,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=60,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
        Effect(type=EffectType.ADD_COMBO_POINTS, base_points=1, implicit_target_a=6),
    ],
    spell_icon_id=244,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134479872, 'AttributesEx2': 1048576, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Stuns the target for $d.  Must be stealthed.  Awards $s2 combo $lpoint:points;.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 536870912, 'SpellClassMask_1': 1024, 'SpellClassSet': 8, 'SpellLevel': 26, 'SpellVisualID_1': 266, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


disarm_trap_1842 = spell(
    id=1842,
    name='Disarm Trap',
    school=School.NORMAL,
    attributes=196624,
    cast_time_ms=1000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.OPEN_LOCK, base_points=199, points_per_level=5.0, implicit_target_a=23, misc_value=4),
    ],
    spell_icon_id=228,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131104, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 4, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Disarm a hostile trap.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ShapeshiftMask': 536870912, 'SpellClassMask_2': 8192, 'SpellClassSet': 8, 'SpellLevel': 30, 'SpellVisualID_1': 252, 'Targets': 16384},
)


vanish_1856 = spell(
    id=1856,
    name='Vanish',
    school=School.NORMAL,
    attributes=135594000,
    category=39,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=180000,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=vanish_11327.id),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=18461),
        Effect(type=79, base_points=-1, implicit_target_a=1),
    ],
    spell_icon_id=252,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 22); RealPointsPerLevel from rank1→level-60 slope (anchor 1857, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (26889, rank 3); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'ActiveIconID': 30, 'AttributesEx': 1056, 'AttributesEx2': 2, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Improved stealth.', 'AuraInterruptFlags': 15367, 'BaseLevel': 22, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows the rogue to vanish from sight, entering an improved stealth mode for $11327d.  Also breaks movement impairing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeCasterAuraState': 12, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 139944, 'RangeIndex': 1, 'SpellClassMask_1': 2048, 'SpellClassSet': 8, 'SpellLevel': 22, 'SpellVisualID_1': 255},
)


rupture_1943 = spell(
    id=1943,
    name='Rupture',
    school=School.NORMAL,
    mechanic=15,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, points_per_level=1.3, mechanic=15, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=500,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor 11275, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48672, rank 9); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 1049088, 'AttributesEx3': 1024, 'AttributesEx4': 8, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Causes damage every $t1 seconds.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that causes damage over time, increased by your attack power.  Lasts longer per combo point:\r\n   1 point  : ${($m1+$b1*1+0.015*$AP)*4} damage over $<dur1> secs\r\n   2 points: ${($m1+$b1*2+0.024*$AP)*5} damage over $<dur2> secs\r\n   3 points: ${($m1+$b1*3+0.03*$AP)*6} damage over $<dur3> secs\r\n   4 points: ${($m1+$b1*4+0.03428571*$AP)*7} damage over $<dur4> secs\r\n   5 points: ${($m1+$b1*5+0.0375*$AP)*8} damage over $<dur5> secs', 'DurationIndex': 553, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_1': 2.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 1048576, 'SpellClassSet': 8, 'SpellDescriptionVariableID': 63, 'SpellLevel': 20, 'SpellVisualID_1': 250, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


feint_1966 = spell(
    id=1966,
    name='Feint',
    school=School.NORMAL,
    attributes=327696,
    category=82,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.ENERGY,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.THREAT, base_points=-151, points_per_level=-14.772727272727273, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=229, misc_value=127),
    ],
    spell_icon_id=539,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 16); RealPointsPerLevel from rank1→level-60 slope (anchor 25302, rank 5); coefficient/cast_time_ms/mana_cost_pct from max rank (48659, rank 8); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana); effect2 (AoE damage avoidance, -51%) added: absent from rank 1, introduced only at max rank (48659); preserved on the survivor per explicit decision, flat (single-rank data point)',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Performs a feint, causing no damage but lowering your threat by a small amount, making the enemy less likely to attack you.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 134217728, 'SpellClassSet': 8, 'SpellLevel': 16, 'SpellVisualID_1': 738, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


blind_2094 = spell(
    id=2094,
    name='Blind',
    school=School.NORMAL,
    mechanic=Mechanic.DISORIENTED,
    attributes=1074855952,
    category=1187,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=20000,
    power_type=PowerType.ENERGY,
    mana_cost=30,
    mana_cost_pct=0,
    range_yards=10.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-61, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_CONFUSE),
    ],
    spell_icon_id=48,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 65536, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Disoriented.', 'AuraInterruptFlags': 4718594, 'BaseLevel': 34, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blinds the target, causing it to wander disoriented for up to $d.  Any damage caused will remove the effect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'SpellClassMask_1': 16777216, 'SpellClassSet': 8, 'SpellLevel': 34, 'SpellVisualID_1': 3440, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


eviscerate_2098 = spell(
    id=2098,
    name='Eviscerate',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, points_per_level=0.8983050847457628, die_sides=5, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=514,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope (anchor 31016, rank 9); coefficient/cast_time_ms/mana_cost_pct from max rank (48668, rank 12); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 1049088, 'AttributesEx3': 1024, 'AttributesEx4': 8, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that causes damage per combo point:\r\n   1 point  : ${$m1+(($b1*1)+$AP*0.03)*$<mult>}-${$M1+(($b1*1)+$AP*0.07)*$<mult>} damage\r\n   2 points: ${$m1+(($b1*2)+$AP*0.06)*$<mult>}-${$M1+(($b1*2)+$AP*0.14)*$<mult>} damage\r\n   3 points: ${$m1+(($b1*3)+$AP*0.09)*$<mult>}-${$M1+(($b1*3)+$AP*0.21)*$<mult>} damage\r\n   4 points: ${$m1+(($b1*4)+$AP*0.12)*$<mult>}-${$M1+(($b1*4)+$AP*0.28)*$<mult>} damage\r\n   5 points: ${$m1+(($b1*5)+$AP*0.15)*$<mult>}-${$M1+(($b1*5)+$AP*0.35)*$<mult>} damage', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_1': 5.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 8519680, 'SpellClassSet': 8, 'SpellDescriptionVariableID': 169, 'SpellLevel': 1, 'SpellVisualID_1': 671, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


deadly_poison_2823 = spell(
    id=2823,
    name='Deadly Poison',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=7),
    ],
    spell_icon_id=513,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1→level-60 slope (anchor 25351, rank 5); coefficient/cast_time_ms/mana_cost_pct from max rank (57973, rank 9); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana); effect1 (type 54, ENCHANT_ITEM_TEMPORARY-family) left untouched -- base_points unused by that effect handler, not a real scaling quantity',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $2823h% chance of poisoning the enemy for ${$2818m1*4+0.12*$AP} Nature damage over $2818d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 30, 'SpellVisualID_1': 12720, 'Targets': 16},
)


deadly_poison_ii_2824 = spell(
    id=2824,
    name='Deadly Poison II',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=599, misc_value=8),
    ],
    spell_icon_id=513,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 38, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $2824h% chance of poisoning the enemy for ${$2819m1*4+0.12*$AP} Nature damage over $2819d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 38, 'SpellVisualID_1': 12720, 'Targets': 16},
)


sprint_2983 = spell(
    id=2983,
    name='Sprint',
    school=School.NORMAL,
    attributes=65552,
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
        Effect(type=EffectType.APPLY_AURA, base_points=49, points_per_level=0.4, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=516,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1→level-60 slope (anchor 11305, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (11305, rank 3); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed increased by $s1%.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the rogue's movement speed by $s1% for $d.  Does not break stealth.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 64, 'SpellClassSet': 8, 'SpellLevel': 10, 'SpellVisualID_1': 6},
)


slice_and_dice_5171 = spell(
    id=5171,
    name='Slice and Dice',
    school=School.NORMAL,
    attributes=537198608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=19, points_per_level=0.4, implicit_target_a=1, apply_aura=138),
    ],
    spell_icon_id=515,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1→level-60 slope (anchor 6774, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (6774, rank 2); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 4195360, 'AttributesEx2': 4, 'AttributesEx3': 1342439424, 'AttributesEx4': 16, 'AttributesEx6': 8388612, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attack speed increased by $s2%.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that increases melee attack speed by $s2%.  Lasts longer per combo point:\r\n   1 point  : ${(9+$<glyph>)*(100+$<mult>)/100} seconds\r\n   2 points: ${(12+$<glyph>)*(100+$<mult>)/100} seconds\r\n   3 points: ${(15+$<glyph>)*(100+$<mult>)/100} seconds\r\n   4 points: ${(18+$<glyph>)*(100+$<mult>)/100} seconds\r\n   5 points: ${(21+$<glyph>)*(100+$<mult>)/100} seconds', 'DurationIndex': 185, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'SpellClassMask_1': 262144, 'SpellClassSet': 8, 'SpellDescriptionVariableID': 164, 'SpellLevel': 10, 'SpellPriority': 50, 'SpellVisualID_1': 254, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


evasion_5277 = spell(
    id=5277,
    name='Evasion',
    school=School.NORMAL,
    attributes=65552,
    category=66,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=180000,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=49),
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=1, apply_aura=185),
    ],
    spell_icon_id=178,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1→level-60 slope (anchor 26669, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (26669, rank 2); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana); effect2 (ranged attacker hit chance, -26%) added: absent from rank 1, introduced only at rank 2/max (26669); preserved on the survivor per explicit decision, flat (single-rank data point)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases dodge chance by $s1%.', 'BaseLevel': 8, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "The rogue's dodge chance will increase by $s1% for $d.", 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 32, 'SpellClassSet': 8, 'SpellLevel': 8, 'SpellVisualID_1': 72},
)


shiv_5938 = spell(
    id=5938,
    name='Shiv',
    school=School.NORMAL,
    attributes=2424848,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=6),
    ],
    spell_icon_id=1834,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx2': 537919488, 'AttributesEx3': 17235968, 'AttributesEx4': 1025, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 70, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Performs an instant off-hand weapon attack that automatically applies the poison from your off-hand weapon to the target.  Slower weapons require more Energy.  Neither Shiv nor the poison it applies can be a critical strike.  Awards 1 combo point.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 536870912, 'SpellClassSet': 8, 'SpellLevel': 70, 'SpellVisualID_1': 8056, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


sap_6770 = spell(
    id=6770,
    name='Sap',
    school=School.NORMAL,
    mechanic=Mechanic.SAPPED,
    attributes=3604496,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=65,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=25000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=249,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1→level-60 slope (anchor 11297, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (51724, rank 4); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 134481184, 'AttributesEx3': 131073, 'AttributesEx4': 8388608, 'AttributesEx5': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Sapped.', 'AuraInterruptFlags': 4718594, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Incapacitates the target for up to $d.  Must be stealthed.  Only works on Humanoids that are not in combat.  Any damage caused will revive the target.  Only 1 target may be sapped at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcTypeMask': 69648, 'RangeIndex': 2, 'ShapeshiftMask': 536870912, 'SpellClassMask_1': 128, 'SpellClassSet': 8, 'SpellLevel': 10, 'SpellVisualID_1': 257, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'TargetCreatureType': 64},
)


expose_armor_8647 = spell(
    id=8647,
    name='Expose Armor',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=6, apply_aura=101, misc_value=1),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=563,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1049088, 'AttributesEx3': 1024, 'AttributesEx4': 8, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Armor decreased by $s1%.', 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that exposes the target, reducing armor by $s1% and lasting longer per combo point:\r\n   1 point  : $?s56803[18][6] sec.\r\n   2 points: $?s56803[24][12] sec.\r\n   3 points: $?s56803[30][18] sec.\r\n   4 points: $?s56803[36][24] sec.\r\n   5 points: $?s56803[42][30] sec.', 'DurationIndex': 588, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 524288, 'SpellClassSet': 8, 'SpellLevel': 14, 'SpellVisualID_1': 3441, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


ambush_8676 = spell(
    id=8676,
    name='Ambush',
    school=School.NORMAL,
    attributes=2555920,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=60,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=27, points_per_level=2.0952380952380953, implicit_target_a=6),
        Effect(type=31, base_points=274, implicit_target_a=6),
        Effect(type=EffectType.ADD_COMBO_POINTS, base_points=1, implicit_target_a=6),
    ],
    spell_icon_id=856,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 18); RealPointsPerLevel from rank1→level-60 slope (anchor 11269, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48691, rank 10); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 1048576, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Ambush the target, causing $m2% weapon damage plus ${$m1*2.75} to the target.  Must be stealthed and behind the target.  Requires a dagger in the main hand.  Awards $s3 combo $lpoint:points;.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 32768, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 536870912, 'SpellClassMask_1': 8389120, 'SpellClassSet': 8, 'SpellLevel': 18, 'SpellPriority': 50, 'SpellVisualID_1': 155, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


instant_poison_8679 = spell(
    id=8679,
    name='Instant Poison',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=323),
    ],
    spell_icon_id=247,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor 11340, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (57968, rank 9); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana); effect1 (type 54, ENCHANT_ITEM_TEMPORARY-family) left untouched -- base_points unused by that effect handler, not a real scaling quantity',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$8680m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 20, 'SpellVisualID_1': 12720, 'Targets': 16},
)


instant_poison_ii_8686 = spell(
    id=8686,
    name='Instant Poison II',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=324),
    ],
    spell_icon_id=247,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 28, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$8685m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 28, 'SpellVisualID_1': 12720, 'Targets': 16},
)


instant_poison_iii_8688 = spell(
    id=8688,
    name='Instant Poison III',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=325),
    ],
    spell_icon_id=247,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 36, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$8689m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 36, 'SpellVisualID_1': 12720, 'Targets': 16},
)


instant_poison_iv_11338 = spell(
    id=11338,
    name='Instant Poison IV',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=623),
    ],
    spell_icon_id=247,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 44, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$11335m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 44, 'SpellVisualID_1': 12720, 'Targets': 16},
)


instant_poison_v_11339 = spell(
    id=11339,
    name='Instant Poison V',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=624),
    ],
    spell_icon_id=247,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 52, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$11336m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 52, 'SpellVisualID_1': 12720, 'Targets': 16},
)


instant_poison_vi_11340 = spell(
    id=11340,
    name='Instant Poison VI',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=625),
    ],
    spell_icon_id=247,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$11337m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 60, 'SpellVisualID_1': 12720, 'Targets': 16},
)


deadly_poison_iii_11355 = spell(
    id=11355,
    name='Deadly Poison III',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=599, misc_value=626),
    ],
    spell_icon_id=513,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 46, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $11355h% chance of poisoning the enemy for ${$11353m1*4+0.12*$AP} Nature damage over $11353d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 46, 'SpellVisualID_1': 12720, 'Targets': 16},
)


deadly_poison_iv_11356 = spell(
    id=11356,
    name='Deadly Poison IV',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=599, misc_value=627),
    ],
    spell_icon_id=513,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 54, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $11356h% chance of poisoning the enemy for ${$11354m1*4+0.12*$AP} Nature damage over $11354d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 54, 'SpellVisualID_1': 12720, 'Targets': 16},
)


wound_poison_13219 = spell(
    id=13219,
    name='Wound Poison',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=703),
    ],
    spell_icon_id=1496,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 32); RealPointsPerLevel from rank1→level-60 slope (anchor 13227, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (57978, rank 7); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana); effect1 (type 54, ENCHANT_ITEM_TEMPORARY-family) left untouched -- base_points unused by that effect handler, not a real scaling quantity',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 32, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy, causing ${$13218m2+0.04*$AP} Nature damage and reducing all healing effects used on them by $13218s1% for $13218d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 8, 'SpellLevel': 32, 'SpellVisualID_1': 12720, 'Targets': 16},
)


wound_poison_ii_13225 = spell(
    id=13225,
    name='Wound Poison II',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=704),
    ],
    spell_icon_id=1496,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy, causing ${$13222m2+0.04*$AP} Nature damage and reducing all healing effects used on them by $13222s1% for $13222d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 8, 'SpellLevel': 40, 'SpellVisualID_1': 12720, 'Targets': 16},
)


wound_poison_iii_13226 = spell(
    id=13226,
    name='Wound Poison III',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=705),
    ],
    spell_icon_id=1496,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 48, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy, causing ${$13223m2+0.04*$AP} Nature damage and reducing all healing effects used on them by $13223s1% for $13223d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 8, 'SpellLevel': 48, 'SpellVisualID_1': 12720, 'Targets': 16},
)


wound_poison_iv_13227 = spell(
    id=13227,
    name='Wound Poison IV',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=706),
    ],
    spell_icon_id=1496,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 56, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy, causing ${$13224m2+0.04*$AP} Nature damage and reducing all healing effects used on them by $13224s1% for $13224d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 8, 'SpellLevel': 56, 'SpellVisualID_1': 12720, 'Targets': 16},
)


backstab_25300 = spell(
    id=25300,
    name='Backstab',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=60,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=149, implicit_target_a=6),
        Effect(type=31, base_points=149, implicit_target_a=6),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=243,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 1048576, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Backstab the target, causing $m2% weapon damage plus ${$m1*1.5} to the target.  Must be behind the target.  Requires a dagger in the main hand.  Awards $s3 combo $lpoint:points;.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 32768, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 8388612, 'SpellClassSet': 8, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 155, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


feint_25302 = spell(
    id=25302,
    name='Feint',
    school=School.NORMAL,
    attributes=327696,
    category=82,
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
    spell_icon_id=539,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Performs a feint, causing no damage but lowering your threat by a large amount, making the enemy less likely to attack you.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 70, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 134217728, 'SpellClassSet': 8, 'SpellLevel': 60, 'SpellVisualID_1': 738, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


deadly_poison_v_25351 = spell(
    id=25351,
    name='Deadly Poison V',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=599, misc_value=2630),
    ],
    spell_icon_id=513,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $25351h% chance of poisoning the enemy for ${$25349m1*4+0.12*$AP} Nature damage over $25349d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 60, 'SpellVisualID_1': 12720, 'Targets': 16},
)


deadly_throw_26679 = spell(
    id=26679,
    name='Deadly Throw',
    school=School.NORMAL,
    attributes=4259858,
    cast_time_ms=-1000000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=58, points_per_level=4.1875, die_sides=17, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=2097,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 64); RealPointsPerLevel from rank1→top rank's own top level (80, rank1 learn level ≥ 60) slope (anchor 48674, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48674, rank 3); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)",
    raw_overrides={'AttributesEx': 1049088, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement slowed by $s2%.', 'BaseLevel': 64, 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that reduces the movement of the target by $s2% for $d and causes increased thrown weapon damage:\r\n   1 point  : ${$m1+($b1*1)+$rwb} - ${$M1+($b1*1)+$RWB} damage\r\n   2 points: ${$m1+($b1*2)+$rwb} - ${$M1+($b1*2)+$RWB} damage\r\n   3 points: ${$m1+($b1*3)+$rwb} - ${$M1+($b1*3)+$RWB} damage\r\n   4 points: ${$m1+($b1*4)+$rwb} - ${$M1+($b1*4)+$RWB} damage\r\n   5 points: ${$m1+($b1*5)+$rwb} - ${$M1+($b1*5)+$RWB} damage', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_1': 105.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 65536, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 74, 'Speed': 50.0, 'SpellClassMask_1': 8388608, 'SpellClassMask_2': 1, 'SpellClassSet': 8, 'SpellLevel': 64, 'SpellVisualID_1': 7929, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


anesthetic_poison_26785 = spell(
    id=26785,
    name='Anesthetic Poison',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=2640),
    ],
    spell_icon_id=110,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 68); RealPointsPerLevel from rank1→top rank's own top level (80, rank1 learn level ≥ 60) slope (anchor 57982, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (57982, rank 2); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana); effect1 (type 54, ENCHANT_ITEM_TEMPORARY-family) left untouched -- base_points unused by that effect handler, not a real scaling quantity",
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 68, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.  Each strike has a $26785h% chance of poisoning the enemy which instantly inflicts $26688s1 Nature damage and dispels $26688s2 Enrage effect, but causes no additional threat.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_2': 16, 'SpellClassSet': 8, 'SpellLevel': 68, 'SpellVisualID_1': 12720, 'Targets': 16},
)


instant_poison_vii_26891 = spell(
    id=26891,
    name='Instant Poison VII',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=2641),
    ],
    spell_icon_id=247,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 68, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$26890m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 68, 'SpellVisualID_1': 12720, 'Targets': 16},
)


deadly_poison_vi_26967 = spell(
    id=26967,
    name='Deadly Poison VI',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=599, misc_value=2642),
    ],
    spell_icon_id=513,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 62, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $26967h% chance of poisoning the enemy for ${$26968m1*4+0.12*$AP} Nature damage over $26968d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 62, 'SpellVisualID_1': 12720, 'Targets': 16},
)


deadly_poison_vii_27186 = spell(
    id=27186,
    name='Deadly Poison VII',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=599, misc_value=2643),
    ],
    spell_icon_id=513,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 70, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $27186h% chance of poisoning the enemy for ${$27187m1*4+0.12*$AP} Nature damage over $27187d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 70, 'SpellVisualID_1': 12720, 'Targets': 16},
)


wound_poison_v_27188 = spell(
    id=27188,
    name='Wound Poison V',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=2644),
    ],
    spell_icon_id=1496,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 64, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy, causing ${$27189m2+0.04*$AP} Nature damage and reducing all healing effects used on them by $27189s1% for $27189d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 8, 'SpellLevel': 64, 'SpellVisualID_1': 12720, 'Targets': 16},
)


eviscerate_31016 = spell(
    id=31016,
    name='Eviscerate',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=53, die_sides=109, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=514,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 1049088, 'AttributesEx3': 1024, 'AttributesEx4': 8, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that causes damage per combo point:\r\n   1 point  : ${$m1+(($b1*1)+$AP*0.03)*$<mult>}-${$M1+(($b1*1)+$AP*0.07)*$<mult>} damage\r\n   2 points: ${$m1+(($b1*2)+$AP*0.06)*$<mult>}-${$M1+(($b1*2)+$AP*0.14)*$<mult>} damage\r\n   3 points: ${$m1+(($b1*3)+$AP*0.09)*$<mult>}-${$M1+(($b1*3)+$AP*0.21)*$<mult>} damage\r\n   4 points: ${$m1+(($b1*4)+$AP*0.12)*$<mult>}-${$M1+(($b1*4)+$AP*0.28)*$<mult>} damage\r\n   5 points: ${$m1+(($b1*5)+$AP*0.15)*$<mult>}-${$M1+(($b1*5)+$AP*0.35)*$<mult>} damage', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_1': 170.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 8519680, 'SpellClassSet': 8, 'SpellDescriptionVariableID': 169, 'SpellLevel': 60, 'SpellVisualID_1': 671, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


cloak_of_shadows_31224 = spell(
    id=31224,
    name='Cloak of Shadows',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=90000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-91, implicit_target_a=1, apply_aura=186, misc_value=126),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=35729),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=1),
    ],
    spell_icon_id=1933,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131104, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases chance to resist spells by $s1%.', 'BaseLevel': 66, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly removes all existing harmful spell effects and increases your chance to resist all spells by $s1% for $d.  Does not remove effects that prevent you from using Cloak of Shadows.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 65536, 'SpellClassSet': 8, 'SpellLevel': 66, 'SpellVisualID_1': 3619, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


envenom_32645 = spell(
    id=32645,
    name='Envenom',
    school=School.NATURE,
    dispel=DispelType.POISON,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=1000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=117, points_per_level=5.444444444444445, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=74, implicit_target_a=1, apply_aura=108, misc_value=26),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=107, misc_value=18),
    ],
    spell_icon_id=2237,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 62); RealPointsPerLevel from rank1→top rank's own top level (80, rank1 learn level ≥ 60) slope (anchor 57993, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (57993, rank 4); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)",
    raw_overrides={'AttributesEx': 1049088, 'AttributesEx3': 1024, 'AttributesEx4': 9, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Chance to apply Deadly Poison increased by $s3% and frequency of applying Instant Poison increased by $s2%.', 'BaseLevel': 62, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that consumes your Deadly Poison doses on the target and deals instant poison damage.  Following the Envenom attack you have an additional $s3% chance to apply Deadly Poison and a $s2% increased frequency of applying Instant Poison for 1 sec plus an additional 1 sec per combo point.  One dose is consumed for each combo point:\r\n  1 dose:  ${($m1-1)*1+$AP*0.09} damage\r\n  2 doses: ${($m1-1)*2+$AP*0.18} damage\r\n  3 doses: ${($m1-1)*3+$AP*0.27} damage\r\n  4 doses: ${($m1-1)*4+$AP*0.36} damage\r\n  5 doses: ${($m1-1)*5+$AP*0.45} damage', 'DurationIndex': 285, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 8192, 'EffectSpellClassMaskC_1': 65536, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 8388608, 'SpellClassMask_2': 8, 'SpellClassSet': 8, 'SpellLevel': 62, 'SpellVisualID_1': 8144, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'TargetAuraState': 16},
)


dismantle_51722 = spell(
    id=51722,
    name='Dismantle',
    school=School.NORMAL,
    mechanic=3,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=278),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=254),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_DISARM),
    ],
    spell_icon_id=2908,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Disarmed.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Disarm the enemy, removing all weapons, shield or other equipment carried for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 1048576, 'SpellClassSet': 8, 'SpellLevel': 20, 'SpellVisualID_1': 11540, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


fan_of_knives_51723 = spell(
    id=51723,
    name='Fan of Knives',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=31, base_points=69, implicit_target_a=18, implicit_target_b=16, radius_yards=8.0),
    ],
    spell_icon_id=2904,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 16, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly throw both weapons at all targets within $a1 yards, causing ${$m1*1.5}% weapon damage with daggers, and $s1% weapon damage with all other weapons.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'Speed': 18.0, 'SpellClassMask_2': 262144, 'SpellClassSet': 8, 'SpellLevel': 80, 'SpellVisualID_1': 12317, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


tricks_of_the_trade_57934 = spell(
    id=57934,
    name='Tricks of the Trade',
    school=School.NORMAL,
    attributes=33882128,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=15,
    mana_cost_pct=0,
    range_yards=20.0,
    duration_ms=30000,
    effects=[
        Effect(type=130, base_points=99, implicit_target_a=57),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3413,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 67634208, 'AttributesEx3': 256, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'The threat caused by your next damaging attack and all actions taken for $57933d afterwards will be transferred to the target.  In addition, all damage caused by the target is increased by $57933s1% during this time.', 'BaseLevel': 75, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The current party or raid member becomes the target of your Tricks of the Trade.  The threat caused by your next damaging attack and all actions taken for $57933d afterwards will be transferred to the target.  In addition, all damage caused by the target is increased by $57933s1% during this time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 340, 'SpellClassMask_2': 131072, 'SpellClassSet': 8, 'SpellLevel': 75, 'SpellVisualID_1': 12786, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


instant_poison_viii_57967 = spell(
    id=57967,
    name='Instant Poison VIII',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=3768),
    ],
    spell_icon_id=247,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 73, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$57964m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 8', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 73, 'SpellVisualID_1': 12720, 'Targets': 16},
)


instant_poison_ix_57968 = spell(
    id=57968,
    name='Instant Poison IX',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=3769),
    ],
    spell_icon_id=247,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 79, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy which instantly inflicts ${$57965m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'RangeIndex': 1, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 79, 'SpellVisualID_1': 12720, 'Targets': 16},
)


deadly_poison_viii_57972 = spell(
    id=57972,
    name='Deadly Poison VIII',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=599, misc_value=3770),
    ],
    spell_icon_id=513,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 76, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $57972h% chance of poisoning the enemy for ${$57969m1*4+0.12*$AP} Nature damage over $57969d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 8', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 76, 'SpellVisualID_1': 12720, 'Targets': 16},
)


deadly_poison_ix_57973 = spell(
    id=57973,
    name='Deadly Poison IX',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=599, misc_value=3771),
    ],
    spell_icon_id=513,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 80, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $57973h% chance of poisoning the enemy for ${$57970m1*4+0.12*$AP} Nature damage over $57970d.  Stacks up to 5 times on a single target.   Once stacked to 5 times, each application of Deadly Poison also causes the poison on the Rogue's other weapon to apply.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'RangeIndex': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 8, 'SpellLevel': 80, 'SpellVisualID_1': 12720, 'Targets': 16},
)


wound_poison_vi_57977 = spell(
    id=57977,
    name='Wound Poison VI',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=3772),
    ],
    spell_icon_id=1496,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 72, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy, causing ${$57974m2+0.04*$AP} Nature damage and reducing all healing effects used on them by $57974s1% for $57974d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 8, 'SpellLevel': 72, 'SpellVisualID_1': 12720, 'Targets': 16},
)


wound_poison_vii_57978 = spell(
    id=57978,
    name='Wound Poison VII',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=3773),
    ],
    spell_icon_id=1496,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 32, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 78, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a chance of poisoning the enemy, causing ${$57975m2+0.04*$AP} Nature damage and reducing all healing effects used on them by $57975s1% for $57975d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_1': 268435456, 'SpellClassSet': 8, 'SpellLevel': 78, 'SpellVisualID_1': 12720, 'Targets': 16},
)


anesthetic_poison_ii_57982 = spell(
    id=57982,
    name='Anesthetic Poison II',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=54, misc_value=3774),
    ],
    spell_icon_id=110,
    notes='pulled from existing data | single-rank conversion (rogue): superseded rank kept in rogue.csv -- still referenced by item_template (spellid/RequiredSpell), not creature-only',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx2': 8200, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 77, 'CastingTimeIndex': 14, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.  Each strike has a $57982h% chance of poisoning the enemy which instantly inflicts $57981s1 Nature damage and dispels $57981s2 Enrage effect, but causes no additional threat.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassMask_2': 16, 'SpellClassSet': 8, 'SpellLevel': 77, 'SpellVisualID_1': 12720, 'Targets': 16},
)


mutilate_1329 = spell(
    id=1329,
    name='Mutilate',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=60,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.ADD_COMBO_POINTS, base_points=1, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=mutilate_5374.id),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=mutilate_27576.id),
    ],
    spell_icon_id=2117,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1→level-60 slope (anchor 34412, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48666, rank 6); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 1048576, 'AttributesEx3': 16843776, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly attacks with both weapons for $<percent>% weapon damage plus an additional $5374s1 with each weapon.  Damage is increased by 20% against Poisoned targets.  Awards 2 combo points.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 32768, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 2097152, 'SpellClassSet': 8, 'SpellDescriptionVariableID': 172, 'SpellLevel': 40, 'SpellVisualID_1': 7913, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


hemorrhage_16511 = spell(
    id=16511,
    name='Hemorrhage',
    school=School.NORMAL,
    attributes=67436560,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=15000,
    effects=[
        Effect(type=121, die_sides=0, implicit_target_a=6),
        Effect(type=31, base_points=109, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=12, points_per_level=0.5333333333333333, implicit_target_a=6, apply_aura=14, misc_value=1),
    ],
    spell_icon_id=153,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1→level-60 slope (anchor 17348, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48660, rank 5); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1026, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases damage taken by $s3.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'An instant strike that deals $s2% weapon damage (${$m2*1.45}% if a dagger is equipped) and causes the target to hemorrhage, increasing any Physical damage dealt to the target by up to $<bonus>.  Lasts $n charges or $d.  Awards 1 combo point.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcCharges': 10, 'ProcTypeMask': 139944, 'RangeIndex': 2, 'SpellClassMask_1': 41943040, 'SpellClassSet': 8, 'SpellDescriptionVariableID': 64, 'SpellLevel': 30, 'SpellVisualID_1': 5119, 'StanceBarOrder': 4294967295, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


adrenaline_rush_13750 = spell(
    id=13750,
    name='Adrenaline Rush',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=110, misc_value=3),
    ],
    spell_icon_id=235,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Energy regeneration increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Energy regeneration rate by $s1% for $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 128, 'SpellClassSet': 8, 'SpellVisualID_1': 8996, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


blade_flurry_13877 = spell(
    id=13877,
    name='Blade Flurry',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=138),
    ],
    spell_icon_id=1477,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attack speed increased by $s1%.  Weapon attacks strike an additional nearby opponent.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your attack speed by $s1%.  In addition, attacks strike an additional nearby opponent.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassMask_1': 1073741824, 'SpellClassMask_2': 2048, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 211, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


cold_blood_14177 = spell(
    id=14177,
    name='Cold Blood',
    school=School.NORMAL,
    attributes=33882128,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=32,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 32, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Critical strike chance of your next offensive ability increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, increases the critical strike chance of your next offensive ability by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 100794886, 'EffectSpellClassMaskA_2': 262415, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassMask_2': 64, 'SpellClassSet': 8, 'SpellVisualID_1': 4371},
)


premeditation_14183 = spell(
    id=14183,
    name='Premeditation',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=20000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.ADD_COMBO_POINTS, base_points=1, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=148),
    ],
    spell_icon_id=98,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268567584, 'AttributesEx3': 196608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When used, adds $s1 combo points to your target.  You must add to or use those combo points within $d or the combo points are lost.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ShapeshiftMask': 536870912, 'SpellClassMask_2': 32, 'SpellClassSet': 8, 'SpellLevel': 20},
)


preparation_14185 = spell(
    id=14185,
    name='Preparation',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=480000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=207,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 32, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, this ability immediately finishes the cooldown on your Evasion, Sprint, Vanish, Cold Blood and Shadowstep abilities.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 4096, 'SpellClassSet': 8, 'SpellVisualID_1': 3259, 'StanceBarOrder': 4294967295, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


riposte_14251 = spell(
    id=14251,
    name='Riposte',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=10,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=30000,
    effects=[
        Effect(type=31, base_points=149, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, mechanic=8, implicit_target_a=6, apply_aura=138),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=278,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131584, 'AttributesEx4': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attack speed slowed by $s2%.', 'CasterAuraState': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "A strike that becomes active after parrying an opponent's attack.  This attack deals $s1% weapon damage and slows their melee attack speed by $s2% for $d.  Awards $s3 combo point.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 256, 'SpellClassSet': 8, 'SpellVisualID_1': 3799, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


ghostly_strike_14278 = spell(
    id=14278,
    name='Ghostly Strike',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=20000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=40,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=7000,
    effects=[
        Effect(type=31, base_points=124, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=49),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=596,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Dodge chance increased by $s2%.', 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A strike that deals $s1% weapon damage (${$m1*1.44}% if a dagger is equipped) and increases your chance to dodge by $s2% for $d.  Awards $s3 combo $lpoint:points;.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 1140850688, 'SpellClassSet': 8, 'SpellVisualID_1': 4159, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


shadowstep_36554 = spell(
    id=36554,
    name='Shadowstep',
    school=School.NORMAL,
    attributes=536870928,
    category=1206,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=10,
    mana_cost_pct=0,
    range_yards=25.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=36563),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=1, trigger_spell=44373),
        Effect(type=EffectType.APPLY_AURA, base_points=69, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=2363,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1056, 'AttributesEx2': 268435456, 'AttributesEx3': 196608, 'AttributesEx6': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed increased by $s3%.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Attempts to step through the shadows and reappear behind your enemy and increases movement speed by $36554s3% for $36554d.  The damage of your next ability is increased by $36563s2% and the threat caused is reduced by $44373s1%.  Lasts $36563d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_1': 772, 'EffectSpellClassMaskC_2': 2, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 65219, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'SpellClassMask_2': 512, 'SpellClassSet': 8, 'SpellLevel': 1},
)


hunger_for_blood_51662 = spell(
    id=51662,
    name='Hunger For Blood',
    school=School.NORMAL,
    dispel=9,
    mechanic=31,
    attributes=2424848,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=15,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=9, implicit_target_a=6),
    ],
    spell_icon_id=2961,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1056, 'AttributesEx3': 64, 'AttributesEx6': 4, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Enrages you, increasing all damage caused by $63848s1%.  Requires a bleed effect to be active on the target.  Lasts $63848d.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 637665798, 'EffectSpellClassMaskA_2': 271, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 16777216, 'SpellClassSet': 8, 'SpellVisualID_1': 11821, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'TargetAuraState': 18},
)


killing_spree_51690 = spell(
    id=51690,
    name='Killing Spree',
    school=School.NORMAL,
    attributes=65552,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=10.0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=226, amplitude=500, misc_value=3),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=18, implicit_target_b=16, radius_yards=10.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=263),
    ],
    spell_icon_id=2907,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx2': 268435456, 'AttributesEx3': 197633, 'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attacking an enemy every $t1 sec.\r\nDamage dealt increased by $61851s3%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Step through the shadows from enemy to enemy within 10 yards, attacking an enemy every .5 secs with both weapons until 5 assaults are made, and increasing all damage done by $61851s3% for the duration.  Can hit the same target multiple times.  Cannot hit invisible or stealthed targets.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 8388608, 'SpellClassSet': 8, 'SpellVisualID_1': 12981, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


shadow_dance_51713 = spell(
    id=51713,
    name='Shadow Dance',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=275),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=13),
    ],
    spell_icon_id=2959,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 132096, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Can use opening abilities without being stealthed.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Enter the Shadow Dance for $d, allowing the use of Sap, Garrote, Ambush, Cheap Shot, Premeditation, Pickpocket and Disarm Trap regardless of being stealthed.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2147485568, 'EffectSpellClassMaskA_2': 8224, 'EffectSpellClassMaskB_1': 2147485568, 'EffectSpellClassMaskB_2': 8224, 'EffectSpellClassMaskC_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 33554432, 'SpellClassSet': 8, 'SpellLevel': 60, 'SpellVisualID_1': 11827, 'StanceBarOrder': 1},
)
