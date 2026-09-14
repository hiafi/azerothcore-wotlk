"""
Auto-converted from source/spells/rogue*.csv + source/talents/rogue.yaml by csv_to_dsl.py
(.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md's Phase 4) - not yet hand-cleaned. See csv_to_dsl.py's docstring for what "mechanical, not hand-authored-quality" means here.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, School
from lib.dsl.registry import spell
from lib.dsl.registry import granted_by_talent, tab

# --- spells trained outright (source/spells/rogue.csv) ---

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

pick_pocket_921 = spell(
    id=921,
    name='Pick Pocket',
    school=School.NORMAL,
    attributes=196624,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=71, base_points=-1, implicit_target_a=6),
    ],
    spell_icon_id=227,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2232352, 'AttributesEx3': 196608, 'AttributesEx4': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Pick the target's pocket.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 536870912, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 8, 'SpellLevel': 4, 'SpellVisualID_1': 251},
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
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=11327),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=18461),
        Effect(type=79, base_points=-1, implicit_target_a=1),
    ],
    spell_icon_id=252,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 22); RealPointsPerLevel from rank1→level-60 slope (anchor 1857, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (26889, rank 3); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'ActiveIconID': 30, 'AttributesEx': 1056, 'AttributesEx2': 2, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Improved stealth.', 'AuraInterruptFlags': 15367, 'BaseLevel': 22, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows the rogue to vanish from sight, entering an improved stealth mode for $11327d.  Also breaks movement impairing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeCasterAuraState': 12, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 139944, 'RangeIndex': 1, 'SpellClassMask_1': 2048, 'SpellClassSet': 8, 'SpellLevel': 22, 'SpellVisualID_1': 255},
)

safe_fall_1860 = spell(
    id=1860,
    name='Safe Fall',
    school=School.NORMAL,
    attributes=262224,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=16, implicit_target_a=1, apply_aura=144),
    ],
    spell_icon_id=1658,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces damage from falling.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Passive', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 32768, 'SpellClassSet': 8, 'SpellLevel': 40},
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

deadly_poison_2818 = spell(
    id=2818,
    name='Deadly Poison',
    school=School.NATURE,
    dispel=DispelType.POISON,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, points_per_level=0.6, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=197),
    ],
    spell_icon_id=513,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1→level-60 slope (anchor 25349, rank 5); coefficient/cast_time_ms/mana_cost_pct from max rank (57970, rank 9); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 131208, 'AttributesEx2': 16777220, 'AttributesEx3': 128, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Target takes $s1 Nature damage every $t1 seconds.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'CumulativeAura': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $2823h% chance of poisoning the enemy for ${$2818m1*4+0.12*$AP} Nature damage over $2818d.  Stacks up to 5 times on a single target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_1': 65536, 'SpellClassMask_2': 524288, 'SpellClassSet': 8, 'SpellLevel': 30, 'SpellVisualID_1': 5100},
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

mutilate_5374 = spell(
    id=5374,
    name='Mutilate',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=43, points_per_level=2.3220338983050848, implicit_target_a=6),
    ],
    spell_icon_id=533,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope (anchor 48665, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48665, rank 6); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx3': 1536, 'AttributesEx4': 1, 'AttributesEx7': 58720256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly attacks with both weapons for $<percent>% weapon damage plus additional $5374s1 with each weapon.  Damage is increased by 20% against Poisoned targets.  Awards 2 combo points.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 32768, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 2, 'SpellClassSet': 8, 'SpellDescriptionVariableID': 172, 'SpellLevel': 1},
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

instant_poison_8680 = spell(
    id=8680,
    name='Instant Poison',
    school=School.NATURE,
    dispel=DispelType.POISON,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=12, points_per_level=1.575, die_sides=5, implicit_target_a=6),
    ],
    spell_icon_id=247,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor 11337, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (57965, rank 9); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $8679h% chance of poisoning the enemy which instantly inflicts ${$8680m1+0.10*$AP} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_1': 8192, 'SpellClassSet': 8, 'SpellLevel': 20, 'SpellVisualID_1': 5100},
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

vanish_11327 = spell(
    id=11327,
    name='Vanish',
    school=School.NORMAL,
    dispel=DispelType.STEALTH,
    attributes=169148688,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=169, points_per_level=5.0, implicit_target_a=1, apply_aura=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=252,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 22); RealPointsPerLevel from rank1→level-60 slope (anchor 11329, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (26888, rank 3); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'ActiveIconID': 30, 'AttributesEx': 32, 'AttributesEx2': 2, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Improved stealth.', 'AuraInterruptFlags': 15364, 'BaseLevel': 22, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712188, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeCasterAuraState': 12, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 536870912, 'SpellClassMask_1': 2048, 'SpellClassSet': 8, 'SpellLevel': 22, 'SpellVisualID_1': 255},
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

wound_poison_13218 = spell(
    id=13218,
    name='Wound Poison',
    school=School.NATURE,
    dispel=DispelType.POISON,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=6, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=16, points_per_level=1.2857142857142858, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=197),
    ],
    spell_icon_id=1496,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 32); RealPointsPerLevel from rank1→level-60 slope (anchor 13224, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (57975, rank 7); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 16777216, 'AttributesEx3': 131072, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All healing effects reduced by $s1%.', 'BaseLevel': 32, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.\r\nEach strike has a $13219h% chance of poisoning the enemy, causing ${$13218m2+0.04*$AP} Nature damage and reducing all healing effects used on them by $13218s1% for $13218d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 32768, 'RangeIndex': 2, 'SpellClassMask_1': 268435456, 'SpellClassMask_2': 524288, 'SpellClassSet': 8, 'SpellLevel': 32, 'SpellVisualID_1': 5100},
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

remorseless_14143 = spell(
    id=14143,
    name='Remorseless',
    school=School.NORMAL,
    attributes=134217728,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, points_per_level=0.3333333333333333, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=695,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1→level-60 slope (anchor 14149, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (14149, rank 2); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Critical strike chance for your next Sinister Strike, Backstab, Mutilate, Ambush, Hemorrhage, or Ghostly strike increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'After killing an opponent that yields experience or honor, gives you a $14143s1% increased critical strike chance on your next Sinister Strike, Hemorrhage, Backstab, Mutilate, Ambush, or Ghostly Strike.  Lasts $14143d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 100663814, 'EffectSpellClassMaskA_2': 6, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 8},
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

anesthetic_poison_26688 = spell(
    id=26688,
    name='Anesthetic Poison',
    school=School.NATURE,
    dispel=DispelType.POISON,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=133, points_per_level=7.0, die_sides=39, implicit_target_a=6),
        Effect(type=EffectType.DISPEL, implicit_target_a=6, misc_value=9),
    ],
    spell_icon_id=110,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 68); RealPointsPerLevel from rank1→top rank's own top level (80, rank1 learn level ≥ 60) slope (anchor 57981, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (57981, rank 2); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)",
    raw_overrides={'AttributesEx': 1160, 'AttributesEx2': 16777216, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 68, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Coats a weapon with poison that lasts for 1 hour.  Each strike has a $26785h% chance of poisoning the enemy which instantly inflicts $26688s1 Nature damage and dispels $26688s2 Enrage effect, but causes no additional threat.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 16, 'SpellClassSet': 8, 'SpellLevel': 68, 'SpellVisualID_1': 5100},
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

mutilate_27576 = spell(
    id=27576,
    name='Mutilate',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=43, points_per_level=2.3220338983050848, implicit_target_a=6),
    ],
    spell_icon_id=533,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope (anchor 48664, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48664, rank 6); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx3': 16777728, 'AttributesEx7': 58720256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly attacks with both weapons for $<percent>% weapon damage plus additional $5374s1 with each weapon.  Damage is increased by 20% against Poisoned targets.  Awards 2 combo points.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 32768, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 4, 'SpellClassSet': 8, 'SpellDescriptionVariableID': 172, 'SpellLevel': 1},
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

infectious_poisons_51630 = spell(
    id=51630,
    name='Infectious Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, points_per_level=0.8333333333333334, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=0.16666666666666666, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=2956,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1→level-60 slope (anchor 51631, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (51631, rank 2); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage caused by your Instant Poison and Deadly Poison by $s2%.  In addition, when a target you've poisoned is healed or cured, there is a $h% chance the poison afflicts the healer.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 131072, 'EffectSpellClassMaskB_1': 73728, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11838},
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


# --- spells granted by a talent point (source/spells/rogue_talents.csv) ---

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
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=5374),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=27576),
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

throwing_specialization_5952 = spell(
    id=5952,
    name='Throwing Specialization',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=51680),
    ],
    spell_icon_id=2910,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of Throw and Deadly Throw by $s1 yards and gives your Deadly Throw a $h% chance to interrupt the target for $51680d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskA_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 349456, 'RangeIndex': 1, 'SpellClassSet': 8},
)

dual_wield_specialization_13715 = spell(
    id=13715,
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
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your offhand weapon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_sinister_strike_13732 = spell(
    id=13732,
    name='Improved Sinister Strike',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=130,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the Energy cost of your Sinister Strike ability by $s1.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 2, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

puncturing_wounds_13733 = spell(
    id=13733,
    name='Puncturing Wounds',
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
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=243,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Backstab ability by $s1%, and the critical strike chance of your Mutilate ability by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4, 'EffectSpellClassMaskB_2': 6, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_gouge_13741 = spell(
    id=13741,
    name='Improved Gouge',
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
        Effect(type=EffectType.APPLY_AURA, base_points=499, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=245,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect duration of your Gouge ability by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 8, 'EffectSpellClassMaskA_1': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

endurance_13742 = spell(
    id=13742,
    name='Endurance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137, misc_value=2),
    ],
    spell_icon_id=178,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Sprint and Evasion abilities by $/1000;s1 sec and increases your total Stamina by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 96, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_sprint_13743 = spell(
    id=13743,
    name='Improved Sprint',
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
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=109, trigger_spell=30918),
    ],
    spell_icon_id=516,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives a $s1% chance to remove all Movement Impairing effects when you activate your Sprint ability.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
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

improved_kick_13754 = spell(
    id=13754,
    name='Improved Kick',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18425),
    ],
    spell_icon_id=246,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Kick ability a $h% chance to silence the target for $18425d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_gouge_13792 = spell(
    id=13792,
    name='Improved Gouge',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1499, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=245,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect duration of your Gouge ability by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 8, 'EffectSpellClassMaskA_1': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_gouge_13793 = spell(
    id=13793,
    name='Improved Gouge',
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
        Effect(type=EffectType.APPLY_AURA, base_points=999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=245,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect duration of your Gouge ability by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 8, 'EffectSpellClassMaskA_1': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

dual_wield_specialization_13848 = spell(
    id=13848,
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
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your offhand weapon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

dual_wield_specialization_13849 = spell(
    id=13849,
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
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=122),
    ],
    spell_icon_id=533,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your offhand weapon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

dual_wield_specialization_13851 = spell(
    id=13851,
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
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=122),
    ],
    spell_icon_id=533,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your offhand weapon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

dual_wield_specialization_13852 = spell(
    id=13852,
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
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=122),
    ],
    spell_icon_id=533,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your offhand weapon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_sinister_strike_13863 = spell(
    id=13863,
    name='Improved Sinister Strike',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=130,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the Energy cost of your Sinister Strike ability by $s1.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 2, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

puncturing_wounds_13865 = spell(
    id=13865,
    name='Puncturing Wounds',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=243,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Backstab ability by $s1%, and the critical strike chance of your Mutilate ability by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4, 'EffectSpellClassMaskB_2': 6, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

puncturing_wounds_13866 = spell(
    id=13866,
    name='Puncturing Wounds',
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
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=243,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Backstab ability by $s1%, and the critical strike chance of your Mutilate ability by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4, 'EffectSpellClassMaskB_2': 6, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_kick_13867 = spell(
    id=13867,
    name='Improved Kick',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18425),
    ],
    spell_icon_id=246,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Kick ability a $h% chance to silence the target for $18425d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 8},
)

endurance_13872 = spell(
    id=13872,
    name='Endurance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-60001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=137, misc_value=2),
    ],
    spell_icon_id=178,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Sprint and Evasion abilities by $/1000;s1 sec and increases your total Stamina by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 96, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_sprint_13875 = spell(
    id=13875,
    name='Improved Sprint',
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
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=109, trigger_spell=30918),
    ],
    spell_icon_id=516,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives a $s1% chance to remove all Movement Impairing effects when you activate your Sprint ability.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
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

camouflage_13975 = spell(
    id=13975,
    name='Camouflage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=250,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your speed while stealthed by $s1% and reduces the cooldown of your Stealth ability by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EffectSpellClassMaskB_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11336},
)

initiative_13976 = spell(
    id=13976,
    name='Initiative',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=109, trigger_spell=13977),
    ],
    spell_icon_id=233,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a $s1% chance to add an additional combo point to your target when using your Ambush, Garrote, or Cheap Shot ability.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1792, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

initiative_13979 = spell(
    id=13979,
    name='Initiative',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=109, trigger_spell=13977),
    ],
    spell_icon_id=233,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a $s1% chance to add an additional combo point to your target when using your Ambush, Garrote, or Cheap Shot ability.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1792, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

initiative_13980 = spell(
    id=13980,
    name='Initiative',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=109, trigger_spell=13977),
    ],
    spell_icon_id=233,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a $s1% chance to add an additional combo point to your target when using your Ambush, Garrote, or Cheap Shot ability.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1792, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

elusiveness_13981 = spell(
    id=13981,
    name='Elusiveness',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-15001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=331,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Vanish and Blind abilities by $/1000;S1 sec and your Cloak of Shadows ability by $/1000;S2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16779264, 'EffectSpellClassMaskB_2': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

opportunity_14057 = spell(
    id=14057,
    name='Opportunity',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=282,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage dealt with your Backstab, Mutilate, Garrote and Ambush abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 516, 'EffectSpellClassMaskA_2': 6, 'EffectSpellClassMaskB_1': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

camouflage_14062 = spell(
    id=14062,
    name='Camouflage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=-4001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=250,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your speed while stealthed by $s1% and reduces the cooldown of your Stealth ability by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EffectSpellClassMaskB_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11335},
)

camouflage_14063 = spell(
    id=14063,
    name='Camouflage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=-6001, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=250,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your speed while stealthed by $s1% and reduces the cooldown of your Stealth ability by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EffectSpellClassMaskB_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11335},
)

elusiveness_14066 = spell(
    id=14066,
    name='Elusiveness',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-60001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=331,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Vanish and Blind abilities by $/1000;S1 sec and your Cloak of Shadows ability by $/1000;S2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16779264, 'EffectSpellClassMaskB_2': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

opportunity_14072 = spell(
    id=14072,
    name='Opportunity',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=282,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage dealt with your Backstab, Mutilate, Garrote and Ambush abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 516, 'EffectSpellClassMaskA_2': 6, 'EffectSpellClassMaskB_1': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

dirty_tricks_14076 = spell(
    id=14076,
    name='Dirty Tricks',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=249,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your Blind and Sap abilities by $s1 yards and reduces the energy cost of your Blind and Sap abilities by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 16777344, 'EffectSpellClassMaskB_1': 16777344, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_ambush_14079 = spell(
    id=14079,
    name='Improved Ambush',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=856,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Ambush ability by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_ambush_14080 = spell(
    id=14080,
    name='Improved Ambush',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=856,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Ambush ability by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

dirty_deeds_14082 = spell(
    id=14082,
    name='Dirty Deeds',
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
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=112, misc_value=6427),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=112, misc_value=6580),
    ],
    spell_icon_id=216,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the Energy cost of your Cheap Shot and Garrote abilities by $s1.  Additionally, your special abilities cause 10% more damage against targets below 35% health.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1280, 'EffectSpellClassMaskB_1': 646054430, 'EffectSpellClassMaskB_2': 271, 'EffectSpellClassMaskC_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

dirty_deeds_14083 = spell(
    id=14083,
    name='Dirty Deeds',
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
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=112, misc_value=6428),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=112, misc_value=6579),
    ],
    spell_icon_id=216,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the Energy cost of your Cheap Shot and Garrote abilities by $s1.  Additionally, your special abilities cause 20% more damage against targets below 35% health.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1280, 'EffectSpellClassMaskB_1': 646054430, 'EffectSpellClassMaskB_2': 271, 'EffectSpellClassMaskC_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'TargetAuraState': 13},
)

dirty_tricks_14094 = spell(
    id=14094,
    name='Dirty Tricks',
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
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=249,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your Blind and Sap abilities by $s1 yards and reduces the energy cost of your Blind and Sap abilities by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 16777344, 'EffectSpellClassMaskB_1': 16777344, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_poisons_14113 = spell(
    id=14113,
    name='Improved Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=26),
    ],
    spell_icon_id=247,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the chance to apply Deadly Poison to your target by $s1% and the frequency of applying Instant Poison to your target by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_poisons_14114 = spell(
    id=14114,
    name='Improved Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=107, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=26),
    ],
    spell_icon_id=247,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the chance to apply Deadly Poison to your target by $s1% and the frequency of applying Instant Poison to your target by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_poisons_14115 = spell(
    id=14115,
    name='Improved Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=107, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=26),
    ],
    spell_icon_id=247,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the chance to apply Deadly Poison to your target by $s1% and the frequency of applying Instant Poison to your target by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_poisons_14116 = spell(
    id=14116,
    name='Improved Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=107, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=108, misc_value=26),
    ],
    spell_icon_id=247,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the chance to apply Deadly Poison to your target by $s1% and the frequency of applying Instant Poison to your target by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_poisons_14117 = spell(
    id=14117,
    name='Improved Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=26),
    ],
    spell_icon_id=247,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the chance to apply Deadly Poison to your target by $s1% and the frequency of applying Instant Poison to your target by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

lethality_14128 = spell(
    id=14128,
    name='Lethality',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=138,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of all combo point-generating abilities that do not require stealth by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 637534222, 'EffectSpellClassMaskA_2': 262, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

lethality_14132 = spell(
    id=14132,
    name='Lethality',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=138,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of all combo point-generating abilities that do not require stealth by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 637534222, 'EffectSpellClassMaskA_2': 262, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

lethality_14135 = spell(
    id=14135,
    name='Lethality',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=17, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=138,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of all combo point-generating abilities that do not require stealth by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 637534222, 'EffectSpellClassMaskA_2': 262, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

lethality_14136 = spell(
    id=14136,
    name='Lethality',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=23, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=138,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of all combo point-generating abilities that do not require stealth by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 637534222, 'EffectSpellClassMaskA_2': 262, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

lethality_14137 = spell(
    id=14137,
    name='Lethality',
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
    spell_icon_id=138,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of all combo point-generating abilities that do not require stealth by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 637534222, 'EffectSpellClassMaskA_2': 262, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

ruthlessness_14156 = spell(
    id=14156,
    name='Ruthlessness',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=14157),
    ],
    spell_icon_id=494,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your melee finishing moves a $h1% chance to add a combo point to your target.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 8},
)

murder_14158 = spell(
    id=14158,
    name='Murder',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=255),
    ],
    spell_icon_id=134,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage caused by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4065152, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

murder_14159 = spell(
    id=14159,
    name='Murder',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=79, misc_value=255),
    ],
    spell_icon_id=134,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage caused by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4065152, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

ruthlessness_14160 = spell(
    id=14160,
    name='Ruthlessness',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=14157),
    ],
    spell_icon_id=494,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your melee finishing moves a $h1% chance to add a combo point to your target.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 40, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 8},
)

ruthlessness_14161 = spell(
    id=14161,
    name='Ruthlessness',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=14157),
    ],
    spell_icon_id=494,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your melee finishing moves a $h1% chance to add a combo point to your target.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 60, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_eviscerate_14162 = spell(
    id=14162,
    name='Improved Eviscerate',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=514,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Eviscerate ability by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_eviscerate_14163 = spell(
    id=14163,
    name='Improved Eviscerate',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=514,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Eviscerate ability by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_eviscerate_14164 = spell(
    id=14164,
    name='Improved Eviscerate',
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
    spell_icon_id=514,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Eviscerate ability by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_slice_and_dice_14165 = spell(
    id=14165,
    name='Improved Slice and Dice',
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
    ],
    spell_icon_id=515,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Slice and Dice ability by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_slice_and_dice_14166 = spell(
    id=14166,
    name='Improved Slice and Dice',
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
    ],
    spell_icon_id=515,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Slice and Dice ability by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_expose_armor_14168 = spell(
    id=14168,
    name='Improved Expose Armor',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=563,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the energy cost of your Expose Armor ability by $s1.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_expose_armor_14169 = spell(
    id=14169,
    name='Improved Expose Armor',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=563,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the energy cost of your Expose Armor ability by $s1.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

serrated_blades_14171 = spell(
    id=14171,
    name='Serrated Blades',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=280, misc_value=1),
    ],
    spell_icon_id=2004,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Causes your attacks to ignore up to $s2% of your target's Armor and increases the damage dealt by your Rupture ability by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

serrated_blades_14172 = spell(
    id=14172,
    name='Serrated Blades',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=280, misc_value=1),
    ],
    spell_icon_id=2004,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Causes your attacks to ignore up to $s2% of your target's Armor and increases the damage dealt by your Rupture ability by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

serrated_blades_14173 = spell(
    id=14173,
    name='Serrated Blades',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=280, misc_value=1),
    ],
    spell_icon_id=2004,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Causes your attacks to ignore up to $s2% of your target's Armor and increases the damage dealt by your Rupture ability by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_kidney_shot_14174 = spell(
    id=14174,
    name='Improved Kidney Shot',
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
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=499,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While affected by your Kidney Shot ability, the target receives an additional $s1% damage from all sources.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 2097152, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_kidney_shot_14175 = spell(
    id=14175,
    name='Improved Kidney Shot',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=499,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While affected by your Kidney Shot ability, the target receives an additional $s1% damage from all sources.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 2097152, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

improved_kidney_shot_14176 = spell(
    id=14176,
    name='Improved Kidney Shot',
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
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=499,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While affected by your Kidney Shot ability, the target receives an additional $s1% damage from all sources.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 2097152, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
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

relentless_strikes_14179 = spell(
    id=14179,
    name='Relentless Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=109, trigger_spell=14181),
    ],
    spell_icon_id=559,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1048576, 'AttributesEx4': 2, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your finishing moves have a $b1% chance per combo point to restore $14181s1 energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_1': 4.0, 'EffectSpellClassMaskA_1': 4063232, 'EffectSpellClassMaskA_2': 9, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
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

seal_fate_14186 = spell(
    id=14186,
    name='Seal Fate',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=14189),
    ],
    spell_icon_id=55,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your critical strikes from abilities that add combo points have a $h% chance to add an additional combo point.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

seal_fate_14190 = spell(
    id=14190,
    name='Seal Fate',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=14189),
    ],
    spell_icon_id=55,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your critical strikes from abilities that add combo points have a $h% chance to add an additional combo point.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 40, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

seal_fate_14193 = spell(
    id=14193,
    name='Seal Fate',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=14189),
    ],
    spell_icon_id=55,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your critical strikes from abilities that add combo points have a $h% chance to add an additional combo point.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 60, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

seal_fate_14194 = spell(
    id=14194,
    name='Seal Fate',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=14189),
    ],
    spell_icon_id=55,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your critical strikes from abilities that add combo points have a $h% chance to add an additional combo point.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 80, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

seal_fate_14195 = spell(
    id=14195,
    name='Seal Fate',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=14189),
    ],
    spell_icon_id=55,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your critical strikes from abilities that add combo points have a $h% chance to add an additional combo point.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
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

vigor_14983 = spell(
    id=14983,
    name='Vigor',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=35, misc_value=3),
    ],
    spell_icon_id=691,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your maximum Energy by $s1.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 4194304, 'SpellClassSet': 8},
)

vile_poisons_16513 = spell(
    id=16513,
    name='Vile Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=857,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage dealt by your poisons and Envenom ability by $s1% and gives your damage over time poisons an additional $s3% chance to resist dispel effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 268443648, 'EffectSpellClassMaskA_2': 24, 'EffectSpellClassMaskB_1': 65536, 'EffectSpellClassMaskC_1': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

vile_poisons_16514 = spell(
    id=16514,
    name='Vile Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=857,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage dealt by your poisons and Envenom ability by $s1% and gives your damage over time poisons an additional $s3% chance to resist dispel effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 268443648, 'EffectSpellClassMaskA_2': 24, 'EffectSpellClassMaskB_1': 65536, 'EffectSpellClassMaskC_1': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

vile_poisons_16515 = spell(
    id=16515,
    name='Vile Poisons',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=857,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage dealt by your poisons and Envenom ability by $s1% and gives your damage over time poisons an additional $s3% chance to resist dispel effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 268443648, 'EffectSpellClassMaskA_2': 24, 'EffectSpellClassMaskB_1': 65536, 'EffectSpellClassMaskC_1': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

aggression_18427 = spell(
    id=18427,
    name='Aggression',
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
    spell_icon_id=84,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Sinister Strike, Backstab, and Eviscerate abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131078, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

aggression_18428 = spell(
    id=18428,
    name='Aggression',
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
    spell_icon_id=84,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Sinister Strike, Backstab, and Eviscerate abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131078, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

aggression_18429 = spell(
    id=18429,
    name='Aggression',
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
    spell_icon_id=84,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Sinister Strike, Backstab, and Eviscerate abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131078, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

dual_wield_specialization_30816 = spell(
    id=30816,
    name='Dual Wield Specialization',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=54),
    ],
    spell_icon_id=2023,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 16777216, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to hit while dual wielding by an additional $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

dual_wield_specialization_30818 = spell(
    id=30818,
    name='Dual Wield Specialization',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=54),
    ],
    spell_icon_id=2023,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 16777216, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to hit while dual wielding by an additional $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

dual_wield_specialization_30819 = spell(
    id=30819,
    name='Dual Wield Specialization',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=54),
    ],
    spell_icon_id=2023,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 16777216, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to hit while dual wielding by an additional $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

sleight_of_hand_30892 = spell(
    id=30892,
    name='Sleight of Hand',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=187),
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=188),
    ],
    spell_icon_id=539,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the chance you are critically hit by melee and ranged attacks by $s2% and increases the threat reduction of your Feint ability by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EffectSpellClassMaskB_1': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

sleight_of_hand_30893 = spell(
    id=30893,
    name='Sleight of Hand',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=187),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=188),
    ],
    spell_icon_id=539,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the chance you are critically hit by melee and ranged attacks by $s2% and increases the threat reduction of your Feint ability by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EffectSpellClassMaskB_1': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

blade_twisting_31124 = spell(
    id=31124,
    name='Blade Twisting',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=31125),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2108,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage dealt by Sinister Strike and Backstab by $s2%, and your damaging melee attacks have a $h% chance to Daze the target for $31125d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 6, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 8},
)

blade_twisting_31126 = spell(
    id=31126,
    name='Blade Twisting',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=51585),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2108,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage dealt by Sinister Strike and Backstab by $s2%, and your damaging melee attacks have a $h% chance to Daze the target for $51585d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 6, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 8},
)

sinister_calling_31216 = spell(
    id=31216,
    name='Sinister Calling',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=137, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108, misc_value=12),
    ],
    spell_icon_id=2118,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Agility by $s1% and increases the percentage damage bonus of Backstab and Hemorrhage by an additional $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 33554436, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

sinister_calling_31217 = spell(
    id=31217,
    name='Sinister Calling',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=137, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108, misc_value=12),
    ],
    spell_icon_id=2118,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Agility by $s1% and increases the percentage damage bonus of Backstab and Hemorrhage by an additional $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 33554436, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

sinister_calling_31218 = spell(
    id=31218,
    name='Sinister Calling',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=137, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108, misc_value=12),
    ],
    spell_icon_id=2118,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Agility by $s1% and increases the percentage damage bonus of Backstab and Hemorrhage by an additional $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 33554436, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

sinister_calling_31219 = spell(
    id=31219,
    name='Sinister Calling',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=137, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=108, misc_value=12),
    ],
    spell_icon_id=2118,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Agility by $s1% and increases the percentage damage bonus of Backstab and Hemorrhage by an additional $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 33554436, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

sinister_calling_31220 = spell(
    id=31220,
    name='Sinister Calling',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=137, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=12),
    ],
    spell_icon_id=2118,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Agility by $s1% and increases the percentage damage bonus of Backstab and Hemorrhage by an additional $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 33554436, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

master_of_subtlety_31223 = spell(
    id=31223,
    name='Master of Subtlety',
    school=School.NORMAL,
    attributes=131536,
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
    spell_icon_id=2114,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Attacks made while stealthed and for 6 seconds after breaking stealth cause an additional $s1% damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

master_poisoner_31226 = spell(
    id=31226,
    name='Master Poisoner',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=231, misc_value=23, trigger_spell=45176),
        Effect(type=EffectType.APPLY_AURA, base_points=-18, implicit_target_a=1, apply_aura=246, misc_value=4),
    ],
    spell_icon_id=1960,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical hit chance of all attacks made against any target you have poisoned by $s1%, reduces the duration of all Poison effects applied to you by $s2%, and gives Envenom a $s3% chance not to consume Deadly Poison.', 'EffectBasePoints_3': 32, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_2': 524288, 'EffectSpellClassMaskC_2': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69632, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

master_poisoner_31227 = spell(
    id=31227,
    name='Master Poisoner',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=231, misc_value=23, trigger_spell=45176),
        Effect(type=EffectType.APPLY_AURA, base_points=-35, implicit_target_a=1, apply_aura=246, misc_value=4),
    ],
    spell_icon_id=1960,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical hit chance of all attacks made against any target you have poisoned by $s1%, reduces the duration of all Poison effects applied to you by $s2%, and gives Envenom a $s3% chance not to consume Deadly Poison.', 'EffectBasePoints_3': 65, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_2': 524288, 'EffectSpellClassMaskC_2': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69632, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

cheat_death_31228 = spell(
    id=31228,
    name='Cheat Death',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=2109,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a $s1% chance that an attack which would otherwise kill you will instead reduce you to 10% of your maximum health. In addition, all damage taken will be reduced by up to 90% for $45182d (modified by resilience).  This effect cannot occur more than once per minute.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 1024, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

cheat_death_31229 = spell(
    id=31229,
    name='Cheat Death',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=2109,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a $s1% chance that an attack which would otherwise kill you will instead reduce you to 10% of your maximum health. In addition, all damage taken will be reduced by up to 90% for $45182d (modified by resilience).  This effect cannot occur more than once per minute.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 1024, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

cheat_death_31230 = spell(
    id=31230,
    name='Cheat Death',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=2109,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a $s1% chance that an attack which would otherwise kill you will instead reduce you to 10% of your maximum health. In addition, all damage taken will be reduced by up to 90% for $45182d (modified by resilience).  This effect cannot occur more than once per minute.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 1024, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

find_weakness_31234 = spell(
    id=31234,
    name='Find Weakness',
    school=School.NORMAL,
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
    spell_icon_id=2112,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Offensive ability damage increased by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 637665822, 'EffectSpellClassMaskA_2': 262415, 'EffectSpellClassMaskB_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

find_weakness_31235 = spell(
    id=31235,
    name='Find Weakness',
    school=School.NORMAL,
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
    spell_icon_id=2112,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Offensive ability damage increased by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 637665822, 'EffectSpellClassMaskA_2': 262415, 'EffectSpellClassMaskB_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

find_weakness_31236 = spell(
    id=31236,
    name='Find Weakness',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=2112,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Offensive ability damage increased by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 637665822, 'EffectSpellClassMaskA_2': 262415, 'EffectSpellClassMaskB_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

quick_recovery_31244 = spell(
    id=31244,
    name='Quick Recovery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=2116,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'All healing effects on you are increased by $s2%.  In addition, your finishing moves refund $s1% of their Energy cost when they fail to hit.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 272, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

quick_recovery_31245 = spell(
    id=31245,
    name='Quick Recovery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=79, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=2116,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'All healing effects on you are increased by $s2%.  In addition, your finishing moves refund $s1% of their Energy cost when they fail to hit.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 272, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

deadened_nerves_31380 = spell(
    id=31380,
    name='Deadened Nerves',
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
    ],
    spell_icon_id=2110,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

deadened_nerves_31382 = spell(
    id=31382,
    name='Deadened Nerves',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=2110,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

deadened_nerves_31383 = spell(
    id=31383,
    name='Deadened Nerves',
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
    ],
    spell_icon_id=2110,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

surprise_attacks_32601 = spell(
    id=32601,
    name='Surprise Attacks',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=202, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2119,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your finishing moves can no longer be dodged, and the damage dealt by your Sinister Strike, Backstab, Shiv, Hemorrhage and Gouge abilities is increased by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3801088, 'EffectSpellClassMaskA_2': 9, 'EffectSpellClassMaskB_1': 570425358, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

combat_potency_35541 = spell(
    id=35541,
    name='Combat Potency',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=35542),
    ],
    spell_icon_id=2260,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your successful off-hand melee attacks a $h% chance to generate $35542s1 Energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 8},
)

combat_potency_35550 = spell(
    id=35550,
    name='Combat Potency',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=35545),
    ],
    spell_icon_id=2260,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your successful off-hand melee attacks a $h% chance to generate $35545s1 Energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 8},
)

combat_potency_35551 = spell(
    id=35551,
    name='Combat Potency',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=35546),
    ],
    spell_icon_id=2260,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your successful off-hand melee attacks a $h% chance to generate $35546s1 Energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 8},
)

combat_potency_35552 = spell(
    id=35552,
    name='Combat Potency',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=35547),
    ],
    spell_icon_id=2260,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your successful off-hand melee attacks a $h% chance to generate $35547s1 Energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 8},
)

combat_potency_35553 = spell(
    id=35553,
    name='Combat Potency',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=35548),
    ],
    spell_icon_id=2260,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your successful off-hand melee attacks a $h% chance to generate $35548s1 Energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 8},
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

deadly_brew_51625 = spell(
    id=51625,
    name='Deadly Brew',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=18),
    ],
    spell_icon_id=2963,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you apply Instant, Wound or Mind-Numbing poison to a target, you have a $h% chance to apply Crippling poison.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 268558336, 'EffectSpellClassMaskA_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 8},
)

deadly_brew_51626 = spell(
    id=51626,
    name='Deadly Brew',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=18),
    ],
    spell_icon_id=2963,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you apply Instant, Wound or Mind-Numbing poison to a target, you have a $h% chance to apply Crippling poison.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 268558336, 'EffectSpellClassMaskA_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69904, 'RangeIndex': 1, 'SpellClassSet': 8},
)

blood_spatter_51632 = spell(
    id=51632,
    name='Blood Spatter',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=2957,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage caused by your Garrote and Rupture abilities by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

blood_spatter_51633 = spell(
    id=51633,
    name='Blood Spatter',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=2957,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage caused by your Garrote and Rupture abilities by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
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

cut_to_the_chase_51664 = spell(
    id=51664,
    name='Cut to the Chase',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=22),
    ],
    spell_icon_id=2909,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Eviscerate and Envenom abilities have a $h% chance to refresh your Slice and Dice duration to its 5 combo point maximum.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11819},
)

cut_to_the_chase_51665 = spell(
    id=51665,
    name='Cut to the Chase',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=22),
    ],
    spell_icon_id=2909,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Eviscerate and Envenom abilities have a $h% chance to refresh your Slice and Dice duration to its 5 combo point maximum.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 40, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11819},
)

cut_to_the_chase_51667 = spell(
    id=51667,
    name='Cut to the Chase',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=22),
    ],
    spell_icon_id=2909,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Eviscerate and Envenom abilities have a $h% chance to refresh your Slice and Dice duration to its 5 combo point maximum.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 60, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11819},
)

cut_to_the_chase_51668 = spell(
    id=51668,
    name='Cut to the Chase',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=22),
    ],
    spell_icon_id=2909,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Eviscerate and Envenom abilities have a $h% chance to refresh your Slice and Dice duration to its 5 combo point maximum.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 80, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11819},
)

cut_to_the_chase_51669 = spell(
    id=51669,
    name='Cut to the Chase',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=22),
    ],
    spell_icon_id=2909,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Eviscerate and Envenom abilities have a $h% chance to refresh your Slice and Dice duration to its 5 combo point maximum.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11819},
)

throwing_specialization_51679 = spell(
    id=51679,
    name='Throwing Specialization',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=51680),
    ],
    spell_icon_id=2910,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of Throw and Deadly Throw by $s1 yards and gives your Deadly Throw a $h% chance to interrupt the target for $51680d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskA_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 349456, 'RangeIndex': 1, 'SpellClassSet': 8},
)

savage_combat_51682 = spell(
    id=51682,
    name='Savage Combat',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=127, trigger_spell=58684),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=166),
    ],
    spell_icon_id=1959,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total attack power by $s2% and all physical damage caused to enemies you have poisoned is increased by $58684s1%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EffectSpellClassMaskB_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69632, 'RangeIndex': 1, 'SpellClassSet': 8},
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

waylay_51692 = spell(
    id=51692,
    name='Waylay',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=1, trigger_spell=51693),
    ],
    spell_icon_id=2958,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Ambush and Backstab hits have a $h% chance to unbalance a target, increasing the time between their melee and ranged attacks by $51693s1%, and reducing movement speed by $51693s2% for $51693d.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 33554436, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 8},
)

waylay_51696 = spell(
    id=51696,
    name='Waylay',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=1, trigger_spell=51693),
    ],
    spell_icon_id=2958,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Ambush and Backstab hits have a $h% chance to unbalance a target, increasing the time between their melee and ranged attacks by $51693s1%, and reducing movement speed by $51693s2% for $51693d.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 33554436, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 8},
)

slaughter_from_the_shadows_51708 = spell(
    id=51708,
    name='Slaughter from the Shadows',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=2962,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the energy cost of your Backstab and Ambush abilities by $s1 and the energy cost of your Hemorrhage by $s2, and increases all damage done by $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 516, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

slaughter_from_the_shadows_51709 = spell(
    id=51709,
    name='Slaughter from the Shadows',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-9, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=2962,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the energy cost of your Backstab and Ambush abilities by $s1 and the energy cost of your Hemorrhage by $s2, and increases all damage done by $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 516, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

slaughter_from_the_shadows_51710 = spell(
    id=51710,
    name='Slaughter from the Shadows',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-13, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=2962,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the energy cost of your Backstab and Ambush abilities by $s1 and the energy cost of your Hemorrhage by $s2, and increases all damage done by $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 516, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

slaughter_from_the_shadows_51711 = spell(
    id=51711,
    name='Slaughter from the Shadows',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-17, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=2962,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the energy cost of your Backstab and Ambush abilities by $s1 and the energy cost of your Hemorrhage by $s2, and increases all damage done by $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 516, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

slaughter_from_the_shadows_51712 = spell(
    id=51712,
    name='Slaughter from the Shadows',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=2962,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the energy cost of your Backstab and Ambush abilities by $s1 and the energy cost of your Hemorrhage by $s2, and increases all damage done by $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 516, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
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

master_poisoner_58410 = spell(
    id=58410,
    name='Master Poisoner',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=231, misc_value=23, trigger_spell=45176),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=246, misc_value=4),
    ],
    spell_icon_id=1960,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical hit chance of all attacks made against any target you have poisoned by $s1%, reduces the duration of all Poison effects applied to you by $s2%, and gives Envenom a $s3% chance not to consume Deadly Poison.', 'EffectBasePoints_3': 99, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_2': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69632, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

savage_combat_58413 = spell(
    id=58413,
    name='Savage Combat',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=127, trigger_spell=58683),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=166),
    ],
    spell_icon_id=1959,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total attack power by $s2% and all physical damage caused to enemies you have poisoned is increased by $58683s1%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EffectSpellClassMaskB_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69632, 'RangeIndex': 1, 'SpellClassSet': 8},
)

filthy_tricks_58414 = spell(
    id=58414,
    name='Filthy Tricks',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-90001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=2906,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown by $/1000;s1 sec and energy cost by $s3 of your Tricks of the Trade, Distract and Shadowstep abilities and reduces the cooldown of Preparation by $/60000;S2 min.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_3': 8, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskA_2': 131584, 'EffectSpellClassMaskB_2': 4096, 'EffectSpellClassMaskC_1': 4096, 'EffectSpellClassMaskC_2': 131584, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11826},
)

filthy_tricks_58415 = spell(
    id=58415,
    name='Filthy Tricks',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-180001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=2906,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown by $/1000;s1 sec and energy cost by $s3 of your Tricks of the Trade, Distract and Shadowstep abilities and reduces the cooldown of Preparation by $/60000;S2 min.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_3': 8, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskA_2': 131584, 'EffectSpellClassMaskB_2': 4096, 'EffectSpellClassMaskC_1': 4096, 'EffectSpellClassMaskC_2': 131584, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11826},
)

relentless_strikes_58422 = spell(
    id=58422,
    name='Relentless Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=109, trigger_spell=14181),
    ],
    spell_icon_id=559,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1048576, 'AttributesEx4': 2, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your finishing moves have a $b1% chance per combo point to restore $14181s1 energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_1': 8.0, 'EffectSpellClassMaskA_1': 4063232, 'EffectSpellClassMaskA_2': 9, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

relentless_strikes_58423 = spell(
    id=58423,
    name='Relentless Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=109, trigger_spell=14181),
    ],
    spell_icon_id=559,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1048576, 'AttributesEx4': 2, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your finishing moves have a $b1% chance per combo point to restore $14181s1 energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_1': 12.0, 'EffectSpellClassMaskA_1': 4063232, 'EffectSpellClassMaskA_2': 9, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

relentless_strikes_58424 = spell(
    id=58424,
    name='Relentless Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=109, trigger_spell=14181),
    ],
    spell_icon_id=559,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1048576, 'AttributesEx4': 2, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your finishing moves have a $b1% chance per combo point to restore $14181s1 energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_1': 16.0, 'EffectSpellClassMaskA_1': 4063232, 'EffectSpellClassMaskA_2': 9, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

relentless_strikes_58425 = spell(
    id=58425,
    name='Relentless Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=109, trigger_spell=14181),
    ],
    spell_icon_id=559,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1048576, 'AttributesEx4': 2, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your finishing moves have a $b1% chance per combo point to restore $14181s1 energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_1': 20.0, 'EffectSpellClassMaskA_1': 4063232, 'EffectSpellClassMaskA_2': 9, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

aggression_61330 = spell(
    id=61330,
    name='Aggression',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=84,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Sinister Strike, Backstab, and Eviscerate abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131078, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

aggression_61331 = spell(
    id=61331,
    name='Aggression',
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
    ],
    spell_icon_id=84,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Sinister Strike, Backstab, and Eviscerate abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131078, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)

molten_skin_63349 = spell(
    id=63349,
    name='Molten Skin',
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
    ],
    spell_icon_id=2307,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

molten_skin_63350 = spell(
    id=63350,
    name='Molten Skin',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=2307,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)

molten_skin_63351 = spell(
    id=63351,
    name='Molten Skin',
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
    ],
    spell_icon_id=2307,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)


# --- talent tabs (source/talents/rogue.yaml) ---

combat_181_tab = tab(
    id=181,
    name='Combat',
    class_mask=8,
    order_index=1,
    spell_icon_id=243,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 365},
)

assassination_182_tab = tab(
    id=182,
    name='Assassination',
    class_mask=8,
    spell_icon_id=514,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 50},
)

subtlety_183_tab = tab(
    id=183,
    name='Subtlety',
    class_mask=8,
    order_index=2,
    spell_icon_id=250,
    raw_overrides={'Name_Lang_Mask': 16712190, 'RaceMask': 2047, 'BackgroundFile': 597},
)


# --- talents (source/talents/rogue.yaml) ---

granted_by_talent(
    id=181,
    tab=combat_181_tab,
    tier=1,
    column=3,
    ranks=[13705, 13832, 13843, 13844, 13845],
    player_castable=False,
)

granted_by_talent(
    id=182,
    tab=combat_181_tab,
    tier=2,
    column=2,
    ranks=[13706, 13804, 13805, 13806, 13807],
    player_castable=False,
    depends_on={'talent_id': 221, 'rank': 4},
)

granted_by_talent(
    id=184,
    tab=combat_181_tab,
    tier=4,
    column=0,
    ranks=[13709, 13800, 13801, 13802, 13803],
    player_castable=False,
)

granted_by_talent(
    id=186,
    tab=combat_181_tab,
    tier=3,
    column=2,
    ranks=[13712, 13788, 13789],
    player_castable=False,
)

granted_by_talent(
    id=187,
    tab=combat_181_tab,
    tier=1,
    column=1,
    ranks=[13713, 13853, 13854],
    player_castable=False,
)

granted_by_talent(
    id=201,
    tab=combat_181_tab,
    tier=0,
    column=1,
    ranks=[improved_sinister_strike_13732, improved_sinister_strike_13863],
    player_castable=False,
)

granted_by_talent(
    id=203,
    tab=combat_181_tab,
    tier=0,
    column=0,
    ranks=[improved_gouge_13741, improved_gouge_13793, improved_gouge_13792],
    player_castable=False,
)

granted_by_talent(
    id=204,
    tab=combat_181_tab,
    tier=2,
    column=0,
    ranks=[endurance_13742, endurance_13872],
    player_castable=False,
)

granted_by_talent(
    id=205,
    tab=combat_181_tab,
    tier=6,
    column=1,
    ranks=[adrenaline_rush_13750],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=206,
    tab=combat_181_tab,
    tier=3,
    column=0,
    ranks=[improved_kick_13754, improved_kick_13867],
    player_castable=False,
)

granted_by_talent(
    id=221,
    tab=combat_181_tab,
    tier=0,
    column=2,
    ranks=[dual_wield_specialization_13715, dual_wield_specialization_13848, dual_wield_specialization_13849, dual_wield_specialization_13851, dual_wield_specialization_13852],
    player_castable=False,
)

granted_by_talent(
    id=222,
    tab=combat_181_tab,
    tier=3,
    column=1,
    ranks=[improved_sprint_13743, improved_sprint_13875],
    player_castable=False,
)

granted_by_talent(
    id=223,
    tab=combat_181_tab,
    tier=4,
    column=1,
    ranks=[blade_flurry_13877],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=241,
    tab=subtlety_183_tab,
    tier=0,
    column=1,
    ranks=[13958, 13970, 13971],
    player_castable=False,
)

granted_by_talent(
    id=242,
    tab=combat_181_tab,
    tier=4,
    column=2,
    ranks=[13960, 13961, 13962, 13963, 13964],
    player_castable=False,
)

granted_by_talent(
    id=244,
    tab=subtlety_183_tab,
    tier=1,
    column=2,
    ranks=[camouflage_13975, camouflage_14062, camouflage_14063],
    player_castable=False,
)

granted_by_talent(
    id=245,
    tab=subtlety_183_tab,
    tier=3,
    column=1,
    ranks=[initiative_13976, initiative_13979, initiative_13980],
    player_castable=False,
)

granted_by_talent(
    id=246,
    tab=subtlety_183_tab,
    tier=3,
    column=0,
    ranks=[13983, 14070, 14071],
    player_castable=False,
)

granted_by_talent(
    id=247,
    tab=subtlety_183_tab,
    tier=2,
    column=0,
    ranks=[elusiveness_13981, elusiveness_14066],
    player_castable=False,
)

granted_by_talent(
    id=261,
    tab=subtlety_183_tab,
    tier=0,
    column=2,
    ranks=[opportunity_14057, opportunity_14072],
    player_castable=False,
)

granted_by_talent(
    id=262,
    tab=subtlety_183_tab,
    tier=1,
    column=1,
    ranks=[dirty_tricks_14076, dirty_tricks_14094],
    player_castable=False,
)

granted_by_talent(
    id=263,
    tab=subtlety_183_tab,
    tier=3,
    column=2,
    ranks=[improved_ambush_14079, improved_ambush_14080],
    player_castable=False,
)

granted_by_talent(
    id=265,
    tab=subtlety_183_tab,
    tier=4,
    column=2,
    ranks=[dirty_deeds_14082, dirty_deeds_14083],
    player_castable=False,
)

granted_by_talent(
    id=268,
    tab=assassination_182_tab,
    tier=3,
    column=2,
    ranks=[improved_poisons_14113, improved_poisons_14114, improved_poisons_14115, improved_poisons_14116, improved_poisons_14117],
    player_castable=False,
)

granted_by_talent(
    id=269,
    tab=assassination_182_tab,
    tier=2,
    column=2,
    ranks=[lethality_14128, lethality_14132, lethality_14135, lethality_14136, lethality_14137],
    player_castable=False,
    depends_on={'talent_id': 270, 'rank': 4},
)

granted_by_talent(
    id=270,
    tab=assassination_182_tab,
    tier=0,
    column=2,
    ranks=[14138, 14139, 14140, 14141, 14142],
    player_castable=False,
)

granted_by_talent(
    id=272,
    tab=assassination_182_tab,
    tier=0,
    column=1,
    ranks=[14144, 14148],
    player_castable=False,
)

granted_by_talent(
    id=273,
    tab=assassination_182_tab,
    tier=1,
    column=0,
    ranks=[ruthlessness_14156, ruthlessness_14160, ruthlessness_14161],
    player_castable=False,
)

granted_by_talent(
    id=274,
    tab=assassination_182_tab,
    tier=5,
    column=2,
    ranks=[murder_14158, murder_14159],
    player_castable=False,
)

granted_by_talent(
    id=276,
    tab=assassination_182_tab,
    tier=0,
    column=0,
    ranks=[improved_eviscerate_14162, improved_eviscerate_14163, improved_eviscerate_14164],
    player_castable=False,
)

granted_by_talent(
    id=277,
    tab=assassination_182_tab,
    tier=1,
    column=3,
    ranks=[puncturing_wounds_13733, puncturing_wounds_13865, puncturing_wounds_13866],
    player_castable=False,
)

granted_by_talent(
    id=278,
    tab=assassination_182_tab,
    tier=2,
    column=1,
    ranks=[improved_expose_armor_14168, improved_expose_armor_14169],
    player_castable=False,
)

granted_by_talent(
    id=279,
    tab=assassination_182_tab,
    tier=4,
    column=2,
    ranks=[improved_kidney_shot_14174, improved_kidney_shot_14175, improved_kidney_shot_14176],
    player_castable=False,
)

granted_by_talent(
    id=280,
    tab=assassination_182_tab,
    tier=4,
    column=1,
    ranks=[cold_blood_14177],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=281,
    tab=assassination_182_tab,
    tier=6,
    column=1,
    ranks=[58426],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=283,
    tab=assassination_182_tab,
    tier=5,
    column=1,
    ranks=[seal_fate_14186, seal_fate_14190, seal_fate_14193, seal_fate_14194, seal_fate_14195],
    player_castable=False,
    depends_on={'talent_id': 280, 'rank': 0},
)

granted_by_talent(
    id=284,
    tab=subtlety_183_tab,
    tier=4,
    column=1,
    ranks=[preparation_14185],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=301,
    tab=combat_181_tab,
    tier=2,
    column=1,
    ranks=[riposte_14251],
    player_castable=False,
    depends_on={'talent_id': 187, 'rank': 2},
    flags=1,
)

granted_by_talent(
    id=303,
    tab=subtlety_183_tab,
    tier=2,
    column=1,
    ranks=[ghostly_strike_14278],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=381,
    tab=subtlety_183_tab,
    tier=6,
    column=1,
    ranks=[premeditation_14183],
    player_castable=False,
    depends_on={'talent_id': 284, 'rank': 0},
    flags=1,
)

granted_by_talent(
    id=382,
    tab=assassination_182_tab,
    tier=2,
    column=0,
    ranks=[vigor_14983],
    player_castable=False,
)

granted_by_talent(
    id=681,
    tab=subtlety_183_tab,
    tier=4,
    column=3,
    ranks=[hemorrhage_16511],
    player_castable=False,
    depends_on={'talent_id': 1123, 'rank': 2},
    flags=1,
)

granted_by_talent(
    id=682,
    tab=assassination_182_tab,
    tier=3,
    column=1,
    ranks=[vile_poisons_16513, vile_poisons_16514, vile_poisons_16515],
    player_castable=False,
)

granted_by_talent(
    id=1122,
    tab=combat_181_tab,
    tier=3,
    column=3,
    ranks=[aggression_18427, aggression_18428, aggression_18429, aggression_61330, aggression_61331],
    player_castable=False,
)

granted_by_talent(
    id=1123,
    tab=subtlety_183_tab,
    tier=2,
    column=2,
    ranks=[serrated_blades_14171, serrated_blades_14172, serrated_blades_14173],
    player_castable=False,
)

granted_by_talent(
    id=1700,
    tab=subtlety_183_tab,
    tier=1,
    column=0,
    ranks=[sleight_of_hand_30892, sleight_of_hand_30893],
    player_castable=False,
)

granted_by_talent(
    id=1701,
    tab=subtlety_183_tab,
    tier=4,
    column=0,
    ranks=[30894, 30895],
    player_castable=False,
)

granted_by_talent(
    id=1702,
    tab=subtlety_183_tab,
    tier=5,
    column=2,
    ranks=[30902, 30903, 30904, 30905, 30906],
    player_castable=False,
)

granted_by_talent(
    id=1703,
    tab=combat_181_tab,
    tier=5,
    column=1,
    ranks=[30919, 30920],
    player_castable=False,
    depends_on={'talent_id': 223, 'rank': 0},
)

granted_by_talent(
    id=1705,
    tab=combat_181_tab,
    tier=6,
    column=0,
    ranks=[31122, 31123, 61329],
    player_castable=False,
)

granted_by_talent(
    id=1706,
    tab=combat_181_tab,
    tier=5,
    column=2,
    ranks=[blade_twisting_31124, blade_twisting_31126],
    player_castable=False,
)

granted_by_talent(
    id=1707,
    tab=combat_181_tab,
    tier=6,
    column=2,
    ranks=[31130, 31131],
    player_castable=False,
)

granted_by_talent(
    id=1709,
    tab=combat_181_tab,
    tier=8,
    column=1,
    ranks=[surprise_attacks_32601],
    player_castable=False,
    depends_on={'talent_id': 205, 'rank': 0},
    flags=1,
)

granted_by_talent(
    id=1711,
    tab=subtlety_183_tab,
    tier=6,
    column=0,
    ranks=[31211, 31212, 31213],
    player_castable=False,
)

granted_by_talent(
    id=1712,
    tab=subtlety_183_tab,
    tier=7,
    column=1,
    ranks=[sinister_calling_31216, sinister_calling_31217, sinister_calling_31218, sinister_calling_31219, sinister_calling_31220],
    player_castable=False,
    depends_on={'talent_id': 381, 'rank': 0},
)

granted_by_talent(
    id=1713,
    tab=subtlety_183_tab,
    tier=5,
    column=0,
    ranks=[31221, 31222, master_of_subtlety_31223],
    player_castable=False,
)

granted_by_talent(
    id=1714,
    tab=subtlety_183_tab,
    tier=8,
    column=1,
    ranks=[shadowstep_36554],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=1715,
    tab=assassination_182_tab,
    tier=8,
    column=0,
    ranks=[master_poisoner_31226, master_poisoner_31227, master_poisoner_58410],
    player_castable=False,
)

granted_by_talent(
    id=1718,
    tab=assassination_182_tab,
    tier=7,
    column=2,
    ranks=[find_weakness_31234, find_weakness_31235, find_weakness_31236],
    player_castable=False,
)

granted_by_talent(
    id=1719,
    tab=assassination_182_tab,
    tier=8,
    column=1,
    ranks=[mutilate_1329],
    player_castable=False,
    depends_on={'talent_id': 281, 'rank': 0},
    flags=1,
)

granted_by_talent(
    id=1721,
    tab=assassination_182_tab,
    tier=4,
    column=0,
    ranks=[31208, 31209],
    player_castable=False,
)

granted_by_talent(
    id=1722,
    tab=subtlety_183_tab,
    tier=6,
    column=2,
    ranks=[cheat_death_31228, cheat_death_31229, cheat_death_31230],
    player_castable=False,
)

granted_by_talent(
    id=1723,
    tab=assassination_182_tab,
    tier=6,
    column=2,
    ranks=[deadened_nerves_31380, deadened_nerves_31382, deadened_nerves_31383],
    player_castable=False,
)

granted_by_talent(
    id=1762,
    tab=assassination_182_tab,
    tier=4,
    column=3,
    ranks=[quick_recovery_31244, quick_recovery_31245],
    player_castable=False,
)

granted_by_talent(
    id=1825,
    tab=combat_181_tab,
    tier=7,
    column=2,
    ranks=[combat_potency_35541, combat_potency_35550, combat_potency_35551, combat_potency_35552, combat_potency_35553],
    player_castable=False,
)

granted_by_talent(
    id=1827,
    tab=combat_181_tab,
    tier=1,
    column=0,
    ranks=[improved_slice_and_dice_14165, improved_slice_and_dice_14166],
    player_castable=False,
)

granted_by_talent(
    id=2065,
    tab=assassination_182_tab,
    tier=6,
    column=0,
    ranks=[deadly_brew_51625, deadly_brew_51626],
    player_castable=False,
)

granted_by_talent(
    id=2066,
    tab=assassination_182_tab,
    tier=8,
    column=2,
    ranks=[51627, 51628, 51629],
    player_castable=False,
)

granted_by_talent(
    id=2068,
    tab=assassination_182_tab,
    tier=1,
    column=1,
    ranks=[blood_spatter_51632, blood_spatter_51633],
    player_castable=False,
)

granted_by_talent(
    id=2069,
    tab=assassination_182_tab,
    tier=7,
    column=0,
    ranks=[51634, 51635, 51636],
    player_castable=False,
)

granted_by_talent(
    id=2070,
    tab=assassination_182_tab,
    tier=9,
    column=1,
    ranks=[cut_to_the_chase_51664, cut_to_the_chase_51665, cut_to_the_chase_51667, cut_to_the_chase_51668, cut_to_the_chase_51669],
    player_castable=False,
)

granted_by_talent(
    id=2071,
    tab=assassination_182_tab,
    tier=10,
    column=1,
    ranks=[hunger_for_blood_51662],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=2072,
    tab=combat_181_tab,
    tier=7,
    column=0,
    ranks=[throwing_specialization_5952, throwing_specialization_51679],
    player_castable=False,
)

granted_by_talent(
    id=2073,
    tab=combat_181_tab,
    tier=8,
    column=0,
    ranks=[51672, 51674],
    player_castable=False,
)

granted_by_talent(
    id=2074,
    tab=combat_181_tab,
    tier=8,
    column=2,
    ranks=[savage_combat_51682, savage_combat_58413],
    player_castable=False,
)

granted_by_talent(
    id=2075,
    tab=combat_181_tab,
    tier=9,
    column=1,
    ranks=[51685, 51686, 51687, 51688, 51689],
    player_castable=False,
)

granted_by_talent(
    id=2076,
    tab=combat_181_tab,
    tier=10,
    column=1,
    ranks=[killing_spree_51690],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=2077,
    tab=subtlety_183_tab,
    tier=7,
    column=2,
    ranks=[waylay_51692, waylay_51696],
    player_castable=False,
)

granted_by_talent(
    id=2078,
    tab=subtlety_183_tab,
    tier=8,
    column=0,
    ranks=[51698, 51700, 51701],
    player_castable=False,
)

granted_by_talent(
    id=2079,
    tab=subtlety_183_tab,
    tier=8,
    column=2,
    ranks=[filthy_tricks_58414, filthy_tricks_58415],
    player_castable=False,
)

granted_by_talent(
    id=2080,
    tab=subtlety_183_tab,
    tier=9,
    column=1,
    ranks=[slaughter_from_the_shadows_51708, slaughter_from_the_shadows_51709, slaughter_from_the_shadows_51710, slaughter_from_the_shadows_51711, slaughter_from_the_shadows_51712],
    player_castable=False,
)

granted_by_talent(
    id=2081,
    tab=subtlety_183_tab,
    tier=10,
    column=1,
    ranks=[shadow_dance_51713],
    player_castable=False,
    flags=1,
)

granted_by_talent(
    id=2244,
    tab=subtlety_183_tab,
    tier=0,
    column=0,
    ranks=[relentless_strikes_14179, relentless_strikes_58422, relentless_strikes_58423, relentless_strikes_58424, relentless_strikes_58425],
    player_castable=False,
)
